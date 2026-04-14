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


def test_build_model_lazy_import_not_ready():
    """Plans 04/05 have not yet landed — lazy imports should surface that clearly."""
    # PLAN-04 REMOVES THIS
    with pytest.raises(ModuleNotFoundError):
        build_model("skeleton_only", skel_dim=256)
