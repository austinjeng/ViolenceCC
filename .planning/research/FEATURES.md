# Feature Landscape

**Domain:** Weakly Supervised Violence-Oriented Video Anomaly Detection (VAD) — Master's Thesis Research Codebase
**Researched:** 2026-03-31
**Project:** ViolenceCC — Dual-modal (CTR-GCN skeleton + CLIP) fusion with MIL Ranking Loss + TENT/SAR-style TTA on LN-based fusion heads

---

## Framing Note

Research codebases for weakly supervised VAD have a consistent anatomy: (1) feature pre-extraction scripts that produce cached .npy/.pkl files, (2) a Dataset class that loads those cached features, (3) a training loop with MIL Ranking Loss, (4) an evaluation script that computes frame-level AUC/AP against ground-truth temporal annotations, and (5) a handful of qualitative visualizations. Every public reference codebase surveyed (RTFM, VadCLIP, PEL4VAD, CMSIL) follows this exact pattern. Deviating from it adds friction without adding research value.

The table-stakes/differentiator distinction below is calibrated to one question: **"Can a thesis committee member or a follow-up researcher reproduce every number in the thesis from the code alone?"** That is the reproducibility bar. Everything beyond it is either differentiating upside or a time sink to avoid.

---

## Table Stakes

Features a thesis examiner expects to find. Absent any of these, the codebase is not defensible as a complete research artifact.

### Data and Feature Infrastructure

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Skeleton extraction script (rtmlib + RTMPose-m) | Thesis pipeline starts here; no pre-extracted skeletons exist for UCF-Crime or XD-Violence | Medium | Batch-processes videos to PYSKL pickle format; must handle missing-person frames gracefully. One-time offline run, not called at training time. |
| CLIP ViT-B/16 feature extraction script | Second modality of core pipeline; no official pre-extracted CLIP features for UCF-Crime | Low-Medium | Extracts per-frame 512-d vectors at 1 FPS, stores mean+max pooled snippet vectors. One-time offline run. |
| Snippet-level feature cache on disk | Standard in every reference codebase (RTFM, VadCLIP, PEL4VAD); enables fast iteration over fusion strategies | Low | Store as .npy or .pkl per video or as a single HDF5. Must be indexed by video ID so Dataset can load both modalities time-aligned. |
| Dataset class with bag-level MIL batching | MIL Ranking Loss requires paired normal/abnormal bags at batch construction time | Low-Medium | Sample K snippets per video (standard: 32 snippets/video in RTFM). Must return video-level label alongside snippet features. |
| Official train/val/test split files | Reproducing exact AUC/AP numbers requires the same splits as published baselines | Low | UCF-Crime: `Anomaly_Train.txt`, `Anomaly_Test.txt`, `Temporal_Anomaly_Annotation.txt`. XD-Violence: official annotation file. Must be committed to repo. |
| Fixed 15% internal validation split (seeded) | Early stopping without test-set leakage; required for correct model selection | Low | One-time seeded split from training set, stored as a text file. ALL experiments use the same split. |

**Dependencies:** Skeleton cache must exist before any training. CLIP cache is independent but also pre-extraction. Both caches must be time-aligned at snippet level before Dataset class is used.

---

