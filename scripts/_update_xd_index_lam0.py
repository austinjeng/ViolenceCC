"""Update auc/ap for retrained XD lam_smooth=0 rows in results-index.csv.

XD analog of recompute_fulllength_ucf.py's _write_results_index. The Stage-2
lam=0 retrain overwrote each results/xd_*/eval_metrics.json but never re-appended
to results-index.csv, leaving the index (and everything downstream) stale.

Updates auc/ap for EXACTLY the xd_* runs listed in results/_lam0_done.txt, read
from each run's eval_metrics.json. Leaves every ucf_* row, every xd_rtfm_i3d_*
row (not retrained, kept at 8e-4), every TTA/corruption row, n_frames, and every
other column untouched. Backup-once, atomic .tmp -> os.replace.

Run from project root in vcc-main:
  C:/Anaconda/envs/vcc-main/python.exe scripts/_update_xd_index_lam0.py
"""
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
INDEX = RESULTS / "results-index.csv"
DONE = RESULTS / "_lam0_done.txt"
BACKUP = INDEX.with_name(INDEX.name + ".pre_xd_lam0.bak")


def main() -> None:
    if not INDEX.exists():
        sys.exit(f"results-index.csv not found at {INDEX}")
    if not DONE.exists():
        sys.exit(f"_lam0_done.txt not found at {DONE}")

    xd_runs = [
        ln.strip()
        for ln in DONE.read_text(encoding="utf-8").splitlines()
        if ln.strip().startswith("xd_")
    ]
    print(f"Retrained xd_* runs in _lam0_done.txt: {len(xd_runs)}")

    # Pull fresh auc/ap from each run's eval_metrics.json.
    updates = {}
    missing = []
    for run in xd_runs:
        mp = RESULTS / run / "eval_metrics.json"
        if not mp.exists():
            missing.append(run)
            continue
        d = json.loads(mp.read_text(encoding="utf-8"))
        if d.get("auc") is None or d.get("ap") is None:
            sys.exit(f"{run}: eval_metrics.json missing auc/ap")
        updates[run] = {"auc": float(d["auc"]), "ap": float(d["ap"])}
    if missing:
        sys.exit(f"Missing eval_metrics.json for: {missing}")

    with open(INDEX, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    seen = set()
    n_updated = 0
    for row in rows:
        nm = updates.get(row.get("run_name"))
        if nm is None:
            continue
        # Defensive: only xd_* keys are in `updates`, but never touch a non-xd row.
        if not row["run_name"].startswith("xd_"):
            continue
        row["auc"] = repr(nm["auc"])
        row["ap"] = repr(nm["ap"])
        seen.add(row["run_name"])
        n_updated += 1

    not_in_index = sorted(set(updates) - seen)
    if not_in_index:
        sys.exit(f"Runs not found as rows in results-index.csv: {not_in_index}")

    if not BACKUP.exists():
        BACKUP.write_bytes(INDEX.read_bytes())
        print(f"  backup -> {BACKUP.name}")
    tmp = INDEX.with_name(INDEX.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, INDEX)
    print(f"  results-index.csv: updated {n_updated} xd_* rows")
    assert n_updated == len(xd_runs), (n_updated, len(xd_runs))
    print("OK")


if __name__ == "__main__":
    main()
