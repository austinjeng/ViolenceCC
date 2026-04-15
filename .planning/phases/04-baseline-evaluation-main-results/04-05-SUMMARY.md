---
phase: 04-baseline-evaluation-main-results
plan: 05
subsystem: orchestration
tags: [run-ablations, wandb-preflight, offline-fallback, results-index, done-marker, run-name, d-26, d-30, d-31, d-32, d-33, d-34, d-39, d-40, d-41, tdd, subprocess]

# Dependency graph
requires:
  - phase: 04-baseline-evaluation-main-results
    plan: 02
    provides: "src/evaluate.py --run-dir CLI + eval_metrics.json schema + atomic .done marker contract (D-31 probe target)"
  - phase: 04-baseline-evaluation-main-results
    plan: 03
    provides: "configs/rtfm_i3d.yaml (queue rtfm_gate config) + MODEL_REGISTRY['rtfm_i3d'] (first queue target)"
  - phase: 04-baseline-evaluation-main-results
    plan: 04
    provides: "configs/gated_fusion_2person.yaml + configs/gated_fusion_clip_mean.yaml (phase4_pooling queue targets)"
  - phase: 03-model-architecture-training-infrastructure
    provides: "src/train.py parse_args + run_name() fallback + run_dir creation site (D-14 timestamped default); CSVLogger pattern reused for results_index_append; WandbLogger init try/except block extended with D-40 offline branch"

provides:
  - "scripts/wandb_preflight.py — fail-fast credential check (exit 0 env var | exit 0 netrc | exit 2 missing; D-39)"
  - "scripts/run_ablations.py — subprocess orchestrator with RunSpec dataclass + 4 queues (rtfm_gate / phase4_main / phase4_pooling / phase4_seeds) + .done probe + runner-errors.log + results-index.csv (D-26 + D-30..D-34 + D-41)"
  - "src.utils.csv_logger.results_index_append(path, row) + RESULTS_INDEX_COLUMNS 12-column schema (D-33)"
  - "src.utils.wandb_logger.WandbLogger offline-fallback branch on wandb.errors.Error (D-40)"
  - "src/train.py --run-name CLI override (D-30 deterministic dirs)"
  - "tests/test_wandb_preflight.py + tests/test_results_index.py + tests/test_done_marker.py + tests/test_run_ablations.py + expanded tests/test_wandb_logger.py"

affects:
  - "04-06 (empirical execution: Plan 06 runs `python scripts/run_ablations.py --queue rtfm_gate` then `--queue phase4_main` then `--queue phase4_pooling` then `--queue phase4_seeds`; all 9 runs auditable via results/results-index.csv)"
  - "04-07 (SUMMARY / UAT: results-index.csv is the thesis-table data source; resume-on-restart via .done markers means long queues can survive laptop reboots)"
  - "05-tta (Phase 5 reads results/ucf_gated_fusion_s42/best_model.pth — the deterministic run_name format here is the stable handoff key)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Subprocess orchestrator with argv-list + check=True + per-call timeout (T-04-05-01: no shell=True anywhere)"
    - "Filesystem-probe resume via atomic .done marker as LAST write after eval_metrics.json + eval_scores.npz"
    - "Dataclass-driven RunSpec with derived @property run_name + wandb_tags (D-30 / D-41 formats)"
    - "Append-only CSV audit log with header-on-first-open, flush+fsync-per-row, missing-columns-blank semantics"
    - "Module-top heavy-import pattern (results_index_append at module top) to load torch before tests monkeypatch subprocess.run (platform.machine() inside `import torch` would otherwise hit the mock)"
    - "D-40 2-level exception catch: first wandb.errors.Error → retry mode='offline'; second failure → self.run=None (noop); getattr(..., 'Error', Exception) for wandb-version agnosticism"
    - "TDD RED-GREEN per-task discipline; tests committed first with import/attribute errors, then GREEN implementation flips all 23 new test assertions"

key-files:
  created:
    - "scripts/wandb_preflight.py"
    - "scripts/run_ablations.py"
    - "tests/test_wandb_preflight.py"
    - "tests/test_results_index.py"
    - "tests/test_done_marker.py"
    - "tests/test_run_ablations.py"
  modified:
    - "src/utils/csv_logger.py"
    - "src/utils/wandb_logger.py"
    - "src/train.py"
    - "tests/test_wandb_logger.py"

