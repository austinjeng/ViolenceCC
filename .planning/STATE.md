---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 12
current_plan: 3
status: complete
stopped_at: Phase 12 Plan 03 complete (final verification PASS)
last_updated: "2026-06-20T22:43:11.000Z"
last_activity: 2026-06-21
progress:
  total_phases: 14
  completed_phases: 14
  total_plans: 59
  completed_plans: 58
  percent: 98
---

# State: ViolenceCC

**Last updated:** 2026-05-30
**Session:** Phase 11 complete. All 4 plans executed. CGW '26 workshop paper draft complete (404 lines, 18 citations, 5 figures, 3 tables). Ready for Overleaf upload.

Last activity: 2026-06-22 - Completed quick task 260622-ukd: fixed HIGH review finding T3-1 (removed fabricated Light-WVAD XD-Violence AP)

---

## Project Reference

**Core value:** A working dual-modal (Skeleton + CLIP) fusion pipeline that produces reproducible frame-level AUC/AP numbers on UCF-Crime and XD-Violence, with complete ablation analysis and TTA experiments.

**Milestone:** 1 — Initial Thesis Results
**Timeline:** 12 weeks (started 2026-03-31, target completion 2026-06-23)

---

## Current Position

Phase: 12 (sota-comparison-and-positioning) — COMPLETE
Plan: 3 of 3
**Current phase:** 12
**Current plan:** 3
**Status:** Phase 12 COMPLETE (3/3 plans). Plan 03 final verification PASSED on all four audits (12-VERIFICATION.md): clean build exit 0 / 11 pages / no undefined citations or references; every cited UCF/XD number traces verbatim to 12-RESEARCH-sota.md (0 untraceable, conflicting re-verify numbers % RE-VERIFY-flagged); overclaim scan 0 disallowed hits; headline anchors + Tables 1-3 byte-identical to pre-phase baseline 16f70fd. No paper source patched (report-only gate). Student manual re-checks enumerated: CLIP-TSA 82.19, MGFN 79.19 (I3D), RTFM 77.81 (I3D), Light-WVAD attribution. Post-completion code-review gate (12-REVIEW.md, standard depth, 3 LaTeX/bib files): 0 critical / 2 warning / 2 info. WR-01 (self-contradicting tab:comparison caption) + IN-01 (empty LAVAD superscript) fixed in b78d0bd (paper rebuilt clean, 11pp, headlines intact); WR-02 + IN-02 (PI-VAD/DSANet bib type + author lists) deferred to the 12-VERIFICATION.md camera-ready re-verify checklist (items 16-17).

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
| Phase 12 P01 | ~14min | 2 tasks | 2 files |
| Phase 12 P02 | ~13min | 3 tasks | 2 files |
| Phase 12 P03 | ~9min | 1 tasks | 1 files |

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
| Never compare a 3-seed metric to a 1-seed baseline (esp. XD) | XD visual-only AP is seed-unstable (std ±1.5–2.2 vs UCF ±0.1–0.5). 2026-06-09 matched-seed runs (260609-cpr) showed the apparent "SigLIP2-Base/XD fusion regression" (−2.3) and "SO400M leads XD visual-only" were BOTH single-seed (s42) artifacts that vanish at 3 seeds. Always replicate both sides before claiming a margin |
| Skeleton complementarity is small + consistent, not large | gated ≥ visual-only in 8/8 backbone×dataset configs (mean +0.6pp, sign test p≈0.008), with NO per-cell significance at n=3; largest on XD (CLIP +1.9, SO400M +2.1). Paper claims/tables must not overstate it; SO400M leads XD only under gated fusion (78.7, robust) |
| Adversarially pre-check exact-number LaTeX/paper edits before applying | 2026-06-09 skeptic workflows caught, pre-edit: 2 dangling \ref{tab:tta}, a stale 81.1→81.2 / 2.5→2.6pp number a prior edit introduced, a wrong "21.6 FPS is unbacked" rationale (it is a real 02-UAT.md measurement), and a T-symbol collision (frame-count vs bag) — none shipped |
| SOTA comparison fragment = standalone, manual-[N] cites, zero references.bib dep (Phase 12 P01) | paper/sota_comparison_full.tex is the full-treatment thesis SOTA artifact (NOT \input by main.tex; main.tex gets a condensed table in Plan 02). Uses \documentclass{standalone}+varwidth and manual bracketed labels so it compiles in isolation with no bib → no `??`. FRAGMENT BODY BEGIN/END markers delimit the lift-into-thesis content. Attribution guardrails baked in: MGFN XD 79.19 (I3D, not 80.11), CLIP-TSA 82.19, EventVAD 64.04 AP / LAVAD 62.01 AP, STPrompt/FDPN XD N/A, Sultani XD omitted (Wu 2020), HyperVD/Ghadiya/PiercingEye labeled audio. 15 inline % RE-VERIFY flags. Zero overclaim (only "we do not claim SOTA" negation). Headlines 82.5/78.7 + all single-stream anchors intact. .gitignore extended for the new fragment's PDF |
| Phase 12 verification gate PASSED — phase COMPLETE (Phase 12 P03) | 12-VERIFICATION.md records all four audits PASS: (1) clean build `build_paper.ps1 -Clean` exit 0, 11 pages, no undefined citations/references, 6 new \cite keys resolve in main.bbl, standalone sota_comparison_full.tex compiles exit 0; (2) number-traceability — every cited UCF/XD value in main.tex (tab:comparison + §2 backfill + §6 prose) AND sota_comparison_full.tex appears verbatim in 12-RESEARCH-sota.md (0 untraceable), conflicting re-verify numbers (CLIP-TSA 82.19, MGFN 79.19 I3D) % RE-VERIFY-flagged; (3) overclaim scan 0 disallowed hits (phase-12 main.tex additions clean; the 2 pre-existing main.tex:265/:429 "outperforms" are internal gated-vs-late ablation, blame 33591ac, outside the phase-12 diff; standalone hits are non-rendered labels/paths or the 2 explicit "we do not claim SOTA" negations); (4) headline integrity — `git diff 16f70fd..HEAD` shows ONLY additive §2-backfill + new-table changes, Tables 1-3 absent from the diff (result cells byte-identical), references.bib +59/−0, anchors 82.5/78.7/68.8/40.8/81.2/74.6/82.4/76.8 all present. Report-only gate: NO paper source patched. Student manual re-checks before camera-ready: CLIP-TSA 82.19, MGFN 79.19(I3D), RTFM 77.81(I3D), Light-WVAD attribution (Wang/Zhou/Guan) |
| FULL condensed table chosen over mini-table fallback (Phase 12 P02) | Baseline main.tex = 11 pages; adding the 10-row condensed comparison table (tab:comparison, two-column table*) in Section 6 kept it at 11 pages — no overflow, so the documented 3-4-row mini-table fallback was NOT needed. table* (not single-column table) gives the Setting column room and matches the existing Tables 1/2 house style. Setting column mandatory; This-work bolded 82.5/78.7; Sultani XD="---" (no 2018 XD number); MGFN XD=79.19(I3D) + CLIP-TSA 82.19 carry % RE-VERIFY flags; no STPrompt/FDPN/audio-visual rows. Table label renamed tab:sota→tab:comparison to avoid a false-positive \bSOTA\b overclaim-grep hit on the label substring. Build exit 0, no undefined citations/refs, zero overclaim tokens in added prose. HUMAN-VERIFY APPROVED (11 pages within venue limit). Commits 2885a9a (backfill+bib) + bdf8b72 (table). NOTE for Plan 03 audit: the two "outperforms" hits at main.tex:265/:429 are PRE-EXISTING internal gated-vs-late-fusion ablation claims (last touched by 33591ac, not this plan) — known-allowed, not SOTA overclaims |

