"""Atomic checkpoint save/load (TRN-02, D-15)."""
import os
import pathlib
from unittest.mock import patch

import pytest
import torch

from src.utils.checkpoint import save_checkpoint_atomic, load_checkpoint


def test_save_load_round_trip(tmp_path):
    m = torch.nn.Linear(4, 2)
    state = m.state_dict()
    path = tmp_path / "best_model.pth"
    save_checkpoint_atomic(state, path)

    # Fresh model; load; verify weights match
    m2 = torch.nn.Linear(4, 2)
    m2.load_state_dict(load_checkpoint(path))
    for k, v in m.state_dict().items():
        assert torch.equal(v, m2.state_dict()[k])


def test_save_is_weights_only_safe(tmp_path):
    """Verify the saved file loads under torch.load(weights_only=True)."""
    m = torch.nn.Linear(4, 2)
    path = tmp_path / "best.pth"
    save_checkpoint_atomic(m.state_dict(), path)
    # No add_safe_globals call needed because state_dict contains only tensors
    reloaded = torch.load(str(path), map_location="cpu", weights_only=True)
    assert "weight" in reloaded and "bias" in reloaded


def test_save_atomic_tempfile_cleaned(tmp_path):
    m = torch.nn.Linear(4, 2)
    path = tmp_path / "x.pth"
    save_checkpoint_atomic(m.state_dict(), path)
    # No leftover .tmp or hidden tempfiles next to x.pth
    leftovers = [p for p in tmp_path.iterdir()
                 if p.name != path.name and ".tmp" in p.name]
    assert leftovers == [], f"leftover tempfiles: {leftovers}"


def test_save_failure_preserves_original(tmp_path):
    """If torch.save raises mid-write, previous file survives (atomic semantics)."""
    m1 = torch.nn.Linear(4, 2)
    m2 = torch.nn.Linear(4, 2)  # different weights
    path = tmp_path / "c.pth"

    # First save succeeds
    save_checkpoint_atomic(m1.state_dict(), path)
    original_sd = load_checkpoint(path)

    # Second save: torch.save raises -> tempfile cleaned -> target unchanged
    with patch("torch.save", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            save_checkpoint_atomic(m2.state_dict(), path)

    # Original file still readable and identical to m1's state
    reloaded = load_checkpoint(path)
    for k in original_sd:
        assert torch.equal(original_sd[k], reloaded[k])
    # No leftover tempfile
    leftovers = [p for p in tmp_path.iterdir()
                 if p.name != path.name and ".tmp" in p.name]
    assert leftovers == []
