<!-- refreshed: 2026-06-09 -->
# Architecture

**Analysis Date:** 2026-06-09

## System Overview

ViolenceCC is an **offline feature-cache pipeline**: heavyweight backbones (RTMPose, CTR-GCN, CLIP/SigLIP2, I3D) run once in separate conda environments and write per-video `.npy` feature caches to disk. The lightweight fusion-head training/eval/TTA layers (`src/`) then operate entirely on those caches in the `vcc-main` environment. No backbone is in the training graph.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                 OFFLINE EXTRACTION (separate conda envs)                  │
├──────────────────────────┬────────────────────────┬──────────────────────┤
│  Skeleton branch          │  Visual branch          │  I3D branch (XD)     │
│  RTMPose → CTR-GCN 4-strm │  CLIP / SigLIP2 1-FPS   │  precomputed RGB     │
│  `scripts/extract_        │  `scripts/extract_      │  features (external) │
│   skeletons.py` →         │   clip.py`              │                      │
│  `scripts/extract_        │  mean+max pool          │                      │
│   ctrgcn.py`              │                         │                      │
│  → [N,256] .npy           │  → [N,1024/1536/3072]   │  → [N,1024] .npy     │
└──────────┬────────────────┴───────────┬─────────────┴──────────┬──────────┘
           │ E:/features/{ds}/skeleton   │ E:/features/{ds}/clip   │ RGB/RGBTest
           ▼                             ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│        DATA LAYER  `src/data/`  (load caches → paired MIL bags)           │
│  MILFeatureDataset `src/data/dataset.py` / I3DFeatureDataset              │
│  build_dataloaders / build_dataloaders_i3d `src/data/loaders.py`          │
└──────────────────────────────────┬────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│   MODEL LAYER  `src/models/`  (registry → variant → shared MILHead)       │
│  build_model() `src/models/registry.py`                                   │
│  skeleton_only | clip_only | late_fusion | gated_fusion | rtfm_i3d        │
│  → per-snippet sigmoid scores [B, T]                                      │
└──────────────────────────────────┬────────────────────────────────────────┘
              ┌─────────────────────┴─────────────────────┐
              ▼ (train)                                    ▼ (eval / tta)
┌──────────────────────────────┐      ┌────────────────────────────────────┐
│ LOSS  `src/losses/mil_loss.py`│      │ EVAL  `src/eval/`  +  TTA `src/tta/`│
│ top-k MIL ranking hinge +     │      │ snippet→frame broadcast → sklearn   │
│ sparsity + smoothness         │      │ AUC/AP; TTA adapts LN affine params │
└──────────────────────────────┘      └────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Training entry point | YAML-config driven train loop, CLI overrides, dual-path dispatch | `src/train.py` |
| Eval entry point | Load `best_model.pth` + snapshot, snippet→frame, write metrics | `src/evaluate.py` |
| TTA entry point | Per-config TTA run: load source model, adapt, frame-level AUC | `src/tta/evaluate_tta.py` |
| Ablation orchestrator | Subprocess loop over (variant, seed, dataset) queues; resume via `.done` | `scripts/run_ablations.py` |
| Model registry | `variant` string → wrapper class via lazy factory | `src/models/registry.py` |
| Shared MIL head | 3-layer MLP `D→128→32→1`+Sigmoid, reused by all variants | `src/models/mil_head.py` |
| MIL loss | top-k ranking hinge + sparsity + smoothness | `src/losses/mil_loss.py` |
| Feature dataset | Per-video `.npy` cache → paired MIL bags | `src/data/dataset.py` |
| DataLoader builder | Independent paired nor/abn loaders + val loader | `src/data/loaders.py` |
| Snippet→frame | Broadcast per-snippet scores to frame grid (C4 guard) | `src/eval/snippet_to_frame.py` |
| Frame metrics | sklearn AUC/AP with length assertions, per-category | `src/eval/metrics.py` |
| TTA adaptors | TENT / SAR / SAM / disc_reweight on LayerNorm affine | `src/tta/{tent,sar,sam,disc_reweight}.py` |

