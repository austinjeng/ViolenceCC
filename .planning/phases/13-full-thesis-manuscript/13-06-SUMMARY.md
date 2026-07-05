---
phase: 13-full-thesis-manuscript
plan: 06
subsystem: thesis-chapters
tags: [ch04, ch05, ch06, experimental-setup, fusion-results, tta-results, number-integrity]

# Dependency graph
requires:
  - phase: 13-full-thesis-manuscript
    plan: 03
    provides: "Class-R generated assets (severity/corruption heatmaps, tab_percat_* tables, sweep PNGs) referenced by ch05/ch06"
  - phase: 13-full-thesis-manuscript
    plan: 04
    provides: "complete thesis/figures/ inventory (Class R/V) + PROVENANCE.md rows for every figure the chapters include"
provides:
  - "thesis/chapters/ch04_experimental_setup.tex — full experimental-setup chapter (8pp): datasets/splits, eval protocol + asymmetry disclosure, UCF-Crime-C with corruption.py:38-42 exact params, implementation details incl. verbatim lambda2 footnote, reproducibility protocol, three-env infrastructure, efficiency tables"
  - "thesis/chapters/ch05_results_fusion.tex — full fusion+backbone results chapter (15pp): Tables 1/2 byte-identical to paper, pooling ablations, backbone comparison, complementarity (p~=0.03 wording), historical-configuration sweep, Pri-6 bootstrap CIs, seed sensitivity, qualitative figures, Pri-9 failure analysis, per-category summary -> App B"
  - "thesis/chapters/ch06_results_tta.tex — full robustness+TTA chapter (11pp): source-only degradation, complete TENT/SAR story (dropout bug, episodic inertness, 3-seed continual null), NORM/CORAL + S1-S6 narrative, disc_reweight Tables 3/breakdown byte-identical to paper, severity heatmap, LN-barrier analysis"
affects: [13-07 ch07-09 integration, appendix writers (App B/C/E/F cross-refs), 13-13 adversarial number audit]

# Tech tracking
tech-stack:
  added: []
  patterns: ["every number-bearing table/figure carries a % Source: comment naming the tracked generator + data (PATTERNS shared pattern); paper-table lifts verified by byte-diff of the tabular bodies against main.tex before commit"]

key-files:
  created: []
  modified:
    - thesis/chapters/ch04_experimental_setup.tex
    - thesis/chapters/ch05_results_fusion.tex
    - thesis/chapters/ch06_results_tta.tex

key-decisions:
  - "lambda2 footnote lifted verbatim except one cross-reference adaptation: 'reported below' -> 'reported in Chapter 5' (the seed-variance range lives in ch05 in the thesis, not below the footnote as in the paper); the <=0.13pp disclosure substance is untouched"
  - "Pooling section: -0.90 AP (2-person, XD) presented as the cross-backbone average of Table 2 deltas (verified: (-2.1-1.3+0.5-0.8)/4 = -0.925); -2.32 AP (mean-only) attributed EXPLICITLY to the original single-configuration CLIP-backbone pooling study (STATE.md decision row), since the final 3-seed grid shows smaller mean-only deltas (-0.3..-0.5) and implying Table-2 derivability would be false"
  - "Seed-sensitivity section uses Table 1/2 std values (UCF 0.1-0.4; XD gated 0.9/0.9/0.9/2.8; XD visual-only 1.0-2.2) rather than the plan-listed '1.08-2.8 vs 0.29-0.4' span, which mixes pre-lambda0 CLIP-era stds (STATE row) with current table stds — avoided era-mixing; substance (order-of-magnitude gap, Giant outlier) preserved"
  - "'SigLIP2-Base -2.2pp UCF story' rendered via Table-1-derived gaps (-2.7 visual-only / -2.4 gated vs CLIP) instead of importing an untraceable -2.2 literal from the Phase-8 era"
  - "+3.31 (s42-only Gaussian mean) never used anywhere, per Pitfall 6 simplest-safe option; +4.83/+8.95/+13.2 kept distinct with an explicit distinctness sentence in ch06"
  - "ch05 qualitative section additionally consumes fig_gate_by_category_ucf/xd + fig_tsne_ucf/xd (13-04 inventory sanctions them as 'Ch 5 / App F'; spec S4 Ch5 names gate-activation distributions + t-SNE) beyond the plan's minimal two-figure list"
  - "Cross-chapter references restricted to permanent labels only (ch:NN, app:a..f) so the parallel-wave build stays free of undefined references; paper label names (tab:ucf-ablation, tab:tta, sec:impl, ...) kept for mechanical portability of sibling chapters' \\ref calls at integration"

