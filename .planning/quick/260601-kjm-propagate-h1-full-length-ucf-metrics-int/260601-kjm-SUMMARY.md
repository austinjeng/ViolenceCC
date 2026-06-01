---
phase: quick-260601-kjm
plan: 01
subsystem: eval / paper
tags: [H1, ucf-crime, full-length-eval, propagation, paper]
requires: [results/h1_recompute/ucf_fulllength_comparison.csv]
provides:
  - "Canonical full-length UCF artifacts (eval_metrics.json, eval_scores.npz) + .pre_h1.bak backups"
  - "results-index.csv ucf_* rows on full-length auc/ap/n_frames"
  - "Regenerated phase10 charts CSVs, tables_generated.tex Table 1, 3 UCF figures"
  - "paper/main.tex prose + inline Table 1 synced to full-length UCF numbers"
affects: [paper/main.tex, paper/tables_generated.tex, results-index.csv]
tech-stack:
  added: []
  patterns: ["backup-before-overwrite (idempotent *.pre_h1.bak)", "atomic .tmp -> os.replace", "recompute reads from .pre_h1.bak source-of-truth on re-run"]
key-files:
  created: []
  modified:
    - scripts/recompute_fulllength_ucf.py
    - results/results-index.csv
    - results/phase10_charts/backbone_comparison_4way.csv
    - results/phase10_charts/seed_stability_4way.csv
    - paper/tables_generated.tex
    - paper/main.tex
    - paper/figures/fig_backbone_comparison.pdf
    - paper/figures/fig_temporal_scores.pdf
    - paper/figures/fig_gating_distribution.pdf
decisions:
  - "Recompute reads .pre_h1.bak when present (idempotent re-run): the overwritten eval_scores.npz is full-length tail-padded and no longer a per-snippet repeat, so re-running --write on the live npz fails the divisible-by-640 reconstruction. Sourcing from the backup makes the canonical overwrite deterministic and re-assertable."
  - "Inline Table 1 deltas follow the generated table (Visual Only +1.2, Gated Fusion +1.2), not the plan's literal example text (+1.3 / +1.1): the plan declares the generated table authoritative on rounding differences and mandates byte-identical inline rows."
  - "Restored fig_tta_comparison.pdf and the 3 phase10 *.png to HEAD: generate_pub_figures.py / generate_phase10_charts.py regenerate ALL outputs, but the plan's commit file lists exclude these (TTA content must not change; PNGs are intermediate). Restoring keeps the tree clean and honors the exact commit spec."
metrics:
  duration: ~30min
  completed: 2026-06-01
---

# Quick Task 260601-kjm: Propagate H1 Full-Length UCF Metrics Summary

One-liner: Made the gated full-length UCF recompute (giant_s42 -> AUC 0.8249 / AP 0.2737) the published reality across canonical per-run artifacts, intermediate CSVs/tables/figures, and paper prose + inline Table 1, while leaving XD and TTA mathematically and byte-identically unchanged.

## Post-Write Gate Result

`conda run -n vcc-main python scripts/recompute_fulllength_ucf.py --write --boundaries-dir E:/snippets/ucf`

```
GATE PASS: H1 GATE ucf_gated_fusion_giant_s42: new_auc=0.824904 (expected ~0.8249, d=+0.000004)  new_ap=0.273712 (expected ~0.2737, d=+0.000012)
--write: overwriting canonical UCF artifacts (backup-before-overwrite)
  results-index.csv: updated 29 ucf_* rows
POST-WRITE GATE ucf_gated_fusion_giant_s42 (on-disk): auc=0.824904 ap=0.273712
POST-WRITE GATE PASS: ucf_gated_fusion_giant_s42 on disk within tol.
```

