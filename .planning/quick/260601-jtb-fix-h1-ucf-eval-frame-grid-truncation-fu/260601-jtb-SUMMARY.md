---
phase: quick-260601-jtb
plan: 01
subsystem: evaluation
tags: [h1, ucf, eval, frame-grid, truncation, analysis-pause-point]
requires: [results/ucf_*/eval_scores.npz, results/ucf_*/eval_metrics.json, E:/snippets/ucf/*_boundaries.json, data/annotations/ucf_temporal.txt]
provides: [results/h1_recompute/ucf_fulllength_comparison.csv, results/h1_recompute/ucf_giant_s42_per_category.csv, boundary-aware UCF eval length]
affects: [src/evaluate.py]
tech-stack:
  added: []
  patterns: [read-only offline recompute, os.replace-after-gate, cfg-gated non-breaking patch, one-time eval-stub warning]
key-files:
  created:
    - scripts/recompute_fulllength_ucf.py
    - results/h1_recompute/ucf_fulllength_comparison.csv
    - results/h1_recompute/ucf_giant_s42_per_category.csv
    - results/h1_recompute/xd_SKIPPED.txt
    - tests/test_h1_fulllength_grid.py
  modified:
    - src/evaluate.py
decisions:
  - "Force-added results/h1_recompute/ CSVs (results/ is gitignored by D-07) so the analysis artifacts are committed alongside the script per the plan's atomic-commit instruction"
  - "warnings.warn alone (no logging import) for the truncated-length warning — keeps the patch minimal per plan guidance"
metrics:
  duration: ~25min
  completed: 2026-06-01
---

# Quick Task 260601-jtb: Fix H1 UCF Eval Frame-Grid Truncation Summary

Boundary-aware full-length UCF AUC/AP: an offline read-only recompute over all
29 `results/ucf_*` runs (verified against the giant-s42 gate) plus a non-breaking
`src/evaluate.py` patch that derives true `n_frames = total_frames*10` from
snippet boundary JSONs when `paths.snippet_boundaries_dir` is set.

## What Was Built

- **Task 1 (Layer 1):** `scripts/recompute_fulllength_ucf.py` — read-only,
  GPU-free. Recovers per-snippet scores from `eval_scores.npz`
  (`arr.reshape(n_snip, 640)[:, 0]`), rebuilds full-length frame scores via
  `snippet_to_frame(..., n_frames=total_frames*10)`, and recomputes global
  AUC/AP via the existing `compute_frame_metrics` (no sklearn reimplementation).
  Writes only under `results/h1_recompute/`. Hard gate on
  `ucf_gated_fusion_giant_s42`; CSV finalized via `os.replace` only after the
  gate passes.
- **Task 2 (Layer 2):** surgical patch to the UCF default path in
  `_build_frame_arrays`. When `cfg.paths.snippet_boundaries_dir` is set and
  `{vid}_boundaries.json` exists, `n_frames = total_frames*upsample` (true full
  length); otherwise current behavior + one-time `warnings.warn`. `xd_i3d`/`xd`
  branches untouched.
- **Task 3:** `tests/test_h1_fulllength_grid.py` locks tail-pad-to-true-length.

## Hard Gate Result (giant s42)

```
GATE PASS: H1 GATE ucf_gated_fusion_giant_s42: new_auc=0.824904 (expected ~0.8249, d=+0.000004)  new_ap=0.273712 (expected ~0.2737, d=+0.000012)
```

Both within ±0.001 (AUC d=+0.000004, AP d=+0.000012). Plan one-liner check:
`GATE PASS rows= 29`.

## Full UCF Comparison CSV (results/h1_recompute/ucf_fulllength_comparison.csv)

All 29 rows. `n_frames_old=1,010,560` -> `n_frames_new=1,097,050` for every run
(+8.56% more frames recovered); `n_skipped=0` for all runs (every video had a
boundary JSON). AUC/AP both DROP under the corrected full length, confirming the
old snippet-grid length inflated the numbers.

| run_name | old_auc | new_auc | d_auc | old_ap | new_ap | d_ap | n_videos | n_frames_old | n_frames_new | n_skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| ucf_clip_only_giant_s42 | 0.830904 | 0.823624 | -0.007280 | 0.252007 | 0.231113 | -0.020894 | 254 | 1010560 | 1097050 | 0 |
| ucf_clip_only_s42 | 0.816850 | 0.811182 | -0.005668 | 0.223399 | 0.211921 | -0.011478 | 254 | 1010560 | 1097050 | 0 |
| ucf_clip_only_siglip2_s42 | 0.791143 | 0.783157 | -0.007987 | 0.196208 | 0.181774 | -0.014434 | 254 | 1010560 | 1097050 | 0 |
| ucf_clip_only_so400m_s42 | 0.814084 | 0.809292 | -0.004792 | 0.206981 | 0.199969 | -0.007011 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_2person_s42 | 0.816519 | 0.811173 | -0.005346 | 0.220102 | 0.211111 | -0.008991 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_clip_mean_s42 | 0.817769 | 0.810787 | -0.006982 | 0.234174 | 0.219621 | -0.014553 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_giant_2person_s42 | 0.834803 | 0.827311 | -0.007492 | 0.244738 | 0.230276 | -0.014462 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_giant_clip_mean_s42 | 0.836258 | 0.829822 | -0.006436 | 0.271660 | 0.255351 | -0.016309 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_giant_s123 | 0.836513 | 0.829231 | -0.007282 | 0.258522 | 0.243796 | -0.014726 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_giant_s2024 | 0.829612 | 0.822182 | -0.007430 | 0.221601 | 0.210716 | -0.010885 | 254 | 1010560 | 1097050 | 0 |
| **ucf_gated_fusion_giant_s42** | **0.832266** | **0.824904** | **-0.007362** | **0.292162** | **0.273712** | **-0.018449** | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_s123 | 0.816835 | 0.811088 | -0.005748 | 0.227153 | 0.215401 | -0.011752 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_s2024 | 0.819958 | 0.813959 | -0.005999 | 0.235257 | 0.223508 | -0.011749 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_s42 | 0.822651 | 0.816687 | -0.005965 | 0.231464 | 0.218262 | -0.013202 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_siglip2_2person_s42 | 0.794812 | 0.787231 | -0.007581 | 0.195036 | 0.183853 | -0.011183 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_siglip2_clip_mean_s42 | 0.799990 | 0.793517 | -0.006473 | 0.247840 | 0.229533 | -0.018307 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_siglip2_s123 | 0.800264 | 0.790428 | -0.009835 | 0.225963 | 0.209336 | -0.016627 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_siglip2_s2024 | 0.796557 | 0.788936 | -0.007621 | 0.201150 | 0.188318 | -0.012831 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_siglip2_s42 | 0.796116 | 0.790320 | -0.005795 | 0.201771 | 0.192678 | -0.009092 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_so400m_2person_s42 | 0.819697 | 0.813267 | -0.006430 | 0.213047 | 0.203244 | -0.009803 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_so400m_clip_mean_s42 | 0.824494 | 0.818401 | -0.006093 | 0.219797 | 0.212029 | -0.007768 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_so400m_s123 | 0.820585 | 0.813730 | -0.006854 | 0.224954 | 0.214245 | -0.010709 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_so400m_s2024 | 0.814624 | 0.809316 | -0.005307 | 0.205128 | 0.197697 | -0.007431 | 254 | 1010560 | 1097050 | 0 |
| ucf_gated_fusion_so400m_s42 | 0.821781 | 0.815207 | -0.006574 | 0.204658 | 0.197065 | -0.007593 | 254 | 1010560 | 1097050 | 0 |
| ucf_late_fusion_giant_s42 | 0.808766 | 0.807627 | -0.001139 | 0.196414 | 0.194288 | -0.002126 | 254 | 1010560 | 1097050 | 0 |
| ucf_late_fusion_s42 | 0.787094 | 0.785842 | -0.001253 | 0.187355 | 0.185609 | -0.001746 | 254 | 1010560 | 1097050 | 0 |
| ucf_late_fusion_siglip2_s42 | 0.799254 | 0.794558 | -0.004697 | 0.202431 | 0.196445 | -0.005986 | 254 | 1010560 | 1097050 | 0 |
| ucf_late_fusion_so400m_s42 | 0.802629 | 0.800098 | -0.002531 | 0.189359 | 0.186729 | -0.002630 | 254 | 1010560 | 1097050 | 0 |
| ucf_skeleton_only_s42 | 0.717960 | 0.717890 | -0.000070 | 0.152661 | 0.147569 | -0.005092 | 254 | 1010560 | 1097050 | 0 |

(Float-exact values are in `results/h1_recompute/ucf_fulllength_comparison.csv`;
the table above is rounded to 6 dp.)

## XD Result

`results/h1_recompute/xd_SKIPPED.txt` written (no `--xd-boundaries-dir` provided):

```
XD full-length recompute skipped: no boundary data; expected ~0 change since upsample_factor=1 and overshoot <= one snippet window
```

XD uses `upsample_factor=1`, so the per-video overshoot is at most one snippet
window — H1 impact on XD is expected to be ~0. The XD branch is implemented and
will run if `--xd-boundaries-dir` is later supplied.

## pytest Result

New regression test (Task 3):
```
tests/test_h1_fulllength_grid.py ... 3 passed in 0.30s
```

Existing eval regression suite (Task 2 non-breaking verification):
```
tests/test_evaluate_cli.py tests/test_evaluate_xd.py tests/test_evaluate_xd_i3d.py tests/test_snippet_to_frame.py ... 25 passed in 49.43s
```

`python -c "import ast; ast.parse(open('src/evaluate.py').read())"` -> `parse ok`.

## Analysis Note (numbers only — NOT paper conclusions)

Read the relevant rows for the two requested checks. These are observations on
the comparison CSV; no paper edit is implied.

**Gated-CLIP vs visual-only-CLIP margin (does the recompute change it?)**

- ViT-B/16 (`ucf_gated_fusion_s42` vs `ucf_clip_only_s42`):
  - AUC margin: old +0.0058 -> new +0.0055 (essentially unchanged; gated still > clip-only).
  - AP margin: old +0.0081 -> new +0.0063 (shrinks slightly; gated still > clip-only).
- Giant (`ucf_gated_fusion_giant_s42` vs `ucf_clip_only_giant_s42`):
  - AUC margin: old +0.0014 -> new +0.0013 (essentially unchanged).
  - AP margin: old +0.0402 -> new +0.0426 (slightly widens in favor of gated).

So the gated-vs-visual-only-CLIP ordering is preserved under the recompute; the
margins move by <=~0.002 except the giant AP margin which widens ~0.002.

**Per-row best-backbone change (does the top run change?)**

- Best **AUC** run: old top = `ucf_gated_fusion_giant_s123` (0.8365) ->
  new top = `ucf_gated_fusion_giant_clip_mean_s42` (0.8298). **The argmax-AUC
  run changes** under the recompute (giant_s123 and giant_clip_mean re-order;
  both are giant variants and within ~0.001 of each other on the new grid).
- Best **AP** run: `ucf_gated_fusion_giant_s42` both old (0.2922) and new
  (0.2737) — **unchanged**.

Magnitude of the correction: AUC drops cluster around -0.005 to -0.008 for
fusion/CLIP runs (late-fusion and skeleton-only drop less, -0.0001 to -0.005,
because their score profiles are flatter over the tail-padded region); AP drops
are larger, roughly -0.005 to -0.021.

## Deviations from Plan

### Auto-fixed / process notes

**1. [Rule 3 - Blocking] `results/` is gitignored (D-07); CSVs force-added**
- **Found during:** Task 1 commit.
- **Issue:** The plan instructs committing the comparison CSV(s) with the
  script, but `results/` is excluded by `.gitignore:9`. A plain `git add` would
  silently drop the CSVs.
- **Fix:** `git add -f` the three `results/h1_recompute/` outputs only (the
  analysis artifacts the plan explicitly names). No run-dir or other gitignored
  artifact was force-added.
- **Files:** results/h1_recompute/{ucf_fulllength_comparison.csv,
  ucf_giant_s42_per_category.csv, xd_SKIPPED.txt}
- **Commit:** 1aae28a

**2. [Process] `conda run` cannot execute multi-line `-c` scripts on Windows**
- The plan's verify one-liners (single-line) ran fine. For the multi-line
  analysis-margin computation I wrote a temporary `scripts/_h1_analysis_note.py`,
  ran it in vcc-main, captured the numbers above, and deleted it (never
  committed). No code change.

## Scope Verification

`git diff --name-only 1aae28a~1 HEAD` shows ONLY the 6 intended files:
`scripts/recompute_fulllength_ucf.py`, `src/evaluate.py`,
`tests/test_h1_fulllength_grid.py`, and the three `results/h1_recompute/`
outputs. No `paper/*`, no `results-index.csv`, no run-dir `eval_metrics.json` /
`eval_scores.npz` / `per_category.csv`, no `tables_generated.tex` / `main.tex`,
no figure was modified. This remains an analysis pause-point for human review
before any paper/canonical change.

## Commits

- `1aae28a` feat(eval): full-length UCF recompute script + H1 comparison
- `7bdb3c4` fix(eval): derive UCF eval length from snippet boundaries (H1), warn when truncated

## Self-Check: PASSED

- scripts/recompute_fulllength_ucf.py — FOUND
- results/h1_recompute/ucf_fulllength_comparison.csv — FOUND (29 rows)
- results/h1_recompute/ucf_giant_s42_per_category.csv — FOUND
- results/h1_recompute/xd_SKIPPED.txt — FOUND
- src/evaluate.py — FOUND (patched)
- tests/test_h1_fulllength_grid.py — FOUND (3 passed)
- commit 1aae28a — FOUND
- commit 7bdb3c4 — FOUND
- giant-s42 gate — PASS (new_auc=0.824904, new_ap=0.273712, both within 0.001)
