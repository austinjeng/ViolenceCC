"""EarlyStopping on val MIL loss (TRN-02)."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class EarlyStopping:
    patience: int = 10
    best_loss: float = math.inf
    best_epoch: int = -1
    counter: int = 0
    stopped: bool = False
    # Track consecutive NaN val-loss epochs; halt after 3 (safety)
    nan_streak: int = 0

    def step(self, epoch: int, val_loss: float) -> dict:
        """Returns {'is_best': bool, 'should_stop': bool}."""
        if val_loss is None or math.isnan(val_loss) or math.isinf(val_loss):
            # Defensive: do not treat NaN/Inf as better or worse than current best
            self.nan_streak += 1
            if self.nan_streak >= 3:
                self.stopped = True
            return {"is_best": False, "should_stop": self.stopped}
        self.nan_streak = 0

        if val_loss < self.best_loss:
            self.best_loss = val_loss
            self.best_epoch = epoch
            self.counter = 0
            is_best = True
        else:
            self.counter += 1
            is_best = False
            if self.counter >= self.patience:
                self.stopped = True
        return {"is_best": is_best, "should_stop": self.stopped}
