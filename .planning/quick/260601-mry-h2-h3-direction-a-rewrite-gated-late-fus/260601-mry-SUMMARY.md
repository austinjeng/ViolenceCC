---
phase: quick-260601-mry
plan: 01
subsystem: thesis-manuscript
tags: [paper, latex, fusion, editorial, H2, H3]
requires:
  - src/models/gated_fusion.py (read-only ground truth)
  - src/models/late_fusion.py (read-only ground truth)
provides:
  - Fusion equations (Eq. 1, 3, 4) and dependent Discussion arguments consistent with the implemented architecture
affects:
  - paper/main.tex
tech-stack:
  added: []
  patterns: [editorial-only, verbatim-OLD-NEW-replacement, structural-grep-verification]
key-files:
  created: []
  modified:
    - paper/main.tex
decisions:
  - "Direction A (fix paper to match code), not Direction B (re-run code) — reported numbers unaffected"
  - "Late fusion = fixed 0.5/0.5 score averaging of two independent heads; NOT concat+projection"
  - "Gated fusion = element-wise (256-d) gated-residual block; gate modulates RELATIVE contribution, does not suppress either modality"
metrics:
  tasks_completed: 2
  files_modified: 1
  edits_applied: 9
  completed: 2026-06-01
---

# Quick 260601-mry: H2/H3 Direction A — Align Gated/Late Fusion Equations with Code Summary

Rewrote the gated-fusion (Eq. 3, 4) and late-fusion (Eq. 1) equations in `paper/main.tex` plus their dependent captions and Discussion arguments so the manuscript matches the implemented architecture: late fusion is fixed-weight score averaging (not concat+projection), and the gated mechanism is an element-wise 256-d gated-residual block that reweights relative contribution (not a scalar gate that suppresses a modality). Purely editorial — every reported number, table, and figure is byte-for-byte unchanged.

## What Changed

Nine verbatim OLD→NEW edits, all in `paper/main.tex`, all within the spans of EDIT 1–7 plus two additional same-class H3 mislabel fixes. Committed as `ced266f`.

| # | Edit | Location | Change |
|---|------|----------|--------|
| 1 | EDIT 5 | Eq. (1), §3.4 (line ~164) | `concatenate + ReLU projection to 512-d` → `a_late = ½ h_s(s) + ½ h_v(v)` (fixed 0.5/0.5 score average of two independent heads) |
| 2 | EDIT 1 | Eq. (3), §3.4 (line ~174) | gating **scalar** `g ∈ [0,1]` → gating **vector** `g ∈ [0,1]^256` computed per dimension; `b_g` → `\mathbf{b}_g` |
| 3 | EDIT 2 | Eq. (4) + trailing text, §3.4 (line ~178) | Added residual term `+ ŝ + v̂`, element-wise `⊙`, "dropout applied after LN_f", and the effective per-dim weighting `(1+g)⊙ŝ + (2−g)⊙v̂` note; clarified the gate modulates *relative* contribution rather than suppressing either modality |
| 4 | EDIT 7 | §4.3 parenthetical (line ~263) | `late fusion (concatenation with projection)` → `late fusion (equal-weight score averaging)` |
| 5 | EDIT 3 | §4.3 final sentence (line ~263) | `suppressing the weaker modality when its signal is noisy` → `reducing the weaker modality's relative contribution when its signal is noisy` |
| 6 | EDIT 4 | Fig. gating-distribution caption (line ~339) | `A gate value of $g > 0.5$` → `A mean gate value $\bar{g} > 0.5$` |
| 7 | EDIT 6 | §5 late-fusion-failure paragraph (line ~349) | Rewrote sentences 2–3: dropped "simple concatenation forces … disentangle" and "suppress the skeleton stream"; reframed as fixed-equal-weight contributing half of every score, with the gate doing input-dependent per-dimension reweighting over a residual baseline. **First sentence preserved verbatim.** |
| 8 | Additional (same as EDIT 7 class) | Fig. 1 architecture caption (line 125) | `late fusion (concatenation with linear projection)` → `late fusion (equal-weight score averaging)` |
| 9 | Additional (same as EDIT 3/7 class) | §4.3 prose (line 272) | `naive concatenation allows the weaker skeleton signal to interfere … when the projection layer lacks the capacity` → `the fixed equal weighting lets the weaker skeleton signal drag down every fused score, with no input-dependent mechanism to reduce its weight relative to the stronger visual stream` |

