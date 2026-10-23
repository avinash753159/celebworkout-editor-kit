"""Full-frame data moments, synced to the word that names them.

Two instructions from the owner govern this file, and both are quoted because
both were ignored once already:

  "Make these cards the whole window."  "Make these the whole screen."
  "Change the format of these cards - they all look the same."

So: the picture CUTS AWAY, the data owns the frame, and it cuts back. And no
two graphics share a layout - the form follows the shape of the number, not a
house template. `emit()` enforces one `kind` per graphic, because "they all look
the same" is a fault that only becomes visible once they are all on screen
together, which is far too late to find it.

Timing is word-level, from `manifest/word_times5.json` plus block offsets. A
graphic's `at` is the phrase that triggers it; a checklist's rows each carry
their own phrase so they land on the word that names them. Phrases match the ASR
TRANSCRIPT, not script.md - the two differ - and `emit()` refuses to write on a
miss rather than falling back to a block start.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FPS = 30

# Every entry a different `kind`. That constraint is the point of the file.
GRAPHICS = [
    dict(id="the_old_week", block="W2", kind="weekgrid",
         title="THE ROUTINE THAT BROKE",
         note="JENNIFER ANISTON, IN HER OWN WORDS",
         at="deliberate variety", hold=2.6,
         days=5, caption="Five days a week, minimum - rotated to beat boredom"),

    dict(id="the_rotation", block="W3", kind="orbit",
         title="ALL OF IT, ON ROTATION",
         note="AND ALL OF IT LOADING THE SPINE",
         at="Every one of those is impact", hold=2.8,
         items=["Spinning", "Yoga", "Strength", "Circuits", "Treadmill"]),

    dict(id="the_rule", block="W5", kind="bignumber",
         title="THE RULE SHE CARRIED", note="JENNIFER ANISTON TO INSTYLE",
         at="45 minutes of cardio", hold=3.2,
         value="45", unit="MINUTES OF CARDIO",
         caption="...or, she believed, it did not count"),

    dict(id="the_barbie", block="W5", kind="tally",
         title="WHAT FIFTEEN YEARS COST",
         note="HER PHYSICAL THERAPIST'S DEMONSTRATION",
         at="one strip for every injury", hold=3.4,
         count=15, unit="YEARS",
         caption="A Barbie doll wrapped in kinesio tape - one strip per injury"),

    dict(id="off_the_menu", block="W7", kind="strikelist",
         title="WHAT A BACK INJURY REMOVES",
         note="ALL OF IT DRIVES FORCE INTO THE LUMBAR SPINE",
         at="removes the entire menu", hold=2.6,
         items=["Running", "Rope", "Plyometrics", "Hard spinning"]),

    dict(id="three_planes", block="W12", kind="planes",
         title="TRAINED THROUGH THREE PLANES", note="DANI COLEMAN, PVOLVE HEAD TRAINER",
         at="Three planes instead of one", hold=3.2,
         items=["Side to side", "Front to back", "Rotational"]),

    dict(id="the_goal", block="W13", kind="triad",
         title="THE GOAL IS BROADER THAN STRENGTH", note="DANI COLEMAN",
         at="Strength, stability and mobility", hold=3.0,
         items=["Strength", "Stability", "Mobility"]),

    dict(id="fifteen_beats_sixty", block="W17", kind="versus",
         title="THE MATH THAT ACTUALLY MATTERS", note="SAME SIXTY MINUTES A WEEK",
         at="15 minutes done four times", hold=4.0,
         win=dict(label="15 min x 4", sub="happens", segs=4),
         lose=dict(label="60 min x 1", sub="quietly stops in November", segs=1)),

    dict(id="two_mistakes", block="W19", kind="numbered",
         title="THE TWO MISTAKES SHE SEES MOST", note="DANI COLEMAN, ON EVERYBODY ELSE",
         at="number one mistake", hold=3.4,
         items=[dict(label="No plan, and sporadic",
                     sub="training without a game plan"),
                dict(label="Fear of building muscle",
                     sub="you will not bulk from weight training")]),

    dict(id="why_lift", block="W20", kind="decline",
         title="WHY SHE LIFTS AFTER FORTY", note="JENNIFER ANISTON TO TODAY",
         at="keeping bones and muscles strong", hold=3.4,
         caption="Muscle mass and bone density both fall with age. "
                 "Loading them is the only thing that holds it off."),

    dict(id="the_morning", block="W23", kind="timeline",
         title="THE MORNING ORDER", note="THE ORDER IS THE POINT, NOT THE INGREDIENTS",
         at="Juice, then meditation", hold=3.4,
         items=["Juice", "Meditation", "Coffee, +30 min", "The dogs", "The workout"]),

    dict(id="sixteen_eight", block="W25", kind="clock",
         title="16:8", note="JENNIFER ANISTON, ON CAMERA",
         at="16 8 pattern", hold=4.2, fasted=16,
         caption="Dinner at 8. First solid meal at noon. "
                 "Sleep does most of the work."),

    dict(id="the_prep", block="W26", kind="fridge",
         title="THE SUNDAY PREP", note="JENNIFER ANISTON TO ELLE",
         at="it is the preparation", hold=3.6,
         items=["Cut raw vegetables", "Hard-boiled eggs",
                "Butter lettuce", "Pulled chicken"]),

    dict(id="eighty_twenty", block="W28", kind="split",
         title="THE RATIO SHE GAVE PEOPLE", note="CONFIRMED BY HER TRAINER",
         at="80 % healthy living", hold=3.8,
         a=dict(label="Healthy living", value=80),
         b=dict(label="The martini and the pizza", value=20)),

    dict(id="four_things", block="W29", kind="checklist",
         title="WHAT ACTUALLY TRANSFERS", note="NOT THE TRAINER, AND NOT THE EQUIPMENT",
         at="Four things", hold=4.0,
         items=[dict(label="Change the unit of measurement",
                     sub="tension held, not minutes of cardio", at="First"),
                dict(label="Shrink the minimum",
                     sub="one 15-minute session for your worst day", at="Second"),
                dict(label="Train the directions you skip",
                     sub="rotation, side-to-side, and hips first", at="Third"),
                dict(label="Prepare the food, don't plan it",
                     sub="cut veg, boiled eggs, cooked protein", at="Fourth")]),

    dict(id="what_she_credits", block="W30", kind="constellation",
         title="WHAT SHE CREDITS IT TO", note="JENNIFER ANISTON TO TODAY",
         at="completely unglamorous", hold=4.0,
         items=["Exercise", "Good nutrition", "Sleep", "Meditation",
                "Mental health", "Enjoying her life"]),
]

_PUNCT = re.compile(r"[^a-z0-9%]+")


def _norm(s: str) -> list[str]:
    return [t for t in _PUNCT.sub(" ", s.lower()).split() if t]


def _find(words: list, phrase: str, after: float = -1.0):
    toks = _norm(phrase)
    flat, owner = [], []
    for i, w in enumerate(words):
        for t in _norm(w[0]):
            flat.append(t)
            owner.append(i)
    n = len(toks)
    for i in range(len(flat) - n + 1):
        if flat[i:i + n] == toks:
            a, b = owner[i], owner[i + n - 1]
            if words[a][1] >= after:
                return words[a][1], words[b][2]
    raise KeyError(phrase)


def build() -> dict:
    words = json.loads((ROOT / "manifest" / "word_times5.json").read_text(encoding="utf-8"))
    offs = json.loads((ROOT / "manifest" / "block_offsets.json").read_text(encoding="utf-8"))
    out, misses = [], []

    for g in GRAPHICS:
        blk = g["block"]
        if blk not in words or blk not in offs:
            misses.append((g["id"], "block", blk))
            continue
        w, off = words[blk], offs[blk]
        try:
            t0, _ = _find(w, g["at"])
        except KeyError as e:
            misses.append((g["id"], "at", str(e)))
            continue

        rec = {k: v for k, v in g.items() if k not in ("at", "hold")}
        rec["start"] = round(off + t0, 3)

        if g["kind"] == "checklist":
            items, cursor, ok = [], t0, True
            for it in g["items"]:
                try:
                    ts, _ = _find(w, it["at"], after=cursor)
                except KeyError as e:
                    misses.append((g["id"], it.get("label", "?"), str(e)))
                    ok = False
                    break
                cursor = ts
                items.append({**{k: v for k, v in it.items() if k != "at"},
                              "at": round(off + ts, 3)})
            if not ok:
                continue
            rec["items"] = items
            last = items[-1]["at"]
        else:
            last = off + t0

        rec["end"] = round(last + g.get("hold", 3.0), 3)
        rec["durSec"] = round(rec["end"] - rec["start"], 3)
        out.append(rec)

    return {"graphics": out, "misses": misses}


def emit() -> dict:
    """Write the resolved graphics. Refuses on a miss, a repeat, or an overlap.

    ENCODING is pinned to utf-8 on both writes: `open(path, "w")` uses the
    Windows codepage, which once turned every em dash into tofu that the fonts
    were then blamed for.
    """
    r = build()
    if r["misses"]:
        raise SystemExit(f"infographics: unresolved {r['misses']}")

    kinds = [g["kind"] for g in r["graphics"]]
    dupe = {k for k in kinds if kinds.count(k) > 1}
    if dupe:
        raise SystemExit(
            f"infographics: {sorted(dupe)} used by more than one graphic. The "
            f"owner's note was 'they all look the same'; one layout per graphic "
            f"is the fix, and this is where it is enforced.")

    spans = sorted((g["start"], g["end"], g["id"]) for g in r["graphics"])
    clash = [(spans[i - 1][2], spans[i][2])
             for i in range(1, len(spans)) if spans[i][0] < spans[i - 1][1]]
    if clash:
        raise SystemExit(f"infographics: overlapping graphics {clash}")

    txt = json.dumps(r["graphics"], indent=1, ensure_ascii=False)
    for dest in (ROOT / "manifest" / "infographics.json",
                 ROOT / "remotion_cards" / "cards" / "src" / "graphics.json"):
        dest.write_text(txt, encoding="utf-8")
    return r


if __name__ == "__main__":
    res = emit()
    for g in res["graphics"]:
        print(f"  {g['id']:20s} {g['kind']:14s} {g['start']:8.1f} -> {g['end']:8.1f} "
              f"({g['durSec']:4.1f}s)")
    print(f"\n{len(res['graphics'])} full-frame graphics, "
          f"{len({g['kind'] for g in res['graphics']})} distinct layouts, 0 misses")
