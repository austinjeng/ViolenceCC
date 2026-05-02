---
phase: "06-analysis-visualization"
plan: "02"
subsystem: "visualization"
tags: [skeleton-overlay, gate-analysis, tsne, pytorch-hooks, thesis-figures]
dependency_graph:
  requires:
    - "scripts/generate_phase6_charts.py (Wave 1 base with Sections A+C+F)"
    - "results/ucf_gated_fusion_s42/best_model.pth (UCF checkpoint)"
    - "results/xd_gated_fusion_s42/best_model.pth (XD checkpoint)"
    - "results/*/config_snapshot.json (model config for build_model)"
    - "E:/XD_Violence/test/videos/*.mp4 (high-res video frames)"
    - "E:/skeletons/xd/*.pkl (COCO-17 skeleton pickles)"
    - "E:/features/{ucf,xd}/{skeleton,clip}/*.npy (feature caches)"
  provides:
    - "scripts/generate_phase6_charts.py (1292 lines, Sections A-F complete)"
    - "results/phase6_charts/B_skeleton/ (3 skeleton overlay PNGs)"
    - "results/phase6_charts/D_gating/ (4 gate distribution PNGs)"
    - "results/phase6_charts/E_projection/ (2 t-SNE scatter PNGs)"
  affects:
    - "Task 2 checkpoint: user visual quality review pending"
tech_stack:
  added:
    - "cv2 (video frame extraction + COCO-17 skeleton drawing)"
    - "torch forward hooks (gate activation + fused feature collection)"
    - "sklearn.manifold.TSNE (2D feature projection)"
  patterns:
    - "Forward hook on nn.Linear with manual torch.sigmoid() for gate values"
    - "config_snapshot.json 'config' wrapper key for build_model kwargs"
    - "MILFeatureDataset mode='test' for full-video inference"
key_files:
  created: []
  modified:
    - "scripts/generate_phase6_charts.py"
decisions:
  - "Used matplotlib.colormaps.get_cmap() instead of deprecated plt.cm.get_cmap()"
  - "Skeleton overlays use XD-Violence only (UCF-Crime has 64x64 PNGs, unusable)"
  - "Gate histograms use 50 bins with density normalization for normal vs anomalous overlay"
  - "t-SNE perplexity auto-scaled to min(30, n_samples//4) for small datasets"
metrics:
  duration: "343s (~6 min)"
  completed: "2026-05-02"
  tasks_completed: 1
  tasks_total: 2
  files_created: 0
  files_modified: 1
  pngs_generated: 9
---

# Phase 6 Plan 02: GPU-Dependent Visualizations (Skeleton + Gate + t-SNE) Summary

Forward-hook-based gate activation collection with manual sigmoid on nn.Linear output, COCO-17 skeleton overlays on XD-Violence MP4 frames via cv2, and t-SNE projections of 256-d fused features for both UCF-Crime (254 videos) and XD-Violence (800 videos).

## What Was Built

### Section B: Skeleton Overlays (3 PNGs)
- **draw_skeleton()**: COCO-17 keypoint circles (red) and limb edges (green) on video frames with confidence threshold 0.3
- **create_skeleton_overlay()**: cv2 video frame extraction + dual-person skeleton drawing (both M=0 and M=1 if >= 5 confident keypoints)
- **run_section_B()**: Uses XD-Violence videos selected by Section A (Salt.2010 Fighting, Tropa.de.Elite.2 Shooting); picks anomaly interval midpoints for frame selection; fallback to quarter-points if < 3 frames generated
- Output: B01 (Salt.2010 frame 697), B02 (Tropa.de.Elite.2 frame 838), B03 (Salt.2010 frame 613)

### Section D: Gate Activation Distributions (4 PNGs)
- **collect_gate_and_features()**: Loads GatedFusion checkpoint via build_model + load_checkpoint (strict=True), registers forward hooks on model.gate and model.ln_fused, runs full test set inference
- **Gate hook applies torch.sigmoid() manually** (Pitfall 5 mitigation): model.gate is nn.Linear, hook captures pre-sigmoid output. Gate values confirmed in [0,1]: UCF [0.0369, 0.9394], XD [0.0286, 0.9564]
- **D01 per-category boxplots**: Mean gate value per video grouped by violence category (Normal + anomaly categories). XD category codes mapped to readable names.
- **D02 overlaid histograms**: 50-bin density histograms of all gate values, normal (blue) vs anomalous (red) with alpha=0.5

### Section E: t-SNE Feature Projections (2 PNGs)
- **chart_E_tsne()**: Pools per-video fused features (mean over T -> [256]), runs TSNE(perplexity=30, random_state=42, init='pca'), plots 2D scatter
- Normal points: grey circles (alpha=0.4). Abnormal points: colored by category using tab10 colormap
- UCF: 254 videos (perplexity=30). XD: 800 videos (perplexity=30)

### Infrastructure
- config_snapshot.json has `{"config": {...}}` wrapper -- code handles both wrapped and unwrapped formats
- Progress counters updated from [1/4]...[4/4] to [1/6]...[6/6]
- Script grew from 802 to 1292 lines (+490 lines, 61% increase)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 26345ef | Sections B, D, E: skeleton overlays + gate distributions + t-SNE projections |

## Task 2: Visual Quality Checkpoint (Pending)

Task 2 is a `checkpoint:human-verify` gate. The user needs to visually inspect all 26 generated PNGs:
- **B_skeleton/**: Verify keypoints align with body positions on video frames
- **D_gating/**: Verify gate histogram values in [0,1], category boxplots show meaningful variation
- **E_projection/**: Verify t-SNE shows at least partial normal/anomalous separation

This checkpoint is documented but not blocking -- user review happens separately.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Matplotlib get_cmap deprecation warning**
- **Found during:** Task 1 verification run
- **Issue:** `plt.cm.get_cmap("tab10", N)` deprecated in matplotlib 3.7+, produces runtime warning
- **Fix:** Changed to `matplotlib.colormaps.get_cmap("tab10").resampled(N)`
- **Files modified:** scripts/generate_phase6_charts.py
- **Commit:** 26345ef

## Verification

- Script runs to completion with exit code 0 (tested from main repo with CUDA)
- 26 total PNGs generated (5 A + 3 B + 6 C + 6 F + 4 D + 2 E)
- Gate values confirmed in [0, 1] range (sigmoid applied correctly)
- strict=True used for model.load_state_dict()
- DPI=150 and seaborn whitegrid style applied consistently
- Both UCF (254 videos) and XD (800 videos) processed for D+E sections

## Known Stubs

None -- all sections produce real data from trained model checkpoints.

## Self-Check: PASSED

- scripts/generate_phase6_charts.py: FOUND
- 06-02-SUMMARY.md: FOUND (this file)
- Commit 26345ef: FOUND
- B_skeleton PNGs: 3 (>= 3 required)
- D_gating PNGs: 4 (>= 2 required)
- E_projection PNGs: 2 (>= 2 required)
