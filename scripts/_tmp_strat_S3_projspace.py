"""STRATEGY S3 — Projection-space restoration (throwaway TTA-boost screen).

Idea (addresses F3 + F4): the model sees the VL stream ONLY through
clip_proj (Dvl->256) then ln_clip. So restore the corruption shift in the
256-d PROJECTED space, not the raw Dvl space. Projected stats are obtained
ANALYTICALLY from the raw cached stats and the linear layer:

    W = clip_proj.weight [256, Dvl],  b = clip_proj.bias [256]
    mu_z = W @ mu_raw + b
    C_z  = W @ C_raw  @ W.T          (bias drops out of covariance)

We CORAL-align z = clip_proj(clip) in 256-d toward the clean-TRAIN projected
stats, THEN apply ln_clip. Because ln_clip re-normalizes EACH token (subtracts
the per-token mean, divides by the per-token std), per-channel MEAN restoration
and a global scale are largely nulled (F4). What survives into p_clip is the
*within-token activation shape* — i.e. the channel CORRELATION structure scaled
by gamma. So a correlation-structure realignment (decorrelate test, recolor to
source correlation) is the rank-relevant intervention; a full-cov CORAL also
moves per-channel scale that ln then discards.

LABEL-FREE / TUNING-FREE (F5): the headline transform `corr` has NO free knob —
it is correlation-only CORAL (standardize each channel to unit var, align the
correlation matrices via symmetric whitening, restore source per-channel std).
We additionally score a few fixed-beta full-cov variants in the SAME run purely
to expose the mechanism; the pre-committed honest choice is `corr`.

Skeleton stream: corrupted only for motion_blur/jpeg; we leave skeleton
untouched here (S3 targets the VL projection path only) to isolate the effect.
"""
import argparse
import json
import pathlib

import numpy as np
import torch

import _tmp_tta_harness as H

# Which aligned variant the forward_fn applies. The honest, pre-committed,
# knob-free choice is "corr" (correlation-only). The fixed-beta full-cov
# variants are mechanism probes (still label-free: beta is a stated constant,
# NOT selected by test AUC).
_VARIANT = "corr"


def _proj_stats(model):
    """Analytic projected clean-TRAIN clip stats (256-d) from raw cached stats."""
    W = model.clip_proj.weight.detach().cpu().numpy().astype(np.float64)   # [256, Dvl]
    b = model.clip_proj.bias.detach().cpu().numpy().astype(np.float64)     # [256]
    return W, b


def _coral_W_corr(mu_t, C_t, mu_s, C_s, ridge_rel=1e-6):
    """Correlation-only CORAL whitening matrix (NO beta knob).

    Standardize each channel to unit variance (using its own std), align the
    correlation matrices via symmetric sqrt, then rescale back to SOURCE std.
    x' = (x - mu_t) @ W + mu_s, with
        W = diag(1/sd_t) @ Rt^{-1/2} @ Rs^{1/2} @ diag(sd_s)
    where Rt,Rs are the correlation matrices of test/source.
    """
    sd_t = np.sqrt(np.clip(np.diag(C_t), 1e-12, None))
    sd_s = np.sqrt(np.clip(np.diag(C_s), 1e-12, None))
    Rt = C_t / np.outer(sd_t, sd_t)
    Rs = C_s / np.outer(sd_s, sd_s)
    d = Rt.shape[0]
    Rt = Rt + np.eye(d) * (ridge_rel * np.trace(Rt) / d)
    Rs = Rs + np.eye(d) * (ridge_rel * np.trace(Rs) / d)
    W = (np.diag(1.0 / sd_t) @ H._sym_sqrt(Rt, inv=True)
         @ H._sym_sqrt(Rs, inv=False) @ np.diag(sd_s))
    return W


