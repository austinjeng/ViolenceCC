# Phase 11: Thesis Manuscript - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Write a complete CGW '26 workshop paper (8-10 pages, ACM sigconf format, English) presenting the full ViolenceCC pipeline — dual-modal skeleton-visual fusion framework, four-backbone visual comparison (CLIP ViT-B/16, SigLIP2 ViT-B/16, SigLIP2 SO400M, SigLIP2 Giant-opt), and TTA robustness experiments. This is a workshop paper first; the full master's thesis will be expanded later as a separate effort.

**Includes:** Running TTA experiments on all backbone variants (new experiments), writing the paper, building BibTeX library, creating architecture diagram, generating publication-quality figures.

**Excludes:** Presentation slides (separate phase), full thesis expansion, new model architectures or experiments beyond TTA.

</domain>

<decisions>
## Implementation Decisions

### Narrative Framing
- **D-01:** Central contribution is the full pipeline study — fusion framework + backbone comparison + TTA investigation together tell a cohesive story about practical weakly-supervised VAD.
- **D-02:** Method-focused title direction (e.g., "Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection").
- **D-03:** Skeleton positioned as a core modality, not a supplementary signal — the fusion IS the contribution.
- **D-04:** MIL ranking loss is the training recipe (adopted from Sultani/RTFM), not a methodological contribution. Explained in background, not presented as novel.
- **D-05:** VadCLIP (AAAI 2024, 88.02% AUC on UCF-Crime) cited for context in related work only — not a direct comparison baseline. VadCLIP is single-modal CLIP; our contribution is the dual-modal fusion + backbone comparison, not SOTA chasing.
- **D-06:** No external baseline comparison table. The paper is self-contained — compare our own variants (skeleton-only, CLIP-only, late fusion, gated fusion) against each other across backbones.
- **D-07:** TTA experiments will run on ALL backbone variants (CLIP, SigLIP2 ViT-B/16, SO400M, Giant-opt) with TENT and SAR on LayerNorm. TTA runs are part of Phase 11 deliverables.
- **D-08:** Target audience is CGW workshop attendees (computer graphics/multimedia) — needs more VAD background than a pure surveillance venue.
- **D-09:** Include 2-3 key qualitative visuals (temporal scores, skeleton overlay, gating analysis) to complement quantitative tables.
- **D-10:** No supervisor guidance on paper angle yet — draft will be presented for iteration.

### Paper Structure
- **D-11:** 8-10 pages, ACM sigconf format (`\documentclass[sigconf]{acmart}`), English, single-blind review.
- **D-12:** Experiments-heavy allocation: ~1p intro, ~1p related work, ~1.5p methodology, ~4p experiments/results, ~0.5p conclusion + separate Limitations section.
- **D-13:** Detailed per-component methodology subsections (skeleton extraction/RTMPose, CTR-GCN feature extraction, CLIP/SigLIP2 visual feature extraction, fusion mechanisms, MIL training).
- **D-14:** Architecture diagram needs to be created (does not exist yet). Created as HTML/SVG, exported to PDF for inclusion.
- **D-15:** Separate Datasets subsection under Experiments describing UCF-Crime and XD-Violence with stats, splits, and evaluation protocol.
- **D-16:** Separate Limitations/Future Work section (not folded into conclusion).
- **D-17:** BibTeX library built from scratch by Claude — search for all cited works (Sultani, VadCLIP, CLIP, SigLIP2, CTR-GCN, RTMPose, TENT, SAR, etc.).
- **D-18:** Professor deadline: June 1 (complete draft including TTA results). Official CGW submission deadline: June 6.
- **D-19:** Authorship: solo + supervisor. Paper + oral presentation at CGW '26 (July 9-10, Hsinchu).
- **D-20:** Standard ACM sigconf requirements, no special CFP constraints.

### Results Presentation
- **D-21:** Two separate tables by dataset (UCF-Crime and XD-Violence), each showing all 4 backbones x 6 variants.
- **D-22:** Metrics: AUC + AP + delta columns (delta = improvement over CLIP baseline).
- **D-23:** Gated Fusion rows use mean±std across 3 seeds (42, 123, 2024) instead of single-seed values.
- **D-24:** Table formatting: bold best result per row only (no underline for second-best).
- **D-25:** Delta formatting: signed numbers with arrows (↑+2.3 / ↓-1.5) — works in B&W print.
- **D-26:** Numeric precision: one decimal place (XX.X%) for all reported metrics.
- **D-27:** 4-5 total figures: (1) architecture diagram, (2) temporal score plot (best fusion advantage example), (3) backbone comparison bar chart, (4) gating weight distribution by category. Optional 5th figure TBD.
- **D-28:** All data charts regenerated as publication-quality figures (proper fonts, grayscale-friendly colors, tight layout for ACM column width). Not reusing existing Phase 6/10 charts as-is.
- **D-29:** Separate TTA subsection (4.X TTA Results) with its own table showing source-only vs TENT vs SAR across backbones.
- **D-30:** Hyperparameter sweep mentioned briefly in methodology — report final tuned values without discussing the search process.
- **D-31:** Highlight best configuration per dataset explicitly in results discussion.
- **D-32:** Computational cost: brief paragraph noting hardware setup (RTX 4090) and rough extraction/training times. No dedicated comparison table.

