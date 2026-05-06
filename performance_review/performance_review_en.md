# ViolenceCC Performance Review

**Date:** 2026-05-03
**Hardware:** NVIDIA GeForce RTX 4090 (24 GB VRAM)
**Project:** Dual-modal (Skeleton + CLIP) fusion for weakly supervised video anomaly detection

---

## 1. Overview

This report presents a comprehensive computational cost analysis of the ViolenceCC pipeline, covering both the lightweight MIL classification heads and the heavyweight backbone feature extractors. The benchmark serves two purposes:

1. **Thesis table** -- standard practice in VAD papers to report model complexity alongside AUC/AP metrics
2. **Fair comparison** -- the classification heads alone (sub-millisecond) hide the true extraction cost; the skeleton pipeline is orders of magnitude more expensive than CLIP

All measurements were taken on a single NVIDIA RTX 4090 with controlled warmup and synchronization protocols.

---

## 2. Test Environment

| Component | Specification |
|-----------|--------------|
| GPU | NVIDIA GeForce RTX 4090 (24 GB GDDR6X) |
| OS | Windows 11 Pro |
| PyTorch (vcc-main) | 2.6.0 + CUDA 12.4 |
| PyTorch (vcc-ctrgcn) | 1.12.1 + CUDA 11.3 |
| ONNX Runtime (vcc-skeleton) | 1.24.4 + CUDA 12.x |
| FLOPs counter | thop (torchprofile) |
| Timing | `time.perf_counter()` with `torch.cuda.synchronize()` |

**Methodology:**
- Warmup iterations discarded before timing (default: 50 for heads, 5 for backbones)
- Multiple timed iterations averaged (default: 200 for heads, 20 for backbones)
- GPU memory measured via `torch.cuda.max_memory_allocated()` after `reset_peak_memory_stats()`
- FLOPs computed per single sample (batch=1) as standard practice
- RTMPose/YOLOX FLOPs are published values (ONNX model, not measurable via thop)

---

## 3. MIL Classification Heads

These are the lightweight anomaly scoring heads that operate on pre-extracted features. All share the same MILHead architecture (Linear-ReLU-Dropout cascade ending in sigmoid) but differ in how they process and fuse modality inputs.

### 3.1 Architecture Summary

| Model | Input | Architecture | Output |
|-------|-------|-------------|--------|
| Skeleton-Only | [B, 32, 256] | LayerNorm(256) -> MILHead(256->128->32->1) | [B, 32] |
| CLIP-Only | [B, 32, 1024] | Linear(1024->512) -> LayerNorm(512) -> MILHead(512->128->32->1) | [B, 32] |
| Late Fusion | skel + clip | SkeletonProj + CLIPProj -> alpha-weighted average | [B, 32] |
| Gated Fusion | skel + clip | Projections -> learned gate -> residual -> MILHead | [B, 32] |
| RTFM-I3D | [B, 32, 1024] | LayerNorm(1024) -> MILHead(1024->128->32->1) | [B, 32] |

### 3.2 Results (batch=16, T=32)

| Model | Params (K) | MACs (M) | FLOPs (M) | Latency (ms/batch) | Latency (ms/sample) | Throughput (samples/s) | Peak GPU (MB) |
|-------|-----------|---------|----------|-------------------|--------------------|-----------------------|--------------|
| Skeleton-Only | 37.57 | 1.21 | 2.43 | 0.504 | 0.0315 | 31,766 | 10.6 |
| CLIP-Only | 595.65 | 19.07 | 38.14 | 0.690 | 0.0431 | 23,181 | 14.8 |
| Late Fusion | 633.22 | 20.29 | 40.57 | 1.153 | 0.0721 | 13,874 | 17.8 |
| Gated Fusion | 498.11 | 15.96 | 31.92 | 1.050 | 0.0656 | 15,237 | 21.7 |
| RTFM-I3D | 137.41 | 4.46 | 8.91 | 0.460 | 0.0287 | 34,786 | 18.8 |

