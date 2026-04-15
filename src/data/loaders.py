"""Paired normal + abnormal DataLoaders (D-04) + val loader.

This module implements the Plan 03-03 DataLoader contract that Phase 3
training consumes. The training step is::

    nor_batch = next(iter(nor_loader))   # 16 videos, label == 0
    abn_batch = next(iter(abn_loader))   # 16 videos, label == 1
    batch = concat(nor_batch, abn_batch)  # 32 videos = 16 ranking pairs

The two loaders use **independent** generators so the normal and abnormal
queues shuffle independently — a prerequisite for the RTFM/MGFN pair-wise
hinge loss (D-04).

The worker-seeding utilities (``seed_worker``, ``make_generator``) are the
canonical versions implemented in Plan 03-01 at ``src/utils/seed.py``.
When that module is not yet merged into the local working tree (as happens
during parallel wave-1 execution), we fall back to inline definitions that
match RESEARCH.md §2.5 verbatim.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, Subset

from src.data.dataset import MILFeatureDataset

try:  # pragma: no cover - import shim for parallel-worktree ergonomics
    from src.utils.seed import seed_worker, make_generator  # type: ignore
except ImportError:  # fallback mirrors RESEARCH.md §2.5
    import random as _random

    def seed_worker(worker_id: int) -> None:  # type: ignore[no-redef]
        """Seed numpy + stdlib random per DataLoader worker.

        Windows spawn start method requires ``worker_init_fn`` to be a
        module-level function (no lambdas), per RESEARCH.md §2.5.
        """
        worker_seed = torch.initial_seed() % 2**32
        np.random.seed(worker_seed)
        _random.seed(worker_seed)

    def make_generator(seed: int) -> torch.Generator:  # type: ignore[no-redef]
        """Build a seeded ``torch.Generator`` for DataLoader shuffling."""
        g = torch.Generator()
        g.manual_seed(int(seed))
        return g


def build_dataloaders(cfg: dict) -> Tuple[Tuple[DataLoader, DataLoader], DataLoader]:
    """Build paired (nor, abn) train loaders + val loader per D-04.

    Parameters
    ----------
    cfg : dict
        Minimum required keys::

            cfg["dataset"]                      # "ucf" or "xd"
            cfg["seed"]                         # int
            cfg["paths"]["splits_dir"]          # directory containing
                                                # {dataset}_train.txt and
                                                # {dataset}_val.txt
            cfg["paths"]["skeleton_features"]   # directory of skel .npy
            cfg["paths"]["clip_features"]       # directory of clip .npy
            cfg["data"]["T"]                    # target snippet count (32)
            cfg["data"]["batch_size"]           # 16 (per D-04)
            cfg["data"]["num_workers"]          # typically 0 on Windows CI
            cfg["data"]["pin_memory"]           # bool, optional

    Returns
    -------
    ((nor_loader, abn_loader), val_loader)
        ``nor_loader`` yields batches of ``batch_size`` normal videos;
        ``abn_loader`` yields batches of ``batch_size`` abnormal videos;
        ``val_loader`` is a single DataLoader over the full val split at
        ``batch_size * 2`` (the Plan 06 training loop splits each val batch
        into normal/abnormal halves internally).

    Notes
    -----
    * ``drop_last=True`` on both train loaders — required so every training
      step gets exactly ``batch_size`` normal + ``batch_size`` abnormal
      videos for the paired MIL hinge (D-04).
    * ``worker_init_fn=seed_worker`` plus per-loader ``torch.Generator``
      seeded with ``cfg["seed"]`` / ``cfg["seed"] + 1`` gives independent,
      reproducible shuffling of the two queues (TRN-03).
    * ``persistent_workers=True`` when ``num_workers > 0`` — first-epoch
      determinism is reliable on Windows; subsequent epochs are fine for
      our single-training-run workflow.
    """
    dataset = cfg["dataset"]                       # 'ucf' or 'xd'
    paths = cfg["paths"]
    data_cfg = cfg["data"]
    T = data_cfg.get("T", 32)
    bs = data_cfg["batch_size"]                    # 16 per D-04
    num_workers = data_cfg.get("num_workers", 0)
    pin_memory = data_cfg.get("pin_memory", False)
    seed = cfg.get("seed", 42)
    # Phase 4 D-21 / Plan 04-06 Rule 1 fix: forward cfg.data.skel_agg to the
    # training and val datasets so the 2-person cache shape [N, 2, 256] is
    # collapsed via concat/max/mean at load time. Default 'none' preserves
    # the Phase 3 contract where the M-pool cache is already 2D.
    skel_agg = data_cfg.get("skel_agg", "none")

    train_full = MILFeatureDataset(
        split_file=f"{paths['splits_dir']}/{dataset}_train.txt",
        skel_dir=paths["skeleton_features"],
        clip_dir=paths["clip_features"],
        T=T, mode="train", seed=seed, dataset=dataset,
        skel_agg=skel_agg,
    )
    val_full = MILFeatureDataset(
        split_file=f"{paths['splits_dir']}/{dataset}_val.txt",
        skel_dir=paths["skeleton_features"],
        clip_dir=paths["clip_features"],
        T=T, mode="val", seed=seed, dataset=dataset,
        skel_agg=skel_agg,
    )

    # Split the training set into normal (label=0) and abnormal (label=1) subsets.
    nor_idx = [i for i, v in enumerate(train_full.video_ids)
               if train_full.labels[v] == 0.0]
    abn_idx = [i for i, v in enumerate(train_full.video_ids)
               if train_full.labels[v] == 1.0]

    g_nor = make_generator(seed)
    g_abn = make_generator(seed + 1)
    g_val = make_generator(seed + 2)

    persistent = num_workers > 0
    common = dict(
        batch_size=bs,
        num_workers=num_workers,
        worker_init_fn=seed_worker,
        pin_memory=pin_memory,
        persistent_workers=persistent,
        drop_last=True,
    )

    nor_loader = DataLoader(Subset(train_full, nor_idx), shuffle=True,
                            generator=g_nor, **common)
    abn_loader = DataLoader(Subset(train_full, abn_idx), shuffle=True,
                            generator=g_abn, **common)

    # Val loader: full split (both labels), not split by label — val MIL loss
    # needs paired bags too, so we re-use the paired pattern at val time inside
    # the training loop. For simplicity here, return a single val DataLoader;
    # the training loop (Plan 06) will split val batches into normal/abnormal
    # halves inside validate().
    val_loader = DataLoader(val_full, batch_size=bs * 2,
                            num_workers=num_workers,
                            worker_init_fn=seed_worker,
                            generator=g_val, pin_memory=pin_memory,
                            persistent_workers=persistent,
                            drop_last=False, shuffle=False)

    return (nor_loader, abn_loader), val_loader
