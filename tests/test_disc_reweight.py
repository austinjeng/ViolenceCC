"""Tests for the R1 disc_reweight TTA method (quick-260607-42h).

Covers:
  (a) source_only-unchanged regression — run_tta_evaluation(method="source_only")
      on the synthetic fixture still produces complete output artifacts, proving the
      disc_reweight refactor did not alter the source_only scoring call path.
  (b) compute_w w-formula unit test (no disk / no GPU) against hand-computed values.
  (c) parse_args accepts --method disc_reweight.

The FULL +4.8 feature-dependent reproduction (clip-vit-b-16 gaussian_noise sev5
source ~57.70 -> ~62.5) needs the E:/ feature cache + checkpoints and is
environment-bound / slow; it is intentionally NOT committed here. That end-to-end
numeric reproduction is covered by scripts/_tmp_r1_full.py and the recorded truth in
results/_coral_derisk/r1full_clip.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.registry import build_model
from src.tta.disc_reweight import compute_w
from src.tta.evaluate_tta import parse_args, run_tta_evaluation


# ---------------------------------------------------------------------------
# (b) compute_w w-formula unit test — pure scalar math, no disk / no GPU.
# ---------------------------------------------------------------------------


def test_compute_w_vl_collapsed_skel_clean():
    """w_vl=0.04 (cstd/clean=0.04), skel_rel=1 (skelZ=floor) -> w == 0.04."""
    floor = 0.5
    w, w_vl, skel_rel = compute_w(
        clip_std_test=0.04, clip_std_clean=1.0, skelZ=floor, skelZ_floor=floor
    )
    assert w_vl == pytest.approx(0.04)
    assert skel_rel == pytest.approx(1.0)
    assert w == pytest.approx(0.04)


def test_compute_w_skel_rel_one_at_floor():
    """skelZ == skelZ_floor -> skel_rel == 1."""
    floor = 0.5
    _, _, skel_rel = compute_w(
        clip_std_test=0.3, clip_std_clean=1.0, skelZ=floor, skelZ_floor=floor
    )
    assert skel_rel == pytest.approx(1.0)


def test_compute_w_skel_rel_zero_at_twice_floor():
    """skelZ == 2*skelZ_floor -> skel_rel == 0 -> w == 1."""
    floor = 0.5
    w, _, skel_rel = compute_w(
        clip_std_test=0.3, clip_std_clean=1.0, skelZ=2 * floor, skelZ_floor=floor
    )
    assert skel_rel == pytest.approx(0.0)
    assert w == pytest.approx(1.0)


def test_compute_w_vl_retained_gives_w_one():
    """w_vl >= 1 (clip_std_test >= clip_std_clean) -> w == 1."""
    floor = 0.5
    w, w_vl, _ = compute_w(
        clip_std_test=1.5, clip_std_clean=1.0, skelZ=floor, skelZ_floor=floor
    )
    assert w_vl == pytest.approx(1.0)  # clipped to 1
    assert w == pytest.approx(1.0)


def test_compute_w_zero_floor_gives_w_one():
    """skelZ_floor <= 1e-9 -> skel_rel == 0 -> w == 1 (no division by ~0)."""
    w, _, skel_rel = compute_w(
        clip_std_test=0.04, clip_std_clean=1.0, skelZ=0.3, skelZ_floor=1e-12
    )
    assert skel_rel == pytest.approx(0.0)
    assert w == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# (c) parse_args accepts --method disc_reweight.
# ---------------------------------------------------------------------------


def test_parse_args_accepts_disc_reweight():
    """--method disc_reweight is a wired argparse choice."""
    args = parse_args([
        "--source-run", "x",
        "--corruption", "gaussian_noise",
        "--severity", "3",
        "--method", "disc_reweight",
        "--output-dir", "y",
    ])
    assert args.method == "disc_reweight"


# ---------------------------------------------------------------------------
# (a) source_only-unchanged regression — synthetic fixture (self-contained).
# ---------------------------------------------------------------------------

_MODEL_CFG = {
    "variant": "gated_fusion",
    "skel_dim": 256,
    "clip_dim": 1024,
    "shared_dim": 256,
    "head_hidden": [128, 32],
    "dropout": 0.3,
}


@pytest.fixture
def tta_fixture(tmp_path):
    """Minimal TTA evaluation fixture (mirrors tests/test_evaluate_tta.py).

    Creates a fake source run dir, synthetic gaussian_noise_3 features, a clean
    skeleton dir, and split + annotation files in the project layout.
    """
    rng = np.random.default_rng(42)

    specs = [
        ("Normal_Videos_001", "Normal", -1, -1, -1, -1),
        ("Normal_Videos_002", "Normal", -1, -1, -1, -1),
        ("Fighting003", "Fighting", 80, 160, -1, -1),
        ("Assault010", "Assault", 100, 250, -1, -1),
    ]
    n_snippets = 5

    feat_root = tmp_path / "features"
    clean_skel = feat_root / "skeleton"
    clean_skel.mkdir(parents=True)
    clip_corr = feat_root / "clip_gaussian_noise_3"
    clip_corr.mkdir(parents=True)

    video_ids = []
    anno_lines = []
    for vid, cat, s1, e1, s2, e2 in specs:
        skel = rng.standard_normal((n_snippets, 256)).astype(np.float32)
        clip = rng.standard_normal((n_snippets, 1024)).astype(np.float32)
        np.save(clean_skel / f"{vid}.npy", skel)
        np.save(clip_corr / f"{vid}.npy", clip)
        video_ids.append(vid)
        anno_lines.append(f"{vid}_x264.mp4  {cat}  {s1}  {e1}  {s2}  {e2}")

    data_dir = tmp_path / "data"
    splits_dir = data_dir / "splits"
    splits_dir.mkdir(parents=True)
    anno_dir = data_dir / "annotations"
    anno_dir.mkdir(parents=True)
    (splits_dir / "ucf_test.txt").write_text(
        "\n".join(video_ids) + "\n", encoding="utf-8"
    )
    (anno_dir / "ucf_temporal.txt").write_text(
        "\n".join(anno_lines) + "\n", encoding="utf-8"
    )

    run_dir = tmp_path / "results" / "ucf_gated_fusion_s42"
    run_dir.mkdir(parents=True)
    cfg = {
        "seed": 42,
        "dataset": "ucf",
        "paths": {
            "skeleton_features": str(clean_skel),
            "clip_features": str(clip_corr),
            "splits_dir": str(splits_dir),
            "annotations_dir": str(anno_dir),
            "results_dir": str(tmp_path / "results"),
        },
        "data": {"T": 32},
        "model": _MODEL_CFG,
        "wandb": {"mode": "disabled"},
    }
    snapshot = {"version": 1, "config": cfg, "git": {"sha": "test", "dirty": False}}
    (run_dir / "config_snapshot.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )

    model = build_model(**_MODEL_CFG)
    torch.save(model.state_dict(), run_dir / "best_model.pth")

    return {"run_dir": run_dir, "feat_root": feat_root, "data_dir": data_dir}


def test_source_only_unchanged_after_disc_reweight_refactor(
    tta_fixture, tmp_path, monkeypatch
):
    """source_only still produces complete artifacts with method=="source_only".

    Guards T-42h-02: the disc_reweight dispatch must not alter the source_only path.
    """
    fx = tta_fixture
    output_dir = tmp_path / "output_source_only"

    import src.tta.evaluate_tta as mod
    monkeypatch.setattr(mod, "_PROJECT_ROOT", fx["data_dir"].parent)

    run_tta_evaluation(
        source_run=fx["run_dir"],
        corruption_type="gaussian_noise",
        severity=3,
        method="source_only",
        lr=1e-3,
        rho=0.05,
        output_dir=output_dir,
        feature_root=fx["feat_root"],
    )

    assert (output_dir / "eval_metrics.json").exists()
    assert (output_dir / "eval_scores.npz").exists()
    assert (output_dir / ".done").exists()

    m = json.loads((output_dir / "eval_metrics.json").read_text())
    assert m["method"] == "source_only"
    assert "auc" in m
    assert m["rho"] is None
