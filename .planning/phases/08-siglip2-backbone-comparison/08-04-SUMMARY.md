---
phase: 08-siglip2-backbone-comparison
plan: 04
subsystem: training, evaluation, visualization
tags: [siglip2, ablation, comparison, charts, backbone]

dependency_graph:
  requires:
    - phase: 08-02
      provides: 10 SigLIP2 YAML configs + 6 Phase 8 queues
    - phase: 08-03
      provides: SigLIP2 feature caches (1536-d mean+max, 768-d mean-only)
  provides:
    - 14 SigLIP2 ablation results in results-index.csv
    - CLIP vs SigLIP2 comparison table (backbone_comparison.csv)
    - Seed stability table (seed_stability.csv)
    - 3 thesis-ready chart PNGs
  affects: [thesis-writing]

tech-stack:
  added: []
  patterns: [results-index-driven-comparison, paired-backbone-ablation]

key-files:
  created:
    - scripts/generate_phase8_charts.py
    - results/phase8_charts/backbone_comparison.csv
    - results/phase8_charts/seed_stability.csv
    - results/phase8_charts/backbone_comparison_auc.png
    - results/phase8_charts/backbone_comparison_ap.png
    - results/phase8_charts/seed_stability.png
  modified:
    - results/results-index.csv

key-decisions:
  - "All 14 SigLIP2 runs executed by user between sessions (all queues had .done markers)"
  - "Skeleton-Only rows reused from Phase 4/4c (backbone-independent, no SigLIP2 variant)"
  - "Chart script follows Phase 6 style pattern (Agg backend, sns.set_theme, DPI/FIG constants)"

requirements-completed: [EVAL-02, EVAL-03, EVAL-04]

duration: "~3 hours training (user-supervised) + 15min chart script"
completed: 2026-05-20
---

# Phase 8 Plan 04: SigLIP2 Ablation Matrix + Comparison Table Summary

**14 SigLIP2 ablation runs complete, CLIP vs SigLIP2 comparison table generated with 3 thesis-ready charts**

## Performance

- **Duration:** ~3h training (user between sessions) + 15min chart script
- **Completed:** 2026-05-20
- **Tasks:** 3 (queue execution + chart script + human verification)
- **Files created:** 6

## Task Commits

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Execute Phase 8 ablation queues | (user-executed, .done markers) | results/results-index.csv |
| 2 | Create backbone comparison chart script | c42e3a3 | scripts/generate_phase8_charts.py |
| 3 | Human verification | — (approved) | — |

## Key Results

### UCF-Crime (AUC) — SigLIP2 slightly below CLIP

| Variant | CLIP | SigLIP2 | Delta |
|---------|------|---------|-------|
| CLIP/SigLIP2 Only | 81.69% | 79.11% | -2.57pp |
| Late Fusion | 78.71% | 79.93% | +1.22pp |
| Gated Fusion | 82.27% | 79.61% | -2.65pp |
| GF 2-Person | 81.65% | 79.48% | -2.17pp |
| GF Mean-Only | 81.78% | 80.00% | -1.78pp |

### XD-Violence (AP) — SigLIP2 roughly matches, slight gains on pooling

| Variant | CLIP | SigLIP2 | Delta |
|---------|------|---------|-------|
| CLIP/SigLIP2 Only | 70.53% | 72.12% | +1.59pp |
| Late Fusion | 65.48% | 65.56% | +0.08pp |
| Gated Fusion | 71.92% | 71.92% | +0.00pp |
| GF 2-Person | 71.02% | 73.08% | +2.05pp |
| GF Mean-Only | 69.60% | 72.45% | +2.85pp |

### 3-Seed Stability (Gated Fusion)

| Dataset | CLIP Mean | SigLIP2 Mean | CLIP Std | SigLIP2 Std |
|---------|-----------|-------------|----------|-------------|
| UCF AUC | 81.98% | 79.77% | 0.30% | 0.22% |
| XD AP | 70.97% | 74.70% | 1.08% | 2.97% |

## Deviations from Plan

- All training runs already executed by user between sessions (verified via .done markers and results-index.csv)
- Backbone dimensions adapted from plan (Giant 3072/1536 → base 1536/768) per commit 50954f1

## Self-Check: PASSED

- [x] All 14 SigLIP2 ablation runs complete with non-NaN AUC/AP values
- [x] 3-seed stability computed for Gated Fusion on both datasets
- [x] Side-by-side CLIP vs SigLIP2 comparison table generated
- [x] Chart script produces 5 output files without error
- [x] Test suite: 219/220 pass (1 pre-existing xd_train.txt split failure)
- [x] SUMMARY.md created

---
*Phase: 08-siglip2-backbone-comparison*
*Completed: 2026-05-20*
