---
quick_id: 260621-fjk
type: quick
date: 2026-06-21
status: complete
files_modified:
  - paper/main.tex
  - paper/sota_comparison_full.tex
---

# Quick Task 260621-fjk: Phase 12 SOTA-comparison framing fixes

Applied the four framing fixes from the SOTA-comparison honesty assessment so the
now-explicit comparison reads as honest and the viva defense has no
unfalsified-assertion / metric-cherry-pick seams. **Writing task — no number changed
anywhere; the numeric diff is empty.**

## What changed

**#3 — Abstract SOTA context (`main.tex` abstract).** Added one sentence after the
results sentence: the field's fine-tuned/text-aligned leaders reach ~88–91% UCF AUC,
the gap follows from the deliberately frozen/no-text design, and the contribution is
the reproducible single-GPU pipeline + label-free robustness study, not a peak score.
Abstract-first readers are now warned of the ceiling instead of meeting it only in §6.

**#1 — Honest-hypothesis CLIP-TSA rewrite (3 locations).** Downgraded the asserted
"the gap is a temporal-modeling/aggregation gap, not a feature-quality gap" to an
explicit hypothesis with "we attribute/hypothesize … but we do not isolate this
experimentally" (and, in the paper, "leave a controlled ablation to future work"):
`main.tex` Limitations, fragment fair-subset read, fragment P2. This was the #1 viva
vulnerability (a same-regime 5-point loss explained by an unproven claim).

**#2 — XD-scoped competitiveness (`main.tex` Limitations + fragment P2).** Made
explicit that on UCF-Crime the work trails *every* modern fair-subset peer (RTFM 84.30,
Light-WVAD 84.7, UR-DMU 86.97, MGFN 86.98, CLIP-TSA 87.58) and that within-regime
competitiveness is clearest on XD-Violence AP, weakest on UCF AUC. Removed the
two-metric "competitive, not an outlier" implication → "a reasonable mid-pack entry on
XD-Violence rather than an outlier."

**#6 — Stance rebalance (fragment positioning).** Positioning section now opens with a
sentence stating the orthogonal contribution is the *central* claim and competitiveness
is supporting/XD-specific; physically moved the orthogonal-contribution paragraph (P3)
ahead of the fair-subset/competitiveness paragraph so the lead is the contribution, not
the leaderboard defense. Tightened, did not delete.

## Verification

- `build_paper.ps1 -Clean`: exit 0, **11 pages**, 0 "Citation/Reference … undefined", 0 fatal `! ` errors.
- Standalone fragment `sota_comparison_full.tex` recompiles: exit 0, 1-page PDF, 0 fatal errors.
- Fix greps: `#1` "we hypothesize" ×2 in fragment + "do not isolate this experimentally" in main.tex; `#3` "88--91" ×1; `#2` "clearest on XD-Violence" present in both files; `#6` lead sentence present and the orthogonal paragraph (l.248) now precedes the competitiveness paragraph (l.268).
- Headline anchors 82.5 / 78.7 / 68.8 / 40.8 / 81.2 / 74.6 / 82.4 / 76.8 all present and unchanged.
- Numeric diff on `main.tex` is empty (no table cell or number changed); overclaim scan finds only pre-existing comment/label/explicit-negation hits — no new disallowed prose tokens.

These are framing-only edits; they do not touch the verified numbers, the headline
anchors, or existing Tables 1–3, so Phase 12's `12-VERIFICATION.md` PASS still holds.
The camera-ready re-verify checklist (items 1–17) is unaffected.

## Self-Check: PASSED
