---
phase: 4b
slug: xd-violence-main-results-rtfm-xd-i3d-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 4b — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (vcc-main env) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] + `tests/conftest.py` |
| **Quick run command** | `pytest tests/test_loaders_i3d.py tests/test_train_i3d.py tests/test_xd_annotations.py tests/test_evaluate_xd_i3d.py -x --tb=short` |
| **Full suite command** | `pytest tests/ -x --tb=short` |
| **Estimated runtime** | ~15-30s quick; ~60-120s full |

---

## Sampling Rate

- **After every task commit:** Run quick command scoped to the module touched
- **After every plan wave:** Run full suite
- **Before `/gsd-verify-work`:** Full suite green + 1-epoch smoke passes + full rtfm_gate queue completes
- **Max feedback latency:** 30 seconds for unit path; ~10-20 minutes for gate rerun

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 4b-01-01 | 01 | 1 | EVAL-01 | — | `data/annotations/xd_temporal.txt` committed; sha256 pinned | unit | `pytest tests/test_xd_annotations.py::test_annotation_file_present -x` | ❌ W0 | ⬜ pending |
| 4b-01-02 | 01 | 1 | EVAL-01 | — | `parse_xd_annotations` returns dict[str, VideoAnnotation] | unit | `pytest tests/test_xd_annotations.py::test_parse_multi_interval -x` | ❌ W0 | ⬜ pending |
| 4b-01-03 | 01 | 1 | EVAL-01 | — | `xd_frame_labels` handles missing videos (300 normals) | unit | `pytest tests/test_xd_annotations.py::test_frame_labels_missing_video -x` | ❌ W0 | ⬜ pending |
| 4b-02-01 | 02 | 1 | EVAL-01 | — | `build_dataloaders_i3d` returns (nor, abn, val) loaders | unit | `pytest tests/test_loaders_i3d.py::test_build_dataloaders_i3d_shape -x` | ❌ W0 | ⬜ pending |
| 4b-02-02 | 02 | 1 | EVAL-01 | — | `collate_i3d_train` flattens `[B, 5, T, 1024]` → `[B*5, T, 1024]` | unit | `pytest tests/test_loaders_i3d.py::test_collate_flattens_crops -x` | ❌ W0 | ⬜ pending |
| 4b-02-03 | 02 | 1 | EVAL-01 | — | nor/abn partition non-empty for both subsets | unit | `pytest tests/test_loaders_i3d.py::test_nor_abn_partition_nonempty -x` | ❌ W0 | ⬜ pending |
| 4b-03-01 | 03 | 2 | EVAL-01 | — | `train_one_epoch_i3d` runs 1 step, loss finite | unit | `pytest tests/test_train_i3d.py::test_train_one_step_loss_finite -x` | ❌ W0 | ⬜ pending |
| 4b-03-02 | 03 | 2 | EVAL-01 | — | `validate_i3d` signature matches `validate` contract | unit | `pytest tests/test_train_i3d.py::test_validate_i3d_signature -x` | ❌ W0 | ⬜ pending |
| 4b-03-03 | 03 | 2 | EVAL-01 | — | `main()` dispatches to i3d path when `cfg.dataset == 'xd_i3d'` | unit | `pytest tests/test_train_i3d.py::test_main_dispatch_xd_i3d -x` | ❌ W0 | ⬜ pending |
| 4b-04-01 | 04 | 2 | EVAL-01 | — | `_build_frame_arrays` for xd_i3d produces non-zero labels for 500 abn videos | unit | `pytest tests/test_evaluate_xd_i3d.py::test_build_frame_arrays_abnormal_nonzero -x` | ❌ W0 | ⬜ pending |
| 4b-04-02 | 04 | 2 | EVAL-01 | — | `_build_frame_arrays` for xd_i3d produces all-zero labels for 300 normal videos | unit | `pytest tests/test_evaluate_xd_i3d.py::test_build_frame_arrays_normal_zero -x` | ❌ W0 | ⬜ pending |
| 4b-04-03 | 04 | 2 | EVAL-01 | — | C4 guard `assert len(scores) == len(labels)` trips on mismatch | unit | `pytest tests/test_evaluate_xd_i3d.py::test_c4_guard_trips_on_length_mismatch -x` | ❌ W0 | ⬜ pending |
| 4b-05-01 | 05 | 3 | EVAL-01 | — | 1-epoch smoke run completes on real E:/i3d-features data | empirical | `python -m src.train --config configs/rtfm_i3d.yaml --epochs 1 --run-name smoke_xd_i3d_rtfm_i3d_s42` | ❌ W0 | ⬜ pending |
| 4b-05-02 | 05 | 3 | EVAL-01 | — | Full `rtfm_gate` queue completes + AP ≥ 0.7681 | empirical | `python scripts/run_ablations.py --queue rtfm_gate --no-preflight` | ❌ W0 | ⬜ pending |
| 4b-05-03 | 05 | 3 | EVAL-01 | — | Bit-identical rerun: `eval_metrics.json` all 9 numeric keys match on rerun (D-12) | empirical | `python scripts/run_ablations.py --queue rtfm_gate --no-preflight` twice + diff | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_xd_annotations.py` — stubs for EVAL-01 (parser correctness); mirrors `tests/test_ucf_annotations.py` if it exists, else follows the existing `src/eval/ucf_annotations.py` test template pattern from `tests/conftest.py`
- [ ] `tests/test_loaders_i3d.py` — stubs for EVAL-01 (build_dataloaders_i3d + collate)
- [ ] `tests/test_train_i3d.py` — stubs for EVAL-01 (train_one_epoch_i3d + validate_i3d + main() dispatch)
- [ ] `tests/test_evaluate_xd_i3d.py` — stubs for EVAL-01 (`_build_frame_arrays` xd_i3d branch + C4 guard)
- [ ] `tests/fixtures/xd_i3d_mock/` — tiny mock splits + synthetic numpy arrays (per research Open Question #1 — prefer synthetic over real-slice to keep tests self-contained per `tests/conftest.py` convention)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Wu annotation file sha256 matches upstream | EVAL-01 | Upstream file may rotate; pin the committed version | `sha256sum data/annotations/xd_temporal.txt` — record hash in commit message |
| RTFM XD-I3D AP gate AP ≥ 0.7681 | EVAL-01 | Gate is the phase goal; `scripts/run_ablations.py` is the only authority | Read `results/xd_i3d_rtfm_i3d_s42/eval_metrics.json` — check `ap` key ≥ 0.7681 |
| D-12 diagnostic check 2 — `snippet_auc` vs `auc` delta < 2pp | EVAL-01 | Qualitative: indicates snippet→frame broadcast is correct (C4) | Read the same `eval_metrics.json` — compute `abs(snippet_auc - auc)` from values |
| D-12 diagnostic check 3 — 5-crop bag-size audit | EVAL-01 | One-shot log during first 3 epochs; reviewed by human | Scan `results/xd_i3d_rtfm_i3d_s42/train_log.csv` or stderr for bag-size print statements |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (4 new test files + fixtures)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for unit path; acceptable ~10-20 min for empirical gate
- [ ] `nyquist_compliant: true` set in frontmatter after Wave 0 completes

**Approval:** pending
