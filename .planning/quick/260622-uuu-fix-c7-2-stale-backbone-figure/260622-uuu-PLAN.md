---
quick_id: 260622-uuu
slug: fix-c7-2-stale-backbone-figure
date: 2026-06-22
status: in-progress
type: quick
---

# Quick Task 260622-uuu — Fix HIGH finding C7-2 / T5-1: stale backbone-comparison figure

## Problem

The 2026-06-22 review (HIGH **C7-2**, dup **T5-1**): `paper/figures/fig_backbone_comparison.pdf`
(included at `main.tex:282`) shows **single-seed (s42) bar values** but its caption (`main.tex:283`)
claims **"Visual Only and Gated Fusion bars are three-seed means … Late Fusion is single-seed."**
The figure predates the Pri-1 3-seed runs, so its bars disagree with the now-3-seed Tables 1/2 —
e.g. XD gated SO400M **79.7** (fig) vs **78.7** (Table 2, the XD headline backbone), and XD gated
Giant **73.6** vs **76.8** (a 3.2pp visible mismatch). The caption also calls Late Fusion
single-seed, but Tables 1/2 now report it over 3 seeds.

**Root cause:** `scripts/generate_phase10_charts.py:build_comparison_table` reads a single `_s42`
run per cell (`COMPARISON_MAP` hardcodes `_s42` names) — no seed averaging — so the generated
`results/phase10_charts/backbone_comparison_4way.csv` is single-seed. The figure
(`generate_pub_figures.py`) faithfully renders those single-seed values.

## Tasks

### Task 1 — Make the chart generator average over seeds (fix root cause)
**File:** `scripts/generate_phase10_charts.py`
- Add `_seed_mean(idx, s42_name, metric)` helper: mean of `metric` over the `{_s42,_s123,_s2024}`
  family for a run given by its `_s42` member (skip absent siblings; fall back to single run).
- `build_comparison_table` uses `_seed_mean(...)` for every CLIP/SigLIP2/SO400M/Giant AUC/AP cell
  (deltas auto-update since they derive from the cell values). `build_seed_table` already per-seed.

**Verify:** re-run regenerates `backbone_comparison_4way.csv` whose Visual Only / Late Fusion /
Gated Fusion cells equal Tables 1/2 to 0.1pp (UCF gated Giant 82.5, XD gated SO400M 78.7, XD gated
Giant 76.8, XD late CLIP 63.9, etc.).
**Done:** CSV bar values == 3-seed table means.

### Task 2 — Regenerate the CSV and the figure
**Action:** `conda run -n vcc-main python scripts/generate_phase10_charts.py` then
`conda run -n vcc-main python scripts/generate_pub_figures.py` (regenerates fig_backbone_comparison.pdf).
**Verify:** figure bar values now match Tables 1/2; `git status` shows only the intended artifacts changed.
**Done:** `paper/figures/fig_backbone_comparison.pdf` refreshed from 3-seed data.

### Task 3 — Correct the caption and rebuild
**File:** `paper/main.tex:283`
- Drop the false "Late Fusion is single-seed" clause; state all three variants are three-seed means
  (Gated Fusion shown with ±std).
**Action:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean`
**Verify:** clean rebuild; caption now consistent with Tables 1/2; headlines 82.5/78.7 intact.
**Done:** figure + caption + tables mutually consistent.

## Must-haves
- truths: every figure bar is a 3-seed mean equal to its Table 1/2 cell; caption makes no false seed-count claim.
- artifacts: fixed `generate_phase10_charts.py`; regenerated `backbone_comparison_4way.csv` + `fig_backbone_comparison.pdf`; corrected `main.tex` caption; rebuilt `main.pdf`.
- key_links: review-2026-06-22.html (C7-2, T5-1).
