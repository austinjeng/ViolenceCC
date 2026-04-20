# Phase 5: TTA Infrastructure & Corruption Experiments - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-20
**Phase:** 05-tta-infrastructure-corruption-experiments
**Areas discussed:** Corruption pipeline, TTA implementation, Experiment orchestration, Phase 5 scope boundary

---

## Corruption Pipeline

### How should corrupted frames be generated and stored?

| Option | Description | Selected |
|--------|-------------|----------|
| On-the-fly | Add --corruption flags to extraction scripts, apply transforms in memory, no stored video files | ✓ |
| Pre-generate corrupted videos | Create 20 corrupted copies of all test videos (~200GB+) | |
| Corrupt PNGs + videos | Mixed approach, corrupt PNGs for skeleton, video frames for CLIP | |

**User's choice:** On-the-fly
**Notes:** Saves ~200GB+ storage. Feature caches at E:/features/ucf/clip_{type}_{sev}/ etc.

### How to handle skeleton re-extraction cost (~67h)?

| Option | Description | Selected |
|--------|-------------|----------|
| Test-set only | Only re-extract for 290 test videos. ~11h skeleton + ~4h CLIP = ~15h total | ✓ |
| All 1728 videos | Full re-extraction for train+val+test. ~79h total | |
| Skip skeleton re-extraction | Use original cache for all conditions, test assumption empirically | |

**User's choice:** Test-set only
**Notes:** TTA adapts and evaluates on test set only. Train/val features unchanged.

### How to implement corruption transforms across environments?

| Option | Description | Selected |
|--------|-------------|----------|
| Shared numpy/PIL module | Standalone module using numpy + PIL + scipy. Both envs can import. | ✓ |
| Kornia in vcc-main, PIL in vcc-skeleton | GPU-accelerated for CLIP, PIL fallback for skeleton. Risk: numerical differences. | |
| Kornia only in vcc-main | All corruption in vcc-main. Skeleton needs pre-corrupted frames on disk. | |

**User's choice:** Shared numpy/PIL module
**Notes:** Ensures bit-identical transforms across both extraction pipelines.

### Should corruption severity values follow PRD exactly?

| Option | Description | Selected |
|--------|-------------|----------|
| PRD values as-is | Use exact values from PRD/CLAUDE.md | |
| Claude's discretion | Let researcher/planner refine per ImageNet-C conventions | ✓ |

**User's choice:** Claude's discretion
**Notes:** Severity values are flexible. Researcher can refine to follow monotonic degradation convention.

---

## TTA Implementation

### How should the entropy objective be defined for sigmoid MIL output?

| Option | Description | Selected |
|--------|-------------|----------|
| Binary entropy | H = -s*log(s) - (1-s)*log(1-s), minimize over 32-snippet batch | ✓ |
| Marginal entropy | Compute marginal p̄ = mean(scores), then H(p̄). Batch-level diversity. | |
| Combined (binary + marginal) | H_individual + λ * H_marginal. Confidence + diversity. | |

**User's choice:** Binary entropy
**Notes:** Direct analog of TENT's softmax entropy for binary case. Clean and simple.

### How to implement TENT-style and SAR-style for LN-based head?

| Option | Description | Selected |
|--------|-------------|----------|
| Port from SAR repo | Adapt tent.py and sar.py. Replace BN with LN collection, softmax with binary entropy. | ✓ |
| Implement from scratch | Write from paper descriptions. Full control but risk missing details. | |
| Minimal wrapper approach | 50-line AdaptiveWrapper. Lean but may miss SAR's gradient filtering. | |

**User's choice:** Port from SAR repo
**Notes:** ICLR 2023 Oral code quality. Retains tested optimizer setup, gradient filtering, reset logic.

### How should adaptation and scoring interact per video?

| Option | Description | Selected |
|--------|-------------|----------|
| Online: adapt+score simultaneously | Forward → scores → entropy → backward → update → next batch. Scores collected per-batch. | ✓ |
| Adapt-then-score | First pass adapts, second pass scores. 2× forward cost. | |
| Both + compare | Report both for thesis comparison. | |

