# Phase 4b: RTFM XD-I3D Gate + xd_i3d Training Dispatch - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `04b-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 04b-xd-violence-main-results-rtfm-xd-i3d-gate (narrowed to RTFM gate only per D-01)
**Areas discussed:** Sub-track structure/sequencing, xd_i3d dispatch architecture, Wu et al. XD annotation source + parser, RTFM gate fallback strategy, wandb/queue/smoke hygiene, Test/parser-forward-compat/commit-granularity

---

## Gray area selection

| Option | Selected |
|--------|----------|
| Sub-track structure/sequencing | ✓ |
| xd_i3d dispatch architecture | ✓ |
| Wu et al. XD annotation source + parser | ✓ |
| RTFM gate fallback strategy | ✓ |

All four presented gray areas selected for discussion.

---

## Area 1: Sub-track structure and sequencing

### Q1: How should Phase 4b be structured given the asymmetric sub-track readiness?

| Option | Description | Selected |
|--------|-------------|----------|
| Split into 4b + 4c | 4b = RTFM gate only; new 4c = XD main, activated when XD features land. | ✓ |
| Keep single 4b with two waves | 4b stays bundled; Wave 1 = RTFM, Wave 2 = XD main (blocks 4b closure indefinitely). | |
| 4b = RTFM-only, XD main → Phase 6 | Fold XD main into Phase 6 Analysis scope. | |

**User's choice:** Split into 4b + 4c. Thesis progress unblocked while XD extraction is stalled at 3/3360 train files.

### Q2: Phase 5 (TTA) readiness while Phase 4b RTFM work is in flight?

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 5 unblocked, runs in parallel | Phase 5's canonical base is ucf_gated_fusion_s42 (already bit-identical verified). | ✓ |
| Phase 5 waits on RTFM gate PASS | Treat RTFM as a trust anchor; serializes main-results window. | |

**User's choice:** Phase 5 runs in parallel. No cross-phase blocker.

### Q3: Phase 4c activation trigger?

| Option | Description | Selected |
|--------|-------------|----------|
| File-count probe: ≥4500 .npy in both XD dirs | Matches current ROADMAP activation-criterion wording. | ✓ |
| Date-based: replan 4c on 2026-05-07 | Forces a calendar decision point. | |
| Feature-count + time bound combined | Whichever arrives first. | |

**User's choice:** File-count probe only. Checked at each /gsd-progress invocation.

---

## Area 2: xd_i3d dispatch architecture

### Q1: How should the xd_i3d training path be wired into src/train.py and src/data/loaders.py?

| Option | Description | Selected |
|--------|-------------|----------|
| Parallel functions | New `build_dataloaders_i3d` + `train_one_epoch_i3d` + `validate_i3d`; main() branches once. Clean boundary, ~60 lines duplication. | ✓ |
| Polymorphic dispatch inside existing functions | Branch on `cfg['dataset']` inside existing build_dataloaders/train_one_epoch. Less duplication, couples contracts. | |
| Dataset-adapter Protocol | BatchBuilder Protocol + concrete adapters. Most abstract; ~80 lines scaffolding. | |

**User's choice:** Parallel functions. Preserves Phase 4 D-07/D-08 test-leakage module-boundary discipline.

### Q2: How should `build_dataloaders_i3d()` materialize the 5-crop training bags?

| Option | Description | Selected |
|--------|-------------|----------|
| Crop-as-sample collate | Custom `collate_i3d_train` flattens [B,5,T,1024] → [B*5,T,1024]. batch_size=3 × 5 = 15 effective, matches k_topk=3. | ✓ |
| Crop-stacked + reshape in train loop | Loader yields [B,5,T,1024] unchanged; train_one_epoch_i3d reshapes. | |
| Crop-averaged at train | Contradicts D-19; loses 5× signal. | |

**User's choice:** Crop-as-sample collate. Cleanest; keeps the reshape responsibility in the data layer.

### Q3: MIL bag labels source for xd_i3d?

