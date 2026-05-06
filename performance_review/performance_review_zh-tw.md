# ViolenceCC 效能評估報告

**日期：** 2026-05-03
**硬體：** NVIDIA GeForce RTX 4090（24 GB VRAM）
**專案：** 雙模態（骨架 + CLIP）融合的弱監督式影片異常偵測

---

## 1. 概述

本報告對 ViolenceCC 管線進行全面的運算成本分析，涵蓋輕量級 MIL 分類頭以及重量級主幹特徵提取器。此基準測試有兩個目的：

1. **論文表格** -- 在影片異常偵測（VAD）論文中，報告模型複雜度（搭配 AUC/AP 指標）是標準做法
2. **公平比較** -- 僅看分類頭（亞毫秒級）會掩蓋真實的提取成本；骨架管線的運算成本比 CLIP 高出數個數量級

所有測量均在單張 NVIDIA RTX 4090 上進行，採用受控的預熱（warmup）和同步協議。

---

## 2. 測試環境

| 元件 | 規格 |
|------|------|
| GPU | NVIDIA GeForce RTX 4090（24 GB GDDR6X）|
| 作業系統 | Windows 11 Pro |
| PyTorch（vcc-main）| 2.6.0 + CUDA 12.4 |
| PyTorch（vcc-ctrgcn）| 1.12.1 + CUDA 11.3 |
| ONNX Runtime（vcc-skeleton）| 1.24.4 + CUDA 12.x |
| FLOPs 計算工具 | thop（torchprofile）|
| 計時方式 | `time.perf_counter()` 搭配 `torch.cuda.synchronize()` |

**方法論：**
- 計時前先執行預熱迭代並丟棄結果（分類頭預設 50 次、主幹預設 5 次）
- 多次計時迭代取平均（分類頭預設 200 次、主幹預設 20 次）
- GPU 記憶體透過 `torch.cuda.max_memory_allocated()`（在 `reset_peak_memory_stats()` 之後）測量
- FLOPs 以單樣本（batch=1）計算，符合標準做法
- RTMPose/YOLOX 的 FLOPs 為論文公開數據（ONNX 模型無法透過 thop 測量）

---

## 3. MIL 分類頭

這些是對預提取特徵進行異常評分的輕量級分類頭。所有模型共用相同的 MILHead 架構（Linear-ReLU-Dropout 級聯，最後接 sigmoid），但在模態處理和融合方式上有所不同。

### 3.1 架構摘要

| 模型 | 輸入 | 架構 | 輸出 |
|------|------|------|------|
| Skeleton-Only | [B, 32, 256] | LayerNorm(256) -> MILHead(256->128->32->1) | [B, 32] |
| CLIP-Only | [B, 32, 1024] | Linear(1024->512) -> LayerNorm(512) -> MILHead(512->128->32->1) | [B, 32] |
| Late Fusion | skel + clip | SkeletonProj + CLIPProj -> alpha 加權平均 | [B, 32] |
| Gated Fusion | skel + clip | 投影 -> 學習門控 -> 殘差連接 -> MILHead | [B, 32] |
| RTFM-I3D | [B, 32, 1024] | LayerNorm(1024) -> MILHead(1024->128->32->1) | [B, 32] |

### 3.2 結果（batch=16, T=32）

| 模型 | 參數量（K）| MACs（M）| FLOPs（M）| 延遲（ms/batch）| 延遲（ms/sample）| 吞吐量（samples/s）| GPU 峰值記憶體（MB）|
|------|----------|---------|----------|----------------|-----------------|-------------------|-------------------|
| Skeleton-Only | 37.57 | 1.21 | 2.43 | 0.504 | 0.0315 | 31,766 | 10.6 |
| CLIP-Only | 595.65 | 19.07 | 38.14 | 0.690 | 0.0431 | 23,181 | 14.8 |
| Late Fusion | 633.22 | 20.29 | 40.57 | 1.153 | 0.0721 | 13,874 | 17.8 |
| Gated Fusion | 498.11 | 15.96 | 31.92 | 1.050 | 0.0656 | 15,237 | 21.7 |
| RTFM-I3D | 137.41 | 4.46 | 8.91 | 0.460 | 0.0287 | 34,786 | 18.8 |

