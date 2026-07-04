# Phase 13: Full Thesis Manuscript - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning
**Source:** PRD Express Path (docs/superpowers/specs/2026-07-05-full-thesis-design.md — approved spec, 4 review rounds closed)

<domain>
## Phase Boundary

Produce the full-length master's thesis manuscript for ViolenceCC as a self-contained
LaTeX document in a new `thesis/` directory, expanding the 11-page CGW '26 workshop
paper (`paper/main.tex`, 457 lines) into a complete, oral-defense-ready document
(90-120 pages, 9 chapters + appendices A-F + frontmatter). Zero-GPU: writing, zero-GPU
figure regeneration from committed data, provenance tracking, and verification only.
`paper/` stays frozen; no headline numbers change.

</domain>

<decisions>
## Implementation Decisions

ALL decisions are locked in the spec (docs/superpowers/specs/2026-07-05-full-thesis-design.md).
The spec is the single source of truth; this file indexes it. Do not re-litigate.

### Format & layout (spec §2 D1-D2, §3)
- Clean generic `report`-class LaTeX (12pt, a4paper, oneside), no university template; English throughout; no Chinese abstract
- Layout: `thesis/main.tex` + `preamble.tex` + `frontmatter/` + `chapters/ch01..ch09.tex` + `appendices/appA..appF.tex` + `references.bib` + vendored `IEEEtranN.bst` + `PROVENANCE.md` + `figures/`
- Bibliography: BibTeX, vendored IEEEtranN.bst + natbib [numbers]
- `scripts/build_thesis.ps1`: non-interactive by default (NO Invoke-Item), -Open opt-in, -Clean flag; preflight HARD-asserts only vendored .bst, package resolution report-only (MiKTeX on-demand install proceeds via latexmk)
- Equations lifted verbatim from paper (code-verified); never alter the math

### Numbers (spec §2 D3, §7)
- FREEZE: canonical verified anchors only — UCF 82.5±0.4 AUC (Gated/Giant), XD 78.7±0.9 AP (Gated/SO400M); full anchor table in spec §7
- Forbidden sources: paper/tables_generated.tex; Phase 8/9/10/11 summary single-seed numbers; REQUIREMENTS.md EVAL rows (0.8227/71.92/0.9200 — sole exception: 0.8227/0.7192 as explicitly-labeled historical sweep baselines in sweep section/Appendix C); fabricated Light-WVAD XD 77.3; old phase6 C-series corruption heatmaps; Phase 4/4c-era per-category numbers
- Pri-5 aggregation traps: +4.83 (3-seed Gaussian family avg) ≠ +3.31 (s42-only) ≠ +8.95 (SO400M family) ≠ +13.2 (SO400M gaussian sev-5 3-seed) — keep distinct
- Honesty framings preserved: no SOTA claim, ~88-91% field ceiling, transductive TTA disclosure, "+13.2 single most-degraded condition", gains in "points" not "%", complementarity "small but consistent" (6/8 strictly positive + 2 ties, p≈0.03)

### Structure (spec §2 D6, §4)
- 9 chapters: Intro / Related Work / Methodology / Experimental Setup / Results: Fusion & Backbones / Results: Robustness & TTA / Discussion (+full SOTA) / Limitations & Future Work / Conclusion
- Appendices: A RTFM repro gap, B per-category + per-class complementarity, C sweep detail, D engineering notes, E reproducibility guide (discharges T6-2), F additional figures
- Full chapter-by-chapter content map with sources: spec §4 (binding)

### Provenance (spec §7a — binding)
- `thesis/PROVENANCE.md` manifest: every number family + figure/table → tracked source
- Every manifest source git-tracked in Wave 0 (gitignore `results/` → `results/*` rewrite with `!` rules, OR `git add -f`); assert via `git ls-files --error-unmatch`; number audit FAILS on untracked sources
- Figures: Class R (regenerable from tracked script + tracked data) or Class V (committed binary + verification note); local checkpoints/E: features disallowed as provenance

