---
phase: 03-model-architecture-training-infrastructure
plan: 01
subsystem: shared-primitives
tags: [phase-3, foundation, wave-1, tdd, pytest-scaffold, seed, mil-head, model-registry]
requires:
  - Phase 1 src/ layout (D-02): src/models/, src/utils/, tests/
  - Phase 1 tests/conftest.py: original weight_dir, pyskl_config_dir, splits_dir fixtures (preserved verbatim)
  - Phase 2 feature cache contracts: skeleton [N,256] (D-05), CLIP [N,1024] (D-06)
  - CLAUDE.md technology stack: PyTorch 2.6.0+cu124, Python 3.11, numpy 2.4.3
provides:
  - set_deterministic(seed): 4-KNOB deterministic training (src.utils)
  - seed_worker(worker_id): Windows-spawn-safe DataLoader init_fn (module-level, picklable)
  - make_generator(seed): seeded torch.Generator for DataLoader shuffle
  - MILHead(D, hidden_dims=(128,32), dropout=0.3): shared 3-layer MLP head per D-05/D-06
  - MODEL_REGISTRY: 4-key lazy factory dict (skeleton_only, clip_only, late_fusion, gated_fusion)
  - build_model(variant, **kwargs): variant dispatcher per D-16
  - Pytest scaffold: synth_skel_features/synth_clip_features/synth_batch/tmp_feature_dir/smoke_cfg/feature_dir_ucf fixtures + e2e/requires_features markers
affects:
  - Plans 02-07: will import MILHead, set_deterministic, seed_worker, make_generator; use synth_* fixtures; extend pytest markers
  - Plan 04 (skeleton_only, clip_only): must delete or update tests/test_registry.py::test_build_model_lazy_import_not_ready
  - Plan 05 (late_fusion, gated_fusion): will import MILHead for shared-head-by-construction guarantee (D-06)
tech-stack:
  added:
    - pytest==7.4.4 (pinned in requirements-main.txt; env has 9.0.2 — pin aspirational)
    - pytest-timeout==2.3.1 (guard against runaway e2e tests)
  patterns:
    - TDD RED -> GREEN commit split (test commit precedes implementation commit)
    - Lazy factory imports in registry (registry importable before Plan 04/05 lands)
    - Module-level worker init_fn (Windows spawn pickling contract)
    - Collection guard via conftest.collect_ignore_glob based on optional import (mmcv)
key-files:
  created:
    - pyproject.toml (pytest config only — no [build-system] per plan)
    - tests/fixtures/__init__.py
    - tests/fixtures/synthetic.py (make_skel, make_clip, make_batch)
    - tests/test_seed.py (6 tests)
    - tests/test_mil_head.py (6 tests)
    - tests/test_registry.py (3 tests)
    - src/utils/seed.py (set_deterministic, seed_worker, make_generator)
    - src/models/mil_head.py (MILHead)
    - src/models/registry.py (MODEL_REGISTRY, build_model)
  modified:
    - src/utils/__init__.py (re-exports seed helpers)
    - src/models/__init__.py (re-exports MILHead + registry)
    - tests/conftest.py (6 new fixtures + collect_ignore_glob for mmcv-absent envs)
    - envs/requirements-main.txt (added pytest, pytest-timeout; header updated)
decisions:
  - D-05 + D-06 shared head: MILHead fixes hidden widths (128, 32) and dropout 0.3 at the class level so all 4 variants are byte-identical in head architecture
  - Lazy-factory registry: tests can import MODEL_REGISTRY before Plan 04/05 implementation files exist (enables parallel wave work)
  - warn_only=True for use_deterministic_algorithms: CONTEXT.md Claude's Discretion default; Plan 06 bit-identical regression test will catch if any Phase 3 op accidentally hits non-deterministic list
  - CUBLAS_WORKSPACE_CONFIG (KNOB 4) documented but NOT set in seed.py: it must be set before `import torch` in the entry point; seed.py is imported after torch and cannot fix it in-place
  - Pytest 9.0.2 in vcc-main env, 7.4.4 pinned: requirements-main.txt is a reference document per STATE.md; pin documents the tested/supported version
  - conftest.collect_ignore_glob for mmcv: test_ctrgcn_smoke.py is vcc-ctrgcn-only; blocking collection in vcc-main (Phase 3 training env) was blocking Task 1 verification. Additive conftest change preserves the Phase 2 test file unchanged (plan constraint: no Phase 1/2 file modifications beyond conftest.py/requirements-main.txt)
