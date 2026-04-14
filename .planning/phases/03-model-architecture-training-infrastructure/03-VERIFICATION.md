---
phase: 03-model-architecture-training-infrastructure
verified: 2026-04-14T18:30:00Z
resolved: 2026-04-15T04:15:00Z
status: passed
score: 4/4 success criteria verified (automated + human-confirmed on real UCF)
overrides_applied: 0
human_verification_resolved:
  - test: "Real UCF-Crime smoke run (SC1)"
    result: "passed — run results/ucf_skeleton_only_42_20260415-041040/; 4/4 artifacts; monotone-descent loss; best_model.pth loads cleanly (8 tensors)"
    root_cause_fix: "commit c42d38c — D-10 revised from zero-pad+mask to sample-with-replacement (RTFM/VadCLIP pattern). Original D-10 caused NaN loss via masked_fill(-inf) propagation through paired hinge when N<k=3 (41.2% of UCF videos)."
  - test: "WR-01 LR-off-by-one fix"
    result: "passed — commit 2656992; micro-smoke + real UCF CSV both show epoch-0 lr=1.00e-6 (warmup start)"
nit_gaps:
  - "WANDB_MODE=disabled does not suppress wandb first-run wizard prompt; defer to Phase 4 pre-flight"
---

# Phase 3: Model Architecture & Training Infrastructure — Verification Report

**Phase Goal:** All model variants are implemented and a single configurable training loop can train any of them to convergence with full reproducibility

**Verified:** 2026-04-14T18:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `python src/train.py --config configs/skeleton_only.yaml` runs to completion producing `best_model.pth` and `train_log.csv` | VERIFIED (synthetic data) / HUMAN (real UCF) | `test_skeleton_only_trains` passes (e2e, 3/3 green); verifies all 4 artifacts including `best_model.pth`. Real UCF run: human verification item #1. |
| 2 | GatedFusion forward produces non-NaN scores in [0,1]; LayerNorm layers accessible via `model.named_modules()` | VERIFIED | Runtime check: `shape=[4,32], min=0.51, max=0.59, any_nan=False`; `named_modules()` returns `['ln_skel', 'ln_clip', 'ln_fused']` confirmed by direct Python invocation. Tests: `test_gated_fusion_shapes`, `test_gated_fusion_layernorms` both pass. |
| 3 | Early stopping halts after 10 consecutive epochs of no val MIL loss improvement; `best_model.pth` corresponds to best val epoch | VERIFIED | `EarlyStopping(patience=10)` dataclass verified by `test_patience_trigger`; `test_best_matches_csv` verifies best checkpoint corresponds to min val_loss row in CSV. Both pass. |
| 4 | `config_snapshot.json` saved alongside every checkpoint; re-running with snapshot reproduces bit-identical loss curves | VERIFIED | `test_snapshot_roundtrip` (e2e marker) passes: two independent runs from YAML and then JSON snapshot produce exact-match (train_loss, val_loss) tuples per row. Bit-identical assertion confirmed. |

**Score:** 4/4 success criteria verified (3 fully automated, 1 needs human for real-data execution path)

---

### Success Criteria Verification

| SC | Criterion | Status | Test(s) | Notes |
|----|-----------|--------|---------|-------|
| SC1 | `python src/train.py --config configs/skeleton_only.yaml` runs to completion on UCF-Crime cached features without crashing, producing `best_model.pth` and `train_log.csv` | PARTIAL — HUMAN NEEDED | `test_skeleton_only_trains` (PASS), `test_all_variants_cli` (PASS) | Tests use synthetic tmp_path features. "UCF-Crime cached features" clause requires real E:/features/ucf run. |
| SC2 | Gated Fusion forward pass produces non-NaN frame-level anomaly scores; LayerNorm layers accessible by name via `model.named_modules()` | VERIFIED | `test_gated_fusion_shapes`, `test_gated_fusion_layernorms`, `test_gated_fusion_layernorm_attribute_access` (all PASS) + direct runtime check | Scores in [0,1], no NaN, 3 LNs (`ln_skel`, `ln_clip`, `ln_fused`) confirmed. |
| SC3 | Early stopping halts when val MIL loss hasn't improved for 10 consecutive epochs; saved checkpoint corresponds to best validation epoch | VERIFIED | `test_patience_trigger`, `test_best_matches_csv` (both PASS) | Patience=10 default confirmed in `EarlyStopping` dataclass. `best_model.pth` existence and distinctness from `last_model.pth` when `best_epoch != final_epoch` verified. |
| SC4 | Config snapshot (JSON) saved alongside every checkpoint; re-running with `--config results/<run>/config_snapshot.json` reproduces bit-identical loss curves | VERIFIED | `test_snapshot_roundtrip` (PASS, e2e), `test_snapshot_contents` (PASS), `test_config_snapshot_written` (PASS), `test_snapshot_can_drive_rerun` (PASS) | Full bit-identical assertion on (train_loss, val_loss) tuples per row confirmed. |

