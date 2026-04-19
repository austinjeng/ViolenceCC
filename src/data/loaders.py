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
from src.data.i3d_dataset import I3DFeatureDataset

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


def collate_i3d_train(batch_list: list) -> dict:
    """D-05 5-crop-as-sample flatten for I3DFeatureDataset (module-scope for Windows spawn).

    Input: list of B dicts from ``I3DFeatureDataset`` mode='train' or mode='val'::

        {"i3d": Tensor[5, T, 1024], "label": float, "video_id": str}

    Output: dict suitable for ``RTFMI3D.forward`` + ``mil_ranking_loss``::

        {
            "i3d":     Tensor[B*5, T, 1024],
            "label":   Tensor[B*5] float32  (each video's label repeated 5x via repeat_interleave),
            "mask":    Tensor[B*5, T] float32 (all ones; I3D has no padding -- Pitfall 1 guard),
            "video_id": list[str] of length B*5 (each vid repeated 5x consecutively),
        }

    Shape contract: first dim of ``i3d`` after collate = ``batch_size * n_crops``.
    With ``rtfm_i3d.yaml`` ``batch_size=3``, this yields an effective MIL bag size
    of 15 matching ``k_topk=3`` (Pitfall 3).

    Notes
    -----
    * Module-scope definition is REQUIRED for Windows spawn semantics + DataLoader
      ``persistent_workers`` (Pitfall 7): a nested closure would not pickle across
      worker processes.
    * Uses ``repeat_interleave(5)`` (not ``repeat(5)``) so labels are replicated
      CONSECUTIVELY -- ``[0, 0, 1]`` -> ``[0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1]``.
      This ordering matches ``torch.stack`` flattening, which produces
      ``sample_0_crop_0..4, sample_1_crop_0..4, sample_2_crop_0..4`` (Pitfall 4 guard).
    """
    # Stack the [5, T, 1024] i3d tensors into [B, 5, T, 1024].
    i3d = torch.stack([s["i3d"] for s in batch_list], dim=0)
    B, n_crops, T, D = i3d.shape
    # Shape assertion (Pitfall 4 -- crop-padding inside _load_crops should ensure 5).
    assert n_crops == 5 and D == 1024, (
        f"collate_i3d_train expected [B, 5, T, 1024], got {tuple(i3d.shape)}"
    )
    i3d_flat = i3d.reshape(B * n_crops, T, D)

    # Labels: each per-video label repeated CONSECUTIVELY 5 times (Pitfall 4 guard).
    # repeat_interleave(5) on [0, 0, 1] -> [0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1]
    labels = torch.tensor(
        [s["label"] for s in batch_list], dtype=torch.float32
    ).repeat_interleave(n_crops)

    # Mask: all ones (I3DFeatureDataset uses sample-with-replacement, no padding).
    mask = torch.ones(B * n_crops, T, dtype=torch.float32)

    # Video IDs: each id repeated consecutively 5 times to match label/i3d ordering.
    video_ids = [s["video_id"] for s in batch_list for _ in range(n_crops)]

    return {"i3d": i3d_flat, "label": labels, "mask": mask, "video_id": video_ids}


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
                            drop_last=False, shuffle=True)

    return (nor_loader, abn_loader), val_loader


