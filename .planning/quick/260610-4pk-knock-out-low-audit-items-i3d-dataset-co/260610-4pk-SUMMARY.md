---
quick_id: 260610-4pk
slug: knock-out-low-audit-items-i3d-dataset-co
status: complete
date: 2026-06-09
commit: ca4802a
---

# Quick Task 260610-4pk — Summary

Resolved the 4 LOW code/doc items from the 2026-06-09 audit. All confined to the
I3D/RTFM baseline path or comments; no headline, paper, or canonical-number change.

| # | File | Change |
|---|---|---|
| 1 | `src/data/i3d_dataset.py:60` | Split-file comprehension now skips `#` lines (`and not i.strip().startswith("#")`) — the 2 `# Excluded:` lines in xd_train.txt no longer inflate the startup "available" count. Mirrors `dataset.py:148`. |
| 2 | `src/data/i3d_dataset.py:_resample_T` | Replaced fixed `np.random.default_rng(0)` with the global RNG (`np.random.randint`) so sub-T sampling varies per epoch/crop (still reproducible via the train-time global seed). |
| 3 | `src/models/rtfm_i3d.py:5` | Docstring corrected — no "L2-norm FM head"; the forward is LayerNorm + standard sigmoid MILHead, top-k handled in the MIL loss. |
| 4 | `src/evaluate.py` (xd_i3d + xd fusion) | Scoped the "bit-identical to gt.npy (2,330,384 frames)" comment to the stride-16 xd_i3d path; documented that the xd fusion path's `n_frames=len(scores)*64` truncates ~0.74% trailing frames (2,313,024), AP-negligible. |

## Verification

- `py_compile` OK on all 3 files; **48 i3d/rtfm/loader/dataset tests pass**.
- 2 failing tests (`test_split_seed_reproducibility`, `test_no_test_split_access`) confirmed
  **PRE-EXISTING** — identical red on committed HEAD with these edits stashed out; they
  reference `test_loader.py`/`evaluate_tta.py`, untouched here. (Out of scope: a leakage-guard
  test that flags legit eval-time test-split loads — flagged to Austin, not fixed.)

## Note

The 2 committed `rtfm_i3d` baseline rows in results-index.csv are non-paper and were produced
with the old sampling; they are not re-run. Future rtfm_i3d training uses the improved sampling.

## Commit

`ca4802a` fix(i3d,docs): resolve 4 LOW audit items (code/doc hygiene)
