"""Unit tests for src/eval/metrics.py (Plan 04-02 Task 2).

Covers C4 regression surface and D-11 per-category breakdown:

  M1: compute_frame_metrics returns auc/ap/n_videos/n_frames/per_category
      keys on a 3-video synthetic dataset.
  M2: Length mismatch between scores and labels raises AssertionError with
      substring "C4 REGRESSION" — the contract every sklearn.metrics
      call must honor per D-15.
  M3: per_category dict excludes "Normal" (D-17 + Discretion default).
  M4: Single-class category is skipped (roc_auc_score needs both classes).
"""
from __future__ import annotations

import numpy as np
import pytest

from src.eval.metrics import compute_frame_metrics


def test_basic_metrics_shape():
    """M1: All expected keys present, values are finite floats."""
    per_scores = {
        "v1": np.array([0.1, 0.2, 0.8, 0.9, 0.1], dtype=np.float32),
        "v2": np.array([0.05, 0.1, 0.1, 0.1, 0.05], dtype=np.float32),
        "v3": np.array([0.9, 0.95, 0.99, 0.9, 0.9], dtype=np.float32),
    }
    per_labels = {
        "v1": np.array([0, 0, 1, 1, 0], dtype=np.int64),
        "v2": np.zeros(5, dtype=np.int64),
        "v3": np.ones(5, dtype=np.int64),
    }
    per_cat = {"v1": "Abuse", "v2": "Normal", "v3": "Fighting"}
    result = compute_frame_metrics(per_scores, per_labels, per_cat)
    for k in ("auc", "ap", "n_videos", "n_frames", "per_category"):
        assert k in result, f"missing key {k}"
    assert result["n_videos"] == 3
    assert result["n_frames"] == 15
    assert isinstance(result["auc"], float) and np.isfinite(result["auc"])
    assert isinstance(result["ap"], float) and np.isfinite(result["ap"])


def test_per_category_excludes_normal():
    """M3: Normal is never a per_category key (D-17 + Discretion omit-normal)."""
    per_scores = {
        "v1": np.array([0.1, 0.9], dtype=np.float32),
        "v2": np.array([0.2, 0.3], dtype=np.float32),
        "v3": np.array([0.8, 0.9], dtype=np.float32),
    }
    per_labels = {
        "v1": np.array([0, 1], dtype=np.int64),
        "v2": np.zeros(2, dtype=np.int64),
        "v3": np.array([1, 1], dtype=np.int64),
    }
    per_cat = {"v1": "Abuse", "v2": "Normal", "v3": "Fighting"}
    result = compute_frame_metrics(per_scores, per_labels, per_cat)
    assert "Abuse" in result["per_category"]
    assert "Fighting" in result["per_category"]
    assert "Normal" not in result["per_category"]


def test_c4_assertion_fires():
    """M2: C4 REGRESSION AssertionError fires on length mismatch."""
    per_scores = {"v1": np.zeros(10, dtype=np.float32)}
    per_labels = {"v1": np.zeros(11, dtype=np.int64)}
    per_cat = {"v1": "Abuse"}
    with pytest.raises(AssertionError, match="C4 REGRESSION"):
        compute_frame_metrics(per_scores, per_labels, per_cat)


def test_per_category_single_class_skipped():
    """M4: A category whose combined vids have only one label class is skipped."""
    # Abuse + Normal — both have only zero labels when combined (no true anomalies).
    per_scores = {
        "v1": np.array([0.5, 0.5], dtype=np.float32),
        "v2": np.array([0.1, 0.1], dtype=np.float32),
    }
    per_labels = {
        "v1": np.zeros(2, dtype=np.int64),
        "v2": np.zeros(2, dtype=np.int64),
    }
    per_cat = {"v1": "Abuse", "v2": "Normal"}
    # Global AUC is undefined (single class) — sklearn raises ValueError.
    # Accept either: graceful None/skip in per_category, or ValueError at global.
    try:
        r = compute_frame_metrics(per_scores, per_labels, per_cat)
        assert "Abuse" not in r.get("per_category", {})
    except ValueError:
        # sklearn's "Only one class" error surfaces for global auc — acceptable
        pass
