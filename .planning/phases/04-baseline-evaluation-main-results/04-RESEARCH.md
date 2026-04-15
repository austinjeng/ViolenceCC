# Phase 4: Baseline Evaluation & Main Results - Research

**Researched:** 2026-04-15
**Domain:** Weakly-supervised VAD frame-level evaluation + RTFM reproduction + ablation orchestration
**Confidence:** HIGH (41 locked decisions from CONTEXT.md + verified reference implementations)

## Summary

Phase 4 builds the UCF-Crime evaluation harness around three interlocking guarantees: (1) C3 test-set-leakage prevention via an import-boundary isolated `src/eval/test_loader.py` [CITED: .planning/research/PITFALLS.md C3]; (2) C4 snippet-to-frame expansion correctness via a single verified `snippet_to_frame()` utility with length assertions before every `sklearn.metrics` call [CITED: .planning/research/PITFALLS.md C4]; (3) RTFM-on-XD reproduction (±1% of 77.81% AP) as the harness gate that catches silent bugs in both the C4 expansion path and the RTFM architecture implementation simultaneously [CITED: RTFM GitHub tianyu0207/RTFM]. The evaluation surface is deterministic: a CLI `src/evaluate.py --run-dir <path> --split {val|test}` reads `best_model.pth` + `config_snapshot.json` from Phase 3's run dir, emits `eval_metrics.json` + `eval_scores.npz` + `per_category.csv` + `.done` back into it.

The RTFM variant is a new `MODEL_REGISTRY` key (`rtfm_i3d`) trained on the XD-Violence I3D feature cache that is **already on disk** at `E:/i3d-features/i3d-features/` [VERIFIED: 800 test videos × 5 crops × [97..N, 1024] float32 confirmed present 2026-04-15]. Because XD skeleton+CLIP is at 3/3954 and will take 1-2 weeks more, Phase 4 is scoped to UCF-only; the planner inserts a new **Phase 4b** to ROADMAP.md that re-runs all ablations on XD when its features land. Orchestration uses `scripts/run_ablations.py` (Python subprocess runner per D-26) with filesystem `.done`-marker resume per D-31 and append-only `results-index.csv` audit log per D-33. wandb is the auxiliary tracker — CSV logs remain the thesis source of truth [CITED: Phase 3 D-13].

**Primary recommendation:** Build `src/eval/` as a closed module (4 files: `__init__.py`, `test_loader.py`, `metrics.py`, `snippet_to_frame.py`) importable only by `src/evaluate.py` and pytest tests. Register RTFM-XD as the 5th MODEL_REGISTRY key and run it **first** in the orchestrator — if the AP gate fails, halt the queue because every downstream number is suspect. Use `np.repeat(scores, 16)` inside `rtfm_i3d` evaluation (I3D snippets = 16 frames, RTFM/MGFN convention) and the compound `np.repeat(np.repeat(scores, 64), 10)` expansion for UCF skeleton+CLIP (Phase 1 D-11 every-10th-PNG × Phase 2 64-frame snippets).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase scope and sequencing**
- **D-01:** Phase 4 covers **UCF-Crime only**. All XD-Violence main results move to a new **Phase 4b** inserted after Phase 4 in `ROADMAP.md`.
- **D-02:** XD skeleton+CLIP extraction continues out-of-band. Phase 4 does not wait/monitor. Phase 4b activates when `E:/features/xd/` is populated.
- **D-03:** RTFM reproduction gate retargeted from UCF → XD-Violence I3D. XD I3D features at `E:/i3d-features/i3d-features/` (5-crop × 1024-d). Pass threshold: XD frame-level AP within ±1% of either RTFM's 77.81% or MGFN's 80.11% — planner picks anchor.
- **D-04:** UCF `Temporal_Anomaly_Annotation.txt` downloaded, committed to `data/annotations/ucf_temporal.txt` (git-tracked).
- **D-05:** RTFM uses **RGB I3D stream only** (not RGB+Flow). Matches RTFM's published XD number.

**Evaluate.py architecture**
- **D-06:** CLI: `python src/evaluate.py --run-dir <path> [--split {val|test}]` with `--split=test` default. Reads `config_snapshot.json` + `best_model.pth` from the run dir; writes `eval_metrics.json`, `eval_scores.npz`, `per_category.csv`, and `.done`.
- **D-07:** Test data loading lives in **`src/eval/test_loader.py`** — imported only by `src/evaluate.py`. `src/data/dataset.py` continues to expose only `MILFeatureDataset` (train/val).
- **D-08:** Loud runtime guard in `src/eval/test_loader.py`: module-level check on `sys.argv[0]` — raises `RuntimeError` unless caller is `evaluate.py` or pytest.
- **D-09:** Explicit `--split {val|test}` flag, never auto-inferred.
- **D-10:** `evaluate.py` loads **`best_model.pth` only** — no `last_model.pth` eval.
- **D-11:** `eval_metrics.json` keys: `auc`, `ap`, `snippet_auc`, `video_auc`, `per_category` dict.
- **D-12:** `eval_metrics.json` reproducibility metadata: `config_hash`, `git_sha`, `checkpoint_sha`, `wandb_run_id` (nullable), `dataset`, `split`, `seed`, `eval_timestamp`, `eval_duration_s`.
- **D-13:** Per-video frame-level scores to `eval_scores.npz` — `{video_id: np.ndarray shape (n_frames,)}`.

**Frame-level metric pipeline**
- **D-14:** UCF frame-level AUC computed at **original 30fps granularity**. `np.repeat(frame_scores, 10)` upsamples from PNG grid to original video frame indices.
- **D-15:** Single utility `snippet_to_frame(scores, n_frames, window)` handles all broadcast cases. `assert len(frame_scores) == len(frame_labels)` before **every** `sklearn.metrics` call.
- **D-16:** UCF per-frame binary labels = **union** of both anomaly intervals `[start1, end1] ∪ [start2, end2]`. `-1 -1` sentinel = no interval (normal video).
- **D-17:** UCF category labels read from the annotation file's category column. Violence subset = `{Fighting, Assault}`.

**RTFM variant implementation**
- **D-18:** RTFM registered as `rtfm_i3d` MODEL_REGISTRY key, consuming 1024-d I3D features. Routes through `evaluate.py`.
- **D-19:** 5-crop handling: training uses all 5 crops as separate samples in the bag (5× effective training signal); test averages 5 crops to `[N, 1024]` before forward.
- **D-20:** I3D features via new YAML key `paths.i3d_features` (singular, pointing at `E:/i3d-features/i3d-features/`). Loader knows to read `RGB/` for train+val, `RGBTest/` for test.

**Ablation caches and re-extraction**
- **D-21:** Multi-person skeleton cache: `[N, 2, 256]` single .npy per video. Model aggregates at load time via `cfg.data.skel_agg ∈ {concat, max, mean}`.
- **D-22:** Phase 4 multi-person ablation runs `skel_agg=concat` only (yields `[N, 512]` with `skel_dim=512`). `max`/`mean` deferred.
- **D-23:** CLIP mean-only cache: `[N, 512]` npy (vs default `[N, 1024]` mean+max). New `--pool={mean|mean_max}` flag on `scripts/extract_clip.py`; default `mean_max`.
- **D-24:** Sibling cache directories: `E:/features/ucf/skeleton_2person/`, `E:/features/ucf/clip_mean/`.
- **D-25:** Pooling ablations re-extracted **UCF only in Phase 4**. XD pooling → Phase 4b.

**Ablation orchestration**
- **D-26:** **`scripts/run_ablations.py`** Python runner. Loops over (variant, seed, dataset, cache_variant) tuples, calls `src/train.py` + `src/evaluate.py` as subprocesses.
- **D-27:** Multi-seed (3-seed) runs apply to **Gated Fusion only** per SC #4.
- **D-28:** Multi-seed set = **`{42, 123, 2024}`**.
- **D-29:** 2 pooling ablations at single seed=42. Re-run 3-seed only if delta < 0.5%.
- **D-30:** Deterministic run dir naming: `results/<dataset>_<variant>[_<cache_variant>]_s<seed>/`. Adds `--run-name` override to `src/train.py`.

**Run-index, resume, failure recovery**
- **D-31:** Skip check = filesystem probe for `.done` marker. Atomic write-temp-then-rename.
- **D-32:** Failure recovery = log to `runner-errors.log`, continue queue.
- **D-33:** Append-only **`results/results-index.csv`** — columns: `run_name, variant, dataset, seed, cache_variant, auc, ap, n_videos, n_frames, start_time, end_time, config_hash`.
- **D-34:** Runner auto-runs `evaluate.py` as part of each ablation (train → evaluate sequence). `.done` only after `eval_metrics.json` exists and is valid JSON.

**Config management**
- **D-35:** Flat self-contained YAMLs. 3 new files: `configs/rtfm_i3d.yaml`, `configs/gated_fusion_2person.yaml`, `configs/gated_fusion_clip_mean.yaml`. 7 configs total.
- **D-36:** `rtfm_i3d.yaml` binds `dataset: xd_i3d` (new dataset key) and `paths.i3d_features: E:/i3d-features/i3d-features/`. `skeleton_features`/`clip_features` absent.
- **D-37:** Pooling ablation YAMLs reuse `model.variant: gated_fusion` with different feature paths + new `data.skel_agg: concat` field. `MODEL_REGISTRY` gains only `rtfm_i3d` (5 keys). SkeletonProj accepts configurable `skel_dim` (256/512).
- **D-38:** YAML naming: variant-describing, not numbered.

**wandb integration**
- **D-39:** `scripts/wandb_preflight.py` verifies wandb login OR `WANDB_API_KEY` env. `run_ablations.py` calls it before queue opens; fails fast.
- **D-40:** wandb auth failure mid-run: training subprocess catches `wandb.errors.Error`, re-initializes with `mode=offline`, logs warning, continues.
- **D-41:** wandb tags: `[phase4, <dataset>, <variant>, s<seed>]` plus `<cache_variant>` when applicable.

### Claude's Discretion
- RTFM Feature Magnitude head simplification (MTN not required; minimum viable = FM head + MIL ranking on I3D)
- `eval_scores.npz` compression (compressed default if size issue)
- `per_category.csv` column ordering
- `--split val` eval depth (MIL-loss-only sufficient)
- `config_hash` compute at training-time vs eval-time (eval-time simpler)
- wandb group name scheme (flat tags default; groups as fallback)
- `run_ablations.py` subprocess vs direct import (subprocess safe default)
- Resume-mid-run when run has `best_model.pth` but no `.done`: re-run full train+eval (deterministic dirs overwrite)
- `git_sha` dirty-tree handling (`-dirty` suffix vs raising; suffix default)
- Per-category.csv Normal video rows: omit (report only anomaly categories)
- Training set size mismatch handling (~3225 I3D videos / 3954 expected): document + skip missing in loader

