"""Diagnostic: does a DISCRIMINATIVE signal (solo-stream score spread) distinguish
'VL shifted but still good' (brightness) from 'VL shifted and broken' (gaussian)?
If yes, it can gate aggressive skeleton routing to capture the large skel headroom
WITHOUT wrecking brightness (the wall that sank shift-based routing S5/S7).

For each condition: clip-only score (zero p_skel) and skel-only score (zero p_clip).
Report std (spread) + IQR of pooled snippet scores. Compare to known source AUC.
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import argparse, json
import numpy as np
import torch
import _tmp_tta_harness as H


def clip_only_fwd(model, skel, clip):
    z = torch.zeros_like(model.skel_proj(skel))
    p_skel = model.ln_skel(z)
    p_clip = model.ln_clip(model.clip_proj(clip))
    g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
    out = model.ln_fused(g * p_skel + (1 - g) * p_clip + p_skel + p_clip)
    return model.head(out).squeeze(-1)


def skel_only_fwd(model, skel, clip):
    p_skel = model.ln_skel(model.skel_proj(skel))
    z = torch.zeros_like(model.clip_proj(clip))
    p_clip = model.ln_clip(z)
    g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
    out = model.ln_fused(g * p_skel + (1 - g) * p_clip + p_skel + p_clip)
    return model.head(out).squeeze(-1)


def pooled_scores(model, skels, clips, vids, fwd):
    alls = []
    with torch.no_grad():
        for v in vids:
            n = skels[v].shape[0]
            for s in range(0, n, 32):
                e = min(s + 32, n)
                sk = torch.from_numpy(skels[v][s:e].astype(np.float32)).unsqueeze(0)
                cl = torch.from_numpy(clips[v][s:e].astype(np.float32)).unsqueeze(0)
                alls.append(fwd(model, sk, cl).squeeze(0).numpy())
    return np.concatenate(alls)


def spread(x):
    return {"std": float(np.std(x)), "iqr": float(np.percentile(x, 75) - np.percentile(x, 25))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True)
    a = ap.parse_args()
    bb = a.backbone
    st = H.build(bb); model = st["model"]
    conds = [("gaussian_noise", 5), ("jpeg_compression", 5), ("brightness", 5), ("motion_blur", 5)]
    print(f"=== {bb} (solo-stream score spread; higher = more discriminative) ===", flush=True)
    print(f"{'cond':<18} {'clip_std':>9} {'clip_iqr':>9} {'skel_std':>9} {'skel_iqr':>9}", flush=True)
    out = {}
    for ct, sev in conds:
        cond = H.load_condition(bb, ct, sev)
        cs = pooled_scores(model, cond.skels, cond.clips, cond.vids, clip_only_fwd)
        ss = pooled_scores(model, cond.skels, cond.clips, cond.vids, skel_only_fwd)
        sc, ssk = spread(cs), spread(ss)
        out[f"{ct}_{sev}"] = {"clip": sc, "skel": ssk}
        print(f"{ct+'_'+str(sev):<18} {sc['std']:>9.4f} {sc['iqr']:>9.4f} "
              f"{ssk['std']:>9.4f} {ssk['iqr']:>9.4f}", flush=True)
    print("REF source AUC: gaussian~45-58 (VL broken), jpeg~38-44 (VL broken), "
          "brightness~76-82 (VL good), motion~63-73 (VL ok, skel broken)", flush=True)
    print("JSON " + json.dumps({bb: out}), flush=True)


if __name__ == "__main__":
    main()
