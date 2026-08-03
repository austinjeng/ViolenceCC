# SCI Journal Placement Survey — 2026-08-03

**Subject:** `paper/main.tex` — "Dual-Modal Skeleton-Visual Fusion for Weakly Supervised
Violence Detection: A Multi-Backbone Study" (Jeng & Yang, NTUST), presented at CGW '26.
**Requested by:** thesis advisor (Prof. Chuan-Kai Yang) — survey of submittable SCI journals.
**Goal:** SCIE-indexed venue, Q2/Q3 target, Q1 evaluated honestly, minimal cost.

**Method:** 20 research agents over two workflows — discovery (`wf_a0ebe9a4-808`, 9 agents,
1.10M tokens, 774 tool calls) then adversarial verification (`wf_c783879f-d77`, 11 agents,
1.31M tokens, 784 tool calls). 133 distinct journals screened, 20 assessed in depth. The
verification pass was instructed to refute rather than confirm; it overturned nine
first-pass claims, all recorded in §9.

**Metrics vintage:** all impact factors and quartiles are **2025 JIFs from the JCR 2026
edition, released 17 June 2026**. Aggregators label the same number the "2026 impact
factor". Unambiguous phrasing for a committee: *"JIF released June 2026, 2025 citation
year."* Quartiles are **JCR per-category**, read from JCR journal profiles — not Scimago,
and not the "best category" headline aggregators print.

Rendered version: `.knowledge/journal-survey-2026-08-03.html`.

---

## 1. Two facts that reshape the decision

**There is no deadline.** The NTUST Information Management graduate regulations
(『國立臺灣科技大學資訊管理系研究所修業規定』, both currently-applicable versions —
113–114學年度 and 115學年度起) contain **zero** occurrences of 期刊, 發表, SCI, or 研討會.
There is no journal-publication requirement for the master's degree, and the oral defence
already passed (2026-07-29). This submission is for merit and career value, not a
graduation gate.

> Correction to a first-pass claim: the *doctoral* rule (a different document,
> 『資訊管理系博士學位候選人資格考試實施要點』, Art. 2) requires **one** article in
> SCI/SCI-E/SSCI/AHCI within 3 years, not on Beall's list, sole NTUST-IM affiliation,
> advisor named, student first author or immediately after the advisor. There is no
> two-paper rule and no "overseas-owned journal" clause. Irrelevant to a master's student
> either way, but the earlier version of this fact was wrong and should not propagate.

**Publishing costs nothing at most good targets.** Every Elsevier and Springer hybrid
journal has a subscription route; Elsevier states verbatim per journal: *"No publication
fee charged to authors."* The venues that cost money are the fully open-access ones
(IEEE Access, MDPI, IET, PeerJ). Cost should therefore carry ~zero weight when choosing
among the free options.

---

## 2. Recommended submission ladder

All three steps are Elsevier, so a rejection carries reviews forward via the Article
Transfer Service rather than restarting review.

| Step | Venue | JIF | Quartile | Cost | 1st decision |
|---|---|---|---|---|---|
| 1 | **Image and Vision Computing** | 5.0 | Q2 CS-AI 67/210 | $0 | 16 d (167 d to accept) |
| 2 | **Computer Vision and Image Understanding** | 3.6 | Q2 CS-AI 99/210 | $0 | 7 d (201 d to accept) |
| 3 | **Journal of Visual Communication and Image Representation** | 2.8 | Q2 CS-SE 59/128 | $0 | 15 d (215 d to accept) |

- **IVC** is the heaviest recent publisher of this exact problem (~9 genuine VAD papers
  2024–26, including weakly supervised and audio-visual). Its scope statement explicitly
  rewards quantitative evaluation and comparison. A failed attempt costs ~2 weeks.
- **CVIU** is the only venue whose aims-and-scope solicits *"papers offering insights that
  differ from predominant views"* — written for the TENT/SAR null. It published a WS-VAD
  paper framed as a **baseline** (Human-Scene Network, 2024, 85.30% UCF AUC). **Promote to
  step 1 only if** the LayerNorm-head instrumentation lands (see §7 item 7); CVIU rejects
  observations that are not mechanisms.
