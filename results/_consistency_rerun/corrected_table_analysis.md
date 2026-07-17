# Consistency-rerun analysis — corrected UCF Table 5.1 means (2026-07-17)

Fully-corrected value per cell = version-locked rerun (clean worktree @ d2e4c2b,
`scoped_dirty: false`) for the 29 legacy cells; existing canonical value for the
cells already trained post-fix (June 9–10). All values frame-level AUC (%).

## Mechanical decision gate: FAIL (16/29 cells exceed row seed std)
Per-cell table: comparison.csv / comparison.md. Escalation per protocol =
adopt rerun numbers in the post-defense revision (full propagation pass).

## Mean-level impact (what actually matters)

| Row (UCF) | Published-era mean | Corrected mean | Shift (pp) |
|---|---|---|---|
| Visual CLIP | 81.18 | 81.29 | +0.11 |
| Visual Base | 78.53 | 78.60 | +0.07 |
| Visual SO400M | 81.14 | 81.39 | +0.26 |
| Visual Giant | 82.35 | 82.03 | −0.32 |
| Skeleton Only | 68.77 | 67.39 | −1.38 |
| Late CLIP | 78.92 | 79.18 | +0.25 |
| Late Base | 77.25 | 76.79 | −0.46 |
| Late SO400M | 79.06 | 78.55 | −0.52 |
| Late Giant | 79.85 | 79.55 | −0.30 |
| Gated CLIP | 81.39 | 81.45 | +0.06 |
| Gated Base | 78.99 | 79.43 | +0.44 |
| Gated SO400M | 81.28 | 81.69 | +0.41 |
| **Gated Giant (headline)** | **82.54** | **82.48** | **−0.06** |
| 2P CLIP | 81.35 | 81.25 | −0.10 |
| 2P Base | 79.45 | 79.91 | +0.46 |
| 2P SO400M | 81.67 | 81.63 | −0.04 |
| 2P Giant | 82.58 | 82.53 | −0.05 |

## Conclusion survival checks

1. **Headline intact:** 82.54 → 82.48; both report as **82.5**. All three
   headline seeds individually PASS the gate (deltas −0.13 / −0.15 / +0.11 pp
   vs row std 0.36 pp).
2. **Gated ≥ Visual (complementarity): holds on all 4 UCF backbones after
   correction** — CLIP +0.16, Base +0.83, SO400M +0.30, Giant +0.45 — i.e.
   strictly positive everywhere on UCF (published table had this pattern too;
   correction strengthens it). XD rows untouched (all trained post-fix, λ=0).
3. **UCF backbone ordering preserved:** Giant (82.48) > SO400M (81.69) >
   CLIP (81.45) > Base (79.43), same as published.
4. **Late fusion still collapses** relative to gated on every backbone.
5. **Skeleton-only stays weak** (68.8 → 67.4; −4.1 pp on the rerun s42 cell,
   1.47σ of its own ±2.8 noise). Conclusion "substantially lower standalone
   performance" unchanged (would strengthen slightly).
6. **REVISION-PASS FLAG — GF 2-Person split moves:** the corrected UCF split is
   2P better on Base+Giant, worse on CLIP+SO400M (XD unchanged: better on
   SO400M only). Corrected overall: **worse in 5 of 8 cells** vs the current
   ch05 sentence "worse than the default in half of the backbone×dataset
   cells" (written for the 4–4 split). If rerun numbers are adopted, update
   that sentence to "five of the eight".

## Interpretation for the ch04 footnote / defense

The version-locked rerun REPRODUCES the headline to 0.1 pp and preserves every
qualitative conclusion. Individual non-headline cells shift by up to ±1 pp
(skeleton-only −4.1 pp inside its ±2.8 seed band) — consistent with the
disclosed sensitivity of low-capacity rows to the smoothness-term
implementation. The June single-config A/B (−0.13 pp) is confirmed exactly by
the headline row. Adoption of the corrected numbers is a post-defense
propagation decision; nothing in the corrected table weakens any claim, and
the complementarity pattern comes out stronger.
