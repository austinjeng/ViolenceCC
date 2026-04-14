---
phase: 03-model-architecture-training-infrastructure
plan: 03
subsystem: data
tags: [pytorch, dataset, dataloader, numpy, mil, windows-seed-worker]

# Dependency graph
requires:
  - phase: 02-feature-extraction-pipeline
    provides: per-video float32 .npy caches — skeleton [N,256], CLIP [N,1024], aligned per DATA-08
  - phase: 03-01 (wave-1 sibling)
    provides: src/utils/seed.py (seed_worker, make_generator); tests/conftest.py fixtures (tmp_feature_dir, smoke_cfg, synth_*); pyproject.toml
provides:
  - src.data.MILFeatureDataset — D-09 segment sampling + D-10 pad+mask + D-12 full-length test mode
  - src.data.build_dataloaders — paired (nor, abn) train loaders + val loader per D-04
  - tests/test_dataset.py — 10 tests (4 VALIDATION.md-required + 6 invariant extras)
  - UCF/XD label-parsing functions covering both real Phase 2 split ids and plan test fixtures
affects: [03-04, 03-05, 03-06, 04-baseline-evaluation, 05-tta-infrastructure]

# Tech tracking
tech-stack:
  added: []  # No new dependencies; uses torch.utils.data, numpy already in vcc-main
  patterns:
    - "Skip-at-load filtering for zero-snippet videos (172 UCF sub-64-frame) — mitigates Phase 2 UAT note"
    - "DATA-08 alignment assertion in __getitem__ with video_id embedded in error message"
    - "Import shim pattern for parallel-wave imports (src.utils.seed with inline fallback)"

key-files:
  created:
    - src/data/dataset.py — MILFeatureDataset class + UCF/XD label parsers
    - src/data/loaders.py — build_dataloaders with paired nor/abn + val
    - tests/test_dataset.py — 10 tests covering D-04/D-09/D-10/D-12 and invariants
  modified:
    - src/data/__init__.py — re-export public API

key-decisions:
  - "Expand UCF normal prefix from plan literal 'Normal_Videos_event' to 'Normal_Videos' so both real Phase 2 ids (Normal_Videos001) and synthetic test ids are classified correctly"
  - "Use np.load(..., mmap_mode='r') for zero-snippet detection so startup cost is O(header-read) not O(full-array) on 3000+ video splits"
  - "Import shim with inline fallback for src.utils.seed — lets this worktree run standalone while staying canonical post wave-1 merge"
  - "Val loader returns a single DataLoader (not split by label) — Plan 06 training loop splits each val batch into nor/abn halves internally"

patterns-established:
  - "Per-video feature cache read: np.load(dir / f'{vid}.npy') — direct, dtype already float32 per Phase 2 D-06"
  - "D-09 segment math: np.linspace(0, N, T+1, dtype=np.int64) with max(lo+1, hi) guard against degenerate segments"
  - "D-10 mask propagation: mask[N:] = 0.0 — downstream MIL top-k masks padded positions to -inf (Plan 02 contract)"

requirements-completed: [MOD-02]

# Metrics
duration: 14min
completed: 2026-04-14
---

# Phase 3 Plan 03: MILFeatureDataset + Paired DataLoaders Summary

**Phase 2 → Phase 3 data interface: per-video .npy reader with D-09 segment sampling, D-10 zero-pad+mask, D-12 full-length test mode, D-04 paired nor/abn DataLoaders, and strict DATA-08 alignment enforcement.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-04-14T08:00Z (approx)
- **Completed:** 2026-04-14T08:14Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files created:** 3 (dataset.py, loaders.py, test_dataset.py)
- **Files modified:** 1 (src/data/__init__.py re-export)

## Accomplishments

- `MILFeatureDataset` reads per-video float32 .npy caches and returns a uniform dict `{skel:[T,256], clip:[T,1024], mask:[T], label, video_id}` in train/val modes, or `[N,...]` in test mode.
- D-09 32-segment uniform sub-sample implemented via `np.linspace(0, N, T+1, dtype=np.int64)` with `np.random.randint(lo, max(lo+1, hi))` for each of the 32 segments.
- D-10 zero-pad + mask with `mask[N:] = 0.0` so downstream MIL top-k (masked to -inf, Plan 02) cannot select padded positions.
- Zero-snippet videos filtered at construction time via `mmap_mode='r'` peek at header shape — addresses the Phase 2 UAT note that 172 UCF sub-64-frame videos produce empty .npy files.
- DATA-08 alignment invariant enforced in `__getitem__` (`assert skel.shape[0] == clip.shape[0]`, video_id in message).
- D-12 test mode returns full-length tensors without sub-sampling so Phase 4 frame-level AUC/AP has one score per snippet.
- `build_dataloaders` yields the RTFM/MGFN-convention paired `(nor_loader, abn_loader)` with independent generators (seed, seed+1) + `drop_last=True` to keep B=16 ranking pair contract clean.
- UCF label parsing widened to `startswith("Normal_Videos")` so real Phase 2 ids (`Normal_Videos001`, `Normal_Videos_event_123_x264`) AND synthetic test ids are both labeled 0.
- XD label parsing: `endswith("_label_A")` after optional `.mp4` strip, matching the Phase 2 convention.
- Import shim lets the module load standalone in this parallel worktree — `src.utils.seed` (Plan 03-01) is preferred; inline RESEARCH.md §2.5 fallback activates when the sibling plan hasn't merged yet.

