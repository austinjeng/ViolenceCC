# Research Summary — ViolenceCC

**Project:** Dual-Modal Weakly Supervised VAD (Skeleton GCN + CLIP) with TTA
**Synthesized:** 2026-03-31
**Research files:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

---

## Executive Summary

ViolenceCC is a master's thesis research codebase for weakly supervised violence-oriented video anomaly detection. The approach fuses two frozen backbones — a CTR-GCN skeleton GCN pretrained on NTU120 and a CLIP ViT-B/16 visual encoder — via a learnable Gated Fusion head trained with MIL Ranking Loss. The core research contribution is applying TENT-style and SAR-style test-time adaptation, restricted to LayerNorm affine parameters in the fusion head, to improve robustness under image corruptions (UCF-Crime-C). This is an established problem structure: every peer reference codebase (RTFM, VadCLIP, PEL4VAD, MGFN) follows the identical anatomy of offline feature pre-extraction → MIL training on cached features → frame-level AUC/AP evaluation.

The recommended build strategy is three isolated conda environments plus an offline feature cache as the central data contract between stages. The mmcv-full 1.x legacy dependency in PYSKL makes sharing a PyTorch environment with the modern training stack impossible; the three-environment split is the only clean resolution. Feature extraction is a one-time GPU-intensive cost; all subsequent iteration (ablations, hyperparameter sweeps, TTA experiments) operates in minutes per run on the cached features. This design is the right architecture for the timeline and hardware constraints.

The primary technical risks are: (1) skeleton coordinate normalization being silently wrong when bypassing PYSKL's preprocessing pipeline, (2) temporal misalignment between skeleton snippets and CLIP snippets in variable-FPS videos, and (3) TTA entropy collapse on normal-heavy batches causing negative transfer. All three have documented prevention strategies and can be caught early with the RTFM baseline reproduction step and an alignment verification script. The project is well-scoped for a 12-week timeline if anti-features (end-to-end training, deployment artifacts, custom metrics) are strictly avoided.

---

## Key Findings

### From STACK.md — Technology Decisions

**Three-environment strategy is mandatory**, not optional:

| Environment | Python | PyTorch | Purpose |
|-------------|--------|---------|---------|
| vcc-skeleton | 3.11 | none | RTMPose extraction via rtmlib + onnxruntime-gpu |
| vcc-ctrgcn | 3.10 | 1.12.1 + cu113 | CTR-GCN frozen forward pass via PYSKL |
| vcc-main | 3.11 | 2.6.0 + cu124 | MIL training, CLIP extraction, TTA, evaluation |

**Critical version pins:**
- `rtmlib==0.0.15` (latest, 2026-02-10) + `onnxruntime-gpu 1.20.x` — requires cuDNN 9.x
- `mmcv-full==1.7.0` for PYSKL (NOT 1.5.0 from requirements.txt — use pyskl_310.yaml as authority)
- `torch==2.6.0+cu124` for main env (NOT 2.11.x — cu126/128 wheels untested with project dependencies)
- `open-clip-torch==3.3.0` — use `pretrained='openai'` to get ViT-B/16 original weights

**RTMPose model:** RTMPose-m (256x192, COCO-17). Best accuracy/speed tradeoff; >200 FPS on RTX 4090.

**CTR-GCN weights:** 4 streams (j/b/jm/bm) from PYSKL NTU120 HRNet 2D. All 4 use COCO-17 topology — no joint mapping needed.

**Feature storage:** float32 .npy per video (not HDF5 — simpler, sufficient at ~25 GB per dataset).

**TTA source:** SAR repo (mr-eggplant/SAR) — both tent.py and sar.py included. Adapt `configure_model()` to target `nn.LayerNorm` instead of `nn.BatchNorm2d`.

**Known compatibility issues to resolve on Day 1:**
- decord on Windows/Python 3.11+ may fail — fallback is eva-decord (identical API)
- mmcv-full wheel URL uses `torch1.12.0` even for PyTorch 1.12.1 installs
- SAR timm conflict is safe to ignore — SAR's entropy logic is pure PyTorch and never calls timm APIs

---

### From FEATURES.md — What Must Be Built

