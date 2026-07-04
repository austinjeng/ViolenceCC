# Pri 5 - Per-corruption-type disc-reweight breakdown

Substantiates the paper prose numbers (+4.8 / +13.2 / -3.2) that currently live nowhere checkable. CPU-only recompute from on-disk disc-reweight (R1) per-condition data.

## Data provenance

- **Seed-42 canonical**: `results/_coral_derisk/r1full_{clip,base,so400m,giant}.json` (`per_condition[<fam>_<sev>].d = r1 - src`, AUC points 0-100).
- **3-seed means**: s42 component = the r1full file above (canonical); s123 / s2024 = `results/_coral_derisk/variants/v_<bb>_s{123,2024}_test.json`. Per-family mean = mean over the 5 severities; 3-seed = mean of the three per-seed per-family means.
- **TENT/SAR overall (context only)**: `results/_tta_rerun_continual/summary_3seed.json` holds 3-seed OVERALL-AUC entropy-min deltas (NOT disc-reweight, NOT per-family). It does NOT contain the +13.2 gaussian value -- that comes from the disc-reweight variants.

## Table 1 - Per-backbone x per-family mean delta AUC (SEED-42, canonical r1full)

| Backbone | Gaussian noise | Motion blur | JPEG comp. | Brightness |
|---|---:|---:|---:|---:|
| CLIP ViT-B/16 | +2.89 | +0.00 | +0.00 | +0.02 |
| SigLIP2-base | +1.08 | +0.00 | +0.00 | +0.00 |
| SigLIP2-SO400M | +7.86 | +0.00 | +0.00 | +0.00 |
| SigLIP2-giant | +1.40 | +0.00 | +0.00 | +0.00 |
| **Average** | **+3.31** | +0.00 | +0.00 | +0.01 |

## Table 2 - Per-backbone x per-family mean delta AUC (3-SEED mean)

| Backbone | Gaussian noise | Motion blur | JPEG comp. | Brightness |
|---|---:|---:|---:|---:|
| CLIP ViT-B/16 | +2.67 | +0.00 | +0.00 | +0.01 |
| SigLIP2-base | +5.99 | +0.00 | +0.00 | -0.00 |
| SigLIP2-SO400M | +8.95 | +0.00 | +0.00 | -0.00 |
| SigLIP2-giant | +1.69 | +0.00 | +0.00 | +0.00 |
| **Average** | **+4.83** | +0.00 | +0.00 | +0.00 |

> Non-Gaussian families are ~0.00 because the R1 reliability route gates blur / JPEG / brightness back to the source model (`d=0`), so the gain is essentially Gaussian-only.

## Gaussian severity sweep (the family that carries the gain)

Per-condition seed-42 delta AUC (canonical r1full):

| Backbone | gn_1 | gn_2 | gn_3 | gn_4 | gn_5 |
|---|---:|---:|---:|---:|---:|
| CLIP ViT-B/16 | +0.92 | +2.66 | +2.56 | +3.49 | +4.83 |
| SigLIP2-base | +5.67 | +3.68 | +1.00 | -1.77 | -3.20 |
| SigLIP2-SO400M | -0.66 | +3.73 | +10.33 | +11.98 | +13.92 |
| SigLIP2-giant | +0.29 | +0.40 | +0.24 | +1.44 | +4.64 |

## SO400M gaussian PEAK (two distinct numbers -- label carefully)

- **Seed-42 per-condition max** (canonical r1full): `gaussian_noise_5` = **+13.92** AUC pts. This is the seed-42-only peak.
- **3-seed gaussian_5 mean** (REVIEW's +13.2): per-seed = [+13.92 (s42), +12.34 (s123), +13.31 (s2024)] -> mean = **+13.19** AUC pts.
- Note: the paper's stale **+13.9** is the seed-42-only value (r1full gaussian_5 = +13.92); the honest 3-seed figure is +13.19 (~+13.2).

## Base single-seed over-route (the -3.2 disclosure)

- **Base seed-42 gaussian_5** = **-3.20** AUC pts (canonical r1full). This is the single-seed disc-reweight over-route the paper discloses; base 3-seed gaussian_5 = +0.35 (the s42 value is an outlier).

## TENT/SAR 3-seed overall context (entropy-min, summary_3seed.json)

| Backbone | dTENT (3-seed) | dSAR (3-seed) |
|---|---:|---:|
| clip-vit-b-16 | +0.02 | +0.02 |
| siglip2-base | -0.08 | -0.08 |
| siglip2-so400m | -0.05 | -0.05 |
| siglip2-giant | +0.01 | +0.01 |

> These are OVERALL-AUC entropy-min deltas (different mechanism from disc-reweight (R1)); near-zero, consistent with the paper's 'LN-barrier' finding. Not the source of +13.2.

## Reproduction checks

| Claim | Target | Recomputed | Verdict |
|---|---:|---:|---|
| Gaussian cross-backbone 3-seed avg = +4.826 | +4.826 | +4.8258 | PASS |
| SO400M gaussian_5 3-seed mean = +13.2 | +13.200 | +13.1917 | PASS |
| Base s42 gaussian_5 = -3.2 | -3.200 | -3.2015 | PASS |

(Transparency) Gaussian cross-backbone **seed-42-only** avg = +3.31 (the 3-seed +4.826 is higher because base/so400m gaussian gains are larger on s123/s2024).
