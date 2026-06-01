---
phase: quick-260601-kjm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/recompute_fulllength_ucf.py
  - results/ucf_*/eval_metrics.json
  - results/ucf_*/eval_scores.npz
  - results/results-index.csv
  - results/phase10_charts/backbone_comparison_4way.csv
  - results/phase10_charts/seed_stability_4way.csv
  - paper/tables_generated.tex
  - paper/figures/fig_backbone_comparison.pdf
  - paper/figures/fig_temporal_scores.pdf
  - paper/figures/fig_gating_distribution.pdf
  - paper/main.tex
autonomous: true
requirements: [H1-PROPAGATE]
must_haves:
  truths:
    - "results/ucf_gated_fusion_giant_s42/eval_metrics.json reads auc~0.8249, ap~0.2737 (+/-0.001)"
    - "results-index.csv ucf_* rows carry full-length auc/ap/n_frames; xd_* and TTA rows untouched"
    - "Regenerated seed_stability_4way.csv UCF Giant Gated Fusion 3-seed AUC mean ~ 0.8254"
    - "tables_generated.tex Table 1 Giant Gated Fusion = 82.5; GF Mean-Only Giant = 83.0; Tables 2/3 byte-identical to pre-run"
    - "paper/main.tex abstract = 82.5; Conclusion = 82.5/83.0; Limitations = 83.0; inline Table 1 == tables_generated.tex Table 1"
    - "Backup .pre_h1.bak files exist for every overwritten canonical UCF artifact"
  artifacts:
    - path: "scripts/recompute_fulllength_ucf.py"
      provides: "Extended recompute with idempotent --write flag (backup-before-overwrite)"
      contains: "--write"
    - path: "results/h1_recompute/ucf_fulllength_comparison.csv"
      provides: "Source-of-truth corrected per-run numbers (already validated, READ-ONLY here)"
    - path: "paper/tables_generated.tex"
      provides: "Regenerated Table 1 (UCF) reflecting full-length numbers; Tables 2/3 unchanged"
    - path: "paper/main.tex"
      provides: "Prose + inline Table 1 synced to full-length UCF numbers"
  key_links:
    - from: "results/ucf_*/eval_metrics.json + results-index.csv"
      to: "results/phase10_charts/*_4way.csv"
      via: "generate_phase10_charts.py reads results-index.csv"
      pattern: "results-index\\.csv"
    - from: "results/phase10_charts/*_4way.csv"
      to: "paper/tables_generated.tex"
      via: "generate_latex_tables.py"
      pattern: "backbone_comparison_4way\\.csv"
    - from: "paper/tables_generated.tex Table 1"
      to: "paper/main.tex inline Table 1"
      via: "manual byte-identical sync"
      pattern: "tab:ucf-ablation"
---

<objective>
Propagate the already-validated H1 full-length UCF recompute (task 260601-jtb: ucf_gated_fusion_giant_s42 -> AUC 0.8249 / AP 0.2737) into EVERY downstream artifact so the entire chain is consistent: canonical per-run UCF artifacts -> regenerated intermediate CSVs/tables/figures -> paper/main.tex prose + inline Table 1.

Purpose: The live UCF eval truncated each video's frame grid to snippet-count length, dropping ~8.8% of positive frames and inflating UCF AUC by ~0.7pp. The fix is computed and gated; this task makes it the published reality. XD and TTA are mathematically UNAFFECTED (XD upsample_factor=1, overshoot <= one snippet window) and MUST NOT change.

Output: Overwritten canonical UCF artifacts (with backups), regenerated derived CSVs/tables/figures via the existing scripts, and surgically edited paper/main.tex.

CRITICAL: this task DOES change published numbers. It is the approved propagation; no mid-task pause. The orchestrator reviews after.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md
@scripts/recompute_fulllength_ucf.py
@results/h1_recompute/ucf_fulllength_comparison.csv
@scripts/generate_phase10_charts.py
@scripts/generate_latex_tables.py
@scripts/generate_pub_figures.py

<interfaces>
<!-- Contracts extracted from the codebase. Executor uses these directly, no exploration needed. -->

# src/eval/metrics.py :: compute_frame_metrics(per_video_scores, per_video_labels, per_video_category) -> dict
#   Returns keys: auc (float), ap (float), n_videos (int), n_frames (int),
#                 per_category (dict cat -> {auc, ap}), and OPTIONALLY video_auc.
#   Does NOT return snippet_auc.