Edits 8–9 were the same H3 mislabel as EDIT 5/7 (late fusion described as "concatenation") in two locations the original 7-edit list missed. They are in scope for the H3 requirement (`H3-direction-a-late-fusion-eq`) — the original list was simply incomplete. The post-edit sentence at line 272 ("The gated mechanism resolves this by learning to modulate each modality's contribution.") was preserved intact and reads coherently after the new sentence.

## Verify Gate: PASS

Full structural verification (no TeX toolchain on PATH — grep/structural only) ran and PASSED:

- **Required new fragments present (7):** `\mathbf{g} \odot \hat{\mathbf{s}}`, `+ \hat{\mathbf{s}} + \hat{\mathbf{v}}`, `(1 + \mathbf{g}) \odot \hat{\mathbf{s}}`, `a_{\text{late}} = \tfrac{1}{2}\, h_s(\mathbf{s})`, `simple late fusion (equal-weight score averaging)`, the Fig. 1 caption phrasing, and the new §4.3 prose sentence.
- **Old mechanism strings absent (8):** `suppressing the weaker modality`, `suppress the skeleton stream`, `simple concatenation forces`, both `late fusion (concatenation with projection)` and `(concatenation with linear projection)`, `\mathbf{f}_{\text{late}} = \text{ReLU}`, `(1 - g) \cdot \hat{\mathbf{v}}`, `naive concatenation allows the weaker skeleton signal`.
- **All 9 protected numbers intact:** 71.8%, 41.3%, 65.5%, 71.0%, 81.4%, 81.1%, 82.5%, 82.4%, 78.6%.
- **Braces balanced:** 315 open / 315 close (escaped `\{`/`\}` excluded), running balance never negative, final 0.
- **Citations/refs intact:** 44 `\cite`, 9 `\ref`, 9 `\label`; no empty `\cite{}`/`\ref{}`; `ba2016layernorm` and `sec:tta` reference targets both present.
- **EDIT 6 first sentence preserved verbatim:** "The consistent underperformance of late fusion relative to both gated fusion and, in some cases, visual-only baselines warrants attention."
- **Post-line-272 sentence intact and coherent:** "The gated mechanism resolves this by learning to modulate each modality's contribution."

### "concatenat" survivors (both legitimate, neither describes late fusion)

| Line | Context | Legitimate because |
|------|---------|--------------------|
| ~158 | "frame-level features are aggregated via **concatenated** mean and max pooling" | Temporal feature pooling, unrelated to fusion mechanism |
| ~174 | "computed per dimension from the **concatenated** projected features" | §3.4 gate input `[ŝ ‖ v̂]` — Eq. (3)'s gate genuinely takes the concatenation of the two projected vectors before the gate linear layer |

No remaining "concatenat" string sits in a clause describing the late-fusion baseline. H3 CONCATENAT GATE: PASS.

## Deviations from Plan

The plan specified 7 edits (EDIT 1–7). Two additional edits (#8, #9 above) were applied with explicit user approval (Option A) after the original 7-edit list was found incomplete — both are the same H3 mislabel (late fusion described as "concatenation") in the Fig. 1 caption (line 125) and §4.3 prose (line 272). These are in scope for the H3 requirement, not a scope expansion. Wording was user-supplied and approved before application.

No Rule 1–3 auto-fixes were required. No code files touched (`src/models/gated_fusion.py` and `src/models/late_fusion.py` remained read-only ground truth).

## Commit

- `ced266f` — `docs(paper): align gated/late fusion equations + discussion with implemented architecture (H2/H3)` — `paper/main.tex` only (13 insertions, 13 deletions).

Per user instruction, only `paper/main.tex` was committed. SUMMARY/STATE/PLAN were NOT committed. The pre-existing unstaged modification to `11-01-SUMMARY.md` and untracked files were left untouched.

## Self-Check: PASSED

- `paper/main.tex` modified and committed: FOUND (commit `ced266f`, `git show --stat` shows 1 file changed).
- Commit `ced266f` exists in `git log`: FOUND.
- Verify gate output "VERIFY GATE: PASS": confirmed (temp verification scripts removed post-run, not committed).