### 3.3 分析

- **所有分類頭每樣本處理時間均低於 0.1 毫秒**（每批次約 0.5–1.2 ms）。分類成本相對於特徵提取可忽略不計。
- **Gated Fusion（498K）比 Late Fusion（633K）更輕量**，儘管它包含門控機制。原因是 Gated Fusion 將兩個模態投影到共享的 256 維空間後再進行門控，而 Late Fusion 則運行兩個完整的獨立分類頭（SkeletonProj + CLIPProj），僅在分數層級合併。
- **RTFM-I3D 吞吐量最高**（34,786 samples/s），因為它是單流頭，沒有投影層，僅有 LayerNorm -> MILHead。
- **記憶體佔用極低**（10-22 MB）。這些是凍結特徵分類器，非端到端模型。
- **參數量以千（K）為單位，非百萬（M）。** 對於這些輕量級分類頭，使用 K 為單位更具資訊性。

---

## 4. 主幹特徵提取器

這些是將原始影片幀轉換為特徵向量的重量級模型，其輸出供上述 MIL 分類頭使用。由於相依套件不相容，每個主幹在獨立的 conda 環境中運行。

### 4.1 架構摘要

| 主幹 | 類型 | 輸入 | 輸出 | 環境 |
|------|------|------|------|------|
| CLIP ViT-B/16 | Vision Transformer | [B, 3, 224, 224] RGB | [B, 512] 嵌入向量 | vcc-main（PyTorch 2.6.0）|
| RTMPose-m + YOLOX | ONNX（偵測器 + 姿態估計）| [H, W, 3] 單張 BGR 幀 | [N_persons, 17, 2] 關鍵點 | vcc-skeleton（ORT 1.24.4）|
| CTR-GCN（4 流）| 圖卷積網路 | [1, 2, 64, 17, 3] 每流 | [1, 256] 特徵 | vcc-ctrgcn（PyTorch 1.12.1）|
| I3D RGB | 3D 卷積網路（Inception）| 影片片段 | [N, 1024] 特徵 | 預提取（外部來源）|

### 4.2 結果

| 主幹 | 參數量（M）| FLOPs（G）| 延遲 | 吞吐量 | GPU 峰值記憶體（MB）| 每幀成本 |
|------|----------|----------|------|--------|-------------------|---------|
| CLIP ViT-B/16 | 86.19 | 22.54 | 67.79 ms/batch（B=64）| 944.1 幀/秒 | 1,062.5 | 1.059 ms |
| RTMPose-m + YOLOX | ~13.0\* | ~3.22\* | 30.07 ms/幀 | 33.3 幀/秒 | 213.0 | 30.07 ms |
| CTR-GCN（4 流）| 5.684 | N/A | 154.17 ms/片段 | 6.5 片段/秒 | 29.1 | N/A（片段級）|
| I3D RGB | ~25.0\* | ~107.9\* | 預提取 | N/A | N/A | N/A |

\* 論文公開數據（非本機實測）

### 4.3 CLIP ViT-B/16 詳細數據

- **模型：** OpenAI ViT-B/16，透過 open-clip-torch 3.3.0 載入
- **視覺編碼器參數量：** 86.19M（實測；排除文字編碼器）
- **FLOPs：** 每張影像 22.54 GFLOPs（透過 thop 實測，batch=1）
- **批次推論：** 64 張影像/批次 -> 67.79 ms -> 每幀 1.059 ms
- **延遲百分位：** P50=67.79 ms，P95=69.04 ms（穩定，低變異）
- **記憶體：** 1,062.5 MB 峰值分配（batch=64）
- **取樣率：** 目標 1 FPS。UCF-Crime：PNG 為 ~3 FPS，sample_every=3，每 64-PNG 片段約取 22 幀；XD-Violence：sample_every=round(fps/1.0)，以 24 FPS 影片為例約取 3 幀/片段

### 4.4 RTMPose-m + YOLOX 詳細數據

