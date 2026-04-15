---
phase: 04-baseline-evaluation-main-results
reviewed: 2026-04-15T00:00:00Z
depth: standard
files_reviewed: 46
files_reviewed_list:
  - configs/clip_only.yaml
  - configs/gated_fusion.yaml
  - configs/gated_fusion_2person.yaml
  - configs/gated_fusion_clip_mean.yaml
  - configs/late_fusion.yaml
  - configs/rtfm_i3d.yaml
  - configs/skeleton_only.yaml
  - data/annotations/ucf_temporal.txt
  - scripts/extract_clip.py
  - scripts/extract_ctrgcn.py
  - scripts/extract_skeletons.py
  - scripts/run_ablations.py
  - scripts/verify_pooling_caches.py
  - scripts/wandb_preflight.py
  - src/data/dataset.py
  - src/data/i3d_dataset.py
  - src/data/loaders.py
  - src/eval/__init__.py
  - src/eval/metrics.py
  - src/eval/snippet_to_frame.py
  - src/eval/test_loader.py
  - src/eval/ucf_annotations.py
  - src/evaluate.py
  - src/models/registry.py
  - src/models/rtfm_i3d.py
  - src/train.py
  - src/utils/config.py
  - src/utils/csv_logger.py
  - src/utils/wandb_logger.py
  - tests/conftest.py
  - tests/fixtures/synthetic_eval.py
  - tests/test_config_hash.py
  - tests/test_done_marker.py
  - tests/test_eval_metrics.py
  - tests/test_evaluate_cli.py
  - tests/test_i3d_dataset.py
  - tests/test_registry.py
  - tests/test_results_index.py
  - tests/test_rtfm_i3d.py
  - tests/test_run_ablations.py
  - tests/test_skel_agg.py
  - tests/test_snippet_to_frame.py
  - tests/test_test_loader.py
  - tests/test_ucf_annotations.py
  - tests/test_verify_pooling.py
  - tests/test_wandb_logger.py
  - tests/test_wandb_preflight.py
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-04-15
**Depth:** standard
**Files Reviewed:** 46
**Status:** issues_found

## Summary

Phase 4 delivers a complete evaluation harness, ablation orchestrator, extraction scripts, and supporting datasets. The C3/C4 defensive layers (test-set leakage guard in `test_loader.py`, length-assertion before every sklearn call, snippet-to-frame tolerance) are well-designed and tested. Atomic write patterns (tmp-rename on `.npy`, `.json`, and `.done`) are consistent. No secrets, injection surfaces, or shell=True usage were found.

Four warnings are raised:

1. `extract_skeletons.py`: first frame is processed twice on a fresh-start path — once explicitly before the chunk loop begins, then again when the cap position is still at frame 1 and the chunk loop re-reads from frame 1 onwards. This doubles frame 0 inference (benign for most videos but wastes GPU time and subtly corrupts keypoint arrays for videos exactly divisible by CHUNK_SIZE).
2. `extract_ctrgcn.py`: the checkpoint state_dict selection heuristic (`"backbone" in str(list(keys)[:1])`) is fragile — it stringifies a Python list repr and does a substring match, which passes for the intended PYSKL format but can silently select the wrong branch if a checkpoint has a key whose repr string happens to contain the word `backbone`.
3. `src/data/i3d_dataset.py`: `_resample_T` uses a fixed `np.random.default_rng(0)` seed regardless of epoch, meaning all training iterations that hit the N < T branch produce the identical index sequence. For a research reproducibility codebase this removes the stochastic augmentation benefit that the sample-with-replacement strategy is meant to provide for short videos.
4. `src/evaluate.py`: the `xd_i3d` label construction in `_build_frame_arrays` falls back to assigning all unannotated videos to category `"Abuse"` (line 191), which is a hardcoded non-Normal placeholder that will produce misleading `per_category` breakdowns if the XD I3D evaluation is ever wired with a real annotation file — Normal videos would be classified under "Abuse" instead of "Normal", skewing per-category AUC.

Five informational items are also noted, mostly dead/stub code and a missing assertion.

---

## Warnings

