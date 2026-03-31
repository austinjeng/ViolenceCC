---
phase: 01-environment
plan: 02
subsystem: infra
tags: [conda, pytorch, rtmlib, pyskl, mmcv, open-clip, cuda, xd-violence, i3d, ntfs-junction]

# Dependency graph
requires:
  - phase: 01-environment-plan-01
    provides: project directory scaffold, envs/ directory, SETUP.md, .gitignore

provides:
  - vcc-skeleton conda env (Python 3.11, rtmlib 0.0.15, onnxruntime-gpu 1.24.4, CUDA EP)
  - vcc-ctrgcn conda env (Python 3.10, PyTorch 1.12.1+cu113, mmcv-full 1.7.0, PYSKL)
  - vcc-main conda env (Python 3.11, PyTorch 2.6.0+cu124, open-clip-torch 3.3.0, scikit-learn, h5py)
  - PYSKL cloned at D:\libs\pyskl (editable install in vcc-ctrgcn)
  - XD-Violence 3954 training videos extracted flat to E:\XD_Violence\train\
  - XD-Violence 800 test videos at E:\XD_Violence\test\videos\
  - I3D features extracted to E:\i3d-features\i3d-features\
  - E:\features\ feature cache root directory
  - D:\ViolenceCC\data\features -> E:\features\ NTFS junction

affects: [01-environment-plan-03, 02-feature-extraction, 03-model-training]

# Tech tracking
tech-stack:
  added:
    - rtmlib 0.0.15 (vcc-skeleton)
    - onnxruntime-gpu 1.24.4 (vcc-skeleton)
    - PyTorch 1.12.1+cu113 pip wheel (vcc-ctrgcn)
    - mmcv-full 1.7.0 OpenMMLab wheel (vcc-ctrgcn)
    - mmdet 2.25.1 (vcc-ctrgcn)
    - mmpose 0.29.0 --no-deps (vcc-ctrgcn)
    - PYSKL editable install --no-deps (vcc-ctrgcn)
    - PyTorch 2.6.0+cu124 (vcc-main)
    - open-clip-torch 3.3.0 (vcc-main)
    - scikit-learn, h5py, scipy, kornia, decord, wandb, tensorboard (vcc-main)
  patterns:
    - "Use pip wheels (not conda) for PyTorch 1.12.1+cu113 on Windows — conda package has shm.dll/torch_cpu.dll load failure (WinError 182)"
    - "mmpose and PYSKL installed with --no-deps to avoid chumpy build failure on Windows"
    - "NTFS junction created via PowerShell New-Item -ItemType Junction (not mklink — garbled in Chinese locale shell)"
    - "Use direct python.exe path (not conda run) when conda Unicode output fails (cp950 codec error)"

key-files:
  created:
    - C:\Anaconda\envs\vcc-skeleton\ (conda env)
    - C:\Anaconda\envs\vcc-ctrgcn\ (conda env)
    - C:\Anaconda\envs\vcc-main\ (conda env)
    - D:\libs\pyskl\ (PYSKL clone)
    - E:\XD_Violence\train\ (3954 training videos)
    - E:\XD_Violence\test\videos\ (800 test videos)
    - E:\i3d-features\i3d-features\ (Flow, FlowTest, RGB, RGBTest)
    - E:\features\ (feature cache root)
    - D:\ViolenceCC\data\features (NTFS junction -> E:\features\)
  modified:
    - .planning/config.json (auto-chain flag update)

key-decisions:
  - "PyTorch 1.12.1 conda wheel fails on Windows with WinError 182 (shm.dll/torch_cpu.dll); must use pip +cu113 wheel instead"
  - "mmpose installed with --no-deps to skip chumpy build failure (chumpy has pip build isolation bug on modern pip)"
  - "PYSKL version conflicts on mmcv/mmdet/mmpose are expected and acceptable — PYSKL code works with newer versions installed"
  - "XD-Violence test zip has top-level videos/ folder — test videos at E:\\XD_Violence\\test\\videos\\ not directly in test\\"
  - "4 CRC errors in 1005-2004.zip are pre-existing corrupt files in source zip, not extraction failures"
  - "I3D features zip has top-level i3d-features/ folder — content at E:\\i3d-features\\i3d-features\\{Flow,FlowTest,RGB,RGBTest}"

