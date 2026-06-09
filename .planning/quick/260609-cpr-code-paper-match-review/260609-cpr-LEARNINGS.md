---
phase: quick-260609-cpr
phase_name: "Code↔Paper Match Review"
project: "ViolenceCC"
generated: "2026-06-09"
counts:
  decisions: 5
  lessons: 5
  patterns: 4
  surprises: 4
missing_artifacts:
  - "260609-cpr-PLAN.md (conversational task — no /gsd:quick PLAN was authored)"
  - "VERIFICATION.md"
  - "UAT.md"
note: "Quick task, not a numbered phase. Primary artifacts: 260609-cpr-SUMMARY.md, .planning/CODE-PAPER-REVIEW-2026-06-07.md (resolution table), .planning/STATE.md (narrative + Key Decisions)."
---

# Phase quick-260609-cpr Learnings: Code↔Paper Match Review

## Decisions

### Adversarially pre-check every exact-number paper/LaTeX edit before applying
Each MEDIUM/LOW edit was routed through a skeptic workflow (verify the fact in code + validate the exact old→new text + check build-safety) *before* touching the file.

**Rationale:** The pre-checks caught, pre-edit: 2 dangling `\ref{tab:tta}`, a stale `81.1→81.2 / 2.5→2.6 pp` number a prior edit had introduced, a wrong "21.6 FPS is unbacked" rationale (it is a real measurement), and a `T`-symbol collision — none shipped.
**Source:** 260609-cpr-SUMMARY.md (decisions), CODE-PAPER-REVIEW-2026-06-07.md

### Run matched-seed baselines rather than reposition a headline on mismatched seeds
For M7, ran visual-only at seeds {123,2024} (queue `m7_visual_seeds`, 16 runs) so gated-vs-visual has 3 seeds on *both* sides, instead of comparing 3-seed-gated to 1-seed-visual.

**Rationale:** The unmatched comparison was itself the bug M7 flagged; reusing it to "fix" M7 would be incoherent. Matched seeds overturned the apparent regression.
**Source:** 260609-cpr-SUMMARY.md

### Drop the Table-3 TENT/SAR columns rather than re-run or footnote (M5)
The TENT/SAR cells printed the 3-seed disc Source-Only, not the continual baseline those methods ran against (SO400M 58.9 shown vs ~60.6 actual).

**Rationale:** The TTA figure already omits TENT/SAR, so dropping the columns makes table+figure consistent; the entropy-null result lives in §4.5 prose. Printing the raw continual values would have implied a fake +1.8 "improvement."
**Source:** 260609-cpr-SUMMARY.md, CODE-PAPER-REVIEW-2026-06-07.md (M5)

### Keep 21.6 FPS; label the 33.3 FPS benchmark as synthetic (M2)
Kept the paper's 21.6 FPS (a real 100-frame `02-UAT.md` profiling result, the 1-person rate) and annotated `benchmark_backbones.py` that its 33.3 FPS is people-free-frame latency.

**Rationale:** 33.3 comes from `np.random` frames → ~0 YOLOX detections → near-zero pose work, so it overstates throughput; 21.6 is the honest extraction rate.
**Source:** 260609-cpr-SUMMARY.md, CODE-PAPER-REVIEW-2026-06-07.md (M2)

### Leave Table-2 Late-Fusion Best Δ at +1.5 (L6)
**Rationale:** Skeptic-verified raw-correct (0.01533 → +1.5); the table uses full-precision rounding throughout, so changing it to the display-subtracted +1.6 would make it the *only* inconsistent cell.
**Source:** 260609-cpr-SUMMARY.md

---

## Lessons

### Single-seed comparisons produced two false findings on seed-unstable XD metrics
The apparent "SigLIP2-Base/XD fusion regression" (−2.3) and "SO400M leads XD visual-only (77.2 > Giant)" were both seed-42 artifacts; with 3 seeds the regression is +0.05 (p=0.97) and SO400M (76.6) ≈ Giant (76.8).

**Context:** XD visual-only AP std is ±1.5–2.2 vs UCF ±0.1–0.5. A 3-seed mean compared to a lucky 1-seed point manufactures effects.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md, STATE.md (Key Decisions)

### The complementarity claim was overstated; the honest result is small + consistent
Gated ≥ visual-only in 8/8 backbone×dataset configs (mean +0.6 pp, sign test p≈0.008) but with no per-cell significance at n=3 — "small, consistent, never-degrading," not "large."

