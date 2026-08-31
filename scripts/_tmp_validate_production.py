"""VALIDATION: re-derive disc_reweight + source_only numbers through the PRODUCTION
evaluate_tta.run_tta_evaluation path (canonical pipeline) and compare to the probe's
recorded values (results/_coral_derisk/r1full_*.json). Also checks determinism
(clip gaussian_5 disc_reweight run twice).

If production matches the probe AND source_only matches the known baselines, the
numbers are real in the canonical path (not a probe-only artifact).
"""
from __future__ import annotations
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import json, sys, tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from src.tta.evaluate_tta import run_tta_evaluation, BACKBONE_SOURCE_RUNS

# (backbone, corruption, severity, method, expected_auc_pct)  expected from r1full_*.json
CASES = [
    ("clip-vit-b-16",  "gaussian_noise",   5, "source_only",   57.70),
    ("clip-vit-b-16",  "gaussian_noise",   5, "disc_reweight", 62.53),
    ("clip-vit-b-16",  "gaussian_noise",   5, "disc_reweight", 62.53),  # determinism re-run
    ("clip-vit-b-16",  "brightness",       5, "disc_reweight", 81.56),
    ("clip-vit-b-16",  "motion_blur",      5, "disc_reweight", 62.78),  # w=1 -> == source
    ("clip-vit-b-16",  "motion_blur",      5, "source_only",   62.78),
    ("siglip2-so400m", "gaussian_noise",   5, "source_only",   45.57),
    ("siglip2-so400m", "gaussian_noise",   5, "disc_reweight", 59.49),  # the +13.9 headline
    ("siglip2-so400m", "gaussian_noise",   3, "disc_reweight", 59.38),
    ("siglip2-base",   "gaussian_noise",   5, "disc_reweight", 60.80),  # the -3.2 caveat
    ("siglip2-giant",  "gaussian_noise",   5, "disc_reweight", 52.16),
]

tmp = Path(tempfile.mkdtemp(prefix="disc_validate_"))
print(f"{'backbone':<16}{'cond':<18}{'method':<14}{'prod_AUC':>9}{'expected':>9}{'diff':>8}  ok", flush=True)
results = []
for i, (bb, ct, sev, method, exp) in enumerate(CASES):
    out = tmp / f"case{i}"
    run_tta_evaluation(
        source_run=_ROOT / "results" / BACKBONE_SOURCE_RUNS[bb],
        corruption_type=ct, severity=sev, method=method, lr=1e-3, rho=0.05,
        output_dir=out, feature_root=Path("E:/features/ucf"), backbone=bb,
        protocol="episodic",
    )
    auc = json.load(open(out / "eval_metrics.json"))["auc"] * 100.0
    diff = auc - exp
    ok = abs(diff) < 0.05
    results.append((bb, ct, sev, method, auc, exp, ok))
    print(f"{bb:<16}{ct+'_'+str(sev):<18}{method:<14}{auc:>9.2f}{exp:>9.2f}{diff:>+8.2f}  {'OK' if ok else 'MISMATCH'}", flush=True)

# determinism check: cases 1 and 2 are identical config
det = abs(results[1][4] - results[2][4]) < 1e-9
n_ok = sum(r[6] for r in results)
print(f"\nMATCH: {n_ok}/{len(results)} within 0.05pp of recorded probe values", flush=True)
print(f"DETERMINISM (clip g5 disc_reweight x2 identical): {det} ({results[1][4]:.6f} vs {results[2][4]:.6f})", flush=True)
print("VALIDATION_PASS" if (n_ok == len(results) and det) else "VALIDATION_FAIL", flush=True)
import shutil
shutil.rmtree(tmp, ignore_errors=True)