## Pattern Overview

**Overall:** Cache-first feature pipeline + registry-dispatched variant models + YAML-config-driven entry points + subprocess-orchestrated ablation sweeps.

**Key Characteristics:**
- **Backbones are frozen and offline.** All learned parameters live in tiny fusion heads (`src/models/`); the 24GB RTX 4090 constraint rules out end-to-end backbone training, so features are cached to `E:/features/`.
- **Variant-uniform forward signature.** Every model's `forward(self, skel=None, clip=None, mask=None)` (RTFMI3D adds `i3d=None`) takes the same keyword set and returns `[B, T]` sigmoid scores, so ablations isolate fusion effects with a byte-identical shared `MILHead`.
- **Reproducibility-first.** `CUBLAS_WORKSPACE_CONFIG` is set before `import torch` (lines 1-2 of every entry point), seeds are fixed via `src/utils/seed.set_deterministic`, and every run writes a full `config_snapshot.json` (git SHA + pip freeze + resolved cfg).
- **Loud-failure invariants.** Length-drift assertions (`snippet_to_frame`, `metrics`), alignment asserts (`dataset.__getitem__`), and an import tripwire (`test_loader.py`) convert silent metric corruption into immediate exceptions.

## Layers

**Data layer (`src/data/`):**
- Purpose: turn per-video `.npy` caches into paired MIL bags
- Location: `src/data/dataset.py`, `src/data/i3d_dataset.py`, `src/data/loaders.py`
- Contains: `MILFeatureDataset` (skel+clip), `I3DFeatureDataset` (5-crop XD path), loader builders, collate functions
- Depends on: cached `.npy` features under `E:/features/`, split files under `data/splits/`
- Used by: `src/train.py` (train/val), `src/eval/test_loader.py` (test)

**Model layer (`src/models/`):**
- Purpose: 5 MIL-head variants, all producing `[B, T]` snippet scores
- Location: `src/models/registry.py` + 5 wrapper files + `mil_head.py`
- Contains: `SkeletonProj`, `CLIPProj`, `LateFusion`, `GatedFusion`, `RTFMI3D`, shared `MILHead`
- Depends on: nothing in `src/` except `mil_head.py`
- Used by: `src/train.py`, `src/evaluate.py`, `src/tta/evaluate_tta.py` via `build_model(**cfg["model"])`

**Loss layer (`src/losses/`):**
- Purpose: top-k MIL ranking loss with regularizers
- Location: `src/losses/mil_loss.py`
- Used by: all training paths (`train_one_epoch`, `train_one_epoch_i3d`, `validate`)

**Eval layer (`src/eval/`):**
- Purpose: snippet→frame broadcast + annotation parsing + sklearn frame metrics
- Location: `src/eval/{snippet_to_frame,metrics,ucf_annotations,xd_annotations,test_loader}.py`
- Depends on: annotation files under `data/annotations/`, external boundary JSONs
- Used by: `src/evaluate.py`, `src/tta/evaluate_tta.py`

**TTA layer (`src/tta/`):**
- Purpose: test-time adaptation of LayerNorm affine params under corruption shift
- Location: `src/tta/{tent,sar,sam,disc_reweight,evaluate_tta}.py`
- Depends on: `src/models/`, `src/eval/`, source run dirs in `results/`
- Used by: `scripts/run_ablations.py` TTA queues, `scripts/run_tta_grid.py`

## Data Flow

### Primary Training Path (`src/train.py`)

1. Parse `--config` YAML, apply CLI overrides (`parse_args` / `apply_cli_overrides`, `src/train.py:34-64`)
2. `set_deterministic(seed)` then create run dir + `snapshot_config` (`src/train.py:288-299`)
3. `build_model(**cfg["model"])` → variant instance (`src/train.py:306`, dispatches via `src/models/registry.py:44`)
4. **Dispatch once** on `cfg["dataset"]`: `xd_i3d` → `build_dataloaders_i3d` + i3d train/val fns; else → `build_dataloaders` + skel+clip fns (`src/train.py:313-321`)
5. Per epoch: concat paired nor+abn batches → `model(skel=, clip=, mask=)` → `mil_ranking_loss` → backward (`src/train.py:119-147`)
6. `validate()` computes val MIL loss on `shuffle=True` val loader (`src/train.py:224-246`)
7. `EarlyStopping` + atomic `save_checkpoint_atomic` of `best_model.pth` / `last_model.pth` (`src/train.py:359-368`)

