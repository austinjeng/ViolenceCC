---
phase: quick
plan: 260601-gap
type: execute
wave: 1
depends_on: []
files_modified: [paper/main.tex]
autonomous: true
requirements: []

must_haves:
  truths:
    - "paper/main.tex reports 74.7% AP (SigLIP2 Base) as the best gated XD-Violence result, matching Table 2's bolded value"
    - "paper/main.tex no longer claims end-to-end training; it states backbones are frozen and only the fusion head/classifier are learned"
    - "Reported hyperparameters (lr, batch size, epochs, top-k, lambda weights, optimizer) match the actual config snapshots"
    - "The fabricated 198-config sweep grid and +3.7/+0.1 tuning deltas are removed from Implementation Details"
    - "Frame-broadcast description says tail-repeat, not zero-pad"
    - "Per-backbone TTA configs are described correctly (CLIP searched; SigLIP2 fixed)"
    - "Parameter-count claims report the 0.5-1.0M range, not a flat 0.8M"
    - "LaTeX remains well-formed (balanced braces, no broken \\cite/\\ref); none of the 15 OLD strings remain; all 15 NEW strings are present"
  artifacts:
    - path: "paper/main.tex"
      provides: "Corrected methodology prose and reported hyperparameters"
      contains: "74.7\\% AP on XD-Violence (SigLIP2 Base)"
  key_links: []
---

<objective>
Reconcile the prose and reported hyperparameters in `paper/main.tex` with the actual configs/results that produced the reported numbers. A 44-agent adversarially-verified code review found that the methodology text systematically MISDESCRIBES the runs (the numbers are real and reproducible from `results/*/config_snapshot.json`; the surrounding descriptions are wrong or fabricated).

Purpose: Make the paper text accurate and defensible before advisor submission. The numbers stay; only the descriptions of how they were produced are corrected.

Output: A `paper/main.tex` whose abstract, methodology (§3.2, §3.4, §3.5), implementation details (§4.2), TTA section (§5), discussion, and conclusion all match the actual experimental configuration.

SCOPE GUARDRAILS (do not violate):
- EDITORIAL ONLY. Do NOT touch any code. Do NOT re-run any experiment.
- Do NOT touch the smoothness / late-fusion / residual EQUATIONS (Eqs. for $\mathcal{L}$, $\mathbf{f}_{\text{late}}$, $\mathbf{f}_{\text{gated}}$). Those are a separate, deferred CODE workstream.
- Do NOT change: the abstract's "+0.6\% for CLIP with SAR", the §5 source-only/TTA table values, the UCF "172 videos excluded" claim, or any Table values.
- Do NOT hand-edit `tables_generated.tex` — it is auto-generated.
- Apply ONLY the 15 verbatim OLD->NEW edits in `<tasks>`. Do not "improve" adjacent prose.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@paper/main.tex

VERIFICATION NOTE (already performed during planning): All 15 OLD strings below were
confirmed to match verbatim in the current `paper/main.tex` (read in full on 2026-06-01).
Line numbers are advisory only — match on TEXT, not line number, because earlier edits in
the same task shift later lines.

DISAMBIGUATION NOTE: EDIT 13 and EDIT 15 both contain the phrase "approximately 0.8M
parameters", but in different sentences with different surrounding context (EDIT 13 is the
§5 Discussion "Computational efficiency" sentence ~line 353; EDIT 15 is the §7 Conclusion
sentence ~line 391). The full OLD strings differ and are each unique in the file. Apply
each by matching its FULL OLD string, not just the shared phrase.

DEFERRED-FINDING NOTE: EDIT 10 removes a fabricated sweep description. This passage is also
entangled with a separate, deferred "test-set-selection" finding the user has not yet
addressed. This plan only removes the fabricated/unsupported sweep-grid + tuning-delta
sentences; it does NOT attempt to resolve the test-set-selection finding.

TOOLCHAIN NOTE: No LaTeX toolchain (latexmk / pdflatex / xelatex) is on PATH in this
environment (verified during planning). The verification task therefore uses a STRUCTURAL
grep + brace-balance check, NOT a compile. Do not block on compilation.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Apply the 15 verbatim OLD->NEW edits to paper/main.tex</name>
  <files>paper/main.tex</files>
  <action>
Apply each of the following 15 edits to `paper/main.tex` using the Edit tool, matching the
OLD string verbatim (exact LaTeX escaping included) and replacing with the NEW string.
Match on text, not line number. Apply them in order. Do NOT alter any other text, equations,
table values, or formatting. Each OLD string was confirmed present verbatim during planning.

