---
phase: 01-environment
plan: 01
subsystem: infra
tags: [conda, rtmlib, pyskl, ctrgcn, open-clip-torch, mmcv, pytorch, gitignore, windows]

# Dependency graph
requires: []
provides:
  - Project directory scaffold (src/, configs/, data/, scripts/, envs/, notebooks/)
  - .gitignore excluding weights, features, results; tracking splits and configs
  - src/tta/__init__.py placeholder with SAR attribution (D-10)
  - envs/requirements-skeleton.txt (rtmlib 0.0.15, onnxruntime-gpu)
  - envs/requirements-ctrgcn.txt (mmcv-full 1.7.0, mmdet 2.25.1, mmpose 0.29.0, PYSKL)
  - envs/requirements-main.txt (PyTorch 2.6.0+cu124, open-clip-torch 3.3.0, kornia)
  - envs/SETUP.md with Windows-specific install commands for all three environments
affects: [02-feature-extraction, 03-model-architecture, 04-baseline-evaluation, 05-tta]

# Tech tracking
tech-stack:
  added:
    - rtmlib==0.0.15 (vcc-skeleton)
    - onnxruntime-gpu>=1.20.0 (vcc-skeleton)
    - mmcv-full==1.7.0 (vcc-ctrgcn)
    - PyTorch 1.12.1+cu113 (vcc-ctrgcn)
    - PyTorch 2.6.0+cu124 (vcc-main)
    - open-clip-torch==3.3.0 (vcc-main)
    - kornia>=0.7.0 (vcc-main)
  patterns:
    - Three isolated conda environments (vcc-skeleton, vcc-ctrgcn, vcc-main) to separate PyTorch 1.x legacy and PyTorch 2.x stacks
    - requirements-{env}.txt as reference documentation per environment (not pip install -r targets)
    - src/ organized by concern: models/, data/, losses/, tta/, utils/ subpackages

key-files:
  created:
    - .gitignore
    - src/__init__.py
    - src/models/__init__.py
    - src/data/__init__.py
    - src/losses/__init__.py
    - src/tta/__init__.py
    - src/utils/__init__.py
    - configs/.gitkeep
    - data/splits/.gitkeep
    - data/weights/ctrgcn/.gitkeep
    - data/weights/clip/.gitkeep
    - scripts/.gitkeep
    - notebooks/.gitkeep
    - envs/requirements-skeleton.txt
    - envs/requirements-ctrgcn.txt
    - envs/requirements-main.txt
    - envs/SETUP.md
  modified: []

key-decisions:
  - "results/.gitkeep cannot be committed because .gitignore excludes the results/ directory by design (D-07) — the directory is created locally but not tracked"
  - "requirements files are reference documents, not pip install -r targets — some packages installed via conda or special --index-url"
  - "torch==2.6.0 line appears in requirements-main.txt as documentation even though installed via --index-url flag"

patterns-established:
  - "Conda env isolation: never mix PyTorch 1.x and 2.x in same env"
  - "gitignore pattern: exclude large artifacts (weights, features, results), commit small metadata (splits, configs)"
  - "Attribution headers on copied external code (SAR/TENT in src/tta/)"

requirements-completed: [ENV-03]

# Metrics
duration: 8min
completed: 2026-03-31
---

# Phase 01 Plan 01: Project Scaffold and Requirements Files Summary

**Three-environment project scaffold with .gitignore, six src/ subpackage stubs, and complete Windows-specific SETUP.md covering conda env creation, CTR-GCN weight download, XD-Violence extraction via 7-Zip, and NTFS junction creation**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-31T05:48:00Z
- **Completed:** 2026-03-31T05:56:30Z
- **Tasks:** 2/2
- **Files modified:** 18

## Accomplishments

