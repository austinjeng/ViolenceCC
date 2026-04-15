"""
extract_ctrgcn.py — CTR-GCN 4-stream feature extraction from skeleton pickles.

Runs in the ``vcc-ctrgcn`` conda environment (PyTorch 1.12.1 + mmcv-full 1.7.0 + PYSKL).

Usage:
    conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset ucf --split train
    conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset ucf --split train --limit 3
    conda run -n vcc-ctrgcn python scripts/extract_ctrgcn.py --dataset xd --split train

Reads:
    E:/skeletons/{dataset}/{video_id}.pkl    — PYSKL-compatible pickle (pixel coords)
    E:/snippets/{dataset}/{video_id}_boundaries.json — snippet boundaries from Plan 01

Outputs:
    E:/features/{dataset}/skeleton/{video_id}.npy  — float32 [N_snippets, 256]

Pipeline:
    1. Load all 4 CTR-GCN stream models (j, b, jm, bm) from vcc-ctrgcn env.
    2. For each video: load pickle + boundary JSON, compute 4 stream inputs per snippet,
       run forward pass through each stream model, compute weighted average,
       stack to [N_snippets, 256] and save as .npy.

Stream weights (per D-01, DATA-05):
    j:1.0, b:1.0, jm:0.5, bm:0.5  -> weighted average: / 3.0

Preprocessing (CRITICAL per DATA-04, C1 pitfall):
    PreNormalize2D must be applied: pixel -> [-1, 1] using img_shape from pickle.

COCO-17 bone pairs (from PYSKL GenSkeFeat source):
    bone[v1] = kp[v1] - kp[v2]  where (v1, v2) are COCO_BONE_PAIRS[v1]
"""

import argparse
import json
import logging
import pathlib
import pickle
import sys

# Force unbuffered output so tqdm/logging display in real-time under `conda run`
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import numpy as np
import torch
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

SKELETON_ROOT = pathlib.Path("E:/skeletons")
SNIPPET_ROOT = pathlib.Path("E:/snippets")
FEATURE_ROOT = pathlib.Path("E:/features")

# CTR-GCN weights and configs (downloaded in Phase 1 Plan 03)
WEIGHT_DIR = pathlib.Path("D:/ViolenceCC/data/weights/ctrgcn")
CONFIG_DIR = pathlib.Path("D:/libs/pyskl/configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet")

# 4 streams: name -> (config_file, weight_file, stream_weight)
STREAMS = {
    "j":  {"config": "j.py",  "weight": "j.pth",  "w": 1.0},
    "b":  {"config": "b.py",  "weight": "b.pth",  "w": 1.0},
    "jm": {"config": "jm.py", "weight": "jm.pth", "w": 0.5},
    "bm": {"config": "bm.py", "weight": "bm.pth", "w": 0.5},
}
WEIGHT_SUM = 1.0 + 1.0 + 0.5 + 0.5  # = 3.0

# COCO-17 bone pairs (child, parent) — from PYSKL GenSkeFeat source
# bone[child] = kp[child] - kp[parent].  For joint 0: (0, 0) -> zero vector.
COCO_BONE_PAIRS = (
    (0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 0), (6, 0),
    (7, 5), (8, 6), (9, 7), (10, 8), (11, 0), (12, 0),
    (13, 11), (14, 12), (15, 13), (16, 14)
)

