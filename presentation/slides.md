# Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection: A Multi-Backbone Study

CGW '26 oral presentation · Paper #32 · Wei-Han Jeng, Chuan-Kai Yang (NTUST) · July 9–10, 2026, Hsinchu, Taiwan
10-minute talk + 2-minute Q&A. English slides; spoken transcript in Traditional Chinese (see `transcript_zh-TW.md`, also embedded in speaker notes).
Built by `scripts/build_talk_pptx.py` (vcc-main env). All numbers are 3-seed means from `paper/main.tex` Tables 1–3.

---

## Slide 1: Title  `[0:00–0:20]`

- **Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection: A Multi-Backbone Study**
- Wei-Han Jeng · Chuan-Kai Yang — National Taiwan University of Science and Technology
- CGW '26 · July 9–10, 2026 · Hsinchu, Taiwan · Paper #32

**Speaker Notes (zh-TW):** 各位老師、各位先進，大家好。我是臺灣科技大學的〔請自行帶入中文姓名〕，指導教授是楊傳凱教授。今天報告的題目是：結合骨架與視覺語言特徵的雙模態融合，應用於弱監督暴力偵測，以及跨骨幹網路的系統性研究。

---

## Slide 2: Violence detection with only video-level labels  `[0:20–1:05]`

- Frame-level annotation of surveillance video is prohibitively expensive → **weakly supervised** VAD: one label per video, trained with Multiple Instance Learning (MIL)
- Strong recent results build on frozen CLIP features — **appearance only**; violence (fighting, assault, collisions) is fundamentally about **motion**
- Deployment reality: cameras degrade — noise, blur, compression, lighting — while models assume fixed conditions

**Speaker Notes (zh-TW):** 先從問題背景說起。監視器影像的暴力偵測，最大的瓶頸在標註成本：整段影片標一個「有沒有暴力」的標籤很便宜，但標到每個影格幾乎不可行，所以主流是弱監督式作法，用 Multiple Instance Learning 只靠影片層級標籤學習。但現有方法多半只用單一視覺模態——例如 CLIP 特徵——只看外觀；而打架、攻擊這類暴力事件，本質上是「動作」。同時，實際部署還會遇到雜訊、模糊、壓縮等畫質劣化問題。

---

## Slide 3: Three gaps → three contributions  `[1:05–1:50]`

Gaps:
- Skeleton dynamics + vision-language features: **unexplored** in weakly supervised VAD
- Sensitivity of fusion to the **visual backbone**: never systematically studied
- Entropy-minimization TTA (TENT/SAR) targets BatchNorm — behavior on **LayerNorm** fusion heads unknown

Contributions:
1. **Gated dual-modal fusion** of frozen CTR-GCN skeleton + frozen VLM features; only a lightweight MIL head is trained
2. **Systematic study**: 4 backbones × 2 benchmarks × 3 seeds
3. **TTA analysis**: structural null result for TENT/SAR + a label-free *discriminative-reliability reweighting*

**Speaker Notes (zh-TW):** 我們看到三個缺口：第一，骨架動態與視覺語言特徵的融合，在弱監督 VAD 裡幾乎沒有被探索；第二，融合對視覺骨幹的選擇有多敏感，沒有系統性研究；第三，TENT、SAR 這類 entropy minimization 的 test-time adaptation 是為 BatchNorm 設計的，在 LayerNorm 架構上行不行，沒人驗證過。對應的就是本文三個貢獻：雙模態閘控融合、四種骨幹的系統性比較，以及 TTA 的深入分析與我們提出的 reliability reweighting。

---

## Slide 4: Architecture — two frozen streams, one trained head  `[1:50–3:05]`

*(Native-shapes rebuild of paper Fig. 1, swimlane layout)*

- **Skeleton stream (frozen)**: RTMPose (COCO-17 keypoints, top-2 persons) → CTR-GCN (NTU RGB+D 120 pre-trained, 4 streams) → 256-d snippet feature
- **Visual stream (frozen)**: frames @ ~1 FPS → CLIP / SigLIP2 backbone → concat mean+max pooling → 1024–3072-d snippet feature
- **Gated fusion + MIL head — the only trained parts**: 0.50–1.02 M params, < 5 min training per configuration on one RTX 4090
- 64-frame snippets; MIL ranking loss; dashed: test-time reliability reweighting (later)