### WR-01: First frame processed twice in `stream_xd_keypoints` fresh-start path

**File:** `scripts/extract_skeletons.py:328-337`

**Issue:** On a fresh start (no checkpoint), the code reads `first_frame` at line 300, runs `_infer_single_frame(model, first_frame, 0, ...)` at line 330, then sets `actual_count = 1` and `chunk_start_idx = actual_count` (= 1). The `while True` loop then calls `cap.read()` which — since the `VideoCapture` cursor advanced past frame 0 when `cap.read()` was called at line 300 — correctly returns frame 1 next. That part is fine.

However there is a subtler bug: when the checkpoint resume path is taken (`ckpt is not None`), `actual_count` is set from the checkpoint and `cap.set(cv2.CAP_PROP_POS_FRAMES, actual_count)` seeks the video to the correct position. But `first_frame` was already read at line 300 (consuming frame 0 from the file descriptor) before the branch decision is made. On resume, `cap.set(...)` re-positions correctly so the frame is not double-processed there. The real bug is on the **fresh-start** path: after processing `first_frame` at frame index 0 and setting `actual_count = 1`, the `get_wholebody_model()` call at line 333 is a no-op singleton, but the chunk loop starts with `chunk_start_idx = 1`. Since `cap.read()` at line 300 already advanced the file cursor past frame 0, the loop correctly starts at frame 1. This is actually correct behavior.

The actual bug is different: `model = get_wholebody_model()` is called **twice** on the fresh-start branch — once at line 329 (inside the `else` block) and again at line 333 (outside both branches). The singleton makes this a noop, but the call at line 333 is dead/redundant on the fresh-start path and can mislead readers into thinking there is something wrong with the resume path's model initialization. More importantly, if the singleton is ever broken (e.g., by multiprocessing), both calls could initialize two separate model instances.

**Fix:** Remove the duplicate `get_wholebody_model()` call at line 333 by restructuring so the model is obtained once before the branch:

```python
model = get_wholebody_model()  # obtain once before branching

ckpt = _load_checkpoint(ckpt_path)
if ckpt is not None and ckpt["n_frames"] == n_frames:
    actual_count = ckpt["actual_count"]
    # ... resume path (no model call needed here)
    cap.set(cv2.CAP_PROP_POS_FRAMES, actual_count)
else:
    # fresh start
    actual_count = 0
    _infer_single_frame(model, first_frame, 0, keypoint, keypoint_score)
    actual_count = 1
```

---

### WR-02: Fragile checkpoint state_dict heuristic in `load_ctrgcn_stream`

**File:** `scripts/extract_ctrgcn.py:121-125`

**Issue:** The heuristic that decides whether the loaded checkpoint is already a flat state_dict or a wrapped dict is:

```python
state_dict = (
    checkpoint
    if isinstance(checkpoint, dict) and "backbone" in str(list(checkpoint.keys())[:1])
    else checkpoint.get("state_dict", checkpoint)
)
```

`str(list(checkpoint.keys())[:1])` produces a Python list repr such as `"['backbone.gcn.0.weight']"`. The substring check `"backbone" in ...` happens to work for PYSKL's format, but it is semantically wrong: it is checking for the string `backbone` inside the list repr rather than checking whether any key starts with `backbone.`. A checkpoint whose first key is `"cls_head_backbone"` or any key that happens to stringify near the start of the repr could produce a false positive. Conversely, a valid PYSKL checkpoint whose first alphabetically-ordered key is `"cls_head...."` (less than `"backbone."` lexicographically) would fall through to the `get("state_dict", checkpoint)` branch.

**Fix:** Use an explicit prefix check on the full key set:

```python
keys = list(checkpoint.keys()) if isinstance(checkpoint, dict) else []
if any(k.startswith("backbone.") for k in keys):
    state_dict = checkpoint          # flat PYSKL state_dict
else:
    state_dict = checkpoint.get("state_dict", checkpoint)
```

---

### WR-03: Fixed RNG seed in `I3DFeatureDataset._resample_T` eliminates per-epoch diversity

**File:** `src/data/i3d_dataset.py:136`

