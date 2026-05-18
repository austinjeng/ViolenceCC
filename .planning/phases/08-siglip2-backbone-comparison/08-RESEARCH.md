# Phase 8: SigLIP2 Backbone Comparison - Research

**Researched:** 2026-05-19
**Domain:** Visual-language backbone replacement (CLIP -> SigLIP2), feature extraction, ablation comparison
**Confidence:** HIGH

## Summary

Phase 8 replaces the CLIP ViT-B/16 visual-language backbone with SigLIP2 Giant (google/siglip2-giant-opt-patch16-384) and re-runs the entire ablation matrix on both UCF-Crime and XD-Violence to produce a direct backbone comparison for the thesis. The key finding is that the existing `vcc-main` environment already supports SigLIP2 Giant with **zero new package installs** -- open-clip-torch 3.3.0 and timm 1.0.26 (both currently installed) fully support it.

The critical architectural impact is a dimensionality change: SigLIP2 Giant's `encode_image()` outputs **[B, 1536]** (verified empirically) vs CLIP ViT-B/16's **[B, 512]**. With the existing mean+max pooling strategy, cached features become **[N_snippets, 3072]** vs the current **[N_snippets, 1024]**. This requires updating `clip_dim` in all YAML configs and the `CLIPProj` / `GatedFusion` / `LateFusion` model constructors (which already accept `clip_dim` as a parameter -- no model code changes needed, only config changes). Extraction time for both datasets is estimated at ~2.5 hours total on the RTX 4090.

**Primary recommendation:** Parameterize `extract_clip.py` with a `--backbone` flag (`clip-vit-b-16` or `siglip2-giant`) that controls model loading, preprocessing, and output subdirectory. Store SigLIP2 features in `E:/features/{dataset}/siglip2/` (and `siglip2_mean/` for mean-only pooling). Create a parallel set of YAML configs with `clip_dim: 3072` and `clip_features: E:/features/{dataset}/siglip2`. The model architecture code (`CLIPProj`, `GatedFusion`, `LateFusion`) requires no changes -- `clip_dim` is already a constructor parameter.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SigLIP2 feature extraction | Extraction script (offline) | GPU (RTX 4090) | Offline batch extraction, same as CLIP pipeline |
| Feature cache storage | Filesystem (E:/features/) | -- | Same .npy per-video pattern, different subdirectory |
| Model architecture adaptation | YAML config | -- | `clip_dim` parameter already exists; no code changes |
| Ablation orchestration | `run_ablations.py` queues | -- | New queue entries, same RunSpec pattern |
| Comparison table generation | Analysis script | -- | Post-hoc: merge results-index.csv rows by variant |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVAL-02 (extended) | All model variants evaluated with SigLIP2 features on both datasets | Config-only change: `clip_dim: 3072`, `clip_features` path swap; same train.py / evaluate.py |
| EVAL-03 (extended) | 3-seed stability for SigLIP2 Gated Fusion on both datasets | Same seed set {42, 123, 2024}; same run_ablations.py queue pattern |
| EVAL-04 (extended) | Side-by-side CLIP vs SigLIP2 comparison table for thesis | Merge results-index.csv rows; backbone column differentiator |
</phase_requirements>

## Standard Stack

### Core (Already Installed -- No New Packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| open-clip-torch | 3.3.0 | SigLIP2 model loading via `create_model_and_transforms('ViT-gopt-16-SigLIP2-384', pretrained='webli')` | Already in vcc-main; supports SigLIP2 since v2.31.0 [VERIFIED: vcc-main env + HuggingFace model card] |
| timm | 1.0.26 | SigLIP2 vision backbone (`vit_giantopt_patch16_siglip_384`) with MAP pooling | Already in vcc-main; required >= 1.0.15 for SigLIP2 [VERIFIED: vcc-main env] |
| PyTorch | 2.6.0 | Training and inference in vcc-main | Already installed; no change needed [VERIFIED: existing env] |

