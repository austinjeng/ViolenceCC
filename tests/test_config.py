"""TRN-05: config_snapshot.json contents + snapshot-as-config round trip."""
import json
import re

import pytest
import yaml

from src.utils.config import (
    load_config, load_snapshot_as_config, snapshot_config,
)


def _example_cfg():
    return {
        "seed": 42,
        "dataset": "ucf",
        "paths": {
            "skeleton_features": "E:/features/ucf/skeleton",
            "clip_features": "E:/features/ucf/clip",
            "splits_dir": "data/splits",
            "results_dir": "results",
        },
        "model": {"variant": "skeleton_only", "skel_dim": 256,
                  "head_hidden": [128, 32], "dropout": 0.3},
        "data": {"T": 32, "batch_size": 16, "num_workers": 0, "pin_memory": False},
        "train": {
            "lr": 1.0e-4, "weight_decay": 1.0e-2,
            "epochs": 50, "warmup_epochs": 5, "patience": 10,
            "k_topk": 3, "margin": 1.0,
            "lam_sparse": 8.0e-3, "lam_smooth": 8.0e-4,
        },
        "wandb": {"project": "violencecc", "mode": "disabled", "tags": ["test"]},
    }


def test_snapshot_contents(tmp_path):
    cfg = _example_cfg()
    out = tmp_path / "snap.json"
    snapshot_config(cfg, out)
    assert out.exists()

    snap = json.loads(out.read_text())
    expected_keys = {"config", "git", "python", "torch", "numpy",
                     "cuda", "env", "packages"}
    assert set(snap.keys()) == expected_keys

    # config round-trip
    assert snap["config"] == cfg

    # env captures the CUBLAS_WORKSPACE_CONFIG set by src/train.py entry point
    # (it is set globally at import time, so at test time it is already ':4096:8')
    import os as _os
    _os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    snapshot_config(cfg, out)
    snap2 = json.loads(out.read_text())
    assert snap2["env"]["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"

    # packages is a list of sorted "name==version" strings
    pkgs = snap["packages"]
    assert isinstance(pkgs, list)
    assert all(isinstance(p, str) and "==" in p for p in pkgs[:5])
    # At least torch and numpy should be present
    names = [p.split("==")[0].lower() for p in pkgs]
    assert "torch" in names
    assert "numpy" in names

    # git info shape
    assert "sha" in snap["git"] and "dirty" in snap["git"]
    # When inside a git repo, sha is a 40-char hex string
    sha = snap["git"]["sha"]
    if sha != "unknown":
        assert re.fullmatch(r"[0-9a-f]{40}", sha), sha


def test_load_snapshot_as_config(tmp_path):
    cfg = _example_cfg()
    out = tmp_path / "snap.json"
    snapshot_config(cfg, out)

    reloaded = load_snapshot_as_config(out)
    assert reloaded == cfg


def test_load_config_dispatches_by_extension(tmp_path):
    cfg = _example_cfg()

    # YAML path
    y = tmp_path / "c.yaml"
    y.write_text(yaml.safe_dump(cfg))
    assert load_config(y) == cfg

    # JSON snapshot path
    j = tmp_path / "snap.json"
    snapshot_config(cfg, j)
    assert load_config(j) == cfg


def test_load_snapshot_missing_config_key(tmp_path):
    j = tmp_path / "broken.json"
    j.write_text(json.dumps({"not_config": {}}))
    with pytest.raises(ValueError, match="not a valid config_snapshot"):
        load_snapshot_as_config(j)
