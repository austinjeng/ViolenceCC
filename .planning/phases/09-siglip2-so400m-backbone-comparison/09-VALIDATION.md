---
phase: 9
slug: siglip2-so400m-backbone-comparison
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-20
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | EVAL-02 | — | N/A | unit | `pytest tests/test_backbone_config.py -v` | TBD | ⬜ pending |
| 09-02-01 | 02 | 2 | EVAL-02 | — | N/A | integration | Feature file count + shape check | TBD | ⬜ pending |
| 09-03-01 | 03 | 3 | EVAL-03/04 | — | N/A | integration | results-index.csv row count | TBD | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Phase 8 established backbone parameterization tests in `tests/test_backbone_config.py`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Feature extraction completes for all videos | EVAL-02 | GPU-bound ~1hr runtime | Run extraction script, verify file counts match expected |
| 14 ablation runs complete successfully | EVAL-03/04 | GPU-bound ~4hr runtime | Run queues, verify results-index.csv entries |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-20
