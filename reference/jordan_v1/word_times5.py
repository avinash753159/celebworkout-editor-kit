"""Word-level timings for every narration block in audio5.

Same method as word_times.py (faster-whisper, word_timestamps=True) but
pointed at audio5/manifest/audio5.json/word_times5.json so it never touches
the v4 files. Importable so tts5.py can transcribe a block immediately after
it renders, and runnable standalone to catch up any block missed:

    python3 word_times5.py            # all vo blocks, skips ones already done
    python3 word_times5.py H1 O2      # just these
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio5"
LEDGER = ROOT / "manifest" / "audio5.json"
OUT = ROOT / "manifest" / "word_times5.json"

_model = None


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _model


def load_word_times() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}


def save_word_times(have: dict) -> None:
    OUT.write_text(json.dumps(have, indent=1), encoding="utf-8")


def transcribe_block(block_id: str, mp3_path: Path, have: dict | None = None) -> list:
    """Transcribe one VO block's rendered audio and persist immediately."""
    model = get_model()
    segs, _ = model.transcribe(str(mp3_path), word_timestamps=True, vad_filter=False)
    words = []
    for s in segs:
        for w in (s.words or []):
            t = w.word.strip()
            if t:
                words.append([t, round(w.start, 3), round(w.end, 3)])
    if have is None:
        have = load_word_times()
    have[block_id] = words
    save_word_times(have)
    return words


def main() -> None:
    man = json.loads(LEDGER.read_text(encoding="utf-8"))
    want = set(sys.argv[1:])
    blocks = [b for b in man["blocks"]
              if b["kind"] == "vo" and (not want or b["block"] in want)]

    have = load_word_times()
    todo = [b for b in blocks if b["block"] not in have]
    print(f"  {len(blocks)} vo blocks, {len(todo)} to transcribe")
    if not todo:
        return

    for b in todo:
        f = AUDIO / b["file"]
        words = transcribe_block(b["block"], f, have)
        span = words[-1][2] if words else 0.0
        print(f"    {b['block']:<6} {len(words):>4} words  "
              f"{span:6.2f}s of {b['seconds']:6.2f}s", flush=True)

    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
