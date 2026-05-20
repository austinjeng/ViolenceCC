# Phase 9: SigLIP2-SO400M Backbone Comparison - Pattern Map

**Mapped:** 2026-05-20
**Files analyzed:** 16 (1 modified script, 10 new configs, 1 modified script, 1 new script, 3 modified tests)
**Analogs found:** 16 / 16

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/extract_clip.py` (MODIFY) | config-dict | batch | itself (Phase 8 `siglip2-base` entry) | exact |
| `configs/clip_only_so400m.yaml` (NEW) | config | -- | `configs/clip_only_siglip2.yaml` | exact |
| `configs/clip_only_xd_so400m.yaml` (NEW) | config | -- | `configs/clip_only_xd_siglip2.yaml` | exact |
| `configs/late_fusion_so400m.yaml` (NEW) | config | -- | `configs/late_fusion_siglip2.yaml` | exact |
| `configs/late_fusion_xd_so400m.yaml` (NEW) | config | -- | `configs/late_fusion_xd_siglip2.yaml` | exact |
| `configs/gated_fusion_so400m.yaml` (NEW) | config | -- | `configs/gated_fusion_siglip2.yaml` | exact |
| `configs/gated_fusion_xd_so400m.yaml` (NEW) | config | -- | `configs/gated_fusion_xd_siglip2.yaml` | exact |
| `configs/gated_fusion_so400m_2person.yaml` (NEW) | config | -- | `configs/gated_fusion_siglip2_2person.yaml` | exact |
| `configs/gated_fusion_xd_so400m_2person.yaml` (NEW) | config | -- | `configs/gated_fusion_xd_siglip2_2person.yaml` | exact |
| `configs/gated_fusion_so400m_clip_mean.yaml` (NEW) | config | -- | `configs/gated_fusion_siglip2_clip_mean.yaml` | exact |
| `configs/gated_fusion_xd_so400m_clip_mean.yaml` (NEW) | config | -- | `configs/gated_fusion_xd_siglip2_clip_mean.yaml` | exact |
| `scripts/run_ablations.py` (MODIFY) | orchestrator | batch | itself (Phase 8 `phase8_*` queues) | exact |
| `scripts/generate_phase9_charts.py` (NEW) | analysis | transform | `scripts/generate_phase8_charts.py` | exact |
| `tests/test_extract_siglip2.py` (MODIFY) | test | -- | itself (Phase 8 assertions) | exact |
| `tests/test_models.py` (MODIFY) | test | -- | itself (Phase 8 `clip_dim_1536` tests) | exact |
| `tests/test_run_ablations.py` (MODIFY) | test | -- | itself (Phase 8 queue assertions) | exact |

## Pattern Assignments

### `scripts/extract_clip.py` -- Add `siglip2-so400m` to BACKBONE_CONFIGS (config-dict, batch)

**Analog:** itself, lines 119-134

**BACKBONE_CONFIGS dict pattern** (lines 119-134):
```python
BACKBONE_CONFIGS = {
    "clip-vit-b-16": {
        "model_name": "ViT-B-16",
        "pretrained": "openai",
        "embed_dim": 512,       # encode_image output dim
        "output_subdir": "clip",
        "mean_subdir": "clip_mean",
    },
    "siglip2-base": {
        "model_name": "ViT-B-16-SigLIP2-256",
        "pretrained": "webli",
        "embed_dim": 768,       # encode_image output dim
        "output_subdir": "siglip2",
        "mean_subdir": "siglip2_mean",
    },
}
```

**New entry to add after line 133** (before the closing `}`):
```python
    "siglip2-so400m": {
        "model_name": "ViT-SO400M-16-SigLIP2-256",
        "pretrained": "webli",
        "embed_dim": 1152,      # encode_image output dim
        "output_subdir": "siglip2_so400m",
        "mean_subdir": "siglip2_so400m_mean",
    },
