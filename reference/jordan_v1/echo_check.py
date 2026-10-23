"""Does the narrator say a thing the recorded voice is about to say?

The owner's rule: *"If the narrator's not providing value, you don't need the
narrator."* Narration that restates a bite is the clearest case of that - the
viewer hears the same claim twice, once from somebody with no authority to make
it and once from the person who was there.

This compares each narration block against the bite immediately before and after
it, on content words, and reports overlap. Every hit is a blocker, not a
suggestion: either the narration is rewritten to set the bite up rather than
summarise it, or it is deleted.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import build as B

ROOT = Path(__file__).resolve().parent

STOP = set("""a an the and or but if then than that this those these of to in on
for with from by as at is are was were be been being it its it's he she they
him her his their them we you i not no do does did have has had will would can
could should about into over out up down so very just more most much many one
two also which who whom whose what when where why how there here all any some
each every other another such own same too only own said says say get got go
goes going make makes made take takes took come comes came know knows knew
think thinks thought like likes liked""".split())


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", s.lower())
            if w not in STOP and len(w) > 3}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    blocks = B.parse_script(ROOT / "script.md")
    quotes = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))

    rows = []
    for i, b in enumerate(blocks):
        if b["kind"] != "vo":
            continue
        vw = words(b["text"])
        if not vw:
            continue
        for j in (i - 1, i + 1):
            if not (0 <= j < len(blocks)) or blocks[j]["kind"] != "bite":
                continue
            q = quotes.get(blocks[j].get("quote"), {})
            bw = words(q.get("text", ""))
            if not bw:
                continue
            shared = vw & bw
            score = len(shared) / max(1, min(len(vw), len(bw)))
            if score >= 0.20:
                rows.append({"vo": b["id"], "bite": blocks[j].get("quote"),
                             "score": round(score, 2),
                             "shared": sorted(shared)})

    rows.sort(key=lambda r: -r["score"])
    out = ["# Echo check — narration restating a bite", "",
           "The owner's rule: if the narrator is not providing value, cut the",
           "narrator. Every hit here is a blocker.", ""]
    if not rows:
        out.append("**No narration block overlaps an adjacent bite above 0.20.**")
    for r in rows:
        out += [f"## `{r['vo']}` vs bite `{r['bite']}` — overlap {r['score']}",
                f"shared: {', '.join(r['shared'])}", ""]
    (ROOT / "qc" / "ECHO_CHECK.md").write_text("\n".join(out), encoding="utf-8")
    print(f"{len(rows)} echo hits")
    for r in rows:
        print(f"  {r['score']:.2f}  {r['vo']:5s} vs {r['bite']:20s} "
              f"{', '.join(r['shared'][:8])}")


if __name__ == "__main__":
    main()
