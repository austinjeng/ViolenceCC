# Phase 4b: RTFM XD-I3D Gate + xd_i3d Training Dispatch - Research

**Researched:** 2026-04-16
**Domain:** MIL training-dispatch plumbing (parallel functions), XD-Violence frame-level annotation wiring, RTFM gate reproduction on 1024-d RGB I3D features
**Confidence:** HIGH

## Summary

Phase 4b is a targeted remediation phase, not a research domain. The architectural work was scoped in the Phase 4 04-06 UAT Rule 4 diagnosis and locked in CONTEXT.md through D-01..D-18 (18 decisions; 9 items in Claude's Discretion). Research here has three jobs:

1. **Confirm the Wu et al. 2020 XD-Violence annotation file** — URL, exact format, ID normalization, coverage against `data/splits/xd_test.txt`.
2. **Verify the I3D cache stride** against the XDVioDet reference `gt.npy` to lock D-08's `snippet_window=16 / upsample_factor=1` numbers before the planner writes tasks.
3. **Cross-check the RTFM/MGFN anchors** against the published I3D-RGB results (not VideoSwin-RGB) so D-11's fallback cascade anchors are correctly stated.

**All three have clean, verified answers that confirm CONTEXT.md defaults.** One correction is warranted: D-11's "MGFN 80.11% fallback upper anchor" is MGFN's **VideoSwin** result, not its I3D-RGB result (MGFN I3D-RGB is 79.19%). The planner should update D-11 accordingly — 80.11% is not a reachable target with the 1024-d I3D-RGB cache on disk.

**Primary recommendation:** Plan the 5-6 atomic commits per D-18 using the parallel-functions dispatch (D-04), mirror the `ucf_annotations.py` structure for `xd_annotations.py` (D-10), replace the `_build_frame_arrays` xd_i3d stub at evaluate.py:180-192 with a real annotation-driven label construction, and gate the full rtfm_gate queue run on a 1-epoch smoke test (D-16) + three orthogonal diagnostic checks (D-12) before concluding any gate miss is a modeling issue worth the D-11 fallback cascade.

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase scope and sequencing:**
- **D-01:** Split original Phase 4b into **Phase 4b (RTFM XD-I3D gate only)** and **Phase 4c (XD-Violence Main Results)**. Phase 4b owns: (a) xd_i3d training dispatch implementation, (b) Wu et al. XD annotation parser, (c) `src/evaluate.py::_build_frame_arrays` xd_i3d path rewrite, (d) rtfm_gate queue rerun + AP ≥ 0.7681 validation. Phase 4c owns the previously-bundled "Deferred from Phase 4" subsection. Planner applies the ROADMAP.md edit as part of Phase 4b's plan.
- **D-02:** Phase 5 (TTA) runs in parallel with Phase 4b. Phase 5's canonical adaptation base is `results/ucf_gated_fusion_s42/best_model.pth`. RTFM gate PASS/FAIL does NOT block Phase 5.
- **D-03:** Phase 4c activation trigger = filesystem probe `ls -1 E:/features/xd/skeleton/*.npy | wc -l >= 4500 && ls -1 E:/features/xd/clip/*.npy | wc -l >= 4500`.

**xd_i3d training dispatch architecture:**
- **D-04:** Parallel functions, not polymorphic dispatch. Add `build_dataloaders_i3d(cfg)` alongside `build_dataloaders()`. Add `train_one_epoch_i3d` + `validate_i3d` alongside existing functions in `src/train.py`. Branch once in `main()` on `cfg['dataset'] == 'xd_i3d'`.
- **D-05:** 5-crop training bag materialization = crop-as-sample collate. DataLoader batch of B videos × [5, T, 1024] → yields `i3d: [B*5, T, 1024]` + `label: [B*5]` + `video_id: [B*5]`. With `data.batch_size=3`, effective MIL bag size = 15, matching `k_topk=3`.
- **D-06:** MIL bag labels from `_label_A` suffix convention. Reuse split-into-nor_idx/abn_idx pattern from `src/data/loaders.py:123-126`.

**Wu et al. XD annotation pipeline:**
- **D-07:** Annotation source = official Wu et al. 2020 release `annotations.txt`, committed to `data/annotations/xd_temporal.txt`. Canonical source is the XD-Violence project page.
- **D-08:** Snippet→frame expansion contract for xd_i3d in `src/evaluate.py::_build_frame_arrays` = 16-frame I3D snippet window × 24fps master grid. `n_frames = len(scores) * 16`; `snippet_to_frame(scores, n_frames=n_frames, snippet_window=16, upsample_factor=1)`.
- **D-09:** C4 guard enforcement = hard `assert len(frame_scores) == len(frame_labels)` before every `sklearn.metrics` call, mirroring UCF.
- **D-10:** Wu annotation parser = forward-compatible, module-level `src/eval/xd_annotations.py`, mirroring `src/eval/ucf_annotations.py` pattern.

**RTFM gate fallback strategy:**
- **D-11:** Fallback cascade: (1) Relax anchor to MGFN 80.11% only if miss < 3pp. (2) Add RGB+Flow I3D stream. (3) Add MTN temporal module. (4) Accept miss + document as thesis limitation.
- **D-12:** Before concluding "dispatch is correct", perform three orthogonal diagnostic checks: bit-identical rerun consistency, C4 sanity (snippet_auc vs auc delta < 2pp), train-time 5-crop bag-size audit.
- **D-13:** No per-category breakdown for RTFM variant. Scope = headline AP only.

**Evaluation harness hygiene:**
- **D-14:** wandb posture = keep Rule 3 fallback (wandb.mode: disabled + --no-preflight).
- **D-15:** Keep `rtfm_gate` queue name as-is. RunSpec at line 84 is reusable.
- **D-16:** Execute a 1-epoch empirical smoke test before the full rtfm_gate queue run.

**Test coverage:**
- **D-17:** Test coverage = pytest unit tests + 1-epoch empirical smoke. New test files: `test_loaders_i3d.py`, `test_train_i3d.py`, `test_xd_annotations.py`, `test_evaluate_xd_i3d.py`.
- **D-18:** Plan shape = one PLAN.md with ~5-6 atomic commits.

### Claude's Discretion (open items this research resolves)

- Exact URL for the Wu 2020 annotations — **RESOLVED**: `https://roc-ng.github.io/XD-Violence/images/annotations.txt` (see §Wu Annotation Format below).
- Exact I3D stride vs. annotation fps — **RESOLVED**: 16-frame stride, annotation-fps = video-fps (not 24fps universal); confirmed bit-identical to XDVioDet gt.npy.
- `collate_i3d_train` implementation — **RECOMMENDED**: custom function using explicit `torch.stack` + `.view(B*5, T, 1024)` for auditability.
- D-12 bag-size audit posture — **RECOMMENDED**: one-shot log in first 3 epochs, not always-on.
- `per_category.csv` row shape for rtfm variant — **RECOMMENDED**: single "overall" row (reuses existing writer without special-casing).
- Unit test mocking strategy — **RECOMMENDED**: reuse existing `synthetic_i3d_features` fixture (Option B, synthetic numpy) — already ships in `tests/fixtures/synthetic_eval.py` and `tests/conftest.py`.
- `parse_xd_annotations` return type — **RECOMMENDED**: `VideoAnnotation`-style namedtuple (dataclass with `frozen=True`, mirroring `src/eval/ucf_annotations.py`).
- `data.batch_size` raise from 3→16 — **DEFERRED** per CONTEXT.md; not Phase 4b scope.
- Queue provenance tag fix — **DEFERRED** per CONTEXT.md; cosmetic only.

### Deferred Ideas (OUT OF SCOPE)

**To Phase 4c:**
- XD-Violence main results table (6 variants × seed=42 + 2 pooling ablations + 3-seed Gated Fusion)
- XD re-extraction passes (`extract_ctrgcn.py --keep-persons`, `extract_clip.py --pool=mean`)
- XD pooling YAMLs (`configs/gated_fusion_xd_2person.yaml` etc.)
- 3 new queues (`phase4c_main`, `phase4c_pooling`, `phase4c_seeds`)
- Per-category Fighting/Abuse/Riot breakdown on XD
- ROADMAP.md Phase 4c detail block creation (Phase 4b's planner performs this edit)
- REQUIREMENTS.md annotation flip: EVAL-02..EVAL-05 XD-side moves from "Phase 4b" to "Phase 4c"

**Conditional on D-11 cascade (may not happen):**
- RGB+Flow I3D variant `rtfm_i3d_rgbflow`
- MTN temporal module addition to `src/models/rtfm_i3d.py`
- `data.batch_size` raise from 3 → 16
- `wandb.tags` historical label fix

**Beyond project scope:**
- UCF-Crime RTFM reproduction (original PRD EVAL-01)
- Multi-person skeleton max/mean aggregation on XD
- `last_model.pth` sanity eval for RTFM
- Flow-stream CLIP ablation
- Cross-dataset RTFM

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVAL-01 | RTFM baseline reproduction — target AP ≥ 76.81% (77.81% ± 1%) on XD-Violence with I3D-RGB 5-crop features. Rescoped from Phase 4 per 2026-04-15 Option B decision. | Verified Wu annotation URL + format (§Wu Annotation Format). Verified I3D stride = 16 via bit-identical match to XDVioDet `gt.npy` (§I3D Cache Validation). Confirmed 1024-d RGB-only feature dim. Verified RTFM published 77.81% AP references I3D-RGB 10-crop (we adapt to XD's 5-crop per D-19). Confirmed MGFN 80.11% is VideoSwin (not I3D-RGB); MGFN I3D-RGB is 79.19%. |

## Architectural Responsibility Map

Phase 4b is pure backend/training-infrastructure work — no browser/CDN concerns.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Wu annotation parsing | API/Backend (`src/eval/`) | — | Parsing logic is pure Python IO + np.ndarray construction; shares C3 test-set-isolation boundary with `ucf_annotations.py` |
| xd_i3d training dispatch | API/Backend (`src/data/`, `src/train.py`) | — | Pure PyTorch/MIL training on cached features; no network IO, no frontend |
| 5-crop collate | Database/Storage adapter (`src/data/loaders.py`) | — | Stateless tensor reshaping between on-disk cache layout and model-forward layout |
| `_build_frame_arrays` xd_i3d branch | API/Backend (`src/evaluate.py`) | — | Reads annotations, writes metric dict consumed by sklearn |
| rtfm_gate queue rerun | Experiment Harness (`scripts/`) | API/Backend (training + eval) | Orchestration-tier; delegates heavy lifting to subprocess train.py + evaluate.py |
| ROADMAP.md + REQUIREMENTS.md edits | Documentation | — | Planning-phase metadata; no runtime impact |

## Standard Stack

All dependencies already installed in `vcc-main` (Python 3.11 + PyTorch 2.6.0 + cu124). No new packages required for Phase 4b.

### Already-in-stack packages consumed

| Library | Version | Purpose | Source of truth |
|---------|---------|---------|----------------|
| torch | 2.6.0 | DataLoader, Dataset, tensor ops, optimizer | [VERIFIED: codebase CLAUDE.md] |
| numpy | >= 1.23 | np.load (allow_pickle=False), array ops | [VERIFIED: src/data/i3d_dataset.py:109] |
| scikit-learn | >= 1.3 | `roc_auc_score`, `average_precision_score` | [VERIFIED: src/eval/metrics.py:26] |
| pytest | 9.0.2 | Unit test runner | [VERIFIED: live query on vcc-main env] |
| PyYAML | >= 6.0 | Config loading | [VERIFIED: existing tests use yaml.safe_load] |

### Internal-project modules consumed unchanged

| Module | Purpose | Why reused |
|--------|---------|-----------|
| `src/utils/seed.py` | `set_deterministic(seed)` + `seed_worker` + `make_generator` | D-12 bit-identical rerun invariant depends on this [VERIFIED: codebase] |
| `src/utils/checkpoint.py::save_checkpoint_atomic` | best/last model atomic save | D-10 (Phase 4) best-only policy [VERIFIED: src/train.py:196-198] |
| `src/utils/config.py::snapshot_config`, `config_hash`, `checkpoint_sha`, `git_sha` | Reproducibility metadata | D-12 config hash diagnostic check |
| `src/utils/csv_logger.py::CSVLogger` + `results_index_append` | train_log.csv + results-index.csv | D-14 wandb-disabled fallback logger [VERIFIED: scripts/run_ablations.py:41] |
| `src/utils/wandb_logger.py::WandbLogger` | wandb-disabled mode handles gracefully | D-14 |
| `src/utils/scheduler.py::build_optimizer`, `build_scheduler` | AdamW + cosine decay | TRN-01 |
| `src/utils/early_stopping.py::EarlyStopping` | val-loss patience gate | TRN-02; patience=10 per rtfm_i3d.yaml:33 |
| `src/losses/mil_loss.py::mil_ranking_loss` | Top-k MIL + sparsity + smoothness | k_topk=3 per rtfm_i3d.yaml:34 [VERIFIED: src/losses/mil_loss.py:52-84] |
| `src/models/rtfm_i3d.py::RTFMI3D` | FM head + MILHead, `self.ln_i3d` named | No changes needed unless D-11 fallback triggers [VERIFIED: src/models/rtfm_i3d.py] |
| `src/models/registry.py::build_model` | `variant="rtfm_i3d"` dispatch | Already registered [VERIFIED: tests/test_rtfm_i3d.py:27] |
| `src/data/i3d_dataset.py::I3DFeatureDataset` | 5-crop loader; [5, T, 1024] train/val, [N, 1024] test | No changes needed [VERIFIED: src/data/i3d_dataset.py; test_i3d_dataset.py] |
| `src/eval/snippet_to_frame.py::snippet_to_frame` | C4-guarded frame broadcast | Reused unchanged with `snippet_window=16, upsample_factor=1` [VERIFIED: src/eval/snippet_to_frame.py] |
| `src/eval/metrics.py::compute_frame_metrics` + `compute_snippet_auc` | Frame-level AUC/AP + snippet AUC | Works dataset-agnostically on per-video dicts [VERIFIED: src/eval/metrics.py] |
| `src/eval/test_loader.py::build_test_dataset` | `ds == 'xd_i3d'` branch already dispatches to `I3DFeatureDataset(mode="test")` | Already correct [VERIFIED: src/eval/test_loader.py:103-117] |
| `scripts/run_ablations.py::QUEUES["rtfm_gate"]` | RunSpec at line 84 | Reusable unchanged [VERIFIED: scripts/run_ablations.py:83-84] |

### Files to ADD (new)

| File | Purpose | Template |
|------|---------|----------|
| `src/eval/xd_annotations.py` | Wu 2020 XD annotation parser + `xd_frame_labels` | Mirror of `src/eval/ucf_annotations.py` |
| `data/annotations/xd_temporal.txt` | Committed Wu annotation file (6.2 KB) | Downloaded from `https://roc-ng.github.io/XD-Violence/images/annotations.txt` |
| `tests/test_loaders_i3d.py` | `build_dataloaders_i3d` + `collate_i3d_train` unit tests | Patterns from `tests/test_loaders*.py` + `tests/conftest.py::synthetic_i3d_features` |
| `tests/test_train_i3d.py` | `train_one_epoch_i3d` + `validate_i3d` unit tests | Patterns from `tests/test_train.py` |
| `tests/test_xd_annotations.py` | Parser + `xd_frame_labels` | Mirror of `tests/test_eval_metrics.py` + `tests/test_snippet_to_frame.py` patterns |
| `tests/test_evaluate_xd_i3d.py` | `_build_frame_arrays` xd_i3d path | Pattern from `tests/test_evaluate_cli.py` |

### Files to MODIFY

| File | Change | Line range |
|------|--------|------------|
| `src/data/loaders.py` | ADD `build_dataloaders_i3d(cfg)` + `collate_i3d_train` alongside existing `build_dataloaders` | New code; no existing code touched |
| `src/train.py` | ADD `train_one_epoch_i3d(...)`, `validate_i3d(...)`, dispatch branch in `main()` after `cfg = apply_cli_overrides(cfg, args)` (around line 144) | ~80 new lines; existing UCF path untouched |
| `src/evaluate.py::_build_frame_arrays` | REWRITE xd_i3d branch (replace all-zero stub) | Lines 180-192 |
| `.planning/ROADMAP.md` | Split Phase 4b block (narrow title to "RTFM XD-I3D Gate"), insert Phase 4c block, update Progress Table | Lines 95-117 + line 150 |
| `.planning/REQUIREMENTS.md` | Annotate EVAL-02..EVAL-05: flip "XD-side" pointer from "Phase 4b" to "Phase 4c" | Lines 51-54, 141-143 |

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ configs/rtfm_i3d.yaml (unchanged)                                           │
│   seed=42, dataset=xd_i3d, model.variant=rtfm_i3d,                          │
│   paths.i3d_features=E:/i3d-features/i3d-features, data.batch_size=3        │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                   python src/train.py --config configs/rtfm_i3d.yaml
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ src/train.py::main()                                                        │
│   cfg = load_config(args.config)                                            │
│   cfg = apply_cli_overrides(cfg, args)                                      │
│   set_deterministic(cfg['seed'])                                            │
│                                                                             │
│   ┌──────────────── NEW dispatch branch (D-04) ────────────────┐           │
│   │ if cfg['dataset'] == 'xd_i3d':                             │           │
│   │   (nor, abn), val = build_dataloaders_i3d(cfg)             │           │
│   │   for epoch in range(epochs):                              │           │
│   │     train_loss = train_one_epoch_i3d(                      │           │
│   │         model, nor, abn, optimizer, device, cfg['train'])  │           │
│   │     val_loss   = validate_i3d(model, val, device, …)       │           │
│   │     save best_model.pth (D-10)                             │           │
│   │     save_checkpoint_atomic(last_model.pth)                 │           │
│   │ else:                                                      │           │
│   │   existing UCF/XD-fusion path (untouched)                  │           │
│   └────────────────────────────────────────────────────────────┘           │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ src/data/loaders.py::build_dataloaders_i3d(cfg)   [NEW]                     │
│                                                                             │
│   train_ds = I3DFeatureDataset(mode='train', feature_dir=…/RGB/)            │
│   val_ds   = I3DFeatureDataset(mode='val',   feature_dir=…/RGB/)            │
│                                                                             │
│   nor_idx = [i for i, v in enumerate(train_ds.video_ids)                    │
│              if v.endswith('_label_A')]                                     │
│   abn_idx = [i for i, v in enumerate(train_ds.video_ids)                    │
│              if not v.endswith('_label_A')]                                 │
│                                                                             │
│   nor_loader = DataLoader(Subset(train_ds, nor_idx),                        │
│                batch_size=3, shuffle=True, drop_last=True,                  │
│                collate_fn=collate_i3d_train, generator=g_nor,               │
│                worker_init_fn=seed_worker, persistent_workers=…)            │
│   abn_loader = DataLoader(Subset(train_ds, abn_idx), … g_abn …)             │
│   val_loader = DataLoader(val_ds, batch_size=6, collate_fn=…, generator=…)  │
│                                                                             │
│   return (nor_loader, abn_loader), val_loader                               │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ collate_i3d_train(batch_list)   [NEW; in src/data/loaders.py]               │
│                                                                             │
│   batch_list = [{'i3d': [5,T,1024], 'label':float, 'video_id':str}, …]      │
│   i3d_stack  = torch.stack([b['i3d'] for b in batch_list])   # [B,5,T,1024] │
│   i3d_flat   = i3d_stack.view(B * 5, T, 1024)                # [B*5,T,1024] │
│   labels     = torch.tensor([b['label']]*5 for b in batch_list)             │
│                                    .view(-1).float()         # [B*5]        │
│   mask       = torch.ones(B*5, T, dtype=torch.float32)       # D-05 no pad  │
│   video_ids  = [vid for b in batch_list for vid in [b['video_id']]*5]       │
│   return {'i3d': i3d_flat, 'label': labels, 'mask': mask,                   │
│           'video_id': video_ids}                                            │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ train_one_epoch_i3d(model, nor_loader, abn_loader, opt, dev, train_cfg)     │
│   [NEW; in src/train.py]                                                    │
│                                                                             │
│   for each paired (nor_batch, abn_batch):                                   │
│     i3d = torch.cat([nor_batch['i3d'], abn_batch['i3d']], dim=0)            │
│             # [2*B*5, T, 1024] — 15 normals then 15 abnormals (@B=3)        │
│     mask = torch.cat([nor_batch['mask'], abn_batch['mask']], dim=0)         │
│     n_normal = nor_batch['i3d'].shape[0]   # = B*5 = 15                     │
│                                                                             │
│     scores = model(i3d=i3d, mask=mask)     # [2*B*5, T]                     │
│     loss = mil_ranking_loss(scores, mask, n_normal=n_normal, k=3, …)        │
│     # D-12 audit: first 3 epochs, assert shapes and log n_normal/n_abnormal │
│                                                                             │
│     optimizer.step(); loss.backward()                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼ (after training completes)
┌─────────────────────────────────────────────────────────────────────────────┐
│ python src/evaluate.py --run-dir results/xd_i3d_rtfm_i3d_s42/               │
│   ─ build_test_dataset(cfg)  → I3DFeatureDataset(mode='test')               │
│      ─ returns [N, 1024] per video (crops averaged)                         │
│   ─ _run_inference(model, dataset)                                          │
│      ─ forward [1, N, 1024] → scores [1, N] → per_video_snippet_scores[vid] │
│   ─ _build_frame_arrays(cfg, per_video_snippet_scores)   [MODIFIED]         │
│      if ds == 'xd_i3d':                                                     │
│         annos = parse_xd_annotations('data/annotations/xd_temporal.txt')    │
│         for vid, scores in per_video_snippet_scores.items():                │
│           n_frames = len(scores) * 16                                       │
│           frames_map[vid] = snippet_to_frame(scores, n_frames, 16, 1)       │
│           if vid in annos:                                                  │
│             labels_map[vid] = xd_frame_labels(annos[vid], n_frames)         │
│             cats_map[vid] = annos[vid].category                             │
│           else:  # normal video (no entry in Wu annotations)                │
│             labels_map[vid] = np.zeros(n_frames, dtype=np.int64)            │
│             cats_map[vid] = "Normal"                                        │
│   ─ compute_frame_metrics → auc + ap + snippet_auc + video_auc              │
│   ─ write eval_metrics.json + eval_scores.npz + .done                       │
│   ─ results-index.csv row appended                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Gate check: AP >= 0.7681  (77.81% - 1% per D-03)                            │
│   PASS → closeout                                                           │
│   MISS → D-12 diagnostic cascade → D-11 fallback if all diagnostics pass    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (paths affected by Phase 4b)

```
D:/ViolenceCC/
├── data/
│   ├── annotations/
│   │   ├── ucf_temporal.txt         # existing (Phase 4 Plan 01)
│   │   └── xd_temporal.txt          # NEW — Wu 2020 500-line annotations file (~6.2 KB)
│   └── splits/
│       ├── xd_train.txt             # unchanged (3360 videos)
│       ├── xd_val.txt               # unchanged (594 videos)
│       └── xd_test.txt              # unchanged (800 videos; 300 normal + 500 abnormal)
├── src/
│   ├── data/
│   │   ├── i3d_dataset.py           # unchanged (5-crop loader, Pitfall 4 filter)
│   │   └── loaders.py               # MODIFIED — ADD build_dataloaders_i3d + collate_i3d_train
│   ├── eval/
│   │   ├── ucf_annotations.py       # unchanged (template)
│   │   ├── xd_annotations.py        # NEW — parse_xd_annotations + xd_frame_labels
│   │   ├── snippet_to_frame.py      # unchanged (already handles 16-frame stride)
│   │   └── metrics.py               # unchanged (compute_frame_metrics)
│   ├── models/
│   │   └── rtfm_i3d.py              # unchanged (FM head + MILHead + ln_i3d)
│   ├── train.py                     # MODIFIED — ADD train_one_epoch_i3d + validate_i3d + dispatch
│   └── evaluate.py                  # MODIFIED — REWRITE _build_frame_arrays xd_i3d branch
├── configs/
│   └── rtfm_i3d.yaml                # unchanged (unless D-11 fallback triggers)
├── scripts/
│   └── run_ablations.py             # unchanged (QUEUES["rtfm_gate"] already correct)
└── tests/
    ├── test_loaders_i3d.py          # NEW
    ├── test_train_i3d.py            # NEW
    ├── test_xd_annotations.py       # NEW
    └── test_evaluate_xd_i3d.py      # NEW
```

### Pattern 1: Parallel-function dispatch (D-04)

**What:** Instead of making `build_dataloaders`, `train_one_epoch`, `validate` polymorphic on `cfg['dataset']`, add parallel `_i3d` variants and branch once in `main()`.

**When to use:** When the contract diverges (different Dataset return shape, different kwargs passed to model, different mask semantics) and polymorphic dispatch would bloat the function body with `if ds == 'xd_i3d'` branches.

**Example:**
```python
# Source: D-04 + src/train.py existing structure
# src/train.py::main() — dispatch branch inserted after apply_cli_overrides

def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = load_config(args.config)
    cfg = apply_cli_overrides(cfg, args)
    set_deterministic(int(cfg["seed"]))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    run_dir_name = args.run_name if args.run_name else run_name(cfg)
    run_dir = Path(cfg["paths"]["results_dir"]) / run_dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot_config(cfg, run_dir / "config_snapshot.json")
    csv_logger = CSVLogger(run_dir / "train_log.csv")
    wandb_logger = WandbLogger(cfg, run_dir)
    model = build_model(**cfg["model"]).to(device)
    optimizer = build_optimizer(model.parameters(), cfg["train"])
    scheduler = build_scheduler(optimizer, cfg["train"])
    early = EarlyStopping(patience=int(cfg["train"]["patience"]))
    best_path = run_dir / "best_model.pth"
    last_path = run_dir / "last_model.pth"

    # ---- Dispatch on cfg['dataset'] (D-04) ----
    if cfg.get("dataset") == "xd_i3d":
        (nor_loader, abn_loader), val_loader = build_dataloaders_i3d(cfg)
        train_fn = train_one_epoch_i3d
        val_fn = validate_i3d
    else:
        (nor_loader, abn_loader), val_loader = build_dataloaders(cfg)
        train_fn = train_one_epoch
        val_fn = validate

    try:
        for epoch in range(int(cfg["train"]["epochs"])):
            train_loss = train_fn(model, nor_loader, abn_loader, optimizer, device, cfg["train"])
            val_loss   = val_fn(model, val_loader, device, cfg["train"])
            # ... (rest of loop unchanged)
```

**Why this pattern over polymorphism:**
1. The `MILFeatureDataset` return shape is `{'skel': [T,256], 'clip': [T,1024], 'mask': [T], 'label': float}` while `I3DFeatureDataset` returns `{'i3d': [5,T,1024], 'label': float, 'video_id': str}`. A polymorphic `train_one_epoch` would need to branch on dict keys at every access.
2. The i3d path does NOT produce a mask from the dataset (all ones synthesized in collate) while the UCF path CAN produce padded positions (zero-padded + mask=0 for N<T; see src/data/dataset.py:248 — but actually RTFM-revised uses sample-with-replacement → all-ones mask too). Both paths emit all-ones masks in practice, which is auditable.
3. Preserves C3 (src/eval/test_loader.py guard): the i3d training path does not reach into src/eval/, consistent with Phase 4 D-07/D-08.

### Pattern 2: Crop-as-sample collate with explicit reshape (D-05)

**What:** DataLoader-level flatten of the 5-crop dim into the batch dim, producing MIL bags of size `B*5` without touching the training loop.

**When to use:** When the dataset's natural unit is a video (with 5 crops as augmentations) but the training loss treats each crop as an independent bag sample.

**Example:**
```python
# Source: D-05 + I3DFeatureDataset.__getitem__ shape contract
# src/data/loaders.py::collate_i3d_train

def collate_i3d_train(batch_list: list[dict]) -> dict:
    """Flatten [B, 5, T, 1024] -> [B*5, T, 1024] for MIL bag materialization.

    Inputs:
      batch_list: list of B dicts from I3DFeatureDataset(mode='train' or 'val'):
        {'i3d': torch.Tensor[5, T, 1024], 'label': float, 'video_id': str}

    Output: dict suitable for model.forward + mil_ranking_loss:
      {
        'i3d':      torch.Tensor[B*5, T, 1024],
        'label':    torch.Tensor[B*5],       # each video's label repeated 5 times
        'mask':     torch.Tensor[B*5, T],    # all ones (no padding; D-05)
        'video_id': list[str]                # length B*5, each vid repeated 5x
      }
    """
    B = len(batch_list)
    T = batch_list[0]["i3d"].shape[1]
    assert all(b["i3d"].shape == (5, T, 1024) for b in batch_list), \
        f"I3D collate expected all samples shape [5, {T}, 1024]; got varied shapes"

    i3d_stack = torch.stack([b["i3d"] for b in batch_list], dim=0)  # [B, 5, T, 1024]
    i3d_flat  = i3d_stack.reshape(B * 5, T, 1024)

    labels_rep = torch.tensor(
        [b["label"] for b in batch_list for _ in range(5)],
        dtype=torch.float32,
    )  # [B*5]

    mask = torch.ones(B * 5, T, dtype=torch.float32)

    vids_rep = [b["video_id"] for b in batch_list for _ in range(5)]
    return {"i3d": i3d_flat, "label": labels_rep, "mask": mask, "video_id": vids_rep}
```

**Why this implementation over `torch.utils.data.default_collate`:**
1. default_collate stacks tensors into `[B, 5, T, 1024]` — the reshape to `[B*5, T, 1024]` still has to happen somewhere; doing it in collate keeps `train_one_epoch_i3d` simple.
2. Explicit shape assertion catches Pitfall 4 filter bugs early (a video with 4-crop-only gets padded from crop 0 inside `_load_crops`, so all samples should reach collate with exactly 5 crops).
3. Label repetition is explicit and auditable (the D-12 audit log checks `n_normal == B*5 == 15` on first 3 epochs).

### Pattern 3: Annotation module mirror (D-10)

**What:** `src/eval/xd_annotations.py` is a structural mirror of `src/eval/ucf_annotations.py`, preserving the `VideoAnnotation` frozen-dataclass + `parse_annotations` + `frame_labels` three-function shape.

**Example:**
```python
# Source: mirror of src/eval/ucf_annotations.py with Wu format adaptation
# src/eval/xd_annotations.py

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

# Wu format: "video_id[.mp4] s1 e1 s2 e2 ..." (pairs of frame indices,
# any number of pairs >= 1; video_id may or may not carry .mp4 suffix;
# normal test videos are OMITTED from the file entirely).

@dataclass(frozen=True)
class VideoAnnotation:
    """Immutable Wu 2020 XD-Violence row keyed by normalized video_id."""
    video_id: str              # without trailing .mp4; matches data/splits/xd_test.txt IDs
    category: str              # parsed from label suffix, e.g. "B2" or "Normal"
    intervals: Tuple[Tuple[int, int], ...]  # ((s1, e1), (s2, e2), ...) — frame indices

    @property
    def is_normal(self) -> bool:
        return len(self.intervals) == 0


def parse_xd_annotations(path: Path) -> Dict[str, VideoAnnotation]:
    """Parse Wu 2020 annotations.txt. Returns {video_id_normalized: VideoAnnotation}.

    Normalization: strip trailing '.mp4' from the first column to match
    data/splits/xd_test.txt ID format (verified: this maps 500/500 abnormal
    test videos cleanly).

    Categories: parsed from the `_label_X1-X2-X3` suffix in the video_id. For Phase 4b
    the category column is informational — D-13 disables per-category breakdown for
    the rtfm variant. Phase 4c will consume the category output.

    File omissions: Wu's annotations.txt only contains entries for the 500 ABNORMAL
    test videos. The 300 normal test videos have no entries; the evaluate.py caller
    handles this by defaulting labels to all-zero for missing IDs.
    """
    annos: Dict[str, VideoAnnotation] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            vid_raw = parts[0]
            # Strip .mp4 suffix if present (Wu file has mixed: some rows have .mp4,
            # some don't). Test split files carry NO .mp4 suffix.
            vid = vid_raw[:-4] if vid_raw.endswith(".mp4") else vid_raw
            ints_flat = [int(p) for p in parts[1:]]
            if len(ints_flat) % 2 != 0:
                raise ValueError(
                    f"Wu annotation has odd number of interval endpoints: {line!r}"
                )
            intervals = tuple(
                (ints_flat[i], ints_flat[i+1]) for i in range(0, len(ints_flat), 2)
            )
            # Parse category from label suffix (e.g., "_label_B2-0-0" -> "B2")
            category = _parse_category(vid)
            annos[vid] = VideoAnnotation(
                video_id=vid, category=category, intervals=intervals
            )
    return annos


def _parse_category(video_id: str) -> str:
    """Parse Wu category from video_id suffix. Multi-label -> first label.

    Suffix formats (verified from Wu file):
      _label_A                → "Normal"   (never appears in annotations.txt, but we handle it)
      _label_B1-0-0           → "B1"
      _label_B6-0-0           → "B6"
      _label_G-B2-B6          → "G"        (first listed; Phase 4c picks primary)
      _label_B2-G-0           → "B2"

    Returns category code (e.g., "B1", "B2", "B4", "B6", "G", or "Normal").
    For Phase 4c's Fighting/Abuse/Riot breakdown, callers map:
      B1 -> "Fighting"   (dynamic violence between people)
      B2 -> "Shooting"
      B4 -> "Riot"
      B5 -> "Abuse"
      B6 -> "Car accident"
      G  -> "Explosion"
    """
    if "_label_" not in video_id:
        return "Unknown"
    suffix = video_id.split("_label_", 1)[1]
    if suffix == "A":
        return "Normal"
    # Take first non-zero-non-dash code
    first = suffix.split("-", 1)[0]
    return first


def xd_frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray:
    """Build [n_frames] binary label vector from Wu intervals.

    Per-frame label = union of all intervals. Endpoints clamped to [0, n_frames]
    so intervals that slightly overshoot the decoded video length (observed in
    71 abnormal test videos by 1-15 frames — confirmed against E:/i3d-features
    RGBTest N_snippets*16) are safe.
    """
    labels = np.zeros(n_frames, dtype=np.int64)
    for s, e in anno.intervals:
        s_c = max(0, int(s))
        e_c = min(n_frames, int(e))
        if e_c > s_c:
            labels[s_c:e_c] = 1
    return labels
```

**Why a namedtuple/dataclass-shaped struct over typed dict:**
1. Matches `src/eval/ucf_annotations.py::VideoAnnotation` exactly → test patterns and eval patterns parallelize.
2. `@dataclass(frozen=True)` prevents accidental mutation; Phase 5 TTA code may later read annotations.
3. The `@property is_normal` mirror gives `if anno.is_normal: skip` ergonomics in callers.

### Pattern 4: Sentinel-guarded all-zero labels for unannotated normals

**What:** Wu's `annotations.txt` contains only abnormal test videos (500 of 800). Normal test videos (300) have no annotation entry. The `_build_frame_arrays` xd_i3d branch MUST default missing entries to all-zero labels — this is correct (normal videos have no anomaly frames) but requires an explicit `if vid in annos` guard, not a crash.

**Example:**
```python
# Source: rewrite of src/evaluate.py::_build_frame_arrays lines 180-192
# The key pattern: parallel the UCF branch's "annotation-or-normal-default" logic

if ds == "xd_i3d":
    snippet_window = 16
    upsample_factor = 1

    ann_dir_cfg = cfg.get("paths", {}).get("annotations_dir")
    ann_path = None
    if ann_dir_cfg:
        candidate = Path(ann_dir_cfg) / "xd_temporal.txt"
        if candidate.exists():
            ann_path = candidate
    if ann_path is None:
        ann_path = _PROJECT_ROOT / "data" / "annotations" / "xd_temporal.txt"

    from src.eval.xd_annotations import parse_xd_annotations, xd_frame_labels
    annos = parse_xd_annotations(ann_path) if ann_path.exists() else {}

    frames_map, labels_map, cats_map = {}, {}, {}
    for vid, scores in per_video_snippet_scores.items():
        n_frames = len(scores) * snippet_window
        frames_map[vid] = snippet_to_frame(
            scores, n_frames=n_frames,
            snippet_window=snippet_window, upsample_factor=upsample_factor,
        )
        if vid in annos:
            anno = annos[vid]
            labels_map[vid] = xd_frame_labels(anno, n_frames)
            # D-13: cats_map populated but compute_frame_metrics skips single-category.
            # Phase 4c consumes this for Fighting/Abuse/Riot breakdown.
            cats_map[vid] = anno.category
        else:
            # Normal test video (Wu annotations omit these)
            labels_map[vid] = np.zeros(n_frames, dtype=np.int64)
            cats_map[vid] = "Normal"
    return frames_map, labels_map, cats_map
```

### Anti-Patterns to Avoid

- **Polymorphic `build_dataloaders(cfg)` that branches on `cfg['dataset']`:** leaks i3d-specific assumptions (5-crop, no mask synthesis) into the UCF code path; D-04 explicitly rejects this.
- **Computing Wu annotation fps from 24fps constant:** the file's frame indices ARE the original-video frame counts (confirmed by bit-identical XDVioDet gt.npy match) — do NOT multiply by `video_fps/24` or similar conversions.
- **Casting `v=YouTubeID` entries to a different prefix:** the annotation file and test split agree: both files carry the `v=` prefix on YouTube-sourced videos, no normalization needed except `.mp4` suffix strip.
- **Loading Wu annotations via a deep-library parser (e.g. pandas):** adds a dependency for a 500-line whitespace-separated text file; plain `line.split()` is sufficient, matching `ucf_annotations.py`.
- **Hard-coding `snippet_window=16` inside `_build_frame_arrays`:** expose as config if Phase 4c's dual xd path lands a different stride. For Phase 4b, the stride is verified constant.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MIL Ranking Loss | Custom hinge + top-k impl | `src/losses/mil_loss.py::mil_ranking_loss` | Already RTFM-exact (k=3, margin=1.0 on sigmoid scores, sparsity+smoothness regs); passed Phase 3 tests |
| I3D feature loading | Raw `np.load` in train loop | `src/data/i3d_dataset.py::I3DFeatureDataset` | Pitfall 4 missing-crop filter + D-19 5-crop / crop-averaging switch + `allow_pickle=False` security |
| Snippet→frame broadcast | `np.repeat(scores, 16)` inline | `src/eval/snippet_to_frame.py::snippet_to_frame` | C4-guarded length-drift assertion (D-15 inherited); consistent with UCF path |
| Frame-level AUC/AP | `sklearn.metrics` call in a loop | `src/eval/metrics.py::compute_frame_metrics` | C4 length-assertion before every sklearn call; video-AUC + per-category pattern; already used by UCF path |
| Annotation parser | Ad-hoc `open().splitlines()` | `src/eval/xd_annotations.py::parse_xd_annotations` (new) mirroring `ucf_annotations.py` | Frozen-dataclass struct + `.mp4` suffix normalization + odd-interval ValueError |
| Deterministic training | Manual `torch.manual_seed` | `src/utils/seed.py::set_deterministic` + `seed_worker` + `make_generator` | CUBLAS_WORKSPACE_CONFIG + `torch.use_deterministic_algorithms(True)` + all three RNG seeds (torch, numpy, python) at once; D-12 bit-identical rerun depends on this |
| Checkpoint I/O | `torch.save` + manual rename | `src/utils/checkpoint.py::save_checkpoint_atomic` | tempfile-in-same-dir + `os.replace` atomicity; D-10 best_model policy already wired |
| Config hashing for reproducibility | Custom JSON canonicalization | `src/utils/config.py::config_hash` + `snapshot_config` | Used by D-12 bit-identical-rerun diagnostic (matches all 9 numeric keys across runs) |
| Subprocess orchestration | Shell script loop | `scripts/run_ablations.py::run_queue` | Already handles .done resume probe, log_error, results-index-append atomicity |
| wandb fallback | Conditional wandb imports | `src/utils/wandb_logger.py::WandbLogger` with `mode='disabled'` | Already tested with Rule 3 fallback in Phase 4 Tasks 2/3/4/5 |
| Unit test fixtures for I3D | Hand-crafted tmp_path scaffolding | `tests/fixtures/synthetic_eval.py::make_synthetic_i3d` | Already shipped (5-crop XD-style cache with `_label_A`/`_label_B1-0-0` IDs, split files); 5 train + 3 test videos |

**Key insight:** Phase 4b is almost entirely composition of existing utilities. The only *new* code is (a) `build_dataloaders_i3d` + `collate_i3d_train` (~60 LOC), (b) `train_one_epoch_i3d` + `validate_i3d` (~50 LOC), (c) `src/eval/xd_annotations.py` (~80 LOC), (d) the `_build_frame_arrays` xd_i3d branch rewrite (~20 LOC), and (e) the four test files (~300 LOC total). The Wu annotation parser is structurally identical to `ucf_annotations.py` — mostly a search-and-replace with Wu-specific format adjustments.

## Wu Annotation Format (verified this session)

### Source

| Property | Value |
|----------|-------|
| Canonical URL | `https://roc-ng.github.io/XD-Violence/images/annotations.txt` [VERIFIED: fetched this session, HTTP 200] |
| File size | ~6.2 KB (500 non-blank lines) [VERIFIED: `urllib.request.urlopen` + line count] |
| Project page | `https://roc-ng.github.io/XD-Violence/` (note: NOT `roseyu.com/XD-Violence/` — that domain now 404s) [VERIFIED: fetched this session] |
| Reference implementation | `https://github.com/Roc-Ng/XDVioDet` (ECCV 2020 official code) [VERIFIED: tree listing via GitHub API] |
| License | Not stated on project page; standard academic redistribution assumption (consistent with Phase 4 `data/annotations/ucf_temporal.txt` precedent) [CITED: roc-ng.github.io/XD-Violence] |

### Format specification (verified by downloading file + cross-matching with xd_test.txt)

```
<video_id>[.mp4] <s1> <e1> [<s2> <e2> [<s3> <e3> ...]]
```

- **Line count:** 500 non-blank lines [VERIFIED: fresh download this session]
- **Columns distribution:**
  - 3 columns (1 interval):  240 lines (48.0%)
  - 5 columns (2 intervals): 105 lines (21.0%)
  - 7 columns (3 intervals):  59 lines (11.8%)
  - 9–45 columns (4–22 intervals): 96 lines (19.2%)
  - All lines have `1 + 2*K` columns for `K >= 1` intervals (no odd-endpoint rows) [VERIFIED]
- **Normal videos:** NOT present in annotations.txt. Only the 500 abnormal test videos have entries. Normal test videos (300 in `data/splits/xd_test.txt`) are inferred from the omission. [VERIFIED: 0/300 normals match; 500/500 abnormals match]
- **Frame indices:** original-video frame counts at the native video FPS (not 24fps-normalized; not snippet-indexed). Cross-verified: the sum of interval lengths across all test videos clamped to `N_snippets * 16` produces exactly 537,805 positive frames, matching 23.08% of 2,330,384 total frames, which is bit-identical to XDVioDet's `list/gt.npy` positive-frame fraction. [VERIFIED]
- **Interval overshoot:** 71 abnormal videos have intervals that exceed `N_snippets * 16` by 1–15 frames (e.g., `Black.Hawk.Down.2001__#02-00-12_02-01-29_label_B2-0-0` has interval ending at 1848 but `N=115 * 16 = 1840`). Root cause: interval endpoints are in the original video's full frame count; the I3D feature extractor may have dropped the final sub-16-frame remainder. The `xd_frame_labels` clamp-to-`n_frames` pattern (identical to `ucf_annotations.py::frame_labels` line 89-90) handles this without error. [VERIFIED]

### ID normalization

| Raw annotation `parts[0]` | Normalized to | Matches split file |
|---------------------------|--------------|-------------------|
| `A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_A.mp4` | `A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_A` (strip `.mp4`) | ✓ |
| `v=S-7rRLrxnVQ__#1_label_B4-0-0` | unchanged (no `.mp4` suffix) | ✓ |
| `v=wVey5JDRf_g__#00-00-00_00-01-20_label_B6-0-0` | unchanged | ✓ |
| `Bad.Boys.1995__#01-33-51_01-34-37_label_B2-0-0` | unchanged | ✓ |

**Normalization rule:** `vid = parts[0][:-4] if parts[0].endswith('.mp4') else parts[0]`. After this step, all 500 abnormal IDs match `xd_test.txt` exactly (no other transformations needed). The `v=` prefix is preserved for YouTube-sourced videos (verified: `xd_test.txt` also carries the `v=` prefix on these). [VERIFIED: 500/500 after normalization]

### Coverage check (cross-verified with on-disk I3D cache)

| Metric | Expected | Measured | Match |
|--------|----------|----------|-------|
| xd_test.txt entries | 800 | 800 | ✓ |
| xd_test.txt normal (endswith `_label_A`) | 300 | 300 | ✓ |
| xd_test.txt abnormal (not endswith `_label_A`) | 500 | 500 | ✓ |
| Wu annotations.txt line count | ~500 | 500 | ✓ |
| Abnormal videos covered in annotations | 500 | 500 (after `.mp4` strip) | ✓ |
| RGBTest crop 0 .npy count | 800 (1 per video) | 800 | ✓ |
| Total frames `sum(N_snippets * 16)` | — | 2,330,384 | — |
| XDVioDet `list/gt.npy` length | — | 2,330,384 | ✓ bit-identical |
| Positive-frame fraction | — | 0.2308 | ✓ matches gt.npy |

## I3D Cache Validation

### Cache layout on disk

| Path | File count | Shape per .npy | Meaning |
|------|-----------|----------------|---------|
| `E:/i3d-features/i3d-features/RGB/` | 16,124 | `[N, 1024]` float32 | 5 crops × 3224.8 videos ≈ 3225 videos with at least 1 crop (Pitfall 4: 729 videos from 3954 train-split are missing from cache) |
| `E:/i3d-features/i3d-features/RGBTest/` | 4,000 | `[N, 1024]` float32 | 5 crops × 800 videos; 100% coverage of `data/splits/xd_test.txt` [VERIFIED: 800/800] |
| `E:/i3d-features/i3d-features/Flow/` | (n/a, not probed) | presumably `[N, 1024]` float32 | RGB+Flow fallback for D-11 cascade step (2); not used in Phase 4b primary path |
| `E:/i3d-features/i3d-features/FlowTest/` | (n/a, not probed) | presumably `[N, 1024]` float32 | ditto |

File naming: `<video_id>__<c>.npy` for c in 0..4. Example: `A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_A__0.npy` (confirmed 5/5 crops present, shape (360, 1024) per crop). [VERIFIED]

### Stride verification (answers CONTEXT.md D-08 open item)

**Finding:** I3D cache stride = **16 frames per snippet**. `snippet_window=16`, `upsample_factor=1`. [VERIFIED via 4 independent cross-checks:]

1. **XDVioDet test.py** references `np.repeat(pred, 16)` to expand predictions to frames. [CITED: https://github.com/Roc-Ng/XDVioDet/blob/master/test.py]
2. **XDVioDet gt.npy** is a flat float32 array of 2,330,384 frame labels. [VERIFIED: downloaded + parsed]
3. Our on-disk computation `sum(N_snippets * 16 for each of 800 test videos)` = **2,330,384 frames** — bit-identical to XDVioDet gt.npy length. [VERIFIED this session]
4. Intersection of Wu intervals with clamped `[0, N*16]` ranges produces **23.08% positive frames**, matching XDVioDet gt.npy's 23.08% positive fraction. [VERIFIED this session]

**Interval fps:** Frame indices in the Wu annotation file correspond directly to the original video's 1-based frame count (not resampled to 24fps). This is consistent with `np.repeat(pred, 16)` — no rescaling needed.

### Feature dimension

**1024-d per snippet per crop** (not 2048-d). This matches:
- RTFM's paper description of I3D-RGB features (Kinetics-I3D outputs 1024-d after the RGB stream's final avg-pool — the 2048-d in RTFM's `model.py` is their internal `Aggregate(len_feature=2048)` which consumes RGB+Flow concat, NOT the raw I3D feature input).
- Our rtfm_i3d.yaml:16 `i3d_dim: 1024`.
- `RTFMI3D.__init__(i3d_dim=1024)` default.

**Implication for D-11 fallback:** If the primary gate misses and RGB+Flow (D-11 step 2) is invoked, the concat would produce 2048-d. That requires `configs/rtfm_i3d_rgbflow.yaml` with `i3d_dim: 2048` AND an `RTFMI3D(i3d_dim=2048)` instantiation — the `ln_i3d` shape would change. This is a real fork beyond the MVP scope; CONTEXT.md correctly defers it.

## RTFM / MGFN Anchor Verification

### Primary anchor: RTFM XD-I3D AP = 77.81%

| Source | Value | Notes |
|--------|-------|-------|
| arXiv paper (Tian et al., ICCV 2021, 2101.10030) | "best AP scores, with 77.81% using I3D features" on XD-Violence | [CITED: quickreview excerpt + openaccess PDF citation] |
| RTFM config (`k_abn = k_nor = num_segments // 10`) | 3 when `num_segments=32` | Matches our `k_topk: 3` in `rtfm_i3d.yaml:34` [VERIFIED via WebFetch of `tianyu0207/RTFM/main/model.py`] |
| RTFM `option.py` defaults | `batch-size: 32`, `lr: [0.001]*15000`, `max-epoch: 15000`, `num-classes: 1`, `modality: RGB` | [VERIFIED via WebFetch] |
| RTFM `model.py` Aggregate | `Aggregate(len_feature=2048)` — MTN module processing RGB+Flow CONCAT features | Our `RTFMI3D` MVP is RGB-ONLY (1024-d) + no MTN — a simplification [VERIFIED] |

**Gate math:** Our configured `data.batch_size=3 * 5 crops = 15 effective bag samples`, `num_segments=T=32`, `k_topk=3`. RTFM uses `batch_size=32 * 10 crops = 320 effective samples` on UCF-style 10-crop. Our ratio `k/bag = 3/15 = 0.2` matches RTFM's `3/32 = 0.094`? No — the RTFM per-bag k is `num_segments // 10 = 3` (per-video top-k), not per-batch. Our per-video top-k is also 3. **The ratio is per-bag, not per-batch** — confirmed equivalent.

**±1% = [76.81%, 78.81%] pass band** per D-03.

### Secondary anchor correction: MGFN I3D-RGB AP = 79.19% (not 80.11%)

| Source | Value | Context |
|--------|-------|---------|
| MGFN paper (Chen et al., AAAI 2023, 2211.15098) | 80.11% AP on XD-Violence | **VideoSwin-RGB features** — NOT vanilla I3D [CITED: quickreview, emergentmind] |
| Derived MGFN I3D-RGB AP | 79.19% | "outperforms RTFM by 1.38% AP on XD-Violence" (using same I3D features) → 77.81 + 1.38 ≈ 79.19 [CITED: WebSearch synthesis] |

**CONTEXT.md D-11 upper anchor correction:**
- Current D-11 wording: "Relax anchor to MGFN 80.11% only if miss < 3pp"
- Research finding: 80.11% is VideoSwin, not I3D. A 1024-d I3D-RGB gate cannot reasonably target 80.11% (wrong backbone). The correct I3D-RGB upper anchor is **79.19%**.
- **Planner should update D-11:** "Relax anchor to MGFN 79.19% only if miss < 3pp. The 80.11% VideoSwin result is a known upper bound but not reachable with 1024-d I3D-RGB features on disk." The config comment at `rtfm_i3d.yaml:48` already flags this ("possibly VideoSwin; not vanilla I3D"), so the correction is aligned with existing codebase awareness.

The ±1% primary anchor (RTFM 77.81 ± 1% = [76.81, 78.81]) is UNCHANGED — this is the Phase 4b gate.

### Bag-size sanity: does our `batch_size=3` preserve enough signal?

| Variable | RTFM published | Our `rtfm_i3d.yaml` | Ratio check |
|----------|---------------|--------------------|-------------|
| `num_segments` (T) | 32 | 32 | ✓ identical |
| `k_abn = k_nor` | 3 | 3 (`k_topk`) | ✓ identical |
| crops per video | 10 (UCF/ShanghaiTech) | 5 (XD per D-19) | XD cache has only 5 crops on disk |
| `batch_size` videos per step | 32 (normal) + 32 (abnormal) | 3 (nor) + 3 (abn) | Much smaller |
| Effective MIL samples per step | 320 per queue = 640 both | 15 per queue = 30 both | Much smaller |

**Concern:** Our effective batch is 21× smaller than RTFM's. This is by-design (Pitfall 3: preserving `k/bag` ratio), but it does mean step-count must compensate. The epoch count is pinned at 50 (`rtfm_i3d.yaml:31`) with early stopping patience=10. At ~3225 train videos split 50/50 nor/abn ≈ 1612 videos per queue / `batch_size=3` = 537 steps per epoch — giving ~26,850 total gradient updates across 50 epochs (matching RTFM's `max-epoch: 15000` as a step budget, not epoch budget, reasonably).

**Risk mitigation:** D-12's bag-size audit log on first 3 epochs. If the loss plateaus unexpectedly high, try:
1. `batch_size: 16` (matches D-05 "post-gate empirical tuning" comment) — but `16 * 5 = 80 effective` breaks the `k/bag = 3/15` ratio.
2. Alternatively, increase `T` from 32 → 64 to match some RTFM forks.

Both are D-11 cascade territory, not Phase 4b MVP.

## Runtime State Inventory

> Phase 4b is a code-change phase, NOT a rename/refactor/migration. No runtime state inventory needed.

**State categories checked (all negative):**
- Stored data: no database keys or collection names carry "xd_i3d" or "rtfm_i3d" strings needing migration — all references are either filesystem paths or Python dict keys internal to the process.
- Live service config: wandb runs in `mode=disabled` (no cloud state); no n8n/Datadog/Cloudflare registrations.
- OS-registered state: no Windows Task Scheduler / pm2 / systemd entries reference Phase 4b artifacts.
- Secrets/env vars: `CUBLAS_WORKSPACE_CONFIG` is set in `src/train.py:5` and `src/evaluate.py:21`; no new env var requirements.
- Build artifacts: `src/` is imported directly from the working tree (no egg-info, no compiled wheels). `results/xd_i3d_rtfm_i3d_s42/` does NOT currently exist (verified: `ls results/` shows only UCF runs) — so no pre-existing artifact to clean up. The Phase 4 run was cleaned up when the queue halted.

**Conclusion:** Nothing to migrate. Planner does not need a cleanup task.

## Common Pitfalls

### Pitfall 1: Missing mask for xd_i3d in `mil_ranking_loss`

**What goes wrong:** `mil_ranking_loss(scores, mask, n_normal=, k=3, ...)` REQUIRES a mask tensor; it uses `scores.masked_fill(mask == 0, float('-inf'))` to suppress padded positions before top-k. If the collate function forgets to emit `mask`, the loss silently NaNs out.

**Why it happens:** `I3DFeatureDataset.__getitem__` does NOT emit a mask (it uses `_resample_T` sample-with-replacement, so there are no padded positions). The `collate_i3d_train` function must synthesize `mask = torch.ones(B*5, T)`.

**How to avoid:** D-05 pattern (verified in "Pattern 2" above) explicitly emits `mask` as all-ones. Unit test `test_loaders_i3d.py` MUST assert `batch['mask'].sum() == B * 5 * T` (all-ones). The same pattern is how `MILFeatureDataset._sample_or_pad` emits its all-ones mask (src/data/dataset.py:248).

**Warning signs:** `train_loss=nan` from epoch 0; `TypeError: mil_ranking_loss() missing 1 required positional argument: 'mask'`.

### Pitfall 2: Normal test videos missing from Wu annotations

**What goes wrong:** Wu's `annotations.txt` only has entries for 500 abnormal test videos. The 300 normal test videos (`_label_A` suffix) have no annotation entry. A naive `labels_map[vid] = xd_frame_labels(annos[vid], ...)` raises `KeyError` on 300 videos, crashing `compute_frame_metrics`.

**Why it happens:** Convention — normal videos have zero anomaly frames, so an all-zeros label vector is semantically correct and the Wu authors omitted them to save space.

**How to avoid:** `_build_frame_arrays` xd_i3d branch MUST guard `if vid in annos: ... else: np.zeros(n_frames)` (Pattern 4 above). Unit test `test_evaluate_xd_i3d.py` MUST include at least one normal video in the synthetic fixture (already true: `make_synthetic_i3d` alternates `_label_A` / `_label_B1`).

**Warning signs:** `KeyError: 'A.Beautiful.Mind.2001__#00-25-20_00-29-20_label_A'` during eval.

### Pitfall 3: Interval endpoints exceeding `N_snippets * 16`

**What goes wrong:** 71 out of 500 abnormal test videos have interval endpoints that exceed `N_snippets * 16` by 1-15 frames. A non-clamping `labels[s:e] = 1` would error with `IndexError` or silently pad the label vector beyond n_frames, mismatching frame_scores length and tripping the C4 assertion.

**Why it happens:** I3D extractor drops the final sub-16-frame remainder; Wu's intervals are in the original full frame count.

**How to avoid:** Clamp in `xd_frame_labels`: `e_c = min(n_frames, int(e))` (Pattern 3 above, identical to `ucf_annotations.py::frame_labels` line 90). Unit test `test_xd_annotations.py` MUST include an "interval-overshoot" case where an interval endpoint exceeds `n_frames` — assert the output is truncated, not errored.

**Warning signs:** `AssertionError: C4 REGRESSION at <vid>: scores=200 labels=250` during compute_frame_metrics.

### Pitfall 4: 5-crop label replication drift

**What goes wrong:** `collate_i3d_train` must replicate each video's scalar label FIVE times (once per crop). If the replication pattern is wrong (e.g., `labels = [b['label'] for b in batch_list].repeat(5)` instead of `[label for b for _ in range(5)]`), the first crop from each video all get one label and the second crop all get another — destroying the bag structure.

**Why it happens:** Python list comprehension ordering matters. `[x for b in batch_list for _ in range(5)]` repeats each label CONSECUTIVELY (5 instances before moving to next video). `list(itertools.chain(*([b['label']]*5 for b in batch_list)))` is equivalent. `torch.tensor([...]*5)` would repeat the whole list — BUG.

**How to avoid:** Explicit `[b['label'] for b in batch_list for _ in range(5)]` pattern (Pattern 2 above). Unit test MUST:
1. Build 2 normal + 2 abnormal videos.
2. Verify `labels[0..4] == 0.0` (first video = normal, 5 crops).
3. Verify `labels[5..9] == 0.0` (second video = normal).
4. Verify `labels[10..14] == 1.0` (third video = abnormal, first crop replica).
5. Verify partitioning by `labels.mean()` matches expected.

**Warning signs:** Training loss oscillates without converging; snippet score distributions are entropy-flat.

### Pitfall 5: Pre-existing `results/xd_i3d_rtfm_i3d_s42/` from Phase 4 Plan 04-06

**What goes wrong:** The Phase 4 Plan 04-06 Task 2 attempted the RTFM gate run and created a partial `results/xd_i3d_rtfm_i3d_s42/` directory that MAY still exist (it would contain a stale `.done` marker triggering `run_ablations.py`'s "skip" path, or a stale `config_snapshot.json` that doesn't match the current code).

**Why it happens:** `run_ablations.py::is_done()` at line 124 skips any spec where `.done` exists. A leftover `.done` from the pre-fix partial run would make the gate rerun a no-op.

**How to avoid:** Planner's task sequence MUST include `rm -rf D:/ViolenceCC/results/xd_i3d_rtfm_i3d_s42/` BEFORE the rtfm_gate queue invocation (both the smoke run AND the full gate run). Verified in this research session: the directory does NOT currently exist (the Phase 4 cleanup removed it per 04-06-UAT.md "results/xd_i3d_rtfm_i3d_s42/ (partial, removed for clean retry)" note). **Still, plan for the cleanup step idempotently** — if the smoke test is rerun for any reason, the fresh queue call would skip it.

**Warning signs:** `run_ablations.py` outputs `[skip] xd_i3d_rtfm_i3d_s42 (.done present)` on the gate run; no new rows appended to results-index.csv.

### Pitfall 6: `_parse_label_xd` collision with `_label_` substring

**What goes wrong:** `label = 0 if vid.endswith("_label_A") else 1` is correct per D-06, but filenames with `_label_A1` or `_label_A2-0-0` suffixes would match `_label_A` via `endswith`... wait, actually `"_label_A1".endswith("_label_A")` is False (case-sensitive exact match). But `_label_A`-prefixed anomaly codes don't exist in the Wu convention (labels are A, B1-B6, G, M) — VERIFIED by parsing all 500 abnormal test videos. Safe.

**Why it happens:** Imagined pitfall — defensive check for future labels. Currently not a risk.

**How to avoid:** Unit test `test_loaders_i3d.py` MUST include label parsing for at least one representative from each of `_label_A`, `_label_B1-0-0`, `_label_B6-0-0`, `_label_G-B2-B6`. Assert 1 vs 0 mapping is correct.

**Warning signs:** `n_normal = 0` in build_dataloaders_i3d; "[i3d_dataset] WARNING: no normal videos after filtering" in stderr.

### Pitfall 7: `persistent_workers=True` on Windows with num_workers > 0

**What goes wrong:** Windows spawn start method + `persistent_workers=True` can hang on `DataLoader` shutdown if workers have not cleanly exited. Our `build_dataloaders` already handles this: `persistent = num_workers > 0`. `collate_i3d_train` is a module-level function (not a lambda), so it pickles cleanly.

**Why it happens:** Lambdas inside class scope fail to pickle on Windows spawn. Our pattern inherits the fix.

**How to avoid:** `collate_i3d_train` MUST be defined at module scope in `src/data/loaders.py` (not inside `build_dataloaders_i3d`). Unit test MUST construct a DataLoader with `num_workers=0` (CI default) to avoid the multiprocessing complexity in tests.

**Warning signs:** "PicklingError: Can't pickle <function>" on worker spawn; DataLoader hang on test exit.

## Code Examples

### Example 1: `src/data/loaders.py` additions (shape-audited)

```python
# Source: combining D-04 + D-05 + Pattern 2 + src/data/loaders.py existing
# Parallel to build_dataloaders at line 52; follow same seed/generator conventions.

from torch.utils.data import Subset

from src.data.i3d_dataset import I3DFeatureDataset


def collate_i3d_train(batch_list: list[dict]) -> dict:
    """D-05 5-crop-as-sample flatten. Module-scope (Windows spawn)."""
    B = len(batch_list)
    # Pitfall 4: all samples have been crop-padded to 5 inside _load_crops.
    i3d_stack = torch.stack([b["i3d"] for b in batch_list], dim=0)  # [B, 5, T, 1024]
    B, n_crops, T, D = i3d_stack.shape
    assert n_crops == 5 and D == 1024, f"unexpected i3d shape {tuple(i3d_stack.shape)}"
    i3d_flat  = i3d_stack.reshape(B * 5, T, 1024)
    labels    = torch.tensor(
        [b["label"] for b in batch_list for _ in range(5)], dtype=torch.float32
    )
    mask      = torch.ones(B * 5, T, dtype=torch.float32)
    vids      = [b["video_id"] for b in batch_list for _ in range(5)]
    return {"i3d": i3d_flat, "label": labels, "mask": mask, "video_id": vids}


def build_dataloaders_i3d(cfg: dict):
    """D-04 parallel function; returns ((nor, abn), val)."""
    paths = cfg["paths"]
    data_cfg = cfg["data"]
    T = data_cfg.get("T", 32)
    bs = data_cfg["batch_size"]                    # 3 per D-05 + Pitfall 3
    num_workers = data_cfg.get("num_workers", 0)
    pin_memory = data_cfg.get("pin_memory", False)
    seed = cfg.get("seed", 42)

    i3d_dir = str(paths["i3d_features"])
    train_ds = I3DFeatureDataset(
        split_file=f"{paths['splits_dir']}/xd_train.txt",
        feature_dir=f"{i3d_dir}/RGB",
        mode="train", T=T,
    )
    val_ds = I3DFeatureDataset(
        split_file=f"{paths['splits_dir']}/xd_val.txt",
        feature_dir=f"{i3d_dir}/RGB",
        mode="val", T=T,
    )

    nor_idx = [i for i, v in enumerate(train_ds.video_ids) if v.endswith("_label_A")]
    abn_idx = [i for i, v in enumerate(train_ds.video_ids) if not v.endswith("_label_A")]

    g_nor = make_generator(seed)
    g_abn = make_generator(seed + 1)
    g_val = make_generator(seed + 2)

    persistent = num_workers > 0
    common = dict(
        batch_size=bs, num_workers=num_workers,
        worker_init_fn=seed_worker,
        pin_memory=pin_memory, persistent_workers=persistent,
        drop_last=True, collate_fn=collate_i3d_train,
    )
    nor_loader = DataLoader(Subset(train_ds, nor_idx), shuffle=True, generator=g_nor, **common)
    abn_loader = DataLoader(Subset(train_ds, abn_idx), shuffle=True, generator=g_abn, **common)
    val_loader = DataLoader(
        val_ds, batch_size=bs * 2, num_workers=num_workers,
        worker_init_fn=seed_worker, pin_memory=pin_memory,
        persistent_workers=persistent, drop_last=False,
        shuffle=False, generator=g_val, collate_fn=collate_i3d_train,
    )
    return (nor_loader, abn_loader), val_loader
```

### Example 2: `src/train.py` additions

```python
# Source: D-04 + mirror of existing train_one_epoch at line 85
# train_one_epoch_i3d consumes the `i3d` / `mask` keys from collate_i3d_train

def train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, device, train_cfg):
    model.train()
    losses = []
    steps_per_epoch = min(len(nor_loader), len(abn_loader))
    nor_iter = iter(nor_loader)
    abn_iter = iter(abn_loader)
    for step in range(steps_per_epoch):
        nor_batch = next(nor_iter)
        abn_batch = next(abn_iter)
        i3d = torch.cat([nor_batch["i3d"], abn_batch["i3d"]], dim=0).to(device)
        mask = torch.cat([nor_batch["mask"], abn_batch["mask"]], dim=0).to(device)
        n_normal = nor_batch["i3d"].shape[0]

        # D-12 bag-size audit: first 3 epochs, first step only
        if step == 0 and train_cfg.get("_audit_epoch", 0) < 3:
            import sys
            print(
                f"[i3d_audit] n_normal={n_normal} n_abnormal={abn_batch['i3d'].shape[0]} "
                f"i3d_shape={tuple(i3d.shape)} mask_shape={tuple(mask.shape)}",
                file=sys.stderr, flush=True,
            )
            assert n_normal == abn_batch["i3d"].shape[0], \
                f"nor/abn mismatch: {n_normal} vs {abn_batch['i3d'].shape[0]}"
            assert i3d.shape[0] == n_normal * 2, \
                f"concat shape bug: {i3d.shape[0]} != 2 * {n_normal}"

        scores = model(i3d=i3d, mask=mask)     # [2*B*5, T]
        loss = mil_ranking_loss(
            scores, mask, n_normal=n_normal,
            k=int(train_cfg["k_topk"]),
            margin=float(train_cfg["margin"]),
            lam_sparse=float(train_cfg["lam_sparse"]),
            lam_smooth=float(train_cfg["lam_smooth"]),
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    return float(sum(losses) / max(len(losses), 1))


@torch.no_grad()
def validate_i3d(model, val_loader, device, train_cfg) -> float:
    model.eval()
    losses = []
    for batch in val_loader:
        # Val batch has labels mixed; split paired halves like _split_labels for UCF
        labels = batch["label"]
        nor_mask = (labels == 0).nonzero(as_tuple=True)[0]
        abn_mask = (labels == 1).nonzero(as_tuple=True)[0]
        if len(nor_mask) == 0 or len(abn_mask) == 0:
            continue
        n = min(len(nor_mask), len(abn_mask))
        nor_mask = nor_mask[:n]
        abn_mask = abn_mask[:n]
        i3d = torch.cat([batch["i3d"][nor_mask], batch["i3d"][abn_mask]], dim=0).to(device)
        mask = torch.cat([batch["mask"][nor_mask], batch["mask"][abn_mask]], dim=0).to(device)
        scores = model(i3d=i3d, mask=mask)
        loss = mil_ranking_loss(
            scores, mask, n_normal=n,
            k=int(train_cfg["k_topk"]),
            margin=float(train_cfg["margin"]),
            lam_sparse=float(train_cfg["lam_sparse"]),
            lam_smooth=float(train_cfg["lam_smooth"]),
        )
        losses.append(loss.item())
    return float(sum(losses) / max(len(losses), 1)) if losses else float("inf")
```

### Example 3: The audit-epoch tracker

The `_audit_epoch` key in `train_cfg` is not pre-set. Recommend the main() loop increment it:

```python
# In main() dispatch branch, for xd_i3d path:
for epoch in range(int(cfg["train"]["epochs"])):
    cfg["train"]["_audit_epoch"] = epoch   # D-12 diagnostic: first 3 epochs audit
    train_loss = train_one_epoch_i3d(...)
    ...
```

Or simpler: pass `epoch` as a kwarg to `train_one_epoch_i3d(epoch=epoch)` and let the function check `if epoch < 3:`. Either works.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MGFN 80.11% as I3D-RGB anchor in D-11 | MGFN 79.19% as I3D-RGB anchor; 80.11% flagged as VideoSwin | This research session (2026-04-16) | Aligns the fallback anchor with the published I3D result; 80.11 is NOT reachable with the on-disk 1024-d cache |
| Wu annotation URL from `roseyu.com/XD-Violence/` | Wu annotation URL from `roc-ng.github.io/XD-Violence/images/annotations.txt` | This research session (2026-04-16) | `roseyu.com/XD-Violence/` now 404s; GitHub Pages (`roc-ng.github.io/XD-Violence/`) is the active canonical URL |
| "Any xd_i3d invocation produces all-zero labels" stub at `evaluate.py:180-192` | Full Wu annotation-driven label construction | Phase 4b delivers | Unblocks EVAL-01; enables real AP measurement against the 76.81% gate |

**Deprecated/outdated:**
- Phase 4 D-36 claim "train.py + evaluate.py dispatch via cfg['dataset'] == 'xd_i3d' → I3DFeatureDataset" — FALSIFIED by 04-06-UAT.md Rule 4 diagnosis. Phase 4b remediation (this phase) implements the actual dispatch.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MGFN I3D-RGB AP = 79.19% (not 80.11%, which is VideoSwin) | RTFM/MGFN Anchor Verification | Low — D-11 wording remains conservative either way; if 79.19% is slightly off, the planner should still document "79–80% band" rather than a point anchor. The primary gate (77.81 ± 1%) is unaffected. |
| A2 | RTFM's published 77.81% is specifically 10-crop I3D-RGB on XD | Primary anchor | Medium — if RTFM's XD result is actually RGB+Flow concat (2048-d), our 1024-d RGB-only MVP may underperform by ~1-2pp structural, pushing the gate into D-11 cascade territory. The config comment at rtfm_i3d.yaml:48-50 already flags this uncertainty and mitigates via D-11 Step 2 (RGB+Flow fallback). |
| A3 | Interval endpoints exceeding `N*16` by 1-15 frames is because I3D extractor dropped final remainder | Pitfall 3 | Low — the clamp-to-n_frames pattern is correct regardless of root cause; the pattern is what ucf_annotations.py already uses at line 89-90. |

**Claims tagged ASSUMED:** 3 assumptions, all LOW-to-MEDIUM risk. None block Phase 4b execution; the D-11 fallback cascade absorbs A1 + A2 risks.

## Open Questions

1. **Does the `I3DFeatureDataset` val mode split have enough abnormal videos?**
   - What we know: `data/splits/xd_val.txt` has 594 videos. Val set created by same stratified 15% split as train. Train is 52% normal (1741/3360), so val should be ~53% normal (~316/594) and ~278 abnormal.
   - What's unclear: After Pitfall 4 filtering (missing I3D crops), how many abnormal videos remain in val? Current filter only runs on construction — if val set loses all abnormal, `validate_i3d` returns `float('inf')` every epoch, breaking early stopping.
   - Recommendation: Add a preflight assertion in `build_dataloaders_i3d` that `len([v for v in val_ds.video_ids if not v.endswith('_label_A')]) >= 1`. The existing `[i3d_dataset] WARNING` in `I3DFeatureDataset.__init__` (src/data/i3d_dataset.py:74-90) already fires on collapsed ratio; make this a hard assertion in build_dataloaders_i3d.

2. **Where does `I3DFeatureDataset` read the xd_val.txt split — is it the same file used for fusion?**
   - What we know: fusion path uses `f"{paths['splits_dir']}/{dataset}_val.txt"` (`src/data/loaders.py:115`). For xd_i3d, we must use `f"{paths['splits_dir']}/xd_val.txt"` (hardcoded — since `cfg['dataset'] == 'xd_i3d'` but the XD val split file is named `xd_val.txt`, not `xd_i3d_val.txt`).
   - What's unclear: None — this is a deterministic mapping. But the planner must NOT pattern-match `{dataset}_val.txt` for xd_i3d (would resolve to non-existent `xd_i3d_val.txt`).
   - Recommendation: Explicitly code `f"{paths['splits_dir']}/xd_val.txt"` in `build_dataloaders_i3d`. Unit test asserts this file resolution works with synthetic fixture + real split file.

3. **Does `scripts/run_ablations.py` correctly skip the smoke run result?**
   - What we know: Smoke test writes to `results/smoke_xd_i3d_rtfm_i3d_s42/`. The gate queue writes to `results/xd_i3d_rtfm_i3d_s42/`. Different directories.
   - What's unclear: None — the smoke test uses a different `--run-name` override. No cleanup interference.
   - Recommendation: Planner task sequence: (1) rm -rf `results/smoke_xd_i3d_rtfm_i3d_s42/` + `results/xd_i3d_rtfm_i3d_s42/` (idempotent), (2) smoke run, (3) rm -rf `results/smoke_xd_i3d_rtfm_i3d_s42/`, (4) full gate run.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 (`vcc-main`) | Training + evaluation | ✓ | 3.11 | — |
| PyTorch 2.6.0 + cu124 | Training + evaluation | ✓ | verified via test_reproducibility.py passing | — |
| scikit-learn | frame-level AUC/AP | ✓ | Phase 4 EVAL paths use this daily | — |
| pytest 9.0.2 | Unit tests (D-17) | ✓ | verified via `pytest --version` in vcc-main | — |
| Wu annotations.txt | xd_temporal.txt commit (D-07) | ✓ | 500 lines, ~6.2 KB from https://roc-ng.github.io/XD-Violence/images/annotations.txt | — |
| XDVioDet gt.npy (reference) | Bit-identical validation (research only) | ✓ | 2,330,384 frames, 0.2308 positive fraction from https://raw.githubusercontent.com/Roc-Ng/XDVioDet/master/list/gt.npy | N/A — research only |
| I3D feature cache RGB | Training (3225 videos × 5 crops) | ✓ | E:/i3d-features/i3d-features/RGB = 16124 files | — |
| I3D feature cache RGBTest | Evaluation (800 videos × 5 crops) | ✓ | E:/i3d-features/i3d-features/RGBTest = 4000 files, 100% xd_test coverage | — |
| I3D feature cache Flow, FlowTest | D-11 Step 2 fallback only | ✓ (not probed) | Existence confirmed from `E:/i3d-features/i3d-features/` ls | — |
| XD skeleton features E:/features/xd/skeleton | NOT Phase 4b | ✓ 3 files (blocked, Phase 4c) | N/A | Phase 4c waits on this |
| XD CLIP features E:/features/xd/clip | NOT Phase 4b | ✓ 3 files (blocked, Phase 4c) | N/A | Phase 4c waits on this |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

> `nyquist_validation: true` in `.planning/config.json` — section included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `tests/conftest.py` (fixtures) + no pytest.ini (pyproject.toml defaults; project uses default collection) |
| Quick run command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_loaders_i3d.py tests/test_train_i3d.py tests/test_xd_annotations.py tests/test_evaluate_xd_i3d.py -x -v` |
| Full suite command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x -v --ignore=tests/test_ctrgcn_smoke.py` (the conditional skip in conftest.py auto-excludes vcc-ctrgcn-only tests) |
| Smoke/empirical command | `python src/train.py --config configs/rtfm_i3d.yaml --epochs 1 --run-name smoke_xd_i3d_rtfm_i3d_s42` |
| Full gate command | `python scripts/run_ablations.py --queue rtfm_gate --no-preflight` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-01 | build_dataloaders_i3d returns correct tuple | unit | `pytest tests/test_loaders_i3d.py::test_build_dataloaders_i3d_shape -x` | ❌ Wave 0 |
| EVAL-01 | collate_i3d_train flattens [B,5,T,1024]→[B*5,T,1024] | unit | `pytest tests/test_loaders_i3d.py::test_collate_i3d_train_flatten -x` | ❌ Wave 0 |
| EVAL-01 | collate_i3d_train replicates label 5x per video | unit | `pytest tests/test_loaders_i3d.py::test_collate_i3d_train_label_replication -x` | ❌ Wave 0 |
| EVAL-01 | collate_i3d_train emits all-ones mask | unit | `pytest tests/test_loaders_i3d.py::test_collate_i3d_train_mask_all_ones -x` | ❌ Wave 0 |
| EVAL-01 | nor_idx/abn_idx partitioning | unit | `pytest tests/test_loaders_i3d.py::test_nor_abn_partitioning -x` | ❌ Wave 0 |
| EVAL-01 | train_one_epoch_i3d returns finite loss on mock | unit | `pytest tests/test_train_i3d.py::test_train_one_epoch_i3d_finite_loss -x` | ❌ Wave 0 |
| EVAL-01 | validate_i3d returns finite loss on mock with both labels | unit | `pytest tests/test_train_i3d.py::test_validate_i3d_finite_loss -x` | ❌ Wave 0 |
| EVAL-01 | validate_i3d returns inf when val has only one class | unit | `pytest tests/test_train_i3d.py::test_validate_i3d_single_class -x` | ❌ Wave 0 |
| EVAL-01 | parse_xd_annotations strips .mp4 suffix | unit | `pytest tests/test_xd_annotations.py::test_parse_strips_mp4 -x` | ❌ Wave 0 |
| EVAL-01 | parse_xd_annotations preserves v= prefix | unit | `pytest tests/test_xd_annotations.py::test_parse_preserves_v_prefix -x` | ❌ Wave 0 |
| EVAL-01 | parse_xd_annotations handles multi-interval | unit | `pytest tests/test_xd_annotations.py::test_parse_multi_interval -x` | ❌ Wave 0 |
| EVAL-01 | parse_xd_annotations raises on odd endpoints | unit | `pytest tests/test_xd_annotations.py::test_parse_raises_odd_intervals -x` | ❌ Wave 0 |
| EVAL-01 | xd_frame_labels produces correct binary vector | unit | `pytest tests/test_xd_annotations.py::test_frame_labels_union -x` | ❌ Wave 0 |
| EVAL-01 | xd_frame_labels clamps endpoint to n_frames | unit | `pytest tests/test_xd_annotations.py::test_frame_labels_clamp -x` | ❌ Wave 0 |
| EVAL-01 | _build_frame_arrays xd_i3d builds real labels (not zeros) for abnormal | unit | `pytest tests/test_evaluate_xd_i3d.py::test_build_frame_arrays_abnormal -x` | ❌ Wave 0 |
| EVAL-01 | _build_frame_arrays xd_i3d defaults to zero labels for missing anno | unit | `pytest tests/test_evaluate_xd_i3d.py::test_build_frame_arrays_normal_missing_anno -x` | ❌ Wave 0 |
| EVAL-01 | _build_frame_arrays xd_i3d trips C4 assertion on length mismatch | unit | `pytest tests/test_evaluate_xd_i3d.py::test_c4_mismatch_raises -x` | ❌ Wave 0 |
| EVAL-01 | 1-epoch smoke test runs end-to-end | empirical | `python src/train.py --config configs/rtfm_i3d.yaml --epochs 1 --run-name smoke_xd_i3d_rtfm_i3d_s42` | N/A (runtime) |
| EVAL-01 | rtfm_gate queue AP >= 0.7681 | empirical | `python scripts/run_ablations.py --queue rtfm_gate --no-preflight` then parse results-index.csv | N/A (runtime gate) |
| EVAL-01 | D-12 bit-identical rerun | empirical (human-UAT) | Run rtfm_gate twice, compare 9 numeric keys in eval_metrics.json | N/A (runtime) |
| EVAL-01 | D-12 C4 sanity: snippet_auc vs auc delta < 2pp | empirical (auto) | Parse eval_metrics.json, assert abs(snippet_auc - auc) < 0.02 | N/A (runtime) |
| EVAL-01 | D-12 bag-size audit log | empirical (auto) | grep stderr for `[i3d_audit] n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024)` on first 3 epochs | N/A (runtime) |

### Sampling Rate

- **Per task commit:** `pytest tests/test_loaders_i3d.py tests/test_train_i3d.py tests/test_xd_annotations.py tests/test_evaluate_xd_i3d.py -x` (quick: the 4 Phase 4b test files only; ~10 seconds)
- **Per wave merge:** `pytest tests/ -x --ignore=tests/test_ctrgcn_smoke.py` (full suite except vcc-ctrgcn-only; ~60 seconds)
- **Phase gate:** Full suite green + 1-epoch smoke passes + rtfm_gate queue AP ≥ 0.7681 + D-12 all three diagnostics pass before `/gsd-verify-work`

### Wave 0 Gaps

All test files are NEW. Wave 0 creates:
- [ ] `tests/test_loaders_i3d.py` — 5 tests covering `build_dataloaders_i3d` + `collate_i3d_train` (EVAL-01)
- [ ] `tests/test_train_i3d.py` — 3 tests covering `train_one_epoch_i3d` + `validate_i3d` (EVAL-01)
- [ ] `tests/test_xd_annotations.py` — 6 tests covering `parse_xd_annotations` + `xd_frame_labels` (EVAL-01)
- [ ] `tests/test_evaluate_xd_i3d.py` — 3 tests covering the rewritten `_build_frame_arrays` xd_i3d branch (EVAL-01)
- [ ] `tests/conftest.py` — ADD `xd_temporal_path` fixture mirroring `ucf_temporal_path` fixture pattern (skipif path absent); ADD small synthetic Wu-annotations fixture for `test_xd_annotations.py`. The `synthetic_i3d_features` fixture already exists at line 121.

**No framework install required:** `vcc-main` already has pytest 9.0.2.

### Validation failure modes Phase 4b explicitly guards against

1. **Shape drift:** `collate_i3d_train` assertion + unit test on `[B*5, T, 1024]` output shape (Pitfall 4 adjacent).
2. **Label replication drift:** unit test that labels[0..4] == labels[5..9] ≠ labels[10..14] on a mixed-class batch (Pitfall 4 above).
3. **Mask-missing:** unit test that batch['mask'] is present and all-ones (Pitfall 1 above).
4. **Wu .mp4 suffix:** unit test both `vid.mp4` and `vid` inputs normalize to same key (Wu Annotation Format §ID normalization).
5. **v= prefix:** unit test that `v=YouTubeID` is preserved through parser (no strip).
6. **Odd-endpoint intervals:** unit test that `parse_xd_annotations` raises on malformed input.
7. **Interval overshoot:** unit test that `xd_frame_labels` clamps to n_frames without IndexError (Pitfall 3 above).
8. **Normal-video missing-annotation:** unit test that `_build_frame_arrays` returns all-zero labels + category="Normal" when vid not in annos (Pitfall 2 above).
9. **C4 length mismatch:** unit test that synthesizing a score vector of wrong length raises AssertionError via compute_frame_metrics.
10. **Bit-identical rerun:** empirical HUMAN-UAT check — run the gate twice, compare 9 numeric keys in eval_metrics.json (D-12 Check 1).
11. **snippet_auc vs auc delta:** empirical auto-check in SUMMARY — abs(snippet_auc - auc) must be < 0.02 (D-12 Check 2).
12. **Bag-size audit:** empirical stderr-log check in SUMMARY — `[i3d_audit]` lines present on first 3 epochs and shapes correct (D-12 Check 3).
13. **`results/xd_i3d_rtfm_i3d_s42/` stale state:** planner cleanup task before each run invocation (Pitfall 5 above).

## Security Domain

> `security_enforcement` not explicitly `false` → section included.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Research codebase; no network service; wandb disabled |
| V3 Session Management | no | Offline batch training; no sessions |
| V4 Access Control | no | Single-user thesis codebase |
| V5 Input Validation | yes | `parse_xd_annotations` validates "6-column" → actually "odd-pair" interval count; raises ValueError on malformed. `I3DFeatureDataset` uses `np.load(allow_pickle=False)` to refuse pickle deserialization (T-04-03-01 inherited from Phase 4). |
| V6 Cryptography | no | No crypto; SHA256 used only for `checkpoint_sha` / `config_hash` as integrity signature |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Pickle deserialization via `np.load(..., allow_pickle=True)` | Elevation of Privilege (T-04-03-01) | `allow_pickle=False` enforced in `i3d_dataset.py:109` — **must inherit** in any new `np.load` calls introduced by Phase 4b (none expected, parser uses `open().read()` not `np.load`) |
| Arbitrary path traversal via `paths.i3d_features` | Tampering | `configs/rtfm_i3d.yaml` pins the absolute path `E:/i3d-features/i3d-features`; `build_dataloaders_i3d` only concatenates `xd_train.txt` / `xd_val.txt` + `/RGB` suffix; no user-controlled string. |
| C3 test-set leakage into training | Information Disclosure | `src/eval/test_loader.py` guard preserved by parallel-functions dispatch (D-04); the i3d training path does NOT import from `src/eval/` |
| XSS / CSRF / SSRF | — (not applicable) | No web interface |
| Injection into subprocess cmdline | Elevation of Privilege | `scripts/run_ablations.py` assembles commands with `sys.executable` + fixed argument list; no user-controlled strings fed into `subprocess.run` |

**Phase 4b security posture:** inherits Phase 4's posture; no new threat surface. Wu annotation file is a plain-text commit under `data/annotations/` — same trust boundary as `ucf_temporal.txt`. The annotation file will be fetched once from `https://roc-ng.github.io/XD-Violence/images/annotations.txt` during the planning/execution phase, its SHA256 recorded in the commit message for provenance, then committed.

**Recommended provenance step for the planner:** before committing `data/annotations/xd_temporal.txt`, compute its SHA256 and include in the commit message body so future rebuilds can verify the same file was used.

## Sources

### Primary (HIGH confidence)

- **Wu 2020 XD-Violence annotations.txt** (via project page GitHub Pages): `https://roc-ng.github.io/XD-Violence/images/annotations.txt` — 500 non-blank lines, verified format `video_id[.mp4] s1 e1 [s2 e2 ...]`
- **XDVioDet gt.npy** (ECCV 2020 reference): `https://raw.githubusercontent.com/Roc-Ng/XDVioDet/master/list/gt.npy` — 2,330,384 frame float32 array, 0.2308 positive fraction
- **XDVioDet test.py** stride=16 reference: `https://github.com/Roc-Ng/XDVioDet/blob/master/test.py` — `np.repeat(pred, 16)` confirmed
- **XDVioDet option.py** gt.npy default: `--gt default='list/gt.npy'` (via WebFetch)
- **RTFM model.py** (ICCV 2021): `https://github.com/tianyu0207/RTFM/blob/main/model.py` — `k_abn = k_nor = num_segments // 10` = 3 when T=32
- **RTFM option.py**: `batch-size=32, lr=[0.001]*15000, max-epoch=15000, modality=RGB`
- **MGFN paper abstract + AAAI reference**: MGFN I3D-RGB outperforms RTFM by 1.38% AP on XD-Violence → 79.19% (confirmed via Liner + emergentmind reviews)
- **Existing codebase (verified this session):** src/data/i3d_dataset.py, src/data/loaders.py, src/train.py, src/evaluate.py, src/eval/ucf_annotations.py, src/eval/snippet_to_frame.py, src/eval/metrics.py, src/eval/test_loader.py, src/losses/mil_loss.py, src/models/rtfm_i3d.py, configs/rtfm_i3d.yaml, scripts/run_ablations.py, tests/conftest.py, tests/fixtures/synthetic_eval.py
- **Phase 4 docs:** 04-CONTEXT.md, 04-06-UAT.md, 04-07-SUMMARY.md (Option B decision), 04-RESEARCH.md (Component 7 + §Architecture pattern references)
- **Project docs:** CLAUDE.md (RTX 4090, deterministic, sklearn, single-GPU), REQUIREMENTS.md (EVAL-01 scope), ROADMAP.md (Phase 4b scope narrowing per D-01)

### Secondary (MEDIUM confidence)

- **RTFM published 77.81% AP** (via multiple paper review sources): matches abstract claim; primary confidence reduced because we didn't inspect the paper's exact Table X row for XD-I3D-RGB 10-crop vs other crop configurations
- **MGFN 79.19% I3D-RGB** (derived: 77.81 + 1.38): derived from "1.38% AP over RTFM" synthesis rather than direct table citation; the 80.11% VideoSwin figure IS cited directly

### Tertiary (LOW confidence)

- None — all critical decisions were verifiable via primary sources or direct codebase inspection.

## Metadata

**Confidence breakdown:**

- **Standard stack:** HIGH — all dependencies already in `vcc-main`, verified via file reads and live pytest probe
- **Architecture:** HIGH — D-04/D-05 patterns are direct mirrors of existing Phase 4 structure; no novel architectural decisions needed
- **Wu annotation format:** HIGH — downloaded file verified bit-identical coverage against XDVioDet gt.npy and our xd_test.txt split
- **I3D stride:** HIGH — bit-identical match (2,330,384 frames) between on-disk cache × 16 stride and XDVioDet reference
- **Pitfalls:** HIGH — 7 pitfalls identified with both root cause and prevention; 5 have corresponding unit tests proposed
- **RTFM anchor (77.81%):** MEDIUM — paper claim is widely cited; exact XD-I3D-RGB table row not pulled from PDF
- **MGFN anchor correction (79.19% not 80.11% for I3D-RGB):** MEDIUM — derived from secondary paper-review sources; one more verification step (paper PDF Table 2) would elevate to HIGH

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (30 days — stable stack, XD-Violence data URLs and reference implementations are stable academic artifacts)

## RESEARCH COMPLETE
