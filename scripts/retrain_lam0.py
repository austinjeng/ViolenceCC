"""Resumable lambda=0 retrain + full-length re-eval over the 58 canonical runs.

This is the Stage-2 orchestrator for the lambda=0 (drop temporal smoothness)
adoption. It enumerates every canonical result dir (those with BOTH
``config_snapshot.json`` and ``eval_metrics.json``) EXCLUDING any whose name
contains ``_i3d_`` (the RTFM i3d baseline is not part of the lambda=0
measurement and is not retrained), yielding 58 runs (29 ``ucf_*`` + 29
``xd_*``). For each run it:

  1. Backs up the existing artifacts to ``*.pre_lam0.bak`` (only if no .bak
     exists yet) -- results/ is gitignored and NOT git-revertible, so the .bak
     IS the recovery path (T-rww-01).
  2. Loads the EXACT resolved config from config_snapshot.json, sets
     train.lam_smooth = 0.0, and for UCF runs sets
     paths.snippet_boundaries_dir = E:/snippets/ucf (full-length H1 eval).
  3. Writes that config to a temp YAML and reruns src/train.py (overwriting the
     canonical dir via --run-name) then src/evaluate.py --split test.
  4. Records the run in results/_lam0_done.txt for resume.

Stage 1 (config edits + this script) only ever invokes this with ``--dry-run``,
which prints the plan and EXITS without importing torch, writing artifacts, or
training (T-rww-02). Stage 2 (user-run, in vcc-main, NO --dry-run) executes the
batch. The script NEVER touches paper/tables/figures.

Usage:
    # Stage 1 verification (no training, no artifacts written):
    conda run -n vcc-main python scripts/retrain_lam0.py --dry-run

    # Stage 2 (user-run, VISIBLE terminal -- this trains ~58 runs):
    conda run -n vcc-main python scripts/retrain_lam0.py
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# PROJECT_ROOT is repo root (parent of scripts/).
_THIS = Path(__file__).resolve()
PROJECT_ROOT = _THIS.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DONE_LOG = RESULTS_DIR / "_lam0_done.txt"
ERR_LOG = RESULTS_DIR / "retrain_lam0_errors.log"
UCF_BOUNDARIES = "E:/snippets/ucf"

# Artifacts backed up (once) before the first overwrite of a run dir.
BACKUP_FILES = [
    "eval_metrics.json",
    "eval_scores.npz",
    "best_model.pth",
    "train_log.csv",
    "config_snapshot.json",
]

# Make the project root importable (for src/train.py + src/evaluate.py cwd use).
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_snapshot_as_config(snapshot_path):
    """Reuse src/utils/config.py's load_snapshot_as_config WITHOUT importing the
    src.utils package (whose __init__ eagerly imports torch via seed.py). We load
    the config module by file path so --dry-run never pulls in torch (T-rww-02);
    the parsing logic itself is the project's, not reimplemented here."""
    module_path = PROJECT_ROOT / "src" / "utils" / "config.py"
    spec = importlib.util.spec_from_file_location("_vcc_config_standalone", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_snapshot_as_config(snapshot_path)


@dataclass
class RetrainSpec:
    """One canonical run to retrain at lambda=0."""

    run_name: str           # canonical results dir name (overwrite target)
    snapshot_path: Path     # source config_snapshot.json
    seed: int
    dataset: str            # "ucf" | "xd"
    variant: str            # model variant (gated_fusion, clip_only, ...)
    backbone: str           # label inferred from clip_features path tail

    @property
    def eval_mode(self) -> str:
        return "UCF-full-length" if self.dataset == "ucf" else "XD-standard"


def _infer_backbone(clip_features: Optional[str], variant: str) -> str:
    """Dry-run label only: infer backbone from the clip_features path tail."""
    if variant == "skeleton_only":
        return "n/a(skeleton)"
    if not clip_features:
        return "unknown"
    tail = clip_features.rstrip("/").rsplit("/", 1)[-1]
    return {
        "clip": "clip-vit-b-16",
        "clip_mean": "clip-vit-b-16-mean",
        "siglip2": "siglip2-vit-b-16",
        "siglip2_so400m": "siglip2-so400m",
        "siglip2_giant": "siglip2-giant",
    }.get(tail, tail)


def enumerate_runs() -> List[RetrainSpec]:
    """Scan results/ for canonical runs (config_snapshot.json + eval_metrics.json),
    excluding any dir whose name contains ``_i3d_``. Sorted by dir name for
    deterministic dry-run output. Reuses src/utils/config.load_snapshot_as_config
    (no reimplementation)."""
    specs: List[RetrainSpec] = []
    for d in sorted(RESULTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        if "_i3d_" in d.name:
            continue
        snap = d / "config_snapshot.json"
        if not snap.exists() or not (d / "eval_metrics.json").exists():
            continue
        cfg = _load_snapshot_as_config(snap)
        dataset = cfg.get("dataset", "ucf")
        variant = cfg.get("model", {}).get("variant", "unknown")
        clip_features = cfg.get("paths", {}).get("clip_features")
        specs.append(
            RetrainSpec(
                run_name=d.name,
                snapshot_path=snap,
                seed=int(cfg.get("seed", 42)),
                dataset=dataset,
                variant=variant,
                backbone=_infer_backbone(clip_features, variant),
            )
        )
    return specs


def is_done(spec: RetrainSpec) -> bool:
    """Resume probe. Done if (a) listed in _lam0_done.txt, OR (b) the on-disk
    snapshot already shows lam_smooth==0.0 AND a *.pre_lam0.bak exists (fallback
    for a run completed before the log existed)."""
    if DONE_LOG.exists():
        logged = {
            line.strip()
            for line in DONE_LOG.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        if spec.run_name in logged:
            return True
    # Fallback (b): trust the on-disk snapshot + presence of a backup.
    run_dir = RESULTS_DIR / spec.run_name
    try:
        cfg = _load_snapshot_as_config(run_dir / "config_snapshot.json")
        lam = float(cfg.get("train", {}).get("lam_smooth", 1.0))
    except Exception:
        return False
    has_bak = any((run_dir / f"{f}.pre_lam0.bak").exists() for f in BACKUP_FILES)
    return lam == 0.0 and has_bak


def backup_run_dir(run_dir: Path) -> None:
    """Backup-before-overwrite (T-rww-01). Copy each existing artifact to
    ``<name>.pre_lam0.bak`` ONLY if that .bak does not already exist (never
    clobber an existing backup)."""
    for fname in BACKUP_FILES:
        src = run_dir / fname
        bak = run_dir / f"{fname}.pre_lam0.bak"
        if src.exists() and not bak.exists():
            shutil.copy2(src, bak)


def build_lam0_config(spec: RetrainSpec) -> dict:
    """Load the resolved config and apply the lambda=0 + UCF-boundaries edits."""
    cfg = _load_snapshot_as_config(spec.snapshot_path)
    cfg.setdefault("train", {})["lam_smooth"] = 0.0
    if spec.dataset == "ucf":
        cfg.setdefault("paths", {})["snippet_boundaries_dir"] = UCF_BOUNDARIES
    return cfg


def log_error(spec: RetrainSpec, step: str, detail: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ERR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{spec.run_name}\t{step}\t{detail}\n")


def mark_done(spec: RetrainSpec) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(DONE_LOG, "a", encoding="utf-8") as f:
        f.write(spec.run_name + "\n")


def run_one(spec: RetrainSpec) -> str:
    """Train + eval a single run at lambda=0. Returns one of:
    'succeeded' | 'failed'. On any failure logs + returns 'failed' (caller
    continues the batch -- never abort)."""
    import yaml

    run_dir = RESULTS_DIR / spec.run_name
    tmp_path: Optional[str] = None
    try:
        backup_run_dir(run_dir)
        cfg = build_lam0_config(spec)
        fd, tmp_path = tempfile.mkstemp(suffix=".yaml", prefix="lam0_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)

        train_cmd = [
            sys.executable, "src/train.py",
            "--config", tmp_path,
            "--seed", str(spec.seed),
            "--results-dir", "results",
            "--run-name", spec.run_name,
        ]
        r = subprocess.run(train_cmd, cwd=str(PROJECT_ROOT))
        if r.returncode != 0:
            log_error(spec, "train", f"returncode={r.returncode}")
            return "failed"

        eval_cmd = [
            sys.executable, "src/evaluate.py",
            "--run-dir", f"results/{spec.run_name}",
            "--split", "test",
        ]
        r = subprocess.run(eval_cmd, cwd=str(PROJECT_ROOT))
        if r.returncode != 0:
            log_error(spec, "eval", f"returncode={r.returncode}")
            return "failed"

        mark_done(spec)
        return "succeeded"
    except Exception as exc:  # noqa: BLE001 -- robustness: log + continue
        log_error(spec, "exception", repr(exc))
        return "failed"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def print_plan(specs: List[RetrainSpec]) -> None:
    """--dry-run: one line per run, then the count. Imports no torch, writes
    no artifact, trains nothing."""
    print(f"lambda=0 retrain plan: {len(specs)} canonical runs "
          "(i3d RTFM-gate runs excluded). NO training in --dry-run.\n")
    ucf = sum(1 for s in specs if s.dataset == "ucf")
    xd = sum(1 for s in specs if s.dataset == "xd")
    for i, s in enumerate(specs, 1):
        print(
            f"[{i:2d}/{len(specs)}] run={s.run_name:42s} "
            f"config={s.snapshot_path.as_posix()} "
            f"seed={s.seed} variant={s.variant:14s} "
            f"backbone={s.backbone:18s} eval-mode={s.eval_mode}"
        )
    print(f"\nTotal: {len(specs)} runs  ({ucf} ucf_* UCF-full-length, "
          f"{xd} xd_* XD-standard).  i3d RTFM-gate runs excluded.")


def run_batch(specs: List[RetrainSpec]) -> None:
    succeeded = skipped = failed = 0
    failed_names: List[str] = []
    for i, s in enumerate(specs, 1):
        if is_done(s):
            print(f"[skip] {s.run_name} (already lambda=0)")
            skipped += 1
            continue
        print(f"[{i}/{len(specs)}] retraining {s.run_name} "
              f"({s.eval_mode}) ...")
        outcome = run_one(s)
        if outcome == "succeeded":
            succeeded += 1
        else:
            failed += 1
            failed_names.append(s.run_name)
    attempted = succeeded + failed
    print("\n=== lambda=0 retrain summary ===")
    print(f"attempted={attempted}  succeeded={succeeded}  "
          f"skipped={skipped}  failed={failed}")
    if failed_names:
        print("failed runs:")
        for n in failed_names:
            print(f"  - {n}")
        print(f"see {ERR_LOG.as_posix()} for details")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Resumable lambda=0 retrain of all 58 canonical runs."
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Print the plan and exit WITHOUT training (no torch, no artifacts).",
    )
    args = ap.parse_args(argv)

    specs = enumerate_runs()

    if args.dry_run:
        print_plan(specs)
        return 0

    run_batch(specs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
