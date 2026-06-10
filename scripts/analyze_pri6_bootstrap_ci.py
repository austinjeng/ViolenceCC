"""Pri 6: video-level bootstrap 95% CIs for headline AUC (UCF) / AP (XD).

CPU-only (numpy + scikit-learn). NO torch / CUDA. Replicates label
reconstruction EXACTLY as src/evaluate.py:_build_frame_arrays does for the
UCF (default) path and the XD fusion ("xd") path, using torch-free helpers
imported from src.eval.

Mandatory sanity gate (run BEFORE bootstrap):
  - UCF: pooled roc_auc_score must equal stored eval_metrics auc within 1e-4.
  - XD:  pooled average_precision_score must equal stored ap within 1e-4.
If the gate fails the label reconstruction is wrong; bootstrap is skipped.

Bootstrap (gate-passing only): resample the SET OF VIDEOS with replacement,
B=2000, rng=default_rng(12345). Each resample pools the chosen videos' frames
and recomputes the metric. CI = [2.5, 97.5] percentiles.

Outputs:
  results/_analysis_2026-06-10/pri6_bootstrap_ci.md
  results/_analysis_2026-06-10/pri6_bootstrap_ci.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# torch-free helpers (verified: ucf_annotations / xd_annotations / snippet_to_frame
# import only numpy / dataclasses / pathlib).
from src.eval.ucf_annotations import frame_labels, parse_annotations
from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels

OUT_DIR = _PROJECT_ROOT / "results" / "_analysis_2026-06-10"
OUT_DIR.mkdir(parents=True, exist_ok=True)

B = 2000
SEED = 12345
GATE_TOL = 1e-4


def _load_scores(run_dir: Path) -> dict:
    """Load eval_scores.npz -> {video_id: float32 array}."""
    npz = np.load(run_dir / "eval_scores.npz")
    return {k: npz[k] for k in npz.files}


def build_ucf_arrays(scores_map: dict):
    """Replicate evaluate.py UCF label reconstruction.

    NOTE: eval_scores.npz stores the FRAME-LEVEL scores (frames_map), already
    broadcast to the full-length grid by evaluate.py (line 478-481). So the
    per-video score array IS the frame grid; n_frames = len(scores). Labels are
    frame_labels(anno, n_frames) for annotated videos and all-zero for videos
    absent from the annotation file (NORMAL). This is exactly what
    compute_frame_metrics consumed to produce the stored auc.

    Verified: sum of len(scores) over the 254 videos == metrics n_frames
    (1,097,050), and len(scores) == manifest_total_frames*10 for every video.
    """
    ann_path = _PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    annos = parse_annotations(ann_path) if ann_path.exists() else {}

    frames_map, labels_map = {}, {}
    n_anno, n_normal = 0, 0
    for vid, scores in scores_map.items():
        n_frames = len(scores)
        if vid in annos:
            labels_map[vid] = frame_labels(annos[vid], n_frames)
            n_anno += 1
        else:
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
            n_normal += 1
        frames_map[vid] = np.asarray(scores, dtype=np.float64)
    return frames_map, labels_map, {"n_annotated": n_anno, "n_normal_default": n_normal}


def build_xd_arrays(scores_map: dict):
    """Replicate evaluate.py XD label reconstruction.

    eval_scores.npz stores the FRAME-LEVEL scores (frames_map) — n_frames =
    len(scores). Videos absent from Wu annotations (the 300 normal test videos)
    -> all-zero labels. Verified: sum of len(scores) == metrics n_frames
    (2,313,024).
    """
    ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"
    annos = parse_xd_annotations(ann_path) if ann_path.exists() else {}

    frames_map, labels_map = {}, {}
    n_abn, n_nor = 0, 0
    for vid, scores in scores_map.items():
        n_frames = len(scores)
        if vid in annos:
            labels_map[vid] = xd_frame_labels(annos[vid], n_frames)
            n_abn += 1
        else:
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
            n_nor += 1
        frames_map[vid] = np.asarray(scores, dtype=np.float64)
    return frames_map, labels_map, {"n_abnormal": n_abn, "n_normal": n_nor}


def pooled_metric(vids, frames_map, labels_map, metric: str) -> float:
    """Pool the given videos' frames and compute AUC or AP."""
    y_s = np.concatenate([frames_map[v] for v in vids])
    y_t = np.concatenate([labels_map[v] for v in vids])
    if metric == "auc":
        return float(roc_auc_score(y_t, y_s))
    return float(average_precision_score(y_t, y_s))


