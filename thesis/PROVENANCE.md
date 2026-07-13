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

All rows below were populated by 13-04 (2026-07-05). Regen commands run from the
repo root in the vcc-main environment (`C:/Anaconda/envs/vcc-main/python.exe`).
Class-V "regenerated" figures used local checkpoints / `E:\` feature caches /
untracked `eval_scores.npz` as regeneration *inputs* only — every such input was
first validated against a tracked anchor as recorded in its note.

| Asset | Kind | Class (R/V) | Tracked source(s) | Regen command (R) / Verification note (V) |
|-------|------|-------------|-------------------|--------------------------------------------|
| `thesis/figures/fig_architecture.tex` | figure (TikZ) | Class R | the file itself (byte-identical copy of `paper/figures/fig_architecture.tex`; cmp exit 0 at 13-01) | tracked TeX source, no data inputs; `\input` + `\resizebox{\textwidth}{!}` in ch03 |
| `thesis/figures/fig_severity_heatmap.pdf` | figure | Class R | `scripts/thesis_severity_heatmap.py` ← `results/_coral_derisk/r1full_{clip,base,so400m,giant}.json` + `results/_coral_derisk/variants/v_{clip,base,so400m,giant}_{s123_test,s2024_test}.json` (+ `results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv` as hard cross-check) | `python scripts/thesis_severity_heatmap.py` — self-checks +13.2 anchor cell (SO400M gaussian_5 3-seed) and +4.826 Gaussian family avg before writing |
| `thesis/figures/fig_corruption_source.pdf` | figure | Class R | `scripts/thesis_corruption_heatmaps.py` ← same r1full/variants set + `results/_tta_rerun_continual/summary_3seed.json` | `python scripts/thesis_corruption_heatmaps.py` — self-checks source-only means 63.71/57.01/58.87/62.83 vs summary_3seed.json |
| `thesis/figures/fig_corruption_disc_reweight.pdf` | figure | Class R | same as `fig_corruption_source.pdf` | same command — self-checks disc_reweight gains +0.67/+1.50/+2.24/+0.42 |
| `thesis/tables/tab_percat_ucf.tex` | table | Class R | `scripts/thesis_per_category_tables.py` ← `results/ucf_gated_fusion_giant_s{42,123,2024}/per_category.csv` | `python scripts/thesis_per_category_tables.py` — 13 categories, 3-seed mean±std, post-λ0/post-h1; asserts forbidden Phase-4-era literals absent |
| `thesis/tables/tab_percat_xd.tex` | table | Class R | `scripts/thesis_per_category_tables.py` ← `results/xd_gated_fusion_so400m_s{42,123,2024}/per_category.csv` | same command — 6 categories, AP %, 3-seed mean±std |
| `thesis/tables/tab_percat_rtfm.tex` | table | Class R | `scripts/thesis_per_category_tables.py` ← `results/xd_i3d_rtfm_i3d_s42/per_category.csv` + `results/xd_i3d_rtfm_i3d_flow_s42/per_category.csv` | same command — 6 categories, AP %, s42-only (RTFM repro, App A) |
| `thesis/figures/fig_sweep_s01_ucf.png` | figure | Class R | `scripts/generate_phase7_charts.py` ← `results/results-index.csv` | `python scripts/generate_phase7_charts.py` then copy `results/phase7_charts/S04_sweep_heatmap_auc.png`. **HISTORICAL-BASELINE GUARD:** chart embeds the 2026-05 sweep-era baseline 0.8227 (CLIP backbone, pre-λ0, s42) as a "P4 baseline" annotation — captions must label it historical-configuration-only, never chain to 82.5 |
| `thesis/figures/fig_sweep_s02_xd.png` | figure | Class R | `scripts/generate_phase7_charts.py` ← `results/results-index.csv` | same command, copy `results/phase7_charts/S01_sweep_heatmap_ap.png`. Same guard: embedded 0.7192 "P4c baseline" is sweep-era historical, never chain to 78.7 |
| `thesis/figures/fig_temporal_scores.pdf` | figure | Class V | byte-identical to `paper/figures/fig_temporal_scores.pdf` (cmp exit 0); generator `scripts/generate_pub_figures.py` (`fig_temporal_scores`) ← `results/ucf_{gated_fusion,clip_only,skeleton_only}_s42/eval_scores.npz` + `data/annotations/ucf_temporal.txt` | REGENERATED 2026-07-13 (quick 260713-mkh, C1 erratum fix): curve video is now **Fighting047** (Fighting), pinned explicitly and also selected by the new positive-alignment filter (in-GT gated mean 0.889 vs out-GT 0.407, gap +0.483). Supersedes the RoadAccidents127 erratum (gap −0.742, worst-aligned test video). Command: `python scripts/generate_pub_figures.py` (temporal panel), copied byte-identical to `paper/figures/` |
| `thesis/figures/fig_backbone_comparison.pdf` | figure | Class V | byte-identical to `paper/figures/fig_backbone_comparison.pdf` (cmp exit 0); generator `scripts/generate_pub_figures.py` | true 3-seed since quick 260622-uuu (commit 2e6cb6b), where all 24 plotted cells were checked ≤0.05pp against paper Tables 1/2 — that check is cited here, not re-measured (figure byte-unchanged since) |
| `thesis/figures/fig_tta_comparison.pdf` | figure | Class V | byte-identical to `paper/figures/fig_tta_comparison.pdf` (cmp exit 0); anchors `results/_tta_rerun_continual/summary_3seed.json` + `results/_coral_derisk/r1full_*.json` | RE-VERIFIED 2026-07-05: per-backbone source means recomputed from summary_3seed.json = 63.7097/57.0052/58.8681/62.8276 → plotted 63.7/57.0/58.9/62.8 (match); "Ours" bars 64.4/58.5/61.1/63.3 and deltas +0.67/+1.50/+2.24/+0.42 match the tracked disc_reweight anchors (§2 row 11); TENT/SAR means also recomputed (63.73/56.92/58.82/62.84 — null result, not plotted) |
| `thesis/figures/fig_gating_distribution.pdf` | figure | Class V | byte-identical to `paper/figures/fig_gating_distribution.pdf` (cmp exit 0); anchors: 6 tracked `results/{ucf,xd}_{skeleton_only,clip_only,gated_fusion}_s42/eval_metrics.json` | verified 2026-07-05: despite its name this is a per-category AUC/AP bar chart (Skeleton/Visual/Gated); all plotted bars match the tracked canonical post-λ0/post-h1 per_category values (spot-checked across both datasets and all three variants, e.g. XD Gated Abuse 43.4 / Riot 91.5 / Fighting 77.9; UCF Skeleton Fighting 66.6 / Robbery 63.5) |
| `thesis/figures/pri9_score_hist.png` | figure | Class V | byte-identical to tracked `results/_analysis_2026-06-10/pri9_score_hist.png` (cmp exit 0); generator `scripts/analyze_pri9_failure_cases.py` | copied 2026-07-05; giant-s42 provenance (Pri-9 failure analysis, §2 row 18); do NOT cite the stored video_auc (known 0.9268 vs 0.9452 recompute discrepancy, deferred) |
| `thesis/figures/fig_skeleton_overlay_b01.png` | figure | Class V | committed binary (this file); drawing code `scripts/generate_phase6_charts.py` | byte-identical copy (cmp exit 0, 2026-07-05) of phase-6 `B01_Salt.2010__#00-17-40_00-18-16_label_B1-0-0_f697.png` (May 2026), renamed LaTeX-safe; RTMPose COCO-17 overlay on an XD source frame — independent of eval scores/checkpoints, so the λ0/h1 fixes cannot stale it; XD-only BY NECESSITY (UCF source frames are 64×64 PNGs — App F documents the limitation) |
| `thesis/figures/fig_skeleton_overlay_b02.png` | figure | Class V | committed binary; drawing code `scripts/generate_phase6_charts.py` | same verification as b01; source `B02_Tropa.de.Elite.2.2010__#00-42-00_00-43-00_label_B2-0-0_f838.png` |
| `thesis/figures/fig_skeleton_overlay_b03.png` | figure | Class V | committed binary; drawing code `scripts/generate_phase6_charts.py` | same verification as b01; source `B03_Salt.2010__#00-17-40_00-18-16_label_B1-0-0_f613.png` |
| `thesis/figures/fig_temporal_extra_ucf_shooting008.png` | figure | Class V | `scripts/generate_phase6_charts.py` (section A) + anchors: 8 tracked `results/{ucf,xd}_{skeleton_only,clip_only,late_fusion,gated_fusion}_s42/eval_metrics.json` | REGENERATED 2026-07-05 from the 8 local s42 `eval_scores.npz` dumps after validating each: frame-level AUC/AP recomputed from npz + tracked annotations matches the tracked canonical eval_metrics.json EXACTLY (diff 0.00e+00, all 8 runs) — the npz dumps are the canonical post-λ0/post-h1 score dumps |
| `thesis/figures/fig_temporal_extra_ucf_explosion033.png` | figure | Class V | same as shooting008 row | same regeneration + validation (2026-07-05) |
| `thesis/figures/fig_temporal_extra_xd_blackhawkdown.png` | figure | Class V | same as shooting008 row | same regeneration + validation (2026-07-05); source video `Black.Hawk.Down.2001__#01-42-58_01-43-58_label_G-0-0` |
| `thesis/figures/fig_gate_by_category_ucf.png` | figure | Class V | `scripts/generate_phase6_charts.py` (section D) + anchor `results/ucf_gated_fusion_s42/eval_metrics.json` | REGENERATED 2026-07-05 from the local `ucf_gated_fusion_s42` checkpoint after verifying it: official `src/evaluate.py` CLI on a scratch copy reproduces the tracked canonical auc/ap EXACTLY (0.816687/0.218262, diff 0.00e+00); gate values sigmoid-bounded [0.037, 0.939]; includes the 13-04 fix classifying UCF's 150 in-annotation Normal videos correctly |
| `thesis/figures/fig_gate_by_category_xd.png` | figure | Class V | `scripts/generate_phase6_charts.py` (section D) + anchor `results/xd_gated_fusion_s42/eval_metrics.json` | same protocol: local `xd_gated_fusion_s42` (post-λ0) checkpoint reproduces tracked 0.923606/0.766164 exactly (diff 0.00e+00); gates [0.024, 0.966] |
| `thesis/figures/fig_gate_histogram_ucf.png` | figure | Class V | same as fig_gate_by_category_ucf | same checkpoint verification (2026-07-05) |
| `thesis/figures/fig_gate_histogram_xd.png` | figure | Class V | same as fig_gate_by_category_xd | same checkpoint verification (2026-07-05) |
| `thesis/figures/fig_tsne_ucf.png` | figure | Class V | `scripts/generate_phase6_charts.py` (section E) + anchor `results/ucf_gated_fusion_s42/eval_metrics.json` | REGENERATED 2026-07-05 from the same verified checkpoint (fused ln_fused features, mean-pooled per video, TSNE seed 42); includes the 13-04 fix — the 150 Normal videos now render as grey points (previously invisible) |
| `thesis/figures/fig_tsne_xd.png` | figure | Class V | `scripts/generate_phase6_charts.py` (section E) + anchor `results/xd_gated_fusion_s42/eval_metrics.json` | same protocol (2026-07-05), 800 test videos |
| `thesis/figures/fig_category_scores_ucf.png` | figure | Class V | `scripts/generate_phase6_charts.py` (chart F02) + anchor `results/ucf_gated_fusion_s42/eval_metrics.json` | REGENERATED 2026-07-05 from the validated `ucf_gated_fusion_s42/eval_scores.npz` (see temporal-extra rows: npz validated exactly vs tracked metrics); per-category frame-score box plots, abnormal videos only |
| `thesis/figures/fig_category_scores_xd.png` | figure | Class V | `scripts/generate_phase6_charts.py` (chart F03) + anchor `results/xd_gated_fusion_s42/eval_metrics.json` | same protocol (2026-07-05) |

