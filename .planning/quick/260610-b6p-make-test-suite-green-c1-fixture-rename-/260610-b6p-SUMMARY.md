---
quick_id: 260610-b6p
status: complete
date: 2026-06-10
commit: cb625fc
---

# Quick Task 260610-b6p: Make the test suite green — SUMMARY

**Status:** Complete. Full suite **321 passed, 0 failed** (was 6 failed / 315 passed
after Batch A). Code committed `cb625fc`.

## Fixes

- **C1** (`tests/fixtures/synthetic_eval.py`) — renamed ALL 10 synthetic UCF fixture
  ids to `Synth*`. The review flagged only `Abuse028`, but I verified **6** of the
  10 ids are real UCF ids in `data/ucf_total_frames.json` (Abuse028=142, Arson011=127,
  Assault010=1618, Fighting003=311, Shooting007=143, Normal_Videos_003=283). Each
  hijacked `n_frames` from the manifest via `evaluate.py:330`, breaking the synthetic
  snippet→frame grid (regression from M3 commit 4ddda56). Category comes from the
  annotation column, not the id, so the rename is label-safe. Fixes the 3
  `test_evaluate_cli.py` failures. Regression-guard comment added.
- **C2** (`src/data/loaders.py:346`) — i3d val loader `shuffle=False`→`True` (seeded
  `g_val` already wired). Matches the fusion-path fix (commit 0999033) and the project
  convention (val loaders MUST shuffle; `validate()` skips single-class batches → an
  unshuffled val set biases MIL val loss → affects early-stopping/selection for the 2
  xd_i3d baseline rows). Latent bug; no covering test (verified by compile + full suite).
- **C3a** (`scripts/create_splits.py`) — added `XD_TRAIN_EXCLUSIONS` (2 ids + reasons,
  insertion order = committed header order) and rewrote the `xd_train.txt` write to emit
  the comment header + `sorted(train_ids − exclusions)`. Both excluded videos enumerate
  from E:/ and land in TRAIN (xd_val/xd_test already reproduced), so only the train
  write needed it. **`--verify` now PASSES (all 6 files byte-identical).** The committed
  `data/splits/xd_train.txt` was NOT modified. Fixes `test_split_seed_reproducibility`.
- **C3b** (`tests/test_train_integration.py::test_no_test_split_access`) — scoped the
  leakage scanner to TRAINING modules: skip `src/eval/` and `src/tta/`, which
  legitimately load `*_test.txt` for inference/adaptation (the only 2 src files
  containing `_test.txt`: `src/tta/evaluate_tta.py`, `src/eval/test_loader.py`). The
  guard targets training-side leakage; the self-test variant is unaffected.
- **TTA pin** (`tests/test_run_ablations_tta.py`) — `500`→`680` (20+80+400 CLIP grids +
  3×60 backbone source/tent/sar) + docstring + fn name `..._is_500`→`..._is_680`.

## Verification

- `python scripts/create_splits.py --verify` → **Verification PASSED** (all 6 OK).
- 4 affected test files → 33 passed.
- Full suite → **321 passed, 0 failed**, 0 warnings of concern.

## Notes

- Did NOT touch the committed split files (source of truth) — only the generator.
- C2 changes early-stopping/selection for the 2 xd_i3d baseline rows in results-index;
  those are baseline (non-headline) rows. Re-running them is optional and out of scope.
