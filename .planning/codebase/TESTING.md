# Testing Patterns

**Analysis Date:** 2026-06-09

The suite is the codebase's primary correctness + reproducibility guard. ~47 `test_*.py` files live flat under `tests/`, backed by a shared `conftest.py` and two synthetic-fixture modules. Most tests are CPU-only, deterministic, and run in seconds; a small number are gated behind markers or skip when real data / a specific conda env is absent.

## Test Framework

**Runner:**
- pytest. Config is in `pyproject.toml` under `[tool.pytest.ini_options]` (there is no separate `pytest.ini`/`tox.ini`).
- Discovery: `testpaths = ["tests"]`, `python_files = ["test_*.py"]`, `python_classes = ["Test*"]`, `python_functions = ["test_*"]`.
- `addopts = "-ra --tb=short"` — report all non-pass reasons, short tracebacks.

**Assertion library:**
- Plain `assert` + `pytest.approx(...)` for float comparisons (`tests/test_disc_reweight.py`). `pytest.raises`, `pytest.skip`, `pytest.fixture`, and markers from pytest itself. No `unittest`.

**Environment:**
- Run from the `vcc-main` conda env (Python 3.11, PyTorch 2.6.0 cu124) — the main training/eval env. `tests/test_ctrgcn_smoke.py` is the one test that needs the separate `vcc-ctrgcn` env (mmcv/pyskl) and is auto-skipped elsewhere (see Environment-conditional collection below).

**Run commands:**
```powershell
# activate the main env first (conda activate vcc-main), then:
pytest                                  # full suite (from repo root D:\ViolenceCC)
pytest tests/test_mil_head.py           # one module
pytest tests/test_disc_reweight.py -k compute_w   # one test group by name
pytest -m "not e2e"                     # skip slow end-to-end CLI tests
pytest -m e2e                           # only the slow full-CLI acceptance tests
pytest --collect-only                   # discovery sanity check (must pass end-to-end)
```
No coverage tool is configured (no `pytest-cov` / `.coveragerc`); coverage targets are not enforced.

## Markers (registered in `pyproject.toml`)

- `e2e` — end-to-end acceptance tests that run the full `src/train.py` CLI (slow, ~2-3 min). Used by `tests/test_train_e2e.py`.
- `requires_features` — tests that need the real `E:/features/ucf/*.npy` cache present on disk.

Apply with `@pytest.mark.e2e` / `@pytest.mark.requires_features` and select/deselect via `-m`.

## Test File Organization

**Location:** Flat — all tests live directly in `tests/`, NOT co-located with `src/`. Fixtures live in `tests/fixtures/`.

**Naming:** `test_<unit-or-area>.py`. The suite mirrors `src/` areas:
- Models / heads / loss — `test_mil_head.py`, `test_models.py`, `test_mil_loss.py`, `test_smoothness_axis.py`, `test_skel_agg.py`, `test_ctrgcn_smoke.py`
- TTA — `test_sar.py`, `test_tent.py`, `test_disc_reweight.py`, `test_evaluate_tta.py`, `test_run_ablations_tta.py`
- Training — `test_train.py`, `test_train_e2e.py`, `test_train_integration.py`, `test_train_i3d.py`, `test_reproducibility.py`
- Evaluation — `test_eval_metrics.py`, `test_evaluate_cli.py`, `test_evaluate_xd.py`, `test_evaluate_xd_i3d.py`, `test_verify_pooling.py`, `test_snippet_to_frame.py`
- Data / splits / datasets — `test_dataset.py`, `test_i3d_dataset.py`, `test_loaders_i3d.py`, `test_test_loader.py`, `test_splits.py`, `test_ucf_annotations.py`, `test_xd_annotations.py`, `test_corruption.py`
- Infra / utils — `test_checkpoint.py`, `test_config.py`, `test_config_hash.py`, `test_seed.py`, `test_scheduler.py`, `test_early_stopping.py`, `test_csv` paths via `test_results_index.py`, `test_done_marker.py`, `test_registry.py`, `test_wandb_logger.py`, `test_wandb_preflight.py`, `test_h1_fulllength_grid.py`, `test_extract_siglip2.py`, `test_rtfm_i3d.py`

