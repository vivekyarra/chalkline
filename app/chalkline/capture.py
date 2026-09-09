from __future__ import annotations

import time
from typing import Iterator

import cv2
import numpy as np


class CaptureSource:
    def __init__(self, source: str, width: int, height: int, fps: float):
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.replay = source.startswith("file:")
        value: int | str = source[7:] if self.replay else int(source.split(":", 1)[1])
        self.cap = cv2.VideoCapture(value)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open capture source {source}")
        if not self.replay:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)

    def frames(self) -> Iterator[tuple[int, np.ndarray]]:
        interval = 1.0 / self.fps
        next_frame = time.perf_counter()
        while True:
            ok, frame = self.cap.read()
            if not ok:
                if self.replay:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                raise RuntimeError("Camera stopped delivering frames")
            yield int(time.time() * 1000), frame
            next_frame += interval
            time.sleep(max(0, next_frame - time.perf_counter()))

    def close(self) -> None:
        self.cap.release()


def demo_frame(tick: int, width: int = 1280, height: int = 720) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic fixture for protocol verification. UI labels it DEMO."""
    image = np.full((height, width, 3), (34, 55, 45), dtype=np.uint8)
    cv2.rectangle(image, (70, 55), (width - 70, height - 55), (27, 43, 35), -1)
    cv2.putText(image, "E = mc", (160, 260), cv2.FONT_HERSHEY_SIMPLEX, 2.4, (235, 238, 225), 5, cv2.LINE_AA)
    cv2.putText(image, "2", (470, 205), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (235, 238, 225), 3, cv2.LINE_AA)
    cv2.line(image, (155, 330), (620, 330), (220, 225, 210), 4, cv2.LINE_AA)
    phase = tick % 200
    if 20 <= phase < 100:
        cv2.putText(image, "+ C", (545, 260), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (235, 238, 225), 5, cv2.LINE_AA)
    if 120 <= phase < 180:
        cv2.putText(image, "a2 + b2 = c2", (160, 455), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (235, 238, 225), 4, cv2.LINE_AA)
    occluded = np.zeros((height, width), dtype=np.uint8)
    if 40 <= phase < 80:
        x = 250 + (phase % 40) * 8
        cv2.ellipse(occluded, (x, 280), (100, 220), 0, 0, 360, 255, -1)
        image[occluded > 0] = (80, 105, 140)
    return image, occluded
