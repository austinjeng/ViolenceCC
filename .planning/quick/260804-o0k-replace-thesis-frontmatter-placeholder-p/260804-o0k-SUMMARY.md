---
phase: quick-260804-o0k
plan: 01
subsystem: thesis-frontmatter
tags: [thesis, latex, pdfpages, frontmatter, pre-binding]
requires: []
provides:
  - "thesis/frontmatter/signed_forms.pdf — tracked 2-page signed scan (p.1 審定書, p.2 推薦書)"
  - "thesis/main.pdf pages 3-4 render the signed 推薦書/審定書 (no grey placeholders)"
affects: [thesis-build]
tech-stack:
  added: [pdfpages (LaTeX package, MiKTeX)]
  patterns: ["\\includepdf for scanned frontmatter pages (handles page break + empty pagestyle itself)"]
key-files:
  created:
    - thesis/frontmatter/signed_forms.pdf
  modified:
    - thesis/frontmatter/recommendation.tex
    - thesis/frontmatter/approval.tex
    - thesis/preamble.tex
decisions:
  - "Crossed page mapping kept in the .tex files, NOT by reordering main.tex: recommendation.tex embeds scan page 2, approval.tex embeds scan page 1 (scan order is 審定書 first, binding order is 推薦書 first)"
  - "Scan copied to ASCII path thesis/frontmatter/signed_forms.pdf to avoid CJK-path issues in latexmk; root upload 審定書和推薦書.pdf left untracked and untouched"
metrics:
  duration: ~5 min
  completed: 2026-08-04
  tasks: 3/3
  commits: 1
---

# Quick 260804-o0k: Replace Thesis Frontmatter Placeholders with Signed Scans Summary

Signed 推薦書/審定書 scans embedded at thesis pages 3-4 via pdfpages with a crossed page mapping (scan order reversed vs. binding order), closing pre-binding item #3; clean 95pp rebuild.

## What Was Done

- **Task 1 — Copy scan + switch to pdfpages** (commit `fec05f5`):
  - Copied the user's upload `審定書和推薦書.pdf` (1,743,631 bytes, byte-identical) to `thesis/frontmatter/signed_forms.pdf` (ASCII path, tracked by git without `-f`).
  - `thesis/preamble.tex`: added `\usepackage{pdfpages}` directly after `graphicx`, before `hyperref`.
  - `thesis/frontmatter/recommendation.tex`: full rewrite → header comment + `\includepdf[pages=2]{frontmatter/signed_forms.pdf}` (scan p.2 = 推薦書 signed 2026-07-30).
  - `thesis/frontmatter/approval.tex`: full rewrite → header comment + `\includepdf[pages=1]{frontmatter/signed_forms.pdf}` (scan p.1 = 審定書 signed 2026-07-21, chair stamp). Deliberate crossing documented in both file headers; `thesis/main.tex` untouched.
- **Task 2 — Clean rebuild**: `build_thesis.ps1 -Clean` exit 0; script log scan clean (0 LaTeX errors, 0 undefined refs/citations); `main.log` reports `Output written on main.pdf (95 pages` — 1:1 placeholder replacement confirmed. pdfpages was already available in MiKTeX (no CTAN auto-install needed).
- **Task 3 — Visual verification + commit**: PyMuPDF rendered pages 1-5 at 80 dpi (read-only, vcc-main env). Confirmed p.1 cover and p.2 titlepage unchanged; **p.3 = signed 指導教授推薦書** (advisor signature, date 2026/07/30, barcode M11309108); **p.4 = signed 學位考試委員審定書** (3 committee signatures + advisor signature + red chair stamp 朱宇倩, date 2026/07/21); p.5 = 中文摘要 with Roman numeral I. No swap, no grey placeholder text. Committed exactly the 4 source files.

## Commits

| Commit | Message |
| --- | --- |
| `fec05f5` | docs(quick-260804-o0k): replace 推薦書/審定書 placeholders with signed scans |

`git show --stat HEAD` lists exactly: thesis/frontmatter/approval.tex, thesis/frontmatter/recommendation.tex, thesis/frontmatter/signed_forms.pdf (new, 1,743,631 bytes), thesis/preamble.tex. No deletions. Build artifacts (thesis/main.pdf etc.) not committed (git-ignored).

## Deviations from Plan

None - plan executed exactly as written. (Only incidental note: the first build invocation failed because Git Bash stripped the `.\scripts\...` backslashes; re-ran with forward slashes — same script, same flags.)

## Verification Results

- Build exit 0; `[build_thesis] LOG SCAN: clean (no errors, no undefined refs/citations).`
- `main.log`: `Output written on main.pdf (95 pages` — page count unchanged.
- Pages 3/4 visually confirmed in correct binding order (推薦書 then 審定書), signed, unnumbered.
- Roman numbering still begins at 中文摘要 (p.5 = I).
- Root `審定書和推薦書.pdf` untouched (still untracked, `??` in git status, same size/mtime).
- `git check-ignore thesis/frontmatter/signed_forms.pdf` exits 1 (tracked without `-f`).

## Known Stubs

None — the two placeholder pages this task existed to remove are gone.

## Impact

Pre-binding revision item #3 ("unsigned 推薦書/審定書 front matter") is CLOSED. Remaining pre-binding items: ch07:541 calibration sentence, Exp3 "effectively identical keypoints" wording (MANDATORY), acknowledgments placeholder.

## Self-Check: PASSED

- FOUND: thesis/frontmatter/signed_forms.pdf (1,743,631 bytes)
- FOUND: thesis/frontmatter/recommendation.tex (includepdf pages=2)
- FOUND: thesis/frontmatter/approval.tex (includepdf pages=1)
- FOUND: thesis/preamble.tex (\usepackage{pdfpages})
- FOUND: commit fec05f5 on main
