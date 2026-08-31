"""R2 = R1 + clip-skel rank-AGREEMENT gate (fixes base over-routing).

R1 over-routes when VL score SPREAD collapses but VL ranking is preserved (base
high-sev gaussian: AUC 64 yet clip_std tiny). Fix: route to skeleton only when VL
both collapses AND DISAGREES with the (robust) skeleton ranking.

  w_vl     = clip_std_test / clip_std_clean
  skel_rel = clip((2*skelZ_floor - skelZ)/skelZ_floor, 0, 1)
  agree    = max(0, Spearman(clip_only_scores, skel_only_scores))   # rank agreement, label-free
  lean     = (1 - w_vl) * skel_rel * (1 - agree)
  w_clip   = 1 - lean
Reports R1 (no agreement) and R2 (with agreement) side by side. All 4 bb x 20 cond.
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import argparse, json, time
from pathlib import Path
import numpy as np
import torch
from scipy.stats import spearmanr
import _tmp_tta_harness as H
from _tmp_coral_derisk import _accumulate

FEAT = Path("E:/features/ucf")


def _solo_fwd(zero_skel):
    def f(model, skel, clip):
        if zero_skel:
            p_skel = model.ln_skel(torch.zeros_like(model.skel_proj(skel)))
            p_clip = model.ln_clip(model.clip_proj(clip))
        else:
            p_skel = model.ln_skel(model.skel_proj(skel))
            p_clip = model.ln_clip(torch.zeros_like(model.clip_proj(clip)))
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        out = model.ln_fused(g * p_skel + (1 - g) * p_clip + p_skel + p_clip)
        return model.head(out).squeeze(-1)
    return f


clip_only_fwd = _solo_fwd(zero_skel=True)
skel_only_fwd = _solo_fwd(zero_skel=False)


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


def solo_vec(model, skels, clips, vids, fwd):
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


def load_clean_test(bb):
    prefix = H.BACKBONE_FEATURE_PREFIX[bb]
    skels, clips, vids = {}, {}, []
    for v in H._TEST_IDS:
        cp = FEAT / prefix / f"{v}.npy"; sp = FEAT / "skeleton" / f"{v}.npy"
        if not cp.exists() or not sp.exists():
            continue
        clips[v] = np.load(str(cp)); skels[v] = np.load(str(sp)); vids.append(v)
    return skels, clips, vids


def run(bb):
    t0 = time.time()
    st = H.build(bb); model = st["model"]
    mu_s_s, C_s_s = H.source_stats(bb, "skel")
    cs, cl, cv = load_clean_test(bb)
    clip_std_clean = float(np.std(solo_vec(model, cs, cl, cv, clip_only_fwd)))
    mu_ct_s, C_ct_s, _ = _accumulate(cv, lambda v: cs[v])
    skelZ_floor = meanZ(mu_s_s, C_s_s, mu_ct_s, C_ct_s)
    print(f"[{bb}] clip_std_clean={clip_std_clean:.4f} skelZ_floor={skelZ_floor:.4f} ({time.time()-t0:.0f}s)", flush=True)
    per = {}
    for ct in H.CORRUPTIONS:
        for sev in (1, 2, 3, 4, 5):
            cond = H.load_condition(bb, ct, sev)
            f0, _ = H.score(model, cond.skels, cond.clips, cond.vids)
            cvec = solo_vec(model, cond.skels, cond.clips, cond.vids, clip_only_fwd)
            svec = solo_vec(model, cond.skels, cond.clips, cond.vids, skel_only_fwd)
            w_vl = min(1.0, max(0.0, float(np.std(cvec)) / clip_std_clean))
            skelZ = meanZ(mu_s_s, C_s_s, cond.mu_t_skel, cond.C_t_skel)
            skel_rel = min(1.0, max(0.0, (2 * skelZ_floor - skelZ) / skelZ_floor)) if skelZ_floor > 1e-9 else 0.0
            rho = spearmanr(cvec, svec).statistic
            agree = 0.0 if np.isnan(rho) else max(0.0, float(rho))
            w_r1 = 1.0 - (1.0 - w_vl) * skel_rel
            w_r2 = 1.0 - (1.0 - w_vl) * skel_rel * (1.0 - agree)
            f_r1, _ = H.score(model, cond.skels, cond.clips, cond.vids, forward_fn=fwd_w(w_r1))
            f_r2, _ = H.score(model, cond.skels, cond.clips, cond.vids, forward_fn=fwd_w(w_r2))
            per[f"{ct}_{sev}"] = {"src": f0, "r1": f_r1, "r2": f_r2, "w_vl": w_vl,
                                  "skel_rel": skel_rel, "agree": agree, "w_r1": w_r1, "w_r2": w_r2,
                                  "d_r1": f_r1 - f0, "d_r2": f_r2 - f0}
            print(f"{bb} {ct}_{sev} src={f0:.2f} r1={f_r1-f0:+.2f}(w{w_r1:.2f}) "
                  f"r2={f_r2-f0:+.2f}(w{w_r2:.2f}) agree={agree:.2f} ({time.time()-t0:.0f}s)", flush=True)
    ks = list(per)
    mean = lambda k: float(np.mean([per[x][k] for x in ks]))
    summ = {"backbone": bb, "src_mean": mean("src"), "r1_delta": mean("d_r1"), "r2_delta": mean("d_r2"),
            "r1_npos": int(sum(per[x]["d_r1"] > 0 for x in ks)),
            "r2_npos": int(sum(per[x]["d_r2"] > 0 for x in ks)),
            "r2_worst": float(min(per[x]["d_r2"] for x in ks))}
    for fam in H.CORRUPTIONS:
        fk = [x for x in ks if x.startswith(fam)]
        summ[f"{fam}_r1"] = float(np.mean([per[x]["d_r1"] for x in fk]))
        summ[f"{fam}_r2"] = float(np.mean([per[x]["d_r2"] for x in fk]))
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
