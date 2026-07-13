# Thesis Review — 2026-07-11 (NTUST compliance + oral-defense readiness)

**Scope**: `thesis/main.pdf` (128 pp, 110 body) + all LaTeX sources, reviewed against the English-applicable rules of `thesis/thesis_requirements.pdf` (NTUST 學位論文撰寫、編排規則, 112.03.07 第211次教務會議) and for oral-defense readiness.
**Method**: 127-agent workflow (17 review units: 4 compliance, 11 content, 2 cross-cutting; BLOCKER/HIGH findings verified by 3 independent adversarial verifiers, MEDIUM by 1). 137 raw findings → 126 survived, 1 refuted. Orchestrator-measured format facts verified directly with PyMuPDF.
**Verdict**: **NOT yet submission-ready and NOT yet oral-ready.** Content is fundamentally sound (numbers trace to PROVENANCE.md; equations match code; honesty framing is strong), but there are 3 content blockers/HIGH clusters that a committee would catch in minutes, plus a batch of NTUST format violations that are mechanical to fix, plus 40 defense questions the thesis currently cannot answer.

Full machine-readable findings: `scratchpad/review_result.json` (session temp); condensed: `findings_condensed.md`, `defense_and_strengths.md` (same dir).

---

## 1. NTUST format compliance matrix

Measured on the rendered PDF (PyMuPDF), not guessed.

| Rule | Requirement | Status |
|---|---|---|
| R1 paper | A4 21×29.7 | ✅ exact on all 128 pages |
| R1 margins | top 3 / bottom 2 / left 3 / right 3 cm | ❌ **2.5 cm uniform** (`preamble.tex:7`) |
| R1 page numbers | centered bottom, every page | ✅ (title page unnumbered — LOW, confirm with dept) |
| R2 font | Times New Roman (English), black | ❌ **Latin Modern** (`preamble.tex:13`); black ✅ |
| R2 title size | 24 pt bold | ❌ renders **20.7 pt** (`titlepage.tex:14` uses `\LARGE`) |
| R2 "Abstract"-style headings | 20 pt bold + 2 blank lines | ❌ render 24.8 pt (`\Huge`); gap ✅ (~43 pt) |
| R3 front-matter numbering | UPPERCASE Roman Ⅰ Ⅱ Ⅲ | ❌ lowercase i, ii (`main.tex:15` → use `\pagenumbering{Roman}`) |
| R3 body numbering | Arabic from 1 | ✅ restarts at 1 on Ch. 1 |
| R4 binding order | cover→title→推薦書→審定書→中文摘要→英文摘要→誌謝→目錄→符號索引→圖目錄→表目錄→正文→**參考文獻→附錄** | ❌ multiple: see §2 |
| R5 cover/title fields | title, student, advisor, school **and department**, year-**month** | ❌ department + month missing; English-only page |
| R6 abstract | ≤500 words/1 page; argument+method+content+results; **5–7 keywords** | ⚠️ 296 words ✅, coverage ✅, **keywords missing**; **Chinese abstract missing entirely** |
| R7 LoF/LoT | required ≥5 items; figures listed before tables | ✅ 18 figures / 22 tables, correct order |
| R8 headings | chapter titles **centered** 20 pt; sections left 18 pt; body 12–13 pt; 1.5 spacing | ❌ chapters flush-left 24.8 pt; sections ✅ left but 17.2 pt; body ✅ 12 pt; spacing ✅ exactly 1.5 |
| R9 first-use/citations | expand terms at first use; every claim sourced | ⚠️ mostly ✅; ~8 first-use lapses (CTR-GCN, C3D, MLLM, t-SNE, MACs, AUPRC, TCN) |
| R10 figures/tables | per-chapter numbering; captions w/o abbreviations; referenced by number; within text width | ⚠️ numbering ✅ (dotted form), zero orphan floats ✅, caption placement ✅; **30/40 caption titles contain abbreviations**; **5 tables overflow right margin** |
| R11 references | uniform style (IEEE OK) | ⚠️ IEEEtranN uniform ✅, 42/42 cited ✅; 2 wrong-author/wrong-year entries (HIGH, §3), 4 arXiv entries render sourceless, misc field gaps |

## 2. Submission blockers (fix before printing)

