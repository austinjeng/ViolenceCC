# Technology Stack

**Project:** ViolenceCC — Dual-Modal Weakly Supervised VAD (Skeleton GCN + CLIP)
**Researched:** 2026-03-31
**Research Mode:** Ecosystem + Compatibility Verification

---

## Recommended Stack

### Python and CUDA Baseline

| Component | Recommended Version | Why |
|-----------|--------------------|----|
| Python | 3.11 | Supported by all libraries in this stack; 3.12 breaks PYSKL's legacy mmcv-full 1.7.x; 3.10 is minimum for PyTorch 2.6+ |
| CUDA Toolkit | 12.4 | Stable, widely tested with PyTorch 2.6; RTX 4090 (Ada Lovelace) fully supported; cu124 wheels available for PyTorch |
| cuDNN | 9.x | Required for onnxruntime-gpu >= 1.19.0 (the CUDA 12 variant); cuDNN 8.x NOT compatible with cuDNN 9 |
| OS | Windows 11 (target) | Project is on Windows; all libraries below support Windows |

**CRITICAL NOTE on Python version:** PYSKL's official `pyskl_310.yaml` pins PyTorch to 1.12.1 + CUDA 11.3 + mmcv-full 1.7.0. This is a legacy environment. The strategy recommended here uses **two separate conda environments** — see "The Two-Environment Strategy" section below.

---

### Core Training Framework

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| PyTorch | 2.6.0 | Deep learning framework for MIL training, TTA | Latest stable with cu124 wheels; 2.7.0 only supports cu126/cu128 which is less tested for research; 2.6.0 cu124 is the sweet spot |
| torchvision | 0.21.0 | Video I/O utilities, paired with PyTorch 2.6 | Version-locked with PyTorch; do not mix |
| torchaudio | 2.6.0 | Audio utilities if needed | Version-locked with PyTorch |

