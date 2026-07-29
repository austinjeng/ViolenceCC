"""One-shot exploratory re-grid: XD-Violence k_topk x lr under the FINAL headline config.

Quick task 260729-5l3. Appendix C's XD sweep found a k_topk=2 / higher-LR ridge, but it
ran under the OLD regime (pre-SO400M features, pre-lam_smooth=0). This re-runs that ridge
-- k in {1,2,3} x lr in {1e-4, 7e-4, 1e-3} x seeds {42,123,2024} = 27 runs -- against the
shipped headline config (configs/gated_fusion_xd_so400m.yaml) to see whether the gain
stacks or was an artifact of the old feature/loss regime.

EXPLORATORY ONLY. Output is a report, not thesis/paper material.

All outputs (per-run dirs, results-index.csv, runner-errors.log) land under
outputs/regrid_so400m_xd/ -- the tracked results/ tree is never written.

Usage:
    python scripts/_tmp_regrid_so400m_xd.py --dry-run
    python scripts/_tmp_regrid_so400m_xd.py --only-first 1
    python scripts/_tmp_regrid_so400m_xd.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make the sibling orchestrator importable regardless of the shell's CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_ablations as RA  # noqa: E402

CONFIG = "configs/gated_fusion_xd_so400m.yaml"
SEEDS = [42, 123, 2024]

# Cell order is load-bearing: earliest sanity signal first. (1e-4, k=3) is the anchor --
# byte-identical hyperparameters to the shipped headline -- then the k=2 ridge, then the
# remainder. Written as an explicit literal because nested loops give the wrong order.
CELLS = [
    (1.0e-4, 3),   # anchor == shipped headline
    (1.0e-4, 2),
    (7.0e-4, 2),
    (1.0e-3, 2),
    (1.0e-4, 1),
    (7.0e-4, 1),
    (1.0e-3, 1),
    (7.0e-4, 3),
    (1.0e-3, 3),
    # Extension (user request): softer selection k in {4..9} at the shipped lr only --
    # the k<=3 grid showed AP rising monotonically toward k=3 at lr 1e-4, so probe the
    # far side of the boundary. k=4 first (most informative cell earliest).
    (1.0e-4, 4),
    (1.0e-4, 5),
    (1.0e-4, 6),
    (1.0e-4, 7),
    (1.0e-4, 8),
    (1.0e-4, 9),
]


def build_specs():
    return [
        RA.RunSpec("xd", "gated_fusion", seed, CONFIG, "so400m",
                   lr_override=lr, k_topk_override=k)
        for lr, k in CELLS
        for seed in SEEDS
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the queue without touching the GPU")
    ap.add_argument("--results-root", default="outputs/regrid_so400m_xd",
                    help="output root (relative paths resolve against the project root)")
    ap.add_argument("--only-first", type=int, default=0,
                    help="run only the first N specs (0 = all); used for the probe run")
    args = ap.parse_args()

    root = Path(args.results_root)
    if not root.is_absolute():
        root = RA.PROJECT_ROOT / root

    specs = build_specs()
    if args.only_first:
        specs = specs[:args.only_first]

    # Call run_queue directly, bypassing run_ablations' argparse/preflight: wandb is
    # already `disabled` in the config, so there is nothing to preflight.
    summary = RA.run_queue(specs, root, root / "runner-errors.log",
                           dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
