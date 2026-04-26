---
phase: 04C-xd-violence-main-results
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - data/splits/xd_train.txt
  - src/data/dataset.py
  - src/evaluate.py
  - configs/skeleton_only_xd.yaml
  - configs/clip_only_xd.yaml
  - configs/late_fusion_xd.yaml
  - configs/gated_fusion_xd.yaml
  - configs/gated_fusion_xd_2person.yaml
  - configs/gated_fusion_xd_clip_mean.yaml
  - scripts/run_ablations.py
  - tests/test_run_ablations.py
  - tests/test_evaluate_xd.py
autonomous: true
requirements: [EVAL-02, EVAL-03, EVAL-04, EVAL-05]

must_haves:
  truths:
    - "XD split files exclude the 2 featureless videos and loaders skip comment lines"
    - "evaluate.py correctly routes dataset=xd to XD annotations with snippet_window=64 and upsample_factor=1"
    - "6 XD YAML configs exist with identical hyperparameters to UCF counterparts"
    - "3 new queues (phase4c_main, phase4c_pooling, phase4c_seeds) are registered and discoverable by --queue"
  artifacts:
    - path: "data/splits/xd_train.txt"
      provides: "Cleaned XD train split with 3358 IDs (2 removed per D-05)"
      contains: "# Excluded:"
    - path: "src/evaluate.py"
      provides: "XD fusion evaluation branch"
      contains: "elif ds == \"xd\":"
    - path: "configs/gated_fusion_xd.yaml"
      provides: "XD Gated Fusion config"
      contains: "dataset: xd"
    - path: "scripts/run_ablations.py"
      provides: "Phase 4c queue definitions"
      contains: "phase4c_main"
    - path: "tests/test_evaluate_xd.py"
      provides: "XD fusion evaluate branch tests"
      exports: ["test_build_frame_arrays_xd_abnormal", "test_build_frame_arrays_xd_normal"]
  key_links:
    - from: "configs/gated_fusion_xd.yaml"
      to: "src/data/loaders.py"
      via: "dataset: xd triggers xd split file routing"
      pattern: "dataset.*xd"
    - from: "src/evaluate.py"
      to: "src/eval/xd_annotations.py"
      via: "elif ds == 'xd' branch calls parse_xd_annotations"
      pattern: "parse_xd_annotations"
    - from: "scripts/run_ablations.py"
      to: "configs/gated_fusion_xd.yaml"
      via: "RunSpec config field"
      pattern: "configs/gated_fusion_xd.yaml"
---

<objective>
Prepare all code, configs, split files, and orchestration queues needed to run XD-Violence ablation experiments. This is the "tooling" plan -- no GPU training happens here.

Purpose: The existing codebase routes dataset="xd" through the UCF annotation path in evaluate.py, which would produce completely wrong frame-level metrics (wrong annotation file, wrong upsample factor). This plan fixes that critical gap, creates the 6 XD configs per D-01, cleans the split files per D-05, registers the 3 orchestration queues per D-02, and adds tests. After this plan, Plan 04C-02 can run training+evaluation without code changes.

Output: 6 new YAML configs, 1 fixed evaluate.py, 1 cleaned split file, 3 new queues in run_ablations.py, 2 new test files, 1 updated test file.
</objective>

<execution_context>
@D:/ViolenceCC/.claude/get-shit-done/workflows/execute-plan.md
@D:/ViolenceCC/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/04C-xd-violence-main-results/04C-CONTEXT.md

<interfaces>
<!-- Key types and contracts the executor needs. Extracted from codebase. -->

From src/data/dataset.py line 144-146:
```python
@staticmethod
def _load_split(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
```

From src/evaluate.py line 166-258 (_build_frame_arrays):
```python
def _build_frame_arrays(cfg: dict, per_video_snippet_scores: dict):
    ds = cfg.get("dataset", "ucf")
    if ds == "xd_i3d":
        # ... XD I3D path (snippet_window=16, upsample_factor=1) ...
        return frames_map, labels_map, cats_map
    # ---- UCF default path (and xd falls through to the same shape) ----
    # ... UCF path (snippet_window=64, upsample_factor=10) ...
```

