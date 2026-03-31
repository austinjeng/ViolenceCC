---
phase: 01-environment
plan: 03
subsystem: infra
tags: [ctrgcn, pyskl, mmcv, pytorch, pytest, weights, conda]

# Dependency graph
requires:
  - phase: 01-02
    provides: vcc-ctrgcn conda environment with PYSKL installed and all three envs operational

provides:
  - CTR-GCN NTU120 HRNet 2D pretrained weights (j.pth, b.pth, jm.pth, bm.pth) at data/weights/ctrgcn/
  - Passing smoke test confirming CTRGCN backbone produces (1,256) features from synthetic COCO-17 input
  - Exact pinned versions in all three requirements files (reproducibility record per D-08)

affects: [02-feature-extraction, all phases using CTR-GCN backbone]

# Tech tracking
tech-stack:
  added: [fvcore==0.1.5.post20221221, liblzma (conda-forge)]
  patterns: [CTRGCN input shape (N,M,T,V,C) with M=2 persons; pool backbone output over M/T/V to get (N,256)]

key-files:
  created:
    - tests/conftest.py
    - tests/test_ctrgcn_smoke.py
  modified:
    - envs/requirements-skeleton.txt
    - envs/requirements-ctrgcn.txt
    - envs/requirements-main.txt

key-decisions:
  - "CTRGCN.forward() expects (N, M, T, V, C) not (N, C, T, V, M) — confirmed from source code"
  - "NTU120 HRNet checkpoint requires M=2 persons (data_bn has 102=2*17*3 channels)"
  - "PYSKL checkpoints are plain OrderedDicts (no state_dict wrapper); load directly with strict=False"
  - "numpy must be pinned to <2 in vcc-ctrgcn; mmcv-full 1.7.0 was compiled against NumPy 1.x"
  - "fvcore required by PYSKL's smp.py but was missing from install; added to requirements-ctrgcn.txt"

patterns-established:
  - "CTR-GCN feature extraction: input (N,2,T,17,3) -> backbone -> pool(M,T,V) -> (N,256)"
  - "Test fixtures in conftest.py; smoke tests in tests/test_ctrgcn_smoke.py"

requirements-completed: [ENV-02]

# Metrics
duration: 35min
completed: 2026-03-31
---

# Phase 01 Plan 03: CTR-GCN Weights and Smoke Test Summary

**CTR-GCN NTU120 HRNet J-stream backbone verified: synthetic COCO-17 input (N=1, M=2, T=64, V=17, C=3) produces clean (1, 256) features with no NaN/Inf and nonzero variance**

## Performance

- **Duration:** 35 min
- **Started:** 2026-03-31T15:50:00Z
- **Completed:** 2026-03-31T16:25:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Downloaded all 4 CTR-GCN NTU120 HRNet 2D pretrained weight files (~6.1 MB each, verified live downloads)
- Implemented and passed 4-test smoke test suite confirming CTRGCN backbone produces (1, 256) features
- Froze all three conda environment requirements with exact pinned versions for reproducibility per D-08
- Discovered and documented critical PYSKL API contract (M=2 person requirement)

## Task Commits

Each task was committed atomically:

1. **Task 1: Download CTR-GCN weights and create smoke test** - `c5b7808` (feat)
2. **Task 2: Freeze environment state into requirements files** - `2d6f9df` (chore)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `tests/conftest.py` - Shared pytest fixtures: weight_dir and pyskl_config_dir path fixtures
- `tests/test_ctrgcn_smoke.py` - 4 smoke tests verifying CTR-GCN (1,256) output with no NaN/Inf/collapse
- `envs/requirements-skeleton.txt` - Pinned: rtmlib 0.0.15, onnxruntime-gpu 1.24.4, numpy 2.4.4
- `envs/requirements-ctrgcn.txt` - Pinned: mmcv-full 1.7.0, numpy 1.26.4, fvcore 0.1.5
- `envs/requirements-main.txt` - Pinned: torch 2.6.0+cu124, open-clip-torch 3.3.0, timm 1.0.26

## Decisions Made

- CTRGCN.forward() expects `(N, M, T, V, C)` shape — confirmed from source code at D:/libs/pyskl/pyskl/models/gcns/ctrgcn.py:84. Pool backbone output over dims [1, 3, 4] (M, T, V) to produce (N, 256).
- The NTU120 HRNet checkpoint requires M=2 persons because data_bn was initialized with `num_person * in_channels * V = 2 * 3 * 17 = 102` channels. Synthetic inputs must include a zero-padded second person.
- PYSKL checkpoints are plain OrderedDicts (not nested under 'state_dict') — load directly.
- numpy must be pinned to <2.0 in vcc-ctrgcn because mmcv-full 1.7.0 compiled against NumPy 1.x C API; NumPy 2.x breaks the binary interface.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed liblzma conda package to fix DLL import error**
- **Found during:** Task 1 (first pytest run)
- **Issue:** `ImportError: DLL load failed while importing _lzma` — torchvision import chain requires lzma but the DLL was absent from vcc-ctrgcn
- **Fix:** `conda install -n vcc-ctrgcn -c conda-forge liblzma`
- **Files modified:** vcc-ctrgcn conda environment (no tracked files)
- **Verification:** ImportError resolved on next pytest run
- **Committed in:** c5b7808 (environment fix, not tracked in git)

