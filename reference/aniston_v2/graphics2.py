"""Graphics v3 — the channel's brand, not a per-video design.

v2's header said the brand document "read as a design system rather than as a
fitness video" and deviated from it. The owner's note on the previous film was
the opposite complaint: *"It didn't seem like one brand theme. It was just cut
and paste."* Identity is cumulative, so this file follows `docs/BRAND.md`
exactly and does not reinterpret it.

What changed, concretely:

- **Celebrity Red is #B22B1A.** v2 used (200,40,30) = #C8281E, a third wrong
  value alongside the #E3120B the brand doc already calls out.
- **No teal.** v2's biggest quote card was a turquoise panel; the palette
  admits black, warm white, grey and red, and nothing else.
- **Four fixed chapters**, Anton over black with a red bar.
- **Type has a floor.** Nothing below 34px at 1920x1080. v2 set a footnote at
  26px and a ten-line quote at 30px, neither of which is readable on a phone.
- **The abstract load diagram is gone.** A shot that needs explaining has
  failed; the narration explains the mechanism while she is on screen doing
  banded work, which shows it.
"""
from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

W, H, FPS = 1920, 1080, 30

RED    = (178, 43, 26)      # #B22B1A  Celebrity Red
BLACK  = (13, 13, 13)       # #0D0D0D  Training Black
PAPER  = (244, 242, 239)    # #F4F2EF  Warm White
STEEL  = (169, 169, 169)    # #A9A9A9  Steel Gray
SHADOW = (37, 37, 37)       # #252525  Deep Shadow

MIN_PT = 34                 # legibility floor at 1080p

FONTS = Path("C:/Users/avina/ytceleb/graphics/public/fonts")


@lru_cache(maxsize=None)
def f(name: str, size: int):
    from PIL import ImageFont
    assert size >= MIN_PT or name == "Anton-Regular.ttf", \
        f"{size}px is below the {MIN_PT}px legibility floor"
    return ImageFont.truetype(str(FONTS / name), size)


def anton(s):  return f("Anton-Regular.ttf", s)
def black(s):  return f("ArchivoBlack-Regular.ttf", s)
def med(s):    return f("Archivo-Medium.ttf", s)
def reg(s):    return f("Archivo-Regular.ttf", s)
def allura(s): return f("Allura-Regular.ttf", s)


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


def ground() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BLACK)
    return img, ImageDraw.Draw(img)


# ─────────────────────────────────────────────────────────── overlays

def credit_png(text: str, out: Path) -> Path:
    """Lower third, per brand: black translucent block, red vertical bar,
    holder in Archivo Black. One credit only - the crop has already pushed
    the broadcaster's own bug off frame, so these no longer stack."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fnt = black(34)
    tw = d.textlength(text.upper(), font=fnt)
    x, y, h = 72, H - 112, 52
    d.rectangle([x, y, x + tw + 62, y + h], fill=(13, 13, 13, 190))
    d.rectangle([x, y, x + 8, y + h], fill=(*RED, 255))
    d.text((x + 30, y + 9), text.upper(), font=fnt, fill=(244, 242, 239, 240))
    img.save(out)
    return out


def move_png(index: int, name: str, cue: str, out: Path) -> Path:
    """Exercise card over footage. Brand: name in Archivo Black, number in
    Anton, cue in Archivo Regular, a red block as the only accent."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x, y = 110, H - 300
    nf, mf, cf = anton(120), black(52), reg(36)
    body_w = max(d.textlength(name.upper(), font=mf),
                 d.textlength(cue, font=cf)) + 150
    d.rectangle([x - 34, y - 26, x + body_w, y + 190], fill=(13, 13, 13, 175))
    d.rectangle([x - 34, y - 26, x - 22, y + 190], fill=(*RED, 255))
    d.text((x, y - 18), f"{index:02d}", font=nf, fill=(*RED, 255))
    d.text((x + 148, y + 6), name.upper(), font=mf, fill=(244, 242, 239, 255))
    d.text((x + 148, y + 76), cue, font=cf, fill=(200, 198, 195, 255))
    img.save(out)
    return out


# ─────────────────────────────────────────────────────────── full cards

def chapter(number: str, title: str) -> Image.Image:
    """Anton over black with a red bar. One of the four fixed chapters."""
    assert title in ("THE ROLE", "THE WORKOUT", "THE DIET", "THE RESULTS"), title
    img, d = ground()
    d.text((W * .09, H * .17), number, font=anton(300), fill=SHADOW)
    d.rectangle([W * .09, H * .565, W * .09 + 190, H * .565 + 10], fill=RED)
    d.text((W * .09, H * .60), title, font=anton(132), fill=PAPER)
    return img


def title_card(lines: list[str], sub: str) -> Image.Image:
    img, d = ground()
    y = H * .26
    for ln in lines:
        d.text((W * .09, y), ln.upper(), font=anton(140), fill=PAPER)
        y += 126
    d.rectangle([W * .09, y + 34, W * .09 + 190, y + 44], fill=RED)
    d.text((W * .09, y + 78), sub, font=reg(38), fill=STEEL)
    return img


def stat(number: str, label: str, foot: str = "") -> Image.Image:
    img, d = ground()
    d.text((W * .09, H * .17), number, font=anton(380), fill=RED)
    d.text((W * .09, H * .64), label.upper(), font=black(56), fill=PAPER)
    if foot:
        d.text((W * .09, H * .74), foot, font=reg(36), fill=STEEL)
    return img


