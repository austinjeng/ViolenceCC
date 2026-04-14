"""TRN-01: SequentialLR(linear warmup -> cosine decay) + AdamW config."""
import math
import pytest
import torch
from torch.optim import AdamW

from src.utils.scheduler import build_optimizer, build_scheduler


def _make_cfg(epochs=50, warmup=5):
    return {
        "lr": 1e-4, "weight_decay": 1e-2,
        "epochs": epochs, "warmup_epochs": warmup,
    }


def test_linear_cosine():
    """LR at epoch 0 ~= lr*0.01; at epoch=warmup ~= lr; at final epoch ~= 0."""
    model = torch.nn.Linear(4, 2)
    cfg = _make_cfg(epochs=50, warmup=5)
    opt = build_optimizer(model.parameters(), cfg)
    sched = build_scheduler(opt, cfg)

    lrs = []
    for epoch in range(50):
        lrs.append(opt.param_groups[0]["lr"])
        sched.step()

    assert lrs[0] == pytest.approx(1e-4 * 0.01, rel=1e-3), f"epoch0 lr={lrs[0]}"
    # After warmup_epochs steps of LinearLR, LR should be at (or very near) the base lr
    assert lrs[5] == pytest.approx(1e-4, rel=1e-3), f"epoch5 lr={lrs[5]}"
    # Cosine should drive LR toward 0 by final epoch
    assert lrs[-1] < lrs[5] * 0.1, f"final lr={lrs[-1]} too high (cosine decay failed?)"


def test_optimizer_config():
    """AdamW built with the exact cfg lr/weight_decay."""
    model = torch.nn.Linear(4, 2)
    opt = build_optimizer(model.parameters(), _make_cfg())
    assert isinstance(opt, AdamW)
    assert opt.param_groups[0]["lr"] == 1e-4
    assert opt.param_groups[0]["weight_decay"] == 1e-2
