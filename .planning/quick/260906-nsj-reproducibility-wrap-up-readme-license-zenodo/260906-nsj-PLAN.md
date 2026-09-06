---
phase: quick-260906-nsj
plan: 01
type: execute
wave: 1
depends_on: [quick-260906-nc8]
files_modified:
  - README.md (new)
  - LICENSE (new)
  - "git tag v1.0-thesis + GitHub release"
  - "Zenodo record (external): feature caches + snippet boundaries + headline checkpoints + CTR-GCN weights"
autonomous: true
requirements: [QUICK-260906-NSJ]

must_haves:
  truths:
    - "Root README.md documents two-tier reproduction: Tier 1 (Zenodo caches + checkpoints -> eval/retrain, hours) and Tier 2 (raw videos -> full 3-env extraction pipeline, days)"
    - "README states the headline numbers with their provenance-pinned configs: UCF 82.5±0.4 AUC (gated_fusion_giant s42/123/2024), XD 78.7±0.9 AP (gated_fusion_so400m s42/123/2024)"
    - "README documents the E:/features + E:/snippets path convention configs hardcode, and how cloners remap it"
    - "LICENSE is MIT, copyright Wei-Han Jeng"
    - "Zenodo record holds ucf/xd feature tars (~16GB), snippet boundaries, 6 headline best_model.pth+config+metrics, CTR-GCN NTU120 2D weights; DOI pre-reserved and cited in README"
    - "Tag v1.0-thesis + GitHub release exist on the post-purge history"
  artifacts:
    - path: "README.md"
      provides: "Entry point: results, setup, data acquisition, reproduction tiers, citation, DOI badge"
      contains: "zenodo"
    - path: "LICENSE"
      provides: "MIT license"
      contains: "MIT License"
  key_links:
    - from: "README.md"
      to: "envs/SETUP.md"
      via: "environment setup section links, no duplication"
      pattern: "envs/SETUP.md"
---

<objective>
Make the now-public repo reproducible by a stranger: root README (none existed), MIT LICENSE, v1.0-thesis tag + GitHub release, and a Zenodo record carrying the artifacts that are not in git — feature caches (E:/features, 16GB, incl. corruption variants), snippet boundaries (E:/snippets, 28MB), the 6 headline checkpoints, and the CTR-GCN NTU120 2D stream weights (24MB). Raw UCF-Crime / XD-Violence videos are NOT re-hosted (upstream distribution terms); README links official sources.

User decisions (2026-09-01/06): caches public, MIT, single Zenodo record, user handles Zenodo account + GitHub-integration toggle; API token supplied for the REST upload.
</objective>

<tasks>

## Task 1: Zenodo draft + DOI
Create deposition via REST API (metadata: dataset, creator Jeng Wei-Han/NTUST, keywords, GitHub related_identifier), capture pre-reserved DOI.

## Task 2: LICENSE + README
MIT LICENSE. README: overview, headline table (PROVENANCE.md families 1-5), repo layout, 3-env setup (link envs/SETUP.md), dataset acquisition (official links), Tier 1 / Tier 2 reproduction incl. E:/ path remap note, TTA/corruption experiments, thesis+paper builds, citation (thesis + DOI), license notes for third-party assets. Commit + push.

## Task 3: Tag + release
git tag v1.0-thesis; gh release create (notes summarize headline results + Zenodo DOI). Zenodo GitHub integration (if toggle on) archives the tagged snapshot as the code DOI.

## Task 4: Stage + upload + publish
Tar staging on E: (ucf_features.tar, xd_features.tar, snippet_boundaries.tar, checkpoints_headline.tar, ctrgcn_ntu120_2d_weights.tar); upload via bucket API in background (~16GB, bandwidth-bound); show user final metadata; publish ONLY after user confirms; then swap the README DOI badge to the live DOI if it differs and record SUMMARY/STATE.
</tasks>

<execution_note>
Executed in main session context (same rationale as 260906-nc8: long-running background uploads + external-service publish gate need direct oversight; no worktree isolation for a docs+external task).
</execution_note>
