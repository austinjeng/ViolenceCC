---
phase: 04b
plan: 03
type: execute
wave: 2
depends_on: [04b-02]
files_modified:
  - src/train.py
  - tests/test_train_i3d.py
autonomous: true
requirements:
  - EVAL-01
tags: [training, mil-loss, dispatch, i3d]
user_setup: []

must_haves:
  truths:
    - "train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, device, train_cfg) -> float runs one epoch consuming `[B*5, T, 1024]` i3d batches and returns the mean MIL ranking loss"
    - "validate_i3d(model, val_loader, device, train_cfg) -> float splits the val batch into paired halves by label and returns mean MIL loss (or float('inf') if no paired samples)"
    - "main() dispatches to the i3d path when cfg['dataset'] == 'xd_i3d' — loaders, train function, val function all selected via one branch"
    - "D-12 bag-size audit prints `[i3d_audit] n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024) mask_shape=(30, 32)` on first step of first 3 epochs (Pitfall 1 + Pitfall 4 diagnostic)"
    - "train_one_epoch_i3d synthesizes mask=torch.ones(i3d.shape[0], i3d.shape[1]) before passing to mil_ranking_loss (even if batch already has mask) — defensive double-ones so the fallback path is explicit"
    - "Existing train_one_epoch / validate (UCF fusion path) signatures and bodies UNCHANGED"
  artifacts:
    - path: "src/train.py"
      provides: "ADDED train_one_epoch_i3d + validate_i3d + _split_labels_i3d helper + main() dispatch branch (existing functions UNCHANGED)"
      adds: ["def train_one_epoch_i3d", "def validate_i3d", "def _split_labels_i3d"]
    - path: "tests/test_train_i3d.py"
      provides: "Unit tests for train_one_epoch_i3d + validate_i3d + main() dispatch routing"
      min_lines: 120
  key_links:
    - from: "src/train.py"
      to: "src/data/loaders.py"
      via: "from src.data.loaders import build_dataloaders, build_dataloaders_i3d"
      pattern: "from src\\.data\\.loaders import .*build_dataloaders_i3d"
    - from: "src/train.py"
      to: "src/losses/mil_loss.py"
      via: "mil_ranking_loss(scores, mask, n_normal=, k=, margin=, lam_sparse=, lam_smooth=)"
      pattern: "mil_ranking_loss"
    - from: "tests/test_train_i3d.py"
      to: "tests/conftest.py"
      via: "synthetic_i3d_features fixture"
      pattern: "synthetic_i3d_features"
---

<objective>
Add `train_one_epoch_i3d`, `validate_i3d`, `_split_labels_i3d`, and a single dispatch branch in `main()` to `src/train.py`. The dispatch branch routes `cfg['dataset'] == 'xd_i3d'` through the new i3d-only training path, consuming `build_dataloaders_i3d` output (from Plan 04b-02). The existing fusion path (UCF Gated Fusion, Late Fusion, etc.) is untouched.

Purpose: This is the actual training loop that Phase 4 Plan 04-03 claimed to implement but did not (Rule 4 architectural gap in 04-06-UAT.md). Without this dispatch, `src/train.py::main()` unconditionally calls `build_dataloaders(cfg)` which tries to read `paths.skeleton_features` — a key that `rtfm_i3d.yaml` intentionally omits, raising `KeyError` at loader construction time. Plan 04b-03 closes that gap with a minimal parallel-functions branch. Includes the D-12 bag-size audit log (first 3 epochs, first step only) to diagnose 5-crop expansion bugs before the full RTFM gate runs.

Output: `src/train.py` with ~80 new LOC added (3 new functions + dispatch branch in main()); `tests/test_train_i3d.py` with 3 unit tests covering signature, loss-finite, and dispatch routing.
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

<!-- Prior plan artifacts (from Wave 1): -->
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-01-PLAN.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-02-PLAN.md

<!-- CRITICAL template (mirror its structure): -->
@src/train.py

<!-- Dependent downstream (read-only, already compatible): -->
@src/losses/mil_loss.py
@src/models/rtfm_i3d.py

