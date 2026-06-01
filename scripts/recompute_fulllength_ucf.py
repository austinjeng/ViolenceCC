"""H1 Layer-1: offline full-length UCF (and optional XD) AUC/AP recompute.

This script fixes H1: the live UCF evaluation frame grid is truncated to the
snippet-count length (`len(scores)*64*10`), which is always SHORTER than the
true video length (`total_frames*10`). The trailing partial 64-PNG window is
dropped at extraction, so the snippet grid under-covers each video by up to one
snippet window (640 frames at upsample 10). This drops UCF positive frames and
inflates AUC.

This is an ANALYSIS PAUSE-POINT tool. It is strictly READ-ONLY w.r.t. every
existing artifact and writes EXCLUSIVELY under results/h1_recompute/.

GUARDRAIL (honored below): this script NEVER writes to or overwrites any
eval_metrics.json, eval_scores.npz, per_category.csv inside a run dir,
results-index.csv, any intermediate CSV, tables_generated.tex, main.tex, or any
figure. It only READS those and WRITES under results/h1_recompute/.

It reuses (never reimplements):
  - src.eval.metrics.compute_frame_metrics   (sklearn AUC/AP)
  - src.eval.ucf_annotations.parse_annotations / frame_labels
  - src.eval.snippet_to_frame.snippet_to_frame

eval_scores.npz is keyed by video_id; each value is a 1-D frame array of length
`n_snip*640` that is a PURE per-snippet repeat (verified: per-640-block
peak-to-peak == 0), so per-snippet scores are recovered by
`arr.reshape(n_snip, 640)[:, 0]`.

HARD GATE: ucf_gated_fusion_giant_s42 must recompute to new_auc within 0.001 of
0.8249 AND new_ap within 0.001 of 0.2737. The UCF comparison CSV is written to a
.tmp path and only os.replace-d into place AFTER the gate passes, so a failed
run leaves no paper-facing CSV.

Run (no GPU required):
    conda run -n vcc-main python scripts/recompute_fulllength_ucf.py \
        --boundaries-dir E:/snippets/ucf
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Script-mode bootstrap (same pattern as src/evaluate.py): project root on
# sys.path so the `src.*` package imports below resolve.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np

from src.eval.metrics import compute_frame_metrics
from src.eval.snippet_to_frame import snippet_to_frame
from src.eval.ucf_annotations import frame_labels, parse_annotations

# UCF gate constants (verified baseline; see plan H1).
GIANT_RUN = "ucf_gated_fusion_giant_s42"
GATE_AUC = 0.8249
GATE_AP = 0.2737
GATE_TOL = 0.001

# UCF grid constants (D-14).
UCF_SNIPPET_WINDOW = 64
UCF_UPSAMPLE = 10
UCF_BLOCK = UCF_SNIPPET_WINDOW * UCF_UPSAMPLE  # 640 frames per snippet on the live grid

UCF_COMPARISON_COLUMNS = [
    "run_name",
    "old_auc",
    "new_auc",
    "d_auc",
    "old_ap",
    "new_ap",
    "d_ap",
    "n_videos",
    "n_frames_old",
    "n_frames_new",
    "n_skipped",
]


def _parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="H1 full-length UCF/XD AUC/AP recompute (read-only analysis tool)"
    )
    ap.add_argument(
        "--boundaries-dir", default="E:/snippets/ucf",
        help="Dir of {video_id}_boundaries.json (total_frames) for UCF",
    )
    ap.add_argument(
        "--results-glob", default="results/ucf_*",
        help="Glob (relative to project root) for UCF run dirs",
    )
    ap.add_argument(
        "--out-dir", default="results/h1_recompute",
        help="Output dir; the ONLY place this script writes",
    )
    ap.add_argument(
        "--xd-boundaries-dir", default=None,
        help="Optional XD boundaries dir; XD recompute runs only if set + exists",
    )
    ap.add_argument(
        "--xd-results-glob", default="results/xd_*",
        help="Glob (relative to project root) for XD run dirs",
    )
    return ap.parse_args(argv)


def _recover_snippet_scores(arr: np.ndarray, block: int) -> np.ndarray:
    """Recover per-snippet scores from a pure per-snippet-repeat frame array.

    arr has length n_snip*block and each block of `block` frames is a constant
    repeat of one snippet score, so [:, 0] of the (n_snip, block) reshape
    recovers the per-snippet scores exactly.
    """
    flat = np.asarray(arr).ravel()
    assert flat.shape[0] % block == 0, (
        f"frame array length {flat.shape[0]} not divisible by block {block}"
    )
    n_snip = flat.shape[0] // block
    return flat.reshape(n_snip, block)[:, 0].astype(np.float32)


def _load_boundaries_total_frames(boundaries_dir: Path, vid: str):
    """Return total_frames int from {vid}_boundaries.json, or None if missing."""
    bpath = boundaries_dir / f"{vid}_boundaries.json"
    if not bpath.exists():
        return None
    with open(bpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return int(data["total_frames"])


def _recompute_ucf_run(
    run_dir: Path,
    boundaries_dir: Path,
    annos: dict,
    snippet_window: int,
    upsample_factor: int,
) -> dict | None:
    """Recompute full-length AUC/AP for one UCF run. Returns a CSV row dict.

    READ-ONLY: only loads run_dir/eval_scores.npz + run_dir/eval_metrics.json.
    """
    scores_npz = run_dir / "eval_scores.npz"
    metrics_json = run_dir / "eval_metrics.json"
    if not (scores_npz.exists() and metrics_json.exists()):
        return None

    block = snippet_window * upsample_factor

    with open(metrics_json, "r", encoding="utf-8") as f:
        old_metrics = json.load(f)
    old_auc = float(old_metrics.get("auc"))
    old_ap = float(old_metrics.get("ap"))

    npz = np.load(scores_npz)
    per_video_scores: dict = {}
    per_video_labels: dict = {}
    per_video_category: dict = {}
    skipped_videos: list = []
    n_frames_old = 0

    for vid in npz.files:
        arr = npz[vid]
        snippet_scores = _recover_snippet_scores(arr, block)
        n_snip = snippet_scores.shape[0]
        n_frames_old += n_snip * block

        total_frames = _load_boundaries_total_frames(boundaries_dir, vid)
        if total_frames is None:
            skipped_videos.append(vid)
            continue

        full_len = total_frames * upsample_factor  # TRUE full length

        frame_scores = snippet_to_frame(
            snippet_scores,
            n_frames=full_len,
            snippet_window=snippet_window,
            upsample_factor=upsample_factor,
        )

        if vid in annos:
            anno = annos[vid]
            per_video_labels[vid] = frame_labels(anno, full_len)
            per_video_category[vid] = anno.category
        else:
            per_video_labels[vid] = np.zeros(full_len, dtype=np.int64)
            per_video_category[vid] = "Normal"
        per_video_scores[vid] = frame_scores

    npz.close()

    new_metrics = compute_frame_metrics(
        per_video_scores, per_video_labels, per_video_category
    )
    new_auc = float(new_metrics["auc"])
    new_ap = float(new_metrics["ap"])

    row = {
        "run_name": run_dir.name,
        "old_auc": old_auc,
        "new_auc": new_auc,
        "d_auc": new_auc - old_auc,
        "old_ap": old_ap,
        "new_ap": new_ap,
        "d_ap": new_ap - old_ap,
        "n_videos": new_metrics["n_videos"],
        "n_frames_old": n_frames_old,
        "n_frames_new": int(new_metrics["n_frames"]),
        "n_skipped": len(skipped_videos),
    }
    # Stash the recompute result for downstream per-category emission.
    row["_new_metrics"] = new_metrics
    row["_old_metrics"] = old_metrics
    if skipped_videos:
        print(
            f"  [{run_dir.name}] skipped {len(skipped_videos)} videos with no "
            f"boundary JSON (e.g. {skipped_videos[:3]})"
        )
    return row


def _write_csv(rows: list, columns: list, path: Path) -> None:
    """Write rows (dicts) to CSV at path, only `columns` (drops _-prefixed keys)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})


