---
phase: 07-xd-violence-hyperparameter-sweep
plan: 01
subsystem: training
tags: [argparse, cli-overrides, run-ablations, hyperparameter-sweep, dataclass]

# Dependency graph
requires:
  - phase: 04c-xd-violence-main-results
    provides: "gated_fusion_xd.yaml config, run_ablations.py orchestration, RunSpec dataclass"
provides:
  - "--lr and --k-topk CLI override flags in train.py"
  - "RunSpec lr_override/k_topk_override fields with D-11 naming"
  - "run_one() CLI override forwarding to subprocess"
affects: [07-02, 07-03, 07-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CLI override pattern: argparse flags override YAML config keys via apply_cli_overrides()"
    - "D-11 run_name encoding: lr floats compressed to {coeff}e{exp} (e.g., 5e-05 -> 5e5)"
    - "RunSpec override forwarding: optional fields extend subprocess train_cmd when non-None"

key-files:
  created: []
  modified:
    - "src/train.py"
    - "scripts/run_ablations.py"
    - "tests/test_train.py"
    - "tests/test_run_ablations.py"

key-decisions:
  - "LR format uses split('e') + abs(int(exp)) instead of string replace/lstrip to avoid leading-zero bugs in exponent"

patterns-established:
  - "CLI override forwarding: RunSpec optional fields -> run_one() train_cmd.extend() -> train.py argparse"

requirements-completed: [EVAL-02]

# Metrics
duration: 4min
completed: 2026-05-01
---

# Phase 7 Plan 01: CLI Override Infrastructure Summary

**Added --lr and --k-topk argparse overrides to train.py with RunSpec extension and subprocess forwarding in run_ablations.py for the 20-run sweep grid**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-30T22:51:21Z
- **Completed:** 2026-04-30T22:56:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- train.py parse_args() accepts --lr (float) and --k-topk (int) flags that override YAML config values via apply_cli_overrides()
- RunSpec dataclass extended with lr_override and k_topk_override optional fields, producing D-11 naming (e.g., xd_gated_fusion_lr5e5_k1_s42)
- run_one() forwards overrides as --lr/--k-topk subprocess args when non-None
- 5 new pytest tests verify end-to-end override behavior; all 20 existing + new tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add --lr and --k-topk CLI overrides to train.py** - `41d5b80` (feat)
2. **Task 2: Extend RunSpec with override fields and run_one forwarding** - `6d3d971` (feat)

## Files Created/Modified
- `src/train.py` - Added --lr/--k-topk argparse flags + apply_cli_overrides extension for cfg["train"] keys
- `scripts/run_ablations.py` - Extended RunSpec with lr_override/k_topk_override fields, _fmt_lr() helper, D-11 run_name, run_one() forwarding
- `tests/test_train.py` - Added test_cli_lr_override and test_cli_k_topk_override
- `tests/test_run_ablations.py` - Added test_phase7_run_name, test_phase7_run_name_no_override, test_phase7_cli_overrides_in_train_cmd

## Decisions Made
- Used split('e') + abs(int(exp)) in _fmt_lr() instead of the plan's string replace/lstrip approach, which produced '5e05' instead of '5e5' for 5e-05 (auto-fixed during Task 2 verification)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _fmt_lr() exponent formatting**
- **Found during:** Task 2 (RunSpec extension)
- **Issue:** Plan's lstrip("0") approach produced '5e05' for 5e-05 because lstrip only strips leading characters, not interior zeros after 'e'
- **Fix:** Replaced with split('e') + abs(int(exp)) to properly strip exponent sign and leading zeros
- **Files modified:** scripts/run_ablations.py
- **Verification:** test_phase7_run_name passes with expected "5e5", "1e4", "3e4" outputs
- **Committed in:** 6d3d971 (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Minor formatting fix necessary for D-11 naming correctness. No scope creep.

## Issues Encountered
None beyond the _fmt_lr deviation documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CLI override plumbing is complete; Plan 02 can define the phase7_sweep queue with 20 RunSpec entries using lr_override and k_topk_override
- All existing queues and behavior unchanged (backward compatible)
- Existing test_queue_definitions still passes (18 unique run_names count unaffected)

---
## Self-Check: PASSED

All 5 files exist. Both commit hashes verified in git log.

---
*Phase: 07-xd-violence-hyperparameter-sweep*
*Completed: 2026-05-01*
