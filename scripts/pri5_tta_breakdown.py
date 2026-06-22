#!/usr/bin/env python
"""Pri 5: per-corruption-type disc-reweight breakdown table + heatmap.

Substantiates the paper prose numbers that "currently live nowhere checkable":
  - Gaussian-family cross-backbone average  ~ +4.8  (REVIEW: +4.826)
  - SO400M gaussian PEAK 3-seed             ~ +13.2 (REVIEW: 3-seed gaussian_5)
  - Base single-seed over-route             ~ -3.2  (REVIEW: s42 gaussian_5 = -3.202)

CPU-only. numpy / json / csv only. NO torch / CUDA. Fixed RNG seed (unused here,
deterministic by construction, but seeded for policy compliance).

Data sources (read-only):
  results/_coral_derisk/r1full_{clip,base,so400m,giant}.json
      -> SEED-42 CANONICAL per-condition disc-reweight (R1) deltas (20 conditions each).
         d = r1 - src, AUC points on 0-100 scale.
  results/_coral_derisk/variants/v_{bb}_s{seed}_*.json
      -> per-seed disc-reweight (R1) per-condition (s42 train ref + s123/s2024 test ref).
         Used for the 3-seed means (the canonical aggregation the REVIEW uses:
         r1full = the s42 component; variants supply s123/s2024).
  results/_tta_rerun_continual/summary_3seed.json
      -> 3-seed TENT/SAR OVERALL-AUC deltas (entropy minimisation; NOT disc-reweight,
         NOT per-family). Reported here only for the overall +1.21 disc-reweight
         context; it does NOT contain the +13.2 gaussian value (that comes from
         the per-seed disc-reweight variants).
"""
import json
import csv
import os
import numpy as np

# ---- determinism (policy: seed every RNG with a fixed int) -------------------
_RNG = np.random.default_rng(12345)  # not used in any stochastic path; here for compliance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERISK_DIR = os.path.join(ROOT, "results", "_coral_derisk")
VAR = os.path.join(DERISK_DIR, "variants")
OUT = os.path.join(ROOT, "results", "_analysis_2026-06-10")
os.makedirs(OUT, exist_ok=True)

# backbone short -> (display name, r1full file)
BACKBONES = [
    ("clip", "CLIP ViT-B/16", "r1full_clip.json"),
    ("base", "SigLIP2-base", "r1full_base.json"),
    ("so400m", "SigLIP2-SO400M", "r1full_so400m.json"),
    ("giant", "SigLIP2-giant", "r1full_giant.json"),
]
FAMILIES = ["gaussian_noise", "motion_blur", "jpeg_compression", "brightness"]
FAM_DISP = {
    "gaussian_noise": "Gaussian noise",
    "motion_blur": "Motion blur",
    "jpeg_compression": "JPEG compression",
    "brightness": "Brightness",
}
SEVERITIES = [1, 2, 3, 4, 5]

# per-seed variant files: s42 -> r1full (CANONICAL), s123/s2024 -> variants test ref
SEED_FILES = {
    "clip":   {"42": "r1full_clip.json",   "123": "variants/v_clip_s123_test.json",   "2024": "variants/v_clip_s2024_test.json"},
    "base":   {"42": "r1full_base.json",   "123": "variants/v_base_s123_test.json",   "2024": "variants/v_base_s2024_test.json"},
    "so400m": {"42": "r1full_so400m.json", "123": "variants/v_so400m_s123_test.json", "2024": "variants/v_so400m_s2024_test.json"},
    "giant":  {"42": "r1full_giant.json",  "123": "variants/v_giant_s123_test.json",  "2024": "variants/v_giant_s2024_test.json"},
}


def load(path):
    with open(os.path.join(DERISK_DIR, path), "r", encoding="utf-8") as f:
        return json.load(f)


def fmt(x, p=2):
    return f"{x:+.{p}f}"


# ---------------------------------------------------------------------------
# 1. seed-42 canonical per-condition (20x4) + per-family means
# ---------------------------------------------------------------------------
s42 = {short: load(fname) for short, _, fname in BACKBONES}

