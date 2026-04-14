# Phase 4: Baseline Evaluation & Main Results - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the UCF-Crime evaluation harness and produce the UCF portion of the thesis ablation table. Deliverables: `src/evaluate.py` CLI (frame-level AUC/AP, per-category breakdown, reproducibility metadata); `src/eval/` module with a hard-bounded `TestDataset`; RTFM variant registered in `MODEL_REGISTRY` and trained on XD-Violence I3D features as the evaluation-harness gate; full UCF ablation table (6 variants × seed=42) with 3-seed mean±std stability for Gated Fusion; 2 re-extraction passes producing `skeleton_2person/` and `clip_mean/` caches; `scripts/run_ablations.py` Python runner with filesystem-probe resume and append-only `results-index.csv` audit log. **Phase 4 = UCF-only**; XD-Violence main results are explicitly scoped to a new **Phase 4b** to be added to `ROADMAP.md` by the planner, activated when XD skeleton+CLIP features complete. Phase 5 (TTA) consumes `results/ucf_gated_fusion_s42/best_model.pth` as the canonical adaptation target.

</domain>

<decisions>
## Implementation Decisions

### Phase scope and sequencing
- **D-01:** Phase 4 covers **UCF-Crime only**. All XD-Violence main results (Gated Fusion AP, ablation row, 3-seed stability, per-category) move to a new **Phase 4b** inserted after Phase 4 in `ROADMAP.md`; planner must add this. Rationale: XD skeleton+CLIP features are at 3/3954 and would block the project for 1–2 weeks; Phase 4 proceeds now on the complete UCF cache.
- **D-02:** XD skeleton+CLIP extraction continues out-of-band ("running elsewhere" per user). Phase 4 does **not** wait on or monitor it. When features land in `E:/features/xd/`, Phase 4b activates with the same `evaluate.py` + runner + ablation YAMLs — the Phase 4 code is dataset-portable.
- **D-03:** RTFM reproduction gate **retargeted from UCF → XD-Violence I3D**. XD I3D features are already on disk at `E:/i3d-features/i3d-features/` (5-crop × 1024-d per snippet). Pass threshold: XD frame-level AP within ±1% of either RTFM's published 77.81% or MGFN's 80.11% — planner picks the anchor and documents it.
- **D-04:** UCF `Temporal_Anomaly_Annotation.txt` downloaded from the official Sultani 2018 release, committed to `data/annotations/ucf_temporal.txt` (git-tracked; small file, same treatment as `data/splits/`). Fresh clones do not require a separate download step.
- **D-05:** RTFM uses **RGB I3D stream only** (not RGB+Flow). Matches RTFM's published XD number; Flow is a Phase 4b consideration if the RGB-only AP misses the gate.

### Evaluate.py architecture
- **D-06:** CLI shape: `python src/evaluate.py --run-dir <path> [--split {val|test}]` with `--split=test` default. Reads `config_snapshot.json` + `best_model.pth` from the run dir; writes `eval_metrics.json`, `eval_scores.npz`, `per_category.csv`, and the `.done` marker back into the same dir.
- **D-07:** Test data loading lives in **`src/eval/test_loader.py`** — a separate module imported **only** by `src/evaluate.py`. `src/data/dataset.py` continues to expose only `MILFeatureDataset` (train/val). The Python import graph itself enforces C3 (test-leakage) prevention.
- **D-08:** Loud runtime guard in `src/eval/test_loader.py`: module-level check on `sys.argv[0]` — raises `RuntimeError` unless the calling entry point is `evaluate.py` or a pytest test path. Belt-and-suspenders on top of D-07.
- **D-09:** Explicit `--split {val|test}` flag, never auto-inferred. Val path computes MIL Ranking Loss only (video-level labels, Phase 2 D-10); test path computes frame-level AUC/AP + per-category breakdown.
- **D-10:** `evaluate.py` loads **`best_model.pth` only** (Phase 3 D-15 canonical; TRN-02 early-stopping protocol). No `last_model.pth` eval. Reporting the max of both would constitute test-set model selection (C3-adjacent).
- **D-11:** `eval_metrics.json` metric keys: `auc` (ROC-AUC, primary for UCF), `ap` (average precision, primary for XD), `snippet_auc` (same AUC on the pre-broadcast snippet grid — debug aid for broadcast bugs), `video_auc` (max-score-per-video AUC — weak-supervision sanity), `per_category` (dict of category → {auc, ap}; also exported to `per_category.csv` for thesis LaTeX).
- **D-12:** `eval_metrics.json` reproducibility metadata: `config_hash` (SHA256 of sorted-key JSON of resolved config), `git_sha` (`git rev-parse HEAD`, `-dirty` suffix if working tree dirty), `checkpoint_sha` (SHA256 of `best_model.pth` bytes), `wandb_run_id` (nullable), `dataset`, `split`, `seed`, `eval_timestamp` (ISO 8601), `eval_duration_s`.
- **D-13:** Per-video frame-level scores written to `eval_scores.npz` alongside the JSON — `{video_id: np.ndarray shape (n_frames,)}`. Phase 6 visualization reads this file directly; no re-inference pass required.

