# 13-SOTA-EVIDENCE — Primary-Source SOTA Verification Gate (Plan 13-11)

**Date:** 2026-07-05
**Scope:** All 17 worklist items from 13-RESEARCH.md §5 (= the 13 fragment `% RE-VERIFY` rows + omission/attribution items + the 17-item camera-ready checklist from 12-VERIFICATION.md, deduplicated) + the 15 GATE-13-marked bib entries in `thesis/references.bib` + the four `and others` author-list expansions.
**Method:** Primary sources only — each verdict is backed by a fetch of the paper's own arXiv abs/HTML/ar5iv page, CVF Open Access record, AAAI OJS PDF, ACM/journal record, or conference proceedings page. Aggregators (paperswithcode, blogs, other papers' comparison tables) were used only as locators, never as evidence. Failed fetch attempts are recorded in NOTES.
**Consumer:** Plan 13-12 (Wave-3 merge) applies these verdicts to `thesis/` AFTER user spot-approval. This plan edits no thesis file.

**Verdict semantics:**
- `VERIFIED` — cell/field ships as-is (RE-VERIFY comment removed by 13-12).
- `CORRECTED -> value` — 13-12 replaces the field with the recorded value.
- `UNVERIFIABLE` — result cell is OMITTED (`---`/N-A) with the drafted omission footnote.

---

## Summary verdict table

### Worklist items (13-RESEARCH.md §5 / 12-VERIFICATION.md #1–#17)