**Speaker Notes (zh-TW):** 這是整體架構。輸入影片走兩條完全凍結的特徵路徑。上面是骨架流：先用 RTMPose 抽出每幀信心值最高的兩個人、十七個關鍵點，送進在 NTU RGB+D 120 預訓練的 CTR-GCN，對每個 64 幀片段得到 256 維骨架特徵。下面是視覺流：約每秒取一張影格，送進凍結的 CLIP 或 SigLIP2 骨幹，再用 mean 加 max pooling 聚合成片段特徵。兩條特徵進到中間橘色的閘控融合模組——這是全模型唯一需要訓練的部分，加上 MIL head 只有五十萬到一百萬個參數，在一張 RTX 4090 上訓練一組設定不到五分鐘。最後 MIL head 對每個片段輸出異常分數，以 MIL ranking loss 訓練。

---

## Slide 5: Gated fusion & MIL training  `[3:05–3:55]`

- Project each modality to a shared 256-d space with per-modality LayerNorm:
  `ŝ = LN_s(W_s s + b_s)`, `v̂ = LN_v(W_v v + b_v)`
- Per-dimension gate `g = σ(W_g[ŝ ‖ v̂] + b_g)`; fused: `f = LN_f(g⊙ŝ + (1−g)⊙v̂ + ŝ + v̂)`
- Residual keeps both modalities; the gate modulates their *relative* contribution
- MIL ranking loss on top-k snippet scores (k=3, margin 1) + sparsity + temporal-smoothness terms
- Baseline for comparison: **late fusion** — fixed equal-weight average of two per-modality heads

**Speaker Notes (zh-TW):** 閘控融合的細節：兩個模態各自線性投影到共享的 256 維空間，各接一個 LayerNorm；接著串接後用 sigmoid 產生逐維度的 gate，對兩模態做加權混合，再加上殘差保留雙方資訊，最後再過一層 LayerNorm。訓練用標準 MIL ranking loss：從異常袋與正常袋各取 top-k 分數拉開間距，再加上稀疏與時間平滑正則項。我們也保留固定等權重的 late fusion 作為對照。

---

## Slide 6: Study design  `[3:55–4:30]`

- **UCF-Crime**: 1,900 videos, 13 anomaly types · frame-level ROC-AUC
- **XD-Violence**: 4,754 videos, 6 violence types · frame-level AP
- 4 backbones: CLIP ViT-B/16 (512-d) · SigLIP2 B/16 (768-d) · SigLIP2 SO400M (1152-d) · SigLIP2 Giant (1536-d)
- All encoders frozen; seeds {42, 123, 2024}, mean ± std; identical splits/protocol everywhere
- † videos < 64 frames excluded (UCF test: 254 of 290 evaluated) — disclosed in paper

**Speaker Notes (zh-TW):** 實驗設計：兩個基準資料集——UCF-Crime 一千九百部影片、以 frame-level AUC 評估；XD-Violence 四千七百多部、以 AP 評估。視覺骨幹比較四種：CLIP ViT-B/16 和三種 SigLIP2，從 Base、SO400M 到 Giant。所有實驗固定三個隨機種子，回報平均加減標準差，切分與流程完全一致。

---

## Slide 7: Main results — fusion never hurts, and sets our headlines  `[4:30–5:45]`

UCF-Crime AUC (%) and XD-Violence AP (%), 3-seed mean±std (paper Tables 1–2, gated-fusion defaults):

| Variant | CLIP B/16 | SigLIP2 B/16 | SO400M | Giant |
|---|---|---|---|---|
| Skeleton only (UCF) | 68.8±2.8 (backbone-independent) | | | |
| Visual only (UCF) | 81.2±0.1 | 78.5±0.5 | 81.1±0.3 | 82.4±0.2 |
| Late fusion (UCF) | 78.9±0.4 | 77.2±2.0 | 79.1±1.3 | 79.9±0.8 |
| **Gated fusion (UCF)** | 81.4±0.3 | 79.0±0.1 | 81.3±0.3 | **82.5±0.4** |
| Skeleton only (XD) | 40.8±0.6 (backbone-independent) | | | |
| Visual only (XD) | 74.6±1.5 | 74.5±2.1 | 76.6±2.2 | 76.8±1.0 |
| Late fusion (XD) | 63.9±0.5 | 63.6±0.7 | 65.7±0.5 | 65.7±0.4 |
| **Gated fusion (XD)** | 76.5±0.9 | 74.5±0.9 | **78.7±0.9** | 76.8±2.8 |

