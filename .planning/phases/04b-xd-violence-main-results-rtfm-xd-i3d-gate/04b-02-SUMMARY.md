---
phase: 04b
plan: 02
subsystem: data
tags: [data, dataloader, i3d, collate, mil-bag, xd-violence, rtfm]
requires:
  - src/data/i3d_dataset.py::I3DFeatureDataset
  - src/utils/seed.py::seed_worker,make_generator
provides:
  - src/data/loaders.py::build_dataloaders_i3d
  - src/data/loaders.py::collate_i3d_train
affects:
  - src/data/loaders.py (existing build_dataloaders UNCHANGED per D-04)
tech_stack:
  added: []
  patterns:
    - "D-04 parallel-functions (not polymorphic dispatch)"
    - "D-05 crop-as-sample flatten via custom collate"
    - "D-06 _label_A suffix partitioning"
    - "Pitfall 7 module-scope collate_fn for Windows spawn"
key_files:
  created:
    - tests/test_loaders_i3d.py (155 lines, 5 tests)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/deferred-items.md
  modified:
    - src/data/loaders.py (+191 lines; added collate_i3d_train + build_dataloaders_i3d)
decisions:
  - "Kept existing build_dataloaders unchanged; added parallel build_dataloaders_i3d (D-04)"
  - "Hardcoded xd_train.txt / xd_val.txt (Open Question #2 resolution)"
  - "Hard-asserted len(val_abn) > 0 to fail loudly on filter collapse (Open Question #1)"
  - "Used repeat_interleave(5) for label replication (not repeat) to guarantee consecutive ordering (Pitfall 4)"
  - "collate_i3d_train at module scope per Windows spawn / persistent_workers requirement (Pitfall 7)"
metrics:
  duration_min: 9
  tasks_completed: 2
  tests_added: 5
  tests_passing: 5
  files_created: 2
  files_modified: 1
  lines_added: 346
  completed: 2026-04-15
commits:
  - 8255e0a (Task 1): feat(04b-02) add build_dataloaders_i3d + collate_i3d_train
  - 7b12ffa (Task 2): test(04b-02) 5 unit tests + deferred-items for pre-existing failure
---

# Phase 4b Plan 02: build_dataloaders_i3d + collate_i3d_train Summary

Wired a dedicated `xd_i3d` DataLoader path (`build_dataloaders_i3d` + module-scope `collate_i3d_train`) alongside the untouched fusion path, plus 5 passing unit tests covering shape, partitioning, label replication, mask synthesis, and fixture integration.

## What Changed

Added two module-level functions to `src/data/loaders.py`:

1. **`collate_i3d_train(batch_list)`** — D-05 5-crop flattener. Takes a list of B dicts from `I3DFeatureDataset` (each with `i3d: [5, T, 1024]`, `label: float`, `video_id: str`) and returns a collated batch with:
   - `i3d: [B*5, T, 1024]` via `torch.stack` + `reshape`
   - `label: [B*5] float32` via `repeat_interleave(5)` — consecutive replication
   - `mask: [B*5, T] float32` — all ones (Pitfall 1 guard; `mil_ranking_loss` requires mask)
   - `video_id: List[str]` length `B*5` — each id repeated 5x consecutively

   Module-scope placement is required by Pitfall 7 (Windows `spawn` + DataLoader `persistent_workers` must pickle the collate_fn).

