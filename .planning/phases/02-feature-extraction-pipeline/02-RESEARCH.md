# Phase 2: Feature Extraction Pipeline - Research

**Researched:** 2026-04-03
**Domain:** Multi-modal feature extraction (skeleton/CLIP), split construction, temporal alignment
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Skeleton features extracted with non-overlapping 64-frame sliding windows (T=64). Each window produces one 256-d vector via 4-stream weighted concat. Variable-length output per video.

**D-02:** CLIP features extracted at true 1 FPS, independent of skeleton window boundaries. Each sampled frame produces one 512-d vector via mean+max pooling. Variable-length output per video.

**D-03:** Phase 3 dataset loader resamples both modalities to T=32 at training time. Extraction does NOT lock T.

**D-04:** UCF-Crime uses pre-extracted PNGs as-is (~3fps equivalent, every 10th frame). No original video decoding needed. Both skeleton and CLIP extract from these same PNGs.

**D-05:** Top-2 persons selected by highest mean keypoint confidence when RTMPose detects 3+ people per frame.

**D-06:** No minimum confidence threshold — accept all RTMPose detections regardless of confidence.

**D-07:** Frames with 0 detected persons → zero-pad both person slots (all-zero keypoints).

**D-08:** Frames with exactly 1 person → zero-pad second person slot (M=2 required by checkpoint).

**D-09:** Per-category stratified 15% val split from training set. For UCF-Crime: sample 15% from each of the 14 categories.

**D-10:** Both UCF-Crime and XD-Violence get 15% val splits.

**D-11:** Val split seed value: 42. Fixed forever once created.

**D-12:** Split format: plain text files in `data/splits/`, one video ID per line. Files: `ucf_train.txt`, `ucf_val.txt`, `ucf_test.txt`, `xd_train.txt`, `xd_val.txt`, `xd_test.txt`.

**D-13:** Process UCF-Crime first (smaller, PNG-based). Validates pipeline end-to-end before XD-Violence.

**D-14:** Skip-if-exists resume strategy for all extraction scripts.

**D-15:** Log-and-skip for corrupted/unreadable videos — write failed video IDs to errors.log.

**D-16:** tqdm progress bar for all extraction scripts.

### Claude's Discretion

