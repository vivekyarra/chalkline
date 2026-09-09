from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import threading
import uuid

import cv2
import numpy as np


class SegmentationWorker:
    """Binary IPC bridge from the host process to native ARM64 QNN inference."""

    def __init__(self, python: Path, worker: Path, model: Path, provider: str, require_npu: bool):
        command = [str(python), str(worker), "--model", str(model), "--provider", provider]
        if require_npu:
            command.append("--require-npu")
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, bufsize=0)
        self.lock = threading.Lock()
        self.backend = "qnn-htp" if provider == "qnn" else "cpu"

    def _read_exact(self, length: int) -> bytes:
        if self.process.stdout is None:
            raise RuntimeError("Worker stdout unavailable")
        data = self.process.stdout.read(length)
        if len(data) != length:
            detail = self.process.stderr.read().decode("utf-8", errors="replace") if self.process.stderr else ""
            raise RuntimeError(f"Inference worker stopped: {detail[-2000:]}")
        return data

    def predict(self, frame: np.ndarray) -> tuple[np.ndarray, float]:
        if self.process.poll() is not None:
            raise RuntimeError("Inference worker is not running")
        request_id = str(uuid.uuid4())
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (513, 513), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
        tensor = np.ascontiguousarray(np.transpose(resized, (2, 0, 1))[None, ...])
        payload = tensor.tobytes()
        header = {"protocol": 1, "request_id": request_id, "capture_ms": 0,
                  "shape": list(tensor.shape), "dtype": "float32", "payload_bytes": len(payload)}
        encoded = json.dumps(header, separators=(",", ":")).encode("utf-8")
        with self.lock:
            if self.process.stdin is None:
                raise RuntimeError("Worker stdin unavailable")
            self.process.stdin.write(struct.pack("<I", len(encoded)) + encoded + payload)
            self.process.stdin.flush()
            response_length = struct.unpack("<I", self._read_exact(4))[0]
            if response_length > 1024 * 1024:
                raise RuntimeError("Invalid worker response header")
            response = json.loads(self._read_exact(response_length))
            if response.get("request_id") != request_id:
                raise RuntimeError("Worker response ID mismatch")
            mask_bytes = self._read_exact(int(response["payload_bytes"]))
        self.backend = response["backend"]
        mask = np.frombuffer(mask_bytes, dtype=np.uint8).reshape(response["shape"])
        mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
        mask = cv2.dilate(mask, np.ones((7, 7), dtype=np.uint8), iterations=1)
        return mask, float(response["inference_ms"])

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
