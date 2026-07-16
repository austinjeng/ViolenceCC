# Archived thesis appendices (A–F)

**Archived:** 2026-07-14 (quick task `260714-gd8`)
**Reason:** Author decision — the thesis main body stands alone as the submitted
document; the six appendices are preserved here retrievably in case they are
needed back. Their content is unchanged from when they were part of the build.

## What is here

These are the six appendix LaTeX sources, moved verbatim (via `git mv`, so their
full edit history is preserved) out of `thesis/appendices/` on the date above:

| File | Was Appendix | Content |
|------|--------------|---------|
| `appA_rtfm.tex` | A | RTFM XD-I3D reproduction investigation |
| `appB_per_category.tex` | B | Per-category / per-class complementarity tables |
| `appC_sweep.tex` | C | Hyperparameter-sweep full grids and heatmaps |
| `appD_engineering.tex` | D | Engineering notes (three-environment coexistence) |
| `appE_reproducibility.tex` | E | Reproducibility / reproduction walkthrough |
| `appF_figures.tex` | F | Additional figures |

When these were archived, every body cross-reference to them in
`thesis/chapters/` was reworded so the thesis PDF builds with zero broken
references and no pointers to absent material.

## Verbatim block removed from `thesis/main.tex`

The archiving commit deleted exactly this block from `main.tex` (it sat between
the `\bibliography{references}` line and `\end{document}`). Restore it verbatim
to bring the appendices back:

```latex
%%
%% Appendices
%%
\appendix
\include{appendices/appA_rtfm}
\include{appendices/appB_per_category}
\include{appendices/appC_sweep}
\include{appendices/appD_engineering}
\include{appendices/appE_reproducibility}
\include{appendices/appF_figures}
```

## Restore recipe

1. **Move the sources back** to the directory `main.tex` `\include`s from:
   ```sh
   git mv thesis/appendices_archived/appA_rtfm.tex           thesis/appendices/appA_rtfm.tex
   git mv thesis/appendices_archived/appB_per_category.tex   thesis/appendices/appB_per_category.tex
   git mv thesis/appendices_archived/appC_sweep.tex          thesis/appendices/appC_sweep.tex
   git mv thesis/appendices_archived/appD_engineering.tex    thesis/appendices/appD_engineering.tex
   git mv thesis/appendices_archived/appE_reproducibility.tex thesis/appendices/appE_reproducibility.tex
   git mv thesis/appendices_archived/appF_figures.tex        thesis/appendices/appF_figures.tex
   ```
2. **Re-insert the verbatim block above** into `thesis/main.tex`, between the
   `\bibliography{references}` line and `\end{document}` (replacing the two-line
   archive comment that now sits there).
3. **Restore the body cross-references** to the appendices from git history. The
   archive commit's parent is `484b84b`; recover the pre-archive chapter wordings
   with:
   ```sh
   git show 484b84b -- thesis/chapters/
   ```
   (or `git checkout 484b84b -- thesis/chapters/ch01_introduction.tex …` for the
   specific files) and re-apply the `\ref{app:*}` / `\ref{fig:appc-*}` pointers.
   Note: label `ch:08` no longer exists in the build (the standalone Limitations
   chapter was dissolved on 2026-07-16, quick `260716-n1r`); `appA_rtfm.tex:17`
   references it, so on restore retarget that `\ref{ch:08}` to `sec:lim-gaps`
   (or `sec:disc-limitations`).
4. **Rebuild:**
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean
   ```

## Note on the per-category tables

`thesis/tables/tab_percat_ucf.tex`, `tab_percat_xd.tex`, and `tab_percat_rtfm.tex`
were **left in place** under `thesis/tables/` — they are not moved. Only the
archived appendices `\input` them (archived `appA_rtfm.tex` inputs
`tab_percat_rtfm.tex`; archived `appB_per_category.tex` inputs
`tab_percat_ucf.tex` and `tab_percat_xd.tex`), so nothing in the current build
references these three table files. They are harmless where they are and are
ready for use the moment the appendices are restored.
