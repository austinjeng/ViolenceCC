# Phase 4b: RTFM XD-I3D Gate + xd_i3d Training Dispatch - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4b delivers the RTFM XD-I3D evaluation-harness gate rescoped from Phase 4 per the 2026-04-15 Option B decision (`04-06-UAT.md`). Concretely: implement the missing xd_i3d training dispatch (`build_dataloaders_i3d`, `train_one_epoch_i3d`, `validate_i3d`), wire the Wu et al. XD-Violence frame-level test annotations into `src/evaluate.py::_build_frame_arrays` (replacing the all-zero stub at lines 180-192), and re-run `scripts/run_ablations.py --queue rtfm_gate` to produce a results-index.csv row with AP ≥ 0.7681 (77.81% ± 1% per D-03). Closes EVAL-01.

**Scope-narrowing decision (D-01 below):** The original Phase 4b scope as written in ROADMAP.md bundled the RTFM gate with XD-Violence main results (6 variants + 2 pooling ablations + 3-seed Gated + per-category Fighting/Abuse/Riot). Given XD skeleton+CLIP extraction is at 3/3360 train files (0.07% of the ≥4500 activation criterion) with no observed progress since 2026-04-08, Phase 4b is narrowed to RTFM gate only. A new Phase 4c (XD-Violence Main Results) carries EVAL-02..EVAL-05 XD-side completion, activated by a filesystem probe when XD features land. The planner MUST apply this ROADMAP.md split as part of Phase 4b planning.

Phase 5 (TTA) runs in parallel with Phase 4b per D-02; no cross-phase blocker.

</domain>

<decisions>
## Implementation Decisions

### Phase scope and sequencing
- **D-01:** Split original Phase 4b into **Phase 4b (RTFM XD-I3D gate only)** and **Phase 4c (XD-Violence Main Results)**. Phase 4b owns: (a) xd_i3d training dispatch implementation, (b) Wu et al. XD annotation parser, (c) `src/evaluate.py::_build_frame_arrays` xd_i3d path rewrite, (d) rtfm_gate queue rerun + AP ≥ 0.7681 validation. Phase 4c owns the previously-bundled "Deferred from Phase 4" subsection (XD main variants, pooling re-extractions, XD pooling YAMLs, `phase4c_main`/`phase4c_pooling`/`phase4c_seeds` queues, per-category Fighting+Abuse+Riot breakdown). The planner applies the ROADMAP.md edit as part of Phase 4b's plan: rename Phase 4b title to "RTFM XD-I3D Gate", insert new Phase 4c detail block with the "Deferred from Phase 4" content relocated, and update the Progress Table. REQUIREMENTS.md annotation: EVAL-01 remains Phase 4b; EVAL-02..EVAL-05 XD-side annotations flip from "Phase 4b" to "Phase 4c".
- **D-02:** Phase 5 (TTA) runs in parallel with Phase 4b. Phase 5's canonical adaptation base is `results/ucf_gated_fusion_s42/best_model.pth` (Phase 4 D-10, bit-identical-rerun verified in 04-06 UAT). RTFM gate PASS/FAIL does NOT block Phase 5 — the gate validates the XD-I3D evaluation harness, not Phase 5's UCF-trained adaptation base. Phase 5 can start independently from any `/gsd-plan-phase 5` invocation.
- **D-03:** Phase 4c activation trigger = filesystem probe `ls -1 E:/features/xd/skeleton/*.npy | wc -l >= 4500 && ls -1 E:/features/xd/clip/*.npy | wc -l >= 4500`. Checked at each `/gsd-progress` invocation; when both counts pass, the user triggers `/gsd-plan-phase 4c`. No polling infrastructure needed. Matches the activation-criterion wording already in the ROADMAP Phase 4b detail block; Phase 4c inherits it verbatim.

