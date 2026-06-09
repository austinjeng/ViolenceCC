"""Build a committed UCF per-video total-frames manifest (M3 provenance fix).

The UCF full-length AUC headline (82.5%) is produced by expanding each video's
snippet scores to its TRUE frame length (`total_frames * 10`), recovering the
trailing partial 64-PNG window that the snippet-grid length drops. That true
length lives ONLY in per-video boundary JSONs at a machine-specific off-repo path
(E:/snippets/ucf/{vid}_boundaries.json), so a fresh `evaluate.py` on the committed
run dir falls back to the truncated snippet-grid length and reproduces 83.2%, not
the released 82.5%.

This script distils the single integer that matters (total_frames) for every UCF
video into a few-KB committed manifest, so `src/evaluate.py` and
`scripts/recompute_fulllength_ucf.py` can reproduce the full-length headline from
git alone (manifest fallback) when the off-repo boundaries dir is absent.

Run once (needs the off-repo boundaries dir present):
    python scripts/build_ucf_frames_manifest.py
    # writes data/ucf_total_frames.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ucf_total_frames.json"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries-dir", default="E:/snippets/ucf",
                    help="Dir of {video_id}_boundaries.json")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    bdir = Path(args.boundaries_dir)
    files = sorted(bdir.glob("*_boundaries.json"))
    if not files:
        print(f"ERROR: no *_boundaries.json under {bdir} — run on the machine that "
              f"holds the boundary data.")
        return 1

    manifest: dict[str, int] = {}
    for f in files:
        d = json.loads(f.read_text())
        vid = d.get("video_id") or f.name[: -len("_boundaries.json")]
        manifest[vid] = int(d["total_frames"])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # sorted keys for a stable, diff-friendly committed artifact
    out.write_text(json.dumps({k: manifest[k] for k in sorted(manifest)}, indent=0))
    print(f"wrote {out}  ({len(manifest)} videos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
