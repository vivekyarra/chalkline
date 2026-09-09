# Benchmark protocol

`scripts/run_benchmark.py` generates a reproducible application-payload diagnostic from a fixed input recording. It records source hash, configuration, per-frame bytes, totals, and limitations. It counts CHALKLINE's initial lossless checkpoint and later PNG tile bytes, periodic full-board PNG bytes, and MJPEG diagnostic bytes.

Example:

```powershell
.venv\Scripts\python.exe scripts\run_benchmark.py data\lesson.mp4 --output evidence\application-run-001
```

To smoke-test the harness before recording the physical lesson, generate the visibly labeled deterministic fixture:

```powershell
.venv\Scripts\python.exe scripts\make_fixture.py --output evidence\fixture.mp4
```

Fixture output verifies the harness only and must never appear in measured product claims.

This diagnostic excludes audio, WebSocket headers, IP/transport overhead, packet loss, and WebRTC behavior. It cannot support a total-link 64 kbps claim and its MJPEG stream is not the final tuned video baseline.

The final comparison follows `bench/profiles/constrained.json`: CHALKLINE, tuned low-frame-rate video, and periodic snapshots at 64/128/256 decimal kbps, with three fixed seeds, 100 ms added one-way delay, 1% random loss, and a ten-second outage. All teacher-to-student audio/control/media traffic must traverse one verified constrained route. Packet capture must establish that routing and define the byte boundary.

Every result directory must contain a manifest, raw metrics/events, failures, and predetermined receiver captures. Keep unsuccessful runs. Generate summaries from those files instead of entering headline numbers manually.
