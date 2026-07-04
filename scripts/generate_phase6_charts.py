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
import pickle
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from sklearn.manifold import TSNE
from torch.utils.data import DataLoader

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
from src.models.registry import build_model
from src.utils.checkpoint import load_checkpoint
from src.data.dataset import MILFeatureDataset

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

# --- COCO-17 Skeleton Constants (VIS-02) ------------------------------------
COCO_EDGES = [
    (0, 1), (0, 2), (1, 3), (2, 4),          # face
    (5, 6),                                     # shoulders
    (5, 7), (7, 9),                            # left arm
    (6, 8), (8, 10),                           # right arm
    (5, 11), (6, 12), (11, 12),               # torso
    (11, 13), (13, 15),                        # left leg
    (12, 14), (14, 16),                        # right leg
]

# XD category code to readable name mapping
XD_CAT_NAMES = {
    "B1": "Fighting", "B2": "Shooting", "B4": "Riot",
    "B5": "Abuse", "B6": "Car Accident", "G": "Explosion",
}


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
    print("\n[2/6] Section A: Temporal Curves")

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


# --- Section B: Skeleton Overlays (VIS-02, D-07/08/09) ----------------------

def draw_skeleton(frame, keypoints, scores, conf_threshold=0.3):
    """Draw COCO-17 skeleton on a video frame.

    keypoints: [17, 2] float32 pixel coordinates
    scores: [17] float32 confidence scores
    """
    # Draw edges first (behind keypoints)
    for (i, j) in COCO_EDGES:
        if scores[i] > conf_threshold and scores[j] > conf_threshold:
            pt1 = (int(keypoints[i, 0]), int(keypoints[i, 1]))
            pt2 = (int(keypoints[j, 0]), int(keypoints[j, 1]))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2, cv2.LINE_AA)

    # Draw keypoints
    for k in range(17):
        if scores[k] > conf_threshold:
            pt = (int(keypoints[k, 0]), int(keypoints[k, 1]))
            cv2.circle(frame, pt, 4, (0, 0, 255), -1, cv2.LINE_AA)

    return frame


def create_skeleton_overlay(video_path, skeleton_pkl_path, frame_idx):
    """Extract a frame from video and overlay skeleton keypoints+edges.

    Draws both persons (person_idx=0 and 1) if both have reasonable confidence.
    Returns RGB frame array.
    """
    with open(skeleton_pkl_path, "rb") as f:
        skel = pickle.load(f)

    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"    [WARN] Failed to read frame {frame_idx} from {video_path}")
        return None

    n_persons = skel["keypoint"].shape[0]
    total_frames = skel["keypoint"].shape[1]

    # Clamp frame_idx to skeleton data range
    skel_frame = min(frame_idx, total_frames - 1)

    for person_idx in range(min(n_persons, 2)):
        kps = skel["keypoint"][person_idx, skel_frame]       # [17, 2]
        sc = skel["keypoint_score"][person_idx, skel_frame]  # [17]
        # Only draw if person has at least 5 confident keypoints
        if (sc > 0.3).sum() >= 5:
            draw_skeleton(frame, kps, sc)

    # BGR -> RGB for matplotlib display
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def run_section_B(xd_selected, xd_annos):
    """Generate Section B: Skeleton Overlays on XD-Violence video frames.

    Uses XD-Violence videos (346x640+ MP4s) per D-07/D-08.
    UCF-Crime only has 64x64 PNGs -- not suitable for overlays (Pitfall 3).
    Minimum 3 frames total across selected videos (D-09).
    """
    print("\n[3/6] Section B: Skeleton Overlays")

    xd_video_dir = Path("E:/XD_Violence/test/videos")
    xd_skel_dir = Path("E:/skeletons/xd")

    frame_count = 0
    for vid in xd_selected:
        video_path = xd_video_dir / f"{vid}.mp4"
        skel_path = xd_skel_dir / f"{vid}.pkl"

        if not video_path.exists():
            print(f"    [WARN] Video not found: {video_path}, skipping")
            continue
        if not skel_path.exists():
            print(f"    [WARN] Skeleton not found: {skel_path}, skipping")
            continue

        # Get anomalous frame indices from GT annotations
        if vid not in xd_annos:
            print(f"    [WARN] {vid} not in annotations, skipping")
            continue

        anno = xd_annos[vid]
        gt_intervals = get_gt_intervals(anno)
        if not gt_intervals:
            print(f"    [WARN] {vid} has no anomaly intervals, skipping")
            continue

        # Pick midpoint of each anomaly interval
        for interval_idx, (start, end) in enumerate(gt_intervals):
            midpoint = (start + end) // 2
            frame_rgb = create_skeleton_overlay(video_path, skel_path, midpoint)
            if frame_rgb is None:
                continue

            frame_count += 1
            cat_code = anno.category
            cat_name = XD_CAT_NAMES.get(cat_code, cat_code)
            fig, ax = plt.subplots(figsize=(10, 7))
            ax.imshow(frame_rgb)
            ax.set_title(
                f"{vid}\nFrame {midpoint} ({cat_name})",
                fontsize=TITLE_SZ - 2,
            )
            ax.axis("off")
            _save(fig, "B_skeleton", f"B{frame_count:02d}_{vid}_f{midpoint}.png")

            # Stop if we have enough from this video (max 2 per video)
            if interval_idx >= 1:
                break

    # If we still need more frames, try additional intervals from the first video
    if frame_count < 3 and xd_selected:
        vid = xd_selected[0]
        video_path = xd_video_dir / f"{vid}.mp4"
        skel_path = xd_skel_dir / f"{vid}.pkl"
        if video_path.exists() and skel_path.exists() and vid in xd_annos:
            anno = xd_annos[vid]
            gt_intervals = get_gt_intervals(anno)
            for start, end in gt_intervals:
                if frame_count >= 3:
                    break
                # Use a different position -- quarter point
                quarter = start + (end - start) // 4
                frame_rgb = create_skeleton_overlay(video_path, skel_path, quarter)
                if frame_rgb is None:
                    continue
                frame_count += 1
                cat_name = XD_CAT_NAMES.get(anno.category, anno.category)
                fig, ax = plt.subplots(figsize=(10, 7))
                ax.imshow(frame_rgb)
                ax.set_title(
                    f"{vid}\nFrame {quarter} ({cat_name})",
                    fontsize=TITLE_SZ - 2,
                )
                ax.axis("off")
                _save(fig, "B_skeleton", f"B{frame_count:02d}_{vid}_f{quarter}.png")

    print(f"  Generated {frame_count} skeleton overlay(s)")
    return frame_count


