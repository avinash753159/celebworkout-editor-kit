"""Thumbnail, 1280x720. Structure A: profile.

v2's thumbnail was cut from a Harper's Bazaar best-dressed roundup - a source
its own clip list described as one "she is barely in it" - and imported the
wrong red. This uses a frame from the Pvolve campaign: her mid-effort, which
is what the video is actually about, at 1080p rather than an upscaled 360p.

Brand structure A is three elements: one dominant person, one short headline,
one red label with the name. Headline 3-6 words, max two text sizes.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from graphics2 import RED, anton, black

ROOT = Path(__file__).resolve().parent
TW, TH = 1280, 720
SRC_ID, SRC_T = "lrZKJPVn89s", 14.4


def grab() -> Image.Image:
    out = ROOT / "work2" / "thumb_src.png"
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(SRC_T), "-i",
                    str(ROOT / "hd" / f"{SRC_ID}.mp4"), "-frames:v", "1",
                    str(out), "-y"], check=True)
    return Image.open(out).convert("RGB")


def main() -> None:
    src = grab()
    src = src.filter(ImageFilter.UnsharpMask(radius=3, percent=85, threshold=3))

    # This shot is pillarboxed inside its 1920 frame, so frame inside the
    # ACTIVE picture (cropdetect: 1488x1080+216) or the thumbnail inherits a
    # black band down one side.
    ACT_X, ACT_W, ACT_Y, ACT_H = 216, 1488, 0, 1080
    TOP, BOTTOM, FACE_X = 0.02, 0.98, 0.52
    crop_h = int((BOTTOM - TOP) * ACT_H)
    crop_w = int(crop_h * TW / TH)
    if crop_w > ACT_W:                      # too wide for the active area
        crop_w = ACT_W
        crop_h = int(crop_w * TH / TW)
    x0 = ACT_X + min(max(int(FACE_X * ACT_W) - crop_w // 2, 0), ACT_W - crop_w)
    y0 = ACT_Y + int(TOP * ACT_H)
    person = src.crop((x0, y0, x0 + crop_w, y0 + crop_h)).resize((TW, TH), Image.LANCZOS)

    img = Image.new("RGB", (TW, TH), (13, 13, 13))
    img.paste(person, (0, 0))

    # Left-side scrim so type reads. Soft black only - never a second colour.
    scrim = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for x in range(TW):
        a = int(238 * max(0.0, 1.0 - (x / (TW * 0.58)) ** 1.4))
        sd.line([(x, 0), (x, TH)], fill=(8, 8, 10, a))
    img = Image.alpha_composite(img.convert("RGBA"), scrim).convert("RGB")

    d = ImageDraw.Draw(img)
    y = 92
    for ln in ("SHE STOPPED", "TRAINING", "LIKE THIS"):
        d.text((54, y), ln, font=anton(102), fill=(244, 242, 239))
        y += 108

    lab = "JENNIFER ANISTON"
    fl = black(40)
    lw = d.textlength(lab, font=fl)
    d.rectangle([54, y + 26, 54 + lw + 46, y + 26 + 68], fill=RED)
    d.text((54 + 23, y + 26 + 14), lab, font=fl, fill=(244, 242, 239))

    out = ROOT / "THUMBNAIL_V3.png"
    img.save(out)
    print(f"  {out.name}  {img.size}  source {SRC_ID} @ {SRC_T:.1f}s")


if __name__ == "__main__":
    main()
