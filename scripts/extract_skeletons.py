"""
extract_skeletons.py — RTMPose skeleton extraction to PYSKL-compatible pickle format.

Runs in the ``vcc-skeleton`` conda environment (rtmlib + onnxruntime-gpu + opencv).

Usage:
    conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split train
    conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split train --limit 3
    conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset xd --split train --limit 10

Outputs per video:
  1. E:/skeletons/{dataset}/{video_id}.pkl  — PYSKL-compatible pickle
  2. E:/snippets/{dataset}/{video_id}_boundaries.json — snippet boundary JSON for CLIP alignment

PYSKL pickle format:
    {
        'keypoint':       ndarray [M=2, T, V=17, C=2]  float32  (pixel coords)
        'keypoint_score': ndarray [M=2, T, V=17]        float32
        'img_shape':      (H, W)   actual frame resolution
        'total_frames':   int      T
        'video_id':       str
    }

Snippet boundary JSON:
    {
        "video_id":            str
        "total_frames":        int
        "frames_per_snippet":  64
        "snippet_frame_ranges": [[start, end], ...]   non-overlapping 64-frame windows
        "n_snippets":          int
        "img_shape":           [H, W]
    }
"""

import argparse
import json
import logging
import os
import pathlib
import pickle
import re
import sys
import warnings

# Force unbuffered output so tqdm/logging display in real-time under `conda run`
# Must reconfigure streams since PYTHONUNBUFFERED only works if set before interpreter starts
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# ---------------------------------------------------------------------------
# cuDNN PATH fix (ISSUE 2 from CLAUDE.md)
# onnxruntime-gpu requires cudnn64_9.dll to be on PATH for CUDAExecutionProvider.
# cuDNN 9.x for CUDA 12 installs into v9.8/bin/12.8/ on Windows, not v9.8/bin/.
# Must be set BEFORE any import that triggers onnxruntime DLL loading.
# ---------------------------------------------------------------------------
_CUDNN_PATH = r"C:\Program Files\NVIDIA\CUDNN\v9.8\bin\12.8"
if _CUDNN_PATH not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _CUDNN_PATH + ";" + os.environ.get("PATH", "")

import cv2
import numpy as np
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

UCF_TRAIN_ROOT = pathlib.Path("E:/UCF_crime_dataset/Train")
UCF_TEST_ROOT = pathlib.Path("E:/UCF_crime_dataset/test")

XD_TRAIN_ROOT = pathlib.Path("E:/XD_Violence/train")
XD_TEST_ROOT = pathlib.Path("E:/XD_Violence/test/videos")

SKELETON_ROOT = pathlib.Path("E:/skeletons")
SNIPPET_ROOT = pathlib.Path("E:/snippets")

UCF_CATEGORIES = [
    "Abuse", "Arrest", "Arson", "Assault", "Burglary", "Explosion", "Fighting",
    "NormalVideos", "RoadAccidents", "Robbery", "Shooting", "Shoplifting",
    "Stealing", "Vandalism",
]

FRAMES_PER_SNIPPET = 64
CHUNK_SIZE = 500   # Process frames in 500-frame chunks to avoid RAM overflow (Pitfall 9)

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
# PreNormalize2D (per PYSKL source: pyskl/datasets/pipelines/pose_related.py:86-89)
# ---------------------------------------------------------------------------

def prenormalize2d(keypoint: np.ndarray, img_shape: tuple) -> np.ndarray:
    """
    Normalize pixel coordinates to [-1, 1] range using PYSKL PreNormalize2D logic.

    Args:
        keypoint: ndarray [..., 2] where [..., 0] = x (pixel), [..., 1] = y (pixel)
        img_shape: (H, W) actual frame resolution

    Returns:
        Normalized keypoint array of same shape (float32).
    """
    h, w = img_shape
    kp = keypoint.copy().astype(np.float32)
    kp[..., 0] = (kp[..., 0] - (w / 2)) / (w / 2)   # x: pixel -> [-1, 1]
    kp[..., 1] = (kp[..., 1] - (h / 2)) / (h / 2)   # y: pixel -> [-1, 1]
    return kp


