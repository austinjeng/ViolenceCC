"""
extract_clip.py — Vision backbone feature extraction from video frames.

Supports multiple vision backbones via the ``--backbone`` flag:

- **clip-vit-b-16** (default): CLIP ViT-B/16, 512-d per frame, 1024-d mean+max pooled.
- **siglip2-base**: SigLIP2 ViT-B/16-256, 768-d per frame,
  1536-d mean+max pooled.

Runs in the ``vcc-main`` conda environment (PyTorch 2.6.0 + open-clip-torch 3.3.0).

Usage:
    conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split train
    conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split train --limit 3
    conda run -n vcc-main python scripts/extract_clip.py --dataset xd --split train --batch-size 64
    conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split train --backbone siglip2-base --batch-size 16

Reads:
    E:/snippets/{dataset}/{video_id}_boundaries.json  — snippet boundaries from Plan 01
    UCF-Crime: E:/UCF_crime_dataset/{Train|test}/{category}/{video_id}_x264_{N}.png
    XD-Violence: E:/XD_Violence/train/{video_id}.mp4 or E:/XD_Violence/test/videos/{video_id}.mp4

Outputs:
    E:/features/{dataset}/{subdir}/{video_id}.npy  — float32 [N_snippets, D]
    subdir and D depend on --backbone and --pool:
      clip-vit-b-16 + mean_max -> clip/, D=1024
      clip-vit-b-16 + mean     -> clip_mean/, D=512
      siglip2-base + mean_max -> siglip2/, D=1536
      siglip2-base + mean     -> siglip2_mean/, D=768

Pipeline:
    1. Load vision model (selected via --backbone) once at startup.
    2. Read snippet boundaries from the SAME JSON as CTR-GCN script (alignment by construction).
    3. For each snippet [start, end): sample frames at ~1 FPS, extract embeddings.
    4. Apply mean+max pooling: concatenate mean and max -> [embed_dim*2] per snippet.
    5. Stack snippets -> [N_snippets, D] and save as float32 .npy.

NOTE: Output dimension depends on backbone. The projection to shared_dim is a LEARNED
      component in Phase 3's CLIP branch. Caching at full dimension avoids double-projection
      pitfall (Pitfall 5).

CLIP 1-FPS sampling within each snippet:
    UCF-Crime PNGs: every 10th original video frame -> ~3 FPS equivalent.
    Sample every 3rd PNG within each snippet (sample_every=3) for true 1-FPS coverage.
    XD-Violence: decode with decord, get actual FPS, sample every round(fps/1.0) frames.
"""

import argparse
import json
import logging
import pathlib
import re
import sys
from pathlib import Path

# Force unbuffered output so tqdm/logging display in real-time under `conda run`
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Ensure scripts/ is on sys.path so `from corruption import ...` works
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

# cv2 is available in vcc-skeleton (rtmlib env) but NOT in vcc-main.
# For UCF-Crime PNG loading: use PIL.Image.open() directly.
# For XD-Violence video decoding: use decord (primary) with a pure-Python fallback.
try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

UCF_TRAIN_ROOT = pathlib.Path("E:/UCF_crime_dataset/Train")
UCF_TEST_ROOT = pathlib.Path("E:/UCF_crime_dataset/test")

XD_TRAIN_ROOT = pathlib.Path("E:/XD_Violence/train")
XD_TEST_ROOT = pathlib.Path("E:/XD_Violence/test/videos")

SNIPPET_ROOT = pathlib.Path("E:/snippets")
FEATURE_ROOT = pathlib.Path("E:/features")

UCF_CATEGORIES = [
    "Abuse", "Arrest", "Arson", "Assault", "Burglary", "Explosion", "Fighting",
    "NormalVideos", "RoadAccidents", "Robbery", "Shooting", "Shoplifting",
    "Stealing", "Vandalism",
]

# UCF-Crime PNGs are every 10th original frame -> ~3 FPS equivalent (D-04)
# CLIP 1-FPS sampling: take every 3rd PNG within a snippet
UCF_SAMPLE_EVERY = 3  # sample_every = round(3.0 FPS / 1.0 FPS target)

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
# Backbone configuration registry
# ---------------------------------------------------------------------------