### Supporting (Already Installed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| decord | existing | XD-Violence video frame decoding | Same as Phase 2 CLIP extraction |
| numpy | existing | Feature array storage (.npy) | Same format as existing caches |
| PIL/Pillow | existing | UCF-Crime PNG frame loading | Same as Phase 2 |
| scikit-learn | existing | AUC/AP evaluation metrics | Same as Phase 4/4c |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SigLIP2 Giant (1.16B vis params) | SigLIP2 SO400M (400M params) | 30% lighter but weaker; Giant is the flagship for thesis impact |
| SigLIP2 via open-clip-torch | SigLIP2 via HuggingFace transformers | Would require adding `transformers` dependency; open-clip matches existing CLIP API exactly |
| mean+max pooling (3072-d) | mean-only pooling (1536-d) | Include both as ablation rows, matching CLIP pooling ablation structure |

**Installation:**
```bash
# NO installation needed -- all packages already present in vcc-main
conda activate vcc-main
python -c "import open_clip; print(open_clip.__version__)"  # 3.3.0
python -c "import timm; print(timm.__version__)"            # 1.0.26
```

**Version verification:** [VERIFIED: empirically tested on this machine 2026-05-19]
```
open-clip-torch: 3.3.0 (PyPI release 2026-02-27)
timm: 1.0.26 (installed in vcc-main)
```

## Package Legitimacy Audit

> No new packages are installed in this phase. Both `open-clip-torch` and `timm` are existing dependencies verified in Phase 1 and continuously used since Phase 2.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| open-clip-torch | PyPI | 3+ yrs | high | github.com/mlfoundations/open_clip | [OK] | Approved (already installed) |
| timm | PyPI | 5+ yrs | high | github.com/huggingface/pytorch-image-models | [OK] | Approved (already installed) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Phase 8 Feature Extraction & Comparison Pipeline
=================================================

Video Frames (UCF PNGs / XD mp4)
    |
    v
[extract_clip.py --backbone siglip2-giant]
    |
    +-- load model: open_clip.create_model_and_transforms(
    |       'ViT-gopt-16-SigLIP2-384', pretrained='webli')
    |
    +-- preprocess: Resize(384,384) + Normalize(0.5, 0.5)
    |       (vs CLIP: Resize(224)+CenterCrop(224) + ImageNet norm)
    |
    +-- encode_image -> [B, 1536] per frame
    |       (vs CLIP: [B, 512] per frame)
    |
    +-- mean+max pool per snippet -> [3072] per snippet
    |       (vs CLIP: [1024] per snippet)
    |
    +-- save: E:/features/{dataset}/siglip2/{video_id}.npy
            shape [N_snippets, 3072], dtype float32

SigLIP2 Features + Existing Skeleton Features
    |
    v
[train.py --config configs/gated_fusion_siglip2.yaml]
    |
    +-- model.clip_dim = 3072  (was 1024)
    |   model.shared_dim = 256 (unchanged)
    |   CLIPProj: Linear(3072 -> 512) -> LN -> MILHead
    |   GatedFusion: Linear(3072 -> 256) -> LN -> gate -> MILHead
    |
    v
[evaluate.py + results-index.csv]
    |
    v
[Comparison table: CLIP vs SigLIP2 side-by-side]
```

### Recommended Project Structure

```
configs/
├── skeleton_only.yaml              # (unchanged -- no CLIP dependency)
├── clip_only.yaml                  # (existing CLIP, clip_dim: 1024)
├── clip_only_siglip2.yaml          # NEW: clip_dim: 3072, siglip2 path
├── clip_only_xd_siglip2.yaml       # NEW
├── late_fusion_siglip2.yaml         # NEW: clip_dim: 3072
├── late_fusion_xd_siglip2.yaml      # NEW
├── gated_fusion_siglip2.yaml        # NEW: clip_dim: 3072
├── gated_fusion_xd_siglip2.yaml     # NEW
├── gated_fusion_siglip2_2person.yaml       # NEW: pooling ablation
├── gated_fusion_xd_siglip2_2person.yaml    # NEW
├── gated_fusion_siglip2_clip_mean.yaml     # NEW: mean-only pooling
└── gated_fusion_xd_siglip2_clip_mean.yaml  # NEW