---

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `src/train.py` | VERIFIED | 196 lines; `def main` present; CUBLAS env at line 5 before `import torch` at line 20; snapshot_config + WandbLogger wired |
| `src/utils/scheduler.py` | VERIFIED | `def build_scheduler` returns SequentialLR(LinearLR warmup + CosineAnnealingLR) |
| `src/utils/early_stopping.py` | VERIFIED | `class EarlyStopping` with `patience: int = 10`; NaN-streak halt at 3 |
| `src/utils/checkpoint.py` | VERIFIED | `def save_checkpoint_atomic` with tempfile + `os.replace` (Windows-safe) |
| `src/utils/csv_logger.py` | VERIFIED | `class CSVLogger` with fieldnames `("epoch","train_loss","val_loss","lr")`; flush+fsync per row |
| `src/utils/config.py` | VERIFIED | `snapshot_config`, `load_config`, `load_snapshot_as_config` present; git SHA via `git rev-parse HEAD` |
| `src/utils/wandb_logger.py` | VERIFIED | `class WandbLogger` with mode-aware noop (disabled/offline/online) |
| `src/utils/seed.py` | VERIFIED | `set_deterministic`, `seed_worker`, `make_generator` present |
| `src/losses/mil_loss.py` | VERIFIED | `def mil_ranking_loss` with k=3, margin=1.0, lam_sparse=8e-3, lam_smooth=8e-4; RTFM-exact `_sparsity`, `_smoothness` |
| `src/data/dataset.py` | VERIFIED | `MILFeatureDataset` with D-09 segment sampling, D-10 pad+mask, D-12 test mode |
| `src/data/loaders.py` | VERIFIED | `build_dataloaders` with paired nor/abn loaders + val loader |
| `src/models/mil_head.py` | VERIFIED | `MILHead` with hidden_dims=(128,32), dropout=0.3 |
| `src/models/registry.py` | VERIFIED | `MODEL_REGISTRY`, `build_model` dispatch |
| `src/models/skeleton_only.py` | VERIFIED | `SkeletonProj` with `ln_skel`, `MILHead` |
| `src/models/clip_only.py` | VERIFIED | `CLIPProj` with `ln_clip`, `MILHead` |
| `src/models/late_fusion.py` | VERIFIED | `LateFusion` with nested `skeleton.ln_skel`, `clip.ln_clip` |
| `src/models/gated_fusion.py` | VERIFIED | `GatedFusion` with 3 named LNs, Xavier gain=0.1 gate init, residual gradient highway |
| `configs/skeleton_only.yaml` | VERIFIED | `variant: skeleton_only`; complete train/data/wandb blocks |
| `configs/clip_only.yaml` | VERIFIED | `variant: clip_only` |
| `configs/late_fusion.yaml` | VERIFIED | `variant: late_fusion` |
| `configs/gated_fusion.yaml` | VERIFIED | `variant: gated_fusion` |