BACKBONE_CONFIGS = {
    "clip-vit-b-16": {
        "model_name": "ViT-B-16",
        "pretrained": "openai",
        "embed_dim": 512,       # encode_image output dim
        "output_subdir": "clip",
        "mean_subdir": "clip_mean",
    },
    "siglip2-base": {
        "model_name": "ViT-B-16-SigLIP2-256",
        "pretrained": "webli",
        "embed_dim": 768,       # encode_image output dim
        "output_subdir": "siglip2",
        "mean_subdir": "siglip2_mean",
    },
    "siglip2-so400m": {
        "model_name": "ViT-SO400M-16-SigLIP2-256",
        "pretrained": "webli",
        "embed_dim": 1152,      # encode_image output dim
        "output_subdir": "siglip2_so400m",
        "mean_subdir": "siglip2_so400m_mean",
    },
}


# ---------------------------------------------------------------------------
# Vision model loading
# ---------------------------------------------------------------------------

def load_vision_model(backbone: str, device: str = "cuda"):
    """
    Load a vision backbone model using open-clip-torch.

    Args:
        backbone: Key into BACKBONE_CONFIGS (e.g. 'clip-vit-b-16', 'siglip2-giant').
        device:   Torch device ('cuda' or 'cpu').

    Returns:
        (model, preprocess, cfg) where cfg is the BACKBONE_CONFIGS entry.
    """
    import open_clip
    cfg = BACKBONE_CONFIGS[backbone]
    logger.info(
        f"Loading {backbone} ({cfg['model_name']}, pretrained='{cfg['pretrained']}')..."
    )
    model, _, preprocess = open_clip.create_model_and_transforms(
        cfg["model_name"], pretrained=cfg["pretrained"]
    )
    model.eval()
    model.to(device)
    logger.info(f"{backbone} model loaded on {device}.")
    return model, preprocess, cfg


# ---------------------------------------------------------------------------
# UCF-Crime: category map and frame loading
# ---------------------------------------------------------------------------

def build_ucf_video_category_map(train: bool = True, test: bool = True) -> dict:
    """
    Build a lookup dict from video_id -> (category, root_dir, [sorted PNG paths]).

    Scans UCF_TRAIN_ROOT and UCF_TEST_ROOT for PNGs matching {video_id}_x264_{N}.png.
    Returns dict: {video_id: (category_name, [sorted png_path, ...])}.

    This is called once at startup to avoid per-video directory scans.
    """
    video_map = {}
    roots_to_scan = []
    if train:
        roots_to_scan.append(UCF_TRAIN_ROOT)
    if test:
        roots_to_scan.append(UCF_TEST_ROOT)

    for root in roots_to_scan:
        if not root.exists():
            logger.warning(f"UCF-Crime root not found: {root}")
            continue
        for cat_dir in root.iterdir():
            if not cat_dir.is_dir():
                continue
            # Collect all PNGs and group by video_id
            video_frames = {}  # {video_id: [(frame_num, path), ...]}
            for png in cat_dir.glob("*_x264_*.png"):
                # Extract video_id (everything before _x264_)
                parts = png.stem.rsplit("_x264_", 1)
                if len(parts) != 2:
                    continue
                vid_id, frame_str = parts
                try:
                    frame_num = int(frame_str)
                except ValueError:
                    continue
                if vid_id not in video_frames:
                    video_frames[vid_id] = []
                video_frames[vid_id].append((frame_num, png))

            for vid_id, frame_list in video_frames.items():
                # Sort numerically by frame number (not lexicographically — critical)
                frame_list.sort(key=lambda x: x[0])
                sorted_paths = [p for _, p in frame_list]
                video_map[vid_id] = sorted_paths

    logger.info(f"Built UCF-Crime video map: {len(video_map)} videos found.")
    return video_map


