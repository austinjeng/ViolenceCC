# Phase 4b — Deferred Items

Out-of-scope discoveries logged during execution. These are NOT auto-fixed by Rule 1/2/3
because they are not caused by the current task's changes; they are pre-existing issues.

---

## Pre-existing test failure: `test_no_test_split_access` (C3 guard)

**Test file:** `tests/test_train_integration.py::test_no_test_split_access`

**Discovered during:** Plan 04b-01 Task 3 full-suite regression check.

**Failure summary:** The C3 scanner detects `_test.txt` string literals inside
`src/eval/test_loader.py` lines 93 (`'ucf_test.txt'`), 113/124 (`'xd_test.txt'`).
Layer-1 substring scan also flags the whole file. The scan does not exempt
intentional test-set loading utilities; `test_loader.py` is an evaluation-time
loader that must reference test-split names to do its job.

**Provenance:** Committed in `2d56418 feat(04-02): test_loader sys.argv guard`
(Phase 4 Plan 04-02 Task 1). Pre-dates Phase 4b by several commits.

**Why deferred:**
- Phase 4b Plan 01 scope is "annotation parser module + committed data file + unit tests"
- The C3 guard is not a Plan 04b-01 deliverable; fixing it requires either:
  1. Adding a file-level exemption list to `test_no_test_split_access` (test-side change)
  2. Refactoring `src/eval/test_loader.py` to accept test-split filename as argument
     rather than hardcoding literals (design change, not a bug fix)
- Either approach is architectural (Rule 4) relative to this plan's objective.

**Verification that this is NOT introduced by Plan 04b-01:**
Running `git checkout 31abfaec5b5c6d6228e934e359064b90cad98899 -- src tests && pytest
tests/test_train_integration.py::test_no_test_split_access` at the phase base commit
reproduces the same 4-hit failure. The 2 hits added in an earlier docstring draft of
`src/eval/xd_annotations.py` were removed in this plan (docstring rewritten to avoid
the `_test.txt` substring while preserving meaning).

**Suggested owner/phase:** Address in Plan 04b-04 or later when evaluate.py is
wired for xd_i3d and the test_loader surface becomes load-bearing again.