E:/features/
├── ucf/
│   ├── skeleton/          # (existing, unchanged)
│   ├── clip/              # (existing CLIP 1024-d)
│   ├── clip_mean/         # (existing CLIP mean-only 512-d)
│   ├── siglip2/           # NEW: SigLIP2 mean+max 3072-d
│   └── siglip2_mean/      # NEW: SigLIP2 mean-only 1536-d
└── xd/
    ├── skeleton/          # (existing, unchanged)
    ├── clip/              # (existing CLIP 1024-d)
    ├── clip_mean/         # (existing CLIP mean-only 512-d)
    ├── siglip2/           # NEW
    └── siglip2_mean/      # NEW

scripts/
└── extract_clip.py        # MODIFIED: add --backbone flag
```

### Pattern 1: Backbone-Parameterized Extraction

**What:** Add a `--backbone` CLI argument to `extract_clip.py` that selects model, preprocessing, output dimension, and output subdirectory.

**When to use:** When the extraction script must support multiple vision backbones while reusing the same snippet boundary files and temporal alignment logic.

**Example:**
```python
# Source: verified empirically on this machine (2026-05-19)
BACKBONE_CONFIGS = {
    "clip-vit-b-16": {
        "model_name": "ViT-B-16",
        "pretrained": "openai",
        "embed_dim": 512,       # encode_image output dim
        "output_subdir": "clip",
        "mean_subdir": "clip_mean",
    },
    "siglip2-giant": {
        "model_name": "ViT-gopt-16-SigLIP2-384",
        "pretrained": "webli",
        "embed_dim": 1536,      # encode_image output dim
        "output_subdir": "siglip2",
        "mean_subdir": "siglip2_mean",
    },
}

def load_vision_model(backbone: str, device: str = "cuda"):
    cfg = BACKBONE_CONFIGS[backbone]
    model, _, preprocess = open_clip.create_model_and_transforms(
        cfg["model_name"], pretrained=cfg["pretrained"]
    )
    model.eval().to(device)
    return model, preprocess, cfg
```

### Pattern 2: Config-Only Model Adaptation

**What:** The model architecture code (`CLIPProj`, `GatedFusion`, `LateFusion`) already accepts `clip_dim` as a constructor parameter. Changing the backbone only requires new YAML configs.

**When to use:** When the projection layers automatically adapt to input dimension.

**Example:**
```yaml
# configs/gated_fusion_siglip2.yaml
model:
  variant: gated_fusion
  skel_dim: 256           # unchanged (skeleton backbone unchanged)
  clip_dim: 3072          # was 1024; SigLIP2 mean+max = 2 * 1536
  shared_dim: 256         # projection target unchanged
  head_hidden: [128, 32]  # MIL head unchanged
  dropout: 0.3

paths:
  skeleton_features: "E:/features/ucf/skeleton"    # unchanged
  clip_features: "E:/features/ucf/siglip2"         # NEW path