### xd_i3d training dispatch architecture
- **D-04:** **Parallel functions, not polymorphic dispatch.** Add `build_dataloaders_i3d(cfg) -> ((nor_loader, abn_loader), val_loader)` in `src/data/loaders.py` alongside existing `build_dataloaders()`. Add `train_one_epoch_i3d(model, nor_loader, abn_loader, optimizer, device, train_cfg) -> float` and `validate_i3d(model, val_loader, device, train_cfg) -> float` in `src/train.py` alongside existing `train_one_epoch` / `validate`. In `src/train.py::main()`, branch once at the top after `cfg = load_config(...)`: `if cfg['dataset'] == 'xd_i3d': (nor, abn), val = build_dataloaders_i3d(cfg); for epoch: ... train_one_epoch_i3d(...); validate_i3d(...)`. ~60 lines of duplication is acceptable — preserves the D-07/D-08 test-leakage module-boundary discipline established in Phase 4 and keeps the fusion and i3d contracts decoupled.
- **D-05:** 5-crop training bag materialization = **crop-as-sample collate**. `src/data/i3d_dataset.py::I3DFeatureDataset` already returns `{"i3d": [5, T, 1024], "label": float, "video_id": str}` at train/val mode (D-19). `build_dataloaders_i3d` uses a custom collate function (`collate_i3d_train`) that flattens the 5-crop dim into the batch dim before yielding: given a DataLoader batch of B videos × [5, T, 1024], yield `i3d: [B*5, T, 1024]` + `label: [B*5]` + `video_id: [B*5]`. With `data.batch_size=3` in `configs/rtfm_i3d.yaml`, effective MIL bag size = 15, matching `train.k_topk=3` per Pitfall 3 (`rtfm_i3d.yaml` comment line 22-25). For val/test, the existing crop-averaged `[N, 1024]` path from `I3DFeatureDataset.__getitem__` mode=test is reused unchanged.
- **D-06:** MIL bag labels for xd_i3d derived from the **`_label_A` suffix convention** — `label = 0 if vid.endswith("_label_A") else 1`. Same logic as `src/data/i3d_dataset.py::__getitem__` (already implemented) and `src/data/dataset.py::_parse_label_xd`. `build_dataloaders_i3d` reuses the existing split-into-nor_idx/abn_idx pattern from `src/data/loaders.py:123-126` (enumerate `train_full.video_ids`, partition by `label_A` suffix). No new label source; the Wu annotation file (D-07) is used only by evaluate.py for frame-level test labels, not by the training MIL bags.

### Wu et al. XD annotation pipeline
- **D-07:** Annotation source = **official Wu et al. 2020 release `annotations.txt`**, committed to `data/annotations/xd_temporal.txt`. Matches Phase 4 D-04 pattern (git-tracked, small file, fresh-clones work without separate download). Canonical source is the XD-Violence project page (roseyu.com/XD-Violence) — phase-researcher confirms the exact URL and any redirects during the research step. Expected format: one line per test video, `video_id start1 end1 start2 end2 ...` (multi-interval, frame indices in the original 24fps video). Test-set only — XD-Violence uses weakly supervised MIL during training, so no frame labels exist for train/val splits.
- **D-08:** Snippet→frame expansion contract for xd_i3d in `src/evaluate.py::_build_frame_arrays` = **16-frame I3D snippet window × 24fps master grid**. `n_frames = len(scores) * 16` at 24fps; `snippet_to_frame(scores, n_frames=n_frames, snippet_window=16, upsample_factor=1)`. This replaces the existing all-zero-label stub at `src/evaluate.py:180-192`. **Phase-researcher must confirm** the exact I3D feature extraction stride used by the Wu 2020 release vs. the annotation fps before the planner locks these numbers in the task breakdown — if the cache was extracted at a different stride (e.g., 32-frame or 24-frame), `snippet_window` adjusts accordingly. The current `snippet_window=16` / `upsample_factor=1` stub in evaluate.py matches the best-guess from research-time evidence and is consistent with MGFN/RTFM published XD evaluation conventions.
- **D-09:** C4 guard enforcement for xd_i3d = **hard `assert len(frame_scores) == len(frame_labels)` before every `sklearn.metrics` call**, mirroring UCF (Phase 4 D-15, implemented in `src/eval/snippet_to_frame.py`). A mismatch — e.g., `n_snippets*16` ≠ annotation-implied frame count — raises loudly rather than silently passing a wrong AP. The existing `src/eval/metrics.py` `compute_frame_metrics()` helper already enforces this for UCF; xd_i3d routes through the same helper, so the guard propagates for free.
- **D-10:** Wu annotation parser = **forward-compatible, module-level** `src/eval/xd_annotations.py`, mirroring the `src/eval/ucf_annotations.py` pattern (`parse_annotations(path) -> Dict[str, VideoAnnotation]` + `frame_labels(anno, n_frames) -> np.ndarray`). Returns a `VideoAnnotation`-like struct with `(video_id, intervals, category)`. `src/evaluate.py::_build_frame_arrays` imports `parse_xd_annotations` + `xd_frame_labels` and uses them for both xd_i3d (now, Phase 4b) and xd (Phase 4c fusion runs later). Writing it dual-use in Phase 4b avoids a file-move refactor in Phase 4c. Category parsing handles multi-label `_label_B1-B4-G-0` suffixes for Phase 4c SC #5 (Fighting/Abuse/Riot breakdown) — but the category output is NOT surfaced in Phase 4b per D-13; only the parser knows how.

