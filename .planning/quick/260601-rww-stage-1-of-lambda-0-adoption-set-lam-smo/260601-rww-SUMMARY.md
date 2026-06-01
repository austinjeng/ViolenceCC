---
phase: quick-260601-rww
plan: 01
subsystem: training-config / orchestration
tags: [lam-smooth, lambda-zero, temporal-smoothness, full-length-eval, retrain-orchestrator]
dependency_graph:
  requires:
    - "src/train.py (--config/--seed/--results-dir/--run-name CLI)"
    - "src/evaluate.py (--run-dir/--split CLI; H1 full-length gated on paths.snippet_boundaries_dir)"
    - "src/utils/config.load_snapshot_as_config"
  provides:
    - "43 fusion configs at lam_smooth=0.0 (canonical λ=0 loss)"
    - "22 UCF configs enable full-length eval via paths.snippet_boundaries_dir"
    - "scripts/retrain_lam0.py — resumable, backup-before-overwrite, dry-run-able 58-run retrain orchestrator"
  affects:
    - "Stage 2 (user-run retrain batch) and Stage 3 (paper/table/figure propagation)"
tech_stack:
  added: []
  patterns:
    - "subprocess orchestration mirroring scripts/run_ablations.py"
    - "standalone module load (importlib spec_from_file_location) to keep --dry-run torch-free"
key_files:
  created:
    - scripts/retrain_lam0.py
  modified:
    - "configs/*.yaml (43 fusion configs)"
decisions:
  - "Load src/utils/config.py by file path (importlib) instead of `from src.utils.config import` — the src.utils package __init__ eagerly imports torch via seed.py, which would break the no-torch-in-dry-run guarantee (T-rww-02)"
  - "Commit _giant_smoothmeasure.yaml (previously untracked) as part of the 43-config λ=0 set"
metrics:
  duration: ~9min
  completed: 2026-06-01
---

# Quick Task 260601-rww: Stage 1 of λ=0 Adoption Summary

Made λ=0 (drop temporal smoothness) the canonical loss in the 43 UCF+XD MIL-path fusion configs, enabled full-length UCF eval (H1) in the 22 UCF configs, and added `scripts/retrain_lam0.py` — a resumable, backup-before-overwrite, dry-run-verified orchestrator for the Stage-2 retrain of all 58 canonical runs. **No training run; no canonical results/ data, paper, tables, or figures touched.**

## What Was Done

### Task 1 — Config edits (commit `b8f56a2`)

Verified counts (Task 1 automated verify **PASSED**):

| Check | Expected | Actual |
|-------|----------|--------|
| Fusion configs now at `lam_smooth: 0.0` | 43 | **43** |
| Configs still at `lam_smooth: 8.0e-4` (i3d only) | `rtfm_i3d.yaml`, `rtfm_i3d_flow.yaml` | **exactly those 2** |
| UCF configs (`E:/features/ucf`) | 22 | **22** |
| UCF configs carrying `snippet_boundaries_dir: "E:/snippets/ucf"` | 22 | **22** (21 added + `_giant_smoothmeasure.yaml` already had it) |
| XD/I3D configs carrying `snippet_boundaries_dir` | 0 | **0** |
| `# D-03` trailing comments preserved (`skeleton_only{,_xd}.yaml`) | yes | **yes** |

- **PART A:** `lam_smooth: 8.0e-4 → 0.0` on 43 configs (22 UCF + 21 XD MIL-path). Trailing inline comments preserved verbatim (e.g. `lam_smooth: 0.0      # D-03`). `lam_sparse`, `lr`, indentation untouched.
- **PART B:** Added `snippet_boundaries_dir: "E:/snippets/ucf"` under `paths:` (after `results_dir`) to the 21 UCF configs that lacked it; skipped `_giant_smoothmeasure.yaml` (already present). No XD/I3D config touched.
- **Intentionally left at 8.0e-4:** `configs/rtfm_i3d.yaml`, `configs/rtfm_i3d_flow.yaml` (the i3d RTFM baseline is not in the Stage-2 retrain set and is not a paper Table 1/2 number; editing without retraining would desync config from on-disk results — T-rww-05).
- `src/losses/mil_loss.py` untouched (the corrected `_smoothness` contributes 0 when lam=0).
- Note: `_giant_smoothmeasure.yaml` was previously untracked in git; it is one of the 43 λ=0 configs (plan Task 1 `<files>`) and was added in this commit.

### Task 2 — `scripts/retrain_lam0.py` (commit `9fb04fa`)

