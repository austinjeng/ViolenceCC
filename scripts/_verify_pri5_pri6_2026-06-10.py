"""Adversarial verification of Pri 5 (TTA breakdown) and Pri 6 (bootstrap CI).

CPU-only. numpy / sklearn / json only. No torch.

Pri 5: recompute TTA gaussian-family deltas from results/_coral_derisk/r1full_*.json
        (seed-42 per_condition 'd' = r1 - src) and the SO400M gaussian 3-seed value.
Pri 6: independently recompute pooled frame-level UCF AUC for
        results/ucf_gated_fusion_giant_s42 by reconstructing labels exactly as
        src/evaluate.py _build_frame_arrays UCF path does, then confirm it equals
        0.8249043114503092 within 1e-4.
"""
import json
import os
import sys

import numpy as np
from sklearn.metrics import roc_auc_score

np.random.seed(12345)  # determinism (not used for the deterministic checks below)

ROOT = "D:/ViolenceCC"
OUT = os.path.join(ROOT, "results", "_analysis_2026-06-10")
os.makedirs(OUT, exist_ok=True)

# Make torch-free helpers importable.
sys.path.insert(0, ROOT)
from src.eval.ucf_annotations import frame_labels, parse_annotations  # noqa: E402

report = {}

# ===========================================================================
# Pri 5 — TTA breakdown
# ===========================================================================
CORAL = os.path.join(ROOT, "results", "_coral_derisk")
backbones = {
    "clip-vit-b-16": "r1full_clip.json",
    "siglip2-base": "r1full_base.json",
    "siglip2-so400m": "r1full_so400m.json",
    "siglip2-giant": "r1full_giant.json",
}
gauss_keys = [f"gaussian_noise_{i}" for i in range(1, 6)]

per_backbone_gauss_mean = {}
all_gauss_d = []
for bb, fn in backbones.items():
    d = json.load(open(os.path.join(CORAL, fn)))
    pc = d["per_condition"]
    ds = [pc[k]["d"] for k in gauss_keys]
    # sanity: confirm d == r1 - src per condition
    recompute = [pc[k]["r1"] - pc[k]["src"] for k in gauss_keys]
    assert all(abs(a - b) < 1e-9 for a, b in zip(ds, recompute)), f"d != r1-src for {bb}"
    bb_mean = float(np.mean(ds))
    per_backbone_gauss_mean[bb] = bb_mean
    all_gauss_d.extend(ds)

# (i) cross-backbone gaussian-family mean delta
# interpretation A: mean over all 4 backbones of their per-backbone gaussian mean
cross_bb_mean_of_means = float(np.mean(list(per_backbone_gauss_mean.values())))
# interpretation B: pooled mean over all 20 gaussian conditions
pooled_all20 = float(np.mean(all_gauss_d))

# (ii) base seed-42 gaussian_noise_5 d  (claim ~-3.2)
base = json.load(open(os.path.join(CORAL, "r1full_base.json")))
base_gn5_d = base["per_condition"]["gaussian_noise_5"]["d"]

# (iii) SO400M gaussian 3-seed value (claim ~+13.2)
so = json.load(open(os.path.join(CORAL, "r1full_so400m.json")))
so_gn5_d = so["per_condition"]["gaussian_noise_5"]["d"]  # seed-42 only
so_gauss_mean_s42 = float(np.mean([so["per_condition"][k]["d"] for k in gauss_keys]))
so_summary_gaussian = so["summary"]["gaussian_noise"]  # summary field

report["pri5"] = {
    "per_backbone_gaussian_mean_d_seed42": per_backbone_gauss_mean,
    "i_cross_backbone_mean_of_per_backbone_means": cross_bb_mean_of_means,
    "i_pooled_mean_over_20_conditions": pooled_all20,
    "ii_base_seed42_gaussian_noise_5_d": base_gn5_d,
    "iii_so400m_gaussian_noise_5_d_seed42": so_gn5_d,
    "iii_so400m_gaussian_mean_d_seed42": so_gauss_mean_s42,
    "iii_so400m_summary_gaussian_field": so_summary_gaussian,
}