### Model Architecture

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Frozen CTR-GCN feature extractor (NTU120 HRNet 2D) | Core skeleton branch; backbone confirmed downloadable; thesis claims COCO-17 compatibility | Medium | Load checkpoint, strip classifier head, set `requires_grad=False` globally. Output: 256-d per snippet. Must verify forward pass on COCO-17 input before any downstream work. |
| CLIP visual encoder wrapper (frozen ViT-B/16) | Core visual-language branch | Low | Thin wrapper around OpenCLIP; extract [CLS] token; FP16 inference. |
| Gated Fusion module | Primary fusion model for thesis contribution (Sigmoid gating, 256-d shared space, LayerNorm + Dropout 0.3) | Low-Medium | Described fully in PRD §9.2. ~50 lines of PyTorch. LayerNorm layers must be named/addressable for TTA parameter collection. |
| Late Fusion baseline (score-level weighted average) | Required ablation; demonstrates Gated Fusion adds value | Low | Trivial to implement. Run before Gated Fusion to validate pipeline end-to-end. |
| Single-modal MIL heads (Skeleton-Only, CLIP-Only) | Required ablation baselines in thesis Table 1 | Low | Same MIL head, single-modal input. |
| MIL Ranking Loss | Standard loss for weakly supervised VAD (RTFM, MGFN, VadCLIP all use it) | Low | Well-documented; max-k snippet selection within each bag, hinge margin loss between top-k anomaly and top-k normal snippets. |

---

### Training Infrastructure

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Fixed random seed everywhere | Reproducibility requirement; thesis numbers must be reproducible | Low | `torch.manual_seed`, `numpy.random.seed`, `random.seed`, `torch.backends.cudnn.deterministic=True`. Set once in main entry point. |
| AdamW optimizer + linear warmup + cosine decay | Specified in PRD §11.1; standard for transformer-adjacent fusion heads | Low | ~10 lines. |
| Early stopping on validation MIL loss (patience=10) | Prevents test-set leakage; required for clean model selection | Low | Monitor `val_loss` each epoch, save `best_model.pth` when it improves, stop after 10 non-improving epochs. |
| Checkpoint saving/loading | Resume interrupted training; load best model for evaluation | Low | Save `{epoch}_{val_loss:.4f}.pth` + `best_model.pth`. |
| Per-epoch logging to file (loss, val_loss) | Thesis-level accountability: committee may ask to see training curves | Low | Write CSV with epoch, train_loss, val_loss. Also print to stdout. No heavyweight MLOps required. |
| Config file (YAML or argparse) for all hyperparameters | Ensures every experiment is fully specified and reproducible from a single config | Low | Argparse is sufficient for a solo researcher. Every hyperparameter must be an argument with a documented default. |

---

### Evaluation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Frame-level AUC (ROC) on UCF-Crime test set | Primary metric for UCF-Crime; must match published baselines within ±1% to validate pipeline | Low | Sklearn `roc_auc_score` on per-frame anomaly scores vs ground-truth binary labels. Snippet scores are interpolated to frame level (repeat score across snippet duration). |
| Frame-level AP on XD-Violence test set | Primary metric for XD-Violence | Low | Sklearn `average_precision_score`. |
| RTFM baseline reproduction on UCF-Crime (target: 84.30 ±1% AUC) | Mandatory sanity check before running any novel experiments | Low | Run existing RTFM code with I3D features. If this fails, the evaluation protocol is broken. |
| Ablation result table (all 8 required ablations) | Core thesis evidence; committee will examine this table in detail | Medium | Covers: Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion, CLIP pooling (mean vs mean+max), multi-person aggregation (concat/max/mean), Corruption TTA (No-Adapt/TENT-style/SAR-style), per-corruption TTA breakdown |
| Mean ± std over 3 runs for key results | Statistical credibility; required for honest reporting at thesis level | Low | Run final model 3× with different seeds, report mean ± std in main results table. |

---

### TTA Infrastructure

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| UCF-Crime-C corruption generator | Required for TTA experiments (4 types × 5 severities = 20 conditions) | Low-Medium | Apply Gaussian noise, motion blur, JPEG compression, brightness shift to raw video frames before CLIP re-extraction. Can be offline script. |
| CLIP re-extraction on corrupted frames | Corruption changes CLIP inputs; skeleton extraction may also need re-run for severe corruptions | Low | Same extraction script, different input folder. |
| TENT-style adaptation module (LN affine parameters only) | Core TTA baseline; adapts γ,β of all LayerNorm layers in fusion head | Low-Medium | Adapt TENT's `configure_model()` and `collect_params()` pattern: freeze all params except LN affine, minimize batch entropy. Per-video reset protocol from PRD §10.3. |
| SAR-style adaptation module (LN + sharpness regularization) | Primary TTA method; main TTA contribution of thesis | Medium | Add SAM optimizer wrapper on top of TENT-style entropy minimization. Complexity is in SAM step (two forward passes). |
| TTA evaluation loop (Source-Only vs TENT-style vs SAR-style across 20 conditions) | Required comparison table in thesis TTA chapter | Low-Medium | Loop over 20 corruption conditions × 3 methods × test videos. Log per-condition AUC per method. |