# per-condition delta matrix:  cond -> {backbone: d}
cond_matrix = {}
for fam in FAMILIES:
    for sev in SEVERITIES:
        cond = f"{fam}_{sev}"
        cond_matrix[cond] = {short: s42[short]["per_condition"][cond]["d"] for short, _, _ in BACKBONES}

# per-backbone per-family mean over 5 severities (seed-42), and verify vs summary
fam_mean_s42 = {}          # short -> fam -> mean over 5 sev
for short, _, _ in BACKBONES:
    fam_mean_s42[short] = {}
    for fam in FAMILIES:
        sevvals = [s42[short]["per_condition"][f"{fam}_{sev}"]["d"] for sev in SEVERITIES]
        m = float(np.mean(sevvals))
        fam_mean_s42[short][fam] = m
        # cross-check against the stored summary value
        stored = s42[short]["summary"][fam]
        assert abs(m - stored) < 1e-6, f"{short}/{fam} recompute {m} != summary {stored}"

# ---------------------------------------------------------------------------
# 3-seed per-family means (canonical aggregation: s42=r1full + s123/s2024=variants)
# ---------------------------------------------------------------------------
fam_mean_3seed = {}        # short -> fam -> 3-seed mean of per-family means
fam_perseed = {}           # short -> fam -> [s42, s123, s2024]
for short, _, _ in BACKBONES:
    fam_mean_3seed[short] = {}
    fam_perseed[short] = {}
    for fam in FAMILIES:
        per = []
        for seed in ("42", "123", "2024"):
            d = load(SEED_FILES[short][seed])
            per.append(float(d["summary"][fam]))
        fam_perseed[short][fam] = per
        fam_mean_3seed[short][fam] = float(np.mean(per))

# ---------------------------------------------------------------------------
# REPRODUCTION CHECK A: cross-backbone gaussian average ~ +4.826
# (mean over the 4 backbones' 3-seed gaussian family means)
# ---------------------------------------------------------------------------
gauss_3seed_per_bb = [fam_mean_3seed[short]["gaussian_noise"] for short, _, _ in BACKBONES]
gauss_xbb_3seed = float(np.mean(gauss_3seed_per_bb))
# also the seed-42-only cross-backbone average for transparency
gauss_xbb_s42 = float(np.mean([fam_mean_s42[short]["gaussian_noise"] for short, _, _ in BACKBONES]))

# ---------------------------------------------------------------------------
# REPRODUCTION CHECK B: SO400M gaussian PEAK
#   B1 = seed-42 per-condition max d (canonical r1full)
#   B2 = 3-seed gaussian_5 mean  ~ +13.2 (variants supply s123/s2024)
# ---------------------------------------------------------------------------
so_s42_gauss_conds = {sev: s42["so400m"]["per_condition"][f"gaussian_noise_{sev}"]["d"] for sev in SEVERITIES}
so_s42_peak_sev = max(so_s42_gauss_conds, key=so_s42_gauss_conds.get)
so_s42_peak_val = so_s42_gauss_conds[so_s42_peak_sev]

so_g5_perseed = []
for seed in ("42", "123", "2024"):
    d = load(SEED_FILES["so400m"][seed])
    so_g5_perseed.append(float(d["per_condition"]["gaussian_noise_5"]["d"]))
so_g5_3seed = float(np.mean(so_g5_perseed))

# ---------------------------------------------------------------------------
# REPRODUCTION CHECK C: base seed-42 gaussian_5 over-route ~ -3.2
# ---------------------------------------------------------------------------
base_s42_g5 = float(s42["base"]["per_condition"]["gaussian_noise_5"]["d"])

# ---------------------------------------------------------------------------
# 3-seed TENT/SAR overall context (from summary_3seed.json) for completeness
# ---------------------------------------------------------------------------
with open(os.path.join(ROOT, "results", "_tta_rerun_continual", "summary_3seed.json"), "r", encoding="utf-8") as f:
    tta3 = json.load(f)

