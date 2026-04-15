"""Fail-fast wandb configuration check (Phase 4 D-39).

Exits 0 if wandb is ready, nonzero with actionable message otherwise.
Resolves the Phase 3 VERIFICATION nit: WANDB_MODE=disabled doesn't suppress
the first-run wizard -- we need explicit preflight in non-interactive queue
contexts.

Usage:
    python scripts/wandb_preflight.py           # exit 0 or 2

Exit codes:
    0 -- wandb is configured (env var OR ~/.netrc/key) OR not installed
         (CSV-only mode is fine if all configs set wandb.mode=disabled)
    2 -- wandb installed but neither env var nor api_key present;
         stderr contains actionable instructions
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    # Path 1: WANDB_API_KEY env var
    if os.environ.get("WANDB_API_KEY"):
        print("[preflight] wandb: WANDB_API_KEY env var set")
        return 0

    # Path 2: wandb installed + has api_key from ~/.netrc or settings
    try:
        import wandb
    except ImportError:
        print(
            "[preflight] wandb not installed; CSV-only mode is fine "
            "if all configs set wandb.mode=disabled"
        )
        return 0

    try:
        key = wandb.api.api_key
    except Exception as exc:
        sys.stderr.write(
            f"[preflight] wandb.api.api_key access failed: {exc}\n"
            "Run `wandb login` or set WANDB_API_KEY.\n"
        )
        return 2

    if key is not None:
        print("[preflight] wandb: api_key discovered via ~/.netrc or settings")
        return 0

    sys.stderr.write(
        "ERROR: wandb is not configured.\n"
        "Run one of:\n"
        "  (1) export WANDB_API_KEY=<your key>\n"
        "  (2) wandb login   # interactive one-time\n"
        "  (3) set `wandb.mode: disabled` in every config YAML (CSV-only mode)\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
