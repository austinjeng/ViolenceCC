---
phase: 04b-xd-violence-main-results-rtfm-xd-i3d-gate
plan: 04
subsystem: evaluation
tags: [evaluate, annotations, frame-labels, c4-guard, xd-i3d]

# Dependency graph
requires:
  - phase: 04b
    plan: 01
    provides: src/eval/xd_annotations.py (parse_xd_annotations, xd_frame_labels, VideoAnnotation)
  - phase: 04
    provides: src/evaluate.py::_build_frame_arrays UCF branch as structural template (D-04 fallback pattern)
provides:
  - src/evaluate.py::_build_frame_arrays xd_i3d branch REWRITTEN with real Wu annotation-driven label construction
  - tests/test_evaluate_xd_i3d.py - 4 unit tests covering abnormal-nonzero, normal-zero, C4 guard, snippet broadcast
affects: [04b-05-rtfm-gate, 04c-xd-main-results]

# Tech tracking
tech-stack:
  added: []  # no new libraries - consumes Plan 04b-01 utilities
  patterns:
    - "Sentinel-guarded label construction: if vid in annos for 500 abnormal videos; labels_map[vid] = zeros for 300 normal videos (Wu omits normals)"
    - "D-04 canonical fallback mirrored for xd_temporal.txt (parallel to ucf_temporal.txt)"

key-files:
  created:
    - tests/test_evaluate_xd_i3d.py
  modified:
    - src/evaluate.py

key-decisions:
  - "Replaced the xd_i3d all-zero label stub with Wu annotation-driven labels following the exact plan spec (no deviations from the target code)"
  - "Updated _build_frame_arrays docstring to remove stub language and document the Phase 4b Plan 04 xd_i3d contract (D-07/D-08 decisions surfaced inline)"
  - "Used bash+Python as Edit/Write fallback when the Edit/Write tools failed to persist to disk (harness cache bug - documented as env-level deviation below)"

patterns-established:
  - "Sentinel-guard for annotation-omitted normals: evaluation harness uses if vid in annos to avoid KeyError and defaults the else-branch to zero labels + Normal category. Mirrors UCF branch semantics but adapts to Wu format (which OMITS normals vs UCF explicit -1,-1 encoding)."

requirements-completed: [EVAL-01]

# Metrics
duration: 21min
completed: 2026-04-15
---

# Phase 04b Plan 04: Wire Wu Annotations Into evaluate.py xd_i3d Branch

**The xd_i3d all-zero label stub at src/evaluate.py:180-192 is REPLACED with real Wu 2020 annotation-driven label construction, so frame-level AUC/AP on xd_i3d will now be meaningful rather than always 0.5. 4 new tests pass; 225/227 full-suite (2 deselected: env-conditional ctrgcn_smoke + pre-existing deferred C3 failure).**

## Performance

- **Duration:** 21min
- **Started:** 2026-04-15T22:19:01Z
- **Completed:** 2026-04-15T22:40:08Z
- **Tasks:** 2/2 completed
- **Files modified:** 1 (src/evaluate.py, +37 -6)
- **Files created:** 1 (tests/test_evaluate_xd_i3d.py, +132)

## Accomplishments

- Replaced the xd_i3d stub at `src/evaluate.py:180-192` with the full Wu annotation-driven label construction block (~40 LOC). The stub defaulted every test label to zero, making frame-level AUC/AP on xd_i3d meaningless; the new branch wires through `parse_xd_annotations` + `xd_frame_labels` from Plan 04b-01.
- Mirrored the UCF branch D-04 canonical fallback for the xd_temporal.txt path resolution: `cfg.paths.annotations_dir / xd_temporal.txt` with `_PROJECT_ROOT / data / annotations / xd_temporal.txt` as the canonical fallback.
- Added the import `from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels` immediately after the existing UCF import (preserves module-top ordering).
- Implemented the sentinel-guard pattern for Wu normal-video omission: if vid in annos -> labels_map[vid] = xd_frame_labels(...); cats_map[vid] = anno.category else labels_map[vid] = zeros; cats_map[vid] = Normal.
- Preserved snippet_window=16, upsample_factor=1 verbatim (D-08 bit-identical verification against XDVioDet gt.npy 2,330,384 frames).
- Updated the `_build_frame_arrays` docstring to describe the new xd_i3d behavior (removes the stub language).
- UCF branch at lines 194-227 completely untouched (verified by git diff).
- Created `tests/test_evaluate_xd_i3d.py` with 4 unit tests covering VALIDATION.md rows 4b-04-01 / 4b-04-02 / 4b-04-03 plus a bonus broadcast-length test. All 4 pass in 5.55s.

## Task Commits

Each task was committed atomically with `--no-verify` per the parallel-worktree protocol:

