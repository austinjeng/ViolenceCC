# Codebase Structure

**Analysis Date:** 2026-06-09

## Directory Layout

```
ViolenceCC/
├── src/                       # Lightweight fusion-head training/eval/TTA (vcc-main env)
│   ├── train.py               # Training entry point (YAML-config driven)
│   ├── evaluate.py            # Eval entry point (run-dir → frame AUC/AP)
│   ├── models/                # 5 variant wrappers + registry + shared MILHead
│   ├── losses/                # MIL ranking loss
│   ├── data/                  # Feature-cache datasets + paired DataLoaders
│   ├── eval/                  # snippet→frame, metrics, annotations, test loader
│   ├── tta/                   # TENT / SAR / SAM / disc_reweight + evaluate_tta.py
│   └── utils/                 # config, checkpoint, seed, scheduler, loggers
├── scripts/                   # Extraction, orchestration, charts, paper build
├── configs/                   # ~45 per-variant YAML configs
├── tests/                     # pytest suite (~46 test files) + fixtures
├── data/
│   ├── splits/                # {dataset}_{train,val,test}.txt video id lists
│   ├── annotations/           # ucf_temporal.txt, xd_temporal.txt (frame GT)
│   └── weights/               # clip/, ctrgcn/ checkpoint dirs
├── results/                   # Per-run output dirs + results-index.csv + tta/
├── paper/                     # CGW '26 LaTeX (main.tex, references.bib, figures/)
├── envs/                      # requirements-{main,ctrgcn,skeleton}.txt + SETUP.md
├── notebooks/                 # Ad-hoc analysis notebooks
├── .planning/                 # GSD phases, quick tasks, codebase docs, research
├── CLAUDE.md                  # Project instructions + stack + conventions
├── thesis_prd_v2.3.md         # PRD (D-XX decision IDs referenced in code)
└── pyproject.toml             # Package metadata
```

## Directory Purposes

**`src/`:**
- Purpose: all learned-parameter code; runs in `vcc-main` (PyTorch 2.6). Never imports mmcv/rtmlib.
- Contains: entry points (`train.py`, `evaluate.py`) + 6 sub-packages
- Key files: `src/train.py`, `src/evaluate.py`

**`src/models/`:**
- Purpose: 5 MIL-head variants behind a registry, all sharing `MILHead`
- Key files: `src/models/registry.py`, `src/models/mil_head.py`, `src/models/gated_fusion.py` (primary thesis model)

**`src/data/`:**
- Purpose: load per-video `.npy` caches into paired MIL bags
- Key files: `src/data/dataset.py` (`MILFeatureDataset`), `src/data/i3d_dataset.py`, `src/data/loaders.py`

**`src/eval/`:**
- Purpose: snippet→frame broadcast + annotation parsing + sklearn frame metrics
- Key files: `src/eval/snippet_to_frame.py`, `src/eval/metrics.py`, `src/eval/ucf_annotations.py`, `src/eval/xd_annotations.py`, `src/eval/test_loader.py` (import-restricted)

**`src/tta/`:**
- Purpose: test-time adaptation of LayerNorm affine parameters under corruption shift
- Key files: `src/tta/evaluate_tta.py` (entry point), `src/tta/tent.py`, `src/tta/sar.py`, `src/tta/sam.py`, `src/tta/disc_reweight.py`

**`src/utils/`:**
- Purpose: shared infra — config snapshot, atomic checkpoints, determinism, scheduling, logging
- Key files: `src/utils/config.py`, `src/utils/checkpoint.py`, `src/utils/seed.py`, `src/utils/scheduler.py`, `src/utils/csv_logger.py`, `src/utils/wandb_logger.py`, `src/utils/early_stopping.py`

**`scripts/`:**
- Purpose: offline extraction (separate envs), ablation orchestration, chart/table/figure generation, paper build
- Key files: `scripts/extract_skeletons.py`, `scripts/extract_ctrgcn.py`, `scripts/extract_clip.py`, `scripts/run_ablations.py`, `scripts/run_tta_grid.py`, `scripts/corruption.py`, `scripts/create_splits.py`, `scripts/build_paper.ps1`, `scripts/generate_phase{4,6,7,8,9,10}_charts.py`, `scripts/generate_latex_tables.py`
- Note: files prefixed `_tmp_*` / `_*` are throwaway research harnesses (untracked); not production code

**`configs/`:**
- Purpose: one YAML per (variant × dataset × backbone × pooling) combination, ~45 total
- Naming families: `{variant}.yaml` (UCF/CLIP-B16 default), `{variant}_xd.yaml` (XD), `{variant}_{backbone}.yaml` (siglip2 / so400m / giant), `{variant}_2person.yaml` / `_clip_mean.yaml` (pooling ablations), `rtfm_i3d.yaml` / `rtfm_i3d_flow.yaml`

**`results/`:**
- Purpose: per-run output dirs + aggregate index; committed (small metrics/checkpoints), caches are not
- Key files: `results/results-index.csv` (one row per completed run), `results/tta/` (TTA grid runs + `best_configs.json`), `results/phase{6,8,9,10}_charts/`
- Generated: Yes (by train/eval/TTA). Committed: Yes (run dirs); large feature caches live on `E:/`, not here

**`data/splits/`:**
- Purpose: video-id lists, one per line, defining train/val/test partitions
- Files: `ucf_train.txt`, `ucf_val.txt`, `ucf_test.txt`, `xd_train.txt`, `xd_val.txt`, `xd_test.txt`

**`paper/`:**
- Purpose: CGW '26 LaTeX manuscript
- Key files: `paper/main.tex`, `paper/references.bib`, `paper/figures/`, `paper/.latexmkrc`
- Build: `scripts/build_paper.ps1 -Clean`; all `*.pdf/.aux/.bbl/...` artifacts are git-ignored — never commit

