"""S4 full confirmation: corruption-aware fusion reweighting on ALL 4 backbones x
20 conditions (4 families x sev 1-5), deterministic, label-free/tuning-free.

S4  (basic):  w = (1 + c*skelZ)/(1 + c*clipZ),  c=1   [downweight corrupted VL, lean on skeleton]
S4r (refined): w_r = 1 - (1-w)*gate,  gate = clip((clipZ-skelZ)/clipZ, 0, 1)
              -> downweight vanishes when skeleton is itself shifted (motion/jpeg). Knob-free.
clipZ/skelZ = mean |per-channel mean-shift z| (clean-TRAIN vs transductive whole-condition test).
Applied to p_clip AFTER ln_clip in both fused + residual (F4-safe). No feature restoration.
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import argparse, json, time
from pathlib import Path
import numpy as np
import torch
import _tmp_tta_harness as H

C_CONST = 1.0


def meanZ(mu_s, C_s, mu_t, C_t):
    return float(np.mean(np.abs(H.shift_stats(mu_s, C_s, mu_t, C_t)["z"])))


def fwd_w(w):
    def f(model, skel, clip):
        p_skel = model.ln_skel(model.skel_proj(skel))
        p_clip = model.ln_clip(model.clip_proj(clip))
        pc = w * p_clip
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        out = model.ln_fused(g * p_skel + (1.0 - g) * pc + p_skel + pc)
        return model.head(out).squeeze(-1)
    return f


def run(bb):
    t0 = time.time()
    st = H.build(bb); model = st["model"]
    mu_s_c, C_s_c = H.source_stats(bb, "clip")
    mu_s_s, C_s_s = H.source_stats(bb, "skel")
    per = {}
    for ct in H.CORRUPTIONS:
        for sev in (1, 2, 3, 4, 5):
            cond = H.load_condition(bb, ct, sev)
            clipZ = meanZ(mu_s_c, C_s_c, cond.mu_t_clip, cond.C_t_clip)
            skelZ = meanZ(mu_s_s, C_s_s, cond.mu_t_skel, cond.C_t_skel)
            wb = min(1.0, max(0.0, (1 + C_CONST * skelZ) / (1 + C_CONST * clipZ)))
            gate = min(1.0, max(0.0, (clipZ - skelZ) / clipZ)) if clipZ > 1e-9 else 0.0
            wr = 1.0 - (1.0 - wb) * gate
            f0, v0 = H.score(model, cond.skels, cond.clips, cond.vids)
            f1, _ = H.score(model, cond.skels, cond.clips, cond.vids, forward_fn=fwd_w(wb))
            f2, _ = H.score(model, cond.skels, cond.clips, cond.vids, forward_fn=fwd_w(wr))
            per[f"{ct}_{sev}"] = {"src": f0, "s4": f1, "s4r": f2, "src_vauc": v0,
                                  "clipZ": clipZ, "skelZ": skelZ, "wb": wb, "wr": wr,
                                  "d_s4": f1 - f0, "d_s4r": f2 - f0}
            print(f"{bb} {ct}_{sev} src={f0:.2f} s4={f1:.2f}({f1-f0:+.2f}) "
                  f"s4r={f2:.2f}({f2-f0:+.2f}) wb={wb:.3f} wr={wr:.3f} "
                  f"({time.time()-t0:.0f}s)", flush=True)
    ks = list(per)
    mean = lambda key: float(np.mean([per[k][key] for k in ks]))
    summ = {"backbone": bb, "src_mean": mean("src"),
            "s4_delta": mean("d_s4"), "s4r_delta": mean("d_s4r"),
            "s4_npos": int(sum(per[k]["d_s4"] > 0 for k in ks)),
            "s4r_npos": int(sum(per[k]["d_s4r"] > 0 for k in ks)), "n": len(ks)}
    for fam in H.CORRUPTIONS:
        fk = [k for k in ks if k.startswith(fam)]
        summ[f"{fam}_s4"] = float(np.mean([per[k]["d_s4"] for k in fk]))
        summ[f"{fam}_s4r"] = float(np.mean([per[k]["d_s4r"] for k in fk]))
    return per, summ


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    per, summ = run(a.backbone)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"summary": summ, "per_condition": per}, indent=2))
    print("SUMMARY " + json.dumps(summ), flush=True)
