# Zero-GPU Analyses — 2026-06-10 (REVIEW-2026-06-10 Pri 5/6/7/9)

Produced by workflow `wf_a7f97072-ec2` (4 analysis agents + 1 adversarial verifier).
**Verification: PASSED, no blocking issues** — the verifier independently reproduced the
Pri-6 label-reconstruction gate to abs-diff **0.0** and recomputed Pri-5's headline numbers.

Reproducible scripts (committed): `scripts/pri5_tta_breakdown.py`,
`scripts/analyze_pri6_bootstrap_ci.py`, `scripts/analyze_pri7_per_class.py`,
`scripts/analyze_pri9_failure_cases.py`, `scripts/_verify_pri5_pri6_2026-06-10.py`.
Outputs (gitignored, regenerable) live in `results/_analysis_2026-06-10/`.
All CPU-only (numpy/sklearn), deterministic (`default_rng(12345)`), no torch/CUDA.

---

## Pri 5 — Per-corruption-type TTA (disc_reweight) breakdown

**Per-backbone × per-family mean ΔAUC (points), 3-seed mean** (s42 from canonical
`r1full_*.json`, s123/s2024 from `results/_coral_derisk/variants/`):

| Backbone | Gaussian | Motion blur | JPEG | Brightness |
|---|---:|---:|---:|---:|
| CLIP ViT-B/16 | +2.67 | 0.00 | 0.00 | +0.01 |
| SigLIP2-base | +5.99 | 0.00 | 0.00 | 0.00 |
| SigLIP2-SO400M | +8.95 | 0.00 | 0.00 | 0.00 |
| SigLIP2-giant | +1.69 | 0.00 | 0.00 | 0.00 |
| **Average** | **+4.83** | 0.00 | 0.00 | 0.00 |

Prose reproductions (all PASS): gaussian cross-backbone 3-seed avg **+4.826**;
SO400M gaussian **severity-5** 3-seed **+13.19 (≈+13.2)** (per-seed 13.92/12.34/13.31 —
exactly the REVIEW triple, and confirms the Batch-C P1 fix `+13.9→+13.2`); base s42
gaussian_5 **−3.20**. Stale "+13.9" = SO400M s42 gaussian_5 = +13.92 (single-seed).

**Precision nuances (must honor if any number reaches the paper):**
- `+4.826` is the 3-seed cross-backbone gaussian-**family** mean. Seed-42-only is **+3.31** (different).
- `+13.2` is gaussian **severity-5** 3-seed; the 5-severity gaussian-family mean for SO400M is **+8.95**.
- Non-gaussian families are exactly 0.00 **by construction** (the R1 reliability gate routes
  blur/JPEG/brightness back to source → d=0), NOT "TTA hurts on blur." Needs a one-line footnote.
- Canonical CORAL 3-seed data is in `results/_coral_derisk/variants/`, NOT `summary_3seed.json`
  (that file is TENT/SAR overall-AUC: 3-seed Δ all ≈0, consistent with the LN-barrier finding).

**Integration:** candidate paper 4×4 mini-table (3-seed column) +
`pri5_per_condition_heatmap.csv` (20×4) as a thesis severity heatmap. **Page-limit decision
pending** (paper already 10pp).

---

## Pri 6 — Video-level bootstrap 95% CIs (defense insurance)

Sanity gate **EXACT** (pooled frame AUC = stored, abs-diff 0.0, both datasets;
double-confirmed by the verifier). Bootstrap resamples **videos** (B=2000, seed 12345).

| Dataset | Metric | Point (s42) | 95% CI | Width |
|---|---|---|---|---|
| UCF | AUC | 82.49% | [75.63, 88.02] | **12.39 pp** |
| XD | AP | 79.74% | [76.62, 82.68] | **6.06 pp** |

