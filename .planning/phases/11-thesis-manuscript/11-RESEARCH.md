# Phase 11: Thesis Manuscript - Research

**Researched:** 2026-05-30
**Domain:** Academic paper writing (LaTeX/ACM sigconf), experimental results integration, TTA experiments
**Confidence:** HIGH

## Summary

Phase 11 is a mixed writing-and-experiments phase: the primary deliverable is a complete 8-10 page CGW '26 workshop paper in ACM sigconf format, but it also includes running TTA experiments on all 4 backbone variants (currently only CLIP has TTA results). The writing task draws from extensive existing experimental data across 766+ completed runs spanning 4 backbone variants (CLIP ViT-B/16, SigLIP2 ViT-B/16, SigLIP2 SO400M, SigLIP2 Giant-opt) on 2 datasets (UCF-Crime, XD-Violence). The existing CGW '26 template provides the exact ACM sigconf formatting scaffold needed.

The TTA experiment scope is significant but feasible: existing TTA infrastructure (500 runs for CLIP backbone) needs to be extended to 3 additional backbones. This requires (1) corrupted feature re-extraction for SigLIP2/SO400M/Giant on UCF test videos (~78 min GPU total), (2) modifying `evaluate_tta.py` to accept backbone-parameterized feature paths, and (3) running reduced TTA grids (source_only + best TENT config + best SAR config) per backbone. The existing CLIP TTA results show marginal AUC improvements from LN-based adaptation (source=0.499 vs TENT=0.510 vs SAR=0.518 at gaussian_noise severity 3), which is itself a meaningful negative finding for the paper.

**Primary recommendation:** Structure the phase as three sequential waves: (1) TTA backbone experiments + BibTeX library, (2) publication-quality figure generation + architecture diagram, (3) full LaTeX paper draft in a single pass. Target June 1 professor deadline.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Central contribution is the full pipeline study -- fusion framework + backbone comparison + TTA investigation together.
- **D-02:** Method-focused title direction (e.g., "Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection").
- **D-03:** Skeleton positioned as a core modality, not a supplementary signal.
- **D-04:** MIL ranking loss is adopted from Sultani/RTFM, not a methodological contribution.
- **D-05:** VadCLIP cited for context in related work only, not a direct comparison baseline.
- **D-06:** No external baseline comparison table. Self-contained variant comparison.
- **D-07:** TTA experiments will run on ALL backbone variants (CLIP, SigLIP2 ViT-B/16, SO400M, Giant-opt) with TENT and SAR on LayerNorm.
- **D-08:** Target audience is CGW workshop attendees (computer graphics/multimedia).
- **D-09:** Include 2-3 key qualitative visuals.
- **D-10:** No supervisor guidance on paper angle yet.
- **D-11:** 8-10 pages, ACM sigconf format, English, single-blind review.
- **D-12:** Experiments-heavy allocation: ~1p intro, ~1p related work, ~1.5p methodology, ~4p experiments/results, ~0.5p conclusion + separate Limitations section.
- **D-13:** Detailed per-component methodology subsections.
- **D-14:** Architecture diagram created as HTML/SVG, exported to PDF for inclusion.
- **D-15:** Separate Datasets subsection under Experiments.
- **D-16:** Separate Limitations/Future Work section.
- **D-17:** BibTeX library built from scratch by Claude.
- **D-18:** Professor deadline: June 1 (complete draft including TTA results). CGW submission deadline: June 6.
- **D-19:** Authorship: solo + supervisor. Paper + oral presentation at CGW '26 (July 9-10, Hsinchu).
- **D-20:** Standard ACM sigconf requirements.
- **D-21:** Two separate tables by dataset (UCF-Crime and XD-Violence), each showing all 4 backbones x 6 variants.
- **D-22:** Metrics: AUC + AP + delta columns (delta = improvement over CLIP baseline).
- **D-23:** Gated Fusion rows use mean+/-std across 3 seeds (42, 123, 2024).
- **D-24:** Table formatting: bold best result per row only.
- **D-25:** Delta formatting: signed numbers with arrows (up/down).
- **D-26:** Numeric precision: one decimal place (XX.X%) for all reported metrics.
- **D-27:** 4-5 total figures: (1) architecture diagram, (2) temporal score plot, (3) backbone comparison bar chart, (4) gating weight distribution. Optional 5th figure TBD.
- **D-28:** All data charts regenerated as publication-quality figures (proper fonts, grayscale-friendly, tight layout for ACM column width). Not reusing Phase 6/10 charts as-is.
- **D-29:** Separate TTA subsection (4.X TTA Results) with its own table.
- **D-30:** Hyperparameter sweep mentioned briefly; report final tuned values without discussing search process.
- **D-31:** Highlight best configuration per dataset explicitly.
- **D-32:** Computational cost: brief paragraph noting hardware setup and rough times.
- **D-33:** Write directly in LaTeX (.tex files in repo), upload to Overleaf for compilation.
- **D-34:** Claude writes full prose drafts in formal academic style with proper hedging.
- **D-35:** Single .tex file (no \input splitting).
- **D-36:** Full draft written in one pass, then reviewed holistically.
- **D-37:** Claude handles all LaTeX formatting.
- **D-38:** Figures generated as PDF/PNG files, included via \includegraphics.
- **D-39:** Rename `CGW2026_Latex_Paper_Template/` to a paper-specific directory name.

