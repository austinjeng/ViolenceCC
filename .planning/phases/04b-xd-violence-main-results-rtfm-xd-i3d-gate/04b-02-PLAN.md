---
phase: 04b
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - src/data/loaders.py
  - tests/test_loaders_i3d.py
autonomous: true
requirements:
  - EVAL-01
tags: [data, dataloader, i3d, collate, mil-bag]
user_setup: []

must_haves:
  truths:
    - "build_dataloaders_i3d(cfg) returns ((nor_loader, abn_loader), val_loader) where nor_loader only yields label=0 samples and abn_loader only yields label=1 samples"
    - "collate_i3d_train flattens a batch of B dicts each with i3d shape [5, T, 1024] into a dict with i3d shape [B*5, T, 1024], label shape [B*5], mask shape [B*5, T] (all ones), and video_id list of length B*5"
    - "build_dataloaders_i3d hardcodes xd_train.txt / xd_val.txt split paths (NOT pattern-matched via {dataset}_val.txt since cfg.dataset=='xd_i3d' would resolve to non-existent xd_i3d_val.txt)"
    - "build_dataloaders_i3d asserts len(val_abn_idx) > 0 to guard against Pitfall 4 filter collapse (Open Question #1 resolution)"
    - "collate_i3d_train uses .repeat_interleave(5) for label replication (NOT .repeat(5) which produces wrong ordering; Pitfall 4 guard)"
    - "data.batch_size=3 from rtfm_i3d.yaml is honored (NOT default 16); effective MIL bag size = 3*5 = 15 matching k_topk=3"
    - "collate_i3d_train is defined at module scope (Windows spawn-safe per Pitfall 7)"
  artifacts:
    - path: "src/data/loaders.py"
      provides: "ADDED build_dataloaders_i3d(cfg) + collate_i3d_train() alongside existing build_dataloaders() (existing function UNCHANGED)"
      adds: ["def collate_i3d_train", "def build_dataloaders_i3d"]
    - path: "tests/test_loaders_i3d.py"
      provides: "Unit tests for build_dataloaders_i3d + collate_i3d_train"
      min_lines: 100
  key_links:
    - from: "src/data/loaders.py"
      to: "src/data/i3d_dataset.py"
      via: "from src.data.i3d_dataset import I3DFeatureDataset"
      pattern: "from src\\.data\\.i3d_dataset import I3DFeatureDataset"
    - from: "tests/test_loaders_i3d.py"
      to: "tests/conftest.py"
      via: "synthetic_i3d_features fixture"
      pattern: "synthetic_i3d_features"
    - from: "tests/test_loaders_i3d.py"
      to: "src/data/loaders.py"
      via: "from src.data.loaders import build_dataloaders_i3d, collate_i3d_train"
      pattern: "from src\\.data\\.loaders import"
---

<objective>
Add `build_dataloaders_i3d(cfg)` and `collate_i3d_train()` to `src/data/loaders.py` alongside (NOT replacing) the existing `build_dataloaders()`. Per D-04 parallel-functions decision, the existing UCF/XD fusion path is untouched. The new function consumes `I3DFeatureDataset` directly, partitions train videos into normal / abnormal subsets by the `_label_A` suffix (D-06), and wires a custom collate that flattens the 5-crop dimension into the batch dimension (D-05 crop-as-sample). Also creates `tests/test_loaders_i3d.py` with 5 unit tests covering shape correctness, partitioning, label replication, mask synthesis, and batch_size honoring.

Purpose: The RTFM XD-I3D training path requires a DataLoader that yields `{i3d: [B*5, T, 1024], label: [B*5], mask: [B*5, T], video_id: list}`. The existing `build_dataloaders()` cannot serve this because it constructs `MILFeatureDataset` with paired `skel+clip` contracts that fail for i3d-only configs (KeyError: 'skeleton_features' — this is the exact Rule 4 failure from Phase 4 Plan 04-06 UAT). This plan delivers the clean parallel function + collate contract that Plan 04b-03 will wire into `train_one_epoch_i3d`.

Output: `src/data/loaders.py` with two new module-level functions added (~60 LOC), `tests/test_loaders_i3d.py` with 5 new unit tests (~120 LOC).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-CONTEXT.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-VALIDATION.md

<!-- CRITICAL analog (mirror its structure for build_dataloaders_i3d): -->
@src/data/loaders.py