### Evaluation Path (`src/evaluate.py`)

1. Load `config_snapshot.json` + `best_model.pth` from `--run-dir` (`src/evaluate.py:82-89`); never `last_model.pth` (D-10)
2. `build_test_dataset` returns all snippets in temporal order (test mode, no sampling)
3. Per-video snippet scores → `snippet_to_frame(scores, n_frames, snippet_window, upsample_factor)` (`src/eval/snippet_to_frame.py:21`)
4. `compute_frame_metrics` concatenates with C4 length asserts → sklearn `roc_auc_score` / `average_precision_score` (`src/eval/metrics.py:29`)
5. Atomic write of `eval_metrics.json`, `eval_scores.npz`, `per_category.csv`, then `.done` last

### TTA Path (`src/tta/evaluate_tta.py`)

1. Resolve `--source-run` + `--backbone` → feature prefix + source run dir (`BACKBONE_FEATURE_PREFIX` / `BACKBONE_SOURCE_RUNS`, `src/tta/evaluate_tta.py:64-77`)
2. Load source `GatedFusion`; `configure_model` puts it in train mode, freezes all but LN affine, disables ALL dropout (`src/tta/tent.py:38-58`)
3. Load corrupted CLIP features (severity) + clean skeleton features for noise/brightness corruptions
4. Adapt per `--method`: `source_only` | `tent` | `sar` | `disc_reweight`, under `--protocol` `episodic` (per-video reset) or `continual` (one stream reset)
5. `disc_reweight` is two-pass transductive: accumulate source/test covariance, compute label-free scalar `w`, scale the CLIP stream after `ln_clip` (`src/tta/disc_reweight.py`)
6. Frame-level AUC via same `snippet_to_frame` + `compute_frame_metrics` as eval

**State Management:**
- All run state is on-disk per run dir: `config_snapshot.json`, `best_model.pth`, `last_model.pth`, `train_log.csv`, `eval_metrics.json`, `.done`.
- TTA episodic reset restores `deepcopy(model.state_dict())` between videos; continual protocol resets once for the whole stream.

## Key Abstractions

**Model variant wrapper:**
- Purpose: uniform `forward(skel, clip, mask)` → `[B, T]` sigmoid scores so ablations isolate fusion choice
- Examples: `src/models/skeleton_only.py`, `src/models/clip_only.py`, `src/models/late_fusion.py`, `src/models/gated_fusion.py`, `src/models/rtfm_i3d.py`
- Pattern: thin projection/fusion + shared `MILHead`; each exposes named `nn.LayerNorm` attributes (`ln_skel`, `ln_clip`, `ln_fused`, `ln_i3d`) so TTA can collect affine params

**MIL bag:**
- Purpose: a video → `[T, D]` snippet tensor + `[T]` mask; paired nor/abn bags form one ranking hinge
- Examples: `MILFeatureDataset.__getitem__` (`src/data/dataset.py:91-101`)
- Pattern: train/val sub-sample to `T=32` (sample-with-replacement when `N<T`); test returns all snippets

**RunSpec:**
- Purpose: one `(dataset, variant, seed, cache_variant)` tuple → deterministic run dir name
- Examples: `scripts/run_ablations.py:52-90`
- Pattern: `run_name` property emits `{dataset}_{variant}[_{cache_variant}]_s{seed}`

## Entry Points

**`src/train.py`** — `python src/train.py --config configs/<variant>.yaml --seed 42`; trains one variant, writes a run dir.

**`src/evaluate.py`** — `python src/evaluate.py --run-dir results/<run>/ --split test`; computes frame AUC/AP.

**`src/tta/evaluate_tta.py`** — one TTA config (corruption × severity × method); called as subprocess by the orchestrator.

