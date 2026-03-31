# Domain Pitfalls

**Domain:** Weakly Supervised Violence-Oriented Video Anomaly Detection — Dual-Modal Skeleton+CLIP with TTA
**Researched:** 2026-03-31
**Scope:** PYSKL/CTR-GCN integration, skeleton extraction in violent scenes, MIL training, feature alignment, evaluation protocol, TTA implementation, and thesis-level research methodology

---

## Critical Pitfalls

Mistakes that cause rewrites, invalidate results, or block thesis submission.

---

### Pitfall C1: Skeleton Coordinate Space Mismatch Between RTMPose and CTR-GCN Input

**What goes wrong:** RTMPose outputs keypoints in *pixel coordinates* relative to the original frame resolution (e.g., x=320, y=180 for a 640x360 frame). PYSKL's preprocessing pipeline for CTR-GCN expects coordinates *normalized to [0,1]* or *centered and scaled* relative to the image size. Feeding raw pixel coordinates produces numerical values orders of magnitude larger than what the pretrained NTU120 HRNet 2D weights expect, causing the feature extractor to output garbage embeddings — often all-zero or all-saturated — with no error message.

**Why it happens:** rtmlib returns raw (x, y, score) pixel coordinates. The PYSKL data pipeline has a `PoseNormalize` or `PreNormalize2D` transform in its config files that performs this normalization before passing data into CTR-GCN. When you bypass the PYSKL training pipeline and call CTR-GCN directly as a feature extractor, these transforms are not applied automatically.

**Consequences:** CTR-GCN 256-d features become meaningless. The MIL head trains on noise. AUC appears slightly above chance (55-60%) and the researcher wastes weeks tuning MIL hyperparameters looking for the wrong cause.

**Prevention:**
1. Before any full-dataset extraction: run a single video through PYSKL's official pipeline, print the input tensor statistics (mean, std, min, max), and match them when building your own extractor.
2. Apply the same normalization as PYSKL's `PreNormalize2D` transform: subtract the centroid of all visible joints, divide by a scale factor proportional to image size.
3. Add a debug assertion: after normalization, joint coordinates should be in roughly [-1, 1] range; log a warning if any value exceeds 5.0.

**Warning signs:** CTR-GCN output features have near-zero variance across all videos; cosine similarities between random video features are all >0.99.

**Phase:** Address in Phase 1 (Week 1) during the CTR-GCN forward-pass verification step. Must be resolved before any full-dataset extraction begins.

---

### Pitfall C2: Temporal Misalignment Between Skeleton Snippets and CLIP Snippets

**What goes wrong:** The skeleton branch processes 64-frame windows. CLIP extracts one embedding per second (1 FPS). If the frame-to-second mapping is not computed from the *actual video FPS* (which varies across UCF-Crime and XD-Violence: some videos are 24 FPS, some 30 FPS, some other values), then a "64-frame skeleton snippet" at 30 FPS covers ~2.1 seconds, but the same snippet at 24 FPS covers ~2.7 seconds. CLIP features pulled using a fixed second-count will cover a different temporal window than the skeleton features for variable-FPS videos, creating systematic misalignment.

**Why it happens:** Researchers often assume uniform FPS across a dataset. UCF-Crime and XD-Violence both contain videos at mixed frame rates. A fixed "stride = 64 frames, CLIP uses frames 0, 64, 128..." approach drifts when FPS varies.

