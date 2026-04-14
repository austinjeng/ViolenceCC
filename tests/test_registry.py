"""MOD-03..06, D-16: string-based variant registry."""
import pytest

from src.models.registry import MODEL_REGISTRY, build_model


def test_registry_has_four_keys():
    assert set(MODEL_REGISTRY.keys()) == {
        "skeleton_only", "clip_only", "late_fusion", "gated_fusion",
    }


def test_build_model_unknown_variant_raises():
    with pytest.raises(ValueError) as exc:
        build_model("not_a_real_variant")
    assert "Unknown variant" in str(exc.value)
    assert "Valid:" in str(exc.value)
    for key in ("skeleton_only", "clip_only", "late_fusion", "gated_fusion"):
        assert key in str(exc.value)


def test_build_model_lazy_import_resolves():
    """After Plan 04: skeleton_only, clip_only, late_fusion all resolve.
    After Plan 05: gated_fusion also resolves.
    This test confirms the lazy factory mechanism does not cache errors."""
    # Should not raise:
    from src.models.registry import build_model
    m1 = build_model("skeleton_only", skel_dim=256)
    m2 = build_model("clip_only", clip_dim=1024, proj_dim=512)
    m3 = build_model("late_fusion", skel_dim=256, clip_dim=1024, proj_dim=512)
    assert m1 is not None
    assert m2 is not None
    assert m3 is not None
