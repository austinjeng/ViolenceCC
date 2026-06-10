---
quick_id: 260610-bed
status: complete
date: 2026-06-10
commit: 9218dd2
---

# Quick Task 260610-bed: Paper P1–P7 corrections — SUMMARY

**Status:** Complete. All 7 confirmed paper findings fixed (`paper/main.tex`,
commit `9218dd2`). PDF rebuilds clean: **10 pages, 0 errors, 0 undefined refs**.
Editorial/factual only — no canonical numbers change. Headlines UCF 82.5 / XD 78.7
intact.

## Edits (11 string edits across 7 findings)

| # | Finding | Locations | Change |
|---|---------|-----------|--------|
| P1 | stale seed-42 peak | :50, :333, :386 | `+13.9` → `+13.2` (3-seed mean) |
| P2 | §5 LN-barrier stale | :348 | rewrote to match §4.5 (frozen gate/head, LN affine 1,536 too small to reorder rank-AUC, shift upstream, disc_reweight = positive path); removed disproven BN/LN "distributional memory" story |
| P3 | "400M+ samples" wrong | :142, :289, :344 | → "shape-optimized ~400M-parameter (SoViT-400M)" / capacity-fit framing |
| P4 | SO400M "visual-only" | :344 | → "under gated fusion" (matches Table 2 + :384) |
| P5 | XD category codes | :206 | no B3; → B1/B2/**B4/B5/B6/G** |
| P6 | "none in XD" <64 | :134 | → "one in XD-Violence" |
| P7 | trailing-frame claim | :217 | qualified per-dataset (UCF pad / XD snippet-aligned) |

## Verification

- `grep` confirms 0 remaining: `13.9`, `400M+ samples`, `broader data distribution`,
  `distributional memory`, `Riot (B3)`, `none in XD-Violence`, `XD-Violence visual-only`.
- `build_paper.ps1 -Clean` → "Output written on main.pdf (10 pages)"; log has no
  `^!` errors and no Undefined references/citations.
- 3 × `+13.2` present in main.tex.

## Notes

- P2 added no dangling `\ref` (review caution from prior edits).
- Page count unchanged at 10 (within prior state; CGW page-limit decision still the
  user's, unchanged by this task).
- Build artifacts (main.pdf etc.) are gitignored — not committed.