--- EDIT 1 (Abstract, ~line 43) — XD headline backbone+number ---
Reason: Table 2 bolds SigLIP2 Base 74.7 as the best gated XD result; SO400M gated is 73.8, not best.
OLD:
```
achieves 83.3\% AUC on UCF-Crime (SigLIP2 Giant) and 73.8\% AP on XD-Violence (SigLIP2 SO400M)
```
NEW:
```
achieves 83.3\% AUC on UCF-Crime (SigLIP2 Giant) and 74.7\% AP on XD-Violence (SigLIP2 Base)
```

--- EDIT 2 (Abstract, ~line 43) — drop "end-to-end" (backbones are frozen) ---
OLD:
```
trained end-to-end with multiple instance learning (MIL) ranking loss.
```
NEW:
```
trained with multiple instance learning (MIL) ranking loss on frozen backbone features (only the lightweight fusion head is learned).
```

--- EDIT 3 (Methodology overview, ~line 129) — drop "end-to-end" ---
OLD:
```
and trained end-to-end with MIL ranking loss.
```
NEW:
```
and trained with MIL ranking loss (only the fusion head and classifier are learned; both backbones are frozen).
```

--- EDIT 4 (§3.2 CTR-GCN, ~line 145) — streams averaged, not concatenated ---
OLD:
```
The four-stream features are concatenated to form the final skeleton representation.
```
NEW:
```
The four-stream features are combined by weighted averaging (joint and bone weighted 1.0, motion streams 0.5) to form the final 256-d skeleton representation.
```

--- EDIT 5 (§3.4 Gated Fusion, ~line 170) — shared dim 512->256 ---
OLD:
```
Each modality is first projected to a shared 512-d space and normalized:
```
NEW:
```
Each modality is first projected to a shared 256-d space and normalized:
```

--- EDIT 6 (§3.5 MIL loss, ~line 194) — lambda values ---
OLD:
```
We set $\lambda_1 = 8 \times 10^{-5}$ and $\lambda_2 = 8 \times 10^{-5}$ following RTFM~\cite{tian2021rtfm}.
```
NEW:
```
We set the sparsity weight $\lambda_1 = 8 \times 10^{-3}$ and the smoothness weight $\lambda_2 = 8 \times 10^{-4}$.
```

--- EDIT 7 (§4.2, ~line 215) — optimizer + lr ---
OLD:
```
The fusion head and anomaly classifier are trained using Adam with a learning rate of $5 \times 10^{-4}$ for UCF-Crime and $1 \times 10^{-3}$ for XD-Violence.
```
NEW:
```
The fusion head and anomaly classifier are trained using AdamW (weight decay $10^{-2}$) with a learning rate of $1 \times 10^{-4}$ for both datasets.
```

--- EDIT 8 (§4.2, ~line 215) — batch size + epochs ---
OLD:
```
We use a batch size of 32 video pairs (normal/anomalous) and train for a maximum of 100 epochs with early stopping (patience of 10 epochs on validation loss).
```
NEW:
```
We use a batch size of 16 normal/anomalous pairs (32 videos per batch) and train for a maximum of 50 epochs with early stopping (patience of 10 epochs on validation loss).
```

--- EDIT 9 (§4.2, ~line 215) — top-k ---
OLD:
```
The top-$k$ selection in MIL ranking uses $k=3$ for UCF-Crime and $k=2$ for XD-Violence.
```
NEW:
```
The top-$k$ selection in MIL ranking uses $k=3$ for both datasets.
```

--- EDIT 10 (§4.2, ~line 215) — remove fabricated sweep grid + tuning deltas ---
Reason: the reported runs all used lr=1e-4/k=3/margin=1.0 defaults; the stated grid was never
run as described (margin was never swept) and the +3.7/+0.1 tuning deltas cannot be traced to
the reported runs. This passage is also entangled with a deferred test-set-selection finding
the user has not yet addressed (see DEFERRED-FINDING NOTE) — only remove the fabricated text here.
OLD:
```
These hyperparameters were determined through a systematic sweep of 198 configurations across both datasets, evaluating combinations of learning rate $\in \{5 \times 10^{-4}, 1 \times 10^{-3}, 2 \times 10^{-3}\}$, top-$k \in \{1, 2, 3, 5\}$, and margin scale $\in \{1.0, 2.0, 4.0\}$, among others. We observed that XD-Violence benefits substantially from tuning (+3.7 percentage points over default), while UCF-Crime performance is largely hyperparameter-insensitive (+0.1 points).
```
NEW:
```
We use a fixed hyperparameter configuration across both datasets (learning rate $1 \times 10^{-4}$, $k=3$, margin $1.0$).
```