## Task Commits

Each task committed atomically:

1. **Task 1: RED — tests/test_dataset.py** — `7ccfbe0` (test)
2. **Task 2: GREEN — MILFeatureDataset + build_dataloaders** — `7440261` (feat)

## Files Created/Modified

- `src/data/dataset.py` (created, 196 lines) — `MILFeatureDataset` class, `_parse_label_ucf`, `_parse_label_xd`, `_LABEL_PARSERS` dispatch, `_is_loadable` mmap-header peek, `_sample_or_pad` D-09/D-10 logic.
- `src/data/loaders.py` (created, 138 lines) — `build_dataloaders(cfg)`, import shim with inline `seed_worker` / `make_generator` fallback mirroring RESEARCH.md §2.5.
- `src/data/__init__.py` (modified) — re-exports `MILFeatureDataset`, `build_dataloaders`.
- `tests/test_dataset.py` (created, 304 lines) — 10 pytest tests: `test_train_resample_long`, `test_train_pad_short`, `test_skip_empty_videos`, `test_label_parsing_ucf`, `test_label_parsing_xd`, `test_alignment_assertion_on_mismatch`, `test_test_mode_returns_full_length`, `test_deterministic_sampling`, `test_paired_loader`, `test_drop_last_prevents_partial_batch`.

## Public API (for Plans 04/05/06)

```python
from src.data import MILFeatureDataset, build_dataloaders

# Single dataset construction:
ds = MILFeatureDataset(
    split_file="data/splits/ucf_train.txt",
    skel_dir="E:/features/ucf/skeleton",
    clip_dir="E:/features/ucf/clip",
    T=32,                       # target snippet count in train/val
    mode="train",               # or "val" or "test"
    seed=42,
    dataset="ucf",              # or "xd"
)
item = ds[0]
# item = {"skel": [T,256] float32, "clip": [T,1024] float32,
#         "mask": [T] float32, "label": 0.0 or 1.0, "video_id": str}

# Paired DataLoaders (D-04):
(nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
# cfg schema:
#   cfg["dataset"]                      "ucf" or "xd"
#   cfg["seed"]                         int
#   cfg["paths"]["splits_dir"]          dir containing {dataset}_train.txt, {dataset}_val.txt
#   cfg["paths"]["skeleton_features"]   dir of {video_id}.npy skel caches
#   cfg["paths"]["clip_features"]       dir of {video_id}.npy clip caches
#   cfg["data"]["T"]                    default 32
#   cfg["data"]["batch_size"]           16 per D-04
#   cfg["data"]["num_workers"]          typical 0 on Windows CI
#   cfg["data"]["pin_memory"]           bool, optional
```

### D-09 Segment Math (canonical reference for Plan 06)

For N >= T (typically T=32):
```python
segs = np.linspace(0, N, T + 1, dtype=np.int64)
for i in range(T):
    lo = int(segs[i])
    hi = max(lo + 1, int(segs[i + 1]))      # guard against degenerate
    idxs[i] = np.random.randint(lo, hi)     # uniform within segment
```

### D-10 Pad Math

For N < T:
```python
skel_pad = np.zeros((T, 256), dtype=np.float32)
clip_pad = np.zeros((T, 1024), dtype=np.float32)
skel_pad[:N] = skel.astype(np.float32)
clip_pad[:N] = clip.astype(np.float32)
mask = torch.ones(T, dtype=torch.float32)
mask[N:] = 0.0  # downstream MIL top-k uses masked_fill(-inf) on these
```

### Label Parsing Rules

| Dataset | Rule | Returns 0 | Returns 1 |
|---------|------|-----------|-----------|
| `ucf`   | `video_id.startswith("Normal_Videos")` | `Normal_Videos001`, `Normal_Videos_event_123_x264` | `Abuse001`, `Fighting042_x264`, `Assault003` |
| `xd`    | `base.endswith("_label_A")` after optional `.mp4` strip | `A.Movie.1999__00-01-00_00-02-00_label_A` | `Fight__..._label_B1`, `Riot__..._label_G`, `wangted.2008__..._label_B2-B6-0` |

### DATA-08 Alignment Guard

`__getitem__` contains (verbatim):
```python
assert skel.shape[0] == clip.shape[0], (
    f"Alignment mismatch for {vid}: skel N={skel.shape[0]} "
    f"vs clip N={clip.shape[0]} (DATA-08 must have caught this)"
)
```
— video_id in the error so a regression in Phase 2 extraction is immediately traceable.

