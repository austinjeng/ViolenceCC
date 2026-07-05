---
phase: 13-full-thesis-manuscript
plan: 05
subsystem: thesis-chapters-1-3
tags: [wave-1, chapter-drafting, introduction, related-work, methodology, verbatim-equations]

# Dependency graph
requires:
  - phase: 13-full-thesis-manuscript
    plan: 01
    provides: "thesis skeleton (main.tex include chain, preamble, chapter placeholders with ch:NN labels)"
  - phase: 13-full-thesis-manuscript
    plan: 02
    provides: "references.bib superset (42 keys) used by ch02's 41 distinct cites"
  - phase: 13-full-thesis-manuscript
    plan: 04
    provides: "verified thesis/figures/ inventory incl. fig_architecture.tex consumed by ch03"
provides:
  - "thesis/chapters/ch01_introduction.tex — full introduction: motivation, problem statement, 4 gaps, RQ1/RQ2/RQ3, 3 expanded contributions, honest-positioning section, 9-chapter + 6-appendix roadmap (7pp)"
  - "thesis/chapters/ch02_related_work.tex — four survey sections (WSVAD lineage ~23 methods, skeleton, VLM backbones, TTA) + design-space taxonomy table tab:rw-taxonomy; 41 distinct cite keys (8pp)"
  - "thesis/chapters/ch03_methodology.tex — expanded methodology with all 8 paper equations byte-verbatim, L136 exclusion sentence + L147 checkpoint names verbatim, TENT/SAR LN protocol, NORM/CORAL subsection, full disc_reweight derivation; labels eq:loss, sec:disc, fig:architecture kept (12pp)"
affects: [13-08 integration gate (RE-VERIFY count unaffected — 0 in ch01-03), 13-13 adversarial number audit, 13-VALIDATION]

# Tech tracking
tech-stack:
  added: []
  patterns: ["byte-verbatim equation splicing: write chapter with @@markers@@, substitute exact paper/main.tex lines via Python, then diff all equation environments programmatically before commit"]

key-files:
  created: []
  modified:
    - thesis/chapters/ch01_introduction.tex
    - thesis/chapters/ch02_related_work.tex
    - thesis/chapters/ch03_methodology.tex

key-decisions:
  - "Ch2 cites external methods WITHOUT numbers except the three paper-S2-verified values (Sultani 75.41; RTFM 84.30/77.81; VadCLIP 88.02/84.51); all other quantitative positioning forward-referenced to Ch7's verified tables — zero new RE-VERIFY markers"
  - "sec:tta / sec:impl cross-references redirected to Chapter refs (ch:06 / ch:04) because those labels live in sibling writers' chapters; labels DEFINED in ch03 keep paper names (eq:loss, sec:disc, fig:architecture)"
  - "Added tab:rw-taxonomy design-space table (mechanism axes only, no performance numbers) to give Ch2 a synthesis artifact without touching the number guardrails"
  - "NORM/CORAL feature-statistic restoration promoted to its own methods subsection (sec:meth-tta-restore) so Ch6's evaluation of it has a proper methods anchor"

requirements-completed: [SC2 (spec S4 Ch1-Ch3 content complete, placeholder-free), SC5 (honesty framings intact: no SOTA claim, 88-91 field ceiling, points-not-percent, transductive disclosure, small-but-consistent complementarity)]

# Metrics
duration: ~45min
completed: 2026-07-05
---

# Phase 13 Plan 05: Chapters 1-3 (Introduction, Related Work, Methodology) Summary

**Three placeholder-free chapters drafted under the binding number guardrails: an 8-section introduction with explicit RQ1/RQ2/RQ3 and honest positioning, a four-lineage related-work survey citing 41 of the 42 bib keys with zero external numbers beyond paper-verified values, and a methodology chapter whose 8 equations byte-match paper/main.tex exactly (verified by automated diff) with the disc_reweight derivation fully unpacked from the .knowledge narrative.**

## Performance

- **Duration:** ~45 min (2026-07-05T04:27Z → ~05:00Z UTC; includes one base-hash recovery)
- **Tasks:** 3/3 complete, 4 commits
- **Page counts (from main.toc):** Ch1 pp.1-7 (7pp) · Ch2 pp.8-15 (8pp) · Ch3 pp.16-27 (12pp) — **27pp combined** vs the plan's ~30-35 target (ch2/ch3 were expanded once toward budget; further padding traded away for prose quality, within CONTEXT's page-budget discretion)

