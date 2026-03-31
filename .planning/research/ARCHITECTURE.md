# Architecture Patterns

**Project:** ViolenceCC — Dual-Modal (Skeleton + CLIP) Weakly Supervised VAD
**Researched:** 2026-03-31
**Confidence:** HIGH (PRD v2.3 is the authoritative spec; reference codebases verified against source)

---

## Reference Codebase Survey

The architecture recommendations below are grounded in a survey of the following codebases, all of which share the same task: weakly supervised VAD with pre-extracted features and MIL training.

| Codebase | Key Pattern Observed | Confidence |
|----------|---------------------|------------|
| RTFM (tianyu0207/RTFM) | Flat layout: main.py, train.py, model.py, dataset.py, option.py, test_10crop.py, list/ | HIGH — GitHub verified |
| MGFN (carolchenyx/MGFN) | Modular layout: models/, datasets/, utils/, config.py, option.py, main.py, train.py, test.py | HIGH — GitHub verified |
| VadCLIP (nwpu-zxr/VadCLIP) | Per-dataset scripts (ucf_train.py / xd_train.py), src/clip/, list/ for CSV split files | HIGH — GitHub verified |
| PEL4VAD (yujiangpu20/PEL4VAD) | Cleanest separation: model.py + modules.py + layers.py + loss.py + train.py + infer.py + test.py, ckpt/, list/, prompt_extract/ | HIGH — GitHub verified |
| TENT (DequanWang/tent) | Compact: tent.py (Tent class), norm.py, conf.py, cfgs/ YAML | HIGH — GitHub verified |

**Synthesis:** The dominant pattern across VAD codebases is a flat-to-moderately-structured layout with clear role separation between data loading, model definition, training, and evaluation. None of the reference codebases use large frameworks like PyTorch Lightning or Hydra — they stay simple and debuggable. This is appropriate for a single-researcher thesis project.

---

## Recommended Architecture

### System-Level View

```
Raw Videos (E:\ drive)
        |
        v
[Stage 1: Feature Pre-Extraction]  ← all backbones frozen, GPU-intensive, runs once
        |
   ┌────┴────────────────────────────┐
   |                                 |
   v                                 v
RTMPose skeleton                  CLIP ViT-B/16
extraction (rtmlib)               1 FPS frame sampling
COCO-17 per frame                 mean+max pooling
        |                                 |
        v                                 v
CTR-GCN NTU120 HRNet2D           [N_snippets, 512]
frozen forward pass              per-video npy file
4 streams (j/b/jm/bm)
        |
        v
weighted concat → [N_snippets, 256]
per-video npy file
        |
        v
[Feature Cache on disk]  ← E:\features\ or local SSD
    ucf_skeleton/     ucf_clip/
    xd_skeleton/      xd_clip/
    ucf_c_clip/       (corruption variants)
        |
        v
[Stage 2: MIL Fusion Training]  ← CPU/GPU, fast iteration, minutes per run
        |
    Dataset loader reads cached npy files
    Bags = (pos_snippets, neg_snippets) pairs per training step
    GatedFusion(F_skel[256], F_clip[512]) → F_fused[256]
    LayerNorm → MLP head → anomaly_score[0,1]
    MIL Ranking Loss minimized
        |
        v
[Saved checkpoint: fusion_head.pth]
        |
        v
[Stage 3: TTA at Test Time]  ← per-video online, minimal overhead
    Load cached features for test video
    Reset LN affine params (γ, β) to source-trained state
    Process 32-snippet batches sequentially
    Entropy minimization updates γ, β (TENT-style or SAR-style)
    Output: frame-level anomaly scores
        |
        v
[Evaluation]
    frame_level_AUC (UCF-Crime)
    frame_level_AP  (XD-Violence)
```

---

## Component Boundaries

Each component is defined by what it reads, what it writes, and what it must NOT touch.

### Component 1: Skeleton Extractor

**Responsibility:** Run RTMPose on raw video frames, aggregate top-2 persons per frame, run CTR-GCN frozen forward pass in 64-frame windows, save per-video feature arrays.