def build_dataloaders_i3d(cfg: dict) -> Tuple[Tuple[DataLoader, DataLoader], DataLoader]:
    """Build paired (nor, abn) train loaders + val loader for xd_i3d dispatch (D-04).

    Parallel to ``build_dataloaders()`` but consumes :class:`I3DFeatureDataset`
    (single feature tensor per video at train/val, 5-crop flattened to ``B*5``
    via :func:`collate_i3d_train`). Per D-04 parallel-functions decision, the
    existing UCF/XD fusion path is UNTOUCHED; this function lives alongside it.

    Parameters
    ----------
    cfg : dict
        Required keys::

            cfg["seed"]                   # int, e.g. 42
            cfg["dataset"]                # "xd_i3d"
            cfg["paths"]["splits_dir"]    # directory containing xd_train.txt / xd_val.txt
            cfg["paths"]["i3d_features"]  # parent dir containing RGB/ subdirectory
            cfg["data"]["batch_size"]     # int, e.g. 3 per rtfm_i3d.yaml + Pitfall 3
            cfg["data"]["T"]              # int, e.g. 32
            cfg["data"]["num_workers"]    # int, default 0
            cfg["data"]["pin_memory"]     # bool, default False

    Returns
    -------
    ((nor_loader, abn_loader), val_loader)
        * ``nor_loader`` yields dict with ``i3d.shape[0] == batch_size * 5`` (all label=0).
        * ``abn_loader`` yields dict with ``i3d.shape[0] == batch_size * 5`` (all label=1).
        * ``val_loader`` yields dict with ``i3d.shape[0] == batch_size * 2 * 5`` (mixed labels).

    Raises
    ------
    AssertionError
        If the train normal partition, train abnormal partition, or the val
        abnormal partition is empty (Open Question #1 guard -- ``validate_i3d``
        requires at least one abnormal val video to produce finite val loss,
        otherwise early stopping breaks silently).

    Notes
    -----
    * D-05 crop-as-sample: each video in the bag contributes 5 independent
      samples via ``collate_i3d_train``; effective MIL bag size with
      ``batch_size=3`` is ``3 * 5 = 15`` matching ``k_topk=3`` (Pitfall 3).
    * D-06 suffix partition: ``I3DFeatureDataset`` does NOT expose a ``.labels``
      dict (unlike ``MILFeatureDataset``), so partitioning uses the canonical
      ``.endswith("_label_A")`` suffix check directly on ``video_ids``.
    * Open Question #2 hardcodes ``xd_train.txt`` / ``xd_val.txt`` -- the
      pattern ``f"{cfg['dataset']}_val.txt"`` would resolve to non-existent
      ``xd_i3d_val.txt`` because ``cfg['dataset']=='xd_i3d'`` is the MODEL-path
      selector, not the SPLIT-file selector.
    """
    paths = cfg["paths"]
    data_cfg = cfg["data"]
    T = data_cfg.get("T", 32)
    bs = data_cfg["batch_size"]                    # 3 per rtfm_i3d.yaml (Pitfall 3)
    num_workers = data_cfg.get("num_workers", 0)
    pin_memory = data_cfg.get("pin_memory", False)
    seed = int(cfg.get("seed", 42))

    # D-06 / Open Question #2: hardcode xd_{train,val}.txt. The pattern
    # f"{cfg['dataset']}_val.txt" would resolve to non-existent xd_i3d_val.txt
    # because cfg['dataset']='xd_i3d' is the model-path selector, not the
    # split-file selector. The XD val split file is canonically named xd_val.txt.
    i3d_dir = str(paths["i3d_features"])
    train_ds = I3DFeatureDataset(
        split_file=f"{paths['splits_dir']}/xd_train.txt",
        feature_dir=f"{i3d_dir}/RGB",
        mode="train",
        T=T,
    )
    val_ds = I3DFeatureDataset(
        split_file=f"{paths['splits_dir']}/xd_val.txt",
        feature_dir=f"{i3d_dir}/RGB",
        mode="val",
        T=T,
    )

    # D-06 partition by _label_A suffix. I3DFeatureDataset has NO .labels dict
    # (verified: src/data/i3d_dataset.py:57-71 exposes only self.video_ids);
    # labels are computed per-item at __getitem__ from the suffix.
    nor_idx = [i for i, v in enumerate(train_ds.video_ids) if v.endswith("_label_A")]
    abn_idx = [i for i, v in enumerate(train_ds.video_ids) if not v.endswith("_label_A")]
    assert len(nor_idx) > 0, (
        "build_dataloaders_i3d: no normal train videos after Pitfall 4 filter; "
        "cannot form MIL bags"
    )
    assert len(abn_idx) > 0, (
        "build_dataloaders_i3d: no abnormal train videos after Pitfall 4 filter; "
        "cannot form MIL bags"
    )

    # Open Question #1: val set must have at least one abnormal video for
    # validate_i3d to produce finite val loss (otherwise early stopping breaks
    # silently every epoch).
    val_abn = [v for v in val_ds.video_ids if not v.endswith("_label_A")]
    assert len(val_abn) > 0, (
        "build_dataloaders_i3d: val set has no abnormal videos after Pitfall 4 filter; "
        "validate_i3d would return float('inf') every epoch -- check xd_val.txt coverage"
    )

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
        collate_fn=collate_i3d_train,
    )

    nor_loader = DataLoader(
        Subset(train_ds, nor_idx), shuffle=True, generator=g_nor, **common
    )
    abn_loader = DataLoader(
        Subset(train_ds, abn_idx), shuffle=True, generator=g_abn, **common
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=bs * 2,
        num_workers=num_workers,
        worker_init_fn=seed_worker,
        pin_memory=pin_memory,
        persistent_workers=persistent,
        drop_last=False,
        shuffle=False,
        generator=g_val,
        collate_fn=collate_i3d_train,
    )
    return (nor_loader, abn_loader), val_loader
