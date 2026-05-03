"""Benchmark all 5 ViolenceCC model variants: params, FLOPs, latency, throughput, GPU memory.

Produces console table, LaTeX table (booktabs), and CSV for thesis inclusion.

Usage:
    conda run -n vcc-main python scripts/benchmark_models.py
    conda run -n vcc-main python scripts/benchmark_models.py --num-warmup 5 --num-bench 10
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence, Tuple

# Project root on sys.path so `from src.models...` works.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _PROJECT_ROOT)

import torch
import torch.nn as nn

from src.models.registry import build_model

# ---------------------------------------------------------------------------
# Display names for thesis readability
# ---------------------------------------------------------------------------
DISPLAY_NAMES: Dict[str, str] = {
    "skeleton_only": "Skeleton-Only",
    "clip_only": "CLIP-Only",
    "late_fusion": "Late Fusion",
    "gated_fusion": "Gated Fusion",
    "rtfm_i3d": "RTFM-I3D",
}

# Ordered list of variants to benchmark
VARIANT_ORDER: List[str] = [
    "skeleton_only",
    "clip_only",
    "late_fusion",
    "gated_fusion",
    "rtfm_i3d",
]

# ---------------------------------------------------------------------------
# Default constants
# ---------------------------------------------------------------------------
BATCH_SIZE = 16
T = 32
SKEL_DIM = 256
CLIP_DIM = 1024
I3D_DIM = 1024


# ---------------------------------------------------------------------------
# Input factories: produce forward-call kwargs for each variant
# ---------------------------------------------------------------------------
def _make_input_factories(B: int, device: torch.device) -> Dict[str, Callable[[], Dict[str, torch.Tensor]]]:
    """Return a dict mapping variant -> callable that produces forward kwargs."""
    return {
        "skeleton_only": lambda: dict(skel=torch.randn(B, T, SKEL_DIM, device=device)),
        "clip_only": lambda: dict(clip=torch.randn(B, T, CLIP_DIM, device=device)),
        "late_fusion": lambda: dict(
            skel=torch.randn(B, T, SKEL_DIM, device=device),
            clip=torch.randn(B, T, CLIP_DIM, device=device),
        ),
        "gated_fusion": lambda: dict(
            skel=torch.randn(B, T, SKEL_DIM, device=device),
            clip=torch.randn(B, T, CLIP_DIM, device=device),
        ),
        "rtfm_i3d": lambda: dict(i3d=torch.randn(B, T, I3D_DIM, device=device)),
    }


# ---------------------------------------------------------------------------
# thop wrapper: adapts keyword-arg models to positional-arg interface
# ---------------------------------------------------------------------------
class _ThopWrapper(nn.Module):
    """Thin wrapper so thop.profile() can call model with positional tensors."""

    def __init__(self, model: nn.Module, input_keys: Sequence[str]) -> None:
        super().__init__()
        self.model = model
        self.input_keys = list(input_keys)

    def forward(self, *args: torch.Tensor) -> torch.Tensor:
        kwargs = dict(zip(self.input_keys, args))
        return self.model(**kwargs)


def _thop_inputs(variant: str, device: torch.device) -> Tuple[Sequence[str], Tuple[torch.Tensor, ...]]:
    """Return (key_names, positional_tensors) for thop.profile().

    Uses batch=1 for FLOPs counting (standard practice -- FLOPs are per-sample).
    """
    if variant == "skeleton_only":
        keys = ["skel"]
        tensors = (torch.randn(1, T, SKEL_DIM, device=device),)
    elif variant == "clip_only":
        keys = ["clip"]
        tensors = (torch.randn(1, T, CLIP_DIM, device=device),)
    elif variant in ("late_fusion", "gated_fusion"):
        keys = ["skel", "clip"]
        tensors = (
            torch.randn(1, T, SKEL_DIM, device=device),
            torch.randn(1, T, CLIP_DIM, device=device),
        )
    elif variant == "rtfm_i3d":
        keys = ["i3d"]
        tensors = (torch.randn(1, T, I3D_DIM, device=device),)
    else:
        raise ValueError(f"Unknown variant: {variant}")
    return keys, tensors


# ---------------------------------------------------------------------------
# Core benchmark function
# ---------------------------------------------------------------------------
def benchmark_one(
    variant: str,
    model: nn.Module,
    input_factory: Callable[[], Dict[str, torch.Tensor]],
    device: torch.device,
    num_warmup: int,
    num_bench: int,
    batch_size: int,
) -> Dict[str, Any]:
    """Benchmark a single model variant. Returns metrics dict."""
    results: Dict[str, Any] = {"variant": variant, "display": DISPLAY_NAMES[variant]}

    # ---- Parameters ----
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    results["total_params"] = total_params
    results["trainable_params"] = trainable_params
    results["params_k"] = total_params / 1_000

    # ---- FLOPs / MACs via thop ----
    try:
        from thop import profile as thop_profile

        keys, tensors = _thop_inputs(variant, device)
        wrapper = _ThopWrapper(model, keys)
        wrapper.eval()
        macs, _ = thop_profile(wrapper, inputs=tensors, verbose=False)
        results["macs_m"] = macs / 1e6
        results["flops_m"] = (2 * macs) / 1e6
    except Exception as e:
        print(f"  WARNING: thop failed for {variant}: {e}")
        results["macs_m"] = float("nan")
        results["flops_m"] = float("nan")

    # ---- Peak GPU memory ----
    if device.type == "cuda":
        # Clean slate
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
        inputs = input_factory()
        with torch.no_grad():
            _ = model(**inputs)
        torch.cuda.synchronize(device)
        peak_mb = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
        results["peak_gpu_mb"] = peak_mb
    else:
        results["peak_gpu_mb"] = float("nan")

    # ---- Latency & Throughput ----
    model.eval()
    with torch.no_grad():
        # Warmup
        for _ in range(num_warmup):
            inputs = input_factory()
            _ = model(**inputs)

        if device.type == "cuda":
            torch.cuda.synchronize(device)

        t_start = time.perf_counter()
        for _ in range(num_bench):
            inputs = input_factory()
            _ = model(**inputs)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        t_end = time.perf_counter()

    total_s = t_end - t_start
    latency_ms = (total_s / num_bench) * 1000
    per_sample_ms = latency_ms / batch_size
    throughput = batch_size / (total_s / num_bench)

    results["latency_ms"] = latency_ms
    results["per_sample_ms"] = per_sample_ms
    results["throughput"] = throughput

    return results


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------
def print_console_table(all_results: List[Dict[str, Any]]) -> None:
    """Print a formatted console table."""
    header = (
        f"{'Model':<16} | {'Params (K)':>11} | {'MACs (M)':>10} | {'FLOPs (M)':>10} | "
        f"{'Lat (ms/B)':>11} | {'Lat (ms/S)':>11} | {'Tput (S/s)':>12} | {'GPU (MB)':>10}"
    )
    sep = "-" * len(header)

    print()
    print(sep)
    print(header)
    print(sep)
    for r in all_results:
        gpu_str = f"{r['peak_gpu_mb']:.1f}" if not _isnan(r["peak_gpu_mb"]) else "N/A"
        macs_str = f"{r['macs_m']:.2f}" if not _isnan(r["macs_m"]) else "N/A"
        flops_str = f"{r['flops_m']:.2f}" if not _isnan(r["flops_m"]) else "N/A"
        print(
            f"{r['display']:<16} | {r['params_k']:>11.2f} | {macs_str:>10} | {flops_str:>10} | "
            f"{r['latency_ms']:>11.3f} | {r['per_sample_ms']:>11.4f} | {r['throughput']:>12.1f} | {gpu_str:>10}"
        )
    print(sep)
    print()


def print_latex_table(all_results: List[Dict[str, Any]]) -> None:
    """Print a LaTeX booktabs table ready for thesis copy-paste."""
    print("% --- LaTeX table (copy-paste into thesis) ---")
    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{Model complexity comparison across ViolenceCC variants.}")
    print(r"\label{tab:model-complexity}")
    print(r"\begin{tabular}{lrrrrr}")
    print(r"\toprule")
    print(r"Model & Params (K) & MACs (M) & Latency (ms) & Throughput (S/s) & Mem (MB) \\")
    print(r"\midrule")
    for r in all_results:
        gpu_str = f"{r['peak_gpu_mb']:.1f}" if not _isnan(r["peak_gpu_mb"]) else "---"
        macs_str = f"{r['macs_m']:.2f}" if not _isnan(r["macs_m"]) else "---"
        name_escaped = r["display"].replace("-", "{-}")
        print(
            f"{name_escaped} & {r['params_k']:.2f} & {macs_str} & "
            f"{r['latency_ms']:.3f} & {r['throughput']:.1f} & {gpu_str} \\\\"
        )
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")
    print("% --- end LaTeX table ---")
    print()


def write_csv(all_results: List[Dict[str, Any]], csv_path: str) -> None:
    """Write benchmark results to CSV."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    fieldnames = [
        "model", "total_params", "trainable_params", "params_k",
        "macs_m", "flops_m", "latency_ms_batch", "latency_ms_sample",
        "throughput_samples_s", "peak_gpu_mb",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_results:
            writer.writerow({
                "model": r["display"],
                "total_params": r["total_params"],
                "trainable_params": r["trainable_params"],
                "params_k": f"{r['params_k']:.2f}",
                "macs_m": f"{r['macs_m']:.2f}" if not _isnan(r["macs_m"]) else "",
                "flops_m": f"{r['flops_m']:.2f}" if not _isnan(r["flops_m"]) else "",
                "latency_ms_batch": f"{r['latency_ms']:.3f}",
                "latency_ms_sample": f"{r['per_sample_ms']:.4f}",
                "throughput_samples_s": f"{r['throughput']:.1f}",
                "peak_gpu_mb": f"{r['peak_gpu_mb']:.1f}" if not _isnan(r["peak_gpu_mb"]) else "",
            })
    print(f"CSV saved to: {csv_path}")


