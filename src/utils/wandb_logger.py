"""wandb mirror for CSV logs (D-13).

CSV is the offline source of truth (Plan 06); wandb is an online mirror.
Supports `mode` in {online, offline, disabled}. In CI / tests, WANDB_MODE=disabled
is the default -- no network, no file writes, no-op methods.

RESEARCH.md 9.2 contract:
  id=run_dir.name                  stable ID for crash-resume
  resume='allow'                   picks up from last logged step if reinitialized
  define_metric('train/*', step_metric='epoch')  aligns curves on epoch axis
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class WandbLogger:
    """Thin wrapper around wandb.init/log/finish with mode-aware noop."""

    def __init__(self, cfg: dict, run_dir: Path) -> None:
        self.run = None
        wcfg = cfg.get("wandb", {}) if isinstance(cfg, dict) else {}
        mode = wcfg.get("mode", "disabled")
        if mode == "disabled":
            return

        try:
            import wandb
        except ImportError:
            # wandb not installed -> degrade silently to disabled
            return

        os.environ.setdefault("WANDB_MODE", mode)
        # run_dir name is the stable ID for crash-resume
        run_id = Path(run_dir).name
        entity = (
            os.environ.get("VIOLENCECC_WANDB_ENTITY")
            or wcfg.get("entity")
        )
        try:
            self.run = wandb.init(
                project=wcfg.get("project", "violencecc"),
                entity=entity,
                mode=mode,
                id=run_id,
                resume="allow",
                name=run_id,
                config=cfg,
                dir=str(run_dir),
                tags=wcfg.get("tags", []),
            )
        except Exception:
            # Any wandb-side initialization failure (network hiccup, login,
            # directory permissions) must not halt training. Degrade to noop.
            self.run = None
            return

        try:
            wandb.define_metric("train/*", step_metric="epoch")
            wandb.define_metric("val/*", step_metric="epoch")
        except Exception:
            # define_metric is cosmetic; don't crash the run over it
            pass

    def log(self, metrics: dict, step: Optional[int] = None) -> None:
        if self.run is None:
            return
        payload = dict(metrics)
        if step is not None:
            payload.setdefault("epoch", step)
        try:
            self.run.log(payload)
        except Exception:
            # wandb client issues must not halt training
            pass

    def finish(self) -> None:
        if self.run is None:
            return
        try:
            self.run.finish()
        except Exception:
            pass
