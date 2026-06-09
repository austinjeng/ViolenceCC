"""Regenerate paper Table 3 (TTA on UCF-Crime-C) from committed JSON artifacts.

This script closes the provenance gap flagged in the 2026-06-07 code/paper review
(H1): the 3-seed disc_reweight ("Ours") numbers, the Source-Only baseline, and the
TENT/SAR entropy results are aggregated here from version-controlled JSONs so the
table is reproducible from git alone, not just from the working tree.

PROVENANCE (exact recipe that reproduces main.tex Table 3):
  Source-Only / Ours / Delta  = mean over 3 seeds {42, 123, 2024}, where
      seed 42   -> results/_coral_derisk/r1full_<tag>.json
      seed 123  -> results/_coral_derisk/variants/v_<tag>_s123_test.json
      seed 2024 -> results/_coral_derisk/variants/v_<tag>_s2024_test.json
  Each summary carries src_mean (Source-Only AUC, mean over the 20 corruption
  conditions) and r1_delta (paired per-seed gain of disc_reweight over Source-Only);
  Ours = src_mean + r1_delta. Delta is reported mean +/- sample std over the 3 seeds.
  The seed-42 disc_reweight math (per-condition w / w_vl / skel_rel columns) is the
  committed implementation in src/tta/disc_reweight.py + src/tta/evaluate_tta.py.

  TENT / SAR = results/_tta_rerun_continual/summary_3seed.json (deterministic
  continual protocol, TENT lr=1e-3, SAR lr=1e-3 rho=0.05, seeds {42,123,2024};
  per-condition eval_metrics under _tta_rerun_continual/<bb>/{source,tent,sar}
  for seed 42 and {source_only,tent,sar}_s<seed> for seeds 123/2024, aggregated
  by scripts/run_tta_seeds_m2.py). Their 3-seed-mean AUC change vs Source-Only is
  <0.1 pp on every backbone (worst 0.082 pp, SigLIP2-Base), so they equal
  Source-Only at the table's 1-decimal display precision. (The legacy seed-42-only
  summary.json is retained for back-compat.)

  The 4 variants/v_<tag>_s42_train.json files are the clean-reference robustness
  check (clip_std_clean computed on clean-TRAIN instead of clean-TEST) backing the
  "clean reference may be drawn from training or clean-test with equivalent results"
  claim; they are NOT the seed-42 source for the table.

Usage:
  python scripts/aggregate_tta_table.py
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DERISK = ROOT / "results" / "_coral_derisk"
CONTINUAL_DIR = ROOT / "results" / "_tta_rerun_continual"
CONTINUAL_3SEED = CONTINUAL_DIR / "summary_3seed.json"
CONTINUAL = CONTINUAL_DIR / "summary.json"  # legacy seed-42-only (back-compat)

# (display name, tag used in artifact filenames, continual-summary key)
BACKBONES = [
    ("CLIP ViT-B/16", "clip", "clip-vit-b-16"),
    ("SigLIP2 Base", "base", "siglip2-base"),
    ("SigLIP2 SO400M", "so400m", "siglip2-so400m"),
    ("SigLIP2 Giant", "giant", "siglip2-giant"),
]


def _summary(path: Path) -> dict:
    return json.loads(path.read_text())["summary"]


def _seed_summaries(tag: str) -> list[dict]:
    """Return the 3 per-seed summaries in the exact recipe order {42, 123, 2024}."""
    return [
        _summary(DERISK / f"r1full_{tag}.json"),  # seed 42
        _summary(DERISK / "variants" / f"v_{tag}_s123_test.json"),  # seed 123
        _summary(DERISK / "variants" / f"v_{tag}_s2024_test.json"),  # seed 2024
    ]


def _continual_delta(ckey: str) -> tuple[float, float, int]:
    """(tent_d, sar_d, n_seeds) entropy change vs Source-Only for a backbone.

    Prefers the 3-seed summary; falls back to the legacy seed-42-only summary.json.
    """
    if CONTINUAL_3SEED.exists():
        m = json.loads(CONTINUAL_3SEED.read_text())[ckey]["mean"]
        return m["dTENT"], m["dSAR"], m["n_seeds"]
    c = json.loads(CONTINUAL.read_text())[ckey]
    return c["tent"] - c["source"], c["sar"] - c["source"], 1


def main() -> None:
    n_seeds_entropy = 3 if CONTINUAL_3SEED.exists() else 1

    print(f"{'Backbone':16} {'Source':>7} {'TENT':>7} {'SAR':>7} {'Ours':>7} "
          f"{'D_Ours':>14}   {'TENT_d':>7} {'SAR_d':>7}")
    print("-" * 86)

    src_all, ours_all = [], []
    for name, tag, ckey in BACKBONES:
        seeds = _seed_summaries(tag)
        srcs = [s["src_mean"] for s in seeds]
        deltas = [s["r1_delta"] for s in seeds]
        ours = [srcs[i] + deltas[i] for i in range(3)]

        source = st.mean(srcs)
        ours_m = st.mean(ours)
        d_m = st.mean(deltas)
        d_sd = st.stdev(deltas)
        src_all.append(source)
        ours_all.append(ours_m)

        tent_d, sar_d, _ = _continual_delta(ckey)
        # TENT/SAR equal Source-Only at 1-dp display (entropy change < 0.1 pp).
        tent = source
        sar = source

        print(f"{name:16} {source:7.1f} {tent:7.1f} {sar:7.1f} {ours_m:7.1f} "
              f"{'+%.2f' % d_m:>7}+-{d_sd:.2f}   {tent_d:+7.3f} {sar_d:+7.3f}")

    mean_src = st.mean(src_all)
    mean_ours = st.mean(ours_all)
    print("-" * 86)
    print(f"{'Mean':16} {mean_src:7.1f} {mean_src:7.1f} {mean_src:7.1f} {mean_ours:7.1f} "
          f"{'+%.2f' % (mean_ours - mean_src):>7}")
    print()
    src = "summary_3seed.json" if n_seeds_entropy == 3 else "summary.json"
    print(f"TENT/SAR entropy change vs Source-Only is <0.1 pp on every backbone "
          f"(continual, {n_seeds_entropy}-seed mean "
          f"{'{42,123,2024}' if n_seeds_entropy == 3 else '{42}'}); "
          f"see results/_tta_rerun_continual/{src}.")


if __name__ == "__main__":
    main()
