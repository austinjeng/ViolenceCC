# Phase 2: Feature Extraction Pipeline - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Valid, temporally aligned skeleton and CLIP feature caches exist for every video in both UCF-Crime and XD-Violence. Official split files and seeded validation splits are committed to the repo. An alignment verification script confirms matching snippet counts across modalities for all videos.

</domain>

<decisions>
## Implementation Decisions

### Temporal granularity
- **D-01:** Skeleton features extracted with non-overlapping 64-frame sliding windows (T=64 matches NTU120 pretrained checkpoint). Each window produces one 256-d vector via 4-stream weighted concat. Variable-length output per video (e.g., 1000 frames -> 15 snippets).
- **D-02:** CLIP features extracted at true 1 FPS, independent of skeleton window boundaries. Each sampled frame produces one 512-d vector via mean+max pooling. Variable-length output per video (e.g., 30-second video -> 30 vectors).
- **D-03:** Phase 3 dataset loader resamples both modalities to T=32 at training time. Extraction does NOT lock T — this preserves flexibility for ablating different snippet counts later.
- **D-04:** UCF-Crime uses pre-extracted PNGs as-is (~3fps equivalent, every 10th frame). No original video decoding needed. Both skeleton and CLIP extract from these same PNGs.

### Multi-person skeleton handling
- **D-05:** Top-2 persons selected by highest mean keypoint confidence when RTMPose detects 3+ people per frame.
- **D-06:** No minimum confidence threshold — accept all RTMPose detections regardless of confidence. Low-confidence detections in dark/occluded violence scenes still carry signal.
- **D-07:** Frames with 0 detected persons -> zero-pad both person slots (all-zero keypoints). CTR-GCN handles zero inputs gracefully.
- **D-08:** Frames with exactly 1 person -> zero-pad second person slot (M=2 required by checkpoint).

### Val split and split files
- **D-09:** Per-category stratified 15% val split from training set — maintains both normal/abnormal ratio and per-category ratio. For UCF-Crime: sample 15% from each of the 14 categories.
- **D-10:** Both UCF-Crime and XD-Violence get 15% val splits. Enables early stopping and hyperparameter tuning on both datasets independently.
- **D-11:** Val split seed value: 42. Fixed forever once created — changing it after feature extraction invalidates all comparisons.
- **D-12:** Split format: plain text files in `data/splits/`, one video ID per line. Files: `ucf_train.txt`, `ucf_val.txt`, `ucf_test.txt`, `xd_train.txt`, `xd_val.txt`, `xd_test.txt`.

### Extraction orchestration
- **D-13:** Process UCF-Crime first (smaller dataset, PNG-based, no video decoding). Validates pipeline end-to-end before tackling XD-Violence (3954 train + 800 test videos).
- **D-14:** Skip-if-exists resume strategy — check for output .npy file before processing each video. Allows resuming interrupted extraction by re-running the same script.
- **D-15:** Log-and-skip for corrupted/unreadable videos — write failed video IDs to errors.log, continue processing. The 4 known CRC-corrupt XD-Violence files are expected failures.
- **D-16:** tqdm progress bar for all extraction scripts (ETA, videos/sec, percentage). Essential for monitoring 20-40 hour jobs.

### Claude's Discretion
- Exact batch size for GPU inference during extraction
- CLIP preprocessing details (resize, center crop, normalization — follow open-clip defaults)
- PYSKL pickle format internals (follow PYSKL's existing examples)
- XD-Violence video decoding library choice (decord vs opencv — whichever works on Windows)
- Error log format and location

</decisions>

<specifics>
## Specific Ideas

- UCF-Crime frame naming: `{VideoName}_x264_{framenum}.png` where framenum increments by 10 (0, 10, 20, ...). Must sort numerically, not lexicographically.
- Fighting category starts from Fighting002 (no Fighting001 in Train). Extraction must handle non-sequential video numbering.
- XD-Violence filenames contain timestamps and labels: `A.Beautiful.Mind.2001__#00-01-45_00-02-50_label_A.mp4`. Parse video ID from filename for split tracking.
- XD-Violence test videos are in `test/videos/` subfolder, not directly in `test/`.
- CTR-GCN forward pass verified in Phase 1: input (N,M,T,V,C) = (1,2,64,17,3), output shape (N,256). Pool over M/T/V dimensions.
- CTR-GCN 4-stream concat: load j/b/jm/bm checkpoints separately, forward pass each, weighted concat (1.0:1.0:0.5:0.5) -> 256*4=1024-d -> or weighted average to 256-d. Clarify in research.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and specifications
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-10 formal requirements for this phase
- `thesis_prd_v2.3.md` — Authoritative PRD with feature extraction protocol, snippet definitions, and evaluation methodology

### Prior phase context
- `.planning/phases/01-environment/1-CONTEXT.md` — D-02 (script locations), D-05/D-06 (weight/feature paths), D-11/D-12/D-13 (dataset locations), D-14 (dual extraction strategy)

### Technology and architecture
- `.planning/research/STACK.md` — Version matrix for vcc-skeleton, vcc-ctrgcn, vcc-main environments
- `.planning/research/ARCHITECTURE.md` — Three-environment justification, frozen backbone rationale, feature storage decisions
- `.planning/research/PITFALLS.md` — C1 (coordinate normalization) and C2 (temporal misalignment) critical pitfalls directly relevant to this phase

### Project state
- `.planning/STATE.md` — Current progress, accumulated key decisions, blockers, and pending todos (FPS distribution scan)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `data/weights/ctrgcn/` — j.pth, b.pth, jm.pth, bm.pth pretrained weights already downloaded and verified
- `data/weights/clip/` — ViT-B-16.pt directory (to be populated or loaded via open-clip)
- `src/` package structure — `__init__.py` files in data/, models/, losses/, tta/, utils/ subpackages ready for imports
- Phase 1 smoke test — CTR-GCN forward pass pattern (load checkpoint, build model, forward) is a reference for extraction script

### Established Patterns
- Scripts in `scripts/` run in different conda envs than `src/` code (D-02 from Phase 1)
- Feature output to `E:\features\{dataset}/{modality}/` with symlinks from `data/features/` (D-06)
- Requirements files are reference documents, not pip install targets (documented in STATE.md)

### Integration Points
- `data/splits/*.txt` — Created here, consumed by Phase 3 dataset loader
- `E:\features\{dataset}/skeleton/*.npy` — Created here, consumed by Phase 3 training
- `E:\features\{dataset}/clip/*.npy` — Created here, consumed by Phase 3 training
- `data/features/` symlink — Must resolve correctly for Phase 3 imports
- `scripts/verify_alignment.py` — Validates skeleton/CLIP snippet count parity before Phase 3 can start

</code_context>

<deferred>
## Deferred Ideas

- FPS distribution scan across both datasets (noted in STATE.md todos) — relevant for extraction but can be done during implementation rather than discussed now
- CLIP sampling rate ablation (1 FPS vs 2 FPS vs 4 FPS) — OPT-07, out of v1 scope
- RWF-2000 feature extraction — OPT-08, out of v1 scope
- Intermediate PYSKL pickle archival after skeleton extraction — could save re-extraction time if CTR-GCN config changes, but storage cost may not justify it

</deferred>

---

*Phase: 02-feature-extraction-pipeline*
*Context gathered: 2026-04-03*