From src/eval/xd_annotations.py:
```python
def parse_xd_annotations(ann_path) -> dict:  # returns {vid: VideoAnnotation}
def xd_frame_labels(anno, n_frames) -> np.ndarray:
def _parse_category(video_id: str) -> str:
```

From scripts/run_ablations.py line 44-73:
```python
@dataclass
class RunSpec:
    dataset: str; variant: str; seed: int; config: str; cache_variant: str = ""
    @property
    def run_name(self) -> str: ...
    def wandb_tags(self) -> List[str]: ...
```

From scripts/run_ablations.py line 82-113 (QUEUES dict):
```python
QUEUES = {
    "rtfm_gate": [...],
    "rtfm_gate_flow": [...],
    "phase4_main": [RunSpec("ucf", "skeleton_only", 42, ...), ...],
    "phase4_pooling": [RunSpec("ucf", "gated_fusion", 42, ..., "2person"), ...],
    "phase4_seeds": [RunSpec("ucf", "gated_fusion", 123, ...), ...],
}
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Clean XD split file + comment-safe loader + evaluate.py XD fusion branch</name>
  <files>data/splits/xd_train.txt, src/data/dataset.py, src/evaluate.py, tests/test_evaluate_xd.py</files>
  <read_first>
    - data/splits/xd_train.txt (current content, lines 1804 and 2036 contain the 2 IDs to remove)
    - src/data/dataset.py (lines 143-146: _load_split method)
    - src/evaluate.py (lines 166-258: _build_frame_arrays with xd_i3d and UCF branches)
    - src/eval/xd_annotations.py (parse_xd_annotations, xd_frame_labels, _parse_category signatures)
    - tests/test_evaluate_xd_i3d.py (pattern for XD evaluate tests)
  </read_first>
  <action>
**Part A -- Clean xd_train.txt (per D-05):**

1. Add 2-line comment header at top of `data/splits/xd_train.txt`:
```
# Excluded: v=8cTqh9tMz_I__#1_label_A (corrupt MP4, missing moov atom)
# Excluded: v=Gm73TwtUyGY__#1_label_G-0-0 (34 frames, below 64-frame window)
```
2. Remove the line `v=8cTqh9tMz_I__#1_label_A` (currently line 1804).
3. Remove the line `v=Gm73TwtUyGY__#1_label_G-0-0` (currently line 2036, will shift to 2035 after first removal).
4. Result: file has 2 comment lines + 3358 video ID lines = 3360 total lines.

Note: `xd_val.txt` and `xd_test.txt` do NOT contain these IDs (confirmed by grep), so they are not modified.

**Part B -- Make _load_split skip comment lines:**

In `src/data/dataset.py`, update `_load_split` (line 144-146) to skip lines starting with `#`:

```python
@staticmethod
def _load_split(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
```

This is backward-compatible: no existing split file has `#` lines, so UCF splits are unaffected.

**Part C -- Add `elif ds == "xd"` branch in evaluate.py (CRITICAL):**

In `src/evaluate.py::_build_frame_arrays`, insert a new `elif ds == "xd":` block between the `if ds == "xd_i3d":` block (ends at line 223) and the UCF default path (line 225). The new block mirrors the xd_i3d branch structure but uses the correct snippet parameters for fusion features:

```python
    elif ds == "xd":
        # Phase 4c: XD fusion (skeleton+CLIP) evaluation path.
        # Annotation routing mirrors xd_i3d (D-07/D-10 canonical fallback).
        ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
        ann_path = None
        if ann_dir_cfg:
            candidate = Path(ann_dir_cfg) / "xd_temporal.txt"
            if candidate.exists():
                ann_path = candidate
        if ann_path is None:
            ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"

        annos = parse_xd_annotations(ann_path) if ann_path.exists() else {}

        # XD fusion: skeleton+CLIP extraction uses 64-frame snippet windows
        # (same as UCF), but XD video frames are native FPS (no PNG 10x
        # upsample). So snippet_window=64, upsample_factor=1.
        snippet_window = 64
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
                anno = annos[vid]
                labels_map[vid] = xd_frame_labels(anno, n_frames)
                cats_map[vid] = anno.category
            else:
                labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
                cats_map[vid] = "Normal"
        return frames_map, labels_map, cats_map
```

