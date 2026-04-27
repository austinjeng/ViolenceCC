---
phase: 05-tta-infrastructure-corruption-experiments
plan: 04
subsystem: tta
tags: [tent, sar, tta-evaluation, per-video-adaptation, binary-entropy, corruption-features, frame-level-auc]

# Dependency graph
requires:
  - phase: 05-tta-infrastructure-corruption-experiments
    provides: TENT/SAR TTA modules (tent.py, sar.py, sam.py) from Plan 02
  - phase: 03-model-architecture-training-infrastructure
    provides: GatedFusion model, build_model registry, MIL training pipeline
  - phase: 04-evaluation-baseline-main-results
    provides: snippet_to_frame, compute_frame_metrics, ucf_annotations, atomic write helpers
provides:
  - Per-run TTA evaluation entry point (run_tta_evaluation)
  - Corruption-aware feature loading bypassing test_loader.py (Pitfall 5)
  - M7-compliant skeleton routing (clean vs re-extracted per corruption type)
  - _SourceOnlyAdaptor for safe no-optimizer baseline evaluation
  - 7 integration tests covering all TTA methods and protocol requirements
affects: [05-05, phase-6-analysis]

# Tech tracking
tech-stack:
  added: []
  patterns: [corruption-aware feature loading, per-video TTA adaptation loop, source_only baseline adaptor]

key-files:
  created:
    - src/tta/evaluate_tta.py
    - tests/test_evaluate_tta.py
  modified: []

key-decisions:
  - "_SourceOnlyAdaptor wrapper instead of passing None optimizer to TentAdaptor (TentAdaptor.reset crashes on None optimizer)"
  - "Feature root configurable via --feature-root CLI arg (default E:/features/ucf) for test fixture flexibility"

patterns-established:
  - "TTA evaluation pattern: load source checkpoint -> configure_model -> create adaptor -> per-video loop (reset + batch adapt) -> frame expand -> compute metrics -> atomic write"
  - "Corruption feature loading: bypass test_loader.py entirely, load directly from corruption cache dirs per M7 routing rules"

requirements-completed: [TTA-06, TTA-07]

# Metrics
duration: 5min
completed: 2026-04-28
---

# Phase 5 Plan 04: TTA Evaluation Entry Point Summary

**Per-run TTA evaluation loop with per-video adaptation, M7 skeleton routing, and 32-snippet batch protocol wiring TENT/SAR modules into a complete adaptation-evaluation pipeline**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-27T20:45:55Z
- **Completed:** 2026-04-27T20:50:56Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created evaluate_tta.py entry point that loads source checkpoint, configures model for TTA (LN-only unfreezing), and runs per-video adaptation with 32-snippet batches
- Implemented corruption-aware feature loading that bypasses test_loader.py (Pitfall 5 / C3 guard) and routes skeleton features per M7 rules (gaussian_noise/brightness use clean cache)
- Created _SourceOnlyAdaptor for safe baseline evaluation without optimizer crash risk
- All 7 integration tests pass covering source_only/tent/sar output format, M7 routing, per-video reset, argument validation, and 1536 adapted params count

## Task Commits

Each task was committed atomically:

1. **Task 1: Create src/tta/evaluate_tta.py** - `5b8c163` (feat)
2. **Task 2: Create tests/test_evaluate_tta.py** - `6f24862` (test)

## Files Created/Modified
- `src/tta/evaluate_tta.py` - Per-run TTA evaluation entry point with run_tta_evaluation(), parse_args(), _load_test_video_features(), _adapt_one_video(), _SourceOnlyAdaptor
- `tests/test_evaluate_tta.py` - 7 integration tests: source_only/tent/sar output, M7 routing, per-video reset, arg validation, n_adapted_params

## Decisions Made
- Created _SourceOnlyAdaptor wrapper class instead of passing None as optimizer to TentAdaptor, because TentAdaptor.reset() calls self.optimizer.state = {} which crashes on None (Rule 1 bug prevention)
- Made feature_root configurable via both function parameter and CLI --feature-root arg (default E:/features/ucf) to enable test fixture injection via monkeypatch

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] _SourceOnlyAdaptor for safe source_only evaluation**
- **Found during:** Task 1 (evaluate_tta.py implementation)
- **Issue:** Plan suggested `TentAdaptor(model, None, source_state)` for source_only, but TentAdaptor.reset() calls `self.optimizer.state = {}` which raises AttributeError when optimizer is None
- **Fix:** Created _SourceOnlyAdaptor class with safe no-op reset and score_only delegation
- **Files modified:** src/tta/evaluate_tta.py
- **Verification:** test_run_tta_source_only_produces_outputs passes
- **Committed in:** 5b8c163 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug)
**Impact on plan:** Fix necessary to prevent runtime crash on source_only evaluation. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- TTA evaluation pipeline ready for Plan 05 (queue orchestrator / run_ablations.py)
- run_tta_evaluation() callable as subprocess for each TTA RunSpec
- All 3 methods (source_only, tent, sar) produce standardized output: eval_metrics.json + eval_scores.npz + .done marker
- 1536 LN adapted params verified in output for GatedFusion model

## Self-Check: PASSED

All created files verified on disk:
- src/tta/evaluate_tta.py: FOUND
- tests/test_evaluate_tta.py: FOUND

Both task commits verified in git log:
- 5b8c163: FOUND
- 6f24862: FOUND

---
*Phase: 05-tta-infrastructure-corruption-experiments*
*Completed: 2026-04-28*