Task 2 automated verify **PASSED** (valid Python, `main()` defined, all required tokens present). The script:

- Enumerates `results/` dirs with **both** `config_snapshot.json` + `eval_metrics.json`, **excluding** any name containing `_i3d_` → 58 runs (29 `ucf_*` + 29 `xd_*`), sorted deterministically.
- Per run: reuses `src/utils/config.load_snapshot_as_config` to recover the exact resolved config, sets `train.lam_smooth = 0.0`, and for UCF runs sets `paths.snippet_boundaries_dir = E:/snippets/ucf` (full-length H1 eval).
- **Real-run (Stage 2):** backup-before-overwrite of `{eval_metrics.json, eval_scores.npz, best_model.pth, train_log.csv, config_snapshot.json}` to `*.pre_lam0.bak` (only if `.bak` absent — never clobbers), writes a temp YAML, runs `src/train.py --config <tmp> --seed <seed> --results-dir results --run-name <canonical>`, then `src/evaluate.py --run-dir results/<run> --split test`, appends to `results/_lam0_done.txt`.
- **Resumable:** skips runs listed in `results/_lam0_done.txt` (primary) or where the on-disk snapshot already shows `lam_smooth==0.0` + a `.pre_lam0.bak` exists (fallback).
- **Robust:** per-run failures logged to `results/retrain_lam0_errors.log`; the batch continues and prints an attempted/succeeded/skipped/failed summary.
- **`--dry-run`** prints the plan and exits without importing torch / writing any artifact.

### Task 3 — Dry-run verification (NO training; commit `9fb04fa`)

Task 3 automated verify **PASSED**: 58 runs, `UCF-full-length` + `XD-standard` labels present, no `_i3d_` runs listed, no `results/_lam0_done.txt` created.

Confirmed by hand: 29 `ucf_*` (all `UCF-full-length`), 29 `xd_*` (all `XD-standard`), seeds 42/123/2024 captured, the 2 `_i3d_` runs (`xd_i3d_rtfm_i3d_s42`, `xd_i3d_rtfm_i3d_flow_s42`) excluded. The dry-run created **no** `_lam0_done.txt`, **no** `retrain_lam0_errors.log`, and **zero** `*.pre_lam0.bak` files (T-rww-02 satisfied). Ran cleanly via `conda run -n vcc-main` (no cp950 error) and also exits 0 under base `python` (which has a broken torch DLL) — proving the dry-run path imports no torch.

#### Full dry-run transcript (`conda run -n vcc-main python scripts/retrain_lam0.py --dry-run`)

