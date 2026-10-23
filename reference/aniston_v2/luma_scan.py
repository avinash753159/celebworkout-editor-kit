"""Per-source luminance map, so the assembler never cuts to a dead frame.

A post-build scan found 16 of 364 shots sitting at mean luma under 26 - most of
them the amber silhouette stretch of the Pvolve campaign film, which two reel
start points walked straight into, repeatedly. Fixing those by hand would fix
this cut and not the next one.

This samples every source once (a single ffmpeg pass per file, a frame every
1.5s) and writes a luma track. `reels4.Reels` consults it and skips a position
that is too dark, which makes the whole class of defect impossible rather than
merely absent.
"""
from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "manifest" / "luma.json"
STEP = 1.5


def scan(vid: str) -> list[float]:
    """One pass over the file, a small frame every STEP seconds."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(ROOT / "hd" / f"{vid}.mp4"),
         "-vf", f"fps=1/{STEP},scale=96:54", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "8", "-"],
        capture_output=True)
    out, data = [], r.stdout
    start = 0
    SOI, EOI = b"\xff\xd8", b"\xff\xd9"
    while True:
        a = data.find(SOI, start)
        if a < 0:
            break
        b = data.find(EOI, a)
        if b < 0:
            break
        try:
            im = Image.open(io.BytesIO(data[a:b + 2])).convert("L")
            out.append(round(ImageStat.Stat(im).mean[0], 1))
        except Exception:
            out.append(-1.0)
        start = b + 2
    return out


def main() -> None:
    from reels4 import POOLS
    vids = sorted({r[0] for p in POOLS.values() for r in p
                   if not r[0].startswith(("still:", "split:"))})
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    for i, v in enumerate(vids, 1):
        if v in have:
            print(f"  [{i:>2}/{len(vids)}] {v} cached")
            continue
        t = scan(v)
        have[v] = t
        dark = sum(1 for x in t if 0 <= x < 26)
        print(f"  [{i:>2}/{len(vids)}] {v:<14} {len(t):>4} samples  "
              f"{dark:>3} dark ({dark/max(1,len(t))*100:.0f}%)")
        OUT.write_text(json.dumps(have), encoding="utf-8")
    OUT.write_text(json.dumps(have), encoding="utf-8")
    print(f"\n  wrote {OUT.name}, {len(have)} sources, step {STEP}s")


if __name__ == "__main__":
    main()
