---
quick_id: 260610-4cj
slug: m3-commit-ucf-total-frames-manifest-wire
status: complete
date: 2026-06-09
commit: 4ddda56
---

# Quick Task 260610-4cj — Summary

## What changed (Option A: manifest + fallback)

The UCF 82.5% AUC headline now reproduces from git alone — no off-repo boundary data needed.

- **`data/ucf_total_frames.json`** (new, committed, ~45KB): `{video_id: total_frames}` for
  all 1900 UCF videos, distilled from the off-repo boundary JSONs. Covers all 254 evaluated
  videos (0 missing).
- **`scripts/build_ucf_frames_manifest.py`** (new): the one-time generator (documents provenance).
- **`src/evaluate.py`**: added a manifest fallback tier — boundaries-dir JSON → committed
  manifest → truncated (warn once). Backward-safe: when `snippet_boundaries_dir` is configured,
  the per-video JSON still wins and behavior is byte-identical.
- **`scripts/recompute_fulllength_ucf.py`**: same fallback in `_load_boundaries_total_frames`;
  startup guard relaxed to proceed when the boundaries dir is absent but the manifest is present
  (so a reviewer with only the repo can run it).

## Verification (both on the giant s42 run, with a nonexistent boundaries dir)

1. **recompute gate PASS**: `new_auc=0.824904 (expected ~0.8249, d=+0.000004)`,
   `new_ap=0.273712`; truncated 0.8323 → full-length 0.8249, n_frames 1,010,560 → 1,097,050, 0 skipped.
2. **fresh `evaluate.py --run-dir <committed snapshot>`** (the real reviewer path): wrote
   `auc=0.824904 ap=0.273712 n_frames=1097050 n_videos=254` — the headline, via the manifest
   fallback, instead of the truncated 0.8323/1,010,560.

Both verifications ran read-only / into temp dirs (now deleted); **no canonical artifact was touched.**

## Commit

`4ddda56` fix(eval): commit UCF total-frames manifest + full-length fallback (M3)

## Notes / optional follow-ups

- No paper edit needed — Option A makes the headline reproducible, so the conclusion's
  reproducibility claim now holds for UCF. A one-line repro note (`python src/evaluate.py
  --run-dir ...` → 82.5%) could be added to a README if desired.
- XD has an analogous ~0.74% trailing-window truncation (audit `xd-stale-gt-comment`, LOW); its
  AP impact is negligible and there is no full-length correction for XD. Out of scope here; a
  future symmetric XD manifest+fallback would close it for completeness.
