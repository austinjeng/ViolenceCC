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
- [x] **Phase 4: Baseline Evaluation & Main Results** - UCF-Crime fusion models evaluated, 8 ablation rows complete, 3-seed stability PASS (completed 2026-04-16; RTFM gate deferred to Phase 4b per 2026-04-15 Option B decision)
- [x] **Phase 4b: RTFM XD-I3D Gate** - xd_i3d training dispatch + Wu XD annotation parser + RTFM XD-I3D-RGB gate (AP 0.6570 vs 0.7681 target — MISS-ACCEPTED per D-11 fallback-step-4 / thesis-limitation pattern; D-12 diagnostics PASS confirm dispatch correct; Flow diagnostic ruled out data-coverage as cause; completed 2026-04-16 per D-01 scope narrowing, XD main results carved out to new Phase 4c)
- [x] **Phase 4c: XD-Violence Main Results** - 8-row XD ablation table complete; Gated Fusion AP=71.92% MISS-ACCEPTED per D-06; default pooling outperforms 2-person/clip-mean; per-category reveals Abuse as hardest category (completed 2026-04-28)
- [ ] **Phase 5: TTA Infrastructure & Corruption Experiments** - UCF-Crime-C generated, TENT-style and SAR-style TTA evaluated across all 20 corruption conditions
- [ ] **Phase 6: Analysis & Visualization** - Temporal curve plots, skeleton overlays, and per-category breakdowns ready for thesis
- [x] **Phase 7: XD-Violence Hyperparameter Sweep** - 198-config sweep across XD + UCF; XD winner lr=1e-3/k=2 (AP=74.69%, +3.72pp); UCF hyperparameter-insensitive; RTFM gap = training regime (completed 2026-05-02)
- [x] **Phase 8: SigLIP2 Backbone Comparison** - Swap CLIP ViT-B/16 with SigLIP2 ViT-B/16-256 as visual-language backbone; re-extract features, run identical ablations on UCF-Crime and XD-Violence, compare against CLIP results for thesis (completed 2026-05-20; UCF: SigLIP2 ~2pp below CLIP AUC; XD: roughly competitive, slight AP gains on pooling ablations)
- [x] **Phase 9: SigLIP2-SO400M Backbone Comparison** - Swap CLIP ViT-B/16 with SigLIP2 SO400M (google/siglip2-so400m-patch16-256) as visual-language backbone; re-extract features, run identical ablation matrix, compare against CLIP and SigLIP2 ViT-B/16-256 for thesis (completed 2026-05-21)

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
- [x] 02-04-PLAN.md — XD-Violence full pipeline run and Phase 2 completion

### Phase 3: Model Architecture & Training Infrastructure

**Goal**: All model variants are implemented and a single configurable training loop can train any of them to convergence with full reproducibility
**Depends on**: Phase 2
**Requirements**: MOD-01, MOD-02, MOD-03, MOD-04, MOD-05, MOD-06, MOD-07, TRN-01, TRN-02, TRN-03, TRN-04, TRN-05, TRN-06
**Success Criteria** (what must be TRUE):

  1. `python train.py --config configs/skeleton_only.yaml` runs to completion on UCF-Crime cached features without crashing, producing a `best_model.pth` and `train_log.csv`
  2. The Gated Fusion module forward pass produces frame-level anomaly scores without NaN, and its LayerNorm layers are accessible by name (verifiable by iterating `model.named_modules()` and confirming `nn.LayerNorm` instances exist)
  3. Early stopping triggers correctly: training halts when validation MIL loss has not improved for 10 consecutive epochs, and the saved checkpoint corresponds to the best validation epoch (confirmed by cross-checking `train_log.csv`)
  4. A config snapshot (JSON) is saved alongside every checkpoint, and re-running with `--config results/<run>/config_snapshot.json` reproduces bit-identical loss curves (confirmed by fixed seed)

**Plans:** 7 plans
Plans:

- [x] 03-01-PLAN.md — Foundation primitives (seed utility, MILHead, MODEL_REGISTRY skeleton, pytest scaffold, requirements pins)
- [x] 03-02-PLAN.md — MIL Ranking Loss (RTFM-exact sparsity+smoothness, masked top-k, MOD-01)
- [x] 03-03-PLAN.md — MILFeatureDataset + paired DataLoaders (D-04/D-09/D-10/D-12, MOD-02)
- [x] 03-04-PLAN.md — SkeletonProj + CLIPProj + LateFusion wrappers with named LNs (MOD-03/04/05/07)
- [x] 03-05-PLAN.md — GatedFusion module with 3 named LNs + m1 gate init mitigation (MOD-06/07)
- [x] 03-06-PLAN.md — Training loop: scheduler, early stopping, atomic checkpoint, CSV logger, src/train.py, bit-identical repro (TRN-01..04, TRN-06, C3, C5)
- [x] 03-07-PLAN.md — Config snapshot (TRN-05) + wandb mirror (D-13) + 4 variant YAMLs + e2e acceptance tests (TRN-05/06)

### Phase 4: Baseline Evaluation & Main Results

**Goal**: UCF-Crime evaluation harness built and the UCF ablation table with statistical stability measures is ready for the thesis. XD-Violence main results move to Phase 4b per D-01. The RTFM XD-I3D gate was ALSO rescoped to Phase 4b (2026-04-15 Option B) because Plan 04-03 did not wire the claimed xd_i3d training dispatch (D-36) — see `04-06-UAT.md` and `04-06-SUMMARY.md`.
**Depends on**: Phase 3
**Requirements**: EVAL-02, EVAL-03, EVAL-04, EVAL-05 (EVAL-01 rescoped to Phase 4b — see Phase 4b block)
**Success Criteria** (what must be TRUE):

  1. ~~RTFM on XD-Violence I3D RGB features reports frame-level AP within +/-1% of 77.81%~~ — **DEFERRED to Phase 4b** per 2026-04-15 Option B decision (Rule 4 architectural gap: xd_i3d training dispatch missing from Plan 04-03; Phase 4b owns the integration work and the re-run)
  2. Gated Fusion achieves frame-level AUC >= 83% on UCF-Crime official test set, reported by `evaluate.py` with no test set used during training — **MISS (documented, accepted):** observed 0.8227 (0.73 pp below target); 3-seed mean 0.81982 confirms architectural, not seed variance
  3. An ablation table exists with results for all 6 model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) and 2 pooling/aggregation ablations on UCF, all run on the same train/val/test split — **PASS:** 8 UCF rows in results-index.csv
  4. Gated Fusion AUC on UCF is reported as mean +/- std over 3 independent seeds ({42, 123, 2024}), and the standard deviation is below 0.5% — **PASS:** std 0.00291 = 0.29%
  5. Per-category breakdown (UCF-Crime: Fighting+Assault) is computed and shows higher AUC on violence-specific subsets versus full test set — **PASS:** Fighting 0.955 (+13.23 pp), Assault 0.985 (+16.19 pp)

**Plans:** 7/7 plans complete (2026-04-16)
Plans:

- [x] 04-01-PLAN.md — Wave 0 fixtures + snippet_to_frame + ucf_annotations parser (D-04, D-14..D-17, C4)
- [x] 04-02-PLAN.md — test_loader.py (C3 guards) + evaluate.py CLI + metrics.py + config_hash/checkpoint_sha/git_sha (D-06..D-13, D-31)
- [x] 04-03-PLAN.md — RTFMI3D model + I3DFeatureDataset (5-crop) + rtfm_i3d.yaml + MODEL_REGISTRY entry (D-18..D-20, D-36) **[xd_i3d training dispatch gap discovered in 04-06; rescoped to Phase 4b per Option B]**
- [x] 04-04-PLAN.md — Pooling re-extraction flags + skel_agg loader + 2 ablation YAMLs + verify_pooling_caches.py (D-21..D-25, D-37)
- [x] 04-05-PLAN.md — scripts/run_ablations.py + wandb_preflight + csv_logger.results_index_append + train.py --run-name (D-26..D-34, D-39..D-41)
- [x] 04-06-PLAN.md — Empirical execution: UCF main queue, pooling ablations, 3-seed stability, 6 HUMAN-UAT items (non-autonomous); RTFM gate blocked and deferred to Phase 4b
- [x] 04-07-PLAN.md — Close Phase 4 + carve out expanded Phase 4b (XD main results + EVAL-01 RTFM XD-I3D gate + xd_i3d training dispatch implementation)

