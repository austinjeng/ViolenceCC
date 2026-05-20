# Phase 9: SigLIP2-SO400M Backbone Comparison - Research

**Researched:** 2026-05-20
**Domain:** Visual-language backbone replacement (CLIP/SigLIP2-base -> SigLIP2 SO400M), feature extraction, three-way ablation comparison
**Confidence:** HIGH

## Summary

Phase 9 adds a third visual-language backbone -- SigLIP2 SO400M (google/siglip2-so400m-patch16-256) -- to the existing CLIP ViT-B/16 and SigLIP2 ViT-B/16-256 comparison from Phase 8. The key finding is that the existing infrastructure from Phase 8 makes this phase almost entirely mechanical: add one entry to `BACKBONE_CONFIGS` in `extract_clip.py`, create 10 new YAML configs with `clip_dim: 2304`, add 6 new queues to `run_ablations.py`, extract features, run ablations, and extend the comparison table to three columns.

The SO400M model has been empirically verified on this machine: `open_clip.create_model_and_transforms('ViT-SO400M-16-SigLIP2-256', pretrained='webli')` loads successfully in vcc-main (open-clip-torch 3.3.0), and `model.encode_image()` outputs **[B, 1152]**. With mean+max pooling, cached features become **[N_snippets, 2304]**. The model uses 256x256 input resolution and (0.5, 0.5, 0.5) normalization -- identical to the SigLIP2 ViT-B/16-256 from Phase 8. At batch_size=16, throughput is ~152 img/s on the RTX 4090 with ~4.6 GB peak VRAM, making extraction comfortable (~1 hour for both datasets). No new packages are required.

**Primary recommendation:** Add a `siglip2-so400m` entry to `BACKBONE_CONFIGS` with `embed_dim: 1152`, `output_subdir: siglip2_so400m`, `mean_subdir: siglip2_so400m_mean`. Create 10 YAML configs with `clip_dim: 2304` (or 1152 for mean-only). Add 6 `phase9_*` queues. Extract features for both datasets. Run the identical 14-run ablation matrix. Extend `generate_phase8_charts.py` (or create `generate_phase9_charts.py`) to produce a three-way comparison table.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SO400M feature extraction | Extraction script (offline) | GPU (RTX 4090) | Same offline batch extraction as CLIP and SigLIP2-base pipelines |
| Feature cache storage | Filesystem (E:/features/) | -- | New subdirectories `siglip2_so400m/` and `siglip2_so400m_mean/`; same .npy per-video format |
| Model architecture adaptation | YAML config | -- | `clip_dim: 2304` parameter; no model code changes |
| Ablation orchestration | `run_ablations.py` queues | -- | New `phase9_*` queue entries, same RunSpec pattern |
| Three-way comparison table | Analysis script | -- | Extend Phase 8 chart script to include SO400M column |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVAL-02 (extended) | All model variants evaluated with SigLIP2 SO400M features on both datasets | Config-only change: `clip_dim: 2304`, `clip_features` path to `siglip2_so400m/`; same train.py / evaluate.py |
| EVAL-03 (extended) | 3-seed stability for SO400M Gated Fusion on both datasets | Same seed set {42, 123, 2024}; same run_ablations.py queue pattern |
| EVAL-04 (extended) | Three-way comparison table (CLIP vs SigLIP2 ViT-B/16-256 vs SigLIP2 SO400M) for thesis | Extend Phase 8 comparison CSV with SO400M columns |
</phase_requirements>

## Standard Stack

### Core (Already Installed -- No New Packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| open-clip-torch | 3.3.0 | SO400M model loading via `create_model_and_transforms('ViT-SO400M-16-SigLIP2-256', pretrained='webli')` | Already in vcc-main; supports SO400M SigLIP2 [VERIFIED: empirically loaded on this machine 2026-05-20] |
| timm | 1.0.26 | SO400M vision backbone (`vit_so400m_patch16_siglip_256`) with MAP pooling | Already in vcc-main [VERIFIED: open-clip config references this timm model] |
| PyTorch | 2.6.0 | Training and inference in vcc-main | Already installed; no change needed [VERIFIED: existing env] |

