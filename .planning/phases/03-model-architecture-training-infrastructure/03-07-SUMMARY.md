---
phase: 03-model-architecture-training-infrastructure
plan: 07
subsystem: training
tags: [phase-3, wave-5, tdd, config-snapshot, wandb, variant-configs, e2e, trn-01, trn-04, trn-05, trn-06, d-13]
requires:
  - Plan 03-06: src/train.py (single entry point with main(argv)), CSVLogger, save_checkpoint_atomic, EarlyStopping, SequentialLR scheduler, set_deterministic
  - Plan 03-05: MODEL_REGISTRY fully resolved for gated_fusion
  - Plan 03-04: SkeletonProj / CLIPProj / LateFusion registered
  - Plan 03-01: build_model dispatcher + MILHead primitive
  - wandb 0.25.1 (already pinned by Phase 1 requirements-main.txt)
provides:
  - src/utils/config.py: load_config + load_snapshot_as_config + snapshot_config (TRN-05)
  - src/utils/wandb_logger.py: WandbLogger class with mode-aware noop (D-13)
  - configs/skeleton_only.yaml: complete variant config with wandb block (replaces Plan 06's minimal stub)
  - configs/clip_only.yaml: complete variant config
  - configs/late_fusion.yaml: complete variant config
  - configs/gated_fusion.yaml: complete variant config
  - src/train.py: replaces shutil.copyfile(args.config, config.yaml) with snapshot_config -> config_snapshot.json; adds WandbLogger instantiation + log + finish
  - tests/test_config.py (4 tests): TRN-05 snapshot contents, round-trip, extension dispatch, missing-config-key validation
  - tests/test_wandb_logger.py (2 tests): mode=disabled / missing block no-op
  - tests/test_train_integration.py (2 new tests): config_snapshot_written, snapshot_can_drive_rerun
  - tests/test_train_e2e.py (3 tests, @pytest.mark.e2e): skeleton_only_trains, all_variants_cli, snapshot_roundtrip (Success Criterion #4 bit-identical CSV)
affects:
  - Phase 4 (baseline eval): `python src/train.py --config configs/<variant>.yaml` produces best_model.pth + config_snapshot.json in results/<run>/; evaluate.py loads best_model.pth with load_checkpoint(weights_only=True); config_snapshot.json available for provenance tracking
  - Phase 5 (TTA): wandb mirror pattern reusable for TTA run logging; snapshot_config captures adaptation-time config the same way
  - Any future plan: JSON snapshot round-trip enables one-line reproduction (`python src/train.py --config results/<prior_run>/config_snapshot.json`)
tech-stack:
  added: []  # wandb 0.25.1 already in Phase 1 requirements-main.txt
  patterns:
    - "YAML/JSON polymorphic --config dispatch: load_config() inspects suffix; .json triggers load_snapshot_as_config() extracting the 'config' sub-dict"
    - "Try/finally wandb_logger.finish(): early-stop path also flushes wandb run (D-13 D-03 contract)"
    - "Graceful-degrade WandbLogger: ImportError -> None; wandb.init() exception -> None; log/finish become no-ops. Any network or login issue cannot halt a multi-hour training run (T-03-07-03)"
    - "importlib.metadata.distributions() for in-process pip freeze: avoids subprocess pip freeze (slow + PATH-dependent) and produces sorted name==version strings"
    - "subprocess.check_output with stderr=DEVNULL + triple-catch (CalledProcessError/FileNotFoundError/OSError): never raises on non-git dirs or Windows-PATH edge cases"
    - "TDD RED -> GREEN commit split continues from Plans 01/04/05/06 (2 RED+GREEN pairs = 4 commits)"
    - "Plan 06 -> Plan 07 contract migration: config.yaml -> config_snapshot.json. Migration is captured by updating test_smoke_2_epoch_produces_artifacts assertion rather than keeping both paths -- the old shutil.copyfile is gone, not parallel to the snapshot"
key-files:
  created:
    - src/utils/config.py (119 lines)
    - src/utils/wandb_logger.py (85 lines)
    - configs/clip_only.yaml (39 lines)
    - configs/late_fusion.yaml (41 lines)
    - configs/gated_fusion.yaml (40 lines)
    - tests/test_config.py (102 lines, 4 tests)
    - tests/test_wandb_logger.py (21 lines, 2 tests)
    - tests/test_train_e2e.py (166 lines, 3 tests)
  modified:
    - src/utils/__init__.py (re-exports config + wandb_logger symbols)
    - src/train.py (removed shutil import + local load_config; added snapshot_config + WandbLogger imports; replaced shutil.copyfile with snapshot_config; wrapped epoch loop in try/finally for wandb_logger.finish())
    - tests/test_train_integration.py (append 2 tests; swap 'config.yaml' assertion for 'config_snapshot.json' in test_smoke_2_epoch_produces_artifacts)
    - configs/skeleton_only.yaml (add wandb block; bump data.num_workers 0 -> 4 + pin_memory false -> true for real runs)
decisions:
  - "load_config polymorphic by extension (not a separate CLI flag): keeps --config a single string argument; user doesn't need to remember --config-is-snapshot. Extension (.yaml vs .json) is a reliable signal because snapshot_config always emits valid JSON."
  - "Remove shutil.copyfile(args.config, run_dir/'config.yaml'): config_snapshot.json supersedes the raw copy -- it includes the resolved cfg verbatim + provenance. Keeping both would double-write and create a stale config.yaml when --epochs CLI override mutates cfg at runtime."
  - "Try/finally around the epoch loop for wandb_logger.finish(): early-stop break and exception paths both need wandb.finish() to avoid orphan runs on the wandb dashboard. Plan 06's early-stop exit path was not wrapped; this plan adds the try/finally so finish() runs in every exit path."
  - "wandb.init() wrapped in try/except (catches network/login/dir errors): any wandb runtime failure must NOT halt training. T-03-07-03 DoS disposition. The empirical test proves disabled mode is noop; runtime failures in online mode cannot be unit-tested without network, but the try/except is grep-verified."
  - "Snapshot includes packages list via importlib.metadata, not subprocess pip freeze: avoids Windows PATH brittleness; stdlib-only; sorted list is stable across runs (needed for bit-identical snapshot content byte-comparison in theory, though Plan 07's bit-identity check is on CSV rows not snapshot bytes)."
  - "test_snapshot_roundtrip over test_bit_identical (additive, not redundant): Plan 06's test_bit_identical uses 2 YAML copies; Plan 07's test_snapshot_roundtrip exercises the JSON-dispatch code path. A bug in load_snapshot_as_config could break SC #4 without test_bit_identical catching it."
  - "Plan 06's test_smoke_2_epoch_produces_artifacts assertion updated in place (not duplicated): the plan explicitly marks the config.yaml -> config_snapshot.json contract change. Keeping the old assertion would require maintaining a dead shutil.copyfile code path; the test is the contract gate, and the new contract is config_snapshot.json."
  - "Plain assertion on WandbLogger.log()/finish() not raising (no mock or network call): wandb's public API guarantees log/finish don't raise when no run is active. Testing disabled mode in isolation is sufficient; testing online mode requires a wandb account, which is out of CI scope."
metrics:
  duration: ~12m
  completed: 2026-04-14T17:25:00Z
  tasks_executed: 2
  commits: 4
  files_created: 8
  files_modified: 3
  tests_added: 11  # 4 config + 2 wandb_logger + 2 integration + 3 e2e
  tests_passing: 104  # 93 pre-existing Wave 1-4 + 11 new Plan 07
  lines_added: ~651
---

# Phase 3 Plan 7: Config Snapshot + wandb + 4 Variant YAMLs Summary

Closes Phase 3 by landing TRN-05 config snapshot (git SHA + pip freeze + env + resolved cfg) and D-13 wandb mirror integration, materializing the 4 variant YAMLs (skeleton_only, clip_only, late_fusion, gated_fusion) with complete `wandb:` blocks, and wiring `src/train.py` to (1) write `config_snapshot.json` per run replacing Plan 06's `config.yaml` copy, (2) accept a prior run's `config_snapshot.json` as `--config` for bit-identical reruns, and (3) invoke the wandb mirror alongside CSV logging.

The Wave 5 acceptance target is met: `pytest tests/test_train_e2e.py -m e2e` runs the full CLI for all 4 variants (1 epoch each, WANDB_MODE=disabled), verifies all expected artifacts exist, and asserts bit-identical CSV rows when rerunning from a snapshot. Phase 3's 6 VALIDATION.md acceptance gates all have an automated test.

## Performance

- **Duration:** ~12 min
- **Tasks:** 2 (each with strict RED/GREEN TDD commits)
- **Commits:** 4 (2 RED + 2 GREEN)
- **Files created:** 8 (2 utils modules + 3 new configs + 3 test files)
- **Files modified:** 3 (src/utils/__init__.py, src/train.py, tests/test_train_integration.py); plus configs/skeleton_only.yaml regenerated with wandb block
- **Tests added:** 11 total (4 config + 2 wandb_logger + 2 integration + 3 e2e)
- **Tests passing:** 104/104 full regression (93 pre-existing + 11 new)

## Accomplishments

- **TRN-05 config snapshot lands:** `snapshot_config(cfg, path)` writes an 8-key JSON payload (`config`, `git`, `python`, `torch`, `numpy`, `cuda`, `env`, `packages`) at `results/<run>/config_snapshot.json` for every run. `git` captures `{sha, dirty}` via `git rev-parse HEAD` + `git status --porcelain` with triple-catch fallback. `packages` is an in-process `importlib.metadata.distributions()` sorted list (stdlib; no subprocess).
- **D-13 wandb mirror lands:** `WandbLogger` wraps `wandb.init` / `log` / `finish`. `mode=disabled` and ImportError both degrade to a silent no-op. Any `wandb.init()` runtime exception (network hiccup, missing login, directory permission) is caught so a multi-hour training run cannot be halted by wandb client issues (T-03-07-03).
- **Success Criterion #4 CONFIRMED:** `test_snapshot_roundtrip` performs two independent runs:
  1. First: `python src/train.py --config configs/skeleton_only.yaml` -> writes `config_snapshot.json`
  2. Second: `python src/train.py --config <first_run>/config_snapshot.json` -> reads snapshot, extracts `config` sub-dict, runs
  Asserts **row-count match** (catches partial/crashed runs) AND **exact string equality on (train_loss, val_loss) tuples per row**. Bit-identical.
- **4 variant YAMLs materialized:** All 4 share identical `train` block (TRN-01 hyperparameters: lr=1e-4, wd=1e-2, epochs=50, warmup=5, patience=10, k_topk=3, margin=1.0, lam_sparse=8e-3, lam_smooth=8e-4) and identical `wandb` block (project=violencecc, mode=online, per-variant tags). Only the `model.variant` + variant-specific `*_dim` / `alpha` fields differ between YAMLs.
- **TRN-06 end-to-end acceptance for all 4 variants:** `test_all_variants_cli` loops through all 4 configs, runs `main(["--config", path, "--epochs", "1"])` for each, verifies each produces the expected artifacts + snapshot with matching `config.model.variant` field.
- **Plan 06 regression preserved:** `test_bit_identical` (2-YAML case) still passes alongside `test_snapshot_roundtrip` (JSON-dispatch case). No contract slippage.

## Config Snapshot File Format (TRN-05)

`results/<run>/config_snapshot.json` — top-level keys (written sorted):

| Key | Type | Content |
|-----|------|---------|
| `config` | dict | Resolved cfg dict (after CLI overrides applied). Round-trip integrity: `load_snapshot_as_config(path) == cfg_passed_in`. |
| `git` | dict | `{"sha": <40-char hex or "unknown">, "dirty": bool}` via `git rev-parse HEAD` + `git status --porcelain`. |
| `python` | str | `sys.version`. |
| `torch` | str | `torch.__version__`. |
| `numpy` | str | `numpy.__version__`. |
| `cuda` | str or null | `torch.version.cuda` (None for CPU-only builds). |
| `env` | dict | `{"CUBLAS_WORKSPACE_CONFIG": <env or null>, "PYTHONHASHSEED": <env or null>}`. |
| `packages` | list[str] | Sorted `name==version` from `importlib.metadata.distributions()`. Includes torch, numpy, and all installed packages. |

## load_snapshot_as_config Shim (Success Criterion #4)

```python
# src/utils/config.py
def load_config(path):
    if Path(path).suffix.lower() == ".json":
        return load_snapshot_as_config(path)
    return yaml.safe_load(open(path))

def load_snapshot_as_config(snapshot_path):
    snap = json.load(open(snapshot_path))
    if "config" not in snap:
        raise ValueError("not a valid config_snapshot")
    return snap["config"]
```

Usage:
```
# First run writes config_snapshot.json
$ python src/train.py --config configs/gated_fusion.yaml

# Later: reproduce from the snapshot
$ python src/train.py --config results/ucf_gated_fusion_42_20260414-172000/config_snapshot.json
# -> bit-identical train_log.csv
```

## 4 Variant YAML Files (TRN-06)

All 4 files share the same `paths`, `data`, `train`, `wandb` blocks. Only the `model` block differs:

| YAML | `model.variant` | `model.*` variant-specific keys |
|------|----------------|----------------------------------|
| `configs/skeleton_only.yaml` | `skeleton_only` | `skel_dim: 256` |
| `configs/clip_only.yaml` | `clip_only` | `clip_dim: 1024, proj_dim: 512` |
| `configs/late_fusion.yaml` | `late_fusion` | `skel_dim: 256, clip_dim: 1024, proj_dim: 512, alpha: equal` |
| `configs/gated_fusion.yaml` | `gated_fusion` | `skel_dim: 256, clip_dim: 1024, shared_dim: 256` |

Shared `train` block (TRN-01): `lr: 1.0e-4, weight_decay: 1.0e-2, epochs: 50, warmup_epochs: 5, patience: 10, k_topk: 3, margin: 1.0, lam_sparse: 8.0e-3, lam_smooth: 8.0e-4`.

Shared `wandb` block (D-13): `project: violencecc, mode: online, tags: [phase3, <variant>, ucf]`.

## wandb Mode Behavior Matrix (D-13)

| Mode | wandb.init called? | Network required? | WANDB_MODE env set? | Use case |
|------|-------------------|-------------------|---------------------|----------|
| `disabled` | no | no | no | CI, offline dev, test fixtures. Default for `pytest`. |
| `offline` | yes (writes local wandb/) | no | WANDB_MODE=offline | Field runs on a laptop without internet; `wandb sync` later. |
| `online` | yes | yes | WANDB_MODE=online | Full experiment tracking; default for real training runs. |

Graceful degradation paths (all become disabled no-op):
1. `wandb` not installed -> `ImportError` -> `self.run = None`
2. `wandb.init()` raises (network, login, dir permission) -> caught -> `self.run = None`
3. `wandb.log()` raises at runtime -> caught -> silent

CSV is the offline source of truth (Plan 06 invariant). wandb is a mirror (D-13).

## Test Inventory

| File | Tests | Marker | Covers |
|------|-------|--------|--------|
| `tests/test_config.py` | 4 | — | TRN-05: snapshot 8-key contents, round-trip, extension dispatch, validation |
| `tests/test_wandb_logger.py` | 2 | — | D-13: disabled + missing-block no-op |
| `tests/test_train_integration.py` (appended 2) | 2 | — | config_snapshot_written, snapshot_can_drive_rerun |
| `tests/test_train_e2e.py` | 3 | `@pytest.mark.e2e` | skeleton_only_trains (TRN-06), all_variants_cli (TRN-06), snapshot_roundtrip (SC #4 + TRN-05) |

## D-XX / TRN-XX Coverage (Plan 07 additions)

| Requirement / Decision | Artifact | Status |
|------------------------|----------|--------|
| TRN-05 config snapshot (git SHA + pip freeze + resolved cfg) | `src/utils/config.py:snapshot_config` | covered |
| TRN-05 snapshot -> --config round-trip | `load_config` dispatches by `.json` suffix -> `load_snapshot_as_config` | covered |
| TRN-06 single YAML-driven entry point for all 4 variants | `tests/test_train_e2e.py::test_all_variants_cli` passes all 4 | covered |
| D-13 wandb online sync (CSV is source of truth) | `src/utils/wandb_logger.py:WandbLogger` + mode-aware noop | covered |
| D-13 wandb `mode=disabled` safe no-op | `tests/test_wandb_logger.py::test_wandb_disabled_is_noop` | covered |
| D-13 wandb 4 variant `tags` block | All 4 configs/*.yaml ship with `tags: [phase3, <variant>, ucf]` | covered |
| Success Criterion #4 bit-identical rerun from snapshot | `tests/test_train_e2e.py::test_snapshot_roundtrip` asserts exact CSV row equality | covered |

## Verification Evidence

```
$ python -m pytest tests/test_config.py tests/test_wandb_logger.py -v --tb=short
tests/test_config.py::test_snapshot_contents PASSED                      [ 16%]
tests/test_config.py::test_load_snapshot_as_config PASSED                [ 33%]
tests/test_config.py::test_load_config_dispatches_by_extension PASSED    [ 50%]
tests/test_config.py::test_load_snapshot_missing_config_key PASSED       [ 66%]
tests/test_wandb_logger.py::test_wandb_disabled_is_noop PASSED           [ 83%]
tests/test_wandb_logger.py::test_wandb_missing_block_is_noop PASSED      [100%]
============================== 6 passed in 4.27s ==============================

$ python -m pytest tests/test_train_integration.py -v --tb=short -k "config_snapshot_written or snapshot_can_drive_rerun"
tests/test_train_integration.py::test_config_snapshot_written PASSED     [ 50%]
tests/test_train_integration.py::test_snapshot_can_drive_rerun PASSED    [100%]
================= 2 passed, 8 deselected, 2 warnings in 7.24s =================

$ python -m pytest tests/test_train_e2e.py -v --tb=short -m e2e
tests/test_train_e2e.py::test_skeleton_only_trains PASSED                [ 33%]
tests/test_train_e2e.py::test_all_variants_cli PASSED                    [ 66%]
tests/test_train_e2e.py::test_snapshot_roundtrip PASSED                  [100%]
============================= 3 passed in 12.12s ==============================

$ python -m pytest tests/ --tb=short -k "not requires_features"
104 passed, 11 warnings in 61.84s

$ python -c "import yaml; [yaml.safe_load(open(f'configs/{v}.yaml')) for v in ['skeleton_only','clip_only','late_fusion','gated_fusion']]; print('4 YAMLs parse ok')"
4 YAMLs parse ok

$ python -c "from src.utils.config import load_config, snapshot_config, load_snapshot_as_config; print('config ok')"
config ok

$ python -c "from src.utils.wandb_logger import WandbLogger; print('wandb_logger ok')"
wandb_logger ok

$ python src/train.py --help
usage: train.py [-h] --config CONFIG [--seed SEED] [--epochs EPOCHS]
                [--results-dir RESULTS_DIR]
ViolenceCC training entry point (TRN-06)

$ findstr /C:"snapshot_config(cfg, run_dir" D:/ViolenceCC/src/train.py
    snapshot_config(cfg, run_dir / "config_snapshot.json")

$ findstr /C:"WandbLogger(cfg, run_dir)" D:/ViolenceCC/src/train.py
    wandb_logger = WandbLogger(cfg, run_dir)

$ findstr /C:"shutil.copyfile" D:/ViolenceCC/src/train.py
(0 matches -- Plan 06's config.yaml copy has been replaced by snapshot_config)

$ findstr /C:"_test.txt" D:/ViolenceCC/src/
(0 matches across all .py files in src/)
```

## Commit Lineage

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| 1 RED | `0e5b649` | test | failing tests for config snapshot + wandb logger |
| 1 GREEN | `3691e4e` | feat | TRN-05 config snapshot + D-13 wandb mirror |
| 2 RED | `66c5887` | test | e2e acceptance tests for 4 variants + snapshot roundtrip |
| 2 GREEN | `db84639` | feat | 4 variant YAMLs + TRN-06 e2e acceptance |

No REFACTOR commits — GREEN implementations matched RESEARCH.md specs verbatim on first write.

## Decisions Made

1. **Polymorphic `load_config` by file suffix** — one CLI argument handles both YAML configs and JSON snapshots. Suffix detection (`.json` -> `load_snapshot_as_config`, else YAML) is a reliable signal because `snapshot_config()` always emits valid JSON. This keeps `--config` as a single string arg rather than adding `--config-snapshot` alongside.

2. **Remove `shutil.copyfile(args.config, run_dir / "config.yaml")` entirely** — `config_snapshot.json` supersedes the raw copy (it includes the resolved cfg verbatim + provenance). Keeping both would double-write and create a stale `config.yaml` when `--epochs` CLI override mutates `cfg` at runtime. The plan explicitly asks for this migration.

3. **Try/finally around epoch loop for `wandb_logger.finish()`** — Plan 06's epoch loop had no try/finally. Plan 07 adds it so `wandb.finish()` runs on early-stop AND on exception paths, avoiding orphan runs on the wandb dashboard.

4. **`wandb.init()` wrapped in try/except** — Any wandb-side runtime failure (network, login, dir permission) must NOT halt training. T-03-07-03 DoS mitigation. The exception handler degrades to `self.run = None` and all subsequent log/finish calls no-op.

5. **`importlib.metadata.distributions()` for pip freeze** — Stdlib; no subprocess overhead; avoids Windows PATH brittleness. Returns sorted `name==version` list. Equivalent content to `pip freeze` for our use case.

6. **Update `test_smoke_2_epoch_produces_artifacts` assertion in-place** — Plan 06 wrote `config.yaml`; Plan 07 writes `config_snapshot.json`. The plan explicitly marks this contract change. Keeping both assertions would imply maintaining a dead `shutil.copyfile` code path; the new contract is JSON snapshot, full stop.

7. **`test_snapshot_roundtrip` is additive, not redundant with `test_bit_identical`** — Plan 06's `test_bit_identical` uses two YAML configs (baseline TRN-03 bit-identity). Plan 07's `test_snapshot_roundtrip` exercises the JSON-dispatch code path inside `load_config`. A bug in `load_snapshot_as_config` could break Success Criterion #4 without `test_bit_identical` catching it — hence the separate test.

8. **`num_workers` / `pin_memory` bump in `configs/skeleton_only.yaml`** — Plan 06's skeleton_only.yaml had `num_workers: 0, pin_memory: false` (smoke-test defaults). Plan 07 bumps to the real-run defaults `num_workers: 4, pin_memory: true`. E2E tests re-override to 0/false for synthetic-feature speed, so this does not affect test execution.

## Hand-offs to Later Plans / Phases

- **Phase 4 (baseline eval):** `python src/train.py --config configs/<variant>.yaml` produces `best_model.pth` + `last_model.pth` + `config_snapshot.json` + `train_log.csv` in `results/<run>/`. `evaluate.py` loads `best_model.pth` with `load_checkpoint(weights_only=True)` (Plan 06 contract). `config_snapshot.json` available for per-model provenance if needed.
- **Phase 5 (TTA):** Same snapshot + wandb patterns apply. TTA run can wrap itself in `WandbLogger` for parity with training. `snapshot_config` captures TTA-time config the same way.
- **Any future plan:** The one-line reproduction pattern (`python src/train.py --config results/<run>/config_snapshot.json`) supports thesis reviewer scenario: "send me the snapshot, I reproduce the numbers".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan 06 test assertion for `config.yaml` must migrate to `config_snapshot.json`**

- **Found during:** Task 1 GREEN verification (Plan 06 regression test `test_smoke_2_epoch_produces_artifacts` failed asserting `config.yaml` exists)
- **Issue:** Plan 06's smoke test asserted `(run / "config.yaml").exists()`. Plan 07 explicitly removes the `shutil.copyfile(args.config, run_dir / "config.yaml")` call and replaces it with `snapshot_config(cfg, run_dir / "config_snapshot.json")`. The Plan 06 test assertion becomes stale under the new contract.
- **Fix:** Updated the assertion from `(run / "config.yaml")` to `(run / "config_snapshot.json")` in `test_smoke_2_epoch_produces_artifacts`. This is an expected Plan 06 -> Plan 07 contract migration flagged by the plan itself (line: "Replace `shutil.copyfile(args.config, run_dir / 'config.yaml')` with `snapshot_config(cfg, run_dir / 'config_snapshot.json')`"). Kept all other Plan 06 tests unchanged.
- **Files modified:** `tests/test_train_integration.py` (1 assertion line)
- **Commit:** `3691e4e` (rolled into Task 1 GREEN)
- **Impact on plan contract:** Plan contract preserved — Plan 07's acceptance criteria explicitly states "src/train.py no longer calls shutil.copyfile to write config.yaml". The test is the enforcement gate for that contract.

### Architectural Changes

None.

### Authentication Gates

None. wandb credentials are user-shell-scoped (`wandb login` writes to `~/.netrc`); never referenced in code or configs.

## Known Stubs

None introduced by this plan. Grep for `TODO|FIXME|placeholder|coming soon` across `src/utils/config.py`, `src/utils/wandb_logger.py` returned 0 matches. The single grep match for "not available" in `src/utils/config.py` (line 47) is a docstring describing the git-fallback path ("if git is not available"), not a stub indicating missing functionality.

## Threat Flags

No new security surface beyond the plan's `<threat_model>`. All 6 threats (T-03-07-01 through T-03-07-06) have their mitigations implemented and verified:

| Threat ID | Mitigation | Test / Evidence |
|-----------|------------|-----------------|
| T-03-07-01 | No secrets in YAML schema; paths are machine-local | Grep configs/ for "api_key"/"token" = 0 matches |
| T-03-07-02 | `wandb==0.25.1` pinned (Phase 1); ImportError -> disabled | `test_wandb_disabled_is_noop` + import-catch in `WandbLogger.__init__` |
| T-03-07-03 | wandb.log/init wrapped in try/except | Grep `src/utils/wandb_logger.py` for `except Exception` = 3 matches (init, log, finish) |
| T-03-07-04 | subprocess git hardcoded args; triple-catch | `_git_info()` catches CalledProcessError/FileNotFoundError/OSError |
| T-03-07-05 | WANDB_API_KEY never in code/configs | Grep codebase for "WANDB_API_KEY" = 0 matches |
| T-03-07-06 | `test_bit_identical` still in regression suite | 104/104 passing suite includes Plan 06 test |

## Phase 3 Status

**Phase 3 (Model Architecture & Training Infrastructure) is COMPLETE** upon this plan merging green.

All 6 VALIDATION.md Phase 3 acceptance gates now have an automated test:
- TRN-01 (AdamW + SequentialLR) — `test_linear_cosine`, `test_optimizer_config`
- TRN-02 (Early stopping + atomic checkpoint) — `test_early_stopping_*`, `test_save_failure_preserves_original`
- TRN-03 (Bit-identical reproducibility) — `test_bit_identical` + `test_snapshot_roundtrip`
- TRN-04 (CSV header + rows) — `test_csv_header`, `test_csv_rows`
- TRN-05 (Config snapshot) — `test_snapshot_contents`, `test_config_snapshot_written`, `test_snapshot_roundtrip`
- TRN-06 (Single entry point for all 4 variants) — `test_all_variants_cli`, `test_skeleton_only_trains`

Next: **Phase 4 (Baseline Evaluation & Main Results)** consumes `best_model.pth` per variant via `evaluate.py` with frame-level AUC/AP computation on UCF-Crime (available) and XD-Violence (pending ~5-8 day extraction).

## Self-Check: PASSED

Created files verified:
- FOUND: `src/utils/config.py`
- FOUND: `src/utils/wandb_logger.py`
- FOUND: `configs/clip_only.yaml`
- FOUND: `configs/late_fusion.yaml`
- FOUND: `configs/gated_fusion.yaml`
- FOUND: `tests/test_config.py`
- FOUND: `tests/test_wandb_logger.py`
- FOUND: `tests/test_train_e2e.py`

Modified files verified:
- FOUND: `src/utils/__init__.py` (re-exports config + wandb_logger)
- FOUND: `src/train.py` (snapshot_config + WandbLogger wired; shutil.copyfile removed)
- FOUND: `tests/test_train_integration.py` (2 appended tests + config.yaml -> config_snapshot.json assertion update)
- FOUND: `configs/skeleton_only.yaml` (wandb block added)

Commits verified in git log:
- FOUND: `0e5b649` (Task 1 RED)
- FOUND: `3691e4e` (Task 1 GREEN)
- FOUND: `66c5887` (Task 2 RED)
- FOUND: `db84639` (Task 2 GREEN)

Test suite verified:
- 104/104 non-requires_features tests GREEN in 61.84s
- 3/3 e2e tests GREEN in 12.12s
- 11 new tests added in Plan 07 (4 config + 2 wandb_logger + 2 integration + 3 e2e)
- All Plan 07 required_tests from VALIDATION.md pass

---
*Phase: 03-model-architecture-training-infrastructure, Plan: 07*
*Completed: 2026-04-14T17:25:00Z*
