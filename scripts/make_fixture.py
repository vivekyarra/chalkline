from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from chalkline.capture import demo_frame


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clearly labeled deterministic CHALKLINE test fixture")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=25)
    parser.add_argument("--fps", type=float, default=8)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(args.output), cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (1280, 720))
    if not writer.isOpened():
        raise SystemExit("Cannot create MP4 fixture")
    for tick in range(round(args.seconds * args.fps)):
        frame, _ = demo_frame(tick)
        cv2.putText(frame, "DETERMINISTIC TEST FIXTURE", (760, 680), cv2.FONT_HERSHEY_SIMPLEX,
                    .65, (120, 210, 230), 2, cv2.LINE_AA)
        writer.write(frame)
    writer.release()
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
