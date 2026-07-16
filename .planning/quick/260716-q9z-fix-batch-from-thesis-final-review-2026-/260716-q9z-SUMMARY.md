---
phase: quick-260716-q9z
plan: 01
subsystem: thesis-manuscript
tags: [latex, thesis, review-fixes, factual-corrections]
requires:
  - "THESIS-FINAL-REVIEW-2026-07-16.md findings H1/H3/H4 + M1-M12/M14"
provides:
  - "All 3 open blockers (H1, H3, H4) and all 13 open MEDIUM findings fixed; M15 (author-only acknowledgments) is the sole remaining blocker"
  - "Clean rebuild: thesis/main.pdf 95pp, 0 errors, 0 undefined refs, 0 Overfull \\vbox (H4 47.58pt warning eliminated)"
affects: [thesis-build, paper-sota-fragment]
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified:
    - thesis/chapters/ch02_related_work.tex
    - thesis/chapters/ch03_methodology.tex
    - thesis/chapters/ch04_experimental_setup.tex
    - thesis/chapters/ch05_results_fusion.tex
    - thesis/chapters/ch06_results_tta.tex
    - thesis/chapters/ch07_discussion.tex
    - thesis/frontmatter/notation.tex
    - paper/sota_comparison_full.tex
  deleted: []
decisions:
  - "M3 deviation: renamed the ch03:303 binary-entropy score from bare $s$ to the chapter's declared score symbol $a$ (single-line change) instead of the report's gate rename to $r_{\\mathrm{skel}}$, which would cascade into ch06:356 + notation.tex:90/94/102; added a Notation-paragraph note for the remaining $\\sigma$/$s$ overloads"
  - "M5 deviation: replaced the report's 'concentrated in CLIP and SigLIP2 Base' with 'spans the three non-SO400M backbones' (verified XD 2-person deltas: CLIP -2.1, Base -1.3, Giant -0.9, SO400M +0.5 — the report's wording omitted Giant)"
  - "Page-count gate deviation: 95pp vs plan's 97-99 expectation — the plan range was calibrated on the review-time tree; base f8bd4bb itself builds to 96pp (verified by scratchpad build), and M2's sanctioned deletions reflow ch03 by exactly -1 page"
metrics:
  duration: ~35min
  completed: 2026-07-16
---

# Quick Task 260716-q9z: Final-Review Fix Batch (H1/H3/H4 + 13 MEDIUM) Summary

**One-liner:** Fixed all 3 open blockers (false 4-4 "majority" claim, SOTA table row order in thesis + standalone fragment, frontmatter Symbols-table page overflow) and all 13 open MEDIUM findings from the 2026-07-16 final review; no experiment number changed (H3 is a pure row move); clean 95pp rebuild with the Overfull \vbox eliminated and headlines 82.5/78.7 intact.

## Per-Finding Fix Record

