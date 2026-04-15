# Phase 4b: RTFM XD-I3D Gate + xd_i3d Training Dispatch - Pattern Map

**Mapped:** 2026-04-16
**Files analyzed:** 10 (6 create, 3 modify, reference-only: I3DFeatureDataset, UCF eval path, rtfm_i3d.yaml)
**Analogs found:** 10 / 10 (all files have exact in-repo templates)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/eval/xd_annotations.py` | utility (module) | file-I/O + transform | `src/eval/ucf_annotations.py` | exact |
| `data/annotations/xd_temporal.txt` | data | file | `data/annotations/ucf_temporal.txt` | exact (both are Wu/Sultani flat-text annotation files) |
| `src/data/loaders.py::build_dataloaders_i3d` | service (dataloader builder) | CRUD over on-disk .npy cache | `src/data/loaders.py::build_dataloaders` (same file) | role-match (paired-bag pattern); data source differs (I3DFeatureDataset vs MILFeatureDataset) |
| `src/data/loaders.py::collate_i3d_train` | utility (collate fn) | transform (tensor reshape) | `torch.utils.data.default_collate` usage pattern; no existing custom collate in repo | no-analog (pure reshape — see Note 3) |
| `src/train.py::train_one_epoch_i3d` | controller (training step) | event-driven loop | `src/train.py::train_one_epoch` (same file) | role-match |
| `src/train.py::validate_i3d` | controller (val step) | event-driven loop | `src/train.py::validate` (same file) | role-match |
| `src/train.py::main()` dispatch branch | controller (entry) | dispatch | `src/train.py::main()` (same file, existing body) | exact (same function, just add `if cfg['dataset'] == 'xd_i3d'` branch before line 165) |
| `src/evaluate.py::_build_frame_arrays` xd_i3d branch | utility (transform) | request-response over annotation file | `src/evaluate.py::_build_frame_arrays` UCF branch (same function, lines 194-227) | exact (direct template) |
| `tests/test_xd_annotations.py` | test | unit | `tests/test_ucf_annotations.py` | exact (same parser contract) |
| `tests/test_loaders_i3d.py` | test | unit | `tests/test_i3d_dataset.py` (synthetic_i3d_features fixture) + `tests/test_train_integration.py::_build_smoke_dataset` | role-match |
| `tests/test_train_i3d.py` | test | unit | `tests/test_train.py` (CLI smoke) + `tests/test_train_integration.py` | role-match |
| `tests/test_evaluate_xd_i3d.py` | test | unit + subprocess | `tests/test_evaluate_cli.py` | exact |

## Pattern Assignments

---

### `src/eval/xd_annotations.py` (utility, file-I/O + transform)

**Analog:** `src/eval/ucf_annotations.py`

**Imports pattern** (lines 18-24, verbatim):
```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
```

**VideoAnnotation dataclass pattern** (lines 27-42 — mirror exactly but change the `intervals` type from `Tuple[Interval, Interval]` to `Tuple[Interval, ...]` because Wu annotations are multi-interval, not fixed-2):
```python
Interval = Tuple[int | None, int | None]


@dataclass(frozen=True)
class VideoAnnotation:
    """Immutable Sultani-row holder keyed by video_id (no filename suffix)."""

    video_id: str  # without _x264.mp4 suffix; matches split file IDs
    category: str  # e.g. "Abuse", "Fighting", "Normal"
    intervals: Tuple[Interval, Interval]  # ((s1, e1), (s2, e2)); -1 encoded as None

    @property
    def is_normal(self) -> bool:
        """True when all four interval endpoints are None (every -1)."""
        return all(s is None for s, _ in self.intervals)
```

**parse_annotations pattern** (lines 44-74 — CRITICAL: keep the SAME function name `parse_annotations` to honor the downstream contract mentioned in CONTEXT.md, OR provide BOTH `parse_annotations` (alias) and `parse_xd_annotations` as the public surface; planner must decide. RESEARCH.md line 453-492 uses the name `parse_xd_annotations`):
```python
def parse_annotations(path: Path) -> Dict[str, VideoAnnotation]:
    """Return {video_id_without_suffix: VideoAnnotation}.

    Raises:
      ValueError: if any non-blank line does not split into exactly 6 columns.
    """
    annos: Dict[str, VideoAnnotation] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()  # whitespace-split handles 1- or 2-space delimiters
            if len(parts) != 6:
                raise ValueError(
                    f"Expected 6 columns, got {len(parts)} in line: {line!r}"
                )
            fname, category, s1, e1, s2, e2 = parts
            # Strip _x264.mp4 (or just .mp4) to match data/splits/ucf_*.txt IDs
            vid = fname.replace("_x264.mp4", "").replace(".mp4", "")

            def _v(s: str) -> int | None:
                return None if int(s) == -1 else int(s)

            anno = VideoAnnotation(
                video_id=vid,
                category=category,
                intervals=((_v(s1), _v(e1)), (_v(s2), _v(e2))),
            )
            annos[vid] = anno
    return annos
```

**frame_labels pattern** (lines 77-93 — keep name `frame_labels` so it mirrors UCF; also export as `xd_frame_labels` alias):
```python
def frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray:
    """Build [n_frames] binary label vector from annotation intervals (D-16).

    Per-frame label = union of both intervals. Endpoints are clamped to
    [0, n_frames] so annotations that extend past the decoded video length
    (e.g., frame_labels(Abuse028, n_frames=100) when Abuse028's end is 240)
    are safe — no out-of-bounds indexing.
    """
    labels = np.zeros(n_frames, dtype=np.int64)
    for (s, e) in anno.intervals:
        if s is None:
            continue
        s = max(0, int(s))
        e = min(n_frames, int(e))
        if e > s:
            labels[s:e] = 1
    return labels
```

**Key notes for planner:**
1. **Signature contract (CONTEXT.md D-10 + context file):** downstream `src/evaluate.py::_build_frame_arrays` imports `parse_xd_annotations` + `xd_frame_labels`. To maintain symmetry with `ucf_annotations.py` AND satisfy the CONTEXT-specified import names, the planner should define `parse_xd_annotations`/`xd_frame_labels` as the public names AND optionally alias `parse_annotations = parse_xd_annotations` / `frame_labels = xd_frame_labels` for mirror-testing ergonomics. CONTEXT.md line 38 says explicitly "mirroring `src/eval/ucf_annotations.py` pattern: `parse_annotations(path) -> Dict[str, VideoAnnotation]` + `frame_labels(anno, n_frames) -> np.ndarray`" — so the planner has freedom but must pick and stick to one.
2. **Column count differs from UCF:** UCF is fixed 6 columns `(fname cat s1 e1 s2 e2)`; Wu XD is variable `(vid s1 e1 [s2 e2 ...])` with `1 + 2*K` columns for K≥1 intervals. Verified in RESEARCH.md lines 629-644. The parser structure is the same, but the column validation check `len(parts) != 6` becomes `(len(parts) - 1) % 2 != 0 or len(parts) < 3`. RESEARCH.md line 474-492 has the full verified parser draft.
3. **ID normalization differs:** UCF strips `_x264.mp4`; Wu strips just `.mp4` (and only when present — some rows have it, some don't). Per RESEARCH.md line 655: `vid = parts[0][:-4] if parts[0].endswith('.mp4') else parts[0]`. Split file IDs carry NO suffix.
4. **Category parsing for Phase 4c compat (D-10, D-13):** Add a `_parse_category(video_id: str) -> str` helper that strips the `_label_<code>-...` suffix. Per CONTEXT.md D-13, Phase 4b does not surface categories in `per_category.csv`, but the parser MUST support it for Phase 4c reuse. RESEARCH.md lines 495-521 show the verified helper.
5. **Missing-entry semantics differ from UCF:** UCF `ucf_temporal.txt` has Normal entries (all -1); Wu `annotations.txt` OMITS all 300 normal test videos. Caller (`_build_frame_arrays`) must guard `if vid in annos` — NOT the parser. The parser just returns the dict it found. Verified: RESEARCH.md lines 642, 778-780.
6. **`is_normal` property:** For Wu, "normal" = annotation absent (parser doesn't see it), so this property is informational only (every parsed Wu annotation has intervals=non-empty → `is_normal` always False for parsed entries). Keep it for signature parity but document the semantic shift.

---

### `data/annotations/xd_temporal.txt` (data file)

**Analog:** `data/annotations/ucf_temporal.txt`

**Format sample (first 3 UCF rows, lines 1-3 of the analog file):**
```
Abuse028_x264.mp4  Abuse  165  240  -1  -1  
Abuse030_x264.mp4  Abuse  1275  1360  -1  -1  
Arrest001_x264.mp4  Arrest  1185  1485  -1  -1  
```

**Target format for xd_temporal.txt (per RESEARCH.md §Wu Annotation Format, verified this session):**
```
<video_id>[.mp4] <s1> <e1> [<s2> <e2> [<s3> <e3> ...]]
```

Example rows (illustrative, from verified Wu file structure):
```
A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_A.mp4 ...  # (does not appear — normals omitted)
Bad.Boys.1995__#01-33-51_01-34-37_label_B2-0-0 420 1848
v=S-7rRLrxnVQ__#1_label_B4-0-0 150 420 680 1267
```

**Key notes for planner:**
1. **Source URL (verified):** `https://roc-ng.github.io/XD-Violence/images/annotations.txt` (RESEARCH.md line 623).
2. **File size:** ~6.2 KB, exactly 500 non-blank lines (only abnormal test videos; normals omitted).
3. **Column distribution (all `1 + 2*K` with K≥1):** 240 lines have 3 cols (1 interval); 105 have 5 cols (2 intervals); 59 have 7 cols (3 intervals); 96 have 9-45 cols (4-22 intervals).
4. **Commit protocol:** Download once, verify SHA256, record in commit message for provenance (RESEARCH.md line 1163).
5. **NOT test-set-leakage-sensitive:** This file is annotation metadata, not a split file. Goes under `data/annotations/` which is the Phase 4 D-04 canonical location (mirrors the UCF precedent exactly). No C3 concern.
6. **Do not commit under `data/splits/`**, under any other feature directory, or under a location that suggests it's a split file.

