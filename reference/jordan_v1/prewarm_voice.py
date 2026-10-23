"""Render every narration block with the paid voice, once, ahead of the build.

Separated from the build so a network hiccup costs a retry rather than a whole
assembly, and so the spend is visible as its own step. Cached on a hash of the
TEXT, so re-running is free and a script edit re-renders only what changed.
"""
import sys, time
from pathlib import Path
import build as B, voice as V

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
blocks = [b for b in B.parse_script(Path("script.md")) if b["kind"] == "vo"]
print(f"{len(blocks)} narration blocks")
done = fresh = 0
for i, b in enumerate(blocks, 1):
    spoken = V._speakable(b["text"])
    k = V.key(spoken, f"kokoro:{V.KOKORO_VOICE}", f"s{V.KOKORO_SPEED}")
    cached = (V.CACHE / f"{k}.wav").exists()
    for attempt in range(3):
        try:
            p = V.render_block(b["text"], final=True)
            break
        except Exception as e:
            if attempt == 2:
                raise
            print(f"    retry {b['id']}: {e}", flush=True)
            time.sleep(4)
    done += 1
    fresh += (not cached)
    print(f"  [{i}/{len(blocks)}] {b['id']:5s} {V.duration(p):6.2f}s "
          f"{'cached' if cached else 'NEW'}", flush=True)
print(f"\n{done} blocks ready, {fresh} newly synthesised")
