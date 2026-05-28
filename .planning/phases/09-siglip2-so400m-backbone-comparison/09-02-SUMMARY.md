---
phase: 09-siglip2-so400m-backbone-comparison
plan: 02
status: complete
started: "2026-05-20T14:46:00.000Z"
completed: "2026-05-21T01:15:00.000Z"
duration: "~2.5 hours (including model download and all 8 extraction runs)"
---

# Plan 09-02 Summary: SO400M Feature Extraction

## What was done
Extracted SigLIP2 SO400M (ViT-SO400M-16-SigLIP2-256) features for all UCF-Crime and XD-Violence videos using batch_size=16 on RTX 4090.

## Extraction runs (8 total)
1. UCF train mean+max — 1368 videos processed
2. UCF test mean+max — 532 videos processed
3. UCF train mean-only — 1368 videos processed
4. UCF test mean-only — 532 videos processed
5. XD train mean+max — 3954 videos processed
6. XD test mean+max — 798 videos processed
7. XD train mean-only — 3954 videos processed
8. XD test mean-only — 798 videos processed

## Feature verification

| Directory | Files | Shape | Dim |
|-----------|-------|-------|-----|
| E:/features/ucf/siglip2_so400m/ | 1508 | [N, 2304] | correct |
| E:/features/ucf/siglip2_so400m_mean/ | 1508 | [N, 1152] | correct |
| E:/features/xd/siglip2_so400m/ | 4158 | [N, 2304] | correct |
| E:/features/xd/siglip2_so400m_mean/ | 4158 | [N, 1152] | correct |

File counts match prior CLIP and SigLIP2-base extractions (1508 UCF, 4158 XD). Same too-short videos skipped across all backbones.

## Notes
- Model weights downloaded from HuggingFace Hub (timm/ViT-SO400M-16-SigLIP2-256, ~2.3 GB)
- No new failures beyond the expected too-short video set
- All exit codes 0
