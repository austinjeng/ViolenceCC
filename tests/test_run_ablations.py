"""Phase 4 D-26..D-34 + D-41 — scripts/run_ablations.py orchestrator.

Tests:
  R1 --help lists all 4 queues
  R2 dry-run prints plan but skips subprocess
  R3 .done probe skips already-complete runs
  R4 success path appends to results-index.csv
  R5 train failure logs to runner-errors.log and returns non-zero status
  R6 queue continues to next spec after a failure
  R7 RunSpec.run_name + wandb_tags match D-30 / D-41 formats
  R8 queue definitions: 1 + 4 + 2 + 2 = 9 specs
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import under test.
from scripts.run_ablations import (  # noqa: E402
    QUEUES,
    RunSpec,
    is_done,
    run_queue,
)


def test_help_has_expected_queues():
    out = subprocess.run(
        [sys.executable, "scripts/run_ablations.py", "--help"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    combined = (out.stdout + out.stderr).lower()
    for q in ("rtfm_gate", "phase4_main", "phase4_pooling", "phase4_seeds"):
        assert q in combined, f"missing queue {q!r} in --help: {combined[:300]}"


def test_queue_definitions():
    """D-26/D-27/D-28: rtfm_gate=1, phase4_main=4, phase4_pooling=2,
    phase4_seeds=2 (seed=42 covered by phase4_main, not duplicated)."""
    assert len(QUEUES["rtfm_gate"]) == 1
    assert QUEUES["rtfm_gate"][0].run_name == "xd_i3d_rtfm_i3d_s42"
    assert len(QUEUES["phase4_main"]) == 4
    assert len(QUEUES["phase4_pooling"]) == 2
    assert len(QUEUES["phase4_seeds"]) == 2
    # Total unique specs across all queues = 9.
    all_run_names = {
        s.run_name for q in QUEUES.values() for s in q
    }
    assert len(all_run_names) == 9, f"expected 9 unique run_names, got {sorted(all_run_names)}"


def test_run_name_deterministic():
    """D-30: <dataset>_<variant>[_<cache_variant>]_s<seed> format."""
    s = RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion.yaml")
    assert s.run_name == "ucf_gated_fusion_s42"

    s2 = RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion_2person.yaml", "2person",
    )
    assert s2.run_name == "ucf_gated_fusion_2person_s42"


def test_wandb_tags_format():
    """D-41: [phase4, <dataset>, <variant>, s<seed>] + <cache_variant>."""
    s = RunSpec("ucf", "gated_fusion", 123, "configs/gated_fusion.yaml")
    assert s.wandb_tags() == ["phase4", "ucf", "gated_fusion", "s123"]

    s2 = RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion_2person.yaml", "2person",
    )
    assert s2.wandb_tags() == ["phase4", "ucf", "gated_fusion", "s42", "2person"]


def test_dry_run_skips_subprocess(tmp_path, capsys):
    err_log = tmp_path / "runner-errors.log"
    summary = run_queue(
        QUEUES["rtfm_gate"], tmp_path, err_log, dry_run=True,
    )
    captured = capsys.readouterr()
    assert "[dry-run] would run xd_i3d_rtfm_i3d_s42" in captured.out
    assert summary == {"succeeded": [], "skipped": [], "failed": []}


def test_skip_if_done(tmp_path, capsys):
    """D-31: filesystem probe for .done marker skips already-complete runs."""
    run_dir = tmp_path / "xd_i3d_rtfm_i3d_s42"
    run_dir.mkdir()
    (run_dir / ".done").write_text("x", encoding="utf-8")
    err_log = tmp_path / "runner-errors.log"
    summary = run_queue(
        QUEUES["rtfm_gate"], tmp_path, err_log, dry_run=False,
    )
    captured = capsys.readouterr()
    assert "[skip] xd_i3d_rtfm_i3d_s42" in captured.out
    assert summary == {
        "succeeded": [], "skipped": ["xd_i3d_rtfm_i3d_s42"], "failed": [],
    }


def test_is_done_helper(tmp_path):
    """is_done() is the thin wrapper used by run_queue."""
    run_dir = tmp_path / "probe"
    run_dir.mkdir()
    assert not is_done(run_dir)
    (run_dir / ".done").write_text("x", encoding="utf-8")
    assert is_done(run_dir)


def test_run_one_success_appends_index(tmp_path, monkeypatch):
    """D-33: simulate both subprocess calls succeeding + evaluate.py writing
    eval_metrics.json; assert results-index.csv gets one row with the
    expected run_name."""
    from scripts import run_ablations

    err_log = tmp_path / "runner-errors.log"
    run_dir = tmp_path / "xd_i3d_rtfm_i3d_s42"

    def fake_run(cmd, **kwargs):
        if any("evaluate.py" in str(c) for c in cmd):
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "eval_metrics.json").write_text(
                json.dumps({
                    "auc": 0.85, "ap": 0.42,
                    "n_videos": 800, "n_frames": 123456,
                    "eval_timestamp": "2026-04-15T14:00:00",
                    "config_hash": "deadbeef",
                }), encoding="utf-8")

        class _R:
            returncode = 0
        return _R()

    monkeypatch.setattr(run_ablations.subprocess, "run", fake_run)
    spec = QUEUES["rtfm_gate"][0]
    status = run_ablations.run_one(spec, tmp_path, err_log)
    assert status["phase"] == "done", f"unexpected status: {status}"
    idx = tmp_path / "results-index.csv"
    assert idx.exists(), "results-index.csv was not appended"
    rows = idx.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2  # header + 1 row
    assert "xd_i3d_rtfm_i3d_s42" in rows[1]


def test_run_one_train_failure_logs_and_continues(tmp_path, monkeypatch):
    """D-32: train.py CalledProcessError -> logged to runner-errors.log,
    runner returns non-zero status for this spec, continues queue."""
    from scripts import run_ablations

    def fake_run(cmd, **kwargs):
        if any("train.py" in str(c) for c in cmd):
            raise run_ablations.subprocess.CalledProcessError(
                returncode=1, cmd=cmd,
            )

        class _R:
            returncode = 0
        return _R()

    monkeypatch.setattr(run_ablations.subprocess, "run", fake_run)
    err_log = tmp_path / "runner-errors.log"
    spec = QUEUES["rtfm_gate"][0]
    status = run_ablations.run_one(spec, tmp_path, err_log)
    assert status["phase"] == "train_failed"
    assert err_log.exists(), "runner-errors.log was not written"
    logtxt = err_log.read_text(encoding="utf-8")
    assert "xd_i3d_rtfm_i3d_s42" in logtxt
    assert "CalledProcessError" in logtxt


def test_run_queue_continues_on_failure(tmp_path, monkeypatch):
    """D-32: 2-spec queue, first fails, second succeeds -> summary has
    1 failed + 1 succeeded. Queue does NOT halt on first failure."""
    from scripts import run_ablations
    specs = [
        RunSpec("ucf", "gated_fusion", 123, "configs/gated_fusion.yaml"),
        RunSpec("ucf", "gated_fusion", 2024, "configs/gated_fusion.yaml"),
    ]

    def fake_run(cmd, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd)
        # First spec (seed=123) fails during training
        if "train.py" in cmd_str and "s123" in cmd_str:
            raise run_ablations.subprocess.CalledProcessError(
                returncode=1, cmd=cmd,
            )
        # Second spec (seed=2024): write eval_metrics.json for the evaluate call
        if "evaluate.py" in cmd_str:
            idx = list(cmd).index("--run-dir")
            run_dir = Path(cmd[idx + 1])
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "eval_metrics.json").write_text(
                json.dumps({
                    "auc": 0.86, "ap": 0.44,
                    "n_videos": 290, "n_frames": 1000000,
                    "eval_timestamp": "2026-04-15T14:30:00",
                    "config_hash": "cafe00",
                }), encoding="utf-8")

        class _R:
            returncode = 0
        return _R()

    monkeypatch.setattr(run_ablations.subprocess, "run", fake_run)
    err_log = tmp_path / "runner-errors.log"
    summary = run_queue(specs, tmp_path, err_log, dry_run=False)
    assert len(summary["succeeded"]) == 1, summary
    assert len(summary["failed"]) == 1, summary
    assert summary["failed"][0]["run"] == "ucf_gated_fusion_s123"


def test_cli_dry_run_no_preflight(tmp_path):
    """End-to-end CLI dry-run with --no-preflight (unit-test context)."""
    out = subprocess.run(
        [
            sys.executable, "scripts/run_ablations.py",
            "--queue", "rtfm_gate", "--dry-run", "--no-preflight",
            "--results-root", str(tmp_path),
        ],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    assert out.returncode == 0, (
        f"stderr: {out.stderr}\nstdout: {out.stdout}"
    )
    assert "[dry-run]" in out.stdout


def test_no_shell_true():
    """T-04-05-01: no shell=True in scripts/run_ablations.py."""
    src = (PROJECT_ROOT / "scripts" / "run_ablations.py").read_text(encoding="utf-8")
    assert "shell=True" not in src, "T-04-05-01: shell=True should not appear"
