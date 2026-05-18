# Phase 8: SigLIP2 Backbone Comparison - Pattern Map

**Mapped:** 2026-05-19
**Files analyzed:** 16 new/modified files
**Analogs found:** 16 / 16

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/extract_clip.py` (MODIFY) | utility | batch-transform | self (current version) | exact |
| `configs/clip_only_siglip2.yaml` (NEW) | config | -- | `configs/clip_only.yaml` | exact |
| `configs/clip_only_xd_siglip2.yaml` (NEW) | config | -- | `configs/clip_only_xd.yaml` | exact |
| `configs/late_fusion_siglip2.yaml` (NEW) | config | -- | `configs/late_fusion.yaml` | exact |
| `configs/late_fusion_xd_siglip2.yaml` (NEW) | config | -- | `configs/late_fusion_xd.yaml` | exact |
| `configs/gated_fusion_siglip2.yaml` (NEW) | config | -- | `configs/gated_fusion.yaml` | exact |
| `configs/gated_fusion_xd_siglip2.yaml` (NEW) | config | -- | `configs/gated_fusion_xd.yaml` | exact |
| `configs/gated_fusion_siglip2_2person.yaml` (NEW) | config | -- | `configs/gated_fusion_2person.yaml` | exact |
| `configs/gated_fusion_xd_siglip2_2person.yaml` (NEW) | config | -- | `configs/gated_fusion_xd_2person.yaml` | exact |
| `configs/gated_fusion_siglip2_clip_mean.yaml` (NEW) | config | -- | `configs/gated_fusion_clip_mean.yaml` | exact |
| `configs/gated_fusion_xd_siglip2_clip_mean.yaml` (NEW) | config | -- | `configs/gated_fusion_xd_clip_mean.yaml` | exact |
| `scripts/run_ablations.py` (MODIFY) | utility | batch-orchestration | self (Phase 7 queue pattern) | exact |
| `scripts/generate_phase8_charts.py` (NEW) | utility | transform | `scripts/generate_phase6_charts.py` | role-match |
| `tests/test_extract_siglip2.py` (NEW) | test | -- | `tests/test_models.py` | role-match |
| `tests/test_models.py` (MODIFY) | test | -- | self (existing clip_dim tests) | exact |
| `tests/test_run_ablations.py` (MODIFY) | test | -- | self (existing queue tests) | exact |

## Pattern Assignments

### `scripts/extract_clip.py` (MODIFY: add --backbone flag)

**Analog:** self -- the modification adds a backbone registry dict and parameterizes model loading, preprocessing, output dim, and output subdir.

**Model loading pattern** (lines 106-123) -- current CLIP-only loading to be replaced by backbone dispatch:
```python
def load_clip_model(device: str = "cuda"):
    import open_clip
    logger.info("Loading CLIP ViT-B/16 (pretrained='openai')...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-16", pretrained="openai"
    )
    model.eval()
    model.to(device)
    logger.info(f"CLIP model loaded on {device}.")
    return model, preprocess
```

**New backbone registry pattern** (from RESEARCH.md Pattern 1, lines 177-200):
```python
BACKBONE_CONFIGS = {
    "clip-vit-b-16": {
        "model_name": "ViT-B-16",
        "pretrained": "openai",
        "embed_dim": 512,       # encode_image output dim
        "output_subdir": "clip",
        "mean_subdir": "clip_mean",
    },
    "siglip2-giant": {
        "model_name": "ViT-gopt-16-SigLIP2-384",
        "pretrained": "webli",
        "embed_dim": 1536,      # encode_image output dim
        "output_subdir": "siglip2",
        "mean_subdir": "siglip2_mean",
    },
}

def load_vision_model(backbone: str, device: str = "cuda"):
    cfg = BACKBONE_CONFIGS[backbone]
    model, _, preprocess = open_clip.create_model_and_transforms(
        cfg["model_name"], pretrained=cfg["pretrained"]
    )
    model.eval().to(device)
    return model, preprocess, cfg
```

**Hardcoded dimension assertions to parameterize** (lines 313, 441-445, 581-583):
```python
# Line 313: in extract_clip_snippet()
expected_dim = 512 if pool == "mean" else 1024

# Lines 441-445: in extract_video_clip_features()
expected_dim = 512 if pool == "mean" else 1024
assert all_feats.shape[1] == expected_dim, (...)

