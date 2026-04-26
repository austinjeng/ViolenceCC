"""Unit tests for the _build_frame_arrays ``dataset=xd`` branch (Phase 4c Plan 01).

Covers:
  - Abnormal videos produce non-zero labels from Wu annotation intervals
  - Normal videos (missing from Wu file) default to zero labels
  - snippet_window=64 and upsample_factor=1 (NOT 10 like UCF)
  - cats_map contains correct XD category codes from _label_ suffix
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.evaluate import _build_frame_arrays


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
# Test 1: abnormal XD video produces non-zero labels
# ==================================================================
def test_build_frame_arrays_xd_abnormal(tmp_path):
    """Abnormal video with matching Wu annotation produces labels with positive region.

    snippet_window=64, so 4 snippets -> n_frames = 4*64 = 256.
    Annotation interval [64, 192] -> labels[64:192] = 1 (128 positive frames).
    """
    ann_dir = _write_xd_annotation(
        tmp_path, ["abnormal_vid_label_B1-0-0 64 192"]
    )
    cfg = {
        "dataset": "xd",
        "paths": {"annotations_dir": str(ann_dir)},
    }
    # 4 snippets -> n_frames = 4 * 64 = 256
    scores = np.array([0.1, 0.5, 0.8, 0.2], dtype=np.float32)
    per_video_scores = {"abnormal_vid_label_B1-0-0": scores}

    frames_map, labels_map, cats_map = _build_frame_arrays(cfg, per_video_scores)

    vid = "abnormal_vid_label_B1-0-0"
    assert vid in frames_map and vid in labels_map and vid in cats_map
    assert frames_map[vid].shape == (256,)
    assert labels_map[vid].shape == (256,)
    assert labels_map[vid].dtype == np.int64
    # Non-zero labels from the [64, 192] interval
    assert labels_map[vid].sum() == 128, (
        f"expected 128 positive frames, got {labels_map[vid].sum()}"
    )
    # Correct region
    assert (labels_map[vid][64:192] == 1).all(), "interval [64, 192] not all ones"
    assert (labels_map[vid][:64] == 0).all(), "pre-interval not all zeros"
    assert (labels_map[vid][192:] == 0).all(), "post-interval not all zeros"
    # Category parsed from _label_ suffix
    assert cats_map[vid] == "B1", f"expected B1, got {cats_map[vid]}"


# ==================================================================
# Test 2: normal XD video (missing from Wu file) -> zero labels
# ==================================================================
def test_build_frame_arrays_xd_normal(tmp_path):
    """Normal video (not in annotations.txt) produces all-zero labels + cats=Normal."""
    # Annotation file has ONLY an abnormal entry; the normal "_label_A" video is omitted.
    ann_dir = _write_xd_annotation(
        tmp_path, ["other_abnormal_label_B2-0-0 10 30"]
    )
    cfg = {
        "dataset": "xd",
        "paths": {"annotations_dir": str(ann_dir)},
    }
    # 3 snippets -> n_frames = 3 * 64 = 192
    scores = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    per_video_scores = {"normal_vid_label_A": scores}

    frames_map, labels_map, cats_map = _build_frame_arrays(cfg, per_video_scores)

    vid = "normal_vid_label_A"
    assert vid in labels_map
    assert labels_map[vid].shape == (192,)
    assert labels_map[vid].sum() == 0, "normal video should have all-zero labels"
    assert cats_map[vid] == "Normal", f"expected Normal, got {cats_map[vid]}"
    assert frames_map[vid].shape == (192,), (
        f"expected shape (192,), got {frames_map[vid].shape}"
    )


# ==================================================================
# Test 3: snippet_window=64, upsample_factor=1 (NOT 10 like UCF)
# ==================================================================
def test_build_frame_arrays_xd_snippet_window(tmp_path):
    """Verify n_frames = len(scores) * 64, NOT len(scores) * 64 * 10 (UCF upsample)."""
    ann_dir = _write_xd_annotation(tmp_path, ["v_label_B1-0-0 0 128"])
    cfg = {
        "dataset": "xd",
        "paths": {"annotations_dir": str(ann_dir)},
    }
    for n_snippets in [1, 5, 20, 100]:
        scores = np.random.rand(n_snippets).astype(np.float32)
        per_video_scores = {"v_label_B1-0-0": scores}
        frames_map, _labels_map, _cats_map = _build_frame_arrays(
            cfg, per_video_scores
        )
        expected_len = n_snippets * 64  # NOT n_snippets * 64 * 10
        assert frames_map["v_label_B1-0-0"].shape == (expected_len,), (
            f"n_snippets={n_snippets}: expected length {expected_len}, "
            f"got {frames_map['v_label_B1-0-0'].shape}"
        )


# ==================================================================
# Test 4: cats_map contains correct XD category codes
# ==================================================================
def test_build_frame_arrays_xd_categories(tmp_path):
    """Verify cats_map contains correct XD category codes parsed from _label_ suffix."""
    ann_dir = _write_xd_annotation(
        tmp_path,
        [
            "fight_vid_label_B1-0-0 10 50",
            "shoot_vid_label_B2-G-0 20 60",
            "riot_vid_label_G-B2-B6 30 70",
        ],
    )
    cfg = {
        "dataset": "xd",
        "paths": {"annotations_dir": str(ann_dir)},
    }
    scores = np.array([0.5, 0.5], dtype=np.float32)
    per_video_scores = {
        "fight_vid_label_B1-0-0": scores,
        "shoot_vid_label_B2-G-0": scores,
        "riot_vid_label_G-B2-B6": scores,
        "normal_vid_label_A": scores,
    }

    _frames_map, _labels_map, cats_map = _build_frame_arrays(
        cfg, per_video_scores
    )

    assert cats_map["fight_vid_label_B1-0-0"] == "B1"
    assert cats_map["shoot_vid_label_B2-G-0"] == "B2"
    assert cats_map["riot_vid_label_G-B2-B6"] == "G"
    assert cats_map["normal_vid_label_A"] == "Normal"
