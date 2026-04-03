---
phase: 02-feature-extraction-pipeline
plan: 03
subsystem: data-pipeline
tags: [alignment-verification, ucf-crime, skeleton, ctrgcn, clip, full-extraction, onnxruntime-gpu, cudnn-fix]

requires:
  - phase: 02-feature-extraction-pipeline
    plan: 02
    provides: extract_ctrgcn.py and extract_clip.py validated on 3 Abuse videos

provides:
  - scripts/verify_alignment.py: post-extraction alignment check (n_skel==n_clip==n_boundary, NaN/Inf, variance, shapes)
  - scripts/extract_skeletons.py: cuDNN 12.8 PATH fix applied (GPU mode now working)
  - UCF-Crime skeleton extraction in progress: 33/1368 train videos done at time of plan commit

affects: [02-04-full-extraction, 03-model-architecture]

tech-stack:
  added:
    - numpy mmap_mode='r' for memory-efficient feature file verification
  patterns:
    - cuDNN 9.x for CUDA 12 installs to v9.8/bin/12.8/ not v9.8/bin/
    - PATH must be set before onnxruntime DLL loading (os.environ["PATH"] at module top)
    - Verification script exit code 0=all pass / 1=any failure for CI-style gating

key-files:
  created:
    - scripts/verify_alignment.py
  modified:
    - scripts/extract_skeletons.py (cuDNN PATH fix)
    - C:/Anaconda/envs/vcc-skeleton/etc/conda/activate.d/cudnn_path_fix.bat (new)

key-decisions:
  - "cuDNN 9.x CUDA 12 DLLs live in v9.8/bin/12.8/ not v9.8/bin/; PATH must include the 12.8 subdir"
  - "RTMPose GPU mode achieves 2-10s/video vs 128s/video CPU; PATH fix is required for feasible extraction"
  - "verify_alignment.py uses mmap_mode='r' for memory-efficient verification without loading full arrays"

metrics:
  duration: 23min
  completed: "2026-04-03T21:45:35Z"
  started: "2026-04-03T21:22:53Z"
  tasks: 2 (+ Task 3 checkpoint)
  files_modified: 3
---

# Phase 02 Plan 03: Alignment Verification and UCF-Crime Full Extraction Summary

**verify_alignment.py built with full shape/dtype/alignment/NaN/Inf/variance checks, cuDNN 12.8 PATH fix applied to extract_skeletons.py enabling GPU mode (2-10s/video vs 128s CPU), and UCF-Crime skeleton extraction launched in GPU mode**

## Performance

- **Duration:** ~23 min
- **Started:** 2026-04-03T21:22:53Z
- **Completed:** 2026-04-03T21:45:35Z
- **Tasks:** 2 complete (Task 3 is checkpoint:human-verify pending extraction completion)
- **Files modified:** 3 (1 created, 2 modified/added)

## Accomplishments

- `scripts/verify_alignment.py` built with full DATA-08 verification logic (520 lines)
  - Checks skeleton [N, 256] and CLIP [N, 1024] shapes, float32 dtype, NaN/Inf, variance
  - DATA-08 core: n_skel == n_clip == n_boundary for every video
  - CLI: `--dataset ucf|xd --split train|val|test|all --sample N --verbose`
  - Exit code 0 all pass / 1 any failures; PASS/FAIL/SKIP counts in report
  - Validated on 3 UCF-Crime Abuse videos (all PASS: Abuse001 n=4, Abuse002 n=1, Abuse003 n=5)
- cuDNN PATH fix: identified that cuDNN 9.x CUDA 12 DLLs live in `v9.8/bin/12.8/` not `v9.8/bin/`
  - Fixed `extract_skeletons.py` to prepend the correct subdir before onnxruntime loads
  - RTMPose now runs on CUDA: `SUCCESS: Model initialized with CUDA backend` confirmed
  - Speed: 2-10s/video on GPU vs 128s/video on CPU (12-60x speedup)
- UCF-Crime skeleton extraction launched in GPU mode: 33/1368 train videos extracted at time of commit

## Task Commits

Each task was committed atomically:

1. **Task 1: Build alignment verification script** - `92a88a1` (feat)
2. **Task 2: cuDNN PATH fix + pipeline launched** - `8ce23a6` (fix)

