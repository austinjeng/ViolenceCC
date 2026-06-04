"""Phase 5 TTA evaluation entry point (TTA-06).

Runs one TTA configuration: loads source model, loads corrupted features,
adapts per-video (TENT/SAR/source_only), computes frame-level AUC.

Called as subprocess by scripts/run_ablations.py for each TTA RunSpec.

Usage:
    python src/tta/evaluate_tta.py \
        --source-run results/ucf_gated_fusion_s42 \
        --corruption gaussian_noise --severity 3 \
        --method tent --lr 1e-3 \
        --output-dir results/tta/tent_gaussian_noise_3_lr0.001
"""
# D-12 reproducibility: CUBLAS_WORKSPACE_CONFIG must be set BEFORE torch import.
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import logging
import sys
import tempfile
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path

# Script-mode bootstrap (same pattern as src/evaluate.py and src/train.py):
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np
import torch

from src.eval.metrics import compute_frame_metrics
from src.eval.snippet_to_frame import snippet_to_frame
from src.eval.ucf_annotations import VideoAnnotation, frame_labels, parse_annotations
from src.models.registry import build_model
from src.tta.sam import SAM
from src.tta.sar import SarAdaptor
from src.tta.tent import TentAdaptor, collect_params, configure_model
from src.utils.checkpoint import load_checkpoint
from src.utils.config import load_snapshot_as_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

CORRUPTION_TYPES = ("gaussian_noise", "jpeg_compression", "brightness", "motion_blur")

# Backbone -> feature subdirectory prefix (matches extract_clip.py output_subdir)
BACKBONE_FEATURE_PREFIX = {
    "clip-vit-b-16": "clip",
    "siglip2-base": "siglip2",
    "siglip2-so400m": "siglip2_so400m",
    "siglip2-giant": "siglip2_giant",
}

# Backbone -> s42 gated fusion source run directory name
BACKBONE_SOURCE_RUNS = {
    "clip-vit-b-16": "ucf_gated_fusion_s42",
    "siglip2-base": "ucf_gated_fusion_siglip2_s42",
    "siglip2-so400m": "ucf_gated_fusion_so400m_s42",
    "siglip2-giant": "ucf_gated_fusion_giant_s42",
}

BACKBONE_CHOICES = list(BACKBONE_FEATURE_PREFIX.keys())


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="TTA evaluation (Phase 5 TTA-06)")
    ap.add_argument("--source-run", required=True,
                    help="Source model run dir (contains config_snapshot.json + best_model.pth)")
    ap.add_argument("--corruption", required=True, choices=CORRUPTION_TYPES)
    ap.add_argument("--severity", required=True, type=int, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--method", required=True, choices=["source_only", "tent", "sar"])
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--rho", type=float, default=0.05, help="SAR only: SAM rho")
    ap.add_argument("--backbone", type=str, default="clip-vit-b-16",
                    choices=BACKBONE_CHOICES,
                    help="Vision backbone for feature loading (default: clip-vit-b-16)")
    ap.add_argument("--output-dir", required=True,
                    help="Output directory for eval_metrics.json + eval_scores.npz + .done")
    ap.add_argument("--feature-root", type=str, default="E:/features/ucf",
                    help="Root directory for corruption feature caches")
    return ap.parse_args(argv)


# ---------------------------------------------------------------------------
# Feature loading — bypass test_loader.py entirely (Pitfall 5 / C3 guard)
# ---------------------------------------------------------------------------

# M7: gaussian_noise and brightness use CLEAN skeleton cache.
# Only motion_blur and jpeg_compression require skeleton re-extraction.
SKELETON_REEXTRACT_TYPES = ("motion_blur", "jpeg_compression")


def _load_test_video_features(
    video_id: str,
    corruption_type: str,
    severity: int,
    feature_root: Path,
    backbone: str = "clip-vit-b-16",
) -> tuple:
    """Load corrupted skel + clip .npy for one test video.

    Per M7: gaussian_noise and brightness use CLEAN skeleton cache
    (corruption only affects pixel-domain, not skeleton joint coordinates
    extracted from clean video).

    Args:
        backbone: Vision backbone key — determines feature subdirectory prefix
                  via BACKBONE_FEATURE_PREFIX (e.g. 'clip', 'siglip2_giant').
    """
    prefix = BACKBONE_FEATURE_PREFIX[backbone]
    clip_dir = feature_root / f"{prefix}_{corruption_type}_{severity}"
    if corruption_type in SKELETON_REEXTRACT_TYPES:
        skel_dir = feature_root / f"skeleton_{corruption_type}_{severity}"
    else:
        skel_dir = feature_root / "skeleton"  # clean cache

    clip_path = clip_dir / f"{video_id}.npy"
    skel_path = skel_dir / f"{video_id}.npy"

    if not clip_path.exists() or not skel_path.exists():
        return None, None  # skip missing videos (sub-64-frame)

    clip_feat = np.load(str(clip_path))   # [N, 1024]
    skel_feat = np.load(str(skel_path))   # [N, 256]
    return skel_feat, clip_feat


# ---------------------------------------------------------------------------
# Per-video adaptation loop (D-07 online adapt+score)
# ---------------------------------------------------------------------------


def _adapt_one_video(
    adaptor,
    skel_feat: np.ndarray,
    clip_feat: np.ndarray,
    method: str,
    device: str,
    T: int = 32,
) -> np.ndarray:
    """Adapt and collect scores for one video.

    Chunks features into T=32-snippet batches per TTA-07.
    Returns snippet scores as 1D numpy array.
    """
    adaptor.reset()
    n_snippets = skel_feat.shape[0]
    all_scores = []

    for start in range(0, n_snippets, T):
        end = min(start + T, n_snippets)
        skel_batch = torch.from_numpy(
            skel_feat[start:end].astype(np.float32)
        ).unsqueeze(0).to(device)
        clip_batch = torch.from_numpy(
            clip_feat[start:end].astype(np.float32)
        ).unsqueeze(0).to(device)

        if method == "source_only":
            scores = adaptor.score_only(skel_batch, clip_batch)
        else:
            scores = adaptor.adapt_and_score(skel_batch, clip_batch)

        all_scores.append(scores.squeeze(0).cpu().numpy())

    return np.concatenate(all_scores)  # [N_snippets]


# ---------------------------------------------------------------------------
# Atomic write helpers (from src/evaluate.py pattern)
# ---------------------------------------------------------------------------


def _write_json_atomic(payload: dict, path: Path) -> None:
    """Atomic JSON dump: write to tempfile in same dir, fsync, os.replace."""
    fd, tmp = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(path))
    except Exception:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise


