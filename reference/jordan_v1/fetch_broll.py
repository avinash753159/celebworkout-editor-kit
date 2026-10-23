"""Harvest PICTURE - him training, and the era around it.

`fetch_talk.py` went looking for speech and deliberately rejected full games and
highlight packages, because a 103-minute broadcast costs 20 minutes of
transcription to return commentary by Marv Albert. That was correct for that
job and is wrong for this one.

The brief is explicit: "Too many interview videos - it should be her working out
if possible." For this subject that means the weight room, the six a.m.
sessions, practice, training camp and in-game conditioning - not podium press
conferences, of which the speech harvest already has plenty.

So this fetch inverts the filter: full games and practice footage are WANTED,
and talking-head interviews are not (we have them). Everything else that was
learned about downloading still applies - stale `.part` files, permissive format
chain, ledger by id.

These sources are NOT transcribed. They are picture, they enter the shot pools,
and they still have to pass the identity gate before they can carry a line.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from fetch_talk import WRONG_SUBJECT, download, existing_ids, search

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
MAN = ROOT / "manifest"
LEDGER = MAN / "fetch_broll.json"
POOL = MAN / "broll_pool.json"

MAX_MIN = 45.0
MIN_MIN = 0.5

QUERIES: list[tuple[str, int]] = [
    # --- the weight room and the work itself: the brief's first preference ---
    ("Michael Jordan weight room workout Bulls", 12),
    ("Michael Jordan lifting weights training footage", 12),
    ("Chicago Bulls practice footage 1990s Jordan", 12),
    ("Michael Jordan training camp Bulls 1995 1996", 10),
    ("Michael Jordan shootaround practice drills", 10),
    ("Bulls Breakfast Club workout footage Jordan", 8),
    ("Michael Jordan offseason training 1991", 8),
    ("Michael Jordan conditioning drills basketball", 8),
    # --- the era, for cutaways and context ---
    ("Michael Jordan 1991 NBA Finals highlights", 8),
    ("Michael Jordan 1996 Bulls 72-10 season", 8),
    ("Michael Jordan flu game 1997 footage", 8),
    ("Michael Jordan dunk highlights 1988 1990", 8),
    ("Michael Jordan Pistons Bad Boys physical play", 8),
    ("Michael Jordan Nike commercial 1990s", 8),
    ("Chicago Bulls 1990s locker room behind the scenes", 8),
    ("Michael Jordan Last Dance documentary training scenes", 8),
]

# Talking heads - the speech harvest already covers these and the brief wants
# less of them, not more.
TALKING_HEAD = re.compile(
    r"\binterview\b|\bpodcast\b|press\s+conference|sit\s*down|"
    r"\bepisode\s*\d+|full\s+speech|\btalks?\s+about\b",
    re.I,
)

# Modern re-edits and AI slop. A 4K-remastered highlight reel with a synth
# score is not 1991 footage, and reads wrong next to genuine archive.
MODERN_EDIT = re.compile(
    r"\b4k\b|remaster|\bai\b\s|\bedit\b|\bfree\s+clips?\b|no\s+copyright|"
    r"green\s+screen|\bmix\b|tribute|\bfan\s*made\b|reaction",
    re.I,
)


def reject(title: str) -> str | None:
    if WRONG_SUBJECT.search(title):
        return "wrong-subject"
    if TALKING_HEAD.search(title):
        return "talking-head"
    if MODERN_EDIT.search(title):
        return "modern-edit"
    return None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    MAN.mkdir(exist_ok=True)
    dry = "--dry" in sys.argv
    budget = next((int(a) for a in sys.argv[1:] if a.isdigit()), 34)

    have = existing_ids()
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    pool: dict[str, dict] = {}
    dropped: list[dict] = []

    for q, n in QUERIES:
        for c in search(q, n):
            if c["id"] in pool or c["id"] in have or ledger.get(c["id"], {}).get("ok"):
                continue
            why = reject(c["title"])
            if why:
                dropped.append({**c, "why": why})
                continue
            if not (MIN_MIN <= c["dur"] <= MAX_MIN):
                dropped.append({**c, "why": "duration"})
                continue
            pool[c["id"]] = c
        print(f"  {q[:52]:54s} pool {len(pool)}", flush=True)

    cands = sorted(pool.values(), key=lambda c: -c["dur"])
    POOL.write_text(json.dumps({"pool": cands, "dropped": dropped}, indent=1,
                               ensure_ascii=False), encoding="utf-8")
    take = cands[:budget]
    print(f"\n{len(cands)} candidates, {len(dropped)} dropped; "
          f"taking {len(take)} ({sum(c['dur'] for c in take):.0f} min)")

    if dry:
        for c in take:
            print(f"  {c['dur']:6.1f}min {c['id']} {c['channel'][:20]:22s} "
                  f"{c['title'][:58]}")
        print("\n--dry: nothing downloaded")
        return

    got = 0
    for i, c in enumerate(take, 1):
        ok = download(c["id"], 1080)
        ledger[c["id"]] = {**c, "ok": ok, "kind": "broll"}
        LEDGER.write_text(json.dumps(ledger, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        got += ok
        print(f"  [{i}/{len(take)}] {'OK  ' if ok else 'FAIL'} {c['dur']:6.1f}min "
              f"{c['id']} {c['title'][:52]}", flush=True)
    print(f"\ndownloaded {got}/{len(take)}")


if __name__ == "__main__":
    main()
