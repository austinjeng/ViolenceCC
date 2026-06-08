# Code ↔ Paper Match Review — ViolenceCC / CGW '26

**Date:** 2026-06-07
**Scope:** Does the code + committed results match `paper/main.tex`?
**Method:** 12-dimension multi-agent audit (architecture, loss, skeleton pipeline, visual pipeline, hyperparameters, datasets/splits, Tables 1–3, disc_reweight method, TENT/SAR method, discussion claims). Every finding adversarially re-verified against the real files.
**Result:** 82 findings, **0 false positives**. Headline numbers are correct. Method core matches the equations. The defects are concentrated in the TTA section (provenance + one overstated bound) and in a handful of imprecise/undisclosed prose details.

---

## ✅ RESOLUTION STATUS — ALL RESOLVED (2026-06-09)

Every finding below was fixed (or consciously left with verified rationale) across ~12 commits on `main` (`22ddb20`→`aa5120b`, pushed to `origin/main`). Each MEDIUM/LOW edit was adversarially pre-checked by a skeptic workflow before applying. Paper rebuilds clean (0 undefined refs, 0 errors, 10 pages); headlines UCF 82.5% / XD 78.7% intact throughout.

| Finding | Resolution | Commit |
|---|---|---|
| **H1** TTA Table-3 provenance | Force-added backing JSONs + tracked `aggregate_tta_table.py` regenerator | `22ddb20` |
| **H2** "≤0.004 pp" entropy bound | → "<0.1 pp" ×3 (abstract, caption, §4.5) + abstract unit fix | `9ba9d00` |
| **H3** category-adaptive gating + Figure 7 | Dropped figure + claim; complementarity re-anchored on XD late→gated gap | `57b4e86` |
| *(bonus)* `:263` "all backbones" late-fusion claim | Corrected (SigLIP2 Base UCF excepted) | `c7791d1` |
| **M1** PreNormalize2D bbox-vs-image | Reframed to image-center; dropped false invariance claims | `7280746` |
| **M4** evaluated UCF n=254 | Disclosed | `7280746` |
| **M3** "2–4 frames/snippet" | Per-dataset snippet duration disclosed (UCF ≈20 s/~20 frames, XD ~2.7 s/~3) | `a1b68ff` |
| **M6** undisclosed gate constant | Disclosed gate form (2× anchor, saturates {0,1}) | `2404d5c` |
| **M7** complementarity within-noise | **Ran matched-seed visual-only** (`m7_visual_seeds`); regression was a single-seed artifact; reframed to small/consistent (8/8, sign p≈0.008); tables→3-seed; figure regenerated | `d9df6db`, `e77f464` |
| **M5** Table-3 TENT/SAR cells | Dropped the TENT/SAR columns (wrong baseline; matches figure) | `a97922c` |
| **M2** 21.6 vs 33.3 FPS | Kept 21.6 (real `02-UAT.md` measurement, 1-person rate); fixed benchmark comment | `a97922c` |
| *(bonus)* `:272` stale 81.1/2.5 from M7 edit | → 81.2 / 2.6 pp | `a97922c` |
| **LOW** L1, L3, L4, L5(+T→T_f), param count 1,536, Giant figure label, stale-file banner | Applied (adversarially pre-checked) | `aa5120b` |
| **LOW** L6 Table-2 Late Δ +1.5 | **Left unchanged** — skeptic-verified raw-correct (table uses full-precision rounding) | — |

*Empirical corrections worth noting:* the "SigLIP2-Base/XD fusion regression" and "SO400M leads XD visual-only" were both **single-seed artifacts** the matched-seed runs overturned. See `project_code_paper_review_2026-06-09` memory.

---

## Verdict

The **paper is substantially faithful to the code.** All four fusion equations, the MIL loss, every training hyperparameter, the dataset/split counts, and every cell of Tables 1 and 2 reconcile to the per-run `eval_metrics.json`. Headlines verified: UCF 82.5% AUC (Giant gated, `auc=0.8249`), 83.0% (Giant mean-only), XD 78.7% AP (SO400M gated, 3-seed mean).

Issues are **3 HIGH** (all in the TTA story / a figure caption), **7 MEDIUM** (mostly undisclosed-but-defensible method details), **~9 LOW** (wording/rounding). None invalidates a headline result. The HIGH items are fixable with edits + one artifact commit; they do not require re-running experiments.

