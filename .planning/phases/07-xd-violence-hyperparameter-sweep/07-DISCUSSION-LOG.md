# Phase 7: XD-Violence Hyperparameter Sweep - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 07-xd-violence-hyperparameter-sweep
**Areas discussed:** Sweep grid design, RTFM gap investigation, Sweep infrastructure, Results presentation

---

## Sweep Grid Design

### Learning rate range

| Option | Description | Selected |
|--------|-------------|----------|
| 5e-5 to 5e-4 | 5 values: {5e-5, 1e-4, 2e-4, 3e-4, 5e-4}. Centered around current 1e-4, biased upward for larger XD dataset. | ✓ |
| 1e-5 to 1e-3 (wider) | 5 values log-scale. More exploratory. | |
| 1e-4 to 1e-3 (upward only) | 4 values. Assumes current lr is at or near lower bound. | |

**User's choice:** 5e-5 to 5e-4 (recommended)
**Notes:** None

### k_topk values

| Option | Description | Selected |
|--------|-------------|----------|
| k={1,3,5,7} | 4 values spanning aggressive to inclusive. 5×4=20 runs matches SC #1. | ✓ |
| k={1,2,3,5} | 4 values with finer resolution near current k=3. | |
| k={3,5,7,9} | 4 values upward only. Tests longer video benefit. | |

**User's choice:** k={1,3,5,7} (recommended)
**Notes:** None

### Seed strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Single seed s42 | 20 runs total. Direct comparison with Phase 4c baseline. | ✓ |
| All 3 seeds per config | 60 runs total. Statistically robust but 3× GPU time. | |
| 2 seeds per config | 40 runs total. Middle ground. | |

**User's choice:** Single seed s42 (recommended)
**Notes:** None

### 3-seed confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, 3-seed confirmation | Seeds {42, 123, 2024} on winning config. Standard thesis rigor. | ✓ |
| No, single seed sufficient | Report best s42 result only. | |

**User's choice:** Yes, 3-seed confirmation (recommended)
**Notes:** None

---

## RTFM Gap Investigation

### Investigation goal

| Option | Description | Selected |
|--------|-------------|----------|
| Diagnose and document | Run diagnostics, identify likely cause, document for thesis. Don't close the gap. | ✓ |
| Diagnose and attempt fix | Same diagnostics, plus attempt corrections if fixable cause found. | |
| Minimal check only | Single annotation alignment check. Minimum SC #3 compliance. | |

**User's choice:** Diagnose and document (recommended)
**Notes:** None

### Diagnostics to run

| Option | Description | Selected |
|--------|-------------|----------|
| Annotation alignment check | Compare Wu parser against original XD evaluation protocol. | ✓ |
| Temporal interpolation check | Verify snippet→frame expansion matches published RTFM. | ✓ |
| I3D feature audit | Compare feature statistics against published RTFM features. | ✓ |
| Published code comparison | Diff against RTFM's official XD evaluation code. | ✓ |

**User's choice:** All 4 diagnostics (multi-select)
**Notes:** None

### Fix policy

| Option | Description | Selected |
|--------|-------------|----------|
| Fix only clear bugs | Fix parsing bugs/off-by-one. Document methodological differences only. | ✓ |
| Document only, no fixes | Strictly observational. | |
| Fix anything found | Attempt to close gap regardless of cause. | |

**User's choice:** Fix only clear bugs (recommended)
**Notes:** None

---

## Sweep Infrastructure

### Config generation

| Option | Description | Selected |
|--------|-------------|----------|
| CLI overrides on base config | Use gated_fusion_xd.yaml as template, pass --lr and --k-topk to train.py. Zero new YAML files. | ✓ |
| 20 new YAML files | Generate one YAML per sweep config. Follows flat convention. | |
| Template YAML + sweep script | Patch config in memory, write temp file, run. | |

**User's choice:** CLI overrides on base config (recommended)
**Notes:** None

### Script approach

| Option | Description | Selected |
|--------|-------------|----------|
| Extend run_ablations.py | Add phase7_sweep queue, extend RunSpec with lr/k_topk override fields. | ✓ |
| New sweep script | Standalone scripts/run_sweep.py. Clean separation but duplicates infrastructure. | |
| Claude decides | Let planner pick. | |

**User's choice:** Extend run_ablations.py (recommended)
**Notes:** None

### Run directory naming

| Option | Description | Selected |
|--------|-------------|----------|
| xd_gated_fusion_lr{}_k{}_s42 | Extends D-30 pattern with lr and k suffix. | ✓ |
| xd_sweep_{N}_s42 | Sequential numbering. Requires mapping file. | |
| Claude decides | Let planner pick. | |

**User's choice:** xd_gated_fusion_lr{}_k{}_s42 (recommended)
**Notes:** None

---

## Results Presentation

### Visualization format

| Option | Description | Selected |
|--------|-------------|----------|
| Heatmap + table | 5×4 heatmap plus markdown table. Visually compelling for thesis. | ✓ |
| Table only | Markdown table sorted by AP. Simpler. | |
| Heatmap only | Just the figure. Compact but lacks exact numbers. | |

**User's choice:** Heatmap + table (recommended)
**Notes:** None

### Primary metric

| Option | Description | Selected |
|--------|-------------|----------|
| AP primary, AUC secondary | Standard for XD-Violence. Report both, rank by AP. | ✓ |
| Both equally | Dual heatmaps. More complete. | |
| AUC primary | Less standard but more stable. | |

**User's choice:** AP primary, AUC secondary (recommended)
**Notes:** None

### RTFM report location

| Option | Description | Selected |
|--------|-------------|----------|
| Same summary document | One Phase 7 summary with sweep + RTFM sections. | ✓ |
| Separate documents | Two files. Cleaner separation. | |

**User's choice:** Same summary document (recommended)
**Notes:** None

---

## Claude's Discretion

- Heatmap color scheme and styling
- Whether to include per-category AP for winning config
- RTFM diagnostic script structure
- wandb posture for sweep runs
- Confirmation queue structure

## Deferred Ideas

None — discussion stayed within phase scope.
