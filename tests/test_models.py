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


def test_clip_dim_1536():
    """Phase 8: CLIPProj with SigLIP2 1536-d input."""
    torch.manual_seed(0)
    model = CLIPProj(clip_dim=1536)
    clip = torch.randn(2, 32, 1536)
    out = model(clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_clip_dim_1536_projection_layer():
    """Phase 8: CLIPProj(clip_dim=1536) projection maps 1536->512."""
    model = CLIPProj(clip_dim=1536)
    assert isinstance(model.clip_proj, nn.Linear)
    assert model.clip_proj.in_features == 1536
    assert model.clip_proj.out_features == 512


def test_clip_dim_2304():
    """Phase 9: CLIPProj with SO400M 2304-d input."""
    torch.manual_seed(0)
    model = CLIPProj(clip_dim=2304)
    clip = torch.randn(2, 32, 2304)
    out = model(clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_clip_dim_2304_projection_layer():
    """Phase 9: CLIPProj(clip_dim=2304) projection maps 2304->512."""
    model = CLIPProj(clip_dim=2304)
    assert isinstance(model.clip_proj, nn.Linear)
    assert model.clip_proj.in_features == 2304
    assert model.clip_proj.out_features == 512


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


def test_late_fusion_clip_dim_1536():
    """Phase 8: LateFusion with SigLIP2 1536-d clip input."""
    torch.manual_seed(0)
    model = LateFusion(skel_dim=256, clip_dim=1536, proj_dim=512, alpha="equal")
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 1536)
    out = model(skel=skel, clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_late_fusion_clip_dim_2304():
    """Phase 9: LateFusion with SO400M 2304-d clip input."""
    torch.manual_seed(0)
    model = LateFusion(skel_dim=256, clip_dim=2304, proj_dim=512, alpha="equal")
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 2304)
    out = model(skel=skel, clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


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


# ---- MOD-06 / MOD-07 Gated Fusion ----

from src.models.gated_fusion import GatedFusion


def test_gated_fusion_shapes():
    """MOD-06 (VALIDATION.md): [B,T,256]+[B,T,1024] -> [B,T]; gate sigmoid in [0,1]."""
    torch.manual_seed(0)
    model = GatedFusion(skel_dim=256, clip_dim=1024, shared_dim=256)
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 1024)
    out = model(skel=skel, clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_gated_fusion_clip_dim_1536():
    """Phase 8: GatedFusion with SigLIP2 1536-d clip input."""
    torch.manual_seed(0)
    model = GatedFusion(skel_dim=256, clip_dim=1536, shared_dim=256)
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 1536)
    out = model(skel=skel, clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_gated_fusion_clip_dim_2304():
    """Phase 9: GatedFusion with SO400M 2304-d clip input."""
    torch.manual_seed(0)
    model = GatedFusion(skel_dim=256, clip_dim=2304, shared_dim=256)
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 2304)
    out = model(skel=skel, clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_gated_fusion_real_features(tmp_feature_dir):
    """MOD-06 (VALIDATION.md): forward on real UCF features produces finite, [0,1] scores.

    Uses a single real UCF feature file if E:/features/ucf/ is mounted; otherwise
    skips (marked requires_features so the CI-mode run does not need E:/).
    """
    import numpy as np
    from pathlib import Path
    ucf_root = Path("E:/features/ucf")
    if not (ucf_root / "skeleton").exists() or not (ucf_root / "clip").exists():
        pytest.skip("E:/features/ucf not mounted")
    # Pick the first skeleton feature file that has N >= 32 for a real-shape test
    skel_files = sorted((ucf_root / "skeleton").glob("*.npy"))
    skel = clip = None
    for sf in skel_files:
        arr = np.load(sf, mmap_mode="r")
        if arr.shape[0] >= 32:
            cf = ucf_root / "clip" / sf.name
            if cf.exists():
                skel = np.load(sf)
                clip = np.load(cf)
                break
    if skel is None or clip is None:
        pytest.skip("no UCF video with N>=32 found in cache")
    # Pad to N==32 (take first 32 snippets)
    skel = torch.from_numpy(skel[:32].astype(np.float32)).unsqueeze(0)
    clip = torch.from_numpy(clip[:32].astype(np.float32)).unsqueeze(0)
    torch.manual_seed(0)
    model = GatedFusion()
    out = model(skel=skel, clip=clip)
    assert out.shape == (1, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_gated_fusion_layernorms():
    """MOD-07 (VALIDATION.md): >= 3 named nn.LayerNorm in GatedFusion per D-07.

    Expected names: ln_skel, ln_clip, ln_fused (PRD 9.2 + CONTEXT.md D-07).
    """
    model = GatedFusion()
    ln_entries = [
        (n, m) for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)
    ]
    ln_names = [n for n, _ in ln_entries]
    assert len(ln_entries) >= 3, f"need >= 3 LN, got {ln_names}"
    assert "ln_skel" in ln_names
    assert "ln_clip" in ln_names
    assert "ln_fused" in ln_names


def test_gated_fusion_layernorm_attribute_access():
    """MOD-07: LN layers accessible as model.ln_<name> for Phase 5 TTA."""
    model = GatedFusion()
    assert hasattr(model, "ln_skel") and isinstance(model.ln_skel, nn.LayerNorm)
    assert hasattr(model, "ln_clip") and isinstance(model.ln_clip, nn.LayerNorm)
    assert hasattr(model, "ln_fused") and isinstance(model.ln_fused, nn.LayerNorm)
    # Each LN normalizes over shared_dim (default 256)
    assert model.ln_skel.normalized_shape == (256,)
    assert model.ln_clip.normalized_shape == (256,)
    assert model.ln_fused.normalized_shape == (256,)


def test_gated_fusion_gate_not_saturated_at_init():
    """m1 mitigation: Xavier gain=0.1 -> initial mean(gate) ~= 0.5.

    Stress the expectation by using 10 random input batches and averaging.
    """
    torch.manual_seed(123)
    model = GatedFusion()
    gate_means = []
    for _ in range(10):
        skel = torch.randn(4, 32, 256)
        clip = torch.randn(4, 32, 1024)
        p_skel = model.ln_skel(model.skel_proj(skel))
        p_clip = model.ln_clip(model.clip_proj(clip))
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        gate_means.append(g.mean().item())
    overall = sum(gate_means) / len(gate_means)
    assert 0.4 < overall < 0.6, (
        f"Gate saturated at init: mean(gate)={overall:.3f} "
        "(m1 mitigation expects ~0.5 due to Xavier gain=0.1)"
    )


def test_gated_fusion_gate_xavier_gain_small():
    """Regression guard: gate weight norm is small due to gain=0.1."""
    model = GatedFusion()
    # Xavier uniform with gain=0.1 produces weights in a much smaller range
    # than the default gain=1.0. The weight std should be < 0.1.
    assert model.gate.weight.std().item() < 0.1, (
        f"gate weight std={model.gate.weight.std().item():.4f} "
        "suggests Xavier gain is too large (m1 mitigation regressed)"
    )
    # Bias should be exactly zero at init
    assert torch.all(model.gate.bias == 0.0)


def test_gated_fusion_residual_is_sum_of_both_projections():
    """Structural: residual = fused + p_skel + p_clip (gradient highway)."""
    torch.manual_seed(0)
    model = GatedFusion()
    model.eval()
    skel = torch.randn(1, 4, 256)
    clip = torch.randn(1, 4, 1024)

    # Compute expected residual path by hand
    with torch.no_grad():
        p_skel = model.ln_skel(model.skel_proj(skel))
        p_clip = model.ln_clip(model.clip_proj(clip))
        g = torch.sigmoid(model.gate(torch.cat([p_skel, p_clip], dim=-1)))
        fused = g * p_skel + (1 - g) * p_clip
        residual_manual = fused + p_skel + p_clip
        out_manual = model.head(model.ln_fused(residual_manual)).squeeze(-1)

    out_model = model(skel=skel, clip=clip)
    # Dropout is inactive in eval mode, so manual and model paths match exactly
    assert torch.allclose(out_model, out_manual, atol=1e-6)


def test_gated_fusion_raises_without_both_inputs():
    model = GatedFusion()
    with pytest.raises(ValueError, match="requires both"):
        model(skel=torch.randn(1, 4, 256))
    with pytest.raises(ValueError, match="requires both"):
        model(clip=torch.randn(1, 4, 1024))


def test_build_model_gated_fusion_round_trip():
    """MODEL_REGISTRY now resolves all 4 variants."""
    from src.models.registry import build_model
    model = build_model("gated_fusion",
                        skel_dim=256, clip_dim=1024, shared_dim=256)
    assert isinstance(model, GatedFusion)
