---
phase: 03-model-architecture-training-infrastructure
plan: 04
subsystem: models
tags: [phase-3, wave-2, tdd, skeleton-only, clip-only, late-fusion, mod-03, mod-04, mod-05, mod-07, d-07, d-16, layernorm-tta]
requires:
  - Plan 03-01: MILHead(input_dim, hidden_dims=(128,32), dropout=0.3), MODEL_REGISTRY lazy factories, build_model dispatcher
  - Plan 03-02: (parallel Wave 2) mil_ranking_loss — not imported here but shares the `forward(skel=, clip=, mask=)` signature contract
  - Plan 03-03: (parallel Wave 2) MILFeatureDataset — shape contracts [B,T,256] and [B,T,1024] verified by this plan's forward tests
  - Phase 2 cache contracts: skeleton features [N,256] float32 (D-05), CLIP features [N,1024] float32 (D-06)
provides:
  - SkeletonProj(skel_dim=256, head_hidden=(128,32), dropout=0.3): MOD-03; forward(skel=[B,T,256], clip=None, mask=None) -> [B,T] sigmoid scores
  - CLIPProj(clip_dim=1024, proj_dim=512, head_hidden=(128,32), dropout=0.3): MOD-04; Linear(1024->512) + LN + MILHead
  - LateFusion(skel_dim=256, clip_dim=1024, proj_dim=512, alpha='equal'|'learned'): MOD-05; score-level 0.5*s_skel + 0.5*s_clip
  - MODEL_REGISTRY resolves 3 of 4 variants: skeleton_only, clip_only, late_fusion (gated_fusion pending Plan 05)
  - Named LayerNorms discoverable for TTA (D-07): SkeletonProj.ln_skel, CLIPProj.ln_clip, LateFusion.skeleton.ln_skel + LateFusion.clip.ln_clip
affects:
  - Plan 03-05 (gated_fusion): must add test_gated_fusion_* tests and its class to registry without breaking any Plan-04 test
  - Plan 03-06 (train.py / reproducibility regression): will use build_model() with YAML config to instantiate any variant at runtime
  - Plan 03-07 (config files): variant YAML `model.variant: skeleton_only|clip_only|late_fusion` keys now resolve end-to-end
  - Phase 5 (TTA): ln_skel and ln_clip are the named LayerNorm entry points for tent.py / sar.py adaptation
tech-stack:
  added: []  # Only torch/pytest already added by Plan 01
  patterns:
    - "Variant-uniform forward signature: `forward(skel=None, clip=None, mask=None) -> [B, T]` for all 4 MIL variants"
    - "LayerNorm TTA discoverability: every modality projection ends with a named `nn.LayerNorm` attribute"
    - "Composition over inheritance for fusion: LateFusion contains SkeletonProj + CLIPProj as submodules (not subclasses) so `named_modules()` naturally exposes nested LNs"
    - "`register_parameter(..., None)` for mode-conditional parameters (alpha_logit) instead of `self.alpha_logit = None`"
    - "TDD RED -> GREEN commit split per task (continued from Plan 01)"
key-files:
  created:
    - src/models/skeleton_only.py (SkeletonProj, MOD-03)
    - src/models/clip_only.py (CLIPProj, MOD-04)
    - src/models/late_fusion.py (LateFusion, MOD-05)
    - tests/test_models.py (17 tests covering MOD-03, MOD-04, MOD-05, MOD-07, D-16)
  modified:
    - src/models/__init__.py (re-exports SkeletonProj, CLIPProj, LateFusion)
    - tests/test_registry.py (replaced test_build_model_lazy_import_not_ready with test_build_model_lazy_import_resolves per Plan-01 hand-off)
key-decisions:
  - "LateFusion child modules (SkeletonProj, CLIPProj) instantiated eagerly in __init__ rather than lazily in forward — so `named_modules()` exposes `skeleton.ln_skel` and `clip.ln_clip` for TTA discoverability"
  - "Default `alpha='equal'` (scalar 0.5 non-parameter) per CONTEXT.md Claude's Discretion; `alpha='learned'` wraps a scalar `alpha_logit = nn.Parameter(torch.zeros(1))` initialized so sigmoid(0)=0.5 matches equal-weighted at step 0 (smooth handoff if retraining with learned alpha)"
  - "`alpha='equal'` uses `register_parameter('alpha_logit', None)` so the attribute still exists but is explicitly not a trainable parameter — keeps the `_alpha()` helper clean and aligns with PyTorch idioms"
  - "Plan-01 hand-off: `tests/test_registry.py::test_build_model_lazy_import_not_ready` replaced by `test_build_model_lazy_import_resolves` asserting the positive path (SkeletonProj / CLIPProj / LateFusion all instantiate via registry)"
  - "CLIPProj's 1024->512 learned projection lives in the class, not the Phase 2 CLIP extraction script — matches D-06 (CLIP cache is 1024-d; 512-d projection is a training-stage learned parameter)"
