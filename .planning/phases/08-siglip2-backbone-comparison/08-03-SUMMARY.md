---
phase: 08-siglip2-backbone-comparison
plan: 03
subsystem: feature-extraction
tags: [siglip2, extraction, ucf-crime, xd-violence, features]

dependency_graph:
  requires:
    - phase: 08-01
      provides: BACKBONE_CONFIGS siglip2-base entry, --backbone CLI flag
  provides:
    - SigLIP2 mean+max features at E:/features/{ucf,xd}/siglip2/ (1536-d)
    - SigLIP2 mean-only features at E:/features/{ucf,xd}/siglip2_mean/ (768-d)
  affects: [08-04-siglip2-ablation-execution]

tech-stack:
  added: []
  patterns: [backbone-parameterized-extraction, resume-safe-extraction]

key-files:
  created:
    - E:/features/ucf/siglip2/ (1728 .npy files)
    - E:/features/ucf/siglip2_mean/ (1728 .npy files)
    - E:/features/xd/siglip2/ (4752 .npy files)
    - E:/features/xd/siglip2_mean/ (4752 .npy files)
  modified: []

key-decisions:
  - "Backbone switched from Giant (1.1B params) to ViT-B/16-256 (93M params) in commit 50954f1 before extraction — all dims updated consistently"
  - "4752 XD videos extracted (same as CLIP count); 2 videos absent from both backbones (split file alignment)"

patterns-established:
  - "Backbone-agnostic extraction: same snippet boundaries reused, only model and output dir change"

requirements-completed: [EVAL-02]

duration: "~5 hours GPU (user-supervised, run between sessions)"
completed: 2026-05-20
---

# Phase 8 Plan 03: SigLIP2 Feature Extraction Summary

**SigLIP2 ViT-B/16-256 features extracted for all UCF-Crime and XD-Violence videos — 4 passes (mean+max and mean-only for each dataset) with perfect snippet alignment to CLIP baseline**

## Performance

- **Duration:** ~5 hours GPU (user ran between sessions)
- **Completed:** 2026-05-20
- **Tasks:** 2 (smoke test + full extraction)

## Accomplishments

- Extracted SigLIP2 mean+max features (1536-d) for 1728 UCF + 4752 XD videos
- Extracted SigLIP2 mean-only features (768-d) for 1728 UCF + 4752 XD videos
- Zero snippet count mismatches vs CLIP features across all videos
- No NaN/Inf values detected in sampled features
- File counts match CLIP extraction exactly (1728 UCF, 4752 XD)

## Verification Results

| Directory | Files | Expected Dim | Actual Dim | Alignment | Status |
|-----------|-------|-------------|------------|-----------|--------|
| E:/features/ucf/siglip2/ | 1728 | 1536 | 1536 | 0 mismatches vs CLIP | PASS |
| E:/features/ucf/siglip2_mean/ | 1728 | 768 | 768 | — | PASS |
| E:/features/xd/siglip2/ | 4752 | 1536 | 1536 | 0 mismatches vs CLIP | PASS |
| E:/features/xd/siglip2_mean/ | 4752 | 768 | 768 | — | PASS |

## Deviations from Plan

- **Backbone variant:** Plan written for `siglip2-giant` (1536-d embed, 3072-d mean+max). Executed with `siglip2-base` (768-d embed, 1536-d mean+max) per commit 50954f1 switch. All configs and tests already updated in that commit.
- **Extraction timing:** User ran extraction between sessions rather than live in this executor session. Verified all outputs exist with correct dimensions.

## Issues Encountered

None — extraction completed cleanly with zero failures.

## Self-Check: PASSED

- [x] All 4 feature directories populated with correct file counts
- [x] Dimension assertions pass for all directories (1536 mean+max, 768 mean-only)
- [x] Snippet counts match existing CLIP extraction per video (0 mismatches)
- [x] No NaN or Inf values in sampled features
- [x] SUMMARY.md created

---
*Phase: 08-siglip2-backbone-comparison*
*Completed: 2026-05-20*
