"""Presence index — does this window actually contain a face?

F1 and F2 in REMEDIATION.md, and the worst defects in the V5 cut: Jimmy Kimmel
alone at his desk four times, Colbert three times (once introducing Usher),
Reese Witherspoon alone twice, a GMA panel of five strangers — in a video about
Jennifer Aniston. Her quote "every Sunday is a cheat day" played over Colbert's
face.

Cause: no pool has ever been checked for whether the subject is on screen. Every
window is a source id and a timecode I assumed was her.

This samples each candidate window, runs a face detector, and records:
  faces      how many
  biggest    area of the largest face as a fraction of frame
Windows with no face cannot carry a line about her. Windows with several faces
and no dominant one are panels and are also excluded from subject lines.

This does not identify WHO the face is - that needs the eyeball pass in pass 1,
which is why the talk-show sources get looked at by hand afterwards.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "manifest" / "presence.json"

CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
PROFILE = cv2.data.haarcascades + "haarcascade_profileface.xml"


def grab(vid: str, t: float, w: int = 480) -> np.ndarray | None:
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(ROOT / "hd" / f"{vid}.mp4"),
         "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "4", "-"], capture_output=True)
    if not r.stdout:
        return None
    arr = np.frombuffer(r.stdout, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def faces_in(img) -> tuple[int, float]:
    if img is None:
        return 0, 0.0
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.equalizeHist(g)
    H, W = g.shape[:2]
    found = []
    for path in (CASCADE, PROFILE):
        c = cv2.CascadeClassifier(path)
        if c.empty():
            continue
        for (x, y, w, h) in c.detectMultiScale(g, 1.12, 5, minSize=(int(W*0.05), int(W*0.05))):
            found.append((x, y, w, h))
    if not found:
        return 0, 0.0
    # crude de-dup between the two cascades
    keep = []
    for f in sorted(found, key=lambda b: -b[2] * b[3]):
        if all(abs(f[0]-k[0]) > k[2]*0.5 or abs(f[1]-k[1]) > k[3]*0.5 for k in keep):
            keep.append(f)
    biggest = max(w * h for _, _, w, h in keep) / float(W * H)
    return len(keep), round(biggest, 4)


def candidate_windows():
    """Every window worth SCORING, with no identity gate applied.

    POOLS is built by spool(), which passes subject=True - so it only contains
    windows that ALREADY have an identity score above the threshold. Both this
    index and recognise.py used to enumerate from POOLS, which meant a newly
    added source could never be scored: no score -> _has_subject fails closed
    -> no windows in POOLS -> never scored. 111 sources added in pass 14 all
    landed in that deadlock.

    So enumerate from the raw source lists instead. This is the bootstrap.
    """
    import reels5 as R
    vids = set()
    for name in dir(R):
        if name.endswith("_SRC") or name in ("DEMO_CLEAN",):
            v = getattr(R, name)
            if isinstance(v, (list, set, tuple)):
                vids |= {x for x in v if isinstance(x, str)}
    vids = {v for v in vids if v not in R.BANNED and v in R.DUR}
    out = set()
    for v in sorted(vids):
        out |= set(R.windows(v))
    return sorted(out)


def main() -> None:
    wins = candidate_windows()
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [w for w in wins if f"{w[0]}@{w[1]}" not in have]
    print(f"  {len(wins)} windows, {len(todo)} to check")
    for i, (vid, t) in enumerate(todo, 1):
        n, big = faces_in(grab(vid, t))
        have[f"{vid}@{t}"] = {"faces": n, "biggest": big}
        if i % 250 == 0:
            OUT.write_text(json.dumps(have), encoding="utf-8")
            print(f"    {i}/{len(todo)}")
    OUT.write_text(json.dumps(have), encoding="utf-8")
    noface = sum(1 for v in have.values() if v["faces"] == 0)
    panel = sum(1 for v in have.values() if v["faces"] >= 3)
    print(f"\n  indexed {len(have)}")
    print(f"    no face at all : {noface} ({noface/len(have)*100:.0f}%)")
    print(f"    3+ faces (panel): {panel} ({panel/len(have)*100:.0f}%)")


if __name__ == "__main__":
    main()