FRAMES_PER_SNIPPET = 64

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_ctrgcn_stream(stream_name: str, device: str = "cuda") -> torch.nn.Module:
    """
    Load a single CTR-GCN stream model (j, b, jm, or bm).

    Uses the proven pattern from tests/test_ctrgcn_smoke.py:
        - Config via mmcv.Config.fromfile
        - Model via pyskl.models.build_model
        - Checkpoint: plain OrderedDict (no 'state_dict' wrapper in PYSKL checkpoints)
        - strict=False to ignore cls_head keys not used in feature extraction
    """
    from mmcv import Config
    from pyskl.models import build_model

    stream_cfg = STREAMS[stream_name]
    cfg_path = str(CONFIG_DIR / stream_cfg["config"])
    weight_path = str(WEIGHT_DIR / stream_cfg["weight"])

    logger.info(f"Loading CTR-GCN stream '{stream_name}' from {weight_path}")
    cfg = Config.fromfile(cfg_path)
    model = build_model(cfg.model)

    checkpoint = torch.load(weight_path, map_location="cpu")
    # PYSKL checkpoints are plain OrderedDicts — no 'state_dict' wrapper key.
    # Keys prefixed with 'backbone.' and 'cls_head.'; strict=False ignores cls_head.
    state_dict = (
        checkpoint
        if isinstance(checkpoint, dict) and "backbone" in str(list(checkpoint.keys())[:1])
        else checkpoint.get("state_dict", checkpoint)
    )
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    model.to(device)
    return model


def load_all_stream_models(device: str = "cuda") -> dict:
    """Load all 4 CTR-GCN stream models onto the specified device."""
    models = {}
    for stream_name in STREAMS:
        models[stream_name] = load_ctrgcn_stream(stream_name, device=device)
    logger.info(f"All 4 CTR-GCN stream models loaded on {device}.")
    return models


# ---------------------------------------------------------------------------
# PreNormalize2D
# ---------------------------------------------------------------------------

def prenormalize2d(kp: np.ndarray, img_shape: tuple) -> np.ndarray:
    """
    Apply PYSKL PreNormalize2D: pixel coords -> [-1, 1].

    Formula (from pyskl/datasets/pipelines/pose_related.py lines 88-89):
        x_norm = (x_pixel - (w / 2)) / (w / 2)
        y_norm = (y_pixel - (h / 2)) / (h / 2)

    Args:
        kp:        ndarray [..., 2] where [..., 0] = x, [..., 1] = y (pixel coords)
        img_shape: (H, W) from the pickle

    Returns:
        Normalized array of same shape (float32).
    """
    h, w = img_shape
    kp_norm = kp.copy().astype(np.float32)
    kp_norm[..., 0] = (kp_norm[..., 0] - (w / 2)) / (w / 2)
    kp_norm[..., 1] = (kp_norm[..., 1] - (h / 2)) / (h / 2)
    return kp_norm


# ---------------------------------------------------------------------------
# 4-stream input preparation per snippet
# ---------------------------------------------------------------------------

def prepare_stream_inputs(kp_snippet: np.ndarray, sc_snippet: np.ndarray) -> dict:
    """
    Prepare the 4 stream inputs (j, b, jm, bm) for a single snippet.

    Args:
        kp_snippet: [M=2, T=64, V=17, C=2] float32 — normalized pixel coords
        sc_snippet: [M=2, T=64, V=17]       float32 — confidence scores

    Returns:
        dict with keys 'j', 'b', 'jm', 'bm', each [M=2, T=64, V=17, C=3] float32
    """
    # --- Joint stream (j): [x, y, conf] ---
    x_j = np.concatenate([kp_snippet, sc_snippet[..., None]], axis=-1)  # [2, 64, 17, 3]

    # --- Bone stream (b): bone vector = child - parent, with same confidence ---
    bone = np.zeros_like(kp_snippet)  # [2, 64, 17, 2]
    for child_idx, (child, parent) in enumerate(COCO_BONE_PAIRS):
        # bone[child] = kp[child] - kp[parent]
        # For joint 0: (0, 0) -> kp[0] - kp[0] = zero vector (by convention)
        bone[:, :, child_idx, :] = kp_snippet[:, :, child, :] - kp_snippet[:, :, parent, :]
    bone_score = sc_snippet.copy()
    x_b = np.concatenate([bone, bone_score[..., None]], axis=-1)  # [2, 64, 17, 3]

    # --- Joint Motion stream (jm): temporal difference of joint ---
    jm = np.zeros_like(kp_snippet)  # [2, 64, 17, 2]
    jm[:, 1:, :, :] = kp_snippet[:, 1:, :, :] - kp_snippet[:, :-1, :, :]
    jm_score = sc_snippet.copy()
    x_jm = np.concatenate([jm, jm_score[..., None]], axis=-1)  # [2, 64, 17, 3]

    # --- Bone Motion stream (bm): temporal difference of bone ---
    bm = np.zeros_like(bone)  # [2, 64, 17, 2]
    bm[:, 1:, :, :] = bone[:, 1:, :, :] - bone[:, :-1, :, :]
    bm_score = sc_snippet.copy()
    x_bm = np.concatenate([bm, bm_score[..., None]], axis=-1)  # [2, 64, 17, 3]

    return {"j": x_j, "b": x_b, "jm": x_jm, "bm": x_bm}


