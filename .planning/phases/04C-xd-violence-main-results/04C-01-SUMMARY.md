---
phase: 04C-xd-violence-main-results
plan: 01
subsystem: evaluation, configs, orchestration
tags: [xd-violence, configs, evaluate, split-cleanup, queues]
dependency_graph:
  requires: []
  provides: [xd-configs, xd-evaluate-branch, xd-split-cleaned, phase4c-queues]
  affects: [04C-02-PLAN, 04C-03-PLAN]
tech_stack:
  added: []
  patterns: [dataset-routing-branch, comment-safe-split-loader]
key_files:
  created:
    - configs/skeleton_only_xd.yaml
    - configs/clip_only_xd.yaml
    - configs/late_fusion_xd.yaml
    - configs/gated_fusion_xd.yaml
    - configs/gated_fusion_xd_2person.yaml
    - configs/gated_fusion_xd_clip_mean.yaml
    - tests/test_evaluate_xd.py
  modified:
    - data/splits/xd_train.txt
    - src/data/dataset.py
    - src/evaluate.py
    - scripts/run_ablations.py
    - tests/test_run_ablations.py
decisions:
  - "XD configs use identical hyperparameters to UCF counterparts (D-04)"
  - "Comment-line skip in _load_split is backward-compatible with all existing splits"
  - "XD fusion branch uses snippet_window=64, upsample_factor=1 (not UCF's 10x upsample)"
metrics:
  duration: 9min
  completed: "2026-04-27T01:32:31+08:00"
  tasks: 2
  files: 12
---

# Phase 04C Plan 01: XD-Violence Tooling Preparation Summary

XD evaluation branch with snippet_window=64/upsample=1, 6 dataset-portable YAML configs, 3 orchestration queues, and cleaned split file excluding 2 featureless videos

## Task Results

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Clean XD split file + comment-safe loader + evaluate.py XD fusion branch | a5a51ba | data/splits/xd_train.txt, src/data/dataset.py, src/evaluate.py, tests/test_evaluate_xd.py |
| 2 | Create 6 XD YAML configs + 3 orchestration queues + update tests | 26e53dc | configs/*_xd*.yaml (6), scripts/run_ablations.py, tests/test_run_ablations.py |

## Key Changes

### Task 1: Critical evaluate.py Fix + Split Cleanup

**Split file cleanup (D-05):** Added 2-line comment header documenting excluded videos, removed `v=8cTqh9tMz_I__#1_label_A` (corrupt MP4, missing moov atom) and `v=Gm73TwtUyGY__#1_label_G-0-0` (34 frames, below 64-frame window). Result: 3358 video IDs + 2 comment lines = 3360 total lines.

**Comment-safe loader:** Updated `_load_split` in `src/data/dataset.py` to skip lines starting with `#`. Backward-compatible -- no existing split file uses comment lines.

**CRITICAL fix -- evaluate.py XD fusion branch:** Added `elif ds == "xd":` branch in `_build_frame_arrays` between the `xd_i3d` and UCF default paths. Without this fix, `dataset=xd` would fall through to the UCF path, using the wrong annotation file (`ucf_temporal.txt` instead of `xd_temporal.txt`), wrong `upsample_factor` (10 instead of 1), and wrong frame count calculation. The new branch uses `snippet_window=64` and `upsample_factor=1`, matching the skeleton+CLIP extraction parameters for XD-Violence.

**Tests:** Created `tests/test_evaluate_xd.py` with 4 tests: abnormal video labels, normal video zero labels, snippet_window=64 verification, and category parsing.

### Task 2: 6 XD Configs + 3 Queues

**Configs (D-01, D-04):** Created 6 flat self-contained YAML configs mirroring UCF counterparts with `dataset: xd` and XD feature paths. All `model:`, `data:`, and `train:` sections are byte-identical to UCF counterparts (identical hyperparameters, no per-dataset tuning).

**Queues (D-02):** Added `phase4c_main` (4 specs: skeleton_only, clip_only, late_fusion, gated_fusion), `phase4c_pooling` (2 specs: 2person, clip_mean), and `phase4c_seeds` (2 specs: seeds 123, 2024) to the QUEUES dict in `run_ablations.py`. Total unique run_names across all queues: 18 (10 existing + 8 new).

**Test updates:** Updated `test_queue_definitions` assertions to verify 18 total unique specs, added Phase 4c run_name spot checks, and updated `test_help_has_expected_queues` to check for 3 new queue names.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- 23/23 tests pass across test_evaluate_xd.py (4), test_evaluate_xd_i3d.py (4), test_evaluate_cli.py (3), test_run_ablations.py (12)
- All 6 XD configs parse without YAML errors and contain `dataset: xd`
- `xd_train.txt` has 3360 lines (2 comments + 3358 IDs)
- `run_ablations.py` contains all 3 new queue names (phase4c_main, phase4c_pooling, phase4c_seeds)

## Self-Check: PASSED

All 12 files verified present. Both commits (a5a51ba, 26e53dc) verified in git log.