key-decisions:
  - "D-26 implemented: Python subprocess orchestrator (not shell, not Makefile). Cross-platform on Windows dev + Linux CI. argv-list form avoids shell=True entirely (T-04-05-01)."
  - "D-30 implemented: --run-name CLI arg on src/train.py overrides the D-14 timestamped default; run_name(cfg) kept as fallback for ad-hoc/debug runs. Deterministic format: <dataset>_<variant>[_<cache_variant>]_s<seed>."
  - "D-31 implemented: is_done(run_dir) = (run_dir / '.done').exists(). The .done marker is the LAST write of a completed run (after eval_metrics.json lands); its presence guarantees resumable downstream processing."
  - "D-32 implemented: CalledProcessError + TimeoutExpired on either train.py OR evaluate.py subprocess → log_error appends a line to runner-errors.log (timestamp + run_name + exc_repr) and run_queue continues to the next spec. Queue never halts on a single spec failure."
  - "D-33 implemented: RESULTS_INDEX_COLUMNS = 12 columns in stable order; results_index_append writes header on first open, flushes + fsyncs after each row. Pandas-reads clean."
  - "D-34 implemented: results-index.csv append happens ONLY after eval_metrics.json validates as JSON. If eval crashed mid-write, runner logs 'eval_missing_metrics' or 'eval_bad_json' phases and the .done marker is absent, so the next run picks up from scratch."
  - "D-39 implemented: scripts/wandb_preflight.py is invoked before every non-dry-run queue unless --no-preflight. Exit 0 if env var OR netrc api_key OR wandb not installed; exit 2 with actionable stderr otherwise. Runner exits 2 too if preflight fails."
  - "D-40 implemented: WandbLogger catches wandb.errors.Error specifically (getattr(..., 'Error', Exception) for version-agnostic compatibility). Retries with mode='offline'; prints '[wandb] offline fallback after <ExcType>: <msg>'. Cascaded failure → self.run=None (silent noop). CSV logger remains source of truth."
  - "D-41 implemented: RunSpec.wandb_tags = ['phase4', dataset, variant, 's<seed>'] + [cache_variant] when set. Consumed by Plan 06 when the YAML's wandb.tags gets overridden with spec-specific values."
  - "Queue composition: rtfm_gate=1 (xd_i3d/rtfm_i3d), phase4_main=4 (ucf/skel_only + ucf/clip_only + ucf/late_fusion + ucf/gated_fusion), phase4_pooling=2 (ucf/gated_fusion × {2person, clip_mean}), phase4_seeds=2 (ucf/gated_fusion × {123, 2024}). Total 9 unique specs; seed=42 gated_fusion is in phase4_main so we deliberately skip it in phase4_seeds (D-27/D-28)."
  - "Results root CLI override (--results-root) lets tests redirect the whole per-run directory tree into tmp_path without touching the real results/ directory. Same override path is used for the runner-errors.log location (test isolation)."
  - "Import results_index_append at module top (not inside run_one) so that the transitive `import torch` (via src.utils.__init__ → src.utils.seed) happens at module-load time, BEFORE any pytest monkeypatch intercepts subprocess.run. Otherwise platform.machine() inside torch's DLL loader would call the mocked run and raise AttributeError. Discovered during Task 2 GREEN verification."

patterns-established:
  - "Pattern: subprocess orchestrator with check=True + timeout + argv-list — the only shell-invocation posture that satisfies T-04-05-01. No shell=True anywhere in the entire runner."
  - "Pattern: D-31 filesystem-probe resume — .done is a 1-byte text marker, trivially cheap to check, atomic via os.replace, LAST write after all heavier outputs. Works identically on POSIX and Windows."
  - "Pattern: append-only audit log with 12-column fixed schema — readers use pandas.read_csv without schema knowledge; writers use results_index_append regardless of which subset of columns they have data for. Stable across all 9 runs + any future Phase 4b rows."
  - "Pattern: heavy-import-at-module-top when tests monkeypatch subprocess.run — avoids latent AttributeError from platform.machine() inside torch DLL loading. Applied to scripts/run_ablations.py."
  - "Pattern: wandb exception catch with getattr(..., 'Error', Exception) fallback — works against wandb versions that don't expose a stable errors.Error class while preserving the specific-then-generic catch ordering in WandbLogger.__init__."

requirements-completed:
  - EVAL-05