# ---------------------------------------------------------------------------
# Snippet boundary computation
# ---------------------------------------------------------------------------

def compute_snippet_boundaries(n_frames: int, frames_per_snippet: int = FRAMES_PER_SNIPPET) -> list:
    """
    Compute non-overlapping snippet frame ranges.

    Returns list of [start_inclusive, end_exclusive] pairs.
    Trailing frames that don't fill a complete window are discarded.
    """
    boundaries = []
    for start in range(0, n_frames - frames_per_snippet + 1, frames_per_snippet):
        boundaries.append([start, start + frames_per_snippet])
    return boundaries


# ---------------------------------------------------------------------------
# UCF-Crime frame loading
# ---------------------------------------------------------------------------

def find_ucf_category(video_id: str) -> tuple:
    """
    Find the category directory that contains this video's PNGs.

    Returns (category, png_dir) or raises FileNotFoundError.
    """
    # Check both Train and test roots
    for root in [UCF_TRAIN_ROOT, UCF_TEST_ROOT]:
        for cat in UCF_CATEGORIES:
            cat_dir = root / cat
            if not cat_dir.exists():
                continue
            # Check if any PNG with this video_id exists
            test_png = list(cat_dir.glob(f"{re.escape(video_id)}_x264_*.png"))
            if test_png:
                return cat, cat_dir
    raise FileNotFoundError(f"No PNGs found for video_id={video_id} in UCF-Crime directories")


def load_ucf_frames(video_id: str) -> tuple:
    """
    Load all PNG frames for a UCF-Crime video.

    Returns (frames, img_shape) where:
        frames:     list of np.ndarray (H, W, 3) in BGR (cv2 default)
        img_shape:  (H, W) tuple from the first frame
    """
    cat, cat_dir = find_ucf_category(video_id)

    # Enumerate all PNGs matching this video_id prefix
    pattern = re.compile(rf"^{re.escape(video_id)}_x264_(\d+)\.png$")
    frame_files = []
    for png in cat_dir.iterdir():
        m = pattern.match(png.name)
        if m:
            frame_num = int(m.group(1))
            frame_files.append((frame_num, png))

    if not frame_files:
        raise FileNotFoundError(f"No PNG files found for {video_id} in {cat_dir}")

    # Sort NUMERICALLY (not lexicographically) — critical pitfall
    frame_files.sort(key=lambda x: x[0])

    # Load frames
    frames = []
    img_shape = None
    for _, png_path in frame_files:
        img = cv2.imread(str(png_path))
        if img is None:
            logger.warning(f"Failed to read frame: {png_path}")
            continue
        if img_shape is None:
            img_shape = (img.shape[0], img.shape[1])  # (H, W)
        frames.append(img)

    if not frames:
        raise ValueError(f"No valid frames loaded for {video_id}")

    return frames, img_shape


# ---------------------------------------------------------------------------
# XD-Violence frame loading
# ---------------------------------------------------------------------------