# ---------------------------------------------------------------------------
# Forward pass helper
# ---------------------------------------------------------------------------

def extract_stream_feature(
    model: torch.nn.Module, x_np: np.ndarray, device: str = "cuda",
    keep_persons: bool = False,
) -> torch.Tensor:
    """
    Run a single CTR-GCN stream backbone forward pass and pool to [1, 256]
    (M-pool default) or [M=2, 256] (Phase 4 D-21 per-person).

    Args:
        model:         Loaded CTR-GCN model in eval mode.
        x_np:          [M=2, T=64, V=17, C=3] float32 numpy array.
        device:        'cuda' or 'cpu'.
        keep_persons:  D-21: when True, emit [M, 256] by pooling ONLY T'/V'
                       (preserving per-person features). Default False =
                       legacy M-pool producing [1, 256].

    Returns:
        [1, 256] float32 tensor (on CPU) when keep_persons=False (default).
        [M=2, 256] float32 tensor (on CPU) when keep_persons=True.

    CTR-GCN input shape: (N, M, T, V, C) — per test_ctrgcn_smoke.py notes.
    Backbone output: (N, M, C_out, T', V'). Default: mean over M, T', V' -> (N, 256).
    keep_persons: mean over T', V' only -> (M, 256) after squeeze(0).
    """
    # Add batch dim: [M, T, V, C] -> [1, M, T, V, C]
    x = torch.from_numpy(x_np).unsqueeze(0).float().to(device)
    with torch.no_grad():
        out = model.backbone(x)   # [1, M, 256, T', V']
        if keep_persons:
            # D-21: preserve M dim; pool only spatial (T', V').
            feat = out.mean(dim=[3, 4]).squeeze(0)  # [M=2, 256]
        else:
            feat = out.mean(dim=[1, 3, 4])          # [1, 256]   (legacy default)
    return feat.cpu()


# ---------------------------------------------------------------------------
# Per-video feature extraction
# ---------------------------------------------------------------------------