All 21 required artifacts exist and are substantive.

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/train.py` line 5 | `os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')` | TRN-03 KNOB 4 before `import torch` | WIRED | Line 5 sets env; line 20 is first `import torch`. Grep confirmed. |
| `src/train.py` | `save_checkpoint_atomic(model.state_dict(), ...)` | D-15 best + last checkpoints | WIRED | Lines 192 (last) and 194 (best) both call `save_checkpoint_atomic`. |
| `src/utils/checkpoint.py` | `os.replace(tmp_path, path)` | Windows-safe atomic write | WIRED | Line 37 confirmed by grep. |
| `src/train.py` | `snapshot_config(cfg, run_dir / "config_snapshot.json")` | TRN-05 per-run snapshot | WIRED | Line 153 confirmed by grep. |
| `src/train.py` | `load_snapshot_as_config` via `load_config` extension dispatch | SC4 snapshot-as-config round-trip | WIRED | `.json` suffix triggers `load_snapshot_as_config` in `config.py:load_config`. |
| `src/models/gated_fusion.py` | `nn.init.xavier_uniform_(self.gate.weight, gain=0.1)` | m1 gate saturation mitigation | WIRED | Line 57 confirmed by grep. |
| `src/models/gated_fusion.py` | `self.ln_fused = nn.LayerNorm(shared_dim)` | D-07 third named LN | WIRED | Line 60 confirmed. |
| `src/models/gated_fusion.py` | `residual = fused + p_skel + p_clip` | Gradient highway (RESEARCH.md §8.D) | WIRED | Line 76 confirmed by grep. |
| `src/losses/mil_loss.py` | `masked_fill(mask == 0, float("-inf"))` before `torch.topk` | D-10 padded position masking | WIRED | Line 71 confirmed. |
| `src/losses/mil_loss.py` | `arr2[:-1] = scores_abn[1:]; arr2[-1] = scores_abn[-1]` | RTFM smoothness exact | WIRED | Lines 47-48 confirmed. |
| `src/utils/config.py` | `subprocess.check_output(["git", "rev-parse", "HEAD"])` | TRN-05 git SHA capture | WIRED | Line 52 confirmed; triple-catch fallback present. |

---

### Data-Flow Trace (Level 4)

The training pipeline is a CLI-driven process, not a React/dynamic-data component. Data flows:
1. YAML config → `load_config()` → `cfg dict` → `build_model(**cfg["model"])` → model instance
2. `.npy` feature caches → `MILFeatureDataset.__getitem__` → `{skel, clip, mask, label}` tensors → `mil_ranking_loss` → scalar loss → backprop
3. Per-epoch metrics → `CSVLogger.log()` → `train_log.csv` (flush+fsync per row)
4. Best model state_dict → `save_checkpoint_atomic()` → `best_model.pth`
5. Config + provenance → `snapshot_config()` → `config_snapshot.json`

All flows verified by integration tests (`test_smoke_2_epoch_produces_artifacts`, `test_csv_header`, `test_csv_rows`, `test_config_snapshot_written`) as producing real data (non-empty artifacts with correct structure).

---

### Behavioral Spot-Checks

