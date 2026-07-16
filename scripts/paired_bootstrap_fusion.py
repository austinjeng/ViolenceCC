#!/usr/bin/env python
"""Paired video-level bootstrap of gated-minus-visual deltas (zero GPU).

Quick 260717-77p Task 2 (Codex round-2 addendum item 4): the thesis's existing
ch05 bootstrap is a *marginal* CI on absolute AUC/AP; this script computes the
*paired* per-configuration difference (Gated Fusion minus Visual-Only) from the
saved frame-level scores in each run's eval_scores.npz.

USAGE (visible terminal, CPU-only, ~1-2 minutes):
    C:/Anaconda/envs/vcc-main/python.exe scripts/paired_bootstrap_fusion.py \
        [--results-dir results] [--out-dir results/paired_bootstrap] [--B 2000]

PROTOCOL (fixed; documented for provenance):
  * Configs: {ucf, xd} x {clip, siglip2, so400m, giant} x seeds {42, 123, 2024}
    -> 24 (dataset, backbone, seed) rows. Gated dir = {ds}_gated_fusion[_{bb}]_s{seed},
    visual dir = {ds}_clip_only[_{bb}]_s{seed}; a missing dir is a hard error.
  * Ground truth mirrors src/evaluate.py:_build_frame_arrays exactly: per-video
    label arrays are built by frame_labels / xd_frame_labels with
    n_frames = len(saved frame-score array). The saved arrays already encode the
    full-length H1/M3 logic (incl. data/ucf_total_frames.json), so lengths match
    by construction; label semantics are NOT reimplemented.
  * MANDATORY sanity gate: for every run dir the full-dataset headline metric
    (UCF: sklearn roc_auc_score; XD: sklearn average_precision_score) is
    recomputed from the loaded npz + rebuilt labels and must match that run's
    eval_metrics.json headline within 1e-3, else the script aborts. The fast
    weighted-metric implementation used inside the bootstrap loop is also
    asserted to reproduce the sklearn value exactly (<1e-9) at multiplicity 1.
  * Bootstrap: B=2000 video-level resamples, numpy default_rng(0) (fixed seed,
    one generator for the whole script). Each iteration draws ONE resample of
    video ids WITH replacement and evaluates BOTH models on that identical
    resample; delta = gated - visual. Degenerate resamples (single-class labels)
    are discarded and redrawn from the same generator (redraw count reported;
    expected 0 for these test sets).
  * Output (ONLY under --out-dir; canonical results/<run>/ dirs are never
    written): paired_bootstrap.csv (24 rows: mean delta, 2.5/97.5 percentiles,
    P(delta>0), n_videos, B, redraws) + summary.json (per-config 3-seed
    aggregates).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eval.ucf_annotations import parse_annotations, frame_labels  # noqa: E402
from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels  # noqa: E402

BACKBONES = {"clip": "", "siglip2": "_siglip2", "so400m": "_so400m", "giant": "_giant"}
SEEDS = (42, 123, 2024)
SANITY_TOL = 1e-3


# --- weighted metrics (exact sklearn-equivalent under integer weights) --------

class CollapsedRun:
    """Per-run collapsed representation for fast weighted AUC/AP.

    Frames are collapsed to unique (video, score, label) triples with counts;
    AUC/AP depend only on score values and (weighted) label counts, so metrics
    under video multiplicities reduce to weighted metrics over this table.
    Sorted order and tie groups are precomputed once (scores never change
    across bootstrap iterations; only the per-video multiplicities do).
    """

    def __init__(self, scores_map: dict, labels_map: dict, video_order: list):
        vidx_l, score_l, label_l, count_l = [], [], [], []
        for vi, vid in enumerate(video_order):
            s = np.asarray(scores_map[vid], dtype=np.float64)
            y = np.asarray(labels_map[vid], dtype=np.int64)
            assert len(s) == len(y), f"len mismatch for {vid}"
            # collapse identical (score, label) pairs within the video
            key = np.stack([s, y.astype(np.float64)], axis=1)
            uniq, counts = np.unique(key, axis=0, return_counts=True)
            vidx_l.append(np.full(len(uniq), vi, dtype=np.int64))
            score_l.append(uniq[:, 0])
            label_l.append(uniq[:, 1].astype(np.int64))
            count_l.append(counts.astype(np.float64))
        vidx = np.concatenate(vidx_l)
        score = np.concatenate(score_l)
        label = np.concatenate(label_l)
        count = np.concatenate(count_l)

        order = np.argsort(-score, kind="mergesort")  # descending, stable
        self.vidx = vidx[order]
        self.score = score[order]
        self.label = label[order]
        self.count = count[order]
        # tie-group starts (distinct thresholds) on the descending-sorted array
        self.group_starts = np.flatnonzero(
            np.r_[True, self.score[1:] != self.score[:-1]]
        )

    def metrics(self, mult: np.ndarray) -> tuple[float, float, float, float]:
        """Return (auc, ap, P, N) under per-video multiplicities `mult`."""
        w = self.count * mult[self.vidx]
        pos_w = w * self.label
        neg_w = w - pos_w
        gs = self.group_starts
        pos_g = np.add.reduceat(pos_w, gs)
        neg_g = np.add.reduceat(neg_w, gs)
        P = pos_g.sum()
        N = neg_g.sum()
        if P == 0 or N == 0:
            return float("nan"), float("nan"), float(P), float(N)
        cum_pos = np.cumsum(pos_g)
        cum_neg = np.cumsum(neg_g)
        # AUC (Mann-Whitney with 0.5 tie credit): each positive-group mass beats
        # all lower-scored negatives and half of the tied negatives.
        neg_below = N - cum_neg
        auc = float(np.sum(pos_g * (neg_below + 0.5 * neg_g)) / (P * N))
        # AP (sklearn step-wise sum over distinct thresholds, descending).
        # Groups whose cumulative weight is still zero (all-absent videos under
        # this resample) have a zero recall increment, so their precision term
        # is irrelevant -- safe-divide it to 0 to avoid 0/0 NaN propagation.
        tot = cum_pos + cum_neg
        recall = cum_pos / P
        precision = np.divide(cum_pos, tot, out=np.zeros_like(cum_pos), where=tot > 0)
        recall_prev = np.r_[0.0, recall[:-1]]
        ap = float(np.sum((recall - recall_prev) * precision))
        return auc, ap, float(P), float(N)


# --- GT construction (mirrors src/evaluate.py:_build_frame_arrays) ------------

def build_labels(dataset: str, scores_map: dict, annos: dict) -> dict:
    labels = {}
    for vid, s in scores_map.items():
        n_frames = len(s)
        if dataset == "ucf":
            if vid in annos:
                labels[vid] = frame_labels(annos[vid], n_frames)
            else:
                labels[vid] = np.zeros(n_frames, dtype=np.int64)
        else:  # xd
            if vid in annos:
                labels[vid] = xd_frame_labels(annos[vid], n_frames)
            else:
                labels[vid] = np.zeros(n_frames, dtype=np.int64)
    return labels


def load_scores(run_dir: Path) -> dict:
    npz = np.load(run_dir / "eval_scores.npz")
    return {k: npz[k] for k in npz.files}


def headline(dataset: str) -> str:
    return "auc" if dataset == "ucf" else "ap"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--out-dir", default="results/paired_bootstrap")
    parser.add_argument("--B", type=int, default=2000)
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    out_dir = Path(args.out_dir)
    assert out_dir.name == "paired_bootstrap", (
        f"Refusing to write outside results/paired_bootstrap/: {out_dir}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(0)  # fixed seed, documented in the header

    annos = {
        "ucf": parse_annotations(PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"),
        "xd": parse_xd_annotations(PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"),
    }

    rows = []
    for dataset in ("ucf", "xd"):
        for bb, suffix in BACKBONES.items():
            for seed in SEEDS:
                gated_dir = results_dir / f"{dataset}_gated_fusion{suffix}_s{seed}"
                visual_dir = results_dir / f"{dataset}_clip_only{suffix}_s{seed}"
                for d in (gated_dir, visual_dir):
                    if not (d / "eval_scores.npz").exists():
                        raise FileNotFoundError(f"missing run artifacts: {d}")

                g_scores = load_scores(gated_dir)
                v_scores = load_scores(visual_dir)
                assert set(g_scores) == set(v_scores), (
                    f"video-id key sets differ: {gated_dir} vs {visual_dir}"
                )
                for vid in g_scores:
                    assert len(g_scores[vid]) == len(v_scores[vid]), (
                        f"frame-count mismatch at {vid}: "
                        f"{len(g_scores[vid])} vs {len(v_scores[vid])}"
                    )

                labels = build_labels(dataset, g_scores, annos[dataset])
                video_order = sorted(g_scores)
                n_videos = len(video_order)
                metric_key = headline(dataset)

                # ---- MANDATORY sanity gate: sklearn recompute vs eval_metrics.json
                for run_dir, scores_map in ((gated_dir, g_scores), (visual_dir, v_scores)):
                    y_score = np.concatenate([scores_map[v] for v in video_order]).astype(np.float64)
                    y_true = np.concatenate([labels[v] for v in video_order])
                    sk = (
                        roc_auc_score(y_true, y_score)
                        if dataset == "ucf"
                        else average_precision_score(y_true, y_score)
                    )
                    stored = json.load(open(run_dir / "eval_metrics.json"))[metric_key]
                    if abs(sk - stored) > SANITY_TOL:
                        raise AssertionError(
                            f"SANITY FAIL {run_dir.name}: recomputed "
                            f"{metric_key}={sk:.6f} vs stored {stored:.6f} "
                            f"(tol {SANITY_TOL}) -- GT reconstruction is NOT exact; aborting."
                        )

                g_run = CollapsedRun(g_scores, labels, video_order)
                v_run = CollapsedRun(v_scores, labels, video_order)

                # fast path must reproduce sklearn exactly at multiplicity 1
                ones = np.ones(n_videos)
                for run, scores_map in ((g_run, g_scores), (v_run, v_scores)):
                    auc1, ap1, _, _ = run.metrics(ones)
                    y_score = np.concatenate([scores_map[v] for v in video_order]).astype(np.float64)
                    y_true = np.concatenate([labels[v] for v in video_order])
                    sk = (
                        roc_auc_score(y_true, y_score)
                        if dataset == "ucf"
                        else average_precision_score(y_true, y_score)
                    )
                    fast = auc1 if dataset == "ucf" else ap1
                    assert abs(fast - sk) < 1e-9, (
                        f"fast weighted metric != sklearn ({fast} vs {sk})"
                    )

                # ---- paired bootstrap
                deltas = np.empty(args.B)
                redraws = 0
                for b in range(args.B):
                    while True:
                        draw = rng.integers(0, n_videos, n_videos)
                        mult = np.bincount(draw, minlength=n_videos).astype(np.float64)
                        g_auc, g_ap, P, N = g_run.metrics(mult)
                        if P == 0 or N == 0:  # degenerate single-class resample
                            redraws += 1
                            continue
                        v_auc, v_ap, _, _ = v_run.metrics(mult)
                        if dataset == "ucf":
                            deltas[b] = g_auc - v_auc
                        else:
                            deltas[b] = g_ap - v_ap
                        break

                lo, hi = np.percentile(deltas, [2.5, 97.5])
                row = {
                    "dataset": dataset,
                    "backbone": bb,
                    "seed": seed,
                    "metric": metric_key,
                    "mean_delta": round(float(deltas.mean()), 6),
                    "p2.5": round(float(lo), 6),
                    "p97.5": round(float(hi), 6),
                    "p_delta_gt0": round(float((deltas > 0).mean()), 6),
                    "n_videos": n_videos,
                    "B": args.B,
                    "redraws": redraws,
                }
                rows.append(row)
                print(
                    f"[{dataset}/{bb}/s{seed}] mean_delta={row['mean_delta']:+.4f} "
                    f"CI[{row['p2.5']:+.4f},{row['p97.5']:+.4f}] "
                    f"P(delta>0)={row['p_delta_gt0']:.3f} (n={n_videos}, B={args.B})",
                    flush=True,
                )

    csv_path = out_dir / "paired_bootstrap.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # per-config 3-seed aggregates
    summary = {}
    for dataset in ("ucf", "xd"):
        for bb in BACKBONES:
            sub = [r for r in rows if r["dataset"] == dataset and r["backbone"] == bb]
            key = f"{dataset}_{bb}"
            summary[key] = {
                "metric": sub[0]["metric"],
                "seeds": [r["seed"] for r in sub],
                "mean_delta_3seed": round(float(np.mean([r["mean_delta"] for r in sub])), 6),
                "p_delta_gt0_per_seed": [r["p_delta_gt0"] for r in sub],
                "p_delta_gt0_min": min(r["p_delta_gt0"] for r in sub),
                "p_delta_gt0_max": max(r["p_delta_gt0"] for r in sub),
                "ci_low_per_seed": [r["p2.5"] for r in sub],
                "ci_high_per_seed": [r["p97.5"] for r in sub],
            }
    with open(out_dir / "summary.json", "w") as f:
        json.dump({"B": args.B, "rng": "numpy default_rng(0)", "configs": summary}, f, indent=2)

    print(f"\nWrote {csv_path} ({len(rows)} rows) + summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
