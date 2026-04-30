#!/usr/bin/env python
"""Phase 7 sweep visualization: heatmap + summary table (D-14).

Reads results/results-index.csv, filters to phase7 sweep runs, and generates:
  S01 -- 5x4 lr x k_topk AP heatmap (PNG)
  S02 -- Markdown summary table sorted by AP descending
  S03 -- Confirmation comparison (3-seed mean +/- std, after phase7_confirm)

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

# ─── Project Setup ───────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
OUT_DIR = RESULTS_DIR / "phase7_charts"

# ─── Style ───────────────────────────────────────────────────────────────────
DPI = 150
TITLE_SZ = 18
LABEL_SZ = 14
TICK_SZ = 12

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

# Phase 4c baseline for delta comparison
BASELINE_AP = 0.7192  # xd_gated_fusion_s42

# Sweep grid constants (must match run_ablations.py)
LR_VALUES = [5e-5, 1e-4, 2e-4, 3e-4, 5e-4]
K_VALUES = [1, 3, 5, 7]

# Regex for matching phase7 sweep run_names: xd_gated_fusion_lr<coeff>e<exp>_k<k>_s42
_SWEEP_PATTERN = re.compile(r"^xd_gated_fusion_lr\d+e\d+_k\d+_s42$")


# ─── Parsers ─────────────────────────────────────────────────────────────────
def _parse_lr_from_name(run_name: str) -> float:
    """Extract lr value from run_name: xd_gated_fusion_lr5e5_k1_s42 -> 5e-5.

    Reverses _fmt_lr(): extracts lr<coeff>e<exp> group and converts back
    to float by inserting a minus sign before the exponent digit group.
    E.g., "5e5" -> "5e-5" -> 5e-5, "1e4" -> "1e-4" -> 1e-4.
    """
    m = re.search(r"_lr(\d+e)(\d+)_", run_name)
    if m is None:
        raise ValueError(f"Cannot parse lr from run_name: {run_name!r}")
    return float(f"{m.group(1)}-{m.group(2)}")


def _parse_k_from_name(run_name: str) -> int:
    """Extract k_topk from run_name: xd_gated_fusion_lr5e5_k1_s42 -> 1."""
    m = re.search(r"_k(\d+)_s", run_name)
    if m is None:
        raise ValueError(f"Cannot parse k_topk from run_name: {run_name!r}")
    return int(m.group(1))


# ─── Data Loading ────────────────────────────────────────────────────────────
def _load_sweep_data(results_dir: Path | None = None) -> pd.DataFrame:
    """Load and filter results-index.csv to phase7 sweep runs.

    Returns a DataFrame with columns: run_name, lr_val, k_val, ap, auc.
    """
    rdir = results_dir or RESULTS_DIR
    csv_path = rdir / "results-index.csv"
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    if "run_name" not in df.columns:
        return pd.DataFrame()

    # Filter to phase7 sweep runs (seed=42, lr+k override pattern)
    mask = df["run_name"].str.match(_SWEEP_PATTERN, na=False)
    sweep = df[mask].copy()

    if sweep.empty:
        return pd.DataFrame()

    # Parse lr and k from run_name
    sweep["lr_val"] = sweep["run_name"].apply(_parse_lr_from_name)
    sweep["k_val"] = sweep["run_name"].apply(_parse_k_from_name)

    # Ensure numeric columns
    for col in ("ap", "auc"):
        if col in sweep.columns:
            sweep[col] = pd.to_numeric(sweep[col], errors="coerce")

    return sweep


# ─── S01: Sweep Heatmap ─────────────────────────────────────────────────────
def generate_sweep_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    """S01: 5x4 lr x k_topk AP heatmap."""
    pivot = df.pivot_table(values="ap", index="lr_val", columns="k_val")
    pivot = pivot.sort_index(ascending=True)

    # Format y-axis labels as scientific notation
    y_labels = [f"{lr:.0e}" for lr in pivot.index]

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(
        pivot, annot=True, fmt=".4f", cmap="RdYlGn",
        ax=ax, linewidths=0.5,
        cbar_kws={"label": "AP"},
        xticklabels=[str(k) for k in pivot.columns],
        yticklabels=y_labels,
    )

    # Highlight Phase 4c baseline cell (lr=1e-4, k=3) if present
    if 1e-4 in pivot.index and 3 in pivot.columns:
        row_idx = list(pivot.index).index(1e-4)
        col_idx = list(pivot.columns).index(3)
        ax.add_patch(plt.Rectangle(
            (col_idx, row_idx), 1, 1,
            fill=False, edgecolor="blue", linewidth=3, linestyle="--",
        ))
        ax.annotate(
            "P4c baseline",
            xy=(col_idx + 0.5, row_idx + 0.5),
            xytext=(col_idx + 1.3, row_idx - 0.3),
            fontsize=9, color="blue", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="blue", lw=1.5),
        )

    ax.set_title(
        "XD-Violence: Phase 7 Sweep AP Heatmap (lr x k_topk)",
        fontsize=TITLE_SZ, fontweight="bold",
    )
    ax.set_xlabel("k_topk", fontsize=LABEL_SZ)
    ax.set_ylabel("Learning Rate", fontsize=LABEL_SZ)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=TICK_SZ)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=TICK_SZ, rotation=0)
    fig.tight_layout()

    out_path = output_dir / "S01_sweep_heatmap_ap.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {out_path}")


# ─── S02: Summary Table ─────────────────────────────────────────────────────
def generate_sweep_table(df: pd.DataFrame, output_dir: Path) -> None:
    """S02: Markdown summary table sorted by AP descending."""
    sorted_df = df.sort_values("ap", ascending=False).reset_index(drop=True)

    lines = [
        "# Phase 7 Sweep Results Summary",
        "",
        f"Baseline (Phase 4c, lr=1e-4, k=3): AP = {BASELINE_AP:.4f}",
        "",
        "| Rank | LR | k_topk | AP | AUC | Delta vs Baseline |",
        "|------|-----|--------|------|------|-------------------|",
    ]

    for i, row in sorted_df.iterrows():
        lr = row["lr_val"]
        k = int(row["k_val"])
        ap = row.get("ap", float("nan"))
        auc = row.get("auc", float("nan"))
        delta = ap - BASELINE_AP if not pd.isna(ap) else float("nan")
        sign = "+" if delta >= 0 else ""
        lines.append(
            f"| {i + 1} | {lr:.0e} | {k} | {ap:.4f} | "
            f"{auc:.4f} | {sign}{delta:.4f} ({sign}{delta * 100:.2f}pp) |"
        )

    # Best config highlight
    if not sorted_df.empty:
        best = sorted_df.iloc[0]
        lines.extend([
            "",
            f"**Best config:** lr={best['lr_val']:.0e}, k_topk={int(best['k_val'])}, "
            f"AP={best['ap']:.4f}",
        ])

    out_path = output_dir / "S02_sweep_summary.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [saved] {out_path}")


# ─── S03: Confirmation Comparison ───────────────────────────────────────────
def generate_confirmation_comparison(output_dir: Path) -> None:
    """S03: 3-seed comparison table (called after phase7_confirm).

    Compares the winning sweep config across 3 seeds vs Phase 4c 3-seed
    baseline (mean 70.97% +/- 1.08%).
    """
    csv_path = RESULTS_DIR / "results-index.csv"
    if not csv_path.exists():
        print("  [WARN] No results-index.csv for confirmation comparison")
        return

    df = pd.read_csv(csv_path)
    # Confirmation runs match: xd_gated_fusion_lr*_k*_s{42,123,2024}
    confirm_pattern = re.compile(r"^xd_gated_fusion_lr\d+e\d+_k\d+_s\d+$")
    mask = df["run_name"].str.match(confirm_pattern, na=False)
    confirm = df[mask].copy()

    if confirm.empty:
        print("  [WARN] No phase7_confirm data found; stub output written")
        out_path = output_dir / "S03_confirmation_comparison.md"
        out_path.write_text(
            "# Phase 7 Confirmation Comparison\n\n"
            "**Awaiting phase7_confirm run data.**\n"
            "This table will be populated after 3-seed confirmation runs complete.\n\n"
            "Phase 4c baseline: AP = 70.97% +/- 1.08% (3-seed)\n",
            encoding="utf-8",
        )
        print(f"  [saved] {out_path} (stub)")
        return

    # Parse lr/k from run names for grouping
    confirm["lr_val"] = confirm["run_name"].apply(_parse_lr_from_name)
    confirm["k_val"] = confirm["run_name"].apply(_parse_k_from_name)
    confirm["ap"] = pd.to_numeric(confirm["ap"], errors="coerce")

    # Group by (lr, k) to find configs with 3 seeds
    grouped = confirm.groupby(["lr_val", "k_val"])["ap"].agg(["mean", "std", "count"])
    multi_seed = grouped[grouped["count"] >= 3].sort_values("mean", ascending=False)

    if multi_seed.empty:
        print("  [WARN] No configs with 3+ seeds found")
        return

    lines = [
        "# Phase 7 Confirmation Comparison",
        "",
        "Phase 4c baseline: AP = 70.97% +/- 1.08% (3-seed mean)",
        "",
        "| LR | k_topk | 3-seed Mean AP | Std | Delta vs P4c |",
        "|-----|--------|---------------|-----|-------------|",
    ]

    for (lr, k), row in multi_seed.iterrows():
        delta = row["mean"] - 0.7097
        sign = "+" if delta >= 0 else ""
        lines.append(
            f"| {lr:.0e} | {int(k)} | {row['mean']:.4f} | "
            f"{row['std']:.4f} | {sign}{delta:.4f} ({sign}{delta * 100:.2f}pp) |"
        )

    out_path = output_dir / "S03_confirmation_comparison.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [saved] {out_path}")


# ─── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase 7 sweep visualization: heatmap + summary table (D-14)"
    )
    ap.add_argument(
        "--with-confirm", action="store_true",
        help="Include 3-seed confirmation comparison (after phase7_confirm runs)",
    )
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = _load_sweep_data()
    if df.empty:
        print("[WARN] No phase7 sweep data found in results-index.csv")
        return 0

    generate_sweep_heatmap(df, OUT_DIR)
    generate_sweep_table(df, OUT_DIR)

    if args.with_confirm:
        generate_confirmation_comparison(OUT_DIR)

    print(f"[done] Charts saved to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