**Reads:** Raw video files (mp4/avi) from E:\
**Writes:** `features/ucf_skeleton/<video_id>.npy` shape `[N_snippets, 256]`
**Must NOT touch:** CLIP extraction, MIL training code, evaluation logic
**Key decisions:**
- Top-2 persons by confidence; weighted concat (j:b:jm:bm = 1:1:0.5:0.5) → 256-d
- 64-frame window with stride to produce N_snippets per video
- Missing-person handling: zero-pad if fewer than 2 persons detected
- Output dtype: float32

**Communicates with:** Feature Cache (writes), MIL Dataset Loader (its output is consumed)

### Component 2: CLIP Extractor

**Responsibility:** Sample frames at 1 FPS from raw video, run CLIP ViT-B/16 frozen visual encoder, apply mean+max pooling within each 64-frame snippet window, save per-video feature arrays.

**Reads:** Raw video files (mp4/avi) from E:\
**Writes:** `features/ucf_clip/<video_id>.npy` shape `[N_snippets, 512]`
**Must NOT touch:** Skeleton extraction, MIL training code
**Key decisions:**
- Strict time alignment with skeleton extractor: snippet boundaries must be identical
- Mean pooling [N_frames_in_window, 512] + max pooling [N_frames_in_window, 512] → concat → linear projection → [512]
- CLIP in eval() mode, torch.no_grad()
- Batch frames for throughput (aim for ~700 img/s on 4090)
- Save a snippet_timestamps.json alongside each npy for alignment verification

**Communicates with:** Feature Cache (writes), MIL Dataset Loader (its output is consumed)

### Component 3: Feature Cache

**Responsibility:** Organized on-disk storage of pre-extracted features. No code logic — purely a directory convention.

**Structure:**
```
features/
  ucf_skeleton/       # [N_snippets, 256] per video
  ucf_clip/           # [N_snippets, 512] per video
  xd_skeleton/
  xd_clip/
  ucf_c_clip/         # corruption variants: ucf_c_clip/<corruption_type>/<severity>/<video_id>.npy
  xd_skeleton/
  xd_clip/
  snippet_timestamps/ # JSON: {video_id: [snippet_start_frame, ...]} for alignment audit
```

**Key decisions:**
- Format: float32 npy (not HDF5 — simpler, sufficient for this scale)
- Naming: `<video_id>.npy` matching official split list filenames exactly
- No computed features in this directory (no aggregations, no fusion)
- Cache must be treated as immutable after extraction — training never writes back here

**Communicates with:** Skeleton Extractor (receives writes), CLIP Extractor (receives writes), Dataset Loader (provides reads)

### Component 4: Dataset Loader

**Responsibility:** PyTorch Dataset that loads a (skeleton_feat, clip_feat, label) triplet on demand, and pairs normal/anomalous bags for MIL training.

**Reads:** Feature Cache npy files + split list CSV/TXT files
**Returns:** Dict with keys `skel_feat [T, 256]`, `clip_feat [T, 512]`, `label [0 or 1]`, `video_id`
**MIL collation:** Custom collate_fn that forms (pos_bag, neg_bag) pairs from a batch — standard RTFM/MGFN convention

**Key design:**
- Train mode: randomly sample T=32 snippets from each video (standard MIL snippet sampling)
- Test mode: load all snippets in temporal order (no sampling)
- Validation mode: same as test mode but on val split
- Feature loading is the hot path — keep it as a simple np.load() call; avoid H5py overhead

**Communicates with:** Feature Cache (reads), MIL Trainer (provides batches)

### Component 5: Fusion Model

**Responsibility:** Take (skel_feat, clip_feat) per snippet and produce anomaly_score per snippet.

**Architecture (primary):** GatedFusion
```
F_skel [256] → Linear(256→256) → proj_skel [256]
F_clip [512] → Linear(512→256) → proj_clip [256]
gate = sigmoid(W_g @ [F_skel; F_clip] + b_g)          # [256]
F_fused = gate * proj_skel + (1-gate) * proj_clip      # [256]
F_fused → LayerNorm(256) → Dropout(0.3) → residual add
MLP head: Linear(256→128) → ReLU → Linear(128→1) → Sigmoid
```

**Architecture (baseline):** LateFusion — separate MIL heads per modality, score-level weighted average

**Architecture (advanced, if time permits):** CrossAttentionFusion — 8-head cross-attention, Q from skeleton, K/V from CLIP

**TTA surface:** LayerNorm affine parameters (gamma, beta) in GatedFusion and MLP head are the only parameters updated during TTA. All other parameters are frozen after Stage 2.

