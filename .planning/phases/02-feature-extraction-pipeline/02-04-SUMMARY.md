---
phase: 02-feature-extraction-pipeline
plan: 04
subsystem: data-pipeline
tags: [xd-violence, skeleton, ctrgcn, clip, smoke-test, full-extraction, decord, cv2-fallback]

requires:
  - phase: 02-feature-extraction-pipeline
    plan: 03
    provides: verify_alignment.py + UCF-Crime extraction complete

provides:
  - XD-Violence smoke test: 3 videos verified, pipeline works end-to-end
  - Full extraction commands: documented for user execution (10-20h total)
  - scripts: all 3 extraction scripts confirmed compatible with XD-Violence mp4/decord

affects: [03-model-architecture]

tech-stack:
  added: []
  patterns:
    - decord not available in vcc-skeleton; cv2.VideoCapture fallback works for XD-Violence mp4 loading
    - conda run captures tqdm unicode block chars which cause cp950 UnicodeEncodeError on Windows; scripts work fine, just conda wrapper fails on stdout capture
    - Direct python execution (C:/Anaconda/envs/vcc-main/python.exe script.py) bypasses conda stdout capture and works cleanly
    - XD-Violence extraction rate ~66s/video GPU skeleton, ~3s/video CLIP; total ~10-20h

key-files:
  created:
    - scripts/_verify_smoke.py (temporary helper, not committed)
  modified:
    - scripts/extract_skeletons.py (stdout reconfigure + val routing bug fix)
    - scripts/extract_ctrgcn.py (stdout reconfigure)
    - scripts/extract_clip.py (stdout reconfigure + val routing bug fix)

key-decisions:
  - "decord not installed in vcc-skeleton; cv2.VideoCapture fallback is sufficient for XD-Violence mp4 decoding"
  - "Smoke test (--limit 3) is sufficient to validate XD-Violence pipeline before committing to 10-20h full extraction"
  - "conda run unicode issue is cosmetic — scripts succeed, only conda stdout wrapper fails on tqdm output"
  - "XD-Violence val split videos are in XD_TRAIN_ROOT (train/), not XD_TEST_ROOT (test/videos/); both train and val route to train folder"

metrics:
  duration: 15min
  completed: "2026-04-05T11:04:18Z"
  started: "2026-04-05T10:49:00Z"
  tasks: 1 (Task 2 is checkpoint:human-verify)
  files_modified: 3
---

# Phase 02 Plan 04: XD-Violence Full Extraction Summary

**XD-Violence smoke test passed on 3 videos (skeleton [N,256] + CLIP [N,1024], aligned), decord fallback to cv2 confirmed working, full extraction commands documented for user to run (10-20h total)**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-05T10:49:00Z
- **Completed:** 2026-04-05T11:04:18Z
- **Tasks:** 1 complete (Task 2 is checkpoint:human-verify)
- **Files modified:** 3 scripts (stdout reconfigure additions)

## Accomplishments

- Validated XD-Violence end-to-end pipeline on 3 smoke test videos
  - Stage 1 (skeleton): cv2.VideoCapture fallback works (decord not in vcc-skeleton env)
  - Stage 2 (CTR-GCN): 3 skeleton .npy files produced [N,256] float32
  - Stage 3 (CLIP): 3 CLIP .npy files produced [N,1024] float32
  - Alignment: all 3 videos PASS (snippets match, no NaN/Inf, positive variance)
- Sample results:
  - `A.Beautiful.Mind.2001__#00-01-45_00-02-50_label_A`: skel=(24,256), clip=(24,1024) PASS
  - `A.Beautiful.Mind.2001__#00-04-20_00-05-35_label_A`: skel=(28,256), clip=(28,1024) PASS
  - `A.Beautiful.Mind.2001__#00-05-52_00-08-22_label_A`: skel=(56,256), clip=(56,1024) PASS
- Added `sys.stdout.reconfigure(line_buffering=True)` to extract_skeletons.py and extract_ctrgcn.py (they already existed in extract_clip.py)

## Task Commits

1. **Task 1: XD-Violence smoke test + script improvements** — `1a233ef` (feat)
2. **Val path bug fix** — `faa1c86` (fix)

## Files Created/Modified

- `scripts/extract_skeletons.py` — sys.stdout/stderr.reconfigure added for conda run compat
- `scripts/extract_ctrgcn.py` — sys.stdout/stderr.reconfigure added for conda run compat
- `scripts/extract_clip.py` — sys.stdout/stderr.reconfigure added for conda run compat

## Full Extraction Commands (User Must Run)

The full XD-Violence extraction requires ~10-20h and cannot run within an agent session. Run these commands sequentially:

### Stage 1: Skeleton Extraction (vcc-skeleton) — ~10-15h

```bash
# Train (3360 videos, ~66s/video on GPU = ~60h theoretical, but many are short clips)
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset xd --split train

# Val (594 videos — subsets of train, same videos)
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset xd --split val

# Test (800 videos in E:\XD_Violence\test\videos\ subfolder)
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset xd --split test
```