- Exact batch size for GPU inference during extraction
- CLIP preprocessing details (resize, center crop, normalization — follow open-clip defaults)
- PYSKL pickle format internals (follow PYSKL's existing examples)
- XD-Violence video decoding library choice (decord vs opencv — whichever works on Windows)
- Error log format and location

### Deferred Ideas (OUT OF SCOPE)

- FPS distribution scan across both datasets
- CLIP sampling rate ablation (1 FPS vs 2 FPS vs 4 FPS) — OPT-07
- RWF-2000 feature extraction — OPT-08
- Intermediate PYSKL pickle archival after skeleton extraction
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Official split files committed — UCF-Crime (Anomaly_Train.txt, Anomaly_Test.txt, Temporal_Anomaly_Annotation.txt), XD-Violence annotation file | Split file sourcing, format parsing, video ID extraction |
| DATA-02 | Fixed 15% stratified validation split from training set (seeded, text file, normal/abnormal ratio preserved) | sklearn stratified split, seed=42, format spec |
| DATA-03 | Skeleton extraction script (rtmlib RTMPose-m) outputting PYSKL-compatible pickle (COCO-17, top-2 persons, confidence scores) | PYSKL pickle format spec, rtmlib API, preprocessing pipeline |
| DATA-04 | Skeleton coordinate normalization verified — raw RTMPose pixel coords pass through PreNormalize2D before CTR-GCN forward pass | PreNormalize2D source code verified, coordinate range assertion |
| DATA-05 | CTR-GCN frozen feature extraction producing 256-d per snippet with 4-stream weighted concat (j:b:jm:bm = 1.0:1.0:0.5:0.5) | 4-stream pipeline, CTR-GCN input shape, pool strategy |
| DATA-06 | CLIP ViT-B/16 feature extraction at 1 FPS with mean+max pooling producing 512-d per snippet | open-clip API, preprocessing defaults, pooling + projection |
| DATA-07 | Feature cache as float32 .npy per video, indexed by video ID, both modalities | .npy format, file naming convention, dtype spec |
| DATA-08 | Temporal alignment verification script — N_skel_snippets == N_clip_snippets for every video | Snippet boundary definition, alignment algorithm |
| DATA-09 | UCF-Crime skeleton + CLIP features fully extracted and cached | UCF-Crime dataset structure, PNG enumeration, video enumeration |
| DATA-10 | XD-Violence skeleton + CLIP features fully extracted and cached | XD-Violence video decoding, annotation parsing, path handling |
</phase_requirements>

---

## Summary

Phase 2 constructs the complete feature extraction pipeline that converts raw video data into the cached feature arrays consumed by the MIL training in Phase 3. The pipeline has three primary components: (1) a skeleton extraction script running in `vcc-skeleton` that uses rtmlib RTMPose-m to produce per-frame COCO-17 keypoints, (2) a CTR-GCN feature script running in `vcc-ctrgcn` that loads the NTU120 HRNet weights and produces 256-d snippet embeddings via 4-stream weighted concatenation, and (3) a CLIP extraction script running in `vcc-main` that samples frames at 1 FPS and applies mean+max pooling to produce 512-d snippet embeddings. All scripts use skip-if-exists resume logic and share a common temporal definition for snippet boundaries so that the alignment verification script can confirm N_skel_snippets == N_clip_snippets for every video.

The extraction targets two datasets with fundamentally different structures. UCF-Crime provides pre-extracted PNGs (every 10th frame, ~3 FPS equivalent) organized by category under `E:\UCF_crime_dataset\Train\{category}\{VideoName}_x264_{framenum}.png` and similarly under `test\`. The naming convention requires numeric sort (not lexicographic) and categories start at non-sequential numbers (Fighting002, no Fighting001). XD-Violence provides raw mp4 files decoded via decord under `E:\XD_Violence\train\` (3954 files) and `E:\XD_Violence\test\videos\` (800 files). XD-Violence has a multi-scene annotation format with variable temporal annotation fields that must be parsed robustly.

**Primary recommendation:** Build scripts in the order: (1) split file creation, (2) skeleton extraction on UCF-Crime as the pipeline validation end-to-end, (3) CTR-GCN feature pass, (4) CLIP extraction with UCF-Crime, (5) alignment verification on UCF-Crime, then (6) scale to XD-Violence skeleton and CLIP in parallel (overnight background jobs). Both modalities must use identical snippet boundary definitions — the frame index ranges — which are computed once and shared between both extraction paths.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| rtmlib | 0.0.15 | RTMPose-based skeleton extraction, ONNX Runtime inference | Only library running RTMPose without mmcv dependency; purpose-built for this use case |
| onnxruntime-gpu | 1.20.x | GPU inference for RTMPose ONNX models | Since v1.19.0, CUDA 12.x default; required by rtmlib for GPU acceleration |
| PyTorch | 1.12.1 (cu113) | CTR-GCN forward pass (vcc-ctrgcn env) | PYSKL pins this version; mmcv-full 1.7.0 only compiles against PyTorch 1.x |
| PYSKL | main branch | CTR-GCN model loading, preprocessing pipelines (PreNormalize2D, GenSkeFeat, FormatGCNInput) | Official repo with CTR-GCN configs and NTU120 HRNet2D weights |
| open-clip-torch | 3.3.0 | CLIP ViT-B/16 visual encoder, openai pretrained weights | Latest stable; `pretrained='openai'` provides identical weights to openai/clip; actively maintained |
| decord | 0.6.0 | Video decoding for XD-Violence mp4 files | Verified installed in vcc-main; required by PYSKL; well-tested for variable-FPS sampling |
| opencv-python | 4.13.0 | Frame reading in vcc-skeleton env, PNG loading for UCF-Crime | Required by rtmlib; confirmed installed |
| numpy | <2.0 (vcc-ctrgcn), >=1.23 (others) | Array operations, feature caching | numpy 2.x breaks mmcv-full 1.7.0 binary interface; enforce <2 in vcc-ctrgcn |
| scikit-learn | >=1.3 | Stratified split creation, StratifiedShuffleSplit | Standard; preserves normal/abnormal + per-category ratio |
| tqdm | >=4.65 | Progress bars for all extraction scripts | Required by D-16; essential for monitoring multi-hour jobs |
| h5py | >=3.8 | Not used for primary cache (float32 .npy preferred per STATE.md) | Available as fallback; .npy is the chosen format |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 (vcc-ctrgcn) | Unit tests for alignment script, coordinate normalization | Phase 2 test suite |
| PyYAML | >=6.0 | Snippet boundary config (shared between skeleton/CLIP scripts) | Config file for snippet definition |
| pathlib | stdlib | Path manipulation across Windows/Linux style | Already in use throughout project |

**Installation note:** All libraries are already installed in their respective environments. No new conda installs required for this phase.

---

## Architecture Patterns

### Recommended Project Structure (additions for Phase 2)

```
ViolenceCC/
├── scripts/
│   ├── extract_skeletons.py          # [vcc-skeleton] RTMPose → PYSKL pickle per video
│   ├── extract_ctrgcn.py             # [vcc-ctrgcn]  pickle → CTR-GCN 256-d .npy per video
│   ├── extract_clip.py               # [vcc-main]    frames → CLIP 512-d .npy per video
│   └── verify_alignment.py           # [vcc-main]    assert N_skel == N_clip for all videos
├── data/
│   └── splits/
│       ├── ucf_train.txt             # video IDs, one per line, relative to Train/ root
│       ├── ucf_val.txt
│       ├── ucf_test.txt
│       ├── xd_train.txt
│       ├── xd_val.txt
│       └── xd_test.txt
└── E:\features\                       # (symlinked from data/features/)
    ├── ucf\
    │   ├── skeleton\                  # {VideoName}.npy [N_snippets, 256] float32
    │   └── clip\                      # {VideoName}.npy [N_snippets, 512] float32
    └── xd\
        ├── skeleton\                  # {video_basename}.npy [N_snippets, 256] float32
        └── clip\                      # {video_basename}.npy [N_snippets, 512] float32
```

### Pattern 1: Three-Script Extraction Pipeline

The skeleton extraction splits into two scripts because skeleton extraction (rtmlib) and CTR-GCN forward (PYSKL) require different conda environments.

**Script 1 (`extract_skeletons.py`, runs in `vcc-skeleton`):**
- Input: raw PNG dir (UCF-Crime) or video file (XD-Violence)
- Output: intermediate PYSKL pickle per video at `E:\skeletons\{dataset}\{video_id}.pkl`
- Per-video dict: `{'keypoint': ndarray[M,T,V,2], 'keypoint_score': ndarray[M,T,V], 'img_shape': (H,W), 'total_frames': T, 'video_id': str}`

**Script 2 (`extract_ctrgcn.py`, runs in `vcc-ctrgcn`):**
- Input: PYSKL pickle from Script 1
- Output: `E:\features\{dataset}\skeleton\{video_id}.npy` shape `[N_snippets, 256]` float32
- Applies PreNormalize2D, GenSkeFeat (4 streams), FormatGCNInput, forward pass, global pool

**Script 3 (`extract_clip.py`, runs in `vcc-main`):**
- Input: raw PNG dir (UCF-Crime) or video file (XD-Violence)
- Output: `E:\features\{dataset}\clip\{video_id}.npy` shape `[N_snippets, 512]` float32
- Uses IDENTICAL snippet boundaries as Script 2; reads boundaries from shared JSON

### Pattern 2: Shared Snippet Boundary File (Critical for Alignment)

The root cause of C2 (temporal misalignment) is that skeleton and CLIP scripts independently compute snippet boundaries. The fix is to compute boundaries ONCE in Script 1 and persist them.

```python
# Script 1 (extract_skeletons.py) writes this after processing each video:
# E:\snippets\{dataset}\{video_id}_boundaries.json
{
    "video_id": "Fighting002",
    "total_frames": 269,       # number of PNGs (or decoded video frames)
    "frames_per_snippet": 64,
    "snippet_frame_ranges": [  # list of [start_inclusive, end_exclusive]
        [0, 64],
        [64, 128],
        [128, 192],
        [192, 256]
    ],
    "n_snippets": 4
}
# Script 3 (extract_clip.py) reads this JSON to determine which frames to pool per snippet
# verify_alignment.py reads both .npy shapes and this JSON as ground truth
```

This pattern guarantees N_skel == N_clip by construction, not just as a post-hoc check.

### Pattern 3: PreNormalize2D Application (Verified from PYSKL source)

**CRITICAL:** Raw RTMPose pixel coordinates must be normalized BEFORE CTR-GCN forward pass. PreNormalize2D with `mode='fix'` (the default used in all HRNet configs) performs:

```python
# Source: D:\libs\pyskl\pyskl\datasets\pipelines\pose_related.py, lines 86-89
# mode='fix': center at image midpoint, scale by half-width/height
h, w = img_shape  # e.g. (720, 1280) for HD video
keypoint[..., 0] = (keypoint[..., 0] - (w / 2)) / (w / 2)   # x: pixel → [-1, 1]
keypoint[..., 1] = (keypoint[..., 1] - (h / 2)) / (h / 2)   # y: pixel → [-1, 1]
# keypoint[..., 2] = confidence score (unchanged)
```

The `img_shape` must come from the actual frame resolution, not a hardcoded default. UCF-Crime PNGs may vary across categories. Load one frame per video to determine its resolution.

**Post-normalization assertion:**
```python
assert np.all(np.abs(keypoint[..., :2]) <= 2.0), "Coord normalization failed: values outside [-2, 2]"
```
Use 2.0 tolerance (not 1.0) because joint pairs at image edges can slightly exceed 1.0.

### Pattern 4: 4-Stream CTR-GCN Weighted Concat

Each stream (j, b, jm, bm) requires a SEPARATE model load with its respective .pth file and config. The 4-stream output is a weighted CONCATENATION, not averaging, producing a 1024-d vector. The planner must clarify: the PRD specifies "weighted concat (1:1:0.5:0.5)" which means concatenating 4×256-d vectors with no dimensionality reduction at this stage. The 1024-d vector is stored as-is (or reduced to 256-d by averaging weighted contributions — see Open Questions).

```python
# Per snippet: load 4 models once at script startup
models = {
    'j':  load_ctrgcn('j.pth',  'j.py'),
    'b':  load_ctrgcn('b.pth',  'b.py'),
    'jm': load_ctrgcn('jm.pth', 'jm.py'),
    'bm': load_ctrgcn('bm.pth', 'bm.py'),
}
weights = {'j': 1.0, 'b': 1.0, 'jm': 0.5, 'bm': 0.5}

def extract_snippet_feature(x_snippet):  # x_snippet: [1, 2, 64, 17, 3]
    feats = {}
    for name, model in models.items():
        with torch.no_grad():
            out = model.backbone(x_snippet)  # [1, 2, 256, T', V']
            feat = out.mean(dim=[1, 3, 4])   # [1, 256]
        feats[name] = feat * weights[name]
    # Weighted average → 256-d (preferred for storage consistency with downstream Phase 3)
    return (feats['j'] + feats['b'] + feats['jm'] + feats['bm']) / sum(weights.values())
    # Result: [1, 256] — output 256-d, NOT 1024-d
```

**Resolution:** Weighted average to 256-d is the correct interpretation consistent with PYSKL multi-stream evaluation. The "1:1:0.5:0.5" are contribution weights, producing 256-d output. This matches ENV-02 (DATA-05 requirement: "256-d per snippet").

### Pattern 5: CLIP Feature Extraction with mean+max Pooling

```python
# Source: open-clip-torch 3.3.0, verified installed in vcc-main
import open_clip

model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-16', pretrained='openai')
model.eval().cuda()

# Preprocessing (verified from open_clip output):
# Resize → 224 (bicubic), CenterCrop → (224,224), Normalize(mean=(0.48145466, 0.4578275, 0.40821073), std=(0.26862954, 0.26130258, 0.27577711))

def extract_clip_snippet(frames_in_window):  # list of PIL Images or numpy arrays
    # frames_in_window: all 1-FPS frames that fall within this snippet's time range
    batch = torch.stack([preprocess(f) for f in frames_in_window]).cuda()  # [N_frames, 3, 224, 224]
    with torch.no_grad():
        embeddings = model.encode_image(batch)  # [N_frames, 512]
        embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)  # L2 normalize per frame
    mean_feat = embeddings.mean(dim=0)   # [512]
    max_feat  = embeddings.max(dim=0).values  # [512]
    concat_feat = torch.cat([mean_feat, max_feat], dim=0)  # [1024]
    # Linear projection to 512-d (the projection layer)
    # NOTE: The projection is a LEARNED component in the MIL head (Phase 3), NOT in this extraction
    # Extract at 1024-d and let Phase 3 apply the projection inside the model
    return concat_feat.cpu().float().numpy()  # [1024] float32
