"""TRN-01 / TRN-03 src/train.py unit tests."""
import pathlib
import subprocess

import pytest
import torch

from src.utils.scheduler import build_optimizer


def test_optimizer_config():
    """TRN-01 (VALIDATION.md): AdamW lr=1e-4, weight_decay=1e-2."""
    model = torch.nn.Linear(4, 2)
    cfg = {"lr": 1e-4, "weight_decay": 1e-2}
    opt = build_optimizer(model.parameters(), cfg)
    assert opt.param_groups[0]["lr"] == 1e-4
    assert opt.param_groups[0]["weight_decay"] == 1e-2


def test_cublas_env():
    """TRN-03 (VALIDATION.md): CUBLAS_WORKSPACE_CONFIG set before `import torch`.

    Read src/train.py as text and confirm the env var set occurs BEFORE the
    first `import torch` line.
    """
    src = pathlib.Path("src/train.py").read_text(encoding="utf-8")
    lines = src.splitlines()
    env_line_idx = None
    torch_import_idx = None
    for i, line in enumerate(lines):
        if "CUBLAS_WORKSPACE_CONFIG" in line and env_line_idx is None:
            env_line_idx = i
        if line.strip() == "import torch" and torch_import_idx is None:
            torch_import_idx = i
    assert env_line_idx is not None, "CUBLAS_WORKSPACE_CONFIG not set in src/train.py"
    assert torch_import_idx is not None, "src/train.py does not import torch"
    assert env_line_idx < torch_import_idx, (
        f"CUBLAS_WORKSPACE_CONFIG at line {env_line_idx+1} must come BEFORE "
        f"`import torch` at line {torch_import_idx+1}"
    )


def test_cli_lr_override():
    """Phase 7 D-09: --lr overrides cfg['train']['lr']."""
    from src.train import parse_args, apply_cli_overrides
    from src.utils.config import load_config
    args = parse_args(["--config", "configs/gated_fusion_xd.yaml", "--lr", "3e-4"])
    assert args.lr == 3e-4
    cfg = load_config("configs/gated_fusion_xd.yaml")
    cfg = apply_cli_overrides(cfg, args)
    assert cfg["train"]["lr"] == 3e-4


def test_cli_k_topk_override():
    """Phase 7 D-09: --k-topk overrides cfg['train']['k_topk']."""
    from src.train import parse_args, apply_cli_overrides
    from src.utils.config import load_config
    args = parse_args(["--config", "configs/gated_fusion_xd.yaml", "--k-topk", "7"])
    assert args.k_topk == 7
    cfg = load_config("configs/gated_fusion_xd.yaml")
    cfg = apply_cli_overrides(cfg, args)
    assert cfg["train"]["k_topk"] == 7


def test_cli_help():
    """Entry point is invokable as a module."""
    r = subprocess.run(
        ["python", "-c", "from src.train import parse_args; parse_args(['--config', 'x'])"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
