---
phase: 12-sota-comparison-and-positioning
reviewed: 2026-06-21T06:52:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - paper/sota_comparison_full.tex
  - paper/main.tex
  - paper/references.bib
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-06-21T06:52:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the Phase 12 additions (diff `16f70fd..HEAD`) to three LaTeX/BibTeX
sources: the new standalone thesis fragment `paper/sota_comparison_full.tex`,
the §2 number-backfill plus the new condensed `tab:comparison` table in
`paper/main.tex`, and the six new SOTA bib entries in `paper/references.bib`.
Scope was limited to intrinsic LaTeX/BibTeX defects a compile-clean build could
still hide (column-count mismatches, undefined refs, unescaped specials,
duplicate/shadowed bib keys, cite/key mismatches, intra-file number
contradictions). External-source number traceability was already audited in
12-VERIFICATION.md and was not re-checked.

The artifacts are in good intrinsic shape. Verified clean:

- **Column counts match in all three tables.** `tab:comparison` (`{l l c c l}`,
  5 cols), `tab:sota-full` (`{l c l c c l}`, 6 cols), and `tab:sota-fair`
  (`{l c c c p{0.40\linewidth}}`, 5 cols) each have headers and data rows with
  the correct ampersand count. No mismatched rows.
- **All `\ref` targets resolve.** `tab:comparison`, `tab:sota-full`,
  `tab:sota-fair` are each labeled exactly once and referenced consistently.
- **Cite/key integrity is complete.** All 6 new keys
  (`joo2023cliptsa`, `zhou2023urdmu`, `chen2023mgfn`, `wang2024lightwvad`,
  `majhi2025pivad`, `yin2026dsanet`) are cited in the new `tab:comparison`
  table and all `\cite` targets in the new content resolve to bib keys. No
  orphan keys, no orphan cites.
- **No duplicate bib keys.** All 24 keys in `references.bib` are unique; the 6
  new keys follow the `firstauthorYYYYkeyword` convention.
- **Special characters are escaped/delimited correctly.** The HyperVD venue
  cell escapes `&` as `\&` (`Image\,\&\,Vis.\,Comp.'24`); `$\pi$` in
  `majhi2025pivad` and `$\times$`/`$^{...}$` in table cells are properly
  math-delimited. Trailing `% RE-VERIFY` comments after `\\` row terminators are
  valid LaTeX.
- **Footnote markers are matched.** Superscripts `a`–`n` used in `tab:sota-full`
  rows each have a corresponding caveat note in the table's `flushleft` block;
  no dangling or unused note letters.
- **Intra-file numbers are self-consistent.** The "This work" headline
  (82.5 / 78.7) is identical across both tables and all positioning prose in
  `sota_comparison_full.tex`; MGFN (86.98 / 79.19), RTFM (84.30 / 77.81),
  Light-WVAD (84.7 / 77.3), CLIP-TSA (87.58 / 82.19), UR-DMU (86.97 / 81.66),
  and Sultani (75.41) agree between the `main.tex` prose paragraph and its own
  `tab:comparison` rows.

Two warnings (bib-hygiene on the two preprint-as-proceedings entries; a caption
claim contradicted by its own Setting column) and two info items (an empty
superscript group; placeholder `others` authors) are below.

## Structural Findings (fallow)

No `<structural_findings>` block was provided for this review.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `tab:comparison` caption asserts "only a trainable head" but its own Setting column lists heavier-than-head training for three rows

