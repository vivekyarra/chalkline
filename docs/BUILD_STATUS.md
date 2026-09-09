# CHALKLINE build status

Last updated: 9 September 2026

## Verification completed

- `python -m pytest`: **10 passed**. One third-party Starlette/AnyIO deprecation warning; no test failures.
- Python compile check passed for application, worker, scripts, and tests.
- Rendered teacher console verified with the deterministic source.
- Rendered student flow verified: checkpoint, version advancement, localized stale overlay, historical version view, and return-to-live resync.
- Fixture benchmark smoke run produced `manifest.json` and `metrics.csv`; its figures are intentionally excluded from product claims.

## Implemented

- FastAPI local service with camera/file capture and a clearly labeled deterministic demo source.
- Four-point board calibration and perspective rectification.
- Strict QNN/HTP inference configuration with CPU fallback disabled.
- Native ARM64 inference worker and framed binary IPC for a separate Windows host process.
- Conservative pixel state with unknown/stale tracking, occlusion hold, stable change confirmation, and longer erasure confirmation.
- Lossless 64x64 tile patches, checkpoints, version/epoch checks, browser resync, history, and SQLite event metadata.
- Teacher console, student canvas, stale overlay, history control, reconnection, and LAN WebRTC audio signaling.
- Application-payload comparison harness and constrained-network profile.
- Per-run evidence manifests and structured JSONL events under `evidence/<run-id>/`.
- Focused automated tests for calibration, board-state invariants, patch fidelity, persistence, HTTP pages, and WebSocket checkpoint delivery.

## Required evidence gates

- Obtain and hash the QNN-compatible DeepLabV3-Plus-MobileNet artifact.
- Verify strict QNN graph execution and profiling on the Snapdragon NPU.
- Calibrate a physical chalkboard and record real presenter/hand failure cases.
- Complete the end-to-end camera, browser, audio, erasure, history, and reconnect run.
- Run native ARM64 CPU versus QNN measurements on the same Snapdragon PC.
- Run the controlled wire-level network matrix and generate results.
- Capture the final screenshots and demo recording.

No unmeasured performance, bandwidth, physical-camera, or NPU result is claimed.
