---
phase: 13-full-thesis-manuscript
plan: 01
subsystem: thesis-latex
tags: [latex, report-class, latexmk, miktex, bibtex, ieeetranN, natbib, gitignore]

# Dependency graph
requires: []
provides:
  - Compiling thesis/ LaTeX skeleton (report class 12pt/a4paper/oneside; 9 chapters + 6 appendices + frontmatter, \include chain)
  - Vendored thesis/IEEEtranN.bst (byte-identical to MiKTeX feupphdteses copy, v1.13 header; CRLF-protected via .gitattributes)
  - scripts/build_thesis.ps1 (non-interactive, -Open/-Clean, .bst hard-assert preflight, kpsewhich report, post-build log scan)
  - thesis/.latexmkrc (paper analog, --enable-installer)
  - thesis/references.bib superset (42 entries: 27 paper base + 11 SOTA + 4 survey; 15 GATE-13 markers)
  - .gitignore thesis-artifact block + results/* rewrite with self-documenting un-ignore rules (C7-3 discharged)
  - Permanent labels ch:01..ch:09, app:a..app:f, sec:disc, fig:architecture for cross-wave \ref resolution
affects: [13-02, 13-03, all wave-1 chapter writers, wave-2 appendix/frontmatter writers, 13-11 bib gate, 13-12, 13-VALIDATION build gate]

# Tech tracking
tech-stack:
  added: [lmodern (scalable Latin Modern fonts, T1 encoding)]
  patterns: [PLACEHOLDER-W0 marker convention for wave acceptance greps, "[build_thesis] prefix + exit-code log-scan discipline", vendored-.bst-wins-in-CWD bibliography resolution]

key-files:
  created:
    - thesis/main.tex
    - thesis/preamble.tex
    - thesis/frontmatter/{titlepage,abstract,acknowledgments,notation}.tex
    - thesis/chapters/ch01_introduction.tex ... ch09_conclusion.tex (9)
    - thesis/appendices/appA_rtfm.tex ... appF_figures.tex (6)
    - thesis/figures/fig_architecture.tex (verbatim paper copy)
    - thesis/IEEEtranN.bst (vendored)
    - thesis/.latexmkrc
    - thesis/references.bib
    - scripts/build_thesis.ps1
    - .gitattributes
  modified:
    - .gitignore

key-decisions:
  - "\\nocite{*} in main.tex as Wave-0 bib smoke test: forces all 42 entries through the vendored IEEEtranN.bst (bibtex errors with zero \\citation commands otherwise); Wave-3 removes it"
  - "lmodern + fontenc(T1) added to preamble: report-class bitmap CM fonts abort pdfTeX under microtype font expansion"
  - "Permanent sec:disc label planted in ch03 (verbatim fig_architecture.tex references it); Wave-1 writer moves it onto the disc_reweight section"
  - ".gitattributes -text pin on thesis/IEEEtranN.bst so core.autocrlf=true cannot break byte-identity on checkout"
  - "Staged bib entries where full author lists were unverifiable use surname-only author fields (song2025fdpn, leng2026piercingeye) rather than invented given names or 'and others' -- GATE-13 markers route them to the Wave-2 gate"

patterns-established:
  - "PLACEHOLDER-W0: literal token in every chapter/appendix/frontmatter placeholder (acknowledgments exempt); wave writers delete it; acceptance greps depend on it"
  - "Log-scan gate: build_thesis.ps1 exits nonzero on '!' lines, 'There were undefined references', 'Citation/Reference .* undefined' in thesis/main.log"
  - "GATE-13 marker: one trailing comment per staged bib entry; 13-11 verifies, 13-12 removes; zero survive to final"

requirements-completed: [SC1]

# Metrics
duration: 21min
completed: 2026-07-05
---

# Phase 13 Plan 01: Thesis LaTeX Skeleton + Build Tooling + Bib Superset Summary

**Complete thesis/ report-class skeleton (9 ch + 6 app + frontmatter) compiles clean end-to-end (28-page PDF, zero errors/undefined refs) through a new non-interactive build_thesis.ps1 with log-scan gate, vendored IEEEtranN.bst, and a 42-entry references.bib superset.**

## Performance

- **Duration:** ~21 min
- **Started:** 2026-07-04T20:08:41Z
- **Completed:** 2026-07-04T20:29:16Z
- **Tasks:** 3/3
- **Files modified:** 30 (28 created, 2 modified)

## Accomplishments

- thesis/ tree exactly per spec §3: `\documentclass[12pt,a4paper,oneside]{report}`, `\input{preamble}`, frontmatter chain (titlepage → abstract → acknowledgments → TOC/LOF/LOT → notation), 9 `\include{chapters/...}` + `\appendix` + 6 `\include{appendices/...}`, `\bibliographystyle{IEEEtranN}` + `\bibliography{references}`
- All 15 chapter/appendix placeholders carry the real spec-§4 titles, permanent labels (ch:01–ch:09, app:a–app:f), and the PLACEHOLDER-W0 token; titlepage carries the real facts (NTUST / Wei-Han Jeng / Chuan-Kai Yang); acknowledgments is the permanent user-fill exemption
- `thesis/IEEEtranN.bst` byte-identical to the MiKTeX feupphdteses copy (cmp exit 0; authentic Michael Shell v1.13 header), protected against autocrlf rewriting via `.gitattributes -text`
- TikZ architecture-figure smoke test wired into ch03 (`\resizebox{\textwidth}{!}{\input{figures/fig_architecture}}`) — rendered successfully at Wave 0 (RESEARCH A5 exercised; observation below)
- `scripts/build_thesis.ps1`: non-interactive default (Invoke-Item only inside `if ($Open)`), hard-asserts the vendored .bst, report-only kpsewhich preflight over 14 packages, NEW post-build main.log scan that fails the build on errors/undefined refs — the scan proved itself by catching the `sec:disc` undefined reference during execution
- `.gitignore`: thesis artifact block (incl. per-chapter `.aux` from `\include`, `.lof`, `.lot`) + `results/` → `results/*` rewrite with self-documenting `!` un-ignore rules and inline policy comment (C7-3 discharged); all 28 previously-tracked results files intact
- `thesis/references.bib`: 27 paper entries verbatim + `%% THESIS SOTA` block (11 staged entries) + `%% THESIS SURVEY` block (4 entries); 15 GATE-13 markers; the fabricated Light-WVAD XD 77.3 never copied (bib fields only, per Pitfall 4); no new `and others` (count stays at the 4 inherited base entries)
- First clean build: exit 0, log scan clean, 28-page PDF, BibTeX resolved `IEEEtranN.bst` from CWD (vendored copy), all 42 entries render in the bibliography (`\nocite{*}` smoke test), zero BibTeX warnings; pytest 322 passed; git status clean of build artifacts

## Task Commits

Each task was committed atomically:

1. **Task 1: thesis/ skeleton tree + vendored .bst + TikZ smoke test** - `fa9a666` (feat)
   - Deviation follow-up: `06acbbc` (fix) — .gitattributes CRLF guard for the vendored .bst
2. **Task 2: build_thesis.ps1 + thesis/.latexmkrc + .gitignore extensions** - `c44020f` (chore)
3. **Task 3: references.bib superset + first clean skeleton build** - `b30f509` (feat)

## Files Created/Modified

- `thesis/main.tex` — report-class root with full \include chain; `\nocite{*}` Wave-0 bib smoke test (Wave-3 removes)
- `thesis/preamble.tex` — RESEARCH §7 package order: geometry(2.5cm) → fontenc/lmodern → amsmath/amssymb → booktabs/multirow → graphicx → array → tikz(+4 libs) → setspace(\onehalfspacing) → caption/subcaption → microtype → natbib[numbers,sort&compress] → hyperref LAST (bookmarksnumbered,hidelinks)
- `thesis/frontmatter/*.tex` — titlepage (real facts), abstract/notation (W0 markers), acknowledgments (permanent user-fill, exempt)
- `thesis/chapters/ch0*.tex` (9) — real titles, permanent labels, W0 markers with pointed source/pitfall notes for Wave-1 writers; ch03 hosts fig:architecture smoke test + permanent sec:disc label
- `thesis/appendices/app*.tex` (6) — real titles, permanent labels, W0 markers
- `thesis/figures/fig_architecture.tex` — byte-identical copy of paper/figures/fig_architecture.tex
- `thesis/IEEEtranN.bst` — vendored, byte-identical (v1.13)
- `thesis/.latexmkrc` — paper analog verbatim, thesis header
- `thesis/references.bib` — 42-entry superset with GATE-13 markers
- `scripts/build_thesis.ps1` — non-interactive latexmk wrapper + preflight + log scan
- `.gitignore` — thesis artifacts + results/* un-ignore policy
- `.gitattributes` — `-text` pin for the vendored .bst

## Decisions Made

- **`\nocite{*}` as Wave-0 smoke test:** with zero `\cite` commands in placeholder chapters, BibTeX errors out ("found no \citation commands") and the build gate could not pass; `\nocite{*}` both unblocks the build and exercises every staged bib entry through the vendored .bst at Wave 0. Clearly commented in main.tex; Wave-3 integration removes it.
- **Surname-only staging for unverifiable author lists** (song2025fdpn, leng2026piercingeye): honest staging beats invented given names; GATE-13 markers guarantee the Wave-2 gate replaces them with primary-source full lists. All other staged entries carry full best-effort author lists for the gate to confirm.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] .gitattributes CRLF guard for vendored .bst**
- **Found during:** Task 1 (commit warning: "LF will be replaced by CRLF the next time Git touches it")
- **Issue:** core.autocrlf=true would rewrite the LF-ending IEEEtranN.bst to CRLF on any future checkout, silently breaking the byte-identical cmp assertion required by Task 1 acceptance and the 13-VALIDATION build gate
- **Fix:** `.gitattributes` with `thesis/IEEEtranN.bst -text` (stored blob verified byte-identical to the MiKTeX source via `git show HEAD:... | cmp`)
- **Files modified:** .gitattributes (new)
- **Verification:** stored blob cmp exit 0; working copy cmp exit 0
- **Committed in:** `06acbbc`

**2. [Rule 2 - Missing critical functionality] Per-chapter .aux ignore rules**
- **Found during:** Task 2 (.gitignore authoring)
- **Issue:** `\include` emits `.aux` files under `thesis/chapters/` and `thesis/appendices/`; the plan's specified pattern list (`thesis/*.aux`) only covers the top level — a build would leave 15 untracked artifacts, violating the "git status stays clean" must-have (the paper never used `\include`, so its block has no analog rule)
- **Fix:** added `thesis/chapters/*.aux` + `thesis/appendices/*.aux` to the thesis artifact block
- **Files modified:** .gitignore
- **Verification:** post-build `git status --porcelain` empty
- **Committed in:** `c44020f`

**3. [Rule 3 - Blocking issue] lmodern fonts for microtype font expansion**
- **Found during:** Task 3 (first clean build)
- **Issue:** fatal `pdfTeX error (font expansion): auto expansion is only possible with scalable fonts` — the report class at 12pt selects bitmap Computer Modern; microtype's font expansion aborts pdflatex (the paper's acmart loads its own scalable fonts, so RESEARCH §7 never hit this)
- **Fix:** `\usepackage[T1]{fontenc}` + `\usepackage{lmodern}` in the preamble fonts slot (before microtype, per "microtype after fonts"); lmodern added to the preflight report list
- **Files modified:** thesis/preamble.tex, scripts/build_thesis.ps1
- **Verification:** rebuild reached bibliography stage, then full clean pass
- **Committed in:** `b30f509`

**4. [Rule 3 - Blocking issue] Permanent sec:disc label for the verbatim architecture figure**
- **Found during:** Task 3 (log scan correctly failed the build)
- **Issue:** the byte-identical `fig_architecture.tex` contains `Sec.~\ref{sec:disc}` (lines 12/93) — the paper's disc_reweight section label, which no thesis file defined; the figure cannot be edited (verbatim-copy requirement), so the reference target must exist in the skeleton
- **Fix:** planted `\label{sec:disc}` in ch03_methodology.tex with a PERMANENT-label comment instructing the Wave-1 writer to MOVE it onto the disc_reweight section, never delete it
- **Files modified:** thesis/chapters/ch03_methodology.tex
- **Verification:** rebuild: log scan clean, zero undefined references
- **Committed in:** `b30f509`

## Preflight Package Report (final list)

All 14 packages resolved as preinstalled on this machine (report-only; MiKTeX installs on demand elsewhere): natbib, booktabs, multirow, graphicx, geometry, setspace, caption, subcaption, microtype, amsmath, amssymb, array, tikz (pgf), lmodern.

## Skeleton PDF + TikZ One-Column Observation (RESEARCH A5)

- **Page count:** 28 pages (titlepage, abstract, acknowledgments, TOC, LOF, LOT, notation, 9 chapters, 6 appendices, 8-page full bibliography via `\nocite{*}`)
- **A5 observation:** the ~8.5in-native swimlane TikZ figure rendered without errors under `\resizebox{\textwidth}{!}` at A4 one-column width (~16cm/6.3in usable) — roughly 74% of natural size versus ~82% in the paper's two-column `figure*` span, i.e. label text ~10% smaller than the paper rendering. Legible at Wave 0; the Ch 3 writer may still prefer `sidewaysfigure` (needs `rotating` in preamble + preflight list) if defense-print legibility matters.

## Known Stubs

All stubs below are **intentional by design** — this plan builds the Wave-0 skeleton; the plan's goal (clean-compiling skeleton + tooling + bib superset) is fully achieved.

| Stub | File(s) | Resolved by |
|------|---------|-------------|
| PLACEHOLDER-W0 chapter bodies (9) | thesis/chapters/ch0*.tex | Wave-1 chapter writers (13-04..13-09 per phase plan) |
| PLACEHOLDER-W0 appendix bodies (6) | thesis/appendices/app*.tex | Wave-2 appendix writers |
| PLACEHOLDER-W0 abstract/notation/titlepage finalization | thesis/frontmatter/*.tex | Wave-2 frontmatter writer |
| Acknowledgments user-fill text | thesis/frontmatter/acknowledgments.tex | User (permanent exemption, spec §11.2) |
| `\nocite{*}` full-bib smoke test | thesis/main.tex | Wave-3 integration (remove once chapters carry real \cite coverage) |
| GATE-13 staged bib fields (15 entries) | thesis/references.bib | 13-11 primary-source gate; 13-12 removes markers |

## Verification Results

- `build_thesis.ps1 -Clean`: exit 0; log scan clean (no `!` errors, no undefined refs/citations)
- BibTeX used the vendored style: `main.blg` reports `The style file: IEEEtranN.bst` resolved from CWD (thesis/); 42/42 entries in main.bbl; `warning$ -- 0`
- `git ls-files results/ | wc -l` = 28 (unchanged by the gitignore rewrite)
- pytest: 322 passed (baseline held)
- `git status --porcelain` after build: empty (no thesis artifacts leak)
- 15/15 PLACEHOLDER-W0 files; 15/15 permanent labels; cmp exit 0 for both the .bst and fig_architecture.tex

## Self-Check: PASSED

All created files exist on disk; all four task/deviation commits (fa9a666, 06acbbc, c44020f, b30f509) present in git log.
