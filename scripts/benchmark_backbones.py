"""Benchmark backbone feature extractors across all 3 ViolenceCC conda environments.

Measures REAL computational cost of each feature extractor backbone:
  - CLIP ViT-B/16 (vcc-main)
  - RTMPose-m + YOLOX (vcc-skeleton)
  - CTR-GCN 4-stream (vcc-ctrgcn)
  - I3D RGB (published numbers only)

Each component writes a JSON result file. The --combine mode reads all JSON files
and produces a unified comparison table (console + LaTeX + CSV) for thesis inclusion.

Usage:
    # Individual components (each in its own conda env):
    C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --clip
    C:/Anaconda/envs/vcc-skeleton/python.exe scripts/benchmark_backbones.py --rtmpose
    C:/Anaconda/envs/vcc-ctrgcn/python.exe scripts/benchmark_backbones.py --ctrgcn

    # Combined table (reads JSON files):
    C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --combine

    # All-in-one (shells out to each env, then combines):
    C:/Anaconda/envs/vcc-main/python.exe scripts/benchmark_backbones.py --all
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root on sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _PROJECT_ROOT)

_RESULTS_DIR = os.path.join(_PROJECT_ROOT, "results")

# Direct python exe paths for cross-env execution (avoids conda run cp950 issues)
_ENV_PYTHON = {
    "vcc-main": "C:/Anaconda/envs/vcc-main/python.exe",
    "vcc-skeleton": "C:/Anaconda/envs/vcc-skeleton/python.exe",
    "vcc-ctrgcn": "C:/Anaconda/envs/vcc-ctrgcn/python.exe",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _isnan(v: float) -> bool:
    """Check for NaN without importing math."""
    return v != v


def _get_gpu_name() -> str:
    """Get GPU name via nvidia-smi (works in any env)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return "Unknown GPU"


def _get_gpu_memory_used_mb() -> Optional[float]:
    """Query current GPU memory used (MB) via nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return float(result.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return None


def _make_system_info(env_name: str) -> Dict[str, str]:
    """Gather system info that works in any env."""
    info: Dict[str, str] = {"gpu": _get_gpu_name()}
    try:
        import torch
        info["pytorch_version"] = torch.__version__
        info["cuda_version"] = str(torch.version.cuda) if torch.cuda.is_available() else "N/A"
    except ImportError:
        info["pytorch_version"] = "N/A"
        info["cuda_version"] = "N/A"
    info["env"] = env_name
    return info


def _write_json(data: Dict[str, Any], path: str) -> None:
    """Write JSON result file with makedirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"JSON saved to: {path}")


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    """Read JSON, return None if missing."""
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Component: CLIP ViT-B/16
# ---------------------------------------------------------------------------