---

### `src/data/loaders.py::build_dataloaders_i3d` (service, CRUD)

**Analog:** `src/data/loaders.py::build_dataloaders` (same file, lines 52-159)

**Imports pattern** (lines 20-49 — keep existing block; add `from src.data.i3d_dataset import I3DFeatureDataset`):
```python
from __future__ import annotations

from typing import Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, Subset

from src.data.dataset import MILFeatureDataset
from src.data.i3d_dataset import I3DFeatureDataset  # NEW

try:  # pragma: no cover - import shim for parallel-worktree ergonomics
    from src.utils.seed import seed_worker, make_generator  # type: ignore
except ImportError:  # fallback mirrors RESEARCH.md §2.5
    import random as _random

    def seed_worker(worker_id: int) -> None:  # type: ignore[no-redef]
        worker_seed = torch.initial_seed() % 2**32
        np.random.seed(worker_seed)
        _random.seed(worker_seed)

    def make_generator(seed: int) -> torch.Generator:  # type: ignore[no-redef]
        g = torch.Generator()
        g.manual_seed(int(seed))
        return g
```

**Signature + doc pattern** (copy the docstring style from `build_dataloaders` at lines 52-92; adapt keys to i3d):
```python
def build_dataloaders(cfg: dict) -> Tuple[Tuple[DataLoader, DataLoader], DataLoader]:
    """Build paired (nor, abn) train loaders + val loader per D-04.

    Parameters
    ----------
    cfg : dict
        Minimum required keys::

            cfg["dataset"]                      # "ucf" or "xd"
            cfg["seed"]                         # int
            cfg["paths"]["splits_dir"]          # directory containing
                                                # {dataset}_train.txt and
                                                # {dataset}_val.txt
            cfg["paths"]["skeleton_features"]   # directory of skel .npy
            cfg["paths"]["clip_features"]       # directory of clip .npy
            ...

    Returns
    -------
    ((nor_loader, abn_loader), val_loader)
        ...

    Notes
    -----
    * ``drop_last=True`` on both train loaders ...
    * ``worker_init_fn=seed_worker`` plus per-loader ``torch.Generator``
      seeded with ``cfg["seed"]`` / ``cfg["seed"] + 1`` ...
```

**Dataset construction pattern** (lines 93-120 — mirror but swap in `I3DFeatureDataset` and `i3d_features` path):
```python
    dataset = cfg["dataset"]                       # 'ucf' or 'xd'
    paths = cfg["paths"]
    data_cfg = cfg["data"]
    T = data_cfg.get("T", 32)
    bs = data_cfg["batch_size"]                    # 16 per D-04
    num_workers = data_cfg.get("num_workers", 0)
    pin_memory = data_cfg.get("pin_memory", False)
    seed = cfg.get("seed", 42)
    ...

    train_full = MILFeatureDataset(
        split_file=f"{paths['splits_dir']}/{dataset}_train.txt",
        skel_dir=paths["skeleton_features"],
        clip_dir=paths["clip_features"],
        T=T, mode="train", seed=seed, dataset=dataset,
        skel_agg=skel_agg,
    )
    val_full = MILFeatureDataset(
        split_file=f"{paths['splits_dir']}/{dataset}_val.txt",
        ...
    )
```

