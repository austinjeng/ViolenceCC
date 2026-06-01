---
phase: quick-260601-okz
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - results/_smoothfix/xd_measurement.md   # gitignored scratch; not committed
autonomous: true
requirements: [QUICK-260601-okz]
must_haves:
  truths:
    - "Both XD gated contenders retrain on current main (corrected smoothness) at seed 42 to scratch"
    - "Each fixed retrain evaluates on XD test split with n_frames ~= 2,313,024 (full XD length, no truncation)"
    - "Fixed AP/AUC are compared against the canonical (buggy) baselines for both backbones"
    - "Delta_AP and Delta_AUC are reported per backbone and contextualized against XD gated AP seed-std (~2.8-2.9pp)"
    - "Verdict (NEGLIGIBLE vs MATERIAL) is stated WITHOUT making the A/B decision or editing the paper"
  artifacts:
    - path: "results/_smoothfix/xd_base_fixed_s42/eval_metrics.json"
      provides: "Fixed SigLIP2 Base eval (AP, AUC, n_frames)"
    - path: "results/_smoothfix/xd_so400m_fixed_s42/eval_metrics.json"
      provides: "Fixed SO400M eval (AP, AUC, n_frames)"
    - path: "results/_smoothfix/xd_measurement.md"
      provides: "Comparison table + ordering check + verdict"
  key_links:
    - from: "src/losses/mil_loss.py"
      to: "results/_smoothfix/*/best_model.pth"
      via: "corrected _smoothness (dim 1 shift) on current main during training"
      pattern: "arr2\\[:, :-1\\] = .*\\[:, 1:\\]"
---

<objective>
Measure the smoothness-axis fix's impact on XD-Violence (the dataset reported in AP). The code fix
(`mil_loss._smoothness` shifting dim 1 instead of dim 0) is already committed on main at f89910b. This
plan retrains the two XD gated contenders (SigLIP2 Base + SO400M, seed 42) with the corrected code,
evaluates them on the XD test split, and compares fixed AP/AUC to the canonical (buggy) baselines.

Because XD training is bit-exact deterministic via `set_deterministic` (proven on the UCF control,
which reproduced canonical BIT-FOR-BIT), the CANONICAL XD eval_metrics ARE the valid buggy control —
no separate buggy re-run is needed. Compare the fixed retrain directly to canonical.

Purpose: Quantify XD-AP exposure of the smoothness fix so the team knows whether XD needs a full
retrain + Table 2 re-propagation, or whether the change is within seed noise.
Output: Two scratch retrains + evals under `results/_smoothfix/`, and a comparison report
`results/_smoothfix/xd_measurement.md` + the same table in SUMMARY.

Scratch only. No canonical changes. No A/B decision. No paper edits.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

# The fix being measured (already committed at f89910b, on main):
@src/losses/mil_loss.py

# Train/eval CLIs:
@src/train.py
@src/evaluate.py

# Configs for the two contenders (confirmed in Task 1 to match canonical snapshots):
@configs/gated_fusion_xd_siglip2.yaml
@configs/gated_fusion_xd_so400m.yaml

<interfaces>
<!-- Verified during planning — executor should use directly, no exploration needed. -->

CLI (src/train.py):
  conda run -n vcc-main python src/train.py \
    --config <yaml> --seed <int> --results-dir <dir> --run-name <name>
  Output run dir = <results-dir>/<run-name>  (run_dir = results_dir / run_name; train.py:294-296)
  Writes: config_snapshot.json, best_model.pth, last_model.pth, train_log.csv
  Training is bit-exact deterministic: set_deterministic(seed) at main() entry (train.py:289).

CLI (src/evaluate.py):
  conda run -n vcc-main python src/evaluate.py --run-dir <run-dir> --split test
  Reads config_snapshot.json + best_model.pth from --run-dir; writes eval_metrics.json into same dir.