**S1. Missing required front-matter elements (R4/R6)** — no 中文摘要 (+5–7 中文關鍵詞), no English keywords, no 指導教授推薦書 page, no 學位考試委員審定書 page, no cover page distinct from the title page and no spine (書背) text prepared anywhere in the repo. Acknowledgments is still the `[to be written]` placeholder.
**S2. Ordering violations (R4)** — Bibliography is placed AFTER the appendices (`main.tex:42-56`; rule: references precede appendices). Notation/symbol list is placed after LoF/LoT (`main.tex:19-22`; rule: 符號索引 before 圖目錄/表目錄). Bibliography also missing from the TOC and titled "Bibliography" instead of "References".
**S3. Geometry/font batch (R1/R2/R3/R8)** — margins 2.5→3/2/3/3 cm; Times New Roman (e.g. `newtxtext/newtxmath` or XeLaTeX+TNR); `\pagenumbering{Roman}`; chapter titles centered at 20 pt via `titlesec`; sections 18 pt; title page title at 24 pt bold. One rebuild fixes all; expect pagination to shift everywhere (re-check overflows after).
**S4. Title page fields (R5)** — add department (系所), degree program name ("Master of Science in …" — currently bare "the degree of Master"), graduation year-**month** (July/Aug leavers print June), and the Chinese elements per 附錄一 template (Chinese school/dept/degree lines, Chinese title, 中華民國 date). A Chinese thesis title must exist for cover + spine.

## 3. Content blockers / HIGH (defense-derailing) — all independently verified

**C1. 🔴 BLOCKER — Figure 5.2 shows RoadAccidents127, the worst anti-aligned test video, under a caption claiming alignment** (`ch05_results_fusion.tex:386-402`, PDF p.61; byte-identical to the known paper erratum figure). Verifiers re-rendered the page and recomputed from `results/ucf_gated_fusion_s42/eval_scores.npz`: gated score ≈0.95 across the normal segment, ≈0.0 inside the GT window; in-GT-minus-normal gap −0.742, worst of all 128; per-video AUC ≈0.10. Caption + §5.7 prose ("sharper score peaks aligned with the anomalous event", "concentrates its score mass on the annotated event window") assert the opposite. Four review units independently flagged it; the mock committee marked it "indefensible as printed — any examiner pointing at the projector". **Fix**: regenerate with Fighting047 (already validated for the CGW talk: gap +0.48) and rewrite caption/§5.7; update PROVENANCE.md:90 and Appendix F's "adds three more" framing; fix the same figure in the paper (open erratum).

**C2. HIGH — Two corrupted bibliography entries with wrong authors/year:**
- `references.bib:122` PYSKL credits "Haodong Yan, Zhigang Tu, Yonghong Hou, Qing Li" — actual authors: **Haodong Duan, Jiaqi Wang, Kai Chen, Dahua Lin** (DOI in the entry is correct and confirms it). Cited 3–4× incl. ch03 methodology.
- `references.bib:112-119` doshi2022skeleton: title is the CVPRW **2020** "Any-Shot Sequential Anomaly Detection" paper but year/DOI say CVPRW 2022; worse, it is the **sole skeleton-VAD citation** in the thesis and it is **not a pose/skeleton paper** — the ch01 motivation ("skeleton-based … explored for anomaly detection") and ch02 description ("pose trajectories in a modular framework") do not match its content. **Fix**: correct PYSKL authors; replace/supplement doshi with the canonical pose-trajectory VAD line (Morais CVPR 2019, Markovitz GEPC CVPR 2020, Hirschorn STG-NF ICCV 2023) — this also closes the "your skeleton survey is one wrong paper" committee question.

**C3. HIGH — CGW '26 paper never cited, thesis delta never stated** (`ch01_introduction.tex:171`). "extending the study reported in our CGW '26 workshop paper" with no bib entry, no title, and no enumeration of what the thesis adds; ch05's "disclosed in the paper" dangles. First question of any defense is "what's new beyond the paper". **Fix**: add self-citation + 3–4-item thesis-delta list (3-seed six-variant ablations, per-category/failure analysis, RTFM reproduction appendix, six-strategy TTA search narrative, appendices D–F).