| Finding | File | Old phrase | New phrase |
|---|---|---|---|
| H1 | ch05:161 | "worse than the default for the majority of backbone×dataset cells" | "worse than the default in half of the backbone×dataset cells, including three of the four XD-Violence backbones" (verified 4-4 split) |
| H3 | ch07:252-253 | This-work row BELOW EventVAD | This-work row moved ABOVE EventVAD — RTFM 84.30 → **This work 82.5** → EventVAD 82.03 → LAVAD 80.28; every cell byte-identical |
| H3-mirror | paper/sota_comparison_full.tex:120-121 | same misorder | same pure row swap; EventVAD's trailing `% RE-VERIFY` comment stayed attached to its row |
| H4 | notation.tex:44-98 | single 21-row unbreakable Symbols tabular (47.58pt Overfull \vbox, folio VIII overprint) | split into two tabulars after the λ₁/λ₂ row; second block led by "*Symbols (continued --- test-time adaptation and reweighting).*"; row order/text unchanged; Remark kept after block 2 |
| M1 | ch02:66 | "sub-million-parameter fusion head" | "lightweight (0.50M--1.02M parameter) fusion head" (matches ch01/ch04/conclusion) |
| M2 | ch03:114 | duplicate four-stream-averaging sentence + "(On UCF-Crime a single snippet thus pools... reported below.)" parenthetical | both deleted; surviving first mention (ch03:109-110) and the Second-consequence caveat with correct Ch.5 pointer (ch03:116-122) carry the content |
| M3 | ch03:303 + ch03:50-58 | binary entropy "$-(s\log s + (1-s)\log(1-s))$ per snippet score $s$"; Notation paragraph silent on overloads | "$-(a\log a + (1-a)\log(1-a))$ per snippet anomaly score $a$"; Notation paragraph now disambiguates σ(·) (sigmoid vs pooled std-dev) and plain $s$ (gate vs bold vector 𝐬) — also makes notation.tex:105's "follow the notation paragraph of Chapter 3" claim true |
| M4 | ch04:385-387 | "runs at ~30 ms per frame (about 21.6 FPS end-to-end, 99.3% of it model inference)" | decoupled: "~30 ms per frame in isolation (Table 4.3)" + "extraction loop sustains about 21.6 FPS on single-person scenes (Chapter 3), 99.3% of that time being model inference" |
| M5 | ch05:150-154 | "measured the same ordering with larger margins (−0.90 AP ... −2.32 AP ...), and the final 3-seed grid confirms its direction on every backbone" | "measured the same default-wins ordering, with a much larger mean-only margin (−2.32 AP); the final 3-seed grid confirms the mean-only direction on every backbone, while the 2-person cost on XD-Violence spans the three non-SO400M backbones" |
| M6 | ch05:342-343 | "its width exceeds the spread of the entire published leaderboard" | "its width rivals the spread of the entire published leaderboard on this benchmark and exceeds the spread of the modern frozen-feature methods it is compared against in Chapter 7" |
| M7 | ch05:542 | "Explosion007 (4.2% anomalous) shows the same pattern." | "is likewise a short-event miss, though there the head saturates the whole video near the ceiling rather than near zero, blending the two regimes" (per pri9_failure_cases.md: 0.992/0.993) |
| M8a | ch05:544 | "are exactly the categories where snippet pooling costs the most" | "are among the categories..." (Shooting is 95.67, 6th strongest) |
| M8b | ch05:595 | "The weak tail is exactly the abrupt, short-event category set..." | "The weak tail overlaps the abrupt, short-event category set... ---RoadAccidents and Explosion appear in both, though Robbery, a sustained-event category, also sits in the weak tail:" (splice keeps the following clause grammatical) |
| M9 | ch06:61-62 | "Gaussian noise at high severities is the deepest failure mode, while..." | "...deepest failure mode for the visual-language stream (in absolute fused AUC several JPEG cells sit lower still; Section 6.5), while..." (matches Fig 6.1 caption + ch06 JPEG concession) |
| M10 | ch06:410-412 | "The per-video episodic protocol shows the problem is not adaptation volume either: even unlimited per-condition adaptation (continual protocol) moves nothing..." | "The continual protocol shows the problem is not adaptation volume either: even unlimited per-condition adaptation moves nothing..." |
| M11 | ch07:273 | "Omitted from the main comparison only because" (GS-MoE is row 1 of the main table) | "Omitted from the fair-subset comparison (Table 7.2) only because" (label tab:sota-fair verified present) |
| M12 | ch07:403 | "up to +13.2 points on the hardest corruption" | "up to +13.2 points in the condition that most collapses the visual-language stream" (thesis-canonical, PROVENANCE row 12) |
| M14a | ch07:542-544 | "AP's calibration dependence and XD-Violence's imbalanced categories still create..." | "AP's sensitivity to the ordering among the highest-ranked frames under XD-Violence's low anomaly prevalence, together with its imbalanced categories, still creates..." |
| M14b | ch04:94-96 | "AP weights precision across the recall range and is therefore more sensitive to score calibration" | "AP weights precision across the recall range, depends on class prevalence, and concentrates weight on the highest-ranked frames, making it more sensitive to small ranking changes among top-scored frames" (AUC sentence untouched — L8 scope) |

## Recorded Deviations