### Supporting (Already Installed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| decord | existing | XD-Violence video frame decoding | Same as Phase 2/8 CLIP extraction |
| numpy | existing | Feature array storage (.npy) | Same format as existing caches |
| PIL/Pillow | existing | UCF-Crime PNG frame loading | Same as Phase 2/8 |
| scikit-learn | existing | AUC/AP evaluation metrics | Same as Phase 4/4c/8 |
| pandas | existing | Comparison table generation | Same as Phase 8 chart script |
| matplotlib + seaborn | existing | Comparison bar charts | Same as Phase 8 chart script |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SO400M patch16-256 (1152-d) | SO400M patch14-378 (1152-d, higher res) | patch14-378 uses 378x378 input -- different from SigLIP2-base's 256x256; breaks controlled comparison by introducing resolution as a confound. Stick with patch16-256 for apples-to-apples |
| SO400M patch16-256 | SO400M patch16-384 or -512 | Higher resolution variants exist but would introduce resolution as a confound vs Phase 8 SigLIP2-base (256). The thesis comparison should isolate model capacity, not resolution |
| Extending Phase 8 chart script | New standalone script | Phase 8 script uses a two-column COMPARISON_MAP; extending to three columns is cleaner than duplicating |

**Installation:**
```bash
# NO installation needed -- all packages already present in vcc-main
conda activate vcc-main
python -c "import open_clip; print(open_clip.__version__)"  # 3.3.0
```

**Version verification:** [VERIFIED: empirically tested on this machine 2026-05-20]
```
open-clip-torch: 3.3.0 (PyPI release 2026-02-27)
timm: 1.0.26 (installed in vcc-main)
```

## Package Legitimacy Audit

> No new packages are installed in this phase. All dependencies (`open-clip-torch`, `timm`, `pandas`, `matplotlib`, `seaborn`) are existing packages verified in prior phases and continuously used since Phase 2.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| open-clip-torch | PyPI | 3+ yrs | high | github.com/mlfoundations/open_clip | [OK] | Approved (already installed) |
| timm | PyPI | 5+ yrs | high | github.com/huggingface/pytorch-image-models | [OK] | Approved (already installed) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Phase 9 Feature Extraction & Three-Way Comparison Pipeline
===========================================================

Video Frames (UCF PNGs / XD mp4)
    |
    v
[extract_clip.py --backbone siglip2-so400m]
    |
    +-- load model: open_clip.create_model_and_transforms(
    |       'ViT-SO400M-16-SigLIP2-256', pretrained='webli')
    |
    +-- preprocess: Resize(256,256) + Normalize(0.5, 0.5)
    |       (identical to SigLIP2-base; vs CLIP: 224+CenterCrop + ImageNet norm)
    |
    +-- encode_image -> [B, 1152] per frame
    |       (vs SigLIP2-base: [B, 768], CLIP: [B, 512])
    |
    +-- mean+max pool per snippet -> [2304] per snippet
    |       (vs SigLIP2-base: [1536], CLIP: [1024])
    |
    +-- save: E:/features/{dataset}/siglip2_so400m/{video_id}.npy
            shape [N_snippets, 2304], dtype float32

SO400M Features + Existing Skeleton Features
    |
    v
[train.py --config configs/gated_fusion_so400m.yaml]
    |
    +-- model.clip_dim = 2304  (was 1536 for SigLIP2-base, 1024 for CLIP)
    |   model.shared_dim = 256 (unchanged)
    |   CLIPProj: Linear(2304 -> 512) -> LN -> MILHead
    |   GatedFusion: Linear(2304 -> 256) -> LN -> gate -> MILHead
    |
    v
[evaluate.py + results-index.csv]
    |
    v
