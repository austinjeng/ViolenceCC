---
phase: 02
slug: feature-extraction-pipeline
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-03
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Direct script-run verification (extraction scripts with `--limit` / `--sample` flags) + pytest for split tests |
| **Config file** | none |
| **Quick run command** | Per-task verify commands (see map below) |
| **Full suite command** | `conda run -n vcc-main python scripts/verify_alignment.py --dataset ucf --split all && conda run -n vcc-main python scripts/verify_alignment.py --dataset xd --split all` |
| **Estimated runtime** | ~30-60 seconds per task verify; full alignment checks ~2-5 minutes |

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` verify command from the plan
- **After every plan wave:** Run verify_alignment.py on completed datasets
- **Before `/gsd:verify-work`:** Both dataset alignment checks must pass
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 02-01-01 | 01 | 1 | DATA-01, DATA-02 | unit + script | `conda run -n vcc-main python scripts/create_splits.py && conda run -n vcc-main python -m pytest tests/test_splits.py -x -v` | pending |
| 02-01-02 | 01 | 1 | DATA-03, DATA-04 | integration | `conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split train --limit 3` | pending |
| 02-02-01 | 02 | 2 | DATA-05 | integration | `conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset ucf --split train --limit 3` | pending |
| 02-02-02 | 02 | 2 | DATA-06, DATA-07 | integration | `conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split train --limit 3` | pending |
| 02-03-01 | 03 | 3 | DATA-08 | integration | `conda run -n vcc-main python scripts/verify_alignment.py --dataset ucf --split train --sample 3 --verbose` | pending |
| 02-03-02 | 03 | 3 | DATA-09 | batch + verify | `conda run -n vcc-main python scripts/verify_alignment.py --dataset ucf --split all` | pending |
| 02-04-01 | 04 | 4 | DATA-10 | batch + verify | `conda run -n vcc-main python scripts/verify_alignment.py --dataset xd --split all` | pending |

*Status: pending / green / red / flaky*

---

## Sampling Mechanism

Phase 02 is a feature extraction pipeline — scripts produce `.npy` files on disk rather than library code with unit-testable interfaces. The sampling mechanism is:

1. **Script-run with `--limit N`**: Extraction scripts accept `--limit 3` to process only 3 videos (~30-60s), confirming output format, shapes, and dtypes.
2. **`verify_alignment.py --sample N`**: Spot-checks N randomly sampled videos for shape/dtype/alignment compliance (~10s).
3. **`verify_alignment.py --split all`**: Full dataset alignment sweep after batch extraction completes (~2-5 min).
4. **`tests/test_splits.py`**: Standard pytest for split file validation (created within Plan 01 Task 1).

These provide adequate feedback latency (<60s) for all tasks. The `--limit` and `--sample` flags serve the same purpose as Wave 0 test stubs: fast, automated verification after each task commit.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full dataset skeleton extraction | DATA-03 | 20-40h batch job, not suitable for CI | Run `extract_skeletons.py` on full dataset, check log for completion |
| Full dataset CLIP extraction | DATA-07 | Multi-hour batch job | Run `extract_clip.py` on full dataset, check log for completion |
| Full alignment verification | DATA-09, DATA-10 | Requires both full extractions complete | Run `verify_alignment.py --split all`, confirm zero failures |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands in their plans
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Script `--limit` and `--sample` flags provide fast feedback (<60s)
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** accepted — direct script-run verification is the appropriate sampling mechanism for extraction pipeline tasks