```

### Pattern 3: Ablation Queue Extension

**What:** Add `phase8_*` queues to `run_ablations.py` following the exact same `RunSpec` pattern as Phase 4/4c.

**When to use:** For systematic execution of all SigLIP2 ablation runs.

**Example:**
```python
"phase8_ucf_main": [
    RunSpec("ucf", "clip_only",     42, "configs/clip_only_siglip2.yaml",     "siglip2"),
    RunSpec("ucf", "late_fusion",   42, "configs/late_fusion_siglip2.yaml",   "siglip2"),
    RunSpec("ucf", "gated_fusion",  42, "configs/gated_fusion_siglip2.yaml",  "siglip2"),
],
# Note: skeleton_only is NOT re-run -- it uses no visual features
```

### Anti-Patterns to Avoid

- **Separate extraction script for SigLIP2:** Do NOT create `extract_siglip2.py`. The extraction logic (snippet boundaries, frame sampling, pooling) is identical -- only model loading and preprocessing differ. Parameterize the existing script.
- **Modifying model architecture code for SigLIP2:** The existing `clip_dim` parameter in all model constructors handles arbitrary input dimensions. Do NOT add SigLIP2-specific branches to `CLIPProj`, `GatedFusion`, or `LateFusion`.
- **Re-running skeleton-only baseline:** Skeleton features are backbone-independent. The Skeleton-Only results from Phase 4/4c are reused directly in the comparison table.
- **Changing shared_dim for SigLIP2:** Keep `shared_dim: 256` identical to CLIP configs. The learned projection absorbs the dimensionality difference. Changing `shared_dim` would invalidate the controlled comparison.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SigLIP2 model loading | Custom HuggingFace transformers integration | `open_clip.create_model_and_transforms('ViT-gopt-16-SigLIP2-384', pretrained='webli')` | Already works in the existing env; identical API to CLIP loading |
| Image preprocessing for SigLIP2 | Custom resize/normalize pipeline | Use the `preprocess` returned by `create_model_and_transforms()` | SigLIP2 uses different normalization (0.5, 0.5) and no center crop; the returned transform handles this automatically |
| Dimension adaptation | Custom wrapper layers | `clip_dim` YAML config parameter | All model constructors already parameterize input dimension |

**Key insight:** This phase is almost entirely a "change config, re-run" operation. The extraction script needs one new flag, and the model code needs zero changes. The complexity is in orchestration (12 new configs, ~20 training runs, extraction for 2 datasets) not in architecture.

## Common Pitfalls

### Pitfall 1: Wrong Output Dimension Assumption
**What goes wrong:** Assuming SigLIP2 Giant outputs 1152-d (the ViT internal embed_dim) instead of 1536-d (the MAP-pooled output dimension).
**Why it happens:** The Google model card says "1152" for the vision encoder width, but the open-clip TimmModel with MAP pooling projects to `embed_dim=1536` (the open_clip config's embed_dim, not the ViT's).
**How to avoid:** Verified empirically: `model.encode_image(x).shape[-1] == 1536`. Mean+max pooling produces 3072-d. Set `clip_dim: 3072` in configs.
**Warning signs:** Shape mismatch errors in `nn.Linear(clip_dim, ...)` at model construction time.

### Pitfall 2: Preprocessing Mismatch Between CLIP and SigLIP2
**What goes wrong:** Using CLIP's preprocessing (Resize(224) + CenterCrop + ImageNet normalization) for SigLIP2 frames, producing garbage features.
**Why it happens:** The extraction script currently hardcodes CLIP preprocessing.
**How to avoid:** Always use the `preprocess` transform returned by `create_model_and_transforms()`. SigLIP2 uses Resize(384, 384) with squash (no crop) and mean/std=(0.5, 0.5, 0.5).
**Warning signs:** Anomalously low AUC/AP (near random baseline) with SigLIP2 features.

### Pitfall 3: Feature Dimension Assertion Failures in Extraction Script
**What goes wrong:** The existing `extract_clip.py` has hardcoded assertions: `assert feats.shape[1] == expected_dim` where `expected_dim = 1024` for mean+max or `512` for mean-only.
**Why it happens:** These assertions were written for CLIP ViT-B/16's 512-d output.
**How to avoid:** Parameterize `expected_dim` based on backbone config: `512` for CLIP, `1536` for SigLIP2 (and `1024` vs `3072` for mean+max).
**Warning signs:** Assertion errors during extraction with SigLIP2.

### Pitfall 4: Mixing CLIP and SigLIP2 Features in the Same Run
**What goes wrong:** A config points `clip_features` to the wrong directory (e.g., `E:/features/ucf/clip` instead of `E:/features/ucf/siglip2`), silently loading CLIP features for a "SigLIP2" run.
**Why it happens:** Copy-paste error in YAML configs.
**How to avoid:** Validate feature dimension at dataset load time. SigLIP2 files are [N, 3072]; CLIP files are [N, 1024]. Add a dimension check in `MILFeatureDataset` that compares loaded `clip.shape[1]` against config's `clip_dim`.
**Warning signs:** "SigLIP2" run produces identical results to CLIP run.

### Pitfall 5: SigLIP2 Offline Loading Bug (Issue #1068)
**What goes wrong:** When loading SigLIP2 models from a cached local copy without internet, the wrong image preprocessor is silently loaded, producing incorrect embeddings.
**Why it happens:** Known open-clip bug (github.com/mlfoundations/open_clip/issues/1068) with offline SigLIP2 loading.
**How to avoid:** Ensure the first extraction run has internet access to download and cache the model correctly. Subsequent runs use the cached model. Verify the preprocessing transform includes `Resize(size=(384, 384))` and `Normalize(mean=(0.5, 0.5, 0.5))` at startup.
**Warning signs:** Preprocessing shows `Resize(224)` or `CenterCrop` when using SigLIP2.

### Pitfall 6: VRAM Pressure During Extraction
**What goes wrong:** Out-of-memory errors with batch_size=64 (the current CLIP default).
**Why it happens:** SigLIP2 Giant vision tower is 1.16B params (vs CLIP's 86M); peak VRAM at batch=32 is ~10.9 GB vs CLIP's ~1 GB.
**How to avoid:** Reduce default `--batch-size` to 16 for SigLIP2 (peak ~10.4 GB, well within 24 GB RTX 4090). The throughput difference between batch=8 and batch=32 is minimal (~68 vs ~66 img/s) due to the model being compute-bound.
**Warning signs:** CUDA OOM at extraction startup.

## Code Examples

### Loading SigLIP2 Giant in open-clip-torch

```python
# Source: verified on this machine (open-clip-torch 3.3.0, timm 1.0.26)
import open_clip

