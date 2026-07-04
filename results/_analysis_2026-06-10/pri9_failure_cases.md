# Pri 9 — Qualitative failure-case analysis (UCF headline, giant, seed 42)

Run: `ucf_gated_fusion_giant_s42`  |  reconstruction matches `src/evaluate.py` UCF path (per-video frame-level scores from `eval_scores.npz`, labels via `frame_labels(anno, n_frames=len(scores))`, explicit-Normal -> all-zero).

## Sanity gate (MANDATORY)

- Pooled frame AUC reconstructed = **0.824904**, stored = **0.824904**, |diff| = 0.00e+00 -> **PASS** (tol 0.0001).
- Pooled frame AP = 0.273712 (stored 0.273712).
- Video-level AUC reproduced = 0.945188 (stored 0.926799).
- Per-video numbers below are therefore trustworthy.

## Cohort summary

- 254 test videos: 128 anomaly (>=1 positive frame), 126 normal (all-negative).
- 128 anomaly videos are AUC-rankable; 0 are 100% anomalous (per-video AUC undefined).
- 82,930 anomaly frames vs 1,014,120 normal frames (7.6% positive).

## 1. Worst ~5 anomaly videos (failure cases, ascending frame-AUC)

| rank | video | category | frame-AUC | n_frames | frac_anom | anom score mean | normal score mean |
|---|---|---|---|---|---|---|---|
| 1 | Burglary017 | Burglary | 0.0569 | 2120 | 0.212 | 0.994 | 0.994 |
| 2 | Shooting028 | Shooting | 0.1135 | 1900 | 0.142 | 0.992 | 0.992 |
| 3 | RoadAccidents011 | RoadAccidents | 0.1415 | 2160 | 0.019 | 0.000 | 0.000 |
| 4 | Explosion007 | Explosion | 0.1447 | 16290 | 0.042 | 0.992 | 0.993 |
| 5 | Shooting018 | Shooting | 0.1453 | 1800 | 0.092 | 0.987 | 0.991 |

### Likely causes (worst cases)

- **Burglary017** (Burglary, AUC 0.0569): the model scores normal frames at least as high as the anomalous ones (inverted ranking) -> appearance/scene-driven, not motion/event-driven; Burglary is subtle/appearance-ambiguous (looks like normal CCTV activity), low motion-saliency for skeleton+CLIP fusion.
- **Shooting028** (Shooting, AUC 0.1135): the model scores normal frames at least as high as the anomalous ones (inverted ranking) -> appearance/scene-driven, not motion/event-driven; Shooting events are abrupt and visually transient, weak signal for a snippet-pooled head.
- **RoadAccidents011** (RoadAccidents, AUC 0.1415): the anomaly is very brief (1.9% of frames), a hard short-event localization case; the model scores normal frames at least as high as the anomalous ones (inverted ranking) -> appearance/scene-driven, not motion/event-driven; RoadAccidents events are abrupt and visually transient, weak signal for a snippet-pooled head.
- **Explosion007** (Explosion, AUC 0.1447): the anomaly is very brief (4.2% of frames), a hard short-event localization case; the model scores normal frames at least as high as the anomalous ones (inverted ranking) -> appearance/scene-driven, not motion/event-driven; Explosion events are abrupt and visually transient, weak signal for a snippet-pooled head.
- **Shooting018** (Shooting, AUC 0.1453): the model scores normal frames at least as high as the anomalous ones (inverted ranking) -> appearance/scene-driven, not motion/event-driven; Shooting events are abrupt and visually transient, weak signal for a snippet-pooled head.

## 2. Top ~5 false-positive normal videos (highest max frame score)

| rank | video | n_frames | max score | mean score | p95 | frac>0.5 |
|---|---|---|---|---|---|---|
| 1 | Normal_Videos_887 | 7630 | 0.994 | 0.982 | 0.994 | 1.000 |
| 2 | Normal_Videos_925 | 7730 | 0.993 | 0.915 | 0.993 | 0.917 |
| 3 | Normal_Videos_884 | 9030 | 0.992 | 0.985 | 0.992 | 1.000 |
| 4 | Normal_Videos_895 | 3030 | 0.992 | 0.989 | 0.992 | 1.000 |
| 5 | Normal_Videos_894 | 2580 | 0.987 | 0.979 | 0.987 | 1.000 |

### Likely causes (false positives)

- **Normal_Videos_887**: peak score 0.994 on an all-normal clip; 100% of frames exceed 0.5 -> a sustained, scene-wide false alarm (appearance-driven, e.g. crowd/motion resembling an event).
- **Normal_Videos_925**: peak score 0.993 on an all-normal clip; 92% of frames exceed 0.5 -> a sustained, scene-wide false alarm (appearance-driven, e.g. crowd/motion resembling an event).
- **Normal_Videos_884**: peak score 0.992 on an all-normal clip; 100% of frames exceed 0.5 -> a sustained, scene-wide false alarm (appearance-driven, e.g. crowd/motion resembling an event).
- **Normal_Videos_895**: peak score 0.992 on an all-normal clip; 100% of frames exceed 0.5 -> a sustained, scene-wide false alarm (appearance-driven, e.g. crowd/motion resembling an event).
- **Normal_Videos_894**: peak score 0.987 on an all-normal clip; 100% of frames exceed 0.5 -> a sustained, scene-wide false alarm (appearance-driven, e.g. crowd/motion resembling an event).
- Context: the global normal-frame mean is 0.382 and p95 is 0.994, so these clips sit far in the right tail of normal scores.

## 3. Score distributions: anomaly vs normal frames

| stat | anomaly frames | normal frames |
|---|---|---|
| n | 82,930 | 1,014,120 |
| mean | 0.8743 | 0.3822 |
| std | 0.3058 | 0.4713 |
| min | 0.0000 | 0.0000 |
| p05 | 0.0009 | 0.0000 |
| p25 | 0.9856 | 0.0000 |
| median | 0.9923 | 0.0001 |
| p75 | 0.9938 | 0.9863 |
| p95 | 0.9948 | 0.9937 |
| max | 0.9952 | 0.9953 |

- Mean separation (anom - normal) = **+0.4921**.
- Histogram: `pri9_score_hist.png`.

## 5 best anomaly videos (for contrast)

| rank | video | category | frame-AUC | frac_anom |
|---|---|---|---|---|
| 1 | Burglary035 | Burglary | 0.9893 | 0.429 |
| 2 | Burglary061 | Burglary | 0.9891 | 0.167 |
| 3 | Burglary005 | Burglary | 0.9791 | 0.043 |
| 4 | Burglary024 | Burglary | 0.9763 | 0.324 |
| 5 | Shooting024 | Shooting | 0.9602 | 0.291 |
