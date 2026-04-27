---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: --phase
current_plan: 1
status: executing
stopped_at: Phase 4c complete (MISS-ACCEPTED), advancing to Phase 5
last_updated: "2026-04-27T20:32:56.086Z"
progress:
  total_phases: 8
  completed_phases: 6
  total_plans: 34
  completed_plans: 29
  percent: 85
---

# State: ViolenceCC

**Last updated:** 2026-04-08
**Session:** Phase 02 UAT in progress (8/12 pass, 4 blocked on XD-Violence extraction). UCF-Crime fully verified (1728/1900 extractable, 172 sub-64-frame). XD-Violence skeleton extraction running (~20% done, ~5-8 days remaining). Profiling shows 99.3% inference bottleneck at 21.6 FPS — no optimization available without replacing rtmlib. Ready to begin Phase 3 with UCF-Crime data while XD extraction continues.

---

## Project Reference

**Core value:** A working dual-modal (Skeleton + CLIP) fusion pipeline that produces reproducible frame-level AUC/AP numbers on UCF-Crime and XD-Violence, with complete ablation analysis and TTA experiments.

**Milestone:** 1 — Initial Thesis Results
**Timeline:** 12 weeks (started 2026-03-31, target completion 2026-06-23)

---

## Current Position

Phase: --phase (05) — EXECUTING
Plan: 1 of --name
**Current phase:** --phase
**Current plan:** 1
**Status:** Executing Phase --phase

**Progress:**

[████████░░] 88%
Phase 2 [████████░░] 80%   Feature Extraction Pipeline (4/4 plans done, UAT partial: XD extraction running)
Phase 3 [          ] 0%    Model Architecture & Training Infrastructure
Phase 4 [          ] 0%    Baseline Evaluation & Main Results
Phase 5 [          ] 0%    TTA Infrastructure & Corruption Experiments
Phase 6 [          ] 0%    Analysis & Visualization