---

## What matches (confirmed)

| Area | Status |
|---|---|
| Gated fusion Eq (2)–(4): proj+LN, sigmoid gate, gated blend + residual highway, dropout after LN_f, g multiplies skeleton | ✅ exact (`gated_fusion.py:66-79`) |
| Late fusion Eq (1): independent heads, fixed 0.5 weight | ✅ exact (`late_fusion.py:68-74`) |
| MIL ranking loss Eq (6)–(7): top-k=3, margin 1.0, RTFM sparsity (mean-of-per-position-ℓ2 over abnormal bag), temporal smoothness | ✅ exact (`mil_loss.py`) |
| Hyperparameters §4.2: AdamW wd=1e-2, lr=1e-4, batch 16 pairs, 50 ep, patience 10, k=3, λ₁=8e-3 | ✅ uniform across 45 configs + 59 run snapshots |
| λ₂ dataset-dependent: 8e-4 UCF / 0 XD | ✅ every UCF and XD config/snapshot |
| Smoothness-fix footnote "≤0.13pp" | ✅ backed by `results/_smoothfix/measurement.md` (0.82490→0.82361 = −0.13pp) |
| Skeleton pipeline: (T,M=2,V=17,C=3), 4 streams (1.0/1.0/0.5/0.5), 64-frame non-overlap, M/T/V pool → 256-d, 172 UCF <64 exclusion | ✅ verified incl. 172/1900 empirically |
| Visual backbones: dims 512/768/1152/1536, mean+max concat → clip_dim 1024/1536/2304/3072, mean-only halves | ✅ matched to cached `.npy` shapes |
| Datasets/splits: UCF 1900 (800N+810A train, 150N+140A test, 13+1 cats); XD 3954/800; 15% stratified val | ✅ matched to split files |
| Table 1 (UCF AUC) — all 14 single-seed + 4 gated mean±std cells, bold = row max | ✅ trace to `eval_metrics.json` |
| Table 2 (XD AP) — all 21 cells, SO400M bold, Giant std 2.8 | ✅ trace to `eval_metrics.json` |
| Table 3 *numbers* (Source-Only / Ours / Δ±std / +1.21 mean) | ✅ reproduce exactly from working-tree JSONs |
| disc_reweight Eq: w_vl=min(1,σ_test/σ_clean), skel gate, w=1−(1−w_vl)·s applied to p_clip after LN in both terms | ✅ matches `disc_reweight.py` |
| TENT/SAR adapt only 3 LN affine (1536 params), continual protocol, lr=1e-3, SAR ρ=0.05 | ✅ matches `tent.py`/`sar.py` |

---

## HIGH

### H1 — Table 3 TTA numbers have no committed provenance
*(table3-tta-provenance/tta-artifacts-not-committed)*

The 3-seed Table 3 values (Source-Only, Ours, Δ) reproduce **exactly** from working-tree JSONs (`results/_coral_derisk/r1full_*.json` + `variants/v_*_{s123,s2024}_test.json`, entropy from `results/_tta_rerun_continual/summary.json`) — verified e.g. CLIP Source-Only mean(63.515, 63.619, 63.996)=63.71 → 63.7; Δ mean 0.665 → +0.67; std 0.230 → ±0.23. **But:**
- All backing files are under `.gitignore:9` (`results/`) and `git ls-files` confirms **untracked**.
- The generating scripts (`scripts/_tmp_r1_full.py`, `_tmp_r1_variants.py`, `_tmp_coral_derisk.py`, `_tmp_tta_harness.py`) are untracked `??` throwaways.
- `scripts/generate_latex_tables.py` still emits the **old** Table 3 format (TENT/SAR Δ≤0.6) and was never updated; `paper/tables_generated.tex` is correspondingly stale.
- Committed anchor exists (`src/tta/disc_reweight.py` + `evaluate_tta.py --method disc_reweight` reproduce the per-run math) but **no committed one-command regenerator** of the 3-seed table.

