---
quick_id: 260610-bed
status: in-progress
date: 2026-06-10
---

# Quick Task 260610-bed: Paper P1–P7 confirmed corrections

**Source:** `.planning/REVIEW-2026-06-10.md` §2 (7 adversarially-verified MEDIUM paper
findings, 0 refuted). All quotes below verified verbatim against `paper/main.tex` this
session. Editorial/factual only — no canonical numbers change. Rebuild with
`build_paper.ps1 -Clean` after (CLAUDE.md convention). Done inline (high-stakes
exact-number LaTeX), like quick 260607-pap.

## P1 — stale "+13.9" → "+13.2" (3-seed mean), 3 locations
- `:50` abstract, `:333` §4.5, `:386` conclusion. 3-seed mean = +13.2 (+13.92/+12.34/+13.31);
  +13.9 is seed-42-only. The adjacent "+0.8→+1.21" was updated 2026-06-07; this was missed.

## P2 — §5 "TTA and the LayerNorm barrier" stale rewrite (`:348`)
- Replace the disproven BN/LN "distributional memory" mechanism with §4.5's corrected one:
  gate+head frozen, only LN affine (γ,β; 1,536 scalars) adapt, shift lives upstream in
  frozen features, affine updates too small to reorder rank-based AUC; NORM/CORAL
  rank-disruptive; disc_reweight is the demonstrated positive path. No dangling \ref.

## P3 — "SO400M trained on 400M+ samples" wrong (= ~400M params), 3 locations
- `:142` backbone list → "shape-optimized ~400M-parameter SigLIP2 encoder (SoViT-400M)".
- `:289` §4.4 + `:344` Discussion → drop "broader data distribution (400M+ samples)"
  rationale (all SigLIP2 variants share WebLI, stated at `:145`); reframe as capacity /
  shape-optimization.

## P4 — `:344` "SO400M for XD-Violence visual-only" contradicts Table 2 (Giant 76.8 > SO400M 76.6)
- → "SO400M for XD-Violence under gated fusion". (`:384` already correct.)

## P5 — XD category codes wrong (`:206`)
- "Riot (B3)" — dataset has no B3. Official (xd_annotations.py:42-58): B1 Fighting,
  B2 Shooting, **B4 Riot, B5 Abuse, B6 Car Accident, G Explosion**.

## P6 — "none in XD-Violence" <64 frames false (`:134`)
- One 34-frame XD train video excluded (v=Gm73TwtUyGY...). → "one in XD-Violence".

## P7 — trailing-frame coverage claim false for XD (`:217`)
- UCF repeats final snippet score over the full-length grid; XD evaluates the
  snippet-aligned portion (drops trailing partial window). Qualify per-dataset.

## Verify
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean`
  → clean rebuild, 0 errors / 0 undefined refs; confirm "+13.9" gone, page count noted.
