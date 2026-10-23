"""Thumbnail, 1280x720. This one has her face on it.

The previous build's thumbnail carried no likeness at all, because no footage
had been sourced. It would not have been clicked. This uses a single frame
from Harper's Bazaar UK's Emmys carpet coverage - a source used nowhere else
in the film, so it is still one use of one source.

Three elements only, per the format: one dominant person, one short headline,
one red label.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from graphics import RED, anton, black, reg

ROOT = Path(__file__).resolve().parent
TW, TH = 1280, 720
SRC_ID, SRC_T = "EXQbHPcoack", 60.0


def grab() -> Image.Image:
    out = ROOT / "work" / "thumb_src.png"
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(SRC_T), "-i",
                    str(ROOT / "raw" / f"{SRC_ID}.mp4"), "-frames:v", "1",
                    str(out), "-y"], check=True)
    return Image.open(out).convert("RGB")


def main() -> None:
    src = grab()
    # Upscale hard: the source is 360p and the thumbnail is served at 1280.
    src = src.resize((TW * 3, int(src.height * TW * 3 / src.width)), Image.LANCZOS)
    src = src.filter(ImageFilter.UnsharpMask(radius=4, percent=110, threshold=3))

    # Frame chest-up with the eyes in the upper third. The first pass cropped
    # around a centre point and lost the top of her head - framing from
    # explicit TOP/BOTTOM fractions is the fix, because what has to land in
    # frame is the head and the waist, not the middle.
    sw, sh = src.size
    TOP, BOTTOM, FACE_X = 0.03, 0.72, 0.53
    crop_h = int((BOTTOM - TOP) * sh)
    crop_w = int(crop_h * TW / TH)
    x0 = min(max(int(FACE_X * sw) - crop_w // 2, 0), max(sw - crop_w, 0))
    y0 = int(TOP * sh)
    person = src.crop((x0, y0, x0 + crop_w, y0 + crop_h)).resize((TW, TH), Image.LANCZOS)

    img = Image.new("RGB", (TW, TH), (12, 12, 12))
    img.paste(person, (0, 0))

    # Scrim so type reads over the carpet backdrop.
    scrim = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for x in range(TW):
        a = int(232 * max(0.0, 1.0 - (x / (TW * 0.60)) ** 1.35))
        sd.line([(x, 0), (x, TH)], fill=(8, 8, 10, a))
    img = Image.alpha_composite(img.convert("RGBA"), scrim).convert("RGB")

    d = ImageDraw.Draw(img)
    y = 96
    for ln in ("SHE STOPPED", "TRAINING", "LIKE THIS"):
        d.text((56, y), ln, font=anton(96), fill=(255, 255, 255))
        y += 104

    lab = "AT 57"
    fl = black(46)
    lw = d.textlength(lab, font=fl)
    d.rectangle([56, y + 24, 56 + lw + 52, y + 24 + 78], fill=RED)
    d.text((56 + 26, y + 24 + 15), lab, font=fl, fill=(255, 255, 255))

    d.text((56, TH - 58), "WORKOUT & DIET  ·  CELEB WORKOUT",
           font=black(24), fill=(190, 190, 190))

    out = ROOT / "THUMBNAIL.png"
    img.save(out)
    print(f"  {out.name}  {img.size}  source {SRC_ID} @ {SRC_T:.0f}s")


if __name__ == "__main__":
    main()
