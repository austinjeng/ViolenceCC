#!/usr/bin/env python
"""Phase 7 sweep visualization: heatmaps + summary tables (D-14).

Reads results/results-index.csv, filters to phase7 sweep runs, and generates:
  S01 -- XD-Violence: 19x6 lr x k_topk AP heatmap (PNG)
  S02 -- XD-Violence: Markdown summary table sorted by AP descending
  S03 -- Confirmation comparison (3-seed mean +/- std for both datasets)
  S04 -- UCF-Crime: 19x6 lr x k_topk AUC heatmap (PNG)
  S05 -- UCF-Crime: Markdown summary table sorted by AUC descending

Usage:
    python scripts/generate_phase7_charts.py
    python scripts/generate_phase7_charts.py --with-confirm  # after 3-seed runs

Output: results/phase7_charts/
"""
from __future__ import annotations

import argparse
import re
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
RESULTS_DIR = PROJECT_ROOT / "results"
OUT_DIR = RESULTS_DIR / "phase7_charts"

# --- Style -------------------------------------------------------------------
DPI = 150
TITLE_SZ = 16
LABEL_SZ = 13
TICK_SZ = 10

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

# Phase 4c baselines
XD_BASELINE_AP = 0.7192   # xd_gated_fusion_s42
UCF_BASELINE_AUC = 0.8227  # ucf_gated_fusion_s42

# Sweep run_name pattern: xd_gated_fusion_lr<code>_k<k>_s42
_SWEEP_PATTERN_XD = re.compile(r"^xd_gated_fusion_lr\w+_k\d+_s42$")
_SWEEP_PATTERN_UCF = re.compile(r"^ucf_gated_fusion_lr\w+_k\d+_s42$")
# Confirmation pattern: any seed
_CONFIRM_PATTERN = re.compile(r"^(xd|ucf)_gated_fusion_lr\w+_k\d+_s\d+$")


# --- Parsers -----------------------------------------------------------------
def _parse_lr_from_name(run_name: str) -> float:
    """Extract lr value from run_name.

    Handles both integer and decimal coefficients:
      xd_gated_fusion_lr5e5_k1_s42 -> 5e-5
      xd_gated_fusion_lr6p5e4_k2_s42 -> 6.5e-4
    """
    m = re.search(r"_lr(\w+?)_k\d+_s", run_name)
    if m is None:
        raise ValueError(f"Cannot parse lr from run_name: {run_name!r}")
    code = m.group(1)
    # Replace 'p' back to '.' for decimal coefficients
    code = code.replace("p", ".")
    # Split on 'e' and reconstruct with negative exponent
    parts = code.split("e")
    return float(f"{parts[0]}e-{parts[1]}")


def _parse_k_from_name(run_name: str) -> int:
    """Extract k_topk from run_name: xd_gated_fusion_lr5e5_k1_s42 -> 1."""
    m = re.search(r"_k(\d+)_s", run_name)
    if m is None:
        raise ValueError(f"Cannot parse k_topk from run_name: {run_name!r}")
    return int(m.group(1))


# --- Data Loading ------------------------------------------------------------
def _load_sweep_data(
    pattern: re.Pattern, results_dir: Path | None = None,
) -> pd.DataFrame:
    """Load and filter results-index.csv to sweep runs matching pattern.

    Returns a DataFrame with columns: run_name, lr_val, k_val, ap, auc.
    """
    rdir = results_dir or RESULTS_DIR
    csv_path = rdir / "results-index.csv"
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    if "run_name" not in df.columns:
        return pd.DataFrame()

    mask = df["run_name"].str.match(pattern, na=False)
    sweep = df[mask].copy()

    if sweep.empty:
        return pd.DataFrame()

    sweep["lr_val"] = sweep["run_name"].apply(_parse_lr_from_name)
    sweep["k_val"] = sweep["run_name"].apply(_parse_k_from_name)

    for col in ("ap", "auc"):
        if col in sweep.columns:
            sweep[col] = pd.to_numeric(sweep[col], errors="coerce")

    return sweep


