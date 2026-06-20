# Phase 12 — SOTA Comparison: Final Verification Audit

**Plan:** 12-03 (Wave 2, goal-backward gate)
**Date:** 2026-06-21
**Auditor scope:** the standalone artifact (`paper/sota_comparison_full.tex`, Plan 01) and the live paper (`paper/main.tex` + `paper/references.bib`, Plan 02).
**Source of truth:** `.planning/phases/12-sota-comparison-and-positioning/12-RESEARCH-sota.md` (40-agent verified-SOTA artifact, 31/34 methods VERIFIED against primary sources).
**Pre-phase git baseline:** `16f70fd` (parent of the first phase-12 commit `c9c2e22`).

---

## OVERALL VERDICT: **PASS**

The paper rebuilds cleanly from scratch (`build_paper.ps1 -Clean` exit 0, 11 pages, zero undefined citations/references); the standalone artifact compiles standalone (exit 0, 1 page); every cited UCF/XD number in both deliverables traces to a VERIFIED value in `12-RESEARCH-sota.md` (0 untraceable) with all conflicting re-verify-list numbers `% RE-VERIFY`-flagged; the overclaim scan finds **zero disallowed hits**; and the headline anchors plus existing Tables 1–3 are byte-identical to the pre-phase git baseline. No defects found. No gap-closure plan required.

---

## Audit 1 — Clean build

| Check | Result |
|-------|--------|
| `powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/build_paper.ps1 -Clean` exit code | **0** |
| `paper/main.pdf` produced | **YES** (773,740 bytes) |
| Page count (`Output written on main.pdf (N pages`) | **11 pages** |
| Within workshop page limit (Plan 02 baseline = 11 pp, human-approved) | **YES** — N=11 equals the human-approved baseline; the new `table*` added 0 pages |
| `Citation .* undefined` in `main.log` | **NONE** |
| `Reference .* undefined` in `main.log` | **NONE** |
| Fatal LaTeX errors (`^! `) in `main.log` | **NONE** |
| 6 new `\cite` keys resolve in `main.bbl` | **ALL 6 RESOLVED** (`joo2023cliptsa`, `zhou2023urdmu`, `chen2023mgfn`, `wang2024lightwvad`, `majhi2025pivad`, `yin2026dsanet`) |
| Standalone `sota_comparison_full.tex` compiles (`latexmk -pdf`, temp outdir) | **exit 0**, 1-page PDF, no fatal errors, no unresolved `??` (manual `[N]` labels, no `\cite`/BibTeX) |

Notes: the `latexmk … MiKTeX updates` lines and the standalone log's single `Font shape OMS/cmtt/m/n undefined` line are benign font-substitution/update advisories, not errors. The transient `build_log.txt` (repo root) and the temp standalone build dir were not committed (build dir removed; `build_log.txt` left untracked, never staged).

**Audit 1: PASS.**

---

## Audit 2 — Number Traceability

Every UCF AUC / XD AP value rendered in the paper's new comparison table (`tab:comparison`, `main.tex:394–403`), the §2 Related-Work backfill (`main.tex:92`), the §6 framing prose (`main.tex:385`), and the standalone artifact's two tables (`sota_comparison_full.tex`) was cross-checked against `12-RESEARCH-sota.md`. **Automated check: all rendered external SOTA numbers appear verbatim in the research artifact — 0 untraceable.**

### Traceability table — paper (`main.tex`) cited numbers