## Files Created/Modified

- `scripts/verify_alignment.py` — Full alignment verification (DATA-08)
  - Per-video: file existence, shape [N,256]/[N,1024], float32, n_skel==n_clip==n_boundary, NaN/Inf, variance
  - Report: PASS/FAIL/SKIP counts, failure details, summary statistics (snippet range, mean, norms)
  - Coverage check: compares feature file count vs split file video count
- `scripts/extract_skeletons.py` — cuDNN 12.8 PATH fix at module top
- `C:/Anaconda/envs/vcc-skeleton/etc/conda/activate.d/cudnn_path_fix.bat` — Conda activation script for persistent PATH fix

## Decisions Made

- cuDNN 9.x CUDA 12 installs DLLs to `v9.8/bin/12.8/` (a CUDA-version-specific subdirectory), not directly to `v9.8/bin/`. The system PATH had `v9.8/bin` but onnxruntime was loading `cudnn64_9.dll` from a subdirectory that wasn't on PATH. Adding `v9.8/bin/12.8` to PATH at the top of `extract_skeletons.py` (before any onnxruntime import) fixes the DLL load failure.
- verify_alignment.py uses `np.load(mmap_mode='r')` for memory efficiency; full array variance check requires `np.array(skel).var()` to materialize the array once per video, which is acceptable for verification purposes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] cuDNN 12.8 subdir missing from PATH blocks GPU mode in extract_skeletons.py**
- **Found during:** Task 2 (running Stage 1 skeleton extraction on train split)
- **Issue:** `extract_skeletons.py` launched but onnxruntime-gpu CUDA provider failed to load: `Error loading onnxruntime_providers_cuda.dll which depends on cudnn64_9.dll which is missing`. The system PATH included `C:/Program Files/NVIDIA/CUDNN/v9.8/bin` but not `v9.8/bin/12.8/` where the actual DLL lives. RTMPose fell back to CPU at ~128s/video (vs 2-10s GPU), making 1900-video extraction take ~68 hours instead of ~5 hours.
- **Fix:** Added `os.environ["PATH"] = r"C:\Program Files\NVIDIA\CUDNN\v9.8\bin\12.8" + ";" + PATH` at the top of `extract_skeletons.py` before any rtmlib/onnxruntime import. Also added `cudnn_path_fix.bat` to vcc-skeleton conda activate.d for persistent fix.
- **Verification:** `SUCCESS: Model initialized with CUDA backend` confirmed; inference runs at 2-10s/video.
- **Files modified:** scripts/extract_skeletons.py, conda activate.d/cudnn_path_fix.bat
- **Commits:** 8ce23a6

---

**Total deviations:** 1 auto-fixed (Rule 3 blocking issue)
**Impact on plan:** Critical fix. Without it, full extraction would take ~68 hours on CPU instead of ~5 hours on GPU, making the extraction infeasible within the project timeline.

## Extraction Status at Plan Commit

**Stage 1: Skeleton extraction (vcc-skeleton)**
- Status: IN PROGRESS (running as background job bv9stfr93)
- Train: 33/1368 videos (~2.4% done) at ~10s/video average → estimated completion ~3.5h
- Val/Test: not yet started (will start automatically after train completes)
- Command: `conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split train`

**Stage 2: CTR-GCN extraction (vcc-ctrgcn)**
- Status: NOT STARTED (depends on Stage 1 skeleton pickles)
- Command ready: `conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset ucf --split {train|val|test}`

**Stage 3: CLIP extraction (vcc-main)**
- Status: NOT STARTED (depends on Stage 1 boundary JSONs)
- Command ready: `conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split {train|val|test}`

**Stage 4: Alignment verification**
- Status: NOT STARTED (depends on Stages 2 and 3 completing)
- Command: `conda run -n vcc-main python scripts/verify_alignment.py --dataset ucf --split all`

**Resume commands (use skip-if-exists logic to pick up from any interruption):**
```bash
# Run each stage sequentially to completion
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split train
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split val
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split test

conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset ucf --split train
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset ucf --split val
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset ucf --split test

conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split train
conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split val
conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split test

# Final verification
conda run -n vcc-main python scripts/verify_alignment.py --dataset ucf --split all
```