[Three-way comparison table: CLIP vs SigLIP2-base vs SigLIP2 SO400M]
```

### Recommended Project Structure

```
configs/
+-- (existing CLIP and SigLIP2-base configs unchanged)
+-- clip_only_so400m.yaml              # NEW: clip_dim: 2304, so400m path
+-- clip_only_xd_so400m.yaml           # NEW
+-- late_fusion_so400m.yaml            # NEW: clip_dim: 2304
+-- late_fusion_xd_so400m.yaml         # NEW
+-- gated_fusion_so400m.yaml           # NEW: clip_dim: 2304
+-- gated_fusion_xd_so400m.yaml        # NEW
+-- gated_fusion_so400m_2person.yaml   # NEW: pooling ablation
+-- gated_fusion_xd_so400m_2person.yaml # NEW
+-- gated_fusion_so400m_clip_mean.yaml  # NEW: mean-only pooling
+-- gated_fusion_xd_so400m_clip_mean.yaml # NEW

E:/features/
+-- ucf/
|   +-- (existing: skeleton, clip, clip_mean, siglip2, siglip2_mean)
|   +-- siglip2_so400m/           # NEW: SO400M mean+max 2304-d
|   +-- siglip2_so400m_mean/      # NEW: SO400M mean-only 1152-d
+-- xd/
    +-- (existing: skeleton, clip, clip_mean, siglip2, siglip2_mean)
    +-- siglip2_so400m/           # NEW
    +-- siglip2_so400m_mean/      # NEW

scripts/
+-- extract_clip.py        # MODIFIED: add siglip2-so400m to BACKBONE_CONFIGS
+-- run_ablations.py       # MODIFIED: add phase9_* queues
+-- generate_phase9_charts.py  # NEW: three-way comparison table + charts
```

### Pattern 1: Add Third Backbone Entry to BACKBONE_CONFIGS

**What:** Add a `siglip2-so400m` entry to the existing `BACKBONE_CONFIGS` dict in `extract_clip.py`. This is the exact same pattern used in Phase 8 to add `siglip2-base`.

**When to use:** When adding a new vision backbone that shares the same extraction pipeline (snippet boundaries, frame sampling, pooling) but has different model loading, preprocessing, dimension, and output subdirectory.

**Example:**
```python
# Source: verified empirically on this machine (2026-05-20)
BACKBONE_CONFIGS = {
    "clip-vit-b-16": {
        "model_name": "ViT-B-16",
        "pretrained": "openai",
        "embed_dim": 512,
        "output_subdir": "clip",
        "mean_subdir": "clip_mean",
    },
    "siglip2-base": {
        "model_name": "ViT-B-16-SigLIP2-256",
        "pretrained": "webli",
        "embed_dim": 768,
        "output_subdir": "siglip2",
        "mean_subdir": "siglip2_mean",
    },
    "siglip2-so400m": {                              # NEW
        "model_name": "ViT-SO400M-16-SigLIP2-256",
        "pretrained": "webli",
        "embed_dim": 1152,
        "output_subdir": "siglip2_so400m",
        "mean_subdir": "siglip2_so400m_mean",
    },
}
```

### Pattern 2: Config-Only Model Adaptation (same as Phase 8)

**What:** Create new YAML configs that mirror existing CLIP configs but change `clip_dim` and `clip_features` path. No model code changes.

**Example:**
```yaml
# configs/gated_fusion_so400m.yaml
model:
  variant: gated_fusion
  skel_dim: 256
  clip_dim: 2304          # was 1536 (SigLIP2-base) / 1024 (CLIP); SO400M mean+max = 2 * 1152
  shared_dim: 256          # unchanged
  head_hidden: [128, 32]
  dropout: 0.3

paths:
  skeleton_features: "E:/features/ucf/skeleton"
  clip_features: "E:/features/ucf/siglip2_so400m"   # NEW path
