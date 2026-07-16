---
phase: quick-260717-77p
verified: 2026-07-17T00:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Quick 260717-77p: Codex Round-2 Batch Verification Report

**Task Goal:** (T1) 13 wording/presentation fixes, (T2) paired video-level bootstrap + honest ch05 paragraph + PROVENANCE row, (T3) three GPU-job setup scripts with no launches.
**Verified:** 2026-07-17 (main tree, after merge 40a2dfa; thesis/main.pdf rebuilt 06:37:26, 41 s after the merge commit — fresh)
**Status:** PASSED

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Zero "apples-to-apples"; fair-subset table "regime-matched" + protocol note | VERIFIED | tr-flattened grep over thesis/chapters + frontmatter + paper/sota_comparison_full.tex = 0; PDF text = 0. ch07:314-326 caption "Fair-subset (regime-matched)" with protocol note (254/290 cohort, 64×64/~3 FPS, "comparability is scoped to the training regime, not the evaluation protocol") |
| 2 | ch04 footnote: legacy/corrected mixture, −0.13pp A/B, no std-bound claim | VERIFIED | ch04:254-270: batch-axis formula description, e5ab412/f89910b + tests/test_smoothness_axis.py, "All seed-42 UCF-Crime runs and all three seeds of the Gated Fusion rows (including the 82.5±0.4 headline)" legacy, s123/s2024 corrected at identical λ2=8e-4, "standard deviations should not be read as pure seed variance", −0.13pp A/B, "reported as run". Flatten-grep for std-bound phrasing: absent |
| 3 | TTA claims argued/scoped + single-LR 1e-3 disclosure in ch06 | VERIFIED | ch06:175 "we argue it is not a tuning artifact"; ch06:180-185 "only at their reference learning rate of 1×10⁻³, with no learning-rate sweep; the categorical reading therefore rests on the rank-invariance mechanism"; ch06:186-189 structural limit scoped to "the evaluated continual protocol and this 1,536-parameter LayerNorm surface... what we argue is"; ch06:428 "full-stream continual adaptation leaves the metric unchanged (<0.1 points)" (no "unlimited" left); ch09:46-55 RQ3 "we argue is structural, within the evaluated continual protocol and this 1,536-parameter adaptation surface"; ch01 pre-existing "We argue" hedge intact. Null result still clearly claimed ("No.", "<0.1 points on every backbone") |
| 4 | ch06 FOURTH honest caveat + ch07 sec:lim-tta mirror | VERIFIED | ch06:374-397 "Four limitations bound the result" — fourth = strategy search scored on reported test conditions, with LOCO/CORAL + unseen-axes mitigations; ch07 sec:lim-tta "Three scope caps" — third cap mirrors it |
| 5 | ch05 paired-bootstrap paragraph numbers verbatim from CSV | VERIFIED | Every claim cross-checked against results/paired_bootstrap/paired_bootstrap.csv (see detailed audit below) |
| 6 | Three GPU-job deliverables validate WITHOUT GPU | VERIFIED | pytest tests/test_run_ablations.py 17 passed (re-run this session); --dry-run emits exactly 24 `[dry-run] would run *learned` lines; run_ucf_consistency_rerun.py --list-only exits 0 with exactly 29 cells incl. ucf_gated_fusion_giant_s123/s2024; measure_keypoint_drift.py --list-only enumerates 53 videos × 4 conditions = 212 measurements, "exiting without inference" |
| 7 | Clean rebuild gates | VERIFIED | main.pdf 97pp (93-97 gate); 0 "Overfull \vbox" in fresh main.log; only "undefined" match is the allowed C70/bkai font-shape warning; headlines 82.5/78.7 present; metadata title/author/keywords non-empty ("Dual-Modal Skeleton-Visual Fusion...", "Wei-Han Jeng"); "ao Carreira" absent / "Carreira" present; references.bib:149 `Jo{\~a}o` |
| 8 | No experiment number changed except NEW bootstrap numbers | VERIFIED | Numeric-line audit of git diff d44a5b4~1..d44a5b4 (thesis sources): all numeric edits confined to the specified footnote/captions/sentences; ±std bands added (78.7±0.9, 76.8±2.8) reuse existing Table 5.2 values; ablation tables untouched |
| 9 | No canonical results/<run>/ created or modified; paired_bootstrap only new results/ path | VERIFIED | `find results -maxdepth 1 -newermt 2026-07-16 -type d` returns only results/paired_bootstrap; results/_consistency_rerun absent; next-newest run-dir mtime 2026-07-05 |

