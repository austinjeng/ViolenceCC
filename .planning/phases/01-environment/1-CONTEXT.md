# Phase 1: Environment & Project Foundation - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Three conda environments (vcc-skeleton, vcc-ctrgcn, vcc-main) created and smoke-tested. CTR-GCN forward pass verified with synthetic COCO-17 input producing 256-d output. Project directory structure scaffolded. XD-Violence dataset unzipped. All prerequisite infrastructure for Phase 2 (Feature Extraction Pipeline) is operational.

</domain>

<decisions>
## Implementation Decisions

### Source code layout
- **D-01:** `src/` organized by concern: `models/`, `data/`, `losses/`, `tta/`, `utils/` subpackages. Entry points `train.py` and `evaluate.py` live at the `src/` root.
- **D-02:** Separate `scripts/` directory at project root for extraction and utility scripts. Scripts run in different conda envs than `src/` code: `extract_skeletons.py` (vcc-skeleton), `extract_ctrgcn.py` (vcc-ctrgcn), `extract_clip.py` (vcc-main), `verify_alignment.py` (vcc-main).

### Config structure
- **D-03:** Flat YAML files in `configs/` — one self-contained file per experiment variant (e.g., `skeleton_only.yaml`, `clip_only.yaml`, `late_fusion.yaml`, `gated_fusion.yaml`, `rtfm_baseline.yaml`). No base+override inheritance.

### PYSKL integration
- **D-04:** Standalone clone at `D:\libs\pyskl`, installed via `pip install -e .` in vcc-ctrgcn environment. Project references PYSKL via standard `import pyskl`. Weight paths and config paths referenced in extraction scripts/YAML configs.

### Artifact locations
- **D-05:** Pretrained weights stored in `data/weights/` (gitignored) with subdirectories: `data/weights/ctrgcn/` (j.pth, b.pth, jm.pth, bm.pth) and `data/weights/clip/` (ViT-B-16.pt).
- **D-06:** Extracted features stored on `E:\features\` with symlinks from `data/features/` pointing there. Both datasets output to same directory structure: `{dataset}/skeleton/` and `{dataset}/clip/`.
- **D-07:** `.gitignore` by directory: `data/weights/`, `data/features/`, `results/`. Commit `data/splits/*.txt` and `configs/*.yaml`.

### Environment reproducibility
- **D-08:** One `requirements-{env}.txt` per conda environment stored in `envs/` directory: `requirements-skeleton.txt`, `requirements-ctrgcn.txt`, `requirements-main.txt`. Accompanied by `envs/SETUP.md` step-by-step guide. No automated setup script — manual is more debuggable on Windows.

### CTR-GCN forward pass smoke test
- **D-09:** Minimal forward pass only. Create synthetic tensor matching COCO-17 format (N=1, C=3, T=64, V=17, M=1), run through CTR-GCN with NTU120-xsub-j weights, assert output shape is (1, 256). No multi-stream or intermediate normalization checks.

### SAR/TENT integration strategy
- **D-10:** Copy `tent.py` and `sar.py` from official SAR repo into `src/tta/` with attribution headers citing https://github.com/mr-eggplant/SAR (ICLR 2023, MIT License). Phase 1 creates `src/tta/` as empty placeholder with `__init__.py`. Actual BN-to-LN adaptation happens in Phase 5.

### Dataset locations and format
- **D-11:** UCF-Crime at `E:\UCF_crime_dataset\` contains pre-extracted PNG frames (every 10th frame, ~3fps equivalent). Organized as `Train/{category}/{video}_x264_{framenum}.png` and `test/{category}/...`. 14 categories.
- **D-12:** XD-Violence zips on `E:\` to be unzipped to `E:\XD_Violence\train\` and `E:\XD_Violence\test\` during Phase 1. Training zips: `1-1004.zip` through `3320-3954.zip` (~72GB). Test zip: `XD_violence_test_video.zip` (~11GB). Annotations: `E:\XD_violence_annotations.txt`.
- **D-13:** Pre-extracted I3D features (`E:\i3d-features.zip`, ~39GB) to be unzipped and kept as reference/baseline comparison material.

### Dual extraction pipeline (Phase 2 prep)
- **D-14:** UCF-Crime extraction reads PNGs directly (no video decoding). Frame indices sorted numerically, grouped into snippets. XD-Violence extraction uses standard video decoding (decord/opencv). Both pipelines output same feature format per video.

</decisions>

<specifics>
## Specific Ideas

- Frame naming pattern for UCF-Crime: `{VideoName}_x264_{framenum}.png` where framenum increments by 10 (0, 10, 20, ...). Must sort numerically, not lexicographically.
- Fighting category starts from Fighting002 (no Fighting001 in Train). Extraction code must handle non-sequential video numbering.
- XD-Violence training videos are split across 5 zip archives by video number range. Unzip into single `train/` directory, not per-zip subdirectories.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Technology stack and version constraints
- `.planning/research/STACK.md` -- Complete version compatibility matrix, known issues, install commands for all three environments
- `CLAUDE.md` "Technology Stack" section -- Authoritative library versions, compatibility warnings, and alternatives considered

### Architecture and environment strategy
- `.planning/research/ARCHITECTURE.md` -- Three-environment justification, frozen backbone rationale, feature storage decisions
- `.planning/research/PITFALLS.md` -- Critical pitfalls C1 (coordinate normalization) and C2 (temporal misalignment) relevant to Phase 1 verification

### Requirements
- `.planning/REQUIREMENTS.md` -- ENV-01 (conda envs), ENV-02 (CTR-GCN weights), ENV-03 (directory structure) formal requirements

### Research synthesis
- `.planning/research/SUMMARY.md` -- Overall research findings informing stack choices and architecture decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — fresh repository with no existing code.

### Established Patterns
- None yet. Phase 1 establishes the patterns that all subsequent phases follow.

### Integration Points
- `data/weights/` structure must match paths used in Phase 2 extraction scripts
- `data/features/` symlink must resolve correctly for Phase 3 training dataset class
- `envs/requirements-*.txt` must accurately capture installed packages after environment verification

</code_context>

<deferred>
## Deferred Ideas

- RWF-2000 dataset on E:\ — potential third dataset for evaluation, not in v1 scope
- Automated environment setup script — manual SETUP.md chosen for debuggability; revisit if reproducibility becomes an issue
- wandb project initialization — defer to Phase 3 when training loop is implemented

</deferred>

---

*Phase: 01-environment*
*Context gathered: 2026-03-31*
