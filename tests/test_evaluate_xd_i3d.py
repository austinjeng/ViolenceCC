"""Unit tests for the rewritten _build_frame_arrays xd_i3d branch (Phase 4b Plan 04).

Covers VALIDATION.md rows 4b-04-01 / 4b-04-02 / 4b-04-03:
  - Abnormal videos produce non-zero labels from Wu annotation intervals
  - Normal videos (missing from Wu file) default to zero labels
  - C4 guard (from compute_frame_metrics) raises on length mismatch
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.evaluate import _build_frame_arrays
from src.eval.metrics import compute_frame_metrics


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------
# Helper: write a tiny Wu-format annotation file to tmp_path
# ------------------------------------------------------------------
def _write_xd_annotation(tmp_path: Path, rows: list[str]) -> Path:
    """Write rows to tmp_path/data/annotations/xd_temporal.txt, return the ann_dir path."""
    ann_dir = tmp_path / "data" / "annotations"
    ann_dir.mkdir(parents=True, exist_ok=True)
    (ann_dir / "xd_temporal.txt").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )
    return ann_dir


# ==================================================================
# VALIDATION.md row 4b-04-01: abnormal video produces non-zero labels
# ==================================================================
def test_build_frame_arrays_abnormal_nonzero(tmp_path):
    """Abnormal video with matching Wu annotation produces labels with positive region."""
    # Annotation: video "abnormal_vid_label_B1-0-0" has a single interval [16, 48]
    # With snippet_window=16, n_frames = 4 * 16 = 64.
    # labels[16:48] should be 1; labels[0:16] and labels[48:64] should be 0.
    ann_dir = _write_xd_annotation(tmp_path, ["abnormal_vid_label_B1-0-0 16 48"])
    cfg = {
        "dataset": "xd_i3d",
        "paths": {"annotations_dir": str(ann_dir)},
    }
    # 4 snippets -> n_frames = 4 * 16 = 64
    scores = np.array([0.1, 0.5, 0.8, 0.2], dtype=np.float32)
    per_video_scores = {"abnormal_vid_label_B1-0-0": scores}

    frames_map, labels_map, cats_map = _build_frame_arrays(cfg, per_video_scores)

    vid = "abnormal_vid_label_B1-0-0"
    assert vid in frames_map and vid in labels_map and vid in cats_map
    assert frames_map[vid].shape == (64,)
    assert labels_map[vid].shape == (64,)
    assert labels_map[vid].dtype == np.int64
    # Non-zero labels from the [16, 48] interval
    assert labels_map[vid].sum() == 32, (
        f"expected 32 positive frames, got {labels_map[vid].sum()}"
    )
    # Correct region
    assert (labels_map[vid][16:48] == 1).all(), "interval [16, 48] not all ones"
    assert (labels_map[vid][:16] == 0).all(), "pre-interval not all zeros"
    assert (labels_map[vid][48:] == 0).all(), "post-interval not all zeros"
    # Category parsed from _label_ suffix
    assert cats_map[vid] == "B1", f"expected B1, got {cats_map[vid]}"


# ==================================================================
# VALIDATION.md row 4b-04-02: normal video (missing from Wu file) -> zero labels
# ==================================================================
def test_build_frame_arrays_normal_zero(tmp_path):
    """Normal video (not in annotations.txt) produces all-zero labels + cats=Normal."""
    # Annotation file has ONLY an abnormal entry; the normal "_label_A" video is omitted.
    ann_dir = _write_xd_annotation(tmp_path, ["other_abnormal_label_B2-0-0 10 30"])
    cfg = {
        "dataset": "xd_i3d",
        "paths": {"annotations_dir": str(ann_dir)},
    }
    scores = np.array([0.1, 0.2, 0.3], dtype=np.float32)  # 3 snippets -> n_frames=48
    per_video_scores = {"normal_vid_label_A": scores}

    frames_map, labels_map, cats_map = _build_frame_arrays(cfg, per_video_scores)

    vid = "normal_vid_label_A"
    assert vid in labels_map
    assert labels_map[vid].shape == (48,)
    assert labels_map[vid].sum() == 0, "normal video should have all-zero labels"
    assert cats_map[vid] == "Normal", f"expected Normal, got {cats_map[vid]}"
    assert frames_map[vid].shape == (48,), (
        f"expected shape (48,), got {frames_map[vid].shape}"
    )


# ==================================================================
# VALIDATION.md row 4b-04-03: C4 guard trips on length mismatch
# ==================================================================
def test_c4_guard_trips_on_length_mismatch(tmp_path):
    """compute_frame_metrics raises AssertionError when frames_map[vid] and labels_map[vid]
    have different lengths (C4 contract inherited from src/eval/metrics.py)."""
    # Construct a deliberately mismatched pair by writing raw numpy arrays.
    # The sklearn downstream would produce garbage; the C4 guard catches it.
    frames_map = {"v": np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)}
    labels_map = {"v": np.array([0, 1, 0, 1, 0, 1], dtype=np.int64)}  # length 6 MISMATCH
    cats_map = {"v": "B1"}

    with pytest.raises((AssertionError, ValueError)):
        compute_frame_metrics(frames_map, labels_map, cats_map)


# ==================================================================
# Additional: snippet_to_frame broadcast shape sanity
# ==================================================================
def test_snippet_to_frame_broadcast_length(tmp_path):
    """frames_map[vid] has length exactly len(scores) * 16 (snippet_window=16, upsample=1)."""
    ann_dir = _write_xd_annotation(tmp_path, ["v_label_B1-0-0 0 32"])
    cfg = {
        "dataset": "xd_i3d",
        "paths": {"annotations_dir": str(ann_dir)},
    }
    for n_snippets in [1, 5, 20, 100]:
        scores = np.random.rand(n_snippets).astype(np.float32)
        per_video_scores = {"v_label_B1-0-0": scores}
        frames_map, _labels_map, _cats_map = _build_frame_arrays(
            cfg, per_video_scores
        )
        assert frames_map["v_label_B1-0-0"].shape == (n_snippets * 16,), (
            f"n_snippets={n_snippets}: expected length {n_snippets * 16}, "
            f"got {frames_map['v_label_B1-0-0'].shape}"
        )