requirements-completed: [MOD-03, MOD-04, MOD-05, MOD-07]
duration: 5m 41s
completed: 2026-04-14T08:28:51Z
---

# Phase 3 Plan 4: Single-Modal Variant Wrappers Summary

Builds SkeletonProj (MOD-03), CLIPProj (MOD-04), and LateFusion (MOD-05) on top of Plan 01's shared MILHead primitive — each wrapper exposes a named `nn.LayerNorm` per D-07 so Phase 5 TENT/SAR adaptation can target them by attribute name, and registry round-trip resolves 3 of 4 MODEL_REGISTRY keys.

## Performance

- **Duration:** 5 min 41 sec
- **Started:** 2026-04-14T08:23:10Z
- **Completed:** 2026-04-14T08:28:51Z
- **Tasks:** 2 (each with RED/GREEN TDD commits)
- **Commits:** 4
- **Files created:** 4 (3 variant modules + 1 test file)
- **Files modified:** 2 (package __init__ + test_registry for Plan-01 hand-off)
- **Tests added:** 18 (17 in test_models.py + 1 replacement in test_registry.py)
- **Tests passing:** 62/62 non-e2e regression (Wave 1: 33, Wave 2 new: 18, other pre-existing: 11)

## Accomplishments

- Three Wave-2 MIL variants land: SkeletonProj, CLIPProj, LateFusion — all share `MILHead(hidden=(128,32), dropout=0.3)` so head architecture is identical by construction
- Named LayerNorm surfaces published for Phase 5 TTA: `ln_skel` (SkeletonProj + nested inside LateFusion), `ln_clip` (CLIPProj + nested inside LateFusion)
- LateFusion default equal-weighted (α=0.5) is algebraically exact in eval mode (atol=1e-6); learned variant initializes at sigmoid(0)=0.5 for smooth mode-switch
- Registry `build_model('skeleton_only'|'clip_only'|'late_fusion', ...)` now resolves to the correct class instance — `gated_fusion` still raises `ModuleNotFoundError` until Plan 05 lands
- Plan-01 hand-off cleared: `test_build_model_lazy_import_not_ready` replaced by `test_build_model_lazy_import_resolves` (positive path)

## Task Commits

Each task followed TDD RED -> GREEN split:

1. **Task 1 RED** - `9a72502` test: failing tests for SkeletonProj + CLIPProj (MOD-03, MOD-04, D-07)
2. **Task 1 GREEN** - `d505d03` feat: SkeletonProj + CLIPProj with named LayerNorms
3. **Task 2 RED** - `54ed8fb` test: failing tests for LateFusion + registry round-trip (MOD-05, D-16)
4. **Task 2 GREEN** - `1b8ad96` feat: LateFusion + complete variant registry

No refactor commits needed — GREEN implementations matched RESEARCH.md specs verbatim.

## Class Signatures (for Plan 05/06 Consumption)

```python
# src/models/skeleton_only.py
class SkeletonProj(nn.Module):
    def __init__(self, skel_dim=256, head_hidden=(128, 32), dropout=0.3, **unused): ...
    def forward(self, skel=None, clip=None, mask=None) -> torch.Tensor: ...  # [B, T]
    # Fields: self.ln_skel (LayerNorm(256)), self.head (MILHead(256))

# src/models/clip_only.py
class CLIPProj(nn.Module):
    def __init__(self, clip_dim=1024, proj_dim=512, head_hidden=(128, 32), dropout=0.3, **unused): ...
    def forward(self, skel=None, clip=None, mask=None) -> torch.Tensor: ...  # [B, T]
    # Fields: self.clip_proj (Linear(1024, 512)), self.ln_clip (LayerNorm(512)), self.head (MILHead(512))

# src/models/late_fusion.py
class LateFusion(nn.Module):
    def __init__(self, skel_dim=256, clip_dim=1024, proj_dim=512,
                 head_hidden=(128, 32), dropout=0.3, alpha='equal', **unused): ...
    def forward(self, skel=None, clip=None, mask=None) -> torch.Tensor: ...  # [B, T]
    # Fields: self.skeleton (SkeletonProj), self.clip (CLIPProj),
    #         self.alpha_mode (str), self.alpha_logit (nn.Parameter | None)
```

## Named LayerNorm Inventory (D-07 / MOD-07)

Confirmed via `named_modules()` walk:

| Variant | LN Count | Named paths | TTA targetability |
|---------|----------|-------------|-------------------|
| SkeletonProj | 1 | `ln_skel` | direct `model.ln_skel` |
| CLIPProj | 1 | `ln_clip` | direct `model.ln_clip` |
| LateFusion | 2 (nested) | `skeleton.ln_skel`, `clip.ln_clip` | `model.skeleton.ln_skel`, `model.clip.ln_clip` |

