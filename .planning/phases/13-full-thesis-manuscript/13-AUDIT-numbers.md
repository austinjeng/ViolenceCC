# Phase 13 — Full Thesis Manuscript: Adversarial Number Audit

**Plan:** 13-13 (Wave 8, phase exit)
**Date:** 2026-07-06
**Auditor scope:** every numeric claim in `thesis/` (9 chapters, 6 appendices, frontmatter, 3 generated tables, main/preamble) traced through `thesis/PROVENANCE.md` to a git-tracked source.
**Audit standard:** Phase-12 (`12-VERIFICATION.md`) — traceability table + findings + dispositions + PASS/FAIL; FAILS on untraceable numbers, forbidden-source values, or untracked manifest sources.
**Oracle:** `13-RESEARCH.md` §2 (anchor + forbidden tables) + §8 (16 pitfalls, each probed); `thesis/PROVENANCE.md` §2 (24 number families) + §4 (forbidden appendix).

---

## NUMBER AUDIT VERDICT: **PASS**

Every numeric claim in `thesis/` traces through a PROVENANCE.md row to a tracked source
(**0 untraceable**); all 238 expanded manifest source paths re-asserted tracked
(`git ls-files --error-unmatch`, **0 untracked**); **0 forbidden-source values** found
(all 16 RESEARCH §8 pitfalls probed, every grep hit dispositioned below); all 42 ablation
table cells, all 19 per-category cells, the full disc_reweight table, the TTA breakdown,
the TENT/SAR null deltas, the Pri-5 anchors, and the Pri-7 per-class table were
**recomputed from the tracked sources and match exactly**. No fixes were required — the
audit found zero defects.

---

## Audit A — Manifest-source tracking re-assertion

Every source path in PROVENANCE.md §2 (24 number families) and §3 (28 figure/table
assets) was expanded (bash brace expansion) and asserted individually:

| Section | Paths asserted | Untracked |
|---------|---------------:|----------:|
| §2 number-family sources (run-dir JSONs ×126, analysis files ×10, coral-derisk ×16, continual ×1, CSVs ×3, scripts ×2, planning docs ×3, paper/main.tex, data manifest, corruption.py) | 173 | **0** |
| §3 figure/table sources (generator scripts ×6, per_category CSVs ×6, paper figure PDFs ×4, all 25 thesis/figures + 3 thesis/tables assets, anchors, rollup CSV, bst/main/preamble/bib/PROVENANCE) | 65 | **0** |
| **Total** | **238** | **0** |

Command per path: `git ls-files --error-unmatch <path>` (exit 0 required). Zero failures.

**Audit A: PASS.**

---

## Audit B — Per-family traceability (recomputation where possible)

Recomputation = the rendered value was regenerated from the tracked source in this
audit session, not merely eyeballed.