**Communicates with:** Dataset Loader (receives features), MIL Loss (provides scores), TTA Engine (exposes LN params)

### Component 6: MIL Training Engine

**Responsibility:** Standard weakly supervised MIL training loop.

**Reads:** Batches from Dataset Loader
**Writes:** checkpoint files, training logs, metrics CSV
**Loss:** MIL Ranking Loss — top-k snippets from anomalous bag scored higher than top-k from normal bag
**Validation:** Monitors val_loss (MIL Ranking Loss on val split) for early stopping
**Hyperparameter tracking:** Writes a config snapshot (JSON) alongside each checkpoint

**Key design:**
- AdamW optimizer, lr=1e-4, linear warmup 5 epochs + cosine decay
- Early stopping patience=10 on val_loss
- Fixed random seed stored in config for reproducibility
- Log metrics per epoch to CSV (not just tensorboard — must be readable without tooling)

**Communicates with:** Dataset Loader (consumes batches), Fusion Model (calls forward), Evaluation Engine (runs after training)

### Component 7: Evaluation Engine

**Responsibility:** Load test set features, run inference, compute frame-level AUC/AP against official annotations.

**Reads:** Saved checkpoint + test split features from Feature Cache + temporal annotations
**Writes:** Results JSON (per-video scores, overall AUC/AP, per-category breakdown)
**Strict rule:** Official test set ground truth is ONLY accessed here, never during training/validation

**Frame-level score construction:** Each snippet score is broadcast to all frames in that snippet's window (e.g., if snippet covers frames 0-63, all 64 frames get that snippet's score). This is the standard protocol used by RTFM/MGFN/VadCLIP.

**Communicates with:** Feature Cache (reads), Fusion Model (inference calls), Results Store (writes)

### Component 8: TTA Engine

**Responsibility:** Wrap a trained Fusion Model for per-video online adaptation during test time.

**Design (adapted from TENT pattern):**
```python
class TTAWrapper(nn.Module):
    def __init__(self, model, optimizer, method='tent'):
        # freeze all params, unfreeze only LN affine
        # method: 'tent' | 'sar' | 'source_only'
    
    def adapt_and_predict(self, skel_feats, clip_feats):
        # 1. reset LN params to source-trained state (per-video)
        # 2. process 32-snippet batches sequentially
        # 3. each batch: forward → compute entropy → update LN γ, β
        # 4. return snippet-level scores
```

**Reads:** Cached features for test video (no raw video access needed)
**Updates:** Only LN affine params (γ, β) — per-video, reset before each video
**Must NOT touch:** Backbone weights, projection matrices, gate weights

**Communicates with:** Fusion Model (wraps it), Feature Cache (reads features), Evaluation Engine (provides scores)

### Component 9: Corruption Generator

**Responsibility:** Apply ImageNet-C style corruptions to raw video frames and re-extract CLIP features.

**Corruption types:** Gaussian noise (5 severities), Motion blur (5), JPEG compression (5), Brightness shift (5)
**Output:** Feature Cache entries under `features/ucf_c_clip/<type>/<severity>/`
**Key design:** Corruption is applied frame-by-frame to RGB images before CLIP encoding; skeleton extraction may or may not need re-running (Gaussian noise and brightness affect RTMPose confidence but motion blur is the more impactful one — run a quick sensitivity check in Week 6)

**Communicates with:** Feature Cache (writes corrupted features), CLIP Extractor (re-uses its logic)

### Component 10: Experiment Harness

**Responsibility:** Orchestrate runs, manage configs, track results, ensure reproducibility.

**Not a framework — a set of conventions:**
- Each experiment has a config YAML in `configs/` specifying: dataset, fusion_type, seed, hyperparams
- Results written to `results/<experiment_name>/` with timestamp
- Shell scripts in `scripts/` for common workflows (train, eval, tta_eval, ablation sweeps)
- No Hydra/Lightning overhead — argparse + YAML load is sufficient for a thesis project

---

## Data Flow (Raw Videos to Anomaly Scores)

