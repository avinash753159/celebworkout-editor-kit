"""Thumbnail v4 — the channel's actual formula, traced off six of their own.

Their layout is fixed across the catalogue (Statham, Bucky Barnes, Yamal,
Halle Berry, and their own Aniston):

  - subject on the RIGHT, bright background, looking at camera
  - headline stacked on the LEFT in huge condensed caps, lines alternating
    WHITE and BLACK so it reads against any background
  - a RED rectangle label with the celebrity's name in white caps
  - a food inset low-left on the newer ones

V3's thumbnail was a dark moody portrait with a hook line. That is a different
channel's aesthetic. This is theirs.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from graphics4 import RED, anton, black

ROOT = Path(__file__).resolve().parent
TW, TH = 1280, 720

# bright, looking toward camera, from the campaign film
SRC_ID, SRC_T = "JJLe4jmbrN0", 3.4   # face to camera, upright, bright room
ACT = (0, 1920)                      # this source is full-frame, not pillarboxed
FOOD = ROOT / "stills_food" / "f_saladbowl.jpg"


def grab(vid: str, t: float) -> Image.Image:
    out = ROOT / "work4" / f"thumb_{vid}_{t}.png"
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i",
                    str(ROOT / "hd" / f"{vid}.mp4"), "-frames:v", "1",
                    str(out), "-y"], check=True)
    return Image.open(out).convert("RGB")


def main() -> None:
    src = grab(SRC_ID, SRC_T).filter(
        ImageFilter.UnsharpMask(radius=3, percent=90, threshold=3))
    sw, sh = src.size
    ax, aw = ACT

    # Subject fills the right half. Crop a tall slice of the active area.
    crop_h = int(sh * 0.98)
    crop_w = int(crop_h * 0.72)
    cx = ax + int(aw * 0.47) - crop_w // 2
    cx = max(ax, min(cx, ax + aw - crop_w))
    person = src.crop((cx, int(sh * 0.02), cx + crop_w, int(sh * 0.02) + crop_h))
    pw = int(TW * 0.50)
    person = person.resize((pw, TH), Image.LANCZOS)

    # Bright ground: a blurred, lifted copy of the same frame.
    bg = src.crop((ax, 0, ax + aw, sh)).resize((TW, TH), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(18))
    # lifted well toward white: the black headline line has to read on it,
    # the way it does on their bright gym backgrounds
    bg = Image.blend(bg, Image.new("RGB", (TW, TH), (240, 240, 238)), 0.66)

    img = bg.copy()
    img.paste(person, (TW - pw, 0))

    # soften the seam down the left edge of the subject
    seam = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seam)
    for i in range(90):
        a = int(190 * (1 - i / 90))
        sd.line([(TW - pw + i, 0), (TW - pw + i, TH)], fill=(232, 232, 230, a))
    img = Image.alpha_composite(img.convert("RGBA"), seam).convert("RGB")

    d = ImageDraw.Draw(img)

    # Headline: alternating white / black caps, stacked left.
    lines = [("WORKOUT", (255, 255, 255)),
             ("& DIET PLAN", (17, 17, 17))]
    y = 74
    for text, fill in lines:
        f = anton(104)
        d.text((46, y), text, font=f, fill=fill,
               stroke_width=3, stroke_fill=(0, 0, 0, 90) if fill[0] > 128 else None)
        y += 108

    # Red name label
    lab = "JENNIFER ANISTON"
    lf = black(46)
    lw = d.textlength(lab, font=lf)
    ly = y + 16
    d.rectangle([44, ly, 44 + lw + 52, ly + 76], fill=RED)
    d.text((44 + 26, ly + 14), lab, font=lf, fill=(255, 255, 255))

    # Food inset, bottom-left, as on the newer thumbnails
    if FOOD.exists():
        fi = Image.open(FOOD).convert("RGB")
        fw, fh = 300, 190
        fi = fi.resize((fw, int(fi.height * fw / fi.width)), Image.LANCZOS)
        fi = fi.crop((0, max(0, (fi.height - fh) // 2), fw,
                      max(0, (fi.height - fh) // 2) + fh))
        fx, fy = 46, TH - fh - 40
        d.rectangle([fx - 5, fy - 5, fx + fw + 5, fy + fh + 5], fill=(255, 255, 255))
        img.paste(fi, (fx, fy))

    out = ROOT / "THUMBNAIL_V4.png"
    img.save(out)
    print(f"  {out.name}  {img.size}  from {SRC_ID}@{SRC_T}s")


if __name__ == "__main__":
    main()
