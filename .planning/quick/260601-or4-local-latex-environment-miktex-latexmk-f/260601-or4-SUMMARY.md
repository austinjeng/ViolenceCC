---
phase: quick-260601-or4
plan: 01
status: complete
date: 2026-06-01
---

# Quick Task 260601-or4 — Local LaTeX Environment (MiKTeX + latexmk)

## Goal

Stand up a local LaTeX toolchain so the CGW '26 paper (`paper/main.tex`) compiles and
opens locally, removing the Overleaf round-trip from the editing loop.

## Outcome — DONE

`scripts/build_paper.ps1` compiles `paper/main.tex` to a **9-page** `paper/main.pdf`
(944 KB), BibTeX-resolved (`main.bbl` 13 KB, **zero** undefined-reference/citation
warnings, no fatal errors), opens it in the default viewer, and is idempotent
(second run = "up-to-date", exit 0). Git tree stays clean — all build artifacts ignored.

## What was installed / created

- **MiKTeX 25.12** (pdfTeX 4.23) — winget user-scope, `$env:LOCALAPPDATA\Programs\MiKTeX`.
- **Strawberry Perl** — `C:\Strawberry\perl\bin` (machine scope; `--scope user` had no
  applicable installer). Required because MiKTeX's `latexmk.exe` is a Perl script with
  no bundled interpreter.
- **latexmk 4.88** (ships with MiKTeX).
- `scripts/build_paper.ps1` — locates `latexmk`/`perl`/MiKTeX-bin by full-path probe and
  prepends them to the session PATH, runs `latexmk -pdf` in `paper/`, opens the PDF.
  `-Clean` switch runs `latexmk -C` first.
- `paper/.latexmkrc` — `$pdf_mode=1`, `$bibtex_use=2`, and `--enable-installer` on the
  pdflatex/bibtex commands.
- `.gitignore` — LaTeX artifact rules under `paper/` (pdf, aux, bbl, blg, out, fls,
  fdb_latexmk, toc, synctex.gz, cut).

## Non-obvious findings (the install was not turnkey)

1. **latexmk needs Perl on MiKTeX.** Fresh MiKTeX errors "could not find the script
   engine 'perl'". Fixed by installing Strawberry Perl (user confirmed, over the
   Perl-free pdflatex+bibtex alternative).
2. **Unrefreshed PATH.** A freshly-installed MiKTeX/Perl is not on PATH in an existing
   shell, and latexmk spawns `pdflatex`/`bibtex` by bare name. The script prepends BOTH
   the MiKTeX bin and the Perl bin to `$env:PATH` — no PATH-refresh dependency.
3. **`[MPM]AutoInstall=1` is not honored** by the engine during compilation (it still
   prompted on missing packages). The reliable fix is the MiKTeX engine flag
   **`--enable-installer`** in `.latexmkrc`, which auto-installs missing CTAN packages
   without prompting.
4. **Claude-tool sandbox blocks MiKTeX's SSL.** Inside Claude Code's tool sandbox,
   MiKTeX's libcurl failed with "SSL connect error" (winget downloads were unaffected).
   Package-DB sync and on-the-fly installs needed the sandbox disabled. **This only
   affects Claude running the build via tools — when Austin runs `build_paper.ps1` in a
   normal terminal there is no sandbox, so it just works.** All acmart dependencies are
   now installed on disk, so the user's first run needs no downloads.

## Usage

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1        # build + open
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_paper.ps1 -Clean # wipe artifacts, full rebuild
```

## Verification

| Check | Result |
|-------|--------|
| latexmk/pdflatex locatable + version | ✓ latexmk 4.88, pdfTeX 4.23 |
| `build_paper.ps1` builds `main.pdf` | ✓ 9 pages, 944 KB |
| BibTeX references resolved | ✓ `main.bbl` 13 KB, 0 undefined warnings |
| No fatal LaTeX errors | ✓ |
| PDF opens in default viewer | ✓ (Invoke-Item) |
| Idempotent re-run | ✓ "up-to-date", exit 0 |
| Clean git tree (artifacts ignored) | ✓ only script + .latexmkrc + .gitignore tracked |