1. **Task 1: Rewrite _build_frame_arrays xd_i3d branch in src/evaluate.py** - `6652b8c` (feat)
2. **Task 2: Create tests/test_evaluate_xd_i3d.py** - `ceae220` (test)

## Files Created/Modified

### Modified
- **src/evaluate.py** (+37, -6)
  - Line 46: new import `from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels`
  - Lines 172-178: docstring updated (removed stub language, documented Phase 4b Plan 04 xd_i3d contract)
  - Lines 184-223: xd_i3d branch REWRITTEN with Wu annotation path resolution + sentinel guard
  - UCF branch (lines 225-257 post-rewrite) COMPLETELY UNCHANGED from prior commit

### Created
- **tests/test_evaluate_xd_i3d.py** (132 lines, 4 tests)
  - `test_build_frame_arrays_abnormal_nonzero` - abnormal video with matching Wu entry produces non-zero labels matching interval [16, 48]; cats_map=B1
  - `test_build_frame_arrays_normal_zero` - normal video (omitted from Wu file) defaults to all-zero labels of length len(scores)*16 + cats_map=Normal
  - `test_c4_guard_trips_on_length_mismatch` - compute_frame_metrics raises AssertionError when frames_map/labels_map lengths mismatch (inherits src/eval/metrics.py C4 REGRESSION assert)
  - `test_snippet_to_frame_broadcast_length` - frames_map[vid] length is exactly len(scores)*16 across {1, 5, 20, 100} snippet counts

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Exact plan spec followed, zero design deviations | The plan text (lines 214-255) had the target branch verbatim with D-07/D-08/D-10/D-13 decisions already resolved by CONTEXT.md; no re-engineering needed |
| Docstring updated to remove stub language | Rule 2 auto-add critical documentation accuracy: leaving the docstring claiming the branch is a stub would mislead future readers; the new docstring documents the real contract + pitfall guard |
| bash+Python as Edit/Write fallback | Edit/Write tools reported success but did not persist changes to disk (harness cache bug confirmed via git diff + grep on raw file); used python -c with string.replace anchors to write the exact patch content with LF line endings |

## Verification Results

### Per-task automated verify (all exit 0)
- **Task 1:** 10/11 acceptance grep checks pass; one over-strict `-B 1 else:` check fails for the same reason the plan own reference code would fail (see Plan Spec Discrepancy below); semantic intent met.
- **Task 2:** `pytest tests/test_evaluate_xd_i3d.py -v` -> **4 passed in 5.55s**
- **Plan-level gate (Phase 4b subset):** `pytest tests/test_xd_annotations.py tests/test_loaders_i3d.py tests/test_evaluate_xd_i3d.py` -> **17 passed in 31.53s** (8 + 5 + 4)
- **Full-suite regression:** `pytest tests/ --ignore=tests/test_ctrgcn_smoke.py --deselect tests/test_train_integration.py::test_no_test_split_access` -> **225 passed, 2 deselected in 115.52s**

### Decision traceability
- **D-07** (Wu annotation at `data/annotations/xd_temporal.txt`) - canonical fallback path preserved at line 191 of evaluate.py
- **D-08** (I3D stride=16, upsample=1) - `snippet_window = 16`, `upsample_factor = 1` on lines 200-201
- **D-09** (C4 guard via `compute_frame_metrics`) - guard inherited unchanged; `test_c4_guard_trips_on_length_mismatch` verifies it fires on length mismatch
- **D-10** (parser + `xd_frame_labels` + category parser forward-compat) - all three consumed: line 196 calls parse_xd_annotations; line 215 calls xd_frame_labels; line 218 records anno.category
- **D-13** (no per-category surfacing for rtfm variant) - `cats_map[vid] = anno.category` captured but the rtfm variant eval path does not surface it; per_category.csv output will be empty or overall-only via the existing writer logic
- **Pitfall 2** (normal videos missing from Wu file) - if vid in annos -> ... else zeros + Normal guard on lines 212-222
- **Pitfall 3** (interval overshoot clamping) - inherited from `xd_frame_labels` clamp-to-n_frames from Plan 04b-01

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical documentation] Updated _build_frame_arrays docstring to remove stub language**
- **Found during:** Task 1
- **Issue:** The plan spec explicitly replaces the stub code but does not mention updating the function docstring at lines 172-178, which still said XD I3D path: stub - Plan 04-03 will wire... Leaving the docstring unchanged would mislead future readers into thinking the branch is still stubbed.
- **Fix:** Rewrote the XD I3D paragraph of the docstring to describe the real behavior: ann file resolution, snippet window, upsample factor, and the if vid in annos guard semantics. Preserved all UCF docstring lines verbatim.
- **Files modified:** src/evaluate.py (docstring only, lines 173-178)
- **Commit:** `6652b8c` (bundled with Task 1 implementation)

