# Phase 7: XD-Violence Hyperparameter Sweep - Research

**Researched:** 2026-05-01
**Domain:** MIL hyperparameter sensitivity (lr x k_topk grid), RTFM reproduction gap investigation, sweep orchestration infrastructure
**Confidence:** HIGH

## Summary

Phase 7 is a targeted hyperparameter exploration phase that extends the Phase 4c XD-Violence Gated Fusion baseline (AP=71.92% at seed=42, 3-seed mean=70.97%). The sweep grid of 5 learning rates x 4 k_topk values = 20 runs is well-scoped to the existing `run_ablations.py` orchestration infrastructure. The key code changes are: (1) extend `train.py` with `--lr` and `--k-topk` CLI overrides, (2) extend `RunSpec` with optional override fields, (3) add `phase7_sweep` and `phase7_confirm` queues, and (4) generate a 5x4 heatmap visualization.

The RTFM gap investigation (65.70% vs 77.81%) has a clear primary suspect: RTFM's official code uses lr=0.001 (1e-3) while our reproduction used lr=1e-4 -- a 10x difference. RTFM also uses a margin=100 on raw feature magnitudes vs our margin=1.0 on sigmoid scores, and batch_size=32 vs our batch_size=3 (5-crop inflated to 15 effective). These are fundamental training regime differences, not evaluation protocol bugs. The 4 diagnostics in D-07 will document these systematically for the thesis.

**Primary recommendation:** Implement the sweep as a straightforward extension of the existing run_ablations.py orchestration pattern. Focus the RTFM gap investigation on documenting the training regime differences (lr, margin, batch_size, feature extraction pipeline) rather than attempting to close the gap -- this aligns with D-06's "diagnose and document" posture.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Sweep grid design:**
- **D-01:** Learning rate grid: {5e-5, 1e-4, 2e-4, 3e-4, 5e-4} -- 5 values centered around current 1e-4, biased upward since XD has ~4x more training data than UCF.
- **D-02:** k_topk grid: {1, 3, 5, 7} -- 4 values spanning aggressive (k=1, top snippet only) to inclusive (k=7, ~22% of 32-snippet bag). k=3 is the Phase 4c default.
- **D-03:** Full combinatorial grid: 5 lr x 4 k_topk = 20 runs at seed=42. Matches SC #1 (~20 runs target).
- **D-04:** Single seed (s42) for sweep exploration. Direct comparison with Phase 4c baseline (xd_gated_fusion_s42, AP=71.92%).
- **D-05:** 3-seed confirmation on the winning lr x k_topk config using seeds {42, 123, 2024}. Reports mean+/-std AP, directly comparable to Phase 4c 3-seed results (mean AP=70.97% +/- 1.08%).

**RTFM gap investigation:**
- **D-06:** Goal is diagnose and document -- identify likely cause of 65.70% vs 77.81% gap, document for thesis. Do not attempt to close the gap through protocol changes.
- **D-07:** Run all 4 diagnostics: (1) annotation alignment check, (2) temporal interpolation check, (3) I3D feature audit, (4) published code comparison.
- **D-08:** Fix policy: fix only clear bugs (parsing errors, off-by-one). Document methodological differences without changing our protocol.

**Sweep infrastructure:**
- **D-09:** Use CLI overrides on base config (`gated_fusion_xd.yaml`). Pass `--lr` and `--k-topk` as CLI args to `train.py`, overriding YAML values. Zero new config files created for the sweep.
- **D-10:** Extend `run_ablations.py` with a `phase7_sweep` queue containing 20 RunSpec entries. Reuses `.done` resume, `results-index.csv` append, error handling. RunSpec gets 2 new optional fields (`lr_override`, `k_topk_override`).
- **D-11:** Run directory naming: `xd_gated_fusion_lr{}_k{}_s42` -- extends Phase 4 D-30 pattern with lr and k suffix.
- **D-12:** 3-seed confirmation queue: `phase7_confirm` with 3 RunSpec entries for the winning config at seeds {42, 123, 2024}. Created after sweep results are analyzed.

**Results presentation:**
- **D-13:** Primary metric: AP (standard for XD-Violence benchmark). AUC is secondary.
- **D-14:** Visualization: heatmap + table. A 5x4 heatmap (lr rows, k_topk columns, AP as cell color/text) plus a markdown table with exact numbers.
- **D-15:** Single Phase 7 results summary document with two sections: sweep results and RTFM gap analysis.

