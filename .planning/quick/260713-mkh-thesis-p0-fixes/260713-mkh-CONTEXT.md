# Quick Task 260713-mkh: Thesis P0 fixes (review 2026-07-11) - Context

**Gathered:** 2026-07-13
**Status:** Ready for planning
**Design by:** Fable 5 (orchestrator). Execution: Opus 4.8 executor. All decisions below are LOCKED — the planner structures them into tasks, it does not revisit them.

<domain>
## Task Boundary

Execute the P0 fixes from `.planning/THESIS-REVIEW-2026-07-11.md` (§2 submission blockers S1–S4, §3 content blockers C1–C6), including the paper mirror fixes for C1/C4a, then rebuild both PDFs and re-verify NTUST compliance with PyMuPDF. MEDIUM/LOW findings are OUT of scope except the 5 overflowing tables + appE verbatim overflows (mandatory after the margin change narrows the text block to 15 cm).
</domain>

<decisions>
## Implementation Decisions (LOCKED)

### Execution environment
- **No worktree isolation.** The figure regeneration needs untracked data (`results/ucf_gated_fusion_s42/eval_scores.npz`, `data/annotations/ucf_temporal.txt`). Execute on the main tree, sequential, atomic commit per task.
- Thesis rebuild: `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_thesis.ps1 -Clean` (pdflatex via latexmk, MiKTeX auto-installs missing packages). Paper rebuild after paper edits: `.\scripts\build_paper.ps1 -Clean`. Never commit build artifacts.

### C1 — Figure 5.2 replacement (thesis + paper)
- Patch `scripts/generate_pub_figures.py::find_best_temporal_video()` to **require in-GT mean score > out-GT mean score** (positive alignment gap) as a hard filter before its existing scoring. Expected selection: **Fighting047** (gap +0.48, validated for the CGW talk). If the filter selects a different video, verify its gap is positive and its curve is visually sensible before accepting; otherwise parameterize the function to take an explicit video id and use Fighting047.
- Regenerate `fig_temporal_scores.pdf`; place the SAME file at `paper/figures/fig_temporal_scores.pdf` and `thesis/figures/fig_temporal_scores.pdf`.
- Rewrite thesis ch05 caption (`ch05_results_fusion.tex:386-392`) and §5.7 prose (`:396-402`) for the new video: describe what the curve actually shows (verify by rendering the new figure); do NOT reuse "representative" unless it is (Fighting is a strong category — call it a well-localized example, not representative of hard categories).
- Mirror in `paper/main.tex` (Figure 2 caption + its referencing prose).
- Update `thesis/PROVENANCE.md:90` (figure provenance row: new video id, generation command, date).
- Check `thesis/appendices/appF_figures.tex:80-81` ("Chapter 5 shows one temporal score curve; Figures F.2 and F.3 add three more") still reads correctly; adjust the sentence if it named the video or its category.

### C2 — Bibliography + skeleton-VAD literature
- `thesis/references.bib:122` PYSKL: author = {Haodong Duan and Jiaqi Wang and Kai Chen and Dahua Lin}. Grep `paper/references.bib` for the same corrupted entry and fix there too if present.
- Add three bib entries (thesis references.bib; also to the paper ONLY if the paper prose is edited to cite them — it is not, so thesis only):
  - `morais2019skeleton`: R. Morais, V. Le, T. Tran, B. Saha, M. Mansour, S. Venkatesh, "Learning Regularity in Skeleton Trajectories for Anomaly Detection in Videos," CVPR 2019, pp. 11996–12004.
  - `markovitz2020gepc`: A. Markovitz, G. Sharir, I. Friedman, L. Zelnik-Manor, S. Avidan, "Graph Embedded Pose Clustering for Anomaly Detection," CVPR 2020, pp. 10539–10547.
  - `hirschorn2023stgnf`: O. Hirschorn, S. Avidan, "Normalizing Flows for Human Pose Anomaly Detection," ICCV 2023, pp. 13545–13554.
