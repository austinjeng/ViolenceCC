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
- [ ] **Phase 4b: XD-Violence Main Results + RTFM XD-I3D Gate** - Gated Fusion + ablations + 3-seed stability on XD-Violence, plus the RTFM XD-I3D gate (rescoped from Phase 4 per 2026-04-15 Option B decision; activated when XD skeleton+CLIP features complete, though the RTFM gate work can start immediately since i3d features are already on disk)
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
  1. ~~RTFM on XD-Violence I3D RGB features reports frame-level AP within ±1% of 77.81%~~ — **DEFERRED to Phase 4b** per 2026-04-15 Option B decision (Rule 4 architectural gap: xd_i3d training dispatch missing from Plan 04-03; Phase 4b owns the integration work and the re-run)
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

### Phase 4b: XD-Violence Main Results + RTFM XD-I3D Gate
**Goal**: (1) Reproduce Phase 4's complete ablation table on XD-Violence — Gated Fusion + pooling ablations + 3-seed stability + per-category breakdown — using the dataset-portable Phase 4 code (evaluate.py, run_ablations.py, extractors with flags). (2) Implement the missing xd_i3d training dispatch and re-run the RTFM XD-I3D gate rescoped from Phase 4 per the 2026-04-15 Option B decision (see `04-06-UAT.md`, `04-06-SUMMARY.md`).
**Depends on**: Phase 4 (code artifacts + deferred scope), Phase 2 DATA-10 (XD skeleton+CLIP extraction complete at E:/features/xd/)
**Activation criterion**: E:/features/xd/skeleton/ and E:/features/xd/clip/ each contain >= 4500 .npy files. Per D-02, Phase 4 does not wait on or monitor this; resume planning with `/gsd-plan-phase 4b` when features land. (Note: the xd_i3d RTFM gate work is NOT gated on XD skeleton/CLIP extraction — it only requires `E:/i3d-features/i3d-features/` which already exists, and may be prioritized ahead of the XD main results work when Phase 4b starts.)
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05 (EVAL-01 rescoped from Phase 4 per Option B decision — Plan 04-03 did not wire the xd_i3d training dispatch claimed by D-36, so the RTFM XD-I3D gate is re-owned by Phase 4b along with the integration work)
**Success Criteria** (what must be TRUE):
  1. RTFM on XD-Violence I3D RGB features reports frame-level AP within +/-1% of 77.81% (D-03 anchor: RTFM-XD; alt anchor: MGFN 80.11%), confirming the xd_i3d training dispatch and evaluation harness are correct (C4 resolved at the XD-I3D boundary)
  2. Gated Fusion achieves frame-level AP >= 80% on XD-Violence official test set, reported by `evaluate.py` with no test set used during training
  3. An ablation table exists with results for all 6 XD model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) and 2 pooling/aggregation ablations, all run on the same XD train/val/test split
  4. Gated Fusion AP on XD-Violence is reported as mean +/- std over 3 independent seeds ({42, 123, 2024}), and the standard deviation is below 0.5%
  5. Per-category breakdown (XD-Violence: Fighting+Abuse+Riot) is computed and shows higher AP on violence-specific subsets versus full test set
**Deferred from Phase 4** (now active):
  - XD skeleton 2-person aggregation re-extraction (`--keep-persons` on XD in extract_ctrgcn.py)
  - XD CLIP mean-only re-extraction (`--pool=mean` on XD in extract_clip.py)
  - XD pooling ablation YAMLs (`configs/gated_fusion_xd_2person.yaml`, `configs/gated_fusion_xd_clip_mean.yaml` — or reuse UCF YAMLs with dataset key swap)
  - XD ablation orchestration queue in `scripts/run_ablations.py` (add `phase4b_main`, `phase4b_pooling`, `phase4b_seeds` sibling queues)
**Rescoped from Phase 4 via Option B** (2026-04-15 DECISION, `04-06-UAT.md`):
  - `build_dataloaders_i3d()` — single-feature loader with 5-crop expansion at train (D-19 5x effective bags) and 5-crop averaging at test; lives in `src/data/loaders.py` alongside the existing paired skel+clip `build_dataloaders()`
  - `train_one_epoch_i3d()` — MIL ranking loss on single `[B, T, 1024]` (or `[B*5, T, 1024]` 5-crop expanded) i3d tensors; no paired skel+clip contract; new branch in `src/train.py`
  - `validate_i3d()` — matching validation path for the i3d-only loader
  - Wu et al. XD-Violence annotation parser in `src/evaluate.py::_build_frame_arrays` to replace the all-zero stub (currently defaults every xd_i3d test label to zero, making AUC/AP meaningless)
  - Re-run the RTFM gate on `xd_i3d_rtfm_i3d_s42` run dir with `scripts/run_ablations.py --queue rtfm_gate`; expected AP >= 0.7681
**Plans**: TBD (plan once XD features land OR prioritize the xd_i3d dispatch + RTFM gate ahead of XD main results since i3d features are already on disk)

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
| 3. Model Architecture & Training Infrastructure | 0/7 | Planned | - |
| 4. Baseline Evaluation & Main Results | 7/7 | Complete | 2026-04-16 |
| 4b. XD-Violence Main Results + RTFM XD-I3D Gate | 0/? | Blocked on XD features (RTFM gate + xd_i3d dispatch can start ahead: i3d features already on disk) | - |
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
*Last updated: 2026-04-16 after Phase 4 closeout (04-07): Phase 4 = 7/7 Complete (UCF-only per D-01); Phase 4b scope expanded to include EVAL-01 RTFM XD-I3D gate + xd_i3d training dispatch per 2026-04-15 Option B decision*
