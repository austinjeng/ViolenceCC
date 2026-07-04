# Phase 13: Full Thesis Manuscript - Pattern Map

**Mapped:** 2026-07-05
**Files analyzed:** 14 file groups (~35 concrete new files)
**Analogs found:** 12 / 14 (2 with partial/no analog: frontmatter, PROVENANCE.md)

All analogs are READ-ONLY sources. `paper/` is frozen — copy patterns and content OUT of it; never edit it or `\input` across into it.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `thesis/main.tex` | LaTeX root/orchestrator | document build | `paper/main.tex` | role-match (report vs acmart; `\include` chapters) |
| `thesis/preamble.tex` | LaTeX config | document build | `paper/main.tex:23-28` + 13-RESEARCH.md §7 preamble spec | role-match |
| `thesis/frontmatter/*` (titlepage, abstract, toc/lof/lot, notation) | LaTeX frontmatter | document build | `paper/main.tex:32-53` (author block, abstract) — structure from 13-RESEARCH.md §7 report-class notes | partial |
| `thesis/chapters/ch01..ch09.tex` | LaTeX prose/content | document build | `paper/main.tex` §§1-7 (section anchor map in 13-RESEARCH.md §1) | exact (base prose lifts) |
| `thesis/chapters/ch07` SOTA section | LaTeX content lift | document build | `paper/sota_comparison_full.tex:65-329` (fragment body) | exact |
| `thesis/appendices/appA..appF.tex` | LaTeX content | document build | same conventions as chapters; narrative from `.planning/` docs | role-match |
| `thesis/references.bib` | bibliography | document build | `paper/references.bib` (copy as base, 27 entries) | exact |
| `thesis/IEEEtranN.bst` | vendored style | document build | none in repo — copy from local MiKTeX feupphdteses path (13-RESEARCH.md §7) | none (vendoring op) |
| `thesis/.latexmkrc` | build config | document build | `paper/.latexmkrc` | exact |
| `scripts/build_thesis.ps1` | build script | request-response (CLI) | `scripts/build_paper.ps1` | exact (minus line 111; plus preflight + log scan) |
| New corruption-heatmap script (Wave 0) | figure generator | file I/O (JSON→PNG/CSV) | `scripts/pri5_tta_breakdown.py` (data) + `scripts/generate_pub_figures.py` (style) | exact composite |
| New 20×4 severity-heatmap script (Wave 0) | figure generator | file I/O (CSV→PNG) | `scripts/generate_phase10_charts.py` + `generate_pub_figures.py` | exact composite |
| New per-category table script (Wave 0) | table generator | file I/O (CSV→.tex) | `scripts/pri5_tta_breakdown.py:184-205` (LaTeX emission) + `generate_phase10_charts.py:92-109` (3-seed mean) | exact composite |
| `thesis/PROVENANCE.md` | manifest doc | none | `12-VERIFICATION.md:41-54` traceability table format | partial |
| `.gitignore` (edit) | config | none | existing `.gitignore:46-57` paper artifact block | exact |
| `thesis/figures/fig_architecture.tex` | TikZ figure | document build | `paper/figures/fig_architecture.tex` (verbatim copy) | exact |

## Pattern Assignments

### `thesis/main.tex` + `thesis/preamble.tex` (LaTeX root + config)

**Analog:** `paper/main.tex` — but the documentclass changes: `\documentclass[12pt,a4paper,oneside]{report}` per spec §2 D1. Do NOT copy the acmart-specific preamble (lines 4-21: `\AtBeginDocument`, `\setcopyright`, `\acmConference`, `\settopmatter`).

**Package block to carry over** (`paper/main.tex:23-28`):
```latex
%% Additional packages
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{positioning,arrows.meta,fit,calc}
```
Add per 13-RESEARCH.md §7 (lines 417-422): geometry (2.5cm), setspace + `\onehalfspacing`, caption/subcaption, microtype, amsmath, amssymb, natbib `[numbers,sort&compress]`, hyperref LAST (`bookmarksnumbered`, `hidelinks`). Bibliography swap: `\bibliographystyle{IEEEtranN}` + `\bibliography{references}` (IEEEtranN REQUIRES natbib).