### Phase 4b: RTFM XD-I3D Gate

**Goal**: The xd_i3d training dispatch (`build_dataloaders_i3d`, `train_one_epoch_i3d`, `validate_i3d`, Wu et al. annotation parser) is implemented, and the RTFM XD-I3D-RGB baseline is empirically executed against the +/-1% of 77.81% published anchor. (Rescoped from Phase 4 per 2026-04-15 Option B decision; scope narrowed to RTFM gate only per D-01 of 04b-CONTEXT.md, XD main results carved out to new Phase 4c.)
**Depends on**: Phase 4 (architectural patterns + code artifacts), E:/i3d-features/i3d-features (RGB + RGBTest I3D features on disk; RGB 3225/3954 partial due to V/W/Y extraction truncation, Flow 3954/3954 complete)
**Requirements**: EVAL-01
**Success Criteria** (what must be TRUE):

  1. RTFM on XD-Violence I3D RGB features reports frame-level AP within +/-1% of 77.81% (primary anchor RTFM 77.81%; secondary anchor MGFN I3D-RGB 79.19% per 04b-RESEARCH.md correction — NOT 80.11% VideoSwin) — **MISS-ACCEPTED per D-11 fallback-step-4 / thesis-limitation pattern:** observed AP 0.6570 (11.11 pp below primary, 13.49 pp below secondary); Flow diagnostic rerun with 100% data coverage produced worse AP 0.5916 (-6.54 pp vs RGB), confirming modeling capacity and not data coverage is the bottleneck; mirrors Phase 4 EVAL-02 UCF 0.8227 MISS-accepted pattern
  2. xd_i3d training dispatch (`build_dataloaders_i3d`, `train_one_epoch_i3d`, `validate_i3d`) exists in `src/data/loaders.py` + `src/train.py` with D-04 parallel-functions discipline (no polymorphic dispatch) — **PASS**
  3. Wu et al. XD-Violence annotation parser (`src/eval/xd_annotations.py`) + `data/annotations/xd_temporal.txt` committed; `src/evaluate.py::_build_frame_arrays` xd_i3d path rewritten (replacing the all-zero stub from Phase 4) — **PASS**
  4. D-12 diagnostic passes: C4 sanity (|auc - snippet_auc| = 0.0024 < 0.02), 5-crop bag-size audit ([i3d_audit] log line with n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024)) — **PASS** (bit-identical rerun not performed; gate-miss path triggered D-11 cascade instead)
  5. 4 new pytest test files pass: test_xd_annotations.py (8 tests), test_loaders_i3d.py (5 tests), test_train_i3d.py (3 tests), test_evaluate_xd_i3d.py (4 tests) — **PASS**

**Plans:** 5/5 plans complete (2026-04-16)
Plans:

- [x] 04b-01-PLAN.md — Wu annotation parser + `data/annotations/xd_temporal.txt` + `tests/test_xd_annotations.py` (D-07, D-10)
- [x] 04b-02-PLAN.md — `build_dataloaders_i3d` + `collate_i3d_train` + `tests/test_loaders_i3d.py` (D-04, D-05, D-06; Pitfalls 1/4/7; Open Questions 1/2)
- [x] 04b-03-PLAN.md — `train_one_epoch_i3d` + `validate_i3d` + `main()` dispatch branch + `tests/test_train_i3d.py` (D-04; D-12 bag-size audit)
- [x] 04b-04-PLAN.md — `src/evaluate.py::_build_frame_arrays` xd_i3d branch rewrite + `tests/test_evaluate_xd_i3d.py` (D-08, D-09, D-10)
- [x] 04b-05-PLAN.md — Smoke test (D-16) + full `rtfm_gate` queue run + Flow diagnostic rerun (Rule 1 scope expansion) + D-12 diagnostic cascade + ROADMAP/REQUIREMENTS split per D-01 + `04b-05-SUMMARY.md` (HUMAN-UAT MISS-ACCEPTED)

### Phase 4c: XD-Violence Main Results