# --- S01: XD Sweep Heatmap --------------------------------------------------
def generate_sweep_heatmap(
    df: pd.DataFrame, output_dir: Path, *,
    metric: str = "ap",
    baseline: float = 0.7192,
    baseline_lr: float = 1e-4,
    baseline_k: int = 3,
    title: str = "XD-Violence: Phase 7 Sweep AP Heatmap (lr x k_topk)",
    filename: str = "S01_sweep_heatmap_ap.png",
    baseline_label: str = "P4c baseline",
) -> None:
    """Generate lr x k_topk heatmap for the given metric."""
    pivot = df.pivot_table(values=metric, index="lr_val", columns="k_val")
    pivot = pivot.sort_index(ascending=True)

    # Format y-axis labels as scientific notation
    y_labels = [f"{lr:.1e}" for lr in pivot.index]

    # Figure size adapts to grid dimensions
    n_rows, n_cols = pivot.shape
    fig_w = max(10, n_cols * 1.8 + 2)
    fig_h = max(7, n_rows * 0.55 + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # Annotation font size adapts to grid density
    annot_sz = max(7, min(11, 200 // max(n_rows, n_cols)))

    sns.heatmap(
        pivot, annot=True, fmt=".4f", cmap="RdYlGn",
        ax=ax, linewidths=0.5,
        annot_kws={"size": annot_sz},
        cbar_kws={"label": metric.upper()},
        xticklabels=[str(int(k)) for k in pivot.columns],
        yticklabels=y_labels,
    )

    # Highlight baseline cell if present
    if baseline_lr in pivot.index and baseline_k in pivot.columns:
        row_idx = list(pivot.index).index(baseline_lr)
        col_idx = list(pivot.columns).index(baseline_k)
        ax.add_patch(plt.Rectangle(
            (col_idx, row_idx), 1, 1,
            fill=False, edgecolor="blue", linewidth=3, linestyle="--",
        ))
        ax.annotate(
            baseline_label,
            xy=(col_idx + 0.5, row_idx + 0.5),
            xytext=(col_idx + 1.3, row_idx - 0.3),
            fontsize=9, color="blue", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="blue", lw=1.5),
        )

    ax.set_title(title, fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xlabel("k_topk", fontsize=LABEL_SZ)
    ax.set_ylabel("Learning Rate", fontsize=LABEL_SZ)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=TICK_SZ)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=TICK_SZ, rotation=0)
    fig.tight_layout()

    out_path = output_dir / filename
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {out_path}")


# --- S02/S05: Summary Table -------------------------------------------------
def generate_sweep_table(
    df: pd.DataFrame, output_dir: Path, *,
    metric: str = "ap",
    baseline: float = 0.7192,
    title: str = "Phase 7 XD Sweep Results Summary",
    baseline_desc: str = "Phase 4c, lr=1e-4, k=3",
    filename: str = "S02_sweep_summary.md",
) -> None:
    """Markdown summary table sorted by metric descending."""
    sorted_df = df.sort_values(metric, ascending=False).reset_index(drop=True)

    lines = [
        f"# {title}",
        "",
        f"Baseline ({baseline_desc}): {metric.upper()} = {baseline:.4f}",
        "",
        f"| Rank | LR | k_topk | AP | AUC | Delta vs Baseline |",
        "|------|-----|--------|------|------|-------------------|",
    ]

    for i, row in sorted_df.iterrows():
        lr = row["lr_val"]
        k = int(row["k_val"])
        ap = row.get("ap", float("nan"))
        auc = row.get("auc", float("nan"))
        val = row.get(metric, float("nan"))
        delta = val - baseline if not pd.isna(val) else float("nan")
        sign = "+" if delta >= 0 else ""
        lines.append(
            f"| {i + 1} | {lr:.1e} | {k} | {ap:.4f} | "
            f"{auc:.4f} | {sign}{delta:.4f} ({sign}{delta * 100:.2f}pp) |"
        )

    if not sorted_df.empty:
        best = sorted_df.iloc[0]
        lines.extend([
            "",
            f"**Best config:** lr={best['lr_val']:.1e}, k_topk={int(best['k_val'])}, "
            f"{metric.upper()}={best[metric]:.4f}",
        ])

    out_path = output_dir / filename
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [saved] {out_path}")


# --- S03: Confirmation Comparison -------------------------------------------
def generate_confirmation_comparison(output_dir: Path) -> None:
    """S03: 3-seed comparison table for both XD and UCF winners vs baselines."""
    csv_path = RESULTS_DIR / "results-index.csv"
    if not csv_path.exists():
        print("  [WARN] No results-index.csv for confirmation comparison")
        return

    df = pd.read_csv(csv_path)
    mask = df["run_name"].str.match(_CONFIRM_PATTERN, na=False)
    confirm = df[mask].copy()

    if confirm.empty:
        print("  [WARN] No phase7 confirmation data found")
        return

    confirm["lr_val"] = confirm["run_name"].apply(_parse_lr_from_name)
    confirm["k_val"] = confirm["run_name"].apply(_parse_k_from_name)
    confirm["dataset"] = confirm["run_name"].apply(
        lambda n: "XD" if n.startswith("xd_") else "UCF"
    )
    confirm["ap"] = pd.to_numeric(confirm["ap"], errors="coerce")
    confirm["auc"] = pd.to_numeric(confirm["auc"], errors="coerce")

    lines = [
        "# Phase 7 Confirmation Comparison (3-seed)",
        "",
        "## XD-Violence (metric: AP)",
        "",
        "Phase 4c baseline: AP = 70.98% +/- 1.08% (3-seed mean)",
        "",
        "| LR | k_topk | s42 AP | s123 AP | s2024 AP | Mean AP | Std | Delta vs P4c |",
        "|-----|--------|--------|---------|----------|---------|-----|-------------|",
    ]

    # XD confirmation configs
    xd = confirm[confirm["dataset"] == "XD"]
    xd_grouped = xd.groupby(["lr_val", "k_val"])
    for (lr, k), group in sorted(
        xd_grouped, key=lambda x: -x[1]["ap"].mean()
    ):
        if len(group) < 3:
            continue
        aps = group.sort_values("run_name")["ap"].values
        mean_ap = np.mean(aps)
        std_ap = np.std(aps)
        delta = mean_ap - 0.7098
        sign = "+" if delta >= 0 else ""
        lines.append(
            f"| {lr:.1e} | {int(k)} | {aps[0]*100:.2f}% | {aps[1]*100:.2f}% | "
            f"{aps[2]*100:.2f}% | {mean_ap*100:.2f}% | {std_ap*100:.2f}% | "
            f"{sign}{delta*100:.2f}pp |"
        )

    lines.extend([
        "",
        "## UCF-Crime (metric: AUC)",
        "",
        "Phase 4 baseline: AUC = 81.98% +/- 0.29% (3-seed mean)",
        "",
        "| LR | k_topk | s42 AUC | s123 AUC | s2024 AUC | Mean AUC | Std | Delta vs P4 |",
        "|-----|--------|---------|----------|-----------|----------|-----|------------|",
    ])

    # UCF confirmation configs
    ucf = confirm[confirm["dataset"] == "UCF"]
    ucf_grouped = ucf.groupby(["lr_val", "k_val"])
    for (lr, k), group in sorted(
        ucf_grouped, key=lambda x: -x[1]["auc"].mean()
    ):
        if len(group) < 3:
            continue
        aucs = group.sort_values("run_name")["auc"].values
        mean_auc = np.mean(aucs)
        std_auc = np.std(aucs)
        delta = mean_auc - 0.8198
        sign = "+" if delta >= 0 else ""
        lines.append(
            f"| {lr:.1e} | {int(k)} | {aucs[0]*100:.2f}% | {aucs[1]*100:.2f}% | "
            f"{aucs[2]*100:.2f}% | {mean_auc*100:.2f}% | {std_auc*100:.2f}% | "
            f"{sign}{delta*100:.2f}pp |"
        )

    out_path = output_dir / "S03_confirmation_comparison.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [saved] {out_path}")


