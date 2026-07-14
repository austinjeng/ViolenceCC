---
task: 260714-gd8
title: Archive thesis appendices A–F out of the build (restorable)
status: complete
date: 2026-07-14
commits:
  - f860753  # refactor(thesis): archive appendices A-F out of the build (restorable)
files_changed:
  - thesis/main.tex
  - thesis/appendices_archived/README.md            # new
  - thesis/appendices_archived/appA_rtfm.tex         # git mv from thesis/appendices/
  - thesis/appendices_archived/appB_per_category.tex # git mv
  - thesis/appendices_archived/appC_sweep.tex        # git mv
  - thesis/appendices_archived/appD_engineering.tex  # git mv
  - thesis/appendices_archived/appE_reproducibility.tex # git mv
  - thesis/appendices_archived/appF_figures.tex      # git mv
  - thesis/chapters/ch01_introduction.tex
  - thesis/chapters/ch04_experimental_setup.tex
  - thesis/chapters/ch05_results_fusion.tex
  - thesis/chapters/ch07_discussion.tex
  - thesis/chapters/ch08_limitations.tex
  - thesis/chapters/ch09_conclusion.tex
  - thesis/PROVENANCE.md
---

# Quick Task 260714-gd8: Archive thesis appendices A–F out of the build — Summary

Archived Appendices A–F out of the thesis build restorably (history-preserving `git mv` to
`thesis/appendices_archived/` + a README restore recipe), reworded all 19 body cross-references
plus the two hidden appendix-figure refs and the §1.7 roadmap sentence so the PDF has zero broken
references and zero pointers to absent material, and rebuilt clean. One refactor commit; no fallout
fix was needed.

## What was done (Task 1 — commit f860753)

1. **Move (history-preserving).** `git mv` of all six appendix sources
   `thesis/appendices/*.tex → thesis/appendices_archived/*.tex` (same filenames; all six show as
   100% renames in `git show --stat`). Deleted the stale git-ignored `thesis/appendices/*.aux`
   artifacts so the emptied directory disappears.
2. **README.** Wrote `thesis/appendices_archived/README.md`: what the six files are, why archived
   (author decision 2026-07-14), the **verbatim** `\appendix` + six-`\include` block removed from
   `main.tex`, the 4-step restore recipe (git mv back → re-insert the verbatim block →
   `git show 484b84b -- thesis/chapters/` to recover the cross-references → rebuild), and the
   table note (`tab_percat_{ucf,xd,rtfm}.tex` stay in `thesis/tables/`; only archived appA/appB
   `\input` them — appA inputs `tab_percat_rtfm`, appB inputs `tab_percat_ucf/xd`).
3. **main.tex.** Deleted the `%% Appendices` header + `\appendix` + six `\include{appendices/...}`
   lines; replaced with a 2-line comment pointing at `appendices_archived/README.md`.
4. **Rewordings (CONTEXT decisions 1–8).** 19 `app:` refs + 2 `fig:appc-sweep-*` figure refs + the
   ch05:591 LaTeX comment, all reworded so every factual claim is preserved and no sentence points
   to absent material:
   - ch01 delta list → dropped app:a/app:b/app:d/app:e pointers; item (b) now cites §5.7–5.9 +
     the RTFM investigation summarized in `sec:lim-gaps`; dropped the appendices-D/E item.
   - ch01 reproducibility pointer → states the measures (committed configs, data manifests, tracked
     per-run metrics) instead of pointing to Appendix E.
   - ch01 §1.7 roadmap → deleted the "Six appendices provide…" sentence; roadmap ends at Chapter 9.
   - ch04 ×3 → repository reproduction path (was app:e); dropped the app:d engineering-pitfalls
     pointer sentence; table caption I3D note → RTFM reproduction summarized in `sec:lim-gaps`.
   - ch05 ×6 → per-class breakdown now points to the Chapter 7 discussion; sweep heatmap sentence
     keeps the 99-config/seed-42 fact without the app:c/figure pointers; app:c "full grids" sentence
     → "omitted from this thesis"; figure caption → §5.8 per-category summary; §5.8 comment + prose
     → "omitted here / not rendered in the thesis body".
   - ch07 → dropped "in Appendix~\ref{app:b}" (the per-class numbers are stated in-place).
   - ch08 → RTFM pointer replaced with the decision-7 clause (harness cleared against an independent
     snippet-vs-frame sanity anchor; gap localized to the training side — feature dimensionality,
     MTN, batch size). No new claims (all grounded in the archived appA + §8.1).
   - ch09 → repository reproduction path (was app:e).
