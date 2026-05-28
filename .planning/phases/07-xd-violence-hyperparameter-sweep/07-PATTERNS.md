# Phase 7: XD-Violence Hyperparameter Sweep - Pattern Map

**Mapped:** 2026-05-01
**Files analyzed:** 7 (4 modified, 3 new)
**Analogs found:** 7 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/train.py` | controller | request-response | `src/train.py` (self — extend) | exact |
| `scripts/run_ablations.py` | service / orchestrator | batch | `scripts/run_ablations.py` (self — extend) | exact |
| `scripts/rtfm_gap_diagnostic.py` | utility / diagnostic | transform | `src/eval/xd_annotations.py` + `src/eval/snippet_to_frame.py` | role-match |
| `scripts/generate_phase7_charts.py` | utility / visualization | transform | `scripts/generate_phase4_charts.py` | exact |
| `tests/test_train.py` | test | request-response | `tests/test_train.py` (self — extend) | exact |
| `tests/test_run_ablations.py` | test | batch | `tests/test_run_ablations.py` (self — extend) | exact |
| `configs/gated_fusion_xd.yaml` | config | -- | read-only reference, not modified | -- |

## Pattern Assignments

### `src/train.py` (controller, request-response) -- MODIFY

**Analog:** `src/train.py` (self -- lines 33-55)

**Imports pattern** (lines 3-29 -- no new imports needed):
```python
import argparse
import datetime
import sys
from pathlib import Path
```

**CLI arg parsing pattern** (lines 33-45):
```python
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="ViolenceCC training entry point (TRN-06)")
    ap.add_argument("--config", required=True, help="Path to variant YAML config")
    ap.add_argument("--seed", type=int, default=None,
                    help="Override cfg['seed']")
    ap.add_argument("--epochs", type=int, default=None,
                    help="Override cfg['train']['epochs'] (for smoke tests)")
    ap.add_argument("--results-dir", type=str, default=None,
                    help="Override cfg['paths']['results_dir']")
    ap.add_argument("--run-name", type=str, default=None,
                    help="Override the default run_name() value "
                         "(Phase 4 D-30: deterministic dirs for run_ablations.py)")
    return ap.parse_args(argv)
```
Add `--lr` and `--k-topk` following the same `type=<type>, default=None, help=` pattern used by `--seed` and `--epochs`.

**CLI override application pattern** (lines 48-55):
```python
def apply_cli_overrides(cfg: dict, args) -> dict:
    if args.seed is not None:
        cfg["seed"] = args.seed
    if args.epochs is not None:
        cfg["train"]["epochs"] = args.epochs
    if args.results_dir is not None:
        cfg["paths"]["results_dir"] = args.results_dir
    return cfg
```
Add `args.lr` -> `cfg["train"]["lr"]` and `args.k_topk` -> `cfg["train"]["k_topk"]` following the same `if args.X is not None: cfg[...] = args.X` guard pattern.

**Key config consumption point** (lines 127-132 -- train_one_epoch reads k_topk from train_cfg):
```python
        loss = mil_ranking_loss(
            scores, mask, n_normal=n_normal,
            k=int(train_cfg["k_topk"]),
            margin=float(train_cfg["margin"]),
            lam_sparse=float(train_cfg["lam_sparse"]),
            lam_smooth=float(train_cfg["lam_smooth"]),
        )
```
No changes needed here -- overrides are applied to `cfg["train"]` before the training loop starts (line 278: `cfg = apply_cli_overrides(cfg, args)`), so `train_cfg["k_topk"]` and `train_cfg["lr"]` will already carry the overridden values.

---

### `scripts/run_ablations.py` (service/orchestrator, batch) -- MODIFY

**Analog:** `scripts/run_ablations.py` (self -- lines 51-164 for RunSpec + QUEUES, lines 225-246 for run_one)

**Imports pattern** (lines 24-33 -- no new imports needed):
```python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
```

**RunSpec dataclass pattern** (lines 51-81):
```python
@dataclass
class RunSpec:
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
        tags = ["phase4", self.dataset, self.variant, f"s{self.seed}"]
        if self.cache_variant:
            tags.append(self.cache_variant)
        return tags
