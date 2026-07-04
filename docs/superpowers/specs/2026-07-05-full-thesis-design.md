# Spec: Full-Length Master's Thesis (ViolenceCC)

**Date:** 2026-07-05
**Status:** Approved design, pending user spec review
**Author:** Claude (brainstorming session with Austin / Wei-Han Jeng)

## 1. Goal

Produce the full-length master's thesis manuscript for the ViolenceCC research —
"Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection" — as a
self-contained LaTeX document. The thesis expands the 11-page CGW '26 workshop paper
(`paper/main.tex`) into a complete, oral-defense-ready document covering everything the
research produced: all methodology, all experiments (including negative and diagnostic
results the paper cut), full SOTA positioning, and engineering/reproducibility detail.

No full-length thesis manuscript exists today; Phase 11 produced the workshop paper only.

## 2. Locked decisions (user-confirmed 2026-07-05)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Format | No university template. Clean generic LaTeX `report`-class skeleton, easy to re-skin later. |
| D2 | Language | English throughout. No Chinese abstract. |
| D3 | Numbers | **Freeze: canonical verified numbers only** (UCF 82.5 AUC / XD 78.7 AP anchors). No new experiments. In-flight tracks (Pri-3 XD smoothing, Pri-2/4/8 TTA extensions) go to Future Work, not results. Enforced via the tracked provenance manifest (Section 7a): every cited source gets git-tracked in Wave 0. |
| D4 | Scope | Thesis document only. Defense slides are a separate later task. |
| D5 | Emphasis | No special committee emphasis — thorough everywhere. |
| D6 | Structure | 9 chapters: paper's core flow preserved, Experiments split into Setup / Fusion-Results / TTA-Results. Appendices A–F. |
| D7 | SOTA debt (added 2026-07-05, spec review) | **In-phase primary-source verification gate**: agents verify all RE-VERIFY / checklist externals against primary papers, user spot-approves the evidence report; no downgraded "draft pending verification" deliverable. |

## 3. Deliverable layout

```
thesis/
  main.tex                  \documentclass[12pt,a4paper,oneside]{report}
  preamble.tex              amsmath/amssymb, booktabs, multirow, graphicx, tikz
                            (positioning,arrows.meta,fit,calc), natbib [numbers]
                            with IEEEtranN.bst (the natbib-compatible variant),
                            hyperref, geometry (2.5cm margins), setspace (1.5),
                            caption, subcaption, microtype
  frontmatter/
    titlepage.tex           NTUST, degree, author Wei-Han Jeng, advisor Chuan-Kai Yang
    abstract.tex            expanded/restructured from paper abstract (fixes T5-2 density)
    acknowledgments.tex     placeholder for user to fill
    notation.tex            abbreviations + symbol table
  chapters/
    ch01_introduction.tex ... ch09_conclusion.tex
  appendices/
    appA_rtfm.tex ... appF_figures.tex
  references.bib            superset: paper's 27 entries + ~11 new (Section 6)
  IEEEtranN.bst             VENDORED copy (do not rely on MiKTeX resolution: the only
                            local hit is inside the unrelated feupphdteses package)
  PROVENANCE.md             tracked manifest: every thesis number/figure -> tracked
                            source path (Section 7a)
  figures/                  thesis figure set (Section 5)
scripts/build_thesis.ps1    latexmk wrapper modeled on build_paper.ps1 but
                            NON-INTERACTIVE by default (no Invoke-Item; build_paper.ps1:111
                            opens the PDF viewer — do not copy that); optional -Open flag;
                            -Clean flag; preflight that asserts the vendored
                            thesis/IEEEtranN.bst exists and kpsewhich resolves each
                            required LaTeX package, failing with a clear message
```

**Build baseline (defines "stock MiKTeX + repo alone"):** MiKTeX with its default
on-demand package installation enabled — same baseline as the existing paper build; no
manual package setup. The only nonstandard-resolution item, `IEEEtranN.bst`, is
vendored. The preflight (and `thesis/PROVENANCE.md` header) lists the required packages
(expected: natbib, booktabs, multirow, tikz/pgf, hyperref, geometry, setspace, caption,
subcaption, microtype, amsmath — finalized in Wave 0) so a failure is diagnosable
offline; anything the preflight finds nonstandard on stock MiKTeX gets vendored too.