# --- Main --------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase 7 sweep visualization: heatmaps + summary tables (D-14)"
    )
    ap.add_argument(
        "--with-confirm", action="store_true",
        help="Include 3-seed confirmation comparison (after phase7_confirm runs)",
    )
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- XD-Violence ---
    xd_df = _load_sweep_data(_SWEEP_PATTERN_XD)
    if xd_df.empty:
        print("[WARN] No XD phase7 sweep data found")
    else:
        print(f"[info] XD sweep: {len(xd_df)} configs loaded")
        generate_sweep_heatmap(
            xd_df, OUT_DIR,
            metric="ap",
            baseline=XD_BASELINE_AP,
            baseline_lr=1e-4, baseline_k=3,
            title="XD-Violence: Phase 7 Sweep AP Heatmap (lr x k_topk)",
            filename="S01_sweep_heatmap_ap.png",
            baseline_label="P4c baseline",
        )
        generate_sweep_table(
            xd_df, OUT_DIR,
            metric="ap",
            baseline=XD_BASELINE_AP,
            title="Phase 7 XD-Violence Sweep Results Summary",
            baseline_desc="Phase 4c, lr=1e-4, k=3",
            filename="S02_sweep_summary.md",
        )

    # --- UCF-Crime ---
    ucf_df = _load_sweep_data(_SWEEP_PATTERN_UCF)
    if ucf_df.empty:
        print("[WARN] No UCF phase7 sweep data found")
    else:
        print(f"[info] UCF sweep: {len(ucf_df)} configs loaded")
        generate_sweep_heatmap(
            ucf_df, OUT_DIR,
            metric="auc",
            baseline=UCF_BASELINE_AUC,
            baseline_lr=1e-4, baseline_k=3,
            title="UCF-Crime: Phase 7 Sweep AUC Heatmap (lr x k_topk)",
            filename="S04_sweep_heatmap_auc.png",
            baseline_label="P4 baseline",
        )
        generate_sweep_table(
            ucf_df, OUT_DIR,
            metric="auc",
            baseline=UCF_BASELINE_AUC,
            title="Phase 7 UCF-Crime Sweep Results Summary",
            baseline_desc="Phase 4, lr=1e-4, k=3",
            filename="S05_ucf_sweep_summary.md",
        )

    # --- Confirmation comparison ---
    if args.with_confirm:
        generate_confirmation_comparison(OUT_DIR)

    print(f"[done] Charts saved to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
