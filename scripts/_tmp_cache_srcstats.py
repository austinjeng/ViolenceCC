"""Cache clean-TRAIN source stats (mean+cov) per backbone+stream to npz.
Throwaway (TTA-boost strategy search). Lets strategy agents load instantly
instead of recomputing (giant clip stats = 172s)."""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import sys, time
from pathlib import Path
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from scripts._tmp_coral_derisk import _clean_train_stats, BACKBONE_FEATURE_PREFIX

CACHE = _ROOT / "results" / "_coral_derisk" / "_srccache"
CACHE.mkdir(parents=True, exist_ok=True)
train_ids = [l.strip() for l in (_ROOT / "data/splits/ucf_train.txt").read_text().splitlines() if l.strip()]

for bb, prefix in BACKBONE_FEATURE_PREFIX.items():
    for stream in ("clip", "skel"):
        out = CACHE / f"{bb}_{stream}.npz"
        if out.exists():
            print(f"skip {out.name}", flush=True); continue
        t = time.time()
        mu, C, n = _clean_train_stats(prefix, train_ids, stream)
        np.savez(str(out), mu=mu, C=C, n=n)
        print(f"{bb}/{stream}: D={mu.shape[0]} n={n} ({time.time()-t:.0f}s) -> {out.name}", flush=True)
print("DONE caching source stats", flush=True)
