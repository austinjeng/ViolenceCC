# Coding Conventions

**Analysis Date:** 2026-06-09

This is a single-researcher PyTorch research codebase. Conventions favor reproducibility, crash-safety, and debuggability by one person over abstraction. Many conventions are codified in `CLAUDE.md` and must be followed exactly.

## Naming Patterns

**Files:**
- Source modules: lowercase `snake_case` — `mil_head.py`, `gated_fusion.py`, `disc_reweight.py`, `csv_logger.py`
- Test modules: `test_<unit>.py` — `test_mil_head.py`, `test_disc_reweight.py`, `test_reproducibility.py` (matches `python_files = ["test_*.py"]` in `pyproject.toml`)
- Configs: `<variant>.yaml` / `<variant>_<dataset>.yaml` — `clip_only.yaml`, `clip_only_xd.yaml`, `gated_fusion.yaml` under `configs/`
- Scratch / scratch-experiment scripts use a `_tmp_` or leading-underscore prefix — `scripts/_tmp_r1_full.py`, `scripts/_check_citations.py` (these are NOT part of the committed test/CI surface)

**Functions:**
- `snake_case` — `set_deterministic`, `seed_worker`, `make_generator`, `snapshot_config`, `config_hash`, `checkpoint_sha`, `results_index_append`
- Module-private helpers prefixed with single underscore — `_git_info`, `_get_version`, `_pip_freeze`, `_make_cfg`, `_read_losses`, `_latest`
- Test functions: `test_<behavior>` — `test_mil_head_output_shape_3d`, `test_compute_w_vl_collapsed_skel_clean`

**Variables:**
- `snake_case` for locals — `worker_seed`, `cfg_path`, `train_nor`, `val_abn`
- Module-level constants in `UPPER_SNAKE` — `PROJECT_ROOT`, `RESULTS_INDEX_COLUMNS`

**Types / Classes:**
- `PascalCase` — `MILHead`, `GatedFusion`, `CSVLogger`, `SarAdaptor`, `SAM` (acronym classes stay upper)

## Code Style

**Formatting:**
- No autoformatter config is committed (no `.prettierrc`, `ruff.toml`, `.black.toml`, `setup.cfg`, or `.pre-commit-config.yaml` present). `pyproject.toml` contains ONLY a `[tool.pytest.ini_options]` block.
- De-facto style is Black-compatible: 4-space indent, double quotes, trailing commas in multi-line literals.
- Module-level docstrings are mandatory and tie the file back to a requirement ID (e.g. `"""Deterministic training reproducibility (TRN-03)."""`, `"""MOD-03/04/05/06 shared head (D-05, D-06)."""`).

**Linting:**
- No linter is enforced. Match surrounding style by hand. Do not introduce a linter/formatter without being asked.

**Type hints:**
- `from __future__ import annotations` at the top of most modules (`seed.py`, `config.py`, `csv_logger.py`, `disc_reweight.py`, `test_reproducibility.py`).
- Public functions are type-annotated, including return types: `def set_deterministic(seed: int = 42) -> None:`, `def config_hash(cfg: dict) -> str:`.
- `Union[str, Path]` used for path-accepting APIs (Python 3.11 target, but `Union` style retained for consistency).

## Import Organization

**Order (observed across `src/utils/` and `tests/`):**
1. `from __future__ import annotations`
2. Standard library — `import csv`, `import os`, `import hashlib`, `from pathlib import Path`
3. Third-party — `import numpy as np`, `import torch`, `import torch.nn as nn`, `import pytest`, `import yaml`
4. First-party — `from src.models.mil_head import MILHead`, `from src.tta.disc_reweight import compute_w`

