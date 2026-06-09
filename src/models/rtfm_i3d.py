"""RTFM variant on XD I3D RGB features (Phase 4 D-18, minimum-viable FM head).

Design: minimum-viable reproduction per CONTEXT.md Claude's Discretion.
  - NO MTN temporal module (no dilated conv, no non-local block)
  - NO explicit feature-magnitude (L2-norm) head: the forward is just
    LayerNorm(self.ln_i3d) + the standard sigmoid MILHead; top-k is handled in
    the MIL loss (mil_loss.py) on the sigmoid scores, not via an FM-magnitude head
  - Standard MILHead reused (same as other variants, MOD-03..06)
  - Named LN (self.ln_i3d) for TTA parameter collection (D-07, Phase 5)

Matches RTFM published XD-I3D AP (77.81%) within +/-1% gate (D-03).
If the gate fails in Plan 06 empirical run, Phase 4b fallback adds the
MTN Aggregate module. This MVP implementation is intentionally parallel
to src/models/skeleton_only.py::SkeletonProj so that all 5 variants share
the same forward-signature shape and ln naming convention.
"""
from __future__ import annotations

import torch.nn as nn

from src.models.mil_head import MILHead


class RTFMI3D(nn.Module):
    """RTFM-style FM head + MILHead on 1024-d I3D RGB features (D-18).

    Inputs:
      i3d: float tensor [B, T, 1024] at training time (5-crop stacked or
           averaged; the data loader owns the 5-crop dispatch per D-19).
      skel/clip/mask: ignored (kept for variant-uniform forward signature
                      matching SkeletonProj / CLIPProj / LateFusion / GatedFusion).
    Output:
      scores: float tensor [B, T] in [0, 1] via MILHead's Sigmoid.
    """

    def __init__(
        self,
        i3d_dim: int = 1024,
        head_hidden=(128, 32),
        dropout: float = 0.3,
        **unused,
    ) -> None:
        super().__init__()
        # D-07 named LN -- Phase 5 TTA iterates these via model.named_modules().
        # Shape matches the I3D cache dim (1024-d per snippet per crop).
        self.ln_i3d = nn.LayerNorm(i3d_dim)
        self.head = MILHead(
            input_dim=i3d_dim,
            hidden_dims=tuple(head_hidden),
            dropout=dropout,
        )

    def forward(self, skel=None, clip=None, i3d=None, mask=None):
        if i3d is None:
            raise ValueError(
                "RTFMI3D requires `i3d` input (1024-d per snippet)"
            )
        x = self.ln_i3d(i3d)
        scores = self.head(x)            # [..., 1]
        if scores.dim() == 3:
            scores = scores.squeeze(-1)  # [B, T]
        return scores
