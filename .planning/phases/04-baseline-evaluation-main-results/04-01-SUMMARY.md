---
phase: 04-baseline-evaluation-main-results
plan: 01
subsystem: testing
tags: [ucf-crime, annotations, snippet-broadcast, c4-prevention, tdd, numpy, sklearn-prep, pytest-fixtures]

# Dependency graph
requires:
  - phase: 03-model-architecture-training-infrastructure
    provides: "MODEL_REGISTRY + gated_fusion architecture + best_model.pth checkpoint format (D-15); tests/conftest.py splits_dir / tmp_feature_dir / synth_* fixtures reused"
  - phase: 02-feature-extraction-pipeline
    provides: "UCF PNG-grid skeleton 64-frame windows + CLIP 1-FPS mean+max cache layout; data/splits/ucf_*.txt frozen split IDs"
provides:
  - "src.eval.snippet_to_frame(scores, n_frames, snippet_window, *, upsample_factor=1) — C4 length-drift-guarded broadcaster"
  - "src.eval.ucf_annotations.parse_annotations(path) — Sultani 2018 6-column parser with _x264.mp4 suffix stripping"
  - "src.eval.ucf_annotations.frame_labels(anno, n_frames) — [n_frames] int64 union-of-intervals vector with end-index clamping"
  - "src.eval.ucf_annotations.VideoAnnotation frozen dataclass + is_normal property"
  - "data/annotations/ucf_temporal.txt — committed Sultani 2018 source (290 rows)"
  - "tests/fixtures/synthetic_eval.py — make_synthetic_ucf + make_synthetic_i3d factory functions"
  - "tests/conftest.py — ucf_temporal_path / test_anno_path / eval_run_dir / synthetic_ucf_features / synthetic_i3d_features fixtures"
affects:
  - 04-02 (src/evaluate.py CLI + src/eval/test_loader.py + src/eval/metrics.py consume snippet_to_frame + parse_annotations directly)
  - 04-03 (rtfm_i3d integration test reuses synthetic_i3d_features fixture)
  - 04-04..04-07 (ablation runner + wandb preflight reuse eval_run_dir + synthetic_ucf_features)
  - 05-tta (Phase 5 evaluate.py path produces the canonical checkpoint Phase 5 adapts)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure-function utility with pre-sklearn length assertion (C4 guard pattern)"
    - "Frozen dataclass + file-parse + ValueError-on-schema-violation trio for Sultani-style text annotations"
    - "tests/fixtures/synthetic_<domain>.py factory functions returning dict of Path artifacts (UCF + I3D layouts)"
    - "TDD RED-GREEN discipline at the per-task level; commit RED before any implementation"

key-files:
  created:
    - "src/eval/__init__.py"
    - "src/eval/snippet_to_frame.py"
    - "src/eval/ucf_annotations.py"
    - "data/annotations/ucf_temporal.txt"
    - "tests/fixtures/synthetic_eval.py"
    - "tests/test_snippet_to_frame.py"
    - "tests/test_ucf_annotations.py"
  modified:
    - "tests/conftest.py"

key-decisions:
  - "D-04 implemented: data/annotations/ucf_temporal.txt committed to repo (15 KB, 290 anomaly rows from Sultani 2018 raw GitHub source). .gitignore does not exclude data/annotations/; no new ignore rule needed."
  - "D-15 implemented: single snippet_to_frame utility with mandatory C4 tolerance guard (|expanded - n_frames| <= 2*snippet_window*upsample_factor) that raises AssertionError before any sklearn call."
  - "D-16 implemented: frame_labels builds a union [s1,e1] ∪ [s2,e2] int64 vector with end-index clamping (labels[s:e] = 1 only when e > s, e = min(n_frames, int(e)))."
  - "D-17 implemented: VideoAnnotation.category reads the category column directly — no filename regex."
  - "src/eval/__init__.py is an empty package marker; no re-exports. Plan 04-02's test_loader.py will carry a sys.argv guard, so package import must not transitively pull it in. Downstream code imports submodules directly."
  - "Sultani 2018 annotation file contains anomaly test videos only (no Normal_Videos_* rows). Normal-row parser behavior is unit-tested via tmp_path synthetic rows instead of the real file — matches PATTERNS.md Example 1 test pattern."

