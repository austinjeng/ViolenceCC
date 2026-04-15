# src/train.py -- single YAML-driven training entry point (TRN-06).
# TRN-03 KNOB 4: CUBLAS_WORKSPACE_CONFIG MUST be set before `import torch`.
# The following 2 lines must remain lines 1-2 of this file.
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

# Standard imports come AFTER the env var is set.
import argparse
import datetime
import sys
from pathlib import Path

# Script-mode bootstrap: when invoked as `python src/train.py` (not
# `python -m src.train`), ensure the project root is on sys.path so the
# `src.*` package imports below resolve.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import torch

from src.data.loaders import build_dataloaders
from src.losses.mil_loss import mil_ranking_loss
from src.models.registry import build_model
from src.utils.checkpoint import save_checkpoint_atomic
from src.utils.config import load_config, snapshot_config
from src.utils.csv_logger import CSVLogger
from src.utils.early_stopping import EarlyStopping
from src.utils.scheduler import build_optimizer, build_scheduler
from src.utils.seed import set_deterministic
from src.utils.wandb_logger import WandbLogger


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="ViolenceCC training entry point (TRN-06)")
    ap.add_argument("--config", required=True, help="Path to variant YAML config")
    ap.add_argument("--seed", type=int, default=None,
                    help="Override cfg['seed']")
    ap.add_argument("--epochs", type=int, default=None,
                    help="Override cfg['train']['epochs'] (for smoke tests)")
    ap.add_argument("--results-dir", type=str, default=None,
                    help="Override cfg['paths']['results_dir']")
    ap.add_argument("--run-name", type=str, default=None,
                    help="Override the default run_name() value "
                         "(Phase 4 D-30: deterministic dirs for run_ablations.py)")
    return ap.parse_args(argv)


def apply_cli_overrides(cfg: dict, args) -> dict:
    if args.seed is not None:
        cfg["seed"] = args.seed
    if args.epochs is not None:
        cfg["train"]["epochs"] = args.epochs
    if args.results_dir is not None:
        cfg["paths"]["results_dir"] = args.results_dir
    return cfg


def run_name(cfg: dict) -> str:
    """D-14 results dir name: <dataset>_<variant>_<seed>_<timestamp>."""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{cfg['dataset']}_{cfg['model']['variant']}_{cfg['seed']}_{ts}"


def _split_labels(batch):
    """Split a val batch (labels 0 normal, 1 abnormal) into paired halves.

    Returns (skel_paired, clip_paired, mask_paired, n_normal) or None if a
    half is empty (batch has only one label).
    """
    labels = batch["label"]
    nor_idx = (labels == 0).nonzero(as_tuple=True)[0]
    abn_idx = (labels == 1).nonzero(as_tuple=True)[0]
    if len(nor_idx) == 0 or len(abn_idx) == 0:
        return None
    n = min(len(nor_idx), len(abn_idx))
    nor_idx = nor_idx[:n]
    abn_idx = abn_idx[:n]
    skel = torch.cat([batch["skel"][nor_idx], batch["skel"][abn_idx]], dim=0)
    clip = torch.cat([batch["clip"][nor_idx], batch["clip"][abn_idx]], dim=0)
    mask = torch.cat([batch["mask"][nor_idx], batch["mask"][abn_idx]], dim=0)
    return skel, clip, mask, n


def train_one_epoch(model, nor_loader, abn_loader, optimizer, device, train_cfg):
    model.train()
    losses = []
    # Shorter queue drives the step count; longer queue cycles
    steps_per_epoch = min(len(nor_loader), len(abn_loader))
    nor_iter = iter(nor_loader)
    abn_iter = iter(abn_loader)
    for _ in range(steps_per_epoch):
        nor_batch = next(nor_iter)
        abn_batch = next(abn_iter)
        skel = torch.cat([nor_batch["skel"], abn_batch["skel"]], dim=0).to(device)
        clip = torch.cat([nor_batch["clip"], abn_batch["clip"]], dim=0).to(device)
        mask = torch.cat([nor_batch["mask"], abn_batch["mask"]], dim=0).to(device)
        n_normal = nor_batch["skel"].shape[0]

        scores = model(skel=skel, clip=clip, mask=mask)
        loss = mil_ranking_loss(
            scores, mask, n_normal=n_normal,
            k=int(train_cfg["k_topk"]),
            margin=float(train_cfg["margin"]),
            lam_sparse=float(train_cfg["lam_sparse"]),
            lam_smooth=float(train_cfg["lam_smooth"]),
        )

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    return float(sum(losses) / max(len(losses), 1))