<!-- Reference integration test (pattern for main() dispatch test): -->
@tests/test_train_integration.py

<interfaces>
<!-- Contract executor must implement. -->

**Existing train_one_epoch signature (src/train.py, DO NOT MODIFY):**
```python
def train_one_epoch(model, nor_loader, abn_loader, optimizer, device, train_cfg) -> float:
    # Concatenates nor_batch["skel"]/["clip"]/["mask"] with abn_batch[...]
    # Calls model(skel=, clip=, mask=)
    # Returns mean MIL ranking loss
```

**Existing validate signature (src/train.py, DO NOT MODIFY):**
```python
def validate(model, val_loader, device, train_cfg) -> float:
    # Uses _split_labels helper to pair normal/abnormal val samples
    # Returns float('inf') if no paired samples available
```

**Existing _split_labels helper (src/train.py, DO NOT MODIFY):**
```python
def _split_labels(batch):
    # Splits mixed-label val batch into paired halves
    # Returns (skel, clip, mask, n_normal) or None if only one class
```

**New functions to add:**
```python
def _split_labels_i3d(batch) -> Optional[Tuple[Tensor, Tensor, int]]:
    # Splits i3d-only mixed-label val batch into paired halves
    # Returns (i3d, mask, n_normal) or None

def train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, device, train_cfg, epoch: int = 0) -> float:
    # Consumes nor_batch["i3d"], abn_batch["i3d"] (NOT skel/clip)
    # Synthesizes mask=torch.ones(...) before calling mil_ranking_loss
    # First step of first 3 epochs prints [i3d_audit] diagnostic line

def validate_i3d(model, val_loader, device, train_cfg) -> float:
    # Parallel to validate() but uses _split_labels_i3d
```

**main() dispatch contract (modify 1 branch in src/train.py::main()):**
```python
# After: cfg = apply_cli_overrides(cfg, args); set_deterministic(...)
# Before: the existing for-loop over epochs
# Add ONE if/else branch that picks loader+train_fn+val_fn based on cfg['dataset']
if cfg.get("dataset") == "xd_i3d":
    (nor_loader, abn_loader), val_loader = build_dataloaders_i3d(cfg)
    train_fn = train_one_epoch_i3d
    val_fn = validate_i3d
else:
    (nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
    train_fn = train_one_epoch
    val_fn = validate
# Then use train_fn / val_fn in the existing for-loop (replacing direct calls)
```

**RTFMI3D.forward contract (src/models/rtfm_i3d.py):**
```python
# model(skel=None, clip=None, i3d=i3d_tensor, mask=mask_tensor) -> scores: [B, T]
```

