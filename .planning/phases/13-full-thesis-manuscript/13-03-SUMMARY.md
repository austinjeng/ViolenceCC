---
phase: 13-full-thesis-manuscript
plan: 03
subsystem: thesis-figures-tables
tags: [class-r, figure-generators, latex-tables, tta-rollup, sweep-charts, provenance]

# Dependency graph
requires:
  - phase: 13-full-thesis-manuscript
    plan: 01
    provides: "thesis/ skeleton (thesis/figures/ dir, gitignore thesis-artifact + results/* policy)"
  - phase: 13-full-thesis-manuscript
    plan: 02
    provides: "269 tracked provenance sources (canonical run-dir per_category.csv files, pri5 CSV) + PROVENANCE.md scaffold"
provides:
  - 4 new tracked Class-R generator scripts (thesis_severity_heatmap.py, thesis_corruption_heatmaps.py, thesis_per_category_tables.py, thesis_tta_rollup.py), all self-checking against tracked anchors
  - thesis/figures/fig_severity_heatmap.pdf (20x4 disc_reweight dAUC, TRUE 3-seed; SO400M gaussian_5 cell reads +13.2)
  - thesis/figures/fig_corruption_source.pdf + fig_corruption_disc_reweight.pdf (post-fix continual data; forbidden phase6 C-series fully replaced)
  - thesis/tables/tab_percat_{ucf,xd,rtfm}.tex (current post-lambda0/post-h1 per-category values, 3-seed mean+/-std)
  - results/_tta_rerun_continual/per_condition_rollup.csv TRACKED (760 rows; results/ tracked count 297 -> 298; partially discharges C7-1)
  - thesis/figures/fig_sweep_s01_ucf.png + fig_sweep_s02_xd.png (regenerated Phase-7 sweep heatmaps, historical-baseline guard documented below)
affects: [13-04 figure/provenance pass, 13-07/13-08 Ch5/Ch6 writers, App A/B/C writers, 13-13 adversarial number audit]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Class-R generator self-check convention: recompute per-backbone means/anchor cells from inputs and assert against published anchors (63.71/57.01/58.87/62.83, +0.67/+1.50/+2.24/+0.42, +13.2, +4.826) so stale data fails loudly before any asset is written"]

key-files:
  created:
    - scripts/thesis_severity_heatmap.py
    - scripts/thesis_corruption_heatmaps.py
    - scripts/thesis_per_category_tables.py
    - scripts/thesis_tta_rollup.py
    - thesis/figures/fig_severity_heatmap.pdf
    - thesis/figures/fig_corruption_source.pdf
    - thesis/figures/fig_corruption_disc_reweight.pdf
    - thesis/tables/tab_percat_ucf.tex
    - thesis/tables/tab_percat_xd.tex
    - thesis/tables/tab_percat_rtfm.tex
    - results/_tta_rerun_continual/per_condition_rollup.csv
    - thesis/figures/fig_sweep_s01_ucf.png
    - thesis/figures/fig_sweep_s02_xd.png
  modified: []

key-decisions:
  - "Severity heatmap plots TRUE 3-seed per-condition values recomputed from the 16 tracked r1full/variants JSONs (pri5 canonical aggregation), NOT the pri5 CSV's per-condition block (which is s42-only and would have reintroduced the forbidden stale +13.9); the tracked CSV is retained as a hard cross-check input"
  - "Rollup CSV stores auc verbatim from eval_metrics.json (0-1 scale, full precision); the self-check multiplies by 100 to match summary_3seed.json's points scale"
  - "fig_sweep_s01_ucf.png <- S04_sweep_heatmap_auc.png and fig_sweep_s02_xd.png <- S01_sweep_heatmap_ap.png (plan filenames use thesis-side numbering s01=UCF/s02=XD; generator S-codes are S01=XD/S04=UCF); no S04/S05 thesis copies made (S02/S03/S05 are markdown summaries, not figures)"

requirements-completed: [SC4 (Class-R provenance for all new figure/table assets)]

# Metrics
duration: ~18min
completed: 2026-07-05
---

# Phase 13 Plan 03: Class-R Figure/Table Generators + TTA Rollup Summary

**Four new tracked, self-checking Class-R generators produced the 20x4 3-seed severity heatmap (+13.2 anchor cell), the two continual-data corruption heatmaps replacing the forbidden phase6 C-series, three current-era per-category LaTeX tables, and a tracked 760-row TENT/SAR per-condition rollup CSV — plus regenerated Phase-7 sweep charts with thesis copies staged.**

## Performance

- **Duration:** ~18 min (2026-07-04T20:47Z -> 2026-07-04T21:05Z UTC)
- **Tasks:** 3/3
- **Files:** 13 created (4 scripts + 6 thesis assets + 1 tracked CSV + 2 sweep PNGs)

## Generated Assets (exact filenames for chapter writers)

