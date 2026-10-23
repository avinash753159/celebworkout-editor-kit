"""The new script, as data.

script4.py is the ELEVEN-MINUTE BIOGRAPHY: a hook, a subscribe ask, five life
chapters, a read-out training week (WK_*) and six read-out food lists (FD_*).
None of that exists any more. script.md is 21 blocks in nine sections and the
narration for every one of them was recorded by section 2 and is already in
manifest/audio5.json.

So this file does not hold a second copy of the words. It reads:

    script.md            for the block ORDER, KIND and SECTION
    manifest/audio5.json for the narration TEXT and the bite windows
    quotes.json          for the credit on each bite

and cross-checks them, because two files that are supposed to agree about
21 blocks will eventually stop agreeing and the failure mode is silent - a
block whose picture is chosen from the wrong section's pool looks like bad
taste, not like a bug.

BLOCKS keeps script4's shape - ("VO", id, section, text) and ("BITE", id, key)
- so build5 needs no new vocabulary for it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Which narration this pipeline is built on. audio6 = the bite-led script
# (she leads, narrator bridges). Set ANISTON_AUDIO=audio5 to rebuild the
# old narration-led cut. One switch, so no run can straddle both.
import os as _os
AUDIO_DIR = _os.environ.get("ANISTON_AUDIO", "audio6")
AUDIO_MAN = AUDIO_DIR + ".json"


ROOT = Path(__file__).resolve().parent

# ── script.md: order, kind, section ───────────────────────────────────────
_HDR = re.compile(r"^###\s+(\S+)\s*\|\s*kind=(\w+)(?:\s*\|\s*section=(\S+))?"
                  r"(?:\s*\|\s*quote=(\S+))?", re.M)

SCRIPT_MD = ROOT / "script.md"
_heads = []
for m in _HDR.finditer(SCRIPT_MD.read_text(encoding="utf-8")):
    bid, kind, section, quote = m.group(1), m.group(2), m.group(3), m.group(4)
    if kind == "bite" and quote is None:
        # "### T1 | kind=bite | quote=jen_mix_it_up" - the regex above puts
        # section and quote in different groups, so a bite line lands its
        # quote id in group 3. Normalise rather than making the pattern
        # cleverer.
        section, quote = None, m.group(3)
    _heads.append((bid, kind, section, quote))

SECTION_OF = {bid: sec for bid, kind, sec, _ in _heads if kind == "vo"}
BLOCK_ORDER = [bid for bid, _, _, _ in _heads]

# ── audio5.json: the recorded narration ───────────────────────────────────
MAN = json.loads((ROOT / "manifest" / AUDIO_MAN).read_text(encoding="utf-8"))
_AUDIO = {b["block"]: b for b in MAN["blocks"]}

if [b["block"] for b in MAN["blocks"]] != BLOCK_ORDER:
    raise SystemExit(
        f"script5: script.md and audio5.json disagree about the block list.\n"
        f"  script.md : {BLOCK_ORDER}\n"
        f"  audio5    : {[b['block'] for b in MAN['blocks']]}\n"
        f"Re-run section 2 rather than reconciling this by hand.")

# ── quotes.json: the credit line for each bite ────────────────────────────
_QUOTES = {e["id"]: e for e in
           json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))}

# key -> (source, t0, t1, credit, text). The key IS the block id for a bite,
# because there is exactly one bite per T-block and the quote id is already on
# the block. script4 used its own short names (OLD, PAST40, INJURY) which were
# a third naming scheme for the same five clips.
BITES: dict = {}
BITE_TEXT: dict = {}
for bid, kind, _, quote in _heads:
    if kind != "bite":
        continue
    a = _AUDIO[bid]
    if a.get("quote_id") != quote:
        raise SystemExit(f"script5: {bid} is quote={quote} in script.md but "
                         f"{a.get('quote_id')} in audio5.json")
    if quote not in _QUOTES:
        raise SystemExit(f"script5: {bid} names quote {quote}, not in quotes.json")
    BITES[bid] = (a["source"], a["t0"], a["t1"], a["credit"], a["text"])
    BITE_TEXT[bid] = a["text"]

# ── a bite whose own footage cannot be shown ──────────────────────────────
# A sync bite normally plays the source it was cut from - her lips have to
# match her voice. BITE_PICTURE is the exception, and there is exactly one:
#
# T4 is voC2DxCL6jQ@4.3-14.4, a Pvolve testimonial ADVERT whose burned-in
# caption runs 0.0-8.1 and 9.6-20.1 (measured with RapidOCR by section 3, see
# reels5.BANNED_WINDOW). Every frame of the 10.1 seconds this bite occupies
# carries text. The audio is hers and stays; the picture cannot be that file.
#
# The replacement has to hold 10.5 seconds without a cut, and cuts.spike can
# only see 7.0 seconds ahead, so no video window in this project can be PROVEN
# to hold it. A still can, trivially. still:q_bands is the Pvolve equipment
# the bite is describing ("an efficient total body workout").
BITE_PICTURE: dict = {"T4": ("still:q_bands", 0.0)}

# ── BLOCKS, in script4's shape ────────────────────────────────────────────
BLOCKS = []
for bid, kind, section, quote in _heads:
    if kind == "vo":
        BLOCKS.append(("VO", bid, section, _AUDIO[bid]["text"]))
    else:
        BLOCKS.append(("BITE", bid, bid))

# script4 exported these and build5 imports them. There is no read-out week
# and no read-out food list in script.md, so they are empty - and empty is the
# honest answer, not a bug. build5's WK_/FD_ branches simply never fire.
WEEK: list = []
FOODS: list = []

VO_BLOCKS = [b[1] for b in BLOCKS if b[0] == "VO"]
BITE_BLOCKS = [b[1] for b in BLOCKS if b[0] == "BITE"]


def check() -> None:
    """Everything the picture pass assumes about the script, asserted."""
    import reels5
    missing = [b for b in VO_BLOCKS if b not in reels5.SECTION_POOL]
    if missing:
        raise SystemExit(
            f"script5: {missing} have no pool in reels5.SECTION_POOL. A "
            f"missing block used to fall through to POOLS['life'], which is "
            f"how a block about her diet drew on 1990s footage.")
    wt = json.loads((ROOT / "manifest" / "word_times5.json").read_text(encoding="utf-8"))
    nowt = [b for b in VO_BLOCKS if b not in wt]
    if nowt:
        raise SystemExit(f"script5: no word timings for {nowt}; cues in those "
                         f"blocks would drift. Run word_times5.py.")
    extra = [b for b in wt if b not in VO_BLOCKS]
    if extra:
        raise SystemExit(f"script5: word_times5.json has blocks the script "
                         f"does not: {extra}")


if __name__ == "__main__":
    check()
    print(f"{len(BLOCKS)} blocks, {len(VO_BLOCKS)} VO, {len(BITE_BLOCKS)} bites")
    for it in BLOCKS:
        kind, bid = it[0], it[1]
        if kind == "VO":
            a, b = it[2], it[3]
            print(f"  {bid:<4} vo   {a:<9} {len(b.split()):>4}w  "
                  f"{_AUDIO[bid]['seconds']:>6.2f}s")
        else:
            src, t0, t1, credit, _ = BITES[bid]
            pic = BITE_PICTURE.get(bid)
            print(f"  {bid:<4} bite {'':<9} {src}@{t0}-{t1}  "
                  f"{_AUDIO[bid]['seconds']:>6.2f}s  {credit[:34]}"
                  f"{'  PICTURE=' + pic[0] if pic else ''}")