def extract_video_features(
    video_id: str,
    pickle_path: pathlib.Path,
    boundary_path: pathlib.Path,
    models: dict,
    device: str = "cuda",
    keep_persons: bool = False,
) -> np.ndarray:
    """
    Extract 256-d CTR-GCN features for all snippets of one video.

    Returns:
        ndarray [N_snippets, 256] float32 when keep_persons=False (default).
        ndarray [N_snippets, 2, 256] float32 when keep_persons=True (D-21).

    Raises on unrecoverable errors (caller handles try/except).
    """
    # Load skeleton pickle
    with open(pickle_path, "rb") as f:
        pkl = pickle.load(f)

    keypoint = pkl["keypoint"]        # [2, T, 17, 2] float32 — pixel coords
    keypoint_score = pkl["keypoint_score"]  # [2, T, 17] float32
    img_shape = pkl["img_shape"]      # (H, W)

    # Load snippet boundaries
    with open(boundary_path) as f:
        boundaries = json.load(f)

    snippet_ranges = boundaries["snippet_frame_ranges"]   # [[start, end], ...]
    n_snippets = boundaries["n_snippets"]

    if n_snippets == 0:
        raise ValueError(f"No snippets defined for {video_id} (video too short < 64 frames?)")

    # Apply PreNormalize2D once for the entire video
    kp_normalized = prenormalize2d(keypoint, img_shape)  # [2, T, 17, 2] normalized

    # Assertion: normalized coords should be within [-2, 2] tolerance (C1 pitfall guard)
    max_abs = float(np.abs(kp_normalized).max())
    if max_abs > 2.0:
        logger.warning(
            f"[{video_id}] PreNormalize2D: max abs coord {max_abs:.4f} > 2.0. "
            f"img_shape={img_shape}. Proceeding anyway."
        )

    snippet_feats = []
    for start, end in snippet_ranges:
        # Slice snippet
        kp_snip = kp_normalized[:, start:end, :, :]   # [2, 64, 17, 2]
        sc_snip = keypoint_score[:, start:end, :]      # [2, 64, 17]

        # Prepare 4 stream inputs
        stream_inputs = prepare_stream_inputs(kp_snip, sc_snip)

        # Forward pass through each stream
        feat_j  = extract_stream_feature(models["j"],  stream_inputs["j"],  device, keep_persons=keep_persons)
        feat_b  = extract_stream_feature(models["b"],  stream_inputs["b"],  device, keep_persons=keep_persons)
        feat_jm = extract_stream_feature(models["jm"], stream_inputs["jm"], device, keep_persons=keep_persons)
        feat_bm = extract_stream_feature(models["bm"], stream_inputs["bm"], device, keep_persons=keep_persons)

        # Weighted average: (1.0*j + 1.0*b + 0.5*jm + 0.5*bm) / 3.0  (DATA-05, D-01)
        # Shape: [1, 256] in legacy mode; [M=2, 256] when keep_persons=True.
        feat = (1.0 * feat_j + 1.0 * feat_b + 0.5 * feat_jm + 0.5 * feat_bm) / 3.0
        snippet_feats.append(feat)

    if keep_persons:
        # Each feat is [M=2, 256]; stack to [N_snippets, 2, 256] (D-21).
        all_feats = torch.stack(snippet_feats, dim=0)
    else:
        # Each feat is [1, 256]; concat to [N_snippets, 256] (legacy default).
        all_feats = torch.cat(snippet_feats, dim=0)
    return all_feats.numpy().astype(np.float32)


# ---------------------------------------------------------------------------
# Main extraction loop
# ---------------------------------------------------------------------------

