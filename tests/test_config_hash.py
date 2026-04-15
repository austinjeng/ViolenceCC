"""Unit tests for config_hash / checkpoint_sha / git_sha helpers (Plan 04-02 Task 1).

These back the D-12 reproducibility-metadata contract: running evaluate.py twice
on the same run_dir must produce byte-identical eval_metrics.json for all
non-clock-dependent keys. config_hash MUST be whitespace- and key-order
insensitive; checkpoint_sha MUST stream large files (no full-read into RAM);
git_sha MUST surface working-tree-dirty state with a '-dirty' suffix.
"""
from __future__ import annotations

import hashlib
import os

import pytest

from src.utils.config import config_hash, checkpoint_sha, git_sha


def test_config_hash_deterministic():
    """H1: two calls with the same dict return the same hex digest."""
    cfg = {"a": 1, "b": {"c": 2, "d": [3, 4]}, "seed": 42}
    assert config_hash(cfg) == config_hash(dict(cfg))


def test_config_hash_key_order_invariant():
    """H2: key-order permutation must not change the digest."""
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})


def test_config_hash_path_conversion():
    """H3: pathlib.Path values are coerced to strings before hashing (default=str)."""
    from pathlib import Path
    h = config_hash({"paths": {"root": Path("C:/x")}, "seed": 42})
    assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def test_checkpoint_sha_streaming(tmp_path):
    """H4: digest a 3 MB random file and compare with a reference full-read SHA256."""
    p = tmp_path / "dummy.pth"
    p.write_bytes(os.urandom(3 * 1024 * 1024))  # 3 MB
    h = checkpoint_sha(p)
    assert len(h) == 64
    # Reference: hash same bytes in one shot
    h_ref = hashlib.sha256(p.read_bytes()).hexdigest()
    assert h == h_ref


def test_git_sha_shape():
    """H5: git_sha returns 40-hex (clean), 40-hex+'-dirty' (dirty), or 'unknown'."""
    sha = git_sha()
    if sha == "unknown":
        return
    assert len(sha) == 40 or sha.endswith("-dirty"), (
        f"git_sha returned unexpected shape: {sha!r}"
    )
