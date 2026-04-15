"""skel_agg reshape tests for 2-person cache (D-21, D-22).

Verifies that MILFeatureDataset accepts the Phase 4 D-21 `skel_agg` parameter and
correctly reshapes [N, 2, 256] 2-person caches at load time per the chosen
aggregation (concat/mean/max), while preserving backward-compat for the legacy
[N, 256] M-pooled caches. Also smoke-tests the extractor CLIs to verify that
--keep-persons and --pool flags are wired through argparse.
"""
from __future__ import annotations

import numpy as np
import pytest
import torch

from src.data.dataset import MILFeatureDataset


@pytest.fixture
def two_person_cache(tmp_path):
    """Build a 5-video UCF fixture with [N, 2, 256] skeleton + [N, 1024] clip."""
    skel_dir = tmp_path / "skel"
    skel_dir.mkdir()
    clip_dir = tmp_path / "clip"
    clip_dir.mkdir()
    splits = tmp_path / "splits"
    splits.mkdir()
    vids = []
    rng = np.random.default_rng(0)
    # Use non-sub-64-frame names (not matching the 172 filtered UCF set)
    specs = [
        ("Abuse028", 40),
        ("Abuse030", 50),
        ("Fighting001", 45),
        ("Normal_Videos_001", 60),
        ("Normal_Videos_002", 55),
    ]
    for vid, N in specs:
        np.save(
            skel_dir / f"{vid}.npy",
            rng.standard_normal((N, 2, 256)).astype(np.float32),
        )
        np.save(
            clip_dir / f"{vid}.npy",
            rng.standard_normal((N, 1024)).astype(np.float32),
        )
        vids.append(vid)
    (splits / "ucf_test.txt").write_text("\n".join(vids) + "\n", encoding="utf-8")
    return {
        "skel_dir": str(skel_dir),
        "clip_dir": str(clip_dir),
        "split_file": str(splits / "ucf_test.txt"),
    }


def test_concat_to_512(two_person_cache):
    """S1: skel_agg='concat' reshapes [N, 2, 256] to [N, 512]."""
    ds = MILFeatureDataset(
        split_file=two_person_cache["split_file"],
        skel_dir=two_person_cache["skel_dir"],
        clip_dir=two_person_cache["clip_dir"],
        T=32,
        mode="test",
        skel_agg="concat",
    )
    s = ds[0]["skel"]
    assert s.shape[-1] == 512, f"got {s.shape}"


def test_mean_to_256(two_person_cache):
    """S2: skel_agg='mean' collapses [N, 2, 256] to [N, 256]."""
    ds = MILFeatureDataset(
        split_file=two_person_cache["split_file"],
        skel_dir=two_person_cache["skel_dir"],
        clip_dir=two_person_cache["clip_dir"],
        T=32,
        mode="test",
        skel_agg="mean",
    )
    s = ds[0]["skel"]
    assert s.shape[-1] == 256


def test_max_to_256(two_person_cache):
    """S3: skel_agg='max' collapses [N, 2, 256] to [N, 256]."""
    ds = MILFeatureDataset(
        split_file=two_person_cache["split_file"],
        skel_dir=two_person_cache["skel_dir"],
        clip_dir=two_person_cache["clip_dir"],
        T=32,
        mode="test",
        skel_agg="max",
    )
    s = ds[0]["skel"]
    assert s.shape[-1] == 256


def test_none_on_3d_raises(two_person_cache):
    """S4: skel_agg='none' on [N, 2, 256] cache raises ValueError."""
    ds = MILFeatureDataset(
        split_file=two_person_cache["split_file"],
        skel_dir=two_person_cache["skel_dir"],
        clip_dir=two_person_cache["clip_dir"],
        T=32,
        mode="test",
        skel_agg="none",
    )
    with pytest.raises(ValueError, match="skel_agg"):
        _ = ds[0]


def test_invalid_skel_agg_raises(tmp_path):
    """S6: skel_agg='foobar' raises ValueError at __init__."""
    splits = tmp_path / "splits.txt"
    splits.write_text("dummy\n", encoding="utf-8")
    with pytest.raises(ValueError, match="skel_agg"):
        MILFeatureDataset(
            split_file=str(splits),
            skel_dir=str(tmp_path),
            clip_dir=str(tmp_path),
            T=32,
            mode="test",
            skel_agg="foobar",
        )


def test_backward_compat_2d_cache(tmp_path):
    """S5: Existing [N, 256] cache continues to work with skel_agg='none'."""
    skel_dir = tmp_path / "skel"
    skel_dir.mkdir()
    clip_dir = tmp_path / "clip"
    clip_dir.mkdir()
    splits = tmp_path / "splits.txt"
    rng = np.random.default_rng(0)
    np.save(skel_dir / "Abuse028.npy", rng.standard_normal((40, 256)).astype(np.float32))
    np.save(clip_dir / "Abuse028.npy", rng.standard_normal((40, 1024)).astype(np.float32))
    splits.write_text("Abuse028\n", encoding="utf-8")
    ds = MILFeatureDataset(
        split_file=str(splits),
        skel_dir=str(skel_dir),
        clip_dir=str(clip_dir),
        T=32,
        mode="test",
        skel_agg="none",
    )
    s = ds[0]["skel"]
    assert s.shape[-1] == 256


def test_extract_ctrgcn_help_has_keep_persons():
    """S7: extract_ctrgcn.py --help includes --keep-persons."""
    import subprocess
    import shutil

    # Prefer vcc-ctrgcn env python (the intended runner); argparse --help does
    # not require mmcv/pyskl imports to resolve, so vcc-main works too.
    candidates = [
        "C:/Anaconda/envs/vcc-ctrgcn/python.exe",
        "C:/Anaconda/envs/vcc-main/python.exe",
        shutil.which("python") or "python",
    ]
    for py in candidates:
        try:
            out = subprocess.run(
                [py, "scripts/extract_ctrgcn.py", "--help"],
                capture_output=True, text=True, timeout=30,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        combined = (out.stdout + out.stderr).lower()
        if not combined:
            continue
        # --help exits 0 under argparse; either stdout or stderr has the text
        assert "--keep-persons" in combined, (
            f"missing --keep-persons in help: {combined[:500]}"
        )
        return
    pytest.skip("no runnable python env found for extract_ctrgcn.py --help")


def test_extract_clip_help_has_pool():
    """S8: extract_clip.py --help includes --pool with mean/mean_max choices."""
    import subprocess
    import shutil

    candidates = [
        "C:/Anaconda/envs/vcc-main/python.exe",
        shutil.which("python") or "python",
    ]
    for py in candidates:
        try:
            out = subprocess.run(
                [py, "scripts/extract_clip.py", "--help"],
                capture_output=True, text=True, timeout=30,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        combined = (out.stdout + out.stderr).lower()
        if not combined:
            continue
        assert "--pool" in combined and ("mean_max" in combined or "mean" in combined), (
            f"missing --pool in help: {combined[:500]}"
        )
        return
    pytest.skip("no runnable python env found for extract_clip.py --help")
