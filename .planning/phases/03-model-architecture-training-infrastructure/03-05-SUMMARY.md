---
phase: 03-model-architecture-training-infrastructure
plan: 05
subsystem: models
tags: [phase-3, wave-3, tdd, gated-fusion, mod-06, mod-07, d-07, layernorm-tta, m1-mitigation]
requires:
  - Plan 03-01: MILHead(input_dim, hidden_dims=(128,32), dropout=0.3), MODEL_REGISTRY lazy factory for gated_fusion
  - Plan 03-04: SkeletonProj / CLIPProj / LateFusion already registered (wave-3 dep: variant wrapper pattern + registry round-trip)
  - Phase 2 cache contracts: skeleton [N,256] (D-05), CLIP [N,1024] (D-06)
provides:
  - "GatedFusion(skel_dim=256, clip_dim=1024, shared_dim=256, head_hidden=(128,32), dropout=0.3)"
  - "forward(skel=[B,T,256], clip=[B,T,1024], mask=None) -> [B,T] scores in [0,1]"
  - "3 named nn.LayerNorm attrs: ln_skel, ln_clip, ln_fused (D-07; Phase 5 TTA surface)"
  - "m1 mitigation: Xavier gain=0.1 on gate.weight + zero bias -> mean(gate) ~= 0.5 at init"
  - "MODEL_REGISTRY fully resolved: build_model('gated_fusion', ...) returns GatedFusion"
affects:
  - Plan 03-06 (train.py): variant dispatch is now complete; `build_model(**cfg['model'])` works for all 4 YAML variants
  - Plan 03-07 (config files): configs/gated_fusion.yaml now has a resolvable target class
  - Phase 5 (TTA): tent.py / sar.py can collect Gated Fusion LN params via `model.named_modules()` filter
tech-stack:
  added: []  # No new deps; reuses Wave 1 MILHead + torch.nn
  patterns:
    - "3-LN placement (D-07): ln_skel after skel_proj, ln_clip after clip_proj, ln_fused at fusion output"
    - "Residual gradient highway: residual = fused + p_skel + p_clip (sum of both projections + fused)"
    - "m1 mitigation pattern: xavier_uniform_(weight, gain=0.1) + zeros_(bias) for sigmoid gates to avoid saturation at init"
    - "Attribute-level LN exposure (not just named_modules): direct model.ln_skel / ln_clip / ln_fused access"
    - "Uniform forward signature: forward(skel=None, clip=None, mask=None) across all 4 variants"
    - "TDD RED -> GREEN commit split (continued from Plans 01/04)"
key-files:
  created:
    - src/models/gated_fusion.py (GatedFusion, 81 lines)
  modified:
    - src/models/__init__.py (re-exports GatedFusion)
    - tests/test_models.py (9 new tests appended, ~153 lines)
decisions:
  - "Implemented RESEARCH.md 8.D verbatim: 3 LN + gradient-highway residual + MILHead tail. No deviation from spec"
  - "Kept LN count at 3 (plan default), not 4-5. CONTEXT.md Claude's Discretion: 'could add ln_head0/ln_head1 if Phase 5 experiments need more TTA params. Default: keep to 3 LN.'"
  - "Dual validation for m1 mitigation: (1) runtime test asserts mean(gate) in [0.4, 0.6] over 10 random batches; (2) static test asserts gate.weight.std() < 0.1. Runtime catches future refactors that change sigmoid/init logic; static catches refactors that change just the Xavier gain constant"
  - "Used **unused kwarg absorber in __init__ (consistent with Plan 04 variants): YAML model.variant config may pass variant-specific kwargs that GatedFusion does not consume (e.g., alpha from LateFusion configs); **unused makes build_model variant swapping config-file-homogeneous"
  - "Residual written exactly as 'residual = fused + p_skel + p_clip' to satisfy the plan's literal grep pattern at line 390 and preserve RESEARCH.md 8.D wording"
requirements-completed: [MOD-06, MOD-07]
metrics:
  duration: 3m 48s
  completed: 2026-04-14T08:39:19Z
  tasks_executed: 1
  commits: 2
  files_created: 1
  files_modified: 2
  tests_added: 9
  tests_passing: 71  # full regression (62 Wave-1/2 + 9 new); non-e2e, non-requires_features
---

# Phase 3 Plan 5: Gated Fusion Summary