def _bench_clip(args: argparse.Namespace) -> None:
    """Benchmark CLIP ViT-B/16 visual encoder (vcc-main env)."""
    import torch
    import torch.nn as nn

    # Lazy import: only in vcc-main
    import open_clip

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[CLIP] Loading model on {device}...")

    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-16", pretrained="openai"
    )
    model.eval().to(device)

    B = args.batch_size

    # --- Parameters (visual encoder only) ---
    total_params = sum(p.numel() for p in model.visual.parameters())
    params_m = total_params / 1e6
    print(f"[CLIP] Visual encoder params: {params_m:.2f}M")

    # --- FLOPs via thop ---
    flops_g = float("nan")
    try:
        from thop import profile as thop_profile

        class _ClipVisualWrapper(nn.Module):
            def __init__(self, clip_model):
                super().__init__()
                self.clip_model = clip_model

            def forward(self, x):
                return self.clip_model.encode_image(x)

        wrapper = _ClipVisualWrapper(model)
        wrapper.eval()
        dummy = torch.randn(1, 3, 224, 224).to(device)
        macs, _ = thop_profile(wrapper, inputs=(dummy,), verbose=False)
        flops_g = (2 * macs) / 1e9
        print(f"[CLIP] FLOPs: {flops_g:.2f} GFLOPs (from thop)")
    except Exception as e:
        print(f"[CLIP] WARNING: thop failed: {e}")

    # --- Peak GPU memory ---
    peak_gpu_mb = float("nan")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
        dummy_batch = torch.randn(B, 3, 224, 224, device=device)
        with torch.no_grad():
            _ = model.encode_image(dummy_batch)
        torch.cuda.synchronize(device)
        peak_gpu_mb = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
        print(f"[CLIP] Peak GPU memory (B={B}): {peak_gpu_mb:.1f} MB")
        del dummy_batch
        torch.cuda.empty_cache()

    # --- Latency / Throughput ---
    print(f"[CLIP] Warmup ({args.num_warmup} iters)...")
    with torch.no_grad():
        for _ in range(args.num_warmup):
            dummy_batch = torch.randn(B, 3, 224, 224, device=device)
            _ = model.encode_image(dummy_batch)

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    print(f"[CLIP] Benchmarking ({args.num_bench} iters, B={B})...")
    latencies = []
    with torch.no_grad():
        for _ in range(args.num_bench):
            dummy_batch = torch.randn(B, 3, 224, 224, device=device)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            t0 = time.perf_counter()
            _ = model.encode_image(dummy_batch)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)  # ms

    import numpy as np
    lat_arr = np.array(latencies)
    mean_ms = float(lat_arr.mean())
    p50_ms = float(np.median(lat_arr))
    p95_ms = float(np.percentile(lat_arr, 95))
    per_frame_ms = mean_ms / B
    throughput_fps = B / (mean_ms / 1000)

    print(f"[CLIP] Latency: mean={mean_ms:.2f}ms p50={p50_ms:.2f}ms p95={p95_ms:.2f}ms (batch={B})")
    print(f"[CLIP] Per-frame: {per_frame_ms:.3f} ms  Throughput: {throughput_fps:.1f} frames/s")

    # --- Write JSON ---
    result = {
        "backbone": "CLIP ViT-B/16",
        "env": "vcc-main",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "batch_size": B,
            "num_warmup": args.num_warmup,
            "num_bench": args.num_bench,
            "input_shape": [B, 3, 224, 224],
        },
        "metrics": {
            "params_m": round(params_m, 2),
            "params_source": "measured",
            "flops_g": round(flops_g, 2) if not _isnan(flops_g) else None,
            "flops_source": "measured",
            "latency_ms_batch_mean": round(mean_ms, 2),
            "latency_ms_batch_p50": round(p50_ms, 2),
            "latency_ms_batch_p95": round(p95_ms, 2),
            "latency_ms_per_frame": round(per_frame_ms, 3),
            "throughput_fps": round(throughput_fps, 1),
            "peak_gpu_mb": round(peak_gpu_mb, 1) if not _isnan(peak_gpu_mb) else None,
            "gpu_mem_source": "torch.cuda.max_memory_allocated",
        },
        "system": _make_system_info("vcc-main"),
    }

    json_path = os.path.join(_RESULTS_DIR, "backbone_bench_clip.json")
    _write_json(result, json_path)


# ---------------------------------------------------------------------------
# Component: RTMPose-m + YOLOX
# ---------------------------------------------------------------------------

