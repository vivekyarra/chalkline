from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any


class EventStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS events (
              session_id TEXT NOT NULL, epoch TEXT NOT NULL, version INTEGER NOT NULL,
              kind TEXT NOT NULL, created_ms INTEGER NOT NULL, payload TEXT NOT NULL,
              PRIMARY KEY(session_id, epoch, version)
            )
        """)
        self._db.commit()

    def append(self, session_id: str, epoch: str, version: int, kind: str, payload: dict[str, Any]) -> None:
        with self._lock, self._db:
            self._db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                             (session_id, epoch, version, kind, int(time.time() * 1000),
                              json.dumps(payload, separators=(",", ":"))))

    def list(self, session_id: str, epoch: str, after: int = -1) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT version,kind,created_ms,payload FROM events WHERE session_id=? AND epoch=? AND version>? ORDER BY version",
                (session_id, epoch, after)).fetchall()
        return [{"version": v, "kind": k, "created_ms": t, "payload": json.loads(p)} for v, k, t, p in rows]

    def close(self) -> None:
        with self._lock:
            self._db.close()
