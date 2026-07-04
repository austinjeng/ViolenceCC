# Thesis Provenance Manifest

**Created:** 2026-07-05 (Phase 13, plan 13-02) · **Governing rule:** spec §7a of
`docs/superpowers/specs/2026-07-05-full-thesis-design.md` (binding)

## 1. Purpose and conventions

Every number family, figure, and table rendered in `thesis/` must trace to a
**git-tracked** source through this manifest. The Wave-3 adversarial number audit
(Phase-12 standard, `12-VERIFICATION.md` traceability-table format) FAILS any number
whose manifest source is untracked. Local checkpoints and `E:\` feature caches are
NOT valid provenance sources (they may be regeneration *inputs* only).

**Path conventions:**
- Source cells use backtick-quoted repo-relative paths. Compact families use bash
  brace patterns (e.g. `results/{ucf,xd}_skeleton_only_s{42,123,2024}/eval_metrics.json`);
  auditors expand with bash brace expansion and assert each expanded path via
  `git ls-files --error-unmatch <path>`.
- Line anchors like (L226–242) refer to the file as of Phase-13 Wave 0
  (`paper/` is frozen this phase, so anchors are stable).
- Every source path in §2 was individually asserted tracked
  (`git ls-files --error-unmatch`, exit 0) when this manifest was created (13-02).

**LaTeX preflight required-package list** (`scripts/build_thesis.ps1` report-only
check; MiKTeX installs on demand via `--enable-installer`): natbib, booktabs,
multirow, graphicx, tikz/pgf, hyperref, geometry, setspace, caption, subcaption,
microtype, amsmath, amssymb, array — plus lmodern (added by 13-01: scalable fonts
required by microtype font expansion under the report class).

**Vendored bibliography style provenance:** `thesis/IEEEtranN.bst` — copied from
local MiKTeX feupphdteses package; authentic Michael Shell header v1.13 2008/09/30.
Byte-identity protected against autocrlf rewriting by `.gitattributes` (`-text`).

## 2. Number-family table (canonical values → tracked sources)

Values are verbatim from the frozen anchor table (spec §7, consolidated in
`13-RESEARCH.md` §2). These are the ONLY permitted values for their families.

| # | Family | Canonical value | Tracked source path(s) | Notes |
|---|--------|-----------------|------------------------|-------|
| 1 | UCF headline | **82.5 ± 0.4 AUC** (Gated Fusion, SigLIP2 Giant, seeds 42/123/2024) | `paper/main.tex` tab:ucf-ablation (L226–242); `results/ucf_gated_fusion_giant_s{42,123,2024}/eval_metrics.json` | headline variant is Gated Fusion DEFAULT pooling (see row 7 note) |
| 2 | XD headline | **78.7 ± 0.9 AP** (Gated Fusion, SigLIP2 SO400M) | `paper/main.tex` tab:xd-ablation (L245–261); `results/xd_gated_fusion_so400m_s{42,123,2024}/eval_metrics.json` | same headline-variant rule |
| 3 | Skeleton-only | UCF 68.8 ± 2.8 · XD 40.8 ± 0.6 | `paper/main.tex` Tables 1–2; `results/{ucf,xd}_skeleton_only_s{42,123,2024}/eval_metrics.json` | supersedes single-seed 71.8/41.3 (forbidden, §4) |
| 4 | Visual-only CLIP | UCF 81.2 · XD 74.6 | `paper/main.tex` Tables 1–2; `results/{ucf,xd}_clip_only_s{42,123,2024}/eval_metrics.json` | |
| 5 | Visual-only Giant | UCF 82.4 ± 0.2 · XD 76.8 ± 1.0 | `paper/main.tex` Tables 1–2; `results/{ucf,xd}_clip_only_giant_s{42,123,2024}/eval_metrics.json` | |
| 6 | Late fusion | UCF max 79.9±0.8 (CLIP 78.9 < visual-only 81.2); XD collapses 63.6–65.7 (CLIP gated-vs-late gap 12.6pp: 76.5 vs 63.9) | `paper/main.tex` Tables 1–2; `results/{ucf,xd}_late_fusion{,_siglip2,_so400m,_giant}_s{42,123,2024}/eval_metrics.json` | |
| 7 | GF 2-Person | UCF 82.6±0.3 (Giant) · XD 79.2±0.3 (SO400M) | `paper/main.tex` Tables 1–2; `results/ucf_gated_fusion_giant_2person_s{42,123,2024}/eval_metrics.json`; `results/xd_gated_fusion_so400m_2person_s{42,123,2024}/eval_metrics.json` | **NOT the headline** despite nominally highest cells (Pitfall 10) — never silently promote |
| 8 | GF pooling ablations (full grid) | per Tables 1–2 (2-Person and CLIP-Mean rows, all backbones) | `paper/main.tex` Tables 1–2; `results/{ucf,xd}_gated_fusion{,_siglip2,_so400m,_giant}_2person_s{42,123,2024}/eval_metrics.json`; `results/{ucf,xd}_gated_fusion{,_siglip2,_so400m,_giant}_clip_mean_s{42,123,2024}/eval_metrics.json`; `results/{ucf,xd}_gated_fusion{,_siglip2,_so400m,_giant}_s{42,123,2024}/eval_metrics.json` | default pooling wins on XD (2-person −0.90 AP, CLIP mean-only −2.32 AP) |
| 9 | Complementarity | 8/8 meet-or-exceed; 6/8 strictly positive + 2 ties; mean +0.6pp; tie-dropping sign test **p≈0.03** | `paper/main.tex` L263 (prose) + Tables 1–2 (underlying cells) | USE the paper's p≈0.03 wording; the per-run p≈0.008 variant (STATE.md) only if explicitly distinguishing tests (Pitfall 11); framing: "small but consistent" |
| 10 | TENT/SAR (3-seed continual) | worst \|Δ\| = 0.082pp < 0.1pp; ΔTENT/ΔSAR per backbone: CLIP +0.021/+0.024 · Base −0.082/−0.077 · SO400M −0.050/−0.051 · Giant +0.011/+0.012 | `results/_tta_rerun_continual/summary_3seed.json` | null result; transductive/continual protocol disclosed |
| 11 | disc_reweight | mean **+1.21pp**; per backbone +0.67±0.23 / +1.50±1.14 / +2.24±0.24 / +0.42±0.12 (CLIP/Base/SO400M/Giant); Source-only 63.7/57.0/58.9/62.8; Ours 64.4/58.5/61.1/63.3; all-positive 12/12 cells (min +0.27) | `paper/main.tex` tab:tta (L301–316); `results/_coral_derisk/r1full_{base,clip,giant,so400m}.json`; `results/_coral_derisk/variants/v_{base,clip,giant,so400m}_{s42_train,s123_test,s2024_test}.json` | corrupted-AUC robustness gains ONLY, never clean AUC; gains in "points" not "%" |
| 12 | Pri-5 aggregations (KEEP DISTINCT) | Gaussian family 3-seed cross-backbone avg **+4.83** (per backbone +2.67/+5.99/+8.95/+1.69) · max **+13.2** = SO400M gaussian severity-5 3-seed (per-seed 13.92/12.34/13.31) · s42-only Gaussian mean **+3.31** (different number) · Base s42 gaussian_5 = **−3.20** (single-seed disclosure) · non-Gaussian families **0.00 BY CONSTRUCTION** | `results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv`; `results/_analysis_2026-06-10/pri5_tta_breakdown.md`; `results/_analysis_2026-06-10/pri5_tta_breakdown.tex`; `paper/main.tex` tab:tta_breakdown (L340–357) | +13.2 labeled "single most-degraded condition"; 0.00 = "gate routes to source", NEVER "TTA hurts"; never reintroduce raw +13.9 (Pitfall 6) |
| 13 | Phase-5 per-condition bests (episodic grid, historical) | TENT +3.81pp (jpeg s2) · SAR +5.38pp (gaussian s5) | `results/results-index.csv` (680 TTA rows: 460 sar / 140 tent / 80 source_only) | per-condition BESTS from the 500-run grid, not means; episodic pre-continual protocol |
| 14 | Episodic inertness | 98.4% of UCF test videos ≤32 snippets | `paper/main.tex` §4.5 (L327–335) | motivates the continual protocol |
| 15 | TTA adapted params | 1,536 (3 LN modules, 6 tensors) | `paper/main.tex` §4.5 (sec:tta) | |
| 16 | Bootstrap CIs (Pri-6, s42-only) | UCF 82.49 CI [75.63, 88.02] width 12.39pp · XD 79.74 CI [76.62, 82.68] width 6.06pp (B=2000, seed 12345) | `results/_analysis_2026-06-10/pri6_bootstrap_ci.json`; `results/_analysis_2026-06-10/pri6_bootstrap_ci.md` | video-level resampling; s42-only caveat stated; frame as field-wide test-set-size uncertainty |
| 17 | Pri-7 per-class complementarity | HM +0.31±1.08 (7/10 pos) · APP −0.29±0.16 · HM−APP +0.60pp · Shooting +1.05±0.20 (n=22) | `results/_analysis_2026-06-10/pri7_per_class_complementarity.csv`; `results/_analysis_2026-06-10/pri7_per_class_complementarity.md` | hedge EXACTLY "directionally supportive but mixed/noisy"; NO Welch t-test |
| 18 | Pri-9 failure analysis | anomaly mean 0.874 / normal mean 0.382 / normal p75 0.986 | `results/_analysis_2026-06-10/pri9_failure_cases.json`; `results/_analysis_2026-06-10/pri9_failure_cases.md` | do NOT cite stored video_auc (0.9268 vs 0.9452 recompute discrepancy — deferred) |
| 19 | Sweep (historical configuration only) | XD +3.72pp 3-seed (lr=1e-3/k=2, 74.69 vs 70.98) · UCF +0.14pp (insensitive) | `results/results-index.csv` (~206 sweep rows); `scripts/generate_phase7_charts.py` (generator, historical-baseline guard) | sweep-era CLIP backbone, pre-λ0, s42 baselines — never chain to 82.5/78.7 (Pitfall 3) |
| 20 | RTFM repro (App A) | AP 0.6570 vs 77.81 anchor (−11.11pp); Flow-swap AP 0.5916 (−6.54pp, 100% coverage) | `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md`; `.planning/phases/07-xd-violence-hyperparameter-sweep/07-VERIFICATION.md`; `results/xd_i3d_rtfm_i3d_s42/{per_category.csv,eval_metrics.json}`; `results/xd_i3d_rtfm_i3d_flow_s42/{per_category.csv,eval_metrics.json}` | RTFM diagnostics cite tracked 07-VERIFICATION.md (the phase7 JSON/summary files no longer exist — §4) |
| 21 | Efficiency | 0.50–1.02M trainable params; <5 min/config; single RTX 4090 | `results/benchmark_models.csv`; `results/backbone_bench_combined.csv`; `paper/main.tex` §5 (L374) | the 0.50–1.02M range = head params across 4 backbones (paper §5 prose anchor); benchmark_models.csv covers CLIP-backbone heads |
| 22 | Dataset facts | UCF 1,900 videos / 13 categories / 800+810 train / 150+140 test / **254 evaluated** (64-frame minimum); XD 4,754 / 6 categories / 3,954 train / 800 test; 172 UCF + 1 XD videos <64 frames excluded | `paper/main.tex` L136 / L206 (exact disclosure sentences); `data/ucf_total_frames.json` (UCF full-length eval manifest, 1900 videos) | lift the two disclosure sentences verbatim (Pitfall 8) |
| 23 | PRD gates (disclosed misses) | UCF min 83 (target 85–87) · XD min 80 (target 82–85) · RTFM 84.30±1% | `.planning/STATE.md` (PRD gate rows, L52–60) | state misses plainly (Ch 8) |
| 24 | Corruption severity parameters | σ [0.08,0.12,0.18,0.26,0.38]; JPEG quality [25,18,15,10,7]; brightness ADDITIVE [0.1–0.5]; motion blur (kernel,σ) [(10,3),(15,5),(15,8),(15,12),(20,15)] | `scripts/corruption.py` (lines 38–42; `SKELETON_REEXTRACT_TYPES` at line 30) | NOT CLAUDE.md's stale pre-implementation lists (Pitfall 5); skeleton re-extraction only for motion_blur + jpeg_compression |

## 3. Figures & tables (populated by 13-04)

Classes per spec §5: **Class R** = regenerated by a tracked script from tracked
data (cell records the regen command); **Class V** = committed binary under
`thesis/figures/` + verification note (what it was checked against, and when).
Local checkpoints / `E:\` features are never valid sources for either class.

| Asset | Kind | Class (R/V) | Tracked source(s) | Regen command (R) / Verification note (V) |
|-------|------|-------------|-------------------|--------------------------------------------|
| _(populated by 13-04 figure regeneration/provenance pass)_ | | | | |

## 4. Forbidden-sources appendix (audit is self-contained)

Writers must NEVER read numbers from these (spec §7 verbatim list + Pitfall 13):

- `paper/tables_generated.tex` — its own header says stale; old single-seed rows, dead Table-3 format.
- Phase 8/9/10/11 summary numbers (single-seed era; superseded by commit 33591ac). Includes 11-04's "UCF best 83.6", "GF Giant 83.3±0.3", "skeleton 71.8/41.3"; Phase-10's "Giant 83.28/83.23".
- `REQUIREMENTS.md` EVAL traceability numbers (0.8227 / 71.92 / 0.9200 — pre-λ0, pre-full-length). Sole exception: 0.8227/0.7192 may appear in the sweep section / Appendix C as explicitly-labeled historical sweep-era baselines, never as current results.
- Light-WVAD XD 77.3 (fabricated; removed in quick 260622-ukd; the XD cell is `---`). Also stale inside `12-RESEARCH-sota.md` §8 and `12-VERIFICATION.md`'s traceability table — both predate the fix.
- Old phase6 C-series corruption heatmaps (C01–C06 in `results/phase6_charts/C_corruption/`) — pre-dropout-fix episodic TTA data.
- Phase 4/4c-era per-category numbers for the current model (e.g. Fighting 0.955 / Assault 0.985 / XD Riot 88.15 / Abuse 44.89) — regenerate from the tracked post-λ0/post-h1 `per_category.csv` files (§2 rows 1–8, 20).
- CLAUDE.md corruption-parameter lists (stale pre-implementation research; real values = §2 row 24).

**Missing-on-disk paths (Pitfall 13) — must never appear as manifest sources:**
`results/phase7_charts/` (absent pre-regeneration; Wave-0 regen writes here),
`results/phase7_summary.md`, `results/phase7_rtfm_gap_diagnostic.json`,
`results/phase4_charts/` — none of these exist on disk; RTFM diagnostics cite the
tracked `07-VERIFICATION.md`, sweep charts are regenerated from `results-index.csv`.