**Table Stakes (must be present for thesis defense):**

1. **Skeleton extraction script** — RTMPose → PYSKL pickle format; handles missing-person frames
2. **CLIP extraction script** — 1 FPS frame sampling, mean+max pooling, snippet-aligned output
3. **Feature cache** — float32 .npy per video, indexed by video ID, both modalities time-aligned
4. **Dataset class** — bag-level MIL batching (T=32 snippets/video), train/val/test modes
5. **Official split files committed to repo** — UCF-Crime Anomaly_Train/Test/Temporal annotations; XD-Violence annotation file
6. **Fixed 15% stratified validation split** — seeded, stored as text file, used by ALL experiments
7. **Frozen CTR-GCN wrapper** — verify forward pass on COCO-17 input before extraction
8. **Frozen CLIP ViT-B/16 wrapper** — [CLS] token extraction, FP16
9. **Gated Fusion module** — sigmoid gating, 256-d shared space, LayerNorm + Dropout 0.3
10. **Late Fusion baseline** — score-level weighted average (2-hour implementation, validates pipeline)
11. **Single-modal baselines** — Skeleton-Only, CLIP-Only
12. **MIL Ranking Loss** — top-k per bag, hinge margin
13. **AdamW + warmup + cosine decay** — with early stopping patience=10 on val MIL loss
14. **Frame-level AUC on UCF-Crime** and **AP on XD-Violence** — sklearn, matching published convention
15. **RTFM baseline reproduction** — target 84.30% ±1% AUC; validates evaluation harness
16. **Ablation table** (8 entries) — all fusion variants, pooling strategies, TTA methods
17. **UCF-Crime-C corruption generator** — 4 types × 5 severities
18. **TENT-style and SAR-style TTA modules** — LN affine params only, per-video reset
19. **Anomaly score temporal curve plots** — matplotlib, 2-3 representative videos
20. **Skeleton overlay visualization** — COCO-17 keypoints on video frames

**High-value differentiators to build after all table stakes pass:**
- Per-category violence subset AUC/AP breakdown (directly answers RQ1)
- CLIP text prompt engineering — 20-30 LLM-generated prompts, version-controlled
- Corruption-severity heatmap (4×5 grid, seaborn)
- Gating weight distribution analysis (sigmoid gate histograms by video category)
- t-SNE / UMAP of fused features — normal vs. abnormal snippets

**Do not build (anti-features):**
- End-to-end backbone training (exceeds VRAM budget, eliminates 3-stage methodology)
- Real-time inference optimization (TensorRT, quantization — not a deployment artifact)
- Web UI, Docker, unit tests for ML internals, custom metrics, multi-GPU, streaming extraction
- Two-Person Interaction Graph (34-node inter-body edges — high risk, marginal gain)
- Three-modal fusion as primary model before dual-modal is stable

---

### From ARCHITECTURE.md — Structure and Patterns

**System stages map directly to conda environments and component tiers:**

```
Stage 1 (vcc-skeleton / vcc-ctrgcn): Feature pre-extraction — runs once per dataset
  Raw videos → RTMPose → CTR-GCN (4-stream weighted concat) → [N_snippets, 256] .npy
  Raw videos → CLIP ViT-B/16 (1 FPS, mean+max pool) → [N_snippets, 512] .npy

Stage 2 (vcc-main): MIL Fusion Training — fast iteration on cached features
  .npy files → Dataset Loader → GatedFusion → MIL Ranking Loss → checkpoint.pth

Stage 3 (vcc-main): Test-Time Adaptation
  Cached features → TTAWrapper (LN-only, per-video reset) → frame-level AUC/AP
```

