---
phase: 04C-xd-violence-main-results
plan: 02
type: execute
wave: 1
depends_on: [04C-01]
files_modified:
  - results/results-index.csv
autonomous: false
requirements: [EVAL-02, EVAL-03, EVAL-05]

must_haves:
  truths:
    - "Gated Fusion AP on XD-Violence is computed and recorded in results-index.csv"
    - "All 4 main XD variants (skeleton_only, clip_only, late_fusion, gated_fusion) complete at seed=42"
    - "Gated Fusion 3-seed stability (seeds 42, 123, 2024) is computed with std reported"
    - "Per-category breakdown CSV exists for all completed runs"
  artifacts:
    - path: "results/xd_skeleton_only_s42/.done"
      provides: "Skeleton-Only XD run complete"
    - path: "results/xd_clip_only_s42/.done"
      provides: "CLIP-Only XD run complete"
    - path: "results/xd_late_fusion_s42/.done"
      provides: "Late Fusion XD run complete"
    - path: "results/xd_gated_fusion_s42/.done"
      provides: "Gated Fusion XD seed=42 run complete"
    - path: "results/xd_gated_fusion_s123/.done"
      provides: "Gated Fusion XD seed=123 run complete"
    - path: "results/xd_gated_fusion_s2024/.done"
      provides: "Gated Fusion XD seed=2024 run complete"
    - path: "results/results-index.csv"
      provides: "6 new XD rows appended"
  key_links:
    - from: "scripts/run_ablations.py"
      to: "src/train.py"
      via: "subprocess invocation with --config and --seed"
      pattern: "train.py.*--config"
    - from: "scripts/run_ablations.py"
      to: "src/evaluate.py"
      via: "subprocess invocation with --run-dir"
      pattern: "evaluate.py.*--run-dir"
    - from: "results/xd_gated_fusion_s42/eval_metrics.json"
      to: "results/results-index.csv"
      via: "results_index_append"
      pattern: "results_index_append"
---

<objective>
Run the Phase 4c main ablation queue (4 XD variants at seed=42) and seed stability queue (Gated Fusion seeds 123, 2024) on the existing 4752 XD features. This produces the thesis-critical Gated Fusion AP number and the 3-seed stability measure.

Purpose: Get the primary XD-Violence results ASAP -- Gated Fusion AP is the #1 thesis deliverable from this phase. The 3-seed stability protocol confirms reproducibility. D-06 contingency cascade applies to the observed AP.

Output: 6 completed run directories under results/, 6 rows appended to results-index.csv, per_category.csv in each run directory.
</objective>

<execution_context>
@D:/ViolenceCC/.claude/get-shit-done/workflows/execute-plan.md
@D:/ViolenceCC/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/04C-xd-violence-main-results/04C-CONTEXT.md
@.planning/phases/04C-xd-violence-main-results/04C-01-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Execute phase4c_main and phase4c_seeds queues</name>
  <files>results/results-index.csv</files>
  <read_first>
    - .planning/phases/04C-xd-violence-main-results/04C-01-SUMMARY.md (confirm all code changes landed)
    - scripts/run_ablations.py (verify phase4c_main and phase4c_seeds queues exist)
    - configs/gated_fusion_xd.yaml (verify dataset: xd and correct paths)
  </read_first>
  <action>
**Step 1 -- Dry run both queues to verify config resolution:**

```bash
cd D:/ViolenceCC
C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue phase4c_main --dry-run --no-preflight
C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue phase4c_seeds --dry-run --no-preflight
```

Verify output shows 4 specs for phase4c_main and 2 specs for phase4c_seeds with correct run names:
- `xd_skeleton_only_s42`, `xd_clip_only_s42`, `xd_late_fusion_s42`, `xd_gated_fusion_s42`
- `xd_gated_fusion_s123`, `xd_gated_fusion_s2024`

**Step 2 -- Run phase4c_main queue (4 XD variants at seed=42):**

```bash
C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue phase4c_main --no-preflight
```

This trains and evaluates 4 models sequentially (~2-3h total GPU time on RTX 4090 with cached features). Each run:
1. Trains via src/train.py with XD config (early stopping patience=10)
2. Evaluates via src/evaluate.py on test split
3. Appends to results/results-index.csv
4. Writes .done marker

