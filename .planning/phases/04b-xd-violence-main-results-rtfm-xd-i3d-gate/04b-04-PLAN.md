---
phase: 04b
plan: 04
type: execute
wave: 2
depends_on: [04b-01]
files_modified:
  - src/evaluate.py
  - tests/test_evaluate_xd_i3d.py
autonomous: true
requirements:
  - EVAL-01
tags: [evaluate, annotations, frame-labels, c4-guard]
user_setup: []

must_haves:
  truths:
    - "`src/evaluate.py::_build_frame_arrays` xd_i3d branch at lines 180-192 REPLACED with Wu annotation-driven label construction (NOT the all-zero stub)"
    - "For each video_id in per_video_snippet_scores: `n_frames = len(scores) * 16`; `snippet_to_frame(scores, n_frames, snippet_window=16, upsample_factor=1)`"
    - "If vid in annos (500 abnormal test videos): `labels_map[vid] = xd_frame_labels(annos[vid], n_frames); cats_map[vid] = annos[vid].category`"
    - "If vid NOT in annos (300 normal test videos — Wu file omits normals): `labels_map[vid] = np.zeros(n_frames, dtype=np.int64); cats_map[vid] = 'Normal'`"
    - "Annotation file resolution: `cfg.paths.annotations_dir / xd_temporal.txt` with `_PROJECT_ROOT / data / annotations / xd_temporal.txt` as canonical fallback (D-04 pattern mirrored)"
    - "C4 guard enforcement: `compute_frame_metrics` (already shipped) asserts `len(frame_scores) == len(frame_labels)` for free — no new guard code needed"
  artifacts:
    - path: "src/evaluate.py"
      provides: "REWRITTEN xd_i3d branch in _build_frame_arrays (lines 180-192 replaced); new imports from src.eval.xd_annotations"
      contains: "parse_xd_annotations"
    - path: "tests/test_evaluate_xd_i3d.py"
      provides: "Unit tests for the rewritten _build_frame_arrays xd_i3d path (3 tests minimum per VALIDATION rows 4b-04-01/02/03)"
      min_lines: 100
  key_links:
    - from: "src/evaluate.py"
      to: "src/eval/xd_annotations.py"
      via: "from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels"
      pattern: "from src\\.eval\\.xd_annotations import"
    - from: "src/evaluate.py"
      to: "data/annotations/xd_temporal.txt"
      via: "_PROJECT_ROOT / data / annotations / xd_temporal.txt canonical fallback"
      pattern: "xd_temporal.txt"
    - from: "tests/test_evaluate_xd_i3d.py"
      to: "src/evaluate.py"
      via: "from src.evaluate import _build_frame_arrays"
      pattern: "from src.evaluate import"
---

<objective>
Rewrite the `src/evaluate.py::_build_frame_arrays` xd_i3d branch at lines 180-192, replacing the all-zero label stub with real Wu 2020 annotation-driven label construction. The stub in prod today defaults every xd_i3d test label to zero, making frame-level AUC/AP meaningless. This plan wires the `parse_xd_annotations` + `xd_frame_labels` utilities created by Plan 04b-01 into the evaluation harness, respecting the sentinel-guard pattern: `if vid in annos` for the 500 abnormal videos, `labels_map[vid] = zeros` for the 300 normal videos (Wu file omits normals).

Purpose: Without real ground-truth labels in `_build_frame_arrays`, the RTFM XD-I3D gate cannot measure anything meaningful. This plan delivers the missing wiring so that when Plan 04b-05 runs `scripts/run_ablations.py --queue rtfm_gate`, the resulting `eval_metrics.json` contains a real AP value that can be compared against the 76.81% gate threshold (D-03). Snippet window (16) and upsample factor (1) are verified correct by RESEARCH.md bit-identical match to XDVioDet's `gt.npy` (2,330,384 frames, 0.2308 positive fraction).

Output: `src/evaluate.py` with the xd_i3d branch at lines 180-192 replaced (~25 LOC new); new imports added; existing UCF branch and function signature UNCHANGED. `tests/test_evaluate_xd_i3d.py` with 3 tests covering abnormal-nonzero labels, normal-zero labels, and C4 guard tripping.
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

