---
phase: 04-baseline-evaluation-main-results
plan: 02
subsystem: evaluation
tags: [c3-import-boundary, c4-length-assertion, sys-argv-guard, config-hash, checkpoint-sha, git-sha, evaluate-cli, frame-metrics, tdd, sklearn, atomic-write]

# Dependency graph
requires:
  - phase: 04-baseline-evaluation-main-results
    plan: 01
    provides: "src.eval.snippet_to_frame + src.eval.ucf_annotations (parse_annotations + frame_labels + VideoAnnotation); tests/fixtures/synthetic_eval.make_synthetic_ucf; tests/conftest.py synthetic_ucf_features + ucf_temporal_path fixtures"
  - phase: 03-model-architecture-training-infrastructure
    provides: "MODEL_REGISTRY (gated_fusion); src/utils/checkpoint.load_checkpoint + save_checkpoint_atomic; src/utils/config.load_snapshot_as_config + _git_info; src/utils/seed.set_deterministic"
  - phase: 02-feature-extraction-pipeline
    provides: "MILFeatureDataset(mode='test') path (D-12 full snippets no sampling); data/splits/ucf_test.txt frozen IDs"
provides:
  - "src/eval/test_loader.py — _assert_called_from_evaluate_or_pytest() + build_test_dataset(cfg) dispatcher with 3-way C3 defense (sys.argv[0] sentinel, pytest substring, sys.modules fallback)"
  - "src/eval/metrics.py — compute_frame_metrics(per_video_scores, per_video_labels, per_video_category) + compute_snippet_auc(...); every sklearn call gated by C4 REGRESSION length-equality assertion"
  - "src/evaluate.py — CLI entry point with --run-dir + --split {val|test}; writes eval_metrics.json + eval_scores.npz + per_category.csv + .done atomically in that order"
  - "src/utils/config.py extended: config_hash(cfg) + checkpoint_sha(path) + git_sha() — D-12 reproducibility metadata helpers"
  - "_construct_mil_dataset kwarg-filter bridge — forward-compat plumbing for Plan 04-04 skel_agg extension on MILFeatureDataset"
