"""C3 regression tests for src/eval/test_loader.py (Plan 04-02 Task 1).

Locks in BOTH defenses of C3 (test-set leakage prevention):

  1. Import boundary invariant (G1): importing src.data.dataset must NOT
     transitively pull in src.eval.test_loader.
  2. sys.argv runtime guard (G2/G3/G4): the module raises RuntimeError at
     import time unless the calling entry point is evaluate.py or pytest.

G5 exercises build_test_dataset(cfg={dataset: ucf}) on the synthetic
10-video fixture to ensure the MILFeatureDataset(mode="test") dispatch
is wired correctly.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_no_transitive_import():
    """G1 (C3 import boundary): `import src.data.dataset` must NOT pull in src.eval.test_loader."""
    out = subprocess.run(
        [sys.executable, "-c",
         "import src.data.dataset; import sys; "
         "assert 'src.eval.test_loader' not in sys.modules, "
         "'C3 regression: src.data.dataset transitively imported test_loader'"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    assert out.returncode == 0, (
        f"C3 import boundary violated:\nstderr={out.stderr}\nstdout={out.stdout}"
    )


def test_argv_guard_accepts_pytest():
    """G3 (C3 runtime guard — pytest accepted): sys.argv[0] contains 'pytest' in test context."""
    import importlib
    import src.eval.test_loader as tl
    importlib.reload(tl)
    assert hasattr(tl, "build_test_dataset")


def test_argv_guard_accepts_evaluate(monkeypatch):
    """G2 (C3 runtime guard — evaluate.py accepted): simulated evaluate.py entry point."""
    import importlib
    import src.eval.test_loader as tl
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--run-dir", "x"])
    importlib.reload(tl)
    assert hasattr(tl, "build_test_dataset")


def test_argv_guard_rejects_bad_entry():
    """G4 (C3 runtime guard — -c rejected): `python -c "import src.eval.test_loader"` exits non-zero."""
    out = subprocess.run(
        [sys.executable, "-c", "import src.eval.test_loader"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
    assert out.returncode != 0, (
        f"guard did not fire on -c entry. stdout={out.stdout} stderr={out.stderr}"
    )
    combined = out.stderr + out.stdout
    assert "test-set leakage" in combined, (
        f"RuntimeError message missing 'test-set leakage' substring: {combined}"
    )


def test_build_test_dataset_ucf_dispatch(synthetic_ucf_features):
    """G5 (dispatch): build_test_dataset(cfg={dataset: ucf}) returns a test-mode
    MILFeatureDataset and __getitem__ yields a well-formed sample."""
    from src.eval.test_loader import build_test_dataset
    fx = synthetic_ucf_features
    cfg = {
        "dataset": "ucf",
        "seed": 42,
        "paths": {
            "skeleton_features": str(fx["skel_dir"]),
            "clip_features": str(fx["clip_dir"]),
            "splits_dir": str(fx["split_file"].parent),
        },
        "data": {"T": 32},
    }
    ds = build_test_dataset(cfg)
    assert len(ds) == len(fx["video_ids"])
    sample = ds[0]
    for k in ("skel", "clip", "video_id", "label", "mask"):
        assert k in sample, f"missing key {k} in dataset sample"