**Root structure pattern** (no repo analog for `\include`; per 13-RESEARCH.md §7 lines 446-448):
```latex
% frontmatter: \begin{titlepage}..., \chapter*{Abstract} + \addcontentsline,
% \tableofcontents, \listoffigures, \listoftables, notation table
\include{chapters/ch01_introduction}
...
\appendix
\include{appendices/appA_rtfm_gap}
```

**Comment banner convention** (`paper/main.tex:1-3`, `48-50`) — section-divider `%%` comments before each major unit:
```latex
%%
%% Main LaTeX source for CGW '26 submission
%%
```

---

### `thesis/chapters/ch01..ch09.tex` (LaTeX prose; base lifts from paper)

**Analog:** `paper/main.tex` — the per-chapter line-anchor map is BINDING in 13-RESEARCH.md §1. Patterns every chapter writer must imitate:

**Figure with TikZ input** (`paper/main.tex:113-118`) — in the one-column report use `figure` (not `figure*`); same `\resizebox`:
```latex
\begin{figure*}[t]
  \centering
  \resizebox{\textwidth}{!}{\input{figures/fig_architecture}}
  \caption{Overview of the dual-modal fusion pipeline. ...}
  \label{fig:architecture}
\end{figure*}
```
Copy `fig_architecture.tex` into `thesis/figures/` first — never `\input` across into `paper/`.

**Figure with PDF include** (`paper/main.tex:267-272`; `\columnwidth` → `\textwidth` in one-column report):
```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{figures/fig_temporal_scores.pdf}
  \caption{Temporal anomaly score comparison on a RoadAccidents test video ...}
  \label{fig:temporal-scores}
\end{figure}
```

**booktabs results table** (`paper/main.tex:226-242`, Table 1) — caption states metric, seed protocol, bold rule, Δ baseline; `\toprule/\midrule/\bottomrule`; mean$\pm$std cells; `---` for empty cells:
```latex
\begin{table*}[t]
\caption{Ablation study on UCF-Crime. AUC (\%) reported for each fusion variant across four
visual backbones. All rows show mean$\pm$std over three seeds (42, 123, 2024). Best result
per row in \textbf{bold}. $\Delta$ relative to CLIP ViT-B/16 baseline.}
\label{tab:ucf-ablation}
\begin{tabular}{l c c c c c}
\toprule
Variant & CLIP ViT-B/16 & SigLIP2 Base & SigLIP2 SO400M & SigLIP2 Giant & Best $\Delta$ \\
\midrule
Skeleton Only & \textbf{68.8$\pm$2.8} & --- & --- & --- & --- \\
Gated Fusion & 81.4$\pm$0.3 & 79.0$\pm$0.1 & 81.3$\pm$0.3 & \textbf{82.5$\pm$0.4} & $\uparrow$+1.2 \\
\bottomrule
\end{tabular}
\end{table*}
```
(In report class use `table`, not `table*`.)

**Equation style** (`paper/main.tex:178-186`) — unnumbered-label-free unless referenced; `\label{eq:...}` only where cited; equations are lifted VERBATIM (code-verified — never alter the math):
```latex
\begin{equation}
    \mathcal{L} = \mathcal{L}_{\text{rank}} + \frac{\lambda_1}{T}\sum_{t=1}^{T} \left\| \mathbf{a}_t \right\|_2 + \lambda_2 \sum_i (a_i - a_{i+1})^2
    \label{eq:loss}
\end{equation}
```
The 8 equations live at main.tex L157, L163, L167, L171, L179, L183, L195, L197 (L197 is a ~1,400-char inline paragraph — lift whole).

