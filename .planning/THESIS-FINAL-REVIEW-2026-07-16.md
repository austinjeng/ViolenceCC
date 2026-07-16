# Thesis Final-Version Review — 2026-07-16

**Context:** Run immediately after the professor-requested restructure (quick 260716-n1r,
merge a72e752): Limitations moved into Ch7 Discussion (§7.7), Future Work into Ch8
"Conclusion and Future Work" (§8.4), old Ch8 dissolved. The author expects this to be the
FINAL version of the thesis.

**Method:** 116-agent workflow (wf_5b45ce3b-16a) — 4 restructure audits (content parity via
mechanical word-level diff, cross-ref audit, seam prose, PDF structure via PyMuPDF) +
13 sweep agents (all 8 chapters individually, frontmatter incl. zh abstract, whole-document
number consistency, citations/bib, NTUST format regression, structure-vs-reality) +
adversarial verification (3 independent refuter lenses per HIGH/MEDIUM finding, 1 per LOW;
majority vote). 51 raw findings -> 44 unique (7 cross-agent duplicates merged), 0 refuted.

## Restructure audit verdicts

| Audit | Verdict | Notes |
|---|---|---|
| Content parity | PASS | Word-level diff old ch08 vs new homes: zero lost/duplicated/altered sentences beyond the 4 sanctioned adaptations; all 5 sec:lim-* labels preserved |
| Cross-references | PASS | No active ref to ch:08/sec:lim-future; all 6 retargets correct in context; 0 undefined refs in log/aux; main.tex has exactly 8 includes |
| Seam prose | FAIL -> FIXED | 3 issues (stale ch07 intro roadmap, 7.6.1 vs 7.7.1 duplication, coda antecedent) — all fixed in 3c275e4 |
| PDF structure | PASS | 8 chapters in TOC/bookmarks; §7.7 with 5 subsections; Ch8 titled correctly; 97pp; zero ??/[?]/TODO/CGW/Appendix in rendered text; R4 order + Roman/arabic numbering intact |

## Status after this review's fix pass (commit 3c275e4)

FIXED (4): H-ch07-intro-roadmap, M-7.7.1-duplication, L-ch09-coda-antecedent,
L-ch09-transductive-pointer. Rebuild clean (0 errors, 0 undefined refs).

## Fix-batch outcome (quick 260716-q9z, 2026-07-16)

H1/H3/H4 + M1-M12/M14 ALL FIXED (commits 7cf64be + c514213, merge 2894307; fragment M12-class
follow-up 22cfa08). Verifier: passed 6/6 must-haves (260716-q9z-VERIFICATION.md) — H1 re-derived
from tables (4-4 exact), H3 byte-identical row move in both files, H4 confirmed spatially in the
PDF (folio VIII clean), zero experiment-number changes, all 4 executor deviations sound.
Build: 95pp (was 97 — root-caused: seam condense 3c275e4 −1pp, M2 sanctioned deletion −1pp),
0 errors, 0 undefined refs, 0 Overfull box, headlines 82.5/78.7 intact.

REMAINING OPEN: M15 acknowledgments (author-only) + 22 LOW (L20/L22 fixed earlier; polish tier).

## Original open-item triage (pre-fix-batch, kept for record)