## What was built

### Ch1 — Introduction (259 lines)
- Motivation (surveillance scale → annotation cost → weak supervision → VLM era → motion gap → robustness), formal problem statement with the three interlocking problems, four research gaps exactly per spec §4, RQ1/RQ2/RQ3 as a description list, the paper's three contributions (L75-83) each expanded with canonical anchors only (82.5±0.4 / 78.7±0.9; mean +0.6 points, 6/8 strictly positive + 2 ties; TENT/SAR <0.1 points; disc_reweight mean +1.2 points, up to +13.2 points in the single most-degraded condition)
- Dedicated "Scope and Honest Positioning" section: no peak-score claim, ~88-91% field-ceiling disclosure, corrupted-AUC-only TTA gains, transductive assumption, reproducibility protocol
- Roadmap paragraph naming all 9 chapters and appendices A-F via `\ref{ch:NN}` / `\ref{app:x}`

### Ch2 — Related Work (334 lines)
- §2.1 WSVAD in five subsections: MIL foundations (Sultani, XD/HL-Net) → feature-magnitude/memory (RTFM, UR-DMU, MGFN, Light-WVAD) → CLIP era (CLIP-TSA, VadCLIP, TPWNG, PEL4VAD, STPrompt, TEVAD, AnomalyCLIP) → MLLM/training-free (LAVAD, EventVAD, Holmes-VAD/VAU) → recent (PI-VAD, DSANet, GS-MoE, PiercingEye, HyperVD, Ghadiya et al.) + design-space synthesis with `tab:rw-taxonomy`
- §2.2 skeleton lineage (ST-GCN → CTR-GCN, PYSKL, RTMPose, Doshi & Yilmaz) + corruption-asymmetry paragraph that sets up Ch6's routing
- §2.3 VLM backbones (ViT, CLIP, SigLIP, SigLIP2) + frozen-feature practice and the no-text-tower design choice
- §2.4 TTA (ImageNet-C, NORM, CORAL, TENT, SAR+SAM) + protocol/rank-metric paragraph + the BN-vs-LN structural argument
- Light-WVAD cited with correct attribution and NO XD number (fabricated 77.3 absent; grep = 0)

### Ch3 — Methodology (427 lines)
- §3.1 overview with the architecture figure (paper caption lifted + one expansion sentence) and a notation paragraph; §3.2 RTMPose (top-2 persons, PreNormalize2D, (T_f, M, V, C) tensors); §3.3 CTR-GCN (4-stream j/b/jm/bm 1.0/1.0/0.5/0.5, GAP, 256-d) with the **whole L136 paragraph verbatim** (incl. the 172-video/one-video exclusion sentence and FPS-asymmetry disclosure); §3.4 VLM features (itemize + **L147 checkpoint-names sentence verbatim**, ~1 FPS, mean+max to 2d); §3.5 late + gated fusion with per-dimension gate, (1+g)ŝ+(2−g)v̂ residual reading, three named LayerNorms and the MIL batch-composition rationale; §3.6 MIL ranking (top-k, λ1=8e-3, λ2 → Ch4, shuffled-val rationale); §3.7 TTA methods
- §3.7.1 TENT/SAR on LN: 1{,}536 params = 3 LN modules / 6 tensors, binary entropy, dropout-eval determinism, episodic inertness (98.4% of UCF test videos ≤32 snippets) → continual protocol
- §3.7.2 NORM/CORAL restoration defined (new subsection, sec:meth-tta-restore)
- §3.7.3 disc_reweight (`\label{sec:disc}`): paper L193 lead-in + Eq. w_vl + **L197 1,663-char paragraph lifted whole**, then unpacked per the .knowledge narrative (dispersion-vs-distribution distinction, factor-2 anchor untuned, {0,1} saturation, w after LN_v in both terms, w=1 ⇒ bit-identical source model, transductive pooling), 4-step procedure summary, code pointers to src/tta/disc_reweight.py / evaluate_tta.py

## Verification evidence