| Option | Description | Selected |
|--------|-------------|----------|
| `_label_A` suffix = normal, else abnormal | Matches existing I3DFeatureDataset + _parse_label_xd convention. | ✓ |
| Wu et al. annotation file = source of truth | Cross-check suffix vs annotations; more robust, extra I/O. | |

**User's choice:** Suffix convention. No new label source; reuses existing partition logic.

---

## Area 3: Wu et al. XD annotation source + parser

### Q1: Annotation source?

| Option | Description | Selected |
|--------|-------------|----------|
| Official Wu 2020 `annotations.txt` | Download from roseyu.com/XD-Violence, commit to `data/annotations/xd_temporal.txt`. Matches Phase 4 D-04 pattern. | ✓ |
| RTFM `list/gt-xd.npy` fallback | Pre-computed binary frame labels; easier parsing but ties to RTFM's assumptions. | |
| Both — commit official + cross-validate against RTFM binary | Belt-and-suspenders. | |

**User's choice:** Official Wu 2020. Phase-researcher confirms exact URL during research step.

### Q2: Snippet→frame expansion contract?

| Option | Description | Selected |
|--------|-------------|----------|
| 16-frame snippet × 24fps master grid | Matches MGFN/RTFM published convention. snippet_to_frame(scores, n_frames=len(scores)*16, snippet_window=16, upsample_factor=1). | ✓ |
| Snippet-native AP only (no frame expansion) | Sidesteps C4 off-by-one risk but diverges from thesis "frame-level" headline. | |
| Researcher investigates exact I3D stride | Defer to gsd-phase-researcher. | |

**User's choice:** 16f/24fps contract — phase-researcher flagged (per decision text) to confirm exact I3D stride vs Wu annotation fps before planner locks the numbers.

### Q3: C4 enforcement strictness?

| Option | Description | Selected |
|--------|-------------|----------|
| Hard assert `len(frame_scores)==len(frame_labels)` before every sklearn call | Mirrors UCF (Phase 4 D-15). Raises loudly on any mismatch. | ✓ |
| Tolerant: truncate to min length + log | More robust to annotation off-by-one, masks real bugs. | |

**User's choice:** Hard assert. Reuses existing `src/eval/snippet_to_frame.py` guard for free.

---

## Area 4: RTFM gate fallback strategy

### Q1: Primary fallback if AP < 76.81%?

| Option | Description | Selected |
|--------|-------------|----------|
| Relax to MGFN 80.11% only if miss < 3pp | Document as "within RTFM/MGFN published band". Zero new runs. | ✓ |
| Add RGB+Flow I3D stream | D-05 Phase 4 contingency; medium effort; strongest anchor match. | |
| Add MTN temporal module to rtfm_i3d.py | Heavier lift; last-resort. | |
| Accept miss + document as thesis limitation | Fastest; weakest harness story. | |

**User's choice:** Cascade starts with MGFN anchor, then RGB+Flow, then MTN, then accept. D-11 defines the ordering.

### Q2: Diagnostic evidence before concluding "modeling issue"?

| Option | Description | Selected |
|--------|-------------|----------|
| Three orthogonal checks | Bit-identical rerun + snippet_auc vs auc < 2pp + 5-crop bag-size audit. | ✓ |
| Single rerun + visual comparison to Phase 4 UCF curves | Lighter, trusts existing infrastructure. | |
| Researcher-driven: no predetermined rule | Most flexible, least reproducible. | |

**User's choice:** Three-check protocol. Each check catches a specific failure mode (nondeterminism, C4 bug, bag collapse).

### Q3: Per-category breakdown for RTFM variant?

| Option | Description | Selected |
|--------|-------------|----------|
| No — per-category is Phase 4c Gated Fusion only | Keeps Phase 4b scope to headline AP. | ✓ |
| Yes — exercises parser's per-category path | Validates parser multi-label handling. | |

**User's choice:** No per-category for RTFM. Phase 4c owns SC #5 via Gated Fusion.

---

## Tactical round: wandb, queue naming, smoke test

### Q1: wandb posture for Phase 4b?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep Rule 3 fallback | mode:disabled + --no-preflight; rtfm_i3d.yaml already set. Zero new work. | ✓ |
| Fix wandb auth properly | WANDB_API_KEY or ~/.netrc setup; restores dashboard. | |
| Switch default to offline mode | Local .wandb/ logs; middle-ground. | |