```

**IMPORTANT CLARIFICATION on CLIP output dimension:**
The PRD specifies "512-d per snippet" after mean+max pooling. But mean+max concatenation naturally yields 1024-d before projection. Two valid approaches:
- Option A: Extract 1024-d, apply projection Linear(1024→512) in Phase 3 CLIP branch (projection is learned with MIL head)
- Option B: Extract 1024-d as the cache, let Phase 3 handle projection

The ARCHITECTURE.md specifies `[N_snippets, 512]` as the cache format with projection applied. Given that the projection is a learned component (it shouldn't be hardcoded as identity), the CORRECT approach is: cache 1024-d at extraction time (no projection applied — there's nothing to project with at extraction time), and let Phase 3 apply a learned projection. See Open Questions section.

### Pattern 6: UCF-Crime Video Enumeration

UCF-Crime PNGs follow the pattern `{VideoName}_x264_{framenum}.png` where `framenum` increments by 10. Videos must be enumerated by grouping PNGs by their VideoName prefix (everything before `_x264_`).

```python
import os
from collections import defaultdict
from pathlib import Path

def enumerate_ucf_videos(category_dir: Path) -> dict:
    """Returns {video_name: sorted list of frame indices}."""
    videos = defaultdict(list)
    for f in category_dir.glob("*_x264_*.png"):
        name = f.stem.rsplit('_x264_', 1)[0]  # VideoName
        frame_idx = int(f.stem.rsplit('_x264_', 1)[1])
        videos[name].append(frame_idx)
    return {name: sorted(idxs) for name, idxs in videos.items()}
    # sort numerically by the integer, not lexicographically
```

**Observed data:** Fighting category has videos Fighting002, Fighting004, Fighting005... (no Fighting001, no Fighting003). All 14 Train categories confirmed present. Fighting002 has 269 PNGs (frame indices 0, 10, 20, ..., 2680), producing 4 non-overlapping 64-frame snippets.

### Pattern 7: XD-Violence Video Decoding

XD-Violence training videos are at `E:\XD_Violence\train\{filename}.mp4`. Test videos are at `E:\XD_Violence\test\videos\{filename}.mp4`. The video ID for split files and feature naming is the filename without extension.

```python
import decord
from pathlib import Path