--- EDIT 11 (§4.2, ~line 217) — frame broadcast (tail-repeat, not zero-pad) ---
OLD:
```
Snippet-level anomaly scores are expanded to frame-level predictions by assigning each frame the score of its enclosing 64-frame snippet, and zero-padded where snippet boundaries exceed the video length.
```
NEW:
```
Snippet-level anomaly scores are expanded to frame-level predictions by assigning each frame the score of its enclosing 64-frame snippet; the final snippet's score is repeated to cover any trailing frames.
```

--- EDIT 12 (§5 TTA, ~line 323) — per-backbone TTA configs ---
OLD:
```
For each backbone, we apply the best-performing TENT~\cite{wang2021tent} and SAR~\cite{niu2023sar} configurations identified from a comprehensive hyperparameter search on the CLIP backbone (500 total runs; TENT best: $\text{lr}=0.005$; SAR best: $\text{lr}=0.0001$, $\rho=0.01$).
```
NEW:
```
For the CLIP backbone we apply the best TENT~\cite{wang2021tent} and SAR~\cite{niu2023sar} configurations identified from a hyperparameter search on CLIP (TENT: $\text{lr}=0.005$; SAR: $\text{lr}=0.0001$, $\rho=0.01$); the SigLIP2 variants use a fixed configuration (TENT: $\text{lr}=0.001$; SAR: $\text{lr}=0.001$, $\rho=0.05$).
```

--- EDIT 13 (§5 Discussion "Computational efficiency", ~line 353) — parameter count ---
NOTE: Match the FULL OLD string. This is the Discussion sentence, distinct from EDIT 15.
OLD:
```
the gated fusion head contains approximately 0.8M parameters regardless of the visual backbone dimension, as only the projection and gating layers are learned.
```
NEW:
```
the gated fusion head contains 0.50M (CLIP) to 1.02M (SigLIP2 Giant) trainable parameters, scaling with the visual feature dimension $d_v$, as only the projection and gating layers are learned.
```