affects:
  - 04-03 (src/data/i3d_dataset.I3DFeatureDataset + xd_i3d label construction — test_loader + evaluate.py xd_i3d stubs block there)
  - 04-04 (MILFeatureDataset.skel_agg kwarg — _construct_mil_dataset picks it up automatically once __init__ accepts it)
  - 04-05 (scripts/run_ablations.py subprocess-invokes src/evaluate.py + parses eval_metrics.json; .done marker is the D-31 resume probe)
  - 04-06 (empirical run consumes bit-identical re-eval on same checkpoint; SC #4 reproducibility inherited)
  - 05-tta (Phase 5 adapts the same best_model.pth + config_snapshot.json contract that evaluate.py establishes here)
  - 06-visualization (eval_scores.npz per-video frame arrays consumed without re-inference)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sys.argv + sys.modules triple-gate for C3 defense (evaluate.py basename, pytest substring, pytest module fallback for `python -m pytest` __main__.py pattern)"
    - "inspect.signature kwarg-filter for cross-plan forward compatibility (Dataset signature drift over Plans 04-02 → 04-04)"
    - "write-temp-rename atomic file writes via tempfile.mkstemp + os.fsync + os.replace for every evaluation artifact"
    - "Pre-sklearn length-equality assertion with 'C4 REGRESSION' sentinel string (consumable by test suite + grep)"
    - "SHA256 streaming in 1 MB chunks for large checkpoint fingerprinting"
    - "sort_keys=True JSON canonical form + Path->str coercion for config_hash whitespace-invariant identifier"
    - "TDD RED-GREEN discipline at per-task level; commit RED before any implementation, verify failure mode, then commit GREEN"

key-files:
  created:
    - "src/eval/test_loader.py"
    - "src/eval/metrics.py"
    - "src/evaluate.py"
    - "tests/test_test_loader.py"
    - "tests/test_config_hash.py"
    - "tests/test_eval_metrics.py"
    - "tests/test_evaluate_cli.py"
  modified:
    - "src/utils/config.py"

key-decisions:
  - "D-06 implemented: CLI shape --run-dir <path> + --split {val|test} (default=test). Reads best_model.pth + config_snapshot.json from run-dir; writes eval_metrics.json + eval_scores.npz + per_category.csv + .done back into it."
  - "D-07 implemented: src/eval/test_loader.py is a separate module; src/data/dataset.py does NOT import from src.eval.* — import-graph verified via subprocess test (test_no_transitive_import)."
  - "D-08 implemented: module-top _assert_called_from_evaluate_or_pytest() guard raising RuntimeError with 'test-set leakage' substring."
  - "D-09 implemented: --split is explicit, never auto-inferred; default=test. val path takes a MIL-loss-only code path (discretion — full val loss is optional)."
  - "D-10 implemented: only best_model.pth loaded; last_model.pth never touched by evaluate.py."
  - "D-11 implemented: eval_metrics.json keys = {auc, ap, snippet_auc, [video_auc], per_category, n_videos, n_frames} + D-12 metadata keys."
  - "D-12 implemented: config_hash, git_sha, checkpoint_sha, wandb_run_id, dataset, split, seed, eval_timestamp, eval_duration_s all populated in _build_metadata."
  - "D-13 implemented: eval_scores.npz = {video_id: np.ndarray[n_frames]} via np.savez_compressed (default compressed per Discretion)."
  - "D-14 implemented: UCF snippet_window=64, upsample_factor=10 feeds snippet_to_frame; n_frames = N*64*10 gives the 30fps grid matching RTFM/MGFN/VadCLIP."
  - "D-15 implemented: compute_frame_metrics asserts len(y_score) == len(y_true) before every sklearn call with 'C4 REGRESSION' sentinel string."
  - "D-16 implemented: frame_labels from Plan 01 produces union of intervals with end-index clamping; consumed directly by _build_frame_arrays."
  - "D-17 implemented: per_category keyed by Sultani category column (VideoAnnotation.category); Normal is explicitly excluded (`if cat == \"Normal\": continue`)."
  - "D-31 implemented: .done is the LAST write in main(); atomic tempfile.mkstemp + os.fsync + os.replace. Runner probes its presence for skip-if-exists."
  - "D-34 implicit: .done written only AFTER eval_metrics.json.write completes; a crash during eval leaves run incomplete so the runner re-picks it."
  - "Per-category CSV row ordering = alphabetical (Discretion default); Normal omitted (Discretion default)."
  - "Triple-gate sys.argv defense: evaluate.py basename match + pytest/py.test substring + 'pytest' in sys.modules fallback. The sys.modules gate was Rule 1 auto-fix when `python -m pytest` was discovered to produce sys.argv[0]='__main__.py'."
  - "_construct_mil_dataset kwarg-filter: uses inspect.signature(MILFeatureDataset.__init__) to drop kwargs not yet accepted. Lets Plan 04-02 pass skel_agg today without breaking against the pre-Plan-04-04 Dataset; no test_loader edit needed when 04-04 adds the param."

patterns-established:
  - "Pattern: sys.argv + sys.modules triple-gate for restricted modules that must only be reachable from a small closed set of entry points. Direct analog for future 'evaluate-only' helpers."
  - "Pattern: pre-sklearn length assertion with distinguishable sentinel ('C4 REGRESSION') for metric correctness regression catches."
  - "Pattern: write-temp-rename with fsync + os.replace for every JSON/NPZ artifact whose atomic visibility matters (runner probe or future-run input)."
  - "Pattern: inspect.signature-based kwarg-filter bridging cross-plan parameter drift; avoids a SKIP-if-extra default-value pile."
  - "Pattern: config_hash(cfg) = sha256(json.dumps(cfg, sort_keys=True, separators=(',',':'))) with json.dumps(default=str) preconversion — canonical identifier invariant to dict-ordering + whitespace + Path vs str."
  - "Pattern: atomic done-marker LAST (written only when all other outputs exist) — contract for runner skip-if-exists semantics."

requirements-completed:
  - EVAL-02
  - EVAL-03
  - EVAL-04

# Metrics
duration: 13min
completed: 2026-04-15
---

# Phase 4 Plan 02: Evaluation CLI + C3/C4 defenses Summary

**Ships src/evaluate.py (run-dir I/O contract with atomic writes), src/eval/test_loader.py (C3 triple-gate: sys.argv basename + pytest substring + sys.modules fallback catches `python -m pytest` __main__.py pattern), src/eval/metrics.py (compute_frame_metrics with 'C4 REGRESSION' length-assertion before every sklearn call), and D-12 reproducibility helpers (config_hash + checkpoint_sha + git_sha in src/utils/config.py). 17 new tests green including subprocess-level C3 import-boundary + C4 assertion + bit-identical rerun. No regressions in the broader 132-test suite.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-04-15T10:10:27Z
- **Completed:** 2026-04-15T10:23:10Z
- **Tasks:** 2 (each with TDD RED + GREEN)
- **Files modified:** 8 (7 created, 1 edited)

## Accomplishments

- **C3 triple-gate defense** (`src/eval/test_loader.py`): `_assert_called_from_evaluate_or_pytest()` fires at module import and raises `RuntimeError` with the sentinel substring `"test-set leakage"` unless one of three conditions holds: `sys.argv[0]` basename is `evaluate.py`, `sys.argv[0]` contains `pytest`/`py.test`, or the `pytest` module is already in `sys.modules`. The third gate was the Rule 1 auto-fix when `python -m pytest` produced `sys.argv[0]='__main__.py'` which slipped past the first two gates.
- **C3 import-boundary invariant** (`tests/test_test_loader.py::test_no_transitive_import`): subprocess test `python -c "import src.data.dataset; assert 'src.eval.test_loader' not in sys.modules"` — locks in the architectural separation between training data path and test-set loading. A future refactor that transitively pulls `test_loader` into the training graph fails loudly.
- **C4 length-assertion contract** (`src/eval/metrics.py`): every `roc_auc_score` / `average_precision_score` call is preceded by `assert len(s) == len(y), f"C4 REGRESSION at {vid}: scores={len(s)} labels={len(y)}"`. 3 distinct concatenation sites (global, per-category, snippet-grid) all carry the assertion.
- **D-12 reproducibility metadata helpers** (`src/utils/config.py`): `config_hash(cfg)` SHA256 of sorted-key JSON with Path→str coercion (whitespace + order invariant); `checkpoint_sha(path)` SHA256 streamed in 1 MB chunks (RAM-safe for 100+ MB checkpoints); `git_sha()` HEAD + `-dirty` suffix when working tree dirty, returns `"unknown"` on git absence (never raises).
- **evaluate.py CLI with atomic run-dir I/O** (`src/evaluate.py`): `--run-dir <path> --split {val|test}`; reads `config_snapshot.json` + `best_model.pth`; writes `eval_metrics.json` → `eval_scores.npz` → `per_category.csv` → `.done` in that order, each via `tempfile.mkstemp` + `os.fsync` + `os.replace`. The `.done` marker is LAST so its presence guarantees all upstream outputs exist (D-31 runner-probe contract).
- **D-14 frame grid**: UCF path uses `snippet_window=64, upsample_factor=10` so `n_frames = N_snippets * 640` matches RTFM/MGFN/VadCLIP's original-30fps AUC convention. `_build_frame_arrays` routes per-video snippet scores through `snippet_to_frame` (Plan 04-01) and builds labels via `parse_annotations` + `frame_labels` with fallback to `data/annotations/ucf_temporal.txt` (D-04 committed).
- **Bit-identical rerun verified** (`tests/test_evaluate_cli.py::test_evaluate_bit_identical_rerun`): running evaluate.py twice on the same `run_dir` produces byte-equal `auc`, `ap`, `n_videos`, `n_frames`, `config_hash`, `checkpoint_sha`, `dataset`, `split`, `seed`. Clock-dependent keys (`eval_timestamp`, `eval_duration_s`) are the only sources of variation.
- **17 new tests green** across 4 test files: 5 in `test_test_loader.py` (G1-G5), 5 in `test_config_hash.py` (H1-H5), 4 in `test_eval_metrics.py` (M1-M4), 3 in `test_evaluate_cli.py` (E1-E3). Combined with Plan 01's 28 tests, total Phase 4 surface is 45 tests green.

## Task Commits

TDD discipline produced 4 commits (test RED → feat GREEN for each task):

1. **Task 1 RED: failing test_loader + config helper tests** — `b3f043b` (test)
2. **Task 1 GREEN: test_loader.py + config.py extension** — `2d56418` (feat)
3. **Task 2 RED: failing metrics + evaluate CLI tests** — `e37a55f` (test)
4. **Task 2 GREEN: metrics.py + evaluate.py** — `030e53a` (feat)

## Files Created/Modified

- `src/eval/test_loader.py` — sys.argv + sys.modules triple-gate + `build_test_dataset` dispatcher + `_construct_mil_dataset` kwarg-filter bridge
- `src/eval/metrics.py` — `compute_frame_metrics` + `compute_snippet_auc` with C4 assertions
- `src/evaluate.py` — CLI entry with run-dir I/O contract + atomic write-temp-rename for all 4 output files
- `src/utils/config.py` — added `config_hash`, `checkpoint_sha`, `git_sha` top-level helpers (D-12)
- `tests/test_test_loader.py` — 5 C3 tests (subprocess import-boundary + 3 sys.argv guard variants + UCF dispatch)
- `tests/test_config_hash.py` — 5 D-12 helper tests (determinism, key-order invariance, Path conversion, streaming, git_sha shape)
- `tests/test_eval_metrics.py` — 4 C4 + per-category tests (basic shape, Normal exclusion, C4 REGRESSION fires, single-class skip)
- `tests/test_evaluate_cli.py` — 3 integration tests (smoke, bit-identical rerun, .done atomicity)

## Decisions Made

- **Triple-gate sys.argv defense in `_assert_called_from_evaluate_or_pytest`.** Original two-gate (basename sentinel + substring) design from the plan missed `python -m pytest` because pytest's stub entry point sets `sys.argv[0]='__main__.py'`. Rule 1 auto-fix added a third gate (`"pytest" in sys.modules`) that catches the `-m` invocation without weakening the `-c` rejection path (which still fails G4 because pytest never enters `sys.modules` in a bare `-c` call).
- **`_construct_mil_dataset` inspect-based kwarg-filter** instead of hardcoded signature. The plan's example passes `skel_agg` to `MILFeatureDataset.__init__` — but `skel_agg` is a Plan 04-04 extension that hasn't landed yet. Using `inspect.signature` to drop unsupported kwargs keeps this plan green today and seamlessly picks up `skel_agg` once Plan 04-04 adds it, without a second test_loader edit.
- **Per-category alphabetical ordering + Normal omitted** (Discretion defaults per CONTEXT.md): both clean and matches the Sultani 2018 reporting convention.
- **`np.savez_compressed` for eval_scores.npz** (Discretion default): size savings on 290-video UCF test split are material and Phase 6 visualization doesn't care about de/compress overhead.
- **val-path MIL loss stub = 0.0** (Discretion): CONTEXT.md explicitly marks full val-loss recomputation as optional. The stub writes a well-formed `eval_metrics.json` with `{"mil_loss": 0.0, ...metadata}` so the contract is consistent; Plan 04-05 can refine this as needed or Phase 6 can recompute offline.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] sys.argv guard failed on `python -m pytest`**
- **Found during:** Task 1 GREEN verification
- **Issue:** The plan specified `_PYTEST_SENTINELS = ("pytest", "py.test")` with substring match against `sys.argv[0]` basename. But `python -m pytest` sets `sys.argv[0]` to `__main__.py` (the package's `__main__.py` entry), which contains neither substring. Result: tests G2 (evaluate-accepted via `importlib.reload`), G3 (pytest-accepted), and G5 (UCF dispatch) all failed with the guard's RuntimeError.
- **Fix:** Added a third gate: `if "pytest" in sys.modules: return`. The `pytest` package is always in `sys.modules` by the time any test collects (pytest imports it as part of its own bootstrap). A bare `python -c "import src.eval.test_loader"` does NOT have `pytest` in `sys.modules`, so G4 (subprocess `-c` rejection) still fails correctly.
- **Files modified:** `src/eval/test_loader.py`
- **Verification:** All 10 Task 1 tests green (`pytest tests/test_test_loader.py tests/test_config_hash.py -x` in 35s); manual `python -c "import src.eval.test_loader"` still exits non-zero with `"test-set leakage"` substring.
- **Committed in:** `2d56418` (Task 1 GREEN commit)

**2. [Rule 2 - Missing critical functionality] `_construct_mil_dataset` kwarg-filter bridge**
- **Found during:** Task 1 implementation
- **Issue:** Plan's reference code passes `skel_agg=data.get("skel_agg", "none")` to `MILFeatureDataset.__init__`, but `MILFeatureDataset.__init__` in the current repo does NOT accept `skel_agg` — that's a Plan 04-04 (Wave 3+) extension. Calling the plan's code verbatim would raise `TypeError: __init__() got an unexpected keyword argument 'skel_agg'`. This is a forward-compat gap the plan's own Interface section notes ("skel_agg added in Plan 04").
- **Fix:** Wrote `_construct_mil_dataset(cls, **kwargs)` that uses `inspect.signature(cls.__init__)` to intersect kwargs with the actual parameters. Plan 04-02 can pass `skel_agg` today (it gets dropped silently on the pre-04-04 signature); Plan 04-04 adds the param (it gets forwarded automatically on the post-04-04 signature). Zero edits to `test_loader.py` needed when 04-04 lands.
- **Files modified:** `src/eval/test_loader.py`
- **Verification:** G5 (`test_build_test_dataset_ucf_dispatch`) passes; sample dict contains all expected keys; `len(ds) == 10` matches the synthetic fixture's 10-video count.
- **Committed in:** `2d56418` (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing-functionality)
**Impact on plan:** Both fixes are pure compatibility improvements — no scope change, no new surface, no deferred work. All plan acceptance criteria met (`grep -q` verified for every pattern in both tasks).

## Known Stubs

Two intentional stubs are documented in code and deferred to downstream plans:

| Stub | File | Line | Reason |
|------|------|------|--------|
| `xd_i3d` ImportError pointer | `src/eval/test_loader.py` | 102-109 | I3DFeatureDataset lives in `src/data/i3d_dataset.py` which Plan 04-03 creates. test_loader raises RuntimeError with "Plan 04-03" pointer if xd_i3d is requested before 04-03 lands. |
| xd_i3d label construction | `src/evaluate.py` | 172, 184-195 | `_build_frame_arrays` for `dataset == "xd_i3d"` emits all-zero labels since Wu et al. XD temporal annotations are not yet wired. Plan 04-03 will replace this branch with actual label parsing. |
| val-path MIL loss = 0.0 | `src/evaluate.py` | 313 | CONTEXT.md Discretion marks val-path loss as optional; writing a well-formed metrics JSON with stub value preserves the D-09 contract shape. Phase 4b or Phase 6 can refine. |

All three stubs are part of the plan's explicit scope boundary (xd_i3d → Plan 04-03; val-loss → Discretion) and do NOT block this plan's goal of shipping the UCF evaluation CLI. They are tracked here for the verifier and for Plan 04-03's / 04-05's awareness.

## Issues Encountered

- **`python -m pytest` sets `sys.argv[0]='__main__.py'`.** Not caught by the plan's original 2-gate guard; required adding a third gate (`"pytest" in sys.modules`). Documented above as auto-fix deviation #1.
- **MILFeatureDataset predates Plan 04-04's skel_agg parameter.** Working around via inspect-based kwarg filtering; documented above as auto-fix deviation #2.

No other issues encountered.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Plan 04-03 ready to start.** It can implement `src/data/i3d_dataset.I3DFeatureDataset` + register `rtfm_i3d` in MODEL_REGISTRY + replace the xd_i3d label-construction stub in `_build_frame_arrays`. The dispatch surface in `build_test_dataset` is already wired; Plan 04-03 only needs to fulfill the `from src.data.i3d_dataset import I3DFeatureDataset` import contract.
- **Plan 04-04 (multi-person / CLIP pooling ablations) will inherit skel_agg wiring automatically.** Once `MILFeatureDataset.__init__` accepts `skel_agg`, `_construct_mil_dataset`'s `inspect.signature` check will thread it through without a test_loader edit.
- **Plan 04-05 (scripts/run_ablations.py) can subprocess-invoke `python src/evaluate.py`** and probe `results/<run>/.done` for skip-if-exists. The atomic write-order (.done last) means probing its presence is safe.
- **Phase 5 TTA** can read the canonical `best_model.pth` that `evaluate.py` leaves unchanged (D-10 read-only).
- **No blockers.**

## Threat Mitigations Applied

| Threat ID | Mitigation Implemented | Evidence |
|-----------|------------------------|----------|
| T-04-02-01 (EoP via torch.load pickle) | `load_checkpoint` uses `weights_only=True` (default on PyTorch 2.6) | `src/utils/checkpoint.py::load_checkpoint` passes `weights_only=True` unchanged; evaluate.py calls it verbatim. |
| T-04-02-02 (Info disclosure via non-evaluate/non-pytest import) | Triple-gate sys.argv + sys.modules guard at module top | `test_argv_guard_rejects_bad_entry` locks this in; subprocess `python -c "import src.eval.test_loader"` exits non-zero with "test-set leakage" substring. |
| T-04-02-03 (Tampering via concurrent race) | Atomic write-temp-rename for `.done` + `eval_metrics.json` + `eval_scores.npz` + `per_category.csv`. `tempfile.mkstemp` in same dir + `os.fsync` + `os.replace` | `_write_json_atomic`, `_mark_done`, `np.savez_compressed` (atomic by default), `_write_per_category_csv`. |
| T-04-02-05 (DoS via missing checkpoint/snapshot) | FileNotFoundError raised with actionable message; `.done` never written → runner re-picks | `_load_cfg` + `main` both check `exists()` and raise with a clear message; manual verification: `evaluate.py --run-dir ./results/does-not-exist` exits non-zero immediately with FileNotFoundError. |

T-04-02-04 (--run-dir outside project root) and T-04-02-06 (argv spoofing) are accept-disposition per the plan's threat model.

## Self-Check: PASSED

- [x] `src/eval/test_loader.py` exists with `_assert_called_from_evaluate_or_pytest` + `"test-set leakage"` + `def build_test_dataset`
- [x] `src/utils/config.py` gained `def config_hash` + `def checkpoint_sha` + `def git_sha`
- [x] `src/eval/metrics.py` exists with `def compute_frame_metrics` + `C4 REGRESSION` + `roc_auc_score`
- [x] `src/evaluate.py` exists with `def main` + `parse_args` + `run-dir` + `eval_metrics.json` + `eval_scores.npz` + `per_category.csv` + `.done` + `os.replace` + `config_hash`
- [x] `tests/test_test_loader.py` contains `test_no_transitive_import`, `test_argv_guard_rejects_bad_entry`, `subprocess.run`
- [x] `tests/test_config_hash.py` covers determinism + key-order invariance + Path conversion + streaming + git_sha shape
- [x] `tests/test_eval_metrics.py` contains `test_c4_assertion_fires` + `C4 REGRESSION`
- [x] `tests/test_evaluate_cli.py` contains `test_evaluate_cli_smoke` + `test_evaluate_bit_identical_rerun` + `test_done_after_metrics`
- [x] Commit `b3f043b` exists (Task 1 RED)
- [x] Commit `2d56418` exists (Task 1 GREEN)
- [x] Commit `e37a55f` exists (Task 2 RED)
- [x] Commit `030e53a` exists (Task 2 GREEN)
- [x] `pytest tests/test_test_loader.py tests/test_eval_metrics.py tests/test_evaluate_cli.py tests/test_config_hash.py -x` → 17 passed
- [x] Full Phase 4 suite (45 tests) green; broader 132-test non-slow suite green (no regressions)
- [x] Manual: `python -c "import src.data.dataset; ..."` prints `"C3 OK"`
- [x] Manual: `python -c "import src.eval.test_loader"` exits non-zero with `"test-set leakage"` in stderr
- [x] Manual: `python src/evaluate.py --run-dir ./results/does-not-exist` exits non-zero with `FileNotFoundError` (clean, not import-path traceback)

---
*Phase: 04-baseline-evaluation-main-results*
*Completed: 2026-04-15*
