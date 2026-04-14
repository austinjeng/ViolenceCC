# Phase 4: Baseline Evaluation & Main Results - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-15
**Phase:** 04-baseline-evaluation-main-results
**Areas discussed:** XD-Violence sequencing, Eval harness + RTFM gate, Ablation orchestration + seeds, Pooling ablation caches, I3D data loader, UCF anno parsing, Run-index & resume, Test-set discipline, Config inheritance vs flat, Evaluate.py output spec, wandb pre-flight

---

## Area 1: XD-Violence sequencing

### Q1.1 — XD extraction status

| Option | Description | Selected |
|--------|-------------|----------|
| Stalled / needs restart | Kick off fresh skeleton + CLIP extraction | |
| Running elsewhere | Progressing on another drive/machine, will land eventually | ✓ |
| Discarded on purpose | Drop XD from Phase 4 scope | |
| Unknown, investigate | Check processes and logs first | |

**User's choice:** Running elsewhere
**Notes:** Extraction proceeds out-of-band; Phase 4 does not monitor or block on it.

### Q1.2 — Phase split

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 4 = UCF only, Phase 4b = XD | Complete UCF work now; new phase for XD | ✓ |
| Wait for XD, then both together | Pause until XD ready | |
| Start UCF now, fold XD mid-phase | Extend same phase when XD lands | |
| UCF only, drop XD entirely | Cut XD from v1 | |

**User's choice:** Phase 4 = UCF only, Phase 4b = XD
**Notes:** Unblocks ~2-3 weeks of work; keeps phase boundaries clean.

### Q1.3 — XD I3D usage

| Option | Description | Selected |
|--------|-------------|----------|
| Use for RTFM on XD | Retarget RTFM gate from UCF to XD I3D | ✓ |
| Keep as reference only | RTFM stays on UCF I3D (requires separate download) | |
| Use for both datasets | Download UCF I3D + use XD I3D | |

**User's choice:** Use for RTFM on XD
**Notes:** Avoids needing UCF I3D; XD I3D features already on disk.

### Q1.4 — UCF annotation source

| Option | Description | Selected |
|--------|-------------|----------|
| Download from official source | Sultani 2018 UCF-Crime webpage, git-track | ✓ |
| Pull from RTFM repo | Use their gt-ucf.npy | |
| User provides locally | Point to existing path | |

**User's choice:** Download from official source
**Notes:** Small file; committed to `data/annotations/`.

---

## Area 2: Eval harness + RTFM gate

### Q2.1 — evaluate.py CLI shape

| Option | Description | Selected |
|--------|-------------|----------|
| Takes run_dir | `--run-dir results/<run>`; reads config + checkpoint | ✓ |
| Takes --config + --checkpoint | Two explicit paths | |
| Either, via argparse | Support both forms | |

**User's choice:** Takes run_dir
**Notes:** Matches Phase 3 D-14 results-dir pattern; adds `.done` marker + writes back into same dir.

### Q2.2 — RTFM reproduction strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Retrain RTFM MIL on XD I3D | Register rtfm_i3d variant; gate on AP number | |
| Clone RTFM repo, run as-is | External subprocess | |
| Use their pretrained checkpoint | Inference-only validation | |
| Our eval.py + our RTFM variant | Validates BOTH architecture AND eval code | ✓ |

**User's choice:** Our eval.py + our RTFM variant
**Notes:** Austin asked for the thesis-best option. Recommended because reproducibility requires validating our own evaluate.py (not just their published binary). Target ±1% of RTFM ~77.81% or MGFN ~80.11% on XD I3D.

### Q2.3 — Frame expansion logic

| Option | Description | Selected |
|--------|-------------|----------|
| Score every snippet at test | Forward all snippets; broadcast per modality | ✓ |
| Unified frame timeline | Combine skel+clip per-frame | |
| Dataset-specific expander | Separate UCF vs XD functions | |

