---
phase: 04-baseline-evaluation-main-results
plan: 07
subsystem: planning-docs
tags: [roadmap, requirements, phase-closeout, scope-carveout, option-b]

# Dependency graph
requires:
  - phase: 04-baseline-evaluation-main-results
    provides: "Phase 4 UCF empirical work + Option B DECISION (04-06)"
  - phase: 04-baseline-evaluation-main-results
    provides: "04-CONTEXT.md D-01 (UCF-only), D-02 (XD out-of-band), D-03 (RTFM anchor retarget), D-25 (XD pooling to 4b)"
provides:
  - "ROADMAP.md Phase 4 closed as 7/7 Complete (2026-04-16)"
  - "ROADMAP.md Phase 4b scope expanded to cover XD main results AND EVAL-01 RTFM XD-I3D gate + xd_i3d training dispatch work"
  - "REQUIREMENTS.md EVAL-02..EVAL-05 marked complete (UCF side); EVAL-01 remains at Phase 4b with expanded remediation notes"
  - "Restart point for /gsd-plan-phase 4b: XD features OR i3d-only RTFM work as prioritizable sub-tracks"
affects: [04b XD main results + RTFM gate, 05 TTA adaptation handoff, 06 thesis writeup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Scope carveout pattern: when Rule 4 architectural gap surfaces mid-execution, the next-phase detail block absorbs the work instead of blocking the current phase"
    - "Half-step phase numbering (4b): preserves main-phase counter stability while representing a deferred dataset-dimension expansion"
    - "Rescoped-from / Deferred-from dual-bucket headings in phase entry: makes scope provenance traceable"

key-files:
  created:
    - .planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "D-01 (UCF-only Phase 4) preserved as written; Phase 4 closes UCF-only as planned"
  - "D-02 (XD out-of-band) preserved; Phase 4b activation remains gated on XD feature filesystem signal"
  - "D-03 (RTFM XD-I3D retarget) preserved architecturally but EMPIRICALLY FALSIFIED in Plan 04-06: Plan 04-03 did not wire the xd_i3d training dispatch claimed by D-36, so the RTFM gate work moves to Phase 4b"
  - "D-25 (XD pooling to 4b) preserved; both XD re-extraction passes remain Phase 4b scope"
  - "Option B scope expansion (2026-04-15): Phase 4b now owns BOTH original XD main results scope AND the Phase 4 RTFM gate remediation work — the xd_i3d training dispatch prerequisite is documented as a named sub-deliverable"

patterns-established:
  - "Phase 4b detail block structure: Goal / Depends on / Activation criterion / Requirements / Success Criteria / Deferred from Phase 4 / Rescoped from Phase 4 via Option B / Plans — the last two subsections are new and surface both carve-out reasons explicitly"
  - "REQUIREMENTS.md traceability entries can carry a multi-phase dataset-split annotation ('Phase 4 (UCF), Phase 4b (XD)') when a single requirement is demonstrated across datasets in sequential phases"

requirements-completed: []  # No new requirements closed by this doc-only plan; EVAL status annotations updated to reflect Phase 4 empirical closure but the canonical completion signal for each is still in Plan 04-06

# Metrics
duration: ~4m (wall-clock; docs-only atomic edit)
completed: 2026-04-16
---

# Phase 4 Plan 07: Phase 4 Close + Expanded Phase 4b Carveout Summary

**ROADMAP.md updated: Phase 4 marked 7/7 Complete (2026-04-16, UCF-only per D-01); Phase 4b scope expanded to cover XD-Violence main results AND the rescoped EVAL-01 RTFM XD-I3D gate + xd_i3d training dispatch work per 2026-04-15 Option B decision.**

## Performance

- **Duration:** ~4 minutes (wall-clock; docs-only atomic edit of 2 planning files)
- **Started:** 2026-04-15T19:20:54Z
- **Completed:** 2026-04-16 (worktree timestamp)
- **Tasks:** 1 of 1
- **Files modified:** 2 tracked files (ROADMAP.md, REQUIREMENTS.md) + 1 created (this SUMMARY)

## Accomplishments

- **Phase 4 formally closed** in ROADMAP.md: top-of-file bullet marked `[x]`, detail block's `Plans:` line reads `7/7 plans complete (2026-04-16)`, Progress Table row reads `7/7 | Complete | 2026-04-16`.
- **Phase 4b scope expanded** per 2026-04-15 Option B decision: the Phase 4b detail block now covers BOTH:
  1. **Original scope** (D-01, D-02, D-25): XD-Violence main results — Gated Fusion AP, 6-variant ablation table, 3-seed stability, per-category Fighting+Abuse+Riot breakdown; deferred XD re-extraction passes; deferred XD ablation orchestration queue.
  2. **Rescoped from Phase 4** (Option B): EVAL-01 RTFM XD-I3D gate + the prerequisite xd_i3d training dispatch implementation (`build_dataloaders_i3d`, `train_one_epoch_i3d`, `validate_i3d`, Wu et al. XD-Violence annotation parser in `src/evaluate.py::_build_frame_arrays`).
- **Phase 4b success criteria** now include 5 items (up from 4): SC #1 is the RTFM AP +/-1% gate (inherited from Phase 4 SC #1), SC #2-5 are the XD-mirror of Phase 4's UCF success criteria.
- **Activation criterion clarified**: XD skeleton+CLIP feature population remains the main-phase activator, but the RTFM gate sub-track can start immediately since `E:/i3d-features/i3d-features/` already exists — this was added as an explicit parenthetical note to the Phase 4b detail block.
- **Phase 4 detail block's Success Criteria annotated** with empirical verdicts (PASS / MISS-documented / DEFERRED) to preserve traceability once Phase 4 is no longer in the active window.
- **Progress Table row for Phase 4b expanded** to read "XD-Violence Main Results + RTFM XD-I3D Gate" with a parenthetical status note that the RTFM sub-track can start ahead of XD features.
- **REQUIREMENTS.md top-of-file checkboxes updated** for EVAL-02..EVAL-05 (now `[x]` with UCF-complete / XD-pending annotations) and EVAL-01 annotation expanded to name the Phase 4b prerequisite work.
- **REQUIREMENTS.md traceability table** rewritten for EVAL-01..EVAL-05 rows to show dual-phase dataset-split annotations (`Phase 4 (UCF), Phase 4b (XD)`) and explicit remediation prerequisite list for EVAL-01.
- **Phase 4b Plans line** reads `TBD (plan once XD features land OR prioritize the xd_i3d dispatch + RTFM gate ahead of XD main results since i3d features are already on disk)` — leaves the restart decision to the next `/gsd-plan-phase 4b` invocation.

## Task Commits

1. **Task 1: ROADMAP + REQUIREMENTS atomic update** — `dd2836e` (docs)

**Plan metadata:** this SUMMARY + state updates will be committed as the final plan close.

## Files Created/Modified

- `.planning/ROADMAP.md` — 4 edits in one commit:
  1. Phase 4 bullet at top: `[ ]` -> `[x]` + description shortened + RTFM deferral called out
  2. New Phase 4b bullet inserted between Phase 4 and Phase 5 bullets at top of file
  3. Phase 4 detail block: `Requirements` list EVAL-02..EVAL-05 (EVAL-01 removed, noted as rescoped); SC #1 struck through with DEFERRED annotation; SC #2-5 annotated with empirical verdicts; `Plans:` line 7/7; Plan 04-03 line notes the discovered dispatch gap; Plan 04-06 line notes RTFM gate deferral; Plan 04-07 line checked and updated
  4. Phase 4b detail block: header expanded to "XD-Violence Main Results + RTFM XD-I3D Gate"; Goal split into two numbered items (XD main + Option B RTFM rescope); Depends-on line mentions deferred scope; Activation criterion clarified with i3d-early-start note; Requirements line expanded to EVAL-01..EVAL-05 with rescope rationale; Success Criteria expanded from 4 to 5 items (SC #1 = RTFM gate); new "Rescoped from Phase 4 via Option B" subsection with 5 named prerequisites; Plans line updated to mention dual-priority starting option
  5. Progress Table: Phase 4 row updated to `7/7 | Complete | 2026-04-16`; Phase 4b row label expanded and status note added
  6. Footer `Last updated` line refreshed to 2026-04-16 with closeout context

- `.planning/REQUIREMENTS.md` — 3 edits in one commit:
  1. EVAL-01..EVAL-05 top-of-file checkbox list: EVAL-01 `[ ]` with expanded deferral annotation (lists xd_i3d dispatch prerequisite); EVAL-02..EVAL-05 marked `[x]` with UCF-complete / XD-pending annotations
  2. Traceability table rows for EVAL-01..EVAL-05: EVAL-01 Phase column stays `Phase 4b`, status column expanded; EVAL-02..EVAL-05 Phase column changed from `Phase 4` to `Phase 4 (UCF), Phase 4b (XD)`, status column updated with empirical numbers
  3. Footer `Last updated` line refreshed to 2026-04-16 with closeout context

- `.planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md` — this file (created).

## Decisions Preserved / Validated / Updated

| Decision | Source | Status After This Plan |
|---|---|---|
| D-01 (UCF-only Phase 4) | 04-CONTEXT.md | UPHELD — Phase 4 closes UCF-only as planned; 8 UCF rows produced by 04-06 |
| D-02 (XD out-of-band) | 04-CONTEXT.md | UPHELD — Phase 4b activation remains gated on XD feature signal |
| D-03 (RTFM XD-I3D anchor) | 04-CONTEXT.md | UPHELD architecturally but EMPIRICALLY FALSIFIED for Phase 4 execution — the anchor choice is still correct for the thesis narrative; Plan 04-03 did not wire the training dispatch; Phase 4b owns the integration |
| D-25 (XD pooling to 4b) | 04-CONTEXT.md | UPHELD — XD pooling re-extraction remains Phase 4b scope |
| D-36 (xd_i3d dispatch in Plan 04-03) | 04-CONTEXT.md | FALSIFIED (by 04-06 Task 2 empirical evidence); Phase 4b must re-implement |
| Option B (2026-04-15 DECISION) | 04-06-UAT.md | FIRST-CLASS in ROADMAP — Phase 4b detail block now names the rescoped work explicitly |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Plan 04-07 as originally written did not cover the 2026-04-15 Option B scope expansion**
- **Found during:** Task 1 (initial reading of the plan vs the update_context instruction in the prompt)
- **Issue:** Plan 04-07 was written BEFORE the 04-06 execution surfaced the Rule 4 architectural gap in Plan 04-03. The plan's Phase 4b scope lists only EVAL-02..EVAL-05 and explicitly writes "EVAL-01 RTFM gate already closed in Phase 4 per D-03" — which is no longer true after the Option B decision. The planner's Step C says "Do NOT modify REQUIREMENTS.md" and "If the grep check fails... align the table but do not add Phase 4b rows" — but REQUIREMENTS.md has ALREADY been modified by commit `10d95a3` (EVAL-01 moved to Phase 4b) prior to this plan's execution. The prompt's `<update_context>` block explicitly overrides the plan's original intent with "Your Phase 4b roadmap entry must therefore cover: (1) Original scope... (2) NEW scope from Option B".
- **Fix:** Expanded the Phase 4b detail block to include both buckets (Original + Rescoped from Phase 4 via Option B), added SC #1 (RTFM gate) back as Phase 4b's first success criterion, listed the 5 named prerequisite deliverables (build_dataloaders_i3d, train_one_epoch_i3d, validate_i3d, Wu et al. parser, RTFM rerun command). Also annotated Phase 4 detail block SC #1 with strike-through + DEFERRED, and annotated SC #2-5 with PASS/MISS verdicts to preserve audit trail.
- **Files modified:** .planning/ROADMAP.md (Phase 4 bullet + Phase 4b bullet + Phase 4 detail block + Phase 4b detail block + Progress Table + footer), .planning/REQUIREMENTS.md (EVAL-01..EVAL-05 checkboxes + traceability rows + footer).
- **Scope check:** Phase 5 and Phase 6 detail blocks are unmodified (verified by `grep '### Phase 5: TTA Infrastructure'` and `grep '### Phase 6: Analysis'`). Phase 5/6 bullets at top of file also unmodified. Plans 04-01..04-06 checkbox states unchanged; only Plan 04-07 flipped to `[x]` and Plan 04-06 line amended to note the RTFM deferral.
- **Committed in:** `dd2836e` (Task 1 single atomic commit).

### No Rule 4 (Architectural) deviations

This plan is docs-only; no architectural decisions were needed.

---

**Total deviations:** 1 auto-fixed (Rule 2 — missing critical functionality: Plan 04-07 needed to reflect the Option B decision that happened AFTER the plan was authored but BEFORE it was executed; the prompt's update_context block authorized this expansion).
**Impact on plan:** The Rule 2 fix transformed a "thin carveout" docs plan into a "full Option B scope expansion" docs plan. The underlying intent (close Phase 4, create Phase 4b restart point) is preserved; the scope of what Phase 4b owns is expanded to match the 2026-04-15 researcher decision.

## Issues Encountered

- **Plan wording vs post-plan-authoring decisions:** the plan was authored before 04-06 executed, so its Step C instruction "Do NOT modify REQUIREMENTS.md" conflicts with the fact that REQUIREMENTS.md had already been modified between plan authoring and plan execution (commit `10d95a3` moved EVAL-01 to Phase 4b as part of the 04-06 Option B handling). The prompt's explicit `<update_context>` block resolved this by overriding the plan's original intent. No downstream impact.
- **Phase bullet list at top of file:** the plan's Step B Edit 1 expected the Phase 4b bullet to be added for the first time, but a Phase 4b bullet already existed in ROADMAP.md (added during planning). The execution path became "update the existing bullet" instead of "insert a new bullet". Functional outcome is identical.
- **Phase 4b detail block:** similarly already existed in skeletal form (Phase 4b created during Phase 4 planning per D-01) with only XD scope. The execution path became "expand the existing detail block" to add the Option B scope. Functional outcome is identical; the text now covers both scope buckets explicitly.

## User Setup Required

None — documentation-only plan; no external service configuration required.

## Open Issues / Phase 4b Backlog (unchanged from 04-06 SUMMARY)

1. **EVAL-01 RTFM XD-I3D gate** — Phase 4b must implement `build_dataloaders_i3d` + `train_one_epoch_i3d` + `validate_i3d` dispatch + Wu et al. annotation parser before the RTFM gate can be re-executed (re-run command: `scripts/run_ablations.py --queue rtfm_gate`).
2. **SC #2 remediation** — 0.73 pp gap to 83% UCF AUC target. Options: (a) accept at 0.8227 with per-category strong signal as thesis justification, (b) Phase 5 TTA + threshold calibration, (c) Phase 4b architectural sweeps (LayerNorm D-07, shared_dim), (d) Late Fusion learned-alpha D-08 rerun.
3. **Optional clip_mean 3-seed rerun** — at D-29 0.5% threshold; researcher discretion.
4. **XD-Violence main results** — Phase 4b scope per D-01 + D-02 + D-25 once XD skeleton + CLIP extraction completes.
5. **Late Fusion inversion disposition** — treat as empirical justification for Gated Fusion superiority in thesis writeup, OR run `alpha: learned` reruns in Phase 4b.

## Next Phase Readiness

- **Phase 4 is fully closed.** 7/7 plans complete; 8 UCF empirical rows produced; RTFM gate DEFERRED to Phase 4b (documented in ROADMAP + REQUIREMENTS).
- **Phase 5 (TTA) is ready to plan.** Canonical adaptation base `results/ucf_gated_fusion_s42/best_model.pth` is bit-identical-rerun verified and locked. Phase 4b does NOT block Phase 5 — the two phases can run in parallel once XD features land.
- **Phase 4b is ready to plan with two sub-track priority options:**
  1. **Start the xd_i3d / RTFM gate sub-track immediately** (i3d features already on `E:/i3d-features/i3d-features/`); estimated 1-2 days of TDD for the training dispatch + parser + re-run.
  2. **Wait for XD skeleton+CLIP features** and do the main XD results work first (scope matches Phase 4 UCF work with the dataset key swapped).
  3. **Interleave** — implement the xd_i3d dispatch in parallel with the XD feature extraction wait, re-run the RTFM gate, then pivot to the XD main results queue when features land.

## Handoff

- **To `/gsd-plan-phase 5`** (TTA): canonical Phase 5 adaptation base is `results/ucf_gated_fusion_s42/best_model.pth`. Phase 5 context gathering is unblocked.
- **To `/gsd-plan-phase 4b`** (when activated): Phase 4b detail block in ROADMAP.md contains the full scope + 5 explicit prerequisite deliverables for the xd_i3d RTFM gate sub-track + 4 deferred XD main results sub-tracks.
- **To thesis writeup:** Phase 4 UCF results (8 rows + 3-seed stability + per-category breakdown) are captured in 04-06-SUMMARY.md's Empirical Results section; per-category Fighting/Assault dominance is the strongest violence-specific result to lead with.

---
*Phase: 04-baseline-evaluation-main-results*
*Completed: 2026-04-16*

## Self-Check: PASSED

- FOUND: .planning/ROADMAP.md (Phase 4b detail block expanded per Option B, Phase 4 marked 7/7 Complete, Progress Table updated)
- FOUND: .planning/REQUIREMENTS.md (EVAL-01 rescoped language + EVAL-02..EVAL-05 marked complete with dual-dataset annotations)
- FOUND: .planning/phases/04-baseline-evaluation-main-results/04-07-SUMMARY.md (this file)
- FOUND: commit dd2836e (Task 1 atomic ROADMAP + REQUIREMENTS commit)
- VERIFIED: all 9 plan acceptance criteria pass
- VERIFIED: 7 `### Phase` detail blocks exist in correct order (Phase 1 -> 2 -> 3 -> 4 -> 4b -> 5 -> 6)
- VERIFIED: Phase 5 and Phase 6 detail blocks unmodified (scope-guard grep checks pass)
