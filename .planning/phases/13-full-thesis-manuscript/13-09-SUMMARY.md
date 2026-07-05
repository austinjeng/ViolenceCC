---
phase: 13-full-thesis-manuscript
plan: 09
subsystem: thesis-appendices
tags: [appA, appB, appC, rtfm-repro, per-category, per-class-complementarity, sweep-detail, historical-baseline-guard]

# Dependency graph
requires:
  - phase: 13-full-thesis-manuscript
    plan: 03
    provides: "Class-R generated assets consumed here: tab_percat_{ucf,xd,rtfm}.tex, fig_sweep_s01_ucf.png, fig_sweep_s02_xd.png"
  - phase: 13-full-thesis-manuscript
    plan: 08
    provides: "Wave-1 exit gate passed (merged 9-chapter clean build); appendix placeholders + \\ref{app:a..c} promises from ch01/ch04/ch05/ch07/ch08"
provides:
  - "thesis/appendices/appA_rtfm.tex — full RTFM XD-I3D reproduction investigation (5pp): gate protocol, 0.6570 vs 0.7781 anchor with -11.11pp shortfall vs the pre-registered 0.7681 threshold, MISS-ACCEPTED disposition, flow-swap diagnostic (100% coverage, 0.5916, -6.54pp), snippet-AUC delta 0.0024, Phase-7 root cause (1024-d vs 2048-d + 3 training-regime diffs), 'training regime, not eval bug' conclusion, \\input{tables/tab_percat_rtfm}"
  - "thesis/appendices/appB_per_category.tex — per-category tables + per-class complementarity (4pp): \\input{tables/tab_percat_ucf} + \\input{tables/tab_percat_xd} with discussion; Pri-7 13-row per-class table (HM +0.31±1.08 7/10, APP -0.29±0.16 0/3, HM-APP +0.60pp, Shooting +1.05±0.20 n=22); exact hedge 'directionally supportive but mixed/noisy'; no Welch/significance test"
  - "thesis/appendices/appC_sweep.tex — hyperparameter sweep detail (5pp): 19x6 staged grid (99 configs/dataset, 198+12 runs), heatmaps at appendix scale, top-10 ranked extracts (delta columns excluded), 3-seed confirmation table; every 0.7192/0.8227/70.98/81.98 occurrence labeled historical sweep-era in-sentence; 82.5/78.7 absent"
affects: [13-11 SOTA gate (no interaction), 13-12 integration, 13-13 adversarial number audit, 13-VALIDATION]

# Tech tracking
tech-stack:
  added: []
  patterns: ["every number-bearing table carries a % Source comment naming the tracked source doc or Class-R generator (13-06 pattern continued into appendices)"]

key-files:
  created: []
  modified:
    - thesis/appendices/appA_rtfm.tex
    - thesis/appendices/appB_per_category.tex
    - thesis/appendices/appC_sweep.tex

key-decisions:
  - "-11.11pp framing quoted as the shortfall against the pre-registered gate threshold 0.7681 (published 77.81 anchor minus one point), exactly as the tracked 04b-05-SUMMARY frontmatter defines it (0.7681-0.6570=0.1111 exact). This keeps the canonical -11.11pp framing arithmetically true (the raw anchor gap 77.81-65.70 is 12.11, which is never quoted as -11.11)."
  - "App C confirmation table reports mean±std only (no per-seed columns from the generator's S03 MD) because the regenerated S03 MD's per-seed column attribution contradicts tracked 07-VERIFICATION.md (see Deferred Issues); the XD winner's per-seed values 77.69/74.93/71.47 are quoted in prose with the 07-VERIFICATION seed attribution, which S02's s42 ranked row (0.7769) independently corroborates"
  - "App C ranked-table extracts keep the generator's 0-1 scale verbatim (0.7769 etc.) — this both matches results-index.csv exactly and keeps the '82.5' substring impossible (82.54% percent-form for UCF rank 4 would have tripped the headline-absence grep)"
  - "Sweep heatmap PNGs are re-included in App C at appendix scale with distinct labels (fig:appc-sweep-*) per the plan's binding content list, even though ch05 also includes them (fig:sweep-*) — flagged for Wave-3 dedup consideration if double inclusion is unwanted"
  - "RTFM per-category prose follows the generated tab_percat_rtfm.tex category naming (G = Explosion, from per_category.csv) rather than 04b-05's prose table which mislabels G as '(Normal)'; the AP values are identical in both sources"

requirements-completed: [SC2 (partial: appendices A-C placeholder-free per spec §4), SC5 (partial: historical sweep framing + honest negative-result framing intact)]

# Metrics
duration: ~25min
completed: 2026-07-05
---

# Phase 13 Plan 09: Appendices A–C (RTFM Reproduction, Per-Category + Complementarity, Sweep Detail) Summary

**Drafted the three data appendices (14pp combined, pp. 78–91) placeholder-free: an honest RTFM negative-result narrative built only from tracked phase docs (never the missing-on-disk diagnostic files), per-category tables consumed via the generated Class-R \input files with the Pri-7 hedge verbatim, and a sweep appendix in which every historical baseline occurrence carries in-sentence historical labeling and the final headlines never appear.**

## Performance

- **Duration:** ~25 min (2026-07-05T05:22Z start)
- **Tasks:** 3/3
- **Files:** 3 appendix files drafted (placeholder → full prose); page ranges from main.toc: App A pp. 78–82 (5pp), App B pp. 83–86 (4pp), App C pp. 87–91 (5pp) — inside the plan's ~12–15pp combined target