**Goal**: Reproduce Phase 4's complete ablation table on XD-Violence — Gated Fusion + pooling ablations + 3-seed stability + per-category breakdown (Fighting/Abuse/Riot) — using the dataset-portable Phase 4 code (evaluate.py, run_ablations.py, extractors with flags). Relocated from the original Phase 4b scope per D-01 scope narrowing (see 04b-CONTEXT.md).
**Depends on**: Phase 4 (code artifacts), Phase 4b (xd_i3d dispatch + Wu annotation parser for the fusion-XD eval path), Phase 2 DATA-10 (XD skeleton+CLIP extraction complete at E:/features/xd/)
**Activation criterion**: `ls -1 E:/features/xd/skeleton/*.npy | wc -l >= 4500 && ls -1 E:/features/xd/clip/*.npy | wc -l >= 4500`. Checked at each `/gsd-progress` invocation; when both counts pass, the user triggers `/gsd-plan-phase 4c`. No polling infrastructure needed (D-03 of 04b-CONTEXT.md).
**Requirements**: EVAL-02, EVAL-03, EVAL-04, EVAL-05 (XD-side; UCF-side already complete in Phase 4)
**Success Criteria** (what must be TRUE):

  1. Gated Fusion achieves frame-level AP >= 80% on XD-Violence official test set, reported by `evaluate.py` with no test set used during training — **MISS-ACCEPTED (D-06 step 2):** AP=71.92% (s42), mean=70.98% (3-seed); 70-79% range, documented as thesis limitation
  2. An ablation table exists with results for all 6 XD model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) and 2 pooling/aggregation ablations, all run on the same XD train/val/test split — **PASS:** 8 XD rows in results-index.csv
  3. Gated Fusion AP on XD-Violence is reported as mean +/- std over 3 independent seeds ({42, 123, 2024}), and the standard deviation is below 0.5% — **PARTIAL:** AP std=1.08% (exceeds gate), AUC std=0.29% (within gate); seed sensitivity documented as thesis finding
  4. Per-category breakdown (XD-Violence: Fighting+Abuse+Riot) is computed and shows higher AP on violence-specific subsets versus full test set — **PARTIAL:** Fighting (77.76%) and Riot (88.15%) individually exceed full AP (71.92%); Abuse (44.89%) drags subset mean to 70.27% (below full AP)

**Scope (relocated from former Phase 4b per D-01):**

  - XD skeleton 2-person aggregation re-extraction (`--keep-persons` on XD in extract_ctrgcn.py)
  - XD CLIP mean-only re-extraction (`--pool=mean` on XD in extract_clip.py)
  - XD pooling ablation YAMLs (`configs/gated_fusion_xd_2person.yaml`, `configs/gated_fusion_xd_clip_mean.yaml` — or reuse UCF YAMLs with dataset key swap)
  - XD ablation orchestration queues in `scripts/run_ablations.py` (add `phase4c_main`, `phase4c_pooling`, `phase4c_seeds` queues)
  - Per-category Fighting/Abuse/Riot breakdown (uses `_parse_category` from `src/eval/xd_annotations.py` delivered in Phase 4b)

**Plans:** 3/3 plans complete (2026-04-28)
Plans:

- [x] 04C-01-PLAN.md — XD split cleaning + evaluate.py XD fusion branch + 6 configs + 3 queues + tests
- [x] 04C-02-PLAN.md — Execute phase4c_main and phase4c_seeds queues (6 XD runs) + D-06 AP assessment
- [x] 04C-03-PLAN.md — User re-extraction checkpoint + phase4c_pooling queue (2 runs) + final ablation table

### Phase 5: TTA Infrastructure & Corruption Experiments

**Goal**: The UCF-Crime-C corruption benchmark is constructed, and TENT-style and SAR-style TTA results across all 20 conditions are logged and ready for analysis
**Depends on**: Phase 4
**Requirements**: TTA-01, TTA-02, TTA-03, TTA-04, TTA-05, TTA-06, TTA-07
**Success Criteria** (what must be TRUE):

  1. UCF-Crime-C exists on disk as structured subdirectories with all 20 corruption conditions (4 types x 5 severities); a spot-check visually confirms each corruption type is perceptually distinguishable
  2. CLIP features are re-extracted for all 20 conditions; skeleton features are re-extracted for motion blur and JPEG compression conditions only, and the feature directories follow the expected structured layout
  3. TENT-style adaptation updates only LN affine parameters (gamma, beta), with per-video reset to the source-trained state confirmed by comparing parameter values before and after processing each test video
  4. SAR-style adaptation converges with a grid-searched rho value (not the ImageNet default), and its per-video AUC is logged alongside TENT-style and Source-Only for every corruption condition
  5. A 4x5 results table (corruption type x severity) exists for Source-Only, TENT-style, and SAR-style, and at least one of the TTA methods shows a statistically meaningful improvement over Source-Only on at least one corruption type

