---
phase: 05-tta-infrastructure-corruption-experiments
plan: 01
subsystem: corruption
tags: [imagenet-c, numpy, cv2, corruption-transforms, ucf-crime-c]

# Dependency graph
requires:
  - phase: 04-baseline-evaluation-main-results
    provides: "UCF-Crime evaluation infrastructure (scripts/, test fixtures)"
provides:
  - "scripts/corruption.py: 4 corruption transforms + dispatcher using numpy+cv2 only"
  - "tests/test_corruption.py: 9 unit tests covering all 20 conditions, monotonicity, M7, D-03"
  - "CORRUPTION_TYPES and SKELETON_REEXTRACT_TYPES constants for downstream plans"
affects: [05-02 (CLIP re-extraction), 05-03 (skeleton re-extraction), 05-04 (TTA evaluation)]

# Tech tracking
tech-stack:
  added: [opencv-python in vcc-main]
  patterns: [numpy+cv2 corruption transforms, ImageNet-C severity conventions]

key-files:
  created:
    - scripts/corruption.py
    - tests/test_corruption.py
  modified: []

key-decisions:
  - "Used numpy+cv2 exclusively (not PIL/scipy) per D-03 correction for cross-env compatibility"
  - "Used Gaussian-weighted motion blur kernel (not uniform) to differentiate severity 2 vs 3 (same kernel_size=15, different sigma)"
  - "Installed opencv-python in vcc-main for universal cv2 availability across all envs"

patterns-established:
  - "Corruption function signature: fn(img: uint8 ndarray, severity: int, rng: Generator) -> uint8 ndarray"
  - "apply_corruption dispatcher with full input validation (type, severity, dtype, ndim)"

requirements-completed: [TTA-01, TTA-03]

# Metrics
duration: 3min
completed: 2026-04-28
---

# Phase 5 Plan 01: Corruption Transform Module Summary

**4 ImageNet-C corruption transforms (gaussian_noise, jpeg_compression, brightness, motion_blur) using numpy+cv2 only, with 9-test coverage for all 20 conditions**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-27T20:34:54Z
- **Completed:** 2026-04-27T20:38:10Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created corruption transform module with 4 types matching ImageNet-C verified severity parameters
- All 20 conditions (4 types x 5 severities) produce valid uint8 output with monotonically increasing degradation
- Full test coverage: 9 tests covering correctness, monotonicity, reproducibility, M7 skeleton re-extraction decision, input validation, and D-03 PIL-free confirmation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create scripts/corruption.py** - `54fd45c` (feat)
2. **Task 2: Create tests/test_corruption.py + fix motion blur** - `d6eda4d` (test)

## Files Created/Modified
- `scripts/corruption.py` - 4 corruption functions + apply_corruption dispatcher, CORRUPTION_TYPES and SKELETON_REEXTRACT_TYPES constants
- `tests/test_corruption.py` - 9 pytest test functions covering TTA-01 and TTA-03

## Decisions Made
- **numpy+cv2 only (D-03 correction):** RESEARCH.md identified that PIL and scipy are absent from vcc-skeleton. Used cv2.imencode/imdecode for JPEG compression and cv2.filter2D for motion blur instead. Installed opencv-python in vcc-main (lightweight, no conflicts) for universal availability.
- **Gaussian-weighted motion blur kernel:** Plan specified uniform horizontal line kernel (A1), but severities 2 and 3 both use kernel_size=15 with different sigma values (5 vs 8). Uniform kernel ignoring sigma produced identical outputs. Used Gaussian-weighted profile to leverage the sigma parameter, ensuring all 5 severity levels produce distinct distortion.
- **Deterministic default RNG:** apply_corruption creates `np.random.default_rng(42)` when no rng is provided, ensuring reproducibility per CONTEXT.md specifics.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Motion blur severity 2 and 3 producing identical output**
- **Found during:** Task 2 (test_motion_blur_severity_monotonic)
- **Issue:** MOTION_BLUR_PARAMS severities 2 and 3 both have kernel_size=15 (sigma differs: 5 vs 8). Plan specified ignoring sigma (A1 assumption), producing identical kernels and thus identical MSE for those two severities.
- **Fix:** Changed motion_blur to use a Gaussian-weighted horizontal kernel profile with the sigma parameter, so all 5 severity levels produce monotonically increasing distortion.
- **Files modified:** scripts/corruption.py
- **Verification:** test_motion_blur_severity_monotonic now passes with strictly increasing MSE across all 5 levels
- **Committed in:** d6eda4d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential for correctness -- identical corruption at two different severity levels would produce meaningless experimental comparison. No scope creep.

## Issues Encountered
- cv2 not available in vcc-main by default. Resolved by installing opencv-python (lightweight pip install, no conflicts with existing packages).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `scripts/corruption.py` ready for import by `extract_clip.py` (Plan 05-02) and `extract_skeletons.py` (Plan 05-03)
- `SKELETON_REEXTRACT_TYPES` constant available for M7 re-extraction decision logic
- All exports documented: gaussian_noise, jpeg_compression, brightness, motion_blur, apply_corruption, CORRUPTION_TYPES, SKELETON_REEXTRACT_TYPES

---
*Phase: 05-tta-infrastructure-corruption-experiments*
*Completed: 2026-04-28*