# ===========================================================================
# Pri 6 — pooled frame-level UCF AUC reconstruction
# ===========================================================================
RUN = os.path.join(ROOT, "results", "ucf_gated_fusion_giant_s42")
z = np.load(os.path.join(RUN, "eval_scores.npz"), allow_pickle=True)
em = json.load(open(os.path.join(RUN, "eval_metrics.json")))
claimed_auc = em["auc"]

# Replicate evaluate.py UCF label reconstruction.
SNIPPET_WINDOW = 64
UPSAMPLE = 10
ann_path = os.path.join(ROOT, "data", "annotations", "ucf_temporal.txt")
manifest_path = os.path.join(ROOT, "data", "ucf_total_frames.json")
annos = parse_annotations(ann_path)
manifest = json.loads(open(manifest_path).read())

all_scores, all_labels = [], []
n_videos = 0
len_mismatch = []
no_nframes_source = []
for vid in z.files:
    scores = z[vid].astype(np.float32)  # already frame-level (broadcast)
    n = len(scores)
    # n_frames per evaluate.py: manifest fallback (boundaries_dir unset in snapshot)
    if vid in manifest:
        n_frames = int(manifest[vid]) * UPSAMPLE
    else:
        no_nframes_source.append(vid)
        n_frames = n  # truncated-grid fallback path
    # The stored frame scores must match the n_frames the eval used.
    if n != n_frames:
        len_mismatch.append((vid, n, n_frames))
    # Build labels exactly as evaluate.py (frame_labels for annotated, zeros else)
    if vid in annos:
        lbl = frame_labels(annos[vid], n)
    else:
        lbl = np.zeros(n, dtype=np.int64)
    assert len(scores) == len(lbl), f"C4 mismatch {vid}: {len(scores)} vs {len(lbl)}"
    all_scores.append(scores)
    all_labels.append(lbl)
    n_videos += 1

y_score = np.concatenate(all_scores)
y_true = np.concatenate(all_labels)
recomputed_auc = float(roc_auc_score(y_true, y_score))
auc_diff = abs(recomputed_auc - claimed_auc)

report["pri6"] = {
    "n_videos": n_videos,
    "claimed_n_videos": em["n_videos"],
    "n_frames_total": int(len(y_true)),
    "claimed_n_frames": em["n_frames"],
    "n_positive_frames": int(y_true.sum()),
    "frac_positive": float(y_true.mean()),
    "claimed_auc": claimed_auc,
    "recomputed_pooled_auc": recomputed_auc,
    "abs_diff": auc_diff,
    "within_1e-4": bool(auc_diff < 1e-4),
    "n_len_mismatch_vs_manifest": len(len_mismatch),
    "examples_len_mismatch": len_mismatch[:5],
    "n_videos_missing_from_manifest": len(no_nframes_source),
}

# Bootstrap CI sanity check (video-level resampling, fixed seed)
rng = np.random.default_rng(12345)
vids = list(z.files)
per_vid_s = {v: z[v].astype(np.float32) for v in vids}
per_vid_l = {}
for v in vids:
    n = len(per_vid_s[v])
    per_vid_l[v] = frame_labels(annos[v], n) if v in annos else np.zeros(n, dtype=np.int64)

B = 2000
boots = []
nv = len(vids)
vids_arr = np.array(vids)
for _ in range(B):
    idx = rng.integers(0, nv, size=nv)
    s = np.concatenate([per_vid_s[vids_arr[i]] for i in idx])
    l = np.concatenate([per_vid_l[vids_arr[i]] for i in idx])
    if l.min() == l.max():
        continue
    boots.append(roc_auc_score(l, s))
boots = np.array(boots)
ci_lo, ci_hi = np.percentile(boots, [2.5, 97.5])
report["pri6_bootstrap"] = {
    "B": int(len(boots)),
    "mean": float(boots.mean()),
    "ci95_lo": float(ci_lo),
    "ci95_hi": float(ci_hi),
    "ci_width_pp": float((ci_hi - ci_lo) * 100),
}

with open(os.path.join(OUT, "verify_pri5_pri6.json"), "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