def load_ucf_snippet_frames_pil(
    png_list: list, start: int, end: int, sample_every: int = UCF_SAMPLE_EVERY,
    corruption_type: str = None, corruption_severity: int = None,
    corruption_rng: np.random.Generator = None,
) -> list:
    """
    Load frames for a UCF-Crime snippet as PIL Images for CLIP preprocessing.

    Args:
        png_list:     Sorted list of pathlib.Path for this video's PNGs (indices 0..T-1).
        start:        Snippet start index (inclusive).
        end:          Snippet end index (exclusive).
        sample_every: Take every Nth frame within [start, end) for 1-FPS coverage.
        corruption_type:     Phase 5 TTA: corruption type (None = clean).
        corruption_severity: Phase 5 TTA: severity 1-5 (None = clean).
        corruption_rng:      Numpy RNG for reproducible corruption.

    Returns:
        List of PIL Images (RGB). Empty list if no valid frames.
    """
    frames = []
    for idx in range(start, end, sample_every):
        if idx >= len(png_list):
            break
        png_path = png_list[idx]
        try:
            # Load PNG directly with PIL (RGB); avoids cv2 dependency in vcc-main
            pil_img = Image.open(str(png_path)).convert("RGB")
            # Phase 5 TTA: apply corruption BEFORE CLIP preprocessing
            if corruption_type is not None:
                from corruption import apply_corruption
                frame_np = np.array(pil_img)  # uint8 [H,W,3] RGB
                frame_np = apply_corruption(frame_np, corruption_type, corruption_severity, rng=corruption_rng)
                pil_img = Image.fromarray(frame_np)
            frames.append(pil_img)
        except Exception as e:
            logger.debug(f"Frame load failed: {png_path}: {e}")
    return frames


# ---------------------------------------------------------------------------
# XD-Violence: video frame loading
# ---------------------------------------------------------------------------

def load_xd_snippet_frames_pil(
    video_path: pathlib.Path, start: int, end: int, fps: float,
    vr=None,
    corruption_type: str = None, corruption_severity: int = None,
    corruption_rng: np.random.Generator = None,
) -> list:
    """
    Load frames for an XD-Violence snippet as PIL Images for CLIP preprocessing.

    Args:
        video_path: Path to the .mp4 file.
        start:      Snippet start frame index (inclusive).
        end:        Snippet end frame index (exclusive).
        fps:        Video FPS (from decord or cv2).
        vr:         Reusable decord VideoReader instance.
        corruption_type:     Phase 5 TTA: corruption type (None = clean).
        corruption_severity: Phase 5 TTA: severity 1-5 (None = clean).
        corruption_rng:      Numpy RNG for reproducible corruption.

    Returns:
        List of PIL Images (RGB). Falls back to cv2 if decord fails.
    """
    sample_every = max(1, round(fps / 1.0))  # true 1-FPS sampling
    frame_indices = list(range(start, end, sample_every))

    if not frame_indices:
        return []

    # Primary: decord (confirmed available in vcc-main)
    try:
        import decord
        if vr is None:
            vr = decord.VideoReader(str(video_path), ctx=decord.cpu(0))
        # Clamp indices to valid range
        frame_indices = [i for i in frame_indices if i < len(vr)]
        if not frame_indices:
            return []
        batch = vr.get_batch(frame_indices).asnumpy()  # [N, H, W, 3] RGB
        frames = []
        for frame_np in batch:
            # Phase 5 TTA: apply corruption BEFORE CLIP preprocessing
            if corruption_type is not None:
                from corruption import apply_corruption
                frame_np = apply_corruption(frame_np, corruption_type, corruption_severity, rng=corruption_rng)
            frames.append(Image.fromarray(frame_np))
        return frames
    except Exception as e:
        logger.warning(f"decord failed for {video_path.stem}: {e}. No fallback available.")
        return []


def get_xd_video_fps(video_path: pathlib.Path) -> float:
    """Get video FPS using decord (primary in vcc-main; cv2 not available in this env)."""
    try:
        import decord
        vr = decord.VideoReader(str(video_path), ctx=decord.cpu(0))
        return float(vr.get_avg_fps())
    except Exception as e:
        logger.warning(f"Could not get FPS for {video_path.stem}: {e}. Defaulting to 25 FPS.")
        return 25.0  # safe fallback for typical video FPS


# ---------------------------------------------------------------------------
# CLIP feature extraction per snippet
# ---------------------------------------------------------------------------

