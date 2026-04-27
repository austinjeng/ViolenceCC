---
phase: 04C-xd-violence-main-results
verified: 2026-04-27T19:55:21Z
status: human_needed
score: 10/11 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Verify results/results-index.csv 8 XD rows display correctly in any CSV viewer"
    expected: "8 rows with dataset=xd, distinct run_names, AP/AUC values matching eval_metrics.json"
    why_human: "CSV formatting edge cases (quoting, commas in fields) require visual inspection"
  - test: "Confirm per_category.csv files open correctly and category codes match XD-Violence documentation"
    expected: "6 categories (B1, B2, B4, B5, B6, G) with AP/AUC values in each per_category.csv"
    why_human: "Category code-to-name mapping (B1=Fighting, B5=Abuse, etc.) requires domain knowledge verification"
  - test: "Verify REQUIREMENTS.md traceability matrix rows EVAL-02..EVAL-05 are updated from 'pending Phase 4c' to reflect completion"
    expected: "Status column reflects XD-side completion with actual AP/AUC numbers"
    why_human: "The requirement descriptions (lines 51-54) are marked [x] but the traceability matrix (lines 140-143) still says 'XD-side pending Phase 4c' -- needs human decision on whether to update"
---

# Phase 4C: XD-Violence Main Results Verification Report

**Phase Goal:** Reproduce Phase 4's complete ablation table on XD-Violence -- Gated Fusion + pooling ablations + 3-seed stability + per-category breakdown (Fighting/Abuse/Riot) -- using the dataset-portable Phase 4 code.
**Verified:** 2026-04-27T19:55:21Z
**Status:** human_needed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Source | Status | Evidence |
|---|-------|--------|--------|----------|
| 1 | XD split files exclude the 2 featureless videos and loaders skip comment lines | Plan 01 | VERIFIED | `data/splits/xd_train.txt` has 3360 lines (2 comment headers + 3358 IDs); `_load_split` in `src/data/dataset.py:148` filters `line.strip().startswith("#")`; excluded videos `v=8cTqh9tMz_I__#1_label_A` and `v=Gm73TwtUyGY__#1_label_G-0-0` documented in comment lines |
| 2 | evaluate.py correctly routes dataset=xd to XD annotations with snippet_window=64 and upsample_factor=1 | Plan 01 | VERIFIED | `src/evaluate.py:225` has `elif ds == "xd":` branch with `snippet_window=64`, `upsample_factor=1`, calls `parse_xd_annotations` from `src.eval.xd_annotations`; 4 unit tests in `test_evaluate_xd.py` all pass |
| 3 | 6 XD YAML configs exist with identical hyperparameters to UCF counterparts | Plan 01 | VERIFIED | All 6 configs exist: `skeleton_only_xd.yaml` (38L), `clip_only_xd.yaml` (39L), `late_fusion_xd.yaml` (41L), `gated_fusion_xd.yaml` (40L), `gated_fusion_xd_2person.yaml` (44L), `gated_fusion_xd_clip_mean.yaml` (43L); all contain `dataset: xd`; gated_fusion_xd.yaml confirmed byte-identical hyperparameters (lr=1e-4, epochs=50, batch_size=16, patience=10, k_topk=3) |
| 4 | 3 new queues (phase4c_main, phase4c_pooling, phase4c_seeds) are registered and discoverable by --queue | Plan 01 | VERIFIED | All 3 queue names found in `scripts/run_ablations.py` QUEUES dict; `--queue` choices include all 3; phase4c_main has 4 specs, phase4c_pooling has 2 specs, phase4c_seeds has 2 specs; 12 tests in `test_run_ablations.py` pass including queue definition verification |
| 5 | Gated Fusion AP on XD-Violence is computed and recorded in results-index.csv | Plan 02 / SC #1 | VERIFIED | `results/xd_gated_fusion_s42/eval_metrics.json` contains `"ap": 0.7192` (71.92%); row exists in `results/results-index.csv` with matching values; MISS-ACCEPTED per D-06 step 2 (70-79% range) |
| 6 | All 4 main XD variants (skeleton_only, clip_only, late_fusion, gated_fusion) complete at seed=42 | Plan 02 | VERIFIED | `.done` markers present in all 4 directories: `xd_skeleton_only_s42`, `xd_clip_only_s42`, `xd_late_fusion_s42`, `xd_gated_fusion_s42`; each has `eval_metrics.json` + `per_category.csv` |
| 7 | Gated Fusion 3-seed stability (seeds 42, 123, 2024) is computed with std reported | Plan 02 / SC #3 | VERIFIED | `.done` + `eval_metrics.json` in all 3 seed dirs; independently verified: AP mean=70.98%, std(ddof=1)=1.08%; AUC mean=91.72%, std(ddof=1)=0.29%; values match SUMMARY claims exactly |
| 8 | Per-category breakdown CSV exists for all completed runs | Plan 02 | VERIFIED | All 8 run directories contain `per_category.csv`; Gated Fusion seed=42 CSV has 6 categories (B1/B2/B4/B5/B6/G) with real AP/AUC values |
| 9 | 2 pooling ablation runs (gated_fusion_xd_2person, gated_fusion_xd_clip_mean) complete | Plan 03 | VERIFIED | `.done` + `eval_metrics.json` + `per_category.csv` in both `xd_gated_fusion_2person_s42/` and `xd_gated_fusion_clip_mean_s42/` |
| 10 | XD ablation table has all 8 rows (4 main + 2 seeds + 2 pooling) | Plan 03 / SC #2 | VERIFIED | `results/results-index.csv` contains 8 rows with `dataset=xd` (not counting 2 xd_i3d rows from Phase 4b); grep count confirmed 10 total xd lines, 8 with dataset field "xd" |
| 11 | Per-category AP for violence-specific subset (Fighting/Abuse/Riot) is higher than full test-set AP | Plan 03 / SC #4 | PARTIAL | Fighting (77.76%) and Riot (88.15%) individually exceed full AP (71.92%); Abuse (44.89%) does not; subset mean 70.27% is below full AP 71.92%. SC as worded ("higher AP on violence-specific subsets versus full test set") is not met for subset mean. Independently verified from eval_metrics.json. |

