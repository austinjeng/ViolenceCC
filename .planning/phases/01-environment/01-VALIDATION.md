---
phase: 1
slug: environment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual smoke tests (no pytest needed — environment verification phase) |
| **Config file** | none — Phase 1 creates environments, not test infrastructure |
| **Quick run command** | `conda activate vcc-main && python -c "import open_clip; print('OK')"` |
| **Full suite command** | `scripts/smoke_test_all_envs.sh` (created in Phase 1) |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run the relevant env smoke test
- **After every plan wave:** Run full suite (all 3 envs)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01 | 01 | 1 | ENV-03 | file check | `test -d src/models && test -d scripts && echo OK` | ❌ W0 | pending |
| 01-02 | 02 | 1 | ENV-01 | import | `conda activate vcc-skeleton && python -c "import rtmlib"` | ❌ W0 | pending |
| 01-03 | 02 | 1 | ENV-01 | import | `conda activate vcc-ctrgcn && python -c "import pyskl"` | ❌ W0 | pending |
| 01-04 | 02 | 1 | ENV-01 | import | `conda activate vcc-main && python -c "import open_clip"` | ❌ W0 | pending |
| 01-05 | 03 | 2 | ENV-02 | forward pass | `conda activate vcc-ctrgcn && python scripts/smoke_test_ctrgcn.py` | ❌ W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `scripts/smoke_test_ctrgcn.py` — CTR-GCN forward pass verification script
- [ ] `scripts/smoke_test_all_envs.sh` — Combined smoke test for all 3 environments

*Existing infrastructure does not exist — this is a fresh project.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| XD-Violence zip extraction | D-12 (CONTEXT.md) | ~83GB extraction, one-time operation | Verify `E:\XD_Violence\train\` and `E:\XD_Violence\test\` exist with video files |
| I3D features extraction | D-13 (CONTEXT.md) | ~39GB extraction, one-time operation | Verify `E:\i3d-features\` exists |
| Windows junction link | D-06 (CONTEXT.md) | OS-level operation | Verify `data\features` resolves to `E:\features\` |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
