---
task_id: 260719-gvj
description: Fold Exp1 (consistency-rerun footnote cite) and Exp2 (learned-scalar late-fusion control) into the thesis; Exp3 wording DEFERRED by author decision
planned_by: Fable (orchestrator-as-brain, per author instruction); workers = Opus 4.8
must_haves:
  truths:
    - The ch04 smoothness footnote additionally cites the 29-cell version-locked consistency rerun (headline reproduces at 82.5, -0.06 points, conclusions preserved) and keeps "reported as run" — NO published number changes anywhere.
    - ch05 gains one short "Learned-scalar control" paragraph and ch07 gains one supporting sentence, both using ONLY the verified numbers listed in this plan (alpha 0.44-0.49; within +-0.9 pts of equal-weight; 1.9-2.5 AUC below gated on UCF; 10-13 AP below gated on XD).
    - The Exp3-related sentence in ch04 ("produces effectively identical keypoints", re-extraction policy subsection) is NOT touched — author explicitly deferred Exp3 wording to a later edit.
    - PROVENANCE.md gains rows for both additions, following its existing row format.
    - Clean rebuild passes - 0 errors, 0 undefined refs (excluding the pre-existing C70/bkai CJK font warning), 0 Overfull vbox, page count 97 plus/minus 1, headlines 82.5/78.7 present.
    - Only these files change: thesis/chapters/ch04_experimental_setup.tex, thesis/chapters/ch05_results_fusion.tex, thesis/chapters/ch07_discussion.tex, thesis/PROVENANCE.md.
  artifacts:
    - Edited thesis sources + rebuilt main.pdf (pdf git-ignored, never committed)
  key_links:
    - results/_consistency_rerun/corrected_table_analysis.md (Exp1 evidence)
    - results/results-index.csv learned rows + .planning/DEFENSE-RUNS-2026-07-17.md (Exp2 evidence)
---

# Plan 260719-gvj — Exp1 + Exp2 thesis fold-in (Exp3 deferred)

## Verified numbers (single source of truth for every new sentence)

Exp1 (Job C, results/_consistency_rerun/): 29 legacy cells retrained with released
code in a version-locked clean worktree (d2e4c2b, scoped_dirty=false). Headline
gated-fusion Giant: 82.54 -> 82.48 (both report 82.5; delta -0.06 pp; per-seed deltas
-0.130/-0.154/+0.105 all within row seed std 0.355). Every qualitative conclusion of
ch05 preserved (gated>=visual on all 4 UCF backbones, ordering unchanged).

Exp2 (Job B, 24 runs, results-index.csv *_late_fusion_*_learned_*): learned scalar
alpha (visual share, sigmoid of the single trainable logit) converges to
0.440-0.485 across 8 configs x 3 seeds. Learned vs equal-weight deltas: UCF +0.56,
-0.73, +0.13, +0.32; XD +0.52, +0.85, +0.10, +0.54 (all within +-0.9 pts). Learned
vs gated: UCF 1.91/2.47/2.09/2.37 AUC below; XD 12.11/10.11/12.88/10.62 AP below.

## Task 1 — ch04 footnote append (Exp1)

File: thesis/chapters/ch04_experimental_setup.tex. Anchor: the footnote ending
"The UCF-Crime results are reported as run.}" (currently lines ~254-270).
INSERT immediately before the closing brace, after "reported as run.":

"A post-submission consistency rerun retrained all twenty-nine
legacy-implementation cells with the released code under a version-locked clean
working tree: the headline reproduces at 82.5\% ($-0.06$ points, with all three
headline seeds inside their seed band) and every qualitative conclusion of
Chapter~\ref{ch:05} is preserved; per-cell deltas are tracked in the released
repository (\texttt{results/\_consistency\_rerun/})."

Keep the footnote as ONE footnote; re-wrap lines to the file's ~80-col style.

## Task 2 — ch05 paragraph + ch07 sentence + PROVENANCE (Exp2)

(a) ch05_results_fusion.tex: place ONE new paragraph immediately after the prose
that interprets the Late Fusion rows of Tables 5.1/5.2 (read the section and pick
the point where late-fusion underperformance is concluded — do NOT place it inside
the GF 2-Person or bootstrap passages). Canonical text:

"\textbf{Learned-scalar control.} Replacing late fusion's fixed equal weight with
a single learned mixing coefficient does not repair it: across all eight
backbone$\times$dataset configurations (three seeds each), the learned
coefficient converges to 0.44--0.49 visual share --- essentially its
equal-weight initialization --- and the resulting scores stay within $\pm0.9$
points of the fixed-weight variant, 1.9--2.5 AUC points below gated fusion on
UCF-Crime and 10--13 AP points below on XD-Violence. A \emph{static} learned
weight therefore cannot escape the late-fusion failure mode; the reweighting
must be input-dependent (run records:
\texttt{results/results-index.csv})."

(b) ch07_discussion.tex: anchor "equal-weight late fusion underperforms,
consistent with its lack of any learned way to perform that suppression."
(currently lines ~43-44). APPEND after that sentence:

"A learned-scalar control sharpens the point: given a single trainable mixing
coefficient, the coefficient stays near equal weighting (0.44--0.49) and the
result within a point of fixed-weight late fusion, still 10--13 AP points below
gated fusion on XD-Violence --- static reweighting, learned or not, does not
suffice."

(c) thesis/PROVENANCE.md: append two rows following the existing table format
(next free row numbers): one for the footnote's rerun claim (source:
scripts/run_ucf_consistency_rerun.py + compare_consistency_rerun.py;
results/_consistency_rerun/comparison.csv + corrected_table_analysis.md), one
for the learned-scalar numbers (source: scripts/run_ablations.py --queue
learned_late_fusion; results/results-index.csv learned rows; alpha extracted
from best_model.pth sigmoid(alpha_logit); .planning/DEFENSE-RUNS-2026-07-17.md).

## Task 3 — rebuild + gates

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean
Gates (ALL mandatory):
1. Build log: 0 errors, 0 undefined refs/citations (build script LOG SCAN "clean"), 0 `Overfull \vbox`.
2. tr-flattened grep: "consistency rerun retrained" present in ch04; "Learned-scalar control" present in ch05; "sharpens the point" present in ch07.
3. Exp3 guard: tr-flattened count of "effectively identical keypoints" in ch04 UNCHANGED from pre-edit (record before/after) — the re-extraction policy subsection must be byte-identical.
4. PDF (PyMuPDF, C:/Anaconda/envs/vcc-main/python.exe): page count in [96,98]; "82.5" and "78.7" present; footnote text findable in extracted text.
5. git diff --stat limited to the four files in must_haves; git diff --word-diff shows NO digit changes outside the two new passages + footnote addition + PROVENANCE rows.
