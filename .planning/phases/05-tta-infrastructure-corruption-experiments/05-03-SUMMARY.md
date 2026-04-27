---
phase: 05-tta-infrastructure-corruption-experiments
plan: 03
subsystem: extraction-corruption
tags: [corruption, clip-extraction, skeleton-extraction, tta, ucf-crime-c]

# Dependency graph
requires:
  - phase: 05-tta-infrastructure-corruption-experiments
    plan: 01
    provides: "scripts/corruption.py with apply_corruption dispatcher"
provides:
  - "scripts/extract_clip.py: --corruption/--severity flags for on-the-fly CLIP corruption"
  - "scripts/extract_skeletons.py: --corruption/--severity flags for on-the-fly skeleton corruption"
  - "D-04 feature cache layout: clip_{type}_{severity}/ and skeleton_{type}_{severity}/ output dirs"
affects: [05-04 (TTA evaluation needs corrupted features), 05-05 (analysis needs corrupted features)]

# Tech tracking
tech-stack:
  added: []
  patterns: [on-the-fly corruption before model preprocessing, deterministic RNG seeding for reproducibility]

key-files:
  created: []
  modified:
    - scripts/extract_clip.py
    - scripts/extract_skeletons.py

key-decisions:
  - "Corruption applied after frame decode but before model preprocessing (CLIP transform / RTMPose inference)"
  - "Deterministic RNG(42) created once per extraction run for reproducible corruption across runs"
  - "Skip post-run validation in corruption mode since output dir differs from clean cache"
  - "Boundary JSONs shared between clean and corrupted extraction (same snippet boundaries)"

patterns-established:
  - "Corruption flags are additive-only: no existing behavior changes when flags absent"
  - "Output directory override pattern: clip_{type}_{severity}/ and skeleton_{type}_{severity}/"

requirements-completed: [TTA-02, TTA-03]

# Metrics
duration: 7min
completed: 2026-04-28
status: checkpoint-pending
---

# Phase 5 Plan 03: Corruption Extraction Flags Summary

**Added --corruption/--severity CLI flags to both extraction scripts for on-the-fly UCF-Crime-C corruption before CLIP and RTMPose preprocessing, with deterministic RNG(42) seeding**

## Performance

- **Duration:** 7 min (Task 1 only; Task 2 is human-supervised checkpoint)
- **Started:** 2026-04-27T20:45:52Z
- **Completed:** 2026-04-27T20:53:44Z (Task 1)
- **Tasks:** 1/2 (Task 2 is checkpoint:human-verify)
- **Files modified:** 2

## Accomplishments
- Added `--corruption` and `--severity` argparse flags to both `extract_clip.py` and `extract_skeletons.py`
- Corruption applied in-memory before CLIP preprocessing (PIL Image path) and before RTMPose inference (BGR frame path)
- Output routed to D-04 feature cache layout: `E:/features/{dataset}/clip_{type}_{severity}/` for CLIP and `E:/skeletons/{dataset}/skeleton_{type}_{severity}/` for skeletons
- Mutual validation: using one flag without the other produces an argparse error
- Smoke test passed: `--corruption gaussian_noise --severity 1 --limit 1` produced valid [2, 1024] float32 .npy at correct corruption-specific path
- All existing behavior preserved when flags are not provided

## Task Commits

Each task was committed atomically:

1. **Task 1: Add --corruption/--severity flags** - `8c1f6ce` (feat)
2. **Task 2: Human-supervised batch re-extraction** - CHECKPOINT (not executed)

## Checkpoint: Task 2

**Status:** Awaiting human-supervised batch re-extraction (~15h)

The user must run the following extraction jobs in a visible terminal:

**CLIP re-extraction (20 conditions, ~4h total):**
```bash
for type in gaussian_noise jpeg_compression brightness motion_blur; do
    for sev in 1 2 3 4 5; do
        echo "=== CLIP: $type severity $sev ==="
        conda run -n vcc-main python scripts/extract_clip.py --dataset ucf --split test --corruption $type --severity $sev
    done
done
```

**Skeleton re-extraction (10 conditions, ~11h total -- motion_blur + jpeg_compression only per M7):**
```bash
for type in motion_blur jpeg_compression; do
    for sev in 1 2 3 4 5; do
        echo "=== SKELETON: $type severity $sev ==="
        conda run -n vcc-skeleton python scripts/extract_skeletons.py --dataset ucf --split test --corruption $type --severity $sev
    done
done
```

Then run CTR-GCN feature extraction on each corrupted skeleton output.

**Verification after extraction:**
- 20 CLIP dirs at `E:/features/ucf/clip_{type}_{severity}/` each with ~290 .npy files
- 10 skeleton dirs at `E:/skeletons/ucf/skeleton_{type}_{severity}/` each with ~290 .pkl files
- For gaussian_noise and brightness: skeleton features use the CLEAN cache at `E:/features/ucf/skeleton/`

## Files Created/Modified
- `scripts/extract_clip.py` - Added --corruption/--severity flags, sys.path setup for corruption import, output dir override, per-frame corruption in UCF PNG and XD mp4 loading paths
- `scripts/extract_skeletons.py` - Added --corruption/--severity flags, sys.path setup for corruption import, output dir override, per-frame BGR-to-RGB-to-BGR corruption before RTMPose, corruption-aware resume logic

## Decisions Made
- **Corruption before preprocessing, not after:** Corruption is applied to raw uint8 RGB frames before CLIP transform and before RTMPose inference, matching ImageNet-C convention (corrupt the input signal, not the processed representation)
- **Deterministic RNG(42) per extraction run:** Single RNG created at run_extraction start, shared across all frames in all videos, ensuring identical corruption given same video order
- **Skip validation in corruption mode:** Post-run validate_sample_outputs checks the clean cache dir; skipped when corruption flags are active since output goes to a different directory
- **Boundary JSONs not duplicated:** Corrupted extractions reuse the same snippet boundary JSONs from E:/snippets/ since corruption does not change frame count or temporal structure

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all corruption paths are fully wired to the apply_corruption dispatcher from Plan 05-01.

## Self-Check: PASSED

- [x] scripts/extract_clip.py exists
- [x] scripts/extract_skeletons.py exists
- [x] scripts/corruption.py exists (Plan 01 dependency)
- [x] 05-03-SUMMARY.md exists
- [x] Commit 8c1f6ce found in git log

---
*Phase: 05-tta-infrastructure-corruption-experiments*
*Completed: 2026-04-28 (Task 1 only; Task 2 checkpoint pending)*