def _bench_rtmpose(args: argparse.Namespace) -> None:
    """Benchmark RTMPose-m + YOLOX detection+pose pipeline (vcc-skeleton env)."""
    # cuDNN PATH fix REQUIRED before any imports
    _CUDNN_PATH = r"C:\Program Files\NVIDIA\CUDNN\v9.8\bin\12.8"
    if _CUDNN_PATH not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _CUDNN_PATH + ";" + os.environ.get("PATH", "")

    import numpy as np
    # Lazy import: only in vcc-skeleton
    from rtmlib import Body

    print("[RTMPose] Loading model (mode='balanced', backend='onnxruntime', device='cuda')...")
    model = Body(mode="balanced", backend="onnxruntime", device="cuda")

    # --- Published parameters and FLOPs ---
    # RTMPose-m: ~4M params, 2.22 GFLOPs
    # YOLOX-m: ~9M params, ~1.0 GFLOPs
    params_m = 13.0   # approximate total
    flops_g = 3.22    # approximate total (YOLOX ~1.0 + RTMPose-m 2.22)

    print(f"[RTMPose] Published params: ~{params_m}M  FLOPs: ~{flops_g} GFLOPs")

    # --- GPU memory (before/after via nvidia-smi) ---
    mem_before = _get_gpu_memory_used_mb()

    # Dummy frame: 480x640 BGR uint8 (typical video resolution)
    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Warmup
    print(f"[RTMPose] Warmup ({args.num_warmup} frames)...")
    for _ in range(args.num_warmup):
        _ = model(dummy_frame)

    mem_after = _get_gpu_memory_used_mb()
    gpu_mem_delta = None
    if mem_before is not None and mem_after is not None:
        gpu_mem_delta = mem_after - mem_before
        print(f"[RTMPose] GPU memory delta: {gpu_mem_delta:.0f} MB ({mem_before:.0f} -> {mem_after:.0f})")
    else:
        print("[RTMPose] GPU memory: N/A (nvidia-smi query failed)")

    # --- Latency (per-frame, no batching) ---
    print(f"[RTMPose] Benchmarking ({args.num_bench} frames)...")
    latencies = []
    for _ in range(args.num_bench):
        # Fresh random frame each iteration (realistic)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        t0 = time.perf_counter()
        _ = model(frame)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    lat_arr = np.array(latencies)
    mean_ms = float(lat_arr.mean())
    p50_ms = float(np.median(lat_arr))
    p95_ms = float(np.percentile(lat_arr, 95))
    throughput_fps = 1000.0 / mean_ms

    print(f"[RTMPose] Latency: mean={mean_ms:.2f}ms p50={p50_ms:.2f}ms p95={p95_ms:.2f}ms")
    print(f"[RTMPose] Throughput: {throughput_fps:.1f} frames/s")

    # --- Write JSON ---
    result = {
        "backbone": "RTMPose-m + YOLOX",
        "env": "vcc-skeleton",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "batch_size": 1,
            "num_warmup": args.num_warmup,
            "num_bench": args.num_bench,
            "input_shape": [1, 480, 640, 3],
            "note": "Single-frame inference (no batch support in rtmlib)",
        },
        "metrics": {
            "params_m": params_m,
            "params_source": "published",
            "flops_g": flops_g,
            "flops_source": "published (YOLOX ~1.0 + RTMPose-m 2.22)",
            "latency_ms_per_frame_mean": round(mean_ms, 2),
            "latency_ms_per_frame_p50": round(p50_ms, 2),
            "latency_ms_per_frame_p95": round(p95_ms, 2),
            "latency_ms_per_frame": round(mean_ms, 2),
            "throughput_fps": round(throughput_fps, 1),
            "peak_gpu_mb": round(gpu_mem_delta, 1) if gpu_mem_delta is not None else None,
            "gpu_mem_source": "nvidia-smi delta" if gpu_mem_delta is not None else "N/A",
        },
        "system": _make_system_info("vcc-skeleton"),
    }

    json_path = os.path.join(_RESULTS_DIR, "backbone_bench_rtmpose.json")
    _write_json(result, json_path)


# ---------------------------------------------------------------------------
# Component: CTR-GCN 4-stream
# ---------------------------------------------------------------------------