Also update the comment on line 225 from `# ---- UCF default path (and xd falls through to the same shape) ----` to `# ---- UCF default path ----` since xd no longer falls through.

**Part D -- Create tests/test_evaluate_xd.py:**

Create a new test file following the pattern of `tests/test_evaluate_xd_i3d.py`. Tests:

1. `test_build_frame_arrays_xd_abnormal` -- Abnormal XD video with Wu annotation produces non-zero labels. Use snippet_scores of length 4, expect n_frames = 4*64 = 256. Verify labels have positive region matching annotation interval.

2. `test_build_frame_arrays_xd_normal` -- Normal XD video (not in annotations) produces all-zero labels of length N*64.

3. `test_build_frame_arrays_xd_snippet_window` -- Verify snippet_window=64 and upsample_factor=1 are used (n_frames = len(scores) * 64, NOT len(scores) * 64 * 10).

4. `test_build_frame_arrays_xd_categories` -- Verify cats_map contains correct XD category codes (e.g., "Fighting" for _label_B1 suffix).

Each test should:
- Write a minimal Wu-format annotation file to tmp_path
- Monkeypatch `_PROJECT_ROOT` to tmp_path
- Call `_build_frame_arrays` with `cfg={"dataset": "xd", "paths": {"annotations_dir": str(ann_dir)}}`
- Assert on frames_map lengths, labels_map content, cats_map values
  </action>
  <verify>
    <automated>cd D:/ViolenceCC && C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_evaluate_xd.py -v --tb=short 2>&1 | head -40</automated>
  </verify>
  <acceptance_criteria>
    - data/splits/xd_train.txt first line is `# Excluded: v=8cTqh9tMz_I__#1_label_A (corrupt MP4, missing moov atom)`
    - data/splits/xd_train.txt second line is `# Excluded: v=Gm73TwtUyGY__#1_label_G-0-0 (34 frames, below 64-frame window)`
    - data/splits/xd_train.txt does NOT contain the string `v=8cTqh9tMz_I__#1_label_A` as a non-comment line
    - data/splits/xd_train.txt does NOT contain the string `v=Gm73TwtUyGY__#1_label_G-0-0` as a non-comment line
    - data/splits/xd_train.txt total non-comment non-empty lines = 3358
    - src/data/dataset.py contains `not line.strip().startswith("#")` in _load_split
    - src/evaluate.py contains `elif ds == "xd":` between `if ds == "xd_i3d":` and the UCF path
    - src/evaluate.py XD fusion branch has `snippet_window = 64` and `upsample_factor = 1`
    - src/evaluate.py XD fusion branch calls `parse_xd_annotations` (not `parse_annotations`)
    - src/evaluate.py XD fusion branch calls `xd_frame_labels` (not `frame_labels`)
    - tests/test_evaluate_xd.py contains `test_build_frame_arrays_xd_abnormal`
    - tests/test_evaluate_xd.py contains `test_build_frame_arrays_xd_normal`
    - `pytest tests/test_evaluate_xd.py` exits 0 with all tests passing
    - `pytest tests/test_evaluate_xd_i3d.py` still exits 0 (no regression)
    - `pytest tests/test_evaluate_cli.py` still exits 0 (no regression)
  </acceptance_criteria>
  <done>XD split cleaned, _load_split handles comments, evaluate.py correctly routes dataset=xd to XD annotations with snippet_window=64/upsample=1, 4+ new tests pass, existing evaluate tests pass.</done>
</task>