```
Step 1: Skeleton Extraction (once per dataset)
  Raw video → RTMPose → COCO-17 keypoints per frame
             → top-2 person selection
             → CTR-GCN (frozen, NTU120 HRNet2D weights) × 4 streams
             → weighted concat → [N_snippets, 256] npy

Step 2: CLIP Extraction (once per dataset, re-run for corruptions)
  Raw video → sample at 1 FPS
             → CLIP ViT-B/16 (frozen)
             → mean+max pooling per snippet window → projection → [N_snippets, 512] npy

Step 3: MIL Training (multiple runs for ablations)
  npy files → Dataset Loader → (pos_bag, neg_bag) pairs
             → GatedFusion forward → snippet anomaly scores
             → MIL Ranking Loss → AdamW update (fusion head only)
             → checkpoint.pth + config.json

Step 4: Evaluation (once per checkpoint)
  npy files → Fusion Model (loaded from checkpoint) → snippet scores
             → broadcast to frame-level → AUC/AP vs temporal annotations
             → results/experiment_name/metrics.json

Step 5: TTA Evaluation (per TTA method × corruption condition)
  npy files (clean or corrupted) → TTAWrapper
             → per-video: reset LN → 32-snippet batches → entropy minimize → predict
             → frame-level scores → AUC/AP
             → results/experiment_name/tta_metrics.json
```

---

## Suggested Directory Layout

This layout is derived from PEL4VAD (cleanest separation) combined with multi-dataset needs from VadCLIP, and scaled for solo-researcher debuggability.

```
ViolenceCC/
├── configs/                    # Experiment configurations
│   ├── base.yaml               # Shared defaults (seed, paths, epochs)
│   ├── ucf_gated.yaml          # UCF-Crime + GatedFusion (primary model)
│   ├── ucf_late.yaml           # UCF-Crime + LateFusion (ablation baseline)
│   ├── xd_gated.yaml           # XD-Violence + GatedFusion
│   ├── ucf_skeleton_only.yaml  # Skeleton-only baseline
│   ├── ucf_clip_only.yaml      # CLIP-only baseline
│   └── tta/
│       ├── tent_ucfc.yaml      # TENT-style on UCF-Crime-C
│       └── sar_ucfc.yaml       # SAR-style on UCF-Crime-C
│
├── data/                       # Split lists and annotation files (not features)
│   ├── ucf_crime/
│   │   ├── train.csv           # video_id, label (0=normal, 1=anomaly)
│   │   ├── val.csv             # 15% split from training set
│   │   ├── test.csv
│   │   └── temporal_annotations.json   # frame-level GT for test
│   └── xd_violence/
│       ├── train.csv
│       ├── val.csv
│       ├── test.csv
│       └── temporal_annotations.json
│
├── src/                        # All Python source code
│   ├── extract/                # Stage 1: Feature extraction
│   │   ├── skeleton_extractor.py   # RTMPose → CTR-GCN pipeline
│   │   ├── clip_extractor.py       # CLIP ViT-B/16 frame sampling + pooling
│   │   ├── corruption_generator.py # Apply corruptions, call clip_extractor
│   │   └── verify_alignment.py     # Sanity check: skeleton vs CLIP snippet counts match
│   │
│   ├── data/                   # Stage 2: Data loading
│   │   ├── dataset.py          # PyTorch Dataset; train/val/test modes
│   │   └── collate.py          # MIL bag-pair collate_fn
│   │
│   ├── models/                 # Stage 2: Model definitions
│   │   ├── fusion.py           # GatedFusion, LateFusion, CrossAttentionFusion
│   │   ├── mil_head.py         # MLP classifier head
│   │   └── backbones/          # Thin wrappers (frozen)
│   │       ├── ctrgcn_wrapper.py   # Load PYSKL CTR-GCN, expose feature extraction
│   │       └── clip_wrapper.py     # Load OpenCLIP ViT-B/16, expose visual encoder
│   │
│   ├── losses/
│   │   └── mil_loss.py         # MIL Ranking Loss (top-k variant)
│   │
│   ├── tta/                    # Stage 3: Test-time adaptation
│   │   ├── tta_wrapper.py      # TTAWrapper base class (per-video reset, LN param mgmt)
│   │   ├── tent_style.py       # Entropy minimization update rule for LN affine params
│   │   └── sar_style.py        # SAR sharpness-aware update rule for LN affine params
│   │
│   ├── eval/
│   │   ├── metrics.py          # frame_auc(), frame_ap(), per_category_breakdown()
│   │   └── visualize.py        # temporal score curves, skeleton overlay (qualitative)
│   │
│   └── utils/
│       ├── config.py           # YAML config loader, merge with CLI args
│       ├── logger.py           # CSV + console logging; no external services
│       ├── seed.py             # set_seed(seed) for torch/numpy/random
│       └── checkpoint.py       # save/load checkpoint with config snapshot
│
├── scripts/                    # Shell scripts for common workflows
│   ├── extract_ucf.sh          # Run skeleton + CLIP extraction on UCF-Crime
│   ├── extract_xd.sh           # Run CLIP extraction on XD-Violence (background)
│   ├── train.sh                # Train with a given config YAML
│   ├── eval.sh                 # Evaluate checkpoint on test set
│   ├── ablation_sweep.sh       # Loop over ablation configs
│   └── tta_eval.sh             # Run TTA evaluation on UCF-Crime-C
│
├── results/                    # All experiment outputs (gitignored except structure)
│   └── <experiment_name>/
│       ├── config_snapshot.json    # Exact config used
│       ├── train_log.csv           # epoch, train_loss, val_loss per row
│       ├── best_model.pth          # Best checkpoint by val_loss
│       ├── metrics.json            # Final test AUC/AP
│       └── tta_metrics.json        # TTA results if applicable
│
├── notebooks/                  # Analysis, visualization, debugging (not part of pipeline)
│   ├── feature_inspection.ipynb
│   ├── score_visualization.ipynb
│   └── ablation_tables.ipynb
│
├── tests/                      # Minimal unit tests for critical components
│   ├── test_mil_loss.py
│   ├── test_fusion_shapes.py   # Verify input/output dimensions
│   └── test_tta_reset.py       # Confirm per-video reset works correctly
│
├── .planning/                  # Research planning (not model code)
├── thesis_prd_v2.3.md
├── environment.yml             # Conda environment spec
└── README.md
```

