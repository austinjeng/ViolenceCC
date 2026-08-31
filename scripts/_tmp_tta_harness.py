"""Reusable harness for the TTA-boost STRATEGY SEARCH (throwaway).

Every strategy is evaluated identically and HONESTLY: label-free / tuning-free
transforms scored on existing test-C. A strategy that uses no test labels and no
tuned-on-test hyperparameter has a directly-honest test-C delta (no val-C needed).

Public API
----------
build(bb) -> dict(model, adaptor, source_state, prefix)      # cached per bb
source_stats(bb, stream) -> (mu[D], C[D,D])                  # clean-TRAIN, cached npz
shift_stats(mu_s, C_s, mu_t, C_t) -> dict(dmu, z, sd_s, ...) # per-channel shift descriptors
load_condition(bb, ctype, sev) -> Cond                       # feats + transductive test stats
score(model, skels, clips, vids, forward_fn=None) -> (frame_auc%, video_auc%)
ref_forward(model, skel, clip) -> scores                     # GatedFusion forward (copy+edit for model strategies)
analyze(per_condition) -> dict                               # honest summary (mean delta, brightness damage, ...)

Reused CORAL primitives (re-exported): _sym_sqrt, _shrink, _coral_W, _apply, _accumulate

Conventions: corruption applies to the VL (clip) stream for all 4 families; the
skeleton stream is CORRUPTED only for motion_blur/jpeg_compression and CLEAN
(reused) for gaussian_noise/brightness. AUC is frame-level (the paper metric);
video-level AUC is the weak signal a real val-C could provide.
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from copy import deepcopy
from src.eval.metrics import compute_frame_metrics
from src.eval.snippet_to_frame import snippet_to_frame
from src.eval.ucf_annotations import frame_labels, parse_annotations
from src.models.registry import build_model
from src.tta.tent import configure_model
from src.utils.checkpoint import load_checkpoint
from src.utils.config import load_snapshot_as_config
from src.tta.evaluate_tta import (
    _SourceOnlyAdaptor, _load_test_video_features,
    BACKBONE_FEATURE_PREFIX, BACKBONE_SOURCE_RUNS, SKELETON_REEXTRACT_TYPES,
)
from _tmp_coral_derisk import (
    _sym_sqrt, _shrink, _coral_W, _apply, _accumulate, _video_score,
)

DEVICE = "cpu"
CORRUPTIONS = ("gaussian_noise", "jpeg_compression", "brightness", "motion_blur")
_CACHE = _ROOT / "results" / "_coral_derisk" / "_srccache"
_ANNOS = parse_annotations(_ROOT / "data" / "annotations" / "ucf_temporal.txt")
_TEST_IDS = [l.strip() for l in (_ROOT / "data/splits/ucf_test.txt").read_text().splitlines() if l.strip()]
_MODELS = {}


def build(bb):
    if bb in _MODELS:
        return _MODELS[bb]
    torch.manual_seed(0); np.random.seed(0)
    run = _ROOT / "results" / BACKBONE_SOURCE_RUNS[bb]
    cfg = load_snapshot_as_config(run / "config_snapshot.json")
    model = build_model(**cfg["model"]).to(DEVICE)
    state = load_checkpoint(run / "best_model.pth", device=DEVICE)
    sd = state.get("model", state) if isinstance(state, dict) else state
    model.load_state_dict(sd, strict=True)
    source_state = deepcopy(model.state_dict())
    configure_model(model)  # disable dropout -> deterministic
    out = {"model": model, "adaptor": _SourceOnlyAdaptor(model, source_state),
           "source_state": source_state, "prefix": BACKBONE_FEATURE_PREFIX[bb]}
    _MODELS[bb] = out
    return out


def source_stats(bb, stream):
    f = _CACHE / f"{bb}_{stream}.npz"
    if not f.exists():
        raise FileNotFoundError(f"run _tmp_cache_srcstats.py first: {f}")
    d = np.load(str(f))
    return d["mu"], d["C"]


def shift_stats(mu_s, C_s, mu_t, C_t):
    sd_s = np.sqrt(np.clip(np.diag(C_s), 1e-12, None))
    sd_t = np.sqrt(np.clip(np.diag(C_t), 1e-12, None))
    dmu = mu_t - mu_s
    z = dmu / sd_s                                   # per-channel mean-shift z-score
    return {"dmu": dmu, "z": z, "sd_s": sd_s, "sd_t": sd_t,
            "var_ratio": (sd_t / sd_s) ** 2,
            "frac_var_shift": float(np.mean(np.abs(np.log(sd_t / sd_s + 1e-12))))}


def load_condition(bb, ctype, sev):
    feat_root = Path("E:/features/ucf")
    skels, clips, vids = {}, {}, []
    for vid in _TEST_IDS:
        sk, cl = _load_test_video_features(vid, ctype, sev, feat_root, backbone=bb)
        if sk is None:
            continue
        skels[vid] = sk; clips[vid] = cl; vids.append(vid)
    skel_corrupt = ctype in SKELETON_REEXTRACT_TYPES
    mu_t_clip, C_t_clip, _ = _accumulate(vids, lambda v: clips[v])
    mu_t_skel, C_t_skel, _ = _accumulate(vids, lambda v: skels[v])
    return SimpleNamespace(bb=bb, ctype=ctype, sev=sev, skels=skels, clips=clips,
                           vids=vids, skel_corrupt=skel_corrupt,
                           mu_t_clip=mu_t_clip, C_t_clip=C_t_clip,
                           mu_t_skel=mu_t_skel, C_t_skel=C_t_skel)


def ref_forward(model, skel, clip):
    """Exact GatedFusion.forward (copy+edit this for model-level strategies).
    skel:[1,t,256] clip:[1,t,Dvl] -> scores [1,t]."""
    p_skel = model.ln_skel(model.skel_proj(skel))
    p_clip = model.ln_clip(model.clip_proj(clip))
    g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
    fused = g * p_skel + (1.0 - g) * p_clip
    residual = fused + p_skel + p_clip
    out = model.ln_fused(residual)            # dropout disabled by configure_model
    return model.head(out).squeeze(-1)


def _snippet_scores(model, skel_feat, clip_feat, forward_fn, T=32):
    n = skel_feat.shape[0]
    chunks = []
    with torch.no_grad():
        for s in range(0, n, T):
            e = min(s + T, n)
            sk = torch.from_numpy(skel_feat[s:e].astype(np.float32)).unsqueeze(0).to(DEVICE)
            cl = torch.from_numpy(clip_feat[s:e].astype(np.float32)).unsqueeze(0).to(DEVICE)
            sc = forward_fn(model, sk, cl) if forward_fn else model(skel=sk, clip=cl)
            chunks.append(sc.squeeze(0).cpu().numpy())
    return np.concatenate(chunks)


def score(model, skels, clips, vids, forward_fn=None):
    """source-only style scoring of (possibly transformed) feats -> (frame%, video%)."""
    frames_map, labels_map, cats_map = {}, {}, {}
    vs, vl = [], []
    for vid in vids:
        sc = _snippet_scores(model, skels[vid], clips[vid], forward_fn)
        nf = len(sc) * 64 * 10
        frames_map[vid] = snippet_to_frame(sc, nf, snippet_window=64, upsample_factor=10)
        if vid in _ANNOS:
            labels_map[vid] = frame_labels(_ANNOS[vid], nf); cats_map[vid] = _ANNOS[vid].category
        else:
            labels_map[vid] = np.zeros(nf, dtype=np.int64); cats_map[vid] = "Normal"
        vs.append(_video_score(sc)); vl.append(0 if vid.startswith("Normal") else 1)
    m = compute_frame_metrics(frames_map, labels_map, cats_map)
    return float(m["auc"]) * 100.0, float(roc_auc_score(vl, vs)) * 100.0


def analyze(per_condition):
    """per_condition: {key: {src_auc, strat_auc, src_vauc, strat_vauc}}.
    Honest summary: tuning-free mean delta + brightness-damage + per-family."""
    keys = list(per_condition)
    d = {k: per_condition[k]["strat_auc"] - per_condition[k]["src_auc"] for k in keys}
    fam = {}
    for c in CORRUPTIONS:
        ks = [k for k in keys if k.startswith(c)]
        if ks:
            fam[c] = float(np.mean([d[k] for k in ks]))
    bright = [d[k] for k in keys if k.startswith("brightness")]
    return {
        "mean_delta": float(np.mean(list(d.values()))),
        "n_positive": int(sum(v > 0 for v in d.values())),
        "n_total": len(d),
        "per_family_delta": fam,
        "brightness_damage": float(np.mean(bright)) if bright else None,
        "worst_condition": min(d, key=d.get),
        "worst_delta": float(min(d.values())),
        "best_condition": max(d, key=d.get),
        "best_delta": float(max(d.values())),
        "per_condition_delta": {k: round(v, 2) for k, v in d.items()},
    }
