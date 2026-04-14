"""MOD-02: MILFeatureDataset + paired DataLoaders (D-04, D-09, D-10, D-12).

Tests use synthetic .npy caches written to tmp_feature_dir. No E:/ mount
required. Synthetic fixtures come from tests/fixtures/synthetic.py (Plan 01).
"""
from __future__ import annotations

import numpy as np
import pytest
import torch

# Created in Task 2 of this plan
from src.data.dataset import MILFeatureDataset
from src.data.loaders import build_dataloaders


def _write_video(dir_skel, dir_clip, video_id: str, N: int, seed: int = 0):
    """Write a synthetic [N, 256] skeleton and [N, 1024] CLIP .npy for tests."""
    rng = np.random.default_rng(seed)
    np.save(dir_skel / f"{video_id}.npy",
            rng.standard_normal((N, 256), dtype=np.float32))
    np.save(dir_clip / f"{video_id}.npy",
            rng.standard_normal((N, 1024), dtype=np.float32))


def _write_split(path, video_ids):
    path.write_text("\n".join(video_ids) + "\n")


# ---- D-09 / D-10 sampling ----

def test_train_resample_long(tmp_feature_dir, tmp_path):
    """D-09: N > T → 32-segment uniform sub-sample."""
    split = tmp_path / "split.txt"
    _write_split(split, ["Fighting001_x264"])
    _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                 "Fighting001_x264", N=100)
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="ucf",
    )
    item = ds[0]
    assert item["skel"].shape == (32, 256)
    assert item["clip"].shape == (32, 1024)
    assert item["mask"].shape == (32,)
    assert (item["mask"] == 1.0).all(), "no padding expected for long video"


def test_train_pad_short(tmp_feature_dir, tmp_path):
    """D-10 (revised): N < T → sample-with-replacement, mask all-ones.

    Original D-10 (zero-pad + mask) was NaN-unsafe with D-01 top-k=3 when
    N<k: masked-fill to -inf propagated through the paired hinge as NaN.
    Revised D-10 follows RTFM/VadCLIP sample-with-replacement: every
    snippet in the bag is a real observation copied from the source cache,
    so mask is all-ones and top-k is always well-defined.
    """
    split = tmp_path / "split.txt"
    _write_split(split, ["Abuse001_x264"])
    _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                 "Abuse001_x264", N=10)
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="ucf",
    )
    item = ds[0]
    assert item["skel"].shape == (32, 256)
    assert item["clip"].shape == (32, 1024)
    # Revised D-10: mask is all-ones — every row is a real observation (possibly repeated)
    assert (item["mask"] == 1.0).all()
    # Every sampled row must match one of the 10 source rows (sample-with-replacement)
    src_skel = np.load(tmp_feature_dir / "skeleton" / "Abuse001_x264.npy")
    for i in range(32):
        row = item["skel"][i].numpy()
        assert any(np.allclose(row, src_skel[j]) for j in range(10)), (
            f"row {i} does not match any source row — sample-with-replacement broken"
        )


def test_skip_empty_videos(tmp_feature_dir, tmp_path):
    """D-10 / Phase 2 UAT: videos with N=0 snippets are skipped at load time."""
    split = tmp_path / "split.txt"
    _write_split(split, ["Good_x264", "Empty_x264", "Another_x264"])
    _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                 "Good_x264", N=50)
    # Empty video: zero-row .npy (matches Phase 2 output for sub-64-frame videos)
    np.save(tmp_feature_dir / "skeleton" / "Empty_x264.npy",
            np.zeros((0, 256), dtype=np.float32))
    np.save(tmp_feature_dir / "clip" / "Empty_x264.npy",
            np.zeros((0, 1024), dtype=np.float32))
    _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                 "Another_x264", N=20)
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="ucf",
    )
    assert len(ds) == 2, f"expected 2 videos (Empty skipped), got {len(ds)}"
    ids = {ds[i]["video_id"] for i in range(len(ds))}
    assert "Empty_x264" not in ids


# ---- Label parsing ----