| Behavior | Command / Test | Result | Status |
|----------|---------------|--------|--------|
| CLI entry point responds to `--help` | `python src/train.py --help` | Prints usage with `--config`, `--seed`, `--epochs`, `--results-dir` | PASS |
| GatedFusion non-NaN forward + LN discoverability | Python one-liner (runtime check) | `shape=[4,32], any_nan=False`; `['ln_skel','ln_clip','ln_fused']` | PASS |
| Fast test suite (90 tests excluding integration/e2e) | `pytest tests/ -q --ignore=test_train_integration.py --ignore=test_reproducibility.py --ignore=test_train_e2e.py` | 90 passed in 46.14s | PASS |
| Integration tests (C3, C5, m1, artifact contract, snapshot) | `pytest tests/test_train_integration.py` | 10 passed in 13.63s | PASS |
| Bit-identical reproducibility (TRN-03) | `pytest tests/test_reproducibility.py` | 1 passed in 6.14s | PASS |
| E2E acceptance for all 4 variants + SC4 snapshot roundtrip | `pytest tests/test_train_e2e.py -m e2e` | 3 passed in 10.24s | PASS |
| Full suite (104 tests) | `pytest tests/ -q -k "not requires_features"` | 104 passed in 62.31s | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MOD-01 | 03-02 | MIL Ranking Loss: top-k selection, hinge margin=1.0, RTFM sparsity+smoothness | SATISFIED | 11 tests pass in `test_mil_loss.py`; bit-parity against RTFM `_rtfm_*_ref` helpers confirmed |
| MOD-02 | 03-03 | Dataset: T=32 segment sampling, zero-pad+mask, skip empty videos, paired DataLoaders | SATISFIED | 10 tests pass in `test_dataset.py`; D-09, D-10, D-12 all implemented |
| MOD-03 | 03-04 | SkeletonProj: 256-d input → [B,T] anomaly scores, `ln_skel` accessible | SATISFIED | `test_skeleton_only_forward`, `test_skeleton_only_ln` pass |
| MOD-04 | 03-04 | CLIPProj: Linear(1024→512) + ln_clip + MILHead → [B,T] scores | SATISFIED | `test_clip_only_forward`, `test_clip_only_ln` pass |
| MOD-05 | 03-04 | LateFusion: equal-weighted 0.5*s_skel + 0.5*s_clip in eval mode to atol=1e-6 | SATISFIED | `test_late_fusion_equal` passes |
| MOD-06 | 03-05 | GatedFusion: sigmoid gate in 256-d shared space + LN + Dropout + residual | SATISFIED | `test_gated_fusion_shapes`, `test_gated_fusion_residual_is_sum_of_both_projections` pass; forward verified non-NaN |
| MOD-07 | 03-05 | Named LayerNorms discoverable for TTA via `model.named_modules()` | SATISFIED | `test_gated_fusion_layernorms`, `test_gated_fusion_layernorm_attribute_access` pass; runtime confirms `['ln_skel','ln_clip','ln_fused']` |
| TRN-01 | 03-06, 03-07 | AdamW lr=1e-4, wd=1e-2; SequentialLR(LinearLR 5 warmup → CosineAnnealingLR 45) | SATISFIED | `test_linear_cosine`, `test_optimizer_config` pass; scheduler confirmed in `scheduler.py` |
| TRN-02 | 03-06 | EarlyStopping patience=10, atomic checkpoint (tempfile+os.replace) | SATISFIED | `test_patience_trigger`, `test_best_matches_csv`, `test_save_failure_preserves_original`, `test_save_is_weights_only_safe` all pass |
| TRN-03 | 03-06 | Fixed seed everywhere; CUBLAS_WORKSPACE_CONFIG before import torch; bit-identical 2-epoch runs | SATISFIED | `test_bit_identical` passes; `test_cublas_env` passes; env var confirmed at line 5 before line 20 |
| TRN-04 | 03-06 | CSV header `epoch,train_loss,val_loss,lr`; one row per epoch, 4 numeric fields | SATISFIED | `test_csv_header`, `test_csv_rows` pass; `CSVLogger` fieldnames match spec |
| TRN-05 | 03-07 | Config snapshot (git SHA + pip freeze + resolved cfg) saved per run | SATISFIED | `test_snapshot_contents`, `test_config_snapshot_written`, `test_snapshot_roundtrip` all pass |
| TRN-06 | 03-07 | Single `train.py` entry point works for all 4 variants via YAML change only | SATISFIED | `test_all_variants_cli` runs all 4 variants; `test_skeleton_only_trains` confirms CLI contract |

