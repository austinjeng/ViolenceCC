"""compare_consistency_rerun.py -- per-cell delta table + DECISION-GATE verdict.

Companion to scripts/run_ucf_consistency_rerun.py (quick 260717-77p, Job C).
Reads each canonical results/<runname>/eval_metrics.json and its
results/_consistency_rerun/<runname>/eval_metrics.json counterpart, and emits:

  * results/_consistency_rerun/comparison.csv -- one row per rerun cell:
    canonical AUC, rerun AUC, delta (rerun - canonical), the row's canonical
    3-seed std (sample std over the cell's s{42,123,2024} siblings, matching
    the thesis tables' statistics.stdev convention), and a within-std flag.
  * results/_consistency_rerun/comparison.md -- markdown summary.
  * A printed DECISION-GATE verdict:
      PASS  -> every |delta| <= its row's seed std: publish the deltas in the
               ch04 footnote ("post-freeze consistency rerun shifts every
               cell by <= X, within seed variance; numbers reported as run").
      FAIL  -> escalation cells listed: adopt the rerun numbers (full
               propagation pass) per the 2026-07-17 addendum decision gate.

Zero GPU; run any time after (or during) the rerun:
    python scripts/compare_consistency_rerun.py
"""
from __future__ import annotations

import csv
import json
import re
import statistics
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = PROJECT_ROOT / "results"
RERUN_ROOT = RESULTS_ROOT / "_consistency_rerun"

_SEEDS = (42, 123, 2024)


def _auc(run_dir: Path) -> float | None:
    p = run_dir / "eval_metrics.json"
    if not p.exists():
        return None
    try:
        return float(json.loads(p.read_text(encoding="utf-8"))["auc"])
    except Exception:
        return None


def row_seed_std(run_name: str) -> tuple:
    """Sample std over the cell's 3-seed canonical siblings.

    ucf_late_fusion_s42 -> siblings ucf_late_fusion_s{42,123,2024}.
    Returns (std, n_siblings_found).
    """
    m = re.match(r"^(.*)_s(\d+)$", run_name)
    if not m:
        return None, 0
    base = m.group(1)
    vals = []
    for s in _SEEDS:
        v = _auc(RESULTS_ROOT / f"{base}_s{s}")
        if v is not None:
            vals.append(v)
    if len(vals) < 2:
        return None, len(vals)
    return statistics.stdev(vals), len(vals)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--results-root", default=None,
        help="Override the canonical results root (default: <repo>/results).",
    )
    args = parser.parse_args()
    global RESULTS_ROOT, RERUN_ROOT
    if args.results_root:
        RESULTS_ROOT = Path(args.results_root)
        RERUN_ROOT = RESULTS_ROOT / "_consistency_rerun"

    if not RERUN_ROOT.exists():
        print(f"No {RERUN_ROOT} yet -- run scripts/run_ucf_consistency_rerun.py first.")
        return 1

    rows = []
    for rerun_dir in sorted(p for p in RERUN_ROOT.iterdir() if p.is_dir()):
        run_name = rerun_dir.name
        rerun_auc = _auc(rerun_dir)
        if rerun_auc is None:
            continue  # not finished yet (job is resumable)
        canon_auc = _auc(RESULTS_ROOT / run_name)
        if canon_auc is None:
            print(f"[warn] {run_name}: no canonical eval_metrics.json; skipping")
            continue
        std, n_sib = row_seed_std(run_name)
        delta = rerun_auc - canon_auc
        within = (std is not None) and (abs(delta) <= std)
        rows.append({
            "run_name": run_name,
            "canonical_auc": round(canon_auc, 6),
            "rerun_auc": round(rerun_auc, 6),
            "delta": round(delta, 6),
            "row_seed_std": round(std, 6) if std is not None else "",
            "n_seed_siblings": n_sib,
            "within_seed_std": within,
        })

    if not rows:
        print("No completed rerun cells found yet.")
        return 1

    out_csv = RERUN_ROOT / "comparison.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    escalation = [r for r in rows if not r["within_seed_std"]]
    max_abs = max(abs(r["delta"]) for r in rows)

    md = [
        "# UCF consistency rerun -- comparison",
        "",
        f"Cells compared: {len(rows)}  |  max |delta|: {max_abs:.6f}  |  "
        f"escalation cells: {len(escalation)}",
        "",
        "| run | canonical AUC | rerun AUC | delta | row seed std | within std |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['run_name']} | {r['canonical_auc']} | {r['rerun_auc']} | "
            f"{r['delta']:+.6f} | {r['row_seed_std']} | "
            f"{'yes' if r['within_seed_std'] else 'NO'} |"
        )
    md.append("")
    if escalation:
        md.append("**DECISION GATE: FAIL** -- adopt the rerun numbers (full "
                  "propagation pass). Escalation cells: "
                  + ", ".join(r["run_name"] for r in escalation))
    else:
        md.append(f"**DECISION GATE: PASS** -- every |delta| <= its row's seed "
                  f"std (max |delta| {max_abs:.6f}); publish the deltas in the "
                  f"ch04 footnote and keep numbers as run.")
    (RERUN_ROOT / "comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv} + comparison.md ({len(rows)} cells)")
    print()
    if escalation:
        print("DECISION-GATE: FAIL -- |delta| exceeds row seed std for:")
        for r in escalation:
            print(f"  {r['run_name']}: delta {r['delta']:+.6f} vs std {r['row_seed_std']}")
        print("-> escalate: adopt the rerun numbers (full propagation pass).")
        return 2
    print(f"DECISION-GATE: PASS -- all {len(rows)} cells within their row seed "
          f"std (max |delta| = {max_abs:.6f}); numbers reported as run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
