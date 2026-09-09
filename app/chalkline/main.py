from __future__ import annotations

import argparse
import asyncio
import base64
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import json
from pathlib import Path
import threading
import time
import uuid

import cv2
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from pydantic import BaseModel, Field

from .board_state import BoardState
from .calibration import Calibration
from .capture import CaptureSource, demo_frame
from .config import ROOT, Settings
from .patches import checkpoint_payload, encode_stale_overlay, encode_tiles
from .segmentation import Segmenter
from .segmentation_client import SegmentationWorker
from .store import EventStore, load_board_snapshot, save_board_snapshot
from .telemetry import Telemetry


class CalibrationRequest(BaseModel):
    points: list[list[float]] = Field(min_length=4, max_length=4)
    source_width: int = Field(gt=0, le=7680)
    source_height: int = Field(gt=0, le=4320)


@dataclass
class Runtime:
    settings: Settings
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    epoch: str = field(default_factory=lambda: str(uuid.uuid4()))
    calibration: Calibration | None = None
    state: BoardState | None = None
    latest_source: np.ndarray | None = None
    latest_rectified: np.ndarray | None = None
    latest_mask: np.ndarray | None = None
    clients: set[WebSocket] = field(default_factory=set)
    audio_clients: set[WebSocket] = field(default_factory=set)
    history: list[dict] = field(default_factory=list)
    running: bool = False
    paused: bool = False
    error: str | None = None
    backend: str = "demo-fixture"
    inference_ms: float = 0.0
    frames: int = 0
    dropped: int = 0
    bytes_sent: int = 0
    state_lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    started_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    run_id: str = field(default_factory=lambda: time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])

    def status(self) -> dict:
        return {"session_id": self.session_id, "epoch": self.epoch,
                "version": self.state.version if self.state else 0,
                "running": self.running, "paused": self.paused, "error": self.error,
                "backend": self.backend, "inference_ms": round(self.inference_ms, 2),
                "frames": self.frames, "dropped": self.dropped, "bytes_sent": self.bytes_sent,
                "stale_percent": round(float(self.state.stale.mean() * 100), 2) if self.state else 100.0,
                "run_id": self.run_id,
                "source": "DEMO" if self.settings.demo_mode else "CAMERA",
                "calibrated": self.calibration is not None}


def encode_jpeg(image: np.ndarray | None) -> str | None:
    if image is None:
        return None
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 78])
    return base64.b64encode(encoded).decode("ascii") if ok else None


