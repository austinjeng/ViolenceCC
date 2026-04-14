"""D-13: WandbLogger respects mode=disabled / offline gracefully."""
from pathlib import Path

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