### Roadmap Evolution

- Phase 8 added: SigLIP2 Backbone Comparison — swap CLIP ViT-B/16 with SigLIP2 Giant (google/siglip2-giant-opt-patch16-384), re-extract features, run identical ablations for thesis comparison
- Phase 9 added: SigLIP2-SO400M Backbone Comparison — swap CLIP ViT-B/16 with SigLIP2 SO400M (google/siglip2-so400m-patch16-256), re-extract features, run identical ablation matrix, compare against both CLIP and SigLIP2 ViT-B/16-256
- Phase 11 added: Thesis Manuscript — full master's thesis document targeting workshop venue, integrating all experimental results
- Phase 12 added (2026-06-21): SOTA Comparison and Positioning — post-milestone phase added after professor review ("thesis lacks SOTA comparison"). Zero-GPU writing/analysis: verified published-numbers comparison table + fair-subset table + positioning prose + §2 Related-Work backfill (thesis) and a condensed table (CGW '26 paper), framed orthogonal-contribution + fair-subset-competitiveness, no SOTA overclaim. Grounded in a 40-agent verified-SOTA research artifact (.planning/phases/12-.../12-RESEARCH-sota.md, 31/34 methods primary-source-verified). CONTEXT seeded; ready to plan.

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
| 260610-2s1 | Fix M1 (from 2026-06-09 full audit): main.tex:217 reworded — Visual Only added to the 3-seed mean±std reporting sentence ("Gated Fusion and Visual Only configurations"), true single-seed variants enumerated (Late Fusion, GF 2-Person, GF Mean-Only, Skeleton Only). Resolves prose↔caption/data contradiction (Visual Only is 3-seed per captions :225/:244/:281 + cells + clip_only s42/123/2024 runs). Prose-only, no numeric change; PDF rebuilds clean (10pp, 0 errors/undefined). M2 (TENT/SAR single-seed→3-seed) next | 2026-06-09 | 48cee29 | [260610-2s1-fix-m1-include-visual-only-in-the-multi-](./quick/260610-2s1-fix-m1-include-visual-only-in-the-multi-/) |
| 260610-4pk | Knock out the 4 LOW audit items (code/doc hygiene; non-paper I3D/RTFM path or comments): (1) i3d_dataset.py skips '#' split-file lines; (2) _resample_T uses the global RNG not fixed default_rng(0) so sub-T sampling varies per epoch/crop; (3) rtfm_i3d.py docstring corrected (no L2-norm FM head — LN+sigmoid MILHead); (4) evaluate.py scoped the gt.npy 'bit-identical' comment to the xd_i3d stride-16 path + documented the xd-fusion ~0.74% trailing truncation. py_compile OK, 48 tests pass. NOTE: 2 PRE-EXISTING test failures (test_split_seed_reproducibility, test_no_test_split_access — a leakage-guard flagging legit eval test-split loads) confirmed red on HEAD before edits; unrelated, left for Austin | 2026-06-09 | ca4802a | [260610-4pk-knock-out-low-audit-items-i3d-dataset-co](./quick/260610-4pk-knock-out-low-audit-items-i3d-dataset-co/) |
| 260610-4cj | Fix M3 (from 2026-06-09 full audit): make the UCF 82.5% AUC headline reproducible from git alone (Option A — user-chosen). The full-length headline previously needed off-repo per-video boundary JSONs at E:/snippets/ucf; committed config_snapshot lacked snippet_boundaries_dir → fresh evaluate.py gave the truncated 83.2%. Distilled per-video total_frames into a 45KB committed manifest (data/ucf_total_frames.json, 1900 vids) via new scripts/build_ucf_frames_manifest.py; wired a backward-safe fallback into src/evaluate.py + recompute_fulllength_ucf.py (boundaries-dir JSON still wins when set). VERIFIED two ways on giant-s42 with a nonexistent boundaries dir: recompute gate PASS new_auc=0.824904 (d=+4e-6); fresh evaluate.py writes auc=0.824904 n_frames=1097050 (headline) not truncated 0.8323/1010560. No canonical artifact touched; no paper edit. ALL 3 audit MEDIUMs now resolved. (Optional follow-up: symmetric XD manifest for its ~0.74% trailing truncation, LOW) | 2026-06-09 | 4ddda56 | [260610-4cj-m3-commit-ucf-total-frames-manifest-wire](./quick/260610-4cj-m3-commit-ucf-total-frames-manifest-wire/) |
| 260610-46n | Fix M2 (from 2026-06-09 full audit): make the TENT/SAR negative result a TRUE 3-seed mean so main.tex:325 ("All TTA results are means over three seeds {42,123,2024}") is honest. Ran the identical committed continual protocol (run_tta_evaluation protocol=continual, TENT lr1e-3, SAR lr1e-3 ρ0.05) on s123+s2024 source ckpts × 4 backbones × 20 conditions (477 runs, 42min; corrupted caches seed-independent → no re-extraction). 3-seed mean ΔTENT/ΔSAR: CLIP +0.021/+0.024, Base −0.082/−0.077, SO400M −0.050/−0.051, Giant +0.011/+0.012 → worst |Δ|=0.082pp < 0.1pp, claim HOLDS. NO paper edit needed (:325/:327 now true). New scripts/run_tta_seeds_m2.py (regenerator) + summary_3seed.json (committed); aggregate_tta_table.py now 3-seed (Table 3 reproduces unchanged). Bonus: 3-seed continual source 63.71/57.01/58.87/62.83 reconciles with Table-3 Source-Only 63.7/57.0/58.9/62.8 (s42-only was the outlier). NEXT: discuss M3 (UCF headline repro/provenance gap) | 2026-06-09 | a5e3f73 | [260610-46n-m2-run-tent-sar-continual-tta-on-s123-s2](./quick/260610-46n-m2-run-tent-sar-continual-tta-on-s123-s2/) |
| 260610-aqm | Add Pri-1 3-seed ablation queue (REVIEW-2026-06-10 Batch A): new `QUEUES["pri1_ablations_seeds"]` in run_ablations.py = 52 RunSpecs (26 single-seed ablation configs × seeds {123,2024}; Late Fusion/GF 2-Person/GF Mean-Only/Skeleton Only × 4 bb × 2 datasets, cloned verbatim from phase4/4c/8/9/10 specs) so the load-bearing single-seed numbers (UCF 83.0 GF Mean-Only, XD 79.9, skeleton-only, Late Fusion, GF 2-Person) can become 3-seed. `--dry-run` validated (52 names: 26 _s123 + 26 _s2024, all resolve); stale queue-count pin 266→334 (test_run_ablations.py now 17 passed). GPU NOT launched — user runs `python scripts/run_ablations.py --queue pri1_ablations_seeds` in a visible terminal (~2-3 GPU-h, resumable via .done). Batches B (suite-green: C1/C2/C3 + TTA pin + scanner) and C (paper P1-P7) pending. | 2026-06-10 | b315108 | [260610-aqm-add-pri-1-3-seed-ablation-queue-pri1-abl](./quick/260610-aqm-add-pri-1-3-seed-ablation-queue-pri1-abl/) |
| 260610-b6p | Make test suite GREEN (REVIEW-2026-06-10 Batch B): 321 passed / 0 failed (was 6 failed). C1 — renamed ALL 10 synthetic_eval.py UCF fixture ids to Synth* (6 collided with real UCF ids in the M3 manifest data/ucf_total_frames.json → hijacked n_frames via evaluate.py:330 → broke evaluate_cli ×3, regression from 4ddda56; category from annotation col so label-safe). C2 — src/data/loaders.py i3d val loader shuffle False→True (convention; mirrors 0999033; latent, affects 2 xd_i3d baseline rows' selection). C3a — encoded XD_TRAIN_EXCLUSIONS in create_splits.py + comment header so --verify regenerates xd_train.txt byte-identically (PASSED; committed split untouched). C3b — scoped test_no_test_split_access leakage scanner to skip src/eval+src/tta (legit test-split loaders). TTA pin 500→680. | 2026-06-10 | cb625fc | [260610-b6p-make-test-suite-green-c1-fixture-rename-](./quick/260610-b6p-make-test-suite-green-c1-fixture-rename-/) |
| 260610-qfy | REVIEW §4 LOW items (16) all resolved + PRI [ ]/[x]/[~] checklist added (§5, all 18 Pri + SKIP). 12 FIXED: P1-P5 paper prose (d_v=2d, GF-variant defs, trainable-set, Table-3 protocol disclosure, per-condition reword); T9 stateful-safe optimizer reset; T10 strict=False assert-keys (tent/sar/eval_tta); T11 log fix; I6 fig-5 retracted-bound docstring; I12 stale-banner guard; I13 backbone col + results-index.csv migrated 17→18 cols; D15 unknown-kwarg warn-log (non-fatal, replay-safe). 4 DOCUMENTED-ACCEPT: D7 off-by-one (0.002pp), T8 SAR-fidelity comment, D14 iterdir DO-NOT-sort, D16 hardcoded paths. Suite 321 passed; paper clean 10pp. | 2026-06-10 | d4f1431 | [260610-qfy-knock-out-review-2026-06-10-section-4-lo](./quick/260610-qfy-knock-out-review-2026-06-10-section-4-lo/) |
| 260610-po3 | Paper 3-seed all ablation rows (REVIEW-2026-06-10 Pri-1 follow-on, user-approved) + Pri-5 TTA table. Ran pri1_ablations_seeds (52 runs, all OK, commit 3aac394); converted the 4 single-seed rows in Tables 1/2 (Skeleton/Late Fusion/GF 2-Person/GF Mean-Only) to 3-seed mean±std. Generator gen_ablation_tables_3seed.py reproduces the already-3-seed rows exactly. MATERIAL: UCF GF Mean-Only 83.0→82.5 (no longer > gated), XD GF Mean-Only SO400M 79.9→78.4 (now < gated 78.7), skeleton UCF 71.8→68.8±2.8, XD 40.9→40.8; removes 'pooling-variant>method' tension. Prose+captions+:217 updated to uniform 3-seed; added tab:tta_breakdown (disc_reweight per-corruption: gaussian +4.83, others ~0 by gate). PDF clean 10pp, headlines 82.5/78.7 intact. Figure fig_backbone_comparison left (stale chart CSV — flagged). | 2026-06-10 | 33591ac | [260610-po3-update-paper-tables-1-2-prose-to-3-seed-](./quick/260610-po3-update-paper-tables-1-2-prose-to-3-seed-/) |
| 260610-bed | Paper P1-P7 confirmed corrections (REVIEW-2026-06-10 Batch C): 11 edits across 7 findings in main.tex, editorial/factual only (no number changes). P1 stale +13.9→+13.2 3-seed mean (×3); P2 rewrote §5 LN-barrier to match §4.5 (frozen gate/head, LN affine 1,536 too small to reorder rank-AUC, disc_reweight=positive path; dropped disproven BN/LN "distributional memory"); P3 "400M+ samples"→"shape-optimized ~400M-param SoViT-400M"/capacity framing (×3); P4 :344 SO400M "visual-only"→"under gated fusion"; P5 XD codes (no B3→B4/B5/B6/G); P6 "none in XD"→"one"; P7 trailing-frame claim qualified per-dataset. PDF rebuilds clean (10pp, 0 errors, 0 undefined refs); headlines UCF 82.5/XD 78.7 intact. | 2026-06-10 | 9218dd2 | [260610-bed-paper-p1-p7-confirmed-corrections-from-r](./quick/260610-bed-paper-p1-p7-confirmed-corrections-from-r/) |
| 260611-ttr | Add .knowledge/tta-to-reweighting.html — self-contained one-time-use HTML explainer of the TTA→reweighting transition (dropout artifact 83b8927 → continual protocol 1ed2d16 → real <0.1pp entropy zero a5e3f73 → CORAL dead end → disc_reweight def88d5 → paper rewrite 12cd95f), with mechanism formulas/diagram, Table-3 + per-corruption evidence, caveats, and code/record pointers. Rendering verified via playwright (full-page screenshots, no console errors beyond favicon 404) | 2026-06-11 | f079df5 | — (inline /gsd:fast) |
| 260611-66v | Rebuild paper Figure 1 as native TikZ vector figure (replaces unreadable ~3pt-text raster PNG): new paper/figures/fig_architecture.tex \input at \textwidth, tikz preamble, content corrected to current methods (late fusion = score averaging, visual feat 1024–3072-d, Eqs (2)-(4) math incl. residual, TENT/SAR blocks → dashed disc-reliability-reweighting annotation ref sec:disc), caption rewritten, PNG/HTML deleted. PDF clean 10pp; visually verified at 300dpi. | 2026-06-11 | 3e9c492 | [260611-66v-rebuild-paper-figure-1-architecture-over](./quick/260611-66v-rebuild-paper-figure-1-architecture-over/) |
| 260611-fsl | Fix paper Figure 4 (fig_tta_comparison.pdf): legend at loc="upper left" overlapped the CLIP ViT-B/16 bars, hiding 63.7/64.4/+0.67 labels. Moved to compact 2-column upper-center box (clear headroom between Base and SO400M groups). Targeted single-figure regen ONLY (fig_backbone_comparison left untouched — its chart CSV is stale/pre-λ0, regen would corrupt; planner-caught hazard). git-status isolation gate confirmed only fig_tta_comparison.pdf changed under paper/figures/. PDF rebuilt clean (10pp); legend placement visually verified in figure PDF + main.pdf p.8. | 2026-06-11 | 2d45071 | [260611-fsl-fix-paper-figure-4-fig-tta-comparison-mo](./quick/260611-fsl-fix-paper-figure-4-fig-tta-comparison-mo/) |
| 260621-fjk | Phase 12 SOTA-comparison framing fixes (from the honesty-assessment workflow): #3 abstract SOTA-context sentence (~88–91% field ceiling, gap-by-design); #1 honest-hypothesis CLIP-TSA rewrite ×3 ('we hypothesize … but do not isolate this experimentally') in main.tex Limitations + fragment fair-subset read + P2; #2 XD-scoped competitiveness (state UCF trails every modern fair-subset peer; drop the 'competitive, not an outlier' two-metric implication); #6 fragment positioning now leads with the orthogonal contribution (P3 moved ahead of the competitiveness paragraph). Framing-only — no number changed; clean rebuild 11pp / 0 undefined citations; standalone fragment recompiles; headlines + Tables 1–3 byte-identical; Phase 12 12-VERIFICATION PASS still holds | 2026-06-21 | 8a72d2d | [260621-fjk-apply-phase-12-sota-comparison-framing-f](./quick/260621-fjk-apply-phase-12-sota-comparison-framing-f/) |
| 260621-gcn | Restructure paper SOTA comparison (main.tex tab:comparison) into an honest, more-favorable framing — group by operating regime into 2 blocks (heavier-budget: text/MLLM/aux-modality; comparable regime: frozen/no-text/visual/single-GPU, This-work bolded), UCF-descending sort within each, stated outcome-neutral inclusion rule in caption; +EventVAD/LAVAD efficiency rows (+references.bib shao2025eventvad/zanella2024lavad, RE-VERIFY on AP cells) + §6 efficiency prose. Independently adversarial-audited → HONEST AND DEFENSIBLE; disclosed the one seam it found (GS-MoE 91.58/82.89 omission) via footnote+cite damicantonio2025gsmoe with outcome-neutral reasons. No number changed, no method dropped by outcome. Table set \footnotesize to hold 11pp; clean rebuild 0 undefined; headlines + Tables 1-2 byte-identical | 2026-06-21 | 9312fe5 | [260621-gcn-restructure-paper-sota-comparison-table-](./quick/260621-gcn-restructure-paper-sota-comparison-table-/) |
| 260621-ibd | Redesign Figure 1 (fig_architecture.tex) into a swimlane layout for readability + less wasted space (user-approved over a compact-pipeline variant via rendered A/B). Tinted skeleton/visual frozen-stream lanes funnel into the trainable gated-fusion box; equations → conceptual labels (already in §3.4 Eqs 2-4); floating "Late fusion baseline" box removed (it's §3.4 Eq 1) + orphaned caption clause trimmed in main.tex; streams equalized to 3 stages (feature boxes align); prediction column centered; MIL-loss → clean right-side loop; test-time note wired to \ref{sec:disc}. Layout-only, no number/claim change; clean rebuild 11pp, 0 errors/undefined, headlines 82.5/78.7 intact. (Cleanup note: also removed pre-existing untracked scratch _tmp_paperfig-1.png — disclosed.) | 2026-06-21 | 4ee73d3 | [260621-ibd-redesign-paper-figure-1-paper-figures-fi](./quick/260621-ibd-redesign-paper-figure-1-paper-figures-fi/) |
| 260622-ukd | Fix HIGH review finding T3-1 (fabricated SOTA citation, from review-2026-06-22.html): Light-WVAD (wang2024lightwvad, Neurocomputing 2024 = arXiv 2310.05330) was credited with 77.3% XD-Violence AP, but that paper evaluates ONLY UCF-Crime + ShanghaiTech and reports ONLY AUC — no XD result, no AP metric. Removed the fabricated 77.3 from main.tex Table 4 (XD cell → ---) + §6 on-par prose, and from BOTH tables + BOTH prose passages of sota_comparison_full.tex (XD cells → ---, "XD not evaluated"). UCF 84.7 AUC cells/prose retained everywhere. Folded in related LOW T3-4: corrected wang2024lightwvad bib title → "A Lightweight Video Anomaly Detection Model with Weak Supervision and Adaptive Instance Selection". grep confirms no Light-WVAD 77.3 remains; clean rebuild 11pp (latexmk converged, bbl carries corrected title); rendered-PDF verified (on-par prose now RTFM+MGFN only, no 77.3 on comparison pages); headlines 82.5/78.7 intact. | 2026-06-22 | f694611 | [260622-ukd-fix-t3-1-light-wvad-xd-ap](./quick/260622-ukd-fix-t3-1-light-wvad-xd-ap/) |

---

## Session Continuity

**Stopped at:** Phase 12 COMPLETE (all 3 plans)
**To resume:** Phase 12 done — SOTA comparison shipped honestly in both the standalone thesis fragment (paper/sota_comparison_full.tex, Plan 01) and the live CGW '26 paper (§2 number-backfill + condensed tab:comparison + 6 bib entries, Plan 02), with Plan 03 final verification PASSED (12-VERIFICATION.md: clean 11-page build, full number traceability to 12-RESEARCH-sota.md, 0 overclaim, byte-identical headlines). No open work in this phase. Student manual re-checks before camera-ready submission: CLIP-TSA XD 82.19, MGFN XD 79.19 (I3D), RTFM XD 77.81 (I3D), Light-WVAD authors = Wang, Zhou & Guan. (Optional parked: Phase 4d XD hyperparameter sweep + RTFM repro-gap investigation.)

**Files of record:**

- `.planning/PROJECT.md` — project definition and key decisions
- `.planning/REQUIREMENTS.md` — 40 v1 requirements with traceability
- `.planning/ROADMAP.md` — 6-phase roadmap with success criteria
- `.planning/research/SUMMARY.md` — research findings and pitfall catalog
- `thesis_prd_v2.3.md` — authoritative PRD specification

---

*State initialized: 2026-03-31*

**Planned Phase:** 6 (Analysis & Visualization) — 2 plans — 2026-05-02T12:36:57.713Z
