"""Measure what the picture actually does, frame to frame.

zoompan floors the crop origin AND the crop size independently. The two
staircases step at different rates, so the image drifts ~0.38px one way for
three frames then jumps ~0.11px BACK. Measured on shot 193, which is a still
image, so nothing in it can move except by the renderer:
    dx: -0.53 -0.35 -0.34 -0.35 +0.17 -0.34 -0.34 -0.35 -0.50 ...
    28 direction reversals in 88 frames
That is the shake. This module is how we prove it is gone.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent


def frames_of(mp4: Path, t0: float, n: int, outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    if not list(outdir.glob("*.png")):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
                        "-i", str(mp4), "-frames:v", str(n), "-vsync", "0",
                        str(outdir / "f%03d.png")], check=False)
    return sorted(outdir.glob("*.png"))


def _steps(paths, box):
    x, y, w, h = box
    win = cv2.createHanningWindow((w, h), cv2.CV_32F)
    prev, out = None, []
    for p in paths:
        g = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if g is None:
            continue
        patch = np.float32(g[y:y + h, x:x + w])
        patch -= patch.mean()
        if prev is not None:
            (dx, dy), _ = cv2.phaseCorrelate(prev, patch, win)
            out.append((dx, dy))
        prev = patch
    return np.array(out) if out else np.zeros((0, 2))


def jitter(paths, box=(300, 220, 420, 420)) -> dict:
    d = _steps(paths, box)
    if len(d) < 3:
        return dict(mean=0.0, sd=0.0, ratio=99.0, reversals=99)
    mag = np.hypot(d[:, 0], d[:, 1])
    dx = d[:, 0]
    reversals = int(np.sum(np.sign(dx[1:]) != np.sign(dx[:-1])))
    return dict(mean=float(mag.mean()), sd=float(mag.std()),
                ratio=float(mag.std() / max(1e-9, mag.mean())),
                reversals=reversals)


def parallax(paths, near_box, far_box) -> float:
    """Near things must travel further than far things. Flat scaling gives
    1.0 by construction; a real dolly gives more."""
    n = float(np.hypot(*_steps(paths, near_box).T).sum())
    f = float(np.hypot(*_steps(paths, far_box).T).sum())
    return n / max(1e-9, f)


GATE_JERK = 0.35
# Not 0. Phase correlation on a low-texture patch can register one spurious
# sign flip in a 60-frame shot, and p_diner did exactly that while scoring
# jerk 0.115 - clean motion by every other measure. The defect this gate
# exists to catch scored 74 reversals AND jerk 1.203, so a ceiling of 2 still
# fails it by a factor of thirty. Jerk is the primary gate; reversals are the
# backstop.
GATE_REVERSALS = 2


def jerk(paths, box=(300, 220, 420, 420)) -> float:
    """How much the step CHANGES from frame to frame, relative to its size.

    `sd/mean` was the wrong gate and it was my mistake, not the renderer's.
    The new renderer eases in and out with a smoothstep, so the step is 0 at
    the start, peaks in the middle and returns to 0 - a large sd/mean is the
    SIGNATURE OF EASING, not of jitter. A linear ramp would score well on
    sd/mean while a beautifully eased move would fail.

    The second difference does not care about the shape of the ramp, only
    about whether it is continuous. A smooth ease has small, slowly varying
    second differences; zoompan's competing staircases have large alternating
    ones.
    """
    d = _steps(paths, box)
    if len(d) < 4:
        return 99.0
    mag = np.hypot(d[:, 0], d[:, 1])
    return float(np.diff(mag, 2).std() / max(1e-9, mag.mean()))


def report(name: str, paths, box=(300, 220, 420, 420)) -> bool:
    j = jitter(paths, box)
    jk = jerk(paths, box)
    ok = jk <= GATE_JERK and j["reversals"] <= GATE_REVERSALS
    print(f"  {name:<24} step {j['mean']:.3f}px  jerk {jk:.3f}  "
          f"reversals {j['reversals']}  {'PASS' if ok else 'FAIL'}")
    return ok


def depth_response(mp4: Path, depth_png: Path, n: int = 60) -> float:
    """Does the picture move MORE where the scene is NEAR?

    The first parallax metric compared a "near" box against a "far" box and was
    worthless: both boxes landed on low-texture regions (bare floor, blown-out
    window) where phase correlation is noise, and it reported 1.03 for a render
    that provably displaced its geometry.

    Radius from frame centre dominates optical flow in any zoom, so this bins
    pixels by radius and, WITHIN each bin, correlates flow magnitude against
    depth. That isolates the depth term from the radial one. Flat scaling
    scores ~0. Real parallax scores positive.
    """
    cap = cv2.VideoCapture(str(mp4))
    ok, first = cap.read()
    if not ok:
        cap.release(); return 0.0
    last = first
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        last = fr
    cap.release()
    a = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(last, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 25, 3, 5, 1.2, 0)
    mag = np.hypot(flow[..., 0], flow[..., 1])
    h, w = mag.shape
    dep = cv2.resize(cv2.imread(str(depth_png), cv2.IMREAD_GRAYSCALE), (w, h))
    yy, xx = np.mgrid[0:h, 0:w]
    rad = np.hypot(yy - h / 2, xx - w / 2)
    out = []
    for lo in range(0, int(rad.max()), 60):
        m = (rad >= lo) & (rad < lo + 60)
        if m.sum() < 5000:
            continue
        d = dep[m].astype(np.float64)
        f = mag[m].astype(np.float64)
        if d.std() < 4 or f.std() < 1e-6:
            continue
        out.append(float(np.corrcoef(d, f)[0, 1]))
    return float(np.mean(out)) if out else 0.0