### RTFM gate fallback strategy
- **D-11:** If the rerun AP < 76.81% after dispatch + annotation fixes are in, fallback cascade (try in order): (1) **Relax anchor to MGFN 80.11% only if miss is < 3pp** (AP ∈ [73%, 77%]) — document in SUMMARY as "within RTFM/MGFN published band; MGFN anchor applied." The MGFN 80.11% upper anchor is flagged in `rtfm_i3d.yaml` line 49 as "possibly VideoSwin; not vanilla I3D" and is a loose upper bound — accept only if modest miss. (2) **Add RGB+Flow I3D stream** (D-05 Phase 4 contingency) — `E:/i3d-features/i3d-features/{Flow,FlowTest}/` exist on disk; add a new variant `rtfm_i3d_rgbflow` + new config + concat-or-sum loader change. Expected ~1-2pp AP lift. (3) **Add MTN temporal module to `src/models/rtfm_i3d.py`** — current MVP is FM head + MIL head only; MTN is the third RTFM architecture piece (dilated conv + non-local block). Heavier engineering lift (~150 lines, breaks D-07 LN-naming simplicity unless carefully done). Only if (1) and (2) both fail. (4) **Accept miss + document as thesis limitation** — final fallback; mirrors Phase 4 EVAL-02 MISS-accepted pattern. Escalate through cascade linearly; do not skip steps unless a gate diagnosis step (D-12) rules out a category.
- **D-12:** Before concluding "dispatch is correct; gate miss is modeling", perform **three orthogonal diagnostic checks**: (1) **Bit-identical rerun consistency** — run `run_ablations.py --queue rtfm_gate` twice with `rm -r results/xd_i3d_rtfm_i3d_s42 && rm results-index.csv-equivalent row` between; all 9 numeric keys in `eval_metrics.json` must match (same invariant Phase 4 verified for UCF Gated Fusion). (2) **C4 sanity** — `snippet_auc` vs `auc` delta < 2pp (large gap indicates snippet→frame expansion bug — same failure mode Phase 4 D-15 explicitly mitigates). (3) **Train-time 5-crop bag-size audit** — add a one-shot log in `train_one_epoch_i3d` first 3 epochs that prints `n_normal, n_abnormal, tensor_shape` per step; assert `n_normal == n_abnormal == batch_size * 5` (= 15 with `batch_size=3`). If all three pass AND AP < 76.81%, it's a modeling issue → trigger D-11 fallback cascade. If any fails, it's a dispatch bug → fix in place before invoking fallbacks.
- **D-13:** **No per-category breakdown for RTFM variant.** Scope = headline AP only (SC #1 owner). Per-category reporting (Fighting/Abuse/Riot) validates the *fusion model's* violence-specific signal and is a Phase 4c Gated Fusion deliverable (SC #5). Keeps Phase 4b scope tight: one number, one gate. The Wu annotation parser (D-10) has category-parsing logic for Phase 4c's benefit, but Phase 4b's `per_category.csv` output for the rtfm variant is intentionally empty or single-row "overall" — planner decides final shape.

### Evaluation harness hygiene
- **D-14:** wandb posture = **keep Rule 3 fallback**. `configs/rtfm_i3d.yaml` already has `wandb.mode: disabled` (line 41-43, comment cites Plan 04-06 auth gate). Continue invoking `run_ablations.py --queue rtfm_gate --no-preflight`. CSV logger (`src/utils/csv_logger.py`) remains thesis source of truth per Phase 3 D-13. Zero new work; consistent with Phase 4 Tasks 2/3/4/5 execution pattern.
- **D-15:** **Keep `rtfm_gate` queue name as-is** in `scripts/run_ablations.py::QUEUES`. Existing RunSpec at line 84 (`RunSpec("xd_i3d", "rtfm_i3d", 42, "configs/rtfm_i3d.yaml")`) is correct and reusable unchanged. No rename to `phase4b_rtfm_gate`. The results-index.csv row provides phase provenance via `run_name=xd_i3d_rtfm_i3d_s42`. wandb tag `phase4` (line 43 of rtfm_i3d.yaml) is historical; not worth churning since wandb is disabled anyway.
- **D-16:** Execute a **1-epoch empirical smoke test before the full rtfm_gate queue run**. Command: `python -m src.train --config configs/rtfm_i3d.yaml --epochs 1 --run-name smoke_xd_i3d_rtfm_i3d_s42` using `src/train.py:39`'s existing `--epochs` override. Smoke validates the full dispatch chain (build_dataloaders_i3d → collate → train_one_epoch_i3d → validate_i3d → save_checkpoint_atomic) runs end-to-end without shape/dim errors on real E:/i3d-features data. Delete `results/smoke_xd_i3d_rtfm_i3d_s42/` after smoke passes. Total compute: ~20-60 seconds wall-clock. The full rtfm_gate queue run follows only if smoke passes.

### Test coverage
- **D-17:** Test coverage for new xd_i3d dispatch surfaces = **pytest unit tests + 1-epoch empirical smoke (D-16)**. Unit test targets (new files under `tests/`):
  - `tests/test_loaders_i3d.py` — `build_dataloaders_i3d` returns the right Loader tuple; `collate_i3d_train` flattens `[B, 5, T, 1024]` → `[B*5, T, 1024]` + asserts shape at a fixed B; normal/abnormal subset partitioning is correct for both label classes (build tiny mock XD split file with 4 normal + 4 abnormal video IDs).
  - `tests/test_train_i3d.py` — `train_one_epoch_i3d` runs one step on a tiny mock dataset + asserts loss is finite; `validate_i3d` signature matches `validate` contract.
  - `tests/test_xd_annotations.py` — `parse_xd_annotations` handles the official format, including multi-interval videos (`v1 10 50 100 150`); empty-interval (normal) videos; `xd_frame_labels` produces correct `[n_frames]` binary vectors including the off-by-one boundary conditions matching Phase 4 D-16 UCF convention (frame `start <= i < end` is 1, else 0).
  - `tests/test_evaluate_xd_i3d.py` — `_build_frame_arrays(cfg={dataset:'xd_i3d'}, per_video_snippet_scores={...})` returns correctly-shaped frame_scores/frame_labels with the C4 guard (D-09) tripping on synthetic length mismatch.
- **D-18:** Plan shape = **one PLAN.md with ~5-6 atomic commits** matching Phase 4 plan atomicity (each Task in 04-0N-PLAN.md = 1-2 commits): (1) Wu annotation parser module + `data/annotations/xd_temporal.txt`, (2) `build_dataloaders_i3d` + `collate_i3d_train`, (3) `train_one_epoch_i3d` + `validate_i3d` + `main()` dispatch branch, (4) `src/evaluate.py::_build_frame_arrays` xd_i3d rewrite, (5) unit test suite, (6) empirical smoke (D-16) + full rtfm_gate run + SUMMARY. Planner may split or merge based on dependency analysis; this is the anticipated shape, not a hard contract.

### Claude's Discretion
- Exact URL for the Wu 2020 official release annotations (phase-researcher confirms during research step)
- Exact I3D stride vs. Wu annotation fps numbers if they differ from D-08 defaults (phase-researcher confirms; planner updates `snippet_window` / `upsample_factor` accordingly)
- `collate_i3d_train` implementation detail (custom function using `torch.utils.data.default_collate` + reshape vs. fully hand-rolled `torch.stack` chain)
- Whether the D-12 5-crop bag-size audit is a one-shot log during the first 3 epochs (preferred) or an always-on assertion (safer but noisier)
- `per_category.csv` row shape for the rtfm variant under D-13 — empty file, single "overall" row, or skipped entirely
- Unit test mocking strategy for I3DFeatureDataset — use real tiny slices of E:/i3d-features/i3d-features/RGB/ (integration-ish) vs. synthetic numpy arrays (pure unit)
- Whether `parse_xd_annotations` returns `VideoAnnotation` (namedtuple) directly or a typed dict — match UCF pattern (`src/eval/ucf_annotations.py::VideoAnnotation`) is the default
- `rtfm_i3d.yaml` `data.batch_size` raise from 3 → 16 (config line 22-25 comment): empirical decision after the gate passes at batch_size=3; NOT a Phase 4b deliverable unless modeling-issue diagnosis (D-12) identifies bag-size inflation as the fix
- Queue provenance fix: after Phase 4b closes, historical phase4 tags in rtfm_i3d.yaml `wandb.tags` can be updated to `phase4b` for clarity; low priority since wandb is disabled

### Folded Todos
None — no pending todos matched Phase 4b per `gsd-tools todo match-phase 4b`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and specifications
- `.planning/REQUIREMENTS.md` — EVAL-01 (rescoped from Phase 4 per 2026-04-15 Option B); note the v1 deferral annotation already in place (line 50)
- `thesis_prd_v2.3.md` §12 — Evaluation protocol + RTFM baseline reproduction gate requirement (anchor: 77.81% XD-I3D per Phase 4 D-03)
- `thesis_prd_v2.3.md` §10.3 — TTA adaptation protocol (Phase 5 handoff unchanged; Phase 4b must preserve D-07 LN naming in rtfm_i3d model, already implemented as `self.ln_i3d`)

### Prior phase context
- `.planning/phases/04-baseline-evaluation-main-results/04-CONTEXT.md` — D-01 (UCF-only Phase 4), D-02 (XD out-of-band), D-03 (RTFM anchor retargeted to XD-I3D with ±1% of 77.81% gate), D-05 (RGB-only I3D stream; Phase 4b fallback only if gate misses), D-07 (named LN for TTA handoff), D-10 (best_model.pth only; no last_model eval), D-18 (`rtfm_i3d` MODEL_REGISTRY key), D-19 (5-crop train / crop-averaged test), D-20 (`paths.i3d_features` YAML key), D-26..D-34 (run_ablations.py orchestration contract), D-36 (originally claimed xd_i3d training dispatch — FALSIFIED by Plan 04-06 Task 2; Phase 4b is the remediation)
- `.planning/phases/04-baseline-evaluation-main-results/04-06-UAT.md` §"EVAL-01 (RTFM XD-I3D) Gate — BLOCKED by Architectural Gap" — the Rule 4 diagnosis that enumerates the five named prerequisites Phase 4b must deliver (build_dataloaders_i3d, train_one_epoch_i3d, validate_i3d, Wu et al. parser, rerun with AP ≥ 0.7681)
- `.planning/phases/04-baseline-evaluation-main-results/04-06-UAT.md` §"DECISION (2026-04-15): Option B" — the researcher decision that authorized Phase 4b's expanded scope; Phase 4b inherits this decision verbatim
- `.planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md` — Phase 4 closeout + Phase 4b expansion wording; ROADMAP.md edits Phase 4b planning must apply
- `.planning/phases/03-model-architecture-training-infrastructure/03-CONTEXT.md` — D-01 (k_topk=3), D-07 (named LN for TTA), D-15 (best/last checkpoint policy; rtfm_i3d obeys D-10 "best only")

### Pitfalls and methodology
- `.planning/research/PITFALLS.md` — Pitfall 3 (5-crop inflation vs k_topk=3 ratio — drives `configs/rtfm_i3d.yaml:22` batch_size=3 and D-05 crop-as-sample collate); Pitfall 4 (XD I3D missing-crops filter — already implemented in `src/data/i3d_dataset.py::_has_at_least_one_crop`); C3 (test-set leakage — preserved by the D-04 parallel-functions dispatch keeping the i3d training path out of the eval-only module boundary); C4 (snippet→frame off-by-one — enforced by D-09 hard assert + reused `src/eval/snippet_to_frame.py` utility)
- `.planning/research/ARCHITECTURE.md` — Component 7 (Evaluation Engine) frame-level broadcast spec
- `.planning/research/SUMMARY.md` — Key insight #3 (RTFM reproduction gating as cross-implementation sanity check)

### Reference implementations
- RTFM repo: https://github.com/tianyu0207/RTFM — FM head reference, 10-crop averaging convention (we adapt to XD's 5-crop per D-19), published XD-I3D AP ≈ 77.81% (primary gate anchor)
- MGFN repo: https://github.com/carolchenyx/MGFN — published XD I3D AP ≈ 80.11% (secondary/fallback anchor per D-11)
- VadCLIP repo: https://github.com/nwpu-zxr/VadCLIP — XD annotation parsing reference implementation

### External data sources
- XD-Violence project page: https://roseyu.com/XD-Violence/ — Wu et al. 2020 `annotations.txt` source (phase-researcher confirms exact download URL; commit to `data/annotations/xd_temporal.txt` per D-07)

### Project state
- `.planning/STATE.md` — current position: Phase 4 closed; Phase 4b ready to plan
- `.planning/ROADMAP.md` Phase 4b detail block (lines 95-117) — source of scope; Phase 4b planning will split this block per D-01 into a narrowed Phase 4b + new Phase 4c
- Feature directories verified on disk: `E:/i3d-features/i3d-features/RGB/` = 16124 files (~3225 videos × 5 crops); `E:/i3d-features/i3d-features/RGBTest/` = 4000 files (800 videos × 5 crops, matches `data/splits/xd_test.txt` exactly); `E:/features/xd/skeleton/` = 3 files (Phase 4c blocked); `E:/features/xd/clip/` = 3 files (Phase 4c blocked)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets (unchanged in Phase 4b)
- `src/data/i3d_dataset.py::I3DFeatureDataset` — Pitfall 4 filter, 5-crop load, resample_T, train/val returns `[5, T, 1024]`, test returns crop-averaged `[N, 1024]`. Fully D-19 compliant; no changes needed.
- `src/models/rtfm_i3d.py::RTFMI3D` — MVP FM head (L2 norm in MILHead) + MILHead; `self.ln_i3d` named LayerNorm preserved for Phase 5 TTA handoff. No MTN by default (D-11 fallback only if gate + Flow both miss).
- `configs/rtfm_i3d.yaml` — structurally complete: `dataset=xd_i3d`, `model.variant=rtfm_i3d`, `data.batch_size=3` (Pitfall 3), `wandb.mode=disabled` (D-14), `paths.i3d_features=E:/i3d-features/i3d-features`. No edits unless D-11 fallback triggers.
- `scripts/run_ablations.py::QUEUES["rtfm_gate"]` — RunSpec at line 84 is correct and reusable unchanged (D-15).
- `src/eval/ucf_annotations.py` — pattern template for new `src/eval/xd_annotations.py` (parse_annotations, frame_labels, VideoAnnotation namedtuple).
- `src/eval/snippet_to_frame.py` + `src/eval/metrics.py` — C4-guard and frame-broadcast utility; reused by xd_i3d path unchanged.
- `src/utils/csv_logger.py::results_index_append` — one-line append to `results/results-index.csv`; run_ablations.py already calls it per-run.
- `src/utils/checkpoint.py::save_checkpoint_atomic` — atomic best_model.pth save pattern.
- `src/utils/seed.py::set_deterministic` + `seed_worker` + `make_generator` — unchanged; reused by build_dataloaders_i3d.
- `tests/conftest.py` — fixture patterns (splits_dir, eval_run_dir) for the new test files (D-17).

### Files requiring modification
- `src/data/loaders.py` — ADD `build_dataloaders_i3d(cfg)` alongside existing `build_dataloaders(cfg)`. Custom `collate_i3d_train` also lives here (or in a sibling module `src/data/collate.py` — planner's call). The existing `build_dataloaders` is unchanged to preserve UCF behavior for Phase 5 TTA and Phase 4c fusion runs.
- `src/train.py` — ADD `train_one_epoch_i3d(...)` + `validate_i3d(...)` alongside existing. ADD dispatch branch in `main()` after `cfg = apply_cli_overrides(cfg, args)`: `if cfg['dataset'] == 'xd_i3d': build_dataloaders_i3d / train_one_epoch_i3d / validate_i3d; else: existing path`. The existing path untouched.
- `src/evaluate.py::_build_frame_arrays` — REWRITE xd_i3d branch at lines 180-192. Replace the all-zero `labels_map[vid] = np.zeros(...)` and the coarse `cats_map = "Normal" | "Abuse"` stub with: (a) `parse_xd_annotations(...)` call loading `data/annotations/xd_temporal.txt`, (b) `xd_frame_labels(anno, n_frames)` per video, (c) proper category parsing from video_id suffix for forward-compat with Phase 4c (category result not surfaced in Phase 4b per D-13).

### Files to create
- `src/eval/xd_annotations.py` — mirror of `src/eval/ucf_annotations.py` (D-10).
- `data/annotations/xd_temporal.txt` — Wu 2020 annotations (D-07, downloaded).
- `tests/test_loaders_i3d.py`, `tests/test_train_i3d.py`, `tests/test_xd_annotations.py`, `tests/test_evaluate_xd_i3d.py` — D-17 pytest unit suite.

### Established patterns preserved
- Scripts-vs-src split (Phase 1 D-02) — xd_i3d dispatch code lives under `src/`, smoke/gate execution under `scripts/` via `run_ablations.py`.
- Flat YAML per variant (Phase 1 D-03, D-35) — rtfm_i3d.yaml already flat; no new YAMLs in Phase 4b.
- Atomic `.done` marker (Phase 4 D-31) — run_ablations.py already writes `results/xd_i3d_rtfm_i3d_s42/.done` post-eval; reused unchanged.
- Append-only results-index.csv (Phase 4 D-33) — one row appended on gate rerun; reused unchanged.
- C3 test-leakage discipline (Phase 4 D-07, D-08) — the parallel-functions dispatch (D-04) keeps i3d training code out of `src/eval/`; the eval path still imports I3DFeatureDataset through `src/eval/test_loader.py:103-112` only at test-split time.
- wandb Rule 3 fallback (Phase 4 Task 3/4/5) — re-applied via D-14; zero new work.

### Integration points
- **Reads:** `E:/i3d-features/i3d-features/{RGB,RGBTest}/*.npy` (16124 + 4000 files verified on disk); `data/splits/xd_{train,val,test}.txt` (3360/594/800); `data/annotations/xd_temporal.txt` (to be committed); `configs/rtfm_i3d.yaml`.
- **Writes:** `results/xd_i3d_rtfm_i3d_s42/{best_model.pth, last_model.pth, config_snapshot.json, eval_metrics.json, eval_scores.npz, per_category.csv, .done, train_log.csv}`; `results/results-index.csv` (appended row); `src/eval/xd_annotations.py` (new); `src/data/loaders.py` (new function added); `src/train.py` (new functions added + main() branch); `src/evaluate.py::_build_frame_arrays` (xd_i3d branch rewritten); `tests/test_*.py` (new files); `data/annotations/xd_temporal.txt` (new committed file).
- **Phase 4c will consume:** `src/eval/xd_annotations.py` (parse_xd_annotations + xd_frame_labels + category parser) unchanged; `data/annotations/xd_temporal.txt` unchanged; `src/evaluate.py::_build_frame_arrays` xd path (for non-i3d xd fusion runs — reuses the same parser). Phase 4c creates `phase4c_main/pooling/seeds` queues, new XD configs, and re-extraction passes; none of those artifacts are in Phase 4b scope.
- **Phase 5 will consume:** unchanged Phase 4 adaptation base (`results/ucf_gated_fusion_s42/best_model.pth`); Phase 4b does not modify this artifact or its dependency graph.

</code_context>

<specifics>
## Specific Ideas

- The primary gate anchor is RTFM 77.81% (±1% → 76.81% as pass threshold, per D-03 verbatim). MGFN 80.11% is an upper anchor, not the gate — only relevant under D-11 fallback (1).
- Existing `rtfm_i3d.yaml:22-24` pins `data.batch_size=3` specifically to preserve `k_topk=3` ratio after 5-crop inflation (Pitfall 3). Raising to 16 is an empirical post-gate decision; not Phase 4b scope.
- `src/evaluate.py::_build_frame_arrays` xd_i3d branch currently at lines 180-192. The shape math (`snippet_window=16`, `upsample_factor=1`) is already correct per D-08; only the `labels_map` zero-stub and the simplistic `cats_map` binary need rewriting.
- The MIL bag pairing for xd_i3d has enough signal on XD — `data/splits/xd_train.txt` has 1741/3360 = 52% normal videos (label_A) — balanced enough that build_dataloaders_i3d's nor/abn partitioning produces non-empty subsets. `I3DFeatureDataset.__init__` already emits a warn-on-stderr guard if filtering collapses a class (lines 74-90).
- The 5-crop train-time expansion means one DataLoader batch of 3 videos yields 15 MIL bag samples, not 3. The existing `MILFeatureDataset`'s `batch_size=16` default (Phase 3 D-04) does NOT translate directly; `rtfm_i3d.yaml:22` explicitly uses 3. Planner must not default to 16 in build_dataloaders_i3d.
- D-12 bit-identical rerun is possible because `set_deterministic(cfg['seed'])` at `src/train.py:147` + `torch.use_deterministic_algorithms(True)` + the CUBLAS env var at src/train.py:4-5 already give us Phase 3 SC #4 byte-for-byte reproducibility. Inherits for free.
- Named LN in rtfm_i3d.py (`self.ln_i3d = nn.LayerNorm(i3d_dim)` at line 44) is the only reason Phase 5 TTA could use the rtfm variant as an adaptation target if ever desired — Phase 5's actual adaptation base is ucf_gated_fusion, but preserving ln_i3d for symmetry is a D-07 inheritance.
- XD-Violence test set is 800 videos; at ~20-60s per video for evaluate.py inference, the post-training eval pass is ~3-5 minutes on RTX 4090. The D-16 smoke test runs on a batch fraction of that (1 epoch ≈ length-of-training / 50 epochs ≈ 10-30s training + no eval). Total Phase 4b compute budget for the gate: ~10-20 minutes wall-clock on GPU.

</specifics>

<deferred>
## Deferred Ideas

### Deferred to Phase 4c (not lost — explicit handoff)
- XD-Violence main results table: 6 variants × seed=42 + 2 pooling ablations + 3-seed Gated Fusion + per-category Fighting/Abuse/Riot (EVAL-02..EVAL-05 XD completion).
- XD re-extraction passes: `scripts/extract_ctrgcn.py --keep-persons` targeting XD; `scripts/extract_clip.py --pool=mean` targeting XD. Activated by the D-03 filesystem trigger.
- 2 XD pooling YAMLs: `configs/gated_fusion_xd_2person.yaml`, `configs/gated_fusion_xd_clip_mean.yaml` (or a dataset-swap on existing UCF pooling YAMLs — planner's call in Phase 4c).
- 3 new orchestrator queues in `scripts/run_ablations.py::QUEUES`: `phase4c_main` (4 XD variants), `phase4c_pooling` (2 ablations), `phase4c_seeds` (Gated Fusion seeds 123, 2024). Phase 4b keeps only the existing `rtfm_gate` queue.
- Per-category Fighting/Abuse/Riot breakdown — uses the D-10 parser's category output (forward-compat is intentional for this purpose).
- ROADMAP.md Phase 4c detail block creation (Goal / Depends on / Activation criterion / Requirements / Success Criteria / Plans: TBD); Phase 4b's planner performs this edit.
- REQUIREMENTS.md annotation flip: EVAL-02..EVAL-05 XD-side annotations move from "Phase 4b" to "Phase 4c"; EVAL-01 stays in Phase 4b.

### Deferred within Phase 4b (may not happen; conditional on D-11 cascade)
- RGB+Flow I3D variant `rtfm_i3d_rgbflow` — only if primary gate misses AND MGFN anchor also misses.
- MTN temporal module addition to `src/models/rtfm_i3d.py` — last-resort fallback before thesis-limitation acceptance.
- `configs/rtfm_i3d.yaml` `data.batch_size` raise from 3 → 16 — empirical post-gate tuning; not a Phase 4b deliverable.
- `wandb.tags` historical label fix (`phase4` → `phase4b` in rtfm_i3d.yaml) — cosmetic; not worth churning while wandb is disabled.

### Deferred beyond project scope (carried from Phase 4)
- UCF-Crime RTFM reproduction (original PRD EVAL-01 target at 84.30% AUC) — requires downloading UCF I3D features separately. Optional supplement only.
- Multi-person skeleton `max` and `mean` aggregation ablations on XD (vs chosen `concat`) — Phase 4c slack.
- `last_model.pth` sanity eval for RTFM variant — not required.
- Flow-stream CLIP ablation — out of v1 scope.
- Cross-dataset RTFM (train on UCF I3D, test on XD I3D) — out of scope.

### Reviewed Todos (not folded)
None — no pending todos matched Phase 4b per `gsd-tools todo match-phase 4b`.

</deferred>

---

*Phase: 04b-xd-violence-main-results-rtfm-xd-i3d-gate (scope narrowed to RTFM XD-I3D Gate only per D-01)*
*Context gathered: 2026-04-16*
