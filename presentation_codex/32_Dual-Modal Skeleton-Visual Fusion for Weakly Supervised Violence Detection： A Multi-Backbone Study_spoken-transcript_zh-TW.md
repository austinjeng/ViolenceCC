# CGW 2026 Spoken Transcript (Traditional Chinese)

Deck: 32_Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection： A Multi-Backbone Study.pptx

Presentation time: 10 minutes
Q&A: 2 minutes
Upload deadline: July 7, 2026, 23:59 (UTC+8)

Note: The slides are written in English. The spoken script below is written for delivery in Traditional Chinese and is also embedded in the PPTX speaker notes.

## Slide 1: Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection [0:00-0:25]

各位老師、各位先進大家好，我是鄭維翰。今天要報告的題目是「Dual-Modal Skeleton-Visual Fusion for Weakly Supervised Violence Detection: A Multi-Backbone Study」。這是 CGW 2026 的第 32 號論文。這個研究的核心問題很直接：在弱監督暴力偵測裡，如果我們不微調大型 backbone，也不使用文字分支，只訓練一個很小的 fusion head，骨架動態到底能不能補足視覺語意特徵的不足？

## Slide 2: Violence detection needs motion, not appearance alone [0:25-1:10]

先說問題背景。弱監督 video anomaly detection 只使用影片層級標籤，也就是一段影片是不是包含異常，而不是逐幀標註。這讓訓練成本降低很多，但模型必須自己從影片片段中找出可疑時間點。近年的 frozen CLIP 或 vision-language feature 很有效率，可是它們主要看的是外觀與語意；暴力事件像打鬥、攻擊、車禍，常常真正重要的是人體動作與時間動態。另外，實際部署時還會遇到雜訊、模糊、壓縮和亮度變化，所以我們也想知道這種 frozen fusion 系統在測試時間能不能調整可靠性。

## Slide 3: The study asks what skeletons add to frozen VLM detectors [1:10-1:55]

因此這篇論文有三個貢獻。第一，我們提出一個 gated dual-modal fusion 架構，把 frozen CTR-GCN 的骨架特徵和 frozen CLIP 或 SigLIP2 的視覺語言特徵結合起來，只有 fusion head 和 MIL classifier 會被訓練。第二，我們不是只測一個 backbone，而是系統性比較四個 visual backbone，在 UCF-Crime 和 XD-Violence 上用三個 random seeds 做評估。第三，我們分析測試時間調適：TENT 和 SAR 在這個 LayerNorm-based frozen detector 上幾乎沒有作用，接著提出一個不需要標籤、也不需要調參的 reliability reweighting 方法。

## Slide 4: Two frozen streams feed one lightweight trained head [1:55-2:50]

這張圖是整體架構。上方是骨架 stream：先用 RTMPose 抽出 COCO 十七個 keypoints，保留前兩個人，再用在 NTU RGB+D 120 預訓練的 CTR-GCN 取出 256 維 snippet 特徵。下方是視覺 stream：我們約每秒取一張影格，經過 CLIP 或 SigLIP2 backbone，再用 mean 和 max pooling 合併成 snippet 特徵。兩個 stream 都是 frozen。訓練的只有中間的 gated fusion 和 MIL head，參數量大約是 0.50 到 1.02 百萬，在一張 RTX 4090 上每個設定少於五分鐘可以訓練完成。

## Slide 5: Gating learns when to trust each modality [2:50-3:35]

Fusion 的做法是先把兩個 modality 都投影到同一個 256 維空間，並各自做 LayerNorm。接著 gate 會根據兩個投影後的特徵，產生每一個維度的權重。重點是我們不是把其中一個 modality 關掉，而是透過 residual 讓兩個訊號都保留，再由 gate 調整相對貢獻。訓練目標使用 MIL ranking loss，讓 abnormal video 裡 top-k snippet 分數高於 normal video。為了比較，我們也測了 late fusion，也就是兩個 modality 固定五五平均；結果會看到，固定權重在 XD-Violence 上會明顯傷害效能。

## Slide 6: The protocol isolates fusion and backbone effects [3:35-4:15]

實驗設計上，我們使用兩個常見 benchmark。UCF-Crime 有一千九百支影片、十三類異常，指標是 frame-level ROC-AUC。XD-Violence 有四千七百五十四支影片、六類暴力事件，指標是 frame-level Average Precision。四個 backbone 分別是 CLIP ViT-B/16、SigLIP2 ViT-B/16、SigLIP2 SO400M 和 SigLIP2 Giant。所有 encoder 都 frozen，使用相同 split 和 protocol，並報告三個 seeds 的平均和標準差。

## Slide 7: Gated fusion sets the headlines without training the backbones [4:15-5:10]