### Claude's Discretion
- Exact heatmap color scheme and styling
- Whether to include per-category AP breakdown for the winning sweep config
- RTFM diagnostic script structure (single script vs modular)
- wandb posture for sweep runs (continue disabled or enable)
- Whether confirmation runs reuse the sweep queue or get a separate queue

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

## Architectural Responsibility Map

Phase 7 is pure backend training + evaluation infrastructure work -- no browser, CDN, or frontend concerns.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Hyperparameter sweep orchestration | CLI / Scripts | -- | `run_ablations.py` subprocess orchestrator drives `train.py` + `evaluate.py` |
| CLI override parsing | Backend (train.py) | -- | argparse extension in existing entry point |
| MIL training with varied lr/k | Backend (GPU) | -- | PyTorch training loop with AdamW + cosine schedule |
| Frame-level AP evaluation | Backend (evaluate.py) | -- | Reuses existing Phase 4 pipeline unchanged |
| Sweep heatmap generation | Scripts | -- | matplotlib/seaborn chart generation script |
| RTFM gap diagnostics | Scripts | -- | Standalone diagnostic script(s) comparing evaluation protocols |
| Results logging | Backend (csv_logger) | -- | Append to existing results-index.csv |

## Standard Stack

### Core (already installed in vcc-main)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyTorch | 2.6.0 | MIL training with varied hyperparameters | Already in vcc-main; no new install |
| scikit-learn | >= 1.3 | `roc_auc_score`, `average_precision_score` | Already used by evaluate.py |
| matplotlib | >= 3.7 | Sweep heatmap generation | Already used by generate_phase4_charts.py |
| seaborn | >= 0.12 | Heatmap color scheme | Already used by generate_phase4_charts.py |
| pandas | >= 2.0 | results-index.csv analysis | Already used by generate_phase4_charts.py |
| numpy | >= 1.23 | Array operations | Universal dependency |

[VERIFIED: codebase grep -- all libraries already imported in existing scripts]

### No New Dependencies
This phase requires zero new pip installs. All tools are already available in the `vcc-main` conda environment.

## Architecture Patterns

### System Architecture Diagram

```
gated_fusion_xd.yaml (base config)
        |
        v
run_ablations.py --queue phase7_sweep
        |
        |  for each of 20 RunSpec entries:
        v
train.py --config configs/gated_fusion_xd.yaml \
         --lr {lr_override} --k-topk {k_override} \
         --seed 42 --run-name xd_gated_fusion_lr{}_k{}_s42
        |
        v
evaluate.py --run-dir results/xd_gated_fusion_lr{}_k{}_s42
        |
        v
results/results-index.csv  (append 1 row per run)
        |
        v
[Analyze: find best lr x k_topk by AP]
        |
        v
run_ablations.py --queue phase7_confirm  (3-seed on winner)
        |
        v
generate_phase7_charts.py  (heatmap + table)
```

### Recommended Project Structure (new/modified files only)

```
scripts/
  run_ablations.py           # MODIFIED: +phase7_sweep queue, +RunSpec override fields
  generate_phase7_charts.py  # NEW: sweep heatmap + summary table
  rtfm_gap_diagnostic.py     # NEW: 4 RTFM diagnostics
src/
  train.py                   # MODIFIED: +--lr and --k-topk CLI args
results/
  xd_gated_fusion_lr*_k*_s*/ # NEW: 20 sweep + 3 confirm run dirs
  phase7_charts/             # NEW: heatmap PNGs
  phase7_summary.md          # NEW: thesis-ready summary document
```

### Pattern 1: CLI Override for Hyperparameter Sweep

**What:** Extend `train.py` `parse_args()` and `apply_cli_overrides()` to accept `--lr` and `--k-topk` flags that override the YAML config values at runtime.

**When to use:** When running the same base config with varied hyperparameters (sweep), avoiding config file proliferation.