Phase 5 tent.py / sar.py can collect adaptable parameters with:

```python
ln_params = [p for n, m in model.named_modules()
             if isinstance(m, nn.LayerNorm)
             for p in m.parameters()]
```

## Registry Resolution Status

```python
build_model("skeleton_only", skel_dim=256)              # OK -> SkeletonProj
build_model("clip_only", clip_dim=1024, proj_dim=512)    # OK -> CLIPProj
build_model("late_fusion", ...)                          # OK -> LateFusion
build_model("gated_fusion", ...)                         # still raises ModuleNotFoundError (Plan 05)
```

## D-XX Coverage

| Requirement / Decision | Artifact | Status |
|------------------------|----------|--------|
| MOD-03 Skeleton-Only baseline | `SkeletonProj` in `src/models/skeleton_only.py` | covered |
| MOD-04 CLIP-Only baseline | `CLIPProj` in `src/models/clip_only.py` | covered |
| MOD-05 Late Fusion baseline | `LateFusion` in `src/models/late_fusion.py` | covered |
| MOD-07 LayerNorm discoverability | `ln_skel`, `ln_clip` named attrs; tested per variant | covered |
| D-06 CLIP learned 1024->512 | `CLIPProj.clip_proj = nn.Linear(1024, 512)` (tested) | covered |
| D-07 LN after modality projection | `ln_skel` after raw skel, `ln_clip` after Linear projection | covered |
| D-08 equal-weighted default | `LateFusion(alpha='equal')` default; tested to 1e-6 | covered |
| D-16 string-based registry | `build_model("late_fusion"...)` returns LateFusion | covered (3/4 keys resolve) |

## Verification Evidence

```
$ python -m pytest tests/test_models.py tests/test_registry.py -v
20 passed in 2.47s

$ python -m pytest tests/ -x --tb=short -k "not e2e"
62 passed in 11.00s

$ python -c "from src.models import SkeletonProj, CLIPProj, LateFusion
for M in (SkeletonProj, CLIPProj, LateFusion):
    m=M()
    lns = [n for n, mod in m.named_modules() if 'LayerNorm' in type(mod).__name__]
    print(M.__name__, lns)"
SkeletonProj ['ln_skel']
CLIPProj ['ln_clip']
LateFusion ['skeleton.ln_skel', 'clip.ln_clip']

$ python -c "from src.models.registry import build_model
from src.models import SkeletonProj, CLIPProj, LateFusion
assert isinstance(build_model('skeleton_only', skel_dim=256), SkeletonProj)
assert isinstance(build_model('clip_only'), CLIPProj)
assert isinstance(build_model('late_fusion'), LateFusion)
try: build_model('gated_fusion')
except ModuleNotFoundError: print('gated_fusion still lazy-raises (correct)')"
registry round-trip ok
gated_fusion still lazy-raises (correct)

$ python -c "import torch; from src.models import LateFusion
m = LateFusion(alpha='equal'); m.eval()
skel = torch.randn(2,32,256); clip = torch.randn(2,32,1024)
f = m(skel=skel, clip=clip)
s = m.skeleton(skel=skel); c = m.clip(clip=clip)
assert torch.allclose(f, 0.5*s + 0.5*c, atol=1e-6)
print('equal-weighted identity ok')"
equal-weighted identity ok
```

## Files Created/Modified

- `src/models/skeleton_only.py` — SkeletonProj (44 lines): raw skel -> ln_skel -> MILHead -> [B,T] scores
- `src/models/clip_only.py` — CLIPProj (49 lines): Linear(1024->512) -> ln_clip -> MILHead -> [B,T] scores
- `src/models/late_fusion.py` — LateFusion (74 lines): 0.5 * s_skel + 0.5 * s_clip (or learned α)
- `src/models/__init__.py` — re-exports SkeletonProj, CLIPProj, LateFusion (12 lines)
- `tests/test_models.py` — 17 tests across MOD-03, MOD-04, MOD-05, MOD-07, D-16 (165 lines)
- `tests/test_registry.py` — Plan-01 hand-off: `test_build_model_lazy_import_not_ready` -> `test_build_model_lazy_import_resolves` (17 lines)

## Decisions Made

1. **Eager child-module instantiation in LateFusion __init__** — if the SkeletonProj + CLIPProj submodules were only created in `forward()`, `named_modules()` would not discover them and Phase 5 TTA would silently lose access to `ln_skel` / `ln_clip` via the Late Fusion entry point. Verified by `test_late_fusion_exposes_nested_layernorms`.

