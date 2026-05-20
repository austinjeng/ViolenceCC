#!/usr/bin/env python
"""
Phase 8 CLIP vs SigLIP2 Backbone Comparison
============================================
Generates a side-by-side comparison table and grouped bar charts for the
thesis backbone ablation study.

Usage:
    conda activate vcc-main
    python scripts/generate_phase8_charts.py

Output: results/phase8_charts/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# --- Project Setup -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- Style (from Phase 6) ---------------------------------------------------
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

OUT_DIR = PROJECT_ROOT / "results" / "phase8_charts"

# --- Run Name Mapping --------------------------------------------------------
# Maps (dataset, display_label) -> (clip_run_name, siglip2_run_name)
# skeleton_only has no SigLIP2 variant (backbone-independent)
COMPARISON_MAP = {
    # UCF main variants (s42)
    ("ucf", "Skeleton Only"): ("ucf_skeleton_only_s42", None),
    ("ucf", "CLIP/SigLIP2 Only"): ("ucf_clip_only_s42", "ucf_clip_only_siglip2_s42"),
    ("ucf", "Late Fusion"): ("ucf_late_fusion_s42", "ucf_late_fusion_siglip2_s42"),
    ("ucf", "Gated Fusion"): ("ucf_gated_fusion_s42", "ucf_gated_fusion_siglip2_s42"),
    ("ucf", "GF 2-Person"): ("ucf_gated_fusion_2person_s42", "ucf_gated_fusion_siglip2_2person_s42"),
    ("ucf", "GF Mean-Only"): ("ucf_gated_fusion_clip_mean_s42", "ucf_gated_fusion_siglip2_clip_mean_s42"),
    # XD main variants (s42)
    ("xd", "Skeleton Only"): ("xd_skeleton_only_s42", None),
    ("xd", "CLIP/SigLIP2 Only"): ("xd_clip_only_s42", "xd_clip_only_siglip2_s42"),
    ("xd", "Late Fusion"): ("xd_late_fusion_s42", "xd_late_fusion_siglip2_s42"),
    ("xd", "Gated Fusion"): ("xd_gated_fusion_s42", "xd_gated_fusion_siglip2_s42"),
    ("xd", "GF 2-Person"): ("xd_gated_fusion_2person_s42", "xd_gated_fusion_siglip2_2person_s42"),
    ("xd", "GF Mean-Only"): ("xd_gated_fusion_clip_mean_s42", "xd_gated_fusion_siglip2_clip_mean_s42"),
}

SEED_MAP = {
    # 3-seed stability for Gated Fusion
    ("ucf", 42): ("ucf_gated_fusion_s42", "ucf_gated_fusion_siglip2_s42"),
    ("ucf", 123): ("ucf_gated_fusion_s123", "ucf_gated_fusion_siglip2_s123"),
    ("ucf", 2024): ("ucf_gated_fusion_s2024", "ucf_gated_fusion_siglip2_s2024"),
    ("xd", 42): ("xd_gated_fusion_s42", "xd_gated_fusion_siglip2_s42"),
    ("xd", 123): ("xd_gated_fusion_s123", "xd_gated_fusion_siglip2_s123"),
    ("xd", 2024): ("xd_gated_fusion_s2024", "xd_gated_fusion_siglip2_s2024"),
}


def load_results() -> pd.DataFrame:
    csv_path = PROJECT_ROOT / "results" / "results-index.csv"
    return pd.read_csv(csv_path)


def build_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.set_index("run_name")
    rows = []
    for (dataset, label), (clip_name, sig_name) in COMPARISON_MAP.items():
        row = {"Dataset": dataset.upper(), "Variant": label}
        if clip_name in idx.index:
            row["CLIP_AUC"] = idx.loc[clip_name, "auc"]
            row["CLIP_AP"] = idx.loc[clip_name, "ap"]
        if sig_name and sig_name in idx.index:
            row["SigLIP2_AUC"] = idx.loc[sig_name, "auc"]
            row["SigLIP2_AP"] = idx.loc[sig_name, "ap"]
            row["Delta_AUC"] = row["SigLIP2_AUC"] - row["CLIP_AUC"]
            row["Delta_AP"] = row["SigLIP2_AP"] - row["CLIP_AP"]
        rows.append(row)
    return pd.DataFrame(rows)


def build_seed_table(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.set_index("run_name")
    rows = []
    for (dataset, seed), (clip_name, sig_name) in SEED_MAP.items():
        row = {"Dataset": dataset.upper(), "Seed": seed}
        if clip_name in idx.index:
            row["CLIP_AUC"] = idx.loc[clip_name, "auc"]
            row["CLIP_AP"] = idx.loc[clip_name, "ap"]
        if sig_name in idx.index:
            row["SigLIP2_AUC"] = idx.loc[sig_name, "auc"]
            row["SigLIP2_AP"] = idx.loc[sig_name, "ap"]
            row["Delta_AUC"] = row["SigLIP2_AUC"] - row["CLIP_AUC"]
            row["Delta_AP"] = row["SigLIP2_AP"] - row["CLIP_AP"]
        rows.append(row)
    return pd.DataFrame(rows)


def plot_comparison_bars(comp: pd.DataFrame, metric: str, title: str,
                         filename: str) -> None:
    clip_col = f"CLIP_{metric}"
    sig_col = f"SigLIP2_{metric}"
    plot_df = comp[comp[sig_col].notna()].copy()
    if plot_df.empty:
        return

    labels = plot_df["Dataset"] + " — " + plot_df["Variant"]
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=FIG_WIDE, dpi=DPI)
    bars1 = ax.bar(x - width / 2, plot_df[clip_col] * 100, width,
                   label="CLIP ViT-B/16", color="#3B82F6", edgecolor="white")
    bars2 = ax.bar(x + width / 2, plot_df[sig_col] * 100, width,
                   label="SigLIP2 ViT-B/16", color="#EF4444", edgecolor="white")

    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                    f"{h:.1f}", ha="center", va="bottom", fontsize=VAL_SZ)

    ax.set_ylabel(f"{metric} (%)", fontsize=LABEL_SZ)
    ax.set_title(title, fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=TICK_SZ)
    ax.legend(fontsize=LABEL_SZ)
    ax.set_ylim(bottom=max(0, plot_df[[clip_col, sig_col]].min().min() * 100 - 10))

    fig.tight_layout()
    fig.savefig(OUT_DIR / filename, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {filename}")


def plot_seed_stability(seed_df: pd.DataFrame, filename: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=FIG_WIDE, dpi=DPI)

    for ax, dataset in zip(axes, ["UCF", "XD"]):
        sub = seed_df[seed_df["Dataset"] == dataset].sort_values("Seed")
        metric = "AUC" if dataset == "UCF" else "AP"
        clip_col = f"CLIP_{metric}"
        sig_col = f"SigLIP2_{metric}"

        seeds = sub["Seed"].astype(str)
        x = np.arange(len(seeds))
        width = 0.35

        ax.bar(x - width / 2, sub[clip_col] * 100, width,
               label="CLIP", color="#3B82F6", edgecolor="white")
        ax.bar(x + width / 2, sub[sig_col] * 100, width,
               label="SigLIP2", color="#EF4444", edgecolor="white")

        clip_mean = sub[clip_col].mean() * 100
        sig_mean = sub[sig_col].mean() * 100
        clip_std = sub[clip_col].std() * 100
        sig_std = sub[sig_col].std() * 100

        ax.axhline(clip_mean, color="#3B82F6", ls="--", alpha=0.5)
        ax.axhline(sig_mean, color="#EF4444", ls="--", alpha=0.5)

        ax.set_title(
            f"{dataset}-Crime Gated Fusion {metric}\n"
            f"CLIP: {clip_mean:.2f}±{clip_std:.2f}  "
            f"SigLIP2: {sig_mean:.2f}±{sig_std:.2f}",
            fontsize=LABEL_SZ,
        )
        ax.set_xticks(x)
        ax.set_xticklabels([f"s{s}" for s in sub["Seed"]], fontsize=TICK_SZ)
        ax.set_ylabel(f"{metric} (%)", fontsize=LABEL_SZ)
        ax.legend(fontsize=TICK_SZ)
        ymin = min(sub[clip_col].min(), sub[sig_col].min()) * 100 - 2
        ax.set_ylim(bottom=ymin)

    fig.suptitle("3-Seed Stability: CLIP vs SigLIP2", fontsize=TITLE_SZ,
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / filename, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {filename}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_results()
    print(f"Loaded {len(df)} rows from results-index.csv")

    sig_count = df["cache_variant"].str.contains("siglip2", na=False).sum()
    print(f"SigLIP2 runs: {sig_count}")

    # Build comparison table
    comp = build_comparison_table(df)
    comp_path = OUT_DIR / "backbone_comparison.csv"
    comp.to_csv(comp_path, index=False, float_format="%.6f")
    print(f"\nComparison table saved to {comp_path}")
    print(comp.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    # Build seed stability table
    seed_df = build_seed_table(df)
    seed_path = OUT_DIR / "seed_stability.csv"
    seed_df.to_csv(seed_path, index=False, float_format="%.6f")
    print(f"\nSeed stability table saved to {seed_path}")
    print(seed_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    # Generate charts
    print("\nGenerating charts...")
    plot_comparison_bars(comp, "AUC", "CLIP vs SigLIP2 — AUC Comparison",
                         "backbone_comparison_auc.png")
    plot_comparison_bars(comp, "AP", "CLIP vs SigLIP2 — AP Comparison",
                         "backbone_comparison_ap.png")
    plot_seed_stability(seed_df, "seed_stability.png")

    print("\nDone.")


if __name__ == "__main__":
    main()
