"""Shared MIL classification head (D-05, D-06).

3-layer MLP with Sigmoid output. Hidden widths 128 -> 32 match RTFM/MGFN
convention. Reused identically by all 4 variant wrappers so that head
differences are zero by construction — ablations isolate fusion effects.
"""
from __future__ import annotations
from typing import Sequence

import torch.nn as nn


class MILHead(nn.Module):
    """Linear(D->128) -> ReLU -> Dropout(0.3) -> Linear(128->32) -> ReLU -> Dropout(0.3) -> Linear(32->1) -> Sigmoid.

    Args:
        input_dim: feature width D coming into the head
        hidden_dims: (128, 32) by D-06; override only for ablations
        dropout: 0.3 by D-05
    """

    def __init__(self, input_dim: int, hidden_dims: Sequence[int] = (128, 32),
                 dropout: float = 0.3) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        prev = input_dim
        for h in hidden_dims:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(dropout)]
            prev = h
        layers += [nn.Linear(prev, 1), nn.Sigmoid()]
        self.mlp = nn.Sequential(*layers)

    def forward(self, x):
        # Accepts [B, T, D] or [B, D]; Linear broadcasts over leading dims.
        return self.mlp(x)  # [..., 1]