```
Add `lr_override: float | None = None` and `k_topk_override: int | None = None` as optional fields with defaults. Extend `run_name` property to append `_lr{}_k{}` when overrides are set. Add `_fmt_lr()` helper per RESEARCH.md Pattern 2.

**QUEUES dict pattern** (lines 112-164):
```python
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
    # ... more queues ...
}
```
Add `phase7_sweep` queue with 20 RunSpec entries using list comprehension (per RESEARCH.md Pattern 3). Add `phase7_confirm` as an empty or placeholder queue -- entries populated after sweep analysis (per D-12).

**TTA queue grid comprehension pattern** (lines 173-192 -- closest analog for sweep grid):
```python
_CORRUPTION_TYPES = ["gaussian_noise", "jpeg_compression", "brightness", "motion_blur"]
_SEVERITIES = [1, 2, 3, 4, 5]
_LR_GRID = [1e-4, 5e-4, 1e-3, 5e-3]
_RHO_GRID = [0.001, 0.005, 0.01, 0.05, 0.1]

TTA_QUEUES = {
    "tta_source_only": [
        TTARunSpec(ct, sev, "source_only", 0.0)
        for ct in _CORRUPTION_TYPES for sev in _SEVERITIES
    ],  # 20 runs
}
```
Use same grid-constant + list-comprehension pattern for phase7_sweep:
```python
_LR_SWEEP = [5e-5, 1e-4, 2e-4, 3e-4, 5e-4]
_K_SWEEP = [1, 3, 5, 7]

QUEUES["phase7_sweep"] = [
    RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd.yaml",
            lr_override=lr, k_topk_override=k)
    for lr in _LR_SWEEP for k in _K_SWEEP
]  # 20 runs
```

**run_one() subprocess cmd construction pattern** (lines 240-246):
```python
    train_cmd = [
        sys.executable, "src/train.py",
        "--config", spec.config,
        "--seed", str(spec.seed),
        "--results-dir", str(results_root),
        "--run-name", spec.run_name,
    ]
```
Append override flags after the base cmd list when non-None:
```python
    if spec.lr_override is not None:
        train_cmd.extend(["--lr", str(spec.lr_override)])
    if spec.k_topk_override is not None:
        train_cmd.extend(["--k-topk", str(spec.k_topk_override)])
```

**main() queue dispatch pattern** (lines 455-508):
```python
def main() -> int:
    all_queue_names = sorted(set(list(QUEUES) + list(TTA_QUEUES)))
    ap = argparse.ArgumentParser(...)
    ap.add_argument("--queue", required=True, choices=all_queue_names, ...)
    # ...
    is_tta = args.queue in TTA_QUEUES
    if is_tta:
        specs = TTA_QUEUES[args.queue]
        summary = run_queue_tta(specs, ...)
    else:
        specs = QUEUES[args.queue]
        summary = run_queue(specs, ...)
```
The new `phase7_sweep` and `phase7_confirm` queues are added to the `QUEUES` dict (not `TTA_QUEUES`), so the existing dispatch at line 503 (`specs = QUEUES[args.queue]`) handles them with no changes to `main()`. The `--queue` choices are computed dynamically from `QUEUES.keys()` at line 456.

---

### `scripts/generate_phase7_charts.py` (utility, transform) -- NEW

**Analog:** `scripts/generate_phase4_charts.py`

**Imports pattern** (lines 1-33):
```python
#!/usr/bin/env python
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
```

**Project setup pattern** (lines 36-43):
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "results"
OUT_DIR = RESULTS_DIR / "phase7_charts"
```

**Style constants pattern** (lines 46-64):
```python
DPI = 150
FIG_STD = (12, 7)
FIG_WIDE = (16, 9)
FIG_SMALL = (9, 6)
TITLE_SZ = 18
LABEL_SZ = 14
TICK_SZ = 12
VAL_SZ = 11

sns.set_theme(
    style="whitegrid",
    font_scale=1.1,
    rc={
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "grid.alpha": 0.3,
        "font.family": "sans-serif",
    },
)
```

