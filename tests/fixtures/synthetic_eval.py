"""Synthetic UCF + I3D eval fixtures (Phase 4 Wave 0, Plan 04-01 Task 1).

Two deterministic factory functions consumed by Wave 2+ test plans:

  - make_synthetic_ucf(tmp_path): 10-video UCF-shaped fixture (skeleton [N, 256]
    + CLIP [N, 1024] npys + split file + ucf_temporal.txt row for each).
  - make_synthetic_i3d(tmp_path):  5-crop I3D cache shaped like XD-Violence
    (train + test splits in separate subdirs; RTFM's 5-crop layout per D-19/D-20).

Both factories use np.random.default_rng(seed) so runs are reproducible.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


def make_synthetic_ucf(tmp_path: Path, n_videos: int = 10, seed: int = 0) -> dict:
    """Build a 10-video UCF-shaped test fixture under tmp_path.

    Layout produced:
      tmp_path/features/skeleton/<vid>.npy   # [N, 256] float32
      tmp_path/features/clip/<vid>.npy        # [N, 1024] float32
      tmp_path/splits/ucf_test.txt            # list of video IDs
      tmp_path/annotations/ucf_temporal.txt   # Sultani-format rows

    Returns dict(root=tmp_path, skel_dir=..., clip_dir=...,
                 split_file=..., anno_path=..., video_ids=[...]).
    """
    rng = np.random.default_rng(seed)
    root = Path(tmp_path)
    skel_dir = root / "features" / "skeleton"
    skel_dir.mkdir(parents=True)
    clip_dir = root / "features" / "clip"
    clip_dir.mkdir(parents=True)
    splits = root / "splits"
    splits.mkdir()
    anno_dir = root / "annotations"
    anno_dir.mkdir()

    # 5 normal + 5 anomaly, varied snippet counts in [4, 12].
    # NOTE: ALL video IDs are SYNTHETIC (Synth*) and MUST NOT match real UCF
    # video IDs. evaluate.py's M3 full-length fallback keys off the video ID
    # against data/ucf_total_frames.json; real IDs (e.g. "Abuse028",
    # "Normal_Videos_003") hijack n_frames from the manifest and break the
    # synthetic snippet->frame grid (regression introduced by commit 4ddda56).
    # Category comes from the annotation column below, not the ID, so the rename
    # is label-safe.
    specs = [
        ("SynthNormal001", "Normal", -1, -1, -1, -1),
        ("SynthNormal002", "Normal", -1, -1, -1, -1),
        ("SynthNormal003", "Normal", -1, -1, -1, -1),
        ("SynthNormal004", "Normal", -1, -1, -1, -1),
        ("SynthNormal005", "Normal", -1, -1, -1, -1),
        ("SynthAbuse900", "Abuse", 165, 240, -1, -1),
        ("SynthArson901", "Arson", 150, 420, 680, 1267),
        ("SynthFighting902", "Fighting", 80, 160, -1, -1),
        ("SynthAssault903", "Assault", 100, 250, -1, -1),
        ("SynthShooting904", "Shooting", 200, 340, -1, -1),
    ]
    vids = []
    anno_lines = []
    for vid, cat, s1, e1, s2, e2 in specs[:n_videos]:
        N = int(4 + rng.integers(0, 9))  # 4..12
        skel = rng.standard_normal((N, 256), dtype=np.float32)
        clip = rng.standard_normal((N, 1024), dtype=np.float32)
        np.save(skel_dir / f"{vid}.npy", skel)
        np.save(clip_dir / f"{vid}.npy", clip)
        vids.append(vid)
        anno_lines.append(f"{vid}_x264.mp4  {cat}  {s1}  {e1}  {s2}  {e2}")
    (splits / "ucf_test.txt").write_text("\n".join(vids) + "\n", encoding="utf-8")
    (anno_dir / "ucf_temporal.txt").write_text(
        "\n".join(anno_lines) + "\n", encoding="utf-8"
    )
    return {
        "root": root,
        "skel_dir": skel_dir,
        "clip_dir": clip_dir,
        "split_file": splits / "ucf_test.txt",
        "anno_path": anno_dir / "ucf_temporal.txt",
        "video_ids": vids,
    }


def make_synthetic_i3d(
    tmp_path: Path, n_train: int = 5, n_test: int = 3, seed: int = 0
) -> dict:
    """Build a synthetic 5-crop I3D cache (D-19, D-20).

    Layout:
      tmp_path/i3d/RGB/<vid>__<c>.npy       # 5 crops, [N, 1024] float32 each
      tmp_path/i3d/RGBTest/<vid>__<c>.npy
      tmp_path/splits/xd_train.txt, xd_test.txt
    """
    rng = np.random.default_rng(seed)
    root = Path(tmp_path) / "i3d"
    rgb = root / "RGB"
    rgb.mkdir(parents=True)
    rgbtest = root / "RGBTest"
    rgbtest.mkdir(parents=True)
    splits = Path(tmp_path) / "splits"
    splits.mkdir(exist_ok=True)

    train_ids = []
    for i in range(n_train):
        # Alternate between normal (_label_A) and anomalous (_label_B1)
        vid = f"v{i:03d}_label_A" if i % 2 == 0 else f"v{i:03d}_label_B1-0-0"
        train_ids.append(vid)
        N = int(20 + rng.integers(0, 11))
        for c in range(5):
            feat = rng.standard_normal((N, 1024)).astype(np.float32)
            np.save(rgb / f"{vid}__{c}.npy", feat)

    test_ids = []
    for i in range(n_test):
        vid = f"t{i:03d}_label_B2-0-0"
        test_ids.append(vid)
        N = int(20 + rng.integers(0, 11))
        for c in range(5):
            feat = rng.standard_normal((N, 1024)).astype(np.float32)
            np.save(rgbtest / f"{vid}__{c}.npy", feat)

    (splits / "xd_train.txt").write_text(
        "\n".join(train_ids) + "\n", encoding="utf-8"
    )
    (splits / "xd_test.txt").write_text(
        "\n".join(test_ids) + "\n", encoding="utf-8"
    )
    return {
        "root": root,
        "rgb": rgb,
        "rgbtest": rgbtest,
        "train_ids": train_ids,
        "test_ids": test_ids,
        "train_split": splits / "xd_train.txt",
        "test_split": splits / "xd_test.txt",
    }
