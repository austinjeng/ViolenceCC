---
quick_id: 260610-aqm
status: complete
date: 2026-06-10
commit: b315108
---

# Quick Task 260610-aqm: Add Pri-1 3-seed ablation queue — SUMMARY

**Status:** Complete. Code committed `b315108`. GPU run NOT launched (user's to run
in a visible terminal).

## What changed

- `scripts/run_ablations.py`: added `QUEUES["pri1_ablations_seeds"]` — 52 RunSpecs
  (26 single-seed ablation configs × seeds {123, 2024}), cloned verbatim from the
  phase4/4c/8/9/10 main+pooling specs (lines 157-270) with seed 42 → 123/2024.
  Covers Late Fusion (8), GF 2-Person (8), GF Mean-Only/clip_mean (8), Skeleton
  Only (2). seed=42 already covered; not duplicated (D-27/D-28).
- `tests/test_run_ablations.py:118-122`: queue-count pin 266 → 334 (comment +
  assertion). The pin was already red (266 claimed vs 282 actual after the
  2026-06-09 `m7_visual_seeds` addition; +52 = 334).

## Verification

- Dry-run: `python scripts/run_ablations.py --queue pri1_ablations_seeds --dry-run
  --no-preflight` → exactly **52** `[dry-run] would run` lines, **26 ×_s123 +
  26 ×_s2024**, all names resolve, no parse/import error.
- `pytest tests/test_run_ablations.py` → **17 passed** (was 16 passed / 1 failed).

## How the user launches the run (visible terminal, RTX 4090)

```powershell
conda activate vcc-main
cd D:\ViolenceCC
python scripts\run_ablations.py --queue pri1_ablations_seeds
```

- ~2–3 GPU-h, 52 runs, sequential. Skips any run with a `.done` marker (resumable).
- Requires cached features at `E:/features/{ucf,xd}/...` (skeleton + clip/siglip2/
  so400m/giant). All frozen/precomputed — no extraction needed.
- Results append to `results/results-index.csv`; per-run dirs under `results/`.
- After it finishes, the single-seed ablation numbers in the paper (UCF 83.0 GF
  Mean-Only, XD 79.9, skeleton-only rows, Late Fusion, GF 2-Person) can be
  reported as 3-seed mean±std.

## Out of scope (next batches)

- Batch B: C1 fixture rename, C2 i3d shuffle, C3 split exclusions, TTA pin,
  train_integration scanner (make full suite green).
- Batch C: paper P1–P7 + rebuild.