<task type="auto">
  <name>Task 2: Create 6 XD YAML configs + 3 orchestration queues + update tests</name>
  <files>configs/skeleton_only_xd.yaml, configs/clip_only_xd.yaml, configs/late_fusion_xd.yaml, configs/gated_fusion_xd.yaml, configs/gated_fusion_xd_2person.yaml, configs/gated_fusion_xd_clip_mean.yaml, scripts/run_ablations.py, tests/test_run_ablations.py</files>
  <read_first>
    - configs/skeleton_only.yaml (full template -- 39 lines)
    - configs/clip_only.yaml (full template -- 40 lines)
    - configs/late_fusion.yaml (full template -- 42 lines)
    - configs/gated_fusion.yaml (full template -- 41 lines)
    - configs/gated_fusion_2person.yaml (full template -- 45 lines)
    - configs/gated_fusion_clip_mean.yaml (full template -- 44 lines)
    - scripts/run_ablations.py (lines 82-113: existing QUEUES dict; line 275: argparse choices)
    - tests/test_run_ablations.py (lines 42-57: test_queue_definitions with assertion counts)
  </read_first>
  <action>
**Part A -- Create 6 XD YAML configs (per D-01, D-04):**

Each XD config is a copy of its UCF counterpart with exactly these field swaps:

| Field | UCF Value | XD Value |
|-------|-----------|----------|
| `dataset` | `ucf` | `xd` |
| `paths.skeleton_features` | `"E:/features/ucf/skeleton"` | `"E:/features/xd/skeleton"` |
| `paths.clip_features` | `"E:/features/ucf/clip"` | `"E:/features/xd/clip"` |
| `wandb.tags` | `[phaseN, <variant>, ucf]` | `[phase4c, <variant>, xd]` |
| Header comment | references UCF/MOD-XX | references XD-Violence/Phase 4c |

All `model:`, `data:`, and `train:` sections remain byte-identical to UCF counterparts (D-04: identical hyperparameters, no per-dataset tuning).

**1. configs/skeleton_only_xd.yaml:**
```yaml
# configs/skeleton_only_xd.yaml
# Phase 4c: XD-Violence Skeleton-Only MIL baseline. Mirrors skeleton_only.yaml with XD paths.
seed: 42
dataset: xd

paths:
  skeleton_features: "E:/features/xd/skeleton"
  clip_features: "E:/features/xd/clip"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: skeleton_only
  skel_dim: 256
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32
  batch_size: 16
  num_workers: 4
  pin_memory: true

train:
  lr: 1.0e-4
  weight_decay: 1.0e-2
  epochs: 50
  warmup_epochs: 5
  patience: 10
  k_topk: 3
  margin: 1.0
  lam_sparse: 8.0e-3
  lam_smooth: 8.0e-4

wandb:
  project: violencecc
  mode: disabled
  tags: [phase4c, skeleton_only, xd]
```

**2. configs/clip_only_xd.yaml:** Copy `clip_only.yaml`, apply same 4-field swap. Header: `# Phase 4c: XD-Violence CLIP-Only MIL baseline.` Model block has `variant: clip_only`, `clip_dim: 1024`, `proj_dim: 512`. Tags: `[phase4c, clip_only, xd]`.

**3. configs/late_fusion_xd.yaml:** Copy `late_fusion.yaml`, apply same 4-field swap. Header: `# Phase 4c: XD-Violence Late Fusion baseline.` Model block has `variant: late_fusion`, `skel_dim: 256`, `clip_dim: 1024`, `proj_dim: 512`, `alpha: equal`. Tags: `[phase4c, late_fusion, xd]`.

**4. configs/gated_fusion_xd.yaml:** Copy `gated_fusion.yaml`, apply same 4-field swap. Header: `# Phase 4c: XD-Violence Gated Fusion (primary thesis model).` Model block has `variant: gated_fusion`, `skel_dim: 256`, `clip_dim: 1024`, `shared_dim: 256`. Tags: `[phase4c, gated_fusion, xd]`.

