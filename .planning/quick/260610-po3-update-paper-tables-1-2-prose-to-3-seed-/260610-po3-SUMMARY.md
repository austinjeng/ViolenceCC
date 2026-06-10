---
quick_id: 260610-po3
status: complete
date: 2026-06-10
commit: 33591ac
---

# Quick Task 260610-po3: Paper 3-seed all ablation rows + Pri-5 table — SUMMARY

**Status:** Complete. `paper/main.tex` updated + new `scripts/gen_ablation_tables_3seed.py`,
commit `33591ac`. PDF rebuilds clean: **10 pages, 0 errors, 0 undefined refs**. Headlines
(gated UCF 82.5 / XD 78.7) unchanged.

## What changed
- **Tables 1 & 2:** the 4 single-seed rows (Skeleton Only, Late Fusion, GF 2-Person, GF
  Mean-Only) → 3-seed mean±std. Values from committed `results-index.csv` (3aac394); the
  generator **reproduces the already-3-seed rows (Visual Only, Gated Fusion) exactly** →
  pipeline faithful. XD Late Fusion best moves Giant→SO400M (65.74 > 65.67).
- **Material shifts:** UCF GF Mean-Only 83.0→82.5 (now ~tied with gated, not above);
  XD GF Mean-Only SO400M 79.9→78.4 (now below gated 78.7); skeleton-only UCF 71.8→68.8±2.8;
  XD 40.9→40.8. Removes the prior "a pooling variant beats our method" tension on both datasets.
- **Captions + :217:** "Gated Fusion and Visual Only rows…" → "All rows…"; dropped the
  single-seed disclosure sentence (now uniform 3-seed reporting).
- **Prose:** skeleton 71.8→68.8 (×3: §4.3, §5, conclusion) / 40.9→40.8 (×2); late-fusion CLIP
  XD 64.4→63.9 + gap 12.1→12.6 (×2); CLIP late fusion UCF 78.6→78.9 + drop 2.6→2.3; mean-only
  83.0→82.5 (×3). NOT :306 (unrelated TTA-source 64.4).
- **New table `tab:tta_breakdown`** (§4.5): per-corruption disc_reweight 3-seed gain — gaussian
  avg +4.83, motion/JPEG/brightness ≈0 by reliability-gate construction. Referenced from the
  gaussian-concentration sentence. Caption fixed from the agent's "CORAL-TTA" to
  "discriminative-reliability reweighting".

## Verification
- `gen_ablation_tables_3seed.py` check: recomputed Visual Only / Gated Fusion == paper exactly.
- `build_paper.ps1 -Clean` → "Output written on main.pdf (10 pages)"; log has no `^!` errors,
  no undefined references (so `tab:tta_breakdown` resolved).
- Post-edit grep: no stale 83.0/71.8/40.9/12.1/78.6 remain except the intended survivors
  (:306 TTA-source 64.4; :281 figure caption "single-seed"). Caught + fixed a missed 71.8 in
  the §5 complementarity paragraph.

## NOT done (flagged)
- **`fig_backbone_comparison.pdf` left untouched.** Its chart CSV
  `results/phase10_charts/backbone_comparison_4way.csv` holds STALE values (pre-λ0 XD, e.g.
  Gated Giant 0.736 vs current 76.8) and the figure only plots Visual/Late/Gated; regenerating
  from it would corrupt the figure. The caption already discloses "Late Fusion is single-seed",
  so the figure is internally honest, but there is now a minor table(3-seed)/figure(s42)
  Late-Fusion discrepancy. **Follow-up:** rebuild the chart CSV from canonical results-index +
  regenerate the figure (separate task; verify whether the committed PDF's XD panel is itself
  stale).