**Context:** The paper had cherry-picked its two weakest backbones (CLIP/Giant UCF) as examples; the genuine gains are on XD (CLIP +1.9, SO400M +2.1).
**Source:** CODE-PAPER-REVIEW-2026-06-07.md (M7)

### Edits cascade into prose numbers — a table change can strand a sentence elsewhere
Updating the Table-1 Visual-Only row to 3-seed (81.1→81.2) silently stranded a §4.3 sentence still citing "81.1% … 2.5 pp"; only the consistency-sweep skeptic caught it.

**Context:** After any table/number edit, sweep prose for downstream references to the old value.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md (consistency sweep)

### "No tuned hyperparameter" needed the gate's functional form disclosed to be credible
The skeleton-reliability gate had an undisclosed 2× ramp constant; disclosing the form (and that it saturates to {0,1} in practice) strengthened the tuning-free claim rather than weakening it.

**Context:** Honest disclosure of a constant that turns out to be immaterial is more convincing than omission.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md (M6)

### Provenance gaps hide in git-ignored result dirs
The headline TTA numbers existed only in git-ignored working-tree JSONs produced by untracked `_tmp` scripts — reproducible while the tree lived, but unrecoverable from version control.

**Context:** Force-add backing artifacts + a tracked regenerator for any number that reaches the paper.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md (H1)

---

## Patterns

### Multi-agent dimension audit → adversarial per-finding verification
Fan out the audit across N dimensions (architecture, loss, tables, …), then have an independent skeptic re-derive each finding from the real files before it counts.

**When to use:** Any large consistency/correctness audit where false positives are costly. Here it yielded 82 findings, 0 false positives.
**Source:** 260609-cpr-SUMMARY.md, CODE-PAPER-REVIEW-2026-06-07.md

### Adversarial pre-check gate before applying edits
Before applying a planned edit set, run skeptics that (a) verify the underlying fact in code, (b) validate the exact edit text + build-safety, (c) hunt for collateral breakage (dangling refs, stale cross-references).

**When to use:** Exact-number or structural LaTeX/code edits where a silent break (undefined ref, wrong column count) is easy to miss.
**Source:** 260609-cpr-SUMMARY.md

### Matched-seed verification before claiming a margin
Replicate *both* sides of a comparison at the same seed count before reporting a difference, especially on seed-unstable metrics.

**When to use:** Any A-vs-B numeric claim where one side has error bars and the other is single-seed.
**Source:** STATE.md (Key Decisions), 260609-cpr-SUMMARY.md

### Resumable workflow recovery from a journaled run
The initial audit workflow's result-assembly had a bug; fixing only the post-agent code and re-running with `resumeFromRunId` replayed all cached agent results instead of re-spending them.

**When to use:** When a long multi-agent workflow fails in synthesis/glue code rather than in the agents themselves.
**Source:** 260609-cpr-SUMMARY.md (process), session workflow runs

---

## Surprises

### The strongest single effect in the matched-seed table was a false negative
The most statistically "clear" cell pre-runs was an apparent −2.3 regression — which evaporated to +0.05 (p=0.97) once matched seeds revealed the seed-42 visual value was a high outlier.

**Impact:** Prevented shipping a false "fusion can hurt" admission; reframed the whole complementarity narrative.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md (M7)

### A "realistic" benchmark was the opposite of realistic
`benchmark_backbones.py` commented its `np.random` frames as "realistic," but noise frames contain no people, so the 33.3 FPS measured near-zero pose load.

**Impact:** Resolved the long-open 21.6-vs-33.3 FPS discrepancy in the paper's favor.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md (M2)

### All headline numbers survived a deep honesty pass unchanged
Across 3 HIGH + 7 MEDIUM + 8 LOW fixes, UCF 82.5% AUC and XD 78.7% AP never moved — the defects were in framing/provenance/disclosure, not the results.

**Impact:** Honesty improvements were "free" — several claims got *stronger* by becoming defensible.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md (Verdict)

### 0 false positives across 82 adversarially-verified findings
Every finding the dimension agents raised was confirmed by an independent skeptic; none were misreads.

**Impact:** High confidence the audit was thorough rather than noisy; the few "leave unchanged" calls (e.g. L6) were also skeptic-confirmed.
**Source:** CODE-PAPER-REVIEW-2026-06-07.md
