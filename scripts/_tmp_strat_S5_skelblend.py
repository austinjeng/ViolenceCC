"""STRATEGY S5 — Robust-stream fallback + shift-weighted SCORE blend (throwaway).

MODEL strategy. Produces two snippet-score vectors per video:
  s_full = H.ref_forward (full GatedFusion)
  s_skel = skeleton-DOMINANT forward (p_clip set to ZERO in BOTH fused & residual)
and blends them with a per-condition convex weight alpha:
  s = alpha*s_full + (1-alpha)*s_skel
Because s_full and s_skel differ across frames/videos, the blend CAN REORDER ->
moves frame-AUC (unlike monotone entropy TTA).

LABEL-FREE / TUNING-FREE alpha
------------------------------
Measure cross-stream shift in the PROJECTED (post-clip_proj/post-skel_proj)
feature space (F4: ln re-normalizes per token, so the relevant distribution is
the post-projection one). For each stream compute frac_var_shift phi (mean abs
log std-ratio test-vs-clean-train), obtained analytically:
  mu_z = W@mu + b ;  C_z = W@C@W.T   (W,b = proj weight/bias)
Then the convex weight is the SKELETON's share of total cross-stream shift:
  alpha = phi_skel / (phi_skel + phi_clip)          (alpha=1 if both ~0)
Interpretation: weight each stream by how CLEAN it is relative to the other.
- VL heavily shifted, skel clean (gaussian/brightness) -> alpha->0 (lean skel)
- both shift comparably (motion/jpeg)                  -> alpha->0.5 (balanced)
- nothing shifted                                      -> alpha=1 (full model, no harm)
ZERO tunable scalars: alpha is a pure ratio of two measured shift magnitudes.

DIAGNOSTIC: also prints (a) skel-dominant headroom (s_skel-only frame-AUC) and
the per-condition (phi_clip, phi_skel, alpha) so we can read the mechanism.
"""
import argparse
import json
import pathlib
import numpy as np
import torch
import _tmp_tta_harness as H


# ----- analytic projected-stream shift (label-free) -------------------------
def _proj_stats(mu, C, layer):
    """Push raw stats through a linear layer: mu_z=W mu + b, C_z = W C W^T."""
    W = layer.weight.detach().cpu().numpy().astype(np.float64)   # [out,in]
    b = layer.bias.detach().cpu().numpy().astype(np.float64) if layer.bias is not None else 0.0
    mu_z = W @ mu + b
    C_z = W @ C @ W.T
    return mu_z, C_z


def _phi(mu_s, C_s, mu_t, C_t):
    """frac_var_shift = mean |log(sd_t/sd_s)| in projected space."""
    sd_s = np.sqrt(np.clip(np.diag(C_s), 1e-12, None))
    sd_t = np.sqrt(np.clip(np.diag(C_t), 1e-12, None))
    return float(np.mean(np.abs(np.log(sd_t / sd_s + 1e-12))))


# ----- skeleton-dominant forward (p_clip := 0) ------------------------------
def _make_blend_forward(alpha, model):
    a = float(alpha)

    def my_forward(m, skel, clip):
        # full branch (exact ref_forward)
        p_skel = m.ln_skel(m.skel_proj(skel))
        p_clip = m.ln_clip(m.clip_proj(clip))
        g = torch.sigmoid(m.gate(torch.cat([p_skel, p_clip], dim=-1)))
        fused = g * p_skel + (1.0 - g) * p_clip
        residual = fused + p_skel + p_clip
        s_full = m.head(m.ln_fused(residual)).squeeze(-1)
        # skeleton-dominant branch: p_clip := 0 in BOTH fused and residual
        zc = torch.zeros_like(p_clip)
        g0 = torch.sigmoid(m.gate(torch.cat([p_skel, zc], dim=-1)))
        fused0 = g0 * p_skel + (1.0 - g0) * zc
        residual0 = fused0 + p_skel + zc
        s_skel = m.head(m.ln_fused(residual0)).squeeze(-1)
        return a * s_full + (1.0 - a) * s_skel

    return my_forward


def _make_skel_only_forward(model):
    """DIAGNOSTIC (a): pure skeleton-dominant (alpha=0)."""
    return _make_blend_forward(0.0, model)


def strategy(cond, st):
    model = st["model"]
    bb = cond.bb
    # raw clean-train + test stats per stream
    mu_s_clip, C_s_clip = H.source_stats(bb, "clip")
    mu_s_skel, C_s_skel = H.source_stats(bb, "skel")
    # project through the trained proj layers (analytic)
    mzs_c, Czs_c = _proj_stats(mu_s_clip, C_s_clip, model.clip_proj)
    mzt_c, Czt_c = _proj_stats(cond.mu_t_clip, cond.C_t_clip, model.clip_proj)
    mzs_s, Czs_s = _proj_stats(mu_s_skel, C_s_skel, model.skel_proj)
    mzt_s, Czt_s = _proj_stats(cond.mu_t_skel, cond.C_t_skel, model.skel_proj)
    phi_clip = _phi(mzs_c, Czs_c, mzt_c, Czt_c)
    phi_skel = _phi(mzs_s, Czs_s, mzt_s, Czt_s)
    tot = phi_clip + phi_skel
    alpha = 1.0 if tot < 1e-9 else phi_skel / tot
    print(f"    [S5] {cond.ctype}_{cond.sev}: phi_clip={phi_clip:.4f} "
          f"phi_skel={phi_skel:.4f} alpha={alpha:.4f}", flush=True)
    fwd = _make_blend_forward(alpha, model)
    return cond.skels, cond.clips, fwd


def run(bb, sevs, diag=False):
    st = H.build(bb)
    model = st["model"]
    per = {}
    for ctype in H.CORRUPTIONS:
        for sev in sevs:
            cond = H.load_condition(bb, ctype, sev)
            f0, v0 = H.score(model, cond.skels, cond.clips, cond.vids)
            if diag:
                # (a) skeleton-dominant headroom
                fsk, vsk = H.score(model, cond.skels, cond.clips, cond.vids,
                                   forward_fn=_make_skel_only_forward(model))
                print(f"    [S5-headroom] {ctype}_{sev}: src={f0:.2f} "
                      f"skel_only={fsk:.2f} (head={fsk - f0:+.2f})", flush=True)
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
    ap.add_argument("--severities", default="5")
    ap.add_argument("--diag", action="store_true")
    a = ap.parse_args()
    per = run(a.backbone, tuple(int(x) for x in a.severities.split(",")), diag=a.diag)
    summ = H.analyze(per)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps({"backbone": a.backbone, "summary": summ,
                                               "per_condition": per}, indent=2))
    print(json.dumps({"backbone": a.backbone, **summ}))
