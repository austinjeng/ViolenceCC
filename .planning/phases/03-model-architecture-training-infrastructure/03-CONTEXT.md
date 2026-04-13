# Phase 3: Model Architecture & Training Infrastructure - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Build all four MIL model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) and a single configurable `train.py` that trains any of them to convergence on the cached features produced by Phase 2. Reproducibility is hardened: bit-identical loss curves under fixed seed, config snapshot saved alongside every checkpoint, early stopping on val MIL Ranking Loss. The phase produces `best_model.pth` + `last_model.pth` + `train_log.csv` + `config_snapshot.json` per run, plus a model registry and addressable `nn.LayerNorm` layers that downstream Phase 4 evaluation and Phase 5 TTA depend on. Evaluation harness (frame-level AUC/AP, RTFM reproduction) belongs to Phase 4.

</domain>

<decisions>
## Implementation Decisions

### MIL Loss
- **D-01:** Top-k = 3 for top-k MIL ranking. RTFM and MGFN convention; consistent across the literature for T=32 snippets.
- **D-02:** Hinge margin = 1.0 in `max(0, margin − mean_topk_abnormal + mean_topk_normal)`. RTFM/MGFN/PEL4VAD default.
- **D-03:** Add RTFM-style sparsity (`λ_sparse=8e-3` on L1 of all snippet scores within abnormal bags) and smoothness (`λ_smooth=8e-4` on L2 of adjacent-snippet score differences within each bag) regularizers. Mitigates Pitfall C5 (training collapse) and produces the temporally-coherent score curves Phase 6 visualization needs.
- **D-04:** Bag construction: `batch_size=32` per PRD §11.1 means **32 videos per batch = 16 normal + 16 abnormal forming 16 ranking pairs** (RTFM convention). Pairing by index within shuffled normal/abnormal queues.

### MIL Head Architecture
- **D-05:** Score head is a 3-layer MLP applied uniformly across all variants: `Linear(D→128) → ReLU → Dropout(0.3) → Linear(128→32) → ReLU → Dropout(0.3) → Linear(32→1) → Sigmoid`. RTFM convention.
- **D-06:** Hidden width 128 → 32 (RTFM/MGFN default). Reused across all 4 variants — head differences are zero by construction, so ablations isolate fusion/modality effects.
- **D-07:** LayerNorm placement: after **every** modality projection (`skel_proj → LN`, `clip_proj → LN`) **and** at fusion output (`F_fused → LN`). Yields ~4-5 LN layers in Gated Fusion, providing meaningful TTA surface for Phase 5. Mitigates the failure mode PRD §9.4 explicitly warns about ("theoretically TTA, practically nothing to adapt").
- **D-08:** Module organization: shared `MILHead(input_dim, hidden_dims, dropout)` class reused by all variants; per-variant backbone wrappers `SkeletonProj`, `CLIPProj`, `LateFusion`, `GatedFusion` live in `src/models/`. CLIP-Only includes the learned `Linear(1024 → 512)` projection inside `CLIPProj` (per Phase 2 D-06).

### Data Loader Sampling
- **D-09:** Training-time sampling for videos with N > 32 snippets: **uniform 32-segment sub-sample**. Divide N snippets into 32 contiguous segments, pick one snippet per segment (random within segment). RTFM convention; preserves full-video temporal coverage.
- **D-10:** Training-time padding for videos with N < 32 snippets: **zero-pad with attention mask**. Append zero feature vectors; mask zero positions out of the MIL top-k selection so they cannot be the "top". 172 UCF videos with 0 snippets are dropped from splits at load time (per Phase 2 UAT note).
- **D-11:** Multi-person aggregation and CLIP pooling ablations (REQ EVAL-04, PRD §12.3) — **deferred to Phase 4**. Phase 3 trains on the existing `[N,256]` M-pooled skeleton + `[N,1024]` mean+max CLIP cache as-is. Phase 4 plan must include re-extraction passes with `--keep-persons` (skeleton) and `--pool=mean` (CLIP) flags.
- **D-12:** Test-time evaluation: **score every snippet** (no T=32 sampling). Forward each snippet (batched) producing one score per snippet, broadcast to frame level for AUC/AP. Required for accurate frame-level metrics against ground-truth temporal annotations (Pitfall C4 prevention).

### Tracking & Artifacts
- **D-13:** Experiment tracking: **wandb** (free for academic use). YAML config gains `wandb.entity` and `wandb.project` fields. Online sync survives crashes; sweep view aggregates the 8-entry ablation table and 3-seed reruns. Run names mirror `D-14`. CSV logging per TRN-04 stays as the offline source-of-truth for thesis tables.
- **D-14:** Results directory layout: `results/{dataset}_{variant}_{seed}_{timestamp}/` — e.g. `results/ucf_gated_fusion_42_20260420-153000/`. Each run dir contains `config_snapshot.json`, `train_log.csv`, `best_model.pth`, `last_model.pth`. Phase 4 writes `eval_metrics.json` into the same dir.
- **D-15:** Checkpoint policy: **`best_model.pth` (lowest val MIL loss) + `last_model.pth` (final epoch)**. ~14 MB each. `last` enables resume after crash; `best` is what Phase 4 evaluation and Phase 5 TTA load.
- **D-16:** Variant selection: **string registry pattern**. YAML field `model.variant: gated_fusion | late_fusion | clip_only | skeleton_only` mapped via `src/models/registry.py` to model class. Human-readable, greppable, no import-string brittleness; matches single-`train.py` requirement (TRN-06).