## Key File Locations

**Entry Points:**
- `src/train.py`: training, `--config configs/<v>.yaml`
- `src/evaluate.py`: eval, `--run-dir results/<run>/`
- `src/tta/evaluate_tta.py`: one TTA config (subprocess of orchestrator)
- `scripts/run_ablations.py`: subprocess sweep orchestrator, `--queue <queue>`

**Configuration:**
- `configs/*.yaml`: per-run config (keys: `seed`, `dataset`, `paths`, `model`, `data`, `train`, `wandb`)
- `results/<run>/config_snapshot.json`: resolved config + git SHA + pip freeze (provenance)

**Core Logic:**
- `src/models/registry.py`: `variant` → wrapper class
- `src/models/mil_head.py`: shared `D→128→32→1`+Sigmoid head
- `src/losses/mil_loss.py`: top-k ranking + sparsity + smoothness
- `src/data/dataset.py`: `MILFeatureDataset`, label parsing, sampling modes

**Testing:**
- `tests/`: ~46 `test_*.py` files (one per module), `tests/conftest.py`, `tests/fixtures/`

## Naming Conventions

**Files:**
- snake_case module names (`mil_loss.py`, `snippet_to_frame.py`); one model variant per file matching its registry key
- Test files mirror source: `test_<module>.py`
- Throwaway research scripts prefixed `_` / `_tmp_` (excluded from production)

**Directories:**
- Lowercase package dirs under `src/`
- Phase dirs under `.planning/phases/`: `NN-kebab-case-name`
- Quick-task dirs under `.planning/quick/`: `YYMMDD-xxx-kebab-summary`

**Run dirs (`results/`):** `{dataset}_{variant}[_{cache_variant}][_{hp}]_s{seed}`
- Built by `RunSpec.run_name` (`scripts/run_ablations.py:86-90`); the `src/train.py` default adds a timestamp (`{dataset}_{variant}_{seed}_{timestamp}`, `src/train.py:67-70`) unless `--run-name` overrides it (the orchestrator always passes the deterministic name).
- Examples: `ucf_gated_fusion_s42`, `ucf_gated_fusion_2person_s42`, `ucf_clip_only_siglip2_s123`, `xd_i3d_rtfm_i3d_s42`, `ucf_gated_fusion_giant_clip_mean_s42`
- Backbone source-run map for TTA: `BACKBONE_SOURCE_RUNS` in `src/tta/evaluate_tta.py:72-77`

**TTA run dirs (`results/tta/`):** `{method}_{corruption}_{severity}_lr{lr}[_rho{rho}]`
- Examples: `sar_brightness_1_lr0.0001_rho0.001`, `tent_gaussian_noise_3_lr0.001`

## Where to Add New Code

**New model variant:**
- Implementation: `src/models/<variant>.py` with `forward(self, skel=None, clip=None, mask=None)` → `[B, T]`, reusing `MILHead`, exposing named `nn.LayerNorm` attrs for TTA
- Register: add a lazy factory + `MODEL_REGISTRY` entry in `src/models/registry.py`
- Config: add `configs/<variant>.yaml` (copy `configs/gated_fusion.yaml` structure)
- Tests: `tests/test_models.py` / new `tests/test_<variant>.py`

**New backbone (visual):**
- Extraction: extend `--backbone` dispatch + output subdir in `scripts/extract_clip.py`
- Wire-up: add to `BACKBONE_FEATURE_PREFIX` / `BACKBONE_SOURCE_RUNS` in `src/tta/evaluate_tta.py`
- Configs: add `{variant}_{backbone}.yaml` family
- Tests: `tests/test_extract_siglip2.py` pattern

**New TTA method:**
- Implementation: `src/tta/<method>.py` (adaptor class with `reset()`); reuse `configure_model` / `collect_params` from `src/tta/tent.py`
- Wire-up: add to `--method` choices + dispatch in `src/tta/evaluate_tta.py`; add a queue in `scripts/run_ablations.py`
- Tests: `tests/test_<method>.py`

**New loss / regularizer:**
- `src/losses/mil_loss.py` (keep masked-padding + abnormal-only-reg invariants); tests in `tests/test_mil_loss.py`

**Shared utilities:**
- `src/utils/` (config, checkpoint, seed, scheduler, loggers)

**New ablation sweep:**
- Add a queue function (list of `RunSpec`) in `scripts/run_ablations.py`; runs resume via `<run_dir>/.done`

## Special Directories

**`results/`:**
- Purpose: per-run dirs (`best_model.pth`, `config_snapshot.json`, `eval_metrics.json`, `eval_scores.npz`, `train_log.csv`, `per_category.csv`, `.done`) + `results-index.csv`
- Generated: Yes. Committed: Yes (metrics/checkpoints). `.pre_*.bak` files are pre-edit backups from quick tasks.

**`E:/` feature caches (not in repo):**
- `E:/features/{ucf,xd}/{skeleton,clip,siglip2,...}/<video_id>.npy`, `E:/snippets/{ds}/<video_id>_boundaries.json`, `E:/skeletons/{ds}/<video_id>.pkl`
- Generated: Yes (extraction). Committed: No (machine-specific drive, multi-GB).

**`.planning/`:**
- Purpose: GSD workflow artifacts — `phases/`, `quick/`, `codebase/` (these docs), `research/`
- Committed: Yes.

**`paper/` build artifacts:**
- `main.pdf`, `*.aux/.bbl/.blg/.fdb_latexmk/.synctex.gz`: git-ignored; regenerate via `scripts/build_paper.ps1 -Clean`. Never commit.

---

*Structure analysis: 2026-06-09*