# Metrics
duration: 10min
completed: 2026-04-15
---

# Phase 4 Plan 05: Ablation orchestrator + wandb preflight + --run-name + offline fallback Summary

**Ships the full ablation orchestration surface so Plan 06 just runs the queues without writing orchestration code.** `scripts/run_ablations.py` with 4 queues (rtfm_gate / phase4_main / phase4_pooling / phase4_seeds) = 9 unique deterministic-named runs, resume-on-restart via `.done` markers, append-only `results/results-index.csv` audit log, and `runner-errors.log` for failed subprocesses. `scripts/wandb_preflight.py` fails fast before the queue opens if wandb credentials are missing (D-39); `src/utils/wandb_logger.py` catches `wandb.errors.Error` mid-run and retries with `mode='offline'` (D-40). `src/train.py` gains `--run-name` for deterministic dirs (D-30). `src/utils/csv_logger.py` gains `results_index_append` + `RESULTS_INDEX_COLUMNS` (D-33). 23 new tests green + 2 augmented wandb_logger tests; 107-test broader Phase 4 suite green, 0 regressions.

## Performance

- **Duration:** ~10 min
- **Started:** 2026-04-15T11:00:14Z
- **Completed:** 2026-04-15T11:10:22Z
- **Tasks:** 2 (each TDD RED + GREEN)
- **Files changed:** 10 (6 created, 4 modified)

## Accomplishments

- **D-39 wandb preflight** (`scripts/wandb_preflight.py`): exit 0 if `WANDB_API_KEY` env var set; exit 0 if `wandb.api.api_key` is non-None (netrc or settings); exit 0 if wandb not installed (CSV-only mode is fine); exit 2 otherwise with actionable stderr mentioning `WANDB_API_KEY`, `wandb login`, and `wandb.mode: disabled`. 3 tests (W1 env, W2 missing, W3 netrc) green.
- **D-40 offline fallback** (`src/utils/wandb_logger.py`): the Phase 3 `try/except Exception` block is now a 2-level catch. `wandb.errors.Error` specifically (via `getattr(..., 'Error', Exception)` for version-agnostic behavior) triggers re-init with `mode='offline'` and prints `[wandb] offline fallback after <ExcType>: <msg>` to stdout. A cascaded failure on the offline re-init falls through to `self.run = None` (silent noop). 2 new tests cover the first-fail-then-success path AND the cascaded-failure path.
- **D-33 append-only audit log** (`src/utils/csv_logger.py`): `RESULTS_INDEX_COLUMNS` defines the 12-column stable schema; `results_index_append(path, row)` writes the header on first open, appends rows on subsequent opens, flushes + fsyncs per row, and fills missing row keys with empty strings. Existing `CSVLogger` class untouched. 4 tests cover header-on-first / no-duplicate-header / missing-columns-blank / column-order-stable.
- **D-30 deterministic run dirs** (`src/train.py`): `--run-name` CLI arg overrides the Phase 3 D-14 timestamped default inside `main()`; absence preserves the timestamped fallback for ad-hoc/debug runs. 3 tests cover `--help` text, arg parsing with the value, default=None.
- **D-26 + D-30..D-34 + D-41 orchestrator** (`scripts/run_ablations.py`): 308-line subprocess orchestrator with:
  * `RunSpec` dataclass with D-30 `run_name` and D-41 `wandb_tags` derived properties.
  * 4 `QUEUES` dict entries summing to 9 unique specs; `rtfm_gate` is first per D-18 (harness gate must pass before main ablations run).
  * `is_done(run_dir)` filesystem probe for `.done` marker (D-31).
  * `run_one(spec, results_root, err_log, timeout_s)`: `subprocess.run(train_cmd, check=True, timeout=...)` then `subprocess.run(eval_cmd, check=True, timeout=...)` — argv list, no `shell=True` anywhere. `CalledProcessError`/`TimeoutExpired` are caught and logged via `log_error` (D-32). After eval succeeds, parses `eval_metrics.json` and calls `results_index_append` (D-33/D-34).
  * `run_queue(specs, results_root, err_log, dry_run)`: iterate specs, skip done, dry-run prints `[dry-run] would run <name>`, otherwise invokes `run_one`. Returns a `{succeeded, skipped, failed}` summary.
  * `main()`: `--queue` choices from `sorted(QUEUES)`; `--dry-run` + `--no-preflight` + `--results-root` CLI overrides. Preflight subprocess blocks queue on non-zero exit unless `--no-preflight`.
