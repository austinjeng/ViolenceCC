"""Subprocess ablation orchestrator for Phase 4 + Phase 5 TTA (D-26, D-09).

Loops over (variant, seed, dataset, cache_variant) tuples, invokes
``src/train.py`` and ``src/evaluate.py`` as subprocesses, and appends one
row per completed run to ``results/results-index.csv`` (D-33). Filesystem
probe on ``<run_dir>/.done`` provides resume-on-restart semantics (D-31).
Failed subprocess exit codes are logged to ``runner-errors.log`` and the
queue continues (D-32, D-34). wandb tags are per-spec (D-41).

Phase 5 TTA extension (D-09): Three TTA queues (tta_source_only,
tta_tent_grid, tta_sar_grid) invoke ``src/tta/evaluate_tta.py`` as
subprocesses for ~500 total runs across 4 corruption types x 5 severities
x {source_only, TENT(4 LRs), SAR(4 LRs x 5 rhos)}.

Usage:
    python scripts/run_ablations.py --queue rtfm_gate
    python scripts/run_ablations.py --queue phase4_main
    python scripts/run_ablations.py --queue phase4_pooling --dry-run
    python scripts/run_ablations.py --queue phase4_seeds --no-preflight
    python scripts/run_ablations.py --queue rtfm_gate --results-root /tmp/x
    python scripts/run_ablations.py --queue tta_source_only --no-preflight
    python scripts/run_ablations.py --queue tta_tent_grid --no-preflight
    python scripts/run_ablations.py --queue tta_sar_grid --no-preflight --dry-run
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
    lr_override: float | None = None
    k_topk_override: int | None = None

    def _fmt_lr(self) -> str:
        """Format LR for run_name: 5e-04 -> '5e4', 6.5e-04 -> '6p5e4'."""
        if self.lr_override is None:
            return ""
        s = f"{self.lr_override:.1e}"  # "5.0e-04" or "6.5e-04"
        coeff, exp = s.split("e")
        exp_val = abs(int(exp))
        if coeff.endswith(".0"):
            coeff = coeff[:-2]
        else:
            coeff = coeff.replace(".", "p")
        return f"{coeff}e{exp_val}"

    @property
    def run_name(self) -> str:
        cv = f"_{self.cache_variant}" if self.cache_variant else ""
        hp = ""
        if self.lr_override is not None:
            hp += f"_lr{self._fmt_lr()}"
        if self.k_topk_override is not None:
            hp += f"_k{self.k_topk_override}"
        return f"{self.dataset}_{self.variant}{cv}{hp}_s{self.seed}"

    def wandb_tags(self) -> List[str]:
        """D-41: [phase4, <dataset>, <variant>, s<seed>] + <cache_variant>."""
        tags = ["phase4", self.dataset, self.variant, f"s{self.seed}"]
        if self.cache_variant:
            tags.append(self.cache_variant)
        return tags


@dataclass
class TTARunSpec:
    """Single TTA evaluation run (D-09).

    D-13 deterministic naming: {method}_{type}_{severity}_lr{lr}[_rho{rho}]
    """

    corruption_type: str   # gaussian_noise, motion_blur, jpeg_compression, brightness
    severity: int          # 1-5
    method: str            # source_only, tent, sar
    lr: float              # from {1e-4, 5e-4, 1e-3, 5e-3}
    rho: float = 0.0      # SAR only, from {0.001, 0.005, 0.01, 0.05, 0.1}
    source_run: str = "ucf_gated_fusion_s42"

    @property
    def run_name(self) -> str:
        """D-13 deterministic naming: {method}_{type}_{severity}_lr{lr}[_rho{rho}]"""
        base = f"{self.method}_{self.corruption_type}_{self.severity}_lr{self.lr}"
        if self.method == "sar" and self.rho > 0:
            base += f"_rho{self.rho}"
        return base


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
    # Plan 04b-05 Task 3 HUMAN-UAT remediation Option A: Flow-only diagnostic.
    # RGB cache is truncated at V/W/Y tail (729 missing); Flow is 100% complete.
    # Directory junction E:/i3d-features-flow/ maps Flow/FlowTest to RGB/RGBTest.
    "rtfm_gate_flow": [
        RunSpec("xd_i3d", "rtfm_i3d_flow", 42, "configs/rtfm_i3d_flow.yaml"),
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
    "phase4c_main": [
        RunSpec("xd", "skeleton_only", 42, "configs/skeleton_only_xd.yaml"),
        RunSpec("xd", "clip_only",     42, "configs/clip_only_xd.yaml"),
        RunSpec("xd", "late_fusion",   42, "configs/late_fusion_xd.yaml"),
        RunSpec("xd", "gated_fusion",  42, "configs/gated_fusion_xd.yaml"),
    ],
    "phase4c_pooling": [
        RunSpec(
            "xd", "gated_fusion", 42,
            "configs/gated_fusion_xd_2person.yaml", "2person",
        ),
        RunSpec(
            "xd", "gated_fusion", 42,
            "configs/gated_fusion_xd_clip_mean.yaml", "clip_mean",
        ),
    ],
    "phase4c_seeds": [
        RunSpec("xd", "gated_fusion", 123, "configs/gated_fusion_xd.yaml"),
        RunSpec("xd", "gated_fusion", 2024, "configs/gated_fusion_xd.yaml"),
        # seed=42 covered by phase4c_main; not duplicated per D-27/D-28.
    ],
}


# ----------------------------------------------------------------------
# Phase 7 hyperparameter sweep queue definitions (D-01, D-02, D-03)
# 5 lr x 4 k_topk = 20 runs at seed=42
# ----------------------------------------------------------------------
_LR_SWEEP = [5e-5, 1e-4, 2e-4, 3e-4, 5e-4]
_K_SWEEP = [1, 3, 5, 7]

QUEUES["phase7_sweep"] = [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP for k in _K_SWEEP
]  # 20 runs

# Phase 7 extension: explore beyond original grid edges
_LR_SWEEP_EXT = [7e-4, 1e-3]
_K_SWEEP_EXT = [2, 9]

QUEUES["phase7_sweep_ext"] = [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP_EXT for k in _K_SWEEP
] + [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP for k in _K_SWEEP_EXT
]  # 8 + 10 = 18 runs

# Phase 7 extension 2: fine-grain the peak LR zone + fill missing cells
_LR_SWEEP_EXT2 = [4e-4, 6e-4, 8e-4, 9e-4]
_K_ALL = [1, 2, 3, 5, 7, 9]

QUEUES["phase7_sweep_ext2"] = [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP_EXT2 for k in _K_ALL
] + [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP_EXT for k in _K_SWEEP_EXT
]  # 24 + 4 = 28 runs

# Phase 7 extension 3: explore above 1e-3 + fine-grain both k=2 peaks
_LR_ABOVE = [1.2e-3, 1.5e-3, 2e-3]
_LR_FINEGRAIN = [6.5e-4, 7.5e-4, 8.5e-4, 1.1e-3, 1.3e-3]
_K_TOP3 = [1, 2, 3]

QUEUES["phase7_sweep_ext3"] = [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_ABOVE for k in _K_ALL
] + [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_FINEGRAIN for k in _K_TOP3
]  # 18 + 15 = 33 runs


# Phase 7 confirmation: 3-seed on top 2 sweep winners
QUEUES["phase7_confirm"] = [
    RunSpec("xd", "gated_fusion", s, "configs/gated_fusion_xd.yaml",
            lr_override=1e-3, k_topk_override=2)
    for s in [42, 123, 2024]
] + [
    RunSpec("xd", "gated_fusion", s, "configs/gated_fusion_xd.yaml",
            lr_override=7e-4, k_topk_override=2)
    for s in [42, 123, 2024]
]  # 6 runs (s42 for both will be skipped via .done)

# Phase 7 UCF-Crime sweep: same grid as XD, 3 batches
# Batch 1: original 5x4 grid (20 runs)
QUEUES["phase7_ucf_sweep"] = [
    RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP for k in _K_SWEEP
]  # 20 runs

# Batch 2: edge exploration + fill gaps (18 + 28 = 46 runs)
QUEUES["phase7_ucf_sweep_ext"] = [
    RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP_EXT for k in _K_SWEEP
] + [
    RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP for k in _K_SWEEP_EXT
] + [
    RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP_EXT2 for k in _K_ALL
] + [
    RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP_EXT for k in _K_SWEEP_EXT
]  # 8+10+24+4 = 46 runs

# Batch 3: fine-grain peaks + above 1e-3 (33 runs)
QUEUES["phase7_ucf_sweep_ext2"] = [
    RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_ABOVE for k in _K_ALL
] + [
    RunSpec(
        "ucf", "gated_fusion", 42,
        "configs/gated_fusion.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_FINEGRAIN for k in _K_TOP3
]  # 18+15 = 33 runs

# Phase 7 UCF confirmation: 3-seed on top 2 sweep winners
QUEUES["phase7_ucf_confirm"] = [
    RunSpec("ucf", "gated_fusion", s, "configs/gated_fusion.yaml",
            lr_override=1.5e-3, k_topk_override=9)
    for s in [42, 123, 2024]
] + [
    RunSpec("ucf", "gated_fusion", s, "configs/gated_fusion.yaml",
            lr_override=1e-3, k_topk_override=1)
    for s in [42, 123, 2024]
]  # 6 runs (s42 for both will be skipped via .done)


# ----------------------------------------------------------------------
# Phase 5 TTA queue definitions (D-09)
# 4 corruption types x 5 severities = 20 conditions per method
# source_only: 20 runs, tent: 80 runs (x4 LRs), sar: 400 runs (x4 LRs x5 rhos)
# Total: 500 runs
# ----------------------------------------------------------------------
_CORRUPTION_TYPES = ["gaussian_noise", "jpeg_compression", "brightness", "motion_blur"]
_SEVERITIES = [1, 2, 3, 4, 5]
_LR_GRID = [1e-4, 5e-4, 1e-3, 5e-3]
_RHO_GRID = [0.001, 0.005, 0.01, 0.05, 0.1]

TTA_QUEUES = {
    "tta_source_only": [
        TTARunSpec(ct, sev, "source_only", 0.0)
        for ct in _CORRUPTION_TYPES for sev in _SEVERITIES
    ],  # 20 runs
    "tta_tent_grid": [
        TTARunSpec(ct, sev, "tent", lr)
        for ct in _CORRUPTION_TYPES for sev in _SEVERITIES for lr in _LR_GRID
    ],  # 80 runs
    "tta_sar_grid": [
        TTARunSpec(ct, sev, "sar", lr, rho)
        for ct in _CORRUPTION_TYPES for sev in _SEVERITIES
        for lr in _LR_GRID for rho in _RHO_GRID
    ],  # 400 runs
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
    # Phase 7 D-10: forward CLI overrides
    if spec.lr_override is not None:
        train_cmd.extend(["--lr", str(spec.lr_override)])
    if spec.k_topk_override is not None:
        train_cmd.extend(["--k-topk", str(spec.k_topk_override)])
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


# ----------------------------------------------------------------------
# Phase 5 TTA run helpers (D-09)
# ----------------------------------------------------------------------
def run_one_tta(
    spec: "TTARunSpec",
    results_root: Path,
    err_log: Path,
    timeout_s: int = 600,
) -> dict:
    """Run one TTA evaluation via subprocess to src/tta/evaluate_tta.py."""
    run_dir = results_root / "tta" / spec.run_name
    status = {
        "spec": spec.run_name,
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    source_dir = results_root / spec.source_run
    cmd = [
        sys.executable, "src/tta/evaluate_tta.py",
        "--source-run", str(source_dir),
        "--corruption", spec.corruption_type,
        "--severity", str(spec.severity),
        "--method", spec.method,
        "--lr", str(spec.lr),
        "--rho", str(spec.rho),
        "--output-dir", str(run_dir),
    ]
    try:
        subprocess.run(cmd, check=True, timeout=timeout_s, cwd=str(PROJECT_ROOT))
    except subprocess.CalledProcessError as e:
        status["phase"] = "tta_failed"
        log_error(err_log, spec, f"CalledProcessError(rc={e.returncode})")
        return status
    except subprocess.TimeoutExpired:
        status["phase"] = "tta_timeout"
        log_error(err_log, spec, f"TimeoutExpired({timeout_s}s)")
        return status

    # Append to results-index.csv
    metrics_path = run_dir / "eval_metrics.json"
    if not metrics_path.exists():
        status["phase"] = "tta_missing_metrics"
        log_error(err_log, spec, "eval_metrics.json not written")
        return status
    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception as exc:
        status["phase"] = "tta_bad_json"
        log_error(err_log, spec, f"json parse failed: {exc}")
        return status

    row = {
        "run_name": spec.run_name,
        "variant": "gated_fusion",
        "dataset": "ucf",
        "seed": 42,
        "cache_variant": f"{spec.corruption_type}_{spec.severity}",
        "auc": metrics.get("auc", ""),
        "ap": metrics.get("ap", ""),
        "n_videos": metrics.get("n_videos", ""),
        "n_frames": metrics.get("n_frames", ""),
        "start_time": status["start_time"],
        "end_time": metrics.get("eval_timestamp", ""),
        "config_hash": "",
        # TTA-specific columns
        "method": spec.method,
        "corruption_type": spec.corruption_type,
        "severity": spec.severity,
        "lr": spec.lr,
        "rho": spec.rho if spec.method == "sar" else "",
    }
    results_index_append(results_root / "results-index.csv", row)
    status["phase"] = "done"
    return status


def run_queue_tta(
    specs: List["TTARunSpec"],
    results_root: Path,
    err_log: Path,
    dry_run: bool = False,
) -> dict:
    """Run a list of TTA specs; skip completed (.done present); log failures
    and continue. Returns a summary with succeeded/skipped/failed."""
    summary = {"succeeded": [], "skipped": [], "failed": []}
    for spec in specs:
        run_dir = results_root / "tta" / spec.run_name
        if is_done(run_dir):
            summary["skipped"].append(spec.run_name)
            print(f"[skip] {spec.run_name} (.done present)")
            continue
        if dry_run:
            print(f"[dry-run] would run {spec.run_name}")
            continue
        print(f"[start] {spec.run_name}")
        status = run_one_tta(spec, results_root, err_log)
        if status.get("phase") == "done":
            summary["succeeded"].append(spec.run_name)
        else:
            summary["failed"].append(
                {"run": spec.run_name, "phase": status.get("phase", "unknown")}
            )
    return summary


def main() -> int:
    all_queue_names = sorted(set(list(QUEUES) + list(TTA_QUEUES)))
    ap = argparse.ArgumentParser(
        description="Phase 4 ablation + Phase 5 TTA + Phase 7 sweep orchestrator (D-26, D-09)"
    )
    ap.add_argument(
        "--queue", required=True, choices=all_queue_names,
        help="Queue to run (Phase 4: rtfm_gate, phase4_main, etc.; "
             "Phase 5 TTA: tta_source_only, tta_tent_grid, tta_sar_grid)",
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

    # TTA queues skip wandb preflight (evaluation only, no training)
    is_tta = args.queue in TTA_QUEUES

    if not is_tta and not args.no_preflight and not args.dry_run:
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

    if is_tta:
        specs = TTA_QUEUES[args.queue]
        summary = run_queue_tta(
            specs, results_root, err_log, dry_run=args.dry_run,
        )
    else:
        specs = QUEUES[args.queue]
        summary = run_queue(
            specs, results_root, err_log, dry_run=args.dry_run,
        )
    print(json.dumps(summary, indent=2))
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
