#!/usr/bin/env python
"""
Publication-Quality Figure Generation for CGW '26 Paper
=======================================================
ACM sigconf formatting: 300 DPI, serif fonts, grayscale-friendly,
proper column widths (3.33in single, 7.0in full-text).

Usage:
    conda activate vcc-main
    python scripts/generate_pub_figures.py

Output: paper/figures/
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

# --- Project Setup -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "results"
OUT_DIR = PROJECT_ROOT / "paper" / "figures"

# --- ACM sigconf Presets -----------------------------------------------------
ACM_COL_WIDTH = 3.33    # inches (single column)
ACM_TEXT_WIDTH = 7.0     # inches (full text width)
PUB_DPI = 300

# Font sizes (points)
FONT_TITLE = 9
FONT_AXES = 8
FONT_TICKS = 7
FONT_LEGEND = 7
FONT_ANNOTATION = 6.5

# Grayscale-friendly palette with hatching
BACKBONE_STYLES = {
    "CLIP":    {"color": "#2c3e50", "hatch": "",    "label": "CLIP ViT-B/16"},
    "SigLIP2": {"color": "#7f8c8d", "hatch": "///", "label": "SigLIP2 ViT-B/16"},
    "SO400M":  {"color": "#bdc3c7", "hatch": "...", "label": "SigLIP2 SO400M"},
    "Giant":   {"color": "#e74c3c", "hatch": "xxx", "label": "SigLIP2 Giant"},
}

# Variant colors for temporal plot (3 curves)
TEMPORAL_COLORS = {
    "skeleton_only": "#7f8c8d",
    "clip_only":     "#2c3e50",
    "gated_fusion":  "#e74c3c",
}
TEMPORAL_LABELS = {
    "skeleton_only": "Skeleton Only",
    "clip_only":     "Visual Only (CLIP)",
    "gated_fusion":  "Gated Fusion",
}
TEMPORAL_STYLES = {
    "skeleton_only": "--",
    "clip_only":     "-.",
    "gated_fusion":  "-",
}

# XD category code to readable name
XD_CAT_NAMES = {
    "B1": "Fighting", "B2": "Shooting", "B4": "Riot",
    "B5": "Abuse", "B6": "Car Acc.", "G": "Explosion",
}


def _setup_style():
    """Configure matplotlib for ACM sigconf publication quality."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
        "font.size": FONT_AXES,
        "axes.titlesize": FONT_TITLE,
        "axes.labelsize": FONT_AXES,
        "xtick.labelsize": FONT_TICKS,
        "ytick.labelsize": FONT_TICKS,
        "legend.fontsize": FONT_LEGEND,
        "figure.dpi": PUB_DPI,
        "savefig.dpi": PUB_DPI,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.4,
        "axes.linewidth": 0.5,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "lines.linewidth": 1.0,
        "pdf.fonttype": 42,      # TrueType fonts in PDF
        "ps.fonttype": 42,
    })


# =============================================================================
# Figure 2: Temporal Anomaly Score Plot
# =============================================================================