**Example:**
```python
# Source: existing train.py parse_args() pattern at line 33-45
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="ViolenceCC training entry point (TRN-06)")
    ap.add_argument("--config", required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--results-dir", type=str, default=None)
    ap.add_argument("--run-name", type=str, default=None)
    # Phase 7 D-09: sweep CLI overrides
    ap.add_argument("--lr", type=float, default=None,
                    help="Override cfg['train']['lr'] (Phase 7 sweep)")
    ap.add_argument("--k-topk", type=int, default=None,
                    help="Override cfg['train']['k_topk'] (Phase 7 sweep)")
    return ap.parse_args(argv)

def apply_cli_overrides(cfg: dict, args) -> dict:
    if args.seed is not None:
        cfg["seed"] = args.seed
    if args.epochs is not None:
        cfg["train"]["epochs"] = args.epochs
    if args.results_dir is not None:
        cfg["paths"]["results_dir"] = args.results_dir
    # Phase 7 D-09
    if args.lr is not None:
        cfg["train"]["lr"] = args.lr
    if args.k_topk is not None:
        cfg["train"]["k_topk"] = args.k_topk
    return cfg
```
[VERIFIED: existing train.py pattern at lines 33-55]

### Pattern 2: RunSpec Extension for CLI Overrides

**What:** Add optional `lr_override` and `k_topk_override` fields to `RunSpec`. The `run_one()` function passes these as additional subprocess args when non-None.

**Example:**
```python
# Source: existing run_ablations.py RunSpec at line 53-81
@dataclass
class RunSpec:
    dataset: str
    variant: str
    seed: int
    config: str
    cache_variant: str = ""
    # Phase 7 D-10: optional hyperparameter overrides
    lr_override: float | None = None
    k_topk_override: int | None = None

    @property
    def run_name(self) -> str:
        cv = f"_{self.cache_variant}" if self.cache_variant else ""
        # Phase 7 D-11: extended naming with lr/k suffix
        hp = ""
        if self.lr_override is not None:
            # Format lr: 5e-05 -> "5e5", 1e-04 -> "1e4", 2e-04 -> "2e4"
            hp += f"_lr{self._fmt_lr()}"
        if self.k_topk_override is not None:
            hp += f"_k{self.k_topk_override}"
        return f"{self.dataset}_{self.variant}{cv}{hp}_s{self.seed}"

    def _fmt_lr(self) -> str:
        """Format LR for run_name: 5e-05 -> '5e5', 1e-04 -> '1e4'."""
        if self.lr_override is None:
            return ""
        s = f"{self.lr_override:.0e}"  # "5e-05"
        # Strip minus sign and leading zeros: "5e-05" -> "5e5"
        return s.replace("-", "").replace("+", "").lstrip("0") or "0"
```
[VERIFIED: existing RunSpec structure at lines 53-81]

### Pattern 3: Phase 7 Sweep Queue

**What:** 20 RunSpec entries forming the full 5x4 combinatorial grid.

**Example:**
```python
# Source: pattern from existing QUEUES dict at line 113
_LR_SWEEP = [5e-5, 1e-4, 2e-4, 3e-4, 5e-4]
_K_SWEEP = [1, 3, 5, 7]

QUEUES["phase7_sweep"] = [
    RunSpec(
        "xd", "gated_fusion", 42,
        "configs/gated_fusion_xd.yaml",
        lr_override=lr, k_topk_override=k,
    )
    for lr in _LR_SWEEP for k in _K_SWEEP
]  # 20 runs
```

### Pattern 4: run_one() Override Forwarding

**What:** When `run_one()` builds the `train_cmd` list, append `--lr` and `--k-topk` flags if the RunSpec has override values.

**Example:**
```python
# Source: existing run_one() at line 225-248
train_cmd = [
    sys.executable, "src/train.py",
    "--config", spec.config,
    "--seed", str(spec.seed),
    "--results-dir", str(results_root),
    "--run-name", spec.run_name,
]
# Phase 7: forward CLI overrides
if spec.lr_override is not None:
    train_cmd.extend(["--lr", str(spec.lr_override)])
if spec.k_topk_override is not None:
    train_cmd.extend(["--k-topk", str(spec.k_topk_override)])
```
[VERIFIED: existing run_one() structure at lines 225-248]

### Anti-Patterns to Avoid

