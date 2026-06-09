---
quick_id: 260610-aqm
status: in-progress
date: 2026-06-10
---

# Quick Task 260610-aqm: Add Pri-1 3-seed ablation queue

**Source:** `.planning/REVIEW-2026-06-10.md` §5 Pri-1 (RECOMMEND tier). The 06-09
audit showed single-seed ablation rows are an active risk class (two single-seed
results were killed as artifacts). This task adds the runner queue that lets the
user 3-seed the 26 currently-single-seed ablation configs. It does NOT launch GPU
work — that is the user's to run in a visible terminal (no headless long jobs).

## Background (verified this session)

- `RunSpec(dataset, variant, seed, config, cache_variant="")`; `run_name =
  {dataset}_{variant}[_{cache_variant}]_s{seed}` (`scripts/run_ablations.py:65-94`).
- The 26 configs exist ONLY at seed=42, defined at `run_ablations.py:157-270`
  (phase4/4c main+pooling, phase8/9/10 main+pooling): Late Fusion (8), GF 2-Person
  (8), GF Mean-Only/clip_mean (8), Skeleton Only (2).
- Runner has NO subset-by-config/seed flag → a new queue is the correct mechanism.
- Seeds {123, 2024} only; seed=42 already covered, not duplicated (D-27/D-28).
- Queue-count pin `tests/test_run_ablations.py:122` expects 266 and is ALREADY red
  (count drifted pre-change; adding 52 raises it further).

## Task 1 — Add `pri1_ablations_seeds` queue

- **files:** `scripts/run_ablations.py`
- **action:** Insert `QUEUES["pri1_ablations_seeds"] = [...]` (52 RunSpecs, cloned
  verbatim from lines 157-270 with seed 42 → 123 and 42 → 2024) immediately after
  the `m7_visual_seeds` block (after line 303), before the Phase 7 section comment.
  Provenance comment block included.
- **verify:** `C:\Anaconda\envs\vcc-main\python.exe scripts/run_ablations.py
  --queue pri1_ablations_seeds --dry-run --no-preflight` prints exactly 52
  `[dry-run] would run ...` lines, all with `_s123` or `_s2024` suffixes.
- **done:** 52 unique run_names resolve; no import/parse error.

## Task 2 — Fix queue-count pin

- **files:** `tests/test_run_ablations.py`
- **action:** Run `pytest tests/test_run_ablations.py`, read the exact new
  unique-run-name count from the assertion, update the pin (line 122) to that value.
  Do NOT touch the TTA pin or other red tests (separate batch).
- **verify:** `pytest tests/test_run_ablations.py` green.
- **done:** test_run_ablations.py passes.

## Out of scope

- Launching the 52-run job (user runs in visible terminal).
- C1/C2/C3, TTA pin, paper P1-P7 (separate batches B and C).
