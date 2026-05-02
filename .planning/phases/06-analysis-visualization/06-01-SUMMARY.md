---
phase: "06-analysis-visualization"
plan: "01"
subsystem: "visualization"
tags: [charts, temporal-curves, corruption-heatmap, thesis-figures, seaborn]
dependency_graph:
  requires:
    - "results/*/eval_scores.npz (8 files: 4 variants x 2 datasets)"
    - "results/tta/*/eval_metrics.json (500 TTA result directories)"
    - "results/results-index.csv (experiment results index)"
    - "src/eval/ucf_annotations.py (GT annotation parser)"
    - "src/eval/xd_annotations.py (XD GT annotation parser)"
  provides:
    - "scripts/generate_phase6_charts.py (802 lines, Sections A+C+F)"
    - "results/phase6_charts/A_temporal/ (5 temporal curve PNGs)"
    - "results/phase6_charts/C_corruption/ (6 corruption heatmap PNGs)"
    - "results/phase6_charts/F_additional/ (6 additional thesis figure PNGs)"
  affects:
    - "Plan 06-02 will extend this script with GPU-dependent sections (B, D, E)"
tech_stack:
  added: []
  patterns:
    - "Phase 4 chart style (DPI=150, whitegrid, VCOLORS/VLABELS)"
    - "Section-prefixed output structure (A_temporal, C_corruption, F_additional)"
    - "eval_scores.npz direct frame-level score loading (no snippet_to_frame)"
key_files:
  created:
    - "scripts/generate_phase6_charts.py"
  modified: []
decisions:
  - "Video selection by score-GT separation heuristic with category diversity greedy selection"
  - "Filter results-index.csv by exact run_name to exclude Phase 7 sweep runs"
  - "XD category codes mapped to readable names (B1=Fighting, B2=Shooting, etc.)"
metrics:
  duration: "486s (~8 min)"
  completed: "2026-05-02"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 0
  pngs_generated: 17
---

# Phase 6 Plan 01: Offline Visualization (Temporal + Corruption + Additional) Summary

Phase 6 chart generation script with 802 lines producing 17 thesis-quality PNGs across 3 sections (A temporal curves, C corruption heatmaps, F additional figures), using pre-computed eval_scores.npz and TTA eval_metrics.json with Phase 4 seaborn whitegrid style.

## What Was Built

### Section A: Temporal Anomaly Score Curves (5 PNGs)
- **Video selection:** Programmatic selection by Gated Fusion score-GT separation heuristic with category diversity
- **UCF-Crime:** Shooting008 (Shooting), Arrest007 (Arrest), Shooting032 (Shooting) -- 3 videos
- **XD-Violence:** Salt.2010 (B1/Fighting), Tropa.de.Elite.2.2010 (B2/Shooting) -- 2 videos
- Each plot: 4-variant overlay (Skeleton/CLIP/Late/Gated) with red GT shading bands via axvspan
- Frame-level scores loaded directly from eval_scores.npz (no snippet_to_frame)

### Section C: Corruption Severity Heatmaps (6 PNGs)
- C01-C03: Absolute AUC heatmaps (corruption_type x severity) for Source-Only, Best-TENT, Best-SAR
- C04-C05: Delta heatmaps (RdBu_r diverging colormap, center=0) showing TENT/SAR improvement over Source-Only
- C06: Grouped bar chart comparing mean AUC across all 20 corruption conditions
- Data from 500 TTA directories (20 source_only + 80 tent + 400 SAR), best-AUC config per condition

### Section F: Additional Thesis Figures (6 PNGs)
- F01: Cross-dataset comparison (UCF AUC vs XD AP side-by-side for 4 variants)
- F02: UCF per-category score distributions (box plot, normal vs anomalous frames, 13 categories)
- F03: XD per-category score distributions (box plot, 6 violence categories with readable names)
- F04: 3-seed stability (s42/s123/s2024 mean+std error bars for both datasets)
- F05-F06: Ablation horizontal bar charts (UCF AUC + XD AP, including cache variants)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | b575650 | Script skeleton + Section A temporal curves with video selection |
| 2 | dbb7f90 | Section C corruption heatmaps + Section F additional thesis figures |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] UCF scores not loading due to dict key collision**
- **Found during:** Task 1
- **Issue:** `load_all_scores()` used `all_runs.update(UCF_RUNS)` then `all_runs.update(XD_RUNS)` -- same variant keys caused XD to overwrite UCF entries
- **Fix:** Iterate both dicts separately in nested loop
- **Files modified:** scripts/generate_phase6_charts.py
- **Commit:** b575650

**2. [Rule 1 - Bug] RuntimeWarning on videos with all anomalous frames**
- **Found during:** Task 1
- **Issue:** Some XD videos have no normal frames, causing `scores[labels == 0].mean()` to produce NaN
- **Fix:** Added `len(norm_scores) == 0` guard to skip such videos in selection
- **Files modified:** scripts/generate_phase6_charts.py
- **Commit:** b575650

**3. [Rule 1 - Bug] Phase 7 sweep runs polluting main variant queries**
- **Found during:** Task 2
- **Issue:** results-index.csv contains 100+ gated_fusion rows from Phase 7 sweep runs that matched the (variant, seed, cache_variant) filter, causing `set_index("variant")` to return Series instead of scalar
- **Fix:** Changed F01, F04, F05 to filter by exact `run_name` instead of (variant, seed, cache_variant)
- **Files modified:** scripts/generate_phase6_charts.py
- **Commit:** dbb7f90

## Verification

- Script runs to completion with exit code 0
- 17 PNG files generated (5 + 6 + 6), all > 10KB
- No `snippet_to_frame` function calls in script (only in comments)
- DPI=150 and seaborn whitegrid style applied consistently
- All VCOLORS hex codes match D-04 specification

## Self-Check: PASSED

- scripts/generate_phase6_charts.py: FOUND
- 06-01-SUMMARY.md: FOUND
- Commit b575650: FOUND
- Commit dbb7f90: FOUND
- PNG count: 17 (>= 14 required)
