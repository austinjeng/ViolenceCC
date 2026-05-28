---
phase: 10-siglip2-giant-backbone-comparison
plan: 02
status: complete
started: "2026-05-21T15:30:00.000Z"
completed: "2026-05-22T02:00:00.000Z"
duration: "~10.5 hours (12 extraction runs including model download)"
---

# Plan 10-02 Summary: Giant-opt Feature Extraction

## What was done
Extracted SigLIP2 Giant-opt (ViT-gopt-16-SigLIP2-256, 1.16B vision params) features for all UCF-Crime and XD-Violence videos. Extracted all 3 splits (train+val+test) per Phase 9 lesson.

## Feature verification

| Directory | Files | Shape | Dim |
|-----------|-------|-------|-----|
| E:/features/ucf/siglip2_giant/ | 1728 | [N, 3072] | correct |
| E:/features/ucf/siglip2_giant_mean/ | 1728 | [N, 1536] | correct |
| E:/features/xd/siglip2_giant/ | 4752 | [N, 3072] | correct |
| E:/features/xd/siglip2_giant_mean/ | 4752 | [N, 1536] | correct |

Val coverage: UCF 220/242, XD 594/594 (matches all prior backbones).
