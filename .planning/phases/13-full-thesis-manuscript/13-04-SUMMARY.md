---
phase: 13-full-thesis-manuscript
plan: 04
subsystem: thesis-figures-provenance
tags: [class-v, class-r, figure-provenance, phase6-disposition, wave0-exit, provenance-manifest]

# Dependency graph
requires:
  - phase: 13-full-thesis-manuscript
    plan: 02
    provides: "PROVENANCE.md scaffold (§3 Class R/V figure schema) + 269 tracked provenance sources"
  - phase: 13-full-thesis-manuscript
    plan: 03
    provides: "Class-R generated assets (severity/corruption heatmaps, per-category tables, sweep PNGs)"
provides:
  - Complete thesis/figures/ inventory (25 files) + thesis/tables/ (3 files) — every asset Class R or Class V
  - 5 verified reuse figures staged byte-identical (4 paper PDFs + pri9_score_hist.png)
  - Phase-6 disposition pass complete — all 20 non-C PNGs dispositioned (3 INCLUDED-V / 9 REGENERATED-V / 8 DROPPED); zero C-series files
  - PROVENANCE.md §3 populated (28 rows: 9 Class R + 19 Class V) + §3a disposition record; every source path git-tracked (asserted)
  - generate_phase6_charts.py fix: UCF Normal videos now classified correctly in D01/D02/E01 charts
  - Wave-0 exit gates green (clean build, log scan clean, pytest 322, git hygiene)
affects: [13-05..13-10 chapter writers, 13-11, 13-12 App F writer, 13-13 adversarial number audit, 13-VALIDATION]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Class-V verification chain for regenerated phase-6 figures: validate every untracked regeneration input against a tracked anchor BEFORE replotting (npz -> recomputed AUC/AP vs tracked eval_metrics.json, diff 0.00e+00; checkpoints -> official evaluate.py CLI on scratch copies reproduces tracked auc/ap exactly)"]

key-files:
  created:
    - thesis/figures/fig_temporal_scores.pdf
    - thesis/figures/fig_backbone_comparison.pdf
    - thesis/figures/fig_tta_comparison.pdf
    - thesis/figures/fig_gating_distribution.pdf
    - thesis/figures/pri9_score_hist.png
    - thesis/figures/fig_skeleton_overlay_b01.png (+ b02, b03)
    - thesis/figures/fig_temporal_extra_ucf_shooting008.png (+ explosion033, xd_blackhawkdown)
    - thesis/figures/fig_gate_by_category_ucf.png (+ xd)
    - thesis/figures/fig_gate_histogram_ucf.png (+ xd)
    - thesis/figures/fig_tsne_ucf.png (+ xd)
    - thesis/figures/fig_category_scores_ucf.png (+ xd)
  modified:
    - thesis/PROVENANCE.md (§3 figure/table rows + §3a disposition record)
    - scripts/generate_phase6_charts.py (UCF Normal-classification fix)

key-decisions:
  - "Phase-6 B-series copied byte-identical but RENAMED LaTeX-safe (originals contain '#' which breaks \\includegraphics); PROVENANCE rows record the original filenames"
  - "A-series regenerated fresh rather than copied: post-h1/post-λ0 data selects different videos for 3 of 5 slots (Arrest007→Explosion033; both XD videos changed), proving the May set was stale; 3 of 5 fresh curves included (App-F 2-3 budget)"
  - "F01/F04/F05/F06 DROPPED: single-seed bar-chart duplicates of canonical 3-seed Tables 1-2 (Pri-1 lesson — no s42-only ablation numbers alongside canonical tables)"
  - "Checkpoint verification via official evaluate.py CLI on scratch run-dir copies (results/_regen1304_check/), respecting test_loader's anti-leakage import guard instead of bypassing it"

requirements-completed: [SC4 (every thesis figure Class R or Class V, no stale provenance, forbidden C-series absent), SC1 (Wave-0 gates green — user approval pending at checkpoint)]

# Metrics
duration: ~35min
completed: 2026-07-05
---

# Phase 13 Plan 04: Wave-0 Figure Set + Provenance Pass Summary

**Complete Wave-0 figure inventory: 5 reuse figures re-verified against tracked anchors, all 20 non-C phase-6 PNGs dispositioned (14 verified figures entered thesis/figures/, 8 dropped with reasons, C-series excluded), PROVENANCE.md §3 populated with 28 Class R/V rows all pointing at tracked sources, and Wave-0 exit gates green — pending USER CHECKPOINT approval of the skeleton.**

## Performance

- **Duration:** ~35 min (2026-07-04T21:14:56Z → ~21:50Z UTC)
- **Tasks:** 3/3 automatable complete; Task 4 = USER CHECKPOINT (pending)
- **Files:** 19 figures staged + PROVENANCE.md populated + 1 script fix

