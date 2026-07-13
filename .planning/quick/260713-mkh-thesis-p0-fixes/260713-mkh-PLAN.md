---
phase: quick-260713-mkh
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/generate_pub_figures.py
  - thesis/figures/fig_temporal_scores.pdf
  - paper/figures/fig_temporal_scores.pdf
  - thesis/chapters/ch01_introduction.tex
  - thesis/chapters/ch02_related_work.tex
  - thesis/chapters/ch04_experimental_setup.tex
  - thesis/chapters/ch05_results_fusion.tex
  - thesis/chapters/ch06_results_tta.tex
  - thesis/chapters/ch07_discussion.tex
  - thesis/chapters/ch08_limitations.tex
  - thesis/chapters/ch09_conclusion.tex
  - thesis/appendices/appC_sweep.tex
  - thesis/appendices/appD_engineering.tex
  - thesis/appendices/appE_reproducibility.tex
  - thesis/appendices/appF_figures.tex
  - thesis/references.bib
  - thesis/main.tex
  - thesis/preamble.tex
  - thesis/PROVENANCE.md
  - thesis/frontmatter/titlepage.tex
  - thesis/frontmatter/abstract.tex
  - thesis/frontmatter/cover.tex
  - thesis/frontmatter/spine.txt
  - thesis/frontmatter/recommendation.tex
  - thesis/frontmatter/approval.tex
  - thesis/frontmatter/abstract_zh.tex
  - paper/main.tex
  - paper/references.bib
autonomous: true
requirements: [C1, C2, C3, C4, C5, C6, S1, S2, S3, S4]   # finding IDs from .planning/THESIS-REVIEW-2026-07-11.md (quick task; no ROADMAP req IDs)
must_haves:
  truths:
    - "Thesis Figure 5.2 and paper Figure 2 show a video whose gated curve is HIGH inside the shaded GT window; caption/prose name that video (expected Fighting047), not RoadAccidents127"
    - "references.bib has correct PYSKL authors, three skeleton-VAD entries (morais/markovitz/hirschorn), and jeng2026dualmodal; ch01 states the thesis-over-paper delta; cite coverage is N/N"
    - "The five C4 claims read per the corrected wording; ch08 contains the score-calibration limitation resolving ch05:566; ch07 presents triangulated evidence, not 'strongest single piece'"
    - "Rebuilt thesis PDF passes NTUST checks: A4, 3/2/3/3 cm margins, Times-family body font, centered 20pt chapters, 18pt sections, UPPERCASE Roman front-matter numbers, bilingual front matter in R4 order, References before Appendix A, 24pt title"
    - "No text/table span crosses the right margin on any page; both PDFs rebuild clean with zero ?? citations"
  artifacts:
    - path: "thesis/figures/fig_temporal_scores.pdf"
      provides: "Regenerated temporal-score figure (same bytes copied to paper/figures/)"
    - path: "thesis/frontmatter/abstract_zh.tex"
      provides: "Chinese abstract + 6 keywords (CJK bkai), exact text from CONTEXT.md"
    - path: "thesis/frontmatter/cover.tex"
      provides: "Bilingual NTUST cover page (附錄一)"
    - path: "thesis/frontmatter/recommendation.tex"
      provides: "指導教授推薦書 placeholder page"
    - path: "thesis/frontmatter/approval.tex"
      provides: "學位考試委員審定書 placeholder page"
    - path: "thesis/frontmatter/spine.txt"
      provides: "Print-shop spine (書背) text, not compiled"
    - path: "thesis/preamble.tex"
      provides: "geometry 3/2/3/3, newtxtext+newtxmath, CJKutf8, titlesec heading formats"
  key_links:
    - from: "thesis/main.tex"
      to: "frontmatter/cover|recommendation|approval|abstract_zh"
      via: "\\input in NTUST R4 order with \\pagenumbering{Roman} before abstract_zh"
    - from: "thesis/main.tex"
      to: "references.bib"
      via: "\\bibliography moved BEFORE \\appendix with \\addcontentsline TOC entry, \\bibname=References"
    - from: "thesis/chapters/ch08_limitations.tex"
      to: "ch05 §5.8"
      via: "calibration limitation cross-ref resolving the ch05:566 forward promise"
---

<objective>
Execute the P0 fixes from `.planning/THESIS-REVIEW-2026-07-11.md`: content blockers C1–C6 (including paper mirrors for C1/C4a) and the NTUST format batch S1–S4 (plus the mandatory table/verbatim overflow fixes at the new 15 cm text width), then rebuild both PDFs and re-verify compliance with PyMuPDF.

