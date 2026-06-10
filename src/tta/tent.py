"""TENT-style entropy-minimization TTA adapted for LayerNorm + binary entropy.

Ported from the official SAR repository (https://github.com/mr-eggplant/SAR,
ICLR 2023 Oral, MIT License).

Key adaptations from original TENT (Wang et al. 2021) / SAR repo:
  1. ``collect_params`` targets ``nn.LayerNorm`` (not ``nn.BatchNorm2d``)
  2. ``binary_entropy`` replaces softmax entropy (D-05)
  3. Per-video episodic reset via state_dict restore (D-07)
  4. ALL Dropout modules set to eval after model.train() (Pitfall 6)

The adaptation surface is the 1536 LN affine parameters (3 LN modules x
256-d weight + 256-d bias) in GatedFusion.
"""
from __future__ import annotations

import collections

import torch
import torch.nn as nn

EPS = 1e-7  # numerical stability for log


# -----------------------------------------------------------------------
# Module-level helpers
# -----------------------------------------------------------------------


def binary_entropy(scores: torch.Tensor) -> torch.Tensor:
    """Binary entropy for sigmoid scores in (0, 1).

    D-05: H = -(s*log(s) + (1-s)*log(1-s)), per-element.
    Minimised at s=0 and s=1 (confident predictions).
    """
    s = scores.clamp(EPS, 1 - EPS)
    return -(s * s.log() + (1 - s) * (1 - s).log())


def configure_model(model: nn.Module) -> nn.Module:
    """Prepare *model* for TTA: train mode, freeze all, unfreeze LN affine.

    Per Pitfall 6: explicitly ``model.dropout.eval()`` after ``model.train()``
    to disable random masking during TTA while keeping LN in train mode for
    gradient flow.  (LayerNorm computes the same statistics in both modes.)
    """
    model.train()
    model.requires_grad_(False)
    for m in model.modules():
        if isinstance(m, nn.LayerNorm):
            m.requires_grad_(True)
    # Pitfall 6: disable ALL dropout during TTA. model.train() (needed for LN
    # gradient flow) turns every dropout on; disabling only the top-level
    # GatedFusion.dropout left MILHead's two nn.Dropout layers (head.mlp.2,
    # head.mlp.5) in train mode, making every TTA score stochastic. Loop over
    # all modules so no dropout is missed.
    for m in model.modules():
        if isinstance(m, nn.Dropout):
            m.eval()
    return model


def collect_params(model: nn.Module) -> tuple[list[torch.nn.Parameter], list[str]]:
    """Collect LN affine parameters (weight, bias).

    Returns ``(params_list, names_list)``.
    Per D-08: exactly 6 tensors from 3 LN modules = 1536 params for
    GatedFusion.
    """
    params: list[torch.nn.Parameter] = []
    names: list[str] = []
    for nm, m in model.named_modules():
        if isinstance(m, nn.LayerNorm):
            for np_name, p in m.named_parameters():
                if np_name in ("weight", "bias"):
                    params.append(p)
                    names.append(f"{nm}.{np_name}")
    return params, names


# -----------------------------------------------------------------------
# Adaptor class
# -----------------------------------------------------------------------


class TentAdaptor:
    """Per-video TENT adaptation with episodic reset (D-06, D-07).

    Usage per video::

        adaptor.reset()  # restore to source state
        for skel_batch, clip_batch in video_batches:
            scores = adaptor.adapt_and_score(skel_batch, clip_batch)
            all_scores.append(scores)
    """

    def __init__(self, model: nn.Module, optimizer, source_state: dict):
        self.model = model
        self.optimizer = optimizer
        self.source_state = source_state  # deepcopy of initial model state_dict

    def reset(self):
        """Restore LN params to source-trained values (per-video reset per D-07)."""
        # strict=False because only the LN affine surface is adapted; the project
        # convention is strict=True, so assert the load was clean (source_state is
        # the full model state_dict -> no missing/unexpected keys) to catch a
        # silently-partial restore.
        result = self.model.load_state_dict(self.source_state, strict=False)
        assert not result.missing_keys and not result.unexpected_keys, (
            f"source_state restore mismatch: missing={result.missing_keys}, "
            f"unexpected={result.unexpected_keys}"
        )
        # Clear optimizer momentum / state buffers. Use a defaultdict(dict)
        # rather than a bare {} so per-parameter state stays writable for
        # stateful optimizers (e.g. SGD-with-momentum / Adam); behaviour is
        # unchanged for the momentum-free SGD used in production.
        self.optimizer.state = collections.defaultdict(dict)

    def adapt_and_score(
        self, skel: torch.Tensor, clip: torch.Tensor
    ) -> torch.Tensor:
        """Forward + adapt on one batch.  Returns detached scores.

        Per D-07: online scoring -- scores are collected during the adaptation
        forward pass, not from a separate clean forward pass.
        """
        scores = self.model(skel=skel, clip=clip)  # [B, T]
        loss = binary_entropy(scores).mean()
        loss.backward()
        self.optimizer.step()
        self.optimizer.zero_grad()
        return scores.detach()

    def score_only(
        self, skel: torch.Tensor, clip: torch.Tensor
    ) -> torch.Tensor:
        """Forward without adaptation (for source_only baseline).

        No gradient computation.
        """
        with torch.no_grad():
            return self.model(skel=skel, clip=clip).detach()
