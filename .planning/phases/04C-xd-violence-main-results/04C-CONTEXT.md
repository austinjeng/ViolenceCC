# Phase 4c: XD-Violence Main Results - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Reproduce the complete Phase 4 ablation table on XD-Violence: 4 main variants (skeleton_only, clip_only, late_fusion, gated_fusion) + 2 pooling ablations (2-person skeleton concat, CLIP mean-only) + 3-seed Gated Fusion stability + per-category breakdown across all 6 XD anomaly types. Uses the dataset-portable Phase 4 code (evaluate.py, run_ablations.py, model registry) with 6 new XD-specific YAML configs. Relocated from the original Phase 4b scope per D-01 of 04b-CONTEXT.md.

</domain>

<decisions>
## Implementation Decisions

### Config strategy
- **D-01:** Create **6 new flat self-contained XD YAML configs** matching the Phase 1 D-03 / Phase 4 D-35 convention: `skeleton_only_xd.yaml`, `clip_only_xd.yaml`, `late_fusion_xd.yaml`, `gated_fusion_xd.yaml`, `gated_fusion_xd_2person.yaml`, `gated_fusion_xd_clip_mean.yaml`. Each is a copy of its UCF counterpart with `dataset: xd`, `paths.skeleton_features: "E:/features/xd/skeleton"`, `paths.clip_features: "E:/features/xd/clip"` (or `skeleton_2person`/`clip_mean` for pooling variants), and `paths.annotations: "data/annotations/xd_temporal.txt"` swapped. ~80% content duplicated but self-contained and greppable. 14 total configs after Phase 4c.

### Execution ordering
- **D-02:** **3-wave execution** with main results first:
  - **Wave 1 (immediate, ~2-3h GPU):** Create XD configs + register 3 new queues in `run_ablations.py`. Run `phase4c_main` (4 XD variants at seed=42) and `phase4c_seeds` (Gated Fusion seeds 123, 2024) on existing 4752 features at `E:/features/xd/{skeleton,clip}/`. Gets the thesis-critical Gated Fusion AP number ASAP.
  - **Wave 2 (user-executed, parallel with Wave 1 completion):** User runs re-extraction in separate terminals: `extract_ctrgcn.py --keep-persons --dataset xd` in `vcc-ctrgcn` env → `E:/features/xd/skeleton_2person/`; `extract_clip.py --pool mean --dataset xd` in `vcc-skeleton` env → `E:/features/xd/clip_mean/`.
  - **Wave 3 (after re-extraction lands):** Run `phase4c_pooling` (2 ablations: gated_fusion_xd_2person, gated_fusion_xd_clip_mean at seed=42).

### Per-category scope
- **D-03:** Compute per-category AP/AUC for **all 6 XD-Violence anomaly categories** (Fighting, Shooting, Riot, Abuse, Car Accident, Explosion) in `per_category.csv`. Thesis narrative highlights Fighting/Abuse/Riot as the violence-specific subset per SC #4 and compares their AP against the full test-set AP. Zero extra compute — `_parse_category()` in `src/eval/xd_annotations.py` already handles all 6.