def _write_giant_per_category(row: dict, path: Path) -> None:
    """Per-category old/new AUC+AP for the giant s42 run only."""
    new_pc = row["_new_metrics"].get("per_category", {})
    old_pc = row["_old_metrics"].get("per_category", {})
    cats = sorted(set(new_pc) | set(old_pc))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "old_auc", "new_auc", "old_ap", "new_ap"])
        for cat in cats:
            o = old_pc.get(cat, {})
            n = new_pc.get(cat, {})
            w.writerow([
                cat,
                o.get("auc", ""),
                n.get("auc", ""),
                o.get("ap", ""),
                n.get("ap", ""),
            ])


def _run_ucf(args, out_dir: Path) -> None:
    boundaries_dir = Path(args.boundaries_dir)
    # Startup guard: fail loudly if UCF boundaries dir is absent.
    if not boundaries_dir.exists():
        sys.exit(
            f"H1 recompute: boundaries dir {boundaries_dir} not found; cannot "
            f"produce correct full-length numbers"
        )

    ann_path = _PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    annos = parse_annotations(ann_path) if ann_path.exists() else {}

    run_dirs = sorted(
        p for p in _PROJECT_ROOT.glob(args.results_glob) if p.is_dir()
    )
    rows: list = []
    for run_dir in run_dirs:
        row = _recompute_ucf_run(
            run_dir, boundaries_dir, annos, UCF_SNIPPET_WINDOW, UCF_UPSAMPLE
        )
        if row is None:
            continue
        print(
            f"  {row['run_name']:<48} "
            f"AUC {row['old_auc']:.4f} -> {row['new_auc']:.4f} "
            f"({row['d_auc']:+.4f})  "
            f"AP {row['old_ap']:.4f} -> {row['new_ap']:.4f} "
            f"({row['d_ap']:+.4f})"
        )
        rows.append(row)

    # HARD GATE on giant s42.
    giant = next((r for r in rows if r["run_name"] == GIANT_RUN), None)
    if giant is None:
        sys.exit(
            f"H1 GATE FAIL: {GIANT_RUN} not found in {args.results_glob}; "
            f"cannot self-verify. No CSV written."
        )
    gate_auc_ok = abs(giant["new_auc"] - GATE_AUC) <= GATE_TOL
    gate_ap_ok = abs(giant["new_ap"] - GATE_AP) <= GATE_TOL
    gate_line = (
        f"H1 GATE {GIANT_RUN}: "
        f"new_auc={giant['new_auc']:.6f} (expected ~{GATE_AUC}, "
        f"d={giant['new_auc'] - GATE_AUC:+.6f})  "
        f"new_ap={giant['new_ap']:.6f} (expected ~{GATE_AP}, "
        f"d={giant['new_ap'] - GATE_AP:+.6f})"
    )
    if not (gate_auc_ok and gate_ap_ok):
        print(gate_line)
        sys.exit(
            f"H1 GATE FAIL: {GIANT_RUN} actual auc={giant['new_auc']:.6f} "
            f"ap={giant['new_ap']:.6f} vs expected auc~{GATE_AUC} ap~{GATE_AP} "
            f"(tol {GATE_TOL}). No paper-facing CSV written."
        )
    print(f"GATE PASS: {gate_line}")

    # Finalize via os.replace (gate passed) — write .tmp first then atomically move.
    out_csv = out_dir / "ucf_fulllength_comparison.csv"
    tmp_csv = out_dir / "ucf_fulllength_comparison.csv.tmp"
    _write_csv(rows, UCF_COMPARISON_COLUMNS, tmp_csv)
    os.replace(tmp_csv, out_csv)
    print(f"Wrote {out_csv} ({len(rows)} rows)")

    # Per-category recompute for the giant s42 run only.
    per_cat_csv = out_dir / "ucf_giant_s42_per_category.csv"
    _write_giant_per_category(giant, per_cat_csv)
    print(f"Wrote {per_cat_csv}")