- **JVCIR** has the highest publication probability on the list. It published a 2025 paper
  that builds its own multiply-distorted video set, analyses data-quality impact on VAD,
  and makes no leaderboard claim — structurally the same paper as UCF-Crime-C. Go here
  *first* if a printed acceptance is ever needed on a fixed date, since even this
  "safe" venue takes 215 days to acceptance.

**Two alternatives:**

- **Signal, Image and Video Processing** (Springer, 2.7, Q3, $0) — advisor's most active
  SCIE venue (6 papers); 15+ video-anomaly papers/yr; verified 132–139 d received→accepted.
  Hard **10-page cap** forces shipping one contribution. Highest single-venue probability
  once reframed: ~55–65%.
- **IEEE Access** (4.2, Q2 ×3, ~4 wk, US$1,728 at NTUST rate) — reviewer guidelines state
  verbatim that articles *"are not necessarily expected to have a high level of novelty,
  but they should be distinct from previous publications and technically sound."* Real
  acceptance rate is **20%** per IEEE, not the 30% folklore. No page limit.

**Do not submit to Pattern Recognition Letters.** Q2 CS-AI on paper (102/210, 51.7 pct —
three ranks off Q3, and Clarivate's own JCI metric already places it Q3), but it published
**one** genuine VAD paper in 2024–2026 against nine or ten each at IVC/CVIU/JVCIR. Its
concision requirement also fights every upgrade the other venues demand, so the work does
not transfer.

---

## 3. Acceptance calibration — what actually cleared review

This paper: **82.5% UCF-Crime AUC / 78.7% XD-Violence AP**. All rows verified from the
paper record (Crossref, OpenAlex, Europe PMC full text, or the open preprint).

| Accepted paper | Venue | UCF AUC | XD AP | Note |
|---|---|---:|---:|---|
| Bameri et al., probabilistic modelling + ensemble | IET Image Processing 2025 | **80.86** | — | **Below ours.** Abstract calls it "competitive performance". DOI 10.1049/ipr2.70247 |
| LTGS-Net | Sensors 2025 | **82.33** | — | Indistinguishable from ours. DOI 10.3390/s25164884 |
| Hybrid-ConvATFM | Pattern Analysis & Applications 2025 | 84.91 | 83.51 | Closest above — 2.4 pp gap |
| Human-Scene Network — *"a novel baseline"* | CVIU 2024 | 85.30 | — | DOI 10.1016/j.cviu.2024.103955; table read from arXiv 2301.07923v1 |
| (WS-VAD acceptance) | The Visual Computer 2026 | 86.48 | — | |
| ViCap-AD — claims SOTA | Machine Vision & Applications 2025 | 87.20 | 85.02 | MVA's one recent WS-VAD acceptance was SOTA-claiming |
| RelVid (CLIP + text, frozen image encoder) | Sensors 2025 | 87.71 | 80.76 | No skeleton. DOI 10.3390/s25072037 |
| TAPL (temporal-aware prompt learning) | SIViP 2025 | 88.00 | 85.26 | Same journal/year as far softer acceptances — SIViP publishes at two tiers |
| VadCLIP++ | Digital Signal Processing 2025 | 88.12 | 85.03 | DOI 10.1016/j.dsp.2025.105560 |

**Read the spread, not the top.** Q2/Q3 journals demonstrably accept work at and below this
operating point — one 1.6 points below it. Accuracy is not the disqualifier. What
disqualifies a paper in this band is **presenting as a competitive detector and losing**.

**Framing principle (applies at every venue).** Three assets are publishable regardless of
the operating point, and none is the fusion architecture:

1. a controlled four-backbone comparison under one fixed head, one protocol, matched
   seeds — unpublished for WS-VAD, and the finding that the SO400M XD lead was seed noise
   is a real methodological result;
2. 3-seed mean±std reporting, above the norm in a single-seed-dominated field;
3. frozen backbones with a 0.5–1.0M-parameter trainable head → a defensible
   accuracy-per-cost claim.

---

## 4. Q2 targets

| Journal | Pub | JIF | JCR 2026 quartile (per category) | Cost | 1st dec. | Verdict |
|---|---|---:|---|---:|---:|---|
| Image and Vision Computing | Elsevier | 5.0 | **Q2 CS-AI 67/210**; Q1 CS-SE 23/128, CS-T&M 29/146, Optics 28/129 | $0 | 16 d | **Target** |
| IEEE Access | IEEE | 4.2 | Q2 ×3 — CS-IS 100/266, EE 124/369, Telecom 53/127 | $1,728 | ~4 wk | **Target** |
| Sensors | MDPI | 4.0 | Q2 ×3 — Instr 24/81, Chem-Anal 37/110, EE 127/369 | ~$3,210 | 17.8 d | Viable |
| Computer Vision and Image Understanding | Elsevier | 3.6 | Q2 CS-AI 99/210; Q2 EE 142/369 | $0 | 7 d | **Target** |
| Pattern Recognition Letters | Elsevier | 3.5 | Q2 CS-AI 102/210 (51.7 pct; JCI says Q3) | $0 | 17 d | Skip |
| The Visual Computer | Springer | 3.4 | Q2 CS-SE 44/128 — **not indexed in CS-AI** | $0 | 3 d | Viable |
| PeerJ Computer Science | PeerJ | 2.9 | Q2 CS-T&M 50/146; **Q3 CS-AI 121/210** | $1,510 | 30–35 d | **Target** |
| J. Visual Communication & Image Repr. | Elsevier | 2.8 | Q2 CS-SE 59/128; **Q3 CS-IS 149/266**; not in CS-AI | $0 | 15 d | **Target** |
| Multimedia Systems | Springer | 2.8 | Q2 CS-T&M 52/146; **Q3 CS-IS 149/266** | $0 | 41 d | Viable |

**Reading "first decision":** a 1–7 day median is a **desk-rejection statistic**, not fast
review. CVIU's 7 d sits against a 94 d decision-after-review median — the median submission
never reaches a referee. Treat low numbers as "title, abstract and cover letter decide the
outcome". The 30–41 d medians (MVA, Multimedia Systems) are evidence a submission is
actually read.

---

## 5. Q3 targets

Structural note: **IEEE has essentially no Q3 in this subject area** — its CS/EE titles are
almost all Q1 or Q2, so "Q2 and Q3" collapses to "IEEE Q2" inside that portfolio. Genuine
Q3 lives at Springer, Elsevier's mid-tier, and IET.

| Journal | Pub | JIF | JCR 2026 quartile | Cost | 1st dec. | Verdict |
|---|---|---:|---|---:|---:|---|
| Signal, Image and Video Processing | Springer | 2.7 | Q3 EE 186/369; Q3 Imaging Sci | $0 | 4 d | **Target** |
| Pattern Analysis and Applications | Springer | 2.6 | Q3 CS-AI 130/210 | $0 | **1 d** | High variance |
| IET Image Processing | Wiley/IET | 2.4 | Q3 ×3 — CS-AI 139/210, EE 215/369, Imaging 27/39 | $2,800 | 38 d | Viable if funded |
| J. on Image and Video Processing | Springer | 2.3 | Q3 both categories | $2,090 | 171 d | Viable |
| Signal Processing: Image Communication | Elsevier | 2.1 | Q3 EE 235/369 | $0 | — | Fallback |
| Machine Vision and Applications | Springer/IAPR | 2.0 | Q3 ×3 — CS-AI 148/210, Cybernetics 23/34, EE 243/369 | $0 | 30 d | Viable |
| ETRI Journal | ETRI/Wiley | 2.0 | Q3 EE 243/369; Q3 Telecom 93/127 | **$0** | unpublished | Skip |

- **SIViP** — SIViP's JIF is **2.7**, not 2.1; the 2.1 figure is the superseded 2024 JIF
  *and* is coincidentally SPIC's current JIF. Hard 10-page cap (10th page references only).
- **PAA** — its stated policy mandates replicable research, released code and data, and
  *"rigorous comparisons under identical conditions"*; this project over-delivers on all
  three, and PAA published a robustness **evaluation** study. But a 1-day median is the
  most aggressive desk filter in the entire survey. Bimodal bet.
- **IET Image Processing** — **best-documented venue in the survey**: publisher states
  **33% acceptance**, 38 d first decision, 131 d to acceptance, 279 articles in 2025. It
  accepted 80.86% UCF. Mandatory APC, no free route; the NTUST Wiley deal is
  **hybrid-only** and this is fully gold OA, so it does *not* qualify.
- **J. on Image and Video Processing** — renamed from *EURASIP Journal on Image and Video
  Processing* on 1 Jan 2026, new eISSN **3091-454X**. Searching Clarivate under the old
  ISSN 1687-5281 returns nothing, which is why it looks delisted and is not.
- **ETRI Journal** — genuinely free (no APC, submission fee, or page charge; DOAJ
  `has_apc: false`), but scope is information/telecom/electronics, 8–10 page hard cap,
  double-anonymous, no speed or acceptance figures published, and **no transfer network on
  rejection**. Not worth the desk-reject risk.

---

## 6. Q1 evaluated honestly

The belief "Q1 is out of reach" is **partly right, and the correction matters**. "Q1 ⇒ must
beat 88–90% AUC" holds at the prestige and video/multimedia tier. It does **not** hold at
the applications-oriented Q1 titles, whose bar is rigour plus application credibility.

| Venue | JIF | Quartile | Cost | Assessment |
|---|---:|---|---:|---|
| **Neurocomputing** | 6.7 | Q1 CS-AI 43/210 (79.8 pct) | $0 | **The one credible shot.** MIL is native vocabulary (it published a PyTorch MIL library); sustained VAD line. 8 d first decision, 139 d to acceptance — the fastest overall, so failure is cheap. But it pays for *methods*: needs disc_reweight formalised as an algorithm, an analytical BN-vs-LN adaptation contrast, ideally one non-VAD LayerNorm head. **~12–18% as-is, 25–30% reframed.** |
| **Expert Systems with Applications** | 9.4 | Q1 | $0 | Bar is application credibility. Published a 2025 violence-detection paper selling embedded deployability, not accuracy. Blocker is framing: a title reading "A Multi-Backbone Study" triggers its fastest desk reject ("application invisibility"). **~10% as-is, 30–40%** after an application-first rewrite with a deployment figure, operational metrics, accuracy-vs-compute Pareto. **Engineering Applications of AI** (9.0) is a near-identical alternate — one manuscript serves both. |
| IEEE TCSVT | 10.8 | Q1 EE 13/369 | $0 + $110–175/pg | No. Most on-topic IEEE venue ⇒ bar set by its own publications. Mandatory over-length charges. |
| IEEE TMM | 9.9 | Q1 ×3 | $0 + $220/pg >8 | No. Where audio-visual VAD lives — every reviewer asks why XD-Violence audio was unused. |
| Pattern Recognition | 9.1 | Q1 | $0 | No — bar, plus the prior-art collision in §8. |
| TIP 15.3 · IJCV 10.3 · TPAMI 20.4 · Information Fusion 17.4 | — | Q1 | $0 | Closed. Expect novel formulation with theoretical depth; below-SOTA is disqualifying; no slot for empirical studies or standalone negative results. |

**Recommendation:** if a Q1 line matters, take Neurocomputing **instead of** CVIU, not
before it — the 8-day desk median makes failure cheap, but the two require incompatible
reframes (adaptation-algorithm-first vs. insight-first), so serial attempts cost real
rewriting.

Also noted by the completeness pass: **Machine Learning** (Springer, Q2 CS-AI 67.1 pct,
JIF 4.9, free subscription route) is the one venue where the TENT/SAR null is an asset
rather than a liability. A genuine reach, but on record. The venues that formally
institutionalise negative results — TMLR, ReScience C, NeurIPS/ICLR reproducibility
tracks, Cambridge *Experimental Results* — are all outside JCR and therefore ineligible.

---

## 7. Traps and exclusions

### 7.1 MTAP is no longer SCI — raise with the advisor

**Multimedia Tools and Applications** was removed from the Web of Science Core Collection
in Clarivate's **October 2024** update. Searching ISSN 1380-7501 on the Master Journal List
returns *"Found 0 results"* while a positive control (ISSN 0028-0836 → Nature) returns an
exact match in the same session; Springer's own indexing list no longer names SCIE; both
wos-journal.info and Retraction Watch corroborate. No JIF, no quartile. Still Scopus- and
EI-indexed and still publishing.

This matters because MTAP is Prof. Yang's dominant venue: **15 of his 40 DBLP-indexed
journal papers** (37.5%), 2008–2026, including one *after* the delisting. If the lab default
is to send multimedia work there, that default no longer produces an SCI paper. SIViP has
already absorbed the overflow and is his active SCIE outlet (6 papers, incl. 2024 + 2025).

*Unverified:* the exact JCR edition in which coverage was lost. Status is established;
timing is not. Confirm via JCR through the NTUST library if a date is needed for paperwork.

### 7.2 The ESCI trap

Since JCR 2023, ESCI journals carry JIFs and quartiles, so metrics sites render them
identically to SCIE titles. Verified individually on the Master Journal List with all four
index filters active and positive/negative controls in-session:

| Journal | JIF | Advertised | **Actual index** |
|---|---:|---|---|
| Journal of Imaging (MDPI) | 3.8 | "JCR-Q2" | **ESCI** |
| Big Data and Cognitive Computing (MDPI) | 5.3 | "JCR-Q1" | **ESCI** |
| Information (MDPI) | 4.3 | "JCR-Q2" | **ESCI** |
| Frontiers in Computer Science | 3.4 | — | **ESCI** |
| PeerJ Computer Science | 2.9 | — | **SCIE** (an earlier ESCI claim was wrong) |
| Sensors / Applied Sciences / Electronics (MDPI) | 4.0 / 2.9 / 2.9 | — | **SCIE** |

MDPI's own pages disclose this: they write "SCIE (Web of Science)" for Sensors/Applied
Sciences/Electronics and "ESCI (Web of Science)" for the four above. This is costly —
**Journal of Imaging is the single best topical match found in the whole survey**, having
published two CLIP-based weakly supervised VAD papers on exactly UCF-Crime and XD-Violence
(incl. TE-VTAF 2026 at 88.93% / 85.62%). **Confirm with the department whether its rule is
"SCIE" or "JCR-indexed with an IF"** before ruling it out.

### 7.3 Coverage status of at-risk journals (verified 2026-08-03)

| Journal | Status |
|---|---|
| Multimedia Tools and Applications | **Delisted** from WoS Core, Oct 2024. No JIF/quartile. |
| Neural Computing and Applications | **Delisted** — zero MJL hits on both ISSNs (0941-0643 / 1433-3058), no SCIE on Springer's own list, no IF displayed. No Clarivate announcement found. *Have the library confirm in JCR before final reliance.* |
| Journal of Ambient Intelligence and Humanized Computing | Out of WoS Core entirely — no JIF, no quartile, no coverage. |
| Soft Computing | Still SCIE, but flagged **On Hold** by Clarivate (under re-evaluation; new content not indexed during review). |
| Alexandria Engineering Journal | **On Hold** in WoS *and* no Scopus CiteScore 2025 while controls populate. High risk both databases. |
| Heliyon | **Cleared** — on hold Sept 2024, but listed under SCIE today with no hold flag. Not delisted (a first-pass claim was wrong). Weak CS reputation is a separate matter. |

### 7.4 The best-category headline

Aggregators print a multi-category journal's *best* quartile. **Image and Vision Computing**
is widely listed as Q1 — Q1 in Software Engineering, Theory & Methods and Optics, but
**Q2 in CS-AI**, the category anyone assessing a vision paper looks up, where it has been
Q2 every year since 2013. Same trap: JVCIR, Multimedia Systems, PeerJ CS (all Q2 in one
category, Q3 in another). Determine which category NTUST reads.

Related: JCR vs SJR disagree by one level on several titles (IET Image Processing is Q3 JCR
/ Q2 SJR; SPIC likewise). Confirm which system the committee uses.

### 7.5 Venues that fail the Q2/Q3 goal

- **Journal of Information Science and Engineering** (Academia Sinica) — SCIE, free, and
  the advisor published there twice (2007, 2008), but **Q4** (CS-IS 228/266, JIF 0.9, down
  18.2%) plus **US$100 per page beyond 12**. Safety net only; argue on accessibility, never
  quartile.
- **IET Computer Vision** — **Q4** both categories, JIF 1.4. Far weaker than IET Image
  Processing despite the name.
- **Journal of Electronic Imaging** (SPIE) — Q4 all three, JIF 1.0.
- **IEICE Trans. Inf. & Syst.** (0.8), **KSII TIIS** (1.0), **IJPRAI** (0.9) — all Q4.

---

## 8. Prior art that must be cited

> **Chen, Cao, Liu, Liu, Zhao, Liu — "Cross-modal attention fusion of RGB and skeleton for
> multimodal-driven video anomaly detection." *Pattern Recognition* **179**, art. 113815.
> DOI `10.1016/j.patcog.2026.113815`. Online 21 Apr 2026; print Nov 2026.**

Existence confirmed via Crossref (exact title, container, volume, article number, 54
references) and OpenAlex (date, affiliations: SJTU / Wuhu Inst. Tech. / Anhui Polytechnic;
corresponding author Boan Chen). **Its reported numbers could not be retrieved** —
ScienceDirect returned 403 to WebFetch, blocked headless Chromium and a real-Chrome profile
with bot-detection references, the jina proxy hit a CAPTCHA, and Crossref / OpenAlex /
Semantic Scholar all carry no abstract.

**Action: pull the PDF via the NTUST library and read it before submitting anywhere.**
Unaddressed, this is blocking prior art in a Q1 venue for what a reviewer will read as this
paper's core idea.

Differentiators to state explicitly: it fuses RGB + skeleton, this work fuses a frozen
**vision-language** backbone + skeleton; both encoders frozen with 0.5–1.0M trainable
parameters; four backbones compared under one protocol; corruption robustness and TTA,
which it does not address.

Two further sweep results:

- **Skeleton ST-GCN + MIL on UCF-Crime**, *Smart Media Journal* 15(6):130, 2026, DOI
  10.30693/smj.2026.15.6.130 — skeleton-only weakly supervised, **0.8368 AUC**, above 82.5%.
  Not SCIE, so not a venue signal, but a citation not to be caught missing.
- **Shin et al., IEEE Open J. Computer Society 2025** (DOI 10.1109/ojcs.2024.3517154) — often
  surfaced as skeleton prior art; it is **not**. RGB + optical flow + audio, no pose modality
  (90.26% UCF / 88.28% XD). Cite as multimodal WS-VAD, not skeleton work.

---

## 9. Cost reality for an NTUST corresponding author

Read verbatim from the NTUST library OA page (**library.ntust.edu.tw** — note: *not*
lib.ntust.edu.tw). **Every arrangement requires the corresponding author to be
NTUST-affiliated** — settle authorship roles before submission.

| Publisher | NTUST arrangement | Effect |
|---|---|---|
| Springer Nature | Free APC on **hybrid** journals. 「2026年52篇(截至 7/21 剩餘：3篇)、2027年53篇」 | 2026 quota effectively exhausted; page unrefreshed for ~2 weeks. Moot — subscription route is already free. |
| Wiley | Free APC on **hybrid** journals; 29 slots 2026, 30 in 2027 | Does **not** cover IET Image Processing (fully gold OA, not hybrid). |
| Elsevier | 10% discount only, no free slots | Moot — take the subscription route, pay $0. |
| IEEE | US$1,728 gold OA / US$2,240 hybrid | IEEE Access drops $2,160 → $1,728; no over-length charge at Access. |
| MDPI | **No library subsidy.** NTUST is an MDPI IOAP participant (since 2020-07-30) but billing is "non-central: invoiced to author", discount undisclosed. | Budget near list. |
| Cambridge · IOP · ACS | Full waivers / coverage | No relevant venues. |

**Out-of-pocket by target:**

- **$0** — IVC, CVIU, JVCIR, PRL, Neurocomputing, SPIC (Elsevier hybrid, verified against
  Elsevier's `article-publishing-charge.xlsx`, "Prices as of 09-Apr-2026"); SIViP, The
  Visual Computer, Multimedia Systems, MVA, PAA (Springer hybrid, *"no APC charges apply"*);
  ETRI Journal (genuinely free); JISE base rate.
- **$1,510** — PeerJ CS via 2 × Lifetime Basic @ $755 (**all** authors need one). Flat APC is
  **$2,155**; DOAJ's $1,395 is stale.
- **$1,728** — IEEE Access at NTUST rate. *Check Prof. Yang's IEEE membership grade:*
  Society member = further 20%, plain member 5%, student grade 0%.
- **$2,090** — J. on Image and Video Processing · **$2,800** — IET Image Processing
  (mandatory) · **~$3,210** — Sensors (CHF 2,600 at 1 CHF ≈ 1.236 USD; every aggregator
  converts 1:1, understating by ~24%).

**Send one email before writing anything.** Ask the library, in writing: (a) does the Wiley
agreement cover IET-branded titles, specifically IET Image Processing, ISSN 1751-9667;
(b) does the library hold an IEEE institutional deposit account for Access APCs; (c) is any
Springer 2026 quota actually left. Ask Prof. Yang whether NSTC project funds cover APCs — in
Taiwan they usually do, which would put IET Image Processing back in play as the best
topical fit in the survey.

---

## 10. Manuscript upgrades, ranked by cross-venue return

Named independently by multiple venue assessments.

1. **Matched-protocol baseline re-runs.** Re-run Sultani-MIL and RTFM inside our harness —
   same splits, snippet count, 3 seeds, 64-frame exclusion rule — reported beside 82.5%.
   Converts the fatal framing *"82.5 vs 88–91 reported"* into *"under identical protocol,
   ours vs their reproduction"*, which is also the honest comparison given the known RTFM
   repro gap (see memory `project_xd_sweep_deferred`). **Nothing else moves the odds this
   much, and it serves every venue at once.**
2. **External baseline under corruption.** +1.2 pp mean / +13.2 pp max is currently our
   method vs. our own model on our own benchmark. Run one reimplemented external baseline
   over the identical corrupted feature caches. If reweighting lifts a baseline too it is a
   method; if only ours, a tuning artifact. Demanded at every venue.
3. **Add ShanghaiTech.** Cheapest kill for the "only two datasets" objection. Mandatory at
   IET Image Processing, where every VAD paper reports 3–5 datasets.
4. **Online/causal TTA variant** reported alongside the transductive one. Whole-condition
   pooled statistics are attackable as a test-set statistics leak — fatal at Q1, awkward
   anywhere.
5. **Accuracy-per-cost Pareto.** Trainable params, total params, FLOPs/snippet, peak VRAM,
   training wall-clock, inference FPS — ours ×4 backbones plus published competitors. Puts
   us on a frontier instead of the bottom of a leaderboard. No new training.
6. **Paired significance tests throughout** (the 8/8 sign test at p=0.008 is the right
   instinct — extend systematically, report effect sizes and CIs), plus the **full
   20-condition distribution** rather than mean and max. A +13.2 pp max beside a +1.2 pp
   mean invites a cherry-picking charge that owning the variance defuses.
7. **Mechanism for the TTA null** — required for CVIU and The Visual Computer. Instrument
   the LayerNorm head: gradient magnitude reaching the affine parameters, entropy
   before/after adaptation, fraction of snippet scores whose rank flips, plus a
   BatchNorm-equipped control proving the null is structural, not a tuning failure. Harness
   exists (`scripts/_tmp_tta_harness.py`).
8. **Fix the Figure 2 erratum** — RoadAccidents127 is anti-aligned with GT; use Fighting047
   (already tracked in memory `project_cgw_talk_2026-07-07`).

### Prior publication: CGW '26 is non-archival

CGW 2026's own call for papers, verbatim:
> 「投稿至Regular Paper的論文須為全新未經發表的論文，經審查後錄取之論文內容將只會在大會上由報告者自行公開，不會收錄於網頁或是會議手冊上。」

No proceedings, no DOI, no ACM DL or IEEE Xplore record; the same clause appears in CGW
2025's CFP, so it is standing policy. **We are extending an unpublished talk, not an indexed
paper** — no duplicate-publication rule is triggered and no formal new-material quota
applies. No CGW journal special issue or fast-track exists either.

Disclose it in the cover letter regardless; Elsevier's ethics policy explicitly exempts
*"an abstract or as part of a published lecture or academic thesis or as an electronic
preprint"*, covering both the talk and the 128-page thesis. Where a journal states its own
threshold (Computers & Graphics and The Visual Computer both say 30% new content), meet it
anyway — the thesis supplies far more than enough.

> One agent asserted the CGW paper is indexed in the ACM DL and treated it as prior
> publication. That is contradicted by CGW's own CFP quoted above. Primary source wins,
> but if an ACM DL record ever surfaces, this subsection changes.

---

## 11. Confidence and what stayed unverified

**Verified against primary sources:** all SCIE-vs-ESCI determinations (Clarivate MJL with
all index filters active, positive and negative controls in-session); all per-category JCR
ranks (JCR journal profiles); Elsevier APCs (publisher price file, 09-Apr-2026); Springer
APCs and publishing models (per-journal pages); NTUST library terms (verbatim, in Chinese);
NTUST IM regulations (both PDFs read); CGW CFP (verbatim); advisor's DBLP record (XML).

**Publisher-stated acceptance rates exist for only three venues in the entire survey:**
IET Image Processing (33%), IEEE Access (20%), PeerJ CS (33%). Every other acceptance-rate
figure in circulation is an aggregator estimate; none is quoted here.

**Unverified, explicitly:**

- The *Pattern Recognition* 2026 paper's reported numbers — every retrieval route blocked.
- The exact date/edition MTAP lost SCIE coverage (status established, timing not).
- Neural Computing and Applications' delisting mechanism — no announcement behind it.
- ETRI Journal's and PeerJ CS's review speed and acceptance rate — publishers do not
  publish them.
- MDPI per-journal acceptance rates — rendered in a JS widget behind bot protection.
- Whether NTUST's Springer agreement extends to fully-OA Nature Portfolio titles.

**Corrections made by the verification pass** (first-pass claim → truth): Neurocomputing
first decision 27 d → **8 d**; its ~47–50% acceptance rate → **not publisher-stated at all**;
PeerJ CS ESCI → **SCIE**; PeerJ APC $1,395 → **$2,155**; Heliyon delisted → **not delisted**;
SIViP JIF 2.1 → **2.7**; JISE "viable Q2/Q3" → **Q4**; the 88.12/85.03 numbers attributed to
Neurocomputing → **Digital Signal Processing**; NTUST doctoral rule "two papers, one
overseas" → **one paper, no overseas clause**; NTUST master's "no requirement" → confirmed;
CGW archival → **non-archival**; advisor MTAP count ~12 → **15 of 40**.

---

*Survey compiled 2026-08-03. Verify any figure against Clarivate JCR through the NTUST
library subscription before quoting it in a cover letter, committee document, or funding
form.*
