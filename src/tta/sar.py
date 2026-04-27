"""SAR-style TTA: TENT + Sharpness-Aware Minimisation + reliable entropy filtering.

Ported from the official SAR repository (https://github.com/mr-eggplant/SAR,
ICLR 2023 Oral, MIT License).

SAR adds two mechanisms over vanilla TENT (D-06):
  1. **SAM optimizer** -- sharpness-aware gradient step (first_step ascent +
     second_step descent) for flatter minima in the LN affine space.
  2. **Reliable entropy filtering** -- exclude high-entropy (unreliable) samples
     from the backward pass gradient, mitigating Pitfall M5 (normal-heavy batch
     entropy collapse).

Per Pitfall M6: rho must be grid-searched from {0.001..0.1}, not the ImageNet
default of 0.05-0.1.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from src.tta.sam import SAM
from src.tta.tent import binary_entropy, collect_params, configure_model, EPS  # noqa: F401 (re-export for convenience)


class SarAdaptor:
    """Per-video SAR adaptation with episodic reset.

    Args:
        model: GatedFusion model prepared via ``configure_model``.
        optimizer: A :class:`SAM` optimizer wrapping SGD or Adam.
        source_state: ``deepcopy`` of the initial ``model.state_dict()``.
        margin_e0: Entropy margin for reliable filtering.  Samples with entropy
            above this threshold are considered unreliable and excluded from the
            backward pass.  Default: ``0.4 * ln(2)`` (~0.277), scaled
            proportionally from ImageNet-C's 1000-class calibration.
    """

    def __init__(
        self,
        model: nn.Module,
        optimizer,
        source_state: dict,
        margin_e0: float = 0.4 * 0.6931,
    ):
        self.model = model
        self.optimizer = optimizer
        self.source_state = source_state
        self.margin_e0 = margin_e0
        # EMA for entropy tracking (SAR recovery mechanism)
        self.ema: float | None = None

    # ------------------------------------------------------------------
    # Per-video lifecycle
    # ------------------------------------------------------------------

    def reset(self):
        """Restore model to source state (per-video reset)."""
        self.model.load_state_dict(self.source_state, strict=False)
        if isinstance(self.optimizer, SAM):
            self.optimizer.base_optimizer.state = {}
        else:
            self.optimizer.state = {}
        self.ema = None

    # ------------------------------------------------------------------
    # Adapt + score
    # ------------------------------------------------------------------

    def adapt_and_score(
        self, skel: torch.Tensor, clip: torch.Tensor
    ) -> torch.Tensor:
        """SAR adapt: forward -> filter reliable -> SAM two-step -> return scores.

        Per D-07: returns scores from the FIRST forward pass (online scoring).
        """
        # -- First forward: compute entropy, collect scores ---------------
        scores = self.model(skel=skel, clip=clip)  # [B, T]
        entropies = binary_entropy(scores)  # [B, T]

        # -- Reliable entropy filtering -----------------------------------
        # Only backprop through low-entropy (confident) samples
        reliable_mask = entropies < self.margin_e0
        if reliable_mask.any():
            loss = entropies[reliable_mask].mean()
        else:
            loss = entropies.mean()  # fallback if no reliable samples

        loss.backward()
        self.optimizer.first_step()  # SAM ascent
        self.optimizer.zero_grad()

        # -- Second forward at perturbed point ----------------------------
        scores_perturbed = self.model(skel=skel, clip=clip)
        entropies_p = binary_entropy(scores_perturbed)
        if reliable_mask.any():
            loss_p = entropies_p[reliable_mask.detach()].mean()
        else:
            loss_p = entropies_p.mean()
        loss_p.backward()
        self.optimizer.second_step()  # SAM descent + actual param update
        self.optimizer.zero_grad()

        # -- EMA tracking for recovery (SAR mechanism) --------------------
        ent_val = entropies.mean().item()
        if self.ema is None:
            self.ema = ent_val
        else:
            self.ema = 0.9 * self.ema + 0.1 * ent_val

        return scores.detach()  # D-07: return scores from FIRST forward

    # ------------------------------------------------------------------
    # Inference-only
    # ------------------------------------------------------------------

    def score_only(
        self, skel: torch.Tensor, clip: torch.Tensor
    ) -> torch.Tensor:
        """Forward without adaptation (for source_only baseline)."""
        with torch.no_grad():
            return self.model(skel=skel, clip=clip).detach()
