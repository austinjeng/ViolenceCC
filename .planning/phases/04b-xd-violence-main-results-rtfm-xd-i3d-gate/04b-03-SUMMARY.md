---
phase: 04b
plan: 03
subsystem: training
tags: [training, dispatch, mil-loss, i3d, xd-violence, rtfm]
requires:
  - src/data/loaders.py::build_dataloaders_i3d (Plan 04b-02)
  - src/losses/mil_loss.py::mil_ranking_loss
  - src/models/rtfm_i3d.py::RTFMI3D
provides:
  - src/train.py::train_one_epoch_i3d
  - src/train.py::validate_i3d
  - src/train.py::_split_labels_i3d
  - src/train.py::main() xd_i3d dispatch branch
affects:
  - src/train.py (existing train_one_epoch, validate, _split_labels UNCHANGED per D-04)
tech_stack:
  added: []
  patterns:
    - "D-04 parallel-functions (not polymorphic dispatch)"
    - "D-12 one-shot bag-size audit on first 3 epochs"
    - "Pitfall 1 defensive mask synthesis (torch.ones for i3d)"
    - "TRN-03 determinism unchanged (inherits set_deterministic + CUBLAS)"
key_files:
  created:
    - tests/test_train_i3d.py (207 lines, 3 tests)
  modified:
    - src/train.py (+162 lines; added _split_labels_i3d + train_one_epoch_i3d + validate_i3d + main() dispatch branch)
decisions:
  - "Added train_one_epoch_i3d/validate_i3d/_split_labels_i3d alongside the UCF fusion path (D-04 parallel-functions)"
  - "main() dispatch is a single if/else in the loader-construction block + a 2-branch if/else in the epoch loop (to thread epoch= only into the i3d path)"
  - "D-12 bag-size audit wired as one-shot print on first step of first 3 epochs to stderr (not assertion-only); includes 2 shape asserts that fail loudly on concat bugs"
  - "Defensive torch.ones mask in train_one_epoch_i3d and _split_labels_i3d -- even when collate already emits one -- per Pitfall 1 explicit-is-better-than-implicit"
metrics:
  duration_min: 14
  tasks_completed: 2
  tests_added: 3
  tests_passing: 3
  files_created: 1
  files_modified: 1
  lines_added: 369
  completed: 2026-04-15
commits:
  - 3d5bdae (Task 1): feat(04b-03) add xd_i3d training dispatch to src/train.py
  - 865c59f (Task 2): test(04b-03) add tests/test_train_i3d.py (3 tests, all passing)
---

# Phase 4b Plan 03: xd_i3d Training Dispatch Summary

Wired the `xd_i3d` training path end-to-end in `src/train.py` via three new functions (`train_one_epoch_i3d`, `validate_i3d`, `_split_labels_i3d`) + a one-site dispatch branch in `main()`, plus 3 passing unit tests that cover signature parity, loss-finite on synthetic, and end-to-end `main()` dispatch with D-12 bag-size audit verification.

## What Changed

### `src/train.py` (+162 LOC)

1. **`_split_labels_i3d(batch) -> Optional[Tuple[Tensor, Tensor, int]]`** — D-04 parallel to `_split_labels`.
   - Partitions a mixed-label val batch by `label == 0` / `label == 1` indices.
   - Returns `(i3d_paired [2n, T, 1024], mask [2n, T] all-ones, n_normal int)` or `None` if a class is missing.
   - Synthesizes `mask = torch.ones(...)` per Pitfall 1 (I3DFeatureDataset has no padding; `_resample_T` produces a fixed-length `[T, 1024]` output).