metrics:
  duration: 6 min 22 sec
  completed: 2026-04-14T08:12:55Z
  tasks_executed: 3
  commits: 4
  files_created: 9
  files_modified: 3
  tests_added: 15
  tests_passing: 15
  lines_added: 278
---

# Phase 3 Plan 1: Shared Primitives Summary

Installs the single source of truth for Phase 3: deterministic seeding (TRN-03), shared MIL head (D-05 + D-06), model registry (D-16), and the pytest scaffold (fixtures, synthetic-feature generators, markers) that Plans 02-07 will extend.

## What Landed

### 1. Deterministic seeding (TRN-03)

`src/utils/seed.py` (59 lines):

- `set_deterministic(seed=42)`: seeds `random`, `numpy`, `torch`, `torch.cuda`; flips `cudnn.deterministic=True`, `cudnn.benchmark=False`; calls `torch.use_deterministic_algorithms(True, warn_only=True)`
- `seed_worker(worker_id)`: module-level function (NOT a lambda) so Windows `spawn` multiprocessing can pickle it for DataLoader workers
- `make_generator(seed)`: returns a seeded `torch.Generator` for DataLoader shuffle reproducibility
- KNOB 4 (`CUBLAS_WORKSPACE_CONFIG=:4096:8`) documented in module docstring but NOT set by this module — it must be set before `import torch` in the entry point (`src/train.py`, Plan 07)

Covers RESEARCH.md section 2.1 (the 4-KNOB list) and addresses pitfall C3 partially (seed determinism for test-set-leakage prevention via reproducible val/train splits).

### 2. Shared MIL head (D-05, D-06)

`src/models/mil_head.py` (35 lines):

`MILHead(input_dim, hidden_dims=(128,32), dropout=0.3)` -> `Linear(D -> 128) -> ReLU -> Dropout(0.3) -> Linear(128 -> 32) -> ReLU -> Dropout(0.3) -> Linear(32 -> 1) -> Sigmoid`

Broadcasts over leading dims so it accepts both `[B, T, D]` (training, with T time snippets) and `[B, D]` (inference). Returns `[..., 1]` scores in `[0, 1]`.

This is the single class that Plans 04 (skeleton_only, clip_only) and 05 (late_fusion, gated_fusion) will all import. Head architecture is identical across variants by construction — the "same head, different body" guarantee behind D-06 is now code-level, not convention-level.

### 3. Model registry (D-16)

`src/models/registry.py` (50 lines):

- `MODEL_REGISTRY`: dict with 4 string keys -> lazy factory callables. Each factory imports the class on first call, so `registry.py` is importable BEFORE `src/models/skeleton_only.py` (Plan 04) and `src/models/gated_fusion.py` (Plan 05) exist
- `build_model(variant, **kwargs)`: dispatches via the registry; raises `ValueError("Unknown variant '{x}'. Valid: [...]")` on unknown variants

Lazy-factory pattern enables Wave 1 parallelization: Plans 02, 03, 04, 05, 06, 07 can import the registry without pulling in every variant's imports.

### 4. Pytest scaffold

- `pyproject.toml` (root, new): `[tool.pytest.ini_options]` section ONLY. No `[build-system]`, no `[tool.ruff]`, no `[tool.mypy]` — out of Phase 3 scope per CONTEXT.md.
- Markers registered: `e2e` (slow end-to-end tests), `requires_features` (tests needing `E:/features/ucf/*.npy`)
- `tests/fixtures/synthetic.py`: `make_skel(N)`, `make_clip(N)`, `make_batch(B_nor, B_abn, T)` — deterministic per seed, shapes match Phase 2 cache contracts exactly
- `tests/conftest.py` extended with 6 new fixtures: `feature_dir_ucf` (skips if E:/ absent), `tmp_feature_dir`, `synth_skel_features`, `synth_clip_features`, `synth_batch`, `smoke_cfg` (minimal training config dict)
- `tests/conftest.py` also adds `collect_ignore_glob` to skip `test_ctrgcn_smoke.py` when `mmcv` is not importable (vcc-main does not have mmcv; vcc-ctrgcn does)

