"""Flag the title-card and credit ranges inside each source.

F5: the V5 cut showed a "WE'RE THE MILLERS" title, "DIRECTED BY" trailer
credits, and a "JENNIFER ANISTON" name super from somebody else's package. V3
banned whole sources for this; that threw away good footage. This flags RANGES
instead, so a trailer can still be used for its actual pictures.

Detection is deliberately crude and errs toward excluding: a frame is "graphic"
if it is very dark AND has high edge density in the middle band (white text on
black), or if it is extremely low-saturation with strong horizontal structure.
Trailer cards live at heads and tails, so those get sampled densely.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "manifest" / "branding.json"

# sources that are trailers / packaged clips - these carry cards
SUSPECT = ["P3IsUOSHlnU", "Ws-9ra38AlI", "JlpIdAmkT_k", "7mM-82tY-ts",
           "BrbwSDa3crU", "oZaoendJ5GQ", "cZh-kPkKcvU", "XbywiblA1eQ",
           "Xm0jeY5Mp5c", "wR1SuuB-hWI", "_K3cpT4-upk", "Ny0zaM7RNg0",
           "aNAAWzLOEKc", "asBfqGQ7b6E", "vPrtuy_4lHM"]


def grab(vid, t):
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(ROOT/"hd"/f"{vid}.mp4"),
         "-frames:v", "1", "-vf", "scale=320:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "5", "-"], capture_output=True)
    if not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)


def is_card(img) -> bool:
    if img is None:
        return False
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    dark = g.mean() < 62
    flat = hsv[:, :, 1].mean() < 26          # almost no colour
    edges = cv2.Canny(g, 90, 200)
    band = edges[int(g.shape[0]*0.3):int(g.shape[0]*0.75), :]
    texty = band.mean() > 7
    return (dark and texty) or (flat and texty and g.std() > 55)


def main():
    dur = json.loads((ROOT/"manifest"/"hd_dur.json").read_text())
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for vid in SUSPECT:
        if vid in out or vid not in dur:
            continue
        d = dur[vid]
        ranges, run = [], None
        # dense at head and tail, sparse in the middle
        pts = [round(x, 1) for x in
               list(np.arange(0, min(25, d), 1.0)) +
               list(np.arange(25, max(25, d-25), 4.0)) +
               list(np.arange(max(0, d-25), d-1, 1.0))]
        for t in pts:
            card = is_card(grab(vid, t))
            if card and run is None:
                run = t
            elif not card and run is not None:
                ranges.append([run, t]); run = None
        if run is not None:
            ranges.append([run, d])
        merged = []
        for a, b in ranges:
            if merged and a - merged[-1][1] < 3.0:
                merged[-1][1] = b
            else:
                merged.append([a, b])
        out[vid] = merged
        tot = sum(b-a for a, b in merged)
        print(f"  {vid:<14} {len(merged):>2} graphic ranges, {tot:5.1f}s excluded")
        OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n  flagged {len(out)} sources")


if __name__ == "__main__":
    main()
