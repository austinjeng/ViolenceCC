---
phase: 03-model-architecture-training-infrastructure
reviewed: 2026-04-14T00:00:00Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - src/data/__init__.py
  - src/data/dataset.py
  - src/data/loaders.py
  - src/losses/__init__.py
  - src/losses/mil_loss.py
  - src/models/__init__.py
  - src/models/clip_only.py
  - src/models/gated_fusion.py
  - src/models/late_fusion.py
  - src/models/mil_head.py
  - src/models/registry.py
  - src/models/skeleton_only.py
  - src/utils/__init__.py
  - src/utils/checkpoint.py
  - src/utils/config.py
  - src/utils/csv_logger.py
  - src/utils/early_stopping.py
  - src/utils/scheduler.py
  - src/utils/seed.py
  - src/utils/wandb_logger.py
  - src/train.py
  - configs/skeleton_only.yaml
  - configs/clip_only.yaml
  - configs/late_fusion.yaml
  - configs/gated_fusion.yaml
  - tests/conftest.py
  - tests/fixtures/__init__.py
  - tests/fixtures/synthetic.py
  - pyproject.toml
status: issues_found
total_findings: 8
by_severity:
  critical: 0
  warning: 4
  info: 4
updated: 2026-04-14T00:00:00Z
---

# Phase 3: Code Review Report

**Reviewed:** 2026-04-14
**Depth:** standard
**Files Reviewed:** 24 source + 3 test/fixture files + 1 config file
**Status:** issues_found

## Summary

Phase 3 delivers a well-structured, well-documented MIL training pipeline. The RTFM-exact loss formulas, Windows-safe atomic checkpointing, layered determinism (CUBLAS_WORKSPACE_CONFIG before import, seed.py KNOBs 1-3, worker seeding), and wandb graceful-degradation pattern are all correctly implemented. YAML safe-loading is used exclusively; no pickle usage outside torch.save/load (weights_only=True). The four model variants correctly implement D-07 named LayerNorms and share an identical MILHead by construction.

Four warnings were found — none are training-correctness bugs that would invalidate results, but two (LR off-by-one and smoothness docstring) will cause confusion during later phases. Four info items flag minor maintainability issues.

---

## Warnings

### WR-01: LR logged one epoch ahead of when it is actually used

**File:** `src/train.py:174-176`

**Issue:** `scheduler.step()` is called at line 174, advancing the LR for the next epoch. The LR read at line 176 (`optimizer.param_groups[0]["lr"]`) is therefore the LR for epoch `epoch+1`, not the LR that was actually applied during `train_one_epoch()` at `epoch`. Concretely, at `epoch=0` the optimizer runs with lr=1e-6 (warmup start) but the CSV and wandb log both record the epoch-1 warmup LR (~2e-5). At the final epoch (epoch 49) the CSV records the hypothetical epoch-50 LR (0.0 for cosine decay to eta_min=0). This is an instrumentation error: training correctness is unaffected, but the logged LR curve is off by one epoch throughout, which matters for thesis reporting and for the `test_snapshot_roundtrip` bit-identical assertion if anyone later changes the step order.

**Fix:** Read the current epoch's LR before calling `scheduler.step()`:

```python
# In main() epoch loop, swap the two lines:
lr = optimizer.param_groups[0]["lr"]   # read BEFORE step
scheduler.step()                        # advance to next epoch
```

---

### WR-02: `_smoothness` docstring incorrectly describes what "adjacent" means

**File:** `src/losses/mil_loss.py:33-49`

**Issue:** The docstring says "L2 on adjacent-**snippet** score differences" and the inline comments in `_smoothness` reference the RTFM arr2-shift pattern. However, for a `[B_abn, T]` tensor with `B_abn > 1`, `arr2[:-1] = arr[1:]` shifts **rows** (videos), not columns (snippets). The penalty is therefore the squared difference between consecutive **video** scores at each snippet position — cross-video, not within-video temporal smoothness. For `B_abn=1` the operation degenerates completely: `arr2[:-1]` is an empty slice assignment, so `arr2 = zeros_like` then `arr2[-1] = arr[-1]`, giving `arr2 == arr` and zero penalty regardless of the actual snippet sequence. This is RTFM-exact behavior and intentional by D-03, but the docstring is factually wrong and will mislead Phase 5 TTA analysis (which may try to interpret the smoothness gradient to understand which LN layers are being regularized temporally).

