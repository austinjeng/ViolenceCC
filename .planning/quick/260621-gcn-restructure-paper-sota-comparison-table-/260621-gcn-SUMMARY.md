---
quick_id: 260621-gcn
type: quick
date: 2026-06-21
status: complete
files_modified:
  - paper/main.tex
  - paper/references.bib
---

# Quick Task 260621-gcn: Restructure paper SOTA comparison (honest favorable framing)

Restructured the paper's `tab:comparison` so the comparison reads more favorably **without
dropping any method by outcome** — the favorable angle comes from regime-grouping + XD-AP/efficiency
emphasis, not from hiding rows. Independently adversarially audited (verdict below). **No number changed.**

## What changed (paper only — fragment left as-is)

**Regime-grouped table.** `tab:comparison` is now two `\midrule`-separated blocks with
`\multicolumn` headers, rows sorted by UCF AUC within each:
- **Heavier-budget regimes** (text alignment / aux modalities / MLLM): PI-VAD, DSANet, VadCLIP,
  + EventVAD, LAVAD (new).
- **Comparable regime** (frozen, no-text, visual/RGB+skeleton, single-GPU head): CLIP-TSA, MGFN,
  UR-DMU, Light-WVAD, RTFM, **This work (82.5/78.7, bold)**, Sultani.
Grouping removes the direct "82.5 next to 90.33" juxtaposition; This-work sits among its true peers.
It is honestly 6th of 7 in its block on UCF (above only Sultani) — the favorable lever is the
XD-AP-led prose, not the sort.

**Stated inclusion rule (caption).** "We list the strongest published methods on each benchmark
together with the established frozen-feature, no-text peers, so the selection is not restricted to
favorable comparisons." Outcome-neutral; the six leaders that beat This-work (VadCLIP/CLIP-TSA/
DSANet/PI-VAD/UR-DMU/MGFN) all remain.

**EventVAD + LAVAD efficiency rows (new).** Added to the heavier block (training-free 7B/13B MLLM on
80GB-class hardware) with new `references.bib` entries (`shao2025eventvad`, `zanella2024lavad`) and
`% RE-VERIFY` comments on their XD-AP cells (64.04 / 62.01 are AP, not their 87.51 / 85.36 ROC-AUC).
§6 prose folds in the efficiency point: a single 24GB GPU reaches 82.5% UCF — at or above these
two — and 78.7% XD AP vs their 64.04 / 62.01.

**§6 prose rewrite.** States the inclusion rule, leads with comparable-regime XD-AP parity, keeps the
honest "trails the other frozen-feature methods on UCF" concession + the CLIP-TSA "we do not isolate
this experimentally" hypothesis, and adds the efficiency comparison.

**GS-MoE disclosure (from the adversarial audit).** The audit found one seam: GS-MoE (91.58/82.89,
ICCV 2025), a colorably no-text frozen-feature method above This-work, was silently absent while two
below-us MLLM methods were included. Closed it with a `\footnotesize` disclosure note + `\cite`
(`damicantonio2025gsmoe`) stating the outcome-neutral exclusion reasons (primary-source numbers
unverifiable; trained per-category MoE head exceeds the single-GPU-class regime). Converts a silent
omission into a disclosed exclusion.

## Adversarial honesty audit (independent agent)

Verdict: **HONEST AND DEFENSIBLE** after the GS-MoE disclosure (pre-disclosure: "honest but one weak seam").
- Number traceability: PASS — all 12 cells trace verbatim to 12-RESEARCH-sota.md §1/§8; AP-vs-AUC and
  MGFN-I3D/CLIP-TSA-primary traps correctly navigated.
- Regime categorization: PASS — every method in its budget-correct block; CLIP-TSA (the strongest
  no-text method, which beats us) correctly kept in the comparable block, not hidden upward.
- Outcome-based selection: PASS — no strong method dropped; the six leaders that beat us are retained;
  EventVAD/LAVAD justified by the compute-honesty argument, not as padding; sort honest.
- Prose vs table: PASS — UCF deficit explicitly conceded; XD parity not bled into UCF; zero overclaim.

## Verification

- `build_paper.ps1 -Clean`: exit 0, **11 pages** (GS-MoE note tipped it to 12; restored via
  `\footnotesize` on the comparison table), 0 undefined citations, 0 fatal errors.
- 3 new bib keys resolve (`shao2025eventvad`, `zanella2024lavad`, `damicantonio2025gsmoe`), each once.
- Headline anchors 82.5 / 78.7 / 68.8 / 40.8 / 81.2 / 74.6 / 82.4 / 76.8 present and unchanged; no
  number altered; existing Tables 1-2 untouched. Earlier framing fixes (abstract context, XD-scoping,
  fragment rebalance) intact.

## Camera-ready re-verify note

Three numbers newly cited in the paper that the student must re-check before submission (all already on
the 12-VERIFICATION.md re-verify list, now cited rather than full-table-only): EventVAD XD 64.04 (AP),
LAVAD XD 62.01 (AP), GS-MoE 91.58/82.89 (MEDIUM-confidence preprint). The three new bib entries are
preprint-typed (arXiv note) and should be confirmed/updated to final venues like PI-VAD/DSANet (re-verify
items 16-17).

## Self-Check: PASSED
