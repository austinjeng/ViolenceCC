"""Phase 4 D-33 — results/results-index.csv append-only audit log.

Verifies `src.utils.csv_logger.results_index_append` plus:
  - `--run-name` arg on src/train.py (D-30)
"""
import csv
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_append_writes_header_first(tmp_path):
    from src.utils.csv_logger import results_index_append, RESULTS_INDEX_COLUMNS
    p = tmp_path / "results-index.csv"
    results_index_append(p, {"run_name": "ucf_gated_fusion_s42",
                             "auc": 0.85, "ap": 0.42})
    txt = p.read_text(encoding="utf-8").strip().splitlines()
    assert txt[0].split(",") == RESULTS_INDEX_COLUMNS


def test_append_second_row_no_duplicate_header(tmp_path):
    from src.utils.csv_logger import results_index_append
    p = tmp_path / "results-index.csv"
    results_index_append(p, {"run_name": "a", "auc": 0.8})
    results_index_append(p, {"run_name": "b", "auc": 0.9})
    with open(p, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
    assert rows[0]["run_name"] == "a"
    assert rows[1]["run_name"] == "b"


def test_missing_columns_blank(tmp_path):
    from src.utils.csv_logger import results_index_append, RESULTS_INDEX_COLUMNS
    p = tmp_path / "results-index.csv"
    results_index_append(p, {"run_name": "x"})
    with open(p, encoding="utf-8") as fh:
        row = next(csv.DictReader(fh))
    for c in RESULTS_INDEX_COLUMNS:
        if c != "run_name":
            assert row[c] == ""


def test_column_order_stable(tmp_path):
    from src.utils.csv_logger import results_index_append, RESULTS_INDEX_COLUMNS
    p = tmp_path / "results-index.csv"
    # Pass fields out-of-order; written row preserves RESULTS_INDEX_COLUMNS order.
    results_index_append(
        p, {"config_hash": "abc", "run_name": "x", "auc": 0.8, "ap": 0.5})
    hdr = p.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert hdr == RESULTS_INDEX_COLUMNS


# --- src/train.py --run-name override (D-30) ---

def test_train_help_has_run_name():
    """Entry point exposes --run-name in --help output."""
    out = subprocess.run(
        [sys.executable, "src/train.py", "--help"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    combined = (out.stdout + out.stderr).lower()
    assert "--run-name" in combined, (
        f"--run-name missing from --help output:\n"
        f"stdout: {out.stdout[:400]}\nstderr: {out.stderr[:400]}"
    )


def test_train_run_name_arg_parsed():
    """parse_args accepts --run-name without error and preserves it on args."""
    from src.train import parse_args
    args = parse_args([
        "--config", "configs/skeleton_only.yaml",
        "--run-name", "my_custom_run",
    ])
    assert args.run_name == "my_custom_run"


def test_train_run_name_default_none():
    """Without --run-name, parse_args sets args.run_name to None (fallback to
    timestamped run_name(cfg) inside main)."""
    from src.train import parse_args
    args = parse_args(["--config", "configs/skeleton_only.yaml"])
    assert args.run_name is None
