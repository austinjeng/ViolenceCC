---
phase: 04-baseline-evaluation-main-results
plan: 03
subsystem: models
tags: [rtfm, i3d, xd-violence, 5-crop, d-18, d-19, d-20, d-36, model-registry, pitfall-3, pitfall-4, tdd]

# Dependency graph
requires:
  - phase: 04-baseline-evaluation-main-results
    plan: 01
    provides: "tests/fixtures/synthetic_eval.make_synthetic_i3d factory + conftest synthetic_i3d_features fixture (5-crop XD-shaped cache under tmp_path)"
  - phase: 04-baseline-evaluation-main-results
    plan: 02
    provides: "src/eval/test_loader.build_test_dataset xd_i3d dispatch branch (stub pointer replaced by live import here); src/evaluate.py xd_i3d label-construction branch unblocked"
  - phase: 03-model-architecture-training-infrastructure
    provides: "src.models.mil_head.MILHead (reused verbatim); src/models/skeleton_only.SkeletonProj structural analog (single-LN + MILHead + **unused kwargs pattern); src/models/registry.MODEL_REGISTRY lazy-factory scheme (extended in place)"
provides:
  - "src/models/rtfm_i3d.RTFMI3D(i3d_dim=1024) — minimum-viable FM head per CONTEXT.md Discretion (LN(1024) + MILHead; NO MTN temporal module)"
  - "src/models/rtfm_i3d.RTFMI3D.ln_i3d — named nn.LayerNorm(1024,) for Phase 5 TTA parameter iteration via model.named_modules() (D-07)"
  - "src/models/registry.MODEL_REGISTRY['rtfm_i3d'] — 5th variant; unchanged lazy-import convention"
  - "src/data/i3d_dataset.I3DFeatureDataset(split_file, feature_dir, mode, T, n_crops=5) — D-19 5-crop train expansion + test averaging; Pitfall-4 missing-video filter + collapsed-ratio warning"
  - "configs/rtfm_i3d.yaml — training config binding dataset=xd_i3d, variant=rtfm_i3d, batch_size=3 (Pitfall 3), wandb tags=[phase4,rtfm_i3d,xd_i3d,i3d_rgb]"
affects:
  - 04-05 (scripts/run_ablations.py can queue RunSpec('xd_i3d','rtfm_i3d',42,'configs/rtfm_i3d.yaml') as the `rtfm_gate` first run)
  - 04-06 (empirical execution: training subprocess launches train.py with configs/rtfm_i3d.yaml → I3DFeatureDataset feeds 5-crop bags → RTFMI3D forward → MIL ranking loss)
  - 05-tta (Phase 5 reads rtfm_i3d best_model.pth and iterates ln_i3d LayerNorm affine parameters for entropy minimization)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "5-variant MODEL_REGISTRY with uniform forward signature (skel, clip, i3d, mask) and **unused kwargs tolerance"
    - "Named-LN discoverability invariant (ln_i3d mirrors ln_skel / ln_clip / ln_fused) for Phase 5 TTA"
    - "5-crop dataset dispatch: train returns [5, T, 1024] stacked, test averages to [N, 1024] before forward"
    - "Construct-time cache-existence filter with stdout count log + stderr collapsed-ratio warning (Pitfall 4 pattern)"
    - "Missing-crop pad from crop 0 (graceful degradation for partial cache)"
    - "TDD RED-GREEN discipline at per-task level; commit RED before any implementation"
    - "Acceptance-grep sentinel pattern (plan spells grep -c targets; tests/code carry matching strings)"

key-files:
  created:
    - "src/models/rtfm_i3d.py"
    - "src/data/i3d_dataset.py"
    - "configs/rtfm_i3d.yaml"
    - "tests/test_rtfm_i3d.py"
    - "tests/test_i3d_dataset.py"
  modified:
    - "src/models/registry.py"
    - "tests/test_registry.py"