**Structure:** Mostly module-level `test_*` functions (no test classes despite `Test*` being registered). Long modules are sectioned with `# ---` banner comments labeling regions (e.g. `# --- Fixtures ---`, `# --- (b) compute_w unit test ---` in `tests/test_disc_reweight.py`, `tests/test_sar.py`).

## conftest.py

`tests/conftest.py` (~168 lines) holds shared fixtures and collection rules so individual test files avoid re-scaffolding temp dirs.

**`PROJECT_ROOT` from `__file__`** (lines 5-9): resolved as `Path(__file__).resolve().parent.parent` so the suite runs both in the canonical checkout and in git worktrees. A prior hardcoded `D:/ViolenceCC` broke worktree runs — do not reintroduce hardcoded roots.

**Environment-conditional collection** (lines 20-22): if `mmcv` is not importable, `test_ctrgcn_smoke.py` is added to `collect_ignore_glob` so `--collect-only` succeeds in `vcc-main`. The test is still runnable in `vcc-ctrgcn`.

**Key fixtures:**
- Path fixtures — `weight_dir`, `pyskl_config_dir`, `splits_dir`, `ucf_temporal_path`, `xd_temporal_path` (and alias `test_anno_path`). Real-data fixtures `pytest.skip(...)` (not fail) when the committed file/mount is absent so collection stays green.
- `feature_dir_ucf` — real `E:/features/ucf`, skips if not mounted.
- `tmp_feature_dir` — writable `tmp_path` shaped like `features/{dataset}/{modality}/*.npy` (creates `skeleton/` + `clip/`).
- Synthetic-feature callables — `synth_skel_features`, `synth_clip_features`, `synth_batch` (lazy-import from `tests.fixtures.synthetic`).
- Synthetic eval fixtures — `synthetic_ucf_features` (10-video UCF), `synthetic_i3d_features` (5-crop I3D), built from `tests.fixtures.synthetic_eval`.
- `eval_run_dir` — writable temp run dir for CLI tests.
- `smoke_cfg` — a minimal training config dict (seed 42, `skeleton_only` variant, 2 epochs) for integration smoke tests, wired to `tmp_path` subdirs.

## Fixtures and Factories

**Synthetic feature factories** — `tests/fixtures/synthetic.py`:
```python
def make_skel(N: int = 40, seed: int = 0) -> np.ndarray:   # [N, 256] float32, np.random.default_rng(seed)
def make_clip(N: int = 40, seed: int = 0) -> np.ndarray:   # [N, 1024] float32, default_rng(seed + 1)
def make_batch(B_nor=16, B_abn=16, T=32, seed=0):          # paired-bag dict (D-04 contract)
```
`make_batch` returns the D-04 batch contract: `{"skel": [B,T,256], "clip": [B,T,1024], "mask": [B,T] (all ones), "label": [B] (B_nor zeros then B_abn ones)}`, built from a seeded `torch.Generator`. Shapes match the Phase 2 cache contracts documented in the module docstring (skeleton 256-d, CLIP 1024-d).

**Synthetic eval fixtures** — `tests/fixtures/synthetic_eval.py`: `make_synthetic_ucf(tmp_path)` and `make_synthetic_i3d(tmp_path)` materialize small on-disk `.npy` fixtures shaped like the real eval inputs.

**Determinism in fixtures:** every generator is seeded (`np.random.default_rng(seed)`, `torch.Generator().manual_seed(seed)`). Tests requiring model determinism seed at the top — e.g. `tests/test_sar.py` `gated_model` fixture does `torch.manual_seed(42)` before constructing `GatedFusion()`.

## Test Structure (representative patterns)

**Pure unit — shape / config assertions** (`tests/test_mil_head.py`): construct the module, push a `torch.randn` tensor, assert output shape, value range, and architecture invariants (layer count/widths, dropout `p`, final `Sigmoid`). No mocks, no disk.
```python
def test_mil_head_layer_widths_d06():
    head = MILHead(input_dim=512)
    linears = [m for m in head.mlp if isinstance(m, nn.Linear)]
    assert len(linears) == 3
    assert linears[0].in_features == 512 and linears[0].out_features == 128
```

