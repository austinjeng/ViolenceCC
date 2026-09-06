---
phase: quick-260906-nsj
status: complete
completed: 2026-09-06
---

# Quick 260906-nsj: Reproducibility wrap-up — SUMMARY

## Delivered

1. **README.md** (root, new) — two-tier reproduction guide (Tier 1: Zenodo caches + checkpoints → evaluate/retrain in hours; Tier 2: raw videos → full 3-env extraction), headline table pinned to PROVENANCE.md families 1–5/7, official dataset links (UCF-Crime CRCV, XD-Violence), E:/features + E:/snippets path-remap note, 3-env table linking envs/SETUP.md, thesis/paper build commands, bibtex (exact thesis title "Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection: A Multi-Backbone Study"), DOI badge.
2. **LICENSE** (new) — MIT, © 2026 Wei-Han Jeng. Third-party terms noted in README (datasets, NTU120, backbone weights; Zenodo artifacts CC-BY-4.0).
3. **Tag + release** — `v1.0-thesis` on post-purge history; GitHub release with headline numbers + DOI.
4. **Zenodo dataset record** — PUBLISHED (user-confirmed): **DOI 10.5281/zenodo.22513205**, concept DOI 10.5281/zenodo.22513204, https://zenodo.org/record/22513205. Files (all MD5-verified server-side vs local staging): ucf_features.tar 2.1GB (100 variant dirs incl. corruption caches), xd_features.tar 14.8GB, snippet_boundaries.tar 19MB (E:/snippets — loaders require these; gap caught during planning), checkpoints_headline.tar 22MB (ucf_gated_fusion_giant + xd_gated_fusion_so400m × s42/123/2024: best_model.pth + config_snapshot.json + eval_metrics.json), ctrgcn_ntu120_2d_weights.tar 25MB (j/b/jm/bm from PYSKL zoo). Upload: single background job, 5/5 first-attempt HTTP 201, ~55 min total.
5. **Code DOI (automatic)** — user's Zenodo GitHub integration archived the release as record 22513692 (10.5281/zenodo.22513692), auto-published.

## Notes

- Deposition metadata: dataset type, creator Jeng Wei-Han (NTUST), CC-BY-4.0, open, isSupplementTo → GitHub repo. Title initially drafted wrong; corrected to the real thesis title via PUT before publish.
- Staging tars remain at `E:\zenodo_staging\` (16.5GB duplicates of E:/features content) — user may delete.
- API token stored only in session scratchpad; user advised to revoke post-task.
- Raw videos deliberately NOT re-hosted (upstream distribution terms); README links official sources.

## Verification

- https://zenodo.org/record/22513205 live (state done, submitted true); DOI in README matches published DOI (pre-reserved, unchanged).
- Server MD5 == local MD5 for all 5 files.
- README claims spot-checked against repo: configs exist, evaluate.py `--run-dir/--split` contract, extract scripts document args in docstrings.
