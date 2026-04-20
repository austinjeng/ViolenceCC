# Phase 5: TTA Infrastructure & Corruption Experiments - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the UCF-Crime-C corruption benchmark (4 types x 5 severities = 20 conditions), implement TENT-style and SAR-style entropy-minimization TTA adapted for LayerNorm-based fusion heads, and evaluate across all 20 corruption conditions with full LR/rho grid search. The canonical adaptation target is `results/ucf_gated_fusion_s42/best_model.pth` (3 named LNs, 1536 adaptable params). Phase 5 is entirely UCF-Crime based — no XD-Violence dependencies. Cross-dataset TTA and EATA-style are stretch goals gated on XD features and timeline.

</domain>

<decisions>
## Implementation Decisions

### Corruption pipeline
- **D-01:** On-the-fly corruption during feature extraction. Add `--corruption {type} --severity {1-5}` flags to `extract_clip.py` and `extract_skeletons.py`. Apply transforms in memory; no stored corrupted video files (~200GB+ savings).
- **D-02:** Re-extract for **test-set only** (290 UCF-Crime test videos). TTA adapts and evaluates on test set; train/val features are unchanged. Total re-extraction budget: ~11h skeleton (10 conditions) + ~4h CLIP (20 conditions) = ~15h.
- **D-03:** Shared `scripts/corruption.py` module using only numpy + PIL + scipy (no PyTorch/kornia). Both `vcc-main` and `vcc-skeleton` environments can import it. Ensures bit-identical transforms across both extraction pipelines.
- **D-04:** Feature cache layout: `E:/features/ucf/clip_{type}_{severity}/` for CLIP, `E:/features/ucf/skeleton_{type}_{severity}/` for skeleton. 30 total directories (20 CLIP + 10 skeleton).