def run_extraction(
    dataset: str,
    split: str,
    limit: int = None,
    device: str = "cuda",
    keep_persons: bool = False,
) -> None:
    """
    Main loop: extract CTR-GCN features for all videos in a dataset split.

    Args:
        dataset, split, limit, device: see argparse below.
        keep_persons: Phase 4 D-21 — emit [N, 2, 256] per-person tensor to
                      <FEATURE_ROOT>/<dataset>/skeleton_2person/ instead of
                      the legacy [N, 256] M-pool to skeleton/.
    """
    # Read video IDs from split file
    split_file = SPLITS_DIR / f"{dataset}_{split}.txt"
    if not split_file.exists():
        raise FileNotFoundError(
            f"Split file not found: {split_file}\n"
            f"Run scripts/create_splits.py first."
        )
    with open(split_file) as f:
        video_ids = [line.strip() for line in f if line.strip()]

    if limit is not None:
        video_ids = video_ids[:limit]
        logger.info(f"Limiting to first {limit} videos (--limit flag).")

    logger.info(f"Processing {len(video_ids)} videos from {dataset}/{split}.")

    # Setup output directories — D-24 sibling dir layout when --keep-persons
    out_subdir = "skeleton_2person" if keep_persons else "skeleton"
    output_dir = FEATURE_ROOT / dataset / out_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    if keep_persons:
        logger.info("D-21 mode: emitting [N, 2, 256] per-person tensors.")

    # Error log
    error_log_path = output_dir / "errors.log"

    # Load all 4 CTR-GCN stream models once at startup
    models = load_all_stream_models(device=device)

    skipped = 0
    processed = 0
    failed = 0

    with tqdm(total=len(video_ids), desc=f"ctrgcn/{dataset}/{split}", unit="video") as pbar:
        for video_id in video_ids:
            pbar.set_description(f"ctrgcn/{dataset}: {video_id[:40]}")

            # Skip-if-exists resume logic (D-14) — validate file is non-trivial
            output_path = output_dir / f"{video_id}.npy"
            if output_path.exists() and output_path.stat().st_size > 128:
                skipped += 1
                pbar.update(1)
                continue

            # Input paths
            pickle_path = SKELETON_ROOT / dataset / f"{video_id}.pkl"
            boundary_path = SNIPPET_ROOT / dataset / f"{video_id}_boundaries.json"

            # Missing input files (D-15): log and skip
            if not pickle_path.exists():
                msg = f"{video_id}\tFileNotFoundError: pickle missing at {pickle_path}"
                logger.error(f"FAILED: {msg}")
                with open(error_log_path, "a") as ef:
                    ef.write(msg + "\n")
                failed += 1
                pbar.update(1)
                continue

            if not boundary_path.exists():
                msg = f"{video_id}\tFileNotFoundError: boundary JSON missing at {boundary_path}"
                logger.error(f"FAILED: {msg}")
                with open(error_log_path, "a") as ef:
                    ef.write(msg + "\n")
                failed += 1
                pbar.update(1)
                continue

            # Per-video error handling (D-15)
            try:
                feats = extract_video_features(
                    video_id, pickle_path, boundary_path, models,
                    device=device, keep_persons=keep_persons,
                )
                # Atomic write: tmp then rename.
                # Name tmp as "{id}.tmp.npy" (not "{id}.npy.tmp") because np.save
                # auto-appends ".npy" to paths that don't already end in ".npy",
                # which would produce "{id}.npy.tmp.npy" and break the rename.
                tmp_path = output_dir / f"{video_id}.tmp.npy"
                np.save(str(tmp_path), feats)
                tmp_path.replace(output_path)

                # Validation: check shape and dtype per keep_persons mode.
                if keep_persons:
                    assert feats.ndim == 3, f"Expected 3D array, got {feats.ndim}D"
                    assert feats.shape[1] == 2 and feats.shape[2] == 256, (
                        f"Expected [N, 2, 256], got {feats.shape} for {video_id}"
                    )
                else:
                    assert feats.ndim == 2, f"Expected 2D array, got {feats.ndim}D"
                    assert feats.shape[1] == 256, f"Expected 256-d, got {feats.shape[1]}"
                assert feats.dtype == np.float32, f"Expected float32, got {feats.dtype}"
                assert not np.any(np.isnan(feats)), "NaN detected in output features"
                assert not np.any(np.isinf(feats)), "Inf detected in output features"

                processed += 1
                logger.debug(f"Saved: {output_path} shape={feats.shape}")
            except Exception as exc:
                failed += 1
                error_msg = f"{video_id}\t{type(exc).__name__}: {exc}"
                logger.error(f"FAILED: {error_msg}")
                with open(error_log_path, "a") as ef:
                    ef.write(error_msg + "\n")

            pbar.update(1)

    logger.info(
        f"Done. Processed: {processed}, Skipped (exists): {skipped}, Failed: {failed}"
    )
    if failed > 0:
        logger.warning(f"See error log: {error_log_path}")


# ---------------------------------------------------------------------------
# Post-run validation
# ---------------------------------------------------------------------------