**User's choice:** Score every snippet at test (with clarification)
**Notes:** Fused model outputs ONE scalar per snippet post-fusion → single broadcast. Master grid = skeleton's native 64-frame window; CLIP resampled to skeleton grid at load time. Single-modal variants use native granularity. Utility `snippet_to_frame()` with length assertion (C4 mitigation).

### Q2.4 — Per-category output format

| Option | Description | Selected |
|--------|-------------|----------|
| Filename prefix + eval_metrics.json | Combined JSON | |
| Filename prefix + per_category.csv | Separate CSV | ✓ |
| Defer until after ablation | Second pass | |

**User's choice:** Separate per_category.csv
**Notes:** LaTeX-paste-ready; keeps eval_metrics.json scalar-clean for 3-seed aggregation.

---

## Area 3: Ablation orchestration + seeds

### Q3.1 — Runner tooling

| Option | Description | Selected |
|--------|-------------|----------|
| Python runner | scripts/run_ablations.py | ✓ |
| Shell script | scripts/run_ablations.sh | |
| Makefile | New build tool | |

**User's choice:** Python runner
**Notes:** Cross-platform, greppable, native resume logic.

### Q3.2 — 3-seed scope

| Option | Description | Selected |
|--------|-------------|----------|
| Gated Fusion only | Per SC #4 | ✓ |
| All 4 primary variants | Stronger stats, +9 runs | |
| Gated + Late only | Middle ground | |

**User's choice:** Gated Fusion only
**Notes:** Matches SC #4 scope exactly; saves ~9 runs.

### Q3.3 — Seed set

| Option | Description | Selected |
|--------|-------------|----------|
| {42, 123, 2024} | Training default + literature standards | ✓ |
| {0, 1, 2} | Clean-slate | |
| {42, 43, 44} | Correlated | |

**User's choice:** {42, 123, 2024}
**Notes:** Defensible in thesis without extra justification.

### Q3.4 — Pooling ablation seeds

| Option | Description | Selected |
|--------|-------------|----------|
| Single seed = 42 | SC #3 asks "results", not ±std | ✓ |
| 3-seed for pooling too | +6 runs | |
| 3-seed only if delta < 0.5% | Adaptive | |

**User's choice:** Single seed = 42
**Notes:** Claude's discretion to re-run 3-seed if delta turns out tiny.

---

## Area 4: Pooling ablation caches

### Q4.1 — Multi-person cache shape

| Option | Description | Selected |
|--------|-------------|----------|
| [N, 2, 256] single file | Aggregation at load time | ✓ |
| [N, 512] pre-concat | Baked into cache | |
| Two files per video | Per-person separation | |

**User's choice:** [N, 2, 256] single file
**Notes:** Switching aggregation doesn't require re-extraction.

### Q4.2 — Multi-person aggregation choice

| Option | Description | Selected |
|--------|-------------|----------|
| concat | PYSKL/PRD §12.3 convention; [N, 512] | ✓ |
| max | Elementwise max across persons | |
| mean | Elementwise mean | |
| All three | Exceeds SC #3 budget | |

**User's choice:** concat
**Notes:** max/mean deferred as optional extras.

### Q4.3 — Cache directory layout

| Option | Description | Selected |
|--------|-------------|----------|
| Sibling dirs | skeleton_2person/ and clip_mean/ | ✓ |
| Suffix in filename | Same dir, _2p / _mean suffix | |
| Under ablations/ subdir | Semantic grouping | |

**User's choice:** Sibling dirs
**Notes:** YAML paths field selects cache; loader stays directory-agnostic.

### Q4.4 — Re-extraction scope

| Option | Description | Selected |
|--------|-------------|----------|
| UCF only in Phase 4 | Matches Area 1 phase split | ✓ |
| Both datasets now | Requires XD base features | |
| UCF now, defer XD (explicit) | Same as recommended, explicit doc | |

