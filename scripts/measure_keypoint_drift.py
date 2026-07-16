"""measure_keypoint_drift.py -- D3 prep run: RTMPose keypoint drift under corruption.

Quick 260717-77p Task 3(A) (Codex round-2 / internal item D3): the thesis
asserts (ch04) that RTMPose "produces effectively identical keypoints" on
gaussian-noise and brightness corruptions, which justifies reusing the CLEAN
skeleton cache for those families. That assertion has never been measured.
This script measures it on a stratified sample of UCF-Crime test videos.

RUN IN A VISIBLE TERMINAL (user preference -- no headless background jobs):
    C:/Anaconda/envs/vcc-skeleton/python.exe scripts/measure_keypoint_drift.py
    (or: conda activate vcc-skeleton && python scripts/measure_keypoint_drift.py)

Environment: vcc-skeleton (rtmlib + onnxruntime-gpu + opencv). The cuDNN PATH
fix and RTMPose init are inherited from scripts/extract_skeletons.py.

Expected runtime: ~50 videos x 4 conditions x ~700 frames at ~46 ms/frame
(RTX 4090, yolox-m + rtmpose-m) ~= 1.5-2.5 h GPU. RESUMABLE: rows already in
the output CSV are skipped, so the job can be interrupted and re-launched.

Validation without GPU:  --list-only  enumerates the stratified sample and
conditions and exits WITHOUT importing rtmlib or running any inference.

PROTOCOL:
  * Sample: ~TARGET_SAMPLE UCF test videos stratified by category directory
    (E:/UCF_crime_dataset/test/<Category>/), proportional allocation with a
    minimum of 1 per category, numpy default_rng(0), restricted to videos
    whose clean skeleton cache E:/skeletons/ucf/<vid>.pkl exists.
  * Conditions: gaussian_noise severities 3/4/5 + brightness severity 5 --
    the clean-cache-reuse families of scripts/corruption.py
    (SKELETON_REEXTRACT_TYPES excludes them). Corruption functions are
    IMPORTED from scripts/corruption.py via extract_skeletons.load_ucf_frames
    (frames corrupted in-memory BEFORE RTMPose inference; rng seed 42,
    mirroring extract_skeletons corruption mode).
  * Per video x condition, against the clean cache pickle
    (keypoint [M=2,T,17,2] pixel coords, keypoint_score [M=2,T,17]):
      - mean_px_dev : mean L2 pixel deviation over joints with clean
        confidence > 0 (person slots matched per frame by the better of the
        identity / swapped assignment).
      - oks         : OKS-style similarity, bbox-scale-normalized:
        per frame/person, s = sqrt(bbox_w * bbox_h) over the clean person's
        valid joints, and OKS = mean_i exp(-d_i^2 / (2 * s^2 * kappa^2)) with
        a single kappa = 0.1 for all joints (simplified from COCO's per-joint
        k_i; documented here as the formula of record).
      - conf_drop   : mean clean keypoint confidence minus mean corrupted
        keypoint confidence over the same valid slots.

NEGLIGIBILITY CRITERION (stated up front; printed with the verdict):
    A condition PASSES if mean OKS >= 0.85 AND mean confidence drop <= 0.10.
    PASS -> the ch04 clean-cache-reuse assertion is supported for that
    condition (add the measurement as one sentence + table row in ch04).
    FAIL -> escalate: re-extract the gaussian-family skeleton cache
    (~1-2 GPU-days per the Phase 5 D-02 budget) before the defense.

Output: results/keypoint_drift/keypoint_drift.csv (one row per
video x condition) + a printed per-condition summary with PASS/FAIL.
"""
from __future__ import annotations

import argparse
import csv
import pickle
import sys
from pathlib import Path

import numpy as np

_SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

UCF_TEST_ROOT = Path("E:/UCF_crime_dataset/test")
CLEAN_SKELETON_DIR = Path("E:/skeletons/ucf")
OUT_CSV = PROJECT_ROOT / "results" / "keypoint_drift" / "keypoint_drift.csv"

TARGET_SAMPLE = 50
CONDITIONS = [
    ("gaussian_noise", 3),
    ("gaussian_noise", 4),
    ("gaussian_noise", 5),
    ("brightness", 5),
]
KAPPA = 0.1          # single OKS falloff constant (see header)
OKS_PASS = 0.85      # negligibility criterion, stated in header
CONF_DROP_PASS = 0.10

