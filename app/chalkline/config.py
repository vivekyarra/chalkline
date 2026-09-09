from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    source: str = "camera:0"
    width: int = 1280
    height: int = 720
    fps: float = 8.0
    board_width: int = 1024
    tile_size: int = 64
    provider: str = "qnn"
    require_npu: bool = True
    worker_python: Path | None = None
    model_path: Path = ROOT / "data" / "models" / "person-segmentation.qdq.onnx"
    calibration_path: Path = ROOT / "data" / "calibration.json"
    database_path: Path = ROOT / "data" / "chalkline.db"
    checkpoint_dir: Path = ROOT / "data" / "checkpoints"
    web_dir: Path = ROOT / "web" / "static"
    demo_mode: bool = False
