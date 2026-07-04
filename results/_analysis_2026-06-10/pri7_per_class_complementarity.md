# Pri 7 — Per-class UCF complementarity (does skeleton help motion classes more?)

**Backbone:** giant (UCF headline) | **Seeds:** 42, 123, 2024 | **Metric:** per-category frame-level AUC

**Comparison:** gated fusion (Skeleton+CLIP) minus visual-only (CLIP). Positive Δ = skeleton helps that category.


## Per-class skeleton gain (3-seed mean), sorted descending

| Category | Group | n (test vids) | ΔAUC (pp) | σ across seeds (pp) | Fused AUC | Visual AUC |
|---|---|---:|---:|---:|---:|---:|
| Fighting | HM | 5 | +1.72 | 0.67 | 0.9392 | 0.9220 |
| Arrest | HM | 5 | +1.72 | 1.07 | 0.9097 | 0.8925 |
| Shooting | HM | 22 | +1.05 | 0.20 | 0.9567 | 0.9462 |
| Burglary | HM | 12 | +0.73 | 0.72 | 0.9484 | 0.9411 |
| Shoplifting | HM | 19 | +0.55 | 0.40 | 0.9181 | 0.9126 |
| Vandalism | HM | 5 | +0.22 | 0.33 | 0.9747 | 0.9724 |
| Stealing | HM | 5 | +0.18 | 0.09 | 0.9934 | 0.9916 |
| Arson | APP | 9 | -0.19 | 0.50 | 0.9688 | 0.9707 |
| RoadAccidents | APP | 16 | -0.21 | 2.42 | 0.8714 | 0.8735 |
| Explosion | APP | 20 | -0.48 | 1.90 | 0.8875 | 0.8924 |
| Abuse | HM | 2 | -0.80 | 1.05 | 0.9605 | 0.9684 |
| Assault | HM | 3 | -0.87 | 0.43 | 0.9718 | 0.9805 |
| Robbery | HM | 5 | -1.46 | 1.97 | 0.8864 | 0.9010 |

HM = human-motion group; APP = appearance/no-human group.


## Group means (mean ± std of per-class ΔAUC, across classes)

| Group | n classes | mean ΔAUC (pp) | std (pp) | classes with Δ>0 | min (pp) | max (pp) |
|---|---:|---:|---:|---:|---:|---:|
| HUMAN-MOTION | 10 | +0.305 | 1.082 | 7/10 | -1.46 | +1.72 |
| APPEARANCE   | 3 | -0.293 | 0.164 | 0/3 | -0.48 | -0.19 |

**Group-mean difference (HM − APP):** +0.598 pp (Welch t = 1.68, df ≈ 10.2). With only 3 appearance classes this t-test has negligible power; treat as descriptive.


## Verdict — does the evidence support 'motion not captured by appearance'?

- The human-motion group shows a LARGER mean skeleton gain than the appearance group by +0.598 pp (+0.305 vs -0.293 pp). Direction is CONSISTENT with the paper's claim.
- BUT the within-HM spread (σ=1.082 pp) is larger than the between-group gap (0.598 pp): the group difference is small relative to class-to-class noise. Evidence is MIXED, not clean.
- 7/10 human-motion classes have positive Δ; 0/3 appearance classes do.

## CAVEAT — per-class AUC is NOISY (tiny test-video counts)

- Per-category test-video counts are recovered by counting distinct ANOMALY video_ids in `results/ucf_clip_only_giant_s42/eval_scores.npz` (keys are video_ids; category = leading non-digit prefix; identical across seeds/backbones since the test split is fixed).
- These counts reflect the EVALUATED test set: the npz holds 254 videos (128 anomaly + 126 normal), the documented <64-frame–exclusion subset of the full 290-video UCF-Crime test split (disclosed at main.tex:134). The 13 per-category counts sum to 128, matching the evaluated anomaly videos — so this is the correct denominator for the per_category.csv AUCs analyzed here (those AUCs are computed on exactly these videos).

- Several categories have only a handful of test videos (smallest: Abuse (n=2), Assault (n=3), Fighting (n=5), Arrest (n=5), Vandalism (n=5), Stealing (n=5)). A single video's score can swing that category's AUC by several points, so per-class deltas — and therefore the group means built from them — carry wide, unquantified uncertainty. The 'across-seeds σ' column captures only seed/training noise, NOT the (larger) sampling noise from tiny per-class video counts.

- Within-class video counts are unequal, so the unweighted group mean treats a 5-video class (e.g. Robbery, Stealing, Fighting) the same as a 22-video class (e.g. Shooting). This is a deliberate per-class average, but it amplifies the influence of the noisiest small classes.

