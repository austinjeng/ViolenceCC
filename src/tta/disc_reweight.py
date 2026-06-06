"""R1 discriminative-reliability routing — production helpers (quick-260607-42h).

Label-free, tuning-free TTA: scale the VL (clip) stream by a per-condition scalar
``w`` AFTER ``ln_clip`` (in BOTH the fused term and the residual highway of
GatedFusion), routing toward the corruption-robust skeleton stream exactly where
(and only where) the VL stream collapses.

Routing scalar (per condition, label-free):

    w_vl     = clip(clip_std_test / clip_std_clean, 0, 1)    # retained VL spread
    skel_rel = clip((2*skelZ_floor - skelZ)/skelZ_floor, 0, 1)  # skeleton reliability
    w        = 1 - (1 - w_vl) * skel_rel                     # lean on skel only if VL
                                                              # collapsed AND skel clean

These helpers are ported verbatim (logic, not behavior) from the validated
throwaway reference ``scripts/_tmp_r1_full.py`` / ``scripts/_tmp_tta_harness.py``
/ ``scripts/_tmp_coral_derisk.py`` so the headline TTA-boost result is reproducible
from the canonical entry point ``src/tta/evaluate_tta.py`` rather than an untracked
script. Full-condition numeric reproduction (e.g. clip-vit-b-16 gaussian_noise sev5
source ~57.70 -> ~62.5, +4.8) is covered by ``scripts/_tmp_r1_full.py`` /
``results/_coral_derisk/r1full_clip.json``; this module carries only the pure
``compute_w`` unit guarantee in ``tests/test_disc_reweight.py``.

This is a pure helper library: no CLI, no argparse, no main(). Tensors operate on
whatever device the caller placed them on (the caller moves features to device).
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import torch


# ---------------------------------------------------------------------------
# Streaming float64 mean/cov (port of scripts/_tmp_coral_derisk.py:_accumulate)
# ---------------------------------------------------------------------------


def accumulate(items, load):
    """Streaming float64 mean/cov over snippet feature arrays.

    Args:
        items: iterable of opaque keys (e.g. video ids).
        load: callable item -> np.ndarray [n, D] (or None / empty to skip).

    Returns:
        (mu[D], cov[D,D], n) with ``cov = ss/n - outer(mu, mu)`` (population cov,
        float64). Items where ``load`` returns None or an empty array are skipped.
    """
    n = 0
    s = None
    ss = None
    for item in items:
        x = load(item)
        if x is None or x.shape[0] == 0:
            continue
        x = x.astype(np.float64)
        if s is None:
            d = x.shape[1]
            s = np.zeros(d)
            ss = np.zeros((d, d))
        s += x.sum(0)
        ss += x.T @ x
        n += x.shape[0]
    mu = s / n
    cov = ss / n - np.outer(mu, mu)
    return mu, cov, n


# ---------------------------------------------------------------------------
# Per-channel mean-shift z-score (port of _tmp_tta_harness.py:shift_stats +
# _tmp_r1_full.py:meanZ)
# ---------------------------------------------------------------------------


def mean_shift_z(mu_s, C_s, mu_t, C_t):
    """Per-channel mean-shift z-score: ``z = (mu_t - mu_s) / sd_s``.

    ``sd_s = sqrt(clip(diag(C_s), 1e-12, None))`` — the source per-channel std.
    ``C_t`` is accepted for signature parity with the reference but is not used
    by the mean-shift z (it only enters variance-ratio descriptors that R1 does
    not consume).
    """
    sd_s = np.sqrt(np.clip(np.diag(C_s), 1e-12, None))
    return (mu_t - mu_s) / sd_s


def mean_abs_z(mu_s, C_s, mu_t, C_t):
    """Mean absolute per-channel mean-shift z (``_tmp_r1_full.py:meanZ``)."""
    return float(np.mean(np.abs(mean_shift_z(mu_s, C_s, mu_t, C_t))))


# ---------------------------------------------------------------------------
# Forward variants (port of _tmp_r1_full.py:clip_only_fwd / fwd_w)
# ---------------------------------------------------------------------------


def clip_only_forward(model, skel, clip):
    """Canonical GatedFusion forward with the skeleton stream ZEROED.

    ``p_skel = ln_skel(zeros_like(skel_proj(skel)))`` isolates the VL (clip)
    stream's solo discriminative spread (the label-free reliability signal).
    Mirrors ``scripts/_tmp_r1_full.py:clip_only_fwd``. Returns scores ``[1, t]``.
    """
    z = torch.zeros_like(model.skel_proj(skel))
    p_skel = model.ln_skel(z)
    p_clip = model.ln_clip(model.clip_proj(clip))
    g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
    out = model.ln_fused(g * p_skel + (1 - g) * p_clip + p_skel + p_clip)
    return model.head(out).squeeze(-1)


def w_scaled_forward(w: float) -> Callable:
    """Return a GatedFusion forward fn that scales ``p_clip`` by ``w``.

    The scaling is applied AFTER ``ln_clip`` (``pc = w * p_clip``) in BOTH the
    fused term and the residual highway:
        out = ln_fused(g*p_skel + (1-g)*pc + p_skel + pc)

    The scaling MUST be after ``ln_clip``: ``ln_clip`` re-centers and re-scales
    per-token, so scaling the clip INPUT (before ln_clip) is nulled by the
    LayerNorm and has no effect on the output. Mirrors
    ``scripts/_tmp_r1_full.py:fwd_w``.
    """

    def f(model, skel, clip):
        p_skel = model.ln_skel(model.skel_proj(skel))
        p_clip = model.ln_clip(model.clip_proj(clip))
        pc = w * p_clip
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        out = model.ln_fused(g * p_skel + (1 - g) * pc + p_skel + pc)
        return model.head(out).squeeze(-1)

    return f


# ---------------------------------------------------------------------------
# Clip-only discriminative spread (port of _tmp_r1_full.py:clip_only_std)
# ---------------------------------------------------------------------------


def clip_only_std(model, skels, clips, vids, T: int = 32):
    """Std of pooled clip-only snippet scores over all videos in ``vids``.

    Chunks each video into T=32-snippet batches under ``torch.no_grad()``,
    concatenates the clip-only scores across all videos, and returns their std
    (the retained VL discriminative spread). Tensors are placed on the same
    device as ``model``'s parameters. Mirrors ``_tmp_r1_full.py:clip_only_std``.
    """
    device = next(model.parameters()).device
    alls = []
    with torch.no_grad():
        for v in vids:
            n = skels[v].shape[0]
            for s in range(0, n, T):
                e = min(s + T, n)
                sk = torch.from_numpy(
                    skels[v][s:e].astype(np.float32)
                ).unsqueeze(0).to(device)
                cl = torch.from_numpy(
                    clips[v][s:e].astype(np.float32)
                ).unsqueeze(0).to(device)
                alls.append(clip_only_forward(model, sk, cl).squeeze(0).cpu().numpy())
    return float(np.std(np.concatenate(alls)))


# ---------------------------------------------------------------------------
# Routing scalar (port of _tmp_r1_full.py:run, lines 93-96)
# ---------------------------------------------------------------------------


def compute_w(clip_std_test: float, clip_std_clean: float, skelZ: float, skelZ_floor: float):
    """Compute the per-condition routing scalar ``w`` (pure scalar math).

        w_vl     = clip(clip_std_test / clip_std_clean, 0, 1)
        skel_rel = clip((2*skelZ_floor - skelZ)/skelZ_floor, 0, 1)  if skelZ_floor > 1e-9 else 0.0
        w        = 1 - (1 - w_vl) * skel_rel

    No torch / no disk. Returns ``(w, w_vl, skel_rel)``.
    """
    w_vl = min(1.0, max(0.0, clip_std_test / clip_std_clean))
    if skelZ_floor > 1e-9:
        skel_rel = min(1.0, max(0.0, (2.0 * skelZ_floor - skelZ) / skelZ_floor))
    else:
        skel_rel = 0.0
    w = 1.0 - (1.0 - w_vl) * skel_rel
    return w, w_vl, skel_rel