**5. configs/gated_fusion_xd_2person.yaml:** Copy `gated_fusion_2person.yaml` with these changes:
- Header: `# Phase 4c D-22 XD: 2-person multi-person aggregation ablation (concat only).`
- `dataset: xd`
- `paths.skeleton_features: "E:/features/xd/skeleton_2person"`
- `paths.clip_features: "E:/features/xd/clip"`
- `model.skel_dim: 512` (concat of 2 persons, same as UCF 2person)
- `data.skel_agg: concat`
- `wandb.tags: [phase4c, gated_fusion, xd, 2person]`

**6. configs/gated_fusion_xd_clip_mean.yaml:** Copy `gated_fusion_clip_mean.yaml` with these changes:
- Header: `# Phase 4c D-23 XD: CLIP mean-only pooling ablation.`
- `dataset: xd`
- `paths.skeleton_features: "E:/features/xd/skeleton"`
- `paths.clip_features: "E:/features/xd/clip_mean"`
- `model.clip_dim: 512` (mean-only, same as UCF clip_mean)
- `wandb.tags: [phase4c, gated_fusion, xd, clip_mean]`

**Part B -- Add 3 new queues to scripts/run_ablations.py (per D-02):**

Append 3 new entries to the QUEUES dict (after the closing of `phase4_seeds` at line 112, before the `}` at line 113):

```python
    "phase4c_main": [
        RunSpec("xd", "skeleton_only", 42, "configs/skeleton_only_xd.yaml"),
        RunSpec("xd", "clip_only",     42, "configs/clip_only_xd.yaml"),
        RunSpec("xd", "late_fusion",   42, "configs/late_fusion_xd.yaml"),
        RunSpec("xd", "gated_fusion",  42, "configs/gated_fusion_xd.yaml"),
    ],
    "phase4c_pooling": [
        RunSpec(
            "xd", "gated_fusion", 42,
            "configs/gated_fusion_xd_2person.yaml", "2person",
        ),
        RunSpec(
            "xd", "gated_fusion", 42,
            "configs/gated_fusion_xd_clip_mean.yaml", "clip_mean",
        ),
    ],
    "phase4c_seeds": [
        RunSpec("xd", "gated_fusion", 123, "configs/gated_fusion_xd.yaml"),
        RunSpec("xd", "gated_fusion", 2024, "configs/gated_fusion_xd.yaml"),
        # seed=42 covered by phase4c_main; not duplicated per D-27/D-28.
    ],
```

Update the help string on `--queue` argument (line 276) to include the new queue names:
```python
help="Queue to run: rtfm_gate, phase4_main, phase4_pooling, phase4_seeds, phase4c_main, phase4c_pooling, phase4c_seeds",
```

Note: `choices=sorted(QUEUES)` is dynamic and auto-discovers new keys. Only the help string needs updating.

**Part C -- Update tests/test_run_ablations.py:**

Update `test_queue_definitions` to include Phase 4c queues:
- Add assertions: `assert len(QUEUES["phase4c_main"]) == 4`
- Add assertions: `assert len(QUEUES["phase4c_pooling"]) == 2`
- Add assertions: `assert len(QUEUES["phase4c_seeds"]) == 2`
- Update total unique run_names assertion from 10 to 18 (10 existing + 8 new Phase 4c specs).
- Add run_name spot checks for Phase 4c:
  - `assert QUEUES["phase4c_main"][3].run_name == "xd_gated_fusion_s42"`
  - `assert QUEUES["phase4c_seeds"][0].run_name == "xd_gated_fusion_s123"`
  - `assert QUEUES["phase4c_pooling"][0].run_name == "xd_gated_fusion_2person_s42"`

