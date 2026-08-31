export const meta = {
  name: 'code-paper-match-audit',
  description: 'Audit whether ViolenceCC code/results match the CGW26 paper (main.tex) across 12 dimensions, then adversarially verify every finding',
  phases: [
    { title: 'Review', detail: '12 dimension reviewers find code/paper discrepancies' },
    { title: 'Verify', detail: 'adversarial skeptic re-checks each finding against the real files' },
  ],
}

// ---------------------------------------------------------------------------
// Shared context handed to every agent. Anchors them on the SAME ground truth.
// ---------------------------------------------------------------------------
const SHARED = `
PROJECT: D:\\ViolenceCC — PyTorch weakly-supervised violence VAD. Dual-modal (CTR-GCN skeleton + CLIP/SigLIP2 visual) gated fusion, MIL ranking loss, + a TTA study.

YOUR JOB: verify whether the CODE and RESULTS match what the PAPER claims. Report ONLY real discrepancies (with evidence) and explicitly-confirmed matches for the key claims. Do not invent issues.

CANONICAL PAPER = D:\\ViolenceCC\\paper\\main.tex  (this is the authoritative, inlined source — read it).
IMPORTANT ANCHORING RULES:
- paper/tables_generated.tex is NOT \\input by main.tex and is KNOWN-STALE (still shows an OLD Table 3). Do NOT treat it as authoritative; if it contradicts main.tex, that's a stale-artifact note at most. main.tex wins.
- The numbers data-flow has TWO layers:
    (a) per-run ground truth: results/<run>/eval_metrics.json  (fields: auc, ap, n_videos, n_frames, per_category, seed)
    (b) aggregated: results/phase10_charts/backbone_comparison_4way.csv (single-seed-42 per-cell, columns *_AUC/*_AP),
        results/phase10_charts/seed_stability_4way.csv (3 seeds 42/123/2024, used for Gated Fusion mean±std),
        results/tta_backbone/summary.csv (OLD TTA: source_only/tent/sar — superseded by the disc_reweight rewrite).
  scripts/generate_latex_tables.py turns (b) into LaTeX. It was NOT regenerated for the new disc_reweight Table 3.
- Run dirs follow: results/{ucf,xd}_{variant}_{backbone?}_{s42,s123,s2024}/  e.g. ucf_gated_fusion_giant_s42, xd_gated_fusion_so400m_s2024. CLIP backbone has no backbone token (ucf_gated_fusion_s42).
- Backbone -> visual feat dim -> mean+max concat clip_dim: CLIP 512->1024, SigLIP2 Base 768->1536, SO400M 1152->2304, Giant 1536->3072.
- Use Read/Grep/Glob/Bash freely. Quote file:line and exact values. Convert fractions to % (0.8249 -> 82.5).
- Severity: critical = headline number wrong / unsupported claim / fabrication; high = material method/number mismatch; medium = imprecise or undisclosed but defensible; low = wording/rounding; info = confirmed match worth recording.
`

const FINDINGS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    dimension: { type: 'string' },
    overall_match: { type: 'string', enum: ['match', 'minor_mismatch', 'major_mismatch'] },
    summary: { type: 'string', description: '2-4 sentence verdict for this dimension' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          id: { type: 'string', description: 'short slug, e.g. tta-source-mismatch' },
          title: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low', 'info'] },
          paper_location: { type: 'string', description: 'main.tex section + line/eq, quote the claim' },
          paper_says: { type: 'string' },
          code_location: { type: 'string', description: 'file:line or results path' },
          code_says: { type: 'string' },
          discrepancy: { type: 'string', description: 'why they do/do not match; for info findings state the confirmed match' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
        required: ['id', 'title', 'severity', 'paper_location', 'paper_says', 'code_location', 'code_says', 'discrepancy', 'confidence'],
      },
    },
  },
  required: ['dimension', 'overall_match', 'summary', 'findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    id: { type: 'string' },
    verdict: { type: 'string', enum: ['CONFIRMED_REAL', 'FALSE_POSITIVE', 'NEEDS_CONTEXT'] },
    corrected_severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low', 'info'] },
    evidence: { type: 'string', description: 'what YOU saw in the real files (quote file:line + values), not what the reviewer said' },
    reasoning: { type: 'string' },
  },
  required: ['id', 'verdict', 'corrected_severity', 'evidence', 'reasoning'],
}