5. **PROVENANCE.** Appended one dated note (no rows rewritten).

## Verification gate (Task 2 — all substantive gates GREEN; measured values)

| Gate | Requirement | Measured | Result |
|------|-------------|----------|--------|
| Clean build | `build_thesis.ps1 -Clean` exit 0 | exit 0; script LOG SCAN "clean (no errors, no undefined refs/citations)" | PASS |
| `??` in PDF | zero | 0 | PASS |
| `[?]` in PDF | zero | 0 | PASS |
| Rendered "Appendix" mentions | zero | 0 | PASS |
| TOC Appendix entries | none | none | PASS |
| TOC last chapter-level entry | References | References (p.76, after ch9) | PASS |
| LoF/LoT A.x–F.x items | none | none | PASS |
| `app:` refs in chapters/frontmatter | 0 | 0 | PASS |
| `fig:appc` refs in chapters | 0 | 0 | PASS |
| Appendix mentions outside `%` comments | 0 | 0 (only main.tex:48/:61/:62, all comments) | PASS |
| `\bibitem` in main.bbl | 45 | 45 (all markers [1]–[45] render) | PASS |
| Front matter | untouched | `git diff --stat HEAD -- thesis/frontmatter/` empty | PASS |
| Working tree (thesis/) | clean apart from build artifacts | clean (only pre-existing untracked `thesis_requirements.pdf`) | PASS |
| Page count | ~101–105 (estimate) | **98** | see note |

**Log note:** the only "undefined" token in `main.log` is a pre-existing `LaTeX Font Warning: Font
shape 'C70/bkai/b/n' undefined` (bold Chinese-kai fallback in the untouched zh front matter) — zero
reference/citation "undefined" warnings.

## Deviations from Plan

**Page count measured 98, not the estimated ~101–105 — correct, not a defect.** The 131→98 drop of
33 pages = the ~30 appendix body pages (Appendix A started at p.102, so A–F spanned p.102–131)
**plus ~3 front-matter pages** of TOC/LoF/LoT appendix listing entries that were removed along with
the appendices. The plan's estimate subtracted only the appendix body (131−30≈101) and did not
account for the front-matter listing shrinkage. No body content was lost (all 9 chapters render, all
45 references [1]–[45] present, zero `??`/`[?]`, clean citation log), so this is the honest result
of a complete, surgical removal. Padding the thesis to reach an arbitrary page number would be
dishonest, so **no source fix was applied and no fallout commit was made** (fallout policy: commit
only if fixes were needed). Every qualitative gate defining "appendices fully absent with zero
broken references" passes.

No other deviations. Front matter and `references.bib` untouched; headlines (UCF 82.5 / XD 78.7)
unaffected (prose-only rewording, no numbers changed).

## Restore recipe (self-contained)

`thesis/appendices_archived/README.md` names the six files, embeds the verbatim `main.tex` block,
records the parent commit `484b84b` for chapter-ref restoration, and gives the rebuild command.

## Self-Check: PASSED

- All six `thesis/appendices_archived/*.tex` exist; none remain under `thesis/appendices/`.
- `thesis/appendices_archived/README.md` exists and contains the verbatim `\include{appendices/appA_rtfm}` block.
- Commit `f860753` exists on main (`refactor(thesis): archive appendices A-F out of the build (restorable)`, 6 renames + README + 8 edits).
- Clean thesis PDF rebuilds (98pp) with zero broken references and zero PDF-visible appendix mentions.