**Score:** 10/11 truths verified (1 PARTIAL)

### Roadmap Success Criteria Cross-Check

| SC | Criterion | ROADMAP Status | Verification Status | Evidence |
|----|-----------|---------------|---------------------|----------|
| #1 | Gated Fusion AP >= 80% on XD-Violence | MISS-ACCEPTED (D-06 step 2) | VERIFIED (as MISS-ACCEPTED) | AP=71.92% (s42), mean=70.98%; D-06 cascade applies; documented in ROADMAP |
| #2 | 8-row ablation table exists | PASS | VERIFIED | 8 XD rows in results-index.csv confirmed by grep |
| #3 | 3-seed std < 0.5% | PARTIAL | VERIFIED (as PARTIAL) | AP std=1.08% exceeds gate; AUC std=0.29% within gate; both values independently computed and confirmed |
| #4 | Violence subset AP > full test-set AP | PARTIAL | PARTIAL | Fighting/Riot individually exceed full AP; Abuse drags subset mean below; independently verified from raw JSON |

All 4 ROADMAP success criteria are accounted for. SC #1 was pre-accepted as MISS-ACCEPTED per D-06. SC #3 and SC #4 are documented as PARTIAL in the ROADMAP with thesis narrative guidance.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/splits/xd_train.txt` | Cleaned XD train split with 3358 IDs | VERIFIED | 3360 lines (2 comments + 3358 IDs); contains `# Excluded:` headers |
| `src/evaluate.py` | XD fusion evaluation branch | VERIFIED | `elif ds == "xd":` at line 225 with snippet_window=64, upsample_factor=1, parse_xd_annotations call |
| `configs/gated_fusion_xd.yaml` | XD Gated Fusion config | VERIFIED | 40 lines, `dataset: xd`, real model/data/train sections |
| `configs/skeleton_only_xd.yaml` | XD Skeleton Only config | VERIFIED | 38 lines, `dataset: xd` |
| `configs/clip_only_xd.yaml` | XD CLIP Only config | VERIFIED | 39 lines, `dataset: xd` |
| `configs/late_fusion_xd.yaml` | XD Late Fusion config | VERIFIED | 41 lines, `dataset: xd` |
| `configs/gated_fusion_xd_2person.yaml` | XD 2-person pooling config | VERIFIED | 44 lines, `skeleton_2person` path |
| `configs/gated_fusion_xd_clip_mean.yaml` | XD CLIP mean pooling config | VERIFIED | 43 lines, `clip_mean` path |
| `scripts/run_ablations.py` | Phase 4c queue definitions | VERIFIED | 3 queues (phase4c_main: 4 specs, phase4c_pooling: 2 specs, phase4c_seeds: 2 specs) |
| `tests/test_evaluate_xd.py` | XD fusion evaluate branch tests | VERIFIED | 4 tests, 120+ lines, substantive assertions (frame counts, label intervals, categories) |
| `results/xd_skeleton_only_s42/.done` | Skeleton-Only run complete | VERIFIED | File exists (2026-04-27) |
| `results/xd_clip_only_s42/.done` | CLIP-Only run complete | VERIFIED | File exists (2026-04-27) |
| `results/xd_late_fusion_s42/.done` | Late Fusion run complete | VERIFIED | File exists (2026-04-27) |
| `results/xd_gated_fusion_s42/.done` | Gated Fusion seed=42 complete | VERIFIED | File exists (2026-04-27) |
| `results/xd_gated_fusion_s123/.done` | Gated Fusion seed=123 complete | VERIFIED | File exists (2026-04-27) |
| `results/xd_gated_fusion_s2024/.done` | Gated Fusion seed=2024 complete | VERIFIED | File exists (2026-04-27) |
| `results/xd_gated_fusion_2person_s42/.done` | 2-person pooling ablation complete | VERIFIED | File exists (2026-04-28) |
| `results/xd_gated_fusion_clip_mean_s42/.done` | CLIP mean pooling ablation complete | VERIFIED | File exists (2026-04-28) |
| `results/results-index.csv` | 8 XD rows appended | VERIFIED | 8 rows with dataset=xd confirmed; AP/AUC values match eval_metrics.json |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `configs/gated_fusion_xd.yaml` | `src/data/loaders.py` | `dataset: xd` triggers XD split routing | WIRED | Config contains `dataset: xd` line 4 |
| `src/evaluate.py` | `src/eval/xd_annotations.py` | `elif ds == 'xd'` branch calls `parse_xd_annotations` | WIRED | Import at line 46, call at line 237 within `elif ds == "xd":` branch |
| `scripts/run_ablations.py` | `configs/gated_fusion_xd.yaml` | RunSpec config field | WIRED | `RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml")` at line 117 |
| `scripts/run_ablations.py` | `src/train.py` | subprocess invocation with --config and --seed | WIRED | `sys.executable, "src/train.py", "--config", spec.config` at line 182 |
| `scripts/run_ablations.py` | `src/evaluate.py` | subprocess invocation with --run-dir | WIRED | `sys.executable, "src/evaluate.py", "--run-dir"` at line 207 |
| `results/xd_gated_fusion_s42/eval_metrics.json` | `results/results-index.csv` | `results_index_append` | WIRED | Import at line 41, call after evaluation in run_one flow |
| `configs/gated_fusion_xd_2person.yaml` | `E:/features/xd/skeleton_2person/` | `paths.skeleton_features` | WIRED | Config line 10: `skeleton_features: "E:/features/xd/skeleton_2person"` |
| `configs/gated_fusion_xd_clip_mean.yaml` | `E:/features/xd/clip_mean/` | `paths.clip_features` | WIRED | Config line 11: `clip_features: "E:/features/xd/clip_mean"` |