**Fix:** Correct the docstring to match what the code actually does:

```python
def _smoothness(scores_abn: torch.Tensor, lam: float = 8e-4) -> torch.Tensor:
    """RTFM-exact cross-video score smoothness (verbatim arr2-shift from RTFM train.py).

    NOTE: The shift `arr2[:-1] = arr[1:]` operates on ROWS (videos in the batch),
    not on COLUMNS (snippet time positions). For B_abn=16 this penalizes the
    score difference between video[i] and video[i+1] at each snippet position.
    For B_abn=1, arr2[:-1] is an empty slice and the penalty is always 0.

    This is exactly what RTFM does; do not change it (D-03).

    arr: [B_abn, T] sigmoid scores in [0, 1]
    """
```

---

### WR-03: `_smoothness` applies an unintended penalty at the real-to-pad boundary when `B_abn == 1` (but the docstring implies it does; confirmed it does NOT — see details)

**File:** `src/losses/mil_loss.py:79-83`

**Issue:** The masking strategy for regularizers is `scores_abn_real = scores[n_normal:] * mask[n_normal:]` which zeros out padded positions. For `_sparsity` this is correct: `torch.norm([..., 0, 0], dim=0)` contributes 0 at padded columns. For `_smoothness` with `B_abn=1`, as shown in WR-02, the penalty is always 0 regardless of masking, so the boundary is not penalized. **However**, for `B_abn > 1`, the padding zeros do create a false discontinuity in `_smoothness` at the boundary between the last real video (row) and the padded videos — if padded rows appear in the middle of the batch. In practice D-04 ensures `B_abn=16` with zero-padded snippets inside each video (not whole-video padding), so the rows all have the same padding structure. The cross-video smoothness penalty at padded snippet columns is genuinely zero (padded columns are all 0.0, so `arr2[i, col] - arr[i+1, col] = 0 - 0 = 0`). Confirmed with runtime check: the boundary does not produce a spurious penalty.

**Revised assessment:** This is not a correctness bug. Retaining as a warning because the comment `"masked to zero at padded positions so padding does not bias reg"` implies an incorrect mechanism (it implies the mask prevents a penalty, but actually the cross-video diff between two zero-padded snippets is zero by the nature of the operation). The comment should be corrected to avoid confusion:

**Fix:** Update the comment at `mil_loss.py:67-70`:

```python
# Step 3: regularizers on abnormal scores only.
# Zero-pad masking ensures padded positions have score=0. For _sparsity,
# zeros contribute 0 to the L2 column norm. For _smoothness, zero-padded
# columns produce zero cross-video differences (0-0=0), so no boundary artifact.
scores_abn_real = scores[n_normal:] * mask[n_normal:]
```

---

### WR-04: `PYTHONHASHSEED` is captured in the config snapshot but never set by `set_deterministic` — the reproducibility documentation is incomplete

**File:** `src/utils/seed.py:17-42`, `src/utils/config.py:114-116`

**Issue:** `set_deterministic()` sets 4 knobs (KNOB 1: RNGs, KNOB 2: cuDNN, KNOB 3: deterministic algorithms, KNOB 4: CUBLAS — documented as needing to be set before `import torch`). However, `PYTHONHASHSEED` controls Python's dict and set iteration order, which affects DataLoader batch construction if any dict-keyed objects are iterated over in a non-deterministic order. `set_deterministic()` does not set `PYTHONHASHSEED`, and `snapshot_config()` records its current value but does not emit a warning if it is unset (which would mean hash randomization is on). For 3-seed reproducibility runs in the thesis ablation table, if `PYTHONHASHSEED` is not explicitly fixed in the training launch command, two runs with the same explicit seed but different `PYTHONHASHSEED` environments could produce different DataLoader batching order.