# Method 1: create_model_and_transforms (matches existing CLIP loading pattern)
model, preprocess_train, preprocess_val = open_clip.create_model_and_transforms(
    'ViT-gopt-16-SigLIP2-384', pretrained='webli'
)
model.eval().cuda()

# Method 2: create_model_from_pretrained (newer API, also works)
from open_clip import create_model_from_pretrained
model, preprocess = create_model_from_pretrained('hf-hub:timm/ViT-gopt-16-SigLIP2-384')
```

### SigLIP2 Preprocessing Comparison

```python
# Source: verified empirically (2026-05-19)

# CLIP ViT-B/16 preprocessing:
# Compose(
#     Resize(224, bicubic)
#     CenterCrop(224, 224)
#     MaybeConvertMode()
#     MaybeToTensor()
#     Normalize(mean=(0.48145466, 0.4578275, 0.40821073),
#               std=(0.26862954, 0.26130258, 0.27577711))
# )

# SigLIP2 Giant preprocessing:
# Compose(
#     Resize((384, 384), bicubic)       # squash/stretch, NO center crop
#     MaybeConvertMode()
#     MaybeToTensor()
#     Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
# )
```

### Backbone-Aware Feature Dimension in Extraction

```python
# Source: project-specific adaptation pattern
def extract_clip_snippet(frames, model, preprocess, batch_size, device, pool, embed_dim):
    """embed_dim: 512 for CLIP, 1536 for SigLIP2."""
    expected_dim = embed_dim if pool == "mean" else embed_dim * 2
    if len(frames) == 0:
        return np.zeros(expected_dim, dtype=np.float32)

    tensors = torch.stack([preprocess(f) for f in frames])
    all_feats = []
    for i in range(0, len(tensors), batch_size):
        batch = tensors[i:i+batch_size].to(device)
        with torch.no_grad():
            feats = model.encode_image(batch)                    # [B, embed_dim]
            feats = feats / feats.norm(dim=-1, keepdim=True)     # L2 normalize
        all_feats.append(feats.cpu().float())

    embeddings = torch.cat(all_feats, dim=0)   # [N, embed_dim]
    mean_feat = embeddings.mean(dim=0)
    if pool == "mean":
        return mean_feat.numpy().astype(np.float32)
    max_feat = embeddings.max(dim=0).values
    return torch.cat([mean_feat, max_feat], dim=0).numpy().astype(np.float32)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CLIP ViT-B/16 (OpenAI, 2021) | SigLIP2 (Google, Feb 2025) | Feb 2025 | SigLIP2 trained on WebLI with sigmoid loss + decoder objectives + self-distillation; outperforms CLIP at all scales on zero-shot classification |
