# ViolenceCC

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22513205.svg)](https://doi.org/10.5281/zenodo.22513205)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Dual-modal (skeleton + vision-language) fusion for **weakly supervised violence-oriented video anomaly detection**, trained with MIL ranking loss, plus a secondary study of entropy-minimization test-time adaptation (TENT/SAR on LayerNorm) for corruption robustness. Experiment code for the master's thesis of Wei-Han Jeng (National Taiwan University of Science and Technology, 2026; advisor: Chuan-Kai Yang).

Skeleton dynamics come from a frozen CTR-GCN (NTU RGB+D 120, 2D) over RTMPose keypoints; visual-language semantics come from frozen CLIP-family backbones (OpenAI ViT-B/16, SigLIP2 SO400M/Giant). Only the lightweight fusion heads are trained.

## Results

Frame-level metrics, mean ± std over seeds {42, 123, 2024}:

| Model | UCF-Crime (AUC %) | XD-Violence (AP %) |
|---|---|---|
| Skeleton only | 68.8 ± 2.8 | 40.8 ± 0.6 |
| Visual only (CLIP ViT-B/16) | 81.2 | 74.6 |
| Visual only (SigLIP2 Giant) | 82.4 ± 0.2 | 76.8 ± 1.0 |
| **Gated Fusion (headline)** | **82.5 ± 0.4** (SigLIP2 Giant) | **78.7 ± 0.9** (SigLIP2 SO400M) |

Full ablation grids (late fusion, pooling variants, four backbones), the TTA null result, and the disc_reweight robustness gains (+1.21pp mean corrupted-AUC) are in the thesis (`thesis/`) and paper (`paper/`); every published number traces to a tracked source via `thesis/PROVENANCE.md`.

## Repository layout

```
configs/          Per-variant YAML configs (dataset x fusion variant x backbone)
src/              Training, evaluation, models, losses, data loaders, TTA
scripts/          Entry points: extraction, ablation runner, TTA grids, LaTeX builds
data/             Splits, temporal annotations, weight directories (weights not tracked)
results/          Per-run eval metrics (tracked); checkpoints are on Zenodo
envs/             Three-environment setup guide + requirements files
thesis/  paper/   LaTeX sources (buildable; see below)
```

## Environments

Three separate conda environments are required (legacy mmcv pins make a single env impossible). Follow **[envs/SETUP.md](envs/SETUP.md)**:

| Env | Python / Torch | Used for |
|---|---|---|
| `vcc-skeleton` | 3.11 / — (ONNX Runtime) | RTMPose keypoint extraction (rtmlib) |
| `vcc-ctrgcn` | 3.10 / 1.12.1 cu113 | CTR-GCN skeleton features (PYSKL, mmcv-full 1.7.0) |
| `vcc-main` | 3.11 / 2.6.0 cu124 | CLIP extraction, MIL training, evaluation, TTA |

Tier 1 reproduction needs only `vcc-main`.

## Data

Raw videos are **not** redistributed here — obtain them from the official sources and agree to their terms:

- **UCF-Crime**: <https://www.crcv.ucf.edu/projects/real-world/> (CRCV, University of Central Florida)
- **XD-Violence**: <https://roc-ng.github.io/XD-Violence/>

Train/val/test splits (`data/splits/`) and frame-level temporal annotations (`data/annotations/`) are tracked in this repo.

### Path convention

Configs hardcode the original machine's layout: feature caches under `E:/features/{ucf,xd}/` and snippet boundaries under `E:/snippets/{ucf,xd}/`. Either recreate that layout (Windows) or edit the `paths:` block of the configs you run — every path the code touches is declared there.

## Reproducing the results

### Tier 1 — from cached features (hours, GPU optional for eval)

All non-git artifacts live in one Zenodo record: **<https://doi.org/10.5281/zenodo.22513205>** — feature caches for both datasets (clean + corruption variants), snippet boundaries, the six headline checkpoints with config snapshots, and the CTR-GCN stream weights.

1. Download and extract `ucf_features.tar`, `xd_features.tar` → `E:/features/` (or remap, see above); `snippet_boundaries.tar` → `E:/snippets/`.
2. Evaluate the shipped headline checkpoints (each run dir contains `best_model.pth` + `config_snapshot.json`):
   ```bash
   python src/evaluate.py --run-dir results/ucf_gated_fusion_giant_s42/ --split test
   python src/evaluate.py --run-dir results/xd_gated_fusion_so400m_s42/ --split test
   ```
3. Or retrain the heads from scratch (deterministic per seed):
   ```bash
   python src/train.py --config configs/gated_fusion_giant.yaml --seed 42
   python src/train.py --config configs/gated_fusion_xd_so400m.yaml --seed 42
   ```
   Repeat for seeds 123 and 2024; `scripts/run_ablations.py --queue ...` orchestrates full grids.

### Tier 2 — from raw videos (days)

Re-extract everything with the three environments:

```bash
# vcc-skeleton: RTMPose keypoints per video
python scripts/extract_skeletons.py ...
# vcc-ctrgcn: CTR-GCN features from keypoints (weights: see below)
python scripts/extract_ctrgcn.py ...
# vcc-main: CLIP/SigLIP2 features per snippet
python scripts/extract_clip.py ...
# vcc-main: corrupted variants for the TTA study (UCF-Crime-C)
python scripts/batch_extract_corrupted.py ...
```

Each script documents its arguments in its module docstring. CTR-GCN NTU120 2D stream weights (`j/b/jm/bm.pth` → `data/weights/ctrgcn/`) are in the Zenodo record, originally from the [PYSKL model zoo](https://github.com/kennymckormick/pyskl) (Apache-2.0). CLIP/SigLIP2 weights download automatically via [open_clip](https://github.com/mlfoundations/open_clip).

### TTA experiments

`scripts/run_tta_grid.py` and `src/tta/` implement TENT/SAR (adapted from the [official SAR implementation](https://github.com/mr-eggplant/SAR), BN→LN transfer) plus the continual protocol and disc_reweight variant reported in the thesis.

## Building the thesis and paper

Windows + MiKTeX + Strawberry Perl:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1  -Clean
```

Public clones build the thesis with unsigned placeholder committee pages (the signed scans are private and gitignored).

## Citation

```bibtex
@mastersthesis{jeng2026violencecc,
  author  = {Jeng, Wei-Han},
  title   = {Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection: A Multi-Backbone Study},
  school  = {National Taiwan University of Science and Technology},
  year    = {2026}
}
```

For the feature caches / checkpoints, cite the Zenodo record: [10.5281/zenodo.22513205](https://doi.org/10.5281/zenodo.22513205).

## License

Code is MIT (see [LICENSE](LICENSE)). The Zenodo artifacts are CC-BY-4.0. UCF-Crime, XD-Violence, NTU RGB+D 120, and all pretrained backbone weights remain under their respective owners' terms.
