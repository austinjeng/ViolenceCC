"""Subprocess ablation orchestrator for Phase 4 (D-26).

Loops over (variant, seed, dataset, cache_variant) tuples, invokes
``src/train.py`` and ``src/evaluate.py`` as subprocesses, and appends one
row per completed run to ``results/results-index.csv`` (D-33). Filesystem
probe on ``<run_dir>/.done`` provides resume-on-restart semantics (D-31).
Failed subprocess exit codes are logged to ``runner-errors.log`` and the
queue continues (D-32, D-34). wandb tags are per-spec (D-41).

Usage:
    python scripts/run_ablations.py --queue rtfm_gate
    python scripts/run_ablations.py --queue phase4_main
    python scripts/run_ablations.py --queue phase4_pooling --dry-run
    python scripts/run_ablations.py --queue phase4_seeds --no-preflight
    python scripts/run_ablations.py --queue rtfm_gate --results-root /tmp/x
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# PROJECT_ROOT is repo root (parent of scripts/). Tests pass --results-root
# to redirect the per-run output directory.
_THIS = Path(__file__).resolve()
PROJECT_ROOT = _THIS.parent.parent

# Make the project root importable before we pull in src.utils.csv_logger.
# We do the results_index_append import here (at module load time) so that
# transitive heavy imports (torch via src.utils.seed) resolve BEFORE any
# test monkeypatches subprocess.run; otherwise platform.machine() inside
# `import torch` would hit the mock and raise AttributeError.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from src.utils.csv_logger import results_index_append  # noqa: E402


@dataclass
class RunSpec:
    """Single (dataset, variant, seed, cache_variant) tuple.

    D-30 deterministic run_dir naming:
        <dataset>_<variant>[_<cache_variant>]_s<seed>

    Examples:
        ucf_gated_fusion_s42
        ucf_gated_fusion_2person_s42
        xd_i3d_rtfm_i3d_s42
    """

    dataset: str
    variant: str
    seed: int
    config: str
    cache_variant: str = ""

    @property
    def run_name(self) -> str:
        cv = f"_{self.cache_variant}" if self.cache_variant else ""
        return f"{self.dataset}_{self.variant}{cv}_s{self.seed}"

    def wandb_tags(self) -> List[str]:
        """D-41: [phase4, <dataset>, <variant>, s<seed>] + <cache_variant>."""
        tags = ["phase4", self.dataset, self.variant, f"s{self.seed}"]
        if self.cache_variant:
            tags.append(self.cache_variant)
        return tags


# ----------------------------------------------------------------------
# Queue definitions (deterministic, no timestamps). Order matters:
# rtfm_gate runs first (D-18 harness validation). phase4_seeds covers
# seeds {123, 2024}; seed=42 gated_fusion is inside phase4_main so we
# do not duplicate the run in phase4_seeds (D-27 / D-28).
# ----------------------------------------------------------------------
QUEUES = {
    "rtfm_gate": [
        RunSpec("xd_i3d", "rtfm_i3d", 42, "configs/rtfm_i3d.yaml"),
    ],
    "phase4_main": [
        RunSpec("ucf", "skeleton_only", 42, "configs/skeleton_only.yaml"),
        RunSpec("ucf", "clip_only",     42, "configs/clip_only.yaml"),
        RunSpec("ucf", "late_fusion",   42, "configs/late_fusion.yaml"),
        RunSpec("ucf", "gated_fusion",  42, "configs/gated_fusion.yaml"),
    ],
    "phase4_pooling": [
        RunSpec(
            "ucf", "gated_fusion", 42,
            "configs/gated_fusion_2person.yaml", "2person",
        ),
        RunSpec(
            "ucf", "gated_fusion", 42,
            "configs/gated_fusion_clip_mean.yaml", "clip_mean",
        ),
    ],
    "phase4_seeds": [
        RunSpec("ucf", "gated_fusion", 123, "configs/gated_fusion.yaml"),
        RunSpec("ucf", "gated_fusion", 2024, "configs/gated_fusion.yaml"),
        # seed=42 covered by phase4_main; not duplicated per D-27/D-28.
    ],
}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _results_root(cli_override: Optional[str]) -> Path:
    return Path(cli_override) if cli_override else PROJECT_ROOT / "results"


def _err_log_path(cli_override: Optional[str]) -> Path:
    # Tests pass a tmp_path-like override as the results root; keep the
    # runner-errors.log alongside it so the test's tmp_path captures it.
    base = Path(cli_override) if cli_override else PROJECT_ROOT
    return base / "runner-errors.log"


def is_done(run_dir: Path) -> bool:
    """D-31 filesystem probe — .done marker is the LAST write of a completed
    (train + evaluate) run, so its presence means all other outputs exist."""
    return (run_dir / ".done").exists()


def log_error(err_log: Path, spec: "RunSpec", exc_repr: str) -> None:
    """D-32: append one line per failed spec to runner-errors.log."""
    err_log.parent.mkdir(parents=True, exist_ok=True)
    with open(err_log, "a", encoding="utf-8") as f:
        f.write(
            f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {spec.run_name}\t{exc_repr}\n"
        )


def run_one(
    spec: "RunSpec",
    results_root: Path,
    err_log: Path,
    timeout_s: int = 7200,
) -> dict:
    """Run train + evaluate for one spec. Returns a status dict."""
    run_dir = results_root / spec.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    status = {
        "spec": spec.run_name,
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # Train (D-30 --run-name override for deterministic run_dir)
    train_cmd = [
        sys.executable, "src/train.py",
        "--config", spec.config,
        "--seed", str(spec.seed),
        "--results-dir", str(results_root),
        "--run-name", spec.run_name,
    ]
    try:
        subprocess.run(
            train_cmd, check=True, timeout=timeout_s,
            cwd=str(PROJECT_ROOT),
        )
    except subprocess.CalledProcessError as e:
        status["phase"] = "train_failed"
        log_error(
            err_log, spec,
            f"CalledProcessError(returncode={e.returncode})",
        )
        return status
    except subprocess.TimeoutExpired:
        status["phase"] = "train_timeout"
        log_error(err_log, spec, f"TimeoutExpired({timeout_s}s)")
        return status

    # Evaluate (Plan 04-02 CLI: --run-dir + --split test by default)
    eval_cmd = [
        sys.executable, "src/evaluate.py",
        "--run-dir", str(run_dir),
        "--split", "test",
    ]
    try:
        subprocess.run(
            eval_cmd, check=True, timeout=max(timeout_s // 4, 600),
            cwd=str(PROJECT_ROOT),
        )
    except subprocess.CalledProcessError as e:
        status["phase"] = "eval_failed"
        log_error(
            err_log, spec,
            f"CalledProcessError(returncode={e.returncode})",
        )
        return status
    except subprocess.TimeoutExpired:
        status["phase"] = "eval_timeout"
        log_error(err_log, spec, "eval TimeoutExpired")
        return status

    # Append to results-index.csv (D-33 + D-34)
    metrics_path = run_dir / "eval_metrics.json"
    if not metrics_path.exists():
        status["phase"] = "eval_missing_metrics"
        log_error(err_log, spec, "eval_metrics.json not written")
        return status
    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception as exc:
        status["phase"] = "eval_bad_json"
        log_error(err_log, spec, f"json parse failed: {exc}")
        return status

    # results_index_append imported at module top (see comment there) so
    # that torch loads before monkeypatches intercept subprocess.run.
    row = {
        "run_name": spec.run_name,
        "variant": spec.variant,
        "dataset": spec.dataset,
        "seed": spec.seed,
        "cache_variant": spec.cache_variant,
        "auc": metrics.get("auc", ""),
        "ap": metrics.get("ap", ""),
        "n_videos": metrics.get("n_videos", ""),
        "n_frames": metrics.get("n_frames", ""),
        "start_time": status["start_time"],
        "end_time": metrics.get("eval_timestamp", ""),
        "config_hash": metrics.get("config_hash", ""),
    }
    results_index_append(results_root / "results-index.csv", row)
    status["phase"] = "done"
    return status


def run_queue(
    specs: List["RunSpec"],
    results_root: Path,
    err_log: Path,
    dry_run: bool = False,
) -> dict:
    """Run a list of specs; skip completed (.done present); log failures and
    continue. Returns a summary with succeeded/skipped/failed."""
    summary = {"succeeded": [], "skipped": [], "failed": []}
    for spec in specs:
        run_dir = results_root / spec.run_name
        if is_done(run_dir):
            summary["skipped"].append(spec.run_name)
            print(f"[skip] {spec.run_name} (.done present)")
            continue
        if dry_run:
            print(f"[dry-run] would run {spec.run_name}")
            continue
        print(f"[start] {spec.run_name}")
        status = run_one(spec, results_root, err_log)
        if status.get("phase") == "done":
            summary["succeeded"].append(spec.run_name)
        else:
            summary["failed"].append(
                {"run": spec.run_name, "phase": status.get("phase", "unknown")}
            )
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase 4 ablation orchestrator (D-26)"
    )
    ap.add_argument(
        "--queue", required=True, choices=sorted(QUEUES),
        help="Queue to run: rtfm_gate, phase4_main, phase4_pooling, phase4_seeds",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Print [dry-run] plan without invoking train.py / evaluate.py",
    )
    ap.add_argument(
        "--no-preflight", action="store_true",
        help="Skip scripts/wandb_preflight.py (unit tests or CSV-only mode)",
    )
    ap.add_argument(
        "--results-root", default=None,
        help="Override results/ directory (tests redirect to tmp_path)",
    )
    args = ap.parse_args()

    results_root = _results_root(args.results_root)
    err_log = _err_log_path(args.results_root)

    if not args.no_preflight and not args.dry_run:
        preflight = subprocess.run(
            [sys.executable, "scripts/wandb_preflight.py"],
            cwd=str(PROJECT_ROOT),
        )
        if preflight.returncode != 0:
            print(
                "wandb preflight failed; aborting queue",
                file=sys.stderr,
            )
            return 2

    specs = QUEUES[args.queue]
    summary = run_queue(specs, results_root, err_log, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
