# 碩士論文研究專案：產品需求文件 (PRD)

## 結合人體骨架與視覺語意之弱監督暴力事件偵測：兼論 Source-Free 測試時適應在跨場景部署下的有效性

---

**文件版本**：v2.3（骨架權重實證確認版）
**建立日期**：2026 年 3 月
**硬體限制**：單張 NVIDIA RTX 4090（24GB VRAM）
**時程限制**：12 週（3 個月）
**人力限制**：單人研究

> **新穎性宣稱 A**（主線）：據我們所知，尚未見到同時整合 skeleton GCN 與 VLM semantic cues 的 violence-oriented weakly supervised anomaly detection framework；本研究進一步探索加入 open-vocabulary object detection 作為第三模態的可行性。

> **新穎性宣稱 B**（副線）：系統性評估 TENT/SAR-style entropy-minimization adaptation 在 violence-oriented weakly supervised VAD 的 LN-based fusion head 上的有效性，填補現有文獻中針對多模態暴力偵測框架缺乏 source-free TTA 系統研究的空白。

---

## 目錄

1. [專案概覽與研究動機](#1-專案概覽與研究動機)
2. [研究目標與新穎性宣稱](#2-研究目標與新穎性宣稱)
3. [任務定義與研究範圍](#3-任務定義與研究範圍)
4. [資料集選擇與完整規格](#4-資料集選擇與完整規格)
5. [系統架構總覽](#5-系統架構總覽)
6. [主線模組一：骨架圖卷積網路（Skeleton GCN）](#6-主線模組一骨架圖卷積網路skeleton-gcn)
7. [主線模組二：視覺語言模型語義增強（CLIP）](#7-主線模組二視覺語言模型語義增強clip)
8. [副線模組三：物件偵測（YOLO-World）](#8-副線模組三物件偵測yolo-world)
9. [多模態融合設計](#9-多模態融合設計)
10. [測試時適應（TTA）](#10-測試時適應tta)
11. [訓練協議與超參數規格](#11-訓練協議與超參數規格)
12. [評估協議、指標與基線方法](#12-評估協議指標與基線方法)
13. [十二週實作時程表](#13-十二週實作時程表)
14. [風險評估與後備計畫](#14-風險評估與後備計畫)
15. [GPU 資源預算與計算成本分析](#15-gpu-資源預算與計算成本分析)
16. [最終交付成果清單](#16-最終交付成果清單)
17. [論文章節結構與寫作規劃](#17-論文章節結構與寫作規劃)

---

## 1. 專案概覽與研究動機

### 1.1 問題陳述

實世界開放場景中的暴力事件（如攻擊、打鬥、持武器襲擊），是影片異常偵測（Video Anomaly Detection, VAD）領域的核心關注目標之一。現有 VAD 方法多依賴 RGB 外觀特徵或預擷取的 I3D/C3D 時序特徵，在面對不同攝影機場景、光照條件、拍攝角度的變化時，性能往往顯著下降。

人體姿態（骨架）資訊天然適合捕捉暴力動作的運動模式——它不受衣著、膚色、背景等外觀因素干擾。與此同時，視覺語言模型（VLM）如 CLIP 所提供的場景級語義理解能力，能夠捕捉骨架資訊無法表達的環境語境。然而，目前的暴力偵測研究尚未充分探索將這兩種本質互補的資訊源整合於弱監督 VAD 框架中的可能性。

此外，現有 VAD 方法在訓練域與部署域之間存在顯著的域偏移問題（domain shift），但 VAD 領域對於 source-free 測試時適應（TTA）的研究極為有限——尤其是針對多模態暴力偵測框架中 normalization-based TTA 方法的系統性評估幾乎空白。

### 1.2 解決方案概述

本專案提出一個以骨架 GCN 與 CLIP 語義特徵為核心的雙模態融合框架，用於弱監督暴力事件異常定位。主線設計以 skeleton branch 捕捉人體動態、CLIP branch 捕捉場景語義，兩者在共同嵌入空間中融合後輸出 frame-level 異常分數。在此基礎上，本專案進一步引入 source-free TTA 機制，評估其在跨場景部署時的泛化改善效果。

物件偵測（YOLO-World）作為第三模態的加入，定位為可選增強模組（optional enhancement），視主線進度決定是否正式整合或僅作為消融分析。

### 1.3 限制條件總覽

| 限制項目 | 具體規格 | 影響 |
|---------|---------|------|
| 硬體 | 單張 NVIDIA RTX 4090，24GB VRAM | 模型大小與批次量限制 |
| 時間 | 12 週（84 天） | 實驗規模與消融深度限制 |
| 人力 | 單人（碩士研究生） | 無法平行處理多項工作 |
| 研究等級 | 碩士論文 | 需合理貢獻但非頂會突破性創新 |
| 場景範圍 | 開放場景 / 實世界暴力事件 | 涵蓋 CCTV、新聞、電影等多種來源 |
| 行為範圍 | 暴力相關異常事件 | 以 fighting、assault 為核心，不排除 benchmark 中其他暴力子類 |

### 1.4 版本演進紀錄

**v1.0 → v2.0 的核心變化**（基於第一輪外部研究專家審核）：任務定義統一為 weakly supervised violence anomaly localization；研究範圍從「戶外公共場所」放寬為「開放場景」；新穎性宣稱移除絕對性措辭；主線從三模態收斂為 Skeleton + CLIP 雙模態；時程乘以工程不確定性係數。

**v2.0 → v2.1 的核心變化**（基於第二輪外部研究專家審核）：修正 skeleton encoder 訓練策略的方法論漏洞（從 supervised fine-tune 改為凍結預訓練特徵抽取器）；新增完整的 validation / early stopping protocol；將 XD-Violence 骨架擷取排入時程關鍵路徑；鎖死 TTA 的 adaptation protocol（更新參數範圍、batch 組成、統一實驗規格）。

**v2.1 → v2.2 的核心變化**（基於第三輪外部研究專家審核）：修正骨架格式相容性問題——RTMPose 輸出的 COCO-17 關鍵點與 NTU120 預訓練 CTR-GCN 的 25-joint 拓樸不相容，改為使用 Kinetics-400 COCO-17 格式的預訓練配置；修正 TTA 方法定位——原始 TENT 是 BN-centered 設計，而本專案 fusion head 使用 LayerNorm，故明確定位為「TENT-style entropy-minimization adaptation on LN-based head」而非「vanilla TENT」。

**v2.2 → v2.3 的核心變化**（基於實際查證 PYSKL repo）：經實際查證，PYSKL 的 CTR-GCN Model Zoo 中不存在 Kinetics-400 的預訓練權重，但提供了 NTU120 + HRNet 2D Skeleton（COCO-17 格式）的完整四模態權重（`ctrgcn_pyskl_ntu120_xsub_hrnet`），可直接下載使用。v2.2 中假設的「首選 Kinetics-400 COCO-17 權重」方案修正為「使用 NTU120 HRNet 2D 權重」，骨架格式相容性問題從「待驗證風險」降級為「已確認可行」。

---

## 2. 研究目標與新穎性宣稱

### 2.1 主要研究問題

**RQ1**：在 weakly supervised VAD 任務上，將骨架動態特徵與 VLM 語義特徵融合，相較於單一模態方法能帶來多少性能提升？加入物件語境特徵作為第三模態是否帶來額外增益？

**RQ2**：TENT/SAR-style entropy-minimization adaptation 應用於 LN-based fusion head 時，是否能有效改善多模態暴力偵測模型在跨場景部署時的泛化能力？在何種域偏移條件下最為有效？其效果與原始 BN-centered TTA 設計有何差異？

### 2.2 新穎性宣稱（修訂版）

以下兩項新穎性宣稱已經過系統性文獻驗證，並根據 2026 年 3 月最新文獻進行了措辭修訂。

**宣稱 A — 多模態暴力偵測框架（主線貢獻）**

> 據我們所知，現有文獻尚未見到同時整合 skeleton GCN 與 VLM semantic cues 的 violence-oriented weakly supervised anomaly detection framework。本研究進一步探索加入 open-vocabulary object detection 作為第三模態的效果。

**重要背景**：骨架 GCN + CLIP 語義的組合在通用動作辨識領域已有大量先例（GAP/ICCV2023、PURLS/CVPR2024、LaSA/ECCV2024 等 30+ 篇），但這些工作均用於通用動作辨識而非暴力偵測 VAD，且均未在弱監督 anomaly localization 設定下運作。本專案的差異化在於「任務情境」（violence-oriented VAD）而非「模態組合」本身。

**宣稱 B — TTA 在 VAD 中的系統性評估（副線貢獻）**

> 本研究系統性評估 TENT/SAR-style entropy-minimization adaptation 在 violence-oriented weakly supervised VAD 的 LN-based fusion head 上的有效性，填補現有文獻中缺乏此類系統研究的空白。

**重要背景**：MM-VAD（arXiv 2603.13374, 2026.03）已在 UCF-Crime/XD-Violence 上進行 adaptive test-time inference，以 test-time 無監督優化 learnable prompts 的方式實現 lightweight TTA。因此，本專案不再宣稱「TTA 首次進入 VAD」，而是聚焦在「TENT/SAR 的 entropy minimization 核心思想，應用於 LN-based 多模態暴力偵測 fusion head 的 affine parameters 時的系統比較與分析」這一更精確的定位。三者在技術路線上有明確區別：MM-VAD 優化的是 prompt parameters，原始 TENT/SAR 更新的是 BN running statistics 和 affine parameters，本專案則探索將 entropy minimization 策略應用於 LN affine parameters 的效果。

**BN vs LN 的差異說明**：原始 TENT 的核心設定是在 test time 以 entropy minimization 更新 BatchNorm 的 running statistics（μ, σ²）和 affine transformations（γ, β），其實作本質上是 BN-centered 的。本專案的 fusion head 使用 LayerNorm，不具備 BN 的 running statistics 機制。因此，本專案所做的是 TENT-style entropy-minimization adaptation（更新 LN 的 γ 和 β），而非 vanilla TENT。這一差異將在論文中明確交代，並作為 discussion 的分析素材——「BN-centered 的 TTA 方法核心思想移植到 LN-based 架構時，其有效性如何」本身即為有研究價值的實驗問題。

### 2.3 貢獻層級定義

本專案的貢獻按照優先級分為三層，以確保在有限時間內至少完成一個完整的研究故事。

**核心貢獻（必須完成）**：Skeleton + CLIP 雙模態融合框架用於 violence-oriented weakly supervised VAD，包含完整的 ablation 分析。

**重要貢獻（高度期望完成）**：Corruption-based TTA 實驗，以 TENT/SAR-style entropy minimization 驗證 source-free adaptation 在 controlled domain shift 下的有效性。

**加分貢獻（視時間而定）**：物件分支整合（三模態融合）、cross-dataset TTA、雙人互動圖、EATA/SAR 全面比較。

---

## 3. 任務定義與研究範圍

### 3.1 正式任務定義

本專案的核心任務為 **Weakly Supervised Violence-Oriented Video Anomaly Localization**。

這意味著：輸入為 untrimmed 長影片，訓練時僅提供影片級別標註（正常/異常），測試時需輸出 frame-level 異常分數，以 frame-level AUC / AP 作為主要評估指標。

### 3.2 為什麼選擇此任務定義

在研究規劃初期，任務定義曾在兩個方向之間搖擺：trimmed violence classification（如 RWF-2000 的短片段二分類）和 weakly supervised anomaly localization（如 UCF-Crime / XD-Violence 的長影片異常定位）。兩者在輸入長度、標註形態、loss 設計、evaluation protocol 和可比較的 SOTA 上都有根本差異。

最終選擇 weakly supervised anomaly localization 的原因如下。第一，整份研究的 baseline 選擇（RTFM、MGFN、VadCLIP 等）、指標設計（frame-level AUC/AP）、和 TTA 的學術意義，都更自然地對齊 VAD 的研究範式。第二，weakly supervised 設定更貼近實務場景（大規模監控影片很難取得精確的幀級標註），碩論的研究深度也更充足。第三，TTA 的跨域泛化故事在 VAD 的 untrimmed 設定下更有說服力。

### 3.3 Violence-Oriented 與 Full Benchmark 的關係

本研究以 violence-related anomalies 為核心研究動機與框架設計的出發點（骨架分支針對暴力動態設計、物件分支聚焦武器偵測、文字提示工程圍繞暴力/正常場景描述），但為維持與既有文獻的可比性，主實驗遵循官方 full-benchmark protocol（涵蓋 UCF-Crime 的全部 13 類異常、XD-Violence 的全部 6 類暴力），並以 violence-related categories 做補充的 per-category breakdown 分析。

這種設計同時保留了兩個優勢：第一，論文的數字可以與 RTFM、VadCLIP 等現有 SOTA 直接比較，不會因為自定義 subset protocol 而失去可比性；第二，violence-related categories 的補充分析能具體回答「本框架是否特別擅長暴力類別」這個核心研究問題。

### 3.4 暴力子集處理原則

**主實驗使用官方 full-benchmark protocol**：在 UCF-Crime 和 XD-Violence 上按照官方的 train/test split 和 evaluation protocol 進行訓練與評估，報告 full-benchmark 的 frame-level AUC / AP。這確保我們的數字可以與現有 SOTA 直接比較。

**暴力子集分析作為補充**：在主實驗之外，額外報告暴力相關子集（如 UCF-Crime 中的 Fighting + Assault、XD-Violence 中的 Fighting + Abuse + Riot）的性能，作為 per-category breakdown 分析的一部分。但不會將子集數字與 full-benchmark SOTA 做一對一比較。

**RWF-2000 的定位**：RWF-2000 為 trimmed binary classification benchmark，與主線任務定義不完全吻合。本專案將其定位為「補充驗證實驗」——用於驗證 skeleton branch 在純暴力分類任務上的有效性，而非主要 benchmark。RWF-2000 已完全移出 critical path，不會阻塞任何主線工作。

---

## 4. 資料集選擇與完整規格

### 4.1 主要基準資料集

| 資料集 | 影片數 | 總時長 | 標註 | 暴力類別 | 來源場景 | 在本專案中的定位 |
|--------|-------|--------|------|---------|---------|----------------|
| UCF-Crime | 1,900 | ~128 h | 影片級 + 幀級(test) | Fighting, Assault (+ 11類) | CCTV 監控 | 主要 VAD benchmark |
| XD-Violence | 4,754 | 217 h | 影片級 + 幀級(test) | Fighting, Abuse, Riot 等 6 類 | 電影 + YouTube + 新聞 | 主要 VAD benchmark |
| RWF-2000 | 2,000 | ~2.8 h | 影片級(binary) | Fighting / Non-Fighting | CCTV 監控 | 補充驗證（二分類） |

**關於 XD-Violence 的場景多樣性說明**：XD-Violence 官方明確標註其為 multi-scene dataset，來源涵蓋電影、YouTube、新聞、CCTV 等多種場景。這是本專案將研究範圍從「戶外公共場所」放寬為「開放場景 / 實世界暴力事件」的主要原因之一。此變更確保論文題目與實際使用的 benchmark 之間不存在範圍矛盾。

### 4.2 資料集取得方式與狀態

**UCF-Crime**（✅ 可直接下載）：官方連結 `crcv.ucf.edu/projects/real-world` 提供 ZIP 下載（~15-20GB）。官方分割檔 `Anomaly_Train.txt`（810 正常 + 800 異常影片）和 `Anomaly_Test.txt`（150 正常 + 140 異常影片）。測試集幀級時序標註在 `Temporal_Anomaly_Annotation.txt`。暴力相關類別：Fighting（50 支）、Assault（50 支）。

**XD-Violence**（✅ 可用但需耐心）：官方頁面 `roc-ng.github.io/XD-Violence` 提供 OneDrive 分段下載。關鍵優勢：官方提供預擷取 I3D RGB+Flow 特徵及 VGGish 音訊特徵，可直接使用省去大量預處理時間。Train 3,954 / Test 800（測試集有幀級標註）。Kaggle 亦有鏡像。

**RWF-2000**（⚠️ 存取受限）：原始 GitHub 標注因隱私問題暫時不可用。備選方案：聯絡 SMIIP Lab (DKU/Duke) 作者索取存取連結，或嘗試 Kaggle 鏡像。官方分割：1,600 train / 400 test，每支影片 ≤5 秒、30 FPS。第一天即應發送索取信件。若無法取得，可以僅用 UCF-Crime + XD-Violence 完成全部主線實驗。

### 4.3 骨架標註規格（自行擷取）

三個資料集均不提供原生骨架標註，需使用外部姿態估計工具自行擷取。推薦使用 rtmlib 套件（無 mmcv 依賴）搭配 RTMPose-m（256×192）+ YOLOX 偵測器。輸出格式對齊 PYSKL pickle 格式：COCO-17 關鍵點。

| 資料集 | 預估幀數 | RTX 4090 擷取時間（含工程不確定性） | 輸出大小 | 時程排程 |
|--------|---------|--------------------------------------|---------|---------|
| UCF-Crime（全部） | ~1,000 萬 | ~5-8 小時 | ~15 GB | Week 2 日間優先 |
| XD-Violence | ~2,000 萬 | ~20-40 小時 | ~30 GB | Week 2 起夜間背景執行 |
| RWF-2000 | ~300K | ~1 小時 | ~500 MB | 取得後有空再跑 |

**工程不確定性說明**：以上時間估計已將原始估計乘以 2 倍的工程不確定性係數。暴力場景中動作快速、motion blur 多、人體遮擋嚴重、多人交疊時 top-2 person 追蹤不穩定——這些都可能導致部分影片需要重新處理或手動檢查。骨架擷取不是「extract 就有」的一次性工作，而是需要迭代調整閾值和處理缺幀問題的工程過程。

**v2.1 時程修正**：v2.0 的 Week 2 僅安排了 UCF-Crime 和 RWF-2000 的骨架擷取，但 Week 5 就需要在 XD-Violence 上做評估，造成時程缺口。v2.1 將 XD-Violence 骨架擷取提前至 Week 2 以夜間背景任務啟動（預計跨越 Week 2-3），同時將 RWF-2000 完全移出 critical path。

---

## 5. 系統架構總覽

### 5.1 整體管線設計

系統採用雙主線 + 可選第三支線的特徵層級融合架構。所有骨幹網路（CTR-GCN、CLIP 視覺編碼器、RTMPose、YOLO-World）均以預訓練權重凍結，在推論模式下運行，僅預擷取特徵並快取至磁碟。後續訓練僅涉及輕量融合層與分類頭。

**主線管線流程**：影片輸入 → (並行) [RTMPose 骨架擷取 → CTR-GCN 凍結特徵編碼 | CLIP 凍結視覺編碼] → 特徵快取 → 雙模態融合模組（MIL 訓練） → 分類頭 → 異常分數輸出。TTA 模組在測試階段啟動，對融合層 / 分類頭中的 normalization 參數進行線上適應。

**可選延伸**：YOLO-World 物件偵測 → 物件特徵工程 → 與雙模態特徵進行三模態 late fusion。

### 5.2 處理階段（v2.1 修訂：三階段流程）

v2.0 原設計為四階段流程（先 fine-tune CTR-GCN → 凍結並擷取特徵 → 訓練融合 head → TTA）。但第一階段存在方法論漏洞：CTR-GCN 是為有明確動作類別標籤的 trimmed clip 設計的分類器，而本專案的主線任務是 weakly supervised VAD——訓練集只有影片級的正常/異常標籤，沒有逐片段的動作類別標籤。「拿什麼 supervision signal 去 fine-tune skeleton encoder」這個問題在 v2.0 中未被交代。

v2.1 將流程簡化為三個階段，消除此方法論漏洞。

**階段一：特徵預擷取與快取（所有 backbone 全部凍結）**。CTR-GCN 使用 NTU120 HRNet 2D Skeleton 預訓練權重（COCO-17 格式，已確認可直接下載，見第 6 節詳細說明）作為凍結的特徵抽取器，不在目標 VAD 資料集上進行任何 supervised fine-tune。對所有影片預擷取骨架特徵（CTR-GCN）、視覺語義特徵（CLIP）、和物件偵測結果（YOLO-World，可選），全部存入磁碟。此階段之後，所有骨幹網路均不再參與梯度計算。

**階段二：融合模組 MIL 訓練**。在快取特徵上訓練輕量融合層與分類頭，使用 MIL Ranking Loss 進行弱監督訓練。此階段的記憶體需求極低（遠小於 24GB VRAM 的限制），支持快速迭代多種融合策略。整個系統從頭到尾只有這一個訓練階段，方法論上乾淨且與 CLIP branch 的凍結策略完全對稱。

**階段三：測試時適應**。部署階段僅對融合層 / 分類頭中的 normalization affine parameters 進行線上適應，所有骨幹特徵保持凍結。

**為什麼凍結 CTR-GCN 是合理的**：NTU120 HRNet 2D 預訓練的 CTR-GCN 已經在 120 類人體動作上學到了豐富的時空動態表徵（包含 punch、kick、push、grab、slap 等與暴力相關的動作類別），這些表徵對暴力偵測有直接的遷移價值。更重要的是，這些權重是從 NTU120 的 RGB 影片中以 HRNet 擷取 COCO-17 格式 2D 骨架後訓練的——它學到的是「2D COCO-17 格式的骨架動態表徵」，而非 Kinect 3D 座標的表徵。這與本專案使用 RTMPose 從 CCTV/YouTube 影片中擷取 2D 骨架的管線在骨架格式上完全一致。在融合框架中，骨架特徵的角色是作為「動態線索」輸入給 MIL head，由 MIL head 學習如何從弱監督信號中利用這些線索——這不需要骨架 encoder 本身被 fine-tune。

**可選 ablation：骨架 encoder fine-tune 的效果**。若時間充裕，可作為加分 ablation 實驗，探索「是否對 CTR-GCN 進行額外的 proxy-label fine-tune 能改善表徵品質」。具體做法是：將 weakly supervised 的影片級標籤繼承至影片內所有 snippet 作為 proxy label，對 CTR-GCN 最後 4 層做輕量 fine-tune，再重新擷取特徵進行比較。此實驗的價值在於量化「凍結 vs fine-tuned backbone」的差異，但它是 ablation 而非主線流程的必要步驟。

### 5.3 特徵維度規格

| 分支 | 骨幹 | 狀態 | 輸出維度 | 時序粒度 | 優先級 |
|------|------|------|---------|---------|--------|
| 骨架分支 | CTR-GCN | 凍結（NTU120 HRNet 2D 預訓練，COCO-17 格式） | 256-d | 片段級 | 🥇 主線 |
| 語義分支 | CLIP ViT-B/16 | 凍結 | 512-d | 1 FPS → 片段級池化 | 🥇 主線 |
| 物件分支 | YOLO-World-M | 凍結 | 可變長度 → 工程特徵 | 逐幀 → 片段級聚合 | 🥉 可選 |

### 5.4 關鍵設計決策

**為何所有 backbone 全部凍結？** 第一，單張 4090 的 VRAM 限制加上三個月的時間壓力，使端到端反向傳播骨幹網路不切實際。第二，特徵預擷取後每次融合實驗僅需數分鐘，支持快速迭代。第三，凍結 backbone 讓整個系統只有一個訓練階段（MIL fusion head），方法論上最乾淨——不會出現「拿什麼 label fine-tune」的方法學漏洞。第四，CTR-GCN 和 CLIP 兩個 branch 使用完全對稱的「凍結預訓練 backbone + 只訓練 head」範式，架構上最一致。

---

## 6. 主線模組一：骨架圖卷積網路（Skeleton GCN）

### 6.1 模型選擇：CTR-GCN

| 屬性 | 規格 |
|------|------|
| 論文 | Channel-wise Topology Refinement Graph Convolution（ICCV 2021） |
| 參數量 | 1.46M（單模態）/ ~5.84M（四模態集成） |
| 計算量 | 3.9 GFLOPs（單模態） |
| 輸入 | 骨架序列 [N, C, T, V, M]（N=批次, C=3 座標, T=64 幀, V=17 關節, M=2 人） |
| 輸出 | 256 維特徵向量（全域平均池化後） |
| 預訓練 | **NTU120 XSub + HRNet 2D Skeleton（COCO-17 格式）** ✅ 已確認可下載 |
| 使用方式 | **凍結預訓練特徵抽取器**（不在目標 VAD 資料集上 fine-tune） |
| 選擇理由 | PYSKL 工具箱完整支持、有 COCO-17 格式預訓練權重、生態最成熟 |

### 6.2 骨架格式相容性（v2.3 修訂：已實證確認）

#### 問題背景

v2.1 及之前版本存在骨架格式不相容的問題：PRD 指定使用 RTMPose 擷取 COCO-17 格式的骨架，同時使用 NTU120 預訓練的 CTR-GCN。但 NTU120 的「Official 3D Skeleton」來自 Kinect 深度感測器，使用 25 個關節點，與 COCO-17 的 17 個關鍵點在數量、語義、和圖拓樸上都不同。v2.2 提出改用 Kinetics-400 COCO-17 權重作為首選，但該權重是否存在於 PYSKL 中尚未被驗證。

#### v2.3 的實證發現

經實際查證 PYSKL 的 CTR-GCN Model Zoo（`github.com/kennymckormick/pyskl/blob/main/configs/ctrgcn/README.md`），關鍵發現如下。

**CTR-GCN 沒有 Kinetics-400 的預訓練權重。** PYSKL 的 CTR-GCN 所有 checkpoint 均訓練於 NTU60 或 NTU120，不包含 Kinetics-400。因此 v2.2 的首選方案（Kinetics-400 COCO-17 權重）不可行。

**但 PYSKL 對每個 NTU 資料集都提供了兩種骨架格式的權重：「Official 3D Skeleton」（Kinect 25-joint）和「HRNet 2D Skeleton」（COCO-17 格式）。** 後者正是我們需要的——HRNet 擷取的 2D 骨架就是 COCO-17 格式，與 RTMPose 的輸出格式原生相容。

#### 已確認可用的預訓練權重

以下為 NTU120 XSub + HRNet 2D Skeleton 的 CTR-GCN 四模態權重，全部已確認可從 OpenMMLab 下載：

| 模態 | Config 路徑 | Top-1 Acc | 權重下載連結 |
|------|-----------|-----------|------------|
| Joint | `configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/j.py` | 82.2% | `http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/j.pth` |
| Bone | `configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/b.py` | 84.6% | `http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/b.pth` |
| Joint Motion | `configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/jm.py` | 82.3% | `http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/jm.pth` |
| Bone Motion | `configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/bm.py` | 82.1% | `http://download.openmmlab.com/mmaction/pyskl/ckpt/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet/bm.pth` |

四流融合（2:2:1:1）準確率為 86.6%。備選組 NTU120 XSet 的 Bone 模態準確率更高（88.6%），亦可使用。

#### 為什麼 NTU120 HRNet 2D 權重是正確的選擇

**格式原生相容。** 這些權重是以 HRNet 從 NTU120 的 RGB 影片中擷取 COCO-17 格式 2D 骨架後訓練的。CTR-GCN 的圖拓樸在訓練時就是 COCO-17 的 17 節點結構，與 RTMPose 的輸出格式完全一致，不需要任何 joint mapping 或格式轉換。

**表徵類型對齊。** 這些權重學到的是「2D COCO-17 格式的骨架動態表徵」，而非 Kinect 3D 座標的表徵。雖然 NTU120 的原始影片來自實驗室環境，但 2D 姿態估計器輸出的骨架格式和你從 CCTV/YouTube 影片中用 RTMPose 擷取的格式是同一個空間（2D pixel coordinates + confidence）。

**動作覆蓋充足。** NTU120 有 120 類人體動作，其中包含 punch、kick、push、grab、slap、hit with object、wield knife 等多個與暴力直接相關的動作類別，遷移價值足夠。

**v2.2 中 Kinetics-400 vs NTU120 的比較已不再需要。** v2.2 列出了三個 Kinetics-400 優於 NTU120 的理由（格式相容、資料來源接近、動作覆蓋），但現在我們使用的是 NTU120 的 HRNet 2D 版本而非 Official 3D 版本，前兩個理由已不適用——HRNet 2D 版本本身就是 COCO-17 格式、本身就是從 RGB 影片中擷取的 2D 骨架。第三個理由（動作覆蓋）NTU120 的 120 類也完全足夠。

#### 降級方案（已大幅簡化）

由於首選方案已確認可行，降級方案的重要性大幅降低。僅在極端情況下（例如 OpenMMLab 下載伺服器長期不可用）才需要考慮：

**方案 B1（唯一保留的降級方案）**：使用 COCO-17 的圖拓樸配置建構 CTR-GCN，隨機初始化權重，讓其特徵品質完全依賴 MIL fusion head 的訓練。方法論上乾淨但沒有預訓練遷移價值。

**方案 B2（已移除）**：v2.2 中的 17→25 joint mapping 方案已移除。既然有格式原生相容的 HRNet 2D 權重可用，就不需要考慮語義品質不保證的 mapping 策略。

#### Week 1 驗證任務（已簡化）

Week 1 的骨架權重驗證從「搜尋 + 決策」簡化為「下載 + 確認」：下載上述四個 .pth 檔案，用一段 COCO-17 格式的骨架序列跑一次 forward pass，確認輸入維度（17 joints × 3 channels × 64 frames × 2 persons）和輸出維度（256-d）正確。預計耗時 30 分鐘以內。

### 6.3 特徵擷取策略

CTR-GCN 以 NTU120 HRNet 2D 預訓練權重直接作為凍結特徵抽取器。對每個 64 幀的 skeleton snippet，輸出 256-d 的特徵向量。四模態（joint, bone, joint-motion, bone-motion）各自獨立擷取特徵後，以加權拼接組成最終骨架表徵：joint:bone:joint-motion:bone-motion = 1.0 : 1.0 : 0.5 : 0.5。

所有骨架特徵在階段一預擷取完畢後存入磁碟，後續訓練階段不再涉及 CTR-GCN 的任何計算。

### 6.4 多人處理策略

暴力場景必然涉及多人互動。本專案對多人處理採取分層策略。

**預設方案（Phase 1）：Top-2 Person Feature Aggregation**。每個片段取信心分數最高的 2 人，各自通過 CTR-GCN 獲得 256-d 特徵，再以 concat（512-d）或 max/mean pooling（256-d）聚合為單一向量。此方案實作簡單、容易 debug、容易做 ablation、結果不好時能快速回退。

**進階方案（Phase 2，若時間充裕）：Two-Person Interaction Graph**。將兩人的 17 個關節合併為 34 節點圖，在對應關節之間建立跨人體邊（inter-body edges）。鄰接矩陣為 34×34，包含人內邊（intra-body）與人間邊（inter-body）。此方案有更強的表達能力，但工程成本和 debug 難度顯著提高。

**關鍵決策**：v1.0 將 Two-Person Graph 作為預設方案，v2.0 將其降為進階方案。原因是在 12 週的限制下，graph topology engineering 的 debug 成本太高，而簡單的 feature aggregation 已經能提供合理的多人互動捕捉能力。進階方案可作為 ablation 來展示對問題的深入理解。

---

## 7. 主線模組二：視覺語言模型語義增強（CLIP）

### 7.1 模型選擇：CLIP ViT-B/16

| 屬性 | 規格 |
|------|------|
| 預訓練 | OpenAI CLIP ViT-B/16（400M 影像-文字對） |
| 視覺輸出 | 512 維 [CLS] token |
| 文字輸出 | 512 維文字嵌入 |
| RTX 4090 吞吐量 | ~700-1,000 img/s（FP16） |
| 完全凍結 | 是——不微調任何 CLIP 參數 |

### 7.2 語義特徵擷取策略

**視覺特徵擷取**：以 1 FPS 均勻取樣 RGB 幀，通過 CLIP 視覺編碼器取得 512 維 [CLS] 向量。

**時序池化策略（修訂）**：v1.0 使用純 mean pooling，但對暴力這種短促、瞬時的動作存在稀釋風險——攻擊動作可能只發生在少數幀，平均池化會將異常信號淹沒在大量正常幀中。v2.0 起改為 **mean + max pooling 並聯**：每個片段同時計算 mean-pooled 特徵（512-d）和 max-pooled 特徵（512-d），拼接為 1024-d 向量再通過線性投影壓縮至 512-d。此設計幾乎不增加工程成本，但能同時保留平均語義和峰值異常信號。

取樣率的 ablation（1 FPS vs 2 FPS vs 4 FPS）列為可選實驗。如果時間有限，1 FPS + mean/max 並聯是最穩的預設配置。

### 7.3 文字提示工程

使用 LLM 生成 20-30 條暴力 / 正常行為的詳細描述，通過 CLIP 文字編碼器取得文字嵌入，作為分類頭的語義先驗引導。

暴力描述範例：「兩人在街道上互相推擠並揮拳攻擊」「一人手持棍棒揮向另一人」「多人在開放空間中混戰」。正常描述範例：「行人在人行道上正常行走」「人們在公園中友好交談」「路人停下腳步看手機」。

---

## 8. 副線模組三：物件偵測（YOLO-World）

### 8.1 定位說明

物件偵測分支在 v2.0 起從「三大主線之一」降級為「可選增強模組」。這不是因為物件資訊沒有價值，而是基於工程風險管理的考量——在 12 週內同時 debug 三個模態的融合遠比先把兩個模態做穩再視情況加入第三個更有風險。

物件分支的加入條件：主線 Skeleton + CLIP 融合模型在 Week 6 前穩定產出合理數字（UCF-Crime AUC > 83%），且 corruption-based TTA 實驗在 Week 7 前完成。

### 8.2 模型選擇：YOLO-World-M

| 屬性 | 規格 |
|------|------|
| 核心能力 | 零樣本開放詞彙物件偵測 |
| RTX 4090 推論速度 | ~78-104 FPS（PyTorch FP16） |
| LVIS 精度 | 37.2 AP（zero-shot） |

### 8.3 物件提示分層設計

**穩定物件（納入主實驗）**：person, knife, gun, pistol, baseball bat, stick, bottle, chair。這些類別在 open-vocabulary detector 中有較高的偵測穩定性。

**探索性物件（僅作 exploratory analysis）**：blood, fist, brick, stone。這些類別因物件過小、模糊、或高度場景依賴，在實務上偵測不穩定，不適合作為主特徵。

### 8.4 特徵設計

工程特徵設計：dangerous object presence ratio（整個片段中有危險物件的幀占比）、max confidence（片段中危險物件信心分數的最大值）、person-object spatial proximity（危險物件與最近人體 bbox 的最小距離/IoU）、object count histogram（各類別出現次數的直方圖）。

這些工程特徵經 MLP 投影至 64 維嵌入後，以 late fusion 方式與雙模態特徵結合。

---

## 9. 多模態融合設計

### 9.1 融合策略分階實作

融合策略採取由簡入繁的工程路線。

| 階段 | 融合方法 | 實作時間 | 定位 | 風險 |
|------|---------|---------|------|------|
| Phase 1（Week 3-4） | Late Fusion（分數加權平均） | 2 小時 | Ablation baseline | 極低 |
| Phase 2（Week 4） | Gated Fusion（Sigmoid 門控） | 1-2 天 | **主模型候選** | 低 |
| Phase 3（Week 5-6，若時間充裕） | Cross-Attention Fusion | 3-5 天 | 進階版 | 中 |

**關鍵調整**：v1.0 以 Cross-Attention 作為主要融合目標，v2.0 起將 Gated Fusion 作為主模型的最低期望。原因有二：第一，在碩論中把簡單方法做乾淨，比做複雜方法但講不清楚好很多；第二，如果最終結果顯示 late fusion 就已經很好了，論文的方法論貢獻會太薄。Gated Fusion 在方法描述上有足夠的內容可以寫，同時工程成本遠低於 Cross-Attention。

### 9.2 Gated Fusion 模組規格

**輸入**：骨架特徵 F_skel (256-d)、CLIP 特徵 F_clip (512-d)。
**投影**：兩分支通過線性投影至 256 維共同空間。
**門控**：Sigmoid 門控機制——g = σ(W_g · [F_skel; F_clip] + b_g)，融合特徵 = g ⊙ F_skel_proj + (1-g) ⊙ F_clip_proj。
**輸出**：融合特徵 F_fused (256-d) → LayerNorm → MLP 分類頭 → 異常分數 [0,1]。
**正則化**：LayerNorm + Dropout(0.3) + 殘差連接。

### 9.3 Cross-Attention 融合規格（進階版，若時間充裕）

**輸入**：骨架特徵 F_skel (256-d)、CLIP 特徵 F_clip (512-d)。
**投影**：所有分支通過線性投影至 512 維共同空間。
**注意力**：8 頭跨模態注意力——Query 來自骨架，Key/Value 來自 CLIP。
**輸出**：融合特徵 F_fused (512-d) → LayerNorm → MLP 分類頭 → 異常分數 [0,1]。
**正則化**：LayerNorm + Dropout(0.3) + 殘差連接。

### 9.4 TTA 友好的架構考量

為確保後續 TTA 實驗有足夠的可適應參數，融合模組和分類頭中保留 normalization layers（LayerNorm）。但這個設計決策需要平衡兩個考量。

**務實面**：如果融合 head 太輕且 normalization 層太少，TTA 的可調參數非常有限，可能導致「理論上用了 TTA，實際上模型幾乎無法 adapt」的尷尬結果。

**學術面**：不應該為了遷就 TTA 實驗而刻意膨脹模型架構。如果合理設計的融合 head 中 TTA 效果有限，這本身就是一個有價值的發現。

**本專案的處理方式**：先把融合 head 設計成我們認為最合理的結構（包含必要的 LayerNorm 作為正則化手段），然後誠實報告 TTA 在此結構上的效果。在 discussion section 中分析可適應參數量與 TTA 效果之間的關係。

### 9.5 時序對齊方案

所有分支的特徵均對齊至統一的時序粒度。骨架分支以 64 幀為一個片段窗口產出 256-d 特徵；CLIP 分支以相同時間窗口內的所有 1 FPS 幀進行 mean+max pooling 產出 512-d 特徵；物件分支以相同窗口內所有幀的偵測結果聚合為工程特徵。所有特徵在時間軸上嚴格對齊，無需額外的時序插值。

---

## 10. 測試時適應（TTA）

### 10.1 TTA 在本專案中的定位

TTA 定位為「deployment robustness study」——它是論文的重要組成部分，但不是生死線。如果 TTA 實驗結果不理想，論文仍然可以靠多模態融合的主線撐起來；如果 TTA 有正面結果，那就是額外加分。

### 10.2 TTA 方法選擇

| 方法 | 核心機制 | 與本專案的關係 | 實作來源 | 優先級 |
|------|---------|---------------|---------|--------|
| TENT-style | 測試時以 entropy minimization 更新 normalization affine parameters | 原始 TENT 為 BN-centered；本專案應用於 LN affine parameters (γ, β) | 基於官方開源改編 | 🥇 必做（baseline） |
| SAR-style | TENT + entropy sharpness regularization，對 noisy batch 更穩定 | 同上，改編至 LN-based head | 基於官方開源改編 | 🥇 必做（主推） |
| EATA-style | 選擇性更新 + Fisher 正則化，防止遺忘 | 同上，改編至 LN-based head | 基於官方開源改編 | 🥈 有餘力再做 |

**方法定位說明**：原始 TENT 的核心機制是在 test time 以 entropy minimization 更新 BatchNorm 的 running statistics（μ, σ²）和 affine transformations（γ, β）。SAR 在此基礎上加入了 sharpness-aware regularization 以提升小 batch / 混合分佈下的穩定性。兩者在實作上都是 BN-centered 的設計。本專案的 fusion head 使用 LayerNorm（不具備 BN 的 running statistics 機制），因此嚴格來說，本專案所做的是「借用 TENT/SAR 的 entropy minimization 核心思想，應用於 LN 的 affine parameters」，而非 vanilla TENT/SAR。論文中將明確使用「TENT-style adaptation」「SAR-style adaptation」等措辭，而非宣稱使用「標準 TENT」。這一 BN vs LN 的差異本身即為有研究價值的分析素材。

### 10.3 Adaptation Protocol（v2.1 新增：鎖死實驗規格）

為確保不同 TTA 方法之間的比較公平且實驗可重現，以下 adaptation protocol 適用於所有 TTA 實驗（TENT-style、SAR-style、以及若做的話 EATA-style），僅差異在於更新規則本身。

**可更新參數範圍**：僅限融合層（Gated Fusion module）和分類頭（MLP classifier）中的 LayerNorm affine parameters（γ 和 β）。所有骨幹網路（CTR-GCN、CLIP）的特徵保持凍結，不重新計算。這意味著 TTA 階段不需要重跑任何 backbone inference——直接在已快取的特徵上操作。

**Adaptation batch 組成**：固定 32 個 snippets 為一個 adaptation batch。每個 batch 從當前測試影片（或影片序列）中按時序順序取出。逐 batch 線上更新 normalization parameters，不回頭重看已處理的 batch。

**重置策略**：每支測試影片開始前，將 normalization parameters 重置為 source-trained 狀態。這確保每支影片的 adaptation 是獨立的，避免跨影片的 error accumulation。

**超參數統一**：所有 TTA 方法使用相同的 adaptation learning rate（1e-3 作為起點，grid search 範圍 {1e-4, 5e-4, 1e-3, 5e-3}）。SAR 的額外超參數（sharpness regularization coefficient）按照官方推薦值設定。

**這個 protocol 為什麼重要**：如果不同 TTA 方法使用不同的 adaptation 範圍或 batch 組成方式，比較結果就失去意義。鎖死 protocol 之後，差異只來自 TTA 更新規則本身，這才是我們真正想比較的東西。

### 10.4 實驗協議

**必做層：Corruption-Based Robustness TTA**

這是 TTA 實驗中最乾淨、最容易解釋的部分。在 UCF-Crime 上製造 UCF-Crime-C 人工腐蝕測試集，腐蝕類型包括 Gaussian noise（σ=0.1-0.5）、Motion blur（kernel=5-15）、JPEG compression（quality=10-50）、Brightness shift（±50%）。每種腐蝕 5 個嚴重程度等級，共 20 種測試條件。此設計參考 ImageNet-C 的範式，移植至影片 VAD 語境。

**重要說明**：corruption 是對原始 RGB 影片施加的，因此 corruption TTA 實驗需要對腐蝕後的影片重新擷取 CLIP 特徵（骨架特徵是否需要重擷取取決於腐蝕是否影響 RTMPose 的輸入）。這筆額外的特徵擷取成本已計入 GPU 預算。

比較矩陣：Source-Only（無適應）vs TENT-style vs SAR-style，在 20 種腐蝕條件下的 frame-level AUC 變化。

**選做層：Cross-Dataset Source-Free TTA**

若時間充裕，進一步評估跨資料集 TTA 的效果。

| 來源（Source） | 目標（Target） | 域偏移類型 | 優先級 |
|---------------|---------------|-----------|--------|
| UCF-Crime | XD-Violence | 監控→電影/新聞（大偏移） | 🥈 有餘力再做 |
| XD-Violence | UCF-Crime | 電影/新聞→監控（大偏移） | 🥈 有餘力再做 |

跨資料集 TTA 的挑戰在於：anomaly detection 的 target test stream 中本身就混合正常與異常樣本。如果直接逐影片 online adapt，entropy minimization 可能讓模型對錯誤分類結果更自信。這個問題本身就值得在 discussion 中分析。

### 10.5 TTA 的五步實驗流程

**步驟一 TRAIN**：在來源資料集上以 MIL Ranking Loss 訓練融合模組 + 分類頭，記錄來源域性能。

**步驟二 FREEZE**：鎖定融合模組和分類頭中除 LayerNorm affine parameters 以外的所有參數。

**步驟三 ADAPT**：測試時在目標條件下（腐蝕 / 跨資料集）按照 10.3 節定義的 adaptation protocol，以 TENT-style 或 SAR-style entropy minimization 更新 LN affine parameters。

**步驟四 EVALUATE**：計算目標條件下的 frame-level AUC / AP。

**步驟五 COMPARE**：對照無適應基線（Source-Only）、各種 TTA 方法、以及目標域完整微調上界（Oracle，若可行）。

---

## 11. 訓練協議與超參數規格

### 11.1 融合模組 MIL 訓練

| 超參數 | 規格 |
|--------|------|
| 優化器 | AdamW (β1=0.9, β2=0.999) |
| 學習率 | 1e-4 |
| 排程 | Linear Warmup (5 epochs) + Cosine Decay |
| Epochs | 50 |
| Batch Size | 32（特徵層級，記憶體需求極低） |
| Dropout | 0.3 |
| 損失函數 | MIL Ranking Loss（弱監督 VAD 標準設定） |
| 早停 | Patience=10, monitor=val_loss（見 11.2 節） |

### 11.2 Validation 與 Early Stopping Protocol（v2.1 新增）

在 weakly supervised VAD 中，frame-level AUC/AP 只有在 test set 上才能計算（因為只有 test set 有 frame-level annotation）。但 early stopping 不能使用 test set 的指標來做 model selection，否則構成 data leakage。本專案的 validation protocol 如下。

**Validation split 切分方式**：從官方 training set 中切出約 15% 作為 internal validation split，維持正常/異常影片的比例不變。具體而言，UCF-Crime 的 training set（810 正常 + 800 異常）中隨機抽出約 120 正常 + 120 異常作為 validation，剩餘作為 training。XD-Violence 同理。切分結果固定為一組 random seed，所有實驗使用相同的 split 以確保比較的公平性。

**Early stopping 監控指標**：以 validation split 上的 **MIL Ranking Loss** 為主要監控指標。選擇 loss 而非 AUC 的原因是：validation split 只有影片級標籤，無法計算 frame-level AUC；而 video-level classification accuracy 在 MIL 設定下的 proxy 品質不穩定。MIL Ranking Loss 本身就是訓練目標，用它做 early stopping 是最直接且一致的做法。

**官方 test set 的使用原則**：官方 test set 的 frame-level annotation 僅用於最終結果報告（frame-level AUC / AP），不參與任何 model selection、hyperparameter tuning、或 early stopping 決策。所有超參數調優均在 training / validation split 上完成。

**一致性保證**：所有 ablation 實驗、不同融合策略的比較、以及 TTA 前後的比較，均使用完全相同的 train/val split 和相同的 early stopping 規則，確保差異只來自實驗變量本身。

### 11.3 骨架 encoder fine-tune 超參數（可選 ablation 用）

以下超參數僅在執行「凍結 vs fine-tuned backbone」ablation 實驗時使用。主線流程不涉及此訓練。

| 超參數 | UCF-Crime |
|--------|-----------|
| 優化器 | SGD (momentum=0.9) |
| 初始學習率 | 0.005 |
| 排程 | Cosine Annealing |
| Epochs | 30 |
| Batch Size | 32 |
| Weight Decay | 1e-4 |
| 輸入長度 | 64 幀 |
| 資料增強 | 隨機平移、旋轉、縮放 |
| 凍結範圍 | 前 6 層 GCN |
| 可訓練範圍 | 最後 4 層 + 分類頭 |
| Label 來源 | 影片級 weak label 繼承至所有 snippet（proxy label） |

---

## 12. 評估協議、指標與基線方法

### 12.1 評估指標

| 資料集 | 主要指標 | 次要指標 | 評估方式 |
|--------|---------|---------|---------|
| UCF-Crime | Frame-level AUC (ROC) | AP, F1 | 官方 full-benchmark protocol |
| XD-Violence | Frame-level AP | AUC | 官方 full-benchmark protocol |
| RWF-2000 | Classification Accuracy | F1, AUC | 補充驗證 |

### 12.2 基線方法與目標數字

| 方法 | UCF-Crime AUC% | XD-Violence AP% | 年份 | 類型 |
|------|---------------|-----------------|------|------|
| RTFM（必重現基線） | 84.30 | 77.81 | 2021 | Generic weakly supervised VAD |
| MGFN | 86.67 | 80.11 | 2023 | Generic weakly supervised VAD |
| BN-WVAD | 87.24 | — | 2024 | Generic weakly supervised VAD |
| VadCLIP | 88.02 | 84.51 | 2024 | Multimodal / prompt-based |
| **Ours（目標）** | **85-87** | **82-85** | — | Multimodal skeleton+VLM |
| **Ours（最低可接受線）** | **83+** | **80+** | — | |

**重要說明**：以上基線數字均為 full-benchmark protocol 下的結果。本專案的數字將在相同 protocol 下取得，確保可直接比較。基線方法已按類型分組標註，以避免在正文中進行「蘋果比橘子」式的比較。在 UCF-Crime 上 0.5-2% AUC 即被視為有意義的改善。本專案的最大優勢是新穎性（多模態框架 + TTA 系統評估）而非追求刷數字，即使數字提升有限，搭配完整的 ablation 分析和 TTA 實驗仍然足以構成碩論貢獻。

### 12.3 必做消融實驗清單

| 實驗 | 目的 | 預計耗時（含工程不確定性） |
|------|------|--------------------------|
| 僅骨架（Skeleton Only） | 單模態基線 | 3-5 小時 |
| 僅 CLIP（CLIP Only） | 單模態基線 | 2-3 小時 |
| Skeleton + CLIP（Late Fusion） | 最簡雙模態 | 2-3 小時 |
| Skeleton + CLIP（Gated Fusion） | 主模型 | 4-6 小時 |
| Mean Pooling vs Mean+Max Pooling | CLIP 池化策略 | 3-4 小時 |
| Top-2 Concat vs Max Pooling vs Mean Pooling | 多人聚合策略 | 3-4 小時 |
| Corruption-based TTA: No Adapt vs TENT-style vs SAR-style | TTA 方法比較 | 8-12 小時 |
| TTA: 不同腐蝕類型 / 程度 | TTA 魯棒性分析 | 10-15 小時 |

### 12.4 加分消融實驗（視時間而定）

| 實驗 | 目的 | 前置條件 |
|------|------|---------|
| 加入物件分支（三模態 Late Fusion） | 第三模態增益 | 主線穩定 |
| Cross-Attention Fusion | 進階融合比較 | Gated Fusion 穩定 |
| Cross-dataset TTA（UCF↔XD） | 跨域 TTA 效果 | Corruption TTA 完成 |
| Two-Person Interaction Graph | 進階骨架建模 | Skeleton baseline 穩定 |
| EATA-style | 額外 TTA 方法 | SAR-style/TENT-style 完成 |
| CLIP 取樣率 ablation（1/2/4 FPS） | 時序粒度影響 | 主線穩定 |
| 凍結 vs Fine-tuned CTR-GCN | Backbone 策略比較 | 主線穩定 |

---

## 13. 十二週實作時程表

### 13.1 時程設計原則

v2.3 的時程設計遵循以下原則。第一，前 6 週必須完成主線（Skeleton + CLIP 融合 + corruption TTA 初步結果），後 6 週用於副線、補實驗、和寫作。第二，所有純實驗耗時估計已乘以 1.8-2.5 倍的工程不確定性係數。第三，第 7-8 週設為明確的緩衝區：如果主線順利，這兩週做進階實驗；如果不順利，這兩週用來救火。第四，寫作從 Week 1 開始，不是最後才寫。第五，XD-Violence 骨架擷取從 Week 2 開始背景執行，RWF-2000 完全移出 critical path。第六，CTR-GCN 預訓練權重已確認可下載（NTU120 HRNet 2D），Week 1 僅需下載並做 forward pass 驗證。

### 13.2 Phase 1：地基建設（Week 1-2）

#### Week 1 — 環境、資料、定義 ⚠️ 關鍵週

| 工作項目 | 具體內容 | 交付物 | 工時估計 |
|---------|---------|--------|---------|
| 任務定義確認 | 與教授確認：weakly supervised violence anomaly localization 作為主線 | 書面確認 | 2h |
| 資料集下載 | UCF-Crime ZIP + XD-Violence OneDrive + RWF-2000 聯絡作者 | 三個資料集就位 | 持續 |
| 預擷取特徵下載 | XD-Violence I3D+VGGish 預擷取特徵 | 預擷取特徵檔案 | 3-4h |
| 環境設置 | PyTorch + rtmlib + PYSKL + SAR + OpenCLIP | conda env 可用 | 5-6h |
| CTR-GCN 預訓練權重下載與驗證 | 下載 NTU120 HRNet 2D 四模態權重（j/b/jm/bm.pth），跑 forward pass 確認維度正確 | 4 個 .pth 檔案 + 驗證通過 | 30min |
| 論文撰寫 | 開始 Introduction 和 Related Work 初稿框架 | 初稿框架 | 持續 |

#### Week 2 — 特徵擷取與 baseline 建立 ⚠️ 關鍵週

| 工作項目 | 具體內容 | 交付物 | 工時估計 |
|---------|---------|--------|---------|
| UCF-Crime 骨架擷取 | rtmlib 對 UCF-Crime 全部影片（日間優先任務） | pickle 檔案 | 5-8h（含 debug） |
| XD-Violence 骨架擷取啟動 | rtmlib 對 XD-Violence（夜間背景任務，預計跨 Week 2-3） | pickle 檔案（Week 3 完成） | 20-40h 背景執行 |
| CLIP 特徵擷取 | ViT-B/16 對 UCF-Crime + XD-Violence @1FPS | npy 特徵檔 | 2-3h |
| 基線重現 | UCF-Crime 上用 I3D 特徵跑 RTFM | RTFM AUC 數字 | 6-8h（含 debug） |
| Validation split 建立 | 從 training set 切出 15% 作為 internal validation | train/val split 檔案 | 1h |
| 特徵品質檢查 | 視覺化骨架擷取結果，確認暴力場景的追蹤穩定性 | 品質報告 | 3-4h |
| 論文撰寫 | 繼續 Related Work | 持續 | 持續 |

### 13.3 Phase 2：主模型建構（Week 3-4）

#### Week 3 — 單模態基線 ⚠️ 檢查點 1

| 工作項目 | 具體內容 | 交付物 | 工時估計 |
|---------|---------|--------|---------|
| XD-Violence 骨架擷取完成 | 確認 Week 2 啟動的背景任務已完成 | pickle 檔案就位 | 檢查 |
| Skeleton Only 基線 | CTR-GCN 凍結特徵 + MIL head 直接訓練 | 骨架 baseline AUC | 3-5h |
| CLIP Only 基線 | CLIP 特徵 + MIL head 直接訓練 | CLIP baseline AUC | 3-5h |
| Late Fusion | 骨架分數 + CLIP MIL 分數加權平均 | Late Fusion 結果 | 2-3h |
| 檢查點判斷 | 確認：(1) baseline 可重現 (2) 特徵已擷取 (3) Late Fusion 有結果 | Go/No-Go 決策 | — |

**檢查點 1 通過條件**：RTFM baseline 在 UCF-Crime 上重現至 ±1% AUC；Skeleton Only 和 CLIP Only 各自產出合理數字；Late Fusion 優於至少一個單模態。

#### Week 4 — 雙模態融合

| 工作項目 | 具體內容 | 交付物 | 工時估計 |
|---------|---------|--------|---------|
| Gated Fusion 實作 | Sigmoid 門控融合模組 | Gated Fusion 結果 | 3-4 天 |
| 超參數調優 | 學習率、dropout、投影維度（在 train/val split 上） | 最佳超參配置 | 2-3 天 |
| UCF-Crime 完整評估 | 主模型在 UCF-Crime 上的 frame-level AUC/AP | 主要數字 | 半天 |
| 論文撰寫 | 開始 Methodology section（邊做邊寫） | 方法初稿 | 持續 |

### 13.4 Phase 3：主線穩定與 TTA（Week 5-6）

#### Week 5 — 主模型穩定化 + 第一輪 ablation

| 工作項目 | 具體內容 | 交付物 | 工時估計 |
|---------|---------|--------|---------|
| XD-Violence 評估 | 主模型在 XD-Violence 上評估 | XD-Violence AP 數字 | 1-2 天 |
| 多人聚合 ablation | Concat vs Max vs Mean pooling | ablation 表格 | 1-2 天 |
| CLIP 池化 ablation | Mean vs Mean+Max | ablation 表格 | 1 天 |
| 論文撰寫 | 繼續 Methodology + 開始 Experiments 框架 | 持續 | 持續 |

#### Week 6 — Corruption TTA ⚠️ 檢查點 2

| 工作項目 | 具體內容 | 交付物 | 工時估計 |
|---------|---------|--------|---------|
| UCF-Crime-C 製作 | 製造 4 類 × 5 等級 = 20 種腐蝕測試條件 | 腐蝕資料集 | 1 天 |
| 腐蝕後特徵重擷取 | 對腐蝕影片重新擷取 CLIP 特徵（骨架視情況） | 腐蝕特徵快取 | 1-2 天 |
| TENT-style 實作 | 官方 TENT 程式碼改編至 LN-based VAD 管線，按 10.3 節 protocol | TENT-style-VAD | 1-2 天 |
| SAR-style 實作 | 官方 SAR 程式碼改編至 LN-based VAD 管線，按 10.3 節 protocol | SAR-style-VAD | 1-2 天 |
| Corruption TTA 實驗 | Source-Only vs TENT-style vs SAR-style 在 20 種條件下 | TTA 比較表格 | 2-3 天 |
| 檢查點判斷 | 確認：(1) 雙模態有穩定結果 (2) TTA 至少某情境有增益 | Go/No-Go 決策 | — |

**檢查點 2 通過條件**：Skeleton + CLIP 在 UCF-Crime 上 AUC ≥ 83%；Corruption TTA 在至少部分腐蝕條件下有正面效果（即使只有 0.3-0.5% 提升）。

### 13.5 Phase 4：緩衝區與進階實驗（Week 7-8）

**這兩週是明確的緩衝區。** 如果前 6 週順利，做進階實驗；如果不順利，用來修復問題和補實驗。

#### Week 7 — 視主線進度決定方向

**如果主線順利**：嘗試加入物件分支做三模態 late fusion（需在本週或更早啟動 YOLO-World 特徵擷取）；或嘗試 Cross-Attention Fusion；或嘗試 cross-dataset TTA。

**如果主線不穩定**：修復融合模組問題；重新調整超參數；修復 TTA pipeline bug。

#### Week 8 — 進階實驗或問題修復

繼續 Week 7 的方向。如果物件分支加入，跑三模態 ablation。如果 cross-dataset TTA 啟動，跑 UCF→XD 和 XD→UCF。

### 13.6 Phase 5：實驗收尾與分析（Week 9-10）

#### Week 9 — 完整實驗 + 分析 ⚠️ 檢查點 3

| 工作項目 | 具體內容 | 交付物 | 工時估計 |
|---------|---------|--------|---------|
| 關鍵實驗重跑 | 主要結果跑 3 次，報告 mean ± std | 統計穩定的數字 | 2-3 天 |
| 失敗案例分析 | 視覺化異常分數時序曲線、骨架偵測結果 | 定性分析圖 | 2 天 |
| 計算效率分析 | FLOPs、推論時間、TTA 額外開銷 | 效率表格 | 1 天 |
| 論文撰寫 | 填入 Experiments section 數字 | 實驗章節初稿 | 持續 |

**檢查點 3 通過條件**：所有必做實驗（12.3 節）已完成；關鍵結果有 3 次重複的統計數字；至少一張定性分析圖可用。

#### Week 10 — 補缺與整合

補充遺漏實驗。RWF-2000 補充驗證（如已取得資料集）。統計顯著性測試。完成 Discussion 初稿。這週是最後的實驗緩衝——之後不再跑新實驗。

### 13.7 Phase 6：寫作與收尾（Week 11-12）

#### Week 11 — 論文整合

整合所有章節（Introduction, Related Work, Methodology, Experiments, Discussion, Conclusion）。製作最終圖表（t-SNE、ROC 曲線、定性範例）。完整初稿交指導教授。開始準備口試簡報。

#### Week 12 — 修改與交付

根據教授回饋修改。校對格式。完成口試簡報。緩衝時間處理所有意外。交付完整論文。

---

## 14. 風險評估與後備計畫

### 14.1 風險矩陣

| 風險 | 機率 | 影響 | 緩解策略 |
|------|------|------|---------|
| RWF-2000 無法取得 | 中 | **低**（已降為補充驗證） | 僅用 UCF-Crime + XD-Violence 完成全部主線 |
| Gated Fusion 不收斂 | 低 | 中 | 退回 Late Fusion（仍有 ablation 價值） |
| Cross-Attention 不收斂 | 中高 | **低**（已降為進階方案） | 維持 Gated Fusion 作為主模型 |
| TTA 對 VAD 無增益 | 中 | 中 | Corruption TTA 保底 + 轉為「系統性分析」論述 |
| TTA 在 anomaly stream 中不穩定 | 中高 | 中 | 在 discussion 中作為有價值的 negative finding 報告 |
| 骨架擷取品質不佳 | 中 | 中高 | 降低取樣 FPS / 增加信心閾值 / 優先處理小資料集 |
| 多人追蹤不穩定 | 中高 | 中 | 使用 top-2 feature aggregation（不依賴穩定追蹤） |
| 凍結 CTR-GCN 表徵不夠好 | 中 | 中 | NTU120 HRNet 2D 預訓練已含暴力相關動作（punch, kick, slap 等）；可做 fine-tune ablation |
| Baseline 重現數字對不上 | 中 | 中 | 調整超參 / 接受 ±1-2% 差異並在論文中說明 |
| 資料集下載緩慢 | 中 | 中 | 第一天啟動所有下載 + 多源嘗試 |
| XD-Violence 骨架擷取超時 | 中 | 中高 | 夜間背景執行 + 可優先用 CLIP-only 做 XD 實驗 |

### 14.2 後備計畫

| 計畫 | 內容 | 新穎性 | 可行性 | 觸發條件 |
|------|------|--------|--------|---------|
| Plan A（完整版） | Skeleton+CLIP（+Object optional）× Gated Fusion × TTA | 雙重貢獻 | ✅ 最佳 | 預設路線 |
| Plan B | Skeleton+CLIP × Late Fusion × Corruption TTA only | 雙重貢獻（較輕） | ✅ 穩健 | Gated Fusion 不收斂 |
| Plan C | 單模態 CLIP × MIL × Corruption TTA + 人工域偏移 | TTA 系統評估貢獻 | ✅ 保底 | Skeleton 分支完全失敗 |
| Plan D | TTA 在 VAD 中的系統性基準研究（無新架構） | 基準研究貢獻 | ✅ 最後防線 | 多模態融合全面失敗 |

---

## 15. GPU 資源預算與計算成本分析

| 任務 | 最低 GPU 小時 | 含工程不確定性 GPU 小時 | 備註 |
|------|-------------|------------------------|------|
| 骨架擷取（UCF + XD） | ~15 h | ~30 h | 含重跑和 debug |
| CLIP 特徵擷取 | ~1 h | ~3 h | 含格式對齊 |
| YOLO-World 物件偵測 | ~7 h | ~14 h | 可選，可隔夜跑 |
| 融合模組 MIL 訓練 | ~2 h | ~20 h | 含多種融合策略比較 |
| Corruption 特徵重擷取 | ~2 h | ~5 h | 腐蝕後 CLIP 特徵（v2.1 新增） |
| TTA 實驗 | ~3 h | ~15 h | 含 20 種腐蝕條件 |
| 消融實驗 | ~5 h | ~30 h | 8+ 項必做消融 |
| 統計顯著性（重複跑） | ~10 h | ~30 h | 關鍵實驗 × 3 次 |
| CTR-GCN fine-tune ablation | ~3 h | ~10 h | 可選 |
| 緩衝（debug/重跑） | — | ~30 h | |
| **總計** | **~48 h** | **~187 h** | |

RTX 4090 可用 GPU 小時：12 週 × 7 天 × 8 小時/天 ≈ 672 GPU 小時。含工程不確定性的 187 小時估計，使用率約 28%。**算力不是瓶頸，研究決策速度和工程 debug 速度才是。**

---

## 16. 最終交付成果清單

| 交付物 | 格式 | 內容 | 完成時間 |
|--------|------|------|---------|
| 碩士論文全文 | PDF / Word | 6 章 + 附錄，預估 40-60 頁 | Week 12 |
| 實驗程式碼 | GitHub Repo | 完整管線：資料預處理、訓練、評估、TTA | Week 10 |
| 預訓練模型權重 | .pt 檔案 | 最佳多模態融合模型 + TTA 適應後模型 | Week 9 |
| 實驗結果 Spreadsheet | Excel/CSV | 所有實驗的指標數字與超參數紀錄 | 持續 |
| 口試簡報 | PPT/PDF | 15-20 頁簡報 | Week 12 |
| 視覺化圖表 | PNG/PDF | t-SNE、ROC 曲線、異常分數時序曲線、特徵空間視覺化、定性範例 | Week 9-10 |

---

## 17. 論文章節結構與寫作規劃

| 章節 | 內容要點 | 預估頁數 | 撰寫時間 |
|------|---------|---------|---------|
| Ch.1 Introduction | 問題動機、研究問題、貢獻聲明（保守措辭）、violence-oriented 與 full benchmark 關係說明 | 3-5 | Week 1-2 |
| Ch.2 Related Work | VAD 方法（分組：generic / multimodal / prompt-based）、骨架動作辨識、VLM in anomaly detection、TTA 方法 | 8-12 | Week 1-4 |
| Ch.3 Methodology | 架構圖、凍結 backbone 策略說明、骨架格式相容性與預訓練選擇、雙模態融合設計、MIL 訓練、TENT-style adaptation 設計與 BN/LN 差異說明、物件分支（若有） | 8-10 | Week 4-6 |
| Ch.4 Experiments | 資料集 protocol、validation protocol、基線（分組比較）、主結果、ablation、TTA、per-category 分析 | 10-15 | Week 8-10 |
| Ch.5 Discussion | TTA 有效性分析（含 BN vs LN adaptation 差異討論）、可適應參數量分析、凍結 vs fine-tune backbone 討論、骨架格式選擇的影響、失敗案例、局限性 | 3-5 | Week 10 |
| Ch.6 Conclusion | 貢獻總結、研究問題回答、未來方向 | 2-3 | Week 11 |

**核心寫作原則**：從 Week 1 開始寫——Introduction 和 Related Work 不需要實驗結果即可動筆。Methodology 在 Week 4-5 實作時同步撰寫（邊寫邊釐清設計決策，邊做邊發現邏輯漏洞）。Experiments 在 Week 8-9 數字出來後填入。每天花 30 分鐘紀錄實驗結果至 spreadsheet，寫論文時會事半功倍。

---

*本 PRD 文件 v2.3 基於 v2.2 版本及對 PYSKL repo 的實際查證修訂而成。核心修正：經查證 PYSKL CTR-GCN Model Zoo，確認 NTU120 + HRNet 2D Skeleton（COCO-17 格式）的完整四模態預訓練權重存在且可直接下載（`ctrgcn_pyskl_ntu120_xsub_hrnet`），與 RTMPose 的 COCO-17 輸出格式原生相容。v2.2 中的「Kinetics-400 COCO-17 權重」首選方案修正為「NTU120 HRNet 2D 權重」，骨架格式相容性問題從「待驗證風險」降級為「已確認可行」，joint mapping 降級方案（B2）已移除。研究者應在正式開始實作前與指導教授確認研究方向與創新點定位。*