---

## Build Order (Component Dependencies)

Dependencies flow strictly downward. Nothing in Stage 2 or Stage 3 needs Stage 1 to be running concurrently — features must be extracted first.

```
Tier 0 (Prerequisites — no code dependencies)
  └── environment.yml: conda env
  └── data/: split list files, temporal annotations

Tier 1 (Stage 1 — must complete before any training)
  ├── src/models/backbones/ctrgcn_wrapper.py
  │     depends on: PYSKL CTR-GCN weights downloaded
  ├── src/models/backbones/clip_wrapper.py
  │     depends on: OpenCLIP installed
  ├── src/extract/skeleton_extractor.py
  │     depends on: ctrgcn_wrapper, rtmlib installed, raw videos on E:\
  ├── src/extract/clip_extractor.py
  │     depends on: clip_wrapper, raw videos on E:\
  └── src/extract/verify_alignment.py
        depends on: skeleton_extractor + clip_extractor outputs

Tier 2 (Stage 2 core — requires Tier 1 outputs)
  ├── src/losses/mil_loss.py
  │     depends on: nothing (pure PyTorch)
  ├── src/models/mil_head.py
  │     depends on: nothing (pure PyTorch)
  ├── src/models/fusion.py
  │     depends on: mil_head.py
  ├── src/data/dataset.py
  │     depends on: Feature Cache (Tier 1 outputs) + data/ split files
  ├── src/data/collate.py
  │     depends on: dataset.py
  └── src/utils/{config, logger, seed, checkpoint}.py
        depends on: nothing (pure Python/PyTorch)

Tier 3 (Stage 2 training — requires Tier 2)
  └── train.py (top-level entry point)
        depends on: all of Tier 2, data/

Tier 4 (Evaluation — requires Tier 3)
  ├── src/eval/metrics.py
  │     depends on: nothing (pure Python)
  └── eval.py (top-level entry point)
        depends on: metrics.py, dataset.py (test mode), saved checkpoint

Tier 5 (TTA — requires Tier 4 passing)
  ├── src/extract/corruption_generator.py
  │     depends on: clip_extractor.py (Tier 1)
  ├── src/tta/tta_wrapper.py
  │     depends on: fusion.py
  ├── src/tta/tent_style.py
  │     depends on: tta_wrapper.py
  ├── src/tta/sar_style.py
  │     depends on: tta_wrapper.py
  └── tta_eval.py (top-level entry point)
        depends on: all TTA components + corrupted features in cache

Tier 6 (Analysis — requires Tier 4-5 results)
  └── src/eval/visualize.py + notebooks/
```

