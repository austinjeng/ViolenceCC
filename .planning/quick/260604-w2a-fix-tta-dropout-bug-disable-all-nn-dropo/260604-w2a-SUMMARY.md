---
quick_id: 260604-w2a
slug: fix-tta-dropout-bug-disable-all-nn-dropo
date: 2026-06-04
type: quick
status: complete
---

# Quick Task 260604-w2a: Fix TTA dropout-in-train-mode bug Summary

Disabled ALL `nn.Dropout` modules in `configure_model` (previously only the top-level
`GatedFusion.dropout` was disabled, leaving MILHead's two `nn.Dropout` layers in train
mode) and seeded `run_tta_evaluation`, making source_only/TENT/SAR forwards deterministic.
Code-only fix: no paper edit, no grid re-run, no canonical-artifact change.

## What changed

### Task 1 — `src/tta/tent.py`
- Module docstring bullet 4: `"Dropout explicitly set to eval after model.train() (Pitfall 6)"`
  → `"ALL Dropout modules set to eval after model.train() (Pitfall 6)"`.
- `configure_model` body: replaced
  ```python
  # Pitfall 6: disable dropout during TTA
  if hasattr(model, "dropout"):
      model.dropout.eval()
  ```
  with a loop disabling every `nn.Dropout`:
  ```python
  # Pitfall 6: disable ALL dropout during TTA. model.train() (needed for LN
  # gradient flow) turns every dropout on; disabling only the top-level
  # GatedFusion.dropout left MILHead's two nn.Dropout layers (head.mlp.2,
  # head.mlp.5) in train mode, making every TTA score stochastic. Loop over
  # all modules so no dropout is missed.
  for m in model.modules():
      if isinstance(m, nn.Dropout):
          m.eval()
  ```

### Task 2 — `src/tta/evaluate_tta.py`
- Inserted at the top of the `run_tta_evaluation` body, after the `feature_root is None`
  block (line 258) and before `device = ...`:
  ```python
  # Determinism (D-12): with dropout disabled in configure_model the forward is
  # already deterministic; pin the RNG anyway so any residual stochasticity is
  # reproducible across re-runs.
  torch.manual_seed(0)
  np.random.seed(0)
  ```
  (`np` already imported at line 35; `torch` already imported.)

### Task 3 — `tests/test_tent.py`
- Added `import torch.nn as nn` at the top.
- Added `test_configure_model_disables_all_dropout`: after `configure_model`, the list of
  `nn.Dropout` modules still in `.training` mode must be empty (model itself stays in train
  mode for LN gradients).
- Added `test_tta_forward_is_deterministic`: two `model(skel=..., clip=...)` forwards on the
  same input after `configure_model` are bit-identical (`max(|pass1 - pass2|) == 0.0`). Uses
  a tiny `GatedFusion(clip_dim=1024)` on CPU.

## Verification

- `python -m pytest tests/test_tent.py -q` → **10 passed** (8 existing + 2 new), 0 failed.
- One-liner verify (PLAN Task 1): train-mode dropouts after `configure_model` → `[]` (EMPTY).
- `grep isinstance(m, nn.Dropout) src/tta/tent.py` → line 56 (inside configure_model); old
  `hasattr(model, "dropout")` line removed.
- `grep torch.manual_seed(0) src/tta/evaluate_tta.py` → line 258 (inside run_tta_evaluation).

## Deviations from Plan

None — plan executed exactly as written.

## Out of scope (not done, as specified)
- Re-running the TTA grid / regenerating `results/tta` or `results/tta_backbone`.
- Any edit to `paper/main.tex` or canonical artifacts.
- The symmetric TTA config protocol.
