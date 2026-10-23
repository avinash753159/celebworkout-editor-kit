"""Pair every shot with the words spoken over it.

This is the tool that finds the "the picture does not match the audio" class of
defect, and until now it was made by hand and went stale the moment the film
was rebuilt. Run it after every build.

Timing comes from the block layout in build5 - the same block_frames() the
picture pass uses - so a shot's time is the film's time, not an estimate.
Within a block the narration is spread by word count, which is close enough to
name the sentence a shot lands on.

Output: manifest/shot_transcript.json, a list of
    {i, t, dur, tag, src_t0, block, kind, says}

    src_t0 is the source in-point. Without it a defective window cannot be
    named, so it cannot be excluded - see reels5.BANNED_WINDOW.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


WORD_TIMES: dict = {}


def main() -> None:
    import build5 as B

    man = json.loads((ROOT / "manifest" / "audio5.json").read_text(encoding="utf-8"))
    shots = json.loads((ROOT / "manifest" / "shots6.json").read_text(encoding="utf-8"))
    global WORD_TIMES
    _wt = ROOT / "manifest" / "word_times5.json"
    if not _wt.exists():
        raise SystemExit("transcript: manifest/word_times5.json is missing - "
                         "the audit would label every shot by word COUNT, "
                         "which is the same bend the thing it measures had.")
    WORD_TIMES = json.loads(_wt.read_text(encoding="utf-8"))
    per = B.block_frames(man)
    fps = shots["fps"]

    # frames per block id, in film order
    blocks = [(b["block"], b.get("text", ""), n) for b, n in zip(man["blocks"], per)]
    text_of = {b: t for b, t, _ in blocks}

    out, t, i = [], 0.0, 0
    # walk the shot list, tracking position inside the block it belongs to
    by_block: dict[str, list] = {}
    for r in shots["shots"]:
        by_block.setdefault(r["block"], []).append(r)

    for r in shots["shots"]:
        blk = r["block"]
        rows = by_block[blk]
        tot = sum(x["frames"] for x in rows)
        before = 0
        for x in rows:
            if x is r:
                break
            before += x["frames"]
        words = (text_of.get(blk) or "").split()
        says = ""
        spoken = WORD_TIMES.get(blk)
        if spoken:
            # By TIME, from manifest/word_times.json. Splitting the word list
            # in proportion to frames assumes every word takes equally long -
            # the same wrong assumption that made cues drift. It made this
            # audit label shots with words they do not actually carry, so the
            # ruler had the same bend as the thing it was measuring.
            a_s = before / fps
            b_s = (before + r["frames"]) / fps
            says = " ".join(w[0] for w in spoken if a_s <= w[1] < b_s)
        if not says and words:
            a = int(len(words) * before / max(1, tot))
            b = int(len(words) * (before + r["frames"]) / max(1, tot))
            says = " ".join(words[a:max(b, a + 1)])
        out.append({"i": i, "t": round(t, 2),
                    "dur": round(r["frames"] / fps, 2),
                    "tag": r["tag"], "block": blk, "kind": r.get("kind", ""),
                    "src_t0": r.get("src_t0"),
                    "says": says})
        t += r["frames"] / fps
        i += 1

    (ROOT / "manifest" / "shot_transcript.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"  {len(out)} shots, {t:.1f}s -> manifest/shot_transcript.json")


if __name__ == "__main__":
    main()