- Headlines: **UCF-Crime 82.5% AUC** (SigLIP2 Giant) · **XD-Violence 78.7% AP** (SigLIP2 SO400M)
- Weak alone (68.8 / 40.8), useful together: gated fusion ≥ visual-only in **8/8** configs (6/8 strictly; mean +0.6 pp)
- Fixed-weight late fusion can *hurt* — it drags below visual-only on UCF

**Speaker Notes (zh-TW):** 主要結果。先看最上面：骨架單獨其實不強，UCF 只有 68.8 的 AUC、XD 只有 40.8 的 AP，遠低於視覺單模態。但重點是融合：閘控融合在全部八個「骨幹×資料集」組合裡，全都大於等於視覺單模態，其中六個嚴格更好——增益不大，平均約 0.6 個百分點，但方向非常一致。最好的結果：UCF-Crime 用 SigLIP2 Giant 到 82.5% AUC；XD-Violence 用 SigLIP2 SO400M 到 78.7% AP，這是我們的 headline。也請注意 late fusion：固定等權重常常反而比視覺單模態差，在 XD 上與閘控融合差距超過十個 AP 百分點。

---

## Slide 8: What the multi-backbone study shows  `[5:45–6:40]`

*(Figure: fig_backbone_comparison — UCF AUC and XD AP panels, 4 backbones × 3 variants)*

1. **Complementarity is small but consistent** — no configuration degrades; up to +2.1 AP (XD, SO400M)
2. **Gating matters** — input-dependent weighting beats fixed late fusion by >10 AP on every XD backbone
3. **Backbone preference is dataset-specific and emerges through fusion** — Giant leads UCF; on XD the four visual-only backbones are within seed variance, SO400M wins *only under gated fusion*

**Speaker Notes (zh-TW):** 把結果畫成圖更清楚。三個觀察：第一，骨架的互補性小而穩定，八組全部不退步；第二，閘控真的重要——它會依樣本動態決定信任哪個模態，late fusion 做不到；第三，骨幹偏好跟資料集有交互作用：UCF 偏好容量最大的 Giant，而 XD 上四個骨幹的視覺單模態表現在種子變異內難分高下，是閘控融合之後 SO400M 才明顯勝出。這提醒我們：挑骨幹不能只看通用 benchmark。

---

## Slide 9: Qualitative — fusion sees what each stream misses  `[6:40–7:05]`

*(Figure: fig_temporal_scores_talk — Fighting047, UCF-Crime, seed-42 run)*

- Gated fusion stays high through the whole fight — including the opening the visual stream misses — then drops on the trailing normal footage; skeleton alone barely reacts
- Scores step at 64-frame-snippet granularity
- NOTE: the paper's Figure 2 video (RoadAccidents127) is anti-aligned with its ground truth (worst fusion advantage among the 128 annotated anomalous test videos, 128/128, in-GT −0.74 gap; independently recomputed twice) — the talk deliberately uses Fighting047 instead (fusion gap +0.48 vs CLIP +0.15 / skeleton −0.01). Flagged as a paper erratum candidate.

**Speaker Notes (zh-TW):** 一個定性例子：UCF-Crime 的打架影片。紅色實線是閘控融合的分數：整段打鬥期間都維持高分——包括視覺單模態一開始漏掉的前段——事件結束後降回低分；骨架單獨則幾乎沒有反應。

---

## Slide 10: Where this sits — honest comparison  `[7:05–7:55]`

Comparable regime (frozen features · no text branch · single-GPU head):

| Method | Venue | UCF AUC | XD AP |
|---|---|---|---|
| CLIP-TSA | ICIP'23 | 87.58 | 82.19 |
| MGFN (I3D) | AAAI'23 | 86.98 | 79.19 |
| UR-DMU | AAAI'23 | 86.97 | 81.66 |
| Light-WVAD | Neurocomp.'24 | 84.7 | — |
| RTFM | ICCV'21 | 84.30 | 77.81 |
| **This work** | CGW'26 | **82.5** | **78.7** |
| Sultani et al. | CVPR'18 | 75.41 | — |

- **No SOTA claim** — competitive within this regime, clearest on XD AP (on par with RTFM / MGFN); UCF AUC trails the modern frozen-feature pack
- Text-aligned / fine-tuned leaders reach ~88–91 UCF AUC — the cost of components we deliberately excluded
- Training-free ≠ cheap: 7B/13B-LLM systems need heavy hardware — EventVAD (82.03/64.04) an 80 GB A800, LAVAD (80.28/62.01) dual RTX 3090; we match/exceed on one RTX 4090 with **+14 AP** on XD

