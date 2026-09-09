import base64
import hashlib

import cv2
import numpy as np

from chalkline.patches import encode_tiles


def test_only_changed_tiles_are_encoded_losslessly():
    image = np.arange(96 * 96 * 3, dtype=np.uint8).reshape((96, 96, 3))
    changed = np.zeros((96, 96), bool); changed[70, 70] = True
    tiles = encode_tiles(image, changed, tile_size=64)
    assert len(tiles) == 1
    tile = tiles[0]
    assert (tile.x, tile.y, tile.w, tile.h) == (64, 64, 32, 32)
    decoded = cv2.imdecode(np.frombuffer(tile.png, np.uint8), cv2.IMREAD_COLOR)
    assert np.array_equal(decoded, image[64:96, 64:96])
    payload = tile.json()
    assert hashlib.sha256(base64.b64decode(payload["png"])).hexdigest() == payload["sha256"]
