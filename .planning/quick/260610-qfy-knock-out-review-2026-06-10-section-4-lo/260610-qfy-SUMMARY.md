---
quick_id: 260610-qfy
status: complete
date: 2026-06-10
---

# Quick Task 260610-qfy: REVIEW §4 LOW items + PRI checklist — SUMMARY

**Status:** Complete. PRI progress checklist added; all 16 §4 LOW items resolved
(**12 fixed `[x]`, 4 documented-accept `[~]`**). Done via workflow wf_8c1ece10-307
(4 parallel file-groups) + orchestrator verification. Full suite **321 passed / 0 failed**;
paper rebuilds clean (10pp, 0 errors/undefined refs).

## Part 1 — PRI checklist (commit 443ae04)
Added a `[ ]`/`[x]`/`[~]` progress tracker for all 18 Pri items + SKIP tier to
REVIEW-2026-06-10.md §5. Pri 1/5/6/7/9 = done; Pri 3 = deferred-noted; SKIP = `[~]`.

## Part 2 — §4 LOW items

**Fixed `[x]` (12):**
- Paper (main.tex): P1 defined `d_v = 2d`; P2 defined GF 2-Person / GF Mean-Only; P3
  trainable set now "projection, gating, and MIL detection-head"; P4 Table-3 caption
  discloses snippet-aligned grid vs full-length Tables 1-2; P5 "per-condition corruption
  stream" reword.
- TTA code: T9 episodic optimizer-state reset → `defaultdict(dict)` (stateful-safe);
  T10 `strict=False` loads now assert no missing/unexpected keys (catches silent partial
  restores) in tent/sar/evaluate_tta; T11 fixed the dup-`method` log line (now prints backbone).
- Infra: I6 fixed Fig-5 retracted-`≤0.004pp` docstring (figure verified: Source vs Ours
  only, no TENT/SAR bars — consistent with title); I12 `generate_latex_tables.py` always
  re-emits the STALE banner (no silent clobber); I13 added `backbone` to
  `RESULTS_INDEX_COLUMNS` **+ migrated results-index.csv to 18 cols** (byte-precise empty
  backfill of 1014 rows; analysis scripts still reproduce — DictReader robust); D15
  model constructors now warn-log unknown kwargs (non-fatal; allow-lists
  variant/strategy/cache_variant/backbone so config_snapshot replay stays silent).

**Documented / accept `[~]` (4):**
- D7 UCF annotation off-by-one — code comment (0.002pp, cosmetic; indexing unchanged).
- T8 SAR fidelity — code comment documenting the intentional simplification (second-pass +
  EMA omitted; deltas≈0); `self.ema` marked dead. (Optional paper footnote not added — no
  claim depends on perfect SAR fidelity.)
- D14 create_splits iterdir ordering — comment documenting source-of-truth splits + DO-NOT-sort.
- D16 hardcoded paths — comments noting machine-specific/overridable; no config refactor.

(The 4 "test suite RED" §4 inventory items were already `[x]` from Batch B 260610-b6p.)

## Verification
- All 11 touched code files `py_compile` OK; T9/T10 present in all 3 TTA files.
- I13 migration: header+1014 rows now 18 cols, backbone empty for legacy rows;
  `gen_ablation_tables_3seed.py` / `aggregate_pri1_3seed.py` still reproduce (e.g. GF
  Mean-Only Giant 82.51).
- D15 runtime check: typo kwarg warns at both levels but model still builds; replay extras silent.
- `build_paper.ps1 -Clean` → 10pp, 0 errors/undefined. Full `pytest` → 321 passed.

## Handled flags
- evaluate_tta.py concurrent-write (B T10/T11 + C2 D16) — both edits confirmed present,
  non-overlapping, compiles.
- I13 half-migration risk (18-col schema vs 17-col file) — RESOLVED by the CSV migration.