// ---------------------------------------------------------------------------
// 12 review dimensions
// ---------------------------------------------------------------------------
const DIMENSIONS = [
  {
    key: 'arch-equations',
    prompt: `${SHARED}
DIMENSION: Fusion architecture & equations (paper Methodology 3.4, lines ~149-171).
Verify the CODE implements the paper's equations exactly.
Paper claims:
- Late Fusion Eq(1): a_late = 1/2 h_s(s) + 1/2 h_v(v)  (independent per-modality heads, fixed equal weight).
- Gated Fusion Eq(2): proj+LN per modality: ŝ=LN_s(W_s s+b_s), v̂=LN_v(W_v v+b_v).
- Eq(3): g = σ(W_g[ŝ||v̂]+b_g), g in [0,1]^256.
- Eq(4): f_gated = LN_f(g⊙ŝ + (1-g)⊙v̂ + ŝ + v̂), dropout AFTER LN_f. Residual gives effective weighting (1+g)⊙ŝ+(2-g)⊙v̂. Three LN layers (LN_s,LN_v,LN_f).
- Shared dim 256; skeleton 256-d; gate Xavier-init small for ~0.5 init gate.
CHECK FILES: src/models/gated_fusion.py, src/models/late_fusion.py, src/models/skeleton_only.py, src/models/clip_only.py, src/models/mil_head.py.
Confirm: order of ⊙ (does g multiply skeleton or visual?), LN count & placement, dropout placement, residual term, dims. Note gate init. Report matches as info findings and any mismatch.`,
  },
  {
    key: 'loss',
    prompt: `${SHARED}
DIMENSION: MIL ranking loss & regularizers (paper 3.5, Eq(6)-(7), lines ~173-186; impl 4.2 line ~215).
Paper claims:
- Eq(6) rank loss: max(0, 1 - mean_top-k(anom) + mean_top-k(normal)), margin 1.0, top-k k=3.
- Eq(7) total: L = L_rank + (λ1/T) Σ_t ||a_t||_2 + λ2 Σ_i (a_i - a_{i+1})^2.
- Sparsity term = mean over snippet POSITIONS of per-position ℓ2 norm over the ABNORMAL bag (RTFM feature-magnitude style). λ1 = 8e-3.
- Smoothness λ2 dataset-dependent: 8e-4 on UCF, 0 on XD. Penalizes ADJACENT-snippet (temporal axis) differences.
- Footnote (line ~215): reported UCF numbers used an EARLIER smoothness impl; released code applies penalty strictly along temporal/adjacent-snippet axis; claims shift ≤0.13pp.
CHECK FILES: src/losses/mil_loss.py, src/train.py (loss assembly + lam_sparse/lam_smooth/k_topk/margin usage). Verify the sparsity term is computed over the abnormal bag and is the mean-of-per-position-ℓ2 (matches Eq form), and the smoothness term is along the temporal axis. Flag any axis/normalization mismatch vs Eq(7), and whether the footnote's "≤0.13pp" claim is supported anywhere (results/h1_recompute or _giant_smoothmeasure config).`,
  },
  {
    key: 'skeleton-pipeline',
    prompt: `${SHARED}
DIMENSION: Skeleton extraction + CTR-GCN (paper 3.1-3.2, lines ~120-134).
Paper claims:
- RTMPose-m + YOLOX-m, top-2 persons by confidence, zero-pad missing, PreNormalize2D to [-1,1] centered at bbox midpoint.
- Tensor (T,M,V,C), M=2, V=17, C=3 (x,y,conf). ~21.6 FPS on RTX4090.
- CTR-GCN pretrained NTU RGB+D 120, frozen. FOUR streams joint(j)/bone(b)/joint-motion(jm)/bone-motion(bm), each 256-d.
- 64-frame NON-overlapping snippets; global average pool over person(M), temporal(T), spatial(V) -> 256-d.
- 4 streams combined by WEIGHTED AVERAGE: joint & bone weight 1.0, motion streams 0.5.
- Videos <64 frames excluded: 172 in UCF-Crime, 0 in XD.
CHECK FILES: scripts/extract_skeletons.py, scripts/extract_ctrgcn.py, src/data/dataset.py, src/data/loaders.py, any skel aggregation (tests/test_skel_agg.py). Verify the 1.0/1.0/0.5/0.5 stream weights, the 64-frame snippet & pooling dims, top-2 persons, and the <64 exclusion count (172 UCF). Flag the GF 2-Person variant relationship (top-2 vs top-1?).`,
  },
  {
    key: 'visual-pipeline',
    prompt: `${SHARED}
DIMENSION: Visual-language feature extraction (paper 3.3, lines ~136-147).
Paper claims:
- 4 frozen backbones: CLIP ViT-B/16 (512-d), SigLIP2 ViT-B/16 (768-d), SigLIP2 SO400M (1152-d), SigLIP2 Giant (1536-d).
- Frame features at 1 FPS sampling (~2-4 frames/snippet).
- Aggregation = CONCATENATED mean & max pooling -> 2d (e.g. 1024-d CLIP, 3072-d Giant). GF Mean-Only variant uses mean only.
CHECK FILES: scripts/extract_clip.py, scripts/extract_siglip2* (tests/test_extract_siglip2.py), src/data/dataset.py, configs (clip_dim values). Verify the per-backbone dims, the mean+max concat giving clip_dim = 2*d (cross-check config_snapshot clip_dim: CLIP 1024, Base 1536, SO400M 2304, Giant 3072), the 1 FPS sampling, and what GF Mean-Only changes (clip_dim halves to d?). Flag any dim mismatch.`,
  },
  {
    key: 'training-hparams',
    prompt: `${SHARED}
DIMENSION: Training hyperparameters (paper 4.2, lines ~210-217).
Paper claims:
- AdamW, weight_decay 1e-2, lr 1e-4 (BOTH datasets).
- batch 16 normal/anom pairs (32 videos/batch). max 50 epochs, early stopping patience 10 on val loss.
- top-k k=3 both datasets. fixed config across datasets (lr 1e-4, k=3, margin 1.0).
- λ2 (smoothness) is the ONLY dataset-dependent setting: 8e-4 UCF, 0 XD. λ1=8e-3.
- Gated Fusion reported mean±std over 3 seeds {42,123,2024}; all OTHER variants single-seed (42).
- snippet->frame: each frame gets its enclosing 64-frame snippet score; final snippet repeated for trailing frames.
CHECK: read EVERY configs/*.yaml (and src/train.py + src/utils/config.py defaults). Build a table of lr / weight_decay / batch_size / epochs / patience / k_topk / margin / lam_sparse / lam_smooth across configs. Verify: lam_smooth=8e-4 in ALL ucf configs and =0 in ALL xd configs; lr/wd/k/margin uniform; lam_sparse=8e-3 everywhere. Flag ANY config whose value contradicts the paper (e.g. an xd config with nonzero lam_smooth, or a stray lr). Also note any param present in code but undisclosed in paper (warmup_epochs, data.T).`,
  },
  {
    key: 'datasets-splits',
    prompt: `${SHARED}
DIMENSION: Datasets & splits (paper 4.1, lines ~202-208).
Paper claims:
- UCF-Crime: 1900 videos, 13 anomaly cats; train 800 normal + 810 anomalous (video-level labels); test 150 normal + 140 anomalous (frame-level). AUC metric.
- XD-Violence: 4754 videos, 6 cats (B1 Fighting,B2 Shooting,B3 Riot,B4 Abuse,B5 Car Accident,B6 Explosion); train 3954, test 800. AP metric.
- 15% stratified val split (preserves normal/anom ratio), used for early stopping only (no frame labels on train).
CHECK FILES: scripts/create_splits.py, data/splits/* (count lines), src/eval/ucf_annotations.py, src/eval/xd_annotations.py, tests/test_splits.py, tests/test_ucf_annotations.py, tests/test_xd_annotations.py. Verify the 15% stratified holdout, the train/test counts, the 13 UCF / 6 XD categories. NOTE: paper test=290 UCF but eval_metrics.json shows n_videos=254 (and XD n_videos=800). Determine whether the 254 vs 290 gap is the documented <64-frame exclusion and whether the paper discloses the actual evaluated n. Flag the n=254 disclosure gap if undisclosed.`,
  },
  {
    key: 'table1-ucf',
    prompt: `${SHARED}
DIMENSION: Table 1 — UCF-Crime AUC (paper lines ~224-240). Verify EVERY cell.
Paper Table 1 (AUC %):
 Skeleton Only: CLIP 71.8.
 Visual Only: 81.1 / 78.3 / 80.9 / 82.4.
 Late Fusion: 78.6 / 79.5 / 80.0 / 80.8.
 Gated Fusion (mean±std 3 seeds): 81.4±0.3 / 79.0±0.1 / 81.3±0.3 / 82.5±0.4.
 GF 2-Person: 81.1 / 78.7 / 81.3 / 82.7.
 GF Mean-Only: 81.1 / 79.4 / 81.8 / 83.0.
Columns = CLIP / SigLIP2 Base / SO400M / Giant.
CHECK: results/phase10_charts/backbone_comparison_4way.csv (*_AUC) for single-seed rows; seed_stability_4way.csv for the Gated mean±std (compute mean & sample stdev of the 3 seeds yourself). THEN trace at least the headline/bold cells back to results/<run>/eval_metrics.json 'auc' (e.g. ucf_gated_fusion_giant_s42 -> 0.8249). Flag any cell that rounds differently, any bold marking that is not actually the row max, and confirm 82.5 (Giant gated) & 83.0 (Giant mean-only) headlines.`,
  },
  {
    key: 'table2-xd',
    prompt: `${SHARED}
DIMENSION: Table 2 — XD-Violence AP (paper lines ~243-259). Verify EVERY cell.
Paper Table 2 (AP %):
 Skeleton Only: CLIP 40.9.
 Visual Only: 74.9 / 76.9 / 77.2 / 75.7.
 Late Fusion: 64.4 / 62.8 / 65.9 / 66.0.
 Gated Fusion (mean±std 3 seeds): 76.5±0.9 / 74.5±0.9 / 78.7±0.9 / 76.8±2.8.
 GF 2-Person: 74.8 / 71.9 / 79.1 / 75.9.
 GF Mean-Only: 76.8 / 74.7 / 79.9 / 76.2.
CHECK: backbone_comparison_4way.csv (*_AP) + seed_stability_4way.csv (compute Gated mean±std). Trace bold/headline cells to results/xd_*/eval_metrics.json 'ap' (e.g. xd_gated_fusion_so400m_s42 -> 0.7974; 3-seed mean -> 78.7). Verify 78.7 (SO400M gated) headline and that SO400M (not Giant) is bold on the fusion rows. Flag mismatches, wrong-bold, rounding issues. Note Giant gated std 2.8 — verify from the 3 seeds (0.736/0.782/0.787).`,
  },
  {
    key: 'table3-tta-provenance',
    prompt: `${SHARED}
DIMENSION: Table 3 — TTA on UCF-Crime-C (paper lines ~298-333) — THE HIGH-RISK DIMENSION.
Paper main.tex Table 3 (the NEW disc_reweight version) claims, mean AUC % over 20 corruptions, 3 seeds:
 Source-Only: CLIP 63.7 / Base 57.0 / SO400M 58.9 / Giant 62.8 ; Mean 60.6.
 TENT = SAR = Source-Only to displayed precision (claim: |Δ| ≤ 0.004pp).
 Ours (disc-reweight): CLIP 64.4 / Base 58.5 / SO400M 61.1 / Giant 63.3 ; Mean 61.8.
 Δ_Ours (paired per-seed): +0.67±0.23 / +1.50±1.14 / +2.24±0.24 / +0.42±0.12 ; overall +1.21.
 Text claims: Gaussian-noise gain +4.8 avg, up to +13.9 on SO400M; one seed SigLIP2-Base loses up to 3.2 at high-severity Gaussian; TENT lr=1e-3, SAR lr=1e-3 rho=0.05; continual-online deterministic protocol; LN affine only, <4000 params across 3 LN.
CRITICAL: results/tta_backbone/summary.csv has DIFFERENT (older) source_only numbers (clip 0.6145, base 0.5680, so400m 0.5873, giant 0.6034) and the OLD tent/sar lrs (tent clip lr 0.005). The paper's NEW numbers must come from elsewhere.
TASK:
1. Find the provenance of EVERY number in main.tex Table 3. Search: src/tta/disc_reweight.py, src/tta/evaluate_tta.py, scripts/_tmp_*.py (esp _tmp_disc_signal, _tmp_r1_full, _tmp_validate_production, _run_tta_backbone_batch), .planning/PAPER-TTA-REVISION-DRAFT.md, .planning/HANDOVER-tta-investigation-2026-06-06.md, .planning/quick/260607-42h-tta-disc-reweight/*, results/tta*.
2. Determine: are the Source-Only / Ours / Δ numbers reproducible from a committed artifact, or do they only exist in a draft .md / uncommitted _tmp script output? Is there a 3-seed CSV/JSON backing them?
3. Verify the +1.21 mean and per-backbone Δ arithmetic. Verify the +13.9 SO400M-Gaussian and +4.8 avg claims if a per-condition breakdown exists.
4. Flag the stale tta_backbone/summary.csv + tables_generated.tex (old Table 3) and whether generate_latex_tables.py can even produce the new table.
5. Verify the TENT/SAR lr=1e-3 & rho=0.05 protocol claim against the actual run configs used for the paper's "≤0.004pp" statement (NOT the old sweep in summary.csv).
Report provenance gaps as high/critical.`,
  },
  {
    key: 'disc-reweight-method',
    prompt: `${SHARED}
DIMENSION: Discriminative-reliability reweighting method (paper 3.6, lines ~188-195; 4.5 lines ~331-333).
Paper claims the method is:
- w_vl = min(1, σ(s_clip^test) / σ(s_clip^clean)), where s_clip = snippet scores from the fusion head with the SKELETON stream ZEROED, σ = std pooled over a corruption condition.
- A skeleton-reliability gate s in [0,1] from skeleton feature distribution shift vs clean stats.
- Final scale w = 1 - (1 - w_vl)·s, applied to p_clip AFTER its LayerNorm, in BOTH the gated and residual terms.
- Label-free, NO tuned hyperparameter, transductive (whole-condition pooling). Clean reference from train OR clean-test (claim: equivalent).
CHECK FILES: src/tta/disc_reweight.py (read fully), src/tta/evaluate_tta.py. Verify: (a) s_clip really zeroes the skeleton stream; (b) w_vl = min(1, std ratio); (c) skeleton gate computed from skel distribution shift; (d) w = 1-(1-w_vl)*s applied to p_clip after LN in both gated AND residual terms (matches code path g*p_skel+(1-g)*(w*p_clip) ... + p_skel + w*p_clip?); (e) genuinely no tuned hyperparameter (any magic threshold/constant = contradicts "tuning-free" — flag it). Report exact code vs Eq match.`,
  },
  {
    key: 'tent-sar-method',
    prompt: `${SHARED}
DIMENSION: TENT/SAR implementation & the "entropy gives no benefit" claim (paper 2.3 line ~104, 4.5 lines ~325-329, 354-355).
Paper claims:
- TENT & SAR adapt ONLY the LayerNorm affine params (γ,β) of the 3 LN layers in the gated fusion head — "fewer than 4,000 parameters".
- Deterministic continual-online protocol across the whole corruption stream. TENT lr=1e-3; SAR lr=1e-3, rho=0.05. SAR = TENT + SAM + reliability filtering.
- Entropy objective: minimize prediction entropy. Claim: changes AUC ≤0.004pp because gate+MIL head frozen, LN affine updates too small to reorder rank-based AUC.
CHECK FILES: src/tta/tent.py, src/tta/sar.py, src/tta/sam.py, src/tta/evaluate_tta.py. Verify: (a) only LN γ,β collected & updated, everything else frozen; (b) param count: 3 LN × 256 dims × 2 (γ,β) = 1536 — is "<4000" right? compute it; (c) SAR uses SAM (sam.py) + entropy reliability filter; (d) the entropy is computed how (binary sigmoid score -> entropy)? For a 1-logit anomaly score, is entropy well-defined / does the objective make sense? Flag if the entropy formulation is degenerate. (e) continual vs episodic reset. Report method-vs-paper match and any overstatement.`,
  },
  {
    key: 'discussion-claims',
    prompt: `${SHARED}
DIMENSION: Discussion / Limitations / Abstract quantitative claims (paper Abstract line ~50, 5 lines ~338-357, 6 lines ~362-372, Conclusion ~387-395).
Verify each QUANTITATIVE or FALSIFIABLE claim:
- "0.50M (CLIP) to 1.02M (SigLIP2 Giant) trainable parameters" (line ~357). Compute actual GatedFusion trainable params for clip_dim=1024 and 3072 (skel_proj 256x256, clip_proj clip_dim->256, gate 512->256, ln's, MILHead 256->128->32->1). Check results/benchmark_models.csv / backbone_bench_*.json.
- "Training completes in under 5 minutes per configuration" (line ~357) — any timing evidence?
- Gating distribution by category (Fig 7, line ~340-349): higher skeleton weight for Fighting/Assault vs Explosion/Arson. Is there code/data (results/phase6_charts/D_gating) backing this? gate>0.5 => skeleton-weighted claim — but in code g multiplies p_skel, so g>0.5 = MORE skeleton: confirm direction.
- Complementarity: "Gated Fusion CLIP 81.4 exceeds CLIP visual-only 81.1" and "Giant 82.5 vs 82.4 visual-only" (line ~261). Check the margin is real (CSV) and not within seed noise.
- Late fusion degrades: "CLIP late 78.6 < CLIP visual-only 81.1" (line ~272); "XD late 64.4 vs gated 76.5 = 12.1pp" (line ~263). Verify arithmetic.
- "82.4% visual-only, 82.5% gated, 83.0% mean-only" Giant ranking (line ~287); "SO400M 77.2 > Giant 75.7 visual-only XD" (line ~289).
- Abstract: "82.5% AUC UCF (Giant)", "78.7% AP XD (SO400M)", "entropy TTA changes AUC by at most 0.004%", "mean +1.2%, up to +13.9%". Cross-check against the table dimensions' findings.
CHECK: results/benchmark_models.csv, results/backbone_bench_*.json, results/phase6_charts/, backbone_comparison_4way.csv. Flag unsupported claims (esp. param counts, <5min, gating-by-category if no backing data) and any claim within seed-noise being stated as a real effect.`,
  },
]