**Path bootstrapping in tests / scripts:**
Several test files and scripts insert the repo root onto `sys.path` before first-party imports:
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```
Resolve `PROJECT_ROOT` from `__file__` — never hardcode `D:/ViolenceCC` (a hardcoded path previously broke git-worktree pytest runs; see `tests/conftest.py` lines 5-9).

**No path aliases** (this is plain Python, not a bundler project). Imports are absolute from the `src.` package root.

## Reproducibility Conventions (CORE — non-negotiable)

Reproducibility is a hard project constraint (`CLAUDE.md`: fixed seeds, same splits, same eval protocol). Honor all of the following.

**Fixed seed set:** `{42, 123, 2024}`. 42 is the default everywhere (`set_deterministic(seed: int = 42)` in `src/utils/seed.py`); multi-seed results use all three.

**Four determinism knobs** (`src/utils/seed.py`, documented in its docstring):
1. Seed `torch` + `numpy` + `random` + CUDA RNGs (`set_deterministic`).
2. `torch.backends.cudnn.deterministic = True`, `cudnn.benchmark = False`.
3. `torch.use_deterministic_algorithms(True, warn_only=True)`.
4. `CUBLAS_WORKSPACE_CONFIG=:4096:8` MUST be set BEFORE `import torch` in the entry point (`src/train.py`). `seed.py` cannot set it (too late). If you see a `RuntimeError` from `torch.mm/bmm`, this env var is missing.

**DataLoader determinism:** use `seed_worker` as `worker_init_fn` and a seeded `make_generator(seed)` for shuffling (`src/utils/seed.py`). `seed_worker` MUST stay module-level (not a lambda) so Windows `spawn` can pickle it.

**Per-run config snapshot:** every run writes `config_snapshot.json` via `snapshot_config(cfg, path)` (`src/utils/config.py`). It captures resolved config + git sha/dirty + python/torch/numpy/cuda versions + key env vars + an in-process `pip freeze`. A run can be re-launched bit-identically with:
```bash
python src/train.py --config results/<prior_run>/config_snapshot.json
```
`load_config()` detects `.json` snapshots and extracts the `config` sub-dict.

**Stable provenance hashes** (`src/utils/config.py`, D-12): `config_hash(cfg)` (SHA256 of `sort_keys=True` JSON — whitespace/order invariant), `checkpoint_sha(path)` (streamed 1 MB chunks, never loads whole file), `git_sha()` (HEAD + `-dirty` suffix, returns `"unknown"` if git absent). Running `evaluate.py` twice on the same `run_dir` must yield byte-identical non-clock keys in `eval_metrics.json`.

**Append-only results audit log:** `results/results-index.csv`, written one row per completed run by `results_index_append(path, row)` (`src/utils/csv_logger.py`). Schema is the FIXED `RESULTS_INDEX_COLUMNS` list (run_name, variant, dataset, seed, cache_variant, auc, ap, n_videos, n_frames, start_time, end_time, config_hash, + TTA columns method/corruption_type/severity/lr/rho). Missing keys are written as empty strings — schema stability matters more than row completeness for post-hoc pandas analysis. Never reorder or rename columns.

**Crash-safe CSV writes:** both `CSVLogger.log()` and `results_index_append()` do `f.flush()` + `os.fsync(f.fileno())` per row, and write the header only on first/empty open. A crash at epoch 17 still leaves epochs 0-16 on disk. Preserve this pattern for any new run-log writer.

## DataLoader Conventions (CLAUDE.md)

- **Val loaders MUST use `shuffle=True`** to prevent single-class batch bias in the MIL ranking loss (`validate()` skips single-class batches). See `src/data/loaders.py`.
- Train loaders are already paired (separate normal / abnormal bags), so their shuffle is correct as-is.

## Checkpoint Loading (CLAUDE.md)

- Always use `strict=True` with `model.load_state_dict()`. `strict=False` silently accepts partial loads and produces misleading metrics.
- If architecture migration is needed, remap keys explicitly — never reach for `strict=False`.
- Checkpoint writes go through `src/utils/checkpoint.py` (Windows-safe atomic write).

## Feature Extraction Conventions (CLAUDE.md — video extraction env)

- Reuse a single `decord.VideoReader` across all snippets of the same video. Do NOT construct a new reader per snippet. (Extraction code lives in the separate `vcc-skeleton` / `vcc-ctrgcn` envs, not in the `src/data` training path.)
- Log decoder failures at WARNING level (not DEBUG) — zero-vector features from failed snippets must be visible at runtime.
- After extraction, log a per-video zero-snippet count so silent degradation is caught.

## Error Handling

- Best-effort provenance helpers never raise: `_git_info()` and `git_sha()` catch `(subprocess.CalledProcessError, FileNotFoundError, OSError)` and return `"unknown"` so a missing git never takes down a run/eval (`src/utils/config.py`).
- `_pip_freeze()` swallows all exceptions and returns `[]` — provenance capture must not break training.
- Prefer explicit narrow `except` tuples over bare `except:` (the broad `except Exception` in `_pip_freeze` is the documented exception).

## Logging & Stub-Metric Warnings (CLAUDE.md)

- When a code path produces placeholder metrics, emit a runtime warning so downstream tooling does not consume stubs as real values.
- Live example in `src/evaluate.py`: the `--split val` path stubs `mil_loss=0.0` and both `print(...)`s a NOTE and `warnings.warn(...)` ONCE (guarded by a `_warned_truncated` flag, lines ~286-310 and ~403-409). Follow this warn-once pattern for any new stub.

## Comments

- Comments explain WHY, and frequently cite a decision/requirement ID (`D-04`, `D-12`, `TRN-03`, `TRN-05`, `RESEARCH.md §6.3`, `Plan 04b-01 Rule 1`) so a future reader can trace the constraint back to a planning doc.
- Heavy use of `# ---` banner separators to section long modules and test files into labeled regions (e.g. `# --- Fixtures ---`, `# --- (b) compute_w unit test ---`).
- Docstrings carry the contract (shapes, units, invariants), e.g. `synthetic.make_batch` documents the exact `{skel, clip, mask, label}` tensor shapes.

