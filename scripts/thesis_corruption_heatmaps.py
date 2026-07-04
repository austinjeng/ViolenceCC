#!/usr/bin/env python
"""Thesis figures: corrupted-AUC heatmaps (source-only + disc_reweight), 3-seed.

Replaces the FORBIDDEN pre-fix phase-6 corruption heatmap series (which was
built from pre-dropout-fix episodic TTA data) with post-fix continual-protocol
data. Emits two 20-condition x 4-backbone absolute corrupted-AUC maps:

  thesis/figures/fig_corruption_source.pdf
      -> source-only corrupted AUC per condition x backbone (degradation map)
  thesis/figures/fig_corruption_disc_reweight.pdf
      -> disc_reweight corrupted AUC per condition x backbone

All values are TRUE 3-SEED means (seeds 42/123/2024), AUC points 0-100.

CPU-only. numpy / json / matplotlib only. NO torch / CUDA. Deterministic
(no stochastic path; RNG seeded 12345 for policy compliance).

Data sources (read-only, ALL git-tracked):
  results/_coral_derisk/r1full_{clip,base,so400m,giant}.json
      -> SEED-42 CANONICAL per-condition source (src) and disc_reweight (r1)
         corrupted AUCs (per_condition[<fam>_<sev>].{src,r1}, points 0-100).
  results/_coral_derisk/variants/v_{bb}_s{123,2024}_test.json
      -> per-seed src/r1 per-condition AUCs for seeds 123/2024.
         3-seed mean = mean over {r1full (s42), s123_test, s2024_test}
         (the canonical aggregation used by scripts/pri5_tta_breakdown.py).
  results/_tta_rerun_continual/summary_3seed.json
      -> TENT/SAR/source 3-seed per-backbone 20-condition means; used to
         cross-assert the recomputed source-only means (stale data fails
         loudly) and printed as TENT/SAR context.
"""
import json
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- determinism (policy: seed every RNG with a fixed int) -------------------
_RNG = np.random.default_rng(12345)  # not used in any stochastic path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERISK_DIR = os.path.join(ROOT, "results", "_coral_derisk")
SUMMARY_3SEED = os.path.join(
    ROOT, "results", "_tta_rerun_continual", "summary_3seed.json")
OUT_DIR = os.path.join(ROOT, "thesis", "figures")
os.makedirs(OUT_DIR, exist_ok=True)

PUB_DPI = 300

BACKBONES = [
    ("clip", "clip-vit-b-16", "CLIP ViT-B/16"),
    ("base", "siglip2-base", "SigLIP2-base"),
    ("so400m", "siglip2-so400m", "SigLIP2-SO400M"),
    ("giant", "siglip2-giant", "SigLIP2-giant"),
]
FAMILIES = ["gaussian_noise", "jpeg_compression", "brightness", "motion_blur"]
FAM_DISP = {
    "gaussian_noise": "Gaussian noise",
    "jpeg_compression": "JPEG compression",
    "brightness": "Brightness",
    "motion_blur": "Motion blur",
}
SEVERITIES = [1, 2, 3, 4, 5]
SEEDS = ("42", "123", "2024")

# Expected 3-seed source-only per-backbone 20-condition means (paper tab:tta /
# summary_3seed.json): CLIP/Base/SO400M/Giant. Stale data fails these asserts.
EXPECTED_SRC_MEANS = {"clip": 63.71, "base": 57.01, "so400m": 58.87, "giant": 62.83}
# Expected 3-seed disc_reweight mean gains (paper tab:tta): +0.67/+1.50/+2.24/+0.42
EXPECTED_R1_DELTAS = {"clip": 0.67, "base": 1.50, "so400m": 2.24, "giant": 0.42}

# s42 -> r1full (CANONICAL); s123/s2024 -> variants test ref (pri5 aggregation)
SEED_FILES = {
    bb: {
        "42": f"r1full_{bb}.json",
        "123": f"variants/v_{bb}_s123_test.json",
        "2024": f"variants/v_{bb}_s2024_test.json",
    }
    for bb, _, _ in BACKBONES
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


def _render(mat, conds, title, cbar_label, out_pdf, vmin, vmax):
    fig, ax = plt.subplots(figsize=(6.3, 7.4))
    im = ax.imshow(mat, cmap="viridis", vmin=vmin, vmax=vmax, aspect="auto")

    ax.set_xticks(range(len(BACKBONES)))
    ax.set_xticklabels([disp for _, _, disp in BACKBONES])
    ax.set_yticks(range(len(conds)))
    ax.set_yticklabels(
        [f"{FAM_DISP[fam]} (sev. {sev})"
         for fam in FAMILIES for sev in SEVERITIES])

    mid = vmin + 0.5 * (vmax - vmin)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            color = "white" if v < mid else "black"
            ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                    fontsize=7, color=color)

    for k in range(1, len(FAMILIES)):
        ax.axhline(k * len(SEVERITIES) - 0.5, color="white", linewidth=0.8)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label(cbar_label)
    ax.set_title(title)

    fig.tight_layout()
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"[thesis_corruption_heatmaps] wrote {out_pdf}")


