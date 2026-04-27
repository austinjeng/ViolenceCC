"""Unit tests for TENT-style TTA adaptation (TTA-04, TTA-07).

Tests cover LN param collection, model configuration (freeze/unfreeze),
dropout eval mode, binary entropy values, adapt+reset lifecycle, 32-snippet
protocol enforcement, and score_only inference.
"""
from __future__ import annotations

from copy import deepcopy

import pytest
import torch

from src.models.gated_fusion import GatedFusion
from src.tta.tent import (
    EPS,
    TentAdaptor,
    binary_entropy,
    collect_params,
    configure_model,
)


# ---------------------------------------------------------------------------
# Fixture: deterministic GatedFusion on CPU
# ---------------------------------------------------------------------------


@pytest.fixture
def gated_model():
    """Fresh GatedFusion with default dims on CPU, seeded for reproducibility."""
    torch.manual_seed(42)
    return GatedFusion()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_collect_params_returns_6_tensors(gated_model):
    """collect_params must return exactly 6 LN affine tensors = 1536 params."""
    params, names = collect_params(gated_model)

    assert len(params) == 6, f"Expected 6 params, got {len(params)}"
    assert len(names) == 6, f"Expected 6 names, got {len(names)}"

    # All names must reference an LN module and end with weight or bias
    for name in names:
        assert "ln_" in name, f"Expected 'ln_' in name: {name}"
        assert name.endswith(".weight") or name.endswith(
            ".bias"
        ), f"Name must end with .weight or .bias: {name}"

    total_numel = sum(p.numel() for p in params)
    assert total_numel == 1536, f"Expected 1536 elements, got {total_numel}"


def test_configure_model_freezes_non_ln(gated_model):
    """configure_model freezes everything except LN affine parameters."""
    configure_model(gated_model)

    # Frozen: skel_proj, clip_proj, gate, head
    assert gated_model.skel_proj.weight.requires_grad is False
    assert gated_model.clip_proj.weight.requires_grad is False
    assert gated_model.gate.weight.requires_grad is False
    assert gated_model.head.mlp[0].weight.requires_grad is False

    # Unfrozen: LN affine
    assert gated_model.ln_skel.weight.requires_grad is True
    assert gated_model.ln_skel.bias.requires_grad is True
    assert gated_model.ln_clip.weight.requires_grad is True
    assert gated_model.ln_clip.bias.requires_grad is True
    assert gated_model.ln_fused.weight.requires_grad is True
    assert gated_model.ln_fused.bias.requires_grad is True


def test_configure_model_sets_dropout_eval(gated_model):
    """Pitfall 6: dropout must be in eval mode while model is in train mode."""
    configure_model(gated_model)

    assert gated_model.training is True, "Model must be in train mode for LN gradients"
    assert (
        gated_model.dropout.training is False
    ), "Dropout must be in eval mode (Pitfall 6)"


def test_binary_entropy_values():
    """binary_entropy matches D-05 formula at known points."""
    import math

    # H(0.5) = ln(2) ~= 0.6931
    h_half = binary_entropy(torch.tensor([0.5]))
    assert abs(h_half.item() - math.log(2)) < 1e-4, (
        f"binary_entropy(0.5) should be ln(2), got {h_half.item()}"
    )

    # H(0.01) should be close to 0 (confident prediction)
    h_low = binary_entropy(torch.tensor([0.01]))
    assert h_low.item() < 0.10, (
        f"binary_entropy(0.01) should be near 0, got {h_low.item()}"
    )

    # H(0.99) should be close to 0 (confident prediction)
    h_high = binary_entropy(torch.tensor([0.99]))
    assert h_high.item() < 0.10, (
        f"binary_entropy(0.99) should be near 0, got {h_high.item()}"
    )

    # Symmetry: H(p) == H(1-p)
    h_02 = binary_entropy(torch.tensor([0.2]))
    h_08 = binary_entropy(torch.tensor([0.8]))
    assert abs(h_02.item() - h_08.item()) < 1e-5, (
        f"binary_entropy should be symmetric: H(0.2)={h_02.item()}, H(0.8)={h_08.item()}"
    )

    # EPS constant
    assert EPS == 1e-7


