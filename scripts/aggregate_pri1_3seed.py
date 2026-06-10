"""Aggregate 3-seed mean+/-std for the Pri-1 ablation configs (REVIEW-2026-06-10).

Reads results/results-index.csv, groups the 26 previously-single-seed ablation
configs by (run_name minus the _s<seed> suffix), and reports mean+/-std over
seeds {42,123,2024} of the dataset-appropriate metric (UCF->AUC, XD->AP).
Compares each against its seed-42-only value (what the paper currently reports).

CPU-only, read-only. Run from repo root with the vcc-main python.
"""
from __future__ import annotations

import csv
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

INDEX = Path("results/results-index.csv")
SEEDS = {42, 123, 2024}

# The 26 Pri-1 configs, identified by run_name with the _s<seed> suffix stripped.
PRI1_BASES = [
    # Late Fusion
    "ucf_late_fusion", "xd_late_fusion",
    "ucf_late_fusion_siglip2", "xd_late_fusion_siglip2",
    "ucf_late_fusion_so400m", "xd_late_fusion_so400m",
    "ucf_late_fusion_giant", "xd_late_fusion_giant",
    # GF 2-Person
    "ucf_gated_fusion_2person", "xd_gated_fusion_2person",
    "ucf_gated_fusion_siglip2_2person", "xd_gated_fusion_siglip2_2person",
    "ucf_gated_fusion_so400m_2person", "xd_gated_fusion_so400m_2person",
    "ucf_gated_fusion_giant_2person", "xd_gated_fusion_giant_2person",
    # GF Mean-Only (clip_mean)
    "ucf_gated_fusion_clip_mean", "xd_gated_fusion_clip_mean",
    "ucf_gated_fusion_siglip2_clip_mean", "xd_gated_fusion_siglip2_clip_mean",
    "ucf_gated_fusion_so400m_clip_mean", "xd_gated_fusion_so400m_clip_mean",
    "ucf_gated_fusion_giant_clip_mean", "xd_gated_fusion_giant_clip_mean",
    # Skeleton Only
    "ucf_skeleton_only", "xd_skeleton_only",
]
PRI1_SET = set(PRI1_BASES)

SUFFIX = re.compile(r"_s(42|123|2024)$")


def main() -> None:
    # base -> seed -> (auc, ap, dataset)
    rows: dict[str, dict[int, tuple]] = defaultdict(dict)
    with open(INDEX, newline="") as f:
        for r in csv.DictReader(f):
            rn = r["run_name"]
            m = SUFFIX.search(rn)
            if not m:
                continue
            base = SUFFIX.sub("", rn)
            if base not in PRI1_SET:
                continue
            seed = int(m.group(1))
            if seed not in SEEDS:
                continue
            try:
                auc = float(r["auc"]); ap = float(r["ap"])
            except (ValueError, KeyError):
                continue
            rows[base][seed] = (auc, ap, r["dataset"])

    print(f"{'config':40s} {'metric':6s} {'s42':>7s} {'s123':>7s} {'s2024':>7s} "
          f"{'3seed mean':>11s} {'std':>6s}")
    print("-" * 92)
    out_lines = []
    for base in PRI1_BASES:
        seedmap = rows.get(base, {})
        present = sorted(seedmap)
        if not present:
            print(f"{base:40s} (no rows found)")
            continue
        ds = seedmap[present[0]][2]
        metric = "AUC" if ds == "ucf" else "AP"
        idx = 0 if metric == "AUC" else 1  # auc col vs ap col
        vals = {s: seedmap[s][idx] * 100.0 for s in present}
        triple = [vals.get(s, float("nan")) for s in (42, 123, 2024)]
        complete = [vals[s] for s in (42, 123, 2024) if s in vals]
        mean = st.mean(complete)
        std = st.stdev(complete) if len(complete) >= 2 else 0.0
        def fmt(x):
            return f"{x:7.2f}" if x == x else "   --  "
        print(f"{base:40s} {metric:6s} {fmt(triple[0])} {fmt(triple[1])} {fmt(triple[2])} "
              f"{mean:11.2f} {std:6.2f}  (n={len(complete)})")
        out_lines.append((base, metric, triple, mean, std, len(complete)))

    # Highlight the load-bearing paper numbers
    print("\n=== Load-bearing paper numbers (paper-stated vs 3-seed) ===")
    checks = [
        ("ucf_gated_fusion_giant_clip_mean", "AUC", 83.0, "GF Mean-Only Giant (main.tex :287/:384 '83.0')"),
        ("xd_gated_fusion_so400m_clip_mean", "AP", 79.9, "GF Mean-Only SO400M (main.tex :256 '79.9')"),
        ("ucf_skeleton_only", "AUC", 71.8, "Skeleton-only UCF (main.tex '71.8')"),
        ("xd_skeleton_only", "AP", 40.9, "Skeleton-only XD (main.tex '40.9')"),
    ]
    for base, metric, paper, label in checks:
        seedmap = rows.get(base, {})
        idx = 0 if metric == "AUC" else 1
        complete = [seedmap[s][idx] * 100.0 for s in (42, 123, 2024) if s in seedmap]
        if not complete:
            print(f"  {label}: NO DATA"); continue
        mean = st.mean(complete); std = st.stdev(complete) if len(complete) >= 2 else 0.0
        s42 = seedmap.get(42, (None, None))[idx]
        s42s = f"{s42*100:.2f}" if s42 is not None else "--"
        print(f"  {label}\n     paper={paper}  s42={s42s}  3-seed={mean:.2f}+/-{std:.2f}  "
              f"delta(mean-s42)={mean - (s42*100 if s42 else mean):+.2f}")


if __name__ == "__main__":
    main()
