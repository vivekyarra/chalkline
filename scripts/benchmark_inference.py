from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time

import numpy as np
import onnxruntime as ort


def main() -> int:
    parser = argparse.ArgumentParser(description="Same-artifact native ARM64 inference benchmark")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--provider", choices=("cpu", "qnn"), required=True)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--iterations", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if platform.machine().upper() not in {"ARM64", "AARCH64"}:
        raise SystemExit("This benchmark requires native ARM64 Python on the Snapdragon PC")
    options = ort.SessionOptions()
    options.enable_profiling = True
    providers = ["CPUExecutionProvider"]
    if args.provider == "qnn":
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        providers = [("QNNExecutionProvider", {"backend_path": "QnnHtp.dll", "profiling_level": "basic"})]
    created = time.perf_counter()
    session = ort.InferenceSession(str(args.model), sess_options=options, providers=providers)
    startup_ms = (time.perf_counter() - created) * 1000
    if args.provider == "qnn" and "QNNExecutionProvider" not in session.get_providers():
        raise SystemExit("QNN provider did not remain active")
    model_input = session.get_inputs()[0]
    shape = [int(v) for v in model_input.shape]
    tensor = np.random.default_rng(4101).random(shape, dtype=np.float32)
    for _ in range(args.warmup):
        session.run(None, {model_input.name: tensor})
    timings = []
    for _ in range(args.iterations):
        started = time.perf_counter()
        session.run(None, {model_input.name: tensor})
        timings.append((time.perf_counter() - started) * 1000)
    timings.sort()
    profile_path = session.end_profiling()
    result = {"provider": args.provider, "active_providers": session.get_providers(),
              "machine": platform.machine(), "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
              "shape": shape, "warmup": args.warmup, "iterations": args.iterations,
              "startup_ms": startup_ms, "latency_ms": {"p50": statistics.median(timings),
              "p95": timings[int(len(timings) * .95) - 1], "max": max(timings)},
              "profile_path": profile_path}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
