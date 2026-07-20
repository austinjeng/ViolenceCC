---
quick_id: 260720-rce
slug: defense-deck-polish
date: 2026-07-20
status: complete
---

# Quick Task 260720-rce — Summary

**Applied 4 committee-visible LOW polish fixes to the defense deck
`outputs/thesis_defense_2026-07-21_zh-TW.pptx`. All verification gates PASS.
Zero experiment-number changes; paper/thesis figure pipeline untouched.**

## What changed (all on `outputs/thesis_defense_2026-07-21_zh-TW.pptx`)

| # | Slide | Before → After |
|---|-------|----------------|
| 1 | S15 figure legend | `SigLIP2 ViT-B/16` → `SigLIP2 Base` (re-rendered `ppt/media/image5.png`; 24 bar values unchanged) |
| 2 | S9 box 矩形 8 | `YOLOX-m 定位人物＋17 個關節` → `YOLOX-m 定位人物，RTMPose-m 估計 17 關節` |
| 3 | S6 box 矩形 23 | `以視覺流 solo…` → `以視覺串流 solo…` (only stray 視覺流 in deck) |
| 4 | S12 formula 矩形 29 | L_rank full-width `＋`(U+FF0B) → ASCII `+`(U+002B) |

## How

- Fix 1: monkeypatched `scripts.generate_pub_figures.BACKBONE_STYLES` label +
  redirected `OUT_DIR` to a scratch temp dir in-memory (committed script and
  `paper/figures/` **not modified** — confirmed via `git status`), rendered
  `fig_backbone_comparison()` → PDF, PyMuPDF PDF→PNG @400 DPI, LANCZOS-resized to
  the original 2062×646, swapped the `image5.png` part blob.
- Fixes 2–4: python-pptx run-level edits (all single-run paragraphs; formatting preserved).
- Edited + verified on a scratch COPY first; original backed up to
  `outputs/thesis_defense_2026-07-21_zh-TW.BACKUP-pre-polish-260720.pptx`; promoted
  only after all gates passed.

## Verification (final, on the promoted deck)

- 31 slides ✓ · timing 1340s / 24 slides ✓ (unchanged)
- Forbidden strings absent (incl. `視覺流`, `幀`, `優化器`, `83.0/79.9/71.8`) ✓
- Required present (incl. new `視覺串流`, `RTMPose-m 估計 17 關節`) ✓
- Exactly 3 text shapes changed, 0 added/removed ✓
- S12 no full-width `＋` ✓ · image5 = 2062×646 ✓ · file re-parses cleanly ✓
- Re-rendered legend visually confirmed = "SigLIP2 Base"; chart otherwise faithful ✓

## Notes / not-done

- Deck file + backup left **untracked** (project keeps `outputs/` untracked; no
  2.6 MB binary added to git). Deliverable lives in `outputs/`; backup enables rollback.
- Root cause of Fix 1 (`generate_pub_figures.py:49` label) left as-is — paper/thesis
  are submitted; a future paper/thesis figure rebuild would make them consistent if
  that line is corrected then. Out of scope for this deck-only task.
- Deferred review items (not requested): B7 Gaussian pose-drift (A′) backup, 498K<633K
  capacity one-liner, no-SOTA framing line, S9 "(Salt, 2010)" credit wording, S21/S23
  timing rehearsal. These are prep/optional — see this session's review report.
- **Recommend the author open the deck in PowerPoint once** and eyeball S6/S9/S12/S15.
