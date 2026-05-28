---
phase: 09-siglip2-so400m-backbone-comparison
plan: 03
status: complete
started: "2026-05-21T04:16:00.000Z"
completed: "2026-05-21T07:30:00.000Z"
duration: "~3.25 hours (6 queues, 14 experiments)"
---

# Plan 09-03 Summary: SO400M Ablation Runs

## What was done
Ran all 6 Phase 9 ablation queues (14 total experiments) using `--no-preflight` flag since all configs have `wandb.mode: disabled`.

## Results

| run_name | AUC | AP |
|----------|-----|-----|
| ucf_clip_only_so400m_s42 | 0.8141 | 0.2070 |
| ucf_late_fusion_so400m_s42 | 0.8026 | 0.1894 |
| ucf_gated_fusion_so400m_s42 | 0.8218 | 0.2047 |
| xd_clip_only_so400m_s42 | 0.9348 | 0.7764 |
| xd_late_fusion_so400m_s42 | 0.9083 | 0.6642 |
| xd_gated_fusion_so400m_s42 | 0.9315 | 0.7377 |
| ucf_gated_fusion_so400m_2person_s42 | 0.8197 | 0.2130 |
| ucf_gated_fusion_so400m_clip_mean_s42 | 0.8245 | 0.2198 |
| xd_gated_fusion_so400m_2person_s42 | 0.9296 | 0.7481 |
| xd_gated_fusion_so400m_clip_mean_s42 | 0.9258 | 0.7247 |
| ucf_gated_fusion_so400m_s123 | 0.8206 | 0.2250 |
| ucf_gated_fusion_so400m_s2024 | 0.8146 | 0.2051 |
| xd_gated_fusion_so400m_s123 | 0.9231 | 0.7104 |
| xd_gated_fusion_so400m_s2024 | 0.9319 | 0.7661 |

## Issues encountered
1. Initial run failed with `wandb preflight` error — resolved with `--no-preflight` (all configs use `wandb.mode: disabled`)
2. Missing val split features caused `num_samples=0` error — resolved by extracting val splits for both datasets (4 additional extraction runs added to Plan 09-02)

## Notes
- All 14 runs have non-zero AUC and AP values
- No training errors or NaN losses
- UCF AUC range: 0.80-0.82, XD AUC range: 0.91-0.93
- SO400M shows competitive performance with CLIP and SigLIP2-base