**2. [Rule 3 - Blocking] Installed missing fvcore dependency**
- **Found during:** Task 1 (second pytest run after lzma fix)
- **Issue:** `ModuleNotFoundError: No module named 'fvcore'` — PYSKL's smp.py imports fvcore for FlopCountAnalysis but it was not installed
- **Fix:** `pip install fvcore` in vcc-ctrgcn; also added `fvcore==0.1.5.post20221221` to requirements-ctrgcn.txt
- **Files modified:** envs/requirements-ctrgcn.txt
- **Verification:** Import succeeds
- **Committed in:** 2d6f9df (included in requirements freeze)

**3. [Rule 3 - Blocking] Downgraded numpy to <2 in vcc-ctrgcn**
- **Found during:** Task 1 (second pytest run, alongside fvcore error)
- **Issue:** NumPy 2.2.6 was installed but mmcv-full 1.7.0 was compiled against NumPy 1.x; runtime warning indicated binary incompatibility
- **Fix:** `pip install "numpy<2"` → installed numpy 1.26.4
- **Files modified:** envs/requirements-ctrgcn.txt (pinned numpy==1.26.4)
- **Verification:** Warning gone; tests pass cleanly
- **Committed in:** 2d6f9df

**4. [Rule 1 - Bug] Fixed checkpoint loading (no 'state_dict' wrapper key)**
- **Found during:** Task 1 (third pytest run)
- **Issue:** Plan's template code used `checkpoint['state_dict']` but PYSKL checkpoints are plain OrderedDicts
- **Fix:** Updated load to use checkpoint directly with graceful fallback: `state_dict = checkpoint if isinstance(...) else checkpoint.get('state_dict', checkpoint)`
- **Files modified:** tests/test_ctrgcn_smoke.py
- **Verification:** Model loads successfully
- **Committed in:** c5b7808

**5. [Rule 1 - Bug] Fixed synthetic input shape: M=1 → M=2**
- **Found during:** Task 1 (fourth pytest run)
- **Issue:** Plan specified `(N=1, C=3, T=64, V=17, M=1)` but CTRGCN data_bn requires 102 = 2*17*3 channels (M=2). Input with M=1 caused `RuntimeError: running_mean should contain 51 elements not 102`.
- **Fix:** Changed synthetic input from `(1,1,64,17,3)` to `(1,2,64,17,3)` with person 1 zero-padded (matches FormatGCNInput behavior for single-person videos)
- **Files modified:** tests/test_ctrgcn_smoke.py, updated docstrings
- **Verification:** All 4 tests pass
- **Committed in:** c5b7808

---

**Total deviations:** 5 auto-fixed (2 blocking-install, 1 blocking-downgrade, 2 bug fixes)
**Impact on plan:** All fixes were necessary to make the vcc-ctrgcn environment work. The M=2 discovery is a critical API contract for Phase 2 feature extraction — extraction scripts MUST pass M=2 tensors to CTR-GCN backbone.

## Issues Encountered

- PYSKL's documented input contract `(N, C, T, V, M)` in some comments conflicts with actual `CTRGCN.forward()` source which expects `(N, M, T, V, C)`. Confirmed from source — use the source, not comments.
- The plan's `(N=1, C=3, T=64, V=17, M=1)` test shape was wrong for the NTU120 HRNet checkpoint. The checkpoint was trained on NTU-RGB+D with 2 persons per video.

## Known Stubs

None — all functionality is fully wired. Test uses real pretrained weights.

## Next Phase Readiness

Phase 2 (Feature Extraction Pipeline) can proceed with the following confirmed facts:
- CTR-GCN backbone operational in vcc-ctrgcn with NTU120 HRNet 2D weights
- Feature extraction must pass `(N, M=2, T, V=17, C=3)` tensors to backbone
- Pool over M, T, V dimensions to get per-clip 256-d feature vector
- Weights are at `data/weights/ctrgcn/` (j.pth for joint stream, primary stream for Phase 2)

ENV-02 formally satisfied.

## Self-Check: PASSED

All created files confirmed present. All commits verified in git history.

| Check | Result |
|-------|--------|
| tests/conftest.py | FOUND |
| tests/test_ctrgcn_smoke.py | FOUND |
| data/weights/ctrgcn/j.pth | FOUND |
| data/weights/ctrgcn/b.pth | FOUND |
| data/weights/ctrgcn/jm.pth | FOUND |
| data/weights/ctrgcn/bm.pth | FOUND |
| SUMMARY.md | FOUND |
| commit c5b7808 | FOUND |
| commit 2d6f9df | FOUND |

---
*Phase: 01-environment*
*Completed: 2026-03-31*