### Writing Workflow
- **D-33:** Write directly in LaTeX (.tex files in repo), upload to Overleaf for compilation. Overleaf will be set up (no local TeX installation).
- **D-34:** Claude writes full prose drafts in formal academic style with proper hedging.
- **D-35:** Single .tex file (no \\input splitting).
- **D-36:** Full draft written in one pass, then reviewed holistically (not section-by-section).
- **D-37:** Claude handles all LaTeX formatting: table/figure numbering, \\ref/\\label cross-references, citation formatting, BibTeX.
- **D-38:** Figures generated as PDF/PNG files, included via \\includegraphics.
- **D-39:** Rename `CGW2026_Latex_Paper_Template/` to a paper-specific directory name.

### Claude's Discretion
- **D-40:** Dataset-specific backbone divergence (Giant-opt leads UCF, SO400M leads XD) — Claude determines appropriate emphasis in discussion section based on narrative flow.
- **D-41:** Skeleton-only gap analysis (71.8% vs ~82% CLIP-only on UCF) — Claude frames this to strengthen the complementarity argument.
- **D-42:** Abstract timing — Claude decides whether to draft abstract first as a guide or last as a summary.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Venue Template
- `CGW2026_Latex_Paper_Template/sample-sigconf.tex` — ACM sigconf template with CGW '26 venue metadata (July 9-10, Hsinchu)
- `CGW2026_Latex_Paper_Template/acmart.cls` — ACM article class file
- `CGW2026_Latex_Paper_Template/ACM-Reference-Format.bst` — BibTeX style

### Experimental Results
- `results/phase10_charts/backbone_comparison_4way.csv` — Complete four-way backbone comparison data (all variants, both datasets)
- `results/phase10_charts/seed_stability_4way.csv` — 3-seed stability data for Gated Fusion
- `results/phase6_charts/` — Qualitative visualizations (temporal scores, skeleton overlays, gating analysis, t-SNE, corruption)
- `results/phase8_charts/backbone_comparison.csv` — 2-way comparison (CLIP vs SigLIP2)
- `results/phase9_charts/backbone_comparison_3way.csv` — 3-way comparison data

### Project Context
- `.planning/ROADMAP.md` — Full phase history and experiment overview
- `.planning/PROJECT.md` — Project specification and constraints

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/generate_phase10_charts.py` — Chart generation infrastructure; adapt for publication-quality figure generation
- `scripts/generate_phase8_charts.py`, `scripts/generate_phase9_charts.py` — Prior chart generation patterns
- `scripts/run_ablations.py` — Ablation queue runner; needed for TTA experiments across backbones
- Feature extraction scripts — Needed for TTA corruption pipeline on all backbone variants
- `configs/` — YAML config files for all backbone variants (CLIP, SigLIP2, SO400M, Giant-opt)

### Established Patterns
- Results stored as `results/{dataset}_{variant}_{backbone}_s{seed}/` directories with JSON metrics
- Phase chart outputs go to `results/phase{N}_charts/` with CSV + PNG pairs
- Config-driven experiment execution via YAML files in `configs/`

### Integration Points
- TTA experiments need to integrate with existing feature extraction + training pipeline across all 4 backbones
- Chart generation scripts need publication-quality overhaul (fonts, colors, sizing for ACM column width)
- Results CSV files are the data source for LaTeX table generation

</code_context>

<specifics>
## Specific Ideas

- Paper first for CGW '26 workshop, full thesis expanded later as separate effort
- Temporal score plot should showcase the video where gated fusion most clearly outperforms single-modality (Claude selects from existing Phase 6 charts)
- Gating weight distribution figure should demonstrate category-specific modality preferences
- Delta arrows (↑/↓) for print-friendly improvement indicators in tables

</specifics>

<deferred>
## Deferred Ideas

- **Presentation slides:** Separate phase after paper is accepted — oral presentation at CGW '26
- **Full thesis manuscript:** Expanded version of the workshop paper with additional chapters, extended results
- **External baseline comparison table:** Could be added for the full thesis version if needed

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-Thesis Manuscript*
*Context gathered: 2026-05-29*