def _isnan(v: float) -> bool:
    """Check for NaN without importing math."""
    return v != v


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark all 5 ViolenceCC model variants."
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help=f"Batch size for latency/throughput (default {BATCH_SIZE})")
    parser.add_argument("--num-warmup", type=int, default=50,
                        help="GPU warmup iterations before timing (default 50)")
    parser.add_argument("--num-bench", type=int, default=200,
                        help="Timed iterations for latency/throughput (default 200)")
    parser.add_argument("--cpu", action="store_true",
                        help="Run on CPU (skip GPU memory measurement)")
    parser.add_argument("--no-latex", action="store_true",
                        help="Suppress LaTeX table output")
    parser.add_argument("--no-csv", action="store_true",
                        help="Suppress CSV output")
    args = parser.parse_args()

    # Device selection
    if args.cpu:
        device = torch.device("cpu")
    else:
        assert torch.cuda.is_available(), (
            "CUDA not available. Use --cpu flag to benchmark on CPU."
        )
        device = torch.device("cuda")

    # Reproducibility header
    print("=" * 72)
    print("ViolenceCC Model Benchmark")
    print("=" * 72)
    print(f"PyTorch version : {torch.__version__}")
    if device.type == "cuda":
        print(f"CUDA version    : {torch.version.cuda}")
        print(f"GPU             : {torch.cuda.get_device_name(0)}")
    print(f"Device          : {device}")
    print(f"Batch size      : {args.batch_size}")
    print(f"Sequence length : {T}")
    print(f"Warmup iters    : {args.num_warmup}")
    print(f"Bench iters     : {args.num_bench}")
    print("=" * 72)

    input_factories = _make_input_factories(args.batch_size, device)
    all_results: List[Dict[str, Any]] = []

    for variant in VARIANT_ORDER:
        print(f"\nBenchmarking: {DISPLAY_NAMES[variant]} ({variant}) ...")
        model = build_model(variant)
        model = model.to(device)
        model.eval()

        result = benchmark_one(
            variant=variant,
            model=model,
            input_factory=input_factories[variant],
            device=device,
            num_warmup=args.num_warmup,
            num_bench=args.num_bench,
            batch_size=args.batch_size,
        )
        all_results.append(result)

        # Free GPU memory between variants
        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()

    # Output
    print_console_table(all_results)

    if not args.no_latex:
        print_latex_table(all_results)

    if not args.no_csv:
        csv_path = os.path.join(_PROJECT_ROOT, "results", "benchmark_models.csv")
        write_csv(all_results, csv_path)

    print("Benchmark complete.")


if __name__ == "__main__":
    main()