requirements-completed: [SC2 (spec S4 Ch4-Ch6 content complete, placeholder-free), SC5 (honesty framings + disclosures retained in the number-densest chapters)]

# Metrics
duration: ~30min
completed: 2026-07-05
---

# Phase 13 Plan 06: Chapters 4-6 (Experimental Setup, Fusion Results, Robustness & TTA) Summary

**Drafted the three number-densest thesis chapters (34pp combined) with every ablation/TTA table byte-diffed against the frozen paper's canonical inlined tables, UCF-Crime-C parameters cited from scripts/corruption.py (not stale CLAUDE.md), all four Pri-5 aggregations kept explicitly distinct, and a clean log-scanned build after each chapter.**

## Performance

- **Duration:** ~30 min (2026-07-05T04:27Z -> ~04:57Z UTC)
- **Tasks:** 3/3
- **Files:** 3 chapter files drafted (placeholder -> full prose)

## Per-chapter page counts (from main.toc of the final build)

| Chapter | Pages | Target | Content |
|---|---|---|---|
| Ch 4 Experimental Setup | pp. 5-12 (8pp) | ~10pp | datasets/splits, eval protocol + UCF/XD grid asymmetry, UCF-Crime-C construction (corruption.py:38-42 exact severity table incl. 0.38 / (20,15) / additive brightness), implementation details + verbatim lambda2 footnote, reproducibility protocol, three-conda-env infrastructure, 2 efficiency tables from tracked CSVs |
| Ch 5 Fusion & Backbones | pp. 13-27 (15pp) | ~15pp | Tables 1/2 verbatim, 3 bolded-thread findings, pooling ablations (2-Person never promoted), backbone comparison, complementarity (6/8 + 2 ties, p~=0.03), historical-configuration sweep (+3.72 labeled sweep-era), Pri-6 bootstrap CIs, seed sensitivity, 5 qualitative figures, Pri-9 failure analysis (worst-5 table, 0.874/0.382/p75 0.986), per-category summary -> App B |
| Ch 6 Robustness & TTA | pp. 28-38 (11pp) | ~12pp | source-only degradation (63.7/57.0/58.9/62.8), dropout cautionary note (~1.07pp, commit 83b8927), episodic grid bests labeled bests (+3.81/+5.38), inertness (98.4%) -> continual, 3-seed null table (worst |d|=0.082), NORM/CORAL (-1.62 LOCO) + S1-S6 -> disc_reweight, Tables 3/breakdown verbatim incl. truncated-grid caveat, severity heatmap (+13.2 single most-degraded), honest caveats (Base s42 -3.20, transductive, rescue-not-robustness), LN-barrier section |

Combined: 34pp vs the plan's ~35-40pp estimate (ch04 runs 2pp lean; no padding added per CLAUDE.md simplicity rules).

## Verification results (all green)

- `build_thesis.ps1` (incremental) after each task: exit 0, log scan clean (no errors, no undefined refs/citations) — final toc confirms all 21 new sections render
- Byte-diffs vs `paper/main.tex`: tab:ucf-ablation (L229-241), tab:xd-ablation (L248-260), tab:tta (L304-315), tab:tta_breakdown (L344-356) — all four tabular bodies identical
- ch04: PLACEHOLDER-W0=0; "0.13">=1; contains 0.38, (20,15), additive; stale brightness multipliers absent; L136 sentence verbatim (whitespace-normalized match=1); "254 meet the 64-frame minimum"=1; seeds {42,123,2024}; corruption.py named 4x
- ch05: "82.5"=6 (>=2); "0.008"=0; p\approx0.03 present; "+3.72" with historical-configuration labeling; 0.9268/0.9452=0; per-category quotes match generated tab_percat_{ucf,xd}.tex exactly; \ref{app:b}=3
- ch06: "13.9"=0; "+1.21", "0.082", "98.4", "by construction", "+13.2"+"most-degraded" all present; "+3.31" absent; fig_severity_heatmap includegraphics present; transductive disclosure present; tab:tta caption caveat present (2 hits)
- Forbidden-value grep across all three chapters (83.6, 71.8, 13.9, 0.9268, 0.9452, 0.955, 0.985, 88.15, 44.89, 0.008): ALL ZERO
- % Source comments: ch04=3, ch05=16, ch06=8 (every number-bearing table/figure covered)
- `git status --porcelain` clean after final build (no artifacts staged)