On-disk confirmation: `results/ucf_gated_fusion_giant_s42/eval_metrics.json` reads `auc=0.8249, ap=0.2737, n_frames=1097050`, with all non-{auc,ap,n_frames,per_category} keys preserved (config_hash, checkpoint_sha, snippet_auc, video_auc all present). All 29 ucf_* runs have `eval_metrics.json.pre_h1.bak`, `eval_scores.npz.pre_h1.bak`, and `results-index.csv.pre_h1.bak`. Idempotency verified: two further `--write` runs printed NO `backup:` lines (backups never re-clobbered, mtimes unchanged) and re-asserted the gate (RC 0).

## Regenerated Table 1 Block (tables_generated.tex, byte-identical to main.tex inline Table 1)

```latex
% Table 1: UCF-Crime Ablation Results (AUC)
\begin{table*}[t]
\caption{Ablation study on UCF-Crime. AUC (\%) reported for each fusion variant across four visual backbones. Gated Fusion rows show mean$\pm$std over three seeds (42, 123, 2024). Best result per row in \textbf{bold}. $\Delta$ relative to CLIP ViT-B/16 baseline.}
\label{tab:ucf-ablation}
\begin{tabular}{l c c c c c}
\toprule
Variant & CLIP ViT-B/16 & SigLIP2 Base & SigLIP2 SO400M & SigLIP2 Giant & Best $\Delta$ \\
\midrule
Skeleton Only & \textbf{71.8} & --- & --- & --- & --- \\
Visual Only & 81.1 & 78.3 & 80.9 & \textbf{82.4} & $\uparrow$+1.2 \\
\midrule
Late Fusion & 78.6 & 79.5 & 80.0 & \textbf{80.8} & $\uparrow$+2.2 \\
Gated Fusion & 81.4$\pm$0.3 & 79.0$\pm$0.1 & 81.3$\pm$0.3 & \textbf{82.5$\pm$0.4} & $\uparrow$+1.2 \\
GF 2-Person & 81.1 & 78.7 & 81.3 & \textbf{82.7} & $\uparrow$+1.6 \\
GF Mean-Only & 81.1 & 79.4 & 81.8 & \textbf{83.0} & $\uparrow$+1.9 \\
\bottomrule
\end{tabular}
\end{table*}
```

Regenerated `seed_stability_4way.csv` UCF Giant Gated Fusion 3-seed AUC = {0.8249, 0.8292, 0.8222}, mean = 0.8254 (gate `abs(m-0.8254)<0.001` PASSED). Table 1 contains `82.5` (Giant Gated) and `83.0` (GF Mean-Only Giant).

## Table 2 / Table 3 Unchanged (XD / TTA invariance)

Snapshotted current `tables_generated.tex` to `tables_generated.tex.prepropagate` before regenerating, then diffed the `tab:xd-ablation` and `tab:tta` blocks against the regenerated file:

```
tab:xd-ablation IDENTICAL
tab:tta IDENTICAL
tab:ucf-ablation CHANGED (expected)
```

Both XD and TTA blocks are byte-identical to the pre-propagation snapshot. results-index.csv `xd_gated_fusion_s42` row unchanged (auc=0.9199907242272506, n_frames=2313024); TTA `source_only_*`/`tent`/`sar` rows unchanged (n_frames still 1010560). Snapshot removed after confirmation.

## main.tex Edits Applied (A--H)

- **A** Abstract: `83.3\% AUC on UCF-Crime (SigLIP2 Giant)` -> `82.5\% ...`.
- **B** Inline Table 1: six data rows replaced to match the regenerated `tab:ucf-ablation` block byte-for-byte (deltas follow generated table: Visual Only +1.2, Gated Fusion +1.2). Skeleton Only (71.8) and the \midrule kept.
- **C** Sec 4.3: CLIP gated `82.0->81.4`, visual `81.7->81.1`; Giant gated `83.3->82.5`, visual `83.1->82.4`; reworded `The improvement is more pronounced with stronger backbones` -> `The same pattern holds for the strongest backbone` (the CLIP margin +0.3 now exceeds the Giant margin +0.1, so the old framing is false).
- **D** Sec 4.3: CLIP late fusion `78.7->78.6`, visual `81.7->81.1`, drop `3.0->2.5` percentage points.
- **E** Sec 4.4: `83.1% visual-only, 83.3% gated fusion, and 83.6% with mean-only pooling` -> `82.4% / 82.5% / 83.0%`.
- **F** Sec 4.4: std range `0.2--0.4\% AUC` -> `0.1--0.4\% AUC`.
- **G** Sec 6 Limitations: best UCF `83.6\%` -> `83.0\%`.
- **H** Sec 7 Conclusion: `83.3% gated fusion, 83.6% mean-only` -> `82.5% / 83.0%`.