Expected convergence: ~20-30 epochs (XD has ~3360 training videos vs UCF's ~810, so early stopping should trigger sooner).

**Step 3 -- Run phase4c_seeds queue (Gated Fusion seeds 123, 2024):**

```bash
C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue phase4c_seeds --no-preflight
```

This trains and evaluates Gated Fusion at seeds 123 and 2024 (~1-1.5h GPU time). seed=42 already completed in phase4c_main.

**Step 4 -- Collect and report results:**

After both queues complete:

1. Read `results/results-index.csv` and extract the 6 new XD rows.
2. Report the ablation table:
   - skeleton_only AP/AUC
   - clip_only AP/AUC
   - late_fusion AP/AUC
   - gated_fusion AP/AUC (seed=42)
3. Report 3-seed Gated Fusion stability: mean +/- std of AP across seeds {42, 123, 2024}.
4. Apply D-06 contingency cascade to Gated Fusion AP:
   - AP >= 80%: SC #1 PASS
   - AP 70-79%: MISS-ACCEPTED (document as thesis limitation)
   - AP < 70%: INVESTIGATE (verify data loader, feature alignment, single-modal APs)
5. Read per_category.csv from `results/xd_gated_fusion_s42/` and report per-category AP/AUC for all 6 XD categories.

**Error handling:** If any run in phase4c_main fails, the queue continues to the next spec (D-32/D-34 behavior). Check `runner-errors.log` for failures. If gated_fusion fails, do NOT proceed to phase4c_seeds until the failure is diagnosed.
  </action>
  <verify>
    <automated>cd D:/ViolenceCC && C:/Anaconda/envs/vcc-main/python.exe -c "import csv; rows=[r for r in csv.DictReader(open('results/results-index.csv')) if r['dataset']=='xd']; print(f'XD rows: {len(rows)}'); [print(f\"  {r['run_name']}: AP={r['ap']}, AUC={r['auc']}\") for r in rows]"</automated>
  </verify>
  <acceptance_criteria>
    - results/xd_skeleton_only_s42/.done exists
    - results/xd_clip_only_s42/.done exists
    - results/xd_late_fusion_s42/.done exists
    - results/xd_gated_fusion_s42/.done exists
    - results/xd_gated_fusion_s123/.done exists
    - results/xd_gated_fusion_s2024/.done exists
    - results/results-index.csv contains 6 rows with dataset=xd
    - Each XD run directory contains eval_metrics.json, eval_scores.npz, per_category.csv, .done
    - results/xd_gated_fusion_s42/per_category.csv has rows for Fighting, Shooting, Riot, Abuse, Car Accident, Explosion
    - Gated Fusion 3-seed AP std is computed (pass/fail evaluated against D-06 cascade)
    - runner-errors.log does not contain any phase4c entries (or if it does, failures are diagnosed)
  </acceptance_criteria>
  <done>6 XD runs complete with .done markers, results-index.csv has 6 XD rows, Gated Fusion AP evaluated against D-06 cascade, 3-seed stability computed, per-category breakdown available.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
Phase 4c main results: 4 XD model variants trained and evaluated, plus Gated Fusion 3-seed stability. The task above will report:
1. Ablation table (4 variants AP/AUC at seed=42)
2. Gated Fusion 3-seed mean +/- std
3. D-06 contingency assessment (PASS / MISS-ACCEPTED / INVESTIGATE)
4. Per-category breakdown for all 6 XD anomaly types
  </what-built>
  <how-to-verify>
1. Review the ablation table printed by Task 1 Step 4
2. Confirm Gated Fusion AP assessment matches D-06 cascade
3. If INVESTIGATE triggered (AP < 70%): review single-modal APs and feature alignment before proceeding
4. Confirm per-category CSV has sensible values (violence categories should have higher AP than full test set)
5. Decide whether to proceed to Wave 2 (pooling ablation re-extraction)
  </how-to-verify>
  <resume-signal>Type "approved" to proceed to Plan 04C-03 (pooling ablations), or describe issues to investigate.</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| subprocess -> train.py | run_ablations.py invokes train.py as subprocess with config path |
| subprocess -> evaluate.py | run_ablations.py invokes evaluate.py as subprocess with run-dir path |
| filesystem -> results-index.csv | Metrics JSON parsed and appended to CSV audit log |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4c-05 | Tampering | results/results-index.csv | accept | Append-only CSV (D-33); .done markers prevent re-execution of completed runs. Research codebase, not deployed. |
| T-4c-06 | Repudiation | eval_metrics.json | mitigate | config_hash and checkpoint_sha recorded in each eval_metrics.json (D-11); git SHA captured for reproducibility. |
| T-4c-07 | Information Disclosure | results/ directory | accept | Contains anomaly scores and metrics only; no PII. Local filesystem. |
</threat_model>

<verification>
1. `ls results/xd_*_s*/.done | wc -l` returns 6
2. `grep -c "xd" results/results-index.csv` returns 6 (excluding header)
3. Gated Fusion AP is assessed against D-06 cascade
4. per_category.csv exists in all 6 run directories
</verification>

<success_criteria>
- 6 XD model runs complete with .done markers
- Gated Fusion AP reported and assessed per D-06 cascade
- 3-seed Gated Fusion std computed and assessed against 0.5% gate (SC #3)
- Per-category breakdown available for all 6 XD anomaly types (SC #4)
- User has approved results before proceeding to pooling ablations
</success_criteria>

<output>
After completion, create `.planning/phases/04C-xd-violence-main-results/04C-02-SUMMARY.md`
</output>