## D-XX Coverage

| Requirement / Decision | Artifact | Status |
|------------------------|----------|--------|
| TRN-03 (deterministic training) | `src/utils/seed.py:set_deterministic`, `seed_worker`, `make_generator` | KNOBs 1-3 covered; KNOB 4 documented for Plan 07 train.py |
| D-05 (shared head + Dropout 0.3) | `src/models/mil_head.py:MILHead.__init__ dropout=0.3` | covered |
| D-06 (hidden widths 128, 32) | `src/models/mil_head.py:MILHead.__init__ hidden_dims=(128, 32)` | covered |
| D-16 (string-based registry) | `src/models/registry.py:MODEL_REGISTRY + build_model` | covered |
| MOD-03, MOD-04, MOD-05, MOD-06 | Registry pre-registers all 4 keys (lazy) | partial — Plans 04/05 add the actual class files |

## Fixtures Available to Downstream Plans

Plans 02-07 can `import pytest` and expect these fixtures in scope:

| Fixture | Returns | Use |
|---------|---------|-----|
| `synth_skel_features` | callable(N, seed) -> np.ndarray[N, 256] float32 | unit tests for skeleton encoders |
| `synth_clip_features` | callable(N, seed) -> np.ndarray[N, 1024] float32 | unit tests for CLIP encoders |
| `synth_batch` | callable(B_nor, B_abn, T, seed) -> dict with keys skel/clip/mask/label | MIL loss / model forward pass tests |
| `tmp_feature_dir` | Path with `skeleton/` + `clip/` subdirs | dataset loader unit tests |
| `smoke_cfg` | dict with seed/paths/model/data/train/wandb | integration smoke tests (Plan 07) |
| `feature_dir_ucf` | Path or skips | integration tests marked `@pytest.mark.requires_features` |

## Hand-offs to Later Plans

- **Plan 04** (skeleton_only + clip_only): the existing test `tests/test_registry.py::test_build_model_lazy_import_not_ready` asserts `ModuleNotFoundError` when `build_model("skeleton_only", skel_dim=256)` is called — because `src/models/skeleton_only.py` does not yet exist. When Plan 04 creates that file, the test will fail. Plan 04 MUST delete or update this test. The test is marked inline with `# PLAN-04 REMOVES THIS` so the executor sees the hand-off explicitly.
- **Plan 05** (late_fusion, gated_fusion): analogous — `build_model("late_fusion", ...)` and `build_model("gated_fusion", ...)` will flip from `ModuleNotFoundError` to success when those files land; Plan 05 will add positive-path tests (`test_build_model_late_fusion`, `test_build_model_gated_fusion`) and drop the lazy-import-not-ready check as test_build_model_lazy_import_not_ready degrades.
- **Plan 07** (train.py): must set `os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'` as the FIRST line before any `import torch`. `set_deterministic` alone is not enough; KNOB 4 cannot be set after torch is imported.
- **Plan 06** (reproducibility regression test): run the 2-epoch smoke twice with the same seed and `assert torch.equal` on final model weights. If this fails, the warn_only=True fallback was triggered — investigate which op hit a non-deterministic kernel.

## Verification Evidence

```
$ python -m pytest tests/test_seed.py tests/test_mil_head.py tests/test_registry.py -v
=============== 15 passed in 2.38s ===============

$ python -m pytest tests/test_splits.py --collect-only -q
9 tests collected (no regressions)

$ python -c "from src.models import MILHead, MODEL_REGISTRY, build_model; from src.utils import set_deterministic, seed_worker, make_generator; print('imports ok')"
imports ok

$ python -m pytest --markers | grep -E "e2e|requires_features"
@pytest.mark.e2e: end-to-end acceptance tests ...
@pytest.mark.requires_features: tests that require E:/features/ucf/*.npy ...

$ python -m pytest --fixtures | grep -E "synth_|tmp_feature_dir|smoke_cfg|feature_dir_ucf"
feature_dir_ucf -- tests\conftest.py:44
tmp_feature_dir -- tests\conftest.py:53
synth_skel_features -- tests\conftest.py:61
synth_clip_features -- tests\conftest.py:68
synth_batch -- tests\conftest.py:75
smoke_cfg -- tests\conftest.py:82
```