### Frame-level metric pipeline
- **D-14:** UCF frame-level AUC computed at **original 30fps granularity**. Model outputs live on the PNG grid (~3fps after Phase 1 D-11 every-10th-frame sampling); `np.repeat(frame_scores, 10)` upsamples to original video frame indices. This matches the RTFM/MGFN/VadCLIP published convention — SC #2 (AUC ≥ 83%) and RTFM gate (84.30% ± 1%) baselines are at this granularity.
- **D-15:** Single utility `snippet_to_frame(scores, n_frames, window)` handles all broadcast cases (skeleton 64-frame windows for fused variants; CLIP 1-FPS windows for single-modal CLIP variant). `assert len(frame_scores) == len(frame_labels)` before **every** `sklearn.metrics` call — C4 prevention per research SUMMARY §4. Master grid for fused variants = skeleton's native `N_snippets`; CLIP features are resampled to skeleton grid at load time.
- **D-16:** UCF per-frame binary labels are the **union** of both anomaly intervals `[start1, end1] ∪ [start2, end2]` from `Temporal_Anomaly_Annotation.txt`. The `-1 -1` sentinel = no interval (normal video). Standard Sultani 2018 convention.
- **D-17:** UCF category labels read from the **category column in the annotation file** (official labels), not regex-parsed from filenames. Violence subset = `{Fighting, Assault}` union per REQUIREMENTS EVAL-04 + research FEATURES.md.

### RTFM variant implementation
- **D-18:** RTFM registered as new `MODEL_REGISTRY` key **`rtfm_i3d`**, consuming 1024-d I3D features (not skel/clip). Routes through our `evaluate.py` — this validates both the RTFM architecture implementation AND our snippet→frame expansion code. A successful AP-within-±1% gate thus proves both surfaces simultaneously.
- **D-19:** 5-crop handling: **training uses all 5 crops as separate samples in the bag** (5× effective training signal); test averages the 5 crops to `[N, 1024]` before forward. Matches RTFM's 10-crop test-time augmentation protocol.
- **D-20:** I3D features accessed via new YAML key `paths.i3d_features` (singular, pointing at `E:/i3d-features/i3d-features/`). The I3D loader knows to read `RGB/` for train+val (via `data/splits/xd_*.txt`) and `RGBTest/` for test.

