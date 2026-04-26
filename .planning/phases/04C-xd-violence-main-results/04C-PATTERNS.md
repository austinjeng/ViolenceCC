# Phase 4c: XD-Violence Main Results - Pattern Map

**Mapped:** 2026-04-27
**Files analyzed:** 11 (6 new configs, 1 modified script, 3 modified split files, 1 modified script argparser)
**Analogs found:** 11 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `configs/skeleton_only_xd.yaml` | config | N/A | `configs/skeleton_only.yaml` | exact |
| `configs/clip_only_xd.yaml` | config | N/A | `configs/clip_only.yaml` | exact |
| `configs/late_fusion_xd.yaml` | config | N/A | `configs/late_fusion.yaml` | exact |
| `configs/gated_fusion_xd.yaml` | config | N/A | `configs/gated_fusion.yaml` | exact |
| `configs/gated_fusion_xd_2person.yaml` | config | N/A | `configs/gated_fusion_2person.yaml` | exact |
| `configs/gated_fusion_xd_clip_mean.yaml` | config | N/A | `configs/gated_fusion_clip_mean.yaml` | exact |
| `scripts/run_ablations.py` (modify) | orchestrator | batch | `scripts/run_ablations.py` (self) | exact |
| `data/splits/xd_train.txt` (modify) | data-split | N/A | `data/splits/xd_train.txt` (self) | exact |
| `data/splits/xd_val.txt` (modify) | data-split | N/A | `data/splits/xd_val.txt` (self) | exact |
| `data/splits/xd_test.txt` (modify) | data-split | N/A | `data/splits/xd_test.txt` (self) | exact |
| `scripts/extract_ctrgcn.py` (no change) | utility | batch | self | exact |
| `scripts/extract_clip.py` (no change) | utility | batch | self | exact |

## Pattern Assignments

### `configs/skeleton_only_xd.yaml` (config)

**Analog:** `configs/skeleton_only.yaml` (lines 1-39)

**Full template to copy and modify:**
```yaml
# configs/skeleton_only.yaml — FULL FILE (39 lines)
# MOD-03 Skeleton-Only MIL baseline. Single-modal; no CLIP reference.
seed: 42
dataset: ucf                                    # CHANGE to: xd

paths:
  skeleton_features: "E:/features/ucf/skeleton"  # CHANGE to: "E:/features/xd/skeleton"
  clip_features: "E:/features/ucf/clip"          # CHANGE to: "E:/features/xd/clip"
  splits_dir: "data/splits"                      # KEEP
  results_dir: "results"                         # KEEP

model:
  variant: skeleton_only
  skel_dim: 256
  head_hidden: [128, 32]
  dropout: 0.3

data:
  T: 32
  batch_size: 16
  num_workers: 4
  pin_memory: true

train:
  lr: 1.0e-4
  weight_decay: 1.0e-2
  epochs: 50
  warmup_epochs: 5
  patience: 10
  k_topk: 3
  margin: 1.0
  lam_sparse: 8.0e-3
  lam_smooth: 8.0e-4

wandb:
  project: violencecc
  mode: disabled
  tags: [phase3, skeleton_only, ucf]             # CHANGE to: [phase4c, skeleton_only, xd]
```

**Transformation rule (applies to all 4 main configs):**
1. `dataset: ucf` -> `dataset: xd`
2. `skeleton_features: "E:/features/ucf/skeleton"` -> `"E:/features/xd/skeleton"`
3. `clip_features: "E:/features/ucf/clip"` -> `"E:/features/xd/clip"`
4. `tags:` update phase to `phase4c` and dataset to `xd`
5. Header comment updated to reference XD-Violence
6. All `model:`, `data:`, `train:` sections are **identical** (D-04: no per-dataset tuning)

---

### `configs/clip_only_xd.yaml` (config)

**Analog:** `configs/clip_only.yaml` (lines 1-40)

**Differences from skeleton_only pattern:** Has `clip_dim: 1024`, `proj_dim: 512` in model block instead of `skel_dim: 256`. Same 3-field swap rule as above.

```yaml
model:
  variant: clip_only
  clip_dim: 1024
  proj_dim: 512
  head_hidden: [128, 32]
  dropout: 0.3
```

