---
quick_id: 260622-ukd
slug: fix-t3-1-light-wvad-xd-ap
date: 2026-06-22
status: in-progress
type: quick
---

# Quick Task 260622-ukd — Fix HIGH finding T3-1: fabricated Light-WVAD XD-Violence AP

## Problem

The 2026-06-22 review (HIGH finding **T3-1**) found that the SOTA comparison credits
**Light-WVAD** (`\cite{wang2024lightwvad}`, Wang/Zhou/Guan, Neurocomputing 2024 = arXiv 2310.05330)
with **77.3% XD-Violence AP**. The cited paper evaluates **only UCF-Crime and ShanghaiTech and
reports only AUC** — it never reports any XD-Violence result and no AP metric anywhere.
The 84.7% UCF AUC cell is correct and stays; the 77.3 XD AP is unsupported and must be removed.

The number is load-bearing: it appears in `paper/main.tex` Table 4 + on-par prose, in **both**
tables of `paper/sota_comparison_full.tex`, and in two prose passages of the fragment.

Folded in: directly-related LOW finding **T3-4** — the bib `title` for `wang2024lightwvad` is wrong.

## Tasks

### Task 1 — Remove the fabricated XD AP everywhere; fix bib title
**Files:** `paper/main.tex`, `paper/sota_comparison_full.tex`, `paper/references.bib`

- `main.tex:406` — Table 4 row: change Light-WVAD XD AP cell `77.3` → `---` (keep UCF `84.7`).
- `main.tex:385` — prose: delete `, and Light-WVAD~\cite{wang2024lightwvad} (77.3\%)` from the
  XD on-par list. The line-385 UCF mention "Light-WVAD 84.7\%" (UCF AUC) STAYS.
- `sota_comparison_full.tex:118` — full table: XD AP `77.3` → `---`.
- `sota_comparison_full.tex:197` — fair-subset table: XD AP `77.3` → `---`.
- `sota_comparison_full.tex:209` — prose: drop `Light-WVAD (77.3), ` from the XD on-par list.
- `sota_comparison_full.tex:274` — prose: drop `, and Light-WVAD (77.3\%, Neurocomputing 2024)`
  from the XD on-par list. The UCF band mention `Light-WVAD (84.7\%)` at :277 STAYS.
- `references.bib:212` — title → `A Lightweight Video Anomaly Detection Model with Weak Supervision and Adaptive Instance Selection`.

**Verify:** `grep -n "77.3" paper/main.tex paper/sota_comparison_full.tex` returns no Light-WVAD XD
row/prose; `grep "84.7" ...` still present (UCF cells intact).
**Done:** all fabricated-77.3 occurrences removed; UCF 84.7 cells intact; bib title corrected.

### Task 2 — Rebuild and confirm compile
**Action:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean`
**Verify:** `paper/main.pdf` rebuilds with exit 0; headlines UCF 82.5% / XD 78.7% unchanged in PDF.
**Done:** paper compiles clean; no new undefined refs/citations.

## Must-haves
- truths: Light-WVAD has no published XD-Violence AP; the 84.7 UCF AUC is real.
- artifacts: corrected `main.tex`, `sota_comparison_full.tex`, `references.bib`; rebuilt `main.pdf`.
- key_links: review-2026-06-22.html (T3-1, T3-4).
