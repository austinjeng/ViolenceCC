---
phase: quick-260601-mry
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - paper/main.tex
autonomous: true
requirements:
  - H2-direction-a-gated-fusion-eq
  - H3-direction-a-late-fusion-eq
must_haves:
  truths:
    - "Eq. (3) describes a 256-d per-dimension gating VECTOR (g bold), not a scalar"
    - "Eq. (4) shows the gated blend PLUS the residual term (ŝ + v̂), with element-wise ⊙ and dropout-after-LN noted"
    - "Eq. (1) describes score-level averaging of two independent heads with fixed 0.5/0.5 weight, not concat+projection"
    - "§4.3 no longer claims the gate 'suppresses' the weaker modality"
    - "§4.3 no longer labels late fusion as '(concatenation with projection)'; the parenthetical describes score averaging"
    - "§5 late-fusion-failure paragraph no longer attributes the gap to 'concatenation' forcing disentanglement, and its first sentence is preserved verbatim"
    - "No remaining 'concatenat' string in paper/main.tex describes the late-fusion mechanism"
    - "All reported numbers (71.8%, 41.3%, 65.5%, 71.0%, etc.), tables, and figures are byte-for-byte unchanged"
  artifacts:
    - path: "paper/main.tex"
      provides: "Fusion equations and dependent Discussion arguments consistent with the implemented architecture"
      contains: "\\mathbf{g} \\odot \\hat{\\mathbf{s}}"
  key_links:
    - from: "paper/main.tex Eq. (4)"
      to: "src/models/gated_fusion.py forward()"
      via: "residual = fused + p_skel + p_clip; out = dropout(ln_fused(residual))"
      pattern: "\\hat\\{\\\\mathbf\\{s\\}\\} \\+ \\hat\\{\\\\mathbf\\{v\\}\\}"
    - from: "paper/main.tex Eq. (1)"
      to: "src/models/late_fusion.py forward()"
      via: "a * s_skel + (1 - a) * s_clip with a=0.5"
      pattern: "a_\\{\\\\text\\{late\\}\\}"
---

<objective>
H2/H3 Direction A (editorial, no code, no re-run): rewrite the gated-fusion equations (Eq. 3, Eq. 4) and the late-fusion equation (Eq. 1) in `paper/main.tex` so they match the implemented architecture, and revise the dependent Discussion arguments so the narrative is consistent with the corrected mechanisms.

Purpose: A code review found that the paper's fusion equations describe architectures the code does not implement. The gated mechanism is a gated-RESIDUAL block with an element-wise (256-d) gate; the residual means it reweights relative contribution rather than suppressing either modality. Late fusion is score-level averaging of two independent heads at a fixed 0.5/0.5 weight, not concat+projection. Three Discussion claims ("suppress the weaker modality"; the "(concatenation with projection)" parenthetical; "concatenation forces the classifier to disentangle") are built on the wrong mechanism. Direction A = fix the paper to match the code. Reported numbers are unaffected.

Output: `paper/main.tex` with seven verbatim OLD→NEW edits applied (EDIT 1–7), all numbers/tables/figures untouched.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

<ground_truth>
The two source files are the architectural ground truth for the edits. Do NOT modify them — they are read-only reference for confirming the equations are correct.

From src/models/gated_fusion.py (forward, lines 70–79):
```
p_skel = self.ln_skel(self.skel_proj(skel))          # [B, T, 256]
p_clip = self.ln_clip(self.clip_proj(clip))          # [B, T, 256]
g = torch.sigmoid(self.gate(torch.cat([p_skel, p_clip], dim=-1)))  # [B, T, 256] VECTOR
fused = g * p_skel + (1.0 - g) * p_clip               # element-wise
residual = fused + p_skel + p_clip                    # gradient highway (residual)
out = self.dropout(self.ln_fused(residual))           # dropout AFTER ln_fused
```
Key facts for the paper: `self.gate = nn.Linear(2*256, 256)` → g is a 256-d per-dimension vector (NOT a scalar). The residual `+ p_skel + p_clip` means the effective per-dimension weighting is `(1+g)⊙ŝ + (2-g)⊙v̂`, so the gate modulates RELATIVE contribution over a baseline that always retains both modalities.