def extract_clip_snippet(
    frames: list,
    model: torch.nn.Module,
    preprocess,
    batch_size: int = 64,
    device: str = "cuda",
    pool: str = "mean_max",
    embed_dim: int = 512,
) -> np.ndarray:
    """
    Extract vision features for a list of frames and apply pooling.

    Args:
        frames:     List of PIL Images sampled from one snippet.
        model:      Vision model in eval mode.
        preprocess: open_clip preprocessing transform.
        batch_size: Number of frames per GPU batch.
        device:     'cuda' or 'cpu'.
        pool:       D-23 — "mean_max" (default) or "mean".
        embed_dim:  Per-frame embedding dimension from BACKBONE_CONFIGS (512 for CLIP, 1536 for SigLIP2).

    Returns:
        [embed_dim*2] float32 numpy array (mean + max concatenated) when
        pool='mean_max' (default), or [embed_dim] when pool='mean'.
        Returns zeros of the correct dimension if no frames are available.
    """
    expected_dim = embed_dim if pool == "mean" else embed_dim * 2
    if len(frames) == 0:
        # Edge case: no frames sampled in this snippet range
        logger.warning("No frames for snippet — returning zero feature vector.")
        return np.zeros(expected_dim, dtype=np.float32)

    # Preprocess all frames into a tensor stack
    tensors = torch.stack([preprocess(f) for f in frames])

    all_feats = []
    for i in range(0, len(tensors), batch_size):
        batch = tensors[i : i + batch_size].to(device)
        with torch.no_grad():
            feats = model.encode_image(batch)        # [B, embed_dim]
            feats = feats / feats.norm(dim=-1, keepdim=True)  # L2 normalize per frame
        all_feats.append(feats.cpu().float())

    embeddings = torch.cat(all_feats, dim=0)   # [N_frames_in_snippet, embed_dim]

    mean_feat = embeddings.mean(dim=0)          # [embed_dim]
    if pool == "mean":
        feat_vec = mean_feat                     # [embed_dim]
    else:
        max_feat = embeddings.max(dim=0).values  # [embed_dim]
        feat_vec = torch.cat([mean_feat, max_feat], dim=0)  # [embed_dim * 2]

    return feat_vec.numpy().astype(np.float32)


# ---------------------------------------------------------------------------
# Per-video extraction
# ---------------------------------------------------------------------------