### 3a. Phase-6 PNG disposition record (13-04, 2026-07-05)

All 20 non-C phase-6 PNGs (`results/phase6_charts/`, single-seed era May 2026,
untracked) received an explicit disposition. C-series (C01–C06) is FORBIDDEN
(§4) — zero C-series files entered `thesis/figures/` (grep gate: 0 matches).

| Old asset | Disposition | Detail |
|-----------|-------------|--------|
| A01_Shooting008 | REGENERATED-V → `fig_temporal_extra_ucf_shooting008.png` | fresh curves from validated npz (post-h1 full-length UCF eval) |
| A02_Arrest007 | DROPPED | current data no longer selects Arrest007 (post-h1 selection: Shooting008/Shooting032/Explosion033); regenerated A02=Shooting032 excluded as category-redundant with A01 under the App-F 2–3 budget |
| A03_Shooting032 | DROPPED | regenerated successfully but category-redundant with Shooting008; App-F budget |
| A04_Salt.2010 (B1) | DROPPED | current data no longer selects this video (post-λ0 XD selection: GoldenEye/Black.Hawk.Down); regenerated A04=GoldenEye excluded as category-redundant with A05 |
| A05_Tropa.de.Elite.2 (B2) | DROPPED (superseded) | replaced by REGENERATED-V `fig_temporal_extra_xd_blackhawkdown.png` (current post-λ0 selection) |
| B01_Salt.2010_f697 | INCLUDED-V → `fig_skeleton_overlay_b01.png` | byte-identical; overlays independent of eval scores; XD-only (UCF frames 64×64) |
| B02_Tropa_f838 | INCLUDED-V → `fig_skeleton_overlay_b02.png` | same |
| B03_Salt.2010_f613 | INCLUDED-V → `fig_skeleton_overlay_b03.png` | same |
| D01_gate_by_category_ucf | REGENERATED-V → `fig_gate_by_category_ucf.png` | checkpoint verified exactly vs tracked metrics; + Normal-classification fix |
| D01_gate_by_category_xd | REGENERATED-V → `fig_gate_by_category_xd.png` | post-λ0 checkpoint verified exactly |
| D02_gate_histogram_ucf | REGENERATED-V → `fig_gate_histogram_ucf.png` | old version showed a single class (UCF Normal-classification bug); fixed + regenerated |
| D02_gate_histogram_xd | REGENERATED-V → `fig_gate_histogram_xd.png` | checkpoint verified exactly |
| E01_tsne_ucf | REGENERATED-V → `fig_tsne_ucf.png` | old version silently omitted all 150 Normal videos (same bug); fixed + regenerated |
| E01_tsne_xd | REGENERATED-V → `fig_tsne_xd.png` | checkpoint verified exactly |
| F01_cross_dataset_comparison | DROPPED | s42-only bar chart duplicating Tables 1–2 cells at single-seed precision; canonical 3-seed tables are the thesis presentation |
| F02_ucf_category_scores | REGENERATED-V → `fig_category_scores_ucf.png` | from validated npz (adds frame-score distribution info not in tables) |
| F03_xd_category_scores | REGENERATED-V → `fig_category_scores_xd.png` | same |
| F04_seed_stability | DROPPED | 2-bar chart duplicating the CLIP-backbone gated 3-seed mean±std already in Tables 1–2 |
| F05_ucf_ablation_bars | DROPPED | s42-only ablation bars embed single-seed-era numbers superseded by the Pri-1 3-seed tables (RESEARCH: almost certainly stale) |
| F06_xd_ablation_bars | DROPPED | same reason as F05 |

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
