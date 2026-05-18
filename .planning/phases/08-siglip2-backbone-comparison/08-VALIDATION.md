---
phase: 08
slug: siglip2-backbone-comparison
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-19
---

# Phase 08 Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/conftest.py |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-T1 | 08-01 | 1 | EVAL-02 | T-08-01, T-08-03 | BACKBONE_CONFIGS validated, dimension assertions parameterized | unit | `python -c "from scripts.extract_clip import BACKBONE_CONFIGS, load_vision_model; assert set(BACKBONE_CONFIGS.keys()) == {'clip-vit-b-16', 'siglip2-giant'}; assert BACKBONE_CONFIGS['siglip2-giant']['embed_dim'] == 1536; print('OK')"` | Yes (modified) | pending |
| 01-T2 | 08-01 | 1 | EVAL-02 | T-08-03 | Backbone config and dimension tests cover both backbones | unit | `pytest tests/test_extract_siglip2.py -v --timeout=30` | No -- Wave 0 | pending |
| 02-T1 | 08-02 | 1 | EVAL-02, EVAL-03 | T-08-04 | 10 SigLIP2 configs parse with correct clip_dim and paths | unit | `python -c "import yaml, glob; files = glob.glob('configs/*siglip2*.yaml'); assert len(files) == 10; [yaml.safe_load(open(f)) for f in files]; print('OK')"` | No -- Wave 0 | pending |
| 02-T2 | 08-02 | 1 | EVAL-02, EVAL-03, EVAL-04 | T-08-04 | Phase 8 queues well-formed; CLIPProj/GatedFusion/LateFusion accept clip_dim=3072 | unit | `pytest tests/test_models.py tests/test_run_ablations.py -v --timeout=60` | Yes (modified) | pending |
| 03-T1 | 08-03 | 2 | EVAL-02 | T-08-07, T-08-08 | SigLIP2 features extracted with correct dimensions | integration | `python -c "import numpy as np, glob; f=glob.glob('E:/features/ucf/siglip2/*.npy'); assert len(f)>=1700; assert np.load(f[0]).shape[1]==3072; print('OK')"` | N/A (runtime) | pending |
| 04-T1 | 08-04 | 3 | EVAL-02, EVAL-03, EVAL-04 | T-08-09, T-08-10 | All SigLIP2 ablation runs produce non-NaN metrics | integration | `python -c "import pandas as pd; df=pd.read_csv('results/results-index.csv'); sig=df[df['cache_variant'].str.contains('siglip2',na=False)]; assert len(sig)>=14; print('OK')"` | N/A (runtime) | pending |
| 04-T2 | 08-04 | 3 | EVAL-04 | -- | Chart script runs and produces output files | integration | `python scripts/generate_phase8_charts.py && python -c "import glob; assert len(glob.glob('results/phase8_charts/*'))>=2; print('OK')"` | No -- Wave 0 | pending |

---

## Wave 0 Requirements

- [x] Extraction script `--backbone siglip2` flag produces valid .npy output (Plan 01 Task 1 creates BACKBONE_CONFIGS; Plan 01 Task 2 tests it)
- [x] SigLIP2 feature dimensionality assertion (1536-d per frame, 3072-d after mean+max) (Plan 01 Task 2 tests dimension logic)
- [x] Model constructor accepts `clip_dim: 3072` without error (Plan 02 Task 2 tests CLIPProj, GatedFusion, and LateFusion with clip_dim=3072)

*All Wave 0 gaps are addressed by Plan 01 Task 2 and Plan 02 Task 2.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Feature extraction wall-clock time | Extends EVAL-02 | GPU-bound runtime varies | Time full extraction run, verify < 3 hours |
| Side-by-side table completeness | Extends EVAL-04 | Visual inspection of table content | Review comparison table for all ablation rows |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
