from __future__ import annotations

import hashlib
from pathlib import Path
import time

import cv2
import numpy as np


class Segmenter:
    def __init__(self, model_path: Path, provider: str, require_npu: bool):
        self.model_path = model_path
        self.provider = provider
        self.require_npu = require_npu
        self.session = None
        self.input = None
        self.backend = "uninitialized"
        self.model_sha256 = "missing"

    def load(self) -> None:
        if not self.model_path.exists():
            raise RuntimeError(f"Model missing: {self.model_path}. Run scripts/setup-snapdragon.ps1")
        self.model_sha256 = hashlib.sha256(self.model_path.read_bytes()).hexdigest()
        import onnxruntime as ort
        options = ort.SessionOptions()
        if self.provider == "qnn":
            options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
            providers = [("QNNExecutionProvider", {"backend_path": "QnnHtp.dll", "profiling_level": "basic"})]
        elif self.provider == "cpu":
            providers = ["CPUExecutionProvider"]
        else:
            raise ValueError("Provider must be qnn or cpu")
        try:
            self.session = ort.InferenceSession(str(self.model_path), sess_options=options, providers=providers)
        except Exception as exc:
            raise RuntimeError(f"Strict {self.provider} session creation failed: {exc}") from exc
        active = self.session.get_providers()
        if self.require_npu and "QNNExecutionProvider" not in active:
            raise RuntimeError(f"QNN NPU required; active providers: {active}")
        self.backend = "qnn-htp" if self.provider == "qnn" else "cpu"
        self.input = self.session.get_inputs()[0]

    def predict(self, frame: np.ndarray) -> tuple[np.ndarray, float]:
        if self.session is None or self.input is None:
            raise RuntimeError("Segmenter is not loaded")
        started = time.perf_counter()
        shape = self.input.shape
        h, w = int(shape[-2]), int(shape[-1])
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
        tensor = np.transpose(resized, (2, 0, 1))[None, ...]
        output = self.session.run(None, {self.input.name: tensor})[0]
        if output.ndim == 4 and output.shape[1] > 1:
            labels = np.argmax(output, axis=1)[0]
        else:
            labels = np.squeeze(output) > 0.5
        mask = (labels == 15).astype(np.uint8) if output.ndim == 4 and output.shape[1] > 1 else labels.astype(np.uint8)
        mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
        mask = cv2.dilate(mask, np.ones((9, 9), np.uint8), iterations=1)
        return mask, (time.perf_counter() - started) * 1000
