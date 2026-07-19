---
task_id: 260719-gvj
title: "Exp1 consistency-rerun footnote + Exp2 learned-scalar control fold-in (Exp3 deferred)"
status: complete
completed: 2026-07-19
commit: b25a95b
files_changed:
  - thesis/chapters/ch04_experimental_setup.tex
  - thesis/chapters/ch05_results_fusion.tex
  - thesis/chapters/ch07_discussion.tex
  - thesis/PROVENANCE.md
deviations: none
---

# Quick 260719-gvj — Exp1 + Exp2 thesis fold-in Summary

Folded two post-submission defense-run findings into the thesis manuscript
using only verified numbers, leaving every published headline unchanged. Exp3
wording was deliberately not touched (author deferral).

## What was placed where (file:line, post-commit)

- **Task 1 — ch04 footnote (Exp1).** Appended one sentence inside the existing
  mixed-provenance footnote, immediately before its closing brace, after "…are
  reported as run." — `thesis/chapters/ch04_experimental_setup.tex:270`. The
  footnote now additionally cites the 29-cell version-locked consistency rerun
  (headline reproduces at 82.5\%, $-0.06$ points, all three headline seeds
  inside their seed band, every ch05 conclusion preserved; per-cell deltas in
  `results/_consistency_rerun/`). Kept as ONE footnote. No published number
  changed.
- **Task 2a — ch05 paragraph (Exp2).** New `\textbf{Learned-scalar control.}`
  paragraph inserted after the "Late fusion can degrade performance" paragraph
  and immediately before `\subsection{Pooling ablations}` —
  `thesis/chapters/ch05_results_fusion.tex:136`. Not placed inside the GF
  2-Person / bootstrap passages, per plan.
- **Task 2b — ch07 sentence (Exp2).** Supporting sentence appended after
  "…lack of any learned way to perform that suppression." —
  `thesis/chapters/ch07_discussion.tex:44`.
- **Task 2c — PROVENANCE.md.** Rows 26 (consistency rerun) and 27
  (learned-scalar late fusion) appended after row 25, following the §2 table
  format — `thesis/PROVENANCE.md:66-67`. All cited sources confirmed git-tracked.

## Numbers verified against evidence before writing (independent recompute)

The plan flagged that its numbers are the single source of truth; I independently
recomputed them from the tracked evidence and found zero discrepancies:

- **Exp1** (`results/_consistency_rerun/corrected_table_analysis.md`): headline
  Gated Giant 82.54 → 82.48 (both report 82.5; Δ $-0.06$ pp); per-seed deltas
  $-0.13/-0.15/+0.11$ vs row std 0.36 (all inside band); 29 legacy cells;
  version-locked clean worktree d2e4c2b, `scoped_dirty=false`. Match.
- **Exp2** (recomputed from `results/results-index.csv`, 24 learned rows +
  matched equal-weight/gated baselines; α extracted from the 24
  `*_learned_s*/best_model.pth` `alpha_logit` via sigmoid):
  - α range 0.4397–0.4852 → "0.44–0.49" (Verified-numbers "0.440–0.485"). Match.
  - learned vs equal-weight: UCF +0.56/−0.73/+0.12/+0.32, XD +0.52/+0.85/+0.11/+0.54
    → all within ±0.9 pts (max |0.85|). Match (SO400M ±0.01 rounding).
  - learned vs gated: UCF 1.91/2.47/2.09/2.37 (→ "1.9–2.5" AUC); XD
    12.11/10.11/12.87/10.62 (→ "10–13" AP). Match.

## Gate results (Task 3 — all 5 mandatory)

1. **Build log clean** — `build_thesis.ps1 -Clean` → LOG SCAN "clean (no errors,
   no undefined refs/citations)"; `Overfull \vbox` = 0 (also `Overfull \hbox` = 0).
   PDF written (98 pages). PASS.
2. **New-passage phrases (tr-flattened, CR-stripped)** — "consistency rerun
   retrained" in ch04, "Learned-scalar control" in ch05, "sharpens the point" in
   ch07 all PRESENT. PASS.
3. **Exp3 guard** — tr-flattened count of "effectively identical keypoints" in
   ch04 = 1 pre-edit and = 1 post-edit (re-extraction-policy subsection
   byte-identical; word-diff shows no touched lines in that region). PASS.
4. **PDF (PyMuPDF / vcc-main)** — page count 98 ∈ [96,98]; "82.5" and "78.7"
   both present; footnote fragments ("consistency rerun retrained all
   twenty-nine", "version-locked clean working tree", "results/_consistency_rerun")
   all findable; new body phrases render. PASS.
5. **Diff discipline** — `git diff --stat` limited to exactly the 4 must_haves
   files (25 insertions / 2 deletions). `git diff --word-diff` shows the only two
   deleted lines are the re-wrapped anchor lines (ch04 "reported as run.}", ch07
   "…perform that suppression. The evidence…"), both re-added verbatim; NO deletion
   token contains a digit → no existing number modified. PASS.

## Deviations from Plan

None — plan executed exactly as written. All plan numbers independently verified
against the cited evidence files (no STOP/deviation triggered). Exp3
re-extraction-policy wording left untouched per hard rule.

## Notes

- Files use CRLF working-tree endings with `core.autocrlf=true` (LF in index);
  inserted lines normalize to LF on commit, so the diff carries no line-ending
  noise.
- Build artifacts (`thesis/main.pdf`, aux/log/etc.) are git-ignored and were NOT
  committed. Per task constraints this SUMMARY, STATE.md, PLAN.md, and ROADMAP.md
  are not committed by this executor.

## Self-Check: PASSED

- All 4 changed thesis files present on disk; SUMMARY.md present.
- Commit b25a95b present in git log (4 files, 25 insertions / 2 deletions).
