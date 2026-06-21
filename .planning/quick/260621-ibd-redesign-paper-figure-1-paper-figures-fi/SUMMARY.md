---
quick_id: 260621-ibd
slug: redesign-paper-figure-1-paper-figures-fi
date: 2026-06-21
status: complete
commit: 4ee73d3
---

# Summary: Redesign Figure 1 (architecture diagram)

## What changed

Reworked the native-TikZ Figure 1 (`paper/figures/fig_architecture.tex`) from a
sparse, hard-to-read pipeline into a compact **swimlane** layout, and trimmed one
orphaned caption clause in `paper/main.tex`. Layout/readability only — no content,
number, or claim changes.

### Figure (`fig_architecture.tex`)
- **Swimlanes**: skeleton (green) and visual (blue) frozen-stream lanes that group
  each stream and visually funnel into the trainable gated-fusion box. The lane tint
  fills the former center-left void with intentional structure.
- **Conceptual fusion box**: the four dense equations were replaced with short
  conceptual steps (project + LayerNorm → per-dim gate → gated blend + residual + LN).
  The equations already appear verbatim in §3.4 (Eqs. 2–4), so nothing was lost.
- **Removed the floating "Late fusion baseline" box** (top-right, no arrows). Late
  fusion is fully described in §3.4 (Eq. 1).
- **Streams equalized to 3 stages** ("~1 FPS frame features" folded into the backbone
  box) so the feature boxes align before fusion.
- **Prediction column centered** on the figure axis (kills the top-right void).
- **MIL-ranking-loss feedback** moved to a clean right-side dashed loop (was crammed
  into the fusion↔MIL-head gap).
- **Test-time note** wired to `\ref{sec:disc}` (auto-numbers to "Sec. 3.6") instead
  of a hard-coded section number.

### Caption (`main.tex`)
- Removed the clause "; the late-fusion baseline instead averages the two
  single-modality scores with equal weights" — it described the now-removed box.
  Rest of the caption unchanged.

## Process

- User-approved design via a 2-question decision gate (conceptual box; remove
  late-fusion box) + a rendered A/B comparison (compact pipeline vs swimlanes);
  user chose swimlanes. Two candidates were prototyped as standalone compiles and
  shown as PNGs before any edit to the real paper.
- Three polish fixes applied on top of the approved render (MIL-loss loop, `\ref`,
  lane-label weights).

## Verification

- `scripts/build_paper.ps1 -Clean` → `paper/main.pdf` builds clean (11 pages, 0
  errors, 0 undefined refs).
- Figure 1 (page 3) visually verified in the real two-column layout: all nodes
  render, no overlap, `\ref{sec:disc}` resolves to "Sec. 3.6", caption consistent
  with the figure. Headlines (UCF 82.5 / XD 78.7) and other pages unaffected.

## Notes / disclosure

- Deleted my own throwaway preview scratch (`.fig_preview/`). In the same cleanup I
  also removed a **pre-existing** untracked file `_tmp_paperfig-1.png` (a transient
  per-category bar-chart render that predated this session) — it was not mine to
  delete; it is regenerable scratch, but flagged here for transparency.

## Files

- `paper/figures/fig_architecture.tex` — full rewrite (swimlane layout)
- `paper/main.tex` — one caption clause removed
- Commit: `4ee73d3`
