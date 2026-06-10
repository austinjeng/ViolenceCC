---
quick_id: 260610-qfy
status: in-progress
date: 2026-06-10
---

# Quick Task 260610-qfy: REVIEW §4 LOW items + PRI progress checklist

## Part 1 — PRI checklist (DONE this commit)
Added a `[ ]`/`[x]`/`[~]` "Progress tracker" to REVIEW-2026-06-10.md §5 covering all 18 Pri
items + SKIP tier, so every improvement idea is trackable like the P/C/LOW findings.
Marked done: Pri 1, 5, 6, 7, 9. Deferred-noted: Pri 3 (headline-changing). SKIP → `[~]`.

## Part 2 — §4 LOW items (16, via workflow wf_8c1ece10-307, 4 file-groups)
Grouped by non-overlapping files to parallelize safely:
- **A (paper main.tex):** P1 define d_v(=2d); P2 define GF 2-Person / GF Mean-Only; P3 trainable
  set incl. MIL head; P4 disclose Table-3 snippet-grid protocol; P5 "per-condition" reword.
- **B (TTA code):** T8 SAR-fidelity comment-only; T9 harden episodic optimizer-state reset;
  T10 assert-keys on strict=False loads; T11 fix dup-method log line.
- **C1 (infra-fix):** I6 fix Fig-5 retracted-bound docstring (+verify bars); I12 guard
  tables_generated.tex stale banner; I13 wire backbone field into TTA CSV rows.
- **C2 (document/accept, behavior-frozen):** D7 off-by-one comment; D14 iterdir-ordering comment
  (NO sort); D15 warn-log for unknown kwargs (must not break replay); D16 hardcoded-paths comment.

Already done in Batch B (260610-b6p): the 4 "test suite RED" LOW inventory items → `[x]`.

## Verify
After workflow: `build_paper.ps1 -Clean` (Group A) + full `pytest` (Groups B/C) green;
mark each §4 LOW `[x]` (fixed) / `[~]` (documented-accept); commit.