Lands the load-bearing Gated Fusion module (MOD-06) per PRD §9.2 + RESEARCH.md §8.D — 256-d shared projections of skeleton and CLIP features, sigmoid gate with m1-mitigation initialization (Xavier gain=0.1), residual gradient-highway sum of both projections + fused vector, LayerNorm at the fusion output, Dropout, and the shared MILHead tail. Three named LNs (`ln_skel`, `ln_clip`, `ln_fused`) make the Phase 5 TTA surface meaningful per D-07. The MODEL_REGISTRY now resolves all 4 variants.

## Performance

- **Duration:** 3 min 48 sec
- **Started:** 2026-04-14T08:35:31Z
- **Completed:** 2026-04-14T08:39:19Z
- **Tasks:** 1 (RED/GREEN TDD split)
- **Commits:** 2
- **Files created:** 1 (`src/models/gated_fusion.py`)
- **Files modified:** 2 (`src/models/__init__.py`, `tests/test_models.py`)
- **Tests added:** 9 (all MOD-06 + MOD-07 VALIDATION.md-named tests plus m1 regression guards)
- **Tests passing:** 71/71 full non-e2e regression (includes all Wave 1/2 tests)

## Accomplishments

- `GatedFusion` implemented per PRD §9.2 spec exactly as quoted in RESEARCH.md §8.D (architecture, 3-LN inventory, m1 init)
- All 9 new VALIDATION.md-named tests green on first GREEN commit; 62 prior Wave 1/2 tests remain green
- **Registry complete:** `build_model('skeleton_only'|'clip_only'|'late_fusion'|'gated_fusion')` all resolve; no more `ModuleNotFoundError` lazy-raise paths
- **Param count:** 498,113 total (skel_proj 65K + clip_proj 262K + gate 131K + MILHead 37K + LN gamma/beta)
- **m1 mitigation verified both ways:**
  - Runtime: 10-batch mean(gate) = ~0.5 (test range `0.4 < mean < 0.6`)
  - Static: `gate.weight.std() < 0.1`, `gate.bias == 0`
- **Real-feature integration:** `test_gated_fusion_real_features` ran positively on cached UCF `.npy` (E:/features/ucf/ is mounted; test produced `[1,32]` scores in `[0,1]` with no NaN)

## Class Signature (for Plan 06/07 Consumption)

```python
# src/models/gated_fusion.py
class GatedFusion(nn.Module):
    def __init__(self,
                 skel_dim: int = 256,
                 clip_dim: int = 1024,
                 shared_dim: int = 256,
                 head_hidden=(128, 32),
                 dropout: float = 0.3,
                 **unused) -> None: ...

    def forward(self, skel=None, clip=None, mask=None) -> torch.Tensor:
        """skel: [B, T, skel_dim], clip: [B, T, clip_dim] -> scores [B, T] in [0, 1]"""

    # Named attributes (all 3 are nn.LayerNorm(shared_dim=256) by default):
    #   self.ln_skel, self.ln_clip, self.ln_fused
    # Other modules:
    #   self.skel_proj (Linear(256, 256)), self.clip_proj (Linear(1024, 256))
    #   self.gate (Linear(512, 256) — Xavier gain=0.1 init, bias=0)
    #   self.dropout (Dropout(0.3))
    #   self.head (MILHead(input_dim=256))
```

## Forward Path (Verbatim Per RESEARCH.md §8.D)

```
p_skel = ln_skel(skel_proj(skel))                                  # [B, T, 256]
p_clip = ln_clip(clip_proj(clip))                                  # [B, T, 256]
g      = sigmoid(gate(cat([p_skel, p_clip], dim=-1)))              # [B, T, 256] in [0, 1]
fused  = g * p_skel + (1 - g) * p_clip                             # [B, T, 256]
residual = fused + p_skel + p_clip                                 # gradient highway
out    = dropout(ln_fused(residual))                               # [B, T, 256]
scores = head(out).squeeze(-1)                                     # [B, T]
```

## D-XX Coverage