def test_label_parsing_ucf(tmp_feature_dir, tmp_path):
    """UCF label: Normal_Videos* → 0; everything else → 1.

    Covers both the plan test fixtures (Normal_Videos_event_*) AND the real
    Phase 2 split format (Normal_Videos001, etc.).
    """
    split = tmp_path / "split.txt"
    vids = [
        "Normal_Videos_event_123_x264",
        "Normal_Videos001",
        "Abuse001_x264",
        "Fighting042_x264",
    ]
    _write_split(split, vids)
    for v in vids:
        _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                     v, N=40)
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="ucf",
    )
    labels = {ds[i]["video_id"]: ds[i]["label"] for i in range(len(ds))}
    assert labels["Normal_Videos_event_123_x264"] == 0.0
    assert labels["Normal_Videos001"] == 0.0
    assert labels["Abuse001_x264"] == 1.0
    assert labels["Fighting042_x264"] == 1.0


def test_label_parsing_xd(tmp_feature_dir, tmp_path):
    """XD label: _label_A → 0; any other label suffix → 1."""
    split = tmp_path / "split.txt"
    vids = [
        "A.Movie.1999__00-01-00_00-02-00_label_A",
        "Fight_scene__00-10-20_00-11-05_label_B1",
        "Riot__00-30-00_00-31-00_label_G",
    ]
    _write_split(split, vids)
    for v in vids:
        _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                     v, N=40)
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="xd",
    )
    labels = {ds[i]["video_id"]: ds[i]["label"] for i in range(len(ds))}
    assert labels["A.Movie.1999__00-01-00_00-02-00_label_A"] == 0.0
    assert labels["Fight_scene__00-10-20_00-11-05_label_B1"] == 1.0
    assert labels["Riot__00-30-00_00-31-00_label_G"] == 1.0


# ---- Alignment assertion (Phase 2 DATA-08 invariant) ----

def test_alignment_assertion_on_mismatch(tmp_feature_dir, tmp_path):
    """Skeleton and CLIP snippet counts must match per video (DATA-08)."""
    split = tmp_path / "split.txt"
    _write_split(split, ["BadAligned_x264"])
    # Write mismatched shapes: skel N=20, clip N=19
    rng = np.random.default_rng(0)
    np.save(tmp_feature_dir / "skeleton" / "BadAligned_x264.npy",
            rng.standard_normal((20, 256), dtype=np.float32))
    np.save(tmp_feature_dir / "clip" / "BadAligned_x264.npy",
            rng.standard_normal((19, 1024), dtype=np.float32))
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="ucf",
    )
    with pytest.raises(AssertionError) as exc:
        _ = ds[0]
    assert "BadAligned_x264" in str(exc.value)


# ---- D-12 test mode ----

def test_test_mode_returns_full_length(tmp_feature_dir, tmp_path):
    """D-12: test-mode scores every snippet; no T=32 sub-sampling."""
    split = tmp_path / "split.txt"
    _write_split(split, ["Long_x264"])
    _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                 "Long_x264", N=100)
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="test", seed=42, dataset="ucf",
    )
    item = ds[0]
    assert item["skel"].shape == (100, 256)
    assert item["clip"].shape == (100, 1024)
    assert item["mask"].shape == (100,)
    assert (item["mask"] == 1.0).all()


def test_deterministic_sampling(tmp_feature_dir, tmp_path):
    """Same seed + same video → same sampled indices (TRN-03 compatibility).

    The random-within-segment pick must be reproducible so that
    Plan 06's bit-identical rerun test can trust the DataLoader output.
    """
    split = tmp_path / "split.txt"
    _write_split(split, ["Repeat_x264"])
    _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                 "Repeat_x264", N=64, seed=7)
    ds1 = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="ucf",
    )
    ds2 = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", seed=42, dataset="ucf",
    )
    # Force RNG reset before each call (match the contract in dataset.py
    # where __getitem__ uses a per-call deterministic source)
    import random
    random.seed(99); np.random.seed(99); torch.manual_seed(99)
    a = ds1[0]
    random.seed(99); np.random.seed(99); torch.manual_seed(99)
    b = ds2[0]
    assert torch.allclose(a["skel"], b["skel"])
    assert torch.allclose(a["clip"], b["clip"])


