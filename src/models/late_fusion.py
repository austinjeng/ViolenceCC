"""Late Fusion MIL variant (MOD-05).

Architecture per RESEARCH.md 8.C:
  s_skel = SkeletonProj(skel)            # [B, T]  (per-snippet score from skeleton)
  s_clip = CLIPProj(clip)                # [B, T]
  alpha  = 0.5 (equal)  OR  sigmoid(alpha_logit) (learned)
  out    = alpha * s_skel + (1 - alpha) * s_clip

CONTEXT.md Claude's Discretion: default to equal-weighted. Switch to learned
scalar alpha only if equal weighting underperforms either single-modal baseline.
"""
from __future__ import annotations
import torch
import torch.nn as nn

from src.models.skeleton_only import SkeletonProj
from src.models.clip_only import CLIPProj


class LateFusion(nn.Module):
    """Score-level average of SkeletonProj and CLIPProj (MOD-05).

    alpha: 'equal' (default) or 'learned'
    """

    def __init__(
        self,
        skel_dim: int = 256,
        clip_dim: int = 1024,
        proj_dim: int = 512,
        head_hidden=(128, 32),
        dropout: float = 0.3,
        alpha: str = "equal",
        **unused,
    ) -> None:
        super().__init__()
        if alpha not in ("equal", "learned"):
            raise ValueError(f"alpha must be 'equal' or 'learned', got {alpha}")
        self.alpha_mode = alpha

        self.skeleton = SkeletonProj(
            skel_dim=skel_dim,
            head_hidden=head_hidden,
            dropout=dropout,
        )
        self.clip = CLIPProj(
            clip_dim=clip_dim,
            proj_dim=proj_dim,
            head_hidden=head_hidden,
            dropout=dropout,
        )

        if alpha == "learned":
            # sigmoid(0) = 0.5 -> effective equal weighting at init
            self.alpha_logit = nn.Parameter(torch.zeros(1))
        else:
            self.register_parameter("alpha_logit", None)

    def _alpha(self) -> torch.Tensor:
        if self.alpha_logit is not None:
            return torch.sigmoid(self.alpha_logit)
        return torch.tensor(0.5, device=self._device())

    def _device(self):
        # Helper: infer device from first parameter
        return next(self.parameters()).device

    def forward(self, skel=None, clip=None, mask=None):
        if skel is None or clip is None:
            raise ValueError("LateFusion requires both `skel` and `clip` inputs")
        s_skel = self.skeleton(skel=skel)   # [B, T]
        s_clip = self.clip(clip=clip)        # [B, T]
        a = self._alpha()
        return a * s_skel + (1 - a) * s_clip