### Claude's Discretion
- **D-40:** Dataset-specific backbone divergence emphasis in discussion.
- **D-41:** Skeleton-only gap analysis framing.
- **D-42:** Abstract timing (first vs last).

### Deferred Ideas (OUT OF SCOPE)
- **Presentation slides:** Separate phase after paper is accepted.
- **Full thesis manuscript:** Expanded version of the workshop paper.
- **External baseline comparison table:** Could be added for full thesis version.

</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| TTA corruption feature extraction | GPU compute (vcc-main env) | Extraction script | Existing `extract_clip.py` with `--backbone` + `--corruption-type` flags |
| TTA evaluation runs | GPU compute (vcc-main env) | `evaluate_tta.py` | Needs backbone parameterization (currently CLIP-hardcoded) |
| Publication figure generation | Python scripts | matplotlib/seaborn | New script adapting Phase 10 chart patterns for ACM column widths |
| Architecture diagram | HTML/SVG tooling | Manual export to PDF | D-14: created as HTML/SVG, exported to PDF |
| LaTeX paper | Repo text file | Overleaf compilation | D-33: write in repo, compile on Overleaf |
| BibTeX references | Repo text file | Claude research | D-17: built from scratch |
| Results data aggregation | CSV files in results/ | Python scripts | backbone_comparison_4way.csv is the primary data source |

## Standard Stack

This phase requires no new library installations. All tools are already available in vcc-main.

### Core (Already Installed)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| matplotlib | (in vcc-main) | Publication-quality figure generation | Available |
| seaborn | (in vcc-main) | Statistical visualization styling | Available |
| pandas | (in vcc-main) | CSV data manipulation for tables | Available |
| numpy | (in vcc-main) | Array operations for TTA evaluation | Available |
| PyTorch | 2.6.0 | TTA model adaptation | Available |

### External Tools (No Install)
| Tool | Purpose | Status |
|------|---------|--------|
| Overleaf | LaTeX compilation | D-33: user will set up; no local TeX installation needed |
| ACM sigconf template | Paper formatting | Already in repo at `CGW2026_Latex_Paper_Template/` |

## Architecture Patterns

### System Architecture Diagram

```
                     Phase 11 Workflow
                     =================

[Existing Results]                [New TTA Experiments]
       |                                |
results/phase10_charts/          E:/features/ucf/
  backbone_comparison_4way.csv     siglip2_gaussian_noise_1/  (NEW)
  seed_stability_4way.csv          siglip2_so400m_...         (NEW)
       |                            siglip2_giant_...         (NEW)
       v                                |
[Figure Generation Scripts]      [evaluate_tta.py]  (MODIFIED)
  scripts/generate_pub_figs.py         |
       |                          results/tta_backbone/  (NEW)
       v                                |
[Paper Directory]  <--------------------+
  paper/
    main.tex          (single .tex file)
    references.bib    (BibTeX from scratch)
    figures/           (PDF/PNG)
      arch_diagram.pdf
      temporal_scores.pdf
      backbone_bars.pdf
      gating_dist.pdf
```

### Recommended Project Structure
```
paper/                              # Renamed from CGW2026_Latex_Paper_Template/
  acmart.cls                        # ACM class file (from template)
  ACM-Reference-Format.bst         # BibTeX style (from template)
  main.tex                          # Single .tex file (D-35)
  references.bib                    # BibTeX library (D-17)
  figures/                          # Publication-quality figures
    fig_architecture.pdf            # Pipeline diagram (D-14)
    fig_temporal_scores.pdf         # Temporal score plot (D-27.2)
    fig_backbone_comparison.pdf     # Backbone bar chart (D-27.3)
    fig_gating_distribution.pdf     # Gating weight analysis (D-27.4)
```