### Data-Flow Trace (Level 4)

Not applicable -- this phase produces training results (eval_metrics.json, per_category.csv, results-index.csv) via GPU training runs, not UI components rendering dynamic data. The data flow is: configs -> train.py -> model -> evaluate.py -> eval_metrics.json -> results_index_append -> results-index.csv. All links verified in Key Link Verification above.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 23/23 tests pass | `python -m pytest tests/test_evaluate_xd.py tests/test_run_ablations.py tests/test_evaluate_xd_i3d.py tests/test_evaluate_cli.py -v` | 23 passed in 90.63s | PASS |
| 3-seed AP std independently computed | `numpy.std([0.7192, 0.7120, 0.6980], ddof=1)` | 1.08% (matches SUMMARY) | PASS |
| 3-seed AUC std independently computed | `numpy.std([0.9200, 0.9173, 0.9142], ddof=1)` | 0.29% (matches SUMMARY) | PASS |
| Per-category Fighting > full AP | `0.7776 > 0.7192` | True | PASS |
| Per-category Riot > full AP | `0.8815 > 0.7192` | True | PASS |
| Per-category Abuse < full AP | `0.4489 > 0.7192` | False (expected) | PASS |
| results-index.csv XD row count | `grep -c "xd" results/results-index.csv` | 10 (8 xd + 2 xd_i3d) | PASS |
| All 8 .done markers present | `ls results/xd_*/.done` | 8 files found | PASS |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| EVAL-02 | 04C-01, 04C-02 | Frame-level AUC evaluation on XD-Violence with correct snippet-to-frame expansion | SATISFIED | `evaluate.py` XD fusion branch uses `snippet_window=64`, `upsample_factor=1`; Gated Fusion AUC=92.00% (s42); all 8 runs produce frame-level AUC in eval_metrics.json |
| EVAL-03 | 04C-01, 04C-02, 04C-03 | Frame-level AP evaluation on XD-Violence + 8-row ablation table | SATISFIED | 8 XD rows in results-index.csv; Gated Fusion AP=71.92% MISS-ACCEPTED per D-06; all variant/seed/pooling combinations computed |
| EVAL-04 | 04C-03 | Per-category violence subset breakdown | SATISFIED | All 6 XD categories (B1/B2/B4/B5/B6/G) in per_category.csv for all 8 runs; Fighting 77.76%, Riot 88.15% exceed full AP; Abuse 44.89% identified as hardest |
| EVAL-05 | 04C-02, 04C-03 | 3-seed mean +/- std for Gated Fusion | SATISFIED | Seeds {42, 123, 2024}: AP 70.98% +/- 1.08%, AUC 91.72% +/- 0.29%; seed sensitivity documented as thesis finding |