def extract_video_clip_features(
    video_id: str,
    dataset: str,
    split: str,
    boundary_path: pathlib.Path,
    model: torch.nn.Module,
    preprocess,
    batch_size: int = 64,
    device: str = "cuda",
    ucf_video_map: dict = None,
    pool: str = "mean_max",
    embed_dim: int = 512,
    corruption_type: str = None,
    corruption_severity: int = None,
    corruption_rng: np.random.Generator = None,
) -> np.ndarray:
    """
    Extract vision [N_snippets, D] features for one video.

    D = embed_dim * 2 when pool='mean_max'; D = embed_dim when pool='mean'.

    Args:
        embed_dim:           Per-frame embedding dimension from BACKBONE_CONFIGS.
        corruption_type:     Phase 5 TTA: corruption type (None = clean).
        corruption_severity: Phase 5 TTA: severity 1-5 (None = clean).
        corruption_rng:      Numpy RNG for reproducible corruption.

    Returns ndarray [N_snippets, D] float32.
    Raises on unrecoverable error.
    """
    # Load snippet boundaries (shared contract with CTR-GCN script)
    with open(boundary_path) as f:
        boundaries = json.load(f)

    snippet_ranges = boundaries["snippet_frame_ranges"]  # [[start, end], ...]
    n_snippets = boundaries["n_snippets"]

    if n_snippets == 0:
        raise ValueError(f"No snippets defined for {video_id} (too short?)")

    snippet_feats = []

    if dataset == "ucf":
        # UCF-Crime: load from pre-extracted PNGs
        png_list = ucf_video_map.get(video_id)
        if png_list is None or len(png_list) == 0:
            raise FileNotFoundError(
                f"UCF-Crime video '{video_id}' not found in PNG map. "
                f"Check UCF-Crime directory structure."
            )
        for start, end in snippet_ranges:
            frames = load_ucf_snippet_frames_pil(
                png_list, start, end, UCF_SAMPLE_EVERY,
                corruption_type=corruption_type,
                corruption_severity=corruption_severity,
                corruption_rng=corruption_rng,
            )
            feat = extract_clip_snippet(frames, model, preprocess, batch_size, device, pool=pool, embed_dim=embed_dim)
            snippet_feats.append(feat)

    else:
        # XD-Violence: decode from mp4
        if split in ("train", "val"):
            video_path = XD_TRAIN_ROOT / f"{video_id}.mp4"
        else:
            video_path = XD_TEST_ROOT / f"{video_id}.mp4"

        if not video_path.exists():
            raise FileNotFoundError(f"XD-Violence video not found: {video_path}")

        import decord as _decord
        vr = _decord.VideoReader(str(video_path), ctx=_decord.cpu(0))
        fps = float(vr.get_avg_fps())

        for start, end in snippet_ranges:
            frames = load_xd_snippet_frames_pil(
                video_path, start, end, fps, vr=vr,
                corruption_type=corruption_type,
                corruption_severity=corruption_severity,
                corruption_rng=corruption_rng,
            )
            feat = extract_clip_snippet(frames, model, preprocess, batch_size, device, pool=pool, embed_dim=embed_dim)
            snippet_feats.append(feat)

    zero_count = sum(1 for f in snippet_feats if not np.any(f))
    if zero_count > 0:
        logger.warning(
            f"{video_id}: {zero_count}/{len(snippet_feats)} snippets produced "
            f"zero vectors (decoder failures)"
        )

    # Stack all snippets -> [N_snippets, D]
    all_feats = np.stack(snippet_feats, axis=0)

    # Assertion: verify output dimension matches the requested pool mode
    # (Pitfall 5 guard — dimension depends on backbone embed_dim and pool mode).
    expected_dim = embed_dim if pool == "mean" else embed_dim * 2
    assert all_feats.shape[1] == expected_dim, (
        f"Expected {expected_dim}-d features (embed_dim={embed_dim}, pool={pool}), got {all_feats.shape[1]}. "
        f"Cache stores pre-projection features."
    )

    return all_feats.astype(np.float32)


# ---------------------------------------------------------------------------
# Main extraction loop
# ---------------------------------------------------------------------------