### Ablation caches and re-extraction
- **D-21:** Multi-person skeleton cache stored as **`[N, 2, 256]` single npy per video**. Model wrapper aggregates at load time via new `cfg.data.skel_agg ∈ {concat, max, mean}` config field. Cache itself is aggregation-agnostic → switching doesn't need re-extraction.
- **D-22:** Phase 4 multi-person ablation runs **`skel_agg=concat` only** (gives `[N, 512]` fed to `SkeletonProj` with `skel_dim=512`). PRD §12.3 lists concat first; SC #3 permits 2 aggregation ablations total, and D-22 spends the skeleton budget on concat. `max` and `mean` tracked as deferred ideas.
- **D-23:** CLIP mean-only cache stored as `[N, 512]` npy (vs default `[N, 1024]` mean+max). New `--pool={mean|mean_max}` flag on `scripts/extract_clip.py`; default remains `mean_max` for backward compatibility.
- **D-24:** Cache layout — **sibling directories**: `E:/features/ucf/skeleton_2person/` and `E:/features/ucf/clip_mean/` alongside existing `skeleton/` and `clip/`. YAML `paths.skeleton_features` / `paths.clip_features` select the cache per-config; the data loader stays directory-agnostic.
- **D-25:** Pooling ablations re-extracted for **UCF only in Phase 4**. XD pooling ablations → Phase 4b scope.

### Ablation orchestration
- **D-26:** **`scripts/run_ablations.py`** Python runner (not shell, not Makefile). Loops over (variant, seed, dataset, cache_variant) tuples, calls `src/train.py` + `src/evaluate.py` as subprocesses. Cross-platform, greppable, straightforward to unit-test, supports resume logic natively.
- **D-27:** Multi-seed (3-seed) runs apply to **Gated Fusion only** per SC #4 ("Gated Fusion AUC/AP on both datasets as mean±std over 3 seeds"). Other variants report single-seed in the ablation table. Saves ~9 runs vs blanket 3-seed.
- **D-28:** Multi-seed set = **`{42, 123, 2024}`**. 42 is the training default (Phase 2 D-11); 123 and 2024 are widely used in VAD literature (PEL4VAD, MGFN, VadCLIP).
- **D-29:** The 2 pooling ablations run at **single seed=42** only. SC #3 asks for "results for" those ablations, not ±std. If the delta between pooling choices is <0.5% in the initial run, Claude's discretion to re-run 3-seed for significance.
- **D-30:** Orchestrated run dir naming (deterministic, no timestamp): `results/<dataset>_<variant>[_<cache_variant>]_s<seed>/`. Examples: `results/ucf_gated_fusion_s42/`, `results/ucf_gated_fusion_2person_s42/`, `results/xd_rtfm_i3d_s42/`. Idempotent — re-running overwrites. Adds `--run-name` override to `src/train.py`. Timestamped Phase 3 D-14 pattern reserved for ad-hoc / debug runs.

### Run-index, resume, and failure recovery
- **D-31:** Skip check = **filesystem probe for `.done` marker**. Runner probes `results/<deterministic_run>/.done`; the marker is written atomically only after both training AND evaluation complete successfully. Its absence means "rerun this tuple".
- **D-32:** Failure recovery = **log error, continue queue**. Runner catches subprocess non-zero exit, appends stdout/stderr to `runner-errors.log` with the (variant, seed, dataset) tuple, proceeds to next run. End-of-queue summary prints succeeded vs failed.
- **D-33:** Append-only **`results/results-index.csv`** audit log: one row per completed run with columns `run_name, variant, dataset, seed, cache_variant, auc, ap, n_videos, n_frames, start_time, end_time, config_hash`. Regenerates thesis tables via `pandas.read_csv` — no re-inference needed.
- **D-34:** Runner auto-runs `evaluate.py` as part of each ablation run (train → evaluate sequence). `.done` is written only after `eval_metrics.json` exists AND is valid JSON. Crashes during eval leave the run incomplete → re-run picks up from training.