```

### Pattern 3: Queue Extension (same as Phase 8)

**What:** Add `phase9_*` queues to `run_ablations.py` following the exact Phase 8 pattern.

**Example:**
```python
"phase9_ucf_main": [
    RunSpec("ucf", "clip_only",    42, "configs/clip_only_so400m.yaml",    "so400m"),
    RunSpec("ucf", "late_fusion",  42, "configs/late_fusion_so400m.yaml",  "so400m"),
    RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion_so400m.yaml", "so400m"),
],
# skeleton_only NOT re-run -- backbone-independent
```

### Pattern 4: Three-Way Comparison Table

**What:** Extend the Phase 8 two-column comparison to include a third backbone column. The comparison CSV format becomes:

```
Dataset, Variant, CLIP_AUC, CLIP_AP, SigLIP2_AUC, SigLIP2_AP, SO400M_AUC, SO400M_AP, Delta_CLIP_SO400M_AUC, Delta_CLIP_SO400M_AP
```

**When to use:** For the final thesis comparison table.

### Anti-Patterns to Avoid

- **Reusing `siglip2/` subdirectory for SO400M features:** SO400M outputs 1152-d (not 768-d like SigLIP2-base). Storing in the same `siglip2/` directory would overwrite Phase 8 features and break the three-way comparison. Use `siglip2_so400m/` and `siglip2_so400m_mean/`.
- **Changing shared_dim or proj_dim for SO400M:** Keep `shared_dim: 256` and `proj_dim: 512` identical to CLIP and SigLIP2-base configs. The learned projection absorbs the dimensionality difference. Changing projection dimensions invalidates the controlled comparison.
- **Re-running skeleton-only baseline:** Skeleton features are backbone-independent. The Skeleton-Only results from Phase 4/4c are reused directly.
- **Using a different SO400M variant (patch14 or higher resolution):** The thesis comparison must isolate backbone capacity, not input resolution. SigLIP2-base uses 256x256; SO400M patch16-256 also uses 256x256. Using SO400M patch14-378 (378x378) introduces resolution as a confound.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SO400M model loading | Custom HuggingFace transformers integration | `open_clip.create_model_and_transforms('ViT-SO400M-16-SigLIP2-256', pretrained='webli')` | Already works in existing env; identical API to CLIP and SigLIP2-base loading |
| Image preprocessing for SO400M | Custom resize/normalize pipeline | Use `preprocess` returned by `create_model_and_transforms()` | SO400M uses Resize(256,256) + Normalize(0.5,0.5,0.5); returned transform handles this automatically |
| Dimension adaptation | Custom wrapper layers | `clip_dim` YAML config parameter | All model constructors already parameterize input dimension |
| Extraction pipeline | New extraction script | `extract_clip.py --backbone siglip2-so400m` | Phase 8 infrastructure handles arbitrary backbones via BACKBONE_CONFIGS |

**Key insight:** Phase 9 is even more mechanical than Phase 8. Phase 8 built the backbone parameterization infrastructure; Phase 9 only adds one dict entry, 10 configs, 6 queues, extracts features, runs ablations, and extends the comparison table. The model architecture code requires zero changes.

## Common Pitfalls

### Pitfall 1: Wrong Output Dimension (1152 vs 768 vs 1536)
**What goes wrong:** Confusing SO400M's embed_dim with SigLIP2-base's (768) or Giant's (1536). Setting `clip_dim: 1536` (Phase 8 value) instead of `clip_dim: 2304` in SO400M configs.
**Why it happens:** Three different SigLIP2 variants have three different embed_dims (768, 1152, 1536). Easy to copy Phase 8 configs and forget to update the dimension.
**How to avoid:** Verified empirically: `model.encode_image(x).shape[-1] == 1152`. Mean+max pooling produces 2304-d. All SO400M configs must use `clip_dim: 2304` (or `clip_dim: 1152` for mean-only configs).
**Warning signs:** Shape mismatch errors in `nn.Linear(clip_dim, ...)` at model construction time. [VERIFIED: empirical test on this machine 2026-05-20]

### Pitfall 2: Overwriting Phase 8 SigLIP2-base Features
**What goes wrong:** Storing SO400M features in `E:/features/{dataset}/siglip2/` (the Phase 8 SigLIP2-base directory), overwriting the 768-d features with 1152-d features.
**Why it happens:** Copy-paste error from Phase 8 configs or BACKBONE_CONFIGS.
**How to avoid:** SO400M must use distinct subdirectories: `siglip2_so400m/` and `siglip2_so400m_mean/`. The `output_subdir` and `mean_subdir` fields in BACKBONE_CONFIGS enforce this.
**Warning signs:** Phase 8 SigLIP2-base ablation results change after Phase 9 extraction.

### Pitfall 3: Mixing SO400M and SigLIP2-base Features
**What goes wrong:** A config points `clip_features` to `E:/features/ucf/siglip2` (Phase 8 features, 1536-d) instead of `E:/features/ucf/siglip2_so400m` (Phase 9 features, 2304-d).
**Why it happens:** Copy-paste error in YAML configs; both paths contain "siglip2".
**How to avoid:** Validate feature dimension at dataset load time. SO400M files are [N, 2304]; SigLIP2-base files are [N, 1536]. The `MILFeatureDataset` will catch mismatches because `clip_dim` in the config won't match the loaded `.npy` shape.
**Warning signs:** "SO400M" run produces results identical to SigLIP2-base, or shape mismatch at dataloader time.

### Pitfall 4: Test Assertions Hardcoded to Two Backbones
**What goes wrong:** Existing `test_extract_siglip2.py::test_backbone_configs_keys()` asserts exactly `{"clip-vit-b-16", "siglip2-base"}`. Adding SO400M without updating this test causes a test failure.
**Why it happens:** Phase 8 tests were written for exactly 2 backbones.
**How to avoid:** Update `test_backbone_configs_keys()` to expect 3 keys: `{"clip-vit-b-16", "siglip2-base", "siglip2-so400m"}`. Add SO400M-specific config value tests. Update `test_run_ablations.py` for new queue counts and total unique run_names.
**Warning signs:** `pytest tests/test_extract_siglip2.py` fails immediately after adding SO400M to BACKBONE_CONFIGS.

### Pitfall 5: Total Queue Count Assertion in test_run_ablations.py
**What goes wrong:** `test_run_ablations.py::test_queue_definitions_complete()` asserts exactly 238 unique run_names. Adding 14 Phase 9 runs without updating this assertion causes a test failure.
**Why it happens:** The total count was set in Phase 8 for exactly the known queues.
**How to avoid:** Update the assertion to 252 (238 + 14 Phase 9 runs).
**Warning signs:** `pytest tests/test_run_ablations.py` fails with "expected 238, got 252".

### Pitfall 6: Batch Size Too Large for SO400M
**What goes wrong:** Using the default CLIP batch_size=64 with SO400M, causing slower-than-expected throughput due to memory pressure.
**Why it happens:** SO400M uses ~4.6 GB VRAM at batch=16 vs CLIP's ~1 GB. While batch=64 fits (~5.3 GB), there is no throughput benefit above batch=16 (152 img/s vs 154 img/s) since the model is compute-bound.
**How to avoid:** Use batch_size=16 for SO400M extraction (same recommendation as Phase 8 SigLIP2 extraction).
**Warning signs:** None critical -- batch=64 works within 24 GB -- but batch=16 is optimal for throughput/VRAM ratio.

## Code Examples

### Loading SigLIP2 SO400M in open-clip-torch

```python
# Source: verified on this machine (open-clip-torch 3.3.0, timm 1.0.26, 2026-05-20)
import open_clip

