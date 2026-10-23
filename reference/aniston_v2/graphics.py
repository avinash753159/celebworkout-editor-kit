"""Graphics. Plainer than the last build, on purpose.

The previous version's look came out of a brand document for this project
rather than out of anything the channel actually puts on screen - warm-white
editorial grounds, big Anton statement cards, a red circular field. It read as
a design system rather than as a fitness video. This is deliberately closer to
what the format is: high contrast, bold sans, one red accent, information
first.

The one thing that IS non-negotiable here is the credit. Every archive clip
carries its rights holder, burned in, bottom left, for as long as the clip is
on screen.
"""
from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1920, 1080, 30

RED = (200, 40, 30)
INK = (16, 16, 16)
PAPER = (250, 249, 247)
WHITE = (255, 255, 255)
DIM = (150, 150, 150)

FONTS = Path("C:/Users/avina/ytceleb/graphics/public/fonts")


@lru_cache(maxsize=None)
def f(name: str, size: int):
    from PIL import ImageFont
    return ImageFont.truetype(str(FONTS / name), size)


def anton(s):    return f("Anton-Regular.ttf", s)
def black(s):    return f("ArchivoBlack-Regular.ttf", s)
def med(s):      return f("Archivo-Medium.ttf", s)
def reg(s):      return f("Archivo-Regular.ttf", s)


def wrap(d, s, fnt, maxw):
    words, out, cur = s.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if d.textlength(t, font=fnt) <= maxw or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    if cur:
        out.append(cur)
    return out


# ───────────────────────────────────────────────────────────── overlays

def credit_png(text: str, out: Path) -> Path:
    """Bottom-left source credit, drawn once and overlaid by ffmpeg."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fnt = black(26)
    tw = d.textlength(text.upper(), font=fnt)
    x, y = 64, H - 104
    d.rectangle([x, y, x + 6, y + 42], fill=RED)
    d.rectangle([x + 6, y, x + tw + 44, y + 42], fill=(0, 0, 0, 165))
    d.text((x + 24, y + 8), text.upper(), font=fnt, fill=(255, 255, 255, 235))
    img.save(out)
    return out


def plate_png(index: int, name: str, setsreps: str, cue: str, out: Path) -> Path:
    """Movement name plate, sat over real demonstration footage."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Raised clear of the bottom strip: several archive sources carry their
    # own burned-in lower third down there, and the first pass collided with
    # a GMA banner mid-sentence.
    x, y = 78, H - 430
    d.rectangle([x, y, x + 980, y + 226], fill=(0, 0, 0, 190))
    d.rectangle([x, y, x + 10, y + 226], fill=RED)
    d.text((x + 34, y + 22), f"{index:02d}", font=anton(78), fill=RED)
    d.text((x + 128, y + 34), name.upper(), font=black(46), fill=WHITE)
    d.text((x + 128, y + 96), setsreps, font=anton(48), fill=WHITE)
    yy = y + 156
    for ln in wrap(d, cue, reg(28), 800):
        d.text((x + 34, yy), ln, font=reg(28), fill=(210, 210, 210, 255))
        yy += 36
    img.save(out)
    return out


# ───────────────────────────────────────────────────────────── full cards

def _card(dark=True):
    img = Image.new("RGB", (W, H), INK if dark else PAPER)
    return img, ImageDraw.Draw(img)


def chapter(n: str, title: str) -> Image.Image:
    img, d = _card(True)
    d.rectangle([0, H * .40, W, H * .40 + 8], fill=RED)
    fn = anton(300)
    d.text((W * .10, H * .16), n, font=fn, fill=(38, 38, 38))
    ft = anton(126)
    d.text((W * .10, H * .45), title.upper(), font=ft, fill=WHITE)
    return img


def title_card(main: list[str], sub: str) -> Image.Image:
    img, d = _card(True)
    y = H * .22
    for ln in main:
        d.text((W * .08, y), ln.upper(), font=anton(132), fill=WHITE)
        y += 142
    d.rectangle([W * .08, y + 26, W * .08 + 180, y + 36], fill=RED)
    yy = y + 76
    for ln in wrap(d, sub, reg(40), int(W * .74)):
        d.text((W * .08, yy), ln, font=reg(40), fill=DIM)
        yy += 54
    return img


def stat(number: str, label: str, note: str = "") -> Image.Image:
    img, d = _card(True)
    d.text((W * .08, H * .16), number, font=anton(400), fill=RED)
    d.text((W * .08, H * .64), label.upper(), font=black(56), fill=WHITE)
    if note:
        yy = H * .755
        for ln in wrap(d, note, reg(34), int(W * .8)):
            d.text((W * .08, yy), ln, font=reg(34), fill=DIM)
            yy += 46
    return img


def quote(text: str, credit: str) -> Image.Image:
    img, d = _card(True)
    fnt = med(52)
    lines = wrap(d, f"\u201c{text}\u201d", fnt, int(W * .78))
    y = (H - len(lines) * 72) / 2 - 30
    d.rectangle([W * .08, y, W * .08 + 8, y + len(lines) * 72 - 14], fill=RED)
    for ln in lines:
        d.text((W * .115, y), ln, font=fnt, fill=WHITE)
        y += 72
    d.text((W * .115, y + 30), credit.upper(), font=black(28), fill=RED)
    return img


