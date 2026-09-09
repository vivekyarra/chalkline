from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import cv2
import numpy as np

from chalkline.board_state import BoardState
from chalkline.patches import encode_tiles


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Application-byte comparison; does not emulate wire-level transport")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=float, default=8)
    parser.add_argument("--snapshot-seconds", type=float, default=5)
    args = parser.parse_args()
    cap = cv2.VideoCapture(str(args.input))
    if not cap.isOpened(): raise SystemExit(f"Cannot open {args.input}")
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    stride = max(1, round(source_fps / args.fps))
    state = None; frame_index = 0; rows=[]; totals={"chalkline":0,"snapshots":0,"mjpeg":0}
    while True:
        ok, frame = cap.read()
        if not ok: break
        if frame_index % stride: frame_index += 1; continue
        frame = cv2.resize(frame, (1024, max(256, round(frame.shape[0]*1024/frame.shape[1]))))
        initialized = state is None
        if initialized: state = BoardState(frame.shape[:2], mask_hold_frames=0)
        commit = state.observe(frame, np.zeros(frame.shape[:2], bool))
        if initialized:
            ok_initial, initial_png = cv2.imencode('.png', state.image, [cv2.IMWRITE_PNG_COMPRESSION, 6])
            patch_bytes = len(initial_png) if ok_initial else 0
        else:
            patch_bytes = sum(len(t.png) for t in encode_tiles(commit.image, commit.changed_mask)) if commit else 0
        ok_jpg,jpg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,55]); mjpeg=len(jpg) if ok_jpg else 0
        seconds=frame_index/source_fps; snapshot=0
        if round(seconds*args.fps) % max(1,round(args.snapshot_seconds*args.fps))==0:
            ok_png,png=cv2.imencode('.png',frame,[cv2.IMWRITE_PNG_COMPRESSION,6]); snapshot=len(png) if ok_png else 0
        for k,v in (("chalkline",patch_bytes),("snapshots",snapshot),("mjpeg",mjpeg)): totals[k]+=v
        rows.append({"source_seconds":round(seconds,3),"chalkline_bytes":patch_bytes,"snapshot_bytes":snapshot,"mjpeg_bytes":mjpeg})
        frame_index += 1
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys() if rows else []);w.writeheader();w.writerows(rows)
    manifest={"label":"application-layer encoded payload comparison","created_ms":int(time.time()*1000),
              "input":args.input.name,"input_sha256":file_hash(args.input),"processing_fps":args.fps,
              "snapshot_seconds":args.snapshot_seconds,"totals":totals,
              "limitations":["No audio","No protocol or transport headers","No packet loss/delay shaping","MJPEG is a diagnostic baseline, not tuned H.264/WebRTC"]}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2)); return 0

if __name__ == '__main__': raise SystemExit(main())
