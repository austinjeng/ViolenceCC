"""YAML config load + snapshot (TRN-05) + Phase 4 eval reproducibility helpers.

TRN-05 snapshot captures the resolved config + git + python/torch/numpy
versions + env + pip freeze so a checkpoint is reproducible by anyone on
the same machine.

Phase 4 D-12 additions (config_hash / checkpoint_sha / git_sha): produce
stable, whitespace- and key-order-invariant identifiers written into
eval_metrics.json so running evaluate.py twice on the same best_model.pth
yields byte-identical non-clock keys (SC #4 bit-identical reproducibility).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Union

import yaml


def load_config(path: Union[str, Path]) -> dict:
    """Load a YAML or JSON-snapshot config.

    If `path` ends with .json, treat it as a `config_snapshot.json` and extract
    the `config` sub-dict. This enables bit-identical reruns:
        python src/train.py --config results/<prior_run>/config_snapshot.json
    """
    p = Path(path)
    if p.suffix.lower() == ".json":
        return load_snapshot_as_config(p)
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_snapshot_as_config(snapshot_path: Union[str, Path]) -> dict:
    """Extract the `config` field from a config_snapshot.json."""
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snap = json.load(f)
    if "config" not in snap:
        raise ValueError(
            f"{snapshot_path} is not a valid config_snapshot.json "
            "(missing 'config' key)"
        )
    return snap["config"]


def _git_info() -> dict:
    """Best-effort capture of current HEAD sha + dirty flag.

    Returns {"sha": "unknown", "dirty": False} if git is not available or the
    current directory is not a git repo. Never raises.
    """
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        sha = "unknown"
        dirty = False
    return {"sha": sha, "dirty": dirty}


def _get_version(pkg_name: str) -> str:
    try:
        mod = __import__(pkg_name)
        return getattr(mod, "__version__", "unknown")
    except ImportError:
        return "not-installed"


def _pip_freeze() -> list:
    """In-process pip freeze via importlib.metadata (stdlib)."""
    try:
        from importlib.metadata import distributions
        names = []
        for d in distributions():
            name = d.metadata.get("Name") if d.metadata else None
            if not name:
                continue
            names.append(f"{name}=={d.version}")
        return sorted(set(names))
    except Exception:
        return []


def snapshot_config(cfg: dict, path: Union[str, Path]) -> None:
    """Write a reproducibility snapshot alongside a checkpoint (TRN-05).

    Contents (RESEARCH.md §6.3):
      config, git{sha,dirty}, python, torch, numpy, cuda, env, packages
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Local import so this module stays torch-free for unit testing of the
    # JSON-only round-trip paths.
    import torch
    cuda_ver = getattr(torch.version, "cuda", None)

    snap = {
        "config": cfg,
        "git": _git_info(),
        "python": sys.version,
        "torch": _get_version("torch"),
        "numpy": _get_version("numpy"),
        "cuda": cuda_ver,
        "env": {
            "CUBLAS_WORKSPACE_CONFIG": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
            "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
        },
        "packages": _pip_freeze(),
    }
    path.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")


# ---------------------------------------------------------------------------
# Phase 4 D-12 reproducibility-metadata helpers.
# These back the evaluate.py `eval_metrics.json` contract:
#   - config_hash(cfg)  -> stable SHA256 identifier of the resolved config
#   - checkpoint_sha(p) -> SHA256 of best_model.pth bytes (streamed for 100MB+
#     checkpoints; keeps RAM use at ~1 MB regardless of file size)
#   - git_sha()         -> 40-hex HEAD + "-dirty" suffix when working tree dirty
#                          or "unknown" when git is unavailable
# Running evaluate.py twice on the same run_dir must produce byte-identical
# values for all three across invocations (SC #4 inherits from Phase 3).
# ---------------------------------------------------------------------------


def config_hash(cfg: dict) -> str:
    """SHA256 of sort_keys=True JSON serialization — whitespace + order invariant (D-12).

    pathlib.Path, numpy scalars, and other non-JSON-native values are coerced
    to strings via the default=str hook on the outer dump; the resulting
    plain-dict is then re-serialized with the canonical separators+sort_keys
    combination so the byte-level payload is insensitive to Python dict
    insertion order.
    """
    serializable = json.loads(json.dumps(cfg, default=str))  # Path -> str
    payload = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def checkpoint_sha(path: Union[str, Path]) -> str:
    """SHA256 of best_model.pth raw bytes, streamed in 1 MB chunks (D-12).

    Never loads the whole file into RAM — safe for 100+ MB I3D-model checkpoints
    on laptops with low free memory.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    """`git rev-parse HEAD` with `-dirty` suffix if working tree dirty (D-12).

    Returns the string "unknown" when git is not installed, not on PATH, or
    the current directory is not a git repo. Never raises: this helper is
    called from evaluate.py where a missing git shouldn't take the eval down.
    """
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL
        ).strip())
        return sha + ("-dirty" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"