**File:** `paper/main.tex:388`
**Issue:** The caption states a universal property of every tabulated method:
"all listed methods use frozen features with only a trainable head." Three rows
in the same table contradict this in their `Setting` cells:
`PI-VAD ... Frozen I3D; +text, +5 train-time modalities`,
`DSANet ... Frozen CLIP; +text alignment`, and
`VadCLIP ... Frozen CLIP; +text alignment`. A learnable text-alignment branch
and five induced training-time modalities are trainable components beyond "only
a trainable head." The next sentence of the same caption even acknowledges this
("Methods with a text-alignment branch or extra training-time modalities operate
under a heavier budget"), so the table internally contradicts itself. This is an
intrinsic consistency defect (caption vs. its own column), not an external-number
question. Note the standalone fragment phrases the equivalent claim more
defensibly ("all listed methods use frozen features"), without the "only a
trainable head" universal.
**Fix:** Drop the over-broad universal from the first sentence so it no longer
conflicts with the Setting column, e.g.:
```latex
The \emph{Setting} column encodes the operating regime so rows are not read as a
bare head-to-head; all listed methods keep their backbone features frozen.
Methods with a text-alignment branch or extra training-time modalities operate
under a heavier budget than our frozen, no-text, visual+skeleton head.
```

### WR-02: Two new bib entries type unpublished arXiv preprints as `@inproceedings` with placeholder authors and no proceedings-level fields

**File:** `paper/references.bib:220-234`
**Issue:** `majhi2025pivad` and `yin2026dsanet` are entered as `@inproceedings`
with `booktitle = {... (CVPR)}` / `... (AAAI)` and `note = {arXiv:2505.13123}` /
`note = {arXiv:2511.10334}`. For an `@inproceedings`, BibTeX styles (incl. ACM
`acmart`) expect proceedings detail (`pages`, `publisher`, or at least a
year-correct proceedings); here the only locator is an arXiv id stuffed into
`note`, and `year = {2026}` (DSANet/AAAI 2026) is a future/forthcoming venue.
Combined with the `author = {... and others}` placeholder (see IN-02), these two
entries are the weakest in the file: BibTeX will not error, but the rendered
reference will read as an incomplete inproceedings (no page range, an "et al."
author list, and an arXiv id in a note field) rather than a clean preprint
citation. This is bib hygiene, not a compile blocker.
**Fix:** Either type them as preprints with an explicit eprint, e.g.:
```bibtex
@misc{majhi2025pivad,
  author       = {Snehashis Majhi and ...},
  title        = {Just Dance with $\pi$! {A} Poly-modal Inductor for
                  Weakly-Supervised Video Anomaly Detection},
  year         = {2025},
  eprint       = {2505.13123},
  archivePrefix= {arXiv},
  primaryClass = {cs.CV},
}
```
or, if keeping `@inproceedings`, add the real `pages`/`publisher` once the
proceedings are out and replace `note` with `eprint`/`archivePrefix` fields.

## Info

### IN-01: Empty superscript group on the LAVAD row

**File:** `paper/sota_comparison_full.tex:122`
**Issue:** The LAVAD row begins `LAVAD$^{}$` — an empty superscript math group.
Every other method either carries a real footnote letter (`$^{a}$`...`$^{n}$`)
or no superscript at all; this one has the markup with an empty argument. It
compiles clean and renders nothing visible, but it is a leftover/malformed marker
(likely a placeholder where a caveat letter was removed, given that LAVAD does
carry a `% RE-VERIFY` note on the same line about its 62.01 AP vs 85.36 AUC).
**Fix:** Remove the empty group, or assign LAVAD a real caveat letter and add the
matching note:
```latex
LAVAD                      & 2024 & CVPR'24           & 80.28 & 62.01 & ...
```

### IN-02: Placeholder `and others` author lists in two new bib entries

**File:** `paper/references.bib:221,229`
**Issue:** `majhi2025pivad` (`author = {Snehashis Majhi and others}`) and
`yin2026dsanet` (`author = {Yang Yin and others}`) use the BibTeX `and others`
placeholder, which renders as "et al." with no co-author names. The four other
new entries (`joo2023cliptsa`, `zhou2023urdmu`, `chen2023mgfn`,
`wang2024lightwvad`) list full author teams. Not a defect — BibTeX handles
`and others` correctly — but it is an incomplete-metadata smell worth filling in
before final submission.
**Fix:** Replace `and others` with the full author lists from the arXiv records
for both entries.

---

_Reviewed: 2026-06-21T06:52:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
