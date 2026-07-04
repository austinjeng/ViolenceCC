#!/usr/bin/env python
"""Thesis data rollup: per-condition continual TENT/SAR/source AUCs -> one CSV.

Walks results/_tta_rerun_continual/<backbone>/<method>/<condition>/
eval_metrics.json (the post-dropout-fix continual-protocol rerun; the
per-condition JSONs are untracked scratch) and emits ONE tidy tracked CSV:

  results/_tta_rerun_continual/per_condition_rollup.csv
      columns: backbone,method,condition,seed,auc
      (auc verbatim from eval_metrics.json, 0-1 scale; multiply by 100 for
       the "points" scale used by summary_3seed.json and the thesis text)

This gives Ch 6 a git-tracked per-condition TENT/SAR source (partially
discharges review item C7-1) without tracking ~760 raw JSONs.

Method-dir naming in the rerun tree (parsed, then cross-checked against each
JSON's own method/source_run fields):
  source / source_only_s123 / source_only_s2024 -> source_only, seeds 42/123/2024
  tent / tent_s123 / tent_s2024                 -> tent,        seeds 42/123/2024
  sar  / sar_s123  / sar_s2024                  -> sar,         seeds 42/123/2024
  tent@paper(0.005), sar@paper(1e-4,0.01)       -> paper-hyperparameter
                                                   variants (clip only, seed 42)

Self-check: recomputes per-backbone x per-seed 20-condition means for
source_only/tent/sar from the rollup and asserts they match the tracked
results/_tta_rerun_continual/summary_3seed.json within 0.01 points (both
per-seed values and 3-seed means) -- stale or partial data fails loudly.

CPU-only. json / csv / numpy only. NO torch / CUDA. Deterministic (sorted
walk + sorted output rows; RNG seeded 12345 for policy compliance).
"""
import csv
import json
import os

import numpy as np

# ---- determinism (policy: seed every RNG with a fixed int) -------------------
_RNG = np.random.default_rng(12345)  # not used in any stochastic path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "results", "_tta_rerun_continual")
OUT_CSV = os.path.join(BASE, "per_condition_rollup.csv")
SUMMARY_3SEED = os.path.join(BASE, "summary_3seed.json")

BACKBONES = ["clip-vit-b-16", "siglip2-base", "siglip2-so400m", "siglip2-giant"]
N_CONDITIONS = 20


def _parse_method_dir(name):
    """Method-dir name -> (method, seed)."""
    seed = "42"
    base = name
    if base.endswith("_s123"):
        seed, base = "123", base[: -len("_s123")]
    elif base.endswith("_s2024"):
        seed, base = "2024", base[: -len("_s2024")]
    if base in ("source", "source_only"):
        base = "source_only"
    return base, seed


def main():
    rows = []
    for bb in BACKBONES:
        bb_dir = os.path.join(BASE, bb)
        assert os.path.isdir(bb_dir), f"missing backbone dir: {bb_dir}"
        for method_dir in sorted(os.listdir(bb_dir)):
            mdir = os.path.join(bb_dir, method_dir)
            if not os.path.isdir(mdir):
                continue
            method, seed = _parse_method_dir(method_dir)
            for cond in sorted(os.listdir(mdir)):
                jpath = os.path.join(mdir, cond, "eval_metrics.json")
                if not os.path.isfile(jpath):
                    continue
                with open(jpath, "r", encoding="utf-8") as f:
                    m = json.load(f)
                # cross-checks: the JSON's own fields agree with the dir parse
                assert m["backbone"] == bb, (jpath, m["backbone"])
                assert m["method"].split("@")[0] == method.split("@")[0], (
                    jpath, m["method"], method)
                assert cond == f"{m['corruption_type']}_{m['severity']}", (
                    jpath, cond)
                assert m["source_run"].endswith(f"_s{seed}"), (
                    jpath, m["source_run"], seed)
                rows.append((bb, method, cond, seed, m["auc"]))

    rows.sort(key=lambda r: (r[0], r[1], int(r[3]), r[2]))
    print(f"[thesis_tta_rollup] collected {len(rows)} rows "
          f"({len({(r[0], r[1], r[3]) for r in rows})} backbone/method/seed groups)")

    # ---- self-check vs tracked summary_3seed.json ----------------------------
    with open(SUMMARY_3SEED, "r", encoding="utf-8") as f:
        s3 = json.load(f)
    by_group = {}
    for bb, method, cond, seed, auc in rows:
        by_group.setdefault((bb, method, seed), []).append(auc)
    for bb in BACKBONES:
        for method, key in (("source_only", "source"), ("tent", "tent"),
                            ("sar", "sar")):
            seed_means = []
            for seed in ("42", "123", "2024"):
                aucs = by_group[(bb, method, seed)]
                assert len(aucs) == N_CONDITIONS, (
                    f"{bb}/{method}/s{seed}: {len(aucs)} conditions != "
                    f"{N_CONDITIONS}")
                mean_pts = float(np.mean(aucs)) * 100.0
                ref = float(s3[bb]["seeds"][seed][key])
                assert abs(mean_pts - ref) <= 0.01, (
                    f"{bb}/{method}/s{seed}: rollup mean {mean_pts:.4f} != "
                    f"summary_3seed {ref:.4f}")
                seed_means.append(mean_pts)
            mean3 = float(np.mean(seed_means))
            ref3 = float(s3[bb]["mean"][key])
            assert abs(mean3 - ref3) <= 0.01, (
                f"{bb}/{method}: rollup 3-seed mean {mean3:.4f} != "
                f"summary_3seed {ref3:.4f}")
    print("[thesis_tta_rollup] self-check PASS: per-seed and 3-seed "
          "source/tent/sar 20-condition means match summary_3seed.json "
          "within 0.01 points")

    # ---- write ----------------------------------------------------------------
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["backbone", "method", "condition", "seed", "auc"])
        for bb, method, cond, seed, auc in rows:
            w.writerow([bb, method, cond, seed, repr(auc)])
    print(f"[thesis_tta_rollup] wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