### Pattern 1: ACM sigconf Paper Structure
**What:** The standard ACM sigconf document structure as specified in the template.
**When to use:** This is the only pattern -- the entire paper uses this format.
**Template scaffold (from `sample-sigconf.tex` analysis):**
```latex
\documentclass[sigconf]{acmart}

% Venue metadata (already configured in template)
\setcopyright{rightsretained}
\acmConference[CGW '26]{}{July 09--10, 2026}{Hsinchu City, Taiwan}

% Disable ACM reference format line (per template)
\settopmatter{printacmref=false}

\begin{document}
\title[Short Title]{Full Title}
\author{...}\affiliation{...}\email{...}

\begin{abstract} ... \end{abstract}
\keywords{video anomaly detection, weakly supervised, multi-modal fusion, ...}

\maketitle
\pagestyle{plain}

\section{Introduction}           % ~1 page
\section{Related Work}           % ~1 page
\section{Methodology}            % ~1.5 pages
\subsection{Skeleton Extraction with RTMPose}
\subsection{CTR-GCN Feature Extraction}
\subsection{Visual-Language Feature Extraction}
\subsection{Fusion Mechanisms}
\subsection{MIL Training with Ranking Loss}
\section{Experiments}            % ~4 pages
\subsection{Datasets}
\subsection{Implementation Details}
\subsection{Ablation Study}
\subsection{Backbone Comparison}
\subsection{TTA Results}
\section{Discussion}
\section{Limitations and Future Work}
\section{Conclusion}             % ~0.5 page

\begin{acks} ... \end{acks}
\bibliographystyle{ACM-Reference-Format}
\bibliography{references}
\end{document}
```

### Pattern 2: Publication-Quality Table Formatting
**What:** LaTeX table formatting per D-21 through D-26.
**Key rules:**
- Two separate tables, one per dataset (UCF-Crime AUC, XD-Violence AP as primary metrics)
- 4 backbone columns + delta columns
- `\textbf{}` for best result per row (D-24)
- Delta arrows: `$\uparrow$+2.3` / `$\downarrow$-1.5` (D-25)
- One decimal place: `82.3\%` not `0.8226` (D-26)
- Gated Fusion rows show `mean$\pm$std` from 3 seeds (D-23)
- Use `booktabs` (`\toprule`, `\midrule`, `\bottomrule`) per ACM template
- Use `table*` for full-width tables spanning both columns

### Pattern 3: Figure Dimensions for ACM sigconf
**What:** Target dimensions for figures in two-column ACM format.
**Column width:** ~3.33 inches (84.7mm). `\columnwidth` in LaTeX.
**Full width:** ~7 inches (177.8mm). `\textwidth` in LaTeX.
**Best practices:**
- Single-column figures: 3.33in wide, use `\columnwidth`
- Full-width figures: 7in wide, use `\textwidth` (for architecture diagram, wide tables)
- DPI: 300 for raster (PNG), vector (PDF) preferred
- Font sizes in figures: minimum 7pt to remain readable at column width
- Grayscale-friendly colors (D-28): use hatching/markers in addition to color

### Anti-Patterns to Avoid
- **Reusing Phase 6/10 charts directly:** D-28 explicitly says regenerate all as publication-quality. Phase 6/10 charts use 150 DPI and are sized for screen, not ACM column width.
- **Multiple .tex files:** D-35 says single .tex file. Do not split into chapter files.
- **External baselines:** D-06 explicitly prohibits external baseline comparison table.
- **VadCLIP as a comparison method:** D-05 says VadCLIP is cited for context only, not compared against.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LaTeX table generation | Manual table typing | Python script reading CSVs + generating LaTeX | 4 backbones x 6 variants x 2 datasets x delta columns = error-prone manual entry |
| BibTeX entries | Manual entry from memory | Search official publication venues (CVPR, AAAI, ICLR, NeurIPS proceedings) | Incorrect year/venue/page numbers are reviewable errors |
| Architecture diagram | TikZ from scratch | HTML/SVG tool + PDF export (D-14) | TikZ for pipeline diagrams is time-consuming; HTML/SVG is faster to iterate |
| Figure font sizing | Per-figure manual adjustment | Matplotlib rcParams preset for ACM column width | Consistent font sizes across all figures |

## TTA Experiment Scope Analysis

### Current State (CLIP-only, 500 runs complete)
- **Source model:** `ucf_gated_fusion_s42` (CLIP backbone, AUC=0.8227)
- **Corrupted features:** 20 corruption conditions (4 types x 5 severities) for CLIP visual features + 10 for skeleton (motion_blur + jpeg_compression only)
- **TTA methods:** source_only (20 runs), TENT (80 runs: 4 LRs x 20 conditions), SAR (400 runs: 4 LRs x 5 rhos x 20 conditions)
- **Key finding:** LN-based TTA shows marginal improvement. At gaussian_noise severity 3: source_only=0.499, TENT=0.510, SAR=0.518. [VERIFIED: results/tta/ metrics files]

### New Work Required (D-07: all 4 backbones)

**Step 1: Corrupted Feature Extraction (3 additional backbones)**

The `extract_clip.py` script already supports `--backbone` and `--corruption-type` flags. [VERIFIED: codebase grep] For each of the 3 additional backbones (siglip2-base, siglip2-so400m, siglip2-giant), extract corrupted features for the UCF test split (255 videos):

- 3 backbones x 4 corruption types x 5 severities = 60 extraction runs
- Estimated time per backbone: ~26 min (255 test videos vs 1729 total, scaled from ~9 min full UCF CLIP extraction)
- Total new extraction time: ~78 min GPU [ASSUMED -- scaled estimate]

