---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 11
current_plan: 4
status: complete
stopped_at: Phase 11 Plan 04 complete
last_updated: "2026-06-09T04:00:00.000Z"
last_activity: 2026-06-09
progress:
  total_phases: 13
  completed_phases: 13
  total_plans: 56
  completed_plans: 56
  percent: 100
---

# State: ViolenceCC

**Last updated:** 2026-05-30
**Session:** Phase 11 complete. All 4 plans executed. CGW '26 workshop paper draft complete (404 lines, 18 citations, 5 figures, 3 tables). Ready for Overleaf upload.

Last activity: 2026-06-09 - CODE↔PAPER MATCH REVIEW COMPLETE (quick 260609-cpr, commits 22ddb20→aa5120b, pushed to origin/main): full multi-agent audit of paper/main.tex vs code+results (82 findings, 0 false-positive); ALL HIGH(3)+MEDIUM(7)+LOW(8) resolved. HIGH: TTA Table-3 provenance committed + scripts/aggregate_tta_table.py regenerator (H1); entropy bound ≤0.004pp→<0.1pp ×3 (H2); unsupported category-adaptive gating Figure 7 dropped (H3). MEDIUM: PreNormalize2D image-center wording (M1), evaluated UCF n=254 disclosed (M4), dataset-dependent snippet duration UCF≈20s/~20frames vs XD≈2.7s/~3 (M3), skel-reliability gate functional form disclosed (M6), matched-seed complementarity re-analysis (M7), Table-3 TENT/SAR columns dropped (M5), FPS provenance 21.6 real/33.3 synthetic (M2). LOW batch (aa5120b): keypoint-confidence wording, SigLIP2 checkpoint names, LR warmup+cosine, bag T=32 (+frame-count T→T_f), param count→1,536, Giant figure label, stale tables_generated.tex banner. KEY EMPIRICAL CORRECTION: ran matched-seed visual-only baselines (queue m7_visual_seeds, 16 runs, ~2min/run) — the apparent SigLIP2-Base/XD fusion regression (−2.3) AND the "SO400M leads XD visual-only (77.2)" claim were both SINGLE-SEED ARTIFACTS; with 3 seeds both vanish (regression +0.05 p=0.97; SO400M 76.6≈Giant 76.8). Complementarity reframed honestly as small+consistent (gated≥visual in 8/8 backbone×dataset configs, mean +0.6pp, sign test p≈0.008), not large/per-cell-significant; SO400M leads XD only under gated fusion (78.7, robust). Every medium/low edit was adversarially pre-checked by a skeptic workflow BEFORE applying (caught 2 dangling LaTeX refs, a wrong M2 rationale, a stale 81.1/2.5→81.2/2.6 number a prior edit introduced, and a T-symbol collision). Tables 1/2 Visual-Only rows now 3-seed mean±std; backbone-comparison + TTA figures regenerated. Paper rebuilds clean (10pp, 0 undefined refs, 0 errors); headlines UCF 82.5% AUC / XD 78.7% AP unchanged throughout. Report w/ resolution table: .planning/CODE-PAPER-REVIEW-2026-06-07.md; memory: project_code_paper_review_2026-06-09. PREVIOUS: 2026-06-07 - PAPER TTA SECTION REWRITTEN (commit 12cd95f): replaced the wrong BN-vs-LN negative finding + the "+0.6% CLIP SAR" artifact with the VALIDATED disc_reweight positive result. Table 3 now 3-seed mean±std (entropy TENT/SAR ≈0, ≤0.004pp; Ours +1.21pp mean over 4 backbones, all-positive, up to +13.9pp SO400M Gaussian); new §3 method subsection (sec:disc)+eq; abstract/§1/§2.3/§4/§5/conclusion rewritten with honest disclosures (entropy≈0 is EMPIRICAL not monotone-theory; per-condition base over-route on ONE seed; gaussian gain = routing to UNTOUCHED clean skeleton, bounded by skeleton ceiling; transductive + clean-ref train≡test); Fig 2 regenerated (3-seed Source-vs-Ours, scripts/generate_pub_figures.py). VALIDATED before editing (user: "serious academic work, confirm valid+real first"): 6-auditor adversarial review wf_446298cf (leakage-free, fair w=1≡source byte-identical, mechanism real not artifact) + production reproduction 11/11 exact+deterministic + 3-SEED sweep (all 4 bb positive on all 3 seeds {42,123,2024}; std bands all >0; mean +1.21 > s42-only +0.83; the s42 base −3.2 over-route was a SINGLE-SEED quirk, base averages +1.50) + clean-TRAIN-reference equivalent (oracle concern defused). PDF rebuilt clean (10 pages, 0 undefined refs). ⚠ NOTE: paper grew 9→10pp — may exceed CGW workshop page limit; can trim (drop Fig 2, tighten §4) if needed. Draft+validation record: .planning/PAPER-TTA-REVISION-DRAFT.md + HANDOVER §10-12. PREVIOUS: 2026-06-07 - Completed quick task 260607-42h (commit def88d5): added `--method disc_reweight` (R1 discriminative-reliability routing) to evaluate_tta.py + new src/tta/disc_reweight.py + unit tests (25 pass). Production VERIFIED to reproduce the reference R1 (clip gaussian_5 57.70→62.53, +4.83). This consolidates the TTA-boost investigation: after the original "+0.6% CLIP SAR" was shown to be a dropout artifact (entropy TTA ≈0) and held-out shrunk-CORAL was a no-go (rank-disruptive, LOCO-video −1.62, 0/4 positive; val-C infeasible — frame labels exist only on test), a 6-strategy parallel search found R1 — label-free, tuning-free, +0.83pp mean over 4 backbones, all-positive, driven by Gaussian/VL-collapse recovery (up to +13.9pp/condition) by routing the fusion to the corruption-robust skeleton stream when the VL stream's solo-score-spread collapses (a discriminative, not distributional, signal). Caveat: gains concentrated on Gaussian; base over-routes at high-sev Gaussian (−3.2, intrinsic). Paper/canonical results UNTOUCHED — the paper rewrite (corrected Table 3 + §4.6/§2.3 mechanism, delete "+0.6% CLIP SAR") is the NEXT step, to be drafted for user review BEFORE editing main.tex. Full record: .planning/HANDOVER-tta-investigation-2026-06-06.md §10-11. PREVIOUS: 2026-06-06 - Completed quick task 260606-3hc (commit 1ed2d16): added continual-online TTA protocol. CONTEXT: the corrected (dropout-fixed) episodic re-run showed TTA does ~0.000pp for all backbones — but that was an artifact of the episodic+online+chunked protocol on UCF's short clips (median 3 snippets; 98.4% single-chunk), NOT evidence about LayerNorm. User chose Option 2: fix the protocol and re-run a VALID test. Continual-online now adapts across the whole corruption stream (sanity-confirmed it bites: +0.24/+0.25pp on one CLIP condition vs +0.000 episodic). Full continual grid (4 backbones × source/tent/sar × 20, symmetric fixed config) running to scratch results/_tta_rerun_continual/. paper/main.tex + canonical results/tta* still UNTOUCHED — user wants to review the continual numbers before ANY paper edit. Also note: corrected episodic numbers showed source-only baselines ~2pp HIGHER than the paper (dropout was depressing them); §4.6 BN-vs-LN interpretation is unsupported and must be revisited. PREVIOUS: 2026-06-04 - Completed quick task 260604-w2a (commit 83b8927): fixed the TTA dropout-in-train-mode bug (configure_model disables ALL nn.Dropout; +manual_seed; +2 determinism tests). TTA scores now deterministic. Decision in progress: B+C — re-running the corrected TTA grid (4 backbones, symmetric fixed config = no per-backbone test-set hyperparam selection) to a SCRATCH dir; canonical results/tta* and paper/main.tex deliberately UNTOUCHED pending user review of the new Table-3 numbers (user wants to discuss before any paper change). PREVIOUS: 2026-06-04 - Completed quick task 260604-vfi (commit c163eb6): aligned paper §3.5 loss equations with mil_loss.py — ranking max→mean-of-top-k, sparsity L1-sum→RTFM L2-column-norm (+RTFM cite); smoothness & all reported numbers unchanged (transparency fix, no code/number change); PDF recompiled clean. Came out of a fresh 2026-06-04 multi-agent code+thesis review (self-reviewed: the earlier "254/290 CRITICAL" was downgraded to a benign, already-disclosed <64-frame exclusion; real open items now = TTA dropout-in-train-mode bug + a few methodology over-claims). PREVIOUS: 2026-06-02 - Stage 3 COMPLETE (quick 260602-339, commits 6599414+2992ce5): XD λ=0 numbers propagated into the CGW '26 paper. results-index.csv (29 xd_* rows) + phase10 CSVs + tables_generated.tex + the 2 XD figures regenerated from canonical via new scripts/_update_xd_index_lam0.py. main.tex: Table 2 (gated SO400M 78.7±0.9 leads; Giant now the ±2.8 outlier; GF Mean-Only SO400M 79.9, brushes 80% gate), abstract 74.7 Base→78.7 SO400M, §4.3/4.4/5/6/Conclusion prose (seed-variance narrative inverts), dataset-dependent λ₂ note (8e-4 UCF / 0 XD; §4.2 sec:impl) + UCF disclosure footnote (≤0.13pp), author "Universiy" typo fix. UCF Table 1 FROZEN (user decision: disclose-and-keep, no retrain). Recompiles clean (9 pp, 0 undefined refs). Independent 5-agent verification PASSED (Table 2 re-derived from canonical, inline=tables_generated, prose consistent, UCF byte-frozen vs 9eb23e0, LaTeX internally consistent). The full paper-review saga (C1/C2/H1/H2/H3/H4 + smoothness axis-fix + dataset-dependent λ) is now resolved & propagated; headlines: UCF 82.5% AUC, XD 78.7% AP.

