---
phase: 02-feature-extraction-pipeline
plan: 01
subsystem: data-pipeline
tags: [sklearn, rtmlib, onnxruntime, rtmpose, pyskl, coco17, ucf-crime, xd-violence, split-files, skeleton-extraction]

requires:
  - phase: 01-environment
    provides: vcc-skeleton conda env with rtmlib+onnxruntime-gpu, UCF-Crime/XD-Violence datasets at E:/ drive

provides:
  - 6 committed split text files in data/splits/ (ucf: 1368/242/290 train/val/test, xd: 3360/594/800)
  - scripts/create_splits.py: stratified 85/15 train/val split with seed=42, reproducibility check
  - scripts/extract_skeletons.py: RTMPose -> PYSKL pickle + snippet boundary JSON pipeline
  - tests/test_splits.py: 9 tests covering file existence, no-overlap, val fraction, reproducibility
  - E:/skeletons/ucf/*.pkl: validated PYSKL pickle files (3 Abuse videos)
  - E:/snippets/ucf/*_boundaries.json: snippet boundary JSON files for CLIP alignment

affects: [02-02-clip-extraction, 02-03-ctrgcn-extraction, 02-04-alignment-verification, 03-model-architecture]

tech-stack:
  added:
    - sklearn.model_selection.StratifiedShuffleSplit (split creation)
    - rtmlib.Wholebody (RTMPose inference, mode=balanced, 133-keypoint wholebody)
    - onnxruntime-gpu (backend for RTMPose ONNX models, fell back to CPU due to cuDNN path)
    - decord (XD-Violence mp4 decoding, with cv2 fallback)
  patterns:
    - XD-Violence anomaly labels extracted from filename suffix (_label_A=normal, B/G=anomalous)
    - Skip-if-exists resume strategy for long-running extraction jobs
    - Shared snippet boundary JSON as alignment contract between skeleton and CLIP scripts
    - PreNormalize2D applied as assertion-only in extract_skeletons.py (pixels stored in pickle, normalization done in CTR-GCN script)
    - Wholebody mode=balanced used instead of pose='rtmpose-m' (rtmlib uses mode strings, not pose name strings)

key-files:
  created:
    - scripts/create_splits.py
    - data/splits/ucf_train.txt
    - data/splits/ucf_val.txt
    - data/splits/ucf_test.txt
    - data/splits/xd_train.txt
    - data/splits/xd_val.txt
    - data/splits/xd_test.txt
    - tests/test_splits.py
    - scripts/extract_skeletons.py
  modified:
    - tests/conftest.py (added splits_dir fixture)

key-decisions:
  - "XD-Violence anomaly labels come from filename suffix (_label_A=normal, B*/G*=anomalous), NOT from XD_violence_annotations.txt which is a frame-level temporal annotation file for a subset of videos"
  - "rtmlib Wholebody uses mode='balanced' (not pose='rtmpose-m') — mode string drives model selection"
  - "UCF-Crime frames are 64x64 pixels (pre-extracted at this resolution), not original HD resolution"
  - "onnxruntime-gpu falls back to CPU when cuDNN 9.x is not in system PATH (DLL load fails silently)"
  - "Snippet boundaries written to E:/snippets/ as shared contract for CLIP script alignment"

patterns-established:
  - "Split files: plain text, one video ID per line, sorted alphabetically, committed to data/splits/"
  - "PYSKL pickle format: {'keypoint': [2,T,17,2], 'keypoint_score': [2,T,17], 'img_shape': (H,W), 'total_frames': T, 'video_id': str}"
  - "Boundary JSON format: {video_id, total_frames, frames_per_snippet: 64, snippet_frame_ranges: [[start,end],...], n_snippets, img_shape: [H,W]}"
  - "Top-2 person selection by mean confidence across 17 COCO-17 keypoints"
  - "Zero-padding for <2 detected persons (D-07, D-08)"

requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04]

duration: 14min
completed: 2026-04-03
---

# Phase 02 Plan 01: Dataset Splits and Skeleton Extraction Summary

**Stratified train/val/test split files committed for UCF-Crime (1368/242/290) and XD-Violence (3360/594/800), plus RTMPose skeleton extraction pipeline validated on 3 UCF-Crime videos producing PYSKL-compatible pickles and snippet boundary JSONs**

## Performance

- **Duration:** ~14 min (includes rtmlib model download ~300MB + 3-video extraction run)
- **Started:** 2026-04-03T20:51:22Z
- **Completed:** 2026-04-03T21:05:59Z
- **Tasks:** 2
- **Files modified:** 10 (9 created, 1 modified)

## Accomplishments
- 6 split text files generated and committed with correct stratified 15% val split (seed=42)
- XD-Violence labels correctly extracted from filename suffix (not annotation file)
- RTMPose skeleton extraction validated on 3 UCF-Crime Abuse videos: keypoint shapes [2,T,17,2] confirmed, snippet boundaries [floor(T/64)] confirmed, coordinates within [-2,2]
- 9 pytest tests cover all split file correctness requirements including byte-identical reproducibility
- Snippet boundary JSON files establish alignment contract for downstream CLIP extraction

## Task Commits

Each task was committed atomically:

