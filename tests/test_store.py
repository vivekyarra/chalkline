import numpy as np

from chalkline.board_state import BoardState
from chalkline.store import EventStore, load_board_snapshot, save_board_snapshot


def test_event_store_orders_versions(tmp_path):
    store = EventStore(tmp_path / "state.db")
    store.append("s", "e", 2, "update", {"value": 2})
    store.append("s", "e", 1, "update", {"value": 1})
    assert [x["version"] for x in store.list("s", "e")] == [1, 2]
    assert store.list("s", "e", after=1)[0]["payload"]["value"] == 2
    store.close()


def test_atomic_board_snapshot_round_trip(tmp_path):
    state = BoardState((12, 16), mask_hold_frames=0)
    frame = np.full((12, 16, 3), 37, dtype=np.uint8)
    state.observe(frame, np.zeros((12, 16), dtype=bool))
    state.version = 7
    path = tmp_path / "checkpoints" / "latest.npz"
    save_board_snapshot(path, state, {"session_id": "s", "epoch": "e", "calibration_id": "c"})
    restored, metadata = load_board_snapshot(path)
    assert restored.version == 7
    assert np.array_equal(restored.image, state.image)
    assert np.array_equal(restored.valid, state.valid)
    assert metadata["epoch"] == "e"
    assert not path.with_suffix(".npz.tmp").exists()
