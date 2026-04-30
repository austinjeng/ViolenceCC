---
phase: 07-xd-violence-hyperparameter-sweep
plan: 02
subsystem: training
tags: [sweep-queue, rtfm-diagnostic, heatmap, chart-generation, results-visualization]

# Dependency graph
requires:
  - phase: 07-xd-violence-hyperparameter-sweep
    plan: 01
    provides: "RunSpec lr_override/k_topk_override fields, _fmt_lr() D-11 naming"
provides:
  - "phase7_sweep queue with 20 RunSpec entries (5 lr x 4 k_topk at seed=42)"
  - "RTFM gap diagnostic script with 4 investigation diagnostics"
  - "Sweep heatmap and summary table chart generation script"
affects: [07-03, 07-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sweep queue: list comprehension over _LR_SWEEP x _K_SWEEP constants"
    - "LR parser roundtrip: _fmt_lr() -> _parse_lr_from_name() is lossless for all 5 grid values"
    - "Diagnostic script pattern: each diagnostic returns dict with status/finding/detail"
    - "Chart script follows generate_phase4_charts.py seaborn heatmap pattern"

key-files:
  created:
    - "scripts/rtfm_gap_diagnostic.py"
    - "scripts/generate_phase7_charts.py"
  modified:
    - "scripts/run_ablations.py"
    - "tests/test_run_ablations.py"

key-decisions:
  - "RTFM 12.11pp AP gap attributed to training regime differences (10x LR, 2x features, loss scaling) not evaluation bugs"
  - "Sweep queue uses seed=42 only; confirmation seeds added in Plan 04 after winner identified"

patterns-established:
  - "Diagnostic script pattern: standalone scripts/[name]_diagnostic.py with JSON output to results/"
  - "Chart script pattern: scripts/generate_phase[N]_charts.py with S01/S02/S03 numbered outputs"

requirements-completed: [EVAL-02]

# Metrics
duration: 7min
completed: 2026-05-01
---

# Phase 7 Plan 02: Sweep Queue + RTFM Diagnostic + Chart Script Summary

**Defined 20-run phase7_sweep queue, created RTFM gap diagnostic with 4 investigations attributing 12.11pp gap to regime differences, and built heatmap/table chart generator with LR parser roundtrip**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-30T23:00:54Z
- **Completed:** 2026-04-30T23:07:32Z
- **Tasks:** 2
- **Files created:** 2
- **Files modified:** 2

## Accomplishments
- phase7_sweep queue added to QUEUES dict with 20 RunSpec entries covering all 5 lr x 4 k_topk combinations at seed=42
- scripts/rtfm_gap_diagnostic.py implements 4 diagnostics: annotation alignment, temporal interpolation, I3D feature audit, published code comparison
- RTFM diagnostic conclusion: 12.11pp AP gap is training regime difference (10x LR, 2x features, loss scaling), not evaluation bug
- scripts/generate_phase7_charts.py produces S01 heatmap, S02 summary table, S03 confirmation comparison
- _parse_lr_from_name() correctly reverses _fmt_lr() for all 5 grid LR values
- test_phase7_sweep_queue verifies queue size (20), uniqueness, naming, and field correctness
- All 16 tests pass including updated test_queue_definitions (38 total unique run_names)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add phase7_sweep queue + RTFM diagnostic script** - `4ccb56a` (feat)
2. **Task 2: Create sweep heatmap + summary table chart script** - `4b67011` (feat)

## Files Created/Modified
- `scripts/run_ablations.py` - Added _LR_SWEEP, _K_SWEEP constants and QUEUES["phase7_sweep"] with 20 entries; updated main() description
- `scripts/rtfm_gap_diagnostic.py` - New: 4 diagnostics (annotation alignment, temporal interpolation, I3D feature audit, published code comparison) with JSON output
- `scripts/generate_phase7_charts.py` - New: S01 heatmap, S02 summary table, S03 confirmation comparison; _parse_lr_from_name/_parse_k_from_name parsers
- `tests/test_run_ablations.py` - Added test_phase7_sweep_queue; updated test_queue_definitions (38 unique names) and test_help_has_expected_queues

## Decisions Made
- RTFM gap attributed to training regime, not evaluation bugs: 3 HIGH-impact differences (LR 10x, features 2x, margin 100x) explain the 12.11pp gap
- phase7_sweep queue uses seed=42 only; phase7_confirm queue with seeds {42, 123, 2024} deferred to Plan 04 per D-12

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- phase7_sweep queue (20 runs) is ready for empirical execution in Plan 03
- RTFM diagnostic results documented at results/phase7_rtfm_gap_diagnostic.json
- Chart generation script ready to produce visualizations once sweep results are in results-index.csv
- All infrastructure for the 5x4 hyperparameter sweep is now complete

---
## Self-Check: PASSED

All 4 files verified. Both commit hashes confirmed in git log.

---
*Phase: 07-xd-violence-hyperparameter-sweep*
*Completed: 2026-05-01*
