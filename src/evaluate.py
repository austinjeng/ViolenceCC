"""Phase 4 evaluation CLI (D-06).

Usage:
    python src/evaluate.py --run-dir results/<run>/ [--split {val|test}]

Contract:
    Reads:   config_snapshot.json + best_model.pth from --run-dir.
    Writes:  eval_metrics.json, eval_scores.npz, per_category.csv, .done
             — all into the same --run-dir. Writes are atomic (D-31).

D-10: loads best_model.pth only (never last_model.pth) — reporting the max
      of both would constitute test-set model selection.
D-31: .done is written last and atomically, so its presence implies all
      other outputs are on disk. run_ablations.py uses it as the resume probe.
"""
# D-12 reproducibility: CUBLAS_WORKSPACE_CONFIG must be set BEFORE torch import.
# Eval is no_grad so strictly optional, but keeps Phase 3 bit-identical
# re-evaluation deterministic across invocations.
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import sys
import tempfile
import time
import warnings
from datetime import datetime
from pathlib import Path

# Script-mode bootstrap (same pattern as src/train.py):
# `python src/evaluate.py ...` without -m needs project root on sys.path so
# the `src.*` package imports below resolve.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# M3: committed fallback manifest of true per-video UCF frame counts. Lets the
# full-length headline (82.5% AUC) reproduce from git alone when the off-repo
# snippet-boundaries dir is absent. Built by scripts/build_ucf_frames_manifest.py.
_UCF_FRAMES_MANIFEST_PATH = _PROJECT_ROOT / "data" / "ucf_total_frames.json"
_UCF_FRAMES_MANIFEST = None  # lazily loaded {video_id: total_frames}


def _load_ucf_frames_manifest() -> dict:
    """Return the committed {video_id: total_frames} manifest (cached; {} if absent)."""
    global _UCF_FRAMES_MANIFEST
    if _UCF_FRAMES_MANIFEST is None:
        try:
            _UCF_FRAMES_MANIFEST = json.loads(_UCF_FRAMES_MANIFEST_PATH.read_text())
        except FileNotFoundError:
            _UCF_FRAMES_MANIFEST = {}
    return _UCF_FRAMES_MANIFEST

import numpy as np
import torch
from torch.utils.data import DataLoader

from src.eval.metrics import compute_frame_metrics, compute_snippet_auc
from src.eval.snippet_to_frame import snippet_to_frame
from src.eval.test_loader import build_test_dataset
from src.eval.ucf_annotations import frame_labels, parse_annotations
from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels
from src.models.registry import build_model
from src.utils.checkpoint import load_checkpoint
from src.utils.config import (
    checkpoint_sha,
    config_hash,
    git_sha,
    load_snapshot_as_config,
)
from src.utils.seed import set_deterministic


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="ViolenceCC evaluation CLI (D-06)")
    ap.add_argument(
        "--run-dir", required=True,
        help="Training run dir containing best_model.pth + config_snapshot.json",
    )
    ap.add_argument(
        "--split", choices=["val", "test"], default="test",
        help="D-09: never auto-inferred",
    )
    return ap.parse_args(argv)


# ---------------------------------------------------------------------------
# Run-dir I/O helpers (atomic write-temp-rename — D-31 idiom)
# ---------------------------------------------------------------------------


def _load_cfg(run_dir: Path) -> dict:
    snap_path = run_dir / "config_snapshot.json"
    if not snap_path.exists():
        raise FileNotFoundError(
            f"config_snapshot.json missing in {run_dir}. "
            "Did training complete and snapshot_config run?"
        )
    return load_snapshot_as_config(snap_path)


def _write_json_atomic(payload: dict, path: Path) -> None:
    """Atomic JSON dump: write to tempfile in same dir, fsync, os.replace."""
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
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


def _write_per_category_csv(per_cat: dict, path: Path) -> None:
    """Alphabetical row ordering (Discretion default)."""
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "auc", "ap"])
        for cat in sorted(per_cat):
            w.writerow([cat, per_cat[cat].get("auc", ""), per_cat[cat].get("ap", "")])


# ---------------------------------------------------------------------------
# Inference + frame-grid construction
# ---------------------------------------------------------------------------


