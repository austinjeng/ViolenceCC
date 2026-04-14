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


# ---- MOD-05 LateFusion ----

from src.models.late_fusion import LateFusion


def test_late_fusion_equal():
    """D-discretion default alpha='equal' -> output = 0.5 * s_skel + 0.5 * s_clip."""
    torch.manual_seed(0)
    model = LateFusion(alpha="equal")
    model.eval()  # disable dropout for exact math check
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 1024)
    with torch.no_grad():
        fused = model(skel=skel, clip=clip)
        s_skel = model.skeleton(skel=skel)
        s_clip = model.clip(clip=clip)
    assert fused.shape == (2, 32)
    # Equal-weighted: exact algebraic identity
    assert torch.allclose(fused, 0.5 * s_skel + 0.5 * s_clip, atol=1e-6)


def test_late_fusion_learned_alpha_init_is_0_5():
    """Learned alpha initialized to sigmoid(0) = 0.5 -> behaves like equal at step 0."""
    torch.manual_seed(0)
    model = LateFusion(alpha="learned")
    model.eval()
    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    with torch.no_grad():
        fused = model(skel=skel, clip=clip)
        s_skel = model.skeleton(skel=skel)
        s_clip = model.clip(clip=clip)
    assert torch.allclose(fused, 0.5 * s_skel + 0.5 * s_clip, atol=1e-6)
    assert model.alpha_logit is not None
    assert model.alpha_logit.item() == 0.0  # sigmoid(0)=0.5


def test_late_fusion_alpha_logit_is_trainable_when_learned():
    model = LateFusion(alpha="learned")
    trainable = [n for n, p in model.named_parameters() if p.requires_grad]
    assert "alpha_logit" in trainable


def test_late_fusion_alpha_none_when_equal():
    model = LateFusion(alpha="equal")
    assert model.alpha_logit is None


def test_late_fusion_exposes_nested_layernorms():
    """MOD-07 nested discovery: LateFusion's child LNs still discoverable."""
    model = LateFusion(alpha="equal")
    ln_names = [n for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)]
    assert any(name.endswith("ln_skel") for name in ln_names), ln_names
    assert any(name.endswith("ln_clip") for name in ln_names), ln_names


def test_late_fusion_invalid_alpha_raises():
    with pytest.raises(ValueError, match="alpha must be"):
        LateFusion(alpha="garbage")


# ---- MODEL_REGISTRY round-trip ----

from src.models.registry import build_model


def test_build_model_skeleton_only_round_trip():
    model = build_model("skeleton_only", skel_dim=256)
    from src.models.skeleton_only import SkeletonProj
    assert isinstance(model, SkeletonProj)


def test_build_model_clip_only_round_trip():
    model = build_model("clip_only", clip_dim=1024, proj_dim=512)
    from src.models.clip_only import CLIPProj
    assert isinstance(model, CLIPProj)


def test_build_model_late_fusion_round_trip():
    model = build_model(
        "late_fusion",
        skel_dim=256, clip_dim=1024, proj_dim=512, alpha="equal",
    )
    assert isinstance(model, LateFusion)
