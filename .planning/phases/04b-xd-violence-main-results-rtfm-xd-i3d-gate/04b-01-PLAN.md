---
phase: 04b
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/eval/xd_annotations.py
  - data/annotations/xd_temporal.txt
  - tests/conftest.py
  - tests/test_xd_annotations.py
autonomous: true
requirements:
  - EVAL-01
tags: [eval, annotation-parser, xd-violence, wu-et-al]
user_setup: []

must_haves:
  truths:
    - "data/annotations/xd_temporal.txt exists with exactly 500 non-blank lines (abnormal test videos only; normals omitted per Wu convention)"
    - "parse_xd_annotations() returns Dict[str, VideoAnnotation] keyed by .mp4-stripped video_id"
    - "xd_frame_labels(anno, n_frames) clamps interval endpoints to n_frames (71 abnormal test videos have intervals overshooting by 1-15 frames)"
    - "tests/test_xd_annotations.py passes with 6 tests: real-file smoke, multi-interval, .mp4 stripping, v= prefix preservation, clamping, odd-endpoint raises"
  artifacts:
    - path: "src/eval/xd_annotations.py"
      provides: "VideoAnnotation frozen dataclass + parse_xd_annotations + xd_frame_labels + _parse_category helper"
      min_lines: 80
      exports: ["VideoAnnotation", "parse_xd_annotations", "xd_frame_labels"]
    - path: "data/annotations/xd_temporal.txt"
      provides: "Wu 2020 XD-Violence frame-level annotations (500 lines, ~6.2KB)"
      sha256_source: "https://roc-ng.github.io/XD-Violence/images/annotations.txt"
    - path: "tests/test_xd_annotations.py"
      provides: "6-test unit suite for xd_annotations.py"
      min_lines: 100
    - path: "tests/conftest.py"
      provides: "Added xd_temporal_path fixture mirroring ucf_temporal_path pattern"
      contains: "def xd_temporal_path"
  key_links:
    - from: "tests/test_xd_annotations.py"
      to: "src/eval/xd_annotations.py"
      via: "from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels, VideoAnnotation"
      pattern: "from src\\.eval\\.xd_annotations import"
    - from: "tests/test_xd_annotations.py"
      to: "data/annotations/xd_temporal.txt"
      via: "xd_temporal_path fixture resolves to this committed file"
      pattern: "xd_temporal_path"
---

<objective>
Create the Wu et al. 2020 XD-Violence annotation parsing module and commit the official annotations file. Produces `src/eval/xd_annotations.py` (mirror of `src/eval/ucf_annotations.py`), the 500-line `data/annotations/xd_temporal.txt` file downloaded from `https://roc-ng.github.io/XD-Violence/images/annotations.txt`, and a 6-test pytest unit suite. This is the FIRST of five atomic commits forming the Phase 4b RTFM XD-I3D gate (D-18 plan shape).

Purpose: EVAL-01 depends on real frame-level ground-truth labels for the 500 abnormal XD-Violence test videos. The current `src/evaluate.py::_build_frame_arrays` xd_i3d branch at lines 180-192 defaults all labels to zero, making AUC/AP meaningless. This plan delivers the parser + data file that Plan 04b-04 will wire into evaluate.py. The parser must ALSO expose category parsing (`_parse_category`) for Phase 4c forward-compat per D-10, even though Phase 4b itself does not surface categories (D-13).

Output: `src/eval/xd_annotations.py` (new module, ~80 LOC), `data/annotations/xd_temporal.txt` (new committed file, ~6.2KB), `tests/test_xd_annotations.py` (new 6-test suite), updated `tests/conftest.py` with `xd_temporal_path` fixture.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-CONTEXT.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-VALIDATION.md

<!-- Critical template file (analog): -->
@src/eval/ucf_annotations.py

<!-- Critical test analog: -->
@tests/test_ucf_annotations.py
@tests/conftest.py

<interfaces>
<!-- Template contract — src/eval/xd_annotations.py MUST mirror this structure with Wu format adjustments. Executor reads ucf_annotations.py directly; excerpt below shows the required public surface. -->

From src/eval/ucf_annotations.py (reference template):
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple
import numpy as np

Interval = Tuple[int | None, int | None]

@dataclass(frozen=True)
class VideoAnnotation:
    video_id: str
    category: str
    intervals: Tuple[Interval, Interval]

    @property
    def is_normal(self) -> bool: ...

