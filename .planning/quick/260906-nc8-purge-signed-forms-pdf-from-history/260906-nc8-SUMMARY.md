---
phase: quick-260906-nc8
status: complete
completed: 2026-09-06
---

# Quick 260906-nc8: Purge signed forms PDF from history — SUMMARY

## What happened

`thesis/frontmatter/signed_forms.pdf` (signed 推薦書/審定書 committee scans, 1.7MB) was stripped from the entire git history with `git filter-repo --invert-paths` and the rewritten history force-pushed, completing the privacy purge started 2026-08-31 (which had removed only the root copy `審定書和推薦書.pdf` per the user's then root-only scope choice — acceptable while the repo was private, not for publication). Trigger: the repo was flipped public on 2026-09-01 for the Zenodo/GitHub reproducibility archive with the file still tracked; it was flipped back to private within minutes and stayed private until this purge landed.

## Changes

1. **LaTeX fallback** — `approval.tex`/`recommendation.tex` wrap their `\includepdf` in `\IfFileExists{frontmatter/signed_forms.pdf}`: local builds (file on disk, gitignored) embed the signed scans; public clones compile the pre-260804 unsigned placeholder pages. Both paths verified with `build_thesis.ps1 -Clean`: 0 errors / 0 undefined refs each.
2. **Gitignore** — `thesis/frontmatter/signed_forms.pdf` added to the personal-documents section; local copy kept on disk (plus backup of the source scan at repo root, also gitignored).
3. **History rewrite** — `git filter-repo` over 586 commits; 17 commits from 2026-08-04 onward re-SHA'd (commit-map: 3333028→fec05f5, bc98dc8→58acba7, e0afb1f→83e74bc, tip 1024077→52789a0, …). Zero objects matching `signed_forms` remain under any ref (codex checkpoint refs included). Force-pushed; `gh api` confirms the path 404s on origin/main.
4. **Doc SHA refresh** — stale references to the 17 old SHAs in STATE.md and three prior quick-task docs updated via the commit-map (same convention as the 08-31 rewrite). First sed pass ingested the commit-map header line ("old new") and mangled words containing "old" (placeholder→placehnewer); caught by diff review, reverted, redone with a hex-only filter.
5. **Housekeeping** — stale clean worktree `D:/ViolenceCC_rerun_wt` (detached at July docs commit, 0 dirty files) removed; filter-repo requires sole-worktree operation.
6. **Repo visibility** — set back to PUBLIC after the purge (prerequisite for Zenodo's GitHub integration).

## Residual risk (accepted)

GitHub retains unreachable objects until server-side gc: the old commit is still addressable by its full 40-char SHA (`3333028ab95b…`), which is unguessable and now referenced nowhere in the repo (short-SHA lookups 422). Exposure window while public was minutes, repo had no forks/watchers. Optional belt-and-braces: ask GitHub Support to run gc on the repo.

## Verification

- `git rev-list --objects --all | grep -i signed_forms` → empty (local, post-rewrite)
- `gh api repos/austinjeng/ViolenceCC/contents/thesis/frontmatter/signed_forms.pdf` → 404
- Thesis builds clean both with and without the PDF present; final local build embeds signed scans
- Working tree clean except deliberate `?? outputs/regrid_so400m_xd/`

## Deviation from workflow

Executed in the main session context instead of a worktree-isolated gsd-executor: filter-repo rewrites every ref, aborts on extra worktrees, and a force push of rewritten history warrants direct step-by-step verification. Sequential main-tree execution is the workflow-sanctioned fallback.
