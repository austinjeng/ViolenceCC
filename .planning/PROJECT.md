# ViolenceCC

## What This Is

A PyTorch research codebase for weakly supervised violence-oriented video anomaly detection (VAD). Combines skeleton dynamics (CTR-GCN) with visual-language semantics (CLIP) in a dual-modal fusion framework, trained with MIL Ranking Loss. Includes a secondary investigation of TENT/SAR-style entropy-minimization TTA on LayerNorm-based fusion heads for cross-scene deployment robustness. This is the experiment code for a master's thesis.

## Core Value

A working dual-modal (Skeleton + CLIP) fusion pipeline that produces reproducible frame-level AUC/AP numbers on UCF-Crime and XD-Violence, with complete ablation analysis and TTA experiments.

## Requirements

### Validated

- [x] Environment setup: conda env with PyTorch, rtmlib, PYSKL, OpenCLIP, SAR dependencies — Validated in Phase 1: Environment & Project Foundation
- [x] CTR-GCN frozen feature extractor using NTU120 HRNet 2D pretrained weights (COCO-17) — Forward pass verified in Phase 1 (ENV-02: 256-d output, no NaN/Inf)

### Active
- [ ] Data pipeline: skeleton extraction (RTMPose COCO-17) for UCF-Crime and XD-Violence
- [ ] Data pipeline: CLIP ViT-B/16 feature extraction at 1 FPS with mean+max pooling
- [ ] Data pipeline: unified snippet-level feature caching (time-aligned skeleton + CLIP)
- [ ] Baseline reproduction: RTFM on UCF-Crime with I3D features (target: ±1% of 84.30 AUC)
- [ ] Single-modal baselines: Skeleton-Only MIL head, CLIP-Only MIL head
- [ ] Late Fusion baseline (score-level weighted average)
- [ ] Gated Fusion module (sigmoid gating, 256-d shared space, LayerNorm + Dropout)
- [ ] MIL Ranking Loss training with validation split (15% from training set) and early stopping
- [ ] Evaluation: frame-level AUC/AP on UCF-Crime and XD-Violence official test sets
- [ ] UCF-Crime-C corruption dataset (4 types x 5 severities = 20 conditions)
- [ ] TENT-style entropy-minimization adaptation on LN affine parameters
- [ ] SAR-style adaptation with sharpness-aware regularization on LN affine parameters
- [ ] Corruption TTA experiments: Source-Only vs TENT-style vs SAR-style on UCF-Crime-C
- [ ] Ablation: multi-person aggregation (concat vs max vs mean pooling)
- [ ] Ablation: CLIP pooling strategy (mean vs mean+max)
- [ ] Per-category violence subset analysis (UCF-Crime: Fighting+Assault, XD-Violence: Fighting+Abuse+Riot)
- [ ] Key results repeated 3 times with mean +/- std for statistical stability
- [ ] Qualitative analysis: anomaly score temporal curves, skeleton visualization, failure cases

### Out of Scope

- Thesis writing and LaTeX — tracked separately, not in this codebase project
- YOLO-World object detection (third modality) — optional enhancement, only if main dual-modal results are strong by Week 6
- Cross-Attention Fusion — only if Gated Fusion is stable and time permits
- Cross-dataset TTA (UCF->XD, XD->UCF) — only if corruption TTA is done
- Two-Person Interaction Graph — advanced skeleton modeling, only if time permits
- EATA-style TTA — only if TENT/SAR are done
- CTR-GCN fine-tune ablation — optional, proxy-label approach
- End-to-end backbone training — all backbones are frozen by design
- Real-time deployment or inference optimization — research code, not production

## Context

**Research positioning:** Novelty Claim A is the dual-modal (skeleton GCN + VLM) combination applied specifically to violence-oriented weakly supervised VAD (the modality combination exists in action recognition, but not in this task context). Novelty Claim B is the systematic evaluation of entropy-minimization TTA on LN-based (not BN-based) fusion heads in VAD.

**Key methodological decisions from PRD v2.3:**
- All backbones frozen (CTR-GCN, CLIP, YOLO-World) — only MIL fusion head trained
- 3-stage pipeline: feature pre-extraction → MIL training → TTA at test time
- CTR-GCN uses NTU120 HRNet 2D weights (COCO-17 format) — confirmed available from PYSKL
- TTA updates only LayerNorm affine parameters (gamma, beta), not BN running statistics
- Adaptation protocol: 32-snippet batches, per-video reset, unified learning rate grid search

**Dataset locations (E:\ drive):**
- UCF-Crime: `E:\UCF_crime_dataset\` (extracted, Train/test split)
- XD-Violence videos: `E:\` (zip files 1-1004.zip through 3320-3954.zip, NOT yet extracted)
- XD-Violence I3D features: `E:\i3d-features.zip` (not yet extracted)
- XD-Violence annotations: `E:\XD_violence_annotations.txt`
- RWF-2000: `E:\RWF_2000\`

**Target numbers:** UCF-Crime AUC 85-87% (minimum 83%), XD-Violence AP 82-85% (minimum 80%)

**Reference PRD:** `thesis_prd_v2.3.md` in project root — the authoritative specification document

## Constraints

- **Hardware**: Single NVIDIA RTX 4090, 24GB VRAM — limits batch sizes and rules out end-to-end backbone training
- **Timeline**: 12 weeks total, ~6 weeks for main results, ~6 weeks for additional experiments + writing
- **Solo researcher**: No parallelization of human effort; code must be debuggable by one person
- **Thesis level**: Master's — needs reasonable contribution, not top-conference breakthrough
- **Reproducibility**: All experiments must use fixed seeds, same train/val splits, same evaluation protocol

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Freeze all backbones | VRAM constraint + methodological cleanliness (one training stage) | — Pending |
| Gated Fusion as primary model | Sufficient complexity for thesis, much lower engineering risk than Cross-Attention | — Pending |
| NTU120 HRNet 2D pretrained CTR-GCN | COCO-17 format natively compatible with RTMPose output, confirmed downloadable | — Pending |
| TENT/SAR-style on LN (not vanilla TENT on BN) | Fusion head uses LayerNorm; BN vs LN difference is itself a research finding | — Pending |
| Corruption-based TTA before cross-dataset TTA | Cleaner experimental setup, easier to interpret, lower risk | — Pending |
| English codebase | Standard for ML research repos | — Pending |
| Code-only project scope | Thesis writing tracked separately | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-31 after Phase 1 completion*