def full_frame_calibration(width: int, height: int, output_width: int) -> Calibration:
    return Calibration.create(str(uuid.uuid4()), width, height, output_width,
                              [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    runtime = Runtime(settings)
    telemetry = Telemetry(ROOT / "evidence" / runtime.run_id,
                          {"run_id": runtime.run_id, "created_ms": runtime.started_ms,
                           "source": "demo-fixture" if settings.demo_mode else settings.source,
                           "requested_provider": settings.provider,
                           "require_npu": settings.require_npu,
                           "model_path": settings.model_path.name})
    if settings.calibration_path.exists():
        try:
            runtime.calibration = Calibration.load(settings.calibration_path)
        except Exception:
            runtime.calibration = None
    snapshot_path = settings.checkpoint_dir / "latest.npz"
    if runtime.calibration and snapshot_path.exists():
        try:
            recovered_state, recovered = load_board_snapshot(snapshot_path)
            if recovered.get("calibration_id") == runtime.calibration.calibration_id:
                runtime.state = recovered_state
                runtime.session_id = str(recovered["session_id"])
                runtime.epoch = str(recovered["epoch"])
                recovered_payload = checkpoint_payload(recovered_state.image, recovered_state.valid, recovered_state.stale)
                runtime.history.append({"version": recovered_state.version, "kind": "recovered-checkpoint",
                                        "created_ms": int(time.time() * 1000), "image": recovered_payload["image"]})
        except Exception:
            runtime.state = None
    store = EventStore(settings.database_path)
    stop_event = threading.Event()
    loop_holder: dict[str, asyncio.AbstractEventLoop] = {}

    async def broadcast(message: dict) -> None:
        encoded = json.dumps(message, separators=(",", ":"))
        runtime.bytes_sent += len(encoded.encode()) * len(runtime.clients)
        dead: list[WebSocket] = []
        for ws in list(runtime.clients):
            try:
                await asyncio.wait_for(ws.send_text(encoded), timeout=1.0)
            except Exception:
                dead.append(ws)
        for ws in dead:
            runtime.clients.discard(ws)

    def publish(message: dict) -> None:
        loop = loop_holder.get("loop")
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(message), loop)

    def pipeline() -> None:
        capture = None
        segmenter = None
        try:
            if not settings.demo_mode:
                if settings.worker_python:
                    segmenter = SegmentationWorker(settings.worker_python, ROOT / "inference" / "worker.py",
                                                   settings.model_path, settings.provider, settings.require_npu)
                else:
                    segmenter = Segmenter(settings.model_path, settings.provider, settings.require_npu)
                    segmenter.load()
                runtime.backend = segmenter.backend
                capture = CaptureSource(settings.source, settings.width, settings.height, settings.fps)
                iterator = capture.frames()
            runtime.running = True
            telemetry.emit("pipeline_started", backend=runtime.backend)
            tick = 0
            while not stop_event.is_set():
                if runtime.paused:
                    time.sleep(0.05)
                    continue
                if settings.demo_mode:
                    timestamp = int(time.time() * 1000)
                    frame, source_mask = demo_frame(tick, settings.width, settings.height)
                    time.sleep(1 / settings.fps)
                else:
                    timestamp, frame = next(iterator)
                    source_mask, runtime.inference_ms = segmenter.predict(frame)
                runtime.latest_source = frame
                cal = runtime.calibration
                if cal is None:
                    cal = full_frame_calibration(frame.shape[1], frame.shape[0], settings.board_width)
                    runtime.calibration = cal
                rectified = cal.rectify(frame)
                mask = cal.rectify(source_mask, mask=True) > 0
                runtime.latest_rectified = rectified
                runtime.latest_mask = mask.astype(np.uint8) * 255
                with runtime.state_lock:
                    initialized = runtime.state is None or runtime.state.image.shape != rectified.shape
                    if initialized:
                        runtime.state = BoardState(rectified.shape[:2])
                        runtime.epoch = str(uuid.uuid4())
                    state = runtime.state
                    commit = state.observe(rectified, mask)
                    runtime.frames += 1
                    if initialized:
                        payload = checkpoint_payload(state.image, state.valid, state.stale)
                        runtime.history.append({"version": 0, "kind": "checkpoint",
                                                "created_ms": int(time.time() * 1000), "image": payload["image"]})
                        publish({"type": "checkpoint", "protocol": 1, "session_id": runtime.session_id,
                                 "epoch": runtime.epoch, "version": 0, "width": state.image.shape[1],
                                 "height": state.image.shape[0], **payload})
                        save_board_snapshot(snapshot_path, state,
                                            {"session_id": runtime.session_id, "epoch": runtime.epoch,
                                             "calibration_id": cal.calibration_id})
                    elif commit:
                        tiles = [tile.json() for tile in encode_tiles(commit.image, commit.changed_mask,
                                                                      settings.tile_size)]
                        message = {"type": "patch", "protocol": 1, "session_id": runtime.session_id,
                                   "epoch": runtime.epoch, "base_version": commit.version - 1,
                                   "version": commit.version, "kind": commit.kind.value,
                                   "capture_ms": timestamp, "committed_ms": int(time.time() * 1000),
                                   "width": commit.image.shape[1], "height": commit.image.shape[0],
                                   "tiles": tiles, "stale_mask": encode_stale_overlay(commit.stale_mask)}
                        store.append(runtime.session_id, runtime.epoch, commit.version, commit.kind.value, message)
                        telemetry.emit("board_commit", epoch=runtime.epoch, version=commit.version,
                                       kind=commit.kind.value, tile_count=len(tiles),
                                       payload_bytes=len(json.dumps(message)))
                        runtime.history.append({"version": commit.version, "kind": commit.kind.value,
                                                "created_ms": message["committed_ms"], "image": checkpoint_payload(
                                                    commit.image, commit.valid_mask, commit.stale_mask)["image"]})
                        save_board_snapshot(snapshot_path, state,
                                            {"session_id": runtime.session_id, "epoch": runtime.epoch,
                                             "calibration_id": cal.calibration_id})
                        publish(message)
                    elif runtime.frames % max(1, int(settings.fps)) == 0:
                        publish({"type": "freshness", "epoch": runtime.epoch,
                                 "version": state.version, "stale_mask": encode_stale_overlay(state.stale),
                                 "committed_ms": int(time.time() * 1000)})
                tick += 1
        except Exception as exc:
            runtime.error = str(exc)
            telemetry.emit("pipeline_error", message=runtime.error)
            publish({"type": "error", "message": runtime.error})
        finally:
            runtime.running = False
            telemetry.emit("pipeline_stopped", frames=runtime.frames, bytes_sent=runtime.bytes_sent)
            if capture:
                capture.close()
            if segmenter and hasattr(segmenter, "close"):
                segmenter.close()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        loop_holder["loop"] = asyncio.get_running_loop()
        thread = threading.Thread(target=pipeline, name="chalkline-pipeline", daemon=True)
        thread.start()
        yield
        stop_event.set()
        thread.join(timeout=3)
        store.close()

    app = FastAPI(title="CHALKLINE", version="0.1.0", lifespan=lifespan)
    app.state.runtime = runtime

    @app.get("/api/health")
    async def health():
        status = runtime.status()
        return JSONResponse(status, status_code=503 if runtime.error else 200)

    @app.get("/api/preview")
    async def preview():
        return {"source": encode_jpeg(runtime.latest_source),
                "rectified": encode_jpeg(runtime.latest_rectified),
                "mask": encode_jpeg(runtime.latest_mask), "status": runtime.status()}

    @app.post("/api/calibration")
    async def calibrate(request: CalibrationRequest, http_request: Request):
        if http_request.client and http_request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            raise HTTPException(403, "Teacher controls are localhost-only")
        try:
            cal = Calibration.create(str(uuid.uuid4()), request.source_width, request.source_height,
                                     settings.board_width, request.points)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        with runtime.state_lock:
            runtime.calibration = cal
            runtime.state = None
            runtime.history.clear()
            runtime.epoch = str(uuid.uuid4())
            cal.save(settings.calibration_path)
        return {"calibration_id": cal.calibration_id, "width": cal.output_width, "height": cal.output_height}

    @app.post("/api/control/{action}")
    async def control(action: str, request: Request):
        if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            raise HTTPException(403, "Teacher controls are localhost-only")
        if action == "pause": runtime.paused = True
        elif action == "start": runtime.paused = False
        elif action == "reset":
            with runtime.state_lock:
                runtime.state = None
                runtime.history.clear()
                runtime.epoch = str(uuid.uuid4())
        else: raise HTTPException(400, "Unknown action")
        return runtime.status()

    @app.get("/api/history")
    async def history():
        return [{k: v for k, v in item.items() if k != "image"} for item in runtime.history]

    @app.get("/api/history/{version}")
    async def history_version(version: int):
        item = next((x for x in runtime.history if x["version"] == version), None)
        if not item: raise HTTPException(404, "Version not retained")
        return item

    @app.websocket("/ws/board")
    async def board_socket(ws: WebSocket):
        await ws.accept()
        runtime.clients.add(ws)
        try:
            if runtime.state:
                payload = checkpoint_payload(runtime.state.image, runtime.state.valid, runtime.state.stale)
                await ws.send_json({"type": "checkpoint", "protocol": 1,
                                    "session_id": runtime.session_id, "epoch": runtime.epoch,
                                    "version": runtime.state.version, "width": runtime.state.image.shape[1],
                                    "height": runtime.state.image.shape[0], **payload})
            while True:
                data = await ws.receive_json()
                if data.get("type") == "resync" and runtime.state:
                    payload = checkpoint_payload(runtime.state.image, runtime.state.valid, runtime.state.stale)
                    await ws.send_json({"type": "checkpoint", "protocol": 1,
                                        "session_id": runtime.session_id, "epoch": runtime.epoch,
                                        "version": runtime.state.version, "width": runtime.state.image.shape[1],
                                        "height": runtime.state.image.shape[0], **payload})
        except WebSocketDisconnect:
            runtime.clients.discard(ws)

    @app.websocket("/ws/audio")
    async def audio_socket(ws: WebSocket):
        await ws.accept()
        runtime.audio_clients.add(ws)
        try:
            while True:
                message = await ws.receive_text()
                for peer in list(runtime.audio_clients - {ws}):
                    try: await peer.send_text(message)
                    except Exception: runtime.audio_clients.discard(peer)
        except WebSocketDisconnect:
            runtime.audio_clients.discard(ws)

    @app.get("/")
    async def root(): return FileResponse(settings.web_dir / "student.html")

    @app.get("/teacher")
    async def teacher(): return FileResponse(settings.web_dir / "teacher.html")

    app.mount("/static", StaticFiles(directory=settings.web_dir), name="static")
    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CHALKLINE Snapdragon classroom server")
    parser.add_argument("--source", default="camera:0")
    parser.add_argument("--provider", choices=("qnn", "cpu"), default="qnn")
    parser.add_argument("--model", type=Path, default=ROOT / "data/models/person-segmentation.qdq.onnx")
    parser.add_argument("--worker-python", type=Path, help="Native ARM64 Python used by the QNN worker")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--demo", action="store_true", help="Clearly labeled deterministic fixture")
    return parser.parse_args()


def run() -> None:
    import uvicorn
    args = parse_args()
    settings = Settings(source=args.source, provider=args.provider, require_npu=args.provider == "qnn",
                        worker_python=args.worker_python, model_path=args.model, demo_mode=args.demo)
    uvicorn.run(create_app(settings), host=args.host, port=args.port)


if __name__ == "__main__":
    run()