- **Equations:** automated extraction diff — 7/7 `\begin{equation}` environments BYTE-MATCH paper/main.tex; L197 inline-equation paragraph verbatim (whole-line substring match). Verification script re-run after every subsequent edit.
- **Builds:** `build_thesis.ps1` (incremental) exit 0 with clean log scan after each task and after each expansion edit; zero undefined references/citations in final main.log.
- **Guardrail greps (all three chapters):** `PLACEHOLDER-W0` = 0; `83.6|71.8|77.3` = 0; `RE-VERIFY` = 0 (ch02); "state-of-the-art" phrasing = 0 in ch01; `82.5` ≥1 in ch01; RQ1/RQ2/RQ3 present (3 mentions each).
- **Citations:** 41 distinct keys in ch02 (≥18 required); yan2018stgcn + sun2016coral + schneider2020norm all cited.
- **Labels:** ch:01/02/03 kept; eq:loss ×1; sec:disc ×1 (moved onto disc_reweight subsection per placeholder instruction); fig:architecture referenced from prose; no `\ref{sec:tta}` / `\ref{sec:impl}` (undefined in this worktree).
- **Layout:** taxonomy-table overfull fixed (footnotesize + tabcolsep + resizebox); remaining Overfull boxes are ≤2.3pt in own prose or inside sibling placeholder files (untouched).

## Task Commits

1. **Task 1: ch01 introduction** — `c44840f` (docs)
2. **Task 2: ch02 related work** — `365ff23` (docs)
3. **Task 3: ch03 methodology** — `6fb3dfc` (docs)
4. **Follow-up: ch02 survey-depth expansion toward page budget** — `4ffca43` (docs)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Orchestrator base-commit hash was garbled and worktree was stale**
- **Found during:** worktree branch check (first action)
- **Issue:** the prompt's full base hash `4187725bb1af...abcd` does not exist; the abbreviated prefix `4187725` resolves uniquely to `41877258d278e50daec4c34be8d7520b45668562` (main's tip, "13-04 merged"). The worktree HEAD was additionally stale at `cb8a26a` (June 10 era).
- **Fix:** verified branch is `worktree-agent-*` (protected-ref assertions passed), then `git reset --hard 41877258d...` to the unambiguous intended base.
- **Files modified:** none (ref move only)
- **Commit:** n/a

**2. [Rule 1 - Bug] Shell heredoc stripped a backslash level during equation splicing, corrupting the figure caption**
- **Found during:** Task 3 (post-substitution inspection)
- **Issue:** the caption-expansion string's `\ref` reached Python as a literal CR + `ef{...}`, leaving `Section~<CR>ef{sec:meth-ctrgcn}` in the caption; a same-script `eq:loss` cross-reference in my expansion prose also misattributed the fusion equation.
- **Fix:** repair script written via the Write tool (verbatim content, no shell escaping), replacing both; re-verified 0 CR chars and full equation byte-match; rebuild clean.
- **Files modified:** thesis/chapters/ch03_methodology.tex
- **Commit:** `6fb3dfc` (fix landed before the task commit)

### Planned-adaptation notes (not rule deviations)

- **Cross-references into sibling chapters:** paper's `Section~\ref{sec:tta}` / `Section~\ref{sec:impl}` become `Chapter~\ref{ch:06}` / `Chapter~\ref{ch:04}` (+ `Section~\ref{sec:meth-tta}` where the TTA implication is now local). Those labels will be defined by the ch04/ch06 writers; referencing them from this worktree would fail the per-task clean-log gate. Labels defined in ch03 keep the paper's names, so downstream porting is unaffected.
- **Page budget:** first drafts landed at 24pp combined; ch2 and ch3 were expanded once (taxonomy table + 3 survey paragraphs; notation + NORM/CORAL subsection + procedure summary) to 27pp. Stopped there deliberately — remaining gap to "~30-35" is within CONTEXT's stated page-budget discretion and preferable to padding.

## Known Stubs

None introduced by this plan. The remaining PLACEHOLDER-W0 bodies (ch04-ch09, appendices, `\nocite{*}` smoke test) belong to sibling Wave-1/2 writers and Wave-3 integration by design.

## Self-Check: PASSED

- thesis/chapters/ch01_introduction.tex (259 lines), ch02_related_work.tex (334), ch03_methodology.tex (427) exist with PLACEHOLDER-W0 absent — verified
- Commits `c44840f`, `365ff23`, `6fb3dfc`, `4ffca43` present in git log — verified
- Equation byte-match verification: RESULT PASS (7 envs + L197) — verified post-final-edit
- Final build: exit 0, log scan clean — verified