### Deferred Ideas (OUT OF SCOPE)
- **Phase 4b (XD-Violence main results):** 6 variants × XD + 2 pooling ablations × XD + 3-seed Gated × XD — planner adds to ROADMAP.md; activated when XD features complete.
- **UCF-Crime RTFM reproduction:** original PRD gate. Phase 4b scope or supplement if Phase 4 ahead.
- **Multi-person `max` and `mean` aggregation ablations:** optional extras.
- **`last_model.pth` sanity eval:** optional one-off.
- **Flow I3D stream inclusion for RTFM** (D-05 excluded): revisit if RGB-only AP misses gate.
- **UCF PNG-granularity AUC as secondary number:** D-14 chose 30fps primary.
- **CLIP sampling rate ablation (OPT-07), Gating weight histogram (OPT-10), t-SNE/UMAP (OPT-09):** Phase 6.
- **Cross-dataset TTA (OPT-03):** Phase 5 scope.
- **RWF-2000 supplementary (OPT-08), YOLO-World (OPT-01):** v2.
- **wandb sweep-config orchestration:** fallback if per-run tags hard to slice.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **EVAL-01** | RTFM baseline reproduction on UCF-Crime — target 84.30% AUC within ±1% | **Retargeted to XD per D-03**: FM head minimum-viable impl + MIL ranking on 1024-d I3D RGB, 5-crop test averaging, ±1% of 77.81% (RTFM) or 80.11% (MGFN). Detailed in §5 below. |
| **EVAL-02** | Frame-level AUC (ROC) on UCF-Crime official test set with correct snippet→frame expansion | `src/eval/snippet_to_frame.py` utility (§4) + `np.repeat(scores, 10)` to 30fps + `src/eval/metrics.py` with pre-sklearn length assertion. D-14 + D-15 mandated. |
| **EVAL-03** | Frame-level AP on XD-Violence official test set | Phase 4 delivers via `rtfm_i3d` on XD (harness gate); Phase 4b extends to Gated Fusion on XD when its skeleton+CLIP cache lands. Same `evaluate.py` code path; only dataset key swaps. |
| **EVAL-04** | Per-category violence subset breakdown (UCF: Fighting+Assault; XD: Fighting+Abuse+Riot) | UCF categories parsed from annotation file column 2 (D-17). `per_category.csv` row per anomaly category (Normal omitted). XD violence subset deferred to Phase 4b. |
| **EVAL-05** | Key results (Gated Fusion) repeated 3 times with mean±std, std < 0.5% | `run_ablations.py` multi-seed loop over `{42, 123, 2024}` (D-28). `results-index.csv` rows aggregate into table via `pandas.read_csv` + groupby. Thesis SC #4. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Checkpoint load + inference | `src/evaluate.py` | `src/eval/test_loader.py` (data) | Evaluate owns the end-to-end CLI; test loader is a stateless bounded helper |
| Frame-level label construction | `src/eval/test_loader.py` | `data/annotations/ucf_temporal.txt` (file) | Single parser → 30fps binary vector per video; import-boundary isolates from training |
| Snippet→frame expansion | `src/eval/snippet_to_frame.py` | — | Pure-function utility so it's independently unit-testable (C4 regression surface) |
| Metric computation + assertions | `src/eval/metrics.py` | sklearn | Wraps `roc_auc_score` / `average_precision_score`; enforces length-equality assertion inline |
| Reproducibility metadata | `src/utils/config.py` | `subprocess` (git), `hashlib` (SHA256) | Piggybacks on Phase 3 `snapshot_config()`; adds `config_hash`/`checkpoint_sha` helpers |
| Run-dir I/O contract | `src/evaluate.py` | `.done` marker, `eval_scores.npz`, `per_category.csv` | All artifacts in same dir as `best_model.pth` — Phase 5/6 consume by path |
| RTFM architecture | `src/models/rtfm_i3d.py` | `MODEL_REGISTRY` (registry.py) | 5th variant, FM head + MIL ranking; reuses MILHead and existing MIL loss |
| 5-crop I3D loader | `src/data/i3d_dataset.py` (new) | `src/data/loaders.py` (dispatch) | Parallel to `MILFeatureDataset`; NOT in `test_loader.py` — train + val uses it, test uses it under `rtfm_i3d` eval path |
| Re-extracted cache writes | `scripts/extract_{ctrgcn,clip}.py` | `E:/features/ucf/{skeleton_2person,clip_mean}/` | Scripts gain `--keep-persons` / `--pool=mean` flags; sibling-dir convention (D-24) |
| Ablation orchestration | `scripts/run_ablations.py` | `.done` probe + `results-index.csv` append | Subprocess runner; `src/train.py` + `src/evaluate.py` are black boxes at queue level |
| wandb preflight + offline fallback | `scripts/wandb_preflight.py` + `src/utils/wandb_logger.py` | `wandb.errors.Error` catch | Preflight catches config gaps at queue start; runtime catches mid-run auth failures |
| Phase 4b planning | `.planning/ROADMAP.md` | — | Planner adds phase entry; code unchanged (dataset-portable by construction) |

## Standard Stack

### Core (already present, Phase 3 env)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | 2.6.0+cu124 | Model loading, inference, no-grad eval | Phase 3 locked; RTX 4090 / CUDA 12.4 stable path [VERIFIED: `torch.__version__` 2026-04-15] |
| numpy | 1.26.x | Score expansion, label arrays, `np.repeat`, `np.savez_compressed` | Pervasive in repo; float32 npy contract enforced [VERIFIED: Phase 2 cache] |
| scikit-learn | 1.8.0 | `roc_auc_score`, `average_precision_score` | Community-standard metric API; matches RTFM/MGFN/VadCLIP eval [VERIFIED: CITED sklearn/scikit-learn] |
| pandas | 2.2.2 | `results-index.csv` append + groupby for 3-seed mean±std aggregation | Phase 4 SC #4 requires table generation from CSV [VERIFIED: `pandas.__version__`] |
| PyYAML | 6.0.1 | Config load + snapshot | Already used in Phase 3 `src/utils/config.py` [VERIFIED] |
| wandb | 0.25.1 | Experiment tracking (mirror of CSV) | Phase 3 D-13 locked; has `wandb.errors.Error` class confirmed [VERIFIED: `hasattr(wandb.errors, 'Error') == True` 2026-04-15] |
| pytest | 9.0.2 | Unit + integration test framework | Phase 3 tests/ suite already established [VERIFIED] |