<!-- Prior plan artifacts (parser + data file): -->
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-01-PLAN.md

<!-- CRITICAL target file: -->
@src/evaluate.py

<!-- UCF branch template (mirror its structure for xd_i3d): -->
<!-- The UCF branch at src/evaluate.py:194-227 is the direct structural template -->

<!-- Parser being consumed (created by Plan 04b-01): -->
@src/eval/xd_annotations.py

<!-- Utilities already present (reused unchanged): -->
@src/eval/snippet_to_frame.py
@src/eval/metrics.py

<!-- Test analog: -->
@tests/test_evaluate_cli.py

<interfaces>
<!-- Contract executor must implement. -->

**Existing _build_frame_arrays signature (src/evaluate.py, DO NOT MODIFY):**
```python
def _build_frame_arrays(cfg: dict, per_video_snippet_scores: Dict[str, np.ndarray]):
    """Returns (frames_map, labels_map, cats_map) per video_id."""
```

**xd_i3d branch to REPLACE (lines 180-192):**
```python
if ds == "xd_i3d":
    snippet_window = 16
    upsample_factor = 1
    frames_map, labels_map, cats_map = {}, {}, {}
    for vid, scores in per_video_snippet_scores.items():
        n_frames = len(scores) * snippet_window
        frames_map[vid] = snippet_to_frame(
            scores, n_frames=n_frames,
            snippet_window=snippet_window, upsample_factor=upsample_factor,
        )
        labels_map[vid] = np.zeros(n_frames, dtype=np.int64)       # <-- STUB (REPLACE)
        cats_map[vid] = "Normal" if vid.endswith("_label_A") else "Abuse"  # <-- STUB (REPLACE)
    return frames_map, labels_map, cats_map
```

**UCF branch structural template (src/evaluate.py:194-227, DO NOT MODIFY — reference only):**
```python
# ---- UCF default path ----
ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
ann_path = None
if ann_dir_cfg:
    candidate = Path(ann_dir_cfg) / "ucf_temporal.txt"
    if candidate.exists():
        ann_path = candidate
if ann_path is None:
    ann_path = _PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"

annos = parse_annotations(ann_path) if ann_path.exists() else {}

snippet_window = 64
upsample_factor = 10

frames_map, labels_map, cats_map = {}, {}, {}
for vid, scores in per_video_snippet_scores.items():
    n_frames = len(scores) * snippet_window * upsample_factor
    if vid in annos:
        anno = annos[vid]
        cats_map[vid] = anno.category
        labels_map[vid] = frame_labels(anno, n_frames)
    else:
        cats_map[vid] = "Normal"
        labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
    frames_map[vid] = snippet_to_frame(
        scores, n_frames=n_frames,
        snippet_window=snippet_window, upsample_factor=upsample_factor,
    )
return frames_map, labels_map, cats_map
```

**xd_annotations.py public surface (Plan 04b-01 delivered):**
```python
def parse_xd_annotations(path: Path) -> Dict[str, VideoAnnotation]
def xd_frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray
```

**snippet_to_frame contract (src/eval/snippet_to_frame.py, unchanged):**
```python
def snippet_to_frame(scores, n_frames: int, snippet_window: int, upsample_factor: int = 1) -> np.ndarray
```