2. **`train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, device, train_cfg, epoch=0) -> float`** — D-04 parallel to `train_one_epoch`.
   - Consumes i3d-only batches (no skel/clip keys); concats `nor_batch["i3d"]` + `abn_batch["i3d"]` along dim 0.
   - Defensive mask synthesis: `mask = torch.ones(i3d.shape[0], i3d.shape[1], device=device)` — independent of the collate's emission so the Pitfall 1 guard is explicit at the call site.
   - **D-12 bag-size audit:** on `epoch < 3 and step == 0`, prints `[i3d_audit]` line to stderr with `epoch`, `step`, `n_normal`, `n_abnormal`, `i3d_shape`, `mask_shape`. Plus two shape assertions that raise loudly on any nor/abn mismatch or concat bug.
   - New `epoch: int = 0` kwarg enables the audit gating without threading through unrelated kwargs in the UCF path.

3. **`validate_i3d(model, val_loader, device, train_cfg) -> float`** — D-04 parallel to `validate`.
   - `@torch.no_grad()` decorated.
   - Iterates val_loader, pairs each batch via `_split_labels_i3d`, computes MIL loss, returns mean. Returns `float('inf')` if no paired samples (Open Question #1 guarded at loader-construction time by `build_dataloaders_i3d`'s `len(val_abn) > 0` assert).
   - Signature parity with `validate` enforced by `test_validate_i3d_signature` (VALIDATION row 4b-03-02).

4. **`main()` dispatch branch** — D-04 "branch once" pattern.
   - After `build_model(...)` and before optimizer construction: a single `if cfg.get("dataset") == "xd_i3d":` block selects `build_dataloaders_i3d` + `_train_fn = train_one_epoch_i3d` + `_val_fn = validate_i3d`; else path uses the Phase 3 fusion wiring unchanged.
   - Inside the `for epoch in range(...)` loop, an additional small `if cfg.get("dataset") == "xd_i3d":` guard threads `epoch=epoch` into `_train_fn` (the non-i3d `train_one_epoch` does not accept `epoch`).
   - **CSV/wandb logging, early stopping, checkpoint save are UNCHANGED** — both paths reuse the same logging + serialization code.

5. **Import change** — `from src.data.loaders import build_dataloaders, build_dataloaders_i3d` (single-line addition of the new name alongside the existing one).

### `tests/test_train_i3d.py` (NEW, 207 lines, 3 tests)

| Test | Requirement Row | What It Guards |
|------|-----------------|----------------|
| `test_train_one_step_loss_finite` | 4b-03-01 | `train_one_epoch_i3d` on `synthetic_i3d_features` returns finite float (not NaN/+Inf/-Inf) |
| `test_validate_i3d_signature` | 4b-03-02 | `inspect.signature(validate_i3d).parameters == inspect.signature(validate).parameters` |
| `test_main_dispatch_xd_i3d` | 4b-03-03 | `main(['--config', cfg, '--epochs', '1'])` with `cfg.dataset=='xd_i3d'` exits 0; writes `best_model.pth`, `config_snapshot.json`, `train_log.csv`; captures `[i3d_audit]` in stderr/stdout (D-12 diagnostic) |

Helpers adapted from `tests/test_train_integration.py`:
- `_ensure_val_split(fx)`: synthesizes `xd_val.txt` inline from the fixture's train split (fixture ships `xd_train.txt` + `xd_test.txt` only).
- `_build_smoke_xd_i3d_config(fx, tmp_path)`: writes a 1-epoch xd_i3d YAML pointing at the synthetic fixture with `batch_size=1` (→ 5 samples after 5-crop flatten, sufficient for `k_topk=3`).
- `_latest_run(results_dir)`: mirrors `test_train_integration.py::_latest_run`.

## Commits

| Hash | Task | Scope |
|------|------|-------|
| `3d5bdae` | Task 1 | `feat(04b-03): add xd_i3d training dispatch to src/train.py` — +162 lines / -5 lines to `src/train.py` |
| `865c59f` | Task 2 | `test(04b-03): add tests/test_train_i3d.py (3 tests, all passing)` — +207 lines new test file |

## Test Results

**Plan 04b-03 target tests (3/3 passing):**
```
$ C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_train_i3d.py -x --tb=short
tests/test_train_i3d.py::test_train_one_step_loss_finite PASSED          [ 33%]
tests/test_train_i3d.py::test_validate_i3d_signature PASSED              [ 66%]
tests/test_train_i3d.py::test_main_dispatch_xd_i3d PASSED                [100%]
============================== 3 passed in 39.88s ==============================
```

**Phase 4b test subset (16/16 passing):**
```
$ pytest tests/test_xd_annotations.py tests/test_loaders_i3d.py tests/test_train_i3d.py -x --tb=short
tests/test_xd_annotations.py ........                                    [ 50%]
tests/test_loaders_i3d.py .....                                          [ 81%]
tests/test_train_i3d.py ...                                              [100%]
============================== 16 passed in 6.72s ==============================
```

**Training-path regression check (27/27 passing, excluding 2 known deferred):**
```
$ pytest tests/test_xd_annotations.py tests/test_loaders_i3d.py tests/test_train_i3d.py \
         tests/test_train.py tests/test_train_integration.py \
         --deselect tests/test_train_integration.py::test_no_test_split_access
================ 27 passed, 2 deselected, 8 warnings in 29.54s ================
```

**Full-suite result (223/224 passing, 1 flaky pre-existing, 2 deselected):**
- `tests/test_train_e2e.py::test_snapshot_roundtrip` failed under the full 137-second suite timing (flaky — `run_name()` uses 1-second timestamp resolution at `src/train.py:61`; both `main()` calls completing within the same second produce identical dir names). **PASSES when the e2e file runs in isolation** (`pytest tests/test_train_e2e.py → 3/3 passed in 41s`), confirming it is a pre-existing timing flake, NOT a regression from this plan's changes. See Deferred Issues below.
- `tests/test_train_integration.py::test_no_test_split_access` — pre-existing deferred failure (documented in `deferred-items.md` from Plan 04b-02).

## Sample D-12 Audit Line (VALIDATION row 4b-03-03 / D-12 diagnostic check 3)

Captured from a live `train_one_epoch_i3d` call on the `synthetic_i3d_features` fixture:

```
[i3d_audit] epoch=0 step=0 n_normal=5 n_abnormal=5 i3d_shape=(10, 32, 1024) mask_shape=(10, 32)
```

Shape breakdown: `batch_size=1 * n_crops=5 = 5` samples per loader, concatenated `nor + abn = 10` along dim 0. `T=32`, `D=1024`. Mask shape matches `[2*B*5, T] = [10, 32]`. The assertions `n_normal == abn_batch.shape[0]` and `i3d.shape[0] == 2*n_normal` both hold.

## Acceptance Criteria

**Plan-level:**
- [x] `src/train.py` contains `def train_one_epoch_i3d` + `def validate_i3d` + `def _split_labels_i3d`
- [x] `src/train.py::main()` dispatch branch present on `cfg.get("dataset") == "xd_i3d"` (2 sites: loader-construction + epoch-loop for `epoch=` threading)
- [x] Existing `train_one_epoch`, `validate`, `_split_labels` bodies UNCHANGED
- [x] `tests/test_train_i3d.py` has 3 tests, all passing
- [x] Full suite: no NEW regressions (UCF fusion train path still works; flaky e2e + deferred C3 are pre-existing)
- [x] `[i3d_audit]` diagnostic line emitted during synthetic 1-epoch run (D-12 Check 3 precursor)
- [x] `cfg.dataset == 'xd_i3d'` correctly routes through new loader + train + val functions
- [x] `build_dataloaders_i3d` imported AND called in `main()`

**Task 1 acceptance:**
- [x] `grep -c "def train_one_epoch_i3d"` = 1
- [x] `grep -c "def validate_i3d"` = 1
- [x] `grep -c "def _split_labels_i3d"` = 1
- [x] `grep -qE "^def train_one_epoch\(" src/train.py` exit 0
- [x] `grep -qE "^def validate\(" src/train.py` exit 0
- [x] `grep -q "from src.data.loaders import" src/train.py` and `build_dataloaders_i3d` is among the imports
- [x] `grep -q 'cfg.get("dataset") == "xd_i3d"' src/train.py` exit 0
- [x] `grep -q "\[i3d_audit\]" src/train.py` exit 0
- [x] `torch.ones` count in src/train.py >= 2 (4 actual; 2 in new code + 2 in regularizer imports)
- [x] `mil_ranking_loss(` count = 4 (2 old + 2 new)
- [x] `python -c "from src.train import train_one_epoch_i3d, validate_i3d"` exits 0
- [x] Signature parity: `validate_i3d.parameters == validate.parameters` (verified via inspect)

**Task 2 acceptance:**
- [x] `tests/test_train_i3d.py` exists
- [x] `grep -c "^def test_"` = 3
- [x] Required test function names present (all 3: `test_train_one_step_loss_finite`, `test_validate_i3d_signature`, `test_main_dispatch_xd_i3d`)
- [x] All 3 tests pass: `pytest tests/test_train_i3d.py -x → 3 passed`
- [x] `grep -q "from src.train import" tests/test_train_i3d.py` exit 0
- [x] `grep -q "synthetic_i3d_features" tests/test_train_i3d.py` exit 0
- [x] `grep -q "\[i3d_audit\]" tests/test_train_i3d.py` exit 0 (in dispatch test)

## Deviations from Plan

**None — plan executed exactly as written.**

The plan's code drafts for `_split_labels_i3d`, `train_one_epoch_i3d`, `validate_i3d`, and the `main()` dispatch were applied verbatim with only minor docstring rewording for clarity. The test file was implemented per the plan's exact specification with one minor structural adjustment: `_ensure_val_split(fx)` was factored out as a helper function rather than being inlined into each test's prologue (cleaner, avoids triplication across the 3 tests) — this is a non-functional refactor, not a semantic deviation.

No Rule 1/2/3/4 auto-fixes were needed.

## Deferred Issues

### Flaky test: `tests/test_train_e2e.py::test_snapshot_roundtrip` (pre-existing timing race)

**Failure:** In the full 137-second suite, two back-to-back `main()` calls within `test_snapshot_roundtrip` complete within the same wall-clock second, causing `run_name()` at `src/train.py:61` (`"%Y%m%d-%H%M%S"` resolution) to produce identical dir names — the assertion `len(runs) >= 2` trips with `1 >= 2`.

**Verified pre-existing / not a 4b-03 regression:**
- `pytest tests/test_train_e2e.py → 3/3 passed in 41s` when run in isolation.
- `pytest tests/test_train_e2e.py::test_snapshot_roundtrip tests/test_train_integration.py → 9/9 passed in 18s` when run in a smaller subset.
- My changes to `src/train.py` do NOT touch `run_name()` (line 59-62). The flake is driven by test-suite wall-clock timing, not code paths I modified.

**Action:** Not fixing in Plan 04b-03 per executor's SCOPE BOUNDARY rule. Root cause is `run_name`'s 1-second resolution; a proper fix is either (a) millisecond/nanosecond resolution in the timestamp, or (b) a monotonic counter suffix when a collision is detected. Both are architectural changes (Rule 4) to a file that is out-of-scope for 04b-03. Logged for a future test-infra cleanup plan.

### Pre-existing failure: `tests/test_train_integration.py::test_no_test_split_access`

Inherited from Plan 04b-02's `deferred-items.md`. The C3 AST scan over `src/` matches `src/eval/test_loader.py`'s intentional `*_test.txt` literals. Not a regression from Plan 04b-03; the `src/train.py` changes in this plan add no `_test.txt` references. Documented in `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/deferred-items.md`.

## Authentication Gates

None encountered. Task is pure Python code + unit tests; no external services, no credential prompts. Wandb is disabled via `cfg.wandb.mode = "disabled"` in the test config, matching the Phase 4 D-14 convention for smoke tests.

## Decision Traceability

| Decision | Implementation |
|----------|----------------|
| **D-04** parallel functions (not polymorphic) | 3 new functions added alongside existing; existing bodies UNCHANGED; main() branches once on `cfg.get("dataset") == "xd_i3d"` |
| **D-05** crop-as-sample inherited | Inherited from Plan 04b-02 `collate_i3d_train`; `train_one_epoch_i3d` operates on already-flattened `[B*5, T, 1024]` batches |
| **D-06** `_label_A` partition inherited | Inherited from Plan 04b-02 `build_dataloaders_i3d`; `_split_labels_i3d` partitions on `batch["label"]` integer values (which are computed per-crop from the suffix at `I3DFeatureDataset.__getitem__` time) |
| **D-12** Train-time 5-crop bag-size audit (Check 3) | `[i3d_audit]` print on `epoch < 3 and step == 0`; includes 2 shape asserts that fail loudly on concat/mismatch bugs |
| **Pitfall 1** missing mask for xd_i3d | Defensive `torch.ones(i3d.shape[0], i3d.shape[1], ...)` in both `_split_labels_i3d` and `train_one_epoch_i3d` — explicit, not inherited from collate |
| **Pitfall 4** 5-crop bag-size audit | 2 shape asserts in `train_one_epoch_i3d` audit block: `n_normal == abn.shape[0]` and `i3d.shape[0] == 2 * n_normal` |
| **TRN-03** determinism | Unchanged — `set_deterministic(cfg['seed'])` at `src/train.py:281` covers both dispatch paths; CUBLAS env var at lines 4-5 is path-agnostic |
| **CSV/wandb logging contract** | Unchanged — both paths emit the same `{train/loss, val/loss, lr}` keys via the shared `CSVLogger` + `WandbLogger` instances |

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. Phase 4b Plan 03 inherits Phase 4b + Phase 4 security posture:

- T-4b-08 (Tampering / polymorphic branch leakage) — **mitigated**: dispatch is a single `if/else` on `cfg.get("dataset") == "xd_i3d"`; the two paths share NO state; `train_one_epoch_i3d` imports nothing from `src/eval/` (C3 preserved per Phase 4 D-07); per-function `grep` verified via acceptance criteria.
- T-4b-09 (Info disclosure / D-12 audit log) — **accepted**: `[i3d_audit]` line prints batch shapes and counts; no PII, no secrets; goes to stderr (not a network sink).
- T-4b-10 (DoS / silent NaN loss) — **mitigated**: `mil_ranking_loss` requires `mask` arg (enforced by function signature); mask synthesis in `train_one_epoch_i3d` + `_split_labels_i3d` defensively uses `torch.ones(...)`; D-12 shape assertions raise AssertionError on first audit step if shape contract is violated, halting training loudly.

## Self-Check: PASSED

**Files created:**
- `tests/test_train_i3d.py` — FOUND (`test -f` exit 0)

**Files modified:**
- `src/train.py` — FOUND (368 lines total after +162 / -5 diff verified via `git show --stat 3d5bdae`)

**Commits:**
- `3d5bdae` — FOUND in `git log --oneline -5` (Task 1: feat(04b-03) add xd_i3d training dispatch to src/train.py)
- `865c59f` — FOUND in `git log --oneline -5` (Task 2: test(04b-03) add tests/test_train_i3d.py (3 tests, all passing))

**Public surface:**
- `train_one_epoch_i3d` — importable from `src.train` (verified via `python -c "from src.train import train_one_epoch_i3d; print('OK')"`)
- `validate_i3d` — importable from `src.train`
- `_split_labels_i3d` — importable from `src.train`
- `train_one_epoch`, `validate`, `_split_labels` — all still importable (UCF fusion path preserved)
- `build_dataloaders_i3d` — imported into `src.train` namespace

**Acceptance verify command:**
```
$ python -c "from src.train import train_one_epoch_i3d, validate_i3d, _split_labels_i3d, train_one_epoch, validate, _split_labels; import inspect; s1 = inspect.signature(validate); s2 = inspect.signature(validate_i3d); assert list(s1.parameters.keys()) == list(s2.parameters.keys()); print('OK')"
OK
```
