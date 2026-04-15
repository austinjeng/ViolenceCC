"""Unit tests for src.eval.ucf_annotations parser (Plan 04-01 Task 2).

Covers behaviors B1..B9 from the plan.

B1: parse_annotations on real data/annotations/ucf_temporal.txt
    → >= 150 entries, Abuse028 category=='Abuse', intervals[0]==(165,240),
      intervals[1]==(None,None)
B2: Normal_Videos_* entry → all four interval values None, is_normal True
    (synthetic; the Sultani file does not include Normal rows — it lists only
     anomaly test videos, so we exercise Normal parsing via tmp_path)
B3: Arson011 (two-interval) → intervals == ((150,420), (680,1267))
B4: frame_labels(Abuse028, 500) → labels[165:240]==1, outside==0
B5: union for Arson011 with n_frames=1400
B6: frame_labels on Normal entry returns all zeros (synthetic)
B7: clamping — frame_labels(Abuse028, n_frames=100) returns (100,) with no OOB
B8: malformed line (5 cols) raises ValueError
B9: import boundary — parse_annotations + frame_labels + VideoAnnotation
    importable from src.eval.* without touching test_loader's sys.argv guard
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.eval.snippet_to_frame import snippet_to_frame  # B9 (co-import)
from src.eval.ucf_annotations import (
    VideoAnnotation,
    frame_labels,
    parse_annotations,
)


# ---------------------------------------------------------------------------
# B1: real-file parse
# ---------------------------------------------------------------------------


def test_parse_annotations_real_file(ucf_temporal_path):
    """B1: parsing the real Sultani file yields >= 150 entries with Abuse028."""
    annos = parse_annotations(ucf_temporal_path)
    assert len(annos) >= 150, f"expected >= 150, got {len(annos)}"
    assert "Abuse028" in annos
    a = annos["Abuse028"]
    assert a.category == "Abuse"
    assert a.intervals[0] == (165, 240)
    assert a.intervals[1] == (None, None)


def test_parse_annotations_is_dataclass_instance(ucf_temporal_path):
    """Sanity: parsed entry is a VideoAnnotation instance."""
    annos = parse_annotations(ucf_temporal_path)
    abuse = annos["Abuse028"]
    assert isinstance(abuse, VideoAnnotation)


# ---------------------------------------------------------------------------
# B2: Normal row (synthetic, since Sultani file lacks Normal rows)
# ---------------------------------------------------------------------------


def test_parse_normal_video_synthetic(tmp_path):
    """B2: Normal row with all -1 → intervals all None, is_normal True."""
    f = tmp_path / "anno.txt"
    f.write_text(
        "Normal_Videos_003_x264.mp4  Normal  -1  -1  -1  -1\n", encoding="utf-8"
    )
    annos = parse_annotations(f)
    assert "Normal_Videos_003" in annos
    n = annos["Normal_Videos_003"]
    assert n.category == "Normal"
    assert n.intervals == ((None, None), (None, None))
    assert n.is_normal is True


# ---------------------------------------------------------------------------
# B3: two-interval entry from real file
# ---------------------------------------------------------------------------


def test_parse_arson011_two_intervals(ucf_temporal_path):
    """B3: Arson011 has intervals ((150,420), (680,1267))."""
    annos = parse_annotations(ucf_temporal_path)
    a = annos["Arson011"]
    assert a.category == "Arson"
    assert a.intervals[0] == (150, 420)
    assert a.intervals[1] == (680, 1267)
    assert a.is_normal is False


# ---------------------------------------------------------------------------
# B4: frame_labels on Abuse028, n_frames=500
# ---------------------------------------------------------------------------


def test_frame_labels_abuse028(ucf_temporal_path):
    """B4: labels[165:240]==1, outside==0 for n_frames=500."""
    annos = parse_annotations(ucf_temporal_path)
    labels = frame_labels(annos["Abuse028"], n_frames=500)
    assert labels.shape == (500,)
    assert labels.dtype == np.int64
    assert labels[:165].sum() == 0
    assert (labels[165:240] == 1).all()
    assert labels[240:].sum() == 0


# ---------------------------------------------------------------------------
# B5: union for Arson011 with n_frames=1400
# ---------------------------------------------------------------------------


def test_frame_labels_arson011_union(ucf_temporal_path):
    """B5: Arson011 with n_frames=1400 → labels[150:420]=1, labels[680:1267]=1, gap=0."""
    annos = parse_annotations(ucf_temporal_path)
    labels = frame_labels(annos["Arson011"], n_frames=1400)
    assert labels.shape == (1400,)
    assert (labels[150:420] == 1).all()
    assert (labels[680:1267] == 1).all()
    assert labels[:150].sum() == 0
    assert labels[420:680].sum() == 0
    assert labels[1267:].sum() == 0


# ---------------------------------------------------------------------------
# B6: Normal entry → all zeros
# ---------------------------------------------------------------------------


def test_frame_labels_normal_all_zeros(tmp_path):
    """B6: Normal anno → labels all zero."""
    f = tmp_path / "anno.txt"
    f.write_text(
        "Normal_Videos_001_x264.mp4  Normal  -1  -1  -1  -1\n", encoding="utf-8"
    )
    annos = parse_annotations(f)
    labels = frame_labels(annos["Normal_Videos_001"], n_frames=300)
    assert labels.shape == (300,)
    assert labels.sum() == 0


# ---------------------------------------------------------------------------
# B7: clamping — n_frames smaller than end index
# ---------------------------------------------------------------------------


def test_frame_labels_clamps_end(ucf_temporal_path):
    """B7: frame_labels(Abuse028, 100) clamps e=240 to 100 without OOB."""
    annos = parse_annotations(ucf_temporal_path)
    labels = frame_labels(annos["Abuse028"], n_frames=100)
    assert labels.shape == (100,)
    # start=165 is already >= n_frames=100, so entire vector should be zero
    assert labels.sum() == 0


def test_frame_labels_clamps_with_partial_overlap(tmp_path):
    """B7 extended: anno interval (50, 120) with n_frames=100 → labels[50:100] == 1."""
    f = tmp_path / "anno.txt"
    f.write_text("X_x264.mp4  Arson  50  120  -1  -1\n", encoding="utf-8")
    annos = parse_annotations(f)
    labels = frame_labels(annos["X"], n_frames=100)
    assert labels.shape == (100,)
    assert (labels[50:100] == 1).all()
    assert labels[:50].sum() == 0


# ---------------------------------------------------------------------------
# B8: malformed row raises
# ---------------------------------------------------------------------------


def test_malformed_row_5_cols_raises(tmp_path):
    """B8: 5-column row → ValueError."""
    f = tmp_path / "bad.txt"
    f.write_text("Abuse028_x264.mp4  Abuse  165  240  -1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="6 columns"):
        parse_annotations(f)


def test_malformed_row_7_cols_raises(tmp_path):
    """B8 extended: 7-column row → ValueError."""
    f = tmp_path / "bad.txt"
    f.write_text(
        "Abuse028_x264.mp4  Abuse  165  240  -1  -1  extra\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="6 columns"):
        parse_annotations(f)


# ---------------------------------------------------------------------------
# B9: import boundary (no sys.argv guard fires)
# ---------------------------------------------------------------------------


def test_import_surface():
    """B9: co-importing utilities does not trigger test_loader sys.argv guard."""
    from src.eval.snippet_to_frame import snippet_to_frame as _s2f  # noqa: F401
    from src.eval.ucf_annotations import (  # noqa: F401
        VideoAnnotation as _VA,
        frame_labels as _fl,
        parse_annotations as _pa,
    )


def test_empty_file_returns_empty_dict(tmp_path):
    """Edge case: empty annotation file yields empty dict (no raise)."""
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    annos = parse_annotations(f)
    assert annos == {}


def test_blank_lines_skipped(tmp_path):
    """Blank lines in between rows should be skipped, not raise."""
    f = tmp_path / "anno.txt"
    f.write_text(
        "Abuse028_x264.mp4  Abuse  165  240  -1  -1\n"
        "\n"
        "   \n"
        "Arson011_x264.mp4  Arson  150  420  680  1267\n",
        encoding="utf-8",
    )
    annos = parse_annotations(f)
    assert len(annos) == 2
    assert "Abuse028" in annos and "Arson011" in annos