**compute_frame_metrics C4 contract (src/eval/metrics.py, unchanged):**
```python
def compute_frame_metrics(frames_map, labels_map, cats_map=None) -> dict:
    # Hard asserts len(frame_scores) == len(frame_labels) per video before sklearn call
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Rewrite _build_frame_arrays xd_i3d branch in src/evaluate.py with Wu annotation wiring</name>
  <files>src/evaluate.py</files>
  <read_first>
    - src/evaluate.py (full file — pay attention to lines 180-192 for the stub being replaced, AND lines 194-227 for the UCF branch template pattern)
    - src/eval/xd_annotations.py (created by Plan 04b-01 — verify `parse_xd_annotations` and `xd_frame_labels` are importable)
    - src/eval/snippet_to_frame.py (understand the reused utility signature — snippet_window + upsample_factor kwargs)
    - src/eval/metrics.py (understand compute_frame_metrics C4 length assertion behavior)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "Pattern 4: Sentinel-guarded all-zero labels for unannotated normals" (lines 546-590) for the verified target code
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "src/evaluate.py::_build_frame_arrays xd_i3d branch" (lines 524-605) for the detailed replacement pattern
  </read_first>
  <behavior>
    - Test 1: Calling `_build_frame_arrays(cfg={"dataset": "xd_i3d", "paths": {"annotations_dir": ann_dir}}, per_video_snippet_scores={"vid_label_B1-0-0": np.array([0.1, 0.2, 0.3])})` where ann_dir/xd_temporal.txt contains `vid_label_B1-0-0 10 30` returns a labels_map where `labels_map["vid_label_B1-0-0"].sum() > 0` (NOT all zeros)
    - Test 2: For a video_id NOT present in the annotation file (normal video), `labels_map[vid]` is all zeros of length `len(scores) * 16`
    - Test 3: `frames_map[vid]` has shape `(len(scores) * 16,)` per `snippet_window=16, upsample_factor=1`
    - Test 4: Both the UCF branch (existing) and the new xd_i3d branch route through `snippet_to_frame` for frames_map construction
  </behavior>
  <action>
    Open `src/evaluate.py`. Perform 2 edits:

    Edit 1 — Add the new imports at the top of the file. Find the existing line that imports UCF annotations:
    ```python
    from src.eval.ucf_annotations import frame_labels, parse_annotations
    ```
    IMMEDIATELY after it, add:
    ```python
    from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels
    ```

    Edit 2 — Replace the `xd_i3d` branch body at lines 180-192. The CURRENT STUB is:
    ```python
    if ds == "xd_i3d":
        snippet_window = 16
        upsample_factor = 1
        frames_map, labels_map, cats_map = {}, {}, {}
        for vid, scores in per_video_snippet_scores.items():
            n_frames = len(scores) * snippet_window
            frames_map[vid] = snippet_to_frame(
                scores, n_frames=n_frames,
                snippet_window=snippet_window, upsample_factor=upsample_factor,
            )
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
            cats_map[vid] = "Normal" if vid.endswith("_label_A") else "Abuse"
        return frames_map, labels_map, cats_map
    ```

    Replace it WITH:
    ```python
    if ds == "xd_i3d":
        # D-07/D-10: Wu 2020 annotation path resolution (mirror UCF D-04 canonical fallback)
        ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
        ann_path = None
        if ann_dir_cfg:
            candidate = Path(ann_dir_cfg) / "xd_temporal.txt"
            if candidate.exists():
                ann_path = candidate
        if ann_path is None:
            # D-07 canonical fallback (parallel to UCF ucf_temporal.txt location)
            ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"

        annos = parse_xd_annotations(ann_path) if ann_path.exists() else {}

        # D-08: I3D stride=16, annotation-fps = video-fps (no upsample needed).
        # Verified bit-identical to XDVioDet gt.npy (2,330,384 frames).
        snippet_window = 16
        upsample_factor = 1

        frames_map: dict = {}
        labels_map: dict = {}
        cats_map: dict = {}
        for vid, scores in per_video_snippet_scores.items():
            n_frames = len(scores) * snippet_window
            frames_map[vid] = snippet_to_frame(
                scores, n_frames=n_frames,
                snippet_window=snippet_window, upsample_factor=upsample_factor,
            )
            if vid in annos:
                # 500 abnormal test videos — Wu provides real intervals
                anno = annos[vid]
                labels_map[vid] = xd_frame_labels(anno, n_frames)
                # D-10: cats_map populated for Phase 4c forward-compat (D-13 suppresses
                # per-category surfacing for rtfm variant but the parser knows the code).
                cats_map[vid] = anno.category
            else:
                # 300 normal test videos — Wu omits normals; Pitfall 2 guard.
                labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
                cats_map[vid] = "Normal"
        return frames_map, labels_map, cats_map
    ```

    Do NOT touch anything else in `_build_frame_arrays`. The UCF branch at lines 194-227 (after the replaced xd_i3d block) is the untouched existing pattern.
  </action>
  <verify>
    <automated>python -c "from src.evaluate import _build_frame_arrays; from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels; print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "from src.eval.xd_annotations import" src/evaluate.py` exit 0
    - `grep -q "parse_xd_annotations" src/evaluate.py` shows at least 2 occurrences (import + call)
    - `grep -q "xd_frame_labels" src/evaluate.py` shows at least 2 occurrences (import + call)
    - The stub is REMOVED: `grep -q 'labels_map\[vid\] = np.zeros(n_frames, dtype=np.int64)$' src/evaluate.py` should match the new branch ONLY inside `else:` block, not as the UNCONDITIONAL `labels_map[vid] = np.zeros(...)` that the stub had. Verify: `grep -B 1 "labels_map\[vid\] = np.zeros(n_frames" src/evaluate.py | grep -q "else:"` exit 0 (the zeros assignment must now be preceded by `else:`)
    - `if vid in annos:` guard present: `grep -q "if vid in annos:" src/evaluate.py`
    - `cats_map[vid] = anno.category` present (Phase 4c forward-compat): `grep -q "cats_map\[vid\] = anno.category" src/evaluate.py`
    - `cats_map[vid] = "Normal"` present in else branch (for omitted normals): `grep -q 'cats_map\[vid\] = "Normal"' src/evaluate.py`
    - `snippet_window = 16` and `upsample_factor = 1` preserved verbatim from the stub: `grep -q "snippet_window = 16" src/evaluate.py && grep -q "upsample_factor = 1" src/evaluate.py`
    - The UCF branch is UNCHANGED: `grep -q "snippet_window = 64" src/evaluate.py && grep -q "upsample_factor = 10" src/evaluate.py` (UCF values preserved)
    - Module imports cleanly: `python -c "from src.evaluate import _build_frame_arrays"` exit 0
    - No regression: existing evaluate tests pass: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_evaluate_cli.py -x --tb=short` exit 0
  </acceptance_criteria>
  <done>xd_i3d branch rewritten with real Wu annotation wiring; UCF branch untouched; imports added; existing tests still pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create tests/test_evaluate_xd_i3d.py covering abnormal-nonzero, normal-zero, and C4 guard</name>
  <files>tests/test_evaluate_xd_i3d.py</files>
  <read_first>
    - src/evaluate.py (after Task 1 — verify `_build_frame_arrays` routes xd_i3d through `parse_xd_annotations`)
    - tests/test_evaluate_cli.py (full file — structural template, especially `prepared_run_dir` fixture pattern at lines 24-74 + CLI subprocess pattern at lines 77-94)
    - tests/conftest.py (verify `synthetic_i3d_features` fixture is accessible)
    - tests/fixtures/synthetic_eval.py (if `make_synthetic_i3d` has a test_ids accessor — we need known-IDs to write matching annotations)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "tests/test_evaluate_xd_i3d.py" (lines 890-981) for test templates
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-VALIDATION.md rows 4b-04-01, 4b-04-02, 4b-04-03 for exact test function names
  </read_first>
  <behavior>
    - Test 1 (`test_build_frame_arrays_abnormal_nonzero`): Given an abnormal video_id with a matching Wu annotation entry, `_build_frame_arrays` produces a labels_map where `labels_map[vid].sum() > 0` AND the positive region matches the annotation intervals
    - Test 2 (`test_build_frame_arrays_normal_zero`): Given a normal video_id (NOT in annotation file), `_build_frame_arrays` produces `labels_map[vid] = zeros` of length `len(scores) * 16`
    - Test 3 (`test_c4_guard_trips_on_length_mismatch`): If a downstream call to `compute_frame_metrics(frames_map, labels_map)` is given arrays with mismatched lengths, the assertion raises (the existing `compute_frame_metrics` enforcement path; we just verify it fires for xd_i3d via integration)
    - Test 4 (`test_snippet_to_frame_broadcast`): `frames_map[vid]` has length `len(scores) * 16` and is monotonically related to the input scores (verify via length assertion + dtype)
  </behavior>
  <action>
    Create NEW file `tests/test_evaluate_xd_i3d.py` with the following structure:

    ```python
    """Unit tests for the rewritten _build_frame_arrays xd_i3d branch (Phase 4b Plan 04).

    Covers VALIDATION.md rows 4b-04-01 / 4b-04-02 / 4b-04-03:
      - Abnormal videos produce non-zero labels from Wu annotation intervals
      - Normal videos (missing from Wu file) default to zero labels
      - C4 guard (from compute_frame_metrics) raises on length mismatch
    """
    from __future__ import annotations

    from pathlib import Path

    import numpy as np
    import pytest

    from src.evaluate import _build_frame_arrays
    from src.eval.metrics import compute_frame_metrics


    PROJECT_ROOT = Path(__file__).resolve().parent.parent


    # ------------------------------------------------------------------
    # Helper: write a tiny Wu-format annotation file to tmp_path
    # ------------------------------------------------------------------
    def _write_xd_annotation(tmp_path: Path, rows: list[str]) -> Path:
        """Write rows to tmp_path/data/annotations/xd_temporal.txt, return the ann_dir path."""
        ann_dir = tmp_path / "data" / "annotations"
        ann_dir.mkdir(parents=True, exist_ok=True)
        (ann_dir / "xd_temporal.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
        return ann_dir


    # ==================================================================
    # VALIDATION.md row 4b-04-01: abnormal video produces non-zero labels
    # ==================================================================
    def test_build_frame_arrays_abnormal_nonzero(tmp_path):
        """Abnormal video with matching Wu annotation produces labels with positive region."""
        # Annotation: video "abnormal_vid_label_B1-0-0" has a single interval [16, 48]
        # With snippet_window=16, n_frames = 4 * 16 = 64.
        # labels[16:48] should be 1; labels[0:16] and labels[48:64] should be 0.
        ann_dir = _write_xd_annotation(tmp_path, ["abnormal_vid_label_B1-0-0 16 48"])
        cfg = {
            "dataset": "xd_i3d",
            "paths": {"annotations_dir": str(ann_dir)},
        }
        # 4 snippets -> n_frames = 4 * 16 = 64
        scores = np.array([0.1, 0.5, 0.8, 0.2], dtype=np.float32)
        per_video_scores = {"abnormal_vid_label_B1-0-0": scores}

        frames_map, labels_map, cats_map = _build_frame_arrays(cfg, per_video_scores)

        vid = "abnormal_vid_label_B1-0-0"
        assert vid in frames_map and vid in labels_map and vid in cats_map
        assert frames_map[vid].shape == (64,)
        assert labels_map[vid].shape == (64,)
        assert labels_map[vid].dtype == np.int64
        # Non-zero labels from the [16, 48] interval
        assert labels_map[vid].sum() == 32, f"expected 32 positive frames, got {labels_map[vid].sum()}"
        # Correct region
        assert (labels_map[vid][16:48] == 1).all(), "interval [16, 48] not all ones"
        assert (labels_map[vid][:16] == 0).all(), "pre-interval not all zeros"
        assert (labels_map[vid][48:] == 0).all(), "post-interval not all zeros"
        # Category parsed from _label_ suffix
        assert cats_map[vid] == "B1", f"expected B1, got {cats_map[vid]}"


    # ==================================================================
    # VALIDATION.md row 4b-04-02: normal video (missing from Wu file) -> zero labels
    # ==================================================================
    def test_build_frame_arrays_normal_zero(tmp_path):
        """Normal video (not in annotations.txt) produces all-zero labels + cats=Normal."""
        # Annotation file has ONLY an abnormal entry; the normal "_label_A" video is omitted.
        ann_dir = _write_xd_annotation(tmp_path, ["other_abnormal_label_B2-0-0 10 30"])
        cfg = {
            "dataset": "xd_i3d",
            "paths": {"annotations_dir": str(ann_dir)},
        }
        scores = np.array([0.1, 0.2, 0.3], dtype=np.float32)  # 3 snippets -> n_frames=48
        per_video_scores = {"normal_vid_label_A": scores}

        frames_map, labels_map, cats_map = _build_frame_arrays(cfg, per_video_scores)

        vid = "normal_vid_label_A"
        assert vid in labels_map
        assert labels_map[vid].shape == (48,)
        assert labels_map[vid].sum() == 0, "normal video should have all-zero labels"
        assert cats_map[vid] == "Normal", f"expected Normal, got {cats_map[vid]}"
        assert frames_map[vid].shape == (48,), f"expected shape (48,), got {frames_map[vid].shape}"


    # ==================================================================
    # VALIDATION.md row 4b-04-03: C4 guard trips on length mismatch
    # ==================================================================
    def test_c4_guard_trips_on_length_mismatch(tmp_path):
        """compute_frame_metrics raises AssertionError when frames_map[vid] and labels_map[vid]
        have different lengths (C4 contract inherited from src/eval/metrics.py)."""
        # Construct a deliberately mismatched pair by writing raw numpy arrays.
        # The sklearn downstream would produce garbage; the C4 guard catches it.
        frames_map = {"v": np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)}  # length 5
        labels_map = {"v": np.array([0, 1, 0, 1, 0, 1], dtype=np.int64)}           # length 6 — MISMATCH

        with pytest.raises((AssertionError, ValueError)):
            compute_frame_metrics(frames_map, labels_map)


    # ==================================================================
    # Additional: snippet_to_frame broadcast shape sanity
    # ==================================================================
    def test_snippet_to_frame_broadcast_length(tmp_path):
        """frames_map[vid] has length exactly len(scores) * 16 (snippet_window=16, upsample=1)."""
        ann_dir = _write_xd_annotation(tmp_path, ["v_label_B1-0-0 0 32"])
        cfg = {
            "dataset": "xd_i3d",
            "paths": {"annotations_dir": str(ann_dir)},
        }
        for n_snippets in [1, 5, 20, 100]:
            scores = np.random.rand(n_snippets).astype(np.float32)
            per_video_scores = {"v_label_B1-0-0": scores}
            frames_map, _labels_map, _cats_map = _build_frame_arrays(cfg, per_video_scores)
            assert frames_map["v_label_B1-0-0"].shape == (n_snippets * 16,), (
                f"n_snippets={n_snippets}: expected length {n_snippets * 16}, "
                f"got {frames_map['v_label_B1-0-0'].shape}"
            )
    ```
  </action>
  <verify>
    <automated>C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_evaluate_xd_i3d.py -x --tb=short</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_evaluate_xd_i3d.py` exists (verify: `test -f tests/test_evaluate_xd_i3d.py`)
    - `grep -c "^def test_" tests/test_evaluate_xd_i3d.py` outputs `4`
    - Required test function names present:
      - `test_build_frame_arrays_abnormal_nonzero` (VALIDATION row 4b-04-01)
      - `test_build_frame_arrays_normal_zero` (VALIDATION row 4b-04-02)
      - `test_c4_guard_trips_on_length_mismatch` (VALIDATION row 4b-04-03)
      - `test_snippet_to_frame_broadcast_length` (bonus shape sanity)
    - All 4 tests pass: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_evaluate_xd_i3d.py -x --tb=short` exit 0
    - Test file imports `_build_frame_arrays` from `src.evaluate`: `grep -q "from src.evaluate import _build_frame_arrays" tests/test_evaluate_xd_i3d.py`
    - Test file imports `compute_frame_metrics`: `grep -q "compute_frame_metrics" tests/test_evaluate_xd_i3d.py`
  </acceptance_criteria>
  <done>4 unit tests pass: abnormal labels non-zero + shape-correct, normal labels all-zero, C4 guard trips on mismatch, snippet-to-frame length correct.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Annotation file → evaluation harness | `data/annotations/xd_temporal.txt` (committed in Plan 04b-01) is read via `parse_xd_annotations`; returns Dict[str, VideoAnnotation] consumed internally |
| Config `paths.annotations_dir` → filesystem read | Optional override path; falls back to canonical `_PROJECT_ROOT / data / annotations / xd_temporal.txt` |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4b-11 | Input Validation | `video_id` string from `per_video_snippet_scores.keys()` used as dict lookup key | accept | video_id originates from `I3DFeatureDataset.video_ids` which is derived from the trusted split file `data/splits/xd_test.txt`. No filesystem traversal; only dict membership check via `if vid in annos`. |
| T-4b-12 | Tampering | Annotation file integrity at eval time | mitigate | File is committed under git with SHA256 recorded in Plan 04b-01's commit message. Any future modification is visible in `git log data/annotations/xd_temporal.txt`. Parser raises ValueError on malformed rows (odd endpoints). |
| T-4b-13 | Denial of Service | Large per-video scores array | accept | `len(scores) * 16` is bounded by the I3D cache structure (~300-1600 frames per video, validated in RESEARCH.md RGBTest inventory); memory O(n_frames) is negligible. |
| T-4b-14 | Information Disclosure | Category metadata `_parse_category` exposes category code | accept | Category is parsed FROM the video_id suffix (already present in split file); no new information disclosure. Phase 4c will surface this in per_category.csv; Phase 4b does not. |

**Phase 4b Plan 04 security posture:** inherits Phase 4 posture. Pure read-only transformation of cached data + annotation file.
</threat_model>

<verification>
## Per-Task Automated Verify
- Task 1: `python -c "from src.evaluate import _build_frame_arrays; from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels"` exit 0
- Task 2: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_evaluate_xd_i3d.py -x --tb=short` exit 0 with 4/4 passing

