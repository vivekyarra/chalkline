# Board protocol v1

Each lesson has a `session_id` and each calibration has an `epoch`. Board versions increase monotonically inside an epoch. A patch is valid only when its `base_version` equals the receiver's applied version and its epoch matches.

The current browser transport uses JSON WebSocket messages so evidence is easily inspectable. Tile and checkpoint PNGs are base64 fields. The native inference subprocess uses length-prefixed binary messages: little-endian uint32 JSON length, JSON header, then the declared raw tensor bytes.

Checkpoint messages carry the full lossless board image, valid-pixel mask, stale-pixel mask, dimensions, epoch, and current version. Patch messages carry changed lossless 64x64 tiles, hashes, version transition, timestamps, and stale mask. A gap or epoch mismatch makes the receiver request a checkpoint.

The board image and stale overlay are separate. Occluded pixels retain their last verified image value. Never-observed pixels stay invalid. The receiver preserves its last board during disconnect and enters `DISCONNECTED`, then `SYNCING`, then `LIVE` after a valid checkpoint.

Event metadata is durable in SQLite. The latest board image, validity mask, stale mask, version, session, and epoch are saved through an atomic compressed checkpoint and recovered after a process restart when calibration matches. Full historical image snapshots remain in memory for the active lesson; durable navigation through every historical version and contiguous delta replay across a restart remain a release gate.
