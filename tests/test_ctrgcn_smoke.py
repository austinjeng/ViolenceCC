"""
CTR-GCN forward pass smoke test (ENV-02).

Verifies that:
1. CTR-GCN J-stream weights load successfully
2. Synthetic COCO-17 input (N=1, M=2, T=64, V=17, C=3) produces (1, 256) output
3. Output contains no NaN or Inf values

Per D-09: Minimal forward pass only. No multi-stream or intermediate normalization checks.

API Notes (from D:/libs/pyskl/pyskl/models/gcns/ctrgcn.py):
- CTRGCN.forward() expects input shape (N, M, T, V, C) — NOT (N, C, T, V, M)
- M=2 persons required: data_bn has 102=2*17*3 channels in NTU120 HRNet checkpoint
- Returns (N, M, C_out, T_out, V_out) where C_out=256 for ntu120 config
- Must pool over M, T, V dimensions to obtain (N, 256) feature vector
"""
import torch
import numpy as np
import pytest
from mmcv import Config
from pyskl.models import build_model


@pytest.fixture
def ctrgcn_model(weight_dir, pyskl_config_dir):
    """Load CTR-GCN J-stream model with pretrained weights."""
    cfg_path = str(pyskl_config_dir / "j.py")
    weight_path = str(weight_dir / "j.pth")

    cfg = Config.fromfile(cfg_path)
    model = build_model(cfg.model)
    checkpoint = torch.load(weight_path, map_location='cpu')
    # PYSKL checkpoints are plain OrderedDicts (no 'state_dict' wrapper key)
    # Keys are prefixed with 'backbone.' and 'cls_head.'; strict=False ignores missing keys
    state_dict = checkpoint if isinstance(checkpoint, dict) and 'backbone' in str(list(checkpoint.keys())[:1]) else checkpoint.get('state_dict', checkpoint)
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    return model


@pytest.fixture
def synthetic_input():
    """
    Synthetic COCO-17 tensor: N=1, M=2, T=64, V=17, C=3.

    Shape order: (N, M, T, V, C) as required by CTRGCN.forward().
    M=2 persons: required by the NTU120 HRNet checkpoint (data_bn has 102=2*17*3 channels).
    The second person can be all zeros (padded absent person, as in FormatGCNInput).
    C=3 channels: x coordinate, y coordinate, confidence score.
    Values for person 0 scaled to simulate post-PreNormalize2D coordinates in [-1, 1].
    """
    torch.manual_seed(42)
    x = torch.zeros(1, 2, 64, 17, 3)
    x[:, 0, :, :, :] = torch.randn(1, 64, 17, 3) * 0.5  # person 0: random keypoints
    # person 1 stays all-zero (absent person pad)
    return x


def _extract_backbone_features(model, x):
    """
    Run backbone forward pass and pool to (N, 256).

    CTRGCN.forward(x) returns (N, M, C, T, V).
    Global average pool over M, T, V to produce (N, C) = (N, 256).
    """
    with torch.no_grad():
        output = model.backbone(x)
        # output shape: (N, M, C, T, V)
        assert output.dim() == 5, f"Expected 5D output from backbone, got {output.dim()}D: {output.shape}"
        # Global average pool over M, T, V (dims 1, 3, 4) -> (N, C)
        output = output.mean(dim=[1, 3, 4])
    return output


def test_ctrgcn_forward_pass_shape(ctrgcn_model, synthetic_input):
    """CTR-GCN backbone produces (1, 256) output from COCO-17 input."""
    output = _extract_backbone_features(ctrgcn_model, synthetic_input)
    assert output.shape == (1, 256), f"Expected (1, 256), got {output.shape}"


def test_ctrgcn_output_no_nan(ctrgcn_model, synthetic_input):
    """CTR-GCN output contains no NaN values."""
    output = _extract_backbone_features(ctrgcn_model, synthetic_input)
    assert not torch.any(torch.isnan(output)), "NaN detected in CTR-GCN output"


def test_ctrgcn_output_no_inf(ctrgcn_model, synthetic_input):
    """CTR-GCN output contains no Inf values."""
    output = _extract_backbone_features(ctrgcn_model, synthetic_input)
    assert not torch.any(torch.isinf(output)), "Inf detected in CTR-GCN output"


def test_ctrgcn_output_nonzero_variance(ctrgcn_model, synthetic_input):
    """CTR-GCN output has nonzero variance (not collapsed to constant)."""
    output = _extract_backbone_features(ctrgcn_model, synthetic_input)
    variance = output.var().item()
    assert variance > 1e-10, f"Output variance too low ({variance}), may indicate collapsed features"