### Claude's Discretion
- Activation choice in MLP heads (default ReLU; switch to GELU only if collapse observed)
- Validation cadence (default every epoch — TRN-04 requires per-epoch CSV log)
- Strictness of `torch.use_deterministic_algorithms(True)` — fall back to non-deterministic kernel for ops without deterministic implementation, log a warning. Cost: ~10-20% throughput, acceptable per success criterion #4.
- Gradient clipping (off by default; enable only if Gated Fusion shows instability)
- AMP/mixed precision (off — feature-level training is memory-trivial; AMP adds nondeterminism risk that conflicts with bit-identical reproducibility goal)
- Snippet shuffling within a bag (off — preserve temporal order so smoothness regularizer is well-defined)
- Exact LayerNorm naming convention (suggested: `ln_skel`, `ln_clip`, `ln_fused`; required: discoverable via `model.named_modules()` for Phase 5 TTA targeting)
- Exact wandb project/entity strings (default project: `violencecc`, entity: user-configurable via env var `VIOLENCECC_WANDB_ENTITY`; allow `wandb.mode=disabled` for CI/offline)
- Pin-memory / num-workers settings for the DataLoader (default: `num_workers=4, pin_memory=True` on Windows; reduce if file-handle issues observed)
- Late Fusion combination: equal-weighted scalar mix `(s_skel + s_clip)/2` as default; learned scalar `α∈[0,1]` if equal weighting underperforms either single-modal baseline

### Folded Todos
None — no pending todos matched Phase 3.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and specifications
- `.planning/REQUIREMENTS.md` — MOD-01 through MOD-07, TRN-01 through TRN-06 formal requirements for this phase
- `thesis_prd_v2.3.md` §9.2 — Gated Fusion module spec (256-d shared, sigmoid gate, LayerNorm + Dropout 0.3 + residual)
- `thesis_prd_v2.3.md` §9.4 — TTA-friendly architecture trade-off (justifies LN placement decision D-07)
- `thesis_prd_v2.3.md` §11.1 — Training hyperparameter table (AdamW, lr=1e-4, batch=32, 50 epochs, warmup+cosine)
- `thesis_prd_v2.3.md` §11.2 — Validation / early-stopping protocol (monitor val MIL Ranking Loss only)
- `thesis_prd_v2.3.md` §12.3 — Required ablation list (multi-person aggregation + CLIP pooling deferred to Phase 4)
- `thesis_prd_v2.3.md` §10.3 — TTA adaptation protocol (defines LN-only TTA targets that Phase 3 architecture must support)

### Prior phase context
- `.planning/phases/01-environment/1-CONTEXT.md` — D-02 (script vs src split, single train.py in vcc-main env), D-03 (flat YAML configs), D-05/D-06 (weight + feature paths), D-08 (manual env setup)
- `.planning/phases/02-feature-extraction-pipeline/02-CONTEXT.md` — D-01/D-02/D-03 (snippet definitions, T=32 resampling lives in Phase 3 loader), D-09/D-10/D-11/D-12 (val splits, seed=42, split file format)

### Pitfalls and architecture
- `.planning/research/PITFALLS.md` — C3 (test-set leakage prevention), C4 (off-by-one in snippet→frame expansion — informs D-12), C5 (MIL training collapse — D-03 regularizers mitigate), M5 (TTA entropy collapse — informs D-07 LN placement)
- `.planning/research/ARCHITECTURE.md` — 3-stage pipeline, build order tiers 2-3, single-train.py pattern
- `.planning/research/SUMMARY.md` — RTFM gating role for Phase 4, late-before-gated build order, val-split discipline
- `.planning/research/STACK.md` — wandb / tensorboard versions, PyTorch 2.6 + open-clip-torch 3.3.0 in vcc-main env

### Project state
- `.planning/STATE.md` — Phase 2 UAT status (UCF complete 1728/1900; XD extraction in flight ~5-8 days), 172 sub-64-frame UCF videos to skip in data loader

