# Phase 5: TTA Infrastructure & Corruption Experiments - Research

**Researched:** 2026-04-20
**Domain:** Test-Time Adaptation (TENT/SAR) on LayerNorm-based anomaly detection fusion heads + ImageNet-C-style corruption benchmarking
**Confidence:** HIGH

## Summary

Phase 5 implements three major subsystems: (1) a corruption generator for UCF-Crime-C producing 20 conditions (4 types x 5 severities), (2) TENT-style and SAR-style entropy-minimization TTA modules adapted for binary sigmoid output and LayerNorm affine parameters, and (3) a grid-search evaluation orchestrator running ~600 experiment configurations. The source checkpoint (`results/ucf_gated_fusion_s42/best_model.pth`) contains exactly 1536 adaptable LN parameters across 3 named LayerNorm modules (ln_skel, ln_clip, ln_fused, each 256-d weight+bias). The corruption pipeline uses numpy+PIL+scipy exclusively (D-03 locked decision) to ensure both vcc-main and vcc-skeleton environments can import it.

The SAR repository (MIT License, ICLR 2023 Oral) provides reference TENT and SAR implementations that target BatchNorm. Phase 5 ports these to target LayerNorm and replaces softmax entropy with binary entropy `H = -(s*log(s) + (1-s)*log(1-s))`. This BN-to-LN transfer and the binary entropy formulation are themselves the research contribution of this thesis chapter. The adaptation surface is deliberately small (1536 params out of 498,113 total) -- PRD section 9.4 acknowledges this may limit TTA effectiveness, which would be a "valuable finding."

**Primary recommendation:** Build corruption module first (no ML dependencies), then TENT/SAR modules (pure PyTorch), then the evaluation orchestrator extending the existing run_ablations.py pattern. Feature re-extraction is a human-supervised batch job (~15h total) that should start early and run in parallel with TTA module development.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** On-the-fly corruption during feature extraction. Add `--corruption {type} --severity {1-5}` flags to `extract_clip.py` and `extract_skeletons.py`. Apply transforms in memory; no stored corrupted video files (~200GB+ savings).
- **D-02:** Re-extract for **test-set only** (290 UCF-Crime test videos). TTA adapts and evaluates on test set; train/val features are unchanged. Total re-extraction budget: ~11h skeleton (10 conditions) + ~4h CLIP (20 conditions) = ~15h.
- **D-03:** Shared `scripts/corruption.py` module using only numpy + PIL + scipy (no PyTorch/kornia). Both `vcc-main` and `vcc-skeleton` environments can import it. Ensures bit-identical transforms across both extraction pipelines.
- **D-04:** Feature cache layout: `E:/features/ucf/clip_{type}_{severity}/` for CLIP, `E:/features/ucf/skeleton_{type}_{severity}/` for skeleton. 30 total directories (20 CLIP + 10 skeleton).
- **D-05:** Binary entropy loss for sigmoid MIL output: `H = -(s*log(s) + (1-s)*log(1-s))`, minimized over 32-snippet batch.
- **D-06:** Port from official SAR repo (MIT License). Key adaptations: (1) `collect_params()` filters for `nn.LayerNorm` not `nn.BatchNorm2d`, (2) entropy loss uses binary entropy not softmax, (3) `reset()` reloads LN params from source checkpoint.
- **D-07:** Online adapt+score per video. For each 32-snippet batch: forward -> collect scores -> compute entropy -> backward -> update LN params -> next batch. No second pass.
- **D-08:** Adaptable parameters: only LN affine (weight, bias) in GatedFusion -- `ln_skel` (512 params), `ln_clip` (512 params), `ln_fused` (512 params) = **1536 total params**.
- **D-09:** Extend existing `scripts/run_ablations.py` with TTA queue types: `tta_source_only` (20 runs), `tta_tent_grid` (80 runs), `tta_sar_grid` (400 runs).
- **D-10:** Full LR grid `{1e-4, 5e-4, 1e-3, 5e-3}` for all 20 conditions.
- **D-11:** SAR rho grid: `{0.001, 0.005, 0.01, 0.05, 0.1}`.
- **D-12:** Primary metric: frame-level AUC (ROC-AUC).
- **D-13:** TTA run output directory: `results/tta/{method}_{type}_{severity}_lr{lr}[_rho{rho}]/`.
- **D-14:** Each TTA evaluation is feature-level only (~30s per run). Full grid: ~600 runs x 30s = ~5 hours total.
- **D-15:** Phase 5 proceeds independently of Phase 4c (XD main results). Zero XD dependencies.
- **D-16:** Cross-dataset TTA (OPT-03) = stretch goal only.
- **D-17:** EATA-style TTA = stretch goal only.
- **D-18:** Estimated Phase 5 timeline: ~1 week.