**Must fix before submission (blockers):**
- M15 acknowledgments placeholder — *author must write this personally* (renders on Roman p. III; rated MEDIUM by verifiers but it is a hard submission blocker)
- H4 notation.tex Symbols table overflow — page number VIII overprints a table row, breaks the 2cm bottom-margin gate (mechanical fix: split tabular / longtable)
- H1 ch05:160 "majority of cells" false claim (actual split 4-4, verified against tables and unrounded eval_metrics.json)
- H3 ch07:253 tab:sota-full row order ("This work" 82.5 must sit above EventVAD 82.03 per the caption's own sorting claim; same fix in paper/sota_comparison_full.tex if that fragment is still used)

**Should fix (MEDIUM, ~1 session):** all quote-verified; none change any number.
Notables: M12 "+13.2 on the hardest corruption" violates the thesis-canonical qualifier
("the condition that most collapses the visual-language stream"); M9 "Gaussian deepest
failure mode" contradicts §6.4 (JPEG is lowest); M11 GS-MoE footnote contradiction;
M1 "sub-million-parameter" vs the 1.02M Giant head.

**Optional polish (LOW):** typos, phrasing, caption/prose nits — batch or skip at author's discretion.

Note: acknowledgments (M15) is the only item Claude cannot fix; everything else is mechanical
or editorial with fixes suggested inline below.

---

## HIGH (4)

### H1. [FIXED 7cf64be] `thesis/chapters/ch05_results_fusion.tex:160` — False claim that 2-person aggregation is worse than default in the majority of cells; the actual split is 4-4

The text reads: "the 2-person aggregation is \emph{worse} than the default for the majority of backbone$\times$dataset cells". This is contradicted by the chapter's own Tables 5.1/5.2 on the same pages. At displayed precision, GF 2-Person beats default Gated Fusion in 4 of 8 cells (UCF Base 79.5 vs 79.0, UCF SO400M 81.7 vs 81.3, UCF Giant 82.6 vs 82.5, XD SO400M 79.2 vs 78.7) and is worse in the other 4 (UCF CLIP 81.3 vs 81.4, XD CLIP 74.4 vs 76.5, XD Base 73.2 vs 74.5, XD Giant 76.0 vs 76.8). I verified with unrounded 3-seed means from results/*_2person_*/eval_metrics.json: better in 4, worse in 4 (diffs +0.465, +0.393, +0.039, +0.473 vs -0.044, -2.119, -1.307, -0.862). A 4-4 split is not a majority, and a committee member can catch this by counting cells in the tables directly above the sentence.

**Suggested fix:** Rewrite to match the data, e.g.: "the 2-person aggregation is worse than the default in half of the backbone$\times$dataset cells, including three of the four XD-Violence backbones" (the other two arguments in the sentence -- within seed variance, post-hoc selection -- already carry the point).

### H2. [FIXED 3c275e4] `thesis/chapters/ch07_discussion.tex:14` — Chapter 7 intro claims the chapter closes with the SOTA comparison, but after the restructure it actually closes with the new \section{Limitations} (§7.7); the intro also omits limitations from its list of chapter contents. *(independently found by 3 agents)*

Lines 14-17 read: "The chapter closes with a full comparison against the published state of the art (Section~\ref{sec:sota}), including the fair-subset analysis that defines the regime in which this work's numbers are directly comparable." This was true before commits f304464/236638a, but the dissolved Chapter 8 limitation sections now sit at the end of this chapter as \section{Limitations} (line 461, label sec:disc-limitations, printed as §7.7 with subsections 7.7.1-7.7.5 — confirmed by main.toc lines 83-88, where 7.7 Limitations follows 7.6 Comparison with the State of the Art). So the chapter's own roadmap is now structurally wrong on two counts: (1) the chapter does not close with the SOTA comparison, and (2) the intro's enumeration of what "this chapter steps back and discusses" (lines 8-14) never mentions the limitations material at all, even though ch01's roadmap (ch01_introduction.tex:265-266) explicitly promises "Chapter~\ref{ch:07} ... states the study's limitations". A committee member reading Chapter 7 end-to-end will see the intro contradict the chapter's actual ending.

**Suggested fix:** Rewrite the last sentence of the Chapter 7 opening paragraph to reflect the new order, e.g.: "The chapter then gives a full comparison against the published state of the art (Section~\ref{sec:sota}), including the fair-subset analysis that defines the regime in which this work's numbers are directly comparable, and closes by stating the study's limitations (Section~\ref{sec:disc-limitations})."

### H3. [FIXED 7cf64be] `thesis/chapters/ch07_discussion.tex:253` — In Table tab:sota-full the bolded 'This work' row (UCF 82.5) is placed BELOW EventVAD (UCF 82.03), contradicting the caption's explicit claims 'sorted by UCF AUC descending' and 'placed at its true position'.

Line 252: 'EventVAD$^{k}$~\cite{shao2025eventvad}    & 2025 & ACM MM'25         & 82.03 & 64.04 & ...' followed by line 253: '\textbf{This work (dual-modal fusion)} & \textbf{2026} & \textbf{(thesis)} & \textbf{82.5} & \textbf{78.7} & ...'. The caption (lines 220-223) states the table is 'sorted by UCF AUC descending. The \textbf{This work} row is placed at its true position'. Since 82.5 > 82.03, the true position is one row higher, above EventVAD. Every other row is correctly ordered; this is the one row a committee member will look at first, and the chapter's own prose agrees 82.5 exceeds EventVAD ('matches or exceeds them on UCF', line 453). The same misordering exists in the source fragment paper/sota_comparison_full.tex:120-121, from which this was ported.

**Suggested fix:** Swap lines 252 and 253 so the 'This work' row precedes the EventVAD row (and apply the same swap in paper/sota_comparison_full.tex if that fragment is still used).

### H4. [FIXED 7cf64be] `thesis/frontmatter/notation.tex:46` — Symbols table overflows the page: it runs ~1.7cm into the bottom margin on Roman page VIII and the page number 'VIII' is printed on top of a table row *(independently found by 2 agents)*

The Symbols table (\begin{center}\begin{tabular}{@{}lp{10.5cm}@{}} ... 25 rows, notation.tex lines 46-98) is a single unbreakable tabular that no longer fits on one page. main.log line 1448 reports 'Overfull \vbox (47.5823pt too high) has occurred while \output is active' when shipping frontmatter page 8 (Roman VIII, physical PDF page 12). Rendering that page confirms the table's last rows ('$w$ & routing scalar scaling the visual stream, $w = 1-(1-w_{\mathrm{vl}})\,s$' and '$\rho$ & SAR sharpness-aware step radius') extend past the 2cm bottom-margin line, and the folio 'VIII' is overprinted directly on the 'routing scalar scaling the visual stream' row. This regresses the fixed NTUST margin gate (bottom 2cm) and is immediately visible to a committee member.

**Suggested fix:** Split the Symbols tabular into two tables so a page break can occur (e.g., end the first tabular after the $\lambda_1,\lambda_2$ row at line 79 and start a second 'Symbols (continued)' tabular for the TTA/reweighting symbols), or convert it to longtable. Rebuild and confirm the Overfull \vbox warning is gone from main.log.


## MEDIUM (15)

### M1. [FIXED c514213] `thesis/chapters/ch02_related_work.tex:66` — "sub-million-parameter fusion head" contradicts the 0.50M-1.02M parameter range stated in Chapters 1, 4, and 8 (Conclusion)

Line 66 reads: "a design goal shared by the sub-million-parameter fusion head of this thesis." But ch01_introduction.tex:105 says "(0.50M--1.02M trainable parameters, depending on backbone)", ch04_experimental_setup.tex:379 says "0.50M--1.02M trainable parameters (scaling with the visual feature dimension)", and ch09_conclusion.tex:66 says "0.50M to 1.02M trainable parameters depending on backbone". The largest configuration (1.02M, which corresponds to the widest visual feature dimension — the SigLIP2 Giant backbone that produces the UCF-Crime 82.5% headline) is above one million parameters, so "sub-million" is false for the headline configuration and inconsistent with three other chapters a committee member can cross-check.

**Suggested fix:** Replace "the sub-million-parameter fusion head" with a claim consistent with the rest of the thesis, e.g. "the lightweight (0.50M--1.02M parameter) fusion head of this thesis" or "the roughly-million-parameter fusion head".

### M2. [FIXED c514213] `thesis/chapters/ch03_methodology.tex:114` — Section 3.3 states the same two facts twice in back-to-back paragraphs (four-stream weighted averaging, and the 20-second-snippet caveat), plus a wrong 'reported below' pointer

Lines 108-112 already say: "Each stream produces a 256-dimensional feature vector per temporal window, and the four are combined by weighted averaging with weights 1.0 (joint), 1.0 (bone), 0.5 (joint motion), and 0.5 (bone motion)". Line 114 then repeats it almost verbatim: "The four-stream features are combined by weighted averaging (joint and bone weighted 1.0, motion streams 0.5) to form the final 256-d skeleton representation." Likewise, line 114's closing parenthetical "(On UCF-Crime a single snippet thus pools skeleton motion over ${\sim}20$~s---far longer than the few-second action clips on which CTR-GCN was pre-trained---a plausible factor in the weaker UCF skeleton-only result reported below.)" duplicates lines 119-122: "Second, the frozen NTU-pretrained encoder was trained on short, single-action indoor clips; the 20-second effective snippet duration on UCF-Crime stretches this encoder well outside its pretraining regime, an honest caveat for interpreting the skeleton-only results of Chapter~\ref{ch:05}." This reads as an unmerged paste (paper text alongside thesis text) that a committee member would mark. Additionally, "reported below" is wrong in place: the skeleton-only result appears nowhere in Chapter 3 — it is in Chapter 5, as the duplicate sentence correctly says.

**Suggested fix:** Delete the redundant sentence "The four-stream features are combined by weighted averaging (joint and bone weighted 1.0, motion streams 0.5) to form the final 256-d skeleton representation." and the closing parenthetical from line 114 (the 'Second, ...' paragraph at lines 116-122 already carries the caveat with the correct Chapter 5 pointer).

### M3. [FIXED c514213] `thesis/chapters/ch03_methodology.tex:359` — Symbol collision inside Section 3.7: plain $s$ means per-snippet sigmoid score in 3.7.1 but skeleton-reliability gate in 3.7.3; $\sigma$ means sigmoid in Eq. (3.3) but standard deviation in Eq. (3.7)

Line 304 defines binary entropy "$-(s\log s + (1-s)\log(1-s))$ per snippet score $s$"; 55 lines later, line 359 reuses the same bare symbol for a different quantity: "A skeleton-reliability gate $s = \min\!\big(1, \max\big(0,\, (2 z_0 - z_{\mathrm{skel}})/z_0\big)\big)$", and it is then used as the gate throughout 3.7.3 (e.g. line 397 "the skeleton is trusted ($s > 0$)") and in the summary at line 416 ("form $w_{\mathrm{vl}}$, $s$, and $w$"). Both usages sit in the same Section 3.7, and the neighboring solo-score symbol $s_{\mathrm{clip}}$ makes bare $s$ naturally read as a score. Compounding this, $\sigma$ is the sigmoid in the gate equation at line 196 ("$\mathbf{g} = \sigma(W_g[\hat{\mathbf{s}} \| \hat{\mathbf{v}}] + \mathbf{b}_g)$") but the standard deviation in Eq. (3.7) at line 357 ("$\sigma\big(s_{\mathrm{clip}}^{\mathrm{test}}\big)$"). Neither overload is flagged in the chapter's Notation paragraph (lines 50-58). A notation-careful committee member will catch this.

**Suggested fix:** Rename the skeleton-reliability gate to a non-colliding symbol (e.g. $r_{\mathrm{skel}}$, matching the code's skel_rel) throughout 3.7.3 and the summary list, and either use $\mathrm{std}(\cdot)$ for the dispersion in Eq. (3.7) or add a one-line note in the Notation paragraph disambiguating the overloads.

### M4. [FIXED c514213] `thesis/chapters/ch04_experimental_setup.tex:385` — Arithmetically inconsistent gloss: ~30 ms/frame is equated with 21.6 FPS end-to-end, but 30 ms/frame is 33.3 FPS (as the cited table's own source CSV states), while 21.6 FPS corresponds to ~46 ms/frame

Line 385-387 reads: "pose estimation runs at ${\sim}30$~ms per frame (about 21.6 FPS end-to-end, 99.3\% of it model inference)". These two numbers cannot describe the same measurement: 1000/30.07 ms = 33.3 FPS (results/backbone_bench_combined.csv, the tracked source of Table tab:efficiency-backbones, lists exactly "30.1 ms/f" latency AND "33.3 f/s" throughput for the RTMPose-m + YOLOX row), whereas 21.6 FPS implies 46.3 ms/frame. The "99.3% of it model inference" clause makes the gap unexplainable by I/O overhead. The two figures come from different measurements: 30.07 ms/frame is the isolated per-frame benchmark (Table 4.3 of this chapter), while 21.6 FPS is the production extraction-loop throughput on single-person scenes (ch03_methodology.tex:88 explicitly says "approximately 21.6 FPS on single-person scenes (about 15 FPS with multiple persons)"). A committee member who divides 1000 by 30 will catch the 1.5x discrepancy within a single sentence, and the sentence also contradicts the throughput column of the table it is drawn from.

**Suggested fix:** Decouple the two measurements, e.g.: "pose estimation costs ${\sim}30$~ms per frame in isolation (Table~\ref{tab:efficiency-backbones}), and the full extraction loop sustains about 21.6 FPS on single-person scenes (Chapter~\ref{ch:03}), 99.3\% of that time being model inference---an order of magnitude slower per frame than CLIP embedding."

### M5. [FIXED c514213] `thesis/chapters/ch05_results_fusion.tex:153` — "Confirms its direction on every backbone" contradicts the same paragraph's "(it helps only SO400M)"; "larger margins" is true only for mean-only pooling

The sentence reads: "The original pooling study ... measured the same ordering with larger margins ($-0.90$~AP for 2-person concatenation and $-2.32$~AP for mean-only pooling), and the final 3-seed grid confirms its direction on every backbone." Two problems: (1) two sentences earlier the same paragraph states the 2-person aggregation "helps only SO400M" on XD-Violence (+0.5 AP, Table 5.2), so the final grid does NOT confirm the 2-person direction on every backbone (on UCF it is also nominally better on 3 of 4 backbones). (2) "larger margins" holds only for mean-only pooling (-2.32 historical vs -0.3..-0.5 final): for 2-person the historical margin (-0.90) is essentially equal to the final cross-backbone XD mean cost ("about 0.90 AP", stated in the same paragraph) and smaller than the final CLIP-backbone margin (-2.1 AP), so the original study did not measure a larger 2-person margin.

**Suggested fix:** Scope the confirmation claim to mean-only pooling (which is negative on every XD backbone) and drop or qualify "larger margins" for the 2-person comparison, e.g.: "...measured the same default-wins ordering, with a much larger mean-only margin ($-2.32$~AP); the final 3-seed grid confirms the mean-only direction on every backbone, while the 2-person cost is concentrated in CLIP and SigLIP2 Base."

### M6. [FIXED c514213] `thesis/chapters/ch05_results_fusion.tex:342` — CI-width claim ("exceeds the spread of the entire published leaderboard") is contradicted by the thesis's own Chapter 7 comparison table

The text reads: "its width exceeds the spread of the entire published leaderboard on this benchmark." The UCF-Crime bootstrap CI width is 12.39 pp, but the thesis's own SOTA comparison table in Chapter 7 (ch07_discussion.tex lines 237-255) spans Sultani et al. 75.41 (explicitly included as the "founding baseline" row) to DSANet 89.44 -- a spread of 14.03 pp, which is wider than 12.39 pp. As written, the claim is false against the thesis's own table; it holds only for the modern frozen-feature subset (84.30-89.44).

**Suggested fix:** Soften or scope the claim, e.g.: "its width rivals the spread of the entire published leaderboard on this benchmark and exceeds the spread of the modern frozen-feature methods it is compared against in Chapter 7."

### M7. [FIXED c514213] `thesis/chapters/ch05_results_fusion.tex:540` — Explosion007 does not "show the same pattern" as the near-0.000 short-event miss: its scores saturate near 0.99, not near zero

The text reads: "RoadAccidents011 contains an event spanning only 1.9\% of its frames, and the model scores the entire video near 0.000... Explosion007 (4.2\% anomalous) shows the same pattern." Per the tracked source results/_analysis_2026-06-10/pri9_failure_cases.md (the file this section cites), Explosion007's frame-score means are 0.992 (anomalous) and 0.993 (normal) -- near-ceiling saturation, the opposite of RoadAccidents011's near-0.000 profile, and matching the chapter's first regime (saturated-high near-ties, like Burglary017 at 0.994/0.994). Explosion007 is a short-event case, but its failure mode is inverted ranking under ceiling saturation, not dilution toward zero, so "the same pattern" is contradicted by the cited data.

**Suggested fix:** Clarify which aspect is shared, e.g.: "Explosion007 (4.2\% anomalous) is likewise a short-event miss, though there the head saturates the whole video near the ceiling rather than near zero, blending the two regimes."

### M8. [FIXED c514213] `thesis/chapters/ch05_results_fusion.tex:543` — Reciprocal "exactly" claims between the failure analysis and the per-category section do not match: Shooting is mid-pack per-category (95.67), and Robbery is in the weak tail but absent from the failure cases

Line 543-545 reads: "abrupt, visually-transient events (RoadAccidents, Explosion, Shooting) are exactly the categories where snippet pooling costs the most (Section~\ref{sec:percat})", and line 595-597 reads back: "The weak tail is exactly the abrupt, short-event category set identified by the failure analysis (Section~\ref{sec:failure})". But Section 5.8's own numbers list the weakest categories as RoadAccidents (87.14), Robbery (88.64), and Explosion (88.75), while Shooting is 95.67 -- 6th strongest of 13, well above mid-pack, not a category where "snippet pooling costs the most". Conversely Robbery (2nd weakest) is neither abrupt/short-event nor identified by the failure analysis. The two sets share only RoadAccidents and Explosion, so "exactly" is wrong in both directions and is checkable from the values quoted in the same chapter.

**Suggested fix:** Weaken "exactly" to a partial correspondence in both places, e.g. at line 543: "...are among the categories where snippet pooling costs the most" (or name only RoadAccidents and Explosion), and at line 595: "The weak tail overlaps the abrupt, short-event category set identified by the failure analysis (RoadAccidents, Explosion), though Robbery -- a sustained-event category -- also sits in it."

### M9. [FIXED c514213] `thesis/chapters/ch06_results_tta.tex:61` — "Gaussian noise at high severities is the deepest failure mode" is contradicted by the figure it describes and by the chapter's own Section 6.4 prose — JPEG compression is the lowest-AUC family on all four backbones

Line 60-62: "Third, the damage is uneven across families: Gaussian noise at high severities is the deepest failure mode, while brightness shift leaves the stream comparatively intact." This paragraph analyzes Figure 6.1 (source-only AUC of the gated fusion model). Verified against the tracked data (results/_coral_derisk/r1full_*.json + variants, 3-seed): the JPEG family mean is the lowest on ALL four backbones (CLIP 46.5, Base 40.0, SO400M 49.2, Giant 41.5) versus Gaussian (57.5, 56.8, 51.3, 58.8), and the worst individual cells are almost all JPEG cells. The chapter itself concedes this at line 333-334: "Gaussian noise is not the lowest-AUC family in absolute terms (several JPEG cells sit lower still)". The claim is only true for the visual-language stream specifically — the qualifier that the Figure 6.1 caption (line 44-45, "the most destructive condition family for the visual-language stream") and PROVENANCE.md row 12's canonical labeling both use, but which this sentence omits. A committee member comparing the sentence to the figure directly above it would catch the contradiction.

**Suggested fix:** Add the stream qualifier to match the figure caption and line 333: e.g. "Gaussian noise at high severities is the deepest failure mode for the visual-language stream (in absolute fused AUC several JPEG cells sit lower still, Section~\ref{sec:disc-results}), while brightness shift leaves the stream comparatively intact."

### M10. [FIXED c514213] `thesis/chapters/ch06_results_tta.tex:410` — Attribution slip in the LayerNorm-barrier argument: the episodic protocol is credited with showing "the problem is not adaptation volume", but the chapter's own Section 6.2 establishes the episodic protocol was structurally incapable of showing anything — the evidence cited is the continual protocol

Lines 410-412: "The per-video episodic protocol shows the problem is not adaptation volume either: even unlimited per-condition adaptation (continual protocol) moves nothing once the reachable parameters are limited to LN affines." This is internally inconsistent: lines 127-132 state the episodic protocol "was structurally incapable of showing an effect, in either direction" (adapted parameters never influenced a scored output), so it cannot demonstrate anything about adaptation volume. The colon clause itself names the continual protocol as the actual evidence. As written, the sentence subject contradicts the chapter's own protocol narrative — a logic error in the mechanism section a careful reader would catch.

**Suggested fix:** Change the subject: "The continual protocol shows the problem is not adaptation volume either: even unlimited per-condition adaptation moves nothing once the reachable parameters are limited to LN affines." (or "The episodic-to-continual comparison shows...")

### M11. [FIXED c514213] `thesis/chapters/ch07_discussion.tex:272` — Self-contradictory table note: footnote (a) says GS-MoE is 'Omitted from the main comparison' while GS-MoE is the first row of that very table; the exclusion actually applies to the fair-subset table.

Lines 271-273: '$^{a}$\,GS-MoE 91.58\,/\,82.89: ... Omitted from the main comparison only because its trained per-category mixture-of-experts head exceeds the single-GPU-class regime.' GS-MoE appears as row 1 of Table~\ref{tab:sota-full} (line 234) — the main comparison — and is only absent from the fair-subset Table~\ref{tab:sota-fair}. The wording is a stale artifact of the paper port: in paper/main.tex the condensed main-text comparison genuinely omits GS-MoE (footnote at paper/main.tex:414), but in the thesis the sentence contradicts the table it annotates.

**Suggested fix:** Change to 'Omitted from the fair-subset comparison (Table~\ref{tab:sota-fair}) only because its trained per-category mixture-of-experts head exceeds the single-GPU-class regime.'

### M12. [FIXED c514213] `thesis/chapters/ch07_discussion.tex:402` — '+13.2 points on the hardest corruption' mislabels the gain condition and breaks the thesis-canonical framing used everywhere else ('the condition that most collapses the visual-language stream'). *(independently found by 2 agents)*

Lines 401-402: 'improves \emph{corrupted-AUC} (robustness, not clean-benchmark AUC) on all four backbones (mean $+1.2$ points, up to $+13.2$ points on the hardest corruption)'. The +13.2 cell is SO400M Gaussian severity 5, which is NOT the hardest corruption in absolute terms — thesis/PROVENANCE.md row 12 records that JPEG cells have lower absolute corrupted AUC and explicitly forbids 'most-degraded'-style labels, mandating the canonical phrase 'the condition that most collapses the visual-language stream' (adopted thesis-wide in quick 260713-mkh, C4). Ch01:223, ch06:304-305, ch06:331-332, and ch09:55-56 all use the canonical phrase; this is the lone deviation, and it is factually misleading about which corruption is 'hardest'.

**Suggested fix:** Replace 'on the hardest corruption' with 'in the condition that most collapses the visual-language stream' to match ch01/ch06/ch09 and PROVENANCE row 12.

### M13. [FIXED 3c275e4] `thesis/chapters/ch07_discussion.tex:498` — The moved 'Positioning within the published landscape' paragraph (7.7.1) is a near-verbatim duplicate of the 'Competitiveness within the comparable regime' paragraph (7.6.1) now in the SAME chapter

Lines 498-521 repeat, with identical numbers and near-identical wording, what lines 407-429 already say a few pages earlier: (a) "our 78.7\% XD-Violence AP is on par with RTFM~\cite{tian2021rtfm} (77.81\%) and the I3D variant of MGFN~\cite{chen2023mgfn} (79.19\%)" vs 7.6.1's "our 78.7\% AP is on par with RTFM~\cite{tian2021rtfm} (77.81\%, ICCV 2021), MGFN's~\cite{chen2023mgfn} I3D variant (79.19\%)"; (b) the verbatim clause "clearest on XD-Violence AP and weakest on UCF-Crime AUC" appears in both (lines 421-422 and 511-512); (c) the CLIP-TSA hypothesis is repeated almost word-for-word, both ending "we do not isolate this experimentally" (lines 426-427 and 514-515); (d) lines 516-521 (EventVAD/LAVAD 7B/13B LLMs, 82.03/80.28 UCF, 64.04/62.01 XD) re-run the 'Compute honesty' paragraph at lines 447-459. This paragraph was written for the old structure where it lived a chapter away from the SOTA section (git show d5303f9:thesis/chapters/ch08_limitations.tex opens it with "Chapter~\ref{ch:07} ... places these numbers"); the recap made sense cross-chapter but is redundant within one chapter. Its own opening line, "we summarize the read here rather than repeating the tables", now reads as an unkept promise since the prose itself is repeated.

**Suggested fix:** Compress lines 498-521 to 2-3 sentences that state only the limitation-relevant conclusion (competitive on XD AP, trails the frozen-feature pack on UCF AUC, gap plausibly due to omitted temporal modeling) and point back to Section~\ref{sec:sota-positioning} / Tables~\ref{tab:sota-full},~\ref{tab:sota-fair} for the full read, dropping the repeated per-method number list and the duplicated EventVAD/LAVAD compute point.

### M14. [FIXED c514213] `thesis/chapters/ch07_discussion.tex:554` — 'AP's calibration dependence' (Section 7.7.3) contradicts the chapter's own statements that AP is rank-based and rewards only score ordering (Sections 7.7.2 and 7.4), and is technically incorrect — AP is invariant to monotone score transforms.

Lines 553-555: 'the residual Giant sensitivity suggests that AP's calibration dependence and XD-Violence's imbalanced categories still create a challenging optimization landscape'. Two subsections earlier (lines 525-527) the thesis states: 'The headline metrics are rank-based (AUC and AP), and rank-based metrics reward only the \emph{ordering} of scores, not their absolute values', and Section 7.4 (lines 150-151) states a rank-based metric 'is invariant to any monotone transformation of the scores'. AP depends only on the ranking (plus class prevalence), not on calibration, so 'calibration dependence' is a technical error a committee member can catch by juxtaposing 7.7.2 and 7.7.3. Note the same framing originates in ch04_experimental_setup.tex:93-96 ('AP ... is therefore more sensitive to score calibration') and paper/main.tex, so the fix should be coordinated across both spots.

**Suggested fix:** Replace 'AP's calibration dependence' with an accurate mechanism, e.g. 'AP's sensitivity to the ordering among the highest-ranked frames under XD-Violence's low anomaly prevalence' (and align the parallel sentence in ch04_experimental_setup.tex:94-96).

### M15. [OPEN] `thesis/frontmatter/acknowledgments.tex:10` — Bracketed placeholder text '[Acknowledgments to be written by the author.]' renders verbatim in the PDF on Roman page III

The acknowledgments body is exactly '[Acknowledgments to be written by the author.]' and it appears as-is in the built PDF (confirmed by rendering physical page 7 / Roman III). The file comment declares it a deliberate user-fill placeholder exempt from the Wave-0 no-placeholder rule, but the 誌謝 page is part of the mandatory NTUST R4 binding order and a bracketed placeholder in the bound copy would be caught instantly. Must be written before final submission. (The 推薦書/審定書 gray-text placeholder pages in recommendation.tex/approval.tex are the normal replace-with-signed-form workflow and self-document that; they are not separately reported.)

**Suggested fix:** Author writes the acknowledgments text before the final build/binding; keep this on the pre-submission checklist so the placeholder cannot ship.


## LOW (25)

### L1. [OPEN] `thesis/chapters/ch01_introduction.tex:182` — Section pointer mis-attributes the episodic-inertness diagnosis to Section \ref{sec:coral}, which actually lives in the preceding entropy-TTA section

The contributions preamble reads: "the six-strategy search, the NORM/CORAL eliminations, and the episodic-inertness diagnosis (Chapter~\ref{ch:06}, Section~\ref{sec:coral})". In ch06_results_tta.tex, sec:coral (line 183) labels "Feature-Statistic Restoration and the Strategy Search", which does contain the six-strategy search and NORM/CORAL eliminations — but the episodic-inertness diagnosis is the subsection "Episodic inertness and the continual protocol" (ch06 line 123) inside the earlier section "Entropy-Minimization TTA: TENT and SAR" (label sec:entropy-tta, ch06 line 67). The reference compiles but sends the reader to the wrong section for one of the three named items.

**Suggested fix:** Change the parenthetical to "(Chapter~\ref{ch:06}, Sections~\ref{sec:entropy-tta} and~\ref{sec:coral})" or simply "(Chapter~\ref{ch:06})".

### L2. [OPEN] `thesis/chapters/ch01_introduction.tex:205` — Awkward elliptical clause with missing comma in Contribution 2: "statistically indistinguishable visual-only and SO400M emerges"

The sentence reads: "whereas on XD-Violence's heterogeneous sources the four backbones are statistically indistinguishable visual-only and SO400M emerges as the clear leader only under gated fusion." "indistinguishable visual-only" is a nonstandard ellipsis (ch05 line 207 spells it out as "the four backbones' visual-only AP is statistically indistinguishable across seeds"), and the two independent clauses joined by "and" lack a comma, so the sentence momentarily parses as "indistinguishable visual-only and SO400M". The underlying claim itself is correct and consistent with Table 5.2 and the ch05 figure caption.

**Suggested fix:** Rephrase to: "...the four backbones are statistically indistinguishable when evaluated visual-only, and SO400M emerges as the clear leader only under gated fusion."

### L3. [OPEN] `thesis/chapters/ch02_related_work.tex:88` — British spelling "analyses" (verb) in a chapter that otherwise uses American -ize spellings throughout

Line 88: "AnomalyCLIP~\cite{zanella2024anomalyclip} analyses CLIP's latent space directly". The chapter consistently uses American spellings elsewhere (14 occurrences of -ize forms: "summarizes" line 142, "regularizers" line 29, "standardized" line 296, "minimization", "normalization", etc.), making the British verb form "analyses" a one-off inconsistency.

**Suggested fix:** Change "analyses" to "analyzes".

### L4. [OPEN] `thesis/chapters/ch02_related_work.tex:162` — Table 2.1 caption and lead-in claim it covers "the surveyed" WSVAD methods, but six surveyed methods are absent from the table

The caption (line 162: "Design-space summary of the surveyed weakly supervised VAD methods") and the lead-in (line 142: "Table~\ref{tab:rw-taxonomy} summarizes the surveyed WSVAD lineage") imply full coverage, yet Holmes-VAU~\cite{zhang2025holmesvau}, DSANet~\cite{yin2026dsanet}, GS-MoE~\cite{damicantonio2025gsmoe}, PiercingEye~\cite{leng2026piercingeye}, HyperVD~\cite{peng2024hypervd}, and Ghadiya et al.~\cite{ghadiya2024crossmodal} — all surveyed in Sections 2.1.4-2.1.5 — have no rows. This also slightly weakens the synthesis observation that additional signals are "predominantly textual ... or auditory" (line 149-150), since only one auditory method (HL-Net) actually appears in the table; a picky committee member could ask why the recent multi-modal methods discussed two paragraphs earlier are missing.

**Suggested fix:** Either qualify the wording (e.g. caption "Design-space summary of representative surveyed WSVAD methods" and lead-in "summarizes representative methods from the surveyed WSVAD lineage") or add rows for the six omitted methods.

### L5. [OPEN] `thesis/chapters/ch03_methodology.tex:22` — Figure 3.1 caption: singular 'the only trained component' for two trained modules (gated fusion + MIL head)

Caption reads "The gated fusion module---together with the MIL head, the only trained component---projects each modality...". Two modules are trainable (the body text at line 31 says "Only the fusion head and the anomaly-scoring head are trainable"), so the singular appositive is grammatically off and can be misread as claiming the fusion module alone is trained.

**Suggested fix:** Change to "---together with the MIL head, the only trained components---" or rephrase as "The gated fusion module and the MIL head (the only trained components)...".

### L6. [OPEN] `thesis/chapters/ch03_methodology.tex:249` — Eq. (3.6) leaves the smoothness term's bag scope and index range unstated, under the chapter's claim that all equations are stated exactly as implemented

The total loss is "$\mathcal{L} = \mathcal{L}_{\text{rank}} + \frac{\lambda_1}{T}\sum_{t=1}^{T} \left\| \mathbf{a}_t \right\|_2 + \lambda_2 \sum_i (a_i - a_{i+1})^2$". The following prose scopes only the sparsity term ("computed over the abnormal bag", line 255) but says nothing about which bag the smoothness sum runs over, and the index $i$ has no stated range. In src/losses/mil_loss.py both regularizers are applied to abnormal-bag scores only (scores_abn_real) with the temporal diff over positions 1..T-1. Since line 13-14 promises "All equations in this chapter are stated exactly as implemented in the released code", a reader checking against the code will find the smoothness scope undocumented.

**Suggested fix:** Add "both regularizers are computed over the abnormal bag" (or extend the existing sparsity sentence to cover smoothness) and bound the smoothness index, e.g. $\sum_{i=1}^{T-1}$.

### L7. [OPEN] `thesis/chapters/ch03_methodology.tex:359` — "guards against this" has no antecedent — the risk being guarded against (a corrupted skeleton) is only introduced after the phrase

The compressed paragraph reads: "...$w_{\mathrm{vl}}\!\to\!0$ when corruption destroys the visual stream's ability to separate snippets and $w_{\mathrm{vl}}\!\to\!1$ when it is unaffected. A skeleton-reliability gate $s = \ldots$ guards against this, where...". The preceding sentence describes the visual-reliability score, not the danger of routing toward a corrupted skeleton, so "this" dangles; the actual risk is only explained at the end of the sentence ("so the fusion does not lean on a skeleton that is itself corrupted"). The unpacked version at line 377 gets it right ("Routing toward the skeleton is only safe if the skeleton itself is clean.").

**Suggested fix:** Replace "guards against this" with an explicit object, e.g. "guards against rerouting toward a skeleton stream that is itself corrupted".

### L8. [OPEN] `thesis/chapters/ch04_experimental_setup.tex:93` — Imprecise metric claim: AP is asserted to be "more sensitive to score calibration" while AUC "depend[s] only on the relative ordering" — AP is equally invariant to monotone score transforms, and Chapter 5's own analysis says cross-video calibration errors hurt the pooled AUC too

Lines 93-97: "AUC is insensitive to class imbalance and score calibration, depending only on the relative ordering of anomalous versus normal frames; AP weights precision across the recall range and is therefore more sensitive to score calibration". Strictly, AP is also a pure ranking metric (invariant to any global monotone transform of scores), so "calibration" sensitivity is not what formally distinguishes it from AUC — the formal distinctions are class-prevalence dependence and heavy weighting of the top of the ranking. Moreover, the blanket "AUC is insensitive to ... score calibration" sits in tension with the thesis's own calibration narrative: ch05_results_fusion.tex:610 states pooled evaluation must "pay for cross-video calibration errors that per-category evaluation does not", i.e. cross-video miscalibration does reorder the pooled ranking and does affect AUC. An ML examiner could probe this apparent contradiction between Section 4.2.1 and Chapter 5. (The same "AP's ... sensitivity to score calibration" phrasing recurs at ch05_results_fusion.tex:375 and in the published paper, so this is a project-wide framing; flagged here only for the over-strong "depending only on the relative ordering" contrast.)

**Suggested fix:** Sharpen the contrast to the defensible properties, e.g.: "AUC is insensitive to class imbalance and weights all thresholds uniformly; AP depends on class prevalence and concentrates weight on the highest-ranked frames, making it more sensitive to small ranking changes among top-scored frames and to cross-video score-scale misalignment---a distinction that matters for the seed-sensitivity analysis in Chapter~\ref{ch:05}."

### L9. [OPEN] `thesis/chapters/ch04_experimental_setup.tex:154` — Overstated stochasticity: "each transform is driven by a seeded random generator", but only Gaussian noise actually consumes the RNG — JPEG, brightness, and motion blur are deterministic in the tracked implementation

Lines 152-155: "All four transforms are implemented with \texttt{numpy} and \texttt{cv2} only... and each transform is driven by a seeded random generator." In scripts/corruption.py only gaussian_noise uses the generator (line 68: noise = rng.normal(...)); jpeg_compression, brightness, and motion_blur each document "``rng`` is unused but present for uniform signature" (lines 78, 107, 137). The pipeline is thus more deterministic than claimed, but the sentence as written is factually wrong about 3 of the 4 transforms, and a reader cross-checking the cited module (which the chapter references by name twice) would notice.

**Suggested fix:** Replace with: "the one stochastic transform (Gaussian noise) is driven by a seeded random generator; the remaining three transforms are fully deterministic."

### L10. [OPEN] `thesis/chapters/ch05_results_fusion.tex:48` — In Tables 5.1/5.2 the printed "Best Δ" disagrees by 0.1 with the difference of the displayed cells in 5 of 10 rows (Δ computed from unrounded means, but no caption note says so)

UCF table (lines 44-51): Late Fusion "79.9$\pm$0.8" vs CLIP "78.9$\pm$0.4" gives 1.0 at displayed precision but prints "$\uparrow$+0.9"; Gated Fusion "82.5$\pm$0.4" vs "81.4$\pm$0.3" gives 1.1 but prints "$\uparrow$+1.2"; GF 2-Person "82.6$\pm$0.3" vs "81.3$\pm$0.5" gives 1.3 but prints "$\uparrow$+1.2". XD table (lines 68-74): Visual Only "76.8$\pm$1.0" vs "74.6$\pm$1.5" gives 2.2 but prints "$\uparrow$+2.3"; Late Fusion "65.7$\pm$0.5" vs "63.9$\pm$0.5" gives 1.8 but prints "$\uparrow$+1.9". The Δ values are evidently computed from unrounded 3-seed means (legitimate), but a reader recomputing from the displayed one-decimal cells gets a different value; the captions (lines 37, 61) do not disclose the convention.

**Suggested fix:** Add to both captions: "$\Delta$ is computed from unrounded seed means and may differ by 0.1 from the difference of the displayed (rounded) cells." (or recompute Δ from the displayed precision).

### L11. [OPEN] `thesis/chapters/ch05_results_fusion.tex:235` — "81--82\%-AUC visual streams" misstates the visual-only range (78.5 to 82.4)

The text reads: "The complementarity claim---that a 68.8\%-AUC skeleton stream improves fusion with 81--82\%-AUC visual streams---deserves scrutiny". Per Table 5.1, the UCF-Crime visual-only baselines span 78.5 (SigLIP2 Base) to 82.4 (SigLIP2 Giant), so two of the four streams fall outside the quoted "81--82\%" band, and the complementarity claim also covers the XD-Violence AP configurations that the phrase omits.

**Suggested fix:** Use the actual range, e.g. "78--82\%-AUC visual streams" or "much stronger visual streams (78.5--82.4\% AUC on UCF-Crime)".

### L12. [OPEN] `thesis/chapters/ch05_results_fusion.tex:292` — Sweep-winner gain "+3.72" disagrees at displayed precision with the quoted endpoints (74.69 − 70.98 = 3.71)

Lines 291-293 read: "reached 74.69\% AP in its 3-seed confirmation, $+3.72$ points over the sweep-era 3-seed baseline of 70.98\% AP". At the displayed two-decimal precision 74.69 − 70.98 = 3.71, not 3.72. Same unrounded-arithmetic artifact as the ablation-table Best-Δ columns; the parallel UCF claim on line 299 (82.12 − 81.98 = +0.14) is exact, making the 0.01 discrepancy here stand out.

**Suggested fix:** Either state "+3.71" to match the displayed endpoints, or keep +3.72 and quote endpoints at matching precision (e.g., 74.695/70.977 rounded consistently).

### L13. [OPEN] `thesis/chapters/ch06_results_tta.tex:276` — Table 6.2 caption attributes the brightness zeros to "the reliability gate", but the prose (lines 353-360) explicitly attributes them to a different mechanism (w_vl ≈ 1, nothing to route away from), reserving the gate s for blur/JPEG

Caption: "for motion blur, JPEG, and brightness the reliability gate keeps the fusion at the source model, so $\Delta\approx0$ by construction." The body text distinguishes two mechanisms: "For motion blur and JPEG compression ... the skeleton-trust gate $s$ drops to zero" versus "For brightness shift the visual stream remains reliable ($w_{\mathrm{vl}} \approx 1$), so there is nothing to route away from." Chapter 3 likewise defines "the skeleton-reliability gate $s$" as distinct from "the visual-reliability score $w_{\mathrm{vl}}$". The caption's blanket gate attribution for brightness is inconsistent with both.

**Suggested fix:** Reword the caption to e.g. "...for motion blur and JPEG the skeleton-trust gate disables rerouting, and for brightness the visual stream remains reliable, so $\Delta\approx0$ by construction."

### L14. [OPEN] `thesis/chapters/ch06_results_tta.tex:340` — "Three distinct aggregations appear in that sentence" has a dangling referent — the sentence containing +4.83/+8.95/+13.2 is three sentences back, with two intervening sentences about JPEG

Line 340-341: "Three distinct aggregations appear in that sentence, and we keep them explicit...". The three numbers (+4.83, +8.95, +13.2) appear in the sentence at lines 327-333, but two later-inserted clarifying sentences ("Gaussian noise is not the lowest-AUC family..." and "Under JPEG the skeleton cache is itself re-extracted...", lines 333-339) now sit between it and the back-reference, so "that sentence" grammatically points at the JPEG sentence, which contains no aggregations.

**Suggested fix:** Replace "in that sentence" with "in the breakdown above" (or move the two intervening JPEG sentences after the aggregation-disambiguation sentence).

### L15. [OPEN] `thesis/chapters/ch06_results_tta.tex:406` — Source line break after "NORM/" renders as "NORM/ CORAL-style" with a stray space after the slash in the built PDF (page 72), inconsistent with "NORM/CORAL" elsewhere in the thesis

Lines 406-407 end/begin as: "...restoration (Section~\ref{sec:coral}) shows the problem is not access: NORM/" + newline + "CORAL-style alignment operates...". LaTeX treats the newline as an interword space, so the PDF renders "NORM/ CORAL-style" — confirmed by text extraction of thesis/main.pdf page 72, whereas pages 23 and 24 (other chapters) correctly render "NORM/CORAL" with no space.

**Suggested fix:** Join into one source line: "NORM/CORAL-style alignment" (or use "NORM\slash CORAL-style" to allow a legal break).

### L16. [OPEN] `thesis/chapters/ch07_discussion.tex:330` — Fair-subset table lists UR-DMU (86.97) above MGFN-I3D (86.98), reversing descending UCF order and the ordering used in the full table.

Lines 330-331: 'UR-DMU~\cite{zhou2023urdmu}    & 2023 & 86.97 & 81.66 & ...' precedes 'MGFN-I3D~\cite{chen2023mgfn}   & 2023 & 86.98 & 79.19 & ...'. The caption of tab:sota-fair makes no sorting claim, but every other row is in descending UCF order and the full table (lines 244-245) correctly lists MGFN (86.98) above UR-DMU (86.97), so the two tables are inconsistent with each other by one adjacent swap.

**Suggested fix:** Swap the UR-DMU and MGFN-I3D rows in tab:sota-fair so both tables use the same descending order.

### L17. [OPEN] `thesis/chapters/ch07_discussion.tex:360` — \subsection{Positioning} is immediately followed by a bold run-in heading repeating the same word *(independently found by 2 agents)*

Line 357 is "\subsection{Positioning}" and the first paragraph (line 360) opens "\noindent\textbf{Positioning.} The central claim of this work is...", so the rendered page shows the heading 'Positioning' twice in a row. Pre-existing before the restructure (present in d5303f9), so not a seam artifact, but it is a visible cosmetic duplication in the audited chapter.

**Suggested fix:** Delete the run-in "\noindent\textbf{Positioning.} " and start the paragraph at "The central claim of this work...", keeping the other bold run-ins (Scope, Contribution axis, etc.) which do not duplicate a heading.

### L18. [OPEN] `thesis/chapters/ch09_conclusion.tex:74` — Missing non-breaking space in "Chapter \ref{ch:07}" — inconsistent with the file's own "Chapter~\ref" convention

Line 74-75 reads "We do not claim state-of-the-art benchmark performance --- Chapter\n\ref{ch:07} places the results honestly...". Every other chapter reference in this file uses a tie: "Chapter~\ref{ch:01}" (line 14), "Chapter~\ref{ch:07}" (lines 100 and 149). Without the ~, LaTeX may break the line between "Chapter" and the number "7".

**Suggested fix:** Change "Chapter \ref{ch:07}" to "Chapter~\ref{ch:07}" on line 74-75.

### L19. [OPEN] `thesis/chapters/ch09_conclusion.tex:100` — "attributes the residual gap ... largely to its temporal self-attention machinery" slightly overstates Chapter 7's hedged, two-component, non-isolated attribution

Lines 100-101: "the analysis in Chapter~\ref{ch:07} attributes the residual gap to CLIP-TSA largely to its temporal self-attention machinery". Chapter 7 is more careful in both places it makes this claim: ch07_discussion.tex:424-427 "we hypothesize that the residual gap to it stems from its temporal self-attention module and multi-crop aggregation ... but we do not isolate this experimentally", and ch07:512-515 "We attribute the residual UCF gap ... to the temporal self-attention and multi-crop aggregation it adds ... but we do not isolate this experimentally". The conclusion's "largely to its temporal self-attention machinery" (a) drops the multi-crop component and (b) adds a dominance qualifier ("largely") that Chapter 7 never establishes.

**Suggested fix:** Reword to match the hedge, e.g. "the analysis in Chapter~\ref{ch:07} attributes the residual gap to CLIP-TSA (without isolating it experimentally) to its temporal self-attention and multi-crop aggregation", or simply drop "largely".

### L20. [FIXED 3c275e4] `thesis/chapters/ch09_conclusion.tex:131` — 'the transductive limitation above' is a leftover intra-chapter pointer whose referent moved to Chapter 7

The Streaming reliability estimation item reads: "A causal, streaming estimate of the routing weight would discharge the transductive limitation above and upgrade the claim class from transductive to online". In the old ch08 (git show d5303f9:thesis/chapters/ch08_limitations.tex line 192, same wording) "above" pointed to the TTA-scope limitation section in the same chapter; that section is now Section 7.7.4 (sec:lim-tta) in Chapter 7. The only surviving in-chapter antecedent is the one-line RQ3 mention of "a transductive protocol" (line 58), so the pointer still weakly resolves but no longer points where it was written to point.

**Suggested fix:** Replace "the transductive limitation above" with "the transductive limitation (Section~\ref{sec:lim-tta})".

### L21. [OPEN] `thesis/chapters/ch09_conclusion.tex:154` — "XD-Violence provides audio annotations" — the dataset provides an audio track, not audio annotations

Line 154-155: "XD-Violence provides audio annotations that our visual-skeleton pipeline does not exploit". What XD-Violence ships is the audio stream/track (VGGish features in the audio-visual literature), not annotations of audio. The thesis itself uses the correct term elsewhere: ch02_related_work.tex:128 says "both exploiting XD-Violence's audio track, which purely visual methods (including ours) do not use." A committee member familiar with the dataset would notice the mislabel.

**Suggested fix:** Replace "audio annotations" with "an audio track" (or "audio streams"), matching the wording already used in Chapter 2.

### L22. [FIXED 3c275e4] `thesis/chapters/ch09_conclusion.tex:166` — Closing coda 'Together, these findings demonstrate...' now immediately follows nine Future Work paragraphs that the section explicitly disclaims as non-findings *(independently found by 2 agents)*

The coda reads: "Together, these findings demonstrate that the combination of skeleton dynamics and visual-language semantics ... advances our understanding ...". In the pre-move file (git show d5303f9:thesis/chapters/ch09_conclusion.tex) this paragraph directly followed the Code and Data Availability section, so "these findings" referred to the just-summarized results. After inserting Section 8.4 Future Work before it, the nearest antecedent content is a list of prospective items the section itself introduces with "none of the numbers below are results of this thesis" (line 97). "These findings" now points at non-findings.

**Suggested fix:** Rephrase the coda opening to re-anchor the antecedent, e.g. "Together, the findings of this thesis demonstrate..." or "In sum, the results presented in this thesis demonstrate...".

### L23. [OPEN] `thesis/frontmatter/abstract_zh.tex:14` — Ambiguous phrasing '於單一視覺串流崩潰最嚴重之條件' — 單一 placement invites the misreading 'the single visual stream', and it drops 語言 from 視覺語言串流

The Chinese abstract says '於單一視覺串流崩潰最嚴重之條件最高 +13.2 點' while the English abstract says 'up to +13.2 points in the condition that most collapses the visual-language stream' (fact sheet: 'the single condition that most collapses the visual-language stream'). 單一 is meant to modify 條件 (the single condition) but sits before 視覺串流, so a natural parse is '單一視覺串流' = 'the single visual stream'; the sentence also abbreviates 視覺語言串流 (used earlier in the same sentence) to 視覺串流. Numbers are consistent, so this is wording polish, not a factual divergence.

**Suggested fix:** Reword to '於視覺語言串流崩潰最嚴重之單一條件下最高 +13.2 點'.

### L24. [OPEN] `thesis/frontmatter/cover.tex:21` — \bfseries on the Chinese cover title is silently dropped — the bkai CJK font has no bold shape, so the Chinese title renders medium weight while the English title is bold *(independently found by 2 agents)*

cover.tex lines 21-23 request '{\fontsize{20}{26}\selectfont\bfseries 雙模態骨架與視覺特徵融合於弱監督暴力偵測：...}' but main.log line 1276 reports "LaTeX Font Warning: Font shape `C70/bkai/b/n' undefined (Font) using `C70/bkai/m/n' instead on input line 22". The rendered cover confirms the Chinese title is not bold while the 24pt English title directly below is bold. The same silent substitution applies to the \bfseries CJK headings in recommendation.tex/approval.tex (推薦書/審定書) and the 摘要 chapter head. Single-weight 標楷體 is the normal look for NTUST covers, so this is likely acceptable — but the request-vs-render mismatch is currently silent.

**Suggested fix:** Either accept single-weight 標楷體 and remove the ineffective \bfseries inside the CJK blocks (silences the warning), or enable faux-bold via CJKutf8's \CJKbold mechanism if a bold Chinese title is actually wanted.

### L25. [OPEN] `thesis/frontmatter/notation.tex:19` — Abbreviation 'BN' is listed in the Notation table but never used in any compiled chapter, contradicting the file's own inclusion rule

notation.tex line 19 lists 'BN      & batch normalization (BatchNorm) \\', and the file header (lines 3-4) states 'Abbreviations restricted to terms used in two or more chapters (verified by grep over thesis/chapters/)'. A word-boundary grep for 'BN' over thesis/chapters/*.tex returns zero matches (the chapters spell out BatchNorm/batch normalization instead). Every other spot-checked abbreviation (CORAL, NORM, FPS, COCO, WSVAD, VLM) does appear in 2+ chapters.

**Suggested fix:** Either delete the BN row from the abbreviations table, or use 'BN' at least where BatchNorm is discussed (e.g., the LN-vs-BN TTA contrast in Chapters 2/3) so the table entry is justified.
