---
quick_id: 260726-kzh
description: Shorten thesis LoF/LoT entries via \caption[short]{full} optional arguments
date: 2026-07-26
mode: quick
planner: Fable (session directive — orchestrator plans, Opus subagents execute, orchestrator verifies)
---

# Quick Task 260726-kzh: Shorten thesis List of Figures / List of Tables entries

## Problem

`thesis/main.tex` emits `\listoffigures` / `\listoftables`, and every in-build caption
except ch07:319 uses the single-argument `\caption{...}` form, so the Lists reproduce
full multi-sentence captions. Fix: add a short optional argument —
`\caption[Short entry]{Full caption unchanged}` — for every long caption. The body
captions must remain byte-identical.

## Scope

In-build chapter files only (appendices archived out of build 2026-07-14; subfigure
captions excluded — already short, not listed in LoF). 22 captions across 6 files.

## Style contract (locked)

- Short caption: concise noun phrase, target ≤ 10 words, one printed LoF/LoT line
  (two max).
- No trailing period — matches existing precedent at ch07_discussion.tex:319
  (`\caption[Fair-subset (regime-matched) comparison]{...}`).
- No `\cite`, `\label`, `\footnote`, `\ref` inside the short argument. Simple math
  ($\Delta$, t-SNE etc.) allowed but avoided where possible.
- Insert ONLY the `[...]` optional argument. Zero changes to the full caption text,
  labels, or anything else.

## Authoritative edit map (short captions are final — apply verbatim)

### thesis/chapters/ch02_related_work.tex (1 edit)
| Line | Label | Short caption |
|---|---|---|
| 162 | tab:rw-taxonomy | `Design-space summary of surveyed weakly supervised VAD methods` |

### thesis/chapters/ch03_methodology.tex (1 edit)
| Line | Label | Short caption |
|---|---|---|
| 22 | fig:architecture | `Overview of the dual-modal gated fusion pipeline` |

### thesis/chapters/ch04_experimental_setup.tex (3 edits)
| Line | Label | Short caption |
|---|---|---|
| 174 | tab:corruption-params | `UCF-Crime-C corruption severity parameterization` |
| 359 | tab:efficiency-heads | `Trainable-head efficiency benchmarks (RTX 4090)` |
| 385 | tab:efficiency-backbones | `Frozen extraction backbones and parameter counts` |

### thesis/chapters/ch05_results_fusion.tex (9 edits)
| Line | Label | Short caption |
|---|---|---|
| 40 | tab:ucf-ablation | `Ablation study on UCF-Crime (AUC, three seeds)` |
| 64 | tab:xd-ablation | `Ablation study on XD-Violence (AP, three seeds)` |
| 191 | (backbone comparison fig) | `Performance comparison across four backbones and three fusion variants` |
| 435 | (Fighting047 fig) | `Frame-level anomaly scores on the Fighting047 test video` |
| 465 | (per-category fig) | `Per-category performance for skeleton-only, visual-only, and gated fusion` |
| 499 | fig:gate-by-category | `Mean gate activation by category for the gated fusion model` |
| 520 | fig:tsne | `t-SNE projection of fused video-level test-set representations` |
| 555 | tab:failure-cases | `Five worst-ranked anomalous test videos (UCF-Crime)` |
| 605 | fig:score-hist | `Frame-score distributions for anomalous versus normal frames` |

### thesis/chapters/ch06_results_tta.tex (7 edits)
| Line | Label | Short caption |
|---|---|---|
| 39 | (source-only heatmap fig) | `Source-only AUC across the 20 UCF-Crime-C conditions` |
| 153 | tab:tent-sar-null | `Entropy-minimization TTA null result on UCF-Crime-C` |
| 237 | tab:tta | `Test-time adaptation on UCF-Crime-C, source-only versus reweighting` |
| 259 | (TTA bars fig) | `TTA gains across four backbones on UCF-Crime-C` |
| 286 | tab:tta_breakdown | `Discriminative-reliability reweighting gain by corruption type` |
| 311 | (per-condition gain fig) | `Per-condition gain of discriminative-reliability reweighting` |
| 327 | fig:corruption-disc-reweight | `Absolute AUC under discriminative-reliability reweighting` |

### thesis/chapters/ch07_discussion.tex (1 edit; line 319 already short-form — DO NOT TOUCH)
| Line | Label | Short caption |
|---|---|---|
| 226 | tab:sota-full | `Published-numbers comparison on UCF-Crime and XD-Violence` |

## Tasks

1. **Apply short captions** — 6 parallel Opus agents, one per chapter file, each
   converting `\caption{` → `\caption[<short>]{` per the map above.
   Verify per file: `\caption[` count equals expected (ch02:1, ch03:1, ch04:3,
   ch05:9, ch06:7, ch07:2 incl. pre-existing 319).
2. **Rebuild thesis** — `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean`
   (clean build so stale .lof/.lot cannot mask results). Verify: exit 0,
   thesis/main.pdf regenerated, no LaTeX errors in main.log.
3. **Verify (orchestrator)** — git diff shows ONLY `[...]` insertions on \caption
   lines; thesis/main.lof + main.lot entries match the map; page count sane
   (~128pp); commit code change atomically, then docs commit + STATE.md row.

## Verification gates

- [ ] 22 new `\caption[` occurrences (23 total incl. ch07:319)
- [ ] Full captions byte-identical (diff audit)
- [ ] Clean build exit 0, no `!` errors, no undefined refs
- [ ] main.lof / main.lot show only short entries, each ≤ 2 lines
- [ ] PDF page count within ±2 of previous (front matter Lists shrink)