- **12 run_ablations tests green + end-to-end CLI dry-run manually verified** (`python scripts/run_ablations.py --queue rtfm_gate --dry-run --no-preflight` emits `[dry-run] would run xd_i3d_rtfm_i3d_s42` and the JSON summary).

## Task Commits

4 commits (RED → GREEN for each task):

1. **Task 1 RED** — `2146607` (test): 11 failing tests across 4 files (3 wandb_preflight + 7 results_index + 3 done_marker + 2 offline_fallback).
2. **Task 1 GREEN** — `1b39184` (feat): wandb_preflight.py + csv_logger.results_index_append + wandb_logger D-40 branch + train.py --run-name.
3. **Task 2 RED** — `5c64aed` (test): 12 failing tests in test_run_ablations.py (ModuleNotFoundError: scripts.run_ablations).
4. **Task 2 GREEN** — `082a51e` (feat): scripts/run_ablations.py 308-line orchestrator + module-top import fix.

## Files Created/Modified

### Created

| Path | Purpose |
| ---- | ------- |
| `scripts/wandb_preflight.py` | D-39: fail-fast credential check |
| `scripts/run_ablations.py` | D-26: subprocess orchestrator with 4 queues + resume + audit log |
| `tests/test_wandb_preflight.py` | 3 tests (W1/W2/W3) covering the 3 preflight paths |
| `tests/test_results_index.py` | 7 tests: 4 CSV (append/no-dup-header/missing-blank/ordering) + 3 train.py --run-name (help/parse/default) |
| `tests/test_done_marker.py` | 3 tests: atomic write-temp-rename + is_done probe + last-write invariant |
| `tests/test_run_ablations.py` | 12 tests covering R1..R8 + CLI dry-run + no-shell-True threat test |

### Modified

| Path | Change |
| ---- | ------ |
| `src/utils/csv_logger.py` | + `RESULTS_INDEX_COLUMNS` (12-col schema) + `results_index_append(path, row)` helper. `CSVLogger` class untouched. |
| `src/utils/wandb_logger.py` | Phase 3 `except Exception:` split into `except _WandbErr:` (offline fallback + `[wandb] offline fallback` print + cascaded noop) and `except Exception:` (silent noop). `_WandbErr = getattr(getattr(wandb, 'errors', None), 'Error', Exception)`. |
| `src/train.py` | `parse_args` gains `--run-name` arg (default=None). `main()` run_dir line becomes `args.run_name if args.run_name else run_name(cfg)`. |
| `tests/test_wandb_logger.py` | + `test_offline_fallback_on_errors_error` + `test_offline_fallback_second_failure_noops`. Existing 2 disabled-mode tests preserved. |

## Acceptance Criteria

Task 1 (from plan `<acceptance_criteria>`):
- [x] `test -f scripts/wandb_preflight.py` — present
- [x] `grep -q 'WANDB_API_KEY' scripts/wandb_preflight.py` — 5 occurrences
- [x] `grep -q 'wandb login' scripts/wandb_preflight.py` — 2 occurrences
- [x] `grep -q 'def results_index_append' src/utils/csv_logger.py` — 1
- [x] `grep -q 'RESULTS_INDEX_COLUMNS' src/utils/csv_logger.py` — 3
- [x] `grep -q 'os.fsync' src/utils/csv_logger.py` — 3 (existing CSVLogger ctor + log + new results_index_append)
- [x] `grep -q 'wandb.errors.Error\|getattr.*errors.*Error' src/utils/wandb_logger.py` — 3
- [x] `grep -q 'mode=.offline.\|mode=\"offline\"' src/utils/wandb_logger.py` — 3 (docstring + init kwarg + comment)
- [x] `grep -q '\-\-run-name\|run_name.*type=str' src/train.py` — 2
- [x] `grep -q 'args.run_name' src/train.py` — 1
- [x] `grep -q 'def test_preflight_env_var_set' tests/test_wandb_preflight.py` — 1
- [x] `grep -q 'def test_preflight_missing_credentials_actionable' tests/test_wandb_preflight.py` — 1
- [x] `grep -q 'def test_append_writes_header_first' tests/test_results_index.py` — 1
- [x] `grep -q 'def test_done_marker_atomic_write' tests/test_done_marker.py` — 1
- [x] `pytest tests/test_wandb_preflight.py tests/test_results_index.py tests/test_done_marker.py -x` exits 0 (13/13 pass)