### 3.3 Analysis

- **All heads are sub-millisecond per sample** (0.5–1.2 ms per batch). Classification cost is negligible compared to feature extraction.
- **Gated Fusion (498K) is lighter than Late Fusion (633K)** despite having the gate mechanism. This is because Gated Fusion projects both modalities into a shared 256-dim space before the gate, while Late Fusion runs two full independent classification heads (SkeletonProj + CLIPProj) and only combines at the score level.
- **RTFM-I3D has the highest throughput** (34,786 samples/s) because it is a single-stream head with no projection layer, just LayerNorm -> MILHead.
- **Memory footprint is minimal** (10-22 MB). These are frozen-feature classifiers, not end-to-end models.
- **Parameter counts are in the thousands (K), not millions (M).** Reporting in K is more informative for these lightweight heads.

---

## 4. Backbone Feature Extractors

These are the heavyweight models that convert raw video frames into the feature vectors consumed by the MIL heads above. Each runs in a separate conda environment due to incompatible dependency chains.

### 4.1 Architecture Summary

| Backbone | Type | Input | Output | Environment |
|----------|------|-------|--------|-------------|
| CLIP ViT-B/16 | Vision Transformer | [B, 3, 224, 224] RGB | [B, 512] embeddings | vcc-main (PyTorch 2.6.0) |
| RTMPose-m + YOLOX | ONNX (detector + pose) | [H, W, 3] single BGR frame | [N_persons, 17, 2] keypoints | vcc-skeleton (ORT 1.24.4) |
| CTR-GCN (4-stream) | Graph Convolutional Network | [1, 2, 64, 17, 3] per stream | [1, 256] features | vcc-ctrgcn (PyTorch 1.12.1) |
| I3D RGB | 3D ConvNet (Inception) | video clips | [N, 1024] features | Pre-extracted (external) |

### 4.2 Results

| Backbone | Params (M) | FLOPs (G) | Latency | Throughput | Peak GPU (MB) | Per-Frame Cost |
|----------|-----------|----------|---------|-----------|--------------|---------------|
| CLIP ViT-B/16 | 86.19 | 22.54 | 67.79 ms/batch (B=64) | 944.1 frames/s | 1,062.5 | 1.059 ms |
| RTMPose-m + YOLOX | ~13.0\* | ~3.22\* | 30.07 ms/frame | 33.3 frames/s | 213.0 | 30.07 ms |
| CTR-GCN (4-stream) | 5.684 | N/A | 154.17 ms/snippet | 6.5 snippets/s | 29.1 | N/A (snippet-level) |
| I3D RGB | ~25.0\* | ~107.9\* | Pre-extracted | N/A | N/A | N/A |

\* Published values (not measured on this hardware)

### 4.3 CLIP ViT-B/16 Details

- **Model:** OpenAI ViT-B/16 via open-clip-torch 3.3.0
- **Visual encoder parameters:** 86.19M (measured; text encoder excluded)
- **FLOPs:** 22.54 GFLOPs per image (measured via thop, batch=1)
- **Batch inference:** 64 images per batch -> 67.79 ms -> 1.059 ms per frame
- **Latency percentiles:** P50=67.79 ms, P95=69.04 ms (stable, low variance)
- **Memory:** 1,062.5 MB peak allocation (batch=64)
- **Frame sampling:** Target 1 FPS. UCF-Crime: PNGs are ~3 FPS, sample_every=3, ~22 frames per 64-PNG snippet; XD-Violence: sample_every=round(fps/1.0), e.g. ~3 frames/snippet at 24 FPS

### 4.4 RTMPose-m + YOLOX Details

- **Detection:** YOLOX-m (~9M params, ~1.0 GFLOPs) -- internal to rtmlib
- **Pose estimation:** RTMPose-m (~4M params, 2.22 GFLOPs) -- 17 COCO body keypoints
- **Combined:** ~13M params, ~3.22 GFLOPs per frame (published)
- **Latency:** 30.07 ms mean per frame (P50=30.05, P95=31.98)
- **Critical limitation:** No batch inference support. rtmlib processes one frame at a time.
- **Memory:** 213 MB delta (measured via nvidia-smi before/after)
- **Processing:** Every frame in the video -- 64 frames per snippet at full frame rate

