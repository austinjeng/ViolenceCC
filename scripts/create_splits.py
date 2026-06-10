"""
create_splits.py — Generate train/val/test split files for UCF-Crime and XD-Violence.

Usage:
    conda run -n vcc-main python scripts/create_splits.py
    conda run -n vcc-main python scripts/create_splits.py --verify

Splits are committed to data/splits/ and must be byte-reproducible (seed=42).

UCF-Crime:
  - Train/val split derived from E:/UCF_crime_dataset/Train/ directory structure
  - Test split derived from E:/UCF_crime_dataset/test/ directory structure
  - 15% stratified val split (stratified by category) with seed=42

XD-Violence:
  - Train/val split derived from E:/XD_Violence/train/ file listing
  - Test split derived from E:/XD_Violence/test/videos/ file listing
  - 15% stratified val split (stratified by normal/anomalous label) with seed=42
"""

import argparse
import os
import pathlib
import re
import sys
import tempfile

from sklearn.model_selection import StratifiedShuffleSplit

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

UCF_TRAIN_ROOT = pathlib.Path("E:/UCF_crime_dataset/Train")
UCF_TEST_ROOT = pathlib.Path("E:/UCF_crime_dataset/test")

XD_TRAIN_ROOT = pathlib.Path("E:/XD_Violence/train")
XD_TEST_ROOT = pathlib.Path("E:/XD_Violence/test/videos")
XD_ANNOTATIONS = pathlib.Path("E:/XD_violence_annotations.txt")

UCF_CATEGORIES = [
    "Abuse", "Arrest", "Arson", "Assault", "Burglary", "Explosion", "Fighting",
    "NormalVideos", "RoadAccidents", "Robbery", "Shooting", "Shoplifting",
    "Stealing", "Vandalism",
]

# XD-Violence train-split exclusions, applied AFTER the seed=42 stratified split.
# Both videos are enumerated from E:/XD_Violence/train and assigned to the TRAIN
# split, then removed; encoding them here (with the original comment header, in
# this order) lets `--verify` regenerate xd_train.txt byte-identically. xd_val and
# xd_test are unaffected (neither excluded video lands there).
# See data/splits/xd_train.txt and paper main.tex:134 (3,952 of 3,954 used).
XD_TRAIN_EXCLUSIONS = {
    "v=8cTqh9tMz_I__#1_label_A": "corrupt MP4, missing moov atom",
    "v=Gm73TwtUyGY__#1_label_G-0-0": "34 frames, below 64-frame window",
}


# ---------------------------------------------------------------------------
# UCF-Crime helpers
# ---------------------------------------------------------------------------

def enumerate_ucf_videos(split_root: pathlib.Path) -> list[tuple[str, str]]:
    """
    Return a list of (video_id, category) tuples from a UCF-Crime split root.

    Video ID is the prefix before ``_x264_`` in PNG filenames.
    Category is the parent directory name.
    """
    results: list[tuple[str, str]] = []
    for cat in UCF_CATEGORIES:
        cat_dir = split_root / cat
        if not cat_dir.exists():
            continue
        seen: set[str] = set()
        for png in cat_dir.iterdir():
            if not png.suffix == ".png":
                continue
            # Extract video_id: everything before "_x264_"
            m = re.match(r"^(.+?)_x264_", png.name)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                results.append((m.group(1), cat))
    return results


