---
phase: 260719-gvj-fold-exp1-consistency-rerun-footnote-cit
verified: 2026-07-19T04:32:58Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
note: >
  Verified against WORKTREE branch worktree-agent-a938c6887794cf7c0 @ b25a95b
  (NOT yet merged to main). Evidence files (results/, .planning/DEFENSE-RUNS-2026-07-17.md)
  read from MAIN repo D:/ViolenceCC. Every load-bearing number was independently
  recomputed from the CSVs and model checkpoints — not trusted from prose.
---

# Quick 260719-gvj: Exp1 + Exp2 thesis fold-in Verification Report

**Phase Goal:** Fold Exp1 (consistency-rerun footnote cite, numbers stay as-run) + Exp2
(learned-scalar late-fusion control prose) into the thesis; Exp3 untouched by author decision.
**Verified:** 2026-07-19T04:32:58Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ch04 footnote cites the 29-cell version-locked consistency rerun (82.5, −0.06 pts, conclusions preserved), keeps "reported as run", NO published number changes | ✓ VERIFIED | ch04 lines 254–276: one coherent `\footnote{}`; "reported as run." retained (L270), rerun sentence appended after it. Recomputed headline mean from comparison.csv: canonical 82.5439 → rerun 82.4843 = **−0.06 pp**; both report **82.5**. comparison.csv = **29** data rows ("twenty-nine"). Per-seed Δ −0.13/−0.15/+0.10 all < row std 0.36. word-diff: no existing digit altered. |
| 2 | ch05 "Learned-scalar control" paragraph + ch07 sentence use ONLY the verified numbers (α 0.44–0.49; within ±0.9; 1.9–2.5 AUC below gated UCF; 10–13 AP below gated XD) | ✓ VERIFIED | ch05 L136–144, ch07 L44–48. Recomputed from results-index.csv (canonical 3-seed means) + 24 checkpoints: α visual-share actual **[0.4397, 0.4852] → 0.44–0.49**; learned−equal max **|0.85| < 0.9**; UCF gated−learned **1.91/2.47/2.09/2.37 → 1.9–2.5**; XD gated−learned **12.11/10.11/12.87/10.62 → 10–13**. |
| 3 | Exp3 sentence ("effectively identical keypoints", re-extraction policy subsection) NOT touched | ✓ VERIFIED | git diff 8e8a8c6..b25a95b for ch04 = single hunk (footnote only); diff mentions no keypoint/extraction text. "effectively identical keypoints" count = **1 in both** parent and worktree (via git-normalized `git show`; earlier 0-vs-1 was a CRLF artifact of the on-disk file). Subsection byte-identical. |
| 4 | PROVENANCE.md gains rows for both additions following existing format | ✓ VERIFIED | Rows **26** (consistency rerun) and **27** (learned-scalar) appended in the exact `\| N \| claim \| value \| source \| note \|` shape of row 25. Row 27 "min 0.440 / max 0.485" matches recomputed α. |
| 5 | Clean rebuild passes — 0 errors, 0 undefined refs (excl. CJK font warning), 0 Overfull vbox, page count 97±1, headlines 82.5/78.7 present | ✓ VERIFIED | thesis/main.log (Jul 19 12:22): LaTeX Error 0, undefined references 0, undefined citations 0, Overfull \vbox 0. "Output written on main.pdf (**98 pages**)" — within [96,98]. PyMuPDF: "82.5" ✓, "78.7" ✓ present. |
| 6 | Only these 4 files change | ✓ VERIFIED | git diff --stat 8e8a8c6..b25a95b = ch04 (+7/−1), ch05 (+10), ch07 (+7/−1), PROVENANCE.md (+2). No other files. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| thesis/chapters/ch04_experimental_setup.tex | footnote append | ✓ VERIFIED | Consistency-rerun sentence in footnote (L270–276) |
| thesis/chapters/ch05_results_fusion.tex | Learned-scalar control paragraph | ✓ VERIFIED | L136–144, placed after late-fusion-degrades conclusion, before Pooling ablations |
| thesis/chapters/ch07_discussion.tex | supporting sentence | ✓ VERIFIED | L44–48, appended after suppression-mechanism anchor |
| thesis/PROVENANCE.md | 2 provenance rows | ✓ VERIFIED | rows 26, 27 |
| thesis/main.pdf (git-ignored) | clean rebuild, 98 pp | ✓ VERIFIED | built Jul 19 12:22 from b25a95b sources; not committed |

### Key Link Verification (independent recomputation)

| Check | Claimed | Recomputed from evidence | Status |
|-------|---------|--------------------------|--------|
| Headline delta | −0.06 pp; both 82.5 | 82.5439 → 82.4843 = −0.0596 (comparison.csv) | ✓ WIRED |
| Cell count | twenty-nine | 29 data rows in comparison.csv | ✓ WIRED |
| Learned α range | 0.44–0.49 | sigmoid(alpha_logit) over 24 best_model.pth → [0.4397, 0.4852] | ✓ WIRED |
| Learned vs equal | within ±0.9 pts | max \|Δ\| = 0.85 (results-index.csv 3-seed means) | ✓ WIRED |
| Learned vs gated (UCF) | 1.9–2.5 AUC below | 1.91 / 2.47 / 2.09 / 2.37 | ✓ WIRED |
| Learned vs gated (XD) | 10–13 AP below | 12.11 / 10.11 / 12.87 / 10.62 | ✓ WIRED |

### Placement Sanity

| Passage | Anchor context | Reads correctly | Status |
|---------|----------------|-----------------|--------|
| ch05 paragraph | After "…worse than not fusing at all." (late-fusion interpretation), before `\subsection{Pooling ablations}` — NOT in GF 2-Person / bootstrap passages | Yes | ✓ VERIFIED |
| ch07 sentence | After "…lack of any learned way to perform that suppression." before "The evidence…is therefore threefold" | Yes — flows naturally | ✓ VERIFIED |
| ch04 footnote | One `\footnote{}`, appended after "reported as run.", ends "(\texttt{results/\_consistency\_rerun/}).}" | Coherent single footnote | ✓ VERIFIED |

### Anti-Patterns Found

None. No TODO/FIXME/placeholder markers introduced. word-diff confirms all four files gain only additive content (plus the ch04 closing-brace reflow: "run.}" → "run. …).}", zero digit change).

### Human Verification Required

None. Every gate is objectively checkable and was checked: numbers recomputed from CSVs and checkpoints, PDF built and text-extracted, placement read in context, diff scope enumerated.

### Gaps Summary

No gaps. All seven task checks pass:
1. Every number in the three new passages traces to evidence — headline Δ and both learned-vs-gated gap ranges recomputed independently and match.
2. Footnote is one coherent block, "reported as run" discipline intact, no published number changed (word-diff clean).
3. Exp3 guard holds — re-extraction subsection byte-identical, "effectively identical keypoints" count unchanged (1→1).
4. Placement correct in both ch05 (late-fusion flow) and ch07 (after its anchor).
5. Build gates green — 0 errors, 0 undefined refs, 0 Overfull vbox, 98 pp, 82.5/78.7 present.

---

_Verified: 2026-07-19T04:32:58Z_
_Verifier: Claude (gsd-verifier)_