---

### `configs/late_fusion_xd.yaml` (config)

**Analog:** `configs/late_fusion.yaml` (lines 1-42)

**Differences from skeleton_only pattern:** Has both `skel_dim` and `clip_dim`, plus `proj_dim` and `alpha: equal`. Same 3-field swap rule.

```yaml
model:
  variant: late_fusion
  skel_dim: 256
  clip_dim: 1024
  proj_dim: 512
  head_hidden: [128, 32]
  dropout: 0.3
  alpha: equal
```

---

### `configs/gated_fusion_xd.yaml` (config)

**Analog:** `configs/gated_fusion.yaml` (lines 1-41)

**Differences from skeleton_only pattern:** Has `skel_dim`, `clip_dim`, `shared_dim: 256`. Same 3-field swap rule.

```yaml
model:
  variant: gated_fusion
  skel_dim: 256
  clip_dim: 1024
  shared_dim: 256
  head_hidden: [128, 32]
  dropout: 0.3
```

---

### `configs/gated_fusion_xd_2person.yaml` (config)

**Analog:** `configs/gated_fusion_2person.yaml` (lines 1-45)

**Key differences from gated_fusion_xd.yaml:**
1. `skeleton_features` points to `"E:/features/xd/skeleton_2person"` (not `skeleton`)
2. `model.skel_dim: 512` (not 256, because concat of 2 persons)
3. `data.skel_agg: concat` field added
4. Tags include `2person`

```yaml
# From gated_fusion_2person.yaml lines 1-6 — header comment pattern:
# configs/gated_fusion_2person.yaml
# Phase 4 D-22: 2-person multi-person aggregation ablation (concat only).
# Reuses model.variant=gated_fusion; swaps in the skeleton_2person/ cache
# produced by scripts/extract_ctrgcn.py --keep-persons and lets the data
# loader reshape [N, 2, 256] -> [N, 512] via data.skel_agg=concat (D-21).
```

**XD version path swap:**
```yaml
paths:
  skeleton_features: "E:/features/xd/skeleton_2person"  # was ucf/skeleton_2person
  clip_features: "E:/features/xd/clip"                  # was ucf/clip

data:
  skel_agg: concat    # D-21: reshape [N, 2, 256] -> [N, 512]
```

---

### `configs/gated_fusion_xd_clip_mean.yaml` (config)

**Analog:** `configs/gated_fusion_clip_mean.yaml` (lines 1-44)

**Key differences from gated_fusion_xd.yaml:**
1. `clip_features` points to `"E:/features/xd/clip_mean"` (not `clip`)
2. `model.clip_dim: 512` (not 1024, because mean-only pooling)
3. Tags include `clip_mean`

```yaml
# From gated_fusion_clip_mean.yaml lines 1-5 — header comment pattern:
# configs/gated_fusion_clip_mean.yaml
# Phase 4 D-23: CLIP mean-only pooling ablation.
# Reuses model.variant=gated_fusion with clip_dim=512 (matches the [N, 512]
# cache produced by scripts/extract_clip.py --pool=mean). Skeleton side uses
# the default M-pool cache ([N, 256]); no skel_agg field needed.
```

**XD version path swap:**
```yaml
paths:
  skeleton_features: "E:/features/xd/skeleton"      # was ucf/skeleton
  clip_features: "E:/features/xd/clip_mean"          # was ucf/clip_mean
```

---

### `scripts/run_ablations.py` (modify orchestrator, batch)

**Analog:** Self — existing QUEUES dict (lines 82-113)