### Config management
- **D-35:** **Flat self-contained YAMLs** per Phase 1 D-03 (decision held). 3 new files: `configs/rtfm_i3d.yaml`, `configs/gated_fusion_2person.yaml`, `configs/gated_fusion_clip_mean.yaml`. 7 configs total after Phase 4. Duplication cost is acceptable at this scale; avoids YAML-inheritance library dependency.
- **D-36:** `rtfm_i3d.yaml` binds `dataset: xd_i3d` (new dataset key; loader dispatches on it) and `paths.i3d_features: E:/i3d-features/i3d-features/`. `paths.skeleton_features` / `paths.clip_features` absent (not consumed by RTFM variant).
- **D-37:** Pooling ablation YAMLs **reuse `model.variant: gated_fusion`** with different `paths.skeleton_features` / `paths.clip_features` + new `data.skel_agg: concat` field. `MODEL_REGISTRY` gains only `rtfm_i3d` (5 keys total: skeleton_only, clip_only, late_fusion, gated_fusion, rtfm_i3d). SkeletonProj must accept configurable `skel_dim` (256 for M-pool, 512 for concat).
- **D-38:** YAML naming convention: variant-describing (`rtfm_i3d.yaml`, `gated_fusion_2person.yaml`, `gated_fusion_clip_mean.yaml`) matching Phase 3 style (`gated_fusion.yaml`, `late_fusion.yaml`). Not numbered, not grouped by ablation-dim.

