# UCF consistency rerun -- comparison

Cells compared: 29  |  max |delta|: 0.041275  |  escalation cells: 16

| run | canonical AUC | rerun AUC | delta | row seed std | within std |
|---|---|---|---|---|---|
| ucf_clip_only_giant_s42 | 0.823624 | 0.813939 | -0.009685 | 0.001716 | NO |
| ucf_clip_only_s42 | 0.811182 | 0.814364 | +0.003182 | 0.001078 | NO |
| ucf_clip_only_siglip2_s42 | 0.783157 | 0.785113 | +0.001956 | 0.00528 | yes |
| ucf_clip_only_so400m_s42 | 0.809292 | 0.817054 | +0.007762 | 0.003021 | NO |
| ucf_gated_fusion_2person_s42 | 0.811173 | 0.808109 | -0.003064 | 0.004814 | yes |
| ucf_gated_fusion_clip_mean_s42 | 0.810787 | 0.804953 | -0.005834 | 0.007292 | yes |
| ucf_gated_fusion_giant_2person_s42 | 0.827311 | 0.825678 | -0.001633 | 0.002962 | yes |
| ucf_gated_fusion_giant_clip_mean_s42 | 0.829822 | 0.825366 | -0.004457 | 0.004087 | NO |
| ucf_gated_fusion_giant_s123 | 0.829231 | 0.827695 | -0.001536 | 0.003555 | yes |
| ucf_gated_fusion_giant_s2024 | 0.822182 | 0.823227 | +0.001046 | 0.003555 | yes |
| ucf_gated_fusion_giant_s42 | 0.824904 | 0.823608 | -0.001296 | 0.003555 | yes |
| ucf_gated_fusion_s123 | 0.811088 | 0.816958 | +0.005870 | 0.0028 | NO |
| ucf_gated_fusion_s2024 | 0.813959 | 0.808191 | -0.005768 | 0.0028 | NO |
| ucf_gated_fusion_s42 | 0.816687 | 0.818355 | +0.001669 | 0.0028 | yes |
| ucf_gated_fusion_siglip2_2person_s42 | 0.787231 | 0.800917 | +0.013686 | 0.007273 | NO |
| ucf_gated_fusion_siglip2_clip_mean_s42 | 0.793517 | 0.792995 | -0.000522 | 0.001457 | yes |
| ucf_gated_fusion_siglip2_s123 | 0.790428 | 0.792768 | +0.002340 | 0.000832 | NO |
| ucf_gated_fusion_siglip2_s2024 | 0.788936 | 0.797007 | +0.008071 | 0.000832 | NO |
| ucf_gated_fusion_siglip2_s42 | 0.79032 | 0.793242 | +0.002921 | 0.000832 | NO |
| ucf_gated_fusion_so400m_2person_s42 | 0.813267 | 0.812151 | -0.001115 | 0.003189 | yes |
| ucf_gated_fusion_so400m_clip_mean_s42 | 0.818401 | 0.817189 | -0.001212 | 0.00679 | yes |
| ucf_gated_fusion_so400m_s123 | 0.81373 | 0.818797 | +0.005067 | 0.003065 | NO |
| ucf_gated_fusion_so400m_s2024 | 0.809316 | 0.814868 | +0.005552 | 0.003065 | NO |
| ucf_gated_fusion_so400m_s42 | 0.815207 | 0.816996 | +0.001789 | 0.003065 | yes |
| ucf_late_fusion_giant_s42 | 0.807627 | 0.798628 | -0.008998 | 0.007868 | NO |
| ucf_late_fusion_s42 | 0.785842 | 0.793469 | +0.007628 | 0.004006 | NO |
| ucf_late_fusion_siglip2_s42 | 0.794558 | 0.780747 | -0.013811 | 0.020244 | yes |
| ucf_late_fusion_so400m_s42 | 0.800098 | 0.7846 | -0.015498 | 0.012563 | NO |
| ucf_skeleton_only_s42 | 0.71789 | 0.676615 | -0.041275 | 0.028125 | NO |

**DECISION GATE: FAIL** -- adopt the rerun numbers (full propagation pass). Escalation cells: ucf_clip_only_giant_s42, ucf_clip_only_s42, ucf_clip_only_so400m_s42, ucf_gated_fusion_giant_clip_mean_s42, ucf_gated_fusion_s123, ucf_gated_fusion_s2024, ucf_gated_fusion_siglip2_2person_s42, ucf_gated_fusion_siglip2_s123, ucf_gated_fusion_siglip2_s2024, ucf_gated_fusion_siglip2_s42, ucf_gated_fusion_so400m_s123, ucf_gated_fusion_so400m_s2024, ucf_late_fusion_giant_s42, ucf_late_fusion_s42, ucf_late_fusion_so400m_s42, ucf_skeleton_only_s42
