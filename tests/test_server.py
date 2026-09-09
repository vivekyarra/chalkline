from pathlib import Path

from fastapi.testclient import TestClient

from chalkline.config import Settings
from chalkline.main import create_app


def test_demo_health_and_pages(tmp_path):
    settings = Settings(demo_mode=True, database_path=tmp_path / "test.db",
                        calibration_path=tmp_path / "cal.json")
    with TestClient(create_app(settings)) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["source"] == "DEMO"
        assert "CHALKLINE" in client.get("/").text
        assert "TEACHER" in client.get("/teacher").text


def test_invalid_calibration_is_rejected(tmp_path):
    settings = Settings(demo_mode=True, database_path=tmp_path / "test.db")
    with TestClient(create_app(settings)) as client:
        response = client.post("/api/calibration", json={"source_width": 100, "source_height": 100,
                                                          "points": [[0,0],[99,99],[99,0],[0,99]]})
        assert response.status_code == 400 or response.status_code == 422


def test_board_websocket_receives_checkpoint(tmp_path):
    settings = Settings(demo_mode=True, database_path=tmp_path / "test.db")
    with TestClient(create_app(settings)) as client:
        with client.websocket_connect("/ws/board") as ws:
            message = ws.receive_json()
            assert message["type"] == "checkpoint"
            assert message["protocol"] == 1
            assert message["width"] > 0 and message["height"] > 0