- Rewrite the skeleton-VAD prose around these three: `ch01_introduction.tex:56-57` (motivation sentence) + the Gap 1 sentence (~:115), and `ch02_related_work.tex:219-230` (the skeleton-VAD paragraph — describe the pose-trajectory line accurately: reconstruction/regularity (Morais), pose-graph clustering (Markovitz), normalizing flows (Hirschorn); keep the thesis's contrast: those are unsupervised single-modality skeleton methods, this thesis uses skeletons as one stream in weakly-supervised fusion).
- `doshi2022skeleton`: after the rewrite, if it is no longer cited anywhere, DELETE the bib entry and update the coverage comment at `thesis/main.tex:52-53` (bib-key count changes from 42). If a citation remains, fix the entry: year 2020, CVPRW 2020, drop the wrong 2022 DOI, add `note={arXiv:2004.02072}`, and make the citing sentence describe it as any-shot sequential anomaly detection (not pose).
- After all bib edits, re-verify N/N cite coverage (grep all \cite keys vs bib keys) and update the main.tex comment.

### C3 — CGW '26 self-citation + thesis delta
- Add bib entry `jeng2026dualmodal`: Wei-Han Jeng and Chuan-Kai Yang, "Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection: A Multi-Backbone Study," in Proceedings of the Computer Graphics Workshop (CGW), Taiwan, 2026.
- At `ch01_introduction.tex:171`: cite it, and append 2–3 sentences enumerating the thesis-only delta: (a) full three-seed ablation grid across six fusion variants and four backbones (Tables 5.1–5.2) vs the paper's condensed tables; (b) per-category and failure analysis (§5.7–5.9, Appendix B) and the RTFM reproduction study (Appendix A); (c) the complete TTA investigation narrative — six-strategy search, CORAL/NORM eliminations, episodic-inertness diagnosis (§6.2–6.3); (d) engineering/reproducibility documentation (Appendices D–E). Fix the dangling "disclosed in the paper" at `ch05:239` to cite the entry.

### C4 — Five claim corrections (exact targets)
1. `ch05_results_fusion.tex:98-101`: replace the "three of the four … lone exception being SigLIP2 Base" sentence with the correct, stronger claim: gated fusion beats late fusion on **every backbone on both datasets** (UCF deltas +2.5/+1.8/+2.2/+2.6; XD +12.6/+10.9/+13.0/+11.1). Mirror the identical stale sentence in `paper/main.tex` (grep for "lone exception"). This also dissolves the ch07 §7.3 inconsistency — check `ch07_discussion.tex:97-` wording still consistent (it becomes correct once ch05 is fixed).
2. `ch06_results_tta.tex:329` and `:303-304` (Fig 6.3 caption): replace "the single most-degraded condition in the benchmark" with the paper's accurate qualifier: "the condition that most collapses the visual-language stream" (Gaussian severity 5; JPEG cells are lower in absolute AUC but there the skeleton cache is also degraded). Also fix `ch09_conclusion.tex` "single most visually-degrading condition" → same canonical phrase. Update PROVENANCE.md canonical-label row if one exists.
3. `ch06_results_tta.tex:41-42` (Fig 6.1 caption): replace the "Degradation deepens monotonically with severity in every family" sentence with wording the plotted data supports, e.g. "Degradation generally deepens with severity; exceptions (e.g., SigLIP2 Base's Gaussian column, where AUC rises with severity due to score compression) are analyzed in §6.4.2."
4. `ch08_limitations.tex:47`: delete "(75.41\%)" from the XD-AP sentence (keep the Sultani comparison qualitative there; 75.41 stays only in the UCF sentence where it is correct).
5. `appC_sweep.tex:44-48, :62, :97-98`: reword — XD baseline reproduced exactly (0.7192); UCF reproduced to within 0.02 pp (82.26 vs historical 82.27). Fig C.1 caption parenthetical → 82.26 (matches the cell annotation); Table C.1 caption → label 0.8227 as the historical sweep-era value.

### C5 — ch08 score-calibration limitation
- Add a short limitation subsection/paragraph in `ch08_limitations.tex` (fits after the §8.1 accuracy discussion or as its own §): rank-based metrics (AUC/AP) mask a heavily right-skewed normal-score distribution (75th percentile of normal-frame scores ≈ 0.986, ch05 §5.8); any fixed-threshold deployment faces severe sustained false alarms; calibration of the MIL head (e.g., post-hoc calibration or threshold-free alarm policies) is future work. Reference back to §5.8 so the ch05:566 forward promise resolves. Keep to the thesis's honest register; no new numbers beyond ch05 §5.8's existing ones.

### C6 — ch07 logic reframe
- `ch07_discussion.tex:35-44`: rewrite the "strongest single piece of evidence" paragraph. New logic: the 12.6-pt gated-vs-late gap on XD CLIP primarily shows the gate avoids noise-dragging — most of it (63.9→74.6) is recovery to the visual-only level, achievable by suppressing an uninformative stream; the evidence for genuinely extracted skeleton signal is (a) the +1.9-pt gated-vs-visual-only margin, (b) the 8/8 meet-or-exceed consistency (sign test, §5.3), (c) category-structured gate activations (Fig 5.x refs unchanged). Do not call any single number "the strongest evidence"; present the triangulation.

### S3 — Geometry / font / heading batch (preamble.tex, titlepage.tex, main.tex)
- `geometry`: `top=3cm,bottom=2cm,left=3cm,right=3cm` (replaces `margin=2.5cm`).
- Fonts: replace `lmodern` with `newtxtext` + `newtxmath` (Times-compatible for pdflatex). REMOVE `amssymb` (newtxmath supplies AMS symbols; keep `amsmath` loaded BEFORE newtxmath). Keep `[T1]{fontenc}` and `microtype`. If newtxmath produces symbol clashes at build, fallback: `mathptmx` + keep amssymb — but try newtx first and check the build log for errors.
- CJK: add `\usepackage{CJKutf8}` (MiKTeX auto-installs cjk + arphic fonts). Chinese blocks use `\begin{CJK}{UTF8}{bkai}` (標楷體-like); if `bkai` font maps fail on MiKTeX, use `bsmi` and note it.
- `titlesec`: chapters centered bold 20pt, sections left bold 18pt:
  `\titleformat{\chapter}[display]{\centering\bfseries\fontsize{20}{24}\selectfont}{\chaptertitlename\ \thechapter}{12pt}{}`
  `\titlespacing*{\chapter}{0pt}{0pt}{30pt}` (the 30pt post-gap satisfies the two-blank-lines rule for Abstract-level headings)
  `\titleformat{\section}{\bfseries\fontsize{18}{22}\selectfont}{\thesection}{1em}{}`
  Leave subsection at class default. Starred chapters inherit the centered format automatically.
- Front matter page numbers: `\pagenumbering{Roman}` (uppercase; starts at the Chinese abstract, see S1 ordering). Body unchanged (`arabic`).
- Title page (`titlepage.tex`): title at `\fontsize{24}{29}\selectfont\bfseries`; add department line "Department of Computer Science and Information Engineering" under the university; degree line → "Master of Science in Computer Science and Information Engineering"; date line → "June 2026". Keep it a clean English 書名頁.

### S1/S2 — Front matter files + ordering (main.tex)
New/changed frontmatter files (all in `thesis/frontmatter/`):
1. `cover.tex` (NEW, first page, unnumbered, bilingual per NTUST 附錄一):
   - 國立臺灣科技大學資訊工程系 / 碩士論文 (CJK bkai, ~18pt)
   - Department of Computer Science and Information Engineering / National Taiwan University of Science and Technology / Master Thesis
   - Chinese title: 基於骨架與視覺雙模態融合之弱監督暴力偵測：多骨幹網路研究 (marked `% TODO-CONFIRM (Austin): Chinese title wording`)
   - English title (24pt bold)
   - 研究生：鄭○○（% TODO-CONFIRM: Chinese given name of Wei-Han Jeng — placeholder MUST be replaced before printing）/ Wei-Han Jeng
   - 指導教授：楊傳凱 博士（% TODO-CONFIRM）/ Advisor: Chuan-Kai Yang, Ph.D.
   - 中華民國一一五年六月 / June 2026 (% TODO-CONFIRM graduation month; July/Aug leavers print June per NTUST rule)
2. `spine.txt` (NEW, not compiled — print-shop text): 國立臺灣科技大學 資訊工程系 碩士論文｜論文題目（中文）｜鄭○○｜115. Plus the same in English underneath as reference.
3. `recommendation.tex` (NEW, unnumbered placeholder page): centered 指導教授推薦書 heading + centered gray note "（此頁由正式簽署之推薦書替換 — replace with the signed advisor recommendation form before binding）".
4. `approval.tex` (NEW, unnumbered placeholder page): same pattern for 學位考試委員審定書.
5. `abstract_zh.tex` (NEW): inside `\begin{CJK}{UTF8}{bkai}`, `\chapter*{摘要}` + `\addcontentsline{toc}{chapter}{摘要}`, body text EXACTLY:

  弱監督影片異常偵測僅以影片層級標籤定位異常事件，然而現有方法多仰賴單一視覺模態，且假設部署環境固定不變。本論文提出一套雙模態融合框架，結合凍結 CTR-GCN 編碼器之骨架動態特徵與凍結視覺語言骨幹網路之視覺特徵，以多實例學習排序損失訓練，僅學習輕量之融合頭。研究涵蓋四種視覺骨幹網路（CLIP ViT-B/16、SigLIP2 ViT-B/16、SigLIP2 SO400M、SigLIP2 Giant），於 UCF-Crime 與 XD-Violence 基準資料集上進行評估。

  閘控融合以學習式模態加權於 UCF-Crime 達到 82.5\% 幀級 AUC（SigLIP2 Giant），於 XD-Violence 達到 78.7\% AP（SigLIP2 SO400M），皆為三種子平均。骨架特徵帶來小而一致的互補增益：閘控融合於全部八組骨幹—資料集設定中皆不低於純視覺基線，其中六組嚴格優於基線。上述結果落後於領域中經微調與文字對齊之領先方法（約 88--91\% UCF-Crime AUC），此差距源於本論文刻意採用之凍結、無文字分支設計。本論文之貢獻為可重現之單 GPU 雙模態流程與免標籤之強健性研究，而非新的最高分數。

  本論文另探討測試時期自適應（TTA）：於 20 種合成劣化條件、三種子下，以熵最小化為基礎之 TENT 與 SAR 受架構限制僅能調整融合頭之 LayerNorm 參數，AUC 變化均小於 0.1 個百分點，為論文中深入分析之結構性零結果。所提出之免標籤、免調參的判別可靠度重加權方法，於視覺語言串流之判別訊號崩潰時，將閘控融合導向對劣化更穩健之骨架串流：於全部四種骨幹之劣化輸入 AUC 均有提升（平均 +1.2 點，於單一視覺串流崩潰最嚴重之條件最高 +13.2 點），採轉導式協定且不宣稱於乾淨資料上有增益。

   關鍵字：影片異常偵測、弱監督學習、多模態融合、骨架動作表徵、視覺語言模型、測試時期自適應
   (% TODO-CONFIRM (Austin): review zh-TW abstract wording — drafted by Claude, byte-consistent numbers with the English abstract)
6. `abstract.tex` (EDIT): append after the last paragraph:
   `\vspace{1.5em}\noindent\textbf{Keywords:} video anomaly detection; weakly supervised learning; multimodal fusion; skeleton-based action representation; vision--language models; test-time adaptation` (6 keywords, matching the Chinese set).

`main.tex` frontmatter order becomes:
`cover` → `titlepage` → `recommendation` → `approval` → `\pagenumbering{Roman}` → `abstract_zh` → `abstract` → `acknowledgments` → `\tableofcontents` → `notation` → `\listoffigures` → `\listoftables` → body. (Cover through approval carry no page numbers: `\thispagestyle{empty}` / titlepage env.)

Backmatter order: bibliography BEFORE `\appendix`:
```
\clearpage
\phantomsection
\renewcommand{\bibname}{References}
\addcontentsline{toc}{chapter}{References}
\bibliographystyle{IEEEtranN}
\bibliography{references}
\appendix
\include{...}
```
(Verify appendix \cite keys still resolve — BibTeX collects cites from the whole document regardless of placement; confirm no `?` citations in the rebuilt PDF.)

### Table/verbatim overflow fixes (mandatory at the new 15 cm text width)
- Tables 4.1, 4.2 (ch04), 5.1, 5.2 (ch05), D.1 (appD): shrink to fit — first try `\small` or `\footnotesize` + `\setlength{\tabcolsep}{3.5pt}` inside the table env; if still overwide, wrap the tabular in `\resizebox{\textwidth}{!}{...}`. Keep booktabs style.
- `appE_reproducibility.tex:104-106` (and any other overflowing verbatim/texttt lines found in the post-build scan): re-break long \texttt paths/command lines manually so nothing crosses the right margin (the clipped-semicolon run-on on current p.114 must be gone).

### Verification gate (executor MUST run before the final commit)
1. `build_thesis.ps1 -Clean` exits 0; `main.log` has no missing-font/package errors; no `??` and no `[?]` citations in the PDF text.
2. PyMuPDF re-scan asserting: page size A4; text-block margins ≈ 3/2/3/3 cm (±0.15 cm; footer page number may sit in the bottom 2 cm band); body font family reports Times/Termes/NimbusRoman (not LMRoman); every `Chapter N` heading line's bbox is horizontally centered (center within ±10 pt of page center) and its span size ≈ 20 pt; section headings ≈ 18 pt; front-matter footers show I, II, III (uppercase); Chinese abstract page exists before the English abstract; References section starts before Appendix A; title-page title spans ≈ 24 pt.
3. Overflow scan: no text/table span with x1 > right-margin boundary (+2 pt tolerance) on any page.
4. Figure check: render the Figure 5.2 page to PNG, confirm the gated-fusion curve is high inside the shaded GT window for the new video; caption names the new video.
5. Paper: `build_paper.ps1 -Clean` exits 0 after paper edits.
6. Cite coverage N/N re-verified; `main.tex` comment updated.

### Commit plan (atomic, on main)
1. `fix(quick-260713-mkh): C1 — replace Figure 5.2 erratum video with Fighting047 (thesis+paper)` — script patch, both figure PDFs, ch05 caption/prose, paper caption/prose, PROVENANCE row, appF cross-ref.
2. `fix(quick-260713-mkh): C2-C6 — bib corrections, skeleton-VAD literature, CGW self-cite, claim fixes` — all remaining content edits (thesis chapters + references.bib + paper "lone exception" mirror).
3. `feat(quick-260713-mkh): NTUST format compliance batch (S1-S4)` — preamble, main.tex reorder, new frontmatter files, titlepage, table/verbatim overflow fixes.
4. Docs commit handled by orchestrator (PLAN/SUMMARY/STATE).
Build artifacts (main.pdf, .aux etc.) are git-ignored — never commit them (paper/ AND thesis/).

### Claude's Discretion
- Exact prose phrasing within the locked semantic constraints above.
- Table-shrink technique per table (font-size vs resizebox), judged by rendered result.
- Minor LaTeX plumbing (hyperref bookmark warnings for CJK: wrap CJK headings with `\texorpdfstring` or accept the warning — do not let bookmarks break the build; `bookmarksnumbered` already set).
</decisions>

<specifics>
## Specific Ideas

- Figure alignment numbers for validation: Fighting047 gated in-GT-minus-normal gap +0.48 (CLIP +0.15, skeleton −0.01), from `.planning/quick/260707-n9l-build-cgw-2026-talk-deck-traditional-chi/260707-n9l-SUMMARY.md`.
- RoadAccidents127 GT interval 2160–2300 (`data/annotations/ucf_temporal.txt:227`) — the OLD video; do not reuse.
- The review report `.planning/THESIS-REVIEW-2026-07-11.md` §2/§3 has full evidence per finding; the executor should read it.
</specifics>

<canonical_refs>
## Canonical References

- `.planning/THESIS-REVIEW-2026-07-11.md` — findings being fixed (P0 scope only)
- `thesis/thesis_requirements.pdf` — NTUST rules (text extract mirrored in the review §1 matrix)
- `thesis/PROVENANCE.md` — number provenance; update figure row after C1
- `CLAUDE.md` — paper rebuild rule (`build_paper.ps1 -Clean` after paper edits; never commit build artifacts)
</canonical_refs>