Skeleton corruption features are backbone-independent (same skeleton for all backbones), so the existing 10 skeleton corruption directories are reused. Only visual corruption features need re-extraction.

**Step 2: evaluate_tta.py Modification**

Current `evaluate_tta.py` hardcodes:
- Line 94: `clip_dir = feature_root / f"clip_{corruption_type}_{severity}"` -- needs to accept backbone-specific subdir (e.g., `siglip2_gaussian_noise_1`)
- Line 106: `clip_feat = np.load(str(clip_path))  # [N, 1024]` -- dimension varies by backbone (1024/1536/2304/3072)
- Line 255: `test_split` hardcoded to UCF -- acceptable since TTA is UCF-only

Modification: add `--backbone` flag that maps to feature subdirectory prefix and selects the correct source model run directory.

**Step 3: Reduced TTA Run Grid**

For the paper, running the full 500-config grid per backbone is unnecessary. Use a reduced grid:
- Source-only: 20 runs (4 types x 5 severities) per backbone
- Best TENT config from CLIP results: 20 runs per backbone
- Best SAR config from CLIP results: 20 runs per backbone
- Total: 60 runs per backbone x 3 backbones = 180 new TTA runs
- At ~5 seconds per run: ~15 min total TTA evaluation time

**Total new experiment time: ~93 min GPU (78 min extraction + 15 min TTA)**

### TTA Paper Table Structure (D-29)

```
Table 3: TTA Results on UCF-Crime-C (averaged over 4 corruption types x 5 severities)

Backbone        | Source-Only AUC | TENT AUC | SAR AUC | Best Delta
----------------|-----------------|----------|---------|----------
CLIP ViT-B/16   | XX.X            | XX.X     | XX.X    | +X.X
SigLIP2 ViT-B/16| XX.X            | XX.X     | XX.X    | +X.X
SigLIP2 SO400M  | XX.X            | XX.X     | XX.X    | +X.X
SigLIP2 Giant   | XX.X            | XX.X     | XX.X    | +X.X
```

## Results Data Inventory

### Available Data Sources (all VERIFIED from filesystem)

| Source | Location | Content | Status |
|--------|----------|---------|--------|
| Four-way backbone comparison | `results/phase10_charts/backbone_comparison_4way.csv` | 12 rows: 6 variants x 2 datasets, all 4 backbones with deltas | Complete |
| Seed stability | `results/phase10_charts/seed_stability_4way.csv` | 6 rows: 3 seeds x 2 datasets, Gated Fusion across 4 backbones | Complete |
| Results index | `results/results-index.csv` | 766 rows: all runs across all phases | Complete |
| TTA results (CLIP only) | `results/tta/` | 500 directories with eval_metrics.json | Complete |
| Phase 6 temporal curves | `results/phase6_charts/A_temporal/` | 5 temporal score plots (3 UCF, 2 XD) | Complete |
| Phase 6 skeleton overlays | `results/phase6_charts/B_skeleton/` | 3 skeleton overlay images | Complete |
| Phase 6 corruption heatmaps | `results/phase6_charts/C_corruption/` | 6 corruption analysis charts | Complete |
| Phase 6 gating distributions | `results/phase6_charts/D_gating/` | 4 gating analysis charts (2 UCF, 2 XD) | Complete |
| Phase 6 t-SNE projections | `results/phase6_charts/E_projection/` | 2 t-SNE plots (UCF, XD) | Complete |
| Phase 6 additional figures | `results/phase6_charts/F_additional/` | 6 supplementary charts | Complete |

### Key Numeric Results for Paper Tables

**UCF-Crime (AUC, seed 42):** [VERIFIED: backbone_comparison_4way.csv]
| Variant | CLIP | SigLIP2 | SO400M | Giant |
|---------|------|---------|--------|-------|
| Skeleton Only | 71.8 | -- | -- | -- |
| Visual Only | 81.7 | 79.1 | 81.4 | 83.1 |
| Late Fusion | 78.7 | 79.9 | 80.3 | 80.9 |
| Gated Fusion | 82.3 | 79.6 | 82.2 | 83.2 |
| GF 2-Person | 81.7 | 79.5 | 82.0 | 83.5 |
| GF Mean-Only | 81.8 | 80.0 | 82.4 | 83.6 |

**XD-Violence (AP, seed 42):** [VERIFIED: backbone_comparison_4way.csv]
| Variant | CLIP | SigLIP2 | SO400M | Giant |
|---------|------|---------|--------|-------|
| Skeleton Only | 41.3 | -- | -- | -- |
| Visual Only | 70.5 | 72.1 | 77.6 | 76.3 |
| Late Fusion | 65.5 | 65.6 | 66.4 | 66.6 |
| Gated Fusion | 71.9 | 71.9 | 73.8 | 72.8 |
| GF 2-Person | 71.0 | 73.1 | 74.8 | 72.7 |
| GF Mean-Only | 69.6 | 72.4 | 72.5 | 73.8 |

