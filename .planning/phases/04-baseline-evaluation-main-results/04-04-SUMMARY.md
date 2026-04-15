---
phase: 04-baseline-evaluation-main-results
plan: 04
subsystem: data-plumbing
tags: [pooling-ablation, skel-agg, keep-persons, clip-mean, multi-person, d-21, d-22, d-23, d-24, d-37, tdd, argparse, yaml-config]

# Dependency graph
requires:
  - phase: 04-baseline-evaluation-main-results
    plan: 01
    provides: "tests/fixtures/synthetic + tests/conftest.py fixtures — reused for tmp_path-driven 2-person cache fixtures; no direct import, mirrored pattern"
  - phase: 04-baseline-evaluation-main-results
    plan: 02
    provides: "_construct_mil_dataset kwarg-filter plumbing in src/evaluate.py — picks up skel_agg automatically once MILFeatureDataset accepts it (no edit required in evaluate.py this plan)"
  - phase: 03-model-architecture-training-infrastructure
    provides: "MILFeatureDataset class at src/data/dataset.py (extended with skel_agg); gated_fusion variant accepts configurable skel_dim (512 for concat, 256 for mean/max); scripts/extract_ctrgcn.py + scripts/extract_clip.py baselines"
  - phase: 02-feature-extraction-pipeline
    provides: "skeleton/ + clip/ baseline caches at E:/features/ucf/ (1728 videos each, [N,256] and [N,1024] respectively); boundary JSON contract reused verbatim by the new keep-persons path"
provides:
  - "scripts/extract_ctrgcn.py --keep-persons flag producing [N, 2, 256] per-video tensors to E:/features/<dataset>/skeleton_2person/"
  - "scripts/extract_clip.py --pool={mean|mean_max} flag producing [N, 512] (mean) or [N, 1024] (mean_max) to E:/features/<dataset>/clip_mean|clip/"
  - "MILFeatureDataset(skel_agg='concat'|'max'|'mean'|'none') — 3D cache reshape at load time with Pitfall 7 mitigation (ValueError when skel_agg='none' on 3D cache)"
  - "configs/gated_fusion_2person.yaml (D-22: 2-person concat ablation, skel_dim=512, skel_agg=concat)"
  - "configs/gated_fusion_clip_mean.yaml (D-23: CLIP mean-only ablation, clip_dim=512)"
  - "scripts/verify_pooling_caches.py — per-video sanity verifier for both new caches (shape axiom + allclose for clip_mean, shape axiom for skeleton_2person)"
  - "tests/test_skel_agg.py (8 tests) + tests/test_verify_pooling.py (8 tests)"
affects:
  - "04-05 (scripts/run_ablations.py: 3 new (variant, cache_variant) tuples now orchestrable — gated_fusion on 2-person cache, gated_fusion on clip_mean cache; wandb tag logic uses 2person/clip_mean keys per D-41)"
  - "04-06 (empirical run: Plan 06 invokes the two new scripts at full UCF scale — long-running jobs — and then runs the 2-pooling-ablation rows; gates on verify_pooling_caches.py passing before training)"
  - "04-07 (SUMMARY / UAT: reports pooling-ablation AUC deltas against gated_fusion baseline)"
  - "04b (XD-Violence main results): all 3 artifacts (extractors + loader + configs + verifier) are dataset-portable via --dataset=xd + paths.skeleton_features/clip_features; Phase 4b activates once XD base caches land"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-mode extractor with flag-branching output dir (D-24 sibling dir pattern) + flag-branching shape validation at save time"
    - "Dataset loader supports polymorphic cache rank (2D or 3D) with aggregation config carrying the reshape decision; ValueError when config is underspecified for cache rank"
    - "Dataclass-driven sanity verifier (VideoResult pass/fail/skip) mirrored from scripts/verify_alignment.py; exit codes separating per-video FAIL (1) from setup errors (2)"
    - "TDD RED-GREEN per-task: commit RED tests first, watch them fail on the expected predicate, then GREEN implementation flips all assertions"
    - "Test candidate iterator with ModuleNotFoundError filtering — base-env anaconda python can find the script but fail on its imports; subprocess-based CLI tests must detect and skip that case to remain portable across pytest contexts"

