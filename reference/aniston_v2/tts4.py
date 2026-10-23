"""Narration v4. One request per speech block; bites measured off the source.

Same discipline as v2/v3 - per-block mp3s joined later at PCM level so the
picture is cut to measured durations and nothing drifts. The week and the food
lists are separate blocks so each day and each food category gets its own
measured duration, which is what lets the day marker and the list graphic sit
exactly over the words that name them.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script4 import BITES, VOICE_ID, VOICE_SETTINGS, all_speech  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "audio4"
OUT.mkdir(exist_ok=True)
HD = ROOT / "hd"

KEY = Path("C:/Users/avina/ytceleb/elevenlabs_key.txt").read_text(encoding="utf-8").strip()
MODEL = "eleven_multilingual_v2"
FMT = "mp3_44100_192"
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"


def probe(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def cut_bite(key: str) -> tuple[Path, float]:
    vid, t0, t1, credit, _ = BITES[key]
    wav = OUT / f"bite_{key}.wav"
    if not wav.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
             "-i", str(HD / f"{vid}.mp4"), "-t", f"{t1 - t0:.3f}",
             "-vn", "-ac", "2", "-ar", "48000",
             "-af", "afade=t=in:d=0.03,afade=t=out:st=%.3f:d=0.03,"
                    "loudnorm=I=-16:TP=-1.5:LRA=11" % max(0.0, t1 - t0 - 0.03),
             "-c:a", "pcm_s16le", str(wav)], check=True)
    return wav, probe(wav)


def main() -> None:
    speech = all_speech()
    vo_texts = [t for _, k, t in speech if k == "vo"]
    ledger, vo_i = [], 0

    for bid, kind, payload in speech:
        if kind == "bite":
            wav, secs = cut_bite(payload)
            vid, t0, t1, credit, text = BITES[payload]
            print(f"  {bid:<12} BITE {secs:6.3f}s  {credit}")
            ledger.append({"block": bid, "kind": "bite", "file": wav.name,
                           "seconds": secs, "bite": payload, "source": vid,
                           "t0": t0, "t1": t1, "credit": credit, "text": text})
            continue

        mp3 = OUT / f"{bid}.mp3"
        if mp3.exists() and mp3.stat().st_size > 12_000:
            secs = probe(mp3)
            print(f"  {bid:<12} cached {secs:6.3f}s")
            ledger.append({"block": bid, "kind": "vo", "file": mp3.name,
                           "seconds": secs, "text": payload})
            vo_i += 1
            continue

        body = {
            "text": payload,
            "model_id": MODEL,
            "voice_settings": VOICE_SETTINGS,
            "previous_text": vo_texts[vo_i - 1] if vo_i > 0 else None,
            "next_text": vo_texts[vo_i + 1] if vo_i + 1 < len(vo_texts) else None,
        }
        for attempt in range(4):
            r = requests.post(URL, params={"output_format": FMT},
                              headers={"xi-api-key": KEY,
                                       "Content-Type": "application/json"},
                              json=body, timeout=300)
            if r.status_code == 200:
                break
            print(f"  {bid} HTTP {r.status_code} try {attempt+1}: {r.text[:160]}")
            time.sleep(4 * (attempt + 1))
        else:
            raise SystemExit(f"{bid} failed after 4 attempts")

        mp3.write_bytes(r.content)
        secs = probe(mp3)
        print(f"  {bid:<12} {secs:6.3f}s  {len(payload.split()):>4}w  "
              f"{len(payload.split())/secs*60:5.1f} wpm")
        ledger.append({"block": bid, "kind": "vo", "file": mp3.name,
                       "seconds": secs, "text": payload})
        vo_i += 1

    total = sum(x["seconds"] for x in ledger)
    bite = sum(x["seconds"] for x in ledger if x["kind"] == "bite")
    print(f"\nTOTAL {total:.2f}s = {int(total)//60}:{total%60:05.2f}")
    print(f"  narrator {total-bite:7.1f}s   her {bite:6.1f}s ({bite/total*100:.0f}%)")
    (ROOT / "manifest" / "audio4.json").write_text(
        json.dumps({"blocks": ledger, "total_seconds": total,
                    "voice": VOICE_ID, "model": MODEL}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