- **人體偵測：** YOLOX-m（~9M 參數，~1.0 GFLOPs）-- 內建於 rtmlib
- **姿態估計：** RTMPose-m（~4M 參數，2.22 GFLOPs）-- 17 個 COCO 身體關鍵點
- **合計：** ~13M 參數，每幀 ~3.22 GFLOPs（論文數據）
- **延遲：** 每幀平均 30.07 ms（P50=30.05，P95=31.98）
- **關鍵限制：** 不支援批次推論。rtmlib 一次只能處理一張幀。
- **記憶體：** 213 MB 增量（透過 nvidia-smi 前後對比測量）
- **處理方式：** 逐幀處理影片中的每一幀 -- 以全幀率處理每片段 64 幀

### 4.5 CTR-GCN 4 流詳細數據

| 流 | 權重 | 參數量（M）| 平均延遲（ms）| P50（ms）| P95（ms）|
|----|------|----------|-------------|---------|---------|
| j（關節）| 1.0 | 1.421 | 38.74 | 37.75 | 45.22 |
| b（骨骼）| 1.0 | 1.421 | 39.09 | 37.48 | 46.65 |
| jm（關節運動）| 0.5 | 1.421 | 38.10 | 37.63 | 39.86 |
| bm（骨骼運動）| 0.5 | 1.421 | 37.99 | 37.63 | 39.01 |
| **總計（4 流）** | | **5.684** | **154.17** | **151.77** | **164.71** |

- **每流輸入形狀：** [N=1, M=2, T=64, V=17, C=3]（2 人、64 幀、17 關節、x/y/confidence）
- **加權平均：** (1.0\*j + 1.0\*b + 0.5\*jm + 0.5\*bm) / 3.0 -> [N, 256] 特徵
- **FLOPs：** 無法測量（vcc-ctrgcn 環境中未安裝 thop；mmcv 自定義運算子不相容）
- **記憶體：** 29.1 MB -- 骨架提取完成後，圖卷積網路極為輕量
- **各流為序列執行：** 4 個流依序運行，每個約 38 ms

### 4.6 I3D RGB（參考數據）

- **來源：** Carreira & Zisserman, "Quo Vadis, Action Recognition?"（CVPR 2017）
- **參數量：** ~25M（論文數據）
- **FLOPs：** 每片段 107.9 GFLOPs（論文數據）
- **狀態：** 從外部來源下載的預提取特徵，非由 ViolenceCC 腳本計算
- **格式：** 5-crop 設計，每個 crop [N_snippets, 1024]

---

## 5. 端到端管線成本分析

關鍵發現：**分類頭的成本可忽略不計；特徵提取主幹才是主要開銷。**

### 5.1 每片段成本分解

一個片段（snippet）是 64 幀的影片段落，為處理的基本單位。

| 管線 | 步驟 1 | 步驟 2 | 步驟 3 | 總計 |
|------|--------|--------|--------|------|
| **骨架路徑** | RTMPose：30.07 ms x 64 幀 = **1,924 ms** | CTR-GCN：**154.17 ms** | Gated Fusion 頭：**1.05 ms** | **~2,079 ms** |
| **CLIP 路徑（UCF）** | CLIP：1.059 ms x ~22 幀 = **~23.3 ms** | -- | CLIP-Only 頭：**0.69 ms** | **~24 ms** |
| **CLIP 路徑（XD，24fps）** | CLIP：1.059 ms x ~3 幀 = **~3.2 ms** | -- | CLIP-Only 頭：**0.69 ms** | **~4 ms** |
| **合併（Gated Fusion，UCF）** | 骨架：**1,924 ms** + CLIP：**~23.3 ms** | CTR-GCN：**154.17 ms** | Gated Fusion 頭：**1.05 ms** | **~2,102 ms** |
| **I3D 路徑** | 預提取（論文：107.9 GFLOPs）| -- | RTFM-I3D 頭：**0.46 ms** | N/A |

### 5.2 成本比值

| 比較項目 | 比值 |
|---------|------|
| 骨架路徑 vs. CLIP 路徑（UCF，每片段）| 骨架貴 **~87 倍**（2,079 ms / 24 ms）|
| 骨架路徑 vs. CLIP 路徑（XD 24fps，每片段）| 骨架貴 **~520 倍**（2,079 ms / 4 ms）|
| RTMPose vs. CLIP（每幀）| RTMPose 貴 **28.4 倍** |
| 提取 vs. 分類（骨架路徑）| 提取成本 **~1,980 倍** |
| 提取 vs. 分類（CLIP 路徑，UCF）| 提取成本 **~34 倍**（23.3 ms / 0.69 ms）|

