# Phase 6: Analysis & Visualization - Research

**Researched:** 2026-05-02
**Domain:** Thesis-quality visualization of anomaly detection results (temporal curves, skeleton overlays, feature projections, gating analysis, corruption heatmaps)
**Confidence:** HIGH

## Summary

Phase 6 produces thesis-ready PNG visualizations from existing experiment results. The codebase already has a mature chart generation pattern (`scripts/generate_phase4_charts.py` with 1149 lines, ~80 PNG outputs, seaborn whitegrid theme, DPI=150 standard). All 8 required eval_scores.npz files exist (4 variants x 2 datasets), 500 TTA result directories are available for the corruption heatmap, skeleton pickles and raw XD-Violence MP4 videos are accessible for overlays, and model checkpoints exist for forward-pass-based feature/activation collection.

The primary technical challenges are: (1) temporal curve generation requires per-video score extraction from eval_scores.npz with correct snippet-to-frame expansion and GT annotation shading, (2) skeleton overlay on XD-Violence requires cv2 video frame extraction with COCO-17 keypoint+edge drawing at full resolution (346x640+), (3) gate activation and feature collection require a modified forward pass through GatedFusion with hook registration, and (4) t-SNE projection requires collecting 256-d fused features across the full test set. UCF-Crime has only 64x64 PNGs (not raw videos), so skeleton overlays should primarily use XD-Violence where 346x640 MP4s are available.