**Seed Stability (3-seed mean +/- std):** [VERIFIED: seed_stability_4way.csv]
- UCF Gated Fusion AUC: CLIP 82.0+/-0.29, SigLIP2 79.8+/-0.24, SO400M 81.9+/-0.39, Giant 83.3+/-0.35
- XD Gated Fusion AP: CLIP 70.9+/-1.08, SigLIP2 74.7+/-2.93, SO400M 73.8+/-2.82, Giant 73.8+/-1.58

**Key finding: Dataset-specific backbone divergence**
- UCF-Crime: Giant-opt leads (83.6% GF Mean-Only AUC), CLIP competitive (82.3% Gated Fusion AUC)
- XD-Violence: SO400M leads (77.6% Visual-Only AP, 74.8% GF 2-Person AP), Giant close behind

## BibTeX Reference Inventory

The following papers must be cited. BibTeX entries will be constructed from official publication metadata. [ASSUMED -- specific BibTeX fields need lookup at write time]

### Core Methods (MUST cite)
| Paper | Venue | Year | Key Ref |
|-------|-------|------|---------|
| Sultani et al., "Real-World Anomaly Detection in Surveillance Videos" | CVPR | 2018 | UCF-Crime dataset, MIL ranking loss |
| Tian et al., "Weakly-supervised Video Anomaly Detection with Robust Temporal Feature Magnitude Learning" (RTFM) | ICCV | 2021 | MIL training recipe adopted |
| Wu et al., "Not Only Look, but Also Hear..." (XD-Violence) | ECCV | 2020 | XD-Violence dataset |
| Radford et al., "Learning Transferable Visual Models From Natural Language Supervision" (CLIP) | ICML | 2021 | CLIP ViT-B/16 backbone |
| Zhai et al., "SigLIP..." / Tschannen et al., "SigLIP 2" | ICCV/arXiv | 2023/2025 | SigLIP2 backbone variants |
| Chen et al., "Channel-wise Topology Refinement Graph Convolution" (CTR-GCN) | ICCV | 2021 | Skeleton backbone |
| Jiang et al., "RTMPose" | arXiv | 2023 | Skeleton extraction |
| Wang et al., "TENT: Fully Test-Time Adaptation by Entropy Minimization" | ICLR | 2021 | TENT method |
| Niu et al., "Towards Stable Test-Time Adaptation in Dynamic Wild World" (SAR) | ICLR | 2023 | SAR method |
| Wu et al., "VadCLIP" | AAAI | 2024 | CLIP-based VAD context |

### Supporting (SHOULD cite)
| Paper | Venue | Year | Key Ref |
|-------|-------|------|---------|
| Doshi & Yilmaz, "Any-Shot Sequential Anomaly Detection" (skeleton VAD) | CVPRW | 2022 | Skeleton-based anomaly detection |
| Yan et al., "PYSKL" | MM | 2022 | Skeleton GCN toolkit |
| Ilg et al. / Carreira & Zisserman, "I3D" | CVPR | 2017 | I3D features (RTFM baseline) |
| Foret et al., "Sharpness-Aware Minimization" (SAM) | ICLR | 2021 | SAM optimizer in SAR |
| Ba et al., "Layer Normalization" | arXiv | 2016 | LN (vs BN for TTA) |

### Total estimated citations: 15-20

## Common Pitfalls

### Pitfall 1: Table Arithmetic Errors
**What goes wrong:** Manual transcription of numbers from CSVs into LaTeX tables introduces rounding or copy-paste errors, especially with delta calculations.
**Why it happens:** 4 backbones x 6 variants x 2 datasets x multiple metrics = 100+ individual numbers.
**How to avoid:** Generate LaTeX table code programmatically from `backbone_comparison_4way.csv` and `seed_stability_4way.csv`. Never type numbers manually.
**Warning signs:** Delta values that don't match the difference between backbone columns.

### Pitfall 2: Figure Resolution and Sizing for ACM
**What goes wrong:** Figures generated at screen resolution (150 DPI, large dimensions) appear blurry or overflow column width in the PDF.
**Why it happens:** Phase 6/10 charts were designed for screen viewing at 150 DPI, not for print at 300 DPI within 3.33-inch column width.
**How to avoid:** Create a dedicated figure generation script with ACM-specific presets: 300 DPI, 3.33in or 7in wide, minimum 7pt font, grayscale-distinguishable markers/hatching.
**Warning signs:** Text in figures smaller than body text in the compiled PDF.

