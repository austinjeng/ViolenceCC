"""STRATEGY S1 — Shift-gated adaptive restoration (label-free, tuning-free).

Idea: apply shrunk-CORAL to the (shifted) clip stream, but
  (a) modulate restoration STRENGTH by detected shift magnitude (mean|z|), so a
      tiny shift -> near-identity (protects already-robust brightness, fixes F1);
      a large shift -> full restoration. Saturating gate on 1-sigma..2-sigma.
  (b) pick the diagonal<->full-covariance point (beta) per condition from a
      label-free signal: off-diagonal vs diagonal magnitude of (C_t - C_s).
      Off-diagonal-dominant (cross-channel cov shift, e.g. jpeg) -> full cov
      (beta=0, fixes F2); else diagonal-only restoration (beta=1).

ALL knobs are fixed by stated STATISTICAL principles computed from FEATURES ONLY
(no test labels, no AUC tuning). The shift descriptor is the 2-SIGMA OUTLIER MASS
frac = fraction of channels with |z| > 2 (per-channel mean-shift z-score). Under a
no-shift Gaussian null, a channel exceeds 2-sigma with prob 0.0455; an honest shift
detector fires only when the observed outlier mass EXCEEDS this chance rate. This
naturally protects already-robust corruptions (brightness frac=0.000 -> identity).
  - strength gate: alpha = clip((frac - 0.0455)/(0.1364 - 0.0455), 0, 1)
        frac_null = 0.0455  (theoretical 2-sigma tail mass under no shift)
        frac_full = 0.1364  (= 3 x null rate: clearly-anomalous outlier mass -> full)
  - covariance point: r = ||offdiag(C_t-C_s)||_F / ||diag(C_t-C_s)||_2
        r > 1.0 (off-diag dominates diag) -> beta = 0 (full covariance)
        else                              -> beta = 1 (diagonal-only)
        threshold 1.0 is the natural off-diag-dominates-diag crossover.
  - final = (1-alpha)*X + alpha*CORAL(X)
Skeleton stream transformed with the same logic ONLY if cond.skel_corrupt.
"""
import argparse
import json
import pathlib
import numpy as np
import _tmp_tta_harness as H

FRAC_NULL = 0.0455   # 2-sigma tail mass under a no-shift Gaussian null
FRAC_FULL = 0.1364   # = 3 x null: clearly-anomalous 2-sigma outlier mass -> full restore
R_THRESH = 1.0       # off-diag dominates diag -> use full covariance


def _gate_and_beta(mu_s, C_s, mu_t, C_t):
    """Label-free: return (alpha in [0,1], beta in {0,1}) from feature stats only."""
    sh = H.shift_stats(mu_s, C_s, mu_t, C_t)
    frac2 = float(np.mean(np.abs(sh["z"]) > 2.0))          # 2-sigma outlier mass
    alpha = float(np.clip((frac2 - FRAC_NULL) / (FRAC_FULL - FRAC_NULL), 0.0, 1.0))

    D = C_t - C_s
    diag_mag = float(np.linalg.norm(np.diag(D)))           # per-channel variance shift
    off = D - np.diag(np.diag(D))
    off_mag = float(np.linalg.norm(off))                   # cross-channel cov shift
    r = off_mag / (diag_mag + 1e-12)
    beta = 0.0 if r > R_THRESH else 1.0
    return alpha, beta, frac2, r


def _restore_stream(X_map, vids, mu_t, C_t, mu_s, C_s):
    alpha, beta, _, _ = _gate_and_beta(mu_s, C_s, mu_t, C_t)
    if alpha <= 0.0:
        return X_map  # near identity -> protect robust conditions, skip work
    W = H._coral_W(mu_t, C_t, mu_s, C_s, beta)
    out = {}
    for v in vids:
        X = X_map[v]
        Xr = H._apply(X, mu_t, mu_s, W)
        out[v] = ((1.0 - alpha) * X.astype(np.float32) + alpha * Xr).astype(np.float32)
    return out


def strategy(cond, st):
    bb = cond.bb
    # --- clip stream (always shifted by the corruption) ---
    mu_s_c, C_s_c = H.source_stats(bb, "clip")
    clips = _restore_stream(cond.clips, cond.vids,
                            cond.mu_t_clip, cond.C_t_clip, mu_s_c, C_s_c)
    # --- skeleton stream (only when actually corrupted) ---
    if cond.skel_corrupt:
        mu_s_s, C_s_s = H.source_stats(bb, "skel")
        skels = _restore_stream(cond.skels, cond.vids,
                                cond.mu_t_skel, cond.C_t_skel, mu_s_s, C_s_s)
    else:
        skels = cond.skels
    return skels, clips, None  # feature-space strategy


def run(bb, sevs):
    st = H.build(bb)
    model = st["model"]
    per = {}
    for ctype in H.CORRUPTIONS:
        for sev in sevs:
            cond = H.load_condition(bb, ctype, sev)
            f0, v0 = H.score(model, cond.skels, cond.clips, cond.vids)
            # diagnostics (label-free signals actually used)
            mu_s_c, C_s_c = H.source_stats(bb, "clip")
            a, b, fr, r = _gate_and_beta(mu_s_c, C_s_c, cond.mu_t_clip, cond.C_t_clip)
            sk, cl, fwd = strategy(cond, st)
            f1, v1 = H.score(model, sk, cl, cond.vids, forward_fn=fwd)
            per[f"{ctype}_{sev}"] = {"src_auc": f0, "strat_auc": f1,
                                     "src_vauc": v0, "strat_vauc": v1,
                                     "alpha": round(a, 3), "beta": b,
                                     "frac2sig": round(fr, 3), "offdiag_ratio": round(r, 3)}
            print(f"  {bb} {ctype}_{sev}: src={f0:.2f} strat={f1:.2f} d={f1-f0:+.2f} "
                  f"[alpha={a:.2f} beta={b:.0f} frac2={fr:.3f} r={r:.2f}]", flush=True)
    return per


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--severities", default="3,5")
    a = ap.parse_args()
    per = run(a.backbone, tuple(int(x) for x in a.severities.split(",")))
    summ = H.analyze(per)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps({"backbone": a.backbone, "summary": summ,
                                               "per_condition": per}, indent=2))
    print(json.dumps({"backbone": a.backbone, **summ}))
