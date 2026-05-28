# Journey Into ViolenceCC

*A technical narrative of 33 days of research engineering, from concept to thesis-ready dual-modal violence detection system.*

---

## 1. Project Genesis

ViolenceCC was born on March 31, 2026, in a single intensive session (session `5b8396ae`) that laid down 86 observations and consumed 436,345 discovery tokens in a matter of hours. The founding vision was clear from observation #362: build a *dual-modal weakly supervised video anomaly detection system* combining skeleton dynamics (CTR-GCN) with CLIP visual-language semantics for a master's thesis, trained under MIL Ranking Loss with test-time adaptation experiments.

The initial session was an act of comprehensive front-loading. Before a single line of implementation code was written, Austin and Claude produced five research documents totaling 1,978 lines: STACK.md resolving dependency conflicts, FEATURES.md defining 20 table-stakes thesis requirements, ARCHITECTURE.md specifying a 10-component system with 6-tier build order, PITFALLS.md cataloging 20 failure modes (6 critical, 7 moderate, 7 minor), and SUMMARY.md synthesizing everything into a 5-phase roadmap. The entire planning baseline -- PROJECT.md, REQUIREMENTS.md with 40 v1 requirements mapped to 6 phases, ROADMAP.md, and STATE.md -- was committed by observation #379.

