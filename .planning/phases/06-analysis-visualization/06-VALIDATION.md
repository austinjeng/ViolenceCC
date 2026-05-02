---
phase: 6
slug: analysis-visualization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-02
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python scripts + file existence checks |
| **Config file** | none — standalone chart generation scripts |
| **Quick run command** | `python scripts/generate_phase6_charts.py --dry-run` |
| **Full suite command** | `python scripts/generate_phase6_charts.py && ls results/phase6_charts/*.png` |
| **Estimated runtime** | ~60-120 seconds (includes model forward passes for gate/feature collection) |

---

## Sampling Rate

- **After every task commit:** Verify output PNG files exist and are non-zero size
- **After every plan wave:** Run full chart generation and verify all expected outputs
- **Before `/gsd-verify-work`:** Full suite must produce all required PNGs
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | VIS-01 | — | N/A | file check | `ls results/phase6_charts/*temporal*.png` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | VIS-02 | — | N/A | file check | `ls results/phase6_charts/*skeleton*.png` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `results/phase6_charts/` — output directory created
- [ ] Verify all 8 eval_scores.npz files accessible
- [ ] Verify skeleton .pkl files accessible at E:/skeletons/
- [ ] Verify XD-Violence test videos accessible at E:/XD_Violence/test/videos/

*Existing chart infrastructure (phase4/phase7 scripts) covers matplotlib/seaborn setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Temporal curves are thesis-quality | VIS-01 | Visual quality is subjective | Open PNGs, verify legibility, color scheme, GT shading alignment |
| Skeleton overlays show correct keypoints | VIS-02 | Visual correctness check | Verify COCO-17 joints match human body in overlay PNGs |
| t-SNE clusters are meaningful | OPT-09 | Semantic interpretation | Verify anomaly/normal clusters show separation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
