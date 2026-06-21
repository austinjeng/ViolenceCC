---
quick_id: 260621-fjk
type: quick
date: 2026-06-21
files_modified:
  - paper/main.tex
  - paper/sota_comparison_full.tex
must_haves:
  truths:
    - "The CLIP-TSA 'temporal-modeling not feature-quality gap' claim is stated as an explicit, unproven hypothesis ('we attribute/hypothesize ... but do not isolate this experimentally') in all 3 locations (main.tex Limitations, fragment fair-subset read, fragment P2)"
    - "The competitiveness claim is scoped honestly: the prose states that on UCF-Crime the work trails the modern fair-subset peers (RTFM/Light-WVAD/MGFN/UR-DMU/CLIP-TSA) and that competitiveness is clearest on XD-Violence AP"
    - "The abstract carries one sentence of SOTA context (field ceiling ~88-91% UCF AUC; gap follows from the frozen/no-text design; contribution is the reproducible single-GPU pipeline + robustness study, not a peak score)"
    - "The fragment positioning leads with the orthogonal contribution (P3 moved ahead of the fair-subset paragraph; opener states the orthogonal claim is central, competitiveness is supporting/XD-specific)"
    - "Paper rebuilds clean: build_paper.ps1 -Clean exit 0, ~11 pages, 0 undefined citations; existing Tables 1-3 and all headline numbers (82.5/78.7/68.8/40.8/81.2/74.6/82.4/76.8) byte-identical"
    - "Zero overclaim language introduced; no number changed anywhere"
  artifacts:
    - path: "paper/main.tex"
      provides: "Abstract SOTA-context sentence (#3); XD-scoped competitiveness + honest-hypothesis CLIP-TSA rewrite in Limitations (#1/#2)"
    - path: "paper/sota_comparison_full.tex"
      provides: "Honest-hypothesis CLIP-TSA rewrite in fair-subset read + P2 (#1); XD-scoped P2 (#2); orthogonal-contribution-led positioning (#6)"
---

<objective>
Apply the four framing fixes recommended by the Phase 12 SOTA-comparison honesty
assessment, so the paper's now-explicit SOTA comparison reads as honest and the
defense has no unfalsified-assertion / metric-cherry-pick seams. Writing task:
"tests" = clean LaTeX build + grep assertions, NOT unit tests. No numbers change.
</objective>

<fix_map>
- #1 (honest-hypothesis CLIP-TSA): downgrade "the gap is a temporal-modeling/aggregation gap, not a feature-quality gap" from an asserted fact to an explicit hypothesis ("we attribute/hypothesize ... but do not isolate this experimentally; leave a controlled ablation to future work") in main.tex Limitations (~l.385), fragment fair-subset read (~l.215), fragment P2 (~l.251).
- #2 (XD-scoped competitiveness): make explicit that on UCF-Crime the work trails the modern fair-subset peers (RTFM 84.30, Light-WVAD 84.7, UR-DMU 86.97, MGFN 86.98, CLIP-TSA 87.58) and that within-regime competitiveness is clearest on XD-Violence AP; remove "competitive, not an outlier" two-metric implication.
- #3 (abstract SOTA context): one sentence after the results sentence naming the ~88-91% field ceiling and framing the gap as design + the contribution as reproducible single-GPU pipeline + robustness.
- #6 (rebalance): fragment positioning leads with the orthogonal-contribution paragraph (move P3 ahead of the fair-subset paragraph; opener states orthogonal claim is central, competitiveness is supporting evidence). Tighten, do not delete.
</fix_map>

<verification>
- grep main.tex/sota_comparison_full.tex for "do not isolate this experimentally" (>=2 hits across files); "hypothesize"/"attribute" present near each CLIP-TSA mention.
- grep abstract for the SOTA-context sentence ("88--91" present).
- build_paper.ps1 -Clean exit 0; main.log: "Output written on main.pdf (N pages" with N ~= 11; 0 "Citation/Reference ... undefined".
- headline anchors all present and unchanged; no number altered (diff is prose-only).
- overclaim grep: no new disallowed tokens in edited prose.
</verification>
