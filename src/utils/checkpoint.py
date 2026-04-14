"""Windows-safe atomic checkpoint writes (RESEARCH.md 5.1).

save_checkpoint_atomic writes the state_dict ONLY - no nested config dict -
so torch.load(weights_only=True) always works cleanly per RESEARCH.md 5.2.
Config snapshotting happens in Plan 07's config_snapshot.json (separate file).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Union

import torch


def save_checkpoint_atomic(state_dict: dict, path: Union[str, Path]) -> None:
    """Atomically save a torch state_dict using tempfile + os.replace.

    state_dict must contain only torch tensors (or nested dicts of tensors).
    Do NOT pass Python dicts with config objects - that breaks weights_only=True.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Same-directory tempfile (cross-device rename is NOT atomic on Windows)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "wb") as f:
            torch.save(state_dict, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, str(path))
    except Exception:
        # Best-effort cleanup; re-raise original exception
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise


def load_checkpoint(path: Union[str, Path], device: str = "cpu") -> dict:
    """Load a state_dict saved by save_checkpoint_atomic.

    Uses weights_only=True (safe; requires state_dict-only files - our contract).
    """
    return torch.load(str(path), map_location=device, weights_only=True)
