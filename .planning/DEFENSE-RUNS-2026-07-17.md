# Defense-preparation runs — final readout (2026-07-17)

Three GPU jobs run post-submission (thesis frozen until after the oral). All artifacts
committed; canonical results untouched. Jobs C and B ran in a clean git worktree pinned
to d2e4c2b (`scoped_dirty: false` recorded per rerun — the provenance the original runs
lacked).

## Verdicts at a glance

| Job | Question it answers | Verdict | Thesis impact |
|---|---|---|---|
| C — consistency rerun (29 cells) | Do the legacy-code UCF numbers survive clean version-locked retraining? | **FAVORABLE.** Headline 82.54→82.48 (both = 82.5); all 3 headline seeds within seed std; every qualitative conclusion survives; gated≥visual becomes strictly positive on all 4 UCF backbones | Footnote upgrade in revision; optional number adoption (gate tripped on 16/29 non-headline cells) |
| B — learned-scalar late fusion (24 runs) | Is a learned static weight enough, or is input-dependent gating needed? | **FAVORABLE.** Learned α gets stuck at 0.44–0.48 (≈equal weight); performance ≈ equal-weight late fusion; 10–13 pp below gated on XD | Strengthens the gating claim; one sentence + row in revision; kills committee Q5 |
| A′ — keypoint drift, fresh baseline (53 videos × 4 conditions) | Is the clean-cache reuse for gaussian/brightness scientifically innocuous? | **UNFAVORABLE.** Gaussian: px_dev 27.7–30.5 (on 64×64 frames!), OKS 0.014–0.025, conf −0.12..−0.14; 0/53 videos keep OKS>0.5 even at severity 3. Brightness: px_dev 13.9, OKS 0.24, 3/53 above 0.5 | ch04's robustness justification is refuted; Chapter 6 gaussian gains do NOT transfer to same-camera deployments; claim-scope revision required (details below) |

Also on record: the original vs-cache Job A run is SUPERSEDED (a 6-video clean-control
found a pathway mismatch between today's extraction and the April cache: clean-vs-cache
px_dev 11.1 / OKS 0.29). A′'s clean_ref rows document this per video.

## What A′ means for Chapter 6 (the honest read)

1. The experiment as run is still exactly what the thesis says it is: the corrupted-input
   gains were measured with a clean skeleton cache for gaussian/brightness, disclosed in a
   dedicated ch04 subsection, and already framed as "rescue, not robustness" (ch06).
   Nothing reported becomes false.
2. What IS refuted is ch04's justification for the cache reuse ("RTMPose produces
   effectively identical keypoints... empirical robustness of top-down pose estimation").
   A′ measures the opposite: on 64×64 inputs, gaussian noise at the studied severities
   destroys the pose stream. The reuse was a cost decision whose innocuousness was
   assumed; the assumption is now measured false.
3. Consequence for claim scope: in a deployment where the SAME camera feed is corrupted,
   the skeleton stream would degrade too, and the thesis's own JPEG rows (where skeletons
   WERE re-extracted) show what happens then: gains = 0 by gate construction. The gaussian
   +13.2/+8.95/etc. rows therefore quantify the mechanism's ceiling when an intact
   alternative stream exists (e.g., pose from a separate uncorrupted source, or corruption
   introduced downstream of pose extraction) — not same-camera robustness.
4. The thesis's aggregate claims survive in narrowed form: routing toward a MORE reliable
   stream works and is label-free (+1.21 mean includes the honest zeros); the "which
   stream is reliable" question must be answered per deployment.

## Decision required (Austin) — two paths for the bound-copy revision

- **Path 1 (recommended if 1–2 GPU-days are available before the oral): escalation run.**
  Re-extract the gaussian/brightness skeleton caches from corrupted frames (the
  infrastructure exists — scripts/batch_extract_corrupted.py did exactly this for
  blur/JPEG), then re-run disc_reweight on those 20-of-20 honest conditions. Expected
  outcome per the JPEG precedent: gaussian gains collapse toward 0 → Table 6.2 gains a
  row and the thesis presents BOTH regimes (intact-stream ceiling vs same-camera
  reality). Strongest possible defense position: no committee question left unanswered.
- **Path 2 (zero GPU): claim-scope revision only.** Remove the refuted justification
  sentence, add the A′ measurement (one sentence + small table), reframe the gaussian
  rows as intact-stream mechanism ceiling. Defensible, but leaves "so what happens if
  you re-extract?" answered by extrapolation (JPEG precedent) rather than measurement.

## Revision checklist for the bound copy (post-defense)

1. ch04 re-extraction policy: replace the "effectively identical keypoints" justification
   with the A′ measurement (px_dev/OKS/conf numbers, 53-video stratified sample); cite
   results/keypoint_drift/keypoint_drift_fresh.csv.
