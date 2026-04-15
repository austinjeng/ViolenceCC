"""D-13: WandbLogger respects mode=disabled / offline gracefully.

Phase 4 additions:
  - D-40: wandb.errors.Error during init -> re-init with mode=offline, log warning.
"""
from pathlib import Path

import pytest

from src.utils.wandb_logger import WandbLogger


def test_wandb_disabled_is_noop(tmp_path):
    cfg = {"wandb": {"mode": "disabled", "project": "violencecc", "tags": []}}
    logger = WandbLogger(cfg, tmp_path / "run")
    assert logger.run is None
    logger.log({"train/loss": 0.1, "val/loss": 0.2, "lr": 1e-4}, step=0)  # no raise
    logger.finish()  # no raise


def test_wandb_missing_block_is_noop(tmp_path):
    """If a config lacks a wandb block entirely, WandbLogger still no-ops safely."""
    cfg = {}
    logger = WandbLogger(cfg, tmp_path / "run")
    assert logger.run is None
    logger.log({"train/loss": 0.1}, step=0)
    logger.finish()


def test_offline_fallback_on_errors_error(tmp_path, monkeypatch, capsys):
    """D-40: WandbLogger catches wandb.errors.Error and retries with mode=offline.

    First wandb.init call raises a simulated wandb.errors.Error; the second
    call (with mode='offline') succeeds and yields a non-None `self.run`.
    The runner continues — CSV is the source of truth; wandb is auxiliary.
    """
    import types
    import sys as _sys
    import importlib

    call_log = []
    fake_wandb = types.ModuleType("wandb")

    class _Err(Exception):
        pass

    fake_wandb.errors = types.SimpleNamespace(Error=_Err)

    def _fake_init(**kwargs):
        call_log.append(dict(kwargs))
        if len(call_log) == 1:
            raise _Err("mock auth failure")
        # second call should use mode='offline'
        return types.SimpleNamespace(
            mode=kwargs.get("mode"), id=kwargs.get("id"),
            log=lambda *a, **k: None, finish=lambda: None,
        )

    def _fake_define_metric(*a, **k):
        return None

    fake_wandb.init = _fake_init
    fake_wandb.define_metric = _fake_define_metric
    fake_wandb.api = types.SimpleNamespace(api_key="dummy")
    monkeypatch.setitem(_sys.modules, "wandb", fake_wandb)

    import src.utils.wandb_logger as wl
    importlib.reload(wl)
    try:
        cfg = {"wandb": {"mode": "online", "project": "violencecc", "tags": []}}
        logger = wl.WandbLogger(cfg, tmp_path / "run-id-xyz")
    finally:
        # Restore the real module for other tests
        _sys.modules.pop("wandb", None)
        importlib.reload(wl)

    assert len(call_log) == 2, (
        f"offline fallback did not fire: expected 2 init calls, got {len(call_log)}"
    )
    assert call_log[1]["mode"] == "offline"
    captured = capsys.readouterr()
    # The fallback prints a diagnostic message the runner logs.
    combined = captured.out + captured.err
    assert "offline fallback" in combined


def test_offline_fallback_second_failure_noops(tmp_path, monkeypatch):
    """D-40 second branch: if both init calls raise, self.run stays None (noop)."""
    import types
    import sys as _sys
    import importlib

    fake_wandb = types.ModuleType("wandb")

    class _Err(Exception):
        pass

    fake_wandb.errors = types.SimpleNamespace(Error=_Err)

    def _fake_init(**kwargs):
        raise _Err("mock: both online and offline init fail")

    fake_wandb.init = _fake_init
    fake_wandb.define_metric = lambda *a, **k: None
    fake_wandb.api = types.SimpleNamespace(api_key="dummy")
    monkeypatch.setitem(_sys.modules, "wandb", fake_wandb)

    import src.utils.wandb_logger as wl
    importlib.reload(wl)
    try:
        cfg = {"wandb": {"mode": "online", "project": "violencecc", "tags": []}}
        logger = wl.WandbLogger(cfg, tmp_path / "run-id")
    finally:
        _sys.modules.pop("wandb", None)
        importlib.reload(wl)

    assert logger.run is None, "cascaded failure should leave self.run = None"
    # No exception raised; logger is a silent noop.
    logger.log({"x": 1})
    logger.finish()