Update `test_help_has_expected_queues` to also check for `"phase4c_main"`, `"phase4c_pooling"`, `"phase4c_seeds"` in --help output.
  </action>
  <verify>
    <automated>cd D:/ViolenceCC && C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_run_ablations.py -v --tb=short 2>&1 | head -30</automated>
  </verify>
  <acceptance_criteria>
    - configs/skeleton_only_xd.yaml contains `dataset: xd`
    - configs/skeleton_only_xd.yaml contains `skeleton_features: "E:/features/xd/skeleton"`
    - configs/clip_only_xd.yaml contains `dataset: xd` and `clip_dim: 1024`
    - configs/late_fusion_xd.yaml contains `dataset: xd` and `alpha: equal`
    - configs/gated_fusion_xd.yaml contains `dataset: xd` and `shared_dim: 256`
    - configs/gated_fusion_xd_2person.yaml contains `skeleton_features: "E:/features/xd/skeleton_2person"` and `skel_dim: 512` and `skel_agg: concat`
    - configs/gated_fusion_xd_clip_mean.yaml contains `clip_features: "E:/features/xd/clip_mean"` and `clip_dim: 512`
    - All 6 XD configs have `wandb.tags` containing `phase4c` and `xd`
    - All 6 XD configs have identical `train:` block values to their UCF counterparts (lr=1.0e-4, epochs=50, patience=10, k_topk=3, batch_size=16)
    - scripts/run_ablations.py QUEUES dict contains keys `phase4c_main`, `phase4c_pooling`, `phase4c_seeds`
    - `phase4c_main` has 4 RunSpec entries with dataset="xd"
    - `phase4c_pooling` has 2 RunSpec entries with cache_variant "2person" and "clip_mean"
    - `phase4c_seeds` has 2 RunSpec entries with seeds 123 and 2024
    - tests/test_run_ablations.py asserts `len(all_run_names) == 18`
    - `pytest tests/test_run_ablations.py` exits 0 with all tests passing
  </acceptance_criteria>
  <done>6 XD YAML configs created matching UCF hyperparameters (D-01, D-04), 3 queues registered in run_ablations.py (D-02), test assertions updated for 18 total unique specs, all tests pass.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem -> split loader | Split file content parsed as video IDs; comment lines now skipped |
| filesystem -> YAML config | Config paths point to feature directories on E:/ drive |
| filesystem -> annotation parser | Wu annotation file parsed for frame-level labels |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4c-01 | Tampering | data/splits/xd_train.txt | accept | Split files are committed to git; any tampering is visible in diff. Comment lines are documentation only. |
| T-4c-02 | Information Disclosure | configs/*_xd.yaml | accept | Configs contain local filesystem paths (E:/features/); no PII, no secrets. Research codebase, not deployed. |
| T-4c-03 | Elevation of Privilege | src/evaluate.py np.load | mitigate | np.load called WITHOUT allow_pickle=True (existing pattern); refuses to deserialize Python objects from .npy cache. |
| T-4c-04 | Denial of Service | scripts/run_ablations.py subprocess timeout | mitigate | Existing 7200s timeout on train subprocess, 600s minimum on eval subprocess (lines 149, 188). No change needed. |
</threat_model>

<verification>
1. All 6 XD config files exist in configs/ and load without YAML parse error
2. `pytest tests/test_evaluate_xd.py tests/test_evaluate_xd_i3d.py tests/test_evaluate_cli.py tests/test_run_ablations.py -v` exits 0
3. `grep -c "dataset: xd" configs/*_xd.yaml` returns 6 matches
4. `grep -c "phase4c_main\|phase4c_pooling\|phase4c_seeds" scripts/run_ablations.py` returns 3+ matches
5. `wc -l data/splits/xd_train.txt` returns 3360 (2 comment lines + 3358 video IDs)
</verification>

<success_criteria>
- All code and config changes committed, no runtime errors
- evaluate.py correctly routes dataset=xd to XD annotations (not UCF annotations)
- All existing tests pass (no regression)
- All new tests pass
- Plan 04C-02 can invoke `run_ablations.py --queue phase4c_main` without code changes
</success_criteria>

<output>
After completion, create `.planning/phases/04C-xd-violence-main-results/04C-01-SUMMARY.md`
</output>