## Plan-Level Gate
- Full test suite green: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x --ignore=tests/test_ctrgcn_smoke.py --tb=short` exit 0 (no regressions to existing evaluate.py tests)
- Combined Phase 4b test subset green: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_xd_annotations.py tests/test_loaders_i3d.py tests/test_train_i3d.py tests/test_evaluate_xd_i3d.py -x --tb=short` exits 0

## Decision Traceability
- D-07 (Wu annotation at `data/annotations/xd_temporal.txt`) — canonical fallback path preserved
- D-08 (I3D stride=16, upsample=1) — `snippet_window = 16`, `upsample_factor = 1` verbatim
- D-09 (C4 guard via `compute_frame_metrics`) — guard inherited unchanged; test_c4_guard_trips_on_length_mismatch verifies
- D-10 (parser + `xd_frame_labels` + category parser forward-compat) — all three consumed
- D-13 (no per-category surfacing for rtfm variant) — `cats_map[vid] = anno.category` captured but NOT processed by the rtfm variant's eval path; `per_category.csv` output will be empty or "overall"-only via existing writer logic
- Pitfall 2 (normal videos missing from Wu file) — `if vid in annos: ... else: zeros + "Normal"` guard
- Pitfall 3 (interval overshoot clamping) — inherited from `xd_frame_labels` clamp-to-n_frames (from Plan 04b-01)
</verification>

