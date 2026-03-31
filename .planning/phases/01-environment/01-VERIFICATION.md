---
phase: 01-environment
verified: 2026-03-31T16:30:00Z
status: passed
score: 3/3 success criteria verified
re_verification: false
gaps: []
human_verification:
  - test: "Confirm rtmlib works end-to-end with a real video frame in vcc-skeleton"
    expected: "RTMPose-m detects COCO-17 keypoints on a test image without error"
    why_human: "rtmlib imports successfully and ORT CUDA EP is present, but rtmlib has no __version__ attribute — functional RTMPose inference requires a live model download and cannot be confirmed from imports alone"
  - test: "Confirm XD-Violence training videos are valid MP4s (not corrupted)"
    expected: "At least one video file in E:\\XD_Violence\\train\\ can be decoded with OpenCV or decord"
    why_human: "3954 files confirmed present and count is correct, but 4 CRC-corrupt files are documented. Spot-check decodability of a sample video to confirm the extraction did not silently corrupt majority of files"
---

# Phase 1: Environment & Project Foundation Verification Report

**Phase Goal:** The three conda environments are functional, the CTR-GCN forward pass is verified with normalized COCO-17 input, and the project directory structure is ready for code
**Verified:** 2026-03-31T16:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All three environments activate without error and pass smoke-test imports (rtmlib, PYSKL, open-clip-torch) | VERIFIED | `vcc-skeleton`: rtmlib imports, ORT 1.24.4 with CUDAExecutionProvider. `vcc-ctrgcn`: pyskl, mmcv 1.7.0, torch 1.12.1+cu113, CUDA=True. `vcc-main`: open-clip 3.3.0, torch 2.6.0+cu124, CUDA=True. Python versions: 3.11 / 3.10 / 3.11 as required. |
| 2 | CTR-GCN forward pass with synthetic COCO-17 input (N=1, M=2, T=64, V=17, C=3) produces (1,256) output with no NaN/Inf | VERIFIED | pytest ran 4 tests in vcc-ctrgcn: `test_ctrgcn_forward_pass_shape` PASSED, `test_ctrgcn_output_no_nan` PASSED, `test_ctrgcn_output_no_inf` PASSED, `test_ctrgcn_output_nonzero_variance` PASSED. 4/4 passed in 29.80s. |
| 3 | Project directory tree (configs/, data/, src/, scripts/, results/, notebooks/) exists and is committed to repo | VERIFIED | All directories confirmed present. src/ has models/, data/, losses/, tta/, utils/ each with `__init__.py`. `.gitignore` excludes weights/features/results, tracks splits and configs. Commits 820fdd5 and da28e4d in git log. |

**Score:** 3/3 truths verified

---

### Required Artifacts

#### From 01-01-PLAN.md (ENV-03)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gitignore` | Git exclusion rules per D-07, contains "data/weights/" | VERIFIED | Contains `data/weights/ctrgcn/*.pth`, `data/weights/clip/*.pt`, `data/features/`, `results/`. Does NOT contain `data/splits/` or `configs/` — correct per D-07. |
| `envs/requirements-skeleton.txt` | vcc-skeleton package list, contains "rtmlib==0.0.15" | VERIFIED | Contains `rtmlib==0.0.15`, `onnxruntime-gpu==1.24.4`. Frozen from pip freeze 2026-03-31. |
| `envs/requirements-ctrgcn.txt` | vcc-ctrgcn package list, contains "mmcv-full==1.7.0" | VERIFIED | Contains `mmcv-full==1.7.0`, `mmdet==2.25.1`, `mmpose==0.29.0`, `fvcore==0.1.5.post20221221`, `numpy==1.26.4`. Exact pins. |
| `envs/requirements-main.txt` | vcc-main package list, contains "open-clip-torch==3.3.0" | VERIFIED | Contains `open-clip-torch==3.3.0`, `torch==2.6.0+cu124`, `kornia==0.8.2`. Exact pins from freeze. |
| `envs/SETUP.md` | Step-by-step install guide, contains "conda create" | VERIFIED | Contains all three `conda create -n vcc-{env} python=3.{x}` commands, mmcv-full wheel URL, `pip install -e D:/libs/pyskl --no-deps`, `mklink /J`, 7-Zip extraction commands. |
| `src/tta/__init__.py` | TTA placeholder per D-10 | VERIFIED | Contains docstring: "TTA module placeholder. TENT and SAR implementations will be added in Phase 5. Source: https://github.com/mr-eggplant/SAR (ICLR 2023, MIT License)." |

