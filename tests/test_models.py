"""MOD-03..06 + MOD-07 variant wrappers and LayerNorm discoverability."""
from __future__ import annotations
import torch
import torch.nn as nn
import pytest

from src.models.skeleton_only import SkeletonProj
from src.models.clip_only import CLIPProj


# ---- MOD-03 SkeletonProj ----

def test_skeleton_only_forward():
    torch.manual_seed(0)
    model = SkeletonProj()
    skel = torch.randn(2, 32, 256)
    out = model(skel=skel)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_skeleton_only_has_named_layernorm():
    model = SkeletonProj()
    ln_names = [n for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)]
    assert "ln_skel" in ln_names
    assert hasattr(model, "ln_skel")
    assert isinstance(model.ln_skel, nn.LayerNorm)
    assert model.ln_skel.normalized_shape == (256,)


def test_skeleton_only_raises_without_skel():
    model = SkeletonProj()
    with pytest.raises(ValueError, match="SkeletonProj requires"):
        model(clip=torch.randn(2, 32, 1024))


# ---- MOD-04 CLIPProj ----

def test_clip_only_forward():
    torch.manual_seed(0)
    model = CLIPProj()
    clip = torch.randn(2, 32, 1024)
    out = model(clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_clip_only_has_named_layernorm():
    model = CLIPProj()
    assert hasattr(model, "ln_clip")
    assert isinstance(model.ln_clip, nn.LayerNorm)
    # D-06 learned projection: 1024 -> 512; LN is after the projection
    assert model.ln_clip.normalized_shape == (512,)


def test_clip_only_projection_layer_d06():
    """D-06/Phase 2 D-06: learned Linear(1024->512) lives inside CLIPProj."""
    model = CLIPProj()
    assert isinstance(model.clip_proj, nn.Linear)
    assert model.clip_proj.in_features == 1024
    assert model.clip_proj.out_features == 512


def test_clip_only_raises_without_clip():
    model = CLIPProj()
    with pytest.raises(ValueError, match="CLIPProj requires"):
        model(skel=torch.randn(2, 32, 256))


# ---- MOD-07 LayerNorm discoverability (variant-wide) ----

def test_layernorm_attribute_access():
    """D-07: all variants expose their LN layers as named attributes for TTA."""
    sk = SkeletonProj()
    cl = CLIPProj()
    assert hasattr(sk, "ln_skel")
    assert hasattr(cl, "ln_clip")
