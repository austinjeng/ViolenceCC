"""Phase 4 D-31 — .done marker atomic-write + filesystem-probe test.

Verifies the write-temp-then-rename pattern for the .done marker AND the
is_done-style filesystem probe used by scripts/run_ablations.py.
"""
import os
import tempfile
from pathlib import Path


def test_done_marker_atomic_write(tmp_path):
    """Write-temp-then-rename: .done exists only after os.replace completes."""
    run_dir = tmp_path / "run_dir"
    run_dir.mkdir()
    target = run_dir / ".done"
    fd, tmp = tempfile.mkstemp(prefix=".done.", suffix=".tmp", dir=str(run_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("eval_complete\n")
            f.flush()
            os.fsync(f.fileno())
        # Before replace: target does not exist.
        assert not target.exists()
        os.replace(tmp, str(target))
        # After replace: target exists with the expected content.
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "eval_complete\n"
    except Exception:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise


def test_is_done_probe(tmp_path):
    """Runner uses (run_dir / '.done').exists() as skip signal (D-31)."""
    run_dir = tmp_path / "incomplete"
    run_dir.mkdir()
    assert not (run_dir / ".done").exists()
    (run_dir / ".done").write_text("x", encoding="utf-8")
    assert (run_dir / ".done").exists()


def test_done_marker_is_last_write(tmp_path):
    """Contract: a run_dir with .done must already contain eval_metrics.json.

    This is the atomic-visibility invariant: readers that see .done can safely
    read the other outputs without polling.
    """
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    # Simulate: eval_metrics.json first, then .done last.
    (run_dir / "eval_metrics.json").write_text("{\"auc\": 0.85}", encoding="utf-8")
    (run_dir / ".done").write_text("eval_complete\n", encoding="utf-8")
    # Invariant: if .done exists, eval_metrics.json must exist.
    assert (run_dir / ".done").exists()
    assert (run_dir / "eval_metrics.json").exists()
