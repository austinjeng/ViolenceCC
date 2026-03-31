# Phase 1: Environment & Project Foundation - Research

**Researched:** 2026-03-31
**Domain:** Conda environment setup, PYSKL/CTR-GCN integration, Windows-specific toolchain, project scaffolding
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** `src/` organized by concern: `models/`, `data/`, `losses/`, `tta/`, `utils/` subpackages. Entry points `train.py` and `evaluate.py` live at the `src/` root.

**D-02:** Separate `scripts/` directory at project root for extraction and utility scripts. Scripts run in different conda envs than `src/` code.

**D-03:** Flat YAML files in `configs/` — one self-contained file per experiment variant. No base+override inheritance.

**D-04:** Standalone clone at `D:\libs\pyskl`, installed via `pip install -e .` in vcc-ctrgcn environment. Project references PYSKL via standard `import pyskl`.

**D-05:** Pretrained weights stored in `data/weights/` (gitignored) with subdirectories: `data/weights/ctrgcn/` (j.pth, b.pth, jm.pth, bm.pth) and `data/weights/clip/` (ViT-B-16.pt).

**D-06:** Extracted features stored on `E:\features\` with symlinks from `data/features/` pointing there.

**D-07:** `.gitignore` by directory: `data/weights/`, `data/features/`, `results/`. Commit `data/splits/*.txt` and `configs/*.yaml`.

**D-08:** One `requirements-{env}.txt` per conda environment stored in `envs/` directory. Accompanied by `envs/SETUP.md` step-by-step guide. No automated setup script — manual is more debuggable on Windows.

**D-09:** CTR-GCN smoke test: minimal forward pass only. Create synthetic tensor (N=1, C=3, T=64, V=17, M=1), run through CTR-GCN with NTU120-xsub-j weights, assert output shape is (1, 256). No multi-stream or intermediate normalization checks.

**D-10:** Copy `tent.py` and `sar.py` from official SAR repo into `src/tta/` with attribution headers. Phase 1 creates `src/tta/` as empty placeholder with `__init__.py`.

**D-11:** UCF-Crime at `E:\UCF_crime_dataset\` contains pre-extracted PNG frames (every 10th frame, ~3fps equivalent). Organized as `Train/{category}/{video}_x264_{framenum}.png` and `test/{category}/...`. 14 categories.

**D-12:** XD-Violence zips on `E:\` to be unzipped to `E:\XD_Violence\train\` and `E:\XD_Violence\test\`. Training zips: `1-1004.zip` through `3320-3954.zip` (~72GB). Test zip: `XD_violence_test_video.zip` (~11GB). Annotations: `E:\XD_violence_annotations.txt`.

**D-13:** Pre-extracted I3D features (`E:\i3d-features.zip`, ~39GB) to be unzipped and kept as reference/baseline comparison material.

**D-14:** UCF-Crime extraction reads PNGs directly. XD-Violence extraction uses standard video decoding. Both pipelines output same feature format per video.

### Claude's Discretion

None specified — all Phase 1 implementation decisions are locked.

### Deferred Ideas (OUT OF SCOPE)

- RWF-2000 dataset on E:\ — potential third dataset, not in v1 scope
- Automated environment setup script — manual SETUP.md chosen
- wandb project initialization — defer to Phase 3
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-01 | Three conda environments created and verified — `vcc-skeleton` (rtmlib 0.0.15 + onnxruntime-gpu), `vcc-ctrgcn` (PyTorch 1.12.1 + PYSKL + mmcv-full 1.7.0), `vcc-main` (PyTorch 2.6.0 + open-clip-torch 3.3.0) | Environment creation commands verified; Windows-specific wheel URLs confirmed; conda cudatoolkit=11.3 availability confirmed |
| ENV-02 | CTR-GCN NTU120 HRNet 2D pretrained weights downloaded and forward pass verified with COCO-17 input (17 joints x 3 channels x 64 frames x 2 persons → 256-d output) | Weight URLs confirmed live (6.1 MB each); PreNormalize2D algorithm documented from source; FormatGCNInput shape contract verified; D-09 restricts to minimal forward pass with M=1 |
| ENV-03 | Project directory structure established following research-recommended layout | Directory tree from ARCHITECTURE.md and CONTEXT.md D-01 through D-10; gitignore rules from D-07 |
</phase_requirements>

---

## Summary

Phase 1 establishes the three isolated conda environments and the project scaffold that all subsequent phases depend on. No novel research is required — the technology decisions are fully locked in CONTEXT.md and verified in the existing research files (STACK.md, ARCHITECTURE.md, PITFALLS.md). The research task for Phase 1 is primarily to verify the environment on the actual machine, document exact installation commands for Windows, and surface any blockers before the plan is written.

Environment audit reveals: none of the three target environments (`vcc-skeleton`, `vcc-ctrgcn`, `vcc-main`) exist yet. The base conda is Python 3.12.4, which is NOT the right Python version for any of the three environments — each must be created with an explicit Python version. CUDA driver is 591.86 supporting CUDA 13.1, which is backward-compatible with CUDA 12.4 and 11.3 as managed by conda. The mmcv-full 1.7.0 Windows wheel for Python 3.10 (`win_amd64`) exists at the OpenMMLab CDN. All CTR-GCN weight download URLs are live.

Dataset audit reveals: UCF-Crime PNG frames are fully extracted at `E:\UCF_crime_dataset\` with the expected structure (14 categories, Train + test directories). XD-Violence is NOT yet extracted — five zip files totaling ~69.5 GB are present on E:. I3D features zip (~39 GB) also awaits extraction. The XD-Violence annotation file is present at `E:\XD_violence_annotations.txt`. No UCF-Crime official split files (Anomaly_Train.txt, Anomaly_Test.txt, Temporal_Anomaly_Annotation.txt) were found in the dataset directory — these must be sourced separately.

The single most important technical detail for Phase 1 is the PreNormalize2D coordinate normalization algorithm (relevant to ENV-02 and the C1 pitfall). The exact implementation from PYSKL source is documented below.

**Primary recommendation:** Create all three conda environments in order (vcc-skeleton → vcc-ctrgcn → vcc-main), using the exact Windows-specific install commands documented below. Do not skip the CTR-GCN smoke test — it is the only Phase 1 verification that can catch Pitfall C1 before it wastes weeks.

---

## Project Constraints (from CLAUDE.md)

| Directive | Constraint |
|-----------|-----------|
| Single RTX 4090, 24GB VRAM | Rules out end-to-end backbone training; feature extraction is offline |
| Python 3.11 for vcc-skeleton and vcc-main | Python 3.12 base env is wrong for any VCC environment |
| Python 3.10 for vcc-ctrgcn | PYSKL pyskl_310.yaml is the authority |
| PyTorch 2.6.0 + cu124 for vcc-main | NOT 2.11.x; cu126/128 untested |
| mmcv-full 1.7.0 for vcc-ctrgcn | NOT 1.5.0 from requirements.txt |
| rtmlib 0.0.15 | Latest (2026-02-10); pure ONNX Runtime |
| open-clip-torch 3.3.0 | NOT openai/clip; use pretrained='openai' |
| float32 .npy per video | NOT HDF5; simpler, sufficient |
| Manual SETUP.md, no automation | Solo researcher, debuggability |
| English codebase | Standard for ML research repos |

---

## Standard Stack

### vcc-skeleton Environment

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| Python | 3.11 | Environment base | CLAUDE.md, STACK.md |
| rtmlib | 0.0.15 | RTMPose skeleton extraction, pure ONNX | PyPI verified 2026-02-10 |
| onnxruntime-gpu | 1.20.x (latest) | GPU-accelerated ONNX inference | Requires cuDNN 9.x (available on this machine) |
| opencv-python | 4.x (latest) | Frame decoding, image preprocessing | Required by rtmlib |
| opencv-contrib-python | 4.x (latest) | Extended OpenCV modules | Required by rtmlib |
| numpy | >= 1.23 | Array operations | rtmlib dependency |
| tqdm | >= 4.65 | Progress bars | Extraction monitoring |

**Install commands (Windows, vcc-skeleton):**
```bash
conda create -n vcc-skeleton python=3.11 -y
conda activate vcc-skeleton
pip install rtmlib -i https://pypi.org/simple
pip install onnxruntime-gpu
pip install opencv-python opencv-contrib-python numpy tqdm
```

### vcc-ctrgcn Environment

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| Python | 3.10 | Required by PYSKL pyskl_310.yaml | CLAUDE.md, STACK.md |
| PyTorch | 1.12.1 + cu113 | CTR-GCN forward pass (legacy) | PYSKL official env pin |
| torchvision | 0.13.1 | Paired with PyTorch 1.12.1 | Version-locked |
| mmcv-full | 1.7.0 | PYSKL hard dependency | Win wheel verified at OpenMMLab CDN |
| mmdet | 2.25.1 | PYSKL dependency | Pinned in pyskl_310.yaml |
| mmpose | 0.29.0 | PYSKL dependency | Pinned in pyskl_310.yaml |
| PYSKL | main branch | CTR-GCN model loading and forward pass | Clone to D:\libs\pyskl |
| decord | >= 0.6.0 | Video decoding (fallback: eva-decord) | PYSKL requirement |
| numpy | >= 1.23 | Array operations | Standard |
| scipy | >= 1.9 | Statistical utilities | PYSKL dependency |
| tqdm | >= 4.65 | Progress bars | Standard |

**Install commands (Windows, vcc-ctrgcn):**
```bash
conda create -n vcc-ctrgcn python=3.10 -y
conda activate vcc-ctrgcn
conda install pytorch==1.12.1 torchvision==0.13.1 cudatoolkit=11.3 -c pytorch -c conda-forge
pip install mmcv-full==1.7.0 -f https://download.openmmlab.com/mmcv/dist/cu113/torch1.12.0/index.html
pip install mmdet==2.25.1 mmpose==0.29.0
# PYSKL installed from D:\libs clone (per D-04)
pip install -e D:/libs/pyskl --no-deps
pip install decord numpy scipy tqdm
```

**Windows wheel confirmation (HIGH confidence, verified 2026-03-31):**
The URL `https://download.openmmlab.com/mmcv/dist/cu113/torch1.12.0/index.html` lists:
- `mmcv_full-1.7.0-cp310-cp310-win_amd64.whl` — confirmed present
- The `-f` flag in pip install will pick this wheel automatically for Python 3.10 on Windows

### vcc-main Environment

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| Python | 3.11 | Environment base | CLAUDE.md |
| PyTorch | 2.6.0 + cu124 | MIL training, CLIP extraction, TTA | CLAUDE.md, STACK.md |
| torchvision | 0.21.0 | Version-locked with PyTorch 2.6.0 | Must not mix |
| torchaudio | 2.6.0 | Version-locked | Must not mix |
| open-clip-torch | 3.3.0 | CLIP ViT-B/16 feature extraction | PyPI verified 2026-02-27 |
| timm | latest | Required by open-clip-torch | open-clip docs: "ensure latest timm" |
| scikit-learn | >= 1.3 | roc_auc_score, average_precision_score | Standard evaluation |
| numpy | >= 1.23 | Array operations, feature caching | Universal |
| h5py | >= 3.8 | Feature storage (HDF5 alternative) | Optional; main format is .npy |
| tqdm | >= 4.65 | Progress bars | Standard |
| PyYAML | >= 6.0 | Config file management | D-03 flat YAML |
| wandb | >= 0.16 | Experiment tracking | Optional; defer init to Phase 3 |
| tensorboard | >= 2.14 | Alternative to wandb | Built into PyTorch |
| kornia | >= 0.7 | Corruption generation (Phase 5) | Install now for completeness |
| Pillow | >= 9.4 | JPEG compression corruption | Standard |
| scipy | >= 1.9 | Statistical utilities | Standard |
| decord | >= 0.6.0 | Video decoding for XD-Violence | Fallback: eva-decord |

**Install commands (Windows, vcc-main):**
```bash
conda create -n vcc-main python=3.11 -y
conda activate vcc-main
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install open-clip-torch timm
pip install scikit-learn h5py numpy scipy tqdm PyYAML wandb tensorboard
pip install kornia Pillow
pip install decord  # or: pip install eva-decord if decord fails on Windows
```

---

## Architecture Patterns

### Recommended Project Structure

Per CONTEXT.md D-01 through D-10 and ARCHITECTURE.md (PEL4VAD-derived layout):

```
ViolenceCC/
├── configs/                       # D-03: flat YAML per experiment variant
│   ├── skeleton_only.yaml
│   ├── clip_only.yaml
│   ├── late_fusion.yaml
│   ├── gated_fusion.yaml
│   └── rtfm_baseline.yaml
│
├── data/                          # Split lists and annotations only (NOT features)
│   ├── splits/                    # D-07: committed to git
│   │   ├── ucf_train.txt
│   │   ├── ucf_val.txt
│   │   ├── ucf_test.txt
│   │   ├── xd_train.txt
│   │   ├── xd_val.txt
│   │   └── xd_test.txt
│   └── weights/                   # D-05: gitignored
│       ├── ctrgcn/                # j.pth, b.pth, jm.pth, bm.pth
│       └── clip/                  # ViT-B-16.pt (auto-downloaded by open-clip)
│
├── data/features -> E:\features\  # D-06: symlink to E: drive
│
├── src/                           # D-01: all Python source
│   ├── train.py                   # D-01: entry point at src/ root
│   ├── evaluate.py                # D-01: entry point at src/ root
│   ├── models/
│   ├── data/
│   ├── losses/
│   ├── tta/                       # D-10: placeholder __init__.py in Phase 1
│   └── utils/
│
├── scripts/                       # D-02: per-env extraction scripts
│   ├── extract_skeletons.py       # runs in vcc-skeleton
│   ├── extract_ctrgcn.py          # runs in vcc-ctrgcn
│   ├── extract_clip.py            # runs in vcc-main
│   └── verify_alignment.py        # runs in vcc-main
│
├── envs/                          # D-08: requirements + SETUP.md
│   ├── requirements-skeleton.txt
│   ├── requirements-ctrgcn.txt
│   ├── requirements-main.txt
│   └── SETUP.md
│
├── results/                       # D-07: gitignored
├── notebooks/
│
├── .gitignore
├── CLAUDE.md
└── thesis_prd_v2.3.md
```

### Pattern 1: Three-Environment Isolation

**What:** Three separate conda environments, each handling one stage of the pipeline, with no cross-environment imports.

**Why:** mmcv-full 1.x cannot coexist with PyTorch 2.x in the same environment. The three-environment split is the only clean resolution for PYSKL's legacy dependency chain.

**The handoff contract:** All environments write/read float32 .npy files to/from `E:\features\`. No environment imports from another environment's libraries.

### Pattern 2: PYSKL CTR-GCN Forward Pass Pattern

**What:** Load CTR-GCN from PYSKL config + checkpoint, call forward in eval + no_grad mode, extract the 256-d backbone output (before the classification head).

**Source:** PYSKL CTR-GCN config `ctrgcn_pyskl_ntu120_xsub_hrnet/j.py` verified on GitHub.

**Input tensor contract (from FormatGCNInput source):**
```python
# Shape: [N, C, T, V, M]
# N = batch size (1 for single video inference)
# C = 3 (x, y, confidence — after PreNormalize2D concatenates score as channel 2)
# T = 64 (frames per snippet window)
# V = 17 (COCO-17 keypoints)
# M = 2 (max persons; FormatGCNInput pads with zeros when M < 2)

import torch
synthetic_input = torch.zeros(1, 3, 64, 17, 2)  # all zeros = valid but empty
# CTR-GCN backbone output shape: (1, 256)
```

**Important:** D-09 specifies M=1 for the smoke test. The actual extraction pipeline will use M=2, but the smoke test uses a simpler (N=1, C=3, T=64, V=17, M=1) input.

### Pattern 3: PreNormalize2D Coordinate Normalization

This is the critical transform that prevents Pitfall C1. Must be applied to RTMPose pixel coordinates before CTR-GCN forward pass.

**Source:** Verified from `pyskl/datasets/pipelines/pose_related.py` on GitHub (2026-03-31).

**'fix' mode (default, what PYSKL uses):**
```python
# PreNormalize2D default: img_shape=(1080, 1920), threshold=0.01, mode='fix'
# Input: keypoint array [M, T, V, C] where C=2 (x, y) in pixel coordinates
# Output: normalized coordinates in [-1, 1]

h, w = img_shape  # (1080, 1920) for HD video
# x normalization (axis 0):
keypoint[..., 0] = (keypoint[..., 0] - (w / 2)) / (w / 2)
# y normalization (axis 1):
keypoint[..., 1] = (keypoint[..., 1] - (h / 2)) / (h / 2)
# Points below threshold=0.01 are zeroed out after normalization
# If keypoint_score exists, concatenated as channel index 2
```

**For the smoke test and early verification:** After applying this normalization to any valid video frame keypoints, all coordinate values must be in [-1, 1]. A debug assertion `assert np.all(np.abs(keypoint[..., :2]) <= 1.5)` provides a reasonable check.

**What happens without it:** Raw RTMPose pixel coordinates (e.g., x=640, y=360 for center of 1280x720 frame) produce values ~300x larger than the pretrained weight distribution expects. CTR-GCN silently outputs garbage features (near-zero variance, all cosine similarities > 0.99).

### Pattern 4: Windows Symlink Strategy for Features

**Decision D-06** requires `data/features/` to be a symlink pointing to `E:\features\`.

**Problem:** Windows symlinks require either Developer Mode enabled or elevated (admin) privileges. Testing on this machine shows symlink creation fails without elevation.

**Alternatives that work without elevation:**
1. **Junction point** (Windows NTFS junction) — works without admin for directories, unlike symlinks:
   ```bash
   # In Windows cmd (not bash):
   mklink /J D:\ViolenceCC\data\features E:\features
   # Or via PowerShell:
   New-Item -ItemType Junction -Path D:\ViolenceCC\data\features -Target E:\features
   ```
2. **Relative path in config** — skip the symlink and reference `E:\features\` directly in YAML configs. Simpler and more debuggable.

**Recommendation:** Use a NTFS junction point (mklink /J) for D-06 compliance. Document this in SETUP.md as a Windows-specific step. If junction creation also fails, fallback to direct E:\ paths in configs and add a note to SETUP.md.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| COCO-17 coordinate normalization | Custom normalize function | PYSKL PreNormalize2D (copy the exact algorithm) | The exact arithmetic is documented from source; deviating from it breaks CTR-GCN compat |
| CTR-GCN forward pass | Custom GCN implementation | PYSKL's RecognizerGCN (feature extraction mode) | NTU120 weights are calibrated to PYSKL's exact graph topology |
| CLIP ViT-B/16 loading | Custom weight loading | `open_clip.create_model_and_transforms('ViT-B-16', pretrained='openai')` | open-clip-torch handles weight download, preprocessing, and eval mode |
| Zip extraction (69.5 GB XD-Violence) | Python zipfile in a loop | 7-Zip at `C:\Program Files\7-Zip\7z.exe` | 7-Zip is installed and handles large archives without Python memory issues |

**Key insight:** Phase 1 is infrastructure work. Every component has a canonical implementation — the research goal is to identify the exact invocation, not to build anything custom.

---

## Common Pitfalls

### Pitfall C1: Coordinate Space Mismatch (CRITICAL — must verify in Phase 1)

**What goes wrong:** RTMPose outputs pixel coordinates (e.g., x=640). CTR-GCN expects normalized coordinates (~[-1, 1]). No error is raised — features silently become garbage.

**Why it happens:** The normalization lives in PYSKL's data pipeline. When calling CTR-GCN directly as a feature extractor (bypassing the training pipeline), PreNormalize2D is not applied automatically.

**Prevention:** Apply PreNormalize2D manually. The exact algorithm is documented in the Code Examples section. Assert `abs(coords) <= 1.5` after normalization. This is verified during the ENV-02 smoke test — D-09 specifies the output must be a (1, 256) tensor with no NaN/Inf.

**Warning signs:** CTR-GCN output features have near-zero variance across videos; all cosine similarities > 0.99.

### Pitfall P1: mmcv-full 1.7.0 Installation Confusion on Windows

**What goes wrong:** The PYSKL `requirements.txt` pins `mmcv-full==1.5.0`. Using this instead of 1.7.0 may work but the 1.7.0 wheel is the correct one per pyskl_310.yaml.

**How to avoid:** Always use the `-f` flag pointing to `https://download.openmmlab.com/mmcv/dist/cu113/torch1.12.0/index.html` and specify `==1.7.0` explicitly. The Windows cp310 wheel (`win_amd64`) is confirmed present at this URL.

### Pitfall P2: Windows Symlink Creation Fails Silently

**What goes wrong:** `os.symlink()` silently fails on Windows without Developer Mode enabled. `data/features/` directory either doesn't get created or gets created as an empty directory.

**How to avoid:** Use `mklink /J` (junction point) via Windows cmd, or use PowerShell `New-Item -ItemType Junction`. Document in SETUP.md. Test that the junction resolves correctly: `ls data/features/` should list E:\features\ contents.

### Pitfall P3: XD-Violence Zip Extraction Creates Per-Zip Subdirectories

**What goes wrong:** Many zip tools extract to a subdirectory named after the zip file (e.g., `E:\XD_Violence\1-1004\` instead of `E:\XD_Violence\train\`). This breaks any script that expects flat video layout.

**How to avoid:** Use explicit target directory: `"C:\Program Files\7-Zip\7z.exe" x E:\1-1004.zip -o"E:\XD_Violence\train\" -y`. The `-o` flag sets the output directory without creating a subdirectory.

**From CONTEXT.md specifics:** "Extract ZIPs into single `train/` directory, not per-zip subdirectories."

### Pitfall P4: UCF-Crime Frame Lexicographic Sort Bug

**What goes wrong:** PNG filenames like `Fighting002_x264_100.png` and `Fighting002_x264_1000.png` sort lexicographically incorrectly (`1000` before `100` is wrong). Any code that sorts frame filenames as strings will produce wrong frame order.

**How to avoid:** Always sort by extracting the integer frame number: `sorted(files, key=lambda f: int(f.split('_x264_')[1].replace('.png', '')))`. This is documented in CONTEXT.md specifics.

**Also noted:** Fighting category starts from Fighting002 (no Fighting001). Code must not assume sequential video numbering starting at 001.

### Pitfall P5: Base Conda Python 3.12 Contamination

**What goes wrong:** The active conda base environment is Python 3.12.4. If `conda create -n vcc-skeleton` is run without explicitly specifying `python=3.11`, conda may inherit the base Python version.

**How to avoid:** Always specify `python=3.11` or `python=3.10` explicitly in the conda create command. Verify after creation: `conda activate vcc-skeleton && python --version`.

---

## Code Examples

### PreNormalize2D Implementation (for smoke test and extraction scripts)

```python
# Source: pyskl/datasets/pipelines/pose_related.py (verified 2026-03-31)
# Replicate this logic when calling CTR-GCN outside PYSKL's training pipeline

import numpy as np

def prenormalize_2d(keypoint, img_shape=(1080, 1920), threshold=0.01, mode='fix'):
    """
    Apply PYSKL PreNormalize2D transform to pixel-coordinate keypoints.
    
    Args:
        keypoint: np.ndarray shape (M, T, V, C) where C=2 (x,y) or C=3 (x,y,score)
                  M = num_persons, T = frames, V = 17 joints, C = channels
        img_shape: (height, width) of source video frames
        threshold: confidence threshold for zeroing low-confidence joints
        mode: 'fix' (normalize by image dims) or 'auto' (normalize by bbox)
    
    Returns:
        normalized keypoint array, same shape, coordinates in ~[-1, 1]
    """
    h, w = img_shape
    keypoint = keypoint.copy().astype(np.float32)
    
    if mode == 'fix':
        keypoint[..., 0] = (keypoint[..., 0] - w / 2) / (w / 2)  # x
        keypoint[..., 1] = (keypoint[..., 1] - h / 2) / (h / 2)  # y
    else:  # 'auto'
        # mask for valid keypoints
        if keypoint.shape[-1] >= 3:
            mask = keypoint[..., 2] > threshold
        else:
            mask = np.ones(keypoint.shape[:-1], dtype=bool)
        x_vals = keypoint[..., 0][mask]
        y_vals = keypoint[..., 1][mask]
        if len(x_vals) > 0:
            x_min, x_max = x_vals.min(), x_vals.max()
            y_min, y_max = y_vals.min(), y_vals.max()
            if (x_max - x_min) > 10 and (y_max - y_min) > 10:
                keypoint[..., 0] = (keypoint[..., 0] - (x_max + x_min) / 2) / (x_max - x_min) * 2
                keypoint[..., 1] = (keypoint[..., 1] - (y_max + y_min) / 2) / (y_max - y_min) * 2
            else:
                keypoint[..., 0] = (keypoint[..., 0] - w / 2) / (w / 2)
                keypoint[..., 1] = (keypoint[..., 1] - h / 2) / (h / 2)
    
    # Zero out low-confidence joints
    if keypoint.shape[-1] >= 3:
        low_conf = keypoint[..., 2] <= threshold
        keypoint[low_conf] = 0
    
    return keypoint

# Verification assertion (use after applying prenormalize_2d):
assert np.all(np.abs(keypoint[..., :2]) <= 2.0), "Coordinates outside expected range after normalization"
```

### CTR-GCN Smoke Test (ENV-02)

```python
# Source: D-09 specification; PYSKL CTR-GCN config j.py (verified 2026-03-31)
# Run in vcc-ctrgcn environment

import torch
import numpy as np
from mmcv import Config
from pyskl.models import build_model

# Load CTR-GCN config and weights (J stream)
cfg = Config.fromfile('D:/libs/pyskl/configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/j.py')
model = build_model(cfg.model)
checkpoint = torch.load('D:/ViolenceCC/data/weights/ctrgcn/j.pth', map_location='cpu')
model.load_state_dict(checkpoint['state_dict'], strict=False)
model.eval()

# Synthetic COCO-17 input: N=1, C=3, T=64, V=17, M=1
# D-09: "Create synthetic tensor matching COCO-17 format (N=1, C=3, T=64, V=17, M=1)"
# Coordinates should be in normalized range [-1, 1] after PreNormalize2D
synthetic_input = torch.randn(1, 3, 64, 17, 1) * 0.5  # ~[-1,1] range

with torch.no_grad():
    output = model.backbone(synthetic_input)  # or model(synthetic_input) depending on PYSKL API

# Per D-09: assert output shape is (1, 256) and no NaN/Inf
assert output.shape == (1, 256), f"Expected (1, 256), got {output.shape}"
assert not torch.any(torch.isnan(output)), "NaN in CTR-GCN output"
assert not torch.any(torch.isinf(output)), "Inf in CTR-GCN output"
print(f"CTR-GCN smoke test PASSED. Output shape: {output.shape}, mean: {output.mean():.4f}")
```

**Note on PYSKL API:** The exact API call to extract backbone features (before the classification head) may require `model.backbone(x)` rather than `model(x)`. The plan should include a step to inspect the PYSKL model definition and verify the correct call to get the 256-d feature output rather than the 120-class logits.

### XD-Violence Zip Extraction (7-Zip)

```bash
# Source: D-12; 7-Zip confirmed at C:\Program Files\7-Zip\7z.exe (verified 2026-03-31)
# Run in Windows cmd or PowerShell; NOT in bash (path with spaces needs quoting)

# Create target directories
mkdir E:\XD_Violence\train
mkdir E:\XD_Violence\test

# Extract training zips (sequential — avoid overwrites)
"C:\Program Files\7-Zip\7z.exe" x E:\1-1004.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\1005-2004.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\2005-2804.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\2805-3319.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\3320-3954.zip -oE:\XD_Violence\train\ -y

# Extract test zip
"C:\Program Files\7-Zip\7z.exe" x E:\XD_violence_test_video.zip -oE:\XD_Violence\test\ -y

# Verify total count against expected 4,754 training videos
```

### NTFS Junction Point for data/features

```bash
# Source: D-06; Windows junction (no admin required unlike symlinks)
# Run in Windows cmd (not bash)

mkdir E:\features
mklink /J D:\ViolenceCC\data\features E:\features

# Verify in bash:
ls D:/ViolenceCC/data/features/  # should show E:\features\ contents (empty initially)
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| conda | All env creation | ✓ | 24.7.1 | — |
| NVIDIA RTX 4090 | GPU inference | ✓ | Driver 591.86, CUDA 13.1 | — |
| cudatoolkit=11.3 (via conda) | vcc-ctrgcn PyTorch | ✓ | confirmed in pkgs/main | — |
| CUDA 12.4 | vcc-main, vcc-skeleton | ✓ (12.6 nvcc; driver backward-compat) | 12.6 system | CUDA 12.4 wheels via conda |
| cuDNN 9.x | onnxruntime-gpu >= 1.19 | ✓ | v9.8 confirmed | — |
| mmcv-full 1.7.0 Windows wheel | vcc-ctrgcn | ✓ | `win_amd64` cp310 confirmed at OpenMMLab CDN | — |
| CTR-GCN weight URLs | ENV-02 | ✓ | All 4 files live, ~6.1 MB each | — |
| PYSKL repo (GitHub) | vcc-ctrgcn | ✓ | git available (2.47.1) | — |
| 7-Zip | XD-Violence extraction | ✓ | At `C:\Program Files\7-Zip\7z.exe` (not in PATH) | PowerShell Expand-Archive |
| PyPI (rtmlib, open-clip-torch) | vcc-skeleton, vcc-main | ✓ | Confirmed reachable | — |
| E: drive (1.9 TB, 1.5 TB free) | Feature storage, datasets | ✓ | 1.5 TB available | — |
| UCF-Crime PNG frames | ENV-02 prep, Phase 2 | ✓ | Fully extracted at E:\UCF_crime_dataset\ | — |
| XD-Violence videos | Phase 2 | ✗ (zips only) | 5 zips totaling 69.5 GB on E:\ | Extract during Phase 1 |
| I3D features | Phase 4 RTFM baseline | ✗ (zip only) | E:\i3d-features.zip (39 GB) | Extract during Phase 1 |
| UCF-Crime official split files | Phase 2 DATA-01 | ✗ | Not found in E:\UCF_crime_dataset\ | Must source from UCF-Crime paper/website |
| Windows Developer Mode / Admin | Symlink creation | ✗ | Symlinks fail without elevation | NTFS Junction (mklink /J) — no elevation required |

**Missing dependencies with no fallback:**
- UCF-Crime official split files (Anomaly_Train.txt, Anomaly_Test.txt, Temporal_Anomaly_Annotation.txt) — not present on E:\. Must be downloaded from the UCF-Crime dataset page or RTFM/MGFN GitHub repos. This blocks DATA-01 in Phase 2 but does not block Phase 1 ENV-01/ENV-02/ENV-03.

**Missing dependencies with fallback:**
- XD-Violence videos: extraction from zips is straightforward; 7-Zip is confirmed available
- Windows symlinks: NTFS junctions work identically for directory mounting without admin
- 7-Zip not in PATH: use full path `C:\Program Files\7-Zip\7z.exe`

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None currently — fresh repository, no Python files exist |
| Config file | None — Wave 0 must create pytest.ini |
| Quick run command | `conda run -n vcc-ctrgcn pytest tests/test_ctrgcn_smoke.py -x -v` |
| Full suite command | `conda run -n vcc-ctrgcn pytest tests/ -v` |

**Note:** Phase 1 has very limited testability. The success criteria are binary environment checks and a single forward pass assertion — these are smoke tests, not unit tests. The REQUIREMENTS.md explicitly excludes "Unit tests for ML internals" from scope. The CTR-GCN forward pass (ENV-02) is the only formally automatable test in this phase.

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-01 | Three envs activate and primary package imports succeed | smoke | `conda run -n vcc-skeleton python -c "import rtmlib; print('OK')"` | ❌ Wave 0 |
| ENV-01 | vcc-ctrgcn: `import pyskl; import mmcv` succeed | smoke | `conda run -n vcc-ctrgcn python -c "import pyskl; import mmcv; print('OK')"` | ❌ Wave 0 |
| ENV-01 | vcc-main: `import open_clip; import torch` succeed | smoke | `conda run -n vcc-main python -c "import open_clip; import torch; print(torch.__version__)"` | ❌ Wave 0 |
| ENV-02 | CTR-GCN forward pass: (1, 256) output, no NaN/Inf | unit | `conda run -n vcc-ctrgcn pytest tests/test_ctrgcn_smoke.py -x` | ❌ Wave 0 |
| ENV-03 | Project directory tree exists | smoke | `python -c "import pathlib; [print(p) for p in pathlib.Path('D:/ViolenceCC').iterdir()]"` | ❌ Wave 0 |

### Sampling Rate
- Per task commit: environment-specific import smoke test
- Per wave merge: full `pytest tests/test_ctrgcn_smoke.py`
- Phase gate: ENV-02 test green + all three env smoke tests pass before marking Phase 1 complete

### Wave 0 Gaps
- [ ] `tests/test_ctrgcn_smoke.py` — covers ENV-02 (CTR-GCN forward pass assertion)
- [ ] `tests/conftest.py` — shared path fixtures (weight paths, config paths)
- [ ] Framework install: `conda run -n vcc-ctrgcn pip install pytest` — pytest needed in vcc-ctrgcn

---

## Runtime State Inventory

Not applicable — Phase 1 is greenfield setup. No existing runtime state with old names to rename or migrate.

---

## Open Questions

1. **UCF-Crime official split files location**
   - What we know: Not present in `E:\UCF_crime_dataset\`. The Train/test directories contain only PNG frames.
   - What's unclear: Whether the files exist elsewhere on the machine or need to be downloaded.
   - Recommendation: Add a task to locate or download Anomaly_Train.txt, Anomaly_Test.txt, and Temporal_Anomaly_Annotation.txt from the UCF-Crime dataset page (http://crcv.ucf.edu/projects/real-world/) or from the RTFM repo's data/list/ directory. This is a dependency for Phase 2 DATA-01 but does not block Phase 1.

2. **PYSKL backbone API for 256-d feature extraction**
   - What we know: CTR-GCN with RecognizerGCN wrapper has a 120-class classification head. The 256-d feature is the backbone output before the head.
   - What's unclear: Whether `model.backbone(x)` or `model.extract_feat(x)` or another API is the correct call to get backbone features rather than 120-class logits.
   - Recommendation: During the ENV-02 task, inspect `pyskl/models/recognizers/recognizergcn.py` to find the correct API. Alternatively, call `model(x)` and verify output shape — if it returns 120 logits instead of 256 features, switch to `model.backbone(x)`.

3. **XD-Violence video count after extraction**
   - What we know: 5 zip archives totaling 69.5 GB; annotation file has 499 lines (test annotations only).
   - What's unclear: Whether the training videos total exactly 4,754 as stated in the literature. Overlapping video IDs between zip archives could cause overwrite without warning.
   - Recommendation: After extraction, count total MP4 files in `E:\XD_Violence\train\` and verify against expected count. Cross-reference 100 random filenames against the annotation file.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| openai/clip (frozen 2021) | open-clip-torch 3.3.0 | Ongoing since 2022 | Identical ViT-B/16 weights, active maintenance, Python 3.9+ |
| mmpose full stack for RTMPose | rtmlib 0.0.15 | 2024-present | No mmcv dependency; pure ONNX; simpler install |
| PyTorch 2.7+ for cu124 | PyTorch 2.6.0 + cu124 | 2025 | 2.7+ uses cu126/128; 2.6 is the cu124 sweet spot |

**Deprecated/outdated:**
- CUDA 11.3 toolkit: Required only for PYSKL in vcc-ctrgcn. Conda installs it as `cudatoolkit=11.3` inside the conda env; system CUDA (12.6) is unaffected.
- openai/clip: Last updated 2023; no Python 3.11 support; open-clip-torch is the active replacement.

---

## Sources

### Primary (HIGH confidence)
- `D:\ViolenceCC\.planning\research\STACK.md` — All version pins, install commands, compatibility matrix
- `D:\ViolenceCC\.planning\research\ARCHITECTURE.md` — Directory layout, component boundaries, data flow
- `D:\ViolenceCC\.planning\research\PITFALLS.md` — C1 (coordinate normalization), C6 (multi-person padding), M3 (VRAM overflow)
- PYSKL pose_related.py (raw GitHub, verified 2026-03-31) — PreNormalize2D exact algorithm
- PYSKL ctrgcn j.py config (GitHub, verified 2026-03-31) — Pipeline transforms, input format
- OpenMMLab CDN index (verified 2026-03-31): `mmcv_full-1.7.0-cp310-cp310-win_amd64.whl` confirmed present
- CTR-GCN weight URLs (HTTP HEAD verified 2026-03-31): All 4 files live at download.openmmlab.com

### Secondary (MEDIUM confidence)
- Environment audit (bash commands, 2026-03-31): conda 24.7.1, CUDA driver 591.86, RTX 4090, E: drive 1.5 TB free
- Dataset audit (bash commands, 2026-03-31): UCF-Crime extracted, XD-Violence as zips, no UCF split files found

### Tertiary (LOW confidence)
- PYSKL backbone API for 256-d extraction (`model.backbone(x)` vs `model.extract_feat(x)`) — needs verification during ENV-02 task implementation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All version pins from CLAUDE.md/STACK.md; Windows mmcv wheel confirmed live
- Architecture: HIGH — Directory layout from CONTEXT.md D-01 through D-10; no ambiguity
- Pitfalls: HIGH — C1/PreNormalize2D documented from PYSKL source; Windows-specific pitfalls (symlinks, PATH) verified empirically
- Environment availability: HIGH — Verified by direct bash commands on target machine

**Research date:** 2026-03-31
**Valid until:** 2026-05-01 (stable ecosystem; rtmlib/open-clip-torch release cadence is slow)