Canonical (buggy) XD baselines — these ARE the valid control:
  SigLIP2 Base  (results/xd_gated_fusion_siglip2_s42/eval_metrics.json):  AP 0.7192352956184961  AUC 0.9184864084233555  n_frames 2313024
  SigLIP2 SO400M(results/xd_gated_fusion_so400m_s42/eval_metrics.json):   AP 0.7376665210508834  AUC 0.9314835343054276  n_frames 2313024
  At seed 42: SO400M AP (0.7377) > Base AP (0.7192). Base only wins on the 3-SEED MEAN (74.70 vs 73.80).
  XD gated AP seed-std is large (~2.8-2.9pp).

Config <-> snapshot confirmation (verified during planning, recorded here for Task 1 cross-check):
  gated_fusion_xd_siglip2.yaml  == results/xd_gated_fusion_siglip2_s42/config_snapshot.json:
    skeleton_features E:/features/xd/skeleton, clip_features E:/features/xd/siglip2, clip_dim 1536,
    seed 42, k_topk 3, lr 1.0e-4, weight_decay 1.0e-2, margin 1.0, lam_sparse 8.0e-3, lam_smooth 8.0e-4, T 32, batch 16.
  gated_fusion_xd_so400m.yaml   == results/xd_gated_fusion_so400m_s42/config_snapshot.json:
    skeleton_features E:/features/xd/skeleton, clip_features E:/features/xd/siglip2_so400m, clip_dim 2304,
    seed 42, k_topk 3, lr 1.0e-4, weight_decay 1.0e-2, margin 1.0, lam_sparse 8.0e-3, lam_smooth 8.0e-4, T 32, batch 16.
  Both MATCH bit-for-bit on every hyperparameter and feature path. (results_dir in snapshot is the
  absolute D:\ViolenceCC\results from the canonical run; the YAML uses "results" — irrelevant here
  since this plan overrides via --results-dir.)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Confirm the two configs match the canonical config snapshots</name>
  <files>configs/gated_fusion_xd_siglip2.yaml, configs/gated_fusion_xd_so400m.yaml, results/xd_gated_fusion_siglip2_s42/config_snapshot.json, results/xd_gated_fusion_so400m_s42/config_snapshot.json</files>
  <action>
    Read both config YAMLs and both canonical config_snapshot.json files. Confirm that
    configs/gated_fusion_xd_siglip2.yaml and configs/gated_fusion_xd_so400m.yaml match the
    feature dirs and hyperparams that produced the canonical runs: skeleton_features, clip_features,
    clip_dim (1536 Base / 2304 SO400M), seed 42, k_topk 3, lr 1.0e-4, weight_decay 1.0e-2, margin 1.0,
    lam_sparse 8.0e-3, lam_smooth 8.0e-4, T 32, batch_size 16. The <interfaces> block above already
    records the confirmed match from planning — re-verify against the live files and record any drift.
    If a config differs from its snapshot, USE THE SNAPSHOT'S SETTINGS (or the exact config the snapshot
    points to) for Task 2 — do not silently train on a diverged config. Do NOT add snippet_boundaries_dir:
    XD eval is standard full-length (canonical n_frames = 2,313,024, no H1-style truncation).
  </action>
  <verify>
    <automated>conda run -n vcc-main python -c "import json,yaml; b=yaml.safe_load(open('configs/gated_fusion_xd_siglip2.yaml')); s=json.load(open('results/xd_gated_fusion_siglip2_s42/config_snapshot.json'))['config']; assert b['paths']['clip_features']==s['paths']['clip_features']==r'E:/features/xd/siglip2', (b['paths']['clip_features'],s['paths']['clip_features']); assert b['model']['clip_dim']==s['model']['clip_dim']==1536; assert b['train']['k_topk']==s['train']['k_topk']==3; assert float(b['train']['lr'])==float(s['train']['lr'])==1e-4; assert float(b['train']['lam_smooth'])==float(s['train']['lam_smooth'])==8e-4; assert float(b['train']['lam_sparse'])==float(s['train']['lam_sparse'])==8e-3; o=yaml.safe_load(open('configs/gated_fusion_xd_so400m.yaml')); so=json.load(open('results/xd_gated_fusion_so400m_s42/config_snapshot.json'))['config']; assert o['paths']['clip_features']==so['paths']['clip_features']==r'E:/features/xd/siglip2_so400m'; assert o['model']['clip_dim']==so['model']['clip_dim']==2304; print('CONFIGS MATCH SNAPSHOTS')"</automated>
  </verify>
  <done>Both configs confirmed to match their canonical snapshots on feature paths + all hyperparams; "CONFIGS MATCH SNAPSHOTS" printed. Any drift (none expected) recorded with the snapshot-derived settings to use instead.</done>
