"""CLIP-Only MIL variant (MOD-04).

Architecture per RESEARCH.md 8.B:
  clip [B,T,1024] -> Linear(1024->512) -> ln_clip -> MILHead(512->128->32->1, Sigmoid)

D-07: `ln_clip` is a named nn.LayerNorm for Phase 5 TTA discoverability.
Phase 2 D-06 keeps CLIP cache at 1024-d (mean+max); the learned 512-d
projection lives here, not in the extraction pipeline.
"""
from __future__ import annotations
import torch
import torch.nn as nn

from src.models.mil_head import MILHead


class CLIPProj(nn.Module):
    """CLIP-only MIL head baseline (MOD-04).

    Inputs:
      skel: ignored (keyword-only)
      clip: float tensor [B, T, clip_dim]  (Phase 2 CLIP cache, 1024-d)
      mask: ignored here
    Output:
      scores: float tensor [B, T] in [0, 1]
    """

    def __init__(
        self,
        clip_dim: int = 1024,
        proj_dim: int = 512,
        head_hidden=(128, 32),
        dropout: float = 0.3,
        **unused,
    ) -> None:
        super().__init__()
        self.clip_proj = nn.Linear(clip_dim, proj_dim)
        self.ln_clip = nn.LayerNorm(proj_dim)         # D-07: named LN
        self.head = MILHead(input_dim=proj_dim,
                            hidden_dims=tuple(head_hidden),
                            dropout=dropout)

    def forward(self, skel=None, clip=None, mask=None):
        if clip is None:
            raise ValueError("CLIPProj requires `clip` input")
        x = self.clip_proj(clip)                      # [B, T, 512]
        x = self.ln_clip(x)
        scores = self.head(x)                         # [B, T, 1]
        return scores.squeeze(-1)                     # [B, T]