def _bench_ctrgcn(args: argparse.Namespace) -> None:
    """Benchmark CTR-GCN 4-stream backbone (vcc-ctrgcn env)."""
    import torch
    import numpy as np

    # Lazy imports: only in vcc-ctrgcn
    from mmcv import Config
    from pyskl.models import build_model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Stream config (same as extract_ctrgcn.py)
    CONFIG_DIR = Path("D:/libs/pyskl/configs/ctrgcn/ctrgcn_pyskl_ntu120_xsub_hrnet")
    WEIGHT_DIR = Path("D:/ViolenceCC/data/weights/ctrgcn")
    STREAMS = {
        "j":  {"config": "j.py",  "weight": "j.pth",  "w": 1.0},
        "b":  {"config": "b.py",  "weight": "b.pth",  "w": 1.0},
        "jm": {"config": "jm.py", "weight": "jm.pth", "w": 0.5},
        "bm": {"config": "bm.py", "weight": "bm.pth", "w": 0.5},
    }

    # Load all 4 streams
    models = {}
    stream_params = {}
    for name, info in STREAMS.items():
        cfg_path = str(CONFIG_DIR / info["config"])
        weight_path = str(WEIGHT_DIR / info["weight"])
        print(f"[CTR-GCN] Loading stream '{name}' from {weight_path}...")

        cfg = Config.fromfile(cfg_path)
        model = build_model(cfg.model)

        checkpoint = torch.load(weight_path, map_location="cpu")
        state_dict = (
            checkpoint
            if isinstance(checkpoint, dict) and "backbone" in str(list(checkpoint.keys())[:1])
            else checkpoint.get("state_dict", checkpoint)
        )
        model.load_state_dict(state_dict, strict=False)
        model.eval().to(device)
        models[name] = model

        # Count params (backbone only, exclude cls_head)
        backbone_params = sum(p.numel() for p in model.backbone.parameters())
        stream_params[name] = backbone_params
        print(f"[CTR-GCN]   {name}: {backbone_params / 1e6:.3f}M backbone params")

    total_params = sum(stream_params.values())
    params_m = total_params / 1e6
    print(f"[CTR-GCN] Total 4-stream backbone params: {params_m:.2f}M")

    # --- FLOPs via thop per stream ---
    stream_flops = {}
    total_flops_g = 0.0
    flops_failed = False
    # Input shape: [N=1, M=2, T=64, V=17, C=2]
    dummy_input = torch.randn(1, 2, 64, 17, 2, device=device)

    for name, model in models.items():
        try:
            from thop import profile as thop_profile
            import torch.nn as nn

            class _BackboneWrapper(nn.Module):
                def __init__(self, backbone):
                    super().__init__()
                    self.backbone = backbone

                def forward(self, x):
                    return self.backbone(x)

            wrapper = _BackboneWrapper(model.backbone)
            wrapper.eval()
            macs, _ = thop_profile(wrapper, inputs=(dummy_input,), verbose=False)
            gflops = (2 * macs) / 1e9
            stream_flops[name] = gflops
            total_flops_g += gflops
            print(f"[CTR-GCN]   {name}: {gflops:.3f} GFLOPs")
        except Exception as e:
            print(f"[CTR-GCN]   WARNING: thop failed for {name}: {e}")
            stream_flops[name] = None
            flops_failed = True

    if flops_failed:
        total_flops_g = float("nan")
    print(f"[CTR-GCN] Total 4-stream FLOPs: {total_flops_g:.2f} GFLOPs" if not _isnan(total_flops_g) else "[CTR-GCN] Total FLOPs: N/A (thop failed)")

    # --- Peak GPU memory ---
    peak_gpu_mb = float("nan")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
        with torch.no_grad():
            for name, model in models.items():
                out = model.backbone(dummy_input)
                feat = out.mean(dim=[1, 3, 4])
        torch.cuda.synchronize(device)
        peak_gpu_mb = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
        print(f"[CTR-GCN] Peak GPU memory (4-stream): {peak_gpu_mb:.1f} MB")

    # --- Latency: full 4-stream pass ---
    print(f"[CTR-GCN] Warmup ({args.num_warmup} iters, full 4-stream)...")
    with torch.no_grad():
        for _ in range(args.num_warmup):
            for name, model in models.items():
                x = torch.randn(1, 2, 64, 17, 2, device=device)
                out = model.backbone(x)
                feat = out.mean(dim=[1, 3, 4])

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    print(f"[CTR-GCN] Benchmarking ({args.num_bench} iters, full 4-stream)...")
    latencies_total = []
    latencies_per_stream = {name: [] for name in STREAMS}

    with torch.no_grad():
        for _ in range(args.num_bench):
            if device.type == "cuda":
                torch.cuda.synchronize(device)

            t_total_start = time.perf_counter()
            for name, model in models.items():
                x = torch.randn(1, 2, 64, 17, 2, device=device)
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                t0 = time.perf_counter()
                out = model.backbone(x)
                feat = out.mean(dim=[1, 3, 4])
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                t1 = time.perf_counter()
                latencies_per_stream[name].append((t1 - t0) * 1000)

            if device.type == "cuda":
                torch.cuda.synchronize(device)
            t_total_end = time.perf_counter()
            latencies_total.append((t_total_end - t_total_start) * 1000)

    lat_total = np.array(latencies_total)
    mean_ms = float(lat_total.mean())
    p50_ms = float(np.median(lat_total))
    p95_ms = float(np.percentile(lat_total, 95))
    throughput_snippets = 1000.0 / mean_ms

    print(f"[CTR-GCN] 4-stream latency: mean={mean_ms:.2f}ms p50={p50_ms:.2f}ms p95={p95_ms:.2f}ms")
    print(f"[CTR-GCN] Throughput: {throughput_snippets:.1f} snippets/s")

    per_stream_stats = {}
    for name in STREAMS:
        arr = np.array(latencies_per_stream[name])
        per_stream_stats[name] = {
            "mean_ms": round(float(arr.mean()), 2),
            "p50_ms": round(float(np.median(arr)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2),
        }
        print(f"[CTR-GCN]   {name}: mean={arr.mean():.2f}ms")

    # --- Write JSON ---
    result = {
        "backbone": "CTR-GCN (4-stream)",
        "env": "vcc-ctrgcn",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "batch_size": 1,
            "num_warmup": args.num_warmup,
            "num_bench": args.num_bench,
            "input_shape": [1, 2, 64, 17, 2],
            "streams": list(STREAMS.keys()),
            "stream_weights": {k: v["w"] for k, v in STREAMS.items()},
        },
        "metrics": {
            "params_m": round(params_m, 3),
            "params_per_stream_m": {k: round(v / 1e6, 3) for k, v in stream_params.items()},
            "params_source": "measured (backbone only, excl. cls_head)",
            "flops_g": round(total_flops_g, 3) if not _isnan(total_flops_g) else None,
            "flops_per_stream_g": {k: round(v, 3) if v is not None else None for k, v in stream_flops.items()},
            "flops_source": "measured (thop)" if not flops_failed else "partial (thop failed on some streams)",
            "latency_ms_4stream_mean": round(mean_ms, 2),
            "latency_ms_4stream_p50": round(p50_ms, 2),
            "latency_ms_4stream_p95": round(p95_ms, 2),
            "latency_per_stream": per_stream_stats,
            "latency_ms_per_snippet": round(mean_ms, 2),
            "throughput_snippets_s": round(throughput_snippets, 1),
            "peak_gpu_mb": round(peak_gpu_mb, 1) if not _isnan(peak_gpu_mb) else None,
            "gpu_mem_source": "torch.cuda.max_memory_allocated",
        },
        "system": _make_system_info("vcc-ctrgcn"),
    }

    json_path = os.path.join(_RESULTS_DIR, "backbone_bench_ctrgcn.json")
    _write_json(result, json_path)