## Final thesis/figures/ + thesis/tables/ inventory (for chapter writers)

### Class R (9) — regenerate via tracked script from tracked data

| Asset | Producer | Consumer |
|---|---|---|
| `fig_architecture.tex` | verbatim paper TikZ copy (13-01) | Ch 3 |
| `fig_severity_heatmap.pdf` | `scripts/thesis_severity_heatmap.py` | Ch 6 |
| `fig_corruption_source.pdf` | `scripts/thesis_corruption_heatmaps.py` | Ch 6 |
| `fig_corruption_disc_reweight.pdf` | `scripts/thesis_corruption_heatmaps.py` | Ch 6 |
| `tab_percat_ucf.tex` / `tab_percat_xd.tex` / `tab_percat_rtfm.tex` | `scripts/thesis_per_category_tables.py` | Ch 5 / App B / App A |
| `fig_sweep_s01_ucf.png` / `fig_sweep_s02_xd.png` | `scripts/generate_phase7_charts.py` (HISTORICAL-BASELINE GUARD — never chain the embedded 0.8227/0.7192 to 82.5/78.7) | Ch 5 / App C |

### Class V (16) — committed binaries with verification notes

| Asset | Verified against (2026-07-05) | Consumer |
|---|---|---|
| `fig_temporal_scores.pdf` | RoadAccidents127 curve video vs frozen paper caption (main.tex L268–273) | Ch 5 |
| `fig_backbone_comparison.pdf` | 24-cell ≤0.05pp vs Tables 1/2 (260622-uuu, commit 2e6cb6b — cited, byte-unchanged since) | Ch 5 |
| `fig_tta_comparison.pdf` | source means recomputed from `summary_3seed.json` = 63.7097/57.0052/58.8681/62.8276 → plotted 63.7/57.0/58.9/62.8; Ours bars 64.4/58.5/61.1/63.3 + deltas +0.67/+1.50/+2.24/+0.42 match disc_reweight anchors | Ch 6 |
| `fig_gating_distribution.pdf` | all bars match tracked per_category values of the 6 s42 canonical runs (NOTE for writers: despite the name, this is the per-category AUC/AP bar chart) | Ch 5 |
| `pri9_score_hist.png` | byte-identical to tracked `_analysis_2026-06-10` asset (giant-s42) | Ch 5 / App F |
| `fig_skeleton_overlay_b01/02/03.png` | byte-identical phase-6 B-series copies; overlays independent of eval scores; XD-only (UCF frames 64×64 — App F documents) | App F |
| `fig_temporal_extra_ucf_shooting008.png`, `..._ucf_explosion033.png`, `..._xd_blackhawkdown.png` | regenerated from 8 npz dumps validated EXACTLY (diff 0.00e+00) vs tracked eval_metrics.json | App F |
| `fig_gate_by_category_ucf/xd.png`, `fig_gate_histogram_ucf/xd.png` | regenerated from checkpoint-verified gated s42 models (official evaluate.py CLI reproduces tracked auc/ap exactly) | Ch 5 / App F |
| `fig_tsne_ucf/xd.png` | same checkpoint verification; UCF now renders its 150 Normal videos (previously invisible — see deviations) | Ch 5 / App F |
| `fig_category_scores_ucf/xd.png` | regenerated from validated npz (frame-score distributions by category) | App B / App F |

## Phase-6 disposition record (all 20 non-C PNGs; full table also in PROVENANCE.md §3a)

- **INCLUDED-V (3):** B01/B02/B03 skeleton overlays → `fig_skeleton_overlay_b01/02/03.png` (byte-identical, renamed LaTeX-safe)
- **REGENERATED-V (9):** D01×2, D02×2, E01×2, F02, F03 + A-series fresh set (3 of 5 fresh curves included as `fig_temporal_extra_*`)
- **DROPPED (8):**
  - A02_Arrest007, A04_Salt.2010: current post-h1/post-λ0 data no longer selects these videos (fresh selection: Shooting008/Shooting032/Explosion033 + GoldenEye/BlackHawkDown)
  - A03/A04-fresh equivalents (Shooting032, GoldenEye): regenerated fine but category-redundant under the App-F 2–3 budget
  - F01_cross_dataset, F04_seed_stability, F05/F06_ablation_bars: single-seed (or table-duplicating) bar charts superseded by the canonical 3-seed Tables 1–2
- **C-series (C01–C06): FORBIDDEN — never copied, never regenerated from that data.** Grep gate over thesis/figures/: 0 matches. Replacements are 13-03's `fig_corruption_source.pdf` / `fig_corruption_disc_reweight.pdf`.

## Verification chain (what makes the Class-V figures trustworthy)