Task 2 (from plan `<acceptance_criteria>`):
- [x] `test -f scripts/run_ablations.py` — present
- [x] `grep -q 'QUEUES' scripts/run_ablations.py` — 3 occurrences
- [x] `grep -q 'rtfm_gate' scripts/run_ablations.py` — 5 (queue key + 2 docstring + 2 comment)
- [x] `grep -q 'phase4_main' scripts/run_ablations.py` — 5
- [x] `grep -q 'phase4_pooling' scripts/run_ablations.py` — 3
- [x] `grep -q 'phase4_seeds' scripts/run_ablations.py` — 5
- [x] `grep -q 'is_done' scripts/run_ablations.py` — 2 (def + call site)
- [x] `grep -q 'class RunSpec' scripts/run_ablations.py` — 1
- [x] `grep -q 'def run_one' scripts/run_ablations.py` — 1
- [x] `grep -q 'results_index_append' scripts/run_ablations.py` — 4
- [x] `grep -q 'runner-errors.log' scripts/run_ablations.py` — 4
- [x] `grep -q 'wandb_preflight' scripts/run_ablations.py` — 2
- [x] `grep -c 'shell=True' scripts/run_ablations.py` = 0 (T-04-05-01 satisfied)
- [x] `grep -q 'def test_queue_definitions' tests/test_run_ablations.py` — 1
- [x] `grep -q 'def test_skip_if_done' tests/test_run_ablations.py` — 1
- [x] `grep -q 'def test_run_one_success_appends_index' tests/test_run_ablations.py` — 1
- [x] `grep -q 'def test_run_one_train_failure_logs_and_continues' tests/test_run_ablations.py` — 1
- [x] `pytest tests/test_run_ablations.py -x` exits 0 (12/12 pass)

## Test Results

- **Plan 04-05 new tests:** 32 green (3 wandb_preflight + 7 results_index + 3 done_marker + 12 run_ablations + 2 new wandb_logger offline fallback + 2 pre-existing wandb_logger + 3 train-related tests).
- **Full Phase 4 regression:** 107 tests green (no regressions) across test_wandb_preflight + test_results_index + test_done_marker + test_run_ablations + test_wandb_logger + test_train + test_config + test_config_hash + test_test_loader + test_eval_metrics + test_evaluate_cli + test_snippet_to_frame + test_ucf_annotations + test_dataset + test_skel_agg + test_verify_pooling. Two sklearn warnings from `test_per_category_single_class_skipped` are pre-existing (Plan 04-02) and unrelated.

## Manual Verification

- **CLI dry-run end-to-end:**
  ```
  $ python scripts/run_ablations.py --queue rtfm_gate --dry-run --no-preflight
  [dry-run] would run xd_i3d_rtfm_i3d_s42
  {
    "succeeded": [],
    "skipped": [],
    "failed": []
  }
  ```
- **--help exposes all 4 queues + overrides:** `{rtfm_gate, phase4_main, phase4_pooling, phase4_seeds}` all listed under `--queue`; `--dry-run`, `--no-preflight`, `--results-root` all present.
- **--run-name on train.py:** `python src/train.py --help` shows `--run-name RUN_NAME` with D-30 help text.

## Decisions Made

- **Module-top import of `results_index_append`** (not inside `run_one`) — discovered as an auto-fix during Task 2 GREEN verification. See Deviations below.
- **12-column RESULTS_INDEX_COLUMNS schema fixed and ordered** — pandas-reads cleanly without header-shifting even as future rows land, and human inspection of the CSV is deterministic.
- **`--results-root` CLI override** for test isolation — every test redirecting results/ to `tmp_path` also gets runner-errors.log inside that tmp_path (single `_err_log_path(cli_override)` helper). No test ever writes into the real repo `results/` or `runner-errors.log`.
- **D-40 `getattr(..., 'Error', Exception)` version-agnostic catch** — different wandb package versions expose `wandb.errors.Error` differently. Evaluating at runtime keeps the catch behavior consistent across `wandb>=0.12` through current.
- **`phase4_seeds` excludes seed=42** — the seed=42 gated_fusion run lives in `phase4_main`. Duplicating it in phase4_seeds would waste 1 full training pass; the `QUEUES` comment documents this invariant explicitly.
- **`rtfm_gate` is a queue of 1 by itself** (not merged into `phase4_main`) — Plan 06 runs `rtfm_gate` first as a harness-quality gate. If it fails the ±1% AP threshold, Plan 06 aborts before spending 6+ hours on main ablations. Separate queue = separate invocation = separate abort boundary.
- **Preflight is subprocess-invoked, not imported.** The runner uses `subprocess.run([sys.executable, 'scripts/wandb_preflight.py'])` instead of `from scripts.wandb_preflight import main`. Rationale: the preflight script exits the whole process on failure; invoking it as a subprocess means its `raise SystemExit(main())` exit-code check is surfaced via `returncode` without affecting the runner's process state.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `results_index_append` import inside `run_one` triggers torch-import-under-mock**

