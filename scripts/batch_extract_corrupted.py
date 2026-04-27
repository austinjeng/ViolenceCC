"""Batch extraction of corrupted features for Phase 5 TTA experiments.

Runs all 30 corrupted feature conditions sequentially:
  - 20 CLIP conditions (4 types x 5 severities) via vcc-main
  - 10 skeleton conditions (motion_blur + jpeg_compression x 5 severities) via vcc-skeleton
  - 10 CTR-GCN conditions on corrupted skeletons via vcc-ctrgcn

Resume-safe: skips conditions where output directory already has >= 280 files.

Usage (run from project root):
    C:/Anaconda/envs/vcc-main/python.exe scripts/batch_extract_corrupted.py
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "extraction_progress.log"

CLIP_PYTHON = "C:/Anaconda/envs/vcc-main/python.exe"
SKEL_PYTHON = "C:/Anaconda/envs/vcc-skeleton/python.exe"
CTRGCN_PYTHON = "C:/Anaconda/envs/vcc-ctrgcn/python.exe"

CORRUPTION_TYPES = ["gaussian_noise", "jpeg_compression", "brightness", "motion_blur"]
SKELETON_REEXTRACT_TYPES = ["motion_blur", "jpeg_compression"]
SEVERITIES = [1, 2, 3, 4, 5]

MIN_FILES = 280  # 290 test videos, allow some failures


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def count_files(directory, ext):
    d = Path(directory)
    if not d.exists():
        return 0
    return len(list(d.glob(f"*.{ext}")))


def run_cmd(cmd, label, timeout_s=7200):
    log(f"  START: {label}")
    start = time.time()
    try:
        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=timeout_s,
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            log(f"  DONE:  {label} ({elapsed / 60:.1f} min)")
            return True
        else:
            log(f"  FAIL:  {label} (rc={result.returncode}, {elapsed / 60:.1f} min)")
            stderr_tail = result.stderr[-300:] if result.stderr else "(no stderr)"
            log(f"         {stderr_tail}")
            return False
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT: {label} (>{timeout_s}s)")
        return False


def main():
    log("=" * 70)
    log("Phase 5 corrupted feature extraction — BATCH START")
    log(f"  CLIP:     {len(CORRUPTION_TYPES) * len(SEVERITIES)} conditions")
    log(f"  Skeleton: {len(SKELETON_REEXTRACT_TYPES) * len(SEVERITIES)} conditions")
    log(f"  CTR-GCN:  {len(SKELETON_REEXTRACT_TYPES) * len(SEVERITIES)} conditions")
    log("=" * 70)

    # ── Stage 1: CLIP extraction (20 conditions, ~12 min each = ~4h) ──
    log("\n=== STAGE 1: CLIP feature extraction (20 conditions) ===")
    clip_done, clip_fail, clip_skip = 0, 0, 0
    for ctype in CORRUPTION_TYPES:
        for sev in SEVERITIES:
            out_dir = Path(f"E:/features/ucf/clip_{ctype}_{sev}")
            n = count_files(out_dir, "npy")
            if n >= MIN_FILES:
                log(f"  SKIP: clip_{ctype}_{sev} (already {n} files)")
                clip_skip += 1
                continue
            ok = run_cmd(
                [CLIP_PYTHON, "scripts/extract_clip.py",
                 "--dataset", "ucf", "--split", "test",
                 "--corruption", ctype, "--severity", str(sev)],
                f"clip_{ctype}_{sev}",
            )
            if ok:
                clip_done += 1
            else:
                clip_fail += 1
    log(f"CLIP summary: {clip_done} done, {clip_skip} skipped, {clip_fail} failed")

    # ── Stage 2: Skeleton re-extraction (10 conditions, ~1h each = ~10h) ──
    log("\n=== STAGE 2: Skeleton re-extraction (10 conditions) ===")
    skel_done, skel_fail, skel_skip = 0, 0, 0
    for ctype in SKELETON_REEXTRACT_TYPES:
        for sev in SEVERITIES:
            out_dir = Path(f"E:/skeletons/ucf/skeleton_{ctype}_{sev}")
            n = count_files(out_dir, "pkl")
            if n >= MIN_FILES:
                log(f"  SKIP: skeleton_{ctype}_{sev} (already {n} files)")
                skel_skip += 1
                continue
            ok = run_cmd(
                [SKEL_PYTHON, "scripts/extract_skeletons.py",
                 "--dataset", "ucf", "--split", "test",
                 "--corruption", ctype, "--severity", str(sev)],
                f"skeleton_{ctype}_{sev}",
                timeout_s=10800,  # 3h timeout per condition
            )
            if ok:
                skel_done += 1
            else:
                skel_fail += 1
    log(f"Skeleton summary: {skel_done} done, {skel_skip} skipped, {skel_fail} failed")

    # ── Stage 3: CTR-GCN on corrupted skeletons (10 conditions) ──
    log("\n=== STAGE 3: CTR-GCN feature extraction on corrupted skeletons ===")
    ctrgcn_done, ctrgcn_fail, ctrgcn_skip = 0, 0, 0
    for ctype in SKELETON_REEXTRACT_TYPES:
        for sev in SEVERITIES:
            out_dir = Path(f"E:/features/ucf/skeleton_{ctype}_{sev}")
            n = count_files(out_dir, "npy")
            if n >= MIN_FILES:
                log(f"  SKIP: ctrgcn_{ctype}_{sev} (already {n} files)")
                ctrgcn_skip += 1
                continue
            pkl_dir = Path(f"E:/skeletons/ucf/skeleton_{ctype}_{sev}")
            if count_files(pkl_dir, "pkl") < MIN_FILES:
                log(f"  SKIP: ctrgcn_{ctype}_{sev} (skeleton pickles not ready)")
                ctrgcn_fail += 1
                continue
            ok = run_cmd(
                [CTRGCN_PYTHON, "scripts/extract_ctrgcn.py",
                 "--dataset", "ucf", "--split", "test",
                 "--corruption", ctype, "--severity", str(sev)],
                f"ctrgcn_{ctype}_{sev}",
                timeout_s=7200,
            )
            if ok:
                ctrgcn_done += 1
            else:
                ctrgcn_fail += 1
    log(f"CTR-GCN summary: {ctrgcn_done} done, {ctrgcn_skip} skipped, {ctrgcn_fail} failed")

    # ── Summary ──
    log("\n" + "=" * 70)
    log("BATCH COMPLETE")
    log(f"  CLIP:     {clip_done + clip_skip}/{len(CORRUPTION_TYPES) * len(SEVERITIES)}")
    log(f"  Skeleton: {skel_done + skel_skip}/{len(SKELETON_REEXTRACT_TYPES) * len(SEVERITIES)}")
    log(f"  CTR-GCN:  {ctrgcn_done + ctrgcn_skip}/{len(SKELETON_REEXTRACT_TYPES) * len(SEVERITIES)}")
    total_fail = clip_fail + skel_fail + ctrgcn_fail
    if total_fail > 0:
        log(f"  FAILURES: {total_fail} — check extraction_progress.log for details")
    else:
        log("  ALL CONDITIONS COMPLETE — ready for TTA evaluation")
    log("=" * 70)


if __name__ == "__main__":
    main()
