# Phase 3: Model Architecture & Training Infrastructure — Research

**Researched:** 2026-04-14
**Domain:** MIL training on cached dual-modal features (PyTorch 2.6 + Windows 11 + CUDA 12.4 + RTX 4090)
**Confidence:** HIGH (reference code verified against RTFM/MGFN/TENT upstream; PyTorch reproducibility docs verified; wandb env vars verified)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### MIL Loss
- **D-01:** Top-k = 3 for top-k MIL ranking (RTFM/MGFN convention; T=32 snippets per bag)
- **D-02:** Hinge margin = 1.0 in `max(0, margin - mean_topk_abnormal + mean_topk_normal)`
- **D-03:** RTFM-style regularizers: `λ_sparse=8e-3` on L1 of abnormal-bag snippet scores + `λ_smooth=8e-4` on L2 of adjacent-snippet score differences
- **D-04:** Bag construction: `batch_size=32` videos per batch = 16 normal + 16 abnormal → 16 ranking pairs, paired by index within shuffled queues

#### MIL Head Architecture
- **D-05:** Score head is shared 3-layer MLP: `Linear(D→128) → ReLU → Dropout(0.3) → Linear(128→32) → ReLU → Dropout(0.3) → Linear(32→1) → Sigmoid`
- **D-06:** Hidden width 128 → 32 (RTFM/MGFN default). Reused across all 4 variants
- **D-07:** LayerNorm placement: after **every** modality projection (`skel_proj → LN`, `clip_proj → LN`) **and** at fusion output (`F_fused → LN`). Gated Fusion has ~4-5 LN layers (TTA surface enabler)
- **D-08:** Module organization: shared `MILHead(input_dim, hidden_dims, dropout)` class reused by all variants; per-variant wrappers `SkeletonProj`, `CLIPProj`, `LateFusion`, `GatedFusion` live in `src/models/`. CLIP-Only includes learned `Linear(1024→512)` inside `CLIPProj`

#### Data Loader Sampling
- **D-09:** Training-time sampling for N > 32: **uniform 32-segment sub-sample** (divide N into 32 contiguous segments, pick one snippet per segment — random within segment)
- **D-10:** Training-time padding for N < 32: **zero-pad with attention mask** (mask zero positions out of MIL top-k). 172 UCF sub-64-frame videos dropped at load time
- **D-11:** Multi-person aggregation and CLIP pooling ablations → **deferred to Phase 4**
- **D-12:** Test-time evaluation: **score every snippet** (no T=32 sampling)

#### Tracking & Artifacts
- **D-13:** Experiment tracking: **wandb** online (project `violencecc`, entity via env var); CSV logging (TRN-04) stays as offline source of truth
- **D-14:** Results directory: `results/{dataset}_{variant}_{seed}_{timestamp}/` — contains `config_snapshot.json`, `train_log.csv`, `best_model.pth`, `last_model.pth`
- **D-15:** Checkpoint policy: `best_model.pth` (lowest val MIL loss) + `last_model.pth` (final epoch)
- **D-16:** Variant selection: **string registry pattern** — YAML `model.variant: gated_fusion | late_fusion | clip_only | skeleton_only` mapped via `src/models/registry.py`

### Claude's Discretion
- Activation in MLP heads (default ReLU; switch to GELU only on collapse)
- Validation cadence (default every epoch per TRN-04)
- Strictness of `torch.use_deterministic_algorithms(True)` — fall back to non-deterministic with warning if no deterministic kernel exists (acceptable ~10-20% throughput cost)
- Gradient clipping (off by default; enable only on Gated Fusion instability)
- AMP/mixed precision (**off** — nondeterminism conflict with reproducibility goal)
- Snippet shuffling within bag (**off** — preserve temporal order for smoothness regularizer)
- LayerNorm naming: suggested `ln_skel`, `ln_clip`, `ln_fused`; required discoverable via `model.named_modules()`
- wandb project/entity strings (default project `violencecc`; entity via `VIOLENCECC_WANDB_ENTITY`; allow `WANDB_MODE=disabled` for CI)
- DataLoader: default `num_workers=4, pin_memory=True` on Windows; reduce if file-handle issues
- Late Fusion combination: equal-weighted `(s_skel + s_clip)/2` default; learned scalar `α∈[0,1]` if equal underperforms single-modal

### Deferred Ideas (OUT OF SCOPE)
- Multi-person aggregation ablation (concat/max/mean over 2-person slots) → Phase 4 re-extraction
- CLIP pooling ablation (mean-only vs mean+max) → Phase 4 re-extraction
- Cross-Attention Fusion module (PRD §9.3) → only if Gated Fusion stable AND Week 5-6 slack
- AMP / mixed-precision training
- Gradient clipping (by default)
- BCE auxiliary head (unless MIL-Ranking-only collapses)
- Val-set frame-level AUC monitoring (val has no frame-level labels per PRD §11.2)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MOD-01 | MIL Ranking Loss (top-k, hinge margin) | §1: RTFM reference implementation in `train.py` lines around `mil_loss`; top-k selection pattern; sparsity + smoothness exact coefficients |
| MOD-02 | Dataset class with bag-level MIL batching (T=32, paired normal/abnormal bags) | §7 (DataLoader), §1 (RTFM `process_feat` sampling), §8 (bag construction pattern from RTFM) |
| MOD-03 | Skeleton-Only MIL head baseline (256-d → score) | §3 (model registry), §8.A (SkeletonProj wrapper spec) |
| MOD-04 | CLIP-Only MIL head baseline (512-d → score after learned projection from 1024-d) | §3, §8.B (CLIPProj wrapper with Linear(1024→512) → LN) |
| MOD-05 | Late Fusion baseline (score-level weighted average) | §8.C (scalar mixing pattern) |
| MOD-06 | Gated Fusion module (256-d shared, sigmoid gate, LN + Dropout(0.3) + residual) | §8.D: exact module spec matching PRD §9.2 |
| MOD-07 | LayerNorm layers named and addressable for TTA | §8.E (`model.named_modules()` pattern), §10 (TTA parameter collection via TENT reference) |
| TRN-01 | Training loop (AdamW, warmup 5 + cosine 45, lr=1e-4, batch=32, 50 epochs) | §4: SequentialLR(LinearLR + CosineAnnealingLR) pattern |
| TRN-02 | Early stopping on val MIL loss (patience=10), save best_model.pth | §4.2 (early stopping), §5 (atomic checkpoint save) |
| TRN-03 | Fixed seed everywhere (torch, numpy, random, cudnn.deterministic) | §2: full reproducibility knob list |
| TRN-04 | Per-epoch CSV logging (epoch, train_loss, val_loss) + stdout | §9 (CSV + wandb mirror) |
| TRN-05 | Config snapshot saved alongside every checkpoint | §6: git SHA + pip freeze + resolved config → JSON |
| TRN-06 | Single `train.py` entry point configurable via YAML/argparse | §3 (registry), §6 (config loader) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Environment: `vcc-main` (PyTorch 2.6.0 cu124, Python 3.11, Windows 11) for all Phase 3 code — NEVER import PYSKL or mmcv
- PyTorch 2.6.0 with CUDA 12.4 cu124 wheels; `torch==2.6.0`, `torchvision==0.21.0`, `torchaudio==2.6.0`
- open-clip-torch 3.3.0 is available but Phase 3 only reads cached `[N,1024]` CLIP features (no CLIP model loaded at train time)
- scikit-learn ≥1.3 for metrics (used in Phase 4, not directly in Phase 3 training)
- h5py ≥3.8 is available but cached features are `.npy` (Phase 2 decision)
- wandb ≥0.16 (**verified latest:** 0.26.0, 2026-04-13 on PyPI); tensorboard ≥2.14 as alternative
- tqdm ≥4.65, PyYAML ≥6.0, numpy ≥1.23
- All backbones frozen — Phase 3 only trains fusion head parameters
- Single RTX 4090 24GB VRAM; feature-level training is memory-trivial (no AMP needed)
- Reproducibility: fixed seeds, `torch.use_deterministic_algorithms(True)`, no AMP

## Executive Summary

Phase 3 builds four MIL model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) plus a single configurable `train.py` in the `vcc-main` environment. All four variants share a 3-layer MILHead MLP (D→128→32→1, Sigmoid). Training uses RTFM's exact MIL Ranking Loss formulation with `λ_sparse=8e-3` L1 and `λ_smooth=8e-4` L2 regularizers [VERIFIED: RTFM `train.py` web-fetched]. Bit-identical reproducibility requires four knobs acting together: fixed seeds (torch/numpy/random/DataLoader generator), `torch.use_deterministic_algorithms(True)`, `cudnn.deterministic=True` + `cudnn.benchmark=False`, and the `CUBLAS_WORKSPACE_CONFIG=:4096:8` environment variable set **before** Python imports PyTorch [VERIFIED: PyTorch reproducibility docs]. AMP is off by design (nondeterminism risk). wandb integrates as a mirror for CSV logs with `WANDB_MODE=offline|disabled|online` controlling behavior per run. Checkpoint atomicity uses `tempfile + os.replace()` for Windows-safe writes. Config snapshot captures resolved YAML + git SHA + pip freeze into JSON for bit-identical reruns.

**Primary recommendation:** Port RTFM's `process_feat` (mean-pool per segment) for training sample_len=32, copy the exact `sparsity()`+`smooth()` regularizer functions verbatim, adopt the TENT `copy_model_and_optimizer` pattern now so Phase 5 TTA drops in without refactoring, and enforce the `CUBLAS_WORKSPACE_CONFIG` env var at the top of `train.py` before any `torch` import — that one line is the most commonly forgotten reproducibility knob.