1. **Task 1: Create split files for UCF-Crime and XD-Violence** - `548d441` (feat)
2. **Task 2: Build skeleton extraction script with snippet boundary output** - `0e2f2b9` (feat)

**Plan metadata:** (committed with docs commit below)

## Files Created/Modified
- `scripts/create_splits.py` - Stratified split generation with --verify flag for reproducibility check
- `data/splits/ucf_train.txt` - 1368 UCF-Crime training video IDs
- `data/splits/ucf_val.txt` - 242 UCF-Crime validation video IDs (15% stratified by category)
- `data/splits/ucf_test.txt` - 290 UCF-Crime test video IDs
- `data/splits/xd_train.txt` - 3360 XD-Violence training video IDs
- `data/splits/xd_val.txt` - 594 XD-Violence validation video IDs (15% stratified by label)
- `data/splits/xd_test.txt` - 800 XD-Violence test video IDs
- `tests/test_splits.py` - 9 split validation tests
- `tests/conftest.py` - Added splits_dir fixture
- `scripts/extract_skeletons.py` - RTMPose skeleton extraction with snippet boundary output

## Decisions Made
- XD-Violence anomaly labels extracted from filename suffix not annotation file: `_label_A` = normal, `_label_B*` or `_label_G*` = anomalous. The `XD_violence_annotations.txt` file contains frame-level temporal annotations for a subset of anomalous videos — it does NOT serve as a complete label list. This was discovered during Task 1 when annotation-based matching yielded 0 matches.
- rtmlib `Wholebody` uses `mode='balanced'` parameter, not `pose='rtmpose-m'` as specified in the plan. The `mode` string drives model selection; `pose` parameter only works with direct URL strings.
- UCF-Crime pre-extracted PNGs are 64x64 pixels (confirmed by cv2.imread shape check). `img_shape=(64,64)` in pickles is correct.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] XD-Violence annotation-based label matching yielded 0 anomalous videos**
- **Found during:** Task 1 (XD-Violence split generation)
- **Issue:** The annotation file `XD_violence_annotations.txt` has 499 entries (temporal frame annotations for a subset of videos), but the 3954 training video stems do not match any annotation keys — they are from different unique YouTube IDs. Zero annotation matches meant all 3954 videos would be labeled as normal, making the stratified split meaningless.
- **Fix:** Replaced annotation-based labeling with filename-suffix-based labeling: `_label_A` suffix = normal (2049 videos), any `_label_B*` or `_label_G*` suffix = anomalous (1905 videos). This is the canonical XD-Violence labeling convention.
- **Files modified:** scripts/create_splits.py (replaced `parse_xd_annotations()` with `xd_is_anomalous()`)
- **Verification:** XD-Violence split now shows Normal: 2049, Anomalous: 1905. Stratified split produces correct 15% val fraction with proper anomaly ratio.
- **Committed in:** 548d441 (Task 1 commit)

**2. [Rule 1 - Bug] rtmlib Wholebody `pose='rtmpose-m'` parameter is not a valid mode string**
- **Found during:** Task 2 implementation (reviewing rtmlib API)
- **Issue:** Plan specified `Wholebody(pose='rtmpose-m', mode='lightweight')` but rtmlib's Wholebody.MODE only accepts {'performance', 'lightweight', 'balanced'} — not model name strings. Passing `pose='rtmpose-m'` would be passed as a URL to download which would fail.
- **Fix:** Used `Wholebody(mode='balanced', backend='onnxruntime', device='cuda')` — `balanced` uses RTMWholebody-DW-X-L (133 keypoints). Taking first 17 gives standard COCO-17 body joints.
- **Files modified:** scripts/extract_skeletons.py
- **Verification:** Script ran successfully on 3 UCF-Crime videos with valid 17-keypoint output.
- **Committed in:** 0e2f2b9 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both auto-fixes required for correctness. XD-Violence split would have been unusable without the label fix. Skeleton extraction would have failed without the rtmlib API fix.

## Issues Encountered
- onnxruntime-gpu CUDA provider fails to load in vcc-skeleton env (cuDNN 9.* DLLs not on system PATH). RTMPose ran on CPU ONNX backend instead of GPU. Extraction still works but is ~10x slower. This is a known environment issue (CLAUDE.md ISSUE 2). CPU processing of 3 videos took ~5 minutes. Full UCF-Crime extraction (~1610 videos) will take many hours on CPU — **cuDNN 9.x PATH fix required before full extraction run.**
- rtmlib model weights automatically downloaded (~300MB total) from mmpose CDN on first run. Subsequent runs use cached models at `C:/Users/Austin/.cache/rtmlib/hub/checkpoints/`.

## Known Stubs
None — all data written to E:/ drive is real extracted content. Split files are complete and production-ready.

## Next Phase Readiness
- Split files ready: all 6 files committed and tested, reproducibility verified
- Skeleton extraction script complete: validated on UCF-Crime Abuse videos
- BLOCKER: cuDNN 9.x must be added to PATH in vcc-skeleton env before full-scale extraction (onnxruntime-gpu CUDA provider currently falls back to CPU)
- Plan 02 (CLIP extraction) can begin writing script without waiting for full skeleton extraction
- Plan 03 (CTR-GCN extraction) depends on skeleton pickles being available

---
*Phase: 02-feature-extraction-pipeline*
*Completed: 2026-04-03*