2. ch06: add the same-camera vs intact-stream scope distinction where the gaussian gains
   are interpreted (§ tab:tta_breakdown prose + honest caveats item 1 extension).
   Abstract/ch01: reword "corruption-robust skeleton stream" → "intact skeleton stream".
3. ch09 future-work "skeleton-head ensemble routing": add the same caveat (its +1–2pp
   estimate presumes the intact cache).
4. Consistency-rerun adoption (if adopted): propagate corrected Table 5.1 numbers
   (results/_consistency_rerun/corrected_table_analysis.md has the full old→new map);
   update the GF 2-Person sentence "half of the cells" → "five of the eight"; update the
   ch04 mixed-provenance footnote to cite the 29-cell clean rerun (headline reproduced,
   82.5 unchanged) instead of only the single-config A/B.
5. Add Job B one-liner to ch05 (learned-scalar late fusion ≈ equal-weight, α≈0.45–0.48,
   still 10+ pp below gated) — directly supports the gating mechanism claim.
6. If Path 1 taken: new Table 6.2 row + rewritten gaussian interpretation from measured
   corrupted-skeleton results.

## Defense Q&A brief (the 9 predicted committee questions)

1. **Why were 36 UCF test videos excluded?** They are shorter than one 64-frame snippet —
   the architecture's minimum unit. Disclosed prominently in §4 with the cohort framing;
   the manifest (data/ucf_total_frames.json) makes the evaluation reproducible from git.
2. **Why compare 64×64 / 3 FPS inputs with full-resolution methods?** Disclosed in §4 (and
   the comparison table's protocol note): the input-fidelity handicap runs AGAINST us, so
   within-regime competitiveness is a conservative claim. We do not claim SOTA anywhere.
3. **Which results used the wrong smoothness axis?** Precisely disclosed (§4 footnote):
   all seed-42 runs + all Gated Fusion seeds. NEW: a 29-cell version-locked clean rerun
   reproduces the headline at 82.5 (Δ −0.06 pp) and preserves every conclusion; corrected
   numbers will be adopted in the final revision.
4. **Does skeleton information help, or is it added capacity?** The gated head has FEWER
   trainable parameters than the late-fusion head (498K vs 633K, §4). New: a learned
   static mixing weight (same capacity class) stays at chance mixing and 10–13 pp below
   gated — the gain is not capacity. Complementarity: 8/8 meet-or-exceed at means, sign
   test p≈0.03; per-config paired bootstrap honestly reported as individually
   nonsignificant on UCF.
5. **Why no learned-weight late fusion?** It is now evaluated (24 runs, 3 seeds): α
   converges to 0.44–0.48, performance ≈ equal-weight, far below gated. A static weight
   cannot fix late fusion; input dependence is the operative ingredient.
6. **Would the Gaussian gain survive pose from corrupted frames?** We measured it
   (53-video stratified sample): it would not — gaussian noise at the studied severities
   destroys RTMPose keypoints on these inputs (OKS ≤0.025; 0/53 videos above 0.5). The
   reported gains quantify routing toward an INTACT stream (as disclosed: "rescue, not
   robustness"); our own JPEG rows — where skeletons WERE re-extracted — show the
   same-camera outcome (zero gain, honestly reported). [If Path 1 taken: cite the
   measured corrupted-skeleton rerun instead of the JPEG extrapolation.]
7. **How was the TTA method selected without using test performance?** Disclosed (§6
   honest caveat #4): the strategy search scored on the reported test conditions —
   residual selection risk acknowledged; mitigations: every candidate label-free and
   tuning-free, a held-out leave-one-condition-out check eliminated CORAL, and the
   winner reproduced on backbones/severities/seeds unseen during screening.
8. **Why do the gates look nearly constant on UCF-Crime?** Gate variation is
   category-structured and small on UCF (boxes ~0.44–0.48) but decisive on XD, where
   fixed weighting loses >10 AP points. The gate's value is not large swings — it is
   input-dependent suppression of the weak stream where needed.
9. **What is the operational value given the fixed-threshold calibration failure?**
   Disclosed as the binding deployment limitation (§7.7.2): rank metrics reward ordering
   only. Deployment requires post-hoc calibration (temperature scaling / isotonic on
   held-out normals) or threshold-free alarms (windowed ranking) — neither needs
   backbone retraining. The contribution is the comparison under standard protocols.

## Artifacts

- results/_consistency_rerun/{comparison.csv, comparison.md, corrected_table_analysis.md} (committed)
- results/keypoint_drift/keypoint_drift.csv (vs-cache, superseded) + keypoint_drift_fresh.csv (quotable) (committed)
- results/results-index.csv +24 learned rows (committed); learned run dirs on disk under results/*_learned_s*/
- Clean worktree D:/ViolenceCC_rerun_wt (pinned d2e4c2b) — can be removed after the revision pass
