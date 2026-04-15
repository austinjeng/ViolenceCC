"""Wu et al. 2020 XD-Violence frame-level annotation parser (D-10).

Parallels src/eval/ucf_annotations.py but handles Wu's variable-interval format:
  <video_id>[.mp4] s1 e1 [s2 e2 [s3 e3 ...]]

Differences vs UCF format:
- Columns are 1 + 2*K for K >= 1 intervals (UCF is fixed 6)
- Video IDs may carry .mp4 suffix that must be stripped (UCF uses _x264.mp4)
- Normal test videos are OMITTED entirely from the annotations file (UCF encodes as -1,-1)
- Categories parsed from video_id _label_<code> suffix (UCF has a separate column)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

Interval = Tuple[int, int]


@dataclass(frozen=True)
class VideoAnnotation:
    """Immutable Wu 2020 row keyed by normalized video_id (no .mp4 suffix)."""

    video_id: str              # without trailing .mp4
    category: str              # parsed from _label_<code> suffix; "B1", "B2", "G", etc.
    intervals: Tuple[Interval, ...]  # variable-length; each (start, end) in original-video frame indices

    @property
    def is_normal(self) -> bool:
        """True when the annotation has no intervals. Parsed Wu entries always
        have intervals >= 1 (normals are omitted from the file), so for parsed
        entries this always returns False."""
        return len(self.intervals) == 0


def _parse_category(video_id: str) -> str:
    """Parse Wu category from video_id _label_<code> suffix.

    Suffix formats (verified from Wu file):
      _label_A             -> "Normal"
      _label_B1-0-0        -> "B1"
      _label_B6-0-0        -> "B6"
      _label_G-B2-B6       -> "G"   (first listed)
      _label_B2-G-0        -> "B2"

    Returns category code ("A", "B1"..."B6", "G", "M") or "Normal" for _label_A.
    Returns "Unknown" if the video_id has no _label_ marker.
    """
    if "_label_" not in video_id:
        return "Unknown"
    suffix = video_id.split("_label_", 1)[1]
    if suffix == "A":
        return "Normal"
    first = suffix.split("-", 1)[0]
    return first


def parse_xd_annotations(path: Path) -> Dict[str, VideoAnnotation]:
    """Parse Wu 2020 annotations.txt. Returns {video_id_normalized: VideoAnnotation}.

    Normalization: strip trailing '.mp4' from the first column so keys match
    the corresponding XD-Violence split file IDs (verified in RESEARCH.md Wu
    Annotation Format: 500/500 abnormal videos match after this step). The v=
    prefix on YouTube-sourced videos is preserved verbatim (split files also
    carry the v= prefix on those rows).

    Categories: parsed from the _label_<code> suffix via _parse_category().

    File omissions: Wu's annotations.txt contains ONLY the 500 abnormal test-set
    videos. The 300 normal videos have no entries; callers (e.g. downstream
    _build_frame_arrays) must guard with `if vid in annos` and default missing
    entries to zero labels.

    Raises:
        ValueError: if any non-blank line has an odd number of interval endpoints.
    """
    annos: Dict[str, VideoAnnotation] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                raise ValueError(
                    f"Wu annotation line {line_no} has {len(parts)} columns, expected >= 3: {line!r}"
                )
            vid_raw = parts[0]
            vid = vid_raw[:-4] if vid_raw.endswith(".mp4") else vid_raw
            ints_flat = [int(p) for p in parts[1:]]
            if len(ints_flat) % 2 != 0:
                raise ValueError(
                    f"Wu annotation line {line_no} has odd number of interval endpoints "
                    f"({len(ints_flat)}): {line!r}"
                )
            intervals = tuple(
                (ints_flat[i], ints_flat[i + 1])
                for i in range(0, len(ints_flat), 2)
            )
            category = _parse_category(vid)
            annos[vid] = VideoAnnotation(
                video_id=vid, category=category, intervals=intervals
            )
    return annos


def xd_frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray:
    """Build [n_frames] binary label vector from a Wu annotation (D-16 UCF-parallel).

    Per-frame label = union of all intervals. Endpoints clamped to [0, n_frames] —
    71 abnormal test videos have intervals that overshoot N_snippets*16 by 1-15 frames
    (verified: I3D extractor dropped final sub-16-frame remainder; clamping avoids
    IndexError / OOB writes).

    Args:
        anno: VideoAnnotation from parse_xd_annotations().
        n_frames: Target length of the output label vector (typically len(scores)*16).

    Returns:
        numpy int64 array of shape [n_frames] with values in {0, 1}.
    """
    labels = np.zeros(n_frames, dtype=np.int64)
    for s, e in anno.intervals:
        s_c = max(0, int(s))
        e_c = min(n_frames, int(e))
        if e_c > s_c:
            labels[s_c:e_c] = 1
    return labels
