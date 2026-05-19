---
phase: "08-siglip2-backbone-comparison"
plan: "01"
subsystem: "feature-extraction"
tags: [siglip2, backbone, extraction, parameterization]
dependency_graph:
  requires: []
  provides: [BACKBONE_CONFIGS, load_vision_model, "--backbone CLI flag"]
  affects: [scripts/extract_clip.py, tests/test_extract_siglip2.py]
tech_stack:
  added: []
  patterns: [backbone-registry, parameterized-dimension, backbone-aware-subdir]
key_files:
  created:
    - tests/test_extract_siglip2.py
  modified:
    - scripts/extract_clip.py
decisions:
  - "BACKBONE_CONFIGS dict at module level with 2 entries (clip-vit-b-16, siglip2-giant)"
  - "load_vision_model replaces load_clip_model, returns (model, preprocess, cfg) 3-tuple"
  - "All dimension assertions parameterized via embed_dim from config (no hardcoded 512/1024)"
  - "Output subdirs: siglip2/ and siglip2_mean/ for SigLIP2 features"
metrics:
  duration_seconds: 687
  completed: "2026-05-19T00:28:22Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 08 Plan 01: Backbone-Parameterized Extraction Summary

BACKBONE_CONFIGS registry with CLIP ViT-B/16 (512-d) and SigLIP2 Giant (1536-d) entries, --backbone CLI flag, parameterized dimension assertions, and backbone-aware output subdirectory routing in extract_clip.py.

## Task Completion

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add BACKBONE_CONFIGS registry and --backbone CLI flag | a6e409d | scripts/extract_clip.py |
| 2 | Create test_extract_siglip2.py with 7 tests | 9490cb5 | tests/test_extract_siglip2.py |

## What Changed

### scripts/extract_clip.py (modified)

- Added `BACKBONE_CONFIGS` module-level dict with two entries:
  - `clip-vit-b-16`: model_name=ViT-B-16, pretrained=openai, embed_dim=512, output_subdir=clip, mean_subdir=clip_mean
  - `siglip2-giant`: model_name=ViT-gopt-16-SigLIP2-384, pretrained=webli, embed_dim=1536, output_subdir=siglip2, mean_subdir=siglip2_mean
- Replaced `load_clip_model()` with `load_vision_model(backbone, device)` returning (model, preprocess, cfg) 3-tuple
- Added `embed_dim` parameter to `extract_clip_snippet()`, `extract_video_clip_features()`, and threaded through `run_extraction()`
- Replaced all three hardcoded dimension assertions (`512 if pool == "mean" else 1024`) with `embed_dim if pool == "mean" else embed_dim * 2`
- Updated output subdir selection to use `cfg["output_subdir"]` and `cfg["mean_subdir"]` instead of hardcoded "clip"/"clip_mean"
- Added `--backbone` argparse argument with choices=["clip-vit-b-16", "siglip2-giant"], default="clip-vit-b-16"
- Updated `validate_sample_outputs()` to accept backbone parameter for proper dimension validation
- Updated module docstring to document SigLIP2 support and output layout

### tests/test_extract_siglip2.py (created)

7 pure config/dict validation tests (no GPU required, completes in ~3.5s):
1. `test_backbone_configs_keys` -- exactly {clip-vit-b-16, siglip2-giant}
2. `test_clip_config_values` -- CLIP config fields correct
3. `test_siglip2_config_values` -- SigLIP2 config fields correct
4. `test_expected_dim_mean_pool` -- mean-only: 512 for CLIP, 1536 for SigLIP2
5. `test_expected_dim_meanmax_pool` -- mean+max: 1024 for CLIP, 3072 for SigLIP2
6. `test_siglip2_output_subdir` -- siglip2/ and siglip2_mean/
7. `test_clip_backward_compat` -- clip/ and clip_mean/ unchanged

## Backward Compatibility

Default behavior with `--backbone clip-vit-b-16` (or omitted) is identical to the previous version:
- Same model (ViT-B-16, openai), same preprocessing, same dimensions (512/1024), same output dirs (clip/clip_mean)
- All existing CLIP extraction results remain valid

## Test Results

- 7/7 new backbone config tests: PASSED
- 215/216 full suite: PASSED (1 pre-existing failure in test_split_seed_reproducibility unrelated to this plan)

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all code paths are fully wired.

## Threat Model Compliance

T-08-03 (feature dimension mismatch): MITIGATED. All three dimension assertion sites now use `embed_dim` from BACKBONE_CONFIGS rather than hardcoded values. Shape assertions fire at extraction time for both CLIP and SigLIP2 backbones.