```
lambda=0 retrain plan: 58 canonical runs (i3d RTFM-gate runs excluded). NO training in --dry-run.

[ 1/58] run=ucf_clip_only_giant_s42                    config=D:/ViolenceCC/results/ucf_clip_only_giant_s42/config_snapshot.json seed=42 variant=clip_only      backbone=siglip2-giant      eval-mode=UCF-full-length
[ 2/58] run=ucf_clip_only_s42                          config=D:/ViolenceCC/results/ucf_clip_only_s42/config_snapshot.json seed=42 variant=clip_only      backbone=clip-vit-b-16      eval-mode=UCF-full-length
[ 3/58] run=ucf_clip_only_siglip2_s42                  config=D:/ViolenceCC/results/ucf_clip_only_siglip2_s42/config_snapshot.json seed=42 variant=clip_only      backbone=siglip2-vit-b-16   eval-mode=UCF-full-length
[ 4/58] run=ucf_clip_only_so400m_s42                   config=D:/ViolenceCC/results/ucf_clip_only_so400m_s42/config_snapshot.json seed=42 variant=clip_only      backbone=siglip2-so400m     eval-mode=UCF-full-length
[ 5/58] run=ucf_gated_fusion_2person_s42               config=D:/ViolenceCC/results/ucf_gated_fusion_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=UCF-full-length
[ 6/58] run=ucf_gated_fusion_clip_mean_s42             config=D:/ViolenceCC/results/ucf_gated_fusion_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=clip-vit-b-16-mean eval-mode=UCF-full-length
[ 7/58] run=ucf_gated_fusion_giant_2person_s42         config=D:/ViolenceCC/results/ucf_gated_fusion_giant_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-giant      eval-mode=UCF-full-length
[ 8/58] run=ucf_gated_fusion_giant_clip_mean_s42       config=D:/ViolenceCC/results/ucf_gated_fusion_giant_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2_giant_mean eval-mode=UCF-full-length
[ 9/58] run=ucf_gated_fusion_giant_s123                config=D:/ViolenceCC/results/ucf_gated_fusion_giant_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=siglip2-giant      eval-mode=UCF-full-length
[10/58] run=ucf_gated_fusion_giant_s2024               config=D:/ViolenceCC/results/ucf_gated_fusion_giant_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=siglip2-giant      eval-mode=UCF-full-length
[11/58] run=ucf_gated_fusion_giant_s42                 config=D:/ViolenceCC/results/ucf_gated_fusion_giant_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-giant      eval-mode=UCF-full-length
[12/58] run=ucf_gated_fusion_s123                      config=D:/ViolenceCC/results/ucf_gated_fusion_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=UCF-full-length
[13/58] run=ucf_gated_fusion_s2024                     config=D:/ViolenceCC/results/ucf_gated_fusion_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=UCF-full-length
[14/58] run=ucf_gated_fusion_s42                       config=D:/ViolenceCC/results/ucf_gated_fusion_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=UCF-full-length
[15/58] run=ucf_gated_fusion_siglip2_2person_s42       config=D:/ViolenceCC/results/ucf_gated_fusion_siglip2_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=UCF-full-length
[16/58] run=ucf_gated_fusion_siglip2_clip_mean_s42     config=D:/ViolenceCC/results/ucf_gated_fusion_siglip2_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2_mean       eval-mode=UCF-full-length
[17/58] run=ucf_gated_fusion_siglip2_s123              config=D:/ViolenceCC/results/ucf_gated_fusion_siglip2_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=UCF-full-length
[18/58] run=ucf_gated_fusion_siglip2_s2024             config=D:/ViolenceCC/results/ucf_gated_fusion_siglip2_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=UCF-full-length
[19/58] run=ucf_gated_fusion_siglip2_s42               config=D:/ViolenceCC/results/ucf_gated_fusion_siglip2_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=UCF-full-length
[20/58] run=ucf_gated_fusion_so400m_2person_s42        config=D:/ViolenceCC/results/ucf_gated_fusion_so400m_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=UCF-full-length
[21/58] run=ucf_gated_fusion_so400m_clip_mean_s42      config=D:/ViolenceCC/results/ucf_gated_fusion_so400m_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2_so400m_mean eval-mode=UCF-full-length
[22/58] run=ucf_gated_fusion_so400m_s123               config=D:/ViolenceCC/results/ucf_gated_fusion_so400m_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=UCF-full-length
[23/58] run=ucf_gated_fusion_so400m_s2024              config=D:/ViolenceCC/results/ucf_gated_fusion_so400m_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=UCF-full-length
[24/58] run=ucf_gated_fusion_so400m_s42                config=D:/ViolenceCC/results/ucf_gated_fusion_so400m_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=UCF-full-length
[25/58] run=ucf_late_fusion_giant_s42                  config=D:/ViolenceCC/results/ucf_late_fusion_giant_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=siglip2-giant      eval-mode=UCF-full-length
[26/58] run=ucf_late_fusion_s42                        config=D:/ViolenceCC/results/ucf_late_fusion_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=clip-vit-b-16      eval-mode=UCF-full-length
[27/58] run=ucf_late_fusion_siglip2_s42                config=D:/ViolenceCC/results/ucf_late_fusion_siglip2_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=siglip2-vit-b-16   eval-mode=UCF-full-length
[28/58] run=ucf_late_fusion_so400m_s42                 config=D:/ViolenceCC/results/ucf_late_fusion_so400m_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=siglip2-so400m     eval-mode=UCF-full-length
[29/58] run=ucf_skeleton_only_s42                      config=D:/ViolenceCC/results/ucf_skeleton_only_s42/config_snapshot.json seed=42 variant=skeleton_only  backbone=n/a(skeleton)      eval-mode=UCF-full-length
[30/58] run=xd_clip_only_giant_s42                     config=D:/ViolenceCC/results/xd_clip_only_giant_s42/config_snapshot.json seed=42 variant=clip_only      backbone=siglip2-giant      eval-mode=XD-standard
[31/58] run=xd_clip_only_s42                           config=D:/ViolenceCC/results/xd_clip_only_s42/config_snapshot.json seed=42 variant=clip_only      backbone=clip-vit-b-16      eval-mode=XD-standard
[32/58] run=xd_clip_only_siglip2_s42                   config=D:/ViolenceCC/results/xd_clip_only_siglip2_s42/config_snapshot.json seed=42 variant=clip_only      backbone=siglip2-vit-b-16   eval-mode=XD-standard
[33/58] run=xd_clip_only_so400m_s42                    config=D:/ViolenceCC/results/xd_clip_only_so400m_s42/config_snapshot.json seed=42 variant=clip_only      backbone=siglip2-so400m     eval-mode=XD-standard
[34/58] run=xd_gated_fusion_2person_s42                config=D:/ViolenceCC/results/xd_gated_fusion_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=XD-standard
[35/58] run=xd_gated_fusion_clip_mean_s42              config=D:/ViolenceCC/results/xd_gated_fusion_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=clip-vit-b-16-mean eval-mode=XD-standard
[36/58] run=xd_gated_fusion_giant_2person_s42          config=D:/ViolenceCC/results/xd_gated_fusion_giant_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-giant      eval-mode=XD-standard
[37/58] run=xd_gated_fusion_giant_clip_mean_s42        config=D:/ViolenceCC/results/xd_gated_fusion_giant_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2_giant_mean eval-mode=XD-standard
[38/58] run=xd_gated_fusion_giant_s123                 config=D:/ViolenceCC/results/xd_gated_fusion_giant_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=siglip2-giant      eval-mode=XD-standard
[39/58] run=xd_gated_fusion_giant_s2024               config=D:/ViolenceCC/results/xd_gated_fusion_giant_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=siglip2-giant      eval-mode=XD-standard
[40/58] run=xd_gated_fusion_giant_s42                  config=D:/ViolenceCC/results/xd_gated_fusion_giant_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-giant      eval-mode=XD-standard
[41/58] run=xd_gated_fusion_s123                       config=D:/ViolenceCC/results/xd_gated_fusion_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=XD-standard
[42/58] run=xd_gated_fusion_s2024                      config=D:/ViolenceCC/results/xd_gated_fusion_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=XD-standard
[43/58] run=xd_gated_fusion_s42                        config=D:/ViolenceCC/results/xd_gated_fusion_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=clip-vit-b-16      eval-mode=XD-standard
[44/58] run=xd_gated_fusion_siglip2_2person_s42        config=D:/ViolenceCC/results/xd_gated_fusion_siglip2_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=XD-standard
[45/58] run=xd_gated_fusion_siglip2_clip_mean_s42      config=D:/ViolenceCC/results/xd_gated_fusion_siglip2_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2_mean       eval-mode=XD-standard
[46/58] run=xd_gated_fusion_siglip2_s123               config=D:/ViolenceCC/results/xd_gated_fusion_siglip2_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=XD-standard
[47/58] run=xd_gated_fusion_siglip2_s2024              config=D:/ViolenceCC/results/xd_gated_fusion_siglip2_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=XD-standard
[48/58] run=xd_gated_fusion_siglip2_s42                config=D:/ViolenceCC/results/xd_gated_fusion_siglip2_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-vit-b-16   eval-mode=XD-standard
[49/58] run=xd_gated_fusion_so400m_2person_s42         config=D:/ViolenceCC/results/xd_gated_fusion_so400m_2person_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=XD-standard
[50/58] run=xd_gated_fusion_so400m_clip_mean_s42       config=D:/ViolenceCC/results/xd_gated_fusion_so400m_clip_mean_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2_so400m_mean eval-mode=XD-standard
[51/58] run=xd_gated_fusion_so400m_s123                config=D:/ViolenceCC/results/xd_gated_fusion_so400m_s123/config_snapshot.json seed=123 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=XD-standard
[52/58] run=xd_gated_fusion_so400m_s2024               config=D:/ViolenceCC/results/xd_gated_fusion_so400m_s2024/config_snapshot.json seed=2024 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=XD-standard
[53/58] run=xd_gated_fusion_so400m_s42                 config=D:/ViolenceCC/results/xd_gated_fusion_so400m_s42/config_snapshot.json seed=42 variant=gated_fusion   backbone=siglip2-so400m     eval-mode=XD-standard
[54/58] run=xd_late_fusion_giant_s42                   config=D:/ViolenceCC/results/xd_late_fusion_giant_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=siglip2-giant      eval-mode=XD-standard
[55/58] run=xd_late_fusion_s42                         config=D:/ViolenceCC/results/xd_late_fusion_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=clip-vit-b-16      eval-mode=XD-standard
[56/58] run=xd_late_fusion_siglip2_s42                 config=D:/ViolenceCC/results/xd_late_fusion_siglip2_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=siglip2-vit-b-16   eval-mode=XD-standard
[57/58] run=xd_late_fusion_so400m_s42                  config=D:/ViolenceCC/results/xd_late_fusion_so400m_s42/config_snapshot.json seed=42 variant=late_fusion    backbone=siglip2-so400m     eval-mode=XD-standard
[58/58] run=xd_skeleton_only_s42                       config=D:/ViolenceCC/results/xd_skeleton_only_s42/config_snapshot.json seed=42 variant=skeleton_only  backbone=n/a(skeleton)      eval-mode=XD-standard

Total: 58 runs  (29 ucf_* UCF-full-length, 29 xd_* XD-standard).  i3d RTFM-gate runs excluded.
```