**Install (main training env):**
```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

**Why NOT PyTorch 2.11.0 (latest as of March 2026):** PyTorch 2.11 requires Python >= 3.10 and supports CUDA 12.6/12.8/13.0 only. None of these have been tested with PYSKL's dependency chain. Stay on 2.6 for the main env; it is stable, well-documented, and covers all project needs.

**Why NOT PyTorch 1.x:** The PYSKL-compatible version (1.12.1) is over 3 years old and lacks flash attention, torch.compile, and modern fp16 APIs needed for efficient CLIP feature extraction.

---

### Skeleton Extraction Environment (Separate)

This is the **first** conda environment, used only for Stage 1 skeleton extraction (rtmlib + ONNX Runtime). It does NOT need PyTorch at all.

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| rtmlib | 0.0.15 | RTMPose-based skeleton extraction, no mmcv dependency | Latest release (2026-02-10); the only library that runs RTMPose without the full mmcv/mmpose stack; pure ONNX Runtime inference |
| onnxruntime-gpu | 1.20.x (latest) | GPU-accelerated ONNX inference for RTMPose | Since v1.19.0, CUDA 12.x is the default; requires CUDA 12.x + cuDNN 9; verified compatible with RTX 4090 |
| opencv-python | 4.x (latest) | Frame decoding, image preprocessing | Required by rtmlib |
| opencv-contrib-python | 4.x (latest) | Extended OpenCV modules | Required by rtmlib |
| numpy | >= 1.23 | Array operations | Required by rtmlib |

**Install (skeleton extraction env):**
```bash
conda create -n vcc-skeleton python=3.11 -y
conda activate vcc-skeleton
pip install rtmlib -i https://pypi.org/simple
pip install onnxruntime-gpu  # installs latest with CUDA 12.x support
```

**RTMPose model to use:** RTMPose-m (256x192) for body 17-keypoint (COCO-17). The `-m` variant provides the best accuracy/speed tradeoff: ~75.8% AP on COCO, >200 FPS on RTX 4090 with onnxruntime-gpu. Do NOT use RTMPose-t (too low AP for violence detection) or RTMPose-x (marginal AP gain, ~3x slower).

**Detector:** YOLOX-m or RTMO for person detection. rtmlib bundles these automatically when using the `Body` or `Wholebody` API.

**Confidence:** HIGH — rtmlib 0.0.15 verified on PyPI (2026-02-10); onnxruntime CUDA 12.x support documented on official onnxruntime.ai.

---

### CTR-GCN / PYSKL Environment (Separate)

This is the **second** conda environment, used only for CTR-GCN forward-pass feature extraction. The mmcv-full 1.x dependency makes it impossible to share with the modern PyTorch training env.

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| PyTorch | 1.12.1 (cu113) | CTR-GCN forward pass only | PYSKL's `pyskl_310.yaml` pins exactly this; mmcv-full 1.7.0 only compiles against PyTorch 1.x |
| mmcv-full | 1.7.0 | Required by PYSKL | PYSKL requires mmcv-full==1.7.0 exactly; mmcv 2.x API is incompatible |
| mmdet | 2.25.1 | PYSKL dependency | Pinned in PYSKL's official env file |
| mmpose | 0.29.0 | PYSKL dependency | Pinned in PYSKL's official env file |
| PYSKL | main branch (git clone) | CTR-GCN model loading and forward pass | Official repo; contains CTR-GCN configs and weight download scripts for NTU120 HRNet 2D checkpoints |
| CUDA Toolkit | 11.3 | Required by PyTorch 1.12.1 cu113 wheels | mmcv-full prebuilt wheels exist for cu113+torch1.12 |
| Python | 3.10 | PYSKL officially supports 3.10 (has `pyskl_310.yaml`) | |

**Install (CTR-GCN env):**
```bash
conda create -n vcc-ctrgcn python=3.10 -y
conda activate vcc-ctrgcn
# Install PyTorch 1.12.1 with CUDA 11.3
conda install pytorch==1.12.1 torchvision==0.13.1 torchaudio==0.12.1 cudatoolkit=11.3 -c pytorch -c conda-forge
# Install mmcv-full 1.7.0 (prebuilt wheel for torch1.12 cu113)
pip install mmcv-full==1.7.0 -f https://download.openmmlab.com/mmcv/dist/cu113/torch1.12.0/index.html
# Clone and install PYSKL
git clone https://github.com/kennymckormick/pyskl.git
cd pyskl && pip install -e .
```

**Critical: mmcv-full 1.5.0 vs 1.7.0 for PYSKL**

PYSKL's `requirements.txt` pins `mmcv-full==1.5.0` but `pyskl_310.yaml` uses `mmcv-full==1.7.0`. Use **1.7.0** — it is the latest 1.x release with prebuilt wheels for PyTorch 1.12, and PYSKL's codebase is compatible with it. The 1.5.0 pin in requirements.txt appears to be an outdated default; the conda env file is the authoritative source.

**Pretrained weights to download (CTR-GCN NTU120 HRNet 2D, COCO-17 format):**
```
http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/j.pth   (Joint, 82.2%)
http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/b.pth   (Bone, 84.6%)
http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/jm.pth  (Joint Motion, 82.3%)
http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/bm.pth  (Bone Motion, 82.1%)
```

All four weights use COCO-17 graph topology (17 joints, natively compatible with RTMPose output). No joint mapping required.

**Confidence:** HIGH for the version pins (verified against `pyskl_310.yaml` from official repo). MEDIUM for the CUDA 11.3 environment on a machine primarily running CUDA 12.4 — requires careful conda isolation; PYSKL's PyTorch 2.x support is labeled "experimental, no performance warranty."

---

### CLIP Feature Extraction

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| open-clip-torch | 3.3.0 | CLIP ViT-B/16 feature extraction | Latest stable (2026-02-27); supports Python 3.9-3.12; NOT the same as openai/clip which is unmaintained |
| timm | latest | Required by open-clip-torch for ConvNext/SigLIP models | open-clip docs say "ensure the latest timm is installed" |

**Install (add to main training env):**
```bash
pip install open-clip-torch timm
```

**Model to use:** `ViT-B-16` with pretrain `openai` (the original OpenAI CLIP weights, 400M image-text pairs). Load with:
```python
import open_clip
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-16', pretrained='openai')
tokenizer = open_clip.get_tokenizer('ViT-B-16')
```

**Why open-clip-torch over openai/clip:**
- openai/clip is frozen at a 2021 release with no active maintenance
- open-clip-torch is actively maintained (v3.3.0 in Feb 2026 vs openai/clip last updated 2023)
- open-clip-torch supports the same ViT-B/16 openai weights via `pretrained='openai'`
- open-clip-torch supports Python 3.9+ vs openai/clip's older requirements
- VadCLIP (88.02% AUC, AAAI 2024) uses CLIP features; open-clip-torch provides identical ViT-B/16 outputs

**Why NOT CLIP ViT-L/14:** VRAM constraint. ViT-B/16 outputs 512-d ([CLS] token). At 1 FPS extraction, throughput on RTX 4090 is ~700-1000 img/s in FP16, which is more than sufficient for batch pre-extraction. ViT-L/14 is 1.5x slower with only marginal feature quality improvement for this frozen-backbone use case.

**Confidence:** HIGH — PyPI version 3.3.0 verified; Python requirement >=3.9 verified.

---

### TTA Implementation

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| SAR (git clone) | main (ICLR 2023 Oral) | TENT-style and SAR-style entropy minimization | Official implementation at github.com/mr-eggplant/SAR; contains both `tent.py` and `sar.py` in the same repo |
| timm | 0.6.11+ (pinned in SAR) | Model utilities used by SAR reference code | SAR requires timm; use same version as open-clip-torch if no conflict |

**TENT-style vs SAR-style adaptation (both from SAR repo):**

The SAR repo contains implementations of both TENT (`tent.py`) and SAR (`sar.py`). For this project, these will be adapted to update only LayerNorm affine parameters (gamma, beta) instead of BatchNorm parameters. This requires minor surgery on the `configure_model()` function — replace BN module targeting with LN module targeting:

```python
# Original SAR/TENT: targets BatchNorm
for m in model.modules():
    if isinstance(m, nn.BatchNorm2d):
        m.requires_grad_(True)