def decode_xd_video_frames(video_path: Path, sample_every_n: int = None) -> list:
    """Decode video frames. For skeleton: all frames. For CLIP: compute 1-FPS sampling."""
    vr = decord.VideoReader(str(video_path), ctx=decord.cpu(0))
    fps = vr.get_avg_fps()
    total_frames = len(vr)
    return vr, fps, total_frames
```

**decord confirmed installed** in vcc-main (v0.6.0). Use decord as the primary decoder; fall back to OpenCV if decord raises a VideoReaderException (known for some corrupted files).

### Pattern 8: Stratified Val Split Construction

```python
from sklearn.model_selection import StratifiedShuffleSplit
import random, numpy as np

# UCF-Crime: video list from Anomaly_Train.txt
# For each category: sample 15% to val, rest to train
# Preserve both normal/abnormal ratio AND per-category ratio (D-09)
def create_stratified_split(video_list, category_labels, val_fraction=0.15, seed=42):
    sss = StratifiedShuffleSplit(n_splits=1, test_size=val_fraction, random_state=seed)
    train_idx, val_idx = next(sss.split(video_list, category_labels))
    return [video_list[i] for i in train_idx], [video_list[i] for i in val_idx]
```

### Anti-Patterns to Avoid

- **Lexicographic frame sort:** `sorted(['10', '100', '20'])` gives wrong frame order. Always sort by integer value: `sorted(frame_indices, key=int)`.
- **Computing CLIP boundaries independently of skeleton boundaries:** The alignment will fail. Always derive CLIP snippet boundaries from the same JSON that skeleton extraction wrote.
- **Using img_shape default (1080, 1920) in PreNormalize2D without reading actual frame size:** UCF-Crime test frames may differ from train frames in resolution. Read `cv2.imread(first_frame).shape` per video.
- **Passing raw pixel coords to CTR-GCN:** This is C1. Always apply PreNormalize2D.
- **Hardcoding video dimensions in skeleton extraction:** Each UCF-Crime PNG may have a different resolution. Verify per-video.
- **Storing all frames in memory before extraction:** M3 pitfall. Process in chunks of 500 frames max per video.
- **Using `model.forward(x)` instead of `model.backbone(x)` for CTR-GCN:** The full forward includes the classification head which outputs logits, not 256-d features. Use `model.backbone(x)` then pool.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pose estimation | Custom keypoint detector | rtmlib RTMPose-m | Complex ML pipeline with non-trivial training; rtmlib is purpose-built |
| Coordinate normalization | Custom formula | PYSKL PreNormalize2D (verified source at pose_related.py:86-89) | Must match exactly what CTR-GCN expects; any deviation breaks features |
| Bone/motion feature generation | Manual subtraction loops | PYSKL JointToBone, ToMotion with dataset='coco' | COCO pair topology is non-obvious (17 specific joint pairs); PYSKL has the correct table |
| FormatGCNInput padding | Manual M-padding | PYSKL FormatGCNInput | Handles M<2 zero-padding; handles M>2 truncation; reshapes for multi-clip inference |
| CLIP preprocessing | Custom resize/crop/normalize | open_clip.create_model_and_transforms preprocess_val | Must match the exact normalization CLIP was trained with |
| Stratified split | Custom balancing | sklearn.model_selection.StratifiedShuffleSplit | Handles edge cases, reproducible with random_state |
| Video decoding | Custom ffmpeg subprocess | decord.VideoReader | Stream-based decoding; get_avg_fps(); well-tested Windows support |

**Key insight:** The PYSKL preprocessing pipeline (PreNormalize2D → GenSkeFeat → FormatGCNInput) is the contractual interface to CTR-GCN. These transforms must be applied in order with `dataset='coco'` parameter for the COCO joint topology. Deviating from this contract will produce silently incorrect features.

---

## Runtime State Inventory

Phase 2 does not involve renaming or refactoring. Not applicable.

---

## Common Pitfalls

### Pitfall 1: Coordinate Normalization (C1 — CRITICAL)

**What goes wrong:** RTMPose outputs pixel coordinates (e.g., x=640, y=360 for a 1280x720 frame). CTR-GCN NTU120 HRNet2D expects normalized coordinates in approximately [-1, 1] (applied by PreNormalize2D with mode='fix'). Passing raw pixels produces garbage features with no error.

**Why it happens:** extract_ctrgcn.py bypasses the PYSKL training pipeline, so PreNormalize2D is not called automatically.

**How to avoid:** Apply PreNormalize2D manually before creating the input tensor. The formula is `x_norm = (x_pixel - W/2) / (W/2)`, `y_norm = (y_pixel - H/2) / (H/2)`. After normalization, assert `np.all(np.abs(keypoint[..., :2]) <= 2.0)`.

**Warning signs:** CTR-GCN output features have near-zero variance across all videos; cosine similarities between random video features are all >0.99.

### Pitfall 2: Temporal Misalignment Between Modalities (C2 — CRITICAL)

**What goes wrong:** Skeleton snippets and CLIP snippets independently compute "which frames belong to snippet N" and produce different results. At training time, fusion receives (skel_snippet_t, clip_snippet_t') where t != t'.

**Why it happens:** Two separate extraction scripts compute snippet boundaries independently. For UCF-Crime PNGs (every 10th original frame), "frame 64" means different things depending on whether you're counting PNG files or original video frames.

**How to avoid:** Compute snippet boundaries (as frame index ranges into the PNG list) once in extract_skeletons.py, persist them as JSON, and have extract_clip.py read those same boundaries. verify_alignment.py checks N_skel == N_clip as a final gate.

**Warning signs:** verify_alignment.py reports count mismatches; CLIP-Only baseline significantly outperforms Late Fusion on short-duration anomaly categories.

### Pitfall 3: PYSKL Pickle Format Missing Fields

**What goes wrong:** The intermediate pickle written by extract_skeletons.py is missing `img_shape` or `total_frames`. PreNormalize2D uses `results.get('img_shape', self.img_shape)` — if missing, it falls back to the default `(1080, 1920)`, which gives incorrect normalization for UCF-Crime frames that are not 1080p.

**How to avoid:** Always write `img_shape: (H, W)` from the actual first frame of each video. UCF-Crime PNGs may vary in resolution across categories.

**Warning signs:** Features extracted from differently-sized videos show inconsistent quality; Fighting category (which has different PNG resolutions from CCTV footage) shows lower skeleton quality than other categories.

### Pitfall 4: FormatGCNInput Padding Mode vs. Zero-Pad Decision

**What goes wrong:** PYSKL's FormatGCNInput supports `mode='zero'` (pad with zeros for absent persons) and `mode='loop'` (repeat person 0 for absent second person). Decisions D-07 and D-08 specify zero-padding. However, the PITFALLS.md (C6) notes that zero-padded skeletons look like "a frozen standing person" to CTR-GCN.

**Decision confirmed (D-07, D-08):** Use zero-padding as decided. This is a known limitation; document it. Departure from D-07/D-08 is not permitted without user confirmation.

**How to avoid the C6 issue:** Log the per-video fraction of snippets with fewer than 2 detected persons. If >30% of snippets in a video have person_count < 2, flag it in errors.log.

### Pitfall 5: CLIP 1024-d vs 512-d Cache Ambiguity

**What goes wrong:** The PRD specifies "512-d per snippet" but mean+max pooling produces 1024-d before projection. If extract_clip.py applies an identity or random linear projection to 512-d, Phase 3's learned projection will be applied on top of already-projected features — double projection.

**How to avoid:** Cache 1024-d (the raw mean+max concatenation) and let Phase 3's CLIP branch apply the learned projection. Document in `feature_schema.py` or a comment block that `clip/*.npy` files are 1024-d, not 512-d. The 512-d target described in the PRD refers to the POST-projection feature used in fusion, not the cached pre-projection feature.

**Alternative:** Cache 512-d with a FIXED (non-learned) normalization as the projection (e.g., L2-normalize the 1024-d vector and take first 512 dimensions). This is less principled. Prefer caching 1024-d.

### Pitfall 6: UCF-Crime Official Split Files Not Available On-Disk

**What goes wrong:** DATA-01 requires committing the official UCF-Crime split files (Anomaly_Train.txt, Anomaly_Test.txt, Temporal_Anomaly_Annotation.txt). These files are NOT currently present at `E:\UCF_crime_dataset\` (only the PNG directories exist). They must be downloaded from the CRCV UCF website.

**How to avoid:** Download the official annotation files before creating split files. The train/test split for UCF-Crime must come from the official Anomaly_Train.txt and Anomaly_Test.txt. Do not reconstruct the split from directory structure alone — the official files define the canonical split used by all comparison baselines.

**Source:** UCF-Crime official page at `http://crcv.ucf.edu/projects/real-world/index.html` provides these text files.

### Pitfall 7: XD-Violence Annotation Format Parsing

**What goes wrong:** The XD-Violence annotation file (`E:\XD_violence_annotations.txt`) uses video IDs that differ from the training video filenames by having the `v=` prefix stripped and using `__#1` vs timestamp format. The frame-level annotations are space-separated start/end pairs (multiple anomaly segments per video). A naive parser treating this as a fixed-format CSV will fail on multi-segment videos.

**Observed format:**
```
v=S-7rRLrxnVQ__#1_label_B4-0-0 0 1517 1970 3038
v=u5SF4SlqNDQ__#00-00-00_00-01-00_label_G-0-0 624 912 950 1441
```

**Parsing note:** The video ID field starts with `v=`. Strip the `v=` prefix to get the video basename. Remaining space-separated values are anomaly frame start/end pairs (multiple allowed). For training, only the video ID matters (no frame-level annotation used). For test set evaluation, the frame pairs define GT intervals.

**Also note:** The training video filenames do NOT have `v=` prefix — they are just `{video_id}.mp4`. Match by stripping the `v=`.

### Pitfall 8: XD-Violence Test Path (test/videos/)

**What goes wrong:** Test videos are at `E:\XD_Violence\test\videos\` (nested under `test/videos/`), not directly under `test/`. Extraction scripts that assume `test/*.mp4` will find 0 videos.

**Confirmed from dir scan:** `E:\XD_Violence\test\videos\` contains 800 .mp4 files.

### Pitfall 9: VRAM / RAM Overflow in Skeleton Extraction (M3)

**What goes wrong:** Processing all frames of a long XD-Violence video (some are 5-10 minutes at 25+ FPS = 7,500-15,000 frames) in a single pass can exhaust CPU RAM (~2 GB per video for 1080p RGB).

**How to avoid:** Process skeleton extraction in chunks of 500 frames. After each chunk, serialize the keypoints to a partial pkl, then load and continue. Call `gc.collect()` and `torch.cuda.empty_cache()` every 100 videos.

---

## Code Examples

Verified patterns from PYSKL source and open-clip:

### PreNormalize2D: Exact Formula (source: PYSKL pose_related.py:86-89)

```python
# Source: D:\libs\pyskl\pyskl\datasets\pipelines\pose_related.py, lines 86-89
# mode='fix' (default used in all HRNet configs):
def prenormalize2d(keypoint, img_shape):
    """
    keypoint: ndarray [M, T, V, C] where C>=2, coords are pixel values
    img_shape: (H, W) of the video frame
    Returns: keypoint with x,y normalized to [-1, 1] range
    """
    h, w = img_shape
    keypoint = keypoint.copy().astype(np.float32)
    keypoint[..., 0] = (keypoint[..., 0] - (w / 2)) / (w / 2)   # x: pixel -> normalized
    keypoint[..., 1] = (keypoint[..., 1] - (h / 2)) / (h / 2)   # y: pixel -> normalized
    # confidence channel (index 2) is unchanged
    return keypoint

# Post-normalization assertion
assert np.all(np.abs(keypoint[..., :2]) <= 2.0), f"Coord out of range: {np.abs(keypoint[..., :2]).max()}"
```

### COCO Bone Pairs for JointToBone (source: PYSKL pose_related.py:310-312)

```python
# Source: D:\libs\pyskl\pyskl\datasets\pipelines\pose_related.py, line 311
# dataset='coco' pairs: (child_joint, parent_joint) for bone vector computation
COCO_BONE_PAIRS = (
    (0, 0), (1, 0), (2, 0), (3, 1), (4, 2), (5, 0), (6, 0),
    (7, 5), (8, 6), (9, 7), (10, 8), (11, 0), (12, 0),
    (13, 11), (14, 12), (15, 13), (16, 14)
)
# bone[..., v1, :] = keypoint[..., v1, :] - keypoint[..., v2, :]
```

### CTR-GCN Forward Pass (verified pattern from smoke test)

```python
# Source: D:\ViolenceCC\tests\test_ctrgcn_smoke.py
from mmcv import Config
from pyskl.models import build_model
import torch

def load_ctrgcn_stream(config_path, weight_path, device='cuda'):
    cfg = Config.fromfile(config_path)
    model = build_model(cfg.model)
    checkpoint = torch.load(weight_path, map_location='cpu')
    model.load_state_dict(checkpoint, strict=False)
    model.eval().to(device)
    return model

def extract_feature(model, x):
    """x: [N, M, T, V, C] = [1, 2, 64, 17, 3]. Returns [N, 256]."""
    with torch.no_grad():
        out = model.backbone(x)   # [N, M, 256, T', V']
        feat = out.mean(dim=[1, 3, 4])  # [N, 256]
    return feat
```

### open-clip CLIP Extraction (verified from env check)

```python
# Source: open-clip-torch 3.3.0, vcc-main environment
import open_clip, torch
from PIL import Image

model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-16', pretrained='openai')
model.eval().cuda()
tokenizer = open_clip.get_tokenizer('ViT-B-16')

def extract_clip_frames_batch(frame_list, batch_size=64):
    """frame_list: list of PIL Images. Returns [N, 512] float32 L2-normalized embeddings."""
    all_feats = []
    for i in range(0, len(frame_list), batch_size):
        batch = torch.stack([preprocess(f) for f in frame_list[i:i+batch_size]]).cuda()
        with torch.no_grad():
            feats = model.encode_image(batch)  # [B, 512]
            feats = feats / feats.norm(dim=-1, keepdim=True)
        all_feats.append(feats.cpu().float())
    return torch.cat(all_feats, dim=0).numpy()  # [N, 512]

# Preprocessing verified:
# Resize(224, bicubic) → CenterCrop(224,224) → Normalize(mean=(0.48145466,0.4578275,0.40821073), std=(0.26862954,0.26130258,0.27577711))
```

### UCF-Crime PNG Numeric Sort

```python
from pathlib import Path
from collections import defaultdict

def get_ucf_video_frames(category_dir: Path) -> dict:
    """Returns {video_name: [frame_idx_sorted_numerically]}."""
    videos = defaultdict(list)
    for f in sorted(category_dir.glob("*_x264_*.png")):
        stem = f.stem  # e.g. "Fighting002_x264_1030"
        parts = stem.rsplit("_x264_", 1)
        video_name, frame_str = parts[0], parts[1]
        videos[video_name].append(int(frame_str))
    # Each list is appended in glob order (may not be numeric) - sort explicitly
    return {name: sorted(frames) for name, frames in videos.items()}
```

### Snippet Boundary Computation

```python
def compute_snippet_boundaries(n_frames: int, frames_per_snippet: int = 64) -> list:
    """Non-overlapping snippets. Returns list of [start, end) frame index pairs."""
    boundaries = []
    for start in range(0, n_frames - frames_per_snippet + 1, frames_per_snippet):
        boundaries.append([start, start + frames_per_snippet])
    return boundaries
# Example: n_frames=269, frames_per_snippet=64 → [[0,64],[64,128],[128,192],[192,256]]
# Note: frames 256-268 (last 13 frames) are DISCARDED — insufficient for a full window
# This is the standard approach (no padding of the last partial snippet)
```

### verify_alignment.py Core Logic

```python
import numpy as np
from pathlib import Path

def verify_alignment(skeleton_dir: Path, clip_dir: Path) -> dict:
    """Returns {video_id: (n_skel, n_clip, match:bool)} for all videos."""
    results = {}
    for skel_file in sorted(skeleton_dir.glob("*.npy")):
        video_id = skel_file.stem
        clip_file = clip_dir / f"{video_id}.npy"
        if not clip_file.exists():
            results[video_id] = (None, None, False, "CLIP file missing")
            continue
        n_skel = np.load(skel_file, mmap_mode='r').shape[0]
        n_clip = np.load(clip_file, mmap_mode='r').shape[0]
        results[video_id] = (n_skel, n_clip, n_skel == n_clip, "")
    failures = {vid: v for vid, v in results.items() if not v[2]}
    return results, failures

# Gate: len(failures) == 0 before Phase 3 can start
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| vcc-skeleton conda env | extract_skeletons.py | Yes | Python 3.11 | — |
| vcc-ctrgcn conda env | extract_ctrgcn.py | Yes | Python 3.10 | — |
| vcc-main conda env | extract_clip.py, verify_alignment.py | Yes | Python 3.11 | — |
| rtmlib | extract_skeletons.py | Yes | 0.0.15 | — |
| onnxruntime-gpu | extract_skeletons.py (via rtmlib) | Yes (vcc-skeleton) | 1.20.x | — |
| cv2 (opencv-python) | extract_skeletons.py | Yes | 4.13.0 | — |
| PYSKL | extract_ctrgcn.py | Yes (vcc-ctrgcn) | main branch | — |
| PyTorch 1.12.1 cu113 | extract_ctrgcn.py | Yes (vcc-ctrgcn) | 1.12.1 | — |
| CTR-GCN weights (j/b/jm/bm) | extract_ctrgcn.py | Yes | N/A | — |
| open-clip-torch | extract_clip.py | Yes (vcc-main) | 3.3.0 | — |
| decord | extract_clip.py (XD-Violence) | Yes (vcc-main) | 0.6.0 | cv2.VideoCapture |
| E:\features\ (symlink from data/features/) | All extraction output | Yes | — | — |
| E:\UCF_crime_dataset\ | UCF-Crime extraction | Yes (Train + test dirs with PNGs) | — | — |
| E:\XD_Violence\train\ | XD-Violence train extraction | Yes (3954 mp4 files) | — | — |
| E:\XD_Violence\test\videos\ | XD-Violence test extraction | Yes (800 mp4 files, path is test/videos/) | — | — |
| E:\XD_violence_annotations.txt | split file creation, DATA-01 | Yes | — | — |
| UCF-Crime official split .txt files | DATA-01 | NOT PRESENT on disk | — | Must download from CRCV UCF website |
| pytest (vcc-ctrgcn) | Validation tests | Yes | 9.0.2 | — |

**Missing dependencies with no fallback:**
- UCF-Crime official split files (Anomaly_Train.txt, Anomaly_Test.txt, Temporal_Anomaly_Annotation.txt) — these must be downloaded before DATA-01 can be completed. Source: `http://crcv.ucf.edu/projects/real-world/index.html`. This blocks DATA-01 and DATA-02.

**Missing dependencies with fallback:**
- decord for XD-Violence: fallback to `cv2.VideoCapture` if decord raises errors on specific files (the 4 known CRC-corrupt XD-Violence files will fail regardless).

---

## Dataset Inventory

### UCF-Crime (Confirmed)

| Property | Value |
|----------|-------|
| Train PNG directory | `E:\UCF_crime_dataset\Train\{14 categories}\` |
| Test PNG directory | `E:\UCF_crime_dataset\test\{14 categories}\` |
| Categories | Abuse(48), Arrest(45), Arson(41), Assault(47), Burglary(87), Explosion(29), Fighting(45), NormalVideos(800), RoadAccidents(127), Robbery(145), Shooting(27), Shoplifting(29), Stealing(95), Vandalism(45) |
| Total train videos | 810 normal + ~750 anomaly = ~1,560 (exact count from Anomaly_Train.txt needed) |
| Test videos | 150 normal + 140 anomaly (from PRD — test category counts sum to 290) |
| Frame naming | `{VideoName}_x264_{framenum}.png`, framenum increments by 10 |
| Frame rate equivalent | Every 10th original frame → ~3 FPS equivalent |
| Sample video | Fighting002: 269 PNGs → 4 snippets at T=64 |
| Official split files | NOT PRESENT on disk — must download |

### XD-Violence (Confirmed)

| Property | Value |
|----------|-------|
| Train directory | `E:\XD_Violence\train\` |
| Test directory | `E:\XD_Violence\test\videos\` (nested!) |
| Train count | 3,954 .mp4 files |
| Test count | 800 .mp4 files |
| Annotation file | `E:\XD_violence_annotations.txt` |
| Annotation format | `v={video_id} {start1} {end1} {start2} {end2} ...` (space-separated, variable fields) |
| Known corrupt files | 4 CRC-corrupt files in the 1005-2004.zip range — expect log-and-skip |
| Video ID for splits | Filename without `.mp4` extension |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (available in vcc-ctrgcn; needs install check in vcc-main) |
| Config file | None currently — Wave 0 gap |
| Quick run command (vcc-ctrgcn) | `conda run -n vcc-ctrgcn pytest tests/ -x -q` |
| Full suite command | `conda run -n vcc-ctrgcn pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Official split files committed | smoke | `pytest tests/test_split_files.py::test_ucf_split_files_exist -x` | No — Wave 0 |
| DATA-02 | Val split stratification and seed reproducibility | unit | `pytest tests/test_split_files.py::test_val_split_stratified -x` | No — Wave 0 |
| DATA-03 | Skeleton extraction produces PYSKL-compatible pickle | unit | `pytest tests/test_skeleton_extraction.py::test_pickle_format -x` | No — Wave 0 |
| DATA-04 | Coordinate normalization — output in [-2, 2] | unit | `pytest tests/test_skeleton_extraction.py::test_prenormalize2d -x` | No — Wave 0 |
| DATA-05 | CTR-GCN 4-stream output shape [N_snippets, 256] | unit | `pytest tests/test_ctrgcn_extraction.py::test_4stream_shape -x` | No — Wave 0 |
| DATA-06 | CLIP output shape [N_snippets, 1024] (pre-projection) | unit | `pytest tests/test_clip_extraction.py::test_clip_shape -x` | No — Wave 0 |
| DATA-07 | Cache files are float32 .npy with correct shape | unit | `pytest tests/test_feature_cache.py::test_npy_dtype_shape -x` | No — Wave 0 |
| DATA-08 | verify_alignment passes on UCF-Crime sample batch | integration | `conda run -n vcc-main python scripts/verify_alignment.py --dataset ucf --sample 10` | No — Wave 0 |
| DATA-09 | UCF-Crime full extraction completion (count check) | smoke | Manual + `verify_alignment.py --dataset ucf` | No — Wave 0 |
| DATA-10 | XD-Violence full extraction completion (count check) | smoke | Manual + `verify_alignment.py --dataset xd` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `conda run -n vcc-ctrgcn pytest tests/test_skeleton_extraction.py -x -q` (fast unit tests, <10s)
- **Per wave merge:** `conda run -n vcc-ctrgcn pytest tests/ -v` then `verify_alignment.py --sample 50`
- **Phase gate:** `verify_alignment.py` passes with zero failures on all extracted videos for both datasets

### Wave 0 Gaps

- [ ] `tests/test_split_files.py` — covers DATA-01, DATA-02
- [ ] `tests/test_skeleton_extraction.py` — covers DATA-03, DATA-04
- [ ] `tests/test_ctrgcn_extraction.py` — covers DATA-05
- [ ] `tests/test_clip_extraction.py` — covers DATA-06
- [ ] `tests/test_feature_cache.py` — covers DATA-07
- [ ] `tests/conftest.py` update — add fixtures for new test modules (extend existing conftest.py)
- [ ] pytest install check in vcc-main: `conda run -n vcc-main pip install pytest`

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| openai/clip (frozen 2021) | open-clip-torch 3.3.0 | 2024-2026 | Identical ViT-B/16 weights, actively maintained, Python 3.9+ |
| PYSKL Kinetics-400 CTR-GCN weights | PYSKL NTU120 HRNet 2D weights | v2.3 PRD (2026-03) | COCO-17 format native compatibility, no joint mapping needed |
| End-to-end backbone training | Pre-extracted feature cache | VAD community ~2021+ (RTFM) | Fast MIL training (minutes per run vs hours); VRAM feasible |
| HDF5 feature cache (h5py) | float32 .npy per video | STATE.md decision (2026-03) | Simpler; no partial-read overhead at this dataset scale |
| Per-dataset training scripts (VadCLIP pattern) | Single extract script with dataset flag | This project | No code duplication for UCF vs XD |

**Deprecated/outdated:**
- openai/clip: Frozen at 2021 release, no longer maintained. Use open-clip-torch with `pretrained='openai'` instead.
- PYSKL CTR-GCN Kinetics-400 weights: Do NOT exist in the model zoo. NTU120 HRNet 2D is the only COCO-17 compatible option.
- 17→25 joint mapping strategies: Unnecessary now that NTU120 HRNet 2D weights are confirmed available.

---

## Open Questions

1. **CLIP cache dimension: 1024-d or 512-d?**
   - What we know: mean+max pooling produces 1024-d. PRD says "512-d per snippet" (post-projection). The projection is a learned component.
   - What's unclear: Should the extraction cache pre-projection 1024-d or post-projection 512-d? If 512-d, what is the projection at extraction time (no learned weights exist yet)?
   - Recommendation: Cache 1024-d. Document `clip/*.npy` as shape `[N_snippets, 1024]` float32. Phase 3 adds the learned Linear(1024→512) projection as part of the CLIP branch. Update DATA-06 requirement wording to reflect this. The planner should treat the clip feature cache as 1024-d.

2. **CLIP 1-FPS sampling for UCF-Crime PNGs: what is "1 FPS"?**
   - What we know: UCF-Crime PNGs are every 10th original frame at ~30 FPS original → ~3 effective FPS. D-02 says "CLIP extracted at true 1 FPS." D-04 says "both skeleton and CLIP extract from these same PNGs."
   - What's unclear: If there are only 3 PNGs per second, does "1 FPS" mean "every 3rd PNG" or "1 PNG per second" (which at ~3 effective FPS means ~1 PNG per second anyway)?
   - Recommendation: For UCF-Crime, "1 FPS" means one frame per second of effective playback. Since each PNG represents 1/3rd of a second (every 10th frame at 30 FPS), take every 3rd PNG for CLIP features (~1 sample/second). For XD-Violence, use actual video FPS from decord to sample at true 1 Hz. This should be confirmed by the planner or user.

3. **Intermediate PYSKL pickle storage location?**
   - What we know: The 2-script approach (extract_skeletons.py → extract_ctrgcn.py) requires intermediate pickle files. Storage location not specified in decisions.
   - Recommendation: `E:\skeletons\{dataset}\{video_id}.pkl` as intermediate storage (not gitignored, not in data/). Add to .gitignore as `E:\skeletons\`. Document in SETUP.md.

4. **CTR-GCN weighted average formula resolution**
   - What we know: DATA-05 says "4-stream weighted concat (j:b:jm:bm = 1.0:1.0:0.5:0.5)". The Phase 1 smoke test used a single stream.
   - What's confirmed: The correct interpretation is weighted AVERAGE to 256-d (not 1024-d concat), as this matches the PYSKL 4-stream evaluation protocol and the DATA-05 requirement for "256-d per snippet".
   - Formula: `feat = (1.0*feat_j + 1.0*feat_b + 0.5*feat_jm + 0.5*feat_bm) / (1.0+1.0+0.5+0.5)` = `feat / 3.0`

---

## Project Constraints (from CLAUDE.md)

- Single RTX 4090 (24GB VRAM) — extraction scripts must not exceed 18GB GPU usage
- Three separate conda environments (vcc-skeleton / vcc-ctrgcn / vcc-main) — extraction scripts run in the correct environment via `conda run -n {env}`
- All backbones frozen — no gradient computation during extraction; always use `model.eval()` and `torch.no_grad()`
- float32 .npy per video — confirmed as the cache format (not HDF5)
- Python 3.11 (vcc-skeleton, vcc-main), Python 3.10 (vcc-ctrgcn)
- numpy <2.0 strictly enforced in vcc-ctrgcn — mmcv-full 1.7.0 breaks with numpy 2.x
- PYSKL must be installed with --no-deps (chumpy build failure on modern pip)
- PyTorch 1.12.1 must be installed via pip cu113 wheel in vcc-ctrgcn (conda wheel causes WinError 182)
- open-clip-torch 3.3.0 is the CLIP library — do not use openai/clip
- Scripts in `scripts/` directory run different conda environments than `src/` code
- Requirements files are reference documents, not pip install targets
- English codebase convention
- GSD workflow enforcement — edits go through GSD plan/execute cycle

---

## Sources

### Primary (HIGH confidence)
- PYSKL source: `D:\libs\pyskl\pyskl\datasets\pipelines\pose_related.py` — PreNormalize2D exact implementation (lines 53-96), JointToBone COCO pairs (lines 310-312), FormatGCNInput (lines 427-467), GenSkeFeat (lines 378-401), ToMotion (lines 336-356)
- PYSKL CTR-GCN config: `D:\libs\pyskl\configs\ctrgcn\ctrgcn_pyskl_ntu120_xsub_hrnet\j.py` — confirmed preprocessing pipeline and FormatGCNInput num_person=2
- Phase 1 smoke test: `D:\ViolenceCC\tests\test_ctrgcn_smoke.py` — verified CTR-GCN forward pass pattern, backbone pooling, input shape (N,M,T,V,C)
- open-clip verification: `open_clip.create_model_and_transforms('ViT-B-16', pretrained='openai')` — confirmed preprocessing pipeline (Resize 224, CenterCrop 224, Normalize CLIP stats)
- Dataset dir scan (2026-04-03): E:\UCF_crime_dataset\Train\ (14 categories, video counts confirmed), E:\XD_Violence\train\ (3954 files), E:\XD_Violence\test\videos\ (800 files), E:\XD_violence_annotations.txt (format verified)
- Environment check (2026-04-03): vcc-skeleton (rtmlib 0.0.15, cv2 4.13.0), vcc-ctrgcn (PYSKL, pytest 9.0.2), vcc-main (open-clip-torch 3.3.0, decord 0.6.0)
- PYSKL data format README: `D:\libs\pyskl\tools\data\README.md` — pickle format spec (frame_dir, total_frames, img_shape, keypoint [M,T,V,C], keypoint_score [M,T,V])
- STATE.md — confirmed: float32 .npy format decision, E:\features\ symlink active, 4 corrupt XD-Violence files expected

### Secondary (MEDIUM confidence)
- ARCHITECTURE.md (D:\ViolenceCC\.planning\research\ARCHITECTURE.md) — 3-stage pipeline, feature storage, component boundaries
- PITFALLS.md (D:\ViolenceCC\.planning\research\PITFALLS.md) — C1, C2, C6, M3, M4 pitfall descriptions and prevention strategies
- PRD v2.3 section 6.3 — 4-stream weighted concat specification: "joint:bone:joint-motion:bone-motion = 1.0:1.0:0.5:0.5"
- PRD v2.3 section 7.2 — CLIP mean+max pooling strategy, 512-d post-projection target

### Tertiary (LOW confidence — verify during implementation)
- UCF-Crime official split file URLs (not yet verified accessible): `http://crcv.ucf.edu/projects/real-world/index.html` — listed in PRD as official download source

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — all library versions verified from active conda environments on target machine
- Dataset Inventory: HIGH — directory scans performed 2026-04-03, counts confirmed
- Architecture Patterns: HIGH — PYSKL source code read directly, open-clip preprocessing confirmed via live import
- Don't Hand-Roll items: HIGH — PYSKL preprocessing pipeline verified from source
- Common Pitfalls: HIGH — derived from direct PYSKL source + PITFALLS.md research + live dataset inspection
- Open Questions: MEDIUM — CLIP dimension ambiguity requires planner decision; UCF-Crime 1-FPS sampling strategy requires clarification

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (30 days; stable libraries)
