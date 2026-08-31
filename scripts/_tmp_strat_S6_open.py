"""STRATEGY S6_open — low-rank clean-manifold denoising (throwaway).

Idea (candidate ii from the brief, refined):
  Corruptions (gaussian/jpeg/motion) inject energy into directions ORTHOGONAL to
  the clean-train feature manifold. The discriminative violence/normal signal
  lives in the TOP clean-train PCA subspace (high-variance eigvecs of C_s).
  Project corrupted features onto the top-k clean-train eigenvectors to strip
  off-manifold corruption energy while PRESERVING in-subspace ordering.

    P    = V_k V_k^T          (V_k = top-k eigvecs of clean-train C_s)
    x'   = (x - mu_s) @ P + mu_s

Why it can move RANK-based AUC and dodge F1-F4:
  * It is an ORTHOGONAL projection, NOT a whitening. It keeps relative scale and
    ordering WITHIN the kept subspace -> does not reorder discriminative
    directions the way global whitening does (dodges F3).
  * Brightness is a coherent gain/offset that lives largely INSIDE the dominant
    clean manifold, so projection leaves it nearly untouched; only off-manifold
    noise energy (gaussian/jpeg/motion) is removed. This is the F1-safe asymmetry.
  * A single FIXED variance-explained ratio sets k automatically per stream -> no
    per-family strength dial, so no F2 conflict.
  * Projection changes the per-token vector CONTENT (not just a global scale), so
    it is not nulled by ln_clip's per-token re-normalisation (dodges F4); we apply
    it to the raw clip input in feature space.

HONESTY: k is set by a FIXED variance-explained ratio (VAR_KEEP=0.95) on the
clean-TRAIN covariance eigenvalues. No test labels, no test-AUC tuning. The
test-C delta is therefore directly honest.
"""
import argparse
import json
import pathlib
import numpy as np
import _tmp_tta_harness as H

VAR_KEEP = 0.95  # fixed variance-explained ratio -> sets k (stated principle, label-free)


def _proj_topk(C_s, var_keep=VAR_KEEP):
    """Top-k clean-train PCA projector P = V_k V_k^T, k by fixed variance ratio."""
    w, V = np.linalg.eigh(C_s)                 # ascending eigenvalues
    order = np.argsort(w)[::-1]                 # descending
    w = w[order]
    V = V[:, order]
    w = np.clip(w, 0.0, None)
    cum = np.cumsum(w) / max(w.sum(), 1e-12)
    k = int(np.searchsorted(cum, var_keep) + 1)
    k = max(1, min(k, V.shape[1]))
    Vk = V[:, :k]
    P = Vk @ Vk.T                              # [D,D] symmetric projector
    return P.astype(np.float64), k


def strategy(cond, st):
    bb = cond.bb
    # --- clip stream: always corrupted ---
    mu_s_clip, C_s_clip = H.source_stats(bb, "clip")
    P_clip, k_clip = _proj_topk(C_s_clip)
    mu_s_clip = mu_s_clip.astype(np.float64)

    def denoise(X, mu_s, P):
        Xd = X.astype(np.float64)
        return ((Xd - mu_s) @ P + mu_s).astype(np.float32)

    clips = {v: denoise(cond.clips[v], mu_s_clip, P_clip) for v in cond.vids}

    # --- skeleton stream: denoise ONLY when corrupted (matches harness convention) ---
    if cond.skel_corrupt:
        mu_s_skel, C_s_skel = H.source_stats(bb, "skel")
        P_skel, k_skel = _proj_topk(C_s_skel)
        mu_s_skel = mu_s_skel.astype(np.float64)
        skels = {v: denoise(cond.skels[v], mu_s_skel, P_skel) for v in cond.vids}
    else:
        skels = cond.skels  # clean skeleton untouched

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
            print(f"  {bb} {ctype}_{sev}: src={f0:.2f} strat={f1:.2f} d={f1-f0:+.2f}", flush=True)
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
