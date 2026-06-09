# Technology Stack

**Analysis Date:** 2026-06-09

## Overview

ViolenceCC is a Python/PyTorch research codebase for weakly-supervised
violence-oriented video anomaly detection. It uses a **three-conda-environment
design** because the components have mutually incompatible dependency stacks
(legacy PyTorch 1.12/mmcv for CTR-GCN, ONNX-only RTMPose for skeletons, modern
PyTorch 2.6 for training). The three environments are documented in
`CLAUDE.md` (Technology Stack section), `envs/SETUP.md`, and pinned in
`envs/requirements-*.txt`.

## Languages

**Primary:**
- Python 3.11 — main training/eval/extraction code under `src/` and `scripts/`
  (the `vcc-main` and `vcc-skeleton` environments)
- Python 3.10 — CTR-GCN feature extraction only (the `vcc-ctrgcn` environment;
  pinned by PYSKL's legacy stack)

**Secondary:**
- PowerShell — build automation (`scripts/build_paper.ps1`), Windows-native
- LaTeX (pdflatex/acmart) — the CGW '26 paper under `paper/`
- YAML — experiment configuration (`configs/*.yaml`)

## Runtime

**The Three-Environment Design** (full matrix in `CLAUDE.md`):

| Environment | Python | PyTorch | CUDA | Purpose |
|-------------|--------|---------|------|---------|
| `vcc-main` | 3.11 | 2.6.0+cu124 | 12.4 | MIL training, CLIP/SigLIP2 extraction, TTA, evaluation, paper figures |
| `vcc-ctrgcn` | 3.10 | 1.12.1+cu113 | 11.3 | CTR-GCN 4-stream skeleton feature extraction (PYSKL forward pass) |
| `vcc-skeleton` | 3.11 | none (ONNX only) | 12.4 (onnxruntime) | RTMPose-m skeleton keypoint extraction |

Environments are invoked cross-process via `conda run -n <env> python ...`
(see usage headers in `scripts/extract_clip.py`, `scripts/extract_ctrgcn.py`,
`scripts/extract_skeletons.py`). They are NOT importable from one another.

**Why three environments:** PYSKL requires `mmcv-full==1.7.0`, which only
compiles against PyTorch 1.x (CLAUDE.md ISSUE 1). RTMPose via `rtmlib` needs
`onnxruntime-gpu` + cuDNN 9 with no PyTorch at all. Modern training needs
PyTorch 2.6. These cannot coexist in one env.

**Package Manager:**
- conda (tested 24.7.1 per `envs/SETUP.md`) for env creation + the PyTorch
  1.12/cudatoolkit 11.3 install in `vcc-ctrgcn`
- pip for everything else; PyTorch 2.6 installed via
  `--index-url https://download.pytorch.org/whl/cu124`
- Lockfile: no true lockfile; pinned `pip freeze` snapshots live in
  `envs/requirements-main.txt`, `envs/requirements-ctrgcn.txt`,
  `envs/requirements-skeleton.txt` (frozen 2026-03-31)

## Frameworks

**Core Training (`vcc-main`):**
- PyTorch 2.6.0+cu124 — MIL training, TTA, evaluation
- torchvision 0.21.0+cu124, torchaudio 2.6.0+cu124 (version-locked with torch)

**Skeleton Pipeline:**
- PYSKL (`main` branch, installed editable from `D:/libs/pyskl` via
  `pip install -e --no-deps`) — CTR-GCN model loading + forward pass.
  Configs/weights referenced at `D:/libs/pyskl/configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet`
  (see `scripts/extract_ctrgcn.py:61`)
- mmcv-full 1.7.0, mmdet 2.25.1, mmpose 0.29.0 — PYSKL dependencies (`vcc-ctrgcn`)
- rtmlib 0.0.15 — RTMPose-m inference; loaded as `rtmlib.Body(mode="balanced",
  backend="onnxruntime", device="cuda")` (`scripts/extract_skeletons.py:466-471`)
- onnxruntime-gpu 1.24.4 — GPU ONNX inference backend for RTMPose (`vcc-skeleton`)

**Vision-Language (`vcc-main`):**
- open-clip-torch 3.3.0 — loads all vision backbones via
  `open_clip.create_model_and_transforms(model_name, pretrained=...)`
  (`scripts/extract_clip.py:171`). Backbone registry at
  `scripts/extract_clip.py:119-148`:
  - `clip-vit-b-16` → `ViT-B-16` / `openai` (512-d → 1024-d mean+max)
  - `siglip2-base` → `ViT-B-16-SigLIP2-256` / `webli` (768-d → 1536-d)
  - `siglip2-so400m` → `ViT-SO400M-16-SigLIP2-256` / `webli` (1152-d)
  - `siglip2-giant` → `ViT-gopt-16-SigLIP2-256` / `webli` (1536-d → 3072-d)
- timm 1.0.26 — required by open-clip-torch for SigLIP/ConvNeXt model families

**Testing (`vcc-main`):**
- pytest 7.4.4 + pytest-timeout 2.3.1 — config in `pyproject.toml`
  (`[tool.pytest.ini_options]`), tests under `tests/`. Custom markers `e2e`
  and `requires_features` (the latter needs `E:/features/ucf/*.npy` on disk).
- pytest 9.0.2 in `vcc-ctrgcn` (separate pin)

**Build/Dev:**
- MiKTeX (latexmk + pdflatex + bibtex) — paper compilation via
  `scripts/build_paper.ps1`; engine flags in `paper/.latexmkrc`
- Strawberry Perl — required by MiKTeX's latexmk wrapper
  (`scripts/build_paper.ps1:67-81`)

## Key Dependencies

**Critical (`vcc-main`, `envs/requirements-main.txt`):**
- scikit-learn 1.8.0 — `roc_auc_score`, `average_precision_score` for
  frame-level AUC/AP (the thesis metrics)
- numpy 2.4.3 — array ops; feature caches are `.npy`
- scipy 1.17.1 — statistical utilities / corruption calibration

**Infrastructure:**
- h5py 3.16.0 — HDF5 feature storage support (partial reads for large caches)
- decord 0.6.0 — fast video frame reading for XD-Violence `.mp4`; `eva-decord`
  is the documented Windows fallback (`envs/SETUP.md:64-67`)
- Pillow 12.1.1 — UCF-Crime PNG loading (cv2 is NOT in `vcc-main`; see
  `scripts/extract_clip.py:70-77`) + JPEG-compression corruption
- kornia 0.8.2 — GPU-accelerated video corruptions (Gaussian noise, motion blur,
  brightness) for the UCF-Crime-C robustness/TTA study (`scripts/corruption.py`)
- tqdm 4.67.3 — progress bars across all three environments
- PyYAML 6.0.3 — config loading (`src/utils/config.py`)

**Experiment tracking:**
- wandb 0.25.1 — online mirror only; **disabled in every config** (see
  INTEGRATIONS.md). CSV logger is the source of truth.
- tensorboard 2.20.0 — installed, alternative tracker

**Skeleton env (`envs/requirements-skeleton.txt`):**
- opencv-python 4.13.0.92 + opencv-contrib-python 4.13.0.92 — frame decoding
  for RTMPose, numpy 2.4.4

## Configuration

**Experiment configs:** `configs/*.yaml` (~45 files). One YAML per
model-variant × dataset × backbone combination. Structure (see
`configs/gated_fusion.yaml`):
- `seed` (always 42), `dataset` (`ucf` / `xd` / `xd_i3d`)
- `paths` — feature cache + splits + results + snippet-boundary dirs (all on
  `E:/`)
- `model` — variant + dims (e.g. `skel_dim: 256`, `clip_dim: 1024`,
  `shared_dim: 256`)
- `data` — `T: 32`, `batch_size`, `num_workers`, `pin_memory`
- `train` — `lr`, `weight_decay`, `epochs`, MIL hyperparams (`k_topk`,
  `margin`, `lam_sparse`, `lam_smooth`)
- `wandb` — `project: violencecc`, `mode: disabled`, `tags`

Loaded by `src/utils/config.py`; consumed by `src/train.py`.

**Backbone-specific dim conventions** (from config inspection):
- CLIP ViT-B/16 mean+max → `clip_dim: 1024`
- SigLIP2-base → `clip_dim: 1536` (`configs/clip_only_siglip2.yaml`)
- SigLIP2-giant → 3072-d; RTFM I3D baseline → `i3d_dim: 1024`
  (`configs/rtfm_i3d.yaml`)

**Build config:** `paper/.latexmkrc` (pdflatex mode, bibtex, nonstopmode,
synctex, MiKTeX auto-installer).

**Secrets:** No `.env` file present. Overleaf MCP credentials come from
environment variables `OVERLEAF_PROJECT_ID` / `OVERLEAF_GIT_TOKEN`
(`.mcp.json`); wandb auth would use `WANDB_API_KEY` / `~/.netrc` but is unset
(configs run `mode: disabled`).

## Platform Requirements

**Development:**
- Windows 11 (target; all paths and scripts are Windows-native, paper build is
  PowerShell)
- Single NVIDIA RTX 4090, 24 GB VRAM (driver 591.86 per `envs/SETUP.md`)
- ~1.5 TB free on the `E:` drive for datasets + feature caches
- cuDNN 9.x for CUDA 12, installed at
  `C:\Program Files\NVIDIA\CUDNN\v9.8\bin\12.8` and prepended to PATH at runtime
  for onnxruntime (`scripts/extract_skeletons.py:62-64`)
- 7-Zip at `C:\Program Files\7-Zip\7z.exe` for dataset extraction
- MiKTeX + Strawberry Perl for the paper build

**Production:**
- Not applicable — research codebase, not deployed. "Deployment" robustness is
  itself the research subject (cross-scene TTA), not an ops target.

## Known Compatibility Issues (from `CLAUDE.md`)

- **ISSUE 1 (CRITICAL):** PYSKL + PyTorch 2.x incompatible → forces the
  separate `vcc-ctrgcn` env on PyTorch 1.12
- **ISSUE 2:** onnxruntime-gpu needs cuDNN 9 DLLs on PATH (handled at
  `scripts/extract_skeletons.py:56-64`)
- **ISSUE 3:** decord on Windows + Python 3.11 → `eva-decord` fallback
- **ISSUE 5:** SAR's timm pin vs open-clip-torch's timm requirement

---

*Stack analysis: 2026-06-09*