**Score:** 9/9 truths verified

### HIGHEST-PRIORITY audit: ch05 paragraph vs paired_bootstrap.csv

Every number/claim in ch05:369-386 checked against the CSV (24 rows = 8 configs × 3 seeds, confirmed):

| ch05 claim | CSV evidence | Match |
|---|---|---|
| "all twelve 95% intervals straddle zero" (UCF) | all 12 UCF rows have p2.5 < 0 < p97.5 | YES |
| "P(Δ>0) from 0.34 to 0.85" (UCF) | min 0.3405 (siglip2 s2024), max 0.848 (siglip2 s42) | YES (correct rounding) |
| "CLIP on all three seeds (P(Δ>0)=1.0; per-seed gains +1.4 to +2.7 AP points)" | xd_clip P=1.0/1.0/1.0; deltas 0.017004/0.014232/0.026676 → +1.7/+1.4/+2.7 pts | YES |
| "SO400M on two of three" (CIs exclude zero) | xd_so400m s42 [0.0148,0.0363], s2024 [0.0238,0.0529] exclude 0; s123 straddles | YES |
| "SigLIP2 Base and Giant... one significantly negative seed-42 interval (−1.3 and −2.1 points)" | xd_siglip2 s42 mean −0.012707 CI [−0.0238,−0.0015]; xd_giant s42 mean −0.020863 CI [−0.0321,−0.0098] | YES |
| "one significantly positive seed-2024 interval" (each) | xd_siglip2 s2024 CI [0.0012,0.0208]; xd_giant s2024 CI [0.0026,0.0278] | YES |
| "the two ties in Table tab:xd-ablation" | Table 5.2: XD Base gated 74.5 vs visual 74.5; XD Giant gated 76.8 vs visual 76.8 | YES |

**Tension check vs existing thesis claims — NO contradiction found:**
- ch05:93-97 / ch05:245-257 (complementarity): "meets or exceeds in all eight... strictly positive in six of eight, the other two tied at the displayed precision" — the bootstrap paragraph identifies exactly those two ties (XD Base/Giant) as the sign-flippers and frames per-seed significance as not implying per-config robustness. The mean-level 8/8 claim is a ties-inclusive "meet-or-exceed"; the sign test drops ties, so seed-level flips on the ties do not touch it.
- ch09 RQ1 (lines 20-31): mean-level phrasing ("strictly positive in six, with two ties, tie-dropping sign test p≈0.03") — consistent.
- The paragraph's closing frame ("sharpens rather than overturns... the defensible evidence for complementarity remains the cross-configuration consistency") matches the thesis's pre-existing position (ch05:98-102 "individually within seed variance... consistency indicates") rather than undermining it, while honestly reporting UCF per-config nonsignificance and the XD seed-level sign flips.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| scripts/paired_bootstrap_fusion.py | Paired video-level bootstrap B=2000 | VERIFIED | Imports frame_labels/xd_frame_labels (src/eval), SANITY_TOL=1e-3 mandatory gate vs eval_metrics.json, default_rng(0), NaN-safe weighted AP (np.divide where=tot>0) |
| results/paired_bootstrap/paired_bootstrap.csv | 24 rows per (dataset,backbone,seed) | VERIFIED | Exactly 24 data rows, all fields present, 0 redraws; git-tracked (with summary.json) |
| scripts/measure_keypoint_drift.py | D3 prep, list-only without inference | VERIFIED | Visible-terminal header, vcc-skeleton env + runtime est., OKS formula documented (κ=0.1), PASS criterion stated (OKS≥0.85 AND drop≤0.10), resumable; --list-only ran clean in vcc-main (deferred rtmlib import) |
| scripts/run_ucf_consistency_rerun.py | Job C rerun, legacy enumeration | VERIFIED | git merge-base ancestry test, 29 cells, path-prefix containment to results/_consistency_rerun/ (T-77p-01), scoped clean-worktree guard, resumable, --results-root default None |
| scripts/compare_consistency_rerun.py | Delta table + DECISION-GATE | VERIFIED | Header documents PASS/FAIL verdict semantics vs row 3-seed std; zero-GPU |
| configs/late_fusion_learned*.yaml (8) | alpha: learned clones | VERIFIED | All 8 exist, all `alpha: learned`; wired into QUEUES["learned_late_fusion"] (24 RunSpecs, test pin 334→358 + queue assert 24) |
| thesis/figures/fig_gate_by_category_{ucf,xd}.png | Regenerated print-legible | VERIFIED | Binary changed in d44a5b4; 830px/150dpi = 5.53in source at 2.83in render → 15-16pt fonts ≈ 7.7-8.2pt effective (≥7pt floor); executor logged identical gate ranges (data unchanged, CPU-only forward) |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| paired_bootstrap_fusion.py | src/evaluate.py GT logic | frame_labels/xd_frame_labels imports + n_frames-from-npz + 1e-3 sanity assert | WIRED |
| ch05_results_fusion.tex | results/paired_bootstrap/paired_bootstrap.csv | paragraph numbers verbatim (7/7 claims matched) + source comment + PROVENANCE row 25 | WIRED |
| scripts/run_ablations.py | configs/late_fusion_learned_xd_giant.yaml (+7) | QUEUES["learned_late_fusion"], dry-run resolves all 24 | WIRED |
| thesis/preamble.tex | frontmatter/titlepage.tex + abstract.tex | \hypersetup strings match titlepage title/author and abstract keywords; PDF metadata populated | WIRED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Ablation queue test suite | pytest tests/test_run_ablations.py -x | 17 passed | PASS |
| Learned-queue dry run | run_ablations.py --queue learned_late_fusion --dry-run \| grep -c '\[dry-run\] would run .*learned' | 24 | PASS |
| Legacy-cell enumeration | run_ucf_consistency_rerun.py --list-only | 29 cells incl. ucf_gated_fusion_giant_s123/s2024, "exiting without training" | PASS |
| Drift-sample enumeration | measure_keypoint_drift.py --list-only | 53 × 4 = 212, "exiting without inference" | PASS |
| PDF gate battery | fitz: pages/metadata/headlines/Carreira/apples | 97pp, all non-empty, all gates pass | PASS |
| Fragment standalone compile | latexmk (scratchpad output dir) | exit 0 | PASS |

