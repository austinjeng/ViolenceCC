"""
tests/test_splits.py — Validation tests for UCF-Crime and XD-Violence split files.

Tests verify:
  - Split files exist in data/splits/
  - No overlap between train/val/test within each dataset
  - Val fraction is approximately 15% (0.14 to 0.16)
  - Seed reproducibility: running create_splits.py twice produces byte-identical output
"""

import pathlib
import subprocess
import sys
import tempfile

import pytest

PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_split(path: pathlib.Path) -> list[str]:
    """Read a split file and return list of video IDs (stripped, non-empty)."""
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


# ---------------------------------------------------------------------------
# Existence tests
# ---------------------------------------------------------------------------

def test_ucf_split_files_exist(splits_dir):
    """All 3 UCF-Crime split files must exist in data/splits/."""
    for fname in ["ucf_train.txt", "ucf_val.txt", "ucf_test.txt"]:
        assert (splits_dir / fname).exists(), f"Missing: {splits_dir / fname}"


def test_xd_split_files_exist(splits_dir):
    """All 3 XD-Violence split files must exist in data/splits/."""
    for fname in ["xd_train.txt", "xd_val.txt", "xd_test.txt"]:
        assert (splits_dir / fname).exists(), f"Missing: {splits_dir / fname}"


# ---------------------------------------------------------------------------
# Non-overlap tests
# ---------------------------------------------------------------------------

def test_ucf_no_overlap(splits_dir):
    """UCF-Crime train, val, and test splits must be mutually exclusive."""
    train = set(read_split(splits_dir / "ucf_train.txt"))
    val = set(read_split(splits_dir / "ucf_val.txt"))
    test = set(read_split(splits_dir / "ucf_test.txt"))

    assert train & val == set(), f"UCF train/val overlap: {train & val}"
    assert train & test == set(), f"UCF train/test overlap: {train & test}"
    assert val & test == set(), f"UCF val/test overlap: {val & test}"


def test_xd_no_overlap(splits_dir):
    """XD-Violence train, val, and test splits must be mutually exclusive."""
    train = set(read_split(splits_dir / "xd_train.txt"))
    val = set(read_split(splits_dir / "xd_val.txt"))
    test = set(read_split(splits_dir / "xd_test.txt"))

    assert train & val == set(), f"XD train/val overlap: {train & val}"
    assert train & test == set(), f"XD train/test overlap: {train & test}"
    assert val & test == set(), f"XD val/test overlap: {val & test}"


# ---------------------------------------------------------------------------
# Val fraction tests
# ---------------------------------------------------------------------------

def test_ucf_val_fraction(splits_dir):
    """UCF-Crime val fraction must be between 14% and 16% of train+val."""
    train_ids = read_split(splits_dir / "ucf_train.txt")
    val_ids = read_split(splits_dir / "ucf_val.txt")
    total = len(train_ids) + len(val_ids)
    assert total > 0, "No UCF-Crime train+val videos found"
    fraction = len(val_ids) / total
    assert 0.14 <= fraction <= 0.16, (
        f"UCF val fraction {fraction:.3f} not in [0.14, 0.16]"
    )


def test_xd_val_fraction(splits_dir):
    """XD-Violence val fraction must be between 14% and 16% of train+val."""
    train_ids = read_split(splits_dir / "xd_train.txt")
    val_ids = read_split(splits_dir / "xd_val.txt")
    total = len(train_ids) + len(val_ids)
    assert total > 0, "No XD-Violence train+val videos found"
    fraction = len(val_ids) / total
    assert 0.14 <= fraction <= 0.16, (
        f"XD val fraction {fraction:.3f} not in [0.14, 0.16]"
    )


# ---------------------------------------------------------------------------
# Reproducibility test
# ---------------------------------------------------------------------------

def test_split_seed_reproducibility(splits_dir, tmp_path):
    """
    Running create_splits.py a second time must produce byte-identical split files.

    The test uses create_splits.py --verify which regenerates splits to a temp
    directory and compares against the committed files.
    """
    script = PROJECT_ROOT / "scripts" / "create_splits.py"
    result = subprocess.run(
        [sys.executable, str(script), "--verify"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, (
        f"Reproducibility check failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "PASSED" in result.stdout, (
        f"Expected 'PASSED' in output.\nSTDOUT:\n{result.stdout}"
    )


# ---------------------------------------------------------------------------
# Content sanity tests
# ---------------------------------------------------------------------------

def test_ucf_video_ids_non_empty(splits_dir):
    """UCF split files must have non-empty video ID lines."""
    for fname in ["ucf_train.txt", "ucf_val.txt", "ucf_test.txt"]:
        ids = read_split(splits_dir / fname)
        assert len(ids) > 0, f"{fname} has no video IDs"
        for vid in ids[:5]:
            assert vid, f"Empty video ID found in {fname}"


def test_xd_video_ids_non_empty(splits_dir):
    """XD split files must have non-empty video ID lines."""
    for fname in ["xd_train.txt", "xd_val.txt", "xd_test.txt"]:
        ids = read_split(splits_dir / fname)
        assert len(ids) > 0, f"{fname} has no video IDs"
        for vid in ids[:5]:
            assert vid, f"Empty video ID found in {fname}"