// ---------------------------------------------------------------------------
// Pipeline: review each dimension, then adversarially verify each finding.
// ---------------------------------------------------------------------------
phase('Review')
const results = await pipeline(
  DIMENSIONS,
  (d) => agent(d.prompt, { label: `review:${d.key}`, phase: 'Review', schema: FINDINGS_SCHEMA }),
  async (review, d) => {
    if (!review || !review.findings || review.findings.length === 0) {
      return { dimension: d.key, review, verified: [] }
    }
    // Verify EVERY finding independently with a skeptic that re-reads the real files.
    const verified = await parallel(
      review.findings.map((f) => () =>
        agent(
          `${SHARED}
ADVERSARIAL VERIFICATION. A reviewer claims a code/paper discrepancy. Do NOT trust them — independently open the real files (paper/main.tex AND the cited code/results) and decide.
Default to FALSE_POSITIVE unless you can reproduce the discrepancy yourself with quoted evidence. If it's real but the reviewer mis-stated severity or it needs nuance, use NEEDS_CONTEXT and correct it.

FINDING id=${f.id} [${f.severity}] ${f.title}
paper_location: ${f.paper_location}
paper_says: ${f.paper_says}
code_location: ${f.code_location}
code_says: ${f.code_says}
claimed discrepancy: ${f.discrepancy}

Re-read both sides. Return your verdict with YOUR OWN quoted evidence (file:line + values).`,
          { label: `verify:${d.key}:${f.id}`, phase: 'Verify', schema: VERDICT_SCHEMA }
        ).then((v) => ({ ...f, dimension: d.key, verification: v }))
      )
    )
    return { dimension: d.key, review, verified }
  }
)

