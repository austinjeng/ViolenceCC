"""TRN-06 acceptance tests. All 4 variants run through src/train.py.

Marked @pytest.mark.e2e so the fast unit suite skips them. Run with:
    python -m pytest tests/test_train_e2e.py -v --tb=short
"""
from __future__ import annotations

import csv
import json
import os
import pathlib

import numpy as np
import pytest
import yaml

from src.train import main


pytestmark = pytest.mark.e2e


CONFIG_ROOT = pathlib.Path("configs")
VARIANTS = ["skeleton_only", "clip_only", "late_fusion", "gated_fusion"]


def _build_synth_features_and_splits(root):
    """20 train (10+10) + 8 val (4+4) videos with [N=40, 256/1024] synthetic arrays."""
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
        rng = np.random.default_rng(abs(hash(v)) & 0xFFFF)
        np.save(skel / f"{v}.npy", rng.standard_normal((40, 256)).astype(np.float32))
        rng2 = np.random.default_rng((abs(hash(v)) + 1) & 0xFFFF)
        np.save(clip / f"{v}.npy", rng2.standard_normal((40, 1024)).astype(np.float32))
    (splits / "ucf_train.txt").write_text("\n".join(train_nor + train_abn) + "\n")
    (splits / "ucf_val.txt").write_text("\n".join(val_nor + val_abn) + "\n")
    return results, splits, skel, clip


def _adapt_yaml(base_yaml_path, tmp_root):
    """Load configs/<variant>.yaml, rewrite paths to point at tmp_root, disable wandb."""
    with open(base_yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    results, splits, skel, clip = _build_synth_features_and_splits(tmp_root)
    cfg["paths"]["skeleton_features"] = str(skel)
    cfg["paths"]["clip_features"] = str(clip)
    cfg["paths"]["splits_dir"] = str(splits)
    cfg["paths"]["results_dir"] = str(results)
    cfg["data"]["batch_size"] = 5
    cfg["data"]["num_workers"] = 0
    cfg["data"]["pin_memory"] = False
    cfg["train"]["epochs"] = 1
    cfg["train"]["warmup_epochs"] = 0
    cfg["wandb"]["mode"] = "disabled"
    out = tmp_root / f"{cfg['model']['variant']}.yaml"
    out.write_text(yaml.safe_dump(cfg))
    return out, results


def _latest_run(results):
    return sorted([p for p in results.iterdir() if p.is_dir()])[-1]


def test_skeleton_only_trains(tmp_path):
    """TRN-06 acceptance: `python src/train.py --config configs/skeleton_only.yaml` succeeds."""
    base = CONFIG_ROOT / "skeleton_only.yaml"
    cfg_path, results = _adapt_yaml(base, tmp_path)
    rc = main(["--config", str(cfg_path)])
    assert rc == 0
    run = _latest_run(results)
    assert (run / "train_log.csv").exists()
    assert (run / "best_model.pth").exists()
    assert (run / "last_model.pth").exists()
    assert (run / "config_snapshot.json").exists()


def test_all_variants_cli(tmp_path):
    """TRN-06: same train.py entry point works for all 4 variants via YAML change only."""
    for variant in VARIANTS:
        sub = tmp_path / variant
        sub.mkdir()
        base = CONFIG_ROOT / f"{variant}.yaml"
        assert base.exists(), f"missing config: {base}"
        cfg_path, results = _adapt_yaml(base, sub)
        rc = main(["--config", str(cfg_path)])
        assert rc == 0, f"variant {variant} failed"
        run = _latest_run(results)
        assert (run / "train_log.csv").exists()
        assert (run / "config_snapshot.json").exists()
        # Sanity-check that the snapshot's model.variant matches the expected one
        snap = json.loads((run / "config_snapshot.json").read_text())
        assert snap["config"]["model"]["variant"] == variant


def test_snapshot_roundtrip(tmp_path):
    """TRN-05 acceptance + Success Criterion #4:
    `--config <config_snapshot.json>` produces a valid run whose train_log.csv
    is bit-identical to the original run that produced the snapshot.

    This is the load-bearing test for ROADMAP Success Criterion #4:
      "re-running with --config results/<run>/config_snapshot.json reproduces
       bit-identical loss curves (confirmed by fixed seed)".

    Plan 06's test_bit_identical covers the two-YAML case; this test covers
    the snapshot-as-config code path (load_snapshot_as_config extracts the
    `config` sub-dict). A bug in that shim could break SC #4 without
    test_bit_identical catching it.
    """
    base = CONFIG_ROOT / "skeleton_only.yaml"
    cfg_path, results = _adapt_yaml(base, tmp_path)
    rc1 = main(["--config", str(cfg_path)])
    assert rc1 == 0
    run1 = _latest_run(results)
    snap_path = run1 / "config_snapshot.json"
    assert snap_path.exists()

    # Feed the snapshot back in as --config
    rc2 = main(["--config", str(snap_path)])
    assert rc2 == 0
    runs = sorted([p for p in results.iterdir() if p.is_dir()])
    assert len(runs) >= 2, "second run did not create a fresh dir"
    run2 = runs[-1]
    assert run2 != run1, "run2 must be a different dir from run1"

    # --- Success Criterion #4: bit-identical CSV rows ---
    csv1 = run1 / "train_log.csv"
    csv2 = run2 / "train_log.csv"
    assert csv1.exists() and csv2.exists(), "both runs must have a train_log.csv"

    with open(csv1, "r", encoding="utf-8") as f:
        rows1 = list(csv.DictReader(f))
    with open(csv2, "r", encoding="utf-8") as f:
        rows2 = list(csv.DictReader(f))

    # Row-count equality -- catches partial/crashed runs (e.g. one stopped at
    # epoch 3, the other at epoch 5) rather than silently passing on a
    # subset match of the first N rows.
    assert len(rows1) == len(rows2), (
        f"row count diverged: run1={len(rows1)} rows, run2={len(rows2)} rows. "
        f"A partial crash or early-stop divergence breaks SC #4."
    )
    assert len(rows1) > 0, "no CSV rows written -- smoke run produced empty log"

    # Exact (train_loss, val_loss) tuple equality per row. Use string equality
    # on the CSV-formatted floats (CSVLogger writes %.6f / %.6f / %.8f) so a
    # one-ULP drift fails just as loudly as a gross divergence.
    losses1 = [(r["train_loss"], r["val_loss"]) for r in rows1]
    losses2 = [(r["train_loss"], r["val_loss"]) for r in rows2]
    assert losses1 == losses2, (
        f"snapshot rerun diverged from original run -- SC #4 broken.\n"
        f"  run1 ({run1.name}): {losses1}\n"
        f"  run2 ({run2.name}): {losses2}\n"
        f"  snapshot: {snap_path}"
    )
