---
phase: 02
slug: feature-extraction-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (vcc-main env) + manual verification scripts |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `conda run -n vcc-main pytest tests/phase02/ -x -q` |
| **Full suite command** | `conda run -n vcc-main pytest tests/phase02/ -v` |
| **Estimated runtime** | ~30 seconds (unit tests); extraction scripts are long-running batch jobs |

---

## Sampling Rate

- **After every task commit:** Run `conda run -n vcc-main pytest tests/phase02/ -x -q`
- **After every plan wave:** Run `conda run -n vcc-main pytest tests/phase02/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DATA-01 | unit | `pytest tests/phase02/test_splits.py` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DATA-02 | unit | `pytest tests/phase02/test_splits.py::test_val_split_reproducibility` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | DATA-03 | integration | `pytest tests/phase02/test_skeleton_extraction.py` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | DATA-04 | integration | `pytest tests/phase02/test_skeleton_extraction.py::test_prenormalize2d` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | DATA-05 | integration | `pytest tests/phase02/test_ctrgcn_features.py` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | DATA-06 | integration | `pytest tests/phase02/test_ctrgcn_features.py::test_output_shape` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 2 | DATA-07 | integration | `pytest tests/phase02/test_clip_features.py` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 2 | DATA-08 | integration | `pytest tests/phase02/test_clip_features.py::test_output_shape` | ❌ W0 | ⬜ pending |
| 02-05-01 | 05 | 3 | DATA-09, DATA-10 | integration | `pytest tests/phase02/test_alignment.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase02/test_splits.py` — stubs for DATA-01, DATA-02
- [ ] `tests/phase02/test_skeleton_extraction.py` — stubs for DATA-03, DATA-04
- [ ] `tests/phase02/test_ctrgcn_features.py` — stubs for DATA-05, DATA-06
- [ ] `tests/phase02/test_clip_features.py` — stubs for DATA-07, DATA-08
- [ ] `tests/phase02/test_alignment.py` — stubs for DATA-09, DATA-10
- [ ] `tests/phase02/conftest.py` — shared fixtures (sample data paths, env detection)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full dataset skeleton extraction | DATA-03 | 20-40h batch job, not suitable for CI | Run `extract_skeletons.py` on full dataset, check log for completion |
| Full dataset CLIP extraction | DATA-07 | Multi-hour batch job | Run `extract_clip.py` on full dataset, check log for completion |
| Full alignment verification | DATA-09 | Requires both full extractions complete | Run `verify_alignment.py`, confirm zero failures |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
