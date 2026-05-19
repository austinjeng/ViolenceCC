"""Phase 8: SigLIP2 backbone config validation and dimension assertions.

Tests BACKBONE_CONFIGS registry in scripts/extract_clip.py for both
CLIP ViT-B/16 (backward compatibility) and SigLIP2 Giant config correctness.
No GPU required -- pure dict/config validation.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path for scripts.extract_clip import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.extract_clip import BACKBONE_CONFIGS


def test_backbone_configs_keys():
    """BACKBONE_CONFIGS has exactly the expected backbone keys."""
    assert set(BACKBONE_CONFIGS.keys()) == {"clip-vit-b-16", "siglip2-giant"}


def test_clip_config_values():
    """clip-vit-b-16 entry has correct model_name, pretrained, embed_dim, and subdirs."""
    cfg = BACKBONE_CONFIGS["clip-vit-b-16"]
    assert cfg["model_name"] == "ViT-B-16"
    assert cfg["pretrained"] == "openai"
    assert cfg["embed_dim"] == 512
    assert cfg["output_subdir"] == "clip"
    assert cfg["mean_subdir"] == "clip_mean"


def test_siglip2_config_values():
    """siglip2-giant entry has correct model_name, pretrained, embed_dim, and subdirs."""
    cfg = BACKBONE_CONFIGS["siglip2-giant"]
    assert cfg["model_name"] == "ViT-gopt-16-SigLIP2-384"
    assert cfg["pretrained"] == "webli"
    assert cfg["embed_dim"] == 1536
    assert cfg["output_subdir"] == "siglip2"
    assert cfg["mean_subdir"] == "siglip2_mean"


def test_expected_dim_mean_pool():
    """Mean-only pooling: expected_dim equals embed_dim for each backbone."""
    for backbone_key, cfg in BACKBONE_CONFIGS.items():
        embed_dim = cfg["embed_dim"]
        expected_dim = embed_dim  # mean-only: no concatenation
        if backbone_key == "clip-vit-b-16":
            assert expected_dim == 512
        elif backbone_key == "siglip2-giant":
            assert expected_dim == 1536


def test_expected_dim_meanmax_pool():
    """Mean+max pooling: expected_dim equals embed_dim * 2 for each backbone."""
    for backbone_key, cfg in BACKBONE_CONFIGS.items():
        embed_dim = cfg["embed_dim"]
        expected_dim = embed_dim * 2  # mean+max concatenation
        if backbone_key == "clip-vit-b-16":
            assert expected_dim == 1024
        elif backbone_key == "siglip2-giant":
            assert expected_dim == 3072


def test_siglip2_output_subdir():
    """SigLIP2 output subdirectories are 'siglip2' and 'siglip2_mean'."""
    cfg = BACKBONE_CONFIGS["siglip2-giant"]
    assert cfg["output_subdir"] == "siglip2"
    assert cfg["mean_subdir"] == "siglip2_mean"


def test_clip_backward_compat():
    """CLIP output subdirectories are unchanged ('clip' and 'clip_mean')."""
    cfg = BACKBONE_CONFIGS["clip-vit-b-16"]
    assert cfg["output_subdir"] == "clip"
    assert cfg["mean_subdir"] == "clip_mean"