(Backbone labels for the `*_clip_mean` giant/so400m/siglip2 variants render as the feature-path tail, e.g. `siglip2_giant_mean` — these are cosmetic dry-run labels only and do not affect run-name, seed, or eval-mode.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `--dry-run` was transitively importing torch**
- **Found during:** Task 3 (base-python dry-run capture)
- **Issue:** `enumerate_runs()` originally did `from src.utils.config import load_snapshot_as_config`. Importing that submodule runs `src/utils/__init__.py`, whose first line imports `src.utils.seed`, which imports `torch`. This violated the plan's requirement (and T-rww-02) that the dry-run path import no torch — and it failed outright in any env without a working torch DLL.
- **Fix:** Added `_load_snapshot_as_config()` that loads `src/utils/config.py` directly by file path via `importlib.util.spec_from_file_location`, bypassing the torch-laden package `__init__`. The reused parsing logic is still the project's `load_snapshot_as_config` (not reimplemented). Verified the dry-run now exits 0 under base `python` (broken torch) and imports no torch.
- **Files modified:** `scripts/retrain_lam0.py`
- **Commit:** `9fb04fa`

**2. [Rule 1 - Bug] Lost blank-line separator after the `paths:` block in 21 UCF configs**
- **Found during:** Task 1 (post-edit diff review)
- **Issue:** The `snippet_boundaries_dir` insertion consumed the blank line that separated the `paths:` block from `model:` in the 21 newly-edited UCF configs.
- **Fix:** Restored the blank line in all 21 files so the diff is purely additive (one `snippet_boundaries_dir` line) plus the `lam_smooth` value change. Re-verified Task 1 still passes.
- **Files modified:** the 21 UCF configs (within the same Task 1 set)
- **Commit:** `b8f56a2`

**3. [Rule 1 - Bug] Task 3 verify tripped on the literal `_i3d_` token in the dry-run's human-readable text**
- **Found during:** Task 3 (running the plan's verify script)
- **Issue:** The plan's Task 3 verify asserts `'_i3d_' not in <output>` to confirm no i3d *runs* are listed. My dry-run header/footer used the literal phrase `_i3d_ excluded`, which falsely tripped that substring check even though zero i3d runs were listed.
- **Fix:** Reworded the two descriptive lines to "i3d RTFM-gate runs excluded" (no surrounding underscores). Meaning unchanged; the in-code exclusion check still uses the `_i3d_` token (Task 2 verify still passes). Task 3 verify now passes cleanly.
- **Files modified:** `scripts/retrain_lam0.py`
- **Commit:** `9fb04fa`

## Stage-2 Launch Command (user-run, in a VISIBLE terminal per no-headless rule)

```
conda run -n vcc-main python scripts/retrain_lam0.py
```

(NO `--dry-run` — this trains + re-evals ~58 runs, overwriting the canonical run dirs after backing each up to `*.pre_lam0.bak`. Resumable: re-running skips completed runs via `results/_lam0_done.txt`. Per-run failures are logged to `results/retrain_lam0_errors.log` and the batch continues.)

**Stage 3** (propagation into canonical artifacts / tables / figures / paper) happens AFTER the user confirms the Stage-2 batch completed.

## Commits

- `b8f56a2` — feat(loss): adopt lam_smooth=0 (drop temporal smoothness) + enable full-length UCF eval in configs (43 configs)
- `9fb04fa` — feat: retrain_lam0.py — resumable λ=0 retrain of all 58 canonical runs (dry-run verified)

## Self-Check: PASSED

- `scripts/retrain_lam0.py` — FOUND
- `260601-rww-SUMMARY.md` — FOUND
- commit `b8f56a2` (configs) — FOUND
- commit `9fb04fa` (script) — FOUND
- No training artifacts created (`results/_lam0_done.txt` absent, `results/retrain_lam0_errors.log` absent, 0 `*.pre_lam0.bak`) — confirmed (T-rww-02)