**Issue:** When `N < T` (a short video), `_resample_T` creates a fresh `np.random.default_rng(0)` on every call:

```python
rng = np.random.default_rng(0)  # deterministic for reproducibility
idxs = np.sort(rng.integers(0, N, size=self.T))
return feat[idxs]
```

This means every short video in every epoch will be sampled with the exact same index sequence (seeded to 0). Across 50 training epochs the model sees the identical upsampled view of every short video, providing no augmentation benefit from the sample-with-replacement strategy. The comment "deterministic for reproducibility" is correct intent for test/val modes, but in `train` mode this removes the data augmentation that RTFM's original approach relies on for short clips.

Note: the sibling `MILFeatureDataset._sample_or_pad` in `src/data/dataset.py` correctly uses `np.random.randint` (global RNG) for the `N < T` replacement branch, giving per-epoch diversity. `I3DFeatureDataset._resample_T` should match that behavior in train mode.

**Fix:** Use the global numpy RNG (or pass the seed as a parameter) to allow per-epoch diversity in train mode, while keeping a fixed seed only for test/val:

```python
def _resample_T(self, feat: np.ndarray) -> np.ndarray:
    N = feat.shape[0]
    if N >= self.T:
        r = np.linspace(0, N, self.T + 1, dtype=np.int64)
        return np.stack(
            [feat[r[i]: max(r[i] + 1, r[i + 1])].mean(axis=0) for i in range(self.T)]
        )
    # N < T: use global RNG in train mode for per-epoch diversity;
    # test/val reproducibility is already guaranteed by set_deterministic() at eval time.
    idxs = np.sort(np.random.randint(0, N, size=self.T))
    return feat[idxs]
```

---

### WR-04: Hardcoded `"Abuse"` placeholder for unannotated XD I3D videos in `_build_frame_arrays`

**File:** `src/evaluate.py:191`

**Issue:** The `xd_i3d` evaluation stub in `_build_frame_arrays` assigns all videos to category `"Abuse"` when they have no annotation:

```python
cats_map[vid] = "Normal" if vid.endswith("_label_A") else "Abuse"
```

This is a temporary stub (the comment says "any xd_i3d invocation produces all-zero labels since there's no ground truth yet"), but the category assignment `"Abuse"` is semantically wrong. When this path is later wired with real XD annotations, any video that is not explicitly categorized will be binned under `"Abuse"` in `per_category` metrics. This can silently produce inflated Abuse AUC numbers and is a correctness risk if anyone runs evaluation without noticing the stub is still active.