def _build_align(model, cond):
    """Precompute the 256-d projected source/test stats and the chosen W,
    plus mu_t_z/mu_s_z for recentering. Returns a dict of W matrices."""
    W, b = _proj_stats(model)

    # raw clean-TRAIN clip stats
    mu_s_raw, C_s_raw = H.source_stats(cond.bb, "clip")
    mu_s_raw = mu_s_raw.astype(np.float64); C_s_raw = C_s_raw.astype(np.float64)
    # raw transductive test stats (this condition)
    mu_t_raw = cond.mu_t_clip.astype(np.float64)
    C_t_raw = cond.C_t_clip.astype(np.float64)

    # analytic projection to 256-d
    mu_s_z = W @ mu_s_raw + b
    C_s_z = W @ C_s_raw @ W.T
    mu_t_z = W @ mu_t_raw + b
    C_t_z = W @ C_t_raw @ W.T

    out = {"mu_s_z": mu_s_z, "mu_t_z": mu_t_z}
    # correlation-only (knob-free headline)
    out["corr"] = _coral_W_corr(mu_t_z, C_t_z, mu_s_z, C_s_z)
    # fixed-beta full/diagonal CORAL mechanism probes (stated constants)
    for beta in (0.0, 0.3, 0.7, 1.0):
        out[f"b{beta:.1f}"] = H._coral_W(mu_t_z, C_t_z, mu_s_z, C_s_z, beta)
    return out


def _make_forward(align, variant):
    mu_t_z = torch.from_numpy(align["mu_t_z"]).float()
    mu_s_z = torch.from_numpy(align["mu_s_z"]).float()
    Wt = torch.from_numpy(align[variant].astype(np.float64)).float()

    def my_forward(model, skel, clip):
        # skel path unchanged
        p_skel = model.ln_skel(model.skel_proj(skel))
        # clip path: project, CORAL-align in 256-d, THEN ln_clip
        z = model.clip_proj(clip)                       # [1, t, 256]
        z_aln = (z - mu_t_z) @ Wt + mu_s_z              # align toward clean-train
        p_clip = model.ln_clip(z_aln)
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        fused = g * p_skel + (1.0 - g) * p_clip
        residual = fused + p_skel + p_clip
        out = model.ln_fused(residual)
        return model.head(out).squeeze(-1)

    return my_forward


def strategy(cond, st):
    model = st["model"]
    align = _build_align(model, cond)
    fwd = _make_forward(align, _VARIANT)
    # feature-space dicts unchanged; the transform lives inside forward.
    return cond.skels, cond.clips, fwd


def _score_variant(model, cond, align, variant):
    fwd = _make_forward(align, variant)
    f, v = H.score(model, cond.skels, cond.clips, cond.vids, forward_fn=fwd)
    return f, v


def run(bb, sevs, probe_all=False):
    st = H.build(bb)
    model = st["model"]
    per = {}
    probe = {}
    variants = ["corr", "b0.0", "b0.3", "b0.7", "b1.0"] if probe_all else [_VARIANT]
    for ctype in H.CORRUPTIONS:
        for sev in sevs:
            cond = H.load_condition(bb, ctype, sev)
            f0, v0 = H.score(model, cond.skels, cond.clips, cond.vids)
            align = _build_align(model, cond)
            # headline pre-committed variant
            f1, v1 = _score_variant(model, cond, align, _VARIANT)
            per[f"{ctype}_{sev}"] = {"src_auc": f0, "strat_auc": f1,
                                     "src_vauc": v0, "strat_vauc": v1}
            line = f"  {bb} {ctype}_{sev}: src={f0:.2f} {_VARIANT}={f1:.2f} d={f1-f0:+.2f}"
            if probe_all:
                pr = {}
                for vv in variants:
                    fa, _ = (f1, v1) if vv == _VARIANT else _score_variant(model, cond, align, vv)
                    pr[vv] = round(fa - f0, 2)
                probe[f"{ctype}_{sev}"] = pr
                line += "  probes=" + " ".join(f"{k}{v:+.1f}" for k, v in pr.items())
            print(line, flush=True)
    return per, probe


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--severities", default="5")
    ap.add_argument("--probe-all", action="store_true",
                    help="also score fixed-beta full-cov variants (mechanism)")
    a = ap.parse_args()
    per, probe = run(a.backbone, tuple(int(x) for x in a.severities.split(",")),
                     probe_all=a.probe_all)
    summ = H.analyze(per)
    out = {"backbone": a.backbone, "variant": _VARIANT, "summary": summ,
           "per_condition": per}
    if probe:
        out["probes"] = probe
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2))
    print(json.dumps({"backbone": a.backbone, "variant": _VARIANT, **summ}))
