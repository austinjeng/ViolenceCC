# Phase 3: Model Architecture & Training Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `03-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-04-14
**Phase:** 03-model-architecture-training-infrastructure
**Areas discussed:** MIL loss specifics, MIL head architecture, Data loader sampling, Tracking & artifacts

---

## MIL Loss Specifics

### Q1 — Top-k value for MIL Ranking Loss

| Option | Description | Selected |
|--------|-------------|----------|
| k=3 | RTFM and MGFN convention. Robust default for T=32 snippets. Easiest cross-paper comparison. | ✓ |
| k=ceil(T/16)=2 | RTFM-original adaptive formula at T=32. Slightly more conservative. | |
| k=5 | Larger top-k smooths gradient. Risks diluting the violence signal. | |

**User's choice:** k=3 (Recommended)

### Q2 — Hinge margin (epsilon)

| Option | Description | Selected |
|--------|-------------|----------|
| margin=1.0 | RTFM, MGFN, PEL4VAD all use 1.0. Default for sigmoid-output anomaly scores in [0,1]. | ✓ |
| margin=0.5 | Smaller margin trains easier but may saturate. | |
| margin=2.0 | Wider margin pushes harder separation. Risk of unstable gradients early. | |

**User's choice:** margin=1.0 (Recommended)

### Q3 — RTFM-style sparsity + smoothness regularizers

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — both regularizers | RTFM-faithful. Sparsity prevents collapse (C5); smoothness gives temporally coherent score curves. | ✓ |
| Hinge only (no extras) | Cleaner methodology, isolates ranking loss effect. Higher collapse risk. | |
| Sparsity only (no smoothness) | Catches collapse without forcing temporal smoothing. Curves may be noisier. | |

**User's choice:** Yes — both regularizers (λ_sparse=8e-3, λ_smooth=8e-4)

### Q4 — Bag construction per batch

| Option | Description | Selected |
|--------|-------------|----------|
| 32 bags = 16 normal + 16 abnormal pairs | RTFM convention. batch_size=32 means 32 videos per batch yielding 16 ranking pairs. | ✓ |
| 32 pairs = 32 normal + 32 abnormal (64 bags) | More gradient signal. Diverges from RTFM — harder direct comparison. | |
| 16 bags = 8+8 pairs | Halves throughput. Useful only if Gated Fusion shows instability at larger batches. | |

**User's choice:** 32 bags = 16 N/A pairs (Recommended)

---

## MIL Head Architecture

### Q1 — Score head depth

| Option | Description | Selected |
|--------|-------------|----------|
| 3-layer MLP: D→128→32→1 | RTFM convention. Strong baseline, matches gating reproduction target. | ✓ |
| 2-layer MLP: D→128→1 | Simpler; faster training. Less expressive. | |
| Single linear: D→1 | Maximally simple. Risks underfitting on CLIP-Only. | |

**User's choice:** 3-layer MLP D→128→32→1 (Recommended)

### Q2 — Hidden width for MLP

| Option | Description | Selected |
|--------|-------------|----------|
| 128 → 32 | RTFM/MGFN default. Memory-trivial at feature level. | ✓ |
| 256 → 64 | Slightly more capacity. Risks overfitting on small UCF training set. | |
| 64 → 16 | Tighter, more regularized. Better only if larger heads collapse. | |

**User's choice:** 128 → 32 (Recommended)

### Q3 — LayerNorm placement

| Option | Description | Selected |
|--------|-------------|----------|
| After every projection + fusion output | LN on each modality projection and at fused output. ~4-5 LN layers — meaningful TTA surface for SAR/TENT. | ✓ |
| Only at fusion output (PRD literal) | Strictly follows PRD §9.2 wording. Minimal TTA surface — risks PRD §9.4 failure mode. | |
| Only on input projections | Normalize before fusion; no post-fusion LN. Less standard. | |

**User's choice:** After every projection + fusion output (Recommended)

### Q4 — Module organization

| Option | Description | Selected |
|--------|-------------|----------|
| Shared MILHead class + 4 backbone wrappers | One MILHead reused by all variants. Cleaner ablation — head differences zero by construction. | ✓ |
| Separate head class per variant | More explicit; duplicates code. Harder to ensure ablation cleanliness. | |
| Single monolithic Model class with mode flag | Smallest file count. Mode-flag branching gets ugly. | |

**User's choice:** Shared MILHead class + per-variant backbone wrappers (Recommended)

---

## Data Loader Sampling

### Q1 — Sampling for N > 32 snippets

| Option | Description | Selected |
|--------|-------------|----------|
| Uniform 32-segment sub-sample | Divide N snippets into 32 contiguous segments, pick one per segment. RTFM convention. | ✓ |
| Random consecutive 32-snippet window | Easier; preserves local temporal structure. May miss anomalies entirely. | |
| Random 32-snippet sample (no order) | Maximum diversity. Breaks smoothness regularizer — incompatible with our loss. | |

**User's choice:** Uniform 32-segment sub-sample (Recommended)

### Q2 — Padding for N < 32 snippets