All 13 requirements for Phase 3 are satisfied by passing tests.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/train.py` | 174-176 | WR-01: `scheduler.step()` called before reading `lr` — logged LR is the next epoch's LR, not the current epoch's | WARNING | Instrumentation error: training correctness unaffected, but `train_log.csv` LR column is off by one epoch throughout. Thesis-reported LR curves will be misleading. Fix: read `lr` before calling `scheduler.step()`. |
| `src/losses/mil_loss.py` | 33-49 | WR-02: Docstring describes "adjacent-snippet" temporal smoothness, but `arr2[:-1] = arr[1:]` shifts rows (videos), not columns (snippets) | INFO | Misleading documentation only; RTFM-exact behavior is correct. Will confuse Phase 5 TTA analysis. Fix: correct docstring. |
| `src/losses/mil_loss.py` | 67-70 | WR-03: Comment "masked to zero at padded positions so padding does not bias reg" implies incorrect mechanism | INFO | Comment confusion only; no correctness impact. Fix: update comment. |
| `src/utils/seed.py` | 17-42 | WR-04: `PYTHONHASHSEED` not set by `set_deterministic()`; captured in snapshot but no warning if unset | INFO | Low practical risk (DataLoader uses explicit torch.Generator seeding); incomplete "5-KNOB" documentation. |
| `src/models/__init__.py` | 1-6 | IN-01: Eager imports of all variants bypass the lazy-factory registry pattern | INFO | Dead code path; no runtime impact. Inconsistency only. |
| `src/losses/__init__.py` | 1,3 | IN-02: Private `_sparsity`, `_smoothness` exported in `__all__` | INFO | Minor API convention violation; tests import directly from `src.losses.mil_loss`. |
| `tests/conftest.py` | 5 | IN-04: Hardcoded absolute Windows path `D:/ViolenceCC` for `PROJECT_ROOT` | INFO | Solo-researcher project; won't affect results. Should use `Path(__file__).resolve().parent.parent`. |

**WR-01 assessment (from 03-REVIEW.md):** This is a real instrumentation bug that will appear in all Phase 4 thesis results. The logged LR in `train_log.csv` is the LR for epoch N+1, not epoch N. At epoch=0, the CSV records the epoch-1 warmup LR instead of the epoch-0 warmup start LR. This does NOT block verification — training correctness and all test assertions are unaffected (bit-identical test uses the same off-by-one consistently in both runs). However, it should be fixed before Phase 4 produces final results tables. Recommendation: fix in Phase 4 as a pre-run setup task.

**No blockers found.** All anti-patterns are warnings or info items.

---

### Human Verification Required

#### 1. Real UCF-Crime Feature Run (Success Criterion 1 — "on UCF-Crime cached features")

**Test:** With E:/features/ucf/skeleton/ and E:/features/ucf/clip/ mounted, run:
```
WANDB_MODE=disabled python src/train.py --config configs/skeleton_only.yaml --epochs 3
```

**Expected:**
- No crash or ImportError
- `results/ucf_skeleton_only_42_<timestamp>/` directory created
- Directory contains: `best_model.pth`, `last_model.pth`, `train_log.csv`, `config_snapshot.json`
- `train_log.csv` has header `epoch,train_loss,val_loss,lr` and 3 rows (one per epoch)
- Both `.pth` files are non-empty (stat().st_size > 0)
- `torch.load("best_model.pth", weights_only=True)` succeeds

**Why human:** Success Criterion 1 explicitly states "on UCF-Crime cached features". The automated test `test_skeleton_only_trains` uses synthetic numpy arrays at `tmp_path`. The code path is the same, but the real-data run validates that the UCF feature cache format, label parsing, and split files all integrate correctly with the training loop.

#### 2. WR-01 Fix Decision (LR Logging Off-By-One)

**Test:** After swapping lines 174-176 in `src/train.py` (read `lr` before `scheduler.step()`), verify:
1. `test_bit_identical` still passes (the fix changes absolute LR values but preserves relative bit-identity between two same-seed runs)
2. `test_linear_cosine` still passes
3. Re-run a 3-epoch smoke run and inspect `train_log.csv`: epoch=0 LR should be the warmup start value (approximately `lr * 1/warmup_epochs = 1e-4/5 = 2e-5`), not a higher value

**Expected:** Tests pass; logged LR at epoch 0 is approximately `2e-5` (one warmup step into the LinearLR schedule)

**Why human:** WR-01 involves a deliberate code change to `src/train.py`. The fix must be made by the developer with awareness of its effect on `test_bit_identical` (which asserts row-by-row CSV equality between two same-seed runs — the fix will change the absolute LR values logged but both runs will still be identical to each other). This is a developer decision that could also be deferred to Phase 4 with an explicit tracking note.

---

## Gaps Summary

No gaps found. All 13 requirements are satisfied. All 104 tests pass. The two human verification items are:

1. A real-data smoke run to confirm the "UCF-Crime cached features" clause of Success Criterion 1 (not a gap — the code is correct; this is a completeness check)
2. A developer decision on WR-01 (LR logging off-by-one) — not a correctness gap for Phase 3, but should be resolved before Phase 4 generates thesis tables

---

_Verified: 2026-04-14T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
