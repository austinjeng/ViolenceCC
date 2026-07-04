# Phase 13: Full Thesis Manuscript - Research

**Researched:** 2026-07-05
**Domain:** LaTeX thesis assembly (report class, MiKTeX/Windows), source-inventory consolidation, provenance tracking. Zero-GPU writing phase.
**Confidence:** HIGH (nearly every claim verified against the repo in this session)

## Summary

Phase 13 writes the full-length master's thesis (`thesis/`, 9 chapters + appendices A–F, 90–120 pages) from an already-approved binding spec (`docs/superpowers/specs/2026-07-05-full-thesis-design.md`). This is a writing + zero-GPU tooling phase: no new experiments, no headline changes, `paper/` frozen. The core planning inputs are (a) an exact per-chapter source inventory so parallel chapter writers get precise pointers, (b) a frozen canonical-numbers table with all precision traps, (c) a git-tracking audit producing the exact Wave-0 file list, (d) a figure provenance worksheet, (e) the external-SOTA verification worklist, (f) the bib plan, and (g) LaTeX build mechanics. All of these are consolidated below — **this document supersedes the session-scoped scratchpad ctxmap entirely; no downstream agent should reference `C:\Users\...\scratchpad\ctxmap\`**.

Everything named by the spec was verified to exist on disk this session. Key verified facts: 28 files tracked under the otherwise-gitignored `results/` (`.gitignore` line 9 = `results/`); the 128 canonical run dirs all exist with `per_category.csv` + `eval_metrics.json`; `results/_analysis_2026-06-10/` has exactly 11 files (all untracked); the two benchmark CSVs exist untracked; `paper/sota_comparison_full.tex` carries 13 row-level `% RE-VERIFY` flags (lines 104–125) + 2 meta mentions; `IEEEtranN.bst` resolves locally only via the unrelated `feupphdteses` MiKTeX package and is the authentic Michael Shell natbib variant v1.13 (2008/09/30); MiKTeX latexmk + Strawberry Perl + vcc-main plotting stack are all present; `scripts/corruption.py:38–42` holds the real ImageNet-C severity parameters, which **contradict the stale parameter lists in CLAUDE.md** (a newly-found stale-number trap, documented in §8 below).

**Primary recommendation:** Plan Wave 0 exactly as the spec's §9 wave shape, with the Wave-0 tracked-file list in §3 below copied verbatim into the plan; seed every Wave-1 chapter writer with §1 (its chapter's source rows) + §2 (canonical numbers + forbidden sources) of this document.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

ALL decisions are locked in the spec (`docs/superpowers/specs/2026-07-05-full-thesis-design.md` — approved 2026-07-05, 4 review rounds closed). The spec is the single source of truth; CONTEXT.md indexes it. Do not re-litigate. Summary of the locked set:

- **Format & layout (spec §2 D1–D2, §3):** Clean generic `report`-class LaTeX (12pt, a4paper, oneside), no university template; English throughout; no Chinese abstract. Layout: `thesis/main.tex` + `preamble.tex` + `frontmatter/` + `chapters/ch01..ch09.tex` + `appendices/appA..appF.tex` + `references.bib` + vendored `IEEEtranN.bst` + `PROVENANCE.md` + `figures/`. Bibliography: BibTeX, vendored IEEEtranN.bst + natbib [numbers]. `scripts/build_thesis.ps1`: non-interactive by default (NO Invoke-Item), `-Open` opt-in, `-Clean` flag; preflight HARD-asserts only vendored .bst, package resolution report-only. Equations lifted verbatim from paper (code-verified); never alter the math.
- **Numbers (spec §2 D3, §7):** FREEZE — canonical verified anchors only: UCF 82.5±0.4 AUC (Gated/Giant), XD 78.7±0.9 AP (Gated/SO400M); full anchor table in spec §7 (copied in §2 below). Forbidden sources list (copied verbatim in §2 below). Pri-5 aggregation traps: +4.83 ≠ +3.31 ≠ +8.95 ≠ +13.2 — keep distinct. Honesty framings preserved: no SOTA claim, ~88–91% field ceiling, transductive TTA disclosure, "+13.2 single most-degraded condition", gains in "points" not "%", complementarity "small but consistent" (6/8 strictly positive + 2 ties, p≈0.03).
- **Structure (spec §2 D6, §4):** 9 chapters (Intro / Related Work / Methodology / Experimental Setup / Results: Fusion & Backbones / Results: Robustness & TTA / Discussion + full SOTA / Limitations & Future Work / Conclusion) + Appendices A RTFM repro gap, B per-category + per-class complementarity, C sweep detail, D engineering notes, E reproducibility guide (discharges T6-2), F additional figures. Spec §4 chapter map is binding.
- **Provenance (spec §7a — binding):** `thesis/PROVENANCE.md` manifest: every number family + figure/table → tracked source. Every manifest source git-tracked in Wave 0 (gitignore `results/` → `results/*` rewrite with `!` rules, OR `git add -f`); assert via `git ls-files --error-unmatch`; number audit FAILS on untracked sources. Figures: Class R (regenerable from tracked script + tracked data) or Class V (committed binary + verification note); local checkpoints / E:\ features disallowed as provenance.
- **SOTA verification gate (spec §2 D7, §7, §8 step 2b):** In-phase primary-source verification of all RE-VERIFY items + 17-item camera-ready checklist (incl. #16/#17 PI-VAD/DSANet bib status + full author lists): agents fetch primary papers, evidence report (quote+URL+verdict per item) saved under `.planning/phases/13-*/`; user spot-approves. Unverifiable result cells OMITTED (`---`/N/A) + omission footnote — never shipped unverified. Zero `% RE-VERIFY` comments and zero bib TODOs survive in `thesis/`.
- **Figures (spec §5):** Reuse as-is: fig_architecture.tex (TikZ), 4 paper PDFs + fig_gating_distribution.pdf, pri9_score_hist.png. Regenerate zero-GPU: Phase-7 sweep heatmaps (historical-baseline guard), corruption heatmaps from post-fix continual data (old phase6 C-series FORBIDDEN), 20×4 severity heatmap from tracked Pri-5 CSV, per-category tables from canonical run dirs (post-λ0/post-h1). Phase-6 PNGs (A/B/D/E/F series): provenance-check each → include (Class V + note) / regenerate / drop.
- **Verification before done (spec §8, §11):** `build_thesis.ps1 -Clean`: zero errors, zero undefined refs/citations (scan .log). Adversarial number audit via PROVENANCE.md (Phase-12 standard); headline-consistency; overclaim scan; structure check; pytest stays green.
- **Execution shape (spec §9):** Wave 0 skeleton+tooling+tracking+figures → Wave 1 parallel chapter drafting → Wave 2 appendices+frontmatter+SOTA verification workflow → Wave 3 integration+audits+final build. User checkpoints: after Wave 0 (skeleton compiles), after Wave 1 (chapter drafts), SOTA evidence report spot-approval, final.
- **Title-page facts:** NTUST; author Wei-Han Jeng; advisor Chuan-Kai Yang. Abstract restructured from paper abstract (fixes review item T5-2 density).

### Claude's Discretion
- Exact prose style (match paper's voice; academic register), section-level organization within chapters, figure placement, notation table contents, per-chapter page budgets within the 90–120 total.

### Deferred Ideas (OUT OF SCOPE)
- Defense slide deck (separate later task)
- Chinese abstract / university-template re-skinning
- GPU tracks: Pri-2 (skeleton-head ensemble), Pri-3 (XD smoothing, headline-changing), Pri-4 (streaming w), Pri-8 (JPEG rescue), Pri-11 (temporal module), Pri-13 (text branch) — Future Work section only
- Optional XD total-frames manifest; video_auc recompute discrepancy (Pri-9 minor)
</user_constraints>

<phase_requirements>
## Phase Requirements

No new requirement IDs (writing deliverable). Success criteria are spec §11 items 1–7; the plan should map tasks to them:

| Spec §11 item | Research support |
|----|-------------|
| 1. Clean build, 90–120pp, 9 ch + 6 app + frontmatter | §7 LaTeX build notes; Environment Availability (toolchain verified present) |
| 2. All §4 content present, no placeholders | §1 per-chapter source inventory (all paths verified) |
| 3. Number audit passes; manifest sources tracked | §2 canonical numbers; §3 git tracking audit + exact Wave-0 list |
| 4. Figures verified-current or regenerated | §4 figure provenance worksheet |
| 5. Honesty framings intact | §2 (framings listed verbatim) |
| 6. Primary-source gate passed | §5 RE-VERIFY worklist (all items enumerated with hints) |
| 7. Builds from repo on stock MiKTeX; vendored .bst | §7 (bst provenance verified; preflight design) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Paper/LaTeX build convention:** after editing any *paper* LaTeX source, run `scripts/build_paper.ps1 -Clean`. Phase 13 must NOT edit `paper/` at all (spec §10) — so this rule translates to: create the analogous `build_thesis.ps1` convention for `thesis/` and never commit build artifacts (extend gitignore patterns to `thesis/`).
- `paper/tables_generated.tex` is NOT `\input` by main.tex (tables inlined) — reinforces the forbidden-source rule.
- **GSD workflow enforcement:** all file changes through GSD phase execution.
- **Simplicity/surgical rules:** minimum tooling; build script modeled on the existing one; don't refactor unrelated code. `pytest` suite must stay green (322 passed baseline as of quick 260623-9tu).
- **Execute code in session:** builds and figure regeneration run locally (toolchain verified available — see Environment Availability).
- **CLAUDE.md stale-content warning (found this session):** CLAUDE.md's "Corruption Generation" stack section lists JPEG quality {10..50}, Gaussian σ {0.1..0.5}, brightness ×{0.5..2.0} — these are **pre-implementation research values, NOT what the code does**. Real values live in `scripts/corruption.py:38-42` (see §8 Pitfall 5). Ch 4 writers must use corruption.py.

## Architectural Responsibility Map

| Capability | Primary owner | Secondary | Rationale |
|------------|--------------|-----------|-----------|
| Thesis prose (Ch 1–9, App A–F) | `thesis/chapters/`, `thesis/appendices/` (new) | `paper/main.tex` as base prose (read-only) | Spec §3 layout; paper frozen |
| Build tooling | `scripts/build_thesis.ps1` + `thesis/.latexmkrc` (new) | `scripts/build_paper.ps1` as model (read-only) | Non-interactive; preflight |
| Bibliography | `thesis/references.bib` + vendored `thesis/IEEEtranN.bst` (new) | `paper/references.bib` (copy base, 27 entries) | natbib numeric |
| Number provenance | `thesis/PROVENANCE.md` (new) + Wave-0 git tracking | `results/` tracked sources | Spec §7a binding |
| Figure regeneration | tracked `scripts/generate_*.py` + new small scripts | vcc-main conda env (plotting stack verified) | Class R/V rules |
| External-SOTA verification | Wave-2 verification workflow + evidence report under `.planning/phases/13-*/` | `12-RESEARCH-sota.md` §8 (tracked) | Spec §8 step 2b |
| Verification gates | Wave-3 audits (number audit, overclaim scan, log scan) | `12-VERIFICATION.md` as the standard | Spec §8 |

---

## 1. Per-Chapter Source Inventory (BINDING pointers for chapter writers)

`paper/main.tex` is **457 lines** (verified `wc -l`). All line anchors below spot-verified this session. `.planning/*` docs, `scripts/*.py` generators, `.knowledge/tta-to-reweighting.html`, `data/ucf_total_frames.json`, and `paper/*` sources are all **git-tracked** (verified `git ls-files --error-unmatch`). `results/` sources marked (T) tracked / (U) untracked-needs-Wave-0.

### Paper section anchor map (base prose for every chapter)

| Paper unit | main.tex lines | Notes |
|---|---|---|
| Abstract | 48–53 | dense single paragraph; restructure per T5-2 |
| §1 Introduction | 61–83 | contributions list 75–83 |
| §2 Related Work | 88–109 | §2.1 L90, §2.2 L94, §2.3 TTA L104 |
| §3 Methodology | 111–200 | fig:architecture 113–118 (`\resizebox{\textwidth}{!}{\input{figures/fig_architecture}}` at L115); §3.1 skeleton L122; §3.2 CTR-GCN L130 (64-frame exclusion sentence at **L136**: "Videos shorter than 64 frames (172 videos in UCF-Crime, one in XD-Violence) are excluded from training and evaluation."); §3.3 VLM L138 (backbones itemized 141–147); §3.4 fusion L151; §3.5 MIL L175; §3.6 disc_reweight L190 `\label{sec:disc}` |
| Equations (8) | L157 late fusion; L163 projections+LN; L167 gate; L171 gated blend+residual; L179 ranking loss; L183 total loss `\label{eq:loss}`; L195 w_vl; L197 skeleton gate s + final w (inline, ~1,400-char line) | lift VERBATIM (code-verified via quick 260601-mry / 260604-vfi) |
| §4.1 Datasets | 204–210 | "254 meet the 64-frame minimum and are evaluated" at **L206** |
| §4.2 Implementation | 212–219 `\label{sec:impl}` | λ2 smoothness-implementation footnote at **L217** (≤0.13pp disclosure — RETAIN); seeds + snippet→frame expansion at L219 |
| §4.3 Ablations | 221–276 | tab:ucf-ablation **226–242**; tab:xd-ablation **245–261**; complementarity prose L263; gated-vs-late L265; fig:temporal-scores 267–272; late-fusion degradation L274 |
| §4.4 Backbones | 278–295 | fig:backbone-comparison 280–285 |
| §4.5 TTA | 297–357 `\label{sec:tta}` | tab:tta **301–316**; fig:tta-comparison 318–323; protocol L327; findings L329–335; Pri-5 provenance comment **337–339**; tab:tta_breakdown **340–357** |
| §5 Discussion | 362–374 | five bolded threads; LN-barrier L372; efficiency L374 |
| §6 Limitations & FW | 379–429 | tab:comparison **387–415** (4 `% RE-VERIFY` comments at L399/400/403/404); GS-MoE footnote 413–414; future directions 423–429 |
| §7 Conclusion | 434–444 | code-release promise L444 |
| Acks / bib | 448–452 / 454–455 | ACM-Reference-Format + references.bib (thesis switches to IEEEtranN + natbib) |

### Ch 1 — Introduction
- Base: main.tex §1 (L61–83). Expand per spec §4: motivation, problem statement, gaps, explicit RQ1/RQ2/RQ3, 3 contributions, thesis roadmap.
- No numeric sources beyond §2 anchors.

### Ch 2 — Related Work
- Base: main.tex §2 (L88–109) — each one-paragraph subsection becomes a survey section.
- Primary expansion source: `.planning/phases/12-sota-comparison-and-positioning/12-RESEARCH-sota.md` (tracked; ~20 methods, 31/34 primary-source-verified; §8 at lines 150–188 = per-method verification appendix with citations).
- Method lineage per spec: Sultani → RTFM → UR-DMU/MGFN → CLIP-era (CLIP-TSA, VadCLIP, AnomalyCLIP, TPWNG, PEL4VAD) → MLLM (LAVAD, EventVAD) → recent (PI-VAD, DSANet, GS-MoE); skeleton lineage ST-GCN→CTR-GCN + PYSKL; VLM backbones CLIP/SigLIP/SigLIP2; TTA: TENT, SAR, NORM, CORAL + BN-vs-LN argument.
- **Trap:** 12-RESEARCH-sota.md §8's Light-WVAD row still lists XD 77.3 as verified — that cell was later found FABRICATED (quick 260622-ukd); XD cell is `---`. See §8 Pitfall 4.
- Bib: needs the ~11 new entries (§6 below) + survey-support cites (ST-GCN, ImageNet-C, CORAL, NORM — see §6).

### Ch 3 — Methodology
- Base: main.tex §3 (L111–200), all subsections expanded; equations verbatim.
- Architecture figure: `paper/figures/fig_architecture.tex` (tracked TikZ; bare tikzpicture, swimlane layout, HTML color palette defined at its lines 18–29, natural width ~8.5in) — copy into `thesis/figures/`, re-wrap for one-column (see §7).
- §3.7 TTA methods narrative source: `.knowledge/tta-to-reweighting.html` (tracked; full TTA→reweighting explainer with mechanism formulas, Table-3 evidence, caveats, code pointers). Unpack the paper's L190–199 one-paragraph compression: w_vl dispersion ratio, skeleton gate s with fixed factor-2 anchor (not tuned), saturation to {0,1}, final w = 1−(1−w_vl)s, transductive whole-condition pooling.
- Code cross-refs (all tracked): `src/tta/disc_reweight.py`, `src/tta/tent.py`, `src/tta/sar.py`, `src/tta/evaluate_tta.py`.

### Ch 4 — Experimental Setup
- Base: main.tex §4.1–4.2 (L204–219).
- UCF-Crime-C construction: `.planning/phases/05-tta-infrastructure-corruption-experiments/05-VERIFICATION.md` (tracked) + **exact severity parameters from `scripts/corruption.py:38-42`** (tracked; verified this session):
  - `GAUSSIAN_NOISE_SIGMA = [0.08, 0.12, 0.18, 0.26, 0.38]`
  - `JPEG_QUALITY = [25, 18, 15, 10, 7]`
  - `BRIGHTNESS_FACTOR = [0.1, 0.2, 0.3, 0.4, 0.5]` (ADDITIVE on normalized [0,1] image)
  - `MOTION_BLUR_PARAMS = [(10,3), (15,5), (15,8), (15,12), (20,15)]` (kernel_size, sigma)
  - Skeleton re-extraction only for `("motion_blur", "jpeg_compression")` (`SKELETON_REEXTRACT_TYPES`, corruption.py:30) — cost decision; CLIP re-extracted for all 20 conditions.
  - **Do NOT use CLAUDE.md's parameter lists** (stale pre-implementation research — see §8 Pitfall 5).
- Eval protocol: UCF full-length grid via `data/ucf_total_frames.json` (tracked, 1900 videos) + `src/evaluate.py` fallback; XD truncated snippet-aligned grid; 64-frame exclusions disclosed EXACTLY as main.tex L136/L206 word them.
- Three-environment infrastructure: `.planning/STATE.md` Key Decisions (lines 89–141, tracked) + CLAUDE.md version-compatibility matrix.
- Efficiency: `results/benchmark_models.csv` (U — header verified: model, total_params, trainable_params, params_k, macs_m, flops_m, latency_ms_batch, latency_ms_sample, throughput_samples_s, peak_gpu_mb; rows Skeleton-Only 37.6K / CLIP-Only 595.6K / Late 633.2K / Gated 498.1K / RTFM-I3D 137.4K) and `results/backbone_bench_combined.csv` (U — CLIP ViT-B/16 86.19M measured, RTMPose-m+YOLOX 13.0M published, CTR-GCN 5.68M measured, I3D 25.0M published). NOTE: paper's "0.50–1.02M trainable params" range refers to head params across the 4 backbones (CLIP head 0.50M … Giant head 1.02M); benchmark_models.csv shows the CLIP-backbone heads only — the per-backbone param range source is the paper §5 L374 prose anchor.
- Implementation details: AdamW wd=1e-2 lr=1e-4, 5-epoch warmup + cosine, batch 16 pairs (32 videos), max 50 epochs patience 10, T=32, top-k=3, margin 1.0, λ1=8e-3, λ2=8e-4 UCF / 0 XD, seeds {42,123,2024} (all at main.tex L212–219).

### Ch 5 — Results: Fusion and Backbone Study
- Base: main.tex §4.3–4.4 (L221–295); Tables 1/2 are the canonical inlined tables (L226–261) — **only** number source for ablations.
- Per-category tables: REGENERATE from canonical run dirs' `per_category.csv` (U — format verified: `category,auc,ap`, one row per class). Phase-4/4c-era per-category values FORBIDDEN.
- Pooling ablations: GF 2-Person and GF Mean-Only rows in Tables 1/2; default pooling wins on XD (STATE.md: 2-person −0.90 AP, CLIP mean-only −2.32 AP on XD).
- Hyperparameter sensitivity: results-index.csv (T) sweep rows (~206) + `scripts/generate_phase7_charts.py` (T) with the **historical-baseline guard** (§4 below). Numbers: XD winner lr=1e-3/k=2 → 3-seed 74.69% (+3.72pp over 70.98); UCF winner lr=1.5e-3/k=9 → 82.12% (+0.14pp, insensitive). Present as historical-configuration sensitivity study (CLIP backbone, pre-λ0, sweep-era); never chain to 82.5/78.7.
- Bootstrap CIs (Pri-6): `results/_analysis_2026-06-10/pri6_bootstrap_ci.json` + `.md` (U). UCF s42 82.49 CI [75.63, 88.02] width 12.39pp; XD s42 79.74 CI [76.62, 82.68] width 6.06pp; B=2000, seed 12345, video-level resampling; s42-only caveat stated; frame as field-wide test-set-size uncertainty.
- Failure analysis (Pri-9): `results/_analysis_2026-06-10/pri9_failure_cases.json` + `.md` + `pri9_score_hist.png` (U). Two regimes (saturated-high near-ties; short-event misses e.g. RoadAccidents011 1.9%-of-frames event scored ≈0.000); top FP normals Normal_Videos_887/925/884/895/894; anomaly mean 0.874 / normal mean 0.382 but normal p75 = 0.986 (calibration limitation). Do NOT cite stored video_auc (0.9268 vs 0.9452 recompute discrepancy — deferred).
- Qualitative figures: `paper/figures/fig_temporal_scores.pdf` (T), `fig_gating_distribution.pdf` (T, publication-grade, unused by paper — free), `fig_backbone_comparison.pdf` (T, true 3-seed since 260622-uuu), phase6 D-series gate distributions + E-series t-SNE (U — provenance-check per §4).
- Seed sensitivity: XD AP std up to 1.08–2.8% (Giant lone outlier 2.8%) vs UCF 0.29–0.4%.

### Ch 6 — Results: Robustness and TTA
- Base: main.tex §4.5 (L297–357) + §5 LN-barrier thread (L372).
- Source-only degradation: clean 82.5 → corrupted means 63.7/57.0/58.9/62.8 (CLIP/Base/SO400M/Giant, from tab:tta + verified against `results/_tta_rerun_continual/summary_3seed.json` (T): 63.71/57.01/58.87/62.83).
- TENT/SAR full story: 500-run lr×ρ grid rows in results-index.csv (T — 680 TTA rows: 460 sar, 140 tent, 80 source_only); per-condition bests (TENT +3.81pp jpeg s2; SAR +5.38pp gaussian s5) vs near-zero means; episodic inertness (98.4% of UCF test videos ≤32 snippets) → continual protocol; TRUE 3-seed continual null from `summary_3seed.json` (T), per-backbone means verified this session: ΔTENT/ΔSAR = CLIP +0.021/+0.024, Base −0.082/−0.077, SO400M −0.050/−0.051, Giant +0.011/+0.012 (worst |Δ| = 0.082pp < 0.1pp). Dropout-in-train-mode bug as methods cautionary note (~1.07pp per-condition noise pre-fix; commit 83b8927).
- NORM/CORAL exploration + S1–S6 strategy narrative: `.knowledge/tta-to-reweighting.html` (T) + `results/_coral_derisk/` — the canonical 3-seed disc_reweight per-condition data is the TRACKED set `r1full_{base,clip,giant,so400m}.json` + `variants/v_{backbone}_{s42_train,s123_test,s2024_test}.json` (16 files, T; JSON structure verified: `{summary, per_condition}`). NOT summary_3seed.json (that is TENT/SAR only).
- disc_reweight results: tab:tta L301–316 (CLIP 63.7→64.4 +0.67±0.23; Base 57.0→58.5 +1.50±1.14; SO400M 58.9→61.1 +2.24±0.24; Giant 62.8→63.3 +0.42±0.12; Mean 60.6→61.8 +1.21); per-corruption tab:tta_breakdown L340–357 (Gaussian: +2.67/+5.99/+8.95/+1.69, avg +4.83; other families 0.00 BY CONSTRUCTION); 20×4 severity heatmap from `results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv` (U — format verified: `family,severity,condition,CLIP ViT-B/16,SigLIP2-base,SigLIP2-SO400M,SigLIP2-giant`); all-positive 12/12 backbone×seed cells (min +0.27); honest caveats (Base −3.20 single seed s42 gaussian-5; non-Gaussian 0.00 = gate routes to source, NOT "TTA hurts").
- Generators for rollups: `scripts/pri5_tta_breakdown.py` (T, inputs = the tracked r1full/variants JSONs), `scripts/aggregate_tta_table.py` (T, 3-seed).
- tab:tta caption caveat: truncated snippet-aligned frame grid → NOT comparable in absolute terms to Tables 1–2. Preserve.

### Ch 7 — Discussion (+ full SOTA)
- Base: main.tex §5 (L362–374) five threads + `paper/sota_comparison_full.tex` (T, 332 lines).
- Lift ONLY between `FRAGMENT BODY BEGIN` (line 65) / `FRAGMENT BODY END` (line 329) markers (verified). Contents: metric-definitions paragraph (69–81), `tab:sota-full` 20-method table (85–171, with 14 caveat footnotes a–n at 137–169), `tab:sota-fair` 7-row fair subset (176–221 + "read of the fair subset" 208–219), positioning paragraphs P1–P5 (226–314; P3 contribution-axis numbers 249–267; P5 compute-honesty 303–314), reproducibility paragraph (289–301), manual-references note (318–327 incl. Light-WVAD attribution correction Wang/Zhou/Guan).
- Rewire manual [N] labels → `\cite` (rewiring instructions in the fragment header lines 20–33; keys per §6 below). Carry caveat footnotes. POST-260622-ukd state: Light-WVAD XD cell = `---` (verified in current fragment).
- All 13 row-level RE-VERIFY flags resolve via the Wave-2 gate (§5 below) before this chapter finalizes.

### Ch 8 — Limitations and Future Work
- Base: main.tex §6 (L379–429).
- Gate misses stated plainly: UCF 82.5 < 83 minimum / XD 78.7 < 80 (PRD targets from STATE.md lines 52–60: UCF min 83 target 85–87; XD min 80 target 82–85; RTFM gate 84.30±1%).
- Future-work pointers from `.planning/REVIEW-2026-06-10.md` §5 tracker (T): Pri-2 skeleton-head ensemble routing (+1–2pp est.), **Pri-3 XD test-score smoothing w=64 (verified +0.57pp: 78.72→79.29 all 3 seeds; deliberately NOT adopted under freeze — cite REVIEW-2026-06-10.md as source, `results/_smoothfix/` is untracked)**, Pri-4 streaming/causal w (would discharge the transductive limitation the paper names twice), Pri-8 JPEG rescue, Pri-11 temporal module, Pri-13 text-prompt branch, audio for XD, additional datasets.
- Transductive TTA cap: no online-adaptation claim without Pri-4. XD seed sensitivity; dataset scope; synthetic corruptions.

### Ch 9 — Conclusion
- Base: main.tex §7 (L434–444). Restate findings with §2 anchor numbers; modularity/efficiency pitch; code availability.

### Appendix A — RTFM XD-I3D reproduction investigation
- `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` (T — note the actual dir name; CONTEXT's `04b-*` glob matches): AP 0.6570 vs 0.7781 anchor (−11.11pp) MISS-ACCEPTED; AUC 0.8675; snippet AUC delta 0.0024 rules out snippet→frame bug; Flow-swap diagnostic (100% coverage, AP 0.5916, −6.54pp worse → data coverage ruled out); RGB train cache truncated at V/W/Y tail (2748/3360 = 81.8%).
- `.planning/phases/07-xd-violence-hyperparameter-sweep/07-VERIFICATION.md` (T): root-cause diagnostics — 1024-d vs published 2048-d I3D features; 3 HIGH-impact training-regime diffs; conclusion "training regime, not eval bug". NOTE: `results/phase7_rtfm_gap_diagnostic.json` and `results/phase7_summary.md` referenced by phase docs **do not exist on disk anymore** (verified) — cite the tracked 07-VERIFICATION.md instead.
- Per-category RTFM table: `results/xd_i3d_rtfm_i3d_s42/per_category.csv` + `results/xd_i3d_rtfm_i3d_flow_s42/per_category.csv` (U — both dirs verified; B1 Fighting 0.6324, B2 0.3969, B4 0.7157, B5 Abuse 0.0434, B6 0.2506, G 0.5195 per 04b summary).

### Appendix B — Per-category tables + per-class complementarity
- Full UCF 13-category and XD 6-category tables: regenerate 3-seed from canonical run dirs' `per_category.csv` (list in §3).
- Pri-7: `results/_analysis_2026-06-10/pri7_per_class_complementarity.csv` + `.md` (U). Numbers: human-motion +0.31±1.08 (7/10 positive); appearance −0.29±0.16 (0/3); HM−APP +0.60pp; Shooting +1.05±0.20 (n=22) cleanest; negatives Robbery −1.46 / Assault −0.87 / Abuse −0.80 all tiny-n. Hedge EXACTLY: "directionally supportive but mixed/noisy"; NO Welch t-test.

### Appendix C — Hyperparameter sweep detail
- Regenerate via `scripts/generate_phase7_charts.py` (T) → S01/S02/S04/S05 heatmaps + S03 confirmation MD; output dir `results/phase7_charts/` currently ABSENT (verified). Historical-baseline guard applies (§4).
- Data: results-index.csv (T). 19×6 lr×k grids, s42; 3-seed confirmations at lr1e3_k1 / lr1p5e3_k9 (UCF), lr1e3_k2 / lr7e4_k2 (XD).

### Appendix D — Engineering notes
- `.planning/STATE.md` Key Decisions (L89–141) + critical pitfalls table (L154–165: C1–C5, M5–M7) (T).
- Windows quirks (STATE.md): PyTorch 1.12.1 conda WinError 182 → pip cu113; mmpose/PYSKL --no-deps (chumpy); cuDNN 9 DLL paths; numpy<2 in vcc-ctrgcn; cv2 absent in vcc-main → PIL; cp950 UnicodeEncodeError cosmetic.
- Extraction throughput ~21.6 FPS, 99.3% inference-bound. Two/three-env strategy (mmcv 1.x vs PyTorch 2.x). Anti-pattern register highlights (04-VERIFICATION WR-01..WR-04).

### Appendix E — Reproducibility guide (discharges T6-2)
- Repo map; env setup → extraction → training → evaluation → table/figure generation walkthrough; seeds/manifests (`data/ucf_total_frames.json`), config snapshots (`config_snapshot.json` per run dir), `results/results-index.csv` (T), bit-identical rerun invariant.
- Command entry points (all tracked): `src/train.py` via configs; `src/evaluate.py`; `src/tta/evaluate_tta.py --method disc_reweight`; `scripts/generate_phase7_charts.py`; `scripts/generate_pub_figures.py`; `scripts/build_thesis.ps1`.

### Appendix F — Additional figures
- Phase-6 B-series skeleton overlays (XD-only; UCF source frames are 64×64 PNGs — document limitation), A-series extra temporal curves, `pri9_score_hist.png`, D-series gate histograms not used in Ch 5. All per §4 provenance rules.

### Frontmatter
- titlepage.tex: NTUST / Wei-Han Jeng / advisor Chuan-Kai Yang (also in paper authors block L34–46: emails austin60616@gmail.com, ckyang@cs.ntust.edu.tw).
- abstract.tex: restructure paper abstract L48–53 (fix T5-2: ~285-word single dense paragraph → trim, defer inline TTA mechanism to body).
- notation.tex: abbreviations + symbols (Claude's discretion; harvest from equations list above).
- acknowledgments.tex: placeholder (exempt from no-placeholder rule).

---

## 2. Canonical Numbers (the ONLY permitted values) + Precision Traps

### Anchor table (spec §7, verified against main.tex tables + tracked JSONs)

| Quantity | Value |
|---|---|
| UCF headline | **82.5 ± 0.4 AUC** (Gated Fusion, SigLIP2 Giant, seeds 42/123/2024) |
| XD headline | **78.7 ± 0.9 AP** (Gated Fusion, SigLIP2 SO400M) |
| Skeleton-only | UCF 68.8 ± 2.8 · XD 40.8 ± 0.6 |
| Visual-only CLIP | UCF 81.2 · XD 74.6 |
| Visual-only Giant | UCF 82.4 ± 0.2 · XD 76.8 ± 1.0 |
| Late fusion | UCF max 79.9±0.8 (CLIP 78.9 < visual-only 81.2); XD collapses 63.6–65.7 (CLIP gated-vs-late gap 12.6pp: 76.5 vs 63.9) |
| GF 2-Person | UCF 82.6±0.3 (Giant) · XD 79.2±0.3 (SO400M) — nominally highest cells but NOT the headline variant (see Pitfall 14) |
| Complementarity | 8/8 meet-or-exceed; 6/8 strictly positive + 2 ties; mean +0.6pp; **tie-dropping sign p≈0.03** (paper wording post-T2-1; the per-run p≈0.008 variant exists in STATE.md — use the paper's) |
| TENT/SAR (3-seed continual) | worst \|Δ\| = 0.082pp < 0.1pp; per backbone ΔTENT/ΔSAR: CLIP +0.021/+0.024 · Base −0.082/−0.077 · SO400M −0.050/−0.051 · Giant +0.011/+0.012 (verified from tracked summary_3seed.json) |
| disc_reweight | mean **+1.21pp**; per backbone +0.67±0.23 / +1.50±1.14 / +2.24±0.24 / +0.42±0.12 (CLIP/Base/SO400M/Giant); Source-only 63.7/57.0/58.9/62.8; Ours 64.4/58.5/61.1/63.3; all-positive 12/12 cells (min +0.27) |
| Pri-5 aggregations (KEEP DISTINCT) | Gaussian family 3-seed cross-backbone avg **+4.83** (per backbone +2.67/+5.99/+8.95/+1.69) · max **+13.2** = SO400M gaussian severity-5 3-seed (per-seed 13.92/12.34/13.31) · s42-only Gaussian mean **+3.31** is a DIFFERENT number · Base s42 gaussian_5 = **−3.20** (single-seed disclosure) · non-Gaussian families **0.00 BY CONSTRUCTION** (gate routes to source) |
| Phase-5 per-condition bests (episodic grid, historical) | TENT +3.81pp (jpeg s2) · SAR +5.38pp (gaussian s5) — per-condition bests from the 500-run grid, NOT means |
| Episodic inertness | 98.4% of UCF test videos ≤32 snippets |
| TTA adapted params | 1,536 (3 LN modules, 6 tensors) |
| Bootstrap CIs (Pri-6, s42-only) | UCF 82.49 CI [75.63, 88.02] width 12.39pp · XD 79.74 CI [76.62, 82.68] width 6.06pp (B=2000, seed 12345) |
| Pri-7 per-class | HM +0.31±1.08 (7/10 pos) · APP −0.29±0.16 · HM−APP +0.60pp · Shooting +1.05±0.20 |
| Pri-9 | anomaly mean 0.874 / normal mean 0.382 / normal p75 0.986 |
| Sweep (historical config only) | XD +3.72pp 3-seed (lr=1e-3/k=2, 74.69 vs 70.98) · UCF +0.14pp (insensitive) |
| RTFM repro (App A) | AP 0.6570 vs 77.81 anchor (−11.11pp); Flow-swap AP 0.5916 (−6.54pp, 100% coverage) |
| Efficiency | 0.50–1.02M trainable params; <5 min/config; single RTX 4090 |
| Dataset facts | UCF 1,900 videos / 13 categories / 800+810 train / 150+140 test / **254 evaluated** (64-frame minimum); XD 4,754 / 6 categories / 3,954 train / 800 test; 172 UCF + 1 XD videos <64 frames excluded (main.tex:136 exact sentence) |
| PRD gates (disclosed misses) | UCF min 83 (target 85–87) · XD min 80 (target 82–85) · RTFM 84.30±1% |

### Forbidden sources (verbatim from spec §7 — writers must never read numbers from these)
- `paper/tables_generated.tex` (its own header says so; old single-seed rows, old Table 3).
- Phase 8/9/10/11 summary numbers (single-seed era; superseded by commit 33591ac). Includes 11-04's "UCF best 83.6", "GF Giant 83.3±0.3", "skeleton 71.8/41.3"; Phase-10's "Giant 83.28/83.23".
- `REQUIREMENTS.md` EVAL traceability numbers (0.8227 / 71.92 / 0.9200 — pre-λ0, pre-full-length). Sole exception: 0.8227/0.7192 may appear in the sweep section / Appendix C as explicitly-labeled historical sweep-era baselines, never as current results.
- Light-WVAD XD 77.3 (fabricated; removed in 260622-ukd; XD cell is `---`). Also stale inside 12-RESEARCH-sota.md §8 and 12-VERIFICATION.md traceability table — both predate the fix.
- Old phase6 C-series corruption heatmaps (pre-fix TTA data; C01–C06 in `results/phase6_charts/C_corruption/`).
- Phase 4/4c-era per-category numbers for the CURRENT model (regenerate from run dirs). E.g. Fighting 0.955 / Assault 0.985 / XD Riot 88.15 / Abuse 44.89 are 4/4c-era; per-category values must come from the current post-λ0/post-h1 `per_category.csv` files.
- (Found this session) CLAUDE.md corruption-parameter lists (see Pitfall 5).

### Honesty framings (preserve in meaning, per spec §7)
No SOTA claim; ~88–91% field-ceiling disclosure; fair-subset framing; TTA gains are corrupted-AUC robustness only (never clean AUC); +13.2 labeled "single most-degraded condition"; gains in "points" not "%"; transductive assumption disclosed; UCF λ2=8e-4 smoothness-implementation footnote (≤0.13pp, main.tex:217) retained; 64-frame exclusion disclosures retained; complementarity "small but consistent".

---

## 3. Git Tracking Audit + Exact Wave-0 File List

**Verified state:** `.gitignore` line 9 = `results/` (wholesale ignore). Exactly **28 files** currently force-tracked under results/ (verified `git ls-files results/`):

```
results/_coral_derisk/r1full_{base,clip,giant,so400m}.json                  (4)
results/_coral_derisk/variants/v_{base,clip,giant,so400m}_{s42_train,s123_test,s2024_test}.json  (12)
results/_tta_rerun_continual/{summary.json,summary_3seed.json}              (2)
results/h1_recompute/{ucf_fulllength_comparison.csv,ucf_giant_s42_per_category.csv,xd_SKIPPED.txt}  (3)
results/phase10_charts/{backbone_comparison_4way.csv,comparison_ap_4way.png,comparison_auc_4way.png,
                        seed_stability_4way.csv,seed_stability_4way.png,visual_only_seed_stability_4way.csv}  (6)
results/results-index.csv                                                   (1)
```

Already tracked elsewhere (verified `git ls-files --error-unmatch`): all `.planning/` docs used as sources (STATE.md, REVIEW-2026-06-10.md, ANALYSIS-2026-06-10-zero-gpu.md, 12-RESEARCH-sota.md, 12-VERIFICATION.md, 05/07-VERIFICATION.md, 04b-05-SUMMARY.md), `.knowledge/tta-to-reweighting.html`, `data/ucf_total_frames.json`, `paper/main.tex`, `paper/sota_comparison_full.tex`, `paper/references.bib`, all 5 `paper/figures/*`, and all generator scripts (`generate_phase6/7/8/9/10_charts.py`, `generate_pub_figures.py`, `pri5_tta_breakdown.py`, `analyze_pri6_bootstrap_ci.py`, `analyze_pri7_per_class.py`, `analyze_pri9_failure_cases.py`, `aggregate_tta_table.py`, `corruption.py`, `batch_extract_corrupted.py`, `generate_latex_tables.py`, `src/tta/*.py`, `build_paper.ps1`).

### Wave-0 MUST-TRACK list (untracked today; verified to exist on disk)

**A. Benchmark CSVs (2 files):**
```
results/benchmark_models.csv
results/backbone_bench_combined.csv
```

**B. `results/_analysis_2026-06-10/` — all 11 files:**
```
pri5_per_condition_heatmap.csv   pri5_tta_breakdown.md   pri5_tta_breakdown.tex
pri6_bootstrap_ci.json           pri6_bootstrap_ci.md
pri7_per_class_complementarity.csv   pri7_per_class_complementarity.md
pri9_failure_cases.json          pri9_failure_cases.md   pri9_score_hist.png
verify_pri5_pri6.json
```

**C. `per_category.csv` + `eval_metrics.json` for exactly the 128 canonical cited run dirs (256 files).** Run-dir enumeration (all verified to exist with both files; naming pattern: backbone token ∈ {'' (=CLIP), `_siglip2`, `_so400m`, `_giant`} placed BEFORE the pooling token; seeds `_s{42,123,2024}`):

- UCF (63 dirs): `ucf_skeleton_only_s*` (3) · `ucf_clip_only{,_siglip2,_so400m,_giant}_s*` (12) · `ucf_late_fusion{,_siglip2,_so400m,_giant}_s*` (12) · `ucf_gated_fusion{,_siglip2,_so400m,_giant}_s*` (12) · `ucf_gated_fusion{,_siglip2,_so400m,_giant}_2person_s*` (12) · `ucf_gated_fusion{,_siglip2,_so400m,_giant}_clip_mean_s*` (12)
- XD (63 dirs): exact mirror with `xd_` prefix
- RTFM (2 dirs): `xd_i3d_rtfm_i3d_s42`, `xd_i3d_rtfm_i3d_flow_s42`

**EXCLUDE** the `.pre_lam0.bak` / `.pre_h1.bak` backup files present in canonical dirs (e.g. `ucf_gated_fusion_giant_s42/eval_metrics.json.pre_h1.bak`) — track only the current `per_category.csv` and `eval_metrics.json`.

### Gitignore mechanics (spec §7a — binding)
A bare `!results/foo` rule is DEAD while the parent dir is excluded by `results/`; git cannot re-include a file whose parent directory is excluded. Two valid options:
1. Rewrite `.gitignore`: `results/` → `results/*`, then add `!results/<subdir>/` + `!results/<subdir>/**` (or exact-file `!` rules) per needed path. This makes the policy self-documenting and discharges review item **C7-3**.
2. `git add -f` each file (existing project practice — the current 28 were added this way).

Either way, Wave 0 MUST assert per file: `git ls-files --error-unmatch <path>` (use `git check-ignore -v <path>` for diagnostics on failure). No silent failure. ~269 new files total (2 + 11 + 256), all small text except `pri9_score_hist.png`.

### Planner decision points (flagged, not decided here)
- **Per-condition continual TENT/SAR data:** `results/_tta_rerun_continual/<backbone>/<method>/<condition>/eval_metrics.json` files are untracked (11 method dirs × 20 conditions × 4 backbones ≈ 880 small JSONs; structure verified). The tracked `summary_3seed.json` holds only 20-condition means per seed (verified — no per-condition detail). If Ch 6 includes a per-condition TENT/SAR table (spec only requires "per-condition bests vs near-zero means", which the tracked results-index.csv covers for the Phase-5 episodic grid), either track the needed subset or (recommended) write + track a small rollup CSV generated by a tracked script. This also partially discharges **C7-1** (untracked `scripts/_tmp_r1_full.py` + deps — promotion optional; the tracked pri5/aggregate scripts + tracked JSONs already give Table-3 provenance).
- `results/_smoothfix/` (Pri-3 evidence) stays untracked — Ch 8 cites REVIEW-2026-06-10.md (tracked) for the +0.57pp number.
- `review-2026-06-22.html` is untracked — cite open findings via STATE.md line 24 instead.

---

## 4. Figure Provenance Worksheet

Classes per spec §5: **R** = regenerated by tracked script from tracked data; **V** = committed binary under `thesis/figures/` + manifest verification note. Local checkpoints + E:\ features CANNOT be manifest sources.

### Reuse as-is (all verified tracked, exist)

| Figure | Path | Tracked | Class | Use | Verification method (V) / regen cmd (R) |
|---|---|---|---|---|---|
| Architecture (TikZ) | `paper/figures/fig_architecture.tex` | ✓ | R (tracked source) | Ch 3 | copy into `thesis/figures/`, `\input` + `\resizebox` (see §7); no data inputs |
| Temporal scores | `paper/figures/fig_temporal_scores.pdf` | ✓ | V | Ch 5 | note: generated by tracked `generate_pub_figures.py` from local eval_scores.npz; verify curve video (RoadAccidents) + caption vs paper L267–272 |
| Backbone comparison | `paper/figures/fig_backbone_comparison.pdf` | ✓ | V | Ch 5 | regenerated true-3-seed 260622-uuu (commit 2e6cb6b); verify 24 cells match Tables 1/2 ≤0.05pp (that check was already done — cite it in the note) |
| TTA comparison | `paper/figures/fig_tta_comparison.pdf` | ✓ | V | Ch 6 | verify means vs summary_3seed.json (tracked) |
| Gating distribution | `paper/figures/fig_gating_distribution.pdf` | ✓ | V | Ch 5 | publication-grade, UNUSED by paper — free thesis figure; verify vs D-series data narrative |
| Pri-9 score histogram | `results/_analysis_2026-06-10/pri9_score_hist.png` | ✗ → Wave 0 | V (after tracking) | Ch 5 / App F | generated by tracked `analyze_pri9_failure_cases.py`; note giant-s42 provenance |

### Regenerate zero-GPU (Class R — tracked script + tracked data)

| Asset | Generator | Data input (tracked?) | Guard |
|---|---|---|---|
| Phase-7 sweep heatmaps S01/S02/S04/S05 + S03 confirmation MD | `scripts/generate_phase7_charts.py` (T) → `results/phase7_charts/` (dir ABSENT today — verified) | `results/results-index.csv` (T) | **Historical-baseline guard (verified in code):** lines 55–56 hardcode `XD_BASELINE_AP = 0.7192`, `UCF_BASELINE_AUC = 0.8227`; S03 section hardcodes "AP = 70.98% +/- 1.08%" (line 266) and "AUC = 81.98% +/- 0.29%" (line 295) with "Delta vs P4c"/"Delta vs P4" columns (lines 268/283/297). Thesis tables/captions must EXCLUDE those delta columns or label them "vs historical 2026-05 sweep configuration (CLIP backbone, pre-λ0, s42)". Those values may appear ONLY as labeled historical baselines. |
| New corruption heatmaps (replace forbidden C-series) | NEW small script (must be written + tracked in Wave 0) | disc_reweight per-condition: `results/_coral_derisk/r1full_*.json` + `variants/v_*.json` (T; contain `per_condition` + src means — verified); TENT/SAR/source-only means: `summary_3seed.json` (T); per-condition source-only if needed: see §3 planner decision | old `results/phase6_charts/C_corruption/C01..C06` = FORBIDDEN (pre-dropout-fix episodic data) |
| 20×4 severity heatmap (thesis-only, new) | NEW small script (Wave 0) | `results/_analysis_2026-06-10/pri5_per_condition_heatmap.csv` (Wave-0 tracked; format verified) | keep Pri-5 aggregation labels straight (§2) |
| Per-category tables (LaTeX) | NEW small script or extend `generate_latex_tables.py` (T — but NOTE its Table-3 section is stale/never updated for disc_reweight; do not reuse blindly) | canonical run dirs' `per_category.csv` (Wave-0 tracked; format `category,auc,ap`) | 3-seed mean±std; post-λ0/post-h1 state = the current files |

### Provenance-check before reuse (Phase-6 PNGs — all UNTRACKED, single-seed era May 2026)

Exact inventory (verified on disk, `results/phase6_charts/`):

| Series | Files | Disposition procedure |
|---|---|---|
| A_temporal (5) | A01_Shooting008, A02_Arrest007, A03_Shooting032, A04_Salt.2010...B1, A05_Tropa.de.Elite.2...B2 .png | Per-figure: verify underlying checkpoint/scores still match canonical (post-λ0/post-h1) numbers; regenerate via `scripts/generate_phase6_charts.py` (T) against current checkpoints (zero-GPU; needs vcc-main + local checkpoints/E: features) → commit as Class V with note; DROP if provenance can't be established. UCF A-series predates h1 full-length eval — likely needs regeneration. |
| B_skeleton (3) | B01/B03 Salt.2010 f697/f613, B02 Tropa f838 | XD-only BY NECESSITY (UCF frames are 64×64 — document). Skeleton overlays don't depend on eval scores → likely reusable as-is, Class V + note. |
| C_corruption (6) | C01–C06 | **FORBIDDEN — do not reuse.** Replace per table above. |
| D_gating (4) | D01_gate_by_category_{ucf,xd}, D02_gate_histogram_{ucf,xd} | Gate distributions depend on checkpoints (λ0 changed XD checkpoints) → verify/regenerate; Class V. |
| E_projection (2) | E01_tsne_{ucf,xd} | t-SNE of fused features; same verify/regenerate rule; no underlying data files persisted (only PNGs) — regeneration requires local caches/checkpoints. Class V. |
| F_additional (6) | F01_cross_dataset, F02/F03 category scores, F04_seed_stability, F05/F06 ablation bars | F04–F06 embed single-seed-era ablation numbers → almost certainly STALE (Pri-1 changed 4 rows materially); regenerate or drop. F02/F03 score distributions: verify. |

**Clean-checkout rule (binding):** every thesis figure lands in PROVENANCE.md as exactly Class R or Class V; a Class-V note records what it was checked against and when.

---

## 5. RE-VERIFY / Verification-Gate Worklist (Wave 2, spec §8 step 2b)

**Grep-verified counts:** `paper/sota_comparison_full.tex` contains 15 `% RE-VERIFY` occurrences = **13 row-level items** (lines 104, 106, 108, 111, 112, 115, 116, 117, 120, 122, 123, 124, 125) + 2 meta-mentions (lines 43 header, 93 body prose — not work items). `paper/main.tex` has 4 more (lines 399, 400, 403, 404) on tab:comparison rows — paper stays frozen, but the thesis copies of those rows inherit the same checks. The 17-item checklist lives at `12-VERIFICATION.md` lines 129–153 (read in full this session). Consolidated per-method worklist:

| # | Method | Claimed numbers (UCF/XD) | What to verify | Primary-source hint (from 12-RESEARCH-sota.md §8) | Flag locations |
|---|--------|--------------------------|----------------|--------------------------------------------------|----------------|
| 1 | CLIP-TSA | 87.58 / **82.19** | XD is AUC@PR from PRIMARY paper (VadCLIP table lists 82.17 — 0.02 drift); NEVER 94.02 (non-comparable protocol) | arXiv:2212.05136v3 (ICIP 2023), Joo, Vo, Yamazaki & Le | frag l.111; main.tex:403; checklist #1 (HIGH) |
| 2 | MGFN | 86.98 / **79.19** | 79.19 = I3D-RGB AP (NOT 80.11 VideoSwin); UCF 86.98 is I3D | AAAI 2023 camera-ready PDF (ojs.aaai.org .../25112/24884), Chen et al. | frag l.112; main.tex:404; checklist #2 (HIGH) |
| 3 | GS-MoE | 91.58 / 82.89 | check ICCV'25 camera-ready status if kept | arXiv:2508.06318, D'Amicantonio et al. | checklist #3; bib `damicantonio2025gsmoe` @misc |
| 4 | Holmes-VAD | 89.51 / 90.67 | preprint status (no peer-reviewed venue); partial MLLM LoRA (not frozen-feature) | arXiv:2406.12235v2, Zhang et al. | frag l.104; checklist #4 |
| 5 | Holmes-VAU | 88.96 / 87.68 | numbers are VIDEO-LEVEL (398-sample split), NOT frame-level — disclose or omit | arXiv:2412.06171v2 (CVPR 2025 camera-ready), Zhang et al. | frag l.106; checklist #5 |
| 6 | PiercingEye | 86.64 / 88.82 | XD LOW conf (inferred from relative gains); AUDIO+visual+text; UCF is visual-only | arXiv:2504.18866 (ar5iv mirror; IEEE TPAMI'26), Leng et al. — Table I/II | frag l.115; checklist #6 |
| 7 | AnomalyCLIP | 86.36 / 78.51 | LOW conf; the ~90.3 figure is recognition mAUC (DIFFERENT task) — never cite as detection AUC | CVIU 2024, Zanella, Liberatori, Menapace, Poiesi, Wang & Ricci — Tables 2/3 | frag l.116; checklist #7 |
| 8 | FDPN | 88.03 / N-A | LOW conf, paper's OWN method self-report (+0.01 over VadCLIP); XD not evaluated — re-check or DROP row | arXiv:2411.10945 (WACV'25), Song, Lee, Joo & Lee | frag l.108; checklist #8, #14 |
| 9 | TEVAD | 84.9 / ≈79.8 | MEDIUM precision (headline 79.8, ablations 79.3–79.76); disregard "88.28" web misattribution | CVPRW 2023 (O-DRUM) CVF Open Access PDF, Chen, Ma, Yew, Hur & Khoo | frag l.117; checklist #9 |
| 10 | Sultani XD cell | — / `---` | already omitted (73.20 is Wu ECCV'20 re-impl, not the 2018 paper); confirm omission stays | Sultani CVPR 2018 (UCF 75.41 fine) | frag l.123; checklist #10 (handled) |
| 11 | RTFM | 84.30 / 77.81 | confirm 77.81 (I3D) is the cited value — already canonical | arXiv:2101.10030 (ICCV 2021), Tian et al. Table 2 | checklist #11 (done — confirm) |
| 12 | EventVAD | 82.03 / 64.04 | XD = 64.04 AP, NOT 87.51 (its XD ROC-AUC); training-free ≠ low-compute (80GB A800) | arXiv:2504.13092v1 (ACM MM 2025), Shao et al. Table 1/2 | frag l.120; main.tex:399; checklist #12 |
| 12b | LAVAD | 80.28 / 62.01 | XD = 62.01 AP, NOT 85.36 (XD ROC-AUC); dual RTX 3090 | arXiv:2404.01014 (CVPR 2024), Zanella, Menapace, Mancini, Wang, Ricci | frag l.122; main.tex:400; checklist #12 |
| 13 | HyperVD | N-A / 85.67 | AUDIO-VISUAL (visual-only variant = 82.51); UCF not reported — label modality | arXiv:2305.18797 (Image & Vision Computing 2024), Peng et al. Table 1 | frag l.124; checklist #13 |
| 13b | Ghadiya et al. | N-A / 86.34 | AUDIO-VISUAL workshop paper; UCF not reported | arXiv:2412.20455 (CVPRW 2024 MULA), Ghadiya, Kar, Chudasama & Wasnik (Sony Research India) | frag l.125; checklist #13 |
| 14 | STPrompt & FDPN XD | N/A cells | confirm neither evaluates XD | STPrompt arXiv:2408.05905 (ACM MM '24) | footnotes d/e; checklist #14 (done — confirm) |
| 15 | Light-WVAD attribution | 84.7 / `---` | authors = Wang, Zhou & Guan (NOT "Sun et al."); XD cell stays `---` (77.3 fabricated, removed 260622-ukd) | Neurocomputing 2024, Vol. 613, art. 128698 | checklist #15 (bib verified correct); frag manual-refs note l.318–327 |
| 16 | PI-VAD & DSANet bib type | 90.33/85.37 · 89.44/86.95 | publication status: accepted CVPR'25 / AAAI'26 or still preprint? retype `@misc` w/ eprint if preprint; add pages/publisher if accepted | PI-VAD arXiv:2505.13123 (Majhi et al.); DSANet arXiv:2511.10334 (Yin et al.; AAAI OJS entry + GitHub lessiYin/DSANet corroborate) | checklist #16 (WR-02) |
| 17 | PI-VAD & DSANet author lists | — | replace `and others` placeholders with full author lists from arXiv records | same arXiv IDs | checklist #17 (IN-02) |

**Gate rules (spec §7/§8):** evidence report (per-item quote + URL + verdict) saved under `.planning/phases/13-full-thesis-manuscript/`; user spot-approves. Failed items corrected; unverifiable RESULT cells → `---`/N-A + omission footnote (row dropped if headline cells unverifiable). Zero `% RE-VERIFY` comments and zero bib TODOs survive in `thesis/`. Do NOT do this verification during planning — it is Wave-2 work.

---

## 6. Bibliography Plan Detail

### Base: copy `paper/references.bib` → `thesis/references.bib` (27 entries, keys verified this session)

`sultani2018ucfcrime, tian2021rtfm, wu2020xdviolence, radford2021clip, zhai2023siglip, tschannen2025siglip2 (@misc), chen2021ctrgcn, jiang2023rtmpose (@misc), wang2021tent, niu2023sar, wu2024vadclip, doshi2022skeleton, yan2022pyskl, carreira2017i3d, foret2021sam, ba2016layernorm (@misc), ioffe2015batchnorm, dosovitskiy2021vit, joo2023cliptsa, zhou2023urdmu, chen2023mgfn, wang2024lightwvad (@article), majhi2025pivad, yin2026dsanet, shao2025eventvad, zanella2024lavad, damicantonio2025gsmoe (@misc)`

### ~11 new entries for the full SOTA table (author/venue data from 12-RESEARCH-sota.md §8, lines 150–188; construct entries in Wave 0, verify in Wave 2 gate)

| Proposed key | Method | Authors (from §8) | Venue | arXiv |
|---|---|---|---|---|
| `zhang2024holmesvad` | Holmes-VAD | Zhang et al. | arXiv preprint (verify status) | 2406.12235 |
| `zhang2025holmesvau` | Holmes-VAU | Zhang et al. | CVPR 2025 | 2412.06171 |
| `wu2024stprompt` | STPrompt | Wu, Zhou, Pang, Yang, Yan, Wang & Zhang | ACM MM 2024 | 2408.05905 |
| `song2025fdpn` | FDPN | Song, Lee, Joo & Lee | WACV 2025 | 2411.10945 |
| `yang2024tpwng` | TPWNG | Yang, Liu & Wu | CVPR 2024 | 2404.08531 |
| `pu2024pel4vad` | PEL4VAD | Pu, Wu, Yang & Wang | (verify journal — TIP per §8 row; confirm in gate) | 2306.14451 |
| `leng2026piercingeye` | PiercingEye | Leng, Wu, Tan, Mo, Zheng, Li, Gan & Gao | IEEE TPAMI 2026 | 2504.18866 |
| `zanella2024anomalyclip` | AnomalyCLIP | Zanella, Liberatori, Menapace, Poiesi, Wang & Ricci | CVIU 2024 | (get ID in gate) |
| `chen2023tevad` | TEVAD | Chen, Ma, Yew, Hur & Khoo | CVPRW 2023 (O-DRUM) | — (CVF OA) |
| `peng2024hypervd` | HyperVD | Peng et al. | Image & Vision Computing 2024 | 2305.18797 |
| `ghadiya2024crossmodal` | Ghadiya et al. | Ghadiya, Kar, Chudasama & Wasnik | CVPRW 2024 (MULA) | 2412.20455 |

(Key naming follows the existing `firstauthorYYYYkeyword` convention. Exact fields finalized against primary sources in the Wave-2 gate — no TODO comments may survive.)

### Survey-support cites Ch 2/Ch 4 will likely need (NOT in references.bib today — [ASSUMED] entries, verify before adding)

| Need | Work | Where used |
|---|---|---|
| ST-GCN lineage | Yan, Xiong & Lin, "Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition," AAAI 2018 | Ch 2 skeleton survey (spec §6 names it) |
| Corruption benchmark | Hendrycks & Dietterich, "Benchmarking Neural Network Robustness to Common Corruptions and Perturbations" (ImageNet-C), ICLR 2019 | Ch 4 UCF-Crime-C construction (corruption.py cites hendrycks/robustness) |
| CORAL | Sun, Feng & Saenko, "Return of Frustratingly Easy Domain Adaptation," AAAI 2016 (and/or Deep CORAL, ECCV-W 2016) | Ch 2 TTA survey; Ch 6 feature-statistic restoration |
| NORM / BN-stats adaptation | Schneider et al., "Improving robustness against common corruptions by covariate shift adaptation," NeurIPS 2020 | Ch 2 TTA survey ("NORM/statistic-restoration" in spec §4 Ch 2) |

### Fragment citation rewiring
`sota_comparison_full.tex` uses manual bracketed [N] labels by design (header lines 20–33 contain the rewiring instructions). Ch 7 writer replaces every manual label with `\cite{key}` after the bib superset lands in Wave 0.

---

## 7. LaTeX Build Notes (report class on MiKTeX/Windows)

### Vendored IEEEtranN.bst — provenance (verified this session)
- Local copy: `C:/Users/Austin/AppData/Local/Programs/MiKTeX/bibtex/bst/feupphdteses/IEEEtranN.bst` — header verified: **authentic Michael Shell "IEEEtranN.bst — Natbib version of IEEEtran.bst", Version 1.13 (2008/09/30)**, natbib-compatible. A sibling `IEEEtranSN.bst` also exists there.
- `kpsewhich IEEEtranN.bst` resolves ONLY to that feupphdteses path (verified) — machine-specific accident, hence vendoring into `thesis/` is correct.
- BibTeX searches the current working directory before distribution trees, so the vendored `thesis/IEEEtranN.bst` wins when latexmk runs inside `thesis/`.
- CTAN comparison: CTAN's IEEEtran package page shows class v1.8b (2015); the .bst bundle was also refreshed in 2015. Could not byte-compare offline. **Disposition:** vendor the local v1.13 copy and record provenance in PROVENANCE.md ("copied from local MiKTeX feupphdteses package; authentic Michael Shell header v1.13 2008/09/30"); optionally fetch the current CTAN copy in Wave 0 and diff — functional risk of v1.13 is negligible (complete, widely-used style).

### Preamble pairing (spec §3)
- `\documentclass[12pt,a4paper,oneside]{report}`.
- `\usepackage[numbers,sort&compress]{natbib}` + `\bibliographystyle{IEEEtranN}` + `\bibliography{references}`. IEEEtranN REQUIRES natbib (it emits natbib-format `\bibitem`s); plain-LaTeX citation without natbib will break — always load natbib.
- Load order: standard packages → natbib → `hyperref` LAST (only cleveref/glossaries would come after; not planned). geometry (2.5cm margins) anywhere early. `\usepackage{setspace}` + `\onehalfspacing`; load `caption`/`subcaption` so captions stay single-spaced and consistent. `microtype` after fonts.
- TikZ: `\usepackage{tikz}` + `\usetikzlibrary{positioning,arrows.meta,fit,calc}` (exact set the paper uses, main.tex L24–28).
- Package list for preflight REPORT (spec §3): natbib, booktabs, multirow, graphicx, tikz/pgf, hyperref, geometry, setspace, caption, subcaption, microtype, amsmath, amssymb — all standard; MiKTeX on-demand install covers anything missing because the latexmkrc passes `--enable-installer`.

### TikZ architecture figure reuse
Paper pattern (verified main.tex:113–118): `\begin{figure*}[t] \resizebox{\textwidth}{!}{\input{figures/fig_architecture}}`. In the one-column report, `figure` (not `figure*`) + same `\resizebox{\textwidth}{!}{...}` works — but A4 one-column `\textwidth` (~16cm with 2.5cm margins) is ~30% narrower than the paper's two-column span, so the ~8.5in-native swimlane will shrink further. Options (planner/writer discretion): (a) accept smaller text; (b) `rotatebox`/`sidewaysfigure` (needs `rotating` package — add to preflight list if used); (c) split lanes. **Copy `fig_architecture.tex` into `thesis/figures/`** — never `\input` across into frozen `paper/`.

### thesis/.latexmkrc (model = paper/.latexmkrc, verified contents)
```perl
$pdf_mode = 1;
$bibtex_use = 2;
$pdflatex = 'pdflatex -interaction=nonstopmode -synctex=1 --enable-installer %O %S';
$bibtex   = 'bibtex --enable-installer %O %S';
@default_files = ('main.tex');
```
(The `--enable-installer` flags are the working MiKTeX on-demand-install mechanism — the [MPM]AutoInstall preference is not honored reliably; keep them.)

### scripts/build_thesis.ps1 — what to copy from build_paper.ps1 (verified anatomy), what to change
COPY: `Find-Exe` probe pattern; latexmk probe at `$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64` (verified `latexmk.exe` exists there); PATH injection for child pdflatex/bibtex processes (lines 62–65); Strawberry Perl probe `C:\Strawberry\perl\bin` (verified `perl.exe` exists) + PATH injection; `Push-Location`/`Pop-Location` around latexmk; `-Clean` → `latexmk -C` then full build; exit-code handling.
CHANGE:
1. Target `thesis/main.tex`; **REMOVE `Invoke-Item $pdf` (build_paper.ps1 line 111)** — non-interactive default; add `[switch]$Open` that gates it.
2. Preflight (before build): HARD-assert `thesis/IEEEtranN.bst` exists (repo-controlled — fail with clear message if absent); REPORT-only (non-blocking) `kpsewhich <pkg>.sty` per required package (absence is NOT an error — MiKTeX installs on demand; the report only makes later failures diagnosable).
3. Post-build log scan (spec §8 step 1): fail (nonzero exit) if `thesis/main.log` contains `There were undefined references`, `Citation .* undefined`, `Reference .* undefined`, or LaTeX `!` errors. build_paper.ps1 has NO log scan — this is new.
4. gitignore: extend the paper artifact patterns to `thesis/` (`thesis/main.pdf`, `*.aux`, `*.bbl`, `*.blg`, `*.fls`, `*.fdb_latexmk`, `*.synctex.gz`, `*.out`, `*.log`, `*.toc`, `*.lof`, `*.lot`).

### report-class specifics
- Frontmatter: `\begin{titlepage}...`, abstract as unnumbered chapter or `abstract`-like environment (report has no `abstract` env in oneside chapters context — use `\chapter*{Abstract}` + `\addcontentsline`), `\tableofcontents`, `\listoffigures`, `\listoftables`, notation table.
- Chapters: `\include{chapters/ch01_introduction}` (gives per-chapter .aux + `\includeonly` fast partial builds; `\include` forces `\clearpage` — fine at chapter granularity).
- Appendices: `\appendix` then `\chapter{...}` per appendix.
- `hyperref` + report: set `bookmarksnumbered`, `hidelinks` (or colorlinks per taste — discretion).

---

## 8. Risks & Pitfalls (stale-number traps and mechanical risks)

### Pitfall 1: `paper/tables_generated.tex` is a trap
Header itself says stale. Skeleton-Only 71.8/40.9, Visual-Only/2-Person/Mean-Only rows single-seed (UCF Mean-Only 83.0, XD Mean-Only 79.9 — superseded to 82.5/78.4), Table 3 is the dead TENT/SAR-only format. `scripts/generate_latex_tables.py` regenerates this stale file (never updated for disc_reweight). **Never read numbers from it; don't re-run its Table-3 path.**

### Pitfall 2: Phase 8/9/10/11 summaries + REQUIREMENTS.md EVAL rows are single-seed/pre-λ0 era
All superseded by commit 33591ac (Pri-1 3-seeding) + λ0 adoption + h1 full-length eval. Phase summaries are fine as NARRATIVE sources (deviations, lessons, diagnostics) but every NUMBER must come from §2. REQUIREMENTS.md 0.8227/71.92/0.9200 forbidden (single labeled-historical exception, §2).

### Pitfall 3: Phase-7 chart generator hardcodes historical baselines
Verified: `generate_phase7_charts.py:55–56` (0.7192 / 0.8227) and S03 text at lines 266 ("70.98% +/- 1.08%") / 295 ("81.98% +/- 0.29%") + Delta columns (lines 268/283/297). Regenerated outputs carry "Delta vs Baseline" columns vs the 2026-05 sweep configuration. Exclude those columns from thesis tables or label historical-configuration-only; never chain to 82.5/78.7.

### Pitfall 4: Light-WVAD XD 77.3 is fabricated AND still present in two tracked planning docs
`12-RESEARCH-sota.md` §8 Light-WVAD row and `12-VERIFICATION.md` traceability table both predate quick 260622-ukd (commit f694611) which found Light-WVAD never evaluated XD. Current fragment/paper correctly show `---`. Writers using the planning docs as citation sources must not resurrect 77.3. UCF 84.7 remains valid.

### Pitfall 5 (NEW, found this session): CLAUDE.md corruption parameters are wrong for the thesis
CLAUDE.md "Corruption Generation" section says JPEG quality {10,20,30,40,50}, σ {0.1–0.5}, brightness ×{0.5–2.0} — pre-implementation research. The implemented ImageNet-C-exact values (verified `scripts/corruption.py:38-42`) are: σ [0.08,0.12,0.18,0.26,0.38]; JPEG quality [25,18,15,10,7]; brightness ADDITIVE [0.1–0.5]; motion blur (kernel,σ) [(10,3),(15,5),(15,8),(15,12),(20,15)]. Ch 4 must cite corruption.py.

### Pitfall 6: Pri-5 aggregation confusion
Four different numbers coexist: +4.83 (3-seed cross-backbone Gaussian-family avg), +3.31 (s42-only Gaussian mean), +8.95 (SO400M Gaussian family mean), +13.2 (SO400M gaussian severity-5, 3-seed). Also +13.9 was the RAW pre-3-seed value (fixed to +13.2 in commit 9218dd2) — never reintroduce. Non-Gaussian 0.00 = "gate routes to source", never "TTA hurts on blur".

### Pitfall 7: Snippet→frame protocol asymmetry
UCF: full-length grid, final snippet score repeated over trailing frames, via `data/ucf_total_frames.json` (git-reproducible). XD: truncated snippet-aligned grid (~0.74% trailing truncation; no manifest — deferred). tab:tta corrupted AUCs use the truncated grid → NOT absolutely comparable to Tables 1–2 (caption discloses; preserve). UCF vs XD snippet duration: 64 frames ≈ 20s UCF (3FPS pre-sampled) vs ≈2.7s XD (native 24FPS) — disclosed at main.tex:136 region; keep.

### Pitfall 8: 64-frame exclusion + λ2 footnote disclosures are load-bearing
Exact sentences: main.tex:136 ("Videos shorter than 64 frames (172 videos in UCF-Crime, one in XD-Violence) are excluded...") and main.tex:206 ("...254 meet the 64-frame minimum and are evaluated."). λ2 smoothness-implementation footnote main.tex:217 (≤0.13pp) must survive into Ch 4. Note STATE.md's "XD has 0 sub-64-frame videos" refers to extraction-time snippet counts; the paper's audited "one in XD-Violence" wording is canonical — lift it verbatim.

### Pitfall 9: Per-category numbers must be regenerated
All previously-quoted per-category values (Fighting 0.955, Assault 0.985, Riot 88.15, Abuse 44.89...) are Phase-4/4c-era (pre-λ0/pre-h1). The current `per_category.csv` files in canonical run dirs are the only valid source; compute 3-seed mean±std.

### Pitfall 10: GF 2-Person cells nominally beat the headline
UCF 82.6±0.3 (Giant 2-Person) > 82.5; XD 79.2±0.3 (SO400M 2-Person) > 78.7. The headline variant is Gated Fusion default pooling (paper's framing; default pooling wins on XD overall ablation logic). Writers must not silently promote 2-Person as the headline.

### Pitfall 11: Complementarity p-value duality
Paper (post-T2-1): "6/8 strictly positive + 2 ties, tie-dropping sign test p≈0.03" — USE THIS. STATE.md's p≈0.008 is the per-run 8/8 test; only mention if explicitly distinguishing tests.

### Pitfall 12: results-index.csv backbone column is EMPTY
Backbone encoded in run_name suffix (none=CLIP, `siglip2`, `so400m`, `giant`). Any new tooling parses run_name (existing generators already do).

### Pitfall 13: Missing-on-disk artifacts referenced by phase docs
`results/phase7_charts/`, `results/phase7_summary.md`, `results/phase7_rtfm_gap_diagnostic.json`, `results/phase4_charts/` do NOT exist (verified). Sweep charts: regenerate. RTFM diagnostics: cite tracked 07-VERIFICATION.md. Never cite the missing paths in PROVENANCE.md.

### Pitfall 14: Fragment lift mechanics
Lift ONLY between FRAGMENT BODY BEGIN (l.65) / END (l.329). The fragment's `\documentclass{standalone}` preamble and `\end{document}` must not leak in. Fragment uses `\texttt{}`/tabularx-style column setups compatible with report class, but verify `array` package needs during Wave-0 compile.

### Pitfall 15: TTA memory staleness
Auto-memory "ACTIVE: NEXT val-C → shrunk-CORAL → Table 3 rewrite" is SUPERSEDED — CORAL abandoned, Table 3 shipped (12cd95f). The HANDOVER file never existed in git. Narrative source = `.knowledge/tta-to-reweighting.html`.

### Pitfall 16: Open low-severity review items intersecting this phase
C7-3 (gitignore un-ignore rules) — discharged by Wave-0 option 1. T6-2 (repro guide) — discharged by Appendix E. T5-2 (abstract density) — discharged by frontmatter abstract restructure. T5-6 (bib RE-VERIFY comments + "and others") — discharged by Wave-2 gate. C7-1 (untracked TTA rollup generators) — partially addressed per §3 planner decision. C6-4 (headline assertion test) — OUT of scope (needs E: features; do not attempt).

---

## Standard Stack (tooling for this phase — no new package installs)

| Tool | Version/Location (verified) | Purpose |
|---|---|---|
| MiKTeX latexmk | `%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\latexmk.exe` (exists) | thesis build |
| Strawberry Perl | `C:\Strawberry\perl\bin\perl.exe` (exists) | latexmk engine |
| pdflatex + BibTeX | MiKTeX, on-demand package install via `--enable-installer` | compile + bibliography |
| IEEEtranN.bst v1.13 | vendored from local MiKTeX feupphdteses path (§7) | numeric natbib bibliography |
| Python (figures) | `C:/Anaconda/envs/vcc-main/python.exe` — matplotlib+pandas+seaborn+torch import OK (verified) | zero-GPU figure regeneration. NOTE: shell-default Python 3.13.5 LACKS matplotlib — always use vcc-main |
| pytest | repo suite, 322 passed baseline | repo hygiene gate |
| git | tracking assertions (`git ls-files --error-unmatch`, `git check-ignore -v`) | Wave-0 provenance |

## Package Legitimacy Audit

Not applicable — this phase installs **no external packages**. LaTeX packages resolve through MiKTeX's on-demand installer from CTAN (same baseline as the existing paper build, per spec §3 "Build baseline"); the only nonstandard-resolution item (IEEEtranN.bst) is vendored from a local, header-verified authentic copy, not downloaded.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Bibliography style | custom .bst | vendored IEEEtranN.bst + natbib | complete, authentic, natbib-tested |
| Build orchestration | new build logic | latexmk + .latexmkrc pattern from paper/ | proven on this machine (paper builds clean) |
| Table numbers | retyping from memory/planning docs | copy from main.tex inlined tables; regenerate per-category from per_category.csv | audit fails on untraceable numbers |
| SOTA table + positioning prose | rewriting | lift fragment body verbatim (markers l.65/329) | purpose-built, 4-audit-verified |
| Equations | re-deriving | lift verbatim from main.tex | code-verified (260601-mry/260604-vfi) |
| Sweep heatmaps | new plotting code | `generate_phase7_charts.py` (with baseline-column guard) | tracked, tested against results-index.csv |

## Environment Availability

| Dependency | Required by | Available | Notes |
|---|---|---|---|
| MiKTeX (latexmk, pdflatex, bibtex, kpsewhich) | build | ✓ | verified paths §7 |
| Strawberry Perl | latexmk | ✓ | C:\Strawberry\perl\bin |
| vcc-main conda env (matplotlib/pandas/seaborn/torch) | figure regeneration | ✓ | verified import OK; shell python lacks matplotlib |
| Local checkpoints (144 best_model.pth) + E:\ features | Phase-6 figure regeneration (Class V path) | ✓ local-only | NOT valid provenance sources; only for regeneration inputs |
| Network access | Wave-2 primary-source verification | assumed ✓ | playwright-cli available per CLAUDE.md if needed |

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test framework
| Property | Value |
|---|---|
| Framework | pytest (repo suite; 322 passed baseline, quick 260623-9tu) |
| Quick run | `python -m pytest -q` (vcc-main env) |
| Full suite | same (suite is fast; no GPU tests in default run) |

### Phase gates → checks map
| Gate | Check | Automated command |
|---|---|---|
| Build clean | zero LaTeX errors / undefined refs / undefined citations | `build_thesis.ps1 -Clean` + built-in .log scan (new; §7) |
| Number audit | every number → PROVENANCE.md → tracked source | Wave-3 multi-agent audit (Phase-12 standard); grep-based headline-consistency (82.5/78.7 byte-identical in abstract/chapters/tables/conclusion) |
| Overclaim scan | honesty framings present; no SOTA/online-TTA/clean-AUC-gain claims | Wave-3 scan (Phase-12 token list) |
| Structure | TOC matches spec §4; every figure/table referenced; all chapters present | Wave-3 structure check |
| Tracking | every manifest source tracked | `git ls-files --error-unmatch <each path>` in Wave 0 (hard assert) |
| Repo hygiene | pytest green; artifacts ignored | `python -m pytest -q`; `git status` clean of thesis build artifacts |

### Wave 0 gaps
- [ ] `scripts/build_thesis.ps1` (new) with preflight + log-scan
- [ ] `thesis/.latexmkrc` (new)
- [ ] gitignore: thesis artifact patterns + results/ un-ignore mechanics (§3)
- [ ] ~269 file trackings + assertions (§3 list)
- [ ] 2 new small figure/table scripts (severity heatmap; corruption heatmaps; per-category table generator) — tracked, Class R

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | CTAN IEEEtranN.bst current version may differ from local v1.13 (could not byte-compare offline) | §7 | negligible — v1.13 is complete/authentic; provenance note covers it |
| A2 | Survey-support citation details (ST-GCN AAAI 2018, ImageNet-C ICLR 2019, CORAL AAAI 2016, Schneider NeurIPS 2020) from training data | §6 | wrong bib fields — verify in Wave 2 gate before adding |
| A3 | Proposed bib keys/fields for the 11 new SOTA entries derived from 12-RESEARCH-sota.md §8 rows (venue/status for Holmes-VAD, PEL4VAD journal, AnomalyCLIP arXiv ID unconfirmed) | §6 | wrong entries — Wave-2 gate confirms every field |
| A4 | Network access available for Wave-2 primary-source fetches | Env | gate blocks; fallback = user-provided PDFs |
| A5 | `\resizebox{\textwidth}` one-column rendering of the swimlane TikZ is legible at A4 width | §7 | figure redesign/rotation needed (writer discretion) |
| A6 | Phase-6 A/D/E/F PNGs are stale w.r.t. post-λ0/post-h1 checkpoints (inferred from dates, not re-measured) | §4 | if actually current, regeneration wasted ~minutes; verification pass决定 per figure |

## Open Questions

1. **Per-condition continual TENT/SAR table in Ch 6?** Tracked summary covers the null-result claim; a per-condition table needs either ~880 small JSON trackings or (recommended) one generated+tracked rollup CSV. → Planner decides; recommend the rollup CSV (also softens C7-1).
2. **Promote `scripts/_tmp_r1_full.py` + 3 deps (C7-1)?** Not strictly required for provenance (tracked pri5/aggregate scripts + tracked JSONs suffice), but Appendix E's reproducibility story is stronger with them. → Planner discretion; low cost.
3. **`\include` vs `\input` for chapters** — recommend `\include` for partial-build speed during Wave-1 parallel drafting. → Executor discretion.

## Sources

### Primary (HIGH confidence — verified in-session against the repo)
- `docs/superpowers/specs/2026-07-05-full-thesis-design.md` (binding spec, read fully)
- `.planning/phases/13-full-thesis-manuscript/13-CONTEXT.md` (read fully)
- `paper/main.tex` (457 lines; all cited line anchors spot-verified), `paper/sota_comparison_full.tex` (markers + RE-VERIFY rows grep-verified), `paper/references.bib` (27 keys listed), `paper/.latexmkrc`, `scripts/build_paper.ps1` (read fully)
- `git ls-files` audits (results/ 28-file list; source-file tracking assertions)
- `scripts/generate_phase7_charts.py` (baseline lines verified), `scripts/corruption.py` (severity params verified)
- `results/` on-disk inventory (128 run dirs, _analysis_2026-06-10 11 files, benchmark CSVs, _tta_rerun_continual structure, phase6_charts 26 PNGs, JSON structures of summary_3seed/r1full/variants)
- `.planning/phases/12-*/12-VERIFICATION.md` lines 129–153 (17-item checklist, read directly), `12-RESEARCH-sota.md` §8 lines 150–188 (read directly)
- Local MiKTeX: IEEEtranN.bst header + kpsewhich resolution; latexmk/perl/vcc-main availability probes

### Secondary (MEDIUM — session ctxmap readers, cross-checked where cheap)
- Scratchpad ctxmap 7 files (paper-structure, thesis-fragments, planning-state, open-issues, results-figures, phase-findings, template-dir) — durable content consolidated above; **scratchpad must not be referenced downstream**
- `.planning/STATE.md`, `REVIEW-2026-06-10.md`, `ANALYSIS-2026-06-10-zero-gpu.md` content via ctxmap (files verified tracked)

### Tertiary (LOW — flagged)
- CTAN IEEEtran version status (WebFetch of ctan.org/pkg/ieeetran: class v1.8b, 2015-era updates; .bst-specific version not shown) — A1
- Training-data citation details for survey-support bib entries — A2/A3

## Metadata

**Confidence breakdown:**
- Per-chapter inventory: HIGH — every path/line anchor verified or spot-verified
- Canonical numbers: HIGH — cross-verified spec §7 ↔ main.tex tables ↔ tracked JSONs (TENT/SAR deltas recomputed from summary_3seed.json this session)
- Git audit / Wave-0 list: HIGH — direct `git ls-files` + on-disk enumeration
- Figure provenance: HIGH for existence/tracking; MEDIUM for staleness judgments on Phase-6 PNGs (A6)
- LaTeX build: HIGH for local toolchain facts; MEDIUM for one-column TikZ legibility (A5)
- Bib plan: MEDIUM — entry fields pend Wave-2 primary-source confirmation by design

**Research date:** 2026-07-05
**Valid until:** stable (repo-frozen inputs; re-verify only if new commits touch paper/, results/ tracked set, or planning docs)