def load_xd_frames(video_id: str, split: str) -> tuple:
    """
    Load all frames from an XD-Violence mp4 file.

    Tries decord first, falls back to cv2.VideoCapture on error.

    Returns (frames, img_shape) where:
        frames:    list of np.ndarray (H, W, 3) in BGR
        img_shape: (H, W) tuple from the first frame
    """
    if split in ("train",):
        video_path = XD_TRAIN_ROOT / f"{video_id}.mp4"
    else:
        video_path = XD_TEST_ROOT / f"{video_id}.mp4"

    if not video_path.exists():
        raise FileNotFoundError(f"XD-Violence video not found: {video_path}")

    frames = []
    img_shape = None

    # Try decord first
    try:
        import decord
        decord.bridge.set_bridge("native")
        vr = decord.VideoReader(str(video_path), ctx=decord.cpu(0))
        n_frames = len(vr)
        # Load all frames
        all_frame_indices = list(range(n_frames))
        decoded = vr.get_batch(all_frame_indices).asnumpy()  # (T, H, W, 3) RGB
        for frame_rgb in decoded:
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            if img_shape is None:
                img_shape = (frame_bgr.shape[0], frame_bgr.shape[1])
            frames.append(frame_bgr)
    except Exception as e:
        logger.warning(f"decord failed for {video_id}: {e}. Falling back to cv2.")
        frames = []
        img_shape = None
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise IOError(f"cv2.VideoCapture failed to open: {video_path}")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if img_shape is None:
                img_shape = (frame.shape[0], frame.shape[1])
            frames.append(frame)
        cap.release()

    if not frames:
        raise ValueError(f"No frames loaded from {video_path}")

    return frames, img_shape


# ---------------------------------------------------------------------------
# RTMPose inference
# ---------------------------------------------------------------------------

_wholebody_model = None


def get_wholebody_model():
    """Lazy-initialize the Wholebody model (singleton)."""
    global _wholebody_model
    if _wholebody_model is None:
        from rtmlib import Wholebody
        logger.info("Initializing Wholebody model (mode=balanced, backend=onnxruntime, device=cuda)...")
        _wholebody_model = Wholebody(
            mode="balanced",    # RTMWholebody-DW-X-L: 133 keypoints (COCO-17 body + face + hands)
            backend="onnxruntime",
            device="cuda",
        )
        logger.info("Wholebody model initialized.")
    return _wholebody_model


def process_frames_to_keypoints(frames: list, img_shape: tuple) -> tuple:
    """
    Run RTMPose inference on a list of BGR frames.

    Returns:
        keypoint:       ndarray [M=2, T, V=17, C=2]  float32  (pixel coords)
        keypoint_score: ndarray [M=2, T, V=17]        float32
    """
    model = get_wholebody_model()
    T = len(frames)

    # Initialize output arrays
    keypoint = np.zeros((2, T, 17, 2), dtype=np.float32)
    keypoint_score = np.zeros((2, T, 17), dtype=np.float32)

    # Process in chunks to avoid RAM overflow (Pitfall 9 from research)
    for chunk_start in range(0, T, CHUNK_SIZE):
        chunk_end = min(chunk_start + CHUNK_SIZE, T)
        for t in range(chunk_start, chunk_end):
            frame = frames[t]
            try:
                kps, scores = model(frame)
                # kps:    [N_persons, 133, 2]  (wholebody has 133 keypoints)
                # scores: [N_persons, 133]
            except Exception as e:
                logger.warning(f"RTMPose inference failed at frame {t}: {e}. Using zeros.")
                continue

            if kps is None or len(kps) == 0:
                # 0 detections: both person slots remain all-zero (D-07)
                continue

            # Take only first 17 COCO-17 body keypoints
            kps = kps[:, :17, :]        # [N, 17, 2]
            scores_17 = scores[:, :17]  # [N, 17]

            n_persons = kps.shape[0]

            if n_persons == 1:
                # 1 detection: person 0 = detected, person 1 = all-zero (D-08)
                keypoint[0, t] = kps[0]
                keypoint_score[0, t] = scores_17[0]
            elif n_persons >= 2:
                # 2+ detections: select top-2 by mean keypoint confidence (D-05)
                mean_conf = scores_17.mean(axis=1)          # [N]
                top2_idx = np.argsort(mean_conf)[-2:][::-1]  # descending order
                keypoint[0, t] = kps[top2_idx[0]]
                keypoint_score[0, t] = scores_17[top2_idx[0]]
                keypoint[1, t] = kps[top2_idx[1]]
                keypoint_score[1, t] = scores_17[top2_idx[1]]

    return keypoint, keypoint_score