On Python 3.11 (the vcc-main env), `PYTHONHASHSEED` defaults to a random value per process unless `PYTHONHASHSEED=0` is set. In practice the risk is low for this codebase since the DataLoader uses explicit `torch.Generator` shuffle seeding (not Python dicts), but the omission means the "4-KNOB" documentation is incomplete: there is an implicit 5th requirement for bit-identical reruns.

**Fix:** Add to `set_deterministic()` and `src/train.py` docstring:

```python
# src/utils/seed.py -- add warning at the end of set_deterministic():
if not os.environ.get("PYTHONHASHSEED"):
    import warnings
    warnings.warn(
        "PYTHONHASHSEED is not set. For complete bit-identical reproducibility, "
        "run: PYTHONHASHSEED=0 python src/train.py ...",
        UserWarning, stacklevel=2
    )
```

Or at minimum, add to the module-level docstring:
```
KNOB 5 (undocumented): Set PYTHONHASHSEED=0 in the shell before launching train.py.
Python hash randomization affects dict/set iteration order; though the DataLoader
generator seed controls shuffling, PYTHONHASHSEED is required for full bit-identity.
```

---

## Info

### IN-01: Eagerly importing all variant models in `src/models/__init__.py` defeats the lazy-factory registry

**File:** `src/models/__init__.py:1-6`

**Issue:** The `MODEL_REGISTRY` in `src/models/registry.py` uses a lazy-factory pattern (each entry is a callable that imports the class on first call) specifically to allow the registry module to be imported before all four variant files exist. However, `src/models/__init__.py` eagerly imports all four classes at the top level. Any code that does `from src.models import build_model` now transitively imports all four variant classes immediately. This makes the lazy-factory pattern in `registry.py` a dead code path in the final state: the "lazy" protection is bypassed. Not harmful in the completed Phase 3 state where all four files exist, but it is an inconsistency that could confuse someone who later adds a 5th variant and only adds the registry entry without the corresponding `__init__.py` import.

**Fix:** Either remove the lazy-factory indirection from `registry.py` and import directly, or remove the variant-level imports from `__init__.py` and rely solely on the registry:

```python
# Option A: simplify registry.py to direct imports since all classes exist
MODEL_REGISTRY: Dict[str, type] = {
    "skeleton_only": SkeletonProj,
    "clip_only": CLIPProj,
    "late_fusion": LateFusion,
    "gated_fusion": GatedFusion,
}
```

---

### IN-02: `src/losses/__init__.py` exports private helpers `_sparsity` and `_smoothness`

**File:** `src/losses/__init__.py:1,3`

**Issue:** Both `_sparsity` and `_smoothness` are exported in `__all__`, making them part of the public API of the `src.losses` package. These are internal helpers (prefixed with `_` per Python convention). Exporting them in `__all__` contradicts the convention and may cause Phase 5/6 code to accidentally depend on their signatures. Tests that reference them can import them directly from `src.losses.mil_loss`.

**Fix:**

```python
# src/losses/__init__.py
from src.losses.mil_loss import mil_ranking_loss

__all__ = ["mil_ranking_loss"]
```

---

### IN-03: `LateFusion._device()` uses `next(self.parameters())` which would raise `StopIteration` for a parameter-free model

**File:** `src/models/late_fusion.py:64-66`

**Issue:** The `_device()` helper returns `next(self.parameters()).device` to get the current device for constructing the `alpha=0.5` tensor. This raises an uncaught `StopIteration` if the model has no trainable parameters. In `LateFusion`, this cannot happen in practice (both `self.skeleton` and `self.clip` sub-modules always have `nn.Linear` layers), but the pattern is fragile and would silently surface as a `StopIteration` if the architecture is ever restructured. Runtime testing confirmed this raises `StopIteration` when called on a bare `nn.Module` with no parameters.

**Fix:** Use the `nn.Module`-idiomatic pattern:

```python
def _device(self):
    # Use a buffer or parameter if available; fallback to CPU
    try:
        return next(self.parameters()).device
    except StopIteration:
        return torch.device("cpu")
```

Or, simpler: pass the device as an argument to `_alpha()` when called from `forward()`:

```python
def forward(self, skel=None, clip=None, mask=None):
    ...
    a = torch.tensor(0.5, device=skel.device) if self.alpha_logit is None \
        else torch.sigmoid(self.alpha_logit)
    ...
```

