---
phase: 08-siglip2-backbone-comparison
plan: 02
subsystem: config, testing, orchestration
tags: [siglip2, yaml, ablation-queue, clip_dim, backbone-comparison]

# Dependency graph
requires:
  - phase: 04-ucf-evaluation
    provides: RunSpec queue pattern, existing YAML config structure, model constructors with clip_dim parameter
  - phase: 04c-xd-evaluation
    provides: XD-Violence configs and queue patterns
provides:
  - 10 SigLIP2 YAML configs (8 at clip_dim=3072, 2 at clip_dim=1536)
  - 6 Phase 8 ablation queues with 14 RunSpecs in run_ablations.py
  - Model dimension tests confirming CLIPProj, GatedFusion, LateFusion accept clip_dim=3072
affects: [08-03-siglip2-extraction, 08-04-siglip2-ablation-execution]

# Tech tracking
tech-stack:
  added: []
  patterns: [config-only-backbone-swap, phase-scoped-queue-naming]

key-files:
  created:
    - configs/clip_only_siglip2.yaml
    - configs/clip_only_xd_siglip2.yaml
    - configs/late_fusion_siglip2.yaml
    - configs/late_fusion_xd_siglip2.yaml
    - configs/gated_fusion_siglip2.yaml
    - configs/gated_fusion_xd_siglip2.yaml
    - configs/gated_fusion_siglip2_2person.yaml
    - configs/gated_fusion_xd_siglip2_2person.yaml
    - configs/gated_fusion_siglip2_clip_mean.yaml
    - configs/gated_fusion_xd_siglip2_clip_mean.yaml
  modified:
    - scripts/run_ablations.py
    - tests/test_models.py
    - tests/test_run_ablations.py

key-decisions:
  - "clip_mean SigLIP2 configs use clip_dim=1536 (mean-only), all others use clip_dim=3072 (mean+max)"
  - "Phase 8 queues skip skeleton_only -- skeleton features are backbone-independent"
  - "cache_variant field distinguishes siglip2 runs from CLIP runs in results-index.csv"

patterns-established:
  - "Config-only backbone swap: new backbone = new YAML with clip_dim + clip_features path changes, zero model code changes"
  - "Phase-scoped queue naming: phase8_{dataset}_{purpose} groups related ablation runs"

requirements-completed: [EVAL-02, EVAL-03, EVAL-04]

# Metrics
duration: 7min
completed: 2026-05-19
---

# Phase 8 Plan 02: SigLIP2 Config and Queue Infrastructure Summary

**10 SigLIP2 YAML configs with clip_dim=3072/1536 and 6 Phase 8 ablation queues (14 RunSpecs) ready for immediate execution after feature extraction**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-19T00:24:07Z
- **Completed:** 2026-05-19T00:31:27Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Created 10 SigLIP2 YAML configs mirroring all CLIP variants (clip_only, late_fusion, gated_fusion, 2person, clip_mean) for both UCF-Crime and XD-Violence
- Added 6 Phase 8 queues to run_ablations.py with 14 total RunSpecs covering main ablation (3+3), pooling (2+2), and seed stability (2+2)
- Verified CLIPProj, GatedFusion, and LateFusion all accept clip_dim=3072 via forward pass tests (4 new tests, all passing)
- Full test suite passes: 47 tests in test_models.py + test_run_ablations.py, zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 10 SigLIP2 YAML configs** - `e11afe5` (feat)
2. **Task 2: Add Phase 8 queues and clip_dim=3072 model tests** - `a3b154b` (feat)

## Files Created/Modified
- `configs/clip_only_siglip2.yaml` - UCF CLIP-Only with SigLIP2 features (clip_dim=3072)
- `configs/clip_only_xd_siglip2.yaml` - XD CLIP-Only with SigLIP2 features (clip_dim=3072)
- `configs/late_fusion_siglip2.yaml` - UCF Late Fusion with SigLIP2 features (clip_dim=3072)
- `configs/late_fusion_xd_siglip2.yaml` - XD Late Fusion with SigLIP2 features (clip_dim=3072)
- `configs/gated_fusion_siglip2.yaml` - UCF Gated Fusion with SigLIP2 features (clip_dim=3072)
- `configs/gated_fusion_xd_siglip2.yaml` - XD Gated Fusion with SigLIP2 features (clip_dim=3072)
- `configs/gated_fusion_siglip2_2person.yaml` - UCF 2-person ablation with SigLIP2 (clip_dim=3072, skel_dim=512)
- `configs/gated_fusion_xd_siglip2_2person.yaml` - XD 2-person ablation with SigLIP2 (clip_dim=3072, skel_dim=512)
- `configs/gated_fusion_siglip2_clip_mean.yaml` - UCF mean-only pooling with SigLIP2 (clip_dim=1536)
- `configs/gated_fusion_xd_siglip2_clip_mean.yaml` - XD mean-only pooling with SigLIP2 (clip_dim=1536)
- `scripts/run_ablations.py` - Added 6 Phase 8 queue definitions (14 RunSpecs)
- `tests/test_models.py` - Added 4 new tests: test_clip_dim_3072, test_clip_dim_3072_projection_layer, test_late_fusion_clip_dim_3072, test_gated_fusion_clip_dim_3072
- `tests/test_run_ablations.py` - Added Phase 8 queue assertions, updated total unique run_names from 224 to 238

## Decisions Made
- clip_mean SigLIP2 variants use clip_dim=1536 (not 3072) because mean-only SigLIP2 embedding is 1536-d (encode_image output) vs mean+max which doubles to 3072-d
- Phase 8 queues do not include skeleton_only because skeleton features are backbone-independent (no visual features used)
- cache_variant="siglip2" (and "siglip2_2person", "siglip2_clip_mean") distinguishes SigLIP2 runs in results-index.csv and run_name format

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 10 SigLIP2 configs are ready for training as soon as SigLIP2 features are extracted (Plan 03)
- All 6 queues are registered in run_ablations.py and accessible via --queue CLI
- Model dimension compatibility verified: CLIPProj(3072->512), GatedFusion(3072->256), LateFusion(3072->512) all produce correct output shapes

---
*Phase: 08-siglip2-backbone-comparison*
*Completed: 2026-05-19*
