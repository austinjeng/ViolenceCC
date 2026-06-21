---
quick_id: 260621-gcn
type: quick
date: 2026-06-21
files_modified:
  - paper/main.tex
  - paper/references.bib
must_haves:
  truths:
    - "tab:comparison is grouped into two regime blocks (heavier-budget; comparable regime), This-work bolded in the comparable block, rows sorted by UCF AUC within each block"
    - "The caption states an outcome-neutral inclusion rule (strongest published methods + all frozen-feature no-text peers; selection not restricted to favorable comparisons)"
    - "EventVAD (82.03/64.04) and LAVAD (80.28/62.01) appear as rows in the heavier-budget block with new resolvable references.bib entries (shao2025eventvad, zanella2024lavad) and % RE-VERIFY comments on their XD-AP cells"
    - "The §6 comparison paragraph states the inclusion rule, leads with comparable-regime XD-AP parity, keeps the honest UCF-trails statement + CLIP-TSA do-not-isolate hypothesis, and folds in the single-24GB-GPU efficiency point vs EventVAD/LAVAD"
    - "Every number traces verbatim to 12-RESEARCH-sota.md; regime categorization correct; no number changed; headline anchors + Tables 1-3 byte-identical"
    - "build_paper.ps1 -Clean exit 0, 0 undefined citations, page count recorded (apply \\small or trim if it exceeds 11pp); earlier framing fixes (abstract context, XD-scoping, fragment rebalance) intact"
  artifacts:
    - path: "paper/main.tex"
      provides: "Regime-grouped tab:comparison + inclusion-rule caption + EventVAD/LAVAD rows + rewritten §6 comparison paragraph with efficiency point"
    - path: "paper/references.bib"
      provides: "shao2025eventvad + zanella2024lavad entries"
---

<objective>
Restructure the paper's SOTA comparison into an honest, more-favorable framing —
group by operating regime (so This-work sits among its comparable-regime peers,
not next to the 90% text/MLLM leaders), state an outcome-neutral inclusion rule,
lead the prose with XD-AP parity, and fold EventVAD/LAVAD in as an efficiency win.
No method is dropped by outcome; no number changes. Writing task — tests = clean
build + number-traceability, not unit tests.
</objective>

<honesty_guardrails>
- Group by a STATED criterion (operating regime), not by who beats us. Both leaders
  and peers stay in the table.
- Regime categorization: comparable = {CLIP-TSA, MGFN, UR-DMU, Light-WVAD, RTFM,
  This work, Sultani}; heavier = {PI-VAD, DSANet, VadCLIP, EventVAD, LAVAD}.
- Sort by UCF AUC within each block (no gamed sort). This-work is honestly 6th of 7
  in the comparable block on UCF; the favorable angle comes from XD-AP + efficiency
  prose, not from hiding rows.
- Every number verbatim from 12-RESEARCH-sota.md §1/§8. EventVAD 82.03/64.04 AP;
  LAVAD 80.28/62.01 AP (NOT their XD ROC-AUC 87.51/85.36 — flag % RE-VERIFY).
</honesty_guardrails>

<verification>
- build_paper.ps1 -Clean exit 0; main.log "Output written ... (N pages"; 0 "Citation/Reference ... undefined".
- grep: two \midrule blocks + block-header \multicolumn rows; shao2025eventvad + zanella2024lavad each once in references.bib and \cite'd once; This-work bold 82.5/78.7.
- number-traceability: every UCF/XD cell matches a VERIFIED value in 12-RESEARCH-sota.md.
- headline anchors + existing Tables 1-2 (impl/ablation) byte-identical vs pre-task.
- adversarial honesty audit (spawned): confirm no outcome-based selection, correct categorization, no overclaim.
</verification>
