"""Deterministic synthetic feature tensors for unit + integration tests.
Shapes match Phase 2 cache contracts (float32 .npy per video):
  - skeleton: [N, 256] — Phase 2 D-05, 4-stream weighted concat output
  - CLIP:     [N, 1024] — Phase 2 D-06, mean+max pooling pre-projection
"""
from __future__ import annotations
import numpy as np
import torch


def make_skel(N: int = 40, seed: int = 0) -> np.ndarray:
    """[N, 256] float32 synthetic skeleton features (deterministic per seed)."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((N, 256), dtype=np.float32)


def make_clip(N: int = 40, seed: int = 0) -> np.ndarray:
    """[N, 1024] float32 synthetic CLIP features (deterministic per seed)."""
    rng = np.random.default_rng(seed + 1)
    return rng.standard_normal((N, 1024), dtype=np.float32)


def make_batch(B_nor: int = 16, B_abn: int = 16, T: int = 32, seed: int = 0):
    """Paired normal+abnormal bag batch (D-04 contract).

    Returns dict of torch tensors:
      skel:  [B_nor+B_abn, T, 256]  (normal first, then abnormal)
      clip:  [B_nor+B_abn, T, 1024]
      mask:  [B_nor+B_abn, T]       (all ones — no padding in synthetic fixture)
      label: [B_nor+B_abn]          (B_nor zeros, B_abn ones)
    """
    g = torch.Generator().manual_seed(seed)
    skel = torch.randn((B_nor + B_abn, T, 256), generator=g, dtype=torch.float32)
    clip = torch.randn((B_nor + B_abn, T, 1024), generator=g, dtype=torch.float32)
    mask = torch.ones((B_nor + B_abn, T), dtype=torch.float32)
    label = torch.cat([torch.zeros(B_nor), torch.ones(B_abn)], dim=0).float()
    return {"skel": skel, "clip": clip, "mask": mask, "label": label}
