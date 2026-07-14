# Quick Task 260714-gd8: Archive thesis appendices A–F out of the build - Context

**Gathered:** 2026-07-14
**Status:** Ready for planning
**Design by:** Fable 5. Execution: Opus 4.8 executor. Decisions LOCKED.

<domain>
## Task Boundary

Remove Appendices A–F (currently PDF p.102+) from the thesis build, preserving them retrievably (author: "remove it from the main paper and place it somewhere else in case we need it back"). Thesis only — the CGW paper has no appendices. All body cross-references must be reworded so the PDF has zero broken refs. No content claims may silently lose their support-wording (rephrase, don't just delete mid-sentence).
</domain>

<decisions>
## Implementation Decisions (LOCKED)

### Archive mechanism
- `git mv thesis/appendices/*.tex` → `thesis/appendices_archived/` (same filenames).
- Add `thesis/appendices_archived/README.md`: what these are, why archived (author decision 2026-07-14, quick 260714-gd8), and exact restore steps: (1) `git mv` the six files back to `thesis/appendices/`, (2) re-add the `\appendix` + `\include` block to `main.tex` (block preserved verbatim in the README), (3) restore the body cross-references from git history (`git show 484b84b -- thesis/chapters/` or this task's parent commit), (4) rebuild.
- `thesis/tables/tab_percat_ucf.tex`, `tab_percat_xd.tex`, `tab_percat_rtfm.tex` stay where they are (only archived appB inputs them — harmless, note in README).
- `main.tex`: delete the `\appendix` + six `\include{appendices/...}` lines; replace with a 2-line comment pointing at `appendices_archived/README.md`.

### Cross-reference rewording (19 refs + 1 word-mention, all verified by grep)
Principles: keep every factual claim; remove pointers to material no longer in the document; never leave a sentence implying the reader can find something that isn't there. Per site:

1. `ch01_introduction.tex:181-185` (CGW-delta list, added in 260713-mkh): rewrite the delta items WITHOUT appendix pointers. New delta content: (a) full three-seed ablation grid across six fusion variants and four backbones (Tables 5.1–5.2); (b) per-category and failure analysis (Sections 5.7–5.9) and an RTFM baseline-reproduction investigation summarized in Section 8.1; (c) the complete test-time-adaptation investigation narrative (Sections 6.2–6.3). Drop the appendices D–E documentation item.
2. `ch01_introduction.tex:252` ("appear in Appendix~\ref{app:e}" — reproducibility pointer): reword the sentence to state the reproducibility measures themselves (fixed seeds {42,123,2024}, committed configs and manifests, tracked metrics files) without the pointer.
3. `ch01_introduction.tex:270-273` (§1.7 roadmap sentence listing all six appendices): delete the appendix sentence entirely; the roadmap ends with Chapter 9.
4. `ch04` (3 refs): reword each so the methodological fact stands alone (e.g., "full per-condition parameters are listed in Appendix X" → "…use the ImageNet-C reference parameterizations given in Table 4.1"; executor judges per sentence, preserving truth).
5. `ch05` (5 refs): per-category-table pointers (app:b) → point to Table 5.3 / Section 5.8 where the in-chapter summary lives, or state "full per-category tables are omitted here"; appF figure pointers → drop the parenthetical (Figure 5.2 remains the in-thesis qualitative example).
6. `ch07` (1), `ch09` (1): drop/reword parenthetical pointers the same way.
7. `ch08` (1 ref, RTFM App A pointer): keep §8.1's own summary of the reproduction miss (it already states the numbers); replace the pointer with a clause noting the diagnostic investigation localized the gap to the training side (feature dimensionality/MTN/batch mismatches) while the evaluation harness was cleared by an independent sanity anchor — all facts already present in ch08/appA; no new claims.
8. The single non-ref "Appendix/appendices" word mention (grep `ppendix` outside `ref{app:`): reword consistently.
9. AFTER rewording, `grep -rn "app:" thesis/chapters/ thesis/frontmatter/` must return ZERO hits, and `grep -rin "appendix\|appendices" thesis/chapters/ thesis/frontmatter/ thesis/main.tex` must return zero PDF-visible mentions (LaTeX comments are fine).

### Untouched
- `thesis/references.bib` — verified: all 45 keys are cited in the body; reference list is unaffected. The 45/45 coverage comment in main.tex stays true (re-verify with grep after edits).
- `thesis/PROVENANCE.md` — internal tracking doc; add one line noting appendices archived 2026-07-14 (quick 260714-gd8), do not rewrite rows.
- `.planning/THESIS-REVIEW-2026-07-11.md` — historical review record; do not edit.

### Verification gate (before final commit)
1. `build_thesis.ps1 -Clean` exits 0; log scan clean.
2. PDF: zero `??`, zero `[?]`; TOC contains no Appendix entries; LoF/LoT contain no A.x–F.x items; last section is References; page count drops from 131 to ~101–105.
3. `grep` gates from decision 9 pass.
4. Cite coverage still 45/45 (rendered reference count = 45).
5. NTUST order still holds (…References last); front matter untouched.

### Commit plan
1. `refactor(thesis): archive appendices A-F out of the build (restorable)` — the move, main.tex, README, all chapter rewordings, PROVENANCE note.
2. Orchestrator docs commit (PLAN/CONTEXT/SUMMARY/STATE).

### Claude's Discretion
- Exact rewording within the per-site principles above.
- Whether a dropped parenthetical needs a comma/word cleanup around it.
</decisions>

<specifics>
## Specific Ideas
- Ref counts by file (grep-verified): ch01=8, ch04=3, ch05=5, ch07=1, ch08=1, ch09=1; labels defined in appendices: 48 (all leave the build together — no body label depends on them once refs are reworded).
- Current build: 131 pp; Appendix A starts at PDF p.102.
</specifics>

<canonical_refs>
## Canonical References
- `.planning/quick/260713-mkh-thesis-p0-fixes/260713-mkh-CONTEXT.md` — prior task that added the delta list being rewritten here
- `CLAUDE.md` — never commit build artifacts
</canonical_refs>