---

### Qualitative Analysis

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Anomaly score temporal curve plots | Standard in every VAD paper (RTFM Fig. 5, MGFN Fig. 6, VadCLIP Fig. 4); committee expects them | Low | Matplotlib: x=frame index, y=anomaly score [0,1], shaded GT anomaly intervals. ~20 lines. Pick 2-3 representative UCF-Crime + XD-Violence videos (one correct, one failure case). |
| Skeleton overlay visualization | Confirms pose extraction quality on violence scenes; required for thesis to demonstrate the skeleton branch actually works | Low-Medium | Draw COCO-17 keypoints + skeleton edges on video frames. OpenCV or matplotlib. Used for quality audit during development, and 1-2 thesis figures. |

---

## Differentiators

Features that go beyond minimum reproducibility and make the thesis stronger or the contribution more distinctive. Build these only after all table stakes are passing.

### Research-Level Differentiators

| Feature | Value Proposition | Complexity | Prerequisite |
|---------|-------------------|------------|-------------|
| Per-category violence subset AUC/AP breakdown (Fighting+Assault on UCF-Crime; Fighting+Abuse+Riot on XD-Violence) | Directly answers RQ1 ("does skeleton+VLM specifically help violence categories?"); distinguishes thesis from generic VAD papers | Low | Evaluation script complete. Subset video IDs are available from dataset annotation files. |
| CLIP text prompt engineering (20-30 LLM-generated violence/normal descriptions as semantic priors) | Thesis claims CLIP semantic branch captures scene context; demonstrating deliberate prompt design strengthens the argument | Low | CLIP encoder available. Prompts generated offline, stored as text file, embedded once. |
| Corruption-severity heatmap (AUC per corruption type × severity level, 4×5 grid) | Reveals which corruptions degrade performance most; strong visualization for TTA chapter | Low | TTA loop complete. Reshape results array and use seaborn heatmap. ~10 lines. |
| t-SNE / UMAP visualization of fused features (normal vs abnormal snippets) | Shows learned embedding space; powerful intuitive evidence that fusion head separates anomalies | Medium | Need ~10K cached features from test set. Compute t-SNE, color by label. One thesis figure. |
| Gating weight distribution analysis (histogram of sigmoid gate values across test set) | Uniquely validates the Gated Fusion claim: "skeleton branch activates more for violent scenes, CLIP branch for scene-context anomalies" | Low | Forward pass on test set, collect gate scalars. Histogram with seaborn. |
| Cross-Attention Fusion module (optional, 8-head, 512-d) | Higher-complexity fusion; if results are better than Gated Fusion, strengthens contribution; if not, the comparison is informative | High | Gated Fusion must be stable first. Engineering risk is 3-5 days of debugging. Only if Week 5 ahead of schedule. |
| RWF-2000 supplementary validation (skeleton-only binary classification accuracy) | Demonstrates skeleton branch generalizes to a second violence dataset | Medium | RWF-2000 access (currently uncertain). Adds a row to supplementary table, not main results. |
| CLIP sampling rate ablation (1 FPS vs 2 FPS vs 4 FPS) | Tests sensitivity of CLIP pooling granularity; 1-page ablation section content | Low | Feature extraction already done at 1 FPS; re-run at 2 and 4 FPS. ~2-3 GPU hours. |
| CTR-GCN frozen vs proxy-label fine-tuned ablation | Quantifies benefit of backbone fine-tuning; "Table 5" level content | High | Requires proxy label scheme, partial backbone unfreeze, re-extraction. ~10 GPU hours. Only if Week 7 has slack. |
| Cross-dataset TTA (UCF->XD, XD->UCF) | Extends TTA chapter to real distribution shift (not synthetic corruption) | High | Corruption TTA must be complete. Raises methodological questions about anomaly stream adaptation. Only if Week 8 has slack. |
| EATA-style adaptation (selective update + Fisher regularization) | Adds third TTA comparison point; completes the TENT/SAR/EATA triad | Medium | SAR must be working. Additional ~5 GPU hours for Fisher diagonal estimation. |

