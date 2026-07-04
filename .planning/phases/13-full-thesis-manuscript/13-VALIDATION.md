---
phase: 13
slug: full-thesis-manuscript
status: draft
nyquist_compliant: true
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

**Per-wave pytest coverage (planner r2):** W1 → 13-01 T3 · W2 → 13-03 T3 (added r2) · W3 → 13-04 T3 · W4 → covered one wave later at 13-08 T1 (wave-4 plans are LaTeX-prose-only; no Python is touched) · W5 → 13-08 T1 · W6 → 13-10 T3 (added r2) · W7 → 13-12 T3 · W8 → 13-13 T3.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 13-01-T1 | 13-01 | 1 | SC1 | T-13-01 | vendored .bst byte-identical | cli/grep | ls+grep counts (9 ch / 6 app); cmp IEEEtranN.bst vs MiKTeX copy | ❌ W0 (builds harness) | ⬜ pending |
| 13-01-T2 | 13-01 | 1 | SC1 | — | no ungated Invoke-Item; log-scan wired | cli/git | file asserts; git ls-files results/ count = 28 | ❌ W0 (builds harness) | ⬜ pending |
| 13-01-T3 | 13-01 | 1 | SC1 | — | N/A (docs) | build/grep/pytest | build_thesis.ps1 -Clean exit 0; grep GATE-13 = 15; pytest green (W1 gate) | ❌ W0 (builds harness) | ⬜ pending |
| 13-02-T1 | 13-02 | 2 | SC3 | T-13-02 | provenance chain fully tracked | git | git ls-files results/ count = 297; per-file --error-unmatch loop | ❌ W0 | ⬜ pending |
| 13-02-T2 | 13-02 | 2 | SC3 | T-13-02 | forbidden source paths absent | grep/git | PROVENANCE.md greps (82.5 ≥1; summary_3seed ≥1; Pitfall-13 paths only in forbidden section); source-path --error-unmatch loop | ❌ W0 | ⬜ pending |
| 13-03-T1 | 13-03 | 2 | SC4 | T-13-03 | Class-R inputs only; stale-data asserts | script/cli | both generators exit 0; 3 output PDFs exist > 5KB | ❌ W0 | ⬜ pending |
| 13-03-T2 | 13-03 | 2 | SC4 | T-13-03 | self-check vs summary_3seed.json | script/git/grep | both generators exit 0; rollup CSV --error-unmatch; grep toprule ≥1 | ❌ W0 | ⬜ pending |
| 13-03-T3 | 13-03 | 2 | SC4 | T-13-03 | historical-baseline guard recorded | script/cli/pytest | fig_sweep_* ≥2; phase7_charts non-empty; pytest green (W2 gate, added r2) | ❌ W0 | ⬜ pending |
| 13-04-T1 | 13-04 | 3 | SC4 | T-13-04 | Class-V notes drafted per figure | cli | 5 figures exist; cmp byte-identical each | ✅ (harness from W0) | ⬜ pending |
| 13-04-T2 | 13-04 | 3 | SC4 | T-13-04 | forbidden C-series excluded | grep | C-series grep in thesis/figures/ = 0 | ✅ | ⬜ pending |
| 13-04-T3 | 13-04 | 3 | SC4, SC1 | T-13-04 | manifest sources tracked | build/pytest/grep | build -Clean exit 0; pytest green (W3 gate); grep Class ≥ asset count | ✅ | ⬜ pending |
| 13-04-T4 | 13-04 | 3 | SC1 | — | Wave-0 approval recorded | manual checkpoint | user response (see Manual-Only) | — | ⬜ pending |
| 13-05-T1 | 13-05 | 4 | SC2, SC5 | T-13-05 | forbidden-value greps | build/grep | incremental build exit 0; PLACEHOLDER-W0 = 0; 82.5 ≥1 (ch01) | ✅ | ⬜ pending |
| 13-05-T2 | 13-05 | 4 | SC2, SC5 | T-13-05 | no new RE-VERIFY outside ch07 (r2) | build/grep | build exit 0; PLACEHOLDER-W0 = 0; 77.3 = 0; RE-VERIFY = 0 (ch02) | ✅ | ⬜ pending |
| 13-05-T3 | 13-05 | 4 | SC2, SC5 | T-13-05 | equations byte-verbatim | build/grep | build exit 0; label{eq:loss} = 1; PLACEHOLDER-W0 = 0 (ch03) | ✅ | ⬜ pending |
| 13-06-T1 | 13-06 | 4 | SC2, SC5 | T-13-06 | corruption.py params, never CLAUDE.md | build/grep | build exit 0; PLACEHOLDER-W0 = 0; 0.13 ≥1 (ch04 λ2 footnote) | ✅ | ⬜ pending |
| 13-06-T2 | 13-06 | 4 | SC2, SC5 | T-13-06 | tables byte-match main.tex; per-category summary (r2) | build/grep | build exit 0; 82.5 ≥2; 0.008 = 0; PLACEHOLDER-W0 = 0 (ch05) | ✅ | ⬜ pending |
| 13-06-T3 | 13-06 | 4 | SC2, SC5 | T-13-06 | Pri-5 aggregations kept distinct | build/grep | build exit 0; 13.9 = 0; 1.21 ≥1; PLACEHOLDER-W0 = 0 (ch06) | ✅ | ⬜ pending |
| 13-07-T1 | 13-07 | 4 | SC2, SC6 | T-13-07 | 13 row RE-VERIFY carried; caption workflow sentence dropped (r2) | build/grep | build exit 0; RE-VERIFY = 13; documentclass/end{document} = 0; 77.3 = 0 (ch07) | ✅ | ⬜ pending |
| 13-07-T2 | 13-07 | 4 | SC2, SC5 | T-13-07 | gate misses stated plainly | build/grep | build exit 0; PLACEHOLDER-W0 = 0; 0.57 ≥1 (ch08) | ✅ | ⬜ pending |
| 13-07-T3 | 13-07 | 4 | SC2, SC5 | T-13-07 | canonical anchors only | build/grep | build exit 0; 82.5 ≥1; 78.7 ≥1; PLACEHOLDER-W0 = 0 (ch09) | ✅ | ⬜ pending |
| 13-08-T1 | 13-08 | 5 | SC1, SC2 | T-13-08 | forbidden-value sweep dispositioned | build/grep/pytest | build -Clean exit 0; PLACEHOLDER-W0 = 0 all chapters; RE-VERIFY = 13 (ch07 only); pytest green (W4+W5 gate) | ✅ | ⬜ pending |
| 13-08-T2 | 13-08 | 5 | SC1, SC2 | T-13-08 | Wave-1 approval recorded | manual checkpoint | user response (see Manual-Only) | — | ⬜ pending |
| 13-09-T1 | 13-09 | 6 | SC2, SC5 | T-13-09 | Pitfall-13 paths never cited | build/grep | build exit 0; phase7_summary/diagnostic refs = 0; PLACEHOLDER-W0 = 0 (appA) | ✅ | ⬜ pending |
| 13-09-T2 | 13-09 | 6 | SC2, SC5 | T-13-09 | exact Pri-7 hedge; no relics | build/grep | build exit 0; "directionally supportive" = 1; 0.955/88.15/44.89 = 0 (appB) | ✅ | ⬜ pending |
| 13-09-T3 | 13-09 | 6 | SC2, SC5 | T-13-09 | historical labeling enforced | build/grep | build exit 0; historical ≥2; PLACEHOLDER-W0 = 0 (appC) | ✅ | ⬜ pending |
| 13-10-T1 | 13-10 | 6 | SC2, SC5 | T-13-10 | tracked STATE.md narrative only | build/grep | build exit 0; PLACEHOLDER-W0 = 0; ucf_total_frames.json ≥1 (appD/E) | ✅ | ⬜ pending |
| 13-10-T2 | 13-10 | 6 | SC2, SC5 | T-13-10 | only dispositioned figures included | build/grep | build exit 0; PLACEHOLDER-W0 = 0; 64×64 limitation ≥1 (appF) | ✅ | ⬜ pending |
| 13-10-T3 | 13-10 | 6 | SC2, SC5 | T-13-10 | abstract headline byte-consistency | build/grep/pytest | build -Clean exit 0; abstract 82.5 = 1, 78.7 = 1; pytest green (W6 gate, added r2) | ✅ | ⬜ pending |
| 13-11-T1 | 13-11 | 6 | SC6 | T-13-11 | primary-source-only evidence | grep | VERDICT ≥ 9 in 13-SOTA-EVIDENCE.md | ✅ | ⬜ pending |
| 13-11-T2 | 13-11 | 6 | SC6 | T-13-11 | all four `and others` author lists recorded (r2) | grep | VERDICT ≥ 32; http ≥ 17 | ✅ | ⬜ pending |
| 13-11-T3 | 13-11 | 6 | SC6 | T-13-11 | spot-approval, never auto-approved | manual checkpoint | user response (see Manual-Only) | — | ⬜ pending |
| 13-12-T1 | 13-12 | 7 | SC6 | T-13-12 | evidence report is sole change authority | build/grep | RE-VERIFY = 0; GATE-13 = 0; `and others` = 0 (all four resolved, r2); TODO = 0 | ✅ | ⬜ pending |
| 13-12-T2 | 13-12 | 7 | SC1 | T-13-12 | structure matches spec §4 (named-unit inventory, r2) | build/grep | build -Clean exit 0; multiply = 0; undefined = 0 in main.log | ✅ | ⬜ pending |
| 13-12-T3 | 13-12 | 7 | SC1, SC2 | T-13-12 | zero surviving verification debt | build/grep/pytest | build -Clean exit 0; pytest green (W7 gate); RE-VERIFY/GATE-13 grep = 0 | ✅ | ⬜ pending |
| 13-13-T1 | 13-13 | 8 | SC3 | T-13-13 | untraceable/forbidden numbers fail the audit | grep/audit | 13-AUDIT-numbers.md PASS ≥1; 77.3/tables_generated = 0 | ✅ | ⬜ pending |
| 13-13-T2 | 13-13 | 8 | SC5 | T-13-13 | framings located; overclaims zero | grep | headline greps ≥2 (abstract+ch09); SOTA-claim greps = 0 | ✅ | ⬜ pending |
| 13-13-T3 | 13-13 | 8 | SC1 | T-13-13 | repo hygiene at exit | build/pytest | build -Clean exit 0; pytest green (W8 gate) | ✅ | ⬜ pending |
| 13-13-T4 | 13-13 | 8 | SC1-SC6 | T-13-13 | final approval recorded | manual checkpoint | user response (see Manual-Only) | — | ⬜ pending |

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

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (the 4 checkpoint tasks are manual-only by design — see Manual-Only Verifications)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 180s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner sign-off r2 (2026-07-05) — Per-Task Verification Map populated from the final 13 plans; per-wave pytest coverage closed (13-03 T3 wave 2, 13-10 T3 wave 6, wave-4 noted as one-wave-later at 13-08 T1); execution-time statuses tracked per task above
