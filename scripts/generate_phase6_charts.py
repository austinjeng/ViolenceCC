#!/usr/bin/env python
"""
Phase 6 Analysis & Visualization -- Thesis-Quality Figures
=========================================================
Generates thesis-ready PNG figures: temporal curves, corruption heatmaps,
cross-dataset comparisons, per-category distributions, and more.

Usage:
    conda activate vcc-main
    python scripts/generate_phase6_charts.py

Output: results/phase6_charts/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# --- Project Setup -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eval.ucf_annotations import parse_annotations, frame_labels
from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels

# --- Style -------------------------------------------------------------------
DPI = 150
FIG_STD = (12, 7)
FIG_WIDE = (16, 9)
FIG_SMALL = (9, 6)
TITLE_SZ = 18
LABEL_SZ = 14
TICK_SZ = 12
VAL_SZ = 11

sns.set_theme(
    style="whitegrid",
    font_scale=1.1,
    rc={
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "grid.alpha": 0.3,
        "font.family": "sans-serif",
    },
)

# --- Variant Definitions -----------------------------------------------------
VCOLORS = {
    "skeleton_only": "#64748B",
    "clip_only": "#3B82F6",
    "late_fusion": "#F59E0B",
    "gated_fusion": "#EF4444",
}
VLABELS = {
    "skeleton_only": "Skeleton Only",
    "clip_only": "CLIP Only",
    "late_fusion": "Late Fusion",
    "gated_fusion": "Gated Fusion",
}

UCF_RUNS = {
    "skeleton_only": "ucf_skeleton_only_s42",
    "clip_only": "ucf_clip_only_s42",
    "late_fusion": "ucf_late_fusion_s42",
    "gated_fusion": "ucf_gated_fusion_s42",
}
XD_RUNS = {
    "skeleton_only": "xd_skeleton_only_s42",
    "clip_only": "xd_clip_only_s42",
    "late_fusion": "xd_late_fusion_s42",
    "gated_fusion": "xd_gated_fusion_s42",
}

RESULTS_DIR = PROJECT_ROOT / "results"
OUT_DIR = RESULTS_DIR / "phase6_charts"


# --- Helpers -----------------------------------------------------------------

def _save(fig, subdir, name):
    p = OUT_DIR / subdir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"    -> {p.relative_to(RESULTS_DIR)}")


# --- Data Loading ------------------------------------------------------------

def load_all_scores() -> dict:
    """Load eval_scores.npz for all 8 runs (4 UCF + 4 XD).

    Returns dict {run_name: {video_id: scores_array}}.
    Scores are ALREADY frame-level (post snippet_to_frame expansion).
    Do NOT re-expand with snippet_to_frame().
    """
    all_scores = {}

    for runs_dict in (UCF_RUNS, XD_RUNS):
        for variant, run_name in runs_dict.items():
            sp = RESULTS_DIR / run_name / "eval_scores.npz"
            if not sp.exists():
                print(f"  SKIP {run_name}: no eval_scores.npz")
                continue
            npz = np.load(sp)
            scores_dict = {vid: npz[vid] for vid in npz.files}
            all_scores[run_name] = scores_dict
            print(f"  Loaded {run_name}: {len(scores_dict)} videos")

    return all_scores


def get_gt_intervals(anno):
    """Extract GT anomaly intervals as (start, end) pairs.

    For UCF: iterate anno.intervals, collect (start, end) where start is not None.
    For XD: iterate anno.intervals, collect all (start, end) tuples.
    """
    intervals = []
    for pair in anno.intervals:
        s, e = pair
        if s is not None:
            intervals.append((int(s), int(e)))
    return intervals


# --- Video Selection ---------------------------------------------------------

def select_best_detection_videos(
    dataset_prefix: str,
    n_videos: int,
    runs_dict: dict,
    annos: dict,
    label_fn,
    all_scores: dict,
) -> list:
    """Select videos with clearest anomaly score spikes aligned with GT (D-01).

    Heuristic: maximize (mean_score_in_anomaly_region - mean_score_in_normal_region)
    for the Gated Fusion variant. Greedily spans different categories (D-03).

    Asserts each selected video exists in ALL 4 variant npz files (Pitfall 6).
    """
    gated_run = runs_dict["gated_fusion"]
    gated_scores = all_scores.get(gated_run, {})

    candidates = []
    for vid, scores in gated_scores.items():
        if vid not in annos:
            continue  # skip normal videos (XD normals omitted from annotations)
        labels = label_fn(annos[vid], len(scores))
        if labels.sum() == 0:
            continue  # no anomaly frames

        anom_mean = float(scores[labels == 1].mean())
        norm_scores = scores[labels == 0]
        if len(norm_scores) == 0:
            continue  # skip videos with no normal frames (all anomalous)
        norm_mean = float(norm_scores.mean())
        separation = anom_mean - norm_mean
        candidates.append((vid, separation, annos[vid].category))

    # Sort by separation descending, pick top N spanning different categories (D-03)
    candidates.sort(key=lambda x: -x[1])
    selected = []
    categories_used = set()
    for vid, sep, cat in candidates:
        if cat not in categories_used or len(selected) < n_videos:
            selected.append(vid)
            categories_used.add(cat)
        if len(selected) >= n_videos:
            break

    # Assert each selected video exists in ALL 4 variant npz files (Pitfall 6)
    for vid in selected:
        for variant, run_name in runs_dict.items():
            run_scores = all_scores.get(run_name, {})
            assert vid in run_scores, (
                f"Video {vid} missing from {run_name} eval_scores.npz"
            )

    return selected


# --- Section A: Temporal Curves ----------------------------------------------

def chart_A_temporal(
    idx: int,
    video_id: str,
    scores_by_variant: dict,
    gt_intervals: list,
    n_frames: int,
    dataset_label: str,
):
    """Plot anomaly score temporal curve for one video with 4-variant overlay + GT shading.

    Per D-04: overlay all 4 model variants on the same axes.
    Per D-05: GT intervals as semi-transparent red shaded bands.
    Per D-06: X-axis = frame number, Y-axis = anomaly score [0, 1].
    """
    fig, ax = plt.subplots(figsize=(16, 5))
    frames = np.arange(n_frames)

    # GT shading (D-05): semi-transparent red bands
    for start, end in gt_intervals:
        end_clamped = min(end, n_frames)
        start_clamped = max(0, start)
        ax.axvspan(start_clamped, end_clamped, alpha=0.15, color="red", label="_nolegend_")
    # Single legend entry for GT
    ax.axvspan(0, 0, alpha=0.15, color="red", label="Ground Truth")

    # Overlay 4 variants (D-04)
    for variant in ["skeleton_only", "clip_only", "late_fusion", "gated_fusion"]:
        scores = scores_by_variant[variant]
        ax.plot(
            frames, scores,
            color=VCOLORS[variant],
            label=VLABELS[variant],
            linewidth=1.5,
            alpha=0.85,
        )

    ax.set_xlabel("Frame Number", fontsize=LABEL_SZ)
    ax.set_ylabel("Anomaly Score", fontsize=LABEL_SZ)
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0, n_frames)
    ax.tick_params(labelsize=TICK_SZ)
    ax.legend(fontsize=11, loc="upper right")
    ax.set_title(
        f"{video_id} ({dataset_label})",
        fontsize=TITLE_SZ,
        fontweight="bold",
    )

    _save(fig, "A_temporal", f"A{idx:02d}_{video_id}.png")


def run_section_A(ucf_annos, xd_annos, all_scores):
    """Generate Section A: Temporal Curves for 3 UCF + 2 XD videos."""
    print("\n[2/4] Section A: Temporal Curves")

    # Select 3 UCF videos (D-02)
    ucf_selected = select_best_detection_videos(
        "ucf", 3, UCF_RUNS, ucf_annos, frame_labels, all_scores
    )
    print(f"  UCF selected videos: {ucf_selected}")
    for vid in ucf_selected:
        cat = ucf_annos[vid].category
        print(f"    {vid} -> category: {cat}")

    # Select 2 XD videos (D-02)
    xd_selected = select_best_detection_videos(
        "xd", 2, XD_RUNS, xd_annos, xd_frame_labels, all_scores
    )
    print(f"  XD selected videos: {xd_selected}")
    for vid in xd_selected:
        cat = xd_annos[vid].category
        print(f"    {vid} -> category: {cat}")

    # Generate temporal curves for UCF videos
    idx = 1
    for vid in ucf_selected:
        anno = ucf_annos[vid]
        gt_intervals = get_gt_intervals(anno)
        # Collect scores from all 4 variants -- scores are ALREADY frame-level
        gated_run = UCF_RUNS["gated_fusion"]
        n_frames = len(all_scores[gated_run][vid])

        scores_by_variant = {}
        for variant, run_name in UCF_RUNS.items():
            s = all_scores[run_name][vid]
            # GT labels must match scores length (Pitfall 2)
            assert len(s) == n_frames, (
                f"{vid} frame count mismatch: {variant}={len(s)} vs gated={n_frames}"
            )
            scores_by_variant[variant] = s

        chart_A_temporal(idx, vid, scores_by_variant, gt_intervals, n_frames, "UCF-Crime")
        idx += 1

    # Generate temporal curves for XD videos
    for vid in xd_selected:
        anno = xd_annos[vid]
        gt_intervals = get_gt_intervals(anno)
        gated_run = XD_RUNS["gated_fusion"]
        n_frames = len(all_scores[gated_run][vid])

        scores_by_variant = {}
        for variant, run_name in XD_RUNS.items():
            s = all_scores[run_name][vid]
            assert len(s) == n_frames, (
                f"{vid} frame count mismatch: {variant}={len(s)} vs gated={n_frames}"
            )
            scores_by_variant[variant] = s

        chart_A_temporal(idx, vid, scores_by_variant, gt_intervals, n_frames, "XD-Violence")
        idx += 1

    return ucf_selected, xd_selected


# --- Section C: Corruption Heatmaps (placeholder for Task 2) ----------------
# Will be filled in Task 2.


# --- Section F: Additional Figures (placeholder for Task 2) ------------------
# Will be filled in Task 2.


# --- Main --------------------------------------------------------------------

def main():
    print("Phase 6 Analysis & Visualization")
    print("=" * 50)
    print(f"Output: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Loading annotations and scores...")
    ucf_annos = parse_annotations(
        PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    )
    xd_annos = parse_xd_annotations(
        PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"
    )
    all_scores = load_all_scores()

    # Section A: Temporal Curves
    ucf_selected, xd_selected = run_section_A(ucf_annos, xd_annos, all_scores)

    print("\n[3/4] Section C: Corruption Heatmaps")
    print("    (placeholder -- will be added in Task 2)")

    print("\n[4/4] Section F: Additional Figures")
    print("    (placeholder -- will be added in Task 2)")

    pngs = list(OUT_DIR.rglob("*.png"))
    print(f"\nDone! Generated {len(pngs)} PNG files in {OUT_DIR}")


if __name__ == "__main__":
    main()
