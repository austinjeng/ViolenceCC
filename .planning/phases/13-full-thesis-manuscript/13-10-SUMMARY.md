---
phase: 13-full-thesis-manuscript
plan: 10
subsystem: thesis-appendices-frontmatter
tags: [appD, appE, appF, frontmatter, abstract-T5-2, repro-guide-T6-2, notation, provenance-figures]

# Dependency graph
requires:
  - phase: 13-full-thesis-manuscript
    plan: 04
    provides: "figure disposition list (INCLUDED-V/REGENERATED-V) + PROVENANCE.md §3 — the only admission ticket for App F assets"
  - phase: 13-full-thesis-manuscript
    plan: 06
    provides: "ch05/ch06 figure-consumption record — App F budgets the unconsumed remainder"
  - phase: 13-full-thesis-manuscript
    plan: 08
    provides: "Wave-1 exit gate (merged 9-chapter clean build) as the base build state"
provides:
  - "thesis/appendices/appD_engineering.tex — three-env version matrix, six Windows quirks, 21.6 FPS / 99.3% throughput analysis, C1–C5/M5–M7 pitfall register, WR-01..WR-04 anti-pattern highlights (narrative from tracked STATE.md + 04-VERIFICATION.md only)"
  - "thesis/appendices/appE_reproducibility.tex — clean-checkout-to-reproduced-tables walkthrough with real CLI flags for all 7 tracked entry points; seeds {42,123,2024}; ucf_total_frames.json manifest; results-index.csv master index; bit-identical rerun invariant (discharges T6-2)"
  - "thesis/appendices/appF_figures.tex — 10 Class-V figures (3 skeleton overlays XD-only w/ 64×64 UCF limitation, 3 temporal extras, 2 gate histograms, 2 category-score boxplots), every caption naming its PROVENANCE.md verification basis"
  - "thesis/frontmatter/{titlepage,abstract,notation}.tex — NTUST titlepage; 3-paragraph 295-word abstract (fixes T5-2) with headlines exactly once each; 22-abbreviation + 26-symbol notation tables"
affects: [13-11 SOTA gate, 13-12 RE-VERIFY merge, 13-13 adversarial number audit, 13-VALIDATION]

# Tech tracking
tech-stack:
  added: []
  patterns: ["App F caption pattern: every figure caption restates its PROVENANCE.md Class-V verification basis (what it was checked against), so the figure is auditable from the rendered page alone"]

key-files:
  created: []
  modified:
    - thesis/appendices/appD_engineering.tex
    - thesis/appendices/appE_reproducibility.tex
    - thesis/appendices/appF_figures.tex
    - thesis/frontmatter/titlepage.tex
    - thesis/frontmatter/abstract.tex
    - thesis/frontmatter/notation.tex

key-decisions:
  - "App E commands quoted with REAL argparse flags verified against the scripts this session (train.py --config/--seed, evaluate.py --run-dir/--split, evaluate_tta.py --source-run/--corruption/--severity/--method/--protocol, extract_* --dataset/--split/--backbone/--corruption) — no invented CLI surface"
  - "App F includes fig_category_scores_{ucf,xd} per the orchestrator's budget (13-04 sanctioned them 'App B / App F'; sibling 13-09 plan does not reference them — verified no double-inclusion risk from my side; labels namespaced fig:appf-*)"
  - "pri9_score_hist.png NOT duplicated in App F (Ch5 consumed it); one-sentence cross-reference instead, and a one-sentence omission note covers the 13-04-DROPPED single-seed charts"
  - "titlepage kept generic (no department/student ID/month invented) — only the binding facts: NTUST, Wei-Han Jeng, Chuan-Kai Yang, paper-matching title, 2026"
  - "acknowledgments.tex untouched: the Wave-0 file already carries the compliant permanent user-fill note without any PLACEHOLDER-W0 token (spec §11.2 exempt)"
  - "notation abbreviations restricted to terms grep-verified in 2+ chapters; symbol table documents the two deliberate collisions (scalar s vs vector s; sigmoid vs std-dev sigma) instead of hiding them"

requirements-completed: [SC2 (App D–F + frontmatter complete per spec §4; T6-2 and T5-2 discharged), SC5 (every honesty framing present in the restructured abstract)]

# Metrics
duration: ~45min
completed: 2026-07-05
---

# Phase 13 Plan 10: Appendices D–F + Frontmatter Summary

**Drafted the engineering, reproducibility, and additional-figures appendices plus all four frontmatter files: App E walks a stranger from clean checkout to reproduced tables with verified-real CLI commands (discharging T6-2), the abstract is restructured into three paragraphs under 300 words with byte-identical headlines appearing exactly once each (discharging T5-2), and App F admits only the ten provenance-verified figures left unconsumed by Chapters 5–6.**

## Performance

- **Duration:** ~45 min (2026-07-05T05:25Z → ~06:10Z UTC)
- **Tasks:** 3/3
- **Files:** 6 modified (appD/appE/appF + titlepage/abstract/notation; acknowledgments already compliant)