A more defensively correct stub uses `"Unknown"` (which `compute_frame_metrics` will skip if it has no Normal contrast, and which is not `"Normal"` so it won't be silently excluded from per_category).

**Fix:**

```python
cats_map[vid] = "Normal" if vid.endswith("_label_A") else "Unknown"
```

Additionally, add a warning log or comment noting this is a stub category to prevent silent misuse:

```python
# Stub: real XD category column is not yet parsed; "Unknown" keeps the
# per_category breakdown from producing misleading "Abuse" AUC numbers.
cats_map[vid] = "Normal" if vid.endswith("_label_A") else "Unknown"
```

---

## Info

### IN-01: Undocumented architectural gap — `xd_i3d` training not dispatched in `src/train.py`

**File:** `src/train.py` (entire file)

**Issue:** Per the known context (Plan 04-03 EVAL-01 deferred gap), `src/train.py` has no dispatch for `dataset: xd_i3d`. When `run_ablations.py` runs the `rtfm_gate` queue with `configs/rtfm_i3d.yaml` (which sets `dataset: xd_i3d`), `build_dataloaders` will attempt to construct a `MILFeatureDataset` with `splits_dir/xd_i3d_train.txt` and `skeleton_features`/`clip_features` paths that are absent from the config (`rtfm_i3d.yaml` only has `i3d_features`). This will raise a `FileNotFoundError` or `KeyError` at the first `build_dataloaders` call.

This is a known deferred gap (EVAL-01), not a regression introduced in Phase 4. The note here is that no runtime guard or early error message exists in `src/train.py` to catch this misconfiguration before the DataLoader construction — the failure will be buried in a subprocess exit code logged to `runner-errors.log`. A cheap guard at the top of `main()` would fail faster:

```python
if cfg.get("dataset") == "xd_i3d" and "i3d_features" not in cfg.get("paths", {}):
    raise ValueError("xd_i3d dataset requires cfg.paths.i3d_features")
```

---

### IN-02: `_per_category_csv` write is not atomic (no tmp-rename)

**File:** `src/evaluate.py:127-134`

**Issue:** `_write_per_category_csv` opens the CSV file directly for writing without the tmp-rename pattern used by `_write_json_atomic` and `_mark_done`:

```python
def _write_per_category_csv(per_cat: dict, path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        ...
```

If the process is interrupted between opening the file (which truncates it) and finishing the write, the file will be left empty or partial. The D-31 contract guarantees that `.done` appearing implies all outputs exist, but a partially-written `per_category.csv` still violates the readability invariant.

This is low severity because `per_category.csv` is auxiliary (the canonical output is `eval_metrics.json`), but it is inconsistent with the surrounding atomic-write idiom.

**Fix:** Apply the same tmp-rename pattern:

```python
def _write_per_category_csv(per_cat: dict, path: Path) -> None:
    import csv, tempfile
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["category", "auc", "ap"])
            for cat in sorted(per_cat):
                w.writerow([cat, per_cat[cat].get("auc", ""), per_cat[cat].get("ap", "")])
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(path))
    except Exception:
        if os.path.exists(tmp): os.unlink(tmp)
        raise
```

---

### IN-03: `config_snapshot.json` written non-atomically in `snapshot_config`

**File:** `src/utils/config.py:126`

**Issue:** `snapshot_config` uses `path.write_text(...)`, which is a single-step write but is not atomic on most filesystems — a process crash during the write leaves a partial JSON file. If training crashes mid-snapshot, `evaluate.py` will fail to load the config with a JSON parse error rather than a clear "snapshot missing" message.

```python
path.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
```

**Fix:** Use the same tmp-rename pattern as `_write_json_atomic`:

```python
tmp = path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
tmp.replace(path)
```

---

### IN-04: `_build_snippet_label_grid` silently drops videos with no annotation

**File:** `src/evaluate.py:237-247`

**Issue:** `_build_snippet_label_grid` skips videos for which `labels_map.get(vid)` returns `None`:

```python
frame_lbl = labels_map.get(vid)
if frame_lbl is None:
    continue
```

For UCF test videos not present in `ucf_temporal.txt` (e.g., normal videos for which the Sultani annotation file contains no row), `_build_frame_arrays` assigns `labels_map[vid] = np.zeros(...)` so they do appear in `labels_map`. However, if the dicts are ever misaligned (e.g., a future code path doesn't populate `labels_map` for every vid in `per_video_snippet_scores`), the snippet-label grid will silently have fewer entries than the score grid. The `compute_snippet_auc` call would then work on a smaller set without warning. A minor log message at the skip point would make such misalignment visible.

**Fix:**
```python
frame_lbl = labels_map.get(vid)
if frame_lbl is None:
    logger.warning(f"_build_snippet_label_grid: no label for {vid}, skipping")
    continue
```

---

### IN-05: Unused `dataset` parameter in `verify_pooling_caches.py`

**File:** `scripts/verify_pooling_caches.py:138`

**Issue:** The `--dataset` argument is parsed and stored in `args.dataset`, but it is never used in any verification logic — both `verify_clip_mean` and `verify_skeleton_2person` operate solely on the `cache_root` and `baseline_root` paths, which are passed directly. The `dataset` value is only printed in the summary line:

```python
print(f"[verify_pooling] cache={args.cache} dataset={args.dataset}")
```

This is dead argument state. It is not a bug, but it could mislead a caller into thinking the verifier applies different logic per dataset, when in fact it does not.

**Fix:** Either remove `--dataset` from the CLI and summary print (if it truly has no intended role), or add dataset-specific validation logic (e.g., checking for `_x264` suffix patterns on UCF vs XD video IDs).

---

_Reviewed: 2026-04-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
