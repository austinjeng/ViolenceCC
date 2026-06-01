---
phase: quick-260601-jtb
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/recompute_fulllength_ucf.py
  - src/evaluate.py
  - tests/test_h1_fulllength_grid.py
autonomous: true
requirements: [H1-RECOMPUTE, H1-PATCH, H1-REGRESSION]

must_haves:
  truths:
    - "An offline script produces corrected full-length AUC/AP for every results/ucf_* run into a comparison CSV"
    - "The recompute reproduces the verified gate (giant s42 -> AUC 0.8249, AP 0.2737) within 0.001"
    - "No canonical/paper artifact (eval_metrics.json, results-index.csv, intermediate CSVs, tables_generated.tex, main.tex, figures) is modified"
    - "src/evaluate.py UCF path uses true video length (total_frames*upsample) when paths.snippet_boundaries_dir is set, and warns when it is not"
    - "A fast unit test proves snippet_to_frame tail-pads to a boundary-driven n_frames larger than the snippet-count grid"
  artifacts:
    - path: "scripts/recompute_fulllength_ucf.py"
      provides: "Layer-1 offline full-length recompute -> results/h1_recompute/*.csv"
    - path: "results/h1_recompute/ucf_fulllength_comparison.csv"
      provides: "Per-run old/new AUC+AP comparison (one row per ucf_* run)"
    - path: "src/evaluate.py"
      provides: "Layer-2 surgical patch: boundary-aware true n_frames for the UCF path"
    - path: "tests/test_h1_fulllength_grid.py"
      provides: "Regression test locking the tail-pad-to-true-length behavior"
  key_links:
    - from: "scripts/recompute_fulllength_ucf.py"
      to: "src/eval/metrics.compute_frame_metrics"
      via: "import + call (reuse existing sklearn util, no reimplementation)"
      pattern: "compute_frame_metrics"
    - from: "scripts/recompute_fulllength_ucf.py"
      to: "E:/snippets/ucf/{vid}_boundaries.json"
      via: "read total_frames; full_len = total_frames * 10"
      pattern: "total_frames"
    - from: "src/evaluate.py"
      to: "cfg.paths.snippet_boundaries_dir"
      via: "optional cfg key gates true-length computation"
      pattern: "snippet_boundaries_dir"
---

<objective>
Fix H1: the UCF evaluation frame grid is truncated to the snippet-count length
(`len(scores)*64*10`), which is always SHORTER than the true video length
(`total_frames*10`). This drops ~8.8% of UCF positive frames and inflates AUC
by ~0.7pp.

Two layers, both in this single plan:
- LAYER 1 (Task 1): an OFFLINE recompute script that produces corrected
  full-length AUC/AP for every `results/ucf_*` run into a comparison CSV. It
  only READS run artifacts and the boundary JSONs; it WRITES only under
  `results/h1_recompute/`. No canonical/paper artifact is touched.
- LAYER 2 (Task 2): a surgical, non-breaking patch to the live eval path in
  `src/evaluate.py` so the bug cannot recur, gated behind a new optional
  `paths.snippet_boundaries_dir` cfg key.
- Task 3: a fast regression unit test locking the tail-pad-to-true-length
  behavior.

Purpose: produce trustworthy full-length numbers for human review, and make
the live evaluator correct-by-construction without disturbing any existing
results. This is an ANALYSIS PAUSE-POINT — the orchestrator reviews the
comparison numbers with the user BEFORE any paper/canonical change.

Output: `scripts/recompute_fulllength_ucf.py`,
`results/h1_recompute/ucf_fulllength_comparison.csv` (and an XD CSV or skip
note), the `src/evaluate.py` patch, and `tests/test_h1_fulllength_grid.py`.
</objective>

<scope_guardrails>
This is an analysis pause-point. Success = the comparison CSV exists, the
giant-s42 gate passes, and the code patch + regression test are in place.