**mil_ranking_loss contract (src/losses/mil_loss.py:52-84):**
```python
def mil_ranking_loss(
    scores: Tensor,           # [2N, T]
    mask: Tensor,             # [2N, T] — REQUIRED
    n_normal: int,            # first n_normal rows are normal bags
    k: int,
    margin: float,
    lam_sparse: float,
    lam_smooth: float,
) -> Tensor
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add train_one_epoch_i3d + validate_i3d + _split_labels_i3d + main() dispatch branch to src/train.py</name>
  <files>src/train.py</files>
  <read_first>
    - src/train.py (full file — identify the existing functions: train_one_epoch at lines 85-113, validate at lines 116-138, _split_labels at lines 65-82, main() at lines 141-207)
    - src/losses/mil_loss.py (signature at lines 52-84 — understand mask contract)
    - src/models/rtfm_i3d.py (forward at line 51 — understand i3d+mask kwargs)
    - src/data/loaders.py (after Plan 04b-02 — verify `build_dataloaders_i3d` is importable)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "Example 2: src/train.py additions" (lines 917-990) for the verified draft of train_one_epoch_i3d + validate_i3d
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "src/train.py::train_one_epoch_i3d" (lines 370-415) + section "src/train.py::validate_i3d" (lines 418-472) + section "src/train.py::main() dispatch branch" (lines 475-521)
  </read_first>
  <behavior>
    - Test 1: `train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, "cpu", {"k_topk": 3, "margin": 1.0, "lam_sparse": 8e-3, "lam_smooth": 8e-4})` on synthetic fixture runs one step and returns a finite float
    - Test 2: `validate_i3d` signature parameters match `validate` parameters (both are `(model, val_loader, device, train_cfg)`) verified via `inspect.signature`
    - Test 3: `main([--config cfg_path, --epochs 1])` with `cfg.dataset == 'xd_i3d'` pointing at synthetic fixture completes without error, produces `best_model.pth` in the run_dir
    - Test 4: When `epoch < 3` and `step == 0`, stderr contains `[i3d_audit]` log line with `n_normal=`, `n_abnormal=`, `i3d_shape=`, `mask_shape=` (verified via `capsys` or `capfd` fixture)
  </behavior>
  <action>
    Open `src/train.py` and make the following additions. CRITICAL:
    - Do NOT modify `train_one_epoch`, `validate`, `_split_labels` — those are the UCF fusion path
    - Do NOT remove any existing imports
    - The `main()` dispatch is a minimal 6-line branch, not a rewrite

    Step 1 — Add import at the top of the file (after the existing `from src.data.loaders import build_dataloaders` line):
    ```python
    from src.data.loaders import build_dataloaders_i3d
    ```
    (If the existing import is a multi-name import, add the new name; e.g. `from src.data.loaders import build_dataloaders, build_dataloaders_i3d`.)

    Step 2 — Add `_split_labels_i3d` helper IMMEDIATELY BEFORE `_split_labels` (around line 65, placement doesn't matter functionally — any module scope is fine, but grouping near the existing helper is cleaner):
    ```python
    def _split_labels_i3d(batch):
        """Split an i3d val batch (labels 0 normal, 1 abnormal) into paired halves.

        I3D-only parallel to _split_labels (no skel/clip). Returns (i3d, mask, n_normal)
        where i3d is the paired [2n, T, 1024] tensor and mask is synthesized as all-ones.

        Returns None if the batch has only one class (no valid pair for MIL ranking).
        """
        labels = batch["label"]
        nor_idx = (labels == 0).nonzero(as_tuple=True)[0]
        abn_idx = (labels == 1).nonzero(as_tuple=True)[0]
        if len(nor_idx) == 0 or len(abn_idx) == 0:
            return None
        n = min(len(nor_idx), len(abn_idx))
        nor_idx = nor_idx[:n]
        abn_idx = abn_idx[:n]
        i3d = torch.cat([batch["i3d"][nor_idx], batch["i3d"][abn_idx]], dim=0)
        # Mask: all ones (I3D has no padding; Pitfall 1 guard)
        mask = torch.ones(i3d.shape[0], i3d.shape[1], dtype=torch.float32)
        return i3d, mask, n
    ```

    Step 3 — Add `train_one_epoch_i3d` IMMEDIATELY AFTER the existing `train_one_epoch` function:
    ```python
    def train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, device, train_cfg, epoch: int = 0):
        """Train one epoch on xd_i3d dispatch path (D-04).

        Parallel to train_one_epoch but consumes i3d-only batches from build_dataloaders_i3d.
        Synthesizes mask=torch.ones(...) defensively before mil_ranking_loss (Pitfall 1).
        First step of first 3 epochs prints the D-12 bag-size audit diagnostic to stderr.

        Args:
            model: RTFMI3D with forward(i3d=, mask=) -> [B, T] scores
            nor_loader: DataLoader yielding {"i3d", "label", "mask", "video_id"} with label==0
            abn_loader: same schema with label==1
            optimizer: AdamW (or any torch optimizer)
            device: "cuda" or "cpu"
            train_cfg: dict with keys k_topk, margin, lam_sparse, lam_smooth
            epoch: current epoch index (used for D-12 audit gating)

        Returns:
            Mean MIL ranking loss (float) across steps.
        """
        import sys

        model.train()
        losses = []
        steps_per_epoch = min(len(nor_loader), len(abn_loader))
        nor_iter = iter(nor_loader)
        abn_iter = iter(abn_loader)
        for step in range(steps_per_epoch):
            nor_batch = next(nor_iter)
            abn_batch = next(abn_iter)
            i3d = torch.cat([nor_batch["i3d"], abn_batch["i3d"]], dim=0).to(device)
            # Defensive mask synthesis (Pitfall 1): I3D has no padding so always all-ones.
            # If the collate already emits mask, prefer that for forward-compat; otherwise
            # synthesize. We always call torch.ones here because shape is known from i3d.
            mask = torch.ones(i3d.shape[0], i3d.shape[1], dtype=torch.float32, device=device)
            n_normal = nor_batch["i3d"].shape[0]

            # D-12 bag-size audit: first step of first 3 epochs
            if epoch < 3 and step == 0:
                print(
                    f"[i3d_audit] epoch={epoch} step={step} "
                    f"n_normal={n_normal} n_abnormal={abn_batch['i3d'].shape[0]} "
                    f"i3d_shape={tuple(i3d.shape)} mask_shape={tuple(mask.shape)}",
                    file=sys.stderr, flush=True,
                )
                assert n_normal == abn_batch["i3d"].shape[0], (
                    f"nor/abn batch-size mismatch: {n_normal} vs {abn_batch['i3d'].shape[0]}"
                )
                assert i3d.shape[0] == 2 * n_normal, (
                    f"concat shape bug: {i3d.shape[0]} != 2 * {n_normal}"
                )

            scores = model(i3d=i3d, mask=mask)     # [2*B*5, T]
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

    Step 4 — Add `validate_i3d` IMMEDIATELY AFTER the existing `validate` function:
    ```python
    @torch.no_grad()
    def validate_i3d(model, val_loader, device, train_cfg) -> float:
        """Compute val MIL ranking loss on xd_i3d path (D-04 parallel to validate).

        Iterates val_loader, pairs each batch via _split_labels_i3d, computes MIL loss,
        returns mean across batches. Returns float('inf') if no paired samples found
        (which would break early stopping — build_dataloaders_i3d asserts val_abn > 0
        to make this loud at loader-construction time).
        """
        model.eval()
        losses = []
        for batch in val_loader:
            pair = _split_labels_i3d(batch)
            if pair is None:
                continue
            i3d, mask, n_normal = pair
            i3d = i3d.to(device)
            mask = mask.to(device)
            scores = model(i3d=i3d, mask=mask)
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

    Step 5 — Modify `main()` to add the dispatch branch. Find the existing line 165:
    ```python
    (nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
    ```
    Replace it with a 6-line dispatch AND also update the per-epoch calls at lines 175-177. The final structure:
    ```python
    # ---- Dispatch on cfg['dataset'] (D-04) ----
    if cfg.get("dataset") == "xd_i3d":
        (nor_loader, abn_loader), val_loader = build_dataloaders_i3d(cfg)
        _train_fn = train_one_epoch_i3d
        _val_fn = validate_i3d
    else:
        (nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
        _train_fn = train_one_epoch
        _val_fn = validate
    # ---- End dispatch ----
    ```

    Then inside the existing `for epoch in range(...)` loop, replace:
    ```python
    train_loss = train_one_epoch(
        model, nor_loader, abn_loader, optimizer, device, cfg["train"])
    val_loss = validate(model, val_loader, device, cfg["train"])
    ```
    with:
    ```python
    # D-12 audit: pass epoch to i3d train fn; non-i3d paths ignore the kwarg safely
    if cfg.get("dataset") == "xd_i3d":
        train_loss = _train_fn(
            model, nor_loader, abn_loader, optimizer, device, cfg["train"], epoch=epoch)
    else:
        train_loss = _train_fn(
            model, nor_loader, abn_loader, optimizer, device, cfg["train"])
    val_loss = _val_fn(model, val_loader, device, cfg["train"])
    ```

    Do NOT change anything else in main() — scheduler, logging, early stopping, checkpoint save are all unchanged.
  </action>
  <verify>
    <automated>python -c "from src.train import train_one_epoch_i3d, validate_i3d, _split_labels_i3d, train_one_epoch, validate, _split_labels; import inspect; s1 = inspect.signature(validate); s2 = inspect.signature(validate_i3d); assert list(s1.parameters.keys()) == list(s2.parameters.keys()); print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "def train_one_epoch_i3d" src/train.py` outputs `1`
    - `grep -c "def validate_i3d" src/train.py` outputs `1`
    - `grep -c "def _split_labels_i3d" src/train.py` outputs `1`
    - `grep -qE "^def train_one_epoch\(" src/train.py` exit 0 (existing UCF path preserved)
    - `grep -qE "^def validate\(" src/train.py` exit 0 (existing UCF path preserved)
    - `grep -q "from src.data.loaders import" src/train.py` and `build_dataloaders_i3d` is among the imports (either multi-name import or separate import line)
    - `main()` dispatch branch present: `grep -q 'cfg.get("dataset") == "xd_i3d"' src/train.py` exit 0 OR `grep -q "cfg\['dataset'\] == 'xd_i3d'" src/train.py` (either quote style)
    - `[i3d_audit]` diagnostic log string present in `train_one_epoch_i3d`: `grep -q "\[i3d_audit\]" src/train.py` exit 0
    - Mask synthesis present in `train_one_epoch_i3d`: `grep -q "torch.ones" src/train.py` shows at least 2 occurrences (one in `_split_labels_i3d`, one in `train_one_epoch_i3d`)
    - `mil_ranking_loss` called from BOTH old and new functions — `grep -c "mil_ranking_loss(" src/train.py` outputs `>=4` (old train+validate + new i3d variants, 2 each)
    - Module imports cleanly: `python -c "from src.train import train_one_epoch_i3d, validate_i3d"` exit 0
    - Signature parity: `validate_i3d` and `validate` share parameter names (validated via `inspect.signature` in the verify command above)
    - No regression to existing tests: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x --ignore=tests/test_ctrgcn_smoke.py --tb=short` exit 0 (UCF fusion train path still works)
  </acceptance_criteria>
  <done>Three new functions added + main() dispatch wired. Existing functions untouched. Imports clean. `mil_ranking_loss` called from both paths.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create tests/test_train_i3d.py with 3 tests covering loss-finite, signature-match, and main() dispatch</name>
  <files>tests/test_train_i3d.py</files>
  <read_first>
    - src/train.py (after Task 1 — verify all new functions importable)
    - tests/test_train_integration.py (full file — the `_build_smoke_dataset` and `_latest_run` helpers are templates for the main() dispatch test)
    - tests/conftest.py (verify `synthetic_i3d_features` fixture is accessible)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md section "tests/test_train_i3d.py" (lines 805-887) for test case templates + config builder
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-VALIDATION.md rows 4b-03-01, 4b-03-02, 4b-03-03 for exact test function names
  </read_first>
  <behavior>
    - Test 1 (`test_train_one_step_loss_finite`): `train_one_epoch_i3d` on synthetic fixture completes 1 step and returns a finite float (not NaN, not inf)
    - Test 2 (`test_validate_i3d_signature`): `inspect.signature(validate_i3d).parameters` equals `inspect.signature(validate).parameters` (same parameter names in same order)
    - Test 3 (`test_main_dispatch_xd_i3d`): `main(['--config', cfg_path, '--epochs', '1'])` with `cfg.dataset == 'xd_i3d'` exits 0 and creates `best_model.pth` in the run dir
    - Test 4 bonus (`test_i3d_audit_log_emitted`): capture stderr via `capfd` during a 1-step `train_one_epoch_i3d` call on synthetic fixture with `epoch=0`; assert `[i3d_audit]` substring appears in captured stderr
  </behavior>
  <action>
    Create NEW file `tests/test_train_i3d.py` with the following structure:

    ```python
    """Unit tests for train_one_epoch_i3d, validate_i3d, and main() dispatch (Phase 4b Plan 03).

    Covers VALIDATION.md rows 4b-03-01 / 4b-03-02 / 4b-03-03:
      - train_one_epoch_i3d runs 1 step and returns finite loss
      - validate_i3d signature matches validate contract
      - main() dispatches to i3d path when cfg.dataset == 'xd_i3d'

    Plus D-12 diagnostic check: [i3d_audit] log line emitted on first 3 epochs.
    """
    from __future__ import annotations

    import inspect
    import json
    from pathlib import Path

    import pytest
    import torch
    import yaml

    from src.train import (
        train_one_epoch_i3d,
        validate_i3d,
        validate,
        main,
    )
    from src.data.loaders import build_dataloaders_i3d
    from src.models.registry import build_model


    # ------------------------------------------------------------------
    # Helper: build a 1-epoch xd_i3d cfg YAML pointing at the synthetic_i3d_features fixture.
    # ------------------------------------------------------------------
    def _build_smoke_xd_i3d_config(fx, tmp_path: Path) -> Path:
        """Mirror of test_train_integration.py::_build_smoke_dataset but for xd_i3d."""
        results = tmp_path / "results"
        results.mkdir(exist_ok=True)
        splits_dir = fx["train_split"].parent
        # Ensure xd_val.txt exists for build_dataloaders_i3d
        val_split = splits_dir / "xd_val.txt"
        if not val_split.exists():
            train_ids = fx["train_split"].read_text(encoding="utf-8").strip().splitlines()
            normal = next((v for v in train_ids if v.strip().endswith("_label_A")), None)
            abnorm = next((v for v in train_ids if not v.strip().endswith("_label_A")), None)
            assert normal and abnorm, "fixture missing mixed labels"
            val_split.write_text(f"{normal}\n{abnorm}\n", encoding="utf-8")

        cfg = {
            "seed": 42,
            "dataset": "xd_i3d",
            "paths": {
                "i3d_features": str(fx["rgb"].parent),
                "splits_dir": str(splits_dir),
                "results_dir": str(results),
            },
            "model": {
                "variant": "rtfm_i3d", "i3d_dim": 1024,
                "head_hidden": [128, 32], "dropout": 0.3,
            },
            "data": {"T": 32, "batch_size": 1, "num_workers": 0, "pin_memory": False},
            "train": {
                "lr": 1e-4, "weight_decay": 1e-2, "epochs": 1, "warmup_epochs": 0,
                "patience": 10, "k_topk": 3, "margin": 1.0,
                "lam_sparse": 8e-3, "lam_smooth": 8e-4,
            },
            "wandb": {"project": "violencecc", "mode": "disabled", "tags": []},
        }
        cfg_path = tmp_path / "cfg.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        return cfg_path


    def _latest_run(results_dir: Path) -> Path:
        """Mirror test_train_integration.py::_latest_run."""
        runs = [p for p in results_dir.iterdir() if p.is_dir()]
        assert runs, f"no run dirs in {results_dir}"
        return max(runs, key=lambda p: p.stat().st_mtime)


    # ==================================================================
    # VALIDATION.md row 4b-03-01: train_one_epoch_i3d loss-finite
    # ==================================================================
    def test_train_one_step_loss_finite(synthetic_i3d_features, tmp_path):
        """train_one_epoch_i3d runs 1 step on synthetic fixture; loss is finite float."""
        fx = synthetic_i3d_features
        cfg = {
            "seed": 42, "dataset": "xd_i3d",
            "paths": {
                "splits_dir": str(fx["train_split"].parent),
                "i3d_features": str(fx["rgb"].parent),
            },
            "data": {"T": 32, "batch_size": 1, "num_workers": 0, "pin_memory": False},
        }
        # Ensure xd_val.txt exists (fixture may only provide train + test)
        splits_dir = fx["train_split"].parent
        val_split = splits_dir / "xd_val.txt"
        if not val_split.exists():
            train_ids = fx["train_split"].read_text(encoding="utf-8").strip().splitlines()
            normal = next(v for v in train_ids if v.strip().endswith("_label_A"))
            abnorm = next(v for v in train_ids if not v.strip().endswith("_label_A"))
            val_split.write_text(f"{normal}\n{abnorm}\n", encoding="utf-8")

        (nor, abn), _val = build_dataloaders_i3d(cfg)

        model = build_model(variant="rtfm_i3d", i3d_dim=1024, head_hidden=[128, 32], dropout=0.3)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

        train_cfg = {
            "k_topk": 3, "margin": 1.0, "lam_sparse": 8e-3, "lam_smooth": 8e-4,
        }
        loss = train_one_epoch_i3d(model, nor, abn, optimizer, "cpu", train_cfg, epoch=0)

        assert isinstance(loss, float), f"expected float, got {type(loss)}"
        assert loss == loss, f"loss is NaN: {loss}"  # NaN check: x != x iff NaN
        assert loss < float("inf"), f"loss is inf: {loss}"
        assert loss > -float("inf"), f"loss is -inf: {loss}"


    # ==================================================================
    # VALIDATION.md row 4b-03-02: validate_i3d signature matches validate
    # ==================================================================
    def test_validate_i3d_signature():
        """validate_i3d has the same parameter signature as validate (D-04 parallel contract)."""
        sig_validate = inspect.signature(validate)
        sig_validate_i3d = inspect.signature(validate_i3d)
        assert list(sig_validate.parameters.keys()) == list(sig_validate_i3d.parameters.keys()), (
            f"validate params: {list(sig_validate.parameters.keys())}; "
            f"validate_i3d params: {list(sig_validate_i3d.parameters.keys())}"
        )
        # Both should return float
        assert sig_validate.return_annotation is float or sig_validate.return_annotation is inspect.Signature.empty
        assert sig_validate_i3d.return_annotation is float or sig_validate_i3d.return_annotation is inspect.Signature.empty


    # ==================================================================
    # VALIDATION.md row 4b-03-03: main() dispatches to xd_i3d path
    # ==================================================================
    def test_main_dispatch_xd_i3d(synthetic_i3d_features, tmp_path, capfd):
        """main() with cfg.dataset=='xd_i3d' completes 1 epoch; best_model.pth written."""
        fx = synthetic_i3d_features
        cfg_path = _build_smoke_xd_i3d_config(fx, tmp_path)

        rc = main(["--config", str(cfg_path), "--epochs", "1"])
        assert rc == 0, "main() exited non-zero"

        run = _latest_run(tmp_path / "results")
        assert (run / "best_model.pth").exists(), "best_model.pth not written"
        assert (run / "config_snapshot.json").exists(), "config_snapshot.json not written"
        assert (run / "train_log.csv").exists(), "train_log.csv not written"

        # D-12 audit check: stderr should contain [i3d_audit] line on epoch 0
        captured = capfd.readouterr()
        assert "[i3d_audit]" in captured.err or "[i3d_audit]" in captured.out, (
            f"D-12 bag-size audit line not emitted.\nSTDERR: {captured.err}\nSTDOUT: {captured.out}"
        )
    ```
  </action>
  <verify>
    <automated>C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_train_i3d.py -x --tb=short</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_train_i3d.py` exists (verify: `test -f tests/test_train_i3d.py`)
    - `grep -c "^def test_" tests/test_train_i3d.py` outputs `3` (or `4` if the bonus audit test is consolidated as a separate function)
    - Required test function names present:
      - `test_train_one_step_loss_finite` (VALIDATION row 4b-03-01)
      - `test_validate_i3d_signature` (VALIDATION row 4b-03-02)
      - `test_main_dispatch_xd_i3d` (VALIDATION row 4b-03-03)
    - All tests pass: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_train_i3d.py -x --tb=short` exit 0
    - Test file imports `main`, `train_one_epoch_i3d`, `validate_i3d`, `validate` — verify: `grep -q "from src.train import" tests/test_train_i3d.py`
    - Test file uses the `synthetic_i3d_features` fixture — verify: `grep -q "synthetic_i3d_features" tests/test_train_i3d.py`
    - `test_main_dispatch_xd_i3d` checks for `[i3d_audit]` in captured output — verify: `grep -q "\[i3d_audit\]" tests/test_train_i3d.py`
  </acceptance_criteria>
  <done>3 unit tests pass (loss-finite, signature-match, main-dispatch). [i3d_audit] D-12 diagnostic verified in the dispatch test.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Config → training loop | `cfg.dataset` string determines dispatch; any string other than `"xd_i3d"` routes to the existing fusion path. Safe — no injection surface. |
| DataLoader batch → mil_ranking_loss | Batch tensors `i3d` and `mask` are shape-validated implicitly by model forward and `mil_ranking_loss.masked_fill` usage |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4b-08 | Tampering | Accidentally polymorphic branch leaking fusion path state | mitigate | Dispatch is a single `if/else` on `cfg.get("dataset") == "xd_i3d"`; the two paths share NO state. `train_one_epoch_i3d` does not import from `src/eval/`, preserving C3 (Phase 4 D-07). Verified via per-function `grep` in acceptance criteria. |
| T-4b-09 | Information Disclosure | D-12 audit log | accept | `[i3d_audit]` line prints batch shapes and counts — no PII, no secrets. Harmless diagnostic. Log goes to stderr (not a network sink). |
| T-4b-10 | Denial of Service | Silent NaN loss propagation | mitigate | `mil_ranking_loss` requires `mask` arg (enforced by function signature). Mask synthesis in `train_one_epoch_i3d` + `_split_labels_i3d` defensively uses `torch.ones(...)`. D-12 shape assertions raise AssertionError on first audit step if shape contract is violated, halting training loudly. |

**Phase 4b Plan 03 security posture:** inherits Phase 4 + Plan 04b-02 posture. The dispatch branch is minimal and does not widen attack surface.
</threat_model>

<verification>
## Per-Task Automated Verify
- Task 1: `python -c "from src.train import train_one_epoch_i3d, validate_i3d, _split_labels_i3d, train_one_epoch, validate; import inspect; s1 = inspect.signature(validate); s2 = inspect.signature(validate_i3d); assert list(s1.parameters.keys()) == list(s2.parameters.keys()); print('OK')"` exit 0
- Task 2: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_train_i3d.py -x --tb=short` exit 0 with 3/3 passing

## Plan-Level Gate
- Full test suite green: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x --ignore=tests/test_ctrgcn_smoke.py --tb=short` exits 0
- Combined Phase 4b test subset green: `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_xd_annotations.py tests/test_loaders_i3d.py tests/test_train_i3d.py -x --tb=short` exits 0
- `[i3d_audit]` log line emitted on epoch 0, step 0 (verified via test_main_dispatch_xd_i3d capfd capture)

## Decision Traceability
- D-04 (parallel functions + branch once in main()) — dispatch branch selects `_train_fn` + `_val_fn` at loader-construction time; reused in per-epoch loop
- D-06 (MIL bag labels from `_label_A` suffix) — inherited from Plan 04b-02 build_dataloaders_i3d
- D-12 diagnostic #3 (bag-size audit) — `[i3d_audit]` line printed on first step of first 3 epochs
- Pitfall 1 (missing mask for xd_i3d) — `mask = torch.ones(...)` synthesized in both train_one_epoch_i3d and _split_labels_i3d
- Pitfall 4 (5-crop bag-size audit) — asserts `n_normal == abn_batch.shape[0]` and `i3d.shape[0] == 2 * n_normal` on first audit step
- Pitfall 5 prevention (clean state): N/A here (results dir cleanup is Plan 04b-05)
</verification>

<success_criteria>
- `src/train.py` contains 3 new functions (`train_one_epoch_i3d`, `validate_i3d`, `_split_labels_i3d`) + dispatch branch in `main()`
- Existing `train_one_epoch`, `validate`, `_split_labels` bodies UNCHANGED
- `tests/test_train_i3d.py` has 3 tests, all passing
- Full suite: no regressions (UCF fusion path still works)
- `[i3d_audit]` diagnostic line emitted during synthetic 1-epoch run (D-12 Check 3 precursor)
- `cfg.dataset == 'xd_i3d'` correctly routes through new loader + train + val functions
- `build_dataloaders_i3d` is imported AND called in main()
</success_criteria>

<output>
After completion, create `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-03-SUMMARY.md` documenting:
- Commit SHAs for Task 1 + Task 2
- Line counts added to `src/train.py` (expect ~80-100 new LOC)
- Test results for test_train_i3d.py with `3 passed`
- Confirmation of no regressions (`pytest tests/ -x` green)
- Sample `[i3d_audit]` log line captured during test run
- Any deviations from plan (Rule 1/2/3/4) with remediation
</output>
</content>
</invoke>