## Task 3 Checkpoint Details

**This is the human-verify checkpoint returned to the orchestrator.**

### What was built
- Complete UCF-Crime feature extraction pipeline infrastructure:
  - Alignment verification script (verify_alignment.py) validated on 3 sample videos
  - GPU mode enabled for skeleton extraction (cuDNN PATH fix)
  - All three extraction scripts (extract_skeletons.py, extract_ctrgcn.py, extract_clip.py) confirmed ready
- UCF-Crime skeleton extraction in progress at ~33/1900 videos

### Checkpoint verification steps (once extraction completes)

1. **Check alignment verification passes:**
   ```bash
   conda run -n vcc-main python scripts/verify_alignment.py --dataset ucf --split all
   ```
   Expected: "RESULT: PASSED (all 1900 checked videos OK)"

2. **Check errors.log files:**
   ```bash
   cat E:/skeletons/ucf/errors.log 2>/dev/null || echo "No skeleton errors"
   cat E:/features/ucf/skeleton/errors.log 2>/dev/null || echo "No CTR-GCN errors"
   cat E:/features/ucf/clip/errors.log 2>/dev/null || echo "No CLIP errors"
   ```

3. **Spot-check a few feature files:**
   ```bash
   conda run -n vcc-main python -c "
   import numpy as np
   s = np.load('E:/features/ucf/skeleton/Fighting002.npy')
   c = np.load('E:/features/ucf/clip/Fighting002.npy')
   print(f'Skeleton: {s.shape} {s.dtype} range=[{s.min():.3f}, {s.max():.3f}]')
   print(f'CLIP: {c.shape} {c.dtype} range=[{c.min():.3f}, {c.max():.3f}]')
   print(f'Snippets match: {s.shape[0] == c.shape[0]}')
   "
   ```

4. **Confirm feature file counts:**
   ```bash
   ls E:/features/ucf/skeleton/*.npy | wc -l   # should be ~1900
   ls E:/features/ucf/clip/*.npy | wc -l        # should be ~1900
   ```

### Resume signal
Type "approved" to proceed to XD-Violence extraction (Plan 04), or describe any issues with the extraction quality.

## Issues Encountered

- RTMPose CUDA mode requires cuDNN 9.x CUDA 12 DLLs from `v9.8/bin/12.8/` subdirectory (not the parent `v9.8/bin/`). This is specific to the Windows cuDNN 9.x installation layout where DLLs are organized by CUDA version in subdirectories. Fixed by PATH prepend.
- UCF-Crime extraction averages ~10s/video on GPU (higher than 2-5s estimate in plan), likely because Abuse category videos used in smoke tests were short. Full-length videos (3-15 min each) have more frames to process.
- Extraction is a multi-hour job (~5h for skeleton + ~2h CTR-GCN + ~1h CLIP = ~8h total).

## Known Stubs

- `E:/features/ucf/skeleton/` and `E:/features/ucf/clip/` are partially populated (33 skeleton files vs 1900 expected). Extraction is in progress but incomplete at plan commit time.
- These are real features, not stubs — but coverage is incomplete pending extraction completion.

## Self-Check: PARTIAL

| Item | Status |
|------|--------|
| scripts/verify_alignment.py | FOUND |
| scripts/extract_skeletons.py (cuDNN fix) | FOUND |
| .planning/phases/02-feature-extraction-pipeline/02-03-SUMMARY.md | FOUND |
| commit 92a88a1 (Task 1) | FOUND |
| commit 8ce23a6 (Task 2 fix) | FOUND |
| E:/features/ucf/skeleton/*.npy (1900 expected) | PARTIAL (33/1900 in progress) |
| E:/features/ucf/clip/*.npy (1900 expected) | NOT STARTED |
| verify_alignment.py --dataset ucf --split all exit 0 | NOT YET (extraction incomplete) |

Self-check is PARTIAL: Tasks 1 and 2 are committed with correct code. Feature extraction is running in the background. The checkpoint (Task 3) will become PASSED when extraction completes.

---
*Phase: 02-feature-extraction-pipeline*
*Completed: 2026-04-03 (partial — extraction in progress)*