**Plans:** 5 plans
Plans:

- [x] 05-01-PLAN.md — Corruption transform module (scripts/corruption.py) with 4 types x 5 severities using numpy+cv2 (TTA-01, TTA-03)
- [x] 05-02-PLAN.md — TENT/SAR/SAM adaptation modules (src/tta/) with LN targeting and binary entropy (TTA-04, TTA-05, TTA-07)
- [x] 05-03-PLAN.md — Extraction script corruption flags + human-supervised batch re-extraction ~15h (TTA-02, TTA-03)
- [x] 05-04-PLAN.md — TTA evaluation entry point (src/tta/evaluate_tta.py) wiring adaptation + Phase 4 metrics (TTA-06, TTA-07)
- [x] 05-05-PLAN.md — Queue orchestrator extension (TTARunSpec + 500-run grid) + empirical execution (TTA-06)

### Phase 6: Analysis & Visualization

**Goal**: Qualitative figures and temporal analysis are complete and polished enough to drop directly into the thesis document
**Depends on**: Phase 5
**Requirements**: VIS-01, VIS-02
**Success Criteria** (what must be TRUE):

  1. Anomaly score temporal curve plots exist for at least 2 UCF-Crime and 1 XD-Violence representative video, with ground-truth anomaly intervals shaded and scores correctly expanded from snippet level to frame level
  2. Skeleton overlay visualizations exist for at least 3 video frames showing COCO-17 keypoints and edges drawn on the original image, confirming extraction quality for a thesis figure

**Plans:** 2/2 plans complete
Plans:

- [x] 06-01-PLAN.md -- Temporal curves (Section A), corruption heatmaps (Section C), additional thesis figures (Section F)
- [x] 06-02-PLAN.md -- Skeleton overlays (Section B), gate distributions (Section D), t-SNE projections (Section E)

### Phase 7: XD-Violence Hyperparameter Sweep

**Goal**: Improve Gated Fusion AP on XD-Violence through targeted hyperparameter optimization; investigate RTFM repro gap (65.70% vs published 77.81%) to determine if systematic evaluation offset affects fusion results
**Depends on**: Phase 4c (XD ablation table complete, baseline AP=71.92%)
**Requirements**: None new (extends EVAL-02 XD-side)
**Success Criteria** (what must be TRUE):

  1. A sweep grid of at least lr x k_topk combinations (~20 runs) is executed on XD-Violence Gated Fusion, with all results logged to results-index.csv
  2. The best sweep configuration achieves AP > 71.92% (the Phase 4c s42 baseline), demonstrating hyperparameter sensitivity
  3. RTFM XD-I3D repro gap is investigated with at least one diagnostic (annotation alignment or temporal interpolation check), and findings are documented
  4. A summary table comparing sweep results against Phase 4c baselines exists, suitable for thesis inclusion

**Plans:** 4 plans
Plans:

- [x] 07-01-PLAN.md — CLI overrides (--lr, --k-topk) in train.py + RunSpec extension in run_ablations.py
- [x] 07-02-PLAN.md — phase7_sweep queue (20 entries) + RTFM diagnostic script + chart generation script
- [x] 07-03-PLAN.md — Empirical execution: 198 sweep configs (99 XD + 99 UCF) + RTFM diagnostics + checkpoint approval
- [x] 07-04-PLAN.md — 3-seed confirmation + heatmap generation + thesis-ready summary document

### Phase 8: SigLIP2 Backbone Comparison