The founding technical decisions that shaped everything to follow were made in this single session: three isolated conda environments (because mmcv-full 1.x is incompatible with PyTorch 2.x), all backbones frozen (RTX 4090's 24GB VRAM rules out end-to-end training), float32 npy feature storage, RTFM baseline reproduction as a hard evaluation gate, and LayerNorm-only TTA as the research contribution. These were not arbitrary choices -- each was grounded in specific codebase investigations of RTFM, VadCLIP, MGFN, PEL4VAD, and the SAR repository.

The constraint profile was honest from the start: single GPU, solo researcher, 12-week timeline, master's level expectations. This self-awareness proved valuable. The architecture document explicitly listed anti-patterns to avoid (feature re-extraction in training loops, test set leakage, TTA without per-video reset), and these warnings prevented real bugs in later phases.

---

## 2. Architectural Evolution

The architecture evolved through three major transitions, each driven by empirical reality rather than theoretical preference.

**The Three-Environment Strategy (Phase 1).** The most consequential architectural decision was the three-environment isolation pattern. PYSKL requires PyTorch 1.12.1 with mmcv-full 1.7.0 (a 2022-era stack), while the main training pipeline uses PyTorch 2.6.0 with open-clip-torch 3.3.0 (a 2025 stack). A third environment hosts rtmlib for ONNX-based skeleton extraction. This created a pipeline that spans three conda environments, three Python versions, and two CUDA generations -- a fragile but necessary arrangement that required careful coordination through shared file formats (pickle files, JSON snippet boundaries, npy feature caches).

**The Shared Boundary JSON Contract (Phase 2).** A critical design pattern emerged during feature extraction planning: computing snippet boundaries once during skeleton extraction and persisting them as JSON files that both skeleton and CLIP scripts read. This "temporal alignment by construction" approach (observation #452) prevented the C2 misalignment pitfall rather than detecting it post-hoc. Every downstream script reads the same `{video_id}_boundaries.json`, guaranteeing `N_skel_snippets == N_clip_snippets` by design.

**The Phase Split Pattern (Phase 4/4b/4c).** When the RTFM XD-I3D gate failed (AP 0.6570 vs. target 0.7681), the project's roadmap had to adapt. Rather than treating this as a blocking failure, Phase 4 was surgically split: Phase 4b narrowed to just the RTFM gate validation, Phase 4c was created for XD-Violence main results (activated when feature extraction completes), and Phase 5 TTA was unblocked to run in parallel. This "accept and restructure" pattern (observation #828) demonstrated mature project management -- the gap was documented as a thesis limitation with community calibration (VadCLIP's published RTFM reproduction achieves only 74--76% AP), and work continued on the critical path.

---

## 3. Key Breakthroughs

**The cuDNN PATH Discovery (Observation #473).** Skeleton extraction was running at 102--128 seconds per video on CPU. Investigation revealed that cuDNN 9.x DLLs were installed but buried in a Windows-specific nested subdirectory (`C:\Program Files\NVIDIA\CUDNN\v9.8\bin\12.8\`). Creating a conda activation script to add this path unlocked GPU acceleration and achieved a **30--40x speedup** (2--10 seconds per video). This single fix reduced the UCF-Crime extraction estimate from 38--48 hours to approximately 1--1.5 hours.

**The Wholebody-to-Body Model Switch (Observation #542).** Performance analysis revealed the extraction pipeline was using RTMWholebody (133 keypoints: body + face + hands) and immediately discarding 116 of them, keeping only the 17 COCO body keypoints. Switching to the RTMPose Body model, which directly outputs 17 keypoints, provided an estimated 2x speedup with zero change to output format. The old slicing code (`kps[:, :17, :]`) was removed across both UCF and XD processing paths.

**The XD-Violence Label Discovery (Observation #458).** An initially puzzling bug showed zero anomalous videos in the XD-Violence training set. Three systematic debug scripts were created before the root cause was found: anomaly labels are encoded in *filenames* (`_label_A` = normal, `_label_B*`/`_label_G*` = anomalous), not in the annotation file, which only contains temporal frame-level annotations for a subset of test videos. This discovery unblocked correct stratified splitting (1,619 anomalous out of 3,360 training videos, 48%).

**The M=2 Person Input Requirement (Observation #429).** The CTR-GCN smoke test initially used M=1 (single person) synthetic input. Analysis of the checkpoint's `data_bn` BatchNorm layer revealed it expected exactly 102 input features (2 persons x 17 joints x 3 channels), meaning the NTU120 checkpoint requires M=2. Zero-padding the second person slot matched the training configuration. Without this discovery, the entire skeleton feature extraction pipeline would have produced garbage embeddings.

**Phase 4 UCF Results (Observation #829).** After weeks of infrastructure work, the empirical results arrived: Gated Fusion achieved 82.27% AUC on UCF-Crime, with skeleton-only at 71.80%, CLIP-only at 81.69%, and late fusion at 78.71%. The late fusion inversion (performing worse than CLIP-only by 3 points) empirically validated the thesis rationale for gated fusion over naive averaging. Three-seed stability was excellent at 0.29% standard deviation, well below the 0.5% threshold.

---

## 4. Work Patterns

The development rhythm reveals distinct modes of operation across the 33-day timeline.

**Intensive Planning Sprints.** March 31 stands out as the most front-loaded day: 86 observations, 436K tokens, laying the entire planning foundation in a single session. Similarly, April 15 was the most active day overall with 181 observations across training runs, evaluation harness construction, and empirical result collection.

**Multi-Day Extraction Marathons.** Feature extraction dominated April 3--8, with skeleton extraction running across multiple sessions while debugging infrastructure issues (cuDNN paths, checkpoint corruption, memory management). The XD-Violence extraction was estimated at 5--8 days for skeleton processing alone, with 99.3% of time spent on inference.

**Rapid Phase Execution.** Phase 3 (model architecture and training) and Phase 4 (evaluation) were executed in concentrated bursts. Phase 4's empirical runs completed in approximately 2 hours wall-clock, far faster than the 4--6 hour estimate, because models early-stopped at epochs 8--13.

**Debugging-then-Hardening Cycles.** A recurring pattern: encounter a bug, fix it, then immediately harden the fix across all related scripts. When atomic file writes were needed for extract_skeletons.py, the same fix was immediately applied to extract_ctrgcn.py and extract_clip.py. When line buffering was added for tqdm under conda, all three extraction scripts were updated simultaneously.

---

## 5. Technical Debt

Technical debt accumulated and was paid in identifiable cycles.

**The `strict=False` Debt.** Early checkpoint loading used `strict=False` with `model.load_state_dict()` to handle mismatched keys between the PYSKL checkpoint format (plain OrderedDict) and the expected wrapper format. While this worked, it silently accepts partial loads. The CLAUDE.md convention was updated to require `strict=True` with explicit key remapping when needed.

**The Validation Shuffle Debt.** Validation DataLoaders were configured with `shuffle=False` (observation #815), combined with sorted split files that group all normal videos together. This caused the `validate()` function to skip most single-class batches, meaning only ~19.8% of UCF validation videos contributed to early stopping. This was identified during a code review audit but represented a significant bias in checkpoint selection throughout Phase 4.

**The C3 Test False Positive.** The `test_no_test_split_access` test, designed to prevent test-set leakage (Pitfall C3), started failing when the evaluation harness (legitimately in `src/eval/`) referenced test split files. The test's blanket scanning of all `src/` files didn't distinguish between training-side code (where test access is leakage) and evaluation-side code (where it is necessary). This was confirmed as a pre-existing Phase 4 issue (observation #812), not introduced by Phase 4b.

**The Missing Error Logging Debt.** Analysis of extraction logs revealed that CLIP extraction had perfect error logging (100% correspondence between logged errors and missing files), while CTR-GCN skeleton extraction had 290 silent failures beyond 136 logged errors (observation #493). The 68% of skeleton failures that occurred without logging made diagnosis significantly harder.

---

## 6. Challenges and Debugging Sagas

**The PyTorch 1.12.1 DLL Saga (Phase 1, observations #394--#402).** The conda-installed PyTorch 1.12.1 failed with WinError 182 when loading `shm.dll`. Systematic diagnosis narrowed the actual failing component to `torch_cpu.dll` (not `shm.dll` -- that was a cascading dependency). Installing VS2019 runtime dependencies did not help. The resolution was switching from conda to pip wheels with explicit `+cu113` suffix, a workaround specific to Windows builds of legacy PyTorch versions. This consumed hours of diagnostic effort and established a critical lesson: use pip wheels, not conda packages, for PyTorch 1.12.1 on Windows.

**The 95-Minute Video Hang (Phase 2, observations #517--#520).** During XD-Violence skeleton extraction, the pipeline stalled for 11 hours despite showing high GPU usage. Investigation revealed the process was stuck on `NewAdd.Dream.Team.8__#1_label_A.mp4` -- a 94.9-minute, 136,704-frame video, vastly exceeding the typical 2--3 minute clips. The downstream queue contained more long videos (NBA game recordings at 21--31 minutes). This led to implementing checkpoint-based resume (saving progress after each 500-frame chunk) and the streaming architecture refactor, replacing batch frame loading with chunk-by-chunk processing that keeps RAM usage constant regardless of video length.

**The RTFM Reproduction Gap (Phase 4b, observation #828).** The RTFM XD-I3D gate achieved AP 0.6570 against a target of 0.7681 (11.11 percentage point shortfall). Extensive diagnostics were run: C4 sanity checks passed (snippet-to-frame expansion error only 0.0024), bag-size audits confirmed correct data shapes, and a Flow diagnostic rerun with 100% training data coverage produced *worse* results (AP 0.5916). The root cause was traced to fundamental training regime differences: RTFM's published code uses lr=1e-3 (10x higher), margin=100 on raw magnitudes (vs. 1.0 on sigmoid scores), batch_size=32 (vs. 3), and 2048-d 10-crop I3D features (vs. 1024-d 5-crop). Community reproductions (VadCLIP paper, GitHub issues) confirm 72--77% AP, calibrating the project's 65.70% as within the expected range for non-identical feature extraction.

---

## 7. Phase-by-Phase Progression

**Phase 1: Environment & Project Foundation** (March 31, 3 plans, completed same day). Established three conda environments, extracted XD-Violence datasets (3,954 train + 800 test videos), created NTFS junction for feature storage, downloaded CTR-GCN weights, and validated the backbone with a 4-check smoke test (shape, NaN, Inf, variance). Key discovery: CTR-GCN requires M=2 person input due to NTU120 training configuration.

**Phase 2: Feature Extraction Pipeline** (April 2--8, 4 plans). Built three extraction scripts spanning three environments: `extract_skeletons.py` (RTMPose), `extract_ctrgcn.py` (4-stream weighted fusion), and `extract_clip.py` (ViT-B/16 mean+max pooling). Created stratified splits with seed=42 reproducibility. Discovered XD-Violence filename-based labeling. Achieved 30x GPU speedup via cuDNN PATH fix. Implemented atomic writes, checkpoint resume, and streaming architecture for multi-day extraction robustness. UCF-Crime extraction completed (1,728 of 1,900 videos; 172 below 64-frame threshold). XD-Violence extraction remained ongoing.

**Phase 3: Model Architecture & Training Infrastructure** (April 13--14). Implemented MIL Ranking Loss, MILFeatureDataset with paired bag sampling, and four model variants (skeleton-only, CLIP-only, late fusion, gated fusion). GatedFusion architecture included three named LayerNorm layers (ln_skel, ln_clip, ln_fused) explicitly designed as the Phase 5 TTA adaptation surface. Established config-driven training with YAML configs, early stopping, and reproducibility via fixed seeds.

**Phase 4: Baseline Evaluation & Main Results** (April 14--16, 7 plans including UAT). Built evaluation harness with C3 test-leakage prevention (import-boundary isolation) and C4 off-by-one prevention (single `snippet_to_frame()` utility). Trained all four variants plus pooling ablations. Results: Gated Fusion 82.27% AUC (missed 83% target by 0.73 points, accepted), 3-seed std 0.29% (well below 0.5% threshold), per-category Fighting/Assault AUC exceeding 95%.

**Phase 4b: RTFM XD-I3D Gate** (April 15--16, 5 plans). Implemented xd_i3d training dispatch (parallel functions, not polymorphic), Wu XD annotation parser, and 5-crop collate. Gate result: AP 0.6570 vs. 0.7681 target. Flow diagnostic confirmed modeling capacity limitation, not data coverage. Accepted as thesis limitation.

**Phase 4c: XD-Violence Main Results** (April 26--30). Activated when XD features completed extraction. Trained all variants on XD-Violence: Gated Fusion achieved AP 71.92% at seed 42, 3-seed mean 70.97% +/- 1.08%. Per-category analysis showed strong Abuse detection.

**Phase 5: TTA Infrastructure & Corruption Experiments** (April 20--21). Planned and researched UCF-Crime-C corruption benchmark (4 types x 5 severities = 20 conditions). Ported TENT and SAR from official repository with key adaptations: LayerNorm targeting instead of BatchNorm, binary entropy loss instead of softmax entropy. Environment gap discovered: PIL and scipy absent from vcc-skeleton, requiring cv2-only corruption implementation.

**Phase 6: Analysis & Visualization** (May 1--2). Generated 17 thesis-quality PNG figures covering temporal anomaly score curves, TTA degradation analysis, ablation bar charts, and per-category breakdowns.

**Phase 7: XD-Violence Hyperparameter Sweep** (April 30--May 2). Planned and began executing 20-run lr x k_topk grid search to improve XD-Violence AP. RTFM reproduction gap diagnosis completed: traced to training regime differences (10x lr, 2x feature dimensionality, different margins).

---

## 8. Token Economics and Memory ROI

The claude-mem persistent memory system tracked ViolenceCC across **48 sessions** producing **744 observations** consuming **7,159,898 total discovery tokens**.

**Monthly Distribution:**
| Month | Observations | Discovery Tokens | Sessions |
|-------|-------------|-----------------|----------|
| March 2026 | 86 | 436,345 | 3 |
| April 2026 | 628 | 6,119,435 | 41 |
| May 2026 | 30 | 604,118 | 5 |

**Average tokens per observation:** 9,624 tokens. This represents the "learning cost" per discoverable fact -- each observation captures a decision, bug fix, feature, or architectural insight.

**Type Breakdown by Token Cost:**
| Type | Count | Total Tokens | Avg Tokens |
|------|-------|-------------|------------|
| discovery | 287 | 1,886,791 | 6,575 |
| change | 207 | 1,774,521 | 8,573 |
| feature | 132 | 1,542,866 | 11,688 |
| decision | 54 | 1,042,724 | 19,310 |
| bugfix | 59 | 825,991 | 13,983 |
| refactor | 5 | 87,005 | 17,401 |

The most expensive observation type is *decision* at 19,310 average tokens -- each architectural decision required extensive context exploration. The most expensive individual observation (#994, 112,755 tokens) was "UCF-Crime dataset complete structure documented," reflecting the cost of mapping a complex real-world dataset.

**Longest Sessions:**
| Session | Observations | Tokens |
|---------|-------------|--------|
| 8a12a96b | 108 | 492,346 |
| 5e1357ea | 93 | 999,961 |
| 17d49d0b | 72 | 455,703 |
| e8bf48fd | 61 | 184,313 |

Session `5e1357ea` was the most token-intensive (nearly 1M tokens) -- this was the Phase 4 empirical execution session that trained all variants, ran pooling ablations, computed 3-seed stability, and performed bit-identical rerun verification.

**Memory ROI.** The system's persistent memory provided measurable value in several dimensions. Cross-session context (the M=2 requirement, cuDNN PATH fix, XD-Violence filename labeling, checkpoint format discovery) was referenced in later sessions without re-discovery. The accumulated KEY DECISIONS table in STATE.md grew from 9 entries after Phase 1 to dozens by Phase 5, each preventing a potential re-investigation. The pitfall tracking system (C1--C5, M5--M7) provided specific prevention strategies that were validated empirically: C1 (coordinate normalization) was verified in the smoke test, C2 (temporal alignment) was prevented by the shared boundary JSON design, and M6 (SAR rho calibration) was addressed in the Phase 5 grid search design.

---

## 9. Timeline Statistics

- **Date range:** March 31 to May 2, 2026 (33 calendar days)
- **Total observations:** 744 across 48 sessions
- **Total discovery tokens:** 7,159,898
- **Most active day:** April 15 (181 observations) -- Phase 4 empirical execution
- **Second most active day:** April 14 (117 observations) -- Phase 3/4 model training
- **Third most active day:** March 31 (86 observations) -- Project genesis
- **Most active week:** April 13--16 (366 observations, 49% of all observations)
- **Longest session:** 108 observations (session 8a12a96b)
- **Most expensive session:** 999,961 tokens (session 5e1357ea)

**Type distribution:** discoveries dominate at 287 (38.6%), followed by changes at 207 (27.8%), features at 132 (17.7%), bugfixes at 59 (7.9%), decisions at 54 (7.3%), and refactors at 5 (0.7%).

**Phase distribution by observation density:**
- Phase 1 (Environment): ~95 observations across 1 day
- Phase 2 (Feature Extraction): ~220 observations across 6 days
- Phase 3 (Model Architecture): ~90 observations across 2 days
- Phase 4/4b (Evaluation): ~230 observations across 3 days
- Phase 5 (TTA): ~50 observations across 2 days
- Phase 6 (Visualization): ~30 observations across 2 days
- Phase 7 (Hyperparameter Sweep): ~30 observations across 2 days

---

## 10. Lessons and Meta-Observations

**Front-loading research pays exponential dividends.** The March 31 genesis session -- 86 observations before writing implementation code -- shaped every subsequent phase. The pitfall catalog prevented at least 5 confirmed bugs (C1 coordinate normalization, C2 temporal misalignment, C3 test leakage, checkpoint format, M=2 person requirement). The three-environment strategy, despite its complexity, prevented dependency conflicts that would have been far more expensive to debug at runtime.

**Windows is a hostile environment for ML research.** The project encountered Windows-specific issues at nearly every phase: PyTorch 1.12.1 DLL loading failures (WinError 182), cuDNN nested subdirectory paths, conda Unicode encoding errors (`cp950` codec), NTFS junction creation requiring PowerShell (not cmd.exe), and `conda run` output buffering preventing tqdm display. Each of these required workarounds that would not exist on Linux. The project adapted by embedding fixes directly into scripts (inline PATH modification, stream reconfiguration) rather than relying on environment configuration.

**Feature extraction dominates the timeline.** Of the 33-day project span, feature extraction (Phase 2 + ongoing XD-Violence processing) consumed the largest continuous block of engineering effort. The actual ML training and evaluation (Phases 3--4) completed in a fraction of the time. The 4,754-video XD-Violence dataset at ~66 seconds per video for skeleton extraction represents a fundamental bottleneck that no code optimization fully resolves -- it is inherently GPU-bound.

**Atomic file operations prevent multi-day heartbreak.** The switch to temp-file-then-rename for all extraction outputs (observations #557--558) was motivated by a concrete risk: a crash during `pickle.dump()` leaves a truncated file that the resume logic sees as complete, permanently corrupting that video's output across a multi-day extraction run. This defensive programming pattern was applied uniformly across all three extraction scripts.

**Accept and document failures, do not hide them.** The RTFM reproduction gap (65.70% vs. 77.81%) was not buried. It was systematically diagnosed (C4 sanity check, bag-size audit, Flow diagnostic rerun), calibrated against community reproductions (72--77%), traced to root causes (training regime differences), and formally accepted as a thesis limitation following a four-level fallback cascade. This honest documentation is more valuable to the thesis than an unexplained success.

**The GSD workflow provided structure without rigidity.** The phased GSD methodology (discuss, plan, execute, verify, complete) created natural checkpoints for quality control. Phase verification reports with formal checklists caught issues like the test regression from queue additions (observation #808). The ability to split phases (4 into 4b/4c) and run phases in parallel (5 independent of 4c) demonstrated the system's flexibility under real project pressures.

**Persistent memory is the solo researcher's multiplier.** With 48 sessions across 33 days, each session needed to pick up where the last left off. The STATE.md accumulated context table, the session continuity instructions, and the claude-mem observation database together provided the "institutional knowledge" that a team would normally hold across multiple people. A new developer could read the 742 observations and understand not just what was built, but *why* each decision was made and what alternatives were rejected.

---

*Report generated May 3, 2026. Covers observations #362 through #1234 across 48 development sessions.*