@torch.no_grad()
def validate(model, val_loader, device, train_cfg) -> float:
    """Compute val MIL Ranking Loss (RESEARCH.md 10.3)."""
    model.eval()
    losses = []
    for batch in val_loader:
        pair = _split_labels(batch)
        if pair is None:
            continue
        skel, clip, mask, n_normal = pair
        skel = skel.to(device)
        clip = clip.to(device)
        mask = mask.to(device)
        scores = model(skel=skel, clip=clip, mask=mask)
        loss = mil_ranking_loss(
            scores, mask, n_normal=n_normal,
            k=int(train_cfg["k_topk"]),
            margin=float(train_cfg["margin"]),
            lam_sparse=float(train_cfg["lam_sparse"]),
            lam_smooth=float(train_cfg["lam_smooth"]),
        )
        losses.append(loss.item())
    return float(sum(losses) / max(len(losses), 1)) if losses else float("inf")


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = load_config(args.config)
    cfg = apply_cli_overrides(cfg, args)

    # Reproducibility first (TRN-03)
    set_deterministic(int(cfg["seed"]))

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Run dir (D-14 default timestamped; Phase 4 D-30 --run-name override)
    run_dir_name = args.run_name if args.run_name else run_name(cfg)
    run_dir = Path(cfg["paths"]["results_dir"]) / run_dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    # TRN-05: full snapshot (git SHA + pip freeze + env + resolved cfg) replaces
    # the minimal config.yaml copy from Plan 06.
    snapshot_config(cfg, run_dir / "config_snapshot.json")

    # Loggers
    csv_logger = CSVLogger(run_dir / "train_log.csv")
    wandb_logger = WandbLogger(cfg, run_dir)

    # Model + data + training pieces
    model = build_model(**cfg["model"]).to(device)
    (nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
    optimizer = build_optimizer(model.parameters(), cfg["train"])
    scheduler = build_scheduler(optimizer, cfg["train"])
    early = EarlyStopping(patience=int(cfg["train"]["patience"]))

    best_path = run_dir / "best_model.pth"
    last_path = run_dir / "last_model.pth"

    try:
        for epoch in range(int(cfg["train"]["epochs"])):
            train_loss = train_one_epoch(
                model, nor_loader, abn_loader, optimizer, device, cfg["train"])
            val_loss = validate(model, val_loader, device, cfg["train"])
            lr = optimizer.param_groups[0]["lr"]
            scheduler.step()

            csv_logger.log(
                epoch=epoch,
                train_loss=f"{train_loss:.6f}",
                val_loss=f"{val_loss:.6f}",
                lr=f"{lr:.8f}",
            )
            wandb_logger.log(
                {"train/loss": train_loss, "val/loss": val_loss, "lr": lr},
                step=epoch,
            )
            print(f"[epoch {epoch:03d}] train_loss={train_loss:.4f} val_loss={val_loss:.4f} lr={lr:.6g}",
                  flush=True)

            decision = early.step(epoch, val_loss)
            # Always save last (D-15)
            save_checkpoint_atomic(model.state_dict(), last_path)
            if decision["is_best"]:
                save_checkpoint_atomic(model.state_dict(), best_path)

            if decision["should_stop"]:
                print(f"[early stop] best_epoch={early.best_epoch} best_loss={early.best_loss:.4f}",
                      flush=True)
                break
    finally:
        wandb_logger.finish()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