**Existing queue definition pattern** (lines 82-113):
```python
QUEUES = {
    "rtfm_gate": [
        RunSpec("xd_i3d", "rtfm_i3d", 42, "configs/rtfm_i3d.yaml"),
    ],
    "rtfm_gate_flow": [
        RunSpec("xd_i3d", "rtfm_i3d_flow", 42, "configs/rtfm_i3d_flow.yaml"),
    ],
    "phase4_main": [
        RunSpec("ucf", "skeleton_only", 42, "configs/skeleton_only.yaml"),
        RunSpec("ucf", "clip_only",     42, "configs/clip_only.yaml"),
        RunSpec("ucf", "late_fusion",   42, "configs/late_fusion.yaml"),
        RunSpec("ucf", "gated_fusion",  42, "configs/gated_fusion.yaml"),
    ],
    "phase4_pooling": [
        RunSpec(
            "ucf", "gated_fusion", 42,
            "configs/gated_fusion_2person.yaml", "2person",
        ),
        RunSpec(
            "ucf", "gated_fusion", 42,
            "configs/gated_fusion_clip_mean.yaml", "clip_mean",
        ),
    ],
    "phase4_seeds": [
        RunSpec("ucf", "gated_fusion", 123, "configs/gated_fusion.yaml"),
        RunSpec("ucf", "gated_fusion", 2024, "configs/gated_fusion.yaml"),
        # seed=42 covered by phase4_main; not duplicated per D-27/D-28.
    ],
}
```

**New queues to add (3 entries, appended after line 113 closing brace):**

Pattern for `phase4c_main` — mirrors `phase4_main` with `"xd"` dataset and `_xd.yaml` configs:
```python
    "phase4c_main": [
        RunSpec("xd", "skeleton_only", 42, "configs/skeleton_only_xd.yaml"),
        RunSpec("xd", "clip_only",     42, "configs/clip_only_xd.yaml"),
        RunSpec("xd", "late_fusion",   42, "configs/late_fusion_xd.yaml"),
        RunSpec("xd", "gated_fusion",  42, "configs/gated_fusion_xd.yaml"),
    ],
```

Pattern for `phase4c_pooling` — mirrors `phase4_pooling` with XD configs and cache_variant:
```python
    "phase4c_pooling": [
        RunSpec(
            "xd", "gated_fusion", 42,
            "configs/gated_fusion_xd_2person.yaml", "2person",
        ),
        RunSpec(
            "xd", "gated_fusion", 42,
            "configs/gated_fusion_xd_clip_mean.yaml", "clip_mean",
        ),
    ],
```

Pattern for `phase4c_seeds` — mirrors `phase4_seeds` with XD gated_fusion config:
```python
    "phase4c_seeds": [
        RunSpec("xd", "gated_fusion", 123, "configs/gated_fusion_xd.yaml"),
        RunSpec("xd", "gated_fusion", 2024, "configs/gated_fusion_xd.yaml"),
        # seed=42 covered by phase4c_main; not duplicated per D-27/D-28.
    ],
```

**RunSpec field mapping** (lines 44-73):
```python
@dataclass
class RunSpec:
    dataset: str       # "xd" for all Phase 4c runs
    variant: str       # model variant name
    seed: int          # 42, 123, or 2024
    config: str        # path to YAML config (relative to PROJECT_ROOT)
    cache_variant: str = ""  # "2person" or "clip_mean" for pooling ablations

    @property
    def run_name(self) -> str:
        cv = f"_{self.cache_variant}" if self.cache_variant else ""
        return f"{self.dataset}_{self.variant}{cv}_s{self.seed}"
```

**Run name output examples (D-30 deterministic naming):**
- `xd_skeleton_only_s42`
- `xd_clip_only_s42`
- `xd_late_fusion_s42`
- `xd_gated_fusion_s42`
- `xd_gated_fusion_s123`
- `xd_gated_fusion_s2024`
- `xd_gated_fusion_2person_s42`
- `xd_gated_fusion_clip_mean_s42`

**Argparse choices update** (line 275):
```python
    # Current:
    ap.add_argument(
        "--queue", required=True, choices=sorted(QUEUES),
        help="Queue to run: rtfm_gate, phase4_main, phase4_pooling, phase4_seeds",
    )
    # choices=sorted(QUEUES) is dynamic — auto-picks up new keys.
    # Only the help string needs updating to mention new queues.
```

**wandb_tags pattern** (lines 68-73) — existing method returns `["phase4", ...]`. For Phase 4c runs, the tag comes from `RunSpec.wandb_tags()` which hardcodes `"phase4"`. The YAML `wandb.tags` field overrides this in practice (tags are set from YAML, not RunSpec). So the YAML tags `[phase4c, <variant>, xd]` are the authoritative source.

---

