"""Narration v3. One request per VO block; bites are measured, not generated.

Same stitching discipline as v2 - per-block mp3s joined later at PCM level, so
the picture is cut to real measured durations and nothing drifts.

New here: the manifest interleaves VO blocks and BITE blocks in script order,
and a bite's duration is measured off the source file rather than requested
from a model. That makes the bite the master clock for its own segment, which
is what keeps her lips in sync with her voice.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script2 import BITES, BLOCKS, VOICE_ID, VOICE_SETTINGS  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "audio2"
OUT.mkdir(exist_ok=True)
HD = ROOT / "hd"

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


def cut_bite(key: str) -> tuple[Path, float]:
    """Pull the bite's audio out of the full-length source, once."""
    vid, t0, t1, credit, text = BITES[key]
    wav = OUT / f"bite_{key}.wav"
    if not wav.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
             "-i", str(HD / f"{vid}.mp4"), "-t", f"{t1 - t0:.3f}",
             "-vn", "-ac", "2", "-ar", "48000",
             "-af", "afade=t=in:d=0.03,afade=t=out:st=%.3f:d=0.03,"
                    "loudnorm=I=-16:TP=-1.5:LRA=11" % max(0.0, t1 - t0 - 0.03),
             "-c:a", "pcm_s16le", str(wav)], check=True)
    return wav, probe_seconds(wav)


# VO text neighbours, for prosody continuity across the bites between them
VO_ORDER = [b for b in BLOCKS if b[0] == "VO"]


def main() -> None:
    ledger: list[dict] = []
    vo_i = 0
    for item in BLOCKS:
        if item[0] == "BITE":
            _, tid, key = item
            wav, secs = cut_bite(key)
            vid, t0, t1, credit, text = BITES[key]
            print(f"  {tid} BITE  {secs:7.3f}s  {vid}@{t0:.2f}  {credit}")
            ledger.append({"block": tid, "kind": "bite", "file": wav.name,
                           "seconds": secs, "bite": key, "source": vid,
                           "t0": t0, "t1": t1, "credit": credit,
                           "words": len(text.split()), "argument": text})
            continue

        _, bid, arg, text = item
        mp3 = OUT / f"{bid}.mp3"
        if mp3.exists() and mp3.stat().st_size > 20_000:
            secs = probe_seconds(mp3)
            print(f"  {bid} cached {secs:7.3f}s")
            ledger.append({"block": bid, "kind": "vo", "file": mp3.name,
                           "seconds": secs, "words": len(text.split()),
                           "argument": arg})
            vo_i += 1
            continue

        payload = {
            "text": text,
            "model_id": MODEL,
            "voice_settings": VOICE_SETTINGS,
            "previous_text": VO_ORDER[vo_i - 1][3] if vo_i > 0 else None,
            "next_text": VO_ORDER[vo_i + 1][3] if vo_i + 1 < len(VO_ORDER) else None,
        }
        for attempt in range(4):
            r = requests.post(
                URL, params={"output_format": FMT},
                headers={"xi-api-key": KEY, "Content-Type": "application/json"},
                json=payload, timeout=300)
            if r.status_code == 200:
                break
            print(f"  {bid} HTTP {r.status_code} attempt {attempt+1}: {r.text[:180]}")
            time.sleep(4 * (attempt + 1))
        else:
            raise SystemExit(f"{bid} failed after 4 attempts")

        mp3.write_bytes(r.content)
        secs = probe_seconds(mp3)
        print(f"  {bid} {secs:7.3f}s  {len(text.split()):>4}w  "
              f"{len(text.split())/secs*60:5.1f} wpm")
        ledger.append({"block": bid, "kind": "vo", "file": mp3.name,
                       "seconds": secs, "words": len(text.split()),
                       "argument": arg})
        vo_i += 1

    total = sum(x["seconds"] for x in ledger)
    vo = sum(x["seconds"] for x in ledger if x["kind"] == "vo")
    bite = total - vo
    print(f"\nTOTAL {total:.3f}s = {int(total)//60}:{total%60:05.2f}")
    print(f"  narrator {vo:7.2f}s  ({vo/total*100:.0f}%)")
    print(f"  her      {bite:7.2f}s  ({bite/total*100:.0f}%)")
    (ROOT / "manifest" / "audio2.json").write_text(
        json.dumps({"blocks": ledger, "total_seconds": total,
                    "voice": VOICE_ID, "model": MODEL}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
