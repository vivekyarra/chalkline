from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import cv2
import numpy as np


class ChangeKind(StrEnum):
    UPDATE = "update"
    ERASURE = "erasure"


@dataclass(frozen=True)
class BoardCommit:
    version: int
    image: np.ndarray
    changed_mask: np.ndarray
    valid_mask: np.ndarray
    stale_mask: np.ndarray
    kind: ChangeKind


class BoardState:
    """Conservative temporal state: occluded pixels never overwrite captured evidence."""

    def __init__(self, shape: tuple[int, int], difference_threshold: int = 12,
                 update_observations: int = 3, erase_observations: int = 5,
                 mask_hold_frames: int = 3):
        h, w = shape
        self.image = np.zeros((h, w, 3), dtype=np.uint8)
        self.valid = np.zeros((h, w), dtype=bool)
        self.stale = np.ones((h, w), dtype=bool)
        self.version = 0
        self.threshold = difference_threshold
        self.update_observations = update_observations
        self.erase_observations = erase_observations
        self.mask_hold_frames = mask_hold_frames
        self._candidate = np.zeros((h, w, 3), dtype=np.uint8)
        self._candidate_count = np.zeros((h, w), dtype=np.uint8)
        self._occlusion_hold = np.zeros((h, w), dtype=np.uint8)

    @classmethod
    def restore(cls, image: np.ndarray, valid: np.ndarray, stale: np.ndarray, version: int,
                **settings: int) -> "BoardState":
        if image.ndim != 3 or image.shape[2] != 3 or valid.shape != image.shape[:2] or stale.shape != image.shape[:2]:
            raise ValueError("Invalid board snapshot dimensions")
        if image.shape[0] > 4320 or image.shape[1] > 7680 or image.size == 0:
            raise ValueError("Board snapshot exceeds limits")
        state = cls(image.shape[:2], **settings)
        state.image = np.ascontiguousarray(image, dtype=np.uint8)
        state.valid = np.ascontiguousarray(valid, dtype=bool)
        state.stale = np.ascontiguousarray(stale, dtype=bool)
        state.version = max(0, int(version))
        return state

    @staticmethod
    def _chalk_score(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        local = cv2.GaussianBlur(gray, (9, 9), 0)
        return cv2.absdiff(gray, local)

    def observe(self, frame: np.ndarray, occluded: np.ndarray) -> BoardCommit | None:
        if frame.shape != self.image.shape or occluded.shape != self.valid.shape:
            raise ValueError("Frame or occlusion dimensions do not match board state")
        mask = occluded.astype(bool)
        self._occlusion_hold[mask] = self.mask_hold_frames
        held = self._occlusion_hold > 0
        self._occlusion_hold[~mask & held] -= 1
        clear = self._occlusion_hold == 0
        self.stale = ~clear

        unknown_clear = clear & ~self.valid
        if unknown_clear.any():
            self.image[unknown_clear] = frame[unknown_clear]
            self.valid[unknown_clear] = True

        delta = np.max(cv2.absdiff(frame, self.image), axis=2)
        changed = clear & self.valid & (delta >= self.threshold)
        # A nearly full-frame jump is more likely lighting or camera movement.
        if changed.mean() > 0.60:
            self._candidate_count.fill(0)
            self.stale[:] = True
            return None

        candidate_delta = np.max(cv2.absdiff(frame, self._candidate), axis=2)
        stable = changed & (candidate_delta < self.threshold)
        new_candidate = changed & ~stable
        self._candidate[new_candidate] = frame[new_candidate]
        self._candidate_count[new_candidate] = 1
        self._candidate_count[stable] = np.minimum(255, self._candidate_count[stable] + 1)
        self._candidate_count[~changed] = 0

        before_chalk = self._chalk_score(self.image)
        after_chalk = self._chalk_score(frame)
        erase_candidate = changed & (after_chalk + 3 < before_chalk)
        required = np.where(erase_candidate, self.erase_observations, self.update_observations)
        confirmed = changed & (self._candidate_count >= required)
        if not confirmed.any():
            return None

        erasure_pixels = confirmed & erase_candidate
        self.image[confirmed] = self._candidate[confirmed]
        self.valid[confirmed] = True
        self._candidate_count[confirmed] = 0
        self.version += 1
        kind = ChangeKind.ERASURE if erasure_pixels.any() else ChangeKind.UPDATE
        return BoardCommit(self.version, self.image.copy(), confirmed.copy(), self.valid.copy(), self.stale.copy(), kind)
