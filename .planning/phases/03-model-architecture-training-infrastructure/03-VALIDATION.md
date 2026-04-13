---
phase: 03
slug: model-architecture-training-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-14
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: RESEARCH.md §11 Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Python 3.11, vcc-main env) |
| **Config file** | `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — to add in Wave 0 |
| **Quick run command** | `pytest tests/ -x --tb=short -m "not e2e"` |
| **Full suite command** | `pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~10s quick; ~2-3 min full (includes 2-epoch smoke) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x --tb=short -m "not e2e"`
- **After every plan wave:** Run `pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green + Success Criterion #4 (bit-identical rerun on Gated Fusion)
- **Max feedback latency:** 10 seconds (quick), 180 seconds (full)

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| MOD-01 | MIL Ranking Loss numerical correctness (hinge form, margin=1.0) | unit | `pytest tests/test_mil_loss.py::test_rank_loss_hinge -x` | ❌ W0 | ⬜ pending |
| MOD-01 | Sparsity regularizer matches RTFM `sparsity()` reference on fixed input | unit | `pytest tests/test_mil_loss.py::test_sparsity_exact -x` | ❌ W0 | ⬜ pending |
| MOD-01 | Smoothness regularizer matches RTFM `smooth()` reference (arr2 shift pattern) | unit | `pytest tests/test_mil_loss.py::test_smoothness_exact -x` | ❌ W0 | ⬜ pending |
| MOD-01 | Top-k with mask ignores zero-padded positions (-inf masking) | unit | `pytest tests/test_mil_loss.py::test_masked_topk -x` | ❌ W0 | ⬜ pending |
| MOD-02 | Dataset returns [T=32, D] tensors for N>32 videos via segment sampling | unit | `pytest tests/test_dataset.py::test_train_resample_long -x` | ❌ W0 | ⬜ pending |
| MOD-02 | Dataset zero-pads + produces mask for N<32 videos | unit | `pytest tests/test_dataset.py::test_train_pad_short -x` | ❌ W0 | ⬜ pending |
| MOD-02 | Dataset skips 172 UCF sub-64-frame (0-snippet) videos at load time | unit | `pytest tests/test_dataset.py::test_skip_empty_videos -x` | ❌ W0 | ⬜ pending |
| MOD-02 | Paired DataLoader yields 16 normal + 16 abnormal = 16 ranking pairs per step | integration | `pytest tests/test_dataset.py::test_paired_loader -x` | ❌ W0 | ⬜ pending |
| MOD-03 | SkeletonProj forward produces [B, T] scores without NaN | unit | `pytest tests/test_models.py::test_skeleton_only_forward -x` | ❌ W0 | ⬜ pending |
| MOD-04 | CLIPProj forward: 1024-d → 512-d → scores, no NaN, correct shape | unit | `pytest tests/test_models.py::test_clip_only_forward -x` | ❌ W0 | ⬜ pending |
| MOD-05 | Late Fusion equal-weighted: (s_skel + s_clip) / 2 | unit | `pytest tests/test_models.py::test_late_fusion_equal -x` | ❌ W0 | ⬜ pending |
| MOD-06 | Gated Fusion forward: [B, T, 256+1024] → [B, T], gate σ in [0,1] | unit | `pytest tests/test_models.py::test_gated_fusion_shapes -x` | ❌ W0 | ⬜ pending |
| MOD-06 | Gated Fusion on real UCF features: no NaN, scores in [0,1] | integration | `pytest tests/test_models.py::test_gated_fusion_real_features -x` | ❌ W0 | ⬜ pending |
| MOD-07 | `model.named_modules()` reveals ≥3 named `nn.LayerNorm` in Gated Fusion | unit | `pytest tests/test_models.py::test_gated_fusion_layernorms -x` | ❌ W0 | ⬜ pending |
| MOD-07 | LN layers reachable as `model.ln_skel`, `model.ln_clip`, `model.ln_fused` | unit | `pytest tests/test_models.py::test_layernorm_attribute_access -x` | ❌ W0 | ⬜ pending |
| TRN-01 | Scheduler: linear warmup 5 epochs → cosine decay via SequentialLR | unit | `pytest tests/test_scheduler.py::test_linear_cosine -x` | ❌ W0 | ⬜ pending |
| TRN-01 | AdamW configured with lr=1e-4, weight_decay=1e-2 per PRD §11.1 | unit | `pytest tests/test_train.py::test_optimizer_config -x` | ❌ W0 | ⬜ pending |
| TRN-02 | EarlyStopping triggers after patience=10 epochs of no val-loss improvement | unit | `pytest tests/test_early_stopping.py::test_patience_trigger -x` | ❌ W0 | ⬜ pending |
| TRN-02 | Saved `best_model.pth` matches the best val epoch (cross-check train_log.csv) | integration | `pytest tests/test_train_integration.py::test_best_matches_csv -x` | ❌ W0 | ⬜ pending |
| TRN-03 | Same seed + same config → bit-identical train losses over 2 epochs | integration | `pytest tests/test_reproducibility.py::test_bit_identical -x` | ❌ W0 | ⬜ pending |
| TRN-03 | `CUBLAS_WORKSPACE_CONFIG=:4096:8` set before `import torch` | unit | `pytest tests/test_train.py::test_cublas_env -x` | ❌ W0 | ⬜ pending |
| TRN-04 | `train_log.csv` exists with header `epoch,train_loss,val_loss,lr` | integration | `pytest tests/test_train_integration.py::test_csv_header -x` | ❌ W0 | ⬜ pending |
| TRN-04 | Each epoch appends exactly one row with 4 numeric fields | integration | `pytest tests/test_train_integration.py::test_csv_rows -x` | ❌ W0 | ⬜ pending |
| TRN-05 | `config_snapshot.json` contains resolved config + git SHA + pip freeze | unit | `pytest tests/test_config.py::test_snapshot_contents -x` | ❌ W0 | ⬜ pending |
| TRN-05 | Loading snapshot + re-running produces bit-identical loss curves | acceptance | `pytest tests/test_train_e2e.py::test_snapshot_roundtrip -x` | ❌ W0 | ⬜ pending |
| TRN-06 | `python src/train.py --config configs/skeleton_only.yaml` succeeds | acceptance | `pytest tests/test_train_e2e.py::test_skeleton_only_trains -x` | ❌ W0 | ⬜ pending |
| TRN-06 | Same `train.py` entry point works for all 4 variants via YAML change only | acceptance | `pytest tests/test_train_e2e.py::test_all_variants_cli -x` | ❌ W0 | ⬜ pending |
| C3 | No training-side code imports or opens `*_test.txt` split files | unit | `pytest tests/test_train_integration.py::test_no_test_split_access -x` | ❌ W0 | ⬜ pending |
| C5 | After 5 smoke epochs, per-video score std > 0.05 (no collapse) | integration | `pytest tests/test_train_integration.py::test_score_variance -x` | ❌ W0 | ⬜ pending |
| m1 | After 5 smoke epochs, 0.2 < mean(gate) < 0.8 (no saturation) | integration | `pytest tests/test_train_integration.py::test_gate_not_saturated -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mil_loss.py` — MIL loss + sparsity/smoothness + masked top-k (MOD-01)
- [ ] `tests/test_dataset.py` — `MILFeatureDataset` sampling, padding, skip logic, paired loader (MOD-02)
- [ ] `tests/test_models.py` — per-variant forward + LN discoverability (MOD-03..07)
- [ ] `tests/test_scheduler.py` — SequentialLR linear warmup + cosine decay curve (TRN-01)
- [ ] `tests/test_early_stopping.py` — EarlyStopping patience + NaN handling (TRN-02)
- [ ] `tests/test_reproducibility.py` — bit-identical 2-epoch rerun smoke (TRN-03)
- [ ] `tests/test_config.py` — config load / merge / snapshot round-trip (TRN-05)
- [ ] `tests/test_train.py` — optimizer / CUBLAS env / seeding unit tests (TRN-01, TRN-03)
- [ ] `tests/test_train_integration.py` — 2-epoch smoke with 10 videos (MOD + TRN end-to-end, C3/C5/m1 regression tests)
- [ ] `tests/test_train_e2e.py` — acceptance: full CLI run produces all artifacts (TRN-06)
- [ ] `tests/conftest.py` — extend with `feature_dir` fixture pointing to `E:/features/ucf/`, `smoke_split_dir` fixture for 10-video synthetic subset, `smoke_fixtures/` dir with pre-committed tiny npy files for determinism of CI-mode tests
- [ ] `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — register `testpaths = ["tests"]`, markers `e2e` and `requires_features`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| wandb UI loss curves render cleanly (per-epoch step alignment, no duplicate x-axis) | TRN-04 | wandb UI is a rendering service; no API to assert visual output | After smoke run: open wandb.ai/<entity>/violencecc/runs/<id>, confirm `train/loss`, `val/loss`, `lr` curves exist and x-axis is `epoch` not `_step` |
| Resumed run after crash continues with matching scheduler LR | TRN-02, TRN-05 | Requires induced crash (kill -9 mid-epoch) which cannot run in pytest CI | Start training, kill after epoch 3, resume via `--resume results/<run>/last_model.pth`, verify epoch-4 LR in CSV matches what a single uninterrupted run would show at epoch 4 |
| Bit-identical rerun on full 50-epoch Gated Fusion run (Success Criterion #4 acceptance) | TRN-03, TRN-05 | 50-epoch run is ~hours; not feasible in CI loop; acceptance gate is a manual one-off | Run Gated Fusion to convergence twice with same config + seed, `diff results/R1/train_log.csv results/R2/train_log.csv` must be empty |

---

## Validation Sign-Off

- [ ] All MOD-0X and TRN-0X requirements have ≥1 automated test mapped in the table above
- [ ] Sampling continuity: every plan wave ends with full-suite green
- [ ] Wave 0 covers all ❌ W0 test files above
- [ ] No watch-mode flags in commands (pytest runs to completion)
- [ ] Feedback latency < 10s for quick run, < 180s for full
- [ ] `nyquist_compliant: true` set in frontmatter after Wave 0 completes and all tests exist

**Approval:** pending
