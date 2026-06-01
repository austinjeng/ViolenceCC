---
phase: quick
plan: 260601-gap
subsystem: thesis-manuscript
tags: [paper, latex, methodology-correction, editorial]
requires: [paper/main.tex]
provides: ["Corrected methodology prose and reported hyperparameters in paper/main.tex"]
affects: [paper/main.tex]
tech-stack:
  added: []
  patterns: ["verbatim OLD->NEW LaTeX edits", "structural grep + brace-balance verification (no TeX toolchain)"]
key-files:
  created: []
  modified: [paper/main.tex]
decisions:
  - "Numbers stay, only descriptions corrected — code review found prose misdescribed real, reproducible runs"
  - "XD headline = 74.7% AP (SigLIP2 Base), matching Table 2 bold, not SO400M 73.8"
  - "Structural verification (braces + grep) used in place of compile — no latexmk/pdflatex/xelatex on PATH"
metrics:
  duration: ~5min
  completed: 2026-06-01
---

# Quick Task 260601-gap: Reconcile main.tex Methodology with Actual Configs/Results Summary

Editorial reconciliation of `paper/main.tex` — applied 15 verbatim OLD->NEW edits so the abstract, methodology (§3.2/§3.4/§3.5), implementation details (§4.2), TTA section (§5), discussion, and conclusion match the actual experimental configuration that produced the reported (real, reproducible) numbers. No code touched, no experiments re-run.

## Edits Applied (15 verbatim OLD -> NEW)

1. **Abstract XD headline** — `73.8\% AP on XD-Violence (SigLIP2 SO400M)` -> `74.7\% AP on XD-Violence (SigLIP2 Base)` (matches Table 2 bold).
2. **Abstract "end-to-end"** — `trained end-to-end with multiple instance learning (MIL) ranking loss.` -> `trained with multiple instance learning (MIL) ranking loss on frozen backbone features (only the lightweight fusion head is learned).`
3. **§3 overview "end-to-end"** — `and trained end-to-end with MIL ranking loss.` -> `and trained with MIL ranking loss (only the fusion head and classifier are learned; both backbones are frozen).`
4. **§3.2 stream combination** — `The four-stream features are concatenated to form the final skeleton representation.` -> `...combined by weighted averaging (joint and bone weighted 1.0, motion streams 0.5) to form the final 256-d skeleton representation.`
5. **§3.4 shared dim** — `projected to a shared 512-d space and normalized:` -> `projected to a shared 256-d space and normalized:`
6. **§3.5 lambda weights** — `$\lambda_1 = 8 \times 10^{-5}$ and $\lambda_2 = 8 \times 10^{-5}$ following RTFM~\cite{tian2021rtfm}.` -> `sparsity weight $\lambda_1 = 8 \times 10^{-3}$ and the smoothness weight $\lambda_2 = 8 \times 10^{-4}$.`
7. **§4.2 optimizer + lr** — `Adam ... lr $5 \times 10^{-4}$ (UCF) / $1 \times 10^{-3}$ (XD).` -> `AdamW (weight decay $10^{-2}$) ... lr $1 \times 10^{-4}$ for both datasets.`
8. **§4.2 batch + epochs** — `batch size of 32 video pairs ... maximum of 100 epochs` -> `batch size of 16 normal/anomalous pairs (32 videos per batch) ... maximum of 50 epochs`.
9. **§4.2 top-k** — `$k=3$ for UCF-Crime and $k=2$ for XD-Violence.` -> `$k=3$ for both datasets.`
10. **§4.2 fabricated sweep removed** — `...systematic sweep of 198 configurations ... (+3.7 percentage points ... +0.1 points).` -> `We use a fixed hyperparameter configuration across both datasets (learning rate $1 \times 10^{-4}$, $k=3$, margin $1.0$).`
11. **§4.2 frame broadcast** — `...zero-padded where snippet boundaries exceed the video length.` -> `...the final snippet's score is repeated to cover any trailing frames.`
12. **§5 TTA per-backbone configs** — single "500 total runs" CLIP search applied to all -> CLIP search (TENT lr=0.005; SAR lr=0.0001, $\rho$=0.01) + SigLIP2 fixed config (TENT lr=0.001; SAR lr=0.001, $\rho$=0.05).
13. **§5 Discussion param count** — `approximately 0.8M parameters regardless of the visual backbone dimension` -> `0.50M (CLIP) to 1.02M (SigLIP2 Giant) trainable parameters, scaling with the visual feature dimension $d_v$`.
14. **§7 Conclusion UCF wording** — `best UCF-Crime performance (83.3\% AUC with gated fusion)` -> `best UCF-Crime results (83.3\% AUC with gated fusion, 83.6\% with mean-only pooling)` (no longer contradicts Limitations' 83.6).
15. **§7 Conclusion param repetition** — `(approximately 0.8M parameters)` -> `(0.5--1.0M parameters depending on backbone)`.

EDIT 13 and EDIT 15 (both containing "approximately 0.8M parameters") were disambiguated by matching their full unique OLD strings.

## Verification Result

No LaTeX toolchain on PATH (`where latexmk` / `pdflatex` / `xelatex` all returned not-found in cp950 locale), so a structural check was used in place of a compile, per plan TOOLCHAIN NOTE.

| Check | Result |
|-------|--------|
| Brace balance (unescaped `{` vs `}`) | 299 / 299 — BALANCED |
| Stale OLD strings remaining (15) | NONE |
| NEW strings present (15) | ALL PRESENT (MISSING_NEW: NONE) |
| Empty `\cite{}` / `\ref{}` | 0 / 0 |
| Dangling `\cite{ ` / `\ref{ ` (trailing whitespace) | 0 / 0 |
| Total `\cite{` / `\ref{` commands intact | 44 / 9 |
| Protected: abstract "+0.6\% for CLIP with SAR" | present (untouched) |
| Protected: "172 videos in UCF-Crime" claim | present (untouched) |

Equations ($\mathcal{L}$, $\mathbf{f}_{\text{late}}$, $\mathbf{f}_{\text{gated}}$), all Table values, `tables_generated.tex`, and §5 source-only/TTA table values were not modified.

## Deviations from Plan

None — plan executed exactly as written. All 15 OLD strings matched verbatim; all edits applied mechanically with no paraphrasing.

A temporary helper script (`scripts/_verify_gap.py`) was created to run the dangling-cite/ref regex (Bash heredoc was mangling backslashes) and removed before commit. It was never staged or committed.

## Commit

- `a12b64e` — `docs(paper): reconcile main.tex methodology with actual configs/results` (1 file changed, 11 insertions, 11 deletions; only `paper/main.tex` staged)

## Self-Check: PASSED

- `paper/main.tex` exists and is committed (verified via git).
- Commit `a12b64e` exists in git log.
- All 15 NEW strings present; all 15 OLD strings absent; braces balanced; cites/refs intact.