---

## Project Reference

**Core value:** A working dual-modal (Skeleton + CLIP) fusion pipeline that produces reproducible frame-level AUC/AP numbers on UCF-Crime and XD-Violence, with complete ablation analysis and TTA experiments.

**Milestone:** 1 — Initial Thesis Results
**Timeline:** 12 weeks (started 2026-03-31, target completion 2026-06-23)

---

## Current Position

Phase: 11 (thesis-manuscript) — COMPLETE
Plan: 4 of 4
**Current phase:** 11
**Current plan:** 4
**Status:** Complete

**Progress:**

[██████████] 100%
Phase 11 [██████████] 100%  Thesis Manuscript (4/4 plans executed)

---

## Performance Metrics

Targets from PRD v2.3:

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
| Phase 07 P01 | 4min | 2 tasks | 4 files |
| Phase 07 P02 | 7min | 2 tasks | 4 files |
| Phase 07 P03 | 240min | 1 tasks | 4 files |
| Phase 07 P04 | 8min | 2 tasks | 3 files |
| Phase 09 P04 | 3min | 2 tasks | 1 files |
| Phase 11 P02 | 515 | 2 tasks | 5 files |
| Phase 11 P03 | 7min | 2 tasks | 7 files |
| Phase 11 P04 | 13min | 2 tasks | 3 files |

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
| LR format uses split/abs instead of lstrip | _fmt_lr() uses split('e') + abs(int(exp)) to avoid lstrip("0") leading-zero bugs in exponent portion |
| RTFM 12.11pp AP gap is training regime not eval bug | 3 HIGH-impact differences (10x LR, 2x features, 100x margin scaling) explain gap; confirmed by 4 diagnostics |
| XD-Violence benefits from tuning (+3.72pp), UCF does not (+0.14pp) | 198-config sweep across both datasets; XD winner lr=1e-3/k=2 (AP=74.69%); UCF hyperparameter-insensitive |
| Decimal LR encoding uses 'p' separator | 6.5e-4 encoded as '6p5e4' in run_name via _fmt_lr(); avoids dots in filesystem paths |
| Sweep grid expanded from 20 to 99 configs | 3 progressive extension rounds: base 20, +18, +28, +33 chasing peak at grid edges |

