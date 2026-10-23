"""Which source windows were actually shot handheld?

The renderer-injected vibration is fixed elsewhere (motion.py, gl/scene.js).
This is about footage that was shaky when it was filmed - red carpets, archive
news, hand-held b-roll.

vidstabdetect writes a transform per frame; the mean translation magnitude of
those transforms is the shake score. Only windows above THRESH get a second
pass, because vidstabtransform crops and softens, and there is no reason to pay
that on a locked-off interview.

Run `python3 stabilise.py` to measure. Until it has been run, trf_for returns
None for everything and the build simply does not stabilise - it never blocks.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# NOT under work5/. The build wipes work5 between runs, and putting the
# transform files there meant a rebuild silently produced no stabilisation at
# all - trf_for just returned None for everything and nothing complained.
TRF = ROOT / "trf"
OUT = ROOT / "manifest" / "shake.json"
SPAN = 2.5
# Residual shake in px/frame at 1920 wide. Measured distribution over 1013
# reachable windows: 50th 1.01, 75th 3.71, 85th 8.77, 95th 17.64. A threshold
# of 1.2 caught 45% of the film, which is not "the handheld ones", it is
# everything - and vidstabtransform crops and softens, so paying it on a
# locked-off interview is a straight loss. Set at the 85th percentile.
THRESH = 8.0

_CACHE: dict | None = None


def _scores() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(OUT.read_text()) if OUT.exists() else {}
    return _CACHE


def _score(vid: str, t: float) -> float:
    """Frame-to-frame camera shake in pixels, at output scale.

    The first version of this parsed vidstabdetect's .trf file as text and
    scored every one of 1013 windows at exactly 0.0. The file is BINARY - it
    starts with the bytes "TRF1" - so the regex matched nothing and the whole
    measurement silently reported "no shaky footage anywhere", which is the
    most dangerous kind of wrong.

    So measure it directly instead. Decode the window small and fast, take the
    global translation between consecutive frames by phase correlation, and
    report the HIGH-FREQUENCY part: a deliberate pan is a smooth trend and must
    not count as shake, so the trend is subtracted first. The result is scaled
    to 1920-wide so the number means pixels the viewer actually sees.
    """
    import cv2
    import numpy as np
    small_w = 320
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", f"hd/{vid}.mp4",
         "-t", str(SPAN), "-vf", f"scale={small_w}:-2,format=gray", "-r", "15",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, cwd=str(ROOT))
    if not r.stdout:
        return 0.0
    buf = np.frombuffer(r.stdout, np.uint8)
    # height is unknown up front; infer it from the byte count
    for h in (180, 176, 182, 240, 160, 136, 168, 240):
        if len(buf) % (small_w * h) == 0 and len(buf) // (small_w * h) >= 6:
            break
    else:
        return 0.0
    n = len(buf) // (small_w * h)
    frames = buf[:n * small_w * h].reshape(n, h, small_w)
    win = cv2.createHanningWindow((small_w, h), cv2.CV_32F)
    steps = []
    prev = None
    for i in range(n):
        f = np.float32(frames[i]); f -= f.mean()
        if prev is not None:
            (dx, dy), _ = cv2.phaseCorrelate(prev, f, win)
            steps.append((dx, dy))
        prev = f
    if len(steps) < 4:
        return 0.0
    a = np.array(steps)
    # detrend: a smooth pan is intent, the residual is shake
    resid = a - np.stack([np.convolve(a[:, k], np.ones(3) / 3, mode="same")
                          for k in range(2)], axis=1)
    return float(np.hypot(resid[:, 0], resid[:, 1]).mean() * (1920 / small_w))


# OFF, and this is a measured reversal rather than an oversight.
#
# Applying vidstabtransform to the 17% of windows that measured shaky made the
# film WORSE, not better. Measured on the finished cut, same shot both builds:
#     #8   lrZKJPVn89s   45.73px -> 51.08px
#     #14  lrZKJPVn89s   48.52px -> 51.81px
#     #24  lrZKJPVn89s   43.19px -> 49.24px
# It also corrupted shot #332 outright - the frame came back as macroblock
# garbage - and cost shot #173 23% of its sharpness (Laplacian variance 435 ->
# 335) plus an unwanted 2% zoom.
#
# Two causes, both real:
#  1. The .trf is generated from an `-ss` seeked segment and applied to another
#     `-ss` seeked segment. Keyframe seeking does not guarantee the same start
#     frame, so the transforms end up misaligned with the frames they correct.
#     Fixing that means decoding each source from zero, which is far too slow.
#  2. The shake metric cannot tell handheld wobble from fast content. The
#     highest scores in the film - 100 to 147 px/frame - are Pvolve campaign
#     close-ups with rapid subject motion and hard cuts, not a shaky camera.
#
# The measurement is kept because it is sound and useful (median 1.0px, 85th
# 8.8px, and it correctly identifies which sources are hand-held). Only the
# TRANSFORM is disabled. Set ENABLED = True to re-enable after fixing (1).
ENABLED = False


def trf_for(vid: str, t: float) -> Path | None:
    """The transform file for this window, or None if it is steady enough
    (or has not been measured yet)."""
    if not ENABLED:
        return None
    key = f"{vid}@{t:.2f}"
    if _scores().get(key, 0.0) < THRESH:
        return None
    p = TRF / f"{vid}_{t:.2f}.trf"
    return p if p.exists() else None


def main() -> None:
    TRF.mkdir(parents=True, exist_ok=True)
    import reels5 as R
    wins = sorted({w for v in R.DUR if v not in R.BANNED
                   for w in R.windows(v, subject=True)})
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [w for w in wins if f"{w[0]}@{w[1]:.2f}" not in have]
    print(f"  {len(wins)} windows, {len(todo)} to measure")
    for i, (vid, t) in enumerate(todo, 1):
        have[f"{vid}@{t:.2f}"] = round(_score(vid, t), 3)
        if i % 100 == 0:
            OUT.write_text(json.dumps(have), encoding="utf-8")
            print(f"    {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have), encoding="utf-8")

    # only the shaky ones need a transform file
    shaky_w = [(v, t) for (v, t) in wins if have.get(f"{v}@{t:.2f}", 0) >= THRESH]
    print(f"  {len(shaky_w)} windows need a .trf")
    for i, (vid, t) in enumerate(shaky_w, 1):
        p = TRF / f"{vid}_{t:.2f}.trf"
        if p.exists():
            continue
        # RELATIVE path, and ffmpeg run from ROOT. An absolute Windows path
        # carries a drive-letter colon, and ffmpeg reads a colon inside a
        # filter argument as the next option: "No option name near
        # '/Users/avina/.../x.trf'".
        rel = p.relative_to(ROOT).as_posix()
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}",
             "-i", f"hd/{vid}.mp4", "-t", str(SPAN),
             "-vf", f"vidstabdetect=shakiness=6:accuracy=12:result={rel}",
             "-f", "null", "-"], check=False, cwd=str(ROOT))
        if i % 25 == 0:
            print(f"    trf {i}/{len(shaky_w)}", flush=True)
    vals = sorted(have.values())
    shaky = sum(1 for v in vals if v >= THRESH)
    if vals:
        pct = lambda q: vals[min(len(vals) - 1, int(len(vals) * q))]
        print(f"\n  percentiles  50th {pct(0.5):.2f}  75th {pct(0.75):.2f}  "
              f"85th {pct(0.85):.2f}  95th {pct(0.95):.2f}")
    print(f"  {shaky} of {len(have)} windows above {THRESH}px/frame "
          f"({shaky / max(1, len(have)) * 100:.0f}%)")


if __name__ == "__main__":
    main()
