---
phase: quick-260609-cpr
plan: 01
subsystem: paper
tags: [paper, code-paper-review, tta, complementarity, adversarial-review, honesty]
requires: [paper/main.tex, results/, scripts/run_ablations.py]
provides: [".planning/CODE-PAPER-REVIEW-2026-06-07.md (all-resolved)", "scripts/aggregate_tta_table.py", "results/phase10_charts/visual_only_seed_stability_4way.csv"]
affects: [paper/main.tex, paper/figures/fig_backbone_comparison.pdf, paper/figures/fig_tta_comparison.pdf, paper/tables_generated.tex, scripts/benchmark_backbones.py, scripts/generate_pub_figures.py]
tech-stack:
  added: []
  patterns: [adversarial-precheck-before-edit, matched-seed-verification, multi-agent-audit]
key-files:
  created:
    - scripts/aggregate_tta_table.py
    - results/phase10_charts/visual_only_seed_stability_4way.csv
    - .planning/quick/260609-cpr-code-paper-match-review/260609-cpr-SUMMARY.md
  modified:
    - paper/main.tex
    - scripts/run_ablations.py
    - scripts/benchmark_backbones.py
    - scripts/generate_pub_figures.py
    - paper/tables_generated.tex
decisions:
  - "Each MEDIUM/LOW edit was adversarially pre-checked by a 3-skeptic workflow BEFORE applying — caught 2 dangling LaTeX refs, a wrong M2 rationale, a stale number a prior edit introduced, and a T-symbol collision"
  - "M7: ran matched-seed visual-only baselines (queue m7_visual_seeds, 16 runs) rather than reposition a headline contribution on 3-seed-gated-vs-1-seed-visual; this overturned the apparent SigLIP2-Base/XD regression (single-seed artifact)"
  - "Complementarity reframed honestly: small + consistent (gated>=visual 8/8 configs, sign test p~0.008), not large/per-cell-significant; backbone-dependent magnitude"
  - "M5: dropped Table-3 TENT/SAR columns (printed wrong baseline) to match the figure which already omits them; entropy-null stays in prose"
  - "M2: kept 21.6 FPS (real 02-UAT.md measurement, 1-person rate); 33.3 FPS benchmark is synthetic people-free-frame latency"
  - "L6 Table-2 Late Delta +1.5 LEFT unchanged — skeptic-verified raw-correct (table uses full-precision rounding throughout)"
metrics:
  duration: multi-session (conversational; not a gsd:quick executor run)
  completed: 2026-06-09
  commits: "22ddb20..aa5120b (~12 commits, pushed to origin/main)"
---

# Phase quick-260609-cpr Plan 01: Code↔Paper Match Review — ALL RESOLVED

Comprehensive code↔paper consistency audit of the CGW '26 paper (`paper/main.tex`) against the implementation + committed results, driven by multi-agent adversarial review workflows. 82 findings, 0 false positives. **All HIGH + MEDIUM + LOW resolved** (or consciously left with verified rationale). Headlines UCF 82.5% AUC / XD 78.7% AP intact throughout; paper rebuilds clean (0 undefined refs, 0 errors, 10 pages).

## What was fixed (by tier)

- **HIGH (3):** TTA Table-3 provenance committed + regenerator (`22ddb20`); "≤0.004 pp" entropy bound → "<0.1 pp" (`9ba9d00`); unsupported category-adaptive gating figure dropped (`57b4e86`).
- **MEDIUM (7):** normalization wording (`7280746`), evaluated n=254 (`7280746`), dataset-dependent snippet duration (`a1b68ff`), gate functional form (`2404d5c`), matched-seed complementarity re-analysis (`d9df6db`+`e77f464`), Table-3 TENT/SAR columns dropped (`a97922c`), FPS provenance (`a97922c`).
- **LOW (8):** keypoint-confidence wording, SigLIP2 checkpoint names, LR warmup+cosine, bag T=32 (+T→T_f rename), param count 1,536, Giant figure label, stale-file banner (`aa5120b`); Table-2 Late Δ left (verified correct).
- **Bonus:** `:263` late-fusion overstatement (`c7791d1`); `:272` stale number from the M7 edit (`a97922c`).

## Headline empirical corrections (matched-seed runs)

- **No fusion regression anywhere** — the apparent SigLIP2-Base/XD −2.3 was a seed-42 outlier; matched 3-seed margin +0.05 (p=0.97).
- **"SO400M leads XD visual-only" was a single-seed artifact** — 3-seed SO400M 76.6 ≈ Giant 76.8; SO400M leads XD only under gated fusion (78.7, robust).
- Complementarity is **small, consistent, never-degrading** (8/8 configs positive, sign test p≈0.008), largest on XD (CLIP +1.9, SO400M +2.1).

## Process note

This ran conversationally (not via the `/gsd:quick` executor) because it was an interactive, high-stakes, exact-number LaTeX review. Every substantive edit was gated by an adversarial-review workflow before applying. Full report: `.planning/CODE-PAPER-REVIEW-2026-06-07.md` (resolution table at top). Memory: `project_code_paper_review_2026-06-09`.
