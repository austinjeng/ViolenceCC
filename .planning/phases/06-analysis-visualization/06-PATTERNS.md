# Phase 6: Analysis & Visualization - Pattern Map

**Mapped:** 2026-05-02
**Files analyzed:** 1 new script + supporting infrastructure reads
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/generate_phase6_charts.py` | script (visualization) | file-I/O + batch transform | `scripts/generate_phase4_charts.py` | exact |
| Output: `results/phase6_charts/A_temporal/*.png` | output | -- | `results/phase4_charts/G_curves/*.png` | exact |
| Output: `results/phase6_charts/B_skeleton/*.png` | output | -- | (no analog — new figure type) | none |
| Output: `results/phase6_charts/C_corruption/*.png` | output | -- | `results/phase7_charts/S01_*.png` | exact |
| Output: `results/phase6_charts/D_gating/*.png` | output | -- | (no analog — new figure type) | none |
| Output: `results/phase6_charts/E_projection/*.png` | output | -- | (no analog — new figure type) | none |
| Output: `results/phase6_charts/F_additional/*.png` | output | -- | `results/phase4_charts/A_comparison/*.png` | role-match |

## Pattern Assignments

### `scripts/generate_phase6_charts.py` (script, file-I/O + batch transform)

**Primary Analog:** `scripts/generate_phase4_charts.py` (1149 lines, ~80 PNG outputs)
**Secondary Analog:** `scripts/generate_phase7_charts.py` (396 lines, heatmap + table pattern)

---

#### Pattern 1: Script Skeleton and Imports (Phase 4, lines 1-44)

Copy verbatim for boilerplate structure: shebang, docstring, Agg backend, project root setup, annotation parser imports.

```python
#!/usr/bin/env python
"""
Phase 6 Analysis & Visualization — Thesis-Quality Figures
=========================================================
Generates thesis-ready PNG figures: temporal curves, skeleton overlays,
corruption heatmaps, gate distributions, t-SNE projections, and more.

Usage:
    conda activate vcc-main
    python scripts/generate_phase6_charts.py

Output: results/phase6_charts/
"""
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

# ─── Project Setup ───────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eval.ucf_annotations import parse_annotations, frame_labels
from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels
```

**Additional imports** needed beyond Phase 4 (for skeleton overlay, model loading, t-SNE):

```python
import pickle
import cv2
import torch
from torch.utils.data import DataLoader
from sklearn.manifold import TSNE

from src.models.registry import build_model
from src.utils.checkpoint import load_checkpoint
from src.utils.config import load_snapshot_as_config
```

---

#### Pattern 2: Style Constants (Phase 4, lines 45-64)

Copy exactly — ensures visual consistency across all thesis figures.

```python
# ─── Style ───────────────────────────────────────────────────────────────────
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

---

#### Pattern 3: Variant Color/Label Dicts (Phase 4, lines 67-78)

Copy exactly — D-04 mandates these colors for 4-variant overlays.

```python
VCOLORS = {
    "skeleton_only": "#64748B",
    "clip_only": "#3B82F6",
    "late_fusion": "#F59E0B",
    "gated_fusion": "#EF4444",
}
VLABELS = {
    "skeleton_only": "Skeleton Only",
    "clip_only": "CLIP Only",
    "late_fusion": "Late Fusion",
    "gated_fusion": "Gated Fusion",
}
```

---

#### Pattern 4: Run Directory Mapping (Phase 4, lines 79-91)

Extend for XD fusion variants (Phase 4 only had XD I3D runs; Phase 6 needs all 8).

```python
UCF_RUNS = {
    "skeleton_only": "ucf_skeleton_only_s42",
    "clip_only": "ucf_clip_only_s42",
    "late_fusion": "ucf_late_fusion_s42",
    "gated_fusion": "ucf_gated_fusion_s42",
}
XD_RUNS = {
    "skeleton_only": "xd_skeleton_only_s42",
    "clip_only": "xd_clip_only_s42",
    "late_fusion": "xd_late_fusion_s42",
    "gated_fusion": "xd_gated_fusion_s42",
}
```

---

#### Pattern 5: Output Directory Setup (Phase 4, lines 42-43)

```python
RESULTS_DIR = PROJECT_ROOT / "results"
OUT_DIR = RESULTS_DIR / "phase6_charts"
```

---

#### Pattern 6: `_save()` Helper (Phase 4, lines 202-207)

Copy exactly — handles mkdir, DPI, tight layout, and console logging.

```python
def _save(fig, subdir, name):
    p = OUT_DIR / subdir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"    -> {p.relative_to(RESULTS_DIR)}")
```

---

#### Pattern 7: eval_scores.npz Loading (Phase 4, lines 151-196)

Load per-video frame-level scores from npz. Scores are ALREADY frame-level (post snippet_to_frame expansion). Do NOT re-expand.

```python
def load_curves() -> dict:
    ucf_ann = PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    xd_ann = PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"
    ucf_annos = parse_annotations(ucf_ann)
    xd_annos = parse_xd_annotations(xd_ann)

    curves: dict = {}
    for run in ALL_RUNS:
        sp = RESULTS_DIR / run / "eval_scores.npz"
        if not sp.exists():
            print(f"  SKIP {run}: no eval_scores.npz")
            continue

        npz = np.load(sp)
        is_xd = run.startswith("xd_")
        annos = xd_annos if is_xd else ucf_annos
        label_fn = xd_frame_labels if is_xd else frame_labels

        all_s, all_l = [], []
        for vid in npz.files:
            s = npz[vid]
            nf = len(s)
            lbl = label_fn(annos[vid], nf) if vid in annos else np.zeros(nf, dtype=np.int64)
            all_s.append(s)
            all_l.append(lbl)
        # ... per-video scores ready for temporal curve extraction
```

**Critical pitfall (from RESEARCH.md Pitfall 1-2):** Scores in eval_scores.npz are already frame-level. Do NOT call `snippet_to_frame()` on them. Only need GT label vectors at matching length.

---

#### Pattern 8: Seaborn Heatmap (Phase 7, lines 126-187)

Copy the `generate_sweep_heatmap()` pattern for the corruption severity heatmap. Adapt the pivot axes from (lr x k_topk) to (corruption_type x severity).

```python
def generate_sweep_heatmap(
    df: pd.DataFrame, output_dir: Path, *,
    metric: str = "ap",
    baseline: float = 0.7192,
    title: str = "...",
    filename: str = "S01_sweep_heatmap_ap.png",
) -> None:
    pivot = df.pivot_table(values=metric, index="lr_val", columns="k_val")
    pivot = pivot.sort_index(ascending=True)

    y_labels = [f"{lr:.1e}" for lr in pivot.index]
    n_rows, n_cols = pivot.shape
    fig_w = max(10, n_cols * 1.8 + 2)
    fig_h = max(7, n_rows * 0.55 + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    annot_sz = max(7, min(11, 200 // max(n_rows, n_cols)))

    sns.heatmap(
        pivot, annot=True, fmt=".4f", cmap="RdYlGn",
        ax=ax, linewidths=0.5,
        annot_kws={"size": annot_sz},
        cbar_kws={"label": metric.upper()},
        xticklabels=[str(int(k)) for k in pivot.columns],
        yticklabels=y_labels,
    )
    ax.set_title(title, fontsize=TITLE_SZ, fontweight="bold")
    # ... save
```

**Adaptation for corruption heatmap (D-11):** Pivot on `(corruption_type, severity)` instead of `(lr, k_topk)`. The TTA eval_metrics.json contains fields: `method`, `corruption_type`, `severity`, `lr`, `rho`, `auc`, `ap`. For each (method, corruption, severity), select the best-AUC configuration before pivoting.

---

#### Pattern 9: TTA eval_metrics.json Loading

From the verified TTA directory structure at `results/tta/`. 500 directories with naming:
- `source_only_{corruption}_{severity}_lr0.0`
- `tent_{corruption}_{severity}_lr{lr}`
- `sar_{corruption}_{severity}_lr{lr}_rho{rho}`

Each contains `eval_metrics.json` with structure:
```json
{
  "method": "sar",
  "corruption_type": "brightness",
  "severity": 1,
  "lr": 0.0001,
  "rho": 0.001,
  "auc": 0.7727,
  "ap": 0.1936,
  "n_frames": 1010560,
  "n_videos": 254,
  "per_category": { ... }
}
```

---

#### Pattern 10: Annotation Parsing for GT Shading

**UCF annotations** (`src/eval/ucf_annotations.py`, lines 44-74, 77-93):

```python
# Parse annotations
ucf_annos = parse_annotations(PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt")
# Returns {video_id: VideoAnnotation} with .category, .intervals, .is_normal

# Build frame labels
labels = frame_labels(anno, n_frames)
# Returns np.ndarray[n_frames] binary (0/1), union of both intervals, clamped to [0, n_frames]
```

**XD annotations** (`src/eval/xd_annotations.py`, lines 61-107, 110-120):

```python
xd_annos = parse_xd_annotations(PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt")
# Returns {video_id: VideoAnnotation} — only 500 abnormal test videos
# Normal test videos are OMITTED; guard with `if vid in annos`

labels = xd_frame_labels(anno, n_frames)
# Returns np.ndarray[n_frames] binary, union of variable-length intervals, clamped
```

**GT interval extraction for axvspan shading (D-05):**
```python
# From VideoAnnotation.intervals: Tuple[Interval, Interval] for UCF
# or Tuple[Interval, ...] for XD (variable-length)
for (start, end) in anno.intervals:
    if start is not None:  # UCF uses None for no-interval
        ax.axvspan(start, end, alpha=0.15, color='red', label='_nolegend_')
```

---

#### Pattern 11: GatedFusion Model Structure for Hook Registration

**Model architecture** (`src/models/gated_fusion.py`, lines 28-79):

Key attributes for forward hooks:
- `model.gate` — `nn.Linear(2*shared_dim, shared_dim)`: raw linear output, NOT sigmoid-activated
- `model.ln_fused` — `nn.LayerNorm(shared_dim)`: post-fusion, post-residual output (256-d fused features)
- `model.ln_skel` — `nn.LayerNorm(shared_dim)`: projected skeleton features
- `model.ln_clip` — `nn.LayerNorm(shared_dim)`: projected CLIP features

**Forward pass** (line 73):
```python
g = torch.sigmoid(self.gate(torch.cat([p_skel, p_clip], dim=-1)))
fused = g * p_skel + (1.0 - g) * p_clip
residual = fused + p_skel + p_clip
out = self.dropout(self.ln_fused(residual))
return self.head(out).squeeze(-1)
```

**Critical pitfall (RESEARCH.md Pitfall 5):** `model.gate` is `nn.Linear`. A forward hook on it captures the LINEAR output (pre-sigmoid). Must apply `torch.sigmoid()` manually to get gate values in [0, 1].

---

#### Pattern 12: Model Loading for Forward Pass

**Registry** (`src/models/registry.py`, lines 44-56):
```python
from src.models.registry import build_model
model = build_model(variant="gated_fusion", **model_kwargs)
```

**Checkpoint loading** (`src/utils/checkpoint.py`, lines 48-53):
```python
from src.utils.checkpoint import load_checkpoint
state_dict = load_checkpoint("results/ucf_gated_fusion_s42/best_model.pth", device="cpu")
model.load_state_dict(state_dict, strict=True)  # CLAUDE.md: always strict=True
```

**Config snapshot** (for building model with correct kwargs):
```python
from src.utils.config import load_snapshot_as_config
cfg = load_snapshot_as_config(Path("results/ucf_gated_fusion_s42/config_snapshot.json"))
model = build_model(**cfg["model"])
```

---

#### Pattern 13: Inference Loop for Feature/Activation Collection

**Adapted from** `src/evaluate.py` lines 143-163 (`_run_inference`):

```python
@torch.no_grad()
def _run_inference(model, dataset, device: str) -> dict:
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)
    per_video_snippet_scores: dict = {}
    for batch in loader:
        vid = batch["video_id"][0] if isinstance(batch["video_id"], list) else batch["video_id"]
        kwargs = {}
        for k in ("skel", "clip", "i3d", "mask"):
            if k in batch:
                t = batch[k]
                if t.dim() == 2:
                    t = t.unsqueeze(0)
                kwargs[k] = t.to(device)
        scores = model(**kwargs)
        # ...
```

**Note:** `src/eval/test_loader.py` has a C3 import guard (line 67) that blocks imports from anything except `evaluate.py` or pytest. The Phase 6 chart script must either:
1. Bypass the test_loader and build the dataset directly using `src.data.dataset.MILFeatureDataset(mode="test")`, OR
2. Build the DataLoader inline from feature directories.

The simpler approach is to construct the dataset directly, avoiding the test_loader import guard.

---

#### Pattern 14: Skeleton Pickle Format

**From** `scripts/extract_skeletons.py` lines 16-22:

```python
# PYSKL pickle format:
#     {
#         'keypoint':       ndarray [M=2, T, V=17, C=2]  float32  (pixel coords)
#         'keypoint_score': ndarray [M=2, T, V=17]        float32
#         'img_shape':      (H, W)   actual frame resolution
#         'total_frames':   int      T
#         'video_id':       str
#     }
```

Skeleton pickles located at `E:/skeletons/{dataset}/{video_id}.pkl`.

**Pitfall (RESEARCH.md Pitfall 3):** UCF-Crime `img_shape` is (64, 64) -- low-res pre-extracted PNGs. Use XD-Violence videos (346x640+ MP4s at `E:/XD_Violence/test/videos/`) for overlay quality.

---

#### Pattern 15: Main Entrypoint Structure (Phase 4, lines 1077-1148)

Copy the sectioned main() with progress printing and file counting.

```python
def main():
    print("Phase 6 Analysis & Visualization")
    print("=" * 50)
    print(f"Output: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/N] Loading data...")
    # ...

    print("\n[2/N] Section A: Temporal Curves")
    # chart_A01(...), chart_A02(...), ...

    print("\n[3/N] Section B: Skeleton Overlays")
    # ...

    # Count generated files
    pngs = list(OUT_DIR.rglob("*.png"))
    print(f"\nDone! Generated {len(pngs)} PNG files in {OUT_DIR}")


if __name__ == "__main__":
    main()
```

---

## Shared Patterns

### Seaborn Theme + DPI
**Source:** `scripts/generate_phase4_charts.py` lines 46-64
**Apply to:** All chart generation in `generate_phase6_charts.py`

Must call `sns.set_theme(style="whitegrid", ...)` at module level before any plotting. DPI=150 for all `fig.savefig()` calls via the `_save()` helper.

### Variant Color Scheme (D-04)
**Source:** `scripts/generate_phase4_charts.py` lines 67-78
**Apply to:** All figures with 4-variant overlays (temporal curves, any comparison chart)

Skeleton=#64748B, CLIP=#3B82F6, Late Fusion=#F59E0B, Gated Fusion=#EF4444. These are locked by D-04.

### Figure Save Convention
**Source:** `scripts/generate_phase4_charts.py` lines 202-207
**Apply to:** Every figure generated

All PNGs saved via `_save(fig, subdir, name)` which creates subdirectories, uses DPI=150, tight bbox, white facecolor, and logs relative path.

### Annotation Parsing
**Source:** `src/eval/ucf_annotations.py` + `src/eval/xd_annotations.py`
**Apply to:** Temporal curves (GT shading), video selection (category filtering)

Parse once, reuse the `{video_id: VideoAnnotation}` dict. Guard XD normal videos with `if vid in annos`.

### Model Loading (strict=True)
**Source:** `src/utils/checkpoint.py` lines 48-53 + CLAUDE.md convention
**Apply to:** Gate activation collection, feature projection (forward pass)

Always `model.load_state_dict(state_dict, strict=True)`. Never use `strict=False`.

---

## No Analog Found

| File/Section | Role | Data Flow | Reason |
|--------------|------|-----------|--------|
| Skeleton overlay drawing (B_skeleton) | visualization | file-I/O (video frame + pickle) | No existing code draws COCO-17 keypoints on video frames. Closest is the skeleton extraction script, but it only extracts, not overlays. Use cv2.circle + cv2.line pattern from RESEARCH.md. |
| Gate activation histograms (D_gating) | visualization | GPU inference + transform | No existing code collects or visualizes gate sigmoid outputs. Use PyTorch forward hook pattern from RESEARCH.md Pattern 3. |
| t-SNE feature projection (E_projection) | visualization | GPU inference + CPU transform | No existing code does dimensionality reduction visualization. Use sklearn.manifold.TSNE from RESEARCH.md Pattern. |
| Video selection heuristic | utility | transform | No existing code selects "best-detection" videos. Use score-GT separation heuristic from RESEARCH.md Code Examples. |

---

## Metadata

**Analog search scope:** `scripts/`, `src/models/`, `src/eval/`, `src/utils/`, `results/tta/`
**Files scanned:** 11 (generate_phase4_charts.py, generate_phase7_charts.py, gated_fusion.py, evaluate.py, registry.py, checkpoint.py, ucf_annotations.py, xd_annotations.py, test_loader.py, extract_skeletons.py, TTA eval_metrics.json sample)
**Pattern extraction date:** 2026-05-02