def week(rows) -> Image.Image:
    img, d = _card(True)
    d.text((W * .07, H * .07), "THE WEEK", font=anton(88), fill=WHITE)
    d.rectangle([W * .07, H * .20, W * .07 + 160, H * .20 + 8], fill=RED)
    y = H * .265
    for day, sess, dur in rows:
        d.text((W * .07, y), day.upper(), font=black(40), fill=RED)
        d.text((W * .20, y + 2), sess, font=reg(38), fill=WHITE)
        tw = d.textlength(dur, font=anton(42))
        d.text((W * .93 - tw, y - 2), dur, font=anton(42), fill=DIM)
        y += 68
        d.line([(W * .07, y - 14), (W * .93, y - 14)], fill=(54, 54, 54), width=2)
    d.text((W * .07, H * .915),
           "Assembled from methods she has publicly described. Not her private programme.",
           font=reg(26), fill=(120, 120, 120))
    return img


def mechanism() -> Image.Image:
    """Where the load goes. A claim about forces, so it is drawn, not filmed."""
    img, d = _card(True)
    d.text((W * .07, H * .07), "WHERE THE LOAD GOES", font=anton(76), fill=WHITE)
    d.rectangle([W * .07, H * .185, W * .07 + 160, H * .185 + 8], fill=RED)

    cx = W * .27
    d.text((cx - 170, H * .27), "IMPACT", font=black(40), fill=DIM)
    d.text((cx - 170, H * .325), "force straight through the joint", font=reg(28), fill=(110, 110, 110))
    top, bot = H * .43, H * .78
    d.line([(cx, top), (cx, bot)], fill=DIM, width=14)
    for i in range(5):
        yy = top + (bot - top) * (i + 1) / 6
        d.polygon([(cx - 26, yy - 20), (cx + 26, yy - 20), (cx, yy + 18)], fill=(95, 95, 95))
    d.ellipse([cx - 48, bot - 22, cx + 48, bot + 26], outline=DIM, width=9)
    d.line([(cx - 220, bot + 44), (cx + 220, bot + 44)], fill=(70, 70, 70), width=6)

    cx = W * .71
    d.text((cx - 170, H * .27), "RANGE", font=black(40), fill=RED)
    d.text((cx - 170, H * .325), "tension across the whole travel", font=reg(28), fill=(150, 105, 100))
    d.arc([cx - 240, H * .40, cx + 240, H * .88], start=200, end=340, fill=RED, width=16)
    for i in range(7):
        t = i / 6
        ax = cx - 240 + 480 * t
        ay = H * .64 - 158 * (1 - (2 * t - 1) ** 2)
        d.ellipse([ax - 12, ay - 12, ax + 12, ay + 12], fill=RED)
    d.line([(cx - 240, H * .88), (cx + 240, H * .88)], fill=(70, 70, 70), width=6)
    d.line([(W * .49, H * .25), (W * .49, H * .86)], fill=(48, 48, 48), width=3)
    return img


def endcard() -> Image.Image:
    img, d = _card(True)
    t = "CELEB WORKOUT"
    fnt = anton(150)
    tw = d.textlength(t, font=fnt)
    d.text(((W - tw) / 2, H * .38), t, font=fnt, fill=WHITE)
    s = "TRAIN LIKE THE ICONS"
    fs = black(40)
    sw = d.textlength(s, font=fs)
    d.rectangle([(W - sw) / 2 - 26, H * .565, (W + sw) / 2 + 26, H * .565 + 68], fill=RED)
    d.text(((W - sw) / 2, H * .565 + 14), s, font=fs, fill=WHITE)
    return img


def subscribe() -> Image.Image:
    img, d = _card(True)
    t = "SUBSCRIBE"
    fnt = anton(190)
    tw = d.textlength(t, font=fnt)
    d.rectangle([(W - tw) / 2 - 50, H * .38, (W + tw) / 2 + 50, H * .38 + 230], fill=RED)
    d.text(((W - tw) / 2, H * .385), t, font=fnt, fill=WHITE)
    s = "it genuinely helps"
    fs = reg(38)
    sw = d.textlength(s, font=fs)
    d.text(((W - sw) / 2, H * .66), s, font=fs, fill=DIM)
    return img


# ───────────────────────────────────────────────────────────── render

def render_still_image(img: Image.Image, frames: int, out: Path,
                       drift: bool = True) -> Path:
    tmp = out.parent / f"_g_{out.stem}"
    tmp.mkdir(parents=True, exist_ok=True)
    for p in tmp.glob("*.png"):
        p.unlink()
    for i in range(frames):
        if not drift:
            img.save(tmp / f"{i:05d}.png")
            continue
        t = i / max(frames - 1, 1)
        z = 1.0 + 0.02 * t
        nw, nh = int(W * z), int(H * z)
        big = img.resize((nw, nh), Image.LANCZOS)
        x, y = (nw - W) // 2, (nh - H) // 2
        big.crop((x, y, x + W, y + H)).save(tmp / f"{i:05d}.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", str(tmp / "%05d.png"), "-c:v", "libx264", "-preset", "medium",
                    "-crf", "18", "-pix_fmt", "yuv420p", str(out)], check=True)
    for p in tmp.glob("*.png"):
        p.unlink()
    tmp.rmdir()
    return out