</task>

<task type="auto">
  <name>Task 2: Fixed retrains (corrected smoothness, seed 42) to scratch, then evaluate on XD test</name>
  <files>results/_smoothfix/xd_base_fixed_s42/ (created), results/_smoothfix/xd_so400m_fixed_s42/ (created)</files>
  <action>
    Run on current main (which contains the corrected smoothness fix). All four commands run in the
    vcc-main conda env (per CLAUDE.md). Run them in a visible terminal, NOT a headless background
    process (per project memory feedback_no_headless). Run sequentially; each train is ~50 epochs with
    patience 10. Use the exact run names below so paths match the report and frontmatter artifacts.

    SigLIP2 Base:
      conda run -n vcc-main python src/train.py --config configs/gated_fusion_xd_siglip2.yaml --seed 42 --results-dir results/_smoothfix --run-name xd_base_fixed_s42
      conda run -n vcc-main python src/evaluate.py --run-dir results/_smoothfix/xd_base_fixed_s42 --split test

    SO400M:
      conda run -n vcc-main python src/train.py --config configs/gated_fusion_xd_so400m.yaml --seed 42 --results-dir results/_smoothfix --run-name xd_so400m_fixed_s42
      conda run -n vcc-main python src/evaluate.py --run-dir results/_smoothfix/xd_so400m_fixed_s42 --split test

    Sanity: each eval_metrics.json n_frames must be ~= 2,313,024 (matches canonical XD full length; XD
    eval is standard, no truncation). If ANY run errors (env/GPU/feature path missing — features live on
    E:\ per the configs) or n_frames deviates materially, STOP and report the failure in SUMMARY — do NOT
    fabricate numbers and do NOT proceed to Task 3 with partial/guessed values.
    (If Task 1 found config drift, substitute the snapshot-derived config/settings here.)
  </action>
  <verify>
    <automated>conda run -n vcc-main python -c "import json; b=json.load(open('results/_smoothfix/xd_base_fixed_s42/eval_metrics.json')); s=json.load(open('results/_smoothfix/xd_so400m_fixed_s42/eval_metrics.json')); assert b['split']=='test' and s['split']=='test'; assert abs(b['n_frames']-2313024)<5000, b['n_frames']; assert abs(s['n_frames']-2313024)<5000, s['n_frames']; print('BASE fixed: AP=%.4f AUC=%.4f n=%d'%(b['ap'],b['auc'],b['n_frames'])); print('SO400M fixed: AP=%.4f AUC=%.4f n=%d'%(s['ap'],s['auc'],s['n_frames']))"</automated>
  </verify>
  <done>Both fixed retrains complete; best_model.pth + eval_metrics.json exist in each scratch run dir; both evals on test split with n_frames ~= 2,313,024; fixed AP/AUC printed for both backbones. If any run errored, STOPPED and reported instead.</done>
</task>