# ---------------------------------------------------------------------------
# I3D published row (hardcoded)
# ---------------------------------------------------------------------------

def _i3d_published() -> Dict[str, Any]:
    """Return I3D RGB published numbers (Carreira & Zisserman, 2017)."""
    return {
        "backbone": "I3D RGB",
        "env": "N/A (pre-extracted features)",
        "timestamp": None,
        "config": {
            "note": "Published numbers from Carreira & Zisserman, 'Quo Vadis, Action Recognition?' (2017)",
        },
        "metrics": {
            "params_m": 25.0,
            "params_source": "published",
            "flops_g": 107.9,
            "flops_source": "published (per clip)",
            "latency_ms_per_frame": None,
            "throughput_fps": None,
            "peak_gpu_mb": None,
            "gpu_mem_source": "N/A",
        },
        "system": {"note": "Pre-extracted features, not measured in this project"},
        "source": "published",
    }


# ---------------------------------------------------------------------------
# Combine: unified table output
# ---------------------------------------------------------------------------

def _combine_results(args: argparse.Namespace) -> None:
    """Read per-component JSON files and produce unified tables."""
    print("=" * 76)
    print("ViolenceCC Backbone Extraction Benchmark -- Combined Results")
    print("=" * 76)

    # Read available results
    clip_data = _read_json(os.path.join(_RESULTS_DIR, "backbone_bench_clip.json"))
    rtmpose_data = _read_json(os.path.join(_RESULTS_DIR, "backbone_bench_rtmpose.json"))
    ctrgcn_data = _read_json(os.path.join(_RESULTS_DIR, "backbone_bench_ctrgcn.json"))
    i3d_data = _i3d_published()

    components = [
        ("CLIP ViT-B/16", clip_data),
        ("RTMPose-m + YOLOX", rtmpose_data),
        ("CTR-GCN (4-stream)", ctrgcn_data),
        ("I3D RGB", i3d_data),
    ]

    # Check which are available
    for name, data in components:
        if data is None:
            print(f"  WARNING: {name} results not found (run --{name.split()[0].lower()} first)")

    print()

    # ---- Build unified rows ----
    rows: List[Dict[str, Any]] = []

    for name, data in components:
        if data is None:
            continue

        m = data["metrics"]
        is_published = data.get("source") == "published"

        row: Dict[str, Any] = {
            "backbone": data["backbone"],
            "params_m": m.get("params_m"),
            "params_star": m.get("params_source") == "published",
            "flops_g": m.get("flops_g"),
            "flops_star": "published" in str(m.get("flops_source", "")),
            "peak_gpu_mb": m.get("peak_gpu_mb"),
        }

        # Latency and throughput: normalize differently per component
        if "CLIP" in name:
            row["latency_label"] = f"{m['latency_ms_batch_mean']:.1f} ms/B"
            row["throughput_label"] = f"{m['throughput_fps']:.0f} f/s"
            row["per_frame_ms"] = m.get("latency_ms_per_frame")
            row["per_frame_label"] = f"{m['latency_ms_per_frame']:.2f} ms"
        elif "RTMPose" in name:
            row["latency_label"] = f"{m['latency_ms_per_frame_mean']:.1f} ms/f"
            row["throughput_label"] = f"{m['throughput_fps']:.1f} f/s"
            row["per_frame_ms"] = m.get("latency_ms_per_frame")
            row["per_frame_label"] = f"{m['latency_ms_per_frame']:.1f} ms"
        elif "CTR-GCN" in name:
            row["latency_label"] = f"{m['latency_ms_4stream_mean']:.1f} ms/sn"
            row["throughput_label"] = f"{m['throughput_snippets_s']:.1f} sn/s"
            row["per_frame_ms"] = None  # snippet-level, not per-frame
            row["per_frame_label"] = "-- (snippet)"
        elif "I3D" in name:
            row["latency_label"] = "Pre-extracted"
            row["throughput_label"] = "---"
            row["per_frame_ms"] = None
            row["per_frame_label"] = "---"

        rows.append(row)

    # ---- Console table ----
    print("-" * 105)
    header = (
        f"{'Backbone':<20} | {'Params (M)':>11} | {'FLOPs (G)':>11} | "
        f"{'Latency':>15} | {'Throughput':>12} | {'GPU Mem (MB)':>12} | {'Per-Frame':>12}"
    )
    print(header)
    print("-" * 105)

    for r in rows:
        params_str = f"{r['params_m']:.1f}" if r["params_m"] is not None else "---"
        if r["params_star"]:
            params_str += "*"
        flops_str = f"{r['flops_g']:.1f}" if r["flops_g"] is not None else "---"
        if r["flops_star"]:
            flops_str += "*"
        gpu_str = f"{r['peak_gpu_mb']:.0f}" if r["peak_gpu_mb"] is not None else "---"

        print(
            f"{r['backbone']:<20} | {params_str:>11} | {flops_str:>11} | "
            f"{r['latency_label']:>15} | {r['throughput_label']:>12} | "
            f"{gpu_str:>12} | {r['per_frame_label']:>12}"
        )

    print("-" * 105)
    print("  * = published number (not measured)")
    print()

    # ---- Pipeline Cost Summary ----
    print("=" * 76)
    print("Pipeline Cost Summary (per 64-frame snippet)")
    print("=" * 76)

    rtm_per_frame = None
    if rtmpose_data:
        rtm_per_frame = rtmpose_data["metrics"].get("latency_ms_per_frame")

    ctrgcn_per_snippet = None
    if ctrgcn_data:
        ctrgcn_per_snippet = ctrgcn_data["metrics"].get("latency_ms_per_snippet")

    clip_per_frame = None
    if clip_data:
        clip_per_frame = clip_data["metrics"].get("latency_ms_per_frame")

    # Skeleton path: RTMPose * 64 frames + CTR-GCN per snippet
    if rtm_per_frame is not None and ctrgcn_per_snippet is not None:
        skel_rtm = rtm_per_frame * 64
        skel_total = skel_rtm + ctrgcn_per_snippet
        print(f"  Skeleton path:  RTMPose ({rtm_per_frame:.1f}ms * 64f = {skel_rtm:.0f}ms) "
              f"+ CTR-GCN ({ctrgcn_per_snippet:.1f}ms) = {skel_total:.0f} ms/snippet")
    elif rtm_per_frame is not None:
        skel_rtm = rtm_per_frame * 64
        print(f"  Skeleton path:  RTMPose ({rtm_per_frame:.1f}ms * 64f = {skel_rtm:.0f}ms) "
              f"+ CTR-GCN (N/A)")
    else:
        print("  Skeleton path:  Data not available (run --rtmpose and --ctrgcn)")

    # CLIP path: ~6 sampled frames per snippet (1 FPS from 64 frames at ~10 FPS)
    clip_frames_per_snippet = 6  # approximate: 64 frames / ~10 FPS = ~6.4s, 1 FPS -> ~6 frames
    if clip_per_frame is not None:
        clip_total = clip_per_frame * clip_frames_per_snippet
        print(f"  CLIP path:      CLIP ({clip_per_frame:.2f}ms * ~{clip_frames_per_snippet}f = {clip_total:.1f}ms) "
              f"= {clip_total:.0f} ms/snippet")
    else:
        print("  CLIP path:      Data not available (run --clip)")

    print(f"  I3D path:       Pre-extracted features; published cost: 107.9 GFLOPs/clip")
    print()

    # ---- LaTeX table ----
    print("% --- LaTeX table (copy-paste into thesis) ---")
    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{Computational cost comparison of backbone feature extractors.}")
    print(r"\label{tab:backbone-cost}")
    print(r"\begin{tabular}{lrrrrr}")
    print(r"\toprule")
    print(r"Backbone & Params (M) & FLOPs (G) & Latency & Throughput & GPU Mem (MB) \\")
    print(r"\midrule")

    for r in rows:
        name_escaped = r["backbone"].replace("-", "{-}").replace("_", r"\_")
        params_str = f"{r['params_m']:.1f}" if r["params_m"] is not None else "---"
        if r["params_star"]:
            params_str = r"$\sim$" + params_str
        flops_str = f"{r['flops_g']:.1f}" if r["flops_g"] is not None else "---"
        if r["flops_star"]:
            flops_str = r"$\sim$" + flops_str
        gpu_str = f"{r['peak_gpu_mb']:.0f}" if r["peak_gpu_mb"] is not None else "---"

        print(
            f"{name_escaped} & {params_str} & {flops_str} & "
            f"{r['latency_label']} & {r['throughput_label']} & {gpu_str} \\\\"
        )

    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\vspace{2mm}")
    print(r"\footnotesize{$\sim$ denotes published (not measured) values. "
          r"B = batch, f = frame, sn = snippet (64 frames).}")
    print(r"\end{table}")
    print("% --- end LaTeX table ---")
    print()

    # ---- CSV ----
    csv_path = os.path.join(_RESULTS_DIR, "backbone_bench_combined.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    fieldnames = [
        "backbone", "params_m", "params_source", "flops_g", "flops_source",
        "latency", "throughput", "peak_gpu_mb", "per_frame_ms",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for name, data in components:
            if data is None:
                continue
            m = data["metrics"]
            # Determine latency string
            if "CLIP" in name:
                lat = f"{m['latency_ms_batch_mean']:.1f} ms/B"
                tput = f"{m['throughput_fps']:.0f} f/s"
                pf = f"{m['latency_ms_per_frame']:.3f}"
            elif "RTMPose" in name:
                lat = f"{m['latency_ms_per_frame_mean']:.1f} ms/f"
                tput = f"{m['throughput_fps']:.1f} f/s"
                pf = f"{m['latency_ms_per_frame']:.2f}"
            elif "CTR-GCN" in name:
                lat = f"{m['latency_ms_4stream_mean']:.1f} ms/sn"
                tput = f"{m['throughput_snippets_s']:.1f} sn/s"
                pf = "N/A (snippet)"
            else:
                lat = "Pre-extracted"
                tput = "---"
                pf = "---"

            writer.writerow({
                "backbone": data["backbone"],
                "params_m": m.get("params_m", ""),
                "params_source": m.get("params_source", ""),
                "flops_g": m.get("flops_g", ""),
                "flops_source": m.get("flops_source", ""),
                "latency": lat,
                "throughput": tput,
                "peak_gpu_mb": m.get("peak_gpu_mb", ""),
                "per_frame_ms": pf,
            })
    print(f"CSV saved to: {csv_path}")
    print()
    print("Combine complete.")


# ---------------------------------------------------------------------------
# --all mode: shell out to each env
# ---------------------------------------------------------------------------

def _run_all(args: argparse.Namespace) -> None:
    """Run all 3 component benchmarks via direct python exe, then combine."""
    script_path = Path(__file__).resolve()

    component_flags = [
        ("vcc-main", "--clip"),
        ("vcc-skeleton", "--rtmpose"),
        ("vcc-ctrgcn", "--ctrgcn"),
    ]

    for env_name, flag in component_flags:
        python_exe = _ENV_PYTHON[env_name]
        cmd = [
            python_exe, str(script_path), flag,
            "--num-warmup", str(args.num_warmup),
            "--num-bench", str(args.num_bench),
            "--batch-size", str(args.batch_size),
        ]
        print(f"\n{'='*76}")
        print(f"Running: {' '.join(cmd)}")
        print(f"{'='*76}")

        result = subprocess.run(cmd, timeout=600)
        if result.returncode != 0:
            print(f"WARNING: {env_name} {flag} exited with code {result.returncode}")
        print()

    # Combine all results
    print(f"\n{'='*76}")
    print("Combining results...")
    print(f"{'='*76}")
    _combine_results(args)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark backbone feature extractors across ViolenceCC conda environments."
    )
    parser.add_argument("--clip", action="store_true",
                        help="Benchmark CLIP ViT-B/16 (requires vcc-main env)")
    parser.add_argument("--rtmpose", action="store_true",
                        help="Benchmark RTMPose-m + YOLOX (requires vcc-skeleton env)")
    parser.add_argument("--ctrgcn", action="store_true",
                        help="Benchmark CTR-GCN 4-stream (requires vcc-ctrgcn env)")
    parser.add_argument("--combine", action="store_true",
                        help="Read all JSON results and produce unified table")
    parser.add_argument("--all", action="store_true",
                        help="Run all 3 envs via subprocess, then combine")
    parser.add_argument("--num-warmup", type=int, default=10,
                        help="Warmup iterations before timing (default 10)")
    parser.add_argument("--num-bench", type=int, default=50,
                        help="Timed iterations for latency measurement (default 50)")
    parser.add_argument("--batch-size", type=int, default=64,
                        help="Batch size for CLIP/CTR-GCN (RTMPose is always 1) (default 64)")
    args = parser.parse_args()

    # Must select at least one mode
    if not any([args.clip, args.rtmpose, args.ctrgcn, args.combine, args.all]):
        parser.error("Specify at least one of: --clip, --rtmpose, --ctrgcn, --combine, --all")

    # Reproducibility header
    print("=" * 76)
    print("ViolenceCC Backbone Extraction Benchmark")
    print("=" * 76)
    print(f"GPU             : {_get_gpu_name()}")
    print(f"Warmup iters    : {args.num_warmup}")
    print(f"Bench iters     : {args.num_bench}")
    print(f"Batch size      : {args.batch_size}")
    print(f"Timestamp       : {datetime.now(timezone.utc).isoformat()}")
    print("=" * 76)

    if args.all:
        _run_all(args)
    else:
        if args.clip:
            _bench_clip(args)
        if args.rtmpose:
            _bench_rtmpose(args)
        if args.ctrgcn:
            _bench_ctrgcn(args)
        if args.combine:
            _combine_results(args)


if __name__ == "__main__":
    main()