def write_split_file(path: pathlib.Path, video_ids: list[str]) -> None:
    """Write sorted video IDs (one per line) to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="\n") as f:
        for vid in sorted(video_ids):
            f.write(vid + "\n")


def generate_ucf_splits(output_dir: pathlib.Path) -> tuple[list[str], list[str], list[str]]:
    """
    Generate UCF-Crime train/val/test split files.

    Returns (train_ids, val_ids, test_ids).
    """
    print("[UCF-Crime] Enumerating training videos...")
    train_all = enumerate_ucf_videos(UCF_TRAIN_ROOT)
    print(f"  Found {len(train_all)} total training videos across {len(UCF_CATEGORIES)} categories")

    video_ids = [v for v, _ in train_all]
    labels = [c for _, c in train_all]

    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
    train_idx, val_idx = next(sss.split(video_ids, labels))

    train_ids = [video_ids[i] for i in train_idx]
    val_ids = [video_ids[i] for i in val_idx]

    print(f"  Train: {len(train_ids)}  Val: {len(val_ids)}  "
          f"(val fraction: {len(val_ids)/(len(train_ids)+len(val_ids)):.3f})")

    # Per-category breakdown
    from collections import Counter
    train_cats = Counter(labels[i] for i in train_idx)
    val_cats = Counter(labels[i] for i in val_idx)
    print("  Per-category (train / val):")
    for cat in sorted(set(labels)):
        print(f"    {cat}: {train_cats[cat]} / {val_cats[cat]}")

    write_split_file(output_dir / "ucf_train.txt", train_ids)
    write_split_file(output_dir / "ucf_val.txt", val_ids)

    print("[UCF-Crime] Enumerating test videos...")
    test_all = enumerate_ucf_videos(UCF_TEST_ROOT)
    test_ids = [v for v, _ in test_all]
    print(f"  Found {len(test_ids)} test videos")
    write_split_file(output_dir / "ucf_test.txt", test_ids)

    return train_ids, val_ids, test_ids


# ---------------------------------------------------------------------------
# XD-Violence helpers
# ---------------------------------------------------------------------------

def xd_is_anomalous(video_id: str) -> bool:
    """
    Determine if an XD-Violence video is anomalous from its filename.

    XD-Violence encodes the label in the filename:
      - ``_label_A``          = normal (no violence)
      - ``_label_B*``         = violent (various violence sub-types)
      - ``_label_G*``         = fighting
      - ``_label_A-B*`` etc.  = anomalous (multi-label, contains violence)

    Any label containing B or G characters (after the ``_label_`` prefix) is
    anomalous. Pure ``_label_A`` (possibly with trailing ``-0-0``) is normal.

    NOTE: The XD-Violence annotation file (XD_violence_annotations.txt) contains
    temporal frame-level annotations for a *subset* of videos; it does NOT serve as
    a complete train/test split or label list. Label extraction from filenames is
    the canonical approach used in the official XD-Violence benchmark.
    """
    if "_label_" not in video_id:
        return False
    label_part = video_id.split("_label_")[-1]
    # Pure normal: starts with A and no B or G components
    # Examples: "A", "A-0-0" → normal
    # Examples: "B1-0-0", "G-0-0", "B2-G-0", "A-B1-0" → anomalous
    components = label_part.replace("-", " ").split()
    for comp in components:
        if comp.startswith("B") or comp.startswith("G"):
            return True
    return False


def enumerate_xd_videos(root: pathlib.Path) -> list[str]:
    """Return sorted list of video IDs (filename without .mp4) from root."""
    return sorted(
        p.stem for p in root.iterdir() if p.suffix == ".mp4"
    )


def generate_xd_splits(output_dir: pathlib.Path) -> tuple[list[str], list[str], list[str]]:
    """
    Generate XD-Violence train/val/test split files.

    Returns (train_ids, val_ids, test_ids).
    """
    print("[XD-Violence] Enumerating training videos...")
    all_train_ids = enumerate_xd_videos(XD_TRAIN_ROOT)
    print(f"  Found {len(all_train_ids)} training videos")

    # Determine binary label for each training video from its filename.
    # XD-Violence encodes normal/anomalous in the label suffix of the filename.
    labels: list[int] = [1 if xd_is_anomalous(vid) else 0 for vid in all_train_ids]

    n_anomalous = sum(labels)
    n_normal = len(labels) - n_anomalous
    print(f"  Normal: {n_normal}  Anomalous: {n_anomalous} in training set")

    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
    train_idx, val_idx = next(sss.split(all_train_ids, labels))

    train_ids = [all_train_ids[i] for i in train_idx]
    val_ids = [all_train_ids[i] for i in val_idx]
    train_labels = [labels[i] for i in train_idx]
    val_labels = [labels[i] for i in val_idx]

    print(f"  Train: {len(train_ids)} ({sum(train_labels)} anomalous)  "
          f"Val: {len(val_ids)} ({sum(val_labels)} anomalous)  "
          f"(val fraction: {len(val_ids)/(len(train_ids)+len(val_ids)):.3f})")

    # Apply documented exclusions and emit the same comment header so the committed
    # xd_train.txt regenerates byte-identically (see XD_TRAIN_EXCLUSIONS).
    train_ids = [v for v in train_ids if v not in XD_TRAIN_EXCLUSIONS]
    n_excl = len(train_idx) - len(train_ids)
    if n_excl:
        print(f"  Excluded {n_excl} documented train video(s): "
              f"{', '.join(XD_TRAIN_EXCLUSIONS)}")
    xd_train_path = output_dir / "xd_train.txt"
    xd_train_path.parent.mkdir(parents=True, exist_ok=True)
    with open(xd_train_path, "w", newline="\n") as f:
        for _vid, _reason in XD_TRAIN_EXCLUSIONS.items():
            f.write(f"# Excluded: {_vid} ({_reason})\n")
        for vid in sorted(train_ids):
            f.write(vid + "\n")
    write_split_file(output_dir / "xd_val.txt", val_ids)

    print("[XD-Violence] Enumerating test videos...")
    test_ids = enumerate_xd_videos(XD_TEST_ROOT)
    print(f"  Found {len(test_ids)} test videos")
    write_split_file(output_dir / "xd_test.txt", test_ids)

    return train_ids, val_ids, test_ids


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def read_split_file(path: pathlib.Path) -> list[str]:
    """Read a split file and return the list of video IDs."""
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def verify_splits(output_dir: pathlib.Path) -> bool:
    """
    Re-generate splits in a temp directory and assert byte-identical output.
    """
    import shutil
    print("\n[Verify] Re-generating splits to check reproducibility...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        generate_ucf_splits(tmp_path)
        generate_xd_splits(tmp_path)

        all_ok = True
        for fname in [
            "ucf_train.txt", "ucf_val.txt", "ucf_test.txt",
            "xd_train.txt", "xd_val.txt", "xd_test.txt",
        ]:
            original = output_dir / fname
            regenerated = tmp_path / fname
            with open(original, "rb") as f1, open(regenerated, "rb") as f2:
                if f1.read() == f2.read():
                    print(f"  OK: {fname}")
                else:
                    print(f"  FAIL: {fname} differs!")
                    all_ok = False
    return all_ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate train/val/test split files for UCF-Crime and XD-Violence."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Re-run split generation and assert byte-identical output (seed reproducibility check).",
    )
    args = parser.parse_args()

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    if args.verify:
        # Still regenerate if files don't exist yet
        if not (SPLITS_DIR / "ucf_train.txt").exists():
            print("Split files don't exist yet — generating first.")
            generate_ucf_splits(SPLITS_DIR)
            generate_xd_splits(SPLITS_DIR)
        ok = verify_splits(SPLITS_DIR)
        if ok:
            print("\nVerification PASSED: all split files are byte-identical on regeneration.")
            sys.exit(0)
        else:
            print("\nVerification FAILED: split files differ on regeneration. Check seed=42.")
            sys.exit(1)
    else:
        generate_ucf_splits(SPLITS_DIR)
        generate_xd_splits(SPLITS_DIR)
        print("\nSplit generation complete.")
        print(f"  Files written to: {SPLITS_DIR}")
        for fname in ["ucf_train.txt", "ucf_val.txt", "ucf_test.txt",
                      "xd_train.txt", "xd_val.txt", "xd_test.txt"]:
            path = SPLITS_DIR / fname
            if path.exists():
                with open(path) as f:
                    n = sum(1 for _ in f if _.strip())
                print(f"  {fname}: {n} videos")


if __name__ == "__main__":
    main()
