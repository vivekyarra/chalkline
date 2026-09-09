from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

import numpy as np
import onnxruntime as ort


def read_exact(size: int) -> bytes:
    data = sys.stdin.buffer.read(size)
    if len(data) != size:
        raise EOFError
    return data


def create_session(model: Path, provider: str, require_npu: bool):
    options = ort.SessionOptions()
    options.enable_profiling = True
    if provider == "qnn":
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        providers = [("QNNExecutionProvider", {"backend_path": "QnnHtp.dll", "profiling_level": "basic"})]
    else:
        providers = ["CPUExecutionProvider"]
    session = ort.InferenceSession(str(model), sess_options=options, providers=providers)
    active = session.get_providers()
    if require_npu and "QNNExecutionProvider" not in active:
        raise RuntimeError(f"QNN NPU required; active providers: {active}")
    return session, "qnn-htp" if provider == "qnn" else "native-arm64-cpu"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--provider", choices=("qnn", "cpu"), default="qnn")
    parser.add_argument("--require-npu", action="store_true")
    args = parser.parse_args()
    if not args.model.exists():
        raise SystemExit(f"Model missing: {args.model}")
    session, backend = create_session(args.model, args.provider, args.require_npu)
    model_hash = hashlib.sha256(args.model.read_bytes()).hexdigest()
    model_input = session.get_inputs()[0]
    while True:
        try:
            header_size = struct.unpack("<I", read_exact(4))[0]
        except EOFError:
            return 0
        if header_size > 1024 * 1024:
            raise RuntimeError("Invalid request header length")
        header = json.loads(read_exact(header_size))
        if header.get("protocol") != 1 or header.get("dtype") != "float32":
            raise RuntimeError("Unsupported inference request")
        payload_size = int(header["payload_bytes"])
        if payload_size > 32 * 1024 * 1024:
            raise RuntimeError("Inference payload exceeds limit")
        tensor = np.frombuffer(read_exact(payload_size), dtype=np.float32).reshape(header["shape"])
        started = time.perf_counter()
        output = session.run(None, {model_input.name: tensor})[0]
        duration = (time.perf_counter() - started) * 1000
        if output.ndim == 4 and output.shape[1] > 1:
            mask = (np.argmax(output, axis=1)[0] == 15).astype(np.uint8)
        else:
            mask = (np.squeeze(output) > 0.5).astype(np.uint8)
        response = {"protocol": 1, "request_id": header["request_id"], "backend": backend,
                    "model_sha256": model_hash, "inference_ms": duration,
                    "shape": list(mask.shape), "payload_bytes": mask.nbytes}
        encoded = json.dumps(response, separators=(",", ":")).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("<I", len(encoded)) + encoded + mask.tobytes())
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    raise SystemExit(main())
