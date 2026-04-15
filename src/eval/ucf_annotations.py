"""Parse Temporal_Anomaly_Annotation.txt per Sultani 2018 convention (D-16, D-17).

File format (whitespace-separated, 6 columns):

    Abuse028_x264.mp4             Abuse   165   240   -1    -1
    Arson011_x264.mp4             Arson   150   420   680   1267
    Normal_Videos_003_x264.mp4    Normal  -1    -1    -1    -1

Columns:
    0: video filename (with _x264.mp4 suffix; stripped to match split file IDs)
    1: category (Abuse, Arrest, ..., Normal)
    2,3: start1, end1 (frame indices in original 30fps video; -1 -> None if N/A)
    4,5: start2, end2 (second anomaly interval; -1 -1 if single or normal)

D-16: per-frame label = union [start1, end1] u [start2, end2]. -1 -1 = all zero.
D-17: category column is the authoritative label (NOT regex-parsed from filename).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


Interval = Tuple[int | None, int | None]


@dataclass(frozen=True)
class VideoAnnotation:
    """Immutable Sultani-row holder keyed by video_id (no filename suffix)."""

    video_id: str  # without _x264.mp4 suffix; matches split file IDs
    category: str  # e.g. "Abuse", "Fighting", "Normal"
    intervals: Tuple[Interval, Interval]  # ((s1, e1), (s2, e2)); -1 encoded as None

    @property
    def is_normal(self) -> bool:
        """True when all four interval endpoints are None (every -1)."""
        return all(s is None for s, _ in self.intervals)


def parse_annotations(path: Path) -> Dict[str, VideoAnnotation]:
    """Return {video_id_without_suffix: VideoAnnotation}.

    Raises:
      ValueError: if any non-blank line does not split into exactly 6 columns.
    """
    annos: Dict[str, VideoAnnotation] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()  # whitespace-split handles 1- or 2-space delimiters
            if len(parts) != 6:
                raise ValueError(
                    f"Expected 6 columns, got {len(parts)} in line: {line!r}"
                )
            fname, category, s1, e1, s2, e2 = parts
            # Strip _x264.mp4 (or just .mp4) to match data/splits/ucf_*.txt IDs
            vid = fname.replace("_x264.mp4", "").replace(".mp4", "")

            def _v(s: str) -> int | None:
                return None if int(s) == -1 else int(s)

            anno = VideoAnnotation(
                video_id=vid,
                category=category,
                intervals=((_v(s1), _v(e1)), (_v(s2), _v(e2))),
            )
            annos[vid] = anno
    return annos


def frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray:
    """Build [n_frames] binary label vector from annotation intervals (D-16).

    Per-frame label = union of both intervals. Endpoints are clamped to
    [0, n_frames] so annotations that extend past the decoded video length
    (e.g., frame_labels(Abuse028, n_frames=100) when Abuse028's end is 240)
    are safe — no out-of-bounds indexing.
    """
    labels = np.zeros(n_frames, dtype=np.int64)
    for (s, e) in anno.intervals:
        if s is None:
            continue
        s = max(0, int(s))
        e = min(n_frames, int(e))
        if e > s:
            labels[s:e] = 1
    return labels