| Asset | Generator (tracked) | Tracked data inputs | Consumer |
|---|---|---|---|
| `thesis/figures/fig_severity_heatmap.pdf` | `scripts/thesis_severity_heatmap.py` | `results/_coral_derisk/r1full_{clip,base,so400m,giant}.json` + `variants/v_*_s{123,2024}_test.json` (+ `results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv` as cross-check) | Ch 6 |
| `thesis/figures/fig_corruption_source.pdf` | `scripts/thesis_corruption_heatmaps.py` | same r1full/variants set + `results/_tta_rerun_continual/summary_3seed.json` | Ch 6 |
| `thesis/figures/fig_corruption_disc_reweight.pdf` | `scripts/thesis_corruption_heatmaps.py` | same as above | Ch 6 |
| `thesis/tables/tab_percat_ucf.tex` (label `tab:percat-ucf`, 13 rows, AUC %) | `scripts/thesis_per_category_tables.py` | `results/ucf_gated_fusion_giant_s{42,123,2024}/per_category.csv` | Ch 5 / App B |
| `thesis/tables/tab_percat_xd.tex` (label `tab:percat-xd`, 6 rows, AP %) | `scripts/thesis_per_category_tables.py` | `results/xd_gated_fusion_so400m_s{42,123,2024}/per_category.csv` | Ch 5 / App B |
| `thesis/tables/tab_percat_rtfm.tex` (label `tab:percat-rtfm`, 6 rows, AP %, s42-only) | `scripts/thesis_per_category_tables.py` | `results/xd_i3d_rtfm_i3d_s42/per_category.csv` + `results/xd_i3d_rtfm_i3d_flow_s42/per_category.csv` | App A |
| `results/_tta_rerun_continual/per_condition_rollup.csv` (TRACKED; columns backbone,method,condition,seed,auc; auc on 0-1 scale, x100 for points) | `scripts/thesis_tta_rollup.py` | 760 untracked continual-rerun `eval_metrics.json` (main-repo scratch; self-checked against tracked `summary_3seed.json`) | Ch 6 |
| `thesis/figures/fig_sweep_s01_ucf.png` (UCF AUC lr x k heatmap) | `scripts/generate_phase7_charts.py` (pre-existing, tracked) | `results/results-index.csv` | Ch 5 / App C |
| `thesis/figures/fig_sweep_s02_xd.png` (XD AP lr x k heatmap) | `scripts/generate_phase7_charts.py` | `results/results-index.csv` | Ch 5 / App C |

All new figure/table assets are **Class R**: tracked script + tracked data inputs. `results/phase7_charts/` (S01-S05) was recreated but deliberately left as untracked regenerable scratch.

## Historical-Baseline Guard (verbatim, for downstream writers)

HISTORICAL-BASELINE GUARD: these charts embed Delta columns vs the 2026-05 sweep configuration (CLIP backbone, pre-λ0, s42; baselines 0.8227 UCF / 0.7192 XD and S03 3-seed 81.98±0.29 / 70.98±1.08). Thesis captions/tables must exclude those delta columns or label them 'vs historical 2026-05 sweep configuration'; never chain to 82.5/78.7.

(The guard applies to `fig_sweep_s01_ucf.png` / `fig_sweep_s02_xd.png` — each embeds a blue "P4 baseline"/"P4c baseline" annotation box — and to any numbers lifted from the regenerated S02/S03/S05 markdown summaries.)

## Self-Check Results (all generator asserts green at run time)

- `thesis_severity_heatmap.py`: SO400M gaussian_noise_5 3-seed recompute **+13.19** (assert vs +13.2, tol 0.05) — PASS; Gaussian cross-backbone 3-seed avg **+4.826** (tol 0.01) — PASS; all 80 CSV s42 per-condition cells match r1full components (tol 1e-3) — PASS; all 16 CSV mean(3seed) family cells match recomputed 3-seed family means (tol 1e-3) — PASS
- `thesis_corruption_heatmaps.py`: source-only 20-condition 3-seed means recompute **63.7098 / 57.0052 / 58.8681 / 62.8276** (assert vs 63.71/57.01/58.87/62.83, tol 0.05; cross-assert vs `summary_3seed.json` mean.source, tol 0.01) — PASS; disc_reweight mean gains recompute **+0.6709 / +1.4966 / +2.2385 / +0.4230** (assert vs +0.67/+1.50/+2.24/+0.42, tol 0.05) — PASS
- `thesis_per_category_tables.py`: category sets exact (13 UCF / 6 XD / 6 RTFM x2) — PASS; forbidden Phase-4/4c-era literals (0.955 / 0.985 / 88.15 / 44.89) absent from all three emitted tables (in-script assert + external grep = 0 matches) — PASS
- `thesis_tta_rollup.py`: 760 rows collected (38 backbone/method/seed groups, each source/tent/sar group complete at 20 conditions); per-seed AND 3-seed source/tent/sar 20-condition means match `summary_3seed.json` within **0.01 points** — PASS
- `git ls-files --error-unmatch results/_tta_rerun_continual/per_condition_rollup.csv` exit 0; `git ls-files results/ | wc -l` = **298** (297 + rollup)
- pytest: **322 passed** (wave-2 gate; baseline held)
- `build_thesis.ps1` (incremental): exit 0, log scan clean (no LaTeX change in this plan — new .tex tables are not yet \input by placeholder chapters)

