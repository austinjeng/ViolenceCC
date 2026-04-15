"""RTFMI3D variant tests (Phase 4 Plan 03 Task 1, D-18).

Covers behaviors R1-R7 from the plan:
  R1  registry dispatch: build_model(variant="rtfm_i3d") returns an RTFMI3D instance.
  R2  forward shape: [B, T, 1024] -> [B, T], finite.
  R3  no NaN on random input.
  R4  named LN (self.ln_i3d) is nn.LayerNorm(1024).
  R5  missing i3d input raises ValueError.
  R6  variant-uniform signature: accepts skel/clip/mask kwargs without error when i3d given.
  R7  LN affine iterable contains "ln_i3d" (Phase 5 TTA prep, mirrors MOD-07 test_models.py).
"""
import sys

import pytest
import torch
import torch.nn as nn

from src.models.rtfm_i3d import RTFMI3D
from src.models.registry import MODEL_REGISTRY, build_model


# ---- R1 registry dispatch ----


def test_registry_dispatch():
    """R1: MODEL_REGISTRY['rtfm_i3d'] -> RTFMI3D via build_model()."""
    assert "rtfm_i3d" in MODEL_REGISTRY
    model = build_model(variant="rtfm_i3d")
    assert isinstance(model, RTFMI3D)


# ---- R2 + R3 forward shape + finite ----


def test_forward_shape():
    """R2 + R3: [2, 32, 1024] -> [2, 32], all finite."""
    torch.manual_seed(0)
    model = RTFMI3D()
    i3d = torch.randn(2, 32, 1024)
    out = model(i3d=i3d)
    assert out.shape == (2, 32), f"got {tuple(out.shape)}"
    assert torch.isfinite(out).all()


def test_forward_finite_small_batch():
    """R3 spot: forward on single-sample input is finite."""
    torch.manual_seed(1)
    model = RTFMI3D()
    out = model(i3d=torch.randn(1, 32, 1024))
    assert torch.isfinite(out).all()


# ---- R4 + R7 named LN discoverability (Phase 5 TTA contract) ----


def test_named_ln_present():
    """R4 + R7: ln_i3d is an nn.LayerNorm(1024,) discoverable via named_modules."""
    model = RTFMI3D()
    names = [n for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)]
    assert "ln_i3d" in names, names
    ln = dict(model.named_modules())["ln_i3d"]
    assert isinstance(ln, nn.LayerNorm)
    assert ln.normalized_shape == (1024,)


def test_ln_attribute_access():
    """R4: ln_i3d accessible as model.ln_i3d (parallel to SkeletonProj.ln_skel)."""
    model = RTFMI3D()
    assert hasattr(model, "ln_i3d")
    assert isinstance(model.ln_i3d, nn.LayerNorm)
    assert model.ln_i3d.normalized_shape == (1024,)


# ---- R5 missing input raises ----


def test_missing_i3d_raises():
    """R5: calling model without `i3d=...` kwarg raises ValueError."""
    model = RTFMI3D()
    with pytest.raises(ValueError, match="i3d"):
        model(skel=torch.randn(1, 32, 256))


# ---- R6 variant-uniform forward signature ----


def test_ignores_other_kwargs():
    """R6: forward accepts and ignores skel/clip/mask kwargs when i3d is provided."""
    torch.manual_seed(2)
    model = RTFMI3D()
    i3d = torch.randn(1, 32, 1024)
    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    mask = torch.ones(1, 32)
    out = model(i3d=i3d, skel=skel, clip=clip, mask=mask)
    assert out.shape == (1, 32)
    assert torch.isfinite(out).all()


# ---- Factory lazy-import hygiene ----


def test_lazy_factory_no_side_effects():
    """The registry factory should import only src.models.rtfm_i3d, not pull
    unrelated modules (e.g. i3d_dataset) at MODEL_REGISTRY dispatch time."""
    before = set(sys.modules)
    _ = MODEL_REGISTRY["rtfm_i3d"]()
    after = set(sys.modules)
    new = after - before
    # It's fine for src.models.rtfm_i3d and mil_head to appear; it is NOT fine
    # for i3d_dataset (data path) to be transitively imported by the model factory.
    assert not any("i3d_dataset" in m for m in new), new