<!-- Dataset being consumed (read-only, already compatible): -->
@src/data/i3d_dataset.py

<!-- Test fixture source (read-only, already compatible): -->
@tests/conftest.py
@tests/fixtures/synthetic_eval.py

<interfaces>
<!-- Contract executor must implement and match. No codebase exploration needed beyond the analog files above. -->

**I3DFeatureDataset contract (src/data/i3d_dataset.py, already shipped):**
```python
# Constructor:
I3DFeatureDataset(
    split_file: str,        # path to xd_train.txt / xd_val.txt / xd_test.txt
    feature_dir: str,       # path to RGB/ (train+val) or RGBTest/ (test)
    mode: Literal["train", "val", "test"],
    T: int = 32,
    n_crops: int = 5,
)

# Public attributes (verified from src/data/i3d_dataset.py:57-71):
self.video_ids: List[str]  # e.g. ["v_label_A", "w_label_B1-0-0", ...]

# __getitem__ returns:
# mode="train" or mode="val": {"i3d": Tensor[5, T, 1024], "label": float, "video_id": str}
# mode="test":                 {"i3d": Tensor[N, 1024], "label": float, "video_id": str}
#   (test mode averages crops; N = variable snippet count after resample)
```

**mil_ranking_loss contract (src/losses/mil_loss.py, already shipped):**
```python
def mil_ranking_loss(
    scores: Tensor,   # [2B, T]
    mask: Tensor,     # [2B, T] — REQUIRED; used by masked_fill before top-k
    n_normal: int,    # number of normal samples in the batch (first n_normal rows are normal)
    k: int = 3,       # top-k snippets per bag
    margin: float = 1.0,
    lam_sparse: float = 8e-3,
    lam_smooth: float = 8e-4,
) -> Tensor
```

**RTFMI3D forward contract (src/models/rtfm_i3d.py, already shipped):**
```python
def forward(self, skel=None, clip=None, i3d=None, mask=None) -> Tensor:
    # ignores skel/clip; accepts i3d: [B, T, 1024]; returns scores [B, T]
```

**Existing build_dataloaders signature (src/data/loaders.py, DO NOT MODIFY):**
```python
def build_dataloaders(cfg: dict) -> Tuple[Tuple[DataLoader, DataLoader], DataLoader]:
    # Returns ((nor_loader, abn_loader), val_loader) for UCF/XD fusion paths
    # Uses MILFeatureDataset with paired skel+clip contracts
    # NOT to be touched — Phase 4b adds parallel build_dataloaders_i3d
```

**Required public surface after this plan:**
```python
def collate_i3d_train(batch_list: list[dict]) -> dict
def build_dataloaders_i3d(cfg: dict) -> Tuple[Tuple[DataLoader, DataLoader], DataLoader]
```