patterns-established:
  - "Pattern: pre-sklearn length assertion — any code that calls roc_auc_score or average_precision_score must first assert len(y_score) == len(y_true) via the snippet_to_frame contract or explicit assert. Implemented inside snippet_to_frame via the drift guard."
  - "Pattern: file-parse utilities raise ValueError on schema violations, never silently produce partial state (threat mitigation T-04-01-02)."
  - "Pattern: synthetic test fixtures live in tests/fixtures/synthetic_<domain>.py with factory signatures (tmp_path, seed=0) → dict of Path objects; pytest fixtures in conftest.py wrap them for direct consumption."

requirements-completed:
  - EVAL-02
  - EVAL-04

# Metrics
duration: 8min
completed: 2026-04-15
---

# Phase 4 Plan 01: Wave 0 eval scaffold + snippet_to_frame + ucf_annotations Summary

**Pure-function snippet-to-frame broadcaster with C4 length-drift guard + Sultani 2018 UCF annotation parser + Wave 0 pytest fixture surface (10-video synthetic UCF + 5-crop synthetic I3D factories) that every subsequent Phase 4 plan consumes.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-15T09:54:58Z
- **Completed:** 2026-04-15T10:03:08Z
- **Tasks:** 2
- **Files modified:** 8 (7 created, 1 edited)

## Accomplishments

- **C4 prevention utility** (`src/eval/snippet_to_frame.py`): single signature handles both UCF compound path (window=64 PNG grid, upsample_factor=10 → 30fps) and XD I3D simple path (window=16, upsample_factor=1). Mandatory length-drift AssertionError fires before any sklearn metric call — closes the C4 off-by-one regression surface identified in `.planning/research/PITFALLS.md`.
- **Sultani 2018 annotation parser** (`src/eval/ucf_annotations.py`): frozen `VideoAnnotation` dataclass with `is_normal` property; `parse_annotations` with strict 6-column schema + `_x264.mp4` suffix stripping; `frame_labels` producing a [n_frames] int64 union-of-intervals vector with end-index clamping.
- **Committed Sultani annotation file** (`data/annotations/ucf_temporal.txt`, 290 rows) downloaded from the official `WaqasSultani/AnomalyDetectionCVPR2018` GitHub repo. First row `Abuse028_x264.mp4 Abuse 165 240 -1 -1` and two-interval row `Arson011_x264.mp4 Arson 150 420 680 1267` both validated against plan-specified fixtures.
- **Wave 0 pytest scaffold**: `tests/fixtures/synthetic_eval.py` (make_synthetic_ucf + make_synthetic_i3d factories); `tests/conftest.py` extended with 5 new fixtures (`ucf_temporal_path`, `test_anno_path`, `eval_run_dir`, `synthetic_ucf_features`, `synthetic_i3d_features`) without removing any existing fixture.
- **28 green unit tests** covering behaviors A1-A7 (snippet_to_frame compound/single repeat, exact multiple, tail-pad, truncation, C4 drift AssertionError, non-1D ValueError) and B1-B9 (real-file parse of Abuse028 + Arson011, synthetic Normal row, frame_labels union + clamping, malformed-row ValueError, import boundary smoke).

## Task Commits

TDD discipline produced 4 commits (test RED → feat GREEN for each task):

1. **Task 1 RED: failing scaffolding tests** — `3fcf360` (test)
2. **Task 1 GREEN: annotation + fixtures** — `c384732` (feat)
3. **Task 2 RED: failing unit tests** — `9a08e51` (test)
4. **Task 2 GREEN: utilities + cleanup of Task-1 scaffold duplicate** — `7316fc8` (feat)

## Files Created/Modified

