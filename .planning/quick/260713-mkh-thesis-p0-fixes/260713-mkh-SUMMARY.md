---
status: complete
phase: quick-260713-mkh
plan: 01
subsystem: thesis + paper (LaTeX manuscript)
tags: [thesis, ntust-format, erratum, bibliography, latex, cjk, verification]
requires: [thesis/main.pdf builds, results/ucf_gated_fusion_s42/eval_scores.npz, data/annotations/ucf_temporal.txt]
provides:
  - "Fighting047 temporal figure (thesis Fig 5.2 + paper Fig 2), positively aligned"
  - "45/45 cited bibliography with PYSKL authors fixed + 3 skeleton-VAD entries + CGW self-cite"
  - "NTUST-compliant thesis PDF (A4 3/2/3/3 cm, Times-family, centered 20pt chapters, R4 binding order, bilingual front matter)"
affects: [thesis/*, paper/main.tex, paper/references.bib, scripts/generate_pub_figures.py]
tech-stack:
  added: [newtxtext/newtxmath, CJKutf8 (bkai), titlesec]
  patterns: [resizebox table-shrink, allowbreak/emergencystretch path wrapping, PyMuPDF format gate]
key-files:
  created:
    - thesis/frontmatter/cover.tex
    - thesis/frontmatter/abstract_zh.tex
    - thesis/frontmatter/recommendation.tex
    - thesis/frontmatter/approval.tex
    - thesis/frontmatter/spine.txt
  modified:
    - scripts/generate_pub_figures.py
    - thesis/figures/fig_temporal_scores.pdf
    - paper/figures/fig_temporal_scores.pdf
    - thesis/preamble.tex
    - thesis/main.tex
    - thesis/references.bib
    - paper/references.bib
    - paper/main.tex
    - (thesis chapters ch01/ch02/ch04/ch05/ch06/ch07/ch08/ch09, appC/appD/appE, frontmatter titlepage/abstract, PROVENANCE.md)
decisions:
  - "Fighting047 pinned explicitly (gap +0.483) after the positive-alignment filter alone would have picked Stealing019 (weak localization)"
  - "doshi2022skeleton deleted (wrong paper for skeleton-VAD) and replaced by Morais/Markovitz/Hirschorn; net 42->45 bib keys"
  - "resizebox for the 5 overflowing tables; emergencystretch + scoped \\sloppy + \\allowbreak for prose/verbatim path overflow"
metrics:
  duration: ~90min
  completed: 2026-07-13
  commits: 3
  tasks: 3
---

# Quick Task 260713-mkh: Thesis P0 Fixes Summary

All P0 findings (C1–C6 content, S1–S4 NTUST format) from `.planning/THESIS-REVIEW-2026-07-11.md` closed in three atomic commits; the rebuilt thesis passes a 19/19 PyMuPDF compliance gate and both PDFs build clean with the headlines (UCF 82.5 / XD 78.7) untouched.

## Commits

| # | Hash | Scope |
|---|------|-------|
| 1 | `c3d70b1` | C1 — Figure 5.2 erratum swap (Fighting047), thesis + paper |
| 2 | `8063c56` | C2–C6 — bib corrections, skeleton-VAD literature, CGW self-cite, claim fixes |
| 3 | `2fc128f` | S1–S4 — NTUST format batch + table/verbatim overflow fixes |

## Task 1 — C1 figure erratum (commit c3d70b1)

- Patched `find_best_temporal_video()` with a hard positive-alignment filter (in-GT gated mean > out-GT mean) that rejects RoadAccidents127 (gap −0.742), and pinned **Fighting047** explicitly (in-GT 0.889 vs out-GT 0.407, **gap +0.483**, recomputed from `eval_scores.npz`). The filter alone would have selected Stealing019 (gap +0.153, high everywhere) — not a clean localization example — so the explicit pin matches the CGW-talk-validated video, exactly the plan's fallback path.
- Regenerated `fig_temporal_scores.pdf` (byte-identical thesis + paper copies, `cmp` exit 0), rewrote the thesis Fig 5.2 caption/§5.7 prose and paper Fig 2 caption/prose to describe what the curve shows (high inside the GT window, collapses below the visual stream in the later normal segment — honest "well-localized example, not representative").
- Updated `PROVENANCE.md` row 90. `appF_figures.tex:80-81` needed no change (it never named the old video/category).

## Task 2 — C2–C6 content (commit 8063c56)

- **C2:** fixed PYSKL authors → Duan/Wang/Chen/Lin (thesis **and** paper bib); deleted `doshi2022skeleton` (an any-shot-AD paper, not skeleton-VAD) and added `morais2019skeleton`, `markovitz2020gepc`, `hirschorn2023stgnf`; rewrote the ch01 motivation/Gap-1 sentences and the ch02 skeleton-VAD paragraph (reconstruction → clustering → normalizing flows; explicit unsupervised-single-modality vs this thesis's weakly-supervised-fusion contrast). Cite coverage recomputed **45/45**; `main.tex` comment updated 42→45.
- **C3:** added `jeng2026dualmodal` + a four-item thesis-delta list at ch01:171; fixed the ch05:239 "disclosed in the paper" dangler to cite it.
- **C4:** (1) gated-beats-late on **all 8/8 cells** with the verified margins (ch05 + paper mirror; UCF +2.5/+1.8/+2.2/+2.6, XD +12.6/+10.9/+13.0/+11.1 — all re-derived from Tables 5.1/5.2); (2) canonical label "the condition that most collapses the visual-language stream" in ch01/ch06/ch09/abstract + PROVENANCE row 12; (3) non-monotone Fig 6.1 caption; (4) moved 75.41% from the ch08 XD-AP sentence to the UCF sentence; (5) appC reworded (XD exact 0.7192, UCF within 0.02 pp 82.26 vs historical 82.27 — 82.26 confirmed by inspecting the figure's P4-baseline cell).
- **C5:** added a "Score Calibration and Fixed-Threshold Deployment" section to ch08 (p75 ≈ 0.986, fixed-threshold false alarms, calibration/threshold-free future work), cross-referencing §5.8 (`sec:failure`); sharpened the ch05 forward promise to point at it.
- **C6:** reframed ch07 into recovery-vs-extraction triangulation (63.9→74.6 recovery = 10.7 of 12.6 pts by suppression; extraction evidence = +1.9 margin, 8/8 sign test §5.3, category-structured gates) — no single number called "strongest".

## Task 3 — S1–S4 NTUST format (commit 2fc128f)

- **S3 preamble:** geometry A4 `top=3,bottom=2,left=3,right=3 cm`; `newtxtext`+`newtxmath` (dropped `amssymb`); `CJKutf8` (bkai); `titlesec` centered-bold-20pt chapters (30pt post-gap), 18pt sections; `\pagenumbering{Roman}`; `\emergencystretch=3em`.
- **S1/S2 reorder:** main.tex frontmatter now cover → title → 推薦書 → 審定書 → (Roman) → 中文摘要 → 英文摘要 → 誌謝 → 目錄 → 符號索引 → 圖目錄 → 表目錄; References moved **before** `\appendix` with `\phantomsection`+`\addcontentsline` (titled "References"). Appendix `\cite` keys still resolve (0 `??`).
- **S1 new files:** `cover.tex` (bilingual, renders correctly), `abstract_zh.tex` (exact locked text, 6 keywords), `recommendation.tex`, `approval.tex` placeholders, `spine.txt` (not compiled). English Keywords line appended to `abstract.tex`.
- **S4 title page:** 24pt bold title, department line, "Master of Science in Computer Science and Information Engineering", June 2026.
- **Overflow:** `\resizebox` on Tables 4.1, 4.2, 5.1, 5.2, D.1; re-broke appE verbatim commands (train.py/evaluate.py/comments), scoped `\sloppy` on the Repository-Map description, and `\allowbreak` on long `\texttt` paths (ch04 + appE). The old clipped run-on paths are gone.

## Verification gate — 19/19 PASS (measured)

| Item | Measured |
|------|----------|
| Page size | A4 595.3 × 841.9 pt |
| Margins | left text x0 = 82.2 pt (target 85.0, within ±0.15 cm+2 tol), top y0 = 85.3 pt |
| Body font | TeXGyreTermes (Times-family), **not** LMRoman |
| Chapter headings | 9 headings, size 19.9 pt, centered at 297.6 (page center 297.64) |
| Section headings | 17.9 pt |
| Title / cover | largest span 23.9 pt (~24) |
| Front-matter numbering | UPPERCASE Roman I, II, III… (0 lowercase); body arabic restarts at 1 |
| Binding order | Chinese abstract (pdf p5) precedes English (p6); References (p97) precede Appendix A (p102) |
| Overflow | **0 real-overflow lines >4 pt** (119 residual spans at 2–4 pt = intentional microtype punctuation/hyphen protrusion) |
| Figure 5.2 | Fighting047 present, RoadAccidents127 absent |
| Citations | 0 `??`, 0 `[?]`; cite coverage 45/45 |
| Builds | thesis 131 pp exit 0; paper 11 pp exit 0 (last edited/rebuilt in Task 2) |

Only build warning: `C70/bkai/b/n undefined` (bkai has no bold weight) — expected and accepted per CONTEXT; CJK renders correctly (visually confirmed on cover + 摘要 pages).

## Deviations from plan

- **[Rule 3 — blocking] Fighting047 pinned, not filter-selected.** The positive-alignment filter alone selects Stealing019 (gap +0.153, high everywhere). Per the plan's explicit fallback ("otherwise parameterize … and pass Fighting047"), the function now takes an explicit id and the figure pins Fighting047. Both mechanisms are in the code.
- **[Rule 2 — completeness] Relabeled all "single most-degraded"/"most visually-degrading" occurrences** (abstract, ch01, ch06, ch09, PROVENANCE), not only the ch06/ch09 lines CONTEXT enumerated, to satisfy the grep gate and keep one canonical label. The paper's abstract/conclusion labels were left as-is per CONTEXT scope (review §8: paper mirror = C1 + the "lone exception" sentence only).
- Table 4.3 (`tab:efficiency-backbones`) did **not** overflow at the new margins, so it was left unwrapped (only the genuinely overflowing tables were touched, per surgical-change discipline).

## Remaining TODO-CONFIRM placeholders (deliberately unresolved — for Austin)

- Chinese title wording (`cover.tex`, `spine.txt`)
- Chinese given name of Wei-Han Jeng — the `鄭○○` placeholder MUST be replaced before printing (`cover.tex`, `spine.txt`)
- Advisor Chinese name confirmation (`cover.tex`)
- Graduation month (June printed; July/Aug leavers print June per NTUST) (`cover.tex`, `titlepage.tex`)
- zh-TW abstract wording review (`abstract_zh.tex`)
- Pre-existing user-fill: `acknowledgments.tex` is still the author placeholder (permanent, exempt per its own note); `recommendation.tex`/`approval.tex` are placeholder pages to be replaced by the signed forms.

## Self-Check: PASSED

- Files created exist: cover.tex, abstract_zh.tex, recommendation.tex, approval.tex, spine.txt (all in `thesis/frontmatter/`) — confirmed via git commit `2fc128f` (create mode 100644 x5).
- Commits exist: `c3d70b1`, `8063c56`, `2fc128f` on main (git log verified).
- No build artifacts committed (only source-tracked `figures/fig_temporal_scores.pdf` x2).