Note: val videos are subsets of the train folder. The val routing bug (faa1c86) has been
fixed — both train and val now route to XD_TRAIN_ROOT (E:\XD_Violence\train\). Only test
split uses XD_TEST_ROOT (E:\XD_Violence\test\videos\).

### Stage 2: CTR-GCN Feature Extraction (vcc-ctrgcn) — ~1-2h

Run after Stage 1 completes for each split:

```bash
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset xd --split train
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset xd --split val
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset xd --split test
```

Note: conda run may show UnicodeEncodeError on stdout capture (cp950 codec). This is
cosmetic — the script runs successfully and produces .npy files. Verify by checking file counts.

### Stage 3: CLIP Feature Extraction (vcc-main) — ~3-6h

Run after Stage 1 boundaries are available for each split:

```bash
conda run -n vcc-main python scripts/extract_clip.py --dataset xd --split train
conda run -n vcc-main python scripts/extract_clip.py --dataset xd --split val
conda run -n vcc-main python scripts/extract_clip.py --dataset xd --split test
```

### Stage 4: Alignment Verification

After all splits complete:

```bash
# Run directly (bypasses conda stdout unicode issue)
C:/Anaconda/envs/vcc-main/python.exe scripts/verify_alignment.py --dataset xd --split all
```

Expected: PASSED with ~4750 videos (4754 minus ~4 CRC-corrupt). The 4 corrupt files
appear as SKIP not FAIL, so exit code is 0.

### Error Log Checks

```bash
cat E:/skeletons/xd/errors.log 2>/dev/null | head -20    # should show 4 corrupt files only
cat E:/features/xd/skeleton/errors.log 2>/dev/null | head -20
cat E:/features/xd/clip/errors.log 2>/dev/null | head -20
```

### File Count Sanity Checks

```bash
ls E:/features/xd/skeleton/*.npy | wc -l   # should be ~4750
ls E:/features/xd/clip/*.npy | wc -l        # should match skeleton count
```

### Spot-Check After Full Extraction

```bash
C:/Anaconda/envs/vcc-main/python.exe scripts/_verify_smoke.py
# (edit _verify_smoke.py to use a sample from the full set if needed)
```

Or directly:
```bash
C:/Anaconda/envs/vcc-main/python.exe -c "
import numpy as np
from pathlib import Path
skel_files = sorted(Path('E:/features/xd/skeleton').glob('*.npy'))
print(f'XD skeleton files: {len(skel_files)}')
print(f'XD clip files: {len(list(Path(\"E:/features/xd/clip\").glob(\"*.npy\")))}')
s = np.load(skel_files[100])
c = np.load(str(skel_files[100]).replace('skeleton', 'clip'))
print(f'Sample - Skeleton: {s.shape}, CLIP: {c.shape}, match: {s.shape[0]==c.shape[0]}')
"
```

## Important Notes on Val Split Routing

The val split for XD-Violence uses the same train folder (not test/videos/). The
extract_skeletons.py script routes `split in ("train",)` to XD_TRAIN_ROOT and
all other splits to XD_TEST_ROOT. Val split IDs are from the train set, so they
ARE in E:\XD_Violence\train\. The val split file (xd_val.txt) was created with
a 15% hold-out from training, so val IDs point to train folder files.

To confirm this is working correctly, the script uses:
- `split in ("train",)` — True for train, False for val/test
- val uses XD_TEST_ROOT (test/videos/) by this logic
- BUT val videos are actually in XD_TRAIN_ROOT

