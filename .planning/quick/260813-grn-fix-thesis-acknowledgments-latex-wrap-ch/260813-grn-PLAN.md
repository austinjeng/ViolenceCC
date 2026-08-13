---
phase: quick-260813-grn
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - thesis/frontmatter/acknowledgments.tex
autonomous: true
requirements: [QUICK-260813-grn]
must_haves:
  truths:
    - "thesis/main.pdf builds cleanly (exit 0, log scan clean) with the filled Chinese acknowledgments"
    - "The acknowledgments page renders the author's Traditional Chinese text (not missing glyphs / not a LaTeX error)"
    - "The signature block (鄭暐瀚　謹誌於 / 國立臺灣科技大學資訊管理系 / 中華民國一一五年八月) appears right-aligned on three separate lines"
    - "The month blank ＿ is replaced with 八 (author-confirmed August)"
    - "All author prose paragraphs are byte-identical to the current file (no wording changes)"
  artifacts:
    - path: "thesis/frontmatter/acknowledgments.tex"
      provides: "CJK-wrapped acknowledgments with flushright signature block and filled month"
      contains: "\\begin{CJK}{UTF8}{bkai}"
    - path: "thesis/main.pdf"
      provides: "Rebuilt thesis PDF (~95-96pp) — git-ignored, NOT committed"
  key_links:
    - from: "thesis/main.tex"
      to: "thesis/frontmatter/acknowledgments.tex"
      via: "\\input{frontmatter/acknowledgments} at main.tex:26 (no outer CJK wrapper — env must live inside the file)"
      pattern: "input\\{frontmatter/acknowledgments\\}"
    - from: "thesis/frontmatter/acknowledgments.tex"
      to: "CJKutf8 bkai font machinery"
      via: "\\begin{CJK}{UTF8}{bkai} ... \\end{CJK} (same pattern as abstract_zh.tex lines 6/22)"
      pattern: "begin\\{CJK\\}\\{UTF8\\}\\{bkai\\}"
---

<objective>
Fix three LaTeX-structure issues in the author-filled thesis acknowledgments, then rebuild the thesis PDF.

Purpose: The author filled thesis/frontmatter/acknowledgments.tex with approved Traditional Chinese prose, but the file has no CJK environment (pdflatex+CJKutf8 cannot typeset the Chinese without it), the 3-line signature block collapses into one flowing paragraph, and the date month is an unfilled blank ＿. This is one of the three open pre-binding items (M15 in the 07-16 final review).
Output: Corrected acknowledgments.tex + freshly rebuilt thesis/main.pdf (git-ignored, not committed).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@thesis/frontmatter/acknowledgments.tex
@thesis/frontmatter/abstract_zh.tex
@scripts/build_thesis.ps1

Current state of acknowledgments.tex (verified during planning):
- Lines 1-6: header comments (keep as-is)
- Line 7: `\chapter*{Acknowledgments}` — English title, stays OUTSIDE the CJK env
- Line 8: `\addcontentsline{toc}{chapter}{Acknowledgments}` — English, stays OUTSIDE the CJK env (no texorpdfstring trick needed, unlike abstract_zh.tex whose title itself is Chinese)
- Lines 10-24: seven Chinese prose paragraphs — author-approved wording, MUST NOT change
- Lines 26-28: signature block as three bare lines (no `\\`), ending with unfilled 「中華民國一一五年＿月」

CJK pattern of record (abstract_zh.tex line 6 / line 22): `\begin{CJK}{UTF8}{bkai}` ... `\end{CJK}`

Build convention (script read during planning): `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean` — runs `latexmk -C` then a full pdflatex→bibtex→pdflatex×2 rebuild inside thesis/, then scans thesis/main.log and exits nonzero on any `!` error line or undefined refs/citations. Prior clean builds are 95pp.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Wrap Chinese in CJK env, flushright the signature block, fill the month</name>
  <files>thesis/frontmatter/acknowledgments.tex</files>
  <action>
Make exactly three surgical structure edits with the Edit tool (never heredoc). Do NOT touch any character of the prose paragraphs at lines 10-24 — content is author-approved as written.

1. Insert `\begin{CJK}{UTF8}{bkai}` on its own line immediately after the `\addcontentsline{toc}{chapter}{Acknowledgments}` line (line 8), before the first prose paragraph. Keep a blank line between `\begin{CJK}...` and the first paragraph so paragraph breaks are preserved. The `\chapter*{Acknowledgments}` title and the `\addcontentsline` stay outside the CJK env (they are pure ASCII).

2. Replace the final three bare lines

   鄭暐瀚　謹誌於
   國立臺灣科技大學資訊管理系
   中華民國一一五年＿月

   with a right-aligned block preceded by vertical space:

   \vspace{2em}
   \begin{flushright}
   鄭暐瀚　謹誌於\\
   國立臺灣科技大學資訊管理系\\
   中華民國一一五年八月
   \end{flushright}

   Preserve the full-width space U+3000 between 鄭暐瀚 and 謹誌於 exactly as the author typed it. The last line of the flushright block takes no trailing `\\`. This edit also performs fix 3: 「＿月」→「八月」 (author confirmed 八月 via interactive question — the ONLY character-level content change permitted).