## Pip Install Commands (if Env Is Fresh)

```
C:/Anaconda/envs/vcc-main/python.exe -m pip install pytest==7.4.4 pytest-timeout==2.3.1
```

The current vcc-main env has pytest 9.0.2 already (plan pins 7.4.4; acceptable drift since tests pass under both versions — the pin documents the tested version for future resurrection).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Collection guard for mmcv-absent env (vcc-main)**

- **Found during:** Task 1 verification (`pytest --collect-only` failed)
- **Issue:** Pre-existing Phase 2 file `tests/test_ctrgcn_smoke.py` imports `from mmcv import Config`. mmcv exists only in `vcc-ctrgcn` env, not `vcc-main`. `pytest --collect-only` in vcc-main failed with `ModuleNotFoundError: No module named 'mmcv'`, blocking Task 1 acceptance criterion "`python -m pytest tests/ --collect-only` exits 0".
- **Fix:** Added `collect_ignore_glob` in `tests/conftest.py` that conditionally skips `test_ctrgcn_smoke.py` when `importlib.util.find_spec("mmcv") is None`. This preserves the Phase 2 test file unchanged (plan constraint) while making Task 1 verification pass. When running in vcc-ctrgcn, mmcv is present and the test is collected as before.
- **Files modified:** `tests/conftest.py` (additive — new conditional module-level block)
- **Commit:** 009c40d (rolled into Task 1 commit)

**2. [Pin drift — not auto-fixed]** Pytest 9.0.2 is installed in vcc-main; plan pins 7.4.4 in requirements-main.txt. Per plan explicitly: "requirements-main.txt is a reference document per STATE.md". The pin documents the tested version; the active env can run newer pytest since the 7.x -> 9.x API surface used here (`--collect-only`, `--markers`, `--fixtures`, `[tool.pytest.ini_options]`) is stable across both. Not flagged as an issue.

### Architectural Changes

None.

### Authentication Gates

None.

## Known Stubs

None introduced by this plan. Pre-existing stub in `src/tta/__init__.py` (1-line placeholder deferring TENT/SAR to Phase 5) is out of scope for Plan 03-01.

## Threat Flags

No new security surface introduced. Threat register items T-03-01-01 through T-03-01-04 from the plan have their dispositions preserved:
- T-03-01-01 (mitigate): pip pins locked in requirements-main.txt
- T-03-01-02 (accept): warn_only=True fallback documented; Plan 06 adds regression test
- T-03-01-03 (accept): synthetic tensors only
- T-03-01-04 (accept): pytest collect-only runs < 3s

## Commit Lineage

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| 1 | `009c40d` | feat | pytest scaffold: pyproject.toml, 6 new fixtures, synthetic feature generators, collect_ignore_glob for mmcv-absent env |
| 2-RED | `37f479b` | test | 15 failing tests for seed/MILHead/registry (modules don't exist yet) |
| 2-GREEN | `d9825c6` | feat | implementation: set_deterministic, MILHead, MODEL_REGISTRY + build_model; 15/15 tests pass |
| 3 | `c198e2b` | chore | pin pytest==7.4.4, pytest-timeout==2.3.1 in requirements-main.txt |

## Self-Check: PASSED

Created files verified:
- pyproject.toml: FOUND
- tests/fixtures/__init__.py: FOUND
- tests/fixtures/synthetic.py: FOUND
- tests/test_seed.py: FOUND
- tests/test_mil_head.py: FOUND
- tests/test_registry.py: FOUND
- src/utils/seed.py: FOUND
- src/models/mil_head.py: FOUND
- src/models/registry.py: FOUND

Commits verified:
- 009c40d: FOUND
- 37f479b: FOUND
- d9825c6: FOUND
- c198e2b: FOUND
