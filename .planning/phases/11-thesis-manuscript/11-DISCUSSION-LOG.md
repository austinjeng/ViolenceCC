# Phase 11: Thesis Manuscript - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-29
**Phase:** 11-thesis-manuscript
**Areas discussed:** Narrative Framing, Paper Structure, Results Presentation, Writing Workflow

---

## Narrative Framing

| Option | Description | Selected |
|--------|-------------|----------|
| Dual-modal fusion framework | Main contribution is the skeleton+visual fusion architecture | |
| Backbone comparison study | Main contribution is the systematic CLIP vs SigLIP2 comparison | |
| Full pipeline study | Complete pipeline — fusion + backbone comparison + TTA together | ✓ |

**User's choice:** Full pipeline study
**Notes:** Paper tells a cohesive story about practical weakly-supervised VAD

### Title Direction

| Option | Description | Selected |
|--------|-------------|----------|
| Method-focused | e.g., "Dual-Modal Skeleton-Visual Fusion for..." | ✓ |
| Study-focused | e.g., "A Comprehensive Study of..." | |
| Let supervisor decide | Draft first, advisor picks title later | |

### TTA Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Include existing TTA results | Use Phase 6 corruption results as preliminary findings | |
| Omit TTA entirely | Skip TTA, focus on fusion + backbone comparison | |
| Execute Phase 5 first | Run TTA experiments before writing | |

**User's choice:** Run TTA on all backbone variants (including SigLIP2 models), then write about complete results.

### Skeleton Role

| Option | Description | Selected |
|--------|-------------|----------|
| Core modality | Equal partner to visual features — fusion IS the contribution | ✓ |
| Supplementary signal | Honest about limited contribution | |
| Depends on numbers | Let data speak | |

### MIL Framing

| Option | Description | Selected |
|--------|-------------|----------|
| Training recipe | Adopted from RTFM/Sultani, not novel | ✓ |
| Methodological contribution | Adaptation to dual-modal is itself a contribution | |
| Background context | Explained in related work as standard approach | |

### External Baselines

| Option | Description | Selected |
|--------|-------------|----------|
| VadCLIP + CLIP-TSA | Compare against recent CLIP-based VAD methods | |
| No external baselines | Self-contained — compare own variants | |
| SOTAs from literature | Table of published numbers for context | |

**User's choice:** Cite VadCLIP for context in related work only. User noted VadCLIP is single-modal CLIP, so not a direct comparison.

### Qualitative Analysis

| Option | Description | Selected |
|--------|-------------|----------|
| Include key visuals | 2-3 best figures to complement tables | ✓ |
| Quantitative only | Tables and bar charts only | |
| Appendix/supplementary | Qualitative in supplementary material | |

### Paper vs Thesis

| Option | Description | Selected |
|--------|-------------|----------|
| Workshop paper = thesis | Published paper IS the thesis | |
| Paper first, thesis later | Workshop paper now, expand to thesis separately | ✓ |
| Thesis with paper format | Thesis in ACM sigconf format | |

### Supervisor Guidance

| Option | Description | Selected |
|--------|-------------|----------|
| No specific guidance yet | Present draft and iterate | ✓ |
| Supervisor has direction | Specific expectations exist | |
| Will discuss with supervisor | Planning to align first | |

---

## Paper Structure

### Page Limit
**User's choice:** 8-10 pages

### Space Allocation

| Option | Description | Selected |
|--------|-------------|----------|
| Experiments-heavy | ~1p intro, ~1p related, ~1.5p method, ~4p experiments, ~0.5p conclusion | ✓ |
| Balanced | ~1.5p intro, ~1.5p related, ~2p method, ~3p experiments, ~0.5p conclusion | |

### Methodology Depth

| Option | Description | Selected |
|--------|-------------|----------|
| System diagram + brief | Architecture figure, 1-2 paragraphs per component | |
| Detailed per-component | Each pipeline in its own subsection with equations | ✓ |
| Diagram + equations | Figure + key equations only | |

### Architecture Diagram
**User's choice:** Needs to be created (does not exist)

### Datasets Section
**User's choice:** Separate subsection under Experiments

### Language
**User's choice:** English

### BibTeX
**Notes:** Template .bib is generic ACM sample — needs to be built from scratch with project-specific citations

### Review Format
**User's choice:** Single-blind or no blind

### Deadline
**User's choice:** June 1 professor deadline (complete draft including TTA), June 6 official submission

### Draft Scope
**User's choice:** Complete draft for June 1

### Phase 10 Status
**Notes:** Verified complete — all Giant-opt results ready, 4-way comparison CSV and charts exist

### Limitations Section
**User's choice:** Separate section (not folded into conclusion)

### Authorship
**User's choice:** Solo + supervisor

### Presentation
**User's choice:** Paper + oral at CGW '26; slides are a separate phase

