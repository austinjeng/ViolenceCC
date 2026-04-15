# Phase 4: Baseline Evaluation & Main Results - Pattern Map

**Mapped:** 2026-04-15
**Files analyzed:** 34 (new + modified)
**Analogs found:** 32 / 34 (2 greenfield with no close analog)

## File Classification

### New source files

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `src/evaluate.py` | CLI entry point | request-response | `src/train.py` | exact (same shape: argparse + load_config + build_model + run_dir) |
| `src/eval/__init__.py` | package marker | — | `src/models/__init__.py` | exact |
| `src/eval/test_loader.py` | data loader with guard | CRUD (read-only) | `src/data/dataset.py` (wrapper); `src/data/loaders.py` (dispatch) | role-match (new isolation layer, no existing module has sys.argv guard) |
| `src/eval/metrics.py` | utility (sklearn wrapper) | transform | `src/losses/mil_loss.py` (pure-function utility with asserts) | partial (different domain, same shape) |
| `src/eval/snippet_to_frame.py` | utility (pure function) | transform | `src/losses/mil_loss.py` (pure function w/ length semantics) | partial |
| `src/eval/ucf_annotations.py` | parser utility | file-I/O | none close; `src/data/dataset.py::_load_split` | partial (similar one-shot text parse pattern) |
| `src/models/rtfm_i3d.py` | model variant wrapper | request-response | `src/models/skeleton_only.py` (single-modality, single-LN, MILHead) | exact (5th variant, parallel construction) |
| `src/data/i3d_dataset.py` | torch Dataset | CRUD (read-only, file-backed) | `src/data/dataset.py::MILFeatureDataset` | exact (directly parallel; substitutes I3D 5-crop for skel+clip) |

### Modified source files

| Modified File | Role | Data Flow | Closest Analog |
|---------------|------|-----------|----------------|
| `src/models/registry.py` | registry (dict + factory) | — | itself (add 5th lazy factory) |
| `src/data/dataset.py` | torch Dataset | CRUD | itself (extend `__init__` with `skel_agg`; extend `__getitem__` with 3D→2D reshape) |
| `src/data/loaders.py` | DataLoader builder | — | itself (pass through `skel_agg`; swap feature paths via cfg) |
| `src/utils/config.py` | config utility | transform | itself (add `config_hash()` + `checkpoint_sha()` helpers parallel to `_git_info()`) |
| `src/utils/wandb_logger.py` | logger wrapper | event-driven | itself (add offline-fallback branch on `wandb.errors.Error`) |
| `src/utils/csv_logger.py` | append-only CSV logger | file-I/O | itself (add `results_index_append()` sibling function) |
| `src/train.py` | CLI entry | request-response | itself (add `--run-name` override to `parse_args` + `apply_cli_overrides` + override `run_name()` when provided) |

### New scripts

| New Script | Role | Data Flow | Closest Analog | Match Quality |
|------------|------|-----------|----------------|---------------|
| `scripts/run_ablations.py` | subprocess orchestrator | batch | `scripts/extract_ctrgcn.py` (CLI+argparse+queue+resume); `src/train.py` (subprocess) | partial (queue semantics are new; resume/logging patterns match extractor) |
| `scripts/wandb_preflight.py` | fail-fast check script | request-response | `scripts/verify_alignment.py` (CLI exit-code-only script) | partial |
| `scripts/verify_pooling_caches.py` | sanity check script | CRUD (read-only) | `scripts/verify_alignment.py` | exact (same role, same pattern) |

### Modified scripts

| Modified Script | Role | Data Flow | Closest Analog |
|-----------------|------|-----------|----------------|
| `scripts/extract_ctrgcn.py` | extractor | batch file-I/O | itself (add `--keep-persons` flag; alter M-pool step to emit `[N, 2, 256]`) |
| `scripts/extract_clip.py` | extractor | batch file-I/O | itself (add `--pool` flag; slice `mean_feat` only when `pool=mean`) |

### New configs

| New Config | Role | Data Flow | Closest Analog | Match Quality |
|------------|------|-----------|----------------|---------------|
| `configs/rtfm_i3d.yaml` | YAML config | — | `configs/skeleton_only.yaml` (single-modality variant) | exact |
| `configs/gated_fusion_2person.yaml` | YAML config | — | `configs/gated_fusion.yaml` (same variant, different cache path + skel_dim) | exact |
| `configs/gated_fusion_clip_mean.yaml` | YAML config | — | `configs/gated_fusion.yaml` (same variant, different cache path + clip_dim) | exact |

### New tests

| New Test | Role | Data Flow | Closest Analog |
|----------|------|-----------|----------------|
| `tests/test_snippet_to_frame.py` | unit test | — | `tests/test_mil_loss.py` (unit test for pure function) — inferred pattern |
| `tests/test_ucf_annotations.py` | unit test | — | `tests/test_splits.py` (text file parsing) |
| `tests/test_test_loader_guard.py` | unit test | — | `tests/test_dataset.py` + sys.argv monkeypatching |
| `tests/test_evaluate_cli.py` | integration test | — | `tests/test_train_e2e.py` (CLI+synthetic+run-dir inspection) |
| `tests/test_rtfm_model.py` | unit test | — | `tests/test_models.py` (variant shape + LN + registry round-trip) |
| `tests/test_i3d_loader.py` | unit test | — | `tests/test_dataset.py` (synthetic .npy fixture + Dataset construction) |
| `tests/test_verify_pooling.py` | unit test | — | `tests/test_dataset.py` (pattern-reuse via synthetic features) |
| `tests/test_skel_agg.py` | unit test | — | `tests/test_dataset.py::test_train_resample_long` (parameterized shape assertion) |
| `tests/test_run_ablations.py` | integration test | — | `tests/test_train_e2e.py` (subprocess invocation + tmp paths) |
| `tests/test_done_marker.py` | unit test | — | `tests/test_checkpoint.py` (atomic write-temp-rename with failure injection) |
| `tests/test_results_index.py` | unit test | — | `tests/test_train_integration.py::test_csv_*` (CSV header + row shape + append) |
| `tests/test_wandb_preflight.py` | unit test | — | `tests/test_wandb_logger.py` (mode-aware noop + env var handling) |
| `tests/test_eval_e2e.py` | integration test | — | `tests/test_train_e2e.py` (full run on synthetic data) |

### Modified tests

| Modified Test | Role | Data Flow | Closest Analog |
|---------------|------|-----------|----------------|
| `tests/conftest.py` | pytest fixtures | — | itself (add `test_anno_path`, `eval_run_dir`, `synthetic_ucf_features`, `synthetic_i3d_features` fixtures parallel to existing `splits_dir`, `tmp_feature_dir`) |

### New data

| File | Role | Data Flow | Closest Analog |
|------|------|-----------|----------------|
| `data/annotations/ucf_temporal.txt` | static text (Sultani 2018 download) | file-I/O (read-only) | `data/splits/ucf_*.txt` (git-tracked small data files) — directory parallel |

## Pattern Assignments

### `src/evaluate.py` (CLI entry, request-response)

**Analog:** `src/train.py`

**Entry-point shape** (lines 1-5, 34-53, 138-153, 206-207):
```python
# src/train.py lines 1-5 — CUBLAS_WORKSPACE_CONFIG before torch import
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

# Standard imports come AFTER the env var is set.
import argparse
```
Phase 4 note: evaluate.py is pure-inference under no_grad, so the CUBLAS env var is
strictly optional, but copying the pattern ensures bit-identical Phase 3 re-evaluation.

**Script-mode bootstrap** (lines 13-18):
```python
# Script-mode bootstrap: when invoked as `python src/train.py` (not
# `python -m src.train`), ensure the project root is on sys.path so the
# `src.*` package imports below resolve.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
```
Copy verbatim.

**Argparse shape** (lines 34-53):
```python
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="ViolenceCC training entry point (TRN-06)")
    ap.add_argument("--config", required=True, help="Path to variant YAML config")
    ap.add_argument("--seed", type=int, default=None, help="Override cfg['seed']")
    ...
    return ap.parse_args(argv)


def apply_cli_overrides(cfg: dict, args) -> dict:
    if args.seed is not None:
        cfg["seed"] = args.seed
    ...
    return cfg
```
For evaluate.py: `--run-dir` (required) + `--split {val|test}` (default=test) per D-06/D-09.

**Run-dir + snapshot load** (lines 139-153):
```python
args = parse_args(argv)
cfg = load_config(args.config)
cfg = apply_cli_overrides(cfg, args)

# Reproducibility first (TRN-03)
set_deterministic(int(cfg["seed"]))

device = "cuda" if torch.cuda.is_available() else "cpu"

# Run dir (D-14)
run_dir = Path(cfg["paths"]["results_dir"]) / run_name(cfg)
run_dir.mkdir(parents=True, exist_ok=True)
snapshot_config(cfg, run_dir / "config_snapshot.json")
```
For evaluate.py: `run_dir = Path(args.run_dir)`; then
`cfg = load_config(run_dir / "config_snapshot.json")` (uses `load_snapshot_as_config`).