### Roadmap Evolution

- Phase 8 added: SigLIP2 Backbone Comparison — swap CLIP ViT-B/16 with SigLIP2 Giant (google/siglip2-giant-opt-patch16-384), re-extract features, run identical ablations for thesis comparison
- Phase 9 added: SigLIP2-SO400M Backbone Comparison — swap CLIP ViT-B/16 with SigLIP2 SO400M (google/siglip2-so400m-patch16-256), re-extract features, run identical ablation matrix, compare against both CLIP and SigLIP2 ViT-B/16-256
- Phase 11 added: Thesis Manuscript — full master's thesis document targeting workshop venue, integrating all experimental results

### Roadmap Evolution

- Phase 7 added: XD-Violence Hyperparameter Sweep (promoted from Phase 4d candidate, 2026-05-01)

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
- [x] Phase 4d candidate: XD hyperparameter sweep — promoted to Phase 7 (2026-05-01)

### Blockers

None currently.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260419-079 | Fix 5 REAL code review findings from ML expert review | 2026-04-19 | 0999033 | [260419-079-fix-code-review-findings](./quick/260419-079-fix-code-review-findings/) |
| 260503-nl6 | Performance benchmark for all 5 model variants (params, FLOPs, latency, memory) | 2026-05-03 | caaad02 | [260503-nl6-create-comprehensive-performance-benchma](./quick/260503-nl6-create-comprehensive-performance-benchma/) |
| 260503-ow4 | Backbone extraction benchmark — CLIP, RTMPose, CTR-GCN, I3D cross-env pipeline cost | 2026-05-03 | 83883b2 | [260503-ow4-backbone-extraction-benchmark-clip-vit-b](./quick/260503-ow4-backbone-extraction-benchmark-clip-vit-b/) |
| 260506-3uu | XD-Violence presentation materials — markdown reports (EN + ZH-TW) with 20 charts | 2026-05-06 | d3e4e48 | [260506-3uu-xd-violence-presentation-materials-markd](./quick/260506-3uu-xd-violence-presentation-materials-markd/) |
| 260531-mcp | Add project-scoped Overleaf MCP config (.mcp.json, env-var placeholders) | 2026-05-31 | 42d368a | — (inline /gsd:fast) |
| 260601-gap | Reconcile paper main.tex methodology with actual configs/results (text→code fixes from code review) | 2026-06-01 | a12b64e | [260601-gap-reconcile-paper-main-tex-methodology-and](./quick/260601-gap-reconcile-paper-main-tex-methodology-and/) |
| 260601-c1f | Reframe §4.1 to remove false no-test-leakage claim (C1 honest fix) | 2026-06-01 | 1866cb3 | — (inline /gsd:fast) |
| 260601-jtb | Fix H1 UCF eval truncation: full-length recompute script + comparison + eval-code patch (paper numbers NOT yet updated — pending review) | 2026-06-01 | 7bdb3c4 | [260601-jtb-fix-h1-ucf-eval-frame-grid-truncation-fu](./quick/260601-jtb-fix-h1-ucf-eval-frame-grid-truncation-fu/) |
| 260601-kjm | Propagate H1 full-length UCF numbers into canonical artifacts + regenerated tables/figures + main.tex (UCF headline 83.3→82.5; XD/TTA unchanged; all qualitative claims survive) | 2026-06-01 | 4c352b8 | [260601-kjm-propagate-h1-full-length-ucf-metrics-int](./quick/260601-kjm-propagate-h1-full-length-ucf-metrics-int/) |
| 260601-mry | H2/H3 Direction A: align gated (residual+vector gate) & late-fusion (score-avg) equations + Discussion with implemented code (9 edits, editorial, no re-run) | 2026-06-01 | ced266f | [260601-mry-h2-h3-direction-a-rewrite-gated-late-fus](./quick/260601-mry-h2-h3-direction-a-rewrite-gated-late-fus/) |
| 260601-o55 | Smoothness-axis fix (mil_loss dim1) + regression test; measured on headline UCF: AUC Δ−0.13pp (negligible), AP Δ−1.23pp (sensitive). Fix committed; XD-AP exposure not yet measured | 2026-06-01 | f89910b | [260601-o55-measure-smoothness-axis-fix-impact-on-he](./quick/260601-o55-measure-smoothness-axis-fix-impact-on-he/) |
| 260601-okz | Measure smoothness fix on XD gated (Base+SO400M s42): MATERIAL & divergent — Base AP +0.76pp, SO400M AP −3.80pp, s42 ordering flips. XD Table 2 needs a decision (retrain / disable-smoothness / disclose); paper unchanged | 2026-06-01 | (measure only) | [260601-okz-measure-smoothness-fix-on-xd-gated-headl](./quick/260601-okz-measure-smoothness-fix-on-xd-gated-headl/) |
| 260601-or4 | Local LaTeX env (MiKTeX 25.12 + Strawberry Perl + latexmk 4.88) to compile/view paper/main.tex locally; build_paper.ps1 → 9-page main.pdf, BibTeX refs resolved, idempotent. latexmk needed Perl; used --enable-installer for CTAN auto-install | 2026-06-01 | 169c2d3 | [260601-or4-local-latex-environment-miktex-latexmk-f](./quick/260601-or4-local-latex-environment-miktex-latexmk-f/) |
| 260601-ltx | CLAUDE.md convention: after editing any paper LaTeX source, recompile + wipe artifacts via `build_paper.ps1 -Clean` | 2026-06-01 | 91786b8 | — (inline /gsd:fast) |
| 260601-au2 | Add second \author block (professor) template to paper/main.tex — `[Professor Name]`/`[professor.email…]` placeholders, NYCU default; recompiles clean (9-page PDF). User to fill in details | 2026-06-01 | ce28d36 | — (inline /gsd:fast) |
| 260601-rww | λ=0 adoption STAGE 1: 43 fusion configs→lam_smooth=0 + 22 UCF configs get snippet_boundaries_dir (full-length eval); retrain_lam0.py (resumable, 58 runs, dry-run verified); 2 i3d configs left at 8e-4. STAGE 2 (user runs ~58-run batch) + STAGE 3 (propagate to tables/abstract/figures, drop smoothness from paper loss) PENDING | 2026-06-01 | 9fb04fa | [260601-rww-stage-1-of-lambda-0-adoption-set-lam-smo](./quick/260601-rww-stage-1-of-lambda-0-adoption-set-lam-smo/) |
| 260604-vfi | Align paper §3.5 loss equations with mil_loss.py: ranking max→mean-of-top-k (Eq.6), sparsity L1-sum→RTFM L2-column-norm (1/T·Σₜ‖aₜ‖₂, Eq.7) + RTFM cite; smoothness & all numbers unchanged (transparency-only, code untouched). PDF recompiled clean (9pp). From the 2026-06-04 self-reviewed code+thesis review | 2026-06-04 | c163eb6 | [260604-vfi-align-paper-loss-equations-with-mil-loss](./quick/260604-vfi-align-paper-loss-equations-with-mil-loss/) |
| 260604-w2a | Fix TTA dropout-in-train-mode bug: configure_model now disables ALL nn.Dropout (MILHead head.mlp.2/.5 were left in train mode → stochastic TTA scores; measured ~1.07pp per-condition AUC std, 0.24pp on the 20-cond Table-3 mean) + manual_seed in run_tta_evaluation; 2 determinism regression tests (10 pass). Verified deterministic (52.233184% ×2 identical). Code-only — canonical TTA results + paper UNCHANGED. B+C corrected grid re-run + paper update PENDING user review of new numbers | 2026-06-04 | 83b8927 | [260604-w2a-fix-tta-dropout-bug-disable-all-nn-dropo](./quick/260604-w2a-fix-tta-dropout-bug-disable-all-nn-dropo/) |
| 260606-3hc | Add continual-online TTA protocol (--protocol {episodic,continual}; default episodic, non-breaking). Continual = ONE stream-level reset then adapt across the whole corruption-condition test stream (TENT/SAR native -C setup), fixing the episodic+short-clip inertness (98.4% of UCF test videos are ≤32 snippets → episodic adaptation never reached the scored output). +unit test (24 pass). Sanity: continual CLIP gaussian sev3 TENT +0.24pp / SAR +0.25pp (episodic gave +0.000 → adaptation now bites, no collapse). User chose Option 2 (fix protocol + re-run). Canonical/paper UNCHANGED; full continual grid re-run in progress, paper change pending user review | 2026-06-06 | 1ed2d16 | [260606-3hc-add-continual-online-tta-protocol-flag-t](./quick/260606-3hc-add-continual-online-tta-protocol-flag-t/) |
| 260607-42h | Add `--method disc_reweight` (R1 discriminative-reliability routing) to evaluate_tta.py — new src/tta/disc_reweight.py + 2-pass transductive dispatch + unit tests (25 pass). Label-free/tuning-free: routes the GatedFusion to the corruption-robust skeleton stream (scales p_clip by w after ln_clip) when the VL stream's solo-score-spread collapses; w=1−(1−w_vl)·skel_rel. Production VERIFIED to reproduce R1 (clip gaussian_5 57.70→62.53, +4.83). Full result: +0.83pp mean over 4 backbones, all-positive, Gaussian recovery up to +13.9pp (results/_coral_derisk/r1full_*). Code-only — paper/canonical UNTOUCHED; paper rewrite is next (draft for review first) | 2026-06-07 | def88d5 | [260607-42h-tta-disc-reweight](./quick/260607-42h-tta-disc-reweight/) |
| 260607-pap | Rewrite paper TTA section (follow-on to 260607-42h): replace the wrong BN-vs-LN negative finding + the "+0.6% CLIP SAR" artifact with the VALIDATED disc_reweight result. Table 3 → 3-seed mean±std (entropy TENT/SAR ≈0; Ours +1.21pp mean, all-4-backbones positive, up to +13.9pp SO400M Gaussian); new §3 method subsection (sec:disc)+eq; abstract/§1/§2.3/§4/§5/conclusion rewritten + Fig 2 regenerated; all 8 audit-mandated disclosures applied (empirical-entropy, per-condition base over-route on 1 seed, skeleton-routing/ceiling, transductive, clean-ref train≡test). VALIDATED before editing: 6-auditor adversarial review (wf_446298cf) + production repro 11/11 exact + 3-seed sweep (all 4 bb positive on all 3 seeds) + clean-train-ref equivalent. PDF clean (⚠ 10pp, was 9pp — page-limit decision pending). Done inline (not a gsd:quick executor) given high-stakes exact-number LaTeX | 2026-06-07 | 12cd95f | — (inline) |
| 260602-339 | Stage 3: propagate XD λ=0 numbers into CGW '26 paper — Table 2 (gated SO400M 78.7 leads, Giant ±2.8 outlier, GF Mean-Only SO400M 79.9), abstract 74.7→78.7 SO400M, §4.3/4.4/5/6/Conclusion prose (variance narrative inverts), dataset-dependent λ₂ note (8e-4 UCF/0 XD, sec:impl) + UCF disclosure footnote, typo fix; regen index/CSVs/tables/2 figures from canonical via _update_xd_index_lam0.py; UCF frozen (disclose-and-keep). Recompiles clean; independent 5-agent verify PASSED | 2026-06-02 | 2992ce5 | [260602-339-stage3-xd-lam0-paper-propagation](./quick/260602-339-stage3-xd-lam0-paper-propagation/) |
| 260609-cpr | Code↔paper match review COMPLETE — multi-agent audit (82 findings, 0 FP); ALL HIGH(3)+MEDIUM(7)+LOW(8) resolved. Matched-seed runs (m7_visual_seeds, 16) overturned 2 single-seed artifacts (no fusion regression; "SO400M leads XD-visual" was noise); complementarity reframed small+consistent (8/8, sign p≈0.008). Each edit adversarially pre-checked. Tables 1/2 Visual-Only→3-seed; 2 figures regenerated; Table-3 TENT/SAR cols dropped. Headlines UCF 82.5/XD 78.7 intact; PDF clean (10pp) | 2026-06-09 | 22ddb20→aa5120b | [260609-cpr-code-paper-match-review](./quick/260609-cpr-code-paper-match-review/) |

---

## Session Continuity

**Stopped at:** Phase 11 Plan 04 complete
**To resume:** Phase 11 complete. CGW '26 workshop paper draft at paper/main.tex (404 lines, 18 citations, 5 figures, 3 tables). Ready for Overleaf upload and compilation. Submit to advisor by June 1 deadline.

**Files of record:**

- `.planning/PROJECT.md` — project definition and key decisions
- `.planning/REQUIREMENTS.md` — 40 v1 requirements with traceability
- `.planning/ROADMAP.md` — 6-phase roadmap with success criteria
- `.planning/research/SUMMARY.md` — research findings and pitfall catalog
- `thesis_prd_v2.3.md` — authoritative PRD specification

---

*State initialized: 2026-03-31*

**Planned Phase:** 6 (Analysis & Visualization) — 2 plans — 2026-05-02T12:36:57.713Z