### `data/splits/xd_train.txt` (modify data-split)

**Analog:** Self — current file format is one video ID per line, no header.

**D-05 cleaning pattern:**
1. Remove line 1804: `v=8cTqh9tMz_I__#1_label_A` (corrupt MP4, missing moov atom)
2. Remove line 2036: `v=Gm73TwtUyGY__#1_label_G-0-0` (34 frames, below 64-frame window)
3. Add comment at top of file documenting exclusions

**Comment pattern** (no existing convention; D-05 specifies "comment at the top"):
```
# Excluded: v=8cTqh9tMz_I__#1_label_A (corrupt MP4, missing moov atom)
# Excluded: v=Gm73TwtUyGY__#1_label_G-0-0 (34 frames, below 64-frame window)
```

**Important:** Verify downstream code in `src/data/loaders.py` and `src/data/dataset.py` handles comment lines (lines starting with `#`). If not, the comment must be added in a way that does not break the loader, or the loader must be updated to skip `#` lines.

---

### `data/splits/xd_val.txt` and `data/splits/xd_test.txt` (modify data-split)

**Analog:** Same format as `xd_train.txt`.

**D-05 states both missing IDs are in `xd_train.txt`** (confirmed by grep: both at lines 1804 and 2036 of xd_train.txt). The val and test files do NOT contain these IDs. However, D-05 says "Add a comment at the top of each affected split file documenting the exclusion." If only train is affected, only train needs the comment. Planner should verify whether val/test also need comments for documentation purposes per D-05's "each affected split file" language.

---

## Shared Patterns

### Config Transformation Rule (all 6 new configs)
**Source:** All 6 UCF configs in `configs/` (lines shown above per file)
**Apply to:** All 6 new XD config files

The transformation from UCF to XD config is mechanical with exactly 3 field swaps + 1 tag update:

| Field | UCF Value | XD Value |
|-------|-----------|----------|
| `dataset` | `ucf` | `xd` |
| `paths.skeleton_features` | `"E:/features/ucf/skeleton"` | `"E:/features/xd/skeleton"` |
| `paths.clip_features` | `"E:/features/ucf/clip"` | `"E:/features/xd/clip"` |
| `wandb.tags` | `[phaseN, <variant>, ucf]` | `[phase4c, <variant>, xd]` |

For pooling variants, additional path differences:
- `_2person`: `skeleton_features` -> `"E:/features/xd/skeleton_2person"`
- `_clip_mean`: `clip_features` -> `"E:/features/xd/clip_mean"`

All `model:`, `data:`, and `train:` sections remain **byte-identical** to UCF counterparts (D-04).

### Deterministic Run Directory Naming (D-30)
**Source:** `scripts/run_ablations.py` RunSpec.run_name property (lines 63-66)
**Apply to:** All 8 XD run directories

```python
# Pattern: {dataset}_{variant}[_{cache_variant}]_s{seed}
f"{self.dataset}_{self.variant}{cv}_s{self.seed}"
```

### Queue Registration Pattern
**Source:** `scripts/run_ablations.py` QUEUES dict (lines 82-113)
**Apply to:** 3 new queue entries

Each queue is a list of RunSpec entries. The naming convention is `phase4c_<purpose>` mirroring `phase4_<purpose>`. The QUEUES dict keys are used directly by `--queue` argparse choices, which auto-discover keys via `choices=sorted(QUEUES)`.

### Annotations Path
**Source:** CONTEXT.md D-01
**Apply to:** All 6 XD configs

The `paths.annotations` field is NOT present in any existing UCF config (annotations path is inferred from dataset key in evaluate.py). Per Claude's Discretion in CONTEXT.md, the annotation path routing is left to the planner/implementer. The existing UCF configs do NOT have a `paths.annotations` field, so XD configs should follow the same pattern (omit it) unless evaluate.py requires it explicitly.

## No Analog Found

No files lack analogs. Every new/modified file has an exact match in the existing codebase.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All 11 files have exact analogs |

## Metadata

**Analog search scope:** `configs/`, `scripts/`, `data/splits/`
**Files scanned:** 8 configs, 3 scripts, 3 split files = 14 files
**Pattern extraction date:** 2026-04-27
