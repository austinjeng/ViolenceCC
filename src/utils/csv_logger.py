"""CSV logger with flush+fsync per row (TRN-04).

Phase 4 D-33 addition: ``results_index_append`` sibling function for the
``results/results-index.csv`` append-only audit log consumed by
``scripts/run_ablations.py``. Shares the header-once + flush + fsync
pattern of ``CSVLogger`` without altering the existing class.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterable, Union


class CSVLogger:
    """Append-mode CSV logger that survives unclean shutdown.

    Header is written on first open; subsequent opens in 'a' mode append rows.
    flush + fsync per row so a crash at epoch 17 still leaves epochs 0-16 on disk.
    """

    def __init__(
        self,
        path: Union[str, Path],
        fieldnames: Iterable[str] = ("epoch", "train_loss", "val_loss", "lr"),
    ) -> None:
        self.path = Path(path)
        self.fieldnames = list(fieldnames)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Write header only if file is new / empty
        if not self.path.exists() or self.path.stat().st_size == 0:
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=self.fieldnames)
                w.writeheader()
                f.flush()
                os.fsync(f.fileno())

    def log(self, **kwargs) -> None:
        row = {k: kwargs.get(k, "") for k in self.fieldnames}
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            w.writerow(row)
            f.flush()
            os.fsync(f.fileno())


# ---------------------------------------------------------------------------
# Phase 4 D-33: results-index.csv append-only audit log
#
# Schema is fixed (12 columns); order is stable across runs so pandas.read_csv
# + column-subset selection keeps working as new rows land. run_ablations.py
# writes one row per completed (train + evaluate) run.
# ---------------------------------------------------------------------------
RESULTS_INDEX_COLUMNS = [
    "run_name",
    "variant",
    "dataset",
    "seed",
    "cache_variant",
    "auc",
    "ap",
    "n_videos",
    "n_frames",
    "start_time",
    "end_time",
    "config_hash",
]


def results_index_append(path: Union[str, Path], row: dict) -> None:
    """Append one run row to results/results-index.csv (D-33).

    Writes the header on first open; subsequent opens append rows. flush + fsync
    per write so a crash after N rows preserves rows 0..N-1 on disk. Missing
    keys in ``row`` are written as empty strings (schema stability matters more
    than row completeness for post-hoc pandas analyses).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    write_header = (not p.exists()) or p.stat().st_size == 0
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULTS_INDEX_COLUMNS)
        if write_header:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in RESULTS_INDEX_COLUMNS})
        f.flush()
        os.fsync(f.fileno())