### Pitfall 3: Overleaf Compilation Failures
**What goes wrong:** Custom packages or incompatible LaTeX syntax causes compilation errors on Overleaf that don't appear locally.
**Why it happens:** Overleaf uses TeX Live with specific package versions; the ACM template is self-contained but custom additions may conflict.
**How to avoid:** Stick strictly to the ACM template packages. Do not add custom packages beyond what `acmart.cls` already provides (it includes booktabs, hyperref, etc.). Test compilation early with a minimal document.
**Warning signs:** Any `\usepackage{}` addition not in the original template.

### Pitfall 4: BibTeX Key Errors
**What goes wrong:** Missing or incorrect BibTeX entries cause `[?]` markers in the compiled PDF.
**Why it happens:** BibTeX keys in `\cite{}` commands don't match entries in the `.bib` file, or entries have malformed fields.
**How to avoid:** Define all BibTeX keys before writing the paper. Use a consistent naming convention (e.g., `sultani2018ucfcrime`, `tian2021rtfm`). Test compilation with bibliography early.
**Warning signs:** Any `\cite{}` command with a key not yet in the `.bib` file.

### Pitfall 5: TTA Feature Path Mismatch
**What goes wrong:** TTA evaluation loads wrong features (CLIP features instead of SigLIP2 corruption features) because the feature subdirectory mapping is incorrect.
**Why it happens:** `evaluate_tta.py` currently hardcodes `clip_` prefix in `_load_test_video_features()`. Adding backbone support requires matching the exact subdirectory names from `extract_clip.py`'s `BACKBONE_CONFIGS`.
**How to avoid:** Parameterize `_load_test_video_features()` with the backbone's `output_subdir` from `BACKBONE_CONFIGS`. Verify by checking `eval_metrics.json` output includes the backbone identifier.
**Warning signs:** TTA AUC identical across backbones (means same features were loaded).

### Pitfall 6: Single-Seed vs Multi-Seed Reporting Inconsistency
**What goes wrong:** Some rows report single-seed (s42) values while Gated Fusion rows report 3-seed mean+/-std, creating confusion about what "the number" represents.
**Why it happens:** Only Gated Fusion had 3-seed stability runs per D-23. Other variants (Skeleton-Only, Visual-Only, Late Fusion, pooling ablations) have single-seed only.
**How to avoid:** Clearly mark which rows are single-seed vs 3-seed in the table caption. Use footnotes if needed. D-23 only requires mean+/-std for Gated Fusion rows.
**Warning signs:** Readers comparing a 3-seed mean to a single-seed value without realizing they're different.

## Code Examples

### LaTeX Table Generation from CSV (Python pattern)
```python
# Source: project convention from generate_phase10_charts.py pattern
import pandas as pd

def csv_to_latex_table(csv_path, dataset, metric_col, caption, label):
    """Generate LaTeX booktabs table from backbone comparison CSV."""
    df = pd.read_csv(csv_path)
    ds = df[df['Dataset'] == dataset.upper()]
    
    lines = []
    lines.append(r'\begin{table*}')
    lines.append(r'  \caption{' + caption + '}')
    lines.append(r'  \label{' + label + '}')
    lines.append(r'  \begin{tabular}{l cccc cc cc}')
    lines.append(r'    \toprule')
    lines.append(r'    Variant & CLIP & SigLIP2 & SO400M & Giant & $\Delta$CLIP-Giant \\')
    lines.append(r'    \midrule')
    
    for _, row in ds.iterrows():
        # Format values at 1 decimal, bold best
        vals = [row.get(f'{b}_{metric_col}', float('nan')) * 100 
                for b in ['CLIP', 'SigLIP2', 'SO400M', 'Giant']]
        best_idx = max(range(len(vals)), key=lambda i: vals[i] if not pd.isna(vals[i]) else -1)
        formatted = []
        for i, v in enumerate(vals):
            s = f'{v:.1f}' if not pd.isna(v) else '--'
            if i == best_idx and not pd.isna(v):
                s = r'\textbf{' + s + '}'
            formatted.append(s)
        
        delta = row.get(f'Delta_CLIP_Giant_{metric_col}', float('nan'))
        if not pd.isna(delta):
            d = delta * 100
            arrow = r'$\uparrow$' if d > 0 else r'$\downarrow$'
            delta_str = f'{arrow}{abs(d):.1f}'
        else:
            delta_str = '--'
        
        lines.append(f'    {row["Variant"]} & {" & ".join(formatted)} & {delta_str} \\\\')
    
    lines.append(r'    \bottomrule')
    lines.append(r'  \end{tabular}')
    lines.append(r'\end{table*}')
    return '\n'.join(lines)
```