| Number | Where cited | Method | Matches VERIFIED value in 12-RESEARCH-sota.md | RE-VERIFY-flagged? |
|--------|-------------|--------|-----------------------------------------------|--------------------|
| 90.33 / 85.37 | `tab:comparison` (l.394) | PI-VAD | YES — §1 row + §8 (I3D, 90.33/85.37) | N/A (verified, not conflicting) |
| 89.44 / 86.95 | `tab:comparison` (l.395) | DSANet | YES — §1 row + §8 (89.44/86.95) | N/A (verified) |
| 88.02 / 84.51 | `tab:comparison` (l.396) + §2 backfill (l.92) | VadCLIP | YES — §1 row + §8 (88.02/84.51) | N/A (verified) |
| 87.58 / **82.19** | `tab:comparison` (l.397) + prose (l.385) | CLIP-TSA | YES — §1 (87.58/82.19); 82.19 = primary AUC@PR | **YES** (l.397: 82.19 primary; 82.17 VadCLIP-table drift noted) |
| 86.97 / 81.66 | `tab:comparison` (l.398) + prose (l.385) | UR-DMU | YES — §1 row + §8 (86.97/81.66) | N/A (verified) |
| 86.98 / **79.19** | `tab:comparison` (l.399) + prose (l.385) | MGFN | YES — §1 (86.98 I3D / 79.19 I3D AP) | **YES** (l.399: 79.19 = I3D, not the VideoSwin 80.11) |
| 84.7 / 77.3 | `tab:comparison` (l.400) + prose (l.385) | Light-WVAD | YES — §1 row + §8 (84.7/77.3, Wang/Zhou/Guan) | N/A (verified) |
| 84.30 / 77.81 | `tab:comparison` (l.401) + §2 (l.92) + prose (l.385) | RTFM | YES — §1 (84.30 I3D / 77.81 I3D AP) | N/A (verified, canonical I3D) |
| **82.5** / **78.7** | `tab:comparison` (l.402) + prose (l.385) | **This work** | Project anchors (Tables 1–2: 82.5 UCF Gated/Giant, 78.7 XD Gated/SO400M) | N/A (own result) |
| 75.41 / — | `tab:comparison` (l.403) + §2 (l.92) + prose (l.385) | Sultani et al. | YES — §1 (75.41 UCF; XD correctly omitted as later re-impl) | N/A (verified; XD dash intentional) |

### Traceability — standalone artifact (`sota_comparison_full.tex`)

The full ~20-method table (l.102–125) and the 7-row fair-subset table (l.194–200) were extracted (RE-VERIFY comments stripped) and every rendered cell matched a §1/§2 value. Representative spot-checks (all PASS): GS-MoE 91.58/82.89 (§1, flagged), Holmes-VAD 89.51/90.67 (§1, flagged), Holmes-VAU 88.96/87.68 (§1, video-level flagged), EventVAD 64.04 AP (§1, flagged — not the 87.51 ROC-AUC), LAVAD 62.01 AP (§1, flagged — not 85.36), Sultani XD = `---` (omitted, footnoted to Wu 2020), MGFN 79.19 (I3D, flagged), CLIP-TSA 82.19 (primary, flagged), PiercingEye 88.82 (audio, flagged), HyperVD/Ghadiya UCF = N/A (audio, flagged). The 15 table-row `% RE-VERIFY` flags cover every Section-6 re-verify-list entry that appears in the tables.

**No number cited in either deliverable fails to match a VERIFIED value, and every conflicting/ambiguous cited number carries a `% RE-VERIFY` flag.**

**Audit 2: PASS.**

---

## Audit 3 — Overclaim scan

Tokens scanned (case-insensitive): `state-of-the-art`, `\bSOTA\b`, `comparable to SOTA`, `outperform(s|ed|ing)?`, `beats SOTA`, `surpass`.

### Paper (`main.tex`) — phase-12 ADDED lines (the diff `+` region)
**ZERO overclaim tokens** in the phase-12 additions (§2 backfill paragraph + the new `tab:comparison` table + its framing prose + caption).

### Pre-existing internal-ablation `outperform` hits (KNOWN-ALLOWED — not failures)
Two `outperform` occurrences exist in `main.tex` but are **outside** the phase-12 diff and predate this phase:

| Line | Text (abridged) | git blame | Disposition |
|------|------------------|-----------|-------------|
| `main.tex:265` | "Gated fusion **outperforms** late fusion consistently… outperforms simple late fusion…" | last touched `33591ac` (2026-06-10, pre-phase) | **KNOWN-ALLOWED** — internal gated-vs-late ablation, not an external SOTA claim |
| `main.tex:429` | "Learned input-dependent gating also substantially **outperforms** fixed equal-weight late fusion on XD-Violence…" | last touched `33591ac` (2026-06-10, pre-phase) | **KNOWN-ALLOWED** — internal gated-vs-late ablation, not an external SOTA claim |

Both compare the project's OWN two fusion variants (gated fusion vs. late fusion). Confirmed via `git diff 16f70fd..HEAD` that **neither line appears in the phase-12 diff**, and via `git blame` that both were authored by `33591ac` before the first phase-12 commit `c9c2e22`. They are explicitly permitted.

### Standalone artifact (`sota_comparison_full.tex`)
All token hits are either non-rendered or explicit negations:

| Line(s) | Context | Disposition |
|---------|---------|-------------|
| 3, 10, 32, 38, 41–43, 93 | `%%` comment / header / `12-RESEARCH-sota.md` file-path references | **Non-rendered** (comments) |
| 81, 95, 136, 183, 187, 245, 312 | `\ref{tab:sota-fair}` / `\label{tab:sota-full}` / `12-RESEARCH-sota.md` — `SOTA` matched inside the `sota` label/filename substring | **Non-rendered** (label/path identifiers) |
| 79 | "We do \emph{not} claim **state-of-the-art** performance; the honest claim is competitiveness…" | **ALLOWED negation** |
| 133 | "\textbf{We do not claim **state-of-the-art**}; rows above this work add a learnable text branch…" | **ALLOWED negation** |

No bare `outperform`, `surpass`, `beats SOTA`, or `comparable to SOTA` appears in any rendered prose of the standalone artifact.

**Total DISALLOWED overclaim hits across all phase-12 deliverables: 0.** (2 explicit negations listed; 2 pre-existing internal-ablation `outperform` lines listed as known-allowed.)

**Audit 3: PASS.**

---

## Audit 4 — Headline integrity

Compared `main.tex` against the pre-phase baseline `16f70fd` (`git diff 16f70fd..HEAD -- paper/main.tex`). The diff contains **exactly two additive changes**:

1. **§2 Related-Work number-backfill** — one paragraph rewritten to quote Sultani 75.41, RTFM 84.30/77.81 (AP), VadCLIP 88.02/84.51 + metric-label clarifications. No result-cell edits.
2. **§6 comparison table + framing prose** — new `\begin{table*}` (`tab:comparison`) + one framing paragraph + bib `\cite`s. Purely inserted.

**Tables 1 (`tab:ucf-ablation`), 2 (`tab:xd-ablation`), and 3 (`tab:tta` + `tab:tta_breakdown`) do not appear in the phase-12 diff at all — every existing result cell is byte-identical to the baseline.** `references.bib` diff is purely additive (59 insertions, 0 deletions; existing 4 SOTA keys untouched).

### Headline anchor presence (all confirmed present, unchanged)

| Anchor | Meaning | Location (unchanged vs baseline) |
|--------|---------|----------------------------------|
| **82.5** | UCF AUC, gated fusion / SigLIP2 Giant | `main.tex:237`, `:239`, `:289`, abstract `:52`, `tab:comparison` `:402` |
| **78.7** | XD AP, gated fusion / SigLIP2 SO400M | `main.tex:256`, `:291`, `:293`, abstract, `tab:comparison` `:402` |
| **68.8** | Skeleton-only UCF AUC | `main.tex:233`, `:263`, `:366` |
| **40.8** | Skeleton-only XD AP | `main.tex:252`, `:263`, `:370` |
| **81.2** | Visual-only CLIP UCF AUC | `main.tex:234`, `:274` |
| **74.6** | Visual-only CLIP XD AP | `main.tex:253`, `:291` |
| **82.4** | Visual-only SigLIP2 Giant UCF AUC | `main.tex:234`, `:289` |
| **76.8** | Visual-only SigLIP2 Giant XD AP | `main.tex:253`, `:291` |

All eight anchors present; none altered by phase 12 (the only places 82.5/78.7/75.41/etc. were *added* are the new §2 prose and the new `tab:comparison`, which cite — not overwrite — the headlines).

**Audit 4: PASS.**

---

## Re-verify checklist (Section 6 of 12-RESEARCH-sota.md) — annotated for the student's manual check

Items the student MUST personally re-check before final submission. **"Cited"** = the number was actually used in a shipped deliverable and therefore needs a primary-source re-check; **"not cited (full table only)"** = appears only in the standalone full ~20-method table (for completeness) and is `% RE-VERIFY`-flagged there but is not in the paper's condensed table; **"not used"** = no rendered cell anywhere.