### wandb integration
- **D-39:** **`scripts/wandb_preflight.py`** verifies wandb login is complete OR `WANDB_API_KEY` is set. `run_ablations.py` calls it before the queue opens; fails fast with an actionable error message if wandb is unconfigured. Resolves the Phase 3 VERIFICATION nit (WANDB_MODE=disabled doesn't suppress the first-run wizard).
- **D-40:** wandb auth failure mid-run: training subprocess catches `wandb.errors.Error`, re-initializes with `mode=offline`, logs a non-fatal warning to `runner-errors.log`, continues training. The CSV logger (Phase 3) remains the thesis source-of-truth — wandb is auxiliary.
- **D-41:** wandb tags per run = `[phase4, <dataset>, <variant>, s<seed>]` plus `<cache_variant>` when applicable (e.g., `2person`, `clip_mean`, `i3d_rgb`). Set by `run_ablations.py` based on the tuple.

### Claude's Discretion
- RTFM Feature Magnitude head implementation faithfulness — can simplify from RTFM Eq. 3–7 if the AP gate is met; MTN temporal module is NOT required (minimum viable reproduction is FM head + MIL ranking on I3D).
- `eval_scores.npz` compression choice (`np.savez_compressed` vs `np.savez`); compressed is default if size is an issue.
- `per_category.csv` column ordering (alphabetical vs by anomaly frequency in test set).
- `--split val` evaluation depth (MIL-loss-only is sufficient; full forward pass is optional).
- Whether `config_hash` is computed at training time (stored in `config_snapshot.json`) OR at eval time only — eval-time is simpler and sufficient.
- wandb group name scheme if per-run tags turn out too flat (group by `phase4_primary` / `phase4_pooling` / `phase4_seeds` is a fallback).
- Whether `run_ablations.py` invokes `src.train.main` via `subprocess` (robust crash isolation) or direct import (faster). Subprocess is the safe default.
- Resume-mid-run behavior when a run has `best_model.pth` but no `.done` (crashed during eval): re-running the full train+eval is safe since deterministic dirs overwrite. Optional optimization: skip train if `best_model.pth` exists and `last_model.pth` matches expected final-epoch state.
- Exact `git_sha` dirty-tree handling (`-dirty` suffix vs raising); suffix is the default to preserve observability without blocking legitimate research iterations.
- Per-category.csv row treatment of Normal videos — include as a row (label=normal, AUC trivially undefined without anomalies) OR omit. Default: omit; report only anomaly categories.
- How to handle the I3D training set size mismatch (~16124 crops / 5 = 3225 videos vs 3954 expected): document and skip missing-crop videos in the loader; assert training set size in preflight.

### Folded Todos
None — no pending todos matched Phase 4.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and specifications
- `.planning/REQUIREMENTS.md` — EVAL-01 through EVAL-05 formal requirements for this phase
- `thesis_prd_v2.3.md` §11.2 — Validation / early-stopping protocol (monitor val MIL Ranking Loss only; no frame-level AUC monitoring on val)
- `thesis_prd_v2.3.md` §12 — Evaluation protocol, required ablation list, 3-seed stability protocol
- `thesis_prd_v2.3.md` §12.3 — Multi-person aggregation + CLIP pooling ablation specs (D-21..D-25 derived from here)
- `thesis_prd_v2.3.md` §10.3 — TTA adaptation protocol (shapes Phase 5 handoff, determines which checkpoint Phase 5 consumes)

### Prior phase context
- `.planning/phases/01-environment/1-CONTEXT.md` — D-03 (flat YAML configs — D-35 holds this), D-06 (feature path convention — D-24 extends), D-07 (.gitignore rules — `data/annotations/` is git-tracked per D-04, exception to features/ rule), D-11 (UCF PNG every-10th-frame sampling — drives D-14 upsampling)
- `.planning/phases/02-feature-extraction-pipeline/02-CONTEXT.md` — D-01/D-02 (skeleton 64-frame windows, CLIP 1-FPS — D-15 master grid derives from D-01), D-09..D-12 (stratified splits, seed=42, split file format — reused as-is)
- `.planning/phases/03-model-architecture-training-infrastructure/03-CONTEXT.md` — D-12 (score every snippet at test — D-15 frame-expansion inherits), D-13 (wandb tracking — D-39..D-41 extend), D-14 (timestamped results dir — D-30 overrides for orchestrated runs), D-15 (best/last checkpoint policy — D-10 holds best-only), D-16 (MODEL_REGISTRY string pattern — D-18 extends)

### Pitfalls and methodology
- `.planning/research/PITFALLS.md` — C3 (test-set leakage prevention; enforced by D-07 import boundary + D-08 runtime guard + D-09 explicit split flag), C4 (snippet→frame off-by-one; mitigated by D-15 single utility + length assertion)
- `.planning/research/ARCHITECTURE.md` — Component 7 (Evaluation Engine boundary, frame-level broadcast spec), Anti-Pattern 2 (no test set for model selection — D-10 enforces this)
- `.planning/research/SUMMARY.md` — Key insights #3 (RTFM reproduction gating — D-18 implements), #14-15 (frame-level AUC on UCF, AP on XD — D-11 computes both), #16 (ablation table — D-26..D-30 orchestrate)
- `.planning/research/FEATURES.md` — Table stakes "Frame-level AUC" + "RTFM baseline reproduction" rows

### Reference implementations
- RTFM repo: https://github.com/tianyu0207/RTFM — Feature Magnitude head, 10-crop averaging (D-19 adapts to XD's 5-crop), published XD AP ≈ 77.81%
- MGFN repo: https://github.com/carolchenyx/MGFN — published XD I3D AP ≈ 80.11% (alternative RTFM gate anchor)
- VadCLIP repo: https://github.com/nwpu-zxr/VadCLIP — CLIP eval protocol + UCF anno parsing reference
- PEL4VAD repo: https://github.com/yujiangpu20/PEL4VAD — cleanest file-per-concern structure (D-07 test loader module boundary mirrors this)

### External data sources
- UCF-Crime `Temporal_Anomaly_Annotation.txt` — Sultani 2018 official release (to be downloaded to `data/annotations/ucf_temporal.txt` per D-04). Source: https://webpages.uncc.edu/cchen62/dataset.html or RTFM `list/gt-ucf.npy` fallback.

### Project state
- `.planning/STATE.md` — UCF-Crime 1728/1728 features complete; XD skeleton+CLIP extraction at 3/3954 ("running elsewhere")
- `.planning/phases/03-model-architecture-training-infrastructure/03-VERIFICATION.md` — nit_gap: wandb first-run wizard not suppressed by `WANDB_MODE=disabled`; Phase 4 resolves via D-39 pre-flight script

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- `src/train.py` — Phase 3 training entry; already supports `--seed`, `--epochs`, `--results-dir` CLI overrides; planner must add `--run-name` for D-30 deterministic dirs
- `src/models/registry.py` — existing `MODEL_REGISTRY` with 4 keys; D-18 adds `rtfm_i3d` as 5th
- `src/models/gated_fusion.py` — reused as-is for D-22 + D-23 pooling ablations (config drives data path, not architecture)
- `src/models/skeleton_only.py`, `src/models/clip_only.py`, `src/models/late_fusion.py` — existing single-modal + late fusion variants; consumed by `run_ablations.py` unchanged
- `src/data/dataset.py` + `src/data/loaders.py` — training loaders; planner must extend to honor `cfg.data.skel_agg` (concat/max/mean) + switchable `cfg.paths.skeleton_features` / `cfg.paths.clip_features`
- `src/utils/config.py` — existing `snapshot_config(cfg, path)` writes `config_snapshot.json`; D-12 requires adding a `config_hash()` helper
- `src/utils/wandb_logger.py` — existing wandb init; D-40 requires an offline-fallback branch on `wandb.errors.Error`
- `src/utils/csv_logger.py` — per-epoch training CSV logger pattern; D-33 adds a sibling `results_index_append()` helper
- `src/utils/checkpoint.py` — atomic save pattern; D-31 `.done` marker uses the same write-temp-then-rename idiom
- `scripts/extract_ctrgcn.py` — existing M-pool extractor; D-21 adds `--keep-persons` flag producing `[N, 2, 256]` to `E:/features/ucf/skeleton_2person/`
- `scripts/extract_clip.py` — existing mean+max extractor; D-23 adds `--pool={mean|mean_max}` flag; `mean` output `[N, 512]` to `E:/features/ucf/clip_mean/`
- `scripts/verify_alignment.py` — pattern reused for a new `scripts/verify_pooling_caches.py` sanity check
- `data/splits/ucf_*.txt` — frozen splits (Phase 2 D-09..D-12); consumed by test loader
- `tests/conftest.py` — `splits_dir` fixture; planner extends with `test_anno_path` fixture + `eval_run_dir` fixture for `evaluate.py` unit tests

### Established patterns
- Scripts-vs-src split (Phase 1 D-02): `src/evaluate.py` + `src/eval/*.py` live with `src/train.py`; `scripts/run_ablations.py` + `scripts/wandb_preflight.py` live in `scripts/`
- Flat YAML per variant (Phase 1 D-03 held via D-35): 3 new configs added flat
- Skip-if-exists resume (Phase 2 D-14): extended to per-run `.done` marker (D-31)
- Atomic checkpoint save (Phase 3): `.done` marker uses the same write-temp-rename pattern
- Float32 npy storage (Phase 1 D-06): `eval_scores.npz` uses same dtype convention
- `video_id` as the cross-modal key (Phase 2): drives features, annotations, per-video score export

### Integration points
- **Reads:** `results/<phase3_run>/best_model.pth`, `results/<phase3_run>/config_snapshot.json`, `E:/features/ucf/{skeleton,clip,skeleton_2person,clip_mean}/*.npy`, `E:/i3d-features/i3d-features/{RGB,RGBTest}/*.npy`, `data/annotations/ucf_temporal.txt`, `data/splits/{ucf,xd}_{train,val,test}.txt`
- **Writes:** `results/<run_dir>/eval_metrics.json`, `results/<run_dir>/eval_scores.npz`, `results/<run_dir>/per_category.csv`, `results/<run_dir>/.done`, `results/results-index.csv` (append-only), `runner-errors.log`, new caches `E:/features/ucf/skeleton_2person/`, `E:/features/ucf/clip_mean/`
- **Phase 5 TTA will consume:** `results/ucf_gated_fusion_s42/best_model.pth` as the adaptation base; iterates LN-affine parameters via `model.named_modules()` (Phase 3 D-07 named LayerNorms)
- **Phase 4b will consume:** all Phase 4 code paths unchanged; swaps UCF splits/annotations for XD when XD features land
- **Phase 6 visualization will consume:** `eval_scores.npz` per-video frame arrays (no re-inference)

</code_context>

<specifics>
## Specific Ideas

- XD skeleton+CLIP extraction is "running elsewhere" per user — Phase 4 does not own or monitor it. Phase 4b is gated on features appearing in `E:/features/xd/`.
- The scope shift of "RTFM on XD instead of UCF" is a defensible thesis narrative: the XD I3D features were released by the XD-Violence authors (Wu et al. 2020) and are the same feature set MGFN/VadCLIP benchmark on; reproducing MGFN/RTFM's published AP on this cache is a valid harness gate.
- The 4–5 LayerNorm layers in Gated Fusion (Phase 3 D-07) must be preserved across `best_model.pth` → Phase 5 TTA handoff. Phase 4 does NOT touch those modules; it loads them via `build_model(**cfg["model"])` and runs inference only.
- `eval_scores.npz` key format: `{video_id: np.ndarray shape (n_frames,)}` where `n_frames` is at original 30fps granularity per D-14.
- Bit-identical reproducibility (Phase 3 SC #4) carries into Phase 4: re-running `evaluate.py` on the same `best_model.pth` must produce the same `eval_metrics.json` byte-for-byte (deterministic eval path, no stochastic ops).
- `config_hash` implementation: `hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()` — whitespace-insensitive, reorder-stable.
- `git_sha` via `subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)` plus a `git diff --quiet` check for dirty-tree suffix.
- The 5-crop I3D training protocol (D-19) effectively multiplies training data by 5× vs MIL bag paired against normal crops — may need to scale `k_topk` (Phase 3 D-01) or keep at 3; plan decision.
- `run_ablations.py` execution order: start with RTFM I3D gate (D-18). If it fails the AP threshold, halt — the harness is broken and all downstream ablations would be unreliable.
- SkeletonProj must accept `skel_dim` as a YAML override (256 default; 512 for D-22 concat ablation). Existing Phase 3 gated_fusion YAML already plumbs `skel_dim` — verify the override path works end-to-end.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 4b (XD-Violence main results):** 6 variants × XD + 2 pooling ablations × XD + 3-seed Gated × XD + per-category XD — activated when XD skeleton+CLIP features complete. Planner must add Phase 4b to ROADMAP.md as part of Phase 4 planning deliverables.
- **UCF-Crime RTFM reproduction:** original PRD gate target. Requires downloading UCF I3D features separately (not on disk). Phase 4b scope OR optional supplement if Phase 4 delivers ahead of schedule.
- **Multi-person `max` and `mean` aggregation ablations (vs the chosen `concat`):** optional extra runs if Phase 4 has slack; otherwise documented in thesis as "we chose concat per PYSKL/PRD §12.3 convention".
- **`last_model.pth` sanity eval:** optional one-off comparison after main results land; not required for the thesis tables.
- **Flow I3D stream inclusion for RTFM** (D-05 excluded): revisit if RGB-only AP misses the gate.
- **UCF PNG-granularity AUC as secondary number:** D-14 chose 30fps primary; PNG-granularity is easy to add if a reviewer asks for it.
- **CLIP sampling rate ablation (OPT-07):** 1 FPS vs 2 FPS vs 4 FPS — Phase 6 if time.
- **Gating weight distribution histogram (OPT-10):** Phase 6 analysis.
- **t-SNE / UMAP embedding visualization (OPT-09):** Phase 6 analysis.
- **Cross-dataset TTA (OPT-03):** Phase 5 scope (TTA infrastructure).
- **RWF-2000 supplementary validation (OPT-08):** out of v1 scope.
- **YOLO-World third modality (OPT-01):** v2.
- **wandb sweep-config orchestration:** fallback if per-run tags turn out to be hard to slice in the wandb UI; default is D-41 tags-per-run.

### Reviewed Todos (not folded)
None — no pending todos matched Phase 4.

</deferred>

---

*Phase: 04-baseline-evaluation-main-results*
*Context gathered: 2026-04-15*
