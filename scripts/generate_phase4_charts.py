#!/usr/bin/env python
"""
Phase 4 Results Visualization — UCF-Crime & XD-I3D
===================================================
Generates ~80 presentation-ready PNG charts for supervisor report.

Usage:
    conda activate vcc-main
    python scripts/generate_phase4_charts.py

Output: results/phase4_charts/
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
from sklearn.metrics import (
    roc_curve,
    precision_recall_curve,
    confusion_matrix as sk_confusion_matrix,
    roc_auc_score,
    average_precision_score,
)

# ─── Project Setup ───────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eval.ucf_annotations import parse_annotations, frame_labels
from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels

RESULTS_DIR = PROJECT_ROOT / "results"
OUT_DIR = RESULTS_DIR / "phase4_charts"

# ─── Style ───────────────────────────────────────────────────────────────────
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

# ─── Variant Definitions ────────────────────────────────────────────────────
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
UCF_MAIN = ["skeleton_only", "clip_only", "late_fusion", "gated_fusion"]
UCF_RUNS = {
    "skeleton_only": "ucf_skeleton_only_s42",
    "clip_only": "ucf_clip_only_s42",
    "late_fusion": "ucf_late_fusion_s42",
    "gated_fusion": "ucf_gated_fusion_s42",
}
XD_COLORS = {"rtfm_i3d": "#3B82F6", "rtfm_i3d_flow": "#10B981"}
XD_LABELS = {"rtfm_i3d": "RTFM I3D (RGB)", "rtfm_i3d_flow": "RTFM I3D (RGB+Flow)"}
XD_RUNS = {
    "rtfm_i3d": "xd_i3d_rtfm_i3d_s42",
    "rtfm_i3d_flow": "xd_i3d_rtfm_i3d_flow_s42",
}

ALL_RUNS = [
    "ucf_skeleton_only_s42",
    "ucf_clip_only_s42",
    "ucf_late_fusion_s42",
    "ucf_gated_fusion_s42",
    "ucf_gated_fusion_2person_s42",
    "ucf_gated_fusion_clip_mean_s42",
    "ucf_gated_fusion_s123",
    "ucf_gated_fusion_s2024",
    "xd_i3d_rtfm_i3d_s42",
    "xd_i3d_rtfm_i3d_flow_s42",
]
RUN_DISPLAY = {
    "ucf_skeleton_only_s42": "Skeleton Only (s42)",
    "ucf_clip_only_s42": "CLIP Only (s42)",
    "ucf_late_fusion_s42": "Late Fusion (s42)",
    "ucf_gated_fusion_s42": "Gated Fusion (s42)",
    "ucf_gated_fusion_2person_s42": "Gated 2-Person (s42)",
    "ucf_gated_fusion_clip_mean_s42": "Gated CLIP-Mean (s42)",
    "ucf_gated_fusion_s123": "Gated Fusion (s123)",
    "ucf_gated_fusion_s2024": "Gated Fusion (s2024)",
    "xd_i3d_rtfm_i3d_s42": "RTFM I3D RGB (s42)",
    "xd_i3d_rtfm_i3d_flow_s42": "RTFM I3D RGB+Flow (s42)",
}

SEED_RUNS = [
    "ucf_gated_fusion_s42",
    "ucf_gated_fusion_s123",
    "ucf_gated_fusion_s2024",
]
ABLATION = {
    "Baseline\n(max-pool)": "ucf_gated_fusion_s42",
    "2-Person\n(concat)": "ucf_gated_fusion_2person_s42",
    "CLIP Mean\n(mean only)": "ucf_gated_fusion_clip_mean_s42",
}


# ─── Data Loading ────────────────────────────────────────────────────────────


def load_all_data() -> dict:
    data: dict = {}
    data["index"] = pd.read_csv(RESULTS_DIR / "results-index.csv")

    metrics, cats, logs = {}, {}, {}
    for run in ALL_RUNS:
        d = RESULTS_DIR / run
        with open(d / "eval_metrics.json") as f:
            metrics[run] = json.load(f)
        cats[run] = pd.read_csv(d / "per_category.csv")
        logs[run] = pd.read_csv(d / "train_log.csv")

    data["metrics"] = metrics
    data["cats"] = cats
    data["logs"] = logs
    return data


def load_curves() -> dict:
    ucf_ann = PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    xd_ann = PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"
    ucf_annos = parse_annotations(ucf_ann)
    xd_annos = parse_xd_annotations(xd_ann)

    curves: dict = {}
    for run in ALL_RUNS:
        sp = RESULTS_DIR / run / "eval_scores.npz"
        if not sp.exists():
            print(f"  SKIP {run}: no eval_scores.npz")
            continue

        npz = np.load(sp)
        is_xd = run.startswith("xd_")
        annos = xd_annos if is_xd else ucf_annos
        label_fn = xd_frame_labels if is_xd else frame_labels

        all_s, all_l = [], []
        v_max, v_lbl = [], []
        for vid in npz.files:
            s = npz[vid]
            nf = len(s)
            lbl = label_fn(annos[vid], nf) if vid in annos else np.zeros(nf, dtype=np.int64)
            all_s.append(s)
            all_l.append(lbl)
            v_max.append(float(s.max()))
            v_lbl.append(1 if lbl.any() else 0)

        y_score = np.concatenate(all_s)
        y_true = np.concatenate(all_l)
        fpr, tpr, roc_th = roc_curve(y_true, y_score)
        prec, rec, pr_th = precision_recall_curve(y_true, y_score)

        ca = roc_auc_score(y_true, y_score)
        cp = average_precision_score(y_true, y_score)
        print(f"  {run}: AUC={ca:.6f}  AP={cp:.6f}")

        curves[run] = {
            "fpr": fpr, "tpr": tpr, "roc_th": roc_th,
            "prec": prec, "rec": rec, "pr_th": pr_th,
            "y_score": y_score, "y_true": y_true,
            "v_max": np.array(v_max), "v_lbl": np.array(v_lbl),
            "auc": ca, "ap": cp,
        }
    return curves


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _save(fig, subdir, name):
    p = OUT_DIR / subdir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"    -> {p.relative_to(RESULTS_DIR)}")


def _bar_vals(ax, bars, fmt=".4f", fs=VAL_SZ):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h, f"{h:{fmt}}",
                ha="center", va="bottom", fontsize=fs, fontweight="bold")


def _hbar_vals(ax, bars, fmt=".4f", fs=VAL_SZ):
    for b in bars:
        w = b.get_width()
        ax.text(w, b.get_y() + b.get_height() / 2, f" {w:{fmt}}",
                ha="left", va="center", fontsize=fs, fontweight="bold")


def _optimal_threshold(fpr, tpr, thresholds):
    j = tpr - fpr
    idx = np.argmax(j)
    return thresholds[idx]


# ═══════════════════════════════════════════════════════════════════════════
# A — Cross-Variant Comparison (UCF, 4 main)
# ═══════════════════════════════════════════════════════════════════════════


def chart_A01(data):
    fig, ax = plt.subplots(figsize=FIG_STD)
    labels = [VLABELS[v] for v in UCF_MAIN]
    aucs = [data["metrics"][UCF_RUNS[v]]["auc"] for v in UCF_MAIN]
    aps = [data["metrics"][UCF_RUNS[v]]["ap"] for v in UCF_MAIN]

    x = np.arange(len(UCF_MAIN))
    w = 0.35
    b1 = ax.bar(x - w / 2, aucs, w, label="AUC", color="#3B82F6", edgecolor="white")
    b2 = ax.bar(x + w / 2, aps, w, label="AP", color="#F59E0B", edgecolor="white")
    _bar_vals(ax, b1)
    _bar_vals(ax, b2)

    ax.set_ylabel("Score", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: AUC & AP by Variant", fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=TICK_SZ)
    ax.legend(fontsize=TICK_SZ)
    ax.set_ylim(0, max(max(aucs), max(aps)) * 1.18)
    _save(fig, "A_comparison", "A01_grouped_bar_auc_ap.png")


def chart_A02(data):
    fig, ax = plt.subplots(figsize=FIG_STD)
    labels = [VLABELS[v] for v in UCF_MAIN]
    aucs = [data["metrics"][UCF_RUNS[v]]["auc"] for v in UCF_MAIN]
    order = np.argsort(aucs)
    bars = ax.barh(
        [labels[i] for i in order],
        [aucs[i] for i in order],
        color=[VCOLORS[UCF_MAIN[i]] for i in order],
        edgecolor="white", height=0.6,
    )
    _hbar_vals(ax, bars)
    ax.set_xlabel("AUC", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: Frame-Level AUC", fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xlim(0.65, max(aucs) * 1.08)
    _save(fig, "A_comparison", "A02_hbar_auc.png")


def chart_A03(data):
    fig, ax = plt.subplots(figsize=FIG_STD)
    labels = [VLABELS[v] for v in UCF_MAIN]
    aps = [data["metrics"][UCF_RUNS[v]]["ap"] for v in UCF_MAIN]
    order = np.argsort(aps)
    bars = ax.barh(
        [labels[i] for i in order],
        [aps[i] for i in order],
        color=[VCOLORS[UCF_MAIN[i]] for i in order],
        edgecolor="white", height=0.6,
    )
    _hbar_vals(ax, bars)
    ax.set_xlabel("Average Precision", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: Frame-Level AP", fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xlim(0.10, max(aps) * 1.18)
    _save(fig, "A_comparison", "A03_hbar_ap.png")


def chart_A04(data):
    keys = ["auc", "ap", "snippet_auc", "video_auc"]
    klabels = ["Frame AUC", "Frame AP", "Snippet AUC", "Video AUC"]
    n = len(keys)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    for v in UCF_MAIN:
        m = data["metrics"][UCF_RUNS[v]]
        vals = [m.get(k, 0) for k in keys] + [m.get(keys[0], 0)]
        ax.plot(angles, vals, "o-", lw=2, label=VLABELS[v], color=VCOLORS[v], ms=6)
        ax.fill(angles, vals, alpha=0.08, color=VCOLORS[v])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(klabels, fontsize=TICK_SZ)
    ax.set_ylim(0, 1.05)
    ax.set_title("UCF-Crime: Multi-Metric Radar", fontsize=TITLE_SZ, fontweight="bold", pad=25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=TICK_SZ)
    _save(fig, "A_comparison", "A04_radar.png")


def chart_A05(data):
    fig, ax = plt.subplots(figsize=FIG_STD)
    base = data["metrics"]["ucf_skeleton_only_s42"]["auc"]
    clip_auc = data["metrics"]["ucf_clip_only_s42"]["auc"]
    late_auc = data["metrics"]["ucf_late_fusion_s42"]["auc"]
    gated_auc = data["metrics"]["ucf_gated_fusion_s42"]["auc"]

    steps = [
        ("Skeleton\nBaseline", base, 0, VCOLORS["skeleton_only"]),
        ("+ CLIP Signal", clip_auc - base, base, "#22C55E"),
        ("Late Fusion\nvs CLIP", late_auc - clip_auc, clip_auc, "#EF4444"),
        ("Gated Fusion\nvs Late", gated_auc - late_auc, late_auc, "#22C55E"),
    ]

    for i, (lbl, val, bot, col) in enumerate(steps):
        ax.bar(i, val, bottom=bot, color=col, edgecolor="white", width=0.6, alpha=0.85)
        top = bot + val
        ax.text(i, top + 0.003, f"{top:.4f}", ha="center", va="bottom",
                fontsize=VAL_SZ, fontweight="bold")
        if i > 0:
            ax.text(i, bot + val / 2, f"{val:+.4f}", ha="center", va="center",
                    fontsize=VAL_SZ - 1, color="white", fontweight="bold")

    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s[0] for s in steps], fontsize=TICK_SZ - 1)
    ax.set_ylabel("AUC", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: AUC Waterfall (Incremental Gains)",
                 fontsize=TITLE_SZ, fontweight="bold")
    ax.axhline(y=base, color="#64748B", ls="--", alpha=0.4)
    ax.set_ylim(0, gated_auc * 1.08)
    _save(fig, "A_comparison", "A05_waterfall.png")


# ═══════════════════════════════════════════════════════════════════════════
# B — Per-Category Analysis
# ═══════════════════════════════════════════════════════════════════════════


def _ucf_cat_order():
    return [
        "Abuse", "Arrest", "Arson", "Assault", "Burglary", "Explosion",
        "Fighting", "RoadAccidents", "Robbery", "Shooting", "Shoplifting",
        "Stealing", "Vandalism",
    ]


def chart_B06(data):
    cats = _ucf_cat_order()
    matrix = []
    for v in UCF_MAIN:
        run = UCF_RUNS[v]
        pc = data["metrics"][run]["per_category"]
        matrix.append([pc[c]["auc"] for c in cats])

    df = pd.DataFrame(matrix, index=[VLABELS[v] for v in UCF_MAIN], columns=cats)
    fig, ax = plt.subplots(figsize=FIG_WIDE)
    sns.heatmap(df, annot=True, fmt=".3f", cmap="RdYlGn", vmin=0.75, vmax=1.0,
                ax=ax, linewidths=0.5, cbar_kws={"label": "AUC"})
    ax.set_title("UCF-Crime: Per-Category AUC Heatmap", fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=TICK_SZ - 1)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=TICK_SZ)
    _save(fig, "B_per_category", "B06_heatmap_auc.png")


def chart_B07(data):
    cats = _ucf_cat_order()
    matrix = []
    for v in UCF_MAIN:
        run = UCF_RUNS[v]
        pc = data["metrics"][run]["per_category"]
        matrix.append([pc[c]["ap"] for c in cats])

    df = pd.DataFrame(matrix, index=[VLABELS[v] for v in UCF_MAIN], columns=cats)
    fig, ax = plt.subplots(figsize=FIG_WIDE)
    sns.heatmap(df, annot=True, fmt=".3f", cmap="RdYlGn", vmin=0, vmax=0.65,
                ax=ax, linewidths=0.5, cbar_kws={"label": "AP"})
    ax.set_title("UCF-Crime: Per-Category AP Heatmap", fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=TICK_SZ - 1)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=TICK_SZ)
    _save(fig, "B_per_category", "B07_heatmap_ap.png")


def chart_B08(data):
    cats = _ucf_cat_order()
    fig, ax = plt.subplots(figsize=(18, 8))
    x = np.arange(len(cats))
    w = 0.2
    for i, v in enumerate(UCF_MAIN):
        pc = data["metrics"][UCF_RUNS[v]]["per_category"]
        vals = [pc[c]["auc"] for c in cats]
        ax.bar(x + i * w - 1.5 * w, vals, w, label=VLABELS[v],
               color=VCOLORS[v], edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=45, ha="right", fontsize=TICK_SZ - 1)
    ax.set_ylabel("AUC", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: Per-Category AUC (All Variants)", fontsize=TITLE_SZ, fontweight="bold")
    ax.legend(fontsize=TICK_SZ)
    ax.set_ylim(0.7, 1.02)
    _save(fig, "B_per_category", "B08_grouped_bar_category_auc.png")


def chart_B09(data):
    cats = _ucf_cat_order()
    pc = data["metrics"]["ucf_gated_fusion_s42"]["per_category"]
    overall = data["metrics"]["ucf_gated_fusion_s42"]["auc"]
    devs = [(pc[c]["auc"] - overall) for c in cats]

    order = np.argsort(devs)
    fig, ax = plt.subplots(figsize=FIG_STD)
    colors = ["#22C55E" if d >= 0 else "#EF4444" for d in [devs[i] for i in order]]
    bars = ax.barh([cats[i] for i in order], [devs[i] for i in order],
                   color=colors, edgecolor="white", height=0.6)
    for b in bars:
        w = b.get_width()
        ax.text(w + (0.002 if w >= 0 else -0.002),
                b.get_y() + b.get_height() / 2,
                f"{w:+.4f}", ha="left" if w >= 0 else "right",
                va="center", fontsize=VAL_SZ, fontweight="bold")

    ax.axvline(x=0, color="black", lw=0.8)
    ax.set_xlabel(f"Deviation from Overall AUC ({overall:.4f})", fontsize=LABEL_SZ)
    ax.set_title("Gated Fusion: Per-Category AUC Deviation",
                 fontsize=TITLE_SZ, fontweight="bold")
    _save(fig, "B_per_category", "B09_diverging_bar_auc.png")


def chart_B10(data):
    cats = _ucf_cat_order()
    pc = data["metrics"]["ucf_gated_fusion_s42"]["per_category"]
    aps = [pc[c]["ap"] for c in cats]

    order = np.argsort(aps)[::-1]
    fig, ax = plt.subplots(figsize=FIG_STD)
    y_pos = range(len(cats))
    sorted_cats = [cats[i] for i in order]
    sorted_aps = [aps[i] for i in order]

    ax.hlines(y_pos, 0, sorted_aps, color="#3B82F6", lw=2)
    ax.scatter(sorted_aps, y_pos, color="#EF4444", s=80, zorder=5)
    for i, val in enumerate(sorted_aps):
        ax.text(val + 0.008, i, f"{val:.4f}", va="center", fontsize=VAL_SZ, fontweight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_cats, fontsize=TICK_SZ)
    ax.set_xlabel("Average Precision", fontsize=LABEL_SZ)
    ax.set_title("Gated Fusion: Per-Category AP (Lollipop)",
                 fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xlim(0, max(sorted_aps) * 1.15)
    ax.invert_yaxis()
    _save(fig, "B_per_category", "B10_lollipop_ap.png")


# ═══════════════════════════════════════════════════════════════════════════
# C — Training Dynamics
# ════════��══════════════════════════════════════════════════════════════════


def chart_C11(data):
    fig, ax = plt.subplots(figsize=FIG_STD)
    for v in UCF_MAIN:
        log = data["logs"][UCF_RUNS[v]]
        ax.plot(log["epoch"], log["val_loss"], "-o", label=VLABELS[v],
                color=VCOLORS[v], lw=2, ms=4, alpha=0.9)

    ax.set_xlabel("Epoch", fontsize=LABEL_SZ)
    ax.set_ylabel("Validation Loss", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: Validation Loss Curves", fontsize=TITLE_SZ, fontweight="bold")
    ax.legend(fontsize=TICK_SZ)
    _save(fig, "C_training", "C11_val_loss_overlay.png")


def chart_C12(data):
    fig, axes = plt.subplots(2, 5, figsize=(24, 10), sharey=False)
    axes = axes.flatten()
    for i, run in enumerate(ALL_RUNS):
        ax = axes[i]
        log = data["logs"][run]
        ax.plot(log["epoch"], log["train_loss"], "-", label="Train", color="#3B82F6", lw=1.5)
        ax.plot(log["epoch"], log["val_loss"], "-", label="Val", color="#EF4444", lw=1.5)
        ax.set_title(RUN_DISPLAY[run], fontsize=10, fontweight="bold")
        ax.tick_params(labelsize=8)
        if i == 0:
            ax.legend(fontsize=8)

    fig.suptitle("Training Dynamics: All Phase 4 Runs", fontsize=TITLE_SZ, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "C_training", "C12_loss_small_multiples.png")


# ═══════════════════════════════════════════════════════════════════════════
# D — Stability (3-Seed Gated Fusion)
# ═══════════════════════════════════════════════════════════════════════════


def chart_D13(data):
    aucs = [data["metrics"][r]["auc"] for r in SEED_RUNS]
    seeds = [42, 123, 2024]
    mean_auc = np.mean(aucs)
    std_auc = np.std(aucs)

    fig, ax = plt.subplots(figsize=FIG_SMALL)
    ax.errorbar(["Gated Fusion"], [mean_auc], yerr=[std_auc],
                fmt="s", ms=12, color="#EF4444", capsize=10, capthick=2, lw=2)
    for i, (s, a) in enumerate(zip(seeds, aucs)):
        ax.scatter(["Gated Fusion"], [a], s=60, zorder=5, alpha=0.7,
                   label=f"Seed {s}: {a:.4f}")

    ax.set_ylabel("AUC", fontsize=LABEL_SZ)
    ax.set_title(f"3-Seed Stability: AUC (mean={mean_auc:.4f}, std={std_auc:.4f})",
                 fontsize=TITLE_SZ - 2, fontweight="bold")
    ax.legend(fontsize=TICK_SZ)
    ax.set_ylim(mean_auc - 0.02, mean_auc + 0.02)
    _save(fig, "D_stability", "D13_errorbar_auc.png")


def chart_D14(data):
    aps = [data["metrics"][r]["ap"] for r in SEED_RUNS]
    seeds = [42, 123, 2024]
    mean_ap = np.mean(aps)
    std_ap = np.std(aps)

    fig, ax = plt.subplots(figsize=FIG_SMALL)
    ax.errorbar(["Gated Fusion"], [mean_ap], yerr=[std_ap],
                fmt="s", ms=12, color="#F59E0B", capsize=10, capthick=2, lw=2)
    for i, (s, a) in enumerate(zip(seeds, aps)):
        ax.scatter(["Gated Fusion"], [a], s=60, zorder=5, alpha=0.7,
                   label=f"Seed {s}: {a:.4f}")

    ax.set_ylabel("AP", fontsize=LABEL_SZ)
    ax.set_title(f"3-Seed Stability: AP (mean={mean_ap:.4f}, std={std_ap:.4f})",
                 fontsize=TITLE_SZ - 2, fontweight="bold")
    ax.legend(fontsize=TICK_SZ)
    ax.set_ylim(mean_ap - 0.02, mean_ap + 0.02)
    _save(fig, "D_stability", "D14_errorbar_ap.png")


def chart_D15(data):
    seeds = [42, 123, 2024]
    aucs = [data["metrics"][r]["auc"] for r in SEED_RUNS]
    aps = [data["metrics"][r]["ap"] for r in SEED_RUNS]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_STD)
    for s, a in zip(seeds, aucs):
        ax1.scatter([f"Seed {s}"], [a], s=120, zorder=5, color="#EF4444")
        ax1.text(0, a + 0.0005, f"{a:.4f}", ha="center", fontsize=VAL_SZ, fontweight="bold")
    ax1.axhline(np.mean(aucs), color="#64748B", ls="--", label=f"Mean: {np.mean(aucs):.4f}")
    ax1.set_ylabel("AUC", fontsize=LABEL_SZ)
    ax1.set_title("AUC by Seed", fontsize=LABEL_SZ, fontweight="bold")
    ax1.legend(fontsize=TICK_SZ - 1)
    ax1.set_ylim(min(aucs) - 0.005, max(aucs) + 0.005)

    for s, a in zip(seeds, aps):
        ax2.scatter([f"Seed {s}"], [a], s=120, zorder=5, color="#F59E0B")
        ax2.text(0, a + 0.0005, f"{a:.4f}", ha="center", fontsize=VAL_SZ, fontweight="bold")
    ax2.axhline(np.mean(aps), color="#64748B", ls="--", label=f"Mean: {np.mean(aps):.4f}")
    ax2.set_ylabel("AP", fontsize=LABEL_SZ)
    ax2.set_title("AP by Seed", fontsize=LABEL_SZ, fontweight="bold")
    ax2.legend(fontsize=TICK_SZ - 1)
    ax2.set_ylim(min(aps) - 0.005, max(aps) + 0.005)

    fig.suptitle("Gated Fusion: 3-Seed Stability", fontsize=TITLE_SZ, fontweight="bold")
    fig.tight_layout()
    _save(fig, "D_stability", "D15_strip_plot.png")


# ═══════════════════════════════════════════════════════════════════════════
# E — Pooling Ablation
# ═══════════════════════════════════════════════════════════════════════════


def chart_E16(data):
    base_auc = data["metrics"]["ucf_gated_fusion_s42"]["auc"]
    base_ap = data["metrics"]["ucf_gated_fusion_s42"]["ap"]

    ablations = {
        "2-Person\n(concat)": "ucf_gated_fusion_2person_s42",
        "CLIP Mean\n(mean only)": "ucf_gated_fusion_clip_mean_s42",
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_STD)
    for i, (lbl, run) in enumerate(ablations.items()):
        d_auc = data["metrics"][run]["auc"] - base_auc
        d_ap = data["metrics"][run]["ap"] - base_ap
        col_a = "#22C55E" if d_auc >= 0 else "#EF4444"
        col_p = "#22C55E" if d_ap >= 0 else "#EF4444"
        b1 = ax1.bar(i, d_auc, color=col_a, edgecolor="white", width=0.5)
        b2 = ax2.bar(i, d_ap, color=col_p, edgecolor="white", width=0.5)
        ax1.text(i, d_auc / 2, f"{d_auc:+.4f}", ha="center", va="center",
                 fontsize=VAL_SZ, fontweight="bold", color="white" if d_auc < 0 else "black")
        ax2.text(i, d_ap / 2, f"{d_ap:+.4f}", ha="center", va="center",
                 fontsize=VAL_SZ, fontweight="bold", color="white" if d_ap < 0 else "black")

    labels = list(ablations.keys())
    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, fontsize=TICK_SZ - 1)
    ax1.axhline(0, color="black", lw=0.8)
    ax1.set_ylabel("ΔAUC vs Baseline", fontsize=LABEL_SZ)
    ax1.set_title("AUC Delta", fontsize=LABEL_SZ, fontweight="bold")

    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, fontsize=TICK_SZ - 1)
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_ylabel("ΔAP vs Baseline", fontsize=LABEL_SZ)
    ax2.set_title("AP Delta", fontsize=LABEL_SZ, fontweight="bold")

    fig.suptitle("Pooling Ablation: Δ from Gated Fusion Baseline",
                 fontsize=TITLE_SZ, fontweight="bold")
    fig.tight_layout()
    _save(fig, "E_ablation", "E16_delta_bar.png")


def chart_E17(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_STD)
    base_m = data["metrics"]["ucf_gated_fusion_s42"]
    names = ["2-Person", "CLIP Mean"]
    runs = ["ucf_gated_fusion_2person_s42", "ucf_gated_fusion_clip_mean_s42"]

    for i, (n, r) in enumerate(zip(names, runs)):
        m = data["metrics"][r]
        ax1.plot([0, 1], [base_m["auc"], m["auc"]], "o-", lw=2, ms=8, label=n)
        ax1.text(-0.05, base_m["auc"], f'{base_m["auc"]:.4f}', ha="right", fontsize=VAL_SZ)
        ax1.text(1.05, m["auc"], f'{m["auc"]:.4f}', ha="left", fontsize=VAL_SZ)

        ax2.plot([0, 1], [base_m["ap"], m["ap"]], "o-", lw=2, ms=8, label=n)
        ax2.text(-0.05, base_m["ap"], f'{base_m["ap"]:.4f}', ha="right", fontsize=VAL_SZ)
        ax2.text(1.05, m["ap"], f'{m["ap"]:.4f}', ha="left", fontsize=VAL_SZ)

    for ax, metric in [(ax1, "AUC"), (ax2, "AP")]:
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Baseline", "Ablation"], fontsize=TICK_SZ)
        ax.set_ylabel(metric, fontsize=LABEL_SZ)
        ax.set_title(f"{metric} Change", fontsize=LABEL_SZ, fontweight="bold")
        ax.legend(fontsize=TICK_SZ - 1)
        ax.set_xlim(-0.3, 1.3)

    fig.suptitle("Pooling Ablation: Paired Comparison",
                 fontsize=TITLE_SZ, fontweight="bold")
    fig.tight_layout()
    _save(fig, "E_ablation", "E17_paired_dot.png")


# ═══════════════════════════════════════════════════════════════════════════
# F — XD-I3D Gate
# ���══════════════════════════════════════════════════════════════════════════


def chart_F18(data):
    fig, ax = plt.subplots(figsize=FIG_STD)
    variants = ["rtfm_i3d", "rtfm_i3d_flow"]
    labels = [XD_LABELS[v] for v in variants]
    aucs = [data["metrics"][XD_RUNS[v]]["auc"] for v in variants]
    aps = [data["metrics"][XD_RUNS[v]]["ap"] for v in variants]

    x = np.arange(len(variants))
    w = 0.35
    b1 = ax.bar(x - w / 2, aucs, w, label="AUC", color="#3B82F6", edgecolor="white")
    b2 = ax.bar(x + w / 2, aps, w, label="AP", color="#F59E0B", edgecolor="white")
    _bar_vals(ax, b1)
    _bar_vals(ax, b2)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=TICK_SZ)
    ax.set_ylabel("Score", fontsize=LABEL_SZ)
    ax.set_title("XD-Violence I3D: RGB vs RGB+Flow", fontsize=TITLE_SZ, fontweight="bold")
    ax.legend(fontsize=TICK_SZ)
    ax.set_ylim(0, max(max(aucs), max(aps)) * 1.18)
    _save(fig, "F_xd_i3d", "F18_grouped_bar_xd.png")


def chart_F19(data):
    cats_rgb = data["cats"]["xd_i3d_rtfm_i3d_s42"]
    cats_flow = data["cats"]["xd_i3d_rtfm_i3d_flow_s42"]
    cat_names = list(cats_rgb["category"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_WIDE)
    x = np.arange(len(cat_names))
    w = 0.35

    b1 = ax1.bar(x - w / 2, cats_rgb["auc"], w, label="RGB", color="#3B82F6")
    b2 = ax1.bar(x + w / 2, cats_flow["auc"], w, label="RGB+Flow", color="#10B981")
    ax1.set_xticks(x)
    ax1.set_xticklabels(cat_names, fontsize=TICK_SZ)
    ax1.set_ylabel("AUC", fontsize=LABEL_SZ)
    ax1.set_title("Per-Category AUC", fontsize=LABEL_SZ, fontweight="bold")
    ax1.legend(fontsize=TICK_SZ)
    ax1.set_ylim(0.7, 1.02)

    b3 = ax2.bar(x - w / 2, cats_rgb["ap"], w, label="RGB", color="#3B82F6")
    b4 = ax2.bar(x + w / 2, cats_flow["ap"], w, label="RGB+Flow", color="#10B981")
    ax2.set_xticks(x)
    ax2.set_xticklabels(cat_names, fontsize=TICK_SZ)
    ax2.set_ylabel("AP", fontsize=LABEL_SZ)
    ax2.set_title("Per-Category AP", fontsize=LABEL_SZ, fontweight="bold")
    ax2.legend(fontsize=TICK_SZ)

    fig.suptitle("XD-Violence I3D: Per-Category Comparison",
                 fontsize=TITLE_SZ, fontweight="bold")
    fig.tight_layout()
    _save(fig, "F_xd_i3d", "F19_category_bar_xd.png")


# ═══════════════════════════════════════════════════════════════════════════
# G — ROC & PR Curves
# ═══════════════════════════════════════════════════════════════════════════


def chart_G20(curves):
    fig, ax = plt.subplots(figsize=FIG_STD)
    for v in UCF_MAIN:
        run = UCF_RUNS[v]
        if run not in curves:
            continue
        c = curves[run]
        ax.plot(c["fpr"], c["tpr"], lw=2, color=VCOLORS[v],
                label=f'{VLABELS[v]} (AUC={c["auc"]:.4f})')

    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.3, label="Random")
    ax.set_xlabel("False Positive Rate", fontsize=LABEL_SZ)
    ax.set_ylabel("True Positive Rate", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: ROC Curves", fontsize=TITLE_SZ, fontweight="bold")
    ax.legend(fontsize=TICK_SZ, loc="lower right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    _save(fig, "G_curves", "G20_roc_ucf.png")


def chart_G21(curves):
    fig, ax = plt.subplots(figsize=FIG_STD)
    for v in UCF_MAIN:
        run = UCF_RUNS[v]
        if run not in curves:
            continue
        c = curves[run]
        ax.plot(c["rec"], c["prec"], lw=2, color=VCOLORS[v],
                label=f'{VLABELS[v]} (AP={c["ap"]:.4f})')

    ax.set_xlabel("Recall", fontsize=LABEL_SZ)
    ax.set_ylabel("Precision", fontsize=LABEL_SZ)
    ax.set_title("UCF-Crime: Precision-Recall Curves", fontsize=TITLE_SZ, fontweight="bold")
    ax.legend(fontsize=TICK_SZ, loc="upper right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    _save(fig, "G_curves", "G21_pr_ucf.png")


def chart_G22(curves):
    fig, ax = plt.subplots(figsize=FIG_STD)
    for v in ["rtfm_i3d", "rtfm_i3d_flow"]:
        run = XD_RUNS[v]
        if run not in curves:
            continue
        c = curves[run]
        ax.plot(c["fpr"], c["tpr"], lw=2, color=XD_COLORS[v],
                label=f'{XD_LABELS[v]} (AUC={c["auc"]:.4f})')

    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.3, label="Random")
    ax.set_xlabel("False Positive Rate", fontsize=LABEL_SZ)
    ax.set_ylabel("True Positive Rate", fontsize=LABEL_SZ)
    ax.set_title("XD-Violence: ROC Curves (I3D)", fontsize=TITLE_SZ, fontweight="bold")
    ax.legend(fontsize=TICK_SZ, loc="lower right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    _save(fig, "G_curves", "G22_roc_xd.png")


def chart_G23(curves):
    fig, ax = plt.subplots(figsize=FIG_STD)
    for v in ["rtfm_i3d", "rtfm_i3d_flow"]:
        run = XD_RUNS[v]
        if run not in curves:
            continue
        c = curves[run]
        ax.plot(c["rec"], c["prec"], lw=2, color=XD_COLORS[v],
                label=f'{XD_LABELS[v]} (AP={c["ap"]:.4f})')

    ax.set_xlabel("Recall", fontsize=LABEL_SZ)
    ax.set_ylabel("Precision", fontsize=LABEL_SZ)
    ax.set_title("XD-Violence: Precision-Recall Curves (I3D)",
                 fontsize=TITLE_SZ, fontweight="bold")
    ax.legend(fontsize=TICK_SZ, loc="upper right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    _save(fig, "G_curves", "G23_pr_xd.png")


# ═══════════════════════════════════════════════════════════════════════════
# H — Confusion Matrix
# ═══════════════════════════════════════════════════════════════════════════


def chart_H24(curves):
    fig, axes = plt.subplots(2, 2, figsize=FIG_WIDE)
    axes = axes.flatten()

    for i, v in enumerate(UCF_MAIN):
        run = UCF_RUNS[v]
        if run not in curves:
            continue
        c = curves[run]
        th = _optimal_threshold(c["fpr"], c["tpr"], c["roc_th"])
        preds = (c["v_max"] >= th).astype(int)
        cm = sk_confusion_matrix(c["v_lbl"], preds)

        ax = axes[i]
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["Normal", "Anomaly"],
                    yticklabels=["Normal", "Anomaly"],
                    cbar=False, linewidths=0.5)
        ax.set_xlabel("Predicted", fontsize=TICK_SZ)
        ax.set_ylabel("Actual", fontsize=TICK_SZ)
        ax.set_title(f"{VLABELS[v]} (th={th:.3f})", fontsize=TICK_SZ, fontweight="bold")

    fig.suptitle("UCF-Crime: Video-Level Confusion Matrix (Youden's J Threshold)",
                 fontsize=TITLE_SZ - 1, fontweight="bold")
    fig.tight_layout()
    _save(fig, "H_confusion", "H24_confusion_video.png")


def chart_H25(curves):
    fig, axes = plt.subplots(2, 2, figsize=FIG_WIDE)
    axes = axes.flatten()

    for i, v in enumerate(UCF_MAIN):
        run = UCF_RUNS[v]
        if run not in curves:
            continue
        c = curves[run]
        th = _optimal_threshold(c["fpr"], c["tpr"], c["roc_th"])
        preds = (c["y_score"] >= th).astype(int)
        cm = sk_confusion_matrix(c["y_true"], preds)
        cm_pct = cm / cm.sum() * 100

        ax = axes[i]
        labels = [[f"{cm[r][cl]:,}\n({cm_pct[r][cl]:.1f}%)" for cl in range(2)] for r in range(2)]
        sns.heatmap(cm_pct, annot=labels, fmt="", cmap="Blues", ax=ax,
                    xticklabels=["Normal", "Anomaly"],
                    yticklabels=["Normal", "Anomaly"],
                    cbar=False, linewidths=0.5, vmin=0, vmax=100)
        ax.set_xlabel("Predicted", fontsize=TICK_SZ)
        ax.set_ylabel("Actual", fontsize=TICK_SZ)
        ax.set_title(f"{VLABELS[v]} (th={th:.3f})", fontsize=TICK_SZ, fontweight="bold")

    fig.suptitle("UCF-Crime: Frame-Level Confusion Matrix (Youden's J Threshold)",
                 fontsize=TITLE_SZ - 1, fontweight="bold")
    fig.tight_layout()
    _save(fig, "H_confusion", "H25_confusion_frame.png")


# ═══════════════════════════════════════════════════════════════════════════
# I — Per-Run Standard Set
# ═══════════════════════════════════════════════════════════════════════════


def charts_per_run(data, curves):
    for run in ALL_RUNS:
        subdir = f"I_per_run/{run}"
        display = RUN_DISPLAY[run]

        # I-1: Loss curve
        log = data["logs"][run]
        fig, ax = plt.subplots(figsize=FIG_SMALL)
        ax.plot(log["epoch"], log["train_loss"], "-o", label="Train", color="#3B82F6", lw=2, ms=3)
        ax.plot(log["epoch"], log["val_loss"], "-o", label="Val", color="#EF4444", lw=2, ms=3)
        ax.set_xlabel("Epoch", fontsize=LABEL_SZ)
        ax.set_ylabel("Loss", fontsize=LABEL_SZ)
        ax.set_title(f"{display}: Training Loss", fontsize=TITLE_SZ - 2, fontweight="bold")
        ax.legend(fontsize=TICK_SZ)
        _save(fig, subdir, "loss_curve.png")

        # I-2: Per-category AUC bar
        cat_df = data["cats"][run]
        fig, ax = plt.subplots(figsize=FIG_STD)
        bars = ax.barh(cat_df["category"], cat_df["auc"], color="#3B82F6",
                       edgecolor="white", height=0.6)
        _hbar_vals(ax, bars, fmt=".3f")
        overall_auc = data["metrics"][run]["auc"]
        ax.axvline(overall_auc, color="#EF4444", ls="--", lw=1.5,
                   label=f"Overall: {overall_auc:.4f}")
        ax.set_xlabel("AUC", fontsize=LABEL_SZ)
        ax.set_title(f"{display}: Per-Category AUC", fontsize=TITLE_SZ - 2, fontweight="bold")
        ax.legend(fontsize=TICK_SZ)
        ax.invert_yaxis()
        _save(fig, subdir, "category_auc.png")

        # I-3: Per-category AP bar
        fig, ax = plt.subplots(figsize=FIG_STD)
        bars = ax.barh(cat_df["category"], cat_df["ap"], color="#F59E0B",
                       edgecolor="white", height=0.6)
        _hbar_vals(ax, bars, fmt=".3f")
        overall_ap = data["metrics"][run]["ap"]
        ax.axvline(overall_ap, color="#EF4444", ls="--", lw=1.5,
                   label=f"Overall: {overall_ap:.4f}")
        ax.set_xlabel("AP", fontsize=LABEL_SZ)
        ax.set_title(f"{display}: Per-Category AP", fontsize=TITLE_SZ - 2, fontweight="bold")
        ax.legend(fontsize=TICK_SZ)
        ax.invert_yaxis()
        _save(fig, subdir, "category_ap.png")

        # I-4: ROC curve
        if run in curves:
            c = curves[run]
            fig, ax = plt.subplots(figsize=FIG_SMALL)
            ax.plot(c["fpr"], c["tpr"], lw=2, color="#3B82F6",
                    label=f'AUC = {c["auc"]:.4f}')
            ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.3)
            th = _optimal_threshold(c["fpr"], c["tpr"], c["roc_th"])
            idx = np.argmin(np.abs(c["roc_th"] - th))
            ax.scatter([c["fpr"][idx]], [c["tpr"][idx]], color="#EF4444", s=80, zorder=5,
                       label=f"Optimal th={th:.3f}")
            ax.set_xlabel("FPR", fontsize=LABEL_SZ)
            ax.set_ylabel("TPR", fontsize=LABEL_SZ)
            ax.set_title(f"{display}: ROC Curve", fontsize=TITLE_SZ - 2, fontweight="bold")
            ax.legend(fontsize=TICK_SZ, loc="lower right")
            _save(fig, subdir, "roc_curve.png")

            # I-5: PR curve
            fig, ax = plt.subplots(figsize=FIG_SMALL)
            ax.plot(c["rec"], c["prec"], lw=2, color="#F59E0B",
                    label=f'AP = {c["ap"]:.4f}')
            ax.set_xlabel("Recall", fontsize=LABEL_SZ)
            ax.set_ylabel("Precision", fontsize=LABEL_SZ)
            ax.set_title(f"{display}: Precision-Recall Curve",
                         fontsize=TITLE_SZ - 2, fontweight="bold")
            ax.legend(fontsize=TICK_SZ, loc="upper right")
            _save(fig, subdir, "pr_curve.png")


# ═══════════════════════════════════════════════════════════════════════════
# J — Summary
# ���══════════════════════════════════════════════════════════════════════════


def chart_J26(data):
    rows = []
    for run in ALL_RUNS:
        m = data["metrics"][run]
        rows.append([
            RUN_DISPLAY[run],
            f'{m["auc"]:.4f}',
            f'{m["ap"]:.4f}',
            f'{m.get("snippet_auc", 0):.4f}',
            f'{m.get("video_auc", 0):.4f}',
            str(m["n_videos"]),
            f'{m["n_frames"]:,}',
        ])

    fig, ax = plt.subplots(figsize=(18, 6))
    ax.axis("off")
    cols = ["Run", "AUC", "AP", "Snip AUC", "Vid AUC", "Videos", "Frames"]
    table = ax.table(cellText=rows, colLabels=cols, loc="center",
                     cellLoc="center", colWidths=[0.22, 0.1, 0.1, 0.1, 0.1, 0.08, 0.14])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.6)

    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#3B82F6")
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#F1F5F9")
        cell.set_edgecolor("#CBD5E1")

    ax.set_title("Phase 4: Complete Results Summary", fontsize=TITLE_SZ,
                 fontweight="bold", pad=20)
    _save(fig, "J_summary", "J26_summary_table.png")


def chart_J27(data, curves):
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)

    # Top-left: AUC bar
    ax1 = fig.add_subplot(gs[0, 0])
    labels = [VLABELS[v] for v in UCF_MAIN]
    aucs = [data["metrics"][UCF_RUNS[v]]["auc"] for v in UCF_MAIN]
    bars = ax1.bar(labels, aucs, color=[VCOLORS[v] for v in UCF_MAIN], edgecolor="white")
    _bar_vals(ax1, bars)
    ax1.set_ylabel("AUC")
    ax1.set_title("Frame-Level AUC", fontweight="bold")
    ax1.set_ylim(0.65, max(aucs) * 1.12)

    # Top-right: ROC overlay
    ax2 = fig.add_subplot(gs[0, 1])
    for v in UCF_MAIN:
        run = UCF_RUNS[v]
        if run in curves:
            c = curves[run]
            ax2.plot(c["fpr"], c["tpr"], lw=2, color=VCOLORS[v],
                     label=f'{VLABELS[v]} ({c["auc"]:.3f})')
    ax2.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.3)
    ax2.set_xlabel("FPR")
    ax2.set_ylabel("TPR")
    ax2.set_title("ROC Curves", fontweight="bold")
    ax2.legend(fontsize=9, loc="lower right")

    # Bottom-left: Per-category heatmap (gated only)
    ax3 = fig.add_subplot(gs[1, 0])
    cat_order = _ucf_cat_order()
    pc = data["metrics"]["ucf_gated_fusion_s42"]["per_category"]
    cat_aucs = [pc[c]["auc"] for c in cat_order]
    ax3.barh(cat_order, cat_aucs, color="#EF4444", edgecolor="white", height=0.6)
    ax3.set_xlabel("AUC")
    ax3.set_title("Gated Fusion: Per-Category AUC", fontweight="bold")
    ax3.invert_yaxis()
    ax3.set_xlim(0.8, 1.0)

    # Bottom-right: 3-seed stability
    ax4 = fig.add_subplot(gs[1, 1])
    seeds = [42, 123, 2024]
    s_aucs = [data["metrics"][r]["auc"] for r in SEED_RUNS]
    s_aps = [data["metrics"][r]["ap"] for r in SEED_RUNS]
    x = np.arange(3)
    w = 0.35
    ax4.bar(x - w / 2, s_aucs, w, label="AUC", color="#3B82F6")
    ax4.bar(x + w / 2, s_aps, w, label="AP", color="#F59E0B")
    ax4.set_xticks(x)
    ax4.set_xticklabels([f"Seed {s}" for s in seeds])
    ax4.set_title("3-Seed Stability", fontweight="bold")
    ax4.legend(fontsize=9)

    fig.suptitle("Phase 4 Results Dashboard", fontsize=20, fontweight="bold")
    _save(fig, "J_summary", "J27_dashboard.png")


# ═══════════════════════════════════════════════════════════════════════════
# Verification
# ═══════════════════════════════════════════════════════════════════════════


def verify(data, curves):
    print("\n" + "=" * 70)
    print("VERIFICATION: Source values vs computed values")
    print("=" * 70)

    for run in ALL_RUNS:
        m = data["metrics"][run]
        stored_auc = m["auc"]
        stored_ap = m["ap"]

        if run in curves:
            comp_auc = curves[run]["auc"]
            comp_ap = curves[run]["ap"]
            auc_match = abs(stored_auc - comp_auc) < 1e-8
            ap_match = abs(stored_ap - comp_ap) < 1e-8
            status = "OK" if (auc_match and ap_match) else "MISMATCH"
            print(f"  {RUN_DISPLAY[run]:35s}  "
                  f"AUC: {stored_auc:.10f} vs {comp_auc:.10f} {'OK' if auc_match else 'FAIL'}  "
                  f"AP: {stored_ap:.10f} vs {comp_ap:.10f} {'OK' if ap_match else 'FAIL'}  "
                  f"[{status}]")
        else:
            print(f"  {RUN_DISPLAY[run]:35s}  (no curve data)")

    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════


def main():
    print("Phase 4 Results Visualization")
    print("=" * 50)
    print(f"Output: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Loading results data...")
    data = load_all_data()

    print("\n[2/4] Loading curve data (eval_scores.npz + label reconstruction)...")
    curves = load_curves()

    print("\n[3/4] Generating charts...")

    print("  Section A: Cross-Variant Comparison")
    chart_A01(data)
    chart_A02(data)
    chart_A03(data)
    chart_A04(data)
    chart_A05(data)

    print("  Section B: Per-Category Analysis")
    chart_B06(data)
    chart_B07(data)
    chart_B08(data)
    chart_B09(data)
    chart_B10(data)

    print("  Section C: Training Dynamics")
    chart_C11(data)
    chart_C12(data)

    print("  Section D: Stability (3-Seed)")
    chart_D13(data)
    chart_D14(data)
    chart_D15(data)

    print("  Section E: Pooling Ablation")
    chart_E16(data)
    chart_E17(data)

    print("  Section F: XD-I3D Gate")
    chart_F18(data)
    chart_F19(data)

    print("  Section G: ROC & PR Curves")
    chart_G20(curves)
    chart_G21(curves)
    chart_G22(curves)
    chart_G23(curves)

    print("  Section H: Confusion Matrix")
    chart_H24(curves)
    chart_H25(curves)

    print("  Section I: Per-Run Standard Set")
    charts_per_run(data, curves)

    print("  Section J: Summary")
    chart_J26(data)
    chart_J27(data, curves)

    print("\n[4/4] Verification...")
    verify(data, curves)

    # Count generated files
    pngs = list(OUT_DIR.rglob("*.png"))
    print(f"\nDone! Generated {len(pngs)} PNG files in {OUT_DIR}")


if __name__ == "__main__":
    main()