key-decisions:
  - "D-18 implemented: MODEL_REGISTRY['rtfm_i3d'] routes to src.models.rtfm_i3d.RTFMI3D via lazy factory; existing 4 keys unchanged."
  - "D-18 MVP scope: RTFMI3D is LN(1024) + MILHead, NO MTN temporal module. CONTEXT.md Discretion explicitly permits MVP if the ±1% gate passes empirically; Phase 4b fallback adds MTN if not."
  - "D-19 implemented: I3DFeatureDataset test mode averages 5 crops to [N, 1024]; train mode returns [5, T, 1024] stacked. Crop-averaging in train collate is deferred to Plan 04-06 empirical tuning per Pitfall 3 Option A/B/C triage."
  - "D-19 extension: _load_crops pads missing crops 1..4 by duplicating crop 0 (XD has ≥1 4-crop training video). _has_at_least_one_crop gates construction-time filtering; subsequent mid-run failures raise loudly."
  - "D-20 implemented: configs/rtfm_i3d.yaml binds paths.i3d_features + dataset: xd_i3d; no skeleton_features / clip_features keys (rtfm_i3d consumes only the I3D cache)."
  - "D-36 implemented: train.py + evaluate.py dispatch via cfg['dataset'] == 'xd_i3d' → I3DFeatureDataset; gated_fusion / skeleton_only / clip_only variants remain on UCF path."
  - "Pitfall 3 mitigation chosen in YAML: batch_size=3 (Option A per RESEARCH.md). 5 crops × 3 videos = 15 effective samples, preserving the k_topk=3 ratio from Phase 3 D-01. Empirical upshift to 16 is an open question for Plan 04-06 (documented in YAML comment block)."
  - "Pitfall 4 mitigation: three-layer defense — crop-0 existence filter at __init__, stdout log of k/n filtered count, stderr warning if filtered set collapses to all-normal or all-abnormal."
  - "ln_i3d name chosen to mirror ln_skel / ln_clip / ln_fused. Phase 5 TTA iterates `[n for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)]` and this convention makes the parameter set trivially enumerable across all 5 variants."
  - "Train-mode _resample_T uses deterministic np.random.default_rng(seed=0) for N<T sample-with-replacement (parallel to Phase 3 D-10-revised). Each dataset construction gets a fresh RNG; within-epoch determinism inherits from PyTorch DataLoader worker seed."
  - "XD label parsing duplicated locally (vid.endswith('_label_A')) rather than imported from src.data.dataset._parse_label_xd. Rationale: keeps the training-path module (src.data.dataset) independent of the harness-path module (src.data.i3d_dataset) per Phase 4 D-07 import-graph isolation philosophy (Plan 02 SUMMARY)."

patterns-established:
  - "Pattern: 5th-variant addition — new module under src/models/, lazy factory in registry.py, grep-discoverable variant string in MODEL_REGISTRY, tests parallel to tests/test_models.py (shape + LN + registry round-trip + factory hygiene)."
  - "Pattern: harness-path dataset module — lives under src/data/ (not src/eval/) to avoid pulling the sys.argv guard from src/eval/test_loader.py into the build_test_dataset import chain."
  - "Pattern: synthetic-fixture driven Dataset test — tmp_path/.npy artifacts + split file → Dataset(...) + __getitem__ shape asserts. Mirrors the Plan 01 make_synthetic_i3d factory consumed via conftest synthetic_i3d_features fixture."
  - "Pattern: yaml schema assertion inside test suite — reads real config from repo, asserts required keys + sentinel values; test_yaml_schema locks the YAML against drift."

requirements-completed:
  - EVAL-01
  - EVAL-03

# Metrics
duration: 8min
completed: 2026-04-15
---

# Phase 4 Plan 03: RTFM variant + I3D 5-crop dataset + rtfm_i3d.yaml Summary

**Ships the EVAL-01 harness-gate trio: `src/models/rtfm_i3d.RTFMI3D` (minimum-viable FM head = LN(1024) + MILHead; no MTN temporal module per CONTEXT.md Discretion) registered as the 5th MODEL_REGISTRY key, `src/data/i3d_dataset.I3DFeatureDataset` (D-19 5-crop train expansion + test averaging; Pitfall-4 missing-video filter with startup log and collapsed-ratio warning; pad-from-crop-0 graceful degradation), and `configs/rtfm_i3d.yaml` (dataset=xd_i3d, batch_size=3 per Pitfall-3 recommendation, wandb tags [phase4, rtfm_i3d, xd_i3d, i3d_rgb]). 18 new tests green (9 RTFMI3D + 10 I3DFeatureDataset + 1 registry 5-key update). Plan 02's `xd_i3d` dispatch stub is retired — `build_test_dataset` now reaches `I3DFeatureDataset` directly, and Plan 05's `run_ablations.py` can queue `RunSpec("xd_i3d", "rtfm_i3d", 42, "configs/rtfm_i3d.yaml")` as the first run.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-15T10:31:01Z
- **Completed:** 2026-04-15T10:39:24Z
- **Tasks:** 2 (each with TDD RED + GREEN)
- **Files modified:** 7 (5 created, 2 edited)

