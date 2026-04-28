"""Phase 5 D-09 -- TTA queue definitions and TTARunSpec in scripts/run_ablations.py.

Tests:
  T1 tta_source_only queue has 20 specs (4 types x 5 sev)
  T2 tta_tent_grid queue has 80 specs (4 types x 5 sev x 4 LRs)
  T3 tta_sar_grid queue has 400 specs (4 types x 5 sev x 4 LRs x 5 rhos)
  T4 TTARunSpec.run_name for source_only
  T5 TTARunSpec.run_name for tent
  T6 TTARunSpec.run_name for sar (includes rho)
  T7 RESULTS_INDEX_COLUMNS includes TTA fields
  T8 TTA queue names are valid --queue choices in CLI
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_ablations import (  # noqa: E402
    TTA_QUEUES,
    TTARunSpec,
    is_done,
    run_queue_tta,
)
from src.utils.csv_logger import RESULTS_INDEX_COLUMNS  # noqa: E402


def test_tta_source_only_queue_has_20_specs():
    """D-09: 4 corruption types x 5 severities = 20 source_only runs."""
    assert len(TTA_QUEUES["tta_source_only"]) == 20


def test_tta_tent_grid_has_80_specs():
    """D-09: 4 types x 5 sev x 4 LRs = 80 TENT runs."""
    assert len(TTA_QUEUES["tta_tent_grid"]) == 80


def test_tta_sar_grid_has_400_specs():
    """D-09: 4 types x 5 sev x 4 LRs x 5 rhos = 400 SAR runs."""
    assert len(TTA_QUEUES["tta_sar_grid"]) == 400


def test_ttarunspec_run_name_source_only():
    """D-13: source_only naming does not include rho."""
    spec = TTARunSpec("gaussian_noise", 1, "source_only", 0.0)
    assert spec.run_name == "source_only_gaussian_noise_1_lr0.0"


def test_ttarunspec_run_name_tent():
    """D-13: tent naming includes lr but not rho."""
    spec = TTARunSpec("brightness", 3, "tent", 0.001)
    assert spec.run_name == "tent_brightness_3_lr0.001"


def test_ttarunspec_run_name_sar():
    """D-13: sar naming includes both lr and rho."""
    spec = TTARunSpec("motion_blur", 5, "sar", 0.001, 0.01)
    assert spec.run_name == "sar_motion_blur_5_lr0.001_rho0.01"


def test_results_index_columns_include_tta_fields():
    """Phase 5 extension: TTA columns appended to RESULTS_INDEX_COLUMNS."""
    tta_fields = ["method", "corruption_type", "severity", "lr", "rho"]
    for field in tta_fields:
        assert field in RESULTS_INDEX_COLUMNS, (
            f"missing TTA field {field!r} in RESULTS_INDEX_COLUMNS"
        )


def test_tta_queue_names_in_choices():
    """TTA queue names are valid --queue choices in the CLI."""
    out = subprocess.run(
        [sys.executable, "scripts/run_ablations.py", "--help"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    combined = (out.stdout + out.stderr).lower()
    for q in ("tta_source_only", "tta_tent_grid", "tta_sar_grid"):
        assert q in combined, f"missing TTA queue {q!r} in --help: {combined[:400]}"


def test_tta_dry_run_skips_subprocess(tmp_path, capsys):
    """dry_run mode prints plan but does not invoke evaluate_tta.py."""
    err_log = tmp_path / "runner-errors.log"
    specs = TTA_QUEUES["tta_source_only"][:2]  # just 2 specs for speed
    summary = run_queue_tta(specs, tmp_path, err_log, dry_run=True)
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out
    assert summary == {"succeeded": [], "skipped": [], "failed": []}


def test_tta_skip_if_done(tmp_path, capsys):
    """D-31: .done marker skips already-complete TTA runs."""
    spec = TTARunSpec("gaussian_noise", 1, "source_only", 0.0)
    run_dir = tmp_path / "tta" / spec.run_name
    run_dir.mkdir(parents=True)
    (run_dir / ".done").write_text("eval_complete\n", encoding="utf-8")
    err_log = tmp_path / "runner-errors.log"
    summary = run_queue_tta([spec], tmp_path, err_log, dry_run=False)
    captured = capsys.readouterr()
    assert "[skip]" in captured.out
    assert summary == {
        "succeeded": [],
        "skipped": [spec.run_name],
        "failed": [],
    }


def test_tta_total_runs_is_500():
    """D-09: total TTA runs = 20 + 80 + 400 = 500."""
    total = sum(len(q) for q in TTA_QUEUES.values())
    assert total == 500, f"expected 500 total TTA runs, got {total}"