def quote(text: str, credit: str) -> Image.Image:
    """Max ~34 words. v2 ran a ten-line quote at 30px inside a teal panel."""
    assert len(text.split()) <= 34, f"quote too long to read: {len(text.split())} words"
    img, d = ground()
    fnt = reg(52)
    lines = wrap(d, f'\u201c{text}\u201d', fnt, W * .78)
    y = (H - len(lines) * 76) / 2 - 30
    d.rectangle([W * .09, y + 8, W * .09 + 9, y + len(lines) * 76 - 16], fill=RED)
    for ln in lines:
        d.text((W * .09 + 42, y), ln, font=fnt, fill=PAPER)
        y += 76
    d.text((W * .09 + 42, y + 26), credit.upper(), font=black(34), fill=RED)
    return img


def week(rows) -> Image.Image:
    """The schedule. Type sized so it survives a phone screen."""
    img, d = ground()
    d.text((W * .07, H * .07), "THE WEEK", font=anton(96), fill=PAPER)
    d.rectangle([W * .07, H * .205, W * .07 + 175, H * .205 + 10], fill=RED)
    y = H * .30
    for day, sess, dur in rows:
        d.text((W * .07, y), day.upper(), font=black(40), fill=RED)
        d.text((W * .175, y + 1), sess, font=reg(40), fill=PAPER)
        tw = d.textlength(dur, font=med(38))
        d.text((W * .93 - tw, y + 2), dur, font=med(38), fill=STEEL)
        y += 82
        if day.lower() != "sun":
            d.line([(W * .07, y - 18), (W * .93, y - 18)], fill=SHADOW, width=2)
    d.text((W * .07, H * .915),
           "Assembled from methods she has publicly described. Not her private programme.",
           font=reg(34), fill=(120, 120, 120))
    return img


def subscribe() -> Image.Image:
    img, d = ground()
    label = "SUBSCRIBE"
    fnt = anton(140)
    tw = d.textlength(label, font=fnt)
    x = (W - tw) / 2
    d.rectangle([x - 54, H * .40, x + tw + 54, H * .40 + 190], fill=RED)
    d.text((x, H * .40 + 18), label, font=fnt, fill=PAPER)
    sub = "It genuinely helps"
    sw = d.textlength(sub, font=reg(40))
    d.text(((W - sw) / 2, H * .625), sub, font=reg(40), fill=STEEL)
    return img


def endcard() -> Image.Image:
    """Primary wordmark: CELEB white, WORKOUT reversed out of a red block."""
    img, d = ground()
    top, bot = "CELEB", "WORKOUT"
    ft = anton(150)
    tw, bw = d.textlength(top, font=ft), d.textlength(bot, font=ft)
    x = (W - max(tw, bw)) / 2
    ty = H * .30
    d.text((x, ty), top, font=ft, fill=PAPER)
    # stack off the measured glyph box, not a guessed fraction, so the red
    # block can never clip the wordmark above it
    by = d.textbbox((x, ty), top, font=ft)[3] + 26
    pad = 20
    bh = d.textbbox((x, 0), bot, font=ft)[3] + pad
    d.rectangle([x - 24, by, x + bw + 24, by + bh], fill=RED)
    d.text((x, by + pad / 2), bot, font=ft, fill=PAPER)
    tag = "TRAIN LIKE THE ICONS"
    gw = d.textlength(tag, font=black(38))
    d.text(((W - gw) / 2, by + bh + 44), tag, font=black(38), fill=STEEL)
    return img


# ─────────────────────────────────────────────────────── image -> piece

def render_still_image(img: Image.Image, frames: int, out: Path, drift=True):
    """Card to video. A slow drift keeps a static card from reading as a
    freeze; tables and anything the viewer must read stay still."""
    tmp = out.with_suffix(".png")
    img.save(tmp)
    if drift:
        vf = (f"scale=2688:1512:flags=lanczos,zoompan="
              f"z='min(1.002+0.00022*on,1.06)':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    else:
        vf = f"scale={W}:{H}:flags=lanczos,fps={FPS}"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(tmp),
                    "-vf", vf, "-frames:v", str(frames), "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "work" / "brandcheck"
    out.mkdir(parents=True, exist_ok=True)
    chapter("02", "THE WORKOUT").save(out / "chapter.png")
    title_card(["She stopped", "training", "like this"],
               "The routine everyone quotes is one she gave up in 2021.").save(out / "title.png")
    stat("57", "and training less than at 30", "Born 11 February 1969.").save(out / "stat.png")
    quote("I just burnt out and broke my body.",
          "Jennifer Aniston to InStyle").save(out / "quote.png")
    week([("Mon", "Low-impact resistance - lower body", "30-50 min"),
          ("Tue", "Cardio blended into the resistance work", "30-50 min"),
          ("Wed", "Arms and abs, short format", "15 min"),
          ("Thu", "Low-impact resistance - upper body and back", "30-50 min"),
          ("Fri", "Boxing or rope, if the body allows", "20-30 min"),
          ("Sat", "Mobility and stretching", "15-20 min"),
          ("Sun", "Rest", "-")]).save(out / "week.png")
    subscribe().save(out / "subscribe.png")
    endcard().save(out / "end.png")
    print(f"brand check written to {out}")
