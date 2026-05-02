# Phase 6: Analysis & Visualization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 06-analysis-visualization
**Areas discussed:** Video selection criteria, Temporal curve layout, Skeleton overlay approach, Scope beyond VIS-01/VIS-02

---

## Video Selection Criteria

| Option | Description | Selected |
|--------|-------------|----------|
| Success + failure mix | 2 clear detections + 1 failure case per dataset. Shows strengths AND limitations. | |
| Best detections only | 2-3 videos where Gated Fusion cleanly separates anomaly vs normal. | ✓ |
| Category diversity | 1 Fighting/Assault + 1 other category + 1 failure. Demonstrates generalization. | |

**User's choice:** Best detections only
**Notes:** User wants strongest visual argument for fusion. Cherry-picking concern acknowledged but acceptable for thesis qualitative section.

---

## Temporal Curve Layout

### Model variant comparison
| Option | Description | Selected |
|--------|-------------|----------|
| Overlay all 4 variants | Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion on same axes. | ✓ |
| Gated Fusion only | Cleaner single-line plots. | |
| Gated Fusion + best single-modal | Two lines per plot. | |

**User's choice:** Overlay all 4 variants

### GT shading style
| Option | Description | Selected |
|--------|-------------|----------|
| Red shaded band | Semi-transparent red fill during GT anomaly frames. Standard in VAD papers. | ✓ |
| Gray shaded band | Neutral gray shading. | |
| Vertical dashed lines | Dashed lines at anomaly start/end. | |

**User's choice:** Red shaded band

### Video count
| Option | Description | Selected |
|--------|-------------|----------|
| 2 UCF + 1 XD | Minimum per success criteria. | |
| 3 UCF + 2 XD | More coverage across categories. | ✓ |
| 2 UCF + 2 XD | Balanced across datasets. | |

**User's choice:** 3 UCF + 2 XD

---

## Skeleton Overlay Approach

### Format
| Option | Description | Selected |
|--------|-------------|----------|
| Static frame grabs | 3-5 key frames with COCO-17 keypoints + limb edges. Standard thesis format. | ✓ |
| Frame sequence strips | Horizontal strip of 4-6 consecutive frames. | |
| Side-by-side: raw + skeleton | Original frame next to skeleton overlay. | |

**User's choice:** Static frame grabs

### Video source
| Option | Description | Selected |
|--------|-------------|----------|
| Same videos as temporal curves | Ties qualitative analysis together. | ✓ |
| Different videos | More freedom for skeleton clarity. | |
| Mix of both | Some overlap + additional videos. | |

**User's choice:** Same videos as temporal curves

---

## Scope Beyond VIS-01/VIS-02

| Option | Description | Selected |
|--------|-------------|----------|
| Corruption severity heatmap (OPT-11) | 4x5 grid of AUC degradation. TTA data ready. | ✓ |
| Gating weight distributions (OPT-10) | Histogram/boxplot of sigmoid gate values by category. | ✓ |
| t-SNE/UMAP of fused features (OPT-09) | 2D projection colored by category. | ✓ |
| None — stick to VIS-01 + VIS-02 | Keep minimal. | |

**User's choice:** All three optional items selected
**Notes:** User explicitly requested maximalist approach: "I want all kinds of graph I can get. I can later pick what I need from the generated visualization later. The more complete my VIS is the better."

### Model runs for feature collection
| Option | Description | Selected |
|--------|-------------|----------|
| Gated Fusion s42 for both datasets | Single seed, simple. Qualitative figures don't need multi-seed stats. | ✓ |
| Best config per dataset | UCF default + XD Phase 7 winner. | |
| All 3 seeds | 3x forward passes. | |

**User's choice:** Gated Fusion s42 for both datasets

### Additional figure types
| Option | Description | Selected |
|--------|-------------|----------|
| Cross-dataset comparison panels | Side-by-side UCF vs XD figures. | |
| Per-category score distributions | Violin/box plots by violence category. | |
| Generate everything you can think of | Claude's discretion on additional figures. | ✓ |

**User's choice:** Generate everything Claude can think of

---

## Claude's Discretion

- Specific video IDs for temporal curves (select programmatically)
- Additional figure types beyond discussed set
- Figure sizing and subplot arrangement
- Number and placement of skeleton overlay frames

## Deferred Ideas

None — discussion stayed within phase scope
