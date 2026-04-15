"""C4 regression unit tests for src.eval.snippet_to_frame (Plan 04-01 Task 2).

Covers behaviors A1..A7 from the plan:

  A1: single-repeat I3D path — shape + first-16-values == scores[0]
  A2: compound-repeat UCF path — 5 * 64 * 10 == 3200
  A3: exact multiple — shape + all-equal
  A4: tail-pad when expanded < n_frames — last values == scores[-1]
  A5: truncation when expanded > n_frames — shape + content
  A6: tolerance violation raises AssertionError (C4 guard)
  A7: non-1D scores raises ValueError
"""
from __future__ import annotations

import numpy as np
import pytest

from src.eval.snippet_to_frame import snippet_to_frame


# ---------------------------------------------------------------------------
# A1: XD I3D path (single np.repeat, upsample_factor=1)
# ---------------------------------------------------------------------------


def test_single_repeat_i3d():
    """A1: XD I3D path — N=10 × window=16, upsample=1 → 160 frames."""
    scores = np.linspace(0.1, 0.5, 10).astype(np.float32)
    frames = snippet_to_frame(scores, n_frames=160, snippet_window=16)
    assert frames.shape == (160,)
    # First 16 frames == scores[0]
    assert np.allclose(frames[:16], scores[0])
    # Last 16 frames == scores[-1]
    assert np.allclose(frames[-16:], scores[-1])


def test_single_repeat_i3d_first_block_equals_first_score():
    """A1 explicit: first 16 values == 0.1 (the explicit A1 spec in plan)."""
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=80, snippet_window=16)
    assert frames.shape == (80,)
    assert np.allclose(frames[:16], 0.1)
    assert np.allclose(frames[16:32], 0.2)


# ---------------------------------------------------------------------------
# A2: UCF compound-repeat path
# ---------------------------------------------------------------------------


def test_compound_repeat_ucf():
    """A2: UCF path — N=5 × 64 PNG-window × 10 upsample → 3200 frames."""
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
    frames = snippet_to_frame(
        scores, n_frames=3200, snippet_window=64, upsample_factor=10
    )
    assert frames.shape == (3200,)
    # First 640 frames (= 64 * 10) all == 0.1
    assert np.allclose(frames[:640], 0.1)
    # Last 640 frames all == 0.5
    assert np.allclose(frames[-640:], 0.5)


# ---------------------------------------------------------------------------
# A3: exact multiple
# ---------------------------------------------------------------------------


def test_exact_multiple():
    """A3: scores=[0.5], n_frames=16, window=16 → shape (16,), all 0.5."""
    scores = np.array([0.5], dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=16, snippet_window=16)
    assert frames.shape == (16,)
    assert np.allclose(frames, 0.5)


# ---------------------------------------------------------------------------
# A4: tail-pad short
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n_frames,expected_last_n", [(20, 4), (30, 14)])
def test_tail_pad_short(n_frames, expected_last_n):
    """A4: expanded < n_frames → tail-repeat last score."""
    scores = np.array([0.5], dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=n_frames, snippet_window=16)
    assert frames.shape == (n_frames,)
    # Last (n_frames - 16) values are the pad — all 0.5 (the last score)
    assert np.allclose(frames[-expected_last_n:], 0.5)


# ---------------------------------------------------------------------------
# A5: truncation
# ---------------------------------------------------------------------------


def test_truncation_long():
    """A5: scores=[0, 1], n_frames=20, window=16 → first 20 of [0]*16 + [1]*16."""
    scores = np.array([0.0, 1.0], dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=20, snippet_window=16)
    assert frames.shape == (20,)
    assert np.allclose(frames[:16], 0.0)
    assert np.allclose(frames[16:], 1.0)


@pytest.mark.parametrize("n_frames", [160, 150, 140, 130])
def test_truncation_long_param(n_frames):
    """A5 variants: scores=ones(10), window=16 expands to 160 frames; truncation
    within 2*tol=32 of n_frames returns correct shape all-ones.
    (n_frames outside [160-32, 160+32] would correctly trip the C4 guard — see A6.)
    """
    scores = np.ones(10, dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=n_frames, snippet_window=16)
    assert frames.shape == (n_frames,)
    assert np.allclose(frames, 1.0)


# ---------------------------------------------------------------------------
# A6: tolerance violation raises
# ---------------------------------------------------------------------------


def test_tolerance_violation_raises():
    """A6: scores=[0.5], n_frames=1000, window=16, uf=1 → drift=984 > 2*16, raises."""
    scores = np.array([0.5], dtype=np.float32)
    with pytest.raises(AssertionError, match="length drift"):
        snippet_to_frame(scores, n_frames=1000, snippet_window=16, upsample_factor=1)


def test_drift_small_does_not_raise():
    """Just inside tolerance → no raise."""
    # expanded = 2 * 16 = 32; n_frames = 60; drift = 28; 2*tol = 32; within bound
    scores = np.ones(2, dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=60, snippet_window=16)
    assert frames.shape == (60,)


# ---------------------------------------------------------------------------
# A7: non-1D scores raises ValueError
# ---------------------------------------------------------------------------


def test_non_1d_scores_raises():
    """A7: 2D scores array → ValueError."""
    scores_2d = np.ones((3, 5), dtype=np.float32)
    with pytest.raises(ValueError, match="1D"):
        snippet_to_frame(scores_2d, n_frames=48, snippet_window=16)