From src/models/late_fusion.py (forward, lines 68–74):
```
s_skel = self.skeleton(skel=skel)   # [B, T]  independent SkeletonProj head → per-snippet score
s_clip = self.clip(clip=clip)        # [B, T]  independent CLIPProj head → per-snippet score
a = self._alpha()                    # default 0.5 (equal), fixed
return a * s_skel + (1 - a) * s_clip
```
Key facts for the paper: late fusion = score-level average of TWO independent classifier heads with a FIXED equal weight (0.5/0.5). There is NO concatenation and NO shared 512-d projection of features.
</ground_truth>
</context>

<guardrails>
EDITORIAL ONLY. The executor MUST NOT:
- Change, recompute, or move any reported number (71.8%, 41.3%, 65.5%, 71.0%, 81.4%, 81.1%, 82.5%, 82.4%, etc.) — they are preserved exactly.
- Touch any table, table value, figure, or `\includegraphics` reference.
- Touch the TTA paragraph (§5 "TTA and the LayerNorm barrier"), the abstract, the MIL ranking-loss equations (Eq. 5+), or any equation other than Eq. (1), (3), (4).
- Modify `src/models/gated_fusion.py` or `src/models/late_fusion.py` (read-only ground truth) or any other code file.
- Apply only PART of an OLD block. Each OLD must be matched and replaced in full.

If ANY OLD block does not match the file verbatim (including LaTeX escaping / whitespace), STOP and flag the mismatch rather than guessing or partially editing. (During planning, all seven OLD blocks were confirmed to match verbatim at the line ranges below.)
</guardrails>

<tasks>

<task type="auto">
  <name>Task 1: Apply the seven verbatim OLD→NEW editorial edits to paper/main.tex</name>
  <files>paper/main.tex</files>
  <action>
Apply these SEVEN edits in order. Each is a verbatim OLD→NEW replacement. Confirm each OLD matches the file exactly (including LaTeX escaping and whitespace) before replacing; if any OLD does not match, STOP and flag rather than guessing. Approximate line numbers are given as anchors — match on content, not line number.

EDIT 5 — Eq. (1) Late Fusion (around lines 164–168):
OLD:
\textbf{Late Fusion.} The simplest approach concatenates the two feature vectors and projects them to a shared 512-dimensional space through a linear transformation followed by ReLU activation:
\begin{equation}
    \mathbf{f}_{\text{late}} = \text{ReLU}\left(W_{\text{proj}} \left[ \mathbf{s} \| \mathbf{v} \right] + \mathbf{b}_{\text{proj}}\right)
\end{equation}
where $[\cdot \| \cdot]$ denotes concatenation and $W_{\text{proj}} \in \mathbb{R}^{512 \times (256 + d_v)}$. This serves as a baseline that treats both modalities equally without learned weighting.
NEW:
\textbf{Late Fusion.} The simplest approach scores each modality independently and averages the two snippet-level anomaly scores. Each modality is passed through its own classifier head---$h_s(\cdot)$ for the skeleton stream and $h_v(\cdot)$ for the visual stream---and the resulting per-snippet scores are combined with a fixed equal weight:
\begin{equation}
    a_{\text{late}} = \tfrac{1}{2}\, h_s(\mathbf{s}) + \tfrac{1}{2}\, h_v(\mathbf{v})
\end{equation}
This serves as a baseline that treats both modalities equally with a fixed weighting and no input-dependent adaptation.

EDIT 1 — Eq. (3) gate scalar→vector (around lines 174–177):
OLD:
A gating scalar $g \in [0, 1]$ is computed from the concatenated projected features:
\begin{equation}
    g = \sigma\left( W_g \left[ \hat{\mathbf{s}} \| \hat{\mathbf{v}} \right] + b_g \right)
\end{equation}
NEW:
A gating vector $\mathbf{g} \in [0, 1]^{256}$ is computed per dimension from the concatenated projected features:
\begin{equation}
    \mathbf{g} = \sigma\left( W_g \left[ \hat{\mathbf{s}} \| \hat{\mathbf{v}} \right] + \mathbf{b}_g \right)
