---
phase: 05-tta-infrastructure-corruption-experiments
plan: 02
subsystem: tta
tags: [tent, sar, sam, layernorm, binary-entropy, test-time-adaptation, pytorch]

# Dependency graph
requires:
  - phase: 03-model-architecture-training-infrastructure
    provides: GatedFusion model with 3 named LayerNorms (ln_skel, ln_clip, ln_fused)
provides:
  - TENT-style TTA adaptor with LN targeting and binary entropy
  - SAR-style TTA adaptor with SAM optimizer and entropy filtering
  - SAM sharpness-aware optimizer (first_step/second_step)
  - Per-video episodic reset mechanism for both adaptors
  - 14 unit tests covering TTA-04, TTA-05, TTA-07
affects: [05-03, 05-04, 05-05, phase-6-analysis]

# Tech tracking
tech-stack:
  added: []
  patterns: [LN-only TTA adaptation, binary entropy loss, SAM two-step optimization, per-video episodic reset]

key-files:
  created:
    - src/tta/tent.py
    - src/tta/sar.py
    - src/tta/sam.py
    - tests/test_tent.py
    - tests/test_sar.py
  modified:
    - src/tta/__init__.py

key-decisions:
  - "High LR (0.1) + multiple steps in tests to ensure visible LN param drift on random data"
  - "SAR entropy margin default 0.4*ln(2) ~= 0.277, proportionally scaled from ImageNet 1000-class calibration"

patterns-established:
  - "TTA module pattern: configure_model() freezes all except LN affine, collect_params() returns exactly the adaptable params"
  - "Per-video lifecycle: reset() -> adapt_and_score() per batch -> collect scores"
  - "Dropout eval guard: model.dropout.eval() after model.train() prevents stochastic masking during TTA"

requirements-completed: [TTA-04, TTA-05, TTA-07]

# Metrics
duration: 6min
completed: 2026-04-28
---

# Phase 5 Plan 02: TENT/SAR TTA Modules Summary

**TENT and SAR entropy-minimization TTA modules ported from SAR repo (MIT), adapted for LayerNorm targeting and binary entropy with 14 unit tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-27T20:35:01Z
- **Completed:** 2026-04-27T20:41:07Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Implemented TENT-style TTA (tent.py) with binary entropy, LN-only param collection, configure_model with dropout eval guard, and per-video episodic reset
- Implemented SAR-style TTA (sar.py) extending TENT with SAM two-step optimizer and reliable entropy filtering (margin_e0 threshold)
- Implemented SAM optimizer (sam.py) with first_step ascent and second_step descent
- Created 14 unit tests (8 TENT + 6 SAR) covering all acceptance criteria: param collection (6 tensors / 1536 params), freeze verification, dropout eval, binary entropy values, adapt+reset lifecycle, SAM mechanics, D-11 rho grid, and 32-snippet protocol

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TTA modules (sam.py, tent.py, sar.py, __init__.py)** - `0da51e7` (feat)
2. **Task 2: Create test suites (test_tent.py, test_sar.py)** - `deb9a9b` (test)

## Files Created/Modified
- `src/tta/sam.py` - SAM optimizer with first_step/second_step, ported from SAR repo
- `src/tta/tent.py` - binary_entropy, configure_model, collect_params, TentAdaptor
- `src/tta/sar.py` - SarAdaptor with entropy filtering + SAM integration + EMA tracking
- `src/tta/__init__.py` - Public API exports replacing placeholder
- `tests/test_tent.py` - 8 unit tests for TENT adaptation (TTA-04, TTA-07)
- `tests/test_sar.py` - 6 unit tests for SAR adaptation (TTA-05)

## Decisions Made
- Used lr=0.1 + 5 adaptation steps in tests (instead of plan's lr=1e-3) because LN gradient magnitude on random data at low LR produces sub-tolerance parameter drift with torch.allclose defaults
- SAR entropy filtering margin defaults to 0.4 * ln(2) as proportional scaling from SAR's ImageNet 1000-class calibration to binary entropy domain

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed MILHead attribute name in test**
- **Found during:** Task 2 (test_tent.py)
- **Issue:** Plan referenced `gated_model.head.layers[0]` but MILHead uses `self.mlp` (nn.Sequential), not `self.layers`
- **Fix:** Changed to `gated_model.head.mlp[0].weight.requires_grad`
- **Files modified:** tests/test_tent.py
- **Verification:** Test passes, correctly verifies head is frozen
- **Committed in:** deb9a9b (Task 2 commit)

**2. [Rule 1 - Bug] Increased test LR to make param drift measurable**
- **Found during:** Task 2 (test_tent.py, test_sar.py)
- **Issue:** lr=1e-3 with random input produces gradient updates smaller than allclose default tolerance (1e-8), making adapt-then-check-change assertions fail
- **Fix:** Used lr=0.1 + 5 adaptation steps in adapt/reset tests; verifies the mechanism works without relying on specific gradient magnitude
- **Files modified:** tests/test_tent.py, tests/test_sar.py
- **Verification:** All 14 tests pass; param change is now measurable
- **Committed in:** deb9a9b (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs in tests)
**Impact on plan:** Both fixes necessary for test correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed test issues documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- TTA modules ready for Plan 03 (corruption module) and Plan 04 (TTA evaluation loop)
- collect_params verified to return exactly 6 tensors / 1536 params from GatedFusion
- SAM optimizer accepts all D-11 rho grid values {0.001, 0.005, 0.01, 0.05, 0.1}
- Per-video reset verified: params return to exact source state after reset()

## Self-Check: PASSED

All 6 created files exist on disk. Both task commits (0da51e7, deb9a9b) verified in git log. SUMMARY.md present.

---
*Phase: 05-tta-infrastructure-corruption-experiments*
*Completed: 2026-04-28*
