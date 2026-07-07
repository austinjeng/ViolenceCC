---
quick_id: 260707-n9l
description: Build CGW 2026 talk deck + Traditional Chinese transcript (PPTX deliverable)
date: 2026-07-07
status: complete
---

# Summary — CGW '26 Talk Deck (Paper #32)

## Delivered

- `presentation/32_Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection：A Multi-Backbone Study.pptx`
  — 18 slides (13 main ≈ 10:00 + divider + 4 Q&A backups), 16:9, ~745 KB, fullwidth-colon
  filename (Windows-safe, matches the conference naming format). Every slide carries the
  spoken 繁體中文 script in its speaker notes.
- `presentation/transcript_zh-TW.md` — full spoken transcript with per-slide timing cues
  (1,695 CJK chars + English terms ≈ 9.5–10.5 min at conference pace), Q&A routing map to
  backup slides, and prepared answers for 4 likely questions.
- `presentation/slides.md` — deck source of truth (content + notes + timing).
- `scripts/build_talk_pptx.py` — one-command rebuild (vcc-main): converts paper PDF figures
  via pymupdf, renders equations via matplotlib mathtext, regenerates the qualitative
  temporal figure from repo npz data, rebuilds the architecture diagram as native PPTX
  shapes, embeds notes. `python-pptx` + `pymupdf` installed into vcc-main.
- `.gitignore` — presentation binaries (pptx, assets/) excluded per artifact convention.

## Verification (2 workflows + 1 agent, 6 auditors total)

- Numeric audit: **134 distinct numeric claims** on slides/notes verified against
  paper/main.tex + sota_comparison_full.tex — **0 wrong result numbers**; 1 MEDIUM fixed
  (LAVAD hardware overgeneralization on slide 10).
- Claims-discipline audit: 7/8 sanctioned framings exactly followed; 1 MEDIUM fixed
  (conclusions slide now scopes the entropy-TTA null to "confined to LN affine updates …
  our detector"); 3 LOW zh fluency fixes applied. No Simplified characters; no retired
  single-seed numbers; metric hygiene clean.
- Data audit: Fighting047 slide-9 claims independently recomputed and confirmed
  (gap +0.4827 / +0.1459 / −0.0101).
- Visual QA: all 18 slides exported via PowerPoint COM and inspected; MIL-equation clipping
  and legend occlusion found and fixed.

## Key discovery — paper Figure 2 erratum candidate (NOT fixed here, out of scope)

`paper/figures/fig_temporal_scores.pdf` (main.tex Figure 2) shows **RoadAccidents127**,
whose gated-fusion scores are ANTI-aligned with its ground truth: in-GT-minus-normal gap
= **−0.74**, the **worst of all 128 annotated anomalous test videos** (independently
recomputed twice). The caption claims "sharper score peaks aligned with the anomalous
event" — the video-selection heuristic in `generate_pub_figures.py` appears to pick a
failure case. The talk deliberately substitutes **Fighting047** (gap +0.48 vs CLIP +0.15,
skeleton −0.01), regenerated from the same seed-42 npz data. **Recommend a paper/thesis
erratum pass on Figure 2 before camera-ready.**

## Open items for the presenter

1. Slide 1 / transcript: speaker's Chinese name is a placeholder 〔請自行帶入中文姓名〕
   (characters unknown to the repo); advisor rendered as 楊傳凱 — please confirm.
2. Upload deadline 2026-07-07 23:59 UTC+8; file name uses fullwidth ： (U+FF1A).

## Deviation note

Planned + executed in-session (no gsd-planner/gsd-executor spawn): content depended on
session-held context (user-approved outline, 3-reader research, sanctioned-framing
constraints). GSD artifact contract preserved (PLAN/SUMMARY/STATE row/atomic commits).
