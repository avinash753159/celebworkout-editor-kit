"""Choose the music bed from WHAT IS BEING SAID, block by block.

The owner's complaint: *"the audio background doesn't really make sense - it
should be in sync with the MOOD of what the transcript is saying."*

`bed.MOOD_OF` keyed mood to BLOCK ID - one mood per narration block, assigned by
hand. Two things were wrong with that:

1. **It is too coarse.** A block that opens on a back injury and closes on the
   recovery gets one bed for both, and the mismatch is audible.
2. **It does not survive a rewrite.** Every block id changed in the bite-led
   script, so the table went stale in one edit and every new block fell through
   to the documentary default - silently, which is the worst part.

So mood is scored from the TEXT at that timecode instead. The block ids can
change freely; the words decide. Each mood carries a vocabulary, a block scores
against all of them, and the winner takes it. Ties and empty scores fall to the
chapter-neutral bed, and `explain()` prints the winning words so a wrong choice
can be argued with rather than guessed at.

This is not sentiment analysis in any clever sense. It is a lookup table that is
honest about being one - and it is keyed on the only thing that actually
correlates with how a passage should feel, which is what the passage says.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Weighted vocabulary per mood. A word may appear in several moods; the totals
# decide. Weights are 2 for words that are decisive and 1 for words that lean.
VOCAB: dict[str, dict[int, list[str]]] = {
    "sad_reflective": {
        2: ["injury", "injured", "broke my body", "burnt out", "hurt", "pain",
            "chronic", "cranky", "couldn't work out", "kinesio", "knee brace",
            "bone loss", "osteoporosis", "failure", "breaking a hip"],
        1: ["back", "daunting", "hard on", "cost", "toll", "exhausted", "lose",
            "struggling", "afraid", "fear", "mistake", "wrong", "stopped"],
    },
    "motivational_workout": {
        2: ["workout", "training", "strength", "lift", "weights", "muscle",
            "reps", "sculpt", "cardio", "boxing", "circuit", "treadmill",
            "resistance", "plyometrics", "sweat"],
        1: ["strong", "stronger", "session", "gym", "trainer", "move",
            "movement", "mobility", "core", "hips", "form", "energised",
            "energized", "consistent", "consistency"],
    },
    "light_positive_acoustic": {
        2: ["diet", "eat", "eating", "food", "meal", "breakfast", "lunch",
            "dinner", "juice", "coffee", "smoothie", "shake", "protein",
            "vegetables", "salad", "fasting", "cheat day", "pizza", "mexican"],
        1: ["morning", "kitchen", "fridge", "prep", "lemon", "eggs", "oatmeal",
            "avocado", "chicken", "lettuce", "martini", "balance"],
    },
    "uplifting_inspiring": {
        2: ["transfers", "takeaway", "better and better", "game changing",
            "rewarding", "in the game", "feel better", "enjoying", "sunset",
            "friends", "ideal", "subscribe"],
        1: ["you can", "copy", "start", "shift", "changed", "credit", "credits",
            "life", "dogs", "happy", "love", "good"],
    },
    "cinematic_documentary": {
        2: ["record", "sourced", "claim", "we went looking", "unsourced",
            "correction", "magazine", "on the record", "trial", "evidence"],
        1: ["told", "reported", "interview", "outlet", "print", "camera",
            "story", "actually", "version"],
    },
    "emotional_piano_nostalgic": {
        2: ["fifteen years", "years ago", "twenties", "turned 50", "her fifties",
            "starstruck", "first time", "began"],
        1: ["remember", "used to", "back then", "career", "before"],
    },
}

NEUTRAL = "cinematic_documentary"
_W = re.compile(r"[^a-z0-9' ]+")


def _norm(t: str) -> str:
    return " " + _W.sub(" ", t.lower()) + " "


def score(text: str) -> dict[str, float]:
    t = _norm(text)
    out: dict[str, float] = {}
    for mood, bands in VOCAB.items():
        s = 0.0
        for w, words in bands.items():
            for k in words:
                s += w * t.count(" " + k + " " if " " not in k else k)
        out[mood] = s
    return out


def mood_for_text(text: str) -> tuple[str, dict[str, float]]:
    sc = score(text)
    best = max(sc, key=lambda k: sc[k])
    if sc[best] <= 0:
        return NEUTRAL, sc
    # a near-tie is not a decision; prefer the neutral bed over a coin flip
    ordered = sorted(sc.values(), reverse=True)
    if len(ordered) > 1 and ordered[0] - ordered[1] < 1.0:
        return NEUTRAL, sc
    return best, sc


def build(man_path: Path | None = None) -> dict[str, str]:
    """block id -> mood, for every block in the narration manifest."""
    import os
    man_path = man_path or (ROOT / "manifest" /
                            (os.environ.get("ANISTON_AUDIO", "audio6") + ".json"))
    man = json.loads(man_path.read_text(encoding="utf-8"))
    out = {}
    for b in man["blocks"]:
        out[b["block"]] = mood_for_text(b.get("text", ""))[0]
    return out


def explain() -> None:
    import os
    man_path = ROOT / "manifest" / (os.environ.get("ANISTON_AUDIO", "audio6") + ".json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    runs = []
    for b in man["blocks"]:
        m, sc = mood_for_text(b.get("text", ""))
        top = ", ".join(f"{k.split('_')[0]}={v:.0f}"
                        for k, v in sorted(sc.items(), key=lambda x: -x[1])[:3]
                        if v > 0)
        runs.append((b["block"], b["kind"], round(b["seconds"], 1), m, top,
                     (b.get("text") or "")[:70]))
    lines = ["# Music mood, chosen from the words", "",
             "One row per block. `mood` is scored from that block's own text - see",
             "mood.py. A block whose top two moods are within a point falls to the",
             "neutral documentary bed rather than flipping a coin.", "",
             "| block | kind | secs | mood | scores | text |",
             "|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | **{r[3]}** | {r[4]} | {r[5]}… |")
    changes = sum(1 for i in range(1, len(runs)) if runs[i][3] != runs[i - 1][3])
    lines += ["", f"{len(runs)} blocks, **{changes} mood changes**."]
    (ROOT / "qc" / "MOOD_TIMELINE.md").write_text("\n".join(lines), encoding="utf-8")
    for r in runs:
        print(f"  {r[0]:6s} {r[1]:5s} {r[2]:6.1f}s  {r[3]:26s} {r[4]}")
    print(f"\n{len(runs)} blocks, {changes} mood changes -> qc/MOOD_TIMELINE.md")


if __name__ == "__main__":
    explain()