### CFP Requirements
**User's choice:** Standard ACM sigconf, no special constraints

---

## Results Presentation

### Main Table Format

| Option | Description | Selected |
|--------|-------------|----------|
| Single mega-table | One large table, all backbones/variants/datasets | |
| Two tables by dataset | Separate UCF and XD tables | ✓ |
| Condensed + full | Main table + supplementary full ablation | |

### Metrics

| Option | Description | Selected |
|--------|-------------|----------|
| AUC + AP | Both metrics, standard | |
| AUC only | Primary metric only | |
| AUC + AP + delta | Both metrics + improvement over CLIP baseline | ✓ |

### Seed Stability

| Option | Description | Selected |
|--------|-------------|----------|
| Mean ± std in main table | Replace single-seed with aggregated values | ✓ |
| Separate stability table | Main uses seed 42, separate table for stability | |
| Both | Mean±std in main + separate per-seed breakdown | |

### Figures

| Option | Description | Selected |
|--------|-------------|----------|
| Architecture + 2-3 key charts | System diagram + temporal + backbone bars + skeleton viz | ✓ |
| Architecture + backbone + t-SNE | Diagram + bars + projection | |

**Count:** 4-5 figures total

### Temporal Score Plot
**User's choice:** Best fusion advantage example (Claude selects)

### Chart Style

| Option | Description | Selected |
|--------|-------------|----------|
| Publication-quality remake | Regenerate with proper fonts/colors/layout for ACM | ✓ |
| Reuse existing | Phase 10 charts as-is | |
| LaTeX TikZ | Native LaTeX charts | |

### Best Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Highlight best per dataset | Explicitly identify and discuss best combo per dataset | ✓ |
| Neutral analysis | Present equally, discuss patterns | |

### TTA Results Format

| Option | Description | Selected |
|--------|-------------|----------|
| Separate TTA subsection | Dedicated subsection with own table | ✓ |
| Integrated into main tables | TTA as additional dimension | |

### Hyperparameter Sweep

| Option | Description | Selected |
|--------|-------------|----------|
| Mention in methodology | Brief mention, report final values | ✓ |
| Sensitivity analysis | Show key HP sensitivity figure | |
| Skip entirely | Just use tuned values | |

### Gating Visualization

| Option | Description | Selected |
|--------|-------------|----------|
| Include as a figure | Shows category-specific modality preferences | ✓ |
| Text only | Describe without figure | |
| Skip | Not worth showing | |

### Table Formatting
- **Bold:** Best only (no underline for second-best)
- **Deltas:** Signed numbers with arrows (↑/↓)
- **Precision:** One decimal place (XX.X%)

### HP Disclosure
**User's choice:** Just list final values without discussing tuning process

### Computational Cost
**User's choice:** Brief paragraph (hardware + rough times), no comparison table

---

## Writing Workflow

### Draft Format

| Option | Description | Selected |
|--------|-------------|----------|
| LaTeX directly | Write .tex files using ACM sigconf template | ✓ |
| Markdown first | Draft in markdown, convert later | |
| Section-by-section LaTeX | One section at a time | |

### Draft Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Full prose drafts | Claude writes complete section text | ✓ |
| Detailed outlines | Bullet-point outlines, user writes prose | |
| Mixed | Full prose for data-heavy, outlines for narrative | |

### BibTeX
**User's choice:** Claude builds it by searching for citation details

### Review Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Section-by-section | Write, review, approve, next | |
| Full draft then review | Write entire paper, review holistically | ✓ |
| Priority sections first | Experiments first, then methodology, then rest | |

### File Location
**User's choice:** Rename `CGW2026_Latex_Paper_Template/` to paper-specific directory name

### Figure Format

| Option | Description | Selected |
|--------|-------------|----------|
| PDF/PNG + includegraphics | Generate as images, include in LaTeX | ✓ |
| TikZ inline | Native LaTeX figures | |
| Mix | Architecture in TikZ, data charts as PDF | |

### LaTeX Setup
**User's choice:** Overleaf (no local installation)

### Authoring Location
**User's choice:** Write .tex files in repo, upload to Overleaf

### File Structure
**User's choice:** Single .tex file (no \input splitting)

### Writing Style
**User's choice:** Formal academic (proper hedging)

### TTA Experiments
**User's choice:** Part of Phase 11 (run experiments + write paper)

### Architecture Diagram Tool
**User's choice:** HTML/SVG → export to PDF

### Formatting Responsibility
**User's choice:** Claude handles everything (tables, figures, refs, labels, citations)

---

## Claude's Discretion

- Dataset-specific backbone divergence emphasis (Giant-opt leads UCF, SO400M leads XD)
- Skeleton-only gap analysis framing
- Abstract timing (draft first vs last)

## Deferred Ideas

- Presentation slides — separate phase after paper acceptance
- Full thesis manuscript — expanded version for thesis submission
- External baseline comparison table — could add for full thesis