- `src/eval/__init__.py` — empty package marker (D-07 / Plan 02 test_loader isolation)
- `src/eval/snippet_to_frame.py` — D-15 unified broadcaster + C4 drift guard
- `src/eval/ucf_annotations.py` — D-16/D-17 parser with VideoAnnotation dataclass, parse_annotations, frame_labels
- `data/annotations/ucf_temporal.txt` — D-04 committed Sultani 2018 source (290 rows, 15 KB)
- `tests/fixtures/synthetic_eval.py` — make_synthetic_ucf + make_synthetic_i3d factories
- `tests/test_snippet_to_frame.py` — 11 C4-regression unit tests (A1-A7 behaviors)
- `tests/test_ucf_annotations.py` — 17 parser unit tests (B1-B9 + edge cases)
- `tests/conftest.py` — extended with 5 new Phase 4 fixtures

## Decisions Made

- **Kept `src/eval/__init__.py` empty (no re-exports).** Rationale: Plan 04-02's `src/eval/test_loader.py` will carry a sys.argv guard (D-08) that raises on unknown entry points. Re-exporting from `__init__` would pull test_loader in transitively when anything imports `src.eval.*`, tripping the guard. Downstream code imports submodules directly: `from src.eval.snippet_to_frame import snippet_to_frame` (not `from src.eval import ...`).
- **Normal-row parsing unit-tested against synthetic `tmp_path` file rather than the real Sultani file.** Rationale: the published Sultani 2018 annotation file contains only anomaly test videos (290 rows, all categories except Normal). Normal videos are implied by the split file. The test pattern mirrors PATTERNS.md Example 1 exactly (Normal rows written to `tmp_path/anno.txt` then parsed).
- **C4 tolerance constant = `2 * (snippet_window * upsample_factor)`.** Rationale: drift of up to one full snippet in either direction is expected (trailing PNGs outside the final full window get dropped at extraction time); drift beyond 2 snippets indicates an upstream N_snippets bug and must fail loudly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Over-aggressive `test_truncation_long_param` parameterization**
- **Found during:** Task 2 GREEN verification
- **Issue:** The initial `@pytest.mark.parametrize("n_frames", [140, 130, 100])` case `n_frames=100` with `scores=ones(10), window=16` produces `expanded=160` and drift=60 which correctly exceeds `2*tol=32` — the C4 guard fires as designed. The test expectation was wrong, not the code.
- **Fix:** Retuned parameters to `[160, 150, 140, 130]` (all within the 2*tol tolerance window) and added an explicit docstring note that out-of-tolerance cases correctly trip the C4 guard (covered separately by A6 test).
- **Files modified:** `tests/test_snippet_to_frame.py`
- **Verification:** 28/28 tests now green; `pytest tests/test_snippet_to_frame.py tests/test_ucf_annotations.py -x` passes in 0.21s.
- **Committed in:** `7316fc8` (Task 2 GREEN commit)

**2. [Rule 2 - Missing Cleanup] Removed duplicate `tests/test_task1_scaffolding.py`**
- **Found during:** Task 2 GREEN verification
- **Issue:** Task 1's scaffolding test file was a TDD RED scaffold intended to verify Task 1 deliverables exist. After Task 2's proper unit tests (`test_snippet_to_frame.py` + `test_ucf_annotations.py`) land — both of which exercise the same fixtures — the scaffolding test is pure duplication. Plan's `files_modified` list only specifies the two proper unit test files.
- **Fix:** `git rm tests/test_task1_scaffolding.py` as part of Task 2's GREEN commit. All Task-1 assertions remain covered: fixture availability via Task 2 tests' parameter lists; annotation file schema via Task 2's real-file parse test; factory availability via conftest's lazy imports which fail at test collection if missing.
- **Files modified:** deleted `tests/test_task1_scaffolding.py`
- **Verification:** full test collection still succeeds (143 tests); all 28 Task 2 tests green.
- **Committed in:** `7316fc8` (Task 2 GREEN commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 cleanup)
**Impact on plan:** Both auto-fixes are pure quality improvements — no scope change, no new surface, no deferred work. All plan acceptance criteria met (`grep`-verified).