**Consequences:** The fusion model receives (skeleton_snippet_t, clip_snippet_t') where t != t'. For coherent anomaly events (e.g., a 1-second fight), skeleton features may capture the punch while CLIP features capture the aftermath or preceding normal moment. The model is forced to learn from misaligned evidence, reducing fusion benefit and increasing variance of results.

**Prevention:**
1. At extraction time, read actual FPS from each video using `cv2.VideoCapture.get(cv2.CAP_PROP_FPS)` and store it in the pickle metadata.
2. Map all temporal indices to wall-clock seconds before computing snippet boundaries.
3. For CLIP, extract frames at the exact timestamps corresponding to the center of each skeleton snippet window (not at fixed second intervals).
4. Add a sanity check: for each snippet, verify that the skeleton timestamp range and the CLIP timestamp overlap by at least 90%.

**Warning signs:** CLIP-Only baseline significantly outperforms Late Fusion on short-duration anomaly categories; suspicious performance variance between videos.

**Phase:** Address in Phase 1 (Week 2) before the feature caching layer is finalized.

---

### Pitfall C3: Data Leakage via Test Set in Hyperparameter Tuning

**What goes wrong:** The official UCF-Crime and XD-Violence test sets contain frame-level annotations. It is tempting — especially under time pressure — to monitor frame-level AUC on the test set during training to decide when to stop or which model checkpoint to keep. This constitutes data leakage: the test set's annotations are used to make modeling decisions, which inflates reported numbers and makes the comparison with prior work methodologically invalid.

**Why it happens:** The training sets for both UCF-Crime and XD-Violence have only *video-level* labels, making it impossible to compute frame-level AUC on training data. Researchers reach for the test set because it is the only source of frame-level signal.

**Consequences:** Results appear better than the model actually is. The gap inflates as more hyperparameter decisions are made with test set guidance. Reviewers and examiners who probe methodology will catch this.

**Prevention:**
1. The PRD v2.3 already specifies the correct protocol: cut a 15% internal validation split from the training set, fixed by random seed, before any experiment begins.
2. Use validation *MIL Ranking Loss* — not frame-level AUC — as the early stopping signal. This is consistent, calculable without frame-level labels, and matches the training objective.
3. Physically separate the test set: do not load test annotations into any training or validation script. Only load them in a standalone `evaluate.py` script that is called after all model selection decisions are finalized.
4. Document the exact train/val split seed in the experiment log. All ablations must use the identical split.

**Warning signs:** You find yourself checking test AUC more than once per ablation variant; test AUC rises while validation loss plateaus.

**Phase:** Address in Phase 1 (Week 2) when constructing the validation split. Non-negotiable before any MIL training begins.

---

### Pitfall C4: Wrong Frame-Level AUC Calculation (Label Alignment Error)

**What goes wrong:** Computing frame-level AUC requires aligning per-frame anomaly scores with per-frame ground-truth labels. The temporal annotation format in UCF-Crime and XD-Violence specifies anomaly start/end times in *seconds* and sometimes in *frame indices*. If the anomaly score is computed at the *snippet level* (one score per 64-frame block) rather than replicated to all frames in that block, then the AUC calculation uses mismatched lengths and either crashes, silently truncates, or produces a number that is meaningless.

**Why it happens:** MIL models output one score per snippet. Researchers post-process by assigning the snippet score to all frames in the snippet window. If the last snippet does not evenly divide the video length, off-by-one errors create a score vector shorter than the ground-truth label vector.

**Consequences:** AUC numbers appear unusually high (>90%) or low (<70%) with no obvious cause. The evaluation looks correct but measures the wrong thing. Published numbers become non-reproducible.

**Prevention:**
1. Use the exact same frame-to-snippet mapping function both during feature extraction AND during evaluation score expansion. Encapsulate this in a single utility function used everywhere.
2. After expanding snippet scores to frame scores: `assert len(frame_scores) == len(frame_labels)` before computing AUC.
3. Cross-validate against RTFM's official evaluation code. RTFM's eval script for UCF-Crime is the community reference; replicate its exact behavior.
4. Report AUC using `sklearn.metrics.roc_auc_score` with `max_fpr=None` (full ROC curve), not partial AUC, to match existing literature convention.

**Warning signs:** Your RTFM reproduction number deviates by more than 2% from the published 84.30%; inconsistent AUC numbers when re-running identical code.

**Phase:** Address in Phase 1 (Week 2) during baseline RTFM reproduction. The reproduction step exists precisely to catch this class of bug.

---

### Pitfall C5: MIL Training Collapses to Trivial Solutions

**What goes wrong:** The MIL Ranking Loss (as used in RTFM) requires that the top-k anomaly scores from an anomalous bag exceed the top-k scores from a normal bag. Two trivial solutions satisfy this without learning anything useful: (a) the model outputs a constant high score for all snippets in all videos, or (b) the model learns to detect video-level features rather than snippet-level anomalies, outputting high scores for all snippets of labeled-anomalous videos. Both manifest as near-perfect video-level classification accuracy but poor frame-level AUC.

**Why it happens:** The MIL loss does not penalize the model for assigning high scores to normal snippets within an anomalous video. Label noise — normal snippets in anomalous training videos receiving implicit high-score pressure — is inherent to weak supervision. Without a smoothness or sparsity regularizer, the path of least resistance is to score all snippets of anomalous videos uniformly high.

**Consequences:** Frame-level AUC stagnates at 60-72% while training loss converges quickly. The model cannot localize anomalies, only detect anomalous videos.

**Prevention:**
1. Add a *temporal smoothness regularizer* or *sparsity penalty* to the loss: penalize large variance in consecutive snippet scores, or penalize the mean anomaly score of anomalous videos being too high (not just the top-k).
2. Monitor both video-level classification AUC and frame-level AUC during training. If the former is high (>90%) and the latter is low (<70%), the model has collapsed to a video-classifier.
3. Use the same bag-construction as RTFM: each batch contains one anomalous video and one normal video; top-k snippets drawn from *each video independently*.
4. Do not use batch sizes larger than recommended (32 snippets per video, not 32 videos) during early training; large batches make the ranking loss easier to satisfy trivially.

**Warning signs:** Training loss drops rapidly in the first 5 epochs then plateaus; snippet score distributions are bimodal with all-high or all-low per video rather than varying within videos.

**Phase:** Address in Phase 2 (Weeks 3-4) when implementing the MIL head. Monitor during single-modal baselines before fusion adds confounding variables.

---

### Pitfall C6: CTR-GCN Input Shape Errors with Violent Multi-Person Scenes

**What goes wrong:** CTR-GCN expects input shape `[N, C, T, V, M]` where M=2 (persons), V=17 (COCO joints), T=64 (frames). When fewer than 2 people are detected in a snippet (e.g., single-person frames), naively passing M=1 causes a shape mismatch. When more than 2 people are detected, selecting "top-2 by confidence" is easy to implement incorrectly — ranking by bounding-box confidence score rather than pose estimation confidence score gives different results, and the two may disagree.

**Why it happens:** Violent scenes are specifically where multi-person detection is most chaotic: people partially occlude each other, tracking IDs swap between frames, and confidence scores fluctuate rapidly.

**Consequences:** Silent padding errors (padding with zeros for missing persons) produce a systematic bias in features: zero-padded skeletons look like a "frozen standing person" to CTR-GCN, which biases the feature toward normal-looking representations even in violent snippets.

**Prevention:**
1. Always pad to M=2 with *mean-person pose* (the average of visible joints across all detected persons in the snippet), not zeros. This is closer to the distribution CTR-GCN saw during NTU120 training.
2. When selecting top-2 persons: rank by *average keypoint confidence across all 17 joints in the snippet window*, not by detection confidence of a single frame.
3. Track person IDs across the 64-frame window before extracting CTR-GCN features; do not re-rank per frame (this causes the M=0 position to swap between different people across frames, producing nonsensical motion patterns).
4. Log the fraction of snippets where person count < 2 per video; if this exceeds 30% in a video, flag for manual inspection.

**Warning signs:** Skeleton-Only baseline performs worse on Fighting/Assault categories specifically (where multi-person density is highest) than on single-person anomaly categories.

**Phase:** Address in Phase 1 (Week 2) during skeleton extraction, and verify during Phase 2 (Week 3) skeleton-only baseline.

---

## Moderate Pitfalls

Mistakes that degrade results or create confusion without causing complete failure.

---

### Pitfall M1: RTMPose Confidence Threshold Too High or Too Low

**What goes wrong:** rtmlib's default keypoint threshold (kpt_thr=0.5) works well for clear, well-lit footage. In violent scenes with motion blur, camera shake, close-range fighting, and occlusion, a threshold of 0.5 will zero out many joints in valid poses, producing sparse skeletons. Setting it too low (e.g., 0.1) includes phantom joints from background noise. Either extreme degrades CTR-GCN feature quality.

**Why it happens:** The threshold is a global setting applied uniformly. Violent scenes have systematically lower pose confidence than normal scenes, creating a selection bias: high thresholds produce better skeletons for normal scenes than for the violent scenes you most care about.

**Prevention:**
1. Run RTMPose on a sample of 20 videos per category (Fighting, Normal) and plot the distribution of per-joint confidence scores.
2. Use a threshold of 0.3-0.4 for violent scene datasets rather than the default 0.5. This retains more joint information for challenging frames.
3. For joints below threshold, store the estimated position with score=0 rather than zeroing the coordinate — CTR-GCN can weight low-confidence joints less through learned channel attention.
4. Report the average skeleton coverage (fraction of joints above threshold, averaged over all frames) as a data quality metric in the thesis appendix.

**Warning signs:** >50% of keypoints in Fighting-category videos have confidence below threshold; skeleton visualizations show disconnected, implausible poses.

**Phase:** Address in Phase 1 (Week 2) during the skeleton quality check step.

---

### Pitfall M2: CLIP Mean+Max Pooling Projection Layer Not Properly Initialized

**What goes wrong:** The mean+max pooling strategy concatenates two 512-d CLIP vectors to a 1024-d vector, then projects to 512-d via a linear layer. If this projection layer is randomly initialized and the training signal is weak (early in MIL training), the projection can amplify or cancel information from mean vs. max components asymmetrically, producing pooled features that are dominated by one component. This is not visible from training loss alone.

**Why it happens:** The projection is a learned component inside what is conceptually a "fixed feature extraction" stage. It sits in an ambiguous zone: conceptually it is preprocessing, but it is trained with the MIL head.

**Prevention:**
1. Initialize the projection with near-identity weights where possible: initialize such that the output is approximately `mean(mean_feat, max_feat)` at initialization (set weights to 0.5 for both halves, add small Gaussian noise).
2. Alternatively, freeze the pooling projection in the first 10 epochs of MIL training, then unfreeze.
3. Monitor the L2 norm of mean-component contribution vs. max-component contribution in the fused 512-d space throughout training.

**Warning signs:** Ablation showing mean-only vs. mean+max pooling yields no difference (suggesting max component is zeroed out by the projection).

**Phase:** Address in Phase 2 (Week 3) when implementing the CLIP branch.

---

### Pitfall M3: VRAM Overflow During Skeleton Extraction at Scale

**What goes wrong:** RTMPose + YOLOX (or the rtmlib detector) running on RTX 4090 can extract skeletons at ~200-300 FPS. For UCF-Crime (~10M frames), the bottleneck is not GPU compute but rather: (a) loading video files from disk into CPU RAM, decoding, and transferring to GPU; (b) accumulating skeleton results in a Python list before serializing to pickle, which can exhaust RAM for long videos; (c) running detection and pose estimation in a tight loop without periodic garbage collection.

**Why it happens:** A naive implementation extracts all frames of a video into a list, runs inference, then serializes. For a 10-minute UCF-Crime video at 30 FPS = 18,000 frames, holding all decoded frames in CPU RAM simultaneously requires ~2 GB per video (at 1080p RGB).

**Consequences:** OOM crash after hours of extraction, requiring restart. For XD-Violence (40+ hours of extraction), a crash at hour 35 means repeating 35 hours of work.

**Prevention:**
1. Use a streaming / chunk-based extraction: process and immediately serialize N=500 frames at a time, never holding more than N frames in CPU RAM.
2. Implement checkpointing: save partial results every 100 videos with a "processed" manifest file; on restart, skip already-processed videos.
3. Monitor GPU memory explicitly with `torch.cuda.memory_allocated()` every 1000 frames; log if it exceeds 18 GB (leaving 6 GB headroom).
4. For rtmlib specifically: call `gc.collect()` and `torch.cuda.empty_cache()` every 500 videos.
5. Store skeleton data in compressed numpy format (`.npz`) rather than raw `.pkl` during extraction; convert to PYSKL pickle format as a post-processing step.

**Warning signs:** Memory usage grows monotonically across a long extraction run; `htop` shows Python process RAM growing without bound.

**Phase:** Address in Phase 1 (Week 2). Must be solved before starting the XD-Violence overnight extraction.

---

### Pitfall M4: Feature Cache File Format Inconsistency Between Extraction and Training

**What goes wrong:** Features are extracted and cached as numpy `.npy` files. The MIL training code loads them with assumed shapes and dtypes. If the extraction code serializes CTR-GCN features as `float32` but saves CLIP features as `float16` (to save disk space), and the fusion head concatenates them without explicit type promotion, PyTorch will raise a cryptic dtype mismatch error or silently cast. More subtly: if feature normalization (L2 normalization, z-score) is applied during extraction for one branch but not the other, the effective learning rate and gradient scale will be mismatched.

**Why it happens:** Feature extraction and MIL training are written at different times (Week 2 vs. Week 3-4). The interface between them (file format specification) is rarely fully documented in research code.

**Prevention:**
1. Write a `feature_schema.py` file on Day 1 of feature extraction that defines: dtype, shape, normalization status, and version for every feature type. Load this schema in the MIL training code and assert conformance at startup.
2. Apply L2 normalization consistently to all feature branches before caching; or do not normalize any branch. Do not mix normalized and unnormalized.
3. After extraction, run a `validate_cache.py` script that loads 100 random feature files and checks: shape matches expected, no NaN/Inf values, values in plausible range.

**Warning signs:** Training crashes within the first batch with a dtype error; training runs but loss is orders of magnitude larger or smaller than expected.

**Phase:** Address at the boundary of Phase 1 and Phase 2 (end of Week 2 / start of Week 3).

---

### Pitfall M5: TTA Entropy Minimization on Anomaly Score Distributions Is Unstable Without Score Filtering

**What goes wrong:** TENT-style adaptation minimizes the entropy of the model's output distribution to make predictions more confident. In the VAD context, the output is an anomaly score (scalar, interpreted as p(anomaly)). The binary entropy H = -p*log(p) - (1-p)*log(1-p) is maximized at p=0.5 (maximum uncertainty). For a test video containing a mix of normal and anomalous snippets, minimizing entropy will push all scores toward either 0 or 1. For batches that happen to be predominantly normal, entropy minimization will push all scores toward 0, collapsing the model's ability to score anomalies in that video.

**Why it happens:** The adaptation protocol specifies 32-snippet batches drawn sequentially from a video. In a 5-minute UCF-Crime test video with a 30-second anomaly, ~90% of snippets are normal. The entropy signal from 29 normal snippets overwhelms the signal from 3 anomalous snippets in a 32-snippet batch.

**Consequences:** TTA degrades performance (negative transfer) on videos with short or rare anomalies, which is precisely the category of hardest cases. This is a known issue in TTA on anomaly streams and should be addressed as a methodological contribution, not hidden.

**Prevention:**
1. Apply SAR-style gradient filtering: before each adaptation step, compute per-sample entropy gradients and exclude samples with gradient magnitude below a threshold (they are probably normal and would push toward a trivial solution).
2. Consider *symmetric entropy* adaptation: push high-confidence normal snippets toward 0 more strongly than uncertain snippets. Use asymmetric weighting that amplifies high-anomaly-score snippets in the entropy gradient.
3. In the thesis discussion: explicitly analyze the entropy distribution over adaptation batches and contrast behavior on short-anomaly vs. long-anomaly videos.
4. Always report per-video TTA improvement breakdown — aggregate AUC can mask improvement on easy videos offsetting degradation on hard videos.

**Warning signs:** TTA improves mean AUC marginally but degrades performance on Fighting/Assault category specifically; per-batch entropy decreases faster than expected.

**Phase:** Address in Phase 3 (Week 6) when implementing TTA. The SAR-style filtering is the primary defense.

---

### Pitfall M6: SAR Sharpness Threshold (rho) Sensitivity in Small-Batch Video Context

**What goes wrong:** SAR's sharpness-aware minimization perturbs model parameters by epsilon=rho*||w||/||grad|| in a neighborhood ball to find parameters with flatter entropy loss. The rho hyperparameter controlling perturbation size is highly sensitive: too small → identical to vanilla TENT-style; too large → perturbs into meaningless parameter regimes. SAR's official rho=0.05 is calibrated for ImageNet-scale classification with batch_size=64. With batch_size=32 (32 snippets from one video) and a very narrow anomaly score distribution (not a 1000-class softmax), the same rho produces drastically different behavior.

**Why it happens:** TTA hyperparameters are implicitly calibrated to the source domain's output dimensionality and batch statistics. Adapting a 2-class (or even scalar) anomaly scorer is a different regime than adapting a 1000-class classifier.

**Prevention:**
1. Include rho in the grid search: {0.005, 0.01, 0.05, 0.1, 0.5}. The optimal value is likely an order of magnitude smaller than ImageNet defaults due to the scalar output.
2. Verify SAR behavior: after each adaptation step, check that the adapted LN parameters (gamma, beta) have not moved more than 20% from their source-trained values. If they move by 200%, rho is too large.
3. Report sensitivity analysis: show TTA performance vs. rho as a supplementary figure. This turns a potential weakness into a methodological contribution.

**Warning signs:** SAR-style performs worse than no-adapt (Source-Only) across all corruption levels; LN gamma values diverge to >2x or <0.5x of initial values after adaptation on a single video.

**Phase:** Address in Phase 3 (Week 6). Include in the hyperparameter grid search during TTA implementation.

---

### Pitfall M7: Wrong Corruption Applied to Both Modalities Unevenly

**What goes wrong:** UCF-Crime-C applies image-level corruptions (Gaussian noise, motion blur, JPEG compression, brightness shift) to RGB frames. This directly degrades CLIP features. However, skeleton extraction via RTMPose operates on the *same corrupted RGB frames*, meaning the corruption also degrades skeleton detection quality — particularly for motion blur and JPEG compression. If the experiment only re-extracts CLIP features for corrupted videos but reuses the clean skeleton features, the experiment measures "how well CLIP adapts when skeleton is clean and oracle", which is not the real deployment scenario.

**Why it happens:** Skeleton extraction is slow (5-8 hours for UCF-Crime). Re-running it for all 20 corruption conditions is expensive. The temptation is to reuse clean skeletons.

**Consequences:** TTA results are artificially favorable for the skeleton branch (it sees clean data while CLIP sees corrupted data). The corruption experiment no longer represents a realistic domain shift scenario. If a reviewer asks "did you re-extract skeletons for corrupted videos?", the answer must be yes.

**Prevention:**
1. For Gaussian noise and brightness shift: skeleton extraction is relatively robust to these corruptions (RTMPose was trained with data augmentation including these). It is defensible to reuse clean skeletons with a footnote explaining this.
2. For motion blur and JPEG compression (quality 10-20): re-extract skeletons because detection performance degrades significantly. Apply the corruption at the frame level before running RTMPose.
3. In the thesis: explicitly state which corruptions required skeleton re-extraction and which did not, and justify the decision.
4. As a minimum: run RTMPose on 50 corrupted frames per corruption type and measure the drop in mean keypoint confidence. Use this as the criterion for whether re-extraction is needed.

**Warning signs:** Skeleton-Only model shows no AUC degradation under motion blur corruption (implausible if clean skeletons are truly reused).

**Phase:** Address in Phase 3 (Week 6) during UCF-Crime-C creation.

---

## Minor Pitfalls

Mistakes that waste time, create confusion, or reduce result quality without being catastrophic.

---

### Pitfall m1: Gated Fusion Gate Values Saturate Early

**What goes wrong:** The Sigmoid gate g = sigma(W_g * [F_skel; F_clip] + b) saturates to near-0 or near-1 for all samples by epoch 10, effectively turning the Gated Fusion into Late Fusion (if always ~0 or ~1) or a fixed-weight combination. When this happens, the model misses the adaptive modality weighting benefit that motivates Gated Fusion.

**Prevention:**
1. Monitor the distribution of gate values across training batches. If mean(g) < 0.1 or > 0.9 by epoch 10, the gate has saturated.
2. Add an auxiliary gate diversity loss: penalize KL divergence of gate distribution from Uniform(0,1) during early training.
3. Initialize W_g with smaller weights (scale by 0.1) to keep initial gate values near 0.5 (maximum uncertainty).

**Phase:** Phase 2 (Week 4).

---

### Pitfall m2: XD-Violence ZIP Extraction Ordering and File Naming

**What goes wrong:** XD-Violence is distributed as multiple numbered ZIP archives (1-1004.zip, 1005-2004.zip, etc.). Extracting in parallel or with incorrect target directories can produce duplicate filenames (video IDs that appear in consecutive archives), silently overwriting some videos. The annotation file uses video filenames as keys; if filenames are wrong, features extracted for video X will be matched to labels for video Y.

**Prevention:**
1. Extract ZIPs sequentially to a single target directory.
2. After extraction, count total video files and compare to the expected 4,754. Verify that no video file is zero-bytes.
3. Cross-reference 100 random video filenames against the annotation file before starting feature extraction.

**Phase:** Phase 1 (Week 1-2).

---

### Pitfall m3: Validation Split Imbalance Creates Misleading MIL Loss Signal

**What goes wrong:** UCF-Crime training set has 810 normal + 800 anomalous videos. A 15% random split should produce ~120 normal + ~120 anomalous in validation. If the random seed accidentally produces a split with 150 normal + 90 anomalous, the MIL Ranking Loss on the validation set will be systematically lower (easier to satisfy) and will not accurately reflect generalization.

**Prevention:**
1. Use *stratified* random splitting to preserve the normal/anomalous ratio exactly.
2. Verify split balance after creation: `assert abs(n_normal_val / n_total_val - 0.5) < 0.05`.
3. Save the split as a text file listing video IDs; commit it to version control so all experiments use an identical split.

**Phase:** Phase 1 (Week 2).

---

### Pitfall m4: Statistical Instability from Insufficient Repetitions on Key Results

**What goes wrong:** MIL training with a fusion head is sensitive to random initialization. A single run can produce AUC numbers that vary by ±0.5-1.0% between runs. Reporting a single-run result in a thesis table can misrepresent the model's actual performance. Even worse: if Gated Fusion happens to outperform Late Fusion by 0.4% in a single run, but the true mean difference is 0.2% with std 0.3%, the ablation table overstates the benefit.

**Prevention:**
1. Run all primary result experiments 3 times with different random seeds; report mean ± std.
2. For ablation experiments, run at least 2 times; if runs disagree by more than 0.5%, run a third.
3. The PRD already mandates 3 runs for key results — enforce this rigorously.

**Phase:** Phase 5 (Week 9) for the final results table.

---

### Pitfall m5: TTA Per-Video Reset Not Actually Resetting

**What goes wrong:** The adaptation protocol resets LN affine parameters (gamma, beta) to source-trained values at the start of each test video. A common implementation mistake: storing the initial state dict at model creation time, but then the model is passed through one epoch of normal training that updates LN parameters, and the "initial state" reference was captured before training completed. The per-video reset then resets to a partially-trained state rather than the source-trained state.

**Prevention:**
1. Capture the reset state dict after training is fully complete and the best checkpoint is loaded.
2. Store only the LN parameter values (gamma, beta of each LN layer) in a dedicated `ln_state_init` dict, separate from the full model state dict.
3. Add a test: after resetting, compute the forward pass on a fixed test snippet and verify the output is deterministic (matches a pre-stored reference output from the source-trained model).

**Phase:** Phase 3 (Week 6) during TTA implementation.

---

### Pitfall m6: Novelty Claim Overclaiming Without Literature Scope Limitation

**What goes wrong:** The thesis novelty claim is "first to combine skeleton GCN + VLM for violence-oriented weakly supervised VAD". If the literature review misses a concurrent arxiv paper that does exactly this (or something very close), the claim is invalidated at defense. The field moves fast; a paper submitted to CVPR 2026 may not be indexed yet.

**Prevention:**
1. Run a literature search at the start of every phase (not just at thesis start) using Google Scholar, arxiv, and Semantic Scholar.
2. Query specifically: "skeleton GCN CLIP violence anomaly detection", "multimodal weakly supervised anomaly localization skeleton", "pose estimation video anomaly detection CLIP".
3. Scope the claim conservatively: "to the best of our knowledge, at the time of this writing" + explicit statement of what distinguishes this work even if something similar exists.
4. The PRD v2.3 already scopes the claim correctly ("violence-oriented weakly supervised VAD, as opposed to general action recognition"). Maintain this scoping and do not relax it.

**Phase:** Relevant throughout all phases; critical check in Phase 5 (Week 9) before finalizing the thesis introduction.

---

### Pitfall m7: CLIP Text Prompt Engineering Unreported and Irreproducible

**What goes wrong:** The PRD specifies using 20-30 LLM-generated text prompts for violence/normal descriptions as semantic prior. If these prompts are not version-controlled and documented, different runs may use different prompts, and results are not reproducible. More subtly: if prompt quality varies (some prompts contain descriptions that are ambiguous between violence and sport), CLIP text embeddings can encode the ambiguity and hurt the semantic prior quality.

**Prevention:**
1. Store all prompts in a versioned text file in the codebase before any CLIP text encoding.
2. Compute and inspect the cosine similarity between violence prompt embeddings and normal prompt embeddings. They should form clearly separated clusters (mean cosine similarity < 0.7 within-class, and violence vs. normal inter-cluster distance > 0.3).
3. Include the final prompt list in the thesis appendix.

**Phase:** Phase 2 (Week 3-4) when implementing the CLIP branch.

---

## Phase-Specific Warning Summary

| Phase | Topic | Primary Pitfall | Mitigation |
|-------|-------|----------------|------------|
| Phase 1 / Week 1 | CTR-GCN verification | C1: Coordinate space mismatch | Run forward-pass verification with coordinate statistics check before any batch extraction |
| Phase 1 / Week 2 | Skeleton extraction | C6: Multi-person padding errors | Implement mean-person padding; track person IDs across snippet window |
| Phase 1 / Week 2 | Skeleton extraction | M1: RTMPose confidence threshold | Use 0.3-0.4 threshold; visualize samples before full dataset run |
| Phase 1 / Week 2 | CLIP extraction | C2: Temporal misalignment | Read actual FPS per video; align all snippets to wall-clock time |
| Phase 1 / Week 2 | Validation split | C3: Test set leakage | Create stratified split; never load test annotations in training scripts |
| Phase 1 / Week 2 | Data management | M3: VRAM / RAM overflow in extraction | Implement streaming extraction with checkpointing before overnight XD-Violence run |
| Phase 1-2 boundary | Feature caching | M4: Format inconsistency | Finalize feature_schema.py before any MIL training; run validate_cache.py |
| Phase 2 / Week 2-3 | Baseline reproduction | C4: Wrong AUC calculation | Replicate RTFM eval code exactly; add shape assertion |
| Phase 2 / Week 3-4 | MIL training | C5: Trivial solution collapse | Monitor snippet-level score distributions; add sparsity penalty if needed |
| Phase 2 / Week 4 | Gated Fusion | m1: Gate saturation | Monitor gate distribution; initialize W_g with small weights |
| Phase 2 / Week 3 | CLIP branch | M2: Projection initialization | Near-identity init for mean+max projection; monitor component contribution |
| Phase 3 / Week 6 | TTA implementation | C3 variation: TTA hyperparameter grid without test set | Select TTA lr and rho on corruption validation set, not test set |
| Phase 3 / Week 6 | TTA implementation | M5: Entropy collapse on normal-heavy batches | Implement SAR-style gradient filtering before adaptation step |
| Phase 3 / Week 6 | TTA implementation | M6: SAR rho calibration | Grid search rho starting at 0.005 (lower than ImageNet default) |
| Phase 3 / Week 6 | TTA implementation | m5: Reset state not clean | Capture LN reset state from final trained checkpoint; add determinism test |
| Phase 3 / Week 6 | Corruption experiment | M7: Uneven corruption across modalities | Re-extract skeletons for motion blur + JPEG; justify reuse for noise + brightness |
| Phase 5 / Week 9 | Results reporting | m4: Single-run instability | All primary results: 3 runs, mean ± std |
| Phase 5 / Week 9 | Thesis writing | m6: Novelty claim | Re-run literature search; verify claim scope is properly bounded |
| Continuous | All | m7: Prompt engineering undocumented | Version-control all prompts from Week 3 onward |

---

## Engineering vs. Research Methodology Pitfall Distribution

**Engineering pitfalls** (wrong code, wrong format, wrong number):
C1, C2, C4, C6, M2, M3, M4, M7 (partial), m2, m3, m5

**Research methodology pitfalls** (wrong experimental design, wrong claims):
C3, C5, M5, M6, m1 (partially), m4, m6, m7

Both categories require equal attention. Engineering bugs produce wrong numbers; methodology errors produce meaningless correct numbers.

---

## Sources

- PYSKL paper and repository: [kennymckormick/pyskl on GitHub](https://github.com/kennymckormick/pyskl), [PYSKL ACM MM 2022](https://dl.acm.org/doi/10.1145/3503161.3548546)
- RTFM paper: [Tian et al., ICCV 2021](https://openaccess.thecvf.com/content/ICCV2021/papers/Tian_Weakly-Supervised_Video_Anomaly_Detection_With_Robust_Temporal_Feature_Magnitude_Learning_ICCV_2021_paper.pdf)
- rtmlib (RTMPose without mmcv): [Tau-J/rtmlib on GitHub](https://github.com/Tau-J/rtmlib)
- TENT paper and pitfalls: [Wang et al., ICLR 2021](https://openreview.net/forum?id=uXl3bZLkr3c), [DequanWang/tent on GitHub](https://github.com/DequanWang/tent)
- SAR paper: [Niu et al., ICLR 2023 Oral — arxiv 2302.12400](https://arxiv.org/abs/2302.12400), [mr-eggplant/SAR on GitHub](https://github.com/mr-eggplant/SAR)
- On Pitfalls of Test-Time Adaptation (ICML 2023): [Zhao et al., ICML 2023](https://proceedings.mlr.press/v202/zhao23d/zhao23d.pdf), [LINs-lab/ttab on GitHub](https://github.com/LINs-lab/ttab)
- Rethinking Metrics and Benchmarks of VAD: [arxiv 2505.19022](https://arxiv.org/html/2505.19022v1)
- Temporal resolution issues in weakly supervised VAD: [Springer Applied Intelligence 2023](https://link.springer.com/article/10.1007/s10489-023-05072-8)
- MIL training instability in weakly supervised VAD: [WACV 2024](https://openaccess.thecvf.com/content/WACV2024/papers/Karim_Real-Time_Weakly_Supervised_Video_Anomaly_Detection_WACV_2024_paper.pdf)
- TTA error accumulation and reset strategies: [arxiv 2603.03796](https://arxiv.org/html/2603.03796)
- PYSKL data format specification: [pyskl/tools/data/README.md](https://github.com/kennymckormick/pyskl/blob/main/tools/data/README.md)
- In Search of Lost Online TTA (survey): [IJCV 2024](https://link.springer.com/article/10.1007/s11263-024-02213-5)