def find_best_temporal_video(video_id: str | None = None) -> str:
    """Find UCF test video where gated fusion shows clear temporal dynamics
    AND outperforms single-modality baselines.

    Heuristic: score = range(gated) * (1 + advantage_over_both), restricted to
    videos whose gated curve is *positively aligned* with the ground-truth
    window (mean score inside GT > mean score outside GT). The alignment filter
    is mandatory: without it the raw range/advantage heuristic selected
    RoadAccidents127, the single worst anti-aligned test video (in-GT mean
    0.001 vs out-GT 0.743, gap -0.742) -- the C1 erratum this fix removes.

    If ``video_id`` is given it is returned as-is (bypassing the heuristic).
    The temporal figure pins ``Fighting047`` explicitly: it is the well-
    localized, CGW-talk-validated example (in-GT 0.889 vs out-GT 0.407, gap
    +0.483). Among positively-aligned videos the pure heuristic would instead
    rank Stealing019 first, but that curve stays high (~0.92) during normal
    segments too (out-GT mean 0.767) and is not a clean localization example.
    """
    if video_id is not None:
        print(f"  Temporal video (explicit): {video_id}")
        return video_id

    from src.eval.ucf_annotations import parse_annotations
    annos = parse_annotations(PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt")

    runs = {}
    for variant, run_name in [
        ("gated", "ucf_gated_fusion_s42"),
        ("clip", "ucf_clip_only_s42"),
        ("skel", "ucf_skeleton_only_s42"),
    ]:
        path = RESULTS_DIR / run_name / "eval_scores.npz"
        if not path.exists():
            print(f"  [WARN] Missing {path}")
            return "Fighting047"
        runs[variant] = np.load(path)

    anom_vids = [k for k in runs["gated"].files if not k.startswith("Normal")]

    best_vid, best_score = "Fighting047", -999
    for vid in anom_vids:
        if vid not in runs["clip"].files or vid not in runs["skel"].files:
            continue
        g = runs["gated"][vid]
        c = runs["clip"][vid]
        s = runs["skel"][vid]
        g_range = float(g.max() - g.min())
        adv = float(g.max()) - max(float(c.max()), float(s.max()))
        n_frames = len(g)
        if g_range < 0.3 or n_frames > 10000:
            continue
        # Hard alignment filter: reject videos whose gated score is not higher
        # inside the GT window than outside it (rejects RoadAccidents127).
        gt_mask = np.zeros(n_frames, dtype=bool)
        if vid in annos:
            for start, end in annos[vid].intervals:
                if start is not None:
                    gt_mask[max(0, int(start)):min(int(end), n_frames)] = True
        if not gt_mask.any() or gt_mask.all():
            continue
        if float(g[gt_mask].mean()) <= float(g[~gt_mask].mean()):
            continue
        score = g_range * (1.0 + max(adv, 0.0))
        if score > best_score:
            best_score = score
            best_vid = vid

    print(f"  Selected temporal video: {best_vid} (score={best_score:.4f})")
    return best_vid


def fig_temporal_scores():
    """Figure 2: Temporal anomaly score comparison on a UCF-Crime test video."""
    print("\n[Fig 2] Temporal Anomaly Scores")

    from src.eval.ucf_annotations import parse_annotations
    annos = parse_annotations(PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt")

    # Pin the well-localized, positively-aligned Fighting047 example (C1 fix).
    video_id = find_best_temporal_video("Fighting047")

    # Load scores for 3 variants
    scores = {}
    for variant, run_name in [
        ("skeleton_only", "ucf_skeleton_only_s42"),
        ("clip_only", "ucf_clip_only_s42"),
        ("gated_fusion", "ucf_gated_fusion_s42"),
    ]:
        path = RESULTS_DIR / run_name / "eval_scores.npz"
        npz = np.load(path)
        scores[variant] = npz[video_id]

    n_frames = len(scores["gated_fusion"])
    frames = np.arange(n_frames)

    # Get GT intervals
    gt_intervals = []
    if video_id in annos:
        for s, e in annos[video_id].intervals:
            if s is not None:
                gt_intervals.append((int(s), int(e)))

    # Plot
    fig, ax = plt.subplots(figsize=(ACM_COL_WIDTH, 1.8))

    # GT shading
    for start, end in gt_intervals:
        ax.axvspan(max(0, start), min(end, n_frames),
                   alpha=0.15, color="#e74c3c", label="_nolegend_")
    if gt_intervals:
        ax.axvspan(0, 0, alpha=0.15, color="#e74c3c", label="Ground Truth")

    # Score curves
    for variant in ["skeleton_only", "clip_only", "gated_fusion"]:
        s = scores[variant]
        # Ensure length matches
        if len(s) != n_frames:
            s = np.interp(frames, np.linspace(0, n_frames - 1, len(s)), s)
        ax.plot(
            frames, s,
            color=TEMPORAL_COLORS[variant],
            label=TEMPORAL_LABELS[variant],
            linestyle=TEMPORAL_STYLES[variant],
            linewidth=0.8,
            alpha=0.9,
        )

    ax.set_xlabel("Frame Number")
    ax.set_ylabel("Anomaly Score")
    ax.set_ylim(-0.02, 1.05)
    ax.set_xlim(0, n_frames)
    ax.legend(loc="upper right", framealpha=0.9, edgecolor="gray")

    category = annos[video_id].category if video_id in annos else "Unknown"
    ax.set_title(f"{video_id} ({category})")

    fig.tight_layout(pad=0.3)
    out_path = OUT_DIR / "fig_temporal_scores.pdf"
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  -> {out_path} ({out_path.stat().st_size} bytes)")


# =============================================================================
# Figure 3: 4-Way Backbone Comparison Bar Chart
# =============================================================================

def fig_backbone_comparison():
    """Figure 3: Grouped bar chart comparing 4 backbones on UCF and XD."""
    print("\n[Fig 3] Backbone Comparison")

    csv_path = RESULTS_DIR / "phase10_charts" / "backbone_comparison_4way.csv"
    seed_csv = RESULTS_DIR / "phase10_charts" / "seed_stability_4way.csv"

    comp = pd.read_csv(csv_path)
    seed_df = pd.read_csv(seed_csv)

    # Filter to main variants for paper (Visual-Only, Late Fusion, Gated Fusion)
    paper_variants = ["CLIP/SigLIP2/SO400M/Giant Only", "Late Fusion", "Gated Fusion"]
    paper_labels = ["Visual Only", "Late Fusion", "Gated Fusion"]

    # Compute error bars from seed stability (Gated Fusion only)
    gf_errors = {}
    for dataset in ["UCF", "XD"]:
        sub = seed_df[seed_df["Dataset"] == dataset]
        metric = "AUC" if dataset == "UCF" else "AP"
        gf_errors[dataset] = {}
        for bb in ["CLIP", "SigLIP2", "SO400M", "Giant"]:
            col = f"{bb}_{metric}"
            if col in sub.columns and sub[col].notna().any():
                gf_errors[dataset][bb] = sub[col].std() * 100  # convert to %
            else:
                gf_errors[dataset][bb] = 0.0

    fig, axes = plt.subplots(1, 2, figsize=(ACM_TEXT_WIDTH, 2.2))
    backbones = ["CLIP", "SigLIP2", "SO400M", "Giant"]
    n_bb = len(backbones)
    width = 0.18

    for ax_idx, (ax, dataset) in enumerate(zip(axes, ["UCF", "XD"])):
        metric = "AUC" if dataset == "UCF" else "AP"
        sub = comp[comp["Dataset"] == dataset]

        x = np.arange(len(paper_variants))

        for bb_idx, bb in enumerate(backbones):
            col = f"{bb}_{metric}"
            vals = []
            errs = []
            for vi, variant in enumerate(paper_variants):
                row = sub[sub["Variant"] == variant]
                if not row.empty and col in row.columns and row[col].notna().any():
                    vals.append(float(row[col].iloc[0]) * 100)
                else:
                    vals.append(0)
                # Error bars only for Gated Fusion
                if variant == "Gated Fusion":
                    errs.append(gf_errors[dataset].get(bb, 0))
                else:
                    errs.append(0)

            style = BACKBONE_STYLES[bb]
            offset = (bb_idx - (n_bb - 1) / 2) * width
            bars = ax.bar(
                x + offset, vals, width * 0.9,
                label=style["label"] if ax_idx == 0 else "_nolegend_",
                color=style["color"],
                hatch=style["hatch"],
                edgecolor="white",
                linewidth=0.3,
                yerr=errs if any(e > 0 for e in errs) else None,
                capsize=2,
                error_kw={"linewidth": 0.5},
            )

            # Value labels on bars
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.3,
                        f"{val:.1f}",
                        ha="center", va="bottom",
                        fontsize=FONT_ANNOTATION,
                        rotation=90,
                    )

        ax.set_ylabel(f"{metric} (%)")
        ax.set_title(f"{'UCF-Crime' if dataset == 'UCF' else 'XD-Violence'}")
        ax.set_xticks(x)
        ax.set_xticklabels(paper_labels)

        # Set y-axis range with headroom for labels
        all_vals = []
        for bb in backbones:
            col = f"{bb}_{metric}"
            for variant in paper_variants:
                row = sub[sub["Variant"] == variant]
                if not row.empty and col in row.columns and row[col].notna().any():
                    all_vals.append(float(row[col].iloc[0]) * 100)
        if all_vals:
            ymin = max(0, min(all_vals) - 8)
            ymax = max(all_vals) + 8
            ax.set_ylim(ymin, ymax)

    # Single legend spanning both subplots
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4,
               bbox_to_anchor=(0.5, 1.02), frameon=False)

    fig.tight_layout(pad=0.4, rect=[0, 0, 1, 0.92])
    out_path = OUT_DIR / "fig_backbone_comparison.pdf"
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  -> {out_path} ({out_path.stat().st_size} bytes)")


