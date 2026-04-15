"""RED-phase test for 04-01 Task 1: annotation file + conftest fixtures + synthetic_eval factories.

This test file is a TDD scaffold; it verifies that Task 1's deliverables land:
  - data/annotations/ucf_temporal.txt (Sultani 2018, >= 100 lines, 6 cols each)
  - tests/fixtures/synthetic_eval.py exports make_synthetic_ucf + make_synthetic_i3d
  - tests/conftest.py adds ucf_temporal_path, test_anno_path, eval_run_dir,
    synthetic_ucf_features, synthetic_i3d_features fixtures

It is removed after Task 2's proper unit tests cover the same surface via
tests/test_ucf_annotations.py + tests/test_snippet_to_frame.py.
"""
from __future__ import annotations

from pathlib import Path

import pytest


PROJECT_ROOT = Path("D:/ViolenceCC")


def test_ucf_temporal_file_exists_and_non_empty():
    p = PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    assert p.exists(), "data/annotations/ucf_temporal.txt must exist after Task 1"
    text = p.read_text(encoding="utf-8")
    assert len(text.strip()) > 0, "annotation file must be non-empty"


def test_ucf_temporal_file_has_6_columns_per_line():
    p = PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 100, f"expected >= 100 lines, got {len(lines)}"
    for ln in lines:
        parts = ln.split()
        assert len(parts) == 6, f"expected 6 cols, got {len(parts)} in line: {ln!r}"


def test_ucf_temporal_contains_known_video():
    p = PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    text = p.read_text(encoding="utf-8")
    assert "Abuse028_x264.mp4" in text, "expected Abuse028_x264.mp4 row"


def test_synthetic_eval_module_exports_factories():
    from tests.fixtures.synthetic_eval import (
        make_synthetic_ucf,
        make_synthetic_i3d,
    )

    assert callable(make_synthetic_ucf)
    assert callable(make_synthetic_i3d)


def test_make_synthetic_ucf_shape(tmp_path):
    from tests.fixtures.synthetic_eval import make_synthetic_ucf

    out = make_synthetic_ucf(tmp_path)
    assert "root" in out and "skel_dir" in out and "clip_dir" in out
    assert "split_file" in out and "anno_path" in out
    assert out["split_file"].exists()
    assert out["anno_path"].exists()
    assert len(out["video_ids"]) == 10


def test_make_synthetic_i3d_shape(tmp_path):
    from tests.fixtures.synthetic_eval import make_synthetic_i3d

    out = make_synthetic_i3d(tmp_path)
    assert out["train_split"].exists()
    assert out["test_split"].exists()
    assert len(out["train_ids"]) == 5
    assert len(out["test_ids"]) == 3


def test_conftest_exposes_ucf_temporal_path(ucf_temporal_path):
    assert ucf_temporal_path.exists()


def test_conftest_exposes_test_anno_path(test_anno_path):
    assert test_anno_path.exists()


def test_conftest_exposes_eval_run_dir(eval_run_dir):
    assert eval_run_dir.exists() and eval_run_dir.is_dir()


def test_conftest_exposes_synthetic_ucf_features(synthetic_ucf_features):
    assert "root" in synthetic_ucf_features


def test_conftest_exposes_synthetic_i3d_features(synthetic_i3d_features):
    assert "rgb" in synthetic_i3d_features