- **Found during:** Task 2 GREEN verification (initial test run after scripts/run_ablations.py creation).
- **Issue:** The plan's reference code put `from src.utils.csv_logger import results_index_append` inside `run_one` (late import, after `subprocess.run` mocking). But `src.utils.__init__.py` eagerly imports `src.utils.seed` which imports `torch`. On Windows, `import torch` runs `platform.machine()` which internally calls `subprocess.check_output(['cmd', '/c', 'ver'])`. The pytest `monkeypatch.setattr(run_ablations.subprocess, 'run', fake_run)` intercepts that call; `fake_run` returns a custom `_R` object without a `stdout` attribute; `check_output` raises `AttributeError: '_R' object has no attribute 'stdout'`.
- **Fix:** Moved `from src.utils.csv_logger import results_index_append` to the module top of `scripts/run_ablations.py`, with `sys.path` insertion beforehand. This forces torch to load at module-load time (before tests monkeypatch subprocess.run), so `platform.machine()` runs against the real subprocess module. Added a comment block explaining why.
- **Files modified:** `scripts/run_ablations.py` (top-of-module import + comment; removed late import inside run_one).
- **Verification:** 12/12 Task 2 tests now green; full 107-test Phase 4 suite green.
- **Committed in:** `082a51e` (Task 2 GREEN commit — fix included in the initial commit, no separate rework commit needed).

### Rules 2/3/4

