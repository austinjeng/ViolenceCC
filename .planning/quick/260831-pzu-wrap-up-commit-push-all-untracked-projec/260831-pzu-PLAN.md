---
phase: quick-260831-pzu
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .gitignore
  - .planning/config.json (stage existing diff)
  - "git index/history: all untracked project artifacts classified COMMIT (see Task 2)"
autonomous: true
requirements: [QUICK-260831-PZU]

must_haves:
  truths:
    - "All COMMIT-classified untracked files are committed and pushed to origin/main"
    - "outputs/regrid_so400m_xd/ remains untracked AND un-ignored (still visible as ?? in git status)"
    - ".playwright-cli/, .qa_tmp/, .pytest_tmp/ no longer appear in git status and the pytest_tmp permission warning is gone"
    - "Branch main is 0 commits ahead of origin/main after push (the 10 waiting commits plus the 2 new ones are published)"
  artifacts:
    - path: ".gitignore"
      provides: "Ignore entries for .playwright-cli/, .qa_tmp/, .pytest_tmp/"
      contains: ".playwright-cli/"
  key_links:
    - from: "git staging area"
      to: "outputs/regrid_so400m_xd/"
      via: "explicit unstage + zero-match gate before commit"
      pattern: "git diff --cached --name-only | grep -c regrid_so400m_xd == 0"
---

<objective>
Wrap-up commit: publish all untracked project artifacts (~20MB) to the private GitHub repo, gitignore three temp/tool dirs, and push — while guaranteeing the 303MB `outputs/regrid_so400m_xd/` checkpoint dir is neither committed nor gitignored (user will decide its fate later; it must stay visibly untracked).

Purpose: This machine has no other backup. The repo is 10 commits ahead of origin and carries months of unpushed research artifacts (TTA experiment scripts, defense materials, signed committee forms, review reports).
Output: Two commits on `main`, pushed; working tree clean except `?? outputs/regrid_so400m_xd/`.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
Orchestrator survey results (authoritative — do NOT re-survey sizes):

- Repo: austinjeng/ViolenceCC, PRIVATE, branch `main`, 10 commits ahead of origin/main.
- Modified tracked file: `.planning/config.json` (trailing-newline-only diff) — include in the artifacts commit.
- COMMIT (small, ~20MB total):
  - `.planning/_review_code_paper_match.mjs`
  - `scripts/_check_citations.py`, `scripts/_run_tta_backbone_batch.py`, 19× `scripts/_tmp_*.py`
  - `pipeline-docs.html`, `review-2026-06-22.html`
  - `thesis/thesis_requirements.pdf`
  - `審定書和推薦書.pdf` (repo root; signed committee forms — repo is PRIVATE, cleared for commit)
  - `CGW2026_Latex_Paper_Template/` (9 files)
  - `output/` (one defense transcript PDF)
  - `presentation_codex/` (CGW talk PPTX + zh-TW transcript)
  - `outputs/` EXCEPT `outputs/regrid_so400m_xd/`: `outputs/defense_visuals/`, `outputs/thesis_defense_2026-07-21_zh-TW.pptx`, `outputs/thesis_defense_2026-07-21_zh-TW.BACKUP-pre-polish-260720.pptx`, `outputs/口試白話總複習.pdf`, `outputs/deck_fix_plan_2026-07-20.md`
- DEFER (do NOT commit, do NOT gitignore): `outputs/regrid_so400m_xd/` (303MB, ~100 .pth checkpoints). Must remain `??` in git status.
- GITIGNORE: `.playwright-cli/`, `.qa_tmp/`, `.pytest_tmp/` (the last is permission-denied and makes git emit a warning on every command).
- `.gitignore` currently ends with the thesis LaTeX artifact block (`thesis/*.lot` on the final line); append the new block after it.
- Per repo policy: NEVER commit LaTeX build artifacts (`paper/main.pdf`, `thesis/main.pdf`, `*.aux` etc.) — they are already gitignored; do not force-add anything.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Gitignore temp dirs and commit</name>
  <files>.gitignore</files>
  <action>
    Append a new block to the end of `.gitignore` (after the existing `thesis/*.lot` line), matching the file's existing comment style:

    a comment line "# Tool/QA temp dirs (quick 260831-pzu)" followed by three entries: `.playwright-cli/`, `.qa_tmp/`, `.pytest_tmp/`.

    Use the Edit tool (not heredoc). Then commit only this file:
    `git add .gitignore` and commit with subject `chore: gitignore playwright/qa/pytest temp dirs` (46 chars). Use one `-m` for the subject and a second `-m` containing BOTH trailer lines in a single quoted multi-line string (a blank line between them would break the trailer block):
    Co-Authored-By: Claude Fable 5 &lt;noreply@anthropic.com&gt;
    Claude-Session: https://claude.ai/code/session_01XQWLfBg5eNB9by6TZYmy6H
  </action>
  <verify>
    <automated>git status 2>&1 | grep -cE 'playwright-cli|qa_tmp|pytest_tmp'</automated>
  </verify>
  <done>Output is 0 (dirs gone from status AND the pytest_tmp permission warning on stderr is silenced). `git log -1 --format=%s` prints the gitignore subject.</done>
