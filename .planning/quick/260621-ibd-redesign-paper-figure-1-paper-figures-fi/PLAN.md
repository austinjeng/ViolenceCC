---
quick_id: 260621-ibd
slug: redesign-paper-figure-1-paper-figures-fi
date: 2026-06-21
status: in-progress
---

# Quick Task: Redesign Figure 1 (architecture diagram)

## Goal

Make Figure 1 reader-friendly and professional, eliminating wasted space. The
current native-TikZ figure (`paper/figures/fig_architecture.tex`) pushes the two
streams to the top/bottom extremes (large center-left void), floats a
disconnected "Late fusion baseline" box top-right, packs four dense equations
into the fusion box, and converges asymmetric-length streams into the fusion box.

## Approved design (swimlane layout — user-selected over a compact-pipeline variant)

Decisions confirmed with the user before implementation:
- **Fusion box → conceptual labels** (the three gated-fusion equations already
  appear verbatim in §3.4 eqs. 2–4, so figure equations are strictly redundant).
- **Late-fusion baseline box → removed** from the figure (late fusion is fully
  described in §3.4 with eq. 1; the floating box was dead clutter).
- **Swimlanes**: tinted skeleton (green) / visual (blue) frozen-stream lanes that
  group each stream and visually funnel into the trainable gated-fusion box.
- Streams equalized to 3 stages each (folded "~1 FPS frame features" into the
  backbone box) so feature boxes align before fusion.
- Prediction column (MIL head + anomaly score) centered on the figure axis,
  filling the former top-right void.

Polish fixes applied on top of the approved render:
1. Move the cramped "MIL ranking loss" feedback label out of the
   fusion↔MIL-head gap → clean right-side dashed loop on the prediction column.
2. Wire the test-time note to `\ref{sec:disc}` (auto-numbering) instead of a
   hard-coded "(Sec. 3.6)".
3. Lane-label weight fix ("Skeleton stream" bold, "(frozen)" regular).

## Tasks

1. Rewrite `paper/figures/fig_architecture.tex` to the approved swimlane layout
   (vector TikZ only; still `\input` inside `\resizebox{\textwidth}{!}{...}` of
   the `figure*` in `main.tex`). → verify: standalone compile renders all nodes,
   no overfull/overlap, labels legible at \textwidth.
2. Trim the orphaned late-fusion clause from the Figure 1 caption in
   `paper/main.tex` (the box it described is gone). → verify: caption no longer
   references a non-existent figure element; rest of caption unchanged.
3. Rebuild: `scripts/build_paper.ps1 -Clean`. → verify: `paper/main.pdf` builds
   with no errors; Figure 1 (page 3) shows the new swimlane layout; headline
   numbers/other pages unaffected.

## Out of scope

- No changes to any other figure, table, or body text beyond the one caption clause.
- No content/claim changes; this is a layout/readability revision only.