**Directory layout (derived from PEL4VAD + VadCLIP patterns):**
```
ViolenceCC/
├── configs/          # YAML per experiment (base.yaml + overrides)
├── data/             # Split lists and temporal annotations only (not features)
├── src/
│   ├── extract/      # skeleton_extractor.py, clip_extractor.py, corruption_generator.py, verify_alignment.py
│   ├── data/         # dataset.py, collate.py
│   ├── models/       # fusion.py (Gated/Late/CrossAttn), mil_head.py, backbones/
│   ├── losses/       # mil_loss.py
│   ├── tta/          # tta_wrapper.py, tent_style.py, sar_style.py
│   ├── eval/         # metrics.py, visualize.py
│   └── utils/        # config.py, logger.py, seed.py, checkpoint.py
├── scripts/          # Shell scripts: extract_ucf.sh, train.sh, eval.sh, tta_eval.sh
├── results/          # Per-experiment: config_snapshot.json, train_log.csv, best_model.pth, metrics.json
└── notebooks/        # Analysis and visualization only; not in pipeline
```

**Build order (enforced by data dependencies):**
- Tier 0: conda envs + data/ split files
- Tier 1: backbone wrappers + extractor scripts (blocks everything downstream)
- Tier 2: MIL loss, fusion model, dataset loader, utils
- Tier 3: train.py entry point
- Tier 4: eval.py entry point
- Tier 5: corruption generator + TTA modules (requires Tier 4 passing)
- Tier 6: notebooks, visualizations

