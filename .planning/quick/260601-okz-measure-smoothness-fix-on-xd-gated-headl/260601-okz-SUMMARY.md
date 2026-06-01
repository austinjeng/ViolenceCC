---
phase: quick-260601-okz
plan: 01
subsystem: testing
tags: [mil-loss, smoothness, xd-violence, gated-fusion, siglip2, so400m, ap, auc, measurement]

requires:
  - phase: quick-260601-o55
    provides: "Smoothness-axis fix (mil_loss dim1) committed at f89910b; measured on headline UCF"
provides:
  - "XD-Violence AP/AUC exposure of the smoothness fix at seed 42 for both gated contenders"
  - "MATERIAL verdict: SO400M ΔAP −3.80pp (beyond seed-std) + s42 AP ordering flip"
  - "Divergent-delta finding → implied 3-seed-mean ordering AT RISK; full XD retrain recommended"
affects: [thesis-manuscript, xd-table2, gated-fusion-backbone-comparison]

tech-stack:
  added: []
  patterns:
    - "Bit-exact deterministic XD training lets canonical (buggy) eval serve as the buggy control — no buggy re-run needed"

key-files:
  created:
    - results/_smoothfix/xd_base_fixed_s42/eval_metrics.json (scratch, gitignored)
    - results/_smoothfix/xd_so400m_fixed_s42/eval_metrics.json (scratch, gitignored)
    - results/_smoothfix/xd_measurement.md (scratch, gitignored)
  modified: []

key-decisions:
  - "Verdict MATERIAL: SO400M |ΔAP|=3.80pp exceeds XD seed-std (~2.8-2.9pp) AND s42 AP ordering flips (canonical SO400M>Base → fixed Base>SO400M)"
  - "Deltas divergent (Base +0.76pp vs SO400M −3.80pp), not systematic → implied 3-seed-mean ordering cannot be assumed; all 3 seeds should be measured before trusting the mean"

patterns-established:
  - "Measurement-only quick task: retrain + eval to scratch, compare to canonical, state verdict WITHOUT making the A/B decision or editing the paper"

requirements-completed: [QUICK-260601-okz]

duration: 13min
completed: 2026-06-01
---

# Quick 260601-okz: XD Smoothness-Fix Measurement Summary

**Measured the smoothness-axis fix (mil_loss dim1, f89910b) on both XD gated contenders at seed 42: Base ΔAP +0.76pp (negligible) but SO400M ΔAP −3.80pp (material) with a seed-42 AP ordering flip — verdict MATERIAL.**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-06-01T09:46:30Z
- **Completed:** 2026-06-01T09:59:40Z
- **Tasks:** 3
- **Files modified:** 0 committed (3 scratch artifacts created under gitignored `results/_smoothfix/`)

## Accomplishments
- Confirmed both live XD configs match their canonical config snapshots bit-for-bit (feature paths, clip_dim, all hyperparams).
- Retrained both XD gated contenders (SigLIP2 Base + SO400M, seed 42) on current main (corrected smoothness) to scratch, then evaluated each on the XD test split.
- Both fixed evals verified at `n_frames = 2,313,024` (full XD length, no truncation) — matches canonical exactly.
- Quantified XD-AP exposure: Base negligible, SO400M material; produced the comparison report with a MATERIAL verdict, stated as a measurement finding only (no A/B decision, no paper edits).

## Comparison Table (canonical buggy vs fixed, seed 42)

| backbone | canonical AP (buggy) | fixed AP | Δ_AP (pp) | canonical AUC | fixed AUC | Δ_AUC (pp) |
|----------|----------------------|----------|-----------|---------------|-----------|------------|
| Base (SigLIP2 1536-d) | 0.7192 | 0.7268 | **+0.76** | 0.9185 | 0.9188 | +0.03 |
| SO400M (2304-d)       | 0.7377 | 0.6997 | **−3.80** | 0.9315 | 0.9192 | −1.23 |

Full precision — Base AP 0.719235→0.726817, AUC 0.918486→0.918753; SO400M AP 0.737667→0.699698, AUC 0.931484→0.919171.