### Publication-Quality Figure Matplotlib Preset
```python
# Source: adapted from Phase 10 chart conventions for ACM sigconf
import matplotlib.pyplot as plt
import matplotlib

# ACM sigconf column width
ACM_COL_WIDTH = 3.33  # inches
ACM_TEXT_WIDTH = 7.0   # inches (full width)
PUB_DPI = 300

def set_pub_style():
    """Set matplotlib defaults for ACM sigconf figures."""
    matplotlib.rcParams.update({
        'figure.dpi': PUB_DPI,
        'savefig.dpi': PUB_DPI,
        'font.size': 8,
        'axes.titlesize': 9,
        'axes.labelsize': 8,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'legend.fontsize': 7,
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif'],
        'figure.figsize': (ACM_COL_WIDTH, 2.5),
        'axes.grid': True,
        'grid.alpha': 0.3,
    })

# Grayscale-friendly color palette (D-28)
COLORS = {
    'CLIP': '#2c3e50',       # dark blue-gray
    'SigLIP2': '#7f8c8d',    # medium gray
    'SO400M': '#bdc3c7',     # light gray
    'Giant': '#e74c3c',      # red accent (distinguishable in B&W via hatching)
}
HATCHES = {
    'CLIP': '',
    'SigLIP2': '///',
    'SO400M': '...',
    'Giant': 'xxx',
}
```

