from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
from typing import Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class EncodedTile:
    x: int
    y: int
    w: int
    h: int
    png: bytes

    def json(self) -> dict:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h,
                "sha256": hashlib.sha256(self.png).hexdigest(),
                "png": base64.b64encode(self.png).decode("ascii")}


def encode_tiles(image: np.ndarray, changed: np.ndarray, tile_size: int = 64) -> list[EncodedTile]:
    if image.shape[:2] != changed.shape:
        raise ValueError("Image and change mask dimensions differ")
    h, w = changed.shape
    tiles: list[EncodedTile] = []
    for y in range(0, h, tile_size):
        for x in range(0, w, tile_size):
            th, tw = min(tile_size, h - y), min(tile_size, w - x)
            if not changed[y:y + th, x:x + tw].any():
                continue
            ok, data = cv2.imencode(".png", image[y:y + th, x:x + tw], [cv2.IMWRITE_PNG_COMPRESSION, 6])
            if not ok:
                raise RuntimeError("PNG tile encoding failed")
            tiles.append(EncodedTile(x, y, tw, th, data.tobytes()))
    return tiles


def encode_mask(mask: np.ndarray) -> str:
    ok, data = cv2.imencode(".png", mask.astype(np.uint8) * 255, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    if not ok:
        raise RuntimeError("Mask encoding failed")
    return base64.b64encode(data.tobytes()).decode("ascii")


def encode_stale_overlay(mask: np.ndarray) -> str:
    overlay = np.zeros((*mask.shape, 4), dtype=np.uint8)
    overlay[..., :3] = (78, 184, 230)  # BGRA representation of amber
    overlay[..., 3] = mask.astype(np.uint8) * 255
    ok, data = cv2.imencode(".png", overlay, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    if not ok:
        raise RuntimeError("Stale overlay encoding failed")
    return base64.b64encode(data.tobytes()).decode("ascii")


def checkpoint_payload(image: np.ndarray, valid: np.ndarray, stale: np.ndarray) -> dict:
    ok, data = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    if not ok:
        raise RuntimeError("Checkpoint encoding failed")
    return {"image": base64.b64encode(data.tobytes()).decode("ascii"),
            "valid_mask": encode_mask(valid), "stale_mask": encode_stale_overlay(stale)}
