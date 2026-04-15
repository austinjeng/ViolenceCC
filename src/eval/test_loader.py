"""Test-set loader with C3 import-boundary + sys.argv guard (D-07, D-08).

RESTRICTED MODULE: this file must only be imported by
  - src/evaluate.py
  - pytest test runners (under tests/)
Any other caller raises RuntimeError at module import time.

Design intent: belt-and-suspenders C3 defense. The directory layout
already isolates test loading from training (src.data.dataset does not
import from src.eval.*) — this runtime guard catches accidental imports
(e.g., from a notebook, a REPL, or a future training script that reaches
into src/eval/).

The guard is a tripwire, not a security primitive: a process with write
access to sys.argv already has access to the feature directories. The
value is accidental-import prevention — see PITFALLS.md C3 and
04-CONTEXT.md D-07/D-08.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from torch.utils.data import Dataset


_ALLOWED_SENTINELS = ("evaluate.py",)
_PYTEST_SENTINELS = ("pytest", "py.test")


def _assert_called_from_evaluate_or_pytest() -> None:
    """Raise RuntimeError unless the caller is evaluate.py or pytest.

    Detection, in order:
      1. sys.argv[0] basename == "evaluate.py"        (python src/evaluate.py ...)
      2. sys.argv[0] basename contains "pytest"/"py.test"
         (pytest invoked via installed entry-point script, e.g. pytest.exe)
      3. "pytest" module is already imported in sys.modules
         (python -m pytest; sys.argv[0] becomes __main__.py, but the pytest
          package is always loaded before any test module imports run).

    Anything else (e.g. `python -c "..."`, Jupyter kernels where argv[0] ends
    with ipykernel_launcher.py, bare `python` REPL where argv[0] is "") is
    rejected with a pointer at the legitimate entry point.

    Rule 1 auto-fix note: the original guard only checked sys.argv[0] which
    misses `python -m pytest` (argv[0] == "__main__.py"). Adding the
    sys.modules check catches it without weakening the -c rejection path.
    """
    argv0 = Path(sys.argv[0]).name if sys.argv else ""
    if argv0 in _ALLOWED_SENTINELS:
        return
    if any(s in argv0 for s in _PYTEST_SENTINELS):
        return
    # python -m pytest: argv[0] is __main__.py but the pytest package is loaded.
    if "pytest" in sys.modules:
        return
    raise RuntimeError(
        f"src/eval/test_loader.py was imported by sys.argv[0]={argv0!r}. "
        "This module is restricted to src/evaluate.py and pytest test runners "
        "to prevent test-set leakage (C3). If you are running a legitimate "
        "evaluation, invoke `python src/evaluate.py --run-dir <path>` instead."
    )


_assert_called_from_evaluate_or_pytest()  # fires at module import


# ---- Public surface ----


def build_test_dataset(cfg: Dict[str, Any]) -> Dataset:
    """Dispatch on cfg['dataset'] to the matching test dataset class (D-07).

    Reuses MILFeatureDataset(mode="test") for the UCF + XD-Violence paths;
    defers to src.data.i3d_dataset.I3DFeatureDataset (Plan 04-03) for xd_i3d.

    Only passes keyword arguments accepted by the current MILFeatureDataset
    signature — Plan 04-04's skel_agg extension will thread through `data.skel_agg`
    when the Dataset accepts it. For now we read it from cfg but only forward
    if the Dataset's __init__ actually takes it, keeping Plan 04-02 compatible
    with both the pre- and post-Plan-04-04 Dataset signature.
    """
    ds = cfg.get("dataset", "ucf")
    paths = cfg["paths"]
    data = cfg.get("data", {})

    if ds == "ucf":
        from src.data.dataset import MILFeatureDataset
        return _construct_mil_dataset(
            MILFeatureDataset,
            split_file=str(Path(paths["splits_dir"]) / "ucf_test.txt"),
            skel_dir=paths["skeleton_features"],
            clip_dir=paths["clip_features"],
            T=data.get("T", 32),
            mode="test",
            seed=int(cfg.get("seed", 42)),
            dataset="ucf",
            skel_agg=data.get("skel_agg", "none"),
        )

    if ds == "xd_i3d":
        # Stub: I3DFeatureDataset lands in Plan 04-03.
        try:
            from src.data.i3d_dataset import I3DFeatureDataset
        except ImportError as e:
            raise RuntimeError(
                "xd_i3d dataset requires src.data.i3d_dataset (Plan 04-03). "
                f"Import failed: {e}"
            )
        return I3DFeatureDataset(
            split_file=str(Path(paths["splits_dir"]) / "xd_test.txt"),
            feature_dir=str(Path(paths["i3d_features"]) / "RGBTest"),
            mode="test",
            T=data.get("T", 32),
        )

    if ds == "xd":
        # Phase 4b scope; keeps signature parallel to ucf.
        from src.data.dataset import MILFeatureDataset
        return _construct_mil_dataset(
            MILFeatureDataset,
            split_file=str(Path(paths["splits_dir"]) / "xd_test.txt"),
            skel_dir=paths["skeleton_features"],
            clip_dir=paths["clip_features"],
            T=data.get("T", 32),
            mode="test",
            seed=int(cfg.get("seed", 42)),
            dataset="xd",
            skel_agg=data.get("skel_agg", "none"),
        )

    raise ValueError(f"Unknown dataset key: {ds!r}")


def _construct_mil_dataset(cls, **kwargs):
    """Forward-compat bridge to MILFeatureDataset.

    Plan 04-04 will extend __init__ with a `skel_agg` param; until that lands,
    drop unknown kwargs and fall back to the current signature. This keeps
    Plan 04-02 tests green on the pre-04-04 Dataset while letting 04-04 plumb
    skel_agg through without a second test_loader edit.
    """
    import inspect
    try:
        sig = inspect.signature(cls.__init__)
        valid = set(sig.parameters.keys())
    except (TypeError, ValueError):
        valid = None
    if valid is not None:
        kwargs = {k: v for k, v in kwargs.items() if k in valid}
    return cls(**kwargs)
