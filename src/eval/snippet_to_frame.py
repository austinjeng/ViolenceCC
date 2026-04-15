"""Snippet-to-frame score broadcaster (Phase 4 D-15, C4 prevention).

Single utility that handles all broadcast cases encountered in Phase 4
evaluation:

  - UCF skeleton / CLIP path:  snippet_window=64 (PNG grid),
                                upsample_factor=10 (PNG -> 30fps original video)
  - XD I3D path:                snippet_window=16 (native I3D stride),
                                upsample_factor=1 (no-op)

Per D-15 the length-drift assertion below is the C4 guard: any upstream
inconsistency between N_snippets and the annotation-derived label vector
fails loudly before the sklearn metric call, instead of silently producing
wrong AUC/AP numbers.
"""
from __future__ import annotations

import numpy as np


def snippet_to_frame(
    scores: np.ndarray,
    n_frames: int,
    snippet_window: int,
    *,
    upsample_factor: int = 1,
) -> np.ndarray:
    """Broadcast snippet scores to frame-level scores (D-15, C4 regression surface).

    Usage:
      UCF skel/CLIP:  snippet_window=64 (PNGs), upsample_factor=10   # PNG grid -> 30fps
      XD I3D:         snippet_window=16,         upsample_factor=1    # native I3D 16-frame stride

    Args:
      scores: [N] 1D float per-snippet anomaly scores.
      n_frames: exact target length (from annotation-derived label vector).
      snippet_window: frames per snippet in model's native grid.
      upsample_factor: post-expansion multiplier (1 = no-op).

    Returns:
      [n_frames] float array. Truncated or tail-repeated to match n_frames exactly.

    Raises:
      ValueError: if scores is not 1D.
      AssertionError: if computed length drifts > 2 * (snippet_window * upsample_factor)
                      from n_frames (catches upstream N_snippets or label bugs).
    """
    if scores.ndim != 1:
        raise ValueError(f"scores must be 1D, got shape {scores.shape}")
    expanded = np.repeat(scores, snippet_window)
    if upsample_factor > 1:
        expanded = np.repeat(expanded, upsample_factor)
    tol = snippet_window * upsample_factor
    if abs(len(expanded) - n_frames) > 2 * tol:
        raise AssertionError(
            f"snippet_to_frame length drift exceeds tolerance: "
            f"expanded={len(expanded)} vs n_frames={n_frames} tol={tol}. "
            f"Upstream N_snippets or label vector is inconsistent."
        )
    if len(expanded) < n_frames:
        pad = np.full(n_frames - len(expanded), expanded[-1], dtype=expanded.dtype)
        return np.concatenate([expanded, pad])
    return expanded[:n_frames]
