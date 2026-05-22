---
phase: 10-siglip2-giant-backbone-comparison
plan: 04
subsystem: analysis
tags: [backbone-comparison, visualization, siglip2-giant, four-way]
dependency_graph:
  requires: [10-03]
  provides: [phase10-charts, four-way-comparison]
  affects: [thesis-results]
tech_stack:
  added: []
  patterns: [matplotlib-agg, grouped-bar-charts, pandas-csv-export]
key_files:
  created:
    - scripts/generate_phase10_charts.py
    - results/phase10_charts/backbone_comparison_4way.csv
    - results/phase10_charts/seed_stability_4way.csv
    - results/phase10_charts/comparison_auc_4way.png
    - results/phase10_charts/comparison_ap_4way.png
    - results/phase10_charts/seed_stability_4way.png
  modified: []
decisions:
  - "VAL_SZ reduced to 10 from Phase 9's 11 to fit 4-bar value labels without overlap"
  - "Bar width 0.2 (vs Phase 9's 0.25) to accommodate 4 grouped bars"
metrics:
  duration: 134s
  completed: 2026-05-22T08:07:00Z
---

# Phase 10 Plan 04: Four-Way Backbone Comparison Analysis Summary

Four-way backbone comparison (CLIP ViT-B/16 vs SigLIP2 ViT-B/16 vs SigLIP2 SO400M vs SigLIP2 Giant-opt) analysis script with CSV tables and PNG charts for thesis.

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create four-way comparison script | 416067b | scripts/generate_phase10_charts.py |
| 2 | Generate four-way comparison tables and charts | c59f0e8 | results/phase10_charts/* (5 files) |

## Key Results

### UCF-Crime (AUC, seed=42)

| Variant | CLIP | SigLIP2 | SO400M | Giant | Best |
|---------|------|---------|--------|-------|------|
| Visual Only | 81.69 | 79.11 | 81.41 | 83.09 | Giant +1.4 |
| Late Fusion | 78.71 | 79.93 | 80.26 | 80.88 | Giant +2.2 |
| Gated Fusion | 82.27 | 79.61 | 82.18 | 83.23 | Giant +1.0 |
| GF 2-Person | 81.65 | 79.48 | 81.97 | 83.48 | Giant +1.8 |
| GF Mean-Only | 81.78 | 80.00 | 82.45 | 83.63 | Giant +1.8 |

### XD-Violence (AP, seed=42)

| Variant | CLIP | SigLIP2 | SO400M | Giant | Best |
|---------|------|---------|--------|-------|------|
| Visual Only | 70.53 | 72.12 | 77.64 | 76.28 | SO400M |
| Late Fusion | 65.48 | 65.56 | 66.42 | 66.62 | Giant +1.1 |
| Gated Fusion | 71.92 | 71.92 | 73.77 | 72.80 | SO400M |
| GF 2-Person | 71.02 | 73.08 | 74.81 | 72.67 | SO400M |
| GF Mean-Only | 69.60 | 72.45 | 72.47 | 73.85 | Giant +4.2 |

### Seed Stability (Gated Fusion, 3 seeds)

| Dataset | Metric | CLIP | SigLIP2 | SO400M | Giant |
|---------|--------|------|---------|--------|-------|
| UCF | AUC mean | 81.98 | 79.76 | 81.90 | 83.28 |
| XD | AP mean | 70.97 | 74.70 | 73.81 | 73.76 |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- scripts/generate_phase10_charts.py: FOUND
- results/phase10_charts/backbone_comparison_4way.csv: FOUND
- results/phase10_charts/seed_stability_4way.csv: FOUND
- results/phase10_charts/comparison_auc_4way.png: FOUND
- results/phase10_charts/comparison_ap_4way.png: FOUND
- results/phase10_charts/seed_stability_4way.png: FOUND
- Commit 416067b: FOUND
- Commit c59f0e8: FOUND