**Implication for phase structure:** The roadmap should map to these tiers. Phase 1 = Tier 0-1 (env + extraction). Phase 2 = Tier 2-3 (baselines + training). Phase 3 = Tier 3 iteration (fusion variants, ablations). Phase 4 = Tier 5 (TTA). Phase 5 = Tier 6 (analysis, write-up support).

---

## Patterns to Follow

### Pattern 1: Pre-Extracted Feature Pipeline (universal in RTFM/MGFN/VadCLIP/PEL4VAD)

**What:** All backbone inference happens in a separate extraction phase. Training only reads npy files.
**Why:** Enables fast experiment iteration (minutes not hours per training run on feature-level data). VRAM constraint makes end-to-end training impossible anyway.
**Implementation note:** The extraction scripts are single-run utilities, not part of the training loop. Keep them in `src/extract/` and document their exact CLI usage in `scripts/`.

### Pattern 2: Snippet-Bag MIL Loader (from RTFM)

**What:** During training, load a fixed number of snippets (T=32) from each video, pair anomalous and normal bags for MIL ranking loss.
**Why:** The original Sultani 2018 MIL convention; all comparison baselines use this. Using a different snippet count breaks comparability.
**Implementation note:** T=32 is the RTFM default and is widely used. Test mode loads all snippets in order.

### Pattern 3: Per-Dataset Option Files (from VadCLIP)

**What:** Separate config files for UCF-Crime vs XD-Violence (different feature paths, annotation paths, evaluation metrics).
**Why:** The two datasets have different primary metrics (AUC vs AP), different feature dimensions if using I3D baselines, and different test set sizes.
**Implementation note:** Use YAML inheritance — `xd_gated.yaml` extends `base.yaml` and overrides only what changes.

### Pattern 4: Modular Loss Files (from PEL4VAD)

**What:** Keep loss functions in their own module, not embedded in train.py.
**Why:** Ablations sometimes involve swapping loss variants. A separate `losses/mil_loss.py` makes this transparent.

### Pattern 5: Config Snapshot with Checkpoint (thesis requirement)

**What:** When saving a model checkpoint, also save the exact config dict as a JSON file in the same directory.
**Why:** For a thesis, every number in a table must be reproducible. The config snapshot ensures you always know what hyperparameters produced each checkpoint. This is not done in RTFM/MGFN but is essential for scientific reproducibility.

### Pattern 6: LN-Only TTA Wrapper (adapted from TENT)

**What:** The TTAWrapper freezes all model params then unfreezes only LayerNorm gamma and beta. Per-video reset is mandatory.
**Why:** TTA without per-video reset causes error accumulation across test videos (a known failure mode documented in TENT/SAR literature). The per-video reset is the key difference from standard TENT usage in classification.
**Implementation note:** `tta_wrapper.py` stores `source_ln_params` at init time and restores them before each video. This must be unit-tested.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Feature Re-Extraction Inside Training Loop

**What:** Calling CTR-GCN or CLIP forward inside the training DataLoader.
**Why bad:** Burns VRAM on frozen backbones, massively slows training (hours vs minutes), prevents fast ablation iteration.
**Instead:** Always pre-extract and cache to disk. Training reads only npy files.

### Anti-Pattern 2: Test Set AUC in Model Selection

**What:** Monitoring frame-level AUC on the official test set for early stopping or hyperparameter selection.
**Why bad:** Test set contains frame-level labels; using it for any selection constitutes data leakage and invalidates results.
**Instead:** Use MIL Ranking Loss on the internal val split (15% from training set, video-level labels only) for all model selection decisions.

### Anti-Pattern 3: Per-Dataset Training Scripts Without Shared Core

**What:** VadCLIP pattern of ucf_train.py and xd_train.py as largely duplicated scripts.
**Why bad:** Bug fixes must be applied twice; divergence accumulates.
**Instead:** Single `train.py` entry point that reads dataset-specific config. Dataset differences handled in config YAML, not in separate script files.

### Anti-Pattern 4: Snippet Count Mismatch Between Modalities

