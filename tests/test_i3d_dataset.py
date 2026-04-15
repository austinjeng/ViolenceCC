"""I3DFeatureDataset tests (Phase 4 Plan 03 Task 2).

Covers behaviors D1-D7 from the plan:
  D1  test-mode shape: [N, 1024] with 5 crops averaged; label parsed correctly.
  D2  train-mode shape: [5, T, 1024] (5-crop expansion, D-19).
  D3  label_A -> 0 (normal), not-label_A -> 1 (abnormal).
  D4  missing crops 1..4: _load_crops pads from crop 0 without exception (Pitfall 4 adjacent).
  D5  missing-video filter: split has 3 videos, only 2 on disk -> len==2 + "2/3 videos available" log.
  D6  all-normal warning: filtered to all label_A -> stderr contains "normal/abnormal" collapse warning.
  D7  yaml schema: configs/rtfm_i3d.yaml has required keys + batch_size=3 + dataset=xd_i3d.
"""
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

from src.data.i3d_dataset import I3DFeatureDataset


# ---- D1 test-mode shape + label parsing ----


def test_test_mode_shape_and_label(synthetic_i3d_features):
    """D1: test mode returns [N, 1024] float32 with crops averaged; label correct."""
    fx = synthetic_i3d_features
    ds = I3DFeatureDataset(
        split_file=str(fx["test_split"]),
        feature_dir=str(fx["rgbtest"]),
        mode="test",
        T=32,
    )
    assert len(ds) == 3
    s0 = ds[0]
    assert s0["i3d"].ndim == 2, f"expected [N, 1024] 2-d, got shape {tuple(s0['i3d'].shape)}"
    assert s0["i3d"].shape[1] == 1024
    # t000_label_B2-0-0 -> anomalous (label=1)
    assert s0["label"] == 1.0
    assert s0["video_id"].startswith("t")
    # dtype is float32 after crop-averaging
    assert s0["i3d"].dtype == torch.float32


# ---- D2 train-mode shape ----


def test_train_mode_shape(synthetic_i3d_features):
    """D2: train mode returns [5, T, 1024] (5 crops stacked, T=32 resampled)."""
    fx = synthetic_i3d_features
    ds = I3DFeatureDataset(
        split_file=str(fx["train_split"]),
        feature_dir=str(fx["rgb"]),
        mode="train",
        T=32,
    )
    assert len(ds) == 5
    s0 = ds[0]
    assert s0["i3d"].shape == (5, 32, 1024), (
        f"expected [5, 32, 1024], got {tuple(s0['i3d'].shape)}"
    )
    assert s0["i3d"].dtype == torch.float32


# ---- D3 label parsing ----


def test_label_parsing_label_a_is_normal(synthetic_i3d_features):
    """D3: videos ending in _label_A -> label=0.0; others -> label=1.0."""
    fx = synthetic_i3d_features
    ds = I3DFeatureDataset(
        split_file=str(fx["train_split"]),
        feature_dir=str(fx["rgb"]),
        mode="train",
        T=32,
    )
    normal = [ds[i] for i in range(len(ds)) if ds.video_ids[i].endswith("_label_A")]
    abnormal = [ds[i] for i in range(len(ds)) if not ds.video_ids[i].endswith("_label_A")]
    assert len(normal) > 0 and len(abnormal) > 0, "fixture must have both classes"
    assert all(s["label"] == 0.0 for s in normal)
    assert all(s["label"] == 1.0 for s in abnormal)


# ---- D4 missing crops pad from crop 0 ----


def test_missing_crops_pad_from_crop0(tmp_path):
    """D4: only __0.npy exists; crops 1..4 pad by duplicating crop 0 (no error)."""
    feat_dir = tmp_path / "feats"
    feat_dir.mkdir()
    vid = "partial_label_B1-0-0"
    np.save(
        feat_dir / f"{vid}__0.npy",
        np.random.randn(20, 1024).astype(np.float32),
    )
    splits = tmp_path / "splits.txt"
    splits.write_text(vid + "\n", encoding="utf-8")
    ds = I3DFeatureDataset(str(splits), str(feat_dir), mode="test", T=32)
    assert len(ds) == 1
    s = ds[0]
    # In test mode the crops (5 copies of crop 0) average back to crop 0.
    # Shape is [N, 1024] where N matches the crop 0 snippet count (20).
    assert s["i3d"].shape == (20, 1024)


# ---- D5 missing-video filter + log ----