## Task Commits

1. **Task 1: severity + corruption heatmap generators** — `2e55cab` (feat)
2. **Task 2: per-category tables + TENT/SAR rollup** — `4a99514` (feat)
3. **Task 3: Phase-7 sweep regeneration + thesis copies** — `56c39d7` (feat)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Severity heatmap computes TRUE 3-seed per-condition values instead of plotting the CSV's per-condition block**
- **Found during:** Task 1 (input-format inspection)
- **Issue:** the plan directs plotting `pri5_per_condition_heatmap.csv` with a "3-seed" colorbar label, but that CSV's 20 per-condition rows are the **s42-only canonical** values (its SO400M gaussian_5 cell is 13.9231 — the stale s42-only +13.9 that Pitfall 6 forbids reintroducing; the honest 3-seed value is +13.2). Plotting the CSV as-is would have mislabeled s42 data as 3-seed AND put the forbidden +13.9 into a thesis figure.
- **Fix:** the script recomputes the 3-seed per-condition matrix from the 16 tracked `r1full_*`/`variants/v_*` JSONs (identical aggregation to `scripts/pri5_tta_breakdown.py`: s42 = r1full canonical, s123/s2024 = variants test refs) and keeps the tracked CSV as a hard cross-check input (s42 components + mean(3seed) family rows asserted equal). The plan's key_link (script -> pri5_per_condition_heatmap.csv) remains satisfied; the "3-seed" label is now truthful; the +13.2 anchor cell renders correctly.
- **Files modified:** scripts/thesis_severity_heatmap.py
- **Commit:** `2e55cab`

**2. [Rule 3 - Blocking issue] Untracked rollup inputs materialized into the worktree before the walk**
- **Found during:** Task 2
- **Issue:** this plan executes in a parallel git worktree, which only checks out tracked files — the ~760 per-condition `eval_metrics.json` files under `results/_tta_rerun_continual/<backbone>/` are untracked and exist on disk only in the main repo working tree.
- **Fix:** copied the 4 backbone dirs byte-identical from `D:\ViolenceCC\results\_tta_rerun_continual\` into the worktree (read-only on the main repo; gitignored scratch in the worktree — `git status` stays clean), then ran the rollup. Same mechanism as 13-02's deviation 1.
- **Files modified:** none (untracked scratch inputs only; only the generated rollup CSV was staged via `git add -f`)
- **Verification:** rollup self-check against tracked `summary_3seed.json` passes per-seed and 3-seed
- **Commit:** `4a99514`

### Notes (not deviations)

- **Actual rollup input count is 760, not the RESEARCH ~880 estimate:** 9 method dirs exist per backbone (source/tent/sar x s42/s123/s2024) plus 2 clip-only paper-hyperparameter variants (`tent@paper(0.005)`, `sar@paper(1e-4,0.01)`) = 38 dirs x 20 conditions. All 38 groups complete; the @paper variants are included in the CSV with seed=42.
- **Sweep chart name mapping:** the plan's thesis filenames use thesis-side numbering (s01=UCF, s02=XD) while the generator's S-codes are S01=XD-AP / S04=UCF-AUC. Mapping committed: `fig_sweep_s01_ucf.png` <- `S04_sweep_heatmap_auc.png`, `fig_sweep_s02_xd.png` <- `S01_sweep_heatmap_ap.png`. The optional "S04/S05 copies if used" were not made — S02/S03/S05 are markdown summaries, not figures; the two heatmap PNGs are the only sweep figures.

## PROVENANCE.md Rows Owed (for 13-04's Class R/V scaffold fill)

Every asset in the table above is Class R; 13-04 should register each with regen command `C:/Anaconda/envs/vcc-main/python.exe scripts/<generator>.py` (sweep PNGs: `scripts/generate_phase7_charts.py --with-confirm` + the two copies, with the historical-baseline guard note attached).

## Known Stubs

None — all planned assets generated and committed; no placeholder values emitted.

## Self-Check: PASSED

- All 13 created files exist on disk (4 scripts, 3 PDFs, 3 .tex tables, rollup CSV, 2 PNGs) — verified
- Commits `2e55cab`, `4a99514`, `56c39d7` present in git log — verified
- `git ls-files results/ | wc -l` = 298; rollup CSV tracked — verified