**User's choice:** UCF only in Phase 4
**Notes:** XD pooling ablations are Phase 4b scope.

---

## Area 5: I3D data loader

### Q5.1 — Crop handling

| Option | Description | Selected |
|--------|-------------|----------|
| All crops train, mean at test | RTFM-standard test-time averaging | ✓ |
| Random crop train, crop 0 test | Simpler, weaker reproduction | |
| Mean all crops (train + test) | Smallest code change | |

**User's choice:** All crops train, mean at test
**Notes:** 5× effective training signal; matches RTFM published protocol.

### Q5.2 — I3D cache path YAML

| Option | Description | Selected |
|--------|-------------|----------|
| paths.i3d_features (single) | Single path; loader routes RGB/RGBTest | ✓ |
| Two paths: train + test | Explicit but duplicates split info | |
| Symlink into data/features/ | Clean relative path, Windows admin | |

**User's choice:** paths.i3d_features = E:/i3d-features/i3d-features/
**Notes:** Consistent with existing paths.skeleton_features pattern.

### Q5.3 — Flow stream

| Option | Description | Selected |
|--------|-------------|----------|
| RGB only for Phase 4 | Matches RTFM's published XD number | ✓ |
| RGB + Flow concat | 2048-d; matches MGFN | |
| Ablate separately | Extra runs, scope creep | |

**User's choice:** RGB only for Phase 4
**Notes:** Flow is a Phase 4b consideration if AP misses the gate.

---

## Area 6: UCF anno parsing

### Q6.1 — AUC frame granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Original 30fps | np.repeat ×10 to match published baselines | ✓ |
| PNG granularity (~3fps) | Natural but diverges from baselines | |
| Both, report one | Extra complexity | |

**User's choice:** Original 30fps
**Notes:** RTFM/MGFN/VadCLIP all at 30fps; thesis comparability requires this.

### Q6.2 — Two-interval handling

| Option | Description | Selected |
|--------|-------------|----------|
| Union both intervals | Sultani 2018 convention | ✓ |
| First interval only | Misses multi-segment anomalies | |
| Treat as separate test items | Breaks cardinality | |

**User's choice:** Union both intervals
**Notes:** Standard RTFM/MGFN handling.

### Q6.3 — Category label source

| Option | Description | Selected |
|--------|-------------|----------|
| Category column in anno | Official labels | ✓ |
| Regex filename prefix | Fragile for edge cases | |
| Both, cross-check | Defensive unit test | |

**User's choice:** Category column in anno
**Notes:** Strictest + reliable; anno file is authoritative.

### Q6.4 — Violence subset definition

| Option | Description | Selected |
|--------|-------------|----------|
| {Fighting, Assault} union | Per EVAL-04 + FEATURES.md | ✓ |
| {Fighting, Assault, Abuse} | Expanded scope | |
| Per-category individually | Scope creep vs EVAL-04 | |

**User's choice:** {Fighting, Assault} union
**Notes:** Matches PRD RQ1 scope exactly.

---

## Area 7: Run-index & resume

### Q7.1 — Skip check mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Filesystem probe + .done marker | Atomic after eval success | ✓ |
| eval_metrics.json presence | Doesn't distinguish partial failure | |
| Central results-index.csv | Drift risk | |

**User's choice:** Filesystem probe + .done marker
**Notes:** .done written only after eval completes successfully.

### Q7.2 — Run dir naming

| Option | Description | Selected |
|--------|-------------|----------|
| Deterministic, no timestamp | Idempotent; --run-name override | ✓ |
| Timestamped (D-14 pattern) | No idempotency | |
| Timestamp + stable symlink | Windows symlink quirks | |

**User's choice:** Deterministic, no timestamp
**Notes:** Timestamped D-14 reserved for ad-hoc / debug runs.

### Q7.3 — Failure recovery

