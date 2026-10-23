"""Full-frame data cards. One layout per card, enforced in code.

THE OWNER'S TWO INSTRUCTIONS, BOTH STRUCTURAL
---------------------------------------------
*"Make these cards the whole window."* The picture cuts away, the data owns the
frame, then it cuts back. These are not lower thirds.

*"Change the format of these cards - they all look the same."* One panel
template reused nineteen times is the defect. Shape follows data: a duration
gets a clock, a comparison gets a versus, a list gets a checklist, a single
number gets a big number.

`emit()` REFUSES to write two cards sharing a `kind`. That rule lives in code
rather than in review because "they all look the same" only becomes visible when
every card is on screen together, which is far too late to restructure them.

COLOUR
------
Accent is **#E8121A**, measured off the channel's own video, NOT the brand
document's #B22B1A. `REFERENCE_SPEC.md` records the discrepancy and the skill
resolves it: *"Where the document and the channel disagree, the channel wins."*

Type is three families, never more than two in a frame: Anton for the hero
line, Archivo Black for names and labels, Archivo Regular/Medium for
information. 70% black/white, 20% neutral, 10% red - red is the signature, not
the ground.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
CARDS = ROOT / "cards"
MAN = ROOT / "manifest"
CARDS.mkdir(exist_ok=True)

W, H = 1280, 720
RED = (232, 18, 26)
INK = (12, 12, 13)
PAPER = (247, 245, 242)
GREY = (128, 126, 124)
FPS = 30

_emitted: dict[str, str] = {}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


ANTON = lambda s: font("Anton-Regular.ttf", s)
BLACK = lambda s: font("ArchivoBlack-Regular.ttf", s)
REG = lambda s: font("Archivo-Regular.ttf", s)
MED = lambda s: font("Archivo-Medium.ttf", s)


def _base(dark: bool = True) -> Image.Image:
    return Image.new("RGB", (W, H), INK if dark else PAPER)


def _text(d, xy, s, f, fill, anchor="la", spacing=4):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, spacing=spacing)


def fit(d, s, maker, maxw, start: int, floor: int = 28):
    """Largest size at which `s` fits in `maxw`.

    Hand-tuned point sizes break the moment the copy changes: the first render
    of `counter` clipped "15 YEARS" off the right edge of the frame at 150pt.
    Fitting is measured, so a longer phrase shrinks instead of disappearing.
    """
    size = start
    while size > floor and d.textlength(s, font=maker(size)) > maxw:
        size -= 4
    return maker(size)


def _wrap(d, s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _footer(d, source: str):
    """Every claim carries its source on screen."""
    if not source:
        return
    _text(d, (64, H - 52), source[:96].upper(), REG(17), GREY)


# ---------------------------------------------------------------------------
# layouts - one function per kind, each visually distinct
# ---------------------------------------------------------------------------
def lay_record(d, im, data):
    """Three years stacked, each struck through in red."""
    _text(d, (64, 92), "ELIMINATED BY DETROIT", BLACK(38), PAPER)
    ys = [220, 350, 480]
    for y, yr in zip(ys, data["items"][:3]):
        _text(d, (64, y), str(yr), ANTON(120), PAPER)
        w = d.textlength(str(yr), font=ANTON(120))
        d.line([(64, y + 74), (64 + w, y + 74)], fill=RED, width=9)
    _text(d, (700, 250), data.get("note", ""), MED(30), GREY)


def lay_counter(d, im, data):
    """A → B, with an arrow that dominates the frame."""
    _text(d, (64, 120), data["label"].upper(), BLACK(34), GREY)
    fa = fit(d, data["a"], ANTON, 440, 150)
    _text(d, (64, 210), data["a"], fa, PAPER)
    d.polygon([(560, 300), (700, 300), (700, 265), (790, 318),
               (700, 371), (700, 336), (560, 336)], fill=RED)
    fb = fit(d, data["b"], ANTON, W - 830 - 48, 150)
    _text(d, (830, 210), data["b"], fb, RED)
    _text(d, (64, 430), data.get("note", ""), MED(30), GREY)


def lay_gauge(d, im, data):
    """A vertical bar filling to a measured value."""
    _text(d, (64, 90), data["label"].upper(), BLACK(34), PAPER)
    x0, y0, x1, y1 = 120, 200, 300, 620
    d.rectangle([x0, y0, x1, y1], outline=GREY, width=3)
    frac = float(data["value"]) / float(data["max"])
    fh = (y1 - y0) * frac
    d.rectangle([x0 + 4, y1 - fh, x1 - 4, y1 - 4], fill=RED)
    _text(d, (360, 250), data["big"], ANTON(160), PAPER)
    for i, ln in enumerate(_wrap(d, data.get("note", ""), MED(30), 780)):
        _text(d, (360, 440 + i * 40), ln, MED(30), GREY)


def lay_clock(d, im, data):
    """A clock face with a shaded window between two hours."""
    cx, cy, r = 330, 360, 200
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=PAPER, width=5)
    a0 = math.radians(float(data["from_h"]) / 12 * 360 - 90)
    a1 = math.radians(float(data["to_h"]) / 12 * 360 - 90)
    d.pieslice([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8],
               math.degrees(a0), math.degrees(a1), fill=RED)
    for i in range(12):
        a = math.radians(i / 12 * 360 - 90)
        d.line([(cx + math.cos(a) * (r - 22), cy + math.sin(a) * (r - 22)),
                (cx + math.cos(a) * (r - 6), cy + math.sin(a) * (r - 6))],
               fill=PAPER, width=3)
    _text(d, (600, 210), data["big"], ANTON(96), PAPER)
    for i, ln in enumerate(_wrap(d, data.get("note", ""), MED(30), 600)):
        _text(d, (600, 340 + i * 40), ln, MED(30), GREY)


def lay_checklist(d, im, data):
    """Two columns of items, each with a red rule."""
    _text(d, (64, 84), data["label"].upper(), BLACK(36), PAPER)
    items = data["items"]
    half = (len(items) + 1) // 2
    for col, group in enumerate((items[:half], items[half:])):
        x = 64 + col * 600
        for i, it in enumerate(group):
            y = 190 + i * 74
            d.rectangle([x, y + 14, x + 26, y + 20], fill=RED)
            _text(d, (x + 46, y), it.upper(), BLACK(30), PAPER)


def lay_versus(d, im, data):
    """A split frame: asked versus done."""
    d.rectangle([0, 0, W // 2 - 3, H], fill=INK)
    d.rectangle([W // 2 + 3, 0, W, H], fill=RED)
    _text(d, (W // 4, 250), data["a_label"].upper(), BLACK(32), GREY, anchor="ma")
    _text(d, (W // 4, 300), data["a"], ANTON(190), PAPER, anchor="ma")
    _text(d, (W * 3 // 4, 250), data["b_label"].upper(), BLACK(32), (255, 210, 208), anchor="ma")
    _text(d, (W * 3 // 4, 300), data["b"], ANTON(190), PAPER, anchor="ma")


def lay_bracket(d, im, data):
    """A series result as four filled squares."""
    _text(d, (64, 96), data["label"].upper(), BLACK(38), PAPER)
    for i in range(int(data["of"])):
        x = 64 + i * 150
        won = i < int(data["won"])
        d.rectangle([x, 250, x + 120, 400], fill=RED if won else INK,
                    outline=PAPER, width=3)
        _text(d, (x + 60, 300), "W" if won else "-", ANTON(80),
              PAPER if won else GREY, anchor="ma")
    _text(d, (64, 470), data["big"], ANTON(110), PAPER)
    _text(d, (64, 610), data.get("note", ""), MED(28), GREY)


def lay_clockface(d, im, data):
    """A countdown bar to tip-off."""
    _text(d, (64, 100), data["label"].upper(), BLACK(36), PAPER)
    x0, x1, y = 64, W - 64, 330
    d.line([(x0, y), (x1, y)], fill=GREY, width=6)
    for i, (frac, lab) in enumerate(data["marks"]):
        x = x0 + (x1 - x0) * float(frac)
        d.line([(x, y - 30), (x, y + 30)], fill=RED, width=7)
        _text(d, (x, y + 52), lab.upper(), BLACK(24), PAPER, anchor="ma")
    _text(d, (64, 470), data["big"], ANTON(120), RED)
    _text(d, (64, 620), data.get("note", ""), MED(28), GREY)


def lay_split(d, im, data):
    """The orthodoxy above, him below."""
    d.rectangle([0, 0, W, H // 2 - 2], fill=PAPER)
    _text(d, (64, 90), data["a_label"].upper(), BLACK(30), GREY)
    _text(d, (64, 150), data["a"], ANTON(96), INK)
    _text(d, (64, 420), data["b_label"].upper(), BLACK(30), (200, 120, 116))
    _text(d, (64, 480), data["b"], ANTON(96), RED)


def lay_bignumber(d, im, data):
    """One number, the size of the frame."""
    _text(d, (64, 110), data["label"].upper(), BLACK(36), GREY)
    _text(d, (64, 190), data["big"], ANTON(340), PAPER)
    d.rectangle([64, 560, 420, 572], fill=RED)
    for i, ln in enumerate(_wrap(d, data.get("note", ""), MED(30), 1100)):
        _text(d, (64, 600 + i * 40), ln, MED(30), GREY)


def lay_concept(d, im, data):
    """A phrase, boxed, with a rule under it."""
    lines = _wrap(d, data["big"], ANTON(130), W - 200)
    y = 260 - len(lines) * 40
    for ln in lines:
        _text(d, (W // 2, y), ln, ANTON(130), PAPER, anchor="ma")
        y += 140
    d.rectangle([W // 2 - 180, y + 20, W // 2 + 180, y + 32], fill=RED)
    for i, ln in enumerate(_wrap(d, data.get("note", ""), MED(30), 900)):
        _text(d, (W // 2, y + 80 + i * 40), ln, MED(30), GREY, anchor="ma")


def lay_event(d, im, data):
    """A dated moment on a timeline."""
    y = 400
    d.line([(0, y), (W, y)], fill=GREY, width=4)
    x = 300
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=RED)
    _text(d, (x - 20, y - 150), data["big"], ANTON(120), PAPER)
    for i, ln in enumerate(_wrap(d, data.get("note", ""), MED(32), 820)):
        _text(d, (x - 20, y + 70 + i * 44), ln, MED(32), GREY)


LAYOUTS = {
    "record": lay_record, "counter": lay_counter, "gauge": lay_gauge,
    "clock": lay_clock, "checklist": lay_checklist, "versus": lay_versus,
    "bracket": lay_bracket, "clockface": lay_clockface, "split": lay_split,
    "bignumber": lay_bignumber, "concept": lay_concept, "event": lay_event,
}


def emit(cid: str, kind: str, data: dict, source: str = "") -> Path:
    """Render one card. REFUSES a duplicate layout."""
    if kind not in LAYOUTS:
        raise KeyError(f"no layout '{kind}' (have {sorted(LAYOUTS)})")
    if kind in _emitted and _emitted[kind] != cid:
        raise RuntimeError(
            f"layout '{kind}' already used by card '{_emitted[kind]}'; "
            f"'{cid}' needs its own shape. The owner's note was 'change the "
            f"format of these cards - they all look the same'.")
    _emitted[kind] = cid
    im = _base(dark=(kind != "split"))
    d = ImageDraw.Draw(im)
    LAYOUTS[kind](d, im, data)
    _footer(d, source)
    dest = CARDS / f"{cid}.png"
    im.save(dest)
    return dest


def card_clip(png: Path, seconds: float, dest: Path) -> Path:
    """A still card becomes a full-frame shot with a slow push-in."""
    nf = round(seconds * FPS)
    zoom = f"zoompan=z='min(zoom+0.00045,1.06)':d={nf}:s={W}x{H}:fps={FPS}"
    subprocess.run(["ffmpeg", "-v", "error", "-loop", "1", "-i", str(png),
                    "-vf", f"{zoom},format=yuv420p", "-frames:v", str(nf),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-r", str(FPS), str(dest), "-y"], capture_output=True)
    return dest


def reset() -> None:
    _emitted.clear()