### 4.5 CTR-GCN 4-Stream Details

| Stream | Weight | Params (M) | Mean Latency (ms) | P50 (ms) | P95 (ms) |
|--------|--------|-----------|-------------------|----------|----------|
| j (joint) | 1.0 | 1.421 | 38.74 | 37.75 | 45.22 |
| b (bone) | 1.0 | 1.421 | 39.09 | 37.48 | 46.65 |
| jm (joint-motion) | 0.5 | 1.421 | 38.10 | 37.63 | 39.86 |
| bm (bone-motion) | 0.5 | 1.421 | 37.99 | 37.63 | 39.01 |
| **Total (4-stream)** | | **5.684** | **154.17** | **151.77** | **164.71** |

- **Input shape per stream:** [N=1, M=2, T=64, V=17, C=3] (2 persons, 64 frames, 17 joints, x/y/confidence)
- **Weighted average:** (1.0*j + 1.0*b + 0.5*jm + 0.5*bm) / 3.0 -> [N, 256] features
- **FLOPs:** Not measurable (thop not available in vcc-ctrgcn env; mmcv custom ops)
- **Memory:** 29.1 MB -- extremely lightweight once skeletons are extracted
- **Streams are sequential:** all 4 run serially, ~38 ms each

### 4.6 I3D RGB (Reference)

- **Source:** Carreira & Zisserman, "Quo Vadis, Action Recognition?" (CVPR 2017)
- **Parameters:** ~25M (published)
- **FLOPs:** 107.9 GFLOPs per clip (published)
- **Status:** Pre-extracted features downloaded from external source. Not computed by ViolenceCC scripts.
- **Format:** 5-crop design, [N_snippets, 1024] per crop

---

## 5. End-to-End Pipeline Cost Analysis

The critical insight: **classification heads are negligible; extraction backbones dominate.**

### 5.1 Per-Snippet Cost Breakdown

A snippet is a 64-frame segment of video, the fundamental unit of processing.

| Pipeline | Step 1 | Step 2 | Step 3 | Total |
|----------|--------|--------|--------|-------|
| **Skeleton Path** | RTMPose: 30.07 ms x 64 frames = **1,924 ms** | CTR-GCN: **154.17 ms** | Gated Fusion head: **1.05 ms** | **~2,079 ms** |
| **CLIP Path (UCF)** | CLIP: 1.059 ms x ~22 frames = **~23.3 ms** | -- | CLIP-Only head: **0.69 ms** | **~24 ms** |
| **CLIP Path (XD, 24fps)** | CLIP: 1.059 ms x ~3 frames = **~3.2 ms** | -- | CLIP-Only head: **0.69 ms** | **~4 ms** |
| **Combined (Gated Fusion, UCF)** | Skeleton: **1,924 ms** + CLIP: **~23.3 ms** | CTR-GCN: **154.17 ms** | Gated Fusion head: **1.05 ms** | **~2,102 ms** |
| **I3D Path** | Pre-extracted (107.9 GFLOPs published) | -- | RTFM-I3D head: **0.46 ms** | N/A |

### 5.2 Cost Ratio

| Comparison | Ratio |
|------------|-------|
| Skeleton path vs. CLIP path (UCF, per snippet) | **~87x** more expensive (2,079 ms / 24 ms) |
| Skeleton path vs. CLIP path (XD 24fps, per snippet) | **~520x** more expensive (2,079 ms / 4 ms) |
| RTMPose vs. CLIP per frame | **28.4x** more expensive |
| Extraction vs. Classification (skeleton path) | **~1,980x** ratio |
| Extraction vs. Classification (CLIP path, UCF) | **~34x** ratio (23.3 ms / 0.69 ms) |

### 5.3 Full Video Processing Time Estimate