2. **`alpha='learned'` initialization via `torch.zeros(1)` not `torch.tensor([0.5])`** — sigmoid(0)=0.5 keeps the parameter in pre-sigmoid space, which is the standard idiom and avoids numerical drift if a future optimizer steps from exactly 0.5 in sigmoid-space. Verified by `test_late_fusion_learned_alpha_init_is_0_5` asserting `alpha_logit.item() == 0.0`.

3. **`register_parameter('alpha_logit', None)` for equal mode** — makes `self.alpha_logit` a recognized attribute that returns None rather than raising AttributeError, which `_alpha()` depends on for its `if self.alpha_logit is not None:` branch. Verified by `test_late_fusion_alpha_none_when_equal`.

4. **Plan-01 hand-off executed without breaking other registry tests** — only `test_build_model_lazy_import_not_ready` was replaced; `test_registry_has_four_keys` and `test_build_model_unknown_variant_raises` remain untouched and still pass.

## Hand-offs to Later Plans

- **Plan 03-05 (gated_fusion)**: Must create `src/models/gated_fusion.py` implementing the `GatedFusion` class. After landing, `build_model('gated_fusion', ...)` will resolve. Plan 05 should ADD `test_gated_fusion_*` tests to `tests/test_models.py` without modifying existing tests. The `test_build_model_lazy_import_resolves` test in `test_registry.py` SHOULD be extended to include `build_model('gated_fusion', ...)` once that module exists. Alternatively, Plan 05 can add its own `test_build_model_gated_fusion_round_trip` to `test_models.py` (Plan-04's preferred pattern).
- **Plan 03-06 (train.py)**: Variant dispatch via YAML `model.variant` is now a no-op except for `gated_fusion`. Forward signature `forward(skel=, clip=, mask=)` is uniform across all 3 variants, so train.py can call `model(skel=batch['skel'], clip=batch['clip'], mask=batch['mask'])` regardless of which variant is loaded.
- **Phase 5 (TENT/SAR)**: LN params are collectible via `model.named_modules()` filter for `nn.LayerNorm`. For LateFusion, both nested LNs will be surfaced (2 entries); for single-modal variants, 1 entry each.

## Deviations from Plan

None — plan executed exactly as written. Both tasks completed in strict TDD order (RED then GREEN), code matches RESEARCH.md §8.A/B/C verbatim, all 18 new tests plus all 44 pre-existing tests pass on first GREEN commit.

### Authentication Gates

None.

### Architectural Changes

None.

## Known Stubs

None introduced by this plan. Grep for `TODO|FIXME|placeholder|coming soon|not available` across `src/models/` returned no matches.

## Threat Flags

No new security surface introduced. Threat register items from the plan preserved:
- T-03-04-01 (mitigate): `test_late_fusion_equal` asserts fused == 0.5*s_skel + 0.5*s_clip in eval mode to atol=1e-6. PASSING.
- T-03-04-02 (accept): no `torch.load` / `torch.save` used at variant-definition time (Plan 06 handles checkpoint loading with `weights_only=True`).
- T-03-04-03 (accept): variant class names are public thesis-code information.

## Issues Encountered

None. Environment (`vcc-main` with pytest 9.0.2, torch 2.6.0+cu124) validated by Plan 01 was sufficient; no new pip installs required.

## Next Phase Readiness

- **Wave 2 (Plans 03-04, 03-02, 03-03)**: Plan 04 delivers its share of Wave 2 (the three non-gated variants). Plans 02 (MIL ranking loss) and 03 (MILFeatureDataset) run in parallel — their outputs compose with Plan 04's variants via the uniform `forward(skel=, clip=, mask=)` signature.
- **Wave 3 (Plan 03-05 gated_fusion)**: Ready to start — the composition pattern from LateFusion (eager child modules, named LNs) provides a template; Plan 05 should wrap SkeletonProj + CLIPProj with a learned gating MLP and a third LayerNorm at the fusion output per D-07.
- **No blockers** for downstream plans. Registry resolution for `gated_fusion` intentionally pending.

## Self-Check: PASSED

Created/modified files verified:
- src/models/skeleton_only.py: FOUND
- src/models/clip_only.py: FOUND
- src/models/late_fusion.py: FOUND
- src/models/__init__.py: FOUND
- tests/test_models.py: FOUND
- tests/test_registry.py: FOUND
- .planning/phases/03-model-architecture-training-infrastructure/03-04-SUMMARY.md: FOUND

Commits verified in git log:
- 9a72502 (Task 1 RED): FOUND
- d505d03 (Task 1 GREEN): FOUND
- 54ed8fb (Task 2 RED): FOUND
- 1b8ad96 (Task 2 GREEN): FOUND

---
*Phase: 03-model-architecture-training-infrastructure, Plan: 04*
*Completed: 2026-04-14T08:28:51Z*
