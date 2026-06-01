"""Regression test: _smoothness must penalize the TEMPORAL axis (dim 1), not
the batch/video axis (dim 0).

Bug (260601-o55): the original `_smoothness` shifted dim 0 (`arr2[:-1] = arr[1:]`),
penalizing differences between DIFFERENT videos in the bag instead of between
adjacent snippets in time within one video.

These assertions distinguish the two axes directly. They deliberately do NOT
compare against tests/test_mil_loss.py::_rtfm_smooth_ref, which carries the same
batch-axis bug and would mask the regression.
"""
import torch

from src.losses.mil_loss import _smoothness


def test_temporal_ramp_incurs_nonzero_penalty():
    """A single bag [1, T] whose scores ramp in time incurs a nonzero temporal penalty."""
    lam = 8e-4
    scores = torch.arange(6, dtype=torch.float32).reshape(1, 6)  # [[0,1,2,3,4,5]]
    penalty = _smoothness(scores, lam)
    # Adjacent temporal diffs are all 1.0 (last position diff = 0 by boundary rule):
    # sum of squares over 5 diffs = 5.0 -> lam * 5.0
    assert penalty.item() > 0.0, f"temporal ramp must be penalized, got {penalty.item()}"
    assert abs(penalty.item() - lam * 5.0) < 1e-9, (
        f"expected lam*5.0={lam*5.0}, got {penalty.item()}"
    )


def test_flat_in_time_but_different_videos_incurs_zero_penalty():
    """Two temporally-FLAT videos that differ from each other (across dim 0) incur ~0.

    scores = [[0.2,0.2,0.2],[0.9,0.9,0.9]] (shape [2,3]):
      - corrected temporal version: each ROW is flat in time -> penalty ~ 0
      - old batch-axis version: rows differ across dim 0 -> heavily penalized
    """
    lam = 8e-4
    scores = torch.tensor([[0.2, 0.2, 0.2], [0.9, 0.9, 0.9]], dtype=torch.float32)
    penalty = _smoothness(scores, lam)
    assert penalty.item() < 1e-6 * lam, (
        "rows are flat in time so temporal smoothness must be ~0; "
        f"got {penalty.item()} (old batch-axis bug would penalize the "
        "inter-video 0.2-vs-0.9 difference)"
    )


def test_axis_distinguishes_temporal_from_batch():
    """A single input whose two interpretations give different penalties.

    scores = [[0,0,0],[1,1,1]]:
      - temporal (correct): each row flat in time -> penalty 0
      - batch-axis (buggy): row0 vs row1 differ by 1 across dim 0 -> penalty lam*3
    The corrected implementation MUST return 0, not lam*3.
    """
    lam = 8e-4
    scores = torch.tensor([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=torch.float32)
    penalty = _smoothness(scores, lam)
    assert abs(penalty.item()) < 1e-9, (
        f"temporal smoothness of row-wise-flat input must be 0, got {penalty.item()} "
        f"(batch-axis bug would give lam*3={lam*3.0})"
    )