**Patterns to follow:**
- Single `train.py` entry point — not per-dataset scripts (avoids VadCLIP's duplication problem)
- Config snapshot saved alongside every checkpoint (not done in RTFM/MGFN; required for thesis reproducibility)
- `verify_alignment.py` assertion: N_skel_snippets == N_clip_snippets for every video
- LN-only TTA with per-video reset; `ln_state_init` captured from final trained checkpoint

**Patterns to avoid:**
- Feature re-extraction inside training loop
- Test set AUC in model selection (data leakage)
- Flat features directory (20 corruption variants need structured subdirectories)
- TTA without per-video reset (error accumulation across test videos)

---

### From PITFALLS.md — Critical Failure Modes

**Top 5 project-breaking pitfalls:**

**1. Skeleton coordinate space mismatch (C1) — Phase 1, Week 1**
rtmlib returns raw pixel coordinates; PYSKL CTR-GCN expects normalized coordinates (~[-1,1]). Feeding raw pixels causes garbage 256-d features with no error message. AUC stagnates at 55-60% and appears to be a model problem. Fix: apply PYSKL's `PreNormalize2D` transform manually; add assertion that all joint coordinates are in [-1, 1] after normalization.

**2. Temporal misalignment between skeleton and CLIP snippets (C2) — Phase 1, Week 2**
UCF-Crime and XD-Violence have mixed FPS. A 64-frame skeleton window at 30 FPS covers 2.1s; at 24 FPS it covers 2.7s. Using fixed second-count for CLIP frames creates systematic drift. Fix: read actual FPS per video with `cv2.CAP_PROP_FPS`; map all snippet boundaries to wall-clock seconds; verify ≥90% temporal overlap per snippet in `verify_alignment.py`.

**3. Data leakage via test set in hyperparameter tuning (C3) — Phase 1, Week 2**
Test set has frame-level annotations; training set does not. Using test AUC for early stopping or model selection inflates reported numbers. Fix: 15% stratified validation split by Week 2; early stopping on val MIL Ranking Loss only; test annotations loaded only in standalone `evaluate.py`.

**4. Wrong frame-level AUC calculation (C4) — Phase 2, Week 2-3**
Snippet-level scores must be broadcast to all frames in each snippet window. Off-by-one errors in the last snippet produce mismatched vector lengths. Fix: encapsulate snippet-to-frame mapping in a single utility function used everywhere; assert `len(frame_scores) == len(frame_labels)` before every AUC call; cross-validate against RTFM's official eval script.

**5. MIL training collapse to trivial solutions (C5) — Phase 2, Weeks 3-4**
Two trivial solutions satisfy MIL Ranking Loss: output constant high scores, or output uniformly high scores for all snippets of anomalous-label videos. Manifests as near-perfect video-level AUC but 60-72% frame-level AUC. Fix: monitor snippet-level score distribution variance; add temporal smoothness or sparsity penalty; verify bag construction matches RTFM's convention (one anomalous + one normal video per batch pair).

**Additional high-priority pitfalls:**
- C6: CTR-GCN shape errors with multi-person violent scenes — use mean-person padding for M<2; track person IDs across snippet window (Phase 1, Week 2)
- M5: TTA entropy collapse on normal-heavy batches — implement SAR-style gradient filtering; analyze entropy distribution by anomaly duration (Phase 3, Week 6)
- M6: SAR rho hyperparameter from ImageNet defaults is too large for scalar anomaly output — grid search starting at 0.005 (Phase 3, Week 6)
- M7: Corruption experiment must re-extract skeletons for motion blur + JPEG (not Gaussian noise / brightness) to be methodologically defensible (Phase 3, Week 6)

---

## Key Decisions Surfaced by Research

1. **Three conda environments are the only viable dependency strategy.** mmcv-full 1.x cannot coexist with PyTorch 2.x. The vcc-ctrgcn env is a legacy silo used once; the vcc-main env is where all research iteration happens.

2. **Float32 .npy per video is the right feature storage format** — not HDF5, not float16. Simpler loading (pure np.load), no dtype mismatch risk, ~25 GB per dataset fits comfortably. Corruption variants go in structured subdirectories.

3. **RTFM baseline reproduction is gating.** It must succeed (84.30% ±1% AUC) before any novel experiment begins. It validates the evaluation protocol, catches C4 (AUC calculation bugs), and provides the comparison anchor for all ablation tables.

4. **15% stratified validation split must be created and committed before the first training run.** All experiments across the entire project use this identical split. Changing it later invalidates all comparisons.

5. **Late Fusion must be implemented before Gated Fusion.** It is a 2-hour implementation that validates the full pipeline end-to-end before adding the complexity of learned gating. If Gated Fusion later underperforms Late Fusion, the comparison is already in hand.

6. **TTA operates entirely on cached features.** No raw video re-reading at test time. Corruption variants require re-extracting CLIP features (and selectively skeleton features) into separate cache subdirectories before any TTA evaluation.

7. **Single train.py entry point** with YAML config inheritance is the correct architecture choice over per-dataset scripts (avoids VadCLIP's code duplication anti-pattern).

8. **YOLO-World third modality is deferred to Week 7+, conditional on main AUC ≥ 83%.** It is an anti-feature if dual-modal results are not stable.

9. **The LN-only TTA methodological contribution is novel but uncertain.** TENT/SAR were developed for BatchNorm. The BN→LN transfer is feasible (LN has gamma/beta analogues), but effectiveness is a research-level unknown — not a software incompatibility. Report per-video TTA breakdown (not just aggregate AUC) to expose whether adaptation helps or hurts on short-anomaly videos.

10. **Novelty claim must be conservatively scoped.** Re-run literature search at each phase boundary. Use "to the best of our knowledge, at time of writing" phrasing. The distinguishing scope is: violence-oriented + weakly supervised + skeleton GCN + VLM + LN-based TTA, not any single element.

---

## Roadmap Implications

Research supports a 5-phase structure mapping to ARCHITECTURE.md's component tiers.

### Phase 1: Environment Setup and Feature Extraction (Weeks 1-3)

**Rationale:** Everything downstream is blocked on having valid, aligned feature caches. This is the longest-lead-time phase due to multi-hour extraction jobs and the most dangerous for silent bugs (C1, C2, C6). Must be completed and verified before any training begins.

**Delivers:**
- Three conda environments fully functional
- CTR-GCN forward-pass verification with coordinate normalization confirmed (C1 resolved)
- Skeleton features for UCF-Crime and XD-Violence cached
- CLIP features for UCF-Crime and XD-Violence cached
- `verify_alignment.py` passing for all videos
- Official split files committed; 15% stratified val split created and seeded

**Features from FEATURES.md:** items 1-6 (extraction scripts, cache, split files, val split)

**Pitfalls to address:** C1 (Week 1), C2 / C6 / M1 / M3 (Week 2), m2 / m3 (XD-Violence data prep)

**Research flag:** Minimal — environment setup and feature extraction are well-documented in PYSKL and rtmlib repos. No phase-level deep research needed. However, the coordinate normalization verification (C1) requires hands-on debugging time; allocate a full day for it.

---

### Phase 2: Baseline Pipeline and MIL Training (Weeks 3-5)

**Rationale:** RTFM reproduction must gate all novel experiments. Skeleton-Only and CLIP-Only single-modal baselines must run before Gated Fusion is built so that ablation comparisons are available from the start. Late Fusion before Gated Fusion validates the fusion pipeline.

**Delivers:**
- RTFM reproduction on UCF-Crime: 84.30% ±1% AUC
- Feature schema finalized; validate_cache.py passing (M4 resolved)
- Dataset class + MIL Ranking Loss implemented
- Skeleton-Only and CLIP-Only baselines run and logged
- Late Fusion baseline run and logged
- Gated Fusion module with training + eval on UCF-Crime

**Features from FEATURES.md:** items 7-16 (backbone wrappers, fusion modules, MIL loss, training infrastructure, evaluation)

**Pitfalls to address:** C4 (AUC calculation, caught during RTFM reproduction), C5 (MIL collapse, monitor during single-modal baselines), M2 (CLIP projection initialization), m1 (gate saturation), M4 (feature schema)

**Research flag:** Standard MIL training patterns are well-documented. Gated Fusion is ~50 lines of PyTorch per PRD §9.2 spec. No deep phase research needed. If C5 (collapse) is triggered, consult MGFN/PEL4VAD for their sparsity/smoothness regularizer implementations.

---

### Phase 3: XD-Violence Evaluation and Ablation Table (Weeks 5-7)

**Rationale:** XD-Violence extraction runs in the background during Phase 2. Once cache is ready and the UCF-Crime model is stable, cross-dataset evaluation and the 8-ablation table can be completed. This phase confirms the dual-modal system meets the AUC ≥ 83% gate before any TTA work begins.

**Delivers:**
- Frame-level AP on XD-Violence test set
- Full 8-entry ablation table (skeleton-only, CLIP-only, late fusion, gated fusion, CLIP pooling variants, multi-person aggregation variants)
- 3-seed mean ± std for key results
- Per-category violence subset AUC/AP breakdown (differentiator — low effort, high thesis value)

**Features from FEATURES.md:** ablation table, per-category breakdown

**Pitfalls to address:** m4 (statistical instability — enforce 3 runs), m7 (prompt version control)

**Research flag:** Standard patterns apply. If AUC < 83% after ablations, revisit CTR-GCN coordinate normalization (C1) and MIL collapse (C5) before proceeding to TTA.

**Gate:** Dual-modal AUC ≥ 83% required before Phase 4 begins.

---

### Phase 4: TTA Infrastructure and UCF-Crime-C Evaluation (Weeks 6-8)

**Rationale:** TTA is the second major thesis contribution. It requires its own infrastructure (corruption generator, re-extracted features, TENT-style and SAR-style modules) and introduces the highest research-level uncertainty (LN-only adaptation effectiveness, SAR rho calibration, entropy collapse on normal-heavy batches).

**Delivers:**
- UCF-Crime-C corruption generator: 4 types × 5 severities
- CLIP re-extraction for all 20 corruption conditions
- Skeleton re-extraction for motion blur + JPEG conditions (M7)
- TENT-style TTA module with per-video reset
- SAR-style TTA module with rho grid search (M6)
- TTA evaluation loop: Source-Only vs TENT-style vs SAR-style across 20 conditions
- Per-condition AUC table and 4×5 heatmap (differentiator)

**Features from FEATURES.md:** items 17-20 (UCF-Crime-C generator, CLIP re-extraction, TENT-style, SAR-style, TTA eval loop)

**Pitfalls to address:** M5 (entropy collapse, SAR-style gradient filtering), M6 (SAR rho calibration), M7 (corruption modality coverage), m5 (TTA reset state verification)

**Research flag:** This phase needs deeper research at planning time. The LN-based TENT/SAR adaptation is methodologically novel. SAR rho defaults are ImageNet-calibrated and will need tuning from first principles. Recommend a targeted `/gsd:research-phase` on: "TENT and SAR behavior with scalar anomaly score outputs vs. softmax classification outputs" before writing TTA code.

---

### Phase 5: Analysis, Visualization, and Write-Up Support (Weeks 8-10)

**Rationale:** Final results require 3-seed runs; qualitative figures take a full day to generate well; literature re-check is mandatory before submitting novelty claims.

**Delivers:**
- Anomaly score temporal curve plots (2-3 UCF-Crime + XD-Violence representative videos)
- Skeleton overlay visualization for thesis figures
- Gating weight distribution histograms (differentiator)
- t-SNE / UMAP of fused features (differentiator, if time permits)
- Cross-dataset TTA (UCF→XD, XD→UCF) — only if Week 8 has slack
- Final 3-seed main results table
- Literature search re-run; novelty claim scoping verified

**Features from FEATURES.md:** qualitative analysis, differentiators gated on time

**Pitfalls to address:** m4 (3-run statistics for final table), m6 (novelty claim scope)

**Research flag:** Standard — these are mechanical execution steps. No deep research needed.

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Stack (environment split, version pins) | HIGH | Verified against official PYSKL pyskl_310.yaml, PyPI release dates, onnxruntime docs |
| Features (what to build, what to defer) | HIGH | Grounded in 4 verified reference codebases (RTFM, VadCLIP, PEL4VAD, CMSIL) + PRD v2.3 |
| Architecture (directory layout, component boundaries, data flow) | HIGH | Directly mirrors PEL4VAD/VadCLIP patterns; PRD v2.3 is authoritative spec |
| Pitfalls (critical bugs and methodology risks) | HIGH | C1-C6 verified from PYSKL data pipeline docs, TENT/SAR papers, RTFM eval code; M5-M6 from ICML 2023 TTA pitfalls survey |
| LN-based TTA effectiveness | MEDIUM | Methodologically novel; BN→LN transfer is software-feasible but empirical outcome is unknown by design |
| decord on Windows/Python 3.11+ | MEDIUM | Known issues; eva-decord fallback is available but adds a dependency decision |
| PyTorch 2.6.0 as main env version | MEDIUM | Stable as of research date; 2.11.x is newer but cu124 wheel availability for 2.11 was unverified |

**Overall confidence:** HIGH for build plan; MEDIUM for TTA empirical results (which is the thesis contribution — uncertainty is appropriate).

**Gaps requiring attention during planning:**
1. Actual FPS distribution in UCF-Crime and XD-Violence — needed to size snippet window computation; gather this in Phase 1 Week 1 by scanning metadata
2. XD-Violence access confirmation — RWF-2000 access described as "currently uncertain" in FEATURES.md; resolve before Phase 3 planning
3. SAR rho sensitivity for scalar anomaly output — no published reference; requires empirical tuning in Phase 4

---

## Sources (Aggregated)

- PYSKL: https://github.com/kennymckormick/pyskl (ACM MM 2022)
- rtmlib: https://github.com/Tau-J/rtmlib (PyPI v0.0.15, 2026-02-10)
- onnxruntime CUDA provider: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html
- open-clip-torch: https://pypi.org/project/open-clip-torch/ (v3.3.0, 2026-02-27)
- SAR: https://github.com/mr-eggplant/SAR (ICLR 2023 Oral; arxiv 2302.12400)
- TENT: https://github.com/DequanWang/tent (ICLR 2021)
- RTFM: https://github.com/tianyu0207/RTFM (ICCV 2021)
- VadCLIP: https://github.com/nwpu-zxr/VadCLIP (AAAI 2024)
- PEL4VAD: https://github.com/yujiangpu20/PEL4VAD (IEEE-TIP)
- MGFN: https://github.com/carolchenyx/MGFN
- CMSIL: https://github.com/casperZB/CMSIL (ICME 2024)
- On Pitfalls of Test-Time Adaptation: https://proceedings.mlr.press/v202/zhao23d/zhao23d.pdf (ICML 2023)
- In Search of Lost Online TTA: https://link.springer.com/article/10.1007/s11263-024-02213-5 (IJCV 2024)
- TTA error accumulation survey: https://arxiv.org/html/2603.03796
- ImageNet-C corruption benchmark: https://arxiv.org/abs/1903.12261 (ICLR 2019)
- PRD v2.3: D:\ViolenceCC\thesis_prd_v2.3.md (authoritative project specification)
