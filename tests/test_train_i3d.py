"""Unit tests for train_one_epoch_i3d, validate_i3d, and main() dispatch (Phase 4b Plan 03).

Covers VALIDATION.md rows 4b-03-01 / 4b-03-02 / 4b-03-03:
  - train_one_epoch_i3d runs 1 step and returns finite loss
  - validate_i3d signature matches validate contract (D-04 parallel)
  - main() dispatches to i3d path when cfg.dataset == 'xd_i3d'

Plus D-12 diagnostic check: [i3d_audit] log line emitted on the first step
of the first 3 epochs (verified via capfd capture inside the main dispatch
test). Pitfall 1 guard: mask is always synthesized as all-ones.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import torch
import yaml

from src.train import (
    train_one_epoch_i3d,
    validate_i3d,
    validate,
    main,
)
from src.data.loaders import build_dataloaders_i3d
from src.models.registry import build_model


# ------------------------------------------------------------------
# Helper: synthesize xd_val.txt from the fixture's train split.
# synthetic_i3d_features only ships xd_train.txt + xd_test.txt; the i3d
# train/val loaders both expect xd_val.txt, so we create a minimal one
# here that reuses one normal + one abnormal video from training.
# ------------------------------------------------------------------
def _ensure_val_split(fx) -> None:
    """Create xd_val.txt if missing; mirrors the pattern in test_loaders_i3d.py."""
    splits_dir = fx["train_split"].parent
    val_split = splits_dir / "xd_val.txt"
    if not val_split.exists():
        train_ids = fx["train_split"].read_text(encoding="utf-8").strip().splitlines()
        normal = next((v for v in train_ids if v.strip().endswith("_label_A")), None)
        abnorm = next((v for v in train_ids if not v.strip().endswith("_label_A")), None)
        assert normal is not None and abnorm is not None, (
            "fixture missing mixed labels"
        )
        val_split.write_text(f"{normal}\n{abnorm}\n", encoding="utf-8")


# ------------------------------------------------------------------
# Helper: build a 1-epoch xd_i3d cfg YAML pointing at the synthetic fixture.
# Mirrors test_train_integration.py::_build_smoke_dataset but for xd_i3d.
# ------------------------------------------------------------------
def _build_smoke_xd_i3d_config(fx, tmp_path: Path) -> Path:
    """Write a 1-epoch xd_i3d YAML that main() can consume end-to-end."""
    results = tmp_path / "results"
    results.mkdir(exist_ok=True)
    _ensure_val_split(fx)
    splits_dir = fx["train_split"].parent

    cfg = {
        "seed": 42,
        "dataset": "xd_i3d",
        "paths": {
            # synthetic_i3d_features lays out tmp_path/i3d/RGB and tmp_path/i3d/RGBTest;
            # build_dataloaders_i3d expects paths.i3d_features to be the PARENT of RGB/.
            "i3d_features": str(fx["rgb"].parent),
            "splits_dir": str(splits_dir),
            "results_dir": str(results),
        },
        "model": {
            "variant": "rtfm_i3d",
            "i3d_dim": 1024,
            "head_hidden": [128, 32],
            "dropout": 0.3,
        },
        "data": {
            "T": 32,
            "batch_size": 1,   # 1 video * 5 crops = 5 samples, sufficient for k_topk=3
            "num_workers": 0,
            "pin_memory": False,
        },
        "train": {
            "lr": 1e-4,
            "weight_decay": 1e-2,
            "epochs": 1,
            "warmup_epochs": 0,
            "patience": 10,
            "k_topk": 3,
            "margin": 1.0,
            "lam_sparse": 8e-3,
            "lam_smooth": 8e-4,
        },
        "wandb": {"project": "violencecc", "mode": "disabled", "tags": []},
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return cfg_path


def _latest_run(results_dir: Path) -> Path:
    """Mirror of test_train_integration.py::_latest_run."""
    runs = [p for p in results_dir.iterdir() if p.is_dir()]
    assert runs, f"no run dirs in {results_dir}"
    return max(runs, key=lambda p: p.stat().st_mtime)


# ==================================================================
# VALIDATION.md row 4b-03-01: train_one_epoch_i3d loss-finite
# ==================================================================
def test_train_one_step_loss_finite(synthetic_i3d_features, tmp_path):
    """train_one_epoch_i3d runs >=1 step on the synthetic fixture and returns a finite float."""
    fx = synthetic_i3d_features
    _ensure_val_split(fx)
    splits_dir = fx["train_split"].parent

    cfg = {
        "seed": 42,
        "dataset": "xd_i3d",
        "paths": {
            "splits_dir": str(splits_dir),
            "i3d_features": str(fx["rgb"].parent),
        },
        "data": {
            "T": 32,
            "batch_size": 1,
            "num_workers": 0,
            "pin_memory": False,
        },
    }
    (nor, abn), _val = build_dataloaders_i3d(cfg)

    model = build_model(
        variant="rtfm_i3d", i3d_dim=1024, head_hidden=[128, 32], dropout=0.3
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    train_cfg = {
        "k_topk": 3,
        "margin": 1.0,
        "lam_sparse": 8e-3,
        "lam_smooth": 8e-4,
    }

    loss = train_one_epoch_i3d(model, nor, abn, optimizer, "cpu", train_cfg, epoch=0)

    assert isinstance(loss, float), f"expected float, got {type(loss)}"
    # NaN check: x != x iff NaN
    assert loss == loss, f"loss is NaN: {loss}"
    assert loss < float("inf"), f"loss is inf: {loss}"
    assert loss > -float("inf"), f"loss is -inf: {loss}"


# ==================================================================
# VALIDATION.md row 4b-03-02: validate_i3d signature matches validate
# ==================================================================
def test_validate_i3d_signature():
    """validate_i3d has the same parameter signature as validate (D-04 parallel contract).

    Ensures the dispatch branch in main() can swap one function for the other
    without changing the call site (beyond the `_val_fn(...)` indirection).
    """
    sig_validate = inspect.signature(validate)
    sig_validate_i3d = inspect.signature(validate_i3d)
    assert list(sig_validate.parameters.keys()) == list(
        sig_validate_i3d.parameters.keys()
    ), (
        f"validate params: {list(sig_validate.parameters.keys())}; "
        f"validate_i3d params: {list(sig_validate_i3d.parameters.keys())}"
    )
    # Both should return float (annotation) or be unannotated.
    assert (
        sig_validate.return_annotation is float
        or sig_validate.return_annotation is inspect.Signature.empty
    )
    assert (
        sig_validate_i3d.return_annotation is float
        or sig_validate_i3d.return_annotation is inspect.Signature.empty
    )


# ==================================================================
# VALIDATION.md row 4b-03-03: main() dispatches to xd_i3d path
# ==================================================================
def test_main_dispatch_xd_i3d(synthetic_i3d_features, tmp_path, capfd):
    """main() with cfg.dataset=='xd_i3d' completes 1 epoch; artifacts written.

    Also doubles as the D-12 diagnostic check: the [i3d_audit] log line MUST
    appear in captured stderr (or stdout on some shells) during epoch 0 step 0.
    """
    fx = synthetic_i3d_features
    cfg_path = _build_smoke_xd_i3d_config(fx, tmp_path)

    rc = main(["--config", str(cfg_path), "--epochs", "1"])
    assert rc == 0, "main() exited non-zero"

    run = _latest_run(tmp_path / "results")
    assert (run / "best_model.pth").exists(), "best_model.pth not written"
    assert (run / "config_snapshot.json").exists(), "config_snapshot.json not written"
    assert (run / "train_log.csv").exists(), "train_log.csv not written"

    # D-12 audit check: stderr should contain [i3d_audit] on epoch 0 step 0.
    captured = capfd.readouterr()
    combined = captured.err + captured.out
    assert "[i3d_audit]" in combined, (
        f"D-12 bag-size audit line not emitted during 1-epoch smoke.\n"
        f"STDERR: {captured.err!r}\nSTDOUT: {captured.out!r}"
    )