DO NOT edit, regenerate, or overwrite ANY of the following — these updates are
DEFERRED pending human review of the comparison numbers:
- paper/main.tex
- paper/tables_generated.tex
- paper/figures/* (any figure)
- results-index.csv (and any other index/intermediate CSV)
- any results/<run>/eval_metrics.json, eval_scores.npz, per_category.csv

The recompute script (Task 1) only READS those; it WRITES exclusively under
results/h1_recompute/. The eval patch (Task 2) is non-breaking and changes no
default behavior unless the new cfg key is explicitly set. The orchestrator
will review the comparison numbers with the user before any paper change.
</scope_guardrails>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md

Run all Python in the `vcc-main` conda environment (PyTorch 2.6 main env).
The script does NOT need a GPU — it reads cached `eval_scores.npz` and never
runs inference. `eval_scores.npz` is keyed by `video_id`; each value is a
1-D frame array of length `n_snip*640` that is a PURE per-snippet repeat
(verified: per-640-block peak-to-peak == 0), so per-snippet scores are
recovered by `arr.reshape(n_snip, 640)[:, 0]`.
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@src/evaluate.py
@src/eval/snippet_to_frame.py
@src/eval/ucf_annotations.py
@src/eval/metrics.py
@tests/test_snippet_to_frame.py

<interfaces>
<!-- Exact signatures the executor must call. Do NOT reimplement these. -->

From src/eval/snippet_to_frame.py:
```python
def snippet_to_frame(
    scores: np.ndarray,          # [N] 1D per-snippet scores
    n_frames: int,               # exact target length
    snippet_window: int,         # frames per snippet (UCF=64)
    *,
    upsample_factor: int = 1,    # post-expansion multiplier (UCF=10)
) -> np.ndarray:                 # [n_frames]; tail-pads with scores[-1] when short, truncates when long
    # Tail-pad branch (already present):  if len(expanded) < n_frames -> pad with expanded[-1]
    # Drift guard (already present):      assert abs(len(expanded) - n_frames) <= 2 * snippet_window * upsample_factor
```
Note: for the UCF full-length fix the per-video overshoot is
`total_frames*10 - n_snip*640`, which is < one snippet window (640) because
only the trailing partial 64-PNG window is dropped at extraction. So the
existing `2 * tol = 1280` drift guard is NOT violated by the fix.

From src/eval/ucf_annotations.py:
```python
@dataclass(frozen=True)
class VideoAnnotation: video_id: str; category: str; intervals: Tuple[Interval, Interval]
def parse_annotations(path: Path) -> Dict[str, VideoAnnotation]   # keyed by id WITHOUT _x264.mp4 suffix
def frame_labels(anno: VideoAnnotation, n_frames: int) -> np.ndarray  # zeros(n_frames), intervals clamped to [0, n_frames]
```

From src/eval/metrics.py:
```python
def compute_frame_metrics(
    per_video_scores: Dict[str, np.ndarray],
    per_video_labels: Dict[str, np.ndarray],
    per_video_category: Dict[str, str],
) -> dict   # returns {"auc","ap","n_videos","n_frames","per_category",[ "video_auc" ]}
```

Boundary JSON shape (E:/snippets/ucf/{video_id}_boundaries.json):
```json
{ "video_id": "Arson011", "total_frames": 127, "frames_per_snippet": 64, "n_snippets": 1 }
```
full_len = total_frames * 10  (upsample_factor; always >= n_snip*640 -> fix only EXTENDS/tail-pads, never truncates).

GT annotation file: data/annotations/ucf_temporal.txt
(format `VideoName_x264.mp4  Category  s1 e1 s2 e2`, frame indices in 30fps grid; -1 = none).
Run artifacts per results/ucf_*/: eval_scores.npz (keyed by video_id),
eval_metrics.json (has "auc","ap"). Old giant s42 baseline = AUC 0.8322664, AP 0.2921619.

Config snapshot note: config_snapshot.json wraps the real config under the
"config" key; src.utils.config.load_snapshot_as_config unwraps it. The UCF
eval path selects via cfg.get("dataset", "ucf") and reads
cfg.get("paths", {}).get(...). The current UCF run snapshots carry no
top-level dataset / paths, so the default ("ucf") path and the
absent-boundaries WARNING branch are the live code paths.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Layer-1 offline full-length recompute script</name>
  <files>scripts/recompute_fulllength_ucf.py</files>
  <action>
Create `scripts/recompute_fulllength_ucf.py`. It is READ-ONLY w.r.t. all
existing artifacts and writes ONLY under `results/h1_recompute/`.

Bootstrap sys.path to project root the same way src/evaluate.py does (insert
parent-of-parent). Accept `--boundaries-dir` (default `E:/snippets/ucf`),
`--results-glob` (default `results/ucf_*`), `--out-dir` (default
`results/h1_recompute`), and `--xd-boundaries-dir` (default None) CLI args.
Reuse, never reimplement: import `compute_frame_metrics` from src.eval.metrics,
`parse_annotations`/`frame_labels` from src.eval.ucf_annotations, and
`snippet_to_frame` from src.eval.snippet_to_frame.