**Note:** REQUIREMENTS.md traceability matrix (lines 140-143) still shows "XD-side pending Phase 4c" even though the requirement checkboxes (lines 51-54) are marked `[x]` as complete. This is a documentation inconsistency that should be cleaned up.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | No TODO/FIXME/PLACEHOLDER/stub patterns found in any modified file |

Zero anti-patterns detected across all 12 modified/created files scanned.

### Human Verification Required

### 1. CSV Formatting Check

**Test:** Open `results/results-index.csv` in a spreadsheet application and verify the 8 XD rows display correctly with all columns populated.
**Expected:** 8 rows with dataset=xd, distinct run_names, AP/AUC values matching eval_metrics.json files.
**Why human:** CSV formatting edge cases (quoting, commas in fields) require visual inspection beyond grep.

### 2. Per-Category Code-to-Name Mapping

**Test:** Verify that per_category.csv category codes (B1, B2, B4, B5, B6, G) map correctly to XD-Violence documentation (B1=Fighting, B2=Shooting, B4=Riot, B5=Abuse, B6=Car Accident, G=Explosion).
**Expected:** All 6 codes present with meaningful AP/AUC values in each file.
**Why human:** Category code-to-name mapping is domain knowledge from the XD-Violence paper, not verifiable from code alone.

### 3. REQUIREMENTS.md Traceability Matrix Update

**Test:** Check whether REQUIREMENTS.md lines 140-143 should be updated from "XD-side pending Phase 4c" to reflect completion.
**Expected:** Status column reflects XD-side completion with actual AP/AUC numbers.
**Why human:** The requirement descriptions (lines 51-54) are already marked `[x]` but the traceability table was not updated -- needs human decision on whether/how to update.

### Gaps Summary

No blocking gaps found. All code artifacts exist, are substantive, and are properly wired. All 8 training runs completed with real metrics. All 23 tests pass. All 4 ROADMAP success criteria are accounted for (SC #1 MISS-ACCEPTED, SC #2 PASS, SC #3 PARTIAL, SC #4 PARTIAL).

The two PARTIAL success criteria (SC #3: AP std 1.08% > 0.5% gate; SC #4: subset mean 70.27% < full AP 71.92%) are documented honestly in the ROADMAP with thesis narrative guidance. These are empirical outcomes, not implementation gaps -- the code correctly computes and reports the metrics, the numbers simply did not meet the aspirational targets. Both are framed as thesis findings (AP seed sensitivity, Abuse category difficulty).

### Confirmation Bias Counter Findings

1. **Partially met requirement (SC #3):** AP std 1.08% exceeds the 0.5% gate. This is a real empirical shortfall, not an implementation bug. The ROADMAP correctly marks it PARTIAL.
2. **Test coverage gap:** Tests verify the evaluation branch but do not exercise the full train-to-evaluate pipeline. This is acceptable because the actual GPU runs (with real metrics) serve as integration tests.
3. **Edge case:** If `xd_temporal.txt` were deleted, the `elif ds == "xd"` branch would set all labels to zero (annos={} fallback). Low risk since the file is committed to git.

---

_Verified: 2026-04-27T19:55:21Z_
_Verifier: Claude (gsd-verifier)_
