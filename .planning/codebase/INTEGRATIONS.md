# External Integrations

**Analysis Date:** 2026-06-09

This is a self-contained research codebase. There are no live API calls,
auth providers, or hosted services in the runtime path. "Integrations" here
means **local datasets, on-disk feature caches, pretrained model hubs, the
LaTeX paper toolchain, and optional dev tooling (wandb, Overleaf MCP)**. The
dominant integration surface is the `E:` data drive.

## Data Storage

**Primary store: the `E:` drive** (local, ~1.5 TB; not committed, not
junctioned reliably — configs use direct `E:/` paths). Layout from extraction
scripts and configs:

- Raw datasets:
  - UCF-Crime: `E:/UCF_crime_dataset/Train/` and `E:/UCF_crime_dataset/test/`
    — per-category PNG frames `{video_id}_x264_{N}.png`
    (`scripts/extract_clip.py:85-86`, `:20`)
  - XD-Violence: `E:/XD_Violence/train/{video_id}.mp4` and
    `E:/XD_Violence/test/videos/{video_id}.mp4`
    (`scripts/extract_clip.py:88-90`, `:21`)
  - I3D RGB features (RTFM baseline): `E:/i3d-features/i3d-features`
    (`configs/rtfm_i3d.yaml:10`)
- Intermediate artifacts:
  - Skeleton pickles: `E:/skeletons/{dataset}/{video_id}.pkl` — PYSKL format
    (`scripts/extract_skeletons.py:55`, `:11`)
  - Snippet boundaries: `E:/snippets/{dataset}/{video_id}_boundaries.json` —
    the alignment contract shared by CLIP + CTR-GCN extractors
    (`scripts/extract_skeletons.py:13`; consumed at
    `scripts/extract_clip.py:19`, `scripts/extract_ctrgcn.py:13`)
- Feature caches (the training inputs): `E:/features/{dataset}/{subdir}/{video_id}.npy`
  float32 `[N_snippets, D]`:
  - `skeleton/` — CTR-GCN 4-stream weighted features, D=256
    (`scripts/extract_ctrgcn.py:16`)
  - `clip/` (D=1024), `clip_mean/` (512), `siglip2/` (1536),
    `siglip2_mean/` (768), `siglip2_so400m/` (2304), `siglip2_giant/` (3072)
    — vision backbones (`scripts/extract_clip.py:24-29`, registry `:119-148`)

**File format:** `.npy` (numpy) for feature caches; `.pkl` for skeletons;
`.json` for snippet boundaries. h5py/HDF5 is available but caches are `.npy`.
Writes are atomic (write-temp-then-rename) to avoid corrupted `.npy`.

**Pretrained model hubs (download-time only):**
- HuggingFace / open_clip pretrained weights pulled by
  `open_clip.create_model_and_transforms(..., pretrained='openai' | 'webli')`
  (`scripts/extract_clip.py:171`). `openai` = CLIP ViT-B/16; `webli` = SigLIP2
  family. Cached in the open_clip / HF cache dir.
- CTR-GCN NTU120 HRNet 2D weights (`j/b/jm/bm.pth`, ~6.1 MB each) downloaded
  manually from `download.openmmlab.com/mmaction/pyskl/ckpt/...` into
  `D:/ViolenceCC/data/weights/ctrgcn/` (`envs/SETUP.md:106-117`). Git-ignored.
- RTMPose-m ONNX weights auto-fetched by `rtmlib.Body(mode="balanced")` on
  first run (`scripts/extract_skeletons.py:466-471`).

**Caching:** No runtime cache service. The `E:/features` `.npy` files ARE the
cache — extracted once, reused across all training runs.

## APIs & External Services

**At runtime:** None. No network calls during training, extraction (after
weight download), or evaluation.

**Dev/tooling only:**
- **wandb** — experiment-tracking SaaS. Integrated via
  `src/utils/wandb_logger.py` (thin wrapper around `wandb.init/log/finish`).
  **Disabled in every config** (`mode: disabled`, e.g.
  `configs/gated_fusion.yaml:40`, `configs/rtfm_i3d.yaml:41`) because no
  `WANDB_API_KEY` / `~/.netrc` is configured. The wrapper degrades to a no-op
  when disabled and falls back to `mode='offline'` on auth/network errors
  (D-40, `src/utils/wandb_logger.py:47-60`). Auth would read
  `WANDB_API_KEY` and optional `VIOLENCECC_WANDB_ENTITY`.
  **CSV logging (`src/utils/csv_logger.py`) is the thesis source of truth.**