def run_extraction(
    dataset: str,
    split: str,
    limit: int = None,
    batch_size: int = 64,
    device: str = "cuda",
    pool: str = "mean_max",
    backbone: str = "clip-vit-b-16",
    corruption_type: str = None,
    corruption_severity: int = None,
) -> None:
    """
    Main loop: extract vision features for all videos in a dataset split.

    Args:
        dataset, split, limit, batch_size, device: see argparse below.
        pool: D-23 — "mean_max" (default) or "mean".
        backbone: Key into BACKBONE_CONFIGS for model selection.
        corruption_type:     Phase 5 TTA: corruption type (None = clean).
        corruption_severity: Phase 5 TTA: severity 1-5 (None = clean).
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

    # Phase 5 TTA: initialize deterministic RNG for corruption reproducibility
    corruption_rng = None
    if corruption_type is not None:
        corruption_rng = np.random.default_rng(42)
        logger.info(
            f"Phase 5 TTA corruption mode: type={corruption_type}, "
            f"severity={corruption_severity}, rng_seed=42"
        )

    # Load vision model (backbone-parameterized)
    cfg = BACKBONE_CONFIGS[backbone]
    embed_dim = cfg["embed_dim"]

    # Setup output directory (backbone-aware routing)
    if corruption_type is not None:
        out_subdir = f"{cfg['output_subdir']}_{corruption_type}_{corruption_severity}"
    elif pool == "mean":
        out_subdir = cfg["mean_subdir"]
    else:
        out_subdir = cfg["output_subdir"]
    output_dir = FEATURE_ROOT / dataset / out_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    if corruption_type is not None:
        logger.info(f"Phase 5 TTA: writing corrupted features to {out_subdir}/")
    elif pool == "mean":
        expected_dim = embed_dim
        logger.info(f"Mean-only mode: emitting [N, {expected_dim}] features to {out_subdir}/.")

    # Error log
    error_log_path = output_dir / "errors.log"

    # Load vision model once at startup
    model, preprocess, _ = load_vision_model(backbone, device=device)

    # Build UCF-Crime video map once at startup (if needed)
    ucf_video_map = None
    if dataset == "ucf":
        ucf_video_map = build_ucf_video_category_map(train=True, test=True)

    skipped = 0
    processed = 0
    failed = 0

    with tqdm(total=len(video_ids), desc=f"clip/{dataset}/{split}", unit="video") as pbar:
        for video_id in video_ids:
            pbar.set_description(f"clip/{dataset}: {video_id[:40]}")

            # Skip-if-exists resume logic (D-14) — validate file is non-trivial
            output_path = output_dir / f"{video_id}.npy"
            if output_path.exists() and output_path.stat().st_size > 128:
                skipped += 1
                pbar.update(1)
                continue

            # Missing boundary JSON: log and skip (D-15)
            boundary_path = SNIPPET_ROOT / dataset / f"{video_id}_boundaries.json"
            if not boundary_path.exists():
                msg = (
                    f"{video_id}\tFileNotFoundError: boundary JSON missing at {boundary_path}. "
                    f"Video likely skipped during skeleton extraction."
                )
                logger.error(f"FAILED: {msg}")
                with open(error_log_path, "a") as ef:
                    ef.write(msg + "\n")
                failed += 1
                pbar.update(1)
                continue

            # Per-video error handling (D-15)
            try:
                feats = extract_video_clip_features(
                    video_id=video_id,
                    dataset=dataset,
                    split=split,
                    boundary_path=boundary_path,
                    model=model,
                    preprocess=preprocess,
                    batch_size=batch_size,
                    device=device,
                    ucf_video_map=ucf_video_map,
                    pool=pool,
                    embed_dim=embed_dim,
                    corruption_type=corruption_type,
                    corruption_severity=corruption_severity,
                    corruption_rng=corruption_rng,
                )
                # Atomic write: tmp then rename.
                # Name tmp as "{id}.tmp.npy" (not "{id}.npy.tmp") because np.save
                # auto-appends ".npy" to paths that don't already end in ".npy",
                # which would produce "{id}.npy.tmp.npy" and break the rename.
                tmp_path = output_dir / f"{video_id}.tmp.npy"
                np.save(str(tmp_path), feats)
                tmp_path.replace(output_path)

                # Runtime shape/dtype validation — branches on pool mode and backbone embed_dim.
                expected_dim = embed_dim if pool == "mean" else embed_dim * 2
                assert feats.ndim == 2, f"Expected 2D array, got {feats.ndim}D"
                assert feats.shape[1] == expected_dim, (
                    f"Expected {expected_dim}-d (embed_dim={embed_dim}, pool={pool}), got {feats.shape[1]}"
                )
                assert feats.dtype == np.float32, f"Expected float32, got {feats.dtype}"
                assert not np.any(np.isnan(feats)), "NaN in CLIP features"
                assert not np.any(np.isinf(feats)), "Inf in CLIP features"

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

def validate_sample_outputs(
    dataset: str, video_ids: list, pool: str = "mean_max",
    backbone: str = "clip-vit-b-16",
) -> None:
    """
    Validate vision backbone .npy outputs for a small set of videos.

    Checks:
        - .npy file exists
        - Shape [N_snippets, expected_dim] with N > 0; expected_dim depends on backbone and pool.
        - dtype float32
        - No NaN or Inf values
        - N_snippets matches skeleton .npy (alignment cross-check)
        - N_snippets matches boundary JSON
    """
    cfg = BACKBONE_CONFIGS[backbone]
    embed_dim = cfg["embed_dim"]
    logger.info(f"Validating {backbone} sample outputs...")
    all_ok = True
    clip_subdir = cfg["mean_subdir"] if pool == "mean" else cfg["output_subdir"]
    clip_dir = FEATURE_ROOT / dataset / clip_subdir
    skel_dir = FEATURE_ROOT / dataset / "skeleton"
    expected_dim = embed_dim if pool == "mean" else embed_dim * 2

    for video_id in video_ids:
        clip_path = clip_dir / f"{video_id}.npy"
        skel_path = skel_dir / f"{video_id}.npy"
        boundary_path = SNIPPET_ROOT / dataset / f"{video_id}_boundaries.json"

        if not clip_path.exists():
            logger.error(f"VALIDATE FAIL: CLIP .npy missing for {video_id}")
            all_ok = False
            continue

        feats = np.load(str(clip_path))

        # Shape check
        if feats.ndim != 2 or feats.shape[1] != expected_dim:
            logger.error(
                f"VALIDATE FAIL: {video_id} shape {feats.shape} (expected [N, {expected_dim}])"
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

        # Alignment check: CLIP N_snippets == skeleton N_snippets (same boundary JSON)
        if skel_path.exists():
            skel_feats = np.load(str(skel_path))
            if skel_feats.shape[0] != feats.shape[0]:
                logger.error(
                    f"VALIDATE FAIL: {video_id} N_snippets mismatch — "
                    f"clip={feats.shape[0]}, skeleton={skel_feats.shape[0]}"
                )
                all_ok = False
            else:
                logger.info(
                    f"  OK alignment: {video_id} N_snippets match "
                    f"clip={feats.shape[0]} == skeleton={skel_feats.shape[0]}"
                )

        # Boundary JSON alignment check
        if boundary_path.exists():
            with open(boundary_path) as f:
                boundaries = json.load(f)
            expected_n = boundaries["n_snippets"]
            if feats.shape[0] != expected_n:
                logger.error(
                    f"VALIDATE FAIL: {video_id} clip n_snippets={feats.shape[0]}, "
                    f"boundary JSON says {expected_n}"
                )
                all_ok = False

    if all_ok:
        logger.info("Validation PASSED: all checked CLIP videos OK.")
    else:
        logger.warning("Validation FAILED: see errors above.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vision backbone feature extraction with pooling (CLIP or SigLIP2)."
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
        "--batch-size",
        type=int,
        default=64,
        help="Number of frames per GPU batch for CLIP inference (default: 64).",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Torch device: 'cuda' or 'cpu' (default: cuda).",
    )
    parser.add_argument(
        "--pool",
        choices=["mean", "mean_max"],
        default="mean_max",
        help="Pooling mode: 'mean_max' (default, mean+max concat) or 'mean' (mean-only).",
    )
    parser.add_argument(
        "--backbone",
        choices=list(BACKBONE_CONFIGS.keys()),
        default="clip-vit-b-16",
        help=(
            "Vision backbone: 'clip-vit-b-16' (default, 512-d embed, 1024-d mean+max) "
            "or 'siglip2-base' (768-d embed, 1536-d mean+max). "
            "Output subdir is backbone-specific (clip/ vs siglip2/)."
        ),
    )
    parser.add_argument(
        "--corruption",
        type=str,
        default=None,
        choices=["gaussian_noise", "jpeg_compression", "brightness", "motion_blur"],
        help="Phase 5 TTA: corruption type to apply before CLIP preprocessing.",
    )
    parser.add_argument(
        "--severity",
        type=int,
        default=None,
        choices=[1, 2, 3, 4, 5],
        help="Phase 5 TTA: corruption severity (1=mild, 5=harsh).",
    )
    args = parser.parse_args()

    # Validate: --corruption and --severity must both be set or both be unset
    if (args.corruption is None) != (args.severity is None):
        parser.error("--corruption and --severity must be used together.")

    run_extraction(
        args.dataset,
        args.split,
        limit=args.limit,
        batch_size=args.batch_size,
        device=args.device,
        pool=args.pool,
        backbone=args.backbone,
        corruption_type=args.corruption,
        corruption_severity=args.severity,
    )

    # Validate on sample videos if --limit was used
    # Skip validation in corruption mode (output dir differs from clean cache)
    if args.limit is not None and args.corruption is None:
        split_file = SPLITS_DIR / f"{args.dataset}_{args.split}.txt"
        with open(split_file) as f:
            all_ids = [line.strip() for line in f if line.strip()]
        sample_ids = all_ids[: min(args.limit, len(all_ids))]
        validate_sample_outputs(args.dataset, sample_ids, pool=args.pool, backbone=args.backbone)


if __name__ == "__main__":
    main()
