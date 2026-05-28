---
phase: 10-siglip2-giant-backbone-comparison
plan: 03
status: complete
started: "2026-05-22T02:10:00.000Z"
completed: "2026-05-22T04:30:00.000Z"
duration: "~2.3 hours (6 queues, 14 experiments)"
---

# Plan 10-03 Summary: Giant-opt Ablation Runs

## Results

| run_name | AUC | AP |
|----------|-----|-----|
| ucf_clip_only_giant_s42 | 0.8309 | 0.2520 |
| ucf_late_fusion_giant_s42 | 0.8088 | 0.1964 |
| ucf_gated_fusion_giant_s42 | 0.8323 | 0.2922 |
| xd_clip_only_giant_s42 | 0.9313 | 0.7628 |
| xd_late_fusion_giant_s42 | 0.9089 | 0.6662 |
| xd_gated_fusion_giant_s42 | 0.9267 | 0.7280 |
| ucf_gated_fusion_giant_2person_s42 | 0.8348 | 0.2447 |
| ucf_gated_fusion_giant_clip_mean_s42 | 0.8363 | 0.2717 |
| xd_gated_fusion_giant_2person_s42 | 0.9247 | 0.7267 |
| xd_gated_fusion_giant_clip_mean_s42 | 0.9258 | 0.7385 |
| ucf_gated_fusion_giant_s123 | 0.8365 | 0.2585 |
| ucf_gated_fusion_giant_s2024 | 0.8296 | 0.2216 |
| xd_gated_fusion_giant_s123 | 0.9265 | 0.7287 |
| xd_gated_fusion_giant_s2024 | 0.9326 | 0.7561 |

## Key observations
- Giant-opt achieves highest UCF Gated Fusion AUC: 83.23% (vs CLIP 82.27%, SO400M 82.18%, SigLIP2-base 79.61%)
- UCF AP also strongest: 29.22% (vs CLIP 23.15%, SO400M 20.47%)
- XD performance competitive but slightly below SO400M (92.67% vs 93.15% AUC)
- Scaling trend: larger vision backbone helps UCF more than XD
