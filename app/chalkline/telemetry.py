from __future__ import annotations

import json
from pathlib import Path
import threading
import time
from typing import Any


class Telemetry:
    def __init__(self, directory: Path, manifest: dict[str, Any]):
        directory.mkdir(parents=True, exist_ok=True)
        self.events_path = directory / "events.jsonl"
        self._lock = threading.Lock()
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def emit(self, event: str, **fields: Any) -> None:
        record = {"timestamp_ms": int(time.time() * 1000), "event": event, **fields}
        with self._lock, self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")