## Task Commits

1. **Task 1: ch04 experimental setup** — `f1dc82e` (docs)
2. **Task 2: ch05 fusion & backbone results** — `b3ed9f3` (docs)
3. **Task 3: ch06 robustness & TTA results** — `b736e05` (docs)

## Figures consumed (for the App F writer's "not used in Ch 5/6" budget)

- ch05: fig_backbone_comparison.pdf, fig_sweep_s01_ucf.png, fig_sweep_s02_xd.png (guard-compliant captions), fig_temporal_scores.pdf, fig_gating_distribution.pdf (honest caption: per-category AUC/AP bars, CLIP s42), fig_gate_by_category_{ucf,xd}.png, fig_tsne_{ucf,xd}.png, pri9_score_hist.png
- ch06: fig_corruption_source.pdf, fig_tta_comparison.pdf, fig_severity_heatmap.pdf, fig_corruption_disc_reweight.pdf
- Still unconsumed for App F: fig_gate_histogram_{ucf,xd}.png, fig_category_scores_{ucf,xd}.png, fig_skeleton_overlay_b0{1,2,3}.png, fig_temporal_extra_*.png
- thesis/tables/tab_percat_{ucf,xd}.tex NOT \input by ch05 (values quoted + \ref{app:b}); the App B writer renders them (labels tab:percat-* stay unused until then, which is safe — no dangling refs)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Orchestrator-supplied base commit hash malformed**
- **Found during:** worktree_branch_check (first action)
- **Issue:** the specified base `4187725bb1af6f13c25802956563a06e0774abcd` does not exist as an object; the short prefix `4187725` uniquely resolves to main's tip `41877258d278e50daec4c34be8d7520b45668562` ("docs(13): roadmap progress 4/13 (13-04 merged...)"), which matches the plan's dependency context exactly. The suffix in the prompt appears mangled.
- **Fix:** reset the (stale, cb8a26a-era) worktree branch to the unambiguously-resolved full hash; branch/namespace assertions passed before and after.
- **Files modified:** none (git state only)
- **Commit:** n/a

### Intentional micro-adaptations (documented, not silent)

**2. lambda2 footnote cross-reference:** "seed variance reported below" -> "reported in Chapter~\ref{ch:05}" (the variance figures live in ch05 in the thesis). All other footnote text verbatim; <=0.13pp disclosure intact.

**3. Mean-only pooling -2.32 AP attribution:** presented as the original single-configuration CLIP-backbone pooling study's measurement (source: STATE.md decision row, per PROVENANCE row 8), alongside the Table-2-derived 3-seed mean-only deltas (-0.3..-0.5 AP) — the plan's phrasing could otherwise imply -2.32 is derivable from Table 2, which it is not.

**4. Seed-sensitivity std values:** used current Table 1/2 stds instead of the plan-listed 1.08/0.29 era-mixed anchors (see key-decisions).

**5. SigLIP2-Base UCF gap:** derived -2.7/-2.4 from Table 1 instead of the spec's Phase-8-era "-2.2pp" literal (Phase-8 summaries are a forbidden number source).

## Known Stubs

None — all three chapters are placeholder-free full prose; no empty values, no TODO/FIXME markers.

## Threat Flags

None — no new code, endpoints, or trust-boundary surface; T-13-06 mitigations applied as specified (byte-match lifts + forbidden-value greps + % Source comments per table).

## Self-Check: PASSED

- thesis/chapters/ch04_experimental_setup.tex, ch05_results_fusion.tex, ch06_results_tta.tex exist with full content — verified
- Commits f1dc82e, b3ed9f3, b736e05 present in git log — verified
- PLACEHOLDER-W0 absent from all three chapters; \label{ch:04/05/06} retained — verified