## Task Commits

1. **Task 1: App D engineering + App E reproducibility** — `033058e` (docs)
2. **Task 2: App F additional figures (provenance-verified only)** — `9c89f24` (docs)
3. **Task 3: frontmatter (titlepage, abstract, notation)** — `b95a707` (docs)

## Verification results (all green)

- `build_thesis.ps1` incremental after Tasks 1–2, `-Clean` after Task 3: exit 0, log scan clean (no errors, no undefined refs/citations) every time
- **App D:** "21.6" ×1, "99.3" ×2, all three env names present; PLACEHOLDER-W0 = 0
- **App E:** all 7 entry points present (src/train.py, src/evaluate.py, evaluate_tta.py, generate_phase7_charts.py, generate_pub_figures.py, thesis_per_category_tables.py, build_thesis.ps1); `ucf_total_frames.json` literal ×1; `results-index.csv` ×2; seed set {42, 123, 2024} ×1; bit-identical invariant ×2; PLACEHOLDER-W0 = 0
- **App F:** all 10 `\includegraphics` targets resolve on disk AND appear in PROVENANCE.md §3; "64" ×2 (64×64 UCF limitation documented twice); zero C-series references; PLACEHOLDER-W0 = 0
- **Abstract:** 295 words, 3 paragraphs; `82.5` exactly 1 occurrence, `78.7` exactly 1 occurrence (byte-consistent with ch09); framings verified by grep: "not a new peak score", "88--91", "small but consistent", "points" ×3, "transductive", "most-degraded", "no gain claimed on clean data"
- **Titlepage:** NTUST ×1, Wei-Han Jeng, Chuan-Kai Yang, 2026 present
- **Notation:** "LayerNorm" ×5; Abbreviations + Symbols sections both present
- **Forbidden-value grep** across appD/appE (83.6, 71.8, 13.9, 0.9268, 0.9452, 0.8227, 0.7192, 77.3): all zero
- **pytest (wave-6 gate):** 322 passed, 0 failed (132.6s) — baseline held. Note: one flaky failure on the first full-suite run (`test_snapshot_roundtrip`, a timing-sensitive assertion, executed while a LaTeX build ran concurrently); it passed in isolation and the full re-run was green — no code was changed between runs (this plan touches only .tex files)
- `git status --short` clean after final build (no artifacts staged)

## Deviations from Plan

### Intentional micro-adaptations (documented, not silent)

**1. acknowledgments.tex not edited.** The plan's Task 3 says to replace the PLACEHOLDER-W0 token with a user-fill note, but the Wave-0 file already carries exactly that ("[Acknowledgments to be written by the author.]") with no W0 token — it was created compliant by design (its header says so). Verified `grep -c "PLACEHOLDER-W0"` = 0; no edit needed.

**2. Abstract header comment reworded during verification.** The first draft's provenance comment quoted the two headline numbers, making the file-level byte-count check read 2 instead of the required exactly-1 per headline. Reworded the comment (numbers now appear only in the abstract body); re-verified 1/1 and rebuilt clean. Caught pre-commit by the plan's own grep gate.

**3. `ucf_total_frames.json` literal placed in a verbatim comment line.** The prose reference uses LaTeX-escaped underscores (`ucf\_total\_frames.json`), which the plan's literal grep cannot match; added the manifest path as a comment line inside the evaluation command block (rendered verbatim, greppable, and genuinely informative in context).

### Scope note

The plan's phase-level verification statement "PLACEHOLDER-W0 count across thesis/ = 0 after this plan" holds for every file this plan owns (appD/appE/appF + all frontmatter = 0). Three W0 markers remain in appA/appB/appC — those files belong to the sibling Wave-2 writer (13-09) executing in parallel and were not touched, per the parallel-execution file-ownership rule.

## Known Stubs

- **acknowledgments.tex** carries the permanent user-fill note "[Acknowledgments to be written by the author.]" — BY DESIGN, exempt per spec §11.2; the author fills it before submission. No other stubs: appD/appE/appF and the other frontmatter files are placeholder-free full prose.

## Threat Flags

None — no code, no new surface. T-13-10 (abstract headline drift) mitigated as specified: byte-consistency greps enforced (82.5 ×1 / 78.7 ×1 in abstract, matching ch09's wording); the Wave-3 headline-consistency check re-verifies.

## Self-Check: PASSED

- thesis/appendices/appD_engineering.tex, appE_reproducibility.tex, appF_figures.tex — full prose on disk, W0-free — verified
- thesis/frontmatter/titlepage.tex, abstract.tex, notation.tex modified; acknowledgments.tex compliant-unchanged — verified
- Commits `033058e`, `9c89f24`, `b95a707` present in git log — verified
- \label{app:d}, \label{app:e}, \label{app:f} retained — verified
- Clean build exit 0 + pytest 322 passed — verified