# ---------------------------------------------------------------------------
# reproduction verdicts
# ---------------------------------------------------------------------------
def verdict(recomputed, target, tol):
    return "PASS" if abs(recomputed - target) <= tol else "FAIL"

checks = [
    ("Gaussian cross-backbone 3-seed avg = +4.826", gauss_xbb_3seed, 4.826, 0.01),
    ("SO400M gaussian_5 3-seed mean = +13.2", so_g5_3seed, 13.2, 0.05),
    ("Base s42 gaussian_5 = -3.2", base_s42_g5, -3.2, 0.01),
]

# ===========================================================================
# WRITE: per-condition heatmap CSV (20 rows x 4 backbones)  for thesis
# ===========================================================================
heatmap_csv = os.path.join(OUT, "pri5_per_condition_heatmap.csv")
with open(heatmap_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["family", "severity", "condition"] + [disp for _, disp, _ in BACKBONES])
    for fam in FAMILIES:
        for sev in SEVERITIES:
            cond = f"{fam}_{sev}"
            row = [FAM_DISP[fam], sev, cond] + [f"{cond_matrix[cond][short]:.4f}" for short, _, _ in BACKBONES]
            w.writerow(row)
    # trailing family-mean rows (seed-42) for convenience
    for fam in FAMILIES:
        w.writerow([FAM_DISP[fam], "mean(s42)", f"{fam}_mean_s42"] +
                   [f"{fam_mean_s42[short][fam]:.4f}" for short, _, _ in BACKBONES])
    for fam in FAMILIES:
        w.writerow([FAM_DISP[fam], "mean(3seed)", f"{fam}_mean_3seed"] +
                   [f"{fam_mean_3seed[short][fam]:.4f}" for short, _, _ in BACKBONES])