**`main(argv=None) -> int` + `__main__` entry**:
```python
def main(argv=None) -> int:
    args = parse_args(argv)
    ...
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**Model load + inference pattern** (lines 160-167):
```python
model = build_model(**cfg["model"]).to(device)
...
best_path = run_dir / "best_model.pth"
```
Phase 4: after build, `model.load_state_dict(load_checkpoint(best_path))` then
`model.eval()` before the no_grad inference loop.

---

### `src/eval/test_loader.py` (data loader, CRUD)

**Analog:** `src/data/dataset.py` + new sys.argv guard from RESEARCH.md §Pattern 1

**Dataset construction pattern** (from dataset.py lines 66-131):
```python
class MILFeatureDataset(Dataset):
    def __init__(
        self,
        split_file: str,
        skel_dir: str,
        clip_dir: str,
        T: int = 32,
        mode: str = "train",
        seed: int = 42,
        dataset: str = "ucf",
    ) -> None:
        if mode not in ("train", "val", "test"):
            raise ValueError(f"mode must be train|val|test, got {mode!r}")
        ...
        self.video_ids: List[str] = [vid for vid in all_ids if self._is_loadable(vid)]
```
Copy the "filter unloadable videos" idiom; test_loader skips missing test feature files
the same way.

**Full-length test-mode pattern** (dataset.py lines 171-186):
```python
if self.mode == "test":
    # D-12: return all snippets, no sampling
    skel_t = torch.from_numpy(skel.astype(np.float32))
    clip_t = torch.from_numpy(clip.astype(np.float32))
    mask = torch.ones(N, dtype=torch.float32)
...
return {
    "skel": skel_t, "clip": clip_t, "mask": mask,
    "label": float(label), "video_id": vid,
}
```
Phase 4 test_loader returns the same dict shape for the UCF path; the I3D path returns
`{"i3d": ..., "label": ..., "video_id": ...}`.

**Sys.argv guard pattern** (from RESEARCH.md §Pattern 1 — new, no existing analog):
```python
import sys
from pathlib import Path

_ALLOWED_SENTINELS = ("evaluate.py",)
_PYTEST_SENTINELS = ("pytest", "py.test")

def _assert_called_from_evaluate_or_pytest() -> None:
    argv0 = Path(sys.argv[0]).name if sys.argv else ""
    if argv0 in _ALLOWED_SENTINELS:
        return
    if any(s in argv0 for s in _PYTEST_SENTINELS):
        return
    raise RuntimeError(
        f"src/eval/test_loader.py was imported by sys.argv[0]={argv0!r}. ..."
    )

_assert_called_from_evaluate_or_pytest()   # fires at module import time
```

---

### `src/eval/snippet_to_frame.py` (utility, transform)

**Analog:** `src/losses/mil_loss.py` (pure function with clear contract + asserts)

**Pure-function signature + docstring shape** (mil_loss.py lines 52-84):
```python
def mil_ranking_loss(
    scores: torch.Tensor,    # [2B, T] sigmoid scores in [0,1]
    mask: torch.Tensor,      # [2B, T] 1.0 where real, 0.0 where padded
    n_normal: int,           # B (= 16 per D-04)
    k: int = 3,              # D-01
    margin: float = 1.0,     # D-02
    ...
) -> torch.Tensor:
    """Top-k MIL Ranking Loss with sparsity + smoothness. Masked for padded positions."""
    ...
```
Copy this docstring style: shape annotations inline, decision references (D-XX),
pure torch/numpy, no side effects.

**Expansion body** (from RESEARCH.md §Pattern 2):
```python
expanded = np.repeat(scores, snippet_window)
if upsample_factor > 1:
    expanded = np.repeat(expanded, upsample_factor)
tol = snippet_window * upsample_factor
if abs(len(expanded) - n_frames) > 2 * tol:
    raise AssertionError(...)
if len(expanded) < n_frames:
    pad = np.full(n_frames - len(expanded), expanded[-1], dtype=expanded.dtype)
    return np.concatenate([expanded, pad])
return expanded[:n_frames]
```

---

### `src/eval/metrics.py` (metric utility, transform)

**Analog:** `src/losses/mil_loss.py`

**Length-assertion pattern before sklearn calls** (from RESEARCH.md §Example 5):
```python
from sklearn.metrics import roc_auc_score, average_precision_score

for vid in per_video_scores:
    s, y = per_video_scores[vid], per_video_labels[vid]
    assert len(s) == len(y), f"C4 REGRESSION at {vid}: scores={len(s)} labels={len(y)}"
    all_scores.append(s); all_labels.append(y)

y_score = np.concatenate(all_scores)
y_true = np.concatenate(all_labels)
assert len(y_score) == len(y_true)