# --- Section C: Corruption Heatmaps ------------------------------------------

def load_tta_results() -> pd.DataFrame:
    """Load eval_metrics.json from all TTA result directories.

    Returns DataFrame with columns: method, corruption, severity, lr, rho, auc, ap.
    """
    tta_dir = RESULTS_DIR / "tta"
    if not tta_dir.exists():
        print("  [WARN] No TTA results directory found")
        return pd.DataFrame()

    rows = []
    for d in sorted(tta_dir.iterdir()):
        metrics_path = d / "eval_metrics.json"
        if not metrics_path.exists():
            continue
        with open(metrics_path) as f:
            m = json.load(f)
        rows.append({
            "method": m["method"],
            "corruption": m["corruption_type"],
            "severity": m["severity"],
            "lr": m.get("lr", 0),
            "rho": m.get("rho"),
            "auc": m["auc"],
            "ap": m["ap"],
        })

    df = pd.DataFrame(rows)
    print(f"  Loaded {len(df)} TTA results ({df['method'].nunique()} methods)")
    return df


def _best_per_condition(df: pd.DataFrame, method: str) -> pd.DataFrame:
    """For each (corruption, severity), select the row with highest AUC.

    This handles the fact that TENT has 4 LR options and SAR has 4x5=20 LR/rho
    combinations per condition (Pitfall 7).
    """
    sub = df[df["method"] == method].copy()
    if sub.empty:
        return sub
    idx = sub.groupby(["corruption", "severity"])["auc"].idxmax()
    return sub.loc[idx]