No other deviations. No architectural questions arose. No missing critical functionality (the plan's Task 1 provided a complete W4/W5 offline-fallback behavior spec which I implemented verbatim). No Phase 3 tests regressed.

## Authentication Gates

None encountered. This plan ships the orchestration infrastructure; actual authentication (wandb.init) happens during Plan 06's empirical runs. `scripts/wandb_preflight.py` is the fail-fast check that WILL hit an auth gate on first queue run — Plan 06 must either `export WANDB_API_KEY=<key>` or `wandb login` interactively before running the non-dry-run queue. This is documented in the preflight's exit-2 stderr message ("Run one of: (1) export WANDB_API_KEY=... (2) wandb login").

## Known Stubs

None. All plan behaviors implemented to spec. The `--no-preflight` CLI flag is intentional (for unit tests + CSV-only mode), not a stub.

## Threat Mitigations Applied

| Threat ID | Mitigation Implemented | Evidence |
|-----------|------------------------|----------|
| T-04-05-01 (EoP via subprocess shell=True) | All `subprocess.run` calls use argv list; 0 occurrences of `shell=True` | `test_no_shell_true` greps the source; passes. Manual `grep -c 'shell=True' scripts/run_ablations.py` = 0. |
| T-04-05-02 (Info disclosure via secrets in logs) | `runner-errors.log` contains only spec.run_name + exc_repr, never env vars; preflight prints "env var set" boolean, not the value | Inspection of `log_error` and `wandb_preflight.main`. No code path embeds `os.environ` or `WANDB_API_KEY` value into logs. |
| T-04-05-03 (DoS via stdin-blocking wandb wizard) | `scripts/wandb_preflight.py` fails fast before queue opens; `run_ablations.main` exits 2 on preflight failure | Test W2 verifies the exit-2 path; runner's `if preflight.returncode != 0: return 2` covers the orchestrator's own abort. |
| T-04-05-04 (Tampering via concurrent CSV writes) | Single-writer serial queue by design; `flush` + `os.fsync` after every row | `results_index_append` implementation + unit tests (test_append_second_row_no_duplicate_header asserts 2 rows + header unchanged). |
| T-04-05-06 (Spoofing via `--run-name` path traversal) | Accept per plan: researcher-owned; D-30 format is internally constrained | No input validation added; documented in docstring. |

T-04-05-05 (runaway training) — 7200s train timeout + 1800s eval timeout per spec. Queue exits cleanly on timeout.

## Issues Encountered

- **`platform.machine()` calls `subprocess.run` inside `import torch`.** On Windows, this hits pytest monkeypatches if `subprocess.run` is patched before `import torch` finishes. Fixed by moving `from src.utils.csv_logger import results_index_append` to the module top of `scripts/run_ablations.py` so torch loads first. Documented above as auto-fix deviation #1.

No other issues encountered.

## User Setup Required

None for this plan itself. The preflight check inside `run_ablations.py` will require user setup at Plan 06 time:
- **Option A:** `export WANDB_API_KEY=<key>` in the shell running the queue (one-time per shell)
- **Option B:** `wandb login` (interactive one-time — wandb writes to `~/.netrc`)
- **Option C:** Set `wandb.mode: disabled` in every config YAML (CSV-only mode)

Any option satisfies the D-39 preflight gate.

## Next Phase Readiness

- **Plan 04-06 ready to execute.** Plan 06 invokes the 4 queues in order:
  1. `python scripts/run_ablations.py --queue rtfm_gate` — gates on ±1% AP.
  2. `python scripts/run_ablations.py --queue phase4_main` — 4 UCF single-seed ablations.
  3. Re-extract pooling caches (scripts/extract_ctrgcn.py --keep-persons + scripts/extract_clip.py --pool mean), then `scripts/verify_pooling_caches.py`, then `python scripts/run_ablations.py --queue phase4_pooling`.
  4. `python scripts/run_ablations.py --queue phase4_seeds` — 2 gated_fusion seed repeats (123 + 2024).
- **Plan 04-07 ready** to UAT-review `results/results-index.csv` (expected 9 rows after queues 1-4 complete).
- **Phase 5 TTA ready** to consume `results/ucf_gated_fusion_s42/best_model.pth` as the canonical adaptation target — deterministic run_name format locks in the handoff path.
- **No blockers.**

## Threat Flags

None. The orchestrator creates no new network endpoints, no new auth paths, no new schema at trust boundaries. `subprocess.run` with argv-list stays inside the existing Phase 3 trust boundary (Python interpreter + project configs + local filesystem).

## Self-Check: PASSED

All 4 task commits exist in git log:
- `2146607` test(04-05): add failing RED tests for Task 1 — **FOUND**
- `1b39184` feat(04-05): wandb preflight + results_index_append + --run-name + offline fallback — **FOUND**
- `5c64aed` test(04-05): add failing RED tests for run_ablations orchestrator — **FOUND**
- `082a51e` feat(04-05): run_ablations.py orchestrator with 4 queues + resume + audit — **FOUND**

All 6 created files exist on disk:
- `scripts/wandb_preflight.py` — **FOUND**
- `scripts/run_ablations.py` — **FOUND**
- `tests/test_wandb_preflight.py` — **FOUND**
- `tests/test_run_ablations.py` — **FOUND**
- `tests/test_results_index.py` — **FOUND**
- `tests/test_done_marker.py` — **FOUND**

All 4 modified files reflect the plan contract:
- `src/utils/csv_logger.py` — `def results_index_append` + `RESULTS_INDEX_COLUMNS` present; `CSVLogger` class unchanged
- `src/utils/wandb_logger.py` — `wandb.errors.Error` catch + `mode="offline"` fallback + `[wandb] offline fallback` print
- `src/train.py` — `--run-name` in parse_args; `args.run_name if args.run_name else run_name(cfg)` override in main
- `tests/test_wandb_logger.py` — 2 new offline-fallback tests; existing 2 disabled-mode tests preserved

Test counts:
- `tests/test_wandb_preflight.py` — 3 tests, 3 pass
- `tests/test_results_index.py` — 7 tests, 7 pass
- `tests/test_done_marker.py` — 3 tests, 3 pass
- `tests/test_run_ablations.py` — 12 tests, 12 pass
- `tests/test_wandb_logger.py` — 4 tests (2 + 2 new), 4 pass
- Broader Phase 4 suite (16 modules) — 107 tests pass, 0 fail

---
*Phase: 04-baseline-evaluation-main-results*
*Completed: 2026-04-15*
