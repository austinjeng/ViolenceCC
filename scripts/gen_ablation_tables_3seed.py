"""Generate 3-seed mean+/-std ablation table bodies (Tables 1 & 2) from results-index.csv.

Emits LaTeX rows in the exact paper format and prints, for the rows that are ALREADY
3-seed in the paper (Visual Only, Gated Fusion), the recomputed values so they can be
eyeball-matched against main.tex as a correctness check before editing.

CPU-only, read-only. Run from repo root with the vcc-main python.
"""
from __future__ import annotations

import csv
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

INDEX = Path("results/results-index.csv")
SEEDS = (42, 123, 2024)
SUFFIX = re.compile(r"_s(42|123|2024)$")

BACKBONES = [  # display name, run_name infix
    ("CLIP ViT-B/16", ""),
    ("SigLIP2 Base", "_siglip2"),
    ("SigLIP2 SO400M", "_so400m"),
    ("SigLIP2 Giant", "_giant"),
]

# variant display -> (run_name template using {ds} and {bb}); SKEL handled separately
VARIANTS = [
    ("Visual Only", "{ds}_clip_only{bb}"),
    ("Late Fusion", "{ds}_late_fusion{bb}"),
    ("Gated Fusion", "{ds}_gated_fusion{bb}"),
    ("GF 2-Person", "{ds}_gated_fusion{bb}_2person"),
    ("GF Mean-Only", "{ds}_gated_fusion{bb}_clip_mean"),
]


def load():
    rows = defaultdict(dict)  # base -> seed -> {auc, ap}
    with open(INDEX, newline="") as f:
        for r in csv.DictReader(f):
            m = SUFFIX.search(r["run_name"])
            if not m:
                continue
            base = SUFFIX.sub("", r["run_name"])
            seed = int(m.group(1))
            if seed not in SEEDS:
                continue
            try:
                rows[base][seed] = {"auc": float(r["auc"]), "ap": float(r["ap"])}
            except (ValueError, KeyError):
                pass
    return rows


def cell(rows, base, metric):
    """Return (mean, std, n) in % or None."""
    sm = rows.get(base, {})
    vals = [sm[s][metric] * 100 for s in SEEDS if s in sm]
    if not vals:
        return None
    mean = st.mean(vals)
    std = st.stdev(vals) if len(vals) >= 2 else 0.0
    return mean, std, len(vals)


def fmt_cell(c, bold=False, show_std=True):
    if c is None:
        return "---"
    mean, std, n = c
    s = f"{mean:.1f}$\\pm${std:.1f}" if show_std else f"{mean:.1f}"
    return f"\\textbf{{{s}}}" if bold else s


def emit(ds, metric, label):
    rows = ROWS
    print(f"\n===== {label} ({metric.upper()}) =====")
    # Skeleton Only (single model, CLIP column only)
    sk = cell(rows, f"{ds}_skeleton_only", metric)
    print(f"Skeleton Only & {fmt_cell(sk, bold=True)} & --- & --- & --- & --- \\\\")
    print("\\midrule  % (Visual Only sits above this midrule in the paper)")
    for vname, tmpl in VARIANTS:
        cells = [cell(rows, tmpl.format(ds=ds, bb=bb), metric) for _, bb in BACKBONES]
        means = [c[0] if c else None for c in cells]
        best_i = max((i for i in range(4) if means[i] is not None),
                     key=lambda i: means[i], default=None)
        cell_strs = [fmt_cell(cells[i], bold=(i == best_i)) for i in range(4)]
        # Best Delta = best - CLIP(col0)
        if best_i is not None and means[0] is not None:
            delta = means[best_i] - means[0]
            dstr = f"$\\uparrow$+{delta:.1f}" if delta >= 0 else f"$\\downarrow${delta:.1f}"
        else:
            dstr = "---"
        print(f"{vname} & {cell_strs[0]} & {cell_strs[1]} & {cell_strs[2]} & {cell_strs[3]} & {dstr} \\\\")
        # provenance line
        prov = "  % " + " | ".join(
            f"{BACKBONES[i][0].split()[-1]}:{means[i]:.2f}" if means[i] is not None else f"{BACKBONES[i][0].split()[-1]}:--"
            for i in range(4)
        )
        print(prov)


ROWS = load()
emit("ucf", "auc", "Table 1: UCF-Crime")
emit("xd", "ap", "Table 2: XD-Violence")

print("\n===== CHECK: rows already 3-seed in paper (should match main.tex) =====")
for ds, metric in (("ucf", "auc"), ("xd", "ap")):
    for vname, tmpl in (("Visual Only", "{ds}_clip_only{bb}"), ("Gated Fusion", "{ds}_gated_fusion{bb}")):
        line = [f"{ds} {vname}:"]
        for bbname, bb in BACKBONES:
            c = cell(ROWS, tmpl.format(ds=ds, bb=bb), metric)
            line.append(f"{bbname.split()[-1]}={c[0]:.1f}±{c[1]:.1f}" if c else f"{bbname.split()[-1]}=--")
        print("  " + "  ".join(line))
