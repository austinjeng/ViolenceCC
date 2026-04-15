"""wandb mirror for CSV logs (D-13).

CSV is the offline source of truth (Plan 06); wandb is an online mirror.
Supports `mode` in {online, offline, disabled}. In CI / tests, WANDB_MODE=disabled
is the default -- no network, no file writes, no-op methods.

RESEARCH.md 9.2 contract:
  id=run_dir.name                  stable ID for crash-resume
  resume='allow'                   picks up from last logged step if reinitialized
  define_metric('train/*', step_metric='epoch')  aligns curves on epoch axis

Phase 4 D-40: if wandb.init raises a wandb.errors.Error on the first call
(auth failure, network hiccup), re-init with mode='offline' so training
continues and metrics land in a local wandb cache. The CSV logger remains
the source of truth for thesis tables.
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
        # D-40: catch wandb.errors.Error specifically so auth/network failures
        # trigger the offline fallback. Other exceptions fall through to the
        # silent noop branch below. getattr(..., "Error", Exception) keeps the
        # handler working against wandb versions without a stable Error class.
        _WandbErr = getattr(getattr(wandb, "errors", None), "Error", Exception)
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
        except _WandbErr as exc:
            # D-40: auth or network failure -> re-init with mode="offline",
            # print a diagnostic the runner picks up via stdout capture.
            try:
                self.run = wandb.init(
                    project=wcfg.get("project", "violencecc"),
                    mode="offline",
                    id=run_id,
                    resume="allow",
                    name=run_id,
                    config=cfg,
                    dir=str(run_dir),
                    tags=wcfg.get("tags", []),
                )
                print(
                    f"[wandb] offline fallback after {type(exc).__name__}: {exc}",
                    flush=True,
                )
            except Exception:
                self.run = None
            return
        except Exception:
            # Any other wandb-side init failure (directory permissions, etc.)
            # must not halt training. Degrade to noop.
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