| Requirement / Decision | Artifact | Status |
|------------------------|----------|--------|
| MOD-06 Gated Fusion module | `GatedFusion` in `src/models/gated_fusion.py` | covered |
| MOD-07 LN discoverability | 3 named LN attrs + `named_modules()` filter | covered |
| D-07 LN placement (after every modality projection + at fusion output) | `ln_skel`, `ln_clip`, `ln_fused` | covered (3 of 3 positions) |
| D-08 module organization (shared MILHead) | `MILHead(input_dim=shared_dim=256, hidden_dims=(128, 32), dropout=0.3)` | covered |
| D-16 string-based registry (all 4 keys resolve) | `build_model('gated_fusion', ...)` returns GatedFusion | covered — registry now complete |
| PRD §9.2 residual = sum of both projections + fused | `residual = fused + p_skel + p_clip` (grep-asserted) | covered |
| m1 mitigation (PITFALLS.md: gate saturation) | `nn.init.xavier_uniform_(self.gate.weight, gain=0.1)` + `zeros_(bias)` | covered |

## Named LayerNorm Inventory (D-07 / MOD-07)

Confirmed via `named_modules()` walk at GatedFusion root:

| LN name | Attribute path | normalized_shape | Where in forward |
|---------|----------------|------------------|------------------|
| `ln_skel` | `model.ln_skel` | `(256,)` | After `skel_proj` (256->256) |
| `ln_clip` | `model.ln_clip` | `(256,)` | After `clip_proj` (1024->256) |
| `ln_fused` | `model.ln_fused` | `(256,)` | On residual (gradient highway) |

`MILHead` has no LN in the base spec (only Linear + ReLU + Dropout + Sigmoid), so the LN total for GatedFusion at root is exactly 3. CONTEXT.md Claude's Discretion allows adding `ln_head0` / `ln_head1` in Phase 5 if TTA surface proves insufficient.

Phase 5 TTA parameter collection (from RESEARCH.md §10):

```python
# Collect adaptable (gamma, beta) parameters from Gated Fusion
ln_params = [p for n, m in model.named_modules()
             if isinstance(m, nn.LayerNorm)
             for p in m.parameters()]
# len(ln_params) == 3 LNs × 2 (weight+bias) == 6 tensors, 6 * 256 == 1,536 scalar params
```

## m1 Mitigation Evidence

**Initialization:**
```python
nn.init.xavier_uniform_(self.gate.weight, gain=0.1)  # std ~= 0.1 * sqrt(6/(512+256)) ~= 0.009
nn.init.zeros_(self.gate.bias)                        # bias == 0 exactly
```

**Runtime test (`test_gated_fusion_gate_not_saturated_at_init`):** Over 10 random batches of shape `[4, 32, _]`, measured `mean(sigmoid(gate(...)))`. Test asserts overall mean in `(0.4, 0.6)`. Passed on first run.

**Static test (`test_gated_fusion_gate_xavier_gain_small`):** Asserts `model.gate.weight.std().item() < 0.1` and `torch.all(model.gate.bias == 0.0)`. Passed on first run.

Dual-test redundancy catches two different regression paths:
- Runtime check catches if `sigmoid` is swapped for an unsquashed activation or if the forward computation changes.
- Static check catches if a future PR flips the gain back to the default 1.0 but keeps sigmoid.

## Registry Resolution Status (Complete)

```python
build_model("skeleton_only", skel_dim=256)                          # -> SkeletonProj
build_model("clip_only", clip_dim=1024, proj_dim=512)               # -> CLIPProj
build_model("late_fusion", ...)                                     # -> LateFusion
build_model("gated_fusion", skel_dim=256, clip_dim=1024, shared_dim=256)  # -> GatedFusion (NEW)
```

Wave 1 (Plan 03-01) -> Wave 2 (Plan 03-04) -> Wave 3 (Plan 03-05) chain is now code-complete for all 4 MIL variants.

## Verification Evidence