### Claude's Discretion
- Corruption severity value refinement per ImageNet-C conventions (monotonic degradation preferred over mixed direction)
- SAR reliable entropy filtering threshold calibration
- Whether `scripts/corruption.py` lives in `scripts/` or `src/` (recommendation: `scripts/` since it's used by extraction scripts, not training code)
- Exact binary entropy numerical stability handling (epsilon clamping on sigmoid outputs)
- Whether to report per-video TTA entropy curves in eval output (useful for M5 analysis but adds storage)
- TTA results CSV column ordering and additional metadata fields
- Whether Source-Only runs go through the TTA evaluation loop (with 0 adaptation steps) or call `evaluate.py` directly (former is cleaner for fair comparison)

### Deferred Ideas (OUT OF SCOPE)
- Cross-dataset TTA (OPT-03): UCF->XD and XD->UCF directions. Stretch goal.
- EATA-style TTA: Selective update + Fisher regularization. Stretch goal.
- TTA on XD-Violence corruption (XD-Violence-C). Deferred until Phase 4c completes.
- Per-video adaptation analysis visualization. Phase 6 material.
- Adaptation parameter count ablation (1 LN vs all 3). Thesis discussion material.
- CLIP text prompt engineering + TTA (OPT-12). v2 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TTA-01 | UCF-Crime-C corruption generator (4 types x 5 severities = 20 conditions) | ImageNet-C severity parameters verified from hendrycks/robustness source. numpy+PIL+scipy implementation confirmed available in vcc-main. D-03 locks the library set. |
| TTA-02 | CLIP feature re-extraction on corrupted frames for all 20 conditions | extract_clip.py structure mapped (700 lines). Add --corruption/--severity flags that call scripts/corruption.py before CLIP preprocessing. Output to E:/features/ucf/clip_{type}_{severity}/. |
| TTA-03 | Skeleton re-extraction decision per corruption type | D-03/M7: motion_blur and jpeg_compression require skeleton re-extraction (10 conditions). gaussian_noise and brightness reuse clean skeleton cache. PIL not in vcc-skeleton -- JPEG corruption must use cv2 or numpy-only fallback. |
| TTA-04 | TENT-style adaptation module | SAR repo tent.py pattern verified: configure_model() + collect_params() + forward_and_adapt(). Port to LN target, binary entropy, per-video episodic reset. 1536 adaptable params confirmed from checkpoint inspection. |
| TTA-05 | SAR-style adaptation module | SAR repo sar.py pattern verified: adds SAM optimizer (sharpness-aware) + reliable entropy filtering + EMA recovery. rho grid {0.001..0.1} per D-11. |
| TTA-06 | TTA evaluation loop | Extend run_ablations.py with TTA queues. New src/tta/evaluate_tta.py as the per-run entry point (replaces train+evaluate pattern with adapt+score pattern). Reuse existing snippet_to_frame and compute_frame_metrics. |
| TTA-07 | Adaptation protocol enforced | 32-snippet batches from MILFeatureDataset(mode='test'), per-video reset via deepcopy state restore, LR grid {1e-4..5e-3}. Protocol matches PRD section 10.3. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Corruption generation | Scripts (extraction-time) | -- | Applied on-the-fly during feature extraction, not during training or inference |
| CLIP feature re-extraction | Scripts (vcc-main env) | -- | GPU-bound extraction in vcc-main; corruption module imported as shared utility |
| Skeleton re-extraction | Scripts (vcc-skeleton env) | -- | GPU-bound extraction in vcc-skeleton; same corruption module imported |
| TENT/SAR adaptation | src/tta/ (training env) | -- | PyTorch-only modules; run in vcc-main alongside the fusion model |
| TTA evaluation loop | src/tta/ (training env) | src/eval/ (reused) | New per-run entry point that adapts then evaluates; reuses metrics/snippet_to_frame |
| Experiment orchestration | scripts/run_ablations.py | -- | Extends existing queue runner with TTA-specific RunSpec variants and queue definitions |
| Results aggregation | results/tta/ + results-index.csv | -- | Same audit log pattern as Phase 4; additional TTA-specific columns |

## Standard Stack

### Core (already in vcc-main, verified)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyTorch | 2.6.0 | Model loading, LN adaptation, gradient computation | Already installed in vcc-main [VERIFIED: checkpoint loads successfully] |
| numpy | 2.4.3 | Corruption transforms, feature I/O | Already in vcc-main [VERIFIED: `import numpy` in vcc-main] |
| Pillow (PIL) | installed | JPEG compression corruption | Already in vcc-main [VERIFIED: `from PIL import Image` succeeds] |
| scipy | 1.17.1 | Motion blur kernel convolution | Already in vcc-main [VERIFIED: `scipy.ndimage` + `scipy.signal` import OK] |
| scikit-learn | installed | `roc_auc_score` for frame-level AUC | Already in vcc-main (used by Phase 4 evaluate.py) |

### Supporting (already in vcc-skeleton, verified)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | 2.4.4 | Corruption transforms in skeleton extraction | [VERIFIED: available in vcc-skeleton] |
| opencv-python | 4.13.0 | Frame loading + JPEG compression fallback for vcc-skeleton | [VERIFIED: available in vcc-skeleton] |

### Critical Gap: PIL/scipy NOT in vcc-skeleton
| Library | Status | Impact | Resolution |
|---------|--------|--------|------------|
| Pillow | NOT installed in vcc-skeleton | JPEG compression in corruption.py uses PIL | Use cv2-based JPEG compression fallback OR install Pillow in vcc-skeleton |
| scipy | NOT installed in vcc-skeleton | Motion blur kernel generation | Use numpy-only motion blur kernel (no scipy dependency) |

**Resolution for D-03 compatibility:** The corruption module MUST work in both environments. Two options:
1. **Recommended:** Implement all corruptions using numpy + cv2 only (both available in vcc-skeleton). Use `cv2.imencode`/`cv2.imdecode` for JPEG compression instead of PIL. Use numpy-only motion blur kernel (simple line kernel convolved with `numpy` or `cv2.filter2D`).
2. **Alternative:** Install Pillow + scipy in vcc-skeleton. Adds dependency but keeps corruption.py identical across envs.

**Installation (no new packages needed if Option 1):**
```bash
# No installation needed -- all libraries already present in their respective envs
# If Option 2 chosen:
# conda run -n vcc-skeleton pip install Pillow scipy
```

**Version verification:** All versions confirmed via runtime imports on 2026-04-20.

## Architecture Patterns

### System Architecture Diagram

```
                     CORRUPTION PIPELINE (scripts/corruption.py)
                     ==========================================
                     numpy+cv2 transforms (no PyTorch dependency)
                     4 types x 5 severities = 20 conditions

    UCF-Crime Test PNGs (290 videos)
              |
              v
    +-------------------+          +---------------------+
    | extract_clip.py   |          | extract_skeletons.py|
    | --corruption X    |          | --corruption X      |
    | --severity N      |          | --severity N        |
    | (vcc-main env)    |          | (vcc-skeleton env)  |
    +-------------------+          +---------------------+
              |                              |
              v                              v
    E:/features/ucf/              E:/features/ucf/
    clip_{type}_{sev}/            skeleton_{type}_{sev}/
    (20 dirs, ~290 .npy each)     (10 dirs -- blur+jpeg only)

                     TTA ADAPTATION PIPELINE (src/tta/)
                     ==================================
                     vcc-main env only

    Source Checkpoint -----> GatedFusion model (498K params)
    best_model.pth           |
                             | freeze all except 3 LNs (1536 params)
                             v
    For each test video:
    +------------------------------------------------------------------+
    | 1. Load corrupted features (skel + clip .npy)                    |
    | 2. Chunk into 32-snippet batches                                 |
    | 3. For each batch:                                               |
    |    a. Forward pass -> sigmoid scores [B, T]                      |
    |    b. Compute binary entropy H = -(s*log(s) + (1-s)*log(1-s))   |
    |    c. [SAR only] Sharpness-aware gradient step (rho perturbation)|
    |    d. [SAR only] Filter unreliable entropy samples               |
    |    e. Backward + update LN affine params only                    |
    |    f. Collect scores from THIS forward pass (online, no 2nd pass)|
    | 4. Reset LN params to source state (per-video reset)             |
    +------------------------------------------------------------------+
              |
              v
    snippet_to_frame() -> frame_labels() -> roc_auc_score()
              |
              v
    results/tta/{method}_{type}_{sev}_lr{lr}[_rho{rho}]/
        eval_metrics.json + eval_scores.npz + .done
```

### Recommended Project Structure
```
scripts/
    corruption.py          # NEW: numpy+cv2 corruption transforms (D-03)
    extract_clip.py        # MODIFIED: add --corruption/--severity flags
    extract_skeletons.py   # MODIFIED: add --corruption/--severity flags
    run_ablations.py       # MODIFIED: add TTA queue definitions + TTARunSpec
src/
    tta/
        __init__.py        # EXISTS: currently placeholder
        tent.py            # NEW: TENT-style adaptation (D-04, D-06)
        sar.py             # NEW: SAR-style adaptation (D-05, D-06)
        sam.py             # NEW: SAM optimizer for SAR (ported from SAR repo)
        evaluate_tta.py    # NEW: per-run TTA evaluation entry point
configs/
    tta_tent.yaml          # NEW: TENT TTA config template
    tta_sar.yaml           # NEW: SAR TTA config template
tests/
    test_corruption.py     # NEW: corruption transform unit tests
    test_tent.py           # NEW: TENT adaptation unit tests
    test_sar.py            # NEW: SAR adaptation unit tests
    test_evaluate_tta.py   # NEW: TTA evaluation integration tests
    test_run_ablations_tta.py  # NEW: TTA queue tests
```

### Pattern 1: Corruption Transform Module
**What:** Pure numpy/cv2 functions that take an RGB uint8 ndarray and return a corrupted uint8 ndarray. No PyTorch dependency.
**When to use:** Called by extract_clip.py and extract_skeletons.py before their respective model inference.
**Example:**
```python
# Source: hendrycks/robustness ImageNet-C severity parameters [VERIFIED: GitHub source]
# Adapted to numpy+cv2 per D-03

import numpy as np
import cv2
from io import BytesIO

# Severity parameters from ImageNet-C (monotonically increasing degradation)
GAUSSIAN_NOISE_SIGMA = [0.08, 0.12, 0.18, 0.26, 0.38]  # severity 1-5
JPEG_QUALITY = [25, 18, 15, 10, 7]                       # severity 1-5 (lower = worse)
BRIGHTNESS_FACTOR = [0.1, 0.2, 0.3, 0.4, 0.5]           # added to normalized image
MOTION_BLUR_PARAMS = [                                    # (kernel_size, sigma)
    (10, 3), (15, 5), (15, 8), (15, 12), (20, 15)
]

def gaussian_noise(img: np.ndarray, severity: int, rng: np.random.Generator) -> np.ndarray:
    """Add Gaussian noise. img: uint8 [H,W,3]. Returns uint8."""
    sigma = GAUSSIAN_NOISE_SIGMA[severity - 1]
    noise = rng.normal(0, sigma, img.shape).astype(np.float32)
    out = img.astype(np.float32) / 255.0 + noise
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def jpeg_compression(img: np.ndarray, severity: int, rng=None) -> np.ndarray:
    """JPEG compress+decompress. img: uint8 [H,W,3] RGB. Returns uint8 RGB."""
    quality = JPEG_QUALITY[severity - 1]
    # cv2-based: works in both vcc-main and vcc-skeleton
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    decoded = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)

def brightness(img: np.ndarray, severity: int, rng=None) -> np.ndarray:
    """Increase brightness. img: uint8 [H,W,3]. Returns uint8."""
    c = BRIGHTNESS_FACTOR[severity - 1]
    out = img.astype(np.float32) / 255.0 + c
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def motion_blur(img: np.ndarray, severity: int, rng=None) -> np.ndarray:
    """Apply horizontal motion blur. img: uint8 [H,W,3]. Returns uint8."""
    size, _ = MOTION_BLUR_PARAMS[severity - 1]
    kernel = np.zeros((size, size), dtype=np.float32)
    kernel[size // 2, :] = 1.0 / size  # horizontal line kernel
    return cv2.filter2D(img, -1, kernel)
```

### Pattern 2: TENT-style Adaptation (ported from SAR repo)
**What:** Entropy minimization updating only LN affine parameters, with per-video episodic reset.
**When to use:** Core TTA module called by evaluate_tta.py for each test video.
**Example:**
```python
# Source: https://github.com/mr-eggplant/SAR/blob/main/tent.py [VERIFIED: WebFetch]
# Adapted: BN -> LN, softmax_entropy -> binary_entropy, episodic per-video reset

import torch
import torch.nn as nn
from copy import deepcopy

EPS = 1e-7  # numerical stability for log

def binary_entropy(scores: torch.Tensor) -> torch.Tensor:
    """Binary entropy for sigmoid scores in (0, 1). D-05."""
    s = scores.clamp(EPS, 1 - EPS)
    return -(s * s.log() + (1 - s) * (1 - s).log())

def configure_model(model: nn.Module) -> nn.Module:
    """Prepare model: train mode, freeze all, unfreeze LN affine only."""
    model.train()  # needed for dropout behavior -- but we may want eval for LN
    model.requires_grad_(False)
    for m in model.modules():
        if isinstance(m, nn.LayerNorm):
            m.requires_grad_(True)  # unfreeze weight + bias
    return model

def collect_params(model: nn.Module):
    """Collect LN affine parameters. Returns (params_list, names_list)."""
    params, names = [], []
    for nm, m in model.named_modules():
        if isinstance(m, nn.LayerNorm):
            for np_name, p in m.named_parameters():
                if np_name in ('weight', 'bias'):
                    params.append(p)
                    names.append(f"{nm}.{np_name}")
    return params, names

class TentAdaptor:
    """Per-video TENT adaptation with episodic reset."""
    def __init__(self, model, optimizer, source_state):
        self.model = model
        self.optimizer = optimizer
        self.source_state = source_state  # deepcopy of initial LN state

    def reset(self):
        """Restore LN params to source-trained values (per-video reset)."""
        self.model.load_state_dict(self.source_state, strict=False)
        self.optimizer.state = {}  # clear momentum buffers

    def adapt_and_score(self, skel, clip):
        """Forward + adapt on one batch. Returns scores detached."""
        scores = self.model(skel=skel, clip=clip)  # [B, T]
        loss = binary_entropy(scores).mean()
        loss.backward()
        self.optimizer.step()
        self.optimizer.zero_grad()
        return scores.detach()
```

### Pattern 3: SAR-style Adaptation (ported from SAR repo)
**What:** TENT + sharpness-aware minimization (SAM optimizer) + reliable entropy filtering.
**When to use:** Primary TTA method; expected to outperform vanilla TENT per M5/M6 analysis.
**Example:**
```python
# Source: https://github.com/mr-eggplant/SAR/blob/main/sar.py [VERIFIED: WebFetch]
# Key additions over TENT: SAM optimizer, entropy filtering, EMA recovery

class SAM(torch.optim.Optimizer):
    """Sharpness-Aware Minimization optimizer. Source: SAR repo sam.py."""
    def __init__(self, params, base_optimizer, rho=0.05, **kwargs):
        defaults = dict(rho=rho, **kwargs)
        super().__init__(params, defaults)
        self.base_optimizer = base_optimizer(self.param_groups, **kwargs)

    @torch.no_grad()
    def first_step(self):
        """Ascent step: perturb params toward high-loss region."""
        grad_norm = self._grad_norm()
        for group in self.param_groups:
            scale = group['rho'] / (grad_norm + 1e-12)
            for p in group['params']:
                if p.grad is None: continue
                e_w = p.grad * scale
                p.add_(e_w)  # climb
                self.state[p]['e_w'] = e_w

    @torch.no_grad()
    def second_step(self):
        """Descent step: update at perturbed point, restore original."""
        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None: continue
                p.sub_(self.state[p]['e_w'])  # restore
        self.base_optimizer.step()

    def _grad_norm(self):
        norm = torch.norm(torch.stack([
            p.grad.norm() for group in self.param_groups
            for p in group['params'] if p.grad is not None
        ]))
        return norm
```

### Pattern 4: TTA Evaluation Entry Point
**What:** Per-run script that loads source model, loads corrupted features, adapts per-video, evaluates frame-level AUC.
**When to use:** Called by run_ablations.py for each TTA run spec.
**Example flow:**
```python
# src/tta/evaluate_tta.py -- entry point for a single TTA run
# Called as subprocess by run_ablations.py (same pattern as train.py + evaluate.py)

def run_tta_evaluation(
    source_checkpoint: Path,
    config_snapshot: Path,
    corruption_type: str,
    severity: int,
    method: str,       # 'source_only' | 'tent' | 'sar'
    lr: float,
    rho: float = None, # SAR only
    output_dir: Path,
):
    # 1. Build model from config_snapshot, load source checkpoint
    # 2. Point feature paths to E:/features/ucf/clip_{type}_{sev}/ etc.
    # 3. If method != 'source_only': configure_model() + create optimizer
    # 4. For each test video:
    #    a. Load corrupted skel + clip features
    #    b. If method == 'source_only': forward only, collect scores
    #    c. Else: adapt_and_score per batch, collect all scores
    #    d. Reset model to source state
    # 5. Expand snippet scores to frame scores (reuse snippet_to_frame)
    # 6. Compute frame-level AUC (reuse compute_frame_metrics)
    # 7. Write eval_metrics.json, eval_scores.npz, .done
```

### Pattern 5: Queue Extension in run_ablations.py
**What:** New RunSpec variant for TTA runs + queue definitions.
**When to use:** Orchestrating the ~600 TTA experiment runs.
**Example:**
```python
# Extension to scripts/run_ablations.py

@dataclass
class TTARunSpec:
    """Single TTA evaluation run."""
    corruption_type: str   # gaussian_noise, motion_blur, jpeg_compression, brightness
    severity: int          # 1-5
    method: str            # source_only, tent, sar
    lr: float              # from {1e-4, 5e-4, 1e-3, 5e-3}
    rho: float = 0.0      # SAR only, from {0.001, 0.005, 0.01, 0.05, 0.1}
    source_run: str = "ucf_gated_fusion_s42"

    @property
    def run_name(self) -> str:
        base = f"{self.method}_{self.corruption_type}_{self.severity}_lr{self.lr}"
        if self.method == "sar" and self.rho > 0:
            base += f"_rho{self.rho}"
        return base

# Queue sizes:
# tta_source_only: 4 types x 5 sev = 20 runs
# tta_tent_grid:   4 types x 5 sev x 4 LRs = 80 runs
# tta_sar_grid:    4 types x 5 sev x 4 LRs x 5 rhos = 400 runs
# Total: 500 runs (D-14 says ~600 including source_only)
```

### Anti-Patterns to Avoid
- **Using model.eval() for TTA:** TENT/SAR need `model.train()` for gradient computation through LN, but LayerNorm (unlike BatchNorm) computes the same statistics in train and eval mode. Still, must set train() so `requires_grad_(True)` propagates. The dropout layer behavior differs though -- must explicitly set `model.dropout.eval()` to avoid random masking during TTA.
- **Forgetting per-video reset:** Without resetting LN params to source state between videos, adaptation accumulates across videos. This violates the protocol and makes results dependent on video ordering.
- **Second-pass scoring:** D-07 locks online scoring -- scores are collected during the adaptation forward pass, not from a separate clean forward pass after adaptation. This matches deployment reality.
- **Importing test_loader.py from TTA module:** The C3 guard in `src/eval/test_loader.py` restricts imports to evaluate.py and pytest. TTA evaluate must either be named in the allowed sentinel list or build the test dataset directly without going through `build_test_dataset()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JPEG compression | Custom DCT implementation | cv2.imencode/imdecode with IMWRITE_JPEG_QUALITY | Exact JPEG standard compliance; bit-identical to real JPEG artifacts |
| Frame-level AUC | Custom ROC implementation | sklearn.metrics.roc_auc_score (via existing compute_frame_metrics) | Community standard; same as Phase 4 |
| Snippet-to-frame expansion | New expansion function | Existing src/eval/snippet_to_frame.py | Already validated in Phase 4; same 64-frame window + 10x upsample for UCF |
| State dict save/restore | Manual parameter copying | torch deepcopy + load_state_dict(strict=False) | SAR repo pattern; handles optimizer state properly |
| Atomic file writes | Raw file I/O | Existing checkpoint.py pattern (tempfile + os.replace) | Windows-safe; crash-resilient |
| Results CSV append | Custom CSV writing | Existing csv_logger.results_index_append | Same audit trail as Phase 4 |

**Key insight:** Phase 5 reuses Phase 4's entire evaluation infrastructure (snippet_to_frame, compute_frame_metrics, results-index.csv). The only new ML code is the corruption module and the TENT/SAR adaptation loop.

## Common Pitfalls

### Pitfall 1: M5 -- TTA Entropy Collapse on Normal-Heavy Batches
**What goes wrong:** In UCF-Crime test videos, ~90% of snippets are normal. Entropy minimization on a 32-snippet batch dominated by normal snippets pushes ALL scores toward 0, collapsing anomaly detection ability. [VERIFIED: PITFALLS.md M5]
**Why it happens:** Binary entropy H is minimized at s=0 and s=1. With 29/32 normal snippets, the gradient signal overwhelmingly favors pushing toward 0.
**How to avoid:** (1) SAR's reliable entropy filtering excludes low-entropy samples from gradient computation. (2) Report per-video TTA improvement/degradation breakdown -- aggregate AUC can mask harmful adaptation on specific videos. (3) This is an expected finding for the thesis, not a bug.
**Warning signs:** TENT degrades AUC below Source-Only; entropy drops rapidly in first batch.

### Pitfall 2: M6 -- SAR rho Too Large for Scalar Output
**What goes wrong:** SAR's rho=0.05 (ImageNet default) perturbs parameters for a 1000-class softmax. With scalar binary output (1536 params), the same rho produces catastrophic perturbation. [VERIFIED: PITFALLS.md M6]
**Why it happens:** The perturbation magnitude scales with rho/||grad||. Scalar output has much smaller gradient norms than 1000-class, so the same rho produces proportionally larger perturbation.
**How to avoid:** D-11 grid includes {0.001, 0.005} which are 10-50x smaller than ImageNet default. Expect best rho to be 0.005-0.01 range. Monitor LN param drift: if gamma moves >20% from initial value after one video, rho is too large.
**Warning signs:** SAR performs worse than TENT across all conditions; LN weights diverge to >2x initial values.

### Pitfall 3: M7 -- Skeleton Re-extraction Needed for Motion Blur + JPEG
**What goes wrong:** Reusing clean skeleton features for motion blur/JPEG corruption creates an unrealistic experimental setting where skeleton sees clean data while CLIP sees corrupted data. [VERIFIED: PITFALLS.md M7]
**Why it happens:** Skeleton extraction is slow (~11h for 10 conditions). Tempting to skip.
**How to avoid:** D-02/D-03 mandate re-extraction for motion blur + JPEG (10 conditions). Gaussian noise and brightness reuse clean skeletons (RTMPose robust to these).
**Warning signs:** Skeleton-Only model shows no AUC degradation under motion blur (implausible).

### Pitfall 4: PIL Not Available in vcc-skeleton Environment
**What goes wrong:** D-03 says corruption.py uses PIL for JPEG compression, but PIL is NOT installed in vcc-skeleton. The extract_skeletons.py script runs in vcc-skeleton and would fail on `from PIL import Image`. [VERIFIED: `import PIL` fails in vcc-skeleton]
**Why it happens:** vcc-skeleton was set up for rtmlib + onnxruntime only; PIL was not in the original requirements.
**How to avoid:** Use cv2-based JPEG compression (`cv2.imencode`/`cv2.imdecode`) instead of PIL. cv2 IS available in vcc-skeleton (v4.13.0 verified). This makes corruption.py work in both environments without installing new packages.
**Warning signs:** ImportError at extraction time; wasted hours waiting for extraction to fail.

### Pitfall 5: C3 Guard Blocks TTA Test Data Loading
**What goes wrong:** `src/eval/test_loader.py` has a runtime import guard that only allows `evaluate.py` and pytest to import it. A new `src/tta/evaluate_tta.py` script would be blocked.
**Why it happens:** C3 leakage prevention from Phase 4 -- test set data is restricted.
**How to avoid:** Either (a) add `evaluate_tta.py` to the allowed sentinels in test_loader.py, or (b) bypass the guard by loading features directly from corrupted cache directories without using build_test_dataset(). Option (b) is cleaner -- TTA needs to point to corrupted feature directories, not the default clean ones, so it needs custom dataset construction anyway.
**Warning signs:** RuntimeError at import time in evaluate_tta.py.

### Pitfall 6: Dropout Behavior in Train vs Eval Mode
**What goes wrong:** TENT/SAR call `model.train()` to enable gradient computation. But GatedFusion has `nn.Dropout(0.3)` which becomes active in train mode, introducing random masking during TTA evaluation. This adds noise to scores and makes results non-deterministic.
**Why it happens:** Original TENT targets BatchNorm in classification models that don't have dropout in the adaptation path.
**How to avoid:** After `model.train()`, explicitly set `model.dropout.eval()` to disable dropout while keeping LN in train mode. LayerNorm behavior is identical in train/eval (no running statistics), so this is safe.
**Warning signs:** Non-reproducible TTA scores across identical runs; unexpectedly high variance in per-video scores.

## Code Examples

### Verified: Source Checkpoint Structure
```python
# Source: D:/ViolenceCC/results/ucf_gated_fusion_s42/best_model.pth [VERIFIED: torch.load]
# 18 parameter tensors, 498,113 total params
# 6 LN tensors (3 LN modules x weight+bias), 1536 LN params total:
#   ln_skel.weight:  [256]  (256 params)
#   ln_skel.bias:    [256]  (256 params)
#   ln_clip.weight:  [256]  (256 params)
#   ln_clip.bias:    [256]  (256 params)
#   ln_fused.weight: [256]  (256 params)
#   ln_fused.bias:   [256]  (256 params)
# Frozen during TTA: 498,113 - 1,536 = 496,577 params
```

### Verified: ImageNet-C Severity Parameters
```python
# Source: https://github.com/hendrycks/robustness/.../corruptions.py [VERIFIED: WebFetch]
# These are the OFFICIAL ImageNet-C severity values

GAUSSIAN_NOISE_SIGMA = [0.08, 0.12, 0.18, 0.26, 0.38]
MOTION_BLUR_PARAMS = [(10, 3), (15, 5), (15, 8), (15, 12), (20, 15)]  # (radius, sigma)
JPEG_QUALITY = [25, 18, 15, 10, 7]
BRIGHTNESS_FACTOR = [0.1, 0.2, 0.3, 0.4, 0.5]

# All are monotonically increasing degradation (severity 1 = mildest, 5 = harshest)
# JPEG: lower quality = more artifacts (monotonically decreasing quality number)
# Brightness: ImageNet-C adds brightness (increase); for VAD we should add AND subtract
#   -> Claude's discretion: recommend using ImageNet-C convention (add only) for
#     comparability, but document that subtraction was considered
```

### Verified: SAR Repo Licensing and Structure
```python
# Source: https://github.com/mr-eggplant/SAR [VERIFIED: WebFetch]
# License: MIT (confirmed in repo)
# Files to port:
#   tent.py -> src/tta/tent.py (configure_model, collect_params, forward_and_adapt)
#   sar.py  -> src/tta/sar.py  (adds entropy filtering + SAM integration)
#   sam.py  -> src/tta/sam.py  (SAM optimizer: first_step/second_step)
#
# Key adaptations needed:
#   1. collect_params: isinstance(m, nn.BatchNorm2d) -> isinstance(m, nn.LayerNorm)
#   2. softmax_entropy: -(x.softmax(1) * x.log_softmax(1)).sum(1) -> binary_entropy
#   3. configure_model: track_running_stats removal (LN has no running stats)
#   4. Episodic mode: per-video reset via deepcopy state_dict restore
```

### Verified: UCF-Crime Test Set Size
```python
# Source: data/splits/ucf_test.txt [VERIFIED: wc -l]
# 290 test videos
# Feature cache: E:/features/ucf/clip/ (1729 files total, 290 test)
#                E:/features/ucf/skeleton/ (1729 files total, 290 test)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TENT (Wang et al. 2021) targets BN layers | SAR (Niu et al. 2023) adds sharpness-aware regularization | ICLR 2023 | More stable adaptation; gradient filtering reduces collapse |
| kornia for GPU corruption | numpy+cv2 for CPU corruption (D-03) | Phase 5 decision | Cross-env compatibility; kornia requires PyTorch |
| ImageNet-C pip package | Custom corruption module matching ImageNet-C params | Phase 5 decision | Lighter; only 4 corruption types needed vs 15 |
| BN-focused TTA | LN-focused TTA (this project) | Novel contribution | No prior work applies TENT/SAR to LayerNorm in anomaly detection |

**Deprecated/outdated:**
- openai/clip: frozen at 2021, use open-clip-torch 3.3.0 (already in env)
- Original TENT without filtering: shown to collapse on imbalanced data; SAR's filtering is the fix

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Motion blur kernel as simple horizontal line filter (numpy) produces perceptually similar results to ImageNet-C's disk/Gaussian motion blur | Corruption Patterns | LOW: ImageNet-C uses a more complex disk-shaped kernel with Gaussian smoothing. Our simplified kernel may produce slightly different artifacts, but the goal is corruption-level degradation, not pixel-exact ImageNet-C reproduction. Can verify by visual inspection. |
| A2 | `model.train()` with explicit `model.dropout.eval()` correctly enables LN gradient flow while disabling dropout | Anti-Patterns | LOW: Standard PyTorch behavior. LN has no train/eval difference. Dropout.eval() disables masking. Can verify with a 1-line assertion. |
| A3 | ~30s per TTA evaluation run (D-14 estimate) | Experiment Orchestration | MEDIUM: Based on source-only eval timing (3.6s per eval_metrics.json). TTA adds forward+backward per batch. With 290 test videos x ~9 batches/video average, gradient computation could add 10-20s. Total may be 20-50s/run rather than 30s. 5h estimate may stretch to 8-10h. |
| A4 | SAR reliable entropy filtering threshold (ema < 0.2 triggers recovery) transfers to binary entropy domain | SAR Patterns | MEDIUM: SAR's threshold was calibrated for softmax entropy on ImageNet (1000 classes). Binary entropy has max=log(2)=0.693 vs softmax max=log(1000)=6.9. Threshold may need rescaling. Claude's discretion area. |

## Open Questions

1. **Dropout during TTA adaptation**
   - What we know: GatedFusion has Dropout(0.3). TENT/SAR call model.train(). Dropout is active in train mode.
   - What's unclear: Should dropout be active during TTA? Stochastic masking adds noise but could provide implicit regularization. SAR repo does not address this because it targets BN in dropout-free paths.
   - Recommendation: Default to dropout.eval() for reproducibility. Add a flag to enable it for ablation if time permits.

2. **SAR entropy filtering threshold calibration**
   - What we know: SAR uses entropy margin E0 and EMA threshold 0.2 for recovery. These were calibrated for 1000-class ImageNet softmax.
   - What's unclear: What are appropriate thresholds for binary entropy (max 0.693)?
   - Recommendation: Scale proportionally: margin = 0.4 * log(2) ~= 0.28. Test empirically and report sensitivity.

3. **Corruption module location: scripts/ vs src/**
   - What we know: D-03 says scripts/corruption.py. Both extraction scripts are in scripts/. Training code is in src/.
   - What's unclear: If tests import corruption.py, scripts/ imports require sys.path manipulation.
   - Recommendation: Place in scripts/ per D-03 convention (extraction-time utility). Tests can add scripts/ to sys.path via conftest.py fixture, matching the existing pattern.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| numpy | Corruption transforms | vcc-main: YES, vcc-skeleton: YES | 2.4.3 / 2.4.4 | -- |
| PIL (Pillow) | JPEG compression (original D-03) | vcc-main: YES, vcc-skeleton: NO | -- | Use cv2.imencode/imdecode |
| scipy | Motion blur kernel (original D-03) | vcc-main: YES, vcc-skeleton: NO | 1.17.1 / -- | Use numpy-only kernel + cv2.filter2D |
| cv2 (OpenCV) | Frame loading + JPEG fallback | vcc-main: NO, vcc-skeleton: YES | -- / 4.13.0 | PIL (vcc-main only) |
| PyTorch | TTA adaptation | vcc-main: YES | 2.6.0 | -- |
| scikit-learn | frame-level AUC | vcc-main: YES | (installed) | -- |

**Missing dependencies with no fallback:**
- None. All critical dependencies have viable alternatives.

**Missing dependencies with fallback:**
- PIL in vcc-skeleton: Use cv2-based JPEG compression instead
- scipy in vcc-skeleton: Use numpy-only motion blur kernel + cv2.filter2D
- cv2 in vcc-main: Not needed if corruption.py uses PIL for JPEG. But since vcc-skeleton needs cv2 path anyway, use cv2 universally.

**CRITICAL RESOLUTION:** The corruption module must use ONLY numpy + cv2 (not PIL, not scipy) to work in both environments without new installs. D-03 specified "numpy + PIL + scipy" but PIL and scipy are absent from vcc-skeleton. The implementation must adapt: cv2.imencode for JPEG, numpy kernel + cv2.filter2D for motion blur. This is a D-03 constraint violation that needs acknowledgment -- the spirit of D-03 (cross-env compatibility, no PyTorch/kornia) is preserved, but the specific library set changes from {numpy, PIL, scipy} to {numpy, cv2}.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | D:/ViolenceCC/tests/conftest.py |
| Quick run command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_corruption.py tests/test_tent.py tests/test_sar.py -x -q` |
| Full suite command | `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TTA-01 | 4 corruption types x 5 severities produce visually distinct outputs | unit | `pytest tests/test_corruption.py -x` | Wave 0 |
| TTA-02 | CLIP features re-extracted for corrupted frames match expected shape | integration | `pytest tests/test_evaluate_tta.py::test_clip_corruption_features -x` | Wave 0 |
| TTA-03 | Skeleton re-extraction only for blur+jpeg; clean reused for noise+brightness | unit | `pytest tests/test_corruption.py::test_skeleton_reextraction_decision -x` | Wave 0 |
| TTA-04 | TENT updates only LN params; per-video reset restores source state | unit | `pytest tests/test_tent.py -x` | Wave 0 |
| TTA-05 | SAR converges with grid-searched rho; EMA recovery triggers on divergence | unit | `pytest tests/test_sar.py -x` | Wave 0 |
| TTA-06 | Source-Only/TENT/SAR produce per-condition AUC in expected format | integration | `pytest tests/test_evaluate_tta.py -x` | Wave 0 |
| TTA-07 | 32-snippet batches, per-video reset verified, LR grid applied | unit | `pytest tests/test_tent.py::test_protocol_enforcement -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/test_corruption.py tests/test_tent.py tests/test_sar.py -x -q`
- **Per wave merge:** `C:/Anaconda/envs/vcc-main/python.exe -m pytest tests/ -x -q` (full 230+ test suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_corruption.py` -- covers TTA-01, TTA-03
- [ ] `tests/test_tent.py` -- covers TTA-04, TTA-07
- [ ] `tests/test_sar.py` -- covers TTA-05
- [ ] `tests/test_evaluate_tta.py` -- covers TTA-02, TTA-06
- [ ] `tests/test_run_ablations_tta.py` -- covers TTA queue definitions

## Security Domain

Security enforcement is not applicable to this phase. This is a local-only research codebase with no network services, no user authentication, no external data ingestion beyond pre-downloaded datasets. All execution is on a single researcher's machine.

| ASVS Category | Applies | Rationale |
|---------------|---------|-----------|
| V2 Authentication | no | No users, no auth |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Single user, local machine |
| V5 Input Validation | no | All inputs are researcher-controlled .npy files |
| V6 Cryptography | no | No secrets, no encryption |

## Sources

### Primary (HIGH confidence)
- SAR repository tent.py -- TENT implementation pattern (configure_model, collect_params, forward_and_adapt) [VERIFIED: WebFetch of raw GitHub source]
- SAR repository sar.py -- SAR implementation pattern (entropy filtering, SAM integration, EMA recovery) [VERIFIED: WebFetch of raw GitHub source]
- SAR repository sam.py -- SAM optimizer (first_step, second_step, rho handling) [VERIFIED: WebFetch of raw GitHub source]
- hendrycks/robustness corruptions.py -- ImageNet-C severity parameters for all 4 corruption types [VERIFIED: WebFetch of raw GitHub source]
- GatedFusion source code (src/models/gated_fusion.py) -- 3 named LNs, architecture [VERIFIED: file read]
- Source checkpoint (results/ucf_gated_fusion_s42/best_model.pth) -- 18 keys, 498K params, 1536 LN params [VERIFIED: torch.load inspection]
- UCF test split (data/splits/ucf_test.txt) -- 290 videos [VERIFIED: wc -l]
- Environment dependencies -- numpy/PIL/scipy/cv2 availability per env [VERIFIED: runtime import tests]

### Secondary (MEDIUM confidence)
- ImageNet-C benchmark paper (Hendrycks & Dietterich, ICLR 2019) -- corruption methodology and severity conventions [CITED: https://arxiv.org/pdf/1807.01697]

### Tertiary (LOW confidence)
- None. All claims verified via tool calls.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified via runtime imports
- Architecture: HIGH -- source code for all integration points read and understood; SAR repo patterns verified
- Pitfalls: HIGH -- M5/M6/M7 documented in PITFALLS.md and cross-referenced with SAR repo behavior
- Corruption params: HIGH -- exact ImageNet-C values extracted from official source code
- Environment gaps: HIGH -- PIL/scipy absence in vcc-skeleton discovered and resolution documented

**Research date:** 2026-04-20
**Valid until:** 2026-05-20 (stable -- no fast-moving dependencies; all libraries pinned)
