"""Section 5's QC: read every card, and read it over what it actually sits on.

Two artifacts, and they answer different questions.

  qc/CARD_SHEET.jpg   every card in the film, one tile each, full text visible.
                      "Is this a whole sentence, correctly credited?"
  qc/CARD_OVER.jpg    each card over its REAL underlying shot, at full size,
                      one panel per SAMPLED INSTANT - head, tail and the
                      middle of every carded shot, never fewer than two.
                      "Can I read it there, and is the thing behind it
                      appropriate to the words - for the whole time it is up?"

                      It used to be one panel per shot, taken at the midpoint,
                      and that is how two hard failures shipped: shot 169 is
                      a clean single on her at its midpoint and holds Jay Leno
                      for its last 3.2s under a card crediting her, and shot
                      201 is a clean portrait at its midpoint and holds a
                      full-frame ELLE cover for its last 1.7s. Both were
                      "read" and passed. An artifact that looks at one instant
                      of a 6.2-second shot is not evidence about the shot.

CARD_OVER pulls its backgrounds out of the rendered pieces in pieces5/ - the
actual MP4 that goes into the concat - so what you are looking at is the frame
the viewer sees, graded, pushed and all. It does NOT re-grab from the source
and it does NOT use a placeholder. If a card's piece is missing the panel says
so rather than drawing something else.

The mechanical checks run alongside and are printed, not hidden:

  * OCR (rapidocr_onnxruntime - tesseract/pytesseract/easyocr are not installed
    here) must read the COMPLETE card text off the PNG. Asserting a substring
    is the bug: a prefix passes a substring test, and a prefix is exactly what
    this section was opened to kill.
  * No card's text may be a strict prefix of any quote in quotes.json.
  * Every print/attributed card must carry its outlet.
  * WCAG contrast of the card's ink against the composited background, sampled
    across the card, must be >= 4.5:1.

    python card_qc.py
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
QC = ROOT / "qc"
PIECES = ROOT / "pieces5"
FONTS = Path("C:/Users/avina/ytceleb/graphics/public/fonts")
sys.path.insert(0, str(ROOT))

import cards as CARD          # noqa: E402
import quotecards as QCARD    # noqa: E402


def norm(s: str) -> str:
    """Compare like a reader, not like a byte stream.

    The renderer sets curly apostrophes and a real ellipsis; the ledger has
    straight ones. OCR drops and invents punctuation and case. Everything below
    is folded away EXCEPT the letters and digits, in order - which is the part
    a prefix bug shows up in.
    """
    s = (s.replace("\u2019", "'").replace("\u2018", "'")
          .replace("\u201c", '"').replace("\u201d", '"')
          .replace("\u2026", "...").replace("\u2013", "-").replace("\u2014", "-"))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def ocr_text(png: Path, crop=None, scale: int = 1) -> str:
    from rapidocr_onnxruntime import RapidOCR
    global _OCR
    try:
        _OCR
    except NameError:
        _OCR = RapidOCR()
    # White-on-near-black with alpha: flatten onto black, which is what the
    # card sits on anyway once the .93 fill is over footage.
    im = Image.open(png).convert("RGBA")
    flat = Image.new("RGB", im.size, (0, 0, 0))
    flat.paste(im, mask=im.split()[3])
    if crop:
        flat = flat.crop(crop)
    if scale != 1:
        flat = flat.resize((flat.width * scale, flat.height * scale), Image.LANCZOS)
    tmp = QC / "_ocr_tmp.png"
    flat.save(tmp)
    res, _ = _OCR(str(tmp))
    return " ".join(d[1] for d in (res or []))


def flat(s: str) -> str:
    """Letters and digits only - the form ALL OCR comparison uses.

    RapidOCR puts spaces where the renderer did not ("What Ido with Jennifer
    Aniston", "20to 30") and drops them where it did. Comparing with spaces
    reported nine card-carrying frames of the finished cut as truncated when
    every one of them is whole - I had read them by eye first, which is the
    only reason the check was not believed. Removing spaces costs nothing: a
    PREFIX is still a prefix once the spaces are gone, which is the property
    this whole file exists to test.

    The credit is set at 20px with .16em tracking, and RapidOCR reads that back
    as "JENNIFERANISTONTOABCNEWS" - one token, no spaces. Comparing with spaces
    reports a missing outlet on a card that plainly has one. ocr_sweep.py hit
    the same thing and solved it the same way.
    """
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def lum(rgb) -> float:
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def contrast(fg, bg) -> float:
    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def composite(bg: Image.Image, card_png: Path) -> Image.Image:
    card = Image.open(card_png).convert("RGBA")
    out = bg.convert("RGBA").copy()
    out.alpha_composite(card)
    return out.convert("RGB")


def card_contrast(frame: Image.Image, card_png: Path, box,
                  burned: bool = True) -> float:
    """Worst ink-vs-paper contrast anywhere inside the card, on THIS frame.

    The card PNG's alpha says which pixels are drawn; the near-white ones are
    type and the near-black ones are the fill. The COLOURS are read off the
    frame, because that is what a reader sees - the fill is 93% opaque, not
    100%, so a blown-out background lifts the paper and closes the gap.

    `burned=True` means the frame already has the card on it (a frame pulled
    out of the finished film), so it must NOT be composited again - doing that
    would darken the paper and report a contrast nobody experiences.
    """
    x, y, w, h = box
    card = Image.open(card_png).convert("RGBA")
    comp = frame if burned else composite(frame, card_png)
    ca = np.asarray(card.crop((x, y, x + w, y + h)), float)
    co = np.asarray(comp.convert("RGB").crop((x, y, x + w, y + h)), float)
    alpha = ca[..., 3]
    ink = (alpha > 200) & (ca[..., :3].mean(axis=2) > 170)     # the type
    paper = (alpha > 200) & (ca[..., :3].mean(axis=2) < 60)    # the fill
    if ink.sum() < 50 or paper.sum() < 50:
        return 0.0
    fg = co[ink].mean(axis=0)
    # worst paper in the card, not the average - a blown-out background makes
    # the fill lighter in one corner only
    ph, pw = paper.shape
    worst = 99.0
    for gy in range(0, ph - 8, max(1, ph // 6)):
        for gx in range(0, pw - 8, max(1, pw // 8)):
            m = paper[gy:gy + ph // 6, gx:gx + pw // 8]
            if m.sum() < 40:
                continue
            bgc = co[gy:gy + ph // 6, gx:gx + pw // 8][m].mean(axis=0)
            worst = min(worst, contrast(fg, bgc))
    return worst if worst < 99 else contrast(fg, co[paper].mean(axis=0))


# ── which piece is under which card ─────────────────────────────────────────
def card_shots() -> list:
    """Every shot in the finished ledger that carries a card, in film order."""
    man = json.loads((ROOT / "manifest" / "shots5.json").read_text(encoding="utf-8"))
    fps = man["fps"]
    out, t = [], 0.0
    for i, r in enumerate(man["shots"]):
        dur = r["frames"] / fps
        if r.get("card"):
            out.append(dict(i=i, t=t, dur=dur, **r))
        t += dur
    return out


# How many instants of each carded shot CARD_OVER shows.
#
# THIS ARTIFACT IS PART OF THE DEFECT IT IS SUPPOSED TO CATCH. Until this pass
# it pulled exactly ONE frame per carded shot, s["t"] + s["dur"]/2, and every
# shot in the film was declared read on the strength of it. That is why
# qc/CARD_OVER_D2.jpg showed a clean black-and-white portrait for shot 201
# while a full-frame ELLE cover was on screen 1.4 seconds later, and why
# qc/CARD_OVER_D1.jpg showed a clean single of her for shot 169 while Jay Leno
# holds the last 3.2 of its 6.2 seconds under a card crediting her.
#
# A card lives for its whole duration, so the artifact has to show its whole
# duration: head, tail, and enough of the middle that no more than
# OVER_STEP seconds of any card's bed goes unlooked-at.
OVER_STEP = 1.5


def over_times(s: dict) -> list:
    """(label, film time) for every instant of this carded shot to show.

    Head and TAIL always - the tail is where both R1 and R2 hid - plus
    intermediate samples for anything long enough to need them. The head is
    nudged 0.1s in and the tail 0.1s back so a frame grab cannot land on the
    neighbouring shot across a boundary.
    """
    t, dur = s["t"], s["dur"]
    n = max(1, int(math.ceil(dur / OVER_STEP)))
    pts = [t + dur * i / n for i in range(n + 1)]
    pts[0] = t + min(0.1, dur / 4)
    pts[-1] = t + max(0.0, dur - 0.1)
    labs = ["head"] + [f"+{p - t:.1f}s" for p in pts[1:-1]] + ["TAIL"]
    if len(pts) == 2:
        labs = ["head", "TAIL"]
    return list(zip(labs, [round(p, 3) for p in pts]))


FILM = ROOT / "JENNIFER_ANISTON_V6.mp4"


def _still(stem: str) -> Path:
    for d in ("stills_move", "stills_place", "stills_food", "stills"):
        p = ROOT / d / f"{stem}.jpg"
        if p.exists():
            return p
    raise SystemExit(f"card_qc: still not found: {stem}")


def frame_at(t: float, out: Path) -> "Path | None":
    """A frame from the FINISHED FILM. Keyed on the film's mtime, because a
    cached frame from the previous cut is this project's most repeated bug."""
    if not FILM.exists():
        return None
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}",
                        "-i", str(FILM), "-frames:v", "1", str(out)], check=True)
    return out


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def wrap(d, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def sheet(rows, path: Path, cols=3, tile=(940, 700)) -> None:
    """CARD_SHEET: the cards themselves, on a neutral checker, full text."""
    tw, th = tile
    n = len(rows)
    r = (n + cols - 1) // cols
    img = Image.new("RGB", (cols * tw, r * th), (26, 26, 28))
    d = ImageDraw.Draw(img)
    hd, sm = font("ArchivoBlack-Regular.ttf", 26), font("Archivo-Medium.ttf", 21)
    for k, row in enumerate(rows):
        ox, oy = (k % cols) * tw, (k // cols) * th
        # a mid-grey ground so white type and the dark fill are both visible
        d.rectangle([ox + 8, oy + 74, ox + tw - 8, oy + th - 8], fill=(112, 112, 116))
        card = Image.open(row["png"]).convert("RGBA")
        scale = (tw - 16) / 1920
        card = card.resize((int(1920 * scale), int(1080 * scale)), Image.LANCZOS)
        img.paste(card, (ox + 8, oy + th - 8 - card.height), card)
        d.text((ox + 18, oy + 14), f"{row['block']}  {row['id']}", font=hd,
               fill=(255, 255, 255))
        d.text((ox + 18, oy + 46), row["note"], font=sm, fill=(210, 210, 214))
    img.save(path, quality=92)
    print(f"  wrote {path}  {img.size[0]}x{img.size[1]}")


def over(panels, path: Path, cols: int = 2) -> None:
    """CARD_OVER: each card over its real shot, big enough to read.

    1280x720 a panel - the card's 48px type comes back as 32px here, which is
    the size it plays at on a laptop. Anything smaller and you are checking that
    a card EXISTS rather than reading it, which is the failure mode the red-flag
    table calls out.
    """
    pw, ph, head = 1280, 720, 96
    rows = (len(panels) + cols - 1) // cols
    img = Image.new("RGB", (pw * cols, (ph + head) * rows), (18, 18, 20))
    d = ImageDraw.Draw(img)
    hd, sm = font("ArchivoBlack-Regular.ttf", 28), font("Archivo-Medium.ttf", 22)
    for k, p in enumerate(panels):
        ox, oy = (k % cols) * pw, (k // cols) * (ph + head)
        d.text((ox + 22, oy + 16), p["title"], font=hd, fill=(255, 255, 255))
        for j, ln in enumerate(wrap(d, p["note"], sm, pw - 44)[:2]):
            d.text((ox + 22, oy + 50 + j * 24), ln, font=sm, fill=(200, 200, 206))
        if p["img"] is None:
            d.rectangle([ox, oy + head, ox + pw, oy + head + ph], fill=(60, 20, 20))
            d.text((ox + 30, oy + head + 40), "NO REAL BACKGROUND AVAILABLE - "
                   "not drawing a substitute", font=hd, fill=(255, 160, 160))
            continue
        img.paste(p["img"].resize((pw, ph), Image.LANCZOS), (ox, oy + head))
    img.save(path, quality=90)
    print(f"  wrote {path}  {img.size[0]}x{img.size[1]}")


def stills_sheets() -> list:
    """qc/CARD_STILLS_*.jpg - EVERY still in the project, with the card gate's
    verdict and the detector numbers behind it burned into the tile.

    This is the artifact for "re-audit by eye every still that carries a card".
    It shows the whole pool rather than just the current beds, because the beds
    move every time a span moves: a still that carries no card today is one
    re-pick away from carrying one, and the question "is there a person in this
    picture" has the same answer either way.

    Green = the gate allows a card here. Red = denied. Orange = allowed only
    because a human name-cleared it while the detectors say person
    (reels5.CARD_STILL_CLEAR); those are the tiles where the gate is somebody's
    eyes, so they are marked as such and counted in the report.
    """
    import reels5
    import build5
    import cv2  # noqa: F401  (imported for the same opencv build reels5 uses)
    rows, fails = [], []
    dirs = ("stills", "stills_move", "stills_food", "stills_place")
    names = sorted({p.stem: p for d in dirs
                    for p in (ROOT / d).glob("*.jpg")}.items())
    for stem, path in names:
        ev = reels5.person_evidence(path)
        denied_by_name = (stem in reels5.CARD_STILL_DENY
                          or stem.startswith(reels5.CARD_STILL_DENY_PREFIX))
        ok = reels5.card_still_ok(path)
        rows.append(dict(stem=stem, path=path, ev=ev, ok=ok,
                         found=reels5.person_found(ev),
                         by_name=denied_by_name,
                         body=stem in reels5.CARD_STILL_BODY,
                         cleared=stem in reels5.CARD_STILL_CLEAR))
    cols, tw = 5, 420
    per = 30
    made = []
    for pg in range((len(rows) + per - 1) // per):
        chunk = rows[pg * per:(pg + 1) * per]
        th = int(tw * 9 / 16) + 46
        img = Image.new("RGB", (cols * tw, ((len(chunk) + cols - 1) // cols) * th),
                        (16, 16, 18))
        d = ImageDraw.Draw(img)
        hd = font("ArchivoBlack-Regular.ttf", 17)
        sm = font("Archivo-Medium.ttf", 15)
        for k, r in enumerate(chunk):
            ox, oy = (k % cols) * tw, (k // cols) * th
            im = Image.open(r["path"]).convert("RGB")
            im = im.resize((tw - 4, int(tw * 9 / 16) - 4), Image.LANCZOS)
            if r["ok"] and r["found"]:
                edge = (232, 150, 40)     # human override
            elif r["ok"]:
                edge = (60, 170, 90)
            else:
                edge = (220, 50, 50)
            d.rectangle([ox, oy + 46, ox + tw - 1, oy + th - 1], fill=edge)
            img.paste(im, (ox + 2, oy + 48))
            e = r["ev"]
            tag = ("DENIED (by name)" if not r["ok"] and r["by_name"] else
                   "DENIED - person" if not r["ok"] else
                   "ok - HUMAN OVERRIDE" if r["found"] and r["cleared"] else
                   "ok - BODY, judged" if r["body"] else "ok")
            d.text((ox + 6, oy + 4), r["stem"], font=hd, fill=(255, 255, 255))
            d.text((ox + 6, oy + 25), tag, font=sm, fill=edge)
            d.text((ox + 176, oy + 25),
                   f"face {e['face']:.3f} up {e['upper']:.3f} "
                   f"fu {e['full']:.3f} hog {e['hog']:.3f}",
                   font=sm, fill=(170, 170, 176))
        p = QC / f"CARD_STILLS_{pg}.jpg"
        img.save(p, quality=88)
        made.append(p)
        print(f"  wrote {p}  {img.size[0]}x{img.size[1]}")
    reels5.save_cardstill()
    return rows


def body_stills_rule(shots, slate, ledger) -> list:
    """A still with a human body in it (reels5.CARD_STILL_BODY) may only carry
    a card whose speaker is the subject. See the note on CARD_STILL_BODY: the
    judgement that keeps q_treadmill is "there is no identity in the frame AND
    no third party in the credit", and this is the half a machine can hold.
    """
    import reels5
    out = []
    for s in shots:
        if not s["tag"].startswith("still:"):
            continue
        stem = s["tag"][len("still:"):]
        if stem not in reels5.CARD_STILL_BODY:
            continue
        speaker = ledger[s["card"]]["speaker"]
        if speaker != "Jennifer Aniston":
            out.append(f"BODY STILL {stem} (shot {s['i']}) carries a card "
                       f"spoken by {speaker!r}, not by the subject. "
                       f"reels5.CARD_STILL_BODY says why that is not allowed.")
    return out


def main() -> None:
    QC.mkdir(exist_ok=True)
    QCARD.check()
    slate = QCARD.slate()
    ledger = {e["id"]: e for e in json.loads(
        (ROOT / "quotes.json").read_text(encoding="utf-8"))}
    fails, notes = [], []

    # ── 1. the cards themselves ─────────────────────────────────────────────
    rows = []
    for bid, v in slate.items():
        png = CARD.quote_card(v["text"], v["credit"])
        got = flat(ocr_text(png))
        want = flat(v["text"])
        ok = want in got
        if not ok:
            # say WHERE it diverges, so a prefix is obvious in the report
            n = 0
            while n < len(want) and want[:n + 1] in got:
                n += 1
            fails.append(f"OCR {bid}/{v['id']}: card does NOT carry the whole "
                         f"text. Matched {n}/{len(want)} chars, stops at "
                         f"...{want[max(0,n-40):n]!r}")
        if v["kind"] in ("print", "attributed"):
            outlet = QCARD.OUTLET[v["outlet"]].split(",")[0]
            # the credit is small; read it again off its own strip at 3x if the
            # full-card pass missed it, before calling it illegible
            cred = got
            if flat(outlet) not in flat(cred):
                bx, by, bw, bh = CARD.card_box(png)
                cred = ocr_text(png, crop=(bx, by + bh - 90, bx + bw, by + bh),
                                scale=3)
            if flat(outlet) not in flat(cred):
                fails.append(f"CREDIT {bid}/{v['id']}: outlet {outlet!r} not "
                             f"legible on the card (OCR read {cred!r})")
        # prefix rule, against the whole ledger
        for qid, e in ledger.items():
            f = flat(e["text"])
            if f.startswith(want) and len(f) > len(want) and not v["shortened"]:
                fails.append(f"PREFIX {bid}: card text is a strict prefix of "
                             f"{qid}")
            if v["shortened"] and qid == v["id"] and f.startswith(want):
                fails.append(f"PREFIX {bid}: the SHORTENED text is still a "
                             f"strict prefix of {qid}")
        rows.append(dict(block=bid, id=v["id"], png=png,
                         note=(f"{v['kind']}  |  {len(v['text'].split())}w  "
                               f"hold {v['hold']:.1f}s"
                               f"{'  |  SHORTENED' if v['shortened'] else ''}"
                               f"  |  OCR {'FULL TEXT OK' if ok else 'INCOMPLETE'}")))
    sheet(rows, QC / "CARD_SHEET.jpg")

    # ── 1b. is there a person in the stills a card can land on? ─────────────
    srows = stills_sheets()
    import reels5
    overrides = sorted(r["stem"] for r in srows if r["ok"] and r["found"])
    denied = sorted(r["stem"] for r in srows if not r["ok"])
    notes.append(f"stills: {len(srows)} in the pool, {len(denied)} may not "
                 f"carry a card, {len(overrides)} of the rest are allowed on a "
                 f"human's say-so against the detectors "
                 f"(reels5.CARD_STILL_CLEAR). Read qc/CARD_STILLS_*.jpg.")

    # ── 2. every card over its real shot ────────────────────────────────────
    shots = card_shots()
    fails += body_stills_rule(shots, slate, ledger)
    for s in shots:
        if s["tag"].startswith("still:"):
            stem = s["tag"][len("still:"):]
            if not reels5.card_still_ok(_still(stem)):
                fails.append(f"PERSON {s['block']} shot {s['i']}: the card "
                             f"sits on still {stem}, which the card gate "
                             f"denies. The manifest is older than the gate - "
                             f"rebuild before reading this sheet.")
    if not shots:
        notes.append("manifest/shots5.json carries no `card` field - rebuild "
                     "with the current build5.py before trusting CARD_OVER.")
    panels = []
    stamp = int(FILM.stat().st_mtime) if FILM.exists() else 0
    seen: dict = {}
    for s in shots:
        seen.setdefault(s["card"], []).append(s)
    for qid, group in seen.items():
        bid = group[0]["block"]
        v = slate[bid]
        png = CARD.quote_card(v["text"], v["credit"])
        box = CARD.card_box(png)
        for s in group:
            # EVERY instant of the shot, not just its midpoint. See over_times.
            for j, (lab, ft) in enumerate(over_times(s)):
                f = frame_at(ft, QC / f"cardover_{stamp}_{s['i']:03d}_{j}.jpg")
                if f is None:
                    panels.append(dict(title=f"{bid} shot {s['i']} {lab}  {qid}",
                                       note="no film on disk", img=None))
                    continue
                # the film already HAS the card burned in, so measure on the
                # finished frame directly rather than compositing again
                shot = Image.open(f).convert("RGB").resize((1920, 1080))
                c = card_contrast(shot, png, box, burned=True)
                if c < 4.5:
                    fails.append(f"CONTRAST {bid} shot {s['i']} @{lab}: "
                                 f"{c:.1f}:1 (needs 4.5:1)")
                panels.append(dict(
                    title=f"{bid} shot {s['i']} {lab}  "
                          f"{ft//60:.0f}:{ft%60:05.2f}  {s['tag']}",
                    note=f"{qid}  |  {s['dur']:.1f}s shot  |  contrast "
                         f"{c:.1f}:1  |  "
                         f"{'CUE SHOT' if s.get('cue') else 'gated pick'}  |  "
                         f"{v['credit']}",
                    img=Image.open(f).convert("RGB")))
    if panels:
        over(panels, QC / "CARD_OVER.jpg")
        # ...and one page per block, because CARD_OVER.jpg is 42 shots tall and
        # anything that tall gets downscaled to unreadable by whatever opens it.
        # The pages are the same panels, same size, split so they can actually
        # be READ - which is the only thing this artifact is for.
        for bid in slate:
            page = [q for q in panels if q["title"].startswith(bid + " ")]
            if page:
                over(page, QC / f"CARD_OVER_{bid}.jpg")

    # ── 3. the FILM, not the PNG ────────────────────────────────────────────
    # "OCR found the text, so the card is fine" is a red flag in the skill, and
    # so is checking the artwork instead of the cut. This reads the finished
    # MP4: for every shot that carries a card, the WHOLE card text must be
    # legible in that frame, and nothing legible in it may be a strict prefix
    # of a longer quote in the ledger.
    # Head, tail and the middle, same instants CARD_OVER shows - a card that
    # reads whole at the midpoint and is half off the bottom of frame at the
    # tail is exactly the kind of thing one sample per shot cannot see.
    full_norms = {qid: flat(e["text"]) for qid, e in ledger.items()}
    read_n = 0
    for s in shots:
        for j, (lab, ft) in enumerate(over_times(s)):
            f = frame_at(ft, QC / f"cardover_{stamp}_{s['i']:03d}_{j}.jpg")
            if f is None:
                continue
            read_n += 1
            v = slate[s["block"]]
            want = flat(v["text"])
            png = CARD.quote_card(v["text"], v["credit"])
            bx, by, bw, bh = CARD.card_box(png)
            # Three tiers, each giving the detector MORE pixels of the same
            # frame - never a looser comparison. At 1x and 2x RapidOCR read
            # O2's "30-minute" as "3O-minute", letter O for digit zero, and
            # reported a whole card as truncated; at 3x it reads it correctly.
            # The assertion does not move, only the resolution does.
            got = flat(ocr_text(f))
            for sc in (2, 3):
                if want in got:
                    break
                got = flat(ocr_text(f, crop=(bx - 20, by - 20, bx + bw + 20,
                                             by + bh + 20), scale=sc))
            if want not in got:
                n = 0
                while n < len(want) and want[:n + 1] in got:
                    n += 1
                fails.append(f"FILM {s['block']} shot {s['i']} @{lab} "
                             f"({ft:.1f}s): the card in the CUT does not read "
                             f"whole. Matched {n}/{len(want)} chars.")
            for qid, fn in full_norms.items():
                if fn.startswith(want) and len(fn) > len(want) + 2:
                    fails.append(f"FILM {s['block']} shot {s['i']} @{lab}: the "
                                 f"text on screen is a strict prefix of {qid}")
    print()
    print(f"  {len(rows)} cards, {len(panels)} card-carrying shots, "
          f"{read_n} film frames read across {len(shots)} carded shots")
    for n in notes:
        print(f"  NOTE: {n}")
    if fails:
        print(f"\n  {len(fails)} FAILURES")
        for f in fails:
            print(f"   - {f}")
        raise SystemExit(1)
    print("\n  all mechanical checks pass "
          "(this is not the same as the cards being RIGHT - read CARD_OVER.jpg)")


if __name__ == "__main__":
    main()
