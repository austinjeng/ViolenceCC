#!/usr/bin/env python
"""Thesis figure: 20-condition x 4-backbone disc_reweight delta-AUC severity heatmap.

Renders thesis/figures/fig_severity_heatmap.pdf -- the per-condition (family x
severity) disc-reweight gain map for Ch 6. Values are TRUE 3-SEED means (seeds
42/123/2024), matching the thesis anchor "+13.2 in the single most-degraded
condition" (SO400M gaussian_noise_5). This figure shows PER-CONDITION values
only; do not confuse with the family/aggregate numbers +4.83 (3-seed Gaussian
family cross-backbone avg), +3.31 (s42-only Gaussian mean), or +8.95 (SO400M
Gaussian family mean).

CPU-only. numpy / json / csv / matplotlib only. NO torch / CUDA. Deterministic
(no stochastic path; RNG seeded 12345 for policy compliance).

Data sources (read-only, ALL git-tracked):
  results/_coral_derisk/r1full_{clip,base,so400m,giant}.json
      -> SEED-42 CANONICAL per-condition disc-reweight deltas
         (per_condition[<fam>_<sev>].d = r1 - src, AUC points 0-100).
  results/_coral_derisk/variants/v_{bb}_s{123,2024}_test.json
      -> per-seed disc-reweight per-condition deltas for seeds 123/2024.
         3-seed mean = mean over {r1full (s42), s123_test, s2024_test}
         (the canonical aggregation used by scripts/pri5_tta_breakdown.py).
  results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv
      -> cross-check ONLY: its 20 per-condition rows are the s42 canonical
         values (asserted equal to the r1full components) and its
         mean(3seed) family rows are asserted equal to the recomputed
         3-seed family means. NOT plotted directly (its per-condition block
         is s42-only; plotting it would reintroduce the stale s42-only
         +13.9 that the review replaced with the honest 3-seed +13.2).
"""
import csv
import json
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# ---- determinism (policy: seed every RNG with a fixed int) -------------------
_RNG = np.random.default_rng(12345)  # not used in any stochastic path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERISK_DIR = os.path.join(ROOT, "results", "_coral_derisk")
HEATMAP_CSV = os.path.join(
    ROOT, "results", "_analysis_2026-06-10", "pri5_per_condition_heatmap.csv")
OUT_DIR = os.path.join(ROOT, "thesis", "figures")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PDF = os.path.join(OUT_DIR, "fig_severity_heatmap.pdf")

PUB_DPI = 300

BACKBONES = [
    ("clip", "CLIP ViT-B/16"),
    ("base", "SigLIP2-base"),
    ("so400m", "SigLIP2-SO400M"),
    ("giant", "SigLIP2-giant"),
]
# Row order per plan: gaussian_noise, jpeg_compression, brightness, motion_blur
FAMILIES = ["gaussian_noise", "jpeg_compression", "brightness", "motion_blur"]
FAM_DISP = {
    "gaussian_noise": "Gaussian noise",
    "jpeg_compression": "JPEG compression",
    "brightness": "Brightness",
    "motion_blur": "Motion blur",
}
SEVERITIES = [1, 2, 3, 4, 5]
SEEDS = ("42", "123", "2024")

# s42 -> r1full (CANONICAL); s123/s2024 -> variants test ref (pri5 aggregation)
SEED_FILES = {
    bb: {
        "42": f"r1full_{bb}.json",
        "123": f"variants/v_{bb}_s123_test.json",
        "2024": f"variants/v_{bb}_s2024_test.json",
    }
    for bb, _ in BACKBONES
}


def _load(rel):
    with open(os.path.join(DERISK_DIR, rel), "r", encoding="utf-8") as f:
        return json.load(f)


