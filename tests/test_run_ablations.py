"""Phase 4 D-26..D-34 + D-41 — scripts/run_ablations.py orchestrator.

Tests:
  R1 --help lists all 4 queues
  R2 dry-run prints plan but skips subprocess
  R3 .done probe skips already-complete runs
  R4 success path appends to results-index.csv
  R5 train failure logs to runner-errors.log and returns non-zero status
  R6 queue continues to next spec after a failure
  R7 RunSpec.run_name + wandb_tags match D-30 / D-41 formats
  R8 queue definitions: 1 + 1 + 4 + 2 + 2 + 4 + 2 + 2 = 18 specs
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
    for q in ("rtfm_gate", "phase4_main", "phase4_pooling", "phase4_seeds",
              "phase4c_main", "phase4c_pooling", "phase4c_seeds",
              "phase7_sweep", "phase7_sweep_ext", "phase7_sweep_ext2",
              "phase7_sweep_ext3", "phase7_confirm",
              "phase7_ucf_sweep", "phase7_ucf_sweep_ext",
              "phase7_ucf_sweep_ext2", "phase7_ucf_confirm",
              "phase8_ucf_main", "phase8_xd_main",
              "phase8_ucf_pooling", "phase8_xd_pooling",
              "phase8_ucf_seeds", "phase8_xd_seeds"):
        assert q in combined, f"missing queue {q!r} in --help: {combined[:300]}"


def test_queue_definitions():
    """D-26/D-27/D-28: rtfm_gate=1, phase4_main=4, phase4_pooling=2,
    phase4_seeds=2 (seed=42 covered by phase4_main, not duplicated).
    Plan 04b-05 Rule 1 scope expansion: rtfm_gate_flow=1 (Flow diagnostic).
    Phase 7 extended sweep: 20+18+28+33=99 XD configs, 20+46+33=99 UCF configs,
    plus 6 XD confirm and 6 UCF confirm."""
    assert len(QUEUES["rtfm_gate"]) == 1
    assert QUEUES["rtfm_gate"][0].run_name == "xd_i3d_rtfm_i3d_s42"
    assert len(QUEUES["rtfm_gate_flow"]) == 1
    assert QUEUES["rtfm_gate_flow"][0].run_name == "xd_i3d_rtfm_i3d_flow_s42"
    assert len(QUEUES["phase4_main"]) == 4
    assert len(QUEUES["phase4_pooling"]) == 2
    assert len(QUEUES["phase4_seeds"]) == 2
    # Phase 4c queues (D-02)
    assert len(QUEUES["phase4c_main"]) == 4
    assert len(QUEUES["phase4c_pooling"]) == 2
    assert len(QUEUES["phase4c_seeds"]) == 2
    # Phase 4c run_name spot checks
    assert QUEUES["phase4c_main"][3].run_name == "xd_gated_fusion_s42"
    assert QUEUES["phase4c_seeds"][0].run_name == "xd_gated_fusion_s123"
    assert QUEUES["phase4c_pooling"][0].run_name == "xd_gated_fusion_2person_s42"
    # Phase 7 XD sweep queues (3 expansion rounds)
    assert len(QUEUES["phase7_sweep"]) == 20
    assert len(QUEUES["phase7_sweep_ext"]) == 18
    assert len(QUEUES["phase7_sweep_ext2"]) == 28
    assert len(QUEUES["phase7_sweep_ext3"]) == 33
    assert len(QUEUES["phase7_confirm"]) == 6
    # Phase 7 UCF sweep queues
    assert len(QUEUES["phase7_ucf_sweep"]) == 20
    assert len(QUEUES["phase7_ucf_sweep_ext"]) == 46
    assert len(QUEUES["phase7_ucf_sweep_ext2"]) == 33
    assert len(QUEUES["phase7_ucf_confirm"]) == 6
    # Phase 8 SigLIP2 backbone comparison queues
    assert len(QUEUES["phase8_ucf_main"]) == 3       # clip_only, late, gated (no skeleton_only)
    assert len(QUEUES["phase8_xd_main"]) == 3
    assert len(QUEUES["phase8_ucf_pooling"]) == 2     # 2person, clip_mean
    assert len(QUEUES["phase8_xd_pooling"]) == 2
    assert len(QUEUES["phase8_ucf_seeds"]) == 2       # seeds 123, 2024
    assert len(QUEUES["phase8_xd_seeds"]) == 2
    # Phase 8 run_name spot checks
    assert QUEUES["phase8_ucf_main"][2].run_name == "ucf_gated_fusion_siglip2_s42"
    assert QUEUES["phase8_xd_seeds"][0].run_name == "xd_gated_fusion_siglip2_s123"
    # Total unique specs across all queues = 238 (224 + 14 Phase 8).
    all_run_names = {
        s.run_name for q in QUEUES.values() for s in q
    }
    assert len(all_run_names) == 238, f"expected 238 unique run_names, got {len(all_run_names)}"


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


def test_phase7_run_name():
    """D-11: RunSpec.run_name with lr_override and k_topk_override."""
    spec = RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml",
                   lr_override=5e-5, k_topk_override=1)
    assert spec.run_name == "xd_gated_fusion_lr5e5_k1_s42"

    spec2 = RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml",
                    lr_override=1e-4, k_topk_override=3)
    assert spec2.run_name == "xd_gated_fusion_lr1e4_k3_s42"

    spec3 = RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml",
                    lr_override=3e-4, k_topk_override=7)
    assert spec3.run_name == "xd_gated_fusion_lr3e4_k7_s42"


def test_phase7_decimal_lr_format():
    """_fmt_lr handles decimal coefficients: 6.5e-4 -> '6p5e4'."""
    spec = RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml",
                   lr_override=6.5e-4, k_topk_override=2)
    assert spec.run_name == "xd_gated_fusion_lr6p5e4_k2_s42"

    spec2 = RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml",
                    lr_override=1.5e-3, k_topk_override=9)
    assert spec2.run_name == "xd_gated_fusion_lr1p5e3_k9_s42"

    spec3 = RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion.yaml",
                    lr_override=7.5e-4, k_topk_override=1)
    assert spec3.run_name == "ucf_gated_fusion_lr7p5e4_k1_s42"


def test_phase7_run_name_no_override():
    """Existing RunSpec without overrides produces unchanged run_name."""
    spec = RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion.yaml")
    assert spec.run_name == "ucf_gated_fusion_s42"
    # With cache_variant
    spec2 = RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion.yaml", "2person")
    assert spec2.run_name == "ucf_gated_fusion_2person_s42"


def test_phase7_cli_overrides_in_train_cmd(tmp_path, monkeypatch):
    """D-10: run_one() forwards --lr and --k-topk when overrides are set."""
    from scripts import run_ablations

    spec = RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml",
                   lr_override=2e-4, k_topk_override=5)
    err_log = tmp_path / "errors.log"

    captured_cmds = []

    def fake_run(cmd, **kwargs):
        captured_cmds.append(list(str(c) for c in cmd))
        if any("evaluate.py" in str(c) for c in cmd):
            run_dir = tmp_path / spec.run_name
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "eval_metrics.json").write_text(
                json.dumps({
                    "auc": 0.72, "ap": 0.71,
                    "n_videos": 800, "n_frames": 100000,
                    "eval_timestamp": "2026-05-01T00:00:00",
                    "config_hash": "abc123",
                }), encoding="utf-8")

        class _R:
            returncode = 0
        return _R()

    monkeypatch.setattr(run_ablations.subprocess, "run", fake_run)
    run_ablations.run_one(spec, tmp_path, err_log)

    # First captured command is train
    train_cmd = captured_cmds[0]
    assert "--lr" in train_cmd
    assert "0.0002" in train_cmd or "2e-04" in train_cmd
    assert "--k-topk" in train_cmd
    assert "5" in train_cmd


def test_phase7_sweep_queue():
    """D-03: phase7_sweep contains 5 lr x 4 k_topk = 20 RunSpec entries."""
    assert "phase7_sweep" in QUEUES
    assert len(QUEUES["phase7_sweep"]) == 20
    # All are xd gated_fusion seed=42
    for spec in QUEUES["phase7_sweep"]:
        assert spec.dataset == "xd"
        assert spec.variant == "gated_fusion"
        assert spec.seed == 42
        assert spec.config == "configs/gated_fusion_xd.yaml"
        assert spec.lr_override is not None
        assert spec.k_topk_override is not None
    # Spot check first and last
    assert QUEUES["phase7_sweep"][0].run_name == "xd_gated_fusion_lr5e5_k1_s42"
    assert QUEUES["phase7_sweep"][-1].run_name == "xd_gated_fusion_lr5e4_k7_s42"
    # All run_names unique
    names = [s.run_name for s in QUEUES["phase7_sweep"]]
    assert len(names) == len(set(names)), f"duplicate run_names: {names}"


def test_no_shell_true():
    """T-04-05-01: no shell=True in scripts/run_ablations.py."""
    src = (PROJECT_ROOT / "scripts" / "run_ablations.py").read_text(encoding="utf-8")
    assert "shell=True" not in src, "T-04-05-01: shell=True should not appear"