### 5.3 完整影片處理時間估算

以典型 UCF-Crime 影片（~500 個片段）為例：

| 管線 | 預估時間 |
|------|---------|
| 骨架提取（RTMPose）| 500 x 64 x 30.07 ms = **~16 分鐘** |
| CTR-GCN 特徵提取 | 500 x 154.17 ms = **~1.3 分鐘** |
| CLIP 特徵提取 | 500 x 23.3 ms = **~11.7 秒** |
| MIL 訓練（1 epoch，~200 batches）| ~200 x 1 ms = **~0.2 秒** |

---

## 6. 關鍵洞察

### 6.1 骨架提取的瓶頸

RTMPose-m + YOLOX 佔骨架管線成本的 **92.6%**（2,079 ms 中的 1,924 ms）。根本原因是**不支援批次推論** -- rtmlib 逐幀處理，每幀都需要完整的 YOLOX 偵測和 RTMPose 姿態估計。這是函式庫層級的限制，非模型架構問題。

### 6.2 CLIP 的批次優勢

儘管 CLIP 擁有最多參數（86.19M vs. RTMPose 的 ~13M），但**每幀速度快 28 倍**，因為批次 GPU 推論分攤了開銷。一次處理 64 幀（67.79 ms）比用 RTMPose 逐一處理 2 幀（60.14 ms）還快。

### 6.3 參數效率

| 模型 | 參數量 | 每幀成本 | 每參數成本 |
|------|--------|---------|----------|
| CLIP ViT-B/16 | 86.19M | 1.06 ms | 0.012 ns/param |
| RTMPose + YOLOX | ~13M | 30.07 ms | 2.31 ns/param |
| CTR-GCN（4 流）| 5.68M | 154.17 ms/片段 | 27.1 ns/param |

得益於 Transformer 架構在 GPU 上的平行性，CLIP 是參數效率最高的主幹。

### 6.4 記憶體使用概況

| 元件 | GPU 記憶體 | 說明 |
|------|----------|------|
| CLIP ViT-B/16（B=64）| 1,062.5 MB | 最大單次分配；在 24 GB 中仍綽綽有餘 |
| RTMPose + YOLOX | 213.0 MB | 適中；ONNX Runtime 自行管理記憶體池 |
| CTR-GCN（4 流）| 29.1 MB | 可忽略；17 關節的小型 GCN |
| 全部 5 個 MIL 分類頭 | 10.6-21.7 MB | 微不足道；凍結特徵分類器 |

單一元件的最大峰值記憶體為 1,062.5 MB（CLIP batch=64）。各主幹在獨立環境中分別測量，並非同時運行，故不應加總。RTX 4090 的 24 GB VRAM 大量閒置，意味著若函式庫支援，可使用更大批次或並行提取。

### 6.5 Gated Fusion vs. Late Fusion

| 面向 | Gated Fusion | Late Fusion |
|------|-------------|-------------|
| 參數量 | 498.11K | 633.22K |
| MACs | 15.96M | 20.29M |
| FLOPs | 31.92M | 40.57M |
| 延遲 | 1.050 ms | 1.153 ms |
| 吞吐量 | 15,237 S/s | 13,874 S/s |

Gated Fusion **參數量少 21%** 且**速度快 10%**。差異來自於 Gated Fusion 將兩個模態投影到共享的 256 維空間再進行門控，而非運行兩個完整的獨立分類頭。這對論文而言是有利的結果：更精密的融合機制同時也是更高效的。

---

## 7. 對論文的啟示

1. **運算成本由骨架提取主導，而非模型複雜度。** MIL 訓練迴圈本身幾乎是即時的。研究迭代速度受限於一次性的特徵提取。

2. **CLIP 特徵的提取成本極低**（相對於骨架特徵）。1 FPS 取樣加上批次推論使 CLIP 提取每片段便宜約 87 倍（UCF）至 520 倍（XD-Violence）。這證明了雙模態方法的合理性：在骨架管線中加入 CLIP，推論時幾乎不增加成本。