\end{equation}

EDIT 2 — Eq. (4) + trailing LN text (around lines 178–182):
OLD:
The fused representation is a weighted combination:
\begin{equation}
    \mathbf{f}_{\text{gated}} = \text{LN}_f\left( g \cdot \hat{\mathbf{s}} + (1 - g) \cdot \hat{\mathbf{v}} \right)
\end{equation}
where $\text{LN}_s$, $\text{LN}_v$, and $\text{LN}_f$ are LayerNorm~\cite{ba2016layernorm} layers. The use of three LayerNorm layers (rather than BatchNorm) is motivated by the variable batch composition in MIL training and has implications for TTA, as discussed in Section~\ref{sec:tta}.
NEW:
The fused representation applies the gated blend together with a residual connection that retains both projected modalities, followed by dropout:
\begin{equation}
    \mathbf{f}_{\text{gated}} = \text{LN}_f\left( \mathbf{g} \odot \hat{\mathbf{s}} + (1 - \mathbf{g}) \odot \hat{\mathbf{v}} + \hat{\mathbf{s}} + \hat{\mathbf{v}} \right)
\end{equation}
where $\odot$ denotes element-wise multiplication and $\text{LN}_s$, $\text{LN}_v$, and $\text{LN}_f$ are LayerNorm~\cite{ba2016layernorm} layers (dropout is applied after $\text{LN}_f$). The residual term $\hat{\mathbf{s}} + \hat{\mathbf{v}}$ gives an effective per-dimension weighting of $(1 + \mathbf{g}) \odot \hat{\mathbf{s}} + (2 - \mathbf{g}) \odot \hat{\mathbf{v}}$, so the gate modulates each modality's \emph{relative} contribution over a baseline that always retains both, rather than suppressing either outright. The use of three LayerNorm layers (rather than BatchNorm) is motivated by the variable batch composition in MIL training and has implications for TTA, as discussed in Section~\ref{sec:tta}.

EDIT 7 — §4.3 late-fusion parenthetical (around line 263). This OLD is the SECOND sentence of the paragraph; replace ONLY the parenthetical clause as shown (the surrounding sentence text is preserved). This is the same H3 mismatch as EDIT 5: the parenthetical mislabels the implemented score-averaging late fusion as concatenation:
OLD:
the gated fusion mechanism outperforms simple late fusion (concatenation with projection).
NEW:
the gated fusion mechanism outperforms simple late fusion (equal-weight score averaging).

EDIT 3 — §4.3 "suppressing" (around line 263). NOTE: this OLD is the FINAL sentence of the same paragraph; replace ONLY this sentence. The earlier parenthetical in this paragraph is handled by EDIT 7 above — apply EDIT 7 and EDIT 3 as two independent replacements within this paragraph:
OLD:
We attribute this to the learned gating mechanism's ability to weight modalities differently for each input, suppressing the weaker modality when its signal is noisy.
NEW:
We attribute this to the learned gating mechanism's ability to weight modalities differently for each input, reducing the weaker modality's relative contribution when its signal is noisy.

EDIT 4 — Fig. gating-distribution caption (around line 339):
OLD:
A gate value of $g > 0.5$ indicates stronger skeleton weighting.
NEW:
A mean gate value $\bar{g} > 0.5$ indicates stronger skeleton weighting.

