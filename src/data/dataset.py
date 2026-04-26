"""MIL Feature Dataset (MOD-02).

Reads Phase 2 cached features from ``{skel_dir,clip_dir}/<video_id>.npy``
and yields bag-level training items with three sampling modes:

  mode='train': D-09 (32-segment uniform sub-sample) or D-10 (zero-pad+mask)
  mode='val':   same as train — validation uses MIL loss on paired bags
  mode='test':  D-12 — return all snippets in temporal order, no sampling

Skip at load time (D-10 + Phase 2 UAT note):
  - Videos with 0 snippets (172 UCF sub-64-frame videos) are filtered from the
    split at construction so they never reach ``__getitem__``.

Label parsing:
  - UCF-Crime: ``Normal_Videos*`` → 0, everything else → 1. The prefix
    ``Normal_Videos`` covers both the real Phase 2 split format
    (``Normal_Videos001``, ``Normal_Videos_event_123``) and the synthetic
    test fixtures used in Plan 03 (``Normal_Videos_event_*_x264``).
  - XD-Violence: filename ending in ``_label_A`` (optionally followed by
    ``.mp4``) → 0, any other label suffix (``_label_B1``, ``_label_G``,
    ``_label_R``, ``_label_B2-B6-0``, etc.) → 1. Phase 2 convention.

Alignment invariant (DATA-08):
  - ``__getitem__`` asserts ``skel.shape[0] == clip.shape[0]`` and embeds the
    ``video_id`` in the error message so a misaligned cache is immediately
    traceable to the offending video.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import torch
from torch.utils.data import Dataset


def _parse_label_ucf(video_id: str) -> int:
    """UCF-Crime: ``Normal_Videos*`` = 0, everything else = 1.

    Real Phase 2 UCF split ids look like ``Normal_Videos001``,
    ``Normal_Videos_event_123_x264``, ``Abuse001``, ``Fighting042``.
    The common normal prefix is ``Normal_Videos``.
    """
    return 0 if video_id.startswith("Normal_Videos") else 1


def _parse_label_xd(video_id: str) -> int:
    """XD-Violence: ``_label_A`` (optionally with ``.mp4`` extension) = 0,
    any other label suffix = 1.

    XD filenames carry both timestamps and labels:
      ``A.Beautiful.Mind.2001__#00-01-45_00-02-50_label_A``  → 0 (normal)
      ``wangted.2008__#01-32-25_01-33-30_label_B1-B2-0``     → 1 (abnormal)
    """
    base = video_id[:-4] if video_id.endswith(".mp4") else video_id
    return 0 if base.endswith("_label_A") else 1


_LABEL_PARSERS = {
    "ucf": _parse_label_ucf,
    "xd": _parse_label_xd,
}


class MILFeatureDataset(Dataset):
    """PyTorch Dataset backed by per-video .npy feature caches.

    Parameters
    ----------
    split_file:
        Text file listing one video id per line (Phase 2 ``data/splits/*.txt``).
    skel_dir:
        Directory containing ``<video_id>.npy`` float32 ``[N, 256]`` skeleton
        features.
    clip_dir:
        Directory containing ``<video_id>.npy`` float32 ``[N, 1024]`` CLIP
        features, produced by Phase 2 at mean+max pooling.
    T:
        Target snippet count per bag in ``train``/``val`` modes (D-09/D-10).
        Default 32 per PRD §11.1.
    mode:
        ``"train"`` / ``"val"`` → apply D-09 segment sub-sample or D-10 pad.
        ``"test"`` → D-12, return all snippets in original order.
    seed:
        Retained for signature compatibility; segment-random pick uses the
        global numpy RNG so the caller can drive reproducibility explicitly.
    dataset:
        ``"ucf"`` or ``"xd"`` — selects the label-parsing function.

    Item schema
    -----------
    ``__getitem__`` returns::

        {
            "skel": torch.float32 [T, 256] (or [N, 256] in test mode),
            "clip": torch.float32 [T, 1024] (or [N, 1024] in test mode),
            "mask": torch.float32 [T] (or [N])  — 1.0 real, 0.0 padded,
            "label": float 0.0 (normal) or 1.0 (abnormal),
            "video_id": str,
        }
    """

    def __init__(
        self,
        split_file: str,
        skel_dir: str,
        clip_dir: str,
        T: int = 32,
        mode: str = "train",
        seed: int = 42,
        dataset: str = "ucf",
        skel_agg: str = "none",
    ) -> None:
        if mode not in ("train", "val", "test"):
            raise ValueError(f"mode must be train|val|test, got {mode!r}")
        if dataset not in _LABEL_PARSERS:
            raise ValueError(f"dataset must be ucf|xd, got {dataset!r}")
        # Phase 4 D-21: skel_agg selects how a 3D [N, 2, 256] 2-person cache
        # collapses to [N, 256] or [N, 512] at load time. 'none' is the default
        # and is REQUIRED when the cache is already 2D ([N, 256] M-pool).
        if skel_agg not in ("none", "concat", "max", "mean"):
            raise ValueError(
                f"skel_agg must be none|concat|max|mean, got {skel_agg!r}"
            )

        self.skel_dir = Path(skel_dir)
        self.clip_dir = Path(clip_dir)
        self.T = T
        self.mode = mode
        self.seed = seed
        self.dataset = dataset
        self.skel_agg = skel_agg
        self._label_fn = _LABEL_PARSERS[dataset]

        # Load split + filter out missing / zero-snippet videos (D-10).
        all_ids = self._load_split(split_file)
        self.video_ids: List[str] = [vid for vid in all_ids if self._is_loadable(vid)]
        self.labels = {vid: float(self._label_fn(vid)) for vid in self.video_ids}

    # ---- internals ----

    @staticmethod
    def _load_split(path: str) -> List[str]:
        with open(path, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
            ]

    def _is_loadable(self, vid: str) -> bool:
        """A video is loadable iff both .npy files exist AND ``N >= 1``.

        Uses ``mmap_mode='r'`` so we peek at the header without copying the
        full array — important for O(N) startup cost on 3000+ video splits.
        """
        skel_p = self.skel_dir / f"{vid}.npy"
        clip_p = self.clip_dir / f"{vid}.npy"
        if not skel_p.exists() or not clip_p.exists():
            return False
        try:
            skel = np.load(skel_p, mmap_mode="r")
        except Exception:
            return False
        if skel.shape[0] == 0:
            return False
        return True

    def __len__(self) -> int:
        return len(self.video_ids)

    def __getitem__(self, idx: int) -> dict:
        vid = self.video_ids[idx]
        label = self.labels[vid]
        skel = np.load(self.skel_dir / f"{vid}.npy")
        clip = np.load(self.clip_dir / f"{vid}.npy")
        # Phase 4 D-21: aggregate 2-person cache to 2D at load time.
        # The cache produced by scripts/extract_ctrgcn.py --keep-persons is
        # [N, 2, 256]; the loader contract downstream consumes [N, D].
        if skel.ndim == 3 and skel.shape[1] == 2:
            if self.skel_agg == "concat":
                skel = skel.reshape(skel.shape[0], -1)  # [N, 512]
            elif self.skel_agg == "max":
                skel = skel.max(axis=1)                 # [N, 256]
            elif self.skel_agg == "mean":
                skel = skel.mean(axis=1)                # [N, 256]
            else:
                raise ValueError(
                    f"2-person cache at shape {skel.shape} requires "
                    f"cfg.data.skel_agg (got {self.skel_agg!r}) for video {vid}"
                )
        assert skel.shape[0] == clip.shape[0], (
            f"Alignment mismatch for {vid}: skel N={skel.shape[0]} "
            f"vs clip N={clip.shape[0]} (DATA-08 must have caught this)"
        )
        N = skel.shape[0]

        if self.mode == "test":
            # D-12: return all snippets, no sampling
            skel_t = torch.from_numpy(skel.astype(np.float32))
            clip_t = torch.from_numpy(clip.astype(np.float32))
            mask = torch.ones(N, dtype=torch.float32)
        else:
            # train / val: D-09 segment sample or D-10 pad
            skel_t, clip_t, mask = self._sample_or_pad(skel, clip, N)

        return {
            "skel": skel_t,
            "clip": clip_t,
            "mask": mask,
            "label": float(label),
            "video_id": vid,
        }

    def _sample_or_pad(self, skel: np.ndarray, clip: np.ndarray, N: int):
        """D-09: uniform 32-segment sub-sample; D-10 (revised): sample-with-replacement.

        D-09 math (N >= T):
          1. Partition [0, N] into T equal segments via
             ``np.linspace(0, N, T + 1, dtype=np.int64)``.
          2. Pick one index per segment uniformly at random.
          3. The ``max(lo+1, hi)`` guard handles degenerate segments where
             integer rounding collapses ``hi == lo``.

        D-10 (revised) math (N < T):
          1. Sample T indices in [0, N) with replacement, then sort.
             Matches RTFM/VadCLIP reference behavior: repeat-sampling
             upsamples short videos to T valid snippets instead of
             zero-padding. Every snippet is a real observation.
          2. Mask is all-ones — MIL top-k is well-defined for all bags.

        Original D-10 (zero-pad + mask) was incompatible with D-01 top-k=3
        for videos with N<k: masked positions became ``-inf`` and the
        paired hinge evaluated to NaN. UCF has ~41% of videos with N<3,
        which produced NaN loss from epoch 0. Reverted to RTFM's
        sample-with-replacement pattern; see commit history for context.
        """
        T = self.T
        if N >= T:
            # D-09: divide N into T contiguous segments, pick one random index per segment
            segs = np.linspace(0, N, T + 1, dtype=np.int64)
            idxs = np.zeros(T, dtype=np.int64)
            for i in range(T):
                lo, hi = int(segs[i]), max(int(segs[i]) + 1, int(segs[i + 1]))
                idxs[i] = np.random.randint(lo, hi)
        else:
            # D-10 (revised): sample T indices with replacement from [0, N), sorted
            idxs = np.sort(np.random.randint(0, N, size=T).astype(np.int64))
        skel_t = torch.from_numpy(skel[idxs].astype(np.float32))
        clip_t = torch.from_numpy(clip[idxs].astype(np.float32))
        mask = torch.ones(T, dtype=torch.float32)
        return skel_t, clip_t, mask