def bootstrap_ci(vids, frames_map, labels_map, metric: str, rng):
    """Video-level bootstrap: resample videos w/ replacement, pool, recompute.

    Returns (lo, hi, mean, all_values). Resamples that are single-class after
    pooling (sklearn cannot compute the metric) are skipped and re-drawn so we
    keep exactly B valid replicates.
    """
    vids = list(vids)
    n = len(vids)
    vals = []
    attempts = 0
    skipped = 0
    while len(vals) < B:
        attempts += 1
        idx = rng.integers(0, n, size=n)
        chosen = [vids[i] for i in idx]
        y_t = np.concatenate([labels_map[v] for v in chosen])
        if y_t.min() == y_t.max():  # single-class pool: metric undefined
            skipped += 1
            continue
        y_s = np.concatenate([frames_map[v] for v in chosen])
        if metric == "auc":
            vals.append(float(roc_auc_score(y_t, y_s)))
        else:
            vals.append(float(average_precision_score(y_t, y_s)))
    vals = np.asarray(vals)
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi), float(vals.mean()), vals, skipped


def run_dataset(name, run_dir, builder, metric, stored_metric):
    scores_map = _load_scores(run_dir)
    frames_map, labels_map, info = builder(scores_map)
    vids = list(scores_map.keys())

    # ---- MANDATORY SANITY GATE ----
    recomputed = pooled_metric(vids, frames_map, labels_map, metric)
    gate_diff = abs(recomputed - stored_metric)
    gate_pass = gate_diff < GATE_TOL

    result = {
        "dataset": name,
        "run_dir": str(run_dir),
        "metric": metric.upper(),
        "n_videos": len(vids),
        "stored_point_estimate": stored_metric,
        "recomputed_point_estimate": recomputed,
        "gate_abs_diff": gate_diff,
        "gate_tol": GATE_TOL,
        "gate_pass": bool(gate_pass),
        "build_info": info,
    }

    if not gate_pass:
        result["bootstrap"] = None
        result["status"] = "GATE FAILED - bootstrap NOT run"
        return result

    rng = np.random.default_rng(SEED)
    lo, hi, mean, vals, skipped = bootstrap_ci(
        vids, frames_map, labels_map, metric, rng
    )
    width_pp = (hi - lo) * 100.0
    inside = lo <= stored_metric <= hi
    result["bootstrap"] = {
        "B": B,
        "rng_seed": SEED,
        "ci_lo": lo,
        "ci_hi": hi,
        "ci_width_pp": width_pp,
        "bootstrap_mean": mean,
        "point_inside_ci": bool(inside),
        "single_class_resamples_skipped": skipped,
        "ci_lo_pct": lo * 100.0,
        "ci_hi_pct": hi * 100.0,
        "stored_pct": stored_metric * 100.0,
    }
    result["status"] = "OK"
    return result


