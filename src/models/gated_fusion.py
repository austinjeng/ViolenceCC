"""Gated Fusion MIL variant (MOD-06).

Architecture (PRD 9.2 / RESEARCH.md 8.D):
  skel [B,T,256] -> Linear(256->256) -> ln_skel -> p_skel [B,T,256]
  clip [B,T,1024]-> Linear(1024->256)-> ln_clip -> p_clip [B,T,256]
  gate  = sigmoid( Linear([p_skel; p_clip]) ) in [0, 1], shape [B,T,256]
  fused = gate * p_skel + (1 - gate) * p_clip
  residual = fused + p_skel + p_clip               # gradient highway
  out   = dropout(ln_fused(residual))
  scores = MILHead(out).squeeze(-1)                # [B, T]

D-07 LN inventory (>=3, discoverable via named_modules()):
  ln_skel   - after skeleton projection
  ln_clip   - after CLIP projection
  ln_fused  - at fusion output (3rd LN; required for Phase 5 TTA surface)

m1 mitigation (PITFALLS.md m1 - gate saturation early in training):
  Initialize gate Linear with Xavier uniform gain=0.1 -> mean(sigmoid(Wg*x+b)) ~= 0.5
  at step 0 for random inputs.
"""
from __future__ import annotations
import logging

import torch
import torch.nn as nn

from src.models.mil_head import MILHead

logger = logging.getLogger(__name__)

# D-15: keys that legitimately ride along in a model config block (e.g. from a
# config_snapshot replay) but are NOT constructor args; allow-listed so the
# unexpected-kwarg warning stays silent during normal replay.
_KNOWN_EXTRA_KWARGS = frozenset({"variant", "strategy", "cache_variant", "backbone"})


class GatedFusion(nn.Module):
    """Gated score-level fusion with 3 named LayerNorms (MOD-06, MOD-07).

    All 3 LNs are exposed as direct attributes (ln_skel, ln_clip, ln_fused) so
    Phase 5 TTA can collect their (gamma, beta) affine parameters without an
    opaque named_modules() traversal.
    """

    def __init__(
        self,
        skel_dim: int = 256,
        clip_dim: int = 1024,
        shared_dim: int = 256,
        head_hidden=(128, 32),
        dropout: float = 0.3,
        **unused,
    ) -> None:
        super().__init__()

        # D-15: warn (never raise) about unknown kwargs swallowed by **unused, so a
        # typo'd hyperparameter does not silently fall back to a default. Known
        # replay-only keys are skipped to keep config_snapshot replay quiet.
        _unexpected = [k for k in unused if k not in _KNOWN_EXTRA_KWARGS]
        if _unexpected:
            # C1-3 (supersedes the D-15 warn-only policy): fail loud on a typo'd
            # hyperparameter rather than silently dropping it to a default. Known
            # replay-only keys are allow-listed above. The primary gate is
            # build_model(); this protects direct construction too.
            raise ValueError(
                f"GatedFusion: unexpected kwargs {sorted(_unexpected)} (possible typo?). "
                "Remove or correct the config key; only "
                f"{sorted(_KNOWN_EXTRA_KWARGS)} ride along as replay keys."
            )

        # Modality projections into shared_dim
        self.skel_proj = nn.Linear(skel_dim, shared_dim)
        self.ln_skel = nn.LayerNorm(shared_dim)

        self.clip_proj = nn.Linear(clip_dim, shared_dim)
        self.ln_clip = nn.LayerNorm(shared_dim)

        # Gate: [p_skel; p_clip] (2*shared_dim) -> shared_dim, then sigmoid
        self.gate = nn.Linear(2 * shared_dim, shared_dim)
        # m1 mitigation: small init so initial gate ~= sigmoid(0) = 0.5
        nn.init.xavier_uniform_(self.gate.weight, gain=0.1)
        nn.init.zeros_(self.gate.bias)

        self.ln_fused = nn.LayerNorm(shared_dim)
        self.dropout = nn.Dropout(dropout)
        self.head = MILHead(input_dim=shared_dim,
                            hidden_dims=tuple(head_hidden),
                            dropout=dropout)

    def forward(self, skel=None, clip=None, mask=None):
        if skel is None or clip is None:
            raise ValueError("GatedFusion requires both `skel` and `clip` inputs")

        p_skel = self.ln_skel(self.skel_proj(skel))          # [B, T, shared_dim]
        p_clip = self.ln_clip(self.clip_proj(clip))          # [B, T, shared_dim]

        g = torch.sigmoid(self.gate(torch.cat([p_skel, p_clip], dim=-1)))
        fused = g * p_skel + (1.0 - g) * p_clip               # [B, T, shared_dim]

        residual = fused + p_skel + p_clip                    # gradient highway
        out = self.dropout(self.ln_fused(residual))

        return self.head(out).squeeze(-1)                     # [B, T]
