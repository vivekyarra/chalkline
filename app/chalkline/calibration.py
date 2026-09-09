from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class Calibration:
    calibration_id: str
    source_width: int
    source_height: int
    output_width: int
    output_height: int
    points: tuple[tuple[float, float], ...]

    @staticmethod
    def validate_points(points: Iterable[Iterable[float]], width: int, height: int) -> np.ndarray:
        pts = np.asarray(list(points), dtype=np.float32)
        if pts.shape != (4, 2) or not np.isfinite(pts).all():
            raise ValueError("Calibration requires four finite [x,y] points")
        if (pts[:, 0] < 0).any() or (pts[:, 0] >= width).any() or (pts[:, 1] < 0).any() or (pts[:, 1] >= height).any():
            raise ValueError("Calibration points must be inside the source frame")
        contour = pts.reshape((-1, 1, 2))
        if not cv2.isContourConvex(contour):
            raise ValueError("Calibration quadrilateral must be convex and ordered clockwise")
        area = abs(float(cv2.contourArea(contour)))
        if area < width * height * 0.05:
            raise ValueError("Calibration region is too small")
        return pts

    @classmethod
    def create(cls, calibration_id: str, source_width: int, source_height: int,
               output_width: int, points: Iterable[Iterable[float]]) -> "Calibration":
        pts = cls.validate_points(points, source_width, source_height)
        top = np.linalg.norm(pts[1] - pts[0])
        bottom = np.linalg.norm(pts[2] - pts[3])
        left = np.linalg.norm(pts[3] - pts[0])
        right = np.linalg.norm(pts[2] - pts[1])
        ratio = max(left, right) / max(max(top, bottom), 1.0)
        output_height = max(256, int(round(output_width * ratio)))
        return cls(calibration_id, source_width, source_height, output_width, output_height,
                   tuple((float(x), float(y)) for x, y in pts))

    @property
    def matrix(self) -> np.ndarray:
        src = np.asarray(self.points, dtype=np.float32)
        dst = np.asarray([[0, 0], [self.output_width - 1, 0],
                          [self.output_width - 1, self.output_height - 1],
                          [0, self.output_height - 1]], dtype=np.float32)
        return cv2.getPerspectiveTransform(src, dst)

    def rectify(self, image: np.ndarray, *, mask: bool = False) -> np.ndarray:
        interpolation = cv2.INTER_NEAREST if mask else cv2.INTER_LINEAR
        return cv2.warpPerspective(image, self.matrix, (self.output_width, self.output_height), flags=interpolation)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Calibration":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["points"] = tuple(tuple(p) for p in data["points"])
        return cls(**data)
