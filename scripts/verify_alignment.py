"""
verify_alignment.py — Post-extraction alignment verification for dual-modal features.

Runs in the ``vcc-main`` conda environment (PyTorch 2.6.0 + numpy).

Usage:
    python scripts/verify_alignment.py --dataset ucf --split all
    python scripts/verify_alignment.py --dataset ucf --split train --verbose
    python scripts/verify_alignment.py --dataset ucf --split train --sample 10 --verbose
    python scripts/verify_alignment.py --dataset xd --split all

Purpose (DATA-08):
    For every video in the specified split file(s), verify that:
      1. Both skeleton .npy and CLIP .npy files exist
      2. Skeleton shape is [N, 256], CLIP shape is [N, 1024], N > 0
      3. Both are float32 dtype
      4. N_skeleton == N_clip (the critical alignment check)
      5. Both match n_snippets in the shared boundary JSON
      6. No NaN or Inf values in either feature file
      7. Feature variance is non-trivial (not collapsed)

Exit code:
    0 — all videos pass all checks
    1 — one or more failures detected (or --split all has no videos)

Report format:
    === Alignment Verification: UCF-Crime ===
    Split: all (train + val + test)
    Total videos checked: 1560
    PASS: 1556
    FAIL: 4
    SKIP (missing files): 0

    Failures:
      - Fighting042: n_skel=5, n_clip=4 (MISMATCH)

    Summary statistics:
      Snippet count range: 1 - 47
      Mean snippets per video: 12.3
      Skeleton feature norm range: [0.12, 4.56]
      CLIP feature norm range: [0.89, 1.23]
"""

import argparse
import json
import pathlib
import random
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

SKELETON_ROOT = pathlib.Path("E:/features")
SNIPPET_ROOT = pathlib.Path("E:/snippets")
FEATURE_ROOT = pathlib.Path("E:/features")