# ===========================================================================
# WRITE: LaTeX mini-table (paper-ready) -- per-backbone x per-family 3-seed means
# ===========================================================================
tex_path = os.path.join(OUT, "pri5_tta_breakdown.tex")
with open(tex_path, "w", encoding="utf-8") as f:
    f.write("% Pri 5: per-corruption-type disc-reweight breakdown (3-seed mean delta AUC, points)\n")
    f.write("% Generated by scripts/pri5_tta_breakdown.py (CPU-only). Read-only on data.\n")
    f.write("% s42 component = results/_coral_derisk/r1full_*.json (canonical);\n")
    f.write("% s123/s2024    = results/_coral_derisk/variants/v_*_s{123,2024}_test.json\n")
    f.write("\\begin{table}[t]\n\\centering\n")
    f.write("\\caption{Per-corruption-type disc-reweight gain (3-seed mean $\\Delta$AUC, points). "
            "Gaussian noise drives nearly all of the gain; blur/JPEG/brightness are gated to the "
            "source model (R1 reliability route) and contribute $\\approx 0$.}\n")
    f.write("\\label{tab:tta_breakdown}\n")
    f.write("\\begin{tabular}{lrrrr}\n\\toprule\n")
    f.write("Backbone & Gaussian & Motion & JPEG & Bright. \\\\\n")
    f.write(" & noise & blur & comp. & \\\\\n")
    f.write("\\midrule\n")
    for short, disp, _ in BACKBONES:
        vals = [fam_mean_3seed[short][fam] for fam in FAMILIES]
        f.write(f"{disp} & {vals[0]:+.2f} & {vals[1]:+.2f} & {vals[2]:+.2f} & {vals[3]:+.2f} \\\\\n")
    f.write("\\midrule\n")
    famavg = [float(np.mean([fam_mean_3seed[s][fam] for s, _, _ in BACKBONES])) for fam in FAMILIES]
    f.write(f"\\textbf{{Average}} & \\textbf{{{famavg[0]:+.2f}}} & {famavg[1]:+.2f} & {famavg[2]:+.2f} & {famavg[3]:+.2f} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# ===========================================================================
# WRITE: markdown report
# ===========================================================================
md_path = os.path.join(OUT, "pri5_tta_breakdown.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# Pri 5 - Per-corruption-type disc-reweight breakdown\n\n")
    f.write("Substantiates the paper prose numbers (+4.8 / +13.2 / -3.2) that currently live "
            "nowhere checkable. CPU-only recompute from on-disk disc-reweight (R1) per-condition data.\n\n")

    f.write("## Data provenance\n\n")
    f.write("- **Seed-42 canonical**: `results/_coral_derisk/r1full_{clip,base,so400m,giant}.json` "
            "(`per_condition[<fam>_<sev>].d = r1 - src`, AUC points 0-100).\n")
    f.write("- **3-seed means**: s42 component = the r1full file above (canonical); s123 / s2024 = "
            "`results/_coral_derisk/variants/v_<bb>_s{123,2024}_test.json`. Per-family mean = mean over "
            "the 5 severities; 3-seed = mean of the three per-seed per-family means.\n")
    f.write("- **TENT/SAR overall (context only)**: `results/_tta_rerun_continual/summary_3seed.json` "
            "holds 3-seed OVERALL-AUC entropy-min deltas (NOT disc-reweight, NOT per-family). It does NOT "
            "contain the +13.2 gaussian value -- that comes from the disc-reweight variants.\n\n")

    f.write("## Table 1 - Per-backbone x per-family mean delta AUC (SEED-42, canonical r1full)\n\n")
    f.write("| Backbone | Gaussian noise | Motion blur | JPEG comp. | Brightness |\n")
    f.write("|---|---:|---:|---:|---:|\n")
    for short, disp, _ in BACKBONES:
        v = fam_mean_s42[short]
        f.write(f"| {disp} | {fmt(v['gaussian_noise'])} | {fmt(v['motion_blur'])} | "
                f"{fmt(v['jpeg_compression'])} | {fmt(v['brightness'])} |\n")
    favg = {fam: float(np.mean([fam_mean_s42[s][fam] for s, _, _ in BACKBONES])) for fam in FAMILIES}
    f.write(f"| **Average** | **{fmt(favg['gaussian_noise'])}** | {fmt(favg['motion_blur'])} | "
            f"{fmt(favg['jpeg_compression'])} | {fmt(favg['brightness'])} |\n\n")

    f.write("## Table 2 - Per-backbone x per-family mean delta AUC (3-SEED mean)\n\n")
    f.write("| Backbone | Gaussian noise | Motion blur | JPEG comp. | Brightness |\n")
    f.write("|---|---:|---:|---:|---:|\n")
    for short, disp, _ in BACKBONES:
        v = fam_mean_3seed[short]
        f.write(f"| {disp} | {fmt(v['gaussian_noise'])} | {fmt(v['motion_blur'])} | "
                f"{fmt(v['jpeg_compression'])} | {fmt(v['brightness'])} |\n")
    favg3 = {fam: float(np.mean([fam_mean_3seed[s][fam] for s, _, _ in BACKBONES])) for fam in FAMILIES}
    f.write(f"| **Average** | **{fmt(favg3['gaussian_noise'])}** | {fmt(favg3['motion_blur'])} | "
            f"{fmt(favg3['jpeg_compression'])} | {fmt(favg3['brightness'])} |\n\n")
    f.write("> Non-Gaussian families are ~0.00 because the R1 reliability route gates blur / JPEG / "
            "brightness back to the source model (`d=0`), so the gain is essentially Gaussian-only.\n\n")

    f.write("## Gaussian severity sweep (the family that carries the gain)\n\n")
    f.write("Per-condition seed-42 delta AUC (canonical r1full):\n\n")
    f.write("| Backbone | gn_1 | gn_2 | gn_3 | gn_4 | gn_5 |\n")
    f.write("|---|---:|---:|---:|---:|---:|\n")
    for short, disp, _ in BACKBONES:
        vals = [cond_matrix[f"gaussian_noise_{s}"][short] for s in SEVERITIES]
        f.write(f"| {disp} | " + " | ".join(fmt(x) for x in vals) + " |\n")
    f.write("\n")

    f.write("## SO400M gaussian PEAK (two distinct numbers -- label carefully)\n\n")
    f.write(f"- **Seed-42 per-condition max** (canonical r1full): `gaussian_noise_{so_s42_peak_sev}` "
            f"= **{fmt(so_s42_peak_val)}** AUC pts. This is the seed-42-only peak.\n")
    f.write(f"- **3-seed gaussian_5 mean** (REVIEW's +13.2): per-seed = "
            f"[{so_g5_perseed[0]:+.2f} (s42), {so_g5_perseed[1]:+.2f} (s123), {so_g5_perseed[2]:+.2f} (s2024)] "
            f"-> mean = **{fmt(so_g5_3seed)}** AUC pts.\n")
    f.write("- Note: the paper's stale **+13.9** is the seed-42-only value (r1full gaussian_5 = "
            f"{fmt(s42['so400m']['per_condition']['gaussian_noise_5']['d'])}); the honest 3-seed figure is "
            f"{fmt(so_g5_3seed)} (~+13.2).\n\n")

    f.write("## Base single-seed over-route (the -3.2 disclosure)\n\n")
    f.write(f"- **Base seed-42 gaussian_5** = **{fmt(base_s42_g5)}** AUC pts (canonical r1full). "
            "This is the single-seed disc-reweight over-route the paper discloses; "
            f"base 3-seed gaussian_5 = {fmt(float(np.mean([load(SEED_FILES['base'][s])['per_condition']['gaussian_noise_5']['d'] for s in ('42','123','2024')])))} "
            "(the s42 value is an outlier).\n\n")

    f.write("## TENT/SAR 3-seed overall context (entropy-min, summary_3seed.json)\n\n")
    f.write("| Backbone | dTENT (3-seed) | dSAR (3-seed) |\n|---|---:|---:|\n")
    for bb_full in ["clip-vit-b-16", "siglip2-base", "siglip2-so400m", "siglip2-giant"]:
        m = tta3[bb_full]["mean"]
        f.write(f"| {bb_full} | {fmt(m['dTENT'])} | {fmt(m['dSAR'])} |\n")
    f.write("\n> These are OVERALL-AUC entropy-min deltas (different mechanism from disc-reweight (R1)); "
            "near-zero, consistent with the paper's 'LN-barrier' finding. Not the source of +13.2.\n\n")

    f.write("## Reproduction checks\n\n")
    f.write("| Claim | Target | Recomputed | Verdict |\n|---|---:|---:|---|\n")
    for label, rec, tgt, tol in checks:
        f.write(f"| {label} | {tgt:+.3f} | {rec:+.4f} | {verdict(rec, tgt, tol)} |\n")
    f.write(f"\n(Transparency) Gaussian cross-backbone **seed-42-only** avg = {fmt(gauss_xbb_s42)} "
            "(the 3-seed +4.826 is higher because base/so400m gaussian gains are larger on s123/s2024).\n")

# ---------------------------------------------------------------------------
# console summary
# ---------------------------------------------------------------------------
print("=== Pri 5 reproduction checks ===")
for label, rec, tgt, tol in checks:
    print(f"  [{verdict(rec, tgt, tol)}] {label}: recomputed {rec:+.4f} (target {tgt:+.3f}, tol {tol})")
print()
print(f"  SO400M s42 gaussian peak: gaussian_noise_{so_s42_peak_sev} = {so_s42_peak_val:+.4f}")
print(f"  SO400M 3-seed gaussian_5: {so_g5_perseed} -> mean {so_g5_3seed:+.4f}")
print(f"  Base   s42 gaussian_5:    {base_s42_g5:+.4f}")
print(f"  Gaussian xbb 3-seed avg:  {gauss_xbb_3seed:+.4f}  (s42-only {gauss_xbb_s42:+.4f})")
print()
print("Wrote:")
for p in (md_path, tex_path, heatmap_csv):
    print("  ", p)