**Synthetic test fixture (tests/conftest.py already ships):**
```python
@pytest.fixture
def synthetic_i3d_features(tmp_path):
    """5 train (3 _label_A + 2 _label_B1-0-0) + 3 test (all B2). Returns dict with:
        "rgb": Path to .../i3d/RGB/       (train features dir)
        "rgbtest": Path to .../i3d/RGBTest/
        "train_split": Path to xd_train.txt
        "test_split": Path to xd_test.txt
        "test_ids": List[str] of test video IDs
    """
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add collate_i3d_train + build_dataloaders_i3d to src/data/loaders.py</name>
  <files>src/data/loaders.py</files>
  <read_first>
    - src/data/loaders.py (full file — read existing build_dataloaders at lines 52-157 to mirror its structure)
    - src/data/i3d_dataset.py (full file — understand __getitem__ return contract at lines 148-167)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "Example 1: src/data/loaders.py additions" (lines 843-915) for the verified draft
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "src/data/loaders.py::build_dataloaders_i3d" (lines 161-308) for the detailed pattern analog
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "Open Questions" (lines 1029-1044) for the Q1 (val partition assertion) and Q2 (explicit xd_val.txt) resolutions
  </read_first>
  <behavior>
    - Test 1: `collate_i3d_train` accepts `[{i3d: Tensor[5, 32, 1024], label: 0.0, video_id: "v0"}, ...]` and returns `{i3d: Tensor[B*5, 32, 1024], label: Tensor[B*5] (float32), mask: Tensor[B*5, 32] (all ones), video_id: List[str] length B*5}`
    - Test 2: `collate_i3d_train` replicates each video's label consecutively via `repeat_interleave(5)` — for a batch `[n, n, a]` with labels `[0, 0, 1]`, output labels are `[0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1]`
    - Test 3: `build_dataloaders_i3d(cfg)` returns `((nor_loader, abn_loader), val_loader)` where iterating `nor_loader` yields batches with `label.max() == 0.0` and `abn_loader` yields batches with `label.min() == 1.0`
    - Test 4: `build_dataloaders_i3d` with `cfg.data.batch_size=3` yields batches with first dim = 15 (= 3 * 5 crops) per D-05
    - Test 5: `build_dataloaders_i3d` raises `AssertionError` if val partition has no abnormal videos (Open Question #1 hard assertion)
  </behavior>
  <action>
    Open `src/data/loaders.py` and add the following to the module. Key constraints:
    - BOTH new functions MUST live at module scope (NOT inside other functions) — Pitfall 7 Windows pickling requirement
    - Do NOT modify `build_dataloaders` — it is D-04 explicitly the untouched UCF/XD fusion path
    - Do NOT rename any existing function
    - Preserve the existing `try/except` import of `seed_worker, make_generator` from `src.utils.seed`

    Step 1 — Add the import at the top of the file (after existing `from src.data.dataset import MILFeatureDataset`):
    ```python
    from src.data.i3d_dataset import I3DFeatureDataset
    ```

    Step 2 — Add `collate_i3d_train` as a module-level function (place it IMMEDIATELY before `build_dataloaders` so it is visible to the new function being added):
    ```python
    def collate_i3d_train(batch_list: list) -> dict:
        """D-05 5-crop-as-sample flatten for I3DFeatureDataset (module-scope for Windows spawn).

        Input: list of B dicts from I3DFeatureDataset mode='train' or mode='val':
            {"i3d": Tensor[5, T, 1024], "label": float, "video_id": str}

        Output: dict suitable for RTFMI3D.forward + mil_ranking_loss:
            {
                "i3d":     Tensor[B*5, T, 1024],
                "label":   Tensor[B*5] float32  (each video's label repeated 5x via repeat_interleave),
                "mask":    Tensor[B*5, T] float32 (all ones; I3D has no padding — Pitfall 1 guard),
                "video_id": list[str] of length B*5 (each vid repeated 5x consecutively)
            }

        Shape contract: first dim of `i3d` after collate = batch_size * n_crops.
        With rtfm_i3d.yaml batch_size=3, this yields effective MIL bag size 15 matching k_topk=3 (Pitfall 3).
        """
        # Stack the [5, T, 1024] i3d tensors into [B, 5, T, 1024].
        i3d = torch.stack([s["i3d"] for s in batch_list], dim=0)
        B, n_crops, T, D = i3d.shape
        # Shape assertion (Pitfall 4 — crop-padding inside _load_crops should ensure 5).
        assert n_crops == 5 and D == 1024, (
            f"collate_i3d_train expected [B, 5, T, 1024], got {tuple(i3d.shape)}"
        )
        i3d_flat = i3d.reshape(B * n_crops, T, D)

        # Labels: each per-video label repeated CONSECUTIVELY 5 times (Pitfall 4 guard).
        # repeat_interleave(5) on [0, 0, 1] -> [0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1]
        labels = torch.tensor(
            [s["label"] for s in batch_list], dtype=torch.float32
        ).repeat_interleave(n_crops)

        # Mask: all ones (I3DFeatureDataset uses sample-with-replacement, no padding).
        mask = torch.ones(B * n_crops, T, dtype=torch.float32)

        # Video IDs: each id repeated consecutively 5 times to match label/i3d ordering.
        video_ids = [s["video_id"] for s in batch_list for _ in range(n_crops)]

        return {"i3d": i3d_flat, "label": labels, "mask": mask, "video_id": video_ids}
    ```

    Step 3 — Add `build_dataloaders_i3d` AFTER `build_dataloaders` (end of file is fine). The function structure is:
    ```python
    def build_dataloaders_i3d(cfg: dict):
        """Build paired (nor, abn) train loaders + val loader for xd_i3d dispatch (D-04).

        Parallel to build_dataloaders() but consumes I3DFeatureDataset (single feature tensor
        per video at train/val, 5-crop flattened to B*5 via collate_i3d_train).

        Parameters
        ----------
        cfg : dict
            Required keys::
                cfg["seed"]                   # int, e.g. 42
                cfg["dataset"]                # "xd_i3d"
                cfg["paths"]["splits_dir"]    # directory containing xd_train.txt / xd_val.txt
                cfg["paths"]["i3d_features"]  # parent dir containing RGB/ subdirectory
                cfg["data"]["batch_size"]     # int, e.g. 3 per rtfm_i3d.yaml + Pitfall 3
                cfg["data"]["T"]              # int, e.g. 32
                cfg["data"]["num_workers"]    # int, default 0
                cfg["data"]["pin_memory"]     # bool, default False

        Returns
        -------
        ((nor_loader, abn_loader), val_loader)
            nor_loader yields dict with i3d.shape[0] == batch_size * 5 (all label=0).
            abn_loader yields dict with i3d.shape[0] == batch_size * 5 (all label=1).
            val_loader yields dict with i3d.shape[0] == batch_size * 2 * 5 (mixed labels).

        Raises
        ------
        AssertionError
            If either the train normal partition or the val abnormal partition is empty
            (Open Question #1 guard — validate_i3d requires at least one abnormal val video
            to produce finite val loss).
        """
        paths = cfg["paths"]
        data_cfg = cfg["data"]
        T = data_cfg.get("T", 32)
        bs = data_cfg["batch_size"]                    # 3 per rtfm_i3d.yaml (Pitfall 3)
        num_workers = data_cfg.get("num_workers", 0)
        pin_memory = data_cfg.get("pin_memory", False)
        seed = int(cfg.get("seed", 42))

        # D-06 explicit xd_{train,val}.txt paths (Open Question #2 resolution):
        # DO NOT pattern-match {dataset}_val.txt — cfg['dataset']='xd_i3d' would resolve to
        # non-existent xd_i3d_val.txt. The XD val split file is named xd_val.txt.
        i3d_dir = str(paths["i3d_features"])
        train_ds = I3DFeatureDataset(
            split_file=f"{paths['splits_dir']}/xd_train.txt",
            feature_dir=f"{i3d_dir}/RGB",
            mode="train",
            T=T,
        )
        val_ds = I3DFeatureDataset(
            split_file=f"{paths['splits_dir']}/xd_val.txt",
            feature_dir=f"{i3d_dir}/RGB",
            mode="val",
            T=T,
        )

        # D-06 partition by _label_A suffix (reuses the pattern at line 123-126 of UCF path
        # but adapted to I3DFeatureDataset which has no .labels dict).
        nor_idx = [i for i, v in enumerate(train_ds.video_ids) if v.endswith("_label_A")]
        abn_idx = [i for i, v in enumerate(train_ds.video_ids) if not v.endswith("_label_A")]
        assert len(nor_idx) > 0, (
            "build_dataloaders_i3d: no normal train videos after Pitfall 4 filter; "
            "cannot form MIL bags"
        )
        assert len(abn_idx) > 0, (
            "build_dataloaders_i3d: no abnormal train videos after Pitfall 4 filter; "
            "cannot form MIL bags"
        )

        # Open Question #1: val set must have at least one abnormal video for validate_i3d
        # to produce finite val loss (otherwise early stopping breaks).
        val_abn = [v for v in val_ds.video_ids if not v.endswith("_label_A")]
        assert len(val_abn) > 0, (
            "build_dataloaders_i3d: val set has no abnormal videos after Pitfall 4 filter; "
            "validate_i3d would return float('inf') every epoch — check xd_val.txt coverage"
        )

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
            collate_fn=collate_i3d_train,
        )

        nor_loader = DataLoader(
            Subset(train_ds, nor_idx), shuffle=True, generator=g_nor, **common
        )
        abn_loader = DataLoader(
            Subset(train_ds, abn_idx), shuffle=True, generator=g_abn, **common
        )

        val_loader = DataLoader(
            val_ds,
            batch_size=bs * 2,
            num_workers=num_workers,
            worker_init_fn=seed_worker,
            pin_memory=pin_memory,
            persistent_workers=persistent,
            drop_last=False,
            shuffle=False,
            generator=g_val,
            collate_fn=collate_i3d_train,
        )
        return (nor_loader, abn_loader), val_loader
    ```

    Step 4 — Ensure `Subset` is imported at the top of the file (likely already imported; if not, add to the existing `from torch.utils.data import DataLoader` line).
  </action>
  <verify>
    <automated>python -c "from src.data.loaders import build_dataloaders_i3d, collate_i3d_train; import inspect; assert 'i3d' in inspect.signature(build_dataloaders_i3d).parameters or 'cfg' in inspect.signature(build_dataloaders_i3d).parameters; print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "def collate_i3d_train" src/data/loaders.py` outputs `1`
    - `grep -c "def build_dataloaders_i3d" src/data/loaders.py` outputs `1`
    - `grep -c "def build_dataloaders" src/data/loaders.py` outputs `>=2` (existing build_dataloaders + new build_dataloaders_i3d — since the latter has a longer name both match)
    - Existing `def build_dataloaders(cfg` (no suffix) still present: `grep -qE "^def build_dataloaders\(cfg" src/data/loaders.py` exit 0
    - Module imports cleanly: `python -c "from src.data.loaders import build_dataloaders_i3d, collate_i3d_train, build_dataloaders"` exit 0
    - `I3DFeatureDataset` is imported: `grep -q "from src.data.i3d_dataset import I3DFeatureDataset" src/data/loaders.py`
    - `repeat_interleave` is used for label replication (NOT `.repeat`): `grep -q "repeat_interleave" src/data/loaders.py`
    - `xd_train.txt` / `xd_val.txt` hardcoded (NOT `{dataset}_val.txt` pattern): `grep -q "xd_train.txt" src/data/loaders.py && grep -q "xd_val.txt" src/data/loaders.py`
    - Val abnormal assertion present: `grep -q "val set has no abnormal videos" src/data/loaders.py`
    - `mask = torch.ones` present (Pitfall 1 guard): `grep -q "torch.ones" src/data/loaders.py`
    - No regression: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_loaders.py -x --tb=short 2>/dev/null` exits 0 (if the file exists; skip if not) — the existing UCF/XD path must remain unbroken
  </acceptance_criteria>
  <done>Both functions added at module scope; imports clean; existing build_dataloaders unchanged; all assertions in place.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create tests/test_loaders_i3d.py with 5 tests covering shape, partitioning, collate, and assertions</name>
  <files>tests/test_loaders_i3d.py</files>
  <read_first>
    - tests/conftest.py (find the `synthetic_i3d_features` fixture; read its full implementation)
    - tests/fixtures/synthetic_eval.py (read the `make_synthetic_i3d` helper to understand fixture structure — what video IDs, what label distribution, where files land on disk)
    - tests/test_i3d_dataset.py (read any existing I3D-dataset tests to mirror their fixture-usage style)
    - src/data/loaders.py (after Task 1 — verify `build_dataloaders_i3d` + `collate_i3d_train` are importable)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "tests/test_loaders_i3d.py" (lines 716-802) for test case templates + fixture usage notes
  </read_first>
  <behavior>
    - Test 1 (`test_build_dataloaders_i3d_shape`): `build_dataloaders_i3d(cfg)` returns a 2-tuple whose first element is a 2-tuple of DataLoaders; first batch from nor_loader has i3d.shape == (batch_size * 5, T, 1024)
    - Test 2 (`test_collate_flattens_crops`): `collate_i3d_train` flattens a list of synthetic 6 samples (each [5, 32, 1024]) to i3d [30, 32, 1024]
    - Test 3 (`test_collate_label_replication`): labels are consecutively replicated 5x per video — for inputs labels [0, 0, 1], output labels == [0]*5 + [0]*5 + [1]*5
    - Test 4 (`test_collate_mask_all_ones`): `collate_i3d_train` output mask has shape [B*5, T] and `.sum() == B*5*T` (all ones)
    - Test 5 (`test_nor_abn_partition_nonempty`): `build_dataloaders_i3d` on synthetic fixture (3 normal + 2 abnormal train videos) yields nor_loader with label.max() == 0 and abn_loader with label.min() == 1
  </behavior>
  <action>
    Create NEW file `tests/test_loaders_i3d.py` with the following structure. Use the `synthetic_i3d_features` fixture (already shipped in conftest.py) for all tests — no new fixtures needed.

    ```python
    """Unit tests for build_dataloaders_i3d + collate_i3d_train (Phase 4b Plan 02).

    Covers VALIDATION.md rows 4b-02-01 / 4b-02-02 / 4b-02-03:
      - Returns tuple of (nor, abn, val) loaders
      - collate_i3d_train flattens [B, 5, T, 1024] -> [B*5, T, 1024]
      - nor/abn partition is non-empty on synthetic fixture

    Plus Pitfall guards:
      - Pitfall 1: mask is all-ones (not missing)
      - Pitfall 4: labels repeated consecutively 5x (not interleaved wrong)
    """
    from __future__ import annotations

    from pathlib import Path

    import pytest
    import torch

    from src.data.loaders import build_dataloaders_i3d, collate_i3d_train


    # ------------------------------------------------------------------
    # Helper: build a minimal cfg dict pointing at the synthetic_i3d_features fixture.
    # ------------------------------------------------------------------
    def _build_cfg(fx, batch_size: int = 2, T: int = 32) -> dict:
        """Build a minimal xd_i3d cfg dict for build_dataloaders_i3d."""
        # synthetic_i3d_features fixture returns paths under tmp_path/i3d/RGB + RGBTest
        # plus tmp_path/splits/xd_train.txt / xd_test.txt.
        # We must also create a tiny xd_val.txt (fixture may not provide it).
        splits_dir = fx["train_split"].parent
        val_split = splits_dir / "xd_val.txt"
        if not val_split.exists():
            # Minimal val split: reuse 1 normal + 1 abnormal train entry
            # (shape-contract test only; not training-convergence test)
            train_ids = fx["train_split"].read_text(encoding="utf-8").strip().splitlines()
            normal = next((v for v in train_ids if v.strip().endswith("_label_A")), None)
            abnorm = next((v for v in train_ids if not v.strip().endswith("_label_A")), None)
            assert normal is not None and abnorm is not None, "fixture missing mixed labels"
            val_split.write_text(f"{normal}\n{abnorm}\n", encoding="utf-8")
        return {
            "seed": 42,
            "dataset": "xd_i3d",
            "paths": {
                "splits_dir": str(splits_dir),
                "i3d_features": str(fx["rgb"].parent),   # parent of RGB/ and RGBTest/
            },
            "data": {
                "T": T,
                "batch_size": batch_size,
                "num_workers": 0,
                "pin_memory": False,
            },
        }


    # ==================================================================
    # VALIDATION.md row 4b-02-01: build_dataloaders_i3d returns (nor, abn, val)
    # ==================================================================
    def test_build_dataloaders_i3d_shape(synthetic_i3d_features):
        """Tuple shape: ((nor_loader, abn_loader), val_loader); batch i3d shape [bs*5, T, 1024]."""
        cfg = _build_cfg(synthetic_i3d_features, batch_size=2, T=32)
        (nor_loader, abn_loader), val_loader = build_dataloaders_i3d(cfg)

        # Verify iterable structure
        assert nor_loader is not None and abn_loader is not None and val_loader is not None

        # Verify batch shape after collate flattens 5 crops into batch dim
        batch = next(iter(nor_loader))
        assert "i3d" in batch and "label" in batch and "mask" in batch and "video_id" in batch
        assert batch["i3d"].shape == (2 * 5, 32, 1024), f"got {tuple(batch['i3d'].shape)}"
        assert batch["label"].shape == (2 * 5,)
        assert batch["mask"].shape == (2 * 5, 32)
        assert len(batch["video_id"]) == 2 * 5


    # ==================================================================
    # VALIDATION.md row 4b-02-02: collate_i3d_train flattens [B, 5, T, 1024] -> [B*5, T, 1024]
    # ==================================================================
    def test_collate_flattens_crops():
        """collate_i3d_train flattens the 5-crop dim into batch dim."""
        samples = [
            {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": f"v{i}_label_A"}
            for i in range(3)
        ] + [
            {"i3d": torch.randn(5, 32, 1024), "label": 1.0, "video_id": f"w{i}_label_B1-0-0"}
            for i in range(3)
        ]
        out = collate_i3d_train(samples)
        assert out["i3d"].shape == (6 * 5, 32, 1024)
        assert out["label"].shape == (6 * 5,)
        assert out["mask"].shape == (6 * 5, 32)
        assert len(out["video_id"]) == 6 * 5


    def test_collate_label_replication():
        """Each video's label replicated CONSECUTIVELY 5x (Pitfall 4 guard).

        Input labels [0.0, 0.0, 1.0] -> output labels [0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1].
        NOT [0,0,0, 0,0,0, 1,1,1, 0,0, 1,1, 0,1] (wrong interleaving).
        """
        samples = [
            {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": "v0_label_A"},
            {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": "v1_label_A"},
            {"i3d": torch.randn(5, 32, 1024), "label": 1.0, "video_id": "v2_label_B1-0-0"},
        ]
        out = collate_i3d_train(samples)
        labels = out["label"]
        # First 5 (sample 0) = 0.0, next 5 (sample 1) = 0.0, next 5 (sample 2) = 1.0
        assert (labels[0:5] == 0.0).all(), f"crops 0-4 not all 0: {labels[0:5]}"
        assert (labels[5:10] == 0.0).all(), f"crops 5-9 not all 0: {labels[5:10]}"
        assert (labels[10:15] == 1.0).all(), f"crops 10-14 not all 1: {labels[10:15]}"
        # Video IDs similarly replicated
        vids = out["video_id"]
        assert vids[0:5] == ["v0_label_A"] * 5
        assert vids[5:10] == ["v1_label_A"] * 5
        assert vids[10:15] == ["v2_label_B1-0-0"] * 5


    def test_collate_mask_all_ones():
        """Pitfall 1 guard: mask is all-ones tensor (no padding; required by mil_ranking_loss)."""
        samples = [
            {"i3d": torch.randn(5, 32, 1024), "label": 0.0, "video_id": f"v{i}"}
            for i in range(4)
        ]
        out = collate_i3d_train(samples)
        mask = out["mask"]
        assert mask.shape == (4 * 5, 32)
        assert mask.sum().item() == 4 * 5 * 32, f"mask not all ones: sum={mask.sum()}"
        assert mask.dtype == torch.float32


    # ==================================================================
    # VALIDATION.md row 4b-02-03: nor/abn partition non-empty for both subsets
    # ==================================================================
    def test_nor_abn_partition_nonempty(synthetic_i3d_features):
        """nor_loader yields only label=0 batches; abn_loader yields only label=1 batches."""
        cfg = _build_cfg(synthetic_i3d_features, batch_size=1, T=32)
        (nor_loader, abn_loader), _ = build_dataloaders_i3d(cfg)

        nor_batch = next(iter(nor_loader))
        assert (nor_batch["label"] == 0.0).all(), (
            f"nor_loader yielded non-zero labels: {nor_batch['label']}"
        )

        abn_batch = next(iter(abn_loader))
        assert (abn_batch["label"] == 1.0).all(), (
            f"abn_loader yielded non-one labels: {abn_batch['label']}"
        )
    ```
  </action>
  <verify>
    <automated>C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_loaders_i3d.py -x --tb=short</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_loaders_i3d.py` exists (verify: `test -f tests/test_loaders_i3d.py`)
    - `grep -c "^def test_" tests/test_loaders_i3d.py` outputs `5`
    - Required test function names present:
      - `test_build_dataloaders_i3d_shape` (VALIDATION row 4b-02-01)
      - `test_collate_flattens_crops` (VALIDATION row 4b-02-02)
      - `test_nor_abn_partition_nonempty` (VALIDATION row 4b-02-03)
      - `test_collate_label_replication` (Pitfall 4 guard)
      - `test_collate_mask_all_ones` (Pitfall 1 guard)
    - All 5 tests pass: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_loaders_i3d.py -x --tb=short` exit 0
    - `grep -q "synthetic_i3d_features" tests/test_loaders_i3d.py` (fixture usage)
    - `grep -q "from src.data.loaders import" tests/test_loaders_i3d.py`
    - `grep -q "build_dataloaders_i3d" tests/test_loaders_i3d.py`
    - `grep -q "collate_i3d_train" tests/test_loaders_i3d.py`
  </acceptance_criteria>
  <done>5 unit tests pass. Fixture path integration works. Label replication and mask-all-ones Pitfall guards verified.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Filesystem path → I3DFeatureDataset | `paths.i3d_features` from config is concatenated with `/RGB` to form feature directory path; config file is version-controlled (not user-input at runtime) |
| Config dict → DataLoader | `cfg["data"]["batch_size"]`, `num_workers`, `pin_memory`, `T` consumed as-is; type-checked by DataLoader |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4b-04 | Input Validation | `cfg["data"]["batch_size"]` | accept | Config is YAML-loaded from version-controlled file; not user-supplied. No validation needed. If batch_size=0 or negative, PyTorch DataLoader raises cleanly. |
| T-4b-05 | Tampering | `_label_A` suffix check for normal partitioning | mitigate | `.endswith("_label_A")` is case-sensitive exact match; verified in RESEARCH.md Pitfall 6 against all 500 abnormal test videos (no false positives). If future Wu convention adds a `_label_A1` code, the endswith check would still be correct (A1 != A). |
| T-4b-06 | Information Disclosure | Train/val/test leakage via shared dataset | mitigate | `build_dataloaders_i3d` constructs separate `I3DFeatureDataset` instances per split (mode="train"/"val"); test split is consumed ONLY by `src/eval/test_loader.py` via `build_test_dataset`, preserving C3 test-set isolation |
| T-4b-07 | Denial of Service | Empty partition causing silent failure | mitigate | `assert len(nor_idx) > 0`, `assert len(abn_idx) > 0`, `assert len(val_abn) > 0` — failures raise AssertionError at loader construction time (loud fail) instead of producing NaN loss every epoch (Open Question #1) |

**Phase 4b Plan 02 security posture:** inherits Phase 4 posture. The parallel-functions dispatch (D-04) preserves C3 module boundaries — `build_dataloaders_i3d` lives in `src/data/loaders.py` next to `build_dataloaders`, does NOT import from `src/eval/`.
</threat_model>

<verification>
## Per-Task Automated Verify
- Task 1: `python -c "from src.data.loaders import build_dataloaders_i3d, collate_i3d_train, build_dataloaders"` exit 0
- Task 2: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_loaders_i3d.py -x --tb=short` exit 0 with 5/5 passing

## Plan-Level Gate
- All existing tests still pass: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x --ignore=tests/test_ctrgcn_smoke.py --tb=short` exits 0 (no regression to UCF/XD fusion path)
- `build_dataloaders` signature UNCHANGED (verify: `grep -E "^def build_dataloaders\(" src/data/loaders.py` shows the original line, no new kwargs)
- New public surface exposed: `collate_i3d_train`, `build_dataloaders_i3d` both at module scope, both importable

## Decision Traceability
- D-04 (parallel functions, not polymorphic) — build_dataloaders_i3d added alongside, not replacing build_dataloaders
- D-05 (crop-as-sample collate) — `collate_i3d_train` flattens [B, 5, T, 1024] -> [B*5, T, 1024] via `repeat_interleave(5)` on labels
- D-06 (_label_A suffix partitioning) — nor_idx / abn_idx use `.endswith("_label_A")` directly (no dependence on I3DFeatureDataset.labels attribute which doesn't exist)
- Pitfall 1 (missing mask for xd_i3d) — collate synthesizes `mask = torch.ones(B*5, T)`
- Pitfall 3 (5-crop vs k_topk ratio) — `bs = data_cfg["batch_size"]` reads from config (3 per rtfm_i3d.yaml); NOT hardcoded 16
- Pitfall 4 (5-crop label replication drift) — `.repeat_interleave(5)` (NOT `.repeat(5)`) + dedicated unit test
- Pitfall 7 (Windows spawn persistent_workers) — `collate_i3d_train` at module scope (not inside build_dataloaders_i3d)
- Open Question #1 (val abnormal coverage) — hard assertion `len(val_abn) > 0`
- Open Question #2 (xd_val.txt explicit path) — hardcoded `xd_train.txt` / `xd_val.txt` (not pattern `{dataset}_val.txt`)
</verification>

<success_criteria>
- `src/data/loaders.py` contains `def build_dataloaders_i3d` + `def collate_i3d_train` at module scope
- `src/data/loaders.py::build_dataloaders` (existing) signature and body UNCHANGED
- `tests/test_loaders_i3d.py` has 5 tests, all passing
- `build_dataloaders_i3d` honors `cfg.data.batch_size=3` and yields batches with first dim = 15
- `collate_i3d_train` emits `mask` (all ones), labels replicated 5x consecutively, video_id list of length B*5
- Val abnormal partition assertion fires loudly if the split filter collapses to empty
- No regression: full test suite green
</success_criteria>

<output>
After completion, create `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-02-SUMMARY.md` documenting:
- Commit SHAs for Task 1 + Task 2
- Line counts added to `src/data/loaders.py` (expect ~60-80 new LOC)
- Test results: `pytest tests/test_loaders_i3d.py -v` output tail with `5 passed`
- Sanity: existing test suite still green (no regressions)
- Any deviations from plan (Rule 1/2/3/4) with remediation
</output>
</content>
</invoke>