### Analysis
1. **Δ_AP:** Base +0.76pp (within ~2.8-2.9pp seed-std → negligible alone); SO400M −3.80pp (exceeds seed-std, ~1.3× → not noise).
2. **s42 ordering FLIPS:** canonical SO400M (0.7377) > Base (0.7192); fixed Base (0.7268) > SO400M (0.6997). The fix swaps the seed-42 rank.
3. **Implied 3-seed-mean ordering AT RISK:** deltas are divergent (opposite signs, ~4.6pp apart), not systematic. The previously reported mean ordering (Base 74.70 > SO400M 73.80) cannot be assumed to hold; all 3 seeds should be measured before trusting the mean.
4. **Seed-std context:** Base |Δ|=0.76pp within ~2.8-2.9pp; SO400M |Δ|=3.80pp beyond it. AUC moves smaller (AP more score-calibration-sensitive than ROC-AUC on XD).
5. **Verdict: MATERIAL** — large SO400M |Δ_AP| OR ordering flip ⇒ MATERIAL per the plan's decision rule. XD needs a full retrain (all seeds, both contenders) + Table-2 re-propagation before the corrected numbers can be trusted. (Measurement finding only — no A/B decision, no paper edits.)

## Task Commits

No code/result commits from this task — by design:
- The code fix is already committed on main at `f89910b` (prior quick task 260601-o55).
- `results/_smoothfix/*` and `xd_measurement.md` are gitignored scratch (verified via `git check-ignore`).
- SUMMARY / STATE / PLAN are committed by the orchestrator.

1. **Task 1: Confirm configs match canonical snapshots** — no commit (verification only); "CONFIGS MATCH SNAPSHOTS" printed.
2. **Task 2: Fixed retrains + XD test evals to scratch** — no commit (gitignored scratch).
3. **Task 3: Write comparison report + verdict** — no commit (gitignored scratch).

## Files Created/Modified
- `results/_smoothfix/xd_base_fixed_s42/` — fixed SigLIP2 Base run (best_model.pth, eval_metrics.json, train_log.csv, config_snapshot.json); scratch/gitignored. Best epoch 38, val_loss 0.1457.
- `results/_smoothfix/xd_so400m_fixed_s42/` — fixed SO400M run; scratch/gitignored. Best epoch 30, val_loss 0.1311.
- `results/_smoothfix/xd_measurement.md` — comparison table + ordering checks + verdict; scratch/gitignored.

## Decisions Made
- Used the canonical (buggy) XD eval_metrics directly as the buggy control (XD training is bit-exact deterministic via `set_deterministic`, proven on the UCF control) — no separate buggy re-run.
- Verdict MATERIAL (not NEGLIGIBLE) because SO400M ΔAP exceeds seed-std and the s42 AP ordering flips with divergent (non-systematic) deltas.

## Deviations from Plan
None - plan executed exactly as written. (The smoothness fix was already on main per the constraint; this task only retrained + measured. No re-edit of the loss.)

## Issues Encountered
- `conda run -n vcc-main python -c "<multi-line script>"` fails on this Windows/conda setup (AssertionError: arguments contain newlines). Resolved by writing the delta computation to a temporary scratch `.py` file, running it, then deleting it. The plan's single-line verification `-c` commands (Task 1/2/3) ran fine.

## Next Phase Readiness
- Measurement complete. The MATERIAL verdict + divergent-delta finding is the input for whoever owns the A/B decision and the XD Table-2 retrain call — those are explicitly out of scope here.
- No canonical artifacts, paper, tables, or figures were touched. `results/xd_*` canonical runs are untouched.

## Self-Check: PASSED
- All artifacts FOUND: both `eval_metrics.json`, both `best_model.pth`, `xd_measurement.md`, and this SUMMARY.
- All three scratch artifacts confirmed gitignored via `git check-ignore` (not committable).
- `git status --short results/` empty — canonical `results/xd_*` untouched, nothing staged.
- No code/result commits made (code fix already at f89910b; scratch is gitignored).

---
*Phase: quick-260601-okz*
*Completed: 2026-06-01*