key-files:
  created:
    - "configs/gated_fusion_2person.yaml"
    - "configs/gated_fusion_clip_mean.yaml"
    - "scripts/verify_pooling_caches.py"
    - "tests/test_skel_agg.py"
    - "tests/test_verify_pooling.py"
  modified:
    - "scripts/extract_ctrgcn.py"
    - "scripts/extract_clip.py"
    - "src/data/dataset.py"

key-decisions:
  - "D-21 implemented: skeleton_2person cache stored as [N, 2, 256] single npy per video; aggregation happens at MILFeatureDataset load time via cfg.data.skel_agg, not at extraction time. The cache itself is aggregation-agnostic — switching concat↔max↔mean does not require re-extraction."
  - "D-22 implemented: gated_fusion_2person.yaml binds skel_agg=concat and skel_dim=512. Phase 4 runs the concat path only; max and mean are tracked as deferred ideas per the plan spec."
  - "D-23 implemented: --pool={mean|mean_max} flag with mean_max default preserves backward compatibility; mean path writes [N,512] to clip_mean/ sibling dir."
  - "D-24 implemented: sibling-directory layout at E:/features/<dataset>/<skeleton|skeleton_2person|clip|clip_mean>/. YAML paths.skeleton_features / paths.clip_features select per-config; the data loader stays directory-agnostic."
  - "D-37 implemented: MODEL_REGISTRY gains no new key — gated_fusion serves all 3 pooling configs (baseline + 2person + clip_mean) through different paths + dim configs; only rtfm_i3d (04-03) adds a new key."
  - "Pitfall 7 mitigation: Dataset __init__ validates skel_agg ∈ {none, concat, max, mean} with ValueError; __getitem__ raises ValueError when a 3D cache is loaded with skel_agg='none' rather than silently forwarding a 3D tensor to Linear layers (which would fail further downstream with a cryptic broadcast error)."
  - "CLI test robustness: sys.executable as first candidate + ModuleNotFoundError filtering. Base-anaconda python exists on PATH and can find the script, but lacks torch — without the filter the tests fall through to that candidate and fail mysteriously. Runtime also dropped 51s → 8s on the skel_agg test module."
  - "extract_stream_feature keeps legacy [1, 256] output by default (`out.mean(dim=[1, 3, 4])`); keep_persons branch pools only T'/V' to yield [M=2, 256]. No behavior change on the default code path that Phase 2/3 callers hit."
  - "Per-snippet stacking uses torch.stack in keep_persons mode (yields [N_snippets, 2, 256]) vs torch.cat in legacy mode (yields [N_snippets, 256]). Each mode's output shape is asserted at np.save time plus at validate_sample_outputs time."
  - "Default behavior of MILFeatureDataset is UNCHANGED: skel_agg='none' + 2D cache = original Phase 3 behavior. All 119 pre-existing tests (test_dataset + test_models + test_mil_*) continue to pass without modification."

patterns-established:
  - "Pattern: flag-branching extractor with output-dir branch. Runtime axioms: (1) default flag path is identical to pre-flag behavior at the bit level; (2) output dir carries the mode (skeleton/ vs skeleton_2person/) so a single disk layout supports both; (3) shape asserts at save time prevent silent rank regressions."
  - "Pattern: polymorphic cache rank with load-time aggregation. Cache stores the most-disaggregated form ([N, 2, 256]), and config-driven reshape at __getitem__ chooses the downstream dim. Avoids a combinatorial explosion of cache variants (concat cache + mean cache + max cache = 3 copies at ~1.5 MB × 1728 = 7.8 GB)."
  - "Pattern: sanity verifier = dataclass per unit + main CLI iteration + PASS/FAIL/SKIP tally + return code. Applies to any 'new cache matches old cache' verification; mirrored from scripts/verify_alignment.py."
  - "Pattern: subprocess-based CLI test with candidate iterator + ModuleNotFoundError filter. Portable across pytest-in-vcc-main, pytest-in-vcc-ctrgcn, and pytest-with-PATH-default-python contexts."