<task type="auto">
  <name>Task 3: Write comparison report (xd_measurement.md + SUMMARY table) with verdict</name>
  <files>results/_smoothfix/xd_measurement.md</files>
  <action>
    Build the comparison table from the canonical (buggy) baselines and the Task 2 fixed evals. Pull
    canonical numbers from results/xd_gated_fusion_siglip2_s42/eval_metrics.json (AP 0.7192, AUC 0.9185)
    and results/xd_gated_fusion_so400m_s42/eval_metrics.json (AP 0.7377, AUC 0.9315); pull fixed numbers
    from the Task 2 eval_metrics.json files. Write the table to results/_smoothfix/xd_measurement.md AND
    reproduce it in the SUMMARY.

    Table columns:
      | backbone | canonical AP (buggy) | fixed AP | Delta_AP | canonical AUC | fixed AUC | Delta_AUC |
    Rows: Base, SO400M. Compute Delta = fixed - canonical (signed, in pp where helpful).

    Then report:
      1. Delta_AP for each backbone (fixed - canonical), signed.
      2. Ordering check at seed 42: is fixed_Base_AP vs fixed_SO400M_AP the SAME ordering as canonical
         (canonical at s42 is SO400M > Base)? State whether the fix preserves or flips s42 ordering.
      3. Implied 3-seed-mean ordering: if BOTH deltas are similar in sign+magnitude (systematic), the
         reported mean ordering (Base 74.70 > SO400M 73.80) likely holds. If the two deltas DIFFER
         materially between backbones, the mean ordering is AT RISK -> flag that all 3 seeds should be
         measured before trusting the mean.
      4. Context: compare each |Delta_AP| to the XD gated AP seed-std (~2.8-2.9pp).
      5. Verdict — exactly one of:
           NEGLIGIBLE: |Delta_AP| within seed noise AND systematic across both backbones AND s42 ordering
             preserved -> mean ordering safe, no XD retrain needed.
           MATERIAL: large |Delta_AP| OR ordering-flipping (s42 or implied-mean) -> XD needs full retrain
             + Table 2 re-propagation.
      Do NOT make the A/B decision and do NOT edit the paper/tables/figures. State the verdict as a
      measurement finding only.
  </action>
  <verify>
    <automated>conda run -n vcc-main python -c "import os,re; p='results/_smoothfix/xd_measurement.md'; assert os.path.exists(p); t=open(p,encoding='utf-8').read(); low=t.lower(); assert 'delta_ap' in low or 'delta ap' in low or 'd_ap' in low or 'Δ' in t, 'delta_ap missing'; assert 'so400m' in low and 'base' in low; assert 'ordering' in low; assert ('negligible' in low) ^ ('material' in low) or ('negligible' in low or 'material' in low), 'verdict missing'; assert '0.7192' in t and '0.7377' in t, 'canonical AP anchors missing'; print('REPORT OK')"</automated>
  </verify>
  <done>results/_smoothfix/xd_measurement.md exists with the comparison table (canonical 0.7192/0.7377 anchors present), per-backbone Delta_AP, s42 ordering check, implied-mean ordering analysis, seed-std context, and exactly one verdict (NEGLIGIBLE or MATERIAL). Same table reproduced in SUMMARY. No paper/canonical edits made.</done>
</task>

</tasks>

<verification>
- Task 1: configs confirmed == canonical snapshots (or snapshot settings adopted on drift).
- Task 2: both fixed evals on XD test split, n_frames ~= 2,313,024; if any run errored, STOPPED + reported.
- Task 3: report table present with canonical anchors, per-backbone Delta_AP, ordering checks, seed-std context, single verdict.
- Scope: results/_smoothfix/* is gitignored (verified: git check-ignore passes); NOT committed. Canonical
  results/xd_*, paper, tables, figures untouched. Code fix already committed at f89910b — nothing new to commit
  except orchestrator-handled docs (SUMMARY/STATE/PLAN).
</verification>

<success_criteria>
- Both XD gated contenders retrained on corrected smoothness (current main), seed 42, to scratch.
- Both fixed evals produced on XD test with full-length n_frames (~2,313,024).
- Delta_AP / Delta_AUC reported per backbone vs canonical baselines.
- s42 ordering and implied 3-seed-mean ordering analyzed; seed-std context (~2.8-2.9pp) included.
- Verdict (NEGLIGIBLE vs MATERIAL) stated as a measurement finding only — no A/B decision, no paper edits.
- No canonical/scratch artifacts committed.
</success_criteria>

<output>
Create `.planning/quick/260601-okz-measure-smoothness-fix-on-xd-gated-headl/260601-okz-SUMMARY.md` when done
(orchestrator handles the commit of SUMMARY/STATE/PLAN; do NOT commit results/_smoothfix/* or any scratch).
</output>
