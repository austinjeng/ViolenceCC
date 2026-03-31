---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 01
current_plan: 2
status: executing
last_updated: "2026-03-31T05:57:48.486Z"
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 3
  completed_plans: 1
  percent: 33
---

# State: ViolenceCC

**Last updated:** 2026-03-31
**Session:** Phase 01 Plan 01 complete — project scaffold and environment docs created

---

## Project Reference

**Core value:** A working dual-modal (Skeleton + CLIP) fusion pipeline that produces reproducible frame-level AUC/AP numbers on UCF-Crime and XD-Violence, with complete ablation analysis and TTA experiments.

**Milestone:** 1 — Initial Thesis Results
**Timeline:** 12 weeks (started 2026-03-31, target completion 2026-06-23)

---

## Current Position

Phase: 01 (environment) — EXECUTING
Plan: 2 of 3
**Current phase:** 01
**Current plan:** 2
**Status:** Executing Phase 01

**Progress:**

```
Phase 1 [███░░░░░░░] 33%  Environment & Project Foundation
Phase 2 [          ] 0%   Feature Extraction Pipeline
Phase 3 [          ] 0%   Model Architecture & Training Infrastructure
Phase 4 [          ] 0%   Baseline Evaluation & Main Results
Phase 5 [          ] 0%   TTA Infrastructure & Corruption Experiments
Phase 6 [          ] 0%   Analysis & Visualization
```

---

## Performance Metrics

No experiments run yet. Targets from PRD v2.3:

| Metric | Minimum Gate | Target Range |
|--------|-------------|--------------|
| UCF-Crime frame-level AUC | 83% | 85-87% |
| XD-Violence frame-level AP | 80% | 82-85% |
| RTFM reproduction AUC | 84.30% ± 1% | — (gate, not target) |

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01-environment P01 | 8min | 2 tasks | 18 files |

## Accumulated Context

### Key Decisions (inherited from research phase)

| Decision | Rationale |
|----------|-----------|
| Three conda environments | mmcv-full 1.x cannot coexist with PyTorch 2.x; vcc-ctrgcn is a legacy silo |
| All backbones frozen | VRAM constraint + 3-stage methodological cleanliness |
| float32 .npy per video | Simpler than HDF5; no dtype mismatch risk; ~25 GB per dataset fits |
| RTFM reproduction gates novel experiments | Validates evaluation harness; catches C4 (AUC calculation bugs) |
| 15% stratified val split committed before first training run | All experiments use identical split; changing it later invalidates comparisons |
| Late Fusion before Gated Fusion | 2-hour implementation; validates full pipeline before adding learned gating complexity |
| LN-only TTA (not BN) | Fusion head uses LayerNorm; the BN→LN transfer is itself a research contribution |
| Single train.py with YAML config | Avoids VadCLIP's per-dataset duplication anti-pattern |
| English codebase | Standard for ML research repos |
| results/.gitkeep not committed | .gitignore excludes results/ by design (D-07); directory created locally as needed |
| requirements files are reference documents | conda and --index-url packages documented as comments; not pip install -r targets |

### Critical Pitfalls to Watch

| ID | Risk | Phase | Prevention |
|----|------|-------|------------|
| C1 | Skeleton coordinate space mismatch (raw pixel coords vs normalized) | Phase 2 | Apply PreNormalize2D; assert coordinates in [-1, 1] |
| C2 | Temporal misalignment in variable-FPS videos | Phase 2 | Read FPS per video with cv2; map snippet boundaries to wall-clock seconds |
| C3 | Test set leakage into hyperparameter tuning | Phase 3-4 | Early stopping on val MIL loss only; test annotations loaded only in evaluate.py |
| C4 | Off-by-one in snippet-to-frame score expansion | Phase 4 | Encapsulate mapping in single utility; assert len(frame_scores)==len(frame_labels) |
| C5 | MIL training collapse to trivial solutions | Phase 3-4 | Monitor snippet score distribution variance; verify bag construction matches RTFM |
| M5 | TTA entropy collapse on normal-heavy batches | Phase 5 | SAR-style gradient filtering; analyze entropy distribution by anomaly duration |
| M6 | SAR rho ImageNet default too large for scalar output | Phase 5 | Grid search from 0.005; not from ImageNet default |
| M7 | Corruption TTA requires skeleton re-extraction for motion blur + JPEG | Phase 5 | Only noise and brightness conditions can reuse source skeleton cache |

### Todos

- [ ] Verify XD-Violence zip access and extraction feasibility before Phase 2 planning (zip files 1-1004.zip through 3320-3954.zip on E:\)
- [ ] Scan UCF-Crime and XD-Violence FPS distribution in Phase 2 Week 1 to size snippet window computation
- [ ] Confirm CTR-GCN weights (j/b/jm/bm) are available for download from PYSKL repo before Phase 1 execution

### Blockers

None currently.

---

## Session Continuity

**To resume:** Read this file and ROADMAP.md. Current phase is Phase 1, plan 2 of 3. Plan 01 (directory scaffold) is complete. Plans 02-03 (environment verification, CTR-GCN smoke test) remain.

**Files of record:**

- `.planning/PROJECT.md` — project definition and key decisions
- `.planning/REQUIREMENTS.md` — 40 v1 requirements with traceability
- `.planning/ROADMAP.md` — 6-phase roadmap with success criteria
- `.planning/research/SUMMARY.md` — research findings and pitfall catalog
- `thesis_prd_v2.3.md` — authoritative PRD specification

---

*State initialized: 2026-03-31*