- Bibliography: BibTeX with the vendored `IEEEtranN.bst` (numeric, natbib-compatible) + natbib `[numbers]`.
- Build artifacts git-ignored (extend existing paper artifact patterns to `thesis/`).
- `paper/` stays frozen as the CGW '26 artifact; the thesis never modifies it.
- Estimated length: 90–120 pages.
- Equations lifted verbatim from `paper/main.tex` (they are code-verified as of
  quick tasks 260601-mry / 260604-vfi); expand prose around them, never alter the math.

## 4. Chapter content map

Every chapter builds on the corresponding paper section as base prose, expanded with the
listed sources. Paper section references are to `paper/main.tex` (458 lines).

### Ch 1 — Introduction (paper §1)
Motivation (surveillance-scale violence detection, annotation cost, weak supervision),
problem statement, gaps (single-modality dominance; CLIP methods miss motion dynamics;
backbone sensitivity unstudied; BN-targeting TTA vs LayerNorm heads), explicit research
questions (RQ1 dual-modal fusion value, RQ2 backbone sensitivity, RQ3 entropy-TTA
transfer to LN), the 3 contributions, thesis organization roadmap.

### Ch 2 — Related Work (paper §2 + `.planning/phases/12-sota-comparison-and-positioning/12-RESEARCH-sota.md`)
Full surveys, one section each:
- Weakly supervised VAD: Sultani → RTFM → memory/uncertainty (UR-DMU, MGFN) →
  CLIP-era (CLIP-TSA, VadCLIP, AnomalyCLIP, TPWNG, PEL4VAD) → MLLM/training-free
  (LAVAD, EventVAD) → recent (PI-VAD, DSANet, GS-MoE). ~20 methods from the Phase-12
  research artifact (31/34 primary-source-verified).
- Skeleton-based action recognition (ST-GCN lineage → CTR-GCN; PYSKL) and
  skeleton use in anomaly detection.
- Vision-language backbones: CLIP, SigLIP, SigLIP2 family.
- Test-time adaptation: TENT, SAR, NORM/statistic-restoration, CORAL; the
  BN-vs-LN structural argument.

### Ch 3 — Methodology (paper §3, all subsections expanded)
3.1 pipeline overview (reuse TikZ architecture figure); 3.2 skeleton extraction
(YOLOX-m + RTMPose-m, top-2 persons, PreNormalize2D, tensor shapes); 3.3 CTR-GCN
features (4-stream j/b/jm/bm weighted 1.0/1.0/0.5/0.5, 64-frame snippets, GAP, 256-d);
3.4 visual-language features (4 backbones with exact open-clip checkpoint names,
~1 FPS sampling, mean+max pooling to 2d); 3.5 fusion mechanisms (late; gated with all
equations, per-dimension gate, residual interpretation (1+g)ŝ+(2−g)v̂, three named
LayerNorms and why); 3.6 MIL training (top-k ranking loss, RTFM L2 sparsity λ1=8e-3,
smoothness λ2 dataset-dependent, shuffled-val rationale); 3.7 TTA methods — TENT/SAR
LN-affine adaptation protocol (1,536 params, per-video reset vs continual) AND the full
disc_reweight derivation unpacked from the paper's one-paragraph compression: w_vl
dispersion ratio, skeleton-reliability gate s with fixed factor-2 anchor (not tuned),
saturation behavior, final w = 1−(1−w_vl)s, transductive whole-condition pooling.
Source for the TTA narrative: `.knowledge/tta-to-reweighting.html`.

### Ch 4 — Experimental Setup (paper §4.1–4.2 + Phase 2/5 artifacts)
Datasets (UCF-Crime 1,900 videos/13 categories; XD-Violence 4,754/6 categories),
official splits + seeded 15% stratified val, video-level-labels-only model selection,
evaluation protocol (frame-level AUC / AP; snippet→frame expansion: UCF full-length
grid via `data/ucf_total_frames.json` manifest, XD truncated snippet-aligned grid;
64-frame exclusions disclosed exactly as main.tex does), **UCF-Crime-C construction**
(4 corruption types × 5 severities with full ImageNet-C-style parameterization from
Phase 5: JPEG quality levels, Gaussian σ set, brightness factors, motion-blur params;
CLIP re-extraction for all 20 conditions, skeleton re-extraction for blur+JPEG only —
cost decision), implementation details (AdamW, warmup+cosine, batch 16 pairs, T=32,
top-k=3, seeds {42,123,2024}), reproducibility protocol (fixed seeds, config snapshots,
bit-identical rerun verification, results-index.csv), three-conda-environment
infrastructure (vcc-skeleton / vcc-ctrgcn / vcc-main and why), efficiency benchmarks
(`results/benchmark_models.csv`, `results/backbone_bench_combined.csv`; 0.50–1.02M
trainable params, <5 min/config on one RTX 4090).