# =============================================================================
# Figure 4: Gating Weight Distribution by Category
# =============================================================================

def fig_gating_distribution():
    """Figure 4: Per-category AUC/AP comparison showing modality contribution.

    Uses per_category.csv from eval_metrics.json to show how different crime
    categories benefit differently from fusion (proxy for modality preference).
    This avoids requiring GPU inference to extract raw gate values.
    """
    print("\n[Fig 4] Gating Distribution (per-category analysis)")

    # Load per-category metrics for multiple variants
    variants = {
        "Skeleton": ("ucf_skeleton_only_s42", "xd_skeleton_only_s42"),
        "Visual":   ("ucf_clip_only_s42",     "xd_clip_only_s42"),
        "Gated":    ("ucf_gated_fusion_s42",  "xd_gated_fusion_s42"),
    }

    fig, axes = plt.subplots(1, 2, figsize=(ACM_TEXT_WIDTH, 2.4))

    for ax_idx, (ax, (dataset, metric)) in enumerate(
        zip(axes, [("UCF", "AUC"), ("XD", "AP")])
    ):
        ds_key = "ucf" if dataset == "UCF" else "xd"
        all_cats = set()
        variant_data = {}

        for var_label, (ucf_run, xd_run) in variants.items():
            run = ucf_run if ds_key == "ucf" else xd_run
            metrics_path = RESULTS_DIR / run / "eval_metrics.json"
            if not metrics_path.exists():
                continue
            with open(metrics_path) as f:
                data = json.load(f)
            cat_data = data.get("per_category", {})
            mapped = {}
            for cat, vals in cat_data.items():
                display_cat = XD_CAT_NAMES.get(cat, cat) if ds_key == "xd" else cat
                mapped[display_cat] = vals[metric.lower()] * 100
                all_cats.add(display_cat)
            variant_data[var_label] = mapped

        cats = sorted(all_cats)
        x = np.arange(len(cats))
        width = 0.25

        colors = {"Skeleton": "#7f8c8d", "Visual": "#2c3e50", "Gated": "#e74c3c"}
        hatches = {"Skeleton": "...", "Visual": "///", "Gated": ""}

        for vi, (var_label, cat_vals) in enumerate(variant_data.items()):
            vals = [cat_vals.get(c, 0) for c in cats]
            offset = (vi - 1) * width
            ax.bar(
                x + offset, vals, width * 0.9,
                label=var_label if ax_idx == 0 else "_nolegend_",
                color=colors[var_label],
                hatch=hatches[var_label],
                edgecolor="white",
                linewidth=0.3,
            )

        ax.set_ylabel(f"{metric} (%)")
        title = "UCF-Crime" if dataset == "UCF" else "XD-Violence"
        ax.set_title(f"Per-Category {metric} ({title})")
        ax.set_xticks(x)
        ax.set_xticklabels(cats, rotation=35, ha="right")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 1.02), frameon=False)

    fig.tight_layout(pad=0.4, rect=[0, 0, 1, 0.92])
    out_path = OUT_DIR / "fig_gating_distribution.pdf"
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  -> {out_path} ({out_path.stat().st_size} bytes)")