**Save helper pattern** (lines 202-207):
```python
def _save(fig, subdir, name):
    p = OUT_DIR / subdir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"    -> {p.relative_to(RESULTS_DIR)}")
```

**Heatmap pattern** (lines 361-376 chart_B06 -- closest analog for sweep heatmap):
```python
def chart_B06(data):
    cats = _ucf_cat_order()
    matrix = []
    for v in UCF_MAIN:
        run = UCF_RUNS[v]
        pc = data["metrics"][run]["per_category"]
        matrix.append([pc[c]["auc"] for c in cats])

    df = pd.DataFrame(matrix, index=[VLABELS[v] for v in UCF_MAIN], columns=cats)
    fig, ax = plt.subplots(figsize=FIG_WIDE)
    sns.heatmap(df, annot=True, fmt=".3f", cmap="RdYlGn", vmin=0.75, vmax=1.0,
                ax=ax, linewidths=0.5, cbar_kws={"label": "AUC"})
    ax.set_title("UCF-Crime: Per-Category AUC Heatmap", fontsize=TITLE_SZ, fontweight="bold")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=TICK_SZ - 1)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=TICK_SZ)
    _save(fig, "B_per_category", "B06_heatmap_auc.png")
```
Adapt: build a `pd.DataFrame` with lr rows x k_topk columns, populated from results-index.csv, then call `sns.heatmap()` with `annot=True, fmt=".4f", cmap="RdYlGn"`.

**Summary table pattern** (lines 948-981 chart_J26):
```python
def chart_J26(data):
    rows = []
    for run in ALL_RUNS:
        m = data["metrics"][run]
        rows.append([
            RUN_DISPLAY[run],
            f'{m["auc"]:.4f}',
            f'{m["ap"]:.4f}',
            # ...
        ])
    fig, ax = plt.subplots(figsize=(18, 6))
    ax.axis("off")
    cols = ["Run", "AUC", "AP", ...]
    table = ax.table(cellText=rows, colLabels=cols, loc="center",
                     cellLoc="center", colWidths=[...])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.6)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#3B82F6")
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#F1F5F9")
        cell.set_edgecolor("#CBD5E1")
    _save(fig, "J_summary", "J26_summary_table.png")
```

**main() orchestration pattern** (lines 1077-1148):
```python
def main():
    print("Phase 4 Results Visualization")
    print("=" * 50)
    print(f"Output: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Loading results data...")
    data = load_all_data()
    # ... sequential chart generation ...
    print(f"\nDone! Generated {len(pngs)} PNG files in {OUT_DIR}")

if __name__ == "__main__":
    main()
```

---

### `scripts/rtfm_gap_diagnostic.py` (utility, transform) -- NEW

**Analog:** `src/eval/xd_annotations.py` (for annotation parsing patterns) + `src/eval/snippet_to_frame.py` (for interpolation logic)

**Imports pattern** -- combine from both analogs:

From `src/eval/xd_annotations.py` (lines 11-17):
```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
```

From `scripts/generate_phase4_charts.py` (lines 36-37 -- project root setup):
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

**Annotation parsing pattern** from `src/eval/xd_annotations.py` (lines 60-99):
```python
def parse_xd_annotations(path: Path) -> Dict[str, VideoAnnotation]:
    annos: Dict[str, VideoAnnotation] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # ...
```
Use same file-parsing conventions (enumerate with line_no, strip, split) when comparing annotation formats.

**Category parsing pattern** from `src/eval/xd_annotations.py` (lines 38-57):
```python
def _parse_category(video_id: str) -> str:
    if "_label_" not in video_id:
        return "Unknown"
    suffix = video_id.split("_label_", 1)[1]
    if suffix == "A":
        return "Normal"
    first = suffix.split("-", 1)[0]
    return first
```