### Hyperparameter transfer
- **D-04:** XD configs use **identical hyperparameters to UCF** — `lr=1e-4`, `epochs=50`, `batch_size=16`, `patience=10`, `k_topk=3`, `warmup_epochs=5`. Early stopping naturally handles convergence speed on the larger XD train set (~3360 videos vs UCF's ~810). Most defensible thesis narrative: "same hyperparameters across datasets, no per-dataset tuning." Also the fairest ablation comparison.

### Missing video handling
- **D-05:** **Clean split files** — remove the 2 video IDs with no features from `xd_{train,val,test}.txt`: `v=8cTqh9tMz_I__#1_label_A` (corrupt MP4, missing moov atom) and `v=Gm73TwtUyGY__#1_label_G-0-0` (34 frames, below 64-frame window). Add a comment at the top of each affected split file documenting the exclusion. All downstream code (loaders, evaluate.py) works unchanged at 4752/4752 = 100%.

### AP target contingency
- **D-06:** Fallback cascade if Gated Fusion AP < 80%:
  1. **AP >= 80%:** SC #1 PASS.
  2. **AP 70–79%:** MISS-ACCEPTED — document as thesis limitation. Ablation table, 3-seed stability, and per-category breakdown remain valid and valuable. Update SC #1 in ROADMAP to reflect actual AP. Mirrors the Phase 4b RTFM gate MISS-ACCEPTED pattern (04b D-11 fallback-step-4).
  3. **AP < 70%:** INVESTIGATE before accepting — verify data loader correctness, feature alignment, single-modal APs. If diagnosis clean, accept + document.

### Claude's Discretion
- XD annotation path routing in evaluate.py — whether `paths.annotations` is read from YAML or inferred from dataset key
- wandb posture for XD runs — continue with `mode: disabled` (Phase 4 Rule 3 fallback) unless user re-enables
- wandb tags for XD runs (`phase4c`, `xd`, `<variant>`)
- Whether XD pooling configs inherit `skel_agg: concat` from UCF 2person config or use a different aggregation
- Exact queue names if planner prefers different naming than `phase4c_main`/`phase4c_pooling`/`phase4c_seeds`
- `results-index.csv` phase provenance tagging for XD rows

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and specifications
- `.planning/REQUIREMENTS.md` — EVAL-02, EVAL-03, EVAL-04, EVAL-05 (XD-side completion; UCF-side already complete in Phase 4)
- `thesis_prd_v2.3.md` §12 — Evaluation protocol, required ablation list, 3-seed stability protocol
- `thesis_prd_v2.3.md` §12.3 — Multi-person aggregation + CLIP pooling ablation specs

### Prior phase context (direct dependencies)
- `.planning/phases/04-baseline-evaluation-main-results/04-CONTEXT.md` — D-22 (skel_agg=concat), D-23 (CLIP mean-only), D-24 (sibling cache dirs), D-25 (XD re-extraction deferred to 4c), D-26..D-34 (run_ablations.py orchestration contract), D-35 (flat YAML convention), D-27/D-28 (3-seed for Gated only, seeds {42,123,2024}), D-29 (pooling ablations at seed=42), D-30 (deterministic run dir naming)
- `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-CONTEXT.md` — D-01 (Phase 4c scope definition), D-03 (filesystem activation criterion), D-10 (Wu annotation parser forward-compatible with _parse_category), D-13 (per-category is Phase 4c deliverable)

### Code artifacts to extend
- `scripts/run_ablations.py` — Add 3 new queues (phase4c_main, phase4c_pooling, phase4c_seeds) with XD RunSpec entries
- `configs/gated_fusion.yaml` — Template for XD config creation (swap dataset + paths)
- `configs/gated_fusion_2person.yaml` + `configs/gated_fusion_clip_mean.yaml` — Templates for XD pooling configs
- `scripts/extract_ctrgcn.py` — `--keep-persons --dataset xd` flag for Wave 2 re-extraction
- `scripts/extract_clip.py` — `--pool mean --dataset xd` flag for Wave 2 re-extraction

### Evaluation infrastructure (reused unchanged)
- `src/evaluate.py` — Frame-level AUC/AP pipeline + per_category.csv writer
- `src/eval/xd_annotations.py` — `parse_xd_annotations()` + `_parse_category()` for all 6 XD categories
- `src/eval/metrics.py` — `compute_frame_metrics()` with per_category dict
- `src/eval/snippet_to_frame.py` — C4-guard snippet→frame expansion
- `src/data/dataset.py` + `src/data/loaders.py` — `dataset: xd` path already implemented

### Pitfalls
- `.planning/research/PITFALLS.md` — C3 (test-set leakage; preserved by existing module boundary), C4 (snippet→frame; enforced by existing assert)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/run_ablations.py` — RunSpec + QUEUES infrastructure, `.done` marker resume, `results-index.csv` append. Needs only 3 new queue definitions + `--queue` choices update.
- `src/evaluate.py` — Full frame-level evaluation pipeline including `_write_per_category_csv`. Works for `dataset: xd` already.
- `src/eval/xd_annotations.py::_parse_category()` — Parses all 6 XD category codes (B1–B6). Forward-compatible from Phase 4b D-10.
- `src/data/dataset.py::MILFeatureDataset` — Already handles `dataset="xd"` at line 118.
- `src/data/loaders.py::build_dataloaders` — Already handles `dataset="xd"` split file routing.
- `scripts/extract_ctrgcn.py --keep-persons` — Tested on UCF; produces `[N, 2, 256]` to `skeleton_2person/`.
- `scripts/extract_clip.py --pool mean` — Tested on UCF; produces `[N, 512]` to `clip_mean/`.
- All 8 existing UCF+I3D configs — Templates for the 6 new XD configs.

### Established Patterns
- Flat self-contained YAML per variant (Phase 1 D-03, Phase 4 D-35) — XD configs follow identical convention
- Deterministic run dir naming: `results/xd_<variant>[_<cache>]_s<seed>/` (Phase 4 D-30)
- `.done` marker for filesystem-probe resume (Phase 4 D-31)
- Append-only `results/results-index.csv` audit log (Phase 4 D-33)
- 3-seed protocol: Gated Fusion only, seeds {42, 123, 2024} (Phase 4 D-27/D-28)
- Early stopping with patience=10 (Phase 3 D-15)

### Integration Points
- **Reads:** `E:/features/xd/{skeleton,clip}/*.npy` (4752 files each), `E:/features/xd/{skeleton_2person,clip_mean}/*.npy` (after Wave 2), `data/splits/xd_{train,val,test}.txt` (cleaned per D-05), `data/annotations/xd_temporal.txt` (Phase 4b)
- **Writes:** `results/xd_<variant>_s<seed>/` (8 run dirs total: 4 main + 2 seeds + 2 pooling), `results/results-index.csv` (8 appended rows), 6 new config files in `configs/`
- **Phase 5 consumes:** Phase 4c does not modify the TTA adaptation base (`results/ucf_gated_fusion_s42/best_model.pth`); no cross-phase interference
- **Phase 6 consumes:** `eval_scores.npz` per-video frame arrays from each XD run dir for temporal visualization

</code_context>

<specifics>
## Specific Ideas

- Feature count 4752/4752 after D-05 split cleaning = 100% coverage. The 2 exclusions (corrupt MP4 + sub-64-frame) are documented in split file comments and affect neither training nor evaluation.
- XD train/val/test split sizes: 3360/594/800 (from Phase 2 split files). With 4x the training data vs UCF, early stopping should trigger sooner — expect convergence in ~20-30 epochs vs UCF's ~40.
- All 8 run dirs follow the D-30 deterministic naming: `xd_skeleton_only_s42`, `xd_clip_only_s42`, `xd_late_fusion_s42`, `xd_gated_fusion_s42`, `xd_gated_fusion_s123`, `xd_gated_fusion_s2024`, `xd_gated_fusion_2person_s42`, `xd_gated_fusion_clip_mean_s42`.
- The per-category CSV will have 6 rows per Gated Fusion run (Fighting, Shooting, Riot, Abuse, Car Accident, Explosion). Thesis Table X.Y highlights Violence = {Fighting, Abuse, Riot} subset AP vs full test-set AP.
- Wave 2 re-extraction wall-clock estimate: skeleton `--keep-persons` on 4752 videos ≈ 2-4 hours in `vcc-ctrgcn`; CLIP `--pool mean` on 4752 videos ≈ 1-2 hours in `vcc-skeleton`. Both can run in parallel on separate GPU sessions.
- The `wandb: mode: disabled` posture carries forward from Phase 4. CSV logger remains thesis source of truth.

</specifics>

<deferred>
## Deferred Ideas

- **Multi-person `max` and `mean` aggregation ablations** (vs chosen `concat`) — optional extra runs if Phase 4c has slack. Documented in thesis as "we chose concat per PYSKL/PRD §12.3 convention."
- **XD-specific hyperparameter tuning** (lr sweep, batch_size adjustment) — only if D-06 AP < 70% investigation suggests hyperparameter mismatch as root cause.
- **wandb re-enablement for XD runs** — low priority; CSV logger is sufficient.
- **Cross-dataset transfer experiment** (train on UCF, test on XD or vice versa) — Phase 5/6 scope if time permits.

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04C-xd-violence-main-results*
*Context gathered: 2026-04-26*