</task>

<task type="auto">
  <name>Task 2: Stage and commit all artifacts, fail-safe excluding regrid checkpoints</name>
  <files>.planning/config.json, .planning/_review_code_paper_match.mjs, scripts/_check_citations.py, scripts/_run_tta_backbone_batch.py, scripts/_tmp_*.py, pipeline-docs.html, review-2026-06-22.html, thesis/thesis_requirements.pdf, 審定書和推薦書.pdf, CGW2026_Latex_Paper_Template/, output/, presentation_codex/, outputs/ (minus regrid_so400m_xd)</files>
  <action>
    Stage in Git Bash with explicit paths (quote the CJK filename):

    1. `git add .planning/config.json .planning/_review_code_paper_match.mjs`
    2. `git add scripts/_check_citations.py scripts/_run_tta_backbone_batch.py scripts/_tmp_*.py`
    3. `git add pipeline-docs.html review-2026-06-22.html thesis/thesis_requirements.pdf "審定書和推薦書.pdf"`
    4. `git add CGW2026_Latex_Paper_Template/ output/ presentation_codex/`
    5. `git add outputs/` then immediately `git reset outputs/regrid_so400m_xd` (fail-safe pair — never commit between these two commands).

    If step 4 emits an "adding embedded git repository" warning for CGW2026_Latex_Paper_Template, STOP: remove the nested `.git` dir inside it, `git rm --cached CGW2026_Latex_Paper_Template`, and re-add so real files (not a gitlink) are staged.

    GATE before committing (both must pass, else `git reset` and re-stage):
    - `git diff --cached --name-only | grep -c regrid_so400m_xd` → must be 0 (grep exits 1 on zero matches; that IS the pass condition)
    - `git status --porcelain | grep '^??'` → only remaining untracked line is `outputs/regrid_so400m_xd/`

    Commit with subject `chore: add thesis and defense wrap-up files` (42 chars), same two-trailer `-m` pattern as Task 1.
  </action>
  <verify>
    <automated>git show --stat --format= HEAD | grep -c regrid_so400m_xd; git status --porcelain</automated>
  </verify>
  <done>HEAD commit contains 0 regrid paths but does contain the scripts, PDFs, template, output/, outputs/ defense files, and presentation_codex/. `git status --porcelain` shows exactly one line: `?? outputs/regrid_so400m_xd/`.</done>
</task>

<task type="auto">
  <name>Task 3: Push and verify remote sync</name>
  <files>(none — remote operation)</files>
  <action>
    `git push` (publishes the 10 pre-existing waiting commits plus the 2 new ones). If push is rejected for auth, surface the exact error to the user rather than changing remotes or credentials. Do NOT use `--force` under any circumstances.
  </action>
  <verify>
    <automated>git status -sb | head -1; git log origin/main..main --oneline | wc -l</automated>
  </verify>
  <done>First line is `## main...origin/main` with no `[ahead N]` marker; ahead-count command prints 0; only untracked path remaining is `outputs/regrid_so400m_xd/`.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| local repo → GitHub (private) | Pushing research artifacts including signed committee PDFs |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-q260831-01 | Information Disclosure | 審定書和推薦書.pdf, thesis_requirements.pdf | accept | Repo verified PRIVATE by orchestrator; signed forms already embedded in tracked thesis/frontmatter/signed_forms.pdf since commit fec05f5 |
| T-q260831-02 | Denial of Service (repo bloat) | outputs/regrid_so400m_xd/ (303MB) | mitigate | Explicit unstage + zero-match `grep -c regrid_so400m_xd` gate before commit (Task 2) |
| T-q260831-03 | Tampering (history loss) | git push | mitigate | Plain `git push` only; `--force` explicitly forbidden in Task 3 |
</threat_model>

<verification>
- `git status` clean except `?? outputs/regrid_so400m_xd/`; no pytest_tmp warning on any git command
- `git log origin/main..main` empty (everything pushed)
- `git show --stat HEAD` and `HEAD~1` contain no regrid paths and no LaTeX build artifacts (main.pdf/*.aux)
</verification>

<success_criteria>
- Two new commits on main (gitignore + artifacts), both with Conventional Commit subjects ≤50 chars and the Claude co-author trailer
- All 12 commits (10 waiting + 2 new) published to origin/main
- outputs/regrid_so400m_xd/ untracked, un-ignored, unmodified
- .playwright-cli/, .qa_tmp/, .pytest_tmp/ ignored
</success_criteria>

<output>
Create `.planning/quick/260831-pzu-wrap-up-commit-push-all-untracked-projec/260831-pzu-SUMMARY.md` when done
</output>
