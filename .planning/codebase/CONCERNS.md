# Codebase Concerns

**Analysis Date:** 2026-06-09

This audit focuses on reproducibility fragility, environment complexity, and
statistical-validity hazards specific to ViolenceCC. The headline numbers (UCF
82.5% AUC, XD 78.7% AP) are verified correct and the method matches the paper
equations (see `.planning/CODE-PAPER-REVIEW-2026-06-07.md`). The concerns below
are about *durability* of those results, not their correctness.

## Tech Debt

**Untracked `_tmp_*` throwaway scripts (TTA investigation):**
- Issue: The entire disc_reweight / CORAL / 6-strategy TTA search lives in ~21 untracked `??` scripts. These produced the committed Table 3 numbers but are not in git.
- Files: `scripts/_tmp_r1_full.py`, `scripts/_tmp_r1_variants.py`, `scripts/_tmp_coral_derisk.py`, `scripts/_tmp_r2_full.py`, `scripts/_tmp_s4_full.py`, `scripts/_tmp_tta_harness.py`, `scripts/_tmp_harness_smoke.py`, `scripts/_tmp_disc_signal.py`, `scripts/_tmp_cache_srcstats.py`, `scripts/_tmp_validate_production.py`, `scripts/_tmp_gate_by_cat.py`, `scripts/_tmp_strat_S1_shiftgated.py` … `scripts/_tmp_strat_S6_open.py`, `scripts/_tmp_strat_template.py`, `scripts/_run_tta_backbone_batch.py`, `scripts/_check_citations.py`
- Impact: The *outputs* of these scripts (the seed-variant JSONs) ARE now force-committed and a tracked regenerator (`scripts/aggregate_tta_table.py`) reconstructs Table 3 from them, so the headline TTA result survives loss of the working tree. But the *generating logic* (how the JSONs were produced) is uncommitted. If a reviewer asks "regenerate `r1full_clip.json` from scratch," only `src/tta/disc_reweight.py` + `src/tta/evaluate_tta.py` (committed) can do that; the orchestration glue cannot.
- Fix approach: Either (a) delete the `_tmp_*` scripts now that the JSONs + `aggregate_tta_table.py` exist, or (b) promote the one or two that still matter (`_tmp_r1_full.py`, `_tmp_r1_variants.py`) to tracked, named drivers and delete the rest. Do NOT leave 21 untracked scripts as the de-facto provenance.

**Stale LaTeX table generator emits an outdated Table 3:**
- Issue: `scripts/generate_latex_tables.py` (tracked) has **zero** references to `disc_reweight` (verified by grep) and regenerates the OLD TENT/SAR-format Table 3 plus a stale Table 1/2 Visual-Only row (XD SO400M 77.2 — the single-seed artifact that the 3-seed re-analysis overturned to ~76.6).
- Files: `scripts/generate_latex_tables.py`, `paper/tables_generated.tex` (its output)
- Impact: `paper/tables_generated.tex` is now banner-marked (`STALE AUTO-GENERATED ARTIFACT -- DO NOT USE / DO NOT \input`, lines 1-9) and is NOT `\input` by `paper/main.tex` (tables are inlined). So the build is safe today. But the generator is a live trap: re-running it overwrites `tables_generated.tex` with wrong numbers, and a future contributor who trusts the filename could `\input` it.
- Fix approach: Update `scripts/generate_latex_tables.py` to emit the disc_reweight 3-seed Table 3 (using `scripts/aggregate_tta_table.py` as the data source) and the 3-seed Visual-Only rows, OR delete the generator and document that `paper/main.tex` inline tables are the canonical source.

**Two parallel, divergent table generators:**
- Issue: `scripts/aggregate_tta_table.py` (new, correct, H1 fix) and `scripts/generate_latex_tables.py` (old, stale) both claim to produce paper tables but disagree. No single source of truth for table generation.
- Files: `scripts/aggregate_tta_table.py`, `scripts/generate_latex_tables.py`
- Fix approach: Consolidate to one generator or clearly scope each (aggregate = Table 3 only; generate_latex = retire).

