"""Integration tests for src/evaluate.py (Plan 04-02 Task 2).

E1: CLI smoke on synthetic UCF fixture — writes all 4 output files.
E2: Bit-identical rerun — all non-clock-dependent keys equal across runs.
E3: .done atomicity — marker only appears after eval_metrics.json is written.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def prepared_run_dir(tmp_path, synthetic_ucf_features):
    """Build a run_dir containing config_snapshot.json + best_model.pth.

    Uses the synthetic 10-video UCF fixture's annotation file at the path
    evaluate.py's D-04 fallback expects (data/annotations/ucf_temporal.txt
    under a local annotations_dir config path).
    """
    fx = synthetic_ucf_features
    run_dir = tmp_path / "ucf_gated_fusion_s42"
    run_dir.mkdir(parents=True)

    # The synthetic fixture already wrote an annotation file matching its
    # video_ids at fx["anno_path"]; copy it into a local annotations_dir.
    ann_dir = tmp_path / "data" / "annotations"
    ann_dir.mkdir(parents=True)
    shutil.copy(fx["anno_path"], ann_dir / "ucf_temporal.txt")

    cfg = {
        "seed": 42,
        "dataset": "ucf",
        "paths": {
            "skeleton_features": str(fx["skel_dir"]),
            "clip_features": str(fx["clip_dir"]),
            "splits_dir": str(fx["split_file"].parent),
            "annotations_dir": str(ann_dir),
            "results_dir": str(tmp_path),
        },
        "data": {"T": 32},
        "model": {
            "variant": "gated_fusion",
            "skel_dim": 256,
            "clip_dim": 1024,
            "shared_dim": 256,
            "head_hidden": [128, 32],
            "dropout": 0.3,
        },
        "wandb": {"mode": "disabled"},
    }
    snapshot = {"version": 1, "config": cfg, "git": {"sha": "test", "dirty": False}}
    (run_dir / "config_snapshot.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )

    # Build + save a randomly initialized model state dict via MODEL_REGISTRY.
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from src.models.registry import build_model
    model = build_model(**cfg["model"])
    torch.save(model.state_dict(), run_dir / "best_model.pth")
    return run_dir


def _run_evaluate(run_dir: Path, split: str = "test"):
    """Invoke `python src/evaluate.py --run-dir <run_dir> --split <split>`."""
    return subprocess.run(
        [sys.executable, "src/evaluate.py",
         "--run-dir", str(run_dir), "--split", split],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )


def test_evaluate_cli_smoke(prepared_run_dir):
    """E1: CLI exits 0 and writes eval_metrics.json + eval_scores.npz + per_category.csv + .done."""
    out = _run_evaluate(prepared_run_dir, split="test")
    assert out.returncode == 0, (
        f"CLI failed.\nstderr:\n{out.stderr}\nstdout:\n{out.stdout}"
    )
    for name in ("eval_metrics.json", "eval_scores.npz", "per_category.csv", ".done"):
        assert (prepared_run_dir / name).exists(), f"{name} missing"

    m = json.loads((prepared_run_dir / "eval_metrics.json").read_text())
    for k in ("auc", "ap", "n_videos", "n_frames",
              "config_hash", "git_sha", "checkpoint_sha",
              "dataset", "split", "seed", "eval_timestamp", "eval_duration_s",
              "per_category"):
        assert k in m, f"missing key {k} in eval_metrics.json"


def test_evaluate_bit_identical_rerun(prepared_run_dir):
    """E2: Running twice on same run_dir: all non-clock keys byte-equal.

    Clock-dependent keys (eval_timestamp, eval_duration_s) are excluded.
    """
    r1 = _run_evaluate(prepared_run_dir, split="test")
    assert r1.returncode == 0, r1.stderr
    m1 = json.loads((prepared_run_dir / "eval_metrics.json").read_text())

    # Remove .done so the runner would re-pick this up (simulates fresh run).
    (prepared_run_dir / ".done").unlink()
    r2 = _run_evaluate(prepared_run_dir, split="test")
    assert r2.returncode == 0, r2.stderr
    m2 = json.loads((prepared_run_dir / "eval_metrics.json").read_text())

    for k in ("auc", "ap", "n_videos", "n_frames",
              "config_hash", "checkpoint_sha", "dataset", "split", "seed"):
        assert m1.get(k) == m2.get(k), (
            f"non-determinism in {k}: {m1.get(k)!r} vs {m2.get(k)!r}"
        )


def test_done_after_metrics(prepared_run_dir):
    """E3: .done must not exist until eval_metrics.json is written."""
    r = _run_evaluate(prepared_run_dir, split="test")
    assert r.returncode == 0, r.stderr
    assert (prepared_run_dir / "eval_metrics.json").exists()
    assert (prepared_run_dir / ".done").exists()