def test_tent_adapt_and_score_updates_ln_params(gated_model):
    """adapt_and_score must update LN params and leave others frozen."""
    torch.manual_seed(42)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    # Use a high LR so gradient updates are visible in a single step
    optimizer = torch.optim.SGD(params, lr=0.1)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = TentAdaptor(gated_model, optimizer, source_state)

    # Record initial LN weight
    ln_skel_init = gated_model.ln_skel.weight.clone()
    skel_proj_init = gated_model.skel_proj.weight.clone()

    # Adapt on random input (multiple steps to accumulate visible change)
    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    for _ in range(5):
        scores = adaptor.adapt_and_score(skel, clip)

    assert scores.shape == (1, 32), f"Expected shape (1, 32), got {scores.shape}"

    # LN weight must have changed
    assert not torch.allclose(
        gated_model.ln_skel.weight, ln_skel_init
    ), "LN weight should change after adaptation"

    # Frozen params must NOT change
    assert torch.allclose(
        gated_model.skel_proj.weight, skel_proj_init
    ), "skel_proj weight should not change"


def test_tent_reset_restores_source_state(gated_model):
    """reset() must restore LN params to exact source-trained values."""
    torch.manual_seed(42)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    # High LR + multiple steps to ensure visible param change
    optimizer = torch.optim.SGD(params, lr=0.1)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = TentAdaptor(gated_model, optimizer, source_state)

    # Record source LN weights
    ln_skel_source = source_state["ln_skel.weight"].clone()

    # Adapt to change params
    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    for _ in range(5):
        adaptor.adapt_and_score(skel, clip)

    # Verify params changed
    assert not torch.allclose(gated_model.ln_skel.weight.data, ln_skel_source)

    # Reset and verify restoration
    adaptor.reset()
    assert torch.allclose(
        gated_model.ln_skel.weight.data, ln_skel_source
    ), "LN weight not restored to source state after reset()"
    assert torch.allclose(
        gated_model.ln_clip.weight.data, source_state["ln_clip.weight"]
    ), "ln_clip weight not restored"
    assert torch.allclose(
        gated_model.ln_fused.weight.data, source_state["ln_fused.weight"]
    ), "ln_fused weight not restored"


def test_protocol_enforcement_32_snippet_batch(gated_model):
    """TTA-07: adapt_and_score handles 32-snippet batches correctly."""
    torch.manual_seed(42)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    optimizer = torch.optim.SGD(params, lr=1e-3)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = TentAdaptor(gated_model, optimizer, source_state)

    # T=32 snippets per D-07 protocol
    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    scores = adaptor.adapt_and_score(skel, clip)

    assert scores.shape == (1, 32), f"Expected (1, 32) for 32-snippet batch, got {scores.shape}"
    assert scores.dtype == torch.float32, f"Expected float32, got {scores.dtype}"

    # Scores should be in (0, 1) range (sigmoid output)
    assert scores.min() >= 0.0, "Scores should be >= 0 (sigmoid)"
    assert scores.max() <= 1.0, "Scores should be <= 1 (sigmoid)"


def test_score_only_no_gradient(gated_model):
    """score_only must not compute or accumulate gradients."""
    torch.manual_seed(42)
    configure_model(gated_model)
    params, _ = collect_params(gated_model)

    optimizer = torch.optim.SGD(params, lr=1e-3)
    source_state = deepcopy(gated_model.state_dict())
    adaptor = TentAdaptor(gated_model, optimizer, source_state)

    skel = torch.randn(1, 32, 256)
    clip = torch.randn(1, 32, 1024)
    scores = adaptor.score_only(skel, clip)

    assert scores.shape == (1, 32)

    # No param should have gradient after score_only
    for p in params:
        assert p.grad is None or torch.all(
            p.grad == 0
        ), "No gradient should exist after score_only"