## Provenance Fragility

**`results/` is git-ignored except hand-picked force-added aggregates:**
- Issue: `.gitignore:9` excludes all of `results/`. Reproducibility of every committed number therefore depends on 27 files that were *manually* force-added past the ignore rule (`git check-ignore` reports them as not-ignored because tracked status wins, confirming they were force-added).
- Files (the only committed evidence for all headline + TTA numbers):
  - `results/results-index.csv` — master index of all runs
  - `results/phase10_charts/backbone_comparison_4way.csv`, `seed_stability_4way.csv`, `visual_only_seed_stability_4way.csv`, `comparison_{auc,ap}_4way.png`, `seed_stability_4way.png`
  - `results/_coral_derisk/r1full_{clip,base,giant,so400m}.json` — seed-42 disc_reweight (TTA "Ours")
  - `results/_coral_derisk/variants/v_<tag>_s{123,2024}_test.json` (8 files) — seeds 123/2024 for the 3-seed TTA mean
  - `results/_coral_derisk/variants/v_<tag>_s42_train.json` (4 files) — clean-TRAIN-reference robustness check
  - `results/_tta_rerun_continual/summary.json` — TENT/SAR entropy baseline
  - `results/h1_recompute/ucf_fulllength_comparison.csv`, `ucf_giant_s42_per_category.csv`, `xd_SKIPPED.txt`
