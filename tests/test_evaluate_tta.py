"""Integration tests for src/tta/evaluate_tta.py (Plan 05-04 Task 2).

Tests cover:
  1. source_only produces complete output artifacts
  2. tent produces correct output format
  3. sar produces correct output format with rho
  4. M7 skeleton path routing (clean vs corrupted)
  5. Per-video LN param reset verification
  6. Argument parser validation
  7. n_adapted_params in output JSON
"""
from __future__ import annotations

import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.registry import build_model
from src.tta.evaluate_tta import (
    SKELETON_REEXTRACT_TYPES,
    _SourceOnlyAdaptor,
    _load_test_video_features,
    parse_args,
    run_tta_evaluation,
)
from src.tta.tent import collect_params, configure_model


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_MODEL_CFG = {
    "variant": "gated_fusion",
    "skel_dim": 256,
    "clip_dim": 1024,
    "shared_dim": 256,
    "head_hidden": [128, 32],
    "dropout": 0.3,
}


@pytest.fixture
def tta_fixture(tmp_path):
    """Build a minimal TTA evaluation fixture.

    Creates:
      - Fake source run dir with config_snapshot.json + best_model.pth
      - Synthetic corruption feature directories
      - Synthetic clean skeleton directory
      - Split file + annotation file
    """
    rng = np.random.default_rng(42)

    # Video specs: 2 normal + 2 anomalous, each with 5 snippets
    specs = [
        ("Normal_Videos_001", "Normal", -1, -1, -1, -1),
        ("Normal_Videos_002", "Normal", -1, -1, -1, -1),
        ("Fighting003", "Fighting", 80, 160, -1, -1),
        ("Assault010", "Assault", 100, 250, -1, -1),
    ]
    n_snippets = 5

    # Feature root mimicking E:/features/ucf
    feat_root = tmp_path / "features"

    # Clean skeleton dir
    clean_skel = feat_root / "skeleton"
    clean_skel.mkdir(parents=True)

    # Corrupted dirs for gaussian_noise severity 3
    clip_corr = feat_root / "clip_gaussian_noise_3"
    clip_corr.mkdir(parents=True)
    skel_corr_mb = feat_root / "skeleton_motion_blur_3"
    skel_corr_mb.mkdir(parents=True)
    clip_corr_mb = feat_root / "clip_motion_blur_3"
    clip_corr_mb.mkdir(parents=True)

    video_ids = []
    anno_lines = []
    for vid, cat, s1, e1, s2, e2 in specs:
        skel = rng.standard_normal((n_snippets, 256)).astype(np.float32)
        clip = rng.standard_normal((n_snippets, 1024)).astype(np.float32)

        # Clean skeleton
        np.save(clean_skel / f"{vid}.npy", skel)
        # Corrupted CLIP for gaussian_noise
        np.save(clip_corr / f"{vid}.npy", clip)
        # Corrupted skel + clip for motion_blur
        np.save(skel_corr_mb / f"{vid}.npy", skel)
        np.save(clip_corr_mb / f"{vid}.npy", clip)

        video_ids.append(vid)
        anno_lines.append(f"{vid}_x264.mp4  {cat}  {s1}  {e1}  {s2}  {e2}")

    # Split file + annotation file in project layout
    data_dir = tmp_path / "data"
    splits_dir = data_dir / "splits"
    splits_dir.mkdir(parents=True)
    anno_dir = data_dir / "annotations"
    anno_dir.mkdir(parents=True)

    (splits_dir / "ucf_test.txt").write_text(
        "\n".join(video_ids) + "\n", encoding="utf-8"
    )
    (anno_dir / "ucf_temporal.txt").write_text(
        "\n".join(anno_lines) + "\n", encoding="utf-8"
    )

    # Source run dir
    run_dir = tmp_path / "results" / "ucf_gated_fusion_s42"
    run_dir.mkdir(parents=True)

    cfg = {
        "seed": 42,
        "dataset": "ucf",
        "paths": {
            "skeleton_features": str(clean_skel),
            "clip_features": str(clip_corr),
            "splits_dir": str(splits_dir),
            "annotations_dir": str(anno_dir),
            "results_dir": str(tmp_path / "results"),
        },
        "data": {"T": 32},
        "model": _MODEL_CFG,
        "wandb": {"mode": "disabled"},
    }
    snapshot = {"version": 1, "config": cfg, "git": {"sha": "test", "dirty": False}}
    (run_dir / "config_snapshot.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )

    model = build_model(**_MODEL_CFG)
    torch.save(model.state_dict(), run_dir / "best_model.pth")

    return {
        "run_dir": run_dir,
        "feat_root": feat_root,
        "data_dir": data_dir,
        "video_ids": video_ids,
        "n_snippets": n_snippets,
    }


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_run_tta_source_only_produces_outputs(tta_fixture, tmp_path, monkeypatch):
    """source_only method produces eval_metrics.json + eval_scores.npz + .done."""
    fx = tta_fixture
    output_dir = tmp_path / "output_source_only"

    # Monkeypatch _PROJECT_ROOT so evaluate_tta finds splits/annotations
    import src.tta.evaluate_tta as mod
    monkeypatch.setattr(mod, "_PROJECT_ROOT", fx["data_dir"].parent)

    run_tta_evaluation(
        source_run=fx["run_dir"],
        corruption_type="gaussian_noise",
        severity=3,
        method="source_only",
        lr=1e-3,
        rho=0.05,
        output_dir=output_dir,
        feature_root=fx["feat_root"],
    )

    # Check output files exist
    assert (output_dir / "eval_metrics.json").exists()
    assert (output_dir / "eval_scores.npz").exists()
    assert (output_dir / ".done").exists()

    # Check metrics JSON content
    m = json.loads((output_dir / "eval_metrics.json").read_text())
    assert "auc" in m
    assert "ap" in m
    assert m["method"] == "source_only"
    assert m["corruption_type"] == "gaussian_noise"
    assert m["severity"] == 3
    assert m["rho"] is None  # source_only has no rho


def test_run_tta_tent_produces_outputs(tta_fixture, tmp_path, monkeypatch):
    """TENT method produces complete output with correct metadata."""
    fx = tta_fixture
    output_dir = tmp_path / "output_tent"

    import src.tta.evaluate_tta as mod
    monkeypatch.setattr(mod, "_PROJECT_ROOT", fx["data_dir"].parent)

    run_tta_evaluation(
        source_run=fx["run_dir"],
        corruption_type="gaussian_noise",
        severity=3,
        method="tent",
        lr=1e-3,
        rho=0.05,
        output_dir=output_dir,
        feature_root=fx["feat_root"],
    )

    assert (output_dir / "eval_metrics.json").exists()
    assert (output_dir / "eval_scores.npz").exists()
    assert (output_dir / ".done").exists()

    m = json.loads((output_dir / "eval_metrics.json").read_text())
    assert m["method"] == "tent"
    assert m["lr"] == 0.001
    assert "auc" in m


def test_run_tta_sar_produces_outputs(tta_fixture, tmp_path, monkeypatch):
    """SAR method produces complete output with rho in metadata."""
    fx = tta_fixture
    output_dir = tmp_path / "output_sar"

    import src.tta.evaluate_tta as mod
    monkeypatch.setattr(mod, "_PROJECT_ROOT", fx["data_dir"].parent)

    run_tta_evaluation(
        source_run=fx["run_dir"],
        corruption_type="gaussian_noise",
        severity=3,
        method="sar",
        lr=1e-3,
        rho=0.01,
        output_dir=output_dir,
        feature_root=fx["feat_root"],
    )

    assert (output_dir / "eval_metrics.json").exists()
    assert (output_dir / ".done").exists()

    m = json.loads((output_dir / "eval_metrics.json").read_text())
    assert m["method"] == "sar"
    assert m["rho"] == 0.01
    assert m["lr"] == 0.001
    assert "auc" in m


def test_skeleton_path_routing_m7(tmp_path):
    """M7: gaussian_noise/brightness use clean skeleton; motion_blur/jpeg use corrupted."""
    feat_root = tmp_path / "features"

    # Create clean skeleton + corrupted dirs
    (feat_root / "skeleton").mkdir(parents=True)
    (feat_root / "clip_gaussian_noise_3").mkdir(parents=True)
    (feat_root / "clip_motion_blur_3").mkdir(parents=True)
    (feat_root / "skeleton_motion_blur_3").mkdir(parents=True)
    (feat_root / "clip_brightness_3").mkdir(parents=True)
    (feat_root / "clip_jpeg_compression_3").mkdir(parents=True)
    (feat_root / "skeleton_jpeg_compression_3").mkdir(parents=True)

    vid = "TestVideo001"
    skel_clean = np.ones((5, 256), dtype=np.float32)
    skel_corr = np.ones((5, 256), dtype=np.float32) * 2.0
    clip_feat = np.ones((5, 1024), dtype=np.float32)

    # Save features in all locations
    np.save(feat_root / "skeleton" / f"{vid}.npy", skel_clean)
    np.save(feat_root / "skeleton_motion_blur_3" / f"{vid}.npy", skel_corr)
    np.save(feat_root / "skeleton_jpeg_compression_3" / f"{vid}.npy", skel_corr)
    np.save(feat_root / "clip_gaussian_noise_3" / f"{vid}.npy", clip_feat)
    np.save(feat_root / "clip_motion_blur_3" / f"{vid}.npy", clip_feat)
    np.save(feat_root / "clip_brightness_3" / f"{vid}.npy", clip_feat)
    np.save(feat_root / "clip_jpeg_compression_3" / f"{vid}.npy", clip_feat)

    # gaussian_noise -> clean skeleton (val == 1.0)
    skel, clip = _load_test_video_features(vid, "gaussian_noise", 3, feat_root)
    assert skel is not None
    assert np.allclose(skel, 1.0), "gaussian_noise should use clean skeleton"

    # brightness -> clean skeleton (val == 1.0)
    skel, clip = _load_test_video_features(vid, "brightness", 3, feat_root)
    assert skel is not None
    assert np.allclose(skel, 1.0), "brightness should use clean skeleton"

    # motion_blur -> corrupted skeleton (val == 2.0)
    skel, clip = _load_test_video_features(vid, "motion_blur", 3, feat_root)
    assert skel is not None
    assert np.allclose(skel, 2.0), "motion_blur should use corrupted skeleton"

    # jpeg_compression -> corrupted skeleton (val == 2.0)
    skel, clip = _load_test_video_features(vid, "jpeg_compression", 3, feat_root)
    assert skel is not None
    assert np.allclose(skel, 2.0), "jpeg_compression should use corrupted skeleton"


def test_per_video_reset_verified():
    """Per-video reset restores LN params to exact source state values."""
    model = build_model(**_MODEL_CFG)
    source_state = deepcopy(model.state_dict())
    configure_model(model)
    params, names = collect_params(model)

    # Use high LR + multiple steps to ensure visible drift (same as test_tent.py pattern)
    optimizer = torch.optim.SGD(params, lr=0.1)
    from src.tta.tent import TentAdaptor
    adaptor = TentAdaptor(model, optimizer, source_state)

    # Process video 1: adapt multiple times to move LN params away from source
    skel = torch.randn(1, 5, 256)
    clip = torch.randn(1, 5, 1024)
    for _ in range(5):
        adaptor.adapt_and_score(skel, clip)

    # Verify params have moved
    current_state = model.state_dict()
    ln_moved = False
    for name in names:
        if not torch.allclose(current_state[name], source_state[name]):
            ln_moved = True
            break
    assert ln_moved, "LN params should have moved after adaptation"

    # Reset and verify params return to source
    adaptor.reset()
    reset_state = model.state_dict()
    for name in names:
        assert torch.allclose(reset_state[name], source_state[name]), (
            f"After reset, {name} should match source state"
        )

    # Process video 2: adapt again to confirm reset works across videos
    skel2 = torch.randn(1, 5, 256)
    clip2 = torch.randn(1, 5, 1024)
    for _ in range(5):
        adaptor.adapt_and_score(skel2, clip2)

    # Reset again
    adaptor.reset()
    reset_state2 = model.state_dict()
    for name in names:
        assert torch.allclose(reset_state2[name], source_state[name]), (
            f"After second reset, {name} should match source state"
        )


def test_parse_args_validates_choices():
    """parse_args rejects invalid method, corruption, and severity."""
    with pytest.raises(SystemExit):
        parse_args(["--source-run", "x", "--corruption", "gaussian_noise",
                     "--severity", "3", "--method", "invalid", "--output-dir", "y"])

    with pytest.raises(SystemExit):
        parse_args(["--source-run", "x", "--corruption", "unknown",
                     "--severity", "3", "--method", "tent", "--output-dir", "y"])

    with pytest.raises(SystemExit):
        parse_args(["--source-run", "x", "--corruption", "gaussian_noise",
                     "--severity", "0", "--method", "tent", "--output-dir", "y"])

    # Valid args should not raise
    args = parse_args(["--source-run", "x", "--corruption", "gaussian_noise",
                        "--severity", "3", "--method", "tent", "--output-dir", "y"])
    assert args.corruption == "gaussian_noise"
    assert args.severity == 3
    assert args.method == "tent"


def test_output_contains_n_adapted_params(tta_fixture, tmp_path, monkeypatch):
    """eval_metrics.json contains n_adapted_params matching GatedFusion's 1536 LN params."""
    fx = tta_fixture
    output_dir = tmp_path / "output_params"

    import src.tta.evaluate_tta as mod
    monkeypatch.setattr(mod, "_PROJECT_ROOT", fx["data_dir"].parent)

    run_tta_evaluation(
        source_run=fx["run_dir"],
        corruption_type="gaussian_noise",
        severity=3,
        method="source_only",
        lr=1e-3,
        rho=0.05,
        output_dir=output_dir,
        feature_root=fx["feat_root"],
    )

    m = json.loads((output_dir / "eval_metrics.json").read_text())
    assert "n_adapted_params" in m
    # GatedFusion has 3 LN modules x 256-d (weight + bias) = 3 * 512 = 1536
    assert m["n_adapted_params"] == 1536, (
        f"Expected 1536 adapted params, got {m['n_adapted_params']}"
    )