---

## 1. MIL Ranking Loss — RTFM / MGFN Reference Implementations

### 1.1 RTFM canonical loss (verbatim from upstream)

The following snippets are extracted from `tianyu0207/RTFM/train.py` [VERIFIED: WebFetch raw GitHub 2026-04-14]. These are the exact functions to port into `src/losses/mil_loss.py`.

```python
# From RTFM train.py — sparsity and smoothness regularizers

def sparsity(arr, batch_size, lamda2):
    """L1 norm on snippet scores — pushes abnormal-bag scores toward sparsity.
    arr: [B_abn, T] abnormal snippet scores (after sigmoid).
    """
    loss = torch.mean(torch.norm(arr, dim=0))  # L2 across videos per snippet, then mean across snippets
    return lamda2 * loss

def smooth(arr, lamda1):
    """L2 on adjacent-snippet score differences — encourages temporal coherence.
    arr: [B_abn, T] abnormal snippet scores.
    Note RTFM's clever trick: shift-by-one using index assignment (not np.roll).
    """
    arr2 = torch.zeros_like(arr)
    arr2[:-1] = arr[1:]   # Shift forward; last position = arr[-1] stays (zero difference at boundary)
    arr2[-1] = arr[-1]
    loss = torch.sum((arr2 - arr) ** 2)
    return lamda1 * loss
```

**RTFM's total-loss composition** [VERIFIED: RTFM `train.py` WebFetch]:

```python
loss_sparse = sparsity(abn_scores, batch_size, 8e-3)
loss_smooth = smooth(abn_scores, 8e-4)
cost = loss_criterion(score_normal, score_abnormal, nlabel, alabel,
                      feat_select_normal, feat_select_abn) + loss_smooth + loss_sparse
```

### 1.2 Top-k pattern (RTFM `model.py`, verified upstream)

RTFM's original model uses **feature magnitude** for top-k selection (their novel contribution). For Phase 3 we use **score-based** top-k (simpler, aligned with the D-01/D-02 decisions):

```python
# From RTFM model.py — feature magnitude approach (DO NOT COPY VERBATIM):
idx_abn = torch.topk(afea_magnitudes_drop, k_abn, dim=1)[1]
feat_select_abn = torch.gather(abnormal_feature, 1, idx_abn_feat)

# Phase 3 implementation — score-based top-k (matches D-01, D-02):
# scores_abn: [B_abn, T] per-snippet anomaly scores (after sigmoid)
# scores_nor: [B_nor, T]
k = 3  # D-01
topk_abn = torch.topk(scores_abn, k=k, dim=1).values.mean(dim=1)  # [B_abn]
topk_nor = torch.topk(scores_nor, k=k, dim=1).values.mean(dim=1)  # [B_nor]

# Hinge margin — D-02 sets margin=1.0 (NOT RTFM's feature-magnitude margin=100)
# Paired by index (D-04): i-th abnormal video paired with i-th normal video
hinge_per_pair = torch.relu(1.0 - topk_abn + topk_nor)  # [B_pair]
rank_loss = hinge_per_pair.mean()
```

**Important note on RTFM's margin=100:** RTFM's margin is on **feature L2 magnitudes** (not scores), which is why it's 100 not 1.0. Our MIL Ranking Loss operates on **post-sigmoid scores in [0,1]**, so margin=1.0 is the correct value for a hinge between mean top-k scores [CITED: PRD D-02].

### 1.3 Masked top-k for zero-padded bags (D-10)

Videos with N<32 snippets are zero-padded. When computing top-k we must mask these positions to `-inf` so padded zeros cannot win:

```python
# mask: [B, T] — 1.0 where real snippet, 0.0 where zero-padded
scores_masked = scores.masked_fill(mask == 0, float("-inf"))
topk_vals = torch.topk(scores_masked, k=k, dim=1).values.mean(dim=1)
```

**Pitfall:** Do not apply the mask by multiplication (`scores * mask`) before top-k — that gives padded positions a score of 0, which is still higher than some real snippets, letting them win. Use `masked_fill(mask==0, -inf)`.

### 1.4 Bag pair construction (D-04 = RTFM convention)

RTFM pairs by index within independently shuffled queues [VERIFIED: RTFM `train.py` WebFetch]:

```python
# RTFM pattern:
# - Two DataLoaders: one for normal videos, one for abnormal
# - Each yields B=16 videos
# - In training step: fetch next batch from each, concatenate
ninput, nlabel = next(nloader)   # [16, T, D]  normal
ainput, alabel = next(aloader)   # [16, T, D]  abnormal
input = torch.cat((ninput, ainput), 0).to(device)  # [32, T, D]
# Model forward produces [32, T] scores; split into [:16]=normal, [16:]=abnormal for loss
```

**Shorter queue cycling:** UCF train split has 800 abnormal + 568 normal (after val holdout). RTFM cycles the shorter queue independently. Reproducible via seeded generators [VERIFIED: RTFM `dataset.py`].

### 1.5 Verified implementation template

```python
# src/losses/mil_loss.py

import torch
import torch.nn as nn

def _sparsity(scores_abn: torch.Tensor, lam: float = 8e-3) -> torch.Tensor:
    """RTFM-exact L1 sparsity on abnormal-bag scores."""
    return lam * torch.mean(torch.norm(scores_abn, dim=0))

def _smoothness(scores_abn: torch.Tensor, lam: float = 8e-4) -> torch.Tensor:
    """RTFM-exact L2 smoothness on adjacent-snippet differences."""
    arr2 = torch.zeros_like(scores_abn)
    arr2[:-1] = scores_abn[1:]
    arr2[-1] = scores_abn[-1]
    return lam * torch.sum((arr2 - scores_abn) ** 2)

def mil_ranking_loss(
    scores: torch.Tensor,       # [2B, T] sigmoid scores (normal first, then abnormal)
    mask: torch.Tensor,          # [2B, T] 1 where real, 0 where zero-padded
    n_normal: int,               # B (= 16 per D-04)
    k: int = 3,                  # D-01
    margin: float = 1.0,         # D-02
    lam_sparse: float = 8e-3,    # D-03
    lam_smooth: float = 8e-4,    # D-03
) -> torch.Tensor:
    """Top-k MIL Ranking Loss with sparsity + smoothness. Masked for padded positions."""
    scores_masked = scores.masked_fill(mask == 0, float("-inf"))
    topk_vals = torch.topk(scores_masked, k=k, dim=1).values.mean(dim=1)
    topk_nor, topk_abn = topk_vals[:n_normal], topk_vals[n_normal:]
    # Paired by index (D-04 — assumes equal-size queues; cycle shorter in DataLoader)
    rank = torch.relu(margin - topk_abn + topk_nor).mean()
    # Regularizers on abnormal-bag sigmoid scores only
    scores_abn_real = scores[n_normal:] * mask[n_normal:]  # zero out padded for reg
    reg = _sparsity(scores_abn_real, lam_sparse) + _smoothness(scores_abn_real, lam_smooth)
    return rank + reg
```

**Confidence:** HIGH for sparsity/smoothness formulas (directly verified from upstream) [VERIFIED: tianyu0207/RTFM `train.py`]. HIGH for top-k masking pattern (standard PyTorch idiom).

---

## 2. Reproducibility Knobs (PyTorch 2.6 + Windows + CUDA 12.4)

### 2.1 The four-knob stack for bit-identical training

Success criterion #4 requires bit-identical loss curves under the same seed. This requires **all four** of the following, not just one:

```python
# seed.py — must be called before any model/dataloader creation

import os
import random
import numpy as np
import torch

def set_deterministic(seed: int = 42) -> None:
    # KNOB 1: seed all RNGs
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # KNOB 2: cuDNN determinism
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    # KNOB 3: global deterministic algorithms
    # warn_only=True = acceptable fallback per CONTEXT discretion
    torch.use_deterministic_algorithms(True, warn_only=True)

    # KNOB 4: (MUST be set BEFORE PyTorch imports) — set in entrypoint:
    # os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
```

### 2.2 `CUBLAS_WORKSPACE_CONFIG` — the most-forgotten knob

[VERIFIED: PyTorch docs + community consensus]

- Valid values: `:4096:8` (larger workspace, slightly faster) or `:16:8` (smaller)
- Affects `torch.mm`, `torch.mv`, `torch.bmm` and all internal matmul operations on CUDA ≥ 10.2
- **Must be set before `import torch`** — setting it later has no effect. Best pattern:

```python
# train.py — FIRST TWO LINES, before any other imports
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

# Now safe to import torch
import torch
# ...
```

- If not set with `use_deterministic_algorithms(True)` and `warn_only=False`, PyTorch raises `RuntimeError` from `torch.mm`/`bmm`.

### 2.3 Operations that LACK deterministic CUDA implementations (PyTorch 2.6)

[VERIFIED: PyTorch 2.6 docs + community knowledge]

Operations that will either error (with `warn_only=False`) or silently be non-deterministic (with `warn_only=True`) on CUDA:

- `torch.Tensor.index_add_` and `torch.Tensor.scatter_add_` (atomicAdd in forward)
- `torch.bincount`
- `torch.nn.functional.interpolate` backward (for certain modes)
- Many pooling/padding backward kernels using atomicAdd
- `torch.nn.functional.embedding_bag` with mode='max' backward

