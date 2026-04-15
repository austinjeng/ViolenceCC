---
phase: 04b
plan: 05
type: execute
wave: 3
depends_on: [04b-01, 04b-02, 04b-03, 04b-04]
files_modified:
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
autonomous: false
requirements:
  - EVAL-01
tags: [empirical-gate, rtfm, roadmap-split, phase-4c-carveout, uat]
user_setup: []

must_haves:
  truths:
    - "1-epoch smoke test (D-16) on real E:/i3d-features data completes end-to-end without shape/dim errors (`python -m src.train --config configs/rtfm_i3d.yaml --epochs 1 --run-name smoke_xd_i3d_rtfm_i3d_s42`)"
    - "Full rtfm_gate queue run (`python scripts/run_ablations.py --queue rtfm_gate --no-preflight`) completes and produces `results/xd_i3d_rtfm_i3d_s42/eval_metrics.json` + `.done` marker + a row appended to `results/results-index.csv`"
    - "The `ap` key in `eval_metrics.json` is >= 0.7681 (D-03 primary gate = 77.81% - 1%) — if miss: trigger D-11 fallback cascade with D-12 diagnostics"
    - "D-12 diagnostic check 1 passes: bit-identical rerun (same cfg, same seed) produces matching 9 numeric keys in `eval_metrics.json`"
    - "D-12 diagnostic check 2 passes: `abs(snippet_auc - auc) < 0.02` (C4 snippet-to-frame integrity)"
    - "D-12 diagnostic check 3 passes: `[i3d_audit]` log line present in first 3 epochs of training, shapes correct (`n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024)`)"
    - "ROADMAP.md split: Phase 4b renamed to 'RTFM XD-I3D Gate' (narrow scope); NEW Phase 4c detail block inserted with the XD main results work relocated from Phase 4b; Progress Table updated"
    - "REQUIREMENTS.md annotation flip: EVAL-02..EVAL-05 XD-side phase annotations move from 'Phase 4b' to 'Phase 4c'; EVAL-01 stays in Phase 4b with expanded completion notes"
    - "04b-SUMMARY.md written documenting gate AP, D-12 diagnostic results, anchor comparison (RTFM 77.81%, MGFN I3D-RGB 79.19% — correction from CONTEXT.md D-11's stale 80.11% VideoSwin anchor), and any D-11 fallback path applied"
  artifacts:
    - path: ".planning/ROADMAP.md"
      provides: "Phase 4b narrowed to RTFM gate only; Phase 4c detail block inserted with XD main results scope"
      contains: "Phase 4c"
    - path: ".planning/REQUIREMENTS.md"
      provides: "EVAL-02..EVAL-05 XD-side annotations flipped to Phase 4c; EVAL-01 closed in Phase 4b"
      contains: "Phase 4c"
    - path: ".planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md"
      provides: "Phase 4b closeout: gate AP, D-12 diagnostics, D-11 fallback if triggered, anchor comparison"
  key_links:
    - from: "scripts/run_ablations.py"
      to: "src/train.py"
      via: "cfg.dataset == 'xd_i3d' dispatch (Plan 04b-03)"
      pattern: "xd_i3d"
    - from: "src/evaluate.py::_build_frame_arrays"
      to: "data/annotations/xd_temporal.txt"
      via: "parse_xd_annotations(ann_path) (Plan 04b-04)"
      pattern: "xd_temporal.txt"
---

<objective>
Execute the empirical RTFM XD-I3D gate and formalize the phase split per D-01. This plan has four concerns:
1. **Smoke test (D-16)** — 1-epoch run on real E:/i3d-features data to validate the dispatch chain (build_dataloaders_i3d → collate_i3d_train → train_one_epoch_i3d → validate_i3d → save_checkpoint_atomic) works without shape/dim errors.
2. **Full gate run** — `python scripts/run_ablations.py --queue rtfm_gate --no-preflight` and check `eval_metrics.json.ap >= 0.7681`.
3. **D-12 diagnostic cascade** — if the smoke passes AND the gate misses, run the 3 orthogonal diagnostic checks (bit-identical rerun, C4 sanity, bag-size audit) to determine whether the miss is a dispatch bug (fix in place) or a modeling issue (trigger D-11 fallback cascade).
4. **ROADMAP + REQUIREMENTS split (D-01)** — rename Phase 4b title to "RTFM XD-I3D Gate", insert Phase 4c detail block carrying the XD main results scope (the previously-bundled "Deferred from Phase 4" subsection), update Progress Table, flip REQUIREMENTS.md EVAL-02..EVAL-05 XD-side annotations from Phase 4b to Phase 4c, and write `04b-05-SUMMARY.md` with empirical results + anchor comparison (noting the MGFN 80.11% -> 79.19% anchor correction from RESEARCH.md).

Purpose: Close EVAL-01. Produce a reproducible AP number that validates the entire XD-I3D evaluation harness. Hand off all XD-Violence main results work (EVAL-02..EVAL-05 XD-side) to the new Phase 4c, cleanly separated by the D-01 scope narrowing.

Output: `results/xd_i3d_rtfm_i3d_s42/` directory with full run artifacts, updated `.planning/ROADMAP.md` + `.planning/REQUIREMENTS.md`, new `04b-05-SUMMARY.md`, optional `04b-UAT.md` if the gate misses and D-11 fallback is triggered.

**Autonomous: FALSE** — the gate pass/fail decision, D-11 fallback triggering, and ROADMAP split wording all require human judgment at the HUMAN-UAT checkpoint.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-CONTEXT.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-PATTERNS.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-VALIDATION.md

<!-- Prior plan artifacts from Waves 1-2: -->
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-01-PLAN.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-02-PLAN.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-03-PLAN.md
@.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-04-PLAN.md

<!-- Empirical infrastructure (unchanged): -->
@configs/rtfm_i3d.yaml
@scripts/run_ablations.py

<!-- Phase 4 closeout patterns (mirror for Phase 4b closeout): -->
@.planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md
@.planning/phases/04-baseline-evaluation-main-results/04-06-UAT.md

<interfaces>
<!-- Contracts the executor works against. -->

**rtfm_gate queue entry in scripts/run_ablations.py::QUEUES (line 84):**
```python
QUEUES = {
    "rtfm_gate": [
        RunSpec("xd_i3d", "rtfm_i3d", 42, "configs/rtfm_i3d.yaml"),
    ],
    ...
}
```

**is_done() skip logic in run_ablations.py (line 124):**
```python
def is_done(run_dir: Path) -> bool:
    return (run_dir / ".done").exists()
```
Implication: a leftover `.done` file skips re-runs. Planner Pitfall 5: cleanup before each invocation.

**eval_metrics.json expected keys (from existing UCF runs):**
```
{
  "auc": float,          # frame-level ROC-AUC
  "ap": float,           # frame-level Average Precision (the gate)
  "snippet_auc": float,  # auc at snippet granularity (for C4 sanity)
  "video_auc": float,
  "n_videos": int,
  "n_frames": int,
  "positive_fraction": float,
  "per_category_auc": object,
  "per_category_ap": object
}
```

