# Board protocol v1

Each lesson has a `session_id` and each calibration has an `epoch`. Board versions increase monotonically inside an epoch. A patch is valid only when its `base_version` equals the receiver's applied version and its epoch matches.

The current browser transport uses JSON WebSocket messages so evidence is easily inspectable. Tile and checkpoint PNGs are base64 fields. The native inference subprocess uses length-prefixed binary messages: little-endian uint32 JSON length, JSON header, then the declared raw tensor bytes.

Checkpoint messages carry the full lossless board image, valid-pixel mask, stale-pixel mask, dimensions, epoch, and current version. Patch messages carry changed lossless 64x64 tiles, hashes, version transition, timestamps, and stale mask. A gap or epoch mismatch makes the receiver request a checkpoint.

The board image and stale overlay are separate. Occluded pixels retain their last verified image value. Never-observed pixels stay invalid. The receiver preserves its last board during disconnect and enters `DISCONNECTED`, then `SYNCING`, then `LIVE` after a valid checkpoint.

Current MVP limitation: event metadata is durable in SQLite, while full historical image snapshots are retained in memory for the active lesson. Durable image checkpoints and contiguous delta replay remain a release gate.
