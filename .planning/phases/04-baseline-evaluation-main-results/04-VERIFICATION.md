---
phase: 04-baseline-evaluation-main-results
verified: 2026-04-15T00:00:00Z
status: passed
score: 5/5
overrides_applied: 2
re_verification: false
overrides:
  - must_have: "RTFM on XD-Violence I3D RGB features reports frame-level AP within plus/minus 1% of 77.81% (SC #1)"
    reason: "EVAL-01 RTFM XD-I3D gate deferred to Phase 4b per 2026-04-15 Option B decision. Rule 4 architectural gap: xd_i3d training dispatch was not wired in Plan 04-03 (src/train.py + build_dataloaders have no xd_i3d branch). Phase 4b owns build_dataloaders_i3d + train_one_epoch_i3d + Wu et al. annotation parser before re-running the gate. Documented in 04-06-UAT.md DECISION block."
    accepted_by: "austinjeng"
    accepted_at: "2026-04-15T00:00:00Z"
  - must_have: "Gated Fusion achieves frame-level AUC >= 83% on UCF-Crime official test set (SC #2)"
    reason: "Documented miss at 0.8227 (0.73 pp below 0.83 target). 3-seed mean 0.81982 confirms the shortfall is architectural, not seed variance. Researcher accepted via plan 04-06 Checkpoint 2 resume signal 'gated fusion below target'. Remediation paths: Phase 5 TTA + threshold calibration, Phase 4b architectural sweeps. The 82.27% result is usable thesis material with documented context."
    accepted_by: "austinjeng"
    accepted_at: "2026-04-16T00:00:00Z"
deferred:
  - truth: "RTFM XD-I3D gate (SC #1) — RTFM on XD-Violence I3D RGB features reports frame-level AP within plus/minus 1% of 77.81%"
    addressed_in: "Phase 4b"
    evidence: "Phase 4b Success Criteria #1: 'RTFM on XD-Violence I3D RGB features reports frame-level AP within +/-1% of 77.81%, confirming the xd_i3d training dispatch and evaluation harness are correct.' Phase 4b also explicitly lists the required integration work: build_dataloaders_i3d, train_one_epoch_i3d, Wu et al. annotation parser."
---

# Phase 4: Baseline Evaluation & Main Results — Verification Report

**Phase Goal:** UCF-Crime evaluation harness built and the UCF ablation table with statistical stability measures is ready for the thesis. XD-Violence main results moved to Phase 4b per D-01. The RTFM XD-I3D gate was ALSO rescoped to Phase 4b (2026-04-15 Option B) because Plan 04-03 did not wire the claimed xd_i3d training dispatch (D-36).
**Verified:** 2026-04-15T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | RTFM on XD-Violence I3D RGB features reports frame-level AP within plus/minus 1% of 77.81% | PASSED (override) | Override: Rule 4 architectural gap — xd_i3d training dispatch not wired in Plan 04-03; deferred to Phase 4b per 2026-04-15 Option B decision. Accepted by austinjeng on 2026-04-15. Tracked in ROADMAP Phase 4b SC #1 and REQUIREMENTS.md traceability. |
| 2 | Gated Fusion achieves frame-level AUC >= 83% on UCF-Crime official test set | PASSED (override) | Override: documented miss at 0.8227 (0.73 pp below target). 3-seed mean 0.81982, std 0.00291. Researcher accepted per plan 04-06 Checkpoint 2 resume signal. Actual value in results/ucf_gated_fusion_s42/eval_metrics.json confirmed. |
| 3 | An ablation table exists with results for all 6 model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) + 2 pooling ablations on UCF | VERIFIED | results/results-index.csv has 8 data rows: ucf_skeleton_only_s42, ucf_clip_only_s42, ucf_late_fusion_s42, ucf_gated_fusion_s42, ucf_gated_fusion_clip_mean_s42, ucf_gated_fusion_2person_s42, ucf_gated_fusion_s123, ucf_gated_fusion_s2024. 12 columns confirmed. |
| 4 | Gated Fusion AUC on UCF reported as mean +/- std over 3 seeds ({42,123,2024}), std < 0.5% | VERIFIED | Seeds {42, 123, 2024} AUCs: 0.8227, 0.8168, 0.8200. Sample std (ddof=1) = 0.00291 = 0.29% < 0.5% gate. Confirmed from actual eval_metrics.json files. |
| 5 | Per-category breakdown (UCF-Crime: Fighting+Assault) shows higher AUC than full test set | VERIFIED | From eval_metrics.json per_category: Full-test AUC 0.8227. Fighting AUC 0.9550 (+13.23 pp). Assault AUC 0.9846 (+16.19 pp). Both violence categories exceed full-test AUC. |