## Issues Encountered

- **Sultani 2018 annotation file contains no Normal_Videos rows.** The raw file from `WaqasSultani/AnomalyDetectionCVPR2018` has 290 anomaly test videos only; Normal test videos are implied by the split file (i.e., any video in `data/splits/ucf_test.txt` not in the annotation dict is treated as all-zero labels by Plan 04-02's evaluator). Behaviors B2 and B6 of the plan (Normal-row parsing + frame_labels all-zero) are therefore tested against synthetic `tmp_path` files, matching PATTERNS.md Example 1 pattern. No code change needed — Plan 02's evaluator is already expected to handle missing anomaly entries as all-zero per D-16.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Plan 04-02 ready to start.** `src/evaluate.py` CLI + `src/eval/test_loader.py` + `src/eval/metrics.py` can now import `snippet_to_frame`, `parse_annotations`, `frame_labels`, `VideoAnnotation` directly without triggering any sys.argv guard.
- **Wave 2+ plans ready.** `synthetic_ucf_features` + `synthetic_i3d_features` + `eval_run_dir` + `ucf_temporal_path` fixtures available for all downstream tests (Plan 03 RTFM shapes, Plan 05 ablation runner, Plan 06 wandb preflight).
- **C4 regression surface is locked.** Single-modal and compound expansion paths are unit-tested; the length-drift AssertionError ensures any upstream N_snippets / label_vector inconsistency fails before sklearn call rather than silently producing wrong AUC/AP.
- **No blockers.**

## Threat Mitigations Applied

| Threat ID | Mitigation Implemented | Evidence |
|-----------|------------------------|----------|
| T-04-01-01 (Tampering) | Post-download integrity check | Task 1 verified 290 lines, all 6-column, contains `Abuse028_x264.mp4` before committing |
| T-04-01-02 (DoS via malformed row) | `parse_annotations` raises ValueError on wrong column count | Task 2 test_malformed_row_5_cols_raises + test_malformed_row_7_cols_raises |
| T-04-01-04 (Spoofing wrong file URL) | Schema validation after download | Task 1 scaffolding verified known video ID string + column count before Task 1 commit |

## Self-Check: PASSED

- [x] `src/eval/__init__.py` exists
- [x] `src/eval/snippet_to_frame.py` exists with `def snippet_to_frame(` + `upsample_factor` + `AssertionError`
- [x] `src/eval/ucf_annotations.py` exists with `class VideoAnnotation` + `def parse_annotations` + `def frame_labels`
- [x] `data/annotations/ucf_temporal.txt` exists (290 lines, 6 cols per line, contains Abuse028_x264.mp4)
- [x] `tests/fixtures/synthetic_eval.py` exists with `make_synthetic_ucf` + `make_synthetic_i3d`
- [x] `tests/conftest.py` contains `ucf_temporal_path`, `test_anno_path`, `eval_run_dir`, `synthetic_ucf_features`, `synthetic_i3d_features` (plus all pre-existing fixtures preserved)
- [x] `tests/test_snippet_to_frame.py` contains `test_compound_repeat_ucf`, `test_single_repeat_i3d`, `test_tolerance_violation_raises`
- [x] `tests/test_ucf_annotations.py` references `Abuse028`, `Arson011`, `Normal_Videos_003`
- [x] Commit `3fcf360` exists (Task 1 RED)
- [x] Commit `c384732` exists (Task 1 GREEN)
- [x] Commit `9a08e51` exists (Task 2 RED)
- [x] Commit `7316fc8` exists (Task 2 GREEN)
- [x] `pytest tests/test_snippet_to_frame.py tests/test_ucf_annotations.py -x` → 28 passed

---
*Phase: 04-baseline-evaluation-main-results*
*Completed: 2026-04-15*
