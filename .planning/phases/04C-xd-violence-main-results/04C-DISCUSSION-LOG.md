# Phase 4c: XD-Violence Main Results - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-26
**Phase:** 4c-xd-violence-main-results
**Areas discussed:** XD config strategy, Execution ordering, Per-category scope, Hyperparameter transfer, Missing video handling, AP target contingency

---

## XD Config Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| 6 new flat XD YAMLs | Create skeleton_only_xd.yaml, clip_only_xd.yaml, late_fusion_xd.yaml, gated_fusion_xd.yaml, gated_fusion_xd_2person.yaml, gated_fusion_xd_clip_mean.yaml. Matches D-35 flat convention. ~80% duplication but self-contained. | ✓ |
| Scripted generation from UCF templates | Script reads UCF configs and generates XD variants by swapping dataset+paths. Fewer files to maintain manually. | |
| Runtime --dataset override | Keep only UCF configs. run_ablations.py passes --dataset xd to swap paths at runtime. Breaks flat-YAML-is-source-of-truth. | |

**User's choice:** 6 new flat XD YAMLs
**Notes:** Consistent with Phase 1 D-03 and Phase 4 D-35 conventions. 14 total configs after Phase 4c.

---

## Execution Ordering

| Option | Description | Selected |
|--------|-------------|----------|
| Main first, pooling after | Wave 1: main+seeds on existing features (~2-3h). Wave 2: user re-extraction. Wave 3: pooling ablations. Gets Gated Fusion AP ASAP. | ✓ |
| Re-extract first, then all at once | User runs both re-extractions before any training. All 3 queues run in one shot. Delays results by re-extraction time. | |
| You decide | Claude picks ordering during planning. | |

**User's choice:** Main first, pooling after
**Notes:** 3-wave structure gets thesis-critical Gated Fusion AP number earliest.

---

## Per-Category Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All 6 categories | Compute AP/AUC for all 6 XD anomaly types. Thesis highlights Fighting/Abuse/Riot. Zero extra compute. | ✓ |
| Violence-specific 3 only | Only Fighting/Abuse/Riot. Matches SC #4 literally. Would need re-running for other categories. | |
| You decide | Claude picks based on thesis argument. | |

**User's choice:** All 6 categories
**Notes:** Full table available for reviewer questions. Thesis narrative focuses on violence-specific subset.

---

## Hyperparameter Transfer

| Option | Description | Selected |
|--------|-------------|----------|
| Identical hyperparams | Same lr=1e-4, epochs=50, batch_size=16, patience=10. Early stopping handles convergence. Most defensible thesis narrative. | ✓ |
| Reduce epochs, keep rest | Lower epochs to 30. Faster wall-clock but introduces per-dataset difference. | |
| You decide | Start identical, adjust if convergence looks wrong. | |

**User's choice:** Identical hyperparams
**Notes:** "Same hyperparameters across datasets, no per-dataset tuning" — strongest thesis position.

---

## Missing Video Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Clean split files | Remove 2 video IDs from split files. Document exclusions in comments. 4752/4752 = 100%. | ✓ |
| Loader skip with warning | Add FileNotFoundError catch in loader. Split files unchanged but 2 silently skipped. | |
| You decide | Claude picks cleanest approach. | |

**User's choice:** Clean split files
**Notes:** 2 excluded: v=8cTqh9tMz_I__#1_label_A (corrupt moov), v=Gm73TwtUyGY__#1_label_G-0-0 (34 frames).

---

## AP Target Contingency

| Option | Description | Selected |
|--------|-------------|----------|
| Accept + document if >= 70% | AP >= 80% PASS. 70-79% MISS-ACCEPTED + thesis limitation. < 70% investigate. | ✓ |
| Hyperparameter sweep if miss | Try lr/batch_size/epochs variations. 12+ extra runs. Weakens thesis narrative. | |
| Hard pass at 80% | AP < 80% = phase failure. Escalate to debugging. Could block thesis timeline. | |

**User's choice:** Accept + document if >= 70%
**Notes:** Mirrors Phase 4b RTFM gate MISS-ACCEPTED pattern. Ablation table remains valuable regardless of absolute AP.

---

## Claude's Discretion

- XD annotation path routing (YAML field vs dataset-key inference)
- wandb posture (continue disabled)
- Queue naming convention
- skel_agg inheritance for XD 2person config

## Deferred Ideas

- Multi-person max/mean aggregation ablations
- XD-specific hyperparameter tuning (only if D-06 < 70% investigation)
- Cross-dataset transfer experiments