#### From 01-02-PLAN.md (ENV-01)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `E:\XD_Violence\train\` | 3954 extracted training videos | VERIFIED | `ls E:/XD_Violence/train/ | wc -l` = 3954. Flat directory, no per-zip subdirectories. |
| `E:\XD_Violence\test\videos\` | Extracted XD-Violence test videos | VERIFIED | 800 test videos at `E:\XD_Violence\test\videos\` (zip contained top-level `videos/` folder — documented deviation). |
| `E:\i3d-features\i3d-features\` | Pre-extracted I3D features | VERIFIED | Subdirs: Flow, FlowTest, RGB, RGBTest — all four present. |
| `E:\features\` | Feature cache root | VERIFIED | Directory exists. |
| `D:\ViolenceCC\data\features` | NTFS junction to E:\features\ | VERIFIED | `ls /d/ViolenceCC/data/features/` resolves without error. Junction active. |

#### From 01-03-PLAN.md (ENV-02)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/weights/ctrgcn/j.pth` | CTR-GCN Joint stream weights | VERIFIED | 6,136,595 bytes (~6.1 MB). |
| `data/weights/ctrgcn/b.pth` | CTR-GCN Bone stream weights | VERIFIED | 6,136,595 bytes (~6.1 MB). |
| `data/weights/ctrgcn/jm.pth` | CTR-GCN Joint Motion stream weights | VERIFIED | 6,136,595 bytes (~6.1 MB). |
| `data/weights/ctrgcn/bm.pth` | CTR-GCN Bone Motion stream weights | VERIFIED | 6,136,595 bytes (~6.1 MB). |
| `tests/conftest.py` | Shared test fixtures, contains "weight_dir" | VERIFIED | Contains `weight_dir` and `pyskl_config_dir` fixtures. |
| `tests/test_ctrgcn_smoke.py` | Automated CTR-GCN forward pass test, contains "assert output.shape" | VERIFIED | Contains `assert output.shape == (1, 256)`, four test functions, correct input shape (N=1, M=2, T=64, V=17, C=3) with zero-padded second person. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `envs/requirements-skeleton.txt` | `envs/SETUP.md` | SETUP.md references requirements files (pattern: "requirements-skeleton") | NOT WIRED | SETUP.md embeds install commands inline; does not cross-reference requirements-skeleton.txt by filename. Both files serve same purpose — this is a documentation style choice, not a functional failure. Install instructions are complete in SETUP.md. |
| `.gitignore` | `data/weights/` | gitignore excludes weight directory (pattern: "data/weights") | VERIFIED | Pattern `data/weights/ctrgcn/*.pth` found in .gitignore. |
| `vcc-ctrgcn` | `D:\libs\pyskl` | pip install -e (pattern: import pyskl) | VERIFIED | `import pyskl` succeeds in vcc-ctrgcn. `D:/libs/pyskl/setup.py` confirmed present. |
| `data/features` | `E:\features` | NTFS junction (pattern: mklink /J) | VERIFIED | Junction resolves; `ls /d/ViolenceCC/data/features/` succeeds. |
| `tests/test_ctrgcn_smoke.py` | `data/weights/ctrgcn/j.pth` | torch.load for checkpoint (pattern: torch.load) | VERIFIED | `torch.load(weight_path, map_location='cpu')` in conftest fixture; tests pass against real weights. |
| `tests/test_ctrgcn_smoke.py` | `D:\libs\pyskl` | pyskl.models.build_model (pattern: build_model) | VERIFIED | `from pyskl.models import build_model` in test file; model builds and runs forward pass. |

**Note on missing link:** The `requirements-skeleton.txt` → `SETUP.md` cross-reference link is not present. This is a cosmetic issue — SETUP.md is self-contained and complete. The requirements files serve as reproducibility records (per D-08), not as pip install -r targets. No functional gap exists.

---

### Data-Flow Trace (Level 4)

