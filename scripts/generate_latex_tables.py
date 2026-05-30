"""Generate LaTeX tables from CSV result data for CGW '26 paper.

Reads backbone_comparison_4way.csv, seed_stability_4way.csv, and
tta_backbone/summary.csv to produce three publication-ready tables
with booktabs formatting, bold-best-per-row, and delta arrows.

Outputs to stdout and paper/tables_generated.tex.
"""

import csv
import sys
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def fmt_pct(val, bold=False):
    """Format a float as XX.X, optionally bold."""
    s = f"{val * 100:.1f}"
    return f"\\textbf{{{s}}}" if bold else s


def fmt_pct_raw(val):
    """Format already-in-percent float as XX.X."""
    return f"{val:.1f}"


def fmt_delta(val):
    """Format delta with arrow: up+X.X or down-X.X."""
    pct = val * 100
    if pct > 0:
        return f"$\\uparrow${pct:+.1f}"
    elif pct < 0:
        return f"$\\downarrow${pct:.1f}"
    else:
        return "0.0"


def fmt_mean_std(values, bold=False):
    """Format mean+-std from a list of floats, as XX.X+-Y.Y."""
    m = statistics.mean(values)
    s = statistics.stdev(values) if len(values) > 1 else 0.0
    m_str = f"{m * 100:.1f}"
    s_str = f"{s * 100:.1f}"
    core = f"{m_str}$\\pm${s_str}"
    return f"\\textbf{{{core}}}" if bold else core


def generate_table1_ucf(rows, seeds):
    """Table 1: UCF-Crime Ablation (AUC as primary metric)."""
    ucf = [r for r in rows if r["Dataset"] == "UCF"]
    ucf_seeds = [r for r in seeds if r["Dataset"] == "UCF"]

    # For each variant, collect AUC across 4 backbones
    variants = [
        ("Skeleton Only", "Skeleton Only"),
        ("Visual Only", "CLIP/SigLIP2/SO400M/Giant Only"),
        ("Late Fusion", "Late Fusion"),
        ("Gated Fusion", "Gated Fusion"),
        ("GF 2-Person", "GF 2-Person"),
        ("GF Mean-Only", "GF Mean-Only"),
    ]

    backbone_keys = [
        ("CLIP_AUC", "CLIP"),
        ("SigLIP2_AUC", "SigLIP2"),
        ("SO400M_AUC", "SO400M"),
        ("Giant_AUC", "Giant"),
    ]

    # Seed data for Gated Fusion mean+-std
    seed_vals = {}
    for bk, bname in backbone_keys:
        seed_vals[bk] = [float(s[bk]) for s in ucf_seeds]

    lines = []
    lines.append("% Table 1: UCF-Crime Ablation Results (AUC)")
    lines.append("\\begin{table*}[t]")
    lines.append("\\caption{Ablation study on UCF-Crime. AUC (\\%) reported for each fusion variant across four visual backbones. Gated Fusion rows show mean$\\pm$std over three seeds (42, 123, 2024). Best result per row in \\textbf{bold}. $\\Delta$ relative to CLIP ViT-B/16 baseline.}")
    lines.append("\\label{tab:ucf-ablation}")
    lines.append("\\begin{tabular}{l c c c c c}")
    lines.append("\\toprule")
    lines.append("Variant & CLIP ViT-B/16 & SigLIP2 Base & SigLIP2 SO400M & SigLIP2 Giant & Best $\\Delta$ \\\\")
    lines.append("\\midrule")

    for display_name, csv_name in variants:
        row = [r for r in ucf if r["Variant"] == csv_name][0]

        if csv_name == "Skeleton Only":
            clip_val = float(row["CLIP_AUC"])
            cells = [fmt_pct(clip_val, bold=True), "---", "---", "---", "---"]
            lines.append(f"{display_name} & " + " & ".join(cells) + " \\\\")
            continue

        vals = []
        for bk, _ in backbone_keys:
            v = row[bk]
            vals.append(float(v) if v else None)

        # Find best (max AUC)
        valid = [(v, i) for i, v in enumerate(vals) if v is not None]
        best_idx = max(valid, key=lambda x: x[0])[1] if valid else -1

        # For Gated Fusion, use mean+-std
        if csv_name == "Gated Fusion":
            cells = []
            means = []
            for i, (bk, _) in enumerate(backbone_keys):
                sv = seed_vals[bk]
                m = statistics.mean(sv)
                means.append((m, i))
            best_seed_idx = max(means, key=lambda x: x[0])[1]
            for i, (bk, _) in enumerate(backbone_keys):
                cells.append(fmt_mean_std(seed_vals[bk], bold=(i == best_seed_idx)))
        else:
            cells = []
            for i, v in enumerate(vals):
                if v is None:
                    cells.append("---")
                else:
                    cells.append(fmt_pct(v, bold=(i == best_idx)))

        # Delta: best vs CLIP
        clip_v = vals[0]
        best_v = max(v for v in vals if v is not None)
        if csv_name == "Gated Fusion":
            clip_mean = statistics.mean(seed_vals["CLIP_AUC"])
            best_mean = max(statistics.mean(seed_vals[bk]) for bk, _ in backbone_keys)
            delta = best_mean - clip_mean
        else:
            delta = best_v - clip_v if clip_v is not None else 0

        delta_str = fmt_delta(delta)
        cells.append(delta_str)

        lines.append(f"{display_name} & " + " & ".join(cells) + " \\\\")

        # Add midrule after Visual Only
        if csv_name == "CLIP/SigLIP2/SO400M/Giant Only":
            lines.append("\\midrule")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")
    lines.append("")
    return "\n".join(lines)