result = {
    "auc": float(roc_auc_score(y_true, y_score)),
    "ap": float(average_precision_score(y_true, y_score)),
    ...
}
```
Copy D-15 mandated length assertions BEFORE every sklearn call.

---

### `src/eval/ucf_annotations.py` (parser, file-I/O)

**Analog:** `src/data/dataset.py::_load_split` (text file parse); RESEARCH.md §Example 1

**File-parse pattern** (dataset.py lines 134-137):
```python
@staticmethod
def _load_split(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
```

**Full annotation parser** (from RESEARCH.md §Example 1):
```python
@dataclass(frozen=True)
class VideoAnnotation:
    video_id: str
    category: str
    intervals: tuple

def parse_annotations(path: Path) -> Dict[str, VideoAnnotation]:
    annos = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split()
            if len(parts) != 6:
                raise ValueError(...)
            ...
    return annos
```

---

### `src/models/rtfm_i3d.py` (model variant, request-response)

**Analog:** `src/models/skeleton_only.py`

**Single-modality wrapper shape** (skeleton_only.py lines 15-44):
```python
class SkeletonProj(nn.Module):
    """Skeleton-only MIL head baseline (MOD-03).

    Inputs:
      skel: float tensor [B, T, skel_dim]
      clip: ignored (keyword-only, for variant-uniform forward signature)
      mask: ignored here (applied at loss time by mil_ranking_loss)
    Output:
      scores: float tensor [B, T] in [0, 1]
    """
    def __init__(
        self,
        skel_dim: int = 256,
        head_hidden=(128, 32),
        dropout: float = 0.3,
        **unused,
    ) -> None:
        super().__init__()
        self.ln_skel = nn.LayerNorm(skel_dim)        # D-07: named LN for TTA
        self.head = MILHead(input_dim=skel_dim,
                            hidden_dims=tuple(head_hidden),
                            dropout=dropout)

    def forward(self, skel=None, clip=None, mask=None):
        if skel is None:
            raise ValueError("SkeletonProj requires `skel` input")
        x = self.ln_skel(skel)
        scores = self.head(x)
        return scores.squeeze(-1)                     # [B, T]
```

**RTFM-specific adaptation** (from RESEARCH.md §Pattern 5):
```python
class RTFMI3D(nn.Module):
    def __init__(self, i3d_dim: int = 1024, head_hidden=(128, 32), dropout: float = 0.3, **unused):
        super().__init__()
        self.ln_i3d = nn.LayerNorm(i3d_dim)           # named LN, parallel to ln_skel
        self.head = MILHead(input_dim=i3d_dim, hidden_dims=tuple(head_hidden), dropout=dropout)

    def forward(self, skel=None, clip=None, i3d=None, mask=None):
        if i3d is None:
            raise ValueError("RTFMI3D requires `i3d` input (1024-d per snippet)")
        x = self.ln_i3d(i3d)
        scores = self.head(x).squeeze(-1)
        return scores
```
Mirrors the exact SkeletonProj shape: named LN + MILHead + variant-uniform forward.

---

### `src/data/i3d_dataset.py` (torch Dataset, CRUD)

**Analog:** `src/data/dataset.py::MILFeatureDataset`

**Filter-unloadable pattern** (dataset.py lines 127-155):
```python
all_ids = self._load_split(split_file)
self.video_ids: List[str] = [vid for vid in all_ids if self._is_loadable(vid)]
...

def _is_loadable(self, vid: str) -> bool:
    skel_p = self.skel_dir / f"{vid}.npy"
    clip_p = self.clip_dir / f"{vid}.npy"
    if not skel_p.exists() or not clip_p.exists():
        return False
    try:
        skel = np.load(skel_p, mmap_mode="r")
    except Exception:
        return False
    if skel.shape[0] == 0:
        return False
    return True
```
Phase 4 I3D adaptation: check `{vid}__0.npy` existence (crop 0 is sufficient; later
crops pad from crop 0 per D-19 + Pitfall 4).

**Startup log for filtered count** (from RESEARCH.md §Example 2):
```python
print(f"[i3d_dataset] {mode}: {len(self.video_ids)}/{len(ids)} videos available")
```

**5-crop train/test dispatch** (from RESEARCH.md §Example 2):
```python
if self.mode == "test":
    # D-19: average crops at test time → [N, 1024]
    feats = crops.mean(axis=0).astype(np.float32)
    return {"i3d": torch.from_numpy(feats), "label": float(label), "video_id": vid}
else:
    resampled = np.stack([self._resample_T(crops[c]) for c in range(self.n_crops)], axis=0)
    return {"i3d": torch.from_numpy(resampled.astype(np.float32)),
            "label": float(label), "video_id": vid}
```

---

### `src/models/registry.py` (modified, registry)

**Analog:** itself — extend with 5th lazy factory

**Extension pattern** (registry.py lines 13-35):
```python
# Lazy factories: import the class on first call. This avoids ImportError
# when Plans 04/05 have not yet populated the implementation files.
def _get_skeleton_only():
    from src.models.skeleton_only import SkeletonProj
    return SkeletonProj

...

def _get_gated_fusion():
    from src.models.gated_fusion import GatedFusion
    return GatedFusion

MODEL_REGISTRY: Dict[str, Callable] = {
    "skeleton_only": _get_skeleton_only,
    "clip_only":     _get_clip_only,
    "late_fusion":   _get_late_fusion,
    "gated_fusion":  _get_gated_fusion,
}
```
Add sibling:
```python
def _get_rtfm_i3d():
    from src.models.rtfm_i3d import RTFMI3D
    return RTFMI3D

MODEL_REGISTRY["rtfm_i3d"] = _get_rtfm_i3d
```

---

### `src/data/dataset.py` (modified, CRUD)

**Analog:** itself — extend `__init__` and `__getitem__`

**Parameter-add pattern** — D-21 adds `skel_agg` field:
Insert after `dataset: str = "ucf"` in `__init__` signature (line 112):
```python
skel_agg: str = "none",   # D-21: none | concat | max | mean
```
Guard in body:
```python
if skel_agg not in ("none", "concat", "max", "mean"):
    raise ValueError(f"skel_agg must be none|concat|max|mean, got {skel_agg!r}")
self.skel_agg = skel_agg
```

**3D cache reshape in `__getitem__`** (new):
Insert after `skel = np.load(...)` (line 163) and before the `skel.shape[0] == clip.shape[0]`
assert (line 165):
```python
# Phase 4 D-21: [N, 2, 256] 2-person cache → aggregate on load
if skel.ndim == 3 and skel.shape[1] == 2:
    if self.skel_agg == "concat":
        skel = skel.reshape(skel.shape[0], -1)   # [N, 512]
    elif self.skel_agg == "max":
        skel = skel.max(axis=1)                  # [N, 256]
    elif self.skel_agg == "mean":
        skel = skel.mean(axis=1)                 # [N, 256]
    else:
        raise ValueError(
            f"2-person cache requires cfg.data.skel_agg; got 'none' for {vid}"
        )
```

---

### `src/utils/config.py` (modified, transform)

**Analog:** itself — add helpers parallel to `_git_info()`

**Existing helper pattern** (config.py lines 44-66):
```python
def _git_info() -> dict:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        sha = "unknown"
        dirty = False
    return {"sha": sha, "dirty": dirty}
```

**New helpers** (from RESEARCH.md §Pattern 4):
```python
def config_hash(cfg: dict) -> str:
    """SHA256 of sort_keys=True JSON — whitespace + order invariant (D-12)."""
    serializable = json.loads(json.dumps(cfg, default=str))   # Path → str
    payload = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def checkpoint_sha(path: Path) -> str:
    """SHA256 of best_model.pth raw bytes, streamed in 1 MB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    """git rev-parse HEAD + `-dirty` suffix if working tree dirty (D-12)."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL
        ).strip())
        return sha + ("-dirty" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"
```
`git_sha()` is a new user-facing wrapper of `_git_info()` that returns the suffixed
string format for eval_metrics.json (D-12).

---

### `src/utils/wandb_logger.py` (modified, event-driven)

**Analog:** itself — extend `__init__` with offline-fallback branch

**Existing init pattern** (wandb_logger.py lines 42-58):
```python
try:
    self.run = wandb.init(
        project=wcfg.get("project", "violencecc"),
        entity=entity,
        mode=mode,
        id=run_id,
        resume="allow",
        name=run_id,
        config=cfg,
        dir=str(run_dir),
        tags=wcfg.get("tags", []),
    )
except Exception:
    # Any wandb-side initialization failure (network hiccup, login,
    # directory permissions) must not halt training. Degrade to noop.
    self.run = None
    return
```

**D-40 offline-fallback branch** (new — per RESEARCH.md Pitfall 6):
Replace the bare `except Exception:` with an explicit 2-level catch:
```python
except wandb.errors.Error as exc:
    # D-40: auth or network failure → re-init with mode=offline, log warning.
    try:
        self.run = wandb.init(
            project=wcfg.get("project", "violencecc"),
            mode="offline",
            id=run_id,
            resume="allow",
            name=run_id,
            config=cfg,
            dir=str(run_dir),
            tags=wcfg.get("tags", []),
        )
        print(f"[wandb] offline fallback after {type(exc).__name__}: {exc}",
              flush=True)
    except Exception:
        self.run = None
    return
except Exception:
    self.run = None
    return
```

---

### `src/utils/csv_logger.py` (modified, file-I/O)

**Analog:** itself — add `results_index_append()` sibling function

**Existing CSVLogger pattern** (csv_logger.py lines 10-39):
```python
class CSVLogger:
    def __init__(
        self,
        path: Union[str, Path],
        fieldnames: Iterable[str] = ("epoch", "train_loss", "val_loss", "lr"),
    ) -> None:
        self.path = Path(path)
        self.fieldnames = list(fieldnames)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Write header only if file is new / empty
        if not self.path.exists() or self.path.stat().st_size == 0:
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=self.fieldnames)
                w.writeheader()
                f.flush()
                os.fsync(f.fileno())

    def log(self, **kwargs) -> None:
        row = {k: kwargs.get(k, "") for k in self.fieldnames}
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            w.writerow(row)
            f.flush()
            os.fsync(f.fileno())
```

**New function** (D-33) — mirrors the append + header-if-new + fsync pattern without
instantiating a class (suits one-shot appends from `run_ablations.py`):
```python
RESULTS_INDEX_COLUMNS = [
    "run_name", "variant", "dataset", "seed", "cache_variant",
    "auc", "ap", "n_videos", "n_frames", "start_time", "end_time", "config_hash",
]

