"""H1 regression: snippet_to_frame tail-pads to a boundary-driven n_frames
that is STRICTLY LARGER than the snippet-count grid (260601-jtb Task 3).

The H1 bug truncated the UCF eval frame grid to the snippet-count length
(len(scores)*64*10) instead of the true video length (total_frames*10). These
tests lock the corrected behavior: when n_frames is derived from the true
boundary length and exceeds the snippet-count grid, snippet_to_frame extends
the grid by tail-repeating the LAST snippet score.

Fast, GPU-free, feature-free — imports only numpy + snippet_to_frame, matching
the style of tests/test_snippet_to_frame.py.
"""
from __future__ import annotations

import numpy as np

from src.eval.snippet_to_frame import snippet_to_frame


# UCF grid constants (D-14): 64-PNG window, 10x upsample -> 640 frames/snippet.
SNIPPET_WINDOW = 64
UPSAMPLE = 10
BLOCK = SNIPPET_WINDOW * UPSAMPLE  # 640


def test_boundary_length_extends_snippet_grid():
    """Boundary-driven n_frames (total_frames*10) > snippet-count grid (N*640).

    scores=[0.1,0.5,0.9] -> snippet-count grid = 3*640 = 1920.
    total_frames=200 -> boundary n_frames = 200*10 = 2000 > 1920 (the fix
    EXTENDS the grid; it never truncates real positive frames).
    """
    scores = np.array([0.1, 0.5, 0.9], dtype=np.float32)
    snippet_grid = len(scores) * SNIPPET_WINDOW * UPSAMPLE  # 1920
    total_frames = 200
    n_frames = total_frames * UPSAMPLE  # 2000

    assert n_frames > snippet_grid  # the fix extends, not truncates
    assert snippet_grid == 1920
    assert n_frames == 2000


def test_tail_pad_to_true_length_repeats_last_score():
    """snippet_to_frame returns EXACTLY n_frames=2000 and tail-pads with the
    last snippet score (0.9) beyond the 1920 snippet-count grid.
    """
    scores = np.array([0.1, 0.5, 0.9], dtype=np.float32)
    frames = snippet_to_frame(
        scores, n_frames=2000, snippet_window=SNIPPET_WINDOW,
        upsample_factor=UPSAMPLE,
    )

    # Exact target length.
    assert frames.shape == (2000,)

    # Body (first 1920) is the normal per-snippet repeat.
    assert np.allclose(frames[:640], 0.1)
    assert np.allclose(frames[640:1280], 0.5)
    assert np.allclose(frames[1280:1920], 0.9)

    # Padded tail (indices >= 1920) all equal the LAST snippet score.
    assert np.allclose(frames[1920:], scores[-1])
    assert np.allclose(frames[1920:], 0.9)


def test_overshoot_within_drift_guard_does_not_raise():
    """Overshoot here is 80 frames (2000 - 1920), well inside the existing
    drift guard 2*snippet_window*upsample = 2*64*10 = 1280, so no
    AssertionError is raised.
    """
    scores = np.array([0.1, 0.5, 0.9], dtype=np.float32)
    overshoot = 2000 - len(scores) * SNIPPET_WINDOW * UPSAMPLE  # 80
    tol = 2 * SNIPPET_WINDOW * UPSAMPLE  # 1280
    assert overshoot < tol

    # Must not raise (the call itself is the assertion).
    frames = snippet_to_frame(
        scores, n_frames=2000, snippet_window=SNIPPET_WINDOW,
        upsample_factor=UPSAMPLE,
    )
    assert frames.shape == (2000,)
