"""TEMPLATE for a TTA-boost strategy screen (throwaway).

COPY this to scripts/_tmp_strat_<yourname>.py and edit ONLY the `strategy()`
function. Run it once per backbone:
    python scripts/_tmp_strat_<name>.py --backbone clip-vit-b-16   --out results/_coral_derisk/strat_<name>_clip.json
    python scripts/_tmp_strat_<name>.py --backbone siglip2-so400m  --out results/_coral_derisk/strat_<name>_so400m.json
Each call screens 4 families x sev{3,5} = 8 conditions and finishes in <9 min.

HONESTY RULE: the transform must be LABEL-FREE and TUNING-FREE (no test labels,
no hyperparameter tuned by maximizing test AUC). Any knob must be set by a stated
principle (e.g. 2-sigma threshold, a fixed ratio) computed from features only.
Then the reported test-C delta is automatically honest (no val-C needed).

Context available inside strategy():
  cond.skels[v] [N,256], cond.clips[v] [N,Dvl]  (per-video corrupted features)
  cond.vids, cond.ctype, cond.sev, cond.skel_corrupt
  cond.mu_t_clip,cond.C_t_clip,cond.mu_t_skel,cond.C_t_skel  (transductive test stats)
  st["model"]  (GatedFusion; layers skel_proj/ln_skel/clip_proj/ln_clip/gate/ln_fused/head)
  H.source_stats(bb,'clip'|'skel') -> (mu_s,C_s)  clean-TRAIN, cached
  H.shift_stats(mu_s,C_s,mu_t,C_t) -> dict(dmu,z,sd_s,sd_t,var_ratio,frac_var_shift)
  H._coral_W(mu_t,C_t,mu_s,C_s,beta), H._apply(X,mu_t,mu_s,W)   (shrunk-CORAL primitives)
  H.ref_forward(model,skel,clip)  (exact GatedFusion forward — copy+edit for model strategies)
"""
import argparse
import json
import pathlib
import numpy as np
import torch
import _tmp_tta_harness as H

# Fixed, label-free constant. STATED PRINCIPLE (no AUC consulted):
# at a canonical 1-sigma per-channel VL mean shift (clipZ=1) with a clean
# skeleton (skelZ~0), trust the clip stream HALF as much: 1/(1+c*1)=1/2 => c=1.
C_CONST = 1.0


def _stream_meanZ(mu_s, C_s, mu_t, C_t):
    """Mean absolute per-channel mean-shift z-score (feature-only descriptor)."""
    return float(np.mean(np.abs(H.shift_stats(mu_s, C_s, mu_t, C_t)["z"])))


def strategy(cond, st):
    """S4 — corruption-aware fusion reweighting (model strategy, F4-safe).

    Downweight the clip contribution by a scalar w in (0,1] applied to p_clip
    AFTER ln_clip, in BOTH the fused term and the residual highway. w is set
    label-free from the detected VL-vs-skeleton shift ratio: large clip shift
    relative to a clean skeleton -> small w (lean on the clean skeleton).

        w = (1 + c*skelZ) / (1 + c*clipZ),  clamped to (0, 1],  c = C_CONST (=1)

    Clean skeleton (skelZ~0) + shifted clip -> w = 1/(1+c*clipZ) < 1.
    Both streams shifted (motion/jpeg) -> w ~ 1 (don't over-trust a corrupt skel).
    """
    bb = cond.bb
    mu_s_clip, C_s_clip = H.source_stats(bb, "clip")
    mu_s_skel, C_s_skel = H.source_stats(bb, "skel")
    clipZ = _stream_meanZ(mu_s_clip, C_s_clip, cond.mu_t_clip, cond.C_t_clip)
    skelZ = _stream_meanZ(mu_s_skel, C_s_skel, cond.mu_t_skel, cond.C_t_skel)
    w = (1.0 + C_CONST * skelZ) / (1.0 + C_CONST * clipZ)
    w = float(min(1.0, max(0.0, w)))
    print(f"    [S4] {cond.ctype}_{cond.sev}: clipZ={clipZ:.3f} skelZ={skelZ:.3f} w={w:.4f}",
          flush=True)

    def my_forward(model, skel, clip):
        # exact ref_forward, but scale p_clip by w after ln_clip (F4-safe).
        p_skel = model.ln_skel(model.skel_proj(skel))
        p_clip = model.ln_clip(model.clip_proj(clip))
        pc = w * p_clip
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        fused = g * p_skel + (1.0 - g) * pc
        residual = fused + p_skel + pc
        out = model.ln_fused(residual)
        return model.head(out).squeeze(-1)

    return cond.skels, cond.clips, my_forward


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
