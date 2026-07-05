---
phase: 13-full-thesis-manuscript
plan: 11
subsystem: verification
tags: [sota, primary-source, verification-gate, sc6, bibliography]
requires: [13-08]
provides:
  - "13-SOTA-EVIDENCE.md: decisive per-item verdicts (quote + URL) for all 17 worklist items + 15 GATE-13 bib entries + 4 author-list expansions"
affects: [13-12]
key-decisions:
  - "Zero UNVERIFIABLE result cells: every UCF/XD number in tab:sota-full/tab:sota-fair survived primary-source verification; no cells omitted"
  - "PiercingEye is NOT published in TPAMI (only 'Submitted to') — venue/year/bib-type correction required"
  - "DSANet first author is 'Wenti Yin', not 'Yang Yin' — bib author field was wrong, not just a placeholder"
  - "CLIP-TSA footnote reworded: 94.02 appears nowhere in the paper (stronger than 'non-comparable protocol')"
  - "Light-WVAD XD absence re-confirmed adversarially; a fetch-model hallucination of 'Table 3 = 77.3' documented in evidence"
duration: ~50min
completed: 2026-07-05
---

# Plan 13-11 Summary: Primary-Source SOTA Verification Gate

**Verdict tally: 31 VERIFIED / 8 CORRECTED / 0 UNVERIFIABLE-omit** (19 worklist verdict rows all with VERIFIED numbers, 5 of them carrying metadata corrections; 12 bib entries VERIFIED + 3 CORRECTED; 4/4 `and others` author lists resolved).

## What was verified

Six parallel research agents fetched every primary source (arXiv abs/HTML/ar5iv, CVF Open Access, AAAI OJS, CVPR/ICCV virtual sites, IEEE Xplore, Crossref). Evidence report at `.planning/phases/13-full-thesis-manuscript/13-SOTA-EVIDENCE.md` records CLAIM / PRIMARY SOURCE URL / verbatim QUOTE / VERDICT / NOTES per item. Gates: 35 `VERDICT` occurrences (>= 32 required), 36 `http` URLs (>= 17 required).

- **All 20 result cells confirmed verbatim from primary tables** — incl. the four known traps: CLIP-TSA XD 82.19 AUC@PR (94.02 not in paper at all), MGFN 79.19 = I3D-RGB (80.11 = VideoSwin), EventVAD 64.04 AP (87.51 is ROC-AUC), LAVAD 62.01 AP (85.36 is ROC-AUC).
- **Holmes-VAU video-level caveat confirmed verbatim** ("evaluated only on the video level", 398-sample tier) — the existing VIDEO-level disclosure stands and is mandatory.
- **All existing omissions re-confirmed correct** (Sultani XD, Light-WVAD XD, STPrompt/FDPN XD N/A, HyperVD/Ghadiya UCF N/A) — no new omissions.

## Corrections for 13-12 to apply (after user approval)

1. GS-MoE: venue → real ICCV 2025 proceedings (Poster + Highlight); bib `@misc` → `@inproceedings`; 7-author expansion (last-two order caveat — user spot-check).
2. PiercingEye: "IEEE TPAMI'26" → arXiv'25 preprint (submitted to TPAMI); bib `@article` → `@misc`; full 8-author names; full title (+ "with Hyperbolic Vision-Language Guidance").
3. FDPN bib: title → "...Using an Egocentric 360-Degree Camera"; authors Inpyo Song / Sanghyeon Lee / Minjun Joo / Jangwon Lee; pages 2828–2837.
4. PEL4VAD bib: author 3 → "Lulu Yang" (+ optional TIP vol. 33 / pp. 4923–4936 / DOI, search-record-backed).
5. DSANet bib: first author → "Wenti Yin"; full 10-author expansion; keep `@inproceedings` AAAI 2026.
6. PI-VAD bib: keep `@inproceedings` CVPR 2025 (main conf, IEEE Xplore-backed); full 8-author expansion.
7. EventVAD bib: full 14-author expansion.
8. CLIP-TSA footnote $^f$: reword — 94.02 does not appear in the paper.
9. Enrichments: AnomalyCLIP (arXiv 2310.02835, CVIU vol. 249, art. 104163, DOI) and HyperVD (vol. 151, art. 105286, DOI — NOT vol. 148).
10. Then remove all 17 `% RE-VERIFY` comments (ch07/ch08) and 15 `% GATE-13` markers; zero `and others` remain.

## Deviations from plan

- Sub-agent final reports were relayed via the coordinator and recovered in full (with verbatim quotes) from the on-disk session transcripts; no re-fetching needed.
- One fetch-model hallucination (Light-WVAD "XD Table 3 = 77.3") was caught by the batch agent's adversarial cross-checks and is documented in the evidence report as a provenance record.

## Checkpoint status

Plan is `autonomous: false` — ends at USER SPOT-APPROVAL (Task 3). Verdicts become binding input to 13-12 only after the user types "approved". No thesis/*.tex file was modified; STATE.md/ROADMAP.md untouched.
