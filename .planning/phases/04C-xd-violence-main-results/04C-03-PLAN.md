---
phase: 04C-xd-violence-main-results
plan: 03
type: execute
wave: 2
depends_on: [04C-02]
files_modified:
  - results/results-index.csv
autonomous: false
requirements: [EVAL-03, EVAL-04]

must_haves:
  truths:
    - "User has re-extracted skeleton_2person and clip_mean features for XD-Violence"
    - "2 pooling ablation runs (gated_fusion_xd_2person, gated_fusion_xd_clip_mean) complete"
    - "XD ablation table has all 8 rows (4 main + 2 seeds + 2 pooling)"
    - "Per-category AP for violence-specific subset (Fighting/Abuse/Riot) is higher than full test-set AP"
  artifacts:
    - path: "results/xd_gated_fusion_2person_s42/.done"
      provides: "2-person aggregation pooling ablation complete"
    - path: "results/xd_gated_fusion_clip_mean_s42/.done"
      provides: "CLIP mean-only pooling ablation complete"
    - path: "results/results-index.csv"
      provides: "2 new pooling ablation rows appended (total 8 XD rows)"
  key_links:
    - from: "E:/features/xd/skeleton_2person/"
      to: "configs/gated_fusion_xd_2person.yaml"
      via: "paths.skeleton_features"
      pattern: "skeleton_2person"
    - from: "E:/features/xd/clip_mean/"
      to: "configs/gated_fusion_xd_clip_mean.yaml"
      via: "paths.clip_features"
      pattern: "clip_mean"
---

<objective>
Complete the XD-Violence ablation table with the 2 pooling ablation runs (2-person skeleton concat and CLIP mean-only), after the user has re-extracted the required features. Then compile the final Phase 4c results summary.

Purpose: The pooling ablations (D-22/D-23) compare multi-person aggregation and CLIP pooling strategies. These require re-extracted features that the user runs in separate conda environments (vcc-ctrgcn for skeleton, vcc-skeleton for CLIP). After re-extraction, Claude runs the 2 remaining training+evaluation specs.

Output: 2 completed pooling ablation runs, final 8-row XD ablation table, per-category analysis confirming SC #4.
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
@.planning/phases/04C-xd-violence-main-results/04C-02-SUMMARY.md
</context>

<tasks>

<task type="checkpoint:human-action" gate="blocking">
  <what-needs-doing>
Re-extract XD-Violence features with pooling variant flags. These commands must run in separate conda environments that Claude cannot activate.

**Terminal 1 -- Skeleton 2-person concat (vcc-ctrgcn env, ~2-4h):**
```bash
conda activate vcc-ctrgcn
cd D:/ViolenceCC
python scripts/extract_ctrgcn.py --keep-persons --dataset xd
```
Output: `E:/features/xd/skeleton_2person/*.npy` — each file shape `[N_snippets, 2, 256]`.

**Terminal 2 -- CLIP mean-only (vcc-main env, ~1-2h):**
```bash
conda activate vcc-main
cd D:/ViolenceCC
python scripts/extract_clip.py --pool mean --dataset xd
```
Output: `E:/features/xd/clip_mean/*.npy` — each file shape `[N_snippets, 512]`.

Both can run in parallel on separate terminals. No code changes needed -- the `--keep-persons` and `--pool mean` flags already exist from Phase 4.
  </what-needs-doing>
  <how-to-verify>
After extraction completes, verify feature counts:
```bash
ls E:/features/xd/skeleton_2person/*.npy | wc -l   # expect ~4752
ls E:/features/xd/clip_mean/*.npy | wc -l           # expect ~4752
```
  </how-to-verify>
  <resume-signal>Type "extracted" when both feature directories are populated, or describe any extraction errors.</resume-signal>
</task>

<task type="auto">
  <name>Task 2: Execute phase4c_pooling queue + compile final ablation table</name>
  <files>results/results-index.csv</files>
  <read_first>
    - .planning/phases/04C-xd-violence-main-results/04C-02-SUMMARY.md (confirm main results and AP assessment)
    - configs/gated_fusion_xd_2person.yaml (verify paths point to skeleton_2person)
    - configs/gated_fusion_xd_clip_mean.yaml (verify paths point to clip_mean)
    - scripts/run_ablations.py (verify phase4c_pooling queue exists)
  </read_first>
  <action>
**Step 1 -- Verify re-extracted features exist:**

```bash
ls E:/features/xd/skeleton_2person/*.npy | wc -l   # expect ~4752
ls E:/features/xd/clip_mean/*.npy | wc -l           # expect ~4752
```

If counts are significantly below 4752, STOP and investigate. The feature count must match the cleaned split file (3358 train + 594 val + 800 test = 4752).

**Step 2 -- Dry run pooling queue:**

```bash
cd D:/ViolenceCC
C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue phase4c_pooling --dry-run --no-preflight
```

Verify output shows 2 specs: `xd_gated_fusion_2person_s42` and `xd_gated_fusion_clip_mean_s42`.

**Step 3 -- Run phase4c_pooling queue:**

```bash
C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue phase4c_pooling --no-preflight
```

This trains and evaluates 2 pooling ablation models (~1-1.5h GPU time).

**Step 4 -- Compile complete Phase 4c ablation table:**

Read all 8 XD rows from `results/results-index.csv` and compile:

| Variant | Cache | Seed | AP | AUC |
|---------|-------|------|----|-----|
| skeleton_only | default | 42 | ? | ? |
| clip_only | default | 42 | ? | ? |
| late_fusion | default | 42 | ? | ? |
| gated_fusion | default | 42 | ? | ? |
| gated_fusion | default | 123 | ? | ? |
| gated_fusion | default | 2024 | ? | ? |
| gated_fusion | 2person | 42 | ? | ? |
| gated_fusion | clip_mean | 42 | ? | ? |

Report:
1. Full 8-row ablation table
2. Gated Fusion 3-seed mean +/- std (from Plan 04C-02 + this data)
3. Pooling comparison: default vs 2person vs clip_mean AP
4. Per-category breakdown for Gated Fusion (seed=42): all 6 categories
5. Violence-specific subset analysis (per D-03): compute mean AP of {Fighting, Abuse, Riot} and compare against full test-set AP (SC #4)

**Step 5 -- Phase 4c success criteria assessment:**

Map each SC to observed result:
- SC #1: Gated Fusion AP >= 80%? (or D-06 cascade outcome from Plan 04C-02)
- SC #2: 8-row ablation table complete? (6 variants + 2 pooling ablations)
- SC #3: 3-seed std < 0.5%?
- SC #4: Per-category violence subset AP > full test-set AP?
  </action>
  <verify>
    <automated>cd D:/ViolenceCC && C:/Anaconda/envs/vcc-main/python.exe -c "import csv; rows=[r for r in csv.DictReader(open('results/results-index.csv')) if r['dataset']=='xd']; print(f'XD rows: {len(rows)}'); [print(f\"  {r['run_name']}: AP={r['ap']}, AUC={r['auc']}\") for r in rows]; assert len(rows) >= 8, f'Expected 8 XD rows, got {len(rows)}'"</automated>
  </verify>
  <acceptance_criteria>
    - results/xd_gated_fusion_2person_s42/.done exists
    - results/xd_gated_fusion_clip_mean_s42/.done exists
    - results/results-index.csv contains exactly 8 rows with dataset=xd
    - results/xd_gated_fusion_2person_s42/per_category.csv exists
    - results/xd_gated_fusion_clip_mean_s42/per_category.csv exists
    - SC #2 confirmed: 8 distinct XD run_names in results-index.csv
    - runner-errors.log does not contain phase4c_pooling entries
  </acceptance_criteria>
  <done>8 XD ablation rows complete in results-index.csv, pooling comparison available, per-category violence subset analysis confirms SC #4, all Phase 4c success criteria assessed.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
Complete Phase 4c XD-Violence ablation table with 8 rows:
1. 4 main variants at seed=42 (from Plan 04C-02)
2. 2 additional Gated Fusion seeds (from Plan 04C-02)
3. 2 pooling ablations at seed=42 (from this plan)
Plus: 3-seed stability, per-category breakdown, violence subset analysis.

Task 2 above will print the complete results table and SC assessment.
  </what-built>
  <how-to-verify>
1. Review the 8-row ablation table
2. Confirm 3-seed Gated Fusion std < 0.5% (SC #3)
3. Confirm per-category violence subset (Fighting/Abuse/Riot mean AP) exceeds full test-set AP (SC #4)
4. Review overall Phase 4c SC assessment (SC #1 through SC #4)
5. If all SCs pass or MISS-ACCEPTED: approve to close Phase 4c
6. If INVESTIGATE needed: describe what to check
  </how-to-verify>
  <resume-signal>Type "approved" to close Phase 4c, or describe issues to investigate.</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| E:/features/xd/skeleton_2person -> train.py | User-extracted 2-person features loaded by dataloader |
| E:/features/xd/clip_mean -> train.py | User-extracted mean-only CLIP features loaded by dataloader |
| subprocess -> train.py | Pooling configs invoke train.py with modified feature paths |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4c-08 | Tampering | E:/features/xd/skeleton_2person/ | accept | Features extracted by user from verified extraction scripts; shape assertions in dataloader catch format mismatches. |
| T-4c-09 | Tampering | E:/features/xd/clip_mean/ | accept | Same as T-4c-08; CLIP extraction script validates output shape. |
| T-4c-10 | Elevation of Privilege | np.load in MILFeatureDataset | mitigate | np.load called WITHOUT allow_pickle (existing pattern from Phase 3 D-10); refuses Python object deserialization. |
</threat_model>

<verification>
1. `ls results/xd_*_s*/.done | wc -l` returns 8 (6 from Plan 02 + 2 from this plan)
2. `grep -c "xd" results/results-index.csv` returns 8 (excluding header)
3. All 8 run directories contain eval_metrics.json, eval_scores.npz, per_category.csv, .done
4. Violence subset (Fighting/Abuse/Riot) mean AP exceeds full test-set AP
</verification>

<success_criteria>
- 8 complete XD ablation runs with .done markers
- Final ablation table printed with AP/AUC for all 8 variants
- 3-seed Gated Fusion std assessed against 0.5% gate
- Per-category violence subset AP exceeds full test-set AP
- All Phase 4c success criteria assessed and documented
- User approves final results
</success_criteria>

<output>
After completion, create `.planning/phases/04C-xd-violence-main-results/04C-03-SUMMARY.md`
</output>