## Decisions Made

- **Widen UCF normal prefix to `"Normal_Videos"`** (instead of plan's literal `"Normal_Videos_event"`): the plan test fixtures use `Normal_Videos_event_*_x264` but real Phase 2 splits use `Normal_Videos001`. The broader prefix is the only value that labels both correctly. Added `"Normal_Videos001"` to `test_label_parsing_ucf` to lock in the real-data case.
- **Import shim for `src.utils.seed`**: during parallel wave-1 execution, Plan 01 (src/utils/seed.py) has not merged. The loader prefers the canonical module; inline RESEARCH.md §2.5 fallback ensures this worktree can load `build_dataloaders` standalone.
- **Val loader single, not paired**: `build_dataloaders` returns one val DataLoader at `batch_size * 2` rather than a paired (nor_val, abn_val) tuple. Plan 06's training loop splits each val batch into nor/abn halves via the `label` field. This keeps the current interface minimal.
- **Use `np.load(..., mmap_mode='r')` for empty-file detection**: peeks header without copying full array. On the 3360-video XD split this avoids ~10 GB of read on startup.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] UCF label prefix too narrow**
- **Found during:** Task 1 writing (reviewing real UCF split content)
- **Issue:** The plan's test_label_parsing_ucf and the canonical `_parse_label_ucf` specify prefix `"Normal_Videos_event"`. Actual Phase 2 UCF splits contain `Normal_Videos001`, `Normal_Videos002`, etc. — NOT `Normal_Videos_event_*`. Literal plan prefix would label all 680 real normal UCF train videos as abnormal (label=1), breaking all downstream MIL training immediately.
- **Fix:** Used `video_id.startswith("Normal_Videos")` which matches both real Phase 2 ids and the plan's synthetic test ids (`Normal_Videos_event_*_x264`). Extended `test_label_parsing_ucf` to include `"Normal_Videos001"` alongside the synthetic id so the real-data case is locked in by test.
- **Files modified:** `src/data/dataset.py`, `tests/test_dataset.py`
- **Verification:** Standalone smoke script confirms both `Normal_Videos_event_123_x264` and `Normal_Videos001` return label 0; `Abuse001_x264`, `Fighting042_x264` return label 1.
- **Committed in:** `7ccfbe0` (test) + `7440261` (impl)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential correctness fix. Literal plan would have silently mislabeled every real UCF normal video as abnormal. No scope creep.

## Issues Encountered

- `tests/test_dataset.py` cannot run to GREEN in this worktree because Plan 01's pytest fixtures (`tmp_feature_dir`, `smoke_cfg`) live in a parallel worktree and haven't merged. **Mitigation:** built a standalone smoke harness that replays all 10 test behaviors with locally-constructed fixtures (PASS across all cases). The harness script was not committed (out of `files_modified` scope). Post wave-1 merge, `pytest tests/test_dataset.py -x` should go GREEN without further changes.

## Verification Performed

- `python -c "from src.data import MILFeatureDataset, build_dataloaders; print('imports ok')"` → `imports ok`.
- `pytest tests/test_dataset.py --collect-only` → 10 tests collected, no import errors.
- Standalone smoke script exercised all 10 test behaviors against in-memory synthetic `.npy` files; every case passed.
- Wave-1 regression: `pytest tests/test_splits.py -v` → 9 passed (pre-existing tests unaffected).
- Acceptance grep patterns all present:
  - `def _parse_label_ucf`, `def _parse_label_xd` in dataset.py
  - `np.linspace(0, N, T + 1` in dataset.py
  - `mask[N:] = 0.0` in dataset.py
  - `skel.shape[0] == clip.shape[0]` assertion with video_id in message
  - `skel.shape[0] == 0` empty-file filter
  - `drop_last=True` in loaders.py (twice — shared `common` dict + explicit mention in docstring)

## Next Phase Readiness

- Plan 03-04 (Skeleton-Only and CLIP-Only MIL head wrappers) can now consume `MILFeatureDataset` directly for forward-pass tests with real UCF .npy files.
- Plan 03-05 (Late Fusion + Gated Fusion) will consume `build_dataloaders` + MILFeatureDataset end-to-end.
- Plan 03-06 (training loop + reproducibility) will use both the paired train loaders and val loader; `test_deterministic_sampling` already locks in the random-within-segment reproducibility so bit-identical rerun testing in Plan 06 can trust the DataLoader side.
- No blockers for downstream plans post wave-1 merge.

## Self-Check: PASSED

Files verified present:
- `src/data/dataset.py` → FOUND
- `src/data/loaders.py` → FOUND
- `src/data/__init__.py` → FOUND (modified)
- `tests/test_dataset.py` → FOUND

Commits verified in `git log`:
- `7ccfbe0` → FOUND (test RED)
- `7440261` → FOUND (feat GREEN)

---
*Phase: 03-model-architecture-training-infrastructure*
*Completed: 2026-04-14*