# Adapted for this project: targets LayerNorm
for m in model.modules():
    if isinstance(m, nn.LayerNorm):
        m.weight.requires_grad_(True)
        m.bias.requires_grad_(True)
```

The rest of the entropy minimization loop (forward pass, entropy loss computation, backward, optimizer step) transfers directly — LayerNorm has gamma/beta parameters analogous to BN's affine parameters.

**SAR's stated requirements:** PyTorch 1.9.0 + timm 0.6.11. These are minimums; the code runs on PyTorch 2.x with no modification needed.

**Confidence:** HIGH for SAR repo availability and implementation quality (ICLR 2023 Oral). MEDIUM for LayerNorm adaptation — the BN-to-LN transfer is methodologically novel; the entropy minimization math is identical but LN's lack of running statistics means no population statistics to update, only affine params. This is a research-level uncertainty, not a software compatibility issue.

---

### MIL Training and Evaluation

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| scikit-learn | >= 1.3 | `roc_auc_score`, `average_precision_score` for frame-level AUC/AP | Standard evaluation; the official UCF-Crime and XD-Violence benchmarks use sklearn-compatible metrics |
| numpy | >= 1.23 | Array operations, feature caching | Universal dependency |
| h5py | >= 3.8 | Feature cache storage (HDF5 format) | Better than .npy for structured multi-modal feature storage; supports partial reads |
| tqdm | >= 4.65 | Progress bars for extraction loops | Essential for monitoring 20-40h extraction jobs |
| PyYAML | >= 6.0 | Config file management | Cleaner than argparse for experiment configs |
| wandb | >= 0.16 | Experiment tracking (optional but recommended) | Tracks AUC/AP curves, config diffs across ablations; free for academic use |
| tensorboard | >= 2.14 | Alternative to wandb | Built into PyTorch; use if wandb is not preferred |

**Confidence:** HIGH — all standard scientific Python libraries, actively maintained.

---

### Video Decoding

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| decord | >= 0.6.0 | Fast video frame reading for CLIP extraction | Required by PYSKL; well-tested for variable-FPS sampling; widely used in VAD research |
| opencv-python | >= 4.7 | Frame-by-frame reading as fallback | More robust for corrupted videos in UCF-Crime |

**Note on decord alternatives:** `torchcodec` (PyTorch official, 2024) is faster than decord for batch training pipelines but adds a PyTorch dependency to the skeleton extraction env. Since this project pre-extracts all features offline, decord's throughput is sufficient. Use decord for feature extraction; use torchcodec only if decord fails on specific XD-Violence files.

**Confidence:** MEDIUM — decord is no longer under active development (the dmlc/decord repo shows limited 2024+ activity); however, it remains stable for offline feature extraction. eva-decord is a community maintained fork if issues arise.

---

### Optional: YOLO-World (Third Modality, Out of Critical Path)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| ultralytics | >= 8.4.0 (latest) | YOLO-World-M inference for open-vocabulary object detection | YOLO-World is included in the Ultralytics package; pip install ultralytics is sufficient; ~78-104 FPS on RTX 4090 FP16 |

**Install only when needed (Week 7+ if main results are strong):**
```bash
pip install ultralytics
```

**Confidence:** HIGH — ultralytics package on PyPI; Python >=3.8 requirement confirmed.

---

### Corruption Generation (for UCF-Crime-C)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| kornia | >= 0.7 | Gaussian noise, motion blur, brightness shift applied to video tensors | GPU-accelerated, differentiable, PyTorch-native; supports batch augmentation of video frames |
| Pillow | >= 9.4 | JPEG compression corruption | Standard; `quality` parameter directly controls JPEG compression severity |
| scipy | >= 1.9 | Any statistical utilities needed for corruption calibration | Included in PYSKL env, safe to reuse |

**Corruption implementation notes:**
- `kornia.filters.motion_blur()` and `kornia.augmentation.RandomGaussianNoise` handle spatial corruptions
- JPEG compression: use `PIL.Image.save(fp, format='JPEG', quality=Q)` with Q in {10, 20, 30, 40, 50} for 5 severity levels
- Brightness shift: simple tensor multiplication by factor in {0.5, 0.7, 1.3, 1.5, 2.0}
- Gaussian noise sigma in {0.1, 0.2, 0.3, 0.4, 0.5} for 5 severities
- Apply to RGB frames BEFORE CLIP feature extraction; for skeleton corruption, re-extract RTMPose on corrupted frames

**Confidence:** HIGH — kornia is actively maintained on PyPI; JPEG corruption with Pillow is a standard approach.

---

## The Two-Environment Strategy

This is the key architectural decision for the stack. The mmcv-full 1.x legacy dependency in PYSKL makes it incompatible with modern PyTorch in the same conda environment.

```
Environment A: vcc-skeleton (Python 3.11, onnxruntime-gpu)
  Purpose: Stage 1a - RTMPose skeleton extraction
  Key libs: rtmlib 0.0.15, onnxruntime-gpu 1.20.x
  No PyTorch needed