| Option | Description | Selected |
|--------|-------------|----------|
| Log error, continue queue | Runner proceeds; end summary | ✓ |
| Halt on first failure | Simpler semantics | |
| Retry once, then halt | Handles transient errors | |

**User's choice:** Log error, continue queue
**Notes:** Filesystem probe skips completed work on re-run.

### Q7.4 — results-index.csv

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, append-only | Easy thesis-table generation | ✓ |
| Regenerate from filesystem | Slow at scale | |
| wandb sweep view only | Coupling to external service | |

**User's choice:** Yes, append-only
**Notes:** Deterministic-dir probe remains the skip mechanism; CSV is audit log.

---

## Area 8: Test-set discipline

### Q8.1 — Test loader location

| Option | Description | Selected |
|--------|-------------|----------|
| Separate module (src/eval/test_loader.py) | Hard import boundary | ✓ |
| Same dataset.py, mode flag | Weaker guard | |
| Test loader under src/data/ | Slightly weaker boundary | |

**User's choice:** Separate module
**Notes:** Python import graph itself blocks C3 leakage.

### Q8.2 — Runtime guard

| Option | Description | Selected |
|--------|-------------|----------|
| Loud fail on test import | sys.argv[0] check | ✓ |
| Lazy load + log audit | Observability only | |
| No runtime guard | Import boundary only | |

**User's choice:** Loud fail on test import
**Notes:** Belt-and-suspenders; pytest paths whitelisted.

### Q8.3 — Val vs test confusion prevention

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit --split flag | evaluate.py --split {val,test} | ✓ |
| Two separate entry points | validate.py + evaluate.py | |
| Auto-infer from split file | Fragile | |

**User's choice:** Explicit --split flag
**Notes:** Default=test; val computes MIL loss only.

### Q8.4 — UCF annotation path

| Option | Description | Selected |
|--------|-------------|----------|
| data/annotations/, git-tracked | Small file, always in repo | ✓ |
| data/annotations/, gitignored | Requires download step | |
| E:/ external, symlinked | Overkill for 50KB file | |

**User's choice:** data/annotations/, git-tracked
**Notes:** No separate download step in SETUP.md.

---

## Area 9: Config inheritance vs flat

### Q9.1 — Config style

| Option | Description | Selected |
|--------|-------------|----------|
| Stay flat per Phase 1 D-03 | 3 new self-contained YAMLs | ✓ |
| Introduce _base.yaml | Inheritance with OmegaConf | |
| Programmatic generation | Flat on disk, DRY source | |

**User's choice:** Stay flat per Phase 1 D-03
**Notes:** 7 configs total after Phase 4; manageable duplication.

### Q9.2 — RTFM YAML dataset binding

| Option | Description | Selected |
|--------|-------------|----------|
| XD-Violence I3D | dataset: xd_i3d (new key) | ✓ |
| Generic I3D | Dataset-switchable via paths | |
| Two separate YAMLs | UCF placeholder | |

**User's choice:** XD-Violence I3D
**Notes:** rtfm_i3d.yaml dedicated to XD path.

### Q9.3 — YAML naming convention

| Option | Description | Selected |
|--------|-------------|----------|
| Describe the variant | rtfm_i3d / gated_fusion_2person / gated_fusion_clip_mean | ✓ |
| Grouped by ablation dim | ablation_rtfm / ablation_skel_agg / ablation_clip_pool | |
| Numbered | ablation_01 / 02 / 03 | |

**User's choice:** Describe the variant
**Notes:** Matches existing Phase 3 style.

### Q9.4 — MODEL_REGISTRY new keys

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse gated_fusion + data cfg | skel_agg field + paths | ✓ |
| New variant keys | gated_fusion_2p_concat etc. | |
| Data-only ablation | Infer from feature shape | |

**User's choice:** Reuse gated_fusion + data cfg
**Notes:** Registry stays at 5 keys (4 existing + rtfm_i3d).

---

## Area 10: Evaluate.py output spec

### Q10.1 — Metric keys (multiSelect)