```
$ python -m pytest tests/test_models.py -v --tb=short -k "gated_fusion or build_model_gated"
tests/test_models.py::test_gated_fusion_shapes PASSED                         [ 11%]
tests/test_models.py::test_gated_fusion_real_features PASSED                  [ 22%]
tests/test_models.py::test_gated_fusion_layernorms PASSED                     [ 33%]
tests/test_models.py::test_gated_fusion_layernorm_attribute_access PASSED     [ 44%]
tests/test_models.py::test_gated_fusion_gate_not_saturated_at_init PASSED     [ 55%]
tests/test_models.py::test_gated_fusion_gate_xavier_gain_small PASSED         [ 66%]
tests/test_models.py::test_gated_fusion_residual_is_sum_of_both_projections PASSED  [ 77%]
tests/test_models.py::test_gated_fusion_raises_without_both_inputs PASSED     [ 88%]
tests/test_models.py::test_build_model_gated_fusion_round_trip PASSED         [100%]
========================= 9 passed, 17 deselected in 2.85s =========================

$ python -m pytest tests/ -x --tb=short -k "not e2e and not requires_features"
tests\test_dataset.py ..........                                         [ 14%]
tests\test_mil_head.py ......                                            [ 22%]
tests\test_mil_loss.py ...........                                       [ 38%]
tests\test_models.py ..........................                          [ 74%]
tests\test_registry.py ...                                               [ 78%]
tests\test_seed.py ......                                                [ 87%]
tests\test_splits.py .........                                           [100%]
========================= 71 passed in 11.43s =========================

$ python -c "from src.models import GatedFusion; import torch.nn as nn; m=GatedFusion(); lns=[n for n,mod in m.named_modules() if isinstance(mod, nn.LayerNorm)]; print(lns)"
['ln_skel', 'ln_clip', 'ln_fused']

$ python -c "import torch; from src.models import GatedFusion; torch.manual_seed(0); m=GatedFusion(); skel=torch.randn(2,32,256); clip=torch.randn(2,32,1024); o=m(skel=skel, clip=clip); print(o.shape, o.min().item(), o.max().item(), torch.isfinite(o).all().item())"
torch.Size([2, 32]) <in (0, 1)> <in (0, 1)> True

$ python -c "from src.models.registry import build_model; from src.models import GatedFusion; assert isinstance(build_model('gated_fusion', skel_dim=256, clip_dim=1024, shared_dim=256), GatedFusion); print('ok')"
ok

$ findstr /C:"xavier_uniform_(self.gate.weight, gain=0.1)" D:\ViolenceCC\src\models\gated_fusion.py
        nn.init.xavier_uniform_(self.gate.weight, gain=0.1)

$ findstr /C:"self.ln_fused = nn.LayerNorm" D:\ViolenceCC\src\models\gated_fusion.py
        self.ln_fused = nn.LayerNorm(shared_dim)

$ findstr /C:"residual = fused + p_skel + p_clip" D:\ViolenceCC\src\models\gated_fusion.py
        residual = fused + p_skel + p_clip                    # gradient highway

$ python -c "from src.models import GatedFusion; n=sum(p.numel() for p in GatedFusion().parameters()); print(f'n_params={n:,}')"
n_params=498,113
```