requirements-completed:
  - EVAL-03

# Metrics
duration: 20min
completed: 2026-04-15
---

# Phase 4 Plan 04: Pooling ablation plumbing Summary

**Ships --keep-persons / --pool extractor flags (D-21/D-23), MILFeatureDataset.skel_agg 3D→2D reshape (D-22/D-37 + Pitfall 7 mitigation), 2 new YAML configs (gated_fusion_2person.yaml + gated_fusion_clip_mean.yaml), and scripts/verify_pooling_caches.py sanity verifier. 16 new tests green; 118-test broader suite green with zero regressions. Default Phase 2/3 code paths untouched.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-04-15T10:31:59Z
- **Completed:** 2026-04-15T10:51:57Z
- **Tasks:** 2 (each with TDD RED + GREEN)
- **Files changed:** 8 (5 created, 3 modified)

## Accomplishments

- **Phase 4 D-21 cache format + D-22 aggregation contract:** `scripts/extract_ctrgcn.py --keep-persons` yields `[N, 2, 256]` float32 npy to `E:/features/<dataset>/skeleton_2person/`. M-pool collapse (`out.mean(dim=[1, 3, 4])`) becomes spatial-only pool (`out.mean(dim=[3, 4]).squeeze(0)`) under the flag, preserving the per-person dim. Per-snippet accumulator switches from `torch.cat` to `torch.stack` in keep-persons mode. Default behavior untouched.
- **Phase 4 D-23 CLIP pooling contract:** `scripts/extract_clip.py --pool={mean|mean_max}` with `mean_max` default preserves the Phase 2 D-06 baseline. The `mean` mode emits `[N, 512]` to `clip_mean/` sibling dir; the `mean_max` mode is the legacy `torch.cat([mean_feat, max_feat])` path producing `[N, 1024]` to `clip/`. `extract_clip_snippet` branches on pool, and the zero-fallback respects the chosen dim (no silent 1024-d write in mean mode).
- **D-21 + Pitfall 7 loader plumbing:** `MILFeatureDataset(skel_agg='concat'|'max'|'mean'|'none')`. `__init__` validates the string (ValueError on typo); `__getitem__` detects `skel.ndim == 3 and shape[1] == 2` and dispatches per skel_agg: `concat` → `reshape(N, 512)`, `max` → `max(axis=1)` → `(N, 256)`, `mean` → `mean(axis=1)` → `(N, 256)`. When skel_agg='none' on a 3D cache, raises a descriptive ValueError mentioning video_id and skel_agg — the Pitfall 7 mitigation against silently feeding a 3D tensor to `nn.Linear`.
- **2-person concat ablation YAML (D-22):** `configs/gated_fusion_2person.yaml` rebinds `paths.skeleton_features=E:/features/ucf/skeleton_2person`, sets `model.skel_dim=512` and `data.skel_agg=concat`, and tags wandb runs with `[phase4, gated_fusion, ucf, 2person]`. CLIP side uses the default 1024-d cache.
- **CLIP mean-only ablation YAML (D-23):** `configs/gated_fusion_clip_mean.yaml` rebinds `paths.clip_features=E:/features/ucf/clip_mean`, sets `model.clip_dim=512` and omits `data.skel_agg` (defaults to `none` since skeleton side stays on the 2D M-pool cache). Wandb tags `[phase4, gated_fusion, ucf, clip_mean]`.
- **Sanity verifier (scripts/verify_pooling_caches.py):** Dataclass-driven `VideoResult` (mirrored from `verify_alignment.py`). Axioms: `clip_mean[vid].shape == (N, 512)` AND `np.allclose(clip_mean[vid], clip[vid][:, :512], atol=1e-5)` when baseline exists; `skeleton_2person[vid].shape == (N, 2, 256)` AND N matches baseline. CLI with `--dataset`, `--cache {clip_mean|skeleton_2person}`, `--cache-root`, `--baseline-root`, `--limit`. Exit 0 on all-pass, 1 on any fail, 2 on setup errors.
- **TDD discipline:** 16 new tests (8 in test_skel_agg.py + 8 in test_verify_pooling.py). Each task committed RED (failing tests) before GREEN (implementation). The skel_agg CLI-subprocess tests (S7/S8) were hardened with `sys.executable` as the first candidate and a `ModuleNotFoundError` filter to survive pytest contexts where `shutil.which('python')` resolves to base anaconda (no torch). Runtime dropped 51s → 8s.