**Score:** 5/5 truths verified (2 via accepted override, 3 via empirical evidence)
**Overrides applied:** 2

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | RTFM XD-I3D AP >= 76.81% (SC #1) | Phase 4b | Phase 4b SC #1: "RTFM on XD-Violence I3D RGB features reports frame-level AP within +/-1% of 77.81%". Phase 4b also inherits the xd_i3d training dispatch implementation work (build_dataloaders_i3d, train_one_epoch_i3d, Wu et al. annotation parser). |

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/eval/snippet_to_frame.py` | snippet_to_frame() pure function with C4 tolerance assertion | VERIFIED | Contains `def snippet_to_frame(`, `upsample_factor`, `AssertionError`. Imports clean. |
| `src/eval/ucf_annotations.py` | parse_annotations + frame_labels + VideoAnnotation | VERIFIED | All three symbols confirmed present and importable. |
| `data/annotations/ucf_temporal.txt` | Sultani 2018 annotation file, 290 lines | VERIFIED | 290 lines, Abuse028_x264.mp4 present, each line 6 columns. |
| `tests/test_snippet_to_frame.py` | C4 regression tests | VERIFIED | `def test_compound_repeat` present; file substantive. |
| `tests/test_ucf_annotations.py` | Annotation parser unit tests | VERIFIED | Abuse028, Arson011, Normal_Videos references present. |
| `tests/fixtures/synthetic_eval.py` | make_synthetic_ucf + make_synthetic_i3d factories | VERIFIED | Both factory functions confirmed present. |
| `src/eval/test_loader.py` | UCFTestDataset + sys.argv guard | VERIFIED | `def _assert_called_from_evaluate_or_pytest` present. |
| `src/eval/metrics.py` | compute_frame_metrics with C4 assertions | VERIFIED | roc_auc_score and AssertionError C4 guards confirmed. |
| `src/evaluate.py` | CLI entry point with --run-dir + --split flags | VERIFIED | `if __name__ == "__main__"` and `json.dump` present; all 14 required eval_metrics.json keys present in output. |
| `src/utils/config.py` | config_hash, checkpoint_sha, git_sha helpers | VERIFIED | `def config_hash` confirmed present. |
| `src/models/rtfm_i3d.py` | RTFMI3D module | VERIFIED | `class RTFMI3D` present. |
| `src/models/registry.py` | rtfm_i3d registry entry | VERIFIED | `from src.models.rtfm_i3d import RTFMI3D` in registry. |
| `src/data/i3d_dataset.py` | I3DFeatureDataset with 5-crop dispatch | VERIFIED | `class I3DFeatureDataset` present. |
| `configs/rtfm_i3d.yaml` | xd_i3d training config | VERIFIED | `dataset: xd_i3d` confirmed. Note: xd_i3d training dispatch deferred to Phase 4b. |
| `scripts/extract_ctrgcn.py` | --keep-persons flag | VERIFIED | `--keep-persons` confirmed present. |
| `scripts/extract_clip.py` | --pool flag | VERIFIED | `--pool` confirmed present. |
| `src/data/dataset.py` | skel_agg parameter + 3D reshape | VERIFIED | `skel_agg` confirmed present. |
| `configs/gated_fusion_2person.yaml` | 2-person concat ablation config | VERIFIED | `skel_agg: concat` confirmed. |
| `configs/gated_fusion_clip_mean.yaml` | CLIP mean-only pooling config | VERIFIED | `clip_mean` confirmed. |
| `scripts/verify_pooling_caches.py` | sanity verifier for pooling caches | VERIFIED | `verify` and `allclose` patterns present. |
| `scripts/wandb_preflight.py` | fail-fast wandb credential check | VERIFIED | `WANDB_API_KEY` confirmed present. |
| `scripts/run_ablations.py` | subprocess orchestrator with QUEUES + .done probe | VERIFIED | `QUEUES`, `is_done`, `src/train.py`, `src/evaluate.py`, `results_index_append`, `.done` all confirmed. |
| `src/utils/csv_logger.py` | results_index_append helper | VERIFIED | `def results_index_append` confirmed. |
| `src/utils/wandb_logger.py` | wandb offline fallback | VERIFIED | `wandb.errors.Error` confirmed. |
| `src/train.py` | --run-name CLI arg | VERIFIED | `--run-name` confirmed. |
| `results/results-index.csv` | 8 data rows, 12 columns | VERIFIED | Confirmed: 8 rows (4 main + 2 pooling + 2 seed-variation), 12 columns (run_name, variant, dataset, seed, cache_variant, auc, ap, n_videos, n_frames, start_time, end_time, config_hash). |
| `results/ucf_gated_fusion_s42/best_model.pth` | Phase 5 TTA handoff checkpoint | VERIFIED | File confirmed present. |
| `results/ucf_gated_fusion_s42/per_category.csv` | Per-category breakdown | VERIFIED | Contains Fighting, Assault columns confirmed. |
| `.planning/ROADMAP.md` | Phase 4b entry with inherited SCs | VERIFIED | `### Phase 4b: XD-Violence Main Results + RTFM XD-I3D Gate` present; 7 `### Phase` blocks (Phases 1-4b-5-6); ordering Phase4 < Phase4b < Phase5 confirmed; `E:/features/xd` activation criterion present; 7/7 complete and `Blocked on XD features` status both confirmed. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| tests/conftest.py | tests/fixtures/synthetic_eval.py | pytest fixture imports | VERIFIED | `from tests.fixtures.synthetic_eval import` pattern confirmed in conftest. |
| tests/test_snippet_to_frame.py | src.eval.snippet_to_frame | import | VERIFIED | Module importable; test file imports from src.eval. |
| src/eval/ucf_annotations.py | data/annotations/ucf_temporal.txt | parse_annotations(path) | VERIFIED | parse_annotations function present; annotation file at expected path (290 lines). |
| src/evaluate.py | src.eval.test_loader | import build_test_dataset | VERIFIED | `from src.eval.test_loader import` confirmed in evaluate.py. |
| src/evaluate.py | results/<run>/eval_metrics.json | json.dump with reproducibility metadata | VERIFIED | json.dump confirmed; all 14 required keys present in actual output. |
| src/evaluate.py | results/<run>/.done | mark_done atomic write | VERIFIED | `_mark_done` with os.replace pattern confirmed; all 8 run dirs have .done markers. |
| src/models/registry.py | src/models/rtfm_i3d.py | lazy factory import | VERIFIED | `from src.models.rtfm_i3d import RTFMI3D` in registry.py. |
| src/eval/test_loader.py | src/data/i3d_dataset.py | build_test_dataset with dataset=='xd_i3d' | VERIFIED | I3DFeatureDataset import in test_loader.py confirmed. |
| scripts/run_ablations.py | src/train.py | subprocess.run | VERIFIED | `src/train.py` reference in run_ablations.py. |
| scripts/run_ablations.py | src/evaluate.py | subprocess.run | VERIFIED | `src/evaluate.py` reference in run_ablations.py. |
| scripts/run_ablations.py | results/results-index.csv | results_index_append | VERIFIED | `results_index_append` call confirmed; 8 rows in CSV. |
| scripts/run_ablations.py | results/<run>/.done | is_done filesystem probe (D-31) | VERIFIED | `is_done` function at line 124; `if is_done(run_dir): skip` logic at line 246. |
| src/data/loaders.py | src/data/dataset.py skel_agg | cfg.data.skel_agg forwarded to MILFeatureDataset | VERIFIED | Rule 1 bug fixed in Plan 04-06 Task 4: skel_agg threaded into both train_full and val_full constructors. |
| src/data/dataset.py | C3 import boundary | must NOT import from src.eval.* | VERIFIED | No src.eval imports found in dataset.py. |

---

### Data-Flow Trace (Level 4)

Results files render empirical data, not synthetic placeholders.

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| results/ucf_gated_fusion_s42/eval_metrics.json | auc, ap, per_category | src/evaluate.py computing roc_auc_score on actual model predictions from best_model.pth | Yes — model trained on 1254 UCF-Crime training videos; eval on 254 test videos, 1,010,560 frames | FLOWING |
| results/results-index.csv | 8 rows of run results | scripts/run_ablations.py calling results_index_append after each completed run | Yes — appended by actual subprocess completions; timestamps span 2026-04-16T02:43:45 to 03:07:42 | FLOWING |
| per_category.csv | per-category AUC values | src/evaluate.py from per_video_category and per_video_scores | Yes — Fighting 0.9550, Assault 0.9846 confirmed from actual eval_metrics.json per_category dict | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| src.eval modules importable (no sys.argv guard on eval utils) | python -c "from src.eval.snippet_to_frame import snippet_to_frame; from src.eval.ucf_annotations import parse_annotations, frame_labels, VideoAnnotation; print('OK')" | import OK | PASS |
| data/annotations/ucf_temporal.txt has 290 lines with Abuse028_x264.mp4 | wc -l + grep | 290 lines, 1 match | PASS |
| results-index.csv has 8 data rows with 12 columns | python csv.DictReader check | 8 rows, 12 columns | PASS |
| 3-seed AUC std from actual eval_metrics.json files | python numpy std(ddof=1) | 0.00291 < 0.005 | PASS |
| eval_metrics.json contains all 14 required keys | python key check | 0 missing keys | PASS |
| .done markers present for all 8 run dirs | filesystem check | 8/8 .done files found | PASS |
| best_model.pth present in gated_fusion_s42 for Phase 5 handoff | ls check | file present | PASS |
| C3 import boundary: dataset.py imports no src.eval.* | grep check | no violations found | PASS |
| skel_agg forwarded in loaders.py (Plan 04-06 Rule 1 fix) | grep | skel_agg at lines 101, 105, 112, 119 | PASS |
| C4 AssertionError guard in metrics.py | grep | AssertionError ("C4 REGRESSION") at lines 62, 69 | PASS |

---

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| EVAL-01 | 04-03, 04-07 | RTFM baseline reproduction on XD-Violence I3D (retargeted per D-03) | DEFERRED to Phase 4b | 2026-04-15 Option B decision; REQUIREMENTS.md traceability row maps to Phase 4b with full explanation. RTFMI3D model and I3DFeatureDataset exist (code artifacts); only training dispatch is missing. |
| EVAL-02 | 04-01, 04-02, 04-06, 04-07 | Frame-level AUC evaluation on UCF-Crime with correct snippet-to-frame expansion | SATISFIED (UCF) | UCF test AUC reported in eval_metrics.json (0.8227); snippet_to_frame C4 guards verified. XD-side scope correctly deferred to Phase 4b per D-01. |
| EVAL-03 | 04-02, 04-05, 04-06, 04-07 | Frame-level AP evaluation + ablation table | SATISFIED (UCF) | 8 UCF rows in results-index.csv with ap column. Full AP values confirmed in CSV and eval_metrics.json. REQUIREMENTS.md updated to reflect UCF complete, XD-side Phase 4b. |
| EVAL-04 | 04-02, 04-06, 04-07 | Per-category violence subset breakdown | SATISFIED (UCF) | per_category.csv confirmed; Fighting 0.9550 (+13.23 pp), Assault 0.9846 (+16.19 pp) both exceed full-test 0.8227. |
| EVAL-05 | 04-05, 04-06, 04-07 | 3-seed stability: mean +/- std, std < 0.5% | SATISFIED (UCF) | Seeds {42, 123, 2024} AUC std = 0.00291 = 0.29% < 0.5% gate. Confirmed from actual eval_metrics.json files. |

**Orphaned requirements:** None. All EVAL-01 through EVAL-05 are accounted for in plan frontmatter and traced correctly. Note: ROADMAP Requirement Coverage table still shows "EVAL-01 | Phase 4" which is a cosmetic inconsistency with REQUIREMENTS.md traceability (which correctly says Phase 4b) — this was intentionally left as-is per Plan 04-07 Task 1 Step C instructions ("Do NOT add Phase 4b rows" to the coverage table). Not a gap.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/evaluate.py | 191 | `cats_map[vid] = "Normal" if vid.endswith("_label_A") else "Abuse"` | Warning | WR-04 from code review: hardcoded "Abuse" category for unannotated XD I3D videos. No impact on UCF evaluation (which uses a separate branch). Will produce misleading per_category breakdowns if XD I3D path is invoked before Phase 4b wires real Wu et al. annotations. Scoped: acceptable risk for Phase 4 UCF-only scope. |
| scripts/extract_skeletons.py | 333 | Duplicate `get_wholebody_model()` call on fresh-start path | Info | WR-01 from code review: duplicate singleton call, benign but misleading. Not a Phase 4 evaluation harness concern. |
| scripts/extract_ctrgcn.py | 121-125 | Fragile `"backbone" in str(list(keys)[:1])` heuristic | Warning | WR-02 from code review: could silently select wrong state_dict branch. Not triggered in Phase 4 execution (CTR-GCN features were already extracted in Phase 2-3). |
| src/data/i3d_dataset.py | 136 | `np.random.default_rng(0)` fixed seed in `_resample_T` | Warning | WR-03 from code review: eliminates per-epoch augmentation diversity for short XD I3D videos. Only affects Phase 4b RTFM training runs; no impact on Phase 4 UCF evaluation. |

**Blockers:** None. All Phase 4 UCF evaluation paths are clean. WR-04 is scoped to the deferred XD I3D path.

---

### Human Verification Required

None. All Plan 06 HUMAN-UAT items were resolved before Phase 4 closure (2026-04-16 Checkpoint 3 resolution). The researcher confirmed:

1. EVAL-01 RTFM gate — DEFERRED per Option B (2026-04-15)
2. EVAL-02 Gated Fusion AUC miss — ACCEPTED via Checkpoint 2 resume signal (2026-04-16)
3. EVAL-03 UCF ablation table — PASS (8 rows, scope-aligned with D-01)
4. EVAL-05 3-seed stability — PASS (std 0.00291 < 0.005)
5. EVAL-04 per-category — PASS (Fighting 0.9550, Assault 0.9846)
6. Bit-identical rerun invariant — PASS (researcher verified 9 numeric keys identical across two evaluate.py runs)
7. wandb preflight fails-fast — PASS (all 3 Rule 3 fallbacks triggered by the actual fails-fast path)

All items resolved programmatically or via documented researcher decision. No new items require human testing.

---

### Gaps Summary

No actionable gaps. All phase deliverables are present and verified.

The two overrides encode known, documented, and accepted deviations:
- SC #1 (EVAL-01 RTFM XD-I3D gate) is structurally deferred to Phase 4b with full scope definition and activation criterion. The code artifacts (RTFMI3D, I3DFeatureDataset, rtfm_i3d.yaml) are present; only the training dispatch and annotation parser are missing — both explicitly owned by Phase 4b.
- SC #2 (Gated Fusion AUC >= 0.83 miss) is empirically documented at 0.8227 with 3-seed confirmation. The miss is architectural (fusion over a weak skeleton branch), not a measurement artifact. Phase 5 TTA and Phase 4b architectural sweeps are the documented next steps.

Phase 4's UCF evaluation harness is fully operational, the ablation table has 8 reproducible rows, statistical stability is confirmed, and the Phase 5 TTA handoff checkpoint (`results/ucf_gated_fusion_s42/best_model.pth`) is in place.

---

_Verified: 2026-04-15T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