3. Close with `\end{CJK}` on its own line as the last content line of the file, after `\end{flushright}`.
  </action>
  <verify>
    <automated>cd /d/ViolenceCC && grep -c 'begin{CJK}{UTF8}{bkai}' thesis/frontmatter/acknowledgments.tex && grep -c 'end{CJK}' thesis/frontmatter/acknowledgments.tex && grep -c 'begin{flushright}' thesis/frontmatter/acknowledgments.tex && grep -c '中華民國一一五年八月' thesis/frontmatter/acknowledgments.tex && ! grep -q '＿' thesis/frontmatter/acknowledgments.tex && git diff --stat thesis/frontmatter/acknowledgments.tex</automated>
  </verify>
  <done>File contains exactly one `\begin{CJK}{UTF8}{bkai}` (after \addcontentsline) and one matching `\end{CJK}` (end of file); signature block sits in a `flushright` env with `\\` breaks preceded by `\vspace{2em}`; 「八月」 present, ＿ absent; `git diff` shows changes ONLY at the env-insertion points and the signature block — all seven prose paragraphs untouched.</done>
</task>

<task type="auto">
  <name>Task 2: Clean-rebuild thesis PDF and verify the acknowledgments page renders</name>
  <files></files>
  <action>
Run the thesis build from the repo root in a visible foreground shell (no headless background per project convention; the build takes ~1-3 min):

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean

The script itself hard-fails (nonzero exit) on any LaTeX `!` error line or undefined reference/citation in thesis/main.log — a passing exit code already proves a clean compile. If it fails with CJK-related errors (e.g. "Unicode character ... not set up"), a Chinese character leaked outside the CJK env — fix the env boundaries in Task 1's file, do not alter prose.

Then verify the acknowledgments page with PyMuPDF (available in the environment; used by prior tasks 260716-q9z and 260804-o0k). Write a short throwaway script in the scratchpad directory (NOT in the repo) that:
1. Opens thesis/main.pdf and asserts page_count is 95 or 96 (was 95pp; filled acknowledgments may add one page).
2. Finds the page whose extracted text contains "Acknowledgments" (the English chapter title extracts reliably even when CJK glyph extraction does not).
3. Renders that page to a pixmap and asserts substantial non-white ink below the title region (i.e., the Chinese body actually typeset — page is not blank apart from the heading). CJKutf8 bkai subfonts may lack usable ToUnicode maps, so do NOT gate on extracting Chinese characters; if 謹誌 or 楊傳凱 DO extract, report it as bonus confirmation.
4. Saves the rendered page PNG to the scratchpad and reports its path so the render can be eyeballed.

Do NOT commit thesis/main.pdf or any build artifact (git-ignored per CLAUDE.md). Commit only thesis/frontmatter/acknowledgments.tex.
  </action>
  <verify>
    <automated>powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean; scratchpad PyMuPDF script exits 0 (page count 95-96, acknowledgments page located, non-blank body render)</automated>
    <human-check>Open the saved PNG of the acknowledgments page: Chinese prose renders in bkai, signature block is right-aligned on three lines, date reads 中華民國一一五年八月</human-check>
  </verify>
  <done>Build exits 0 with "LOG SCAN: clean"; thesis/main.pdf regenerated at 95-96pp; acknowledgments page render shows typeset Chinese body (non-blank below the English title); rendered PNG saved to scratchpad for eyeball confirmation; no build artifacts staged or committed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| (none) | Docs-only LaTeX edit + local build; no untrusted input, no network, no package-manager installs (MiKTeX on-demand CTAN installs are pre-existing build behavior, unchanged by this plan) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-q260813-01 | Tampering | thesis/frontmatter/acknowledgments.tex prose | mitigate | Task 1 verify gates on `git diff` showing zero prose-paragraph hunks; only env insertion + signature block + ＿→八 permitted |
</threat_model>

<verification>
1. `git diff thesis/frontmatter/acknowledgments.tex` shows only: one `\begin{CJK}{UTF8}{bkai}` insertion, the signature-block rewrite (vspace + flushright + `\\` + 八月), and one trailing `\end{CJK}` — nothing else.
2. `build_thesis.ps1 -Clean` exits 0 with a clean log scan (0 LaTeX errors, 0 undefined refs/citations).
3. thesis/main.pdf page count 95-96; acknowledgments page shows typeset Chinese body.
4. `git status` shows no PDF/build artifacts staged.
</verification>

<success_criteria>
- Acknowledgments Chinese content compiles inside `\begin{CJK}{UTF8}{bkai}`...`\end{CJK}` matching the abstract_zh.tex pattern
- Signature block renders right-aligned on three separate lines with `\vspace{2em}` above it
- Date reads 中華民國一一五年八月 (blank filled, author-confirmed)
- Author's prose wording byte-identical — zero content edits beyond ＿→八
- Fresh clean rebuild succeeds; thesis/main.pdf reflects the change; artifacts not committed
</success_criteria>

<output>
Create `.planning/quick/260813-grn-fix-thesis-acknowledgments-latex-wrap-ch/260813-grn-SUMMARY.md` when done.
Commit only thesis/frontmatter/acknowledgments.tex (+ planning docs), message style: `docs(quick-260813-grn): wrap acknowledgments in CJK env, flushright signature, fill 八月`
</output>
