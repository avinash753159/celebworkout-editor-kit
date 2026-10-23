"""Transcribe every source video, so her own words can be FOUND rather than remembered.

The previous cut used five on-camera bites. Five, out of 16.5 hours of source.
They were the five somebody happened to know about; nothing had ever read the
rest. The owner's instruction is to include ALL interviews where she talks
about her health, workout and diet, and that is not possible until the library
is searchable.

Output: one JSON per source in `asr/`, holding segments with start, end and
text. Content-cached on (file size, mtime, model), so re-running is free and a
re-downloaded source re-transcribes automatically.

Model choice: `base` with int8. `small` is better on names but roughly 2.5x
slower over 16.5 hours, and what this index is for is FINDING candidate windows
- every window that survives is read and cut by hand afterwards, so a missed
capital letter costs nothing and an extra hour of compute costs the schedule.

VAD is on. Roughly a third of this library is b-roll, applause and music beds
with no speech in it at all; without VAD those minutes get hallucinated into
plausible-looking sentences, which is worse than silence because it puts words
in her mouth that were never said.

TWO THINGS THIS SCRIPT LEARNED THE HARD WAY, both about long files:

1. It runs under a wall-clock limit and gets killed. Work is therefore saved in
   SLICES: a source is cut into `SLICE_MIN` chunks, each transcribed and
   written to `asr/.part/` before the next begins. A kill loses at most one
   slice, and re-running resumes. The first version transcribed whole files and
   a 146-minute podcast consumed an entire window, was killed, and saved
   nothing - twice.

2. Sources are processed SHORTEST FIRST. Alphabetical order put that same
   146-minute file fourth, so it blocked 190 short sources behind it. Shortest
   first means the index is usable early and the giants pay their cost last.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
OUT = ROOT / "asr"
PART = OUT / ".part"
MODEL = "base"
SLICE_MIN = 8.0          # minutes of audio per resumable unit

OUT.mkdir(exist_ok=True)
PART.mkdir(exist_ok=True)

_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    return _model


def sig(p: Path) -> str:
    st = p.stat()
    return f"{st.st_size}_{int(st.st_mtime)}_{MODEL}"


def duration(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _slice_wav(v: Path, t0: float, dur: float, dest: Path) -> bool:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}",
                        "-i", str(v), "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "pcm_s16le", str(dest), "-y"], capture_output=True)
    return r.returncode == 0 and dest.exists() and dest.stat().st_size > 1024


def transcribe_source(v: Path, dur: float) -> bool:
    """Returns True when the whole source is finished and written."""
    n = max(1, int(dur / (SLICE_MIN * 60)) + (1 if dur % (SLICE_MIN * 60) > 1 else 0))
    rows: list[dict] = []
    for i in range(n):
        pf = PART / f"{v.stem}.{i:03d}.json"
        if pf.exists():
            try:
                rows += json.loads(pf.read_text(encoding="utf-8"))
                continue
            except Exception:
                pf.unlink(missing_ok=True)

        t0 = i * SLICE_MIN * 60
        span = min(SLICE_MIN * 60, dur - t0)
        if span <= 0.5:
            pf.write_text("[]", encoding="utf-8")
            continue

        wav = PART / f"{v.stem}.{i:03d}.wav"
        if not _slice_wav(v, t0, span, wav):
            pf.write_text("[]", encoding="utf-8")
            wav.unlink(missing_ok=True)
            continue
        try:
            segs, _ = model().transcribe(
                str(wav), language="en", vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500), beam_size=1)
            got = [{"t0": round(t0 + s.start, 2), "t1": round(t0 + s.end, 2),
                    "text": s.text.strip()} for s in segs if s.text.strip()]
        except Exception as e:
            print(f"      slice {i} failed: {e}", flush=True)
            got = []
        finally:
            wav.unlink(missing_ok=True)
        pf.write_text(json.dumps(got, ensure_ascii=False), encoding="utf-8")
        rows += got

    (OUT / f"{v.stem}.json").write_text(
        json.dumps({"sig": sig(v), "dur": round(dur, 2), "segments": rows},
                   ensure_ascii=False), encoding="utf-8")
    for pf in PART.glob(f"{v.stem}.*.json"):
        pf.unlink(missing_ok=True)
    return True


def main(limit: int | None = None) -> None:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    vids = sorted(HD.glob("*.mp4"))
    todo = []
    for v in vids:
        dest = OUT / f"{v.stem}.json"
        if dest.exists():
            try:
                if json.loads(dest.read_text(encoding="utf-8")).get("sig") == sig(v):
                    continue
            except Exception:
                pass
        todo.append(v)

    # shortest first: the index becomes usable early, and the handful of
    # feature-length podcasts pay their cost at the end instead of blocking
    todo = sorted(todo, key=duration)
    if limit:
        todo = todo[:limit]

    done = len(vids) - len(todo)
    print(f"{len(vids)} sources, {done} already done, {len(todo)} to go", flush=True)
    for i, v in enumerate(todo, 1):
        d = duration(v)
        transcribe_source(v, d)
        segs = len(json.loads((OUT / f"{v.stem}.json").read_text(encoding="utf-8"))["segments"])
        print(f"  [{i}/{len(todo)}] {v.stem:16s} {d/60:6.1f}min {segs:5d} segments", flush=True)


if __name__ == "__main__":
    main(limit=int(sys.argv[1]) if len(sys.argv) > 1 else None)