model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-SO400M-16-SigLIP2-256', pretrained='webli'
)
model.eval().cuda()

# encode_image output: [B, 1152]
# preprocess: Resize(256,256) + Normalize(0.5, 0.5, 0.5) -- identical to SigLIP2-base
```

### SO400M Preprocessing (Identical to SigLIP2-base)

```python
# Source: verified empirically (2026-05-20)

# SigLIP2 SO400M preprocessing:
# Compose(
#     Resize((256, 256), bicubic)       # squash/stretch, NO center crop
#     MaybeConvertMode()
#     MaybeToTensor()
#     Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
# )
# NOTE: Identical to SigLIP2 ViT-B/16-256 preprocessing
```

### YAML Config for SO400M Gated Fusion

```yaml
# configs/gated_fusion_so400m.yaml
# Source: project-specific, mirrors gated_fusion_siglip2.yaml with SO400M dimensions
seed: 42
dataset: ucf

paths:
  skeleton_features: "E:/features/ucf/skeleton"
  clip_features: "E:/features/ucf/siglip2_so400m"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: gated_fusion
  skel_dim: 256
  clip_dim: 2304          # SO400M mean+max = 2 * 1152
  shared_dim: 256
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32
  batch_size: 16
  num_workers: 4
  pin_memory: true

train:
  lr: 1.0e-4
  weight_decay: 1.0e-2
  epochs: 50
  warmup_epochs: 5
  patience: 10
  k_topk: 3
  margin: 1.0
  lam_sparse: 8.0e-3
  lam_smooth: 8.0e-4

