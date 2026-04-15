"""Phase 4 Plan 04 Task 2 tests — YAML schemas + verify_pooling_caches.py.

Covers:
  Y1: configs/gated_fusion_2person.yaml shape/schema check.
  Y2: configs/gated_fusion_clip_mean.yaml shape/schema check.
  V1: verify_pooling_caches.py --help surface.
  V2: PASS mode on matching synthetic clip + clip_mean caches.
  V3: FAIL mode when clip_mean shape is wrong.
  V4: FAIL mode when clip_mean values don't match baseline[:, :512].
  V5: PASS mode on matching synthetic skeleton + skeleton_2person caches.
  V6: FAIL mode when skeleton_2person rank is wrong.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
# YAML schema tests
# -----------------------------------------------------------------------------

def test_config_2person_schema():
    """Y1: gated_fusion_2person.yaml has skel_dim=512 + skel_agg=concat + skel_2person path."""
    with open(PROJECT_ROOT / "configs/gated_fusion_2person.yaml", encoding="utf-8") as f:
        c = yaml.safe_load(f)
    assert c["model"]["variant"] == "gated_fusion"
    assert c["model"]["skel_dim"] == 512
    assert c["model"]["clip_dim"] == 1024
    assert c["data"]["skel_agg"] == "concat"
    assert c["paths"]["skeleton_features"].endswith("skeleton_2person")


def test_config_clip_mean_schema():
    """Y2: gated_fusion_clip_mean.yaml has clip_dim=512 + clip_mean path."""
    with open(PROJECT_ROOT / "configs/gated_fusion_clip_mean.yaml", encoding="utf-8") as f:
        c = yaml.safe_load(f)
    assert c["model"]["variant"] == "gated_fusion"
    assert c["model"]["skel_dim"] == 256
    assert c["model"]["clip_dim"] == 512
    assert c["paths"]["clip_features"].endswith("clip_mean")


# -----------------------------------------------------------------------------
# verify_pooling_caches.py — CLI + behavior tests
# -----------------------------------------------------------------------------

def _mk_matching_clip_cache(tmp_path, vid, N):
    """Create a matching pair: clip/{vid}.npy [N,1024] + clip_mean/{vid}.npy [N,512]
    where clip_mean == clip[:, :512] exactly."""
    clip_dir = tmp_path / "clip"
    clip_dir.mkdir(exist_ok=True)
    clip_mean_dir = tmp_path / "clip_mean"
    clip_mean_dir.mkdir(exist_ok=True)
    rng = np.random.default_rng(hash(vid) & 0xFFFF)
    clip = rng.standard_normal((N, 1024)).astype(np.float32)
    np.save(clip_dir / f"{vid}.npy", clip)
    np.save(clip_mean_dir / f"{vid}.npy", clip[:, :512].copy())
    return clip_dir, clip_mean_dir


def test_verify_pooling_help():
    """V1: --help surfaces --dataset + --cache + --cache-root + --baseline-root."""
    out = subprocess.run(
        [sys.executable, "scripts/verify_pooling_caches.py", "--help"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    combined = (out.stdout + out.stderr).lower()
    assert "--dataset" in combined and "--cache" in combined, combined[:500]
    assert "--cache-root" in combined, combined[:500]
    assert "--baseline-root" in combined, combined[:500]


def test_verify_pooling_clip_mean_pass(tmp_path):
    """V2: matching clip/clip_mean caches → exit 0, FAIL: 0."""
    for vid, N in [("Abuse028", 20), ("Arson011", 35)]:
        _mk_matching_clip_cache(tmp_path, vid, N)
    out = subprocess.run(
        [sys.executable, "scripts/verify_pooling_caches.py",
         "--dataset", "ucf", "--cache", "clip_mean",
         "--cache-root", str(tmp_path / "clip_mean"),
         "--baseline-root", str(tmp_path / "clip")],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    assert out.returncode == 0, f"stderr={out.stderr}\nstdout={out.stdout}"
    assert "FAIL: 0" in out.stdout


def test_verify_pooling_clip_mean_detects_mismatch(tmp_path):
    """V4: corrupted clip_mean values → exit non-zero, FAIL > 0."""
    vid = "Abuse028"
    clip_dir = tmp_path / "clip"
    clip_dir.mkdir()
    clip_mean_dir = tmp_path / "clip_mean"
    clip_mean_dir.mkdir()
    clip = np.random.default_rng(0).standard_normal((20, 1024)).astype(np.float32)
    np.save(clip_dir / f"{vid}.npy", clip)
    # Deliberately store a CORRUPTED clip_mean (all zeros instead of clip[:, :512])
    np.save(clip_mean_dir / f"{vid}.npy", np.zeros((20, 512), dtype=np.float32))
    out = subprocess.run(
        [sys.executable, "scripts/verify_pooling_caches.py",
         "--dataset", "ucf", "--cache", "clip_mean",
         "--cache-root", str(clip_mean_dir),
         "--baseline-root", str(clip_dir)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    assert out.returncode != 0
    assert "allclose fail" in out.stdout or "FAIL: 1" in out.stdout


def test_verify_pooling_clip_mean_shape_mismatch(tmp_path):
    """V3: clip_mean shape is (N, 512) but N differs from baseline → FAIL."""
    vid = "Abuse028"
    clip_dir = tmp_path / "clip"
    clip_dir.mkdir()
    clip_mean_dir = tmp_path / "clip_mean"
    clip_mean_dir.mkdir()
    rng = np.random.default_rng(0)
    np.save(clip_dir / f"{vid}.npy", rng.standard_normal((20, 1024)).astype(np.float32))
    # clip_mean has 21 rows not 20 — N mismatch
    np.save(clip_mean_dir / f"{vid}.npy", rng.standard_normal((21, 512)).astype(np.float32))
    out = subprocess.run(
        [sys.executable, "scripts/verify_pooling_caches.py",
         "--dataset", "ucf", "--cache", "clip_mean",
         "--cache-root", str(clip_mean_dir),
         "--baseline-root", str(clip_dir)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    assert out.returncode != 0, f"stdout={out.stdout}\nstderr={out.stderr}"
    assert "FAIL: 1" in out.stdout or "N mismatch" in out.stdout


def test_verify_pooling_skeleton_2person(tmp_path):
    """V5: matching skeleton/skeleton_2person caches → exit 0."""
    vid = "Abuse028"
    skel_dir = tmp_path / "skel"
    skel_dir.mkdir()
    skel2_dir = tmp_path / "skel2"
    skel2_dir.mkdir()
    rng = np.random.default_rng(0)
    np.save(skel_dir / f"{vid}.npy", rng.standard_normal((40, 256)).astype(np.float32))
    np.save(skel2_dir / f"{vid}.npy", rng.standard_normal((40, 2, 256)).astype(np.float32))
    out = subprocess.run(
        [sys.executable, "scripts/verify_pooling_caches.py",
         "--dataset", "ucf", "--cache", "skeleton_2person",
         "--cache-root", str(skel2_dir),
         "--baseline-root", str(skel_dir)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    assert out.returncode == 0, f"stderr={out.stderr}\nstdout={out.stdout}"


def test_verify_pooling_skeleton_2person_bad_rank(tmp_path):
    """V6: skeleton_2person saved as 2D (wrong rank) → FAIL.

    Tightened: require the script's FAIL summary line to be present, so we
    don't accidentally pass on a FileNotFoundError (missing script) during RED.
    """
    vid = "Abuse028"
    skel_dir = tmp_path / "skel"
    skel_dir.mkdir()
    skel2_dir = tmp_path / "skel2"
    skel2_dir.mkdir()
    rng = np.random.default_rng(0)
    np.save(skel_dir / f"{vid}.npy", rng.standard_normal((40, 256)).astype(np.float32))
    # Wrong: saved as [N, 256] instead of [N, 2, 256]
    np.save(skel2_dir / f"{vid}.npy", rng.standard_normal((40, 256)).astype(np.float32))
    out = subprocess.run(
        [sys.executable, "scripts/verify_pooling_caches.py",
         "--dataset", "ucf", "--cache", "skeleton_2person",
         "--cache-root", str(skel2_dir),
         "--baseline-root", str(skel_dir)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    assert out.returncode != 0
    # Ensure the failure came from our verifier, not a missing-file error
    assert "FAIL: 1" in out.stdout or "shape" in out.stdout.lower(), (
        f"stdout={out.stdout}\nstderr={out.stderr}"
    )