```

---

## Performance Metrics

No experiments run yet. Targets from PRD v2.3:

| Metric | Minimum Gate | Target Range |
|--------|-------------|--------------|
| UCF-Crime frame-level AUC | 83% | 85-87% |
| XD-Violence frame-level AP | 80% | 82-85% |
| RTFM reproduction AUC | 84.30% ± 1% | — (gate, not target) |

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01-environment P01 | 8min | 2 tasks | 18 files |
| Phase 01-environment P02 | 78 | 2 tasks | 10 files |
| Phase 01-environment P03 | 35min | 2 tasks | 5 files |
| Phase 02 P01 | 16 | 2 tasks | 10 files |
| Phase 02 P02 | 8min | 2 tasks | 2 files |
| Phase 02 P03 | 23min | 2 tasks | 3 files |
| Phase 02-feature-extraction-pipeline P04 | 15min | 1 tasks | 4 files |
| Phase 04 P07 | 4min | 1 tasks | 3 files |
| Phase 04C P01 | 9min | 2 tasks | 12 files |
| Phase 04C P02 | 16min | 1 tasks | 6 files |
| Phase 04C P03 | 10min | 2 tasks | 4 files |

## Accumulated Context

### Key Decisions (inherited from research phase)

| Decision | Rationale |
|----------|-----------|
| Three conda environments | mmcv-full 1.x cannot coexist with PyTorch 2.x; vcc-ctrgcn is a legacy silo |
| All backbones frozen | VRAM constraint + 3-stage methodological cleanliness |
| float32 .npy per video | Simpler than HDF5; no dtype mismatch risk; ~25 GB per dataset fits |
| RTFM reproduction gates novel experiments | Validates evaluation harness; catches C4 (AUC calculation bugs) |
| 15% stratified val split committed before first training run | All experiments use identical split; changing it later invalidates comparisons |
| Late Fusion before Gated Fusion | 2-hour implementation; validates full pipeline before adding learned gating complexity |
| LN-only TTA (not BN) | Fusion head uses LayerNorm; the BN→LN transfer is itself a research contribution |
| Single train.py with YAML config | Avoids VadCLIP's per-dataset duplication anti-pattern |
| English codebase | Standard for ML research repos |
| results/.gitkeep not committed | .gitignore excludes results/ by design (D-07); directory created locally as needed |
| requirements files are reference documents | conda and --index-url packages documented as comments; not pip install -r targets |
| PyTorch 1.12.1 conda wheel fails on Windows | WinError 182 (DLL ordinal conflict); must use pip +cu113 wheel in vcc-ctrgcn |
| mmpose/PYSKL installed with --no-deps | chumpy build failure on modern pip; PYSKL doesn't need SMPL mesh estimation |
| XD-Violence test videos at test/videos/ subfolder | Source zip had top-level videos/ folder; Phase 2 scripts must use this path |
| XD-Violence anomaly labels from filename suffix | _label_A=normal, B*/G*=anomalous; XD_violence_annotations.txt is frame-level temporal annotations, not a label list |
| rtmlib Wholebody uses mode='balanced' (not pose name) | mode string drives ONNX model download; 'performance'/'balanced'/'lightweight' are valid modes |
| UCF-Crime PNGs are 64x64 pixels | Pre-extracted at this resolution; img_shape=(64,64) in skeleton pickles is correct |
| onnxruntime-gpu CUDA provider needs cuDNN 9.x on PATH | DLL missing error; CPU fallback works but ~10x slower; fix PATH before full extraction |
| cuDNN 9.x CUDA 12 DLLs in v9.8/bin/12.8/ not v9.8/bin/ | Windows cuDNN 9 organizes DLLs by CUDA version in subdirs; PATH must include 12.8/ subdir for cudnn64_9.dll |
| 4 CRC-corrupt files in 1005-2004.zip | Pre-existing source zip corruption; <0.1% training data loss, acceptable |
| CTRGCN.forward() expects (N,M,T,V,C); NTU120 checkpoint requires M=2 | data_bn has 102=2*17*3 channels; pool backbone over M/T/V to get (N,256) |
| PYSKL checkpoints are plain OrderedDicts (no state_dict wrapper) | Load directly with strict=False; not wrapped like mmcv checkpoints |
| numpy must be <2 in vcc-ctrgcn | mmcv-full 1.7.0 compiled against NumPy 1.x C API; 2.x breaks binary interface |
| fvcore must be installed in vcc-ctrgcn | PYSKL smp.py imports fvcore; missing from original install |
| CLIP cache at 1024-d (not 512-d) | mean+max pooling is 1024-d; 512-d projection is learned in Phase 3 MIL head, not at extraction time |
| cv2 not in vcc-main; use PIL for PNG loading | opencv-python is in vcc-skeleton only; PIL.Image.open().convert('RGB') is available and cleaner |
| CTR-GCN forward uses model.backbone(x) not model(x) | model.forward() includes cls_head logits; backbone() gives 256-d features needed for feature extraction |
| XD-Violence val split videos are in XD_TRAIN_ROOT (train/) not XD_TEST_ROOT | val is 15% holdout from training set; code routes both train and val to train folder |
| decord not available in vcc-skeleton; cv2.VideoCapture fallback works for XD-Violence mp4 | No code change needed; existing fallback handles XD-Violence mp4 decoding |
| conda run on Windows (cp950 locale) fails with UnicodeEncodeError on tqdm output | Cosmetic only; scripts succeed; use direct python exe path (C:/Anaconda/envs/vcc-main/python.exe) for scripts needing stdout capture |
| UCF-Crime has 172 sub-64-frame videos (max 63 frames) producing 0 snippets | Expected behavior; 1728/1900 are extractable; Phase 3 data loader must skip these |
| XD-Violence has 0 sub-64-frame videos (min 120 frames) | All 4754 videos will produce at least 1 snippet |
| Skeleton extraction bottleneck is 99.3% inference, 0.7% decode | rtmlib runs yolox_m (detection) + rtmpose-m (pose) per frame at ~46ms/frame (21.6 FPS on RTX 4090) |
| No viable optimization for skeleton extraction speed | rtmlib: no batch inference, no TensorRT backend; frame sampling destroys CTR-GCN motion signal |
| Proceed with Phase 3 using UCF-Crime while XD-Violence extraction runs | UCF-Crime features complete; XD-Violence ~5-8 days remaining for skeleton stage |
| Default pooling outperforms alternatives on XD-Violence | 2-person concat (-0.90% AP) and CLIP mean-only (-2.32% AP) both worse than default M-pool+global-pool |
| Abuse (B5) is hardest XD category for skeleton+CLIP fusion | AP=44.89% vs full test-set 71.92%; subtle interpersonal violence lacks distinctive motion/visual signatures |
| XD AP seed sensitivity higher than UCF | AP std=1.08% (3-seed) vs UCF AUC std=0.29%; precision-recall is more sensitive to score calibration than ROC-AUC |

### Critical Pitfalls to Watch

| ID | Risk | Phase | Prevention |
|----|------|-------|------------|
| C1 | Skeleton coordinate space mismatch (raw pixel coords vs normalized) | Phase 2 | Apply PreNormalize2D; assert coordinates in [-1, 1] |
| C2 | Temporal misalignment in variable-FPS videos | Phase 2 | Read FPS per video with cv2; map snippet boundaries to wall-clock seconds |
| C3 | Test set leakage into hyperparameter tuning | Phase 3-4 | Early stopping on val MIL loss only; test annotations loaded only in evaluate.py |
| C4 | Off-by-one in snippet-to-frame score expansion | Phase 4 | Encapsulate mapping in single utility; assert len(frame_scores)==len(frame_labels) |
| C5 | MIL training collapse to trivial solutions | Phase 3-4 | Monitor snippet score distribution variance; verify bag construction matches RTFM |
| M5 | TTA entropy collapse on normal-heavy batches | Phase 5 | SAR-style gradient filtering; analyze entropy distribution by anomaly duration |
| M6 | SAR rho ImageNet default too large for scalar output | Phase 5 | Grid search from 0.005; not from ImageNet default |
| M7 | Corruption TTA requires skeleton re-extraction for motion blur + JPEG | Phase 5 | Only noise and brightness conditions can reuse source skeleton cache |

### Todos

- [x] Verify XD-Violence zip access and extraction feasibility before Phase 2 planning — DONE: 3954 training videos extracted flat to E:\XD_Violence\train\ (Plan 02)
- [x] Confirm CTR-GCN weights (j/b/jm/bm) are available for download from PYSKL repo — DONE: all 4 files downloaded ~6.1MB each (Plan 03)
- [ ] Scan UCF-Crime and XD-Violence FPS distribution in Phase 2 Week 1 to size snippet window computation
- [ ] Phase 4d candidate: XD hyperparameter sweep (lr × k_topk grid, ~20 runs) + investigate RTFM repro gap (65.70% vs 77.81%) — deferred from Phase 4c, revisit after Phase 5 if timeline permits

### Blockers

None currently.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260419-079 | Fix 5 REAL code review findings from ML expert review | 2026-04-19 | 0999033 | [260419-079-fix-code-review-findings](./quick/260419-079-fix-code-review-findings/) |

---

## Session Continuity

**Stopped at:** Phase 4c complete (MISS-ACCEPTED), advancing to Phase 5
**To resume:** Phase 4c delivered 8-row XD ablation table (Gated Fusion AP=71.92% MISS-ACCEPTED). Hyperparameter sweep deferred as Phase 4d candidate (see Todos). Next: Phase 5 (TTA Infrastructure & Corruption Experiments) — plans already created (5 plans, 3 waves).

**Files of record:**

- `.planning/PROJECT.md` — project definition and key decisions
- `.planning/REQUIREMENTS.md` — 40 v1 requirements with traceability
- `.planning/ROADMAP.md` — 6-phase roadmap with success criteria
- `.planning/research/SUMMARY.md` — research findings and pitfall catalog
- `thesis_prd_v2.3.md` — authoritative PRD specification

---

*State initialized: 2026-03-31*

**Planned Phase:** 4c (XD-Violence Main Results) — 3 plans — 2026-04-26T16:30:47.698Z
