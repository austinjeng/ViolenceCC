"""Unit tests for SAR-style TTA adaptation (TTA-05).

Tests cover SAM optimizer two-step update, SarAdaptor adapt+score, per-video
reset, entropy filtering threshold, rho grid acceptance (D-11), and
score_only inference.
"""
from __future__ import annotations

from copy import deepcopy

import pytest
import torch
import torch.nn as nn

from src.models.gated_fusion import GatedFusion
from src.tta.sam import SAM
from src.tta.sar import SarAdaptor
from src.tta.tent import collect_params, configure_model


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gated_model():
    """Fresh GatedFusion with default dims on CPU, seeded for reproducibility."""
    torch.manual_seed(42)
    return GatedFusion()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_sam_optimizer_first_second_step():
    """SAM optimizer two-step update modifies parameters correctly."""
    torch.manual_seed(42)

    # Simple linear model to test SAM mechanics
    model = nn.Linear(4, 1)
    initial_weight = model.weight.data.clone()

    sam = SAM(model.parameters(), torch.optim.SGD, rho=0.05, lr=0.01)

    # Forward + backward
    x = torch.randn(2, 4)
    loss = model(x).sum()
    loss.backward()

    # first_step: params should be perturbed (ascent)
    sam.first_step()
    assert not torch.allclose(
        model.weight.data, initial_weight
    ), "Params should change after first_step"

    perturbed_weight = model.weight.data.clone()
    sam.zero_grad()

    # Second forward at perturbed point
    loss2 = model(x).sum()
    loss2.backward()

    # second_step: params should be updated (different from both initial and perturbed)
    sam.second_step()
    assert not torch.allclose(
        model.weight.data, initial_weight
    ), "Params should differ from initial after second_step"
    assert not torch.allclose(
        model.weight.data, perturbed_weight
    ), "Params should differ from perturbed after second_step"


def test_sar_adapt_and_score_returns_scores(gated_model):
    """SarAdaptor.adapt_and_score returns correct shape and dtype."""
    torch.manual_seed(42)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    sam_opt = SAM(params, torch.optim.SGD, rho=0.01, lr=1e-3)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = SarAdaptor(gated_model, sam_opt, source_state)

    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    scores = adaptor.adapt_and_score(skel, clip)

    assert scores.shape == (1, 32), f"Expected (1, 32), got {scores.shape}"
    assert scores.dtype == torch.float32, f"Expected float32, got {scores.dtype}"
    assert scores.min() >= 0.0, "Scores should be >= 0 (sigmoid)"
    assert scores.max() <= 1.0, "Scores should be <= 1 (sigmoid)"


def test_sar_reset_restores_source_state(gated_model):
    """reset() restores model to source state and clears SAM optimizer state."""
    torch.manual_seed(42)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    # High LR + multiple steps to ensure visible param change
    sam_opt = SAM(params, torch.optim.SGD, rho=0.01, lr=0.1)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = SarAdaptor(gated_model, sam_opt, source_state)

    # Record source values
    ln_skel_source = source_state["ln_skel.weight"].clone()

    # Adapt to change params
    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    for _ in range(5):
        adaptor.adapt_and_score(skel, clip)

    # Verify params changed
    assert not torch.allclose(gated_model.ln_skel.weight.data, ln_skel_source)
    assert adaptor.ema is not None, "EMA should be set after adaptation"

    # Reset
    adaptor.reset()
    assert torch.allclose(
        gated_model.ln_skel.weight.data, ln_skel_source
    ), "LN weight not restored after reset"
    assert adaptor.ema is None, "EMA should be cleared after reset"
    # SAM base optimizer state should be cleared
    assert len(sam_opt.base_optimizer.state) == 0, (
        "SAM base optimizer state should be empty after reset"
    )


def test_sar_entropy_filtering_threshold(gated_model):
    """SarAdaptor stores margin_e0 and handles both high- and low-entropy inputs."""
    import math

    torch.manual_seed(42)
    custom_margin = 0.3 * math.log(2)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    sam_opt = SAM(params, torch.optim.SGD, rho=0.01, lr=1e-3)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = SarAdaptor(gated_model, sam_opt, source_state, margin_e0=custom_margin)

    assert adaptor.margin_e0 == custom_margin, (
        f"margin_e0 should be {custom_margin}, got {adaptor.margin_e0}"
    )

    # Should run without error on random inputs (mix of entropies)
    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    scores = adaptor.adapt_and_score(skel, clip)
    assert scores.shape == (1, 32)


def test_sar_rho_grid_values(gated_model):
    """D-11 rho grid {0.001, 0.005, 0.01, 0.05, 0.1} must all work with SAM."""
    rho_grid = [0.001, 0.005, 0.01, 0.05, 0.1]

    for rho in rho_grid:
        torch.manual_seed(42)
        model = GatedFusion()
        configure_model(model)
        params, _ = collect_params(model)

        sam_opt = SAM(params, torch.optim.SGD, rho=rho, lr=1e-3)
        source_state = deepcopy(model.state_dict())
        adaptor = SarAdaptor(model, sam_opt, source_state)

        skel = torch.randn(1, 32, 256)
        clip = torch.randn(1, 32, 1024)

        # Must not raise
        scores = adaptor.adapt_and_score(skel, clip)
        assert scores.shape == (1, 32), (
            f"rho={rho}: Expected (1, 32), got {scores.shape}"
        )

        # Reset must work cleanly
        adaptor.reset()


def test_sar_score_only_no_gradient(gated_model):
    """score_only must not compute or accumulate gradients."""
    torch.manual_seed(42)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    sam_opt = SAM(params, torch.optim.SGD, rho=0.01, lr=1e-3)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = SarAdaptor(gated_model, sam_opt, source_state)

    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    scores = adaptor.score_only(skel, clip)

    assert scores.shape == (1, 32)

    # No param should have gradient after score_only
    for p in params:
        assert p.grad is None or torch.all(
            p.grad == 0
        ), "No gradient should exist after score_only"