**Goal**: Replace CLIP ViT-B/16 with SigLIP2 Giant (google/siglip2-giant-opt-patch16-384) as the visual-language feature backbone, re-extract features for both datasets, and run the identical ablation matrix (model variants, pooling, seeds) under controlled conditions to produce a direct backbone comparison for the thesis
**Depends on**: Phase 4 (UCF ablation table + evaluation harness), Phase 4c (XD ablation table), Phase 2 (extraction pipeline patterns)
**Requirements**: None new (extends EVAL-02, EVAL-03, EVAL-04 with alternative backbone)
**Success Criteria** (what must be TRUE):

  1. SigLIP2 Giant features are extracted for all UCF-Crime and XD-Violence videos using the same snippet boundaries and temporal alignment as the original CLIP extraction
  2. All model variants (Skeleton-Only baseline unchanged, SigLIP2-Only, Late Fusion, Gated Fusion) and pooling ablations are trained and evaluated on both datasets with identical configs (only the visual feature path changes)
  3. 3-seed stability runs ({42, 123, 2024}) are completed for Gated Fusion on both datasets with SigLIP2 features
  4. A side-by-side comparison table (CLIP vs SigLIP2) exists for all ablation rows on both datasets, suitable for thesis inclusion

**Plans:** 4 plans
Plans:
**Wave 1**

- [x] 08-01-PLAN.md -- Extraction script backbone parameterization (--backbone flag + BACKBONE_CONFIGS + tests)
- [x] 08-02-PLAN.md -- 10 SigLIP2 YAML configs + 6 Phase 8 queues in run_ablations.py + model dim tests

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-03-PLAN.md -- SigLIP2 feature extraction for UCF-Crime and XD-Violence (~5 hours GPU)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 08-04-PLAN.md -- Execute 14 ablation runs + 3-seed stability + CLIP vs SigLIP2 comparison table

### Phase 9: SigLIP2-SO400M Backbone Comparison

**Goal**: Swap CLIP ViT-B/16 with SigLIP2 SO400M (google/siglip2-so400m-patch16-256) as the visual-language feature backbone, re-extract features for both datasets, and run the identical ablation matrix (model variants, pooling, seeds) under controlled conditions to produce a direct backbone comparison against CLIP and SigLIP2 ViT-B/16-256 for the thesis
**Depends on**: Phase 4 (UCF ablation table + evaluation harness), Phase 4c (XD ablation table), Phase 2 (extraction pipeline patterns), Phase 8 (SigLIP2 ViT-B/16-256 results + backbone parameterization infrastructure)
**Requirements**: None new (extends EVAL-02, EVAL-03, EVAL-04 with alternative backbone)
**Success Criteria** (what must be TRUE):

  1. SigLIP2 SO400M features are extracted for all UCF-Crime and XD-Violence videos using the same snippet boundaries and temporal alignment as the original CLIP and SigLIP2 ViT-B/16-256 extraction
  2. All model variants (Skeleton-Only baseline unchanged, SigLIP2-SO400M-Only, Late Fusion, Gated Fusion) and pooling ablations are trained and evaluated on both datasets with identical configs (only the visual feature path changes)
  3. 3-seed stability runs ({42, 123, 2024}) are completed for Gated Fusion on both datasets with SigLIP2 SO400M features
  4. A three-way comparison table (CLIP vs SigLIP2 ViT-B/16-256 vs SigLIP2 SO400M) exists for all ablation rows on both datasets, suitable for thesis inclusion


**Plans:** 4/4 plans complete
Plans:
**Wave 1**

- [x] 09-01-PLAN.md -- SO400M backbone config, 10 YAML configs, 6 ablation queues, test updates

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-02-PLAN.md -- SO400M feature extraction for UCF-Crime and XD-Violence (~1.1 hrs GPU)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-03-PLAN.md -- Run 14 SO400M ablation experiments (8 main + 6 seed stability)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 09-04-PLAN.md -- Three-way comparison analysis script, tables, and charts

### Phase 10: SigLIP2 Giant-opt Backbone Comparison