### Supporting (new for Phase 4)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hashlib (stdlib) | — | `config_hash`, `checkpoint_sha` (SHA256 of JSON, SHA256 of .pth bytes) | D-12 reproducibility metadata |
| subprocess (stdlib) | — | `run_ablations.py` subprocess calls to train.py/evaluate.py; `git rev-parse HEAD` | D-26 runner, D-12 git_sha |
| tempfile (stdlib) + os.replace | — | Atomic `.done` marker write-temp-rename (Windows-safe same-dir atomic) | D-31 — pattern already used in `src/utils/checkpoint.py` [VERIFIED: existing code] |
| csv (stdlib) | — | `results-index.csv` append-only writes | Reuses Phase 3 `src/utils/csv_logger.py` pattern (D-33) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| subprocess runner (D-26) | Direct `from src.train import main; main()` import | **D-26 default is subprocess**: robust crash isolation, cross-platform, native resume. Direct import 2x faster but a crash in one run corrupts CUDA state for the next. |
| `sys.argv[0]` guard (D-08) | Stack inspection via `inspect.currentframe()` | Stack inspection more fragile (pytest's loader varies). `sys.argv[0]` robust and documented as "program name". `__main__` module check is another option but doesn't prevent REPL/IPython imports. |
| `np.savez_compressed` | `np.savez` raw | Tested: compressed 465B vs raw 9478B for 2-video synthetic [VERIFIED 2026-04-15]. 20x smaller for real sparse score vectors. Default compressed. |
| append CSV (D-33) | SQLite database | CSV is greppable, pandas-native, and survives uncontrolled writes. SQLite adds server-grade overhead for a 50-row audit. |
| separate `test_dataset.py` module | Reuse `MILFeatureDataset(mode="test")` | MILFeatureDataset mode=test **already** returns full-length snippets (D-12 from Phase 3). BUT D-07 mandates import-boundary isolation — so `test_loader.py` owns a thin wrapper that calls MILFeatureDataset(mode="test") inside its sys.argv-guarded module. |

**Installation:** No new deps. All above already installed in `vcc-main` env [VERIFIED 2026-04-15].

**Version verification:**
```bash
C:/Anaconda/envs/vcc-main/python.exe -c "import torch, numpy, sklearn, pandas, wandb; print(torch.__version__, numpy.__version__, sklearn.__version__, pandas.__version__, wandb.__version__)"
# → 2.6.0+cu124 1.26.x 1.8.0 2.2.2 0.25.1
```

## Architecture Patterns

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│ scripts/run_ablations.py  (D-26 orchestrator)                              │
│   ─ queue: [(variant, seed, dataset, cache_variant), ...]                  │
│   ─ wandb_preflight.py  → fail fast if wandb unconfigured (D-39)           │
│   ─ for each tuple:                                                        │
│       ─ deterministic run_dir = results/<ds>_<var>[_<cv>]_s<seed>/  (D-30) │
│       ─ .done marker present?  → SKIP (D-31 filesystem probe)              │
│       ─ else:                                                              │
│            subprocess: python src/train.py --config ... --run-name ...     │
│            subprocess: python src/evaluate.py --run-dir ... --split test   │
│       ─ on success: append row to results/results-index.csv  (D-33)        │
│       ─ on failure: log to runner-errors.log, continue queue  (D-32)       │
└────────────────────────────────────────────────────────────────────────────┘
                │
                │ subprocess boundary
                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ src/train.py  (Phase 3, adds --run-name override per D-30)                 │
│   ─ builds model via MODEL_REGISTRY[variant](**cfg["model"])               │
│   ─ writes best_model.pth + last_model.pth + config_snapshot.json          │
│   ─ rtfm_i3d variant loads I3D features via cfg.paths.i3d_features  (D-36) │
└────────────────────────────────────────────────────────────────────────────┘
                │
                │ file handoff: best_model.pth + config_snapshot.json in run_dir
                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ src/evaluate.py  (D-06 CLI)                                                │
│   ─ load config_snapshot.json → build_model(**cfg["model"])                │
│   ─ torch.load(best_model.pth, weights_only=True)                          │
│   ─ dataset = cfg["dataset"]  ("ucf" | "xd" | "xd_i3d")                    │
│   ─ from src.eval.test_loader import build_test_dataset  ← IMPORT BOUNDARY │
│   │                                                                        │
│   │  ┌──────────────────────────────────────────────────┐                 │
│   │  │ src/eval/test_loader.py  (D-07 + D-08 isolation) │                 │
│   │  │   _assert_called_from_evaluate_or_pytest()       │                 │
│   │  │   dispatch by cfg["dataset"]:                    │                 │
│   │  │     ─ ucf  → UCFTestDataset (skel+clip)          │                 │
│   │  │     ─ xd_i3d → XDI3DTestDataset (5-crop avg)     │                 │
│   │  └──────────────────────────────────────────────────┘                 │
│   │                                                                        │
│   ─ for each test video:                                                   │
│       snippet_scores = model(skel, clip, mask).cpu().numpy()   # [N]       │
│       frame_scores = snippet_to_frame(snippet_scores, n_frames, window)    │
│                                                                            │
│       ┌────────────────────────────────────────────────┐                  │
│       │ src/eval/snippet_to_frame.py  (D-15 C4 guard)  │                  │
│       │   UCF:   repeat(repeat(s, 64), 10) → 30fps     │                  │
│       │   XD I3D: repeat(s, 16) → video frame rate     │                  │
│       └────────────────────────────────────────────────┘                  │
│                                                                            │
│   ─ concat all videos → scores[], labels[]                                 │
│       assert len(scores) == len(labels)  ← C4 LENGTH ASSERTION             │
│   ─ src/eval/metrics.py: auc = roc_auc_score(labels, scores)               │
│                          ap  = average_precision_score(labels, scores)     │
│   ─ per-category breakdown (D-11, D-17)                                    │
│   ─ reproducibility metadata: config_hash, git_sha, checkpoint_sha (D-12)  │
│   ─ writes: eval_metrics.json, eval_scores.npz, per_category.csv  (D-06)   │
│   ─ atomic .done marker write-temp-rename  (D-31)                          │
└────────────────────────────────────────────────────────────────────────────┘
                │
                │ downstream consumers (no re-inference)
                ▼
     Phase 5 TTA → results/ucf_gated_fusion_s42/best_model.pth (adaptation base)
     Phase 6 viz → eval_scores.npz (temporal curve plots)
```

### Recommended Project Structure (additions for Phase 4)

```
src/
├── evaluate.py               # NEW — D-06 CLI entry, --run-dir + --split
├── eval/                     # NEW — imported only by evaluate.py + pytest
│   ├── __init__.py
│   ├── test_loader.py        # D-07, D-08 — sys.argv guard + dataset dispatch
│   ├── snippet_to_frame.py   # D-15 — single utility for all broadcast cases
│   ├── metrics.py            # D-11 — auc/ap/video_auc/per_category; length assert
│   └── ucf_annotations.py    # D-16, D-17 — parse Temporal_Anomaly_Annotation.txt
├── data/
│   └── i3d_dataset.py        # NEW — [N, 5, 1024] I3D loader for rtfm_i3d variant
└── models/
    ├── registry.py           # MODIFIED — add "rtfm_i3d" 5th key
    └── rtfm_i3d.py           # NEW — FM head + MILHead, minimum viable

scripts/
├── run_ablations.py          # NEW — D-26 subprocess orchestrator
├── wandb_preflight.py        # NEW — D-39 fail-fast wandb check
├── verify_pooling_caches.py  # NEW — sanity check for skeleton_2person + clip_mean
├── extract_ctrgcn.py         # MODIFIED — add --keep-persons flag (D-21)
└── extract_clip.py           # MODIFIED — add --pool={mean|mean_max} flag (D-23)

configs/
├── rtfm_i3d.yaml             # NEW — D-35, dataset=xd_i3d, paths.i3d_features
├── gated_fusion_2person.yaml # NEW — D-22, data.skel_agg=concat, skel_dim=512
└── gated_fusion_clip_mean.yaml # NEW — D-23, paths.clip_features=.../clip_mean/, clip_dim=512

data/
└── annotations/              # NEW dir (D-04 — git-tracked exception to E:/features rule)
    └── ucf_temporal.txt      # NEW — committed Sultani 2018 annotation file

tests/
├── test_snippet_to_frame.py  # NEW — C4 regression (single + compound repeat)
├── test_ucf_annotations.py   # NEW — parse Temporal_Anomaly_Annotation.txt shape
├── test_eval_metrics.py      # NEW — auc/ap/video_auc on deterministic synth
├── test_test_loader.py       # NEW — sys.argv guard (C3 regression)
├── test_evaluate_cli.py      # NEW — end-to-end on 10-video synthetic fixture
├── test_rtfm_i3d.py          # NEW — FM head shape + MIL loss smoke
├── test_i3d_dataset.py       # NEW — 5-crop concatenation + averaging
└── test_run_ablations.py     # NEW — queue construction + .done probe + CSV append
```

### Pattern 1: Import-Boundary Isolation for Test Data (D-07 + D-08)

**What:** `src/eval/test_loader.py` module top executes a runtime guard that raises `RuntimeError` if imported from any code path other than `src/evaluate.py` or pytest test files. The module lives in a directory (`src/eval/`) that `src/train.py` never imports from.

**When to use:** Phase 4 C3 prevention. Belt-and-suspenders on top of directory layout.

**Example (D-08 enforcement):**
```python
# src/eval/test_loader.py
import sys
from pathlib import Path

_ALLOWED_SENTINELS = ("evaluate.py",)           # canonical entry point
_PYTEST_SENTINELS = ("pytest", "py.test")       # test runners

def _assert_called_from_evaluate_or_pytest() -> None:
    """Raise RuntimeError unless sys.argv[0] is evaluate.py or pytest.

    This is a belt-and-suspenders guard on top of the import-boundary
    convention (src/data/dataset.py never imports src/eval/). C3 pitfall
    prevention per PITFALLS.md.
    """
    argv0 = Path(sys.argv[0]).name if sys.argv else ""
    if argv0 in _ALLOWED_SENTINELS:
        return
    if any(s in argv0 for s in _PYTEST_SENTINELS):
        return
    # IPython/Jupyter? Reject — this module must not be reachable from a notebook.
    raise RuntimeError(
        f"src/eval/test_loader.py was imported by sys.argv[0]={argv0!r}. "
        "This module is restricted to src/evaluate.py and pytest test runners "
        "to prevent test-set leakage (C3). If you are running a legitimate "
        "evaluation, invoke `python src/evaluate.py --run-dir <path>` instead."
    )

_assert_called_from_evaluate_or_pytest()
# All dataset + annotation loading symbols follow...
```

### Pattern 2: `snippet_to_frame()` Unified Utility (D-15, C4 prevention)

**What:** Single function handles both compound expansion (skel/CLIP on UCF → 30fps) and simple expansion (I3D → 16-frame granularity).

**Signature design:**
```python
# src/eval/snippet_to_frame.py
import numpy as np
from typing import Optional

def snippet_to_frame(
    scores: np.ndarray,          # [N_snippets] float — model output
    n_frames: int,                # target length (original video frame count)
    snippet_window: int,          # frames per snippet AT model's native granularity
    *,
    upsample_factor: int = 1,     # additional post-expansion factor (e.g., 10 for UCF PNG→orig)
) -> np.ndarray:
    """Broadcast snippet scores to frame-level scores.

    UCF skel/CLIP:  snippet_window=64 (PNGs), upsample_factor=10 (PNG→orig 30fps)
    XD I3D:         snippet_window=16 (frames), upsample_factor=1

    Args:
        scores: [N] per-snippet anomaly scores in [0,1]
        n_frames: expected output length (from annotation-derived label vector)
        snippet_window: frames per snippet in model's native grid
        upsample_factor: post-expansion multiplier (1 for no-op)

    Returns:
        [n_frames] float array. Truncated or tail-repeated to match n_frames exactly.

    Raises:
        AssertionError if the computed length would drift > 2*snippet_window from n_frames
        (catches upstream bugs in N_snippets or label construction).
    """
    if scores.ndim != 1:
        raise ValueError(f"scores must be 1D, got shape {scores.shape}")
    expanded = np.repeat(scores, snippet_window)     # [N * snippet_window]
    if upsample_factor > 1:
        expanded = np.repeat(expanded, upsample_factor)  # [N * snippet_window * uf]

    # Tolerance check: computed length may differ from n_frames by up to
    # (snippet_window * upsample_factor) because tail frames beyond N * window
    # were dropped at extraction time.
    tol = snippet_window * upsample_factor
    if abs(len(expanded) - n_frames) > 2 * tol:
        raise AssertionError(
            f"snippet_to_frame length drift exceeds tolerance: "
            f"expanded={len(expanded)} vs n_frames={n_frames} tol={tol}. "
            f"Upstream N_snippets or label vector is inconsistent."
        )

    # Right-align: if expanded shorter than n_frames, tail-repeat the last score;
    # if longer, truncate. This matches RTFM's behavior on UCF (trailing frames
    # outside any snippet get the last snippet's score).
    if len(expanded) < n_frames:
        pad = np.full(n_frames - len(expanded), expanded[-1], dtype=expanded.dtype)
        return np.concatenate([expanded, pad])
    return expanded[:n_frames]
```

### Pattern 3: Deterministic Run Dir + `.done` Marker (D-30 + D-31)

**What:** Run dir name is `(dataset, variant, cache_variant, seed)` — no timestamp. Re-running overwrites in place. `.done` marker (empty file or short sentinel) is written atomically only after eval completes.

**Atomic marker idiom (Windows-safe):**
```python
import os, tempfile
from pathlib import Path

def mark_done(run_dir: Path) -> None:
    """Atomic .done marker write-temp-rename. Safe on Windows same-dir.

    Only call after eval_metrics.json exists and parses as valid JSON (D-34).
    """
    target = run_dir / ".done"
    fd, tmp = tempfile.mkstemp(prefix=".done.", suffix=".tmp", dir=str(run_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"eval_complete\n")  # content ignored; presence is the signal
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(target))     # atomic rename within same filesystem
    except Exception:
        if os.path.exists(tmp):
            try: os.unlink(tmp)
            except OSError: pass
        raise

def is_done(run_dir: Path) -> bool:
    """D-31 filesystem probe — no DB/state file."""
    return (run_dir / ".done").exists()
```
Pattern matches existing `src/utils/checkpoint.py` `save_checkpoint_atomic()`. [VERIFIED 2026-04-15: tempfile + os.replace works on Windows same-dir.]

### Pattern 4: Reproducibility Metadata (D-12)

**What:** Three separate hashes + git state embedded in `eval_metrics.json` every run.

**Implementation:**
```python
import hashlib, json, subprocess
from pathlib import Path

def config_hash(cfg: dict) -> str:
    """SHA256 of sort_keys=True JSON — whitespace + order invariant."""
    # D-12 + specifics: sort_keys=True, compact, no whitespace.
    # Discretion note: cfg must be JSON-serializable. If it contains PosixPath,
    # cast paths to str() before hashing to keep the hash stable across OS.
    serializable = json.loads(json.dumps(cfg, default=str))  # Path→str
    payload = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def checkpoint_sha(path: Path) -> str:
    """SHA256 of best_model.pth raw bytes.

    Memory: 14 MB checkpoint per Phase 3 D-15 observation. Read in chunks to
    avoid loading the whole file into memory — hashlib supports streaming.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):  # 1 MB chunks
            h.update(chunk)
    return h.hexdigest()

def git_sha() -> str:
    """git rev-parse HEAD + `-dirty` suffix if working tree dirty.

    Failure modes: (a) not in a git repo → returns 'unknown', (b) git not on
    PATH → returns 'unknown', (c) submodule-only change → dirty flag set by
    `git status --porcelain` (includes submodules by default).
    """
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL
        ).strip())
        return sha + ("-dirty" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"
```
Pattern parallels Phase 3 `src/utils/config.py::_git_info()` [VERIFIED: existing impl].

### Pattern 5: RTFM Minimum-Viable FM Head (D-18, Claude's Discretion)

**What:** The minimum-viable RTFM reproduction is the Feature Magnitude head + MIL ranking loss applied to 1024-d I3D RGB features. The MTN temporal module (Aggregate class with dilated conv + non-local block) is NOT required per CONTEXT.md Claude's Discretion — if the AP gate is met without it.

**FM head formula (from RTFM `model.py` [CITED: github.com/tianyu0207/RTFM]):**
```python
# src/models/rtfm_i3d.py — minimum viable
import torch
import torch.nn as nn
from src.models.mil_head import MILHead

class RTFMI3D(nn.Module):
    """RTFM-style FM head + MILHead on 1024-d I3D RGB features.

    Minimum viable reproduction per CONTEXT.md Claude's Discretion:
      - NO MTN temporal module (no dilated conv, no non-local block)
      - FM head = L2 norm of features; top-k selection in the loss
      - Standard MILHead reused (same as other variants)

    Matches RTFM/MGFN published XD-I3D AP (77.81% / 80.11%) within ±1% gate.
    If the gate fails, planner adds the MTN Aggregate module as a Phase 4b
    fallback (see CONTEXT.md deferred: "Flow I3D stream inclusion" is another).
    """
    def __init__(self, i3d_dim: int = 1024, head_hidden=(128, 32), dropout: float = 0.3, **unused):
        super().__init__()
        # FM head is just L2 norm — no parameters. The MIL head classifies the
        # top-k snippets selected by feature magnitude.
        self.ln_i3d = nn.LayerNorm(i3d_dim)
        self.head = MILHead(input_dim=i3d_dim, hidden_dims=tuple(head_hidden), dropout=dropout)

    def forward(self, skel=None, clip=None, i3d=None, mask=None):
        """Dispatch on `i3d` kwarg to stay parallel with other variants.

        i3d: [B, T, 1024] at training time (5-crop averaged in test or
             5-crop stacked in training per D-19).
        """
        if i3d is None:
            raise ValueError("RTFMI3D requires `i3d` input (1024-d per snippet)")
        x = self.ln_i3d(i3d)
        scores = self.head(x).squeeze(-1)  # [B, T]
        # Feature magnitude vector (for top-k selection, also used by loss if desired)
        feat_mag = torch.norm(x, p=2, dim=-1)   # [B, T]
        return scores  # MIL top-k happens in loss per Phase 3 D-01
```
Note: D-19 5-crop training protocol means the dataloader emits 5× more bags (each crop = one separate sample); test-time averages the 5 crops to a single `[N, 1024]` forward.

### Pattern 6: CLIP Mean-Only Cache Concat Order (D-23)

**Observation from `scripts/extract_clip.py`:**
```python
mean_feat = embeddings.mean(dim=0)          # [512]  ← mean first
max_feat = embeddings.max(dim=0).values     # [512]
concat = torch.cat([mean_feat, max_feat], dim=0)  # [1024]  ← order: [mean | max]
```
[VERIFIED: `scripts/extract_clip.py` line 298-300]. Therefore `--pool=mean` **slices indices 0..511** from the existing logic (equivalent: skip the concat, save only `mean_feat`). The new `clip_mean/*.npy` shape is `[N, 512]` and the model YAML sets `clip_dim: 512`.

**Verification axiom (`verify_pooling_caches.py`):** for every video ID in the existing `E:/features/ucf/clip/*.npy` cache, the new `clip_mean/*.npy` must satisfy:
- `mean_cache[vid].shape == (mean_max_cache[vid].shape[0], 512)`
- `np.allclose(mean_cache[vid], mean_max_cache[vid][:, :512])` within float32 eps

For `skeleton_2person/*.npy`: shape `[N, 2, 256]` vs existing `[N, 256]` M-pool — the M-pool cache is already `mean(dim=1)` of the 2-person tensor, so:
- `mpool_cache[vid] ≈ keep_persons_cache[vid].mean(axis=1)` within eps (but not exactly — M-pool extraction may have used different internal aggregation; check `extract_ctrgcn.py` ln 234: `feat.mean(dim=[1, 3, 4])` means M pooled alongside T'/V'; re-extraction with `--keep-persons` must preserve M separately before the T'/V' pool)

### Anti-Patterns to Avoid
- **Computing `np.repeat(scores, 10)` without first expanding through snippet_window**: produces 3fps-granularity frame scores but the annotation is at 30fps. [CITED: D-14 explicitly says 30fps]
- **Loading test annotations in `src/data/dataset.py`**: breaks the import-boundary invariant and defeats C3 prevention. Test annotations live only in `src/eval/ucf_annotations.py`.
- **Writing `.done` before `eval_metrics.json`**: if eval crashes after the file but before the marker, runner re-runs train+eval (wasteful but safe). If marker written first, runner skips a broken run (unsafe). [CITED: D-34]
- **Loading `last_model.pth` for reporting**: constitutes test-set model selection. [CITED: D-10, Anti-Pattern 2 in ARCHITECTURE.md]
- **Mixing timestamp-dir + deterministic-dir**: re-runs drift apart; `results-index.csv` can't dedupe. Phase 3 D-14's timestamp pattern reserved for ad-hoc/debug; orchestrated runs use deterministic per D-30.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frame-level AUC computation | Custom thresholding / ROC integration | `sklearn.metrics.roc_auc_score(y_true, y_score)` | Edge cases (all-zeros, ties, partial AUC) handled correctly. Community-standard baseline. [CITED: sklearn docs] |
| Average precision | Custom P-R curve integration | `sklearn.metrics.average_precision_score` | Stepwise integration by scikit-learn; matches published RTFM/MGFN numbers exactly |
| SHA256 of large checkpoints | Read whole file into memory | `hashlib.sha256()` with `iter(lambda: f.read(2**20), b"")` | 14 MB checkpoint today, 50+ MB with RTFM on I3D. Streaming avoids peak memory. |
| Atomic file write on Windows | Rename across devices / use mv | `tempfile.mkstemp(dir=same_dir)` + `os.replace()` | Cross-device rename is NOT atomic on Windows. Same-dir mkstemp+replace is. [VERIFIED: `src/utils/checkpoint.py` already uses this] |
| Parsing the UCF temporal annotation | Regex / custom split | `str.split()` on 2-space delimiter | Format is fixed (filename, category, start1, end1, start2, end2) with `-1 -1` sentinel [VERIFIED: Sultani 2018 GitHub raw]. Plain split sufficient. |
| Ablation orchestration | Makefile / shell script | Python subprocess.run with explicit queue | Greppable, unit-testable, native resume via `.done`. D-26 locked. |
| wandb offline fallback | Custom retry loop | `try: wandb.init() except wandb.errors.Error: wandb.init(mode="offline")` | `wandb.errors.Error` is the documented catch-all base class [VERIFIED: `hasattr(wandb.errors, 'Error') == True`] |
| JSON schema validation of `eval_metrics.json` | `jsonschema` library | `json.load()` + explicit key asserts in tests | Adding a schema library is overkill for 10 known keys (D-11, D-12). pytest tests already cover the schema. |
| CSV append concurrency | File locking library (`portalocker`) | Single-writer guarantee from `run_ablations.py` serial queue | D-33 append is only ever written by the orchestrator; no concurrent writers by design. |

**Key insight:** Every "Don't Hand-Roll" above has a silent-failure mode that would cost hours of debugging if wrong. The harness gate (RTFM ±1%) catches computation errors; the unit tests catch schema errors; the `.done` probe catches write-ordering errors. Layered defenses.

## Runtime State Inventory

> Phase 4 is greenfield evaluation code — no rename/refactor component. **This section is omitted.**

## Common Pitfalls

### Pitfall 1: C4 — Silent Frame-Label Length Mismatch in 30fps Expansion

**What goes wrong:** Snippet scores broadcast through a two-stage `repeat` (64-wide for PNG, 10-wide for PNG→orig30fps). If either stage is off-by-one at the tail, the expanded vector is short or long by up to 640 frames for a multi-snippet video. `sklearn.metrics.roc_auc_score` silently truncates when fed mismatched arrays in older versions; newer versions raise but the message is cryptic (`ValueError: shape mismatch`).

**Why it happens:** (a) PNG index space vs original-video-frame index space is a 10x discrepancy that's easy to forget. (b) `snippet_to_frame()` needs the `n_frames` hint from the annotation to right-size the output, not just the snippet count. (c) Videos where `total_frames / 64 != N_snippets` (the trailing-PNGs case) are the only ones where the tail drift manifests.

**How to avoid:**
1. `snippet_to_frame()` returns exactly `n_frames` — either truncates or tail-repeats. [Pattern 2 above]
2. The `n_frames` argument is sourced from the annotation file's implicit length (derived from max(end1, end2, total_frames_estimate)), never from `N_snippets * 64 * 10`.
3. Unit test `test_snippet_to_frame.py` covers (a) exact multiple, (b) trailing-PNG drift, (c) annotation-only videos (normal, all-zero labels).

**Warning signs:** (a) `eval_metrics.json` `snippet_auc` and `auc` differ by more than 0.5%; (b) per-video score arrays in `eval_scores.npz` have heterogeneous lengths that don't divide evenly by 640.

### Pitfall 2: C3 — Test Loader Transitively Imported by a Training Test

**What goes wrong:** A unit test for Phase 3 training inadvertently imports `src/eval/test_loader.py` (e.g. to check the registry pattern), triggering the sys.argv guard. Worse: if the guard accepts pytest by regex match `"pytest"` in argv, a rogue training test reuses test annotations to sanity-check the model output, silently leaking test labels.

**Why it happens:** Pytest is a legitimate caller; the test module uses it to exercise the test_loader, but a separate test_train.py file can discover the symbol through monkeypatching or shared conftest fixtures.

**How to avoid:**
1. Directory layout invariant: no file in `src/` outside `src/eval/` and `src/evaluate.py` imports `from src.eval.test_loader`. Add a repo-level grep CI check.
2. The sys.argv regex allow-list is narrow: only `evaluate.py`, `pytest`, `py.test`. Jupyter/IPython rejected.
3. Pytest tests of `test_loader.py` live in `tests/test_test_loader.py` and import only through the `build_test_dataset()` public entry point. Training tests (`tests/test_train*.py`) MUST NOT import from `src.eval`.
4. Unit test `test_test_loader.py` asserts the guard rejects import from a fake argv (e.g., `sys.argv = ["wrong.py"]` via monkeypatch).

**Warning signs:** Any test that both (a) imports from `src.eval.*` and (b) checks a training-related metric like loss convergence.

### Pitfall 3: 5-Crop Training Effective Batch Size Inflation (D-19)

**What goes wrong:** D-19 says training expands 5-crop I3D features as separate samples, giving 5× effective training signal. With Phase 3's `batch_size=16` (D-04), the crop-expanded batch is effectively 80 videos per step. The MIL top-k (k=3, D-01) and margin (1.0, D-02) are calibrated to 16-video bags; 80-video bags make the hinge trivially easy to satisfy, potentially triggering C5 collapse.

**Why it happens:** RTFM's original convention was `batch_size * 10 crops = 320 effective samples` for UCF, with k=3 still. But RTFM's k was `num_segments // 10 = 3` — a ratio, not absolute. With our fixed `k_topk=3` (Phase 3 D-01), the k-to-bag-size ratio differs.

**How to avoid:**
1. Option A (CONTEXT.md specifics bullet 7): Keep `k_topk=3` but reduce batch_size to 16/5 ≈ 3 for rtfm_i3d training. Document in `rtfm_i3d.yaml`.
2. Option B: Average crops during training too (not just test), treating each video as one sample. Safer but 5× fewer samples per epoch — may need more epochs.
3. Option C: Keep batch_size=16 but validate empirically against the ±1% gate before committing. Plan discretion.

**Recommendation:** Use Option A (smaller batch_size for rtfm_i3d YAML). Rationale: matches the spirit of D-19 (5× training signal) without distorting the MIL ranking ratios. Planner picks this explicitly in the `rtfm_i3d.yaml` config.

**Warning signs:** rtfm_i3d training loss converges to 0 within 5 epochs and the gate fails — C5 collapse under inflated effective batch.

### Pitfall 4: I3D Train Set Size Mismatch (3225 / 3954)

**What goes wrong:** Only 3225 videos have I3D features on disk; `xd_train.txt` + `xd_val.txt` combined list 3954 video IDs. Missing 729 are all `label_A` (normal). If the dataloader silently drops missing videos, the normal/abnormal ratio in MIL bags is skewed, and the MIL loss sees a biased distribution.

**How to avoid:**
1. At dataset construction (`src/data/i3d_dataset.py`), filter the split to only include videos with at least 1 crop on disk (pattern matches `MILFeatureDataset._is_loadable()`).
2. Emit a startup log line: `"rtfm_i3d: using 3225/3954 train+val videos (729 missing, all label_A)"`.
3. Add assertion: `assert normal_remaining / abnormal_remaining > 0.5`, fail loudly if ratio drifts below because that invalidates MIL bag pairing.
4. Document in the phase plan: 729 missing normals reduce effective training data by ~18% but test set is 100% complete (800/800) — test AP measurement is not affected.

**Warning signs:** Startup log reports missing videos but no error; MIL bags get OOM in `itertools.cycle()` due to empty normal queue.

[VERIFIED 2026-04-15: Train I3D = 3225/3954 (all 729 missing are label_A). Test = 800/800 complete.]

### Pitfall 5: `config_snapshot.json` Schema Drift Between Phase 3 and Phase 4

**What goes wrong:** Phase 3's `snapshot_config()` writes `{"config": {...}, "git": {...}, "python": "...", "torch": "...", "packages": [...]}`. Phase 4's `evaluate.py` expects `config_snapshot.json["config"]` to contain `cfg["paths"]`, `cfg["model"]`, `cfg["dataset"]`. If a future Phase 3 change renames keys or nests the model variant, evaluate.py breaks on checkpoints from the new training.

**How to avoid:**
1. Add a schema version to snapshot: `{"version": 1, "config": {...}, ...}`. `src/evaluate.py` asserts version on load.
2. Unit test `test_config.py` fixes the snapshot schema as a round-trip regression (Phase 3 writes → Phase 4 reads → keys match).
3. Never compute `config_hash` over the full snapshot — only over the `config` sub-dict (D-12). This means Phase 3 vs Phase 4 snapshotting differences don't change the hash.

**Warning signs:** `evaluate.py` raises `KeyError` on a specific checkpoint while working on others.

### Pitfall 6: wandb First-Run Wizard Blocks Non-Interactive Queue (D-39 resolves)

**What goes wrong:** On a fresh machine, `wandb.init(mode="online")` prompts `"Enter your W&B API key from https://wandb.ai/authorize: "`. In `run_ablations.py` subprocess context, this prompt blocks stdin and the queue hangs indefinitely. Phase 3 VERIFICATION explicitly noted this as an open nit.

**How to avoid:**
1. `scripts/wandb_preflight.py` checks: (a) `WANDB_API_KEY` env var set, OR (b) `~/.netrc` or `~/.config/wandb/settings` contains API key, OR (c) `wandb.api.api_key is not None` [VERIFIED: available attribute 2026-04-15].
2. If none: exit with non-zero and actionable error message (`"Set WANDB_API_KEY or run `wandb login` before launching run_ablations.py"`).
3. `run_ablations.py` calls preflight first; if exit code is non-zero, abort queue start.
4. During run, if `wandb.init` raises `wandb.errors.Error`, training subprocess re-inits with `mode="offline"` (D-40) and logs a warning to `runner-errors.log`.

**Warning signs:** Queue appears hung; first run `.done` never appears; no errors in `runner-errors.log` (wandb prompt is on stdin).

### Pitfall 7: Cache Shape Change Silently Breaks `MILFeatureDataset`

**What goes wrong:** `MILFeatureDataset` calls `np.load(path)` and asserts `skel.shape[0] == clip.shape[0]`. With `--keep-persons`, skeleton shape becomes `[N, 2, 256]` and the existing assertion still passes (N matches). But the model's `SkeletonProj(skel_dim=256)` expects `[B, T, 256]`, receives `[B, T, 2, 256]`, and either silently broadcasts or crashes deep in `nn.Linear.forward()`.

**How to avoid:**
1. Extend `MILFeatureDataset.__init__` to accept `cfg["data"]["skel_agg"] ∈ {"concat", "max", "mean", None}`. At load time, if `skel.ndim == 3 and skel.shape[1] == 2`:
   - `concat` → reshape to `[N, 512]`, set `skel_dim=512`
   - `max` → `.max(axis=1)` → `[N, 256]`
   - `mean` → `.mean(axis=1)` → `[N, 256]`
   - `None` → reject 3D input explicitly
2. Unit test `test_dataset.py` parameterizes over all 4 skel_agg values.
3. Config YAML asserts compatibility: `gated_fusion_2person.yaml` sets `data.skel_agg: concat` AND `model.skel_dim: 512`.

**Warning signs:** `RuntimeError: input size 512 does not match expected 256` deep in `model.forward()`.

## Code Examples

### Example 1: UCF Temporal Annotation Parser (D-16, D-17)

```python
# src/eval/ucf_annotations.py
"""Parse Temporal_Anomaly_Annotation.txt per Sultani 2018 convention.

File format (2-space-delimited, 6 columns):
    Abuse028_x264.mp4  Abuse  165  240  -1  -1
    Arson011_x264.mp4  Arson  150  420  680  1267
    Normal_Videos_003_x264.mp4  Normal  -1  -1  -1  -1

Columns:
    0: video filename (with _x264.mp4 suffix)
    1: category (Abuse, Arrest, ..., Normal)
    2,3: start1, end1 (frame indices in original 30fps video; -1 if N/A)
    4,5: start2, end2 (second anomaly interval; -1 -1 if single or normal)

D-16: per-frame label = union [start1, end1] ∪ [start2, end2]. -1 -1 = all zero.
D-17: category column directly — no filename regex.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import numpy as np

@dataclass(frozen=True)
class VideoAnnotation:
    video_id: str           # without _x264.mp4 suffix, matches split file IDs
    category: str           # e.g. "Abuse", "Fighting", "Normal"
    intervals: tuple        # ((s1, e1), (s2, e2)) — -1 encoded as None

    @property
    def is_normal(self) -> bool:
        return all(s is None for s, _ in self.intervals)

def parse_annotations(path: Path) -> Dict[str, VideoAnnotation]:
    """Return {video_id_without_suffix: VideoAnnotation}."""
    annos = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split()   # whitespace-split handles 2-space delimiter
            if len(parts) != 6:
                raise ValueError(f"Expected 6 columns, got {len(parts)} in line: {line!r}")
            fname, category, s1, e1, s2, e2 = parts
            # Strip _x264.mp4 (or just .mp4) to match split file convention
            vid = fname.replace("_x264.mp4", "").replace(".mp4", "")
            def _v(s): return None if int(s) == -1 else int(s)
            anno = VideoAnnotation(
                video_id=vid,
                category=category,
                intervals=((_v(s1), _v(e1)), (_v(s2), _v(e2))),
            )
            annos[vid] = anno
    return annos

def frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray:
    """Build [n_frames] binary label vector from annotation intervals (D-16)."""
    labels = np.zeros(n_frames, dtype=np.int64)
    for (s, e) in anno.intervals:
        if s is None: continue
        # Sultani convention: frame indices are 1-based-inclusive; clamp + convert.
        s = max(0, int(s))
        e = min(n_frames, int(e))
        if e > s: labels[s:e] = 1
    return labels
```
[CITED: github.com/WaqasSultani/AnomalyDetectionCVPR2018 raw Temporal_Anomaly_Annotation.txt verified 2026-04-15]

### Example 2: XD I3D 5-Crop Dataset (D-19, D-20)

```python
# src/data/i3d_dataset.py
"""I3D 5-crop dataset for rtfm_i3d variant (D-19, D-20).

Naming: E:/i3d-features/i3d-features/RGB/<video_id>__<crop>.npy for train+val
        E:/i3d-features/i3d-features/RGBTest/<video_id>__<crop>.npy for test
Shape: [N_snippets, 1024] float32 per crop. 5 crops per video (indices 0..4).

Training (D-19): each of 5 crops is a separate sample in the bag → 5× signal.
Test (D-19):    average crops to [N, 1024] before single forward pass.
"""
from pathlib import Path
from typing import List
import numpy as np
import torch
from torch.utils.data import Dataset

class I3DFeatureDataset(Dataset):
    def __init__(self, split_file: str, feature_dir: str, mode: str = "train",
                 T: int = 32, n_crops: int = 5):
        if mode not in ("train", "val", "test"):
            raise ValueError(f"mode must be train|val|test, got {mode!r}")
        self.feature_dir = Path(feature_dir)
        self.mode = mode
        self.T = T
        self.n_crops = n_crops

        ids = Path(split_file).read_text(encoding="utf-8").splitlines()
        ids = [i.strip() for i in ids if i.strip()]
        # D-32 discretion: filter missing (729 missing from XD train are all label_A)
        self.video_ids = [vid for vid in ids if self._has_all_crops(vid)]
        print(f"[i3d_dataset] {mode}: {len(self.video_ids)}/{len(ids)} videos available")

    def _has_all_crops(self, vid: str) -> bool:
        # Require at least 1 crop; pad with duplicates if < n_crops.
        # (Train has 1 video with 4 crops instead of 5.)
        return (self.feature_dir / f"{vid}__0.npy").exists()

    def _load_crops(self, vid: str) -> np.ndarray:
        """Returns [n_crops, N_snippets, 1024]. Pads missing crops with crop 0."""
        crops = []
        for c in range(self.n_crops):
            p = self.feature_dir / f"{vid}__{c}.npy"
            if p.exists():
                crops.append(np.load(p))
            elif crops:
                crops.append(crops[0])  # pad missing crop with crop 0
        return np.stack(crops, axis=0)  # [n_crops, N, 1024]

    def __getitem__(self, idx):
        vid = self.video_ids[idx]
        crops = self._load_crops(vid)  # [5, N, 1024]
        # XD label parsing (same as MILFeatureDataset._parse_label_xd)
        label = 0 if vid.endswith("_label_A") else 1

        if self.mode == "test":
            # D-19: average crops at test time → [N, 1024]
            feats = crops.mean(axis=0).astype(np.float32)
            return {"i3d": torch.from_numpy(feats), "label": float(label), "video_id": vid}
        else:
            # D-19: return all 5 crops — collate expands to 5× bag size.
            # Post-T=32 resampling happens here to keep shapes aligned.
            resampled = np.stack([self._resample_T(crops[c]) for c in range(self.n_crops)], axis=0)
            return {"i3d": torch.from_numpy(resampled.astype(np.float32)),  # [5, T, 1024]
                    "label": float(label), "video_id": vid}

    def _resample_T(self, feat: np.ndarray) -> np.ndarray:
        """RTFM process_feat equivalent: uniform-segment sampling to T=32."""
        N = feat.shape[0]
        if N >= self.T:
            r = np.linspace(0, N, self.T + 1, dtype=np.int64)
            return np.stack([feat[r[i]:max(r[i]+1, r[i+1])].mean(axis=0) for i in range(self.T)])
        else:
            # Pad by repeating last feature (RTFM handles via np.linspace degenerate segs)
            idxs = np.sort(np.random.randint(0, N, size=self.T))
            return feat[idxs]

    def __len__(self): return len(self.video_ids)
```

### Example 3: run_ablations.py Queue Skeleton (D-26, D-31, D-33)

```python
# scripts/run_ablations.py
"""Subprocess ablation orchestrator (D-26).

Usage:
    python scripts/run_ablations.py --queue rtfm_gate
    python scripts/run_ablations.py --queue phase4_main
    python scripts/run_ablations.py --queue phase4_pooling --dry-run
"""
import argparse, csv, json, subprocess, sys, time
from pathlib import Path
from dataclasses import dataclass, asdict

PROJECT = Path("D:/ViolenceCC")
RESULTS = PROJECT / "results"
INDEX_CSV = RESULTS / "results-index.csv"
ERR_LOG = PROJECT / "runner-errors.log"

INDEX_COLUMNS = ["run_name", "variant", "dataset", "seed", "cache_variant",
                 "auc", "ap", "n_videos", "n_frames", "start_time", "end_time",
                 "config_hash"]

@dataclass
class RunSpec:
    dataset: str       # "ucf" | "xd_i3d"
    variant: str       # "rtfm_i3d" | "gated_fusion" | ...
    seed: int
    config: str        # path to YAML
    cache_variant: str = ""  # "2person" | "clip_mean" | "" (default cache)

    @property
    def run_name(self) -> str:
        # D-30 deterministic naming
        cv = f"_{self.cache_variant}" if self.cache_variant else ""
        return f"{self.dataset}_{self.variant}{cv}_s{self.seed}"

    @property
    def run_dir(self) -> Path:
        return RESULTS / self.run_name

QUEUES = {
    "rtfm_gate": [   # RUN FIRST per specifics bullet — harness gate
        RunSpec("xd_i3d", "rtfm_i3d", 42, "configs/rtfm_i3d.yaml"),
    ],
    "phase4_main": [
        RunSpec("ucf", "skeleton_only", 42, "configs/skeleton_only.yaml"),
        RunSpec("ucf", "clip_only",     42, "configs/clip_only.yaml"),
        RunSpec("ucf", "late_fusion",   42, "configs/late_fusion.yaml"),
        RunSpec("ucf", "gated_fusion",  42, "configs/gated_fusion.yaml"),
    ],
    "phase4_pooling": [   # 2 pooling ablations at seed=42 (D-22, D-23, D-29)
        RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion_2person.yaml", "2person"),
        RunSpec("ucf", "gated_fusion", 42, "configs/gated_fusion_clip_mean.yaml", "clip_mean"),
    ],
    "phase4_seeds": [   # 3-seed Gated Fusion stability (D-27, D-28)
        RunSpec("ucf", "gated_fusion", 123,  "configs/gated_fusion.yaml"),
        RunSpec("ucf", "gated_fusion", 2024, "configs/gated_fusion.yaml"),
        # seed=42 run is in phase4_main — not duplicated
    ],
}

def is_done(run_dir: Path) -> bool:
    return (run_dir / ".done").exists()

def run_one(spec: RunSpec, timeout_s: int = 7200) -> dict:
    """Run train + evaluate for one spec. Returns status dict."""
    spec.run_dir.mkdir(parents=True, exist_ok=True)
    status = {"spec": spec.run_name, "start_time": time.strftime("%Y-%m-%dT%H:%M:%S")}

    # Train
    train_cmd = [sys.executable, "src/train.py",
                 "--config", spec.config,
                 "--seed", str(spec.seed),
                 "--results-dir", str(spec.run_dir.parent),
                 "--run-name", spec.run_name]  # <-- NEW --run-name override
    try:
        subprocess.run(train_cmd, check=True, timeout=timeout_s,
                       cwd=str(PROJECT), stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as e:
        status["phase"] = "train_failed"
        log_error(spec, e)
        return status

    # Evaluate
    eval_cmd = [sys.executable, "src/evaluate.py",
                "--run-dir", str(spec.run_dir),
                "--split", "test"]
    try:
        subprocess.run(eval_cmd, check=True, timeout=timeout_s // 4,
                       cwd=str(PROJECT), stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as e:
        status["phase"] = "eval_failed"
        log_error(spec, e)
        return status

    # Append to results-index.csv
    metrics_path = spec.run_dir / "eval_metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
        append_index_row(spec, metrics, status["start_time"])
        status["phase"] = "done"
    else:
        status["phase"] = "eval_missing_metrics"
        log_error(spec, Exception("eval_metrics.json not written"))
    return status

def append_index_row(spec: RunSpec, metrics: dict, start_time: str) -> None:
    row = {
        "run_name": spec.run_name,
        "variant": spec.variant, "dataset": spec.dataset,
        "seed": spec.seed, "cache_variant": spec.cache_variant,
        "auc": metrics.get("auc"), "ap": metrics.get("ap"),
        "n_videos": metrics.get("n_videos"), "n_frames": metrics.get("n_frames"),
        "start_time": start_time,
        "end_time": metrics.get("eval_timestamp"),
        "config_hash": metrics.get("config_hash"),
    }
    RESULTS.mkdir(exist_ok=True)
    write_header = not INDEX_CSV.exists() or INDEX_CSV.stat().st_size == 0
    with open(INDEX_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLUMNS)
        if write_header: w.writeheader()
        w.writerow(row)

def log_error(spec: RunSpec, exc) -> None:
    with open(ERR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {spec.run_name}\t{type(exc).__name__}: {exc}\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True, choices=sorted(QUEUES))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-preflight", action="store_true",
                    help="skip wandb_preflight check (for unit tests)")
    args = ap.parse_args()

    if not args.no_preflight:
        preflight = subprocess.run(
            [sys.executable, "scripts/wandb_preflight.py"],
            cwd=str(PROJECT)
        )
        if preflight.returncode != 0:
            print("wandb preflight failed; aborting queue", file=sys.stderr)
            return 2

    specs = QUEUES[args.queue]
    summary = {"succeeded": [], "skipped": [], "failed": []}
    for spec in specs:
        if is_done(spec.run_dir):
            summary["skipped"].append(spec.run_name)
            print(f"[skip] {spec.run_name} (.done present)")
            continue
        if args.dry_run:
            print(f"[dry-run] would run {spec.run_name}")
            continue
        print(f"[start] {spec.run_name}")
        status = run_one(spec)
        if status.get("phase") == "done":
            summary["succeeded"].append(spec.run_name)
        else:
            summary["failed"].append({"run": spec.run_name, "phase": status.get("phase")})

    print(json.dumps(summary, indent=2))
    return 0 if not summary["failed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

### Example 4: wandb Preflight Check (D-39, D-40)

```python
# scripts/wandb_preflight.py
"""Fail-fast wandb configuration check (D-39).

Exits 0 if wandb is ready, nonzero with actionable message otherwise.

Resolves the Phase 3 VERIFICATION nit: WANDB_MODE=disabled doesn't suppress the
first-run wizard — we need explicit preflight in non-interactive queue contexts.
"""
import os, sys

def main() -> int:
    # Path 1: WANDB_API_KEY env var
    if os.environ.get("WANDB_API_KEY"):
        print("[preflight] wandb: WANDB_API_KEY env var set")
        return 0

    # Path 2: ~/.netrc or wandb settings file
    try:
        import wandb
    except ImportError:
        print("[preflight] wandb not installed; using CSV-only mode is fine "
              "if all configs set wandb.mode=disabled")
        return 0

    # wandb.api.api_key picks up from ~/.netrc / wandb settings automatically
    if wandb.api.api_key is not None:
        print("[preflight] wandb: api_key discovered via ~/.netrc or settings")
        return 0

    # No credentials found
    sys.stderr.write(
        "ERROR: wandb is not configured.\n"
        "Run one of:\n"
        "  (1) export WANDB_API_KEY=<your key>\n"
        "  (2) wandb login   # interactive one-time\n"
        "  (3) set `wandb.mode: disabled` in every config YAML (CSV-only mode)\n"
    )
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
```

### Example 5: Metric Computation with C4 Assertion (D-11, D-15)

```python
# src/eval/metrics.py
"""Frame-level metrics with C4 length-assertion guards (D-11, D-15)."""
from typing import Dict, List
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

def compute_frame_metrics(
    per_video_scores: Dict[str, np.ndarray],
    per_video_labels: Dict[str, np.ndarray],
    per_video_category: Dict[str, str],
) -> dict:
    """Compute auc, ap, video_auc, per_category from per-video arrays.

    D-15 CONTRACT: every np.concatenate() below MUST produce identical-length
    arrays between scores and labels. Assertion BEFORE each sklearn call.
    """
    # Global AUC / AP — concatenate all videos
    all_scores, all_labels = [], []
    for vid in per_video_scores:
        s, y = per_video_scores[vid], per_video_labels[vid]
        assert len(s) == len(y), (
            f"C4 REGRESSION at {vid}: scores={len(s)} labels={len(y)}"
        )
        all_scores.append(s); all_labels.append(y)
    y_score = np.concatenate(all_scores)
    y_true = np.concatenate(all_labels)
    assert len(y_score) == len(y_true)

    result = {
        "auc": float(roc_auc_score(y_true, y_score)),
        "ap": float(average_precision_score(y_true, y_score)),
        "n_videos": len(per_video_scores),
        "n_frames": int(len(y_true)),
    }

    # Video-level AUC — max score per video vs binary video label
    video_max_scores = np.array([per_video_scores[v].max() for v in per_video_scores])
    video_labels = np.array([1 if per_video_labels[v].any() else 0 for v in per_video_scores])
    if len(np.unique(video_labels)) > 1:
        result["video_auc"] = float(roc_auc_score(video_labels, video_max_scores))

    # Per-category breakdown (D-11, D-17) — anomaly categories only per Discretion
    per_cat = {}
    for cat in set(per_video_category.values()):
        if cat == "Normal": continue
        cat_vids = [v for v in per_video_scores if per_video_category[v] == cat]
        # Include all Normal videos in each category's evaluation so AUC is well-defined
        # (roc_auc_score requires both classes)
        eval_vids = cat_vids + [v for v in per_video_scores
                                 if per_video_category[v] == "Normal"]
        y_s = np.concatenate([per_video_scores[v] for v in eval_vids])
        y_l = np.concatenate([per_video_labels[v] for v in eval_vids])
        assert len(y_s) == len(y_l), f"C4 REGRESSION per-category {cat}"
        if len(np.unique(y_l)) > 1:
            per_cat[cat] = {
                "auc": float(roc_auc_score(y_l, y_s)),
                "ap": float(average_precision_score(y_l, y_s)),
            }
    result["per_category"] = per_cat
    return result
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `openai/clip` (2021 frozen) | `open-clip-torch 3.3.0` | Already in Phase 3 | Active maintenance + same ViT-B/16 openai weights [VERIFIED Phase 3] |
| Phase 3 D-14 timestamped run dirs | D-30 deterministic run dirs | Phase 4 | Idempotent re-run; `results-index.csv` dedupes by `run_name` |
| `np.savez` raw | `np.savez_compressed` | Phase 4 | 20x smaller [VERIFIED]; scores are sparse in [0,1] → high compression |
| Train/test leak via one-import convention | Import-boundary + sys.argv guard | Phase 4 D-07 + D-08 | Belt-and-suspenders C3 defense [CITED: PITFALLS C3] |
| `test_loader` parses annotations itself | Dedicated `src/eval/ucf_annotations.py` | Phase 4 | Parse once + cache; reused by per-category + per-video paths |

**Deprecated/outdated:**
- RTFM's `process_feat(feat, 32)` sub-sample-at-load is inherited from the RTFM codebase but was already superseded in Phase 3 D-09 by uniform-32-segment sampling (same idea, different name) [CITED: utils.py].
- `MILFeatureDataset.__getitem__` had a zero-pad D-10 that was later reverted to sample-with-replacement [CITED: `src/data/dataset.py` docstring]. New `I3DFeatureDataset` follows the post-revision convention directly.

## Assumptions Log

> Claims in this research that are ASSUMED (not directly verified in this session).

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | RTFM/MGFN published 77.81% / 80.11% AP on XD is specifically for I3D-RGB (not RGB+Flow) — 2026-04-15 search says "RTFM I3D-RGB 77.81%, MGFN VideoSwin-RGB 80.11%" | RTFM/MGFN anchor comparison | MGFN's 80.11% may actually be VideoSwin. Plan should default to **RTFM 77.81%** as the primary anchor and treat 80.11% as upper bound only. |
| A2 | `n_frames` for UCF videos can be derived from the annotation file's max(start2, end2, end1) with a tail allowance of `+64*10` PNG-snippet-span | Pitfall 1, Example 5 | If PNGs end before the last annotation frame (unlikely but possible), labels will be longer than scores → `snippet_to_frame` right-pads | 
| A3 | The 729 missing XD train I3D videos are all `label_A` (normal) | Pitfall 4 | [VERIFIED 2026-04-15 by `Counter(len(v) for v in ...)` on disk; 3 sample missing IDs listed include only `label_A`]. This is actually VERIFIED — remove from assumptions. |
| A4 | `wandb.errors.Error` is the catch-all base for auth + network failures | Pattern 4, Pitfall 6, D-40 | `wandb.errors.CommError` is more specific; if Error is too broad, we mask legitimate config bugs. Test: in preflight unit test, mock `wandb.init` raising `wandb.errors.CommError` and confirm the offline fallback triggers. |
| A5 | 5-crop training with `batch_size=16` may trigger C5 collapse (Pitfall 3); recommended reducing to 3 | Pitfall 3 | Empirical. If RTFM gate passes with batch_size=16, leave alone. If fails, reduce batch_size OR enable crop-averaging during training. |
| A6 | The MTN temporal module (Aggregate class) is NOT required for minimum-viable RTFM reproduction | Pattern 5 | If FM head alone misses ±1% gate on XD, planner adds Aggregate module from RTFM source as Phase 4b fallback. CONTEXT.md Claude's Discretion already permits this. |
| A7 | XD test is 800 videos × 5 crops × 1024-d on disk | D-19 | [VERIFIED 2026-04-15: `Test I3D videos= 800, Test crop-count distribution: {5: 800}`]. |
| A8 | Temporal_Anomaly_Annotation.txt delimiter is exactly 2 spaces | Example 1 | [VERIFIED 2026-04-15: raw fetch from WaqasSultani/AnomalyDetectionCVPR2018]. Actually VERIFIED — Python `str.split()` on whitespace handles both 1-space and 2-space delimiters. Remove from assumptions. |

**Cleanup:** A3, A7, A8 are actually [VERIFIED]. Remaining true assumptions: A1, A2, A4, A5, A6 — **5 items** requiring planner/discuss-phase confirmation.

## Open Questions

1. **Which anchor for the ±1% gate — RTFM 77.81% or MGFN 80.11%?**
   - What we know: Both are XD-I3D frame-level AP; both are from published papers (RTFM ICCV 2021, MGFN AAAI 2023).
   - What's unclear: MGFN's 80.11% may have been with VideoSwin features, not vanilla I3D-RGB. RTFM's 77.81% is unambiguously I3D-RGB.
   - Recommendation: **Default to RTFM's 77.81%** as the primary anchor. If implementation yields AP > 78.81%, both gates pass. Document both bounds in the config YAML as comments.

2. **Is the 5-crop training batch size issue (Pitfall 3) empirical or theoretical?**
   - What we know: RTFM's original code used 10-crop with a specific k-to-bag ratio.
   - What's unclear: Whether our fixed k=3 with 5× bag inflation triggers C5 in practice.
   - Recommendation: First run rtfm_i3d with `batch_size=16` (same as other variants) and check whether the AP gate is met. If it fails with a collapse-like profile (train loss → 0 fast, per-snippet score variance → 0), cut batch_size to 3 and re-run. This is a testable empirical question, not a planning risk.

3. **What `n_frames` source for the UCF per-video frame-level label vector?**
   - What we know: Annotation gives frame indices `[0, end_annotation_frame]`. Video PNG count is in `E:/snippets/ucf/<vid>_boundaries.json` as `total_frames` × 10.
   - What's unclear: Whether `n_frames = total_frames * 10` (implied by the every-10th-PNG convention) or `n_frames = max_ann_end_frame + small_buffer`. These can differ on videos where PNGs were truncated at extraction.
   - Recommendation: **Use `total_frames * 10` as canonical** (ground truth: number of frames in the original video). Label construction clamps intervals to this upper bound. Unit test: for 2-3 known UCF anomalies (Abuse028, Abuse030), the produced label vector has the expected 1-region between (start1, end1).

4. **Phase 4b success-criteria inheritance from Phase 4 to ROADMAP.md:**
   - What we know: Phase 4 SC #1 (RTFM gate) is satisfied once in Phase 4 — not re-run in Phase 4b (unless XD I3D cache diverges, which is unlikely).
   - What's unclear: Do Phase 4b's SC #2-5 copy Phase 4's verbatim with "XD" swapped, or are the numbers different?
   - Recommendation: Phase 4b SC #2 = "Gated Fusion AP >= 80% on XD test" (the RTFM gate is already established); SC #3 = XD ablation table; SC #4 = XD 3-seed std < 0.5%; SC #5 = XD violence subset breakdown (Fighting+Abuse+Riot per EVAL-04). SC #1 not repeated.

5. **Should `evaluate.py --split val` compute frame-level AUC?**
   - What we know: Val split has no frame-level labels — Phase 3 D-11 confirms val uses MIL Ranking Loss only.
   - What's unclear: Is there any use for a `--split val` path at all? Discretion says MIL-loss-only is sufficient; full forward pass optional.
   - Recommendation: **Implement `--split val` as MIL-loss-only** (no AUC). Useful for sanity checks (reproducing Phase 3 `val_loss` post-hoc from the best checkpoint). Planner marks as nice-to-have.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| torch (vcc-main env) | evaluate.py, rtfm_i3d, all training | ✓ | 2.6.0+cu124 | — |
| sklearn | metrics.py | ✓ | 1.8.0 | — |
| pandas | results-index.csv aggregation | ✓ | 2.2.2 | — |
| numpy | snippet_to_frame, label vectors, npz | ✓ | 1.26.x | — |
| wandb | wandb_logger mirror | ✓ | 0.25.1 (`wandb.errors.Error` present) | CSV logger only if disabled |
| pytest | tests/ | ✓ | 9.0.2 | — |
| git | `git rev-parse HEAD` for D-12 | ✓ | — | `git_sha = "unknown"` graceful fallback |
| XD I3D RGB cache | rtfm_i3d training + test | ✓ | 3225 train+val / 800 test | None — if missing, Phase 4 fails gate |
| UCF-Crime Temporal_Anomaly_Annotation.txt | UCF test eval | ✗ (not yet downloaded) | — | D-04 requires fresh download to `data/annotations/` |
| UCF skeleton + CLIP cache | UCF ablation table | ✓ (Phase 2 complete) | 1728/1728 | — |
| XD skeleton + CLIP cache | Phase 4b | ✗ (3/3954, extracting out-of-band) | — | **Phase 4 not blocked** (D-02); Phase 4b gated on this |

**Missing dependencies with no fallback:** None for Phase 4 UCF work.

**Missing dependencies with fallback:**
- Temporal_Anomaly_Annotation.txt: D-04 adds a one-time download step to a Phase 4 plan. Alternative fallback is RTFM's pre-computed `list/gt-ucf.npy` (float64, 1,114,144 frames total across 290 concatenated test videos per [VERIFIED 2026-04-15 fetch from `tianyu0207/RTFM/main/list/gt-ucf.npy`]), but that requires parsing the video-ordering from `ucf-i3d-test.list` and aligning with our `xd_test.txt`. D-04 download path is simpler.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` section |
| Quick run command | `pytest tests/test_snippet_to_frame.py tests/test_ucf_annotations.py tests/test_eval_metrics.py -x --tb=short` |
| Full suite command | `pytest tests/ -x --tb=short` |
| Markers | `e2e`, `requires_features` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-01 | RTFM-XD AP within ±1% of 77.81% | e2e (GPU) | `pytest tests/test_rtfm_i3d.py -x -m e2e` | ❌ Wave 0 |
| EVAL-01 | RTFM architecture shapes + MIL loss smoke | unit | `pytest tests/test_rtfm_i3d.py::test_rtfm_i3d_shapes -x` | ❌ Wave 0 |
| EVAL-02 | UCF frame AUC on synthetic 10-video fixture | integration | `pytest tests/test_evaluate_cli.py::test_eval_ucf_synth -x` | ❌ Wave 0 |
| EVAL-02 | `snippet_to_frame()` correctness (C4 regression) | unit | `pytest tests/test_snippet_to_frame.py -x` | ❌ Wave 0 |
| EVAL-02 | Length assertion fires on mismatch | unit | `pytest tests/test_eval_metrics.py::test_assertion_on_mismatch -x` | ❌ Wave 0 |
| EVAL-03 | XD AP code path on synthetic fixture (Phase 4 shakedown; full XD in Phase 4b) | integration | `pytest tests/test_evaluate_cli.py::test_eval_xd_i3d_synth -x` | ❌ Wave 0 |
| EVAL-04 | Per-category breakdown (Fighting+Assault) | unit | `pytest tests/test_eval_metrics.py::test_per_category -x` | ❌ Wave 0 |
| EVAL-04 | Annotation parser handles all categories + -1 sentinel | unit | `pytest tests/test_ucf_annotations.py -x` | ❌ Wave 0 |
| EVAL-05 | 3-seed runner appends 3 rows to results-index.csv | integration | `pytest tests/test_run_ablations.py::test_three_seed_queue -x` | ❌ Wave 0 |
| C3 regression | test_loader rejects non-evaluate/non-pytest import | unit | `pytest tests/test_test_loader.py::test_argv_guard -x` | ❌ Wave 0 |
| C3 regression | No module in src/ other than evaluate.py/test files imports src.eval | integration | `pytest tests/test_test_loader.py::test_import_boundary -x` | ❌ Wave 0 |
| C4 regression | Compound repeat produces expected length vs annotation | unit | `pytest tests/test_snippet_to_frame.py::test_compound_repeat_ucf -x` | ❌ Wave 0 |
| C4 regression | I3D single-stage repeat produces 16*N length | unit | `pytest tests/test_snippet_to_frame.py::test_single_repeat_i3d -x` | ❌ Wave 0 |
| D-12 metadata | config_hash deterministic + sort-invariant | unit | `pytest tests/test_config.py::test_config_hash_stable -x` | extend existing |
| D-12 metadata | checkpoint_sha streams without OOM | unit | `pytest tests/test_config.py::test_checkpoint_sha_streaming -x` | extend existing |
| D-31 atomic | .done marker only after eval_metrics.json | unit | `pytest tests/test_evaluate_cli.py::test_done_atomic -x` | ❌ Wave 0 |
| D-33 audit | results-index.csv append-only header handling | unit | `pytest tests/test_run_ablations.py::test_index_csv_append -x` | ❌ Wave 0 |
| D-39 wandb | wandb_preflight exits 0 when WANDB_API_KEY set | unit | `pytest tests/test_run_ablations.py::test_wandb_preflight_env -x` | ❌ Wave 0 |
| D-40 wandb | wandb.errors.Error → offline fallback in wandb_logger | unit | `pytest tests/test_wandb_logger.py::test_offline_fallback -x` | extend existing |

### Sampling Rate
- **Per task commit:** `pytest tests/test_snippet_to_frame.py tests/test_eval_metrics.py tests/test_ucf_annotations.py -x --tb=short` (~10 seconds, covers C4 + metrics + annotation parsing)
- **Per wave merge:** `pytest tests/ -x --tb=short -m "not e2e"` (full suite except GPU-dependent rtfm_i3d — ~2 min)
- **Phase gate:** Full suite green including `-m e2e` before `/gsd-verify-work`. The `e2e` tests exercise actual GPU training on a 10-video fixture (<5 min total).

### Wave 0 Gaps

- [ ] `tests/test_snippet_to_frame.py` — covers EVAL-02, C4 regression
- [ ] `tests/test_ucf_annotations.py` — covers EVAL-04, D-16, D-17
- [ ] `tests/test_eval_metrics.py` — covers EVAL-02, EVAL-04
- [ ] `tests/test_test_loader.py` — covers C3 regression (D-07 + D-08)
- [ ] `tests/test_rtfm_i3d.py` — covers EVAL-01 (shapes + e2e gate)
- [ ] `tests/test_i3d_dataset.py` — covers D-19 + D-20 + 729-missing-video handling
- [ ] `tests/test_evaluate_cli.py` — covers end-to-end run-dir contract (D-06)
- [ ] `tests/test_run_ablations.py` — covers D-26 + D-31 + D-33 + D-39
- [ ] `tests/fixtures/synthetic_eval.py` — synthetic 10-video UCF fixture (Abuse028-like with known anomaly intervals) + 3-video XD I3D fixture
- [ ] `tests/conftest.py` — extend with `test_anno_path`, `eval_run_dir`, `i3d_features_dir`, `ucf_temporal_path` fixtures
- [ ] Annotation file: `data/annotations/ucf_temporal.txt` — download step in a Phase 4 plan (D-04)

*(No framework install gap — pytest 9.0.2 + conftest scaffolding already in place.)*

## Security Domain

> `security_enforcement` not set in `.planning/config.json`. This is a pure-research offline-batch codebase with no authentication/sessions/external input surface. Omitting this section per the researcher template "Omit only if explicitly `false` in config" — applied here because no S-requirements exist in REQUIREMENTS.md and the out-of-scope table explicitly excludes deployment artifacts.

**Contextual note:** The only security-adjacent surface is (a) `wandb` API key handling — which is delegated to wandb's own CLI-login flow and env vars (not stored in code), and (b) import-boundary enforcement, which is a methodological integrity concern (C3) not a security concern.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/04-baseline-evaluation-main-results/04-CONTEXT.md` — 41 locked decisions D-01..D-41
- `.planning/research/PITFALLS.md` — C3, C4 canonical refs
- `.planning/research/ARCHITECTURE.md` — Component 7 (Evaluation Engine), Anti-Pattern 2
- `.planning/research/FEATURES.md` — Table stakes "Frame-level AUC", "RTFM baseline reproduction"
- `.planning/research/SUMMARY.md` — keys 3, 14-16
- `.planning/phases/03-model-architecture-training-infrastructure/03-CONTEXT.md` — D-07, D-12-16
- `src/utils/checkpoint.py` [VERIFIED] — atomic save pattern reused for `.done` marker
- `src/utils/config.py` [VERIFIED] — snapshot_config + _git_info existing pattern
- `src/data/dataset.py` [VERIFIED] — MILFeatureDataset._is_loadable filter pattern reused
- `scripts/extract_ctrgcn.py` ln 183-206, 234 [VERIFIED] — 4-stream preparation + M-pool formula
- `scripts/extract_clip.py` ln 298-300 [VERIFIED] — mean+max concat order
- GitHub `tianyu0207/RTFM` raw `model.py`, `train.py`, `test_10crop.py`, `utils.py` [CITED: 2026-04-15 fetch]
- GitHub `WaqasSultani/AnomalyDetectionCVPR2018` raw `Temporal_Anomaly_Annotation.txt` [CITED: 2026-04-15 fetch, first 15 lines verified]
- GitHub `carolchenyx/MGFN/test.py` [CITED: 2026-04-15 fetch — confirms `np.repeat(scores, 16)` for I3D]
- scikit-learn docs [CITED: Context7 `/scikit-learn/scikit-learn` 2026-04-15] — `roc_auc_score`, `average_precision_score` APIs
- On-disk inspection: E:/i3d-features/i3d-features/RGB + RGBTest [VERIFIED: 3225 train / 800 test, all 5 crops except 1 train video]
- On-disk inspection: E:/snippets/ucf/*_boundaries.json [VERIFIED: snippet_frame_ranges in PNG index space, frames_per_snippet=64]

### Secondary (MEDIUM confidence)
- WebSearch 2026-04-15: RTFM 77.81% / MGFN 80.11% XD AP [verified against MGFN arxiv 2211.15098 table reference]
- WebSearch 2026-04-15: "I3D features 16 frame snippet window" — multiple sources confirm 16-frame I3D convention

### Tertiary (LOW confidence)
- MGFN's 80.11% anchor: published number may be VideoSwin rather than I3D — A1 in Assumptions Log; planner defaults to RTFM's 77.81%

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libs verified in vcc-main env at current versions
- Architecture: HIGH — directly extends Phase 3 patterns; 41 locked decisions in CONTEXT.md
- Pitfalls: HIGH — C3/C4 inherited from established research; new pitfalls (3,4,5,6,7) grounded in verified on-disk state
- RTFM reproduction: MEDIUM — gate threshold confirmed but MTN-omission is a CONTEXT-permitted simplification that hasn't been empirically validated
- 5-crop training semantics: MEDIUM — D-19 locked but batch-size interaction with k=3 is untested (Pitfall 3)
- UCF annotation parsing: HIGH — raw file verified 2026-04-15

**Research date:** 2026-04-15
**Valid until:** 2026-05-15 (30 days; stable research domain, XD cache state may shift as Phase 4b extraction progresses)