# Dataset display names
DATASET_NAMES = {
    "ucf": "UCF-Crime",
    "xd": "XD-Violence",
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class VideoResult:
    video_id: str
    status: str  # 'pass', 'fail', 'skip'
    failures: List[str] = field(default_factory=list)
    n_skel: Optional[int] = None
    n_clip: Optional[int] = None
    skel_norm: Optional[float] = None
    clip_norm: Optional[float] = None


# ---------------------------------------------------------------------------
# Per-video verification
# ---------------------------------------------------------------------------

def verify_video(
    video_id: str,
    dataset: str,
    verbose: bool = False,
) -> VideoResult:
    """
    Run all alignment checks for a single video.

    Returns a VideoResult with status 'pass', 'fail', or 'skip'.
    'skip' means required files are missing (extraction incomplete).
    'fail' means files exist but have integrity/alignment errors.
    """
    skel_path = FEATURE_ROOT / dataset / "skeleton" / f"{video_id}.npy"
    clip_path = FEATURE_ROOT / dataset / "clip" / f"{video_id}.npy"
    boundary_path = SNIPPET_ROOT / dataset / f"{video_id}_boundaries.json"

    result = VideoResult(video_id=video_id, status="pass")

    # -----------------------------------------------------------------------
    # 1. File existence check
    # -----------------------------------------------------------------------
    missing = []
    if not skel_path.exists():
        missing.append(f"skeleton .npy missing: {skel_path}")
    if not clip_path.exists():
        missing.append(f"clip .npy missing: {clip_path}")
    if not boundary_path.exists():
        missing.append(f"boundary JSON missing: {boundary_path}")

    if missing:
        # All three required; any missing -> skip (extraction incomplete)
        result.status = "skip"
        result.failures = missing
        if verbose:
            print(f"  SKIP {video_id}: {'; '.join(missing)}")
        return result

    # -----------------------------------------------------------------------
    # 2. Load features (memory-mapped for efficiency)
    # -----------------------------------------------------------------------
    try:
        skel = np.load(str(skel_path), mmap_mode='r')
    except Exception as exc:
        result.status = "fail"
        result.failures.append(f"skeleton load error: {exc}")

    try:
        clip = np.load(str(clip_path), mmap_mode='r')
    except Exception as exc:
        result.status = "fail"
        result.failures.append(f"clip load error: {exc}")

    if result.status == "fail":
        return result

    # -----------------------------------------------------------------------
    # 3. Shape validation
    # -----------------------------------------------------------------------
    if skel.ndim != 2 or skel.shape[1] != 256:
        result.status = "fail"
        result.failures.append(
            f"skeleton shape {skel.shape} != [N, 256]"
        )
    elif skel.shape[0] == 0:
        result.status = "fail"
        result.failures.append("skeleton has 0 snippets")

    if clip.ndim != 2 or clip.shape[1] != 1024:
        result.status = "fail"
        result.failures.append(
            f"clip shape {clip.shape} != [N, 1024]"
        )
    elif clip.shape[0] == 0:
        result.status = "fail"
        result.failures.append("clip has 0 snippets")

    # -----------------------------------------------------------------------
    # 4. Dtype check
    # -----------------------------------------------------------------------
    if skel.dtype != np.float32:
        result.status = "fail"
        result.failures.append(f"skeleton dtype {skel.dtype} != float32")

    if clip.dtype != np.float32:
        result.status = "fail"
        result.failures.append(f"clip dtype {clip.dtype} != float32")

    # If shape/dtype checks failed, skip alignment checks to avoid index errors
    if result.status == "fail":
        return result

    # -----------------------------------------------------------------------
    # 5. Snippet count alignment (DATA-08 core check)
    # -----------------------------------------------------------------------
    n_skel = skel.shape[0]
    n_clip = clip.shape[0]
    result.n_skel = n_skel
    result.n_clip = n_clip

    if n_skel != n_clip:
        result.status = "fail"
        result.failures.append(
            f"n_skel={n_skel} != n_clip={n_clip} (MISMATCH)"
        )

    # Load boundary JSON and verify against both
    try:
        with open(boundary_path) as f:
            boundaries = json.load(f)
        n_boundary = boundaries["n_snippets"]

        if n_skel != n_boundary:
            result.status = "fail"
            result.failures.append(
                f"n_skel={n_skel} != n_boundary={n_boundary} (boundary JSON mismatch)"
            )

        if n_clip != n_boundary:
            result.status = "fail"
            result.failures.append(
                f"n_clip={n_clip} != n_boundary={n_boundary} (boundary JSON mismatch)"
            )
    except Exception as exc:
        result.status = "fail"
        result.failures.append(f"boundary JSON read error: {exc}")

    # -----------------------------------------------------------------------
    # 6. NaN / Inf checks
    # -----------------------------------------------------------------------
    # Note: mmap_mode='r' still supports np.any(np.isnan()) without loading full array
    if np.any(np.isnan(skel)):
        result.status = "fail"
        result.failures.append("skeleton contains NaN values")

    if np.any(np.isinf(skel)):
        result.status = "fail"
        result.failures.append("skeleton contains Inf values")

    if np.any(np.isnan(clip)):
        result.status = "fail"
        result.failures.append("clip contains NaN values")

    if np.any(np.isinf(clip)):
        result.status = "fail"
        result.failures.append("clip contains Inf values")

    # -----------------------------------------------------------------------
    # 7. Variance check (collapsed feature guard, C1 pitfall)
    # -----------------------------------------------------------------------
    skel_var = float(np.array(skel).var())  # load to compute var
    if skel_var <= 1e-10:
        result.status = "fail"
        result.failures.append(
            f"skeleton variance={skel_var:.2e} <= 1e-10 (collapsed features)"
        )

    clip_var = float(np.array(clip).var())
    if clip_var <= 1e-10:
        result.status = "fail"
        result.failures.append(
            f"clip variance={clip_var:.2e} <= 1e-10 (collapsed features)"
        )

    # -----------------------------------------------------------------------
    # 8. Compute summary stats (norms for report)
    # -----------------------------------------------------------------------
    try:
        skel_norms = np.linalg.norm(np.array(skel), axis=1)  # [N]
        result.skel_norm = float(skel_norms.mean())
        clip_norms = np.linalg.norm(np.array(clip), axis=1)  # [N]
        result.clip_norm = float(clip_norms.mean())
    except Exception:
        pass  # Non-critical stat computation failure

    if verbose:
        if result.status == "pass":
            print(
                f"  PASS {video_id}: skel={skel.shape}, clip={clip.shape}, "
                f"n_snippets={n_skel}"
            )
        else:
            for f in result.failures:
                print(f"  FAIL {video_id}: {f}")

    return result


# ---------------------------------------------------------------------------
# Split loading
# ---------------------------------------------------------------------------

def load_video_ids_for_splits(dataset: str, split: str) -> Tuple[List[str], List[str]]:
    """
    Return (video_ids, split_names_used) for the specified split.

    split can be 'train', 'val', 'test', or 'all' (all three combined).
    """
    splits_to_load = ["train", "val", "test"] if split == "all" else [split]
    all_ids = []
    found_splits = []

    for s in splits_to_load:
        split_file = SPLITS_DIR / f"{dataset}_{s}.txt"
        if not split_file.exists():
            print(f"WARNING: Split file not found: {split_file}. Skipping.")
            continue
        with open(split_file) as f:
            ids = [line.strip() for line in f if line.strip()]
        all_ids.extend(ids)
        found_splits.append(f"{s}({len(ids)})")

    return all_ids, found_splits


# ---------------------------------------------------------------------------
# Main verification function
# ---------------------------------------------------------------------------

def run_verification(
    dataset: str,
    split: str,
    sample: Optional[int] = None,
    verbose: bool = False,
) -> int:
    """
    Run alignment verification for all (or sampled) videos in the given split(s).

    Returns 0 if all pass, 1 if any failures.
    """
    dataset_name = DATASET_NAMES.get(dataset, dataset.upper())

    # Print header
    print(f"\n{'='*60}")
    print(f"=== Alignment Verification: {dataset_name} ===")
    print(f"{'='*60}")

    # Load video IDs
    video_ids, split_names = load_video_ids_for_splits(dataset, split)

    if not video_ids:
        print(f"ERROR: No videos found for dataset={dataset} split={split}")
        return 1

    # Coverage check: which split files were used
    split_label = (
        "all (train + val + test)" if split == "all"
        else f"{split} ({len(video_ids)} videos)"
    )
    if split == "all":
        split_label = f"all ({' + '.join(split_names)})"
    print(f"Split: {split_label}")
    print(f"Total videos in split file(s): {len(video_ids)}")

    # Optional: random sample for quick checks
    if sample is not None and sample < len(video_ids):
        random.seed(42)
        video_ids = random.sample(video_ids, sample)
        print(f"Sampling {sample} random videos for quick check.")

    print(f"Videos to check: {len(video_ids)}")

    if verbose:
        print()

    # -----------------------------------------------------------------------
    # Coverage check: which videos have feature files at all
    # -----------------------------------------------------------------------
    skel_dir = FEATURE_ROOT / dataset / "skeleton"
    clip_dir = FEATURE_ROOT / dataset / "clip"

    # Count feature files vs split file entries
    skel_count = len(list(skel_dir.glob("*.npy"))) if skel_dir.exists() else 0
    clip_count = len(list(clip_dir.glob("*.npy"))) if clip_dir.exists() else 0
    print(f"Feature files on disk: skeleton={skel_count}, clip={clip_count}")

    if verbose:
        print()

    # -----------------------------------------------------------------------
    # Per-video verification loop
    # -----------------------------------------------------------------------
    results = []
    for video_id in video_ids:
        result = verify_video(video_id, dataset, verbose=verbose)
        results.append(result)

    # -----------------------------------------------------------------------
    # Aggregate results
    # -----------------------------------------------------------------------
    passes = [r for r in results if r.status == "pass"]
    fails = [r for r in results if r.status == "fail"]
    skips = [r for r in results if r.status == "skip"]

    print()
    print(f"Total videos checked: {len(results)}")
    print(f"PASS: {len(passes)}")
    print(f"FAIL: {len(fails)}")
    print(f"SKIP (missing files): {len(skips)}")

    # Report failures
    if fails:
        print()
        print("Failures:")
        for r in fails:
            for failure_msg in r.failures:
                print(f"  - {r.video_id}: {failure_msg}")

    # Report skips (extraction incomplete)
    if skips and verbose:
        print()
        print("Skipped (missing files — extraction incomplete):")
        for r in skips[:20]:  # Limit skip list to first 20 for readability
            print(f"  - {r.video_id}: {r.failures[0] if r.failures else 'missing files'}")
        if len(skips) > 20:
            print(f"  ... and {len(skips) - 20} more.")
    elif skips:
        print(f"\nSkipped videos (first 5 of {len(skips)}):")
        for r in skips[:5]:
            print(f"  - {r.video_id}")

    # -----------------------------------------------------------------------
    # Summary statistics (only from passing videos with valid stats)
    # -----------------------------------------------------------------------
    passing_with_stats = [
        r for r in passes if r.n_skel is not None and r.n_clip is not None
    ]

    if passing_with_stats:
        n_counts = [r.n_skel for r in passing_with_stats]
        skel_norms = [r.skel_norm for r in passing_with_stats if r.skel_norm is not None]
        clip_norms = [r.clip_norm for r in passing_with_stats if r.clip_norm is not None]

        print()
        print("Summary statistics:")
        print(f"  Snippet count range: {min(n_counts)} - {max(n_counts)}")
        print(f"  Mean snippets per video: {sum(n_counts) / len(n_counts):.1f}")
        if skel_norms:
            print(f"  Skeleton feature norm range: [{min(skel_norms):.3f}, {max(skel_norms):.3f}]")
        if clip_norms:
            print(f"  CLIP feature norm range: [{min(clip_norms):.3f}, {max(clip_norms):.3f}]")

    # -----------------------------------------------------------------------
    # Coverage gap report
    # -----------------------------------------------------------------------
    if skips:
        print()
        print(
            f"WARNING: {len(skips)}/{len(results)} videos in split files have no feature files. "
            f"Extraction may be incomplete."
        )

    # -----------------------------------------------------------------------
    # Exit code
    # -----------------------------------------------------------------------
    if fails:
        print()
        print(f"RESULT: FAILED ({len(fails)} alignment failures)")
        return 1
    elif skips:
        print()
        print(
            f"RESULT: INCOMPLETE (0 failures but {len(skips)} videos with missing files — "
            f"run extraction scripts first)"
        )
        return 1
    else:
        print()
        print(f"RESULT: PASSED (all {len(passes)} checked videos OK)")
        return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Verify alignment between skeleton and CLIP feature files. "
            "Checks: file existence, shape [N,256]/[N,1024], float32 dtype, "
            "n_skel==n_clip==n_boundary, no NaN/Inf, non-zero variance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify_alignment.py --dataset ucf --split all
  python scripts/verify_alignment.py --dataset ucf --split train --sample 10 --verbose
  python scripts/verify_alignment.py --dataset xd --split all

Exit codes:
  0 = all checked videos passed all checks
  1 = one or more failures (or no videos found)
        """,
    )
    parser.add_argument(
        "--dataset",
        choices=["ucf", "xd"],
        required=True,
        help="Dataset to verify: ucf (UCF-Crime) or xd (XD-Violence).",
    )
    parser.add_argument(
        "--split",
        choices=["train", "val", "test", "all"],
        default="all",
        help="Which split(s) to verify. 'all' = train+val+test (default: all).",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="Verify only N randomly sampled videos (seed=42). For quick checks.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-video PASS/FAIL details.",
    )
    args = parser.parse_args()

    exit_code = run_verification(
        dataset=args.dataset,
        split=args.split,
        sample=args.sample,
        verbose=args.verbose,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
