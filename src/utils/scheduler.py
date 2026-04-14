"""SequentialLR = LinearLR warmup -> CosineAnnealingLR decay (TRN-01).

PRD 11.1 hyperparameter table:
  epochs=50, warmup_epochs=5, lr=1e-4, weight_decay=1e-2
"""
from __future__ import annotations

import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR


def build_optimizer(params, train_cfg: dict):
    """AdamW with lr / weight_decay from cfg['train']."""
    return AdamW(
        params,
        lr=float(train_cfg["lr"]),
        weight_decay=float(train_cfg["weight_decay"]),
    )


def build_scheduler(optimizer: torch.optim.Optimizer, train_cfg: dict):
    """SequentialLR(linear warmup -> cosine decay).

    train_cfg keys used:
      epochs (int)         total epochs, e.g. 50
      warmup_epochs (int)  e.g. 5
    """
    epochs = int(train_cfg["epochs"])
    warmup = int(train_cfg["warmup_epochs"])
    cosine_epochs = max(1, epochs - warmup)

    warmup_sched = LinearLR(
        optimizer,
        start_factor=0.01,
        end_factor=1.0,
        total_iters=warmup,
    )
    cosine_sched = CosineAnnealingLR(
        optimizer,
        T_max=cosine_epochs,
        eta_min=0.0,
    )
    return SequentialLR(
        optimizer,
        schedulers=[warmup_sched, cosine_sched],
        milestones=[warmup],
    )
