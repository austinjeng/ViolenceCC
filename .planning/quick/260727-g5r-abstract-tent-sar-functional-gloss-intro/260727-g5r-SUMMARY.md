---
quick_id: 260727-g5r
description: Abstract TENT/SAR functional gloss — introduce them as two representative entropy-minimization TTA methods (EN+ZH abstracts)
date: 2026-07-27
status: complete
commit: 07d6851
---

# Summary — Quick Task 260727-g5r

## What was done

Both thesis abstracts now introduce TENT/SAR with a functional gloss so readers
outside WSVAD can tell they are established prior methods, not datasets or our
own variants:

- EN (abstract.tex): "Entropy-minimization TTA (TENT, SAR), … changes AUC" →
  "Two representative entropy-minimization TTA methods (TENT, SAR), restricted
  by the architecture to adapting only the fusion head's LayerNorm parameters,
  change AUC …" (verb agreement fixed).
- ZH (abstract_zh.tex:14): 「以熵最小化為基礎之 TENT 與 SAR 受架構限制…」→
  「以熵最小化為基礎之兩種代表性 TTA 方法（TENT 與 SAR）受架構限制…」.

## Decision trail

User chose "functional gloss" over acronym expansion via AskUserQuestion
(2026-07-27), on the named-method convention: expansions ("sharpness-aware and
reliable") are jargon that self-explain nothing; CLIP/SigLIP2/CTR-GCN stay
unexpanded in the same abstract; thesis abstracts avoid citations. Formal
expansions remain in the notation index (notation.tex:32,34, bound right after
the abstracts); first body use (ch01_introduction.tex:67) carries \cite.

Deliberate deviation from the approved preview, flagged to author: preview
spelled out "test-time adaptation methods", final text uses "TTA methods"
because the immediately preceding sentence defines "(TTA)" — re-spelling a
just-defined abbreviation is a style wart.

## Execution model (session directive)

Fable planned (exact old→new strings in PLAN.md) and verified; one Opus 5
subagent (gloss-executor) applied both edits and ran the clean rebuild.

## Verification (orchestrator, independent)

- git diff: exactly 2 files / 2 hunks, only the planned lines; all headline
  numbers (82.5/78.7, +1.2/+13.2, 0.1) byte-identical elsewhere.
- Clean rebuild: 95 pages, 0 `!` error lines, 0 undefined references/citations;
  main.aux/.bbl/.lof all regenerated fresh.
- Cosmetic note: executor wrapped the EN source lines differently from the plan
  spec (one ~100-char source line); prose content byte-equivalent, PDF output
  identical — accepted, not churned.

## Commit

- 07d6851 `docs(260727-g5r): gloss TENT/SAR in abstracts as representative TTA methods`
