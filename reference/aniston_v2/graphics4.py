"""Graphics v4 — traced off the reference frames, not off the brand document.

Three treatments, all measured from `REFERENCE_CelebWorkout_Aniston_309k.mp4`:

1. EXERCISE WEDGE  — red diagonal filling the bottom-right corner, a thin white
   line along the diagonal, two lines of white text inside it:
       CARDIO / 30 MINUTES        TEMPLE POSE / 8 REPS, 8 BREATHS
2. FOOD LIST       — heavy black category on a white box, top-left; items below
   in big white caps with a dark edge, one per line, over food footage.
3. DAY MARKER      — white box, red border, day in black caps.

The red is `#E8121A`, sampled off their wedge. That is NOT the `#B22B1A` in
docs/BRAND.md — where the document and the channel disagree, the channel wins,
because the channel is what is being emulated.

Everything V3 had that the channel does not do — full-frame black chapter
cards, giant minimalist stat cards, generated empty-room stills — is gone.
"""
from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

W, H, FPS = 1920, 1080, 30

RED   = (232, 18, 26)       # #E8121A, sampled off the reference wedge
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)

FONTS = Path("C:/Users/avina/ytceleb/graphics/public/fonts")


@lru_cache(maxsize=None)
def f(name: str, size: int):
    from PIL import ImageFont
    return ImageFont.truetype(str(FONTS / name), size)


def anton(s):  return f("Anton-Regular.ttf", s)
def black(s):  return f("ArchivoBlack-Regular.ttf", s)
def med(s):    return f("Archivo-Medium.ttf", s)
def reg(s):    return f("Archivo-Regular.ttf", s)


def _outline(d, xy, text, font, fill=WHITE, ring=(0, 0, 0, 190), w=3):
    x, y = xy
    for dx in range(-w, w + 1):
        for dy in range(-w, w + 1):
            if dx * dx + dy * dy <= w * w:
                d.text((x + dx, y + dy), text, font=font, fill=ring)
    d.text((x, y), text, font=font, fill=fill)


# ─────────────────────────────────────────────────── 1. exercise wedge

