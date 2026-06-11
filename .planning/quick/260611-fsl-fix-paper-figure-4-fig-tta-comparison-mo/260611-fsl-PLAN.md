---
phase: quick-260611-fsl
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/generate_pub_figures.py
  - paper/figures/fig_tta_comparison.pdf
autonomous: true
requirements: [QUICK-260611-FSL]

must_haves:
  truths:
    - "Figure 4 legend does not overlap any bar, error bar, or value annotation"
    - "CLIP ViT-B/16 annotations (63.7, 64.4, +0.67) are fully visible"
    - "paper/main.pdf rebuilds clean (10 pages, 0 errors) with the corrected figure"
    - "The other three figure PDFs (fig_temporal_scores, fig_backbone_comparison, fig_gating_distribution) are byte-unchanged"
  artifacts:
    - path: "scripts/generate_pub_figures.py"
      provides: "fig_tta_comparison() with non-overlapping legend placement"
      contains: "upper center"
    - path: "paper/figures/fig_tta_comparison.pdf"
      provides: "Regenerated paper-ready Figure 4"
  key_links:
    - from: "scripts/generate_pub_figures.py"
      to: "paper/figures/fig_tta_comparison.pdf"
      via: "fig_tta_comparison() savefig"
      pattern: "fig_tta_comparison\\.pdf"
    - from: "paper/main.tex"
      to: "figures/fig_tta_comparison.pdf"
      via: "includegraphics in Figure 4 environment"
      pattern: "fig_tta_comparison"
---

<objective>
Fix paper Figure 4 (fig_tta_comparison.pdf): the legend at loc="upper left" overlaps the CLIP ViT-B/16 bar group (tallest, ~64.4 with ylim 54-67) and hides its value labels (63.7, 64.4, +0.67). Move the legend to a compact horizontal placement over the empty center-top region, regenerate ONLY this figure, and rebuild the paper PDF.

Purpose: Figure 4 is paper-ready for CGW '26 submission — no hidden data labels.
Output: Updated scripts/generate_pub_figures.py + regenerated paper/figures/fig_tta_comparison.pdf, committed; paper/main.pdf rebuilt locally (git-ignored, NOT committed).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md  (section "Paper / LaTeX Build" — mandatory rebuild command after figure edits)
@scripts/generate_pub_figures.py  (fig_tta_comparison() at lines 421-467; legend at line 459)

CRITICAL CONSTRAINT — do NOT run the full script / main():
fig_backbone_comparison() (lines ~231-235) reads results/phase10_charts/backbone_comparison_4way.csv, which STATE.md flags as STALE (pre-lambda0) — regenerating that figure would corrupt it (known FOLLOW-UP item). fig_gating_distribution() and fig_temporal_scores() also read from results/ data files. Only fig_tta_comparison() uses hardcoded data. Regenerate ONLY fig_tta_comparison via a targeted single-function invocation.

Geometry facts (from orchestrator diagnosis, verified against source):
- 4 bar groups at x=0..3, bar tops 57.01-64.38, ylim (54, 67), figsize (3.33, 2.0)
- Annotations extend to ~66.1 above CLIP group (x=0) and ~65.0 above Giant (x=3)
- Center-top region (between SigLIP2 Base at x=1, tops ~60.2, and SO400M at x=2, tops ~62.8) has the most headroom
</context>

<tasks>

<task type="auto">
  <name>Task 1: Move legend to upper center and regenerate only fig_tta_comparison.pdf</name>
  <files>scripts/generate_pub_figures.py, paper/figures/fig_tta_comparison.pdf</files>
  <action>
    In scripts/generate_pub_figures.py, inside fig_tta_comparison() only (line 459), replace `ax.legend(loc="upper left", framealpha=0.9, edgecolor="gray")` with `ax.legend(loc="upper center", ncol=2, framealpha=0.9, edgecolor="gray", columnspacing=1.0, handletextpad=0.5)`. Touch nothing else — no changes to other figure functions, data arrays, ylim (yet), or style presets (surgical-change constraint).

    Regenerate ONLY this figure from the repo root (D:\ViolenceCC) with: `python -c "import sys; sys.path.insert(0, 'scripts'); import generate_pub_figures as g; g._setup_style(); g.fig_tta_comparison()"`. OUT_DIR is absolute (derived from __file__), so the PDF lands in paper/figures/ regardless of cwd. Do NOT run `python scripts/generate_pub_figures.py` (main() would regenerate fig_backbone_comparison from the stale CSV — see context constraint).

    Confirm isolation: `git status --porcelain paper/figures/` must list exactly one modified file, fig_tta_comparison.pdf.
  </action>
  <verify>
    <automated>python -c "import sys; sys.path.insert(0, 'scripts'); import generate_pub_figures as g; g._setup_style(); g.fig_tta_comparison()" exits 0 and prints "-> ...fig_tta_comparison.pdf"; then git status --porcelain paper/figures/ shows ONLY fig_tta_comparison.pdf modified</automated>
  </verify>
  <done>Legend call updated to upper-center 2-column; fig_tta_comparison.pdf regenerated; the other three figure PDFs byte-unchanged per git status.</done>