def chart_C_corruption_heatmap(
    pivot: pd.DataFrame,
    title: str,
    filename: str,
    cmap: str = "RdYlGn",
    fmt: str = ".4f",
    center=None,
):
    """Generate a corruption_type x severity heatmap."""
    n_rows, n_cols = pivot.shape
    fig_w = max(10, n_cols * 2.0 + 3)
    fig_h = max(5, n_rows * 0.8 + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    annot_sz = max(8, min(12, 200 // max(n_rows, n_cols)))

    hm_kwargs = dict(
        annot=True, fmt=fmt, cmap=cmap, ax=ax, linewidths=0.5,
        annot_kws={"size": annot_sz},
        cbar_kws={"label": "AUC"},
    )
    if center is not None:
        hm_kwargs["center"] = center

    sns.heatmap(pivot, **hm_kwargs)
    ax.set_title(title, fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xlabel("Severity", fontsize=LABEL_SZ)
    ax.set_ylabel("Corruption Type", fontsize=LABEL_SZ)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=TICK_SZ)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=TICK_SZ, rotation=0)

    _save(fig, "C_corruption", filename)


def chart_C_method_comparison(source_pivot, tent_pivot, sar_pivot):
    """C06: Grouped bar chart comparing mean AUC across all 20 conditions."""
    methods = ["Source-Only", "Best TENT", "Best SAR"]
    means = [
        source_pivot.values.mean(),
        tent_pivot.values.mean(),
        sar_pivot.values.mean(),
    ]
    stds = [
        source_pivot.values.std(),
        tent_pivot.values.std(),
        sar_pivot.values.std(),
    ]
    colors = ["#64748B", "#3B82F6", "#EF4444"]

    fig, ax = plt.subplots(figsize=FIG_SMALL)
    bars = ax.bar(methods, means, yerr=stds, capsize=5, color=colors, edgecolor="white")
    for bar, val in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
            f"{val:.4f}", ha="center", va="bottom", fontsize=VAL_SZ, fontweight="bold",
        )
    ax.set_ylabel("Mean AUC (across 20 conditions)", fontsize=LABEL_SZ)
    ax.set_title("TTA Method Comparison: Mean AUC", fontsize=TITLE_SZ, fontweight="bold")
    ax.tick_params(labelsize=TICK_SZ)
    ax.set_ylim(0, min(1.0, max(means) + 0.05))

    _save(fig, "C_corruption", "C06_method_comparison.png")


def run_section_C():
    """Generate Section C: Corruption Severity Heatmaps."""
    print("\n[4/6] Section C: Corruption Heatmaps")
    df = load_tta_results()
    if df.empty:
        print("  [WARN] No TTA data -- skipping Section C")
        return

    # Best per condition for each method
    source_best = _best_per_condition(df, "source_only")
    tent_best = _best_per_condition(df, "tent")
    sar_best = _best_per_condition(df, "sar")

    def _pivot(sub):
        p = sub.pivot_table(values="auc", index="corruption", columns="severity")
        return p.sort_index()

    source_pivot = _pivot(source_best)
    tent_pivot = _pivot(tent_best)
    sar_pivot = _pivot(sar_best)

    # C01-C03: Absolute AUC heatmaps
    chart_C_corruption_heatmap(
        source_pivot,
        "Source-Only AUC by Corruption x Severity",
        "C01_source_only_auc.png",
    )
    chart_C_corruption_heatmap(
        tent_pivot,
        "Best-TENT AUC by Corruption x Severity",
        "C02_best_tent_auc.png",
    )
    chart_C_corruption_heatmap(
        sar_pivot,
        "Best-SAR AUC by Corruption x Severity",
        "C03_best_sar_auc.png",
    )

    # C04-C05: Delta heatmaps (improvement over source-only)
    tent_delta = tent_pivot - source_pivot
    sar_delta = sar_pivot - source_pivot

    chart_C_corruption_heatmap(
        tent_delta,
        "TENT AUC Delta vs Source-Only",
        "C04_tent_vs_source_delta.png",
        cmap="RdBu_r",
        center=0,
    )
    chart_C_corruption_heatmap(
        sar_delta,
        "SAR AUC Delta vs Source-Only",
        "C05_sar_vs_source_delta.png",
        cmap="RdBu_r",
        center=0,
    )

    # C06: Method comparison bar chart
    chart_C_method_comparison(source_pivot, tent_pivot, sar_pivot)


# --- Section F: Additional Thesis Figures ------------------------------------

def _load_results_index() -> pd.DataFrame:
    """Load results-index.csv."""
    csv_path = RESULTS_DIR / "results-index.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    for col in ("auc", "ap"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def chart_F01_cross_dataset_comparison(results_df: pd.DataFrame):
    """F01: Grouped bar chart comparing UCF AUC and XD AP across 4 model variants."""
    variants_order = ["skeleton_only", "clip_only", "late_fusion", "gated_fusion"]

    # Filter by exact run_name to exclude sweep runs (which also have seed=42, no cache_variant)
    ucf_run_names = list(UCF_RUNS.values())
    xd_run_names = list(XD_RUNS.values())

    ucf_data = results_df[results_df["run_name"].isin(ucf_run_names)].set_index("variant")
    xd_data = results_df[results_df["run_name"].isin(xd_run_names)].set_index("variant")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_WIDE)

    # UCF AUC bars
    ucf_vals = [ucf_data.loc[v, "auc"] if v in ucf_data.index else 0 for v in variants_order]
    ucf_colors = [VCOLORS[v] for v in variants_order]
    bars1 = ax1.bar(
        [VLABELS[v] for v in variants_order], ucf_vals,
        color=ucf_colors, edgecolor="white",
    )
    for bar, val in zip(bars1, ucf_vals):
        ax1.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
            f"{val:.4f}", ha="center", va="bottom", fontsize=VAL_SZ, fontweight="bold",
        )
    ax1.set_ylabel("AUC", fontsize=LABEL_SZ)
    ax1.set_title("UCF-Crime: Frame-Level AUC", fontsize=TITLE_SZ - 2, fontweight="bold")
    ax1.set_ylim(0, 1.0)
    ax1.tick_params(labelsize=TICK_SZ - 1, axis="x", rotation=15)

    # XD AP bars
    xd_vals = [xd_data.loc[v, "ap"] if v in xd_data.index else 0 for v in variants_order]
    bars2 = ax2.bar(
        [VLABELS[v] for v in variants_order], xd_vals,
        color=ucf_colors, edgecolor="white",
    )
    for bar, val in zip(bars2, xd_vals):
        ax2.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
            f"{val:.4f}", ha="center", va="bottom", fontsize=VAL_SZ, fontweight="bold",
        )
    ax2.set_ylabel("AP", fontsize=LABEL_SZ)
    ax2.set_title("XD-Violence: Frame-Level AP", fontsize=TITLE_SZ - 2, fontweight="bold")
    ax2.set_ylim(0, 1.0)
    ax2.tick_params(labelsize=TICK_SZ - 1, axis="x", rotation=15)

    fig.suptitle(
        "Cross-Dataset Comparison (Seed 42)",
        fontsize=TITLE_SZ, fontweight="bold", y=1.02,
    )
    fig.tight_layout()
    _save(fig, "F_additional", "F01_cross_dataset_comparison.png")


