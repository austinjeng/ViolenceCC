---
phase: "11"
plan: "01"
subsystem: tta-backbone
tags: [tta, backbone, siglip2, infrastructure]
dependency_graph:
  requires: []
  provides: [tta-backbone-parameterization, analyze-tta-best]
  affects: [evaluate_tta, run_ablations]
tech_stack:
  added: []
  patterns: [backbone-parameterized-tta, auto-resolved-source-runs]
key_files:
  created:
    - scripts/analyze_tta_best.py
  modified:
    - src/tta/evaluate_tta.py
    - scripts/run_ablations.py
decisions:
  - "Route non-CLIP backbone TTA results to results/tta_backbone/ to preserve existing 500 CLIP runs in results/tta/"
  - "Use __post_init__ in TTARunSpec to auto-resolve source_run from backbone key"
  - "Best CLIP TTA configs: SAR lr=1e-4 rho=0.01 (AUC 0.6202), TENT lr=5e-3 (AUC 0.6158), source_only (AUC 0.6145)"
metrics:
  duration_seconds: 491
  completed_date: "2026-05-30"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 11 Plan 01: TTA Backbone Experiments Summary

Backbone-parameterized TTA evaluation infrastructure with CLIP best-config analyzer, enabling TTA experiments across all 4 vision backbones.

## Task 1: Backbone-parameterize evaluate_tta.py and create TTA best-config analyzer [COMPLETE]

### Changes Made

**src/tta/evaluate_tta.py:**
- Added `BACKBONE_FEATURE_PREFIX` dict mapping 4 backbone keys to feature subdirectory prefixes (clip, siglip2, siglip2_so400m, siglip2_giant)
- Added `BACKBONE_SOURCE_RUNS` dict mapping 4 backbone keys to s42 gated fusion run directories
- Added `BACKBONE_CHOICES` list for argparse validation
- Added `--backbone` argument to `parse_args()` with 4 choices and default `clip-vit-b-16`
- Modified `_load_test_video_features()` to accept `backbone` parameter and use `BACKBONE_FEATURE_PREFIX` for feature directory routing instead of hardcoded `clip_` prefix
- Threaded `backbone` parameter through `run_tta_evaluation()` to `_load_test_video_features()` and CLI `main()`
- Added `backbone` field to `eval_metrics.json` payload

**scripts/run_ablations.py:**
- Added `backbone` field to `TTARunSpec` dataclass (default: `"clip-vit-b-16"`)
- Added `__post_init__` to auto-resolve `source_run` from backbone if not explicitly set
- Updated `run_name` property to prefix non-CLIP backbone names (e.g., `siglip2_giant_tent_brightness_3_lr0.001`)
- Added `--backbone` flag to subprocess command in `run_one_tta()`
- Added `backbone` field to results-index CSV row
- Added `_tta_subdir()` helper to route non-CLIP results to `tta_backbone/` directory
- Added 3 new TTA queues: `tta_backbone_source` (60 runs), `tta_backbone_tent` (60 runs), `tta_backbone_sar` (60 runs)

**scripts/analyze_tta_best.py (new):**
- Reads all `results/tta/*/eval_metrics.json` files
- Groups by (method, lr, rho) and computes mean AUC across all 20 conditions
- Outputs winning configs to stdout and `results/tta/best_configs.json`
- When invoked with `--all-backbones`, also scans `results/tta_backbone/` and writes `results/tta_backbone/summary.csv`

### Verification Results

- `BACKBONE_FEATURE_PREFIX` has 4 entries: PASSED
- `BACKBONE_SOURCE_RUNS` has 4 entries: PASSED
- `parse_args` accepts `--backbone` with 4 choices: PASSED
- `_load_test_video_features` accepts backbone parameter: PASSED
- `eval_metrics.json` payload includes backbone field: PASSED
- `TTARunSpec` has backbone field with auto-resolved source_run: PASSED
- `analyze_tta_best.py` produces `best_configs.json` from 500 CLIP runs: PASSED

### Best CLIP TTA Configs (from 500 runs)

| Method | LR | Rho | Mean AUC | Conditions |
|--------|-----|------|----------|------------|
| SAR | 1e-4 | 0.01 | 0.6202 | 20 |
| TENT | 5e-3 | - | 0.6158 | 20 |
| source_only | - | - | 0.6145 | 20 |

## Task 2: Run TTA Backbone Experiments [COMPLETE]

All GPU jobs completed successfully (458.9 min total):
- 60/60 corrupted feature extractions succeeded (3 backbones x 4 corruptions x 5 severities)
- 3 TTA evaluation queues (source, tent, sar) completed
- Summary CSV generated at `results/tta_backbone/summary.csv`

### TTA Backbone Results

| Backbone | Source-Only AUC | TENT AUC | SAR AUC | Best Delta |
|----------|----------------|----------|---------|------------|
| CLIP ViT-B/16 | 0.6145 | 0.6158 | **0.6202** | +0.57% |
| SigLIP2 Base | 0.5680 | 0.5647 | 0.5655 | -0.25% |
| SigLIP2 SO400M | 0.5873 | 0.5844 | 0.5870 | -0.03% |
| SigLIP2 Giant | 0.6034 | 0.6031 | **0.6037** | +0.03% |

**Key finding:** LN-based TTA shows marginal improvement on CLIP only (+0.57% SAR). SigLIP2 variants show negligible or slightly negative effects. Confirms honest negative finding for the paper.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Added tta_backbone/ directory routing**
- **Found during:** Task 1, action 6
- **Issue:** Non-CLIP backbone TTA results would collide with existing 500 CLIP runs in `results/tta/` since run_name prefixing alone does not create a clean separation.
- **Fix:** Added `_tta_subdir()` helper that routes CLIP runs to `tta/` and non-CLIP runs to `tta_backbone/`. Updated both `run_one_tta()` and `run_queue_tta()`.
- **Files modified:** scripts/run_ablations.py
- **Commit:** d06f7fe

## Known Stubs

None -- all code paths are fully wired with real data sources.

## Self-Check: PASSED