Environment B: vcc-ctrgcn (Python 3.10, PyTorch 1.12.1+cu113)
  Purpose: Stage 1b - CTR-GCN frozen feature extraction
  Key libs: PyTorch 1.12.1, mmcv-full 1.7.0, PYSKL
  Output: .npy or .h5 feature cache files

Environment C: vcc-main (Python 3.11, PyTorch 2.6.0+cu124)
  Purpose: Stage 2 (MIL training) + Stage 3 (TTA) + CLIP extraction
  Key libs: PyTorch 2.6, open-clip-torch 3.3.0, SAR, scikit-learn, wandb
  Reads cached features from Stage 1; no backbone code needed
```

**The handoff:** All three stages write feature tensors to disk. The `vcc-main` environment reads these files and never imports mmcv or PYSKL. This cleanly separates legacy dependency concerns from the actual research code.

**Why this works:** CTR-GCN is frozen; it is used purely as a feature extractor. Once features are cached to disk (once per dataset), the `vcc-ctrgcn` environment is only invoked again if the extraction needs to be re-run (e.g., different windowing strategy). The vast majority of iteration happens in `vcc-main`.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Skeleton extraction | rtmlib + RTMPose-m | mmpose full stack | mmpose requires mmcv 2.x which conflicts with PYSKL's mmcv 1.x; rtmlib is the lighter, purpose-built alternative |
| Skeleton extraction | rtmlib + RTMPose-m | AlphaPose | More accurate multi-person but requires separate conda env, slower, more engineering overhead |
| CLIP library | open-clip-torch 3.3.0 | openai/clip | openai/clip is frozen at 2021, unmaintained; open-clip-torch provides identical ViT-B/16 openai weights with active support |
| CLIP model size | ViT-B/16 | ViT-L/14 | ViT-L/14 requires ~2x VRAM for same batch size; marginal improvement for frozen feature extraction; no justification for the cost |
| TTA source | SAR repo (adapted) | Custom TENT implementation | SAR repo contains both TENT and SAR; saves implementation effort; ICLR 2023 Oral code quality is high |
| Feature storage | HDF5 (h5py) | Raw .npy files | HDF5 supports partial reads (critical for large XD-Violence ~30GB cache); numpy arrays require loading entire file |
| Video decoding | decord | torchcodec | torchcodec requires PyTorch in skeleton env; decord is self-contained and sufficient for offline extraction |
| Experiment tracking | wandb | MLflow | wandb has better hyperparameter sweep integration; free for academic; MLflow adds server overhead |
| Corruption generation | kornia + Pillow | Custom numpy | kornia is GPU-accelerated and batch-capable; faster for generating 20-condition corruption sets |
| GCN training framework | PYSKL (feature extraction only) | PyTorch Geometric | PyG would require reimplementing CTR-GCN graph topology from scratch; PYSKL already has the exact config and weights |

---

## Complete Version Compatibility Matrix

| Component | vcc-skeleton | vcc-ctrgcn | vcc-main |
|-----------|-------------|-----------|---------|
| Python | 3.11 | 3.10 | 3.11 |
| PyTorch | not required | 1.12.1 | 2.6.0 |
| CUDA | 12.4 (onnxruntime) | 11.3 (PyTorch) | 12.4 (PyTorch) |
| cuDNN | 9.x (for ORT) | 8.3.2 (PyTorch 1.12 pin) | 9.x (PyTorch 2.6) |
| mmcv-full | not required | 1.7.0 | not required |
| rtmlib | 0.0.15 | not required | not required |
| onnxruntime-gpu | 1.20.x | not required | not required |
| open-clip-torch | not required | not required | 3.3.0 |
| PyTorch version age | N/A | 2022 (legacy) | 2025 (current) |

**The CUDA version mismatch (11.3 in ctrgcn, 12.4 in main) is expected and safe** because conda isolates these environments. The NVIDIA driver for RTX 4090 supports CUDA 11.x through 12.x via backwards compatibility. Conda manages the toolkit per-environment.

---

## Known Compatibility Issues

### ISSUE 1: PYSKL + PyTorch 2.x (CRITICAL)

**Problem:** PYSKL's `requirements.txt` hardcodes `mmcv-full==1.5.0`. mmcv-full 1.x was only compiled against PyTorch 1.x. There are no official prebuilt mmcv-full 1.x wheels for PyTorch 2.x.

**Community workaround exists:** A fork at `github.com/c7w/mmcv-full-1.7.1-torch-2` provides patched mmcv-full 1.7.1 that compiles against PyTorch 2.x, but this is unofficial and adds maintenance risk.

**Recommended mitigation:** Use the `vcc-ctrgcn` environment with PyTorch 1.12.1 as described above. The CTR-GCN model only needs to run forward pass once per dataset — this is a one-time cost. Do not attempt to mix PYSKL and PyTorch 2.x in the same environment.

**Confidence:** HIGH — this incompatibility is documented in multiple GitHub issues and is a known ecosystem limitation.

### ISSUE 2: onnxruntime-gpu cuDNN version conflict

**Problem:** onnxruntime-gpu >= 1.19.0 requires cuDNN 9.x. PYSKL's PyTorch 1.12.1 (cu113) was built with cuDNN 8.3.2. If both are installed in the same environment, cuDNN version conflicts will cause runtime errors.

**Mitigation:** Enforced by the two-environment strategy. onnxruntime-gpu is only in `vcc-skeleton`; PyTorch 1.12.1 is only in `vcc-ctrgcn`. They never coexist.

### ISSUE 3: decord on Windows with Python 3.11+

**Problem:** decord has sporadic Windows installation issues on Python 3.11+. The `eva-decord` fork (community-maintained) is more reliable on Windows.

**Mitigation:** Try `pip install decord` first; if it fails with binary compatibility errors, use `pip install eva-decord`. The API is identical.

### ISSUE 4: mmcv-full 1.7.0 prebuilt wheel URL for CUDA 11.3 + PyTorch 1.12

**Problem:** OpenMMLab's prebuilt mmcv-full wheel URLs use exact CUDA and PyTorch version numbers. The correct URL pattern is:
```
https://download.openmmlab.com/mmcv/dist/cu113/torch1.12.0/index.html
```
Using `torch1.12.1` in the URL (note: the URL uses `1.12.0` even for PyTorch 1.12.1 installs) is the documented behavior — the 1.x.0 wheel is compatible with 1.x.1.

### ISSUE 5: SAR timm version conflict with open-clip-torch

**Problem:** SAR was tested with timm 0.6.11. open-clip-torch 3.3.0 recommends "latest timm." Modern timm (1.x) has breaking API changes vs timm 0.6.x.

**Mitigation:** SAR only uses timm for its reference classification model wrappers (not used in this project's adaptation of SAR). The entropy minimization logic in `sar.py` and `tent.py` is pure PyTorch and does not call timm APIs. Install latest timm for open-clip-torch; the adapted SAR code will not break.

---

## Installation Summary

### Phase 1: Create skeleton extraction environment

```bash
conda create -n vcc-skeleton python=3.11 -y
conda activate vcc-skeleton
pip install rtmlib -i https://pypi.org/simple
pip install onnxruntime-gpu  # CUDA 12.x variant, latest
pip install opencv-python opencv-contrib-python numpy tqdm
```

### Phase 2: Create CTR-GCN feature extraction environment

```bash
conda create -n vcc-ctrgcn python=3.10 -y
conda activate vcc-ctrgcn
conda install pytorch==1.12.1 torchvision==0.13.1 cudatoolkit=11.3 -c pytorch -c conda-forge
pip install mmcv-full==1.7.0 -f https://download.openmmlab.com/mmcv/dist/cu113/torch1.12.0/index.html
pip install mmdet==2.25.1 mmpose==0.29.0
git clone https://github.com/kennymckormick/pyskl.git
cd pyskl && pip install -e . --no-deps
cd ..
pip install decord numpy scipy tqdm
```

### Phase 3: Create main training environment

```bash
conda create -n vcc-main python=3.11 -y
conda activate vcc-main
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install open-clip-torch timm
pip install scikit-learn h5py numpy scipy tqdm PyYAML wandb tensorboard
pip install kornia Pillow
pip install decord  # or eva-decord if decord fails on Windows
# TTA: clone SAR repo and copy tent.py / sar.py into project
git clone https://github.com/mr-eggplant/SAR.git
```

---

## Confidence Assessment

| Area | Confidence | Evidence |
|------|------------|---------|
| rtmlib version (0.0.15) | HIGH | Verified on PyPI, released 2026-02-10 |
| onnxruntime-gpu CUDA 12.x requirement | HIGH | Official onnxruntime.ai documentation |
| PYSKL + PyTorch 1.12.1 + mmcv-full 1.7.0 | HIGH | Verified from official `pyskl_310.yaml` |
| PYSKL + PyTorch 2.x incompatibility | HIGH | Multiple GitHub issues, no official resolution |
| open-clip-torch 3.3.0 | HIGH | Verified on PyPI, released 2026-02-27 |
| PyTorch 2.6.0 as main env version | MEDIUM | Latest stable with cu124 wheels confirmed; 2.11.0 is newer but cu124 wheel availability for 2.11 unverified at research time |
| SAR implementation quality | HIGH | ICLR 2023 Oral; official GitHub |
| LN-based TENT/SAR adaptation | MEDIUM | The BN-to-LN methodological transfer is the project's research contribution; software feasibility is HIGH, but effectiveness is uncertain by design |
| decord Windows compatibility | MEDIUM | Known Windows issues on Python 3.11+; eva-decord is fallback |
| CTR-GCN weight download URLs | HIGH | Verified in PRD v2.3 from direct PYSKL repo inspection |

---

## Sources

- rtmlib PyPI: https://pypi.org/project/rtmlib/
- rtmlib GitHub: https://github.com/Tau-J/rtmlib
- PYSKL GitHub: https://github.com/kennymckormick/pyskl
- PYSKL pyskl_310.yaml (verified): PyTorch 1.12.1 + mmcv-full 1.7.0 + Python 3.10
- open-clip-torch PyPI: https://pypi.org/project/open-clip-torch/ (v3.3.0, 2026-02-27)
- PyTorch PyPI: https://pypi.org/project/torch/ (v2.11.0 latest, Python >=3.10)
- PyTorch install page: https://pytorch.org/get-started/locally/
- SAR GitHub: https://github.com/mr-eggplant/SAR
- onnxruntime CUDA provider: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html
- mmcv-full 1.7.1 torch-2 fork: https://github.com/c7w/mmcv-full-1.7.1-torch-2
- VadCLIP GitHub: https://github.com/nwpu-zxr/VadCLIP
- RTFM GitHub: https://github.com/tianyu0207/RTFM
- PyTorch 2.6.0 release: https://dev-discuss.pytorch.org/t/pytorch-2-6-0-general-availability/2762
- kornia documentation: https://kornia.readthedocs.io/en/latest/
- Ultralytics YOLO: https://docs.ultralytics.com/quickstart/