**User's choice:** Online adapt+score
**Notes:** Matches PRD §10.3 "online update without revisiting." Realistic deployment scenario.

---

## Experiment Orchestration

### How should the TTA experiment runner be organized?

| Option | Description | Selected |
|--------|-------------|----------|
| Extend run_ablations.py | Add TTA queues. Same resume logic, same results-index.csv. | ✓ |
| New scripts/run_tta.py | Separate runner. Cleaner separation but new codebase. | |
| Notebook-based | Interactive Jupyter. Less automation. | |

**User's choice:** Extend run_ablations.py
**Notes:** Unified runner with familiar patterns. TTA queues: tta_source_only, tta_tent_grid, tta_sar_grid.

### How should LR grid search be conducted?

| Option | Description | Selected |
|--------|-------------|----------|
| Full grid, report best | All 4 LRs for all 20 conditions. Pick best per-condition. ~90 min total. | ✓ |
| Representative subset first | Grid on 4 conditions, pick single LR, apply to all. | |
| Single LR from literature | Use 1e-3 for all. Only grid-search if poor results. | |

**User's choice:** Full grid, report best
**Notes:** Cheap computationally (~90 min total). Captures whether different corruptions need different rates.

### SAR rho grid size?

| Option | Description | Selected |
|--------|-------------|----------|
| 3 values: {0.005, 0.01, 0.05} | Small grid. ~240 SAR runs (~2 hours). | |
| Single rho = 0.01 | Fixed at 10× below ImageNet default. 80 runs. | |
| 5 values: {0.001, 0.005, 0.01, 0.05, 0.1} | Wider exploration including ImageNet default. ~400 runs (~3.5h). | ✓ |

**User's choice:** 5 values
**Notes:** Validates Pitfall M6 empirically by including ImageNet default. Richer thesis analysis.

### Primary metric for TTA results table?

| Option | Description | Selected |
|--------|-------------|----------|
| Frame-level AUC | Same as main results. Direct comparison. | ✓ |
| Both AUC and AP | Richer but adds columns. | |
| Relative degradation (mCE) | Mean Corruption Error à la ImageNet-C. Normalized. | |

**User's choice:** Frame-level AUC
**Notes:** Consistent with Phase 4. Δ format shows TTA impact clearly.

---

## Phase 5 Scope Boundary

### Cross-dataset TTA (OPT-03) in scope?

| Option | Description | Selected |
|--------|-------------|----------|
| Out of scope | Defer entirely. Too many XD dependencies. | |
| Include UCF→XD only | One direction. Feasible IF XD features land during execution. | |
| Include as stretch goal | Plan it, execute only if conditions met. | ✓ |

**User's choice:** Include as stretch goal
**Notes:** Gated on XD features + Phase 4c completion.

### EATA-style TTA in scope?

| Option | Description | Selected |
|--------|-------------|----------|
| Out of scope | Defer to thesis "future work." | |
| Include as stretch goal | After TENT + SAR deliver results. ~3 days if activated. | ✓ |
| Include in main scope | Three methods for stronger chapter. | |

**User's choice:** Include as stretch goal
**Notes:** After TENT + SAR. Adds Fisher Information Matrix computation.

### Phase 5 execution strategy relative to Phase 4c?

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 5 first, 4c when XD ready | Start now. Zero XD dependencies. Avoids idle time. | ✓ |
| Phase 4c first, Phase 5 after | Sequential. Wait for XD features. | |
| Interleave as needed | Flexible but risks half-done Phase 5. | |

**User's choice:** Phase 5 first, 4c when XD ready
**Notes:** ~1 week estimated. Independent tracks.

---

## Claude's Discretion

- Corruption severity value refinement per ImageNet-C conventions
- SAR reliable entropy filtering threshold
- Binary entropy numerical stability (epsilon clamping)
- scripts/corruption.py file location
- Per-video entropy curve storage
- Source-Only evaluation path design

## Deferred Ideas

- Cross-dataset TTA (stretch goal, gated on XD features + Phase 4c)
- EATA-style TTA (stretch goal, after TENT + SAR results)
- XD-Violence-C corruption benchmark (after Phase 4c)
- Adaptation parameter count ablation (thesis discussion)