# Lines 581-583: in run_extraction() main loop
expected_dim = 512 if pool == "mean" else 1024
assert feats.shape[1] == expected_dim, (...)
```

**Parameterized replacement pattern** (from RESEARCH.md lines 343-363):
```python
# embed_dim comes from BACKBONE_CONFIGS[backbone]["embed_dim"]
expected_dim = embed_dim if pool == "mean" else embed_dim * 2
```

**Output subdir selection pattern** (lines 500-508) -- current:
```python
if corruption_type is not None:
    out_subdir = f"clip_{corruption_type}_{corruption_severity}"
elif pool == "mean":
    out_subdir = "clip_mean"
else:
    out_subdir = "clip"
output_dir = FEATURE_ROOT / dataset / out_subdir
```

**New backbone-aware subdir pattern:**
```python
# cfg = BACKBONE_CONFIGS[backbone]
if corruption_type is not None:
    out_subdir = f"{cfg['output_subdir']}_{corruption_type}_{corruption_severity}"
elif pool == "mean":
    out_subdir = cfg["mean_subdir"]
else:
    out_subdir = cfg["output_subdir"]
output_dir = FEATURE_ROOT / dataset / out_subdir
```

**CLI argparse pattern** (lines 706-762) -- add `--backbone` flag following existing `--pool` pattern:
```python
parser.add_argument(
    "--backbone",
    choices=["clip-vit-b-16", "siglip2-giant"],
    default="clip-vit-b-16",
    help="Vision backbone: 'clip-vit-b-16' (default, 512-d) or 'siglip2-giant' (1536-d).",
)
```

**Batch size default** (line 730) -- current default is 64; SigLIP2 needs lower. Handle via backbone config or CLI default guidance. SigLIP2 recommended: `--batch-size 16`.

---

### `configs/clip_only_siglip2.yaml` (NEW, config)

**Analog:** `configs/clip_only.yaml` (lines 1-40)

Copy the entire file verbatim. Change exactly three fields:
```yaml
# configs/clip_only_siglip2.yaml
# Phase 8: SigLIP2 CLIP-Only MIL baseline. Mirrors clip_only.yaml with SigLIP2 features.

paths:
  clip_features: "E:/features/ucf/siglip2"    # was "E:/features/ucf/clip"

model:
  clip_dim: 3072          # was 1024; SigLIP2 mean+max = 2 * 1536

wandb:
  tags: [phase8, clip_only, ucf, siglip2]      # was [phase3, clip_only, ucf]
```

All other fields (seed, dataset, proj_dim, data, train, paths.skeleton_features, paths.splits_dir, paths.results_dir) remain identical.

---

### `configs/clip_only_xd_siglip2.yaml` (NEW, config)

**Analog:** `configs/clip_only_xd.yaml` (lines 1-40)

Same pattern as UCF variant. Change three fields:
```yaml
paths:
  clip_features: "E:/features/xd/siglip2"     # was "E:/features/xd/clip"

model:
  clip_dim: 3072          # was 1024

wandb:
  tags: [phase8, clip_only, xd, siglip2]       # was [phase4c, clip_only, xd]
```

---

### `configs/late_fusion_siglip2.yaml` (NEW, config)

**Analog:** `configs/late_fusion.yaml` (lines 1-42)

Change three fields:
```yaml
paths:
  clip_features: "E:/features/ucf/siglip2"    # was "E:/features/ucf/clip"

model:
  clip_dim: 3072          # was 1024

wandb:
  tags: [phase8, late_fusion, ucf, siglip2]    # was [phase3, late_fusion, ucf]
```

---

### `configs/late_fusion_xd_siglip2.yaml` (NEW, config)

**Analog:** `configs/late_fusion_xd.yaml` (lines 1-42)

```yaml
paths:
  clip_features: "E:/features/xd/siglip2"

model:
  clip_dim: 3072

wandb:
  tags: [phase8, late_fusion, xd, siglip2]
```

---

### `configs/gated_fusion_siglip2.yaml` (NEW, config)

**Analog:** `configs/gated_fusion.yaml` (lines 1-41)

```yaml
paths:
  clip_features: "E:/features/ucf/siglip2"    # was "E:/features/ucf/clip"

model:
  clip_dim: 3072          # was 1024

wandb:
  tags: [phase8, gated_fusion, ucf, siglip2]   # was [phase3, gated_fusion, ucf]