**Pure scalar math** (`tests/test_disc_reweight.py` group b): hand-compute the expected value from the formula and assert with `pytest.approx`, no disk / no GPU. One assert per documented edge case (collapsed VL channel, skel at floor, twice-floor, retained VL, near-zero floor).
```python
def test_compute_w_skel_rel_zero_at_twice_floor():
    w, _, skel_rel = compute_w(clip_std_test=0.3, clip_std_clean=1.0, skelZ=2*0.5, skelZ_floor=0.5)
    assert skel_rel == pytest.approx(0.0) and w == pytest.approx(1.0)
```

## Common Patterns

**Reproducibility / bit-identical guard** (`tests/test_reproducibility.py`, marker TRN-03): build two independent run roots with the SAME seed+config, run `src/train.py:main(["--config", ...])` twice, read back `train_log.csv` loss rows, and assert the two row lists are equal. This is the canonical reproducibility test — keep it green when touching seeding, dataloaders, or the loss.
```python
def test_bit_identical(tmp_path):
    main(["--config", str(cfg_a)]); main(["--config", str(cfg_b)])
    assert _read_losses(_latest(res_a)) == _read_losses(_latest(res_b))
```

**Regression guard for refactors** (`tests/test_disc_reweight.py` group a): a `source_only`-unchanged test proves a new TTA method's refactor did not alter the existing scoring call path (run `run_tta_evaluation(method="source_only")` on the synthetic fixture, assert complete output artifacts). Add a similar guard whenever a change threads through a shared code path.

**CLI argument acceptance** (`tests/test_disc_reweight.py` group c): call `parse_args(["--method", "disc_reweight", ...])` and assert the namespace — cheap guard that a new CLI flag is wired before the expensive run path.

**TTA mechanics** (`tests/test_sar.py`, `tests/test_tent.py`): seed, clone initial params, run optimizer steps (`SAM.first_step`/`second_step`), assert params changed/restored. Cover entropy filtering threshold, per-video reset, and `rho`-grid acceptance.

**End-to-end CLI** (`tests/test_train_e2e.py`, `@pytest.mark.e2e`): drive the full `src/train.py` CLI on a synthetic config to a `results/<run>/` dir and assert artifacts (`train_log.csv`, `config_snapshot.json`, `best_model.pth`, done-marker). Slow (~2-3 min); deselect with `-m "not e2e"` for fast iteration.

## What's Covered

- **Models / heads:** `MILHead` shape+architecture, `GatedFusion`, skeleton aggregation, full-model forward (`test_models.py`), pooling correctness (`test_verify_pooling.py`, `test_snippet_to_frame.py`).
- **Loss:** MIL ranking loss + sparsity/smoothness terms (`test_mil_loss.py`, `test_smoothness_axis.py`).
- **TTA:** TENT, SAR (+ SAM optimizer), disc_reweight w-formula, TTA evaluate CLI + ablation runner.
- **Training:** entry-point smoke, integration, e2e CLI, and bit-identical reproducibility.
- **Evaluation:** frame-level AUC/AP metrics, UCF + XD + I3D eval CLIs, eval-stub warnings.
- **Data:** datasets, loaders, splits, UCF/XD annotation parsing, corruption generation (`test_corruption.py`).
- **Infra:** atomic checkpoint, config load/snapshot, `config_hash`, seeding, scheduler, early stopping, `results-index.csv` append (`test_results_index.py`), done-marker, model registry, wandb logger + preflight.

**Coverage notes / gaps:**
- The full feature-dependent numeric reproductions (e.g. the disc_reweight +4.8 AUC reproduction) are NOT committed as tests — they need the `E:/` feature cache + checkpoints and are slow/environment-bound. Recorded truth lives in `scripts/_tmp_r1_full.py` + `results/_coral_derisk/r1full_clip.json`. Committed tests cover the formula and the refactor regression guard instead.
- `requires_features` and the `E:/`-mounted fixtures skip on machines without the cache, so a green local run does not exercise real-feature paths.
- No coverage measurement is enforced; treat the suite as behavior-spec, not a coverage gate.

---

*Testing analysis: 2026-06-09*