def generate_table2_xd(rows, seeds):
    """Table 2: XD-Violence Ablation (AP as primary metric)."""
    xd = [r for r in rows if r["Dataset"] == "XD"]
    xd_seeds = [r for r in seeds if r["Dataset"] == "XD"]

    variants = [
        ("Skeleton Only", "Skeleton Only"),
        ("Visual Only", "CLIP/SigLIP2/SO400M/Giant Only"),
        ("Late Fusion", "Late Fusion"),
        ("Gated Fusion", "Gated Fusion"),
        ("GF 2-Person", "GF 2-Person"),
        ("GF Mean-Only", "GF Mean-Only"),
    ]

    backbone_keys = [
        ("CLIP_AP", "CLIP"),
        ("SigLIP2_AP", "SigLIP2"),
        ("SO400M_AP", "SO400M"),
        ("Giant_AP", "Giant"),
    ]

    seed_vals = {}
    for bk, _ in backbone_keys:
        seed_vals[bk] = [float(s[bk]) for s in xd_seeds]

    lines = []
    lines.append("% Table 2: XD-Violence Ablation Results (AP)")
    lines.append("\\begin{table*}[t]")
    lines.append("\\caption{Ablation study on XD-Violence. AP (\\%) reported for each fusion variant across four visual backbones. Gated Fusion rows show mean$\\pm$std over three seeds. Best result per row in \\textbf{bold}. $\\Delta$ relative to CLIP ViT-B/16 baseline.}")
    lines.append("\\label{tab:xd-ablation}")
    lines.append("\\begin{tabular}{l c c c c c}")
    lines.append("\\toprule")
    lines.append("Variant & CLIP ViT-B/16 & SigLIP2 Base & SigLIP2 SO400M & SigLIP2 Giant & Best $\\Delta$ \\\\")
    lines.append("\\midrule")

    for display_name, csv_name in variants:
        row = [r for r in xd if r["Variant"] == csv_name][0]

        if csv_name == "Skeleton Only":
            clip_val = float(row["CLIP_AP"])
            cells = [fmt_pct(clip_val, bold=True), "---", "---", "---", "---"]
            lines.append(f"{display_name} & " + " & ".join(cells) + " \\\\")
            continue

        vals = []
        for bk, _ in backbone_keys:
            v = row[bk]
            vals.append(float(v) if v else None)

        valid = [(v, i) for i, v in enumerate(vals) if v is not None]
        best_idx = max(valid, key=lambda x: x[0])[1] if valid else -1

        if csv_name == "Gated Fusion":
            cells = []
            means = []
            for i, (bk, _) in enumerate(backbone_keys):
                sv = seed_vals[bk]
                m = statistics.mean(sv)
                means.append((m, i))
            best_seed_idx = max(means, key=lambda x: x[0])[1]
            for i, (bk, _) in enumerate(backbone_keys):
                cells.append(fmt_mean_std(seed_vals[bk], bold=(i == best_seed_idx)))
        else:
            cells = []
            for i, v in enumerate(vals):
                if v is None:
                    cells.append("---")
                else:
                    cells.append(fmt_pct(v, bold=(i == best_idx)))

        clip_v = vals[0]
        best_v = max(v for v in vals if v is not None)
        if csv_name == "Gated Fusion":
            clip_mean = statistics.mean(seed_vals["CLIP_AP"])
            best_mean = max(statistics.mean(seed_vals[bk]) for bk, _ in backbone_keys)
            delta = best_mean - clip_mean
        else:
            delta = best_v - clip_v if clip_v is not None else 0

        delta_str = fmt_delta(delta)
        cells.append(delta_str)

        lines.append(f"{display_name} & " + " & ".join(cells) + " \\\\")

        if csv_name == "CLIP/SigLIP2/SO400M/Giant Only":
            lines.append("\\midrule")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")
    lines.append("")
    return "\n".join(lines)


