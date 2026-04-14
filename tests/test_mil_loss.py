"""MOD-01: MIL Ranking Loss with RTFM-exact regularizers (D-01, D-02, D-03, D-10).

All tests here reference RESEARCH.md §1.1-1.5 for the exact RTFM formulas
verbatim. Do NOT relax a test; if one fails, the implementation is wrong,
not the test.
"""
import math
import pytest
import torch

# Will be created in Task 2 of this plan
from src.losses.mil_loss import mil_ranking_loss, _sparsity, _smoothness


def _rtfm_sparsity_ref(arr: torch.Tensor, lam: float) -> torch.Tensor:
    """RTFM's sparsity formula copied verbatim from upstream train.py."""
    return lam * torch.mean(torch.norm(arr, dim=0))


def _rtfm_smooth_ref(arr: torch.Tensor, lam: float) -> torch.Tensor:
    """RTFM's smoothness formula copied verbatim from upstream train.py."""
    arr2 = torch.zeros_like(arr)
    arr2[:-1] = arr[1:]
    arr2[-1] = arr[-1]
    return lam * torch.sum((arr2 - arr) ** 2)


# ---- MOD-01 VALIDATION.md-listed tests ----

def test_rank_loss_hinge():
    """Hinge margin=1.0 (D-02) on paired bags; top-k=3 (D-01).

    Abnormal bag (B=2): each row has top-3 scores that average to 0.9.
    Normal   bag (B=2): each row has top-3 scores that average to 0.1.
    Expected hinge per pair: max(0, 1.0 - 0.9 + 0.1) = 0.2.
    With regularizers disabled (lam=0), total loss == 0.2.
    """
    T, n_nor = 32, 2
    # Scores arranged so top-3 per row is {0.85, 0.90, 0.95} (mean 0.9) for abn
    # and {0.05, 0.10, 0.15} (mean 0.1) for nor; remaining padded with -10 so
    # they are never selected by top-k.
    sen = torch.full((n_nor, T), -10.0)
    sen[:, :3] = torch.tensor([0.05, 0.10, 0.15])
    sab = torch.full((n_nor, T), -10.0)
    sab[:, :3] = torch.tensor([0.85, 0.90, 0.95])
    scores = torch.cat([sen, sab], dim=0)
    mask = torch.ones_like(scores)
    loss = mil_ranking_loss(
        scores, mask, n_normal=n_nor,
        k=3, margin=1.0,
        lam_sparse=0.0, lam_smooth=0.0,
    )
    assert abs(loss.item() - 0.2) < 1e-5, f"expected 0.2, got {loss.item()}"


def test_sparsity_exact():
    """Sparsity output bit-matches the RTFM reference formula."""
    torch.manual_seed(0)
    arr = torch.rand(4, 32)
    lam = 8e-3
    got = _sparsity(arr, lam)
    want = _rtfm_sparsity_ref(arr, lam)
    assert torch.allclose(got, want, atol=1e-7), f"{got.item()} != {want.item()}"


def test_smoothness_exact():
    """Smoothness output bit-matches the RTFM arr2-shift reference formula."""
    torch.manual_seed(0)
    arr = torch.rand(4, 32)
    lam = 8e-4
    got = _smoothness(arr, lam)
    want = _rtfm_smooth_ref(arr, lam)
    assert torch.allclose(got, want, atol=1e-7), f"{got.item()} != {want.item()}"


def test_masked_topk():
    """D-10: zero-padded positions must be masked to -inf before top-k.

    Construct a bag where real snippets have low scores and padded zeros
    exist. Without masking, `topk` could pick padded zeros (0.0 > real
    score of -0.5). With masking, top-k must come from real positions only.
    """
    n_nor = 1
    T = 32
    # Normal row: all small positive (top-3 mean ~ 0.266 after masking)
    nor = torch.zeros(1, T)
    nor[0, :10] = torch.linspace(0.1, 0.3, 10)  # real positions 0-9
    # Abnormal row: first 10 real positions have small NEGATIVE scores;
    # remaining positions are zero-padded (mask=0).
    # Unmasked top-3 would pick the padded 0.0 positions -> wrong!
    # Masked top-3 MUST pick the 3 least-negative real values: -0.1, -0.188, -0.277 -> mean ~ -0.19
    abn = torch.zeros(1, T)
    abn[0, :10] = torch.linspace(-0.9, -0.1, 10)  # real = negative
    scores = torch.cat([nor, abn], dim=0)
    mask = torch.zeros_like(scores)
    mask[:, :10] = 1.0  # only first 10 positions are real

    loss = mil_ranking_loss(
        scores, mask, n_normal=n_nor,
        k=3, margin=1.0, lam_sparse=0.0, lam_smooth=0.0,
    )
    # If masking works: mean_topk_abn in [-0.3, -0.1] < 0; mean_topk_nor ~ 0.266
    # hinge = max(0, 1.0 - mean_topk_abn + mean_topk_nor) > 1.0
    # If masking fails: mean_topk_abn == 0.0 (padded zeros win) and hinge ~ 0.77
    assert loss.item() > 1.0, (
        f"masked top-k appears broken: loss={loss.item():.4f} "
        "(would be >1.0 if padded zeros are correctly masked)"
    )