- **20 separate YAML configs for sweep:** D-09 explicitly prohibits this. CLI overrides on a single base config are cleaner and auditable.
- **Modifying gated_fusion_xd.yaml in-place between runs:** Race condition risk; CLI overrides are subprocess-safe.
- **Using the Phase 4c baseline run `xd_gated_fusion_s42` as the k=3/lr=1e-4 sweep point:** The sweep should re-run this config point as `xd_gated_fusion_lr1e4_k3_s42` so all 20 runs have identical training conditions. The Phase 4c result serves as the external comparison baseline, not a sweep participant.
- **Skipping the 3-seed confirmation step:** The sweep identifies the best config at s42 only. Without 3-seed confirmation, the improvement could be seed-specific noise (recall XD AP std=1.08% from Phase 4c).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sweep orchestration | Custom sweep loop script | Extend `run_ablations.py` QUEUES | `.done` resume, error logging, results-index.csv append already work |
| Config override merging | Custom config patcher | argparse CLI override in train.py | Already has `apply_cli_overrides()` pattern |
| Results logging | Custom CSV writer | `results_index_append()` | Schema-stable, fsync-safe, already handles 17-column schema |
| Heatmap visualization | Raw matplotlib grid | seaborn `heatmap()` | Already used in generate_phase4_charts.py (chart B06/B07) |
| AP/AUC computation | Custom metric code | `evaluate.py` pipeline | C4-guard snippet-to-frame already validated |

**Key insight:** Phase 7 is an *extension* phase, not a *creation* phase. Every infrastructure component already exists from Phase 4/4c. The code changes are additive: ~40 lines in train.py, ~60 lines in run_ablations.py, ~150 lines in a new chart script, ~100 lines in a diagnostic script.

## Common Pitfalls

### Pitfall 1: LR Formatting in Run Directory Names
**What goes wrong:** Python's `f"{5e-5}"` produces `"5e-05"` which includes a minus sign -- undesirable in directory names.
**Why it happens:** Scientific notation formatting includes sign characters.
**How to avoid:** Use a helper like `_fmt_lr()` that strips minus/plus signs: `5e-05` -> `5e5`, `1e-04` -> `1e4`, `3e-04` -> `3e4`. Ensure the mapping is bijective (no two grid LRs produce the same string).
**Warning signs:** Run directory name collisions; `results-index.csv` rows with ambiguous lr values.

### Pitfall 2: k_topk=1 Causing MIL Collapse
**What goes wrong:** With k=1, the MIL ranking loss selects only the single highest-scoring snippet per bag. If many videos have the same "hottest" snippet pattern (e.g., scene transitions), the model may collapse to a trivial solution.
**Why it happens:** k=1 provides the least gradient diversity per bag. Normal videos may have a single high-confidence false positive that dominates the hinge loss.
**How to avoid:** Monitor for abnormally fast convergence or train_loss near zero in the k=1 runs. If k=1 runs show degenerate AP (e.g., < 50%), this is expected behavior documenting the sensitivity, not a bug.
**Warning signs:** train_loss drops to < 0.05 within 5 epochs; val_loss diverges while train_loss stays flat.

### Pitfall 3: Confirmation Queue Created Before Sweep Completes
**What goes wrong:** The `phase7_confirm` queue depends on knowing the winning lr/k_topk from the sweep. If the queue is hard-coded before the sweep runs, it will use the wrong config.
**Why it happens:** The QUEUES dict is defined at module load time.
**How to avoid:** D-12 specifies `phase7_confirm` is created *after* sweep results are analyzed. Two options: (a) add the queue entries manually after analyzing results, or (b) use a `--best-config` CLI arg that reads from results-index.csv. Option (a) is simpler and matches the project's manual-queue-definition pattern.
**Warning signs:** Running `phase7_confirm` before the sweep is complete.

### Pitfall 4: Confusing Sweep Re-Run with Phase 4c Baseline
**What goes wrong:** The sweep point lr=1e-4, k=3 will reproduce the Phase 4c baseline approximately (same config, same seed), but NOT identically -- `config_snapshot.json` will differ (it captures the CLI override presence), and the run directory is different (`xd_gated_fusion_lr1e4_k3_s42` vs `xd_gated_fusion_s42`). AP should match within training noise.
**Why it happens:** Different code paths (CLI override vs. pure YAML) produce slightly different config snapshots.
**How to avoid:** Use the Phase 4c baseline AP (71.92%) as the external comparison, not the sweep's lr=1e-4/k=3 re-run. If the re-run AP differs by > 2pp from 71.92%, investigate (seed or config drift). The re-run serves as an internal consistency check.
**Warning signs:** Re-run AP differs from Phase 4c by > 2pp despite identical hyperparameters and seed.

