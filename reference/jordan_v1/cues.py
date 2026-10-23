"""Pin the picture to the WORDS.

The owner, 28 Aug: *"whenever it mentions other players like Scotty Pippen or
whoever it is, you need to have pictures of them. Also when you're talking about
his childhood and all that stuff, it needs to be a picture of him as a kid...
Why is it that you're using the footage when you should really be using him as a
kid?"*

That is the cue problem, exactly. Choosing shots from a per-section pool means
any era-appropriate clip plays under any era-appropriate line, so "Scottie
Pippen came, Ron Harper came" ran over anonymous game footage while a photograph
of Pippen sat unused. On the Aniston build the same defect put "her father, John
Aniston" over an empty studio.

A cue forces a specific picture onto a specific block. Cues are exempt from the
identity gate by design: a picture of Dean Smith is SUPPOSED to be somebody
other than the subject.

Ordering inside a block is by position in the list, so a block that names three
people shows three people in the order the narration says them.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT / "photos"

# block id -> ordered list of picture slugs (files in photos/)
#
# Each entry answers a sentence the pool cannot: a name, a childhood, or a body
# that the narration is explicitly describing.
CUES: dict[str, list[str]] = {
    # --- who he was, before any of it. Photographs, not game footage: the
    #     narration is talking about a boy in Wilmington and a college
    #     freshman, and a clip of him in a Bulls jersey is the wrong picture.
    "R1": ["mj_young1", "mj_young2"],         # born, Wilmington, cut from varsity
    "R2": ["mj_young2", "mj_young1"],         # grew four inches, the back garden
    "R3": ["dean_smith", "mj_young1"],        # North Carolina under Dean Smith
    "R4": ["mj_skinny2", "mj_dunk87"],        # Rookie of the Year, 63 points
    # --- the body the whole film turns on ---
    "R6": ["mj_skinny", "mj_skinny2"],        # 195 pounds, knocked to the floor
    "T5": ["mj_skinny", "mj_built"],          # about fifteen pounds of muscle
    "W15": ["mj_built2"],                     # what the programme actually built
    # --- the trainer ---
    "T1": ["tim_grover_b"],                   # "a young trainer named Tim Grover"
    "T3": ["tim_grover_a"],                   # most of those letters never opened
    # --- the Breakfast Club, named man by man ---
    "W1": ["scottie_pippen", "ron_harper"],   # Pippen came. Harper came.
    # --- the result ---
    "S2": ["mj_dunk87"],                      # 1991, swept Detroit
}


def available() -> dict[str, Path]:
    return {p.stem: p for p in PHOTOS.glob("*.jpg")}


def resolved() -> dict[str, list[Path]]:
    """Cues whose picture actually exists on disk.

    A cue naming a missing file is dropped and reported, never silently skipped:
    47 cue pins survived a script rewrite on the previous build, pointing at
    blocks and phrases that no longer existed.
    """
    have = available()
    out: dict[str, list[Path]] = {}
    missing: list[str] = []
    for block, slugs in CUES.items():
        paths = []
        for s in slugs:
            if s in have:
                paths.append(have[s])
            else:
                missing.append(f"{block}:{s}")
        if paths:
            out[block] = paths
    if missing:
        print(f"  cues with no picture on disk: {', '.join(missing)}")
    return out


def check_against_script(script: Path) -> list[str]:
    """Every cue must name a block that still exists."""
    ids = set()
    for line in script.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            ids.add(line[4:].split("|")[0].strip())
    return sorted(b for b in CUES if b not in ids)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    stale = check_against_script(ROOT / "script.md")
    r = resolved()
    print(f"{sum(len(v) for v in r.values())} cue pictures across {len(r)} blocks")
    for b, ps in r.items():
        print(f"  {b:5s} {', '.join(p.stem for p in ps)}")
    if stale:
        raise SystemExit(f"cues point at blocks that no longer exist: {stale}")
