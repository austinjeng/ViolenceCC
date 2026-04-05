# Requirements: ViolenceCC

**Defined:** 2026-03-31
**Core Value:** A working dual-modal (Skeleton + CLIP) fusion pipeline that produces reproducible frame-level AUC/AP numbers on UCF-Crime and XD-Violence, with complete ablation analysis and TTA experiments.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Environment

- [x] **ENV-01**: Three conda environments created and verified — `vcc-skeleton` (rtmlib 0.0.15 + onnxruntime-gpu), `vcc-ctrgcn` (PyTorch 1.12.1 + PYSKL + mmcv-full 1.7.0), `vcc-main` (PyTorch 2.6.0 + open-clip-torch 3.3.0)
- [x] **ENV-02**: CTR-GCN NTU120 HRNet 2D pretrained weights (j/b/jm/bm) downloaded and forward pass verified with COCO-17 input (17 joints x 3 channels x 64 frames x 2 persons -> 256-d output)
- [x] **ENV-03**: Project directory structure established following research-recommended layout (configs/, data/, src/, scripts/, results/, notebooks/)

### Data Pipeline

- [x] **DATA-01**: Official split files committed to repo — UCF-Crime (Anomaly_Train.txt, Anomaly_Test.txt, Temporal_Anomaly_Annotation.txt), XD-Violence annotation file
- [x] **DATA-02**: Fixed 15% stratified validation split created from training set (seeded, stored as text file, maintains normal/abnormal ratio)
- [x] **DATA-03**: Skeleton extraction script using rtmlib RTMPose-m that outputs PYSKL-compatible pickle format (COCO-17, top-2 persons per frame, confidence scores)
- [x] **DATA-04**: Skeleton coordinate normalization verified — raw RTMPose pixel coords pass through PreNormalize2D before CTR-GCN forward pass
- [x] **DATA-05**: CTR-GCN frozen feature extraction producing 256-d per snippet with 4-stream weighted concat (j:b:jm:bm = 1.0:1.0:0.5:0.5)
- [x] **DATA-06**: CLIP ViT-B/16 feature extraction at 1 FPS with mean+max pooling producing 1024-d per snippet (pre-projection; Phase 3 applies learned Linear(1024->512))
- [x] **DATA-07**: Feature cache stored as float32 .npy per video, indexed by video ID, for both modalities
- [x] **DATA-08**: Temporal alignment verification script confirming N_skel_snippets == N_clip_snippets for every video across both datasets
- [x] **DATA-09**: UCF-Crime skeleton + CLIP features fully extracted and cached
- [x] **DATA-10**: XD-Violence skeleton + CLIP features fully extracted and cached

### Model

- [ ] **MOD-01**: MIL Ranking Loss implementation (top-k snippet selection within each bag, hinge margin between top-k anomaly and top-k normal)
- [ ] **MOD-02**: Dataset class with bag-level MIL batching (T=32 snippets per video, paired normal/abnormal bags per batch)
- [ ] **MOD-03**: Skeleton-Only MIL head baseline (256-d input -> anomaly score)
- [ ] **MOD-04**: CLIP-Only MIL head baseline (512-d input -> anomaly score)
- [ ] **MOD-05**: Late Fusion baseline (score-level weighted average of single-modal outputs)
- [ ] **MOD-06**: Gated Fusion module — sigmoid gating in 256-d shared space with LayerNorm + Dropout(0.3) + residual connection, producing frame-level anomaly scores
- [ ] **MOD-07**: LayerNorm layers in fusion head are named and addressable for TTA parameter collection

### Training

- [ ] **TRN-01**: Training loop with AdamW optimizer, linear warmup (5 epochs) + cosine decay, lr=1e-4, batch_size=32, max_epochs=50
- [ ] **TRN-02**: Early stopping on validation MIL loss (patience=10), saving best_model.pth
- [ ] **TRN-03**: Fixed random seed everywhere (torch, numpy, random, cudnn.deterministic)
- [ ] **TRN-04**: Per-epoch logging to CSV (epoch, train_loss, val_loss) and stdout
- [ ] **TRN-05**: Config snapshot saved alongside every checkpoint for full reproducibility
- [ ] **TRN-06**: Single train.py entry point configurable via YAML/argparse for all experiments (not per-dataset scripts)

### Evaluation

- [ ] **EVAL-01**: RTFM baseline reproduction on UCF-Crime using I3D features — target 84.30% AUC within ±1%
- [ ] **EVAL-02**: Frame-level AUC (ROC) evaluation on UCF-Crime official test set with correct snippet-to-frame score expansion
- [ ] **EVAL-03**: Frame-level AP evaluation on XD-Violence official test set
- [ ] **EVAL-04**: Per-category violence subset breakdown (UCF-Crime: Fighting+Assault, XD-Violence: Fighting+Abuse+Riot)
- [ ] **EVAL-05**: Key results (Gated Fusion on both datasets) repeated 3 times with mean +/- std

### TTA

