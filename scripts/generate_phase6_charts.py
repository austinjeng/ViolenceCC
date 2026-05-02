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
    print("\n[3/4] Section C: Corruption Heatmaps")
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

        fig, ax = plt.subplots(figsize=(12, max(5, len(sub) * 0.6 + 1)))
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
    print("\n[4/4] Section F: Additional Figures")

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

    # Section C: Corruption Heatmaps
    run_section_C()

    # Section F: Additional Figures
    run_section_F(ucf_annos, xd_annos, all_scores)

    pngs = list(OUT_DIR.rglob("*.png"))
    print(f"\nDone! Generated {len(pngs)} PNG files in {OUT_DIR}")


if __name__ == "__main__":
    main()
