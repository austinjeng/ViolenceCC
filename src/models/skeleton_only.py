"""Skeleton-Only MIL variant (MOD-03).

Architecture per RESEARCH.md 8.A:
  skel [B,T,256] -> ln_skel -> MILHead(256 -> 128 -> 32 -> 1, Sigmoid)

D-07: `ln_skel` is a named nn.LayerNorm for Phase 5 TTA discoverability.
"""
from __future__ import annotations
import torch
import torch.nn as nn

from src.models.mil_head import MILHead


class SkeletonProj(nn.Module):
    """Skeleton-only MIL head baseline (MOD-03).

    Inputs:
      skel: float tensor [B, T, skel_dim]  (Phase 2 skeleton cache)
      clip: ignored (keyword-only, for variant-uniform forward signature)
      mask: ignored here (applied at loss time by mil_ranking_loss)
    Output:
      scores: float tensor [B, T] in [0, 1]
    """

    def __init__(
        self,
        skel_dim: int = 256,
        head_hidden=(128, 32),
        dropout: float = 0.3,
        **unused,
    ) -> None:
        super().__init__()
        self.ln_skel = nn.LayerNorm(skel_dim)        # D-07: named LN for TTA
        self.head = MILHead(input_dim=skel_dim,
                            hidden_dims=tuple(head_hidden),
                            dropout=dropout)

    def forward(self, skel=None, clip=None, mask=None):
        if skel is None:
            raise ValueError("SkeletonProj requires `skel` input")
        x = self.ln_skel(skel)                        # [B, T, skel_dim]
        scores = self.head(x)                         # [B, T, 1]
        return scores.squeeze(-1)                     # [B, T]