# ---------------------------------------------------------------------------
# Per-video processing
# ---------------------------------------------------------------------------

def process_video(video_id: str, dataset: str, split: str) -> dict:
    """
    Extract skeleton keypoints from a single video.

    Returns a dict with all data needed to write pickle + boundary JSON.
    Raises on unrecoverable error (caller handles try/except).
    """
    # Step 1: Load frames
    if dataset == "ucf":
        frames, img_shape = load_ucf_frames(video_id)
    else:
        frames, img_shape = load_xd_frames(video_id, split)

    T = len(frames)

    # Step 2: RTMPose inference
    keypoint, keypoint_score = process_frames_to_keypoints(frames, img_shape)

    # Step 3: Coordinate normalization assertion (DATA-04, C1 pitfall)
    normalized_kp = prenormalize2d(keypoint, img_shape)
    max_abs = np.abs(normalized_kp).max()
    if max_abs > 2.0:
        logger.warning(
            f"[{video_id}] PreNormalize2D: max abs coord {max_abs:.4f} exceeds 2.0 tolerance. "
            f"img_shape={img_shape}. Check coordinate system."
        )

    # Step 4: Compute snippet boundaries
    boundaries = compute_snippet_boundaries(T, FRAMES_PER_SNIPPET)

    return {
        "keypoint": keypoint,              # [2, T, 17, 2] float32 — pixel coords
        "keypoint_score": keypoint_score,  # [2, T, 17] float32
        "img_shape": img_shape,            # (H, W)
        "total_frames": T,
        "video_id": video_id,
        "snippet_boundaries": boundaries,  # [[start, end], ...]
    }


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------

def write_outputs(data: dict, dataset: str) -> None:
    """
    Write PYSKL pickle and snippet boundary JSON for one video.
    """
    video_id = data["video_id"]
    skeleton_dir = SKELETON_ROOT / dataset
    snippet_dir = SNIPPET_ROOT / dataset
    skeleton_dir.mkdir(parents=True, exist_ok=True)
    snippet_dir.mkdir(parents=True, exist_ok=True)

    # Write PYSKL-compatible pickle
    pickle_path = skeleton_dir / f"{video_id}.pkl"
    pickle_data = {
        "keypoint": data["keypoint"],
        "keypoint_score": data["keypoint_score"],
        "img_shape": data["img_shape"],
        "total_frames": data["total_frames"],
        "video_id": video_id,
    }
    with open(pickle_path, "wb") as f:
        pickle.dump(pickle_data, f)

    # Write snippet boundary JSON
    boundaries = data["snippet_boundaries"]
    boundary_path = snippet_dir / f"{video_id}_boundaries.json"
    boundary_data = {
        "video_id": video_id,
        "total_frames": data["total_frames"],
        "frames_per_snippet": FRAMES_PER_SNIPPET,
        "snippet_frame_ranges": boundaries,
        "n_snippets": len(boundaries),
        "img_shape": list(data["img_shape"]),  # [H, W] for JSON serialization
    }
    with open(boundary_path, "w") as f:
        json.dump(boundary_data, f, indent=2)


# ---------------------------------------------------------------------------
# Main extraction loop
# ---------------------------------------------------------------------------