def parse_annotations(path: Path) -> Dict[str, VideoAnnotation]: ...
def frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray: ...
```

Differences for Wu 2020 XD format:
- Columns are variable `1 + 2*K` for K >= 1 intervals (not fixed 6 like UCF)
- ID suffix stripping: `.mp4` only (not `_x264.mp4`)
- Normal videos are OMITTED from the file entirely (not encoded as -1,-1 placeholder rows)
- Categories are parsed from the video_id suffix `_label_B1-0-0` -> "B1" (not a separate column)

Required public names (imported by Plan 04b-04):
- `parse_xd_annotations(path: Path) -> Dict[str, VideoAnnotation]`
- `xd_frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray`
- `VideoAnnotation` dataclass with `video_id`, `category`, `intervals` fields
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Download Wu annotation file and add xd_temporal_path fixture to conftest.py</name>
  <files>data/annotations/xd_temporal.txt, tests/conftest.py</files>
  <read_first>
    - tests/conftest.py (read the full file; locate the existing `ucf_temporal_path` fixture around line 88-96 to mirror its pattern)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "Wu Annotation Format" (lines 617-669) for URL, format, size, line count
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "data/annotations/xd_temporal.txt" (lines 128-158) for commit protocol + sha256 recording requirement
  </read_first>
  <behavior>
    - Test 1: `pytest tests/test_xd_annotations.py::test_annotation_file_present -x` finds the file at `data/annotations/xd_temporal.txt` (500 lines, non-empty)
    - Test 2: the `xd_temporal_path` fixture in conftest.py resolves to `PROJECT_ROOT/data/annotations/xd_temporal.txt` and calls `pytest.skip(...)` if the file is missing (parallel to `ucf_temporal_path`)
  </behavior>
  <action>
    Step 1 — Download the Wu 2020 annotations file:
    ```bash
    curl -fsSL "https://roc-ng.github.io/XD-Violence/images/annotations.txt" -o data/annotations/xd_temporal.txt
    # Alternative if curl fails: use python
    # python -c "import urllib.request; urllib.request.urlretrieve('https://roc-ng.github.io/XD-Violence/images/annotations.txt', 'data/annotations/xd_temporal.txt')"
    ```
    Verify the file:
    ```bash
    wc -l data/annotations/xd_temporal.txt  # expect 500 non-blank lines
    ls -la data/annotations/xd_temporal.txt # expect ~6.2 KB
    sha256sum data/annotations/xd_temporal.txt  # RECORD THIS HASH; include in commit message body
    ```
    The file MUST be 500 non-blank lines per RESEARCH.md line 636. If line count is not 500, ABORT and report the discrepancy.

    Step 2 — Add `xd_temporal_path` fixture to `tests/conftest.py`:
    Open `tests/conftest.py`, find the existing `ucf_temporal_path` fixture (around line 88-96), and add a parallel `xd_temporal_path` fixture IMMEDIATELY after it:
    ```python
    @pytest.fixture
    def xd_temporal_path():
        """Real Wu 2020 Xd-Violence annotation file committed at data/annotations/xd_temporal.txt (D-07)."""
        p = PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"
        if not p.exists():
            pytest.skip(
                "data/annotations/xd_temporal.txt not present; Plan 04b-01 Task 1 creates it"
            )
        return p
    ```
    Use whatever PROJECT_ROOT / pytest import style the existing fixture uses in conftest.py (do not redefine).

    Step 3 — Verify the file is committable:
    ```bash
    git status data/annotations/xd_temporal.txt tests/conftest.py
    # Both should show as modified/new
    ```
    Do NOT commit yet — the commit happens after all three tasks in this plan succeed.
  </action>
  <verify>
    <automated>wc -l data/annotations/xd_temporal.txt | awk '{exit !($1 == 500)}' && grep -q "def xd_temporal_path" tests/conftest.py</automated>
  </verify>
  <acceptance_criteria>
    - `data/annotations/xd_temporal.txt` exists and has exactly 500 non-blank lines (verify: `grep -c -v '^$' data/annotations/xd_temporal.txt` outputs `500`)
    - File size ~6-7 KB (verify: `stat -c %s data/annotations/xd_temporal.txt` returns value between 5000 and 8000)
    - SHA256 of file recorded (will be written into commit message body in Task 3 or by the execute-phase commit step)
    - `tests/conftest.py` contains `def xd_temporal_path` (verify: `grep -c "def xd_temporal_path" tests/conftest.py` outputs `1`)
    - `tests/conftest.py` fixture body contains `pytest.skip` for the missing-file case (verify: `grep -A 5 "def xd_temporal_path" tests/conftest.py | grep -q "pytest.skip"`)
    - First line of `data/annotations/xd_temporal.txt` contains a video_id (any format starting with a non-whitespace character and followed by whitespace + digits; verify: `head -1 data/annotations/xd_temporal.txt | grep -qE '^\S+\s+[0-9]+'`)
  </acceptance_criteria>
  <done>Wu annotation file downloaded, committed to `data/annotations/xd_temporal.txt` with 500 verified lines. SHA256 recorded. conftest.py carries the new fixture.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement src/eval/xd_annotations.py with VideoAnnotation + parse_xd_annotations + xd_frame_labels</name>
  <files>src/eval/xd_annotations.py</files>
  <read_first>
    - src/eval/ucf_annotations.py (full file — this is the structural template)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md sections "Pattern 3: Annotation module mirror" (lines 422-545) and "Wu Annotation Format" (lines 617-669) for the verified parser code + format spec
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "src/eval/xd_annotations.py" (lines 28-126) for detailed template adaptation notes
  </read_first>
  <behavior>
    - Test 1: `parse_xd_annotations(path)` returns `Dict[str, VideoAnnotation]` with keys matching the .mp4-stripped video IDs
    - Test 2: a row with `"v.mp4 50 100"` parses to `intervals=((50, 100),)` keyed as `"v"` (no `.mp4` suffix)
    - Test 3: a row with `"v 50 100 150 200 250 300"` (3 intervals) parses to `intervals=((50,100), (150,200), (250,300))`
    - Test 4: a row with `"v 50 100 150"` (odd endpoints) raises `ValueError`
    - Test 5: `xd_frame_labels(anno, n_frames=100)` on anno `intervals=((50, 120),)` clamps endpoint to 100, returns vector with `labels[50:100] == 1`
    - Test 6: `_parse_category("v_label_B1-0-0")` returns `"B1"`; `_parse_category("v_label_G-B2-B6")` returns `"G"`; `_parse_category("v_label_A")` returns `"Normal"`
  </behavior>
  <action>
    Create NEW file `src/eval/xd_annotations.py` with the following verbatim contents (adapted from the verified RESEARCH.md lines 427-539 parser draft):

    ```python
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
        data/splits/xd_test.txt IDs (verified in RESEARCH.md Wu Annotation Format: 500/500
        abnormal test videos match after this step). The v= prefix on YouTube-sourced
        videos is preserved (verified: xd_test.txt also carries v= prefix on those).

        Categories: parsed from the _label_<code> suffix via _parse_category().

        File omissions: Wu's annotations.txt contains ONLY the 500 abnormal test videos.
        The 300 normal test videos have no entries; callers (e.g., _build_frame_arrays)
        must guard with `if vid in annos` and default missing entries to zero labels.

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
    ```

    Do NOT add any other functions. Do NOT re-export anything from ucf_annotations.py.
  </action>
  <verify>
    <automated>python -c "from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels, VideoAnnotation; a = parse_xd_annotations; b = xd_frame_labels; c = VideoAnnotation; print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `src/eval/xd_annotations.py` exists (verify: `test -f src/eval/xd_annotations.py`)
    - Module imports successfully: `python -c "from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels, VideoAnnotation"` exits 0
    - `grep -c "def parse_xd_annotations" src/eval/xd_annotations.py` outputs `1`
    - `grep -c "def xd_frame_labels" src/eval/xd_annotations.py` outputs `1`
    - `grep -c "def _parse_category" src/eval/xd_annotations.py` outputs `1`
    - `grep -c "class VideoAnnotation" src/eval/xd_annotations.py` outputs `1`
    - `grep -c "@dataclass(frozen=True)" src/eval/xd_annotations.py` outputs `>=1` (used on VideoAnnotation)
    - Parser round-trips on real file: `python -c "from src.eval.xd_annotations import parse_xd_annotations; a = parse_xd_annotations('data/annotations/xd_temporal.txt'); print(len(a))"` outputs `500`
    - Clamping works: `python -c "from src.eval.xd_annotations import VideoAnnotation, xd_frame_labels; a = VideoAnnotation('v', 'B1', ((50, 120),)); l = xd_frame_labels(a, 100); print(int(l.sum()))"` outputs `50`
    - Category parsing works: `python -c "from src.eval.xd_annotations import _parse_category; print(_parse_category('v_label_B1-0-0'), _parse_category('v_label_A'))"` outputs `B1 Normal`
  </acceptance_criteria>
  <done>Module file exists with the exact function signatures. Imports cleanly. Real-file round trip parses 500 entries.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Create tests/test_xd_annotations.py with 6-test suite covering parser + clamping + category</name>
  <files>tests/test_xd_annotations.py</files>
  <read_first>
    - tests/test_ucf_annotations.py (full file — structural template)
    - tests/conftest.py (after Task 1 modifications — verify `xd_temporal_path` fixture is defined)
    - src/eval/xd_annotations.py (created by Task 2)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "tests/test_xd_annotations.py" (lines 608-713) for test case templates
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-VALIDATION.md section "Per-Task Verification Map" (rows 4b-01-01 to 4b-01-03) for the exact test function names required
  </read_first>
  <behavior>
    - Test 1 (`test_annotation_file_present`): The committed `data/annotations/xd_temporal.txt` has >= 500 non-blank lines
    - Test 2 (`test_parse_multi_interval`): A synthetic 3-interval row parses to a VideoAnnotation with `len(intervals) == 3`
    - Test 3 (`test_parse_strips_mp4_suffix`): A row with `.mp4` suffix normalizes to no-suffix key
    - Test 4 (`test_parse_preserves_v_prefix`): A row with `v=XXX` prefix preserves the prefix in the key
    - Test 5 (`test_frame_labels_clamp`): Interval `(50, 120)` with `n_frames=100` produces a labels vector of length 100 with `labels[50:100] == 1` and no out-of-bounds error
    - Test 6 (`test_parse_raises_odd_intervals`): Row with odd endpoint count raises `ValueError`
    - Test 7 (`test_frame_labels_missing_video`): Calling `xd_frame_labels` on a VideoAnnotation constructed with empty intervals yields an all-zero label vector (supports VALIDATION.md row 4b-01-03)
    - Test 8 (`test_parse_category_codes`): `_parse_category` returns `"B1"` for `_label_B1-0-0`, `"G"` for `_label_G-B2-B6`, `"Normal"` for `_label_A`
  </behavior>
  <action>
    Create NEW file `tests/test_xd_annotations.py` with the following structure:

    ```python
    """Unit tests for src/eval/xd_annotations.py (Phase 4b Plan 01).

    Mirrors tests/test_ucf_annotations.py patterns, adapted for Wu 2020 format:
    - Variable-interval rows (1+2*K columns)
    - .mp4 suffix stripping (not _x264.mp4)
    - Missing-normal-video semantics handled at the caller level
    - Category parsing from _label_<code> suffix
    """
    from __future__ import annotations

    from pathlib import Path

    import numpy as np
    import pytest

    from src.eval.xd_annotations import (
        VideoAnnotation,
        parse_xd_annotations,
        xd_frame_labels,
        _parse_category,
    )

    PROJECT_ROOT = Path(__file__).resolve().parent.parent


    # ------------------------------------------------------------------
    # VALIDATION.md row 4b-01-01: real-file smoke test on committed data
    # ------------------------------------------------------------------
    def test_annotation_file_present(xd_temporal_path):
        """File at data/annotations/xd_temporal.txt exists with 500 abnormal entries."""
        annos = parse_xd_annotations(xd_temporal_path)
        assert len(annos) >= 500, f"expected >= 500 entries, got {len(annos)}"
        # Every parsed entry has at least one interval (normals are omitted from file)
        for vid, anno in annos.items():
            assert len(anno.intervals) >= 1, f"{vid} has no intervals"


    # ------------------------------------------------------------------
    # VALIDATION.md row 4b-01-02: multi-interval parsing (Wu-specific)
    # ------------------------------------------------------------------
    def test_parse_multi_interval(tmp_path):
        """Row with 3 intervals (7 columns total) parses to 3-tuple of intervals."""
        f = tmp_path / "anno.txt"
        f.write_text("v_label_B4-0-0 100 200 300 400 500 600\n", encoding="utf-8")
        annos = parse_xd_annotations(f)
        assert "v_label_B4-0-0" in annos
        anno = annos["v_label_B4-0-0"]
        assert anno.intervals == ((100, 200), (300, 400), (500, 600))
        assert anno.category == "B4"


    def test_parse_strips_mp4_suffix(tmp_path):
        """Video IDs ending in .mp4 get the suffix stripped to match split-file keys."""
        f = tmp_path / "anno.txt"
        f.write_text(
            "A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_B2-0-0.mp4 420 1848\n",
            encoding="utf-8",
        )
        annos = parse_xd_annotations(f)
        assert "A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_B2-0-0" in annos
        # And NOT the .mp4 version
        assert "A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_B2-0-0.mp4" not in annos


    def test_parse_preserves_v_prefix(tmp_path):
        """YouTube-sourced v=XXX IDs are preserved verbatim (no prefix stripping)."""
        f = tmp_path / "anno.txt"
        f.write_text("v=S-7rRLrxnVQ__#1_label_B4-0-0 150 420\n", encoding="utf-8")
        annos = parse_xd_annotations(f)
        assert "v=S-7rRLrxnVQ__#1_label_B4-0-0" in annos


    # ------------------------------------------------------------------
    # VALIDATION.md row 4b-01-03: frame_labels handles missing-video + clamping
    # ------------------------------------------------------------------
    def test_frame_labels_missing_video():
        """Empty-intervals annotation yields all-zero labels (supports normal-video default)."""
        anno = VideoAnnotation(video_id="v", category="Normal", intervals=())
        labels = xd_frame_labels(anno, n_frames=100)
        assert labels.shape == (100,)
        assert labels.sum() == 0


    def test_frame_labels_clamp(tmp_path):
        """Interval endpoint > n_frames clamps without error."""
        f = tmp_path / "anno.txt"
        f.write_text("X_label_B1-0-0 50 120\n", encoding="utf-8")
        annos = parse_xd_annotations(f)
        labels = xd_frame_labels(annos["X_label_B1-0-0"], n_frames=100)
        assert labels.shape == (100,)
        assert int(labels[50:100].sum()) == 50
        assert int(labels[:50].sum()) == 0


    def test_parse_raises_odd_intervals(tmp_path):
        """Row with odd-endpoint count raises ValueError."""
        f = tmp_path / "bad.txt"
        f.write_text("v_label_B1-0-0 100 200 300\n", encoding="utf-8")
        with pytest.raises(ValueError, match="odd"):
            parse_xd_annotations(f)


    # ------------------------------------------------------------------
    # Category parsing (Phase 4c forward-compat per D-10)
    # ------------------------------------------------------------------
    def test_parse_category_codes():
        """_parse_category maps common suffixes correctly."""
        assert _parse_category("v_label_B1-0-0") == "B1"
        assert _parse_category("v_label_B6-0-0") == "B6"
        assert _parse_category("v_label_G-B2-B6") == "G"
        assert _parse_category("v_label_B2-G-0") == "B2"
        assert _parse_category("v_label_A") == "Normal"
        assert _parse_category("random_noprefix") == "Unknown"
    ```
  </action>
  <verify>
    <automated>C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_xd_annotations.py -x --tb=short</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_xd_annotations.py` exists (verify: `test -f tests/test_xd_annotations.py`)
    - Pytest collection finds exactly 8 test functions (verify: `grep -c "^def test_" tests/test_xd_annotations.py` outputs `8`)
    - The following test function names are present:
      - `test_annotation_file_present` (VALIDATION row 4b-01-01)
      - `test_parse_multi_interval` (VALIDATION row 4b-01-02)
      - `test_parse_strips_mp4_suffix`
      - `test_parse_preserves_v_prefix`
      - `test_frame_labels_missing_video` (VALIDATION row 4b-01-03)
      - `test_frame_labels_clamp`
      - `test_parse_raises_odd_intervals`
      - `test_parse_category_codes`
    - All 8 tests pass: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_xd_annotations.py -x --tb=short` exits 0
    - Test file imports only from `src.eval.xd_annotations` (no coupling to other modules; verify: `grep "from src" tests/test_xd_annotations.py` shows only `from src.eval.xd_annotations import`)
  </acceptance_criteria>
  <done>8 unit tests pass (7 required + 1 bonus clamp test). File names match VALIDATION.md rows 4b-01-01, 4b-01-02, 4b-01-03.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| External HTTPS → local filesystem | Wu annotation file fetched from `roc-ng.github.io/XD-Violence/images/annotations.txt` (GitHub Pages); trusted academic source; downloaded ONCE at plan-execution time and committed to git for tamper-evidence |
| Filesystem → Python parser | `parse_xd_annotations()` reads the committed text file; inputs are untrusted-in-principle but the committed file is version-controlled |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4b-01 | Tampering | Wu annotation file contents | mitigate | SHA256 of downloaded file recorded in commit message body; subsequent verifiers can diff `sha256sum data/annotations/xd_temporal.txt` against the commit message. Source is `https://` (TLS-authenticated). File is committed to git providing per-commit integrity. |
| T-4b-02 | Input Validation | `parse_xd_annotations()` parsing | mitigate | Parser returns only `Dict[str, VideoAnnotation]` with `video_id` as a string key — never concatenated into a filesystem path or shell command downstream. `ValueError` raised on odd-endpoint rows. No `eval()`, no pickle, no dynamic imports. The parsed `video_id` is only used as a dict key in `_build_frame_arrays` (Plan 04b-04); it is NOT used to read files. |
| T-4b-03 | Denial of Service | Malformed large annotation file | accept | File size bound to ~6.2 KB by the trusted source; parsing is O(n) line-by-line and memory-bounded. No amplification attack possible. A future Wu-file rotation could ship a larger file, but the committed sha256 pin detects this. |