1. **npz validation (8/8 EXACT):** frame-level AUC/AP recomputed from each local `eval_scores.npz` + tracked annotations matches the tracked canonical eval_metrics.json to 0.00e+00 for all 8 s42 runs (ucf/xd × 4 variants) — the local dumps ARE the canonical post-λ0/post-h1 score dumps.
2. **checkpoint validation (2/2 EXACT):** official `src/evaluate.py` CLI on scratch copies of `{ucf,xd}_gated_fusion_s42` reproduces tracked auc/ap exactly (0.816687/0.218262 and 0.923606/0.766164) — the local checkpoints are the canonical models. D/E figures derive from these verified checkpoints.
3. **Reuse figures:** re-verified against tracked anchors as listed above (no re-measurement only where a cited prior check exists and the binary is byte-unchanged).

## Task Commits

1. **Task 1: 5 reuse figures staged with Class-V verification** — `0b90849` (feat)
2. **Task 2: phase-6 disposition pass, 14 figures + script fix** — `c659dc8` (feat)
3. **Task 3: PROVENANCE.md §3 (28 rows) + §3a + Wave-0 gates** — `72c1e14` (docs)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] generate_phase6_charts.py misclassified UCF Normal videos in D/E charts**
- **Found during:** Task 2 (D/E regeneration spot-check)
- **Issue:** UCF's annotation file contains its 150 Normal test videos (category "Normal"), so the charts' bare `vid in annos` membership check typed them as anomalous: D02_ucf rendered a single-class "Normal vs Anomalous" histogram, and E01_tsne_ucf silently omitted all 150 Normal points (embedded in the t-SNE but never plotted). The May originals have the same defect (regenerated-pre-fix output was pixel-identical to the May D02_ucf, incidentally confirming the UCF checkpoint is unchanged since May). XD unaffected (its annotation file omits normals).
- **Fix:** classify by `vid in annos and not annos[vid].is_normal` in `chart_D_gate_by_category`, `chart_D_gate_histogram`, `chart_E_tsne` (both annotation classes expose `is_normal`). No tests exist for the plotting script; fix verified by regeneration output (both classes now render; 150 grey Normal points visible in the UCF t-SNE revealing the normal/anomalous cluster structure).
- **Files modified:** scripts/generate_phase6_charts.py
- **Commit:** `c659dc8`

**2. [Rule 3 - Blocking issue] Untracked regeneration inputs materialized into the worktree**
- **Found during:** Task 2
- **Issue:** parallel worktree only checks out tracked files — the 8 `eval_scores.npz`, 2 `best_model.pth` + `config_snapshot.json` pairs, and the 3 B-series PNGs exist on disk only in the main repo working tree.
- **Fix:** copied byte-identical from `D:\ViolenceCC\results\` (read-only on the main repo) into gitignored worktree scratch paths, then validated each against tracked anchors before use (same mechanism as 13-02/13-03 deviation 1). Feature caches read directly from `E:\` (regeneration inputs only, never provenance sources).
- **Files modified:** none (gitignored scratch only; git status stayed clean)
- **Commit:** n/a (no tracked-file changes)

### Notes (not deviations)

- **test_loader anti-leakage guard respected:** `src/eval/test_loader.py` refuses import outside `src/evaluate.py`/pytest. Checkpoint verification therefore ran the official `evaluate.py` CLI on scratch run-dir copies (`results/_regen1304_check/`, gitignored) instead of importing the guarded module — slightly slower, provably identical protocol.
- **B-series renamed for LaTeX:** original phase-6 filenames contain `#` (breaks `\includegraphics`); copies are byte-identical (cmp exit 0) under `fig_skeleton_overlay_b0{1,2,3}.png`; PROVENANCE rows record original names.

## Wave-0 exit gates (all green)

- `build_thesis.ps1 -Clean`: exit 0; log scan clean (no errors, no undefined refs/citations)
- pytest: **322 passed** (baseline held; script fix touched no tested code)
- `git status --porcelain`: clean after build (no thesis artifacts, no scratch leakage)
- PROVENANCE.md: 28 asset rows (9 Class R + 19 Class V) = every file in thesis/figures/ (25) + thesis/tables/ (3); every source path `git ls-files --error-unmatch` exit 0
- C-series gate: `ls thesis/figures/ | grep -ci "C0\|corruption_C"` = 0; B-series gate = 3

## Known Stubs

None introduced by this plan. The 15 PLACEHOLDER-W0 chapter/appendix bodies and the `\nocite{*}` bib smoke test remain from 13-01 **by wave design** (resolved by Wave-1/2 writers and Wave-3 integration respectively).

## Self-Check: PASSED

- All 19 staged figure files + thesis/PROVENANCE.md exist on disk — verified
- Commits `0b90849`, `c659dc8`, `72c1e14` present in git log — verified
- thesis/figures/ = 25 files, thesis/tables/ = 3 files; PROVENANCE §3 rows = 28 — verified