# ---- Additional invariants beyond the VALIDATION.md minimum ----

def test_mil_ranking_loss_is_scalar_float():
    torch.manual_seed(0)
    scores = torch.rand(4, 32).requires_grad_(True)
    mask = torch.ones_like(scores)
    loss = mil_ranking_loss(scores, mask, n_normal=2)
    assert loss.dim() == 0
    assert loss.dtype == torch.float32
    assert torch.isfinite(loss).item()


def test_mil_ranking_loss_gradient_flows():
    torch.manual_seed(0)
    scores = torch.rand(4, 32).requires_grad_(True)
    mask = torch.ones_like(scores)
    loss = mil_ranking_loss(scores, mask, n_normal=2)
    loss.backward()
    assert scores.grad is not None
    assert torch.isfinite(scores.grad).all()


def test_regularizers_apply_to_abnormal_only():
    """Sparsity / smoothness evaluated on scores[n_normal:] only (RTFM convention).

    Case A: normal=0, abnormal=0.5 -> sparsity > 0
    Case B: normal=0.5, abnormal=0 -> sparsity == 0 (abnormal half is empty of mass)
    """
    T, n_nor = 32, 2
    mask = torch.ones(4, T)
    # Case A
    s_a = torch.zeros(4, T)
    s_a[n_nor:] = 0.5
    loss_a = mil_ranking_loss(s_a, mask, n_nor, margin=0.0,
                              lam_sparse=8e-3, lam_smooth=0.0)
    # Case B (flip normal/abnormal)
    s_b = torch.zeros(4, T)
    s_b[:n_nor] = 0.5
    loss_b = mil_ranking_loss(s_b, mask, n_nor, margin=0.0,
                              lam_sparse=8e-3, lam_smooth=0.0)
    assert loss_a.item() > loss_b.item(), (
        f"regularizer-on-abnormal contract violated: "
        f"loss_a (abn=0.5)={loss_a.item():.6f}, loss_b (nor=0.5)={loss_b.item():.6f}"
    )


def test_topk_k_value_default_is_3():
    """D-01: default k=3 - verify by constructing a bag where top-3 mean differs from top-1."""
    T, n_nor = 32, 1
    scores = torch.zeros(2, T)
    # Nor: all 0.0; Abn: one position 1.0, the rest 0.0
    scores[1, 0] = 1.0
    mask = torch.ones_like(scores)
    # top-1 mean for abn = 1.0; top-3 mean = (1.0 + 0 + 0)/3 ~ 0.333
    loss_k1 = mil_ranking_loss(scores, mask, n_nor, k=1, margin=1.0,
                               lam_sparse=0.0, lam_smooth=0.0)
    loss_k3 = mil_ranking_loss(scores, mask, n_nor, k=3, margin=1.0,
                               lam_sparse=0.0, lam_smooth=0.0)
    assert abs(loss_k1.item() - max(0, 1.0 - 1.0 + 0.0)) < 1e-5
    assert abs(loss_k3.item() - max(0, 1.0 - (1.0/3.0) + 0.0)) < 1e-5
    assert loss_k3.item() > loss_k1.item()


def test_margin_default_is_1_0():
    """D-02: default margin=1.0 (NOT RTFM's feature-magnitude margin of 100)."""
    T, n_nor = 32, 1
    scores = torch.full((2, T), 0.5)  # top-k for both = 0.5 -> hinge = margin - 0.5 + 0.5 = margin
    mask = torch.ones_like(scores)
    loss = mil_ranking_loss(scores, mask, n_nor, lam_sparse=0.0, lam_smooth=0.0)
    assert abs(loss.item() - 1.0) < 1e-5, (
        f"default margin appears wrong: loss={loss.item():.4f} (expected ~1.0 if margin=1.0)"
    )


def test_lam_sparse_default_is_8e_minus_3():
    """D-03: default lam_sparse=8e-3."""
    torch.manual_seed(0)
    scores = torch.rand(4, 32)
    mask = torch.ones_like(scores)
    # Compare call with default vs explicit 8e-3 - must be identical
    a = mil_ranking_loss(scores, mask, 2, margin=0.0, lam_smooth=0.0)
    b = mil_ranking_loss(scores, mask, 2, margin=0.0, lam_sparse=8e-3, lam_smooth=0.0)
    assert torch.allclose(a, b, atol=1e-8)


def test_lam_smooth_default_is_8e_minus_4():
    """D-03: default lam_smooth=8e-4."""
    torch.manual_seed(0)
    scores = torch.rand(4, 32)
    mask = torch.ones_like(scores)
    a = mil_ranking_loss(scores, mask, 2, margin=0.0, lam_sparse=0.0)
    b = mil_ranking_loss(scores, mask, 2, margin=0.0, lam_sparse=0.0, lam_smooth=8e-4)
    assert torch.allclose(a, b, atol=1e-8)