### Reference implementations
- RTFM repo: https://github.com/tianyu0207/RTFM — top-k MIL loss, sparsity / smoothness regularizers, 32-segment sampling. Convention source for D-01..D-04, D-09. Phase 4 reproduces this codebase against I3D features for the EVAL-01 gate.
- MGFN repo: https://github.com/carolchenyx/MGFN — same MIL convention; useful cross-reference for top-k value and margin defaults
- VadCLIP repo: https://github.com/nwpu-zxr/VadCLIP — CLIP ViT-B/16 + MIL head reference for CLIP-Only baseline implementation patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `data/splits/{ucf,xd}_{train,val,test}.txt` — stratified splits ready (UCF: 1368/242/290; XD: 3360/594/800), seed=42
- `E:/features/ucf/skeleton/*.npy` — 1728 files, `[N,256]` float32, M-pool already done in extraction
- `E:/features/ucf/clip/*.npy` — 1728 files, `[N,1024]` float32, mean+max pool
- `E:/features/xd/{skeleton,clip}/*.npy` — 3 smoke files; full XD extraction in flight, expected complete in ~5-8 days
- `scripts/verify_alignment.py` — pattern for safe `.npy` load + shape check (reuse for data loader unit tests)
- `src/{data,models,losses,tta,utils}/__init__.py` — empty package skeletons ready for imports
- `tests/conftest.py` — `splits_dir` fixture (extend with `feature_dir` fixture for Phase 3 data-loader tests)
- `data/weights/ctrgcn/` — CTR-GCN weights present (frozen, not loaded by Phase 3 — used by Phase 2 extraction only)

### Established Patterns
- Scripts vs src split (Phase 1 D-02): training entry `src/train.py` runs in `vcc-main` env
- Flat YAML config per variant (Phase 1 D-03): `configs/skeleton_only.yaml`, `configs/clip_only.yaml`, `configs/late_fusion.yaml`, `configs/gated_fusion.yaml`. Phase 4 adds `configs/rtfm_baseline.yaml`.
- Skip-if-exists resume (Phase 2 D-14): apply to per-run output-dir creation so resumed runs do not silently overwrite
- Float32 `.npy` storage (Phase 1 D-06): data loader uses `np.load(path)` directly; cast safety only if mixed dtypes ever arise
- Test pattern: pytest with `PROJECT_ROOT` fixture in `tests/conftest.py`

### Integration Points
- Reads: `data/splits/*.txt`, `E:/features/{ucf,xd}/{skeleton,clip}/*.npy`
- Writes: `results/{dataset}_{variant}_{seed}_{timestamp}/best_model.pth` + `last_model.pth` + `config_snapshot.json` + `train_log.csv`
- Phase 4 evaluation consumes: `results/{run}/best_model.pth`, the `MODEL_REGISTRY` for variant lookup, full-video test-time scoring path (D-12)
- Phase 5 TTA consumes: `model.named_modules()` traversal to collect `nn.LayerNorm` instances, `best_model.pth` as the per-video reset state

</code_context>

<specifics>
## Specific Ideas

- 4-5 LayerNorm layers in Gated Fusion is a deliberate Phase 5 enabler — small head with single LN risks the "nothing to adapt" failure mode (PRD §9.4)
- Smoothness regularizer requires temporal order in bags → the data loader must NOT shuffle snippets within a bag, only shuffle the bag-level pair order across batches
- Late Fusion is the 2-hour pipeline-validation step (Phase 1 D-10 + research SUMMARY) — build it first to validate full train→checkpoint→reload path before adding Gated Fusion complexity
- The model registry should make swapping variants a one-line YAML change so the 8-entry ablation table can be generated with minimal config-file divergence
- For the RTFM baseline reproduction (Phase 4), the same MIL Ranking Loss conventions captured in D-01..D-04 should apply — ensures the comparison is "fusion architecture" not "loss formulation"
- Bit-identical reproducibility (success criterion #4) requires fixed seeds + `torch.use_deterministic_algorithms(True)` + `cudnn.deterministic=True` + `cudnn.benchmark=False` — accept the throughput cost

</specifics>

<deferred>
## Deferred Ideas

- Multi-person aggregation ablation (concat vs max vs mean pooling over the 2 person slots) — Phase 4: re-extract a `[N, 2, 256]` cache with `--keep-persons` flag added to `extract_ctrgcn.py`
- CLIP pooling ablation (mean only vs mean+max) — Phase 4: re-extract a `[N, 512]` cache with `--pool=mean` flag added to `extract_clip.py`
- Cross-Attention Fusion module (PRD §9.3) — only if Gated Fusion stable AND Week 5-6 has slack (OPT-02)
- AMP / mixed-precision training — not justified at feature-level memory cost; nondeterminism risk conflicts with reproducibility goal
- Gradient clipping — enable only if Gated Fusion shows training instability; not the default
- BCE auxiliary head — not in PRD scope; revisit only if MIL-Ranking-only training collapses despite D-03 regularizers
- val-set frame-level AUC monitoring — val split has no frame-level labels per PRD §11.2; only MIL loss is monitorable

### Reviewed Todos (not folded)
None — no pending todos matched Phase 3.

</deferred>

---

*Phase: 03-model-architecture-training-infrastructure*
*Context gathered: 2026-04-14*