Reproduces the REVIEW probe (UCF CI width ~12.7pp → actual 12.39pp). Point estimates sit
inside their CIs. **Key takeaway:** test-set sampling uncertainty (~12pp UCF) ≫ seed std
(~0.1–0.4pp) — i.e. the headline's real uncertainty is dominated by which test videos you drew,
a property *all* VAD numbers on 254-video UCF share.

**Caveat:** the XD CI is on the **s42** run (AP 79.74%); the 78.7% headline is the 3-seed mean.
**Integration:** thesis robustness/limitations footnote (NOT the paper main table — a 12pp CI is
honest but visually undercuts the headline; the multi-seed spread is the conventional paper metric).

---

## Pri 7 — Per-class UCF complementarity (giant backbone, 3-seed)

Δ = gated.auc − visual-only.auc per category. **Group means:** HUMAN-MOTION (10 classes)
**+0.31 ± 1.08 pp** (7/10 positive); APPEARANCE/no-human {Arson, Explosion, RoadAccidents}
**−0.29 ± 0.16 pp** (0/3 positive); **HM − APP = +0.60 pp**.

Cleanest single point: **Shooting +1.05 pp** (n=22, seed σ=0.20 — the most trustworthy).
Strongest gains are pose-driven (Fighting/Arrest/Shooting +1.0–1.7). But the within-HM spread
(σ=1.08) **exceeds** the between-group gap (0.60), and the 3 biggest negatives (Robbery −1.46,
Assault −0.87, Abuse −0.80) are all human-motion classes — all tiny-n (Abuse n=2, Assault n=3),
so plausibly sampling noise.

**Verdict: directionally supportive but mixed/noisy.** Per-class test sets are tiny.
**Integration:** thesis appendix only, hedged ("directionally consistent ... suggestive not
conclusive"). Do NOT report the Welch t (negligible power, 3 appearance classes). Not paper main body.

---

## Pri 9 — Qualitative failure cases (giant s42, UCF)

Sanity gate EXACT (pooled frame AUC 0.824904 = stored). Cohort: 254 videos = 128 anomaly + 126 normal.

**Worst anomaly videos (per-video frame-AUC):** Burglary017 (0.057), Shooting028 (0.114),
RoadAccidents011 (0.142), Explosion007 (0.145), Shooting018 (0.145). **Two regimes:**
(1) *saturated-high near-ties* (Burglary/Shooting/Explosion — head pins ~all frames at ~0.99,
ranking marginally favors normals by 0.0001–0.004); (2) *short-event miss* — RoadAccidents011
scores the brief accident (1.9% of frames) ≈0.000.

**Top false-positive normals:** Normal_Videos_887/925/884/895/894 — sustained scene-wide
over-firing (~100% of frames > 0.5 on correctly-labeled-normal clips).

**Score distribution (pooled frames):** anomaly mean 0.874 / normal mean 0.382; heavily bimodal
but **normal p75 = 0.986** — >25% of normal frames are pushed to ~0.99. The 0.825 AUC is carried
by the suppressed normal majority; the over-fired normal tail drives the failures.

**Honest limitation (thesis-grade):** poor calibration / over-confidence (snippet-pooled head
saturates) + weak short-abrupt-event localization.
**Integration:** thesis failure-analysis subsection (paper has 1 success, 0 failures) +
`pri9_score_hist.png`. Paper: at most a 1-sentence worst-case + FP-saturation mention.
Minor: stored `video_auc` 0.9268 recomputes to 0.9452 (secondary metric, different pooling grid;
the binding frame-AUC gate is exact) — worth a separate look later, not blocking.

---

## Net integration guidance

- **Paper (needs decisions, page-limited at 10pp):** Pri-5 mini-table is the strongest paper
  candidate (makes +4.8/gaussian-only/per-backbone checkable). Everything else → thesis.
- **Thesis (no decision needed, additive):** Pri-5 heatmap, Pri-6 CI footnote, Pri-7 appendix
  (hedged), Pri-9 failure subsection + histogram.
- Nothing here changes a headline number. Pri-6 independently re-confirmed UCF 82.5% and the
  Batch-C P1 `+13.2` value.
