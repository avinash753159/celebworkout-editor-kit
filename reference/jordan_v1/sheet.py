"""Contact sheets — the only instrument that has ever found a real defect here.

Every defect that mattered on the previous build was found by looking: a
ten-second static open, twenty-four identical talking heads, stale exercise
cards, a repeated place label, a full-frame Eminem magazine spread, a portrait
pillarboxed into a narrow strip. All of them passed every automated check that
existed at the time.

Two rules baked in, both learned by getting them wrong:

- **Sample the MIDDLE of a span, never the end.** Sampling 1.2s before a span's
  exit lands on the NEXT shot's first frame and invents defects that are not
  there - it produced six false defect reports on the previous build.
- **Render large.** A 300px thumbnail is too small to judge identity on. On this
  build a frame was rejected by eye as "not Jordan" off a 300px sheet, and at
  560px it was plainly him; the recogniser had been right.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def grid(tiles: list[tuple[np.ndarray, str]], dest: Path, cols: int = 3,
         w: int = 440) -> Path:
    """Label each tile, pad the last row, write the sheet."""
    imgs = []
    for im, label in tiles:
        if im is None:
            continue
        h = max(1, int(w * im.shape[0] / im.shape[1]))
        im = cv2.resize(im, (w, h))
        im = cv2.copyMakeBorder(im, 26, 3, 3, 3, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        cv2.putText(im, label[:46], (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 255, 255), 1)
        imgs.append(im)
    if not imgs:
        return dest
    H = max(i.shape[0] for i in imgs)
    imgs = [cv2.copyMakeBorder(i, 0, H - i.shape[0], 0, 0, cv2.BORDER_CONSTANT,
                               value=(0, 0, 0)) for i in imgs]
    blank = np.zeros_like(imgs[0])
    while len(imgs) % cols:
        imgs.append(blank)
    rows = [np.hstack(imgs[i:i + cols]) for i in range(0, len(imgs), cols)]
    cv2.imwrite(str(dest), np.vstack(rows))
    return dest


def mid_frame(video: Path) -> np.ndarray | None:
    """The MIDDLE frame of a piece. Never the last."""
    cap = cv2.VideoCapture(str(video))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if n <= 0:
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_POS_FRAMES, n // 2)
    ok, fr = cap.read()
    cap.release()
    return fr if ok else None


def at(video: Path, t: float, w: int = 640) -> np.ndarray | None:
    import subprocess
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video),
         "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "3", "-"], capture_output=True)
    if not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