**User's choice:** Rule 3 fallback. Consistent with Phase 4.

### Q2: Queue naming?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep `rtfm_gate` as-is | RunSpec already correct at scripts/run_ablations.py:84. | ✓ |
| Rename to `phase4b_rtfm_gate` | Phase provenance in name. | |
| Keep + alias | Both work; flexible for Phase 4c sibling. | |

**User's choice:** Keep as-is. results-index.csv row provides provenance via run_name.

### Q3: Empirical smoke test?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — 1-epoch smoke before full run | `python -m src.train --config configs/rtfm_i3d.yaml --epochs 1`. ~20-60s. | ✓ |
| No — go straight to full run | Full run is only 5-15 min; deviations surface fast enough. | |
| Unit tests only — no empirical smoke | Unit tests cheaper but don't exercise main() dispatch branch. | |

**User's choice:** 1-epoch smoke. Catches dispatch-chain bugs cheaply before the full gate rerun.

---

## Additional tactical round: tests, parser, commits

### Q1: Test coverage depth?

| Option | Description | Selected |
|--------|-------------|----------|
| Unit + smoke | pytest per new function + 1-epoch smoke. Mirrors Phase 4 discipline. | ✓ |
| Unit only — skip smoke | Contradicts D-16. | |
| Integration only — real E:/i3d-features data | End-to-end validation; CI portability loss. | |

**User's choice:** Unit + smoke. Four new test files listed in D-17.

### Q2: Wu annotation parser forward-compat?

| Option | Description | Selected |
|--------|-------------|----------|
| Forward-compatible, dual-use | `src/eval/xd_annotations.py` module mirroring ucf_annotations.py. Phase 4c reuses unchanged. | ✓ |
| xd_i3d-scoped inside _build_frame_arrays | Inline parser; Phase 4c refactors later. | |

**User's choice:** Forward-compatible module. Small extra discipline now saves a file-move refactor in Phase 4c.

### Q3: Plan commit granularity?

| Option | Description | Selected |
|--------|-------------|----------|
| One plan with ~5-6 atomic commits | Per-artifact commits: parser, loader, train, evaluate, tests, run. Mirrors Phase 4. | ✓ |
| Fewer, larger commits (1-3) | Faster plan; harder to bisect. | |
| Defer — planner decides | Safer if dependency analysis reveals different shape. | |

**User's choice:** ~5-6 atomic commits. D-18 specifies the anticipated shape; planner may adjust.

---

## Claude's Discretion (not discussed; noted for flexibility)

- Exact URL for Wu 2020 annotations (phase-researcher confirms)
- Exact I3D stride vs Wu annotation fps (phase-researcher confirms)
- `collate_i3d_train` implementation detail (default_collate + reshape vs hand-rolled)
- D-12 bag-size audit: one-shot log vs always-on assertion
- `per_category.csv` shape for rtfm variant under D-13 (empty / overall-only / skipped)
- Unit test mocking: real i3d slices vs synthetic arrays
- `VideoAnnotation` struct shape (namedtuple matching UCF default)
- `rtfm_i3d.yaml` `data.batch_size` raise from 3 → 16 (post-gate empirical only)
- Queue provenance: `phase4` → `phase4b` in wandb.tags (cosmetic)

## Deferred Ideas (recorded in CONTEXT.md, summarized)

**To Phase 4c:** XD-Violence main results (6 variants + 2 pooling + 3-seed Gated + per-category), XD re-extraction passes, new XD pooling YAMLs, `phase4c_*` orchestrator queues, EVAL-02..EVAL-05 XD-side completion, ROADMAP.md/REQUIREMENTS.md edits to reflect the 4b↔4c split.

**Within Phase 4b (conditional on D-11 cascade):** RGB+Flow I3D variant, MTN temporal module addition, `data.batch_size` raise.

**Beyond project scope:** UCF-Crime RTFM reproduction (original PRD target), multi-person max/mean aggregation, Flow CLIP ablation, cross-dataset RTFM.