### TTA evaluate_tta.py Backbone Extension Pattern
```python
# Source: pattern derived from extract_clip.py BACKBONE_CONFIGS
# Modification to _load_test_video_features():

# Map backbone key to feature subdirectory prefix
BACKBONE_FEATURE_PREFIX = {
    "clip-vit-b-16": "clip",
    "siglip2-base": "siglip2",
    "siglip2-so400m": "siglip2_so400m",
    "siglip2-giant": "siglip2_giant",
}

def _load_test_video_features(
    video_id, corruption_type, severity, feature_root, backbone="clip-vit-b-16"
):
    prefix = BACKBONE_FEATURE_PREFIX[backbone]
    clip_dir = feature_root / f"{prefix}_{corruption_type}_{severity}"
    # Skeleton is backbone-independent
    if corruption_type in SKELETON_REEXTRACT_TYPES:
        skel_dir = feature_root / f"skeleton_{corruption_type}_{severity}"
    else:
        skel_dir = feature_root / "skeleton"
    # ... rest unchanged
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| openai/clip (frozen 2021) | open-clip-torch 3.3.0 | Phase 8 (2026-05) | Enabled SigLIP2 backbone swapping via same API |
| Single CLIP backbone | 4-way backbone comparison | Phase 8-10 (2026-05) | Paper contribution: backbone sensitivity analysis |
| BN-based TTA (TENT/SAR original) | LN-based TTA (this project) | Phase 5 (2026-04) | Paper contribution: first LN TTA evaluation in VAD |
| CLIP-only TTA | All-backbone TTA | Phase 11 (new work) | D-07: extends TTA comparison across backbones |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TTA corruption feature extraction for 3 additional backbones takes ~78 min GPU total | TTA Experiment Scope | Low -- estimate is conservative; actual may be faster or slower by 2x but still feasible within timeline |
| A2 | Reduced TTA grid (60 runs per backbone) is sufficient for paper | TTA Experiment Scope | Medium -- if reviewer expects full grid per backbone, paper needs a sentence justifying the reduced grid |
| A3 | BibTeX entries for all ~15-20 cited papers can be found via standard venues | BibTeX Reference Inventory | Low -- all are well-known publications in top venues |
| A4 | Overleaf compilation of ACM sigconf template works without issues | Architecture Patterns | Low -- ACM template is heavily tested; CGW template is already provided |
| A5 | ACM sigconf column width is ~3.33 inches | Figure Dimensions | Low -- standard ACM two-column format |
| A6 | The best TENT and SAR hyperparameters from CLIP transfer well to other backbones | TTA Experiment Scope | Medium -- different backbones may have different optimal TTA LR/rho; but paper reports per-backbone results regardless |

## Open Questions

1. **Phase 10 ROADMAP Status vs Actual Results**
   - What we know: Phase 10 Giant-opt results exist (14 runs in results-index.csv, backbone_comparison_4way.csv populated). ROADMAP says "0/4 plans complete, Executing."
   - What's unclear: Whether Phase 10 plan files and summaries were formally completed, or if execution happened outside the GSD workflow.
   - Recommendation: Treat results data as available (it is). ROADMAP status is stale metadata, not a blocker.

2. **TTA Best Hyperparameter Selection**
   - What we know: 500 CLIP TTA runs exist with 4 LRs for TENT, 4 LRs x 5 rhos for SAR.
   - What's unclear: Which specific LR and rho configuration performed best overall across all corruption types and severities.
   - Recommendation: Analyze the 500 existing CLIP TTA results to select the best-performing TENT LR and SAR LR+rho before running the backbone TTA grid. This should be done programmatically (find argmax AUC across conditions).

3. **Architecture Diagram Tooling**
   - What we know: D-14 says "created as HTML/SVG, exported to PDF."
   - What's unclear: Which specific tool (draw.io, Excalidraw, raw SVG, Playwright screenshot).
   - Recommendation: Use HTML with inline SVG rendered via Playwright to capture a high-quality PNG/PDF. This aligns with the playwright-cli skill available in the project.

4. **CCS Concepts for CGW Submission**
   - What we know: ACM requires CCS concepts (computing classification system codes) for papers over 2 pages.
   - What's unclear: Whether CGW '26 enforces this requirement or accepts papers without CCS codes.
   - Recommendation: Include CCS concepts -- the template has placeholder code. Use: "Computing methodologies -> Activity recognition and understanding" and "Computing methodologies -> Neural networks".

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| vcc-main conda env | TTA experiments, chart generation | Assumed available | Python 3.11, PyTorch 2.6.0 | -- |
| matplotlib | Figure generation | Available in vcc-main | -- | -- |
| Overleaf | LaTeX compilation | User sets up externally | -- | Local TeX Live (not planned) |
| GPU (RTX 4090) | TTA feature extraction | Available | 24GB VRAM | -- |
| Playwright | Architecture diagram | Available (skill installed) | -- | Manual SVG creation |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing in project) |
| Config file | `pytest.ini` (existing) |
| Quick run command | `pytest tests/ -x -q --tb=short` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
This phase has no new code requirements (writing deliverable). However, the TTA backbone extension involves code changes that should be validated:

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-07 | TTA runs on all 4 backbones | smoke | Verify eval_metrics.json exists for each backbone TTA run | Wave 1 |
| D-21 | Tables show 4 backbones x 6 variants | manual | Visual check of generated LaTeX table code | Wave 2 |
| D-28 | Publication-quality figures | manual | Visual inspection of generated PDFs at 300 DPI | Wave 2 |
| D-35 | Single .tex file compiles | manual | Overleaf compilation succeeds | Wave 3 |

### Sampling Rate
- **Per task commit:** Visual inspection of outputs (no automated test suite for paper writing)
- **Per wave merge:** Verify all outputs from that wave exist and look correct
- **Phase gate:** Complete paper compiles on Overleaf without errors; all tables/figures present

### Wave 0 Gaps
- None -- existing test infrastructure covers TTA code changes; paper writing has no automated test requirement

## Security Domain

> Not applicable -- this phase writes a paper and runs experiments with existing code. No authentication, user input, network services, or cryptography involved. `security_enforcement` considerations do not apply to academic paper writing.

## Project Constraints (from CLAUDE.md)

- **DataLoader Conventions:** Val loaders MUST use `shuffle=True` (relevant if TTA code touches dataloaders -- it does not; TTA loads features directly)
- **Checkpoint Loading:** Always `strict=True` (TTA evaluate_tta.py already uses `strict=True` at line 235)
- **Feature Extraction:** Reuse `decord.VideoReader` across snippets (relevant for corruption re-extraction -- extract_clip.py already follows this)
- **Evaluation Stubs:** Emit runtime warning for placeholder metrics (not applicable to this phase)
- **No headless processes:** TTA extraction and evaluation runs must be in visible terminals (user memory)
- **Present thesis recommendations:** Label recommended option + cite justification (relevant for D-40/D-41 discretion areas)

## Sources

### Primary (HIGH confidence)
- `CGW2026_Latex_Paper_Template/sample-sigconf.tex` -- ACM sigconf template structure, venue metadata
- `results/phase10_charts/backbone_comparison_4way.csv` -- four-way comparison data (all variants, both datasets)
- `results/phase10_charts/seed_stability_4way.csv` -- 3-seed stability data
- `results/tta/*/eval_metrics.json` -- 500 CLIP-only TTA result files
- `scripts/extract_clip.py` -- BACKBONE_CONFIGS supporting all 4 backbones with corruption flags
- `src/tta/evaluate_tta.py` -- TTA evaluation infrastructure (CLIP-hardcoded feature paths)
- `scripts/generate_phase10_charts.py` -- chart generation pattern for matplotlib/seaborn
- `E:/features/ucf/` directory listing -- confirms corruption features exist for CLIP only

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` -- phase history and success criteria
- `.planning/STATE.md` -- accumulated context and key decisions
- `.planning/phases/11-thesis-manuscript/11-CONTEXT.md` -- 42 locked decisions

### Tertiary (LOW confidence)
- ACM sigconf column width ~3.33in [ASSUMED -- standard for two-column ACM format]
- Extraction timing estimates [ASSUMED -- scaled from prior phase timing]

## Metadata

**Confidence breakdown:**
- Results data availability: HIGH -- verified all CSV files and result directories exist on disk
- TTA experiment scope: HIGH -- verified existing code, identified exact modifications needed
- Paper structure: HIGH -- template analyzed, decisions documented in CONTEXT.md
- BibTeX completeness: MEDIUM -- paper list identified but entries not yet constructed
- Timing estimates: MEDIUM -- scaled from prior phase data, not measured for this specific workload

**Research date:** 2026-05-30
**Valid until:** 2026-06-06 (CGW submission deadline)
