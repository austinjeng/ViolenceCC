"""STRATEGY S2 — Selective shifted-channel restoration (rank-preserving). THROWAWAY.

Diagonal per-channel NORM (mean + optional variance) applied ONLY to channels
whose mean-shift z-score |z| (H.shift_stats) exceeds a FIXED threshold Z_THR=2.0.
Variance is restored ONLY where |log(var_ratio)| exceeds a FIXED threshold
LV_THR=log(1.5) (i.e. test sd differs from clean sd by >1.5x). Every other
channel is left EXACTLY unchanged.

Rationale wrt the documented failure modes:
  F3 (rank disruption from whitening): diagonal, per-channel — no rotation, no
     cross-channel mixing, so discriminative DIRECTIONS are preserved.
  F1 (damages robust corruptions): near-identity when few channels shift
     (brightness should touch very few channels), so it does not wreck what is
     not broken.
  F4 (ln_clip nulls input mean restore): mean restoration on the clip INPUT is
     partially nulled by ln_clip's per-token re-normalisation, but per-channel
     VARIANCE restoration (rescaling) survives LN's affine far better, and the
     selective per-channel mean still perturbs the projection input non-globally.

HONESTY: Z_THR=2.0 and LV_THR=log(1.5) are FIXED principled thresholds computed
from clean-train vs transductive-test feature stats only — no test labels, no
tuning on test AUC. Transductive test stats (mean/var of the test split) are
allowed (standard TTA), the threshold itself is not data-fit.
"""
import argparse
import json
import pathlib
import numpy as np
import _tmp_tta_harness as H

import os as _os
Z_THR = float(_os.environ.get("S2_ZTHR", 2.0))         # restore mean where |mean-shift z| > 2 sigma
# variance mode: 'off' = mean-only; 'thr' = restore var where |log var_ratio|>LV_THR
_VMODE = _os.environ.get("S2_VMODE", "thr")
LV_THR = float(_os.environ.get("S2_LVTHR", np.log(2.0)))  # restore var where sd ratio > 2.0x

# accumulate channel-correction counts for reporting
_REPORT = {}


def _selective_diag(X, mu_s, sd_s, mu_t, sd_t, z, var_ratio, tag):
    """Per-channel diagonal restore on the shifted channels only; identity else.
    X: [N, D] (float32). Returns transformed copy."""
    D = X.shape[1]
    mean_mask = np.abs(z) > Z_THR
    if _VMODE == "off":
        var_mask = np.zeros(D, dtype=bool)
    else:
        var_mask = np.abs(np.log(var_ratio + 1e-12)) > LV_THR
    # per-channel affine: x' = (x - mu_t)*scale + mu_s'  where for unshifted-mean
    # channels mu_s' collapses back so the channel is left identical.
    scale = np.ones(D, dtype=np.float64)
    scale[var_mask] = (sd_s[var_mask] / np.clip(sd_t[var_mask], 1e-12, None))
    # mean target: shifted-mean channels -> mu_s ; else keep own mu_t (identity center)
    center_t = np.where(mean_mask | var_mask, mu_t, 0.0)
    add_back = np.where(mean_mask, mu_s, 0.0) + np.where(~mean_mask & var_mask, mu_t, 0.0)
    # For channels with neither mask: scale=1, center_t=0, add_back=0 -> x' = x (identity).
    Xt = X.astype(np.float64)
    Xt = (Xt - center_t) * scale + add_back
    _REPORT[tag] = {"n_mean": int(mean_mask.sum()),
                    "n_var": int(var_mask.sum()),
                    "D": int(D)}
    return Xt.astype(np.float32)


def strategy(cond, st):
    # ---- CLIP (VL) stream: always corrupted ----
    mu_s_c, C_s_c = H.source_stats(cond.bb, "clip")
    ss_c = H.shift_stats(mu_s_c, C_s_c, cond.mu_t_clip, cond.C_t_clip)
    clips = {}
    tag_c = f"{cond.ctype}_{cond.sev}_clip"
    for v in cond.vids:
        clips[v] = _selective_diag(
            cond.clips[v], mu_s_c, ss_c["sd_s"], cond.mu_t_clip, ss_c["sd_t"],
            ss_c["z"], ss_c["var_ratio"], tag_c)

    # ---- SKELETON stream: only if corrupted for this condition ----
    if cond.skel_corrupt:
        mu_s_s, C_s_s = H.source_stats(cond.bb, "skel")
        ss_s = H.shift_stats(mu_s_s, C_s_s, cond.mu_t_skel, cond.C_t_skel)
        skels = {}
        tag_s = f"{cond.ctype}_{cond.sev}_skel"
        for v in cond.vids:
            skels[v] = _selective_diag(
                cond.skels[v], mu_s_s, ss_s["sd_s"], cond.mu_t_skel, ss_s["sd_t"],
                ss_s["z"], ss_s["var_ratio"], tag_s)
    else:
        skels = cond.skels

    return skels, clips, None


def run(bb, sevs):
    st = H.build(bb)
    model = st["model"]
    per = {}
    for ctype in H.CORRUPTIONS:
        for sev in sevs:
            cond = H.load_condition(bb, ctype, sev)
            f0, v0 = H.score(model, cond.skels, cond.clips, cond.vids)
            sk, cl, fwd = strategy(cond, st)
            f1, v1 = H.score(model, sk, cl, cond.vids, forward_fn=fwd)
            per[f"{ctype}_{sev}"] = {"src_auc": f0, "strat_auc": f1,
                                     "src_vauc": v0, "strat_vauc": v1}
            rep = _REPORT.get(f"{ctype}_{sev}_clip", {})
            print(f"  {bb} {ctype}_{sev}: src={f0:.2f} strat={f1:.2f} d={f1-f0:+.2f}"
                  f"  [clip n_mean={rep.get('n_mean')}/{rep.get('D')} "
                  f"n_var={rep.get('n_var')}]", flush=True)
    return per


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--severities", default="3,5")
    a = ap.parse_args()
    per = run(a.backbone, tuple(int(x) for x in a.severities.split(",")))
    summ = H.analyze(per)
    summ["channel_report"] = _REPORT
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps({"backbone": a.backbone, "summary": summ,
                                               "per_condition": per}, indent=2))
    print(json.dumps({"backbone": a.backbone, **{k: v for k, v in summ.items()
                                                 if k != "channel_report"}}))