## Verification results (all green)

- `build_thesis.ps1` (incremental) after each task: exit 0, log scan clean (no errors, no undefined refs/citations)
- appA: PLACEHOLDER-W0=0; `phase7_summary|phase7_rtfm_gap_diagnostic` = 0 (Pitfall 13); contains 0.6570 (×3), 0.5916 (×2), 11.11 (×3), "accepted", verbatim "training regime, not eval bug"; \input + \ref of tab_percat_rtfm (s42-only stated in caption and prose)
- appB: PLACEHOLDER-W0=0; "directionally supportive" = 1 (exact hedge "directionally supportive but mixed/noisy" on one line); Welch = 0; forbidden Phase-4/4c relics (0.955/0.985/88.15/44.89) = 0; both generated tables \input'ed; Pri-7 numbers match RESEARCH §2 / PROVENANCE row 17 exactly
- appC: PLACEHOLDER-W0=0; "historical" = 29 (≥2); 82.5 = 0; 78.7 = 0; all 8 occurrences of 0.8227/0.7192/82.27/71.92/81.98/70.98 verified line-by-line to carry "historical" labeling in the same sentence/caption; generator delta columns excluded from ranked tables (Δ column in the confirmation table is caption-labeled vs the historical baselines only)
- Cross-file forbidden-value grep (83.6/71.8/13.9/0.9268/0.9452/0.955/0.985/88.15/44.89/0.008): NONE across all three appendices
- \label{app:a}, \label{app:b}, \label{app:c} all retained (ch01/ch04/ch05/ch07/ch08 \ref promises resolve)
- Overfull hboxes: the one box my appC table introduced (40.9pt) was fixed before commit; appendix-file overfulls now belong only to appE's pre-existing placeholder (sibling writer's scope); total log count 11 → 10
- `git status --short` clean after final build (regenerated results/phase7_charts/ scratch is gitignored by the results/* policy)

## Task Commits

1. **Task 1: Appendix A (RTFM reproduction investigation)** — `38ee8a5` (docs)
2. **Task 2: Appendix B (per-category + per-class complementarity)** — `b9ca1a0` (docs)
3. **Task 3: Appendix C (sweep detail, historical configuration)** — `d8338a0` (docs)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] S03 confirmation MD (read_first input) absent from disk — regenerated via the tracked Class-R path**
- **Found during:** Task 3 setup (also needed for Task 3's ranked-table extracts)
- **Issue:** `results/phase7_charts/` is untracked regenerable scratch (13-03 policy); it existed neither in this worktree nor in the main repo working tree, so the plan's content source for the confirmation-runs section was missing.
- **Fix:** regenerated S01–S05 by running the tracked generator over the tracked index: `C:/Anaconda/envs/vcc-main/python.exe scripts/generate_phase7_charts.py --with-confirm` (exit 0; 99 XD + 99 UCF configs loaded). Outputs remain untracked gitignored scratch; all values consumed from them were cross-checked against tracked 07-VERIFICATION.md.
- **Files modified:** none (scratch regeneration only)
- **Commit:** n/a (no repo change)

### Intentional adaptations (documented, not silent)

**2. −11.11pp attached to the gate threshold, not the raw anchor:** the spec/plan shorthand "0.6570 vs 77.81 anchor (−11.11pp)" is arithmetically the shortfall vs the pre-registered threshold 0.7681 (anchor − 1pp), which is how tracked 04b-05-SUMMARY's frontmatter defines it. App A states both the anchor and the threshold and quotes −11.11pp against the threshold, keeping the canonical number exact.

**3. Confirmation table uses mean±std, not the generator's per-seed columns** (see key-decisions; generator seed-attribution discrepancy logged below).

## Deferred Issues

- **`scripts/generate_phase7_charts.py` S03 per-seed column attribution appears swapped:** the regenerated S03_confirmation_comparison.md lists the XD winner as s42=74.93/s123=71.47/s2024=77.69, but tracked 07-VERIFICATION.md records s42=77.69/s123=74.93/s2024=71.47, and S02's own s42 ranked row (0.7769 for lr1e-3/k2) corroborates the latter. Mean/std are unaffected (74.69±2.55 either way). Pre-existing generator issue, out of this plan's scope; App C avoids per-seed column attribution from S03 entirely. Worth a one-line fix if the generator is touched again.
- **Sweep heatmaps now appear twice** (ch05 fig:sweep-* and App C fig:appc-sweep-* reference the same two PNGs) per the plan's binding App C content list; Wave-3 polish may prefer to keep only the appendix copies and have ch05 point forward, or vice versa.

## Known Stubs

None — all three appendices are placeholder-free full prose; appD/appE/appF placeholders remain by wave design (sibling 13-10 writer's scope).

## Threat Flags

None — no code, no new surface. T-13-09 (historical-vs-current confusion) mitigations applied as specified: binding labeling rule enforced line-by-line on every baseline occurrence, 82.5/78.7 grep = 0 in appC, Phase-4/4c relic grep = 0 in appB.

## Self-Check: PASSED

- thesis/appendices/appA_rtfm.tex, appB_per_category.tex, appC_sweep.tex exist with full content, PLACEHOLDER-W0 absent, \label{app:a..c} retained — verified
- Commits 38ee8a5, b9ca1a0, d8338a0 present in git log — verified
- Final incremental build exit 0 with clean log scan; git status clean — verified
