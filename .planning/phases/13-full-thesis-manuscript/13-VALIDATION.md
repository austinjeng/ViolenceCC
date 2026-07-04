---
phase: 13
slug: full-thesis-manuscript
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-05
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 13-RESEARCH.md §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (repo suite; 322-passed baseline per quick 260623-9tu) + LaTeX build gate |
| **Config file** | existing repo pytest config; `thesis/.latexmkrc` (Wave 0 installs) |
| **Quick run command** | `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1` (incremental build + .log scan) |
| **Full suite command** | `.\scripts\build_thesis.ps1 -Clean` then `python -m pytest -q` (vcc-main) |
| **Estimated runtime** | build ~60-120 s; pytest ~1-2 min |

---

## Sampling Rate

- **After every task commit that touches thesis/ LaTeX:** incremental `build_thesis.ps1` (zero errors, zero undefined refs/citations via .log scan)
- **After every plan wave:** `build_thesis.ps1 -Clean` + `python -m pytest -q`
- **Before `/gsd:verify-work`:** clean build green + pytest green + number audit + overclaim scan passed
- **Max feedback latency:** ~180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (populated by planner — every thesis-content task verifies via build + targeted grep assertions; tracking tasks verify via `git ls-files --error-unmatch`) | | | | — | N/A (docs phase; no attack surface) | build/grep/cli | see gates below | ❌ W0 | ⬜ pending |

Phase gates → checks map (binding, from RESEARCH):

| Gate | Check | Automated command |
|---|---|---|
| Build clean | zero LaTeX errors / undefined refs / undefined citations | `build_thesis.ps1 -Clean` + built-in .log scan |
| Number audit | every number → PROVENANCE.md → tracked source; headlines 82.5/78.7 byte-consistent everywhere | Wave-3 multi-agent audit + grep headline-consistency |
| Overclaim scan | honesty framings present; no SOTA / online-TTA / clean-AUC-gain claims | Wave-3 scan (Phase-12 token list) |
| Structure | TOC matches spec §4; every figure/table referenced; all chapters present | Wave-3 structure check |
| Tracking | every manifest source tracked | `git ls-files --error-unmatch <each path>` (Wave 0 hard assert) |
| Repo hygiene | pytest green; thesis build artifacts ignored | `python -m pytest -q`; `git status` clean |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/build_thesis.ps1` — non-interactive latexmk wrapper + preflight + .log scan
- [ ] `thesis/.latexmkrc` — engine flags for thesis build
- [ ] `.gitignore` — thesis artifact patterns + `results/` un-ignore mechanics (or `git add -f` route)
- [ ] ~269 provenance-source trackings + `git ls-files --error-unmatch` assertions (RESEARCH §3 list)
- [ ] 2-3 small tracked Class-R figure/table scripts (severity heatmap; corruption heatmaps from `_tta_rerun_continual`; per-category table generator)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Chapter-draft quality/voice | spec §4 | prose judgment | user checkpoint after Wave 1 |
| SOTA evidence report | spec §8 2b | external-source judgment | user spot-approves report (Wave 2) |
| Final PDF visual pass | spec §11 | layout judgment | user checkpoint at final |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