**`scripts/run_ablations.py`** — `python scripts/run_ablations.py --queue <queue>`; orchestrates train/eval/TTA subprocess sweeps with resume.

## Architectural Constraints

- **Two-environment strategy:** Extraction (`vcc-skeleton`, `vcc-ctrgcn`) and training (`vcc-main`) are mutually incompatible (PyTorch 1.12 + mmcv-full 1.7 vs PyTorch 2.6). Extraction scripts are invoked via `conda run -n <env>`; `src/` never imports mmcv/rtmlib.
- **Feature caches are external:** Paths point at `E:/features/`, `E:/snippets/`, `E:/skeletons/` (machine-specific drive). Run dirs and split files are in-repo; multi-GB caches are not.
- **Threading:** Single-process training; DataLoader workers must use module-level `seed_worker` / `collate_i3d_train` (no lambdas/closures) for Windows `spawn` start method (`src/data/loaders.py:36-104`).
- **Global state:** `CUBLAS_WORKSPACE_CONFIG` env var set at import time; numpy global RNG drives segment sub-sampling in `MILFeatureDataset`.
- **Restricted import:** `src/eval/test_loader.py` raises `RuntimeError` at import unless called from `evaluate.py` or pytest (C3 test-leakage tripwire).

## Anti-Patterns

### `strict=False` checkpoint loading

**What happens:** `model.load_state_dict(..., strict=False)` silently accepts partial loads.
**Why it's wrong:** Produces misleading metrics from an architecture mismatch with no error.
**Do this instead:** Always `strict=True` (project convention); handle key remapping explicitly. See `src/utils/checkpoint.py`.

### Single-class MIL batch

**What happens:** A batch with only normal or only abnormal samples has no valid ranking pair.
**Why it's wrong:** The hinge loss is undefined; silently skewed loss values.
**Do this instead:** Val loaders use `shuffle=True`, and `_split_labels` / `validate` skip single-class batches (`src/train.py:99-116, 230-232`).

### Reaching into `src/eval/test_loader.py` from training

**What happens:** A training script or notebook imports the test-set loader.
**Why it's wrong:** Risks test-set leakage into model selection.
**Do this instead:** Only `src/evaluate.py` and pytest may import it; the module enforces this at import (`src/eval/test_loader.py:32`).

### Dropout left enabled during TTA

**What happens:** `model.train()` (needed for LN gradient flow) re-enables every `nn.Dropout`, making TTA scores stochastic.
**Why it's wrong:** Non-deterministic adaptation noise contaminated early TTA results.
**Do this instead:** `configure_model` loops all modules and `.eval()`s every Dropout after `train()` (`src/tta/tent.py:55-57`).

## Error Handling

**Strategy:** Fail loud at correctness boundaries; best-effort silence only for provenance metadata.

**Patterns:**
- Length-drift `AssertionError` (substring `C4 REGRESSION`) before any sklearn call (`src/eval/metrics.py:62-72`, `src/eval/snippet_to_frame.py:54`)
- Cache alignment assert `skel.shape[0] == clip.shape[0]` with `video_id` in the message (`src/data/dataset.py`)
- `git_sha` capture never raises (returns `"unknown"` if git unavailable, `src/utils/config.py:51`)
- Orchestrator logs failed subprocess exit codes to `runner-errors.log` and continues the queue

## Cross-Cutting Concerns

**Logging:** stdlib `logging` in scripts/eval; per-epoch `print` + `CSVLogger` (`train_log.csv`) + optional `WandbLogger` (default `mode: disabled`).
**Validation:** YAML loaded via `src/utils/config.load_config`; variant kwargs validated in each model `__init__`; dataset/mode enums validated in `MILFeatureDataset`.
**Reproducibility:** `set_deterministic` + `CUBLAS_WORKSPACE_CONFIG` + `config_hash`/`checkpoint_sha`/`git_sha` written into `eval_metrics.json` for bit-identical reruns (`src/utils/config.py`).

---

*Architecture analysis: 2026-06-09*