**Honest-disclosure footnote style** (`paper/main.tex:217`) — MUST survive into Ch 4; this is the template for all disclosure footnotes:
```latex
...while providing a small benefit on UCF-Crime's continuous fixed-camera footage.\footnote{The
reported UCF-Crime numbers were produced with an earlier implementation of the smoothness term;
the released code applies the penalty strictly along the temporal (adjacent-snippet) axis. We
verified that this change shifts the headline UCF-Crime AUC by at most 0.13 percentage
points---within the 0.1--0.4\% seed variance reported below---so the UCF-Crime results are
reported as run.}
```

**Label/ref conventions** (throughout main.tex): `\label{tab:ucf-ablation}`, `\label{fig:architecture}`, `\label{sec:impl}`/`\label{sec:disc}`/`\label{sec:tta}`, `\label{eq:loss}`. References: `Table~\ref{tab:tta}`, `Figure~\ref{fig:backbone-comparison}`, `Section~\ref{sec:impl}`, `Eq.~(\ref{eq:loss})`, `Sec.~\ref{sec:disc}` inside captions. Non-breaking `~` before every `\ref`/`\cite` number word. Keep the paper's label names so cross-references port mechanically; chapters add `sec:`-prefixed labels as needed.

**Prose voice**: bolded thread-lead sentences for findings (`paper/main.tex:265,274`): `\textbf{Gated fusion outperforms late fusion consistently.} ...` — reuse for results chapters.

---

### `thesis/chapters/ch07` SOTA section (fragment lift)

**Analog:** `paper/sota_comparison_full.tex`. Lift ONLY between the markers (line 65 `%% --- FRAGMENT BODY BEGIN ---` and line 329 END); discard the standalone wrapper (`\documentclass[border=12pt,varwidth=560pt]{standalone}` at line 56 and its `\begin{document}/\end{document}`). Note `\usepackage{array}` (line 61) — the fragment's column setups may need `array` in the thesis preamble; verify at Wave-0 compile (Pitfall 14).

**Citation rewiring instruction is embedded in the analog itself** (`sota_comparison_full.tex:28-33`):
```latex
%%  TO REWIRE TO THE REAL references.bib LATER: replace each inline "[N]"
%%  with the corresponding \cite{key}, drop the manual References list at the
%%  bottom, and add the proper @article/@inproceedings entries to the thesis
%%  references.bib. The per-method citation appendix (Section 8 of
%%  .planning/phases/12-sota-comparison-and-positioning/12-RESEARCH-sota.md)
%%  holds the full author/venue strings for each [N].
```
Zero `% RE-VERIFY` comments may survive in thesis/ (they resolve in the Wave-2 gate).

---

### `thesis/references.bib`

**Analog:** `paper/references.bib` — copy verbatim as the base (27 entries), then append ~11 SOTA + ~4 survey entries per 13-RESEARCH.md §6.

**Header + key convention** (`references.bib:1-8`):
```bibtex
%%
%% references.bib -- BibTeX library for CGW '26 submission
%% Key naming convention: firstauthorYYYYkeyword
%%
%% ============================================================
%% MUST-CITE: Core methods and datasets (11 entries)
%% ============================================================
```
Comment-block organization: banner-delimited sections (`MUST-CITE`, `SHOULD-CITE`, `ADDITIONAL`, `SOTA COMPARISON` at lines 6, 108, 156, 177). New thesis sections should follow the same banner style (e.g., a `THESIS SURVEY` block).