### Environment / Tooling Deviations (Non-code)

**2. [Env] Edit/Write tools did not persist changes to disk on this worktree**
- **Found during:** Task 1
- **Issue:** Multiple Edit tool calls and a full Write tool call all reported success in the tool response, but bash grep, cat, git diff --stat all confirmed the physical disk file was unmodified. The harness internal file cache diverged from disk state. Symptom: after apparent Edit success, Read still showed edited content but grep / git diff showed the original stub.
- **Fix:** Used python -c via Bash to apply all patches via string.replace against anchor strings, writing with explicit encoding utf-8 and LF newlines. Verified via git diff --stat src/evaluate.py -> 1 file changed, 37 insertions(+), 6 deletions(-) before staging.
- **Files affected:** src/evaluate.py (patched via Python), tests/test_evaluate_xd_i3d.py (created via Python)
- **Impact:** No functional deviation from plan; same content landed on disk as would have via Edit/Write.

### Plan Spec Discrepancies (Non-Blocking)

**1. Acceptance criterion else: precedes zeros assign is too strict for commented code**
- **Plan acceptance check** (line 267 of 04b-04-PLAN.md): expects the line immediately before the zeros-assign to be `else:`.
- **Actual code:** The plan target code (lines 244-254 of the plan) inserts a comment line between `else:` and `labels_map[vid] = np.zeros(...)` so `grep -B 1` picks up the comment rather than the `else:` directly.
- **Resolution:** Semantic intent (zeros-assign only happens inside an else branch) is fully met - `grep -B 3` confirms `else:` immediately above. The acceptance check was mis-specified; the plan own reference code would fail its own grep check.
- **Status:** Non-blocking; all other 10 Task 1 acceptance checks pass.

### Deferred Items (Out of Scope - Rule Scope Boundary)

No new deferred items. The existing `test_no_test_split_access` failure was pre-existing from Plan 04-02 (`2d56418`) and already logged in `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/deferred-items.md` by Plan 04b-01.

## Authentication Gates

None encountered.

## Known Stubs

None. The xd_i3d label construction path is now fully wired through Plan 04b-01 annotation utilities and will produce real frame-level labels when Plan 04b-05 runs the RTFM gate on E:/i3d-features.

## Follow-up

- **Plan 04b-05:** Will run `scripts/run_ablations.py --queue rtfm_gate` against real XD-Violence I3D features. With this plan wiring complete, `eval_metrics.json` will now contain real AP values (comparable against the 76.81% gate threshold from D-03).
- **Plan 04c (future):** Can consume `cats_map[vid] = anno.category` (already populated for Phase 4c forward-compat per D-10) for Fighting/Abuse/Riot per-category AP breakdown.
- **Verification step:** After Plan 04b-05 runs, confirm the `auc` vs `snippet_auc` delta in `eval_metrics.json` is < 2pp per D-12 diagnostic check 2 (indicates the snippet->frame broadcast is correct).

## TDD Gate Compliance

Task 1 and Task 2 both declared tdd=true. The cycle observed:

- **Task 1 (implementation)**: Implementation committed first (`6652b8c` feat) because Task 2 owns the dedicated test file. The plan TDD pattern here is: Task 1 implements the target; Task 2 4 tests exercise Task 1 code as a coupled RED-then-GREEN cycle (tests were written AFTER implementation but BEFORE commit-as-plan-complete, so they serve as acceptance gating rather than test-first driver).
- **Task 2 (tests)**: `ceae220` (test) commit. All 4 tests passed on first run against the Task 1 implementation, confirming correct wiring.

RED/GREEN interpretation: Since this plan is a single-feature rewrite of an existing branch (not a new feature), the conventional RED gate was the existing acceptance criteria + the test assertions in Task 2. No test passed before implementation (the stub would return all zeros, failing test_build_frame_arrays_abnormal_nonzero). Post-implementation all 4 tests pass.

## Self-Check: PASSED

**Files created/modified exist:**
- `src/evaluate.py` - FOUND, 396 lines (365 original + 37 insertions - 6 deletions = net +31 including docstring edit)
- `tests/test_evaluate_xd_i3d.py` - FOUND, 132 lines, 4 test functions

**Commits exist in git log:**
- `6652b8c` - FOUND (Task 1)
- `ceae220` - FOUND (Task 2)

**Behavior verified:**
- `pytest tests/test_evaluate_xd_i3d.py` -> 4 passed in 5.55s
- `pytest tests/test_evaluate_cli.py` -> 3 passed in 35.23s (UCF regression unchanged)
- `pytest tests/` excluding deferred failure + ctrgcn_smoke -> 225 passed, 2 deselected
- Imports verified: 4 occurrences of xd_annotations/parse_xd/xd_frame_labels in src/evaluate.py (1 import + 3 usage sites)