**C4. HIGH — Stale/incorrect claims vs the thesis's own tables** (each verified against unrounded run data):
- `ch05:98-101`: "gated beats late on three of the four on UCF (lone exception SigLIP2 Base)" — **wrong; gated beats late on all 8/8 cells** (Base: 79.0 vs 77.2). Single-seed-era sentence inherited from the paper (fix there too). Also contradicts ch07 §7.3's "consistent underperformance of late fusion".
- `ch06:329` + Fig 6.3 caption: "+13.2 in the single most-degraded condition in the benchmark" — **wrong; JPEG cells are more degraded** (SO400M jpeg s5 = 39.2 < gaussian s5 = 44.7; global min Base jpeg s4 = 37.1). Paper uses the correct qualifier ("the corruption that most collapses the visual stream") — adopt it. Same wrong label in ch09 ("most visually-degrading", also drifts from the PROVENANCE canonical label).
- `ch06:41-42` Fig 6.1 caption: "degradation deepens monotonically with severity in every family" — **contradicted by the plotted data** (Base Gaussian column *improves* 51.8→63.3 with severity; several non-monotone columns).
- `ch08:47`: Sultani's 75.41 (a UCF **AUC**) quoted as the comparison point in an **XD AP** sentence — contradicts ch07 footnote l's own discipline. Delete the parenthetical.
- `appC_sweep.tex:44-48`: "reproduced the historical sweep-era baselines exactly — … 82.27% AUC" — UCF default cell is **82.26** (Fig C.1 displays 0.8226 in the same figure). Only XD is exact.

**C5. HIGH — Broken promise: ch05 declares score calibration "the binding limitation of the current head, and we return to it in Chapter 8" (`ch05:566`) — Chapter 8 never mentions calibration, thresholds, or false-alarm rate.** Add the limitation (normal-frame p75 = 0.986 → severe fixed-threshold false alarms) to ch08; it is also a mock-committee question.

**C6. HIGH — ch07 "strongest single piece of evidence" is logically overstated** (`ch07:35-44`): "if the skeleton carried no usable information, no weighting scheme could recover 12 points by consulting them" — false by the thesis's own Table 5.2: a gate that merely suppresses a pure-noise skeleton recovers 10.7 of the 12.6 points (63.9→74.6 visual-only level). The real evidence is the +1.9 gated-vs-visual margin + the 8/8 pattern. Reframe (suppression component vs extraction component).

## 4. HIGH defense-prep gaps (disclosure and/or cheap experiment recommended)

These four were confirmed by 3/3 adversarial verifiers each; they cannot be fully fixed by wording alone.

**D1. 64×64 / ~3 FPS UCF-Crime input disclosed only in Appendices D.2/F.1** — never in §4.1.1 (which discloses only 3 FPS) nor in the ch07 comparison tables where 82.5 sits against methods using ~320×240 originals. *Fix*: disclose in §4.1.1 + a caveat in Table 7.1/7.2 captions. *Prep*: be ready to bound the effect (small full-resolution re-extraction on a test subset would be the gold answer).

**D2. λ₂ (the one dataset-dependent hyperparameter) is justified by its effect on "the AP metric" — a test-set quantity** — while §4.1.3 asserts frame-level information "plays no role in any training or selection decision". The thesis never states what data drove the λ₂=0 decision. *Fix*: state the decision procedure in §4.4 and frame it as a disclosed protocol deviation. This is the statistics examiner's sharpest question.

**D3. The clean-skeleton-cache assumption under Gaussian/brightness ("RTMPose produces effectively identical keypoints") is asserted, never measured** — and 100% of the headline robustness gain (+1.21 mean, +13.2 max) lives exactly in those conditions; the z_skel≈z₀ gate check is circular for reused-cache conditions. *Prep (recommended)*: a small keypoint-delta run (re-extract a sample under gaussian s3–s5, measure OKS/deviation, ideally re-run reweighting with re-extracted skeletons). If it holds, one sentence + a table row makes the +13.2 defensible; if not, better to know before the committee asks.

