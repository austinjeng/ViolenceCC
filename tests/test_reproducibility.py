"""TRN-03: bit-identical train_log.csv across two independent runs with same seed."""
from __future__ import annotations

import csv
import pathlib

import pytest
import yaml

from src.train import main


def _make_cfg(root, seed=42, epochs=2):
    # Reuse the smoke fixture construction from test_train_integration to keep
    # the two test files independent.
    import numpy as np
    splits = root / "splits"
    splits.mkdir(parents=True, exist_ok=True)
    skel = root / "features" / "skeleton"
    skel.mkdir(parents=True, exist_ok=True)
    clip = root / "features" / "clip"
    clip.mkdir(parents=True, exist_ok=True)
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
    train_nor = [f"Normal_Videos_event_{i}_x264" for i in range(10)]
    train_abn = [f"Abuse{i:03d}_x264" for i in range(10)]
    val_nor = [f"Normal_Videos_event_v{i}_x264" for i in range(4)]
    val_abn = [f"Assault{i:03d}_x264" for i in range(4)]
    for v in train_nor + train_abn + val_nor + val_abn:
        rng = np.random.default_rng(hash(v) & 0xFFFF)
        np.save(skel / f"{v}.npy", rng.standard_normal((40, 256), dtype=np.float32))
        rng2 = np.random.default_rng((hash(v) + 1) & 0xFFFF)
        np.save(clip / f"{v}.npy", rng2.standard_normal((40, 1024), dtype=np.float32))
    (splits / "ucf_train.txt").write_text("\n".join(train_nor + train_abn) + "\n")
    (splits / "ucf_val.txt").write_text("\n".join(val_nor + val_abn) + "\n")

    cfg = {
        "seed": seed, "dataset": "ucf",
        "paths": {
            "skeleton_features": str(skel),
            "clip_features": str(clip),
            "splits_dir": str(splits),
            "results_dir": str(results),
        },
        "model": {"variant": "skeleton_only", "skel_dim": 256,
                  "head_hidden": [128, 32], "dropout": 0.3},
        "data": {"T": 32, "batch_size": 5, "num_workers": 0, "pin_memory": False},
        "train": {
            "lr": 1.0e-4, "weight_decay": 1.0e-2,
            "epochs": epochs, "warmup_epochs": 1, "patience": 10,
            "k_topk": 3, "margin": 1.0,
            "lam_sparse": 8.0e-3, "lam_smooth": 8.0e-4,
        },
    }
    cfg_path = root / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    return cfg_path, results


def _read_losses(run_dir):
    rows = list(csv.DictReader(open(run_dir / "train_log.csv")))
    return [(r["train_loss"], r["val_loss"]) for r in rows]


def _latest(results):
    return sorted([p for p in results.iterdir() if p.is_dir()])[-1]


def test_bit_identical(tmp_path):
    """TRN-03 (VALIDATION.md): same seed + same config -> identical CSV loss rows."""
    root_a = tmp_path / "runA"
    root_b = tmp_path / "runB"
    cfg_a, res_a = _make_cfg(root_a, seed=42, epochs=2)
    cfg_b, res_b = _make_cfg(root_b, seed=42, epochs=2)
    main(["--config", str(cfg_a)])
    main(["--config", str(cfg_b)])
    rows_a = _read_losses(_latest(res_a))
    rows_b = _read_losses(_latest(res_b))
    assert rows_a == rows_b, (
        f"Bit-identical reproducibility broken:\n  A: {rows_a}\n  B: {rows_b}"
    )