**Goal**: Add SigLIP2 Giant-opt (ViT-gopt-16-SigLIP2-256, 1.16B vision params, 1536-d) as the fourth backbone, re-extract features, run the identical ablation matrix, and produce a four-way backbone comparison table for the thesis
**Depends on**: Phase 9 (SO400M results + infrastructure), Phase 8 (SigLIP2 ViT-B/16 results), Phase 4/4c (CLIP results)
**Requirements**: None new (extends EVAL-02, EVAL-03, EVAL-04)
**Success Criteria**:

  1. SigLIP2 Giant-opt features extracted for all UCF-Crime and XD-Violence videos (train+val+test splits)
  2. All model variants and pooling ablations trained and evaluated on both datasets with Giant-opt features
  3. 3-seed stability runs completed for Gated Fusion on both datasets
  4. Four-way comparison table (CLIP vs SigLIP2 ViT-B/16 vs SO400M vs Giant-opt) exists for all ablation rows

**Plans:** 0/4 plans complete
Plans:
**Wave 1**

- [ ] 10-01-PLAN.md -- Giant-opt backbone config, 10 YAML configs, 6 ablation queues, test updates

**Wave 2** *(blocked on Wave 1)*

- [ ] 10-02-PLAN.md -- Giant-opt feature extraction for UCF-Crime and XD-Violence (12 runs: train+val+test)

**Wave 3** *(blocked on Wave 2)*

- [ ] 10-03-PLAN.md -- Run 14 Giant-opt ablation experiments (8 main + 6 seed stability)

**Wave 4** *(blocked on Wave 3)*

- [ ] 10-04-PLAN.md -- Four-way comparison analysis script, tables, and charts

### Phase 11: Thesis Manuscript

**Goal**: Write the full master's thesis manuscript targeting a workshop venue, integrating all experimental results (CLIP baseline, SigLIP2 backbone comparisons, ablation studies) into a cohesive document with introduction, related work, methodology, experiments, and conclusion chapters
**Depends on**: Phase 10 (four-way backbone comparison), Phase 7 (hyperparameter sweep), Phase 4/4c (baseline results)
**Requirements**: None new (writing deliverable, not code)
**Success Criteria**:

  1. Complete thesis manuscript draft with all required chapters
  2. All experimental results tables and figures integrated from pipeline outputs
  3. Workshop-ready formatting and submission compliance

**Plans:** 2/4 plans executed
Plans:
**Wave 1**

- [x] 11-01-PLAN.md -- TTA backbone extension (evaluate_tta.py parameterization + corrupted feature extraction + TTA evaluation grid)
- [x] 11-02-PLAN.md -- Paper directory setup + BibTeX library + LaTeX scaffold

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 11-03-PLAN.md -- Publication-quality figures + architecture diagram

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 11-04-PLAN.md -- Complete LaTeX paper draft (full prose, tables, figures, citations)

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Environment & Project Foundation | 3/3 | Complete   | 2026-03-31 |
| 2. Feature Extraction Pipeline | 1/4 | In Progress|  |
| 3. Model Architecture & Training Infrastructure | 0/7 | Planned | - |
| 4. Baseline Evaluation & Main Results | 7/7 | Complete | 2026-04-16 |
| 4b. RTFM XD-I3D Gate | 5/5 | Complete (MISS-ACCEPTED) | 2026-04-16 |
| 4c. XD-Violence Main Results | 3/3 | Complete (MISS-ACCEPTED) | 2026-04-28 |
| 5. TTA Infrastructure & Corruption Experiments | 0/5 | Planned | - |
| 6. Analysis & Visualization | 2/2 | In Progress | - |
| 7. XD-Violence Hyperparameter Sweep | 4/4 | Complete | 2026-05-02 |
| 8. SigLIP2 Backbone Comparison | 4/4 | Complete | 2026-05-20 |
| 9. SigLIP2-SO400M Backbone Comparison | 4/4 | Complete   | 2026-05-21 |
| 10. SigLIP2 Giant-opt Backbone Comparison | 0/4 | Executing | - |
| 11. Thesis Manuscript | 2/4 | In Progress|  |

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
| EVAL-01 | Phase 4b |
| EVAL-02 | Phase 4 (UCF), Phase 4c (XD) |
| EVAL-03 | Phase 4 (UCF), Phase 4c (XD) |
| EVAL-04 | Phase 4 (UCF), Phase 4c (XD) |
| EVAL-05 | Phase 4 (UCF), Phase 4c (XD) |
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
*Last updated: 2026-05-02 — Phase 7 complete: 198-config sweep, XD winner lr=1e-3/k=2 (+3.72pp), UCF insensitive*
