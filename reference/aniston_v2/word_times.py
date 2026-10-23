"""Word-level timings for every narration block.

Why: `cues.cue_positions` locates a cue phrase by WORD COUNT through the block

    frac = len(text[:i].split()) / len(words)

and `build5.main` compares that against shot starts built from cumulative
FRAME counts. Those two only agree if every word takes the same time. They do
not - the narrator's pace varies and pauses are unevenly distributed - so cues
land a shot early or late, and a collision between two cues in one long shot
cascades onto the next.

The missing quantity is the duration of each word. faster-whisper gives it
directly, and it is already trusted in this repo: the JUICE bite's in/out
points (70.18 -> 78.58) were set from exactly this.

Writes manifest/word_times.json:  block -> [[word, start, end], ...]
Times are seconds from the START OF THAT BLOCK, which is what cue_positions
needs; build5 already knows where each block begins.

    python3 word_times.py            # all blocks, skips ones already done
    python3 word_times.py L1 L4      # just these
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio4"
OUT = ROOT / "manifest" / "word_times.json"


def main() -> None:
    man = json.loads((ROOT / "manifest" / "audio4.json").read_text(encoding="utf-8"))
    want = set(sys.argv[1:])
    blocks = [b for b in man["blocks"]
              if b["kind"] == "vo" and (not want or b["block"] in want)]

    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [b for b in blocks if b["block"] not in have]
    print(f"  {len(blocks)} vo blocks, {len(todo)} to transcribe")
    if not todo:
        return

    from faster_whisper import WhisperModel
    model = WhisperModel("base.en", device="cpu", compute_type="int8")

    for b in todo:
        f = AUDIO / b["file"]
        segs, _ = model.transcribe(str(f), word_timestamps=True, vad_filter=False)
        words = []
        for s in segs:
            for w in (s.words or []):
                t = w.word.strip()
                if t:
                    words.append([t, round(w.start, 3), round(w.end, 3)])
        have[b["block"]] = words
        OUT.write_text(json.dumps(have), encoding="utf-8")
        span = words[-1][2] if words else 0.0
        print(f"    {b['block']:<6} {len(words):>4} words  "
              f"{span:6.2f}s of {b['seconds']:6.2f}s", flush=True)

    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