```

---

### `configs/gated_fusion_xd_siglip2.yaml` (NEW, config)

**Analog:** `configs/gated_fusion_xd.yaml` (lines 1-41)

```yaml
paths:
  clip_features: "E:/features/xd/siglip2"

model:
  clip_dim: 3072

wandb:
  tags: [phase8, gated_fusion, xd, siglip2]
```

---

### `configs/gated_fusion_siglip2_2person.yaml` (NEW, config)

**Analog:** `configs/gated_fusion_2person.yaml` (lines 1-45)

Change three fields (keep `skel_dim: 512` and `data.skel_agg: concat` from 2person analog):
```yaml
paths:
  clip_features: "E:/features/ucf/siglip2"

model:
  skel_dim: 512           # unchanged from 2person analog
  clip_dim: 3072          # was 1024

data:
  skel_agg: concat        # unchanged from 2person analog

wandb:
  tags: [phase8, gated_fusion, ucf, 2person, siglip2]
```

---

### `configs/gated_fusion_xd_siglip2_2person.yaml` (NEW, config)

**Analog:** `configs/gated_fusion_xd_2person.yaml`

Same pattern as UCF 2person variant with XD paths:
```yaml
paths:
  skeleton_features: "E:/features/xd/skeleton_2person"
  clip_features: "E:/features/xd/siglip2"

model:
  skel_dim: 512
  clip_dim: 3072

data:
  skel_agg: concat

wandb:
  tags: [phase8, gated_fusion, xd, 2person, siglip2]
```

---

### `configs/gated_fusion_siglip2_clip_mean.yaml` (NEW, config)

**Analog:** `configs/gated_fusion_clip_mean.yaml` (lines 1-44)

Key difference: mean-only SigLIP2 is 1536-d (not 512-d like CLIP mean-only):
```yaml
paths:
  clip_features: "E:/features/ucf/siglip2_mean"   # was "E:/features/ucf/clip_mean"

model:
  clip_dim: 1536          # was 512; SigLIP2 mean-only = 1536

wandb:
  tags: [phase8, gated_fusion, ucf, clip_mean, siglip2]
```

---

### `configs/gated_fusion_xd_siglip2_clip_mean.yaml` (NEW, config)

**Analog:** `configs/gated_fusion_xd_clip_mean.yaml` (lines 1-44)

```yaml
paths:
  clip_features: "E:/features/xd/siglip2_mean"

model:
  clip_dim: 1536

wandb:
  tags: [phase8, gated_fusion, xd, clip_mean, siglip2]