**D4. disc_reweight is the survivor of a six-strategy search evaluated on the same 20 conditions it is reported on — no held-out check** — while the thesis itself kills TENT/SAR post-hoc-selection and CORAL via leave-one-family-out. *Fix*: state the structural defense explicitly (zero tuned hyperparameters, zero updated parameters, a-priori factor-2 anchor, gate saturation). *Prep (recommended)*: run LOCO (or an unseen corruption family) for disc_reweight — cheap, and converts the weakest methodological point into a strength.

## 5. MEDIUM (43) — grouped

**Format** (fix during the S3 rebuild): heading sizes 24.8/17.2 vs 20/18 pt; degree line lacks program name; Bibliography not in TOC + naming; 5 tables overflow the right margin (T4.1 +21 pt, T4.2 +44 pt, **T5.1/T5.2 +45 pt (headline tables)**, TD.1 +59 pt); 30/40 caption titles contain abbreviations (published rule 標題不得使用縮寫 — batch-fix by spelling out first words or confirm dept tolerance); no short captions → LoF/LoT span 7 pages incl. internal audit jargon; 4 arXiv @misc entries render with no source (add `note={arXiv:…}`); "J. ao Carreira" name mangling; pu2024pel4vad missing volume/pages.

**Content consistency**:
- ch01: "~88–91% leaders are fine-tuned and text-aligned" contradicted by own Table 7.1 (GS-MoE 91.58 is frozen/no-text); "two architectural families" vs ch03/ch05 "all four ViTs".
- ch02: open-vocabulary VAD line absent; skeleton-VAD lineage = 1 (wrong) citation; Table 2.1 missing six surveyed methods vs caption.
- ch03: solo-score text says input zeroed, code zeroes projection **output** (under an "exactly as implemented" chapter claim); `s` symbol collision (snippet score vs reliability gate); p_clip ≡ v̂ never stated; sparsity mislabeled "feature-magnitude formulation of RTFM" (it's score sparsity; RTFM's feature-magnitude loss is the thing the thesis *doesn't* use); Eq. 3.6 smoothness scope (abnormal-only) undisclosed; NTU RGB+D 120 dataset paper uncited.
- ch04: second XD exclusion (corrupt MP4) undisclosed → 3,954-video accounting off by one; "~30 ms/frame (21.6 FPS)" self-contradictory (21.6 FPS = 46 ms; appD says 46 ms — reconcile).
- ch05: §5.8/§5.9 weak-category cross-refs falsified by the per-category table (Shooting is 4th strongest, 95.67; Robbery never named by the failure analysis); pooling paragraph internal contradiction ("every backbone" vs "helps only SO400M"); CI-vs-leaderboard-spread overclaim (12.39 pp CI < 16.17 pp spread).
- ch06: "Gaussian is the deepest failure mode" vs figure (JPEG deeper); "Base loses most, CLIP least" wrong (SO400M drops most); "gain growing with severity" false for Base; Fig 6.2 caption describes TENT/SAR bars that aren't plotted; CORAL rejection sentence misdescribes protocol (family-level LOCO, video-level-label operating point, exact −1.6x).
- ch07: Table 7.1 sort violates own caption (EventVAD 82.03 above This-work 82.5); "well above the founding Sultani baseline" on XD rests on a number both tables refuse to tabulate.
- ch08: per-category weaknesses (XD Abuse 43.6 / Car Accident 48.2 AP; UCF short-event tail) never acknowledged as limitations; RTFM gate anchor inconsistency vs App A (84.30 UCF vs 77.81 XD, "pre-registered" conflict).
- ch09: "under heavier budgets" claim contradicted by Table 7.1 top row.
- appA: cites a "0.02 sanity ceiling used throughout this thesis" that is defined nowhere; appB "exactly … Section 5.8's set" mismatch (Robbery vs Shooting); appE: `evaluate.py` does NOT append to results-index (that's `run_ablations.py`); appE lines overrun the page edge (clipped semicolon).
- mock-committee: GF 2-Person described as replacing "single-person aggregation" but the default is M=2 mean-pool (contradiction with ch03 + code); sign test is the only statistic where a per-video paired bootstrap would be stronger and is never run.

## 6. LOW (57) — one-liners in `findings_condensed.md`

Typos/wording (analyses→analyzes, missing antecedents, em-dash splits), first-use lapses (CTR-GCN, C3D, MLLM, t-SNE, MACs, AUPRC, TCN), "SigLIP2 Base" alias never defined vs "SigLIP2 ViT-B/16", 'skeleton-trust' vs 'skeleton-reliability' gate naming, +3.72 vs displayed-operand 3.71, ch09 §"Code and Data Availability" contains no data-availability statement or release location, internal jargon leaks ("P4 baseline", "Pri-9", "Phase 7 Sweep" in rendered figures/appendices), blank page xiv, brightness/motion-blur ImageNet-C implementation deviations undisclosed, appF best-case selection criterion undisclosed, PRD expanded as "pre-registered research plan", bash line-continuations in Windows command listings, etc.

**Refuted (1)**: ch02's "no surveyed method keeps a separately encoded auxiliary stream behind a learned gate at inference" survives only via the "learned gate" qualifier — verifiers found HL-Net/HyperVD/Ghadiya audio-visual streams make it defensible but fragile; tighten wording (kept as the ch02 MEDIUM/defense item).

## 7. Oral-defense readiness

94 committee-grade questions generated; **54 the thesis already answers** (strong: honesty framing §1.6, transductive disclosures, episodic-inertness diagnosis, RTFM gap localization, 8/8 complementarity discipline, refusing to promote GF-2P maxima). **40 gaps** — full list in `defense_and_strengths.md`. The ones to prepare hardest (beyond §4 D1–D4):

1. Figure 5.2 walkthrough (moot once C1 fixed).
2. "What's new beyond the CGW paper?" (moot once C3 fixed).
3. Skeleton-VAD literature anchor (moot once C2 fixed).
4. Why can't the learned gate g down-weight a corrupted visual stream by itself — why is external w needed?
5. Solo scores s_clip are off-manifold (gate never saw zeroed skeleton in training) — why is their dispersion a valid reliability estimate?
6. Hinge margin 1.0 on [0,1] sigmoid scores never clips — why this margin, sensitivity?
7. BN-vs-LN batch-contamination argument has no BN-head control experiment.
8. Fixed-w / oracle-w baseline for the reweighting ("isn't this just 'trust skeleton more when noisy'?").
9. Named modern TTA baselines beyond TENT/SAR (CoTTA/EATA/MEMO/T3A) — structural argument exists, no empirical row.
10. Val-MIL-loss ↔ test-metric correlation for checkpoint selection.
11. SO400M-vs-Giant XD ranking distinguishability (0.9 vs 2.8 std, n=3).
12. Top-2-person cap in crowd violence (Riot) — not in limitations.
13. n=3 seed-std noisiness; sign-test on full-precision values.
14. "Will be released" with no URL/DOI/scope (ch09 §9.3).
15. App A flow-concat tension with the thesis's own weak-stream-helps-strong-stream logic.

**Strengths to lead with** (verified): every ch03 equation matches code line-for-line; every ch04 hyperparameter matches committed configs; dataset accounting recomputable from the committed manifest; Tables 5.1/5.2 byte-identical to canonical results and re-derived to 3 decimals; zero broken cross-references; zero orphan floats; 42/42 citations; pre-registered gate misses reported as misses; disclosure discipline (transductive, exclusions, no-SOTA) unusually strong for a master's thesis.

## 8. Recommended fix order

1. **P0-content** (hours): C1 figure swap + caption/prose; C2 two bib fixes + skeleton-VAD citations; C3 self-cite + delta list; C4 five claim corrections; C5 ch08 calibration paragraph; C6 ch07 reframe.
2. **P0-format** (one focused pass): S3 geometry/font/heading batch → S2 reordering → S1 new front-matter files (Chinese abstract + keywords ×2, cover+spine, 推薦書/審定書 placeholders, acknowledgments) → S4 title-page fields. Rebuild, then re-check the 5 overflowing tables + appE verbatim overflows at the new 3 cm margins.
3. **P1-medium** (a day): §5 list, prioritizing caption-vs-data contradictions and cross-chapter inconsistencies.
4. **P1-defense** (before oral): D1–D4 prep incl. the two cheap runs (keypoint-delta; disc_reweight LOCO); rehearse the §7 list.
5. **P2**: LOW polish.

Paper erratum reminder: C1 and the C4 "three of four" sentence exist verbatim in `paper/main.tex` — fix both there when touching the paper (camera-ready).