2. **`build_dataloaders_i3d(cfg)`** — Parallel to `build_dataloaders` per D-04. Returns `((nor_loader, abn_loader), val_loader)` where:
   - Train/val datasets are `I3DFeatureDataset` instances constructed with hardcoded `xd_train.txt` / `xd_val.txt` (Open Question #2 — the pattern `f"{cfg['dataset']}_val.txt"` would resolve to non-existent `xd_i3d_val.txt`).
   - Partitioning uses `.endswith("_label_A")` on `train_ds.video_ids` directly (D-06) — `I3DFeatureDataset` exposes no `.labels` dict.
   - Three hard assertions prevent silent failure: `len(nor_idx) > 0`, `len(abn_idx) > 0`, `len(val_abn) > 0` (Open Question #1).
   - All loaders wire `collate_fn=collate_i3d_train` so the 5-crop dim flattens into the batch dim.
   - Independent `torch.Generator` seeds (`seed`, `seed+1`, `seed+2`) mirror the existing fusion-path determinism pattern.

Added `tests/test_loaders_i3d.py` with 5 tests:

| Test | Requirement Row | What It Guards |
|------|-----------------|----------------|
| `test_build_dataloaders_i3d_shape` | 4b-02-01 | Returns `((nor, abn), val)` tuple; first batch shape = `(bs*5, 32, 1024)` |
| `test_collate_flattens_crops` | 4b-02-02 | `[B, 5, T, 1024]` -> `[B*5, T, 1024]` flatten |
| `test_collate_label_replication` | Pitfall 4 | `[0,0,1]` -> `[0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1]` (consecutive, not interleaved) |
| `test_collate_mask_all_ones` | Pitfall 1 | `mask.sum() == B*5*T`, dtype `float32` |
| `test_nor_abn_partition_nonempty` | 4b-02-03 | `nor_loader` yields label=0; `abn_loader` yields label=1 |

## Commits

| Hash | Task | Scope |
|------|------|-------|
| `8255e0a` | Task 1 | `feat(04b-02): add build_dataloaders_i3d + collate_i3d_train for xd_i3d dispatch` — +191 lines to `src/data/loaders.py` |
| `7b12ffa` | Task 2 | `test(04b-02): add 5 unit tests for build_dataloaders_i3d + collate_i3d_train` — +155 lines `tests/test_loaders_i3d.py` + deferred-items.md |

## Test Results

```
$ C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_loaders_i3d.py -v --tb=short
...
tests/test_loaders_i3d.py::test_build_dataloaders_i3d_shape PASSED       [ 20%]
tests/test_loaders_i3d.py::test_collate_flattens_crops PASSED            [ 40%]
tests/test_loaders_i3d.py::test_collate_label_replication PASSED         [ 60%]
tests/test_loaders_i3d.py::test_collate_mask_all_ones PASSED             [ 80%]
tests/test_loaders_i3d.py::test_nor_abn_partition_nonempty PASSED        [100%]

============================== 5 passed in 3.57s ==============================
```

**Regression check (core related tests):**
```
$ pytest tests/test_dataset.py tests/test_i3d_dataset.py tests/test_train.py \
         tests/test_mil_loss.py tests/test_models.py tests/test_mil_head.py \
         tests/test_skel_agg.py -x --tb=short
============================= 74 passed in 17.98s =============================
```

All 74 tests in core related paths (MILFeatureDataset, I3DFeatureDataset, train.py CLI, MIL losses, models, MIL head, skeleton aggregation) pass. No regression to the existing UCF/XD fusion path.

## Acceptance Criteria

**Plan-level:**
- [x] `src/data/loaders.py` contains `def build_dataloaders_i3d` + `def collate_i3d_train` at module scope
- [x] `src/data/loaders.py::build_dataloaders` (existing) signature and body UNCHANGED
- [x] `tests/test_loaders_i3d.py` has 5 tests, all passing
- [x] `build_dataloaders_i3d` honors `cfg.data.batch_size=3` (read via `data_cfg["batch_size"]`; not hardcoded)
- [x] `collate_i3d_train` emits `mask` (all ones), labels replicated 5x consecutively, video_id list length `B*5`
- [x] Val abnormal partition assertion fires loudly if the split filter collapses (Open Question #1)
- [x] No regression to fusion-path test suite

**Task 1 acceptance:**
- [x] `grep -c "def collate_i3d_train"` = 1
- [x] `grep -c "def build_dataloaders_i3d"` = 1
- [x] `grep -c "def build_dataloaders"` = 2 (original + _i3d suffix match)
- [x] Original `def build_dataloaders(cfg` line still present (line 107)
- [x] Module imports cleanly: `from src.data.loaders import build_dataloaders_i3d, collate_i3d_train, build_dataloaders`
- [x] `from src.data.i3d_dataset import I3DFeatureDataset` imported
- [x] `repeat_interleave` used (not `.repeat`)
- [x] `xd_train.txt` + `xd_val.txt` hardcoded
- [x] Val abnormal assertion present
- [x] `torch.ones` used for mask

**Task 2 acceptance:**
- [x] `tests/test_loaders_i3d.py` exists
- [x] 5 `def test_*` functions present with exact required names
- [x] All 5 pass
- [x] Uses `synthetic_i3d_features` fixture
- [x] Imports `build_dataloaders_i3d` + `collate_i3d_train` from `src.data.loaders`

## Deviations from Plan

**None — plan executed exactly as written.**

The plan's code drafts for `collate_i3d_train` and `build_dataloaders_i3d` were applied verbatim (with minor docstring rewording for clarity). The test file was implemented per the plan's exact specification including the `_build_cfg` helper that synthesizes `xd_val.txt` on the fly (since the `synthetic_i3d_features` fixture ships only `xd_train.txt` and `xd_test.txt`).

No Rule 1/2/3/4 auto-fixes were needed.

## Deferred Issues

### Pre-existing failure: `tests/test_train_integration.py::test_no_test_split_access`

Discovered during the full-suite regression check. Verified reproduces at base commit `31abfae` (before my Task 1), so this is NOT a regression from Plan 04b-02. Root cause: the C3 AST scan iterates ALL files under `src/` and flags `src/eval/test_loader.py` for containing `xd_test.txt`/`ucf_test.txt` string literals — but that module IS the canonical test loader, which is by definition allowed to reference the test split.

**Action:** Logged to `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/deferred-items.md` for a future test-infra cleanup plan. Out of scope for 04b-02 per the executor's SCOPE BOUNDARY rule.

## Authentication Gates

None encountered. Task is pure Python code + unit tests; no external services, no credential prompts.

## Decision Traceability

| Decision | Implementation |
|----------|----------------|
| **D-04** parallel functions (not polymorphic) | `build_dataloaders_i3d` added alongside `build_dataloaders`; original UNCHANGED |
| **D-05** crop-as-sample collate | `collate_i3d_train` flattens `[B, 5, T, 1024]` -> `[B*5, T, 1024]` via `torch.stack` + `reshape`; labels via `repeat_interleave(5)` |
| **D-06** `_label_A` suffix partitioning | `nor_idx = [i for i, v in enumerate(train_ds.video_ids) if v.endswith("_label_A")]` — no dependence on absent `.labels` attribute |
| **Pitfall 1** missing mask for xd_i3d | `collate_i3d_train` synthesizes `mask = torch.ones(B*5, T, dtype=torch.float32)` |
| **Pitfall 3** 5-crop × k_topk=3 budgeting | `bs = data_cfg["batch_size"]` read from config (3 per `rtfm_i3d.yaml`); NOT hardcoded |
| **Pitfall 4** label replication drift | `.repeat_interleave(5)` + dedicated `test_collate_label_replication` guard |
| **Pitfall 7** Windows spawn pickling | `collate_i3d_train` at module scope (not nested inside `build_dataloaders_i3d`) |
| **Open Question #1** val abnormal coverage | Hard assertion `len(val_abn) > 0` with explicit error message |
| **Open Question #2** xd_val.txt explicit path | Hardcoded `f"{paths['splits_dir']}/xd_val.txt"` (not `{dataset}_val.txt` pattern) |

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced. Phase 4b Plan 02 inherits Phase 4 security posture — only adds parallel in-module functions consuming an already-audited dataset (`I3DFeatureDataset`).

## Self-Check: PASSED

**Files created:**
- `tests/test_loaders_i3d.py` — FOUND
- `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/deferred-items.md` — FOUND

**Files modified:**
- `src/data/loaders.py` — FOUND (+191 lines verified via `git show --stat 8255e0a`)

**Commits:**
- `8255e0a` — FOUND in `git log --oneline` (Task 1)
- `7b12ffa` — FOUND in `git log --oneline` (Task 2)

**Public surface:**
- `build_dataloaders_i3d` — importable from `src.data.loaders`
- `collate_i3d_train` — importable from `src.data.loaders`
- `build_dataloaders` — still importable (unchanged)
