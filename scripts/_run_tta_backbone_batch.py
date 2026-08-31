"""One-shot batch runner for Plan 11-01 Task 2: TTA backbone experiments.

Runs 60 corrupted feature extractions (3 backbones x 4 corruptions x 5 severities)
+ TTA evaluation grids + summary CSV generation.
Writes a completion marker when done.
"""
import subprocess
import sys
import time
from pathlib import Path

PYTHON = sys.executable
PROJECT = Path(__file__).resolve().parent.parent
MARKER = PROJECT / "results" / "tta_backbone" / "_batch_complete.marker"

BACKBONES = ["siglip2-base", "siglip2-so400m", "siglip2-giant"]
CORRUPTIONS = ["gaussian_noise", "jpeg_compression", "brightness", "motion_blur"]
SEVERITIES = [1, 2, 3, 4, 5]

def run(cmd, label):
    print(f"\n{'='*60}")
    print(f"[{time.strftime('%H:%M:%S')}] {label}")
    print(f"  CMD: {' '.join(cmd)}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(PROJECT))
    elapsed = time.time() - t0
    status = "OK" if result.returncode == 0 else f"FAIL (rc={result.returncode})"
    print(f"[{time.strftime('%H:%M:%S')}] {status} in {elapsed:.1f}s")
    return result.returncode == 0

def main():
    t_start = time.time()
    (PROJECT / "results" / "tta_backbone").mkdir(parents=True, exist_ok=True)

    # Step 1: Corrupted feature extraction (60 runs)
    total = len(BACKBONES) * len(CORRUPTIONS) * len(SEVERITIES)
    done = 0
    failed = []
    for bb in BACKBONES:
        for corr in CORRUPTIONS:
            for sev in SEVERITIES:
                done += 1
                label = f"[{done}/{total}] extract {bb} {corr} sev={sev}"
                ok = run([
                    PYTHON, str(PROJECT / "scripts" / "extract_clip.py"),
                    "--dataset", "ucf", "--split", "test",
                    "--backbone", bb,
                    "--corruption", corr, "--severity", str(sev),
                ], label)
                if not ok:
                    failed.append(f"{bb}/{corr}/{sev}")

    # Step 2: TTA evaluation grids
    for queue in ["tta_backbone_source", "tta_backbone_tent", "tta_backbone_sar"]:
        run([
            PYTHON, str(PROJECT / "scripts" / "run_ablations.py"),
            "--queue", queue, "--no-preflight",
        ], f"TTA eval: {queue}")

    # Step 3: Summary CSV
    run([
        PYTHON, str(PROJECT / "scripts" / "analyze_tta_best.py"),
        "--all-backbones",
    ], "Generate TTA backbone summary CSV")

    elapsed_total = time.time() - t_start
    summary = (
        f"Batch complete in {elapsed_total/60:.1f} min\n"
        f"Extractions: {total - len(failed)}/{total} succeeded\n"
        f"Failed: {failed if failed else 'none'}\n"
    )
    print(f"\n{'='*60}")
    print(summary)
    MARKER.write_text(summary)
    print(f"Marker written to {MARKER}")

if __name__ == "__main__":
    main()