def main():
    ucf_run = _PROJECT_ROOT / "results" / "ucf_gated_fusion_giant_s42"
    xd_run = _PROJECT_ROOT / "results" / "xd_gated_fusion_so400m_s42"

    ucf_stored = json.loads((ucf_run / "eval_metrics.json").read_text())["auc"]
    xd_stored = json.loads((xd_run / "eval_metrics.json").read_text())["ap"]

    ucf = run_dataset("UCF", ucf_run, build_ucf_arrays, "auc", ucf_stored)
    xd = run_dataset("XD", xd_run, build_xd_arrays, "ap", xd_stored)

    payload = {
        "task": "Pri 6 - video-level bootstrap 95% CIs (defense insurance)",
        "primary_seed": 42,
        "bootstrap_B": B,
        "rng_seed": SEED,
        "ucf": ucf,
        "xd": xd,
    }

    (OUT_DIR / "pri6_bootstrap_ci.json").write_text(json.dumps(payload, indent=2))

    # ---- markdown ----
    lines = []
    lines.append("# Pri 6: Video-Level Bootstrap 95% CIs (Defense Insurance)")
    lines.append("")
    lines.append(f"- Primary seed: s42 | Bootstrap B={B} | rng=default_rng({SEED})")
    lines.append("- Resampling unit: VIDEO (resample videos w/ replacement, "
                 "pool their frames, recompute metric).")
    lines.append("- Labels reconstructed exactly as `src/evaluate.py`:`_build_frame_arrays` "
                 "(UCF default path / XD fusion path).")
    lines.append("")
    lines.append("## Sanity gate (pooled recompute vs stored eval_metrics)")
    lines.append("")
    lines.append("| Dataset | Metric | Stored | Recomputed | |diff| | Tol | Pass |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in (ucf, xd):
        lines.append(
            f"| {r['dataset']} | {r['metric']} | {r['stored_point_estimate']:.7f} | "
            f"{r['recomputed_point_estimate']:.7f} | {r['gate_abs_diff']:.2e} | "
            f"{r['gate_tol']:.0e} | {'PASS' if r['gate_pass'] else 'FAIL'} |"
        )
    lines.append("")
    lines.append("## Bootstrap 95% CIs")
    lines.append("")
    if ucf["gate_pass"] and xd["gate_pass"]:
        lines.append("| Dataset | Metric | Point (s42) | CI lo | CI hi | "
                     "Width (pp) | Point inside CI? |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in (ucf, xd):
            b = r["bootstrap"]
            lines.append(
                f"| {r['dataset']} | {r['metric']} | "
                f"{r['stored_point_estimate']*100:.2f}% | {b['ci_lo']*100:.2f}% | "
                f"{b['ci_hi']*100:.2f}% | {b['ci_width_pp']:.2f} | "
                f"{'YES' if b['point_inside_ci'] else 'NO'} |"
            )
        lines.append("")
        ub = ucf["bootstrap"]
        xb = xd["bootstrap"]
        lines.append("### Plain-language")
        lines.append("")
        lines.append(
            f"- **UCF AUC (s42 = {ucf_stored*100:.2f}%)**: 95% CI "
            f"[{ub['ci_lo']*100:.2f}%, {ub['ci_hi']*100:.2f}%], "
            f"width {ub['ci_width_pp']:.2f} pp. Point estimate "
            f"{'INSIDE' if ub['point_inside_ci'] else 'OUTSIDE'} the CI."
        )
        lines.append(
            f"- **XD AP (s42 = {xd_stored*100:.2f}%)**: 95% CI "
            f"[{xb['ci_lo']*100:.2f}%, {xb['ci_hi']*100:.2f}%], "
            f"width {xb['ci_width_pp']:.2f} pp. Point estimate "
            f"{'INSIDE' if xb['point_inside_ci'] else 'OUTSIDE'} the CI."
        )
        lines.append("")
        lines.append("### REVIEW probe reproduce check")
        lines.append("")
        lines.append(
            f"- REVIEW probe estimated UCF-AUC CI width ~12.7 pp. "
            f"Actual UCF-AUC width: **{ub['ci_width_pp']:.2f} pp**."
        )
    else:
        lines.append("GATE FAILED for at least one dataset; bootstrap not run. "
                     "See JSON for details.")
    lines.append("")
    lines.append("## Build provenance")
    lines.append("")
    lines.append(f"- UCF: {ucf['build_info']} (snippet_window=64, upsample=10, "
                 "n_frames from M3 manifest data/ucf_total_frames.json)")
    lines.append(f"- XD: {xd['build_info']} (snippet_window=64, upsample=1, "
                 "n_frames=len(scores)*64; normals absent from Wu file -> zero labels)")

    (OUT_DIR / "pri6_bootstrap_ci.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