**Gate anchors (D-03, per RESEARCH.md anchor verification):**
- Primary: RTFM XD-I3D-RGB AP = 77.81% → ±1% → pass if AP ∈ [76.81%, 78.81%]
- Secondary (D-11 fallback 1): MGFN XD-I3D-RGB AP = **79.19%** (NOT 80.11% — that is MGFN VideoSwin per RESEARCH.md §RTFM/MGFN Anchor Verification; planner MUST use 79.19% in SUMMARY and UAT)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Idempotent cleanup + 1-epoch smoke test on real data (D-16)</name>
  <files>(execution only — no file writes to track; artifacts in results/ are ignored by .gitignore)</files>
  <read_first>
    - configs/rtfm_i3d.yaml (confirm `wandb.mode: disabled`, `data.batch_size: 3`, `paths.i3d_features: E:/i3d-features/i3d-features`)
    - scripts/run_ablations.py (confirm `rtfm_gate` queue entry)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "Pitfall 5" (lines 811-819) for idempotent cleanup requirement
  </read_first>
  <action>
    Step 1 — Idempotent cleanup of any leftover run directories (Pitfall 5):
    ```bash
    rm -rf results/smoke_xd_i3d_rtfm_i3d_s42/ results/xd_i3d_rtfm_i3d_s42/ 2>/dev/null || true
    # Verify cleanup
    test ! -d results/smoke_xd_i3d_rtfm_i3d_s42/
    test ! -d results/xd_i3d_rtfm_i3d_s42/
    ```

    Step 2 — Run the 1-epoch smoke test (D-16):
    ```bash
    C:/Anaconda/envs/vcc-main/python.exe -m src.train \
      --config configs/rtfm_i3d.yaml \
      --epochs 1 \
      --run-name smoke_xd_i3d_rtfm_i3d_s42 \
      2>&1 | tee /tmp/smoke_stdout.log
    ```
    Expected behavior:
    - Exits 0
    - stderr contains `[i3d_audit] epoch=0 step=0 n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024) mask_shape=(30, 32)` (or equivalent shapes)
    - `results/smoke_xd_i3d_rtfm_i3d_s42/best_model.pth` exists
    - `results/smoke_xd_i3d_rtfm_i3d_s42/train_log.csv` exists
    - No KeyError, no NaN loss in train_log.csv
    - Total wall-clock: ~20-60 seconds on RTX 4090 (per research budget)

    Step 3 — Verify smoke artifacts + extract the bag-size audit line for the SUMMARY:
    ```bash
    ls -la results/smoke_xd_i3d_rtfm_i3d_s42/
    cat results/smoke_xd_i3d_rtfm_i3d_s42/train_log.csv | head -3
    # Grep the audit line from the tee'd stdout
    grep "\[i3d_audit\]" /tmp/smoke_stdout.log || true
    ```
    Record the audit line verbatim for inclusion in 04b-05-SUMMARY.md.

    Step 4 — Delete the smoke run dir (research Open Question #3 recommendation):
    ```bash
    rm -rf results/smoke_xd_i3d_rtfm_i3d_s42/
    test ! -d results/smoke_xd_i3d_rtfm_i3d_s42/
    ```

    IF SMOKE FAILS:
    - If `KeyError: 'skeleton_features'` or similar → dispatch branch missing in src/train.py::main() (Plan 04b-03 regression); STOP and flag Rule 4
    - If `KeyError: 'i3d'` in collate → build_dataloaders_i3d collate wiring broken (Plan 04b-02 regression); STOP and flag Rule 4
    - If NaN loss in first epoch → mask synthesis missing in train_one_epoch_i3d (Pitfall 1); STOP and flag Rule 4
    - If file-not-found on E:/i3d-features/i3d-features/RGB → I3D cache missing; STOP — this is a data-availability issue, NOT a code issue, requires user intervention
    - Any other failure → STOP and report stderr tail
  </action>
  <verify>
    <automated>test ! -d results/smoke_xd_i3d_rtfm_i3d_s42/ && test ! -d results/xd_i3d_rtfm_i3d_s42/</automated>
  </verify>
  <acceptance_criteria>
    - Before-smoke cleanup: `ls results/` shows NO `smoke_xd_i3d_rtfm_i3d_s42/` or `xd_i3d_rtfm_i3d_s42/` directory
    - Smoke run exits 0: `echo $?` immediately after smoke command outputs `0`
    - Smoke artifacts written during the run: `best_model.pth` and `train_log.csv` both appeared in `results/smoke_xd_i3d_rtfm_i3d_s42/` BEFORE Step 4 cleanup
    - `[i3d_audit]` line captured to the SUMMARY notes
    - After Step 4 cleanup: `test ! -d results/smoke_xd_i3d_rtfm_i3d_s42/` exit 0
    - Clean state confirmed before Task 2: `test ! -d results/xd_i3d_rtfm_i3d_s42/` exit 0
  </acceptance_criteria>
  <done>Smoke test passes on real data. Dispatch chain end-to-end validated. Bag-size audit line captured. Smoke dir cleaned up. Ready for full gate run.</done>
</task>

<task type="auto">
  <name>Task 2: Full rtfm_gate queue run + eval_metrics.json parsing + gate check</name>
  <files>(execution only — no file writes to track)</files>
  <read_first>
    - configs/rtfm_i3d.yaml (unchanged)
    - scripts/run_ablations.py (unchanged; `rtfm_gate` queue is already correct)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "RTFM / MGFN Anchor Verification" (lines 704-750) for the anchor bands
  </read_first>
  <action>
    Step 1 — Run the full rtfm_gate queue (expected wall-clock: 10-20 minutes on RTX 4090 for 50 epochs + eval):
    ```bash
    C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue rtfm_gate --no-preflight 2>&1 | tee /tmp/gate_stdout.log
    ```
    Expected artifacts in `results/xd_i3d_rtfm_i3d_s42/`:
    - `best_model.pth`
    - `last_model.pth`
    - `config_snapshot.json`
    - `eval_metrics.json`
    - `eval_scores.npz`
    - `per_category.csv`
    - `.done`
    - `train_log.csv`
    Plus one row appended to `results/results-index.csv`.

    Step 2 — Parse eval_metrics.json and check the gate:
    ```bash
    C:/Anaconda/envs/vcc-main/python.exe -c "
    import json
    m = json.load(open('results/xd_i3d_rtfm_i3d_s42/eval_metrics.json'))
    print('=== eval_metrics.json ===')
    for k, v in sorted(m.items()):
        print(f'  {k}: {v}')
    ap = m.get('ap')
    print(f'\\n=== Gate check (D-03 primary anchor: RTFM 77.81%, ±1%) ===')
    print(f'AP = {ap:.4f}')
    gate = 0.7681
    if ap >= gate:
        print(f'PASS: AP {ap:.4f} >= {gate} gate')
    else:
        delta = gate - ap
        print(f'MISS: AP {ap:.4f} < {gate} gate (shortfall: {delta:.4f} = {delta*100:.2f}pp)')
    "
    ```

    Step 3 — Record all 9 numeric keys from `eval_metrics.json` for the SUMMARY + D-12 check 2:
    ```bash
    # Capture auc vs snippet_auc delta (D-12 check 2: abs < 0.02)
    C:/Anaconda/envs/vcc-main/python.exe -c "
    import json
    m = json.load(open('results/xd_i3d_rtfm_i3d_s42/eval_metrics.json'))
    auc = m.get('auc', 0.0); snip_auc = m.get('snippet_auc', 0.0)
    delta = abs(auc - snip_auc)
    print(f'D-12 Check 2 (C4 sanity): auc={auc:.4f} snippet_auc={snip_auc:.4f} delta={delta:.4f}')
    print(f'PASS' if delta < 0.02 else f'LARGE DELTA — investigate snippet-to-frame broadcast (C4 Pitfall)')
    "
    ```

    Step 4 — Confirm a new row appended to results-index.csv:
    ```bash
    tail -3 results/results-index.csv
    grep "xd_i3d_rtfm_i3d_s42" results/results-index.csv | wc -l
    # expect >= 1 (may be 1 if fresh, or 2 if a stale row already existed from earlier attempts)
    ```
  </action>
  <verify>
    <automated>test -f results/xd_i3d_rtfm_i3d_s42/.done && test -f results/xd_i3d_rtfm_i3d_s42/eval_metrics.json</automated>
  </verify>
  <acceptance_criteria>
    - `results/xd_i3d_rtfm_i3d_s42/.done` exists
    - `results/xd_i3d_rtfm_i3d_s42/eval_metrics.json` exists and is valid JSON
    - `results/xd_i3d_rtfm_i3d_s42/best_model.pth` exists
    - `results/xd_i3d_rtfm_i3d_s42/config_snapshot.json` exists
    - eval_metrics.json contains an `ap` key of float type
    - `grep -c "xd_i3d_rtfm_i3d_s42" results/results-index.csv` outputs `>=1`
    - Gate status recorded: PASS if `ap >= 0.7681` OR MISS (with shortfall magnitude) — BOTH outcomes are acceptable here; the PASS/MISS disposition is handled in Task 3
    - D-12 Check 2 (auc vs snippet_auc delta): value captured into the SUMMARY draft; delta < 0.02 is ideal but any value is recorded for human review
  </acceptance_criteria>
  <done>Full gate queue completed. eval_metrics.json produced. AP value extracted. Gate status (PASS / MISS) determined. All 9 numeric keys captured for SUMMARY.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: HUMAN-UAT — Gate disposition decision + D-12 bit-identical rerun diagnostic</name>
  <what-built>
    Task 2 completed a full rtfm_gate queue run. `results/xd_i3d_rtfm_i3d_s42/eval_metrics.json` contains the AP value.
    The numeric outcome (PASS / MISS) requires human judgment on:
    1. Whether AP passes the D-03 primary anchor (≥ 0.7681)
    2. If MISS: whether to invoke the D-11 fallback cascade (relax to MGFN 79.19%, add Flow, add MTN, or accept as thesis limitation)
    3. Whether the D-12 bit-identical rerun diagnostic should be executed (recommended if MISS; optional but highly encouraged if PASS for reproducibility provenance)
  </what-built>
  <how-to-verify>
    1. Read the eval_metrics.json + gate disposition from Task 2 output:
       ```
       AP = {value}
       Gate check: PASS / MISS
       D-12 Check 2 (auc vs snippet_auc delta): {value}
       ```
       And review the `[i3d_audit]` line captured from Task 1 (D-12 Check 3).

    2. If GATE PASS (AP >= 0.7681):
       - (Recommended but not blocking) Run the D-12 bit-identical rerun diagnostic:
         ```bash
         # Cleanup
         rm -rf results/xd_i3d_rtfm_i3d_s42/
         # Re-run
         C:/Anaconda/envs/vcc-main/python.exe scripts/run_ablations.py --queue rtfm_gate --no-preflight 2>&1 | tee /tmp/gate_rerun.log
         # Capture new metrics
         C:/Anaconda/envs/vcc-main/python.exe -c "import json; print(json.dumps(json.load(open('results/xd_i3d_rtfm_i3d_s42/eval_metrics.json')), indent=2, sort_keys=True))" > /tmp/gate_rerun_metrics.json
         # Compare
         diff /tmp/gate_original_metrics.json /tmp/gate_rerun_metrics.json || true
         ```
         Expected: 9 numeric keys match to the same precision (`set_deterministic(42)` + `CUBLAS_WORKSPACE_CONFIG` guarantee this per Phase 3 SC #4).
       - RESPOND: `"approved: AP={value} passes; {with|without} D-12 rerun verified"`

    3. If GATE MISS (AP < 0.7681):
       - First: verify D-12 checks 2 & 3 pass (these rule out dispatch bugs before invoking D-11 fallback)
         - Check 2: `abs(auc - snippet_auc) < 0.02` (from Task 2 Step 3 output)
         - Check 3: `[i3d_audit]` line from Task 1 shows `n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024)`
       - If either diagnostic fails → dispatch bug; STOP and return to Plan 04b-02 or 04b-03 with the failure mode documented
       - If both diagnostics pass → modeling issue; choose D-11 fallback step (per RESEARCH.md §RTFM/MGFN Anchor Verification corrected to 79.19% not 80.11%):
         - **Step 1 (if miss is < 3pp, AP ∈ [73.81%, 76.81%])**: Relax anchor to MGFN I3D-RGB 79.19% (NOT 80.11% VideoSwin per research correction). Document in SUMMARY as "within RTFM/MGFN I3D-RGB published band; MGFN I3D-RGB 79.19% anchor applied."
         - **Step 2**: Add RGB+Flow I3D stream. Requires new `configs/rtfm_i3d_rgbflow.yaml` with `i3d_dim: 2048` + modified loader to concat RGB + Flow crops + `RTFMI3D(i3d_dim=2048)`. Expected ~1-2pp AP lift. Estimated: 1 day engineering.
         - **Step 3**: Add MTN temporal module to `src/models/rtfm_i3d.py`. Heavier lift (~150 LOC); breaks LN-naming simplicity unless carefully done. Estimated: 2-3 days.
         - **Step 4**: Accept miss + document as thesis limitation. Mirrors Phase 4 EVAL-02 MISS-accepted pattern (UCF 0.8227 vs 0.83 gate).
       - RESPOND: `"miss: AP={value}; fallback-step-{1|2|3|4} selected; {rationale}"`

    4. If the D-12 bit-identical rerun is run, record the rerun AP + any numeric divergence in the SUMMARY. Bit-identical means ALL 9 numeric keys match exactly. Any divergence indicates a non-determinism bug (e.g., hidden `torch.use_deterministic_algorithms(False)` somewhere, or a library update).
  </how-to-verify>
  <resume-signal>
    Required format for resume:
    - "approved: AP={value} passes; {with|without} D-12 rerun verified"
    - OR "miss: AP={value}; fallback-step-{1|2|3|4} selected; {rationale}"

    Common cases:
    - `"approved: AP=0.7850 passes; with D-12 rerun verified"` → proceed to Task 4
    - `"miss: AP=0.7650; fallback-step-1 selected; within MGFN I3D-RGB 79.19% published band, 0.31pp under primary anchor"` → proceed to Task 4 with D-11 fallback wording in SUMMARY
    - `"miss: AP=0.6800; fallback-step-4 selected; thesis limitation mirrors EVAL-02 UCF pattern"` → proceed to Task 4 with acceptance wording
    - `"abort: dispatch bug in {Plan 04b-0X}, returning to fix"` → STOP; return to upstream plan for remediation
  </resume-signal>
  <files>(no file writes — decision/review only)</files>
  <action>
    HUMAN-UAT gate. The assistant MUST NOT proceed past this task without a resume-signal from the user. The decision criteria and options are documented fully in the `<how-to-verify>` block above. The assistant should:
    1. Print the eval_metrics.json summary (AP, AUC, snippet_auc, video_auc) captured in Task 2.
    2. Print the `[i3d_audit]` line captured in Task 1.
    3. Print the D-12 Check 2 delta (abs(auc - snippet_auc)).
    4. Wait for the user to issue a resume-signal in the required format.

    On resume-signal:
    - If "approved": proceed to Task 4 (record the PASS disposition and AP in the SUMMARY draft).
    - If "miss: ... fallback-step-1 ...": proceed to Task 4 (record MISS with MGFN 79.19% anchor applied).
    - If "miss: ... fallback-step-2/3 ...": STOP — this is a D-11 cascade invocation that requires a follow-up plan to add RGB+Flow or MTN; Plan 04b-05 cannot complete autonomously in this case.
    - If "miss: ... fallback-step-4 ...": proceed to Task 4 (record MISS-ACCEPTED with thesis-limitation wording).
    - If "abort": STOP — return to upstream plan for remediation.
  </action>
  <verify>
    <automated>test -f results/xd_i3d_rtfm_i3d_s42/eval_metrics.json</automated>
  </verify>
  <acceptance_criteria>
    - Resume-signal received in one of the 4 documented formats
    - Gate disposition (PASS / MISS-step-N / abort) captured for Task 5 SUMMARY
    - If D-12 bit-identical rerun was performed, both runs' eval_metrics.json available for diff (captured to /tmp/gate_original_metrics.json + /tmp/gate_rerun_metrics.json)
  </acceptance_criteria>
  <done>Human judgment received; gate disposition recorded; assistant proceeds to Task 4 (or stops if fallback-step-2/3 or abort signaled).</done>
</task>

<task type="auto">
  <name>Task 4: ROADMAP.md + REQUIREMENTS.md split per D-01 (narrow Phase 4b, insert Phase 4c)</name>
  <files>.planning/ROADMAP.md, .planning/REQUIREMENTS.md</files>
  <read_first>
    - .planning/ROADMAP.md (full file — focus on the Phase 4b detail block at lines 95-117, the Phase 4 -> Phase 4b transition at lines 75-94, the Phase 4b -> Phase 5 transition at lines 119+, the Progress Table at lines 142-153, and the Requirement Coverage table at lines 156-199)
    - .planning/REQUIREMENTS.md (full file — focus on the EVAL-01..EVAL-05 block at lines 50-54 and the Traceability table at lines 111-152)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-CONTEXT.md Decisions D-01 (scope narrowing contract — the planner edit spec)
    - Phase 4 Plan 07 summary for the closeout-pattern template: .planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md
  </read_first>
  <action>
    The ROADMAP.md and REQUIREMENTS.md edits are a documentation-only atomic commit. Follow D-01's verbatim requirements:

    Edit Set A — `.planning/ROADMAP.md`:

    A1. Update the top-of-file phase bullet list entry for Phase 4b. Find the current:
    ```
    - [ ] **Phase 4b: XD-Violence Main Results + RTFM XD-I3D Gate** - ... (activated when XD skeleton+CLIP features complete, though the RTFM gate work can start immediately ...)
    ```
    Replace with (per D-01 title narrowing):
    ```
    - [x] **Phase 4b: RTFM XD-I3D Gate** - xd_i3d training dispatch + Wu XD annotation parser + RTFM XD-I3D-RGB gate (AP {GATE_AP} vs 0.7681 target per D-03; completed {DATE} per D-01 scope narrowing, XD main results carved out to new Phase 4c)
    - [ ] **Phase 4c: XD-Violence Main Results** - Gated Fusion + ablations + 3-seed stability on XD-Violence (scope relocated from former Phase 4b per D-01; activated when XD skeleton+CLIP features complete)
    ```
    (If the gate was a MISS, change `[x]` to `[ ]` and annotate with MISS-accepted wording reflecting Task 3's decision.)

    A2. Replace the existing Phase 4b detail block (lines ~95-117) with a narrow Phase 4b detail block:
    ```markdown
    ### Phase 4b: RTFM XD-I3D Gate
    **Goal**: The xd_i3d training dispatch (`build_dataloaders_i3d`, `train_one_epoch_i3d`, `validate_i3d`, Wu et al. annotation parser) is implemented, and the RTFM XD-I3D-RGB baseline reproduces frame-level AP within ±1% of 77.81% (Rescoped from Phase 4 per 2026-04-15 Option B decision; scope narrowed to RTFM gate only per D-01 of 04b-CONTEXT.md, XD main results carved out to new Phase 4c).
    **Depends on**: Phase 4 (architectural patterns + code artifacts), E:/i3d-features/i3d-features (RGB + RGBTest I3D features on disk; verified 16124 + 4000 files)
    **Requirements**: EVAL-01
    **Success Criteria** (what must be TRUE):
      1. RTFM on XD-Violence I3D RGB features reports frame-level AP within ±1% of 77.81% (primary anchor RTFM 77.81%; secondary anchor MGFN I3D-RGB 79.19% per 04b-RESEARCH.md correction — NOT 80.11% VideoSwin)
      2. xd_i3d training dispatch (`build_dataloaders_i3d`, `train_one_epoch_i3d`, `validate_i3d`) exists in `src/data/loaders.py` + `src/train.py` with D-04 parallel-functions discipline (no polymorphic dispatch)
      3. Wu et al. XD-Violence annotation parser (`src/eval/xd_annotations.py`) + `data/annotations/xd_temporal.txt` committed; `src/evaluate.py::_build_frame_arrays` xd_i3d path rewritten (replacing the all-zero stub from Phase 4)
      4. D-12 diagnostic passes: bit-identical rerun (9 numeric keys match), C4 sanity (|auc - snippet_auc| < 2pp), 5-crop bag-size audit ([i3d_audit] log line with n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024))
      5. 4 new pytest test files pass: test_xd_annotations.py (8 tests), test_loaders_i3d.py (5 tests), test_train_i3d.py (3 tests), test_evaluate_xd_i3d.py (4 tests)
    **Plans:** 5/5 plans complete ({DATE})
    Plans:
    - [x] 04b-01-PLAN.md — Wu annotation parser + data/annotations/xd_temporal.txt + test_xd_annotations.py (D-07, D-10)
    - [x] 04b-02-PLAN.md — build_dataloaders_i3d + collate_i3d_train + test_loaders_i3d.py (D-04, D-05, D-06; Pitfalls 1, 4, 7; OQ #1, #2)
    - [x] 04b-03-PLAN.md — train_one_epoch_i3d + validate_i3d + main() dispatch + test_train_i3d.py (D-04; D-12 bag-size audit)
    - [x] 04b-04-PLAN.md — _build_frame_arrays xd_i3d rewrite + test_evaluate_xd_i3d.py (D-08, D-09, D-10)
    - [x] 04b-05-PLAN.md — Smoke test (D-16) + rtfm_gate queue run + ROADMAP/REQUIREMENTS split (D-01) + 04b-05-SUMMARY.md
    ```

    A3. IMMEDIATELY AFTER the narrowed Phase 4b block, INSERT a new Phase 4c detail block carrying the previously-bundled XD main results scope:
    ```markdown
    ### Phase 4c: XD-Violence Main Results
    **Goal**: Reproduce Phase 4's complete ablation table on XD-Violence — Gated Fusion + pooling ablations + 3-seed stability + per-category breakdown (Fighting/Abuse/Riot) — using the dataset-portable Phase 4 code (evaluate.py, run_ablations.py, extractors with flags). Relocated from the original Phase 4b scope per D-01 scope narrowing (see 04b-CONTEXT.md).
    **Depends on**: Phase 4 (code artifacts), Phase 4b (xd_i3d dispatch + Wu annotation parser for the fusion-XD eval path), Phase 2 DATA-10 (XD skeleton+CLIP extraction complete at E:/features/xd/)
    **Activation criterion**: `ls -1 E:/features/xd/skeleton/*.npy | wc -l >= 4500 && ls -1 E:/features/xd/clip/*.npy | wc -l >= 4500`. Checked at each `/gsd-progress` invocation; when both counts pass, the user triggers `/gsd-plan-phase 4c`. No polling infrastructure needed (D-03 of 04b-CONTEXT.md).
    **Requirements**: EVAL-02, EVAL-03, EVAL-04, EVAL-05 (XD-side; UCF-side already complete in Phase 4)
    **Success Criteria** (what must be TRUE):
      1. Gated Fusion achieves frame-level AP >= 80% on XD-Violence official test set, reported by `evaluate.py` with no test set used during training
      2. An ablation table exists with results for all 6 XD model variants (Skeleton-Only, CLIP-Only, Late Fusion, Gated Fusion) and 2 pooling/aggregation ablations, all run on the same XD train/val/test split
      3. Gated Fusion AP on XD-Violence is reported as mean ± std over 3 independent seeds ({42, 123, 2024}), and the standard deviation is below 0.5%
      4. Per-category breakdown (XD-Violence: Fighting+Abuse+Riot) is computed and shows higher AP on violence-specific subsets versus full test set
    **Scope (relocated from former Phase 4b per D-01):**
      - XD skeleton 2-person aggregation re-extraction (`--keep-persons` on XD in extract_ctrgcn.py)
      - XD CLIP mean-only re-extraction (`--pool=mean` on XD in extract_clip.py)
      - XD pooling ablation YAMLs (`configs/gated_fusion_xd_2person.yaml`, `configs/gated_fusion_xd_clip_mean.yaml` — or reuse UCF YAMLs with dataset key swap)
      - XD ablation orchestration queues in `scripts/run_ablations.py` (add `phase4c_main`, `phase4c_pooling`, `phase4c_seeds` queues)
      - Per-category Fighting/Abuse/Riot breakdown (uses `_parse_category` from `src/eval/xd_annotations.py` delivered in Phase 4b)
    **Plans**: TBD (plan with `/gsd-plan-phase 4c` once XD skeleton+CLIP features land)
    ```

    A4. Update the Progress Table at lines ~142-153:
    - Change the existing "4b. XD-Violence Main Results + RTFM XD-I3D Gate" row to reflect the narrow Phase 4b title + completion
    - ADD a new row for "4c. XD-Violence Main Results" with "Blocked on XD features" status
    Example:
    ```markdown
    | Phase | Plans Complete | Status | Completed |
    |-------|----------------|--------|-----------|
    | 1. Environment & Project Foundation | 3/3 | Complete   | 2026-03-31 |
    | 2. Feature Extraction Pipeline | 4/4 | Complete   | 2026-04-XX |
    | 3. Model Architecture & Training Infrastructure | 7/7 | Complete | 2026-04-XX |
    | 4. Baseline Evaluation & Main Results | 7/7 | Complete | 2026-04-16 |
    | 4b. RTFM XD-I3D Gate | 5/5 | Complete | {DATE} |
    | 4c. XD-Violence Main Results | 0/? | Blocked on XD features | - |
    | 5. TTA Infrastructure & Corruption Experiments | 0/? | Not started | - |
    | 6. Analysis & Visualization | 0/? | Not started | - |
    ```
    (Adjust Phase 2/3 rows to reflect their actual completion state — do NOT invent; if they're still pending per STATE.md, leave them as-is. The Progress Table entry for 4b/4c is the MUST-have edit.)

    A5. Update the Requirement Coverage table at lines ~156-199 to reflect dual-phase ownership for EVAL-02..EVAL-05:
    ```markdown
    | EVAL-01 | Phase 4b |
    | EVAL-02 | Phase 4 (UCF), Phase 4c (XD) |
    | EVAL-03 | Phase 4 (UCF), Phase 4c (XD) |
    | EVAL-04 | Phase 4 (UCF), Phase 4c (XD) |
    | EVAL-05 | Phase 4 (UCF), Phase 4c (XD) |
    ```

    A6. Refresh the footer `Last updated:` line:
    ```markdown
    *Last updated: {DATE} after Phase 4b closeout (04b-05): Phase 4b narrowed to RTFM XD-I3D Gate (5/5 Complete); new Phase 4c detail block inserted for XD-Violence Main Results per D-01 scope narrowing*
    ```

    Edit Set B — `.planning/REQUIREMENTS.md`:

    B1. Update the checkbox list entries for EVAL-01..EVAL-05 at lines ~50-54. CURRENT:
    ```markdown
    - [ ] **EVAL-01**: ... (retargeted to XD-I3D per Phase 4 D-03; deferred to Phase 4b per 2026-04-15 Option B decision — xd_i3d training dispatch not wired in Plan 04-03)
    - [x] **EVAL-02**: Frame-level AUC (ROC) evaluation on UCF-Crime official test set with correct snippet-to-frame score expansion (UCF complete in Phase 4; XD-side Phase 4b)
    - [x] **EVAL-03**: Frame-level AP evaluation on XD-Violence official test set (UCF-adapted ablation table complete in Phase 4; XD AP pending Phase 4b)
    - [x] **EVAL-04**: Per-category violence subset breakdown (UCF-Crime: Fighting+Assault complete in Phase 4; XD-Violence: Fighting+Abuse+Riot pending Phase 4b)
    - [x] **EVAL-05**: Key results (Gated Fusion on both datasets) repeated 3 times with mean +/- std (UCF complete in Phase 4: std 0.00291; XD pending Phase 4b)
    ```

    Replace with:
    ```markdown
    - [x] **EVAL-01**: RTFM baseline reproduction — frame-level AP gate on XD-Violence I3D-RGB 5-crop features within ±1% of 77.81% per D-03 (Rescoped from Phase 4 per 2026-04-15 Option B decision; completed in Phase 4b per D-01 scope narrowing; AP {GATE_AP} {PASS|MISS-ACCEPTED}; xd_i3d training dispatch + Wu annotation parser implemented in Phase 4b)
    - [x] **EVAL-02**: Frame-level AUC (ROC) evaluation on UCF-Crime official test set with correct snippet-to-frame score expansion (UCF complete in Phase 4; XD-side Phase 4c per D-01 scope narrowing)
    - [x] **EVAL-03**: Frame-level AP evaluation on XD-Violence official test set (UCF-adapted ablation table complete in Phase 4; XD AP pending Phase 4c per D-01 scope narrowing)
    - [x] **EVAL-04**: Per-category violence subset breakdown (UCF-Crime: Fighting+Assault complete in Phase 4; XD-Violence: Fighting+Abuse+Riot pending Phase 4c per D-01 scope narrowing)
    - [x] **EVAL-05**: Key results (Gated Fusion on both datasets) repeated 3 times with mean +/- std (UCF complete in Phase 4: std 0.00291; XD pending Phase 4c per D-01 scope narrowing)
    ```
    (If the gate MISSED, change `[x]` to `[ ]` for EVAL-01 AND update the annotation. `MISS-ACCEPTED` wording mirrors Phase 4 EVAL-02 pattern.)

    B2. Update the Traceability table rows at lines ~139-143. CURRENT for EVAL-01:
    ```markdown
    | EVAL-01 | Phase 4b | Deferred — xd_i3d training dispatch not implemented in Phase 4; rescoped to Phase 4b per 2026-04-15 Option B decision (04-06-UAT.md). Phase 4b must implement `build_dataloaders_i3d` + `train_one_epoch_i3d` + Wu et al. annotation parser before re-running the RTFM gate. |
    | EVAL-02 | Phase 4 (UCF), Phase 4b (XD) | Complete (UCF): ... ; XD-side pending Phase 4b |
    ... (same pattern for EVAL-03/04/05)
    ```

    Replace EVAL-01 row with:
    ```markdown
    | EVAL-01 | Phase 4b | {PASS|MISS-ACCEPTED}: AP {GATE_AP} ({PASS: "within RTFM 77.81 ±1% band" | MISS-ACCEPTED: "shortfall {X}pp; D-11 fallback step {N} applied: {rationale}"}); xd_i3d dispatch + Wu parser implemented in Phase 4b; 4 new pytest files pass. |
    ```

    Replace EVAL-02..EVAL-05 rows with:
    ```markdown
    | EVAL-02 | Phase 4 (UCF), Phase 4c (XD) | Complete (UCF): AUC 0.8227 (documented MISS vs 0.83 target; 3-seed mean 0.81982 std 0.00291); XD-side pending Phase 4c per D-01 scope narrowing |
    | EVAL-03 | Phase 4 (UCF), Phase 4c (XD) | Complete (UCF): 8 UCF rows in results/results-index.csv; XD-side pending Phase 4c per D-01 scope narrowing |
    | EVAL-04 | Phase 4 (UCF), Phase 4c (XD) | Complete (UCF): Fighting 0.955 (+13.23 pp), Assault 0.985 (+16.19 pp); XD-side (Fighting+Abuse+Riot) pending Phase 4c per D-01 scope narrowing |
    | EVAL-05 | Phase 4 (UCF), Phase 4c (XD) | Complete (UCF): 3-seed AUC std 0.00291 < 0.5% gate; XD-side pending Phase 4c per D-01 scope narrowing |
    ```

    B3. Refresh the footer `Last updated:` line:
    ```markdown
    *Last updated: {DATE} after Phase 4b closeout (04b-05): EVAL-01 {PASS|MISS-ACCEPTED} in Phase 4b (RTFM XD-I3D gate); EVAL-02..EVAL-05 XD-side annotations flipped from Phase 4b to Phase 4c per D-01 scope narrowing*
    ```

    After edits, verify the atomic commit is clean:
    ```bash
    git diff --stat .planning/ROADMAP.md .planning/REQUIREMENTS.md
    # Both files should show as modified; no other files
    ```
  </action>
  <verify>
    <automated>grep -q "### Phase 4c: XD-Violence Main Results" .planning/ROADMAP.md && grep -q "Phase 4c (XD)" .planning/REQUIREMENTS.md && grep -q "### Phase 4b: RTFM XD-I3D Gate" .planning/ROADMAP.md</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "### Phase 4b: RTFM XD-I3D Gate" .planning/ROADMAP.md` exit 0 (narrowed title present)
    - `grep -q "### Phase 4c: XD-Violence Main Results" .planning/ROADMAP.md` exit 0 (new Phase 4c detail block present)
    - Phase 4b detail block mentions AP value (PASS or MISS) via `grep -q "ap" .planning/ROADMAP.md` (the edit includes the gate AP)
    - `grep -q "Phase 4c (XD)" .planning/REQUIREMENTS.md` exit 0 (traceability flipped)
    - `grep -c "Phase 4b (XD)" .planning/REQUIREMENTS.md` outputs `0` (old annotation removed)
    - Progress Table has both Phase 4b and Phase 4c rows: `grep -c "| 4b\." .planning/ROADMAP.md` outputs `>=1`; `grep -c "| 4c\." .planning/ROADMAP.md` outputs `>=1`
    - `Last updated` footer refreshed in both files
    - Diff is docs-only: `git diff --stat .planning/ROADMAP.md .planning/REQUIREMENTS.md` shows only these two files modified
    - Phase 5 + Phase 6 bullets and detail blocks UNCHANGED: `grep -c "### Phase 5: TTA" .planning/ROADMAP.md` outputs `1`; `grep -c "### Phase 6: Analysis" .planning/ROADMAP.md` outputs `1`
  </acceptance_criteria>
  <done>ROADMAP.md + REQUIREMENTS.md atomically updated per D-01; Phase 4b narrowed; Phase 4c inserted; EVAL-02..EVAL-05 annotations flipped to Phase 4c; Phase 5/6 untouched; docs-only diff.</done>
</task>

<task type="auto">
  <name>Task 5: Write 04b-05-SUMMARY.md with gate AP, D-12 diagnostics, D-11 fallback (if applicable), and anchor comparison</name>
  <files>.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md</files>
  <read_first>
    - .planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md (structural template for phase closeout summary; mirror YAML frontmatter + section structure)
    - results/xd_i3d_rtfm_i3d_s42/eval_metrics.json (the empirical output of Task 2)
    - results/xd_i3d_rtfm_i3d_s42/config_snapshot.json (the frozen config)
    - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-RESEARCH.md section "RTFM / MGFN Anchor Verification" (lines 704-750) for the anchor correction (MGFN I3D-RGB 79.19%, NOT 80.11% VideoSwin)
    - Task 1-4 output logs (captured [i3d_audit] line, 9 numeric keys, gate disposition, ROADMAP diff)
  </read_first>
  <action>
    Create NEW file `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` with the following structure (mirror 04-07-SUMMARY.md):

    ```markdown
    ---
    phase: 04b-xd-violence-main-results-rtfm-xd-i3d-gate
    plan: 05
    subsystem: training-harness + eval-harness + planning-docs
    tags: [eval-01, rtfm-gate, xd-i3d, dispatch-remediation, anchor-correction, roadmap-split]

    # Dependency graph
    requires:
      - phase: 04b
        provides: "04b-01 (Wu annotation parser + xd_temporal.txt), 04b-02 (build_dataloaders_i3d + collate), 04b-03 (train_one_epoch_i3d + validate_i3d + main() dispatch), 04b-04 (_build_frame_arrays xd_i3d rewrite)"
    provides:
      - "EVAL-01 {PASS|MISS-ACCEPTED}: AP {VALUE} on RTFM XD-I3D-RGB gate (primary anchor 77.81%, ±1%)"
      - "xd_i3d training dispatch implemented end-to-end; D-36 FALSIFIED-BY-4 now TRUE"
      - "Wu annotation parser + data/annotations/xd_temporal.txt committed (SHA256 {SHA})"
      - "ROADMAP.md Phase 4b narrowed to RTFM gate; Phase 4c detail block inserted for XD main results (D-01 scope split)"
      - "REQUIREMENTS.md EVAL-01 closed in Phase 4b; EVAL-02..EVAL-05 XD-side annotations flipped to Phase 4c"
      - "4 new pytest test files with 20 tests total (8 xd_annotations + 5 loaders + 3 train + 4 evaluate) all green"
    affects: [Phase 4c XD main results plan-invocation prompt, Phase 5 TTA adaptation base unchanged]

    # Tech tracking
    tech-stack:
      added: []
      patterns:
        - "Parallel-functions dispatch (D-04): avoids polymorphic bloat by adding _i3d variants alongside existing functions; single branch in main() selects based on cfg['dataset']"
        - "Crop-as-sample collate (D-05): custom collate_fn flattens [B, 5, T, 1024] -> [B*5, T, 1024] via torch.stack + reshape + labels.repeat_interleave(5); preserves MIL bag structure"
        - "Sentinel-guarded all-zero labels for omitted normals (Pitfall 2): Wu file omits 300 normal test videos; _build_frame_arrays uses 'if vid in annos' guard"
        - "Annotation-file canonical fallback (D-07 mirror of UCF D-04): cfg['paths']['annotations_dir'] with _PROJECT_ROOT / data / annotations / xd_temporal.txt fallback"
        - "D-12 orthogonal diagnostics: bit-identical rerun + |auc - snippet_auc| < 2pp + [i3d_audit] shape audit; rules out dispatch bugs before invoking D-11 fallback"

    key-files:
      created:
        - src/eval/xd_annotations.py
        - data/annotations/xd_temporal.txt
        - tests/test_xd_annotations.py
        - tests/test_loaders_i3d.py
        - tests/test_train_i3d.py
        - tests/test_evaluate_xd_i3d.py
        - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-01-SUMMARY.md
        - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-02-SUMMARY.md
        - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-03-SUMMARY.md
        - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-04-SUMMARY.md
        - .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md  # this file
      modified:
        - src/data/loaders.py  # added build_dataloaders_i3d + collate_i3d_train
        - src/train.py  # added train_one_epoch_i3d + validate_i3d + _split_labels_i3d + main() dispatch
        - src/evaluate.py  # rewrote _build_frame_arrays xd_i3d branch
        - tests/conftest.py  # added xd_temporal_path fixture
        - .planning/ROADMAP.md
        - .planning/REQUIREMENTS.md

    key-decisions:
      - "D-01 (Phase 4b scope narrowing) — APPLIED via ROADMAP.md + REQUIREMENTS.md edits in Task 4"
      - "D-11 fallback step {N} — {applied | not triggered}: {rationale}"
      - "MGFN I3D-RGB anchor corrected to 79.19% (was 80.11% VideoSwin per RESEARCH.md anchor-verification research)"

    # Metrics
    duration: "~{WALL_CLOCK_MINUTES} minutes (1-epoch smoke {SMOKE_MIN}m; full gate {GATE_MIN}m; docs edits {DOCS_MIN}m; {OPTIONAL: D-12 rerun {RERUN_MIN}m})"
    started: "{START_TIMESTAMP}"
    completed: "{END_TIMESTAMP}"
    tasks: 5 of 5
    files_modified: 6  # 4 .py src files + 2 .planning/*.md
    files_created: 10  # 6 src + 5 summary + 1 data

    requirements_completed:
      - "EVAL-01 ({PASS | MISS-ACCEPTED} per D-11 fallback step {N})"

    # Empirical results
    rtfm_gate:
      ap: {GATE_AP}
      gate_threshold: 0.7681
      disposition: "{PASS | MISS-ACCEPTED}"
      fallback_step: {1 | 2 | 3 | 4 | null}  # null if PASS
      auc: {AUC}
      snippet_auc: {SNIPPET_AUC}
      video_auc: {VIDEO_AUC}
      n_videos: {N_VIDEOS}
      n_frames: {N_FRAMES}
      positive_fraction: {POS_FRAC}

    d12_diagnostics:
      check_1_bit_identical_rerun:
        performed: {true | false}
        result: "{9 numeric keys match | divergence in {key}: orig={X} rerun={Y}}"
      check_2_c4_sanity:
        auc: {AUC}
        snippet_auc: {SNIPPET_AUC}
        delta: {DELTA}
        threshold: 0.02
        disposition: "{PASS | FAIL}"
      check_3_bag_size_audit:
        audit_line: "[i3d_audit] epoch=0 step=0 n_normal={X} n_abnormal={Y} i3d_shape=({A}, {B}, {C}) mask_shape=({D}, {E})"
        expected: "n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024) mask_shape=(30, 32)"
        disposition: "{PASS | FAIL}"

    anchor_comparison:
      primary_rtfm_i3d_rgb: 0.7781
      secondary_mgfn_i3d_rgb: 0.7919  # CORRECTED from CONTEXT.md D-11's 0.8011 (which is VideoSwin, not I3D-RGB)
      our_ap: {GATE_AP}
      relative_to_rtfm: "{+X pp | -X pp}"
      relative_to_mgfn: "{+X pp | -X pp}"
    ---

    # Phase 4b Plan 05: RTFM XD-I3D Gate Empirical Run + ROADMAP/REQUIREMENTS Split

    **EVAL-01 {PASS | MISS-ACCEPTED}: AP {GATE_AP} on RTFM XD-I3D-RGB.** Gate threshold 0.7681 (77.81% - 1%). ROADMAP.md Phase 4b narrowed to RTFM gate per D-01; new Phase 4c detail block inserted for XD-Violence main results.

    ## Performance

    - **Duration:** ~{WALL_CLOCK} wall-clock (smoke {SMOKE_MIN}m + full gate {GATE_MIN}m + docs {DOCS_MIN}m{D12_RERUN: + rerun {RERUN_MIN}m})
    - **Tasks:** 5/5 (3 automated + 1 HUMAN-UAT + 1 docs)
    - **Commits:** {N} atomic commits across 5 plans + 1 final closeout commit

    ## Empirical Results (RTFM Gate)

    | Metric | Value | Anchor | Delta |
    |--------|-------|--------|-------|
    | Frame-level AP | {GATE_AP} | RTFM I3D-RGB 0.7781 | {DELTA} |
    | Frame-level AUC | {AUC} | - | - |
    | Snippet AUC | {SNIPPET_AUC} | - | - |
    | Video AUC | {VIDEO_AUC} | - | - |
    | n_videos | {N_VIDEOS} | 800 (xd_test) | {MATCH} |
    | n_frames | {N_FRAMES} | 2,330,384 (XDVioDet gt.npy) | {MATCH} |
    | positive_fraction | {POS_FRAC} | 0.2308 (gt.npy) | {MATCH} |

    **Gate disposition:** {PASS (within ±1% primary anchor) | MISS (shortfall {X}pp; fallback step {N} applied: {RATIONALE})}

    ## D-12 Diagnostic Cascade Results

    ### Check 1 — Bit-identical rerun (D-12)

    {IF PERFORMED:}
    - First run: AP = {AP1}, 9 numeric keys captured to `/tmp/gate_original_metrics.json`
    - Rerun after `rm -rf results/xd_i3d_rtfm_i3d_s42/`: AP = {AP2}
    - Diff: {all match | divergence in: {key}: orig={X} rerun={Y}}
    - Disposition: {PASS (bit-identical per Phase 3 SC #4) | FAIL (non-determinism regression — investigate `torch.use_deterministic_algorithms` + CUBLAS_WORKSPACE_CONFIG)}

    {IF NOT PERFORMED: "Skipped — gate PASS with no diagnostic triggers; D-12 rerun optional for PASS cases."}

    ### Check 2 — C4 sanity (snippet_auc vs auc delta)

    - auc = {AUC}
    - snippet_auc = {SNIPPET_AUC}
    - |delta| = {DELTA}
    - Threshold = 0.02
    - Disposition: {PASS | FAIL — large gap indicates snippet→frame broadcast bug in _build_frame_arrays or snippet_to_frame.py}

    ### Check 3 — 5-crop bag-size audit (D-12)

    - Audit line (from stderr on first step of first 3 epochs):
      ```
      {AUDIT_LINE}
      ```
    - Expected: `n_normal=15 n_abnormal=15 i3d_shape=(30, 32, 1024) mask_shape=(30, 32)`
    - Disposition: {PASS | FAIL — shape mismatch indicates collate_i3d_train or dataset return-shape regression}

    ## Anchor Correction (MGFN 80.11% → 79.19%)

    CONTEXT.md D-11 (line 42) wrote the secondary anchor as "MGFN 80.11%". RESEARCH.md Section "RTFM/MGFN Anchor Verification" (this phase, 2026-04-16) found that:
    - MGFN 80.11% is MGFN's **VideoSwin-RGB** result on XD-Violence (NOT vanilla I3D)
    - MGFN I3D-RGB is **79.19%** (RTFM 77.81 + MGFN's reported 1.38pp improvement over RTFM using the same I3D features)

    Our 1024-d I3D-RGB cache is NOT compatible with the 80.11% VideoSwin anchor. The correct I3D-RGB upper-bound anchor is **79.19%**.

    D-11 fallback cascade Step 1 (relax anchor if miss < 3pp): uses **79.19% MGFN I3D-RGB**, not 80.11%.

    ## Deferred to Phase 4c (unchanged from D-01)

    - XD-Violence main results table: 6 variants × seed=42 + 2 pooling ablations + 3-seed Gated Fusion + per-category Fighting/Abuse/Riot
    - XD re-extraction passes: `extract_ctrgcn.py --keep-persons`, `extract_clip.py --pool=mean`
    - 2 XD pooling YAMLs + 3 orchestrator queues (`phase4c_main`, `phase4c_pooling`, `phase4c_seeds`)
    - Activation: when `ls E:/features/xd/skeleton/*.npy | wc -l >= 4500` AND `ls E:/features/xd/clip/*.npy | wc -l >= 4500` (D-03 filesystem probe)

    ## Deviations from Plan

    {DOCUMENT any Rule 1/2/3/4 deviations surfaced during execution. Follow Phase 4 04-07-SUMMARY.md format.}

    ## Phase 4b Closeout Checklist

    - [x] xd_i3d training dispatch implemented (Plans 04b-02 + 04b-03)
    - [x] Wu annotation parser + data file committed (Plan 04b-01)
    - [x] _build_frame_arrays xd_i3d path rewritten (Plan 04b-04)
    - [x] 4 new pytest test files with 20 passing tests
    - [x] rtfm_gate queue executed, eval_metrics.json produced
    - [{x|  }] EVAL-01 gate: AP {GATE_AP} {PASS|MISS-ACCEPTED per fallback step {N}}
    - [x] D-12 diagnostic cascade completed
    - [x] ROADMAP.md Phase 4b narrowed + Phase 4c inserted
    - [x] REQUIREMENTS.md EVAL-01..EVAL-05 annotations flipped
    - [x] 04b-05-SUMMARY.md written
    ```

    Replace all `{PLACEHOLDER}` substrings with actual values from Task 2 output, Task 3 decision, and the Task 4 edits. Keep the structure verbatim.

    If the gate MISSED and a D-11 fallback was triggered, also create `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-UAT.md` documenting the fallback decision rationale in full (HUMAN-UAT artifact pattern mirroring 04-06-UAT.md).
  </action>
  <verify>
    <automated>test -f .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md && grep -q "EVAL-01" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md && grep -q "79.19" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md</automated>
  </verify>
  <acceptance_criteria>
    - `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` exists
    - SUMMARY has YAML frontmatter (verify: `head -1 .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` outputs `---`)
    - Gate AP value present (verify: `grep -qE "ap: [0-9]" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md`)
    - D-12 diagnostics section present: `grep -q "Check 1" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md && grep -q "Check 2" ... && grep -q "Check 3" ...`
    - Anchor correction documented: `grep -q "79.19" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` AND `grep -q "80.11" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` (both present because the correction is explained against the old value)
    - Phase 4c handoff section present: `grep -q "Phase 4c" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md`
    - If D-11 fallback was triggered: `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-UAT.md` also exists
    - All `{PLACEHOLDER}` substrings replaced with real values (NO literal `{PLACEHOLDER}` remaining): `grep -c "{.*}" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` outputs `0` OR the matches are all markdown-escape sequences (not planning-template placeholders)
  </acceptance_criteria>
  <done>04b-05-SUMMARY.md complete with gate AP, D-12 diagnostics, anchor correction (79.19% not 80.11%), Phase 4c handoff, and deviation log. Optional 04b-05-UAT.md if D-11 fallback triggered.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| `scripts/run_ablations.py` subprocess → training | Command line built from hardcoded RunSpec in QUEUES; no user-controlled strings |
| eval_metrics.json filesystem read → JSON parse | Standard `json.load`; trusted content produced by our own evaluation harness |
| ROADMAP.md + REQUIREMENTS.md edits | Documentation-only; no runtime impact; version-controlled |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-4b-15 | Tampering | Pre-existing stale results/xd_i3d_rtfm_i3d_s42/ directory | mitigate | Task 1 Step 1 does idempotent `rm -rf`; Pitfall 5 covered |
| T-4b-16 | Information Disclosure | config_snapshot.json contains resolved cfg | accept | cfg contains no secrets (wandb.mode=disabled; no API keys); paths are local filesystem references |
| T-4b-17 | Denial of Service | Gate queue runs 50 epochs = 10-20min wall-clock on RTX 4090 | accept | Bounded duration per RESEARCH.md compute budget; user can Ctrl+C to abort |
| T-4b-18 | Non-repudiation | Gate AP value + diagnostic provenance | mitigate | `config_snapshot.json` + `git_sha` + `checkpoint_sha` + `config_hash` all captured by existing Phase 3 D-13 machinery; SUMMARY records ap + delta + fallback decision + commit SHAs |

**Phase 4b Plan 05 security posture:** docs-only edits + pre-existing training/eval harness. No new attack surface.
</threat_model>

<verification>
## Per-Task Automated Verify
- Task 1 (smoke): `test ! -d results/smoke_xd_i3d_rtfm_i3d_s42/ && test ! -d results/xd_i3d_rtfm_i3d_s42/` exit 0 (both clean after step 4)
- Task 2 (gate): `test -f results/xd_i3d_rtfm_i3d_s42/.done && test -f results/xd_i3d_rtfm_i3d_s42/eval_metrics.json` exit 0
- Task 3 (HUMAN-UAT): resume-signal received and disposition recorded
- Task 4 (docs split): `grep -q "### Phase 4b: RTFM XD-I3D Gate" .planning/ROADMAP.md && grep -q "### Phase 4c: XD-Violence Main Results" .planning/ROADMAP.md` exit 0
- Task 5 (SUMMARY): `test -f .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md && grep -q "79.19" .planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` exit 0

## Plan-Level Gate (HUMAN-UAT covered)
- EVAL-01 gate disposition recorded (PASS, MISS-ACCEPTED per D-11 Step 1, or re-plan if upstream dispatch bug)
- D-12 diagnostic check 2 (C4 sanity) and check 3 (bag-size audit) both PASS OR are explicitly accepted in SUMMARY
- D-01 ROADMAP split applied: Phase 4b narrowed title, Phase 4c detail block present, EVAL-02..EVAL-05 XD-side flipped to Phase 4c
- 04b-05-SUMMARY.md contains: gate AP, 9 eval_metrics keys, D-12 results, anchor correction (79.19% not 80.11%), Phase 4c handoff, deviation log

## Decision Traceability
- D-01 (scope narrowing) — Task 4 executes the split
- D-03 (activation criterion for Phase 4c) — preserved verbatim in the new Phase 4c detail block
- D-11 (fallback cascade) — Task 3 decides; Task 5 documents
- D-12 (three orthogonal diagnostics) — Task 3 performs; Task 5 documents all 3
- D-14 (wandb Rule 3 fallback) — `--no-preflight` preserved; wandb.mode: disabled in rtfm_i3d.yaml
- D-15 (keep rtfm_gate queue name as-is) — Task 2 uses the existing queue unchanged
- D-16 (1-epoch smoke before gate) — Task 1 performs
- Pitfall 5 (clean state before run) — Task 1 Step 1 + Step 4 idempotent cleanup
- Anchor correction (MGFN 80.11% → 79.19%) — Task 5 SUMMARY documents + Task 4 ROADMAP SC #1 mentions
</verification>

<success_criteria>
- `results/xd_i3d_rtfm_i3d_s42/.done` exists with full eval artifacts
- `eval_metrics.json` contains `ap` and it is either:
  - `>= 0.7681` (PASS) OR
  - `< 0.7681` with documented D-11 fallback disposition in SUMMARY + UAT
- D-12 Check 2 (C4 sanity): `|auc - snippet_auc| < 0.02` OR fallback
- D-12 Check 3 (bag-size audit): `[i3d_audit]` line shows correct shapes
- D-12 Check 1 (bit-identical rerun): performed on gate MISS, optional on PASS
- `.planning/ROADMAP.md`: Phase 4b title narrowed; Phase 4c detail block inserted; Progress Table + Requirement Coverage updated; Phase 5/6 untouched
- `.planning/REQUIREMENTS.md`: EVAL-01 closed (or MISS-accepted); EVAL-02..EVAL-05 XD-side flipped to Phase 4c
- `04b-05-SUMMARY.md` contains gate AP, 9 numeric keys, D-12 diagnostics, anchor correction (79.19%), Phase 4c handoff
- Full test suite still green: `pytest tests/ -x --ignore=tests/test_ctrgcn_smoke.py --tb=short` exit 0
- All changes committed atomically (1 commit for docs edits, 1 commit for SUMMARY; optional 1 commit for UAT if D-11 fallback)
</success_criteria>

<output>
After completion of Tasks 1-5, the `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-SUMMARY.md` IS the phase closeout artifact. It mirrors `.planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md` in structure.

If D-11 fallback is triggered (gate miss), ALSO create `.planning/phases/04b-xd-violence-main-results-rtfm-xd-i3d-gate/04b-05-UAT.md` with the fallback-decision text, mirroring 04-06-UAT.md's structure.

No other output files are required — STATE.md updates are handled by the execute-phase orchestrator.
</output>
</content>
</invoke>