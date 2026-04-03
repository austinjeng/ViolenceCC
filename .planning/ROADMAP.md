# Roadmap: ViolenceCC

**Project:** Dual-Modal Weakly Supervised VAD (Skeleton GCN + CLIP) with TTA
**Milestone:** 1 — Initial Thesis Results
**Created:** 2026-03-31
**Granularity:** Standard (5-8 phases)
**Coverage:** 40/40 v1 requirements mapped

---

## Phases

- [x] **Phase 1: Environment & Project Foundation** - Three conda envs operational, CTR-GCN weights verified, directory scaffold in place (completed 2026-03-31)
- [ ] **Phase 2: Feature Extraction Pipeline** - Skeleton and CLIP features fully extracted, aligned, and cached for both datasets
- [ ] **Phase 3: Model Architecture & Training Infrastructure** - All model variants built, training loop operational, reproducibility hardened
- [ ] **Phase 4: Baseline Evaluation & Main Results** - RTFM gate passed, all fusion models evaluated on UCF-Crime and XD-Violence, ablation table complete
- [ ] **Phase 5: TTA Infrastructure & Corruption Experiments** - UCF-Crime-C generated, TENT-style and SAR-style TTA evaluated across all 20 corruption conditions
- [ ] **Phase 6: Analysis & Visualization** - Temporal curve plots, skeleton overlays, and per-category breakdowns ready for thesis

---

## Phase Details

### Phase 1: Environment & Project Foundation
**Goal**: The three conda environments are functional, the CTR-GCN forward pass is verified with normalized COCO-17 input, and the project directory structure is ready for code
**Depends on**: Nothing (first phase)
**Requirements**: ENV-01, ENV-02, ENV-03
**Success Criteria** (what must be TRUE):
  1. All three environments (`vcc-skeleton`, `vcc-ctrgcn`, `vcc-main`) activate without error and pass a smoke-test import of their primary packages (rtmlib, PYSKL, open-clip-torch)
  2. A test forward pass through CTR-GCN with a synthetically constructed COCO-17 input (17 joints x 3 channels x 64 frames x 2 persons) produces a 256-d output tensor with no NaN/Inf values, confirming PreNormalize2D is applied and coordinates are in [-1, 1]
  3. The project directory tree (`configs/`, `data/`, `src/`, `scripts/`, `results/`, `notebooks/`) exists and is committed to the repo
**Plans:** 3/3 plans complete
Plans:
- [x] 01-01-PLAN.md — Project directory scaffold, .gitignore, requirements files, and SETUP.md
- [x] 01-02-PLAN.md — Three conda environments, XD-Violence/I3D dataset extraction, feature directory junction
- [x] 01-03-PLAN.md — CTR-GCN weight download and forward pass smoke test

### Phase 2: Feature Extraction Pipeline
**Goal**: Valid, temporally aligned skeleton and CLIP feature caches exist for every video in both UCF-Crime and XD-Violence, verified by the alignment script
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, DATA-10
**Success Criteria** (what must be TRUE):
  1. Official split files for UCF-Crime and XD-Violence are committed to `data/`; a seeded 15% stratified validation split file exists and can be reproduced byte-for-byte from the same seed
  2. Skeleton extraction produces PYSKL-compatible pickle output for a sample of UCF-Crime videos, with joint coordinates confirmed to be in [-1, 1] after PreNormalize2D (C1 resolved)
  3. CTR-GCN feature extraction produces `[N_snippets, 256]` float32 .npy files per video using 4-stream weighted concat (j:b:jm:bm = 1.0:1.0:0.5:0.5)
  4. CLIP extraction produces `[N_snippets, 1024]` float32 .npy files per video with mean+max pooling at 1 FPS (1024-d pre-projection; Phase 3 applies learned projection to 512-d)
  5. `verify_alignment.py` runs to completion with zero failures across all videos in both datasets (N_skel_snippets == N_clip_snippets for every video)
**Plans:** 1/4 plans executed
Plans:
- [x] 02-01-PLAN.md — Data splits and skeleton extraction script
- [x] 02-02-PLAN.md — CTR-GCN and CLIP feature extraction scripts
- [x] 02-03-PLAN.md — UCF-Crime full pipeline run and alignment verification
- [ ] 02-04-PLAN.md — XD-Violence full pipeline run and Phase 2 completion

### Phase 3: Model Architecture & Training Infrastructure
**Goal**: All model variants are implemented and a single configurable training loop can train any of them to convergence with full reproducibility
**Depends on**: Phase 2
**Requirements**: MOD-01, MOD-02, MOD-03, MOD-04, MOD-05, MOD-06, MOD-07, TRN-01, TRN-02, TRN-03, TRN-04, TRN-05, TRN-06
**Success Criteria** (what must be TRUE):
  1. `python train.py --config configs/skeleton_only.yaml` runs to completion on UCF-Crime cached features without crashing, producing a `best_model.pth` and `train_log.csv`
  2. The Gated Fusion module forward pass produces frame-level anomaly scores without NaN, and its LayerNorm layers are accessible by name (verifiable by iterating `model.named_modules()` and confirming `nn.LayerNorm` instances exist)
  3. Early stopping triggers correctly: training halts when validation MIL loss has not improved for 10 consecutive epochs, and the saved checkpoint corresponds to the best validation epoch (confirmed by cross-checking `train_log.csv`)
  4. A config snapshot (JSON) is saved alongside every checkpoint, and re-running with `--config results/<run>/config_snapshot.json` reproduces bit-identical loss curves (confirmed by fixed seed)
