---
phase: 12-sota-comparison-and-positioning
plan: 01
subsystem: paper/thesis
tags: [sota-comparison, latex, positioning, thesis-fragment, zero-gpu]
requires:
  - .planning/phases/12-sota-comparison-and-positioning/12-RESEARCH-sota.md
provides:
  - paper/sota_comparison_full.tex
affects:
  - .gitignore
tech-stack:
  added: []
  patterns:
    - "standalone-compilable LaTeX fragment (\\documentclass{standalone}, varwidth)"
    - "manual [N] citation labels (zero references.bib dependency for isolated compile)"
    - "inline % RE-VERIFY source comments flagging Section-6 re-verify items per row"
key-files:
  created:
    - paper/sota_comparison_full.tex
  modified:
    - .gitignore
decisions:
  - "Citation strategy: manual bracketed [N]/method-name labels, NOT \\cite — keeps the fragment self-contained so it compiles with zero references.bib dependency; documented in the file header how to rewire to the real bib later"
  - "Standalone wrapper: \\documentclass[border=12pt,varwidth=560pt]{standalone} with FRAGMENT BODY BEGIN/END markers, so the body can be lifted into the thesis and the wrapper discarded"
  - "Added paper/sota_comparison_full.pdf to .gitignore (deviation) — .gitignore only covered paper/main.pdf, not paper/*.pdf, so the new fragment's build output was uncovered"
metrics:
  duration: ~14min
  completed: 2026-06-21
  tasks: 2
  files: 2
---

# Phase 12 Plan 01: Standalone SOTA Comparison Thesis Fragment Summary

Self-contained LaTeX fragment (`paper/sota_comparison_full.tex`) holding the full-treatment verified-SOTA analysis — a ~20-method published-numbers comparison table (sorted by UCF AUC, mandatory Setting column, per-number caveat footnotes, 15 inline RE-VERIFY flags), a 7-row fair-subset apples-to-apples table, and the five positioning paragraphs — compiling standalone to a PDF with zero overclaim language and every number traced to the verified research artifact.

## What was built

**Task 1 — Full SOTA comparison table** (commit `c9c2e22`):
- New file `paper/sota_comparison_full.tex` with a documented header block (standalone drop-in fragment; manual-[N] citation strategy + rewire instructions; source-of-record = `12-RESEARCH-sota.md`; RE-VERIFY flagging convention).
- `\documentclass{standalone}` (varwidth) wrapper with explicit `FRAGMENT BODY BEGIN/END` markers for later lift-into-thesis.
- Metric definitions stated once and prominently (UCF = frame-level ROC-AUC %; XD = Average Precision %).
- Full ~20-method table transcribed from Section 1, sorted by UCF AUC descending (GS-MoE 91.58 → … → This work 82.5 → LAVAD 80.28 → Sultani 75.41; the two UCF-N/A audio rows HyperVD/Ghadiya at the bottom). Columns: Method | Year | Venue | UCF AUC | XD AP | Setting. The `This work` row is bolded at its true position 82.5/78.7 and is never a bare head-to-head (the Setting column makes each regime explicit).
- All 14 per-number caveat footnotes (a–n) reproduced verbatim from the artifact.
- 15 inline `% RE-VERIFY: <reason>` comments (≥8 required) on every tabulated Section-6 re-verify entry.

**Task 2 — Fair-subset table + 5 positioning paragraphs + standalone compile** (commit `b240df5`):
- 7-row fair-subset table (Section 2): CLIP-TSA 87.58/82.19, UR-DMU 86.97/81.66, MGFN-I3D 86.98/79.19, Light-WVAD 84.7/77.3, RTFM 84.30/77.81, **This work** 82.5/78.7 (bold), Sultani 75.41/— . Subset-definition caption stated explicitly in lieu of a per-row Setting column (every row is the same setting by construction), plus the "Read of the fair subset" prose.
- Five positioning paragraphs P1–P5 transcribed from Section 3 (deliberate-constraint frame; fair-subset competitiveness; orthogonal contribution; reproducibility/transparency; training-free ≠ low-compute), all anchors kept exactly.
- TTA claim scoped to **corrupted-AUC / robustness only** (mean +1.2%, up to +13.2% on the hardest corruption), with the explicit phrase "robustness, not clean-benchmark AUC" — never a clean-headline-AUC improvement.
- Manual-References note at the end (incl. the Light-WVAD → Wang, Zhou & Guan attribution correction).

## Attribution guardrails honored (verified by grep)