# src/eval/snippet_to_frame.py :: snippet_to_frame(scores, n_frames, snippet_window, *, upsample_factor)
#   Returns [n_frames] float array, TAIL-PADDED with the last value when expanded < n_frames
#   (this is exactly the full-length per-video frame array to store in eval_scores.npz).

# results/ucf_*/eval_metrics.json scalar keys present (verified on giant_s42):
#   ap, auc, checkpoint_sha, config_hash, dataset, eval_duration_s, eval_timestamp,
#   git_sha, n_frames, n_videos, per_category, seed, snippet_auc, split, video_auc, wandb_run_id
#   OVERWRITE ONLY: auc, ap, n_frames, per_category. PRESERVE every other key verbatim
#   (checkpoint_sha, config_hash, dataset, seed, split, git_sha, snippet_auc, video_auc, n_videos, eval_*, wandb_run_id).

# results/ucf_*/eval_scores.npz : keyed by video_id; each value is a 1-D float32 frame array of
#   length n_snip*640 that is a PURE per-snippet repeat. Per-snippet scores recovered by
#   arr.reshape(n_snip, 640)[:, 0]  (block = 64*10 = 640).

# results/h1_recompute/ucf_fulllength_comparison.csv columns:
#   run_name, old_auc, new_auc, d_auc, old_ap, new_ap, d_ap, n_videos, n_frames_old, n_frames_new, n_skipped
#   29 ucf_* rows. new_auc/new_ap/n_frames_new are the SOURCE OF TRUTH. n_frames_new = 1097050 for all. n_skipped = 0 for all.

# results/results-index.csv columns (row 1 header):
#   run_name, variant, dataset, seed, cache_variant, auc, ap, n_videos, n_frames, start_time,
#   end_time, config_hash, method, corruption_type, severity, lr, rho
#   Update auc, ap, n_frames for ucf_* rows ONLY. Leave xd_* and any method/source_only/tent/sar rows untouched.

# Existing recompute internals to REUSE (do NOT reimplement metrics):
#   _recompute_ucf_run(run_dir, boundaries_dir, annos, snippet_window, upsample_factor) -> row dict
#     - already computes full-length per-video frame_scores + new_metrics (with per_category)
#     - stashes row["_new_metrics"] (full dict) and row["_old_metrics"]
#   GIANT_RUN="ucf_gated_fusion_giant_s42", GATE_AUC=0.8249, GATE_AP=0.2737, GATE_TOL=0.001
#   UCF_SNIPPET_WINDOW=64, UCF_UPSAMPLE=10, UCF_BLOCK=640
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Extend recompute script with idempotent --write flag and overwrite canonical UCF artifacts (backup-before-overwrite)</name>
  <files>scripts/recompute_fulllength_ucf.py, results/ucf_*/eval_metrics.json, results/ucf_*/eval_scores.npz, results/results-index.csv</files>
  <action>
EXTEND scripts/recompute_fulllength_ucf.py, do NOT rewrite it; reuse the existing full-length computation in _recompute_ucf_run (the SAME math already gated in 260601-jtb). Add a --write boolean flag (default False) to _parse_args. When --write is absent, behavior is byte-for-byte unchanged (still READ-ONLY, still writes only under results/h1_recompute/). When --write is set, after the HARD GATE passes in _run_ucf, perform the canonical overwrite for every ucf_* run.

Implementation notes:
1. _recompute_ucf_run must ALSO return the per-video full-length frame_scores it already builds (currently discarded). Add row["_per_video_scores"] = per_video_scores (the dict of {vid: tail-padded full-length np.float32 array from snippet_to_frame}) alongside the existing row["_new_metrics"] / row["_old_metrics"] stashes. These underscore keys are already dropped by _write_csv (extrasaction="ignore"), so the comparison CSV is unaffected.