**This is a potential bug.** Check before running full val extraction:
```bash
head -1 data/splits/xd_val.txt
# Check if this file exists in E:\XD_Violence\train\ vs test\videos\
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Added sys.stdout/stderr.reconfigure to extract_skeletons.py and extract_ctrgcn.py**
- **Found during:** Task 1 setup
- **Issue:** extract_skeletons.py and extract_ctrgcn.py were missing the `sys.stdout.reconfigure(line_buffering=True)` lines that were previously documented as needed for conda run tqdm output. extract_clip.py already had them from a prior wave.
- **Fix:** Added `sys.stdout.reconfigure(line_buffering=True)` and `sys.stderr.reconfigure(line_buffering=True)` to both scripts
- **Files modified:** scripts/extract_skeletons.py, scripts/extract_ctrgcn.py
- **Commit:** 1a233ef

**2. [Rule 1 - Bug] Val split videos routed to wrong directory (XD_TEST_ROOT instead of XD_TRAIN_ROOT)**
- **Found during:** Task 1 smoke test analysis
- **Issue:** `extract_skeletons.py` and `extract_clip.py` route `val` split to `XD_TEST_ROOT` (E:\XD_Violence\test\videos\) but XD-Violence val is a 15% holdout from training — val IDs are in `XD_TRAIN_ROOT` (E:\XD_Violence\train\). Without this fix, the val extraction would fail with FileNotFoundError for all 594 videos.
- **Fix:** Changed `if split in ("train",)` to `if split in ("train", "val")` in both scripts.
- **Verified:** First 3 val IDs confirmed present in train folder, not test/videos/.
- **Files modified:** scripts/extract_skeletons.py, scripts/extract_clip.py
- **Commit:** faa1c86

**3. [Rule 3 - Blocking] decord not available in vcc-skeleton environment**
- **Found during:** Task 1 smoke test
- **Issue:** `import decord` fails in vcc-skeleton with `No module named 'decord'`. The script already has a cv2.VideoCapture fallback path which works correctly.
- **Fix:** No code change needed — fallback path works. Documented that decord is not needed in vcc-skeleton.
- **Files modified:** None (pre-existing fallback code handles this)
- **Commit:** N/A

**3. [Rule 1 - Bug discovery] conda run unicode bug cosmetic issue**
- **Found during:** Task 1 verification
- **Issue:** `conda run` on Windows (cp950 locale) fails with UnicodeEncodeError when scripts produce tqdm unicode block characters in stdout. This affects vcc-ctrgcn and vcc-main scripts.
- **Resolution:** Scripts run successfully and produce correct output files despite conda wrapper failure. Workaround: use direct python path `C:/Anaconda/envs/vcc-main/python.exe script.py` for scripts that need stdout capture.
- **Files modified:** None needed
- **Commit:** N/A

### Total deviations: 4
- 2 auto-fixed (missing stdout reconfigure, val split path bug)
- 2 documented with workarounds (decord fallback already exists, conda unicode is cosmetic)

## Extraction Status at Plan Commit

**All 3 stages validated on 3 XD-Violence smoke test videos**

| Stage | Status | Files |
|-------|--------|-------|
| Stage 1: Skeleton extraction | 3/4754 done (smoke test) | E:\skeletons\xd\ |
| Stage 2: CTR-GCN extraction | 3/4754 done (smoke test) | E:\features\xd\skeleton\ |
| Stage 3: CLIP extraction | 3/4754 done (smoke test) | E:\features\xd\clip\ |
| Stage 4: Alignment verification | 3/3360 PASS (smoke test) | N/A |

**Full extraction is pending user execution (see Full Extraction Commands above)**

## Task 2 Checkpoint Details

**This is the human-verify checkpoint.**

### What was built

- XD-Violence smoke test: 3 videos through full pipeline (skeleton + CTR-GCN + CLIP)
- All 3 videos PASS alignment verification: shapes, dtypes, snippet counts, NaN/Inf checks
- Full extraction commands documented (see section above)
- All 3 extraction scripts updated with stdout reconfigure for conda run compatibility
- Key discovery: decord not in vcc-skeleton but cv2 fallback works; conda unicode issue is cosmetic

### Verification steps (once full extraction completes)

1. **Run alignment verification (both datasets):**
   ```bash
   C:/Anaconda/envs/vcc-main/python.exe scripts/verify_alignment.py --dataset ucf --split all
   C:/Anaconda/envs/vcc-main/python.exe scripts/verify_alignment.py --dataset xd --split all
   ```
   Expected: UCF PASSED (~1900 videos), XD PASSED (~4750 videos with 4 known SKIP)

2. **Check file counts:**
   ```bash
   ls E:/features/ucf/skeleton/*.npy | wc -l   # ~1900
   ls E:/features/ucf/clip/*.npy | wc -l
   ls E:/features/xd/skeleton/*.npy | wc -l    # ~4750
   ls E:/features/xd/clip/*.npy | wc -l
   ```

3. **Check error logs (only CRC-corrupt files expected):**
   ```bash
   cat E:/skeletons/xd/errors.log 2>/dev/null
   ```

4. **Spot-check XD features:**
   ```bash
   C:/Anaconda/envs/vcc-main/python.exe scripts/_verify_smoke.py
   ```

5. **Phase 2 is complete when both datasets pass alignment verification.**

### Resume signal

Type "phase 2 approved" to mark Phase 2 complete, or describe issues.

## Known Stubs

- `E:/features/xd/skeleton/` — 3/4754 populated (smoke test only; full extraction pending)
- `E:/features/xd/clip/` — 3/4754 populated (smoke test only; full extraction pending)
- These are real features, not stubs, but coverage is incomplete pending user-run full extraction

## Self-Check

| Item | Status |
|------|--------|
| scripts/extract_skeletons.py (stdout reconfigure) | FOUND |
| scripts/extract_ctrgcn.py (stdout reconfigure) | FOUND |
| scripts/extract_clip.py (stdout reconfigure) | FOUND |
| E:/features/xd/skeleton/ 3 smoke test .npy files | FOUND |
| E:/features/xd/clip/ 3 smoke test .npy files | FOUND |
| Alignment PASS for 3 smoke test videos | CONFIRMED |
| commit 1a233ef (Task 1) | FOUND |
| .planning/phases/02-feature-extraction-pipeline/02-04-SUMMARY.md | FOUND |

## Self-Check: PASSED

---
*Phase: 02-feature-extraction-pipeline*
*Completed: 2026-04-05 (partial — full XD-Violence extraction pending user execution)*