def exercise_png(name: str, reps: str, out: Path) -> Path:
    """Red diagonal wedge, bottom-right. Traced off the reference: the diagonal
    runs from roughly 45% across the bottom edge up to 33% down the right
    edge, with a thin white rule along it."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p1 = (W * 0.44, H)
    p2 = (W, H * 0.31)
    d.polygon([p1, p2, (W, H)], fill=(*RED, 255))
    d.line([p1, p2], fill=(255, 255, 255, 255), width=5)
    # Auto-fit: "BANDED GLUTE BRIDGE" overflowed the frame at a fixed 46px.
    # The wedge is a triangle, so the usable width is whatever fits inside it
    # at the text's own baseline, less a margin.
    x, y = W * 0.70, H * 0.755
    avail = W - x - 46
    nf = next((med(s) for s in range(46, 21, -2)
               if d.textlength(name.upper(), font=med(s)) <= avail), med(22))
    rf = next((reg(s) for s in range(42, 19, -2)
               if d.textlength(reps.upper(), font=reg(s)) <= avail), reg(20))
    d.text((x, y), name.upper(), font=nf, fill=WHITE)
    d.text((x, y + 58), reps.upper(), font=rf, fill=WHITE)
    img.save(out)
    return out


# ─────────────────────────────────────────────────── 2. food list

def food_png(category: str, items: list[str], out: Path, reveal: int | None = None) -> Path:
    """Category on a white box top-left, items in big white caps below.
    `reveal` limits how many items are drawn, so the list can build in time
    with the narrator reading them."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Left scrim. Food footage is often bright (a white plate, a pale board)
    # and plain white type with a thin edge disappeared on it. The reference's
    # food shots are darker; this guarantees the same contrast on any plate.
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for px in range(int(W * 0.52)):
        a = int(165 * max(0.0, 1.0 - (px / (W * 0.52)) ** 1.5))
        sd.line([(px, 0), (px, H)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, scrim)
    d = ImageDraw.Draw(img)
    cf = black(64)
    x, y = W * 0.045, H * 0.05
    tw = d.textlength(category.upper(), font=cf)
    d.rectangle([x - 22, y - 14, x + tw + 30, y + 84], fill=(255, 255, 255, 245))
    d.text((x, y), category.upper(), font=cf, fill=BLACK)
    itf = reg(66)
    iy = y + 128
    shown = items if reveal is None else items[:max(1, reveal)]
    for it in shown:
        _outline(d, (x, iy), it.upper(), itf)
        iy += 82
    img.save(out)
    return out


# ─────────────────────────────────────────────────── 3. day marker

def day_png(day: str, session: str, out: Path) -> Path:
    """White box with a red border, day in black caps, session line under it."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    df = black(78)
    tw = d.textlength(day.upper(), font=df)
    x, y = W * 0.06, H * 0.075
    d.rectangle([x - 26, y - 20, x + tw + 34, y + 108], fill=(255, 255, 255, 250))
    d.rectangle([x - 26, y - 20, x + tw + 34, y + 108], outline=RED, width=8)
    d.text((x, y), day.upper(), font=df, fill=BLACK)
    if session:
        # The session line was outlined white text. Against d_tuesday (a gym
        # full of windows) and d_thursday (a pale green wall) it was unreadable
        # in the cut, so it sits on its own bar now - the day box already does
        # the same thing one line above it.
        sf = med(40)
        st = session.upper()
        sx, sy = x - 20, y + 132
        sw = d.textlength(st, font=sf)
        d.rectangle([sx - 12, sy - 8, sx + sw + 14, sy + 54],
                    fill=(0, 0, 0, 205))
        d.text((sx, sy), st, font=sf, fill=WHITE)
    img.save(out)
    return out


# ─────────────────────────────────────────────────── 4. source credit

def credit_png(text: str, out: Path) -> Path:
    """Small, unobtrusive, bottom-left. The reference does not credit sources
    at all; this is kept minimal so it does not read as a compliance stamp
    across every shot the way V3's did."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fnt = med(26)
    _outline(d, (W * 0.035, H - 62), text.upper(), fnt, fill=(235, 235, 235, 220), w=2)
    img.save(out)
    return out


# ─────────────────────────────────────────────────── 5. title / outro

def title_png(lines: list[str], out: Path) -> Path:
    """Burned over the opening footage, not on a black card."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = H * 0.33
    for ln in lines:
        _outline(d, (W * 0.06, y), ln.upper(), anton(120), w=4)
        y += 118
    d.rectangle([W * 0.06, y + 22, W * 0.06 + 210, y + 34], fill=RED)
    img.save(out)
    return out


def endcard() -> Image.Image:
    img = Image.new("RGB", (W, H), (13, 13, 13))
    d = ImageDraw.Draw(img)
    top, bot, ft = "CELEB", "WORKOUT", anton(150)
    tw, bw = d.textlength(top, font=ft), d.textlength(bot, font=ft)
    x, ty = (W - max(tw, bw)) / 2, H * 0.30
    d.text((x, ty), top, font=ft, fill=WHITE)
    by = d.textbbox((x, ty), top, font=ft)[3] + 26
    bh = d.textbbox((x, 0), bot, font=ft)[3] + 20
    d.rectangle([x - 24, by, x + bw + 24, by + bh], fill=RED)
    d.text((x, by + 10), bot, font=ft, fill=WHITE)
    tag = "TRAIN LIKE THE ICONS"
    gw = d.textlength(tag, font=black(38))
    d.text(((W - gw) / 2, by + bh + 44), tag, font=black(38), fill=(169, 169, 169))
    return img


def render_still_image(img: Image.Image, frames: int, out: Path):
    tmp = out.with_suffix(".png")
    img.save(tmp)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(tmp),
                    "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS}",
                    "-frames:v", str(frames), "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "work4" / "gfx"
    out.mkdir(parents=True, exist_ok=True)
    exercise_png("Banded Glute Bridge", "3 sets of 15", out / "wedge.png")
    food_png("VEGETABLES", ["SPINACH", "KALE", "BROCCOLI", "CELERY",
                            "TOMATOES", "MUSHROOMS", "SWEET POTATOES"],
             out / "food.png")
    day_png("MONDAY", "Low-impact resistance - lower body", out / "day.png")
    title_png(["She stopped", "training", "like this"], out / "title.png")
    endcard().save(out / "end.png")
    print(f"wrote {out}")


# ─────────────────────────────────────── 6. split-screen comparison

def split_piece(left: Path, right: Path, l_label: str, r_label: str,
                frames: int, out: Path, fps: int = FPS):
    """Two images side by side with a red divider and a label under each.

    The reference leans on this constantly in the biography - childhood photo
    against adult face, her against her mother, her against her father - and it
    is the single most obvious thing V4's life section was missing. Cutting
    fast between twenty-four seated interviews is not variety; this is."""
    half = W // 2
    img = Image.new("RGB", (W, H), (13, 13, 13))
    for i, p in enumerate((left, right)):
        im = Image.open(p).convert("RGB")
        sc = max(half / im.width, H / im.height)
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
        x = (im.width - half) // 2
        y = (im.height - H) // 2
        img.paste(im.crop((x, y, x + half, y + H)), (i * half, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([half - 5, 0, half + 5, H], fill=RED)
    for i, lab in enumerate((l_label, r_label)):
        if not lab:
            continue
        f = black(44)
        tw = d.textlength(lab.upper(), font=f)
        x = i * half + (half - tw) / 2
        y = H - 132
        d.rectangle([x - 26, y - 16, x + tw + 26, y + 68], fill=RED)
        d.text((x, y), lab.upper(), font=f, fill=WHITE)
    tmp = out.with_suffix(".png")
    img.save(tmp)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(tmp),
                    "-vf", f"scale={W}:{H},fps={fps}", "-frames:v", str(frames),
                    "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "19", "-pix_fmt", "yuv420p", str(out)], check=True)
    tmp.unlink(missing_ok=True)
    return out


# ─────────────────────────────────────── 7. place label

def place_png(name: str, sub: str, out: Path) -> Path:
    """Locates a beat the way the reference's animated map does - it names
    where we are. Same white box / red border vocabulary as the day marker."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = black(66)
    tw = d.textlength(name.upper(), font=f)
    x, y = W * 0.06, H * 0.735
    d.rectangle([x - 24, y - 18, x + tw + 32, y + 94], fill=(255, 255, 255, 250))
    d.rectangle([x - 24, y - 18, x + tw + 32, y + 94], outline=RED, width=8)
    d.text((x, y), name.upper(), font=f, fill=BLACK)
    if sub:
        _outline(d, (x - 18, y + 118), sub.upper(), med(38))
    img.save(out)
    return out


# ─────────────────────────────────────── 8. quote bar

def quote_png(*_a, **_k):
    """REMOVED. This was the PIL quote bar, and it carried two truncations:

        keep  = max(1, int(round(len(words) * reveal)))   # a prefix of the text
        lines = lines[-3:]                                # then drop lines too

    so it could print half a sentence and then silently throw away the top of
    what was left. It also drew a #122A5C blue bar, which is not the channel's
    colour and never matched the day cards immediately next to it in the cut.

    Quote cards are gl/card.mjs via cards.py now: one PNG per quote, the whole
    quote, the same #E8121A accent and Anton/Archivo pairing as everything else
    in this file. Nothing calls this; it stays only so that anything reaching
    for the old renderer fails loudly instead of drawing half a sentence.
    """
    raise RuntimeError("graphics4.quote_png is gone - use cards.quote_card")
