---
phase: quick-260601-rww
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - configs/*.yaml  # 43 fusion configs that adopt lam_smooth: 0.0 (22 UCF + 21 XD MIL-path); the 2 xd_i3d RTFM-gate configs are intentionally NOT edited
  - scripts/retrain_lam0.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Every UCF + XD MIL-path config that previously set lam_smooth: 8.0e-4 (43 total) now sets lam_smooth: 0.0 (canonical λ=0 loss)"
    - "The 2 xd_i3d RTFM-gate configs (rtfm_i3d.yaml, rtfm_i3d_flow.yaml) STILL set lam_smooth: 8.0e-4 — untouched, because the i3d RTFM baseline is not part of the λ=0 measurement, is not being retrained (Task 2 excludes _i3d_), and is not a paper Table 1/2 number; editing without retraining would create a config≠results mismatch"
    - "Every UCF config (E:/features/ucf) has paths.snippet_boundaries_dir: E:/snippets/ucf so a fresh eval is full-length (H1)"
    - "No XD or I3D config gains a snippet_boundaries_dir key"
    - "scripts/retrain_lam0.py --dry-run lists exactly 58 canonical runs (29 UCF + 29 XD) with correct run/config-source/seed/eval-mode and excludes the 2 _i3d_ runs, WITHOUT executing any training or eval"
  artifacts:
    - path: "scripts/retrain_lam0.py"
      provides: "Resumable, backup-before-overwrite, dry-run-able λ=0 retrain orchestrator over the 58 canonical runs"
      contains: "def main"
  key_links:
    - from: "scripts/retrain_lam0.py"
      to: "src/utils/config.load_snapshot_as_config"
      via: "extract resolved config from config_snapshot.json[\"config\"]"
      pattern: "load_snapshot_as_config|config_snapshot"
    - from: "scripts/retrain_lam0.py"
      to: "src/train.py + src/evaluate.py"
      via: "subprocess.run (reuse, do not reimplement training/eval)"
      pattern: "subprocess"
---

<objective>
Stage 1 of the λ=0 (drop temporal smoothness) adoption. Three deliverables, NO training:

1. Make λ=0 the canonical loss in the 43 fusion configs that currently set `lam_smooth: 8.0e-4` (22 UCF + 21 XD MIL-path), changing the value to `0.0`. LEAVE the 2 xd_i3d RTFM-gate configs (rtfm_i3d.yaml, rtfm_i3d_flow.yaml) at `lam_smooth: 8.0e-4` — untouched.
2. Enable full-length UCF eval (H1) by adding `paths.snippet_boundaries_dir: E:/snippets/ucf` to every UCF config (the 22 whose feature paths use `E:/features/ucf`). XD and I3D configs are NOT touched for this.
3. Write `scripts/retrain_lam0.py` — a resumable, backup-before-overwrite, dry-run-able orchestrator that will (in Stage 2, user-run) retrain + re-eval all 58 canonical runs at λ=0. Dry-run it to verify the plan, but DO NOT run the actual batch.

Purpose: Prepare the codebase so the user can launch the ~58-run Stage-2 retrain batch with one command, and so the canonical configs reflect the approved λ=0 decision. The over-regularizing smoothness term hurts XD AP (SO400M 73.8→78.7%, CLIP +5.5pp, Giant +3.1pp; UCF AUC unaffected); λ=0 is the corrected canonical loss.

The 2 xd_i3d RTFM-gate configs are deliberately excluded from PART A: the i3d RTFM baseline was NOT part of the λ=0 smoothness measurement, is NOT being retrained (Task 2 enumeration excludes any dir whose name contains `_i3d_`), and is NOT a paper Table 1/2 number. Editing those configs to λ=0 without retraining would create a config≠results mismatch (config claims λ=0 but the on-disk results were trained at 8.0e-4). Leaving them at 8.0e-4 keeps config and results consistent.

Output: 43 edited config YAMLs + scripts/retrain_lam0.py + a verified dry-run transcript in the SUMMARY.

SCOPE GUARD (do not cross): This stage commits ONLY config edits + the script. It does NOT retrain, does NOT touch canonical results/ data, paper, tables, or figures, and does NOT edit src/losses/mil_loss.py (the corrected `_smoothness` simply contributes 0 when lam=0; leave the function as-is). Stage 2 (training) and Stage 3 (propagation/paper) are separate and orchestrator/user-driven.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

<interfaces>
<!-- Contracts the executor needs. Extracted from the codebase. Use directly — no exploration needed. -->

src/train.py CLI (reads lam_smooth from the config file; there is NO --lam-smooth flag — config must be edited):
  python src/train.py --config <path.yaml> [--seed N] [--results-dir DIR] [--run-name NAME]
  - --run-name overrides the auto-generated dir name (Phase 4 D-30: deterministic dirs).
  - --results-dir + --run-name together place output at <results-dir>/<run-name>, so passing
    --results-dir results --run-name <canonical-run-name> OVERWRITES the canonical run dir.

src/evaluate.py CLI:
  python src/evaluate.py --run-dir results/<run> --split test
  - Reads config_snapshot.json + best_model.pth from --run-dir, writes eval_metrics.json,
    eval_scores.npz, per_category.csv, .done (atomic, .done written last).
  - UCF full-length eval is GATED on cfg["paths"]["snippet_boundaries_dir"] (evaluate.py ~line 287):
    if set and <vid>_boundaries.json exists, n_frames = total_frames*10 (TRUE full length, H1);
    if unset, it warns once and uses the truncated snippet-grid length. XD path has no truncation.

src/utils/config.py (reuse — do NOT reimplement):
  load_snapshot_as_config(snapshot_path) -> dict   # returns the ["config"] sub-dict (resolved config)
  load_config(path) -> dict                          # loads any YAML config
  Use load_snapshot_as_config(run_dir/"config_snapshot.json") to recover the EXACT resolved config
  (incl. seed + paths + train block) that produced each canonical run.

config_snapshot.json structure (verified on results/ucf_gated_fusion_giant_s42/):
  { "config": { "dataset": "ucf"|"xd"|"xd_i3d", "seed": 42,
                "paths": { "skeleton_features", "clip_features", "splits_dir", "results_dir", ... },
                "train": { "lam_smooth": 0.0008, "lam_sparse": ..., "lr": ..., ... },
                "model": {...}, "data": {...}, "wandb": {...} }, ...other top-level keys... }
  NOTE: lam_smooth serializes as 0.0008 (numeric) in the snapshot, not "8.0e-4".

scripts/run_ablations.py — the established subprocess-orchestration reference (subprocess.run,
  .done resume probe, error log, --dry-run flag). Mirror its style; do not import it.
</interfaces>

<ground_truth>
Verified during planning (authoritative — use these exact numbers):

- 45 configs currently set `lam_smooth: 8.0e-4` (grep `lam_smooth:\s*8\.0e-4` over configs/).
  This stage edits 43 of them and INTENTIONALLY LEAVES 2 (the xd_i3d RTFM-gate configs) at 8.0e-4:
    * 22 UCF (feature path E:/features/ucf) — EDITED to 0.0: clip_only.yaml, clip_only_giant.yaml, clip_only_siglip2.yaml,
      clip_only_so400m.yaml, gated_fusion.yaml, gated_fusion_2person.yaml, gated_fusion_clip_mean.yaml,
      gated_fusion_giant.yaml, gated_fusion_giant_2person.yaml, gated_fusion_giant_clip_mean.yaml,
      gated_fusion_siglip2.yaml, gated_fusion_siglip2_2person.yaml, gated_fusion_siglip2_clip_mean.yaml,
      gated_fusion_so400m.yaml, gated_fusion_so400m_2person.yaml, gated_fusion_so400m_clip_mean.yaml,
      late_fusion.yaml, late_fusion_giant.yaml, late_fusion_siglip2.yaml, late_fusion_so400m.yaml,
      skeleton_only.yaml, _giant_smoothmeasure.yaml
    * 21 XD (feature path E:/features/xd) — EDITED to 0.0: clip_only_xd*.yaml (4), gated_fusion_xd*.yaml (12),
      late_fusion_xd*.yaml (4), skeleton_only_xd.yaml (1)
    * 2 I3D (xd_i3d dataset, i3d_features path) — NOT EDITED, remain at 8.0e-4: rtfm_i3d.yaml, rtfm_i3d_flow.yaml
  Edited total = 22 + 21 = 43. Untouched (remain 8.0e-4) = 2.

- `snippet_boundaries_dir` is currently present in ONLY ONE config: `_giant_smoothmeasure.yaml`
  (the others lack it). So 21 UCF configs need the key ADDED; _giant_smoothmeasure.yaml already
  has it (skip-if-present). XD/I3D configs must NOT get it.

- `skeleton_only.yaml` and `skeleton_only_xd.yaml` have a trailing comment on the lam_smooth line:
  `lam_smooth: 8.0e-4      # D-03`. PRESERVE that comment (and any other trailing comment) — only the
  numeric value changes to 0.0.

- 58 canonical result dirs (each has config_snapshot.json + eval_metrics.json), name-prefix split:
  29 `ucf_*` + 29 `xd_*` (non-i3d). The 2 excluded are `xd_i3d_rtfm_i3d_s42`, `xd_i3d_rtfm_i3d_flow_s42`
  (any dir whose name contains `_i3d_`). This is why the 2 rtfm_i3d configs are also left unedited in
  PART A — they are not in the retrain set, so editing their configs would desync config from results.
</ground_truth>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Adopt λ=0 in the 43 fusion configs (UCF + XD MIL-path) + add full-length UCF eval boundaries to the 22 UCF configs; LEAVE the 2 xd_i3d RTFM-gate configs at 8.0e-4</name>
  <files>
    configs/clip_only.yaml, configs/clip_only_giant.yaml, configs/clip_only_siglip2.yaml, configs/clip_only_so400m.yaml,
    configs/gated_fusion.yaml, configs/gated_fusion_2person.yaml, configs/gated_fusion_clip_mean.yaml,
    configs/gated_fusion_giant.yaml, configs/gated_fusion_giant_2person.yaml, configs/gated_fusion_giant_clip_mean.yaml,
    configs/gated_fusion_siglip2.yaml, configs/gated_fusion_siglip2_2person.yaml, configs/gated_fusion_siglip2_clip_mean.yaml,
    configs/gated_fusion_so400m.yaml, configs/gated_fusion_so400m_2person.yaml, configs/gated_fusion_so400m_clip_mean.yaml,
    configs/late_fusion.yaml, configs/late_fusion_giant.yaml, configs/late_fusion_siglip2.yaml, configs/late_fusion_so400m.yaml,
    configs/skeleton_only.yaml, configs/_giant_smoothmeasure.yaml,
    configs/clip_only_xd.yaml, configs/clip_only_xd_giant.yaml, configs/clip_only_xd_siglip2.yaml, configs/clip_only_xd_so400m.yaml,
    configs/gated_fusion_xd.yaml, configs/gated_fusion_xd_2person.yaml, configs/gated_fusion_xd_clip_mean.yaml,
    configs/gated_fusion_xd_giant.yaml, configs/gated_fusion_xd_giant_2person.yaml, configs/gated_fusion_xd_giant_clip_mean.yaml,
    configs/gated_fusion_xd_siglip2.yaml, configs/gated_fusion_xd_siglip2_2person.yaml, configs/gated_fusion_xd_siglip2_clip_mean.yaml,
    configs/gated_fusion_xd_so400m.yaml, configs/gated_fusion_xd_so400m_2person.yaml, configs/gated_fusion_xd_so400m_clip_mean.yaml,
    configs/late_fusion_xd.yaml, configs/late_fusion_xd_giant.yaml, configs/late_fusion_xd_siglip2.yaml, configs/late_fusion_xd_so400m.yaml,
    configs/skeleton_only_xd.yaml
  </files>
  <action>
    Edit each of the 43 fusion configs listed in &lt;files&gt; (these are exactly the UCF + XD MIL-path configs whose `train:` block contains `lam_smooth: 8.0e-4`, per the verified &lt;ground_truth&gt; list — 22 UCF + 21 XD). DO NOT edit configs/rtfm_i3d.yaml or configs/rtfm_i3d_flow.yaml — they are intentionally left at `lam_smooth: 8.0e-4` (the i3d RTFM baseline is not part of the λ=0 measurement, is not in the Stage-2 retrain set, and is not a paper Table 1/2 number; editing without retraining would create a config≠results mismatch).

    PART A — λ=0 canonical loss (the 43 fusion configs ONLY): On the `lam_smooth:` line, change the numeric value from `8.0e-4` to `0.0`. PRESERVE any trailing inline comment exactly (skeleton_only.yaml and skeleton_only_xd.yaml end the line with `# D-03` — keep that comment verbatim; result line: `  lam_smooth: 0.0      # D-03`). Do NOT alter `lam_sparse`, `lr`, indentation, or any other line. Use targeted line edits (Edit tool), not a blanket file rewrite. Leave rtfm_i3d.yaml and rtfm_i3d_flow.yaml completely untouched.

    PART B — full-length UCF eval (H1) for the 22 UCF configs ONLY (the configs/ files above whose `paths:` block uses `E:/features/ucf`): under the `paths:` block, add a new line `  snippet_boundaries_dir: "E:/snippets/ucf"` (same 2-space indentation as the sibling `splits_dir`/`results_dir` keys). SKIP this addition for `_giant_smoothmeasure.yaml` — it ALREADY has the key (do not duplicate it). Do NOT add this key to any XD config (E:/features/xd) or either I3D config (rtfm_i3d.yaml, rtfm_i3d_flow.yaml).

    Rationale traceability: λ=0 is the user-approved decision (drop temporal smoothness; over-regularizes and hurts XD AP). The 2 xd_i3d RTFM-gate configs are deliberately excluded to keep config and on-disk results consistent (they were trained at 8.0e-4 and are not being retrained). snippet_boundaries_dir gates evaluate.py's H1 full-length frame grid (evaluate.py ~line 287) so the Stage-2 λ=0 UCF re-eval is full-length rather than snippet-grid-truncated.

    Do NOT touch src/losses/mil_loss.py — the corrected `_smoothness` contributes 0 when lam=0; leaving it intact is intentional.

    COMMIT after edits with message exactly:
    "feat(loss): adopt lam_smooth=0 (drop temporal smoothness) in 43 fusion configs + enable full-length UCF eval (xd_i3d RTFM-gate configs left at 8.0e-4)"
  </action>
  <verify>
    <automated>cd /d D:\ViolenceCC &amp;&amp; python -c "import pathlib,re,sys; d=pathlib.Path('configs'); rem=[f.name for f in d.glob('*.yaml') if re.search(r'lam_smooth:\s*8\.0e-4', f.read_text(encoding='utf-8'))]; zero=[f.name for f in d.glob('*.yaml') if re.search(r'lam_smooth:\s*0\.0(\s|$|#)', f.read_text(encoding='utf-8'))]; ucf=[f.name for f in d.glob('*.yaml') if 'E:/features/ucf' in f.read_text(encoding='utf-8')]; ucf_b=[n for n in ucf if 'snippet_boundaries_dir: \"E:/snippets/ucf\"' in (d/n).read_text(encoding='utf-8')]; xd_b=[f.name for f in d.glob('*.yaml') if 'E:/features/xd' in f.read_text(encoding='utf-8') and 'snippet_boundaries_dir' in f.read_text(encoding='utf-8')]; i3d_8e4=[n for n in ('rtfm_i3d.yaml','rtfm_i3d_flow.yaml') if re.search(r'lam_smooth:\s*8\.0e-4', (d/n).read_text(encoding='utf-8'))]; d03=[(d/n).read_text(encoding='utf-8') for n in ('skeleton_only.yaml','skeleton_only_xd.yaml')]; ok = (sorted(rem)==sorted(['rtfm_i3d.yaml','rtfm_i3d_flow.yaml'])) and (len(zero)==43) and (len(ucf)==22) and (len(ucf_b)==22) and (len(xd_b)==0) and (len(i3d_8e4)==2) and all('# D-03' in t for t in d03); print('remaining_8e4=%s zero=%d ucf=%d ucf_with_bound=%d xd_with_bound=%d i3d_still_8e4=%d'%(sorted(rem),len(zero),len(ucf),len(ucf_b),len(xd_b),len(i3d_8e4))); sys.exit(0 if ok else 1)"</automated>
  </verify>
  <done>
    Exactly 43 fusion configs now set `lam_smooth: 0.0`; the only 2 configs that still retain `lam_smooth: 8.0e-4` are rtfm_i3d.yaml and rtfm_i3d_flow.yaml (intentionally untouched); all 22 UCF configs contain `snippet_boundaries_dir: "E:/snippets/ucf"`; zero XD/I3D configs contain that key; the `# D-03` comments on skeleton_only{,_xd}.yaml are preserved; commit made with the exact message.
  </done>
</task>

<task type="auto">
  <name>Task 2: Write scripts/retrain_lam0.py (resumable, backup-before-overwrite, dry-run-able)</name>
  <files>scripts/retrain_lam0.py</files>
  <action>
    Create `scripts/retrain_lam0.py` — a batch orchestrator that prepares and (in Stage 2) executes the λ=0 retrain + full-length re-eval of every canonical run. Reuse src/train.py and src/evaluate.py via subprocess (DO NOT reimplement training or eval). Mirror the style of scripts/run_ablations.py (argparse, subprocess.run, resume probe, error log, --dry-run). Run target environment is vcc-main.

    ENUMERATION: scan `results/` for directories that contain BOTH `config_snapshot.json` AND `eval_metrics.json`, EXCLUDING any whose name contains `_i3d_`. This yields the 58 canonical runs (29 `ucf_*` + 29 `xd_*`). Sort the list deterministically (e.g. sorted by dir name) so dry-run output is stable.

    PER-RUN PLAN (compute for every run, used by both dry-run and real run):
      - Load the exact resolved config via src.utils.config.load_snapshot_as_config(run_dir/"config_snapshot.json").
      - seed := config["seed"]; dataset := config.get("dataset","ucf"); variant := config["model"]["variant"]; backbone := infer from config["paths"]["clip_features"] tail (e.g. clip / siglip2 / siglip2_so400m / siglip2_giant / *_mean) for the dry-run label only.
      - Apply λ=0: set config["train"]["lam_smooth"] = 0.0.
      - eval-mode: if dataset == "ucf" (UCF run), ensure config["paths"]["snippet_boundaries_dir"] = "E:/snippets/ucf" → eval-mode label "UCF-full-length"; else (xd) leave paths untouched → eval-mode label "XD-standard".
      - run_name := the canonical results dir name (so the overwrite targets the same dir).

    REAL-RUN EXECUTION (only when NOT --dry-run), per run:
      1. BACKUP-BEFORE-OVERWRITE: before the FIRST overwrite of a run dir, for each of
         {eval_metrics.json, eval_scores.npz, best_model.pth, train_log.csv, config_snapshot.json}
         that exists in the dir, copy it to "<name>.pre_lam0.bak" — but ONLY if that .bak does not already
         exist (never clobber an existing backup; results/ is gitignored and NOT git-revertible, so the .bak
         IS the safety net). Use shutil.copy2.
      2. Write the λ=0-modified resolved config to a temp YAML (tempfile + yaml.safe_dump; UTF-8). The temp
         file is the only thing handed to train.py since train.py reads lam_smooth from the config (no CLI flag).
      3. Train (overwrites the canonical dir):
         python src/train.py --config <temp.yaml> --seed <seed> --results-dir results --run-name <canonical run name>
      4. Eval (full-length for UCF via the boundaries key now in the fresh snapshot):
         python src/evaluate.py --run-dir results/<run> --split test
      5. Mark done: append the run name to results/_lam0_done.txt (create if absent). Remove the temp YAML.
      Invoke train/eval with sys.executable (the active interpreter) so the script runs inside whatever
      env launched it (vcc-main in Stage 2). Pass cwd=PROJECT_ROOT. Capture returncode.

    RESUMABILITY: skip a run if it is already done. Detect "done" by EITHER (a) its name is listed in
    results/_lam0_done.txt, OR (b) results/<run>/eval_metrics.json's embedded config/snapshot shows lam_smooth==0.0
    AND a *.pre_lam0.bak exists in the dir. The _lam0_done.txt log is the primary marker; (b) is a fallback so a
    run completed before the log existed is still skipped. Print "[skip] <run> (already λ=0)" for skipped runs.

    ROBUSTNESS: wrap each run's train+eval in try/except and on ANY failure (non-zero exit or exception) append a
    line to results/retrain_lam0_errors.log (run name + step + returncode/exception) and CONTINUE to the next run
    (do not abort the batch). At the end, print a summary: N attempted, N succeeded, N skipped, N failed, and list
    failed run names. Note: `conda run python -c "<multiline>"` is broken on this Windows setup, but this script is
    a .py file invoked directly, which is fine.

    --dry-run FLAG: print the full plan — one line per run with: run-name, config-source path, seed, variant,
    backbone, eval-mode (UCF-full-length | XD-standard) — then print the total count and EXIT(0) WITHOUT loading
    torch, without backups, without training, and without writing any results artifact. Default (no flag) runs the
    batch. The dry-run path must NOT import torch or call train.py/evaluate.py.

    Keep it a single self-contained script (~150-220 lines). Add a module docstring stating: Stage 1 prepares the
    plan; Stage 2 (user-run, no --dry-run) executes the batch; the script never touches paper/tables/figures.
  </action>
  <verify>
    <automated>cd /d D:\ViolenceCC &amp;&amp; python -c "import ast,sys; src=open('scripts/retrain_lam0.py',encoding='utf-8').read(); t=ast.parse(src); names={n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef)}; need=['subprocess','load_snapshot_as_config','_i3d_','pre_lam0.bak','snippet_boundaries_dir','dry-run','_lam0_done.txt']; miss=[s for s in need if s not in src]; print('funcs=',sorted(names)); print('missing_tokens=',miss); sys.exit(0 if ('main' in names and not miss) else 1)"</automated>
  </verify>
  <done>
    scripts/retrain_lam0.py parses (valid Python), defines main(), references src.utils.config.load_snapshot_as_config, excludes `_i3d_` runs, implements *.pre_lam0.bak backup-before-overwrite, sets snippet_boundaries_dir for UCF runs, writes/reads results/_lam0_done.txt for resume, logs failures to results/retrain_lam0_errors.log and continues, and supports a --dry-run flag that exits without training.
  </done>
</task>

<task type="auto">
  <name>Task 3: Dry-run verification (NO training executed) + commit the script</name>
  <files>scripts/retrain_lam0.py</files>
  <action>
    Run the dry-run and confirm the plan, then commit the script.

    1. Execute: `conda run -n vcc-main python scripts/retrain_lam0.py --dry-run`
       (If `conda run` produces a cp950/UnicodeEncodeError on tqdm-style output per the known Windows issue, fall
       back to the direct interpreter `C:/Anaconda/envs/vcc-main/python.exe scripts/retrain_lam0.py --dry-run` —
       the dry-run path does not import torch, so either works.)
    2. Confirm the output:
       - Lists exactly 58 runs (29 ucf_*, 29 xd_*).
       - Each line shows the correct run-name, config-source, seed (42), variant, backbone, and eval-mode.
       - UCF runs show eval-mode "UCF-full-length" (boundaries set); XD runs show "XD-standard".
       - The 2 `_i3d_` runs (xd_i3d_rtfm_i3d_s42, xd_i3d_rtfm_i3d_flow_s42) are NOT listed (excluded).
       - The script exits 0 and creates NO new results artifact and runs NO training (verify by confirming
         results/_lam0_done.txt and results/retrain_lam0_errors.log were NOT created by the dry-run, and no run dir
         gained a *.pre_lam0.bak).
    3. Paste the FULL dry-run stdout into the SUMMARY (this is the evidence of correctness).
    4. DO NOT run the batch (no `python scripts/retrain_lam0.py` without --dry-run). Stage 2 is user-run.
    5. COMMIT scripts/retrain_lam0.py with message exactly:
       "feat: retrain_lam0.py — resumable λ=0 retrain of all canonical runs (dry-run verified)"
  </action>
  <verify>
    <automated>cd /d D:\ViolenceCC &amp;&amp; python scripts/retrain_lam0.py --dry-run > .tmp_dryrun.txt 2>&1 &amp;&amp; python -c "import sys; t=open('.tmp_dryrun.txt',encoding='utf-8',errors='replace').read(); import re; ucf=len(re.findall(r'(?m)^.*\bucf_', t)); xd=len(re.findall(r'(?m)^.*\bxd_(?!i3d)', t)); has_full='UCF-full-length' in t; has_std='XD-standard' in t; no_i3d=('_i3d_' not in t); import os; no_done=not os.path.exists('results/_lam0_done.txt'); print('ucf_lines~=%d xd_lines~=%d full=%s std=%s no_i3d=%s no_done_log=%s'%(ucf,xd,has_full,has_std,no_i3d,no_done)); sys.exit(0 if (has_full and has_std and no_i3d and ('58' in t)) else 1)"</automated>
  </verify>
  <done>
    Dry-run lists 58 runs with correct (run, config, seed, eval-mode) mapping; UCF runs flagged UCF-full-length and XD runs flagged XD-standard; `_i3d_` runs excluded; no training executed and no results artifact written by the dry-run; full dry-run output pasted into SUMMARY; scripts/retrain_lam0.py committed with the exact message.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| config YAML → train.py/evaluate.py | λ=0 + boundaries values flow from edited configs into Stage-2 training/eval; a wrong value silently produces wrong canonical numbers |
| script → canonical results/ dirs | retrain_lam0.py (in Stage 2) OVERWRITES irreplaceable, gitignored run artifacts |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-rww-01 | Tampering | retrain_lam0.py overwriting canonical run dirs | mitigate | backup-before-overwrite to *.pre_lam0.bak (never clobber existing .bak) before the first train of each run; results/ is gitignored so this is the only recovery path |
| T-rww-02 | Tampering | This stage accidentally running training/eval | mitigate | Stage 1 only ever invokes the script with --dry-run; dry-run path imports no torch, writes no artifact, exits before any subprocess; Task 3 verify asserts no _lam0_done.txt / .bak created |
| T-rww-03 | Information disclosure | snippet_boundaries_dir added to wrong dataset (XD/I3D) → silently wrong eval grid | mitigate | Task 1 PART B restricted to E:/features/ucf configs only; Task 1 verify asserts xd_with_bound==0 |
| T-rww-04 | Tampering | I3D runs (separate RTFM baseline) pulled into the retrain | mitigate | enumeration excludes any dir name containing `_i3d_`; Task 1 leaves the 2 rtfm_i3d configs at 8.0e-4 (config matches the un-retrained results); Task 3 verify asserts `_i3d_` absent from dry-run output |
| T-rww-05 | Tampering | config≠results mismatch from editing un-retrained i3d configs | mitigate | Task 1 explicitly EXCLUDES rtfm_i3d.yaml + rtfm_i3d_flow.yaml from PART A and verify asserts they STILL read 8.0e-4 (i3d_still_8e4==2), so their config stays consistent with the on-disk 8.0e-4 results |
| T-rww-SC | Tampering | npm/pip/cargo installs | accept | No new packages installed this stage; PyYAML/numpy already in vcc-main per config_snapshot packages list; no install tasks → legitimacy gate N/A |
</threat_model>

<verification>
- Task 1 verify script: the only 2 configs that retain 8.0e-4 are rtfm_i3d.yaml + rtfm_i3d_flow.yaml; exactly 43 fusion configs at 0.0; 22 UCF all carry the boundaries key; 0 XD/I3D carry it; D-03 comments preserved.
- Task 2 verify script: retrain_lam0.py is valid Python with main() and all required behaviors present as tokens.
- Task 3 verify script: dry-run prints 58 with UCF-full-length / XD-standard labels, excludes `_i3d_`, and creates no results artifact.
- Manual cross-check in SUMMARY: pasted dry-run transcript shows 29 ucf_* + 29 xd_* with seed 42 and correct backbone labels.
</verification>

<success_criteria>
- The 43 fusion configs set λ=0; the 2 xd_i3d RTFM-gate configs remain at 8.0e-4 (config matches un-retrained results); the 22 UCF configs enable full-length eval; XD/I3D untouched for boundaries.
- scripts/retrain_lam0.py exists, is resumable, backs up before overwrite, and dry-runs cleanly over 58 canonical runs (excluding the 2 _i3d_ runs).
- Two commits made (config edits; then the script — or one combined commit per the second message), with NO training run, NO results/ data touched, NO paper/table/figure changes.
- SUMMARY contains the verbatim dry-run transcript.
</success_criteria>

<output>
Create `.planning/quick/260601-rww-stage-1-of-lambda-0-adoption-set-lam-smo/260601-rww-SUMMARY.md` when done.
Hand the user the Stage-2 launch command (run in a VISIBLE terminal per the no-headless rule):
  `conda run -n vcc-main python scripts/retrain_lam0.py`   (NO --dry-run — this trains ~58 runs)
Note for the orchestrator: Stage 3 (propagation into canonical artifacts / tables / figures / paper) happens AFTER the user confirms the Stage-2 batch completed.
</output>