- Created all project directories per D-01 through D-07 and D-10 with correct structure
- Created .gitignore that excludes data/weights/, data/features/, results/ but tracks data/splits/ and configs/
- Created src/tta/__init__.py with SAR attribution docstring linking to https://github.com/mr-eggplant/SAR (D-10)
- Created three requirements files with exact version pins from CLAUDE.md and RESEARCH.md
- Created envs/SETUP.md with complete Windows-specific install commands for all three conda environments, dataset extraction via 7-Zip, NTFS junction creation, and CTR-GCN weight download URLs

## Task Commits

Each task was committed atomically:

1. **Task 1: Create project directory tree and .gitignore** - `820fdd5` (chore)
2. **Task 2: Create requirements files and SETUP.md** - `da28e4d` (chore)

**Plan metadata:** (docs commit — see final_commit below)

## Files Created/Modified

- `.gitignore` - Excludes weights, features, results; tracks splits and configs per D-07
- `src/__init__.py` - Empty package root
- `src/models/__init__.py` - Empty subpackage
- `src/data/__init__.py` - Empty subpackage
- `src/losses/__init__.py` - Empty subpackage
- `src/tta/__init__.py` - TTA placeholder with SAR attribution (D-10)
- `src/utils/__init__.py` - Empty subpackage
- `configs/.gitkeep` - Tracks empty configs/ directory
- `data/splits/.gitkeep` - Tracks empty data/splits/ directory
- `data/weights/ctrgcn/.gitkeep` - Tracks empty ctrgcn weights directory
- `data/weights/clip/.gitkeep` - Tracks empty clip weights directory
- `scripts/.gitkeep` - Tracks empty scripts/ directory
- `notebooks/.gitkeep` - Tracks empty notebooks/ directory
- `envs/requirements-skeleton.txt` - vcc-skeleton packages (rtmlib 0.0.15, onnxruntime-gpu 1.20+)
- `envs/requirements-ctrgcn.txt` - vcc-ctrgcn packages (mmcv-full 1.7.0, PyTorch 1.12.1)
- `envs/requirements-main.txt` - vcc-main packages (PyTorch 2.6.0, open-clip-torch 3.3.0, kornia)
- `envs/SETUP.md` - Step-by-step Windows install guide with dataset extraction commands

## Decisions Made

- `results/.gitkeep` intentionally not committed: the .gitignore `results/` rule correctly excludes the directory. The directory will exist locally but is not tracked in git — this is the intended behavior per D-07.
- requirements files are annotated reference documents, not pip install -r targets: conda packages and --index-url packages are documented as comments to clarify the actual install commands in SETUP.md.

## Deviations from Plan

None — plan executed exactly as written. The only edge case was `results/.gitkeep` being rejected by git due to the `results/` gitignore rule, which is the correct behavior per D-07 (results/ is intentionally gitignored). This was a plan clarification, not a deviation.

## Issues Encountered

- `git add results/.gitkeep` rejected by gitignore rule — expected behavior since D-07 specifies results/ is gitignored. Simply omitted results/.gitkeep from the commit; the results/ directory will be created locally as needed.

## User Setup Required

None — no external service configuration required. Environment creation is manual per SETUP.md (by design per D-08: "No automated setup script — manual is more debuggable on Windows").

## Next Phase Readiness

- All directories and source package stubs are committed and ready for Phase 1 Plans 02-03 (environment verification and CTR-GCN smoke test)
- requirements files and SETUP.md provide the canonical reference for environment creation
- No blockers

## Known Stubs

- `src/models/__init__.py` — empty, intentional placeholder; models implemented in Plans 02-03+
- `src/data/__init__.py` — empty, intentional placeholder; data pipeline in Phase 2
- `src/losses/__init__.py` — empty, intentional placeholder; MIL loss in Phase 3
- `src/tta/__init__.py` — docstring only, intentional per D-10; TENT/SAR added in Phase 5
- `src/utils/__init__.py` — empty, intentional placeholder; utilities added per-need

These stubs are structural placeholders required by D-01 through D-10. They do not affect this plan's goal (directory scaffold + environment documentation), which is fully achieved.

---
*Phase: 01-environment*
*Completed: 2026-03-31*
