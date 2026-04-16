<!-- GSD:project-start source:PROJECT.md -->
## Project

**ViolenceCC**

A PyTorch research codebase for weakly supervised violence-oriented video anomaly detection (VAD). Combines skeleton dynamics (CTR-GCN) with visual-language semantics (CLIP) in a dual-modal fusion framework, trained with MIL Ranking Loss. Includes a secondary investigation of TENT/SAR-style entropy-minimization TTA on LayerNorm-based fusion heads for cross-scene deployment robustness. This is the experiment code for a master's thesis.

**Core Value:** A working dual-modal (Skeleton + CLIP) fusion pipeline that produces reproducible frame-level AUC/AP numbers on UCF-Crime and XD-Violence, with complete ablation analysis and TTA experiments.

### Constraints

- **Hardware**: Single NVIDIA RTX 4090, 24GB VRAM — limits batch sizes and rules out end-to-end backbone training
- **Timeline**: 12 weeks total, ~6 weeks for main results, ~6 weeks for additional experiments + writing
- **Solo researcher**: No parallelization of human effort; code must be debuggable by one person
- **Thesis level**: Master's — needs reasonable contribution, not top-conference breakthrough
- **Reproducibility**: All experiments must use fixed seeds, same train/val splits, same evaluation protocol
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Python and CUDA Baseline
| Component | Recommended Version | Why |
|-----------|--------------------|----|
| Python | 3.11 | Supported by all libraries in this stack; 3.12 breaks PYSKL's legacy mmcv-full 1.7.x; 3.10 is minimum for PyTorch 2.6+ |
| CUDA Toolkit | 12.4 | Stable, widely tested with PyTorch 2.6; RTX 4090 (Ada Lovelace) fully supported; cu124 wheels available for PyTorch |
| cuDNN | 9.x | Required for onnxruntime-gpu >= 1.19.0 (the CUDA 12 variant); cuDNN 8.x NOT compatible with cuDNN 9 |
| OS | Windows 11 (target) | Project is on Windows; all libraries below support Windows |
### Core Training Framework
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| PyTorch | 2.6.0 | Deep learning framework for MIL training, TTA | Latest stable with cu124 wheels; 2.7.0 only supports cu126/cu128 which is less tested for research; 2.6.0 cu124 is the sweet spot |
| torchvision | 0.21.0 | Video I/O utilities, paired with PyTorch 2.6 | Version-locked with PyTorch; do not mix |
| torchaudio | 2.6.0 | Audio utilities if needed | Version-locked with PyTorch |
### Skeleton Extraction Environment (Separate)
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| rtmlib | 0.0.15 | RTMPose-based skeleton extraction, no mmcv dependency | Latest release (2026-02-10); the only library that runs RTMPose without the full mmcv/mmpose stack; pure ONNX Runtime inference |
| onnxruntime-gpu | 1.20.x (latest) | GPU-accelerated ONNX inference for RTMPose | Since v1.19.0, CUDA 12.x is the default; requires CUDA 12.x + cuDNN 9; verified compatible with RTX 4090 |
| opencv-python | 4.x (latest) | Frame decoding, image preprocessing | Required by rtmlib |
| opencv-contrib-python | 4.x (latest) | Extended OpenCV modules | Required by rtmlib |
| numpy | >= 1.23 | Array operations | Required by rtmlib |
### CTR-GCN / PYSKL Environment (Separate)
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| PyTorch | 1.12.1 (cu113) | CTR-GCN forward pass only | PYSKL's `pyskl_310.yaml` pins exactly this; mmcv-full 1.7.0 only compiles against PyTorch 1.x |
| mmcv-full | 1.7.0 | Required by PYSKL | PYSKL requires mmcv-full==1.7.0 exactly; mmcv 2.x API is incompatible |
| mmdet | 2.25.1 | PYSKL dependency | Pinned in PYSKL's official env file |
| mmpose | 0.29.0 | PYSKL dependency | Pinned in PYSKL's official env file |
| PYSKL | main branch (git clone) | CTR-GCN model loading and forward pass | Official repo; contains CTR-GCN configs and weight download scripts for NTU120 HRNet 2D checkpoints |
| CUDA Toolkit | 11.3 | Required by PyTorch 1.12.1 cu113 wheels | mmcv-full prebuilt wheels exist for cu113+torch1.12 |
| Python | 3.10 | PYSKL officially supports 3.10 (has `pyskl_310.yaml`) | |
# Install PyTorch 1.12.1 with CUDA 11.3
# Install mmcv-full 1.7.0 (prebuilt wheel for torch1.12 cu113)
# Clone and install PYSKL
### CLIP Feature Extraction
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| open-clip-torch | 3.3.0 | CLIP ViT-B/16 feature extraction | Latest stable (2026-02-27); supports Python 3.9-3.12; NOT the same as openai/clip which is unmaintained |
| timm | latest | Required by open-clip-torch for ConvNext/SigLIP models | open-clip docs say "ensure the latest timm is installed" |
- openai/clip is frozen at a 2021 release with no active maintenance
- open-clip-torch is actively maintained (v3.3.0 in Feb 2026 vs openai/clip last updated 2023)
- open-clip-torch supports the same ViT-B/16 openai weights via `pretrained='openai'`
- open-clip-torch supports Python 3.9+ vs openai/clip's older requirements
- VadCLIP (88.02% AUC, AAAI 2024) uses CLIP features; open-clip-torch provides identical ViT-B/16 outputs
### TTA Implementation
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| SAR (git clone) | main (ICLR 2023 Oral) | TENT-style and SAR-style entropy minimization | Official implementation at github.com/mr-eggplant/SAR; contains both `tent.py` and `sar.py` in the same repo |
| timm | 0.6.11+ (pinned in SAR) | Model utilities used by SAR reference code | SAR requires timm; use same version as open-clip-torch if no conflict |
# Original SAR/TENT: targets BatchNorm
# Adapted for this project: targets LayerNorm
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
### Video Decoding
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| decord | >= 0.6.0 | Fast video frame reading for CLIP extraction | Required by PYSKL; well-tested for variable-FPS sampling; widely used in VAD research |
| opencv-python | >= 4.7 | Frame-by-frame reading as fallback | More robust for corrupted videos in UCF-Crime |
### Optional: YOLO-World (Third Modality, Out of Critical Path)
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| ultralytics | >= 8.4.0 (latest) | YOLO-World-M inference for open-vocabulary object detection | YOLO-World is included in the Ultralytics package; pip install ultralytics is sufficient; ~78-104 FPS on RTX 4090 FP16 |
### Corruption Generation (for UCF-Crime-C)
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| kornia | >= 0.7 | Gaussian noise, motion blur, brightness shift applied to video tensors | GPU-accelerated, differentiable, PyTorch-native; supports batch augmentation of video frames |
| Pillow | >= 9.4 | JPEG compression corruption | Standard; `quality` parameter directly controls JPEG compression severity |
| scipy | >= 1.9 | Any statistical utilities needed for corruption calibration | Included in PYSKL env, safe to reuse |
- `kornia.filters.motion_blur()` and `kornia.augmentation.RandomGaussianNoise` handle spatial corruptions
- JPEG compression: use `PIL.Image.save(fp, format='JPEG', quality=Q)` with Q in {10, 20, 30, 40, 50} for 5 severity levels
- Brightness shift: simple tensor multiplication by factor in {0.5, 0.7, 1.3, 1.5, 2.0}
- Gaussian noise sigma in {0.1, 0.2, 0.3, 0.4, 0.5} for 5 severities
- Apply to RGB frames BEFORE CLIP feature extraction; for skeleton corruption, re-extract RTMPose on corrupted frames
## The Two-Environment Strategy
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
## Known Compatibility Issues
### ISSUE 1: PYSKL + PyTorch 2.x (CRITICAL)
### ISSUE 2: onnxruntime-gpu cuDNN version conflict
### ISSUE 3: decord on Windows with Python 3.11+
### ISSUE 4: mmcv-full 1.7.0 prebuilt wheel URL for CUDA 11.3 + PyTorch 1.12
### ISSUE 5: SAR timm version conflict with open-clip-torch
## Installation Summary
### Phase 1: Create skeleton extraction environment
### Phase 2: Create CTR-GCN feature extraction environment
### Phase 3: Create main training environment
# TTA: clone SAR repo and copy tent.py / sar.py into project
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

## Use playwright-cli when needed

If you need to search the web, you can use playwright-cli to help you. It can also test web-related applications.

## Execute codes in session when needed. User intervention is last resort

In the claude code sessions, if you can run the code yourself, you should. You can use sub-agents or seperate shells if the code is complex or need a lot of time to run. If the code has some nature that MUST need users to execute, give the user the complete steps and commands to do so.