Purpose: thesis is currently NOT submission-ready (format) and NOT oral-ready (Figure 5.2 erratum, stale claims). These are the blockers a committee catches in minutes.
Output: 3 atomic commits on main; compliant `thesis/main.pdf` and updated `paper/main.pdf` (both git-ignored, never committed).
</objective>

<execution_notes>
- **MAIN TREE, no worktree.** Figure regeneration needs untracked data (`results/ucf_gated_fusion_s42/eval_scores.npz`, `data/annotations/ucf_temporal.txt`). Execute sequentially, one atomic commit per task.
- **Every implementation decision is already LOCKED** in `.planning/quick/260713-mkh-thesis-p0-fixes/260713-mkh-CONTEXT.md`. Read it in full before Task 1, plus the review report §2/§3 for per-finding evidence. Do not re-decide; only prose phrasing, table-shrink technique, and minor LaTeX plumbing are discretionary (CONTEXT "Claude's Discretion").
- Builds: `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean` and `.\scripts\build_paper.ps1 -Clean`. Rebuild the paper in ANY task that edits paper LaTeX (CLAUDE.md rule). Never commit build artifacts (main.pdf/.aux/.bbl/… in paper/ AND thesis/). Figure PDFs under `paper/figures/` and `thesis/figures/` ARE tracked sources — commit those.
- PyMuPDF (fitz) scripts: write throwaway scan scripts to the session scratchpad, not the repo.
</execution_notes>

<context>
@.planning/quick/260713-mkh-thesis-p0-fixes/260713-mkh-CONTEXT.md   (LOCKED decisions — the authoritative spec)
@.planning/THESIS-REVIEW-2026-07-11.md                              (findings §2 S1–S4, §3 C1–C6 with evidence)
@CLAUDE.md                                                          (paper build rule)
@thesis/main.tex
@thesis/preamble.tex
</context>

<tasks>

<task type="auto">
  <name>Task 1: C1 — replace Figure 5.2 erratum video (thesis + paper)</name>
  <files>scripts/generate_pub_figures.py, thesis/figures/fig_temporal_scores.pdf, paper/figures/fig_temporal_scores.pdf, thesis/chapters/ch05_results_fusion.tex, paper/main.tex, thesis/PROVENANCE.md, thesis/appendices/appF_figures.tex</files>
  <action>
    Per CONTEXT §C1:
    1. Patch `scripts/generate_pub_figures.py::find_best_temporal_video()` — add a hard filter requiring in-GT mean score > out-GT mean score (positive alignment gap) before its existing scoring. Expected selection: Fighting047 (gap +0.48, validated in quick 260707-n9l). If a different video is selected, accept only if its gap is positive AND the rendered curve is visually sensible; otherwise parameterize the function to take an explicit video id and pass Fighting047.
    2. Regenerate `fig_temporal_scores.pdf`; place the SAME file at both `thesis/figures/` and `paper/figures/`.
    3. Render the new figure and LOOK at it before writing prose. Rewrite thesis caption at `ch05_results_fusion.tex:386-392` and §5.7 prose at `:396-402` to describe what the curve actually shows. Do NOT call it "representative" — Fighting is a strong category; frame as a well-localized example.
    4. Mirror in `paper/main.tex`: Figure 2 caption + its referencing prose (this is the open paper erratum from memory/STATE).
    5. Update `thesis/PROVENANCE.md:90` figure row: new video id, generation command, date.
    6. Check `thesis/appendices/appF_figures.tex:80-81` ("Chapter 5 shows one temporal score curve; Figures F.2 and F.3 add three more") — adjust only if it names the old video/category.
    7. Rebuild BOTH PDFs (`build_thesis.ps1 -Clean`, `build_paper.ps1 -Clean`).
    Commit (figure PDFs + script + TeX + PROVENANCE only, no build artifacts):
    `fix(quick-260713-mkh): C1 — replace Figure 5.2 erratum video with Fighting047 (thesis+paper)`
  </action>
  <verify>
    <automated>PyMuPDF scratch script: render the thesis Figure 5.2 page to PNG and assert the caption text names the new video and does not contain "RoadAccidents127"; recompute in-GT-minus-out-GT gap for the selected video from results/ucf_gated_fusion_s42/eval_scores.npz + data/annotations/ucf_temporal.txt and assert gap > 0. Grep both thesis/ and paper/ TeX for "RoadAccidents127" → 0 hits in figure caption/prose contexts.</automated>
  </verify>
  <done>Both figure PDFs are byte-identical regenerations showing a positively-aligned video; thesis + paper captions/prose match the rendered curve; PROVENANCE row updated; appF cross-ref reads correctly; both builds exit 0; commit 1 made.</done>