Not applicable — this is an infrastructure/environment phase. No components render dynamic data from a data source. The smoke test uses synthetic (hardcoded) input by design (per D-09: "Minimal forward pass only").

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| vcc-skeleton imports rtmlib | `vcc-skeleton python -c "import rtmlib; print('OK')"` | `rtmlib OK: no version attr` | PASS |
| vcc-skeleton ORT CUDA EP available | `vcc-skeleton python -c "import onnxruntime; print('CUDA EP:', ...)"` | `ORT: 1.24.4, CUDA EP: True` | PASS |
| vcc-ctrgcn PyTorch 1.12.1+cu113 | `vcc-ctrgcn python -c "import torch; print(torch.__version__)"` | `1.12.1+cu113` | PASS |
| vcc-ctrgcn mmcv 1.7.0 | `vcc-ctrgcn python -c "import mmcv; print(mmcv.__version__)"` | `1.7.0` | PASS |
| vcc-ctrgcn pyskl imports | `vcc-ctrgcn python -c "import pyskl; print('OK')"` | `PYSKL OK` | PASS |
| vcc-ctrgcn CUDA available | `vcc-ctrgcn python -c "import torch; print(torch.cuda.is_available())"` | `True` | PASS |
| vcc-main PyTorch 2.6.0+cu124 | `vcc-main python -c "import torch; print(torch.__version__)"` | `2.6.0+cu124` | PASS |
| vcc-main open-clip 3.3.0 | `vcc-main python -c "import open_clip; print(open_clip.__version__)"` | `3.3.0` | PASS |
| vcc-main CUDA available | `vcc-main python -c "import torch; print(torch.cuda.is_available())"` | `True` | PASS |
| CTR-GCN smoke tests (4 tests) | `vcc-ctrgcn python -m pytest tests/test_ctrgcn_smoke.py -x -v` | `4 passed in 29.80s` | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ENV-01 | 01-02-PLAN.md | Three conda environments created and verified | SATISFIED | All three envs activate, import primary packages, CUDA available in vcc-ctrgcn and vcc-main. Python versions: 3.11/3.10/3.11. |
| ENV-02 | 01-03-PLAN.md | CTR-GCN NTU120 HRNet 2D weights downloaded and forward pass verified with COCO-17 input | SATISFIED | 4 weight files at data/weights/ctrgcn/ (~6.1 MB each). pytest: 4/4 tests pass confirming (1,256) output, no NaN/Inf, nonzero variance. Input shape (N=1,M=2,T=64,V=17,C=3) confirmed. |
| ENV-03 | 01-01-PLAN.md | Project directory structure established per research-recommended layout | SATISFIED | configs/, data/, src/, scripts/, results/, notebooks/ all present. src/ has 5 subpackages with __init__.py. .gitignore correctly excludes/includes per D-07. |

**All three Phase 1 requirements satisfied. No orphaned requirements detected.**

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/models/__init__.py` | 1 | Empty file | INFO | Intentional structural placeholder per D-01. Models implemented in Phase 3. |
| `src/data/__init__.py` | 1 | Empty file | INFO | Intentional structural placeholder. Data pipeline in Phase 2. |
| `src/losses/__init__.py` | 1 | Empty file | INFO | Intentional structural placeholder. MIL loss in Phase 3. |
| `src/utils/__init__.py` | 1 | Empty file | INFO | Intentional structural placeholder. Utilities added per-need. |

All empty `__init__.py` files are intentional structural placeholders documented in 01-01-SUMMARY.md as "Known Stubs." None affect Phase 1 goal (directory scaffold + environment verification). No blockers found.

---

### Human Verification Required

#### 1. rtmlib RTMPose Functional Inference

**Test:** In vcc-skeleton, run RTMPose-m inference on a single test frame image.
**Expected:** Detects COCO-17 keypoints without error; ORT CUDAExecutionProvider is used for inference.
**Why human:** `import rtmlib` succeeds and ORT CUDA EP is confirmed available, but rtmlib has no `__version__` attribute and we cannot invoke full inference programmatically without a model checkpoint download and test image. The functional path (skeleton extraction → COCO-17 output) is a Phase 2 concern but catching rtmlib inference failures early is prudent.

#### 2. XD-Violence Video Decodability

**Test:** Decode a sample of 5-10 videos from `E:\XD_Violence\train\` using `cv2.VideoCapture` or `decord.VideoReader`.
**Expected:** Videos open and yield frames without error; frame count > 0.
**Why human:** 3954 files are present and `wc -l` confirms count, but 4 CRC-corrupt files are documented in the source zip. A quick decodability spot-check confirms the majority of files are valid before committing to Phase 2 extraction (20-40h runtime).

---

### Gaps Summary

No gaps blocking Phase 1 goal achievement. All three success criteria from ROADMAP.md are fully verified:

1. All three environments activate and pass smoke-test imports — confirmed via direct python.exe invocation.
2. CTR-GCN forward pass verified with (N=1,M=2,T=64,V=17,C=3) synthetic input — pytest 4/4 PASSED.
3. Project directory tree committed to repo — all directories present, .gitignore correct.

One key link from Plan 01 frontmatter (SETUP.md referencing requirements-skeleton.txt by filename) is not wired — SETUP.md is self-contained with inline commands. This is a documentation style choice, not a functional issue. Both files fulfill their documented purpose per D-08.

**Notable discovery documented for Phase 2:** CTR-GCN input contract is `(N, M, T, V, C)` with M=2 required (data_bn initialized with 102=2×17×3 channels). Extraction scripts in Phase 2 MUST pad to M=2 and pool over M/T/V dimensions to produce (N,256). XD-Violence test videos reside at `E:\XD_Violence\test\videos\` (not `E:\XD_Violence\test\`) due to zip structure.

---

_Verified: 2026-03-31T16:30:00Z_
_Verifier: Claude (gsd-verifier)_
