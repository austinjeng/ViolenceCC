"""Sanity-verifier for Phase 4 pooling caches (D-22, D-23, PATTERNS.md Pattern 6).

Checks per-video axioms:
  clip_mean axiom:
    shape == (N, 512); for every vid also present in baseline clip/,
    np.allclose(clip_mean[vid], clip[vid][:, :512], atol=1e-5).
  skeleton_2person axiom:
    shape == (N, 2, 256); for every vid also present in baseline skeleton/,
    matches N across both caches (shape-level only — M-pool baseline may have
    pooled alongside T'/V' so an exact allclose on mean-over-M is NOT required).

Usage:
  python scripts/verify_pooling_caches.py --dataset ucf --cache clip_mean \\
      --cache-root E:/features/ucf/clip_mean \\
      --baseline-root E:/features/ucf/clip

  python scripts/verify_pooling_caches.py --dataset ucf --cache skeleton_2person \\
      --cache-root E:/features/ucf/skeleton_2person \\
      --baseline-root E:/features/ucf/skeleton

Exits:
  0 if all probed videos pass AND at least one was checked.
  1 on any FAIL (axiom violation).
  2 on setup errors (no cache root, empty cache dir).

Analog: scripts/verify_alignment.py (dataclass-driven PASS/FAIL/SKIP summary).
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Per-video result
# ---------------------------------------------------------------------------

@dataclass
class VideoResult:
    video_id: str
    status: str       # "pass" | "fail" | "skip"
    failures: List[str] = field(default_factory=list)
    shape_cache: Optional[tuple] = None
    shape_baseline: Optional[tuple] = None


# ---------------------------------------------------------------------------
# Per-cache verifiers
# ---------------------------------------------------------------------------

def verify_clip_mean(vid: str, cache_root: Path, baseline_root: Path) -> VideoResult:
    """Axioms for clip_mean: shape (N, 512); allclose to baseline[:, :512]."""
    r = VideoResult(video_id=vid, status="pass")
    p_cache = cache_root / f"{vid}.npy"
    p_base = baseline_root / f"{vid}.npy"
    if not p_cache.exists():
        return VideoResult(vid, "skip", [f"cache missing: {p_cache}"])
    try:
        arr = np.load(p_cache)
    except Exception as e:
        return VideoResult(vid, "fail", [f"np.load failed on {p_cache}: {e}"])
    r.shape_cache = tuple(arr.shape)
    if arr.ndim != 2 or arr.shape[1] != 512:
        r.failures.append(f"shape {arr.shape} != (N, 512)")
    if p_base.exists():
        try:
            base = np.load(p_base)
            r.shape_baseline = tuple(base.shape)
            if base.ndim != 2 or base.shape[1] != 1024:
                r.failures.append(f"baseline shape {base.shape} != (N, 1024)")
            elif base.shape[0] != arr.shape[0]:
                r.failures.append(
                    f"N mismatch: cache N={arr.shape[0]} baseline N={base.shape[0]}"
                )
            elif arr.shape[1] == 512:
                # Only run allclose when shapes align so we don't raise inside
                # a broadcasting error (already caught by the shape assertion).
                diff = float(np.max(np.abs(arr - base[:, :512])))
                if diff > 1e-5:
                    r.failures.append(
                        f"allclose fail: max|cache - baseline[:, :512]| = {diff:.3e}"
                    )
        except Exception as e:
            r.failures.append(f"baseline compare failed: {e}")
    if r.failures:
        r.status = "fail"
    return r


def verify_skeleton_2person(
    vid: str, cache_root: Path, baseline_root: Path,
) -> VideoResult:
    """Axioms for skeleton_2person: shape (N, 2, 256); N matches baseline."""
    r = VideoResult(video_id=vid, status="pass")
    p_cache = cache_root / f"{vid}.npy"
    p_base = baseline_root / f"{vid}.npy"
    if not p_cache.exists():
        return VideoResult(vid, "skip", [f"cache missing: {p_cache}"])
    try:
        arr = np.load(p_cache)
    except Exception as e:
        return VideoResult(vid, "fail", [f"np.load failed: {e}"])
    r.shape_cache = tuple(arr.shape)
    if arr.ndim != 3 or arr.shape[1] != 2 or arr.shape[2] != 256:
        r.failures.append(f"shape {arr.shape} != (N, 2, 256)")
    if p_base.exists():
        try:
            base = np.load(p_base)
            r.shape_baseline = tuple(base.shape)
            if base.ndim != 2 or base.shape[1] != 256:
                r.failures.append(f"baseline shape {base.shape} != (N, 256)")
            elif base.shape[0] != arr.shape[0]:
                r.failures.append(
                    f"N mismatch: cache N={arr.shape[0]} baseline N={base.shape[0]}"
                )
            # Shape-level axiom only; M-pool aggregation in the baseline may have
            # pooled alongside T'/V', so exact allclose is NOT required.
        except Exception as e:
            r.failures.append(f"baseline compare failed: {e}")
    if r.failures:
        r.status = "fail"
    return r


# ---------------------------------------------------------------------------
# CLI main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase 4 pooling cache sanity verifier (D-22, D-23)."
    )
    ap.add_argument("--dataset", choices=["ucf", "xd"], required=True)
    ap.add_argument(
        "--cache", choices=["clip_mean", "skeleton_2person"], required=True,
    )
    ap.add_argument("--cache-root", required=True, help="path to cache dir")
    ap.add_argument("--baseline-root", required=True, help="path to baseline dir")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    cache_root = Path(args.cache_root)
    baseline_root = Path(args.baseline_root)
    if not cache_root.exists():
        print(f"ERROR: cache root missing: {cache_root}", file=sys.stderr)
        return 2

    vids = sorted(p.stem for p in cache_root.glob("*.npy"))
    if args.limit:
        vids = vids[: args.limit]
    if not vids:
        print(f"ERROR: no .npy files in {cache_root}", file=sys.stderr)
        return 2

    verifier = (
        verify_clip_mean if args.cache == "clip_mean" else verify_skeleton_2person
    )
    results = [verifier(v, cache_root, baseline_root) for v in vids]
    passes = [r for r in results if r.status == "pass"]
    fails = [r for r in results if r.status == "fail"]
    skips = [r for r in results if r.status == "skip"]

    print(f"[verify_pooling] cache={args.cache} dataset={args.dataset}")
    print(f"  PASS: {len(passes)}   FAIL: {len(fails)}   SKIP: {len(skips)}")
    for r in fails[:20]:
        print(f"  FAIL {r.video_id}: {r.failures}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