- Impact: This is structurally fragile. Any per-run `eval_metrics.json` that Tables 1/2 trace to (per `.planning/CODE-PAPER-REVIEW-2026-06-07.md`) is NOT committed — only the aggregated CSVs are. The full audit trail from raw run → table cell exists only in the working tree / on `E:\`. A `git clone` on a fresh machine cannot reproduce Tables 1/2 from scratch, only re-display the committed aggregates. The TTA story is safer (raw JSONs + `aggregate_tta_table.py` committed), but the ablation tables are aggregate-only.
- Fix approach: Decide the reproducibility contract explicitly. Either force-add the per-run `eval_metrics.json` set that Tables 1/2 depend on, or document in a README that `results/` is intentionally aggregate-only and raw runs live on `E:\`. The force-add mechanism is undocumented; a contributor running `git add results/` gets nothing.

**E:\ external-drive dependency for all features and snippets:**
- Issue: Every training/eval config hard-codes absolute Windows paths to an external drive: `skeleton_features: "E:/features/ucf/skeleton"`, `clip_features: "E:/features/ucf/clip"`, `snippet_boundaries_dir: "E:/snippets/ucf"` (`configs/gated_fusion.yaml:8-11`, replicated across ~50 configs in `configs/`).
- Files: all of `configs/*.yaml` (verified `E:[\\/]` matches in 40+ configs), plus `scripts/run_ablations.py`, `scripts/retrain_lam0.py`
- Impact: Nothing reproduces without the `E:\` drive mounted at that exact letter. `.gitignore:6` also ignores `data/features/` (the documented symlink/junction target). The ~25 GB feature cache per dataset is the single point of failure for the whole pipeline and is not backed up in-repo (correctly — it is too large), but there is no manifest/checksum committed to detect cache corruption or verify the right features are present. The CLAUDE.md "Feature Extraction" convention warns about silent zero-vector degradation; a missing/wrong `E:\` cache would surface as bad metrics, not a clean error.
- Fix approach: Add an env-var or config-relative path indirection (`${FEATURES_ROOT}`) so the drive letter is not baked into 50 files; commit a feature-cache manifest (per-video shape + checksum) so presence/integrity is verifiable; document the `E:\` layout in a setup README.

## Environment Complexity

**Three-conda-environment split with a legacy PyTorch 1.12 silo:**
- Issue: The pipeline requires three mutually incompatible conda environments (`vcc-skeleton`, `vcc-ctrgcn`, `vcc-main`) because `mmcv-full 1.7.0` (PYSKL/CTR-GCN) cannot coexist with PyTorch 2.x (`STATE.md` Key Decisions: "Three conda environments"; "vcc-ctrgcn is a legacy silo").
- Files: `envs/requirements-skeleton.txt`, `envs/requirements-ctrgcn.txt`, `envs/requirements-main.txt`; documented in `CLAUDE.md` (Complete Version Compatibility Matrix)
- Impact: High setup and reproduction cost. `vcc-ctrgcn` pins PyTorch 1.12.1+cu113 / CUDA 11.3 / cuDNN 8.3.2 / numpy<2 / mmcv-full 1.7.0 / mmdet 2.25.1 / mmpose 0.29.0 — a 2022-era stack frozen against EOL libraries. The Windows-specific install hazards are extensive (per `STATE.md`): PyTorch 1.12.1 conda wheel fails (WinError 182, must use pip +cu113 wheel), mmpose/PYSKL installed `--no-deps` (chumpy build failure), cp950 locale breaks tqdm stdout, cuDNN 9 DLLs in version-subdirs requiring manual PATH surgery. The `requirements-*.txt` are explicitly "reference documents," not `pip install -r` targets (`STATE.md` Key Decisions) — so there is no one-command env rebuild.
- Fix approach: This is a hard external constraint (PYSKL is unmaintained against torch 2.x), not fixable cheaply. Mitigation: the legacy env is only needed for one-time *feature extraction*; once `E:\features` exists, only `vcc-main` is needed for all training/eval. Document this so reproducers do not rebuild `vcc-ctrgcn` unnecessarily. Consider committing an `environment.yml` lockfile for `vcc-ctrgcn` specifically since it is the most fragile.

## Statistical-Validity Hazards

**XD visual-only metrics are seed-unstable (±1.5–2.2 AP):**
- Issue: XD visual-only AP has per-seed std ±1.5–2.2 (vs UCF AUC ±0.1–0.5), large enough that single-seed runs produce phantom effects. Two such effects were caught and reversed during the 2026-06-09 review (`STATE.md` Key Decisions; `.planning/CODE-PAPER-REVIEW-2026-06-07.md` M7).
- Files: backbone seed-comparison driver `scripts/generate_pub_figures.py`; committed evidence `results/phase10_charts/visual_only_seed_stability_4way.csv`, `results/phase10_charts/seed_stability_4way.csv`; per-run JSONs in `results/_coral_derisk/variants/`
- Impact: TWO published-claim-grade findings were single-seed (s42) artifacts that vanished at 3 seeds: (1) the apparent "SigLIP2-Base/XD fusion regression" (−2.3 → +0.05, p≈0.97); (2) "SO400M leads XD visual-only (77.2)" (→ 76.6 ≈ Giant 76.8). The stale `paper/tables_generated.tex:39` still prints the 77.2 artifact. Any future XD claim built on a 1-seed run is at high risk.
- Standing rule (from `STATE.md`): "Never compare a 3-seed metric to a 1-seed baseline (esp. XD)" and "always replicate BOTH sides before claiming a margin." This is a recurring footgun, not a one-off.
- Fix approach: Enforce a minimum 3-seed protocol for any reported XD metric; gate paper edits on matched-seed both-sides replication. The skeleton-complementarity claim is now correctly reframed as "small + consistent" (gated ≥ visual in 8/8 configs, sign-test p≈0.008, no per-cell significance at n=3) — keep tables from overstating it.

**Single-seed visual-only baselines still lack error bars in places:**
- Issue: Per `.planning/CODE-PAPER-REVIEW-2026-06-07.md` M7, some complementarity endpoints compared a 3-seed gated mean to a seed-42-only visual-only number. The 3-seed visual-only runs now exist (`m7_visual_seeds`, committed to `results/phase10_charts/visual_only_seed_stability_4way.csv`), but the discipline of always pairing seed counts must be maintained going forward.
- Files: `results/phase10_charts/visual_only_seed_stability_4way.csv`
- Risk: Re-introducing a 1-seed-vs-3-seed comparison in a future revision.
- Priority: Medium (procedural).

## Documented Pitfalls (C1–C5 / M5–M7)

**Standing risk register carried in `STATE.md` "Critical Pitfalls to Watch":**
- Issue: These are known, mitigated-but-not-eliminated hazards that any code change touching the affected paths must respect. Captured here so they are not lost when `STATE.md` rotates.
- Files: documented in `.planning/STATE.md` lines 149-158
- Catalog:
  - **C1** Skeleton coordinate-space mismatch (raw pixel vs normalized). Phase 2. Mitigation: `PreNormalize2D`, assert coords in [−1,1]. (Note: paper wording about this transform was corrected in M1 — it is image-center, not bbox-midpoint, normalization; see `extract_skeletons.py:120-124`.)
  - **C2** Temporal misalignment in variable-FPS videos. Phase 2. Mitigation: read FPS per video, map snippet boundaries to wall-clock seconds.
  - **C3** Test-set leakage into hyperparameter tuning. Phase 3-4. Mitigation: early-stop on val MIL loss only; test annotations loaded only in `evaluate.py`. (The TTA disc_reweight path is transductive + uses a clean reference — validated leakage-free, clean-train-ref ≡ clean-test-ref.)
  - **C4** Off-by-one in snippet-to-frame score expansion. Phase 4. Mitigation: single utility, assert `len(frame_scores)==len(frame_labels)`. (Related to the H1 UCF full-length-eval recompute, `results/h1_recompute/`.)
  - **C5** MIL training collapse to trivial solutions. Phase 3-4. Mitigation: monitor snippet-score variance; match RTFM bag construction.
  - **M5** TTA entropy collapse on normal-heavy batches. Phase 5. Mitigation: SAR-style gradient filtering. (Empirically: entropy TTA ≈ 0 effect, <0.1 pp; the BN→LN transfer is inert on these short clips.)
  - **M6** SAR ρ ImageNet default too large for scalar output. Phase 5. Mitigation: ρ=0.05 (not ImageNet default).
  - **M7** Corruption TTA requires skeleton re-extraction for motion-blur + JPEG. Phase 5. Mitigation: only noise/brightness conditions reuse the source skeleton cache.
- Impact: These are correctness landmines specific to weakly-supervised VAD. Any new fusion variant, eval path, or corruption condition must re-check the relevant pitfall.

## Test Coverage Gaps

**TTA orchestration / aggregation is not unit-tested end-to-end:**
- What's not tested: `scripts/aggregate_tta_table.py` (the H1 regenerator that reconstructs Table 3) has no test asserting its output matches the committed paper numbers. The disc_reweight *math* is well-covered (`tests/test_disc_reweight.py`, `tests/test_evaluate_tta.py`, 25 pass) and TTA determinism is tested (dropout-disable + manual_seed regression tests, per `STATE.md` 260604-w2a), but the JSON → table-cell aggregation path is not.
- Files: `scripts/aggregate_tta_table.py`, `results/_coral_derisk/`, `results/_tta_rerun_continual/summary.json`
- Risk: A silent drift between the committed JSONs and the paper's Table 3 would not be caught. Given the provenance is the whole point of the H1 fix, an assertion test (aggregate output == hard-coded paper values) would lock it.
- Priority: Medium.

**Per-run eval artifacts for Tables 1/2 are not committed, so table regeneration is untestable from git:**
- What's not tested: There is no committed fixture set of `eval_metrics.json` to regression-test Table 1/2 generation against. Verification (per the review) was done manually against working-tree files.
- Files: Tables 1/2 in `paper/main.tex`; un-committed `eval_metrics.json` per run
- Risk: Ablation tables can drift undetected.
- Priority: Medium (tied to the provenance-fragility item above).

---

*Concerns audit: 2026-06-09*