Startup guard: if the UCF boundaries dir does not exist, FAIL LOUDLY with a
clear message (`H1 recompute: boundaries dir {dir} not found; cannot produce
correct full-length numbers`) and exit non-zero. Do NOT emit any partial CSV.

For each `results/ucf_*` run dir that has BOTH eval_scores.npz AND
eval_metrics.json:
  - Load eval_scores.npz (np.load, keyed by video_id). For each video:
    recover per-snippet scores = `arr.reshape(n_snip, 640)[:, 0]` where
    n_snip = arr.shape[0] // 640 (assert arr.shape[0] % 640 == 0).
  - Read `{boundaries_dir}/{vid}_boundaries.json`; full_len = total_frames*10
    with snippet_window=64, upsample_factor=10. If a boundary JSON is missing
    for a video, append vid to a per-run `skipped_videos` list and skip that
    video (do not crash the whole run; surface the count in stdout and the CSV).
  - Build full-length frame scores via `snippet_to_frame(snippet_scores,
    n_frames=full_len, snippet_window=64, upsample_factor=10)` (its tail-pad
    branch repeats the LAST snippet score up to full_len; never truncates
    since full_len >= n_snip*640).
  - Build labels: parse data/annotations/ucf_temporal.txt once via
    parse_annotations. If vid in annos -> frame_labels(anno, full_len) and
    category = anno.category. Else -> np.zeros(full_len) and category="Normal".
  - Recompute global frame AUC/AP via compute_frame_metrics(scores, labels,
    cats). Read old_auc/old_ap from THIS run's eval_metrics.json.
  - Collect a row: run_name, old_auc, new_auc, d_auc(=new-old), old_ap, new_ap,
    d_ap(=new-old), n_videos, n_frames_old(sum of n_snip*640),
    n_frames_new(=compute_frame_metrics result "n_frames"), n_skipped.

HARD GATE (run after the giant s42 run is recomputed): assert
ucf_gated_fusion_giant_s42 new_auc within 0.001 of 0.8249 AND new_ap within
0.001 of 0.2737. If the gate FAILS, print actual-vs-expected and exit non-zero
WITHOUT finalizing the CSV. Implement by writing the CSV to a `.tmp` path
first and only `os.replace`-ing it into
results/h1_recompute/ucf_fulllength_comparison.csv AFTER the gate passes — so
a failed run leaves no paper-facing CSV. If giant s42 is absent from the glob,
treat as gate failure (cannot self-verify) and exit non-zero.

Also emit a per-category recompute for ONLY ucf_gated_fusion_giant_s42 into
results/h1_recompute/ucf_giant_s42_per_category.csv (columns: category,
old_auc, new_auc, old_ap, new_ap) using the per_category dict from
compute_frame_metrics and the run's eval_metrics.json per_category block — to
aid later human review.