## Accomplishments

- **RTFMI3D model** (`src/models/rtfm_i3d.py`): `RTFMI3D(i3d_dim=1024, head_hidden=(128,32), dropout=0.3, **unused)` with a single named `self.ln_i3d = nn.LayerNorm(1024)` + `self.head = MILHead(input_dim=1024, ...)`. Forward accepts the variant-uniform `(skel, clip, i3d, mask)` signature, raises `ValueError` if `i3d` is missing, squeezes the trailing `[...,1]` dim only when present (supports both `[B,T,1024]` and `[B,1024]` inputs). Mirrors `src/models/skeleton_only.SkeletonProj` verbatim in shape and LN-naming convention. No MTN temporal module — minimum-viable per CONTEXT.md Discretion.
- **5th MODEL_REGISTRY entry** (`src/models/registry.py`): new `_get_rtfm_i3d` lazy factory + `MODEL_REGISTRY["rtfm_i3d"] = _get_rtfm_i3d`. Existing 4 keys unchanged; `build_model(variant="rtfm_i3d")` returns an `RTFMI3D` instance. `test_registry.py::test_registry_has_four_keys` updated in-place to `test_registry_has_five_keys` (clean rename — no legacy test left asserting only 4 keys).
- **I3DFeatureDataset** (`src/data/i3d_dataset.py`): full 5-crop dispatch per D-19. Test mode loads 5 crops, averages to `[N, 1024]` float32. Train/val mode stacks 5 crops after `_resample_T` uniform-segment sampling to `T=32` giving `[5, 32, 1024]`. Missing crops 1..4 pad by duplicating crop 0 at load time. Construct-time filter drops videos missing crop 0 with a startup log `"[i3d_dataset] <mode>: <k>/<n> videos available (feature_dir=...)"`. Stderr `"WARNING: no [normal|abnormal] videos after filtering; normal/abnormal ratio collapsed"` fires if the filtered set loses either class (MIL bag pairing safety). `np.load` called without `allow_pickle` (threat mitigation T-04-03-01).
- **rtfm_i3d.yaml** (`configs/rtfm_i3d.yaml`): full training config per PATTERNS.md. `dataset: xd_i3d`, `paths.i3d_features: "E:/i3d-features/i3d-features"` (no `skeleton_features` / `clip_features`), `model.variant: rtfm_i3d`, `model.i3d_dim: 1024`, `data.batch_size: 3` (Pitfall 3: 5-crop × 3 ≈ 15 effective vs `k_topk=3` preservation), `train.k_topk: 3 / margin: 1.0 / lam_sparse: 8e-3 / lam_smooth: 8e-4` (Phase 3 inheritance), `wandb.tags: [phase4, rtfm_i3d, xd_i3d, i3d_rgb]`. Trailing comment documents the 77.81%±1% gate and the batch-size upshift option.
- **Plan 02 stub retired**: `src/eval/test_loader.py::build_test_dataset(cfg with dataset='xd_i3d')` now imports `I3DFeatureDataset` directly without hitting the Plan-04-03 pointer RuntimeError. The xd_i3d path is live end-to-end from `evaluate.py` onward.
- **18 new tests green + 1 existing test renamed**:
  - `tests/test_rtfm_i3d.py` (9 tests): R1 registry dispatch; R2/R3 forward shape `[2,32,1024]→[2,32]` + finite; R3 spot on `[1,32,1024]`; R4/R7 named `ln_i3d` LayerNorm(1024,) via `named_modules()`; R4 attribute access; R5 missing-i3d `ValueError`; R6 variant-uniform kwargs tolerance; factory-import hygiene (no transitive i3d_dataset import).
  - `tests/test_i3d_dataset.py` (10 tests): D1 test-mode shape + label; D2 train-mode shape `[5,32,1024]`; D3 label_A→0 mapping; D4 missing-crops pad from crop 0; D5 missing-video filter + stdout log; D6 all-normal collapsed-ratio stderr; D6 mirror all-abnormal; D7 YAML schema assertion; invalid-mode defensive; Plan 02 importability smoke.
  - `tests/test_registry.py::test_registry_has_five_keys` (renamed from `_has_four_keys`).

## Task Commits

TDD discipline produced 4 commits (test RED → feat GREEN for each task):