def _setup_style():
    """Publication style (matches scripts/generate_pub_figures.py)."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "figure.dpi": PUB_DPI,
        "savefig.dpi": PUB_DPI,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "pdf.fonttype": 42,      # TrueType fonts in PDF
        "ps.fonttype": 42,
    })


def main():
    conds = [f"{fam}_{sev}" for fam in FAMILIES for sev in SEVERITIES]

    data = {bb: {sd: _load(fn) for sd, fn in SEED_FILES[bb].items()}
            for bb, _ in BACKBONES}

    # ---- 3-seed per-condition delta matrix (20 x 4) --------------------------
    mat = np.zeros((len(conds), len(BACKBONES)))
    for j, (bb, _) in enumerate(BACKBONES):
        for i, cond in enumerate(conds):
            per_seed = [data[bb][sd]["per_condition"][cond]["d"] for sd in SEEDS]
            mat[i, j] = float(np.mean(per_seed))

    # ---- self-check 1: SO400M gaussian_5 3-seed == the +13.2 anchor ----------
    so_g5 = mat[conds.index("gaussian_noise_5"), 2]
    assert abs(so_g5 - 13.2) <= 0.05, (
        f"SO400M gaussian_noise_5 3-seed recompute {so_g5:+.4f} != +13.2 anchor")

    # ---- self-check 2: cross-backbone Gaussian family 3-seed avg == +4.826 ---
    fam3 = {}
    for j, (bb, _) in enumerate(BACKBONES):
        per_seed_fam = [
            float(np.mean([data[bb][sd]["per_condition"][f"gaussian_noise_{s}"]["d"]
                           for s in SEVERITIES]))
            for sd in SEEDS
        ]
        fam3[bb] = float(np.mean(per_seed_fam))
    xbb = float(np.mean(list(fam3.values())))
    assert abs(xbb - 4.826) <= 0.01, (
        f"Gaussian cross-backbone 3-seed avg recompute {xbb:+.4f} != +4.826")

    # ---- cross-check vs tracked pri5_per_condition_heatmap.csv ---------------
    # (a) its 20 per-condition rows are the s42 canonical values;
    # (b) its mean(3seed) family rows match the recomputed 3-seed family means.
    with open(HEATMAP_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    col_of = {disp: header.index(disp) for _, disp in BACKBONES}
    csv_rows = {r[2]: r for r in rows[1:]}
    for cond in conds:
        r = csv_rows[cond]
        for (bb, disp) in BACKBONES:
            csv_val = float(r[col_of[disp]])
            s42_val = data[bb]["42"]["per_condition"][cond]["d"]
            assert abs(csv_val - s42_val) <= 1e-3, (
                f"CSV s42 cross-check failed at {cond}/{bb}: "
                f"{csv_val} vs {s42_val}")
    for fam in FAMILIES:
        r = csv_rows[f"{fam}_mean_3seed"]
        for (bb, disp) in BACKBONES:
            csv_val = float(r[col_of[disp]])
            rec = float(np.mean([
                float(np.mean([data[bb][sd]["per_condition"][f"{fam}_{s}"]["d"]
                               for s in SEVERITIES]))
                for sd in SEEDS
            ]))
            assert abs(csv_val - rec) <= 1e-3, (
                f"CSV mean(3seed) cross-check failed at {fam}/{bb}: "
                f"{csv_val} vs {rec}")

    print("[thesis_severity_heatmap] self-checks PASS "
          f"(SO400M gn_5 3-seed {so_g5:+.2f}; Gaussian xbb 3-seed avg {xbb:+.2f}; "
          "CSV s42 + mean(3seed) cross-checks OK)")

    # ---- render ---------------------------------------------------------------
    _setup_style()
    fig, ax = plt.subplots(figsize=(6.3, 7.4))
    vmax = float(np.max(np.abs(mat)))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    im = ax.imshow(mat, cmap="RdBu_r", norm=norm, aspect="auto")

    ax.set_xticks(range(len(BACKBONES)))
    ax.set_xticklabels([disp for _, disp in BACKBONES])
    ax.set_yticks(range(len(conds)))
    ax.set_yticklabels(
        [f"{FAM_DISP[fam]} (sev. {sev})"
         for fam in FAMILIES for sev in SEVERITIES])

    # annotate cells to 1 decimal (per-condition values only)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            color = "white" if abs(v) > 0.6 * vmax else "black"
            ax.text(j, i, f"{v:+.1f}", ha="center", va="center",
                    fontsize=7, color=color)

    # family separators
    for k in range(1, len(FAMILIES)):
        ax.axhline(k * len(SEVERITIES) - 0.5, color="black", linewidth=0.8)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("disc_reweight $\\Delta$AUC (points), 3-seed")
    ax.set_title("Per-condition disc_reweight gain on UCF-Crime-C\n"
                 "(3-seed mean $\\Delta$AUC, points; 4 families $\\times$ 5 severities)")

    fig.tight_layout()
    fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"[thesis_severity_heatmap] wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
