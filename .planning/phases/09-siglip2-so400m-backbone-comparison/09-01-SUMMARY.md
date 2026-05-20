---
phase: "09-siglip2-so400m-backbone-comparison"
plan: "01"
subsystem: "extraction, training, ablation"
tags: [siglip2, so400m, backbone, configs, ablation-queues]
dependency_graph:
  requires: []
  provides: ["siglip2-so400m backbone config", "10 SO400M YAML configs", "6 phase9 ablation queues"]
  affects: ["scripts/extract_clip.py", "scripts/run_ablations.py", "configs/*_so400m*.yaml"]
tech_stack:
  added: []
  patterns: ["backbone config registry", "YAML config mirroring", "RunSpec queue pattern"]
key_files:
  created:
    - configs/clip_only_so400m.yaml
    - configs/clip_only_xd_so400m.yaml
    - configs/late_fusion_so400m.yaml
    - configs/late_fusion_xd_so400m.yaml
    - configs/gated_fusion_so400m.yaml
    - configs/gated_fusion_xd_so400m.yaml
    - configs/gated_fusion_so400m_2person.yaml
    - configs/gated_fusion_xd_so400m_2person.yaml
    - configs/gated_fusion_so400m_clip_mean.yaml
    - configs/gated_fusion_xd_so400m_clip_mean.yaml
  modified:
    - scripts/extract_clip.py
    - scripts/run_ablations.py
    - tests/test_extract_siglip2.py
    - tests/test_models.py
    - tests/test_run_ablations.py
decisions: []
metrics:
  duration: "6m"
  completed: "2026-05-20T12:33:00Z"
---

# Phase 9 Plan 01: SO400M Infrastructure Setup Summary

SigLIP2 SO400M backbone (embed_dim=1152, ViT-SO400M-16-SigLIP2-256) added to BACKBONE_CONFIGS, 10 YAML configs created with correct clip_dim (2304 mean+max, 1152 mean-only), 6 phase9 ablation queues with 14 RunSpecs, and all test assertions updated for 3-backbone registry.

## Completed Tasks

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | Add SO400M backbone config, 10 YAML configs, 6 phase9 queues | 0d8ecdf | BACKBONE_CONFIGS entry, 10 configs, 6 queues (14 RunSpecs) |
| 2 | Update test files for SO400M assertions | c77c5a7 | 3 test files updated, 60 tests passing |

## Changes Made

### Task 1: SO400M backbone config, YAML configs, and ablation queues

**BACKBONE_CONFIGS addition (scripts/extract_clip.py):**
- Added `siglip2-so400m` entry: model_name=ViT-SO400M-16-SigLIP2-256, pretrained=webli, embed_dim=1152, output_subdir=siglip2_so400m, mean_subdir=siglip2_so400m_mean

**10 YAML configs (configs/):**
- 8 mean+max pooling configs with clip_dim=2304: clip_only, late_fusion, gated_fusion (UCF+XD), 2person (UCF+XD)
- 2 mean-only pooling configs with clip_dim=1152: gated_fusion_clip_mean (UCF+XD)
- All configs use siglip2_so400m / siglip2_so400m_mean feature paths
- shared_dim=256, proj_dim=512 preserved across all configs
- wandb tags: phase9, so400m (replacing phase8, siglip2)

**6 phase9 ablation queues (scripts/run_ablations.py):**
- phase9_ucf_main (3): clip_only, late_fusion, gated_fusion at seed 42
- phase9_xd_main (3): same variants for XD-Violence
- phase9_ucf_pooling (2): 2person + clip_mean ablations
- phase9_xd_pooling (2): same for XD
- phase9_ucf_seeds (2): seeds 123, 2024 for gated_fusion
- phase9_xd_seeds (2): same for XD
- Total unique run_names across all queues: 238 -> 252 (+14)

### Task 2: Test updates

**tests/test_extract_siglip2.py:**
- Updated expected backbone keys: 2 -> 3 (added siglip2-so400m)
- Added test_so400m_config_values: validates all 5 config fields
- Added SO400M branches in mean pool (1152) and meanmax pool (2304) tests
- Added test_so400m_output_subdir: validates output directory names

**tests/test_models.py:**
- Added test_clip_dim_2304: CLIPProj forward pass with 2304-d input
- Added test_clip_dim_2304_projection_layer: verifies 2304->512 projection
- Added test_late_fusion_clip_dim_2304: LateFusion forward pass
- Added test_gated_fusion_clip_dim_2304: GatedFusion forward pass

**tests/test_run_ablations.py:**
- Added 6 phase9 queue names to help text assertion
- Added phase9 queue length assertions (3,3,2,2,2,2)
- Added 2 spot checks: ucf_gated_fusion_so400m_s42, xd_gated_fusion_so400m_s123
- Updated total unique run_names: 238 -> 252

## Verification

```
60 passed in 12.82s (first run) / 32.81s (second run with spot check addition)
```

All tests pass across test_extract_siglip2.py, test_models.py, and test_run_ablations.py.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- All 10 YAML config files exist: VERIFIED
- Both commits exist in git log: VERIFIED (0d8ecdf, c77c5a7)
- 60 tests pass: VERIFIED
- BACKBONE_CONFIGS has 3 keys: VERIFIED
- Total unique run_names = 252: VERIFIED