| openai/clip (frozen 2021) | open-clip-torch 3.3.0 | Ongoing | open-clip supports both CLIP and SigLIP2 via same API |
| CenterCrop preprocessing | Squash resize (SigLIP2) | Feb 2025 | SigLIP2 resizes to target without cropping; preserves more spatial information |

**Deprecated/outdated:**
- SigLIP v1 (original sigmoid loss only) superseded by SigLIP2 (decoder + self-distillation objectives)
- The `openai/clip` package remains frozen; open-clip-torch is the maintained alternative

## Verified Technical Specifications

### SigLIP2 Giant (ViT-gopt-16-SigLIP2-384) [VERIFIED: empirically tested 2026-05-19]

| Property | Value |
|----------|-------|
| open-clip model name | `ViT-gopt-16-SigLIP2-384` |
| pretrained weight ID | `webli` |
| Total parameters | 1,871,885,426 (1.87B) |
| Vision parameters | 1,163,659,776 (1.16B) |
| Text parameters | 708,225,650 (0.71B) |
| Input resolution | 384 x 384 |
| `encode_image()` output | **[B, 1536]** |
| mean+max pooled | **[N, 3072]** |
| mean-only pooled | **[N, 1536]** |
| FP16 model size (full) | 3.74 GB |
| FP16 vision-only size | 2.33 GB |
| timm vision model | `vit_giantopt_patch16_siglip_384` |
| timm pooling | MAP (Multihead Attention Pooling) |
| Normalization | mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5) |
| Resize mode | Squash (no center crop) |

### CLIP ViT-B/16 (for comparison) [VERIFIED: empirically tested 2026-05-19]

| Property | Value |
|----------|-------|
| open-clip model name | `ViT-B-16` |
| pretrained weight ID | `openai` |
| Total parameters | 149,620,737 (150M) |
| Vision parameters | 86,192,640 (86M) |
| Input resolution | 224 x 224 |
| `encode_image()` output | **[B, 512]** |
| mean+max pooled | **[N, 1024]** |
| mean-only pooled | **[N, 512]** |
| FP16 model size | ~0.30 GB |
| Normalization | ImageNet mean/std |
| Resize mode | Resize(224) + CenterCrop(224) |

### Inference Throughput on RTX 4090 [VERIFIED: benchmarked 2026-05-19]

| Backbone | Batch Size | Throughput (img/s) | ms/img | Peak VRAM (MB) |
|----------|-----------|-------------------|--------|----------------|
| CLIP ViT-B/16 | 64 | 2,167 | 0.5 | 1,061 |
| CLIP ViT-B/16 | 32 | 1,969 | 0.5 | 922 |
| SigLIP2 Giant | 32 | 66 | 15.1 | 10,854 |
| SigLIP2 Giant | 16 | 68 | 14.8 | 10,374 |
| SigLIP2 Giant | 8 | 68 | 14.6 | 10,135 |
| SigLIP2 Giant | 1 | 30 | 33.3 | 9,922 |

**Key insight:** SigLIP2 is ~32x slower per frame than CLIP, but extraction is still feasible (~2.5 hours total for both datasets). Batch sizes 8-32 have nearly identical throughput, meaning the model is compute-bound, not memory-bound. Use batch_size=16 for safe VRAM headroom.

### Extraction Time Estimates [ASSUMED -- based on throughput benchmarks + Phase 2 I/O patterns]

| Dataset | Videos | Est. Frames | SigLIP2 Time (encoder) | With I/O Overhead |
|---------|--------|-------------|----------------------|-------------------|
| UCF-Crime | 1,728 | ~51,840 | ~13 min | ~17 min |
| XD-Violence | 4,752 | ~356,400 | ~87 min | ~131 min |
| **Total** | **6,480** | **~408,240** | **~100 min** | **~2.5 hrs** |

