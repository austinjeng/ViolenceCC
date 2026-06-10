"""Pri 7: Per-class UCF complementarity (skeleton gain by category group).

Question: Does adding the skeleton modality (gated fusion) help HUMAN-MOTION
classes more than APPEARANCE/NO-HUMAN classes? This tests the paper's
"motion not captured by appearance" complementarity claim.

Method:
  delta_per_class = mean_over_seeds( gated.auc - clip_only.auc )  [per category]
  Then compare the two category groups (mean +/- std across classes).

Backbone: 'giant' (the UCF headline backbone). 3 seeds: 42, 123, 2024.

CPU-only: numpy + csv + json only. No torch, no CUDA.
Determinism: no RNG needed (deterministic averaging), but we fix one anyway
  per environment instructions.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

# Fixed seed per environment instructions (not actually used for any sampling,
# but set so the run is fully reproducible).
RNG = np.random.default_rng(12345)

REPO = Path(r"D:\ViolenceCC")
OUT_DIR = REPO / "results" / "_analysis_2026-06-10"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 123, 2024]
FUSED_TMPL = "results/ucf_gated_fusion_giant_s{seed}/per_category.csv"
VISUAL_TMPL = "results/ucf_clip_only_giant_s{seed}/per_category.csv"

# Category grouping (per task spec).
HUMAN_MOTION = {
    "Abuse", "Arrest", "Assault", "Burglary", "Fighting",
    "Robbery", "Shooting", "Shoplifting", "Stealing", "Vandalism",
}
APPEARANCE = {"Arson", "Explosion", "RoadAccidents"}


def read_per_category(path: Path) -> dict[str, float]:
    """Return {category: auc} from a per_category.csv file."""
    out: dict[str, float] = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["category"].strip()
            if not cat:
                continue
            out[cat] = float(row["auc"])
    return out


def recover_per_category_counts() -> dict[str, int]:
    """Count distinct ANOMALY video_ids per category from an eval_scores.npz.

    The npz keys are video_ids; category = leading non-digit prefix
    (e.g. 'RoadAccidents001' -> 'RoadAccidents', 'Abuse028' -> 'Abuse').
    'Normal_Videos_*' rows are excluded (they belong to no anomaly category).
    Per-category test-video counts are identical across seeds/backbones
    (same fixed test split), so any one npz suffices.
    """
    npz_path = REPO / "results" / "ucf_clip_only_giant_s42" / "eval_scores.npz"
    counts: dict[str, int] = {}
    with np.load(npz_path, allow_pickle=True) as d:
        for key in d.files:
            if key.startswith("Normal"):
                continue
            m = re.match(r"^([A-Za-z]+)", key)
            if not m:
                continue
            cat = m.group(1)
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def main() -> None:
    # ---- Load all seeds for both conditions ----
    fused_by_seed: dict[int, dict[str, float]] = {}
    visual_by_seed: dict[int, dict[str, float]] = {}
    for s in SEEDS:
        fused_by_seed[s] = read_per_category(REPO / FUSED_TMPL.format(seed=s))
        visual_by_seed[s] = read_per_category(REPO / VISUAL_TMPL.format(seed=s))

    # ---- Sanity: identical category sets across all 6 files ----
    cat_sets = [set(d) for d in list(fused_by_seed.values()) + list(visual_by_seed.values())]
    base = cat_sets[0]
    assert all(c == base for c in cat_sets), "Category sets differ across files!"
    categories = sorted(base)

    # Sanity: every category falls into exactly one group.
    grouped = HUMAN_MOTION | APPEARANCE
    unassigned = set(categories) - grouped
    extra = grouped - set(categories)
    assert not unassigned, f"Categories not assigned to a group: {unassigned}"
    assert not extra, f"Group categories absent from data: {extra}"

    # ---- Per-class 3-seed mean delta (gated.auc - visual.auc) ----
    counts = recover_per_category_counts()

    rows = []
    for cat in categories:
        per_seed_delta = [
            fused_by_seed[s][cat] - visual_by_seed[s][cat] for s in SEEDS
        ]
        mean_delta = float(np.mean(per_seed_delta))
        std_delta = float(np.std(per_seed_delta, ddof=0))  # spread across seeds
        group = "human_motion" if cat in HUMAN_MOTION else "appearance"
        rows.append({
            "category": cat,
            "group": group,
            "n_test_videos": counts.get(cat, -1),
            "delta_auc_mean_3seed": mean_delta,
            "delta_auc_std_across_seeds": std_delta,
            "delta_auc_pp": mean_delta * 100.0,
            "fused_auc_mean": float(np.mean([fused_by_seed[s][cat] for s in SEEDS])),
            "visual_auc_mean": float(np.mean([visual_by_seed[s][cat] for s in SEEDS])),
            **{f"delta_s{s}": fused_by_seed[s][cat] - visual_by_seed[s][cat] for s in SEEDS},
        })

    # Sort by mean delta descending (largest skeleton gain first).
    rows.sort(key=lambda r: r["delta_auc_mean_3seed"], reverse=True)

    # ---- Group statistics (mean +/- std ACROSS CLASSES of the per-class deltas) ----
    def group_stats(group_name: str) -> dict[str, float]:
        vals = np.array([r["delta_auc_mean_3seed"] for r in rows if r["group"] == group_name])
        return {
            "n_classes": int(vals.size),
            "mean_delta": float(np.mean(vals)),
            "std_delta": float(np.std(vals, ddof=1)),  # sample std across classes
            "mean_delta_pp": float(np.mean(vals)) * 100.0,
            "std_delta_pp": float(np.std(vals, ddof=1)) * 100.0,
            "n_positive": int(np.sum(vals > 0)),
            "min_pp": float(np.min(vals)) * 100.0,
            "max_pp": float(np.max(vals)) * 100.0,
        }

    hm = group_stats("human_motion")
    ap = group_stats("appearance")

    # Welch's t-test (unequal variance) between the two groups of per-class deltas,
    # computed manually (no scipy dependency required). Tiny n => weak power; report
    # descriptively only.
    hm_vals = np.array([r["delta_auc_mean_3seed"] for r in rows if r["group"] == "human_motion"])
    ap_vals = np.array([r["delta_auc_mean_3seed"] for r in rows if r["group"] == "appearance"])
    m1, m2 = hm_vals.mean(), ap_vals.mean()
    v1, v2 = hm_vals.var(ddof=1), ap_vals.var(ddof=1)
    n1, n2 = hm_vals.size, ap_vals.size
    se = np.sqrt(v1 / n1 + v2 / n2)
    t_stat = float((m1 - m2) / se) if se > 0 else float("nan")
    # Welch-Satterthwaite df
    df = ((v1 / n1 + v2 / n2) ** 2) / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    ) if (n1 > 1 and n2 > 1) else float("nan")

    # ---- Write CSV ----
    csv_path = OUT_DIR / "pri7_per_class_complementarity.csv"
    fieldnames = [
        "category", "group", "n_test_videos",
        "delta_auc_pp", "delta_auc_mean_3seed", "delta_auc_std_across_seeds",
        "fused_auc_mean", "visual_auc_mean",
        "delta_s42", "delta_s123", "delta_s2024",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fieldnames})

    # ---- Write Markdown report ----
    md = []
    md.append("# Pri 7 — Per-class UCF complementarity (does skeleton help motion classes more?)\n")
    md.append("**Backbone:** giant (UCF headline) | **Seeds:** 42, 123, 2024 | "
              "**Metric:** per-category frame-level AUC\n")
    md.append("**Comparison:** gated fusion (Skeleton+CLIP) minus visual-only (CLIP). "
              "Positive Δ = skeleton helps that category.\n")
    md.append("\n## Per-class skeleton gain (3-seed mean), sorted descending\n")
    md.append("| Category | Group | n (test vids) | ΔAUC (pp) | σ across seeds (pp) | Fused AUC | Visual AUC |")
    md.append("|---|---|---:|---:|---:|---:|---:|")
    for r in rows:
        md.append(
            f"| {r['category']} | {'HM' if r['group']=='human_motion' else 'APP'} "
            f"| {r['n_test_videos']} | {r['delta_auc_pp']:+.2f} "
            f"| {r['delta_auc_std_across_seeds']*100:.2f} "
            f"| {r['fused_auc_mean']:.4f} | {r['visual_auc_mean']:.4f} |"
        )

    md.append("\nHM = human-motion group; APP = appearance/no-human group.\n")

    md.append("\n## Group means (mean ± std of per-class ΔAUC, across classes)\n")
    md.append("| Group | n classes | mean ΔAUC (pp) | std (pp) | classes with Δ>0 | min (pp) | max (pp) |")
    md.append("|---|---:|---:|---:|---:|---:|---:|")
    md.append(
        f"| HUMAN-MOTION | {hm['n_classes']} | {hm['mean_delta_pp']:+.3f} "
        f"| {hm['std_delta_pp']:.3f} | {hm['n_positive']}/{hm['n_classes']} "
        f"| {hm['min_pp']:+.2f} | {hm['max_pp']:+.2f} |"
    )
    md.append(
        f"| APPEARANCE   | {ap['n_classes']} | {ap['mean_delta_pp']:+.3f} "
        f"| {ap['std_delta_pp']:.3f} | {ap['n_positive']}/{ap['n_classes']} "
        f"| {ap['min_pp']:+.2f} | {ap['max_pp']:+.2f} |"
    )

    diff_pp = (hm["mean_delta"] - ap["mean_delta"]) * 100.0
    md.append(
        f"\n**Group-mean difference (HM − APP):** {diff_pp:+.3f} pp "
        f"(Welch t = {t_stat:.2f}, df ≈ {df:.1f}). "
        "With only 3 appearance classes this t-test has negligible power; treat as descriptive.\n"
    )

    # ---- Honest verdict ----
    md.append("\n## Verdict — does the evidence support 'motion not captured by appearance'?\n")
    verdict_lines = []
    if diff_pp > 0:
        verdict_lines.append(
            f"- The human-motion group shows a LARGER mean skeleton gain than the appearance "
            f"group by {diff_pp:+.3f} pp ({hm['mean_delta_pp']:+.3f} vs {ap['mean_delta_pp']:+.3f} pp). "
            "Direction is CONSISTENT with the paper's claim."
        )
    else:
        verdict_lines.append(
            f"- The human-motion group does NOT show a larger mean skeleton gain "
            f"({hm['mean_delta_pp']:+.3f} vs appearance {ap['mean_delta_pp']:+.3f} pp; "
            f"difference {diff_pp:+.3f} pp). Direction CONTRADICTS the simple version of the claim."
        )
    # Overlap / mixed evidence flags
    if hm["std_delta_pp"] > abs(diff_pp):
        verdict_lines.append(
            f"- BUT the within-HM spread (σ={hm['std_delta_pp']:.3f} pp) is larger than the "
            f"between-group gap ({abs(diff_pp):.3f} pp): the group difference is small relative "
            "to class-to-class noise. Evidence is MIXED, not clean."
        )
    verdict_lines.append(
        f"- {hm['n_positive']}/{hm['n_classes']} human-motion classes have positive Δ; "
        f"{ap['n_positive']}/{ap['n_classes']} appearance classes do."
    )
    md.extend(verdict_lines)

    md.append("\n## CAVEAT — per-class AUC is NOISY (tiny test-video counts)\n")
    small = sorted([(r["category"], r["n_test_videos"]) for r in rows], key=lambda x: x[1])
    smallest = ", ".join(f"{c} (n={n})" for c, n in small[:6])
    md.append(
        "- Per-category test-video counts are recovered by counting distinct ANOMALY "
        "video_ids in `results/ucf_clip_only_giant_s42/eval_scores.npz` (keys are video_ids; "
        "category = leading non-digit prefix; identical across seeds/backbones since the test "
        "split is fixed).\n"
    )
    md.append(
        f"- Several categories have only a handful of test videos (smallest: {smallest}). "
        "A single video's score can swing that category's AUC by several points, so per-class "
        "deltas — and therefore the group means built from them — carry wide, unquantified "
        "uncertainty. The 'across-seeds σ' column captures only seed/training noise, NOT the "
        "(larger) sampling noise from tiny per-class video counts.\n"
    )
    md.append(
        "- Within-class video counts are unequal, so the unweighted group mean treats a "
        "5-video class (e.g. Robbery, Stealing, Fighting) the same as a 22-video class "
        "(e.g. Shooting). This is a deliberate per-class average, but it amplifies the "
        "influence of the noisiest small classes.\n"
    )

    md_path = OUT_DIR / "pri7_per_class_complementarity.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    # ---- Console summary (for the agent) ----
    print("=== PER-CLASS DELTA (sorted desc) ===")
    for r in rows:
        print(f"{r['category']:>14s} [{('HM' if r['group']=='human_motion' else 'APP')}] "
              f"n={r['n_test_videos']:>2d}  Δ={r['delta_auc_pp']:+.3f}pp  "
              f"(seedσ={r['delta_auc_std_across_seeds']*100:.2f}pp)")
    print("\n=== GROUP MEANS (mean±std across classes) ===")
    print(f"HUMAN-MOTION: {hm['mean_delta_pp']:+.3f} ± {hm['std_delta_pp']:.3f} pp "
          f"(n={hm['n_classes']}, {hm['n_positive']} positive, "
          f"range [{hm['min_pp']:+.2f},{hm['max_pp']:+.2f}])")
    print(f"APPEARANCE  : {ap['mean_delta_pp']:+.3f} ± {ap['std_delta_pp']:.3f} pp "
          f"(n={ap['n_classes']}, {ap['n_positive']} positive, "
          f"range [{ap['min_pp']:+.2f},{ap['max_pp']:+.2f}])")
    print(f"HM - APP = {diff_pp:+.3f} pp  (Welch t={t_stat:.2f}, df≈{df:.1f})")
    print(f"\nWrote: {csv_path}")
    print(f"Wrote: {md_path}")


if __name__ == "__main__":
    main()