---

### Infrastructure Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Weights & Biases (W&B) experiment tracking | Auto-logs all hyperparameters, metrics, and system resources; generates shareable run comparison dashboards | Low | 5 lines to add after basic logging is working. Recommended if committee wants to see hyperparameter search evidence. |
| Hydra or YAML config system | Enables multi-run sweeps from config files; cleaner than argparse for 20+ hyperparameters | Medium | Overkill for a solo researcher with argparse already working. Add only if argparse configs become unmaintainable. |
| Automatic result CSV aggregation script | Collects all experiment CSV logs into one comparison table | Low | ~30 lines. Useful for building thesis tables without manual copy-paste. |

---

## Anti-Features

Things to deliberately NOT build in this research codebase. Building any of these is a time sink that does not contribute to the thesis and cannot be completed in 12 weeks by a solo researcher.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| End-to-end backbone training / gradient through CTR-GCN or CLIP | Exceeds VRAM budget (24GB); eliminates the clean 3-stage methodology; adds a training-stage justification problem for MIL signal | Keep all backbones frozen. The PRD has already resolved this correctly. |
| Real-time inference optimization (TensorRT, ONNX export, quantization) | This is a research codebase, not a deployment artifact. Committee does not evaluate inference speed | Report FLOPs and per-video wall-clock time instead (a single Python `time.time()` call). |
| Web UI or dashboard for anomaly visualization | Zero thesis value; builds a product, not research | Use Matplotlib static figures. |
| Docker/containerization of the full pipeline | Adds maintenance burden; not expected for master's thesis code submission | Provide `requirements.txt` + conda `environment.yml` with pinned versions. |
| Unit tests for ML model internals | ML models defy unit testing at the unit level; shape-check tests only add maintenance overhead without catching real bugs | Use `assert tensor.shape == expected_shape` inline during development, remove before submission. |
| Custom evaluation metrics beyond frame-level AUC/AP | Diverges from published baselines; makes comparisons invalid | Use sklearn directly. Report only standard metrics (AUC, AP, optionally F1 at fixed threshold). |
| Multi-GPU training / DDP | Single RTX 4090 is sufficient; distributed training adds debugging complexity without benefit | Single-GPU PyTorch. Batch size 32 on cached features requires <1GB VRAM. |
| Streaming / online feature extraction during training | Defeats the purpose of the 3-stage pre-extraction + cache design; reduces iteration speed dramatically | Pre-extract all features to disk before any training run. |
| Two-Person Interaction Graph (34-node inter-body edges) | High engineering risk; CTR-GCN graph topology must be rebuilt; weeks of debug; marginal expected gain over top-2 aggregation | Use top-2 person feature aggregation (concat/max/mean) as the multi-person ablation instead. |
| Three-modal fusion (+ YOLO-World object branch) as primary model | Adds a third modality before dual-modal baseline is stable; high engineering risk in a 12-week timeline | Defer entirely to Week 7+ conditional on main results already meeting AUC ≥ 83%. |
| Experiment database (SQLite, MLflow tracking server) | Infrastructure cost >> benefit for one researcher running <50 total experiments | Write experiment results to CSV files. One CSV per experiment group. |
| Automated hyperparameter search (Optuna, Ray Tune) | Premature optimization; hyperparameter space is small and well-constrained by PRD defaults | Manual grid search over the 4-point learning rate grid specified in PRD §10.3. Log each run to CSV. |

