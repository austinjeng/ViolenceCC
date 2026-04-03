# Phase 2: Feature Extraction Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 02-feature-extraction-pipeline
**Areas discussed:** Temporal granularity, Multi-person skeleton, Val split + split files, Extraction orchestration

---

## Temporal Granularity

### Q1: Skeleton temporal granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Sliding window | CTR-GCN processes non-overlapping 64-frame windows. Compact storage, natural for GCN temporal modeling. Phase 3 resamples to T=32. | ✓ |
| Per-frame with pooling | Overlapping windows centered on each frame. Maximum flexibility but ~10x larger cache and much slower. | |
| Fixed T=32 segments | Divide video into exactly 32 segments upfront. Locks T at extraction time. | |

**User's choice:** Sliding window (recommended)
**Notes:** None

### Q2: CLIP temporal approach

| Option | Description | Selected |
|--------|-------------|----------|
| True 1 FPS | Sample one frame per second. Phase 3 resamples to T=32 independently. Standard practice (VadCLIP). | ✓ |
| Match skeleton boundaries | Pool CLIP features within each skeleton snippet window. Couples the two pipelines. | |

**User's choice:** True 1 FPS (recommended)
**Notes:** None

### Q3: CTR-GCN window size

| Option | Description | Selected |
|--------|-------------|----------|
| T=64 | Matches pretrained checkpoint config. Non-overlapping windows. Last window zero-padded if needed. | ✓ |
| T=48 | Shorter windows, more snippets, but mismatches pretrained config. | |
| You decide | Claude picks based on standard CTR-GCN usage. | |

**User's choice:** T=64 (recommended)
**Notes:** None

### Q4: UCF-Crime frame handling

| Option | Description | Selected |
|--------|-------------|----------|
| Use PNGs as-is | Treat ~3fps PNGs as the video. Both modalities see same frames. No video decoding needed. | ✓ |
| Decode original videos | Go back to original video files for full framerate. Higher resolution but more complex. | |

**User's choice:** Use PNGs as-is (recommended)
**Notes:** None

---

## Multi-person Skeleton

### Q1: Top-2 person selection criterion

| Option | Description | Selected |
|--------|-------------|----------|
| Highest confidence | Sort by mean keypoint confidence, take top-2. Standard practice. | ✓ |
| Largest bounding box | Sort by bbox area, take top-2. Prioritizes people closest to camera. | |
| You decide | Claude picks based on PYSKL conventions. | |

**User's choice:** Highest confidence (recommended)
**Notes:** None

### Q2: Handling 0-person frames

| Option | Description | Selected |
|--------|-------------|----------|
| Zero-pad | Fill both slots with all-zero keypoints. Preserves temporal alignment. | ✓ |
| Interpolate from neighbors | Copy skeleton from nearest valid frame. More complex, risks propagating errors. | |
| You decide | Claude picks based on PYSKL examples. | |

**User's choice:** Zero-pad (recommended)
**Notes:** None

### Q3: Minimum confidence threshold

| Option | Description | Selected |
|--------|-------------|----------|
| No threshold | Accept all detections. Low-confidence detections still carry signal. | ✓ |
| Threshold at 0.3 | Discard detections with mean confidence < 0.3. Filters noise. | |
| You decide | Claude picks based on RTMPose characteristics. | |

**User's choice:** No threshold (recommended)
**Notes:** None

### Q4: Single-person frames (M=2 required)

| Option | Description | Selected |
|--------|-------------|----------|
| Zero-pad slot 2 | Second person slot all zeros. Standard PYSKL behavior. | ✓ |
| Duplicate person 1 | Copy person 1 into slot 2. Could confuse model. | |

**User's choice:** Zero-pad slot 2 (recommended)
**Notes:** None

---

## Val Split + Split Files

### Q1: Stratification method

| Option | Description | Selected |
|--------|-------------|----------|
| By category | Maintain normal/abnormal AND per-category ratio. Sample 15% from each category. | ✓ |
| Binary only | Only maintain normal vs abnormal ratio. Simpler but some categories may be absent. | |
| You decide | Claude picks best stratification for MIL training. | |

**User's choice:** By category (recommended)
**Notes:** None

### Q2: Which datasets get val splits

| Option | Description | Selected |
|--------|-------------|----------|
| Both datasets | UCF-Crime and XD-Violence both get 15% val splits. | ✓ |
| UCF-Crime only | Only split UCF-Crime. Use XD-Violence fully for training. | |

**User's choice:** Both datasets (recommended)
**Notes:** None

### Q3: Seed value

| Option | Description | Selected |
|--------|-------------|----------|
| 42 | Standard ML convention seed. | ✓ |
| 2026 | Year-based seed. | |
| You decide | Claude picks a reasonable seed. | |

**User's choice:** 42 (recommended)
**Notes:** None

### Q4: Split file format

| Option | Description | Selected |
|--------|-------------|----------|
| One video ID per line | Simple .txt files. Easy to parse, git-diffable. | ✓ |
| CSV with metadata | CSV with video_id, split, category, label columns. More structured but overkill. | |

**User's choice:** One video ID per line (recommended)
**Notes:** None

---

## Extraction Orchestration

### Q1: Processing order

| Option | Description | Selected |
|--------|-------------|----------|
| UCF-Crime first | Smaller dataset, PNG-based. Validates pipeline before tackling XD-Violence. | ✓ |
| XD-Violence first | Larger dataset first. Bugs found late are more costly. | |
| You decide | Claude picks most efficient order. | |

**User's choice:** UCF-Crime first (recommended)
**Notes:** None

### Q2: Interruption handling

| Option | Description | Selected |
|--------|-------------|----------|
| Skip-if-exists | Check for output .npy before processing. Resume by re-running. | ✓ |
| Checkpoint file | Write checkpoint tracking completed IDs. More complex. | |
| You decide | Claude picks resume strategy. | |

**User's choice:** Skip-if-exists (recommended)
**Notes:** None

### Q3: Error handling

| Option | Description | Selected |
|--------|-------------|----------|
| Log and skip | Write failed IDs to errors.log, continue. 4 known CRC-corrupt files expected. | ✓ |
| Fail fast | Stop on first error. | |

**User's choice:** Log and skip (recommended)
**Notes:** None

### Q4: Progress reporting

| Option | Description | Selected |
|--------|-------------|----------|
| tqdm progress bar | ETA, videos/sec, percentage. Essential for long jobs. | ✓ |
| Periodic logging | Print log line every N videos. Better for log files. | |

**User's choice:** tqdm progress bar (recommended)
**Notes:** None

---

## Claude's Discretion

- Exact batch size for GPU inference
- CLIP preprocessing details (follow open-clip defaults)
- PYSKL pickle format internals
- XD-Violence video decoding library (decord vs opencv)
- Error log format and location

## Deferred Ideas

- FPS distribution scan — can be done during implementation
- CLIP sampling rate ablation (OPT-07) — out of v1 scope
- RWF-2000 feature extraction (OPT-08) — out of v1 scope
- Intermediate PYSKL pickle archival — storage cost may not justify it