DO-NOT-CHANGE invariants confirmed still present and untouched: 71.8 (skeleton), 41.3 / 65.5 / 71.0 / 5.5pp / 74.7 / 77.6 / 76.3 (XD), +0.6% (CLIP SAR TTA).

## Structural-Check Result

- Brace balance: 299 `{` == 299 `}` -> True.
- Abstract = 82.5; Conclusion = 82.5/83.0; Limitations = 83.0; Sec 4.4 std = 0.1--0.4 -> all present, old figures absent.
- `\cite`/`\ref`/`\label` key sets identical to HEAD (0 added, 0 removed) -> no broken citations/refs; tab:ucf-ablation / tab:xd-ablation / tab:tta labels still resolve.
- Inline Table 1 data rows == `tables_generated.tex` tab:ucf-ablation data rows -> byte-identical (header row included).
- 3 UCF figures regenerated (mtimes updated): fig_backbone_comparison.pdf (63,852 B), fig_temporal_scores.pdf (34,011 B, selected RoadAccidents127), fig_gating_distribution.pdf (64,432 B). fig_tta_comparison.pdf restored to HEAD (TTA content unchanged).

ALL STRUCTURAL CHECKS PASSED.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Idempotent re-run failed reconstruction after first --write**
- **Found during:** Task 1 (idempotency verification, 2nd --write run).
- **Issue:** `_recompute_ucf_run` reconstructs per-snippet scores from `eval_scores.npz` via `arr.reshape(n_snip, 640)[:,0]`, asserting length divisible by 640. After the first `--write`, the live npz stores full-length tail-padded arrays (e.g. 1420 frames = 142*10) that are NOT per-snippet repeats and NOT divisible by 640, so a second `--write` raised `AssertionError: frame array length 1420 not divisible by block 640`. The plan explicitly requires re-running `--write` to "produce identical canonical files" and "re-assert the gate".
- **Fix:** `_recompute_ucf_run` now prefers `eval_scores.npz.pre_h1.bak` / `eval_metrics.json.pre_h1.bak` as the source-of-truth when they exist (set by a prior `--write`), so the recompute always operates on the original pre-H1 per-snippet-repeat data. Re-runs are now deterministic and re-assert the gate (verified RC 0, no backups re-clobbered).
- **Files modified:** scripts/recompute_fulllength_ucf.py
- **Commit:** 8f148dd

### Plan-text vs generated-table rounding
The plan's EDIT B example listed Visual Only delta `+1.3` and Gated Fusion delta `+1.1`; the regenerated table emits `+1.2` for both. Per the plan ("the generated table is authoritative if rounding differs ... inline Table 1 MUST be byte-identical to the regenerated tables_generated.tex"), the generated values were used. Not a deviation in intent.

## Self-Check: PASSED

- scripts/recompute_fulllength_ucf.py: FOUND, contains `--write`.
- results/ucf_gated_fusion_giant_s42/eval_metrics.json: auc=0.8249, ap=0.2737, n_frames=1097050.
- Commit 8f148dd (feat/eval): FOUND. Commit 4c352b8 (docs/paper): FOUND.
- XD/TTA Table 2/3 byte-identical; inline Table 1 == generated Table 1; braces balanced; cite/ref keys unchanged.