| Option | Description | Selected |
|--------|-------------|----------|
| auc + ap (primary) | Both always computed | ✓ |
| snippet-level AUC (debug) | Pre-broadcast | ✓ |
| video-level AUC (sanity) | Max-score per video | ✓ |
| per-category dict | Sub-dict in JSON (+ separate CSV) | ✓ |

**User's choice:** All four
**Notes:** Full metric coverage for thesis + debug aid.

### Q10.2 — Reproducibility metadata (multiSelect)

| Option | Description | Selected |
|--------|-------------|----------|
| config_hash + git_sha + checkpoint_sha | Minimum audit chain | ✓ |
| wandb_run_id | Cross-link to curves | ✓ |
| dataset + split + seed | Redundant but standalone-readable | ✓ |
| eval_timestamp + eval_duration_s | Audit aid | ✓ |

**User's choice:** All four
**Notes:** Full reproducibility bundle in each JSON.

### Q10.3 — Per-video score export

| Option | Description | Selected |
|--------|-------------|----------|
| Separate eval_scores.npz | Compressed, Phase 6 consumes | ✓ |
| Embed in JSON | ~20MB per run | |
| Re-run inference in Phase 6 | Wasted compute | |

**User's choice:** Separate eval_scores.npz
**Notes:** {video_id: frame_scores_array} at 30fps granularity.

### Q10.4 — Checkpoint selection

| Option | Description | Selected |
|--------|-------------|----------|
| best_model.pth | Honors Phase 3 D-15 + TRN-02 | ✓ |
| best + last, report max | Test-set model selection (C3 risk) | |
| best + last, both in JSON | Transparency extra | |

**User's choice:** best_model.pth
**Notes:** No test-leakage via model selection.

---

## Area 11: wandb pre-flight

### Q11.1 — Pre-flight handling

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-flight check + fail fast | scripts/wandb_preflight.py | ✓ |
| Offline by default, sync later | Loses live monitoring | |
| WANDB_API_KEY env var | Solo-use awkward for reproduction | |

**User's choice:** Pre-flight check + fail fast
**Notes:** Resolves Phase 3 VERIFICATION nit; keeps sweep view working.

### Q11.2 — Runtime auth fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Fall back to offline + log | CSV remains source of truth | ✓ |
| Halt the run | Too harsh for transient errors | |
| Silent disable | Loses observability | |

**User's choice:** Fall back to offline + log
**Notes:** Training subprocess re-inits with mode=offline on wandb failure.

### Q11.3 — wandb tag scheme

| Option | Description | Selected |
|--------|-------------|----------|
| Tags per run dim | [phase4, dataset, variant, seed, cache_variant] | ✓ |
| wandb sweep config | Conflicts with Area 3 Python runner | |
| Group name per ablation set | Cleaner but flatter | |

**User's choice:** Tags per run dim
**Notes:** Matches Phase 3 pattern.

---

## Claude's Discretion

See CONTEXT.md `<decisions>` → `### Claude's Discretion` for the list (RTFM FM head fidelity, eval_scores compression, per_category.csv column ordering, val eval depth, config_hash timing, wandb group fallback, subprocess-vs-import, resume-mid-run edge cases, dirty-tree handling, Normal-row in per_category.csv, I3D training size mismatch).

## Deferred Ideas

See CONTEXT.md `<deferred>` section. Key items:
- Phase 4b (XD-Violence main results) — new phase to be added to ROADMAP.md
- UCF-Crime RTFM reproduction via UCF I3D — Phase 4b or optional supplement
- Multi-person max/mean aggregation — optional if time permits
- Flow I3D stream inclusion for RTFM — fallback if RGB AP misses gate
- OPT-07 (CLIP FPS ablation), OPT-08 (RWF-2000), OPT-09 (t-SNE), OPT-10 (gating histograms), OPT-01 (YOLO-World) — out of Phase 4 scope