--- EDIT 14 (§7 Conclusion, ~line 387) — "best UCF" wording (avoid contradicting Limitations' 83.6) ---
OLD:
```
SigLIP2 Giant achieves the best UCF-Crime performance (83.3\% AUC with gated fusion)
```
NEW:
```
SigLIP2 Giant achieves the best UCF-Crime results (83.3\% AUC with gated fusion, 83.6\% with mean-only pooling)
```

--- EDIT 15 (§7 Conclusion, ~line 391) — parameter-count repetition ---
NOTE: Match the FULL OLD string. This is the Conclusion sentence, distinct from EDIT 13.
OLD:
```
requires training only the lightweight fusion head (approximately 0.8M parameters)
```
NEW:
```
requires training only the lightweight fusion head (0.5--1.0M parameters depending on backbone)
```

If ANY OLD string is not found verbatim when you attempt the edit, STOP and report it as
"VERIFY: string not found as written — locate the equivalent current text" rather than
guessing. (During planning all 15 matched verbatim, so this should not occur unless a prior
edit in this same task altered overlapping text.)
  </action>
  <verify>
    <automated>cd D:\ViolenceCC; python -c "import io; t=io.open('paper/main.tex',encoding='utf-8').read(); olds=['and 73.8\\\\% AP on XD-Violence (SigLIP2 SO400M)','trained end-to-end with multiple instance learning','and trained end-to-end with MIL ranking loss.','features are concatenated to form the final skeleton','projected to a shared 512-d space','\\\\lambda_2 = 8 \\\\times 10^{-5} following','using Adam with a learning rate of $5','batch size of 32 video pairs','$k=3$ for UCF-Crime and $k=2$','systematic sweep of 198 configurations','and zero-padded where snippet boundaries','search on the CLIP backbone (500 total runs','approximately 0.8M parameters regardless','best UCF-Crime performance (83.3\\\\% AUC with gated fusion)','lightweight fusion head (approximately 0.8M parameters)']; rem=[o for o in olds if o in t]; print('STALE_OLD_REMAINING:', rem if rem else 'NONE')"</automated>
  </verify>
  <done>All 15 NEW strings are present in paper/main.tex; none of the 15 OLD strings remain (verify task confirms STALE_OLD_REMAINING: NONE). No equations, table values, or out-of-scope prose were modified.</done>
</task>

<task type="auto">
  <name>Task 2: Structural verification — braces balance, no stale OLD strings, all NEW present, no broken cite/ref</name>
  <files>paper/main.tex</files>
  <action>
No LaTeX toolchain is available in this environment (latexmk/pdflatex/xelatex absent, verified
during planning), so do a STRUCTURAL check instead of a compile. Do not block on compilation.

Run the verification commands below. All four checks must pass:

1. BRACE BALANCE: count unescaped `{` vs `}` — they must be equal. (Edits only changed prose
   and inline math; brace count should be unchanged from before, but confirm it balances.)
2. NO STALE OLD: none of the 15 OLD strings remain (same check as Task 1's verify).
3. ALL NEW PRESENT: each of the 15 NEW marker substrings is present.
4. CITES/REFS INTACT: the edits that touched `\cite{...}` (EDIT 6 removed a cite intentionally;
   EDITs 12 retained both `\cite{wang2021tent}` and `\cite{niu2023sar}`) did not leave a dangling
   `\cite{}` or `\cite{` without a closing brace, and `\ref{fig:architecture}`/`\ref{sec:tta}`
   etc. are untouched. Confirm there are zero empty `\cite{}` or `\ref{}` and zero `\cite{`
   immediately followed by whitespace/newline.

If a TeX toolchain happens to be present (re-check with `where latexmk` / `where pdflatex`),
optionally attempt `latexmk -pdf -interaction=nonstopmode paper/main.tex` from `paper/` and
report pass/fail, but do NOT block the task on a compile failure caused by a missing toolchain,
missing figures, or missing `references.bib` resolution.
  </action>
  <verify>
    <automated>cd D:\ViolenceCC; python -c "import io,re; t=io.open('paper/main.tex',encoding='utf-8').read(); nob=re.sub(r'\\\\[{}]','',t); ob=nob.count('{'); cb=nob.count('}'); print('BRACES open',ob,'close',cb,'BALANCED' if ob==cb else 'UNBALANCED'); news=['74.7\\\\% AP on XD-Violence (SigLIP2 Base)','on frozen backbone features (only the lightweight fusion head is learned)','only the fusion head and classifier are learned; both backbones are frozen','combined by weighted averaging (joint and bone weighted 1.0, motion streams 0.5)','projected to a shared 256-d space','sparsity weight $\\\\lambda_1 = 8 \\\\times 10^{-3}$','using AdamW (weight decay $10^{-2}$)','batch size of 16 normal/anomalous pairs (32 videos per batch)','maximum of 50 epochs','$k=3$ for both datasets','fixed hyperparameter configuration across both datasets','final snippet\\'s score is repeated to cover any trailing frames','the SigLIP2 variants use a fixed configuration (TENT: $\\\\text{lr}=0.001$','0.50M (CLIP) to 1.02M (SigLIP2 Giant) trainable parameters','best UCF-Crime results (83.3\\\\% AUC with gated fusion, 83.6\\\\% with mean-only pooling)','(0.5--1.0M parameters depending on backbone)']; miss=[n for n in news if n not in t]; print('MISSING_NEW:', miss if miss else 'NONE'); print('EMPTY_CITE:', t.count('\\\\cite{}')); print('EMPTY_REF:', t.count('\\\\ref{}'))"</automated>
  </verify>
  <done>Brace check reports BALANCED; MISSING_NEW: NONE; EMPTY_CITE: 0; EMPTY_REF: 0. (If a TeX toolchain is present and compile was attempted, report result but do not gate on it.)</done>
</task>

</tasks>

<verification>
Phase-level checks:
- All 15 NEW strings present; all 15 OLD strings absent (Task 1 + Task 2 automated checks).
- LaTeX braces balanced; no empty `\cite{}` / `\ref{}` (Task 2 automated check).
- No equations, table values, or out-of-scope prose changed (the abstract "+0.6\% for CLIP
  with SAR", §5 TTA table values, UCF "172 videos excluded", and `tables_generated.tex` are untouched).
- Edits applied by verbatim text match, not line number.
</verification>

<success_criteria>
- `paper/main.tex` methodology and reported hyperparameters match the actual config snapshots.
- XD headline = 74.7% AP (SigLIP2 Base); "end-to-end" claims removed in favor of frozen-backbone framing.
- Fabricated 198-config sweep + tuning deltas removed; frame broadcast = tail-repeat; per-backbone
  TTA configs correct; parameter count = 0.5-1.0M range; conclusion UCF wording no longer contradicts Limitations' 83.6.
- LaTeX is structurally well-formed (balanced braces, intact cites/refs). No code touched, no experiments re-run.
</success_criteria>

<output>
Create `.planning/quick/260601-gap-reconcile-paper-main-tex-methodology-and/260601-gap-SUMMARY.md` when done.
</output>