**Snippet-to-frame pattern** from `src/eval/snippet_to_frame.py` (lines 20-62):
```python
def snippet_to_frame(
    scores: np.ndarray,
    n_frames: int,
    snippet_window: int,
    *,
    upsample_factor: int = 1,
) -> np.ndarray:
    expanded = np.repeat(scores, snippet_window)
    if upsample_factor > 1:
        expanded = np.repeat(expanded, upsample_factor)
    # ...
```
The RTFM diagnostic should compare this against RTFM's `np.repeat(pred, 16)` pattern.

**Script entry point pattern** -- follow `generate_phase4_charts.py` `main()` style:
```python
def main():
    print("RTFM Gap Diagnostic")
    print("=" * 50)
    # Run 4 diagnostics sequentially
    # Print findings to stdout as structured text
    # Optionally write summary to a file

if __name__ == "__main__":
    main()
```

---

### `tests/test_train.py` (test, request-response) -- MODIFY

**Analog:** `tests/test_train.py` (self -- lines 1-49)

**Imports pattern** (lines 1-8):
```python
"""TRN-01 / TRN-03 src/train.py unit tests."""
import pathlib
import subprocess

import pytest
import torch

from src.utils.scheduler import build_optimizer
```
Add `from src.train import parse_args, apply_cli_overrides` for the new tests.

**CLI test pattern** (lines 43-49):
```python
def test_cli_help():
    """Entry point is invokable as a module."""
    r = subprocess.run(
        ["python", "-c", "from src.train import parse_args; parse_args(['--config', 'x'])"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
```
New tests should follow the same pattern: call `parse_args()` with specific argv and verify the result, then call `apply_cli_overrides()` with a mock cfg dict and verify the overridden values.

**Config override test pattern** (lines 11-17 -- analogous structure):
```python
def test_optimizer_config():
    """TRN-01 (VALIDATION.md): AdamW lr=1e-4, weight_decay=1e-2."""
    model = torch.nn.Linear(4, 2)
    cfg = {"lr": 1e-4, "weight_decay": 1e-2}
    opt = build_optimizer(model.parameters(), cfg)
    assert opt.param_groups[0]["lr"] == 1e-4
    assert opt.param_groups[0]["weight_decay"] == 1e-2
```
New tests should construct a minimal cfg dict, create args with override values, call `apply_cli_overrides()`, and assert the cfg is updated.

---

### `tests/test_run_ablations.py` (test, batch) -- MODIFY

**Analog:** `tests/test_run_ablations.py` (self -- lines 0-66)

**Imports pattern** (lines 12-28):
```python
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_ablations import (
    QUEUES,
    RunSpec,
    is_done,
    run_queue,
)
```

**Queue length assertion pattern** (lines 42-65):
```python
def test_queue_definitions():
    assert len(QUEUES["rtfm_gate"]) == 1
    assert QUEUES["rtfm_gate"][0].run_name == "xd_i3d_rtfm_i3d_s42"
    assert len(QUEUES["phase4_main"]) == 4
    # ...
    all_run_names = {
        s.run_name for q in QUEUES.values() for s in q
    }
    assert len(all_run_names) == 18, f"expected 18 unique run_names, got {sorted(all_run_names)}"
```
Add assertions for `len(QUEUES["phase7_sweep"]) == 20` and spot-check specific run_names. Update the total unique run_names count from 18 to 38 (18 existing + 20 sweep).

**RunSpec.run_name test pattern** (lines 68-77):
```python
def test_run_name_deterministic():
    s = RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion.yaml")
    assert s.run_name == "ucf_gated_fusion_s42"
    s2 = RunSpec("ucf", "gated_fusion", 42,
                 "configs/gated_fusion_2person.yaml", "2person")
    assert s2.run_name == "ucf_gated_fusion_2person_s42"
```
Add tests for RunSpec with `lr_override` and `k_topk_override` set, verifying D-11 naming: `xd_gated_fusion_lr5e5_k1_s42`, `xd_gated_fusion_lr1e4_k3_s42`, etc.

