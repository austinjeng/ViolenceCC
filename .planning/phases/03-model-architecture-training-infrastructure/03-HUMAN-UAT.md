---
status: resolved
phase: 03-model-architecture-training-infrastructure
source: [03-VERIFICATION.md]
started: 2026-04-14T18:35:00Z
updated: 2026-04-15T04:15:00Z
---

## Current Test

[all tests complete]

## Tests

### 1. Real UCF-Crime 3-epoch smoke run (SC1 clause "on UCF-Crime cached features")
expected: No crash; `results/ucf_skeleton_only_42_<ts>/` contains `best_model.pth`, `last_model.pth`, `train_log.csv`, `config_snapshot.json`; CSV has 3 rows with header `epoch,train_loss,val_loss,lr`; both `.pth` files non-empty; `torch.load(...)` succeeds.
result: passed (run `results/ucf_skeleton_only_42_20260415-041040/`). All 4 artifacts present; CSV rows [epoch,train_loss,val_loss,lr]: (0,1.018285,1.009353,1.00e-6), (1,1.014272,1.002269,2.08e-5), (2,1.009694,0.987334,4.06e-5). best_model.pth loads via torch.load(weights_only=True) — 8 tensors.

debug_session: first attempt produced NaN loss (run `ucf_skeleton_only_42_20260415-034926/`) due to D-10 zero-pad+mask being NaN-unsafe under D-01 top-k=3 when N<k (41.2% of UCF videos). Root-caused via snippet-count distribution analysis + MIL loss -inf propagation trace. Fixed by commit c42d38c — `_sample_or_pad` N<T branch now samples T indices with replacement (RTFM/VadCLIP reference pattern), mask always all-ones, top-k always well-defined. Revises D-10 design decision; 90/90 regression tests green.

### 2. WR-01 fix (LR off-by-one in CSV/wandb logs)
expected: After swapping `lr = optimizer.param_groups[0]["lr"]` to execute before `scheduler.step()` in `src/train.py:174-176`, logged LR at epoch 0 should be the warmup start LR (~1e-6), not the epoch-1 value. Training correctness unaffected; this is an instrumentation fix so thesis LR curves are accurate before Phase 4 produces final result tables.
result: passed (commit 2656992). Micro-smoke with warmup_epochs=3, lr=1e-3 confirms epoch-0 logs lr=1e-5 (warmup start) instead of 3.4e-4. Real UCF smoke CSV row 0 shows lr=1.00e-6 (config warmup-start LR), confirming the fix composes correctly with the full training loop.

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

### Non-blocking (nit) — wandb interactive prompt despite WANDB_MODE=disabled
The env var `WANDB_MODE=disabled` set via `$env:WANDB_MODE="disabled"` suppresses data upload but the wandb library still prompts for the account wizard on first run per shell. `src/utils/wandb_logger.py::WandbLogger.__init__` initializes wandb before reading WANDB_MODE. Does not affect Phase 3 correctness. Defer to Phase 4 pre-flight cleanup.