## Commit Lineage

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| 1 RED | `9260652` | test | 9 failing tests for GatedFusion (module doesn't exist -> ModuleNotFoundError at collection) |
| 1 GREEN | `5084f48` | feat | GatedFusion module with 3 named LNs + m1 gate init; 9/9 new tests + 62 regression green |

No REFACTOR commit — GREEN implementation matched RESEARCH.md §8.D verbatim on first write.

## Decisions Made

1. **Literal verbatim implementation of RESEARCH.md §8.D:** Every code line of the `GatedFusion.__init__` and `forward` blocks was preserved exactly as written (including comments and the `residual = fused + p_skel + p_clip` phrasing), because the plan's acceptance criteria include literal grep-pattern assertions against these strings. Reduces ambiguity and ensures plan-verifier satisfaction.

2. **Dual m1-mitigation testing (runtime + static):** Plan specifies both `test_gated_fusion_gate_not_saturated_at_init` (runtime mean(gate)) and `test_gated_fusion_gate_xavier_gain_small` (static weight std). Both kept. Rationale: different refactor paths break each test independently; keeping both maximizes regression-guard coverage for the m1 pitfall identified in PITFALLS.md.

3. **`**unused` kwarg absorber kept consistent with Plan 04 variants:** YAML-driven `build_model(**cfg['model'])` calls may pass variant-specific kwargs not applicable to GatedFusion (e.g., `alpha` from a LateFusion config if someone hot-swaps a variant). `**unused` absorbs them silently so the 4 variants share a homogeneous keyword-calling convention from train.py's perspective.

4. **No additional LNs (3, not 4-5):** CONTEXT.md line 121 says "4-5 LayerNorm layers in Gated Fusion is a deliberate Phase 5 enabler — small head with single LN risks the 'nothing to adapt' failure mode". RESEARCH.md §8.D then defaults to 3 LN at root (with an optional note: "ln_head0/ln_head1 could be added if Phase 5 experiments need more TTA params. Default: keep to 3 LN."). Plan 03-05's `must_haves.truths` requires **at least 3** LNs. Stayed with 3; Phase 5 can add head-level LNs if TTA surface proves insufficient.

5. **`head` is a `MILHead` submodule (3 dense layers + 2 LN-less dropouts + sigmoid, no LN), so `named_modules()` inside the head returns 0 LN.** The total count at GatedFusion root is exactly 3 LN — matches test expectations.

## Hand-offs to Later Plans

- **Plan 03-06 (train.py)**: `build_model(**cfg['model'])` now resolves for **all** YAML variants. Training loop can call `model(skel=batch['skel'], clip=batch['clip'], mask=batch['mask'])` regardless of variant — forward signature is uniform. The `m1` smoke-run check (`test_gate_not_saturated` in `tests/test_train_integration.py`) from VALIDATION.md Wave 0 will run against this module after 5 epochs and assert `0.2 < mean(gate) < 0.8`.
- **Plan 03-07 (config files)**: `configs/gated_fusion.yaml` can now land with `model.variant: gated_fusion` + `model.skel_dim: 256` + `model.clip_dim: 1024` + `model.shared_dim: 256` + `model.head_hidden: [128, 32]` + `model.dropout: 0.3`. All kwargs are accepted by `GatedFusion.__init__`.
- **Phase 5 (TENT/SAR)**: The 3 LN attributes (`model.ln_skel`, `model.ln_clip`, `model.ln_fused`) give the TTA loop exactly 6 tensors of `(gamma, beta)` to adapt — 1,536 scalar parameters total (3 * 2 * 256). Matches RESEARCH.md §10 target size range.

## Deviations from Plan

None — plan executed exactly as written. The single task (RED -> GREEN) matched RESEARCH.md §8.D verbatim, all 9 new tests plus all 62 pre-existing tests pass on first GREEN commit, no refactor was needed, no auto-fixes required.

### Authentication Gates

None.

### Architectural Changes

None.

## Known Stubs

None introduced by this plan. Grep for `TODO|FIXME|placeholder|coming soon|not available` across `src/models/gated_fusion.py` returned no matches.

## Threat Flags

No new security surface introduced. Threat register items from the plan preserved:
- T-03-05-01 (mitigate): `test_gated_fusion_gate_xavier_gain_small` + `test_gated_fusion_gate_not_saturated_at_init`. BOTH PASSING — m1 mitigation guarded statically and dynamically.
- T-03-05-02 (mitigate): `test_gated_fusion_layernorms` + `test_gated_fusion_layernorm_attribute_access`. BOTH PASSING — any LN rename breaks the test and the Phase 5 TTA contract loudly.
- T-03-05-03 (accept): residual gradient highway could theoretically amplify gradients, but all three terms pass through LN before summing (unit variance by construction). No NaN in any test; Plan 06 smoke tests will verify stability over 50 training epochs.
- T-03-05-04 (accept): architecture details are public thesis information.

## Issues Encountered

None. Environment (`vcc-main` with pytest 9.0.2, torch 2.6.0+cu124) validated by Plans 01/04 was sufficient; no new pip installs required. `E:/features/ucf/` is mounted, so the integration test `test_gated_fusion_real_features` ran positively rather than skipping — extra free verification.

## Next Wave Readiness

- **Wave 3 (Plan 03-05)**: Complete. All 4 MIL variants exist, forward signature is uniform, registry resolves all 4 keys, LN discoverability works across variants.
- **Wave 4 (Plans 03-06, 03-07)**: Ready to start — train.py can dispatch to any variant via YAML config change; config files need only specify `model.variant` and the variant-specific kwargs.
- **Phase 5 readiness**: `model.ln_skel / ln_clip / ln_fused` is the TTA surface contract. All 4 variants support `named_modules()` LN filtering. Gated Fusion specifically has 3 LN × 2 params × 256 dim = 1,536 adaptable scalars — enough surface for TENT/SAR without triggering the "nothing to adapt" failure mode (PRD §9.4).
- **No blockers** for downstream plans.

## Self-Check: PASSED

Created/modified files verified:
- src/models/gated_fusion.py: FOUND
- src/models/__init__.py: FOUND (modified, GatedFusion re-exported)
- tests/test_models.py: FOUND (modified, 9 new tests appended)
- .planning/phases/03-model-architecture-training-infrastructure/03-05-SUMMARY.md: FOUND

Commits verified in git log:
- 9260652 (Task 1 RED): FOUND
- 5084f48 (Task 1 GREEN): FOUND

---
*Phase: 03-model-architecture-training-infrastructure, Plan: 05*
*Completed: 2026-04-14T08:39:19Z*