CSV_FIELDS = [
    "video_id", "category", "condition", "severity",
    "n_frames", "n_compared_frames",
    "mean_px_dev", "oks", "conf_drop",
]


def enumerate_test_videos() -> dict:
    """{category: sorted [video_id]} from the UCF test PNG tree, filtered to
    videos whose clean skeleton cache exists."""
    by_cat: dict = {}
    for cat_dir in sorted(p for p in UCF_TEST_ROOT.iterdir() if p.is_dir()):
        vids = set()
        for png in cat_dir.glob("*_x264_*.png"):
            vids.add(png.name.rsplit("_x264_", 1)[0])
        kept = sorted(v for v in vids if (CLEAN_SKELETON_DIR / f"{v}.pkl").exists())
        if kept:
            by_cat[cat_dir.name] = kept
    return by_cat


def stratified_sample(by_cat: dict, target: int = TARGET_SAMPLE) -> list:
    """Proportional allocation, min 1 per category, numpy default_rng(0)."""
    rng = np.random.default_rng(0)
    total = sum(len(v) for v in by_cat.values())
    sample = []
    for cat in sorted(by_cat):
        vids = by_cat[cat]
        n = max(1, round(target * len(vids) / total))
        n = min(n, len(vids))
        picked = rng.choice(len(vids), size=n, replace=False)
        sample.extend((cat, vids[i]) for i in sorted(picked))
    return sample


def _existing_rows(csv_path: Path) -> set:
    """(video_id, condition, severity) keys already in the CSV (resume)."""
    if not csv_path.exists():
        return set()
    with open(csv_path, newline="") as f:
        return {
            (r["video_id"], r["condition"], int(r["severity"]))
            for r in csv.DictReader(f)
        }


def _frame_metrics(kp_clean, sc_clean, kp_corr, sc_corr):
    """Metrics for ONE frame: best over the two person-slot assignments.

    Returns (px_dev, oks, conf_clean, conf_corr) or None if the clean frame
    has no detected joints.
    """
    best = None
    for perm in ((0, 1), (1, 0)):
        devs, okss, cc, co = [], [], [], []
        for p_clean, p_corr in ((0, perm[0]), (1, perm[1])):
            valid = sc_clean[p_clean] > 0
            if not valid.any():
                continue
            c = kp_clean[p_clean][valid]
            r = kp_corr[p_corr][valid]
            d = np.linalg.norm(c - r, axis=1)
            w = max(float(c[:, 0].max() - c[:, 0].min()), 1.0)
            h = max(float(c[:, 1].max() - c[:, 1].min()), 1.0)
            s2 = w * h  # bbox area = (sqrt(w*h))^2
            oks = float(np.mean(np.exp(-(d ** 2) / (2.0 * s2 * KAPPA ** 2))))
            devs.append(float(d.mean()))
            okss.append(oks)
            cc.append(float(sc_clean[p_clean][valid].mean()))
            co.append(float(sc_corr[p_corr][valid].mean()))
        if not okss:
            return None
        cand = (
            float(np.mean(devs)), float(np.mean(okss)),
            float(np.mean(cc)), float(np.mean(co)),
        )
        if best is None or cand[1] > best[1]:  # keep the higher-OKS assignment
            best = cand
    return best


