---
quick_id: 260622-vc8
slug: low-batch-paper-editorial
date: 2026-06-22
status: complete
commit: bb71fb9
---

# Summary — Quick Task 260622-vc8 (low-severity batch, paper-editorial group)

Fixed 8 low-severity review findings (paper-editorial). Each was gated behind an **independent
adversarial check** (skeptic re-derived from the live repo, default not-resolved) before being
marked resolved — per the user's requirement. Two findings (T3-3, T5-3) FAILED the first check
(missed occurrences in the standalone fragment `sota_comparison_full.tex`), were re-fixed, and
PASSED a re-check. Editorial/factual only — no numbers changed.

## Findings resolved (all adversarially verified, commit bb71fb9)
- **T2-1** sign test: "8/8 positive, p≈0.008" → "6/8 strictly positive, 2 ties, tie-dropping p≈0.03" (abstract, main.tex:263, conclusion).
- **T2-2** added correlated-configs caveat (shared frozen skeleton stream) at main.tex:263.
- **T2-3** added domain/horizon caveat at main.tex:136 (~20s UCF snippet ≫ CTR-GCN NTU action-clip horizon → plausible cause of weak UCF skeleton-only).
- **T3-2** LAVAD hardware "HPC cluster" → "dual RTX 3090" (table + prose + fragment); 80GB-class now attributed to EventVAD only.
- **T3-3** dropped the false GS-MoE "could not be verified from the primary-source PDF" rationale (numbers verify from arXiv:2508.06318, ICCV 2025); kept the architectural-budget reason; fixed all 3 fragment caveats incl. the contradictory "resists automated verification" line.
- **T4-1** abstract "+13.2%" now labeled the single most-degraded condition.
- **T4-2** main.tex:82 "structural limitation rather than a tuning issue" → grounded mechanistically (LayerNorm-affine-only adaptation of a frozen rank detector).
- **T5-3** TTA gains "%" → "points" in abstract + conclusion + fragment (AUC percentage-points); accuracy %s untouched.

## Verification
- Adversarial check #1 (workflow whwsgh2xx): PASS T2-1,T2-2,T2-3,T3-2,T4-1,T4-2; FAIL T3-3,T5-3 (fragment occurrences missed).
- Residuals fixed in `sota_comparison_full.tex` (TTA-gain "%"→points line 263-264; removed GS-MoE "resists verification" example line 294-295).
- Adversarial re-check (workflow w2hpj9534): PASS T3-3, T5-3.
- `build_paper.ps1 -Clean` → main.pdf clean, 11 pp, latexmk converged; standalone fragment compiles (exit 0, 0 errors); headlines UCF 82.5 / XD 78.7 byte-identical.
- review-2026-06-22.html updated: these 8 marked ✓ resolved (12 of the review's findings now resolved total).

## Deferred (next low-severity groups)
- Paper: T5-2 (abstract density trim), T5-6 (remaining RE-VERIFY comments + author lists).
- Code: C2-1, C3-2, C4-1, C4-3, C1-1/C1-2, C1-3 (hygiene); C7-1, C7-3, T6-2, C6-4 (reproducibility/tests).
