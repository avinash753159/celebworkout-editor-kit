"""What is actually IN each source, and which section may draw on it.

A clip filed as "campaign coverage" on the previous build turned out to be a
design-portfolio showreel carrying a full-frame Eminem spread, and it went to
air. The rule that came out of it - label a source by what is IN it, not by its
search-result title - is enforced here rather than remembered.

The first mock cut of this film made the case again, immediately. Drawing pool
shots from every "usable" source put **Yao Ming** and **Vanessa Bryant** at Hall
of Fame podiums under the opening narration, and **Andy Frisella** in a podcast
studio - because `jHkkaTt1OdU` is two hours of OTHER people's enshrinement
speeches and the trainer sources are studio talking heads. Every one of them
passed the crop gate, the duration gate and the no-repeat gate. Nothing was
asking what was in the frame.

So each source is sampled and scored, and gets a measured `mj_rate`: the
fraction of sampled windows where the recogniser finds Michael Jordan. That
number, not the title, decides what a source may be used for.

  mj_rich   he is in it often          -> may carry lines about him
  archive   era footage, he is rare     -> cutaways, crowds, opponents, context
  studio    a talking head who is not him -> only when that person is QUOTED
  banned    nothing usable in it

Sampling is cheap because identity is measured lazily and cached, so the cost is
paid once and shared with the picker.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import edit as E
import srcindex as SI

ROOT = Path(__file__).resolve().parent
MAN = ROOT / "manifest"
OUT = MAN / "source_class.json"

SAMPLES = 12
MJ_RICH = 0.30       # >=30% of sampled windows are him
MJ_SOME = 0.08

# Sources whose CONTENT is known to be wrong for any pool, established by eye.
HARD_BAN = {
    # two hours of other people's Hall of Fame speeches - Yao Ming, Vanessa
    # Bryant and others at a podium. Jordan's own HOF speech is a separate
    # source (XLzBMGXfK4c) and is kept.
    "jHkkaTt1OdU",
    # "Michael Jordan being a Bully", channel Hoop Hacks. Two of its runs
    # reached the bite shortlist reading like Jordan on work ethic, passed the
    # text gates, and passed word-overlap verification at 0.90 and 0.95 -
    # because the audio really does say those words. Looking at the frames
    # settled what no text or overlap check could: burned-in subtitles of the
    # exact quoted lines, a channel watermark, a game-highlight montage rather
    # than an interview, and no face detected anywhere in the window. There is
    # no real clip to play, and burned-in captions fight our own labels.
    "1oCATl-7FsI",
    # Reached the cut through a B-ROLL query, so the trainer-tier exclusion
    # (which reads the talk ledger) never saw them. Both verified by eye on
    # qc/FILM2.jpg:
    #   iTFtY6KgS58  GQ's trainer feature - Grover alone on a chair in a gym,
    #                playing under narration about Jordan, before Grover has
    #                even been introduced.
    #   ahtfxlaufBk  a modern three-way Zoom podcast, appearing under 1980s
    #                biography. Era mismatch as well as studio.
    "iTFtY6KgS58",
    "ahtfxlaufBk",
    # The 1991 Bulls episode of Oprah. Genuinely mixed - Jordan is in it, but
    # so are Oprah, her audience, Pippen and Horace Grant, and it has now put
    # the wrong face on screen in two successive cuts. Its picture value does
    # not justify a third attempt; his own words from it are unaffected,
    # because a bite plays its own clip.
    "u1_3Zt0Ij6Q",
}


def classify(vid: str, dur: float) -> dict:
    ws = E.windows(vid)
    if not ws:
        return {"class": "banned", "mj_rate": 0.0, "n": 0, "why": "no windows"}
    rnd = random.Random(f"cls|{vid}")
    pick = rnd.sample(ws, min(SAMPLES, len(ws)))
    hits = faces = 0
    for t in pick:
        s = E.identity_near(vid, t, tol=0.6)
        if s >= E.MIN_IDENTITY:
            hits += 1
        if s > -1.0:
            faces += 1
    rate = hits / len(pick)
    if vid in HARD_BAN:
        return {"class": "banned", "mj_rate": round(rate, 3), "n": len(pick),
                "why": "hard ban, verified by eye"}
    if rate >= MJ_RICH:
        c = "mj_rich"
    elif rate >= MJ_SOME:
        c = "archive"
    elif faces / len(pick) >= 0.6:
        c = "studio"          # plenty of faces, none of them his
    else:
        c = "archive"         # few faces: game wides, crowds, b-roll
    return {"class": c, "mj_rate": round(rate, 3),
            "face_rate": round(faces / len(pick), 3), "n": len(pick), "why": ""}


def load() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}


def build(force: bool = False) -> dict:
    dur = json.loads((MAN / "hd_dur.json").read_text(encoding="utf-8"))
    cls = {} if force else load()
    todo = [v for v in dur if v not in cls and SI.usable(v)]
    print(f"{len(todo)} sources to classify")
    for i, vid in enumerate(todo, 1):
        cls[vid] = classify(vid, dur[vid])
        if i % 10 == 0:
            OUT.write_text(json.dumps(cls, indent=1), encoding="utf-8")
            E._save_identity()
            print(f"  {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(cls, indent=1), encoding="utf-8")
    E._save_identity()
    return cls


def sources_for(kind: str) -> list[str]:
    cls = load()
    return sorted(v for v, c in cls.items() if c["class"] == kind)


def trainer_sources() -> set[str]:
    """Sources harvested as TRAINER speech, from the fetch ledger.

    The measured `studio` class catches most of them, but not all: a wide shot
    of Grover addressing a room has faces too small for the detector, so
    `j6ejmZRo-qM` scored as `archive` and a man in a suit presenting to a
    boardroom appeared under the opening narration of the mock cut.

    Class is measured and can be fooled by framing. Tier is recorded at fetch
    time and cannot. A trainer source appears when that trainer is being
    QUOTED, and never as pool filler.
    """
    try:
        from fetch_talk import SUBJECT_QUERIES
        led = json.loads((MAN / "fetch_talk.json").read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {k for k, v in led.items() if v.get("query") not in SUBJECT_QUERIES}


def section_pool(section: str) -> list[str]:
    """Which sources a section may draw on.

    Derived from the section NAME, so a new section in the script gets a pool
    without anybody editing a list of block ids. The previous build kept
    SECTION_POOL as a hand-maintained mapping of block ids and every new block
    was silently poolless.
    """
    deny = trainer_sources()
    rich = [v for v in sources_for("mj_rich") if v not in deny]
    arch = [v for v in sources_for("archive") if v not in deny]
    # Him first, era footage behind it. Studio talking heads are never pool
    # filler - they appear only when the person speaking is being quoted.
    return rich + arch


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cls = build(force="--force" in sys.argv)
    by = {}
    for v, c in cls.items():
        by.setdefault(c["class"], []).append((v, c["mj_rate"]))
    for k in ("mj_rich", "archive", "studio", "banned"):
        rows = sorted(by.get(k, []), key=lambda r: -r[1])
        print(f"\n{k}: {len(rows)}")
        for v, r in rows[:40]:
            print(f"   {v:14s} mj_rate {r:.2f}")


if __name__ == "__main__":
    main()