```

**Key values:** `embed_dim: 1152` (NOT 768 or 1536). Mean+max pooled output = 2304. Mean-only = 1152. Verified empirically on this machine.

---

### `configs/clip_only_so400m.yaml` (config, UCF clip_only)

**Analog:** `configs/clip_only_siglip2.yaml` (full file, 40 lines)

**Changes from analog:**
- Line 1 comment: `Phase 9` instead of `Phase 8`, `SO400M` instead of `SigLIP2`
- Line 8 `clip_features`: `"E:/features/ucf/siglip2_so400m"` (was `siglip2`)
- Line 14 `clip_dim`: `2304` (was `1536`)
- Line 39 tags: `[phase9, clip_only, ucf, so400m]` (was `[phase8, clip_only, ucf, siglip2]`)

**Full analog for reference** (`configs/clip_only_siglip2.yaml`):
```yaml
# configs/clip_only_siglip2.yaml
# Phase 8: SigLIP2 CLIP-Only MIL baseline. Mirrors clip_only.yaml with SigLIP2 features.
seed: 42
dataset: ucf

paths:
  skeleton_features: "E:/features/ucf/skeleton"
  clip_features: "E:/features/ucf/siglip2"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: clip_only
  clip_dim: 1536
  proj_dim: 512
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32
  batch_size: 16
  num_workers: 4
  pin_memory: true

train:
  lr: 1.0e-4
  weight_decay: 1.0e-2
  epochs: 50
  warmup_epochs: 5
  patience: 10
  k_topk: 3
  margin: 1.0
  lam_sparse: 8.0e-3
  lam_smooth: 8.0e-4

wandb:
  project: violencecc
  mode: disabled
  tags: [phase8, clip_only, ucf, siglip2]
```

---

### `configs/clip_only_xd_so400m.yaml` (config, XD clip_only)

**Analog:** `configs/clip_only_xd_siglip2.yaml` (full file, 40 lines)

**Changes from analog:**
- Line 1 comment: `Phase 9`, `SO400M`
- Line 2 dataset: `xd` (already correct in analog)
- Line 8 `clip_features`: `"E:/features/xd/siglip2_so400m"`
- Line 14 `clip_dim`: `2304`
- Line 39 tags: `[phase9, clip_only, xd, so400m]`

---

### `configs/late_fusion_so400m.yaml` (config, UCF late_fusion)

**Analog:** `configs/late_fusion_siglip2.yaml` (full file, 42 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/ucf/siglip2_so400m"`
- `clip_dim`: `2304`
- tags: `[phase9, late_fusion, ucf, so400m]`

**Note:** Retains `proj_dim: 512` and `alpha: equal` unchanged from analog.

---

### `configs/late_fusion_xd_so400m.yaml` (config, XD late_fusion)