3. **Gated Fusion 頭增加的開銷可忽略不計**（~1 ms/batch），同時比 Late Fusion 更輕量。論文可以在準確度提升的同時宣稱效率優勢。

4. **若 RTMPose 支援批次推論，骨架管線有望大幅加速。** 目前 rtmlib 不支援批次推論，逐幀處理是主要瓶頸。理論下界為 30 ms / 64 幀 ≈ 0.47 ms/幀，但此假設完美線性加速，實際偵測器+姿態估計管線不太可能達到——此數值僅為樂觀參考，非實測。

5. **I3D 單次前向傳播的 FLOPs 最高**（每片段 107.9 GFLOPs）。注意此為每片段成本，不可直接與 CLIP 的每幀 22.5 GFLOPs 或 RTMPose 的每幀 3.2 GFLOPs 比較——歸一化後每片段成本為：I3D 107.9 G、CLIP（UCF）~495 G（22 幀 x 22.5）、RTMPose ~206 G（64 幀 x 3.2）。使用預提取 I3D 特徵仍是正確決定，因其不支援增量更新。

---

## 8. 重現方式

### MIL 分類頭

```bash
conda run -n vcc-main python scripts/benchmark_models.py
```

### 主幹特徵提取器

```bash
# 一次執行所有環境（推薦）：
C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --all

# 個別元件：
C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --clip
C:/Anaconda/envs/vcc-skeleton/python.exe scripts/benchmark_backbones.py --rtmpose
C:/Anaconda/envs/vcc-ctrgcn/python.exe scripts/benchmark_backbones.py --ctrgcn

# 合併結果為表格：
C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --combine
```

### 輸出檔案

| 檔案 | 內容 |
|------|------|
| `results/benchmark_models.csv` | MIL 分類頭指標（5 個模型）|
| `results/backbone_bench_clip.json` | CLIP ViT-B/16 詳細指標 |
| `results/backbone_bench_rtmpose.json` | RTMPose + YOLOX 詳細指標 |
| `results/backbone_bench_ctrgcn.json` | CTR-GCN 4 流詳細指標 |
| `results/backbone_bench_combined.csv` | 合併主幹比較 |

---

## 9. LaTeX 表格（論文可直接使用）

### MIL 分類頭

```latex
\begin{table}[t]
\centering
\caption{模型複雜度比較。}
\label{tab:model-complexity}
\begin{tabular}{lrrrrr}
\toprule
模型 & 參數量 (K) & MACs (M) & 延遲 (ms) & 吞吐量 (S/s) & 記憶體 (MB) \\
\midrule
Skeleton{-}Only & 37.57 & 1.21 & 0.504 & 31,766 & 10.6 \\
CLIP{-}Only & 595.65 & 19.07 & 0.690 & 23,181 & 14.8 \\
Late Fusion & 633.22 & 20.29 & 1.153 & 13,874 & 17.8 \\
Gated Fusion & 498.11 & 15.96 & 1.050 & 15,237 & 21.7 \\
RTFM{-}I3D & 137.41 & 4.46 & 0.460 & 34,786 & 18.8 \\
\bottomrule
\end{tabular}
\end{table}
```

### 主幹特徵提取器

```latex
\begin{table}[t]
\centering
\caption{主幹特徵提取器運算成本比較。}
\label{tab:backbone-cost}
\begin{tabular}{lrrrrr}
\toprule
主幹 & 參數量 (M) & FLOPs (G) & 延遲 & 吞吐量 & GPU 記憶體 (MB) \\
\midrule
CLIP ViT{-}B/16 & 86.2 & 22.5 & 67.8 ms/B & 944 f/s & 1,062 \\
RTMPose{-}m + YOLOX & $\sim$13.0 & $\sim$3.2 & 30.1 ms/f & 33.3 f/s & 213 \\
CTR{-}GCN (4{-}stream) & 5.7 & --- & 154.2 ms/sn & 6.5 sn/s & 29 \\
I3D RGB & $\sim$25.0 & $\sim$107.9 & 預提取 & --- & --- \\
\bottomrule
\end{tabular}
\vspace{2mm}
\footnotesize{$\sim$ 表示論文公開數據（非實測）。B = batch，f = frame，sn = snippet（64 幀）。}
\end{table}
```
