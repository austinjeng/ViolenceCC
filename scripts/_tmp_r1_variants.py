"""VALIDATION runner: R1 (disc_reweight) across SEEDS and clean-reference SPLIT.

Addresses two audit blockers before paper edits:
  (1) SINGLE-SEED: run seeds {42,123,2024} so Table 3 can report mean+/-std like
      the rest of the paper (base/giant deltas fall within the 0.1-0.4pp seed band).
  (2) CLEAN-REFERENCE: clip_std_clean is computed on CLEAN TEST by default; the
      --clip-ref train variant computes it on CLEAN TRAIN instead, to check the
      headline survives a non-test reference (defuses the oracle-adjacent concern).

Same R1 math as scripts/_tmp_r1_full.py; only the source checkpoint (seed) and the
clip_std_clean reference split vary. skelZ_floor always = clean-train-vs-clean-test
skeleton gap (feature-only, seed-independent).
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import argparse, json, time
from copy import deepcopy
from pathlib import Path
import numpy as np
import torch
import _tmp_tta_harness as H
from _tmp_coral_derisk import _accumulate
from _tmp_r1_full import clip_only_fwd, fwd_w, meanZ, clip_only_std

from src.models.registry import build_model
from src.tta.tent import configure_model
from src.utils.checkpoint import load_checkpoint
from src.utils.config import load_snapshot_as_config
from src.tta.evaluate_tta import _SourceOnlyAdaptor, BACKBONE_FEATURE_PREFIX

FEAT = Path("E:/features/ucf")
RUN_SUFFIX = {"clip-vit-b-16": "", "siglip2-base": "_siglip2",
              "siglip2-so400m": "_so400m", "siglip2-giant": "_giant"}


def build_seed_model(bb, seed):
    run = H._ROOT if False else Path("D:/ViolenceCC") / "results" / f"ucf_gated_fusion{RUN_SUFFIX[bb]}_s{seed}"
    cfg = load_snapshot_as_config(run / "config_snapshot.json")
    model = build_model(**cfg["model"])
    state = load_checkpoint(run / "best_model.pth", device="cpu")
    sd = state.get("model", state) if isinstance(state, dict) else state
    model.load_state_dict(sd, strict=True)
    configure_model(model)
    return model


def load_clean_split(bb, split):
    prefix = BACKBONE_FEATURE_PREFIX[bb]
    ids = [l.strip() for l in (Path("D:/ViolenceCC/data/splits") / f"ucf_{split}.txt").read_text().splitlines() if l.strip()]
    skels, clips, vids = {}, {}, []
    for v in ids:
        cp = FEAT / prefix / f"{v}.npy"; sp = FEAT / "skeleton" / f"{v}.npy"
        if not cp.exists() or not sp.exists():
            continue
        clips[v] = np.load(str(cp)); skels[v] = np.load(str(sp)); vids.append(v)
    return skels, clips, vids


def run(bb, seed, clip_ref):
    t0 = time.time()
    model = build_seed_model(bb, seed)
    mu_s_s, C_s_s = H.source_stats(bb, "skel")  # clean-train skel (seed-independent)
    # clip_std_clean reference (model-dependent): clean test OR clean train
    rsk, rcl, rv = load_clean_split(bb, clip_ref)
    clip_std_clean = clip_only_std(model, rsk, rcl, rv)
    # skelZ_floor always from clean-TEST skel gap
    tsk, _, tv = load_clean_split(bb, "test")
    mu_ct_s, C_ct_s, _ = _accumulate(tv, lambda v: tsk[v])
    skelZ_floor = meanZ(mu_s_s, C_s_s, mu_ct_s, C_ct_s)
    print(f"[{bb} s{seed} ref={clip_ref}] clip_std_clean={clip_std_clean:.4f} "
          f"skelZ_floor={skelZ_floor:.4f} ({time.time()-t0:.0f}s)", flush=True)
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
            per[f"{ct}_{sev}"] = {"src": f0, "r1": f1, "w": w, "d": f1 - f0}
    ks = list(per)
    mean = lambda k: float(np.mean([per[x][k] for x in ks]))
    summ = {"backbone": bb, "seed": seed, "clip_ref": clip_ref,
            "src_mean": mean("src"), "r1_delta": mean("d"), "r1_mean": mean("src") + mean("d"),
            "npos": int(sum(per[x]["d"] > 0 for x in ks))}
    for fam in H.CORRUPTIONS:
        fk = [x for x in ks if x.startswith(fam)]
        summ[fam] = float(np.mean([per[x]["d"] for x in fk]))
    return per, summ


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--clip-ref", default="test", choices=["test", "train"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    per, summ = run(a.backbone, a.seed, a.clip_ref)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"summary": summ, "per_condition": per}, indent=2))
    print("SUMMARY " + json.dumps(summ), flush=True)
