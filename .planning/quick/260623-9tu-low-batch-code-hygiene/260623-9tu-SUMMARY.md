---
quick_id: 260623-9tu
slug: low-batch-code-hygiene
date: 2026-06-23
status: complete
commit: 99078d7
---

# Summary — Quick Task 260623-9tu (low-severity batch #2, code-hygiene group)

Fixed 7 low-severity code-hygiene findings. Each was gated behind BOTH (a) a full green pytest
run and (b) an independent adversarial check (skeptic re-derived from live source, default
not-resolved). All 7 passed on the first adversarial pass.

## Findings resolved (commit 99078d7)
- **C1-1** `src/losses/mil_loss.py`: fail-loud `ValueError` guard before top-k — raises if any bag has
  fewer than k real (unmasked) snippets, preventing the latent {finite,-inf}→NaN loss. Never fires in
  production (callers pad to all-ones T=32). Verified empirically (2-real bag raises; full mask finite).
- **C1-2** `tests/test_mil_loss.py`: regression test `test_mil_ranking_loss_raises_when_bag_has_fewer_than_k_real` pinning the contract.
- **C1-3** `src/models/registry.py` + `gated_fusion.py`: `build_model()` and `GatedFusion` now RAISE on
  truly-unexpected kwargs (not declared AND not in the `_KNOWN_EXTRA_KWARGS` replay allow-list),
  superseding the D-15 warn-only policy. Verified SAFE: every tracked config's model-block keys are
  declared args (incl. `proj_dim`/`alpha`) or allow-listed, so the raise never fires today; a typo
  (e.g. `droput`) now fails loud. Corroborated by green registry/config/ablation/e2e tests.
- **C2-1** `src/data/dataset.py`: `warnings.warn` with loadable/total + dropped count + sample ids when
  MILFeatureDataset filters unloadable/<64-frame videos (CLAUDE.md convention). Fires only on drops;
  filtering logic unchanged.
- **C3-2** `scripts/pri5_tta_breakdown.py`: renamed the mislabeled "CORAL-TTA"/"CORAL R1" method
  references to disc-reweight (discriminative-reliability reweighting); kept the real `_coral_derisk`
  directory path (var `CORAL`→`DERISK_DIR`). Script reruns; reproduction checks PASS (+4.826/+13.2/-3.2).
- **C4-1** `src/evaluate.py`: `--split val` mil_loss=0.0 stub now emits `warnings.warn` (RuntimeWarning), not `print()`.
- **C4-3** `src/train.py`: `validate()` and `validate_i3d()` now `warnings.warn` before returning inf on a
  degenerate all-single-class val split; added `import warnings`.

## Verification
- pytest (vcc-main): **322 passed, 0 failed** — 319 non-e2e (136s) + 3 e2e (39s). (Suite was 321; +1 = the new C1-2 test.)
- Adversarial check (workflow w6fhzmlch): PASS for all 7 (C1-1, C1-2, C1-3, C2-1, C3-2, C4-1, C4-3); 0 failed.
- `pri5_tta_breakdown.py` re-run: all reproduction checks PASS post-rename.
- review-2026-06-22.html updated: 19 of the review's findings now marked ✓ resolved.

## Remaining low batch
- Reproducibility/tests group: C7-1 (tracked TTA driver), C7-3 (gitignore un-ignore rules), T6-2 (README), C6-4 (integration test).
- Remaining paper: T5-2 (abstract density trim), T5-6 (remaining RE-VERIFY comments + author lists).