**Plans**: TBD

### Phase 4: Baseline Evaluation & Main Results
**Goal**: The evaluation harness is validated by RTFM reproduction, and the complete ablation table with statistical stability measures is ready for the thesis
**Depends on**: Phase 3
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05
**Success Criteria** (what must be TRUE):
  1. RTFM on UCF-Crime with I3D features reports frame-level AUC within ±1% of 84.30%, confirming the evaluation harness is correct (C4 resolved)
  2. Gated Fusion achieves frame-level AUC >= 83% on UCF-Crime official test set and AP >= 80% on XD-Violence official test set, reported by `evaluate.py` with no test set used during training
  3. An ablation table exists with results for all 6 model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) and 2 pooling/aggregation ablations, all run on the same train/val/test split
  4. Gated Fusion AUC/AP on both datasets is reported as mean +/- std over 3 independent seeds, and the standard deviation is below 0.5%
  5. Per-category breakdown (UCF-Crime: Fighting+Assault; XD-Violence: Fighting+Abuse+Riot) is computed and shows higher AUC/AP on violence-specific subsets versus full test set
**Plans**: TBD

### Phase 5: TTA Infrastructure & Corruption Experiments
**Goal**: The UCF-Crime-C corruption benchmark is constructed, and TENT-style and SAR-style TTA results across all 20 conditions are logged and ready for analysis
**Depends on**: Phase 4
**Requirements**: TTA-01, TTA-02, TTA-03, TTA-04, TTA-05, TTA-06, TTA-07
**Success Criteria** (what must be TRUE):
  1. UCF-Crime-C exists on disk as structured subdirectories with all 20 corruption conditions (4 types x 5 severities); a spot-check visually confirms each corruption type is perceptually distinguishable
  2. CLIP features are re-extracted for all 20 conditions; skeleton features are re-extracted for motion blur and JPEG corruption conditions only, and the feature directories follow the expected structured layout
  3. TENT-style adaptation updates only LN affine parameters (gamma, beta), with per-video reset to the source-trained state confirmed by comparing parameter values before and after processing each test video
  4. SAR-style adaptation converges with a grid-searched rho value (not the ImageNet default), and its per-video AUC is logged alongside TENT-style and Source-Only for every corruption condition
  5. A 4x5 results table (corruption type x severity) exists for Source-Only, TENT-style, and SAR-style, and at least one of the TTA methods shows a statistically meaningful improvement over Source-Only on at least one corruption type
**Plans**: TBD

### Phase 6: Analysis & Visualization
**Goal**: Qualitative figures and temporal analysis are complete and polished enough to drop directly into the thesis document
**Depends on**: Phase 5
**Requirements**: VIS-01, VIS-02
**Success Criteria** (what must be TRUE):
  1. Anomaly score temporal curve plots exist for at least 2 UCF-Crime and 1 XD-Violence representative video, with ground-truth anomaly intervals shaded and scores correctly expanded from snippet level to frame level
  2. Skeleton overlay visualizations exist for at least 3 video frames showing COCO-17 keypoints and edges drawn on the original image, confirming extraction quality for a thesis figure
**Plans**: TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Environment & Project Foundation | 3/3 | Complete   | 2026-03-31 |
| 2. Feature Extraction Pipeline | 1/4 | In Progress|  |
| 3. Model Architecture & Training Infrastructure | 0/? | Not started | - |
| 4. Baseline Evaluation & Main Results | 0/? | Not started | - |
| 5. TTA Infrastructure & Corruption Experiments | 0/? | Not started | - |
| 6. Analysis & Visualization | 0/? | Not started | - |

---

## Requirement Coverage

| Requirement | Phase |
|-------------|-------|
| ENV-01 | Phase 1 |
| ENV-02 | Phase 1 |
| ENV-03 | Phase 1 |
| DATA-01 | Phase 2 |
| DATA-02 | Phase 2 |
| DATA-03 | Phase 2 |
| DATA-04 | Phase 2 |
| DATA-05 | Phase 2 |
| DATA-06 | Phase 2 |
| DATA-07 | Phase 2 |
| DATA-08 | Phase 2 |
| DATA-09 | Phase 2 |
| DATA-10 | Phase 2 |
| MOD-01 | Phase 3 |
| MOD-02 | Phase 3 |
| MOD-03 | Phase 3 |
| MOD-04 | Phase 3 |
| MOD-05 | Phase 3 |
| MOD-06 | Phase 3 |
| MOD-07 | Phase 3 |
| TRN-01 | Phase 3 |
| TRN-02 | Phase 3 |
| TRN-03 | Phase 3 |
| TRN-04 | Phase 3 |
| TRN-05 | Phase 3 |
| TRN-06 | Phase 3 |
| EVAL-01 | Phase 4 |
| EVAL-02 | Phase 4 |
| EVAL-03 | Phase 4 |
| EVAL-04 | Phase 4 |
| EVAL-05 | Phase 4 |
| TTA-01 | Phase 5 |
| TTA-02 | Phase 5 |
| TTA-03 | Phase 5 |
| TTA-04 | Phase 5 |
| TTA-05 | Phase 5 |
| TTA-06 | Phase 5 |
| TTA-07 | Phase 5 |
| VIS-01 | Phase 6 |
| VIS-02 | Phase 6 |

**Total:** 40/40 requirements mapped

---

*Roadmap created: 2026-03-31*
*Last updated: 2026-04-03 after Phase 2 planning*
