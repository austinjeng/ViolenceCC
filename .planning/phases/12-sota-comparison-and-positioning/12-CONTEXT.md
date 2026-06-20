# Phase 12 — Context: SOTA Comparison and Positioning

**Created:** 2026-06-21 (via brainstorm + 40-agent verified-SOTA research workflow)
**Trigger:** Professor's thesis-review feedback — "the thesis lacks comparison with current SOTA." Despite a different method and computational budget, a real comparison is required; framed to acknowledge the gap without undermining the thesis's own claims.
**Mode:** writing / analysis — **zero GPU, no new training runs.**

---

## Scope decisions (locked via brainstorm, 2026-06-21)

| Decision | Choice | Rationale |
|---|---|---|
| **Depth** | Published-numbers table + positioning prose (NO GPU re-runs) | Single RTX 4090 cannot fairly reproduce fine-tuned/MLLM/audio SOTA; standard thesis practice is to cite published numbers with a settings column. The compute gap is itself part of the honest framing. |
| **Target** | Thesis (full treatment) **+** condensed table in the CGW '26 paper | Thesis has room; paper is at 10pp and page-limited → needs ~½ page reclaimed (the §2 number-backfill can absorb some). Page-budget call deferred to planning. |
| **Stance** | **Orthogonal contribution + fair-subset competitiveness** | Lead with the different contribution axis (skeleton+VL fusion + label-free reliability-routing TTA, not peak AUC); support with competitiveness inside the frozen / no-text / visual+skeleton / single-GPU subset. Strongest honest framing. |

## This work's anchors
UCF-Crime frame-AUC **82.5%** · XD-Violence AP **78.7%** · single-stream baselines: skeleton-only 68.8/40.8, visual-only CLIP 81.2/74.6, SigLIP2-Giant 82.4/76.8.

---

## Deliverables

**Thesis:**
1. Full SOTA comparison table (~20 methods, sorted by UCF AUC) with a mandatory **Setting column** (Frozen? / Text branch? / Audio? / frame-vs-video metric) and per-number footnotes for every caveated value; `This work` row included, never bare head-to-head.
2. Fair-subset table (CLIP-TSA, UR-DMU, MGFN-I3D, RTFM, Light-WVAD, Sultani, This work) — the apples-to-apples band where 78.7 XD is on par with RTFM/MGFN-I3D and 82.5 UCF beats Sultani by ~7pt.
3. Five positioning paragraphs: deliberate-constraint frame → fair-subset competitiveness → orthogonal contribution → reproducibility/transparency → "training-free ≠ low-compute."
4. §2 Related-Work backfill: quote benchmark numbers for already-cited methods (Sultani 75.41; RTFM 84.30/77.81; VadCLIP 88.02/84.51) — the precise reviewer gap.

**Paper (CGW '26):**
5. Condensed comparison table (fair-subset + a few top anchors, with the Setting column). **Page-budget checkpoint in planning:** reclaim ~½ page or fall back to a 3–4-row mini-table.

**Both:**
6. `references.bib` entries for the new methods cited; the verified-numbers artifact (`12-RESEARCH-sota.md`) is the source of record + the manual re-check list.

---

## Guardrails (must hold)

- Setting column on every comparison table; metric definitions stated once (UCF = frame ROC-AUC, XD = AP).
- **Never** compare a frozen-feature number head-to-head with fine-tuned / MLLM / audio rows without the caveat/Setting column.
- No "SOTA / comparable to SOTA / outperforms" language — the honest claim is competitiveness *within the constrained, frozen, visual-only regime*.
- TTA result scoped to **robustness** (corrupted-AUC), not clean headline AUC.
- Correct attribution of re-implemented baselines (e.g. Sultani's XD number is Wu et al. 2020, not the 2018 paper; RTFM's 78.27 XD is from VadCLIP's table, not RTFM's own).
- Cite **only** verified numbers; flag every entry on the re-check list before it ships.

## Out of scope
- Re-running any external SOTA method (weeks of work, unfair single-seed repro, risk of a misleadingly low number). The optional CLIP-TSA-style aggregation on own cached features: **SKIP** unless trivially cheap.

---

## Success criteria
- Thesis compiles with both tables + 5 paragraphs + §2 backfill.
- Paper compiles at the page limit with the condensed table (or documented fallback).
- Every cited number traces to a VERIFIED entry in `12-RESEARCH-sota.md`, or is explicitly flagged for manual re-check.
- Zero overclaim language; all new citations resolve in `references.bib`.
- Headlines UCF 82.5 / XD 78.7 unchanged (this phase adds context, not new results).

## Inputs of record
- **`12-RESEARCH-sota.md`** — verified comparison table, fair subset, positioning drafts, do/don't, per-method citations, and the mandatory re-verify list (31/34 methods confirmed against primary sources).
- `paper/main.tex`, `paper/references.bib` — edit targets.
- Already-cited SOTA in §2 (from draft scan): RTFM, VadCLIP, Sultani, Doshi & Yilmaz.

---

## Planning resolution (2026-06-21, /gsd-plan-phase)

**Target-document ambiguity resolved.** Phase 11 delivered only `paper/main.tex` (the CGW '26 workshop paper) and explicitly **deferred the full thesis manuscript** ("workshop paper first; the full master's thesis will be expanded later as a separate effort"). No thesis LaTeX file exists. Therefore:

- **Paper edits (live, this phase):** `paper/main.tex` receives the **condensed** comparison table (deliverable 5, with the Setting column; page-budget fallback to a 3–4-row mini-table), the §2 Related-Work number-backfill (deliverable 4), and new `paper/references.bib` entries (deliverable 6). Rebuild via `scripts/build_paper.ps1 -Clean`.
- **Thesis full-treatment deliverables (1–3) → standalone reusable artifact**, NOT a new thesis scaffold. The full ~20-method SOTA table, the fair-subset table, and the 5 positioning paragraphs are written as a self-contained, drop-in **LaTeX fragment** (plus prose) committed in-repo for later incorporation into the expanded thesis. This captures the verified-SOTA analysis while it is fresh, stays zero-GPU, and does not contradict Phase 11's deferral.
- **Research:** plan directly from `12-RESEARCH-sota.md` (the verified input of record); no fresh researcher spawn.