def _mark_done(run_dir: Path) -> None:
    """Atomic .done marker write (D-31)."""
    target = run_dir / ".done"
    fd, tmp = tempfile.mkstemp(prefix=".done.", suffix=".tmp", dir=str(run_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("eval_complete\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(target))
    except Exception:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise


# ---------------------------------------------------------------------------
# Main evaluation function
# ---------------------------------------------------------------------------


def run_tta_evaluation(
    source_run: Path,
    corruption_type: str,
    severity: int,
    method: str,
    lr: float,
    rho: float,
    output_dir: Path,
    feature_root: Path | None = None,
    backbone: str = "clip-vit-b-16",
):
    """Full TTA evaluation for one configuration.

    Args:
        source_run: Path to training run dir (contains config_snapshot.json + best_model.pth).
        corruption_type: One of gaussian_noise, jpeg_compression, brightness, motion_blur.
        severity: Corruption severity 1-5.
        method: One of source_only, tent, sar.
        lr: Learning rate for TTA adaptation.
        rho: SAM rho parameter (SAR only).
        output_dir: Directory for eval_metrics.json + eval_scores.npz + .done.
        feature_root: Root directory for corruption feature caches.
        backbone: Vision backbone key for feature subdirectory routing.
    """
    if feature_root is None:
        feature_root = Path("E:/features/ucf")

    # Determinism (D-12): with dropout disabled in configure_model the forward is
    # already deterministic; pin the RNG anyway so any residual stochasticity is
    # reproducible across re-runs.
    torch.manual_seed(0)
    np.random.seed(0)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()

    # 1. Load source model config + checkpoint
    cfg = load_snapshot_as_config(source_run / "config_snapshot.json")
    model = build_model(**cfg["model"]).to(device)
    best_path = source_run / "best_model.pth"
    state = load_checkpoint(best_path, device=device)
    state_dict = state.get("model", state) if isinstance(state, dict) else state
    model.load_state_dict(state_dict, strict=True)

    # 2. Configure model for TTA (freeze all except LN)
    source_state = deepcopy(model.state_dict())
    configure_model(model)
    params, param_names = collect_params(model)
    n_adapted_params = sum(p.numel() for p in params)

    # 3. Create adaptor based on method
    if method == "tent":
        optimizer = torch.optim.SGD(params, lr=lr)
        adaptor = TentAdaptor(model, optimizer, source_state)
    elif method == "sar":
        optimizer = SAM(params, torch.optim.SGD, rho=rho, lr=lr)
        adaptor = SarAdaptor(model, optimizer, source_state)
    else:
        # source_only: use _SourceOnlyAdaptor that has a no-op reset
        adaptor = _SourceOnlyAdaptor(model, source_state)

    # 4. Load test video list
    test_split = _PROJECT_ROOT / "data" / "splits" / "ucf_test.txt"
    video_ids = [line.strip() for line in test_split.read_text().splitlines()
                 if line.strip()]

    # 5. Per-video adaptation loop
    per_video_snippet_scores = {}
    n_skipped = 0
    for vid in video_ids:
        skel, clip = _load_test_video_features(
            vid, corruption_type, severity, feature_root, backbone=backbone
        )
        if skel is None:
            n_skipped += 1
            continue  # skip sub-64-frame videos or missing features
        scores = _adapt_one_video(adaptor, skel, clip, method, device)
        per_video_snippet_scores[vid] = scores

    # 6. Frame expansion + metrics (reuse Phase 4 infrastructure)
    # UCF: snippet_window=64, upsample_factor=10
    ann_path = _PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    annos = parse_annotations(ann_path)
    frames_map, labels_map, cats_map = {}, {}, {}
    for vid, scores in per_video_snippet_scores.items():
        n_frames = len(scores) * 64 * 10
        frames_map[vid] = snippet_to_frame(
            scores, n_frames, snippet_window=64, upsample_factor=10,
        )
        if vid in annos:
            labels_map[vid] = frame_labels(annos[vid], n_frames)
            cats_map[vid] = annos[vid].category
        else:
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
            cats_map[vid] = "Normal"

    metrics = compute_frame_metrics(frames_map, labels_map, cats_map)

    eval_duration_s = float(time.time() - t0)

    # 7. Write outputs (D-31 pattern: metrics -> scores -> .done last)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        **metrics,
        "method": method,
        "corruption_type": corruption_type,
        "severity": severity,
        "lr": lr,
        "rho": rho if method == "sar" else None,
        "backbone": backbone,
        "source_run": str(source_run.name),
        "n_adapted_params": n_adapted_params,
        "n_videos_evaluated": len(per_video_snippet_scores),
        "n_videos_skipped": n_skipped,
        "eval_duration_s": round(eval_duration_s, 3),
        "eval_timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    _write_json_atomic(payload, output_dir / "eval_metrics.json")
    np.savez_compressed(
        output_dir / "eval_scores.npz",
        **{k: v.astype(np.float32) for k, v in frames_map.items()},
    )
    _mark_done(output_dir)

    auc = metrics.get("auc", float("nan"))
    ap = metrics.get("ap", float("nan"))
    logger.info(
        "[evaluate_tta] %s %s sev=%d method=%s lr=%.1e => AUC=%.4f AP=%.4f",
        corruption_type, method, severity, method, lr, auc, ap,
    )


# ---------------------------------------------------------------------------
# Source-only adaptor (no optimizer needed, safe reset)
# ---------------------------------------------------------------------------


class _SourceOnlyAdaptor:
    """Minimal adaptor for source_only baseline: no optimizer, no adaptation.

    TentAdaptor.reset() calls self.optimizer.state = {} which crashes when
    optimizer is None. This wrapper provides a safe no-op reset and delegates
    scoring to model forward with no_grad.
    """

    def __init__(self, model, source_state):
        self.model = model
        self.source_state = source_state

    def reset(self):
        """Restore model to source state (per-video reset)."""
        self.model.load_state_dict(self.source_state, strict=False)

    def adapt_and_score(self, skel, clip):
        """Source-only has no adaptation; delegates to score_only."""
        return self.score_only(skel, clip)

    def score_only(self, skel, clip):
        """Forward without adaptation."""
        with torch.no_grad():
            return self.model(skel=skel, clip=clip).detach()


# ---------------------------------------------------------------------------
# CLI main
# ---------------------------------------------------------------------------


def main(argv=None) -> int:
    args = parse_args(argv)
    run_tta_evaluation(
        source_run=Path(args.source_run).resolve(),
        corruption_type=args.corruption,
        severity=args.severity,
        method=args.method,
        lr=args.lr,
        rho=args.rho,
        output_dir=Path(args.output_dir).resolve(),
        feature_root=Path(args.feature_root),
        backbone=args.backbone,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