wandb:
  project: violencecc
  mode: disabled
  tags: [phase9, gated_fusion, ucf, so400m]
```

## Verified Technical Specifications

### SigLIP2 SO400M (ViT-SO400M-16-SigLIP2-256) [VERIFIED: empirically tested 2026-05-20]

| Property | Value |
|----------|-------|
| open-clip model name | `ViT-SO400M-16-SigLIP2-256` |
| pretrained weight ID | `webli` |
| HuggingFace model ID | `google/siglip2-so400m-patch16-256` |
| Total parameters | 1,135,670,962 (1.14B) |
| Vision parameters | 427,888,064 (428M) |
| Text parameters | 707,782,898 (708M) |
| Input resolution | 256 x 256 |
| `encode_image()` output | **[B, 1152]** |
| mean+max pooled | **[N, 2304]** |
| mean-only pooled | **[N, 1152]** |
| FP16 model size (full) | 2.27 GB |
| FP16 vision-only size | 0.86 GB |
| timm vision model | `vit_so400m_patch16_siglip_256` |
| timm pooling | MAP (Multihead Attention Pooling) |
| Normalization | mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5) |
| Resize mode | Squash (no center crop) |

### Three-Backbone Comparison Table [VERIFIED: all measured on same RTX 4090]

| Property | CLIP ViT-B/16 | SigLIP2 ViT-B/16-256 | SigLIP2 SO400M-16-256 |
|----------|--------------|----------------------|----------------------|
| Vision params | 86M | 93M | 428M |
| Input resolution | 224x224 | 256x256 | 256x256 |
| encode_image dim | 512 | 768 | 1152 |
| mean+max dim | 1024 | 1536 | 2304 |
| clip_dim (YAML) | 1024 | 1536 | 2304 |
| Normalization | ImageNet | (0.5, 0.5, 0.5) | (0.5, 0.5, 0.5) |
| Resize mode | Resize(224)+CenterCrop | Squash(256) | Squash(256) |
| Throughput (batch=16) | ~2167 img/s | ~661 img/s | ~152 img/s |
| Peak VRAM (batch=16) | ~922 MB | ~1692 MB | ~4611 MB |

### Inference Throughput on RTX 4090 [VERIFIED: benchmarked 2026-05-20]

| Backbone | Batch Size | Throughput (img/s) | ms/img | Peak VRAM (MB) |
|----------|-----------|-------------------|--------|----------------|
| SO400M | 1 | 53 | 18.8 | 4,401 |
| SO400M | 8 | 138 | 7.2 | 4,496 |
| SO400M | 16 | 152 | 6.6 | 4,611 |
| SO400M | 32 | 154 | 6.5 | 4,834 |
| SO400M | 64 | 154 | 6.5 | 5,285 |

**Key insight:** SO400M throughput plateaus at batch=16. Compute-bound, not memory-bound. Use batch_size=16 for optimal throughput with safe VRAM headroom (4.6 GB of 24 GB).

### Extraction Time Estimates [ASSUMED: based on throughput benchmarks + Phase 2/8 I/O patterns]

| Dataset | Videos | Est. Frames | SO400M Time (encoder) | With I/O Overhead |
|---------|--------|-------------|----------------------|-------------------|
| UCF-Crime | 1,728 | ~51,840 | ~6 min | ~9 min |
| XD-Violence | 4,752 | ~356,400 | ~39 min | ~59 min |
| **Total** | **6,480** | **~408,240** | **~45 min** | **~68 min (~1.1 hrs)** |

### Storage Estimates

| Config | UCF | XD | Total |
|--------|-----|-----|-------|
| SO400M mean+max (2304-d) | 0.16 GB | 1.10 GB | 1.26 GB |
| SO400M mean-only (1152-d) | 0.08 GB | 0.55 GB | 0.63 GB |

Disk space available: 1,414 GB free on E: drive. Storage is negligible.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single CLIP backbone | Multi-backbone ablation (CLIP + SigLIP2 variants) | Phase 8-9 | Thesis strengthened by showing results are not backbone-specific |
| Two-way comparison (Phase 8) | Three-way comparison (Phase 9) | This phase | SO400M (428M vis params) fills gap between ViT-B (93M) and Giant (1.16B); shows scaling trend |
| CenterCrop preprocessing | Squash resize (SigLIP2 variants) | Phase 8 | Both SO400M and ViT-B use 256x256 squash; apples-to-apples within SigLIP2 family |

**Deprecated/outdated:**
- SigLIP v1 superseded by SigLIP2 (decoder + self-distillation objectives)
- The `openai/clip` package remains frozen; open-clip-torch is the maintained alternative

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Extraction I/O overhead adds ~30-50% to encoder-only time | Extraction Time Estimates | Total time could be 1.5 hrs instead of 1.1 hrs; still feasible in a single session |
| A2 | Average ~30 frames/video (UCF) and ~75 frames/video (XD) for 1-FPS sampling | Extraction Time Estimates | Extraction time proportional to actual frame count; could vary +/-50% |
| A3 | SO400M features will produce meaningfully different results from SigLIP2-base and CLIP (thesis-worthy comparison) | Summary | If results are nearly identical to SigLIP2-base, the comparison is still valuable as a scaling analysis (93M vs 428M visual params at same resolution shows diminishing returns) |
| A4 | The `so400m` cache_variant tag is sufficient to distinguish SO400M runs in results-index.csv | Pattern 3 | If collisions occur with Phase 8 `siglip2` tags, rename to more specific variant; risk is LOW because `so400m` is unique |

## Open Questions

1. **Should the three-way comparison script extend Phase 8's `generate_phase8_charts.py` or be a new script?**
   - What we know: Phase 8's script uses a two-column COMPARISON_MAP with hardcoded CLIP and SigLIP2 column names. Extending it to three columns requires restructuring the `build_comparison_table()` and `plot_comparison_bars()` functions.
   - What's unclear: Whether the Phase 8 charts should remain as-is (for reproducibility of Phase 8 deliverables) or be replaced by the three-way version.
   - Recommendation: Create a new `generate_phase9_charts.py` that produces the three-way table and charts. Leave Phase 8's script untouched. The three-way comparison supersedes the two-way for the thesis, but the Phase 8 script remains as documentation of Phase 8's deliverables.

2. **Should the thesis comparison table include the Phase 7 sweep winner (lr=1e-3, k=2) for SO400M?**
   - What we know: Phase 7 found XD benefits from lr=1e-3/k=2. Phase 8 excluded sweep winners to keep the backbone comparison clean (default hyperparameters only).
   - Recommendation: Keep the primary comparison at default hyperparameters (lr=1e-4, k=3) for controlled comparison, same decision as Phase 8. The thesis can note this as a limitation ("backbone comparison uses default hyperparameters; per-backbone tuning may yield different rankings").

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| open-clip-torch | SO400M model loading | Yes | 3.3.0 | -- |
| timm | SO400M vision backbone | Yes | 1.0.26 | -- |
| PyTorch | Inference + training | Yes | 2.6.0 | -- |
| CUDA 12.4 | GPU inference | Yes | 12.4 | -- |
| RTX 4090 (24GB) | Extraction + training | Yes | -- | -- |
| decord | XD video decoding | Yes | existing | -- |
| E: drive (1.4 TB free) | Feature storage | Yes | -- | -- |
| HuggingFace Hub (internet) | First model download (~2.3 GB) | Required once | -- | Cache after first download |

**Missing dependencies with no fallback:** None
**Missing dependencies with fallback:** None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | none (standard discovery) |
| Quick run command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_extract_siglip2.py tests/test_models.py tests/test_run_ablations.py -x -q` |
| Full suite command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-02 ext | SO400M config entry in BACKBONE_CONFIGS | unit | `pytest tests/test_extract_siglip2.py -x` | Yes (update needed) |
| EVAL-02 ext | clip_dim=2304 forward pass for all model variants | unit | `pytest tests/test_models.py -x` | Yes (new test needed) |
| EVAL-02 ext | Phase 9 queues exist in run_ablations.py | unit | `pytest tests/test_run_ablations.py -x` | Yes (update needed) |
| EVAL-03 ext | 3-seed results in results-index.csv | manual-only | Check CSV after queue execution | N/A |
| EVAL-04 ext | Three-way comparison table exists | manual-only | Run chart generation script | N/A |