1. **M3 — minimal non-cascading rename (plan-directed).** The report's example fix (rename the gate to $r_{\mathrm{skel}}$) would cascade into ch06:356 and three notation.tex rows. Instead the entropy score (the ONLY bare-$s$ score usage in the thesis, ch03:303) was renamed to $a$, aligning with the chapter's own declared convention ("Scalar $a$ denotes a snippet anomaly score"), plus a Notation-paragraph note covering the remaining $\sigma$/$s$ overloads (the report's own alternative). Gate-$s$ usages (ch03 §3.7.3, ch06:356, notation.tex rows) untouched.
2. **M5 — precision wording (plan-directed).** The report's "concentrated in CLIP and SigLIP2 Base" omits Giant's −0.9 AP. Data-verified replacement: "spans the three non-SO400M backbones" (XD 2-person deltas: CLIP −2.1, Base −1.3, Giant −0.9, SO400M +0.5). The historical −0.90 2-person margin token was dropped per the report's own "drop or qualify" instruction; the final-grid ≈0.90 AP mean cost remains stated two sentences earlier.
3. **Page-count gate: 95pp, outside the plan's 97-99 range — expectation was stale, sources are correct.** Evidence: the unedited base commit f8bd4bb was built in the scratchpad and yields **96pp** (with the H4 47.58pt Overfull \vbox present), i.e. the plan's "~97" figure predates 3c275e4's M13 compression. Post-batch TOC comparison shows the −1 page comes exactly from the M2 sanctioned deletions in ch03 (ch04 onward each start 1 physical page earlier; frontmatter pagination identical — the H4 split did not add a page, it lets the Symbols table break legally instead of overprinting folio VIII). Structure verified complete: 8 chapters + references in TOC/bookmarks, all frontmatter present.
4. **M9 line re-wrap.** The plan's wrap-tolerant verify grep (`tr '\n' ' '`) is defeated by the file's CRLF line endings (stray `\r` between joined words). Fixed by placing the full anchor phrase "deepest failure mode for the visual-language stream" on a single source line — the literal gate command now passes; content identical to the report's suggested fix.

## Deliberately NOT Touched (out of batch)

- **M15** (acknowledgments placeholder — author-only), **M13** (already fixed in 3c275e4).
- **All 25 LOW findings** — spot-checked anchors survive: "analyses" ch02:88, BN row notation.tex:19, ch05:377 "sensitivity to score calibration" (L8 scope), "NORM/" line-break ch06:409 (L15), UR-DMU-above-MGFN order in tab:sota-fair (L16).
- **M14 leftovers:** ch05:377 AP-calibration phrasing and the parallel sentence in paper/main.tex (L8 / paper scope) — both intentionally unchanged.
- **paper/main.tex** not edited → build_paper.ps1 convention not triggered.

## Verification Gate Results

| Gate | Result |
|---|---|
| build_thesis.ps1 -Clean exit code | 0, log scan "clean (no errors, no undefined refs/citations)" |
| `Overfull \vbox` in thesis/main.log | **0** (base build had exactly 1: the 47.58pt frontmatter warning — H4 fix confirmed) |
| Undefined references/citations | 0 (pattern excludes the pre-existing, accepted C70/bkai CJK font-shape warning, L24) |
| Page count | 95 (deviation #3 above; base = 96, review-time = 97) |
| Headlines in rendered PDF text | 82.5 ✓ and 78.7 ✓ |
| H3 rendered row order (spatial y-check) | thesis p.81 and fragment p.1: RTFM < This work < EventVAD < LAVAD ✓ |
| H3 fragment compile | `latexmk -pdf -gg sota_comparison_full.tex` exit 0, 1-page PDF; artifacts gitignored, none committed |
| Number integrity (`git diff --word-diff`) | no table cell or reported metric changed; digit-bearing diffs are: M1 param range (matches 3 other chapters), M2/M5 sanctioned prose deletions, M3 symbol rename, M4 21.6 FPS decoupling, H3 pure row moves |
| Task 1 / Task 2 grep gates | all PASS |

## Commits

| Commit | Message |
|---|---|
| 7cf64be | fix(thesis): blockers H1/H3/H4 — cell-split claim, SOTA row order, notation table split [260716-q9z] |
| c514213 | fix(thesis): 13 MEDIUM findings M1-M12, M14 from final review [260716-q9z] |

## Self-Check: PASSED

- thesis/frontmatter/notation.tex contains "Symbols (continued" and 3 `begin{tabular}` ✓
- Both commits present on branch `worktree-agent-aca1984937064ccf1` ✓
- Working tree clean after build (all artifacts gitignored) ✓
