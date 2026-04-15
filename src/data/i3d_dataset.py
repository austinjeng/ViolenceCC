"""I3D 5-crop dataset for rtfm_i3d variant (Phase 4 D-19, D-20 + Pitfall 4).

Cache layout (verified RESEARCH.md 2026-04-15):
  {feature_dir}/<video_id>__<c>.npy for c in 0..4, shape [N_snippets, 1024] float32.
  Train+val live under E:/i3d-features/i3d-features/RGB/;
  test lives under E:/i3d-features/i3d-features/RGBTest/.
  Train: 3225 videos with features, 729 missing (all label_A per Pitfall 4).
  Test:  800/800 complete.

Training (D-19): each of 5 crops is a separate sample in the bag (5x signal).
Test    (D-19): crops averaged to [N, 1024] before a single forward pass.

Label parsing (same as src/data/dataset.py::_parse_label_xd but kept local
to avoid cross-module coupling between training path and the harness path):
  `label = 0 if vid.endswith("_label_A") else 1`.

Pitfall 4 mitigation:
  1. Construct-time filter drops videos missing crop 0 (cheap existence check
     parallel to MILFeatureDataset._is_loadable).
  2. Startup log: "[i3d_dataset] <mode>: <k>/<n> videos available ...".
  3. Warn on stderr if the filtered set has no abnormal OR no normal videos
     (MIL bag pairing requires both classes).

Security (Plan threat_model):
  T-04-03-01 Elevation of Privilege: np.load is called WITHOUT allow_pickle,
    refusing to deserialize Python objects from the .npy cache.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import numpy as np
import torch
from torch.utils.data import Dataset


class I3DFeatureDataset(Dataset):
    """XD I3D 5-crop features dataset (D-19, D-20)."""

    def __init__(
        self,
        split_file: str,
        feature_dir: str,
        mode: str = "train",
        T: int = 32,
        n_crops: int = 5,
    ):
        if mode not in ("train", "val", "test"):
            raise ValueError(f"mode must be train|val|test, got {mode!r}")
        self.feature_dir = Path(feature_dir)
        self.mode = mode
        self.T = T
        self.n_crops = n_crops

        all_ids = [
            i.strip()
            for i in Path(split_file).read_text(encoding="utf-8").splitlines()
            if i.strip()
        ]
        self.video_ids: List[str] = [
            vid for vid in all_ids if self._has_at_least_one_crop(vid)
        ]

        # D-19/Pitfall 4: report filtered count to stdout at construction time.
        print(
            f"[i3d_dataset] {mode}: {len(self.video_ids)}/{len(all_ids)} "
            f"videos available (feature_dir={self.feature_dir})",
            flush=True,
        )

        # Collapsed-ratio guard: MIL bag pairing requires both classes in train/val.
        if mode in ("train", "val") and len(self.video_ids) > 0:
            n_normal = sum(1 for v in self.video_ids if v.endswith("_label_A"))
            n_abnormal = len(self.video_ids) - n_normal
            if n_abnormal == 0:
                print(
                    "[i3d_dataset] WARNING: no abnormal videos after filtering; "
                    "normal/abnormal ratio collapsed -- MIL bag pairing will fail",
                    file=sys.stderr,
                    flush=True,
                )
            elif n_normal == 0:
                print(
                    "[i3d_dataset] WARNING: no normal videos after filtering; "
                    "normal/abnormal ratio collapsed -- MIL bag pairing will fail",
                    file=sys.stderr,
                    flush=True,
                )

    # ---------------------------------------------------------------- helpers

    def _has_at_least_one_crop(self, vid: str) -> bool:
        """A video is usable if at least crop 0 is on disk (D-19 pad from crop 0)."""
        return (self.feature_dir / f"{vid}__0.npy").exists()

    def _load_crops(self, vid: str) -> np.ndarray:
        """Return [n_crops, N_snippets, 1024]. Missing crops pad by duplicating crop 0.

        Pitfall 4 + D-19: at least one XD train video has only 4 crops on disk.
        Instead of skipping it, duplicate the existing crop 0 to fill to n_crops.
        """
        crops = []
        base = None
        for c in range(self.n_crops):
            p = self.feature_dir / f"{vid}__{c}.npy"
            if p.exists():
                arr = np.load(p)  # allow_pickle=False by default (T-04-03-01)
                crops.append(arr)
                if base is None:
                    base = arr
            elif base is not None:
                crops.append(base)
            else:
                # _has_at_least_one_crop is checked at __init__, so reaching
                # here means crop 0 vanished mid-run -- raise loudly.
                raise FileNotFoundError(
                    f"No crops found for {vid} in {self.feature_dir}"
                )
        return np.stack(crops, axis=0)

    def _resample_T(self, feat: np.ndarray) -> np.ndarray:
        """Uniform-segment sampling to T (RTFM process_feat equivalent)."""
        N = feat.shape[0]
        if N >= self.T:
            r = np.linspace(0, N, self.T + 1, dtype=np.int64)
            return np.stack(
                [
                    feat[r[i]: max(r[i] + 1, r[i + 1])].mean(axis=0)
                    for i in range(self.T)
                ]
            )
        # N < T: sample-with-replacement (matches RTFM upsampling behavior
        # documented in src/data/dataset.py D-10-revised comment).
        rng = np.random.default_rng(0)  # deterministic for reproducibility
        idxs = np.sort(rng.integers(0, N, size=self.T))
        return feat[idxs]

    # ---------------------------------------------------------------- Dataset

    def __len__(self) -> int:
        return len(self.video_ids)

    def __getitem__(self, idx: int) -> dict:
        vid = self.video_ids[idx]
        crops = self._load_crops(vid)  # [n_crops, N, 1024]
        label = 0 if vid.endswith("_label_A") else 1

        if self.mode == "test":
            # D-19: average crops -> [N, 1024] float32
            feats = crops.mean(axis=0).astype(np.float32)
            return {
                "i3d": torch.from_numpy(feats),
                "label": float(label),
                "video_id": vid,
            }

        # train / val: 5 crops as separate samples in the bag (D-19).
        resampled = np.stack(
            [self._resample_T(crops[c]) for c in range(self.n_crops)], axis=0
        ).astype(np.float32)
        return {
            "i3d": torch.from_numpy(resampled),  # [5, T, 1024]
            "label": float(label),
            "video_id": vid,
        }
