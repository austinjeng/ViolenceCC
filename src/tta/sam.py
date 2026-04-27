"""Sharpness-Aware Minimization (SAM) optimizer.

Ported from the official SAR repository (https://github.com/mr-eggplant/SAR,
ICLR 2023 Oral, MIT License).  SAM performs a two-step update:
  1. first_step: perturb parameters toward the high-loss region (ascent)
  2. second_step: compute gradient at the perturbed point, undo perturbation,
     then take a standard optimizer step (descent)

Used by SarAdaptor (src/tta/sar.py) for sharpness-aware TTA.
"""
from __future__ import annotations

import torch


class SAM(torch.optim.Optimizer):
    """Sharpness-Aware Minimization optimizer wrapping a base optimizer.

    Args:
        params: Iterable of parameters to optimize (typically LN affine only).
        base_optimizer: Optimizer class (e.g. ``torch.optim.SGD``).
        rho: Neighbourhood radius for perturbation.  D-11 grid:
             {0.001, 0.005, 0.01, 0.05, 0.1}.
        **kwargs: Forwarded to *base_optimizer* (lr, momentum, etc.).
    """

    def __init__(self, params, base_optimizer, rho: float = 0.05, **kwargs):
        defaults = dict(rho=rho, **kwargs)
        super().__init__(params, defaults)
        self.base_optimizer = base_optimizer(self.param_groups, **kwargs)

    # ------------------------------------------------------------------
    # Two-step update
    # ------------------------------------------------------------------

    @torch.no_grad()
    def first_step(self):
        """Ascent step: perturb params toward high-loss region."""
        grad_norm = self._grad_norm()
        for group in self.param_groups:
            scale = group["rho"] / (grad_norm + 1e-12)
            for p in group["params"]:
                if p.grad is None:
                    continue
                e_w = p.grad * scale
                p.add_(e_w)  # climb
                self.state[p]["e_w"] = e_w

    @torch.no_grad()
    def second_step(self):
        """Descent step: undo perturbation, then take base optimizer step."""
        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                p.sub_(self.state[p]["e_w"])  # restore
        self.base_optimizer.step()

    @torch.no_grad()
    def zero_grad(self, set_to_none: bool = True):  # noqa: D401
        """Zero gradients in both SAM and the base optimizer."""
        super().zero_grad(set_to_none=set_to_none)
        self.base_optimizer.zero_grad(set_to_none=set_to_none)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _grad_norm(self) -> torch.Tensor:
        norm = torch.norm(
            torch.stack(
                [
                    p.grad.norm()
                    for group in self.param_groups
                    for p in group["params"]
                    if p.grad is not None
                ]
            )
        )
        return norm