def validate_sample_outputs(dataset: str, video_ids: list, keep_persons: bool = False) -> None:
    """
    Validate the output .npy files for a small set of videos.

    Checks:
        - .npy file exists
        - Shape [N_snippets, 256] (legacy) or [N_snippets, 2, 256] (keep_persons)
        - N > 0
        - dtype float32
        - No NaN or Inf values
        - N_snippets matches the boundary JSON (alignment sanity)
    """
    logger.info("Validating sample outputs...")
    all_ok = True
    subdir = "skeleton_2person" if keep_persons else "skeleton"
    output_dir = FEATURE_ROOT / dataset / subdir

    for video_id in video_ids:
        npy_path = output_dir / f"{video_id}.npy"
        boundary_path = SNIPPET_ROOT / dataset / f"{video_id}_boundaries.json"

        if not npy_path.exists():
            logger.error(f"VALIDATE FAIL: .npy missing for {video_id}")
            all_ok = False
            continue

        feats = np.load(str(npy_path))

        # Shape check — branches on keep_persons mode.
        if keep_persons:
            shape_ok = (
                feats.ndim == 3
                and feats.shape[1] == 2
                and feats.shape[2] == 256
            )
            expected_label = "[N, 2, 256]"
        else:
            shape_ok = feats.ndim == 2 and feats.shape[1] == 256
            expected_label = "[N, 256]"

        if not shape_ok:
            logger.error(
                f"VALIDATE FAIL: {video_id} shape {feats.shape} (expected {expected_label})"
            )
            all_ok = False
        elif feats.shape[0] == 0:
            logger.error(f"VALIDATE FAIL: {video_id} has 0 snippets")
            all_ok = False
        else:
            logger.info(f"  OK shape: {video_id} -> {feats.shape} float32")

        # Dtype check
        if feats.dtype != np.float32:
            logger.error(f"VALIDATE FAIL: {video_id} dtype {feats.dtype} != float32")
            all_ok = False

        # NaN/Inf check
        if np.any(np.isnan(feats)):
            logger.error(f"VALIDATE FAIL: {video_id} contains NaN")
            all_ok = False
        if np.any(np.isinf(feats)):
            logger.error(f"VALIDATE FAIL: {video_id} contains Inf")
            all_ok = False

        # Alignment check: N_snippets matches boundary JSON
        if boundary_path.exists():
            with open(boundary_path) as f:
                boundaries = json.load(f)
            expected_n = boundaries["n_snippets"]
            actual_n = feats.shape[0]
            if actual_n != expected_n:
                logger.error(
                    f"VALIDATE FAIL: {video_id} n_snippets={actual_n}, "
                    f"expected {expected_n} from boundary JSON"
                )
                all_ok = False
            else:
                logger.info(f"  OK snippets: {video_id} -> {actual_n} == boundary JSON")

    if all_ok:
        logger.info("Validation PASSED: all checked videos OK.")
    else:
        logger.warning("Validation FAILED: see errors above.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CTR-GCN 4-stream feature extraction from skeleton pickles."
    )
    parser.add_argument(
        "--dataset",
        choices=["ucf", "xd"],
        required=True,
        help="Dataset to process: ucf (UCF-Crime) or xd (XD-Violence).",
    )
    parser.add_argument(
        "--split",
        choices=["train", "val", "test"],
        required=True,
        help="Which split to process (reads from data/splits/{dataset}_{split}.txt).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N videos (for testing / smoke run).",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Torch device: 'cuda' or 'cpu' (default: cuda).",
    )
    parser.add_argument(
        "--keep-persons",
        action="store_true",
        help=(
            "D-21: emit [N, 2, 256] per-person tensor instead of M-pooled "
            "[N, 256]. Output goes to <FEATURE_ROOT>/<dataset>/skeleton_2person/ "
            "instead of <FEATURE_ROOT>/<dataset>/skeleton/."
        ),
    )
    args = parser.parse_args()

    run_extraction(
        args.dataset,
        args.split,
        limit=args.limit,
        device=args.device,
        keep_persons=args.keep_persons,
    )

    # Run validation on sample videos if --limit was used (smoke test)
    if args.limit is not None:
        split_file = SPLITS_DIR / f"{args.dataset}_{args.split}.txt"
        with open(split_file) as f:
            video_ids_all = [line.strip() for line in f if line.strip()]
        sample_ids = video_ids_all[: min(args.limit, len(video_ids_all))]
        validate_sample_outputs(args.dataset, sample_ids, keep_persons=args.keep_persons)


if __name__ == "__main__":
    main()
