"""Put the photographs into the frame the renderer actually draws.

WHY THIS EXISTS. gl/scene.js builds a PlaneGeometry at the OUTPUT aspect
(job.w / job.h = 16:9) and maps the texture across it with the default 0..1
UVs. There is no cover, no contain and no letterbox anywhere in the shader.
Every generated still in this project is exactly 1024x576 or 1920x1080, so
that has always been a no-op and nobody has had to know.

Fifteen of the nineteen photographs are PORTRAIT - 2560x3718, 1000x1434,
1242x1863. Mapped onto a 16:9 plane a 0.69-aspect picture is stretched 2.6x
horizontally: her face comes out three times as wide as it is tall. That is
not a subtle grade problem, it is the single most obvious defect a viewer
could find, and it would have shipped the first time a photograph reached a
pool - which is this pass.

WHAT IT DOES. Writes photos_169/<same filename> at 1920x1080:

  * 16:9 or wider  -> centre-crop. Nothing is invented and nothing is lost
                      that was not already outside a 16:9 frame.
  * taller than 16:9 -> the sharp photograph is fitted to full height and
                      centred, over a blurred, darkened, cover-scaled copy of
                      itself. NOT over black: black bars are the pillarbox
                      defect that got CsLRK1JphL4 banned outright, and a
                      viewer reads them as a phone video. reels5's note on
                      p_hairtimeline records the same decision - "letterboxed
                      onto a blurred copy of itself rather than onto black".

Everything downstream keys on the file, not the directory: build5._still_path
and semantic._still_file prefer photos_169, depth_gen reads it, and
still_sig() fingerprints on size and mtime, so a re-crop invalidates the
rendered piece by itself.

    python3 photo_frame.py     # then depth_gen.py, then semantic.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "photos"
DST = ROOT / "photos_169"
W, H = 1920, 1080
TARGET = W / H
BLUR = 42          # px at 1920 wide
DIM = 0.42         # the background is a texture, not a second picture


def frame(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
    a = im.width / im.height
    # 1% tolerance. 1600x901 is 1.7758 against 16:9's 1.7778 - a rounding
    # difference from whoever encoded it, not a shape - and an exact
    # comparison sent it down the letterbox path and put blurred bars either
    # side of a picture that already fits.
    if a >= TARGET * 0.99:
        # crop the sides
        nh = H
        nw = int(round(im.width * nh / im.height))
        r = im.resize((max(nw, W), nh), Image.LANCZOS)
        x = (r.width - W) // 2
        return r.crop((x, 0, x + W, H))
    # portrait: blurred cover behind, sharp fit in front
    cover_w = int(round(im.width * H / im.height))
    bg = im.resize((max(W, cover_w), H), Image.LANCZOS)
    if bg.width < W or bg.height < H:
        bg = bg.resize((W, H), Image.LANCZOS)
    # scale the cover up so the blur has material outside the frame to smear
    bw = int(round(im.width * (W / im.width)))
    bh = int(round(im.height * (W / im.width)))
    if bh < H:
        bh = H
        bw = int(round(im.width * H / im.height))
    bg = im.resize((bw, bh), Image.LANCZOS)
    bg = bg.crop(((bw - W) // 2, (bh - H) // 2,
                  (bw - W) // 2 + W, (bh - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(BLUR))
    bg = ImageEnhance.Brightness(bg).enhance(DIM)
    fw = int(round(im.width * H / im.height))
    fg = im.resize((fw, H), Image.LANCZOS)
    bg.paste(fg, ((W - fw) // 2, 0))
    return bg


def main() -> None:
    DST.mkdir(exist_ok=True)
    n = 0
    for p in sorted(SRC.glob("*.jpg")):
        out = DST / p.name
        if out.exists() and out.stat().st_mtime >= p.stat().st_mtime:
            continue
        im = Image.open(p)
        a = im.width / im.height
        frame(im).save(out, quality=94, subsampling=0)
        print(f"  {p.name[:46]:<48} {im.width}x{im.height} ({a:.2f}) -> "
              f"{'crop' if a >= TARGET * 0.99 else 'blurred letterbox'}")
        n += 1
    print(f"  {n} written, {len(list(DST.glob('*.jpg')))} in photos_169/")


if __name__ == "__main__":
    main()