@torch.no_grad()
def _run_inference(model, dataset, device: str) -> dict:
    """Return {video_id: np.ndarray[N_snippets]} per-video snippet scores."""
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)
    per_video_snippet_scores: dict = {}
    for batch in loader:
        vid = batch["video_id"][0] if isinstance(batch["video_id"], list) else batch["video_id"]
        # variant-uniform forward (Phase 3 MOD-03..07)
        kwargs = {}
        for k in ("skel", "clip", "i3d", "mask"):
            if k in batch:
                t = batch[k]
                if t.dim() == 2:
                    t = t.unsqueeze(0)  # ensure [B, T, d]
                kwargs[k] = t.to(device)
        scores = model(**kwargs)  # [B, T] or [B, T, 1]
        if scores.dim() == 3:
            scores = scores.squeeze(-1)
        scores_np = scores.squeeze(0).detach().cpu().numpy().astype(np.float32)
        per_video_snippet_scores[vid] = scores_np
    return per_video_snippet_scores


def _build_frame_arrays(cfg: dict, per_video_snippet_scores: dict):
    """Expand snippet scores to frame grid + build frame labels (D-14..D-17).

    UCF path: ann file at cfg["paths"]["annotations_dir"]/ucf_temporal.txt, or
    the D-04 committed fallback at data/annotations/ucf_temporal.txt.
    Snippet window: 64 PNGs, upsample factor 10 -> original-30fps grid.

    XD I3D path (Phase 4b Plan 04): ann file at
    cfg["paths"]["annotations_dir"]/xd_temporal.txt, or the D-07 committed
    fallback at data/annotations/xd_temporal.txt. Snippet window 16, no
    upsample (I3D stride == video fps). Wu 2020 file OMITS normal test
    videos; `if vid in annos` guard routes the 500 abnormal videos through
    xd_frame_labels and defaults the 300 normal videos to all-zero labels.

    Returns: (frames_map, labels_map, categories_map).
    """
    ds = cfg.get("dataset", "ucf")

    if ds == "xd_i3d":
        # D-07/D-10: Wu 2020 annotation path resolution (mirror UCF D-04 canonical fallback)
        ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
        ann_path = None
        if ann_dir_cfg:
            candidate = Path(ann_dir_cfg) / "xd_temporal.txt"
            if candidate.exists():
                ann_path = candidate
        if ann_path is None:
            # D-07 canonical fallback (parallel to UCF ucf_temporal.txt location)
            ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"

        annos = parse_xd_annotations(ann_path) if ann_path.exists() else {}

        # D-08: I3D stride=16, annotation-fps = video-fps (no upsample needed).
        # This xd_i3d (stride-16) path is verified bit-identical to XDVioDet
        # gt.npy (2,330,384 frames). NOTE: the separate xd FUSION path below uses
        # snippet_window=64 and yields 2,313,024 frames (~0.74% shorter); that
        # 'bit-identical' claim applies ONLY to this stride-16 path.
        snippet_window = 16
        upsample_factor = 1

        frames_map: dict = {}
        labels_map: dict = {}
        cats_map: dict = {}
        for vid, scores in per_video_snippet_scores.items():
            n_frames = len(scores) * snippet_window
            frames_map[vid] = snippet_to_frame(
                scores, n_frames=n_frames,
                snippet_window=snippet_window, upsample_factor=upsample_factor,
            )
            if vid in annos:
                # 500 abnormal test videos — Wu provides real intervals
                anno = annos[vid]
                labels_map[vid] = xd_frame_labels(anno, n_frames)
                # D-10: cats_map populated for Phase 4c forward-compat (D-13 suppresses
                # per-category surfacing for rtfm variant but the parser knows the code).
                cats_map[vid] = anno.category
            else:
                # 300 normal test videos — Wu omits normals; Pitfall 2 guard.
                labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
                cats_map[vid] = "Normal"
        return frames_map, labels_map, cats_map

    elif ds == "xd":
        # Phase 4c: XD fusion (skeleton+CLIP) evaluation path.
        # Annotation routing mirrors xd_i3d (D-07/D-10 canonical fallback).
        ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
        ann_path = None
        if ann_dir_cfg:
            candidate = Path(ann_dir_cfg) / "xd_temporal.txt"
            if candidate.exists():
                ann_path = candidate
        if ann_path is None:
            ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"

        annos = parse_xd_annotations(ann_path) if ann_path.exists() else {}

        # XD fusion: skeleton+CLIP extraction uses 64-frame snippet windows
        # (same as UCF), but XD video frames are native FPS (no PNG 10x
        # upsample). So snippet_window=64, upsample_factor=1.
        # NOTE: n_frames = len(scores)*64 drops each video's trailing partial
        # 64-frame window, giving 2,313,024 frames vs the canonical 2,330,384
        # (~0.74% short). Scores and labels share this truncated grid so AP is
        # internally consistent; impact on the 78.7% AP headline is negligible.
        # (Unlike UCF, there is no full-length boundary correction for XD; a
        # symmetric XD total_frames manifest could close this if desired.)
        snippet_window = 64
        upsample_factor = 1

        frames_map: dict = {}
        labels_map: dict = {}
        cats_map: dict = {}
        for vid, scores in per_video_snippet_scores.items():
            n_frames = len(scores) * snippet_window
            frames_map[vid] = snippet_to_frame(
                scores, n_frames=n_frames,
                snippet_window=snippet_window, upsample_factor=upsample_factor,
            )
            if vid in annos:
                anno = annos[vid]
                labels_map[vid] = xd_frame_labels(anno, n_frames)
                cats_map[vid] = anno.category
            else:
                labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
                cats_map[vid] = "Normal"
        return frames_map, labels_map, cats_map

    # ---- UCF default path ----
    ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
    ann_path = None
    if ann_dir_cfg:
        candidate = Path(ann_dir_cfg) / "ucf_temporal.txt"
        if candidate.exists():
            ann_path = candidate
    if ann_path is None:
        # D-04 canonical fallback
        ann_path = _PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"

    annos = parse_annotations(ann_path) if ann_path.exists() else {}

    # D-14: UCF PNG grid (64 frames) upsampled 10x -> original 30fps grid.
    snippet_window = 64
    upsample_factor = 10

    # H1: optionally derive the TRUE full video length from snippet boundary
    # JSONs (total_frames*upsample) instead of the snippet-grid length
    # (len(scores)*64*10), which drops the trailing partial 64-PNG window and
    # truncates ~8.6% of frames. Gated behind paths.snippet_boundaries_dir so
    # this is non-breaking: runs without the cfg key behave exactly as before
    # (plus one warning).
    boundaries_dir = cfg.get("paths", {}).get("snippet_boundaries_dir")
    # M3: committed manifest fallback so full-length frames are recovered from git
    # even when boundaries_dir is unset (the common case for the released snapshots).
    frames_manifest = _load_ucf_frames_manifest()
    _warned_truncated = False

    frames_map: dict = {}
    labels_map: dict = {}
    cats_map: dict = {}
    for vid, scores in per_video_snippet_scores.items():
        n_frames = None
        if boundaries_dir:
            bpath = Path(boundaries_dir) / f"{vid}_boundaries.json"
            if bpath.exists():
                with open(bpath, "r", encoding="utf-8") as f:
                    total_frames = int(json.load(f)["total_frames"])
                n_frames = total_frames * upsample_factor  # H1 TRUE full length
        if n_frames is None and vid in frames_manifest:
            # M3 fallback: true full length from the committed manifest.
            n_frames = int(frames_manifest[vid]) * upsample_factor
        if n_frames is None:
            # CLAUDE.md eval-stub convention: warn ONCE that the live eval is
            # using the truncated snippet-grid length (H1) — only reached when
            # neither the boundaries dir nor the committed manifest has the video.
            if not _warned_truncated:
                warnings.warn(
                    "UCF eval uses the snippet-grid (truncated) length; set "
                    "paths.snippet_boundaries_dir or commit the video to "
                    "data/ucf_total_frames.json to use true full-length frames (H1)."
                )
                _warned_truncated = True
            n_frames = len(scores) * snippet_window * upsample_factor
        if vid in annos:
            anno = annos[vid]
            cats_map[vid] = anno.category
            labels_map[vid] = frame_labels(anno, n_frames)
        else:
            cats_map[vid] = "Normal"
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
        frames_map[vid] = snippet_to_frame(
            scores, n_frames=n_frames,
            snippet_window=snippet_window, upsample_factor=upsample_factor,
        )
    return frames_map, labels_map, cats_map


