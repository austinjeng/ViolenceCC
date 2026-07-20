---
quick_id: 260720-rce
slug: defense-deck-polish
date: 2026-07-20
mode: quick
---

# Quick Task 260720-rce: Defense deck polish (fixes 1–4)

## Goal

Apply 4 pre-verified LOW-severity polish fixes to the oral-defense deck
`outputs/thesis_defense_2026-07-21_zh-TW.pptx` (defense 2026-07-21). Fixes were
surfaced by a 10-agent adversarial deck review this session (0 HIGH / 0 MEDIUM
survived verification; these 4 are committee-visible LOW items). **No experiment
number changes.** Deck-only — do NOT touch the paper/thesis figure pipeline.

## Tasks

1. **Fix 1 — S15 backbone-comparison figure legend.** Legend labeled backbone-2
   "SigLIP2 ViT-B/16"; all deck text + thesis call it "SigLIP2 Base". Root cause
   = `scripts/generate_pub_figures.py:49` label. Render the figure with the label
   patched **in-memory** (monkeypatch `BACKBONE_STYLES`, redirect `OUT_DIR` to a
   temp dir — committed script and `paper/figures/` untouched), PDF→PNG at 400 DPI,
   resize to the original 2062×646, swap into `ppt/media/image5.png`. All 24 bar
   values already match ch05 tables — legend label only.
   - verify: rendered legend reads "SigLIP2 Base"; chart otherwise pixel-faithful; image dims 2062×646.
2. **Fix 2 — S9 box (矩形 8).** `YOLOX-m 定位人物＋17 個關節` → `YOLOX-m 定位人物，RTMPose-m 估計 17 關節` (RTMPose-m regresses the 17 keypoints, not YOLOX-m).
3. **Fix 3 — S6 contribution-4 box (矩形 23).** Only stray `視覺流` in the deck → `視覺串流` (deck standard; matches this slide's own notes).
4. **Fix 4 — S12 formula (矩形 29).** L_rank full-width `＋` (U+FF0B) → ASCII `+` (U+002B); the `−` on the same line is a math minus (U+2212).

## Method / constraints

- Edit via python-pptx in `vcc-main` (call `C:/Anaconda/envs/vcc-main/python.exe`
  directly; `conda run` wrapper chokes on unicode stdout → write output to files).
- All 3 text targets are single-run paragraphs → edit `run.text` directly, format preserved.
- Edit + verify on a COPY first; back up the original; promote only after all gates pass.

## Verification gates (all must pass)

- 31 slides; timing sum 1340s / 24 slides (unchanged).
- Forbidden absent (incl. now `視覺流`, `幀`, `優化器`, `83.0`, `79.9`, `71.8`).
- Required present (incl. new `視覺串流`, `RTMPose-m 估計 17 關節`).
- Exactly 3 text shapes changed vs the original snapshot; 0 shapes added/removed.
- S12 has no full-width `＋`; image5 = 2062×646; file re-parses cleanly.
