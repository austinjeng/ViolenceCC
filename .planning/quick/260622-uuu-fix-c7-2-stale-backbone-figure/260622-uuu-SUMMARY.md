---
quick_id: 260622-uuu
slug: fix-c7-2-stale-backbone-figure
date: 2026-06-22
status: complete
commit: 2e6cb6b
---

# Summary — Quick Task 260622-uuu

Fixed HIGH review finding **C7-2** (dup **T5-1**): `fig_backbone_comparison.pdf` rendered
single-seed (s42) bars while its caption claimed "three-seed means", contradicting the
now-3-seed Tables 1/2 (worst case: XD gated Giant 73.6 in figure vs 76.8 in table).

## Root cause
`scripts/generate_phase10_charts.py:build_comparison_table` read a single `_s42` run per cell
(`COMPARISON_MAP` hardcodes `_s42` names) — no seed averaging — so the generated
`backbone_comparison_4way.csv`, and the figure built from it, were single-seed.

## Changes (commit 2e6cb6b)
- `scripts/generate_phase10_charts.py`: added `_seed_mean()`; `build_comparison_table` now
  averages every CLIP/SigLIP2/SO400M/Giant AUC/AP cell over the `{_s42,_s123,_s2024}` family
  (deltas auto-update). Fixes the root cause reproducibly.
- Regenerated `results/phase10_charts/backbone_comparison_4way.csv` (+ the two tracked phase10
  PNGs) and `paper/figures/fig_backbone_comparison.pdf` via a targeted single-figure regen
  (other paper figures untouched — mirrors quick-260611-fsl precedent).
- `paper/main.tex` caption: "six fusion variants" → "three"; removed the false
  "Visual Only and Gated Fusion … three-seed means; Late Fusion is single-seed" clause →
  "All bars are three-seed means over seeds {42,123,2024}, matching Tables 1–2
  (Gated Fusion shown with ±std)".

## Verification
- Regenerated CSV: all 24 (3 variants × 4 backbones × 2 metrics) cells equal their Table 1/2
  cell to ≤0.05pp (automated check: ALL MATCH).
- Figure bar labels: now {…78.7, 76.8, 81.4…} (the table values); old single-seed values
  79.7 / 73.6 / 81.7 are **gone**.
- `git status` confirmed only `fig_backbone_comparison.pdf` changed under `paper/figures/`.
- `scripts/build_paper.ps1 -Clean` → main.pdf rebuilt, 11 pages, latexmk converged; rendered
  caption reads "three fusion variants … All bars are three-seed means … matching Tables 1–2".
- Headlines UCF 82.5% / XD 78.7% unchanged.

## Notes
- `seed_stability_4way.csv` was already correct 3-seed per-seed data (no change).
- The figure shows ±std error bars on Gated Fusion only (as the caption now states);
  the other bars are 3-seed means without drawn error bars — accurate, not misleading.