### Anti-Patterns Found

None. No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER in any created/modified script or test. The three unlaunched GPU scripts are deliverables by spec, not stubs.

### Deviation Assessment (5 recorded — all sound)

1. **NaN safe-divide in weighted AP** — verified at paired_bootstrap_fusion.py:125 (`np.divide(..., out=zeros, where=tot>0)`); mathematically exact: zero-multiplicity tie groups have zero recall increment so their precision value is never weighted in. Sound.
2. **Page-count fix (96→99→97) via tab:sota-fair short caption + tightened own prose + fig canvas** — `\caption[Fair-subset (regime-matched) comparison]{...}` short form present (LoT de-duplication is standard practice); protocol-note content fully retained in the long caption; disclosure content of ch06/ch07 additions verified present post-tightening; 97pp inside the 95±2 gate. Sound.
3. **CUDA_VISIBLE_DEVICES=-1 instead of ""** — `-1` is the canonical way to hide CUDA devices; executor additionally asserted `not torch.cuda.is_available()`. Sound; no GPU launch evidence (results/ mtimes clean).
4. **--results-root flag on Job C scripts** — verified optional with default None mirroring run_ablations.py; user-facing default behavior unchanged. Sound.
5. **Per-task commits (3) + dual-location bootstrap outputs** — all three commits on main via merge 40a2dfa; results/paired_bootstrap/{csv,json} git-tracked in the main repo (PROVENANCE requires tracked sources) and present on disk. Sound.

### Minor Notes (info-level, non-blocking)

- thesis/PROVENANCE.md row 25 lists xd_clip "per-seed gains +1.4/+1.7/+2.7" — the value set is correct but seed order (42/123/2024) is +1.7/+1.4/+2.7. The ch05 text itself uses a range ("+1.4 to +2.7") and is unaffected. Cosmetic ordering in a provenance note only.
- Page count 97 sits at the top edge of the 93-97 gate; future additions will need offsetting cuts.

### Gaps Summary

None. All 9 must-have truths verified against the main tree; the highest-priority ch05 bootstrap paragraph is numerically verbatim from the CSV and reconciles per-seed sign flips with the mean-level 8/8 claim without contradiction.

---

_Verified: 2026-07-17_
_Verifier: Claude (gsd-verifier)_
