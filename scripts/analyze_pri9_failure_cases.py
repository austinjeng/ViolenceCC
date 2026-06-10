"""Pri 9: qualitative failure-case analysis for the headline UCF run (giant, seed 42).

CPU-only (numpy / scikit-learn / json / matplotlib-Agg). No torch / CUDA.

Reconstructs frame labels EXACTLY as src/evaluate.py's UCF default path does:
  - per-video score array taken AS-IS from eval_scores.npz (already frame-level,
    broadcast via the M3 manifest -> total_frames*10 grid at extraction time);
  - frame labels built with src.eval.ucf_annotations.frame_labels(anno, n_frames)
    at n_frames = len(score_array); explicit-Normal videos -> all-zero labels.

A MANDATORY sanity gate verifies the pooled frame AUC reproduces the stored
auc=0.8249 (within 1e-4) before any per-video number is trusted.

Outputs (results/_analysis_2026-06-10/):
  pri9_failure_cases.md, pri9_failure_cases.json, pri9_score_hist.png

The label / score reconstruction imports ONLY torch-free helpers
(src.eval.ucf_annotations) — confirmed not to import torch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_PROJECT_ROOT = Path(r"D:\ViolenceCC")
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.eval.ucf_annotations import frame_labels, parse_annotations  # torch-free

# Determinism (no RNG is strictly used, but fix one per the task contract).
RNG = np.random.default_rng(12345)

RUN_DIR = _PROJECT_ROOT / "results" / "ucf_gated_fusion_giant_s42"
SCORES_NPZ = RUN_DIR / "eval_scores.npz"
METRICS_JSON = RUN_DIR / "eval_metrics.json"
ANN_PATH = _PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
OUT_DIR = _PROJECT_ROOT / "results" / "_analysis_2026-06-10"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STORED_AUC = None  # filled from metrics
SANITY_TOL = 1e-4


def safe_video_auc(y_true: np.ndarray, y_score: np.ndarray):
    """Per-video frame AUC; None when only one class present."""
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, y_score))


def main():
    metrics = json.loads(METRICS_JSON.read_text())
    stored_auc = float(metrics["auc"])
    stored_ap = float(metrics["ap"])
    stored_video_auc = float(metrics["video_auc"])
    stored_snippet_auc = float(metrics["snippet_auc"])

    annos = parse_annotations(ANN_PATH)
    npz = np.load(SCORES_NPZ)
    vids = sorted(npz.keys())

    scores_map: dict[str, np.ndarray] = {}
    labels_map: dict[str, np.ndarray] = {}
    cats_map: dict[str, str] = {}

    for vid in vids:
        s = np.asarray(npz[vid], dtype=np.float64).ravel()
        n_frames = len(s)
        if vid in annos:
            anno = annos[vid]
            cats_map[vid] = anno.category
            labels_map[vid] = frame_labels(anno, n_frames)
        else:
            # evaluate.py: videos absent from the annotation file -> all-zero Normal.
            cats_map[vid] = "Normal"
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
        scores_map[vid] = s

    # ---- MANDATORY SANITY GATE: pooled frame AUC must == stored auc ----
    all_scores = np.concatenate([scores_map[v] for v in vids])
    all_labels = np.concatenate([labels_map[v] for v in vids])
    pooled_auc = float(roc_auc_score(all_labels, all_scores))
    pooled_ap = float(average_precision_score(all_labels, all_scores))
    auc_diff = abs(pooled_auc - stored_auc)
    gate_pass = auc_diff <= SANITY_TOL

    print(f"[sanity] pooled frame AUC = {pooled_auc:.6f} | stored = {stored_auc:.6f} "
          f"| |diff| = {auc_diff:.2e} | PASS={gate_pass}")
    print(f"[sanity] pooled frame AP  = {pooled_ap:.6f} | stored AP = {stored_ap:.6f}")

    if not gate_pass:
        raise SystemExit(
            f"SANITY GATE FAILED: pooled AUC {pooled_auc:.6f} != stored {stored_auc:.6f} "
            f"(|diff|={auc_diff:.2e} > {SANITY_TOL}). Per-video numbers NOT trustworthy."
        )

    # Also reproduce video-level AUC (max-pooled) as a secondary cross-check.
    vid_max = np.array([scores_map[v].max() for v in vids])
    vid_lbl = np.array([1 if labels_map[v].any() else 0 for v in vids])
    repro_video_auc = float(roc_auc_score(vid_lbl, vid_max))

    # ---- 1. Per-anomaly-video frame AUC; worst cases ----
    anomaly_rows = []
    for vid in vids:
        y = labels_map[vid]
        n_pos = int(y.sum())
        if n_pos < 1:
            continue  # anomaly = >=1 positive frame
        s = scores_map[vid]
        auc = safe_video_auc(y, s)
        anomaly_rows.append({
            "video_id": vid,
            "category": cats_map[vid],
            "n_frames": int(len(y)),
            "n_positive_frames": n_pos,
            "frac_anomalous": float(n_pos) / float(len(y)),
            "frame_auc": auc,  # may be None if degenerate (won't happen: n_pos>=1 and normals exist within video? no)
            "score_mean": float(s.mean()),
            "score_max": float(s.max()),
            "score_min": float(s.min()),
            "anom_score_mean": float(s[y == 1].mean()),
            "normal_score_mean": float(s[y == 0].mean()) if (y == 0).any() else None,
        })

    # All anomaly videos have both classes? A video that is 100% anomalous would
    # have no negative frames -> per-video AUC undefined (None). Separate those.
    rankable = [r for r in anomaly_rows if r["frame_auc"] is not None]
    degenerate = [r for r in anomaly_rows if r["frame_auc"] is None]
    rankable.sort(key=lambda r: r["frame_auc"])
    worst5 = rankable[:5]
    best5 = rankable[-5:][::-1]

    # ---- 2. False positives: NORMAL videos by max frame score ----
    normal_rows = []
    for vid in vids:
        if labels_map[vid].any():
            continue  # all-negative only
        s = scores_map[vid]
        normal_rows.append({
            "video_id": vid,
            "category": cats_map[vid],
            "n_frames": int(len(s)),
            "score_max": float(s.max()),
            "score_mean": float(s.mean()),
            "score_p95": float(np.percentile(s, 95)),
            "frac_above_0.5": float((s > 0.5).mean()),
        })
    normal_rows.sort(key=lambda r: r["score_max"], reverse=True)
    top5_fp = normal_rows[:5]

    # ---- 3. Score distributions: anomaly-frame vs normal-frame ----
    anom_frame_scores = all_scores[all_labels == 1]
    norm_frame_scores = all_scores[all_labels == 0]

    def stats(a: np.ndarray) -> dict:
        return {
            "n": int(a.size),
            "mean": float(a.mean()),
            "std": float(a.std()),
            "min": float(a.min()),
            "p05": float(np.percentile(a, 5)),
            "p25": float(np.percentile(a, 25)),
            "median": float(np.median(a)),
            "p75": float(np.percentile(a, 75)),
            "p95": float(np.percentile(a, 95)),
            "max": float(a.max()),
        }

    anom_stats = stats(anom_frame_scores)
    norm_stats = stats(norm_frame_scores)

    # Histogram (Agg). Two overlaid normalized histograms.
    fig, ax = plt.subplots(figsize=(8, 5))
    lo = float(min(all_scores.min(), 0.0))
    hi = float(all_scores.max())
    bins = np.linspace(lo, hi, 60)
    ax.hist(norm_frame_scores, bins=bins, density=True, alpha=0.55,
            label=f"normal frames (n={norm_stats['n']:,})", color="#3b7dd8")
    ax.hist(anom_frame_scores, bins=bins, density=True, alpha=0.55,
            label=f"anomaly frames (n={anom_stats['n']:,})", color="#d8453b")
    ax.axvline(norm_stats["mean"], color="#3b7dd8", linestyle="--", linewidth=1.2,
               label=f"normal mean={norm_stats['mean']:.3f}")
    ax.axvline(anom_stats["mean"], color="#d8453b", linestyle="--", linewidth=1.2,
               label=f"anomaly mean={anom_stats['mean']:.3f}")
    ax.set_xlabel("frame anomaly score")
    ax.set_ylabel("density")
    ax.set_title("UCF giant s42: frame-score distribution (pooled frame AUC=%.4f)" % pooled_auc)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    hist_path = OUT_DIR / "pri9_score_hist.png"
    fig.savefig(hist_path, dpi=130)
    plt.close(fig)

    # ---- JSON output ----
    payload = {
        "run_dir": str(RUN_DIR),
        "rng_seed": 12345,
        "sanity_gate": {
            "stored_auc": stored_auc,
            "pooled_frame_auc": pooled_auc,
            "abs_diff": auc_diff,
            "tol": SANITY_TOL,
            "passed": gate_pass,
            "stored_ap": stored_ap,
            "pooled_frame_ap": pooled_ap,
            "stored_video_auc": stored_video_auc,
            "reproduced_video_auc": repro_video_auc,
            "stored_snippet_auc": stored_snippet_auc,
        },
        "counts": {
            "n_videos": len(vids),
            "n_anomaly_videos": len(anomaly_rows),
            "n_rankable_anomaly_videos": len(rankable),
            "n_degenerate_all_anomalous": len(degenerate),
            "n_normal_videos": len(normal_rows),
            "n_frames_total": int(all_labels.size),
            "n_anomaly_frames": int(anom_stats["n"]),
            "n_normal_frames": int(norm_stats["n"]),
        },
        "worst5_anomaly_videos": worst5,
        "best5_anomaly_videos": best5,
        "degenerate_all_anomalous_videos": degenerate,
        "top5_false_positive_normals": top5_fp,
        "score_distribution": {
            "anomaly_frames": anom_stats,
            "normal_frames": norm_stats,
            "mean_gap_anom_minus_norm": anom_stats["mean"] - norm_stats["mean"],
        },
        "all_anomaly_videos_sorted_by_auc": rankable,
    }
    (OUT_DIR / "pri9_failure_cases.json").write_text(json.dumps(payload, indent=2))

    # ---- Markdown report ----
    def fmt_auc(x):
        return "n/a" if x is None else f"{x:.4f}"

    md = []
    md.append("# Pri 9 — Qualitative failure-case analysis (UCF headline, giant, seed 42)\n")
    md.append(f"Run: `{RUN_DIR.name}`  |  reconstruction matches `src/evaluate.py` UCF path "
              f"(per-video frame-level scores from `eval_scores.npz`, labels via "
              f"`frame_labels(anno, n_frames=len(scores))`, explicit-Normal -> all-zero).\n")
    md.append("## Sanity gate (MANDATORY)\n")
    md.append(f"- Pooled frame AUC reconstructed = **{pooled_auc:.6f}**, stored = **{stored_auc:.6f}**, "
              f"|diff| = {auc_diff:.2e} -> **{'PASS' if gate_pass else 'FAIL'}** (tol {SANITY_TOL}).")
    md.append(f"- Pooled frame AP = {pooled_ap:.6f} (stored {stored_ap:.6f}).")
    md.append(f"- Video-level AUC reproduced = {repro_video_auc:.6f} (stored {stored_video_auc:.6f}).")
    md.append(f"- Per-video numbers below are therefore trustworthy.\n")

    md.append("## Cohort summary\n")
    md.append(f"- {len(vids)} test videos: {len(anomaly_rows)} anomaly (>=1 positive frame), "
              f"{len(normal_rows)} normal (all-negative).")
    md.append(f"- {len(rankable)} anomaly videos are AUC-rankable; "
              f"{len(degenerate)} are 100% anomalous (per-video AUC undefined).")
    md.append(f"- {anom_stats['n']:,} anomaly frames vs {norm_stats['n']:,} normal frames "
              f"({100.0*anom_stats['n']/all_labels.size:.1f}% positive).\n")

    md.append("## 1. Worst ~5 anomaly videos (failure cases, ascending frame-AUC)\n")
    md.append("| rank | video | category | frame-AUC | n_frames | frac_anom | anom score mean | normal score mean |")
    md.append("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(worst5, 1):
        nm = "n/a" if r["normal_score_mean"] is None else f"{r['normal_score_mean']:.3f}"
        md.append(f"| {i} | {r['video_id']} | {r['category']} | {fmt_auc(r['frame_auc'])} | "
                  f"{r['n_frames']} | {r['frac_anomalous']:.3f} | {r['anom_score_mean']:.3f} | {nm} |")
    md.append("")

    md.append("### Likely causes (worst cases)\n")
    interp = interpret_worst(worst5)
    for line in interp:
        md.append(f"- {line}")
    md.append("")

    if degenerate:
        md.append("### Note: 100%-anomalous videos (excluded from AUC ranking)\n")
        for r in degenerate:
            md.append(f"- {r['video_id']} ({r['category']}): all {r['n_frames']} frames positive; "
                      f"per-video AUC undefined (no negative frames). Score mean {r['score_mean']:.3f}.")
        md.append("")

    md.append("## 2. Top ~5 false-positive normal videos (highest max frame score)\n")
    md.append("| rank | video | n_frames | max score | mean score | p95 | frac>0.5 |")
    md.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(top5_fp, 1):
        md.append(f"| {i} | {r['video_id']} | {r['n_frames']} | {r['score_max']:.3f} | "
                  f"{r['score_mean']:.3f} | {r['score_p95']:.3f} | {r['frac_above_0.5']:.3f} |")
    md.append("")
    md.append("### Likely causes (false positives)\n")
    for line in interpret_fp(top5_fp, norm_stats):
        md.append(f"- {line}")
    md.append("")

    md.append("## 3. Score distributions: anomaly vs normal frames\n")
    md.append("| stat | anomaly frames | normal frames |")
    md.append("|---|---|---|")
    for key in ["n", "mean", "std", "min", "p05", "p25", "median", "p75", "p95", "max"]:
        av = anom_stats[key]; nv = norm_stats[key]
        if key == "n":
            md.append(f"| {key} | {av:,} | {nv:,} |")
        else:
            md.append(f"| {key} | {av:.4f} | {nv:.4f} |")
    md.append("")
    md.append(f"- Mean separation (anom - normal) = "
              f"**{anom_stats['mean'] - norm_stats['mean']:+.4f}**.")
    md.append(f"- Histogram: `pri9_score_hist.png`.\n")

    md.append("## 5 best anomaly videos (for contrast)\n")
    md.append("| rank | video | category | frame-AUC | frac_anom |")
    md.append("|---|---|---|---|---|")
    for i, r in enumerate(best5, 1):
        md.append(f"| {i} | {r['video_id']} | {r['category']} | {fmt_auc(r['frame_auc'])} | "
                  f"{r['frac_anomalous']:.3f} |")
    md.append("")

    (OUT_DIR / "pri9_failure_cases.md").write_text("\n".join(md), encoding="utf-8")

    print("[done] wrote:")
    for p in ["pri9_failure_cases.md", "pri9_failure_cases.json", "pri9_score_hist.png"]:
        print("  ", OUT_DIR / p)

    return payload


def interpret_worst(worst5):
    """One-to-two-sentence likely-cause per worst failure case."""
    out = []
    for r in worst5:
        vid, cat = r["video_id"], r["category"]
        frac = r["frac_anomalous"]
        auc = r["frame_auc"]
        anom_m, norm_m = r["anom_score_mean"], r["normal_score_mean"]
        bits = []
        if frac >= 0.85:
            bits.append(f"anomaly spans {frac*100:.0f}% of the clip, so the few "
                        f"normal frames are easily out-scored by the anomalous bulk")
        elif frac <= 0.05:
            bits.append(f"the anomaly is very brief ({frac*100:.1f}% of frames), "
                        f"a hard short-event localization case")
        if norm_m is not None and anom_m is not None and anom_m <= norm_m:
            bits.append("the model scores normal frames at least as high as the "
                        "anomalous ones (inverted ranking) -> appearance/scene-driven, "
                        "not motion/event-driven")
        if cat in ("RoadAccidents", "Explosion", "Shooting"):
            bits.append(f"{cat} events are abrupt and visually transient, weak signal "
                        f"for a snippet-pooled head")
        if cat in ("Shoplifting", "Stealing", "Burglary", "Robbery", "Abuse"):
            bits.append(f"{cat} is subtle/appearance-ambiguous (looks like normal CCTV "
                        f"activity), low motion-saliency for skeleton+CLIP fusion")
        if not bits:
            bits.append(f"frame-AUC {auc:.3f}: weak temporal separation; scores are nearly "
                        f"flat across anomalous and normal segments")
        out.append(f"**{vid}** ({cat}, AUC {fmt_auc_local(auc)}): " + "; ".join(bits) + ".")
    return out


def interpret_fp(top5_fp, norm_stats):
    out = []
    for r in top5_fp:
        vid = r["video_id"]
        mx = r["score_max"]
        frac = r["frac_above_0.5"]
        bits = [f"peak score {mx:.3f} on an all-normal clip"]
        if frac > 0.5:
            bits.append(f"{frac*100:.0f}% of frames exceed 0.5 -> a sustained, "
                        f"scene-wide false alarm (appearance-driven, e.g. crowd/motion "
                        f"resembling an event)")
        elif frac > 0.05:
            bits.append(f"{frac*100:.0f}% of frames over 0.5 -> intermittent spikes, "
                        f"likely brief motion/occlusion bursts misread as anomalous")
        else:
            bits.append("isolated peak only -> a single ambiguous moment drives the "
                        "max-pooled video score")
        out.append(f"**{vid}**: " + "; ".join(bits) + ".")
    out.append(f"Context: the global normal-frame mean is {norm_stats['mean']:.3f} and p95 is "
               f"{norm_stats['p95']:.3f}, so these clips sit far in the right tail of normal scores.")
    return out


def fmt_auc_local(x):
    return "n/a" if x is None else f"{x:.4f}"


if __name__ == "__main__":
    main()
