"""Build an .srt from the narration, and chapter markers from the sections.

F12. The narration text exists verbatim in the audio manifest and the block
boundaries are already frame-exact, so captions are close to free - and a
10-minute video with five clear sections should ship chapters too.

Timing within a block is apportioned by word count, which is accurate enough
for reading: the narrator's rate is near-constant at 161 wpm.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAXCHARS = 84            # two lines of ~42


def ts(t: float) -> str:
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def chunk(text: str, limit: int = MAXCHARS):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > limit and cur:
            out.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def main():
    import build5
    man = json.loads((ROOT / "manifest" / "audio4.json").read_text())
    blocks = man["blocks"]

    cues, t = [], 0.0
    for i, b in enumerate(blocks):
        dur = b["seconds"]
        text = b.get("text") or b.get("argument") or ""
        if b["kind"] == "bite":
            text = b.get("text", "")
        if text.strip():
            parts = chunk(text)
            total_w = sum(len(p.split()) for p in parts) or 1
            ct = t
            for p in parts:
                share = len(p.split()) / total_w * dur
                cues.append((ct, ct + share, p, b["kind"] == "bite"))
                ct += share
        t += dur + (build5.gap_after(b["block"]) if i < len(blocks) - 1 else 0.0)

    srt = []
    for n, (a, bb, txt, is_bite) in enumerate(cues, 1):
        body = f"[Jennifer Aniston] {txt}" if is_bite else txt
        srt.append(f"{n}\n{ts(a)} --> {ts(bb)}\n{body}\n")
    (ROOT / "JENNIFER_ANISTON_V5.srt").write_text("\n".join(srt), encoding="utf-8")

    # chapters from the section a block belongs to
    from script4 import BLOCKS
    sec_of = {b[1]: b[2] for b in BLOCKS if b[0] == "VO"}
    label = {"hook": "Intro", "subscribe": None, "life": "Her Life",
             "turn": "The Injury That Changed Everything",
             "workout_intro": "The Workout", "week_intro": None, "week": None,
             "diet_intro": "The Diet", "diet": None, "outro": "The Takeaway"}
    chapters, seen, t = [], set(), 0.0
    for i, b in enumerate(blocks):
        sec = sec_of.get(b["block"])
        name = label.get(sec)
        if name and name not in seen:
            chapters.append((t, name)); seen.add(name)
        t += b["seconds"] + (build5.gap_after(b["block"]) if i < len(blocks) - 1 else 0.0)
    if chapters and chapters[0][0] > 0:
        chapters.insert(0, (0.0, "Intro"))
    lines = [f"{int(a)//60:02d}:{int(a)%60:02d} {n}" for a, n in chapters]
    (ROOT / "CHAPTERS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"  {len(cues)} caption cues -> JENNIFER_ANISTON_V5.srt")
    print("  chapters:")
    for l in lines:
        print("   ", l)


if __name__ == "__main__":
    main()