| Option | Description | Selected |
|--------|-------------|----------|
| Pad with zeros + attention mask | Append zero feature vectors; mask zero positions out of MIL top-k. | ✓ |
| Loop (cyclic repeat) until 32 | Simpler; no masking. Inflates duplicates which biases top-k. | |
| Drop video from training | Aggressive — may remove too much training signal. | |

**User's choice:** Zero-pad + attention mask (Recommended)

### Q3 — Multi-person & CLIP-pooling ablations

| Option | Description | Selected |
|--------|-------------|----------|
| Defer ablation re-extractions to Phase 4 | Phase 3 trains on current cache. Ablations re-extract in Phase 4 with extractor flags. | ✓ |
| Re-extract per-person + CLIP-mean caches now | Front-loads everything. Adds ~10-20h re-extraction to Phase 3 critical path. Risky. | |
| Drop ablations entirely | Saves time but skips REQ EVAL-04. Weakens thesis. | |

**User's choice:** Defer to Phase 4 (Recommended)

### Q4 — Test-time evaluation pass

| Option | Description | Selected |
|--------|-------------|----------|
| Score every snippet, no T=32 sampling | RTFM/MGFN convention. Required for accurate frame-level AUC vs ground-truth temporal annotations. | ✓ |
| Same T=32 sampling as training | Faster but loses snippets — wrong for the metric. | |

**User's choice:** Score every snippet (Recommended)

---

## Tracking & Artifacts

### Q1 — Experiment tracking tool

| Option | Description | Selected |
|--------|-------------|----------|
| wandb | Free academic; built-in sweep/comparison views; survives crashes via online sync. | ✓ |
| TensorBoard local only | Built into PyTorch; no external account. Weaker for cross-run comparisons. | |
| CSV + stdout only | Minimum viable per TRN-04. Manual aggregation gets painful. | |
| wandb + CSV both | Belt-and-suspenders. | |

**User's choice:** wandb (Recommended). Note: CSV per TRN-04 stays as offline source-of-truth alongside wandb.

### Q2 — results/ directory layout

| Option | Description | Selected |
|--------|-------------|----------|
| results/{dataset}_{variant}_{seed}_{timestamp}/ | Self-describing. Sortable, no collisions across re-runs. | ✓ |
| results/{variant}/{dataset}/seed{N}/ | Hierarchical by experiment dimension. Re-runs collide unless suffixed. | |
| results/{user_provided_name}/ | Free-form via --run-name. Risk of inconsistent naming. | |

**User's choice:** results/{dataset}_{variant}_{seed}_{timestamp}/ (Recommended)

### Q3 — Checkpoint policy

| Option | Description | Selected |
|--------|-------------|----------|
| best_model.pth + last_model.pth | best = lowest val MIL loss; last = final epoch. ~14 MB each, trivial. | ✓ |
| best_model.pth only | Saves disk. No resume-from-crash safety. | |
| Every epoch | 50 × 14 MB ≈ 700 MB per run. Pointless given early-stopping discipline. | |

**User's choice:** best_model.pth + last_model.pth (Recommended)

### Q4 — Variant selection in train.py

| Option | Description | Selected |
|--------|-------------|----------|
| String registry: model.variant = 'gated_fusion' | YAML stays human-readable. src/models/registry.py maps strings to classes. | ✓ |
| Import path: model.class = 'src.models.GatedFusion' | Couples YAML to file structure — renames break configs silently. | |
| Per-variant train script | Diverges from REQ TRN-06 "single train.py entry point". | |

**User's choice:** String registry (Recommended)

---

## Claude's Discretion

The user explicitly chose all "Recommended" defaults, so the following downstream-implementation choices remain at Claude's discretion within Phase 3 plan:

- Activation choice in MLP heads (default ReLU; switch to GELU only if collapse observed)
- Validation cadence (default every epoch)
- Strictness of `torch.use_deterministic_algorithms(True)` — fall back to non-deterministic kernel for ops without deterministic implementation, log a warning
- Gradient clipping (off by default; enable only if Gated Fusion shows instability)
- AMP / mixed-precision training (off — feature-level training is memory-trivial; AMP adds nondeterminism risk)
- Snippet shuffling within a bag (off — preserve temporal order for smoothness regularizer)
- Exact LayerNorm naming convention (suggested: `ln_skel`, `ln_clip`, `ln_fused`; required: discoverable via `model.named_modules()`)
- Exact wandb project/entity strings (default project: `violencecc`, entity configurable via env var; allow `wandb.mode=disabled`)
- DataLoader pin-memory / num-workers settings (default: `num_workers=4, pin_memory=True`)
- Late Fusion combination weight (default equal-weighted scalar mix; learned scalar α only if equal weighting underperforms)

## Deferred Ideas

Captured in `03-CONTEXT.md` `<deferred>` section. Summary:

- Multi-person aggregation ablation → Phase 4 re-extraction
- CLIP pooling ablation → Phase 4 re-extraction
- Cross-Attention Fusion (PRD §9.3) → OPT-02, only if Week 5-6 slack
- AMP / gradient clipping → not the default; revisit only if instability
- BCE auxiliary head → not in PRD scope
- val frame-level AUC → impossible (val has no frame labels per PRD §11.2)

No pending todos matched Phase 3 — none folded, none deferred.
