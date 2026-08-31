"""THROWAWAY de-risk probe (TTA-boost investigation, 2026-06-07).

Question: BEFORE committing ~30h to val-C extraction, will a held-out-tuned
shrunk-CORAL feature restoration give NET-POSITIVE corrupted frame-AUC?

We answer it using ONLY data already on disk (test-C + clean-train features),
by simulating the val->test transfer two ways:

  * oracle_fixed_beta : best single beta picked by peeking at test frame-AUC
                        (the ceiling; what the deleted throwaway probes reported).
  * loco_frame        : leave-one-corruption-out CV. Pick beta on 3 families by
                        FRAME-AUC, evaluate held-out 4th family. Tests whether a
                        fixed per-backbone beta generalises across corruptions.
  * loco_video        : same LOCO, but pick beta by VIDEO-level AUC (the ONLY
                        signal a real val-C set can give us, since val has no
                        frame annotations). THIS is the honest predictor of the
                        real val-C -> test-C pipeline.

shrunk-CORAL: whiten corrupted-test features, recolor to clean-TRAIN mean+cov.
  C_b = (1-b)*C_emp + b*diag(C_emp)          # b=1 -> diagonal (==NORM), b=0 -> full CORAL
  W   = C_t_b^{-1/2} @ C_s_b^{1/2}
  x'  = (x - mu_t) @ W + mu_s
Source stats from clean TRAIN. Test stats transductive over the WHOLE condition.
Applied to the VL (clip) stream always; to the skeleton stream only for
motion_blur/jpeg (gaussian/brightness reuse the clean skeleton cache).

Reuses evaluate_tta helpers so source_only reproduces the canonical baseline.
Not committed via GSD: this is an exploratory probe (like the prior _tmp_*).
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import time
from copy import deepcopy
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.eval.metrics import compute_frame_metrics
from src.eval.snippet_to_frame import snippet_to_frame
from src.eval.ucf_annotations import frame_labels, parse_annotations
from src.models.registry import build_model
from src.tta.tent import configure_model
from src.utils.checkpoint import load_checkpoint
from src.utils.config import load_snapshot_as_config
from src.tta.evaluate_tta import (
    _SourceOnlyAdaptor,
    _adapt_one_video,
    _load_test_video_features,
    BACKBONE_FEATURE_PREFIX,
    BACKBONE_SOURCE_RUNS,
    SKELETON_REEXTRACT_TYPES,
)

CORRUPTIONS = ("gaussian_noise", "jpeg_compression", "brightness", "motion_blur")
SEVERITIES = (1, 2, 3, 4, 5)
BETAS = (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.85, 1.0)
FEATURE_ROOT = Path("E:/features/ucf")
DEVICE = "cpu"  # tiny fusion head; avoids GPU contention across parallel backbones


# ----------------------------------------------------------------------------
# stats helpers (streaming covariance, float64)
# ----------------------------------------------------------------------------
def _accumulate(paths_or_arrays, load):
    n = 0
    s = None
    ss = None
    for item in paths_or_arrays:
        x = load(item)
        if x is None or x.shape[0] == 0:
            continue
        x = x.astype(np.float64)
        if s is None:
            d = x.shape[1]
            s = np.zeros(d)
            ss = np.zeros((d, d))
        s += x.sum(0)
        ss += x.T @ x
        n += x.shape[0]
    mu = s / n
    cov = ss / n - np.outer(mu, mu)
    return mu, cov, n


def _clean_train_stats(prefix, split_ids, stream):
    """mean+cov over clean-TRAIN snippets for one stream."""
    if stream == "clip":
        d = FEATURE_ROOT / prefix
    else:
        d = FEATURE_ROOT / "skeleton"

    def load(vid):
        p = d / f"{vid}.npy"
        return np.load(str(p)) if p.exists() else None

    return _accumulate(split_ids, load)


def _sym_sqrt(C, inv=False, floor_rel=1e-8):
    w, V = np.linalg.eigh(C)
    fl = max(w.max() * floor_rel, 1e-12)
    w = np.clip(w, fl, None)
    s = 1.0 / np.sqrt(w) if inv else np.sqrt(w)
    return (V * s) @ V.T


def _shrink(C, beta, ridge_rel=1e-6):
    d = np.diag(np.diag(C))
    Cb = (1.0 - beta) * C + beta * d
    Cb = Cb + np.eye(Cb.shape[0]) * (ridge_rel * np.trace(Cb) / Cb.shape[0])
    return Cb


def _coral_W(mu_t, C_t, mu_s, C_s, beta):
    Ctb = _shrink(C_t, beta)
    Csb = _shrink(C_s, beta)
    W = _sym_sqrt(Ctb, inv=True) @ _sym_sqrt(Csb, inv=False)
    return W  # x' = (x - mu_t) @ W + mu_s


def _apply(x, mu_t, mu_s, W):
    return ((x.astype(np.float64) - mu_t) @ W + mu_s).astype(np.float32)


# ----------------------------------------------------------------------------
# scoring
# ----------------------------------------------------------------------------
def _video_score(snip_scores):
    k = max(1, int(np.ceil(0.1 * len(snip_scores))))
    return float(np.mean(np.sort(snip_scores)[-k:]))


def _score_condition(adaptor, skels, clips, vids, annos):
    """Return (frame_auc, video_auc) given (already-transformed) feats."""
    frames_map, labels_map, cats_map = {}, {}, {}
    vid_scores, vid_labels = [], []
    for vid in vids:
        scores = _adapt_one_video(adaptor, skels[vid], clips[vid],
                                  "source_only", DEVICE, reset=False)
        n_frames = len(scores) * 64 * 10
        frames_map[vid] = snippet_to_frame(scores, n_frames, snippet_window=64,
                                            upsample_factor=10)
        if vid in annos:
            labels_map[vid] = frame_labels(annos[vid], n_frames)
            cats_map[vid] = annos[vid].category
        else:
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
            cats_map[vid] = "Normal"
        vid_scores.append(_video_score(scores))
        vid_labels.append(0 if vid.startswith("Normal") else 1)
    m = compute_frame_metrics(frames_map, labels_map, cats_map)
    vauc = roc_auc_score(vid_labels, vid_scores)
    return float(m["auc"]) * 100.0, float(vauc) * 100.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True, choices=list(BACKBONE_FEATURE_PREFIX))
    ap.add_argument("--out", required=True)
    ap.add_argument("--conditions", type=int, default=0,
                    help="0=all; else cap #conditions for smoke test")
    ap.add_argument("--severities", type=str, default="1,2,3,4,5",
                    help="comma list of severities to run")
    ap.add_argument("--betas", type=str, default="",
                    help="comma list of betas (override default grid)")
    args = ap.parse_args()

    global BETAS
    if args.betas:
        BETAS = tuple(float(x) for x in args.betas.split(","))
    sevs = tuple(int(x) for x in args.severities.split(","))

    torch.manual_seed(0)
    np.random.seed(0)
    t0 = time.time()
    bb = args.backbone
    prefix = BACKBONE_FEATURE_PREFIX[bb]

    # model
    src_run = _ROOT / "results" / BACKBONE_SOURCE_RUNS[bb]
    cfg = load_snapshot_as_config(src_run / "config_snapshot.json")
    model = build_model(**cfg["model"]).to(DEVICE)
    state = load_checkpoint(src_run / "best_model.pth", device=DEVICE)
    sd = state.get("model", state) if isinstance(state, dict) else state
    model.load_state_dict(sd, strict=True)
    source_state = deepcopy(model.state_dict())
    configure_model(model)
    adaptor = _SourceOnlyAdaptor(model, source_state)

    annos = parse_annotations(_ROOT / "data" / "annotations" / "ucf_temporal.txt")
    train_ids = [l.strip() for l in (_ROOT / "data/splits/ucf_train.txt").read_text().splitlines() if l.strip()]
    test_ids = [l.strip() for l in (_ROOT / "data/splits/ucf_test.txt").read_text().splitlines() if l.strip()]

    print(f"[{bb}] clean-train source stats...", flush=True)
    mu_s_clip, C_s_clip, n_clip = _clean_train_stats(prefix, train_ids, "clip")
    mu_s_skel, C_s_skel, n_skel = _clean_train_stats(prefix, train_ids, "skel")
    print(f"[{bb}] src clip {C_s_clip.shape} n={n_clip} | skel n={n_skel} "
          f"({time.time()-t0:.0f}s)", flush=True)

    conds = [(c, s) for c in CORRUPTIONS for s in sevs]
    if args.conditions:
        conds = conds[: args.conditions]

    per_condition = {}
    for ci, (ctype, sev) in enumerate(conds):
        tc = time.time()
        skels, clips, vids = {}, {}, []
        for vid in test_ids:
            sk, cl = _load_test_video_features(vid, ctype, sev, FEATURE_ROOT, backbone=bb)
            if sk is None:
                continue
            skels[vid] = sk
            clips[vid] = cl
            vids.append(vid)
        skel_corrupt = ctype in SKELETON_REEXTRACT_TYPES

        # transductive test stats over the whole condition
        mu_t_clip, C_t_clip, _ = _accumulate(vids, lambda v: clips[v])
        if skel_corrupt:
            mu_t_skel, C_t_skel, _ = _accumulate(vids, lambda v: skels[v])

        key = f"{ctype}_{sev}"
        rec = {"n_videos": len(vids), "auc_by_beta": {}, "vauc_by_beta": {}}

        # source_only (identity, no transform)
        f0, v0 = _score_condition(adaptor, skels, clips, vids, annos)
        rec["source_only_auc"] = f0
        rec["source_only_vauc"] = v0

        for beta in BETAS:
            W_clip = _coral_W(mu_t_clip, C_t_clip, mu_s_clip, C_s_clip, beta)
            tclips = {v: _apply(clips[v], mu_t_clip, mu_s_clip, W_clip) for v in vids}
            if skel_corrupt:
                W_skel = _coral_W(mu_t_skel, C_t_skel, mu_s_skel, C_s_skel, beta)
                tskels = {v: _apply(skels[v], mu_t_skel, mu_s_skel, W_skel) for v in vids}
            else:
                tskels = skels  # clean skeleton untouched
            f, v = _score_condition(adaptor, tskels, tclips, vids, annos)
            rec["auc_by_beta"][f"{beta:.2f}"] = f
            rec["vauc_by_beta"][f"{beta:.2f}"] = v

        per_condition[key] = rec
        best_b = max(rec["auc_by_beta"], key=rec["auc_by_beta"].get)
        print(f"[{bb}] {ci+1}/{len(conds)} {key} src={f0:.2f} "
              f"best_b={best_b} dAUC={rec['auc_by_beta'][best_b]-f0:+.2f} "
              f"({time.time()-tc:.0f}s)", flush=True)

    # ------------------------------------------------------------------
    # analysis
    # ------------------------------------------------------------------
    betas = [f"{b:.2f}" for b in BETAS]
    all_keys = list(per_condition)

    def mean_auc(keys, b):
        return float(np.mean([per_condition[k]["auc_by_beta"][b] for k in keys]))

    def mean_vauc(keys, b):
        return float(np.mean([per_condition[k]["vauc_by_beta"][b] for k in keys]))

    def mean_src(keys):
        return float(np.mean([per_condition[k]["source_only_auc"] for k in keys]))

    src_mean = mean_src(all_keys)

    # oracle: single beta maximising mean frame-AUC over ALL conditions
    oracle_b = max(betas, key=lambda b: mean_auc(all_keys, b))
    oracle = {"beta": oracle_b, "frame_delta": mean_auc(all_keys, oracle_b) - src_mean}

    # LOCO
    def loco(select_fn):
        folds = []
        for fam in CORRUPTIONS:
            held = [k for k in all_keys if k.startswith(fam)]
            train = [k for k in all_keys if not k.startswith(fam)]
            if not held or not train:
                continue
            b = max(betas, key=lambda bb_: select_fn(train, bb_))
            delta = mean_auc(held, b) - mean_src(held)
            folds.append({"family": fam, "beta": b, "heldout_frame_delta": delta})
        return {"folds": folds, "mean_delta": float(np.mean([f["heldout_frame_delta"] for f in folds]))}

    loco_frame = loco(mean_auc)
    loco_video = loco(mean_vauc)

    out = {
        "backbone": bb,
        "betas": betas,
        "source_only_frame_auc_mean": src_mean,
        "per_condition": per_condition,
        "oracle_fixed_beta": oracle,
        "loco_frame": loco_frame,
        "loco_video": loco_video,
        "elapsed_s": round(time.time() - t0, 1),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"[{bb}] DONE src={src_mean:.2f} oracle={oracle['frame_delta']:+.2f} "
          f"loco_frame={loco_frame['mean_delta']:+.2f} "
          f"loco_video={loco_video['mean_delta']:+.2f} -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