1. **Task 1 RED: failing RTFMI3D + 5-key registry tests** — `edb6b99` (test)
2. **Task 1 GREEN: RTFMI3D module + registry entry** — `ebf4ca6` (feat)
3. **Task 2 RED: failing I3DFeatureDataset + yaml schema tests** — `3c46b62` (test)
4. **Task 2 GREEN: I3DFeatureDataset + rtfm_i3d.yaml** — `a8db06f` (feat)

## Files Created/Modified

- `src/models/rtfm_i3d.py` — new RTFMI3D class (LN(1024) + MILHead; variant-uniform forward)
- `src/data/i3d_dataset.py` — new I3DFeatureDataset class (5-crop train/test dispatch + filter + collapsed-ratio guard)
- `configs/rtfm_i3d.yaml` — new training config (dataset=xd_i3d, batch_size=3, Pitfall-3 mitigation)
- `tests/test_rtfm_i3d.py` — 9 unit tests covering R1–R7 + factory hygiene
- `tests/test_i3d_dataset.py` — 10 unit tests covering D1–D7 + defensive + smoke
- `src/models/registry.py` — added `_get_rtfm_i3d` + `MODEL_REGISTRY['rtfm_i3d']`
- `tests/test_registry.py` — renamed 4-key test to 5-key; updated valid-variants list in unknown-variant error assertion

## Decisions Made

- **MVP RTFMI3D (no MTN, no dilated temporal conv, no non-local block).** CONTEXT.md Discretion: "RTFM Feature Magnitude head implementation faithfulness — can simplify from RTFM Eq. 3–7 if the AP gate is met; MTN temporal module is NOT required (minimum viable reproduction is FM head + MIL ranking on I3D)." Shipping the MVP now lets Plan 06 check the ±1% gate empirically. If the gate fails, Phase 4b adds the MTN Aggregate module as a scoped fallback.
- **batch_size=3 in `rtfm_i3d.yaml` (Pitfall 3 Option A).** 5 crops × 3 videos = 15 effective samples per step; `k_topk=3` (Phase 3 D-01) gives the same 20% top-k ratio as the Phase 3 `batch_size=16` + `k_topk=3` skeleton/CLIP variants (3/16 ≈ 19%). Preserves the MIL ranking geometry. Documented in the YAML comment block as reversible if the gate passes empirically with a larger batch.
- **Named LN = `ln_i3d` (matches `ln_skel` / `ln_clip` / `ln_fused`).** Phase 5 TTA iterates `[n for n, m in model.named_modules() if isinstance(m, nn.LayerNorm)]` and enumerates all affine parameters. Keeping the naming convention consistent across all 5 variants means the TTA adapter loop written in Phase 5 works identically on rtfm_i3d checkpoints.
- **Deterministic RNG inside `_resample_T` for N<T case** (`np.random.default_rng(seed=0)`). Parallel to Phase 3 D-10-revised's choice of sample-with-replacement upsampling. Seed=0 is fixed per construction (not per call), giving within-video reproducibility; across-video variation comes from `np.linspace` partitioning which is deterministic. Cross-run reproducibility inherits from DataLoader worker seeding (Phase 3).
- **XD label parsing duplicated (not imported from `src.data.dataset`)** to preserve the Phase 4 D-07 module-boundary invariant: `src.data.i3d_dataset` and `src.data.dataset` are siblings but never import from each other. This keeps the training-path (`MILFeatureDataset`) module import graph free of the I3D code path, matching the Plan 02 rationale for keeping `src.eval.test_loader` isolated from `src.data.dataset`.
- **Missing-crop padding duplicates crop 0 (not crop `c-1`).** Simpler than most-recent-crop padding; gives deterministic pad source regardless of which crops are missing. At test time, `crops.mean(axis=0)` with 5 copies of crop 0 collapses to `crop_0` exactly — safe mean.
- **Collapsed-ratio warning writes to stderr, does NOT raise.** Paralleling Phase 4 D-40 (wandb auth failure mid-run logs + continues, CSV is source-of-truth). A training subprocess that hits a collapsed ratio will fail at MIL loss anyway; the stderr warning gives an actionable log line before that failure instead of hiding it behind a generic traceback.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Existing `test_registry_has_four_keys` hardcoded exactly 4 keys**