# ---- D-04 paired DataLoader ----

def test_paired_loader(tmp_feature_dir, tmp_path, smoke_cfg):
    """D-04: build_dataloaders yields paired (nor, abn) + val DataLoaders.

    nor_loader step: 16 normal videos (label=0).
    abn_loader step: 16 abnormal videos (label=1).
    val_loader: MILFeatureDataset on the val split (still bag-pair semantics).
    """
    # Create 20 normal + 20 abnormal train videos + 8 of each for val
    splits_dir = tmp_path / "splits"; splits_dir.mkdir()
    train_ids = (
        [f"Normal_Videos_event_{i}_x264" for i in range(20)]
        + [f"Abuse{i:03d}_x264" for i in range(20)]
    )
    val_ids = (
        [f"Normal_Videos_event_v{i}_x264" for i in range(8)]
        + [f"Assault{i:03d}_x264" for i in range(8)]
    )
    (splits_dir / "ucf_train.txt").write_text("\n".join(train_ids) + "\n")
    (splits_dir / "ucf_val.txt").write_text("\n".join(val_ids) + "\n")

    for v in train_ids + val_ids:
        _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                     v, N=40)

    # Adapt smoke_cfg to point at tmp_feature_dir
    smoke_cfg["paths"]["skeleton_features"] = str(tmp_feature_dir / "skeleton")
    smoke_cfg["paths"]["clip_features"] = str(tmp_feature_dir / "clip")
    smoke_cfg["paths"]["splits_dir"] = str(splits_dir)
    smoke_cfg["dataset"] = "ucf"
    smoke_cfg["data"]["batch_size"] = 16
    smoke_cfg["data"]["num_workers"] = 0

    (nor_loader, abn_loader), val_loader = build_dataloaders(smoke_cfg)

    nor_batch = next(iter(nor_loader))
    abn_batch = next(iter(abn_loader))
    assert nor_batch["skel"].shape == (16, 32, 256)
    assert abn_batch["skel"].shape == (16, 32, 256)
    assert nor_batch["clip"].shape == (16, 32, 1024)
    assert abn_batch["clip"].shape == (16, 32, 1024)
    assert (nor_batch["label"] == 0).all()
    assert (abn_batch["label"] == 1).all()

    # val_loader is iterable and non-empty
    assert len(val_loader) > 0


def test_drop_last_prevents_partial_batch(tmp_feature_dir, tmp_path, smoke_cfg):
    """drop_last=True on train loaders — partial batches are discarded to keep
    the 16+16 pair contract clean for the MIL hinge."""
    splits_dir = tmp_path / "splits"; splits_dir.mkdir()
    # Only 18 normals and 18 abnormals → with batch_size=16 and drop_last,
    # each loader yields exactly 1 batch (not 2).
    train_ids = (
        [f"Normal_Videos_event_{i}_x264" for i in range(18)]
        + [f"Abuse{i:03d}_x264" for i in range(18)]
    )
    val_ids = [f"Normal_Videos_event_v{i}_x264" for i in range(4)] + [f"Assault{i:03d}_x264" for i in range(4)]
    (splits_dir / "ucf_train.txt").write_text("\n".join(train_ids) + "\n")
    (splits_dir / "ucf_val.txt").write_text("\n".join(val_ids) + "\n")
    for v in train_ids + val_ids:
        _write_video(tmp_feature_dir / "skeleton", tmp_feature_dir / "clip",
                     v, N=40)

    smoke_cfg["paths"]["skeleton_features"] = str(tmp_feature_dir / "skeleton")
    smoke_cfg["paths"]["clip_features"] = str(tmp_feature_dir / "clip")
    smoke_cfg["paths"]["splits_dir"] = str(splits_dir)
    smoke_cfg["dataset"] = "ucf"
    smoke_cfg["data"]["batch_size"] = 16
    smoke_cfg["data"]["num_workers"] = 0

    (nor_loader, abn_loader), _ = build_dataloaders(smoke_cfg)
    assert len(nor_loader) == 1  # 18 videos, drop_last=True → floor(18/16)=1
    assert len(abn_loader) == 1
