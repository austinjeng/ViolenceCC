---
status: partial
phase: 02-feature-extraction-pipeline
source: 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md
started: 2026-04-08T04:00:00Z
updated: 2026-04-08T04:05:00Z
---

## Current Test

[testing paused — 4 items outstanding (blocked on XD-Violence extraction)]

## Tests

### 1. Split File Counts
expected: 6 split files exist in data/splits/ with correct line counts: ucf_train=1368, ucf_val=242, ucf_test=290, xd_train=3360, xd_val=594, xd_test=800
result: pass

### 2. Split Reproducibility
expected: Running `python scripts/create_splits.py --verify` exits successfully, confirming byte-identical splits with seed=42
result: pass

### 3. Split Test Suite
expected: `pytest tests/test_splits.py` passes all 9 tests (file existence, no overlap, val fraction, reproducibility)
result: pass

### 4. UCF-Crime Skeleton Pickles Complete
expected: E:/skeletons/ucf/ contains 1900 .pkl files (1368 train + 242 val + 290 test), each with PYSKL-compatible format (keypoint shape [2,T,17,2])
result: pass

### 5. UCF-Crime Feature Shapes
expected: Sample .npy files in E:/features/ucf/skeleton/ have shape [N,256] float32 and E:/features/ucf/clip/ have shape [N,1024] float32, with no NaN or Inf values
result: pass
note: 1728/1900 have features. 172 videos have <64 frames (max 63), producing 0 snippets — correctly skipped by extraction. This is expected behavior, not missing extraction.

### 6. UCF-Crime Alignment Verification
expected: `python scripts/verify_alignment.py --dataset ucf --split all` exits 0, reporting all checked videos PASS (skeleton snippet count == CLIP snippet count == boundary snippet count for every video)
result: pass
note: 1728 PASS, 0 FAIL, 172 SKIP (sub-64-frame videos with no features). All extractable videos pass alignment. Phase 3 must handle 172 zero-snippet videos in the data loader.

### 7. XD-Violence Smoke Test
expected: At least 3 XD-Violence .npy files exist in E:/features/xd/skeleton/ and E:/features/xd/clip/ with correct shapes ([N,256] and [N,1024]) and alignment verified
result: pass

### 8. Extraction Resume Logic
expected: Re-running any extraction script on already-processed videos completes quickly, printing skip messages for each existing file (skip-if-exists pattern)
result: pass

### 9. XD-Violence Skeleton Extraction Complete
expected: E:/skeletons/xd/ contains ~4754 .pkl files and E:/snippets/xd/ contains matching boundary JSONs for all XD-Violence videos (train+val+test)
result: blocked
blocked_by: prior-phase
reason: "Only 939/4754 skeleton pickles extracted (20%). User must run full skeleton extraction (~10-15h)."

### 10. XD-Violence Feature Extraction Complete
expected: E:/features/xd/skeleton/ contains .npy files with shape [N,256] float32 and E:/features/xd/clip/ contains matching [N,1024] float32 for all extractable XD-Violence videos
result: blocked
blocked_by: prior-phase
reason: "Only 3/4754 feature files exist (smoke test). Depends on test 9 completing first, then CTR-GCN (~1-2h) and CLIP (~3-6h) extraction."

### 11. XD-Violence Alignment Verification
expected: `python scripts/verify_alignment.py --dataset xd --split all` exits 0, reporting all checked videos PASS
result: blocked
blocked_by: prior-phase
reason: "Depends on tests 9 and 10 completing."

### 12. XD-Violence Sub-64-Frame Video Audit
expected: Any XD-Violence videos with <64 frames are correctly skipped (same pattern as UCF-Crime's 172 zero-snippet videos), and the count is documented for Phase 3 data loader
result: blocked
blocked_by: prior-phase
reason: "Depends on test 9 completing to identify which XD videos are sub-64-frame."

## Summary

total: 12
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 4

## Gaps

[none so far — 8/8 testable items pass. 4 blocked tests await XD-Violence extraction completion.]

## XD-Violence Extraction Commands (User Must Run)

### Stage 1: Skeleton Extraction (~10-15h)
```bash
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset xd --split train
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset xd --split val
conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset xd --split test
```

### Stage 2: CTR-GCN Feature Extraction (~1-2h)
```bash
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset xd --split train
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset xd --split val
conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset xd --split test
```

### Stage 3: CLIP Feature Extraction (~3-6h)
```bash
conda run -n vcc-main python scripts/extract_clip.py --dataset xd --split train
conda run -n vcc-main python scripts/extract_clip.py --dataset xd --split val
conda run -n vcc-main python scripts/extract_clip.py --dataset xd --split test
```

### Stage 4: Verify
```bash
C:/Anaconda/envs/vcc-main/python.exe scripts/verify_alignment.py --dataset xd --split all
```