**Phase 4b Plan 01 security posture:** inherits Phase 4 posture; no new network-facing code, no dynamic evaluation, no pickle, no user-controlled paths. The annotation parser exposes only a pure-function surface.
</threat_model>

<verification>
## Per-Task Automated Verify
- Task 1: `wc -l data/annotations/xd_temporal.txt` outputs `500`; `grep -q "def xd_temporal_path" tests/conftest.py` exit 0
- Task 2: `python -c "from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels, VideoAnnotation"` exit 0
- Task 3: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_xd_annotations.py -x --tb=short` exit 0

## Plan-Level Gate
- All 3 tasks acceptance criteria pass
- Full Phase 4b scoped run: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_xd_annotations.py -x --tb=short` exits 0 with 8/8 passing
- `parse_xd_annotations('data/annotations/xd_temporal.txt')` returns a dict with >= 500 keys
- Pitfalls guarded (per RESEARCH.md):
  - Pitfall 3 (interval overshoot): `test_frame_labels_clamp` asserts clamping works
  - Pitfall 2 (normal videos missing from file): `test_frame_labels_missing_video` asserts zero-labels path works

## Decision Traceability
- D-07 (annotation source + commit location) — Task 1 downloads to `data/annotations/xd_temporal.txt`
- D-10 (parser module mirror of ucf_annotations.py) — Task 2 creates `src/eval/xd_annotations.py`
- D-13 (no per-category in Phase 4b rtfm variant, but parser supports it for Phase 4c) — Task 2 implements `_parse_category` but does NOT surface it in the rtfm variant
- D-17 (pytest unit tests) — Task 3 creates 8 tests covering parser + clamping + category
</verification>

<success_criteria>
- `data/annotations/xd_temporal.txt` committed with exactly 500 non-blank lines and SHA256 recorded in commit message
- `src/eval/xd_annotations.py` exists, imports cleanly, exposes `parse_xd_annotations`, `xd_frame_labels`, `VideoAnnotation`, `_parse_category`
- `tests/test_xd_annotations.py` has 8 tests, all passing via `pytest tests/test_xd_annotations.py -x`
- `tests/conftest.py` includes `xd_temporal_path` fixture (parallel to existing `ucf_temporal_path`)
- Real-file round-trip verifies: parser returns dict of length 500 from committed file
- No regressions to existing tests: `pytest tests/ -x --ignore=tests/test_ctrgcn_smoke.py` (full suite) exits 0
</success_criteria>

<output>
After completion, create `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-01-SUMMARY.md` documenting:
- Commit SHA for each atomic commit (Task 1-3)
- SHA256 of the downloaded annotation file
- Line count and size of the committed file
- Test results: `pytest tests/test_xd_annotations.py -v` output tail with `8 passed`
- Any deviations from plan (Rule 1/2/3/4) with remediation
</output>
</content>
</invoke>