```

---

### `scripts/run_ablations.py` (MODIFY: add phase8 queues)

**Analog:** self -- Phase 4/4c queue definitions (lines 133-185) and Phase 7 sweep queues (lines 192-345).

**Phase 4 main queue pattern** (lines 143-148):
```python
"phase4_main": [
    RunSpec("ucf", "skeleton_only", 42, "configs/skeleton_only.yaml"),
    RunSpec("ucf", "clip_only",     42, "configs/clip_only.yaml"),
    RunSpec("ucf", "late_fusion",   42, "configs/late_fusion.yaml"),
    RunSpec("ucf", "gated_fusion",  42, "configs/gated_fusion.yaml"),
],
```

**Phase 4 pooling queue pattern** (lines 149-158):
```python
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
```

**Phase 4 seeds queue pattern** (lines 159-163):
```python
"phase4_seeds": [
    RunSpec("ucf", "gated_fusion", 123, "configs/gated_fusion.yaml"),
    RunSpec("ucf", "gated_fusion", 2024, "configs/gated_fusion.yaml"),
],
```

**New Phase 8 queues follow the same structure** (from RESEARCH.md lines 232-238):
```python
# Phase 8 SigLIP2 backbone comparison queues
# NOTE: skeleton_only is NOT re-run -- it uses no visual features
"phase8_ucf_main": [
    RunSpec("ucf", "clip_only",     42, "configs/clip_only_siglip2.yaml",     "siglip2"),
    RunSpec("ucf", "late_fusion",   42, "configs/late_fusion_siglip2.yaml",   "siglip2"),
    RunSpec("ucf", "gated_fusion",  42, "configs/gated_fusion_siglip2.yaml",  "siglip2"),
],
"phase8_xd_main": [
    RunSpec("xd", "clip_only",     42, "configs/clip_only_xd_siglip2.yaml",     "siglip2"),
    RunSpec("xd", "late_fusion",   42, "configs/late_fusion_xd_siglip2.yaml",   "siglip2"),
    RunSpec("xd", "gated_fusion",  42, "configs/gated_fusion_xd_siglip2.yaml",  "siglip2"),
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

**RunSpec.wandb_tags() pattern** (lines 96-101) -- note Phase 8 runs use `cache_variant="siglip2"` which automatically appears in tags. The `wandb_tags()` method already handles this:
```python
def wandb_tags(self) -> List[str]:
    tags = ["phase4", self.dataset, self.variant, f"s{self.seed}"]
    if self.cache_variant:
        tags.append(self.cache_variant)
    return tags
```
Consider updating the hardcoded `"phase4"` tag to derive from the queue name or add a `phase` field to `RunSpec` for Phase 8. Alternatively, keep `"phase4"` as-is (it is a legacy tag) and rely on the `siglip2` cache_variant tag for filtering.

---

### `scripts/generate_phase8_charts.py` (NEW, utility)

**Analog:** `scripts/generate_phase6_charts.py` (lines 1-60)

**Imports and project setup pattern** (lines 1-36):
```python
#!/usr/bin/env python
"""
Phase 8 SigLIP2 Backbone Comparison -- CLIP vs SigLIP2 Tables/Charts
=====================================================================
Generates backbone comparison tables from results/results-index.csv.

Usage:
    conda activate vcc-main
    python scripts/generate_phase8_charts.py

Output: results/phase8_charts/
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

# --- Project Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

**Style constants pattern** (lines 44-60):
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
    },
)
```

**Core data loading pattern:** Read `results/results-index.csv`, filter by backbone tag (siglip2 vs no siglip2 in cache_variant), pivot into comparison table. This is new logic but the CSV loading pattern follows Phase 6.

---

### `tests/test_extract_siglip2.py` (NEW, test)

**Analog:** `tests/test_models.py` (lines 1-80)

**Imports and setup pattern** (lines 1-9):
```python
"""Phase 8: SigLIP2 extraction output shape and backbone config tests."""
from __future__ import annotations
import torch
import torch.nn as nn
import pytest
import numpy as np
```

**Test function naming pattern** (from test_models.py):
```python
def test_output_shape():
    ...

def test_backbone_config():
    ...
```

**Assertion style pattern** (lines 17-19):
```python
assert out.shape == (2, 32)
assert torch.isfinite(out).all()
```

---

### `tests/test_models.py` (MODIFY: add clip_dim=3072 tests)

**Analog:** self -- existing `test_clip_only_forward()` pattern (lines 40-47):
```python
def test_clip_only_forward():
    torch.manual_seed(0)
    model = CLIPProj()
    clip = torch.randn(2, 32, 1024)
    out = model(clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()
```

**New test follows same pattern with clip_dim=3072:**
```python
def test_clip_dim_3072():
    """Phase 8: CLIPProj with SigLIP2 3072-d input."""
    torch.manual_seed(0)
    model = CLIPProj(clip_dim=3072)
    clip = torch.randn(2, 32, 3072)
    out = model(clip=clip)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
```

**Existing D-06 projection test** (lines 58-63) -- verifies in_features/out_features:
```python
def test_clip_only_projection_layer_d06():
    model = CLIPProj()
    assert isinstance(model.clip_proj, nn.Linear)
    assert model.clip_proj.in_features == 1024
    assert model.clip_proj.out_features == 512
```

New test should verify `in_features=3072` when constructed with `clip_dim=3072`.

---

### `tests/test_run_ablations.py` (MODIFY: add Phase 8 queue assertions)

**Analog:** self -- existing queue definition test (lines 47-78):
```python
def test_queue_definitions():
    assert len(QUEUES["rtfm_gate"]) == 1
    assert QUEUES["rtfm_gate"][0].run_name == "xd_i3d_rtfm_i3d_s42"
    assert len(QUEUES["phase4_main"]) == 4
    assert len(QUEUES["phase4_pooling"]) == 2
    assert len(QUEUES["phase4_seeds"]) == 2
    ...
```

**New assertions follow the same pattern:**
```python
# Phase 8 SigLIP2 queues
assert len(QUEUES["phase8_ucf_main"]) == 3       # clip_only, late, gated (no skeleton_only)
assert len(QUEUES["phase8_xd_main"]) == 3
assert len(QUEUES["phase8_ucf_pooling"]) == 2     # 2person, clip_mean
assert len(QUEUES["phase8_xd_pooling"]) == 2
assert len(QUEUES["phase8_ucf_seeds"]) == 2       # seeds 123, 2024
assert len(QUEUES["phase8_xd_seeds"]) == 2
# run_name spot checks
assert QUEUES["phase8_ucf_main"][2].run_name == "ucf_gated_fusion_siglip2_s42"
assert QUEUES["phase8_xd_seeds"][0].run_name == "xd_gated_fusion_siglip2_s123"
```

**--help queue listing test** (lines 32-44) -- add phase8 queue names to the assertion list:
```python
for q in (..., "phase8_ucf_main", "phase8_xd_main",
          "phase8_ucf_pooling", "phase8_xd_pooling",
          "phase8_ucf_seeds", "phase8_xd_seeds"):
    assert q in combined, f"missing queue {q!r} in --help"
```

---

## Shared Patterns

### Config Template Pattern
**Source:** All existing YAML configs (`configs/*.yaml`)
**Apply to:** All 10 new SigLIP2 YAML configs

Every config follows the same 5-section structure:
```yaml
# configs/{variant}[_{xd}][_{ablation}].yaml
# Comment explaining the config purpose
seed: 42
dataset: ucf|xd

paths:
  skeleton_features: "E:/features/{dataset}/skeleton[_2person]"
  clip_features: "E:/features/{dataset}/{subdir}"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: clip_only|late_fusion|gated_fusion
  [skel_dim: 256|512]
  clip_dim: {dim}
  [proj_dim: 512]
  [shared_dim: 256]
  head_hidden: [128, 32]
  dropout: 0.3
  [alpha: equal]

data:
  T: 32
  batch_size: 16
  num_workers: 4
  pin_memory: true
  [skel_agg: concat]

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
  tags: [phase8, {variant}, {dataset}, ...]
```

### RunSpec Queue Pattern
**Source:** `scripts/run_ablations.py` lines 133-185
**Apply to:** All Phase 8 queue additions

Every queue is a list of `RunSpec(dataset, variant, seed, config_path, cache_variant)` tuples. The `cache_variant` field ("siglip2") is appended to `run_name` and `wandb_tags`. Phase 8 queues mirror Phase 4/4c structure but: (a) skip `skeleton_only`, (b) use `_siglip2` configs, (c) set `cache_variant="siglip2"`.

### Dimension Parameterization Pattern
**Source:** `scripts/extract_clip.py` lines 289-339
**Apply to:** Modified `extract_clip_snippet()`, `extract_video_clip_features()`, `run_extraction()`

All hardcoded dimension values (`512`, `1024`) must be replaced with `embed_dim` (from `BACKBONE_CONFIGS`) and `embed_dim * 2` for mean+max pooling. The pattern is:
```python
embed_dim = cfg["embed_dim"]  # 512 for CLIP, 1536 for SigLIP2
expected_dim = embed_dim if pool == "mean" else embed_dim * 2
```

### Atomic Write Pattern
**Source:** `scripts/extract_clip.py` lines 576-578
**Apply to:** Unchanged -- SigLIP2 extraction uses the same atomic write pattern:
```python
tmp_path = output_dir / f"{video_id}.tmp.npy"
np.save(str(tmp_path), feats)
tmp_path.replace(output_path)
```

### Error Handling Pattern
**Source:** `scripts/extract_clip.py` lines 556-598
**Apply to:** Unchanged -- SigLIP2 extraction uses the same try/except per-video pattern with error log:
```python
try:
    feats = extract_video_clip_features(...)
    # atomic write + assertions
    processed += 1
except Exception as exc:
    failed += 1
    error_msg = f"{video_id}\t{type(exc).__name__}: {exc}"
    logger.error(f"FAILED: {error_msg}")
    with open(error_log_path, "a") as ef:
        ef.write(error_msg + "\n")
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | -- | -- | All files have exact analogs in the existing codebase |

Every file in Phase 8 is either a parameterized variant of an existing file (configs) or a modification to an existing file (extract_clip.py, run_ablations.py). The comparison chart script is the only truly new file, and it follows the established Phase 6 chart generation pattern closely.

## Metadata

**Analog search scope:** `configs/`, `scripts/`, `tests/`, `src/`
**Files scanned:** 20 configs, 19 scripts, 42 test files
**Pattern extraction date:** 2026-05-19
