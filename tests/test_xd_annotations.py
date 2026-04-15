"""Unit tests for src/eval/xd_annotations.py (Phase 4b Plan 01).

Mirrors tests/test_ucf_annotations.py patterns, adapted for Wu 2020 format:
- Variable-interval rows (1+2*K columns)
- .mp4 suffix stripping (not _x264.mp4)
- Missing-normal-video semantics handled at the caller level
- Category parsing from _label_<code> suffix
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.eval.xd_annotations import (
    VideoAnnotation,
    parse_xd_annotations,
    xd_frame_labels,
    _parse_category,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------
# VALIDATION.md row 4b-01-01: real-file smoke test on committed data
# ------------------------------------------------------------------
def test_annotation_file_present(xd_temporal_path):
    """File at data/annotations/xd_temporal.txt exists with 500 abnormal entries."""
    annos = parse_xd_annotations(xd_temporal_path)
    assert len(annos) >= 500, f"expected >= 500 entries, got {len(annos)}"
    # Every parsed entry has at least one interval (normals are omitted from file)
    for vid, anno in annos.items():
        assert len(anno.intervals) >= 1, f"{vid} has no intervals"


# ------------------------------------------------------------------
# VALIDATION.md row 4b-01-02: multi-interval parsing (Wu-specific)
# ------------------------------------------------------------------
def test_parse_multi_interval(tmp_path):
    """Row with 3 intervals (7 columns total) parses to 3-tuple of intervals."""
    f = tmp_path / "anno.txt"
    f.write_text("v_label_B4-0-0 100 200 300 400 500 600\n", encoding="utf-8")
    annos = parse_xd_annotations(f)
    assert "v_label_B4-0-0" in annos
    anno = annos["v_label_B4-0-0"]
    assert anno.intervals == ((100, 200), (300, 400), (500, 600))
    assert anno.category == "B4"


def test_parse_strips_mp4_suffix(tmp_path):
    """Video IDs ending in .mp4 get the suffix stripped to match split-file keys."""
    f = tmp_path / "anno.txt"
    f.write_text(
        "A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_B2-0-0.mp4 420 1848\n",
        encoding="utf-8",
    )
    annos = parse_xd_annotations(f)
    assert "A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_B2-0-0" in annos
    # And NOT the .mp4 version
    assert "A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_B2-0-0.mp4" not in annos


def test_parse_preserves_v_prefix(tmp_path):
    """YouTube-sourced v=XXX IDs are preserved verbatim (no prefix stripping)."""
    f = tmp_path / "anno.txt"
    f.write_text("v=S-7rRLrxnVQ__#1_label_B4-0-0 150 420\n", encoding="utf-8")
    annos = parse_xd_annotations(f)
    assert "v=S-7rRLrxnVQ__#1_label_B4-0-0" in annos


# ------------------------------------------------------------------
# VALIDATION.md row 4b-01-03: frame_labels handles missing-video + clamping
# ------------------------------------------------------------------
def test_frame_labels_missing_video():
    """Empty-intervals annotation yields all-zero labels (supports normal-video default)."""
    anno = VideoAnnotation(video_id="v", category="Normal", intervals=())
    labels = xd_frame_labels(anno, n_frames=100)
    assert labels.shape == (100,)
    assert labels.sum() == 0


def test_frame_labels_clamp(tmp_path):
    """Interval endpoint > n_frames clamps without error."""
    f = tmp_path / "anno.txt"
    f.write_text("X_label_B1-0-0 50 120\n", encoding="utf-8")
    annos = parse_xd_annotations(f)
    labels = xd_frame_labels(annos["X_label_B1-0-0"], n_frames=100)
    assert labels.shape == (100,)
    assert int(labels[50:100].sum()) == 50
    assert int(labels[:50].sum()) == 0


def test_parse_raises_odd_intervals(tmp_path):
    """Row with odd-endpoint count raises ValueError."""
    f = tmp_path / "bad.txt"
    f.write_text("v_label_B1-0-0 100 200 300\n", encoding="utf-8")
    with pytest.raises(ValueError, match="odd"):
        parse_xd_annotations(f)


# ------------------------------------------------------------------
# Category parsing (Phase 4c forward-compat per D-10)
# ------------------------------------------------------------------
def test_parse_category_codes():
    """_parse_category maps common suffixes correctly."""
    assert _parse_category("v_label_B1-0-0") == "B1"
    assert _parse_category("v_label_B6-0-0") == "B6"
    assert _parse_category("v_label_G-B2-B6") == "G"
    assert _parse_category("v_label_B2-G-0") == "B2"
    assert _parse_category("v_label_A") == "Normal"
    assert _parse_category("random_noprefix") == "Unknown"