## Function & Module Design

- Small, single-purpose functions with explicit returns; helpers kept module-private with a leading underscore.
- Modules avoid importing `torch` at module top when the JSON/path round-trip can be unit-tested torch-free — `snapshot_config` does a local `import torch` inside the function for exactly this reason (`src/utils/config.py` line ~110).
- Exports are implicit (no `__all__`); `__init__.py` files are mostly empty package markers.

## GSD Workflow Enforcement (CLAUDE.md)

Before using Edit/Write or any file-changing tool, work must be initiated through a GSD command so planning artifacts and execution context stay in sync:
- `/gsd:quick` — small fixes, doc updates, ad-hoc tasks
- `/gsd:debug` — investigation and bug fixing
- `/gsd:execute-phase` — planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it. Commit messages and planning artifacts reference the originating task ID (e.g. `quick-260607-42h`).

## Paper / LaTeX Build Convention (CLAUDE.md)

- The CGW '26 paper compiles locally via `scripts/build_paper.ps1` (MiKTeX + Strawberry Perl + latexmk).
- After editing ANY paper LaTeX source (`paper/main.tex`, `paper/references.bib`, `paper/figures/*`, or `paper/.latexmkrc`), recompile a fresh PDF and wipe stale artifacts:
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean
  ```
  `-Clean` runs `latexmk -C` (wipes all build artifacts) then does a full rebuild, so `paper/main.pdf` always reflects the latest edits with no stale intermediates.
- Build artifacts (`paper/main.pdf`, `*.aux/*.bbl/*.blg/*.fdb_latexmk/*.synctex.gz/...`) are git-ignored — NEVER commit them.
- `paper/tables_generated.tex` is NOT `\input` by `main.tex` (tables are inlined); editing it alone does not change the build.

---

*Convention analysis: 2026-06-09*