**Speaker Notes (zh-TW):** 跟文獻比較，我們刻意誠實：在「凍結特徵、不用文字對齊、單卡可訓」的同級方法裡，XD 的 78.7 AP 與 RTFM、MGFN 相當；UCF 的 82.5 則落後這個級距所有的現代凍結特徵方法，我們不主張 SOTA。另一個值得注意的點：training-free 不等於便宜——EventVAD 用 80GB 的 A800、LAVAD 用雙張 RTX 3090，我們在單張 4090 上 UCF 持平或更好、XD 領先超過 14 個 AP。

---

## Slide 11: Test-time adaptation — a null result and a fix  `[7:55–9:05]`

*(Figure: fig_tta_comparison)*

- **UCF-Crime-C**: 4 corruption types × 5 severities × 3 seeds (20 conditions)
- **TENT / SAR**: adapt the head's 1,536 LayerNorm affine params → |ΔAUC| < 0.1 pp on *every* backbone.
  Structural: shift lives in frozen upstream features; AUC is a pure ranking metric
- **Discriminative-reliability reweighting** (ours): label-free, tuning-free, adapts **zero parameters** — when the visual stream's score spread collapses, scale it by `w = 1−(1−w_vl)·s` and lean on the corruption-robust skeleton stream
- **+1.21 pp mean** corrupted-AUC; positive on all 4 backbones on every seed; up to **+13.2 pp** where the visual stream collapses hardest (Gaussian, severity 5); ~0 elsewhere — the gate correctly declines to act. *Rescue, not blanket robustness.*

**Speaker Notes (zh-TW):** 最後是 test-time adaptation。我們在 UCF-Crime-C 上測試：四種劣化、五個嚴重度、共二十個條件、三個種子。第一個發現：TENT 和 SAR 只能更新融合頭裡 LayerNorm 的一千五百多個 affine 參數，結果每個骨幹的 AUC 變化都小於 0.1 個百分點——等於零。這是結構性的：分布偏移發生在凍結的骨幹特徵，而 AUC 是純排序指標。所以我們換個思路，提出 discriminative-reliability reweighting：完全不更新參數，監測視覺流分數的離散度，一旦崩塌，就把融合導向較耐劣化的骨架流。平均提升 1.21 個百分點，四個骨幹、每個種子全部為正；在視覺流崩最嚴重的高斯雜訊最高嚴重度可達 +13.2；其他劣化型態增益為零——代表 gate 正確地選擇不出手。這是「救援」而不是全面的 robustness。

---

## Slide 12: Conclusions & limitations  `[9:05–9:45]`

Findings:
1. Skeleton features are weak alone but give a **small, consistent complementary gain** on strong visual backbones — and never degrade them
2. **Backbone choice interacts with the dataset** and emerges through fusion → evaluate multi-backbone, not general benchmarks
3. Entropy TTA confined to LN affine updates **cannot move** our frozen rank-based detector; reliability reweighting can — when one modality stays healthy

Limitations: frozen design trails fine-tuned/text-aligned leaders · reweighting is transductive (whole-condition statistics) · 2 datasets, synthetic corruptions

Modular & efficient: swap in a new VLM by re-extracting features; the 0.5–1.0 M-param head retrains in < 5 min

**Speaker Notes (zh-TW):** 總結三點：第一，骨架特徵雖弱，卻能對強的視覺骨幹提供小而一致的互補增益，而且不會造成退步；第二，骨幹選擇與資料集有交互作用，且透過融合才顯現，多骨幹評估有其必要；第三，entropy TTA 只能動 LN 的 affine 參數，在我們這種凍結的排序式偵測器上推不動；reliability reweighting 可以，前提是至少一個模態仍然可靠。限制包括凍結設計的效能上限、reweighting 的 transductive 統計假設，以及只涵蓋兩個資料集與合成劣化。

---

## Slide 13: Thank you  `[9:45–10:00]`

- **Thank you — Questions?**
- UCF-Crime **82.5% AUC** · XD-Violence **78.7% AP** · corrupted-AUC **+1.21 pp** (mean)
- Wei-Han Jeng · austin60616@gmail.com · code & experiment configs to be released