- **Overleaf (via MCP)** — `.mcp.json` registers the `overleaf` MCP server
  `@mjyoo2/overleaf-mcp@1.0.0` (run through `npx`). Auth via env vars
  `OVERLEAF_PROJECT_ID` and `OVERLEAF_GIT_TOKEN`. This is a Claude-Code-side
  tool for syncing the paper to Overleaf; not part of the training pipeline.
  The local `scripts/build_paper.ps1` "stands in for the Overleaf round-trip."

## Authentication & Identity

- Application auth: None (no users, no auth provider).
- wandb: `WANDB_API_KEY` (unset → disabled).
- Overleaf MCP: `OVERLEAF_GIT_TOKEN` + `OVERLEAF_PROJECT_ID` (env-var
  interpolation in `.mcp.json`).

## Monitoring & Observability

**Error tracking:** None (no Sentry/etc.).

**Logs:** Python `logging` to console across extraction scripts; decoder /
RTMPose-inference failures logged at WARNING with per-video zero-snippet counts
(CLAUDE.md Feature Extraction conventions). Run logs: `extraction_progress.log`,
`tta_grid_progress.log`, `runner-errors.log` at repo root (git-ignored via
`*.log`). Training metrics → CSV under `results/` (git-ignored).

## CI/CD & Deployment

**Hosting:** None — local research.

**CI pipeline:** None detected (no `.github/workflows`, no CI config). pytest is
run locally (`pyproject.toml` markers `e2e`, `requires_features`).

**Version control:** GitHub remote `origin` →
`https://github.com/austinjeng/ViolenceCC.git`.

## Paper / LaTeX Build Integration

The CGW '26 paper (`paper/main.tex`, ACM `acmart` sigconf) compiles locally:
- Driver: `scripts/build_paper.ps1` — full-path-probes for `latexmk.exe`
  (MiKTeX, `%LOCALAPPDATA%\Programs\MiKTeX\...\bin\x64`) and `perl.exe`
  (Strawberry Perl), prepends them to PATH, runs `latexmk -pdf` in `paper/`,
  opens the PDF. `-Clean` runs `latexmk -C` first.
- Engine config: `paper/.latexmkrc` (pdflatex, bibtex, nonstopmode, synctex,
  MiKTeX `--enable-installer` to auto-fetch missing CTAN packages).
- Bibliography: classic BibTeX with `paper/references.bib` +
  `paper/ACM-Reference-Format.bst`.
- Figures: `paper/figures/*.pdf` (generated by `scripts/generate_pub_figures.py`
  and `scripts/generate_phase*_charts.py`), `paper/figures/fig_architecture.png`.
- Tables: `paper/tables_generated.tex` is produced by
  `scripts/generate_latex_tables.py` but is NOT `\input` by `main.tex` (tables
  are inlined — see CLAUDE.md Paper/LaTeX Build conventions).
- **Convention:** after editing any paper LaTeX source, rebuild with
  `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean`.
  Build artifacts (`main.pdf`, `*.aux/.bbl/.blg/.fdb_latexmk/.synctex.gz/...`)
  are git-ignored (`.gitignore`) — never commit them.

## Environment Configuration

**Required env vars (all optional / dev-only):**
- `OVERLEAF_PROJECT_ID`, `OVERLEAF_GIT_TOKEN` — Overleaf MCP (`.mcp.json`)
- `WANDB_API_KEY`, `VIOLENCECC_WANDB_ENTITY`, `WANDB_MODE` — wandb (currently
  unset; configs force `disabled`)
- `PATH` augmentation — cuDNN 9 dir for onnxruntime
  (`scripts/extract_skeletons.py:62`); MiKTeX + Perl bins
  (`scripts/build_paper.ps1`)

**Hardcoded paths (not env-driven):**
- Project root `D:/ViolenceCC` (e.g. `scripts/extract_clip.py:82`)
- PYSKL configs `D:/libs/pyskl/configs/...` (`scripts/extract_ctrgcn.py:61`)
- All `E:/...` data/feature locations (in `configs/*.yaml` + script constants)

**Secrets location:** No `.env`, no committed credentials. `.gitignore` excludes
`.gsd/firecrawl_api_key` and `wandb/`. Secrets are environment variables only.

## Webhooks & Callbacks

**Incoming:** None.
**Outgoing:** None.

---

*Integration audit: 2026-06-09*