### Storage Estimates

| Config | UCF | XD | Total |
|--------|-----|-----|-------|
| CLIP mean+max (1024-d) | 0.07 GB | 0.49 GB | 0.56 GB |
| SigLIP2 mean+max (3072-d) | 0.21 GB | 1.46 GB | 1.67 GB |
| SigLIP2 mean-only (1536-d) | 0.11 GB | 0.73 GB | 0.84 GB |

Disk space available: 1,520 GB free on E: drive. Storage is negligible.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Extraction I/O overhead adds ~30-50% to encoder-only time | Extraction Time Estimates | Total time could be 3-4 hrs instead of 2.5 hrs; still feasible in a single session |
| A2 | Average ~30 frames/video (UCF) and ~75 frames/video (XD) for 1-FPS sampling | Extraction Time Estimates | Extraction time proportional to actual frame count; could vary +/-50% |
| A3 | SigLIP2 features will produce meaningfully different results from CLIP (thesis-worthy comparison) | Summary | If results are identical, the comparison is still valuable as a negative result |

## Open Questions (RESOLVED)

1. **Should mean+max pooling (3072-d) be the primary, or should we switch to mean-only (1536-d)?**
   - What we know: The CLIP pipeline uses mean+max (1024-d) as default, mean-only (512-d) as ablation. Phase 4c showed default pooling outperforms mean-only by 2.32% AP on XD.
   - What's unclear: Whether SigLIP2's MAP attention pooling (which already aggregates spatial info) makes the max-pool component redundant.
   - Recommendation: Keep mean+max as primary (3072-d) for controlled comparison with CLIP; include mean-only (1536-d) as a pooling ablation row, same as the CLIP setup.
   - **RESOLVED:** Mean+max (3072-d) is the primary pooling. Mean-only (1536-d) included as ablation row via gated_fusion_siglip2_clip_mean.yaml configs. Matches CLIP pooling ablation structure.

2. **Should `proj_dim` in CLIPProj change for SigLIP2?**
   - What we know: CLIP uses `clip_dim=1024 -> proj_dim=512`. SigLIP2 would use `clip_dim=3072 -> proj_dim=512`.
   - What's unclear: Whether the 6:1 compression ratio (3072->512) is too aggressive vs CLIP's 2:1 (1024->512).
   - Recommendation: Keep `proj_dim=512` and `shared_dim=256` identical to CLIP configs for controlled comparison. The learned projection should adapt. If results are anomalously poor, test `proj_dim=768` as a follow-up.
   - **RESOLVED:** Keep proj_dim=512 and shared_dim=256 unchanged for controlled comparison. All SigLIP2 configs mirror CLIP projection dimensions exactly.

3. **Should the Phase 7 sweep winner (lr=1e-3, k=2) be used for SigLIP2 runs?**
   - What we know: Phase 7 found XD benefits from lr=1e-3/k=2 (+3.72pp AP). UCF is hyperparameter-insensitive.
   - What's unclear: Whether SigLIP2's different feature distribution changes optimal hyperparameters.
   - Recommendation: Run the primary comparison with default hyperparameters (lr=1e-4, k=3) for controlled comparison. Optionally add one sweep winner config as a bonus comparison row.
   - **RESOLVED:** Primary comparison uses default hyperparameters (lr=1e-4, k=3). Phase 7 sweep winners not included in Phase 8 scope to keep the backbone comparison clean.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| open-clip-torch | SigLIP2 model loading | Yes | 3.3.0 | -- |
| timm | SigLIP2 vision backbone | Yes | 1.0.26 | -- |
| PyTorch | Inference + training | Yes | 2.6.0 | -- |
| CUDA 12.4 | GPU inference | Yes | 12.4 | -- |
| RTX 4090 (24GB) | Extraction + training | Yes | -- | -- |
| decord | XD video decoding | Yes | existing | -- |
| E: drive (1.5TB free) | Feature storage | Yes | -- | -- |
| HuggingFace Hub (internet) | First model download (~4GB) | Required once | -- | Cache after first download |