| # | Re-verify item | Cited where | Flagged in LaTeX | Student action |
|---|----------------|-------------|------------------|----------------|
| 1 | CLIP-TSA XD = 82.19 (not 82.17 / 94.02) | **paper `tab:comparison` + fair-subset + full table** | YES (main.tex:397; full l.111) | **RE-CHECK** primary AUC@PR before submission |
| 2 | MGFN XD = 79.19 (I3D, not 80.11 VideoSwin) | **paper `tab:comparison` + fair-subset + full table** | YES (main.tex:399; full l.112) | **RE-CHECK** backbone label |
| 3 | GS-MoE 91.58 / 82.89 (MEDIUM, preprint) | full table only | YES (full l.102) | RE-CHECK ICCV camera-ready if kept in thesis |
| 4 | Holmes-VAD 89.51 / 90.67 (preprint, MLLM LoRA) | full table only | YES (full l.104) | RE-CHECK venue + note non-frozen |
| 5 | Holmes-VAU 88.96 / 87.68 (VIDEO-level) | full table only (disclosed) | YES (full l.106) | RE-CHECK / keep metric disclosure |
| 6 | PiercingEye XD = 88.82 (LOW, audio+visual+text) | full table only | YES (full l.115) | RE-CHECK TPAMI Table I |
| 7 | AnomalyCLIP 86.36 / 78.51 (LOW; not the 90.3 mAUC) | full table only | YES (full l.116) | RE-CHECK CVIU Tables 2/3 |
| 8 | FDPN 88.03 (LOW, self-report; XD N/A) | full table only | YES (full l.108) | RE-CHECK or drop |
| 9 | TEVAD XD ≈ 79.8 (MEDIUM) | full table only | YES (full l.117) | RE-CHECK headline value |
| 10 | Sultani XD 73.20 not from 2018 paper (Wu 2020) | **omitted as `---` in both** | YES (full l.123; footnote) | Already handled — XD cell omitted; confirm omission |
| 11 | RTFM XD 78.27 (CLIP) vs 77.81 (I3D own) | **77.81 cited in paper + standalone** | (77.81 verified, canonical I3D) | Confirm 77.81 (I3D) is the cited value — it is |
| 12 | EventVAD XD = 64.04 AP (not 87.51); LAVAD 62.01 (not 85.36) | full table only | YES (full l.120, l.122) | RE-CHECK AP vs AUC if kept |
| 13 | Ghadiya 86.34 / HyperVD 85.67 / HL-Net 78.64 — AUDIO-VISUAL | full table only (labelled audio) | YES (full l.124, l.125) | RE-CHECK modality labels |
| 14 | STPrompt & FDPN have NO XD number | full table (N/A) | YES (footnotes d, e) | Confirm N/A — done |
| 15 | Light-WVAD authors = Wang, Zhou & Guan (not "Sun et al.") | **paper `tab:comparison` + fair-subset** | bib `wang2024lightwvad` correctly attributes Wang/Zhou/Guan | Confirm bib author string — VERIFIED correct |
| 16 | PI-VAD (`majhi2025pivad`) & DSANet (`yin2026dsanet`) publication status / bib type (code-review WR-02) | **paper `tab:comparison`** | typed `@inproceedings` w/ arXiv id in `note` | **RE-CHECK** whether each is accepted to CVPR'25 / AAAI'26; if still preprint, retype as `@misc`/preprint with `eprint`+`archivePrefix`; if accepted, add real `pages`/`publisher` |
| 17 | PI-VAD & DSANet full author lists (code-review IN-02) | bib only (renders as "et al.") | `author = {... and others}` placeholder | Fill full author lists from the primary arXiv records before submission |

**Highest-priority manual re-checks for the SHIPPED paper (condensed table):** items **#1 (CLIP-TSA 82.19)**, **#2 (MGFN 79.19 I3D)**, **#11 (RTFM 77.81 I3D)**, and **#15 (Light-WVAD attribution)** — these are the four re-verify-list entries whose numbers/attributions actually appear in `paper/main.tex`. All are flagged/handled correctly as audited; the student should still confirm #1 and #2 against the primary PDFs before camera-ready. **Items #16–#17** are bib-hygiene follow-ups deferred from code review (WR-02 / IN-02) for the two preprint entries (PI-VAD, DSANet) — fold into the same publication-status pass.

---

## Threat register disposition (from 12-03-PLAN.md)

| Threat ID | Threat | Audit | Result |
|-----------|--------|-------|--------|
| T-12-04 | Un-verified number ships | Audit 2 (Traceability) | MITIGATED — 0 untraceable numbers |
| T-12-05 | Overclaim ships | Audit 3 (Overclaim scan) | MITIGATED — 0 disallowed hits |
| T-12-06 | Headline silently changed | Audit 4 (Headline integrity) | MITIGATED — Tables 1–3 byte-identical to baseline |

---

## Summary

All four audits PASS. The phase goal is provably met: an **honest, fully-verified** SOTA comparison ships in both the live CGW '26 paper (condensed `tab:comparison` + §2 backfill) and the standalone thesis fragment (full ~20-method table + fair subset + 5 positioning paragraphs), with **zero overclaim**, **every number traceable** to the verified research artifact (and the student's manual re-check items enumerated above), a **clean within-budget 11-page build** with all citations resolving, and **untouched headlines** (82.5 / 78.7 and the single-stream baselines byte-identical to the pre-phase git baseline).

**OVERALL: PASS.**