| # | Item | Claimed (UCF / XD) | Verdict | Action for 13-12 |
|---|------|--------------------|---------|------------------|
| 1 | CLIP-TSA | 87.58 / 82.19 | VERIFIED | Keep both; fix footnote $^f$ text: 94.02 is NOT in the paper at all (see item 1 NOTES) |
| 2 | MGFN | 86.98 / 79.19 | VERIFIED | Keep I3D-RGB pair; remove RE-VERIFY comments |
| 3 | GS-MoE | 91.58 / 82.89 | VERIFIED (numbers); CORRECTED (venue) | Venue -> ICCV 2025 proceedings (drop "(arXiv)"); bib retype `@misc` -> `@inproceedings`; author list added (order caveat — user spot-check) |
| 4 | Holmes-VAD | 89.51 / 90.67 | VERIFIED | Keep with preprint + LoRA-MLLM disclosure (already footnoted) |
| 5 | Holmes-VAU | 88.96 / 87.68 | VERIFIED (with confirmed video-level caveat) | Keep only with VIDEO-level disclosure (already footnoted); may add "398-sample split" detail |
| 6 | PiercingEye | 86.64 / 88.82 | VERIFIED (numbers); CORRECTED (venue) | 88.82 LOW-conf flag CLEARED (verbatim Table I, multimodal); venue -> arXiv preprint "submitted to TPAMI", NOT TPAMI'26; bib retype `@article` -> `@misc`; full authors + full title recorded |
| 7 | AnomalyCLIP | 86.36 / 78.51 | VERIFIED | LOW-conf flag cleared (Table 2/3 detection rows); bib gains arXiv:2310.02835 + CVIU vol/article/DOI |
| 8 | FDPN | 88.03 / N-A | VERIFIED (number + XD absence); CORRECTED (bib title + authors) | Keep row with self-report footnote; bib title -> "...Egocentric 360-Degree Camera"; full authors + pages added |
| 9 | TEVAD | 84.9 / 79.8 | VERIFIED | Keep (one-decimal precision is the paper's own); remove RE-VERIFY |
| 10 | Sultani XD cell | 75.41 / `---` | VERIFIED (omission correct) | XD cell stays `---`; 73.20 is Wu et al. ECCV'20 re-impl (footnote $^l$ stands) |
| 11 | RTFM | 84.30 / 77.81 | VERIFIED | Canonical I3D pair confirmed |
| 12 | EventVAD | 82.03 / 64.04 | VERIFIED | 64.04 is AP; 87.51 is ROC-AUC (never AP); A800-80GB confirmed; full 14-author list recorded |
| 12b | LAVAD | 80.28 / 62.01 | VERIFIED | 62.01 is AP; 85.36 is ROC-AUC (never AP) |
| 13 | HyperVD | N-A / 85.67 | (pending batch 5 — do not merge) | — |
| 13b | Ghadiya et al. | N-A / 86.34 | (pending batch 5 — do not merge) | — |
| 14 | STPrompt & FDPN XD cells | N/A cells | VERIFIED | Neither paper evaluates XD-Violence; N/A cells + footnotes d/e stand |
| 15 | Light-WVAD attribution | 84.7 / `---` | (pending batch 5 — do not merge) | — |
| 16 | PI-VAD & DSANet bib status | — | (pending batch 5 — do not merge) | — |
| 17 | PI-VAD & DSANet author lists | — | (pending batch 5 — do not merge) | — |

### GATE-13 bib entries (15)

| Bib key | Verdict | Correction (if any) |
|---------|---------|---------------------|
| zhang2024holmesvad | VERIFIED | none — `@misc` + eprint correct (arXiv-only confirmed); authors exact match |
| zhang2025holmesvau | VERIFIED | none — CVPR 2025 confirmed; authors exact match |
| wu2024stprompt | VERIFIED | none — ACM MM 2024 confirmed ("Accepted by ACMMM2024") |
| song2025fdpn | CORRECTED | title -> "Anomaly Detection for People with Visual Impairments Using an Egocentric 360-Degree Camera"; authors -> Inpyo Song, Sanghyeon Lee, Minjun Joo, Jangwon Lee; add pages 2828–2837 |
| yang2024tpwng | VERIFIED | none — CVPR 2024 confirmed ("Accepted to CVPR2024") |
| pu2024pel4vad | CORRECTED | author 3 -> "Lulu Yang" (not "Lu Yang"); optional TIP coordinates: vol. 33, pp. 4923–4936, DOI 10.1109/TIP.2024.3451935 (search-record-backed — see NOTES) |
| leng2026piercingeye | CORRECTED | NOT published in TPAMI — "Submitted to IEEE TPAMI" only; retype `@misc` arXiv preprint, year 2025; full author names + full title recorded |
| zanella2024anomalyclip | VERIFIED (+fields added) | add eprint 2310.02835, volume 249, article 104163, DOI 10.1016/j.cviu.2024.104163 |
| chen2023tevad | VERIFIED | none — CVPRW 2023 (O-DRUM) + authors confirmed |
| peng2024hypervd | (pending batch 5) | — |
| ghadiya2024crossmodal | (pending batch 5) | — |
| yan2018stgcn | VERIFIED | none ("Accepted by AAAI 2018") |
| hendrycks2019imagenetc | VERIFIED | none ("ICLR 2019 camera-ready") |
| sun2016coral | VERIFIED | none ("Full paper to appear in AAAI-16") |
| schneider2020norm | VERIFIED | none ("Thirty-fourth Conference on Neural Information Processing Systems" = NeurIPS 2020) |

---

## Part A — Worklist items 1–9 (Task 1)

### Item 1 — CLIP-TSA

- **CLAIM:** UCF-Crime frame-level ROC-AUC = 87.58; XD-Violence = 82.19 as the paper's own AUC@PR number (VadCLIP's table shows 82.17 drift; "94.02" must never be attributed).
- **PRIMARY SOURCE URL:** https://ar5iv.labs.arxiv.org/html/2212.05136 (Joo, Vo, Yamazaki & Le, IEEE ICIP 2023, arXiv:2212.05136). Failed attempts recorded: `arxiv.org/html/2212.05136v3` mis-rendered to the ICIP author-guidelines template; `/abs` page omits tables.
- **QUOTE:** UCF: "CLIP-TSA achieving 87.58 AUC@ROC on UCF-Crime, as shown in Table 2". XD: Table 3 "Comparisons on XD-Violence Dataset", metric column header "AUC@PR ↑", final row verbatim: "Ours: CLIP-TSA | CLIP(V) | 82.19".
- **VERDICT:** VERIFIED (UCF 87.58 AUC-ROC; XD 82.19 AUC@PR).
- **NOTES:** (a) The 94.02 trap resolves more strongly than expected: **94.02 appears NOWHERE in the CLIP-TSA paper** (every Table 3 row dumped; full text searched twice; the paper's highest number anywhere is 98.32 ShanghaiTech AUC-ROC). The current thesis footnote $^f$ says "the paper's own 94.02 uses a non-comparable protocol" — that wording wrongly implies 94.02 IS in the paper. 13-12 must reword footnote $^f$ to: the 94.02 figure circulating on leaderboards does not appear in the CLIP-TSA paper at all; the paper's only XD number is 82.19 AUC@PR. (b) AUC@PR = area under the precision–recall curve = what other XD papers call AP, so 82.19 is directly comparable to the AP column; keep the metric-name footnote. (c) VadCLIP's 82.17 is a 0.02 secondary-table drift; the primary 82.19 stands.

### Item 2 — MGFN

- **CLAIM:** UCF-Crime AUC = 86.98 (I3D-RGB); XD-Violence AP = 79.19 (I3D-RGB; NOT 80.11, which is VideoSwin).
- **PRIMARY SOURCE URL:** https://ar5iv.labs.arxiv.org/html/2211.15098 (Chen, Liu, Zhang, Fok, Qi & Wu, AAAI 2023, arXiv:2211.15098). Failed attempt recorded: `arxiv.org/html/2211.15098` returned HTTP 404.
- **QUOTE:** UCF-Crime table: "MGFN(Ours) | I3D-RGB | ✓ | 86.98" and separately "MGFN(Ours) | VideoSwin-RGB | ✓ | 86.67". XD-Violence AP table: "MGFN(Ours) | I3D-RGB | ✓ | 79.19" and separately "MGFN(Ours) | VideoSwin-RGB | ✓ | 80.11".
- **VERDICT:** VERIFIED — both cited numbers are the I3D-RGB rows; the pairing (86.98 UCF + 79.19 XD, both I3D-RGB) is internally consistent.
- **NOTES:** 80.11 belongs to VideoSwin-RGB, exactly as the thesis footnote $^g$ states. Keep the single-backbone (I3D-RGB) row; remove the RE-VERIFY comments in ch07/ch08.

### Item 3 — GS-MoE

- **CLAIM:** UCF-Crime AUC = 91.58; XD-Violence AP = 82.89; table venue currently "ICCV'25 (arXiv)"; bib `damicantonio2025gsmoe` is `@misc` with `and others`.
- **PRIMARY SOURCE URL:** https://arxiv.org/html/2508.06318 (numbers) + https://iccv.thecvf.com/virtual/2025/poster/2527 (venue). CVF camera-ready HTML returned HTTP 403 to the fetcher, but the CVF supplemental exists: https://openaccess.thecvf.com/content/ICCV2025/supplemental/Amicantonio_Mixture_of_Experts_ICCV_2025_supplemental.pdf — confirming ICCV 2025 proceedings inclusion.
- **QUOTE:** UCF: "On the challenging UCF-Crime dataset, GS-MoE achieves an AUC of 91.58%, surpassing the previous best model". XD: "On the XD-Violence dataset, GS-MoE achieves an AP score of 82.89%, which is competitive with the best-performing TSA". Venue (ICCV virtual page): "Accepted as ICCV 2025 Poster (Poster Exhibit Hall I #25) with Highlight Award".
- **VERDICT:** VERIFIED (91.58 / 82.89); CORRECTED (venue) -> genuine ICCV 2025 acceptance: table venue cell becomes "ICCV'25" (drop "(arXiv)"), bib retyped `@inproceedings` with booktitle "Proceedings of the IEEE/CVF International Conference on Computer Vision ({ICCV})", year 2025.
- **NOTES:** **Full author list (arXiv abs order, BibTeX-ready):** `Giacomo D'Amicantonio and Snehashis Majhi and Quan Kong and Lorenzo Garattoni and Gianpiero Francesca and François Brémond and Egor Bondarev`. **Author-order caveat (USER SPOT-CHECK):** arXiv lists ...Francesca, Brémond, Bondarev; the ICCV 2025 virtual page lists ...Francesca, Bondarev, Brémond (Brémond last — likelier canonical since Brémond is the PI). CVF camera-ready 403'd the fetcher, so the final order could not be byte-confirmed. 13-12 should adopt one order (recommend the ICCV page order: `... and Egor Bondarev and François Brémond`) and note the source.

### Item 4 — Holmes-VAD

- **CLAIM:** UCF AUC = 89.51; XD AP = 90.67; arXiv preprint with no peer-reviewed venue; LoRA-fine-tunes an MLLM (not frozen-feature).
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2406.12235 + https://arxiv.org/html/2406.12235v2 (Zhang et al., arXiv:2406.12235v2).
- **QUOTE:** Table 1 row: "Holmes-VAD (Ours) | ViT | Instruction-Tuned | ✓ | 90.67 | 89.51" under caption "Table 1: Comparision with state-of-the-art Video Anomaly Detection approches." (columns: XD-Violence AP = 90.67, UCF-Crime AUC = 89.51). Training: "we train the projector and use LoRA to fine-tune the Multi-modal LLM"; "We utilize Vicuna as our LLM". Status: Comments field = "19 pages, 9 figures"; no journal-ref/venue/DOI beyond arXiv ([v1] 18 Jun 2024, [v2] 29 Jun 2024).
- **VERDICT:** VERIFIED — numbers, arXiv-only status, and LoRA-MLLM characterization all confirmed verbatim.
- **NOTES:** Bib author list is an EXACT match (9 authors). Row ships with the existing footnote $^b$ (preprint + LoRA-tuned, not frozen-feature); remove RE-VERIFY comment.

### Item 5 — Holmes-VAU

- **CLAIM:** UCF AUC = 88.96; XD AP = 87.68; numbers suspected VIDEO-LEVEL on a 398-sample split; CVPR 2025.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2412.06171 + https://arxiv.org/html/2412.06171v2 (Zhang et al., CVPR 2025 camera-ready, arXiv:2412.06171v2).
- **QUOTE:** Numbers: Table 1 ("Comparison of detection performance with state-of-the-art Video Anomaly Detection approaches...") reports Holmes-VAU XD-Violence AP = 87.68% and UCF-Crime AUC = 88.96%. Protocol (Sec. 5.1): "Following [14, 46, 74, 67], we use AUC and AP to quantify detection performance, which is evaluated only on the video level." Granularity: "The test set contains 2200/732/398 samples at clip/event/video levels." Status: abs page "Accepted by CVPR2025".
- **VERDICT:** VERIFIED — numbers, CVPR 2025, and the video-level caveat are all confirmed; the verbatim protocol sentence "evaluated only on the video level" settles it.
- **NOTES:** The thesis already tabulates this row with the bold "\emph{VIDEO-level}" Setting label and footnote $^c$ — that disclosure is mandatory and stands. 13-12 may append "(video-level tier = 398 samples)" to footnote $^c$ for precision. Bib author list EXACT match (correctly differs from Holmes-VAD's list). Remove RE-VERIFY comment.

### Item 6 — PiercingEye

- **CLAIM:** UCF AUC = 86.64 (visual-only); XD AP = 88.82 (LOW confidence, audio+visual+text); venue cited as IEEE TPAMI'26.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2504.18866 + https://ar5iv.labs.arxiv.org/html/2504.18866 (Leng et al., arXiv:2504.18866).
- **QUOTE:** UCF (Table II, caption "Comparisons of frame-level AUC performance on UCF-Crime dataset under unimodal input setting."): "PiercingEye | - | Uni | E & H | 86.64". XD (Table I, caption "Comparison of frame-level AP performance on the XD-Violence dataset under unimodal and multimodal input settings."): "PiercingEye | - | Multi | E & H | 88.82" — the value appears verbatim. Status: abs page "Submitted to IEEE Transactions on Pattern Analysis and Machine Intelligence" ([v1] 26 Apr 2025; only the arXiv DOI exists).
- **VERDICT:** VERIFIED (numbers — the 88.82 LOW-confidence flag is CLEARED, it reads directly off Table I as multimodal frame-level AP); CORRECTED (publication status) -> the paper is only SUBMITTED to TPAMI, not accepted/published. Table venue cell must change from "IEEE TPAMI'26" to "arXiv'25 (subm. TPAMI)" (or equivalent), year 2026 -> 2025; bib `leng2026piercingeye` retyped from `@article` (TPAMI 2026) to `@misc` arXiv preprint, year 2025.
- **NOTES:** Full title is "PiercingEye: Dual-Space Video Violence Detection with Hyperbolic Vision-Language Guidance" (bib title is currently truncated — extend). **Full author list (BibTeX-ready):** `Jiaxu Leng and Zhanjie Wu and Mingpi Tan and Mengjingcheng Mo and Jiankang Zheng and Qingqing Li and Ji Gan and Xinbo Gao` (surname order matches the current bib exactly; just expand to full names). Modality labels in the Setting column (audio+text for XD; UCF visual-only) confirmed correct.

### Item 7 — AnomalyCLIP

- **CLAIM:** UCF detection AUC = 86.36; XD detection AP = 78.51 (LOW confidence); the ~90.3 leaderboard figure is recognition mAUC (different task).
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2310.02835 + https://ar5iv.labs.arxiv.org/html/2310.02835 (Zanella, Liberatori, Menapace, Poiesi, Wang & Ricci, CVIU 2024; ScienceDirect record pii S1077314224002443).
- **QUOTE:** Table 2 (UCF-Crime, VAD/detection task): AnomalyCLIP AUC = 86.36. Table 3 (XD-Violence, VAD/detection task): AnomalyCLIP AP = 78.51. The ~90 figure (90.66% UCF) is the recognition mean-AUC of the VAR (video anomaly recognition) task — a different task, never citable as detection AUC.
- **VERDICT:** VERIFIED — LOW-confidence flag cleared; detection-task numbers confirmed from the paper's own Tables 2/3.
- **NOTES:** Bib enrichment for 13-12: eprint 2310.02835; CVIU vol. 249 (2024), article 104163, DOI 10.1016/j.cviu.2024.104163. Footnote $^i$ (mAUC trap) stands; remove RE-VERIFY comment.

### Item 8 — FDPN

- **CLAIM:** UCF AUC = 88.03 (I3D; the paper's OWN method, +0.01 self-report over VadCLIP); XD not evaluated; row flagged "re-check primary or drop".
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2411.10945 + CVF WACV 2025 Open Access record (Song, Lee, Joo & Lee, WACV 2025, arXiv:2411.10945).
- **QUOTE:** Table 3: "FDPN (Ours), I3D — 88.03" (sits directly above VadCLIP's 88.02). XD-Violence appears only as dataset statistics in Table 1 — no XD evaluation. FDPN = "Frame and Direction Prediction Network".
- **VERDICT:** VERIFIED (88.03 + XD absence + WACV 2025); CORRECTED (bib fields) -> the bib title is wrong: actual title is "Anomaly Detection for People with Visual Impairments Using an Egocentric **360-Degree Camera**" (not "...Egocentric AI Assistant"); full authors: `Inpyo Song and Sanghyeon Lee and Minjun Joo and Jangwon Lee`; add pages 2828–2837 (WACV 2025).
- **NOTES:** The row KEEPS its self-report footnote $^e$ (paper's own method, narrowly beats VadCLIP). Verified from primary — no need to drop the row. N/A XD cell confirmed (also closes checklist #14 for FDPN).

### Item 9 — TEVAD

- **CLAIM:** UCF AUC = 84.9; XD AP ≈ 79.8 (MEDIUM precision; ablations 79.3–79.76; web "88.28" is a misattribution).
- **PRIMARY SOURCE URL:** CVF Open Access PDF https://openaccess.thecvf.com/content/CVPR2023W/O-DRUM/papers/Chen_TEVAD_Improved_Video_Anomaly_Detection_With_Captions_CVPRW_2023_paper.pdf (WebFetch 403'd; the PDF was downloaded directly and its tables extracted) + https://github.com/coranholmes/TEVAD (official repo, locator only).
- **QUOTE:** Table 3 (UCF-Crime): 84.9 (printed to one decimal). Table 4 (XD-Violence): 79.8 AP (one decimal, visual-only). Ablation XD variants: MTN concat 79.3, MTN add 79.76, MTN product 78.49.
- **VERDICT:** VERIFIED — both headline numbers confirmed at the paper's own one-decimal precision; "88.28" does not appear in the paper.
- **NOTES:** Footnote $^j$ (MEDIUM precision, ablation range) can be simplified: the headline 79.8 is the paper's own Table 4 value. Authors (Weiling Chen, Keng Teck Ma, Zi Jian Yew, Minhoe Hur, David Aik-Aun Khoo) and CVPRW 2023 O-DRUM venue confirmed — bib `chen2023tevad` VERIFIED as-is.

---

## Part B — Worklist items 10–17 (Task 2)

### Item 10 — Sultani et al. (XD cell omission)

- **CLAIM:** UCF AUC = 75.41 (original paper); the thesis XD cell is `---` because 73.20 AP is Wu et al. ECCV 2020's re-implementation, not a 2018 result.
- **PRIMARY SOURCE URL:** https://ar5iv.labs.arxiv.org/html/1801.04264 (Sultani, Chen & Shah, CVPR 2018) + cross-check https://ar5iv.labs.arxiv.org/html/2007.04687 (Wu et al., ECCV 2020).
- **QUOTE:** Sultani Table 3: "an AUC of 75.41 for their proposed method with constraints" — evaluated on the paper's own newly introduced 1,900-video / 128-hour dataset (which IS UCF-Crime; this is the paper that introduced it). The paper contains no XD-Violence number (the dataset did not exist until 2020). Wu et al. XD-Violence paper Table 3: "Sultani et al. [36]" at 73.20% AP (Wu's own re-implementation; Wu's proposed HL-Net reaches 78.64% AP).
- **VERDICT:** VERIFIED — 75.41 confirmed; the `---` omission of the XD cell is CORRECT and stays; footnote $^l$ (attribute 73.20 to Wu et al. 2020) stands.
- **NOTES:** If an XD entry for Sultani's method is ever wanted, it must be cited as "re-implemented by Wu et al. 2020 (73.20 AP)" — never as Sultani's own result.

### Item 11 — RTFM

- **CLAIM:** UCF AUC = 84.30 (I3D RGB); XD AP = 77.81 (I3D RGB) — the canonical pair cited in paper + thesis.
- **PRIMARY SOURCE URL:** https://ar5iv.labs.arxiv.org/html/2101.10030 (Tian et al., ICCV 2021, arXiv:2101.10030).
- **QUOTE:** Table 2 — RTFM with I3D-RGB features = 84.30% AUC on UCF-Crime. Table 3 — RTFM with I3D-RGB features = 77.81% AP on XD-Violence.
- **VERDICT:** VERIFIED — both numbers confirmed for the I3D-RGB variant.
- **NOTES:** No "78.27" appears anywhere in the paper's tables (any such figure is from a later re-implementation, not RTFM's own paper). Closes checklist #11.

### Item 12 — EventVAD

- **CLAIM:** UCF AUC = 82.03; XD AP = 64.04 (the paper's XD ROC-AUC 87.51 must never be used as AP); ACM MM 2025; training-free but 80GB A800-class compute.
- **PRIMARY SOURCE URL:** https://ar5iv.labs.arxiv.org/html/2504.13092 (tables) + https://arxiv.org/abs/2504.13092 (metadata) (Shao et al., ACM MM 2025).
- **QUOTE:** Table 1 — "82.03" AUC on UCF-Crime (training-free setting). Table 2 — "64.04" AP on XD-Violence, with "87.51" reported in the same table as a separate ROC-AUC metric. Compute: "All experiments were conducted on a single NVIDIA A800 (80GB) GPU"; framework described as "training-free". Comments field verbatim: "Paper was accepted by ACM MM 2025; Code: https://github.com/YihuaJerry/EventVAD".
- **VERDICT:** VERIFIED — 82.03 / 64.04 confirmed with correct metric labels; ACM MM 2025 and the A800-80GB compute claim confirmed.
- **NOTES:** **Full author list (BibTeX-ready, replaces `and others` in `shao2025eventvad`):** `Yihua Shao and Haojin He and Sijie Li and Siyu Chen and Xinwei Long and Fanhu Zeng and Yuxuan Fan and Muyang Zhang and Ziyang Yan and Ao Ma and Xiaochen Wang and Hao Tang and Yan Wang and Shuyan Li` (14 authors, in order). Footnote $^k$ stands; remove RE-VERIFY comments in ch07 + ch08.

### Item 12b — LAVAD

- **CLAIM:** UCF AUC = 80.28; XD AP = 62.01 (the paper's XD ROC-AUC 85.36 must never be used as AP).
- **PRIMARY SOURCE URL:** https://ar5iv.labs.arxiv.org/html/2404.01014 (Zanella, Menapace, Mancini, Wang & Ricci, CVPR 2024).
- **QUOTE:** Table 1 — LAVAD = "80.28" AUC ROC on UCF-Crime (frame-level). Table 2 — LAVAD = "62.01" AP and "85.36" AUC ROC on XD-Violence, AP being the primary metric.
- **VERDICT:** VERIFIED — 80.28 / 62.01 confirmed; 85.36 correctly identified as ROC-AUC.
- **NOTES:** Remove RE-VERIFY comments in ch07 + ch08.

### Item 13 — HyperVD

- (PENDING batch 5 — placeholder; will be replaced before finalization.)

### Item 13b — Ghadiya et al.

- (PENDING batch 5 — placeholder; will be replaced before finalization.)

### Item 14 — STPrompt & FDPN XD cells (N/A confirmation)

- **CLAIM:** Neither STPrompt nor FDPN evaluates XD-Violence; both N/A cells + footnotes d/e are correct.
- **PRIMARY SOURCE URL:** STPrompt: https://ar5iv.labs.arxiv.org/html/2408.05905 + https://arxiv.org/abs/2408.05905. FDPN: https://arxiv.org/abs/2411.10945 (see Item 8).
- **QUOTE:** STPrompt Table 1 row: "STPrompt | CLIP | 88.08 | 23.90" (UCF-Crime AUC = 88.08%); datasets evaluated: UCF-Crime, ShanghaiTech, UBnormal — XD-Violence is not among them. Comments field verbatim: "Accepted by ACMMM2024". FDPN: XD-Violence appears only as dataset statistics (Table 1), never as an evaluation benchmark.
- **VERDICT:** VERIFIED — both N/A cells confirmed; STPrompt UCF 88.08 also confirmed in passing.
- **NOTES:** STPrompt bib fields confirmed (authors Peng Wu, Xuerong Zhou, Guansong Pang, Zhiwei Yang, Qingsen Yan, Peng Wang, Yanning Zhang; ACM MM 2024). The arXiv page exposes only the arXiv DOI — the canonical ACM DOI (10.1145/...) would need an ACM DL fetch; not required for the thesis bib (venue + year suffice).

### Item 15 — Light-WVAD attribution + XD cell

- (PENDING batch 5 — placeholder; will be replaced before finalization.)

### Item 16 — PI-VAD & DSANet publication status (checklist #16 / WR-02)

- (PENDING batch 5 — placeholder; will be replaced before finalization.)

### Item 17 — PI-VAD & DSANet full author lists (checklist #17 / IN-02)

- (PENDING batch 5 — placeholder; will be replaced before finalization.)

---

## Part C — GATE-13 bib entries (15) — field-by-field

### C.1 zhang2024holmesvad
- **CLAIM (current bib):** `@misc`, 9 authors (Huaxin Zhang ... Nong Sang), eprint 2406.12235, year 2024.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2406.12235
- **QUOTE:** abs page authors: "Huaxin Zhang, Xiaohao Xu, Xiang Wang, Jialong Zuo, Chuchu Han, Xiaonan Huang, Changxin Gao, Yuehuan Wang, Nong Sang"; Comments: "19 pages, 9 figures" (no journal-ref).
- **VERDICT:** VERIFIED — `@misc` + eprint is the correct type (arXiv-only, no venue); author list exact match.

### C.2 zhang2025holmesvau
- **CLAIM (current bib):** `@inproceedings` CVPR 2025, 9 authors, note arXiv:2412.06171.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2412.06171
- **QUOTE:** abs page: "Accepted by CVPR2025"; authors "Huaxin Zhang, Xiaohao Xu, Xiang Wang, Jialong Zuo, Xiaonan Huang, Changxin Gao, Shanjun Zhang, Li Yu, Nong Sang".
- **VERDICT:** VERIFIED — type, venue, year, and author list all confirmed.

### C.3 wu2024stprompt
- **CLAIM (current bib):** `@inproceedings` ACM MM 2024, 7 authors, note arXiv:2408.05905.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2408.05905
- **QUOTE:** Comments field verbatim: "Accepted by ACMMM2024"; authors Peng Wu, Xuerong Zhou, Guansong Pang, Zhiwei Yang, Qingsen Yan, Peng Wang, Yanning Zhang.
- **VERDICT:** VERIFIED.

### C.4 song2025fdpn
- **CLAIM (current bib):** `@inproceedings` WACV 2025, authors "Song and Lee and Joo and Lee" (surnames only), title "...Using an Egocentric AI Assistant".
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2411.10945 + CVF WACV 2025 Open Access record.
- **QUOTE:** actual title: "Anomaly Detection for People with Visual Impairments Using an Egocentric 360-Degree Camera"; authors Inpyo Song, Sanghyeon Lee, Minjun Joo, Jangwon Lee; WACV 2025, pp. 2828–2837.
- **VERDICT:** CORRECTED -> title = "Anomaly Detection for People with Visual Impairments Using an Egocentric 360-Degree Camera"; author = `Inpyo Song and Sanghyeon Lee and Minjun Joo and Jangwon Lee`; add `pages = {2828--2837}`.

### C.5 yang2024tpwng
- **CLAIM (current bib):** `@inproceedings` CVPR 2024, authors Zhiwei Yang, Jing Liu, Peng Wu, note arXiv:2404.08531.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2404.08531 + https://ar5iv.labs.arxiv.org/abs/2404.08531
- **QUOTE:** Comments: "Accepted to CVPR2024"; authors "Zhiwei Yang, Jing Liu, Peng Wu"; Table 1 proposed-method row: "Ours | 87.79% | 83.68%" (confirms the thesis table's TPWNG row 87.79/83.68 as a bonus).
- **VERDICT:** VERIFIED (bib + both table numbers).

### C.6 pu2024pel4vad
- **CLAIM (current bib):** `@article` IEEE Transactions on Image Processing 2024, authors "Yujiang Pu and Xiaoyu Wu and Lu Yang and Shengjin Wang", note arXiv:2306.14451.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2306.14451 + https://arxiv.org/html/2306.14451v2
- **QUOTE:** author affiliation line: "Yujiang Pu, Xiaoyu Wu and Lulu Yang are with the School of Information and Communication Engineering, Communication University of China"; Table I (UCF): "Ours | I3D RGB | 86.76 | 0.43"; Table II (XD): "Ours | I3D RGB | 85.59 | 0.57" (confirms the thesis table's PEL4VAD row 86.76/85.59 as a bonus).
- **VERDICT:** CORRECTED -> author 3 is "Lulu Yang" (not "Lu Yang"): `Yujiang Pu and Xiaoyu Wu and Lulu Yang and Shengjin Wang`. Journal confirmed: IEEE TIP. Optional coordinates: vol. 33, pp. 4923–4936, DOI 10.1109/TIP.2024.3451935.
- **NOTES:** Evidence-strength caveat: the TIP volume/pages/DOI come from IEEE Xplore (doc 10667004) + ADS bibliographic records surfaced via search — IEEE Xplore itself returned empty and ACM DL 403'd the fetcher. The author-name correction and both accuracy numbers are backed by directly fetched arXiv primary sources. If the user wants publisher-page-grade certainty for vol/pages, keep the bib minimal (journal + year + arXiv note, as now) — the "Lulu Yang" fix applies either way.

### C.7 leng2026piercingeye
- **CLAIM (current bib):** `@article` IEEE TPAMI, year 2026, authors surnames-only, title "PiercingEye: Dual-Space Video Violence Detection".
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2504.18866
- **QUOTE:** abs page: "Submitted to IEEE Transactions on Pattern Analysis and Machine Intelligence" ([v1] 26 Apr 2025; only arXiv DOI).
- **VERDICT:** CORRECTED -> NOT a published TPAMI article. Retype `@misc` (eprint 2504.18866, archivePrefix arXiv), year 2025; author = `Jiaxu Leng and Zhanjie Wu and Mingpi Tan and Mengjingcheng Mo and Jiankang Zheng and Qingqing Li and Ji Gan and Xinbo Gao`; title extended to "PiercingEye: Dual-Space Video Violence Detection with Hyperbolic Vision-Language Guidance". The ch07 table's Venue cell "IEEE TPAMI'26" and Year "2026" must change accordingly (see Item 6).

### C.8 zanella2024anomalyclip
- **CLAIM (current bib):** `@article` Computer Vision and Image Understanding 2024, 6 authors, no arXiv/DOI fields.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2310.02835 (+ ScienceDirect record pii S1077314224002443)
- **QUOTE:** CVIU 2024, vol. 249, article 104163, DOI 10.1016/j.cviu.2024.104163; authors Luca Zanella, Benedetta Liberatori, Willi Menapace, Fabio Poiesi, Yiming Wang, Elisa Ricci.
- **VERDICT:** VERIFIED (existing fields) — enrich with `volume = {249}`, `pages/article = {104163}`, `doi = {10.1016/j.cviu.2024.104163}`, `note = {arXiv:2310.02835}`.

### C.9 chen2023tevad
- **CLAIM (current bib):** `@inproceedings` CVPRW 2023, 5 authors.
- **PRIMARY SOURCE URL:** https://openaccess.thecvf.com/content/CVPR2023W/O-DRUM/papers/Chen_TEVAD_Improved_Video_Anomaly_Detection_With_Captions_CVPRW_2023_paper.pdf
- **QUOTE:** CVF Open Access PDF title/author block: "TEVAD: Improved Video Anomaly Detection with Captions" — Weiling Chen, Keng Teck Ma, Zi Jian Yew, Minhoe Hur, David Aik-Aun Khoo; CVPR 2023 Workshops (O-DRUM).
- **VERDICT:** VERIFIED.

### C.10 peng2024hypervd
- (PENDING batch 5 — placeholder; will be replaced before finalization.)

### C.11 ghadiya2024crossmodal
- (PENDING batch 5 — placeholder; will be replaced before finalization.)

### C.12 yan2018stgcn
- **CLAIM (current bib):** `@inproceedings` AAAI 2018, authors Sijie Yan, Yuanjun Xiong, Dahua Lin.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/1801.07455
- **QUOTE:** Title "Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition"; authors "Sijie Yan, Yuanjun Xiong, Dahua Lin"; Comments "Accepted by AAAI 2018".
- **VERDICT:** VERIFIED.

### C.13 hendrycks2019imagenetc
- **CLAIM (current bib):** `@inproceedings` ICLR 2019, authors Dan Hendrycks, Thomas Dietterich.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/1903.12261
- **QUOTE:** Title "Benchmarking Neural Network Robustness to Common Corruptions and Perturbations"; authors "Dan Hendrycks, Thomas Dietterich"; Comments "ICLR 2019 camera-ready; datasets available at [github.com/hendrycks/robustness]".
- **VERDICT:** VERIFIED.

### C.14 sun2016coral
- **CLAIM (current bib):** `@inproceedings` AAAI 2016, authors Baochen Sun, Jiashi Feng, Kate Saenko.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/1511.05547
- **QUOTE:** Title "Return of Frustratingly Easy Domain Adaptation"; authors "Baochen Sun, Jiashi Feng, Kate Saenko"; Comments "Fixed typos. Full paper to appear in AAAI-16. Extended Abstract of the full paper to appear in TASK-CV 2015 workshop".
- **VERDICT:** VERIFIED.

### C.15 schneider2020norm
- **CLAIM (current bib):** `@inproceedings` NeurIPS 2020, 6 authors.
- **PRIMARY SOURCE URL:** https://arxiv.org/abs/2006.16971
- **QUOTE:** Title "Improving robustness against common corruptions by covariate shift adaptation"; authors "Steffen Schneider, Evgenia Rusak, Luisa Eck, Oliver Bringmann, Wieland Brendel, Matthias Bethge"; Comments "Accepted at the Thirty-fourth Conference on Neural Information Processing Systems".
- **VERDICT:** VERIFIED ("Thirty-fourth Conference on Neural Information Processing Systems" = NeurIPS 2020).

---

## Part D — `and others` author-list expansions (four entries)

| Bib key | Status | Full author list (BibTeX-ready) |
|---------|--------|--------------------------------|
| shao2025eventvad | RESOLVED | `Yihua Shao and Haojin He and Sijie Li and Siyu Chen and Xinwei Long and Fanhu Zeng and Yuxuan Fan and Muyang Zhang and Ziyang Yan and Ao Ma and Xiaochen Wang and Hao Tang and Yan Wang and Shuyan Li` |
| damicantonio2025gsmoe | RESOLVED (order caveat) | `Giacomo D'Amicantonio and Snehashis Majhi and Quan Kong and Lorenzo Garattoni and Gianpiero Francesca and François Brémond and Egor Bondarev` (arXiv order; ICCV virtual page swaps the last two — recommend `... and Egor Bondarev and François Brémond`; USER SPOT-CHECK) |
| majhi2025pivad | (pending batch 5) | — |
| yin2026dsanet | (pending batch 5) | — |

---

## Part E — Cells to omit + omission footnotes

(To be finalized in Task 2 — no UNVERIFIABLE result cells identified so far among items 1–12b/14; existing omissions confirmed correct: Sultani XD `---` [Item 10], STPrompt/FDPN XD N/A [Item 14].)

---

*Draft status: Task 1 complete (items 1–9 + bib C.1–C.9, C.12–C.15). Items 13/13b/15/16/17 + C.10/C.11 + Part D rows 3–4 pending batch-5 completion; final verdict tally and Part E in Task 2.*
