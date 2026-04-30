# Phase 7: XD-Violence Hyperparameter Sweep - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Improve Gated Fusion AP on XD-Violence through a targeted lr × k_topk grid search (~20 runs), with 3-seed confirmation on the best configuration. Investigate the RTFM XD-I3D reproduction gap (65.70% vs published 77.81%) through 4 diagnostics and document findings. Produce a heatmap + table suitable for thesis inclusion.

</domain>

<decisions>
## Implementation Decisions

### Sweep grid design
- **D-01:** Learning rate grid: {5e-5, 1e-4, 2e-4, 3e-4, 5e-4} — 5 values centered around current 1e-4, biased upward since XD has ~4x more training data than UCF.
- **D-02:** k_topk grid: {1, 3, 5, 7} — 4 values spanning aggressive (k=1, top snippet only) to inclusive (k=7, ~22% of 32-snippet bag). k=3 is the Phase 4c default.
- **D-03:** Full combinatorial grid: 5 lr × 4 k_topk = **20 runs** at seed=42. Matches SC #1 (~20 runs target).
- **D-04:** Single seed (s42) for sweep exploration. Direct comparison with Phase 4c baseline (xd_gated_fusion_s42, AP=71.92%).
- **D-05:** 3-seed confirmation on the winning lr × k_topk config using seeds {42, 123, 2024}. Reports mean±std AP, directly comparable to Phase 4c 3-seed results (mean AP=70.97% ± 1.08%).

### RTFM gap investigation
- **D-06:** Goal is **diagnose and document** — identify likely cause of 65.70% vs 77.81% gap, document for thesis. Do not attempt to close the gap through protocol changes.
- **D-07:** Run **all 4 diagnostics**:
  1. Annotation alignment check — compare our xd_temporal.txt parsing (Wu parser) against original XD-Violence evaluation protocol
  2. Temporal interpolation check — verify snippet→frame score expansion matches published RTFM code
  3. I3D feature audit — compare I3D feature statistics (mean/std/shape) against published RTFM features
  4. Published code comparison — diff our evaluation path against RTFM's official XD evaluation code
- **D-08:** Fix policy: **fix only clear bugs** (parsing errors, off-by-one). Document methodological differences (different I3D features, different eval protocol) without changing our protocol.

### Sweep infrastructure
- **D-09:** Use **CLI overrides** on base config (`gated_fusion_xd.yaml`). Pass `--lr` and `--k-topk` as CLI args to `train.py`, overriding YAML values. Zero new config files created for the sweep.
- **D-10:** **Extend `run_ablations.py`** with a `phase7_sweep` queue containing 20 RunSpec entries. Reuses `.done` resume, `results-index.csv` append, error handling. RunSpec gets 2 new optional fields (`lr_override`, `k_topk_override`).
- **D-11:** Run directory naming: `xd_gated_fusion_lr{}_k{}_s42` — extends Phase 4 D-30 pattern with lr and k suffix. Example: `xd_gated_fusion_lr2e4_k5_s42`.
- **D-12:** 3-seed confirmation queue: `phase7_confirm` with 3 RunSpec entries for the winning config at seeds {42, 123, 2024}. Created after sweep results are analyzed.

### Results presentation
- **D-13:** Primary metric: **AP** (standard for XD-Violence benchmark). AUC is secondary — report both but rank/optimize by AP.
- **D-14:** Visualization: **heatmap + table**. A 5×4 heatmap (lr rows, k_topk columns, AP as cell color/text) plus a markdown table with exact numbers. Use existing chart generation infrastructure (`scripts/generate_phase4_charts.py` as template).
- **D-15:** Single Phase 7 results summary document with two sections: sweep results (heatmap + table + 3-seed confirmation) and RTFM gap analysis (diagnostic findings).

### Claude's Discretion
- Exact heatmap color scheme and styling
- Whether to include per-category AP breakdown for the winning sweep config
- RTFM diagnostic script structure (single script vs modular)
- wandb posture for sweep runs (continue disabled or enable)
- Whether confirmation runs reuse the sweep queue or get a separate queue

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase dependency
- `.planning/phases/04C-xd-violence-main-results/04C-CONTEXT.md` — D-01 (XD config convention), D-04 (hyperparameter transfer from UCF), D-06 (AP target contingency/MISS-ACCEPTED pattern)
- `.planning/phases/04-baseline-evaluation-main-results/04-CONTEXT.md` — D-26..D-34 (run_ablations.py orchestration contract), D-30 (deterministic run dir naming), D-35 (flat YAML convention)

### Training infrastructure
- `scripts/run_ablations.py` — QUEUES dict, RunSpec dataclass, `.done` resume, `results-index.csv` append. Extend with phase7_sweep queue and CLI override support.
- `src/train.py` — Training entry point. Needs CLI override support for `--lr` and `--k-topk`.
- `configs/gated_fusion_xd.yaml` — Base config for sweep (lr=1e-4, k_topk=3, epochs=50, patience=10)

### Evaluation infrastructure
- `src/evaluate.py` — Frame-level AUC/AP pipeline
- `src/eval/xd_annotations.py` — Wu parser, `_parse_category()` for all 6 XD categories
- `src/eval/snippet_to_frame.py` — C4-guard snippet→frame expansion (relevant to RTFM interpolation diagnostic)

### Results logging
- `src/utils/csv_logger.py` — `results_index_append()` for `results/results-index.csv`
- `scripts/generate_phase4_charts.py` — Chart generation template for heatmap creation

### RTFM reference
- `configs/rtfm_i3d.yaml` — RTFM XD-I3D config used in Phase 4b
- RTFM GitHub: `https://github.com/tianyu0207/RTFM` — Official XD evaluation code for comparison

### Pitfalls
- `.planning/research/PITFALLS.md` — C3 (test-set leakage), C4 (snippet→frame off-by-one)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/run_ablations.py` — Full queue orchestration with `.done` resume, error logging, `results-index.csv` append. Needs RunSpec extension for CLI overrides.
- `src/utils/csv_logger.py::results_index_append` — Append-only audit log writer. Already has lr/rho columns from Phase 5 TTA extension.
- `scripts/generate_phase4_charts.py` — Matplotlib chart generation. Template for sweep heatmap.
- `src/eval/xd_annotations.py` — Wu parser with `_parse_category()`. Key artifact for RTFM annotation alignment diagnostic.

### Established Patterns
- Flat self-contained YAML per variant (Phase 1 D-03, Phase 4 D-35) — sweep breaks this intentionally by using CLI overrides on a single base config
- QUEUES dict with RunSpec entries in `run_ablations.py` — extend with `phase7_sweep`
- Deterministic run dir naming (Phase 4 D-30) — extended with `lr{}_k{}` suffix
- `.done` marker for filesystem-probe resume (Phase 4 D-31)

### Integration Points
- `train.py` CLI arg parsing — add `--lr` and `--k-topk` override flags
- `run_ablations.py::RunSpec` — add `lr_override` and `k_topk_override` optional fields
- `run_ablations.py::run_queue()` — pass overrides as additional subprocess args
- `results/results-index.csv` — sweep rows logged alongside Phase 4/4c/5 results

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-xd-violence-hyperparameter-sweep*
*Context gathered: 2026-05-01*
