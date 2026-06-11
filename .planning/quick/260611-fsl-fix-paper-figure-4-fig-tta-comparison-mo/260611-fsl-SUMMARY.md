---
phase: quick-260611-fsl
plan: 01
subsystem: paper-figures
tags: [paper, matplotlib, figure-4, tta, legend]
requires: []
provides:
  - "fig_tta_comparison.pdf with non-overlapping upper-center 2-column legend"
affects: [paper]
tech-stack:
  added: []
  patterns: ["targeted single-figure regeneration (avoid stale-CSV figures)"]
key-files:
  created: []
  modified:
    - scripts/generate_pub_figures.py
    - paper/figures/fig_tta_comparison.pdf
decisions:
  - "Legend moved to loc='upper center', ncol=2 with columnspacing=1.0, handletextpad=0.5 — primary plan option worked first try; no ylim or bbox_to_anchor fallback needed"
metrics:
  duration: ~8min
  completed: 2026-06-11
---

# Quick Task 260611-fsl: Fix Paper Figure 4 (fig_tta_comparison) Legend Overlap Summary

**One-liner:** Moved Figure 4's legend from upper-left (where it covered the CLIP ViT-B/16 bar group and its 63.7/64.4/+0.67 labels) to a compact 2-column upper-center box over the empty center-top region; regenerated only that figure and rebuilt the paper clean (10pp).

## What Was Done

### Task 1: Legend relocation + targeted regeneration
- `scripts/generate_pub_figures.py` `fig_tta_comparison()` (line ~459): `ax.legend(loc="upper left", ...)` → `ax.legend(loc="upper center", ncol=2, framealpha=0.9, edgecolor="gray", columnspacing=1.0, handletextpad=0.5)`. No other function, data array, ylim, or style preset touched.
- Regenerated ONLY this figure via targeted invocation (`g._setup_style(); g.fig_tta_comparison()`) using `C:/Anaconda/envs/vcc-main/python.exe` (plain `python` lacks pandas). main() deliberately NOT run — fig_backbone_comparison reads the stale pre-lambda0 CSV and would have been corrupted.
- Isolation gate PASSED: `git status --porcelain paper/figures/` showed exactly one modified file (`fig_tta_comparison.pdf`); the other three figure PDFs byte-unchanged.

### Task 2: Visual verification + paper rebuild + commit
- Visual check (rendered PDF): legend sits in a 2-column box at top center, clear of all bars, error-bar caps, value labels, and red delta annotations. CLIP group's 63.7 / 64.4 / +0.67 fully visible; SO400M's +2.24 clear below the legend's bottom-right; no fallback (ylim raise / bbox_to_anchor) needed.
- Paper rebuilt per CLAUDE.md: `build_paper.ps1 -Clean` → main.pdf 10 pages, 0 errors, 0 undefined references in the final pass (the single "undefined references" warning was pdflatex run 1, pre-bibtex — expected). Page 8 of main.pdf confirms the corrected Figure 4 embedded and legible.
- Committed exactly the 2 source files (plain git fallback used for full commit-message control incl. Co-Authored-By trailer; no build artifacts staged).

## Commits

| Commit | Message | Files |
|--------|---------|-------|
| 2d45071 | fix(quick-260611-fsl): move Figure 4 legend off CLIP bar group | scripts/generate_pub_figures.py, paper/figures/fig_tta_comparison.pdf |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plain `python` lacks matplotlib/pandas**
- **Found during:** Task 1 (regeneration command from the plan failed with ModuleNotFoundError: pandas)
- **Fix:** Used the project's vcc-main env interpreter directly (`C:/Anaconda/envs/vcc-main/python.exe`), per the existing STATE.md decision about direct exe paths on Windows
- **Files modified:** none (invocation only)
- **Commit:** n/a

Otherwise the plan executed exactly as written; the primary legend placement (upper center, ncol=2) worked on the first try with no fallback needed.

## Notes / Known Pre-existing Issues (not in scope)

- SigLIP2 Giant's "63.3" value label has the thin error-bar whisker passing near/through it — pre-existing in the original figure (label placed at o+0.25 while yerr=0.58 extends past it), unaffected by legend placement, still legible. Left untouched per surgical-change constraint.
- Regenerated PDF grew 19,451 → 38,584 bytes (matplotlib font-embedding difference vs the originally committed render); visual output verified correct.
- fig_backbone_comparison regeneration remains a tracked FOLLOW-UP (stale backbone_comparison_4way.csv) — deliberately NOT touched here.

## Known Stubs

None.

## Threat Flags

None — local figure generation from hardcoded in-repo data; T-q260611fsl-01 mitigation (targeted regeneration + git-status isolation gate) applied and verified.

## Verification Against Must-Haves

- [x] Figure 4 legend does not overlap any bar, error bar, or value annotation (visual render checked)
- [x] CLIP ViT-B/16 annotations (63.7, 64.4, +0.67) fully visible
- [x] paper/main.pdf rebuilds clean (10 pages, 0 errors, 0 undefined refs final pass)
- [x] Other three figure PDFs byte-unchanged (git-status isolation gate)
- [x] scripts/generate_pub_figures.py contains "upper center" in fig_tta_comparison() only
- [x] Commit contains exactly the 2 tracked files; no build artifacts staged

## Self-Check: PASSED

- scripts/generate_pub_figures.py: FOUND
- paper/figures/fig_tta_comparison.pdf: FOUND
- Commit 2d45071: FOUND (2 files, 2 insertions / 1 deletion in the .py — confined to fig_tta_comparison())
- "upper center" present in fig_tta_comparison() (other 2 occurrences in the file are pre-existing in other figure functions)