### Pitfall 5: RTFM Gap Investigation Conflating Evaluation and Training Differences
**What goes wrong:** Concluding the 12.11pp gap is due to evaluation protocol differences (annotation parsing, snippet-to-frame), when the root cause is training regime differences (lr, margin, batch_size, feature pipeline).
**Why it happens:** Evaluation diagnostics are easier to run than training regime analysis, so researchers gravitate toward them.
**How to avoid:** The 4 diagnostics in D-07 should *start* with the published code comparison (diagnostic #4) which reveals the training regime differences, then verify evaluation alignment as a secondary check. Document both categories of difference in the thesis.
**Warning signs:** Spending more than 1 day trying to "fix" the evaluation path when the published RTFM code shows fundamentally different training hyperparameters.

## Code Examples

### Sweep Heatmap Generation

```python
# Source: adapted from generate_phase4_charts.py chart B06 pattern [VERIFIED: lines 361-376]
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_sweep_heatmap(results_csv, output_path):
    """Generate 5x4 lr x k_topk AP heatmap from results-index.csv."""
    df = pd.read_csv(results_csv)
    # Filter to phase7 sweep runs only
    sweep = df[df["run_name"].str.startswith("xd_gated_fusion_lr")]
    
    # Extract lr and k from run_name
    sweep = sweep.copy()
    sweep["lr_val"] = sweep["run_name"].str.extract(r"lr(\d+e\d+)").apply(
        lambda x: float(x.str.replace("e", "e-"))  # "5e5" -> 5e-5
    )
    sweep["k_val"] = sweep["run_name"].str.extract(r"k(\d+)").astype(int)
    
    # Pivot to heatmap grid
    pivot = sweep.pivot_table(values="ap", index="lr_val", columns="k_val")
    pivot = pivot.sort_index(ascending=True)
    
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(
        pivot, annot=True, fmt=".4f", cmap="RdYlGn",
        linewidths=0.5, ax=ax,
        cbar_kws={"label": "AP"},
    )
    ax.set_xlabel("k_topk", fontsize=14)
    ax.set_ylabel("Learning Rate", fontsize=14)
    ax.set_title("XD-Violence Gated Fusion: lr x k_topk Sweep (AP)",
                 fontsize=16, fontweight="bold")
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
```

### RTFM Diagnostic: Published Code Comparison

```python
# Source: RTFM official repo [CITED: https://github.com/tianyu0207/RTFM]
def compare_training_regimes():
    """Document the training regime differences between our repro and RTFM published."""
    our_config = {
        "lr": 1e-4,           # TRN-01
        "margin": 1.0,        # Phase 3 D-02 (sigmoid scores in [0,1])
        "batch_size": 3,      # 5-crop x 3 = 15 effective
        "k_topk": 3,          # Phase 3 D-01 = 32//10
        "optimizer": "AdamW", # weight_decay=1e-2
        "scheduler": "cosine_warmup",
        "epochs": 50,
        "patience": 10,
        "features": "XDVioDet 5-crop I3D RGB 1024-d",
    }
    rtfm_published = {
        "lr": 1e-3,           # option.py default [VERIFIED: WebFetch]
        "margin": 100,        # train.py RTFM_loss(0.0001, 100) [VERIFIED: WebFetch]
        "batch_size": 32,     # option.py default [VERIFIED: WebFetch]
        "k_topk": 3,          # model.py num_segments//10 [VERIFIED: WebFetch]
        "optimizer": "Adam",  # inferred from standard RTFM
        "scheduler": "constant",  # '[0.001]*15000' = flat LR [VERIFIED: WebFetch]
        "epochs": 15000,      # iterations, not epochs [VERIFIED: WebFetch]
        "patience": None,     # no early stopping
        "features": "RTFM 10-crop I3D RGB 2048-d",
    }
    return our_config, rtfm_published
```

### Run Directory Naming Convention

```python
# D-11 examples [VERIFIED: CONTEXT.md D-11]
# Sweep runs:
#   xd_gated_fusion_lr5e5_k1_s42    (lr=5e-5, k=1)
#   xd_gated_fusion_lr1e4_k3_s42    (lr=1e-4, k=3)  <- re-runs Phase 4c baseline
#   xd_gated_fusion_lr5e4_k7_s42    (lr=5e-4, k=7)
# Confirmation runs:
#   xd_gated_fusion_lr{best}_k{best}_s42
#   xd_gated_fusion_lr{best}_k{best}_s123
#   xd_gated_fusion_lr{best}_k{best}_s2024
```

## RTFM Gap Analysis: Pre-Research Findings

### Known Differences Between Our Reproduction and RTFM Published

| Parameter | Our Repro | RTFM Published | Impact |
|-----------|-----------|----------------|--------|
| Learning rate | 1e-4 | 1e-3 | 10x lower; likely causes underfitting [VERIFIED: WebFetch RTFM option.py] |
| Loss margin | 1.0 (sigmoid [0,1]) | 100 (feature magnitudes) | Different loss scale; not directly comparable [VERIFIED: WebFetch RTFM train.py] |
| Batch size | 3 (x5 crop = 15 effective) | 32 | 2x fewer gradient samples per step [VERIFIED: WebFetch RTFM option.py] |
| I3D features | XDVioDet 5-crop, 1024-d | RTFM 10-crop, 2048-d | Different backbone/crop count; 2x feature dim [VERIFIED: WebFetch RTFM option.py feature-size=2048] |
| Schedule | Cosine warmup (50 epochs) | Constant LR (15k iterations) | Different convergence dynamics [VERIFIED: WebFetch RTFM option.py] |
| Optimizer | AdamW (wd=1e-2) | Adam (no wd specified) | Minor difference [ASSUMED] |
| Early stopping | patience=10 | None | May stop too early [VERIFIED: WebFetch RTFM option.py max-epoch=15000] |
| k_topk | 3 | 3 (32//10) | Same [VERIFIED: WebFetch RTFM model.py] |

### Evaluation Protocol Comparison

| Aspect | Our Repro | RTFM/XDVioDet Published | Match? |
|--------|-----------|------------------------|--------|
| Snippet-to-frame | `np.repeat(scores, snippet_window)` | `np.repeat(pred, 16)` | YES [VERIFIED: our snippet_to_frame.py + WebFetch RTFM test_10crop.py] |
| Snippet window | 16 (for I3D path) | 16 | YES [VERIFIED: our evaluate.py line 199 + WebFetch] |
| GT source | Wu annotations parsed on-the-fly | Pre-generated `gt.npy` | Different source, should give same labels [CITED: 04b-RESEARCH.md] |
| AP computation | `sklearn.average_precision_score` | `sklearn.auc(recall, precision)` | Functionally identical for binary classification [ASSUMED] |
| Test set size | 800 videos (500 abn + 300 nor) | 800 videos | YES [VERIFIED: eval_metrics.json n_videos=800] |
| Total frames (I3D) | 2,330,384 | ~2,330,384 (from XDVioDet gt.npy) | YES [CITED: 04b-RESEARCH.md] |

### Root Cause Assessment

The 12.11pp AP gap (65.70% vs 77.81%) is **overwhelmingly likely a training regime difference**, not an evaluation bug:

1. **LR 10x lower** -- our AdamW at lr=1e-4 with cosine schedule reaches very low effective LR during training. RTFM uses constant lr=1e-3 for 15k iterations.
2. **Feature dimension mismatch** -- RTFM's 2048-d features vs our 1024-d XDVioDet features mean the model sees different information.
3. **10-crop vs 5-crop** -- RTFM uses 10-crop averaging which provides more robust per-snippet representations.
4. **Evaluation protocol is aligned** -- both use `np.repeat(pred, 16)` snippet-to-frame expansion, same sklearn AP computation, same 800-video test set.

**Recommendation for diagnostics:** Focus D-07 diagnostics on *documenting* these differences for the thesis, not on finding evaluation bugs. The evaluation path is already validated by the Phase 4b D-12 diagnostics (C4 sanity delta = 0.0024, bag-size audit correct).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-config YAML for each sweep point | CLI override on single base config | Phase 7 D-09 | 0 new config files vs 20 |
| RTFM 10-crop I3D (2048-d) | XDVioDet 5-crop I3D (1024-d) | Phase 4b (April 2026) | Known dimension/crop mismatch drives repro gap |
| Hyperparameter transfer from UCF (lr=1e-4, k=3) | Sweep grid exploration | Phase 7 | Tests whether XD-specific tuning improves AP |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `sklearn.average_precision_score` and `sklearn.auc(recall, precision)` produce identical results for binary frame-level labels | RTFM Gap Analysis | LOW -- both compute area under PR curve; minor numerical differences possible but < 0.1pp |
| A2 | RTFM uses Adam (not AdamW) optimizer | RTFM Gap Analysis | LOW -- optimizer choice has minor impact compared to 10x LR difference |
| A3 | Sweep runs at lr=1e-4/k=3 will approximately reproduce Phase 4c AP=71.92% within 2pp | Pitfall 4 | MEDIUM -- if reproduction drift > 2pp, suggests config override path introduces a bug |

## Open Questions

1. **Best LR formatting for directory names**
   - What we know: Need to convert `5e-05` -> short string. Options: `5e5`, `5e-5`, `0.00005`
   - What's unclear: Which format is most readable and grep-friendly
   - Recommendation: Use `5e5` (no minus sign, compact). The D-11 examples in CONTEXT.md show `lr2e4` pattern which matches this. Verify the formatting is bijective across all 5 grid points.

2. **Whether to re-run the Phase 4c baseline as part of the sweep**
   - What we know: lr=1e-4/k=3 is in the sweep grid and matches the Phase 4c config
   - What's unclear: Whether this re-run is redundant or valuable as an internal consistency check
   - Recommendation: Include it in the sweep (it's only 1 of 20 runs, ~3 min). Compare against Phase 4c AP=71.92% as a sanity check. If delta > 2pp, investigate.

3. **Phase 7 confirm queue: static or dynamic?**
   - What we know: D-12 says the queue is created after sweep analysis
   - What's unclear: Whether to hard-code the winning config or read from results
   - Recommendation: Hard-code the winning config into the QUEUES dict after manual analysis. This matches the project's manual-queue-definition pattern and avoids runtime complexity.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | `pytest.ini` / `pyproject.toml` (existing) |
| Quick run command | `pytest tests/test_run_ablations.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC-1 | 20 sweep RunSpec entries in phase7_sweep queue | unit | `pytest tests/test_run_ablations.py::test_phase7_sweep_queue -x` | Wave 0 |
| SC-1 | RunSpec.run_name produces D-11 naming pattern | unit | `pytest tests/test_run_ablations.py::test_phase7_run_name -x` | Wave 0 |
| SC-1 | CLI overrides forwarded to train_cmd | unit | `pytest tests/test_run_ablations.py::test_phase7_cli_overrides -x` | Wave 0 |
| SC-1 | train.py --lr and --k-topk parsed and applied | unit | `pytest tests/test_train.py::test_cli_lr_override -x` | Wave 0 |
| SC-2 | Sweep results logged to results-index.csv | integration | `pytest tests/test_run_ablations.py::test_run_one_success_appends_index -x` | Existing (reusable) |
| SC-3 | RTFM diagnostic produces comparison output | smoke | Manual: `python scripts/rtfm_gap_diagnostic.py` | Wave 0 |
| SC-4 | Heatmap PNG generated from results-index.csv | smoke | Manual: `python scripts/generate_phase7_charts.py` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_run_ablations.py tests/test_train.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_run_ablations.py` -- add test_phase7_sweep_queue, test_phase7_run_name, test_phase7_cli_overrides (extend existing file)
- [ ] `tests/test_train.py` -- add test_cli_lr_override, test_cli_k_topk_override (extend existing file)

## Existing Infrastructure Baseline

### Training Convergence Data (XD Gated Fusion)
[VERIFIED: results/xd_gated_fusion_s42/train_log.csv]

| Property | Value |
|----------|-------|
| Total epochs | 24 (0-23) |
| Best val_loss epoch | 13 |
| Best val_loss | 0.272038 |
| Early stopping triggered | Yes (epoch 23, patience=10) |
| Training time | ~2-3 min per run |

### Wall-Clock Estimates
[VERIFIED: results-index.csv timestamps]

| Phase | Runs | Per Run | Total |
|-------|------|---------|-------|
| Sweep (20 runs) | 20 | ~2-3 min | ~40-60 min |
| Confirmation (3 runs) | 3 | ~2-3 min | ~6-9 min |
| Diagnostics | 4 | ~5 min each | ~20 min |
| Chart generation | 1 | ~2 min | ~2 min |
| **Total** | -- | -- | **~70-90 min** |

### Phase 4c Baseline Numbers (Comparison Targets)
[VERIFIED: results/results-index.csv]

| Run | AP | AUC |
|-----|-----|-----|
| xd_gated_fusion_s42 | 0.7192 | 0.9200 |
| xd_gated_fusion_s123 | 0.7120 | 0.9173 |
| xd_gated_fusion_s2024 | 0.6980 | 0.9142 |
| 3-seed mean | 0.7097 +/- 0.0108 | 0.9172 +/- 0.0029 |

### Per-Category Baseline (xd_gated_fusion_s42)
[VERIFIED: results/xd_gated_fusion_s42/per_category.csv]

| Category | Code | AP | AUC |
|----------|------|-----|-----|
| Fighting | B1 | 0.7776 | 0.9673 |
| Shooting | B2 | 0.5135 | 0.9729 |
| Riot | B4 | 0.8815 | 0.9763 |
| Abuse | B5 | 0.4489 | 0.9734 |
| Car Accident | B6 | 0.4154 | 0.9545 |
| Explosion | G | 0.5402 | 0.9758 |

### RTFM I3D Baseline
[VERIFIED: results/xd_i3d_rtfm_i3d_s42/eval_metrics.json]

| Run | AP | AUC |
|-----|-----|-----|
| xd_i3d_rtfm_i3d_s42 (RGB) | 0.6570 | 0.8675 |
| xd_i3d_rtfm_i3d_flow_s42 | 0.5916 | 0.8341 |
| RTFM published (I3D-RGB) | 0.7781 | -- |
| Gap (RGB) | -12.11 pp | -- |

## Security Domain

Phase 7 involves no authentication, session management, access control, or cryptographic operations. All data is local (E:/ features, results/ directory). No network services, no user input from external sources.

Security enforcement: Not applicable -- this is an offline ML experiment with no external interfaces.

## Sources

### Primary (HIGH confidence)
- Codebase files: `scripts/run_ablations.py`, `src/train.py`, `src/evaluate.py`, `src/losses/mil_loss.py`, `configs/gated_fusion_xd.yaml`, `src/eval/snippet_to_frame.py`, `src/eval/xd_annotations.py`, `src/utils/csv_logger.py`, `scripts/generate_phase4_charts.py` -- all read in full
- `results/results-index.csv` -- 18 Phase 4/4b/4c rows + TTA rows verified
- `results/xd_gated_fusion_s42/eval_metrics.json` -- AP=0.7192, AUC=0.9200 verified
- `.planning/phases/07-xd-violence-hyperparameter-sweep/07-CONTEXT.md` -- 15 locked decisions
- `.planning/phases/04C-xd-violence-main-results/04C-CONTEXT.md` -- Phase 4c decisions and conventions
- `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-CONTEXT.md` -- Phase 4b RTFM gate decisions

### Secondary (MEDIUM confidence)
- RTFM official code (WebFetch verified): `option.py` (lr=0.001, batch_size=32, feature-size=2048), `model.py` (k=num_segments//10=3), `train.py` (margin=100, sparsity=8e-3, smoothness=8e-4)
- RTFM test_10crop.py (WebFetch verified): `np.repeat(pred, 16)` snippet-to-frame expansion
- XDVioDet test.py (WebFetch verified): same `np.repeat(pred, 16)` pattern
- [RTFM GitHub](https://github.com/tianyu0207/RTFM) -- official ICCV 2021 code
- [XDVioDet GitHub](https://github.com/Roc-Ng/XDVioDet) -- official ECCV 2020 code
- [RTFM GitHub Issue #72](https://github.com/tianyu0207/RTFM/issues/72) -- user reports inability to reproduce XD results (no resolution)

### Tertiary (LOW confidence)
- [RTFM paper](https://arxiv.org/abs/2101.10030) -- k=3 default mentioned in ablation; exact sensitivity numbers not extracted from PDF

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies; all tools already in vcc-main
- Architecture: HIGH -- extends existing run_ablations.py orchestration pattern with minimal changes
- Pitfalls: HIGH -- all pitfalls derived from verified codebase analysis + RTFM code inspection
- RTFM gap analysis: HIGH -- training regime differences verified from official RTFM repo code

**Research date:** 2026-05-01
**Valid until:** 2026-06-01 (stable -- no external dependency changes expected)
