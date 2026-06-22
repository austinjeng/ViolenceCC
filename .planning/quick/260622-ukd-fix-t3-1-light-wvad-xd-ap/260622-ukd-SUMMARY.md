---
quick_id: 260622-ukd
slug: fix-t3-1-light-wvad-xd-ap
date: 2026-06-22
status: complete
commit: f694611
---

# Summary — Quick Task 260622-ukd

Fixed HIGH review finding **T3-1**: the SOTA comparison credited **Light-WVAD**
(`wang2024lightwvad`, Neurocomputing 2024 / arXiv 2310.05330) with a fabricated
**77.3% XD-Violence AP**. That paper evaluates only UCF-Crime and ShanghaiTech and
reports only AUC — it has no XD-Violence result and no AP metric. The correct
84.7% UCF AUC cell was retained everywhere.

## Changes (commit f694611)
- `paper/main.tex`: Table 4 Light-WVAD XD AP `77.3` → `---`; removed Light-WVAD from
  the §6 XD on-par prose. UCF `84.7%` band mention retained.
- `paper/sota_comparison_full.tex`: both tables (full + fair-subset) XD AP `77.3` → `---`
  with "XD not evaluated" notes; removed Light-WVAD from both XD on-par prose passages.
  UCF `84.7%` mentions retained.
- `paper/references.bib` (folds in related LOW finding **T3-4**): corrected the
  `wang2024lightwvad` title to "A Lightweight Video Anomaly Detection Model with Weak
  Supervision and Adaptive Instance Selection".

## Verification
- `grep "77.3"` over main.tex + sota_comparison_full.tex → **no occurrences** (fabricated value gone).
- All UCF `84.7` cells/prose intact.
- `scripts/build_paper.ps1 -Clean` → **main.pdf rebuilt, 11 pages, latexmk converged** (citations resolved on final pass; bbl carries the corrected title).
- Rendered-PDF text check (pages 8–10): on-par prose now "RTFM (77.81%) and MGFN (79.19%)"; **no `77.3`** on the comparison pages.
- Headlines UCF 82.5% / XD 78.7% unchanged.

## Notes
- The XD claim ("on par with RTFM, MGFN") still holds without Light-WVAD.
- Build artifacts (main.pdf, .aux/.bbl/...) are git-ignored and not committed.