def results_index_append(path: Union[str, Path], row: dict) -> None:
    """Append one run row to results/results-index.csv (D-33).

    Header written on first open; subsequent opens append. flush+fsync so a
    crash after N rows preserves rows 0..N-1 on disk.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULTS_INDEX_COLUMNS)
        if write_header:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in RESULTS_INDEX_COLUMNS})
        f.flush()
        os.fsync(f.fileno())
```

---

### `src/train.py` (modified, CLI)

**Analog:** itself — add `--run-name` CLI arg and use when provided

**Existing parse_args** (train.py lines 34-43):
```python
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="ViolenceCC training entry point (TRN-06)")
    ap.add_argument("--config", required=True, help="Path to variant YAML config")
    ap.add_argument("--seed", type=int, default=None, help="Override cfg['seed']")
    ap.add_argument("--epochs", type=int, default=None,
                    help="Override cfg['train']['epochs'] (for smoke tests)")
    ap.add_argument("--results-dir", type=str, default=None,
                    help="Override cfg['paths']['results_dir']")
    return ap.parse_args(argv)
```

**Add run-name argument and use it at dir creation time** (lines 56-59, 148-149):
```python
# ADD in parse_args():
ap.add_argument("--run-name", type=str, default=None,
                help="Override the default run_name() value (D-30: deterministic dirs)")

# CHANGE in main():
run_dir_name = args.run_name if args.run_name else run_name(cfg)
run_dir = Path(cfg["paths"]["results_dir"]) / run_dir_name
```
The existing `run_name(cfg)` timestamped format (line 56-59) is preserved as the
fallback for ad-hoc / debug runs per D-30.

---

### `scripts/run_ablations.py` (orchestrator, batch)

**Analog:** `scripts/extract_ctrgcn.py` (CLI + queue + resume + error log)

**Argparse entry + PROJECT_ROOT constants** (extract_ctrgcn.py lines 52-57, 498-535):
```python
PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
...

def main() -> None:
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--dataset", choices=["ucf", "xd"], required=True, ...)
    parser.add_argument("--split", choices=["train", "val", "test"], required=True, ...)
    parser.add_argument("--limit", type=int, default=None, ...)
    parser.add_argument("--device", default="cuda", ...)
    args = parser.parse_args()

    run_extraction(args.dataset, args.split, limit=args.limit, device=args.device)
```

**Resume probe + error log** (extract_ctrgcn.py lines 339-409):
```python
error_log_path = output_dir / "errors.log"
...
for video_id in video_ids:
    # Skip-if-exists resume logic (D-14) — validate file is non-trivial
    output_path = output_dir / f"{video_id}.npy"
    if output_path.exists() and output_path.stat().st_size > 128:
        skipped += 1
        pbar.update(1)
        continue
    ...
    try:
        feats = extract_video_features(...)
        ...
    except Exception as exc:
        failed += 1
        error_msg = f"{video_id}\t{type(exc).__name__}: {exc}"
        logger.error(f"FAILED: {error_msg}")
        with open(error_log_path, "a") as ef:
            ef.write(error_msg + "\n")
```
Phase 4 adaptation: the probe is `(run_dir / ".done").exists()` instead of output_path.exists();
the error log is the project-level `runner-errors.log` (D-32).

**Subprocess invocation + CalledProcessError handling** (from RESEARCH.md §Example 3):
```python
train_cmd = [sys.executable, "src/train.py",
             "--config", spec.config,
             "--seed", str(spec.seed),
             "--results-dir", str(spec.run_dir.parent),
             "--run-name", spec.run_name]
try:
    subprocess.run(train_cmd, check=True, timeout=timeout_s,
                   cwd=str(PROJECT), stdout=sys.stdout, stderr=sys.stderr)
except subprocess.CalledProcessError as e:
    status["phase"] = "train_failed"
    log_error(spec, e)
    return status
```

**Atomic `.done` marker** (from RESEARCH.md §Pattern 3 + checkpoint.py lines 17-45):
```python
# src/utils/checkpoint.py pattern:
fd, tmp_path = tempfile.mkstemp(
    prefix=f".{path.name}.",
    suffix=".tmp",
    dir=str(path.parent),
)
try:
    with os.fdopen(fd, "wb") as f:
        torch.save(state_dict, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, str(path))
except Exception:
    if os.path.exists(tmp_path):
        try: os.unlink(tmp_path)
        except OSError: pass
    raise
```
Copy this `.done` marker writer; replace the `torch.save` line with `f.write("eval_complete\n")`.

---

### `scripts/wandb_preflight.py` (check script, request-response)

**Analog:** `scripts/verify_alignment.py` (CLI + exit code script)

**Exit-code CLI shape** (verify_alignment.py lines 465-517):
```python
def main() -> None:
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--dataset", choices=["ucf", "xd"], required=True, ...)
    ...
    args = parser.parse_args()
    exit_code = run_verification(...)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

**Full preflight body** (from RESEARCH.md §Example 4):
```python
import os, sys

def main() -> int:
    if os.environ.get("WANDB_API_KEY"):
        print("[preflight] wandb: WANDB_API_KEY env var set")
        return 0
    try:
        import wandb
    except ImportError:
        print("[preflight] wandb not installed; CSV-only mode is fine "
              "if all configs set wandb.mode=disabled")
        return 0
    if wandb.api.api_key is not None:
        print("[preflight] wandb: api_key discovered via ~/.netrc or settings")
        return 0
    sys.stderr.write(
        "ERROR: wandb is not configured.\n"
        "Run one of:\n"
        "  (1) export WANDB_API_KEY=<your key>\n"
        "  (2) wandb login   # interactive one-time\n"
        "  (3) set `wandb.mode: disabled` in every config YAML (CSV-only mode)\n"
    )
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
```

---

### `scripts/verify_pooling_caches.py` (sanity check, CRUD)

**Analog:** `scripts/verify_alignment.py`

**Dataclass-driven per-video result + PASS/FAIL/SKIP aggregation** (verify_alignment.py
lines 75-83, 90-275, 371-459):
```python
@dataclass
class VideoResult:
    video_id: str
    status: str   # 'pass', 'fail', 'skip'
    failures: List[str] = field(default_factory=list)
    n_skel: Optional[int] = None
    n_clip: Optional[int] = None
    ...

def verify_video(video_id: str, dataset: str, verbose: bool = False) -> VideoResult:
    result = VideoResult(video_id=video_id, status="pass")
    ...

    # ---- Aggregate ----
passes = [r for r in results if r.status == "pass"]
fails  = [r for r in results if r.status == "fail"]
skips  = [r for r in results if r.status == "skip"]
```

**Specific sanity checks** (from RESEARCH.md §Pattern 6):
```python
# For every video ID in the existing E:/features/ucf/clip/ cache:
#   mean_cache[vid].shape == (mean_max_cache[vid].shape[0], 512)
#   np.allclose(mean_cache[vid], mean_max_cache[vid][:, :512]) within float32 eps
#
# For skeleton_2person/*.npy:
#   keep_persons_cache[vid].shape == (N, 2, 256)
```

---

### `scripts/extract_ctrgcn.py` (modified, batch file-I/O)

**Analog:** itself — add `--keep-persons` flag

**Existing CLI + pooling site** (lines 229-235, 498-527):
```python
# Current extract_stream_feature collapses M dim (line 234):
out = model.backbone(x)         # [1, M, 256, T', V']
feat = out.mean(dim=[1, 3, 4])  # [1, 256]   ← M collapsed here

# argparse:
parser.add_argument("--device", default="cuda", ...)
# ADD:
parser.add_argument("--keep-persons", action="store_true",
                    help="D-21: emit [N, 2, 256] per-person tensor to skeleton_2person/")
```

**D-21 branching** — preserve M, produce `[N, 2, 256]`:
```python
if keep_persons:
    # Pool T', V' but keep M: [1, M, 256, T', V'] → [1, M, 256] → [M, 256]
    feat = out.mean(dim=[3, 4]).squeeze(0)   # [M=2, 256]
    # Upstream snippet_feats append stacks → final [N, 2, 256] via torch.stack
else:
    feat = out.mean(dim=[1, 3, 4])           # [1, 256]   ← existing default
```
Output dir branches at the top: `FEATURE_ROOT / dataset / ("skeleton_2person" if keep_persons
else "skeleton")`.

---

### `scripts/extract_clip.py` (modified, batch file-I/O)

**Analog:** itself — add `--pool={mean|mean_max}` flag

**Existing concat site** (lines 298-302, 593-626):
```python
# Current (lines 298-300):
mean_feat = embeddings.mean(dim=0)         # [512]
max_feat = embeddings.max(dim=0).values    # [512]
concat = torch.cat([mean_feat, max_feat], dim=0)  # [1024]

# argparse:
parser.add_argument("--batch-size", type=int, default=64, ...)
# ADD:
parser.add_argument("--pool", choices=["mean", "mean_max"], default="mean_max",
                    help="D-23: mean_max (default, [N,1024]) or mean ([N,512])")
```

**D-23 branching**:
```python
if pool == "mean":
    feat = mean_feat                     # [512]
else:
    feat = torch.cat([mean_feat, max_feat], dim=0)  # [1024]
```
Output dir branches: `FEATURE_ROOT / dataset / ("clip_mean" if pool == "mean" else "clip")`.
The shape assertion (line 372-375) adjusts to check against `expected_dim` (512 or 1024).

---

### `configs/rtfm_i3d.yaml` (new YAML config)

**Analog:** `configs/skeleton_only.yaml` (single-modality variant YAML)

**Full template** (skeleton_only.yaml):
```yaml
# configs/skeleton_only.yaml
# MOD-03 Skeleton-Only MIL baseline. Single-modal; no CLIP reference.
seed: 42
dataset: ucf

paths:
  skeleton_features: "E:/features/ucf/skeleton"
  clip_features: "E:/features/ucf/clip"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: skeleton_only
  skel_dim: 256
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
  mode: online
  tags: [phase3, skeleton_only, ucf]
```

**Phase 4 adaptation for rtfm_i3d.yaml**:
```yaml
# configs/rtfm_i3d.yaml
# Phase 4 D-18: RTFM variant on XD-Violence I3D features (harness gate)
seed: 42
dataset: xd_i3d            # new dataset key; loader dispatches on it (D-36)

paths:
  i3d_features: "E:/i3d-features/i3d-features"   # D-20 new key
  splits_dir: "data/splits"
  results_dir: "results"
  # skeleton_features / clip_features intentionally absent (D-36)

model:
  variant: rtfm_i3d         # D-18 registry key
  i3d_dim: 1024
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32
  batch_size: 3              # D-19 + Pitfall 3: reduced from 16 to counter 5× crop inflation
  num_workers: 4
  pin_memory: true

train:
  # Same TRN-01 / D-01 / D-02 / D-03 values as other variants
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
  mode: online
  tags: [phase4, rtfm_i3d, xd_i3d, i3d_rgb]     # D-41 tag format
```

---

### `configs/gated_fusion_2person.yaml` (new YAML config)

**Analog:** `configs/gated_fusion.yaml` (full template)

**Copy with 3 changes** (from gated_fusion.yaml lines 1-41):
```yaml
# configs/gated_fusion_2person.yaml
# Phase 4 D-22: 2-person multi-person aggregation ablation (concat only)
seed: 42
dataset: ucf

paths:
  skeleton_features: "E:/features/ucf/skeleton_2person"   # ← CHANGED (D-24)
  clip_features: "E:/features/ucf/clip"
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: gated_fusion
  skel_dim: 512              # ← CHANGED from 256 (D-22: concat produces 2×256)
  clip_dim: 1024
  shared_dim: 256
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32
  batch_size: 16
  num_workers: 4
  pin_memory: true
  skel_agg: concat           # ← NEW field (D-22, D-37)

train:
  # identical to gated_fusion.yaml
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
  mode: online
  tags: [phase4, gated_fusion, ucf, 2person]     # D-41 tag format
```

---

### `configs/gated_fusion_clip_mean.yaml` (new YAML config)

**Analog:** `configs/gated_fusion.yaml`

**Copy with 3 changes**:
```yaml
# configs/gated_fusion_clip_mean.yaml
# Phase 4 D-23: CLIP mean-only pooling ablation
seed: 42
dataset: ucf

paths:
  skeleton_features: "E:/features/ucf/skeleton"
  clip_features: "E:/features/ucf/clip_mean"      # ← CHANGED (D-24)
  splits_dir: "data/splits"
  results_dir: "results"

model:
  variant: gated_fusion
  skel_dim: 256
  clip_dim: 512              # ← CHANGED from 1024 (D-23)
  shared_dim: 256
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
  mode: online
  tags: [phase4, gated_fusion, ucf, clip_mean]    # D-41 tag format
```

---

### `tests/conftest.py` (modified, fixtures)

**Analog:** itself — add sibling fixtures

**Existing fixture shape** (conftest.py lines 21-57):
```python
@pytest.fixture
def splits_dir():
    return PROJECT_ROOT / "data" / "splits"


@pytest.fixture
def tmp_feature_dir(tmp_path):
    """Writable temp dir shaped like features/{dataset}/{modality}/*.npy."""
    (tmp_path / "skeleton").mkdir()
    (tmp_path / "clip").mkdir()
    return tmp_path


@pytest.fixture
def synth_skel_features():
    """Callable returning [N, 256] float32 skeleton features."""
    from tests.fixtures.synthetic import make_skel
    return make_skel
```

**New Phase 4 fixtures** (parallel shape):
```python
@pytest.fixture
def test_anno_path():
    """Real UCF Temporal_Anomaly_Annotation.txt (D-04, git-tracked)."""
    p = PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    if not p.exists():
        pytest.skip("ucf_temporal.txt not yet downloaded (D-04)")
    return p


@pytest.fixture
def eval_run_dir(tmp_path):
    """Writable temp run dir shaped like results/<run_name>/ with a stub best_model.pth
    and config_snapshot.json — used by test_evaluate_cli.py."""
    d = tmp_path / "eval_run"
    d.mkdir()
    return d


@pytest.fixture
def synthetic_ucf_features():
    """Callable returning a small UCF test set: 10 videos with [N, 256] skel + [N, 1024]
    clip + synthetic ucf_temporal.txt annotation rows. Returns a temp dir shaped
    like E:/features/ucf/."""
    from tests.fixtures.synthetic import make_synthetic_ucf
    return make_synthetic_ucf


@pytest.fixture
def synthetic_i3d_features(tmp_path):
    """Writable temp dir shaped like E:/i3d-features/i3d-features/ with 5 crops
    per video. Returns the dir Path."""
    from tests.fixtures.synthetic import make_synthetic_i3d
    return make_synthetic_i3d(tmp_path)
```

`tests/fixtures/synthetic.py` gets two new factory functions (`make_synthetic_ucf`,
`make_synthetic_i3d`) that follow the existing `make_skel` / `make_clip` shape
(synthetic.py lines 11-37).

---

### `tests/test_snippet_to_frame.py` (new unit test)

**Analog:** `tests/test_mil_loss.py` (pattern inferred — pure-function unit test)

**Test structure pattern**: Use parameterized fixtures with known expected lengths.
Representative test cases (from RESEARCH.md Pitfall 1 + §Validation Architecture):

```python
import numpy as np
import pytest

from src.eval.snippet_to_frame import snippet_to_frame


def test_single_repeat_i3d():
    """XD I3D path: N=10 snippets × window=16 → 160-frame expansion."""
    scores = np.linspace(0, 1, 10).astype(np.float32)
    frames = snippet_to_frame(scores, n_frames=160, snippet_window=16)
    assert len(frames) == 160
    # first 16 frames should all have scores[0]
    assert np.allclose(frames[:16], scores[0])


def test_compound_repeat_ucf():
    """UCF path: N=5 snippets × 64 PNG × 10 upsample → 3200 frames."""
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=3200, snippet_window=64,
                              upsample_factor=10)
    assert len(frames) == 3200


def test_tail_pad_short():
    """expanded < n_frames → pad with last score."""
    scores = np.array([0.5], dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=20, snippet_window=16)
    assert len(frames) == 20
    assert np.allclose(frames[-4:], 0.5)


def test_tail_truncate_long():
    """expanded > n_frames → truncate."""
    scores = np.ones(10, dtype=np.float32)
    frames = snippet_to_frame(scores, n_frames=140, snippet_window=16)
    assert len(frames) == 140


def test_drift_exceeds_tolerance_raises():
    """n_frames off by > 2*tol → AssertionError."""
    scores = np.ones(2, dtype=np.float32)   # 2 × 16 = 32 expanded
    with pytest.raises(AssertionError, match="length drift"):
        snippet_to_frame(scores, n_frames=200, snippet_window=16)
```

---

### `tests/test_ucf_annotations.py` (new unit test)

**Analog:** `tests/test_splits.py` (text parsing test pattern — file not shown but
follows same shape as `test_config.py` round-trip tests)

**Test structure pattern**:
```python
import pytest
from pathlib import Path
from src.eval.ucf_annotations import parse_annotations, frame_labels


def test_parse_normal_video(tmp_path):
    """Normal row: -1 -1 -1 -1 → intervals all None, is_normal=True."""
    f = tmp_path / "anno.txt"
    f.write_text("Normal_Videos_003_x264.mp4  Normal  -1  -1  -1  -1\n")
    annos = parse_annotations(f)
    assert "Normal_Videos_003" in annos
    assert annos["Normal_Videos_003"].is_normal


def test_parse_single_interval(tmp_path):
    """Abuse028: single interval (165, 240), second is -1 -1."""
    f = tmp_path / "anno.txt"
    f.write_text("Abuse028_x264.mp4  Abuse  165  240  -1  -1\n")
    annos = parse_annotations(f)
    a = annos["Abuse028"]
    assert a.category == "Abuse"
    assert a.intervals[0] == (165, 240)
    assert a.intervals[1] == (None, None)


def test_parse_double_interval(tmp_path):
    """Arson011: two intervals."""
    f = tmp_path / "anno.txt"
    f.write_text("Arson011_x264.mp4  Arson  150  420  680  1267\n")
    annos = parse_annotations(f)
    a = annos["Arson011"]
    assert a.intervals[0] == (150, 420)
    assert a.intervals[1] == (680, 1267)


def test_frame_labels_union(tmp_path):
    """D-16: per-frame label = union of both intervals."""
    f = tmp_path / "anno.txt"
    f.write_text("X_x264.mp4  Arson  10  20  30  40\n")
    annos = parse_annotations(f)
    labels = frame_labels(annos["X"], n_frames=50)
    assert labels[:10].sum() == 0
    assert labels[10:20].sum() == 10
    assert labels[20:30].sum() == 0
    assert labels[30:40].sum() == 10
    assert labels[40:].sum() == 0


def test_malformed_row_raises(tmp_path):
    """6-column contract — fewer or more columns raises."""
    f = tmp_path / "anno.txt"
    f.write_text("TooFewCols  Abuse  10  20\n")
    with pytest.raises(ValueError, match="Expected 6 columns"):
        parse_annotations(f)
```

---

### `tests/test_test_loader_guard.py` (new unit test)

**Analog:** `tests/test_dataset.py` (monkey-patchable module-level side effects) +
RESEARCH.md §Pitfall 2

**Test structure pattern**:
```python
import importlib
import sys
import pytest


def test_import_from_pytest_is_allowed():
    """argv[0] contains 'pytest' → guard returns normally."""
    # This test is itself running under pytest → importing the module works.
    import src.eval.test_loader   # no raise


def test_import_from_evaluate_name_is_allowed(monkeypatch):
    """argv[0] = 'evaluate.py' → guard returns normally."""
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--run-dir", "x"])
    # Need to force re-import to re-trigger the module-level check
    if "src.eval.test_loader" in sys.modules:
        del sys.modules["src.eval.test_loader"]
    import src.eval.test_loader


def test_import_from_unknown_argv_raises(monkeypatch):
    """argv[0] = arbitrary → RuntimeError."""
    monkeypatch.setattr(sys, "argv", ["malicious_tool.py"])
    if "src.eval.test_loader" in sys.modules:
        del sys.modules["src.eval.test_loader"]
    with pytest.raises(RuntimeError, match="src/eval/test_loader.py was imported"):
        import src.eval.test_loader
```

---

### `tests/test_evaluate_cli.py` (new integration test)

**Analog:** `tests/test_train_e2e.py`

**E2E harness shape** (test_train_e2e.py lines 27-70):
```python
def _build_synth_features_and_splits(root):
    splits = root / "splits"
    splits.mkdir(parents=True, exist_ok=True)
    skel = root / "features" / "skeleton"
    skel.mkdir(parents=True, exist_ok=True)
    ...
    train_nor = [f"Normal_Videos_event_{i}_x264" for i in range(10)]
    ...
    for v in train_nor + train_abn + val_nor + val_abn:
        rng = np.random.default_rng(abs(hash(v)) & 0xFFFF)
        np.save(skel / f"{v}.npy", rng.standard_normal((40, 256)).astype(np.float32))
    ...
    return results, splits, skel, clip
```

**Phase 4 adaptation**:
1. Synthesize a small 10-video UCF test set (split, skel, clip, ucf_temporal.txt).
2. Point a `gated_fusion.yaml` copy at the synthetic dirs; run `src.train.main()` to
   produce `best_model.pth` + `config_snapshot.json` + `train_log.csv`.
3. Invoke `from src.evaluate import main; rc = main(["--run-dir", str(run), "--split", "test"])`.
4. Assert the 4 output artifacts exist: `eval_metrics.json`, `eval_scores.npz`,
   `per_category.csv`, `.done`.
5. Load `eval_metrics.json`; assert all 10 keys from D-11 + D-12 are present.

---

### `tests/test_rtfm_model.py` (new unit test)

**Analog:** `tests/test_models.py::test_skeleton_only_*` (lines 13-36)

**Test pattern** (test_models.py lines 13-45 — 4 parallel tests):
```python
def test_skeleton_only_forward():
    torch.manual_seed(0)
    model = SkeletonProj()
    skel = torch.randn(2, 32, 256)
    out = model(skel=skel)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_skeleton_only_has_named_layernorm():
    model = SkeletonProj()
    ln_names = [n for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)]
    assert "ln_skel" in ln_names
    assert isinstance(model.ln_skel, nn.LayerNorm)
    assert model.ln_skel.normalized_shape == (256,)


def test_skeleton_only_raises_without_skel():
    model = SkeletonProj()
    with pytest.raises(ValueError, match="SkeletonProj requires"):
        model(clip=torch.randn(2, 32, 1024))
```

**Phase 4 RTFMI3D tests** (mirror all 4 shapes):
```python
def test_rtfm_i3d_forward():
    torch.manual_seed(0)
    model = RTFMI3D(i3d_dim=1024)
    i3d = torch.randn(2, 32, 1024)
    out = model(i3d=i3d)
    assert out.shape == (2, 32)
    assert torch.isfinite(out).all()
    assert (out >= 0).all() and (out <= 1).all()


def test_rtfm_i3d_has_named_layernorm():
    model = RTFMI3D()
    assert hasattr(model, "ln_i3d")
    assert isinstance(model.ln_i3d, nn.LayerNorm)
    assert model.ln_i3d.normalized_shape == (1024,)


def test_rtfm_i3d_raises_without_i3d():
    model = RTFMI3D()
    with pytest.raises(ValueError, match="RTFMI3D requires"):
        model(skel=torch.randn(2, 32, 256))


def test_build_model_rtfm_i3d_round_trip():
    model = build_model("rtfm_i3d", i3d_dim=1024)
    from src.models.rtfm_i3d import RTFMI3D
    assert isinstance(model, RTFMI3D)


def test_registry_has_five_keys():
    from src.models.registry import MODEL_REGISTRY
    assert set(MODEL_REGISTRY.keys()) == {
        "skeleton_only", "clip_only", "late_fusion", "gated_fusion", "rtfm_i3d",
    }
```

---

### `tests/test_i3d_loader.py` (new unit test)

**Analog:** `tests/test_dataset.py::_write_video` + `test_train_resample_long`
(lines 17-48)

**Synthetic-fixture pattern** (test_dataset.py lines 17-23):
```python
def _write_video(dir_skel, dir_clip, video_id: str, N: int, seed: int = 0):
    """Write a synthetic [N, 256] skeleton and [N, 1024] CLIP .npy for tests."""
    rng = np.random.default_rng(seed)
    np.save(dir_skel / f"{video_id}.npy",
            rng.standard_normal((N, 256), dtype=np.float32))
    np.save(dir_clip / f"{video_id}.npy",
            rng.standard_normal((N, 1024), dtype=np.float32))
```

**Phase 4 adaptation** — 5-crop I3D synthesis:
```python
def _write_i3d_video(feature_dir, video_id: str, N: int, n_crops: int = 5, seed: int = 0):
    """Write 5 synthetic [N, 1024] I3D crop files named {vid}__{c}.npy."""
    for c in range(n_crops):
        rng = np.random.default_rng(seed + c)
        np.save(feature_dir / f"{video_id}__{c}.npy",
                rng.standard_normal((N, 1024), dtype=np.float32))


def test_test_mode_averages_crops(tmp_path):
    _write_i3d_video(tmp_path, "Fight_label_B1", N=50)
    # split file + construction…
    ds = I3DFeatureDataset(..., mode="test")
    item = ds[0]
    assert item["i3d"].shape == (50, 1024)        # crops averaged


def test_train_mode_returns_all_crops(tmp_path):
    _write_i3d_video(tmp_path, "Fight_label_B1", N=50)
    ds = I3DFeatureDataset(..., mode="train", T=32)
    item = ds[0]
    assert item["i3d"].shape == (5, 32, 1024)     # 5 crops × T=32


def test_missing_crops_filter(tmp_path):
    """Pitfall 4: videos with 0 crops skipped from split."""
    (tmp_path / "A_label_A__0.npy").write_bytes(np.zeros((10, 1024), dtype=np.float32).tobytes())
    # split lists A_label_A AND B_label_A (missing)
    ds = I3DFeatureDataset(split_file=..., feature_dir=str(tmp_path))
    assert "B_label_A" not in ds.video_ids
```

---

### `tests/test_skel_agg.py` (new unit test)

**Analog:** `tests/test_dataset.py::test_train_resample_long` (parametric shape test)

**Test pattern**:
```python
import numpy as np
import pytest
from src.data.dataset import MILFeatureDataset


@pytest.mark.parametrize("skel_agg,expected_dim", [
    ("concat", 512),
    ("max", 256),
    ("mean", 256),
])
def test_skel_agg_dimensions(tmp_feature_dir, tmp_path, skel_agg, expected_dim):
    """D-21: [N, 2, 256] cache + skel_agg produces the right skel_dim."""
    split = tmp_path / "split.txt"
    split.write_text("Fighting001_x264\n")
    # Write [N, 2, 256] cache
    rng = np.random.default_rng(0)
    np.save(tmp_feature_dir / "skeleton" / "Fighting001_x264.npy",
            rng.standard_normal((40, 2, 256), dtype=np.float32))
    np.save(tmp_feature_dir / "clip" / "Fighting001_x264.npy",
            rng.standard_normal((40, 1024), dtype=np.float32))
    ds = MILFeatureDataset(
        split_file=str(split),
        skel_dir=str(tmp_feature_dir / "skeleton"),
        clip_dir=str(tmp_feature_dir / "clip"),
        T=32, mode="train", dataset="ucf", skel_agg=skel_agg,
    )
    item = ds[0]
    assert item["skel"].shape == (32, expected_dim)


def test_skel_agg_missing_raises(tmp_feature_dir, tmp_path):
    """3D cache with skel_agg='none' → explicit rejection."""
    # ... construct cache ...
    ds = MILFeatureDataset(..., skel_agg="none")
    with pytest.raises(ValueError, match="requires cfg.data.skel_agg"):
        _ = ds[0]
```

---

### `tests/test_run_ablations.py` (new integration test)

**Analog:** `tests/test_train_e2e.py` (subprocess + tmp paths)

**Test structure pattern**:
```python
import subprocess
import sys
from pathlib import Path


def test_dry_run_prints_queue(tmp_path):
    """--dry-run exits 0 without invoking train.py."""
    r = subprocess.run(
        [sys.executable, "scripts/run_ablations.py",
         "--queue", "phase4_main", "--dry-run", "--no-preflight"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    assert "[dry-run]" in r.stdout


def test_done_marker_skips_run(tmp_path, monkeypatch):
    """A run dir with .done marker is skipped."""
    run = tmp_path / "results" / "ucf_skeleton_only_s42"
    run.mkdir(parents=True)
    (run / ".done").write_text("eval_complete\n")
    # run_ablations.py probe should skip this spec
    from scripts.run_ablations import is_done
    assert is_done(run)


def test_results_index_append(tmp_path):
    """append_index_row writes one row per run + header on first write."""
    from src.utils.csv_logger import results_index_append, RESULTS_INDEX_COLUMNS
    idx = tmp_path / "results-index.csv"
    results_index_append(idx, {
        "run_name": "ucf_gated_s42", "variant": "gated_fusion",
        "dataset": "ucf", "seed": 42, "auc": 0.85, "ap": 0.42,
    })
    results_index_append(idx, {
        "run_name": "ucf_gated_s123", "variant": "gated_fusion",
        "dataset": "ucf", "seed": 123, "auc": 0.86, "ap": 0.43,
    })
    import csv
    with open(idx) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["run_name"] == "ucf_gated_s42"
```

---

### `tests/test_done_marker.py` (new unit test)

**Analog:** `tests/test_checkpoint.py` (atomic write-temp-rename with failure injection)

**Test pattern** (test_checkpoint.py lines 35-67):
```python
def test_save_atomic_tempfile_cleaned(tmp_path):
    m = torch.nn.Linear(4, 2)
    path = tmp_path / "x.pth"
    save_checkpoint_atomic(m.state_dict(), path)
    # No leftover .tmp or hidden tempfiles next to x.pth
    leftovers = [p for p in tmp_path.iterdir()
                 if p.name != path.name and ".tmp" in p.name]
    assert leftovers == [], f"leftover tempfiles: {leftovers}"


def test_save_failure_preserves_original(tmp_path):
    m1 = torch.nn.Linear(4, 2)
    path = tmp_path / "c.pth"
    save_checkpoint_atomic(m1.state_dict(), path)
    original_sd = load_checkpoint(path)
    with patch("torch.save", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            save_checkpoint_atomic(m2.state_dict(), path)
    # Original file still readable
    reloaded = load_checkpoint(path)
    for k in original_sd:
        assert torch.equal(original_sd[k], reloaded[k])
```

**Phase 4 adaptation** for `.done` marker:
```python
from scripts.run_ablations import mark_done, is_done


def test_mark_done_is_atomic(tmp_path):
    mark_done(tmp_path)
    assert (tmp_path / ".done").exists()
    assert is_done(tmp_path)


def test_mark_done_cleans_tempfile(tmp_path):
    mark_done(tmp_path)
    leftovers = [p for p in tmp_path.iterdir() if ".done." in p.name and ".tmp" in p.name]
    assert leftovers == []


def test_mark_done_failure_no_partial_file(tmp_path, monkeypatch):
    """If fsync raises, .done must NOT exist (no half-written marker)."""
    monkeypatch.setattr("os.fsync", lambda *a, **kw: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(OSError):
        mark_done(tmp_path)
    assert not (tmp_path / ".done").exists()
```

---

### `tests/test_results_index.py` (new unit test)

**Analog:** `tests/test_train_integration.py::test_csv_header` + `test_csv_rows` (lines 140-164)

**Test pattern**:
```python
def test_csv_header(tmp_path):
    cfg_path, results = _build_smoke_dataset(tmp_path)
    main(["--config", str(cfg_path)])
    run = _latest_run(results)
    with open(run / "train_log.csv", "r", encoding="utf-8") as f:
        header = f.readline().strip()
    assert header == "epoch,train_loss,val_loss,lr"


def test_csv_rows(tmp_path):
    cfg_path, results = _build_smoke_dataset(tmp_path)
    main(["--config", str(cfg_path)])
    run = _latest_run(results)
    with open(run / "train_log.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    for r in rows:
        assert set(r.keys()) == {"epoch", "train_loss", "val_loss", "lr"}
```

**Phase 4 adaptation**:
```python
from src.utils.csv_logger import results_index_append, RESULTS_INDEX_COLUMNS


def test_header_written_on_first_row(tmp_path):
    idx = tmp_path / "results-index.csv"
    results_index_append(idx, {"run_name": "a", "auc": 0.8})
    with open(idx) as f:
        header = f.readline().strip()
    assert header == ",".join(RESULTS_INDEX_COLUMNS)


def test_append_preserves_rows(tmp_path):
    idx = tmp_path / "results-index.csv"
    for i in range(5):
        results_index_append(idx, {"run_name": f"r{i}", "seed": 42 + i})
    rows = list(csv.DictReader(open(idx)))
    assert len(rows) == 5
    assert [r["run_name"] for r in rows] == [f"r{i}" for i in range(5)]


def test_missing_column_becomes_empty(tmp_path):
    """A row dict missing a column writes empty string (D-33)."""
    idx = tmp_path / "results-index.csv"
    results_index_append(idx, {"run_name": "r1"})   # most columns missing
    rows = list(csv.DictReader(open(idx)))
    assert rows[0]["ap"] == ""
```

---

### `tests/test_wandb_preflight.py` (new unit test)

**Analog:** `tests/test_wandb_logger.py` (mode-aware noop + env var handling)

**Test pattern** (test_wandb_logger.py lines 7-22):
```python
def test_wandb_disabled_is_noop(tmp_path):
    cfg = {"wandb": {"mode": "disabled", "project": "violencecc", "tags": []}}
    logger = WandbLogger(cfg, tmp_path / "run")
    assert logger.run is None
    logger.log({"train/loss": 0.1, ...}, step=0)   # no raise
    logger.finish()                                 # no raise


def test_wandb_missing_block_is_noop(tmp_path):
    cfg = {}
    logger = WandbLogger(cfg, tmp_path / "run")
    assert logger.run is None
    logger.log({"train/loss": 0.1}, step=0)
    logger.finish()
```

**Phase 4 adaptation**:
```python
import subprocess
import sys


def test_preflight_env_key(monkeypatch):
    """Path 1: WANDB_API_KEY set → exit 0."""
    monkeypatch.setenv("WANDB_API_KEY", "fake_key")
    from scripts.wandb_preflight import main
    assert main() == 0


def test_preflight_no_wandb_installed(monkeypatch):
    """Path 2 fallback: wandb missing → exit 0 (CSV-only mode OK)."""
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    # force ImportError
    monkeypatch.setitem(sys.modules, "wandb", None)
    from scripts.wandb_preflight import main
    rc = main()
    assert rc == 0


def test_preflight_no_config_exits_nonzero(monkeypatch, capsys):
    """Path 3: no env, no ~/.netrc, wandb importable → exit 2."""
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    import wandb
    monkeypatch.setattr(wandb.api, "api_key", None, raising=False)
    from scripts.wandb_preflight import main
    rc = main()
    assert rc == 2
    err = capsys.readouterr().err
    assert "wandb is not configured" in err


def test_offline_fallback_on_wandb_error(tmp_path, monkeypatch):
    """D-40: wandb.errors.Error → re-init with mode=offline, no raise."""
    import wandb
    call_count = {"n": 0}

    def fake_init(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise wandb.errors.Error("auth failure")
        return MagicMock()   # offline init succeeds

    monkeypatch.setattr(wandb, "init", fake_init)
    cfg = {"wandb": {"mode": "online", "project": "violencecc"}}
    logger = WandbLogger(cfg, tmp_path / "run")
    # First call failed, second call (offline) succeeded
    assert call_count["n"] == 2
    assert logger.run is not None
```

---

### `tests/test_eval_e2e.py` (new integration test)

**Analog:** `tests/test_train_e2e.py::test_snapshot_roundtrip` (lines 107-166)

**Test pattern**:
```python
@pytest.mark.e2e
def test_full_eval_pipeline(tmp_path):
    """End-to-end: train on synthetic UCF → evaluate → results-index row."""
    # 1. Synthesize UCF splits + skel + clip + ucf_temporal.txt
    # 2. Adapt gated_fusion.yaml to point at synthetic dirs
    # 3. main(["--config", str(cfg_path), "--run-name", "test_e2e"])
    # 4. from src.evaluate import main as eval_main
    # 5. eval_main(["--run-dir", str(run_dir), "--split", "test"])
    # 6. Assert eval_metrics.json, eval_scores.npz, per_category.csv, .done all exist
    # 7. results_index_append was called → CSV has 1 row
    ...
```

---

### `tests/test_verify_pooling.py` (new unit test)

**Analog:** `tests/test_dataset.py::_write_video` + verify_alignment VideoResult dataclass

**Test pattern** — use synthetic 2-person cache and verify:
```python
def test_mean_slice_equals_mean_from_mean_max(tmp_path):
    """verify_pooling_caches: mean_cache[vid] ≈ mean_max_cache[vid][:, :512]."""
    from scripts.verify_pooling_caches import verify_clip_mean_slice
    # Write mean_max cache + mean-only cache for one synthetic video
    # Assert the verification function returns status="pass"
    ...


def test_detects_drift(tmp_path):
    """If mean_cache[vid] != mean_max_cache[vid][:, :512], status='fail'."""
    # Write mismatched caches
    # Assert status="fail"
    ...


def test_skeleton_2person_shape(tmp_path):
    """keep_persons_cache[vid].shape must be [N, 2, 256]."""
    # Write [N, 2, 256] to tmp_path, run verify function, expect pass
    # Write [N, 256] to tmp_path, run verify function, expect fail
    ...
```

---

## Shared Patterns

### Atomic write-temp-then-rename (Windows-safe)

**Source:** `src/utils/checkpoint.py` lines 17-45
**Apply to:** `mark_done()` in scripts/run_ablations.py (new); `eval_metrics.json` writes in
src/evaluate.py; any file output in scripts/extract_*.py
```python
fd, tmp_path = tempfile.mkstemp(
    prefix=f".{path.name}.",
    suffix=".tmp",
    dir=str(path.parent),
)
try:
    with os.fdopen(fd, "wb") as f:
        # ... write content ...
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, str(path))
except Exception:
    if os.path.exists(tmp_path):
        try: os.unlink(tmp_path)
        except OSError: pass
    raise
```
The extractor scripts already use a simpler `tmp_path.replace(output_path)` pattern
(extract_ctrgcn.py line 391); new code should follow the `mkstemp + fsync + replace`
pattern for reproducibility guarantees on power loss.

### PROJECT_ROOT constant + deterministic feature paths

**Source:** `scripts/extract_ctrgcn.py` lines 52-62; `scripts/verify_alignment.py`
lines 57-68
**Apply to:** All scripts/ files (`run_ablations.py`, `wandb_preflight.py`,
`verify_pooling_caches.py`)
```python
PROJECT_ROOT = pathlib.Path("D:/ViolenceCC")
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

SKELETON_ROOT = pathlib.Path("E:/skeletons")
SNIPPET_ROOT = pathlib.Path("E:/snippets")
FEATURE_ROOT = pathlib.Path("E:/features")
```

### Resume-if-done filesystem probe

**Source:** `scripts/extract_ctrgcn.py` lines 354-358
**Apply to:** scripts/run_ablations.py (.done marker instead of .npy size check)
```python
# Phase 2 pattern:
output_path = output_dir / f"{video_id}.npy"
if output_path.exists() and output_path.stat().st_size > 128:
    skipped += 1
    pbar.update(1)
    continue

# Phase 4 pattern (D-31):
if (spec.run_dir / ".done").exists():
    summary["skipped"].append(spec.run_name)
    print(f"[skip] {spec.run_name} (.done present)")
    continue
```

### Per-video error logging

**Source:** `scripts/extract_ctrgcn.py` lines 382-407
**Apply to:** scripts/run_ablations.py (D-32 runner-errors.log)
```python
error_log_path = output_dir / "errors.log"
...
try:
    feats = extract_video_features(...)
except Exception as exc:
    failed += 1
    error_msg = f"{video_id}\t{type(exc).__name__}: {exc}"
    logger.error(f"FAILED: {error_msg}")
    with open(error_log_path, "a") as ef:
        ef.write(error_msg + "\n")
```
D-32 variant: append to `runner-errors.log` at project root; tuple identifier is
`spec.run_name` instead of `video_id`.

### Lazy-import factory registry

**Source:** `src/models/registry.py` lines 13-35
**Apply to:** any future extensibility points (none in Phase 4 beyond adding rtfm_i3d)
```python
def _get_variant_X():
    from src.models.variant_X import VariantX
    return VariantX
MODEL_REGISTRY["variant_X"] = _get_variant_X
```

### Named LayerNorm on every model variant

**Source:** `src/models/gated_fusion.py` lines 47-60, `src/models/skeleton_only.py` line 34,
`src/models/clip_only.py` line 38
**Apply to:** `src/models/rtfm_i3d.py` — MUST expose `self.ln_i3d = nn.LayerNorm(i3d_dim)`
as a named attribute (D-07) so Phase 5 TTA can discover it via `model.named_modules()`.

### Variant-uniform forward signature

**Source:** all `src/models/*.py` (skeleton_only.py line 39, clip_only.py line 43, etc.)
**Apply to:** `src/models/rtfm_i3d.py` — `forward(self, skel=None, clip=None, i3d=None, mask=None)`
even though only `i3d` is used. This allows `src/train.py::train_one_epoch` and the
eval loop to call `model(skel=..., clip=..., i3d=..., mask=...)` uniformly without a
variant switch.

### CSV logger append pattern

**Source:** `src/utils/csv_logger.py` lines 10-39
**Apply to:** `results_index_append()` helper (new in csv_logger.py)
```python
self.path.parent.mkdir(parents=True, exist_ok=True)
if not self.path.exists() or self.path.stat().st_size == 0:
    with open(self.path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=self.fieldnames)
        w.writeheader()
        f.flush()
        os.fsync(f.fileno())
...
with open(self.path, "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=self.fieldnames)
    w.writerow(row)
    f.flush()
    os.fsync(f.fileno())
```

### Deterministic run-dir name convention

**Source:** `src/train.py` lines 56-59 (timestamped, kept as fallback)
**Apply to:** `scripts/run_ablations.py::RunSpec.run_name`:
```python
@property
def run_name(self) -> str:
    # D-30 deterministic naming
    cv = f"_{self.cache_variant}" if self.cache_variant else ""
    return f"{self.dataset}_{self.variant}{cv}_s{self.seed}"
```
The new `--run-name` CLI arg on `src/train.py` (D-30) consumes this string and
bypasses the timestamp-embedding in `run_name(cfg)`.

### Tests: synthetic feature factories + tmp_feature_dir

**Source:** `tests/conftest.py` lines 52-72, `tests/fixtures/synthetic.py` lines 11-37,
`tests/test_dataset.py` lines 17-23, `tests/test_train_e2e.py` lines 27-49
**Apply to:** all new Phase 4 tests
```python
@pytest.fixture
def tmp_feature_dir(tmp_path):
    (tmp_path / "skeleton").mkdir()
    (tmp_path / "clip").mkdir()
    return tmp_path


def make_skel(N: int = 40, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal((N, 256), dtype=np.float32)


def _write_video(dir_skel, dir_clip, video_id: str, N: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    np.save(dir_skel / f"{video_id}.npy",
            rng.standard_normal((N, 256), dtype=np.float32))
    np.save(dir_clip / f"{video_id}.npy",
            rng.standard_normal((N, 1024), dtype=np.float32))
```

### Tests: config_snapshot.json round-trip in integration tests

**Source:** `tests/test_train_e2e.py::_adapt_yaml` (lines 52-69) + `test_snapshot_roundtrip`
(lines 107-166)
**Apply to:** `tests/test_evaluate_cli.py`, `tests/test_eval_e2e.py`
```python
def _adapt_yaml(base_yaml_path, tmp_root):
    with open(base_yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    results, splits, skel, clip = _build_synth_features_and_splits(tmp_root)
    cfg["paths"]["skeleton_features"] = str(skel)
    cfg["paths"]["clip_features"] = str(clip)
    cfg["paths"]["splits_dir"] = str(splits)
    cfg["paths"]["results_dir"] = str(results)
    cfg["data"]["batch_size"] = 5
    cfg["data"]["num_workers"] = 0
    cfg["data"]["pin_memory"] = False
    cfg["train"]["epochs"] = 1
    cfg["train"]["warmup_epochs"] = 0
    cfg["wandb"]["mode"] = "disabled"
    out = tmp_root / f"{cfg['model']['variant']}.yaml"
    out.write_text(yaml.safe_dump(cfg))
    return out, results
```

### pytest e2e marker

**Source:** `tests/test_train_e2e.py` line 20: `pytestmark = pytest.mark.e2e`
**Apply to:** `tests/test_evaluate_cli.py`, `tests/test_eval_e2e.py`,
`tests/test_run_ablations.py` (for subprocess-based tests)

### Docstring convention (decision reference)

**Source:** every file under src/ (e.g., `src/models/gated_fusion.py` lines 1-20,
`src/losses/mil_loss.py` lines 1-14, `src/utils/checkpoint.py` lines 1-6)
**Apply to:** every new Phase 4 file
```python
"""<short module purpose> (<PRD/plan ID>).

<Optional architecture diagram or formula in ASCII>.

D-XX: <decision reference explaining a specific design choice>.
"""
```

## No Analog Found

These files have no close existing analog in the codebase:

| File | Role | Data Flow | Reason | Fallback |
|------|------|-----------|--------|----------|
| `src/eval/__init__.py` | package marker | — | No `src/data/__init__.py` has meaningful content; use empty-ish marker matching `src/models/__init__.py` | Empty file or `__all__ = []` |
| `scripts/_gate_check.py` (implied by D-18 "halt queue if gate fails") | runtime check | — | No existing "halt-if-threshold" script in the codebase | Inline logic in `run_ablations.py::main()` — check AP from `results-index.csv` after first rtfm_i3d run, sys.exit(3) if < anchor - 0.01 |

## Metadata

**Analog search scope:**
- `src/**/*.py` (all phase-3 modules)
- `scripts/**/*.py` (extractors, verifiers)
- `tests/**/*.py` (existing unit + integration tests)
- `configs/*.yaml` (all 4 phase-3 configs)
- `data/splits/*.txt`, `data/annotations/` (conventions)

**Files scanned:** 34 source files + 4 YAML configs + 15 test files = 53 total

**Pattern extraction date:** 2026-04-15

**Key architectural invariants preserved:**
1. **Flat YAML per variant** (Phase 1 D-03, held via D-35) — 3 new YAML files are
   self-contained, no YAML inheritance.
2. **Variant-uniform forward signature** — RTFMI3D accepts `skel=None, clip=None, i3d=None`
   so train.py / evaluate.py code paths don't branch on variant.
3. **Named LayerNorm discoverability** (D-07) — RTFMI3D exposes `ln_i3d` attribute for
   Phase 5 TTA.
4. **Atomic file writes** (checkpoint.py pattern) — `.done` marker, `eval_metrics.json`,
   `eval_scores.npz` all use `mkstemp + fsync + os.replace`.
5. **Decision-driven naming** — every new file docstring begins with its decision ID
   (D-01 through D-41).
6. **Synthetic features over E:/ mounts in tests** — all new tests follow
   `tmp_feature_dir` fixture convention; integration tests skip gracefully if
   real feature dirs aren't mounted (`pytest.skip`).