**Monkeypatch subprocess pattern** (lines 127-159):
```python
def test_run_one_success_appends_index(tmp_path, monkeypatch):
    from scripts import run_ablations

    def fake_run(cmd, **kwargs):
        if any("evaluate.py" in str(c) for c in cmd):
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "eval_metrics.json").write_text(
                json.dumps({...}), encoding="utf-8")
        class _R:
            returncode = 0
        return _R()

    monkeypatch.setattr(run_ablations.subprocess, "run", fake_run)
    spec = QUEUES["rtfm_gate"][0]
    status = run_ablations.run_one(spec, tmp_path, err_log)
    assert status["phase"] == "done"
```
Add a test that creates a RunSpec with `lr_override`/`k_topk_override`, monkeypatches subprocess, and asserts the train_cmd includes `--lr` and `--k-topk` flags.

---

## Shared Patterns

### Project Root Bootstrap
**Source:** `src/train.py` lines 12-17, `scripts/generate_phase4_charts.py` lines 36-37
**Apply to:** `scripts/rtfm_gap_diagnostic.py`, `scripts/generate_phase7_charts.py`
```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

### CLI Override Guard
**Source:** `src/train.py` lines 48-55
**Apply to:** `src/train.py` (extend with lr + k_topk)
```python
if args.lr is not None:
    cfg["train"]["lr"] = args.lr
if args.k_topk is not None:
    cfg["train"]["k_topk"] = args.k_topk
```
This `if X is not None` guard is used for every CLI override in the codebase. Never set a default that collides with a valid config value.

### Results Index Append
**Source:** `src/utils/csv_logger.py` lines 54-73 (schema), lines 76+ (append function)
**Apply to:** `scripts/run_ablations.py` run_one() -- no changes needed; existing row dict at lines 302-316 already captures `auc`, `ap`, `seed`, `variant`, `dataset`. Sweep rows log naturally with the same schema.
```python
RESULTS_INDEX_COLUMNS = [
    "run_name", "variant", "dataset", "seed", "cache_variant",
    "auc", "ap", "n_videos", "n_frames",
    "start_time", "end_time", "config_hash",
    "method", "corruption_type", "severity", "lr", "rho",
]
```
No schema extension needed -- the existing `lr` and `rho` columns (added in Phase 5 for TTA) are available but will be empty for Phase 7 sweep rows. The sweep lr/k values are encoded in `run_name` (D-11 naming) and recoverable via parsing.

### Matplotlib Agg Backend + Save
**Source:** `scripts/generate_phase4_charts.py` lines 23-24, lines 202-207
**Apply to:** `scripts/generate_phase7_charts.py`
```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _save(fig, subdir, name):
    p = OUT_DIR / subdir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
```

### Test Fixtures
**Source:** `tests/test_run_ablations.py` lines 92-99 (tmp_path + capsys), lines 127-159 (tmp_path + monkeypatch)
**Apply to:** New tests in `tests/test_run_ablations.py` and `tests/test_train.py`
```python
def test_phase7_cli_overrides(tmp_path, monkeypatch):
    from scripts import run_ablations
    # monkeypatch subprocess.run to capture train_cmd
    # assert "--lr" and "--k-topk" appear in cmd
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| -- | -- | -- | All files have close analogs in the existing codebase |

Every Phase 7 file is either a direct extension of an existing file (train.py, run_ablations.py, both test files) or a new script with an exact-match template (generate_phase7_charts.py from generate_phase4_charts.py). The RTFM diagnostic script combines patterns from two existing eval modules (xd_annotations.py, snippet_to_frame.py) plus the script entry-point pattern from generate_phase4_charts.py.

## Metadata

**Analog search scope:** `src/`, `scripts/`, `tests/`, `configs/`
**Files scanned:** 12 (train.py, run_ablations.py, generate_phase4_charts.py, evaluate.py, xd_annotations.py, snippet_to_frame.py, csv_logger.py, gated_fusion_xd.yaml, test_train.py, test_run_ablations.py, conftest.py, CLAUDE.md)
**Pattern extraction date:** 2026-05-01
