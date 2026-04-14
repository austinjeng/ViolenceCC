"""MIL Ranking Loss with sparsity + smoothness regularizers (MOD-01).

Implements the top-k MIL Ranking Loss from RTFM (Tian et al., ICCV 2021)
with the project-specific decisions:

  D-01: top-k = 3
  D-02: hinge margin = 1.0  (on sigmoid scores in [0,1], NOT RTFM's 100
        which is on feature magnitudes)
  D-03: lam_sparse = 8e-3, lam_smooth = 8e-4  (RTFM exact)
  D-10: zero-padded positions are masked to -inf before top-k

References:
  - RTFM upstream train.py (WebFetch 2026-04-14) - see RESEARCH.md Section 1.1
  - RESEARCH.md Section 1.5 - verified implementation template
"""
from __future__ import annotations

import torch


def _sparsity(scores_abn: torch.Tensor, lam: float = 8e-3) -> torch.Tensor:
    """RTFM-exact L1-via-L2-column sparsity on abnormal-bag scores.

    Formula (verbatim from RTFM train.py):
        loss = torch.mean(torch.norm(arr, dim=0))
        return lam * loss

    arr: [B_abn, T] sigmoid scores in [0, 1]
    """
    return lam * torch.mean(torch.norm(scores_abn, dim=0))


def _smoothness(scores_abn: torch.Tensor, lam: float = 8e-4) -> torch.Tensor:
    """RTFM-exact L2 smoothness on adjacent-snippet score differences.

    Formula (verbatim from RTFM train.py - arr2-shift pattern, NOT np.roll):
        arr2 = torch.zeros_like(arr)
        arr2[:-1] = arr[1:]
        arr2[-1]  = arr[-1]
        loss = torch.sum((arr2 - arr) ** 2)
        return lam * loss

    The boundary `arr2[-1] = arr[-1]` makes the final position's diff = 0,
    preventing an artificial penalty at the bag boundary.
    """
    arr2 = torch.zeros_like(scores_abn)
    arr2[:-1] = scores_abn[1:]
    arr2[-1] = scores_abn[-1]
    return lam * torch.sum((arr2 - scores_abn) ** 2)


def mil_ranking_loss(
    scores: torch.Tensor,    # [2B, T] sigmoid scores in [0,1]; normal first, then abnormal
    mask: torch.Tensor,      # [2B, T] 1.0 where real snippet, 0.0 where zero-padded (D-10)
    n_normal: int,           # B (= 16 per D-04)
    k: int = 3,              # D-01
    margin: float = 1.0,     # D-02
    lam_sparse: float = 8e-3,  # D-03
    lam_smooth: float = 8e-4,  # D-03
) -> torch.Tensor:
    """Top-k MIL Ranking Loss with sparsity + smoothness. Masked for padded positions.

    Structure:
      1. Mask padded positions to -inf so they cannot win top-k (D-10).
      2. Mean of top-k scores per bag, split into normal and abnormal halves.
      3. Hinge rank loss paired by index (D-04 paired bags).
      4. Sparsity + smoothness regularizers on abnormal-bag scores ONLY
         (masked to zero at padded positions so padding does not bias reg).
    """
    # Step 1: mask for top-k
    scores_masked = scores.masked_fill(mask == 0, float("-inf"))
    topk_vals = torch.topk(scores_masked, k=k, dim=1).values.mean(dim=1)
    topk_nor = topk_vals[:n_normal]
    topk_abn = topk_vals[n_normal:]

    # Step 2: paired hinge (D-04)
    rank = torch.relu(margin - topk_abn + topk_nor).mean()

    # Step 3: regularizers on abnormal scores only, zero-padded positions zeroed
    scores_abn_real = scores[n_normal:] * mask[n_normal:]
    reg = (_sparsity(scores_abn_real, lam_sparse)
           + _smoothness(scores_abn_real, lam_smooth))

    return rank + reg
