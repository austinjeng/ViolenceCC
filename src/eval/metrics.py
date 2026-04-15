"""Frame-level metrics with C4 length-assertion guards (D-11, D-15).

Every call into sklearn.metrics is preceded by a `len(y_score) == len(y_true)`
assertion that raises AssertionError("C4 REGRESSION ...") on mismatch. The
utility inherits the D-15 contract from src/eval/snippet_to_frame.py — any
upstream inconsistency between snippet counts and the annotation-derived
label vector fails loudly before an invalid AUC/AP number is produced.

Returned metric keys (in the primary dict):
  - auc:            ROC-AUC across concatenated per-video frame scores.
  - ap:             Average precision (PR-AUC) on the same concatenation.
  - video_auc:      Optional — max-score-per-video vs binary video label.
  - n_videos:       Count of videos contributing to the concatenation.
  - n_frames:       Total frame count in the concatenated label vector.
  - per_category:   dict of category -> {"auc": ..., "ap": ...}.
                    "Normal" is never a per_category key (D-17 + Discretion).
                    Single-class categories (only zero labels after joining
                    with the Normal pool) are skipped silently — sklearn's
                    roc_auc_score requires both classes present.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def compute_frame_metrics(
    per_video_scores: Dict[str, np.ndarray],
    per_video_labels: Dict[str, np.ndarray],
    per_video_category: Dict[str, str],
) -> dict:
    """Compute auc / ap / video_auc / per_category from per-video arrays (D-11).

    D-15 CONTRACT: every concatenation below produces identical-length score
    and label arrays; the assertion before each sklearn call catches upstream
    N_snippets vs annotation mismatch before a nonsense metric is emitted.

    Args:
      per_video_scores: {video_id: np.ndarray[n_frames]} per-video frame-level
                        anomaly scores (already broadcast from snippet grid).
      per_video_labels: {video_id: np.ndarray[n_frames]} binary ground-truth.
      per_video_category: {video_id: str} — from Sultani category column
                          (D-17). "Normal" is allowed; all other strings are
                          treated as anomaly categories.

    Returns:
      dict with keys: auc, ap, n_videos, n_frames, per_category (dict).
      Optional keys: video_auc (only when videos span both label classes).

    Raises:
      AssertionError: on length mismatch (containing substring "C4 REGRESSION").
      ValueError: from sklearn when the global concatenation has only one
                  class — caller is expected to ensure both classes present.
    """
    # ---- Concatenate per-video scores + labels with C4 length-guard ----
    all_scores, all_labels = [], []
    for vid in per_video_scores:
        s = per_video_scores[vid]
        y = per_video_labels[vid]
        assert len(s) == len(y), (
            f"C4 REGRESSION at {vid}: scores={len(s)} labels={len(y)}"
        )
        all_scores.append(s)
        all_labels.append(y)
    y_score = np.concatenate(all_scores)
    y_true = np.concatenate(all_labels)
    assert len(y_score) == len(y_true), (
        f"C4 REGRESSION at global concatenate: "
        f"y_score={len(y_score)} y_true={len(y_true)}"
    )

    result: dict = {
        "auc": float(roc_auc_score(y_true, y_score)),
        "ap": float(average_precision_score(y_true, y_score)),
        "n_videos": len(per_video_scores),
        "n_frames": int(len(y_true)),
    }

    # ---- Video-level sanity (D-11 weak-supervision check) ----
    vids = list(per_video_scores.keys())
    video_max_scores = np.array([per_video_scores[v].max() for v in vids])
    video_labels = np.array(
        [1 if per_video_labels[v].any() else 0 for v in vids]
    )
    if len(np.unique(video_labels)) > 1:
        result["video_auc"] = float(
            roc_auc_score(video_labels, video_max_scores)
        )

    # ---- Per-category breakdown (D-11, D-17) ----
    # For each anomaly category, join its videos with the Normal pool so that
    # per_category AUC/AP is computed against a sensible "this category vs
    # normal" contrast (matches Sultani et al. evaluation convention).
    per_cat: Dict[str, Dict[str, float]] = {}
    for cat in set(per_video_category.values()):
        if cat == "Normal":
            continue
        cat_vids = [v for v in vids if per_video_category[v] == cat]
        normal_vids = [v for v in vids if per_video_category[v] == "Normal"]
        eval_vids = cat_vids + normal_vids
        if not eval_vids:
            continue
        y_s = np.concatenate([per_video_scores[v] for v in eval_vids])
        y_l = np.concatenate([per_video_labels[v] for v in eval_vids])
        assert len(y_s) == len(y_l), f"C4 REGRESSION per-category {cat}"
        if len(np.unique(y_l)) > 1:
            per_cat[cat] = {
                "auc": float(roc_auc_score(y_l, y_s)),
                "ap": float(average_precision_score(y_l, y_s)),
            }
    result["per_category"] = per_cat
    return result


def compute_snippet_auc(
    per_video_snippet_scores: Dict[str, np.ndarray],
    per_video_snippet_labels: Dict[str, np.ndarray],
) -> float:
    """Snippet-grid AUC (D-11) — debug aid for broadcast bugs.

    If the snippet-grid AUC differs materially from the frame-grid AUC, the
    culprit is almost always the snippet_to_frame broadcast — a different
    number than the frame AUC quickly localizes the bug.
    """
    all_s, all_y = [], []
    for v in per_video_snippet_scores:
        s = per_video_snippet_scores[v]
        y = per_video_snippet_labels[v]
        assert len(s) == len(y), (
            f"C4 REGRESSION snippet-grid mismatch at {v}: "
            f"scores={len(s)} labels={len(y)}"
        )
        all_s.append(s)
        all_y.append(y)
    y_s = np.concatenate(all_s)
    y_l = np.concatenate(all_y)
    return float(roc_auc_score(y_l, y_s))