**Primary recommendation:** Build a single `scripts/generate_phase6_charts.py` script following the established Phase 4 pattern, with modular sections (A-temporal curves, B-skeleton overlays, C-corruption heatmap, D-gating analysis, E-feature projection, F-additional thesis figures). Use matplotlib+seaborn for charts, cv2 for video frame extraction and skeleton drawing, sklearn.manifold.TSNE for dimensionality reduction (umap-learn not installed, numba dependency missing).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Select best-detection videos only (clear score spikes aligned with GT) for temporal curves. No failure cases -- figures serve as strongest visual argument for the fusion approach.
- **D-02:** 3 UCF-Crime + 2 XD-Violence videos for temporal curves. More coverage across categories than minimum requirement.
- **D-03:** Videos selected should span different violence categories where possible (e.g., Fighting, Explosion, Shooting for UCF; Fighting, Riot for XD).
- **D-04:** Overlay all 4 model variants on the same axes per video: Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion. Uses established Phase 4 color scheme (Skeleton=slate #64748B, CLIP=blue #3B82F6, Late Fusion=amber #F59E0B, Gated Fusion=red #EF4444).
- **D-05:** Ground-truth anomaly intervals shown as semi-transparent red shaded bands (y=0 to y=1). Standard in VAD literature (RTFM, MGFN use this).
- **D-06:** X-axis = frame number, Y-axis = anomaly score [0, 1]. Scores expanded from snippet-level to frame-level using existing `snippet_to_frame` infrastructure.
- **D-07:** Static frame grabs with COCO-17 keypoints + limb edges drawn on original video frames. Standard thesis figure format -- high-res PNG.
- **D-08:** Skeleton overlays use the same videos selected for temporal curves. Ties qualitative analysis into a coherent narrative.
- **D-09:** Minimum 3 frames total across the selected videos. Pick frames during anomalous activity where skeleton poses are informative.
- **D-10:** Use Gated Fusion seed=42 checkpoints for both datasets (`ucf_gated_fusion_s42`, `xd_gated_fusion_s42`) for all intermediate feature/activation collection. Qualitative figures don't need multi-seed statistics.
- **D-11:** Include corruption severity heatmap (OPT-11) -- 4x5 grid (corruption type x severity) showing AUC degradation. Phase 5 TTA results in `results/tta/` are ready. Follow seaborn heatmap pattern from Phase 4/7.
- **D-12:** Include gating weight distributions (OPT-10) -- histogram or boxplot of sigmoid gate values by violence category. Requires forward pass through Gated Fusion to collect gate activations.
- **D-13:** Include t-SNE/UMAP of fused features (OPT-09) -- 2D projection of fused feature space colored by category/normal-vs-anomaly. Requires forward pass to collect intermediate features.
- **D-14:** Generate additional figure types at Claude's discretion to maximize thesis figure coverage.

### Claude's Discretion
- Additional figure types beyond VIS-01, VIS-02, OPT-09/10/11 -- generate as many useful thesis visualizations as reasonable from available data. Examples: cross-dataset comparison panels, per-category score distributions (violin/box), Phase 7 sweep result visualizations, training dynamics comparisons.
- Specific video IDs for temporal curves -- select programmatically based on highest Gated Fusion score separation between anomalous and normal segments.
- Number and placement of skeleton overlay frames within selected videos.
- Figure sizing, subplot arrangement, and annotation density.

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VIS-01 | Anomaly score temporal curve plots (x=frame, y=score, shaded GT intervals) for 2-3 representative videos per dataset | Temporal curves: eval_scores.npz contains per-video frame-level scores for all 4 variants x 2 datasets (verified 254 UCF + 800 XD keys). GT annotations available via `ucf_annotations.py` and `xd_annotations.py`. `snippet_to_frame.py` handles score expansion. D-04 overlays 4 variants; D-05 uses `axvspan` for GT shading. |
| VIS-02 | Skeleton overlay visualization on video frames (COCO-17 keypoints + edges) for quality validation and thesis figures | Skeleton overlays: Skeleton pickles at `E:/skeletons/{dataset}/{video_id}.pkl` with shape [M=2, T, V=17, C=2]. XD-Violence has raw MP4s at 346x640+ resolution. UCF-Crime only has 64x64 PNGs -- overlays should use XD-Violence videos primarily, with UCF as secondary (lower quality). cv2 4.13.0 available in vcc-main for video reading and drawing. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Temporal curve generation | Script (offline) | -- | Pure matplotlib rendering from pre-computed eval_scores.npz; no model inference needed |
| Skeleton overlay drawing | Script (offline) | Video I/O (cv2) | cv2 reads MP4 frames, draws COCO-17 keypoints+edges; matplotlib saves final PNG |
| Gate activation collection | GPU inference (PyTorch) | -- | Requires forward pass through GatedFusion with hook to capture sigmoid gate tensor |
| Feature projection (t-SNE) | CPU compute (sklearn) | GPU inference (collect) | Forward pass collects 256-d features; sklearn TSNE reduces to 2D; matplotlib plots |
| Corruption heatmap | Script (offline) | -- | Reads eval_metrics.json from 500 TTA result dirs; seaborn heatmap rendering |
| Video selection (best-detection) | Script (offline) | -- | Programmatic selection from eval_scores.npz by score-GT alignment quality |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | 3.10.8 | All chart generation (temporal curves, bar charts, scatter plots) | Already installed, established Phase 4 pattern [VERIFIED: vcc-main python import] |
| seaborn | 0.13.2 | Heatmaps, statistical plots, theme management | Already installed, Phase 4/7 heatmap pattern [VERIFIED: vcc-main python import] |
| numpy | 2.4.3 | Array operations, score manipulation | Already installed [VERIFIED: vcc-main python import] |
| opencv-python (cv2) | 4.13.0 | Video frame extraction, skeleton keypoint drawing | Already installed in vcc-main (contrary to earlier CLAUDE.md note), verified drawing + video read works [VERIFIED: vcc-main python import + functional test] |
| torch | 2.6.0+cu124 | Forward pass for gate activation and feature collection | Already installed [VERIFIED: vcc-main python import] |
| scikit-learn | 1.8.0 | t-SNE dimensionality reduction, ROC/AUC computation | Already installed, TSNE class verified [VERIFIED: vcc-main python import] |
| pandas | (installed) | Results CSV parsing | Already installed, used in Phase 4 charts [VERIFIED: generate_phase4_charts.py imports] |
| PIL/Pillow | (installed) | PNG loading for UCF-Crime 64x64 frames | Already installed [VERIFIED: vcc-main python import] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sklearn TSNE | umap-learn (UMAP) | UMAP preserves global structure better, but requires numba (not installed) + umap-learn install. t-SNE is sufficient for thesis figure and avoids environment modification. |
| cv2 for skeleton drawing | matplotlib scatter+line | cv2.circle + cv2.line on actual video frame is more natural for overlay; matplotlib would require coordinate transformation |
| Separate scripts per figure | Single monolithic script | Single script (like Phase 4) is easier to maintain and ensures consistent style; section prefixes keep outputs organized |

**Installation:**
```bash
# No new packages needed -- all dependencies already in vcc-main
# If UMAP is desired (optional):
# pip install umap-learn  # requires numba, ~500MB download
```

## Architecture Patterns

### System Architecture Diagram

```
eval_scores.npz (4 variants x 2 datasets)
    |
    v
[Video Selector] ---> best-detection video IDs
    |                       |
    v                       v
[Temporal Curve Gen]  [Skeleton Overlay Gen]
    |                       |
    |  GT annotations       |  E:/skeletons/*.pkl
    |  (ucf/xd_annotations) |  E:/XD_Violence/test/videos/*.mp4
    |                       |  cv2 frame extraction
    v                       v
 axvspan GT shading      cv2.circle + cv2.line
 4-variant overlay       on video frame
    |                       |
    v                       v
 results/phase6_charts/  results/phase6_charts/
 A_temporal/             B_skeleton/

results/tta/eval_metrics.json (500 dirs)
    |
    v
[TTA Heatmap Gen] --> corruption x severity x method grid
    |
    v
 results/phase6_charts/C_corruption/

best_model.pth (Gated Fusion s42)
    |
    v
[Modified Forward Pass] ---> gate activations [B,T,256]
    |                    ---> fused features [B,T,256]
    v                         v
[Gate Histogram]         [t-SNE Projection]
    |                         |
    v                         v
 results/phase6_charts/   results/phase6_charts/
 D_gating/                E_projection/
```

### Recommended Project Structure
```
scripts/
  generate_phase6_charts.py     # Main visualization script (single file, sectioned)
results/
  phase6_charts/
    A_temporal/                  # Temporal anomaly score curves
    B_skeleton/                  # Skeleton overlay PNGs
    C_corruption/                # TTA corruption heatmaps
    D_gating/                    # Gate weight distributions
    E_projection/                # t-SNE feature projections
    F_additional/                # Cross-dataset, per-category, etc.
```

### Pattern 1: Temporal Score Curve with GT Shading
**What:** Per-video anomaly score plot with 4 model variant overlays and ground-truth shaded bands
**When to use:** VIS-01 temporal curve plots
**Example:**
```python
# Source: Verified from matplotlib 3.10.8 axvspan docs + Phase 4 VCOLORS pattern
import matplotlib.pyplot as plt
import numpy as np

def plot_temporal_curve(video_id, scores_by_variant, gt_intervals, n_frames,
                        dataset, ax=None):
    """Plot anomaly scores with GT shading for one video.
    
    scores_by_variant: dict {variant_name: np.ndarray[n_frames]}
    gt_intervals: list of (start, end) frame-level intervals
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(16, 5))
    
    frames = np.arange(n_frames)
    
    # GT shading (D-05): semi-transparent red bands
    for start, end in gt_intervals:
        ax.axvspan(start, end, alpha=0.15, color='red', label='_nolegend_')
    # Add single legend entry for GT
    ax.axvspan(0, 0, alpha=0.15, color='red', label='Ground Truth')
    
    # Overlay 4 variants (D-04)
    VCOLORS = {
        "skeleton_only": "#64748B",
        "clip_only": "#3B82F6",
        "late_fusion": "#F59E0B",
        "gated_fusion": "#EF4444",
    }
    VLABELS = {
        "skeleton_only": "Skeleton Only",
        "clip_only": "CLIP Only",
        "late_fusion": "Late Fusion",
        "gated_fusion": "Gated Fusion",
    }
    
    for variant in ["skeleton_only", "clip_only", "late_fusion", "gated_fusion"]:
        scores = scores_by_variant[variant]
        ax.plot(frames, scores, color=VCOLORS[variant],
                label=VLABELS[variant], linewidth=1.5, alpha=0.85)
    
    ax.set_xlabel("Frame Number", fontsize=14)
    ax.set_ylabel("Anomaly Score", fontsize=14)
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0, n_frames)
    ax.legend(fontsize=11, loc='upper right')
    ax.set_title(f"{video_id} ({dataset})", fontsize=16, fontweight='bold')
```

### Pattern 2: COCO-17 Skeleton Overlay on Video Frame
**What:** Draw keypoints and limb edges on an actual video frame
**When to use:** VIS-02 skeleton overlay visualization
**Example:**
```python
# Source: COCO keypoint format (verified from extract_skeletons.py + COCO docs)
import cv2
import numpy as np

# COCO-17 keypoint names and edge connectivity
COCO_KEYPOINTS = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
]
# Edge pairs (0-indexed)
COCO_EDGES = [
    (0, 1), (0, 2), (1, 3), (2, 4),          # face
    (5, 6),                                     # shoulders
    (5, 7), (7, 9),                            # left arm
    (6, 8), (8, 10),                           # right arm
    (5, 11), (6, 12), (11, 12),                # torso
    (11, 13), (13, 15),                        # left leg
    (12, 14), (14, 16),                        # right leg
]
# Color coding by body part
EDGE_COLORS = {
    'face': (255, 200, 0),      # yellow
    'left': (0, 255, 0),        # green
    'right': (0, 150, 255),     # orange
    'torso': (255, 0, 255),     # magenta
}

def draw_skeleton(frame, keypoints, scores, conf_threshold=0.3):
    """Draw COCO-17 skeleton on a video frame.
    
    keypoints: [17, 2] float32 pixel coordinates
    scores: [17] float32 confidence scores
    """
    h, w = frame.shape[:2]
    
    # Draw edges first (behind keypoints)
    for (i, j) in COCO_EDGES:
        if scores[i] > conf_threshold and scores[j] > conf_threshold:
            pt1 = (int(keypoints[i, 0]), int(keypoints[i, 1]))
            pt2 = (int(keypoints[j, 0]), int(keypoints[j, 1]))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2, cv2.LINE_AA)
    
    # Draw keypoints
    for k in range(17):
        if scores[k] > conf_threshold:
            pt = (int(keypoints[k, 0]), int(keypoints[k, 1]))
            cv2.circle(frame, pt, 4, (0, 0, 255), -1, cv2.LINE_AA)
    
    return frame
```

### Pattern 3: Modified Forward Pass for Gate Activation Collection
**What:** Register a PyTorch forward hook on GatedFusion.gate to capture sigmoid outputs
**When to use:** D-12 gate weight distributions, D-13 feature collection
**Example:**
```python
# Source: Verified from src/models/gated_fusion.py (line 73)
import torch

def collect_gate_activations(model, dataset, device):
    """Collect sigmoid gate values from GatedFusion forward pass.
    
    Returns: dict {video_id: np.ndarray[T, 256]} gate activations
    """
    gate_outputs = {}
    fused_features = {}
    
    def gate_hook(module, input, output):
        # output is the raw linear output BEFORE sigmoid
        # sigmoid is applied inline in forward(): g = torch.sigmoid(self.gate(...))
        # So we hook the gate Linear and apply sigmoid manually
        gate_hook._last_output = torch.sigmoid(output).detach().cpu()
    
    hook = model.gate.register_forward_hook(gate_hook)
    
    # Also hook ln_fused output for feature collection
    fused_hook_data = {}
    def fused_hook(module, input, output):
        fused_hook_data['last'] = output.detach().cpu()
    
    hook2 = model.ln_fused.register_forward_hook(fused_hook)
    
    model.eval()
    with torch.no_grad():
        loader = DataLoader(dataset, batch_size=1, shuffle=False)
        for batch in loader:
            vid = batch["video_id"][0]
            kwargs = {}
            for k in ("skel", "clip"):
                if k in batch:
                    t = batch[k]
                    if t.dim() == 2:
                        t = t.unsqueeze(0)
                    kwargs[k] = t.to(device)
            model(**kwargs)
            gate_outputs[vid] = gate_hook._last_output.squeeze(0).numpy()
            fused_features[vid] = fused_hook_data['last'].squeeze(0).numpy()
    
    hook.remove()
    hook2.remove()
    return gate_outputs, fused_features
```

### Pattern 4: Corruption Severity Heatmap from TTA Results
**What:** 4x5 grid (corruption type x severity) showing AUC degradation
**When to use:** D-11 corruption heatmap
**Example:**
```python
# Source: Verified from results/tta/ directory structure + generate_phase7_charts.py heatmap pattern
import json, os
import pandas as pd
import seaborn as sns

def load_tta_results(tta_dir):
    """Load eval_metrics.json from all TTA result directories.
    
    TTA dir naming: {method}_{corruption}_{severity}_lr{lr}[_rho{rho}]
    Methods: source_only (20 dirs), tent (80 dirs), sar (400 dirs)
    """
    rows = []
    for d in os.listdir(tta_dir):
        metrics_path = os.path.join(tta_dir, d, 'eval_metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                m = json.load(f)
            rows.append({
                'method': m['method'],
                'corruption': m['corruption_type'],
                'severity': m['severity'],
                'lr': m.get('lr', 0),
                'rho': m.get('rho'),
                'auc': m['auc'],
                'ap': m['ap'],
            })
    return pd.DataFrame(rows)
```

### Anti-Patterns to Avoid
- **Re-running evaluation:** All eval_scores.npz files already exist. Do NOT re-run src/evaluate.py. Load scores directly from the .npz files.
- **Using notebook-style plots:** All figures must be thesis-quality PNGs from a reproducible script, not Jupyter notebook outputs.
- **Inconsistent style:** Reuse VCOLORS, VLABELS, DPI, figure sizes, and seaborn theme from Phase 4 charts. Do not define new color schemes.
- **Loading all 500 TTA dirs in memory:** Parse eval_metrics.json (small JSON) not eval_scores.npz (large arrays) for the heatmap.
- **Using strict=False for checkpoint loading:** Per CLAUDE.md convention, always use strict=True with model.load_state_dict().

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Snippet-to-frame expansion | Custom repeat/interpolation | `src.eval.snippet_to_frame.snippet_to_frame()` | Already handles UCF (window=64, upsample=10) and XD (window=64, upsample=1); includes C4 drift assertion |
| GT annotation parsing | Regex on filenames | `src.eval.ucf_annotations.parse_annotations()` + `frame_labels()` | Handles Sultani 2018 format, dual intervals, category extraction |
| XD GT annotations | Custom parser | `src.eval.xd_annotations.parse_xd_annotations()` + `xd_frame_labels()` | Handles Wu 2020 variable-interval format, 500/300 abnormal/normal split |
| Model loading | Manual state_dict | `src.models.registry.build_model()` + `src.utils.checkpoint.load_checkpoint()` | Registry resolves variant, checkpoint handles strict loading |
| Color scheme | New hex codes | Phase 4 `VCOLORS` dict | Consistency across all thesis figures |
| Heatmap generation | Custom grid plot | `seaborn.heatmap()` | Already proven in Phase 4 (B06/B07) and Phase 7 (S01/S04) |
| Dimensionality reduction | Custom PCA+plotting | `sklearn.manifold.TSNE` | Standard, well-tested, available in vcc-main |

**Key insight:** This phase is primarily a data visualization task that should reuse all existing evaluation infrastructure. The only new code is (1) visualization logic itself, (2) forward-pass hooks for gate/feature collection, and (3) video-selection heuristic.

## Common Pitfalls

### Pitfall 1: UCF-Crime vs XD-Violence Score Expansion Parameters
**What goes wrong:** UCF-Crime uses snippet_window=64 with upsample_factor=10 (64x64 PNG grid -> 30fps original video), while XD-Violence uses snippet_window=64 with upsample_factor=1 (native FPS). Using wrong parameters produces misaligned GT shading.
**Why it happens:** The evaluate.py code handles this per-dataset but when extracting scores from eval_scores.npz, the scores are ALREADY frame-level (post-expansion). The npz stores the final frame-level scores, not snippet scores.
**How to avoid:** Read scores directly from eval_scores.npz -- they are already frame-level. No snippet_to_frame call needed for temporal curves. Only need GT annotation label vectors at matching length.
**Warning signs:** Score array length doesn't match GT label vector length.

### Pitfall 2: eval_scores.npz Contains Frame-Level Scores (Not Snippet-Level)
**What goes wrong:** Attempting to apply snippet_to_frame on scores from eval_scores.npz would double-expand them.
**Why it happens:** evaluate.py stores the FINAL frame-level scores after snippet_to_frame expansion. The scores in the npz are keyed by video_id and have shape [n_frames_expanded].
**How to avoid:** Verified: `Abuse028` has shape (1280,) which is snippet_count * snippet_window * upsample_factor. Use directly.
**Warning signs:** Scores array much longer than expected.

### Pitfall 3: UCF-Crime 64x64 PNG Resolution for Skeleton Overlay
**What goes wrong:** Drawing COCO-17 keypoints on a 64x64 image produces unusable figures. The skeleton pickle `img_shape` for UCF is (64, 64) -- these are pre-extracted low-res PNGs, not raw videos.
**Why it happens:** UCF-Crime dataset was distributed as pre-extracted 64x64 PNG frames, not raw video. No MP4 files exist on disk.
**How to avoid:** Use XD-Violence videos (346x640+ MP4s at `E:/XD_Violence/test/videos/`) for skeleton overlays. If UCF is needed, note the low resolution in the figure caption or upscale with cv2.resize().
**Warning signs:** img_shape=(64, 64) in skeleton pickle.

### Pitfall 4: XD-Violence Normal Videos Missing from Annotation File
**What goes wrong:** Trying to look up GT intervals for normal XD-Violence test videos in the annotations file returns KeyError.
**Why it happens:** Wu 2020 annotation file contains only the 500 abnormal test videos. The 300 normal test videos are omitted entirely.
**How to avoid:** Guard with `if vid in annos` before accessing annotations. Normal videos have no anomaly intervals (all-zero labels).
**Warning signs:** KeyError on normal video IDs.

### Pitfall 5: Gate Hook Captures Pre-Sigmoid Values
**What goes wrong:** The `self.gate` module is `nn.Linear(2*shared_dim, shared_dim)`. Its forward hook output is the LINEAR output, not the sigmoid-activated gate values. The sigmoid is applied inline in GatedFusion.forward() at line 73: `g = torch.sigmoid(self.gate(...))`.
**Why it happens:** PyTorch forward hooks on nn.Linear capture the linear projection output.
**How to avoid:** Apply `torch.sigmoid()` to the hook output manually, or register the hook differently.
**Warning signs:** Gate values outside [0, 1] range; negative values.

### Pitfall 6: Video Selection Requires All 4 Variants' Scores
**What goes wrong:** Selecting best-detection videos based only on Gated Fusion scores, then finding other variants have no scores for that video.
**Why it happens:** All 4 variants have identical video IDs in eval_scores.npz (254 UCF test videos, 800 XD test videos), so this is unlikely. But worth asserting.
**How to avoid:** Verify video_id exists in all 4 variants' npz files before selecting.
**Warning signs:** KeyError when loading variant scores for selected video.

### Pitfall 7: TTA Heatmap Best-LR Selection
**What goes wrong:** The corruption heatmap should show best-performing LR/rho for each method (not a fixed hyperparameter), since TENT has 4 LR options and SAR has 4x5=20 LR/rho combinations per condition.
**Why it happens:** Multiple hyperparameter configurations exist per corruption condition per method.
**How to avoid:** For each (method, corruption, severity), select the best AUC configuration, then display only the best result in the heatmap.
**Warning signs:** Heatmap shows worse-than-source-only results for adapted methods (may indicate wrong hyperparameter selection).

## Code Examples

### Video Selection Heuristic (D-01, D-02)
```python
# Source: Verified from eval_scores.npz structure + annotation parsing
def select_best_detection_videos(dataset, n_videos, eval_scores_npz, annos, label_fn):
    """Select videos with clearest anomaly score spikes aligned with GT.
    
    Heuristic: maximize (mean_score_in_anomaly_region - mean_score_in_normal_region)
    for the Gated Fusion variant. This finds videos where the model's detection
    is cleanest for thesis presentation.
    """
    candidates = []
    for vid in eval_scores_npz.files:
        scores = eval_scores_npz[vid]
        if vid not in annos:
            continue  # skip normal videos
        labels = label_fn(annos[vid], len(scores))
        if labels.sum() == 0:
            continue  # no anomaly frames
        
        anom_mean = scores[labels == 1].mean()
        norm_mean = scores[labels == 0].mean()
        separation = anom_mean - norm_mean
        
        candidates.append((vid, separation, annos[vid].category))
    
    # Sort by separation, pick top N spanning different categories (D-03)
    candidates.sort(key=lambda x: -x[1])
    selected = []
    categories_used = set()
    for vid, sep, cat in candidates:
        if cat not in categories_used or len(selected) < n_videos:
            selected.append(vid)
            categories_used.add(cat)
        if len(selected) >= n_videos:
            break
    return selected
```

### Skeleton Overlay from XD-Violence Video + Pickle
```python
# Source: Verified from extract_skeletons.py pickle format + cv2 functional test
def create_skeleton_overlay(video_path, skeleton_pkl_path, frame_idx, person_idx=0):
    """Extract a frame from video and overlay skeleton keypoints+edges.
    
    video_path: path to XD-Violence MP4 file
    skeleton_pkl_path: PYSKL-format pickle with keypoint [M=2, T, V=17, C=2]
    frame_idx: which frame to extract (0-indexed)
    person_idx: which person (0 or 1, M dimension)
    """
    import pickle
    
    # Read skeleton data
    with open(skeleton_pkl_path, 'rb') as f:
        skel = pickle.load(f)
    
    kps = skel['keypoint'][person_idx, frame_idx]      # [17, 2] pixel coords
    scores = skel['keypoint_score'][person_idx, frame_idx]  # [17]
    
    # Extract video frame
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise RuntimeError(f"Failed to read frame {frame_idx} from {video_path}")
    
    # Draw skeleton
    frame = draw_skeleton(frame, kps, scores, conf_threshold=0.3)
    return frame
```

### t-SNE Feature Projection (D-13)
```python
# Source: sklearn 1.8.0 TSNE verified available
from sklearn.manifold import TSNE

def compute_tsne(features_dict, categories_dict, perplexity=30, random_state=42):
    """Project fused features to 2D for visualization.
    
    features_dict: {video_id: np.ndarray[T, 256]} from forward pass
    categories_dict: {video_id: str} category labels
    
    Returns: (X_2d, labels, categories) for plotting
    """
    # Pool per-video features (mean over T dimension)
    X = []
    labels = []
    cats = []
    for vid in features_dict:
        feat = features_dict[vid].mean(axis=0)  # [256]
        X.append(feat)
        cat = categories_dict.get(vid, "Normal")
        labels.append(0 if cat == "Normal" else 1)
        cats.append(cat)
    
    X = np.stack(X)  # [N_videos, 256]
    
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=random_state,
                init='pca', method='barnes_hut')
    X_2d = tsne.fit_transform(X)
    
    return X_2d, np.array(labels), cats
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Jupyter notebook plots | Standalone Python scripts with Agg backend | Phase 4 (2026-04) | Reproducible thesis-quality PNGs, no notebook dependency |
| Per-variant score comparison | 4-variant overlay on same axes | Phase 4 (VCOLORS pattern) | Direct visual comparison of fusion benefit |
| matplotlib defaults | seaborn whitegrid + consistent DPI/sizing | Phase 4 | Professional appearance suitable for thesis |

**Deprecated/outdated:**
- openai/clip is frozen at 2021 -- open-clip-torch used instead (project standard)
- matplotlib interactive backends -- use Agg only for script-based generation

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | eval_scores.npz stores frame-level (post-expansion) scores, not snippet scores | Pitfalls 1-2 | Would need snippet_to_frame call; temporal curve X-axis alignment would be wrong |
| A2 | COCO-17 edge connectivity list is standard | Code Examples | Skeleton edges drawn incorrectly; visual artifact |
| A3 | Forward hook on nn.Linear captures pre-sigmoid output | Pitfall 5 | Gate values would be wrong if sigmoid is applied elsewhere |

**Note on A1:** Verified empirically -- Abuse028 has shape (1280,) = 2 snippets * 64 window * 10 upsample. This confirms frame-level storage. Risk is LOW.

**Note on A3:** Verified from source code at gated_fusion.py line 73: `g = torch.sigmoid(self.gate(...))`. The sigmoid IS applied after the linear layer, not inside it. Risk is LOW.

## Open Questions

1. **UCF-Crime raw video availability for skeleton overlay**
   - What we know: Only 64x64 PNGs exist at `E:/UCF_crime_dataset/`. No MP4 files found.
   - What's unclear: Whether the user has raw UCF-Crime videos elsewhere, or if 64x64 overlays are acceptable.
   - Recommendation: Use XD-Violence for primary skeleton overlays (D-09 requires minimum 3 frames). If UCF overlay is desired, upscale 64x64 PNGs with bicubic interpolation or note limitation in figure caption.

2. **Best TTA hyperparameter selection for heatmap**
   - What we know: 500 TTA result dirs with varying LR and rho. source_only has lr=0 (no adaptation). tent has 4 LR choices. SAR has 4*5=20 LR*rho choices per condition.
   - What's unclear: Whether heatmap should show best-per-condition or fixed-hyperparameter results.
   - Recommendation: Show 3 heatmaps side-by-side (Source-Only, best-TENT, best-SAR) where "best" is the highest AUC for each (corruption, severity) cell. This is standard TTA presentation.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| matplotlib | All charts | Yes | 3.10.8 | -- |
| seaborn | Heatmaps, themes | Yes | 0.13.2 | -- |
| cv2 (opencv-python) | Skeleton overlay, video reading | Yes | 4.13.0 | PIL for static images |
| torch (CUDA) | Gate/feature collection | Yes | 2.6.0+cu124 | -- |
| sklearn (TSNE) | Feature projection | Yes | 1.8.0 | -- |
| numpy | Array ops | Yes | 2.4.3 | -- |
| umap-learn | Alternative to t-SNE | No | -- | sklearn TSNE (adequate for thesis) |
| numba | umap-learn dependency | No | -- | Not needed if using t-SNE |
| XD-Violence MP4s | Skeleton overlay source frames | Yes | 800 test videos | -- |
| UCF-Crime raw videos | Skeleton overlay (UCF) | No (64x64 PNGs only) | -- | Use XD-Violence videos or upscale PNGs |

**Missing dependencies with no fallback:**
- None -- all critical dependencies are available.

**Missing dependencies with fallback:**
- umap-learn -> use sklearn TSNE instead (adequate for thesis figure).
- UCF-Crime raw videos -> use XD-Violence videos for skeleton overlays; UCF at 64x64 if needed with upscaling.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via vcc-main) |
| Config file | `tests/conftest.py` (project-root-relative) |
| Quick run command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x --tb=short -q` |
| Full suite command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VIS-01 | Temporal curve PNG generation with GT shading + 4-variant overlay | smoke | `python scripts/generate_phase6_charts.py` (verify output exists) | No -- Wave 0 |
| VIS-02 | Skeleton overlay PNG with COCO-17 keypoints+edges on video frame | smoke | `python scripts/generate_phase6_charts.py` (verify output exists) | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** Verify output PNGs exist and are non-zero size
- **Per wave merge:** Full script run produces all expected outputs
- **Phase gate:** All output PNGs exist, manually spot-check visual quality

### Wave 0 Gaps
- [ ] No dedicated test file needed -- visualization scripts are validated by output existence and visual inspection. Chart generation scripts are end-to-end integration tests by nature (they fail loudly on data format mismatches).
- [ ] The existing test suite covers all upstream dependencies (annotations, metrics, snippet_to_frame, model loading).

## Security Domain

> Phase 6 is a read-only visualization phase that produces PNG files from existing experiment results. No network endpoints, user input processing, authentication, or data modification is involved. Security domain is not applicable.

## Sources

### Primary (HIGH confidence)
- `scripts/generate_phase4_charts.py` -- Established chart pattern (1149 lines, VCOLORS, style constants, seaborn whitegrid, DPI=150). Directly inspected.
- `scripts/generate_phase7_charts.py` -- Heatmap generation pattern (seaborn heatmap with baseline annotation). Directly inspected.
- `src/models/gated_fusion.py` -- GatedFusion architecture (lines 66-79), gate sigmoid at line 73, 3 LayerNorm positions. Directly inspected.
- `src/eval/snippet_to_frame.py` -- Score expansion logic (64-window, 10x upsample for UCF, 1x for XD). Directly inspected.
- `src/eval/ucf_annotations.py` + `src/eval/xd_annotations.py` -- GT annotation parsing. Directly inspected.
- `src/evaluate.py` -- Evaluation CLI producing eval_scores.npz. Directly inspected.
- `results/ucf_gated_fusion_s42/eval_scores.npz` -- 254 keys, frame-level float32 arrays (verified: Abuse028 shape=(1280,)). Empirically verified.
- `results/xd_gated_fusion_s42/eval_scores.npz` -- 800 keys. Empirically verified.
- All 8 variant/dataset eval_scores.npz confirmed present. Empirically verified.
- `results/tta/` -- 500 directories (20 source_only + 80 tent + 400 SAR). Empirically verified.
- `E:/skeletons/ucf/Abuse028.pkl` -- PYSKL format confirmed: keypoint [2,142,17,2], img_shape (64,64). Empirically verified.
- `E:/skeletons/xd/*.pkl` -- img_shape (346,640), actual video resolution. Empirically verified.
- `E:/XD_Violence/test/videos/` -- 800 MP4 files available. Empirically verified.
- `E:/UCF_crime_dataset/test/` -- Only 64x64 PNGs, no MP4 files. Empirically verified.
- cv2 4.13.0 available in vcc-main, drawing + video reading functional. Empirically verified.
- sklearn 1.8.0 TSNE available. Empirically verified.
- umap-learn NOT installed, numba NOT available. Empirically verified.

### Secondary (MEDIUM confidence)
- [matplotlib axvspan docs](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.axvspan.html) -- Shaded region API for GT bands
- [COCO keypoint skeleton connectivity](https://github.com/facebookresearch/Detectron/issues/640) -- COCO-17 edge pair standard

### Tertiary (LOW confidence)
- None -- all claims verified from codebase inspection or empirical testing.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified in vcc-main
- Architecture: HIGH -- follows established Phase 4 chart generation pattern exactly
- Data availability: HIGH -- all 8 eval_scores.npz, 500 TTA dirs, skeleton pickles, XD videos verified on disk
- Pitfalls: HIGH -- all verified from codebase inspection (snippet_to_frame parameters, UCF PNG resolution, gate sigmoid location)

**Research date:** 2026-05-02
**Valid until:** 2026-06-02 (stable -- visualization libraries and data on disk are static)