**Speaker Notes (zh-TW):** 以上是今天的報告，程式碼與實驗設定將會公開。謝謝大家，歡迎提問。

---

## Slide 14: Backup (section divider)

- Backup slides — Q&A

---

## Slide 15 (B1): Full comparison incl. heavier-budget regimes

| Method | Venue | UCF AUC | XD AP | Setting |
|---|---|---|---|---|
| PI-VAD | CVPR'25 | 90.33 | 85.37 | frozen I3D; +text, +5 train-time modalities |
| DSANet | AAAI'26 | 89.44 | 86.95 | frozen CLIP; +text alignment |
| VadCLIP | AAAI'24 | 88.02 | 84.51 | frozen CLIP; +text alignment |
| EventVAD | ACM MM'25 | 82.03 | 64.04 | training-free 7B MLLM; 80 GB A800 |
| LAVAD | CVPR'24 | 80.28 | 62.01 | training-free 13B LLM; dual RTX 3090 |
| CLIP-TSA | ICIP'23 | 87.58 | 82.19 | frozen CLIP; no text |
| MGFN (I3D) | AAAI'23 | 86.98 | 79.19 | frozen I3D; no text |
| UR-DMU | AAAI'23 | 86.97 | 81.66 | frozen I3D; no text |
| Light-WVAD | Neurocomp.'24 | 84.7 | — | frozen I3D; no text |
| RTFM | ICCV'21 | 84.30 | 77.81 | frozen I3D; no text |
| **This work** | CGW'26 | **82.5** | **78.7** | frozen skeleton+CLIP/SigLIP2; no text |
| Sultani et al. | CVPR'18 | 75.41 | — | frozen C3D; no text |

- GS-MoE (ICCV'25, 91.58/82.89) omitted from the comparable block in the paper: per-category MoE head exceeds the single-GPU-class regime

---

## Slide 16 (B2): TTA breakdown & method detail

Reweighting: `w_vl = min(1, σ(s_test)/σ(s_clean))` (visual-score spread) · skeleton gate `s` from feature-shift ratio · visual scaled by `w = 1−(1−w_vl)·s`

Gain by corruption family (3-seed mean ΔAUC, averaged over 5 severities):

| Backbone | Gaussian | Motion blur | JPEG | Brightness |
|---|---|---|---|---|
| CLIP ViT-B/16 | +2.67 | 0.00 | 0.00 | +0.01 |
| SigLIP2 B/16 | +5.99 | 0.00 | 0.00 | 0.00 |
| SigLIP2 SO400M | +8.95 | 0.00 | 0.00 | 0.00 |
| SigLIP2 Giant | +1.69 | 0.00 | 0.00 | 0.00 |
| **Average** | **+4.83** | 0.00 | 0.00 | 0.00 |

- Zeros = the gate declining to act (visual still reliable, or skeleton also corrupted)
- Known caveat: spread proxy can over-route — one seed of SigLIP2-B/16 loses up to 3.2 pp at high-severity Gaussian (average across seeds still positive)
- Transductive: pools statistics over a whole corruption condition; streaming variant = future work

---

## Slide 17 (B3): Per-category behavior (exploratory)

*(Figure: fig_gating_distribution — per-category UCF AUC / XD AP, skeleton vs visual vs gated)*

- Exploratory, seed-42 single-run breakdown (not a paper figure; paper tables are 3-seed)
- XD categories: Fighting, Shooting, Riot, Abuse, Car Accident, Explosion

---

## Slide 18 (B4): Protocol details

- <64-frame videos excluded (172 UCF, 1 XD); UCF test: 254 of 290 evaluated — disclosed in paper §4.1
- 15% stratified validation split; checkpoint selection by validation MIL loss (no frame-level peeking)
- Frame-rate asymmetry: UCF distributed at ~3 FPS (64-frame snippet ≈ 20 s); XD native ~24 FPS (≈ 2.7 s) — a plausible factor in weaker UCF skeleton-only results
- Snippet→frame expansion: UCF final-snippet score repeated to full frame grid; XD evaluated on snippet-aligned portion
- λ₂ (temporal smoothness) = 8×10⁻⁴ on UCF, 0 on XD (over-regularizes heterogeneous rapidly-cut sources)
- Optimizer AdamW, lr 1e-4, warmup 5 epochs + cosine; batch 16 normal/anomalous pairs; bag T=32; top-k k=3
