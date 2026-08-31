"""R1 — discriminative-reliability routing. Capture the large skeleton headroom on
VL-collapse corruptions WITHOUT wrecking brightness/motion, using a DISCRIMINATIVE
signal (VL solo-score spread) instead of a distributional one.

  w_vl     = clip_std_test / clip_std_clean   (retained VL discriminative spread; label-free)
  skel_rel = clip((2*skelZ_floor - skelZ)/skelZ_floor, 0, 1)   (skeleton reliability; =1 at clean floor)
  lean     = (1 - w_vl) * skel_rel            (lean on skeleton only if VL collapsed AND skeleton clean)
  w_clip   = 1 - lean                          (scale p_clip after ln_clip, both fused+residual; F4-safe)

clip_std_clean and skelZ_floor are computed from CLEAN TEST features (label-free, the
irreducible domain gap). gaussian/brightness reuse the clean skeleton so their skelZ ~= floor
-> skel_rel=1; motion/jpeg re-extract skeleton -> skelZ>floor -> skel_rel->0 (don't lean).
All 4 backbones x 20 conditions, deterministic.
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import argparse, json, time
from pathlib import Path
import numpy as np
import torch
import _tmp_tta_harness as H
from _tmp_coral_derisk import _accumulate

FEAT = Path("E:/features/ucf")


def clip_only_fwd(model, skel, clip):
    z = torch.zeros_like(model.skel_proj(skel))
    p_skel = model.ln_skel(z)
    p_clip = model.ln_clip(model.clip_proj(clip))
    g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
    out = model.ln_fused(g * p_skel + (1 - g) * p_clip + p_skel + p_clip)
    return model.head(out).squeeze(-1)


def fwd_w(w):
    def f(model, skel, clip):
        p_skel = model.ln_skel(model.skel_proj(skel))
        p_clip = model.ln_clip(model.clip_proj(clip))
        pc = w * p_clip
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        out = model.ln_fused(g * p_skel + (1 - g) * pc + p_skel + pc)
        return model.head(out).squeeze(-1)
    return f


def meanZ(ms, Cs, mt, Ct):
    return float(np.mean(np.abs(H.shift_stats(ms, Cs, mt, Ct)["z"])))


def clip_only_std(model, skels, clips, vids):
    alls = []
    with torch.no_grad():
        for v in vids:
            n = skels[v].shape[0]
            for s in range(0, n, 32):
                e = min(s + 32, n)
                sk = torch.from_numpy(skels[v][s:e].astype(np.float32)).unsqueeze(0)
                cl = torch.from_numpy(clips[v][s:e].astype(np.float32)).unsqueeze(0)
                alls.append(clip_only_fwd(model, sk, cl).squeeze(0).numpy())
    return float(np.std(np.concatenate(alls)))


def load_clean_test(bb):
    prefix = H.BACKBONE_FEATURE_PREFIX[bb]
    skels, clips, vids = {}, {}, []
    for v in H._TEST_IDS:
        cp = FEAT / prefix / f"{v}.npy"
        sp = FEAT / "skeleton" / f"{v}.npy"
        if not cp.exists() or not sp.exists():
            continue
        clips[v] = np.load(str(cp)); skels[v] = np.load(str(sp)); vids.append(v)
    return skels, clips, vids


def run(bb):
    t0 = time.time()
    st = H.build(bb); model = st["model"]
    mu_s_s, C_s_s = H.source_stats(bb, "skel")
    cs, cl, cv = load_clean_test(bb)
    clip_std_clean = clip_only_std(model, cs, cl, cv)
    mu_ct_s, C_ct_s, _ = _accumulate(cv, lambda v: cs[v])
    skelZ_floor = meanZ(mu_s_s, C_s_s, mu_ct_s, C_ct_s)
    print(f"[{bb}] clip_std_clean={clip_std_clean:.4f} skelZ_floor={skelZ_floor:.4f} "
          f"({time.time()-t0:.0f}s)", flush=True)
    per = {}
    for ct in H.CORRUPTIONS:
        for sev in (1, 2, 3, 4, 5):
            cond = H.load_condition(bb, ct, sev)
            f0, _ = H.score(model, cond.skels, cond.clips, cond.vids)
            cstd = clip_only_std(model, cond.skels, cond.clips, cond.vids)
            w_vl = min(1.0, max(0.0, cstd / clip_std_clean))
            skelZ = meanZ(mu_s_s, C_s_s, cond.mu_t_skel, cond.C_t_skel)
            skel_rel = min(1.0, max(0.0, (2 * skelZ_floor - skelZ) / skelZ_floor)) if skelZ_floor > 1e-9 else 0.0
            w = 1.0 - (1.0 - w_vl) * skel_rel
            f1, _ = H.score(model, cond.skels, cond.clips, cond.vids, forward_fn=fwd_w(w))
            per[f"{ct}_{sev}"] = {"src": f0, "r1": f1, "cstd": cstd, "w_vl": w_vl,
                                  "skelZ": skelZ, "skel_rel": skel_rel, "w": w, "d": f1 - f0}
            print(f"{bb} {ct}_{sev} src={f0:.2f} r1={f1:.2f}({f1-f0:+.2f}) "
                  f"w_vl={w_vl:.3f} skel_rel={skel_rel:.3f} w={w:.3f} ({time.time()-t0:.0f}s)", flush=True)
    ks = list(per)
    mean = lambda k: float(np.mean([per[x][k] for x in ks]))
    summ = {"backbone": bb, "src_mean": mean("src"), "r1_delta": mean("d"),
            "r1_npos": int(sum(per[x]["d"] > 0 for x in ks)),
            "clip_std_clean": clip_std_clean, "skelZ_floor": skelZ_floor}
    for fam in H.CORRUPTIONS:
        fk = [x for x in ks if x.startswith(fam)]
        summ[fam] = float(np.mean([per[x]["d"] for x in fk]))
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