def generate_table3_tta(tta_rows):
    """Table 3: TTA Results on UCF-Crime-C."""
    backbones = [
        ("clip-vit-b-16", "CLIP ViT-B/16"),
        ("siglip2-base", "SigLIP2 Base"),
        ("siglip2-so400m", "SigLIP2 SO400M"),
        ("siglip2-giant", "SigLIP2 Giant"),
    ]

    lines = []
    lines.append("% Table 3: TTA Results on UCF-Crime-C")
    lines.append("\\begin{table}[t]")
    lines.append("\\caption{Test-time adaptation results on UCF-Crime-C, averaged over 20 corruption conditions (4 types $\\times$ 5 severities). AUC (\\%) reported. Best method per backbone in \\textbf{bold}.}")
    lines.append("\\label{tab:tta}")
    lines.append("\\begin{tabular}{l c c c c}")
    lines.append("\\toprule")
    lines.append("Backbone & Source-Only & TENT & SAR & $\\Delta$ \\\\")
    lines.append("\\midrule")

    for bb_key, bb_name in backbones:
        bb_rows = [r for r in tta_rows if r["backbone"] == bb_key]
        source = [r for r in bb_rows if r["method"] == "source_only"][0]
        tent = [r for r in bb_rows if r["method"] == "tent"][0]
        sar = [r for r in bb_rows if r["method"] == "sar"][0]

        s_val = float(source["mean_auc"])
        t_val = float(tent["mean_auc"])
        r_val = float(sar["mean_auc"])

        vals = [s_val, t_val, r_val]
        best_idx = vals.index(max(vals))

        cells = []
        for i, v in enumerate(vals):
            cells.append(fmt_pct(v, bold=(i == best_idx)))

        # Delta: best - source
        delta = max(vals) - s_val
        delta_str = fmt_delta(delta)
        cells.append(delta_str)

        lines.append(f"{bb_name} & " + " & ".join(cells) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    lines.append("")
    return "\n".join(lines)


def main():
    comp_path = RESULTS / "phase10_charts" / "backbone_comparison_4way.csv"
    seed_path = RESULTS / "phase10_charts" / "seed_stability_4way.csv"
    tta_path = RESULTS / "tta_backbone" / "summary.csv"

    comp_rows = read_csv(comp_path)
    seed_rows = read_csv(seed_path)
    tta_rows = read_csv(tta_path)

    t1 = generate_table1_ucf(comp_rows, seed_rows)
    t2 = generate_table2_xd(comp_rows, seed_rows)
    t3 = generate_table3_tta(tta_rows)

    output = "\n".join([t1, t2, t3])
    print(output)

    out_path = ROOT / "paper" / "tables_generated.tex"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output + "\n")

    print(f"\n% Written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