EDIT 6 — §5 "late fusion failure mode" paragraph (around line 349). Replace ONLY the second+third sentences below; the paragraph's first sentence ("The consistent underperformance of late fusion relative to both gated fusion and, in some cases, visual-only baselines warrants attention.") MUST remain intact:
OLD:
When the skeleton signal quality is low (as reflected by its 71.8\% standalone AUC on UCF-Crime and 41.3\% AP on XD-Violence), simple concatenation forces the downstream classifier to disentangle useful skeleton information from noise---a task that a single linear projection may lack the capacity to solve. The gated mechanism, by learning to modulate each modality's contribution with a sigmoid gate, provides an implicit attention mechanism that can effectively suppress the skeleton stream for inputs where visual features alone are more informative.
NEW:
Late fusion combines the two modalities with a fixed equal weight, so when the skeleton signal quality is low (as reflected by its 71.8\% standalone AUC on UCF-Crime and 41.3\% AP on XD-Violence) it still contributes half of every score, degrading inputs where the visual stream alone is more reliable. The gated mechanism instead learns an input-dependent, per-dimension reweighting over a residual baseline, allowing it to reduce the skeleton stream's relative contribution for inputs where visual features are more informative.
  </action>
  <verify>
    <automated>git -C D:/ViolenceCC diff --stat -- paper/main.tex | grep -q "paper/main.tex"</automated>
  </verify>
  <done>All seven OLD blocks replaced with their NEW text. `git diff` shows changes ONLY in paper/main.tex, only within the spans of EDIT 1–7. No numbers (71.8%, 41.3%, 65.5%, 71.0%, etc.), tables, figures, the TTA paragraph, the abstract, or any code file changed.</done>
</task>

<task type="auto">
  <name>Task 2: Structural verification of the edited LaTeX (no TeX toolchain — grep/structural only)</name>
  <files>paper/main.tex</files>
  <action>
No LaTeX toolchain is on PATH, so this is a structural-grep verification only (no compile). Run these checks against paper/main.tex and the git diff. All must pass.

1. Brace balance: count `{` vs `}` across the whole file; they must be equal (or unchanged from before the edit — the seven NEW blocks introduce balanced braces only).

2. No broken `\cite` / `\ref`: the only such macros inside the edited spans are `\cite{ba2016layernorm}` (preserved in EDIT 2) and `Section~\ref{sec:tta}` (preserved in EDIT 2). Confirm `ba2016layernorm` and `sec:tta` still appear in the edited region and that no `\cite{}`/`\ref{}` is left empty.

3. New equations / phrasing present:
   - Gated residual form: `\mathbf{g} \odot \hat{\mathbf{s}}` AND `+ \hat{\mathbf{s}} + \hat{\mathbf{v}}` AND `(1 + \mathbf{g}) \odot \hat{\mathbf{s}}` all appear.
   - Late score-average form: `a_{\text{late}} = \tfrac{1}{2}\, h_s(\mathbf{s})` appears.
   - EDIT 7 new parenthetical: `simple late fusion (equal-weight score averaging)` appears.