### Sampling Rate
- **Per task commit:** `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_extract_siglip2.py tests/test_models.py tests/test_run_ablations.py -x -q`
- **Per wave merge:** `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_extract_siglip2.py` -- update `test_backbone_configs_keys` to expect 3 keys; add `test_so400m_config_values`; update dimension tests
- [ ] `tests/test_models.py` -- add `test_clip_dim_2304` forward pass test
- [ ] `tests/test_run_ablations.py` -- add Phase 9 queue assertions; update total unique run_names count from 238 to 252

## Existing Phase 8 Results (Baseline for Three-Way Comparison)

### CLIP vs SigLIP2-base Results [VERIFIED: from results-index.csv, 2026-05-20]

| Dataset | Variant | CLIP AUC | CLIP AP | SigLIP2 AUC | SigLIP2 AP |
|---------|---------|----------|---------|-------------|------------|
| UCF | CLIP/SigLIP2 Only | 0.8169 | 0.2234 | 0.7911 | 0.1962 |
| UCF | Late Fusion | 0.7871 | 0.1874 | 0.7993 | 0.2024 |
| UCF | Gated Fusion | 0.8227 | 0.2315 | 0.7961 | 0.2018 |
| XD | CLIP/SigLIP2 Only | 0.9113 | 0.7053 | 0.9168 | 0.7212 |
| XD | Late Fusion | 0.9000 | 0.6548 | 0.8984 | 0.6556 |
| XD | Gated Fusion | 0.9200 | 0.7192 | 0.9185 | 0.7192 |

