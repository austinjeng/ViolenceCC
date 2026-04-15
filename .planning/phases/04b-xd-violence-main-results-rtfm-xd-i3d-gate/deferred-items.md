# Phase 04b Deferred Items

Items discovered during execution but out of scope for the current plan.

## From Plan 04b-02

### Pre-existing test failure: `tests/test_train_integration.py::test_no_test_split_access`

**Discovered during:** Plan 04b-02 full-suite regression check (2026-04-15)

**Root cause:** The C3 AST scan at `tests/test_train_integration.py:286-313` iterates over ALL files under `src/` (including `src/eval/test_loader.py`). The scan's purpose is to catch training-side code touching the test split, but it does not exclude the test loader module itself -- which is definitionally the one module allowed to reference `xd_test.txt` / `ucf_test.txt`.

**Verified as pre-existing:** Checked out base commit `31abfaec` (`docs(04b): record planning completion + pattern map`) and the failure reproduces identically. My Plan 04b-02 changes to `src/data/loaders.py` do NOT reference `*_test.txt` -- I only reference `xd_train.txt` and `xd_val.txt`, so I'm not contributing to the failure.

**Recommendation:** Add an allowlist in `_scan_py_for_test_split()` for `src/eval/test_loader.py`. This is a separate plan -- not part of 04b-02 scope.

**Tracked for:** Future test-infra cleanup plan (not Phase 04b scope).