For a typical UCF-Crime video (~500 snippets):

| Pipeline | Estimated Time |
|----------|---------------|
| Skeleton extraction (RTMPose) | 500 x 64 x 30.07 ms = **~16 min** |
| CTR-GCN feature extraction | 500 x 154.17 ms = **~1.3 min** |
| CLIP feature extraction | 500 x 23.3 ms = **~11.7 sec** |
| MIL training (1 epoch, ~200 batches) | ~200 x 1 ms = **~0.2 sec** |

---

## 6. Key Insights

### 6.1 The Skeleton Bottleneck

RTMPose-m + YOLOX accounts for **92.6%** of the skeleton pipeline cost (1,924 ms out of 2,079 ms). The fundamental issue is **no batch inference** -- rtmlib processes frames one at a time, each requiring a full YOLOX detection pass followed by RTMPose pose estimation. This is a library-level constraint, not a model architecture issue.

### 6.2 CLIP's Batch Advantage

Despite having the most parameters (86.19M vs. RTMPose's ~13M), CLIP is **28x faster per frame** because batch GPU inference amortizes the overhead. Processing 64 frames in a single batch (67.79 ms) is faster than processing 2 frames individually through RTMPose (60.14 ms).

### 6.3 Parameter Efficiency

| Model | Params | Per-Frame Cost | Cost per Parameter |
|-------|--------|---------------|-------------------|
| CLIP ViT-B/16 | 86.19M | 1.06 ms | 0.012 ns/param |
| RTMPose + YOLOX | ~13M | 30.07 ms | 2.31 ns/param |
| CTR-GCN (4-stream) | 5.68M | 154.17 ms/snippet | 27.1 ns/param |

CLIP is the most parameter-efficient backbone by a wide margin, thanks to the Transformer architecture's parallelism on GPU.

### 6.4 Memory Profiles

| Component | GPU Memory | Context |
|-----------|-----------|---------|
| CLIP ViT-B/16 (B=64) | 1,062.5 MB | Largest single allocation; fits comfortably in 24 GB |
| RTMPose + YOLOX | 213.0 MB | Modest; ONNX Runtime manages its own memory pool |
| CTR-GCN (4-stream) | 29.1 MB | Negligible; small GCN on 17-joint graph |
| All 5 MIL heads | 10.6-21.7 MB | Trivial; frozen-feature classifiers |

Maximum peak memory from any single component is 1,062.5 MB (CLIP batch=64). Each backbone was measured in a separate environment; they do not run concurrently, so summing is not valid. The RTX 4090's 24 GB VRAM is heavily underutilized, suggesting room for larger batch sizes or concurrent extraction if library support permits.

### 6.5 Gated Fusion vs. Late Fusion

| Aspect | Gated Fusion | Late Fusion |
|--------|-------------|-------------|
| Parameters | 498.11K | 633.22K |
| MACs | 15.96M | 20.29M |
| FLOPs | 31.92M | 40.57M |
| Latency | 1.050 ms | 1.153 ms |
| Throughput | 15,237 S/s | 13,874 S/s |

Gated Fusion is **21% lighter in parameters** and **10% faster** than Late Fusion. The reduction comes from projecting both modalities into a shared 256-dim space before the gate, rather than running two independent full-size classification heads. This is a favorable result for the thesis: the more sophisticated fusion mechanism is also the more efficient one.

---

## 7. Implications for Thesis

1. **Computational cost is dominated by skeleton extraction, not model complexity.** The MIL training loop itself is near-instantaneous. Research iteration speed is gated by the one-time feature extraction.

2. **CLIP features are extremely cheap** relative to skeleton features. The 1 FPS sampling + batch inference makes CLIP extraction ~87x (UCF) to ~520x (XD-Violence) cheaper per snippet. This justifies the dual-modal approach: adding CLIP to a skeleton pipeline costs almost nothing at inference time.

3. **The Gated Fusion head adds negligible overhead** (~1 ms/batch) while being lighter than Late Fusion. The thesis can claim efficiency alongside accuracy improvements.

4. **RTMPose batch support could significantly accelerate the skeleton pipeline.** Currently rtmlib does not support batch inference, making per-frame processing the main bottleneck. A theoretical lower bound is 30 ms / 64 frames = 0.47 ms/frame, but this assumes perfect linear speedup which is unlikely for detector+pose pipelines — this figure is an optimistic reference only, not a benchmark result.

5. **I3D has the highest single-forward-pass FLOPs** at 107.9 GFLOPs per clip. Note this is a per-clip cost and not directly comparable to CLIP's per-frame 22.5 GFLOPs or RTMPose's per-frame 3.2 GFLOPs — normalized per snippet: I3D 107.9 G, CLIP (UCF) ~495 G (22 frames x 22.5), RTMPose ~206 G (64 frames x 3.2). Using pre-extracted I3D features was still the correct decision as it does not support incremental updates.

---

## 8. Reproduction

### MIL Classification Heads

```bash
conda run -n vcc-main python scripts/benchmark_models.py
```

### Backbone Feature Extractors

```bash
# All environments at once (recommended):
C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --all

# Individual components:
C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --clip
C:/Anaconda/envs/vcc-skeleton/python.exe scripts/benchmark_backbones.py --rtmpose
C:/Anaconda/envs/vcc-ctrgcn/python.exe scripts/benchmark_backbones.py --ctrgcn

# Combine results into table:
C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --combine
```

### Output Files

| File | Contents |
|------|---------|
| `results/benchmark_models.csv` | MIL head metrics (5 models) |
| `results/backbone_bench_clip.json` | CLIP ViT-B/16 detailed metrics |
| `results/backbone_bench_rtmpose.json` | RTMPose + YOLOX detailed metrics |
| `results/backbone_bench_ctrgcn.json` | CTR-GCN 4-stream detailed metrics |
| `results/backbone_bench_combined.csv` | Combined backbone comparison |

---

## 9. LaTeX Tables (Thesis-Ready)

### MIL Classification Heads

```latex
\begin{table}[t]
\centering
\caption{Model complexity comparison.}
\label{tab:model-complexity}
\begin{tabular}{lrrrrr}
\toprule
Model & Params (K) & MACs (M) & Latency (ms) & Throughput (S/s) & Mem (MB) \\
\midrule
Skeleton{-}Only & 37.57 & 1.21 & 0.504 & 31,766 & 10.6 \\
CLIP{-}Only & 595.65 & 19.07 & 0.690 & 23,181 & 14.8 \\
Late Fusion & 633.22 & 20.29 & 1.153 & 13,874 & 17.8 \\
Gated Fusion & 498.11 & 15.96 & 1.050 & 15,237 & 21.7 \\
RTFM{-}I3D & 137.41 & 4.46 & 0.460 & 34,786 & 18.8 \\
\bottomrule
\end{tabular}
\end{table}
```

### Backbone Feature Extractors

```latex
\begin{table}[t]
\centering
\caption{Computational cost comparison of backbone feature extractors.}
\label{tab:backbone-cost}
\begin{tabular}{lrrrrr}
\toprule
Backbone & Params (M) & FLOPs (G) & Latency & Throughput & GPU Mem (MB) \\
\midrule
CLIP ViT{-}B/16 & 86.2 & 22.5 & 67.8 ms/B & 944 f/s & 1,062 \\
RTMPose{-}m + YOLOX & $\sim$13.0 & $\sim$3.2 & 30.1 ms/f & 33.3 f/s & 213 \\
CTR{-}GCN (4{-}stream) & 5.7 & --- & 154.2 ms/sn & 6.5 sn/s & 29 \\
I3D RGB & $\sim$25.0 & $\sim$107.9 & Pre-extracted & --- & --- \\
\bottomrule
\end{tabular}
\vspace{2mm}
\footnotesize{$\sim$ denotes published (not measured) values. B = batch, f = frame, sn = snippet (64 frames).}
\end{table}
```