</task>

<task type="auto">
  <name>Task 2: Visually verify no overlap, rebuild paper, commit</name>
  <files>paper/figures/fig_tta_comparison.pdf, scripts/generate_pub_figures.py</files>
  <action>
    Visual check: Read paper/figures/fig_tta_comparison.pdf with the Read tool (PDFs render visually). Confirm the legend box does not touch any bar, error-bar cap, value label, or red delta annotation — especially "63.7", "64.4", "+0.67" above the CLIP ViT-B/16 group, and the SO400M annotations (top ~62.8) under the centered legend. If any overlap remains, apply the minimal fallback in this order and re-run the Task 1 regeneration command: (a) raise ylim upper bound from 67 to 68 in fig_tta_comparison() only; (b) if still overlapping, move the legend outside the axes with bbox_to_anchor=(0.5, 1.18) anchored to "upper center" plus ncol=2 (title may need to move or be kept — keep the change minimal). Re-verify visually after any fallback.

    Rebuild the paper per CLAUDE.md: `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean`. Confirm exit code 0 and a clean build (10 pages, 0 errors / 0 undefined refs, consistent with the current paper state). Read the page of paper/main.pdf containing Figure 4 (TTA comparison) to confirm the corrected figure is embedded and legible.

    Commit ONLY scripts/generate_pub_figures.py and paper/figures/fig_tta_comparison.pdf (paper/main.pdf and all LaTeX build artifacts are git-ignored — never commit them): `gsd-sdk query commit "fix(quick-260611-fsl): move Figure 4 legend off CLIP bar group" --files scripts/generate_pub_figures.py paper/figures/fig_tta_comparison.pdf` (fall back to plain git add of exactly those two paths + git commit if the SDK helper is unavailable).
  </action>
  <verify>
    <automated>powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean exits 0; git log -1 --stat shows the commit touching exactly scripts/generate_pub_figures.py and paper/figures/fig_tta_comparison.pdf</automated>
    <human-check>Rendered fig_tta_comparison.pdf shows the legend clear of all bars and annotations; 63.7 / 64.4 / +0.67 fully visible above the CLIP group</human-check>
  </verify>
  <done>Figure visually confirmed overlap-free; paper rebuilt clean with the corrected Figure 4; the two source files committed; no build artifacts committed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| none | Local figure generation from hardcoded in-repo data; no untrusted input, no network, no new packages |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-q260611fsl-01 | Tampering | paper/figures/*.pdf | mitigate | Targeted single-function regeneration + git-status isolation gate prevents stale-CSV corruption of fig_backbone_comparison.pdf |
</threat_model>

<verification>
- scripts/generate_pub_figures.py line ~459 uses loc="upper center" (or documented fallback), only within fig_tta_comparison()
- git diff shows changes confined to fig_tta_comparison() — no other figure function touched
- paper/figures/: only fig_tta_comparison.pdf modified
- Visual render: legend overlaps nothing; all 8 value labels + 4 delta annotations legible
- build_paper.ps1 -Clean succeeds; paper/main.pdf shows corrected Figure 4
- Commit contains exactly the 2 tracked files; no .pdf build artifacts staged
</verification>

<success_criteria>
- Figure 4 is paper-ready: legend in a non-overlapping position, CLIP group labels (63.7, 64.4, +0.67) fully visible
- Other three figure PDFs byte-identical to HEAD before this task
- Paper rebuilds clean (10pp, 0 errors); headlines untouched (no number changes anywhere)
- Changes committed with quick-task scoped message
</success_criteria>

<output>
Create `.planning/quick/260611-fsl-fix-paper-figure-4-fig-tta-comparison-mo/260611-fsl-SUMMARY.md` when done
</output>
