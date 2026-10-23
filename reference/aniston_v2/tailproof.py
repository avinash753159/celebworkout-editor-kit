"""Render the LAST ALLOWED WINDOW of every source, and its first, so the tail
rule can be read rather than argued about.

reels5.tail_for() decides how close to the end of a file a window may start.
It is a formula plus a table, and a formula that has not been looked at is a
guess. This takes the real output of reels5.windows() - so it sees the bans,
the brightness gate and the cut gate too - and tiles, per source:

    col 0   the FIRST allowed window          (head title cards live here)
    col 1   the LAST allowed window, at t0    (end cards live here)
    col 2   the same window at +2.1s
    col 3   the same window at +4.2s
    col 4   the same window at +6.4s = MAX_SHOT, the last frame a shot
            starting there could reach

Writes qc/srcsweep/TAIL_*.jpg. READ THEM. Anything that is a graphic at any of
columns 1-4 needs a reels5.TAIL_EXTRA entry; anything graphic at column 0
needs a BANNED_WINDOW entry at the head.

    python3 tailproof.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import reels5 as R

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "qc" / "srcsweep"
CACHE = OUT / "tailframes"
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

W, H, LBL = 300, 169, 22
PER_SHEET = 11


def grab(vid: str, t: float, tag: str) -> Path | None:
    p = CACHE / f"{vid}_{tag}_{t:.1f}.jpg"
    if p.exists():
        return p
    src = ROOT / "hd" / f"{vid}.mp4"
    if not src.exists():
        return None
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src),
                    "-frames:v", "1", "-vf", f"scale={W}:{H}", str(p)], check=False)
    return p if p.exists() else None


def main() -> None:
    vids = sorted(p.stem for p in (ROOT / "hd").glob("*.mp4"))
    rows = []
    for v in vids:
        w = R.windows(v)
        if not w:
            continue
        rows.append((v, w[0][1], w[-1][1]))
    print(f"{len(rows)} sources with windows")
    try:
        F = ImageFont.truetype("arialbd.ttf", 14)
    except Exception:
        F = ImageFont.load_default()

    for si in range(0, len(rows), PER_SHEET):
        chunk = rows[si:si + PER_SHEET]
        sheet = Image.new("RGB", (5 * W, len(chunk) * (H + LBL)), (8, 8, 10))
        d = ImageDraw.Draw(sheet)
        for j, (vid, first, last) in enumerate(chunk):
            y = j * (H + LBL)
            dur = R.DUR[vid]
            d.text((4, y + 3),
                   f"{vid}   dur {dur:.0f}s   first {first:.1f}   "
                   f"LAST {last:.1f}   (tail margin {dur - last:.1f}s)",
                   font=F, fill=(255, 225, 110))
            pts = [(first, "head")] + [(last + o, "tail") for o in (0.0, 2.1, 4.2, 6.4)]
            for i, (t, tag) in enumerate(pts):
                p = grab(vid, min(t, dur - 0.1), tag)
                if p:
                    try:
                        sheet.paste(Image.open(p).convert("RGB"), (i * W, y + LBL))
                    except Exception:
                        pass
        o = OUT / f"TAIL_{si // PER_SHEET:02d}.jpg"
        sheet.save(o, quality=86)
        print("wrote", o)


if __name__ == "__main__":
    main()
