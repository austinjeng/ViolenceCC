---
quick_id: 260606-3hc
slug: add-continual-online-tta-protocol-flag-t
date: 2026-06-06
type: quick
status: complete
commit: 1ed2d16
---

# Quick Task 260606-3hc: Add continual-online TTA protocol to evaluate_tta.py — Summary

Added an opt-in `--protocol {episodic,continual}` flag to the TTA eval. Default
stays `episodic` (current per-video-reset behavior, non-breaking). `continual`
performs one stream-level reset then adapts continuously across all test videos
with no per-video reset (TENT/SAR native -C setup). Code-only; no grid re-run,
no canonical-artifact change, no paper edit.

## Changes

### src/tta/evaluate_tta.py
- **Task 1 — `_adapt_one_video`:** added `reset: bool = True` parameter (after
  `T: int = 32,`); the unconditional `adaptor.reset()` at the top of the loop
  body became `if reset: adaptor.reset()`. Episodic callers (default) behave
  exactly as before.
- **Task 2 — `run_tta_evaluation`:**
  - added `protocol: str = "episodic"` parameter (+ docstring entry).
  - after adaptor creation and before the test-video list load, inserted the
    continual-online guard block: `per_video_reset = protocol != "continual"`
    and `if not per_video_reset: adaptor.reset()` (one-time stream-level reset).
  - per-video scoring call now passes `reset=per_video_reset` to
    `_adapt_one_video`.
  - added `"protocol": protocol,` to the `eval_metrics.json` payload (next to
    `backbone`) for provenance.
- **Task 3 — CLI:** added `--protocol` arg in `parse_args`
  (`default="episodic"`, `choices=["episodic", "continual"]`) and passed
  `protocol=args.protocol` into the `run_tta_evaluation(...)` call in `main()`.

### tests/test_evaluate_tta.py
- **Task 4:** imported `_adapt_one_video`; added `_ResetCountingAdaptor` (fake
  adaptor with a `reset()` call-counter and fixed `torch.zeros(1, n)` scoring),
  and `test_adapt_one_video_reset_flag_controls_reset` asserting reset is NOT
  called when `reset=False` (count 0) and called exactly once when `reset=True`
  (count 1), with score shapes `(5,)`.

## Verification

- `python -m pytest tests/test_evaluate_tta.py -q` → **8 passed** (includes the
  new test).
- `python -m pytest tests/test_evaluate_tta.py tests/test_tent.py tests/test_sar.py -q`
  → **24 passed** (no regression).
- `python src/tta/evaluate_tta.py --help` → lists `--protocol {episodic,continual}`.
- `grep -n "protocol" src/tta/evaluate_tta.py` shows the param (line 244), the
  reset guard (line 302), and the payload field (line 355), plus CLI arg (91)
  and main() call (426).

## Deviations from Plan

None — plan executed exactly as written. The Task 2 payload field and the
main() call (no verbatim strings given) were located by reading the file and
inserted next to `backbone` / after `feature_root` respectively.

## Commit

Single atomic commit `1ed2d16` of the two source files only
(`src/tta/evaluate_tta.py`, `tests/test_evaluate_tta.py`). PLAN/SUMMARY/STATE
not committed per constraints.

## Out of scope (not done, per plan)

- No grid run / results regeneration; no paper edit; default protocol unchanged
  (stays episodic). SAR EMA reset-on-collapse recovery not wired (noted only).

## Self-Check: PASSED
- `src/tta/evaluate_tta.py` modified, committed in 1ed2d16. FOUND.
- `tests/test_evaluate_tta.py` modified, committed in 1ed2d16. FOUND.
- Commit 1ed2d16 present in `git log`. FOUND.
