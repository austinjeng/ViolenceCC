---
phase: 09-siglip2-so400m-backbone-comparison
plan: 04
status: complete
started: "2026-05-21T07:07:09Z"
completed: "2026-05-21T07:09:57Z"
duration: "3min"
subsystem: analysis
tags: [charts, comparison, backbone, thesis]
dependency_graph:
  requires: [09-03]
  provides: [phase9-analysis-tables, phase9-comparison-charts]
  affects: [thesis-writing]
tech_stack:
  added: []
  patterns: [matplotlib-agg, seaborn-whitegrid, pandas-csv]
key_files:
  created:
    - scripts/generate_phase9_charts.py
  modified: []
decisions:
  - "Three grouped bars (width=0.25) for 3-way comparison; colors: #3B82F6 CLIP, #EF4444 SigLIP2, #10B981 SO400M"
  - "Delta columns show both CLIP-vs-SO400M and SigLIP2-vs-SO400M differences"
metrics:
  duration: "3min"
  completed: "2026-05-21"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_generated: 5
---

# Phase 9 Plan 04: Three-Way Backbone Comparison Analysis Summary

Three-way CLIP vs SigLIP2 ViT-B/16-256 vs SigLIP2 SO400M comparison script with 12-row comparison table, 6-row seed stability table, and 3 grouped bar charts for thesis inclusion.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create three-way comparison script | 92ee4e0 | scripts/generate_phase9_charts.py |
| 2 | Generate tables and charts | (gitignored outputs) | results/phase9_charts/*.csv, *.png |

## Key Outputs

### Comparison Table (backbone_comparison_3way.csv)
- 12 rows: 6 UCF variants + 6 XD variants
- 14 columns: Dataset, Variant, CLIP_AUC, CLIP_AP, SigLIP2_AUC, SigLIP2_AP, SO400M_AUC, SO400M_AP, plus 6 delta columns
- Skeleton Only rows have NaN for SigLIP2/SO400M (backbone-independent)

### Key Findings from Three-Way Comparison

**UCF-Crime (AUC):**
- Gated Fusion: CLIP 82.27% vs SigLIP2 79.61% vs SO400M 82.18% -- SO400M recovers nearly all CLIP performance
- GF Mean-Only: SO400M 82.45% beats both CLIP (81.78%) and SigLIP2 (80.00%)
- SO400M consistently outperforms SigLIP2 ViT-B/16 on UCF by +2-2.5pp AUC

**XD-Violence (AP):**
- SO400M Only: 77.64% AP, +7.12pp over CLIP (70.53%), +5.53pp over SigLIP2 (72.12%)
- Gated Fusion: SO400M 73.77% AP, +1.85pp over CLIP, +1.84pp over SigLIP2
- SO400M is the best backbone for XD-Violence across all variants

### Seed Stability (seed_stability_3way.csv)
- UCF Gated Fusion AUC: CLIP 81.98+/-0.30, SigLIP2 79.77+/-0.23, SO400M 81.90+/-0.38
- XD Gated Fusion AP: CLIP 71.00+/-1.08, SigLIP2 72.80+/-2.93, SO400M 73.81+/-2.81
- SO400M seed stability comparable to CLIP on UCF; higher variance on XD (similar to SigLIP2)

### Charts Generated
- comparison_auc_3way.png (163 KB) -- 10 grouped bars, 3 backbones each
- comparison_ap_3way.png (159 KB) -- 10 grouped bars, 3 backbones each
- seed_stability_3way.png (109 KB) -- UCF/XD panels with mean+std dashed lines

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- [x] scripts/generate_phase9_charts.py exists (committed)
- [x] Commit 92ee4e0 verified in git log
- [x] results/phase9_charts/ contains 5 output files (gitignored by design)
- [x] backbone_comparison_3way.csv has 12 rows, SO400M_AUC column present
- [x] seed_stability_3way.csv has 6 rows with SO400M columns
- [x] All 3 PNGs exceed 10 KB minimum