**What:** Skeleton extraction producing a different number of snippets than CLIP extraction for the same video.
**Why bad:** Feature alignment breaks silently; the model learns from misaligned signals.
**Instead:** Both extractors use the same snippet boundary definition (frame range per snippet). `verify_alignment.py` should assert N_skel_snippets == N_clip_snippets for every video before training starts.

### Anti-Pattern 5: TTA Without Per-Video Reset

**What:** Accumulating LN affine parameter updates across multiple test videos.
**Why bad:** Each video is an independent inference context. Accumulated error from previous videos degrades performance and makes results non-reproducible if test order changes.
**Instead:** `tta_wrapper.py` resets to source-trained state at the start of each video. Document and test this explicitly.

### Anti-Pattern 6: Flat Features Namespace

**What:** Dumping all extracted features into a single directory.
**Why bad:** UCF-Crime corruption experiments require 20 variants (4 types × 5 severities) of features. Flat storage becomes unmanageable.
**Instead:** Structured `features/<dataset>_<modality>/<video_id>.npy` for clean features, `features/<dataset>_c_<modality>/<type>/<severity>/<video_id>.npy` for corrupted.

---

## PRD Stage Pipeline Compatibility

The PRD v2.3 specifies a 3-stage pipeline. All architecture decisions above are compatible:

| PRD Stage | Architecture Components | Notes |
|-----------|------------------------|-------|
| Stage 1: Feature Pre-Extraction (all backbones frozen) | Skeleton Extractor + CLIP Extractor + Feature Cache + Corruption Generator | CTR-GCN and CLIP in eval() + no_grad(). 4-stream CTR-GCN weighted concat. CLIP mean+max pooling. Outputs: [N_snippets, 256] and [N_snippets, 512] npy files. |
| Stage 2: Fusion Module MIL Training | Dataset Loader + Fusion Model + MIL Training Engine + Evaluation Engine | Only GatedFusion (or LateFusion/CrossAttention) + MLP head parameters are trained. AdamW, early stopping on val_loss. Frame-level AUC/AP reported on official test set. |
| Stage 3: Test-Time Adaptation | TTA Engine (TENT-style / SAR-style) | Only LN affine params updated. Per-video reset. 32-snippet batches. Operates on cached features — no backbone re-run needed. |

The 3-stage separation also maps cleanly to GPU usage: Stage 1 is GPU-intensive (backbone inference), Stage 2 is lightweight (feature-level training, minutes per run), Stage 3 adds minimal overhead to test inference.

---

## Scalability Considerations

This is a research project, not a production system. Scalability analysis is relevant only for ensuring the design doesn't create engineering bottlenecks.

| Concern | At current scale (UCF 1900 + XD 4754 videos) | If extended |
|---------|----------------------------------------------|-------------|
| Feature storage | ~15 GB skeleton + ~10 GB CLIP = ~25 GB per dataset. Fits on E:\ with room to spare | Add E:\ capacity or use compression |
| Training speed | With pre-extracted npy: <5 min per epoch on 4090. 50 epochs = ~4 hours total | Not a concern for thesis |
| TTA overhead | Per-video: ~32 forward passes × 1 update. Adds ~10-20% to test-time. Acceptable. | Not a concern for thesis |
| Corruption variants | 20 × CLIP extraction runs for UCF-Crime-C. ~2-3h total (pre-computed, cached). | Already planned |
| Memory in training | Batch of 32 snippets × 768-d features = negligible. Well within 24GB VRAM. | Not a concern |

---

## Sources

- RTFM codebase structure: https://github.com/tianyu0207/RTFM (verified 2026-03-31)
- MGFN codebase structure: https://github.com/carolchenyx/MGFN. (verified 2026-03-31)
- VadCLIP codebase structure: https://github.com/nwpu-zxr/VadCLIP (verified 2026-03-31)
- PEL4VAD codebase structure: https://github.com/yujiangpu20/PEL4VAD (verified 2026-03-31)
- TENT adaptation pattern: https://github.com/DequanWang/tent (verified 2026-03-31)
- PRD v2.3: D:\ViolenceCC\thesis_prd_v2.3.md (authoritative specification, all architecture decisions cross-referenced)
- PYSKL CTR-GCN model zoo: https://github.com/kennymckormick/pyskl/blob/main/configs/ctrgcn/README.md
- rtmlib (RTMPose without mmcv): https://github.com/Tau-J/rtmlib