def _run_xd(args, out_dir: Path) -> None:
    """Optional XD pass. Only runs if --xd-boundaries-dir is set AND exists.

    XD uses upsample_factor=1; overshoot is at most one snippet window, so the
    expected change is ~0. Window inferred per run: 16 for run names containing
    'i3d', else 64 (fusion).
    """
    if not args.xd_boundaries_dir:
        note = out_dir / "xd_SKIPPED.txt"
        note.write_text(
            "XD full-length recompute skipped: no boundary data; expected ~0 "
            "change since upsample_factor=1 and overshoot <= one snippet window\n",
            encoding="utf-8",
        )
        print(f"Wrote {note} (no --xd-boundaries-dir)")
        return

    xd_boundaries = Path(args.xd_boundaries_dir)
    if not xd_boundaries.exists():
        note = out_dir / "xd_SKIPPED.txt"
        note.write_text(
            "XD full-length recompute skipped: no boundary data; expected ~0 "
            "change since upsample_factor=1 and overshoot <= one snippet window\n",
            encoding="utf-8",
        )
        print(f"Wrote {note} (xd boundaries dir absent: {xd_boundaries})")
        return

    # XD annotations + label helper (imported lazily; only needed for XD pass).
    from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels

    ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"
    annos = parse_xd_annotations(ann_path) if ann_path.exists() else {}

    run_dirs = sorted(
        p for p in _PROJECT_ROOT.glob(args.xd_results_glob) if p.is_dir()
    )
    rows: list = []
    for run_dir in run_dirs:
        scores_npz = run_dir / "eval_scores.npz"
        metrics_json = run_dir / "eval_metrics.json"
        if not (scores_npz.exists() and metrics_json.exists()):
            continue

        snippet_window = 16 if "i3d" in run_dir.name else 64
        upsample_factor = 1
        block = snippet_window * upsample_factor

        with open(metrics_json, "r", encoding="utf-8") as f:
            old_metrics = json.load(f)
        old_auc = float(old_metrics.get("auc"))
        old_ap = float(old_metrics.get("ap"))

        npz = np.load(scores_npz)
        per_video_scores: dict = {}
        per_video_labels: dict = {}
        per_video_category: dict = {}
        skipped_videos: list = []
        n_frames_old = 0
        for vid in npz.files:
            arr = npz[vid]
            snippet_scores = _recover_snippet_scores(arr, block)
            n_snip = snippet_scores.shape[0]
            n_frames_old += n_snip * block

            total_frames = _load_boundaries_total_frames(xd_boundaries, vid)
            if total_frames is None:
                skipped_videos.append(vid)
                continue
            full_len = total_frames * upsample_factor
            frame_scores = snippet_to_frame(
                snippet_scores,
                n_frames=full_len,
                snippet_window=snippet_window,
                upsample_factor=upsample_factor,
            )
            if vid in annos:
                anno = annos[vid]
                per_video_labels[vid] = xd_frame_labels(anno, full_len)
                per_video_category[vid] = anno.category
            else:
                per_video_labels[vid] = np.zeros(full_len, dtype=np.int64)
                per_video_category[vid] = "Normal"
            per_video_scores[vid] = frame_scores
        npz.close()

        if not per_video_scores:
            print(f"  [{run_dir.name}] all videos skipped (no XD boundaries); run omitted")
            continue

        new_metrics = compute_frame_metrics(
            per_video_scores, per_video_labels, per_video_category
        )
        rows.append({
            "run_name": run_dir.name,
            "old_auc": old_auc,
            "new_auc": float(new_metrics["auc"]),
            "d_auc": float(new_metrics["auc"]) - old_auc,
            "old_ap": old_ap,
            "new_ap": float(new_metrics["ap"]),
            "d_ap": float(new_metrics["ap"]) - old_ap,
            "n_videos": new_metrics["n_videos"],
            "n_frames_old": n_frames_old,
            "n_frames_new": int(new_metrics["n_frames"]),
            "n_skipped": len(skipped_videos),
        })

    if not rows:
        note = out_dir / "xd_SKIPPED.txt"
        note.write_text(
            "XD full-length recompute skipped: boundary dir present but no XD "
            "run produced a usable recompute (all videos missing boundaries)\n",
            encoding="utf-8",
        )
        print(f"Wrote {note} (no usable XD runs)")
        return

    out_csv = out_dir / "xd_fulllength_comparison.csv"
    tmp_csv = out_dir / "xd_fulllength_comparison.csv.tmp"
    _write_csv(rows, UCF_COMPARISON_COLUMNS, tmp_csv)
    os.replace(tmp_csv, out_csv)
    print(f"Wrote {out_csv} ({len(rows)} rows)")


def main(argv=None) -> None:
    args = _parse_args(argv)
    out_dir = _PROJECT_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== H1 UCF full-length recompute ===")
    _run_ucf(args, out_dir)

    print("=== H1 XD full-length recompute (optional) ===")
    _run_xd(args, out_dir)

    print("H1 recompute complete.")


if __name__ == "__main__":
    main()
