"""E0 only: CUDA availability, sustained matmul, replay, empty-state throughput."""
import os
os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

import argparse
import hashlib
import json
import platform
import subprocess
import threading
import time
import traceback
from pathlib import Path

import torch


def precision(tf32=False):
    torch.backends.cuda.matmul.allow_tf32 = tf32
    torch.backends.cudnn.allow_tf32 = False


def fingerprint():
    g = torch.Generator(device="cuda").manual_seed(701)
    a = torch.randn((1024, 1024), device="cuda", generator=g)
    b = torch.randn((1024, 1024), device="cuda", generator=g)
    first, second = a @ b, a @ b
    return {"bitwise_equal": bool(torch.equal(first, second)),
            "max_abs_diff": float((first - second).abs().max()),
            "sha256": hashlib.sha256(first.cpu().numpy().tobytes()).hexdigest()}


def telemetry(stop, samples):
    while not stop.is_set():
        p = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu,clocks.current.graphics,clocks.current.memory,power.draw,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True)
        samples.append({"elapsed_s": time.perf_counter() - START, "returncode": p.returncode,
                        "csv_temperature_C_graphics_MHz_memory_MHz_power_W_util_percent": p.stdout.strip(),
                        "stderr": p.stderr.strip()})
        stop.wait(1)


def matmul(tf32):
    precision(tf32)
    g = torch.Generator(device="cuda").manual_seed(702)
    a = torch.randn((4096, 4096), device="cuda", generator=g)
    b = torch.randn((4096, 4096), device="cuda", generator=g)
    out = torch.empty_like(a)
    for _ in range(10):
        torch.mm(a, b, out=out)
    torch.cuda.synchronize()
    measurements = []
    # Ten measured batches keep the GPU under load long enough to sample clocks.
    for _ in range(10):
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(50):
            torch.mm(a, b, out=out)
        end.record()
        end.synchronize()
        seconds = start.elapsed_time(end) / 1000
        measurements.append({"seconds": seconds, "gflops": 50 * 2 * 4096 ** 3 / seconds / 1e9})
    return {"tf32": tf32, "shape": [4096, 4096], "dtype": "float32",
            "iterations": 500, "batches": measurements,
            "aggregate_gflops": 500 * 2 * 4096 ** 3 / sum(x["seconds"] for x in measurements) / 1e9}


def empty_state(batch):
    # Explicitly a launch-overhead probe, NOT Room-v0 or an ES budget estimate.
    g = torch.Generator(device="cuda").manual_seed(703 + batch)
    moves = torch.randint(-1, 2, (1500, batch, 2), device="cuda", generator=g)
    pos = torch.zeros((batch, 2), device="cuda", dtype=torch.int64)
    energy = torch.ones(batch, device="cuda")
    torch.cuda.synchronize()
    start = time.perf_counter()
    for t in range(1500):
        pos = (pos + moves[t]).clamp(1, 10)
        energy = (energy - 0.004).clamp(0, 1)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    return {"batch": batch, "steps": 1500, "wall_seconds": elapsed,
            "scheduled_individual_steps_per_second": batch * 1500 / elapsed,
            "scope": "empty state only; excludes observations, brain and ES"}


START = time.perf_counter()
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fingerprint", action="store_true")
    parser.add_argument("--out", default="evidence/e0_torch.json")
    args = parser.parse_args()
    result = {"python": platform.python_version(), "torch": torch.__version__,
              "cuda_runtime": torch.version.cuda, "cuda_available": torch.cuda.is_available(),
              "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"]}
    stop, samples = threading.Event(), []
    monitor = None
    try:
        assert torch.cuda.is_available(), "CUDA unavailable; no CPU fallback"
        result.update(device=torch.cuda.get_device_name(0), capability=torch.cuda.get_device_capability(0),
                      arch_list=torch.cuda.get_arch_list())
        assert torch.cuda.get_device_capability(0) == (12, 0)
        torch.use_deterministic_algorithms(True)
        precision(False)
        if args.fingerprint:
            print(json.dumps(fingerprint()))
        else:
            monitor = threading.Thread(target=telemetry, args=(stop, samples), daemon=True)
            monitor.start()
            result["matmul"] = [matmul(False), matmul(True)]
            precision(False)
            result["determinism"] = fingerprint()
            result["fresh_processes"] = [json.loads(subprocess.check_output(
                [os.sys.executable, __file__, "--fingerprint"], text=True)) for _ in range(2)]
            assert result["determinism"]["bitwise_equal"]
            assert result["fresh_processes"][0] == result["fresh_processes"][1] == result["determinism"]
            result["empty_state"] = [empty_state(n) for n in (2048, 4096, 8192)]
            result["status"] = "PASS_GPU_SMOKE"
    except Exception:
        result["status"] = "FAIL"
        result["error"] = traceback.format_exc()
        raise
    finally:
        if not args.fingerprint:
            stop.set()
            if monitor:
                monitor.join(timeout=5)
            result["telemetry"] = samples
            result["wall_seconds"] = time.perf_counter() - START
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result, indent=2))
