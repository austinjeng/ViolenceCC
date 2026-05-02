# Phase 6: Analysis & Visualization - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Qualitative figures and temporal analysis for the thesis document. Produces thesis-ready PNG visualizations covering anomaly score temporal curves, skeleton overlays, feature space projections, gating weight analysis, and corruption robustness heatmaps. All figures generated programmatically for reproducibility.

</domain>

<decisions>
## Implementation Decisions

### Video Selection (VIS-01)
- **D-01:** Select best-detection videos only (clear score spikes aligned with GT) for temporal curves. No failure cases — figures serve as strongest visual argument for the fusion approach.
- **D-02:** 3 UCF-Crime + 2 XD-Violence videos for temporal curves. More coverage across categories than minimum requirement.
- **D-03:** Videos selected should span different violence categories where possible (e.g., Fighting, Explosion, Shooting for UCF; Fighting, Riot for XD).

### Temporal Curve Composition (VIS-01)
- **D-04:** Overlay all 4 model variants on the same axes per video: Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion. Uses established Phase 4 color scheme (Skeleton=slate #64748B, CLIP=blue #3B82F6, Late Fusion=amber #F59E0B, Gated Fusion=red #EF4444).
- **D-05:** Ground-truth anomaly intervals shown as semi-transparent red shaded bands (y=0 to y=1). Standard in VAD literature (RTFM, MGFN use this).
- **D-06:** X-axis = frame number, Y-axis = anomaly score [0, 1]. Scores expanded from snippet-level to frame-level using existing `snippet_to_frame` infrastructure.

### Skeleton Overlay (VIS-02)
- **D-07:** Static frame grabs with COCO-17 keypoints + limb edges drawn on original video frames. Standard thesis figure format — high-res PNG.
- **D-08:** Skeleton overlays use the same videos selected for temporal curves. Ties qualitative analysis into a coherent narrative.
- **D-09:** Minimum 3 frames total across the selected videos. Pick frames during anomalous activity where skeleton poses are informative.

### Model Runs for Feature Collection
- **D-10:** Use Gated Fusion seed=42 checkpoints for both datasets (`ucf_gated_fusion_s42`, `xd_gated_fusion_s42`) for all intermediate feature/activation collection. Qualitative figures don't need multi-seed statistics.

### Extended Scope (OPT-09, OPT-10, OPT-11)
- **D-11:** Include corruption severity heatmap (OPT-11) — 4x5 grid (corruption type x severity) showing AUC degradation. Phase 5 TTA results in `results/tta/` are ready. Follow seaborn heatmap pattern from Phase 4/7.
- **D-12:** Include gating weight distributions (OPT-10) — histogram or boxplot of sigmoid gate values by violence category. Requires forward pass through Gated Fusion to collect gate activations.
- **D-13:** Include t-SNE/UMAP of fused features (OPT-09) — 2D projection of fused feature space colored by category/normal-vs-anomaly. Requires forward pass to collect intermediate features.
- **D-14:** Generate additional figure types at Claude's discretion to maximize thesis figure coverage. Priority on figures that tell different stories (cross-dataset comparison, per-category distributions, etc.). User will curate from the full set during thesis writing.

### Claude's Discretion
- Additional figure types beyond VIS-01, VIS-02, OPT-09/10/11 — Claude should generate as many useful thesis visualizations as reasonable from available data. Examples: cross-dataset comparison panels, per-category score distributions (violin/box), Phase 7 sweep result visualizations, training dynamics comparisons.
- Specific video IDs for temporal curves — select programmatically based on highest Gated Fusion score separation between anomalous and normal segments.
- Number and placement of skeleton overlay frames within selected videos.
- Figure sizing, subplot arrangement, and annotation density.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Evaluation Infrastructure
- `src/evaluate.py` — Evaluation CLI that produces `eval_scores.npz` (per-video frame-level scores)
- `src/eval/snippet_to_frame.py` — Snippet-to-frame score expansion logic
- `src/eval/ucf_annotations.py` — `frame_labels()` and `parse_annotations()` for UCF-Crime GT
- `src/eval/xd_annotations.py` — `xd_frame_labels()` and `parse_xd_annotations()` for XD-Violence GT
- `src/eval/metrics.py` — `compute_frame_metrics()` for AUC/AP computation

### Existing Chart Patterns
- `scripts/generate_phase4_charts.py` — Established chart style (seaborn whitegrid, DPI=150, color scheme, figure sizes). Follow this pattern for consistency.
- `scripts/generate_phase7_charts.py` — Heatmap generation pattern for sweep results.

### Data Sources
- `results/*/eval_scores.npz` — Per-video frame-level anomaly scores (keyed by video ID, 1D float arrays)
- `results/tta/*/eval_scores.npz` — TTA experiment scores for corruption heatmap
- `E:/skeletons/{dataset}/{video_id}.pkl` — PYSKL-format skeleton data (M=2, T, V=17, C=2 keypoints + scores)
- `E:/UCF_crime_dataset/` — Raw UCF-Crime video files
- `scripts/extract_skeletons.py` — Documents skeleton .pkl format (lines 16-22)

### Model Configs
- `configs/gated_fusion.yaml` — UCF Gated Fusion config
- `configs/gated_fusion_xd.yaml` — XD Gated Fusion config

### Requirements
- `.planning/REQUIREMENTS.md` — VIS-01 (temporal curves), VIS-02 (skeleton overlays), OPT-09/10/11

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generate_phase4_charts.py` — Full chart generation pipeline with style constants (DPI, figure sizes, color scheme, seaborn theme). Reuse style setup and variant color/label dicts.
- `eval_scores.npz` — Already contains per-video frame-level scores for all model variants and both datasets. No re-evaluation needed for temporal curves.
- `src/eval/ucf_annotations.py` + `src/eval/xd_annotations.py` — GT annotation parsers ready for temporal curve GT shading.
- `src/eval/snippet_to_frame.py` — Score expansion already implemented and tested.
- `results/tta/` — 120+ TTA result directories with eval_scores.npz ready for corruption heatmap.

### Established Patterns
- Chart scripts as standalone `scripts/generate_phase{N}_charts.py` with matplotlib Agg backend
- Output to `results/phase{N}_charts/` with section-prefixed filenames (A01_, B06_, S01_, etc.)
- Seaborn whitegrid theme, DPI=150, standard figure sizes (12x7, 16x9, 9x6)
- Variant colors: VCOLORS dict with hex values per model variant

### Integration Points
- Skeleton .pkl files at `E:/skeletons/` — need opencv for frame extraction + keypoint drawing
- Raw videos at `E:/UCF_crime_dataset/` for skeleton overlay source frames
- Model checkpoints at `results/*/best_model.pth` for forward passes (gate activations, feature collection)
- `src/models/registry.py` — `build_model()` for loading trained models

</code_context>

<specifics>
## Specific Ideas

- User wants maximalist figure coverage: "all kinds of graph I can get" — generate comprehensively, curate during thesis writing
- Temporal curves should tell a clean "fusion is better" story through best-detection video selection
- All figures must be thesis-quality PNG (not exploratory notebook plots)
- Maintain consistency with Phase 4 chart style for visual coherence across thesis

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-analysis-visualization*
*Context gathered: 2026-05-02*