def run_extraction(dataset: str, split: str, limit: int = None, workers: int = 1) -> None:
    """
    Main extraction loop for one dataset/split combination.
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

    # Setup output directories
    (SKELETON_ROOT / dataset).mkdir(parents=True, exist_ok=True)
    (SNIPPET_ROOT / dataset).mkdir(parents=True, exist_ok=True)

    # Error log path
    error_log_path = SKELETON_ROOT / dataset / "errors.log"

    skipped = 0
    processed = 0
    failed = 0

    with tqdm(total=len(video_ids), desc=f"{dataset}/{split}", unit="video") as pbar:
        for video_id in video_ids:
            pbar.set_description(f"{dataset}/{split}: {video_id[:40]}")

            # Resume logic (D-14): skip if both outputs already exist
            pickle_path = SKELETON_ROOT / dataset / f"{video_id}.pkl"
            boundary_path = SNIPPET_ROOT / dataset / f"{video_id}_boundaries.json"
            if pickle_path.exists() and boundary_path.exists():
                skipped += 1
                pbar.update(1)
                continue

            # Per-video error handling (D-15)
            try:
                data = process_video(video_id, dataset, split)
                write_outputs(data, dataset)
                processed += 1
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

def validate_sample_outputs(dataset: str, video_ids: list) -> None:
    """
    Validate the output for a small set of videos after extraction.

    Checks:
        - Pickle exists and has correct keypoint shape [2, T, 17, 2]
        - Boundary JSON exists and has n_snippets == floor(T / 64)
        - Normalized coordinates are within [-2, 2]
    """
    logger.info("Validating sample outputs...")
    all_ok = True

    for video_id in video_ids:
        pkl_path = SKELETON_ROOT / dataset / f"{video_id}.pkl"
        json_path = SNIPPET_ROOT / dataset / f"{video_id}_boundaries.json"

        if not pkl_path.exists():
            logger.error(f"VALIDATE FAIL: Pickle missing for {video_id}")
            all_ok = False
            continue
        if not json_path.exists():
            logger.error(f"VALIDATE FAIL: Boundary JSON missing for {video_id}")
            all_ok = False
            continue

        with open(pkl_path, "rb") as f:
            pkl = pickle.load(f)
        with open(json_path) as f:
            boundaries = json.load(f)

        kp = pkl["keypoint"]
        T = pkl["total_frames"]
        img_shape = pkl["img_shape"]

        # Shape check
        if kp.shape != (2, T, 17, 2):
            logger.error(f"VALIDATE FAIL: {video_id} keypoint shape {kp.shape} != (2, {T}, 17, 2)")
            all_ok = False
        else:
            logger.info(f"  OK shape: {video_id} -> {kp.shape}")

        # Snippet count check
        expected_n = len(compute_snippet_boundaries(T, FRAMES_PER_SNIPPET))
        actual_n = boundaries["n_snippets"]
        if actual_n != expected_n:
            logger.error(f"VALIDATE FAIL: {video_id} n_snippets={actual_n}, expected {expected_n}")
            all_ok = False
        else:
            logger.info(f"  OK snippets: {video_id} -> {actual_n} snippets (T={T})")

        # Coordinate normalization check
        normalized = prenormalize2d(kp, img_shape)
        max_abs = np.abs(normalized).max()
        if max_abs > 2.0:
            logger.warning(
                f"  WARN: {video_id} max coord {max_abs:.4f} > 2.0 (borderline joint at edge)"
            )
        else:
            logger.info(f"  OK coords: {video_id} -> max abs {max_abs:.4f} <= 2.0")

    if all_ok:
        logger.info("Validation PASSED: all checked videos OK.")
    else:
        logger.warning("Validation FAILED: see errors above.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract RTMPose skeletons to PYSKL-compatible pickle format."
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
        help="Process only the first N videos (for testing).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers (default 1; skeleton extraction is GPU-bound).",
    )
    args = parser.parse_args()

    if args.workers != 1:
        logger.warning(
            f"--workers={args.workers} requested but GPU-bound extraction runs sequentially. "
            "Using 1 worker."
        )

    run_extraction(args.dataset, args.split, limit=args.limit, workers=1)

    # Run validation on sample videos if --limit was used (smoke test)
    if args.limit is not None:
        split_file = SPLITS_DIR / f"{args.dataset}_{args.split}.txt"
        with open(split_file) as f:
            video_ids = [line.strip() for line in f if line.strip()]
        sample_ids = video_ids[: min(args.limit, len(video_ids))]
        validate_sample_outputs(args.dataset, sample_ids)


if __name__ == "__main__":
    main()