---

### IN-04: `conftest.py` hardcodes absolute Windows path for `PROJECT_ROOT`

**File:** `tests/conftest.py:5`

**Issue:** `PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")` is an absolute machine-specific path. Any collaborator or CI runner on a different machine or drive letter will get failures that look like missing fixtures rather than a clear error about path configuration. This is a solo-researcher project where this is unlikely to matter in practice, but it is fragile.

**Fix:** Use a relative path derived from the conftest location:

```python
# tests/conftest.py
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
```

This matches the pattern used in `src/train.py:16-18` (`Path(__file__).resolve().parent.parent`).

---

## Numerical Correctness Audit — No Additional Issues Found

The following were verified correct during review:

- **MIL ranking loss formula** (D-01, D-02): `torch.relu(margin - topk_abn + topk_nor).mean()` matches RTFM exactly. `topk_vals` is computed from `scores_masked` (after `-inf` fill), so padded positions cannot win top-k.
- **Top-k mask with `-inf`** (D-10): `masked_fill(mask == 0, float("-inf"))` before `torch.topk` is correct. Zero-padded scores of 0.0 could otherwise outrank real snippets with negative pre-sigmoid logits; `-inf` prevents this.
- **Sparsity regularizer** (D-03): `lam * mean(norm(arr, dim=0))` matches RTFM verbatim. `dim=0` computes L2 norm over the batch dimension (across videos per snippet), not across snippets.
- **Segment sampling** (D-09): `np.linspace(0, N, T+1, dtype=np.int64)` with the `max(lo+1, hi)` guard handles degenerate segments correctly. Last segment always ends at exactly `N`, and `randint(lo, N)` is exclusive-upper so max index is `N-1` — no out-of-bounds.
- **CUBLAS_WORKSPACE_CONFIG ordering** (TRN-03): `os.environ.setdefault(...)` is at `src/train.py:5`, before `import torch` at line 20. Verified by inspection.
- **GatedFusion gate init** (m1 mitigation): `nn.init.xavier_uniform_(self.gate.weight, gain=0.1)` with `nn.init.zeros_(self.gate.bias)` gives `mean(sigmoid(Wx+b)) ≈ 0.5` for random inputs.
- **Windows atomic checkpoint** (TRN-02): `tempfile.mkstemp(dir=path.parent)` + `os.fsync` + `os.replace` — same-directory tempfile ensures `os.replace` is within one filesystem, which is atomic on NTFS.
- **YAML loading** (security): All YAML is loaded via `yaml.safe_load` — confirmed no `yaml.load` with unsafe Loader anywhere in `src/`.
- **Pickle security**: Checkpoints save only `state_dict` (tensor-only); `torch.load(..., weights_only=True)` rejects any non-tensor payload.
- **Scheduler correctness**: `SequentialLR(milestones=[warmup_epochs=5])` with `LinearLR(total_iters=5)` and `CosineAnnealingLR(T_max=45)` produces the expected warmup+cosine curve over 50 epochs. Confirmed by runtime trace.
- **D-07 named LayerNorms**: `ln_skel`, `ln_clip`, and `ln_fused` are direct attributes on `GatedFusion`, `SkeletonProj`, and `CLIPProj` respectively. Discoverable via `model.named_modules()` for Phase 5 TTA collection.
- **val loader `_split_labels` paired reconstruction**: `_split_labels` truncates to `n = min(len(nor_idx), len(abn_idx))` so `n_normal == n_abnormal` for every val batch, ensuring the paired hinge `topk_abn + topk_nor` addition is same-shaped.

---

## Security Audit — No Issues

- No `yaml.load` with unsafe Loader
- No `eval()` usage
- No hardcoded secrets or API keys
- No path traversal risk in config loading (`load_config` accepts a user-supplied path but only reads it, does not execute it)
- `subprocess` usage in `_git_info()` is safe: `["git", "rev-parse", "HEAD"]` is a hardcoded list, not a shell string — no injection possible
- `wandb.init(config=cfg)` passes the full config dict to wandb; this includes filesystem paths but does not execute them

---

_Reviewed: 2026-04-14_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
