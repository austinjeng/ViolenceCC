"""Analyze TTA results to find best TENT and SAR configurations.

Reads all results/tta/*/eval_metrics.json files, computes mean AUC across
all 20 conditions (4 corruption types x 5 severities) for each (method, lr,
rho) combination, and outputs the winning configs.

Usage:
    python scripts/analyze_tta_best.py
    python scripts/analyze_tta_best.py --results-root results
    python scripts/analyze_tta_best.py --all-backbones

Outputs:
    - Winning configs to stdout
    - results/tta/best_configs.json (CLIP best configs)
    - results/tta_backbone/summary.csv (when --all-backbones, all backbones)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Find best TTA configs from eval results")
    ap.add_argument(
        "--results-root", type=str, default=None,
        help="Results directory (default: PROJECT_ROOT/results)",
    )
    ap.add_argument(
        "--all-backbones", action="store_true",
        help="Also scan tta_backbone/ results and write summary.csv",
    )
    return ap.parse_args(argv)


def _load_tta_metrics(tta_dir: Path) -> list[dict]:
    """Load all eval_metrics.json files from subdirectories of tta_dir."""
    results = []
    if not tta_dir.exists():
        return results
    for sub in sorted(tta_dir.iterdir()):
        metrics_path = sub / "eval_metrics.json"
        if not metrics_path.exists():
            continue
        try:
            data = json.loads(metrics_path.read_text(encoding="utf-8"))
            data["_run_dir"] = sub.name
            results.append(data)
        except (json.JSONDecodeError, OSError):
            print(f"[warn] Skipping unreadable: {metrics_path}", file=sys.stderr)
    return results


def _find_best_configs(metrics: list[dict]) -> dict:
    """Find best TENT lr and best SAR (lr, rho) by mean AUC across conditions.

    Groups results by (method, lr, rho), computes mean AUC, and picks the
    config with the highest mean AUC for each method.

    Returns dict with 'source_only', 'tent', 'sar' entries.
    """
    # Group: (method, lr, rho) -> list of AUC values
    groups = defaultdict(list)
    for m in metrics:
        method = m.get("method", "unknown")
        lr = m.get("lr", 0.0)
        rho = m.get("rho") or 0.0
        auc = m.get("auc")
        if auc is None:
            continue
        groups[(method, lr, rho)].append(float(auc))

    best = {}
    for method_name in ("source_only", "tent", "sar"):
        method_groups = {
            k: v for k, v in groups.items() if k[0] == method_name
        }
        if not method_groups:
            continue
        # Find config with highest mean AUC
        best_key = max(method_groups, key=lambda k: sum(method_groups[k]) / len(method_groups[k]))
        mean_auc = sum(method_groups[best_key]) / len(method_groups[best_key])
        best[method_name] = {
            "lr": best_key[1],
            "rho": best_key[2],
            "mean_auc": round(mean_auc, 6),
            "n_conditions": len(method_groups[best_key]),
        }

    return best


def _print_best(best: dict, label: str = "CLIP") -> None:
    """Pretty-print best configs to stdout."""
    print(f"\n=== Best TTA configs ({label}) ===")
    for method, info in best.items():
        parts = [f"  {method}: mean_AUC={info['mean_auc']:.4f}"]
        if method != "source_only":
            parts.append(f"lr={info['lr']}")
        if method == "sar":
            parts.append(f"rho={info['rho']}")
        parts.append(f"({info['n_conditions']} conditions)")
        print("  ".join(parts))


def _write_best_configs(best: dict, output_path: Path) -> None:
    """Write best configs to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(best, f, indent=2, sort_keys=True)
    print(f"\nBest configs written to: {output_path}")


def _write_backbone_summary(
    all_results: dict[str, dict],
    output_path: Path,
) -> None:
    """Write summary CSV with best configs for all backbones.

    Args:
        all_results: {backbone_label: best_configs_dict}
        output_path: Path to write summary.csv
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for backbone, best in all_results.items():
        for method, info in best.items():
            rows.append({
                "backbone": backbone,
                "method": method,
                "lr": info["lr"],
                "rho": info["rho"],
                "mean_auc": info["mean_auc"],
                "n_conditions": info["n_conditions"],
            })

    if not rows:
        print("[warn] No backbone results to write.", file=sys.stderr)
        return

    fieldnames = ["backbone", "method", "lr", "rho", "mean_auc", "n_conditions"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nBackbone summary written to: {output_path}")


def main(argv=None) -> int:
    args = parse_args(argv)
    results_root = Path(args.results_root) if args.results_root else PROJECT_ROOT / "results"

    # 1. Analyze CLIP TTA results (existing 500 runs in results/tta/)
    tta_dir = results_root / "tta"
    metrics = _load_tta_metrics(tta_dir)
    if not metrics:
        print(f"[error] No TTA results found in {tta_dir}", file=sys.stderr)
        return 1

    print(f"Loaded {len(metrics)} CLIP TTA results from {tta_dir}")
    best_clip = _find_best_configs(metrics)
    _print_best(best_clip, label="CLIP (clip-vit-b-16)")
    _write_best_configs(best_clip, tta_dir / "best_configs.json")

    # 2. If --all-backbones, also scan tta_backbone/ results
    if args.all_backbones:
        all_results = {"clip-vit-b-16": best_clip}

        tta_bb_dir = results_root / "tta_backbone"
        if tta_bb_dir.exists():
            bb_metrics = _load_tta_metrics(tta_bb_dir)
            print(f"\nLoaded {len(bb_metrics)} backbone TTA results from {tta_bb_dir}")

            # Group by backbone
            by_backbone = defaultdict(list)
            for m in bb_metrics:
                bb = m.get("backbone", "unknown")
                by_backbone[bb].append(m)

            for bb, bb_mets in sorted(by_backbone.items()):
                best_bb = _find_best_configs(bb_mets)
                _print_best(best_bb, label=bb)
                all_results[bb] = best_bb
        else:
            print(f"\n[info] No backbone TTA results yet at {tta_bb_dir}")

        _write_backbone_summary(all_results, tta_bb_dir / "summary.csv")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
