---
quick_id: 260604-vfi
slug: align-paper-loss-equations-with-mil-loss
date: 2026-06-04
type: quick
status: complete
commit: c163eb6
files-modified:
  - paper/main.tex
---

# Quick Task 260604-vfi: Align paper loss equations with `mil_loss.py` — Summary

Aligned `paper/main.tex` §3.5 (MIL Training with Ranking Loss) so the ranking and
sparsity equations describe the loss `src/losses/mil_loss.py` actually computes — a
transparency/reproducibility fix with no code change, no numeric change, and the
smoothness term left untouched.

## What changed

Four exact string replacements in `paper/main.tex` (verified verbatim against the
code source of truth before editing):

| # | Line | Before | After |
|---|------|--------|-------|
| 1a | 175 | "...highest-scoring snippet in the anomalous bag to exceed the highest-scoring snippet in the normal bag by a margin:" | "...mean of the top-$k$ scores in the anomalous bag to exceed that of the normal bag by a margin:" |
| 1b | 177 | `\mathcal{L}_{\text{rank}} = \max\left(0, 1 - \max_{i \in \mathcal{A}_k} a_i + \max_{j \in \mathcal{N}_k} a_j\right)` | `\mathcal{L}_{\text{rank}} = \max\left(0,\; 1 - \frac{1}{k}\sum_{i \in \mathcal{A}_k} a_i + \frac{1}{k}\sum_{j \in \mathcal{N}_k} a_j\right)` |
| 1c | 181 | `\mathcal{L} = \mathcal{L}_{\text{rank}} + \lambda_1 \sum_i a_i + \lambda_2 \sum_i (a_i - a_{i+1})^2` | `\mathcal{L} = \mathcal{L}_{\text{rank}} + \frac{\lambda_1}{T}\sum_{t=1}^{T} \left\| \mathbf{a}_t \right\|_2 + \lambda_2 \sum_i (a_i - a_{i+1})^2` |
| 1d | 184 | "The sparsity term encourages most snippets to receive low anomaly scores, reflecting the prior that anomalous events occupy a small fraction of each video's duration." | Prepended where-clause defining $\mathbf{a}_t$ (abnormal-bag scores at snippet position $t$ across batch) and stating the RTFM mean-over-positions-of-per-position-$\ell_2$-norm formulation, then the original sentence. |

## Source-of-truth verification (no code touched)

- **Ranking** — `mil_loss.py:77` `torch.topk(scores_masked, k=k, dim=1).values.mean(dim=1)` = mean of top-k. Paper previously wrote `\max` (ignores k). Now `\frac{1}{k}\sum`. ✓
- **Sparsity** — `mil_loss.py:30` `lam * torch.mean(torch.norm(scores_abn, dim=0))` over abnormal-bag `[B, T]` = mean over snippet positions of the per-position L2 norm across the bag (RTFM L1-via-L2-column). Paper previously wrote the L1 sum `\lambda_1 \sum_i a_i`. Now `\frac{\lambda_1}{T}\sum_t \|\mathbf{a}_t\|_2`. ✓
- **Smoothness** — `mil_loss.py:51-54` temporal-axis L2 diff, already matches paper's `\lambda_2 \sum_i (a_i - a_{i+1})^2`. Left unchanged per plan. ✓
- $\lambda_1 = 8\times10^{-3}$ and the dataset-dependent $\lambda_2$ language unchanged. No reported number changed.

## Build (CLAUDE.md convention)

Ran `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean`.

- **Exit code:** 0
- **PDF:** `paper/main.pdf` regenerated — 9 pages, 948134 bytes, mtime 2026-06-04 22:41:19.
- **Log scan (`paper/main.log`):** no `!`, no "Undefined control sequence", no "Missing", no LaTeX/Package errors. `\frac`, `\mathbf`, `\ell`, `\|`, `\sum` all resolved cleanly (amsmath via acmart).
- The only "major issue" lines are MiKTeX's "you have not checked for updates" notices — benign, unrelated to the edits.

## Deviations from Plan

None — plan executed exactly as written. All four `old_string` fragments matched verbatim on the first attempt.

## Commit

- `c163eb6` — `docs(260604-vfi): align paper loss equations (ranking mean-of-top-k, sparsity RTFM L2 column-norm) with mil_loss.py` (1 file changed, 4 insertions(+), 4 deletions(-))
- Only `paper/main.tex` staged; build artifacts (git-ignored) not committed. Verified via `git status` before commit.

## Self-Check: PASSED

- `paper/main.tex` modified and committed in `c163eb6` (`git log` confirms).
- `paper/main.pdf` exists, freshly regenerated (mtime 22:41:19).
- New equation forms present (`\frac{1}{k}\sum`, `\mathbf{a}_t`); old forms (`\max_{i \in \mathcal{A}_k}`, `\lambda_1 \sum_i a_i`) absent.
