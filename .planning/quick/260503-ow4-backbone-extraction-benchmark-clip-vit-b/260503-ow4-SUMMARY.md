---
status: complete
quick_id: 260503-ow4
date: "2026-05-03"
commits:
  - hash: 0f3c90e
    message: "feat(quick-260503-ow4): cross-environment backbone extraction benchmark"
---

# Quick Task 260503-ow4: Backbone Extraction Benchmark

## What was done

Created `scripts/benchmark_backbones.py` — a cross-environment backbone feature extraction benchmark that measures the REAL computational cost of each pipeline component. Runs across 3 conda environments via `--all` mode with JSON intermediaries.

## Architecture

Single script with `--component` dispatch and lazy imports:
- `--clip` (vcc-main): CLIP ViT-B/16 visual encoder via open-clip + thop
- `--rtmpose` (vcc-skeleton): RTMPose-m + YOLOX via rtmlib + onnxruntime
- `--ctrgcn` (vcc-ctrgcn): CTR-GCN 4-stream backbone via mmcv + PYSKL
- `--all`: shells out to all 3 envs, then combines
- `--combine`: reads JSON results, adds I3D published numbers, produces unified tables

## Results (RTX 4090)

### Backbone Comparison

| Backbone | Params (M) | FLOPs (G) | Latency | Throughput | GPU Mem (MB) | Per-Frame |
|----------|-----------|----------|---------|-----------|-------------|----------|
| CLIP ViT-B/16 | 86.2 | 22.5 | 67.8 ms/B | 944 f/s | 1,062 | 1.06 ms |
| RTMPose-m + YOLOX | ~13.0* | ~3.2* | 30.1 ms/f | 33.3 f/s | 213 | 30.1 ms |
| CTR-GCN (4-stream) | 5.7 | --- | 154.2 ms/sn | 6.5 sn/s | 29 | -- (snippet) |
| I3D RGB | ~25.0* | ~107.9* | Pre-extracted | --- | --- | --- |

\* = published number (not measured)

### Pipeline Cost Summary (per 64-frame snippet)

| Pipeline | Computation | Total |
|----------|------------|-------|
| **Skeleton path** | RTMPose (30.1ms × 64f = 1,924ms) + CTR-GCN (154.2ms) | **2,079 ms** |
| **CLIP path** | CLIP (1.06ms × ~6f at 1 FPS) | **~6 ms** |
| **I3D path** | Pre-extracted | N/A |

## Key observations

- Skeleton extraction pipeline is ~350× more expensive than CLIP per snippet
- RTMPose dominates the skeleton path cost (93% of total) due to frame-by-frame ONNX inference with no batching
- CLIP benefits enormously from batch GPU inference (64 frames/batch)
- CTR-GCN is lightweight (5.7M params, 29 MB GPU) — the skeleton pipeline bottleneck is pose estimation, not GCN features
- CLIP has the most parameters (86.2M) but is fastest per-frame due to batching

## Bug fixed during execution

- CTR-GCN dummy input shape was [N, M, T, V, C=2] but model expects C=3 (x, y, confidence). Fixed to C=3.

## Artifacts

- `scripts/benchmark_backbones.py` (889 lines) — cross-env benchmark with --all mode
- `results/backbone_bench_clip.json` — CLIP benchmark results
- `results/backbone_bench_rtmpose.json` — RTMPose benchmark results
- `results/backbone_bench_ctrgcn.json` — CTR-GCN benchmark results
- `results/backbone_bench_combined.csv` — combined CSV export
- LaTeX booktabs table printed to stdout for thesis inclusion
