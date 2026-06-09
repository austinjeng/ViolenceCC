"""M2: extend the continual TENT/SAR entropy comparison to 3 training seeds.

The paper (main.tex:325) states "All TTA results are means over three training
seeds {42,123,2024}", but TENT/SAR were only ever run on the seed-42 source
checkpoint (results/_tta_rerun_continual/<bb>/{source,tent,sar}/). This driver
runs the IDENTICAL committed continual protocol (src.tta.evaluate_tta.
run_tta_evaluation, protocol='continual', lr=1e-3, SAR rho=0.05) on the s123 and
s2024 gated-fusion source checkpoints for all 4 backbones x 20 corruption
conditions, so the negative entropy result becomes a true 3-seed mean.

Corrupted feature caches are seed-independent (corruption is applied to frames
before backbone extraction), so NO re-extraction is needed — only adaptation +
scoring with the s123/s2024 checkpoints. All 12 source checkpoints already exist.

New seeds write to:  results/_tta_rerun_continual/<bb>/{method}_s<seed>/<corr>_<sev>/
(the bare {source,tent,sar}/ dirs are the existing seed-42 runs.)

Resumable: a condition whose eval_metrics.json already exists is skipped.

Usage:
    python scripts/run_tta_seeds_m2.py                 # full 2-seed grid + aggregate
    python scripts/run_tta_seeds_m2.py --smoke         # 1 bb / source_only / gaussian_1 (timing probe)
    python scripts/run_tta_seeds_m2.py --aggregate-only # recompute the 3-seed table from existing files
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.tta.evaluate_tta import (  # noqa: E402
    run_tta_evaluation,
    CORRUPTION_TYPES,
    BACKBONE_FEATURE_PREFIX,
)

BACKBONES = ["clip-vit-b-16", "siglip2-base", "siglip2-so400m", "siglip2-giant"]
# backbone -> gated-fusion source-run name suffix (run = ucf_gated_fusion{suffix}_s{seed})
SUFFIX = {
    "clip-vit-b-16": "",
    "siglip2-base": "_siglip2",
    "siglip2-so400m": "_so400m",
    "siglip2-giant": "_giant",
}
SEVERITIES = [1, 2, 3, 4, 5]
METHODS = ["source_only", "tent", "sar"]
OUT_ROOT = _ROOT / "results" / "_tta_rerun_continual"
FEATURE_ROOT = Path("E:/features/ucf")
LR = 1e-3
RHO = 0.05


def _method_dir(bb: str, method: str, seed: int) -> Path:
    """Existing s42 dirs are bare ({source,tent,sar}); new seeds are {method}_s{seed}.

    Note the existing seed-42 source-only dir is named 'source' (not 'source_only').
    """
    if seed == 42:
        name = "source" if method == "source_only" else method
    else:
        name = f"{method}_s{seed}"
    return OUT_ROOT / bb / name


def _read_auc(path: Path):
    f = path / "eval_metrics.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())["auc"] * 100.0


def run_grid(seeds, backbones, methods, conditions, smoke: bool):
    jobs = []
    for bb in backbones:
        for seed in seeds:
            src_run = _ROOT / "results" / f"ucf_gated_fusion{SUFFIX[bb]}_s{seed}"
            if not (src_run / "best_model.pth").exists():
                print(f"!! MISSING checkpoint {src_run} — skipping bb={bb} seed={seed}")
                continue
            for method in methods:
                for (corr, sev) in conditions:
                    jobs.append((bb, seed, src_run, method, corr, sev))

    total = len(jobs)
    print(f"== M2 continual grid: {total} condition-runs "
          f"(seeds={seeds} backbones={len(backbones)} methods={methods} "
          f"conditions={len(conditions)}) ==", flush=True)
    t_all = time.time()
    done = skipped = 0
    for i, (bb, seed, src_run, method, corr, sev) in enumerate(jobs, 1):
        out_dir = _method_dir(bb, method, seed) / f"{corr}_{sev}"
        if (out_dir / "eval_metrics.json").exists():
            skipped += 1
            continue
        t0 = time.time()
        run_tta_evaluation(
            source_run=src_run,
            corruption_type=corr,
            severity=sev,
            method=method,
            lr=LR,
            rho=RHO,
            output_dir=out_dir.resolve(),
            feature_root=FEATURE_ROOT,
            backbone=bb,
            protocol="continual",
        )
        done += 1
        dt = time.time() - t0
        auc = _read_auc(out_dir)
        print(f"[{i}/{total}] {bb} s{seed} {method:11s} {corr}_{sev}  "
              f"AUC={auc:.3f}  ({dt:.1f}s)", flush=True)
        if smoke:
            break
    print(f"== grid done: {done} ran, {skipped} already-present, "
          f"{(time.time()-t_all)/60:.1f} min ==", flush=True)


def aggregate(seeds_all):
    """3-seed per-backbone mean entropy delta vs source over 20 conditions.

    Writes results/_tta_rerun_continual/summary_3seed.json (committed provenance
    for the paper's '<0.1pp on every backbone' / 'three seeds' TENT/SAR claim).
    """
    conditions = [(c, s) for c in CORRUPTION_TYPES for s in SEVERITIES]
    print("\n== 3-seed continual entropy comparison (mean AUC% over 20 conditions) ==")
    header = f"{'backbone':16s} {'seed':>5s} {'source':>8s} {'tent':>8s} {'sar':>8s} {'dTENT':>7s} {'dSAR':>7s}"
    print(header)
    print("-" * len(header))
    rows = {}
    out_json = {}
    for bb in BACKBONES:
        per_seed = {}
        for seed in seeds_all:
            aucs = {}
            ok = True
            for method in METHODS:
                mdir = _method_dir(bb, method, seed)
                vals = [_read_auc(mdir / f"{c}_{s}") for (c, s) in conditions]
                if any(v is None for v in vals):
                    ok = False
                    break
                aucs[method] = sum(vals) / len(vals)
            if not ok:
                print(f"{bb:16s} s{seed:<4d}  (incomplete — missing conditions)")
                continue
            d_tent = aucs["tent"] - aucs["source_only"]
            d_sar = aucs["sar"] - aucs["source_only"]
            per_seed[seed] = (aucs["source_only"], aucs["tent"], aucs["sar"], d_tent, d_sar)
            print(f"{bb:16s} s{seed:<4d} {aucs['source_only']:8.3f} {aucs['tent']:8.3f} "
                  f"{aucs['sar']:8.3f} {d_tent:+7.3f} {d_sar:+7.3f}")
        if per_seed:
            n = len(per_seed)
            mt = sum(v[3] for v in per_seed.values()) / n
            ms = sum(v[4] for v in per_seed.values()) / n
            m_src = sum(v[0] for v in per_seed.values()) / n
            m_tent = sum(v[1] for v in per_seed.values()) / n
            m_sar = sum(v[2] for v in per_seed.values()) / n
            rows[bb] = (n, mt, ms)
            out_json[bb] = {
                "seeds": {str(s): {"source": v[0], "tent": v[1], "sar": v[2],
                                   "dTENT": v[3], "dSAR": v[4]}
                          for s, v in per_seed.items()},
                "mean": {"source": m_src, "tent": m_tent, "sar": m_sar,
                         "dTENT": mt, "dSAR": ms, "n_seeds": n},
            }
            print(f"{bb:16s} {'MEAN':>5s} {m_src:8.3f} {m_tent:8.3f} {m_sar:8.3f} "
                  f"{mt:+7.3f} {ms:+7.3f}  ({n}-seed)")
        print()
    # verdict
    print("== verdict: does '<0.1pp on every backbone' hold as a 3-seed mean? ==")
    worst = 0.0
    for bb, (n, mt, ms) in rows.items():
        worst = max(worst, abs(mt), abs(ms))
        flag = "OK" if max(abs(mt), abs(ms)) < 0.1 else "!! >=0.1pp"
        print(f"  {bb:16s} ({n}-seed)  |dTENT|={abs(mt):.3f}  |dSAR|={abs(ms):.3f}   {flag}")
    print(f"  WORST |delta| across all backbones = {worst:.3f} pp  "
          f"({'HOLDS' if worst < 0.1 else 'DOES NOT HOLD'} < 0.1pp claim)")
    out_path = OUT_ROOT / "summary_3seed.json"
    out_path.write_text(json.dumps(out_json, indent=2))
    print(f"\nwrote {out_path}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="123,2024")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--aggregate-only", action="store_true")
    args = ap.parse_args()

    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    conditions = [(c, s) for c in CORRUPTION_TYPES for s in SEVERITIES]

    if args.smoke:
        run_grid([seeds[0]], ["clip-vit-b-16"], ["source_only"],
                 [("gaussian_noise", 1)], smoke=True)
        return

    if not args.aggregate_only:
        run_grid(seeds, BACKBONES, METHODS, conditions, smoke=False)

    aggregate([42] + seeds)


if __name__ == "__main__":
    main()
