"""Unit tests for build_dataloaders_i3d + collate_i3d_train (Phase 4b Plan 02).

Covers VALIDATION.md rows 4b-02-01 / 4b-02-02 / 4b-02-03:
  - Returns tuple of (nor, abn, val) loaders with correct batch shape [B*5, T, 1024]
  - collate_i3d_train flattens [B, 5, T, 1024] -> [B*5, T, 1024]
  - nor/abn partition is non-empty on synthetic fixture

Plus Pitfall guards:
  - Pitfall 1: mask is all-ones (not missing; required by mil_ranking_loss)
  - Pitfall 4: labels repeated consecutively 5x via repeat_interleave (not interleaved wrong)
"""
from __future__ import annotations

import pytest
import torch

from src.data.loaders import build_dataloaders_i3d, collate_i3d_train


# ------------------------------------------------------------------
# Helper: build a minimal cfg dict pointing at the synthetic_i3d_features fixture.
# ------------------------------------------------------------------
def _build_cfg(fx, batch_size: int = 2, T: int = 32) -> dict:
    """Build a minimal xd_i3d cfg dict for build_dataloaders_i3d.

    The synthetic_i3d_features fixture creates ``xd_train.txt`` and ``xd_test.txt``
    but NOT ``xd_val.txt``; this helper synthesizes a minimal ``xd_val.txt`` that
    contains one normal + one abnormal video reused from the training set so
    ``build_dataloaders_i3d``'s Open Question #1 assertion (val must have >=1
    abnormal video) is satisfied for shape-contract tests.
    """
    splits_dir = fx["train_split"].parent
    val_split = splits_dir / "xd_val.txt"
    if not val_split.exists():
        train_ids = fx["train_split"].read_text(encoding="utf-8").strip().splitlines()
        normal = next((v for v in train_ids if v.strip().endswith("_label_A")), None)
        abnorm = next((v for v in train_ids if not v.strip().endswith("_label_A")), None)
        assert normal is not None and abnorm is not None, (
            "fixture missing mixed labels"
        )
        val_split.write_text(f"{normal}\n{abnorm}\n", encoding="utf-8")
    return {
        "seed": 42,
        "dataset": "xd_i3d",
        "paths": {
            "splits_dir": str(splits_dir),
            # synthetic_i3d_features lays out tmp_path/i3d/RGB and tmp_path/i3d/RGBTest;
            # build_dataloaders_i3d expects paths.i3d_features to be the PARENT of RGB/.
            "i3d_features": str(fx["rgb"].parent),
        },
        "data": {
            "T": T,
            "batch_size": batch_size,
            "num_workers": 0,
            "pin_memory": False,
        },
    }


# ==================================================================
# VALIDATION.md row 4b-02-01: build_dataloaders_i3d returns (nor, abn, val)
# ==================================================================
def test_build_dataloaders_i3d_shape(synthetic_i3d_features):
    """Tuple shape: ((nor_loader, abn_loader), val_loader); batch i3d shape [bs*5, T, 1024]."""
    cfg = _build_cfg(synthetic_i3d_features, batch_size=2, T=32)
    (nor_loader, abn_loader), val_loader = build_dataloaders_i3d(cfg)

    # Verify iterable structure
    assert nor_loader is not None and abn_loader is not None and val_loader is not None

    # Verify batch shape after collate flattens 5 crops into batch dim.
    # batch_size=2, n_crops=5 -> 10 samples per batch.
    batch = next(iter(nor_loader))
    assert "i3d" in batch and "label" in batch and "mask" in batch and "video_id" in batch
    assert batch["i3d"].shape == (2 * 5, 32, 1024), (
        f"got {tuple(batch['i3d'].shape)}"
    )
    assert batch["label"].shape == (2 * 5,)
    assert batch["mask"].shape == (2 * 5, 32)
    assert len(batch["video_id"]) == 2 * 5


# ==================================================================
# VALIDATION.md row 4b-02-02: collate_i3d_train flattens [B, 5, T, 1024] -> [B*5, T, 1024]
# ==================================================================
def test_collate_flattens_crops():
    """collate_i3d_train flattens the 5-crop dim into batch dim."""
    samples = [
        {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": f"v{i}_label_A"}
        for i in range(3)
    ] + [
        {"i3d": torch.randn(5, 32, 1024), "label": 1.0, "video_id": f"w{i}_label_B1-0-0"}
        for i in range(3)
    ]
    out = collate_i3d_train(samples)
    assert out["i3d"].shape == (6 * 5, 32, 1024)
    assert out["label"].shape == (6 * 5,)
    assert out["mask"].shape == (6 * 5, 32)
    assert len(out["video_id"]) == 6 * 5


def test_collate_label_replication():
    """Each video's label replicated CONSECUTIVELY 5x (Pitfall 4 guard).

    Input labels [0.0, 0.0, 1.0] -> output labels [0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1].
    NOT [0,0,0, 0,0,0, 1,1,1, 0,0, 1,1, 0,1] (wrong interleaving).
    """
    samples = [
        {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": "v0_label_A"},
        {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": "v1_label_A"},
        {"i3d": torch.randn(5, 32, 1024), "label": 1.0, "video_id": "v2_label_B1-0-0"},
    ]
    out = collate_i3d_train(samples)
    labels = out["label"]
    # First 5 (sample 0) = 0.0, next 5 (sample 1) = 0.0, next 5 (sample 2) = 1.0
    assert (labels[0:5] == 0.0).all(), f"crops 0-4 not all 0: {labels[0:5]}"
    assert (labels[5:10] == 0.0).all(), f"crops 5-9 not all 0: {labels[5:10]}"
    assert (labels[10:15] == 1.0).all(), f"crops 10-14 not all 1: {labels[10:15]}"
    # Video IDs similarly replicated
    vids = out["video_id"]
    assert vids[0:5] == ["v0_label_A"] * 5
    assert vids[5:10] == ["v1_label_A"] * 5
    assert vids[10:15] == ["v2_label_B1-0-0"] * 5


def test_collate_mask_all_ones():
    """Pitfall 1 guard: mask is all-ones tensor (no padding; required by mil_ranking_loss)."""
    samples = [
        {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": f"v{i}"}
        for i in range(4)
    ]
    out = collate_i3d_train(samples)
    mask = out["mask"]
    assert mask.shape == (4 * 5, 32)
    assert mask.sum().item() == 4 * 5 * 32, f"mask not all ones: sum={mask.sum()}"
    assert mask.dtype == torch.float32


# ==================================================================
# VALIDATION.md row 4b-02-03: nor/abn partition non-empty for both subsets
# ==================================================================
def test_nor_abn_partition_nonempty(synthetic_i3d_features):
    """nor_loader yields only label=0 batches; abn_loader yields only label=1 batches."""
    cfg = _build_cfg(synthetic_i3d_features, batch_size=1, T=32)
    (nor_loader, abn_loader), _ = build_dataloaders_i3d(cfg)

    nor_batch = next(iter(nor_loader))
    assert (nor_batch["label"] == 0.0).all(), (
        f"nor_loader yielded non-zero labels: {nor_batch['label']}"
    )

    abn_batch = next(iter(abn_loader))
    assert (abn_batch["label"] == 1.0).all(), (
        f"abn_loader yielded non-one labels: {abn_batch['label']}"
    )
