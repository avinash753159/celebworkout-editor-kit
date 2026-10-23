"""Narration. One ElevenLabs request per block, stitched for prosody continuity.

Per-block generation is what lets the picture be cut to real measured audio
durations instead of estimates, so nothing drifts. The blocks are joined later
at PCM level and encoded ONCE - decoding each mp3 and butt-joining samples,
never concatenating encoded frames, which puts an audible click at every join.

`previous_text` / `next_text` are passed so the model knows where a block sits
in the paragraph and does not reset its intonation at every boundary.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script import BLOCKS, VOICE_ID, VOICE_SETTINGS  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "audio"
OUT.mkdir(exist_ok=True)

KEY = Path("C:/Users/avina/ytceleb/elevenlabs_key.txt").read_text(encoding="utf-8").strip()
MODEL = "eleven_multilingual_v2"
FMT = "mp3_44100_192"

URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"


def probe_seconds(p: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(p)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main() -> None:
    ledger: list[dict] = []
    for i, (bid, arg, text) in enumerate(BLOCKS):
        mp3 = OUT / f"{bid}.mp3"
        if mp3.exists() and mp3.stat().st_size > 20_000:
            secs = probe_seconds(mp3)
            print(f"  {bid} cached {secs:7.3f}s")
            ledger.append({"block": bid, "file": mp3.name, "seconds": secs,
                           "words": len(text.split()), "argument": arg})
            continue

        payload = {
            "text": text,
            "model_id": MODEL,
            "voice_settings": VOICE_SETTINGS,
            "previous_text": BLOCKS[i - 1][2] if i > 0 else None,
            "next_text": BLOCKS[i + 1][2] if i + 1 < len(BLOCKS) else None,
        }
        for attempt in range(4):
            r = requests.post(
                URL, params={"output_format": FMT},
                headers={"xi-api-key": KEY, "Content-Type": "application/json"},
                json=payload, timeout=300)
            if r.status_code == 200:
                break
            print(f"  {bid} HTTP {r.status_code} attempt {attempt+1}: {r.text[:200]}")
            time.sleep(4 * (attempt + 1))
        else:
            raise SystemExit(f"{bid} failed after 4 attempts")

        mp3.write_bytes(r.content)
        secs = probe_seconds(mp3)
        wpm = len(text.split()) / secs * 60
        print(f"  {bid} {secs:7.3f}s  {len(text.split()):>4}w  {wpm:5.1f} wpm  "
              f"{len(r.content)/1024:6.1f} kB")
        ledger.append({"block": bid, "file": mp3.name, "seconds": secs,
                       "words": len(text.split()), "argument": arg})

    total = sum(x["seconds"] for x in ledger)
    words = sum(x["words"] for x in ledger)
    print(f"\nTOTAL {total:.3f}s  = {int(total)//60}:{total%60:05.2f}   "
          f"{words} words   {words/total*60:.1f} wpm")
    (ROOT / "manifest" / "audio.json").write_text(
        json.dumps({"blocks": ledger, "total_seconds": total,
                    "voice": VOICE_ID, "model": MODEL}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
