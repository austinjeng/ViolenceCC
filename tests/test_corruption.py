"""
test_corruption.py -- Unit tests for scripts/corruption.py.

Covers TTA-01 (4 types x 5 severities) and TTA-03 (skeleton re-extraction decision).
9 test functions covering: all 20 conditions, monotonicity, reproducibility,
M7 skeleton re-extraction, input validation, and D-03 PIL-free confirmation.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# corruption.py lives in scripts/, not src/; add to sys.path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from corruption import (
    CORRUPTION_TYPES,
    GAUSSIAN_NOISE_SIGMA,
    JPEG_QUALITY,
    BRIGHTNESS_FACTOR,
    MOTION_BLUR_PARAMS,
    SKELETON_REEXTRACT_TYPES,
    apply_corruption,
    gaussian_noise,
    jpeg_compression,
    brightness,
    motion_blur,
)


@pytest.fixture
def test_image():
    """Deterministic 64x64 RGB uint8 test image."""
    return np.random.default_rng(0).integers(0, 255, (64, 64, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Test 1: All 20 conditions produce uint8 with correct shape
# ---------------------------------------------------------------------------


def test_all_20_conditions_produce_uint8(test_image):
    """Loop 4 types x 5 severities. Each returns uint8 ndarray with same shape."""
    for ctype in CORRUPTION_TYPES:
        for sev in range(1, 6):
            result = apply_corruption(test_image, ctype, sev)
            assert result.dtype == np.uint8, (
                f"{ctype} sev={sev}: expected uint8, got {result.dtype}"
            )
            assert result.shape == test_image.shape, (
                f"{ctype} sev={sev}: shape mismatch {result.shape} != {test_image.shape}"
            )


# ---------------------------------------------------------------------------
# Test 2: Gaussian noise severity is monotonically increasing MSE
# ---------------------------------------------------------------------------


def test_gaussian_noise_severity_monotonic(test_image):
    """Higher severity produces larger MSE from original."""
    mses = []
    for sev in range(1, 6):
        rng = np.random.default_rng(42)
        corrupted = gaussian_noise(test_image, sev, rng)
        mse = np.mean((test_image.astype(float) - corrupted.astype(float)) ** 2)
        mses.append(mse)
    for i in range(len(mses) - 1):
        assert mses[i] < mses[i + 1], (
            f"Gaussian noise MSE not monotonic: sev {i+1} MSE={mses[i]:.4f} "
            f">= sev {i+2} MSE={mses[i+1]:.4f}"
        )


# ---------------------------------------------------------------------------
# Test 3: JPEG compression severity is monotonically increasing distortion
# ---------------------------------------------------------------------------


def test_jpeg_compression_severity_monotonic(test_image):
    """Lower quality (higher severity) produces larger MSE."""
    mses = []
    for sev in range(1, 6):
        corrupted = jpeg_compression(test_image, sev)
        mse = np.mean((test_image.astype(float) - corrupted.astype(float)) ** 2)
        mses.append(mse)
    for i in range(len(mses) - 1):
        assert mses[i] < mses[i + 1], (
            f"JPEG MSE not monotonic: sev {i+1} MSE={mses[i]:.4f} "
            f">= sev {i+2} MSE={mses[i+1]:.4f}"
        )


# ---------------------------------------------------------------------------
# Test 4: Brightness severity is monotonically increasing mean
# ---------------------------------------------------------------------------


def test_brightness_severity_monotonic(test_image):
    """Higher severity produces brighter image (higher mean pixel value)."""
    means = []
    for sev in range(1, 6):
        corrupted = brightness(test_image, sev)
        means.append(np.mean(corrupted.astype(float)))
    for i in range(len(means) - 1):
        assert means[i] < means[i + 1], (
            f"Brightness mean not monotonic: sev {i+1} mean={means[i]:.2f} "
            f">= sev {i+2} mean={means[i+1]:.2f}"
        )


# ---------------------------------------------------------------------------
# Test 5: Motion blur severity is monotonically increasing distortion
# ---------------------------------------------------------------------------


def test_motion_blur_severity_monotonic(test_image):
    """Higher severity produces more blur (larger MSE from original)."""
    mses = []
    for sev in range(1, 6):
        corrupted = motion_blur(test_image, sev)
        mse = np.mean((test_image.astype(float) - corrupted.astype(float)) ** 2)
        mses.append(mse)
    for i in range(len(mses) - 1):
        assert mses[i] < mses[i + 1], (
            f"Motion blur MSE not monotonic: sev {i+1} MSE={mses[i]:.4f} "
            f">= sev {i+2} MSE={mses[i+1]:.4f}"
        )


# ---------------------------------------------------------------------------
# Test 6: Gaussian noise reproducible with same RNG seed
# ---------------------------------------------------------------------------


def test_gaussian_noise_reproducible_with_rng(test_image):
    """Same seed produces identical output; different seeds produce different output."""
    rng1 = np.random.default_rng(42)
    out1 = gaussian_noise(test_image, 3, rng1)

    rng2 = np.random.default_rng(42)
    out2 = gaussian_noise(test_image, 3, rng2)

    np.testing.assert_array_equal(out1, out2, err_msg="Same seed should produce identical output")

    rng3 = np.random.default_rng(99)
    out3 = gaussian_noise(test_image, 3, rng3)
    assert not np.array_equal(out1, out3), "Different seeds should produce different output"


# ---------------------------------------------------------------------------
# Test 7: SKELETON_REEXTRACT_TYPES matches M7 specification
# ---------------------------------------------------------------------------


def test_skeleton_reextract_types():
    """Assert M7: motion_blur and jpeg_compression require skeleton re-extraction.
    gaussian_noise and brightness do NOT (RTMPose is robust to these)."""
    assert SKELETON_REEXTRACT_TYPES == ("motion_blur", "jpeg_compression")
    assert "gaussian_noise" not in SKELETON_REEXTRACT_TYPES
    assert "brightness" not in SKELETON_REEXTRACT_TYPES


# ---------------------------------------------------------------------------
# Test 8: apply_corruption validates inputs
# ---------------------------------------------------------------------------


def test_apply_corruption_validates_inputs(test_image):
    """Invalid inputs raise ValueError."""
    # Unknown corruption type
    with pytest.raises(ValueError, match="Unknown corruption_type"):
        apply_corruption(test_image, "unknown_type", 3)

    # Severity out of range
    with pytest.raises(ValueError, match="severity must be 1-5"):
        apply_corruption(test_image, "gaussian_noise", 0)
    with pytest.raises(ValueError, match="severity must be 1-5"):
        apply_corruption(test_image, "gaussian_noise", 6)

    # Non-uint8 input
    float_img = test_image.astype(np.float32)
    with pytest.raises(ValueError, match="uint8"):
        apply_corruption(float_img, "gaussian_noise", 3)

    # 2-D input (missing channel dim)
    img_2d = test_image[:, :, 0]
    with pytest.raises(ValueError, match="3-D"):
        apply_corruption(img_2d, "gaussian_noise", 3)


# ---------------------------------------------------------------------------
# Test 9: JPEG uses cv2, not PIL (D-03 confirmation)
# ---------------------------------------------------------------------------


def test_jpeg_uses_cv2_not_pil(test_image):
    """Confirm D-03 correction: importing and calling jpeg_compression does
    NOT pull PIL into sys.modules."""
    # Remove PIL from sys.modules if it was loaded by other tests
    pil_keys = [k for k in sys.modules if k == "PIL" or k.startswith("PIL.")]
    saved = {k: sys.modules.pop(k) for k in pil_keys}

    try:
        # Re-import corruption module to verify no PIL dependency
        import importlib
        import corruption
        importlib.reload(corruption)

        # Call jpeg_compression
        corruption.jpeg_compression(test_image, 3)

        # Check PIL was NOT loaded
        assert "PIL" not in sys.modules, (
            "PIL was loaded by corruption.jpeg_compression -- violates D-03"
        )
        assert not any(k.startswith("PIL.") for k in sys.modules), (
            "PIL submodule was loaded by corruption module -- violates D-03"
        )
    finally:
        # Restore PIL modules to avoid affecting other tests
        sys.modules.update(saved)