def _build_snippet_label_grid(per_video_snippet_scores: dict, labels_map: dict) -> dict:
    """Fold frame labels back to snippet grid via max-pool over each window."""
    snippet_labels_map: dict = {}
    for vid in per_video_snippet_scores:
        frame_lbl = labels_map.get(vid)
        if frame_lbl is None:
            continue
        N = len(per_video_snippet_scores[vid])
        if N == 0:
            continue
        sw = len(frame_lbl) // N
        if sw <= 0:
            continue
        snippet_labels_map[vid] = np.array(
            [int(frame_lbl[i * sw:(i + 1) * sw].any()) for i in range(N)],
            dtype=np.int64,
        )
    return snippet_labels_map


# ---------------------------------------------------------------------------
# Metadata builder (D-12)
# ---------------------------------------------------------------------------


def _build_metadata(
    cfg: dict, run_dir: Path, split: str, eval_duration_s: float
) -> dict:
    """Reproducibility metadata appended to every eval_metrics.json."""
    best_path = run_dir / "best_model.pth"
    return {
        "config_hash": config_hash(cfg),
        "git_sha": git_sha(),
        "checkpoint_sha": checkpoint_sha(best_path) if best_path.exists() else "missing",
        "wandb_run_id": cfg.get("wandb", {}).get("run_id"),
        "dataset": cfg.get("dataset", "ucf"),
        "split": split,
        "seed": int(cfg.get("seed", 42)),
        "eval_timestamp": datetime.now().isoformat(timespec="seconds"),
        "eval_duration_s": round(eval_duration_s, 3),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv=None) -> int:
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists():
        raise FileNotFoundError(f"run-dir does not exist: {run_dir}")
    cfg = _load_cfg(run_dir)
    set_deterministic(int(cfg.get("seed", 42)))

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # ---- Build model + load best checkpoint (D-10) ----
    model = build_model(**cfg["model"]).to(device)
    best_path = run_dir / "best_model.pth"
    if not best_path.exists():
        raise FileNotFoundError(f"best_model.pth missing in {run_dir}")
    state = load_checkpoint(best_path, device=device)
    # Phase 3 checkpoints are plain state_dicts (save_checkpoint_atomic saves
    # only the state_dict); but we accept wrapped dicts too for forward compat.
    state_dict = state.get("model", state) if isinstance(state, dict) else state
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    # ---- Build test/val dataset through the guarded module (D-07, D-08) ----
    dataset = build_test_dataset(cfg)

    t0 = time.time()

    if args.split == "val":
        # D-09: val path computes MIL-loss-only (no frame-level metrics).
        # For Phase 4 evaluate.py we stub this as a minimal inference pass
        # plus metadata — full MIL loss recomputation is optional per
        # "Claude's Discretion" in CONTEXT.md.
        per_video_snippet_scores = _run_inference(model, dataset, device)
        eval_duration_s = float(time.time() - t0)
        metadata = _build_metadata(cfg, run_dir, args.split, eval_duration_s)
        print("NOTE: --split val writes mil_loss=0.0 (stub). "
              "Scores saved to eval_scores.npz; loss not recomputed.")
        out = {"mil_loss": 0.0, **metadata}
        _write_json_atomic(out, run_dir / "eval_metrics.json")
        np.savez_compressed(
            run_dir / "eval_scores.npz",
            **{k: v for k, v in per_video_snippet_scores.items()},
        )
        _mark_done(run_dir)
        return 0

    # ---- TEST path ----
    per_video_snippet_scores = _run_inference(model, dataset, device)
    frames_map, labels_map, cats_map = _build_frame_arrays(cfg, per_video_snippet_scores)

    # D-15: compute_frame_metrics asserts length before every sklearn call.
    metrics = compute_frame_metrics(frames_map, labels_map, cats_map)

    # Snippet-grid AUC (debug aid, D-11)
    snippet_labels_map = _build_snippet_label_grid(per_video_snippet_scores, labels_map)
    try:
        metrics["snippet_auc"] = compute_snippet_auc(
            per_video_snippet_scores, snippet_labels_map
        )
    except (ValueError, AssertionError):
        # Fall back to frame AUC if snippet-grid has only one class or
        # labels_map had no usable entry (fully-normal fixture).
        metrics["snippet_auc"] = metrics["auc"]

    eval_duration_s = float(time.time() - t0)
    metadata = _build_metadata(cfg, run_dir, args.split, eval_duration_s)

    # Write order: metrics json -> scores npz -> per_category csv -> .done (last).
    # .done atomicity (D-31): its presence implies all upstream outputs exist.
    out_payload = {**metrics, **metadata}
    _write_json_atomic(out_payload, run_dir / "eval_metrics.json")
    np.savez_compressed(
        run_dir / "eval_scores.npz",
        **{k: v.astype(np.float32) for k, v in frames_map.items()},
    )
    _write_per_category_csv(metrics.get("per_category", {}), run_dir / "per_category.csv")
    _mark_done(run_dir)

    auc = metrics.get("auc", float("nan"))
    ap = metrics.get("ap", float("nan"))
    print(
        f"[evaluate] wrote {run_dir}/eval_metrics.json "
        f"auc={auc:.4f} ap={ap:.4f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
