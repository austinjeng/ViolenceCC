---
quick_id: 260604-vfi
slug: align-paper-loss-equations-with-mil-loss
date: 2026-06-04
type: quick
status: planned
---

# Quick Task 260604-vfi: Align paper loss equations with `mil_loss.py`

## Goal

Two equations in `paper/main.tex` §3.5 (MIL Training with Ranking Loss) describe a
different loss than the one `src/losses/mil_loss.py` actually computes (the loss that
produced every reported number). Make the **paper** match the **code**. This is a
transparency/reproducibility fix only — **no code changes, no reported numbers change.**

Verified mismatches (re-read against `src/losses/mil_loss.py`):
- **Ranking term** — code uses `torch.topk(...).values.mean(dim=1)` (mean of top-k),
  paper Eq. writes `\max_{i\in\mathcal{A}_k} a_i` (max of the top-k set, which ignores k).
- **Sparsity term** — code is `lam * torch.mean(torch.norm(scores_abn, dim=0))` over the
  abnormal-bag score matrix `[B, T]` (RTFM L2-column-norm = mean over snippet positions of
  the per-position L2 norm across the bag), paper Eq. writes the L1 sum `\lambda_1 \sum_i a_i`.
- Smoothness term already matches (`mil_loss.py:51-54`) — leave unchanged.

## Tasks

### Task 1 — Edit the three LaTeX fragments in `paper/main.tex`

Apply these EXACT string replacements (preserve surrounding text exactly):

**1a. Ranking prose (line ~175).** Replace:
```
The ranking loss encourages the highest-scoring snippet in the anomalous bag to exceed the highest-scoring snippet in the normal bag by a margin:
```
with:
```
The ranking loss encourages the mean of the top-$k$ scores in the anomalous bag to exceed that of the normal bag by a margin:
```

**1b. Ranking equation (line ~177).** Replace:
```
    \mathcal{L}_{\text{rank}} = \max\left(0, 1 - \max_{i \in \mathcal{A}_k} a_i + \max_{j \in \mathcal{N}_k} a_j\right)
```
with:
```
    \mathcal{L}_{\text{rank}} = \max\left(0,\; 1 - \frac{1}{k}\sum_{i \in \mathcal{A}_k} a_i + \frac{1}{k}\sum_{j \in \mathcal{N}_k} a_j\right)
```

**1c. Total-loss equation (line ~181).** Replace:
```
    \mathcal{L} = \mathcal{L}_{\text{rank}} + \lambda_1 \sum_i a_i + \lambda_2 \sum_i (a_i - a_{i+1})^2
```
with:
```
    \mathcal{L} = \mathcal{L}_{\text{rank}} + \frac{\lambda_1}{T}\sum_{t=1}^{T} \left\| \mathbf{a}_t \right\|_2 + \lambda_2 \sum_i (a_i - a_{i+1})^2
```

**1d. Where-clause / sparsity explanation (line ~184).** Replace:
```
The sparsity term encourages most snippets to receive low anomaly scores, reflecting the prior that anomalous events occupy a small fraction of each video's duration.
```
with:
```
Here $\mathbf{a}_t$ is the vector of abnormal-bag anomaly scores at snippet position $t$ across the batch, so the sparsity term---following the feature-magnitude formulation of RTFM~\cite{tian2021rtfm}---is the mean over snippet positions of the per-position $\ell_2$ norm, computed over the abnormal bag. The sparsity term encourages most snippets to receive low anomaly scores, reflecting the prior that anomalous events occupy a small fraction of each video's duration.
```

- `files`: paper/main.tex
- `verify`: `grep -n "frac{1}{k}" paper/main.tex` returns the ranking eq; `grep -n "mathbf{a}_t" paper/main.tex` returns the sparsity eq; the `\max_{i \in \mathcal{A}_k} a_i` and `\lambda_1 \sum_i a_i` forms are gone.
- `done`: all four fragments replaced; smoothness term and every numeric value unchanged.

### Task 2 — Rebuild the PDF (CLAUDE.md convention)

Run from repo root:
```
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean
```
- `verify`: command exits 0 and `paper/main.pdf` is regenerated (newer mtime). Check `paper/main.log` for `Rerun`/undefined-reference/error lines related to eq:loss.
- `done`: clean compile, fresh `paper/main.pdf`, no new LaTeX errors introduced by the edits.

## Commit

Single atomic commit (code/source change = paper/main.tex only; build artifacts are
git-ignored, do NOT stage them):
```
docs(260604-vfi): align paper loss equations (ranking mean-of-top-k, sparsity RTFM L2 column-norm) with mil_loss.py
```

## Out of scope
- No change to `src/losses/mil_loss.py` or any code.
- No change to the smoothness term or any reported number.
- TTA dropout fix is a separate task (deferred).
