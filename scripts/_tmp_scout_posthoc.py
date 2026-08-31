# Scout experiment: post-hoc score smoothing + seed/backbone ensembling on saved frame scores.
# Read-only w.r.t. results; prints AUC/AP deltas. NOT a production script.
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

from src.eval.ucf_annotations import parse_annotations, frame_labels
from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels


def load_scores(run):
    d = np.load(ROOT / "results" / run / "eval_scores.npz")
    return {k: d[k] for k in d.files}


def ucf_labels(frames_map):
    annos = parse_annotations(ROOT / "data" / "annotations" / "ucf_temporal.txt")
    labels = {}
    for vid, s in frames_map.items():
        n = len(s)
        if vid in annos:
            labels[vid] = frame_labels(annos[vid], n)
        else:
            labels[vid] = np.zeros(n, dtype=np.int64)
    return labels


def xd_labels(frames_map):
    annos = parse_xd_annotations(ROOT / "data" / "annotations" / "xd_temporal.txt")
    labels = {}
    for vid, s in frames_map.items():
        n = len(s)
        if vid in annos:
            labels[vid] = xd_frame_labels(annos[vid], n)
        else:
            labels[vid] = np.zeros(n, dtype=np.int64)
    return labels


def metric(frames_map, labels_map, kind):
    vids = sorted(frames_map.keys())
    y = np.concatenate([labels_map[v] for v in vids])
    s = np.concatenate([frames_map[v] for v in vids])
    if kind == "auc":
        return roc_auc_score(y, s)
    return average_precision_score(y, s)


def smooth(frames_map, w):
    """Per-video centered moving average, window w frames."""
    out = {}
    kern = np.ones(w, dtype=np.float64) / w
    for vid, s in frames_map.items():
        if len(s) < 2:
            out[vid] = s
            continue
        pad = w // 2
        sp = np.pad(s.astype(np.float64), pad, mode="edge")
        sm = np.convolve(sp, kern, mode="same")[pad:pad + len(s)]
        out[vid] = sm
    return out


def ens(maps):
    """Average several frames_maps; truncate to common length per video."""
    out = {}
    for vid in maps[0]:
        arrs = [m[vid] for m in maps]
        n = min(len(a) for a in arrs)
        out[vid] = np.mean([a[:n].astype(np.float64) for a in arrs], axis=0)
    return out


def main():
    print("=" * 70)
    print("UCF (metric: AUC). Headline = gated_fusion GIANT 3-seed mean 0.8254")
    print("=" * 70)
    giant_runs = ["ucf_gated_fusion_giant_s42", "ucf_gated_fusion_giant_s123", "ucf_gated_fusion_giant_s2024"]
    g_maps = [load_scores(r) for r in giant_runs]
    lab = ucf_labels(g_maps[0])
    base = [metric(m, lab, "auc") for m in g_maps]
    print("baseline per-seed:", [round(a, 4) for a in base], "mean %.4f" % np.mean(base))

    for w in [320, 640, 1280, 1920, 2560, 3840]:
        sm = [metric(smooth(m, w), lab, "auc") for m in g_maps]
        print(f"smooth w={w:5d} frames: per-seed", [round(a, 4) for a in sm], "mean %.4f (delta %+0.4f)" % (np.mean(sm), np.mean(sm) - np.mean(base)))

    e = ens(g_maps)
    print("3-seed ensemble (giant): %.4f (delta vs seed-mean %+0.4f)" % (metric(e, lab, "auc"), metric(e, lab, "auc") - np.mean(base)))
    e_sm = smooth(e, 1280)
    print("3-seed ensemble + smooth w=1280: %.4f" % metric(e_sm, lab, "auc"))

    # backbone ensemble, matched seed 42
    bb_runs = ["ucf_gated_fusion_giant_s42", "ucf_gated_fusion_so400m_s42", "ucf_gated_fusion_s42", "ucf_gated_fusion_siglip2_s42"]
    bb = [load_scores(r) for r in bb_runs]
    e2 = ens(bb)
    lab2 = ucf_labels(e2)
    print("4-backbone ensemble (s42): %.4f" % metric(e2, lab2, "auc"))
    e3 = ens(bb[:2])
    print("giant+so400m ensemble (s42): %.4f" % metric(e3, ucf_labels(e3), "auc"))
    # all 12 (4 backbones x 3 seeds)
    all_runs = []
    for b in ["giant_", "so400m_", "", "siglip2_"]:
        for s in ["s42", "s123", "s2024"]:
            all_runs.append(f"ucf_gated_fusion_{b}{s}")
    am = [load_scores(r) for r in all_runs]
    ea = ens(am)
    print("12-run (4bb x 3seed) ensemble: %.4f" % metric(ea, ucf_labels(ea), "auc"))

    print()
    print("=" * 70)
    print("XD (metric: AP). Headline = gated_fusion SO400M 3-seed mean 0.7872")
    print("=" * 70)
    so_runs = ["xd_gated_fusion_so400m_s42", "xd_gated_fusion_so400m_s123", "xd_gated_fusion_so400m_s2024"]
    x_maps = [load_scores(r) for r in so_runs]
    xlab = xd_labels(x_maps[0])
    xbase = [metric(m, xlab, "ap") for m in x_maps]
    print("baseline per-seed:", [round(a, 4) for a in xbase], "mean %.4f" % np.mean(xbase))

    for w in [64, 128, 256, 512, 768, 1024]:
        sm = [metric(smooth(m, w), xlab, "ap") for m in x_maps]
        print(f"smooth w={w:5d} frames: per-seed", [round(a, 4) for a in sm], "mean %.4f (delta %+0.4f)" % (np.mean(sm), np.mean(sm) - np.mean(xbase)))

    e = ens(x_maps)
    print("3-seed ensemble (so400m): AP %.4f (delta vs seed-mean %+0.4f)" % (metric(e, xlab, "ap"), metric(e, xlab, "ap") - np.mean(xbase)))
    e_sm = smooth(e, 256)
    print("3-seed ensemble + smooth w=256: AP %.4f" % metric(e_sm, xlab, "ap"))

    bb_runs = ["xd_gated_fusion_so400m_s42", "xd_gated_fusion_giant_s42", "xd_gated_fusion_s42", "xd_gated_fusion_siglip2_s42"]
    bb = [load_scores(r) for r in bb_runs]
    e2 = ens(bb)
    xlab2 = xd_labels(e2)
    print("4-backbone ensemble (s42): AP %.4f" % metric(e2, xlab2, "ap"))
    e3 = ens(bb[:2])
    print("so400m+giant ensemble (s42): AP %.4f" % metric(e3, xd_labels(e3), "ap"))
    all_runs = []
    for b in ["so400m_", "giant_", "", "siglip2_"]:
        for s in ["s42", "s123", "s2024"]:
            all_runs.append(f"xd_gated_fusion_{b}{s}")
    am = [load_scores(r) for r in all_runs]
    ea = ens(am)
    print("12-run (4bb x 3seed) ensemble: AP %.4f" % metric(ea, xd_labels(ea), "ap"))


if __name__ == "__main__":
    main()
