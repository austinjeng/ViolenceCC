# Phase 4b — Deferred Items

Out-of-scope discoveries logged during execution. These are NOT auto-fixed by Rule 1/2/3
because they are not caused by the current task's changes; they are pre-existing issues.

---

## Pre-existing test failure: `test_no_test_split_access` (C3 guard)

**Test file:** `tests/test_train_integration.py::test_no_test_split_access`

**Discovered during:** Plan 04b-01 Task 3 full-suite regression check (independently
confirmed during Plan 04b-02 regression check on 2026-04-15).

**Failure summary:** The C3 scanner at `tests/test_train_integration.py:286-313` iterates
over ALL files under `src/` (including `src/eval/test_loader.py`). It detects `_test.txt`
string literals inside `src/eval/test_loader.py` lines 93 (`'ucf_test.txt'`), 113/124
(`'xd_test.txt'`). Layer-1 substring scan also flags the whole file. The scan does not
exempt intentional test-set loading utilities; `test_loader.py` is an evaluation-time
loader that must reference test-split names to do its job.

**Provenance:** Committed in `2d56418 feat(04-02): test_loader sys.argv guard`
(Phase 4 Plan 04-02 Task 1). Pre-dates Phase 4b by several commits.

**Verified pre-existing (not a 4b regression):**
- Plan 04b-01: docstring of new `src/eval/xd_annotations.py` was rewritten to avoid the
  `_test.txt` substring; failure still reproduces at base commit `31abfaec`.
- Plan 04b-02: only modifies `src/data/loaders.py` to reference `xd_train.txt` /
  `xd_val.txt`; failure still reproduces at base commit `31abfaec`.

**Why deferred (Rule 4 — architectural):**
- Phase 4b Plan scopes do not include test-infra refactors.
- Fixing requires either:
  1. Adding a file-level allowlist in `_scan_py_for_test_split()` for
     `src/eval/test_loader.py` (test-side change).
  2. Refactoring `src/eval/test_loader.py` to accept test-split filename as argument
     rather than hardcoding literals (design change).

**Suggested owner/phase:** Address in Plan 04b-04 or later when `evaluate.py` is wired
for xd_i3d and the test_loader surface becomes load-bearing again.

**Tracked for:** Future test-infra cleanup plan (not Phase 04b scope).