主要結果有三個數字。第一，UCF-Crime 的最佳結果是 SigLIP2 Giant 的 gated fusion，達到 82.5% AUC。第二，XD-Violence 的最佳結果是 SigLIP2 SO400M 的 gated fusion，達到 78.7% AP。第三，在 corrupted UCF-Crime-C 上，我們的 reliability reweighting 平均提升 1.21 個百分點。雖然骨架單獨表現不強，UCF 只有 68.8 AUC，XD 只有 40.8 AP，但放進 gated fusion 後，八個 backbone-by-dataset 設定都至少不低於 visual-only，其中六個是嚴格提升。這說明骨架不是取代視覺，而是提供小但穩定的互補資訊。

## Slide 8: Backbone choice is dataset-specific and visible after fusion [5:10-6:05]

這張圖整理四個 backbone 和三種 fusion variant。左邊是 UCF-Crime，右邊是 XD-Violence。可以看到 UCF 上 SigLIP2 Giant 最好；但 XD 上，visual-only 的四個 backbone 其實都在 seed variance 附近，真正透過 gated fusion 拉開的是 SO400M。另一個重點是 late fusion 幾乎不是好選擇，特別是在 XD 上，每個 backbone 都比 gated fusion 低超過十個 AP。這表示 skeleton signal 雖然有用，但必須用 input-dependent weighting，而不是固定平均。

## Slide 9: Skeletons carry different evidence, not stronger evidence [6:05-6:45]

這裡用骨架 overlay 直觀說明 skeleton stream 捕捉的是人體關節與動作，而不是影像外觀。這個表示法有兩個優點：一方面，它能補到視覺語意模型可能忽略的動態資訊；另一方面，在 keypoints 已經被抽出並快取的情況下，它對某些 pixel-level corruption 比較不敏感。不過我們也很誠實地看到，骨架單獨不夠強，會受到姿態估計品質、人物遮擋、影片 frame rate 和 snippet 長度影響。因此我們把它定位為 complementary modality，而不是主模型。

## Slide 10: This is a constrained regime, not a SOTA claim [6:45-7:35]

接著是和相關方法的定位。這篇工作不宣稱 state of the art。可比的 regime 是 frozen features、沒有文字分支、單張 GPU 等級的小型 head。在這個範圍內，我們的 XD 78.7 AP 接近 RTFM 和 MGFN-I3D；UCF 82.5 AUC 則低於現代 frozen-feature 方法，例如 CLIP-TSA、UR-DMU 和 MGFN。這個差距是合理的，因為我們刻意排除了 text alignment、audio、MLLM 或 backbone fine-tuning。換句話說，這篇工作的重點是可重現、低成本、多 backbone 的 dual-modal study，以及 robustness 分析，而不是追求最高排行榜分數。

## Slide 11: Entropy TTA cannot move this frozen rank-based detector [7:35-8:30]

測試時間調適的結果很有意思。我們建立 UCF-Crime-C，包含四種 corruption、五個 severity，一共二十個條件。TENT 和 SAR 在這個架構裡只能更新 fusion head 的 LayerNorm affine 參數，總共 1,536 個 scalar。結果三個 seeds、四個 backbone 都一樣，AUC 的改變小於 0.1 個百分點。這不是沒有調好，而是結構限制：corruption 造成的偏移在 frozen upstream features 裡，LayerNorm affine 的小更新不足以改變 snippet 排名，而 AUC 又是一個純排名指標。

## Slide 12: Reliability reweighting changes routing instead of parameters [8:30-9:25]

因此我們改用 reliability reweighting，不更新任何參數。想法是觀察 visual-only anomaly scores 的分散度；如果 corruption 讓 visual stream 失去區分能力，score spread 會塌縮，這時就降低 visual contribution，讓 fusion 多相信骨架 stream。如果 visual stream 仍然可靠，或 skeleton 也受到 corruption 影響，gate 就不動作。這個方法不需要標籤、不需要調參，平均提升 corrupted-AUC 1.21 個百分點，在四個 backbone、三個 seeds 上都是正向；最大提升出現在 Gaussian noise severity 5，達到 13.2 個百分點。這不是全面 robustness，而是針對一個 modality 還健康時的 rescue mechanism。

## Slide 13: Takeaways [9:25-10:00]

最後總結三點。第一，骨架特徵單獨不強，但在 gated fusion 裡提供小而穩定的互補增益。第二，backbone 選擇和資料集有互動，不能只看 general benchmark；UCF 偏向 Giant，XD 則在 gated fusion 下偏向 SO400M。第三，對 frozen、LayerNorm-based、rank-based detector 來說，entropy TTA 很難有效；比較可行的是 reliability-aware routing。限制也很清楚：frozen no-text 設計犧牲 peak AUC，reweighting 是 transductive，目前只在兩個資料集和 synthetic corruptions 上驗證。以上是我的報告，謝謝大家，歡迎提問。

## Q&A opening [10:00-12:00]

以上是我的報告，謝謝大家。接下來兩分鐘歡迎提問。若問題與比較方法有關，我會先區分是否包含 text branch、audio、MLLM 或 fine-tuning；若問題與 TTA 有關，我會先說明這裡的 gain 是 corrupted-AUC 的 rescue gain，不代表 clean AUC 也會上升；若問題與部署有關，我會強調目前 reweighting 使用 whole-condition statistics，streaming 版本會是後續工作。