<success_criteria>
- `src/evaluate.py::_build_frame_arrays` xd_i3d branch (formerly at lines 180-192) is rewritten with:
  - Import of `parse_xd_annotations` + `xd_frame_labels` at module top
  - Annotation file resolution with `_PROJECT_ROOT / data / annotations / xd_temporal.txt` fallback
  - `if vid in annos:` guard routing abnormal videos through `xd_frame_labels`
  - `else:` branch for normals (zeros + "Normal" category)
  - `snippet_window=16, upsample_factor=1` preserved
- UCF branch at lines 194-227 UNCHANGED
- `tests/test_evaluate_xd_i3d.py` has 4 tests, all passing
- No regression: existing test suite remains green
- When Plan 04b-05 runs `evaluate.py` on real I3D test features, `_build_frame_arrays` will now produce NON-ZERO labels for the 500 abnormal test videos (making AUC/AP meaningful)
</success_criteria>

<output>
After completion, create `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-04-SUMMARY.md` documenting:
- Commit SHAs for Task 1 + Task 2
- Diff summary for src/evaluate.py (lines 180-192 replaced with ~25 LOC; imports added)
- Test results: `pytest tests/test_evaluate_xd_i3d.py -v` output tail with `4 passed`
- Sanity: full suite still green
- Any deviations from plan (Rule 1/2/3/4) with remediation
</output>
</content>
</invoke>