| # | Family (PROVENANCE §2) | Rendered where | Trace method | Result |
|---|------------------------|----------------|--------------|--------|
| 1 | UCF headline 82.5±0.4 | abstract:26, ch01:179, ch05 T1, ch07 (both tables), ch08:18, ch09:30 | **Recomputed** from `results/ucf_gated_fusion_giant_s{42,123,2024}/eval_metrics.json`: mean 82.5, std(ddof=1) 0.4 | EXACT |
| 2 | XD headline 78.7±0.9 | abstract:27, ch01:180, ch05 T2, ch07, ch08:21, ch09:31 | **Recomputed** from `results/xd_gated_fusion_so400m_s*/eval_metrics.json`: 78.7±0.9 | EXACT |
| 3–8 | Tables 1–2, all 42 cells (skeleton/visual/late/gated/2-person/mean-only × 4 backbones × 2 datasets) | ch05:41–71 | (a) **byte-diff vs frozen paper** `main.tex:233–239` / `:252–258` — diff exit 0 both tables; (b) **all 42 cells recomputed** from the 126 tracked `eval_metrics.json` (mean + sample std, ddof=1): 42/42 match | EXACT (both methods) |
| 9 | Complementarity 8/8, 6/8 strictly + 2 ties, mean +0.6, p≈0.03 | ch01:182–184, ch05:87–90, :239–243, ch09:24 | paper L263 wording; p≈0.03 used everywhere (the per-run p≈0.008 variant: **0 hits** in thesis/) | PASS |
| 10 | TENT/SAR 3-seed null | ch06 tab:tent-sar-null (:158–162), abstract:40, ch01:203 | **Recomputed** from tracked `summary_3seed.json`: +0.021/+0.024, −0.082/−0.077, −0.050/−0.051, +0.011/+0.012; worst \|Δ\|=0.082 | EXACT |
| 11 | disc_reweight table (src 63.7/57.0/58.9/62.8; ours 64.4/58.5/61.1/63.3; Δ +0.67±0.23/+1.50±1.14/+2.24±0.24/+0.42±0.12; mean +1.21; 12/12 positive min +0.27) | ch06 tab (byte-diff vs paper L308–314: exit 0), ch06:260 | **Recomputed** from tracked `r1full_*.json` + `variants/v_*_{s123,s2024}_test.json` (20-condition per-seed means): every value matches; grand mean 1.21; min seed-delta 0.27 | EXACT |
| 12 | Pri-5 aggregations kept distinct: +4.83 family avg (+2.67/+5.99/+8.95/+1.69) · +13.2 = SO400M gaussian-5 3-seed (per-seed 13.92/12.34/13.31) · Base s42 gaussian-5 −3.20 · non-Gaussian 0.00 | ch06 tab:tta_breakdown (byte-match paper L349–354), ch06:325–333 (explicit disambiguation paragraph), ch06:361 (−3.20 disclosure) | **Recomputed** family averages from the same tracked JSONs: 4.83 / 2.67 / 5.99 / 8.95 / 1.69; SO400M g5 mean 13.19 (per-seed 13.92/12.34/13.31); Base s42 g5 −3.20; motion/jpeg/brightness ≈0.00 | EXACT; +3.31 (s42-only) **0 hits**; raw +13.9 **0 hits** |
| 13 | Episodic per-condition bests TENT +3.81 (jpeg s2), SAR +5.38 (gaussian s5) | ch06:112–114 | labeled per-condition bests of the 500-run episodic grid (results-index.csv, 680 TTA rows) — framing preserved (bests, not means) | PASS |
| 14 | Episodic inertness 98.4% ≤32 snippets | ch03:313 | paper §4.5 anchor | PASS |
| 15 | 1,536 adapted params (3 LN, 6 tensors) | ch01:202, ch03:298 | paper sec:tta anchor | PASS |
| 16 | Pri-6 bootstrap CIs (82.49 [75.63, 88.02] w12.39; 79.74 [76.62, 82.68] w6.06; B=2000 seed 12345) | ch05:316–334 | tracked `pri6_bootstrap_ci.json`; 82.49 appears ONLY in the permitted ch05 CI context (grep: 1 hit repo-thesis-wide) | PASS |
| 17 | Pri-7 per-class (HM +0.31±1.08 7/10 pos · APP −0.29±0.16 · HM−APP +0.60 · Shooting +1.05±0.20 n=22) | appB:91–113 | **Recomputed** all 13 table rows + group means from tracked `pri7_per_class_complementarity.csv` — every cell matches; exact hedge "directionally supportive but mixed/noisy" present (appB:120); Welch t-test: absent | EXACT |
| 18 | Pri-9 (anomaly mean 0.874 / normal 0.382 / p75 0.986; failure rows) | ch05:511–561 | tracked `pri9_failure_cases.json`: RoadAccidents011 0.1415/0.019 (1.9%), Shooting028 0.1135/0.142, Explosion007 0.1447/0.042, Shooting018 0.1453/0.092 — all verified; stored video_auc (0.9268/0.9452): **0 hits** | PASS |
| 19 | Sweep (historical): XD 74.69±2.55 (+3.72 over 70.98±1.08); UCF 82.12±0.46 (+0.14 over 81.98±0.29); second UCF confirmation +0.12 | ch05:287–295, appC:150–172 | **Recomputed** 3-seed confirmations from tracked `results-index.csv` (lr1e3_k2: 74.69±2.55; lr1p5e3_k9: 82.12±0.46; lr1e3_k1: 82.10 → +0.12); appC top-10 table cells match the ranked s42 sweep rows (top-5 both datasets verified cell-by-cell) | EXACT |
| 20 | RTFM repro (0.6570 vs 0.7781; gate 0.7681; −11.11pp vs gate; flow 0.5916 −6.54pp; AUC 0.8675/0.8341; snippet 0.8699/0.8365, Δ0.0024; coverage 2748/3360=81.8%, 477/594=80.3%) | appA:38–129, ch08:24–26 | tracked `eval_metrics.json` both runs (0.65697/0.59157/0.86748/0.83413 ✓); coverage figures verbatim in tracked `04b-05-SUMMARY.md:87–100`; −11.11 correctly framed **vs the gate threshold** (0.7681−0.6570), not the anchor; per-category RTFM table: all 12 cells match the two tracked CSVs | PASS |
| 21 | Efficiency (0.50–1.02M head params; <5 min/config; RTX 4090; benchmark tables) | ch01:102, ch04:344–370, ch09:65 | ch04 model table matches tracked `benchmark_models.csv` row-for-row (37.57/595.65/633.22/498.11/137.41 K params + MACs/latency/throughput/VRAM); backbone table matches `backbone_bench_combined.csv` (86.19M/13.0M/5.684M/25.0M) | EXACT |
| 22 | Dataset facts (UCF 1,900/13 cat/800+810/150+140/**254 evaluated**; XD 4,754/6 cat/3,954/800; 172+1 <64-frame exclusions) | ch03:114 (exclusion sentence lifted verbatim from paper L136), ch04:22–44, :76 | paper L136/L206 disclosure sentences present; snippet-duration asymmetry (20 s vs ~2.7 s, 3 FPS vs 24 FPS) disclosed ch03:114 | PASS |
| 23 | PRD gate misses (UCF min 83 target 85–87 → miss by 0.5; XD min 80 target 82–85 → miss by 1.3; RTFM 84.30±1%) | ch08:16–26 | STATE.md PRD gate rows; arithmetic verified (83−82.5=0.5; 80−78.7=1.3) | PASS |
| 24 | Corruption severity params (σ 0.08/0.12/0.18/0.26/0.38; JPEG 25/18/15/10/7; brightness ADDITIVE 0.1–0.5; blur (10,3)…(20,15); skeleton re-extract only blur+JPEG) | ch04:179–182 table + :189–199 | **byte-match vs tracked `scripts/corruption.py:30–43`** — all four parameter rows identical; brightness correctly labeled "additive offset"; CLAUDE.md's stale lists (JPEG 10–50, σ 0.1–0.5, multiplicative brightness): **not used** | EXACT (Pitfall 5 clear) |

Additional traced values not in a §2 family: ch02 external anchors (Sultani 75.41,
RTFM 84.30/77.81, VadCLIP 88.02/84.51) — verified SOTA values (12-RESEARCH-sota /
13-SOTA-EVIDENCE); ch07 SOTA tables — see Audit C; ch05 pooling deltas (2-person
≈−0.90 AP cross-backbone, CLIP −2.1; mean-only −0.3…−0.5) — recomputed from the 42
verified cells (−0.925 ≈ 0.90 ✓); XD seed-sensitivity claims (Giant 2.8% lone outlier,
UCF max 0.4%) — consistent with the recomputed stds.

**Audit B: PASS — 0 untraceable numbers; every recomputable family recomputed EXACT.**

---

## Audit C — SOTA table cells (ch07)

The full ~20-method table (ch07:218–248) and the 7-row fair-subset table (ch07:318–325)
were checked cell-by-cell against the user-approved 13-SOTA-EVIDENCE verdicts (19/19
result cells VERIFIED, applied by plan 13-12 — the sole change authority for external
numbers): GS-MoE 91.58/82.89, PI-VAD 90.33/85.37, Holmes-VAD 89.51/90.67 (preprint
disclosed), DSANet 89.44/86.95, Holmes-VAU 88.96/87.68 (**VIDEO-level** disclosed),
STPrompt 88.08/N-A, FDPN 88.03/N-A, VadCLIP 88.02/84.51, TPWNG 87.79/83.68, CLIP-TSA
87.58/82.19, MGFN 86.98/79.19 (I3D), UR-DMU 86.97/81.66, PEL4VAD 86.76/85.59,
PiercingEye 86.64/88.82 (audio+text disclosed), AnomalyCLIP 86.36/78.51, TEVAD
84.9/79.8, Light-WVAD 84.7/**---**, RTFM 84.30/77.81, EventVAD 82.03/64.04 (AP not
ROC-AUC), This work **82.5/78.7**, LAVAD 80.28/62.01, Sultani 75.41/---, HyperVD
N-A/85.67 (audio), Ghadiya N-A/86.34 (audio). All 14 caveat footnotes (a–n) present.

Paper `tab:comparison` subset (10 rows) matches the thesis rows verbatim.

**Audit C: PASS.**

---

## Audit D — Forbidden-source / pitfall probes (all 16 RESEARCH §8 pitfalls)

Scan scope: `thesis/chapters/ thesis/appendices/ thesis/frontmatter/ thesis/tables/ thesis/main.tex thesis/preamble.tex`.

| Probe (pitfall) | Pattern(s) | Hits | Disposition |
|---|---|---:|---|
| tables_generated.tex values (P1) | `tables_generated`, `71.8`, `40.9`, `83.0`/`79.9`-as-mean-only | 0 / 0 / 0 / n.a. | CLEAN — 79.9 appears only as the canonical Late-Fusion Giant UCF cell (79.9±0.8), a Tables-1/2 value, not the forbidden XD Mean-Only single-seed relic |
| Phase 8–11 relics (P2) | `83.6`, `83.3`, `83.28` | 2 / 0 / 0 | the two `83.6` hits are **TPWNG 83.68** (external XD AP, verified SOTA cell) — substring false positive, ALLOWED |
| Sweep chained to headlines (P3) | `0.8227`, `0.7192`, `71.92`, `0.9200` | 2 / 3 / 4 / 0 | ALL hits in ch05 sweep section (:265–278) + appC only, every one carrying an in-sentence historical label ("historical 2026-05 sweep-era configuration", "labeled historical sweep-era baseline", "never chain into the headline results"); delta-vs-baseline columns EXCLUDED from tab:appc-ranked (caption states this) — the sole permitted exception, correctly executed |
| Light-WVAD fabricated XD (P4) | `77.3` | 0 | CLEAN — XD cell is `---` in both ch07 tables with "(XD not evaluated)" |
| CLAUDE.md corruption params (P5) | ch04 params vs corruption.py | — | EXACT byte-match with `scripts/corruption.py:38–42`; stale CLAUDE.md values absent |
| Raw +13.9 (P6) | `13.9` | 0 | CLEAN (13.92 appears only as an explicit per-seed value inside the +13.2 3-seed disclosure — checked, PROVENANCE row 12 sanctions it) |
| Protocol asymmetry (P7) | tab:tta caption | — | truncated-grid non-comparability caveat present in ch06 caption (byte-identical to paper caption) |
| Load-bearing disclosures (P8) | 64-frame sentences, λ2 footnote | — | ch03:114 lifts paper L136 verbatim; ch04:29 has the "254 meet the 64-frame minimum" sentence; λ2 ≤0.13 pp disclosure at ch04:247 |
| Phase-4/4c per-category relics (P9) | `0.955`, `0.985`, `88.15`, `44.89` | 0 | CLEAN — all per-category values regenerated from tracked post-λ0/post-h1 CSVs (Audit B rows verified) |
| 2-Person promotion (P10) | ch05:151–160 | — | explicitly NOT promoted, with a three-reason justification paragraph; headline remains default-pooling Gated Fusion |
| p-value duality (P11) | `0.008` | 0 | CLEAN — p≈0.03 (tie-dropping) used exclusively |
| results-index backbone column (P12) | audit tooling | — | audit recomputations parsed run_name suffixes (not the empty backbone column) |
| Missing-on-disk citations (P13) | `phase7_summary`, `phase7_rtfm_gap_diagnostic`, `phase4_charts` | 0 | CLEAN — appA cites tracked 07-VERIFICATION.md |
| Fragment lift mechanics (P14) | `documentclass`/`end{document}` in ch07 | 0 | CLEAN (verified by 13-12 gates; re-confirmed) |
| TTA memory staleness (P15) | CORAL-as-shipped claims | — | ch06 frames NORM/CORAL as explored-and-rejected (rank-disruptive, backbone-dependent sign) — matches the tracked narrative source |
| Stored video_auc (P16 / Pri-9 note) | `0.9268`, `0.9452` | 0 | CLEAN |
| Non-family relics | `94.02` | 1 | ch07:275 footnote $^f$ — explicit *negation* ("does not appear in the CLIP-TSA paper at all"), the exact wording the evidence report mandated; ALLOWED |
| Pri-6 drift guard | `82.49`, `79.74`, `78.72` | 1 / 1 / 1 | 82.49/79.74 only as s42 bootstrap point estimates in the ch05 CI section (the explicitly permitted context); 78.72 only in ch08:146 as the Pri-3 smoothing baseline (78.72→79.29, +0.57, cited to REVIEW-2026-06-10 tracker) — all permitted |

**Audit D: PASS — 0 forbidden-source values (every hit dispositioned above).**

---

## Findings & dispositions

**No defects found.** Zero fixes required; zero PROVENANCE.md rows missing (the manifest
already covered every family and asset encountered during extraction — no completeness
additions needed).

Observation (non-defect, recorded for transparency): the paper's Tables 1–2 report
sample std (ddof=1) while the per-category generator documents and uses population std
(ddof=0). Both conventions reproduce their respective rendered values exactly from the
tracked sources, and each table's convention is internally consistent; no rendered value
is affected.

---

## NUMBER AUDIT: **PASS** (Audits A–D all PASS; 0 untraceable, 0 forbidden, 0 untracked)

---

# Task 2 — Overclaim Scan + Headline-Consistency Check

**Scope:** all rendered prose in `thesis/` (comments excluded). Token list per Phase-12
(Audit 3) + the Phase-13 additions (online-TTA cap, clean-AUC-gain cap, points-not-%).

## Audit E — Overclaim scan

### Token hits and dispositions

| Token | Hits (rendered) | Disposition |
|---|---|---|
| `state-of-the-art` / `state of the art` | ch07:15, ch07:190, ch07:204, ch07:257, ch07:378, ch09:73 | :15 "comparison **against** the published state of the art" (descriptive); :190 section title (descriptive); :204 "We do \emph{not} claim state-of-the-art performance" (**required negation** — note: this hit contains the literal token sequence "state-of-the-art performance"; it is the mandated no-SOTA framing itself, ALLOWED per the Phase-12 negation precedent); :257 "\textbf{We do not claim state-of-the-art}" (negation, table note); :378 "does not claim a new state of the art" (negation); ch09:73 "We do not claim state-of-the-art benchmark performance" (negation). **0 disallowed** |
| `\bSOTA\b` | 0 rendered (1 hit inside a `%` provenance comment, ch07:225) | non-rendered — ALLOWED |
| `achieves SOTA` / `beats SOTA` / `comparable to SOTA` | 0 | CLEAN |
| `outperform*` | ch02:266, ch05:98–99 | ch02:266 — **other** (task-adapted/text-aligned) systems outperform frozen-feature ones: the honesty-ceiling statement itself; ch05:98–99 — internal gated-vs-late ablation claim (the exact analog of the two 12-VERIFICATION KNOWN-ALLOWED lines). **0 disallowed** |
| `surpass` / `beats` | ch07:273 | FDPN footnote quoting that paper's own "narrowly beats" self-report (external attribution). ALLOWED |
| online/streaming TTA claims | ch01:232, ch03:316/:403, ch06:76/:132/:368–369, ch08:92–98/:165–168 | every hit is either the protocol name ("continual-online", TENT/SAR's own terminology), a future-work pointer, or an explicit **negation** — ch08:98: "we make no online-adaptation claim". **0 disallowed** |
| clean-AUC TTA gains | ch06:19, abstract:47, ch01:230, ch03:403 region, ch09:57 | all negations/caps: "no method in this chapter changes clean-data [metrics]", "no gain claimed on clean data", "improves AUC \emph{under corruption} only", "not clean[-data] improvement". **0 disallowed** |
| "%" used on TTA gains (points required) | 0 | all ch06 gains denominated in "points" (grep for `+N.NN\%` gain phrasing: 0 hits); ch06:19 states the convention explicitly ("gains, stated in points") |

**Total disallowed overclaim hits: 0.** (6 negations, 2 descriptive headers, 1 external
self-report, 2 internal-ablation claims — all itemized above.)

### Required framings — located (file:line)

| # | Required framing | Locations |
|---|---|---|
| 1 | No-SOTA / no-peak-score statement | ch07:204, ch07:257, ch07:378, ch09:73; ch01:220 ("\textbf{No peak-score claim.}"); abstract:34–35 ("not a new peak score") |
| 2 | ~88–91% field-ceiling disclosure | abstract:32, ch01:221–222 (+ ch02:266 qualitative ceiling statement) |
| 3 | Fair-subset framing (ch07) | ch07:16 (intro pointer), ch07:333 ("\textit{Read of the fair subset.} Within this strictly-frozen / no-text ...") |
| 4 | "+13.2 … single most-degraded condition" | abstract:46, ch01:212, ch06:303 (fig caption), ch06:329 (prose) |
| 5 | Transductive disclosure (ch03/ch06/ch08) | ch03:334, ch03:359, ch03:401; ch06:366–370; ch08:92–98, :123, :165–168; also ch07:165, ch09:57, abstract:46, ch01:232 |
| 6 | λ2 smoothness-implementation footnote (ch04) | ch04:237–247 ("shifts the headline UCF-Crime AUC by at most 0.13 percentage points") |
| 7 | 64-frame exclusion disclosures (ch03/ch04) | ch03:114 (paper L136 sentence verbatim: "Videos shorter than 64 frames (172 videos in UCF-Crime, one in XD-Violence) are excluded…"); ch04:29 ("254 meet the 64-frame minimum") + ch04:76 |
| 8 | "small but consistent" complementarity (ch05) | ch05:231 (\emph{small but consistent}); also ch01:184, ch07:29, ch09:21, abstract:28 |

All 8 required framings present. **Audit E: PASS.**

## Audit F — Headline byte-consistency

Full occurrence inventory (rendered lines only):

**82.5 — 22 occurrences:** abstract:26 · ch01:179, :220 · ch05:47, :49 (table cells), :78, :137, :188 · ch06:52 · ch07:68, :244, :306, :325, :337, :358, :407 · ch08:18, :48, :61 · ch09:30, :37. Every occurrence is byte-exactly `82.5`; wherever a std is attached it is `$\pm$0.4` (ch01:179, :220; ch05:47, :49, :78, :137; ch07:68; ch08:18). Near-string `82.51` (ch07:293) is HyperVD's visual-only variant — an external verified number, not drift.

**78.7 — 21 occurrences:** abstract:27 · ch01:180, :220 · ch05:69 (table cell), :79, :204, :213 · ch07:69, :244, :306, :325, :334, :358, :403, :445 · ch08:21, :44, :63 · ch09:31, :37. Every occurrence byte-exactly `78.7`; std wherever given is `$\pm$0.9` (ch01:180, :220; ch05:69, :79; ch07:69; ch08:21). Near-string `78.72` (ch08:146) is the Pri-3 smoothing baseline (78.72→79.29, +0.57), cited to the tracked REVIEW-2026-06-10 tracker — the explicitly permitted context.

**Drift guard:** `82.49` — exactly 1 occurrence (ch05:331), the s42 bootstrap point
estimate inside the Pri-6 CI paragraph — the ONLY permitted context. `79.74` — 1
occurrence (ch05:333), same context. No other precision variants of either headline
exist anywhere in `thesis/`.

Plan gate check: abstract + ch09 contain ≥2 occurrences of 82.5 (3 found: abstract:26,
ch09:30, ch09:37) ✓; `achieves SOTA` = 0 ✓; the single `state-of-the-art performance`
token match is the mandated negation at ch07:204, dispositioned above ✓.

**Audit F: PASS — headlines byte-consistent everywhere; zero unexplained drift.**

---

## OVERALL VERDICT (Tasks 1 + 2): **PASS**

Number audit PASS (Audits A–D) · Overclaim scan PASS with 0 disallowed hits and all 8
required framings located (Audit E) · Headlines 82.5 / 78.7 byte-consistent across
abstract, ch01, ch05, ch06, ch07, ch08, ch09 with ±0.4 / ±0.9 wherever std is given
(Audit F).
