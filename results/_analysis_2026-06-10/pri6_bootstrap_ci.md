# Pri 6: Video-Level Bootstrap 95% CIs (Defense Insurance)

- Primary seed: s42 | Bootstrap B=2000 | rng=default_rng(12345)
- Resampling unit: VIDEO (resample videos w/ replacement, pool their frames, recompute metric).
- Labels reconstructed exactly as `src/evaluate.py`:`_build_frame_arrays` (UCF default path / XD fusion path).

## Sanity gate (pooled recompute vs stored eval_metrics)

| Dataset | Metric | Stored | Recomputed | |diff| | Tol | Pass |
|---|---|---|---|---|---|---|
| UCF | AUC | 0.8249043 | 0.8249043 | 0.00e+00 | 1e-04 | PASS |
| XD | AP | 0.7974129 | 0.7974129 | 0.00e+00 | 1e-04 | PASS |

## Bootstrap 95% CIs

| Dataset | Metric | Point (s42) | CI lo | CI hi | Width (pp) | Point inside CI? |
|---|---|---|---|---|---|---|
| UCF | AUC | 82.49% | 75.63% | 88.02% | 12.39 | YES |
| XD | AP | 79.74% | 76.62% | 82.68% | 6.06 | YES |

### Plain-language

- **UCF AUC (s42 = 82.49%)**: 95% CI [75.63%, 88.02%], width 12.39 pp. Point estimate INSIDE the CI.
- **XD AP (s42 = 79.74%)**: 95% CI [76.62%, 82.68%], width 6.06 pp. Point estimate INSIDE the CI.

### REVIEW probe reproduce check

- REVIEW probe estimated UCF-AUC CI width ~12.7 pp. Actual UCF-AUC width: **12.39 pp**.

## Build provenance

- UCF: {'n_annotated': 254, 'n_normal_default': 0} (snippet_window=64, upsample=10, n_frames from M3 manifest data/ucf_total_frames.json)
- XD: {'n_abnormal': 500, 'n_normal': 300} (snippet_window=64, upsample=1, n_frames=len(scores)*64; normals absent from Wu file -> zero labels)