"""
corruption.py -- UCF-Crime-C corruption transform module.

Uses ONLY numpy + cv2 (D-03 correction from RESEARCH.md).
PIL and scipy are absent from vcc-skeleton, so this module avoids them
to ensure bit-identical transforms across both vcc-main and vcc-skeleton
environments.

4 corruption types x 5 severity levels = 20 conditions.
Severity parameters match ImageNet-C verified values exactly
(source: https://github.com/hendrycks/robustness).

Corruption function signature (all 4 match):
    def corruption_fn(img: np.ndarray, severity: int,
                      rng: np.random.Generator) -> np.ndarray:
        '''img: uint8 [H,W,3] RGB. severity: 1-5. Returns uint8 [H,W,3] RGB.'''
"""

import numpy as np
import cv2

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

CORRUPTION_TYPES = ("gaussian_noise", "jpeg_compression", "brightness", "motion_blur")

# M7 (PITFALLS.md): these corruption types alter spatial structure enough to
# require skeleton re-extraction. gaussian_noise and brightness are robust --
# RTMPose produces effectively identical keypoints on those corruptions.
SKELETON_REEXTRACT_TYPES = ("motion_blur", "jpeg_compression")

# ---------------------------------------------------------------------------
# Severity parameter arrays (exact ImageNet-C verified values)
# Source: https://github.com/hendrycks/robustness/.../corruptions.py
# All are monotonically increasing degradation (severity 1 = mildest, 5 = harshest)
# ---------------------------------------------------------------------------

GAUSSIAN_NOISE_SIGMA = [0.08, 0.12, 0.18, 0.26, 0.38]
JPEG_QUALITY = [25, 18, 15, 10, 7]  # lower = worse quality (more artifacts)
BRIGHTNESS_FACTOR = [0.1, 0.2, 0.3, 0.4, 0.5]  # added to normalized [0,1] image
MOTION_BLUR_PARAMS = [(10, 3), (15, 5), (15, 8), (15, 12), (20, 15)]  # (kernel_size, sigma)


# ---------------------------------------------------------------------------
# 4 corruption functions
# ---------------------------------------------------------------------------

def gaussian_noise(img: np.ndarray, severity: int,
                   rng: np.random.Generator) -> np.ndarray:
    """Add Gaussian noise to an RGB image.

    Parameters
    ----------
    img : np.ndarray
        uint8 [H, W, 3] RGB image.
    severity : int
        Severity level 1-5.
    rng : np.random.Generator
        Numpy random generator for reproducibility.

    Returns
    -------
    np.ndarray
        uint8 [H, W, 3] corrupted RGB image.
    """
    sigma = GAUSSIAN_NOISE_SIGMA[severity - 1]
    noise = rng.normal(0, sigma, img.shape).astype(np.float32)
    out = img.astype(np.float32) / 255.0 + noise
    return np.clip(out * 255, 0, 255).astype(np.uint8)


def jpeg_compression(img: np.ndarray, severity: int,
                     rng: np.random.Generator = None) -> np.ndarray:
    """Apply JPEG compression artifacts via encode/decode cycle.

    Uses cv2.imencode/imdecode (works in both vcc-main and vcc-skeleton).
    ``rng`` is unused but present for uniform signature.

    Parameters
    ----------
    img : np.ndarray
        uint8 [H, W, 3] RGB image.
    severity : int
        Severity level 1-5.
    rng : np.random.Generator, optional
        Unused (deterministic transform).

    Returns
    -------
    np.ndarray
        uint8 [H, W, 3] corrupted RGB image.
    """
    quality = JPEG_QUALITY[severity - 1]
    # cv2 operates in BGR; convert RGB -> BGR before encode, BGR -> RGB after decode
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    decoded = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)


def brightness(img: np.ndarray, severity: int,
               rng: np.random.Generator = None) -> np.ndarray:
    """Increase brightness by adding a constant to the normalized image.

    Uses ImageNet-C convention (add only, not subtract) for comparability.
    ``rng`` is unused but present for uniform signature.

    Parameters
    ----------
    img : np.ndarray
        uint8 [H, W, 3] RGB image.
    severity : int
        Severity level 1-5.
    rng : np.random.Generator, optional
        Unused (deterministic transform).

    Returns
    -------
    np.ndarray
        uint8 [H, W, 3] corrupted RGB image.
    """
    factor = BRIGHTNESS_FACTOR[severity - 1]
    out = img.astype(np.float32) / 255.0 + factor
    return np.clip(out * 255, 0, 255).astype(np.uint8)


def motion_blur(img: np.ndarray, severity: int,
                rng: np.random.Generator = None) -> np.ndarray:
    """Apply horizontal motion blur using a line kernel.

    Simplified horizontal kernel per Assumption A1 (RESEARCH.md). The second
    element of MOTION_BLUR_PARAMS (sigma) is unused; the kernel is a uniform
    horizontal line of length ``kernel_size``.

    ``rng`` is unused but present for uniform signature.

    Parameters
    ----------
    img : np.ndarray
        uint8 [H, W, 3] RGB image.
    severity : int
        Severity level 1-5.
    rng : np.random.Generator, optional
        Unused (deterministic transform).

    Returns
    -------
    np.ndarray
        uint8 [H, W, 3] corrupted RGB image.
    """
    size, _ = MOTION_BLUR_PARAMS[severity - 1]
    kernel = np.zeros((size, size), dtype=np.float32)
    kernel[size // 2, :] = 1.0 / size  # horizontal line kernel
    return cv2.filter2D(img, -1, kernel)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_DISPATCH = {
    "gaussian_noise": gaussian_noise,
    "jpeg_compression": jpeg_compression,
    "brightness": brightness,
    "motion_blur": motion_blur,
}


def apply_corruption(img: np.ndarray, corruption_type: str, severity: int,
                     rng: np.random.Generator = None) -> np.ndarray:
    """Apply a named corruption transform to an RGB image.

    Parameters
    ----------
    img : np.ndarray
        uint8 [H, W, 3] RGB image.
    corruption_type : str
        One of ``CORRUPTION_TYPES``.
    severity : int
        Severity level 1-5.
    rng : np.random.Generator, optional
        Numpy random generator. If ``None``, creates a deterministic default
        ``np.random.default_rng(42)`` for reproducibility (per CONTEXT.md).

    Returns
    -------
    np.ndarray
        uint8 [H, W, 3] corrupted RGB image.

    Raises
    ------
    ValueError
        If ``corruption_type`` is not in ``CORRUPTION_TYPES``, ``severity``
        is not in [1, 5], ``img`` is not uint8, or ``img`` is not 3-D.
    """
    if corruption_type not in CORRUPTION_TYPES:
        raise ValueError(
            f"Unknown corruption_type '{corruption_type}'. "
            f"Must be one of {CORRUPTION_TYPES}"
        )
    if not (1 <= severity <= 5):
        raise ValueError(
            f"severity must be 1-5, got {severity}"
        )
    if img.dtype != np.uint8:
        raise ValueError(
            f"img.dtype must be uint8, got {img.dtype}"
        )
    if img.ndim != 3:
        raise ValueError(
            f"img must be 3-D [H, W, C], got {img.ndim}-D"
        )

    if rng is None:
        rng = np.random.default_rng(42)

    return _DISPATCH[corruption_type](img, severity, rng)
