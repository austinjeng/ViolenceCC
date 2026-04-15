---
phase: 4
slug: baseline-evaluation-main-results
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-15
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing, per Phase 3 conftest.py) |
| **Config file** | `pyproject.toml` or `pytest.ini` (existing) |
| **Quick run command** | `pytest tests/test_eval_*.py tests/test_ucf_annotations.py -x -q` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~30-60 seconds (quick); ~3-5 min (full with Phase 3 integration) |

---

## Sampling Rate

- **After every task commit:** Run quick command (file-scoped subset)
- **After every plan wave:** Run full suite
- **Before `/gsd-verify-work`:** Full suite green + RTFM gate run complete (EVAL-01 empirical)
- **Max feedback latency:** 60 seconds for unit/integration layers

---

## Per-Task Verification Map

Planner will populate this table in each PLAN.md `<automated>` block. Expected coverage lines derived from RESEARCH.md §Validation Architecture:

| Task Class | Plan | Wave | Requirement | Test Type | Example Command |
|------------|------|------|-------------|-----------|-----------------|
| `snippet_to_frame()` broadcast | 01 | 1 | EVAL-03 (C4) | unit | `pytest tests/test_snippet_to_frame.py -x` |
| UCF annotation parser | 01 | 1 | EVAL-02, EVAL-04 | unit | `pytest tests/test_ucf_annotations.py -x` |
| Test-loader import guard (C3) | 02 | 2 | EVAL-03 | unit + subprocess | `pytest tests/test_test_loader_guard.py -x` |
| `evaluate.py` CLI contract | 02 | 2 | EVAL-02, EVAL-03 | integration (tmp_path run dir) | `pytest tests/test_evaluate_cli.py -x` |
| `rtfm_i3d` forward pass | 03 | 3 | EVAL-01 | unit (synthetic I3D tensors) | `pytest tests/test_rtfm_model.py -x` |
| I3D loader crop-avg + missing-ID filter | 03 | 3 | EVAL-01 | unit | `pytest tests/test_i3d_loader.py -x` |
| Pooling cache shape axioms | 04 | 4 | EVAL-03 | unit (synthetic fixtures) | `pytest tests/test_verify_pooling.py -x` |
| `cfg.data.skel_agg` loader branch | 04 | 4 | EVAL-03 | unit | `pytest tests/test_skel_agg.py -x` |
| `run_ablations.py` resume + skip | 05 | 5 | EVAL-05 | integration (fake subprocess) | `pytest tests/test_run_ablations.py -x` |
| `.done` marker atomicity | 05 | 5 | EVAL-05 | unit | `pytest tests/test_done_marker.py -x` |
| `results-index.csv` append | 05 | 5 | EVAL-05 | unit | `pytest tests/test_results_index.py -x` |
| `wandb_preflight.py` detection | 05 | 5 | EVAL-05 (ops) | unit (env patching) | `pytest tests/test_wandb_preflight.py -x` |
| End-to-end synthetic run | 05 | 6 | EVAL-02..EVAL-05 | integration (10-video fixture) | `pytest tests/test_eval_e2e.py -x` |

*Planner MUST emit one per-task row covering `<automated>` verify commands — this table is the reference, not the contract.*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — extend with fixtures: `test_anno_path`, `eval_run_dir` (tmp_path-backed), `synthetic_ucf_features` (10-video stub), `synthetic_i3d_features` (5-crop stub)
- [ ] `tests/fixtures/ucf_temporal_mini.txt` — 10-line Sultani-format fixture (5 normal `-1 -1`, 5 anomaly with varied interval counts)
- [ ] `tests/fixtures/i3d_mini/` — synthetic I3D cache (5 train, 3 test, both RGB dirs)
- [ ] `data/annotations/ucf_temporal.txt` — downloaded + committed per D-04 (Wave 0 dependency for real fixture tests)

Existing pytest infrastructure covers invocation; Wave 0 adds only the domain-specific fixtures above.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RTFM AP ≥ 76.81% on XD I3D (±1% of 77.81%) | EVAL-01 | Empirical gate — depends on training dynamics, cannot be unit-tested | Run `python scripts/run_ablations.py --tuple xd_rtfm_i3d_s42`; inspect `results/xd_rtfm_i3d_s42/eval_metrics.json[ap]` |
| Gated Fusion AUC ≥ 83% on UCF test | EVAL-02 | Model accuracy gate — empirical | Run full ablation queue; inspect `results/ucf_gated_fusion_s42/eval_metrics.json[auc]` |
| 3-seed Gated Fusion std < 0.5% | EVAL-05 | Statistical stability over 3 seeds — requires 3× training runs | `python scripts/run_ablations.py --seeds 42,123,2024 --variant gated_fusion --dataset ucf`; compute std from `results-index.csv` |
| Per-category violence AUC > full-test AUC | EVAL-04 | Sensible-result check — depends on model outputs | Inspect `results/*/per_category.csv`; confirm Fighting+Assault rows exceed aggregate |
| `eval_metrics.json` bit-identical on rerun | SC supporting C3/C4 | Determinism invariant across clock/PID — requires two full runs | Run `evaluate.py` twice on same `best_model.pth`; `diff` the JSON output |
| wandb preflight fails-fast on missing auth | EVAL-05 (ops) | Requires unset `WANDB_API_KEY` and no `~/.netrc` wandb entry | Temporarily move `~/.netrc`, unset env var, run `python scripts/wandb_preflight.py`; expect non-zero exit with actionable message |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (annotation file, fixtures, conftest extensions)
- [ ] No watch-mode flags (pytest -x, not --watch)
- [ ] Feedback latency < 60s on quick command
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