**Analog:** `configs/late_fusion_xd_siglip2.yaml` (full file, 42 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/xd/siglip2_so400m"`
- `clip_dim`: `2304`
- tags: `[phase9, late_fusion, xd, so400m]`

---

### `configs/gated_fusion_so400m.yaml` (config, UCF gated_fusion)

**Analog:** `configs/gated_fusion_siglip2.yaml` (full file, 41 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/ucf/siglip2_so400m"`
- `clip_dim`: `2304` (was `1536`)
- `shared_dim`: `256` (UNCHANGED -- critical for controlled comparison)
- tags: `[phase9, gated_fusion, ucf, so400m]`

**Full analog for reference** (`configs/gated_fusion_siglip2.yaml`):
```yaml
# configs/gated_fusion_siglip2.yaml
# Phase 8: SigLIP2 Gated Fusion (primary thesis model). Mirrors gated_fusion.yaml with SigLIP2 features.
seed: 42
dataset: ucf

paths:
  skeleton_features: "E:/features/ucf/skeleton"
  clip_features: "E:/features/ucf/siglip2"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: gated_fusion
  skel_dim: 256
  clip_dim: 1536
  shared_dim: 256          # PRD 9.2 shared projection space
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32
  batch_size: 16
  num_workers: 4
  pin_memory: true

train:
  lr: 1.0e-4
  weight_decay: 1.0e-2
  epochs: 50
  warmup_epochs: 5
  patience: 10
  k_topk: 3
  margin: 1.0
  lam_sparse: 8.0e-3
  lam_smooth: 8.0e-4

wandb:
  project: violencecc
  mode: disabled
  tags: [phase8, gated_fusion, ucf, siglip2]
```

---

### `configs/gated_fusion_xd_so400m.yaml` (config, XD gated_fusion)

**Analog:** `configs/gated_fusion_xd_siglip2.yaml` (full file, 41 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/xd/siglip2_so400m"`
- `clip_dim`: `2304`
- tags: `[phase9, gated_fusion, xd, so400m]`

---

### `configs/gated_fusion_so400m_2person.yaml` (config, UCF 2person ablation)

**Analog:** `configs/gated_fusion_siglip2_2person.yaml` (full file, 42 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/ucf/siglip2_so400m"` (NOT `siglip2`)
- `clip_dim`: `2304`
- `skel_dim`: `512` (UNCHANGED -- 2person concat)
- `skel_agg: concat` (UNCHANGED)
- `skeleton_features`: `"E:/features/ucf/skeleton_2person"` (UNCHANGED)
- tags: `[phase9, gated_fusion, ucf, 2person, so400m]`

---

### `configs/gated_fusion_xd_so400m_2person.yaml` (config, XD 2person ablation)

**Analog:** `configs/gated_fusion_xd_siglip2_2person.yaml` (full file, 42 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/xd/siglip2_so400m"`
- `clip_dim`: `2304`
- tags: `[phase9, gated_fusion, xd, 2person, so400m]`

---

### `configs/gated_fusion_so400m_clip_mean.yaml` (config, UCF mean-only ablation)

**Analog:** `configs/gated_fusion_siglip2_clip_mean.yaml` (full file, 41 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/ucf/siglip2_so400m_mean"` (was `siglip2_mean`)
- `clip_dim`: `1152` (was `768`; mean-only = embed_dim, NOT embed_dim*2)
- tags: `[phase9, gated_fusion, ucf, clip_mean, so400m]`

**Critical dimension note:** Mean-only configs use `clip_dim: 1152` (embed_dim). Mean+max configs use `clip_dim: 2304` (embed_dim * 2).

---

### `configs/gated_fusion_xd_so400m_clip_mean.yaml` (config, XD mean-only ablation)

**Analog:** `configs/gated_fusion_xd_siglip2_clip_mean.yaml` (full file, 41 lines)

**Changes from analog:**
- Comment: `Phase 9`, `SO400M`
- `clip_features`: `"E:/features/xd/siglip2_so400m_mean"`
- `clip_dim`: `1152`
- tags: `[phase9, gated_fusion, xd, clip_mean, so400m]`

---

### `scripts/run_ablations.py` -- Add `phase9_*` queues (orchestrator, batch)

**Analog:** itself, lines 187-211 (Phase 8 queues)

**Phase 8 queue pattern** (lines 187-211):
```python
    "phase8_ucf_main": [
        RunSpec("ucf", "clip_only",    42, "configs/clip_only_siglip2.yaml",    "siglip2"),
        RunSpec("ucf", "late_fusion",  42, "configs/late_fusion_siglip2.yaml",  "siglip2"),
        RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion_siglip2.yaml", "siglip2"),
    ],
    "phase8_xd_main": [
        RunSpec("xd", "clip_only",    42, "configs/clip_only_xd_siglip2.yaml",    "siglip2"),
        RunSpec("xd", "late_fusion",  42, "configs/late_fusion_xd_siglip2.yaml",  "siglip2"),
        RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd_siglip2.yaml", "siglip2"),
    ],
    "phase8_ucf_pooling": [
        RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion_siglip2_2person.yaml",   "siglip2_2person"),
        RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion_siglip2_clip_mean.yaml", "siglip2_clip_mean"),
    ],
    "phase8_xd_pooling": [
        RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd_siglip2_2person.yaml",   "siglip2_2person"),
        RunSpec("xd", "gated_fusion", 42, "configs/gated_fusion_xd_siglip2_clip_mean.yaml", "siglip2_clip_mean"),
    ],
    "phase8_ucf_seeds": [
        RunSpec("ucf", "gated_fusion", 123,  "configs/gated_fusion_siglip2.yaml", "siglip2"),
        RunSpec("ucf", "gated_fusion", 2024, "configs/gated_fusion_siglip2.yaml", "siglip2"),
    ],
    "phase8_xd_seeds": [
        RunSpec("xd", "gated_fusion", 123,  "configs/gated_fusion_xd_siglip2.yaml", "siglip2"),
        RunSpec("xd", "gated_fusion", 2024, "configs/gated_fusion_xd_siglip2.yaml", "siglip2"),
    ],
```

**New Phase 9 queues to add** (same structure, `so400m` cache_variant):
- `phase9_ucf_main`: 3 RunSpecs (clip_only, late_fusion, gated_fusion) with `"so400m"` cache_variant
- `phase9_xd_main`: 3 RunSpecs
- `phase9_ucf_pooling`: 2 RunSpecs (2person as `"so400m_2person"`, clip_mean as `"so400m_clip_mean"`)
- `phase9_xd_pooling`: 2 RunSpecs
- `phase9_ucf_seeds`: 2 RunSpecs (seeds 123, 2024)
- `phase9_xd_seeds`: 2 RunSpecs
- **Total:** 14 new RunSpecs (6 queues)

---

### `scripts/generate_phase9_charts.py` (analysis, transform)

**Analog:** `scripts/generate_phase8_charts.py` (full file, 244 lines)

**Imports pattern** (lines 1-29):
```python
#!/usr/bin/env python
"""
Phase 8 CLIP vs SigLIP2 Backbone Comparison
============================================
...
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# --- Project Setup -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

**Style constants pattern** (lines 31-52):
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

OUT_DIR = PROJECT_ROOT / "results" / "phase8_charts"
```

**COMPARISON_MAP pattern** (lines 57-72) -- extend to three-column:
```python
COMPARISON_MAP = {
    # Maps (dataset, display_label) -> (clip_run_name, siglip2_run_name)
    ("ucf", "CLIP/SigLIP2 Only"): ("ucf_clip_only_s42", "ucf_clip_only_siglip2_s42"),
    ...
}
```

Phase 9 extends this to include SO400M run names as a third element in each tuple (or a separate SO400M_MAP dict).

**build_comparison_table pattern** (lines 90-104):
```python
def build_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.set_index("run_name")
    rows = []
    for (dataset, label), (clip_name, sig_name) in COMPARISON_MAP.items():
        row = {"Dataset": dataset.upper(), "Variant": label}
        if clip_name in idx.index:
            row["CLIP_AUC"] = idx.loc[clip_name, "auc"]
            row["CLIP_AP"] = idx.loc[clip_name, "ap"]
        if sig_name and sig_name in idx.index:
            row["SigLIP2_AUC"] = idx.loc[sig_name, "auc"]
            row["SigLIP2_AP"] = idx.loc[sig_name, "ap"]
            row["Delta_AUC"] = row["SigLIP2_AUC"] - row["CLIP_AUC"]
            row["Delta_AP"] = row["SigLIP2_AP"] - row["CLIP_AP"]
        rows.append(row)
    return pd.DataFrame(rows)
```

Phase 9 extends this to add `SO400M_AUC`, `SO400M_AP`, and delta columns for CLIP-vs-SO400M and SigLIP2-vs-SO400M.

**plot_comparison_bars pattern** (lines 124-158) -- extend from 2 bars to 3 bars per group:
```python
def plot_comparison_bars(comp, metric, title, filename):
    # ... grouped bar chart with 2 bars per x-tick
    width = 0.35
    bars1 = ax.bar(x - width / 2, ..., label="CLIP ViT-B/16", color="#3B82F6")
    bars2 = ax.bar(x + width / 2, ..., label="SigLIP2 ViT-B/16", color="#EF4444")
```

Phase 9 uses 3 bars (width ~0.25) with a third color for SO400M.

**main() pattern** (lines 208-243):
```python
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_results()
    comp = build_comparison_table(df)
    comp.to_csv(OUT_DIR / "backbone_comparison.csv", ...)
    seed_df = build_seed_table(df)
    seed_df.to_csv(OUT_DIR / "seed_stability.csv", ...)
    plot_comparison_bars(comp, "AUC", ...)
    plot_comparison_bars(comp, "AP", ...)
    plot_seed_stability(seed_df, ...)
```

---

### `tests/test_extract_siglip2.py` -- Add SO400M assertions (test)

**Analog:** itself (full file, 77 lines)

**test_backbone_configs_keys pattern** (line 18-20):
```python
def test_backbone_configs_keys():
    """BACKBONE_CONFIGS has exactly the expected backbone keys."""
    assert set(BACKBONE_CONFIGS.keys()) == {"clip-vit-b-16", "siglip2-base"}
```
Update to: `== {"clip-vit-b-16", "siglip2-base", "siglip2-so400m"}`

**test_siglip2_config_values pattern** (lines 33-40) -- add analogous `test_so400m_config_values`:
```python
def test_siglip2_config_values():
    """siglip2-base entry has correct model_name, pretrained, embed_dim, and subdirs."""
    cfg = BACKBONE_CONFIGS["siglip2-base"]
    assert cfg["model_name"] == "ViT-B-16-SigLIP2-256"
    assert cfg["pretrained"] == "webli"
    assert cfg["embed_dim"] == 768
    assert cfg["output_subdir"] == "siglip2"
    assert cfg["mean_subdir"] == "siglip2_mean"
```
New test asserts: `model_name == "ViT-SO400M-16-SigLIP2-256"`, `embed_dim == 1152`, `output_subdir == "siglip2_so400m"`, `mean_subdir == "siglip2_so400m_mean"`.

**test_expected_dim_mean_pool pattern** (lines 43-51) -- add `siglip2-so400m` branch:
```python
def test_expected_dim_mean_pool():
    for backbone_key, cfg in BACKBONE_CONFIGS.items():
        embed_dim = cfg["embed_dim"]
        expected_dim = embed_dim
        if backbone_key == "clip-vit-b-16":
            assert expected_dim == 512
        elif backbone_key == "siglip2-base":
            assert expected_dim == 768
```
Add: `elif backbone_key == "siglip2-so400m": assert expected_dim == 1152`

**test_expected_dim_meanmax_pool pattern** (lines 54-62) -- add SO400M branch:
Add: `elif backbone_key == "siglip2-so400m": assert expected_dim == 2304`

---

### `tests/test_models.py` -- Add `clip_dim=2304` forward-pass tests (test)

**Analog:** itself, Phase 8 tests at lines 72-88 and 216-222

**CLIPProj 1536 pattern** (lines 72-88):
```python
def test_clip_dim_1536():
    """Phase 8: CLIPProj with SigLIP2 1536-d input."""
    torch.manual_seed(0)
    model = CLIPProj(clip_dim=1536)
    clip = torch.randn(2, 32, 1536)
    out = model(clip=clip)
    assert out.shape == (2, 32)
    assert (out >= 0).all() and (out <= 1).all()

def test_clip_dim_1536_projection_layer():
    """Phase 8: CLIPProj(clip_dim=1536) projection maps 1536->512."""
    model = CLIPProj(clip_dim=1536)
    assert isinstance(model.clip_proj, nn.Linear)
    assert model.clip_proj.in_features == 1536
    assert model.clip_proj.out_features == 512
```

New tests: `test_clip_dim_2304()` with `clip_dim=2304`, `torch.randn(2, 32, 2304)`, assert shape `(2, 32)`. And `test_clip_dim_2304_projection_layer()` with `in_features == 2304`.

**LateFusion 1536 pattern** (line 162-168):
```python
def test_late_fusion_clip_dim_1536():
    model = LateFusion(skel_dim=256, clip_dim=1536, proj_dim=512, alpha="equal")
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 1536)
    out = model(skel=skel, clip=clip)
```

New test: `test_late_fusion_clip_dim_2304()` with `clip_dim=2304`.

**GatedFusion 1536 pattern** (lines 216-222):
```python
def test_gated_fusion_clip_dim_1536():
    model = GatedFusion(skel_dim=256, clip_dim=1536, shared_dim=256)
    skel = torch.randn(2, 32, 256)
    clip = torch.randn(2, 32, 1536)
    out = model(skel=skel, clip=clip)
```

New test: `test_gated_fusion_clip_dim_2304()` with `clip_dim=2304`.

---

### `tests/test_run_ablations.py` -- Add Phase 9 queue assertions (test)

**Analog:** itself, lines 32-96

**test_help_has_expected_queues pattern** (lines 32-47):
```python
def test_help_has_expected_queues():
    ...
    for q in ("rtfm_gate", ...,
              "phase8_ucf_main", "phase8_xd_main",
              "phase8_ucf_pooling", "phase8_xd_pooling",
              "phase8_ucf_seeds", "phase8_xd_seeds"):
        assert q in combined, ...
```
Add Phase 9 queue names to the tuple: `"phase9_ucf_main", "phase9_xd_main", "phase9_ucf_pooling", "phase9_xd_pooling", "phase9_ucf_seeds", "phase9_xd_seeds"`.

**test_queue_definitions pattern** (lines 82-96):
```python
    # Phase 8 SigLIP2 backbone comparison queues
    assert len(QUEUES["phase8_ucf_main"]) == 3
    assert len(QUEUES["phase8_xd_main"]) == 3
    assert len(QUEUES["phase8_ucf_pooling"]) == 2
    assert len(QUEUES["phase8_xd_pooling"]) == 2
    assert len(QUEUES["phase8_ucf_seeds"]) == 2
    assert len(QUEUES["phase8_xd_seeds"]) == 2
    # Phase 8 run_name spot checks
    assert QUEUES["phase8_ucf_main"][2].run_name == "ucf_gated_fusion_siglip2_s42"
    assert QUEUES["phase8_xd_seeds"][0].run_name == "xd_gated_fusion_siglip2_s123"
    # Total unique specs across all queues = 238
    all_run_names = {
        s.run_name for q in QUEUES.values() for s in q
    }
    assert len(all_run_names) == 238, ...
```

Add Phase 9 assertions (same structure):
- `assert len(QUEUES["phase9_ucf_main"]) == 3`
- `assert len(QUEUES["phase9_xd_main"]) == 3`
- `assert len(QUEUES["phase9_ucf_pooling"]) == 2`
- `assert len(QUEUES["phase9_xd_pooling"]) == 2`
- `assert len(QUEUES["phase9_ucf_seeds"]) == 2`
- `assert len(QUEUES["phase9_xd_seeds"]) == 2`
- Spot checks: `QUEUES["phase9_ucf_main"][2].run_name == "ucf_gated_fusion_so400m_s42"`
- Update total: `assert len(all_run_names) == 252` (238 + 14)

---

## Shared Patterns

### Config Dimension Mapping (applies to all 10 YAML configs)

**Rule:** SO400M embed_dim = 1152. Mean+max pooled = 2304. Mean-only = 1152.

| Config Type | `clip_dim` | `clip_features` subdirectory |
|-------------|-----------|------------------------------|
| clip_only, late_fusion, gated_fusion, 2person | `2304` | `siglip2_so400m` |
| clip_mean (mean-only) | `1152` | `siglip2_so400m_mean` |

### Config Naming Convention (applies to all 10 YAML configs)

**Source:** Phase 8 naming pattern in `configs/` directory

| Phase 8 Name | Phase 9 Name |
|--------------|--------------|
| `*_siglip2.yaml` | `*_so400m.yaml` |
| `*_xd_siglip2.yaml` | `*_xd_so400m.yaml` |
| `*_siglip2_2person.yaml` | `*_so400m_2person.yaml` |
| `*_siglip2_clip_mean.yaml` | `*_so400m_clip_mean.yaml` |

### Queue cache_variant Convention (applies to all 6 queues)

**Source:** Phase 8 queues in `scripts/run_ablations.py` lines 187-211

| Phase 8 cache_variant | Phase 9 cache_variant |
|------------------------|-----------------------|
| `"siglip2"` | `"so400m"` |
| `"siglip2_2person"` | `"so400m_2person"` |
| `"siglip2_clip_mean"` | `"so400m_clip_mean"` |

### Wandb Tag Convention (applies to all 10 configs)

**Source:** Phase 8 tags pattern

Replace `phase8` with `phase9` and `siglip2` with `so400m` in all tags arrays.

### Test Assertion Constants

| Constant | Phase 8 Value | Phase 9 Value |
|----------|---------------|---------------|
| BACKBONE_CONFIGS key count | 2 | 3 |
| Total unique run_names | 238 | 252 |
| SO400M embed_dim | -- | 1152 |
| SO400M mean+max dim | -- | 2304 |

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | -- | -- | All files have exact analogs from Phase 8 |

Every file in Phase 9 has an exact structural analog from Phase 8. This phase is entirely mechanical substitution.

## Metadata

**Analog search scope:** `configs/`, `scripts/`, `tests/`
**Files scanned:** 16 analogs identified and read
**Pattern extraction date:** 2026-05-20