### Ch 5 — Results: Fusion and Backbone Study (paper §4.3–4.4 + analysis artifacts)
- Main ablations: 3-seed Tables 1/2 (6 variants × 4 backbones, from main.tex canonical
  inlined tables) + pooling ablations (2-person, mean-only) with the finding that
  default pooling wins on XD.
- Per-category breakdowns: regenerate tables from the CURRENT canonical run dirs'
  `per_category.csv` (3-seed, post-λ0/post-h1) — do NOT reuse Phase-4/4c-era values.
- Backbone comparison: 4-way analysis (UCF favors larger backbones, Giant best;
  XD statistically indistinguishable visual-only, SO400M leads under fusion;
  SigLIP2-Base −2.2pp UCF story from Phase 8; skeleton benefit backbone-dependent).
- Complementarity: 8/8 meet-or-exceed, 6/8 strictly positive + 2 ties, mean +0.6pp,
  tie-dropping sign test p≈0.03 (exact paper wording post-T2-1); per-class analysis
  pointer to Appendix B.
- Hyperparameter sensitivity (Phase 7): 198-config lr×k sweep, XD winner lr=1e-3/k=2
  (+3.72pp 3-seed), UCF insensitive (+0.14pp). **Context trap:** the sweep predates
  λ_smooth=0 adoption and ran on the CLIP backbone — present as a sensitivity study in
  its historical configuration, explicitly noted; do not chain its numbers to the
  current 78.7 headline.
- Statistical robustness: Pri-6 bootstrap CIs (UCF s42 82.49 CI [75.63, 88.02] width
  12.39pp; XD s42 79.74 CI [76.62, 82.68]) framed as field-wide test-set-size
  uncertainty, s42-only caveat stated.
- Seed sensitivity: XD AP std up to 1.08–2.8% vs UCF 0.29–0.4%; Giant XD outlier.
- Qualitative: temporal score curves, gate-activation distributions, t-SNE projections.
- Failure analysis (Pri-9): two failure regimes (saturated-high near-ties; short-event
  misses), top FP normals, normal-frame p75 = 0.986 over-confidence/calibration
  limitation, score histogram.