2. Add a helper _write_canonical(rows) invoked from _run_ucf ONLY when args.write is True AND after print("GATE PASS: ..."). For each row (each ucf_* run dir, reconstructed as _PROJECT_ROOT/"results"/row["run_name"]):
   a. eval_metrics.json: load the existing JSON. Write a backup eval_metrics.json.pre_h1.bak FIRST, but ONLY if that .bak does not already exist (idempotent: never clobber the original pre-H1 backup on a re-run). Then set ONLY these four keys from row["_new_metrics"]: auc, ap, n_frames, per_category. PRESERVE every other key verbatim (checkpoint_sha, config_hash, dataset, seed, split, git_sha, snippet_auc, video_auc, n_videos, eval_duration_s, eval_timestamp, wandb_run_id). Write atomically via a .tmp then os.replace.
   b. eval_scores.npz: write backup eval_scores.npz.pre_h1.bak FIRST (only if absent). Then save the FULL-LENGTH per-video frame arrays from row["_per_video_scores"] with np.savez (keyed by video_id, float32) to a .tmp then os.replace. The stored arrays are now tail-padded to true full length (total_frames*10), so fig_temporal_scores reflects full length. n_skipped=0 across all 29 runs (verified in the comparison CSV), so every video has a full-length array; if a run ever has skipped videos, OMIT those vids from the npz rather than writing a truncated array, and log a WARNING (per CLAUDE.md: decoder/extraction failures log at WARNING, not DEBUG).
   c. results-index.csv: update ONLY the ucf_* rows. Read the CSV with csv.DictReader (preserve fieldnames/order), and for each row whose run_name matches a recomputed ucf_* run, set auc, ap, n_frames (as strings) from row["_new_metrics"]. Do NOT touch any xd_* row or any row with method in {source_only, tent, sar} or any corruption row. Back up results-index.csv.pre_h1.bak FIRST (only if absent), then write atomically (.tmp -> os.replace), preserving column order and all other columns/rows exactly.

3. Idempotency contract: re-running with --write a second time must (a) NOT overwrite any existing .pre_h1.bak, (b) produce identical canonical files (the recompute is deterministic), (c) re-assert the gate.