XD pass: repeat the per-run recompute loop for `results/xd_*` into
results/h1_recompute/xd_fulllength_comparison.csv ONLY IF `--xd-boundaries-dir`
is provided AND exists (XD uses snippet_window=16 for xd_i3d-style runs / 64
for xd fusion runs, upsample_factor=1; infer the window from arr.shape[0]
divisibility or default to 64 for fusion runs and 16 for run names containing
`i3d`). If XD boundary data is absent, write a one-line note file
results/h1_recompute/xd_SKIPPED.txt ("XD full-length recompute skipped: no
boundary data; expected ~0 change since upsample_factor=1 and overshoot
<= one snippet window") and continue — do NOT fail the UCF pass on XD absence.

GUARDRAIL (state it in a top-of-file docstring AND honor it): the script NEVER
writes to or overwrites any eval_metrics.json, eval_scores.npz, per_category.csv
inside a run dir, results-index.csv, any intermediate CSV, tables_generated.tex,
main.tex, or any figure. It only READS those and WRITES under
results/h1_recompute/.
  </action>
  <verify>
    <automated>conda run -n vcc-main python scripts/recompute_fulllength_ucf.py --boundaries-dir E:/snippets/ucf && conda run -n vcc-main python -c "import csv; rows=list(csv.DictReader(open('results/h1_recompute/ucf_fulllength_comparison.csv'))); g=[r for r in rows if r['run_name']=='ucf_gated_fusion_giant_s42']; assert g, 'giant s42 row missing'; r=g[0]; assert abs(float(r['new_auc'])-0.8249)<=0.001 and abs(float(r['new_ap'])-0.2737)<=0.001, ('gate fail',r['new_auc'],r['new_ap']); print('GATE PASS rows=',len(rows))"</automated>
  </verify>
  <done>
results/h1_recompute/ucf_fulllength_comparison.csv exists with one row per
discoverable results/ucf_* run; the giant s42 gate passes (new_auc within
0.001 of 0.8249, new_ap within 0.001 of 0.2737); a giant-s42 per-category CSV
exists; XD produced either xd_fulllength_comparison.csv or xd_SKIPPED.txt; and
NO existing artifact outside results/h1_recompute/ was modified (confirm via
`git status` showing only the new script + results/h1_recompute/ as changes).
  </done>
</task>

<task type="auto">
  <name>Task 2: Layer-2 surgical eval-code patch (boundary-aware true length)</name>
  <files>src/evaluate.py</files>
  <action>
Patch ONLY the UCF default path in `_build_frame_arrays` (the block at
src/evaluate.py ~lines 263-296, after `snippet_window = 64; upsample_factor =
10`). Do NOT touch the `xd_i3d` or `xd` branches' call sites.

Add `import warnings` to the stdlib import group at the top of the file (it is
not currently imported).

Read the optional cfg key once before the per-video loop:
`boundaries_dir = cfg.get("paths", {}).get("snippet_boundaries_dir")`.

In the per-video loop, replace the single hardcoded
`n_frames = len(scores) * snippet_window * upsample_factor` with:
  - If boundaries_dir is set AND `{boundaries_dir}/{vid}_boundaries.json`
    exists: read total_frames from that JSON and set
    `n_frames = int(total_frames) * upsample_factor` (TRUE full length).
  - Otherwise: keep CURRENT behavior `n_frames = len(scores) *
    snippet_window * upsample_factor` (snippet-grid / truncated length).

Pass that `n_frames` to BOTH frame_labels(anno, n_frames) and
snippet_to_frame(scores, n_frames=..., snippet_window=64, upsample_factor=10),
exactly as the current code already does — so snippet_to_frame's existing
tail-pad branch covers the extended length. Make NO change to
src/eval/ucf_annotations.py (frame_labels already clamps to n_frames) or to
src/eval/snippet_to_frame.py (its tail-pad path already exists).

One-time WARNING per CLAUDE.md eval-stub convention: when boundaries_dir is
absent/None, emit ONCE per eval (guard with a local boolean flag set before
the loop, not per-video) both `warnings.warn(...)` and `logging.warning(...)`
reading: "UCF eval uses the snippet-grid (truncated) length; set
paths.snippet_boundaries_dir to use true full-length frames (H1)." If the
module does not already have a logging import, prefer warnings.warn alone
rather than introducing a new logging dependency — keep the change minimal.

This is non-breaking: existing runs without the cfg key behave identically to
today (plus one warning); the fix activates only when the cfg key points at
the boundary JSONs.
  </action>
  <verify>
    <automated>conda run -n vcc-main python -c "import ast; ast.parse(open('src/evaluate.py').read()); print('parse ok')" && conda run -n vcc-main python -m pytest tests/test_evaluate_cli.py tests/test_evaluate_xd.py tests/test_evaluate_xd_i3d.py -q</automated>
  </verify>
  <done>
src/evaluate.py parses; the UCF path computes true `n_frames =
total_frames*upsample` when paths.snippet_boundaries_dir is set and a boundary
JSON exists, else keeps current behavior plus a single H1 warning; the
xd_i3d/xd branches are unchanged; and existing evaluate CLI/XD/XD-I3D tests
still pass.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Regression test locking tail-pad-to-true-length</name>
  <files>tests/test_h1_fulllength_grid.py</files>
  <behavior>
    - Given per-snippet scores of length N (e.g. [0.1,0.5,0.9], window=64,
      upsample=10), the snippet-count grid is N*640. A boundary-driven
      n_frames = total_frames*10 with total_frames just over N*64 (e.g. 200
      -> 2000) is STRICTLY LARGER than the snippet-count grid (3*640=1920).
    - snippet_to_frame(scores, n_frames=2000, snippet_window=64,
      upsample_factor=10) returns an array of length EXACTLY 2000.
    - The padded tail (indices >= 1920) all equal the LAST snippet score (0.9):
      assert np.allclose(frames[1920:], scores[-1]).
    - The body (first 1920) is the normal repeat: frames[:640]==0.1,
      frames[640:1280]==0.5, frames[1280:1920]==0.9.
    - Sanity: boundary-driven n_frames (2000) > snippet-count grid
      (len(scores)*64*10 == 1920), i.e. the fix EXTENDS the grid.
    - The overshoot here (80 frames) is within the existing drift guard
      (2*64*10=1280), so no AssertionError is raised.
  </behavior>
  <action>
Create `tests/test_h1_fulllength_grid.py` as a fast, GPU-free, feature-free
unit test importing only `numpy` and
`from src.eval.snippet_to_frame import snippet_to_frame`. Encode the behaviors
above as assertions. Match the style of the existing
tests/test_snippet_to_frame.py (plain pytest functions, np.float32 score
arrays, np.allclose checks). Do NOT add fixtures, GPU, or model loading.
  </action>
  <verify>
    <automated>conda run -n vcc-main python -m pytest tests/test_h1_fulllength_grid.py -q</automated>
  </verify>
  <done>
pytest tests/test_h1_fulllength_grid.py passes in vcc-main: it proves
snippet_to_frame tail-pads with the last snippet score to a boundary-driven
n_frames that is strictly larger than the snippet-count grid.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem -> recompute script | Reads run artifacts + boundary JSONs from disk (E:/snippets/ucf); untrusted only in that files could be missing/malformed |
| cfg -> evaluate.py UCF path | New optional cfg key `paths.snippet_boundaries_dir` controls a length computation |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-h1-01 | Tampering | recompute script writing canonical artifacts | mitigate | Script writes ONLY under results/h1_recompute/; guardrail asserted in docstring; `git status` check in Task 1 done-criteria confirms no other file changed |
| T-h1-02 | Information disclosure | partial/wrong CSV consumed as paper fact | mitigate | Hard gate (giant s42 0.8249/0.2737); CSV finalized via os.replace ONLY after gate passes, so a failed run leaves no paper-facing CSV |
| T-h1-03 | Denial of correctness | missing boundary dir -> silent wrong numbers | mitigate | Startup guard fails loudly + non-zero exit when boundaries dir absent; per-video missing JSON logged as n_skipped, never silently zero-filled |
| T-h1-04 | Repudiation | live eval silently using truncated length | mitigate | One-time runtime WARNING (CLAUDE.md eval-stub convention) when snippet_boundaries_dir is unset |
| T-h1-SC | Tampering | npm/pip/cargo installs | accept | No new dependencies installed; reuses existing src.eval utils and stdlib + numpy already in vcc-main |
</threat_model>

<verification>
- `git status` after Task 1 shows changes ONLY in scripts/recompute_fulllength_ucf.py and results/h1_recompute/ (no eval_metrics.json, results-index.csv, intermediate CSV, paper/*, or figure modified).
- results/h1_recompute/ucf_fulllength_comparison.csv has exactly one row per discoverable results/ucf_* run with both eval_scores.npz and eval_metrics.json.
- Giant-s42 gate: new_auc within 0.001 of 0.8249 AND new_ap within 0.001 of 0.2737.
- src/evaluate.py: `conda run -n vcc-main python -m pytest tests/test_evaluate_cli.py tests/test_evaluate_xd.py tests/test_evaluate_xd_i3d.py tests/test_snippet_to_frame.py -q` passes (no regression in XD/I3D/UCF eval paths or the broadcast util).
- `conda run -n vcc-main python -m pytest tests/test_h1_fulllength_grid.py -q` passes.
</verification>

<success_criteria>
- scripts/recompute_fulllength_ucf.py exists, runs in vcc-main without a GPU, and produces results/h1_recompute/ucf_fulllength_comparison.csv plus the giant-s42 per-category CSV; XD produces a comparison CSV or xd_SKIPPED.txt.
- The giant-s42 hard gate passes (0.8249 / 0.2737 within 0.001); a failed gate leaves NO finalized CSV.
- src/evaluate.py UCF path uses true full length when paths.snippet_boundaries_dir is set and warns once when it is not; xd_i3d/xd paths unchanged; existing eval tests pass.
- tests/test_h1_fulllength_grid.py passes and locks the tail-pad-to-true-length behavior.
- ZERO canonical/paper artifacts modified — this remains an analysis pause-point for human review before any paper change.
</success_criteria>

<output>
Create `.planning/quick/260601-jtb-fix-h1-ucf-eval-frame-grid-truncation-fu/260601-jtb-SUMMARY.md` when done.
</output>
