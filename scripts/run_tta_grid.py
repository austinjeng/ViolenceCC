"""Run the full TTA evaluation grid (~500 runs) sequentially.

Launches source_only → tent_grid → sar_grid queues.
Resume-safe via .done markers.

Usage:
    C:/Anaconda/envs/vcc-main/python.exe scripts/run_tta_grid.py
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "tta_grid_progress.log"
PYTHON = sys.executable

QUEUES = ["tta_source_only", "tta_tent_grid", "tta_sar_grid"]


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    log("=" * 60)
    log("TTA evaluation grid — STARTING")
    log(f"Queues: {QUEUES}")
    log("=" * 60)

    for queue in QUEUES:
        log(f"\n--- Queue: {queue} ---")
        start = time.time()
        cmd = [
            PYTHON, "scripts/run_ablations.py",
            "--queue", queue, "--no-preflight",
        ]
        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            log(f"Queue {queue} DONE ({elapsed / 60:.1f} min)")
        else:
            log(f"Queue {queue} FAILED (rc={result.returncode}, {elapsed / 60:.1f} min)")
            stderr_tail = result.stderr[-500:] if result.stderr else ""
            if stderr_tail:
                log(f"  stderr: {stderr_tail}")

    log("\n" + "=" * 60)
    log("TTA evaluation grid — COMPLETE")
    log("=" * 60)


if __name__ == "__main__":
    main()