def chart_F02_per_category_ucf(ucf_annos, gated_scores):
    """F02: Box plot of anomaly score distributions per UCF category."""
    rows = []
    for vid, scores in gated_scores.items():
        if vid not in ucf_annos:
            continue
        anno = ucf_annos[vid]
        if anno.is_normal:
            continue
        labels = frame_labels(anno, len(scores))
        # Subsample for plotting efficiency (take every 10th frame)
        step = max(1, len(scores) // 200)
        for i in range(0, len(scores), step):
            rows.append({
                "category": anno.category,
                "score": float(scores[i]),
                "label": "Anomalous" if labels[i] == 1 else "Normal",
            })

    df = pd.DataFrame(rows)
    if df.empty:
        print("  [WARN] No UCF per-category data -- skipping F02")
        return

    categories = sorted(df["category"].unique())
    fig, ax = plt.subplots(figsize=(max(12, len(categories) * 1.5), 7))
    sns.boxplot(
        data=df, x="category", y="score", hue="label",
        palette={"Normal": "#64748B", "Anomalous": "#EF4444"},
        ax=ax, fliersize=2,
    )
    ax.set_xlabel("Crime Category", fontsize=LABEL_SZ)
    ax.set_ylabel("Anomaly Score", fontsize=LABEL_SZ)
    ax.set_title(
        "UCF-Crime: Score Distribution by Category (Gated Fusion s42)",
        fontsize=TITLE_SZ, fontweight="bold",
    )
    ax.tick_params(labelsize=TICK_SZ, axis="x", rotation=30)
    ax.legend(fontsize=11, loc="upper right")

    _save(fig, "F_additional", "F02_ucf_category_scores.png")


def chart_F03_per_category_xd(xd_annos, gated_scores):
    """F03: Box plot of anomaly score distributions per XD-Violence category."""
    # XD category code to readable name mapping
    cat_names = {
        "B1": "Fighting", "B2": "Shooting", "B4": "Riot",
        "B5": "Abuse", "B6": "Car Accident", "G": "Explosion",
    }
    rows = []
    for vid, scores in gated_scores.items():
        if vid not in xd_annos:
            continue
        anno = xd_annos[vid]
        cat_code = anno.category
        cat_label = cat_names.get(cat_code, cat_code)
        labels = xd_frame_labels(anno, len(scores))
        step = max(1, len(scores) // 200)
        for i in range(0, len(scores), step):
            rows.append({
                "category": cat_label,
                "score": float(scores[i]),
                "label": "Anomalous" if labels[i] == 1 else "Normal",
            })

    df = pd.DataFrame(rows)
    if df.empty:
        print("  [WARN] No XD per-category data -- skipping F03")
        return

    categories = sorted(df["category"].unique())
    fig, ax = plt.subplots(figsize=(max(12, len(categories) * 1.5), 7))
    sns.boxplot(
        data=df, x="category", y="score", hue="label",
        palette={"Normal": "#64748B", "Anomalous": "#EF4444"},
        ax=ax, fliersize=2,
    )
    ax.set_xlabel("Violence Category", fontsize=LABEL_SZ)
    ax.set_ylabel("Anomaly Score", fontsize=LABEL_SZ)
    ax.set_title(
        "XD-Violence: Score Distribution by Category (Gated Fusion s42)",
        fontsize=TITLE_SZ, fontweight="bold",
    )
    ax.tick_params(labelsize=TICK_SZ, axis="x", rotation=30)
    ax.legend(fontsize=11, loc="upper right")

    _save(fig, "F_additional", "F03_xd_category_scores.png")


def chart_F04_seed_stability(results_df: pd.DataFrame):
    """F04: Bar chart with error bars showing 3-seed mean+std for Gated Fusion."""
    seeds = [42, 123, 2024]

    # UCF: AUC metric -- filter by exact run_name to exclude sweep runs
    ucf_seed_names = [f"ucf_gated_fusion_s{s}" for s in seeds]
    ucf_aucs = results_df[results_df["run_name"].isin(ucf_seed_names)]["auc"].values

    # XD: AP metric
    xd_seed_names = [f"xd_gated_fusion_s{s}" for s in seeds]
    xd_aps = results_df[results_df["run_name"].isin(xd_seed_names)]["ap"].values

    datasets = []
    means = []
    stds = []
    colors = []
    if len(ucf_aucs) >= 2:
        datasets.append("UCF-Crime AUC")
        means.append(ucf_aucs.mean())
        stds.append(ucf_aucs.std())
        colors.append("#3B82F6")
    if len(xd_aps) >= 2:
        datasets.append("XD-Violence AP")
        means.append(xd_aps.mean())
        stds.append(xd_aps.std())
        colors.append("#EF4444")

    if not datasets:
        print("  [WARN] Insufficient seed data for F04")
        return

    fig, ax = plt.subplots(figsize=FIG_SMALL)
    bars = ax.bar(datasets, means, yerr=stds, capsize=8, color=colors, edgecolor="white")
    for bar, m, s in zip(bars, means, stds):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + s + 0.005,
            f"{m:.4f} +/- {s:.4f}", ha="center", va="bottom",
            fontsize=VAL_SZ, fontweight="bold",
        )
    ax.set_ylabel("Metric Value", fontsize=LABEL_SZ)
    ax.set_title(
        "Gated Fusion: 3-Seed Stability (s42, s123, s2024)",
        fontsize=TITLE_SZ, fontweight="bold",
    )
    ax.set_ylim(0, 1.0)
    ax.tick_params(labelsize=TICK_SZ)

    _save(fig, "F_additional", "F04_seed_stability.png")


def chart_F05_ablation_bars(results_df: pd.DataFrame):
    """F05-F06: Horizontal bar chart of all ablation rows for each dataset."""
    variants_order = ["skeleton_only", "clip_only", "late_fusion", "gated_fusion"]

    for dataset, metric, fig_name, runs_dict in [
        ("ucf", "auc", "F05_ucf_ablation_bars.png", UCF_RUNS),
        ("xd", "ap", "F06_xd_ablation_bars.png", XD_RUNS),
    ]:
        # Filter by exact run_names to exclude sweep runs
        main_run_names = list(runs_dict.values())
        sub = results_df[results_df["run_name"].isin(main_run_names)].copy()
        if sub.empty:
            print(f"  [WARN] No {dataset} ablation data for {fig_name}")
            continue

        # Also include cache variants (e.g. 2person, clip_mean)
        mask_extra = (
            (results_df["dataset"] == dataset)
            & (results_df["seed"] == 42)
            & (results_df["variant"] == "gated_fusion")
            & (results_df["cache_variant"].notna())
        )
        extra = results_df[mask_extra].copy()
        sub = pd.concat([sub, extra], ignore_index=True)

        # Create display names
        def _display(row):
            name = VLABELS.get(row["variant"], row["variant"])
            cv = row.get("cache_variant")
            if pd.notna(cv) and cv:
                name = f"{name} ({cv})"
            return name

        sub["display"] = sub.apply(_display, axis=1)
        sub = sub.sort_values(metric, ascending=True)

        fig, ax = plt.subplots(figsize=(10, max(6, len(sub) * 1.0 + 1.5)))
        colors = [VCOLORS.get(v, "#888888") for v in sub["variant"]]
        bars = ax.barh(sub["display"], sub[metric], color=colors, edgecolor="white")

        for bar, val in zip(bars, sub[metric]):
            ax.text(
                val + 0.003, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=VAL_SZ, fontweight="bold",
            )

        ds_label = "UCF-Crime" if dataset == "ucf" else "XD-Violence"
        ax.set_xlabel(metric.upper(), fontsize=LABEL_SZ)
        ax.set_title(
            f"{ds_label}: Ablation Comparison ({metric.upper()}, Seed 42)",
            fontsize=TITLE_SZ, fontweight="bold",
        )
        ax.tick_params(labelsize=TICK_SZ)

        _save(fig, "F_additional", fig_name)


def run_section_F(ucf_annos, xd_annos, all_scores):
    """Generate Section F: Additional Thesis Figures."""
    print("\n[5/6] Section F: Additional Figures")

    results_df = _load_results_index()
    if results_df.empty:
        print("  [WARN] No results-index.csv -- skipping most Section F charts")
    else:
        chart_F01_cross_dataset_comparison(results_df)
        chart_F04_seed_stability(results_df)
        chart_F05_ablation_bars(results_df)

    # Per-category box plots from eval_scores
    ucf_gated = all_scores.get(UCF_RUNS["gated_fusion"], {})
    xd_gated = all_scores.get(XD_RUNS["gated_fusion"], {})

    if ucf_gated:
        chart_F02_per_category_ucf(ucf_annos, ucf_gated)
    if xd_gated:
        chart_F03_per_category_xd(xd_annos, xd_gated)


# --- Section D: Gate Activation Distributions (D-12) -------------------------

def collect_gate_and_features(dataset_name, config_path, checkpoint_path):
    """Load GatedFusion checkpoint and collect gate activations + fused features.

    Uses forward hooks on model.gate (pre-sigmoid nn.Linear) and model.ln_fused.
    CRITICAL (Pitfall 5): model.gate is nn.Linear -- hook output is pre-sigmoid.
    Must apply torch.sigmoid() manually to get gate values in [0, 1].

    Returns (gate_outputs, fused_features) -- both {video_id: ndarray[T, 256]}.
    """
    # Load config snapshot -- note: wrapped in "config" key
    with open(config_path) as f:
        snapshot = json.load(f)
    cfg = snapshot["config"] if "config" in snapshot else snapshot

    # Build model
    model = build_model(**cfg["model"])

    # Load checkpoint with strict=True (CLAUDE.md convention)
    state_dict = load_checkpoint(checkpoint_path, device="cpu")
    model.load_state_dict(state_dict, strict=True)

    # Move to device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    print(f"  Model loaded on {device} from {checkpoint_path}")

    # Build test dataset
    splits_dir = cfg["paths"]["splits_dir"]
    # Resolve splits_dir relative to PROJECT_ROOT if not absolute
    splits_path = Path(splits_dir)
    if not splits_path.is_absolute():
        splits_path = PROJECT_ROOT / splits_path

    dataset = MILFeatureDataset(
        skel_dir=cfg["paths"]["skeleton_features"],
        clip_dir=cfg["paths"]["clip_features"],
        split_file=str(splits_path / f"{dataset_name}_test.txt"),
        dataset=dataset_name,
        mode="test",
    )
    print(f"  Test dataset: {len(dataset)} videos")

    # Register forward hooks
    gate_outputs = {}
    fused_features = {}

    def gate_hook(module, input, output):
        # CRITICAL: apply sigmoid manually -- model.gate is nn.Linear (Pitfall 5)
        gate_hook._last = torch.sigmoid(output).detach().cpu()

    def fused_hook(module, input, output):
        fused_hook._last = output.detach().cpu()

    h1 = model.gate.register_forward_hook(gate_hook)
    h2 = model.ln_fused.register_forward_hook(fused_hook)

    # Run inference
    with torch.no_grad():
        loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)
        for batch in loader:
            vid = batch["video_id"]
            if isinstance(vid, (list, tuple)):
                vid = vid[0]

            kwargs = {}
            for k in ("skel", "clip"):
                if k in batch:
                    t = batch[k]
                    if t.dim() == 2:
                        t = t.unsqueeze(0)
                    kwargs[k] = t.to(device)
            model(**kwargs)

            gate_outputs[vid] = gate_hook._last.squeeze(0).numpy()
            fused_features[vid] = fused_hook._last.squeeze(0).numpy()

    h1.remove()
    h2.remove()

    # Validate gate values are in [0, 1] (confirms sigmoid was applied)
    all_gate_vals = np.concatenate([g.ravel() for g in gate_outputs.values()])
    g_min, g_max = all_gate_vals.min(), all_gate_vals.max()
    print(f"  Gate value range: [{g_min:.4f}, {g_max:.4f}]")
    assert g_min >= 0.0 and g_max <= 1.0, (
        f"Gate values outside [0,1]: min={g_min}, max={g_max}. "
        "Did you forget torch.sigmoid() on hook output?"
    )

    return gate_outputs, fused_features


