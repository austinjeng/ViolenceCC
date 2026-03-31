# ViolenceCC Environment Setup

Step-by-step guide for setting up the three conda environments on Windows.
All commands are for Windows cmd or PowerShell unless noted.

## Prerequisites

- Conda (tested with 24.7.1)
- NVIDIA GPU with CUDA support (tested with RTX 4090, driver 591.86)
- 7-Zip at `C:\Program Files\7-Zip\7z.exe` (for dataset extraction)
- ~1.5 TB free on E: drive for features and datasets

## Environment 1: vcc-skeleton (RTMPose skeleton extraction)

```bash
conda create -n vcc-skeleton python=3.11 -y
conda activate vcc-skeleton
pip install rtmlib==0.0.15
pip install onnxruntime-gpu
pip install opencv-python opencv-contrib-python numpy tqdm
```

**Verify:**
```bash
conda activate vcc-skeleton
python -c "import rtmlib; print('rtmlib OK')"
python -c "import onnxruntime; print('ORT version:', onnxruntime.__version__); print('CUDA available:', 'CUDAExecutionProvider' in onnxruntime.get_available_providers())"
```

## Environment 2: vcc-ctrgcn (CTR-GCN feature extraction)

```bash
conda create -n vcc-ctrgcn python=3.10 -y
conda activate vcc-ctrgcn
conda install pytorch==1.12.1 torchvision==0.13.1 cudatoolkit=11.3 -c pytorch -c conda-forge
pip install mmcv-full==1.7.0 -f https://download.openmmlab.com/mmcv/dist/cu113/torch1.12.0/index.html
pip install mmdet==2.25.1 mmpose==0.29.0
pip install -e D:/libs/pyskl --no-deps
pip install decord numpy scipy tqdm pytest
```

**Important:** The mmcv-full wheel URL uses `torch1.12.0` (not `torch1.12.1`) in the path. This is correct -- OpenMMLab indexes by minor version.

**Verify:**
```bash
conda activate vcc-ctrgcn
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
python -c "import mmcv; print('mmcv:', mmcv.__version__)"
python -c "import pyskl; print('PYSKL OK')"
```

## Environment 3: vcc-main (Training, CLIP extraction, evaluation)

```bash
conda create -n vcc-main python=3.11 -y
conda activate vcc-main
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install open-clip-torch==3.3.0 timm
pip install scikit-learn h5py numpy scipy tqdm PyYAML wandb tensorboard
pip install kornia Pillow
pip install decord
```

If `decord` fails on Windows Python 3.11, install the fork instead:
```bash
pip install eva-decord
```

**Verify:**
```bash
conda activate vcc-main
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
python -c "import open_clip; print('open-clip OK')"
```

## Dataset Preparation

### XD-Violence (extract from zips on E:\)

```cmd
mkdir E:\XD_Violence\train
mkdir E:\XD_Violence\test
"C:\Program Files\7-Zip\7z.exe" x E:\1-1004.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\1005-2004.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\2005-2804.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\2805-3319.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\3320-3954.zip -oE:\XD_Violence\train\ -y
"C:\Program Files\7-Zip\7z.exe" x E:\XD_violence_test_video.zip -oE:\XD_Violence\test\ -y
```

### I3D Features (for RTFM baseline in Phase 4)

```cmd
"C:\Program Files\7-Zip\7z.exe" x E:\i3d-features.zip -oE:\i3d-features\ -y
```

### Feature Directory Junction

```cmd
mkdir E:\features
mklink /J D:\ViolenceCC\data\features E:\features
```

If junction creation fails, use direct path `E:\features\` in YAML configs instead.

## CTR-GCN Weights

Download NTU120 HRNet 2D pretrained weights (4 streams, ~6.1 MB each):

```bash
mkdir -p D:/ViolenceCC/data/weights/ctrgcn
# Download URLs from PYSKL repo (verified 2026-03-31):
# j.pth: https://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/j.pth
# b.pth: https://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/b.pth
# jm.pth: https://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/jm.pth
# bm.pth: https://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/bm.pth
```