### TTA implementation
- **D-05:** Binary entropy loss for sigmoid MIL output: `H = -(s*log(s) + (1-s)*log(1-s))`, minimized over 32-snippet batch. Direct analog of TENT's softmax entropy for binary classification case.
- **D-06:** Port from official SAR repo (https://github.com/mr-eggplant/SAR, ICLR 2023 Oral, MIT License). Key adaptations: (1) `collect_params()` filters for `nn.LayerNorm` not `nn.BatchNorm2d`, (2) entropy loss uses binary entropy not softmax, (3) `reset()` reloads LN params from source checkpoint. SAR adds sharpness-aware gradient step + reliable entropy filtering.
- **D-07:** Online adapt+score per video. For each 32-snippet batch: forward → collect scores → compute entropy → backward → update LN params → next batch. Scores from each batch (using model state at that point) are collected. Matches PRD §10.3 "online update without revisiting processed batches." No second pass.
- **D-08:** Adaptable parameters: only LN affine (weight, bias) in GatedFusion — `ln_skel` (512 params), `ln_clip` (512 params), `ln_fused` (512 params) = **1536 total params**. All other model parameters frozen during adaptation. Per PRD §10.3.

### Experiment orchestration
- **D-09:** Extend existing `scripts/run_ablations.py` with TTA queue types: `tta_source_only` (20 runs), `tta_tent_grid` (80 runs), `tta_sar_grid` (400 runs). Same resume logic (`.done` markers), same `results-index.csv` append pattern.
- **D-10:** Full LR grid `{1e-4, 5e-4, 1e-3, 5e-3}` for all 20 conditions. Report best-per-condition LR in results table metadata. Also report whether a single LR dominates across conditions (thesis narrative simplification).
- **D-11:** SAR rho grid: `{0.001, 0.005, 0.01, 0.05, 0.1}`. Includes ImageNet default (0.05-0.1) for empirical validation of Pitfall M6 (expected to underperform vs smaller values on scalar output).
- **D-12:** Primary metric: frame-level AUC (ROC-AUC), consistent with Phase 4 main results. Results table format: `| Type | Sev | Source-Only AUC | TENT AUC (Δ) | SAR AUC (Δ) |` with summary row (mean ΔAUC across all 20 conditions).
- **D-13:** TTA run output directory: `results/tta/{method}_{type}_{severity}_lr{lr}[_rho{rho}]/` containing `eval_metrics.json`, `eval_scores.npz`, `.done` marker. Source-Only runs at `results/tta/source_only_{type}_{severity}/`.
- **D-14:** Each TTA evaluation is feature-level only (no video decoding), estimated ~30s per run. Full grid: ~180 TENT + ~400 SAR + 20 Source-Only = ~600 runs × 30s = ~5 hours total evaluation time.

### Scope and scheduling
- **D-15:** Phase 5 proceeds independently of Phase 4c (XD main results). Zero XD dependencies. Phase 4c activates when XD features land.
- **D-16:** Cross-dataset TTA (OPT-03) = **stretch goal**. Planned in CONTEXT but not in the main plan. Execute only if: (a) corruption TTA finishes on schedule, (b) XD features are complete, (c) Phase 4c has produced an XD source model.
- **D-17:** EATA-style TTA = **stretch goal**. Execute only after TENT + SAR deliver positive results and timeline has slack. Adds Fisher Information Matrix computation (~3 days).
- **D-18:** Estimated Phase 5 timeline: ~1 week (corruption module + re-extraction: 2 days; TENT/SAR implementation: 2 days; evaluation grid: 1 day; analysis + verification: 1 day).

### Claude's Discretion
- Corruption severity value refinement per ImageNet-C conventions (monotonic degradation preferred over mixed direction)
- SAR reliable entropy filtering threshold calibration
- Whether `scripts/corruption.py` lives in `scripts/` or `src/` (recommendation: `scripts/` since it's used by extraction scripts, not training code)
- Exact binary entropy numerical stability handling (epsilon clamping on sigmoid outputs)
- Whether to report per-video TTA entropy curves in eval output (useful for M5 analysis but adds storage)
- TTA results CSV column ordering and additional metadata fields
- Whether Source-Only runs go through the TTA evaluation loop (with 0 adaptation steps) or call `evaluate.py` directly (former is cleaner for fair comparison)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and specifications
- `.planning/REQUIREMENTS.md` — TTA-01 through TTA-07 formal requirements for this phase
- `thesis_prd_v2.3.md` §10.1 — TTA positioning as "deployment robustness study" (not life-or-death)
- `thesis_prd_v2.3.md` §10.2 — Method selection table (TENT-style baseline, SAR-style primary)
- `thesis_prd_v2.3.md` §10.3 — Adaptation protocol (locked): LN affine params only, 32-snippet batches, per-video reset, LR grid {1e-4, 5e-4, 1e-3, 5e-3}
- `thesis_prd_v2.3.md` §10.4 — Corruption-based TTA experiment protocol (4 types × 5 severities = 20 conditions)
- `thesis_prd_v2.3.md` §10.5 — Five-step TTA flow (TRAIN → FREEZE → ADAPT → EVALUATE → COMPARE)

### Prior phase context
- `.planning/phases/03-model-architecture-training-infrastructure/03-CONTEXT.md` — D-07 (LN placement: 3 named LNs in GatedFusion for TTA surface), D-05/D-06 (MILHead architecture: no LN in head itself)
- `.planning/phases/04-baseline-evaluation-main-results/04-CONTEXT.md` — D-30 (deterministic run-dir naming), D-31 (`.done` marker resume logic), D-33 (`results-index.csv` append pattern)
- `src/models/gated_fusion.py` — Lines 12-15: LN inventory (ln_skel, ln_clip, ln_fused); Lines 29-33: class docstring confirming direct attribute exposure for TTA

### Pitfalls
- `.planning/research/PITFALLS.md` — M5 (TTA entropy collapse on normal-heavy batches: SAR gradient filtering mitigates), M6 (SAR rho ImageNet default too large for scalar output: grid from 0.005), M7 (skeleton re-extraction needed for motion blur + JPEG corruption only)

### Reference implementations
- SAR repo: https://github.com/mr-eggplant/SAR — Official TENT + SAR implementation (ICLR 2023 Oral, MIT License). Contains `tent.py` and `sar.py` to port.
- ImageNet-C: https://github.com/hendrycks/robustness — Corruption generation reference (4 noise types inspired by this benchmark)

### Existing code (TTA target)
- `results/ucf_gated_fusion_s42/best_model.pth` — Canonical adaptation source checkpoint (verified: `.done` marker present, 2MB)
- `results/ucf_gated_fusion_s42/config_snapshot.json` — Config for rebuilding the model architecture
- `src/tta/__init__.py` — Phase 5 placeholder (currently empty docstring)
- `scripts/run_ablations.py` — Existing runner to extend with TTA queues
- `scripts/extract_clip.py` — CLIP extraction script to add `--corruption` flag
- `scripts/extract_skeletons.py` — Skeleton extraction script to add `--corruption` flag

### Project state
- `.planning/STATE.md` — Phase 4b complete, Phase 4c blocked on XD features, Phase 5 can proceed
- `.planning/ROADMAP.md` — Phase 5 depends on Phase 4 (complete), not Phase 4c

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/models/gated_fusion.py` — 3 named LNs (`ln_skel`, `ln_clip`, `ln_fused`), each `nn.LayerNorm(256)`. Directly accessible as attributes for TTA param collection.
- `scripts/run_ablations.py` — Queue-based runner with `.done` marker resume, `results-index.csv` append. Extend with TTA queues.
- `src/eval/snippet_to_frame.py` — Frame-level score expansion. Reuse as-is for TTA evaluation.
- `src/evaluate.py` — Evaluation CLI (`--run-dir`, `--split test`). TTA evaluation adapts this pattern but adds adaptation loop before scoring.
- `scripts/extract_clip.py` — CLIP feature extraction at 1 FPS. Add `--corruption` + `--severity` flags for on-the-fly transform.
- `scripts/extract_skeletons.py` — RTMPose skeleton extraction. Add same corruption flags for motion blur + JPEG conditions.
- `src/utils/checkpoint.py` — Atomic save pattern. Reuse for TTA `.done` markers.
- `configs/gated_fusion.yaml` — Config for the canonical s42 model (TTA loads this via `config_snapshot.json`).

### Established Patterns
- Queue-based experiment runner with `.done` resume (Phase 4 D-31)
- Deterministic output directories (Phase 4 D-30): extend to `results/tta/` subtree
- `results-index.csv` append-only audit log (Phase 4 D-33): add TTA-specific columns (method, lr, rho, corruption_type, severity)
- Feature cache per video as `[N, D]` float32 .npy (Phase 1 D-06): corrupted features follow same convention
- Scripts vs src split (Phase 1 D-02): `scripts/corruption.py` (extraction-time utility), `src/tta/tent.py` + `src/tta/sar.py` (training-env modules)

### Integration Points
- **Reads:** `results/ucf_gated_fusion_s42/best_model.pth` + `config_snapshot.json` (source model), `E:/features/ucf/{clip,skeleton}_{type}_{sev}/*.npy` (corrupted features), `data/splits/ucf_test.txt`, `data/annotations/ucf_temporal.txt`
- **Writes:** `E:/features/ucf/clip_{type}_{sev}/`, `E:/features/ucf/skeleton_{type}_{sev}/` (corrupted feature caches), `results/tta/*/eval_metrics.json` + `eval_scores.npz` + `.done`, `results/results-index.csv` (TTA rows appended)
- **Phase 6 consumes:** `results/tta/*/eval_scores.npz` for temporal curve visualization under corruption; `results/results-index.csv` for thesis table generation

</code_context>

<specifics>
## Specific Ideas

- The BN→LN adaptation transfer is itself a research contribution (PRD §10.2 note). The binary entropy formulation is novel relative to standard TENT (softmax entropy). Document this clearly in the thesis methodology.
- The 1536-param adaptation surface is deliberately small (3 LNs × 256-d × 2 affine). PRD §9.4 acknowledges this may limit TTA effectiveness — if so, it's a "valuable finding" per PRD, not a failure.
- Source-Only runs should go through the same TTA evaluation loop with 0 adaptation steps (same forward path, same chunking) for fair comparison. This isolates the adaptation effect from any differences in evaluation pipeline.
- The SAR rho grid including ImageNet default {0.05, 0.1} empirically validates Pitfall M6 — expect underperformance at these values, which strengthens the thesis narrative about adapting hyperparameters for the anomaly detection domain.
- Corruption re-extraction should use a fixed seed for numpy random (noise generation) to ensure reproducibility. Document the seed in the corruption module.
- Per-video entropy curves (entropy at each adaptation step) would be valuable for M5 analysis (normal-heavy batch collapse). Consider saving these alongside `eval_scores.npz` if storage permits.

</specifics>

<deferred>
## Deferred Ideas

- **Cross-dataset TTA (OPT-03):** UCF→XD and XD→UCF directions. Stretch goal for Phase 5. Requires XD features complete + Phase 4c source model. If activated, add `tta_cross_dataset` queue to runner.
- **EATA-style TTA:** Selective update + Fisher regularization (PRD "有餘力再做" tier). Stretch goal. Requires Fisher Information Matrix computation over training set. ~3 days additional work.
- **TTA on XD-Violence corruption (XD-Violence-C):** Parallel to UCF-Crime-C but for the other dataset. Deferred until Phase 4c completes and XD model exists.
- **Per-video adaptation analysis:** Visualize how LN params evolve across batches within a single long video. Phase 6 analysis material.
- **Adaptation parameter count ablation:** Test TTA with only 1 LN adapted vs all 3. Would show whether ln_fused alone is sufficient or all 3 are needed. Thesis discussion material.
- **CLIP text prompt engineering + TTA (OPT-12):** Combining text-guided CLIP features with TTA. v2 scope.

</deferred>

---

*Phase: 05-tta-infrastructure-corruption-experiments*
*Context gathered: 2026-04-20*