---

## Feature Dependencies

Key dependency chains that constrain implementation order:

```
Skeleton extraction (rtmlib+RTMPose) 
  → PYSKL pickle format output
    → CTR-GCN frozen forward pass (feature extraction)
      → Skeleton feature cache (.npy per video)

CLIP ViT-B/16 forward pass (frozen)
  → CLIP feature extraction at 1 FPS + mean+max pooling
    → CLIP feature cache (.npy per video)

Skeleton cache + CLIP cache (time-aligned)
  → Dataset class (bag MIL batching)
    → Training loop (AdamW + MIL Ranking Loss + early stopping)
      → best_model.pth

best_model.pth
  → Evaluation on UCF-Crime test set (frame-level AUC)
  → Evaluation on XD-Violence test set (frame-level AP)
  → Ablation variants (swap fusion module, re-train, re-evaluate)

UCF-Crime-C generator (corruption script)
  → Re-extract CLIP features on corrupted frames
    → TTA evaluation loop (Source-Only / TENT-style / SAR-style)
      → Per-condition AUC table

RTFM baseline reproduction
  → Validates evaluation protocol before novel experiments (must pass first)
```

**Critical path:** Skeleton extraction → CLIP extraction → Dataset → Training → Evaluation. RTFM reproduction must happen concurrently with or before the first novel training run to validate the evaluation harness.

---

## MVP Recommendation

Prioritize for first working end-to-end pass (Weeks 1-4):

1. Environment setup + CTR-GCN forward pass verification (30 min, Week 1)
2. RTFM reproduction on UCF-Crime with I3D features (validates evaluation protocol before anything else)
3. Skeleton extraction for UCF-Crime; CLIP extraction for UCF-Crime
4. Dataset class + MIL Ranking Loss training loop
5. Skeleton-Only and CLIP-Only single-modal baselines
6. Late Fusion (2 hours — validates fusion pipeline before building Gated Fusion)
7. Gated Fusion module + ablation table

Defer until Weeks 5-6:
- TTA infrastructure (UCF-Crime-C generator, TENT-style, SAR-style)
- XD-Violence evaluation (blocked on XD skeleton extraction which runs in background)
- Any differentiator features

Defer until Weeks 7-10 (conditional on main results passing AUC ≥ 83%):
- Per-category breakdown, t-SNE, gating weight analysis, cross-dataset TTA, YOLO-World

---

## Sources

- RTFM codebase structure: [github.com/tianyu0207/RTFM](https://github.com/tianyu0207/RTFM) (ICCV 2021)
- VadCLIP codebase structure: [github.com/nwpu-zxr/VadCLIP](https://github.com/nwpu-zxr/VadCLIP) (AAAI 2024)
- PEL4VAD codebase structure: [github.com/yujiangpu20/PEL4VAD](https://github.com/yujiangpu20/PEL4VAD) (IEEE-TIP)
- CMSIL codebase structure: [github.com/casperZB/CMSIL](https://github.com/casperZB/CMSIL) (ICME 2024)
- SAR codebase structure: [github.com/mr-eggplant/SAR](https://github.com/mr-eggplant/SAR) (ICLR 2023)
- rtmlib documentation: [github.com/Tau-J/rtmlib](https://github.com/Tau-J/rtmlib)
- ImageNet-C corruption benchmark pattern: [arxiv.org/abs/1903.12261](https://arxiv.org/abs/1903.12261) (Hendrycks & Dietterich, ICLR 2019)
- PRD v2.3 specification: `thesis_prd_v2.3.md` (authoritative project spec)
- PROJECT.md: `.planning/PROJECT.md`
