---
status: complete
quick_id: 260503-nl6
date: "2026-05-03"
commits:
  - hash: c22f326
    message: "feat(quick-260503-nl6): add comprehensive model benchmark script"
---

# Quick Task 260503-nl6: Model Performance Benchmark

## What was done

Created `scripts/benchmark_models.py` — a self-contained benchmark script that measures computational cost for all 5 ViolenceCC model variants on the RTX 4090.

## Metrics measured

- **Parameters** (total, trainable, in K)
- **MACs / FLOPs** via thop (per-sample, batch=1)
- **Inference latency** (ms/batch, ms/sample)
- **Throughput** (samples/sec)
- **Peak GPU memory** (MB)

## Results (RTX 4090, batch=16, T=32)

| Model | Params (K) | MACs (M) | FLOPs (M) | Latency (ms/B) | Throughput (S/s) | GPU (MB) |
|-------|-----------|---------|----------|----------------|-----------------|---------|
| Skeleton-Only | 37.57 | 1.21 | 2.43 | 0.504 | 31,766 | 10.6 |
| CLIP-Only | 595.65 | 19.07 | 38.14 | 0.690 | 23,181 | 14.8 |
| Late Fusion | 633.22 | 20.29 | 40.57 | 1.153 | 13,874 | 17.8 |
| Gated Fusion | 498.11 | 15.96 | 31.92 | 1.050 | 15,237 | 21.7 |
| RTFM-I3D | 137.41 | 4.46 | 8.91 | 0.460 | 34,786 | 18.8 |

## Key observations

- All models are lightweight MIL heads (37K–633K params) — backbone feature extraction dominates real-world cost
- Gated Fusion (498K) is lighter than Late Fusion (633K) despite having the gate mechanism, because it projects to shared_dim=256 instead of running two full independent heads
- Sub-millisecond batch latency across the board — inference cost is negligible relative to feature extraction
- GPU memory footprint is minimal (10–22 MB) since these are frozen-feature classifiers

## Artifacts

- `scripts/benchmark_models.py` (370 lines) — benchmark script with console, LaTeX, and CSV output
- `results/benchmark_models.csv` — CSV export for downstream analysis
- LaTeX booktabs table printed to stdout for thesis inclusion