**Entry style — column-aligned fields, braced acronyms in booktitle, trailing commas** (`references.bib:10-17`):
```bibtex
@inproceedings{sultani2018ucfcrime,
  author    = {Waqas Sultani and Chen Chen and Mubarak Shah},
  title     = {Real-World Anomaly Detection in Surveillance Videos},
  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition ({CVPR})},
  pages     = {6479--6488},
  year      = {2018},
  doi       = {10.1109/CVPR.2018.00678},
}
```
Journal-article style (`references.bib:210-218`, `wang2024lightwvad`): `@article` with `journal`, `volume`, `pages`, `doi`. Accepted-but-arXiv-only style (`references.bib:220-226`, `majhi2025pivad`): `note = {arXiv:2505.13123}`. **Anti-pattern:** the `and others` author placeholders in `majhi2025pivad`/`yin2026dsanet` (lines 221, 229) must be REPLACED with full author lists (checklist #17) — do not copy that shortcut into new entries. No TODO comments may survive.

---

### `thesis/.latexmkrc`

**Analog:** `paper/.latexmkrc` (19 lines, copy nearly verbatim; update the header comment to reference the thesis):
```perl
$pdf_mode = 1;
$bibtex_use = 2;
$pdflatex = 'pdflatex -interaction=nonstopmode -synctex=1 --enable-installer %O %S';
$bibtex   = 'bibtex --enable-installer %O %S';
@default_files = ('main.tex');
```
Keep the `--enable-installer` flags — they are the working MiKTeX on-demand-install mechanism (the `[MPM]AutoInstall` preference is not honored reliably; documented at `paper/.latexmkrc:13-14`).

---

### `scripts/build_thesis.ps1`

**Analog:** `scripts/build_paper.ps1` (118 lines). COPY these blocks, retargeted `$paperDir` → `thesis/`:

**Param + repo-path anatomy** (`build_paper.ps1:20-31`), adding `[switch]$Open`:
```powershell
[CmdletBinding()]
param(
    [switch]$Clean
)
$ErrorActionPreference = 'Continue'
$scriptDir = $PSScriptRoot
$repoRoot  = Split-Path $scriptDir -Parent
$paperDir  = Join-Path $repoRoot 'paper'
$mainTex   = Join-Path $paperDir 'main.tex'
```

**Find-Exe probe** (`build_paper.ps1:38-49`):
```powershell
function Find-Exe {
    param([Parameter(Mandatory)][string]$Name, [string[]]$ProbeDirs)
    foreach ($d in $ProbeDirs) {
        if ($d) {
            $p = Join-Path $d $Name
            if (Test-Path $p) { return $p }
        }
    }
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}
```

**latexmk probe + PATH injection for child processes** (`build_paper.ps1:51-65`):
```powershell
$miktexBin = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64'
$latexmk = Find-Exe -Name 'latexmk.exe' -ProbeDirs @($miktexBin)
...
$latexmkDir = Split-Path $latexmk -Parent
if (($env:PATH -split ';') -notcontains $latexmkDir) { $env:PATH = "$latexmkDir;$env:PATH" }
```
Plus the Strawberry Perl probe (`build_paper.ps1:67-81`, probe `C:\Strawberry\perl\bin`).

**Push-Location build + -Clean + exit code** (`build_paper.ps1:87-100`):
```powershell
$code = 0
Push-Location $paperDir
try {
    if ($Clean) {
        & $latexmk -C main.tex | Out-Host
    }
    & $latexmk -pdf main.tex | Out-Host
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
```

**EXCLUDE** (`build_paper.ps1:111`): `Invoke-Item $pdf` — the thesis script is non-interactive by default; gate it behind `if ($Open) { Invoke-Item $pdf }`.

**NEW (no analog — spec §2/§8, 13-RESEARCH.md §7 lines 441-442):**
1. Preflight before build: HARD-assert `thesis/IEEEtranN.bst` exists (fail with clear message); REPORT-only `kpsewhich <pkg>.sty` loop over the required-package list (absence is NOT an error).
2. Post-build log scan: nonzero exit if `thesis/main.log` contains `There were undefined references`, `Citation .* undefined`, `Reference .* undefined`, or `!` LaTeX errors. Follow the existing message prefix convention `[build_thesis] ...` (cf. `[build_paper]` at lines 83-84, 105, 109).

---

### New figure/table generator scripts (Wave 0; corruption heatmaps, 20×4 severity heatmap, per-category tables, optional TENT/SAR rollup CSV)

Three analogs compose the pattern:

**A. Provenance-first docstring + determinism + path anatomy** — `scripts/pri5_tta_breakdown.py:1-38`. Every new generator MUST open with a data-provenance docstring naming exact tracked inputs, and be CPU-only:
```python
#!/usr/bin/env python
"""Pri 5: per-corruption-type disc-reweight breakdown table + heatmap.
...
CPU-only. numpy / json / csv only. NO torch / CUDA. Fixed RNG seed ...
Data sources (read-only):
  results/_coral_derisk/r1full_{clip,base,so400m,giant}.json
      -> SEED-42 CANONICAL per-condition disc-reweight (R1) deltas ...
"""
_RNG = np.random.default_rng(12345)  # seeded for policy compliance
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "_analysis_2026-06-10")
os.makedirs(OUT, exist_ok=True)
```
Also copy its self-check habit (`pri5_tta_breakdown.py:94-96`): recompute and `assert` against stored summary values so stale data fails loudly.

**B. LaTeX table emission with provenance comment header** — `scripts/pri5_tta_breakdown.py:184-205` (this is what produced the paper's `tab:tta_breakdown`; per-category table script should emit the same shape):
```python
with open(tex_path, "w", encoding="utf-8") as f:
    f.write("% Pri 5: per-corruption-type disc-reweight breakdown (3-seed mean delta AUC, points)\n")
    f.write("% Generated by scripts/pri5_tta_breakdown.py (CPU-only). Read-only on data.\n")
    f.write("% s42 component = results/_coral_derisk/r1full_*.json (canonical);\n")
    f.write("\\begin{table}[t]\n\\centering\n")
    f.write("\\caption{...}\n")
    f.write("\\label{tab:tta_breakdown}\n")
    f.write("\\begin{tabular}{lrrrr}\n\\toprule\n")
    ...
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
```
CSV emission pattern with labeled aggregation rows (`pri5_tta_breakdown.py:164-179`) — note the explicit `mean(s42)` vs `mean(3seed)` row labels that keep Pri-5 aggregations distinct (Pitfall 6).

**C. results-index.csv reading + 3-seed averaging + run-name parsing** — `scripts/generate_phase10_charts.py:87-109`. The `backbone` column in results-index.csv is EMPTY (Pitfall 12); backbone is encoded in the run_name suffix. Reuse `_seed_mean` verbatim — it exists because single-seed chart bugs already happened once (review C7-2):
```python
def load_results() -> pd.DataFrame:
    csv_path = PROJECT_ROOT / "results" / "results-index.csv"
    return pd.read_csv(csv_path)

def _seed_mean(idx, s42_name, metric):
    """Mean of ``metric`` over the 3-seed family ({_s42,_s123,_s2024}) ..."""
    if not isinstance(s42_name, str) or not s42_name.endswith("_s42"):
        return idx.loc[s42_name, metric] if s42_name in idx.index else np.nan
    base = s42_name[:-4]
    vals = [idx.loc[n, metric]
            for n in (f"{base}_s42", f"{base}_s123", f"{base}_s2024")
            if n in idx.index]
    vals = [v for v in vals if pd.notna(v)]
    return float(np.mean(vals)) if vals else np.nan
```
Run-name grids for the 128 canonical dirs: `COMPARISON_MAP`/`SEED_MAP` at `generate_phase10_charts.py:59-84` (backbone token ∈ {'', `_siglip2`, `_so400m`, `_giant`} BEFORE the pooling token; seeds `_s{42,123,2024}`).

**D. Publication figure style (300 DPI, serif)** — `scripts/generate_pub_figures.py:23-25, 34-44, 78-102`:
```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PUB_DPI = 300
def _setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
        "figure.dpi": PUB_DPI,
        "savefig.dpi": PUB_DPI,
        "axes.grid": True, "grid.alpha": 0.3,
        "pdf.fonttype": 42,      # TrueType fonts in PDF
        "ps.fonttype": 42,
    })
```
Save pattern (`generate_pub_figures.py:218`): `fig.savefig(out_path, bbox_inches="tight", pad_inches=0.02)`. Grayscale-friendly palette + hatching per backbone: `BACKBONE_STYLES` dict at lines 47-52. For thesis A4 one-column figures, size to ~6.3in text width instead of ACM's 3.33/7.0in constants (lines 35-36).

**Anti-patterns:** do NOT extend `scripts/generate_latex_tables.py`'s Table-3 path (stale, never updated for disc_reweight — Pitfall 1). If regenerating sweep charts via `scripts/generate_phase7_charts.py`, its hardcoded historical baselines (lines 55-56: 0.7192/0.8227; S03 text lines 266/295; Delta columns 268/283/297) may appear ONLY as labeled historical baselines — exclude Delta columns from thesis tables or label "vs historical 2026-05 sweep configuration" (Pitfall 3).

---

### `thesis/PROVENANCE.md`

**Analog (partial):** `12-VERIFICATION.md:41-54` — the number-traceability table is the closest existing format; extend it from "number → research artifact" to "number family / figure / table → git-tracked source + class":
```markdown
### Traceability table — paper (`main.tex`) cited numbers

| Number | Where cited | Method | Matches VERIFIED value in 12-RESEARCH-sota.md | RE-VERIFY-flagged? |
|--------|-------------|--------|-----------------------------------------------|--------------------|
| 90.33 / 85.37 | `tab:comparison` (l.394) | PI-VAD | YES — §1 row + §8 (I3D, 90.33/85.37) | N/A (verified, not conflicting) |
| **82.5** / **78.7** | `tab:comparison` (l.402) | **This work** | Project anchors (Tables 1–2: ...) | N/A (own result) |
```
Adaptations required by spec §7a: every source column entry must be a git-tracked path (assert `git ls-files --error-unmatch`); every figure row carries Class R (regen command: tracked script + tracked data) or Class V (verification note: what checked against, when). Model for a Class-V note: the pri5 markdown "Data provenance" section (`scripts/pri5_tta_breakdown.py:216-224` writes it) and the figure worksheet rows in 13-RESEARCH.md §4. Missing-on-disk paths (`results/phase7_charts/` etc., Pitfall 13) must never appear as sources.

---

### `thesis/frontmatter/*` (titlepage, abstract, toc, notation)

**No direct analog** — the paper's acmart `\title`/`\author`/`\affiliation` block (`paper/main.tex:32-46`) supplies the facts (title, Wei-Han Jeng, NTUST; advisor Chuan-Kai Yang from CONTEXT.md) but not the form. Use 13-RESEARCH.md §7 report-class recipe: `\begin{titlepage}...\end{titlepage}`, `\chapter*{Abstract}` + `\addcontentsline{toc}{chapter}{Abstract}`, `\tableofcontents`, `\listoffigures`, `\listoftables`, notation table (contents = Claude's discretion). Abstract content: restructure `paper/main.tex:51-53` (fixes T5-2 density) — keep every honesty framing (no-SOTA disclosure, "points" not "%", "small but consistent").

---

### `.gitignore` (edit)

**Analog:** existing `.gitignore:46-57` — the paper artifact block; mirror it for thesis/:
```gitignore
# LaTeX build artifacts (paper/) — global *.log rule above already covers main.log
paper/main.pdf
paper/sota_comparison_full.pdf
paper/*.aux
paper/*.bbl
paper/*.blg
paper/*.out
paper/*.fls
paper/*.fdb_latexmk
paper/*.toc
paper/*.synctex.gz
paper/*.cut
```
Thesis block adds `thesis/*.lof`, `thesis/*.lot` (report class emits them; paper had none). Comment-block style: `# Section name` header per group (lines 1, 5, 8, 12, ...). **Wave-0 results/ rewrite** (spec §7a, 13-RESEARCH.md §3): line 9 `results/` must become `results/*` + `!results/<subdir>/` + `!results/<subdir>/**` rules (a bare `!results/foo` under a dir-level exclude is DEAD), or use `git add -f` per file (existing practice for the current 28). Either way assert each of the ~269 files with `git ls-files --error-unmatch`.

---

### `thesis/IEEEtranN.bst` (vendored)

**No repo analog** — copy `C:/Users/Austin/AppData/Local/Programs/MiKTeX/bibtex/bst/feupphdteses/IEEEtranN.bst` (authentic Michael Shell header, v1.13 2008/09/30) into `thesis/`; BibTeX prefers CWD so the vendored copy wins when latexmk runs in `thesis/`. Record provenance in PROVENANCE.md exactly as worded in 13-RESEARCH.md §7 line 415.

## Shared Patterns

### Number provenance comments (apply to every thesis table/figure and every generator)
**Source:** `paper/main.tex:337-339` (comment block above `tab:tta_breakdown`):
```latex
% Pri-5 (REVIEW-2026-06-10): per-corruption-type breakdown of the disc_reweight gain.
% 3-seed mean dAUC averaged over the 5 severities per family.
% Source: scripts/pri5_tta_breakdown.py (r1full_*.json s42 + variants/v_*_s{123,2024}).
```
Every number-bearing table in thesis/ gets an equivalent `% Source:` comment naming the tracked generator + data, mirrored by a PROVENANCE.md row.

### Honesty framing (apply to abstract, Ch 1, Ch 5-7, Ch 9)
**Source:** `paper/main.tex:52` (abstract) and `main.tex:335` (TTA findings prose). Locked phrasings: gains in "points" not "%"; "up to $+13.2$ points in the single most-degraded condition"; "small but consistent" complementarity (6/8 strictly positive + 2 ties, p≈0.03 — NOT the 8/8 p≈0.008 variant, Pitfall 11); "these numbers trail the field's fine-tuned and text-aligned leaders (~88-91%)"; transductive-TTA disclosure. Never silently promote GF 2-Person cells (82.6/79.2) over the Gated-default headline (Pitfall 10).

### Canonical anchors only (apply to all chapters/appendices)
Numbers come exclusively from the anchor table in 13-RESEARCH.md §2 / spec §7. Forbidden: `paper/tables_generated.tex`, Phase 8-11 summaries, REQUIREMENTS.md EVAL rows, old C-series heatmaps, Phase-4-era per-category values (regenerate from canonical run dirs' `per_category.csv`, 3-seed mean±std).

### Message-prefix + exit-code discipline (PowerShell tooling)
**Source:** `scripts/build_paper.ps1:83-84, 102-117` — `Write-Output "[build_paper] ..."` prefix on every line, `Write-Error` + `exit 1` on missing prerequisites, propagate `$LASTEXITCODE`.

### CPU-only determinism (all new generators)
**Source:** `scripts/pri5_tta_breakdown.py:9-10, 31-32` — "CPU-only. numpy / json / csv only. NO torch / CUDA." + fixed RNG seed even when unused. `matplotlib.use("Agg")` before pyplot import (`generate_phase10_charts.py:24-26`).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `thesis/frontmatter/*` | LaTeX frontmatter | document build | No report-class document exists in repo; use 13-RESEARCH.md §7 report-class recipe + paper title-block facts |
| `thesis/IEEEtranN.bst` | bib style | document build | Vendoring operation, not authored code; copy from local MiKTeX path with provenance note |
| build_thesis.ps1 preflight + log scan | build script additions | request-response | build_paper.ps1 has NO log scan; requirements fully specified in 13-RESEARCH.md §7 items 2-3 |

## Metadata

**Analog search scope:** `paper/` (main.tex, references.bib, sota_comparison_full.tex, .latexmkrc, figures/), `scripts/` (build_paper.ps1, pri5_tta_breakdown.py, generate_phase10_charts.py, generate_pub_figures.py), `.planning/phases/12-*/12-VERIFICATION.md`, `.gitignore`
**Files scanned:** 10 analogs read (targeted, non-overlapping ranges)
**Pattern extraction date:** 2026-07-05