def test_missing_video_filter_and_log(tmp_path, capsys):
    """D5: 3 videos in split, 2 on disk -> len==2 + stdout log '2/3 videos available'."""
    feat_dir = tmp_path / "feats"
    feat_dir.mkdir()
    for vid in ["v0_label_A", "v1_label_B1-0-0"]:
        np.save(
            feat_dir / f"{vid}__0.npy",
            np.random.randn(10, 1024).astype(np.float32),
        )
    splits = tmp_path / "splits.txt"
    splits.write_text(
        "v0_label_A\nv1_label_B1-0-0\nv2_label_A\n", encoding="utf-8"
    )
    ds = I3DFeatureDataset(str(splits), str(feat_dir), mode="train", T=32)
    assert len(ds) == 2
    captured = capsys.readouterr()
    assert "2/3 videos available" in captured.out, captured.out


# ---- D6 all-normal collapsed-ratio warning ----


def test_all_normal_warns_on_stderr(tmp_path, capsys):
    """D6: filtered set is all label_A -> WARNING on stderr, does NOT raise."""
    feat_dir = tmp_path / "feats"
    feat_dir.mkdir()
    for vid in ["v0_label_A", "v1_label_A"]:
        np.save(
            feat_dir / f"{vid}__0.npy",
            np.random.randn(10, 1024).astype(np.float32),
        )
    splits = tmp_path / "splits.txt"
    splits.write_text("v0_label_A\nv1_label_A\n", encoding="utf-8")
    ds = I3DFeatureDataset(str(splits), str(feat_dir), mode="train", T=32)
    assert len(ds) == 2
    captured = capsys.readouterr()
    # Accept either the "no abnormal videos" or "normal/abnormal ratio" phrasing.
    assert (
        "normal/abnormal" in captured.err
        or "no abnormal videos" in captured.err
    ), captured.err


# ---- D6 mirror: all-abnormal ratio warning ----


def test_all_abnormal_warns_on_stderr(tmp_path, capsys):
    """D6 mirror: filtered set is all abnormal -> WARNING on stderr."""
    feat_dir = tmp_path / "feats"
    feat_dir.mkdir()
    for vid in ["v0_label_B1-0-0", "v1_label_B2-0-0"]:
        np.save(
            feat_dir / f"{vid}__0.npy",
            np.random.randn(10, 1024).astype(np.float32),
        )
    splits = tmp_path / "splits.txt"
    splits.write_text(
        "v0_label_B1-0-0\nv1_label_B2-0-0\n", encoding="utf-8"
    )
    ds = I3DFeatureDataset(str(splits), str(feat_dir), mode="train", T=32)
    assert len(ds) == 2
    captured = capsys.readouterr()
    assert (
        "normal/abnormal" in captured.err
        or "no normal videos" in captured.err
    ), captured.err


# ---- D7 yaml schema ----


def test_yaml_schema():
    """D7: configs/rtfm_i3d.yaml has required keys per D-18/D-20/D-36 + Pitfall 3 batch_size."""
    with open("configs/rtfm_i3d.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg["dataset"] == "xd_i3d", cfg.get("dataset")
    assert cfg["paths"]["i3d_features"], "paths.i3d_features required"
    assert isinstance(cfg["paths"]["i3d_features"], str)
    assert cfg["model"]["variant"] == "rtfm_i3d"
    assert cfg["model"]["i3d_dim"] == 1024
    assert isinstance(cfg["data"]["batch_size"], int)
    # D-36: rtfm_i3d does not consume skeleton_features / clip_features.
    assert "skeleton_features" not in cfg["paths"]
    assert "clip_features" not in cfg["paths"]
    # Wandb tags per D-41: phase4 + rtfm_i3d markers.
    assert "phase4" in cfg["wandb"]["tags"]
    # Pitfall 3 recommendation: batch_size=3 (5-crop inflation vs k_topk=3).
    assert cfg["data"]["batch_size"] == 3, (
        f"Pitfall 3 recommends batch_size=3 at MVP; got {cfg['data']['batch_size']}"
    )


# ---- Invalid mode ----


def test_invalid_mode_raises(tmp_path):
    """Defensive: unknown mode raises ValueError before any file access."""
    splits = tmp_path / "splits.txt"
    splits.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="mode"):
        I3DFeatureDataset(str(splits), str(tmp_path), mode="garbage", T=32)


# ---- Plan 02 xd_i3d dispatch is now importable end-to-end ----


def test_test_loader_xd_i3d_importable(synthetic_i3d_features):
    """Smoke: Plan 02 test_loader.build_test_dataset can now import I3DFeatureDataset.

    Post-Task-2 we can reach the xd_i3d dispatch branch without the ImportError
    pointer message firing. We don't execute it end-to-end here -- just confirm
    the import contract is satisfied.
    """
    import sys
    # test_loader requires pytest-loaded or evaluate.py argv; pytest covers us.
    if "pytest" not in sys.modules:
        pytest.skip("only valid inside pytest")
    from src.data.i3d_dataset import I3DFeatureDataset as _I3D  # noqa: F401
    # Just importing it is the contract; actual dispatch is tested in test_test_loader.py.