patterns-established:
  - "Windows DLL issues: conda PyTorch packages may fail; always verify with direct python.exe invocation"
  - "conda run encoding: use direct python.exe path when conda run fails with cp950 UnicodeEncodeError"
  - "NTFS junction creation: use PowerShell New-Item -ItemType Junction on Chinese-locale Windows"

requirements-completed:
  - ENV-01

# Metrics
duration: 78min
completed: 2026-03-31
---

# Phase 01 Plan 02: Conda Environments and Dataset Extraction Summary

**Three isolated conda environments operational (Python 3.11/3.10/3.11 with PyTorch 1.12.1/2.6.0) plus 3954 XD-Violence training videos extracted flat and NTFS junction D:\ViolenceCC\data\features -> E:\features\ active**

## Performance

- **Duration:** 78 min
- **Started:** 2026-03-31T05:00:21Z
- **Completed:** 2026-03-31T06:19:13Z
- **Tasks:** 2 of 3 complete (Task 3 is checkpoint:human-verify)
- **Files modified:** 2 (config.json, data/features junction)

## Accomplishments

- vcc-skeleton: Python 3.11, rtmlib 0.0.15, onnxruntime-gpu 1.24.4 with CUDAExecutionProvider available
- vcc-ctrgcn: Python 3.10, PyTorch 1.12.1+cu113, mmcv-full 1.7.0, PYSKL from D:\libs\pyskl — all imports verified
- vcc-main: Python 3.11, PyTorch 2.6.0+cu124, open-clip-torch 3.3.0, full ML stack including scikit-learn, h5py, kornia, wandb
- XD-Violence: 3954 training videos extracted flat to E:\XD_Violence\train\ (no per-zip subdirectories)
- XD-Violence test: 800 videos at E:\XD_Violence\test\videos\ (zip had top-level videos/ folder)
- I3D features: extracted to E:\i3d-features\i3d-features\ with Flow, FlowTest, RGB, RGBTest subdirs
- NTFS junction D:\ViolenceCC\data\features -> E:\features\ created and resolves correctly

## Task Commits

1. **Task 1: Create three conda environments** - `6579326` (chore)
2. **Task 2: Extract XD-Violence and I3D datasets, create feature junction** - `385bec0` (chore)
3. **Task 3: Verify environments and dataset extraction** - CHECKPOINT (awaiting human verification)

## Files Created/Modified