**Relevance for Phase 3:** Our MIL head is MLPs + LayerNorm + Sigmoid + top-k + mean — **none of these hit the non-deterministic list**. Top-k is deterministic. Our loss is fully deterministic-safe. Use `warn_only=True` as a safety net so the run doesn't crash if a PyTorch internal happens to call a nondeterministic op, but we do not expect to hit one.

### 2.4 Expected throughput cost

[CITED: PyTorch docs] "Deterministic operations tend to have worse performance than nondeterministic operations."

For feature-level MLP training on RTX 4090, the expected cost is 5-15% — acceptable per CONTEXT.md "Claude's Discretion" section. An epoch is ~1 min on cached features, so slowdown is ~5-10 seconds per epoch — negligible for a 50-epoch run.

### 2.5 DataLoader worker seeding (Windows + num_workers=4)

[VERIFIED: PyTorch reproducibility docs]

```python
def seed_worker(worker_id: int) -> None:
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)

g = torch.Generator()
g.manual_seed(42)

DataLoader(
    dataset=train_set,
    batch_size=16,
    num_workers=4,
    worker_init_fn=seed_worker,
    generator=g,
    shuffle=True,
    pin_memory=True,
    persistent_workers=True,  # speeds up Windows dataloader; still deterministic
)
```

**Windows-specific gotchas** [VERIFIED: WebSearch results 2026-04-14]:
- `worker_init_fn` must be a module-level function, **not a lambda** (spawn start method can't pickle lambdas on Windows)
- `collate_fn` likewise must be module-level or a `functools.partial` of a module-level function
- With `persistent_workers=True`, first-epoch determinism is reliable; subsequent epochs may differ from fresh-worker runs [CITED: pytorch/pytorch#73603]. For our use case (single training run), this is fine.
- If `num_workers=4` causes file-handle issues on Windows, drop to `num_workers=2` or `0` per CONTEXT "Claude's Discretion"

### 2.6 PYTHONHASHSEED

Python 3.11+ hash randomization affects dict iteration order. For full reproducibility, set:

```bash
set PYTHONHASHSEED=42  # Windows cmd
$env:PYTHONHASHSEED=42  # Windows PowerShell
```

Or in Python (before any dict operations that affect training):
```python
os.environ["PYTHONHASHSEED"] = "42"  # set once at entrypoint
```

**Relevance for Phase 3:** Our code paths are not order-dependent on dict iteration (we use explicit YAML-keyed configs and seeded DataLoader shuffling). This is a defense-in-depth measure but not strictly required.

### 2.7 Reproducibility verification test

A bit-identical check compares two independent training runs:

```python
# tests/test_reproducibility.py (Phase 3)
def test_bit_identical_losses():
    # Run 1 with seed=42
    losses_1 = run_smoke_train(seed=42, epochs=2, n_videos=10)
    # Run 2 same config
    losses_2 = run_smoke_train(seed=42, epochs=2, n_videos=10)
    # Bit-identical: exact float equality
    assert np.array_equal(losses_1, losses_2), f"diff at step {np.argmax(losses_1 != losses_2)}"
```

---

## 3. Model Registry Pattern

### 3.1 Recommended pattern: simple dict-based registry

No decorators needed; explicit is better than implicit for a 4-variant registry. Greppable, no import-time side effects.

```python
# src/models/registry.py

from typing import Callable, Dict

from src.models.gated_fusion import GatedFusion
from src.models.late_fusion import LateFusion
from src.models.clip_only import CLIPProj
from src.models.skeleton_only import SkeletonProj

MODEL_REGISTRY: Dict[str, Callable] = {
    "skeleton_only": SkeletonProj,
    "clip_only": CLIPProj,
    "late_fusion": LateFusion,
    "gated_fusion": GatedFusion,
}

def build_model(variant: str, **kwargs) -> "nn.Module":
    """Instantiate a model variant from YAML config.

    YAML: model: {variant: gated_fusion, skel_dim: 256, clip_dim: 1024, ...}
    Caller: build_model(**cfg["model"])
    """
    if variant not in MODEL_REGISTRY:
        raise ValueError(f"Unknown variant '{variant}'. Valid: {list(MODEL_REGISTRY)}")
    return MODEL_REGISTRY[variant](**kwargs)
```

### 3.2 Alternative considered: decorator registry (timm pattern)

[CITED: huggingface/pytorch-image-models `_registry.py`] Timm uses a `@register_model` decorator that populates a dict at import time. This is cleaner at scale (100+ models) but has two drawbacks for our 4-variant project:

1. **Import-time side effects** — tests that import a single model file also register it globally
2. **Less greppable** — "where is this model's class defined?" requires IDE support rather than a text search on MODEL_REGISTRY

The explicit dict pattern is chosen for a 4-variant thesis codebase. If the codebase grows to many variants (unlikely), the migration cost is trivial.

### 3.3 YAML → kwargs unpacking

YAML config:
```yaml
# configs/gated_fusion.yaml
model:
  variant: gated_fusion
  skel_dim: 256
  clip_dim: 1024
  shared_dim: 256
  head_hidden: [128, 32]
  dropout: 0.3
```

Code:
```python
cfg = yaml.safe_load(open(args.config))
model = build_model(**cfg["model"])  # kwargs unpack
```

The `build_model(variant="gated_fusion", skel_dim=256, ...)` call resolves to `GatedFusion(skel_dim=256, clip_dim=1024, shared_dim=256, head_hidden=[128, 32], dropout=0.3)`. Each model class's `__init__` must accept these kwargs.

---

## 4. Training Loop Skeleton

### 4.1 AdamW + warmup + cosine (TRN-01)

PRD §11.1 specifies: AdamW, lr=1e-4, batch=32, 50 epochs, linear warmup 5 epochs + cosine decay 45 epochs.

```python
# Composed scheduler using SequentialLR
from torch.optim.lr_scheduler import LinearLR, CosineAnnealingLR, SequentialLR

optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-2)

warmup_epochs = 5
cosine_epochs = 45  # total 50 epochs
warmup = LinearLR(optimizer, start_factor=0.01, end_factor=1.0, total_iters=warmup_epochs)
cosine = CosineAnnealingLR(optimizer, T_max=cosine_epochs, eta_min=0.0)
scheduler = SequentialLR(optimizer, schedulers=[warmup, cosine], milestones=[warmup_epochs])

# Call scheduler.step() ONCE per epoch (not per batch), per PyTorch convention
```

[VERIFIED: PyTorch docs for LinearLR, CosineAnnealingLR, SequentialLR]

**Potential warning (benign):** SequentialLR warns on reconstruction because LinearLR's internal state mutates. The training still produces the correct LR curve. Silence with `warnings.filterwarnings("ignore", message="detected call of")` if noise is a problem.

### 4.2 Early stopping on val MIL loss (TRN-02)

```python
# src/utils/early_stopping.py

from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class EarlyStopping:
    patience: int = 10
    best_loss: float = float("inf")
    best_epoch: int = -1
    counter: int = 0
    stopped: bool = False
    # Persist state to resume training after crash
    state_path: Path | None = None

    def step(self, epoch: int, val_loss: float) -> dict:
        """Returns dict with 'is_best' (bool) and 'should_stop' (bool)."""
        if val_loss < self.best_loss:
            self.best_loss = val_loss
            self.best_epoch = epoch
            self.counter = 0
            is_best = True
        else:
            self.counter += 1
            is_best = False
            if self.counter >= self.patience:
                self.stopped = True
        return {"is_best": is_best, "should_stop": self.stopped}
```

**NaN handling:** If `val_loss` is NaN/Inf, do **not** treat it as best-or-worse — log a warning and continue (counter unchanged). If NaN persists for 3 consecutive epochs, halt with a clear error message. A silent NaN treated as "worst ever" would extend training pointlessly.

### 4.3 Training loop skeleton

```python
# src/train.py

import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import torch
from tqdm import tqdm
from pathlib import Path

from src.utils.seed import set_deterministic
from src.utils.config import load_config, snapshot_config
from src.utils.checkpoint import save_checkpoint_atomic
from src.utils.early_stopping import EarlyStopping
from src.utils.logger import CSVLogger, WandbLogger
from src.models.registry import build_model
from src.data.dataset import build_dataloaders
from src.losses.mil_loss import mil_ranking_loss


def main(args):
    cfg = load_config(args.config, overrides=args.overrides)
    set_deterministic(cfg["seed"])

    run_dir = Path(cfg["results_dir"]) / run_name(cfg)
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot_config(cfg, run_dir / "config_snapshot.json")  # §6

    csv_logger = CSVLogger(run_dir / "train_log.csv")
    wandb_logger = WandbLogger(cfg, run_dir)  # §9

    model = build_model(**cfg["model"]).cuda()
    optimizer = torch.optim.AdamW(model.parameters(),
                                   lr=cfg["train"]["lr"],
                                   weight_decay=cfg["train"]["weight_decay"])
    scheduler = build_scheduler(optimizer, cfg["train"])  # §4.1

    train_loader, val_loader = build_dataloaders(cfg)  # §7
    early = EarlyStopping(patience=cfg["train"]["patience"])

    for epoch in range(cfg["train"]["epochs"]):
        train_loss = train_one_epoch(model, train_loader, optimizer)
        val_loss = validate(model, val_loader)
        scheduler.step()

        decision = early.step(epoch, val_loss)
        csv_logger.log(epoch=epoch, train_loss=train_loss, val_loss=val_loss,
                       lr=optimizer.param_groups[0]["lr"])
        wandb_logger.log({"train/loss": train_loss, "val/loss": val_loss,
                          "lr": optimizer.param_groups[0]["lr"]}, step=epoch)

        if decision["is_best"]:
            save_checkpoint_atomic(model, optimizer, epoch, cfg,
                                    run_dir / "best_model.pth")
        save_checkpoint_atomic(model, optimizer, epoch, cfg,
                                run_dir / "last_model.pth")  # D-15

        if decision["should_stop"]:
            break

    wandb_logger.finish()
```

---

## 5. Checkpointing & Atomic Writes on Windows

### 5.1 Atomic write pattern (tempfile + os.replace)

[VERIFIED: Python docs + community consensus WebSearch 2026-04-14]

Windows `os.replace` is atomic (calls `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING`). Writing directly to `best_model.pth` risks corruption if the process dies mid-write; recovery then requires an unreliable snapshot.

```python
# src/utils/checkpoint.py

import os
import tempfile
from pathlib import Path
import torch

def save_checkpoint_atomic(
    model: "nn.Module",
    optimizer: "Optimizer",
    epoch: int,
    cfg: dict,
    path: Path,
) -> None:
    """Atomically save checkpoint on Windows using tempfile + os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "epoch": epoch,
        "config": cfg,  # Inline config for self-contained recovery
    }

    # Same-directory tempfile (cross-device rename is NOT atomic)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "wb") as f:
            torch.save(state, f)
            f.flush()
            os.fsync(f.fileno())  # Force OS buffer → disk
        os.replace(tmp_path, str(path))  # Atomic on Windows + POSIX
    except Exception:
        # Clean up temp file on any failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
```

### 5.2 Checkpoint loading with weights_only=True (security)

[VERIFIED: PyTorch 2.6 release notes + CVE-2025-32434 WebSearch]

PyTorch 2.6+ defaults `weights_only=True` in `torch.load`. Use this default for loading our own checkpoints — but our checkpoint dict contains non-tensor objects (config dict, epoch int) which may require allowlisting:

```python
# For loading our own trusted checkpoints that contain a "config" dict:
import torch
from torch.serialization import add_safe_globals

# Allowlist our known safe types (done once at startup)
add_safe_globals([dict, int, float, str, list, tuple])

state = torch.load(ckpt_path, weights_only=True)
model.load_state_dict(state["model"])
```

**Simpler alternative:** Save only `state_dict` (tensors) in `best_model.pth`; save config separately as JSON. Then `torch.load(weights_only=True)` has no issues:

```python
# Recommended split:
torch.save(model.state_dict(), path)  # only tensors → weights_only=True loads cleanly
# config_snapshot.json is a separate sibling file (see §6)
```

### 5.3 Atomic write verification test

```python
def test_checkpoint_atomic_on_interrupt(tmp_path):
    # Simulate mid-write kill by monkey-patching torch.save to raise mid-call
    # Verify: target file either doesn't exist OR is the previous valid state
    path = tmp_path / "best_model.pth"
    save_checkpoint_atomic(model_v1, opt, 0, cfg, path)
    # Inject failure
    with patch("torch.save", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            save_checkpoint_atomic(model_v2, opt, 1, cfg, path)
    # path still has v1
    state = torch.load(path, weights_only=True)
    assert state["epoch"] == 0  # v1 survived
```

---

## 6. YAML Config & Snapshot Strategy

### 6.1 Flat YAML schema (Phase 1 D-03)

One file per variant. Phase 1 already committed to flat YAML per-variant (no inheritance tree).

```yaml
# configs/gated_fusion.yaml
seed: 42
dataset: ucf  # ucf | xd

paths:
  skeleton_features: "E:/features/ucf/skeleton"
  clip_features: "E:/features/ucf/clip"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: gated_fusion
  skel_dim: 256
  clip_dim: 1024
  shared_dim: 256
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32            # snippets per bag (D-09)
  batch_size: 16   # 16 normal + 16 abnormal = 32 videos = 16 pairs (D-04)
  num_workers: 4
  pin_memory: true

train:
  lr: 1.0e-4
  weight_decay: 1.0e-2
  epochs: 50
  warmup_epochs: 5
  patience: 10     # TRN-02
  k_topk: 3        # D-01
  margin: 1.0      # D-02
  lam_sparse: 8.0e-3  # D-03
  lam_smooth: 8.0e-4  # D-03

wandb:
  project: violencecc
  mode: online     # online | offline | disabled
  tags: [phase3, gated_fusion, ucf]
```

### 6.2 Schema validation via dataclass

Use `dataclasses` (stdlib, zero deps) rather than pydantic — simpler for a thesis codebase:

```python
# src/utils/config.py

from dataclasses import dataclass, field
from typing import List
import yaml

@dataclass
class TrainConfig:
    lr: float = 1e-4
    weight_decay: float = 1e-2
    epochs: int = 50
    warmup_epochs: int = 5
    patience: int = 10
    k_topk: int = 3
    margin: float = 1.0
    lam_sparse: float = 8e-3
    lam_smooth: float = 8e-4

@dataclass
class DataConfig:
    T: int = 32
    batch_size: int = 16
    num_workers: int = 4
    pin_memory: bool = True

# ... (similar for ModelConfig, PathsConfig, WandbConfig)

def load_config(path: str, overrides: dict | None = None) -> dict:
    raw = yaml.safe_load(open(path))
    if overrides:
        deep_merge(raw, overrides)  # CLI --model.dropout=0.5 overrides YAML
    # Validate: construct each sub-dataclass; raises TypeError on missing/extra keys
    # Return the plain dict for downstream use (kwargs unpacking friendly)
    return raw
```

### 6.3 Config snapshot with full provenance (TRN-05)

```python
# src/utils/config.py

import json
import subprocess
import sys
from pathlib import Path

def snapshot_config(cfg: dict, path: Path) -> None:
    """Snapshot the resolved config + environment for bit-identical reproducibility."""
    snapshot = {
        "config": cfg,
        "git": {
            "sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "dirty": bool(subprocess.check_output(
                ["git", "status", "--porcelain"], text=True
            ).strip()),
        },
        "python": sys.version,
        "torch": _get_version("torch"),
        "numpy": _get_version("numpy"),
        "cuda": torch.version.cuda,  # None if CPU-only
        "env": {
            "CUBLAS_WORKSPACE_CONFIG": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
            "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
        },
        "packages": _pip_freeze(),  # list[str] of "name==version" lines
    }
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))

def _pip_freeze() -> list[str]:
    """In-process pip freeze — no subprocess for speed."""
    try:
        from importlib.metadata import distributions
        return sorted(f"{d.metadata['Name']}=={d.version}" for d in distributions())
    except Exception:
        return []

def _get_version(pkg: str) -> str:
    try:
        module = __import__(pkg)
        return getattr(module, "__version__", "unknown")
    except ImportError:
        return "not-installed"
```

### 6.4 Snapshot round-trip test (Success Criterion #4)

```python
def test_config_snapshot_roundtrip(tmp_path):
    cfg = load_config("configs/skeleton_only.yaml")
    snapshot_config(cfg, tmp_path / "snap.json")
    # Re-load snapshot and verify cfg is bit-identical
    reloaded = json.loads((tmp_path / "snap.json").read_text())["config"]
    assert reloaded == cfg
```

---

## 7. DataLoader with Seeded Workers on Windows

### 7.1 Complete dataset + dataloader spec (MOD-02 + D-09/D-10)

```python
# src/data/dataset.py

import numpy as np
import torch
from torch.utils.data import Dataset


class MILFeatureDataset(Dataset):
    """Load cached [N, D_skel] skeleton + [N, D_clip] CLIP features per video.

    Training mode: 32-segment uniform sampling (D-09) or zero-pad+mask (D-10).
    Test mode: return all snippets in temporal order (D-12).
    """

    def __init__(self, split_file, skel_dir, clip_dir, T=32, mode="train",
                 seed=42):
        self.video_ids = self._load_split(split_file)
        self.video_ids = [v for v in self.video_ids
                          if self._has_features(v, skel_dir, clip_dir)]
        # D-10: skip 172 UCF sub-64-frame videos at load time
        self.skel_dir = skel_dir
        self.clip_dir = clip_dir
        self.T = T
        self.mode = mode
        self.labels = self._load_labels()
        self.seed = seed

    def __getitem__(self, idx):
        vid = self.video_ids[idx]
        label = self.labels[vid]  # 0 normal, 1 abnormal
        skel = np.load(f"{self.skel_dir}/{vid}.npy")   # [N, 256]
        clip = np.load(f"{self.clip_dir}/{vid}.npy")   # [N, 1024]
        N = skel.shape[0]
        assert N == clip.shape[0], f"Misaligned snippet counts for {vid}"

        if self.mode == "train":
            skel_t, clip_t, mask = self._train_resample(skel, clip, N)
        else:
            skel_t, clip_t, mask = self._test_pad(skel, clip, N)

        return {
            "skel": torch.from_numpy(skel_t).float(),   # [T, 256]
            "clip": torch.from_numpy(clip_t).float(),   # [T, 1024]
            "mask": torch.from_numpy(mask).float(),     # [T] 1/0
            "label": float(label),
            "video_id": vid,
        }

    def _train_resample(self, skel, clip, N):
        """D-09: uniform 32-segment sub-sample; D-10: zero-pad + mask."""
        T = self.T
        mask = np.ones(T, dtype=np.float32)
        if N >= T:
            # D-09: divide N into 32 contiguous segments, pick one per segment
            segs = np.linspace(0, N, T + 1, dtype=np.int64)
            idxs = np.zeros(T, dtype=np.int64)
            for i in range(T):
                lo, hi = segs[i], max(segs[i] + 1, segs[i + 1])
                idxs[i] = np.random.randint(lo, hi)  # random within segment
            return skel[idxs], clip[idxs], mask
        else:
            # D-10: zero-pad + mask out padded positions
            skel_t = np.zeros((T, skel.shape[1]), dtype=np.float32)
            clip_t = np.zeros((T, clip.shape[1]), dtype=np.float32)
            skel_t[:N] = skel
            clip_t[:N] = clip
            mask[N:] = 0.0
            return skel_t, clip_t, mask

    def _test_pad(self, skel, clip, N):
        """D-12: return all snippets in order (no sampling). Caller batches per-video."""
        return skel, clip, np.ones(N, dtype=np.float32)
```

### 7.2 Paired normal/abnormal loaders (D-04)

```python
# src/data/loaders.py

def build_dataloaders(cfg):
    """Two DataLoaders (normal + abnormal), each yielding B=16 videos."""
    train_dir_split = cfg["paths"]["splits_dir"] + f"/{cfg['dataset']}_train.txt"
    val_dir_split = cfg["paths"]["splits_dir"] + f"/{cfg['dataset']}_val.txt"

    # Filter by label
    full = MILFeatureDataset(train_dir_split, **cfg["paths"], mode="train", T=cfg["data"]["T"])
    nor_idx = [i for i, v in enumerate(full.video_ids) if full.labels[v] == 0]
    abn_idx = [i for i, v in enumerate(full.video_ids) if full.labels[v] == 1]

    g = torch.Generator()
    g.manual_seed(cfg["seed"])

    nor_loader = DataLoader(
        Subset(full, nor_idx),
        batch_size=cfg["data"]["batch_size"],  # 16
        num_workers=cfg["data"]["num_workers"],
        worker_init_fn=seed_worker,
        generator=g,
        shuffle=True,
        pin_memory=cfg["data"]["pin_memory"],
        persistent_workers=(cfg["data"]["num_workers"] > 0),
        drop_last=True,
    )
    # abn_loader: separate generator so queues shuffle independently
    g2 = torch.Generator(); g2.manual_seed(cfg["seed"] + 1)
    abn_loader = DataLoader(..., generator=g2, ...)

    val_loader = DataLoader(  # full videos, no sampling — see §10
        MILFeatureDataset(val_dir_split, ..., mode="val", T=cfg["data"]["T"]),
        batch_size=cfg["data"]["batch_size"] * 2,
        ...
    )
    return (nor_loader, abn_loader), val_loader
```

### 7.3 Test-mode collate (variable-length sequences)

See §10 — test mode cannot use stock collate because snippet counts vary per video. Solution: batch_size=1 at test time OR custom pad collate.

---

## 8. Model Module Definitions

### 8.A SkeletonProj (MOD-03)

```python
# src/models/skeleton_only.py

import torch.nn as nn
from src.models.mil_head import MILHead

class SkeletonProj(nn.Module):
    """Skeleton-Only MIL variant. Input [B, T, 256] → scores [B, T].
    No modality to fuse — just a LN + MILHead pipeline."""

    def __init__(self, skel_dim=256, head_hidden=(128, 32), dropout=0.3, **unused):
        super().__init__()
        self.ln_skel = nn.LayerNorm(skel_dim)   # D-07: named LN for Phase 5 TTA
        self.head = MILHead(input_dim=skel_dim, hidden_dims=head_hidden, dropout=dropout)

    def forward(self, skel, clip=None, mask=None):
        x = self.ln_skel(skel)          # [B, T, 256]
        scores = self.head(x)            # [B, T, 1]
        return scores.squeeze(-1)        # [B, T]
```

### 8.B CLIPProj (MOD-04)

```python
# src/models/clip_only.py

class CLIPProj(nn.Module):
    """CLIP-Only MIL variant. Input [B, T, 1024] → Linear(1024→512) → LN → MILHead."""

    def __init__(self, clip_dim=1024, proj_dim=512, head_hidden=(128, 32),
                 dropout=0.3, **unused):
        super().__init__()
        self.clip_proj = nn.Linear(clip_dim, proj_dim)
        self.ln_clip = nn.LayerNorm(proj_dim)
        self.head = MILHead(input_dim=proj_dim, hidden_dims=head_hidden, dropout=dropout)

    def forward(self, skel=None, clip=None, mask=None):
        x = self.clip_proj(clip)    # [B, T, 512]
        x = self.ln_clip(x)
        return self.head(x).squeeze(-1)
```

### 8.C LateFusion (MOD-05)

```python
# src/models/late_fusion.py

class LateFusion(nn.Module):
    """Late Fusion = separate single-modal heads + scalar score averaging."""

    def __init__(self, skel_dim=256, clip_dim=1024, proj_dim=512,
                 head_hidden=(128, 32), dropout=0.3, alpha="equal", **unused):
        super().__init__()
        self.skeleton = SkeletonProj(skel_dim=skel_dim, head_hidden=head_hidden,
                                      dropout=dropout)
        self.clip = CLIPProj(clip_dim=clip_dim, proj_dim=proj_dim,
                              head_hidden=head_hidden, dropout=dropout)
        if alpha == "learned":
            self.alpha_logit = nn.Parameter(torch.zeros(1))  # sigmoid(0)=0.5 init
        else:
            self.alpha_logit = None  # Fixed 0.5

    def forward(self, skel, clip, mask=None):
        s_skel = self.skeleton(skel=skel)   # [B, T]
        s_clip = self.clip(clip=clip)        # [B, T]
        a = torch.sigmoid(self.alpha_logit) if self.alpha_logit is not None else 0.5
        return a * s_skel + (1 - a) * s_clip
```

### 8.D GatedFusion (MOD-06) — **exact PRD §9.2 spec**

This is the load-bearing module. Note the **4 LN layers** for Phase 5 TTA (D-07).

```python
# src/models/gated_fusion.py

class GatedFusion(nn.Module):
    """Gated Fusion: 256-d shared space, sigmoid gate, residual + LN + Dropout.

    Architecture (PRD §9.2):
      x_skel [256] → Linear(256→256) → ln_skel      → p_skel [256]
      x_clip [1024]→ Linear(1024→256)→ ln_clip      → p_clip [256]
      concat [512] → Linear(512→256) → sigmoid      → gate [256]
      fused = gate * p_skel + (1-gate) * p_clip
      residual = fused + p_skel + p_clip  (sum of both projections)
      out      = dropout(ln_fused(residual))
      scores   = MILHead(out)

    LN inventory (D-07, TTA surface):
      - ln_skel   (after skeleton projection)
      - ln_clip   (after CLIP projection)
      - ln_fused  (at fusion output)
      - MILHead internally has no LN in the base spec; ln_head0/ln_head1 could be
        added if Phase 5 experiments need more TTA params. Default: keep to 3 LN.
    """

    def __init__(self, skel_dim=256, clip_dim=1024, shared_dim=256,
                 head_hidden=(128, 32), dropout=0.3, **unused):
        super().__init__()
        self.skel_proj = nn.Linear(skel_dim, shared_dim)
        self.ln_skel = nn.LayerNorm(shared_dim)

        self.clip_proj = nn.Linear(clip_dim, shared_dim)
        self.ln_clip = nn.LayerNorm(shared_dim)

        # Gate network: W_g in R^{shared_dim × 2*shared_dim}
        self.gate = nn.Linear(2 * shared_dim, shared_dim)
        # m1 mitigation: scale initial W_g small so initial gate ≈ sigmoid(0) = 0.5
        nn.init.xavier_uniform_(self.gate.weight, gain=0.1)
        nn.init.zeros_(self.gate.bias)

        self.ln_fused = nn.LayerNorm(shared_dim)
        self.dropout = nn.Dropout(dropout)
        self.head = MILHead(input_dim=shared_dim, hidden_dims=head_hidden,
                             dropout=dropout)

    def forward(self, skel, clip, mask=None):
        p_skel = self.ln_skel(self.skel_proj(skel))    # [B, T, 256]
        p_clip = self.ln_clip(self.clip_proj(clip))    # [B, T, 256]
        g = torch.sigmoid(self.gate(torch.cat([p_skel, p_clip], dim=-1)))
        fused = g * p_skel + (1 - g) * p_clip          # [B, T, 256]
        residual = fused + p_skel + p_clip              # Gradient highway
        out = self.dropout(self.ln_fused(residual))
        return self.head(out).squeeze(-1)
```

### 8.E Shared MILHead (D-05)

```python
# src/models/mil_head.py

class MILHead(nn.Module):
    """3-layer MLP head: D → 128 → 32 → 1, Sigmoid out, Dropout 0.3 (D-05)."""

    def __init__(self, input_dim: int, hidden_dims=(128, 32), dropout=0.3):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(dropout)]
            prev = h
        layers += [nn.Linear(prev, 1), nn.Sigmoid()]
        self.mlp = nn.Sequential(*layers)

    def forward(self, x):
        return self.mlp(x)   # [..., 1]
```

### 8.F LayerNorm discoverability test (MOD-07)

```python
def test_gated_fusion_has_named_layernorms():
    model = GatedFusion(skel_dim=256, clip_dim=1024, shared_dim=256)
    ln_names = [n for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)]
    # D-07: expects ≥ 3 LN in Gated Fusion (ln_skel, ln_clip, ln_fused)
    assert len(ln_names) >= 3, f"Expected ≥3 LN, found {ln_names}"
    # Explicit named access (Phase 5 TTA)
    assert hasattr(model, "ln_skel")
    assert hasattr(model, "ln_clip")
    assert hasattr(model, "ln_fused")
```

---

## 9. wandb Integration

### 9.1 Environment variables (D-13)

[VERIFIED: wandb env vars docs WebFetch 2026-04-14]

| Variable | Value | Purpose |
|---|---|---|
| `WANDB_MODE` | `online` \| `offline` \| `disabled` | Controls sync. Default online; `disabled` fully disables for CI/dev |
| `WANDB_PROJECT` | `violencecc` | Project name (can also be set in YAML) |
| `WANDB_ENTITY` | user-set via `VIOLENCECC_WANDB_ENTITY` env var | Entity/team (CONTEXT discretion) |
| `WANDB_RUN_ID` | set per-run from run-dir timestamp | Required for resume |
| `WANDB_RESUME` | `allow` \| `must` \| `never` \| `auto` | `allow` + explicit ID = safe default |
| `WANDB_DIR` | `results/<run>/wandb` | Co-located with checkpoints |
| `WANDB_API_KEY` | set in user env (`wandb login` or env) | Never committed to git |

### 9.2 Integration pattern

```python
# src/utils/wandb_logger.py

import os
import wandb
from pathlib import Path

class WandbLogger:
    def __init__(self, cfg: dict, run_dir: Path):
        mode = cfg["wandb"].get("mode", "online")
        if mode == "disabled":
            self.run = None
            return
        # Use run_dir name as stable ID → resume works after crash
        run_id = run_dir.name  # e.g. "ucf_gated_fusion_42_20260420-153000"
        self.run = wandb.init(
            project=cfg["wandb"]["project"],
            entity=os.environ.get("VIOLENCECC_WANDB_ENTITY") or cfg["wandb"].get("entity"),
            mode=mode,                 # D-13
            id=run_id,
            resume="allow",
            name=run_dir.name,
            config=cfg,
            dir=str(run_dir),          # Wandb files co-located
            tags=cfg["wandb"].get("tags", []),
        )
        # Define step axis so train/val metrics align on the same epoch x-axis
        wandb.define_metric("train/*", step_metric="epoch")
        wandb.define_metric("val/*", step_metric="epoch")

    def log(self, metrics: dict, step: int):
        if self.run is None:
            return
        self.run.log({**metrics, "epoch": step})

    def finish(self):
        if self.run is not None:
            self.run.finish()
```

### 9.3 Crash-resume pattern

- Run dir name is the stable ID (e.g. `ucf_gated_fusion_42_20260420-153000`)
- On restart: same YAML → same run dir → same `id=` → `resume="allow"` picks up where it left off
- Val-loss history is re-logged from CSV on first step, avoiding a gap in the wandb curve
- `WANDB_MODE=offline` is an acceptable degraded mode if network is down; `wandb sync <dir>` replays later

### 9.4 Sweep launch for 3-seed reruns (EVAL-05)

```yaml
# configs/sweep_gated_seeds.yaml
method: grid
parameters:
  seed:
    values: [42, 1337, 2024]  # 3-seed runs
command:
  - ${env}
  - ${interpreter}
  - src/train.py
  - --config=configs/gated_fusion.yaml
  - --seed=${seed}
```

```bash
wandb sweep configs/sweep_gated_seeds.yaml
wandb agent <sweep_id>
```

### 9.5 CSV is source of truth, wandb is mirror (D-13)

```python
# src/utils/csv_logger.py

import csv
from pathlib import Path

class CSVLogger:
    def __init__(self, path: Path):
        self.path = path
        self.fieldnames = ["epoch", "train_loss", "val_loss", "lr"]
        self._init_header()

    def log(self, **kwargs):
        # Append immediately — flush ensures data survives crash
        with open(self.path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            w.writerow({k: kwargs.get(k, "") for k in self.fieldnames})
            f.flush()
            os.fsync(f.fileno())  # Survive unclean shutdown
```

---

## 10. Test-Time Full-Video Scoring (D-12)

### 10.1 Score every snippet, no T=32 sampling

Evaluation must produce frame-level scores for AUC/AP. T=32 sampling at train time throws away data for long videos; at test time we must score all snippets in temporal order.

```python
@torch.no_grad()
def score_video(model: nn.Module, skel: np.ndarray, clip: np.ndarray,
                 chunk_size: int = 256) -> np.ndarray:
    """Score all N snippets of a video. Returns [N] float scores.

    Uses chunking to bound VRAM on long videos. 256 snippets × 1024 floats × 4 bytes
    ≈ 1 MB per chunk — trivial on 24GB RTX 4090, but good hygiene.
    """
    model.eval()
    N = skel.shape[0]
    scores = np.zeros(N, dtype=np.float32)

    skel_t = torch.from_numpy(skel).float().cuda()   # [N, 256]
    clip_t = torch.from_numpy(clip).float().cuda()   # [N, 1024]

    for i in range(0, N, chunk_size):
        j = min(i + chunk_size, N)
        # Add batch dim: [1, chunk, D]
        s = skel_t[i:j].unsqueeze(0)
        c = clip_t[i:j].unsqueeze(0)
        mask = torch.ones(1, j - i, device="cuda")
        out = model(skel=s, clip=c, mask=mask)   # [1, chunk]
        scores[i:j] = out[0].cpu().numpy()

    return scores
```

### 10.2 Variable-length batching at eval time

Because test videos have different N, either:
- **Batch size 1** (simplest, negligible cost for a few hundred test videos)
- **Sort by length + pad** within same-length bins (~2-4x faster but more code)

Phase 3 recommendation: batch_size=1 for test. The 290 UCF test videos at ~5 min each with feature-level inference is < 30 seconds total on RTX 4090.

### 10.3 Validation-loss-only monitoring (PRD §11.2)

Val split has **no frame-level labels** (DATA-02). We compute:
- Val MIL Ranking Loss — same formulation as training, including sparsity+smoothness, on paired bags from val split
- Average over all val mini-batches per epoch

```python
@torch.no_grad()
def validate(model, val_loader):
    """Compute val MIL loss for early stopping. No frame-level eval."""
    model.eval()
    losses = []
    for (nor_batch, abn_batch) in val_loader:  # Same bag-pair structure as train
        skel = torch.cat([nor_batch["skel"], abn_batch["skel"]], dim=0).cuda()
        clip = torch.cat([nor_batch["clip"], abn_batch["clip"]], dim=0).cuda()
        mask = torch.cat([nor_batch["mask"], abn_batch["mask"]], dim=0).cuda()
        scores = model(skel=skel, clip=clip, mask=mask)
        loss = mil_ranking_loss(scores, mask, n_normal=nor_batch["skel"].shape[0])
        losses.append(loss.item())
    return float(np.mean(losses))
```

**Smoothing for early stopping:** Monitor raw per-epoch val loss (not smoothed). Patience=10 absorbs normal noise. If one epoch spikes due to rare RNG effect, the counter just increments — it doesn't permanently derail.

---

## 11. Validation Architecture (MANDATORY)

**Nyquist validation:** ENABLED (config has `nyquist_validation: true`).

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest 7.x (Python 3.11, vcc-main env) |
| Config file | `pytest.ini` or `pyproject.toml` — to add in Wave 0 |
| Quick run command | `pytest tests/ -x --tb=short` |
| Full suite command | `pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| MOD-01 | MIL Ranking Loss numerical correctness with known inputs | unit | `pytest tests/test_mil_loss.py::test_rank_loss_hinge -x` | ❌ Wave 0 |
| MOD-01 | Sparsity regularizer matches RTFM reference output on fixed input | unit | `pytest tests/test_mil_loss.py::test_sparsity_exact -x` | ❌ Wave 0 |
| MOD-01 | Smoothness regularizer matches RTFM reference output on fixed input | unit | `pytest tests/test_mil_loss.py::test_smoothness_exact -x` | ❌ Wave 0 |
| MOD-01 | Top-k with mask ignores zero-padded positions (set to -inf) | unit | `pytest tests/test_mil_loss.py::test_masked_topk -x` | ❌ Wave 0 |
| MOD-02 | Dataset returns [T=32, D] tensors for N>32 videos via segment sampling | unit | `pytest tests/test_dataset.py::test_train_resample_long -x` | ❌ Wave 0 |
| MOD-02 | Dataset zero-pads + masks for N<32 videos | unit | `pytest tests/test_dataset.py::test_train_pad_short -x` | ❌ Wave 0 |
| MOD-02 | Dataset skips 172 UCF sub-64-frame videos at load time | unit | `pytest tests/test_dataset.py::test_skip_empty_videos -x` | ❌ Wave 0 |
| MOD-02 | Paired DataLoader yields 16 normal + 16 abnormal per step | integration | `pytest tests/test_dataset.py::test_paired_loader -x` | ❌ Wave 0 |
| MOD-03 | SkeletonProj forward produces [B, T] scores without NaN | unit | `pytest tests/test_models.py::test_skeleton_only_forward -x` | ❌ Wave 0 |
| MOD-04 | CLIPProj forward: 1024-d → 512-d → scores, no NaN | unit | `pytest tests/test_models.py::test_clip_only_forward -x` | ❌ Wave 0 |
| MOD-05 | Late Fusion = 0.5 * skel_score + 0.5 * clip_score (equal weight) | unit | `pytest tests/test_models.py::test_late_fusion_equal -x` | ❌ Wave 0 |
| MOD-06 | Gated Fusion forward: [B, T, 256+1024] → [B, T], gate in [0,1] | unit | `pytest tests/test_models.py::test_gated_fusion_shapes -x` | ❌ Wave 0 |
| MOD-06 | Gated Fusion forward on real UCF features: no NaN, scores in [0,1] | integration | `pytest tests/test_models.py::test_gated_fusion_real_features -x` | ❌ Wave 0 |
| MOD-07 | `model.named_modules()` reveals ≥3 named nn.LayerNorm in Gated Fusion | unit | `pytest tests/test_models.py::test_gated_fusion_layernorms -x` | ❌ Wave 0 |
| MOD-07 | LN layers reachable as `model.ln_skel`, `model.ln_clip`, `model.ln_fused` | unit | `pytest tests/test_models.py::test_layernorm_attribute_access -x` | ❌ Wave 0 |
| TRN-01 | Scheduler warmup reaches full lr at epoch 5, then decays cosine | unit | `pytest tests/test_scheduler.py::test_linear_cosine -x` | ❌ Wave 0 |
| TRN-01 | AdamW optimizer configured with lr=1e-4, weight_decay=1e-2 | unit | `pytest tests/test_train.py::test_optimizer_config -x` | ❌ Wave 0 |
| TRN-02 | EarlyStopping triggers after patience=10 epochs of no improvement | unit | `pytest tests/test_early_stopping.py::test_patience_trigger -x` | ❌ Wave 0 |
| TRN-02 | Saved best_model.pth corresponds to the best val epoch (cross-check CSV) | integration | `pytest tests/test_train_integration.py::test_best_matches_csv -x` | ❌ Wave 0 |
| TRN-03 | Same seed produces bit-identical train losses over 2 epochs | integration | `pytest tests/test_reproducibility.py::test_bit_identical -x` | ❌ Wave 0 |
| TRN-03 | CUBLAS_WORKSPACE_CONFIG set before torch imports | unit | `pytest tests/test_train.py::test_cublas_env -x` | ❌ Wave 0 |
| TRN-04 | train_log.csv exists with header `epoch,train_loss,val_loss,lr` | integration | `pytest tests/test_train_integration.py::test_csv_header -x` | ❌ Wave 0 |
| TRN-04 | Each epoch appends exactly one row with 4 numeric fields | integration | `pytest tests/test_train_integration.py::test_csv_rows -x` | ❌ Wave 0 |
| TRN-05 | config_snapshot.json contains resolved config + git SHA + pip freeze | unit | `pytest tests/test_config.py::test_snapshot_contents -x` | ❌ Wave 0 |
| TRN-05 | Loading snapshot + re-running produces bit-identical loss curves | acceptance | `pytest tests/test_train_e2e.py::test_snapshot_roundtrip -x` | ❌ Wave 0 |
| TRN-06 | `python src/train.py --config configs/skeleton_only.yaml` succeeds | acceptance | `pytest tests/test_train_e2e.py::test_skeleton_only_trains -x` | ❌ Wave 0 |
| TRN-06 | Same entry point works for all 4 variants via YAML change only | acceptance | `pytest tests/test_train_e2e.py::test_all_variants_cli -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x --tb=short` (unit + integration, skip e2e) — < 10 seconds
- **Per wave merge:** `pytest tests/ -v` (all including e2e 2-epoch smoke) — ~2-3 minutes
- **Phase gate:** Full suite green + Success Criterion #4 (bit-identical rerun on Gated Fusion)

### Wave 0 Gaps

- [ ] `tests/test_mil_loss.py` — MIL loss + sparsity/smoothness + masked top-k (MOD-01)
- [ ] `tests/test_dataset.py` — MILFeatureDataset sampling, padding, skip logic (MOD-02)
- [ ] `tests/test_models.py` — per-variant forward + LN discoverability (MOD-03..07)
- [ ] `tests/test_scheduler.py` — SequentialLR warmup+cosine curve (TRN-01)
- [ ] `tests/test_early_stopping.py` — EarlyStopping patience + NaN handling (TRN-02)
- [ ] `tests/test_reproducibility.py` — bit-identical rerun smoke (TRN-03)
- [ ] `tests/test_config.py` — config load/merge/snapshot (TRN-05)
- [ ] `tests/test_train_integration.py` — 2-epoch smoke with 10 videos (MOD + TRN end-to-end)
- [ ] `tests/test_train_e2e.py` — acceptance: full CLI run produces artifacts (TRN-06)
- [ ] `tests/conftest.py` extensions — `feature_dir` fixture pointing to `E:/features/ucf/`, `smoke_split_dir` for 10-video subset
- [ ] `pytest.ini` or `pyproject.toml` with `[tool.pytest.ini_options]` + `testpaths = ["tests"]`

---

## 12. Security Considerations

Phase 3 is an offline training pipeline. Attack surface is limited but not zero:

### 12.1 Supply-chain integrity

- **Pin versions in `requirements-main.txt`** — `torch==2.6.0`, `torchvision==0.21.0`, `wandb==0.26.0`, `open-clip-torch==3.3.0`, `numpy>=1.23,<2.0` (numpy 2.x breaks some libs)
- Reason: an unversioned `pip install torch` picks up whatever is current, breaking reproducibility

### 12.2 `torch.load` safety (CVE-2025-32434 context)

[VERIFIED: PyTorch 2.6 release + security advisory WebSearch 2026-04-14]

- PyTorch 2.6+ defaults `weights_only=True`. CVE-2025-32434 affected versions ≤2.5.1 **even with weights_only=True**; fixed in 2.6.0. Our stack (2.6.0) is patched.
- **Never load a third-party `.pth`** with `weights_only=False`. All checkpoints in this project are produced by us in the same run; the security surface is internal only.
- Recommendation: save `model.state_dict()` (tensors only) not pickled objects. Config snapshot goes in a separate `config_snapshot.json` (§6.3). Then `weights_only=True` always works.

### 12.3 Credential leaks in wandb logs

- **Never commit WANDB_API_KEY** to git. Use `wandb login` (writes to `~/.netrc`) or env var set by user shell.
- `wandb.config = cfg` logs the whole config dict. **Never put API keys or secrets in YAML.** Our YAML schema has no secret fields — this is safe.
- Private dataset paths (`E:/features/ucf/`) are logged to wandb. This is a machine-local path not a sensitive secret; acceptable for a personal thesis project. If sensitive: scrub via `wandb.config.update({"paths": "redacted"})`.

### 12.4 Results directory permissions

- `results/` is gitignored (Phase 1 D-07); checkpoints never committed
- Windows default ACLs on `results/` grant write only to the running user — no action needed unless using a shared machine

### 12.5 Reproducibility as integrity

- `config_snapshot.json` with git SHA + pip freeze is a passive integrity check: if the checkpoint in `results/X/best_model.pth` is claimed to be from config X, anyone can verify by re-running. Tampering is detectable.

---

## 13. Pitfall Mitigation Map

| Pitfall | From research | Phase 3 prevention | Regression test |
|---|---|---|---|
| **C3** Test set leakage | Loading test annotations into training | Only `data/splits/*_val.txt` (MIL loss monitorable) accessed by training; test annotations live only in Phase 4 `evaluate.py` | `tests/test_train_integration.py::test_no_test_split_access` — grep AST for imports/opens of `*_test.txt` in training-side code |
| **C4** Off-by-one in snippet→frame expansion | Only relevant at eval time (Phase 4) | Phase 3 produces scores at snippet level; snippet-to-frame mapping happens in Phase 4 `evaluate.py`. Test-time score dict keyed by video_id + snippet_index, not frame_index — no expansion in Phase 3 | Deferred to Phase 4; Phase 3 ensures `len(scores) == N_snippets` via assertion in `score_video()` (§10.1) |
| **C5** MIL training collapse to trivial solution | Model outputs all-high or all-low per video | (a) D-03 λ_sparse=8e-3 + λ_smooth=8e-4 regularizers from RTFM; (b) monitor snippet score variance per epoch and log to wandb; (c) per-video score histograms in `train_log.csv` at sampled epochs | `tests/test_train_integration.py::test_score_variance` — after 5 smoke epochs on 10 abnormal videos, assert per-video `std(scores) > 0.05` (not collapsed) |
| **M5** TTA entropy collapse on normal-heavy batches | Phase 5 concern, but Phase 3 architecture must enable the fix | D-07 places 3-4 LN layers as TTA surface (not 1) — Phase 5 SAR-style filtering has enough parameters to selectively update | `tests/test_models.py::test_gated_fusion_layernorms` verifies ≥3 LN; Phase 5 will add entropy-collapse regression tests |
| **m1** Gated Fusion gate saturation | Sigmoid saturates → equivalent to Late Fusion | Small Xavier init (gain=0.1) on `self.gate.weight` — §8.D — keeps initial gate ≈ sigmoid(0) = 0.5; monitor `mean(gate)` per epoch | `tests/test_train_integration.py::test_gate_not_saturated` — after 5 smoke epochs, assert `0.2 < mean(gate) < 0.8` |
| **m3** Val split imbalance | Already handled in Phase 2 — stratified split committed | Read-only for Phase 3; CSV logger tags dataset ratio at startup as a sanity check | `tests/test_dataset.py::test_val_split_balance` — assert `abs(n_normal/n_total - 0.5) < 0.1` |
| **m4** Single-run statistical instability | Report single-run numbers is unstable | Phase 3 infrastructure (seeds in YAML + CLI override) enables Phase 4 EVAL-05 3-seed reruns trivially; wandb sweep config in §9.4 | Deferred to Phase 4 |
| **m5** TTA reset state stale | Phase 5 concern | D-15 saves `best_model.pth` — Phase 5 TTAWrapper captures `ln_state_init = {name: (ln.weight.clone(), ln.bias.clone()) for name, ln in named_LN_modules}` AFTER loading best_model.pth (not at init) | Deferred to Phase 5 |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Val MIL loss is a reliable early-stopping signal for all 4 variants (including single-modal) | §10.3 | If val loss is uncorrelated with test AUC for Skeleton-Only (possible — single modality might have noisier val loss), early stopping could pick a mediocre checkpoint. Mitigation: phase-4 RTFM reproduction will catch it (comparison anchor reveals if training is broken). |
| A2 | RTFM `process_feat` (mean-pool per segment) is compatible with D-09 (random-within-segment) | §1.5, §7.1 | Negligible — both are segment-based. The D-09 choice "random within segment" is a minor augmentation on top of RTFM's exact spec. |
| A3 | `persistent_workers=True` on Windows preserves determinism on first epoch | §7.2 | Low — [CITED: pytorch/pytorch#73603] documents a subtle second-epoch issue but first-epoch is reliable. For bit-identical 2-epoch smoke tests, may need `persistent_workers=False`. |
| A4 | RTX 4090 + CUDA 12.4 + PyTorch 2.6 has no known nondeterminism affecting our specific ops (MLP + LN + top-k + sigmoid + mean) | §2.3 | Low — the ops we use are all in the deterministic list. `warn_only=True` is a safety net if a PyTorch internal turns out to call a nondeterministic op. |
| A5 | Config snapshot `pip freeze` via `importlib.metadata.distributions()` captures all relevant versions | §6.3 | Low — stdlib approach; robust. Edge case: editable installs may report `0.0.0` as version. Acceptable since we don't use editable installs for the main env libs. |
| A6 | `model.named_modules()` traversal finds all LN layers including those inside MILHead | §8.F | Zero risk — PyTorch's named_modules recurses into all submodules. Unit-testable. |
| A7 | wandb 0.26.0 API (`wandb.init`, `wandb.log`, `wandb.define_metric`) matches the patterns documented | §9 | Low — APIs are stable since 0.16+. If `define_metric` signature changes, fall back to raw logging without step axis alignment (cosmetic effect on wandb UI only). |

---

## Open Questions

1. **Exact validation sampling convention**
   - **What we know:** Val uses the same MIL loss as training, so val videos must also be paired into normal+abnormal bags with T=32 sampling
   - **What's unclear:** Should val sampling be deterministic (e.g. always pick segment-centers) for a stable loss number, or match training's random-within-segment?
   - **Recommendation:** Use deterministic center-segment sampling for val (fixed generator seeded from config seed + 1000) to reduce val-loss variance that could destabilize early stopping. Verify against a pilot run in Wave 1.

2. **RTFM sparsity formula's `dim=0` behavior with zero-padded bags**
   - **What we know:** RTFM's `torch.norm(arr, dim=0)` is L2 across the batch dimension at each snippet position, then mean across positions
   - **What's unclear:** With zero-padded positions, `arr * mask` (zero where padded) means zero contributes to the L2 — this biases the sparsity downward for short videos
   - **Recommendation:** Before computing sparsity, multiply by `mask` and divide the mean by `sum(mask)/mask.numel()` to normalize for expected non-padded fraction. If this produces weird values, revert to the simpler `arr * mask` and document the known bias.

3. **`torch.use_deterministic_algorithms(True, warn_only=True)` vs `False`**
   - **What we know:** Our model and loss use only deterministic-capable ops
   - **What's unclear:** Will any internal PyTorch 2.6 op silently hit a non-deterministic path and invalidate bit-identical claims?
   - **Recommendation:** Start with `warn_only=True` (resilient); collect warning output in the first full-run smoke test. If zero warnings, switch to `warn_only=False` for production runs as a stronger guarantee. Document this in Phase 3 run log.

4. **How to make the scheduler exactly reproducible across resume**
   - **What we know:** SequentialLR stores state in its sub-schedulers; `scheduler.state_dict()` captures it
   - **What's unclear:** `last_model.pth` needs to save scheduler state too, otherwise a resumed run after crash has a slightly different LR trajectory
   - **Recommendation:** Include `scheduler.state_dict()` in the saved checkpoint dict. Round-trip test it in `tests/test_train_integration.py::test_resume_roundtrip`.

5. **Concrete data path on Windows junction target**
   - **What we know:** Phase 1 D-05/D-06 specify `E:/features/ucf/...` as the feature path; Phase 2 produced files there
   - **What's unclear:** Does the test suite (Wave 0) depend on the actual `E:/` drive being mounted, or should we mock with tiny synthetic features?
   - **Recommendation:** Unit tests (MIL loss, model forward) use synthetic tensors — zero dependency on E:/. Integration tests use a `smoke_fixtures/` dir in the repo with 10 pre-committed synthetic npy files. End-to-end tests require real `E:/` (skip with `@pytest.mark.requires_features` if path missing).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| PyTorch | All of Phase 3 | ✓ (vcc-main env) | 2.6.0+cu124 | — |
| CUDA 12.4 | PyTorch CUDA ops | ✓ | 12.4 | CPU training (60x slower, fine for smoke) |
| RTX 4090 | Fast training | ✓ | — | — |
| wandb | Experiment tracking (D-13) | ✓ (pip installable) | 0.26.0 latest | `WANDB_MODE=disabled`, CSV only |
| numpy | Arrays, npy load | ✓ | ≥1.23 | — |
| PyYAML | Config parsing | ✓ | ≥6.0 | — |
| pytest | Test framework | ✓ (pip installable) | 7.x | — |
| scikit-learn | Not in Phase 3 hot path | ✓ | ≥1.3 | — (used in Phase 4) |
| h5py | Not used in Phase 3 | ✓ | ≥3.8 | — |
| `E:/features/ucf/*` | Data loader (real train) | ✓ (confirmed in STATE.md) | — | Synthetic `smoke_fixtures/` for Wave 0 tests |
| `E:/features/xd/*` | Data loader (XD runs) | Partial (extraction in flight, 5-8d remaining) | — | Train on UCF only until XD ready |
| git CLI | Config snapshot (TRN-05) | ✓ | — | Omit git SHA if `git` missing |

**Missing dependencies with no fallback:** None for UCF Phase 3.
**Missing dependencies with fallback:** XD-Violence features — train on UCF first (parallel to extraction), rerun on XD once ready.

---

## Sources

### Primary (HIGH confidence)
- RTFM upstream: https://github.com/tianyu0207/RTFM — `train.py` sparsity/smoothness, `model.py` top-k, `utils.py` process_feat (WebFetch 2026-04-14)
- TENT upstream: https://github.com/DequanWang/tent — `tent.py` configure_model, collect_params, episodic reset (WebFetch 2026-04-14)
- PyTorch reproducibility docs: https://docs.pytorch.org/docs/stable/notes/randomness.html (WebFetch 2026-04-14)
- PyTorch CUBLAS_WORKSPACE_CONFIG: verified via WebSearch + community consensus (PyTorch 2.6+ requires `:4096:8` or `:16:8`)
- PyTorch 2.6 release notes: https://pytorch.org/blog/pytorch2-6/ + https://dev-discuss.pytorch.org/t/pytorch-2-6-0-general-availability/2762 (release date 2025-01-29, weights_only default flip)
- wandb env vars: https://docs.wandb.ai/guides/track/environment-variables/ (WebFetch 2026-04-14)
- wandb resumable runs: https://docs.wandb.ai/guides/runs/resuming/ (WebFetch 2026-04-14)
- wandb latest: https://pypi.org/project/wandb/ — version 0.26.0, 2026-04-13 (WebFetch 2026-04-14)
- CVE-2025-32434 (PyTorch torch.load): https://github.com/pytorch/pytorch/security/advisories/GHSA-53q9-r3pm-6pq6 (patched in 2.6.0, our stack is safe)

### Secondary (MEDIUM confidence)
- Python atomic write pattern: activestate recipe + zetcode os.replace guide (WebSearch verified against multiple sources, standard tempfile+os.replace on same directory)
- Windows DataLoader pickling: pytorch/pytorch#12831, #51344, #73603 (WebSearch)
- SequentialLR + LinearLR + CosineAnnealingLR patterns: PyTorch docs + discuss.pytorch.org community examples
- Timm-style model registry: huggingface/pytorch-image-models `_registry.py` (referenced but not adopted — explicit dict chosen instead)

### Tertiary (LOW confidence, not used as authoritative)
- MGFN `train.py` — upstream fetch returned 404 (repo name carolchenyx/MGFN. with trailing dot). RTFM serves as the canonical reference since MGFN inherits RTFM's loss formulation.

---

## Metadata

**Confidence breakdown:**
- MIL loss exact formulation: HIGH — directly verified against RTFM upstream code
- Reproducibility knob stack: HIGH — verified against PyTorch official docs + Python stdlib docs
- Gated Fusion module spec: HIGH — matches PRD §9.2 verbatim with one addition (residual sum of both projections, reading the architecture spec literally)
- wandb integration: HIGH — env vars, resume pattern, define_metric all verified
- Atomic Windows writes: HIGH — `tempfile + os.replace` is the documented stdlib pattern
- DataLoader seeded workers on Windows: MEDIUM — base pattern is documented; Windows edge cases (persistent_workers 2nd-epoch nondeterminism, lambda pickling) are community-reported but consistent across sources
- TTA stub for Phase 5 compatibility: HIGH — TENT episodic reset pattern is directly transferable

**Research date:** 2026-04-14
**Valid until:** 2026-05-14 (30 days — PyTorch 2.6 + wandb 0.26 are stable; RTFM/TENT upstream are frozen)