### SOTA verification gate (spec §2 D7, §7, §8 step 2b)
- In-phase primary-source verification of all 15 RE-VERIFY items + 17-item camera-ready checklist (incl. #16/#17 PI-VAD/DSANet bib status + full author lists): agents fetch primary papers, evidence report (quote+URL+verdict per item) saved under .planning/phases/13-*/; user spot-approves
- Unverifiable result cells OMITTED (---/N-A) + omission footnote — never shipped unverified; secondary-detail mismatches corrected in place
- Zero % RE-VERIFY comments and zero bib TODOs survive in thesis/

### Figures (spec §5)
- Reuse as-is: fig_architecture.tex (TikZ), 4 paper PDFs + fig_gating_distribution.pdf, pri9_score_hist.png
- Regenerate zero-GPU: Phase-7 sweep heatmaps (guard: generator hardcodes sweep-era baselines 0.8227/0.7192 lines 55-56 AND S03 3-seed baselines 70.98±1.08/81.98±0.29 with Delta columns — exclude deltas or label historical-configuration-only); corruption heatmaps from results/_tta_rerun_continual (old C-series forbidden); 20×4 severity heatmap from tracked Pri-5 CSV; per-category tables from canonical run dirs (post-λ0/post-h1)
- Phase-6 PNGs (A/B/D/E/F series): provenance-check each → include (Class V + note) / regenerate / drop

### Verification before done (spec §8, §11)
- build_thesis.ps1 -Clean: zero errors, zero undefined refs/citations (scan .log)
- Adversarial number audit via PROVENANCE.md (Phase-12 standard); headline-consistency; overclaim scan; structure check; pytest stays green

### Execution shape (spec §9)
- Wave 0: skeleton + preamble + vendored bst + build script + bib superset + provenance-source tracking + PROVENANCE.md scaffold + figure regeneration/provenance pass
- Wave 1: chapter drafting (parallel writers, seeded with guardrails + pointed sources)
- Wave 2: appendices + frontmatter; SOTA primary-source verification workflow in parallel
- Wave 3: integration, number audit, overclaim scan, RE-VERIFY resolution merge, final clean build
- User checkpoints: after Wave 0 (skeleton compiles), after Wave 1 (chapter drafts), SOTA evidence report spot-approval, final

### Claude's Discretion
- Exact prose style (match paper's voice; academic register), section-level organization within chapters, figure placement, notation table contents, per-chapter page budgets within the 90-120 total

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The spec (primary, binding)
- `docs/superpowers/specs/2026-07-05-full-thesis-design.md` — the approved design: layout, chapter map, figures plan, bib plan, number guardrails, provenance rules, verification gates, wave plan

### Base prose & thesis fragments
- `paper/main.tex` — CGW '26 paper (457 lines), canonical inlined tables 1-5, all equations, base prose for every chapter
- `paper/sota_comparison_full.tex` — purpose-built thesis SOTA fragment (FRAGMENT BODY BEGIN/END markers, lines 65/329); 20-method + fair-subset tables + P1-P5 paragraphs; manual [N] cites to rewire
- `paper/references.bib` — 27 verified entries (base for thesis superset)
- `paper/figures/` — fig_architecture.tex (TikZ) + 4 result PDFs + unused fig_gating_distribution.pdf
- `scripts/build_paper.ps1` — build-script analog (do NOT copy Invoke-Item at line 111)

### Result & analysis sources
- `results/results-index.csv` — 1,014-run master index (tracked)
- `results/_analysis_2026-06-10/` — Pri-5/6/7/9 thesis-designated analyses (needs tracking in Wave 0)
- `results/_tta_rerun_continual/summary_3seed.json` — TENT/SAR 3-seed null (tracked)
- `results/benchmark_models.csv`, `results/backbone_bench_combined.csv` — efficiency tables (needs tracking)
- `.planning/ANALYSIS-2026-06-10-zero-gpu.md` — Pri-5/6/7/9 numbers + precision traps
- `.planning/REVIEW-2026-06-10.md` — §5 Pri tracker (future-work items 2/3/4/8, MAYBE tier)
- `.planning/phases/12-sota-comparison-and-positioning/12-RESEARCH-sota.md` — verified SOTA research artifact (§8 = citation strings for ~11 missing bib entries)
- `.planning/phases/12-sota-comparison-and-positioning/12-VERIFICATION.md` — 17-item camera-ready re-verify checklist (input to verification gate)
- `.knowledge/tta-to-reweighting.html` — TTA→disc_reweight narrative source (Ch 6)
- `scripts/generate_phase7_charts.py` — sweep chart generator (historical-baseline guard applies)
- `scripts/generate_phase6_charts.py`, `scripts/generate_pub_figures.py` — figure generator analogs
- `data/ucf_total_frames.json` — UCF full-length eval manifest (reproducibility chapter)

### Phase history (narrative sources for negative results / engineering appendices)
- `.planning/phases/04b-*/04b-05-SUMMARY.md`, `.planning/phases/07-*/07-VERIFICATION.md` — RTFM repro gap (Appendix A)
- `.planning/phases/05-*/05-VERIFICATION.md` — UCF-Crime-C construction params (Ch 4)
- `.planning/STATE.md` — Key Decisions log (Appendix D engineering notes)

</canonical_refs>

<specifics>
## Specific Ideas

- Session context map (7-reader inventory of paper/planning/results/figures) available at
  `C:\Users\Austin\AppData\Local\Temp\claude\D--ViolenceCC\6fc43350-7d29-4e5d-afe5-5df8ec804c4c\scratchpad\ctxmap\`
  (paper-structure.md, thesis-fragments.md, planning-state.md, open-issues.md,
  results-figures.md, phase-findings.md, template-dir.md) — researcher should consolidate
  the durable parts into 13-RESEARCH.md since scratchpad is session-scoped
- Title-page facts: NTUST; author Wei-Han Jeng; advisor Chuan-Kai Yang
- Abstract: restructure from paper abstract (fixes review item T5-2 density)
- MiKTeX resolves IEEEtranN.bst only via unrelated feupphdteses package — hence vendoring

</specifics>

<deferred>
## Deferred Ideas

- Defense slide deck (separate later task)
- Chinese abstract / university-template re-skinning
- GPU tracks: Pri-2 (skeleton-head ensemble), Pri-3 (XD smoothing, headline-changing), Pri-4 (streaming w), Pri-8 (JPEG rescue), Pri-11 (temporal module), Pri-13 (text branch) — Future Work section only
- Optional XD total-frames manifest; video_auc recompute discrepancy (Pri-9 minor)

</deferred>

---

*Phase: 13-full-thesis-manuscript*
*Context gathered: 2026-07-05 via PRD Express Path*
