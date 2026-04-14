"""CSV logger with flush+fsync per row (TRN-04)."""
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