</task>

<task type="auto">
  <name>Task 2: C2–C6 — bib corrections, skeleton-VAD literature, CGW self-cite, claim fixes</name>
  <files>thesis/references.bib, paper/references.bib, thesis/main.tex, thesis/chapters/ch01_introduction.tex, thesis/chapters/ch02_related_work.tex, thesis/chapters/ch05_results_fusion.tex, thesis/chapters/ch06_results_tta.tex, thesis/chapters/ch07_discussion.tex, thesis/chapters/ch08_limitations.tex, thesis/chapters/ch09_conclusion.tex, thesis/appendices/appC_sweep.tex, paper/main.tex, thesis/PROVENANCE.md</files>
  <action>
    Apply CONTEXT §C2–§C6 exactly (semantic content is locked; phrasing is discretionary):
    - **C2**: Fix PYSKL authors at `thesis/references.bib:122` (Duan/Wang/Chen/Lin); grep `paper/references.bib` for the same corruption and fix if present. Add three bib entries to thesis only: `morais2019skeleton` (CVPR 2019), `markovitz2020gepc` (CVPR 2020), `hirschorn2023stgnf` (ICCV 2023) — full fields in CONTEXT. Rewrite skeleton-VAD prose: `ch01_introduction.tex:56-57` + Gap 1 sentence (~:115), and `ch02_related_work.tex:219-230` (pose-trajectory line: reconstruction/regularity → clustering → normalizing flows; contrast with this thesis's weakly-supervised fusion use). Then resolve `doshi2022skeleton`: DELETE the entry if no longer cited (and update the coverage comment at `thesis/main.tex:52-53` from 42); otherwise fix it per CONTEXT (CVPRW 2020, drop wrong DOI, arXiv note, describe as any-shot sequential AD).
    - **C3**: Add `jeng2026dualmodal` bib entry (CGW 2026, fields in CONTEXT). At `ch01_introduction.tex:171` cite it + append 2–3 sentences enumerating the four thesis-only deltas (a)–(d) from CONTEXT. Fix the dangling "disclosed in the paper" at `ch05_results_fusion.tex:239` to cite the entry.
    - **C4** (five corrections, exact targets in CONTEXT §C4): (1) `ch05:98-101` "lone exception" → gated beats late on every backbone/both datasets with the listed deltas; mirror the identical sentence in `paper/main.tex` (grep "lone exception"); sanity-check `ch07_discussion.tex:97-` stays consistent. (2) `ch06:329` + Fig 6.3 caption `:303-304` + `ch09_conclusion.tex` → canonical qualifier "the condition that most collapses the visual-language stream"; update PROVENANCE canonical-label row if one exists. (3) `ch06:41-42` Fig 6.1 caption → "generally deepens … exceptions analyzed in §6.4.2". (4) `ch08:47` delete "(75.41\%)" from the XD-AP sentence. (5) `appC_sweep.tex:44-48, :62, :97-98` → XD exact (0.7192), UCF within 0.02 pp (82.26 vs 82.27); Fig C.1 caption 82.26; Table C.1 caption labels 0.8227 as historical.
    - **C5**: Add the score-calibration limitation to `ch08_limitations.tex` (after §8.1 or own §): rank metrics mask right-skewed normal scores (p75 ≈ 0.986, §5.8), fixed-threshold deployment ⇒ sustained false alarms, calibration/threshold-free policies as future work; cross-ref §5.8 so `ch05:566`'s promise resolves. No new numbers.
    - **C6**: Rewrite `ch07_discussion.tex:35-44` per CONTEXT's triangulation logic (suppression recovers 63.9→74.6; extraction evidence = +1.9 gated-vs-visual margin, 8/8 sign test §5.3, category-structured gates). No single number called "the strongest evidence".
    - Re-verify cite coverage: grep all \cite keys across thesis TeX vs bib keys, update the N/N comment at `thesis/main.tex:52-53`.
    - Rebuild thesis AND paper (paper/main.tex edited → `build_paper.ps1 -Clean` per CLAUDE.md).
    Commit: `fix(quick-260713-mkh): C2-C6 — bib corrections, skeleton-VAD literature, CGW self-cite, claim fixes`
  </action>
  <verify>
    <automated>Grep gates: "lone exception" → 0 hits in thesis/ and paper/ TeX; "single most-degraded" and "most visually-degrading" → 0 hits; "deepens monotonically" → 0 hits; "75.41" absent from ch08's XD sentence (still present in the UCF sentence); "strongest single piece" → 0 hits in ch07. Cite-coverage scratch script reports N/N (all \cite keys ∈ bib, all bib keys cited). Both builds exit 0; PDF text contains no "??" / "[?]" citations.</automated>
  </verify>
  <done>All C2–C6 targets edited per CONTEXT; jeng2026dualmodal + three skeleton-VAD entries resolve in the PDF; doshi entry deleted-or-fixed with main.tex comment matching the new count; paper mirror applied; both builds green; commit 2 made.</done>
</task>

<task type="auto">
  <name>Task 3: S1–S4 NTUST format batch + full verification gate</name>
  <files>thesis/preamble.tex, thesis/main.tex, thesis/frontmatter/titlepage.tex, thesis/frontmatter/abstract.tex, thesis/frontmatter/cover.tex, thesis/frontmatter/spine.txt, thesis/frontmatter/recommendation.tex, thesis/frontmatter/approval.tex, thesis/frontmatter/abstract_zh.tex, thesis/chapters/ch04_experimental_setup.tex, thesis/chapters/ch05_results_fusion.tex, thesis/appendices/appD_engineering.tex, thesis/appendices/appE_reproducibility.tex</files>
  <action>
    Apply CONTEXT §S3, §S1/S2, and the overflow section exactly:
    - **preamble.tex** (currently `margin=2.5cm` at :7, `lmodern` at :13, `amssymb` at :17): geometry → `top=3cm,bottom=2cm,left=3cm,right=3cm`; fonts → `newtxtext`+`newtxmath` (REMOVE amssymb; amsmath BEFORE newtxmath; keep fontenc T1 + microtype; fallback `mathptmx`+amssymb only if newtx errors in the build log); add `\usepackage{CJKutf8}` (bkai; fallback bsmi if font maps fail); add titlesec with the exact `\titleformat`/`\titlespacing` lines from CONTEXT (chapters centered bold 20pt with 30pt post-gap; sections left bold 18pt; subsections default).
    - **main.tex reorder**: frontmatter becomes cover → titlepage → recommendation → approval → `\pagenumbering{Roman}` → abstract_zh → abstract → acknowledgments → `\tableofcontents` → notation → `\listoffigures` → `\listoftables` → body (cover through approval unnumbered via `\thispagestyle{empty}`/titlepage env; replace `\pagenumbering{roman}` at :15). Backmatter: move bibliography (currently :55-56, AFTER appendices at :42) to BEFORE `\appendix`, using the exact block from CONTEXT (`\clearpage` + `\phantomsection` + `\renewcommand{\bibname}{References}` + `\addcontentsline` + style/bibliography), then `\appendix` + the six `\include`s. Confirm appendix \cite keys still resolve.
    - **New frontmatter files** (contents specified verbatim in CONTEXT §S1/S2 items 1–5, including the exact zh abstract body text, the 6 Chinese keywords, and all `% TODO-CONFIRM (Austin)` placeholders — copy them faithfully): `cover.tex`, `spine.txt` (not compiled — do NOT \input it), `recommendation.tex`, `approval.tex`, `abstract_zh.tex`.
    - **abstract.tex**: append the English Keywords line from CONTEXT item 6 (6 keywords matching the Chinese set).
    - **titlepage.tex**: title at `\fontsize{24}{29}\selectfont\bfseries`; add department line; degree → "Master of Science in Computer Science and Information Engineering"; date → "June 2026".
    - **Overflow fixes at the new 15 cm text width**: Tables 4.1, 4.2 (ch04), 5.1, 5.2 (ch05), D.1 (appD) — try `\small`/`\footnotesize` + `\setlength{\tabcolsep}{3.5pt}` first, `\resizebox{\textwidth}{!}{...}` if still overwide; keep booktabs. `appE_reproducibility.tex:104-106` + any other overflowing verbatim/texttt lines found in the post-build scan: manually re-break long paths/commands (the clipped-semicolon run-on on old p.114 must be gone).
    - Hyperref/CJK bookmark warnings: `\texorpdfstring` or accept warnings — never let bookmarks break the build.
    - **Run the full verification gate from CONTEXT before committing** (all six items — see <verify>).
    Commit: `feat(quick-260713-mkh): NTUST format compliance batch (S1-S4)`
  </action>
  <verify>
    <automated>CONTEXT verification gate, all six items: (1) `build_thesis.ps1 -Clean` exits 0, main.log free of missing-font/package errors, no "??"/"[?]" citations in PDF text. (2) PyMuPDF scratch script asserts: A4 pages; text-block margins ≈ 3/2/3/3 cm ±0.15 (footer number may sit in the bottom 2 cm band); body font family Times/Termes/NimbusRoman (not LMRoman); every "Chapter N" heading bbox centered within ±10 pt of page center at span ≈20 pt; sections ≈18 pt; front-matter footers show I, II, III (uppercase); Chinese abstract page precedes English abstract; References section starts before Appendix A; title-page title span ≈24 pt. (3) Overflow scan: no span with x1 > right-margin boundary +2 pt on any page. (4) Figure 5.2 page render still shows the Task-1 curve/caption. (5) `build_paper.ps1 -Clean` exits 0. (6) Cite coverage N/N re-verified, main.tex comment current.</automated>
  </verify>
  <done>All six gate items pass; thesis PDF is NTUST-compliant per the §1 matrix rows R1–R8; new frontmatter files exist with TODO-CONFIRM markers intact; spine.txt present but not compiled; no table/verbatim overflow anywhere; commit 3 made (sources only, no build artifacts).</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| (none) | Local LaTeX/docs edits + local figure regeneration from tracked script and local data; no untrusted input, no network services |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-q260713-01 | Tampering | MiKTeX auto-install of CTAN packages (newtx, CJKutf8, titlesec) during build | accept | Standard MiKTeX package sourcing; no npm/pip/cargo installs in scope |
</threat_model>

<coverage_audit>
| Source | Item | Covered by |
|--------|------|-----------|
| CONTEXT | C1 figure swap (script, PDFs, captions, PROVENANCE, appF) | Task 1 |
| CONTEXT | C2 bib fixes + 3 entries + prose rewrite + doshi resolution + cite count | Task 2 |
| CONTEXT | C3 self-cite + delta + ch05:239 | Task 2 |
| CONTEXT | C4 five claim fixes incl. paper mirror | Task 2 |
| CONTEXT | C5 ch08 calibration paragraph | Task 2 |
| CONTEXT | C6 ch07 reframe | Task 2 |
| CONTEXT | S3 geometry/font/CJK/titlesec/Roman/titlepage | Task 3 |
| CONTEXT | S1/S2 frontmatter files + ordering + References-before-appendix | Task 3 |
| CONTEXT | Table/verbatim overflow fixes | Task 3 |
| CONTEXT | Verification gate (6 items) | Task 3 verify |
| CONTEXT | Commit plan items 1–3 | Tasks 1–3 (item 4, docs commit, is the orchestrator's) |
| CONTEXT | Deferred/out-of-scope: MEDIUM/LOW findings, D1–D4 defense prep | Excluded per domain boundary |
</coverage_audit>

<verification>
- Three atomic commits on main matching the CONTEXT commit plan, in order C1 → C2-C6 → S1-S4.
- `git status` shows no committed build artifacts under thesis/ or paper/.
- The six-item verification gate (Task 3) all green — this is the plan-level acceptance test.
</verification>

<success_criteria>
- Every P0 finding (C1–C6, S1–S4) from THESIS-REVIEW-2026-07-11.md §2/§3 is closed, including paper mirrors for C1 and C4a.
- Rebuilt thesis passes the PyMuPDF compliance scan (margins, fonts, headings, numbering, ordering, overflows).
- Headlines 82.5 UCF / 78.7 XD untouched; no numbers changed anywhere except the C4/appC corrections specified in CONTEXT.
- TODO-CONFIRM placeholders for Austin (Chinese title wording, Chinese given name, advisor name, graduation month, zh abstract review) present in the new frontmatter — these are deliberately NOT resolved by the executor.
</success_criteria>

<output>
Create `.planning/quick/260713-mkh-thesis-p0-fixes/260713-mkh-SUMMARY.md` when done (orchestrator commits docs; no ROADMAP/STATE changes by the executor).
</output>