# =============================================================================
# Figure 5: TTA Comparison Across Backbones
# =============================================================================

def fig_tta_comparison():
    """Figure: discriminative-reliability reweighting (Ours) vs source-only across
    4 backbones. 3-seed (42,123,2024) mean AUC; entropy TTA (TENT/SAR) is omitted as
    it changes AUC by <0.1 pp vs source-only (validated 3-seed finding; the earlier
    "<=0.004 pp" bound was retracted). Data: results/_coral_derisk/
    r1full_*.json (s42) + variants/v_*_{s123,s2024}_test.json (TTA-boost study, 2026-06-07)."""
    print("\n[Fig] TTA Comparison (disc_reweight vs source, 3-seed)")

    bbs = ["CLIP\nViT-B/16", "SigLIP2\nBase", "SigLIP2\nSO400M", "SigLIP2\nGiant"]
    source_mean = [63.71, 57.01, 58.87, 62.83]
    source_std = [0.25, 1.40, 1.78, 0.53]
    ours_mean = [64.38, 58.50, 61.11, 63.2505]  # Giant 63.2505 -> label 63.3, matches Table 3
    ours_std = [0.13, 0.27, 1.58, 0.58]
    delta_mean = [0.67, 1.50, 2.24, 0.42]

    fig, ax = plt.subplots(figsize=(ACM_COL_WIDTH, 2.0))
    x = np.arange(len(bbs))
    width = 0.34

    ax.bar(x - width / 2, source_mean, width, yerr=source_std, capsize=2,
           label="Source-Only", color="#7f8c8d", edgecolor="white", linewidth=0.3,
           error_kw=dict(lw=0.6))
    ax.bar(x + width / 2, ours_mean, width, yerr=ours_std, capsize=2,
           label="Ours", color="#e74c3c", edgecolor="white", linewidth=0.3,
           error_kw=dict(lw=0.6))

    for xi, (s, o, dm) in enumerate(zip(source_mean, ours_mean, delta_mean)):
        ax.text(xi - width / 2, s + 0.25, f"{s:.1f}", ha="center", va="bottom",
                fontsize=FONT_ANNOTATION)
        ax.text(xi + width / 2, o + 0.25, f"{o:.1f}", ha="center", va="bottom",
                fontsize=FONT_ANNOTATION)
        ax.annotate(f"+{dm:.2f}", xy=(xi + width / 2, o), xytext=(xi + width / 2, o + 1.7),
                    ha="center", fontsize=FONT_ANNOTATION, color="#e74c3c")

    ax.set_ylabel("Mean AUC (%)")
    ax.set_title("Reweighting vs Source-Only (3 seeds, 20 corruptions)")
    ax.set_xticks(x)
    ax.set_xticklabels(bbs)
    ax.legend(loc="upper center", ncol=2, framealpha=0.9, edgecolor="gray",
              columnspacing=1.0, handletextpad=0.5)
    ax.set_ylim(54, 67)

    fig.tight_layout(pad=0.3)
    out_path = OUT_DIR / "fig_tta_comparison.pdf"
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  -> {out_path} ({out_path.stat().st_size} bytes)")
    return True


# =============================================================================
# Main
# =============================================================================

def main():
    print("Publication Figure Generation (CGW '26)")
    print("=" * 50)
    print(f"Output: {OUT_DIR}")
    print(f"DPI: {PUB_DPI}, Column width: {ACM_COL_WIDTH}in, Text width: {ACM_TEXT_WIDTH}in")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _setup_style()

    fig_temporal_scores()
    fig_backbone_comparison()
    fig_gating_distribution()
    tta_ok = fig_tta_comparison()

    # Summary
    figs = list(OUT_DIR.glob("fig_*.pdf"))
    print(f"\nDone! Generated {len(figs)} PDF figures:")
    for f in sorted(figs):
        print(f"  {f.name}: {f.stat().st_size:,} bytes")
    if not tta_ok:
        print("  [NOTE] fig_tta_comparison.pdf was SKIPPED (summary.csv missing)")


if __name__ == "__main__":
    main()