- `C:\Anaconda\envs\vcc-skeleton\` - Python 3.11 skeleton extraction environment
- `C:\Anaconda\envs\vcc-ctrgcn\` - Python 3.10 CTR-GCN legacy environment
- `C:\Anaconda\envs\vcc-main\` - Python 3.11 main training environment
- `D:\libs\pyskl\` - PYSKL repository clone, editable install in vcc-ctrgcn
- `E:\XD_Violence\train\` - 3954 training MP4 videos (flat, no subdirs)
- `E:\XD_Violence\test\videos\` - 800 test MP4 videos
- `E:\i3d-features\i3d-features\` - Pre-extracted I3D features (4 subdirs)
- `E:\features\` - Feature cache root directory (empty, ready for Phase 2)
- `D:\ViolenceCC\data\features` - NTFS junction pointing to E:\features\
- `.planning/config.json` - Auto-chain flag added by orchestrator

## Decisions Made

- PyTorch 1.12.1 conda wheel has a DLL load failure (WinError 182, ERROR_INVALID_ORDINAL) on this Windows system. The pip +cu113 wheel works correctly and is used instead.
- mmpose 0.29.0 installed with `--no-deps` to bypass the `chumpy` build failure (modern pip's build isolation triggers a pip-within-pip error in chumpy's setup.py).
- PYSKL's own requirements.txt pins mmcv-full==1.5.0, mmdet==2.23.0, mmpose==0.24.0 — these conflict with the installed versions, but the warning is expected. PYSKL code works correctly with the newer versions.
- XD-Violence test data structure: the zip created a `videos/` subdirectory, so test videos are at `E:\XD_Violence\test\videos\` — Phase 2 extraction scripts must account for this path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PyTorch 1.12.1 conda wheel DLL failure**
- **Found during:** Task 1 (vcc-ctrgcn environment setup)
- **Issue:** Conda-installed pytorch==1.12.1 (pytorch/win-64::pytorch-1.12.1-py3.10_cuda11.3_cudnn8_0) fails with OSError: [WinError 182] when loading torch_cpu.dll/torch.dll. WinError 182 is ERROR_INVALID_ORDINAL, indicating a DLL function ordinal conflict.
- **Fix:** Removed conda PyTorch package and installed `torch==1.12.1+cu113 torchvision==0.13.1+cu113` from PyTorch's pip index (https://download.pytorch.org/whl/cu113). The +cu113 pip wheel loads correctly.
- **Files modified:** C:\Anaconda\envs\vcc-ctrgcn\ (system-level)
- **Verification:** `"C:/Anaconda/envs/vcc-ctrgcn/python.exe" -c "import torch; print(torch.__version__)"` outputs `1.12.1+cu113` and CUDA is available.
- **Committed in:** 6579326

**2. [Rule 2 - Missing Critical] opencv-python missing from vcc-ctrgcn**
- **Found during:** Task 1 (vcc-ctrgcn mmcv smoke test)
- **Issue:** mmcv imports cv2 in its environment collection code; cv2 was not installed, causing `ModuleNotFoundError: No module named 'cv2'`.
- **Fix:** Installed opencv-python and opencv-contrib-python in vcc-ctrgcn.
- **Files modified:** C:\Anaconda\envs\vcc-ctrgcn\ (system-level)
- **Verification:** `import mmcv; print(mmcv.__version__)` outputs `1.7.0`.
- **Committed in:** 6579326

**3. [Rule 1 - Bug] mmpose chumpy build failure**
- **Found during:** Task 1 (mmpose install)
- **Issue:** `pip install mmpose==0.29.0` fails due to `chumpy` dependency triggering ModuleNotFoundError: No module named 'pip' in its build isolation environment.
- **Fix:** Installed mmpose with `--no-deps` flag. chumpy is only needed for human body mesh estimation (SMPL), which is not used in this project's CTR-GCN workflow.
- **Files modified:** C:\Anaconda\envs\vcc-ctrgcn\ (system-level)
- **Verification:** `import pyskl` succeeds.
- **Committed in:** 6579326

---

**Total deviations:** 3 auto-fixed (1 bug/DLL, 1 missing dependency, 1 build workaround)
**Impact on plan:** All three fixes were necessary for correct environment operation. No scope creep.

## Issues Encountered

- **conda run Unicode failure (cp950):** On this Windows system with Chinese locale (code page 950), `conda run` fails with `UnicodeEncodeError: 'cp950'` when subprocess output contains characters outside cp950. Workaround: run `python.exe` directly by full path (e.g., `"C:/Anaconda/envs/vcc-ctrgcn/python.exe" -c ...`). This does not affect runtime operation.
- **NTFS junction via cmd.exe failed:** `cmd.exe /c "mklink /J ..."` produced garbled output on Chinese locale Windows and did not create the junction. Workaround: used PowerShell `New-Item -ItemType Junction -Path ... -Target ...` which worked correctly.
- **XD-Violence test zip structure:** The test zip `XD_violence_test_video.zip` contains a top-level `videos/` folder. Test videos landed at `E:\XD_Violence\test\videos\` instead of `E:\XD_Violence\test\`. Phase 2 extraction scripts must reference this path.
- **4 CRC errors in 1005-2004.zip:** Files `NewAdd.NBA-2017...`, `Saving.Private.Ryan...`, `v=8cTqh9...`, `v=9eME1y...` have CRC/data errors. These are pre-existing corrupt files in the source zip (not an extraction error). The remaining ~996 files in that archive extracted correctly. These 4 videos will be absent from Phase 2 extraction — acceptable loss (<0.1% of training set).

## Known Stubs

None — this plan creates system environments and extracts data. No placeholder code was written.

## Next Phase Readiness

- vcc-ctrgcn is ready for Plan 03 (CTR-GCN weight download and forward pass smoke test)
- vcc-main is ready for Phase 2 CLIP feature extraction
- vcc-skeleton is ready for Phase 2 RTMPose skeleton extraction
- XD-Violence training videos are available for Phase 2 extraction
- Feature junction resolves correctly — Phase 2 outputs will land in E:\features\ via data/features/

**Blocker for Phase 2 scripts:** XD-Violence test path is `E:\XD_Violence\test\videos\` not `E:\XD_Violence\test\`. Must update path constants in extraction scripts.

---
*Phase: 01-environment*
*Completed: 2026-03-31*