Run order: gate runs first (existing code); canonical overwrite happens ONLY on GATE PASS. Per CLAUDE.md, run in vcc-main. UCF boundaries dir is E:/snippets/ucf (the script's default --boundaries-dir).

HARD GATE (re-assert AFTER write): after _write_canonical, re-load results/ucf_gated_fusion_giant_s42/eval_metrics.json from disk and assert auc within 0.001 of 0.8249 AND ap within 0.001 of 0.2737. If not, sys.exit loudly -> STOP. Print the on-disk auc/ap so the failure is diagnosable.

Per CLAUDE.md conventions: surgical changes only; touch only the four metric keys + the three CSV columns; do not refactor unrelated parts of the recompute script.
  </action>
  <verify>
    <automated>cd /d D:\ViolenceCC ; conda run -n vcc-main python scripts/recompute_fulllength_ucf.py --write --boundaries-dir E:/snippets/ucf 2>&1 | findstr /C:"GATE PASS"</automated>
  </verify>
  <done>
Script exits 0 with "GATE PASS". On disk: results/ucf_gated_fusion_giant_s42/eval_metrics.json reads auc~0.8249 ap~0.2737 (+/-0.001) with all non-{auc,ap,n_frames,per_category} keys preserved; eval_metrics.json.pre_h1.bak / eval_scores.npz.pre_h1.bak / results-index.csv.pre_h1.bak exist; results-index.csv ucf_* rows updated, xd_*/TTA rows unchanged; re-running --write does not overwrite any .pre_h1.bak. Confirm with:
conda run -n vcc-main python -c "import json;d=json.load(open('results/ucf_gated_fusion_giant_s42/eval_metrics.json'));print(round(d['auc'],4),round(d['ap'],4),d['n_frames'],'config_hash' in d,'checkpoint_sha' in d)"
(expect: 0.8249 0.2737 1097050 True True)
  </done>
</task>

<task type="auto">
  <name>Task 2: Regenerate derived artifacts via the existing scripts (charts CSVs -> LaTeX tables -> figures); verify XD/TTA unchanged</name>
  <files>results/phase10_charts/backbone_comparison_4way.csv, results/phase10_charts/seed_stability_4way.csv, paper/tables_generated.tex, paper/figures/fig_backbone_comparison.pdf, paper/figures/fig_temporal_scores.pdf, paper/figures/fig_gating_distribution.pdf</files>
  <action>
Before regenerating, snapshot the to-be-unchanged content so XD/TTA invariance is provable: copy the current paper/tables_generated.tex to a temp path (e.g. paper/tables_generated.tex.prepropagate) so the Table 2 (tab:xd-ablation) and Table 3 (tab:tta) blocks can be diffed afterward.

Then run the EXISTING scripts in vcc-main, in THIS exact order (each reads the previous stage's output). Do NOT modify the scripts; they already read the updated results-index.csv / regenerated CSVs:
  1. conda run -n vcc-main python scripts/generate_phase10_charts.py
       -> regenerates results/phase10_charts/backbone_comparison_4way.csv + seed_stability_4way.csv from the updated results-index.csv (also rewrites comparison/seed PNGs, which are intermediate and fine to change).
  2. conda run -n vcc-main python scripts/generate_latex_tables.py
       -> regenerates paper/tables_generated.tex (Table 1 UCF changes; Table 2 XD + Table 3 TTA must be UNCHANGED, since both derive from XD AP / tta_backbone/summary.csv which this task never touched).
  3. conda run -n vcc-main python scripts/generate_pub_figures.py
       -> regenerates ALL figures. fig_backbone_comparison.pdf (reads the 2 CSVs) and fig_temporal_scores.pdf (reads results/ucf_*/eval_scores.npz) WILL change; fig_gating_distribution.pdf (reads per_category from eval_metrics.json) WILL change on its UCF subplot and must be regenerated for consistency. The XD-side content of these figures derives from unchanged xd_* artifacts, so XD bars/values must remain the same numbers. fig_tta_comparison.pdf reads tta_backbone/summary.csv (untouched); do NOT alter TTA content.

After regeneration, VERIFY XD/TTA invariance: extract the Table 2 (tab:xd-ablation) and Table 3 (tab:tta) blocks from the regenerated tables_generated.tex and from the .prepropagate snapshot; the data rows MUST be byte-identical (caption/label/structure included). If any XD or TTA data cell changed, STOP and report (it indicates unintended cross-contamination). Remove the .prepropagate temp file once invariance is confirmed.
  </action>
  <verify>
    <automated>cd /d D:\ViolenceCC ; conda run -n vcc-main python -c "import csv,statistics as st; r=list(csv.DictReader(open('results/phase10_charts/seed_stability_4way.csv'))); ucf=[x for x in r if x['Dataset']=='UCF']; m=st.mean(float(x['Giant_AUC']) for x in ucf); print('mean',round(m,4)); assert abs(m-0.8254)<0.001, m; print('OK')"</automated>
  </verify>
  <done>
seed_stability_4way.csv UCF Giant Gated Fusion 3-seed AUC mean ~ 0.8254. In tables_generated.tex Table 1: Giant Gated Fusion = 82.5 and GF Mean-Only Giant = 83.0. Table 2 (tab:xd-ablation) and Table 3 (tab:tta) data rows byte-identical to the .prepropagate snapshot. Figures fig_backbone_comparison.pdf, fig_temporal_scores.pdf, fig_gating_distribution.pdf regenerated (mtimes updated). Confirm Table 1 generated values:
conda run -n vcc-main python -c "t=open('paper/tables_generated.tex',encoding='utf-8').read();b=t.split('tab:ucf-ablation')[1].split('end{tabular}')[0];print('82.5' in b,'83.0' in b)"
(expect: True True)
  </done>
</task>

<task type="auto">
  <name>Task 3: Apply exact surgical edits to paper/main.tex (abstract, inline Table 1, prose); sync inline Table 1 to regenerated tables_generated.tex</name>
  <files>paper/main.tex</files>
  <action>
Apply EXACTLY these edits. For each, verify the OLD text matches verbatim before replacing (all confirmed present in the codebase at the cited lines). Keep edits surgical; do not touch anything else.

EDIT A (Abstract, line ~43): replace `83.3\% AUC on UCF-Crime (SigLIP2 Giant)` with `82.5\% AUC on UCF-Crime (SigLIP2 Giant)`.

EDIT B (Inline Table 1, lines ~231-237): replace the six data rows so they MATCH the regenerated paper/tables_generated.tex Table 1 (tab:ucf-ablation) block EXACTLY. The generated table is authoritative if rounding differs; the expected new rows are:
  Skeleton Only & \textbf{71.8} & --- & --- & --- & --- \\
  Visual Only & 81.1 & 78.3 & 80.9 & \textbf{82.4} & $\uparrow$+1.3 \\
  Late Fusion & 78.6 & 79.5 & 80.0 & \textbf{80.8} & $\uparrow$+2.2 \\
  Gated Fusion & 81.4$\pm$0.3 & 79.0$\pm$0.1 & 81.3$\pm$0.3 & \textbf{82.5$\pm$0.4} & $\uparrow$+1.1 \\
  GF 2-Person & 81.1 & 78.7 & 81.3 & \textbf{82.7} & $\uparrow$+1.6 \\
  GF Mean-Only & 81.1 & 79.4 & 81.8 & \textbf{83.0} & $\uparrow$+1.9 \\
The current OLD rows to replace are (verbatim, lines 231-237):
  Visual Only & 81.7 & 79.1 & 81.4 & \textbf{83.1} & $\uparrow$+1.4 \\
  Late Fusion & 78.7 & 79.9 & 80.3 & \textbf{80.9} & $\uparrow$+2.2 \\
  Gated Fusion & 82.0$\pm$0.3 & 79.8$\pm$0.2 & 81.9$\pm$0.4 & \textbf{83.3$\pm$0.3} & $\uparrow$+1.3 \\
  GF 2-Person & 81.7 & 79.5 & 82.0 & \textbf{83.5} & $\uparrow$+1.8 \\
  GF Mean-Only & 81.8 & 80.0 & 82.4 & \textbf{83.6} & $\uparrow$+1.8 \\
Do NOT change the Skeleton Only row (keep \textbf{71.8}). Keep the \midrule between Visual Only and Late Fusion. After editing, the inline Table 1 data rows MUST be byte-identical to the regenerated tables_generated.tex tab:ucf-ablation rows (cross-check; the generated table wins on any rounding difference).

EDIT C (Section 4.3, line ~261): replace `Gated Fusion with CLIP (82.0\%) exceeds the CLIP visual-only baseline (81.7\%), indicating that skeleton features contribute information not captured by visual appearance alone. The improvement is more pronounced with stronger backbones: SigLIP2 Giant achieves 83.3\% AUC with Gated Fusion compared to 83.1\% visual-only.` with `Gated Fusion with CLIP (81.4\%) exceeds the CLIP visual-only baseline (81.1\%), indicating that skeleton features contribute information not captured by visual appearance alone. The same pattern holds for the strongest backbone: SigLIP2 Giant reaches 82.5\% AUC with Gated Fusion versus 82.4\% visual-only.` (MANDATORY consistency reword: the old "more pronounced with stronger backbones" is now false since the CLIP margin +0.3 exceeds the Giant margin +0.1; reword to the neutral "same pattern holds". Do not over-edit beyond this.)

EDIT D (Section 4.3, line ~272): replace `On UCF-Crime, CLIP late fusion (78.7\%) falls below CLIP visual-only (81.7\%), a drop of 3.0 percentage points.` with `On UCF-Crime, CLIP late fusion (78.6\%) falls below CLIP visual-only (81.1\%), a drop of 2.5 percentage points.`

EDIT E (Section 4.4, line ~287): replace `83.1\% visual-only, 83.3\% gated fusion, and 83.6\% with mean-only pooling` with `82.4\% visual-only, 82.5\% gated fusion, and 83.0\% with mean-only pooling`.

EDIT F (Section 4.4, line ~293): replace `(standard deviation 0.2--0.4\% AUC)` with `(standard deviation 0.1--0.4\% AUC)`.

EDIT G (Section 6 Limitations, line ~362): replace `Our best UCF-Crime result (83.6\% AUC with SigLIP2 Giant GF Mean-Only)` with `Our best UCF-Crime result (83.0\% AUC with SigLIP2 Giant GF Mean-Only)`.

EDIT H (Section 7 Conclusion, line ~387): replace `SigLIP2 Giant achieves the best UCF-Crime results (83.3\% AUC with gated fusion, 83.6\% with mean-only pooling)` with `SigLIP2 Giant achieves the best UCF-Crime results (82.5\% AUC with gated fusion, 83.0\% with mean-only pooling)`.

DO NOT change (leave verbatim wherever they appear): the 71.8\% skeleton-only figure; the XD numbers 41.3\% / 65.5\% / 71.0\% / 5.5 percentage points / 74.7\% / 77.6\% / 76.3\%; the "+0.6\% CLIP SAR" TTA figure; Table 2 (tab:xd-ablation); Table 3 (tab:tta); or any XD/TTA prose. Touch only the eight edits above.
  </action>
  <verify>
    <automated>cd /d D:\ViolenceCC ; conda run -n vcc-main python -c "t=open('paper/main.tex',encoding='utf-8').read(); assert '83.3\\% AUC on UCF-Crime' not in t; assert '82.5\\% AUC on UCF-Crime (SigLIP2 Giant)' in t; assert '83.6\\% AUC with SigLIP2 Giant GF Mean-Only' not in t; assert '83.0\\% AUC with SigLIP2 Giant GF Mean-Only' in t; assert '0.2--0.4\\% AUC' not in t; assert t.count('{')==t.count('}'); print('OK')"</automated>
  </verify>
  <done>
All eight edits applied verbatim; no stray 83.3/83.6/82.0 UCF figures remain in changed locations; abstract = 82.5; Limitations = 83.0; Conclusion = 82.5/83.0; std range = 0.1--0.4. Braces balanced. XD/TTA numbers and 71.8 skeleton figure untouched. Inline Table 1 data rows byte-identical to tables_generated.tex tab:ucf-ablation block.
  </done>
</task>

</tasks>

<verification>
Structural / consistency checks after all tasks (no TeX toolchain on PATH; structural only):
1. Brace balance in main.tex: python -c "t=open('paper/main.tex',encoding='utf-8').read(); print(t.count('{')==t.count('}'))" -> True.
2. No broken citations/refs introduced: this task changes NO \cite or \ref targets (only numeric/prose cells), so the set of \cite{...} and \ref{...}/\label{...} keys in main.tex must be identical before and after. Spot-check that tab:ucf-ablation, tab:xd-ablation, tab:tta labels still resolve.
3. Inline Table 1 == tables_generated.tex Table 1: extract the tab:ucf-ablation data rows from both files; confirm byte-identical.
4. Table 2 / Table 3 unchanged: diff regenerated tables_generated.tex Table 2/3 blocks vs the .prepropagate snapshot -> identical.
5. Paper numbers: abstract = 82.5; Conclusion = 82.5/83.0; Limitations = 83.0; section 4.4 std = 0.1--0.4.
6. Canonical UCF gate: results/ucf_gated_fusion_giant_s42/eval_metrics.json auc~0.8249, ap~0.2737 (+/-0.001).
7. Figures' mtimes updated for fig_backbone_comparison.pdf, fig_temporal_scores.pdf, fig_gating_distribution.pdf.
8. results-index.csv ucf_* rows carry full-length auc/ap/n_frames; xd_* and TTA rows byte-unchanged.

Commit atomically (results/ is gitignored for some paths; force-add only the needed ones):
- Commit 1 (data pipeline): extended script + canonical results-index.csv + regenerated charts CSVs + tables.
    git add scripts/recompute_fulllength_ucf.py
    git add -f results/results-index.csv                                   (GITIGNORED -> needs -f)
    git add results/phase10_charts/backbone_comparison_4way.csv results/phase10_charts/seed_stability_4way.csv   (TRACKED, no -f)
    git add paper/tables_generated.tex                                      (TRACKED)
  Do NOT commit per-run eval_metrics.json/eval_scores.npz or any .pre_h1.bak (gitignored); leave them on disk as canonical artifacts + backups.
- Commit 2 (paper): prose + figures.
    git add paper/main.tex paper/figures/fig_backbone_comparison.pdf paper/figures/fig_temporal_scores.pdf paper/figures/fig_gating_distribution.pdf
  tables_generated.tex already in Commit 1; no separate Commit 3 needed.
Before committing, run git status --short and confirm staging matches. Sanity-check gitignore: git check-ignore results/phase10_charts/backbone_comparison_4way.csv returns nothing (tracked); git check-ignore results/results-index.csv returns the path (needs -f).
End commit messages with the Co-Authored-By trailer per repo policy.
</verification>

<success_criteria>
- scripts/recompute_fulllength_ucf.py has an idempotent --write flag; default (no flag) behavior unchanged.
- Every results/ucf_* run has: eval_metrics.json (auc/ap/n_frames/per_category = full-length, all other keys preserved), eval_scores.npz (full-length tail-padded arrays), and a .pre_h1.bak for each. results-index.csv ucf_* rows updated; xd_*/TTA rows untouched; results-index.csv.pre_h1.bak present.
- HARD GATE holds post-write: giant_s42 auc~0.8249, ap~0.2737 (+/-0.001).
- Regenerated seed_stability_4way.csv UCF Giant GF AUC mean ~ 0.8254; tables_generated.tex Table 1 Giant GF = 82.5, GF Mean-Only Giant = 83.0; Tables 2/3 byte-identical to pre-run.
- Three UCF-affected figures regenerated; XD/TTA figure content unchanged.
- paper/main.tex: 8 edits applied; abstract = 82.5; section 4.3 reworded for consistency; section 4.4 = 82.4/82.5/83.0 and std 0.1--0.4; Limitations = 83.0; Conclusion = 82.5/83.0; inline Table 1 == tables_generated.tex Table 1; braces balanced; XD/TTA/skeleton numbers untouched.
- Two atomic commits (data pipeline; paper), with results-index.csv force-added.
</success_criteria>

<output>
Create `.planning/quick/260601-kjm-propagate-h1-full-length-ucf-metrics-int/260601-kjm-SUMMARY.md` when done.
</output>