4. Old mechanisms gone (in these two mechanisms' context):
   - The word "suppress" no longer describes the gate. Specifically, neither "suppressing the weaker modality" nor "suppress the skeleton stream" appears anywhere in the file.
   - "concatenation forces" / "simple concatenation forces" no longer appears.
   - The §4.3 mislabel `late fusion (concatenation with projection)` no longer appears.
   - Eq. (4) old form `(1 - g) \cdot \hat{\mathbf{v}}` (scalar, no residual) no longer appears.
   - Eq. (1) old form `\mathbf{f}_{\text{late}} = \text{ReLU}` no longer appears.

   CONCATENAT GATE: After EDIT 7, NO remaining "concatenat" string in the file may describe the late-fusion mechanism. The only acceptable remaining "concatenat" hits are unrelated usages: the formal feature-concatenation notation `$[\cdot \| \cdot]$ denotes concatenation` in the gated-fusion §3 math (Eq. 3 input is genuinely the concatenation of $\hat{\mathbf{s}}$ and $\hat{\mathbf{v}}$ before the gate linear layer), and any "concatenated mean and max pooling" temporal-aggregation usage. Confirm each surviving "concatenat" occurrence and assert NONE of them sits in a clause describing the late-fusion baseline. If any remaining "concatenat" describes late fusion, FAIL.

5. Numbers preserved: confirm 71.8\%, 41.3\%, 65.5\%, 71.0\% still appear exactly as before (EDIT 6 re-states 71.8% and 41.3% verbatim; the others are untouched).

6. EDIT 6 first sentence intact: "The consistent underperformance of late fusion relative to both gated fusion and, in some cases, visual-only baselines warrants attention." still appears verbatim.
  </action>
  <verify>
    <automated>cd D:/ViolenceCC; python -c "import re,sys; t=open('paper/main.tex',encoding='utf-8').read(); req=[r'\mathbf{g} \odot \hat{\mathbf{s}}', r'+ \hat{\mathbf{s}} + \hat{\mathbf{v}}', r'(1 + \mathbf{g}) \odot \hat{\mathbf{s}}', r'a_{\text{late}} = \tfrac{1}{2}\, h_s(\mathbf{s})', 'simple late fusion (equal-weight score averaging)']; gone=['suppressing the weaker modality','suppress the skeleton stream','simple concatenation forces','late fusion (concatenation with projection)',r'\mathbf{f}_{\text{late}} = \text{ReLU}', r'(1 - g) \cdot \hat{\mathbf{v}}']; nums=['71.8','41.3','65.5','71.0']; first='The consistent underperformance of late fusion relative to both gated fusion and, in some cases, visual-only baselines warrants attention.'; errs=[]; errs+=[f'MISSING: {s}' for s in req if s not in t]; errs+=[f'STILL PRESENT: {s}' for s in gone if s in t]; errs+=[f'NUMBER LOST: {n}' for n in nums if n not in t]; errs+=['FIRST SENTENCE LOST'] if first not in t else []; errs+=['BRACE IMBALANCE'] if t.count('{')!=t.count('}') else []; lf=[ln for ln in t.splitlines() if 'concatenat' in ln and ('late fusion' in ln or 'late-fusion' in ln)]; errs+=[f'CONCATENAT DESCRIBES LATE FUSION: {ln.strip()[:80]}' for ln in lf]; print('\n'.join(errs) if errs else 'ALL STRUCTURAL CHECKS PASS'); sys.exit(1 if errs else 0)"</automated>
  </verify>
  <done>The structural check script prints "ALL STRUCTURAL CHECKS PASS" and exits 0: braces balanced, the five required new equation/phrasing fragments present, all six old-mechanism strings absent, the four reported numbers preserved, EDIT 6's first sentence intact, and NO remaining "concatenat" string sits in a clause describing late fusion. Any surviving "concatenat" hits are unrelated (the §3 formal `$[\cdot \| \cdot]$ denotes concatenation` notation and temporal pooling usage), noted in the SUMMARY.</done>
</task>

</tasks>

<verification>
- `git diff -- paper/main.tex` touches only the seven edit spans; no other file changed.
- Brace balance preserved; no empty `\cite{}`/`\ref{}`; `ba2016layernorm` and `sec:tta` references intact.
- Eq. (1) now `a_{\text{late}} = \tfrac{1}{2}\, h_s(\mathbf{s}) + \tfrac{1}{2}\, h_v(\mathbf{v})`; Eq. (3) gate is bold vector `\mathbf{g} \in [0,1]^{256}`; Eq. (4) includes the residual `+ \hat{\mathbf{s}} + \hat{\mathbf{v}}` with `\odot`.
- §4.3 parenthetical now reads "(equal-weight score averaging)"; "suppress" (gated context) and "concatenation forces" / "simple concatenation" no longer describe these two mechanisms.
- No remaining "concatenat" string describes the late-fusion mechanism.
- All reported numbers, tables, figures, the TTA paragraph, and the abstract are unchanged.
</verification>

<success_criteria>
- Seven verbatim OLD→NEW edits applied to `paper/main.tex` (EDIT 1–7).
- Fusion equations and the dependent Discussion arguments are consistent with the implemented architecture (element-wise residual gate; fixed-weight score-average late fusion).
- No remaining "concatenat" string in the paper describes the late-fusion mechanism.
- Structural verification passes; no TeX compile required.
- Zero changes to numbers, tables, figures, code, the TTA paragraph, or the abstract.
</success_criteria>

<output>
Create `.planning/quick/260601-mry-h2-h3-direction-a-rewrite-gated-late-fus/260601-mry-SUMMARY.md` when done.
</output>
</content>
</invoke>