// Assemble compact return for synthesis in the main context.
const reviews = results.filter(Boolean).map((r) => ({
  dimension: r.dimension,
  overall_match: r.review ? r.review.overall_match : 'ERROR',
  summary: r.review ? r.review.summary : 'reviewer died',
  n_findings: r.review && r.review.findings ? r.review.findings.length : 0,
}))

const allFindings = results
  .filter(Boolean)
  .flatMap((r) => (r.verified || []).filter(Boolean))

const confirmed = allFindings.filter(
  (f) => f.verification && (f.verification.verdict === 'CONFIRMED_REAL' || f.verification.verdict === 'NEEDS_CONTEXT')
)
const falsePositives = allFindings.filter(
  (f) => f.verification && f.verification.verdict === 'FALSE_POSITIVE'
)

log(`Reviews: ${reviews.length} dimensions. Findings: ${allFindings.length} total -> ${confirmed.length} confirmed/context, ${falsePositives.length} false-positive.`)

return {
  reviews,
  confirmed: confirmed.map((f) => ({
    dimension: f.dimension,
    id: f.id,
    title: f.title,
    severity: f.verification.corrected_severity,
    verdict: f.verification.verdict,
    paper_location: f.paper_location,
    paper_says: f.paper_says,
    code_location: f.code_location,
    code_says: f.code_says,
    discrepancy: f.discrepancy,
    verifier_evidence: f.verification.evidence,
    verifier_reasoning: f.verification.reasoning,
  })),
  falsePositives: falsePositives.map((f) => ({
    dimension: f.dimension,
    id: f.id,
    title: f.title,
    why_rejected: f.verification.reasoning,
    verifier_evidence: f.verification.evidence,
  })),
}