def chart_D_gate_by_category(gate_outputs, annos, label_fn, dataset_label):
    """D01: Box plot of mean gate value per video, grouped by category.

    Color-coded by normal vs abnormal.
    """
    rows = []
    for vid, gates in gate_outputs.items():
        mean_gate = float(np.mean(gates))
        # UCF's annotation file INCLUDES the 150 Normal test videos (category
        # "Normal"), so membership alone misclassifies them as anomalous.
        if vid in annos and not annos[vid].is_normal:
            cat = annos[vid].category
            if dataset_label.startswith("XD"):
                cat = XD_CAT_NAMES.get(cat, cat)
            is_anom = True
        else:
            cat = "Normal"
            is_anom = False
        rows.append({
            "category": cat,
            "mean_gate": mean_gate,
            "type": "Anomalous" if is_anom else "Normal",
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return

    # Sort categories: Normal first, then alphabetical
    cats = sorted(df["category"].unique(), key=lambda c: (0 if c == "Normal" else 1, c))
    fig, ax = plt.subplots(figsize=(max(12, len(cats) * 1.2), 7))
    sns.boxplot(
        data=df, x="category", y="mean_gate", hue="type",
        palette={"Normal": "#64748B", "Anomalous": "#EF4444"},
        ax=ax, fliersize=2, order=cats,
    )
    ax.set_xlabel("Category", fontsize=LABEL_SZ)
    ax.set_ylabel("Mean Gate Value (sigmoid)", fontsize=LABEL_SZ)
    ax.set_ylim(0, 1)
    ax.set_title(
        f"Gate Activation Distribution ({dataset_label})",
        fontsize=TITLE_SZ, fontweight="bold",
    )
    ax.tick_params(labelsize=TICK_SZ, axis="x", rotation=30)
    ax.legend(fontsize=11, loc="upper right")

    tag = "ucf" if "UCF" in dataset_label else "xd"
    _save(fig, "D_gating", f"D01_gate_by_category_{tag}.png")


def chart_D_gate_histogram(gate_outputs, annos, dataset_label):
    """D02: Overlaid histograms of gate values for normal vs anomalous videos.

    X-axis: gate sigmoid value [0, 1]. Y-axis: density.
    """
    normal_gates = []
    abnormal_gates = []

    for vid, gates in gate_outputs.items():
        flat = gates.ravel()
        # See chart_D_gate_by_category: UCF normals ARE in annos (category
        # "Normal") -- classify by is_normal, not bare membership.
        if vid in annos and not annos[vid].is_normal:
            abnormal_gates.append(flat)
        else:
            normal_gates.append(flat)

    fig, ax = plt.subplots(figsize=FIG_STD)

    if normal_gates:
        all_normal = np.concatenate(normal_gates)
        ax.hist(
            all_normal, bins=50, range=(0, 1), density=True,
            alpha=0.5, color="#3B82F6", label="Normal", edgecolor="white",
        )
    if abnormal_gates:
        all_abnormal = np.concatenate(abnormal_gates)
        ax.hist(
            all_abnormal, bins=50, range=(0, 1), density=True,
            alpha=0.5, color="#EF4444", label="Anomalous", edgecolor="white",
        )

    ax.set_xlabel("Gate Value (sigmoid)", fontsize=LABEL_SZ)
    ax.set_ylabel("Density", fontsize=LABEL_SZ)
    ax.set_xlim(0, 1)
    ax.set_title(
        f"Gate Value Distribution: Normal vs Anomalous ({dataset_label})",
        fontsize=TITLE_SZ, fontweight="bold",
    )
    ax.legend(fontsize=12)
    ax.tick_params(labelsize=TICK_SZ)

    tag = "ucf" if "UCF" in dataset_label else "xd"
    _save(fig, "D_gating", f"D02_gate_histogram_{tag}.png")


# --- Section E: t-SNE Feature Projection (D-13) -----------------------------

def chart_E_tsne(fused_features, annos, dataset_label):
    """t-SNE 2D projection of fused features, colored by category.

    Per D-13: pool per-video features (mean over T) to [256] per video,
    then TSNE(perplexity=30, random_state=42, init='pca') to 2D.
    Normal = grey circles. Abnormal = colored by category.
    """
    vids = list(fused_features.keys())
    X = np.stack([fused_features[v].mean(axis=0) for v in vids])  # [N, 256]

    labels = []
    categories = []
    for vid in vids:
        # See chart_D_gate_by_category: UCF normals ARE in annos (category
        # "Normal") -- without the is_normal check they get label 1 with
        # category "Normal", which the plotting loops below silently skip
        # (invisible points).
        if vid in annos and not annos[vid].is_normal:
            cat = annos[vid].category
            if "xd" in dataset_label.lower():
                cat = XD_CAT_NAMES.get(cat, cat)
            labels.append(1)
            categories.append(cat)
        else:
            labels.append(0)
            categories.append("Normal")
    labels = np.array(labels)

    # Adjust perplexity if dataset is small
    n_samples = len(vids)
    perplexity = min(30, max(5, n_samples // 4))

    print(f"  t-SNE: {n_samples} videos, perplexity={perplexity}")
    tsne = TSNE(
        n_components=2, perplexity=perplexity, random_state=42,
        init="pca", method="barnes_hut",
    )
    X_2d = tsne.fit_transform(X)

    # Build color map for categories
    unique_cats = sorted(set(c for c in categories if c != "Normal"))
    cmap = matplotlib.colormaps.get_cmap("tab10").resampled(max(len(unique_cats), 1))
    cat_colors = {cat: cmap(i) for i, cat in enumerate(unique_cats)}

    fig, ax = plt.subplots(figsize=FIG_STD)

    # Plot normal points first (background)
    normal_mask = labels == 0
    if normal_mask.sum() > 0:
        ax.scatter(
            X_2d[normal_mask, 0], X_2d[normal_mask, 1],
            c="grey", alpha=0.4, s=20, label="Normal", edgecolors="none",
        )

    # Plot abnormal points by category
    for cat in unique_cats:
        cat_mask = np.array([c == cat for c in categories])
        if cat_mask.sum() > 0:
            ax.scatter(
                X_2d[cat_mask, 0], X_2d[cat_mask, 1],
                c=[cat_colors[cat]], alpha=0.7, s=35, label=cat,
                edgecolors="white", linewidths=0.3,
            )

    ax.set_title(
        f"t-SNE of Fused Features ({dataset_label})",
        fontsize=TITLE_SZ, fontweight="bold",
    )
    ax.set_xlabel("t-SNE 1", fontsize=LABEL_SZ)
    ax.set_ylabel("t-SNE 2", fontsize=LABEL_SZ)
    ax.tick_params(labelsize=TICK_SZ)

    # Place legend outside plot if many categories
    if len(unique_cats) > 5:
        ax.legend(fontsize=9, loc="center left", bbox_to_anchor=(1.02, 0.5),
                  borderaxespad=0)
    else:
        ax.legend(fontsize=10, loc="best")

    tag = "ucf" if "UCF" in dataset_label else "xd"
    _save(fig, "E_projection", f"E01_tsne_{tag}.png")


def run_section_DE(ucf_annos, xd_annos):
    """Generate Sections D+E: Gate distributions and t-SNE projections.

    For each dataset (UCF, XD), call collect_gate_and_features() once,
    then generate both D and E charts from the collected data (D-10).
    """
    print("\n[6/6] Sections D+E: Gate Distributions & t-SNE")

    configs = [
        (
            "ucf", "UCF-Crime",
            RESULTS_DIR / "ucf_gated_fusion_s42" / "config_snapshot.json",
            RESULTS_DIR / "ucf_gated_fusion_s42" / "best_model.pth",
            ucf_annos,
        ),
        (
            "xd", "XD-Violence",
            RESULTS_DIR / "xd_gated_fusion_s42" / "config_snapshot.json",
            RESULTS_DIR / "xd_gated_fusion_s42" / "best_model.pth",
            xd_annos,
        ),
    ]

    for dataset_name, dataset_label, config_path, ckpt_path, annos in configs:
        if not config_path.exists():
            print(f"  [WARN] Config not found: {config_path}, skipping {dataset_label}")
            continue
        if not ckpt_path.exists():
            print(f"  [WARN] Checkpoint not found: {ckpt_path}, skipping {dataset_label}")
            continue

        print(f"\n  --- {dataset_label} ---")
        gate_outputs, fused_features = collect_gate_and_features(
            dataset_name, config_path, ckpt_path
        )

        # Section D: Gate distributions
        label_fn = frame_labels if dataset_name == "ucf" else xd_frame_labels
        chart_D_gate_by_category(gate_outputs, annos, label_fn, dataset_label)
        chart_D_gate_histogram(gate_outputs, annos, dataset_label)

        # Section E: t-SNE
        chart_E_tsne(fused_features, annos, dataset_label)


# --- Main --------------------------------------------------------------------

def main():
    print("Phase 6 Analysis & Visualization")
    print("=" * 50)
    print(f"Output: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/6] Loading annotations and scores...")
    ucf_annos = parse_annotations(
        PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    )
    xd_annos = parse_xd_annotations(
        PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"
    )
    all_scores = load_all_scores()

    # Section A: Temporal Curves
    ucf_selected, xd_selected = run_section_A(ucf_annos, xd_annos, all_scores)

    # Section B: Skeleton Overlays (uses XD selected videos from Section A)
    run_section_B(xd_selected, xd_annos)

    # Section C: Corruption Heatmaps
    run_section_C()

    # Section F: Additional Figures
    run_section_F(ucf_annos, xd_annos, all_scores)

    # Sections D+E: Gate Distributions & t-SNE (GPU-dependent)
    run_section_DE(ucf_annos, xd_annos)

    pngs = list(OUT_DIR.rglob("*.png"))
    print(f"\nDone! Generated {len(pngs)} PNG files in {OUT_DIR}")


if __name__ == "__main__":
    main()