def measure_video(video_id: str, condition: str, severity: int) -> dict | None:
    """Corrupt frames in-memory, run RTMPose, compare vs the clean cache."""
    # Heavy imports deferred so --list-only works without rtmlib/onnxruntime.
    from extract_skeletons import load_ucf_frames, process_frames_to_keypoints

    # Security note: pickle is safe here -- these are the project's OWN clean
    # skeleton cache files written by scripts/extract_skeletons.py (PYSKL
    # pickle format is the established project-wide convention; no untrusted
    # input is ever loaded through this path).
    with open(CLEAN_SKELETON_DIR / f"{video_id}.pkl", "rb") as f:
        clean = pickle.load(f)
    kp_clean_all = clean["keypoint"]        # [2, T, 17, 2] pixel coords
    sc_clean_all = clean["keypoint_score"]  # [2, T, 17]

    rng = np.random.default_rng(42)  # mirrors extract_skeletons corruption mode
    frames, img_shape = load_ucf_frames(
        video_id, corruption_type=condition,
        corruption_severity=severity, corruption_rng=rng,
    )
    kp_corr_all, sc_corr_all = process_frames_to_keypoints(frames, img_shape)

    t_clean = kp_clean_all.shape[1]
    t_corr = kp_corr_all.shape[1]
    if t_clean != t_corr:
        print(f"  [warn] {video_id}: frame count clean={t_clean} corr={t_corr}; "
              f"comparing the first {min(t_clean, t_corr)} frames")
    t = min(t_clean, t_corr)

    devs, okss, drops, n_cmp = [], [], [], 0
    for f_idx in range(t):
        m = _frame_metrics(
            kp_clean_all[:, f_idx], sc_clean_all[:, f_idx],
            kp_corr_all[:, f_idx], sc_corr_all[:, f_idx],
        )
        if m is None:
            continue  # clean extraction detected nobody in this frame
        px, oks, conf_c, conf_r = m
        devs.append(px)
        okss.append(oks)
        drops.append(conf_c - conf_r)
        n_cmp += 1

    if n_cmp == 0:
        print(f"  [warn] {video_id}: no comparable frames (no clean detections)")
        return None
    return {
        "n_frames": t,
        "n_compared_frames": n_cmp,
        "mean_px_dev": round(float(np.mean(devs)), 4),
        "oks": round(float(np.mean(okss)), 4),
        "conf_drop": round(float(np.mean(drops)), 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--list-only", action="store_true",
        help="Enumerate the stratified sample and exit (NO inference, no rtmlib import).",
    )
    parser.add_argument("--out", default=str(OUT_CSV))
    args = parser.parse_args()

    by_cat = enumerate_test_videos()
    sample = stratified_sample(by_cat)
    print(f"Stratified sample: {len(sample)} videos across {len(by_cat)} categories")
    for cat in sorted(by_cat):
        n = sum(1 for c, _ in sample if c == cat)
        print(f"  {cat:15s} {n:3d} of {len(by_cat[cat])}")
    print(f"Conditions: {CONDITIONS}")
    print(f"Criterion: PASS iff mean OKS >= {OKS_PASS} AND mean conf drop <= {CONF_DROP_PASS}")

    if args.list_only:
        for cat, vid in sample:
            print(f"  [sample] {cat}/{vid}")
        print(f"[list-only] {len(sample)} videos x {len(CONDITIONS)} conditions "
              f"= {len(sample) * len(CONDITIONS)} measurements; exiting without inference.")
        return 0

    out_csv = Path(args.out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    done = _existing_rows(out_csv)
    new_file = not out_csv.exists()
    with open(out_csv, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        for cat, vid in sample:
            for cond, sev in CONDITIONS:
                if (vid, cond, sev) in done:
                    print(f"[skip] {vid} {cond}_{sev} (row exists)")
                    continue
                print(f"[run ] {vid} {cond}_{sev}")
                m = measure_video(vid, cond, sev)
                if m is None:
                    continue
                writer.writerow({
                    "video_id": vid, "category": cat,
                    "condition": cond, "severity": sev, **m,
                })
                f.flush()

    # Per-condition summary + PASS/FAIL readout
    with open(out_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    print("\n=== Per-condition summary ===")
    print(f"(criterion: PASS iff mean OKS >= {OKS_PASS} AND mean conf drop <= {CONF_DROP_PASS})")
    for cond, sev in CONDITIONS:
        sub = [r for r in rows if r["condition"] == cond and int(r["severity"]) == sev]
        if not sub:
            print(f"  {cond}_{sev}: no rows")
            continue
        oks = float(np.mean([float(r["oks"]) for r in sub]))
        drop = float(np.mean([float(r["conf_drop"]) for r in sub]))
        dev = float(np.mean([float(r["mean_px_dev"]) for r in sub]))
        verdict = "PASS" if (oks >= OKS_PASS and drop <= CONF_DROP_PASS) else "FAIL"
        print(f"  {cond}_{sev}: n={len(sub)} mean_px_dev={dev:.3f} "
              f"OKS={oks:.4f} conf_drop={drop:.4f} -> {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
