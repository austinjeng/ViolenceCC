"""run_ucf_consistency_rerun.py -- Job C: version-locked rerun of legacy-trained UCF cells.

Quick 260717-77p Task 3(C) (Codex round-2 addendum): all seed-42 UCF runs and
the Gated Fusion s123/s2024 runs were trained BEFORE smoothness-axis fix
f89910b, and their config snapshots record dirty worktrees -- so the exact
training code is not provable from the snapshot SHA alone. This job retrains
every legacy-trained UCF cell with CURRENT HEAD code and the SAME config/seed
into results/_consistency_rerun/ as a VERIFICATION artifact (per-cell deltas
for the ch04 footnote), NOT a number replacement.

RUN IN A VISIBLE TERMINAL (user preference -- no headless background jobs):
    conda activate vcc-main
    python scripts/run_ucf_consistency_rerun.py            # full rerun
    python scripts/run_ucf_consistency_rerun.py --list-only  # enumerate only (no GPU)

Expected runtime: ~29 runs x <5 min/run (head-only training on cached
features, ch04 Sec. "efficiency": "training completes in under 5 minutes per
configuration") ~= 2.5 GPU-h. (The 2026-07-17 addendum's 5-6 h estimate was
conservative.) RESUMABLE: runs whose
results/_consistency_rerun/<runname>/eval_metrics.json exists are skipped.

After completion, compare with:
    python scripts/compare_consistency_rerun.py
DECISION GATE (from the addendum): if every |rerun - canonical| <= that
row's 3-seed std, publish the deltas in the ch04 footnote and keep numbers
as run; if any cell exceeds its row seed-std, escalate to adopting the rerun
numbers (full propagation pass).

ENUMERATION RULE: a UCF run dir results/ucf_*/ is LEGACY iff the git sha
recorded in its config_snapshot.json does NOT have fix f89910b as an
ancestor (`git merge-base --is-ancestor f89910b <sha>` exits nonzero).
Expected ~29 cells: all 21 UCF *_s42 runs + gated-fusion (default + giant
variants trained pre-fix) s123/s2024.

SAFETY:
  * NEVER writes into canonical results/<runname>/ -- every output path is
    asserted to live under results/_consistency_rerun/ before any write.
  * Clean-worktree guard: aborts unless `git status --porcelain` is clean
    for paths under src/ scripts/ configs/ (untracked .planning/ and
    results/ noise is allowed); records {sha, scoped_dirty: false} into each
    rerun's config snapshot so THIS provenance is provable, unlike the
    original runs'.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Module-level defaults; --results-root overrides both (mirrors
# run_ablations.py --results-root).
RESULTS_ROOT = PROJECT_ROOT / "results"
RERUN_ROOT = RESULTS_ROOT / "_consistency_rerun"
FIX_COMMIT = "f89910b"  # smoothness-axis fix (2026-06-01)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )


def _assert_rerun_path(p: Path) -> None:
    """T-77p-01 mitigation: refuse to write anywhere but _consistency_rerun/."""
    rp = p.resolve()
    root = RERUN_ROOT.resolve()
    assert rp == root or root in rp.parents, (
        f"REFUSING write outside results/_consistency_rerun/: {p}"
    )


def enumerate_legacy_runs() -> list:
    """[(run_name, sha, seed, config_dict)] for every legacy-trained UCF cell."""
    legacy = []
    for snap_path in sorted(RESULTS_ROOT.glob("ucf_*/config_snapshot.json")):
        run_name = snap_path.parent.name
        try:
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[warn] {run_name}: unreadable config_snapshot.json ({exc}); "
                  f"treating as LEGACY (conservative)")
            legacy.append((run_name, "<unreadable>", None, None))
            continue
        sha = (snap.get("git") or {}).get("sha")
        cfg = snap.get("config", snap)
        seed = cfg.get("seed")
        if not sha:
            print(f"[warn] {run_name}: no recorded git sha; treating as LEGACY")
            legacy.append((run_name, "<missing>", seed, cfg))
            continue
        res = _git("merge-base", "--is-ancestor", FIX_COMMIT, sha)
        if res.returncode != 0:
            # fix NOT an ancestor of the training commit -> legacy objective
            legacy.append((run_name, sha, seed, cfg))
    return legacy


def scoped_worktree_clean() -> bool:
    """True iff src/ scripts/ configs/ have no modifications (untracked
    .planning/ and results/ noise elsewhere is allowed)."""
    res = _git("status", "--porcelain", "--", "src", "scripts", "configs")
    return res.stdout.strip() == ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--list-only", action="store_true",
        help="Print the legacy-cell enumeration and exit (reads snapshots + git only; zero GPU).",
    )
    parser.add_argument(
        "--results-root", default=None,
        help="Override the canonical results root (default: <repo>/results).",
    )
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()

    global RESULTS_ROOT, RERUN_ROOT
    if args.results_root:
        RESULTS_ROOT = Path(args.results_root)
        RERUN_ROOT = RESULTS_ROOT / "_consistency_rerun"

    legacy = enumerate_legacy_runs()
    print(f"Legacy-trained UCF cells (fix {FIX_COMMIT} NOT an ancestor): {len(legacy)}")
    for run_name, sha, seed, _ in legacy:
        print(f"  {run_name:45s} seed={seed} trained_at={str(sha)[:10]}")

    if args.list_only:
        print(f"[list-only] {len(legacy)} cells enumerated; exiting without training.")
        return 0

    # ---- Clean-worktree guard (scoped) ----
    if not scoped_worktree_clean():
        print("ABORT: src/ scripts/ or configs/ have uncommitted changes. "
              "Commit or revert them first -- the whole point of this job is "
              "version-locked provenance.", file=sys.stderr)
        return 1
    head_sha = _git("rev-parse", "HEAD").stdout.strip()
    print(f"Worktree clean for src/scripts/configs at HEAD {head_sha[:10]}")

    _assert_rerun_path(RERUN_ROOT)
    RERUN_ROOT.mkdir(parents=True, exist_ok=True)

    failed = []
    for run_name, sha, seed, cfg in legacy:
        run_dir = RERUN_ROOT / run_name
        _assert_rerun_path(run_dir)
        metrics_path = run_dir / "eval_metrics.json"
        if metrics_path.exists():
            print(f"[skip] {run_name} (eval_metrics.json present)")
            continue
        if cfg is None or seed is None:
            print(f"[fail] {run_name}: snapshot unusable; rerun manually")
            failed.append(run_name)
            continue

        # SAME config as the canonical run: rerun from the snapshot's config
        # dict (not the possibly-drifted configs/*.yaml).
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg_path = run_dir / "config_rerun.yaml"
        _assert_rerun_path(cfg_path)
        import yaml  # vcc-main dependency
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False)

        print(f"[train] {run_name} (seed {seed})")
        train_cmd = [
            sys.executable, "src/train.py",
            "--config", str(cfg_path),
            "--seed", str(seed),
            "--results-dir", str(RERUN_ROOT),
            "--run-name", run_name,
        ]
        try:
            subprocess.run(train_cmd, check=True, timeout=args.timeout,
                           cwd=str(PROJECT_ROOT))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f"[fail] {run_name}: train {type(exc).__name__}")
            failed.append(run_name)
            continue

        print(f"[eval ] {run_name}")
        eval_cmd = [
            sys.executable, "src/evaluate.py",
            "--run-dir", str(run_dir),
            "--split", "test",
        ]
        try:
            subprocess.run(eval_cmd, check=True, timeout=max(args.timeout // 4, 600),
                           cwd=str(PROJECT_ROOT))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f"[fail] {run_name}: eval {type(exc).__name__}")
            failed.append(run_name)
            continue

        # Record provable provenance into the rerun's own snapshot.
        snap_path = run_dir / "config_snapshot.json"
        _assert_rerun_path(snap_path)
        if snap_path.exists():
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
            snap["consistency_rerun"] = {
                "sha": head_sha,
                "scoped_dirty": False,
                "canonical_run": run_name,
                "canonical_trained_at": sha,
                "fix_commit": FIX_COMMIT,
            }
            snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")

    done = sum(1 for r, *_ in legacy if (RERUN_ROOT / r / "eval_metrics.json").exists())
    print(f"\nComplete: {done}/{len(legacy)} cells have rerun metrics; "
          f"{len(failed)} failed: {failed or '-'}")
    print("Next: python scripts/compare_consistency_rerun.py")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
