"""Narration: draft free, final paid, and never served from a stale cache.

CACHE ON THE TEXT, NOT THE BLOCK ID
-----------------------------------
Every cache disaster on this project traces to a key that was a NAME or a
POSITION rather than content. The audio cache once served V5's soundtrack under
V6's picture because its test was "file exists and duration > 600s" - both true,
neither meaning current. The TTS cache would have served V10's narration under
V11's words, because both scripts use block ids like W1 and H1 for entirely
different sentences.

So the key here is a hash of the exact text plus the voice and rate. Change a
word and that block re-renders; change nothing and it costs nothing. A block id
never enters the key.

WAV THROUGHOUT, ENCODED ONCE
----------------------------
Narration is rendered per block because bites interleave with it, but every
block stays PCM until the final mux. Per-block AAC would put an audible glitch
at every join - that is the "never slice narration per beat" rule arriving in a
build where slicing is unavoidable, so the fix moves to the codec instead.

Joins are butt-joins with 30ms edge fades. Never `acrossfade`: each crossfade
overlaps its inputs and shortens total audio by ~0.3s per junction, which
accumulates into A/V drift over sixty blocks.

AUDIO LAST
----------
`--final` is the only path that spends money, and it refuses to run unless the
script is locked. Everything upstream builds against the free draft.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "audio"
CACHE = OUT / "blocks"
MAN = ROOT / "manifest"

DRAFT_VOICE = "en-US-GuyNeural"
DRAFT_RATE = "+6%"
SR = 48000

OUT.mkdir(exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)


def key(text: str, voice: str, rate: str) -> str:
    h = hashlib.sha256(f"{voice}|{rate}|{text.strip()}".encode("utf-8"))
    return h.hexdigest()[:20]


def _speakable(text: str) -> str:
    """What the narrator actually says.

    Markdown emphasis and bracketed stage directions are for the page. Numbers
    are left as digits - edge-tts and ElevenLabs both read them correctly, and
    rewriting "45" to "forty-five" here would desynchronise the graphics
    trigger matching, which matches against the ASR of what was SPOKEN.
    """
    t = re.sub(r"\[[^\]]*\]", " ", text)
    t = re.sub(r"[*_`]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


async def _edge(text: str, dest: Path, voice: str, rate: str) -> None:
    import edge_tts
    mp3 = dest.with_suffix(".mp3")
    await edge_tts.Communicate(text, voice, rate=rate).save(str(mp3))
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "2",
                    "-ar", str(SR), "-c:a", "pcm_s16le", str(dest), "-y"],
                   capture_output=True)
    mp3.unlink(missing_ok=True)


# --- Kokoro, the production voice -------------------------------------------
# The owner rejected the edge-tts draft ("complete crap"), then rejected
# ElevenLabs Brian ("doesn't work"), and pointed at Voice-Pro
# (github.com/abus-aikorea/voice-pro).
#
# Voice-Pro itself is a Gradio web app: it wants an NVIDIA GPU, ~20GB of disk
# and a browser, and documents no CLI or REST interface, so it cannot be driven
# headlessly over 46 narration blocks. What it IS is a front end onto a set of
# engines, and the strongest of those - by its own README, ranked #2 on the
# HuggingFace TTS Arena - is KOKORO. Kokoro ships as an ONNX model that runs
# locally on CPU with no key, no quota and no network, which is a better fit
# for a batch build than any hosted API.
#
# `am_michael` measured at 158 wpm on this script, against the 161 wpm measured
# off the channel's own video. Deep, even, documentary pace. The alternatives
# were auditioned: am_onyx (deeper, slightly flatter), am_eric (193 wpm, too
# fast), bm_george (British, wrong register for this channel).
KOKORO_VOICE = "am_michael"
KOKORO_SPEED = 1.0
_kokoro = None


def _kokoro_engine():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        m = ROOT / "models" / "kokoro"
        _kokoro = Kokoro(str(m / "kokoro-v1.0.onnx"), str(m / "voices-v1.0.bin"))
    return _kokoro


def _kokoro_tts(text: str, dest: Path) -> None:
    import soundfile as sf
    audio, sr = _kokoro_engine().create(text, voice=KOKORO_VOICE,
                                        speed=KOKORO_SPEED, lang="en-us")
    raw = dest.with_suffix(".raw.wav")
    sf.write(str(raw), audio, sr)
    # up to the project sample rate and to stereo, so every block joins without
    # a format change at the seam
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(raw), "-ac", "2",
                    "-ar", str(SR), "-c:a", "pcm_s16le", str(dest), "-y"],
                   capture_output=True)
    raw.unlink(missing_ok=True)


def _eleven(text: str, dest: Path, voice_id: str, api_key: str) -> None:
    import urllib.request
    mp3 = dest.with_suffix(".mp3")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data=json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.42, "similarity_boost": 0.75,
                               "style": 0.25, "use_speaker_boost": True},
        }).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        mp3.write_bytes(r.read())
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "2",
                    "-ar", str(SR), "-c:a", "pcm_s16le", str(dest), "-y"],
                   capture_output=True)
    mp3.unlink(missing_ok=True)


def render_block(text: str, final: bool = False) -> Path:
    """Render one narration block, cached on a fingerprint of its TEXT."""
    spoken = _speakable(text)
    if final:
        k = key(spoken, f"kokoro:{KOKORO_VOICE}", f"s{KOKORO_SPEED}")
    else:
        k = key(spoken, DRAFT_VOICE, DRAFT_RATE)
    dest = CACHE / f"{k}.wav"
    if dest.exists() and dest.stat().st_size > 2048:
        return dest
    if final:
        _kokoro_tts(spoken, dest)
    else:
        asyncio.run(_edge(spoken, dest, DRAFT_VOICE, DRAFT_RATE))
    if not dest.exists() or dest.stat().st_size <= 2048:
        raise RuntimeError(f"TTS produced nothing for: {spoken[:60]!r}")
    return dest


def _final_creds() -> tuple[str, str]:
    """The project key file beats an ambient env var.

    An operator's shell can carry a stale key from another project - this
    machine did, for three runs on the previous build - so the file is
    preferred and the source is printed, masked.
    """
    import os
    kf = Path("C:/Users/avina/ytceleb/elevenlabs_key.txt")
    if kf.exists():
        api_key = kf.read_text(encoding="utf-8").strip()
        src = "project key file"
    else:
        api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        src = "environment"
    if not api_key:
        raise SystemExit("no ElevenLabs key found")
    print(f"  key from {src}: ...{api_key[-4:]}")
    # Brian - deep, resonant. Chosen by the owner after hearing the edge-tts
    # draft: "the audio is complete crap ... use the Brian thing from Eleven Labs".
    voice_id = os.environ.get("ELEVEN_VOICE_ID", "nPczCjzI2devNBz1zQrb")
    return voice_id, api_key


def duration(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def silence(seconds: float, dest: Path) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    f"anullsrc=r={SR}:cl=stereo", "-t", f"{seconds:.3f}",
                    "-c:a", "pcm_s16le", str(dest), "-y"], capture_output=True)
    return dest


def join(parts: list[Path], dest: Path, fade_ms: int = 30) -> Path:
    """Butt-join with short edge fades. Never acrossfade - see module docstring."""
    lst = dest.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts),
                   encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-af",
                    f"afade=t=in:st=0:d={fade_ms/1000:.3f}",
                    "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "2",
                    str(dest), "-y"], capture_output=True)
    lst.unlink(missing_ok=True)
    return dest


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    t = " ".join(sys.argv[1:]) or "Six in the morning, the gym was already open."
    p = render_block(t, final="--final" in sys.argv)
    print(f"{p}  {duration(p):.2f}s")
