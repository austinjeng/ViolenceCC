---
phase: 13-full-thesis-manuscript
plan: 02
subsystem: thesis-provenance
tags: [git-tracking, provenance, gitignore, results, manifest, spec-7a]

# Dependency graph
requires:
  - phase: 13-full-thesis-manuscript
    plan: 01
    provides: ".gitignore results/* rewrite with un-ignore rules (benchmark CSVs + _analysis_2026-06-10/); thesis/ skeleton"
provides:
  - 269 newly tracked provenance sources under results/ (git ls-files results/ = 297), every path individually asserted via git ls-files --error-unmatch
  - thesis/PROVENANCE.md scaffold — 24-row number-family table (every canonical anchor mapped to tracked sources), Class R/V figure schema, self-contained forbidden-sources appendix
affects: [13-04, 13-05..13-10 chapter writers, 13-11, 13-13 adversarial number audit, 13-VALIDATION]

# Tech tracking
tech-stack:
  added: []
  patterns: ["brace-pattern source cells in PROVENANCE.md (bash brace expansion -> git ls-files --error-unmatch per expanded path) — documented in the manifest header for 13-13's audit"]

key-files:
  created:
    - thesis/PROVENANCE.md
  modified: []
  tracked (git index only, no content edits):
    - results/benchmark_models.csv + results/backbone_bench_combined.csv (2)
    - results/_analysis_2026-06-10/* (11)
    - 128 canonical run dirs x {per_category.csv, eval_metrics.json} (256, via git add -f)

key-decisions:
  - "Tracked-source cells in PROVENANCE.md use documented bash brace patterns; the 13-02 verification expanded them to 166 concrete paths and asserted every one tracked (exit 0)"
  - "add -f vs gitignore split followed 13-01's policy comment exactly: 13 files (A+B) plain git add via the existing ! un-ignore rules; 256 run-dir files (C) via git add -f (no new gitignore rules — keeps ~880 untracked TTA JSONs out of git status)"
  - "Number-family table carries 24 rows (full RESEARCH §2 anchor table + corruption-parameters row) — superset of the plan's >=17 requirement"

patterns-established:
  - "PROVENANCE.md source-cell convention: backtick repo-relative path, optional brace pattern, line anchors outside the backticks; auditors brace-expand then assert per file"

requirements-completed: [SC3 (groundwork — clean checkout traces every canonical number family to a tracked source)]

# Metrics
duration: ~12min
completed: 2026-07-05
---

# Phase 13 Plan 02: Provenance-Source Tracking + PROVENANCE.md Scaffold Summary

**All 269 spec-named provenance sources now git-tracked with per-file assertions (results/ 28 -> 297, zero .bak), and thesis/PROVENANCE.md maps all 24 canonical number families to tracked sources with the Class R/V figure scaffold and a self-contained forbidden-sources appendix.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-04T20:34:36Z
- **Completed:** 2026-07-04T20:46:00Z (approx)
- **Tasks:** 2/2
- **Files:** 269 newly tracked + 1 created

## Accomplishments

- Tracked exactly the RESEARCH §3 MUST-TRACK list: A (2 benchmark CSVs, plain `git add` via 13-01's un-ignore rules), B (all 11 `results/_analysis_2026-06-10/` files, plain `git add`), C (`per_category.csv` + `eval_metrics.json` for the 128 canonical run dirs = 256 files, `git add -f` per 13-01's hybrid policy)
- Spec §7a assertion protocol executed in full: `git ls-files --error-unmatch` looped over all 269 paths (0 failures, no `git check-ignore` diagnostics needed); staged set diffed against the enumerated list (exact match); final count `git ls-files results/ | wc -l` = **297** (28 + 269); `git ls-files results/ | grep -c "\.bak"` = **0** — no `.pre_lam0.bak`/`.pre_h1.bak` files entered the index
- `thesis/PROVENANCE.md` created with all four required sections: (1) header with spec §7a purpose statement, 15-package preflight list (plan's 14 + lmodern from 13-01), and the exact vendored-.bst provenance wording ("copied from local MiKTeX feupphdteses package; authentic Michael Shell header v1.13 2008/09/30"); (2) 24-row number-family table with anchor values verbatim from RESEARCH §2 (UCF 82.5 ± 0.4, XD 78.7 ± 0.9, Pri-5 aggregations kept distinct, Pitfall 10/11 notes inline); (3) empty Class R / Class V figures-and-tables scaffold for 13-04; (4) forbidden-sources appendix reproducing the spec §7 list + Pitfall-13 missing-on-disk paths
- Every section-2 source cell machine-verified: 35 backtick tokens brace-expanded to 166 concrete paths, each asserted tracked (`git ls-files --error-unmatch` exit 0); Pitfall-13 paths (`phase7_summary.md`, `phase7_rtfm_gap_diagnostic`, `phase4_charts`) grep-confirmed absent outside the forbidden-sources section

## Task Commits

Each task was committed atomically:

1. **Task 1: Track the exact RESEARCH §3 file list with per-file assertions** - `a8c48aa` (chore) — 269 files, no deletions
2. **Task 2: thesis/PROVENANCE.md scaffold with complete number-family table** - `a3e37d3` (docs)

## Files Created/Modified

- `thesis/PROVENANCE.md` — provenance manifest: purpose/conventions header, 24-row number-family table, Class R/V figure scaffold, forbidden-sources appendix

## Full Asserted Path List (Task 1 — all 269, every path `git ls-files --error-unmatch` exit 0)

Compact form uses the same bash brace-expansion convention documented in
`thesis/PROVENANCE.md` §1 (13-13's audit re-asserts from PROVENANCE.md rows).

**A. Benchmark CSVs (2):**
```
results/benchmark_models.csv
results/backbone_bench_combined.csv
```

**B. `results/_analysis_2026-06-10/` (11):**
```
results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv
results/_analysis_2026-06-10/pri5_tta_breakdown.md
results/_analysis_2026-06-10/pri5_tta_breakdown.tex
results/_analysis_2026-06-10/pri6_bootstrap_ci.json
results/_analysis_2026-06-10/pri6_bootstrap_ci.md
results/_analysis_2026-06-10/pri7_per_class_complementarity.csv
results/_analysis_2026-06-10/pri7_per_class_complementarity.md
results/_analysis_2026-06-10/pri9_failure_cases.json
results/_analysis_2026-06-10/pri9_failure_cases.md
results/_analysis_2026-06-10/pri9_score_hist.png
results/_analysis_2026-06-10/verify_pri5_pri6.json
```

**C. 128 canonical run dirs × `{per_category.csv,eval_metrics.json}` (256):**
```
results/{ucf,xd}_skeleton_only_s{42,123,2024}/{per_category.csv,eval_metrics.json}                        (6 dirs)
results/{ucf,xd}_clip_only{,_siglip2,_so400m,_giant}_s{42,123,2024}/{per_category.csv,eval_metrics.json}   (24 dirs)
results/{ucf,xd}_late_fusion{,_siglip2,_so400m,_giant}_s{42,123,2024}/{per_category.csv,eval_metrics.json} (24 dirs)
results/{ucf,xd}_gated_fusion{,_siglip2,_so400m,_giant}_s{42,123,2024}/{per_category.csv,eval_metrics.json}            (24 dirs)
results/{ucf,xd}_gated_fusion{,_siglip2,_so400m,_giant}_2person_s{42,123,2024}/{per_category.csv,eval_metrics.json}    (24 dirs)
results/{ucf,xd}_gated_fusion{,_siglip2,_so400m,_giant}_clip_mean_s{42,123,2024}/{per_category.csv,eval_metrics.json}  (24 dirs)
results/xd_i3d_rtfm_i3d_s42/{per_category.csv,eval_metrics.json}                                           (1 dir)
results/xd_i3d_rtfm_i3d_flow_s42/{per_category.csv,eval_metrics.json}                                      (1 dir)
```
Backbone token (none=CLIP, `_siglip2`, `_so400m`, `_giant`) precedes the pooling
token (`_2person`, `_clip_mean`) in every dir name; expansion = 128 dirs = 256
files; commit `a8c48aa` contains exactly these 269 create-mode entries.

## Decisions Made

- **add -f vs gitignore:** no new gitignore rules were needed or added — 13-01's rewrite already un-ignores lists A and B (plain `git add` worked), and list C was added with `git add -f` exactly as 13-01's inline policy comment prescribes for the mixed-content run dirs. Zero deviation from the planned mechanics.
- **Brace-pattern source cells:** PROVENANCE.md documents the expansion convention in its header so the Wave-3 audit can mechanically re-assert every source (verified here: 166/166 expanded paths tracked).
- **24 rows instead of the enumerated ~20:** included every RESEARCH §2 anchor-table row (adding Phase-5 episodic bests, episodic inertness, TTA adapted params, and the full GF pooling-ablation grid) so no future chapter number lacks a manifest row.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Source files materialized into the worktree before `git add`**
- **Found during:** Task 1
- **Issue:** This plan executes in a parallel git worktree, which only checks out *tracked* files — all ~269 gitignored provenance sources exist on disk only in the main repo working tree (`D:\ViolenceCC\results\`), so there was nothing to `git add` in the worktree
- **Fix:** copied each of the 269 files byte-identical from the main repo working tree into the corresponding worktree path (read-only on the main repo; zero content edits), then staged
- **Files modified:** none (file contents unchanged; git index additions only)
- **Verification:** staged set diffed equal to the enumerated RESEARCH §3 list; all per-file assertions pass
- **Commit:** `a8c48aa`

## Verification Results

- `git ls-files results/ | wc -l` = **297** (expected 28 + 269) — PASS
- Per-file assertion loop over all 269 added paths: **0 failures** — PASS
- `git ls-files results/ | grep -c "\.bak"` = **0**; commit `a8c48aa` contains no `.pre_h1.bak`/`.pre_lam0.bak` paths (create-list inspected) — PASS
- Plan spot-checks (`benchmark_models.csv`, `pri9_score_hist.png`, `ucf_gated_fusion_giant_s42/per_category.csv`, `xd_gated_fusion_so400m_s42/eval_metrics.json`): exit 0 — PASS
- `grep -c "82.5" thesis/PROVENANCE.md` = 2 (≥1); `grep -c "summary_3seed.json"` = 1 (≥1) — PASS
- Pitfall-13 strings (`phase7_summary.md|phase7_rtfm_gap_diagnostic|phase4_charts`) appear **0** times outside the forbidden-sources section (awk-scoped grep) — PASS
- Number-family rows = 24 (≥17); exact string "authentic Michael Shell header v1.13" present; "Class R" and "Class V" present — PASS
- All 166 expanded section-2 source paths tracked (`git ls-files --error-unmatch` exit 0) — PASS
- pytest untouched: no source code modified (git index additions + one markdown file only)
- No deletions in either commit; `git status` clean after both commits

## Known Stubs

| Stub | File | Resolved by |
|------|------|-------------|
| §3 Figures & tables — empty Class R/V scaffold (intentional by plan design) | thesis/PROVENANCE.md | 13-04 figure regeneration/provenance pass |

## Next Phase Readiness

- Wave-3 adversarial number audit (13-13) is now passable: every canonical number family maps to a tracked source, re-assertable from PROVENANCE.md rows via the documented brace-expansion convention
- 13-04 populates the §3 figure/table scaffold; chapter writers cite §2 rows

## Self-Check: PASSED

thesis/PROVENANCE.md and 13-02-SUMMARY.md exist on disk; commits a8c48aa and a3e37d3 present in git log; `git ls-files results/` = 297.
