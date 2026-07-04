# latexmk config for the ViolenceCC master's thesis (thesis/main.tex)
# Read automatically when latexmk runs with thesis/ as the working directory.

# PDF via pdflatex (report class targets pdflatex).
$pdf_mode = 1;

# Always run bibtex for the \bibliography{references} directive
# (classic BibTeX + vendored IEEEtranN.bst). 2 = treat .bib as a dependency.
$bibtex_use = 2;

# nonstopmode so a single undefined-reference warning never blocks the build;
# synctex=1 enables editor<->PDF reverse search;
# --enable-installer forces MiKTeX to auto-install missing CTAN packages without
# prompting (the [MPM]AutoInstall config preference is not honored reliably).
$pdflatex = 'pdflatex -interaction=nonstopmode -synctex=1 --enable-installer %O %S';
$bibtex   = 'bibtex --enable-installer %O %S';

# Main document.
@default_files = ('main.tex');