def main():
    conds = [f"{fam}_{sev}" for fam in FAMILIES for sev in SEVERITIES]

    data = {bb: {sd: _load(fn) for sd, fn in SEED_FILES[bb].items()}
            for bb, _, _ in BACKBONES}

    # ---- 3-seed per-condition matrices (20 x 4), AUC points 0-100 ------------
    src_mat = np.zeros((len(conds), len(BACKBONES)))
    r1_mat = np.zeros((len(conds), len(BACKBONES)))
    for j, (bb, _, _) in enumerate(BACKBONES):
        for i, cond in enumerate(conds):
            src_mat[i, j] = float(np.mean(
                [data[bb][sd]["per_condition"][cond]["src"] for sd in SEEDS]))
            r1_mat[i, j] = float(np.mean(
                [data[bb][sd]["per_condition"][cond]["r1"] for sd in SEEDS]))

    # ---- self-check 1: source-only 20-condition means vs expected anchors ----
    with open(SUMMARY_3SEED, "r", encoding="utf-8") as f:
        s3 = json.load(f)
    for j, (bb, bb_full, _) in enumerate(BACKBONES):
        src_mean = float(np.mean(src_mat[:, j]))
        exp = EXPECTED_SRC_MEANS[bb]
        assert abs(src_mean - exp) <= 0.05, (
            f"source-only mean for {bb} recompute {src_mean:.4f} != {exp} "
            "(stale data?)")
        # cross-assert vs the tracked TENT/SAR summary's source means
        s3_src = float(s3[bb_full]["mean"]["source"])
        assert abs(src_mean - s3_src) <= 0.01, (
            f"source-only mean for {bb} {src_mean:.4f} != "
            f"summary_3seed.json {s3_src:.4f}")

    # ---- self-check 2: disc_reweight mean gains vs paper anchors -------------
    for j, (bb, _, _) in enumerate(BACKBONES):
        delta = float(np.mean(r1_mat[:, j]) - np.mean(src_mat[:, j]))
        exp = EXPECTED_R1_DELTAS[bb]
        assert abs(delta - exp) <= 0.05, (
            f"disc_reweight mean gain for {bb} recompute {delta:+.4f} != "
            f"{exp:+.2f} (stale data?)")

    print("[thesis_corruption_heatmaps] self-checks PASS "
          "(source means 63.71/57.01/58.87/62.83 within 0.05; "
          "disc_reweight gains +0.67/+1.50/+2.24/+0.42 within 0.05)")
    for bb, bb_full, _ in BACKBONES:
        m = s3[bb_full]["mean"]
        print(f"  [context] {bb_full}: TENT {m['tent']:.2f} / SAR {m['sar']:.2f} "
              f"(dTENT {m['dTENT']:+.3f}, dSAR {m['dSAR']:+.3f}) -- near-zero, "
              "per the LN-barrier finding")

    # ---- render (shared color scale across both figures) ---------------------
    _setup_style()
    vmin = float(min(src_mat.min(), r1_mat.min()))
    vmax = float(max(src_mat.max(), r1_mat.max()))
    _render(
        src_mat, conds,
        "Source-only corrupted AUC on UCF-Crime-C\n"
        "(3-seed mean, points; no adaptation)",
        "Corrupted AUC (points), 3-seed, source-only",
        os.path.join(OUT_DIR, "fig_corruption_source.pdf"), vmin, vmax)
    _render(
        r1_mat, conds,
        "disc_reweight corrupted AUC on UCF-Crime-C\n"
        "(3-seed mean, points)",
        "Corrupted AUC (points), 3-seed, disc_reweight",
        os.path.join(OUT_DIR, "fig_corruption_disc_reweight.pdf"), vmin, vmax)


if __name__ == "__main__":
    main()
