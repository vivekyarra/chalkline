from chalkline.store import EventStore


def test_event_store_orders_versions(tmp_path):
    store = EventStore(tmp_path / "state.db")
    store.append("s", "e", 2, "update", {"value": 2})
    store.append("s", "e", 1, "update", {"value": 1})
    assert [x["version"] for x in store.list("s", "e")] == [1, 2]
    assert store.list("s", "e", after=1)[0]["payload"]["value"] == 2
    store.close()