- **Found during:** Task 1 RED planning (acceptance criterion `pytest tests/test_registry.py tests/test_models.py -x exits 0`).
- **Issue:** The existing Phase 3 `tests/test_registry.py::test_registry_has_four_keys` asserts `set(MODEL_REGISTRY.keys()) == {"skeleton_only", "clip_only", "late_fusion", "gated_fusion"}`. Adding `rtfm_i3d` would make this assertion false. Without updating the test, Task 1's acceptance criterion "`pytest tests/test_registry.py tests/test_models.py -x exits 0`" would fail immediately after GREEN. The plan's `files_modified` list does not include `tests/test_registry.py` explicitly.
- **Fix:** Renamed `test_registry_has_four_keys` → `test_registry_has_five_keys` in place and added `rtfm_i3d` to both the expected-set assertion and the unknown-variant error-message check. Kept the test_id suffix meaningful (count-describing) so a future 6th variant will again fail loudly.
- **Files modified:** `tests/test_registry.py` (same-file edit; no new file).
- **Verification:** `pytest tests/test_registry.py tests/test_models.py -x` passes (37 green after Task 1 GREEN).
- **Committed in:** `edb6b99` (Task 1 RED) — folded into the RED commit because the updated test is a RED assertion that fails against the pre-GREEN registry (exactly the right TDD shape).

**2. [Rule 2 - Missing critical functionality] Pitfall-3 warning on all-abnormal set (not only all-normal)**

- **Found during:** Task 2 implementation.
- **Issue:** RESEARCH.md Pitfall 4 explicitly calls out the 729 missing XD train videos are all `_label_A` (normal) — collapsing the normal pool. The mirror case is theoretically possible in a pathological filter of synthetic fixtures (tests) or a future extraction bug that drops all normal videos. MIL bag pairing requires BOTH classes; a collapsed-abnormal case would break training just as severely.
- **Fix:** Added symmetric stderr warning for `n_normal == 0` alongside the `n_abnormal == 0` case. Mirror test `test_all_abnormal_warns_on_stderr` verifies the symmetric path. No production impact (XD never hits this case), but lockout coverage protects against future regressions.
- **Files modified:** `src/data/i3d_dataset.py`, `tests/test_i3d_dataset.py`
- **Verification:** Both `test_all_normal_warns_on_stderr` and `test_all_abnormal_warns_on_stderr` green.
- **Committed in:** `a8db06f` (Task 2 GREEN commit).

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing-functionality).
**Impact on plan:** Both fixes are pure invariant tightening — no scope change, no new surface, no deferred work. All plan acceptance criteria met (all 15+ `grep -c` targets verified, all specified test commands exit 0).

## Threat Mitigations Applied

| Threat ID | Mitigation Implemented | Evidence |
|-----------|------------------------|----------|
| T-04-03-01 (EoP via untrusted `.npy`) | `np.load` called with default `allow_pickle=False` | `src/data/i3d_dataset.py::_load_crops` does not pass `allow_pickle=True`; Python object deserialization disabled. |
| T-04-03-02 (Tampering via `yaml.load`) | `test_yaml_schema` uses `yaml.safe_load` | `tests/test_i3d_dataset.py::test_yaml_schema` calls `yaml.safe_load` directly; no `yaml.load` anywhere in Task 2 code. |
| T-04-03-03 (DoS via malformed `.npy` mid-epoch) | Accept per plan; pre-flight `_has_at_least_one_crop` filters missing crops, corrupted mid-epoch fails loudly | Plan threat_model explicit accept-disposition; `_load_crops` raises `FileNotFoundError` if crop 0 vanishes at run time. |
| T-04-03-04 (Info disclosure via run_dir) | Accept per plan (local filesystem, researcher owns run dir) | Plan threat_model explicit accept-disposition. |

## Known Stubs

None. Plan 02's Known Stubs list included three items; Plan 03 retires one of them (`xd_i3d` ImportError pointer in `test_loader.py`) by satisfying the `from src.data.i3d_dataset import I3DFeatureDataset` contract. The other two (xd_i3d label construction in `src/evaluate.py` and val-path MIL loss stub) remain Plan 02's responsibility and are not touched here.

## Issues Encountered

- **Pre-existing dataset.py modifications unrelated to Plan 03** (`src/data/dataset.py`, `scripts/extract_*.py`, `CLAUDE.md`). These appeared in `git status -- modified` at plan start but belong to Plan 04-04 (skel_agg extension — see commit `49d8da0` which was created in parallel on another worktree). Plan 03 touched none of these; they remain unmodified in the working tree. No conflict — Plan 03's files are disjoint from Plan 04-04's.