- [ ] **TTA-01**: UCF-Crime-C corruption generator (Gaussian noise, motion blur, JPEG compression, brightness shift — 4 types x 5 severities = 20 conditions)
- [ ] **TTA-02**: CLIP feature re-extraction on corrupted frames for all 20 conditions
- [ ] **TTA-03**: Skeleton re-extraction decision per corruption type (motion blur and JPEG require re-extraction; noise and brightness do not)
- [ ] **TTA-04**: TENT-style adaptation module — entropy minimization updating only LN affine parameters (gamma, beta) with per-video reset to source-trained state
- [ ] **TTA-05**: SAR-style adaptation module — TENT-style + sharpness-aware regularization with per-video reset
- [ ] **TTA-06**: TTA evaluation loop — Source-Only vs TENT-style vs SAR-style across all 20 corruption conditions, reporting per-condition frame-level AUC
- [ ] **TTA-07**: Adaptation protocol enforced: 32-snippet batches, per-video reset, unified LR grid search {1e-4, 5e-4, 1e-3, 5e-3}

### Visualization

- [ ] **VIS-01**: Anomaly score temporal curve plots (matplotlib: x=frame, y=score, shaded GT intervals) for 2-3 representative videos per dataset
- [ ] **VIS-02**: Skeleton overlay visualization on video frames (COCO-17 keypoints + edges) for quality validation and thesis figures

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Optional Enhancements

- **OPT-01**: YOLO-World-M object detection branch with engineering features (dangerous object ratio, max confidence, spatial proximity) as third modality late fusion
- **OPT-02**: Cross-Attention Fusion module (8-head, 512-d shared space, query from skeleton, key/value from CLIP)
- **OPT-03**: Cross-dataset TTA (UCF-Crime -> XD-Violence and reverse)
- **OPT-04**: Two-Person Interaction Graph (34-node merged skeleton with inter-body edges)
- **OPT-05**: EATA-style TTA (selective update + Fisher regularization)
- **OPT-06**: CTR-GCN fine-tune ablation (proxy labels from video-level weak labels)
- **OPT-07**: CLIP sampling rate ablation (1 FPS vs 2 FPS vs 4 FPS)
- **OPT-08**: RWF-2000 supplementary validation (trimmed binary classification)
- **OPT-09**: t-SNE / UMAP visualization of fused feature space
- **OPT-10**: Gating weight distribution analysis (sigmoid gate histograms by category)
- **OPT-11**: Corruption severity heatmap (4x5 grid, seaborn)
- **OPT-12**: CLIP text prompt engineering (20-30 LLM-generated violence/normal descriptions)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| End-to-end backbone training | Exceeds 24GB VRAM budget; eliminates 3-stage methodology cleanliness |
| Real-time inference / TensorRT / quantization | Not a deployment artifact; thesis is research-focused |
| Web UI / demo app | No deployment target; all evaluation is offline |
| Docker containerization | Solo researcher; conda environments are sufficient |
| Unit tests for ML internals | Research codebase; integration validation via RTFM reproduction is the gate |
| Custom evaluation metrics | Frame-level AUC/AP are community standard; custom metrics reduce comparability |
| Multi-GPU training | Single RTX 4090; feature-cached MIL training doesn't need multi-GPU |
| Streaming / real-time video extraction | All extraction is offline batch processing |
| Thesis LaTeX writing | Tracked separately, not in this codebase project |
| Professor meeting scheduling | Not a code deliverable |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01 | Phase 1 | Complete |
| ENV-02 | Phase 1 | Complete |
| ENV-03 | Phase 1 | Complete |
| DATA-01 | Phase 2 | Complete |
| DATA-02 | Phase 2 | Complete |
| DATA-03 | Phase 2 | Complete |
| DATA-04 | Phase 2 | Complete |
| DATA-05 | Phase 2 | Complete |
| DATA-06 | Phase 2 | Complete |
| DATA-07 | Phase 2 | Complete |
| DATA-08 | Phase 2 | Complete |
| DATA-09 | Phase 2 | Complete |
| DATA-10 | Phase 2 | Complete |
| MOD-01 | Phase 3 | Pending |
| MOD-02 | Phase 3 | Pending |
| MOD-03 | Phase 3 | Pending |
| MOD-04 | Phase 3 | Pending |
| MOD-05 | Phase 3 | Pending |
| MOD-06 | Phase 3 | Pending |
| MOD-07 | Phase 3 | Pending |
| TRN-01 | Phase 3 | Pending |
| TRN-02 | Phase 3 | Pending |
| TRN-03 | Phase 3 | Pending |
| TRN-04 | Phase 3 | Pending |
| TRN-05 | Phase 3 | Pending |
| TRN-06 | Phase 3 | Pending |
| EVAL-01 | Phase 4 | Pending |
| EVAL-02 | Phase 4 | Pending |
| EVAL-03 | Phase 4 | Pending |
| EVAL-04 | Phase 4 | Pending |
| EVAL-05 | Phase 4 | Pending |
| TTA-01 | Phase 5 | Pending |
| TTA-02 | Phase 5 | Pending |
| TTA-03 | Phase 5 | Pending |
| TTA-04 | Phase 5 | Pending |
| TTA-05 | Phase 5 | Pending |
| TTA-06 | Phase 5 | Pending |
| TTA-07 | Phase 5 | Pending |
| VIS-01 | Phase 6 | Pending |
| VIS-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-04-03 after Phase 2 plan revision (DATA-06 updated to 1024-d pre-projection)*