### Ch 6 — Results: Robustness and Test-Time Adaptation (paper §4.5 + TTA artifacts)
- Source-only degradation on UCF-Crime-C (clean 82.5 → corrupted means 57.0–63.7).
- **Full TENT/SAR results** (the paper's one-sentence negative result expanded):
  500-run lr×ρ grid (Phase 5), per-condition bests vs near-zero means, the episodic
  protocol inertness finding (98.4% of UCF test videos ≤32 snippets) and the continual
  protocol fix, TRUE 3-seed continual null: ΔTENT/ΔSAR per backbone
  CLIP +0.021/+0.024, Base −0.082/−0.077, SO400M −0.050/−0.051, Giant +0.011/+0.012
  (worst |Δ| = 0.082pp < 0.1pp). Also the dropout-in-train-mode bug as a methods
  cautionary note (~1.07pp per-condition noise before the fix).
- Feature-statistic restoration exploration (NORM/CORAL): rank-disruptive,
  backbone-dependent sign; the S1–S6 strategy exploration narrative that led to
  disc_reweight (source: `.knowledge/tta-to-reweighting.html`, `results/_coral_derisk/`).
- disc_reweight results: Table 3 (Source-Only / Ours / Δ paired per-seed), per-corruption
  breakdown table, 20×4 severity heatmap (`pri5_per_condition_heatmap.csv`, thesis-only),
  all-positive 12/12 backbone×seed cells (min +0.27), honest caveats (Base −3.2 single
  seed at gaussian-5; non-Gaussian families 0.00 BY CONSTRUCTION — gate routes to
  source, not "TTA hurts").
- LN-barrier mechanism analysis (paper §5 thread, expanded): frozen gate/head,
  LN-affine capacity too small to reorder a rank metric, shift lives in frozen
  backbone features.

### Ch 7 — Discussion (paper §5 + `paper/sota_comparison_full.tex`)
The paper's five discussion threads expanded, plus full SOTA positioning lifted from the
fragment (content between `FRAGMENT BODY BEGIN/END` markers): 20-method table
(`tab:sota-full`), 7-row fair-subset table (`tab:sota-fair`), positioning paragraphs
P1–P5, metric-definitions paragraph, compute-honesty argument. Citations rewired from
manual [N] labels to `\cite` (Section 6). Carry the fragment's caveat footnotes.
Use the POST-260622-ukd state: Light-WVAD XD cell is `---` (the 77.3 was fabricated
and removed; never reintroduce it).

### Ch 8 — Limitations and Future Work (paper §6 + REVIEW-2026-06-10 §5)
All paper limitations expanded + accepted gate misses stated plainly (UCF 82.5 < 83
minimum target; XD 78.7 < 80; PRD targets disclosed), XD seed sensitivity, transductive
TTA cap (no online claim without Pri-4), dataset scope, synthetic corruptions.
Future work: deferred tracks as forward pointers — Pri-3 XD test-score smoothing
(verified +0.57pp, deliberately not adopted under freeze), Pri-2 skeleton-head ensemble
routing, Pri-4 streaming/causal w, Pri-8 JPEG rescue, temporal module (Pri-11),
text-prompt branch (Pri-13), audio for XD, additional datasets.

### Ch 9 — Conclusion (paper §7)
Restate findings with numbers, modularity/efficiency pitch, code availability.

### Appendices
- **A — RTFM XD-I3D reproduction investigation:** AP 0.6570 vs 77.81 anchor (−11.11pp);
  Flow-swap diagnostic (100% coverage, AP 0.5916, −6.54pp → data coverage ruled out);
  Phase-7 root-cause diagnostics (1024-d vs published 2048-d features; 3 training-regime
  diffs); conclusion "training regime, not eval bug — fusion results unaffected".
  Per-category RTFM table.
- **B — Per-category tables + per-class complementarity:** full UCF 13-category and
  XD 6-category tables (regenerated, 3-seed); Pri-7 per-class complementarity
  (human-motion +0.31±1.08, 7/10 positive; appearance −0.29±0.16; HM−APP +0.60pp;
  Shooting +1.05±0.20 cleanest) — hedged exactly as designated: "directionally
  supportive but mixed/noisy"; no Welch t-test.
- **C — Hyperparameter sweep detail:** 19×6 grids, heatmaps, ranked tables,
  3-seed confirmations (regenerated via `scripts/generate_phase7_charts.py`).
- **D — Engineering notes:** two/three-environment strategy (mmcv 1.x vs PyTorch 2.x),
  Windows-specific quirks, extraction throughput (~21.6 FPS, 99.3% inference-bound),
  pitfall register (C1–C5, M5–M7), anti-pattern register highlights.
- **E — Reproducibility guide:** repo map, env setup → extraction → training →
  evaluation → table/figure generation command walkthrough; seeds/manifests/config
  snapshots. (Discharges review item T6-2 as a side effect.)
- **F — Additional figures:** skeleton overlays (XD-only; UCF 64×64 source limitation
  documented), extra temporal curves, Pri-9 score histogram, gate histograms not used
  in Ch 5.

## 5. Figures and tables plan

### Reuse as-is (verified current)
| Asset | Use |
|---|---|
| `paper/figures/fig_architecture.tex` (TikZ) | Ch 3 overview (re-wrap for one-column width) |
| `paper/figures/fig_temporal_scores.pdf` | Ch 5 qualitative |
| `paper/figures/fig_backbone_comparison.pdf` (3-seed, regenerated 260622-uuu) | Ch 5 |
| `paper/figures/fig_tta_comparison.pdf` | Ch 6 |
| `paper/figures/fig_gating_distribution.pdf` (publication-grade, unused by paper) | Ch 5 |
| `results/_analysis_2026-06-10/pri9_score_hist.png` | Ch 5 / App F |

### Regenerate zero-GPU (replot committed data; no new experiments — consistent with D3)
| Asset | Action |
|---|---|
| Phase-7 sweep heatmaps (S01/S02/S04/S05) | Run `scripts/generate_phase7_charts.py` (output dir currently absent; regenerable from results-index.csv) |
| Corruption heatmaps (old phase6 C01–C06) | STALE (pre-dropout-fix episodic runs). Regenerate from `results/_tta_rerun_continual/` 3-seed data + disc_reweight results; old C-series is FORBIDDEN |
| 20×4 severity heatmap | New figure/table from `results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv` |
| Per-category tables | Regenerate from canonical run dirs' `per_category.csv` (3-seed, post-λ0/post-h1 state) |

### Provenance-check before reuse (include / regenerate / drop, per figure)
Phase-6 PNGs: A-series temporal curves (5), B-series skeleton overlays (3), D-series
gate distributions (4), E-series t-SNE (2), F-series extras (6). These date from the
single-seed era (May 2026). For each: verify the underlying checkpoint/scores still match
canonical numbers; regenerate via `scripts/generate_phase6_charts.py` against current
checkpoints where feasible (zero-GPU: checkpoints + cached features exist locally);
drop if provenance cannot be established. B-series is XD-only by necessity (documented).

### Figure provenance classes (binding — clean-checkout rule)
Checkpoints and cached features are LOCAL-ONLY (untracked, E:/) — they cannot serve as
manifest sources. Every thesis figure must land in exactly one class in PROVENANCE.md:
- **Class R (regenerable):** generated by a tracked script from tracked data
  (e.g. sweep heatmaps from results-index.csv; severity heatmap from the tracked
  Pri-5 CSV). Manifest row lists script + tracked inputs.
- **Class V (verified binary):** the final PDF/PNG is itself committed under
  `thesis/figures/`, with a manifest verification note recording what it was checked
  against and when (e.g. "regenerated 2026-07-XX from local checkpoints; values
  cross-checked against tracked per_category.csv / Table 1 anchors"). All Phase-6
  reuses and locally regenerated figures end up Class V.
No figure may cite untracked inputs as its provenance without a Class-V verification
note; a clean checkout gets tracked binaries + the note, or full regenerability.

## 6. Bibliography plan

- Start from `paper/references.bib` (27 entries, all current).
- Add ~11 entries for the full SOTA table: Holmes-VAD, Holmes-VAU, STPrompt, FDPN,
  TPWNG, PEL4VAD, PiercingEye, AnomalyCLIP, TEVAD, HyperVD, Ghadiya et al. — citation
  strings staged in `12-RESEARCH-sota.md` Section 8.
- Add survey-support cites for Ch 2 as needed (ST-GCN, etc.) — verified entries only.
- PI-VAD/DSANet publication status + full author lists (12-VERIFICATION items #16/#17)
  are RESOLVED by the primary-source verification gate (Section 8, step 2b) — no TODO
  comments survive into the final bib.

## 7. Number-integrity guardrails (binding on all writers)

### Canonical anchors (the only permitted values)
| Quantity | Value |
|---|---|
| UCF headline | 82.5 ± 0.4 AUC (Gated Fusion, SigLIP2 Giant, seeds 42/123/2024) |
| XD headline | 78.7 ± 0.9 AP (Gated Fusion, SigLIP2 SO400M) |
| Skeleton-only | UCF 68.8 ± 2.8 · XD 40.8 ± 0.6 |
| Visual-only CLIP | UCF 81.2 · XD 74.6 |
| Visual-only Giant | UCF 82.4 ± 0.2 · XD 76.8 ± 1.0 |
| Complementarity | 8/8 meet-or-exceed; 6/8 strictly positive + 2 ties; mean +0.6pp; tie-dropping sign p≈0.03 |
| TENT/SAR (3-seed continual) | worst \|Δ\| = 0.082pp < 0.1pp; per-backbone deltas as listed in Ch 6 spec |
| disc_reweight | mean +1.21pp; per-backbone +0.67±0.23 / +1.50±1.14 / +2.24±0.24 / +0.42±0.12; Source-only 63.7/57.0/58.9/62.8 |
| Pri-5 aggregations (keep distinct!) | Gaussian family 3-seed avg +4.83 (per backbone +2.67/+5.99/+8.95/+1.69); max +13.2 = SO400M gaussian severity-5 3-seed; s42-only Gaussian mean +3.31 is a DIFFERENT number |
| Efficiency | 0.50–1.02M trainable params; <5 min/config; single RTX 4090 |

### Forbidden sources (stale / superseded / fabricated)
- `paper/tables_generated.tex` (its own header says so; old single-seed rows, old Table 3).
- Phase 8/9/10/11 summary numbers (single-seed era; superseded by commit 33591ac).
- `REQUIREMENTS.md` EVAL traceability numbers (0.8227 / 71.92 / 0.9200 — pre-λ0, pre-full-length).
- Light-WVAD XD 77.3 (fabricated; removed in 260622-ukd; XD cell is `---`).
- Old phase6 C-series corruption heatmaps (pre-fix TTA data).
- Phase 4/4c-era per-category numbers for the CURRENT model (regenerate from run dirs).

### Honesty framings (preserve verbatim in meaning)
No SOTA claim; ~88–91% field-ceiling disclosure; fair-subset framing; TTA gains are
corrupted-AUC robustness only (never clean AUC); +13.2 labeled "single most-degraded
condition"; gains in "points" not "%"; transductive assumption disclosed; UCF λ2=8e-4
smoothness-implementation footnote (≤0.13pp) retained; 64-frame exclusion disclosures
retained; complementarity wording "small but consistent".

### SOTA external numbers — in-phase verification gate (user decision 2026-07-05)
The 15 inline `% RE-VERIFY` items from `sota_comparison_full.tex` and the 17-item
camera-ready checklist (`12-VERIFICATION.md`) are RESOLVED inside Phase 13, not carried
as debt: a primary-source verification workflow (Section 8, step 2b) checks every
flagged external number against the method's primary paper and produces an evidence
report; the user spot-approves it. Items that fail verification are corrected. Result
cells whose value CANNOT be confirmed in the primary source are OMITTED (cell becomes
`---`/N/A, or the row is dropped if its headline cells are unverifiable), with a
footnote explaining the omission — an unverified number never ships in the final
thesis. Secondary-detail mismatches (venue, author list) that don't affect the number
are corrected in place. Zero unresolved `% RE-VERIFY` comments may survive into the
final thesis source.

## 7a. Provenance manifest and tracked sources (binding)

`results/` is git-ignored wholesale (`.gitignore:9`) with only 28 force-tracked files;
several sources this spec names are currently UNTRACKED (`benchmark_models.csv`,
`backbone_bench_combined.csv`, all run-dir `per_category.csv`, all of
`_analysis_2026-06-10/`). A clean checkout must be able to reproduce the thesis audit,
so:

1. `thesis/PROVENANCE.md` is a tracked manifest mapping every numeric claim family and
   every figure/table to its source: tracked repo path (+ generating script where
   applicable). One row per source; no thesis number without a manifest row.
2. Every source named in the manifest MUST be tracked in git. Wave 0 tracks the missing
   ones with CORRECT gitignore mechanics — a bare `!results/foo` rule is dead while the
   parent dir is excluded by `results/` (`.gitignore:9`); git cannot re-include a file
   whose parent directory is excluded. Required sequence: change `results/` to
   `results/*`, then `!results/<subdir>/` + `!results/<subdir>/**` (or exact-file `!`
   rules) per needed path — OR `git add -f` each file (existing project practice; 28
   files already tracked this way). Either way, Wave 0 MUST assert with
   `git ls-files --error-unmatch <path>` (and `git check-ignore -v` for diagnostics)
   that every manifest source is actually tracked — no silent failure. This also
   discharges open review item C7-3. Expected additions: the two benchmark CSVs,
   `_analysis_2026-06-10/` artifacts (Pri-5/6/7/9 CSVs/JSONs/MDs + score histogram),
   and `per_category.csv` + `eval_metrics.json` for exactly the canonical run dirs the
   thesis cites (small text files; only cited runs, not all 141 dirs).
3. The adversarial number audit (Section 8, step 2) FAILS any number whose manifest
   source is missing, untracked, or mismatched.

## 8. Build and verification

1. `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean`
   compiles `thesis/main.pdf` with zero LaTeX errors, zero undefined references,
   zero undefined citations (assert by scanning the .log).
2. **Adversarial number audit** (same standard as Phase 12's 4 audits): every numeric
   claim in the thesis traced through `thesis/PROVENANCE.md` to a tracked canonical
   source (main.tex inlined tables, results-index.csv, run-dir CSV/JSON,
   `_analysis_2026-06-10/` artifacts, verified planning docs). Multi-agent verification
   workflow; audit FAILS on any untracked or manifest-missing source; findings fixed
   before done.
2b. **Primary-source verification gate (external SOTA numbers)**: for each RE-VERIFY
   item and 12-VERIFICATION checklist item (incl. #16/#17 PI-VAD/DSANet bib
   status/authors), agents fetch the primary paper and confirm the cited number, venue,
   metric definition, and author list; output = evidence report (per-item quote + URL +
   verdict) saved under `.planning/phases/13-*/`. User spot-approves the report.
   Failed items corrected; unverifiable items get a visible footnote. No `% RE-VERIFY`
   comment survives in `thesis/`.
3. Headline-consistency check: 82.5 / 78.7 identical in abstract, chapters, tables,
   conclusion.
4. Overclaim scan: honesty framings present; no disallowed claims (SOTA, online TTA,
   clean-AUC TTA gains).
5. Structure check: TOC matches this spec; every figure/table referenced from prose;
   every chapter present.
6. Repo hygiene: `pytest` suite stays green (no production code changes expected;
   figure-regeneration scripts are additive); build artifacts git-ignored.

## 9. Execution plan

Per CLAUDE.md GSD enforcement, implementation runs as **GSD Phase 13 — Full Thesis
Manuscript** (added via `/gsd:phase`, planned via `/gsd:plan-phase`, executed via
`/gsd:execute-phase`), with this spec as the phase's context input. Expected wave shape:

- **Wave 0:** thesis skeleton + preamble + vendored IEEEtranN.bst + non-interactive
  build script + bib superset + `.gitignore` un-ignore rules + PROVENANCE.md scaffold +
  figure regeneration/provenance pass (zero-GPU).
- **Wave 1:** chapter drafting (parallel writers per chapter, each seeded with this
  spec's guardrails + pointed sources).
- **Wave 2:** appendices + frontmatter; primary-source verification workflow for
  external SOTA numbers (Section 8, step 2b) runs in parallel.
- **Wave 3:** integration (cross-references, notation consistency), adversarial number
  audit against PROVENANCE.md, overclaim scan, RE-VERIFY resolution merge, final clean
  build.

User checkpoints: after Wave 0 (skeleton compiles), after Wave 1 (chapter drafts),
spot-approval of the SOTA evidence report, final.

## 10. Out of scope

- Chinese abstract, committee/cover pages beyond the generic title page.
- Defense slide deck (separate later task).
- Any GPU experiment; any change to headline numbers (incl. Pri-3 XD smoothing).
- Any modification to `paper/` or its build.
- University-template re-skinning (structure kept re-skin-friendly).

## 11. Success criteria

1. `thesis/main.pdf` builds clean via `build_thesis.ps1 -Clean`; 90–120 pages;
   9 chapters + 6 appendices + frontmatter per this spec.
2. All content listed in Section 4 present; no `\todo`, no placeholder prose
   (acknowledgments placeholder exempt).
3. Number audit passes: zero untraceable numbers, zero forbidden-source values,
   headlines byte-consistent; every manifest source tracked in git (clean checkout
   reproduces the audit).
4. All figures either verified-current or regenerated from committed data;
   no stale-provenance figure included.
5. Honesty framings intact (Section 7 list).
6. Primary-source verification gate passed: evidence report user-approved; zero
   unresolved `% RE-VERIFY` comments and zero bib TODOs in `thesis/`; zero unverified
   external numbers in any table (unverifiable cells omitted as `---`/N/A with a
   footnote explaining the omission).
7. `thesis/main.pdf` builds from the repo on MiKTeX with default on-demand package
   install (the paper-build baseline): vendored .bst, non-interactive build script,
   preflight that names any missing package; every figure is provenance Class R or
   Class V per Section 5.