**Paired partition pattern** (lines 122-126 — REUSE VERBATIM; the label attribute name `labels` / `video_ids` exists on I3DFeatureDataset too, but note I3DFeatureDataset doesn't currently expose a `.labels` dict — see note 2 below):
```python
    # Split the training set into normal (label=0) and abnormal (label=1) subsets.
    nor_idx = [i for i, v in enumerate(train_full.video_ids)
               if train_full.labels[v] == 0.0]
    abn_idx = [i for i, v in enumerate(train_full.video_ids)
               if train_full.labels[v] == 1.0]
```

**DataLoader assembly pattern** (lines 128-157 — copy verbatim, including the `g_nor`/`g_abn`/`g_val` Generator fan-out and `common` kwargs):
```python
    g_nor = make_generator(seed)
    g_abn = make_generator(seed + 1)
    g_val = make_generator(seed + 2)

    persistent = num_workers > 0
    common = dict(
        batch_size=bs,
        num_workers=num_workers,
        worker_init_fn=seed_worker,
        pin_memory=pin_memory,
        persistent_workers=persistent,
        drop_last=True,
    )

    nor_loader = DataLoader(Subset(train_full, nor_idx), shuffle=True,
                            generator=g_nor, **common)
    abn_loader = DataLoader(Subset(train_full, abn_idx), shuffle=True,
                            generator=g_abn, **common)

    val_loader = DataLoader(val_full, batch_size=bs * 2,
                            num_workers=num_workers,
                            worker_init_fn=seed_worker,
                            generator=g_val, pin_memory=pin_memory,
                            persistent_workers=persistent,
                            drop_last=False, shuffle=False)

    return (nor_loader, abn_loader), val_loader
```

**Key notes for planner:**
1. **Do NOT hardcode batch_size** — read `data_cfg["batch_size"]` exactly like `build_dataloaders` does at line 97 (`bs = data_cfg["batch_size"]`). `configs/rtfm_i3d.yaml:22` pins this to 3 per Pitfall 3 (5-crop × 3 = 15 effective bag, matching k_topk=3).
2. **I3DFeatureDataset has NO `.labels` dict** (verified from reading `src/data/i3d_dataset.py` lines 57-71). It only stores `self.video_ids: List[str]`. Labels are computed per-item in `__getitem__` from the `_label_A` suffix (line 148). The partitioning must use the suffix directly:
   ```python
   nor_idx = [i for i, v in enumerate(train_full.video_ids) if v.endswith("_label_A")]
   abn_idx = [i for i, v in enumerate(train_full.video_ids) if not v.endswith("_label_A")]
   ```
   This matches CONTEXT.md D-06 exactly.
3. **Dataset construction signature** — `I3DFeatureDataset(split_file, feature_dir, mode, T, n_crops=5)` (from `src/data/i3d_dataset.py` lines 42-49). Pass:
   - `split_file=f"{paths['splits_dir']}/xd_train.txt"` (hardcode `xd_train` / `xd_val` since xd_i3d is single-dataset)
   - `feature_dir=f"{paths['i3d_features']}/RGB"` (train+val both live under RGB/ per CONTEXT.md line 103 and `src/eval/test_loader.py:113` — but the TEST path uses `RGBTest/`)
   - `mode="train"` for train_full, `mode="val"` for val_full
   - `T=data_cfg.get("T", 32)`
4. **COLLATE FN goes in `common` dict:** The custom `collate_i3d_train` must be wired via `collate_fn=collate_i3d_train` in both `nor_loader` and `abn_loader` DataLoader() calls. The existing `build_dataloaders` uses PyTorch's default collate; this is the one concrete kwargs change vs. the analog.
5. **Val loader batch size:** Keep `batch_size=bs * 2` like the analog, but understand val yields `[B*5, T, 1024]` (15 × 2 = 30 samples × 5 crops = 150 effective? No — with `bs*2=6` videos × 5 crops via collate = 30 samples). The val loader also needs `collate_fn=collate_i3d_train` applied OR a separate val collate. Planner decides: simplest is to use the same `collate_i3d_train` for val since I3DFeatureDataset at `mode="val"` returns the same `[5, T, 1024]` shape (lines 160-167 of `i3d_dataset.py`).
6. **No `skel_agg` knob** — I3D has no 2-person skeleton aggregation; drop the `skel_agg` plumbing.
7. **New function lives ALONGSIDE `build_dataloaders`** — CONTEXT.md D-04 is explicit: parallel functions, not polymorphic. Do not modify the existing `build_dataloaders`.

---

### `src/data/loaders.py::collate_i3d_train` (utility, transform)

**Analog:** No existing custom collate in the repo. `torch.utils.data.default_collate` gives `[B, 5, T, 1024]`; the target is `[B*5, T, 1024]`.

**Concrete pattern (pure reshape — recommended explicit form per CONTEXT.md Claude's Discretion line 57 "custom function using explicit `torch.stack` + `.view(B*5, T, 1024)` for auditability"):**
```python
def collate_i3d_train(samples: list[dict]) -> dict:
    """Flatten 5-crop dim into batch dim for RTFM MIL bag assembly (D-05).

    Input: list of B dicts each with
      - "i3d":     torch.Tensor [5, T, 1024]
      - "label":   float
      - "video_id": str

    Output: dict with
      - "i3d":     torch.Tensor [B*5, T, 1024]
      - "label":   torch.Tensor [B*5]
      - "video_id": list[str], length B*5

    Matches I3DFeatureDataset train/val __getitem__ return shape
    (src/data/i3d_dataset.py:160-167). With batch_size=3 from
    configs/rtfm_i3d.yaml, yields effective MIL bag size 15 matching
    k_topk=3 (Pitfall 3).
    """
    # Stack the [5, T, 1024] i3d tensors into [B, 5, T, 1024].
    i3d = torch.stack([s["i3d"] for s in samples], dim=0)
    B, n_crops, T, D = i3d.shape
    i3d = i3d.reshape(B * n_crops, T, D)

    # Labels are per-video; broadcast each label to all 5 of its crops.
    labels = torch.tensor(
        [s["label"] for s in samples], dtype=torch.float32
    ).repeat_interleave(n_crops)

    # video_ids broadcast similarly (str, not tensor).
    video_ids = [s["video_id"] for s in samples for _ in range(n_crops)]

    return {"i3d": i3d, "label": labels, "video_id": video_ids}
```

**Shape audit log pattern for D-12 diagnostic** (from CONTEXT.md line 38 + D-12 "Train-time 5-crop bag-size audit"):

No direct analog in repo, but follow the `[i3d_dataset]` prefix style from `src/data/i3d_dataset.py:67-71`:
```python
# Example one-shot log scaffold (to be added in train_one_epoch_i3d, not here):
print(
    f"[train_i3d] epoch=0 step=0 n_normal={n_normal} n_abnormal={n_abnormal} "
    f"i3d_shape={tuple(i3d.shape)}",
    flush=True,
)
```

**Key notes for planner:**
1. **D-05 shape contract:** input dict → output dict; BOTH input and output satisfy variant-uniform forward (see `src/evaluate.py:150-157` for the kwargs pattern — the model receives `i3d` key only, no `skel`/`clip`).
2. **Test mode uses crop-averaged `[N, 1024]`** from `I3DFeatureDataset.__getitem__` test path (lines 150-157). Test collate is simply the default; do NOT apply `collate_i3d_train` at test time. The test path is routed through `src/eval/test_loader.py` which bypasses this collate entirely.
3. **Placement options per CONTEXT.md line 123:** may live in `src/data/loaders.py` (simpler; adds ~30 lines) or `src/data/collate.py` (new module; cleaner separation). Planner's call. Simpler = same file.
4. **`.repeat_interleave(5)` is KEY** — if the planner uses `.repeat(5)` instead, the labels will be in the WRONG order (all normals then all abnormals across crops, not per-video). The MIL bag ordering assumes `[video0_crop0, video0_crop1, ..., video0_crop4, video1_crop0, ...]` which matches `i3d.reshape(B*5, ...)` memory layout and `labels.repeat_interleave(5)` expansion.

---

### `src/train.py::train_one_epoch_i3d` (controller, event-driven loop)

**Analog:** `src/train.py::train_one_epoch` (same file, lines 85-113)

**Full function pattern to mirror:**
```python
def train_one_epoch(model, nor_loader, abn_loader, optimizer, device, train_cfg):
    model.train()
    losses = []
    # Shorter queue drives the step count; longer queue cycles
    steps_per_epoch = min(len(nor_loader), len(abn_loader))
    nor_iter = iter(nor_loader)
    abn_iter = iter(abn_loader)
    for _ in range(steps_per_epoch):
        nor_batch = next(nor_iter)
        abn_batch = next(abn_iter)
        skel = torch.cat([nor_batch["skel"], abn_batch["skel"]], dim=0).to(device)
        clip = torch.cat([nor_batch["clip"], abn_batch["clip"]], dim=0).to(device)
        mask = torch.cat([nor_batch["mask"], abn_batch["mask"]], dim=0).to(device)
        n_normal = nor_batch["skel"].shape[0]

        scores = model(skel=skel, clip=clip, mask=mask)
        loss = mil_ranking_loss(
            scores, mask, n_normal=n_normal,
            k=int(train_cfg["k_topk"]),
            margin=float(train_cfg["margin"]),
            lam_sparse=float(train_cfg["lam_sparse"]),
            lam_smooth=float(train_cfg["lam_smooth"]),
        )

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    return float(sum(losses) / max(len(losses), 1))
```

**Key notes for planner:**
1. **Signature (CONTEXT.md D-04):** `train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, device, train_cfg) -> float` — identical kwargs, identical return type.
2. **Concat key change:** Instead of `torch.cat([nor_batch["skel"], abn_batch["skel"]], dim=0)`, use `torch.cat([nor_batch["i3d"], abn_batch["i3d"]], dim=0)`. No skel, no clip, no mask.
3. **MIL mask synthesis:** `mil_ranking_loss` requires a `mask: [2B, T]` arg (src/losses/mil_loss.py:56). The UCF path gets this from `MILFeatureDataset` which produces a padding mask. I3DFeatureDataset's `_resample_T` gives a fixed-length `[T, 1024]` output (no padding), so the mask is ALL ONES. Synthesize: `mask = torch.ones(i3d.shape[0], i3d.shape[1], device=device)`. Pass it into `mil_ranking_loss(scores, mask, ...)`.
4. **n_normal counts crops, not videos:** After the collate flattens `[B, 5, T, 1024]` → `[B*5, T, 1024]`, `nor_batch["i3d"].shape[0]` == `batch_size * n_crops` == 15 (with bs=3). The hinge loss pairs top-k scores by index (src/losses/mil_loss.py:76-77), so this naturally gives a 15-vs-15 pairing.
5. **forward() signature** per `src/models/rtfm_i3d.py:51`: `model(skel=None, clip=None, i3d=..., mask=...)`. Pass `i3d=i3d, mask=mask`; the model ignores `skel`/`clip`.
6. **Output shape** from `RTFMI3D`: `[B, T]` after the `.squeeze(-1)` in `rtfm_i3d.py:59`. This matches what `mil_ranking_loss` expects (`scores: [2B, T]`). No shape conversion needed.
7. **D-12 one-shot audit (first 3 epochs) — CONTEXT.md discretion line 58:** Add a conditional log at the START of the for-loop body, wrapped in `if epoch < 3 and step == 0:` (or similar). The training loop (main()) passes `epoch` to the function — but the current `train_one_epoch` signature does NOT receive `epoch`. Planner must either: (a) add `epoch: int = 0` kwarg, or (b) use a module-level closure, or (c) log unconditionally on step 0 of every epoch and tolerate the noise. (a) is cleanest.

---

### `src/train.py::validate_i3d` (controller, event-driven loop)

**Analog:** `src/train.py::validate` (same file, lines 116-138)

**Full function pattern to mirror:**
```python
@torch.no_grad()
def validate(model, val_loader, device, train_cfg) -> float:
    """Compute val MIL Ranking Loss (RESEARCH.md 10.3)."""
    model.eval()
    losses = []
    for batch in val_loader:
        pair = _split_labels(batch)
        if pair is None:
            continue
        skel, clip, mask, n_normal = pair
        skel = skel.to(device)
        clip = clip.to(device)
        mask = mask.to(device)
        scores = model(skel=skel, clip=clip, mask=mask)
        loss = mil_ranking_loss(
            scores, mask, n_normal=n_normal,
            k=int(train_cfg["k_topk"]),
            margin=float(train_cfg["margin"]),
            lam_sparse=float(train_cfg["lam_sparse"]),
            lam_smooth=float(train_cfg["lam_smooth"]),
        )
        losses.append(loss.item())
    return float(sum(losses) / max(len(losses), 1)) if losses else float("inf")
```

**`_split_labels` helper pattern** (lines 65-82, called by `validate`):
```python
def _split_labels(batch):
    """Split a val batch (labels 0 normal, 1 abnormal) into paired halves."""
    labels = batch["label"]
    nor_idx = (labels == 0).nonzero(as_tuple=True)[0]
    abn_idx = (labels == 1).nonzero(as_tuple=True)[0]
    if len(nor_idx) == 0 or len(abn_idx) == 0:
        return None
    n = min(len(nor_idx), len(abn_idx))
    nor_idx = nor_idx[:n]
    abn_idx = abn_idx[:n]
    skel = torch.cat([batch["skel"][nor_idx], batch["skel"][abn_idx]], dim=0)
    clip = torch.cat([batch["clip"][nor_idx], batch["clip"][abn_idx]], dim=0)
    mask = torch.cat([batch["mask"][nor_idx], batch["mask"][abn_idx]], dim=0)
    return skel, clip, mask, n
```

**Key notes for planner:**
1. **Write a sibling `_split_labels_i3d` helper** mirroring `_split_labels` but keyed on `"i3d"` only (no skel/clip/mask). Return `(i3d_paired, mask_paired, n_normal)` — mask synthesized as `torch.ones(...)`.
2. **Val loader is a single DataLoader** over `I3DFeatureDataset(mode="val")` + `collate_fn=collate_i3d_train`. After collate, `batch["label"]` is `[B*5]` with labels repeated `5×` per video. The `_split_labels_i3d` helper partitions on these per-crop labels, not per-video — which is CORRECT because top-k is per-snippet-per-crop-per-video in the MIL loss.
3. **Return type preserved:** `float` (mean MIL loss) or `float("inf")` if loader yielded no pairs (D-04 failure mode). Same as analog.
4. **`@torch.no_grad()` decorator:** keep it (line 116 of analog).

---

### `src/train.py::main()` dispatch branch (controller, entry)

**Analog:** `src/train.py::main()` (same file, lines 141-207)

**Existing dispatch-free body (lines 162-177):**
```python
    # Model + data + training pieces
    model = build_model(**cfg["model"]).to(device)
    (nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
    optimizer = build_optimizer(model.parameters(), cfg["train"])
    scheduler = build_scheduler(optimizer, cfg["train"])
    early = EarlyStopping(patience=int(cfg["train"]["patience"]))

    best_path = run_dir / "best_model.pth"
    last_path = run_dir / "last_model.pth"

    try:
        for epoch in range(int(cfg["train"]["epochs"])):
            train_loss = train_one_epoch(
                model, nor_loader, abn_loader, optimizer, device, cfg["train"])
            val_loss = validate(model, val_loader, device, cfg["train"])
            ...
```

**Key notes for planner (CONTEXT.md D-04 branch pattern):**
1. **Insertion point:** After `cfg = apply_cli_overrides(cfg, args)` at line 144, BEFORE `set_deterministic` at 147 (cfg read only, no side effects yet). But more naturally: keep `set_deterministic`, `device`, and `run_dir` setup identical; branch at line 165 where `build_dataloaders(cfg)` is called, and again at lines 175-177 where `train_one_epoch` + `validate` are called. Branch pattern:
   ```python
       if cfg["dataset"] == "xd_i3d":
           (nor_loader, abn_loader), val_loader = build_dataloaders_i3d(cfg)
       else:
           (nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
       ...
       for epoch in range(int(cfg["train"]["epochs"])):
           if cfg["dataset"] == "xd_i3d":
               train_loss = train_one_epoch_i3d(
                   model, nor_loader, abn_loader, optimizer, device, cfg["train"])
               val_loss = validate_i3d(model, val_loader, device, cfg["train"])
           else:
               train_loss = train_one_epoch(
                   model, nor_loader, abn_loader, optimizer, device, cfg["train"])
               val_loss = validate(model, val_loader, device, cfg["train"])
   ```
2. **D-04 says "Branch once in `main()`"** — but two branch points (loader + step) are required since the function variants are non-polymorphic. Alternative: factor into local `_train_step = train_one_epoch_i3d if cfg["dataset"] == "xd_i3d" else train_one_epoch` + `_validate = ...` selections ONCE after loader construction, then call unconditionally in the loop. This honors D-04's "once" discipline.
3. **Checkpoint save logic (lines 194-198):** unchanged for xd_i3d. `save_checkpoint_atomic` is dataset-agnostic; CONTEXT.md line 118 confirms reuse.
4. **CSV/wandb loggers (lines 160-162):** unchanged. Same keys (epoch/train_loss/val_loss/lr) work for both paths.
5. **Imports needed:** add `from src.data.loaders import build_dataloaders_i3d` alongside line 22 existing `build_dataloaders` import. `train_one_epoch_i3d` / `validate_i3d` are same-file so no new import.

---

### `src/evaluate.py::_build_frame_arrays` xd_i3d branch (utility, transform)

**Analog:** `src/evaluate.py::_build_frame_arrays` UCF branch (same function, lines 194-227)

**Current xd_i3d STUB (lines 180-192 — TO BE REPLACED):**
```python
    if ds == "xd_i3d":
        snippet_window = 16
        upsample_factor = 1
        frames_map, labels_map, cats_map = {}, {}, {}
        for vid, scores in per_video_snippet_scores.items():
            n_frames = len(scores) * snippet_window
            frames_map[vid] = snippet_to_frame(
                scores, n_frames=n_frames,
                snippet_window=snippet_window, upsample_factor=upsample_factor,
            )
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
            cats_map[vid] = "Normal" if vid.endswith("_label_A") else "Abuse"
        return frames_map, labels_map, cats_map
```

**UCF target pattern (lines 194-227 — DIRECT TEMPLATE):**
```python
    # ---- UCF default path (and xd falls through to the same shape) ----
    ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
    ann_path = None
    if ann_dir_cfg:
        candidate = Path(ann_dir_cfg) / "ucf_temporal.txt"
        if candidate.exists():
            ann_path = candidate
    if ann_path is None:
        # D-04 canonical fallback
        ann_path = _PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"

    annos = parse_annotations(ann_path) if ann_path.exists() else {}

    # D-14: UCF PNG grid (64 frames) upsampled 10x -> original 30fps grid.
    snippet_window = 64
    upsample_factor = 10

    frames_map: dict = {}
    labels_map: dict = {}
    cats_map: dict = {}
    for vid, scores in per_video_snippet_scores.items():
        n_frames = len(scores) * snippet_window * upsample_factor
        if vid in annos:
            anno = annos[vid]
            cats_map[vid] = anno.category
            labels_map[vid] = frame_labels(anno, n_frames)
        else:
            cats_map[vid] = "Normal"
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
        frames_map[vid] = snippet_to_frame(
            scores, n_frames=n_frames,
            snippet_window=snippet_window, upsample_factor=upsample_factor,
        )
    return frames_map, labels_map, cats_map
```

**Imports needed (at module top):**
```python
from src.eval.xd_annotations import (
    parse_xd_annotations,
    xd_frame_labels,
)
```
(Mirror the existing line 45 `from src.eval.ucf_annotations import frame_labels, parse_annotations`.)

**Key notes for planner:**
1. **Replace lines 180-192 verbatim** — the new xd_i3d branch MUST (per RESEARCH.md lines 555-588, which is the verified reference implementation):
   - Resolve `ann_path` from `cfg["paths"]["annotations_dir"] / xd_temporal.txt` with `_PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"` as canonical fallback (same D-04 pattern as UCF branch).
   - Parse annotations via `parse_xd_annotations(ann_path)`.
   - For each `(vid, scores)` in `per_video_snippet_scores.items()`:
     - `n_frames = len(scores) * snippet_window` (D-08: `snippet_window=16`, `upsample_factor=1`, so no `* upsample_factor` term).
     - `frames_map[vid] = snippet_to_frame(scores, n_frames=n_frames, snippet_window=16, upsample_factor=1)`.
     - IF `vid in annos`: `labels_map[vid] = xd_frame_labels(annos[vid], n_frames)`; `cats_map[vid] = annos[vid].category`.
     - ELSE: `labels_map[vid] = np.zeros(n_frames, dtype=np.int64)`; `cats_map[vid] = "Normal"` (this is the D-13/RESEARCH.md line 548 contract — Wu file OMITS normals; the `if vid in annos` guard is REQUIRED).
2. **Snippet window differs from UCF** — UCF uses `snippet_window=64 * upsample_factor=10`; xd_i3d uses `snippet_window=16 * upsample_factor=1`. This is per CONTEXT.md D-08 verified from RESEARCH.md I3D Cache Validation bit-identical check against XDVioDet `gt.npy`.
3. **C4 guard propagates for free** — `snippet_to_frame` (src/eval/snippet_to_frame.py:54-59) already asserts length drift < 2×tol; downstream `compute_frame_metrics` (D-09) hard-asserts `len(frame_scores) == len(frame_labels)` before sklearn. No new guard code needed here.
4. **Keep all 3 return values:** `(frames_map, labels_map, cats_map)`. The cats_map IS populated for Phase 4c forward-compat per CONTEXT.md D-10; Phase 4b's `per_category.csv` reuses the existing `_write_per_category_csv` writer unchanged (D-13). For the rtfm variant, `per_category` will be computed naturally by `compute_frame_metrics` for whatever categories appear.
5. **Do NOT touch the UCF branch** (lines 194-227). Do NOT change the signature `_build_frame_arrays(cfg, per_video_snippet_scores)` or return shape.

---

### `tests/test_xd_annotations.py` (test, unit)

**Analog:** `tests/test_ucf_annotations.py` (exact mirror, file-for-file)

**Fixture pattern (test_ucf_annotations.py uses `ucf_temporal_path` fixture from conftest.py lines 88-96):**
```python
@pytest.fixture
def ucf_temporal_path():
    """Real Sultani 2018 annotation file committed at data/annotations/ucf_temporal.txt (D-04)."""
    p = PROJECT_ROOT / "data" / "annotations" / "ucf_temporal.txt"
    if not p.exists():
        pytest.skip(
            "data/annotations/ucf_temporal.txt not present; Plan 04-01 Task 1 creates it"
        )
    return p
```

**Test case templates to mirror (lines 40-226 of analog):**

B1-equivalent: real-file parse smoke (scope: 500 entries, pick a known Wu entry):
```python
def test_parse_annotations_real_file(xd_temporal_path):
    """B1: parsing real Wu file yields >= 500 entries; verify a known entry."""
    annos = parse_xd_annotations(xd_temporal_path)
    assert len(annos) >= 500, f"expected >= 500, got {len(annos)}"
    # Pick a known verified entry (from RESEARCH.md §Wu Annotation Format)
    known_id = "Bad.Boys.1995__#01-33-51_01-34-37_label_B2-0-0"
    # ... (planner: find a stable known entry in the downloaded file during test-writing)
```

B2/B6 synthetic normal test (no Normal rows in Wu file → synthetic only, tests the guard semantic):
```python
def test_parse_normal_video_synthetic(tmp_path):
    """B2: Wu omits normals; synthesize one entry to confirm parser is robust."""
    # NOTE: Wu file has no normals, so this test exercises "missing-annotation = normal"
    # semantics at the CALLER level (_build_frame_arrays), not the parser.
    # Alt: skip this test; add test_missing_key_handled_by_caller in test_evaluate_xd_i3d.py.
```

B3/B5 multi-interval pattern (CRITICAL — Wu supports arbitrary K>=1 intervals, unlike UCF's fixed 2):
```python
def test_parse_multi_interval_3_intervals(tmp_path):
    """B3-extended: Wu row with 3 intervals (7 columns) parsed correctly."""
    f = tmp_path / "anno.txt"
    f.write_text("v_label_B4-0-0 100 200 300 400 500 600\n", encoding="utf-8")
    annos = parse_xd_annotations(f)
    a = annos["v_label_B4-0-0"]
    assert len(a.intervals) == 3
    assert a.intervals == ((100, 200), (300, 400), (500, 600))
```

B4/B5 frame_labels pattern:
```python
def test_xd_frame_labels_union_3_intervals(tmp_path):
    """B5-extended: 3-interval union produces correct label vector."""
    f = tmp_path / "anno.txt"
    f.write_text("v_label_B4-0-0 100 200 300 400 500 600\n", encoding="utf-8")
    annos = parse_xd_annotations(f)
    labels = xd_frame_labels(annos["v_label_B4-0-0"], n_frames=700)
    assert labels[100:200].sum() == 100
    assert labels[300:400].sum() == 100
    assert labels[500:600].sum() == 100
    assert labels[200:300].sum() == 0
    assert labels[400:500].sum() == 0
```

B7 clamping pattern (verbatim from analog):
```python
def test_xd_frame_labels_clamps_end(tmp_path):
    """B7: interval (50, 120) with n_frames=100 → labels[50:100] == 1 (no OOB)."""
    f = tmp_path / "anno.txt"
    f.write_text("X_label_B1-0-0 50 120\n", encoding="utf-8")
    annos = parse_xd_annotations(f)
    labels = xd_frame_labels(annos["X_label_B1-0-0"], n_frames=100)
    assert labels.shape == (100,)
    assert (labels[50:100] == 1).all()
```

B8 malformed row pattern (odd endpoints — Wu-specific, differs from UCF 6-col):
```python
def test_malformed_odd_endpoints_raises(tmp_path):
    """B8: row with odd interval-endpoint count → ValueError."""
    f = tmp_path / "bad.txt"
    f.write_text("v_label_B1-0-0 100 200 300\n", encoding="utf-8")  # 3 endpoints = odd
    with pytest.raises(ValueError, match="odd number"):
        parse_xd_annotations(f)
```

**Key notes for planner:**
1. **Add `xd_temporal_path` fixture to `tests/conftest.py`** mirroring line 88-96 (UCF fixture) with `/data/annotations/xd_temporal.txt`.
2. **Coverage tiers (CONTEXT.md D-17):**
   - Real-file parse smoke (need file committed, otherwise `pytest.skip`).
   - Multi-interval synthetic test (Wu-specific — UCF is always 2).
   - `.mp4` suffix stripping test (RESEARCH.md line 655 — critical ID normalization).
   - Missing-normal-entry caller semantic (document that parser returns dict; caller must `if vid in annos` guard).
   - Category parsing test (`_label_B1-0-0` → "B1"; `_label_G-B2-B6` → "G" first-label; verified in RESEARCH.md lines 495-521).
   - Boundary: clamping, empty file, blank lines (mirror UCF lines 147-226).
3. **Import pattern mirror** (line 27-32 of analog):
   ```python
   from src.eval.xd_annotations import (
       VideoAnnotation,
       xd_frame_labels,
       parse_xd_annotations,
   )
   ```

---

### `tests/test_loaders_i3d.py` (test, unit)

**Analog:** `tests/test_i3d_dataset.py` (for fixture usage) + `tests/test_train_integration.py::_build_smoke_dataset` (for end-to-end loader assembly pattern)

**Fixture usage pattern** (from `test_i3d_dataset.py` lines 25-62, `synthetic_i3d_features` fixture):
```python
def test_test_mode_shape_and_label(synthetic_i3d_features):
    """D1: test mode returns [N, 1024] float32 with crops averaged; label correct."""
    fx = synthetic_i3d_features
    ds = I3DFeatureDataset(
        split_file=str(fx["test_split"]),
        feature_dir=str(fx["rgbtest"]),
        mode="test",
        T=32,
    )
    assert len(ds) == 3
    s0 = ds[0]
    assert s0["i3d"].ndim == 2, ...
    assert s0["i3d"].shape[1] == 1024
    assert s0["label"] == 1.0
```

**Minimal test case pattern for `build_dataloaders_i3d`:**
```python
def test_build_dataloaders_i3d_shapes(synthetic_i3d_features, tmp_path):
    """L1: build_dataloaders_i3d returns (nor, abn, val) with correct shapes after collate."""
    fx = synthetic_i3d_features
    # Build a tiny cfg dict matching rtfm_i3d.yaml schema
    cfg = {
        "seed": 42, "dataset": "xd_i3d",
        "paths": {
            "splits_dir": str(fx["train_split"].parent),
            "i3d_features": str(fx["rgb"].parent),  # parent of RGB/ and RGBTest/
        },
        "data": {"T": 32, "batch_size": 2, "num_workers": 0, "pin_memory": False},
    }
    (nor, abn), val = build_dataloaders_i3d(cfg)
    # Shape check after collate: B*5 flattened dim
    nb = next(iter(nor))
    assert nb["i3d"].shape[1] == 32  # T
    assert nb["i3d"].shape[2] == 1024  # D
    assert nb["i3d"].shape[0] == 2 * 5  # B*n_crops = 10
    assert nb["label"].shape == (10,)
```

**Collate shape test (L2):**
```python
def test_collate_i3d_train_flattens_5crop():
    """L2: collate transforms list of [5, T, 1024] dicts -> [B*5, T, 1024]."""
    samples = [
        {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": f"v{i}_label_A"}
        for i in range(3)
    ] + [
        {"i3d": torch.randn(5, 32, 1024), "label": 1.0, "video_id": f"w{i}_label_B1-0-0"}
        for i in range(3)
    ]
    out = collate_i3d_train(samples)
    assert out["i3d"].shape == (30, 32, 1024)
    assert out["label"].shape == (30,)
    assert len(out["video_id"]) == 30
    # First 5 labels are all 0.0 (crop-expanded from sample 0)
    assert (out["label"][:5] == 0.0).all()
    # Samples 15-20 are abnormal (sample 3 crops)
    assert (out["label"][15:20] == 1.0).all()
```

**Partitioning test (L3 — MIL bag balance):**
```python
def test_nor_abn_partitioning(synthetic_i3d_features):
    """L3: nor_loader yields only label=0 videos; abn_loader only label=1."""
    fx = synthetic_i3d_features  # 5 train videos: 3 normal (_label_A), 2 abnormal
    cfg = ...
    (nor, abn), _ = build_dataloaders_i3d(cfg)
    nb = next(iter(nor))
    assert (nb["label"] == 0.0).all()
    ab = next(iter(abn))
    assert (ab["label"] == 1.0).all()
```

**Key notes for planner:**
1. **Test targets per CONTEXT.md D-17:** (a) returns correct Loader tuple shape; (b) collate flattens correctly; (c) nor/abn partitioning is correct.
2. **Use existing `synthetic_i3d_features` fixture** (conftest.py lines 120-124) — 5 train videos + 3 test videos, alternating normal/abnormal, under tmp_path/i3d/RGB + tmp_path/i3d/RGBTest. Matches `make_synthetic_i3d` output in `tests/fixtures/synthetic_eval.py:79-131`.
3. **`cfg["paths"]["i3d_features"]` points to the parent of RGB/** per rtfm_i3d.yaml:10 and test_loader.py:114 (`Path(paths["i3d_features"]) / "RGBTest"`). The fixture returns `fx["rgb"]` = tmp_path/i3d/RGB, so `cfg["paths"]["i3d_features"] = str(fx["rgb"].parent)`.
4. **Do NOT require CUDA** — all tests run on CPU, `num_workers=0` for Windows determinism.
5. **Test split file** for val — the synthetic_i3d_features fixture only creates train + test splits; create a tiny tmp val split inline if val partitioning is tested separately, OR (simpler) use the train split as val for the test (the shape + partition contract is identical).
6. **4 normal + 4 abnormal mini-mock** per CONTEXT.md line 48 — the existing `synthetic_i3d_features` has 5 train (3A+2B) / 3 test (all B2). If 4+4 is needed, parametrize `make_synthetic_i3d(tmp_path, n_train=8, seed=0)` with the `i % 2` alternation.

---

### `tests/test_train_i3d.py` (test, unit)

**Analog:** `tests/test_train.py` (for CLI + CUBLAS smoke) + `tests/test_train_integration.py::test_smoke_2_epoch_produces_artifacts` (for e2e main() invocation)

**Test patterns to mirror:**

T1: `train_one_epoch_i3d` signature/loss-finite test (mirror `test_train.py::test_optimizer_config` minimal invocation style):
```python
def test_train_one_epoch_i3d_loss_finite(synthetic_i3d_features, tmp_path):
    """T1: train_one_epoch_i3d runs one step; loss is finite + float."""
    fx = synthetic_i3d_features
    cfg = ...  # minimal cfg dict
    (nor, abn), _ = build_dataloaders_i3d(cfg)
    model = build_model(variant="rtfm_i3d", i3d_dim=1024, head_hidden=[128, 32], dropout=0.3)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    loss = train_one_epoch_i3d(model, nor, abn, optimizer, "cpu", train_cfg={
        "k_topk": 3, "margin": 1.0, "lam_sparse": 8e-3, "lam_smooth": 8e-4,
    })
    assert isinstance(loss, float)
    assert loss == loss  # NaN check
    assert loss < float("inf")
```

T2: `validate_i3d` signature match:
```python
def test_validate_i3d_signature_matches_validate(synthetic_i3d_features, tmp_path):
    """T2: validate_i3d returns float; signature (model, val_loader, device, train_cfg) -> float."""
    import inspect
    from src.train import validate, validate_i3d
    sig1 = inspect.signature(validate)
    sig2 = inspect.signature(validate_i3d)
    assert list(sig1.parameters.keys()) == list(sig2.parameters.keys())
```

T3: dispatch branch routed correctly (mirror `test_train.py::test_cli_help` subprocess style, adapted):
```python
def test_main_dispatches_xd_i3d(synthetic_i3d_features, tmp_path):
    """T3: main() with cfg.dataset==xd_i3d invokes train_one_epoch_i3d, not train_one_epoch."""
    # Build a 1-epoch YAML pointing at synthetic features
    cfg_path = _build_smoke_xd_i3d_config(synthetic_i3d_features, tmp_path)
    rc = main(["--config", str(cfg_path), "--epochs", "1"])
    assert rc == 0
    # Verify artifacts landed (mirror test_smoke_2_epoch_produces_artifacts:128-138)
    run = _latest_run(tmp_path / "results")
    assert (run / "best_model.pth").exists()
    assert (run / "train_log.csv").exists()
```

T4: helper builder (mirror `_build_smoke_dataset` from test_train_integration.py:29-70):
```python
def _build_smoke_xd_i3d_config(fx, tmp_path) -> Path:
    """Build a 1-epoch xd_i3d YAML pointing at the synthetic_i3d_features fixture."""
    results = tmp_path / "results"
    results.mkdir(exist_ok=True)
    cfg = {
        "seed": 42, "dataset": "xd_i3d",
        "paths": {
            "i3d_features": str(fx["rgb"].parent),
            "splits_dir": str(fx["train_split"].parent),
            "results_dir": str(results),
        },
        "model": {"variant": "rtfm_i3d", "i3d_dim": 1024,
                  "head_hidden": [128, 32], "dropout": 0.3},
        "data": {"T": 32, "batch_size": 2, "num_workers": 0, "pin_memory": False},
        "train": {
            "lr": 1e-4, "weight_decay": 1e-2, "epochs": 1, "warmup_epochs": 0,
            "patience": 10, "k_topk": 3, "margin": 1.0,
            "lam_sparse": 8e-3, "lam_smooth": 8e-4,
        },
        "wandb": {"project": "violencecc", "mode": "disabled", "tags": []},
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    return cfg_path
```

**Key notes for planner:**
1. **3 test classes per CONTEXT.md D-17:** loss-finite, signature-match, dispatch-branch. All synthetic, ~3 tests total.
2. **Reuse `synthetic_i3d_features` fixture** — same pattern as `test_i3d_dataset.py`; no new fixture needed.
3. **`_latest_run(results)` helper** lives in `test_train_integration.py:122-125` — duplicate or import (if imported, watch for test-collection order issues). Simpler: duplicate the 3-line helper.
4. **Do not test the full RTFM gate empirically here** — that's a Phase 4b execution-step deliverable (not a unit test). Unit tests must complete in <10 seconds.
5. **CPU-only** — mirror `test_smoke_2_epoch_produces_artifacts`'s use of `--num_workers 0`.

---

### `tests/test_evaluate_xd_i3d.py` (test, unit + subprocess)

**Analog:** `tests/test_evaluate_cli.py` (exact structural mirror)

**Fixture pattern (lines 24-74 of analog — `prepared_run_dir` that builds a run_dir with config_snapshot.json + best_model.pth):**
```python
@pytest.fixture
def prepared_xd_i3d_run_dir(tmp_path, synthetic_i3d_features):
    """Build an xd_i3d run_dir containing config_snapshot.json + best_model.pth
    pointing at the synthetic 5-crop fixture.
    """
    fx = synthetic_i3d_features
    run_dir = tmp_path / "xd_i3d_rtfm_i3d_s42"
    run_dir.mkdir(parents=True)

    # Build/copy xd_temporal.txt (synthetic, matching fix test IDs)
    ann_dir = tmp_path / "data" / "annotations"
    ann_dir.mkdir(parents=True)
    # Synthesize annotation rows for the 3 test IDs (all abnormal in fixture)
    ann_lines = [f"{vid} 50 100" for vid in fx["test_ids"]]
    (ann_dir / "xd_temporal.txt").write_text("\n".join(ann_lines) + "\n", encoding="utf-8")

    cfg = {
        "seed": 42, "dataset": "xd_i3d",
        "paths": {
            "i3d_features": str(fx["rgb"].parent),
            "splits_dir": str(fx["train_split"].parent),
            "annotations_dir": str(ann_dir),
            "results_dir": str(tmp_path),
        },
        "data": {"T": 32},
        "model": {"variant": "rtfm_i3d", "i3d_dim": 1024,
                  "head_hidden": [128, 32], "dropout": 0.3},
        "wandb": {"mode": "disabled"},
    }
    snapshot = {"version": 1, "config": cfg, "git": {"sha": "test", "dirty": False}}
    (run_dir / "config_snapshot.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )

    from src.models.registry import build_model
    model = build_model(**cfg["model"])
    torch.save(model.state_dict(), run_dir / "best_model.pth")
    return run_dir
```

**Test patterns (mirror `test_evaluate_cli.py:87-131`):**

E1-equivalent — CLI smoke:
```python
def test_evaluate_xd_i3d_cli_smoke(prepared_xd_i3d_run_dir):
    """E1: CLI on xd_i3d path exits 0 and writes all 4 outputs."""
    out = subprocess.run(
        [sys.executable, "src/evaluate.py",
         "--run-dir", str(prepared_xd_i3d_run_dir), "--split", "test"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    assert out.returncode == 0, f"stderr={out.stderr}\nstdout={out.stdout}"
    for name in ("eval_metrics.json", "eval_scores.npz", "per_category.csv", ".done"):
        assert (prepared_xd_i3d_run_dir / name).exists()
```

E2-equivalent — C4 guard trips on length mismatch (CONTEXT.md D-09):
```python
def test_c4_guard_trips_on_length_mismatch(tmp_path, synthetic_i3d_features):
    """C4 (D-09): mismatched n_frames between annotation and snippet grid raises."""
    # Construct per_video_snippet_scores with deliberately wrong-length scores
    # and call _build_frame_arrays directly. Expect AssertionError or ValueError.
    from src.evaluate import _build_frame_arrays
    cfg = {"dataset": "xd_i3d", "paths": {"annotations_dir": str(tmp_path)}}
    # Synthesize an annotation with end=1000 but scores implying n_frames=160
    (tmp_path / "xd_temporal.txt").write_text("fake_vid_label_B1-0-0 50 2000\n")
    fake_scores = {"fake_vid_label_B1-0-0": np.random.randn(10).astype(np.float32)}
    # n_frames = 10 * 16 = 160, but annotation says end=2000 > 160 (clamped OK).
    # The TRUE C4 mismatch test: directly call compute_frame_metrics with drifted arrays.
    ...  # planner: lift pattern from test_snippet_to_frame.py C4 tests
```

**Key notes for planner:**
1. **3 test classes per CONTEXT.md D-17:** `_build_frame_arrays` xd_i3d path returns correct shapes; C4 guard trips on mismatch; CLI smoke writes 4 outputs.
2. **Synthesize annotations matching fixture test IDs:** The fixture's 3 test videos have IDs like `t000_label_B2-0-0`. The tests must WRITE a tiny `xd_temporal.txt` with matching IDs before invoking `_build_frame_arrays`.
3. **Test that normal videos (missing from annotation) produce all-zero labels** (RESEARCH.md line 548 sentinel-guard pattern):
   ```python
   def test_missing_annotation_defaults_to_normal(prepared_xd_i3d_run_dir):
       # If annotation file has NO entry for a test video, labels_map[vid] = zeros.
       ...
   ```
4. **Reuse `PROJECT_ROOT` pattern** from line 21 of analog:
   ```python
   PROJECT_ROOT = Path(__file__).resolve().parent.parent
   ```
5. **CONTEXT.md D-09 hard assert:** verify that `compute_frame_metrics` from `src/eval/metrics.py` asserts length before sklearn — already tested in `tests/test_eval_metrics.py`, so here just unit-test the integration (`_build_frame_arrays` → `compute_frame_metrics` chain).

---

## Shared Patterns

### Pattern A: `__future__ annotations` + `Path`-typed IO

**Source:** `src/eval/ucf_annotations.py` lines 18-24
**Apply to:** `src/eval/xd_annotations.py`, both new test modules

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
```

### Pattern B: `seed_worker` + `make_generator` imports with fallback

**Source:** `src/data/loaders.py` lines 30-49
**Apply to:** any new dataloader construction (no changes needed — keep the existing `try/except` in `build_dataloaders_i3d`; seed_worker/make_generator are already module-level).

```python
try:  # pragma: no cover - import shim for parallel-worktree ergonomics
    from src.utils.seed import seed_worker, make_generator  # type: ignore
except ImportError:  # fallback mirrors RESEARCH.md §2.5
    import random as _random

    def seed_worker(worker_id: int) -> None:
        worker_seed = torch.initial_seed() % 2**32
        np.random.seed(worker_seed)
        _random.seed(worker_seed)

    def make_generator(seed: int) -> torch.Generator:
        g = torch.Generator()
        g.manual_seed(int(seed))
        return g
```

### Pattern C: DataLoader kwargs for deterministic shuffling (TRN-03)

**Source:** `src/data/loaders.py` lines 128-145
**Apply to:** `build_dataloaders_i3d` — REUSE VERBATIM

```python
    g_nor = make_generator(seed)
    g_abn = make_generator(seed + 1)
    g_val = make_generator(seed + 2)

    persistent = num_workers > 0
    common = dict(
        batch_size=bs,
        num_workers=num_workers,
        worker_init_fn=seed_worker,
        pin_memory=pin_memory,
        persistent_workers=persistent,
        drop_last=True,
    )

    nor_loader = DataLoader(Subset(train_full, nor_idx), shuffle=True,
                            generator=g_nor, **common)
```

**ADD `collate_fn=collate_i3d_train` to `common` dict** for the i3d path. That's the single divergence from the UCF dataloader.

### Pattern D: MIL loss invocation with k_topk/margin/lam_sparse/lam_smooth

**Source:** `src/train.py::train_one_epoch` lines 101-107
**Apply to:** `train_one_epoch_i3d`, `validate_i3d` — REUSE VERBATIM

```python
loss = mil_ranking_loss(
    scores, mask, n_normal=n_normal,
    k=int(train_cfg["k_topk"]),
    margin=float(train_cfg["margin"]),
    lam_sparse=float(train_cfg["lam_sparse"]),
    lam_smooth=float(train_cfg["lam_smooth"]),
)
```

### Pattern E: C4-guarded snippet_to_frame call

**Source:** `src/evaluate.py::_build_frame_arrays` UCF branch lines 223-226
**Apply to:** xd_i3d branch rewrite — MIRROR EXACTLY

```python
frames_map[vid] = snippet_to_frame(
    scores, n_frames=n_frames,
    snippet_window=snippet_window, upsample_factor=upsample_factor,
)
```

Only difference: `snippet_window=16` (not 64), `upsample_factor=1` (not 10), `n_frames = len(scores) * snippet_window` (no `* upsample_factor` since it's 1).

### Pattern F: Annotation-file resolution with D-04 canonical fallback

**Source:** `src/evaluate.py::_build_frame_arrays` lines 195-203
**Apply to:** xd_i3d branch rewrite — MIRROR but swap `ucf_temporal.txt` → `xd_temporal.txt`

```python
    ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
    ann_path = None
    if ann_dir_cfg:
        candidate = Path(ann_dir_cfg) / "xd_temporal.txt"  # was "ucf_temporal.txt"
        if candidate.exists():
            ann_path = candidate
    if ann_path is None:
        ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"  # was ucf_temporal.txt
```

### Pattern G: pytest subprocess CLI smoke test

**Source:** `tests/test_evaluate_cli.py` lines 77-94
**Apply to:** `test_evaluate_xd_i3d.py` — MIRROR EXACTLY

```python
def _run_evaluate(run_dir: Path, split: str = "test"):
    return subprocess.run(
        [sys.executable, "src/evaluate.py",
         "--run-dir", str(run_dir), "--split", split],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True,
    )
```

### Pattern H: Synthetic config dict from fixture directories

**Source:** `tests/test_evaluate_cli.py::prepared_run_dir` lines 24-74
**Apply to:** `test_loaders_i3d.py`, `test_train_i3d.py`, `test_evaluate_xd_i3d.py`

Cfg dict shape (swap `skeleton_features`+`clip_features` for `i3d_features`; swap `gated_fusion` for `rtfm_i3d`):
```python
cfg = {
    "seed": 42,
    "dataset": "xd_i3d",
    "paths": {
        "i3d_features": str(fx["rgb"].parent),
        "splits_dir": str(fx["train_split"].parent),
        "annotations_dir": str(ann_dir),
        "results_dir": str(tmp_path),
    },
    "data": {"T": 32, "batch_size": 2, "num_workers": 0, "pin_memory": False},
    "model": {
        "variant": "rtfm_i3d", "i3d_dim": 1024,
        "head_hidden": [128, 32], "dropout": 0.3,
    },
    "train": {
        "lr": 1e-4, "weight_decay": 1e-2, "epochs": 1, "warmup_epochs": 0,
        "patience": 10, "k_topk": 3, "margin": 1.0,
        "lam_sparse": 8e-3, "lam_smooth": 8e-4,
    },
    "wandb": {"project": "violencecc", "mode": "disabled", "tags": []},
}
```

## No Analog Found

None. All 10 files (6 create + 3 modify with 1 in-file branch + 4 tests) have exact or near-exact in-repo analogs. The only novel code is:
- **`collate_i3d_train`** body (pure PyTorch reshape; no existing custom collate, but the pattern is trivial — `torch.stack` + `.reshape` + `.repeat_interleave`).
- **D-12 one-shot audit log** (new print statement at first step of first 3 epochs; no existing instrumentation in `train_one_epoch`).

These are both documented inline above with verified code sketches.

## Reference-Only (Files to Understand, Not Modify)

| File | Why Read |
|------|----------|
| `src/data/i3d_dataset.py` | __getitem__ return shape: `[5, T, 1024]` train/val (line 163), `[N, 1024]` test (line 154). `collate_i3d_train` output MUST match this input contract. |
| `src/models/rtfm_i3d.py` | forward signature `(skel, clip, i3d, mask)` (line 51); expects `i3d: [B, T, 1024]`; returns `[B, T]` (after squeeze). `train_one_epoch_i3d` must pass kwargs accordingly. |
| `src/losses/mil_loss.py` | `mil_ranking_loss(scores: [2B, T], mask: [2B, T], n_normal: int, k, margin, lam_sparse, lam_smooth)` signature (lines 52-60). mask must be synthesized as all-ones in the i3d path. |
| `src/eval/test_loader.py:103-117` | xd_i3d test-path dispatch (already correct). No changes. |
| `src/eval/snippet_to_frame.py` | C4 guard semantics (length drift tolerance); reused unchanged by xd_i3d branch. |
| `src/eval/metrics.py::compute_frame_metrics` | CONTEXT.md D-09 hard assert lives here (reused for xd_i3d automatically). |
| `configs/rtfm_i3d.yaml` | READ-ONLY per CONTEXT.md. `data.batch_size=3` is load-bearing (Pitfall 3). Do not modify unless D-11 fallback triggers. |
| `scripts/run_ablations.py::QUEUES["rtfm_gate"]` line 84 | RunSpec is reusable unchanged per D-15. Phase 4b execution invokes `python scripts/run_ablations.py --queue rtfm_gate --no-preflight`. |

## Metadata

**Analog search scope:** `src/data/`, `src/eval/`, `src/train.py`, `src/evaluate.py`, `src/models/rtfm_i3d.py`, `src/losses/mil_loss.py`, `tests/` (all), `data/annotations/`, `configs/rtfm_i3d.yaml`
**Files scanned:** 18 source + 6 test + 2 config/data = 26 files read
**Pattern extraction date:** 2026-04-16

## PATTERN MAPPING COMPLETE