No other issues encountered.

## Open Question for Plan 06

If the RTFM gate fails the ±1% threshold on `rtfm_i3d` (77.81% ± 1% = 76.81%–78.81% XD AP) at `batch_size=3`, the fallback triage:
1. First, try raising `batch_size` to 16 (Pitfall 3 Option C). A passing gate at 16 invalidates the Pitfall-3 warning without code change.
2. If (1) still fails, add Option B (crop averaging at train time too) — one-line dataset change.
3. Last resort: add MTN Aggregate module from the RTFM paper. This is Phase 4b scope per CONTEXT.md Discretion, not Plan 06 in-scope.

Plan 06 owns this triage decision point.

## User Setup Required

None — no external service configuration required for this plan. (wandb configuration is Plan 04-05's `wandb_preflight.py` gate; RTFM training itself runs in Plan 04-06.)

## Next Phase Readiness

- **Plan 04-04 already in progress on a parallel worktree** (`49d8da0 feat(04-04): add --keep-persons + --pool flags + skel_agg loader branch`). Plan 03's additions are disjoint; no merge conflict expected.
- **Plan 04-05 ready to start.** `scripts/run_ablations.py` can queue `RunSpec(dataset="xd_i3d", variant="rtfm_i3d", seed=42, config="configs/rtfm_i3d.yaml")` as the first (gate) run in the `rtfm_gate` queue. `configs/rtfm_i3d.yaml` is complete and imports through both `yaml.safe_load` and the Dataset dispatch.
- **Plan 04-06 (empirical execution) ready to gate on RTFM.** Training subprocess launches `src/train.py --config configs/rtfm_i3d.yaml` which will invoke `build_test_dataset` → `I3DFeatureDataset(mode="test", ...)` at eval time. The 5-crop bag expansion in train mode feeds directly through `RTFMI3D.forward(i3d=...)` → `MILHead` → top-k MIL ranking loss.
- **Phase 5 TTA inherits ln_i3d naming convention.** When Phase 5 reads `results/xd_rtfm_i3d_s42/best_model.pth` (D-30 naming from Plan 04-05), the LN-affine iteration will pick up `ln_i3d` automatically via the existing `named_modules()` enumeration, identical to how it picks up `ln_skel` / `ln_clip` / `ln_fused` on gated_fusion checkpoints.
- **No blockers.**

## Self-Check: PASSED

- [x] `src/models/rtfm_i3d.py` exists with `class RTFMI3D` + `self.ln_i3d = nn.LayerNorm` + `def forward`
- [x] `src/models/registry.py` contains `rtfm_i3d` (3 occurrences) + `_get_rtfm_i3d` (2 occurrences: definition + dict entry)
- [x] `src/data/i3d_dataset.py` contains `class I3DFeatureDataset` + `def _load_crops` + `def _resample_T` + `mode == "test"` + n_crops loop + `normal/abnormal`
- [x] `configs/rtfm_i3d.yaml` exists + contains `dataset: xd_i3d` + `variant: rtfm_i3d` + `i3d_features` + `batch_size: 3`
- [x] `tests/test_rtfm_i3d.py` contains `test_forward_shape`, `test_named_ln_present`, `ln_i3d`
- [x] `tests/test_i3d_dataset.py` contains `test_test_mode_shape`, `test_train_mode_shape`, `test_missing_crops`, `test_yaml_schema`
- [x] Commit `edb6b99` exists (Task 1 RED)
- [x] Commit `ebf4ca6` exists (Task 1 GREEN)
- [x] Commit `3c46b62` exists (Task 2 RED)
- [x] Commit `a8db06f` exists (Task 2 GREEN)
- [x] `pytest tests/test_rtfm_i3d.py tests/test_i3d_dataset.py -x` → 18 passed
- [x] `pytest tests/test_rtfm_i3d.py tests/test_i3d_dataset.py tests/test_registry.py tests/test_models.py -x` → 47 passed
- [x] Full non-train-e2e regression (21 safe test files): 151 passed
- [x] Manual: `yaml.safe_load(open('configs/rtfm_i3d.yaml'))` → `dataset='xd_i3d', variant='rtfm_i3d'`
- [x] Manual: `build_model(variant='rtfm_i3d', i3d_dim=1024).named_modules()` exposes `['ln_i3d']`

---
*Phase: 04-baseline-evaluation-main-results*
*Completed: 2026-04-15*