- MGFN XD cell = **79.19** (I3D), NOT 80.11 (VideoSwin).
- CLIP-TSA XD = **82.19** (primary AUC@PR), NOT 82.17, NOT 94.02.
- EventVAD XD = **64.04** AP (not the 87.51 ROC-AUC); LAVAD XD = **62.01** AP (not 85.36 ROC-AUC).
- STPrompt and FDPN XD cells = **N/A** (XD not evaluated — any value would be fabricated).
- Sultani XD cell = **—** (dash), with a footnote attributing the often-quoted 73.20 to Wu et al. ECCV 2020.
- HyperVD, Ghadiya, PiercingEye explicitly **labeled audio** in the Setting column / footnotes.

## Verification results

| Check | Result |
|-------|--------|
| Task 1 automated (Setting column + 82.5 present) | PASS |
| `% RE-VERIFY` count | 15 (≥8 required) |
| Fair-subset method names (7) | all present |
| MGFN 79.19 / CLIP-TSA 82.19 | present |
| Paragraph distinctive phrases (5) | all present |
| Anchors 68.8 / 40.8 / 81.2 / 74.6 / 82.4 / 76.8 / 82.5 / 78.7 | all present |
| TTA +1.2 / +13.2 scoping | corrupted-AUC/robustness only |
| Standalone compile (latexmk → PDF) | PDF produced, exit 0 |
| Fatal `! ` LaTeX errors in log | 0 |
| Unresolved `??` refs in log | 0 (manual [N] labels, no `\cite`, no BibTeX) |
| Overclaim tokens (SOTA / state-of-the-art / outperform) | 0 in prose except explicit "we do not claim state-of-the-art" negation framing (×2) |
| references.bib touched? | NO |
| `\input` by main.tex? | NO |

## Overclaim note (documented per acceptance criteria)

The strings `state-of-the-art` / `SOTA` appear only in:
1. Two explicit **negation** sentences — "We do not claim state-of-the-art performance…" (caption + table note) — which the acceptance criteria explicitly permit ("the phrase may appear only inside a neutral 'we do NOT claim SOTA' framing").
2. **Comment/header** lines describing the artifact, **file-path** references to `12-RESEARCH-sota.md`, and LaTeX **label** names (`tab:sota-full`, `tab:sota-fair`) — none of which render as prose.

No "comparable to SOTA", "outperforms", or bare-SOTA claim appears anywhere in the rendered output.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking hygiene] Added `paper/sota_comparison_full.pdf` to `.gitignore`**
- **Found during:** Task 2 (standalone compile produced the PDF).
- **Issue:** `.gitignore` ignored only `paper/main.pdf` (specific filename), not `paper/*.pdf`. The new fragment's compile output (`sota_comparison_full.pdf`) therefore showed as an untracked, non-ignored build artifact — at risk of accidental commit, which CLAUDE.md prohibits ("NEVER commit paper build artifacts").
- **Fix:** Added a single `paper/sota_comparison_full.pdf` line to `.gitignore` (consistent with the existing `paper/main.pdf` entry). Build intermediates (`.aux/.log/.fls/.fdb_latexmk/.synctex.gz`) were already covered by the existing `paper/*.…` rules.
- **Files modified:** `.gitignore`
- **Commit:** `fd6bb0a`

All numbers and prose otherwise transcribed exactly as written in `12-RESEARCH-sota.md` Sections 1–3.

## Known Stubs

None. The fragment is complete: both tables fully populated from verified numbers, all five paragraphs non-empty, no placeholder cells beyond the deliberate N/A / dash cells (STPrompt/FDPN XD, HyperVD/Ghadiya UCF, Sultani XD) that are intentional and footnoted.

## File ownership (clean for parallel execution with Plan 02)

- Owns: `paper/sota_comparison_full.tex` (+ `.gitignore` deviation, + this SUMMARY).
- Did NOT touch `paper/main.tex` or `paper/references.bib` (Plan 02's files).
- Fragment is NOT `\input` by `main.tex`.

## Commits

- `c9c2e22` — feat(12-01): add full ~20-method SOTA comparison table fragment
- `b240df5` — feat(12-01): add fair-subset table + 5 positioning paragraphs; verify standalone compile
- `fd6bb0a` — chore(12-01): git-ignore paper/sota_comparison_full.pdf standalone build output

## Self-Check: PASSED

- FOUND: paper/sota_comparison_full.tex
- FOUND: .planning/phases/12-sota-comparison-and-positioning/12-01-SUMMARY.md
- FOUND commits: c9c2e22, b240df5, fd6bb0a, 9d1cd01