**Missing dependencies with no fallback:** None
**Missing dependencies with fallback:** None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | existing (pytest runs from project root) |
| Quick run command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x --timeout=30` |
| Full suite command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXT-01 | SigLIP2 extraction produces [N, 3072] features | unit | `pytest tests/test_extract_siglip2.py::test_output_shape -x` | No -- Wave 0 |
| EXT-02 | Backbone flag selects correct model/preprocess | unit | `pytest tests/test_extract_siglip2.py::test_backbone_config -x` | No -- Wave 0 |
| CFG-01 | SigLIP2 YAML configs load and build models | unit | `pytest tests/test_models.py::test_siglip2_configs -x` | No -- Wave 0 |
| CFG-02 | clip_dim=3072 produces correct model shapes | unit | `pytest tests/test_models.py::test_clip_dim_3072 -x` | No -- Wave 0 |
| ABL-01 | SigLIP2 queues in run_ablations.py are well-formed | unit | `pytest tests/test_run_ablations.py::test_phase8_queues -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x --timeout=30 -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_extract_siglip2.py` -- SigLIP2 extraction output shape and backbone config tests
- [ ] `tests/test_models.py::test_clip_dim_3072` -- Model construction with SigLIP2 dimensions
- [ ] `tests/test_run_ablations.py::test_phase8_queues` -- Phase 8 queue well-formedness

## Security Domain

> This phase involves no authentication, network services, user input handling, or cryptography. It is a purely offline feature extraction and model training workflow.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | -- |
| V3 Session Management | no | -- |
| V4 Access Control | no | -- |
| V5 Input Validation | no | -- (file paths from config, not user input) |
| V6 Cryptography | no | -- |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: empirical test] `open_clip.create_model_and_transforms('ViT-gopt-16-SigLIP2-384', pretrained='webli')` loads successfully in vcc-main (open-clip-torch 3.3.0, timm 1.0.26)
- [VERIFIED: empirical test] `model.encode_image(x).shape == [B, 1536]` confirmed on this machine
- [VERIFIED: empirical test] Vision tower parameters: 1,163,659,776 (1.16B)
- [VERIFIED: empirical test] Throughput benchmarks on RTX 4090 (30-68 img/s depending on batch size)
- [VERIFIED: empirical test] Peak VRAM: 9.9-10.9 GB depending on batch size
- [VERIFIED: open-clip GitHub] Model config JSON: `embed_dim: 1536, timm_pool: map, timm_proj: none` -- https://github.com/mlfoundations/open_clip/blob/main/src/open_clip/model_configs/ViT-gopt-16-SigLIP2-384.json
- [VERIFIED: timm test] `timm.create_model('vit_giantopt_patch16_siglip_384', num_classes=0, global_pool='map')` outputs [B, 1536]

### Secondary (MEDIUM confidence)
- [CITED: huggingface.co/blog/siglip2] SigLIP2 architecture details, training objectives, model sizes
- [CITED: github.com/mlfoundations/open_clip/pull/1033] SigLIP2 support merged Feb 21, 2025
- [CITED: github.com/mlfoundations/open_clip/issues/1068] Offline loading bug with wrong preprocessor
- [CITED: huggingface.co/google/siglip2-giant-opt-patch16-384] Google model card, 2B total params
- [CITED: huggingface.co/collections/timm/siglip-2] timm SigLIP2 collection with all model variants

### Tertiary (LOW confidence)
- [ASSUMED] Extraction I/O overhead estimates (30-50% on top of encoder time) based on Phase 2 patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new packages; all verified empirically on this machine
- Architecture: HIGH -- output dimensions verified empirically; model code confirmed to accept arbitrary clip_dim
- Pitfalls: HIGH -- identified from empirical testing (dimension mismatch, preprocessing differences, VRAM) and known issues (offline loading bug)
- Extraction time: MEDIUM -- throughput benchmarks are verified but total wall-clock depends on I/O patterns

**Research date:** 2026-05-19
**Valid until:** 2026-06-19 (30 days -- stable; no fast-moving dependencies)