These results form columns 1-2 of the three-way comparison. Phase 9 adds column 3 (SO400M).

## Sources

### Primary (HIGH confidence)
- open-clip-torch model list: `open_clip.list_models()` + `open_clip.list_pretrained()` verified on this machine [2026-05-20]
- open-clip model config: `open_clip.get_model_config('ViT-SO400M-16-SigLIP2-256')` verified on this machine [2026-05-20]
- SO400M encode_image output dimension: empirically verified `model.encode_image(x).shape == [1, 1152]` [2026-05-20]
- SO400M preprocessing: empirically verified `Resize(256,256) + Normalize(0.5,0.5,0.5)` [2026-05-20]
- SO400M throughput benchmarks: empirically measured on RTX 4090 [2026-05-20]
- Phase 8 BACKBONE_CONFIGS and queue structure: verified from `scripts/extract_clip.py` and `scripts/run_ablations.py` [2026-05-20]
- Phase 8 results: verified from `results/results-index.csv` [2026-05-20]

### Secondary (MEDIUM confidence)
- HuggingFace model card: https://huggingface.co/google/siglip2-so400m-patch16-256 [confirmed model exists, 1B params total]

### Tertiary (LOW confidence)
- None -- all claims verified empirically or from codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new packages; all verified empirically on this machine
- Architecture: HIGH -- exact replication of Phase 8 patterns with one new BACKBONE_CONFIGS entry
- Pitfalls: HIGH -- all dimension values verified empirically; test update requirements identified from codebase inspection
- Extraction feasibility: HIGH -- throughput and VRAM benchmarked on actual hardware

**Research date:** 2026-05-20
**Valid until:** indefinite (SO400M model weights are static; open-clip API is stable)