**Impact:** Numbers are correct and re-derivable *while the working tree exists*; if lost, the headline TTA result is unrecoverable from git. Violates the repo's own reproducibility mandate.
**Fix:** Commit the 12 `variants/v_*.json` + `_tta_rerun_continual/summary.json` (force-add past `.gitignore`, as already done for `phase10_charts/`), commit a tracked driver, and regenerate `tables_generated.tex`.

### H2 — "entropy TTA changes AUC by ≤0.004 pp" is too tight (actual up to ~0.069 pp)
*(tent-sar-method/tta-entropy-bound-too-tight + table3/tta-entropy-0004pp-bound-unsupported — same issue, two dimensions)*

Recomputed from seed-42 continual `eval_metrics.json` (paper hyperparams, `n_adapted_params=1536`), mean ΔAUC vs Source-Only over 20 conditions: CLIP +0.020 / Base **−0.068** / SO400M −0.035 / Giant +0.0005 pp. Only Giant is ≤0.004; **SigLIP2-Base is ~17× the claimed bound**; max per-condition |Δ| reaches 0.34 pp. The `0.004` figure appears in **no measured artifact** — only the planning draft.

The claim is stated **three times**: abstract (`main.tex:50`), Table 3 caption (`:300`), §4.5 (`:327`). The qualitative conclusion ("entropy TTA negligible, entries equal Source-Only at 1-dp") **holds** (0.069 ≪ 0.05 display resolution), so no table cell is wrong.
**Fix:** Replace "≤0.004 pp" with "<0.1 pp" (the author's own revision draft already proposes "≤0.1 point") in all three locations.

### H3 — Category-adaptive gating claim is unsupported AND the cited figure can't show it
*(discussion-claims/gating-by-category-unsupported — NEEDS_CONTEXT)*

Paper (`:343` caption, `:349` Discussion, restated Conclusion `:389`): the gate assigns "higher skeleton weights to … Fighting, Assault … lower to … Explosion, Arson," with "ḡ > 0.5 indicates stronger skeleton weighting." Two confirmed problems:
1. **Caption ↔ figure mismatch.** Figure 7 is `paper/figures/fig_gating_distribution.pdf` — rendered, it is a per-category **AUC/AP bar chart** of variants, with **no gate values, no 0.5 line, no boxplot** (its own generator docstring calls it a "proxy … avoids requiring GPU inference to extract raw gate values"). The caption describes a gate-value plot the figure does not contain.
2. **The real gate data contradicts the claim.** The actual gate boxplots (`results/phase6_charts/D_gating/D01_*`) show UCF categories all ~0.44–0.46 (**all below 0.5**), Fighting ≈ Assault ≈ Explosion ≈ Arson (~0.01 spread); XD all ~0.49–0.51. No motion-vs-scene separation. Gate direction itself is stated correctly (g·p_skel ⇒ higher g = more skeleton).

**Fix:** Either insert the real gate-value plot and soften the claim to the near-0.5 reality, or rewrite the caption/Discussion to describe per-category *fusion benefit* (what the bar chart shows) and drop the Fighting/Assault > Explosion/Arson skeleton-weight assertion.

---

## MEDIUM

- **M1 — PreNormalize2D centers on image center, not bbox midpoint** (`:124`). Code (`extract_skeletons.py:120-124`) does `(kp−w/2)/(w/2)` — image-frame normalization (correct PYSKL behavior). Paper's "midpoint of the detected bounding box" and the "invariance to absolute position" rationale are both wrong for this transform. *Fix: describe as image-center normalization to [−1,1]; drop bbox-midpoint and position-invariance claims.*
- **M2 — 21.6 FPS vs committed benchmark 33.3 FPS** (`:126`,`:213`, NEEDS_CONTEXT). `results/backbone_bench_rtmpose.json` (committed) records 33.3 FPS / 30.07 ms-per-frame; 21.6 FPS sits only in `STATE.md` free text, and `HANDOVER:159` flags the gap as unresolved. Plausibly different regimes (synthetic isolated-frame latency vs real-video end-to-end), but unreconciled. *Fix: report 33.3 FPS, or state 21.6 is end-to-end extraction and explain the gap.*
- **M3 — "~2–4 frames per snippet" wrong for UCF** (`:147`). Correct for XD (64 native ~24 FPS frames → 3 sampled). For UCF the 64 units are already-3-FPS PNGs spanning ~21 s → **~22** sampled frames/snippet. One dataset-specific figure presented as universal. *Fix: give both, or state it is the XD rate.*
- **M4 — Evaluated UCF test n=254 undisclosed** (`:204`). Every UCF `eval_metrics.json` has `n_videos=254`, not the stated 290; the 36-gap is the test-split share of the disclosed 172 <64-frame exclusions. Legitimate, but the reader cannot derive 254. *Fix: state evaluated n=254.*
- **M5 — Table-3 TENT/SAR cells = 3-seed disc_reweight Source-Only, not their own baseline** (`:306-309`). TENT/SAR were run single-seed-42 against the *continual* source (SO400M 60.68); Table 3 prints the 3-seed disc_reweight source (SO400M 58.9) in those cells — a 1.8 pp gap for SO400M. Harmless to the conclusion (entropy ≈ 0 from either baseline); the author's own draft item-8 flags it. *Fix: print the ~60.7 values or footnote that TENT/SAR were measured single-seed vs the continual source.*
- **M6 — Undisclosed "2× floor" slope in the skeleton-reliability gate** (`:195`,`:331`). `disc_reweight.py:184`: `skel_rel = clip((2·floor − skelZ)/floor, 0, 1)`. The `2` is a fixed design constant; the paper gives no functional form and says "no tuned hyperparameter." Not label-fit (so the strict claim survives), but an undisclosed magic constant. In practice binary (skel_rel ∈ {0,1} in all observed conditions). *Fix: state the functional form.*
- **M7 — Complementarity endpoint margins are within seed noise** (`:261`). Giant gated 82.5 (3-seed mean) vs visual-only 82.4 (seed-42) = +0.18 pp < its own gated std 0.36; CLIP +0.27 ≈ std 0.28. Visual-only has no error bar (no s123/s2024 runs). The broader complementarity evidence (12.1 pp XD late→gated) is robust; these two endpoints are not statistically separated. *Fix: soften, or report matched 3-seed visual-only std.*

---

## LOW (wording / rounding / undisclosed-but-defensible)

- **L1** Top-2 persons ranked by mean **pose-keypoint** confidence, not YOLOX "detection confidence" (`:124`; `extract_skeletons.py:517`).
- **L2** XD "none excluded" — one 34-frame video exists in the raw download but is commented out of all splits, so true as used (NEEDS_CONTEXT).
- **L3** SigLIP2 checkpoints: paper omits `-256` resolution + `webli` tag and writes "Giant" for `gopt` (`:141-143`). Dims correct.
- **L4** LR **warmup (5 ep) + cosine annealing** present in every config/run (`scheduler.py`) but undisclosed; lr=1e-4 is the peak, not constant.
- **L5** Temporal **bag length data.T=32** (snippets/video, feeds top-k and 1/T sparsity) undisclosed numerically; interacts with ~41% UCF videos having <3 real snippets.
- **L6** Table 2 Late-Fusion Best Δ printed +1.5 (raw, correct) vs +1.6 (from displayed cells). Cosmetic double-rounding; only this row.
- **L7** "fewer than 4,000 parameters" is true but loose — exact adapted count is **1,536** (recorded `n_adapted_params=1536`).
- **L8** disc_reweight canonical path uses a **mixed** clean reference (clean-test for VL std + skel floor, clean-train for skel-z baseline), vs the prose's either/or "training or clean-test"; "equivalent results" claim itself is supported.
- **L9** CLIP complementarity cites 81.4 (3-seed mean) vs visual-only 81.1 (seed-42) — minor basis mix; the paper's table correctly shows 81.4±0.3 (NEEDS_CONTEXT; direction holds).

---

## Recommended fix priority

1. **H1** commit the TTA artifacts + a tracked regenerator (reproducibility).
2. **H2** one-token edit ×3: "≤0.004 pp" → "<0.1 pp".
3. **H3** fix the gating figure/caption — highest *reader-credibility* risk (a claim with a figure that can't show it).
4. **M3, M4, M1** methods-section accuracy (frames/snippet, n=254, normalization).
5. **M5, M6** TTA reporting transparency.
6. LOW items: batch into one "Implementation Details" cleanup pass (warmup, T=32, exact checkpoints, param count 1,536).

*All findings carry file:line evidence in the audit transcript; none required re-running experiments.*
