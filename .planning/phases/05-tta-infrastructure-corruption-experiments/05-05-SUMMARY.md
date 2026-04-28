---
phase: 05-tta-infrastructure-corruption-experiments
plan: 05
subsystem: tta-queue-orchestrator
tags: [tta, run-ablations, queue-runner, tent, sar, source-only, corruption-grid]

# Dependency graph
requires:
  - phase: 05-tta-infrastructure-corruption-experiments
    plan: 03
    provides: "Corruption extraction flags for CLIP and skeleton scripts"
  - phase: 05-tta-infrastructure-corruption-experiments
    plan: 04
    provides: "evaluate_tta.py entry point with per-video TTA adaptation loop"
provides:
  - "TTARunSpec dataclass with D-13 deterministic run naming"
  - "3 TTA queues: tta_source_only (20), tta_tent_grid (80), tta_sar_grid (400)"
  - "run_one_tta + run_queue_tta with .done resume and results-index append"
  - "RESULTS_INDEX_COLUMNS extended with method/corruption_type/severity/lr/rho"
affects: [phase-6-analysis]

# Tech tracking
tech-stack:
  added: []
  patterns: [TTA queue orchestration via subprocess, TTARunSpec dataclass for grid parameterization]

key-files:
  created:
    - tests/test_run_ablations_tta.py
  modified:
    - scripts/run_ablations.py
    - src/utils/csv_logger.py

key-decisions:
  - "TTA queues skip wandb preflight (evaluation only, no training)"
  - "run_one_tta timeout set to 600s (10 min) vs 7200s for train+eval runs"
  - "TTA results stored under results/tta/{run_name}/ subdirectory (not flat in results/)"
  - "TTA_QUEUES dict is separate from QUEUES to keep Phase 4 and Phase 5 concerns distinct"

patterns-established:
  - "TTARunSpec.run_name follows D-13: {method}_{type}_{severity}_lr{lr}[_rho{rho}]"
  - "TTA queue dispatch: main() detects is_tta and routes to run_queue_tta"

requirements-completed: [TTA-06]

# Metrics
duration: 4min
completed: 2026-04-28
status: checkpoint-pending
---

# Phase 5 Plan 05: TTA Queue Orchestrator Summary

**TTARunSpec dataclass + 3 TTA queues (500 total runs) extending run_ablations.py with subprocess dispatch to evaluate_tta.py, .done resume semantics, and results-index.csv TTA column extension**

## Performance

- **Duration:** 4 min (Task 1 only; Task 2 is checkpoint:human-verify for ~5h grid)
- **Started:** 2026-04-28T21:57:30Z
- **Completed:** 2026-04-28T22:01:45Z (Task 1)
- **Tasks:** 1/2 (Task 2 is checkpoint:human-verify)
- **Files modified:** 3

## Accomplishments
- Added `TTARunSpec` dataclass with `run_name` property following D-13 naming convention
- Built 3 TTA queue definitions totaling 500 runs: tta_source_only (4x5=20), tta_tent_grid (4x5x4=80), tta_sar_grid (4x5x4x5=400)
- Added `run_one_tta` function that invokes `src/tta/evaluate_tta.py` as subprocess, reads eval_metrics.json, and appends TTA-enriched row to results-index.csv
- Added `run_queue_tta` function with .done marker resume and dry-run support
- Extended `RESULTS_INDEX_COLUMNS` with 5 TTA columns (method, corruption_type, severity, lr, rho) -- backward-compatible with Phase 4 rows
- Updated `main()` to merge TTA queue names into --queue choices and route TTA queues to `run_queue_tta` (skipping wandb preflight)
- Created 11 tests covering queue sizes, run naming, CLI choices, dry-run, skip-done, and total count

## Task Commits

Each task was committed atomically:

1. **Task 1: Add TTARunSpec + TTA queues + tests** - `740cc12` (feat)
2. **Task 2: Run TTA evaluation grid (~5-8h)** - CHECKPOINT (not executed)

## Checkpoint: Task 2

**Status:** Awaiting human-supervised TTA grid execution (~5-8h)

The ~500-run TTA evaluation grid must be run in a visible terminal. The user should execute these commands sequentially:

**Step 1: Dry-run to verify queue sizes:**
```bash
python scripts/run_ablations.py --queue tta_source_only --dry-run --no-preflight
python scripts/run_ablations.py --queue tta_tent_grid --dry-run --no-preflight
python scripts/run_ablations.py --queue tta_sar_grid --dry-run --no-preflight
```
Expected: 20 + 80 + 400 = 500 [dry-run] lines total.

**Step 2: Run Source-Only first (~10 min):**
```bash
python scripts/run_ablations.py --queue tta_source_only --no-preflight
```

**Step 3: Run TENT grid (~40 min):**
```bash
python scripts/run_ablations.py --queue tta_tent_grid --no-preflight
```

**Step 4: Run SAR grid (~3-5h):**
```bash
python scripts/run_ablations.py --queue tta_sar_grid --no-preflight
```

**Step 5: Verify results:**
```bash
python -c "
import csv
with open('results/results-index.csv') as f:
    rows = list(csv.DictReader(f))
tta = [r for r in rows if r.get('method')]
print(f'Total TTA rows: {len(tta)}')
print(f'Source-Only: {len([r for r in tta if r[\"method\"]==\"source_only\"])}')
print(f'TENT: {len([r for r in tta if r[\"method\"]==\"tent\"])}')
print(f'SAR: {len([r for r in tta if r[\"method\"]==\"sar\"])}')
"
```
Expected: 500 total TTA rows (20 + 80 + 400).

## Files Created/Modified
- `scripts/run_ablations.py` - Added TTARunSpec dataclass, TTA_QUEUES dict, run_one_tta, run_queue_tta, updated main() with TTA dispatch
- `src/utils/csv_logger.py` - Extended RESULTS_INDEX_COLUMNS with 5 TTA columns
- `tests/test_run_ablations_tta.py` - 11 tests for TTA queue definitions, naming, CLI, dry-run, skip-done

## Decisions Made
- TTA queues skip wandb preflight since they are evaluation-only (no training runs)
- TTA results stored under `results/tta/` subdirectory to separate from Phase 4 training results
- `run_one_tta` timeout set to 600s (10 min per run) vs 7200s for full train+eval runs
- `TTA_QUEUES` kept as separate dict from `QUEUES` for clean Phase 4/5 separation
- `log_error` reused for TTA error logging (both RunSpec and TTARunSpec have `.run_name`)

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all TTA queue infrastructure is fully wired to evaluate_tta.py from Plan 04.

## Self-Check: PASSED

- [x] scripts/run_ablations.py exists and contains TTARunSpec + TTA_QUEUES
- [x] src/utils/csv_logger.py exists and RESULTS_INDEX_COLUMNS has TTA fields
- [x] tests/test_run_ablations_tta.py exists with 11 tests
- [x] Commit 740cc12 found in git log
- [x] 11 tests pass, 12 existing tests still pass

---
*Phase: 05-tta-infrastructure-corruption-experiments*
*Completed: 2026-04-28 (Task 1 only; Task 2 checkpoint pending)*