## Task Commits

4 commits (RED → GREEN for each task):

1. **Task 1 RED** — `207a124` (test): failing skel_agg + extractor CLI tests; 8 tests expected to fail until MILFeatureDataset accepts skel_agg and the extractors gain their flags.
2. **Task 1 GREEN** — `49d8da0` (feat): `--keep-persons` + `--pool` flags + skel_agg loader branch. 3 files modified: scripts/extract_ctrgcn.py, scripts/extract_clip.py, src/data/dataset.py. 119 broader-suite tests green.
3. **Task 2 RED** — `83b495d` (test): failing verify_pooling + YAML schema tests; 8 tests expected to fail until configs/*.yaml and scripts/verify_pooling_caches.py exist.
4. **Task 2 GREEN** — `54f32b1` (feat): 2 YAML configs + verify_pooling_caches.py + test hardening. 4 files: configs/gated_fusion_2person.yaml, configs/gated_fusion_clip_mean.yaml, scripts/verify_pooling_caches.py, tests/test_skel_agg.py (CLI test robustness patch).

## Files Created/Modified

### Created

| Path | Purpose |
| ---- | ------- |
| `configs/gated_fusion_2person.yaml` | D-22: 2-person concat ablation — skel_dim=512, skel_agg=concat, paths.skeleton_features=skeleton_2person |
| `configs/gated_fusion_clip_mean.yaml` | D-23: CLIP mean-only ablation — clip_dim=512, paths.clip_features=clip_mean |
| `scripts/verify_pooling_caches.py` | Per-video axiom verifier with dataclass VideoResult + CLI + exit codes |
| `tests/test_skel_agg.py` | 8 tests: 6 skel_agg branch tests + 2 extractor CLI --help smoke tests |
| `tests/test_verify_pooling.py` | 8 tests: 2 YAML schema + 6 verifier behavior (PASS / FAIL / shape-mismatch / allclose-fail / bad-rank) |

### Modified

| Path | Change |
| ---- | ------ |
| `scripts/extract_ctrgcn.py` | +--keep-persons flag; extract_stream_feature accepts keep_persons kwarg; extract_video_features propagates keep_persons; torch.stack vs torch.cat accumulator branch; output dir branches skeleton_2person/ vs skeleton/; shape asserts at save + validate_sample_outputs |
| `scripts/extract_clip.py` | +--pool={mean,mean_max} flag (default mean_max); extract_clip_snippet + extract_video_clip_features accept pool kwarg; output dir branches clip_mean/ vs clip/; expected_dim (512 or 1024) drives all shape asserts |
| `src/data/dataset.py` | MILFeatureDataset.__init__ gains skel_agg param with ValueError validation; __getitem__ detects 3D cache and reshapes per skel_agg; ValueError on skel_agg='none' + 3D cache (Pitfall 7 mitigation) |

## Acceptance Criteria

Task 1 (from plan `<acceptance_criteria>`):
- [x] `grep -q '\-\-keep-persons' scripts/extract_ctrgcn.py` — present in argparse + extract_stream_feature docstring + run_extraction logger
- [x] `grep -q 'keep_persons' scripts/extract_ctrgcn.py` — 34 occurrences (kwarg-propagation through 3 functions)
- [x] `grep -q 'skeleton_2person' scripts/extract_ctrgcn.py` — output dir branch
- [x] `grep -q 'out.mean(dim=\[3, 4\])' scripts/extract_ctrgcn.py` — the per-person pool (spatial-only)
- [x] `grep -q '\-\-pool' scripts/extract_clip.py` — argparse + branching code
- [x] `grep -q 'clip_mean' scripts/extract_clip.py` — output dir branch
- [x] `grep -q 'choices=\["mean", "mean_max"\]' scripts/extract_clip.py` — argparse constraint
- [x] `grep -q 'skel_agg' src/data/dataset.py` — 10 occurrences in __init__ + __getitem__
- [x] `grep -q 'skel_agg must be none' src/data/dataset.py` — ValueError message
- [x] `grep -q 'skel.ndim == 3' src/data/dataset.py` — 3D cache detection
- [x] `grep -q 'def test_concat_to_512' tests/test_skel_agg.py`
- [x] `grep -q 'def test_none_on_3d_raises' tests/test_skel_agg.py`
- [x] `grep -q 'def test_backward_compat_2d_cache' tests/test_skel_agg.py`
- [x] `pytest tests/test_skel_agg.py tests/test_dataset.py -x` exits 0 (18/18 pass)

Task 2 (from plan `<acceptance_criteria>`):
- [x] `test -f configs/gated_fusion_2person.yaml` — exists
- [x] `grep -q 'skel_agg: concat' configs/gated_fusion_2person.yaml`
- [x] `grep -q 'skel_dim: 512' configs/gated_fusion_2person.yaml`
- [x] `grep -q 'skeleton_2person' configs/gated_fusion_2person.yaml` — paths + wandb tag
- [x] `test -f configs/gated_fusion_clip_mean.yaml`
- [x] `grep -q 'clip_mean' configs/gated_fusion_clip_mean.yaml` — paths + wandb tag
- [x] `grep -q 'clip_dim: 512' configs/gated_fusion_clip_mean.yaml`
- [x] `test -f scripts/verify_pooling_caches.py`
- [x] `grep -q 'def verify_clip_mean' scripts/verify_pooling_caches.py`
- [x] `grep -q 'def verify_skeleton_2person' scripts/verify_pooling_caches.py`
- [x] `grep -q 'allclose' scripts/verify_pooling_caches.py`
- [x] `grep -q 'np.load' scripts/verify_pooling_caches.py`
- [x] `grep -q 'def test_config_2person_schema' tests/test_verify_pooling.py`
- [x] `grep -q 'def test_verify_pooling_clip_mean_pass' tests/test_verify_pooling.py`
- [x] `grep -q 'def test_verify_pooling_clip_mean_detects_mismatch' tests/test_verify_pooling.py`
- [x] `pytest tests/test_verify_pooling.py -x` exits 0 (8/8 pass)

## Test Results

- `tests/test_skel_agg.py` — 8/8 pass (concat/mean/max/none-raises/invalid-raises/2D-backcompat/extract_ctrgcn-help/extract_clip-help)
- `tests/test_verify_pooling.py` — 8/8 pass (Y1/Y2 YAML schemas + V1-V6 verifier behaviors)
- `tests/test_dataset.py` — 10/10 pass (no regressions from Phase 3 dataset semantics)
- Broader regression: `test_skel_agg + test_verify_pooling + test_dataset + test_models + test_mil_head + test_mil_loss + test_eval_metrics + test_evaluate_cli + test_test_loader + test_config + test_config_hash + test_snippet_to_frame + test_ucf_annotations` — **118 passed in 67.68s**; 2 pre-existing sklearn warnings from test_eval_metrics (unrelated).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CLI subprocess tests brittle under pytest contexts**

- **Found during:** Task 2 GREEN verification — the skel_agg CLI tests (S7/S8) intermittently failed when the full test suite was run, despite passing when run on the skel_agg module alone.
- **Issue:** `shutil.which('python')` in the test's candidate list resolved to `C:/Anaconda/python.EXE` (base anaconda, no torch). When an earlier candidate (`vcc-main`) somehow produced empty output under resource pressure from adjacent test modules, the loop fell through to the broken python and the test's assertion saw a `ModuleNotFoundError: No module named 'torch'` traceback. The test then asserted `'--keep-persons' in traceback_text`, which (correctly) failed — but the failure was misleading because the extractor itself was fine.
- **Fix:** Refactored the candidate loop into a `_run_help()` helper that (a) uses `sys.executable` as the first candidate (guaranteed to be the running pytest's env — has torch), and (b) filters out candidates that print `'modulenotfounderror'` in their combined output. Runtime also dropped 51s → 8s because `sys.executable` succeeds immediately.
- **Files modified:** `tests/test_skel_agg.py`
- **Commit:** `54f32b1` (bundled with Task 2 GREEN)

### Rules 2/3/4
No other deviations. No architectural questions arose. No missing critical functionality. Default Phase 2/3 code paths preserved (zero regressions across 118 broader-suite tests).

## Authentication Gates
None encountered. No external services touched; no credentials needed.

## Known Stubs
None. All plan behaviors implemented to spec. Scope note from the plan is honored: this plan delivers the CODE; actual re-extraction at full UCF scale is Plan 04-06's empirical-execution deliverable — that is the intended scope split, not a stub.

## Threat Flags
None. The two new network/filesystem touchpoints (the `--keep-persons` / `--pool` output dirs) are inside the existing `E:/features/<dataset>/` trust boundary already established by Phase 2. No new auth path, no new schema at a trust boundary, no new external service.

## Self-Check: PASSED

All 4 task commits exist in git log:
- `207a124` test(04-04): add failing skel_agg + extractor CLI tests — **FOUND**
- `49d8da0` feat(04-04): add --keep-persons + --pool flags + skel_agg loader branch — **FOUND**
- `83b495d` test(04-04): add failing verify_pooling + YAML schema tests — **FOUND**
- `54f32b1` feat(04-04): add pooling-ablation YAML configs + verify_pooling_caches.py — **FOUND**

All 5 created files exist on disk:
- `configs/gated_fusion_2person.yaml` — **FOUND**
- `configs/gated_fusion_clip_mean.yaml` — **FOUND**
- `scripts/verify_pooling_caches.py` — **FOUND**
- `tests/test_skel_agg.py` — **FOUND**
- `tests/test_verify_pooling.py` — **FOUND**

All 3 modified files reflect the plan contract:
- `scripts/extract_ctrgcn.py` — `--keep-persons` in argparse; `keep_persons` propagates through 3 functions; `out.mean(dim=[3, 4]).squeeze(0)` branch present; `skeleton_2person` output dir branch
- `scripts/extract_clip.py` — `--pool` in argparse with `{mean, mean_max}` choices; `clip_mean` output dir branch; `expected_dim` shape assert
- `src/data/dataset.py` — `skel_agg` param in `__init__` with ValueError validation; 3D cache detection + reshape in `__getitem__` with Pitfall 7 mitigation

Test counts:
- `tests/test_skel_agg.py` — 8 tests, 8 pass
- `tests/test_verify_pooling.py` — 8 tests, 8 pass
- `tests/test_dataset.py` — 10 tests, 10 pass (no regressions)
- Broader suite (13 modules) — 118 tests pass, 0 fail
