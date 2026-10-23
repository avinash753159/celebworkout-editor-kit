"""Five frames across EVERY source in a pool, tiled, so you can SEE what a
source actually is before it reaches the cut.

Why this exists
---------------
Two defects reached the V9 cut that no mechanical gate could catch:

  * `jD2V79_dNuQ` is a fan-made slideshow - a "OneTrueMedia.com" promo bumper
    at head and tail, two full-frame ELLE covers with mastheads, and
    pillarboxed B&W editorial spreads between. Every window is a magazine
    graphic. It played a full-frame ELLE cover 7.4s into the film.
  * `-MXQ_3DNX_Y`'s last allowed window (TAIL = MAX_SHOT + 3.0) is a full-frame
    "WATCH MORE / SUBSCRIBE" end card.

Both score fine on identity - the magazine covers genuinely depict her - and
both survive the cut check, because a slideshow with a Ken Burns push has
normal inter-frame motion. Two mechanical detectors were tried and neither
discriminated:

    pillarbox fraction   flags the SAG podium (dark background) as heavily
                         letterboxed: false positives everywhere
    inter-frame motion   jD2V79_dNuQ scores 6.8% static, the same as real
                         footage, because each still is pushed

So there is no cheap signature. The sweep must be visual, and this makes it
cheap to do once for the whole pool instead of discovering one bad window per
build.

    python3 src_sweep.py                 # every source in manifest/shots6.json
    python3 src_sweep.py --all           # every source in hd/, cut or not
    python3 src_sweep.py --pool turn     # one pool

Writes qc/srcsweep/SRC_*.jpg. READ THEM. Look for: a full-frame magazine
cover or masthead, a service bumper ("created at ..."), a SUBSCRIBE / WATCH
MORE end card, a channel ident, a title card, a face that is not hers.
"""
from __future__ import annotations

import collections
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "qc" / "srcsweep"
CACHE = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

W, H, LBL = 300, 169, 22
PER_SHEET = 11
# fractions through the source. The head and tail matter most - that is where
# idents, title cards and subscribe screens live - so sample them tightly.
FRACS = (0.02, 0.25, 0.5, 0.75, 0.98)

DUR = json.loads((ROOT / "manifest" / "hd_dur.json").read_text(encoding="utf-8"))


def sources() -> list[tuple[str, int]]:
    if "--all" in sys.argv:
        vids = sorted(p.stem for p in (ROOT / "hd").glob("*.mp4"))
        return [(v, 0) for v in vids]
    if "--pool" in sys.argv:
        import reels5
        name = sys.argv[sys.argv.index("--pool") + 1]
        pool = reels5.POOLS[name]
        c = collections.Counter(v for v, _ in pool
                                if not str(v).startswith(("still:", "split:")))
        return c.most_common()
    shots = json.loads((ROOT / "manifest" / "shots6.json").read_text(encoding="utf-8"))
    c = collections.Counter(
        str(r["tag"]) for r in shots["shots"]
        if not str(r["tag"]).startswith(("still:", "split:")))
    return c.most_common()


def grab(vid: str, t: float, idx: int) -> Path | None:
    p = CACHE / f"{vid}_{idx}.jpg"
    if p.exists():
        return p
    src = ROOT / "hd" / f"{vid}.mp4"
    if not src.exists():
        return None
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.1f}", "-i", str(src),
                    "-frames:v", "1", "-vf", f"scale={W}:{H}", str(p)], check=False)
    return p if p.exists() else None


def main() -> None:
    srcs = sources()
    srcs = [(v, n) for v, n in srcs if (ROOT / "hd" / f"{v}.mp4").exists()]
    print(f"{len(srcs)} sources")
    try:
        F = ImageFont.truetype("arialbd.ttf", 14)
    except Exception:
        F = ImageFont.load_default()

    for si in range(0, len(srcs), PER_SHEET):
        chunk = srcs[si:si + PER_SHEET]
        sheet = Image.new("RGB", (len(FRACS) * W, len(chunk) * (H + LBL)), (8, 8, 10))
        d = ImageDraw.Draw(sheet)
        for j, (vid, n) in enumerate(chunk):
            dur = DUR.get(vid) or 60.0
            y = j * (H + LBL)
            d.text((4, y + 3), f"{vid}   {n} shots   dur {dur:.0f}s",
                   font=F, fill=(255, 225, 110))
            for i, f in enumerate(FRACS):
                p = grab(vid, dur * f, i)
                if p:
                    try:
                        sheet.paste(Image.open(p).convert("RGB"), (i * W, y + LBL))
                    except Exception:
                        pass
        o = OUT / f"SRC_{si // PER_SHEET:02d}.jpg"
        sheet.save(o, quality=86)
        print("wrote", o)


if __name__ == "__main__":
    main()
