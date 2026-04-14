"""Deterministic training reproducibility (TRN-03).

Four knobs are required for bit-identical runs (RESEARCH.md section 2):
  KNOB 1: seed torch + numpy + random + cuda RNGs
  KNOB 2: cudnn.deterministic=True, cudnn.benchmark=False
  KNOB 3: torch.use_deterministic_algorithms(True, warn_only=True)
  KNOB 4: CUBLAS_WORKSPACE_CONFIG=:4096:8 — MUST be set BEFORE `import torch`
          in the entry point (src/train.py); this module cannot set it (already too late).
"""
from __future__ import annotations
import os
import random
import numpy as np
import torch


def set_deterministic(seed: int = 42) -> None:
    """Seed all RNGs and enable deterministic kernels.

    Call this ONCE at the top of training, after imports but before
    dataloader / model construction.

    WARNING: CUBLAS_WORKSPACE_CONFIG must be set before `import torch`.
    If you see a RuntimeError from torch.mm/bmm after calling this, check that
    the entry point sets os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8' as its
    first line (before any torch import).
    """
    # KNOB 1: RNGs
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # KNOB 2: cuDNN
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    # KNOB 3: global deterministic algorithms
    # warn_only=True is the CONTEXT.md Claude's Discretion default — accept
    # ~10-20% throughput cost, fall back to nondeterministic kernel with
    # warning if no deterministic implementation exists.
    torch.use_deterministic_algorithms(True, warn_only=True)


def seed_worker(worker_id: int) -> None:
    """DataLoader worker init_fn per RESEARCH.md section 2.5.

    MUST be module-level (not a lambda) so Windows spawn can pickle it.
    """
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)


def make_generator(seed: int) -> torch.Generator:
    """Seeded torch.Generator for DataLoader shuffling reproducibility."""
    g = torch.Generator()
    g.manual_seed(seed)
    return g
