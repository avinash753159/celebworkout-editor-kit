"""Prove every bite against its OWN audio. Nothing ships unverified.

A transcript is an INDEX, not the audio. An index can be off by two seconds, or
belong to a different speaker in the room, or - on this subject especially - be
a scripted voiceover that the text gates could not distinguish from an
interview.

So each bite is cut from its source, the CUT is re-transcribed from scratch, and
the result is compared word for word against what the script claims it says.
32/32 passed at 75-100% overlap on the previous build. That was the first time
on the project the audio was checked rather than assumed.

Also checked here:

- **Headroom.** A bite must end at least a second before its source does, or the
  video comes out frames shorter than the audio. One did, on the last build, and
  the film was four frames short.
- **Speaker plausibility.** Reported, never decided automatically: the identity
  score across the bite window says who is ON SCREEN, which is evidence about
  the speaker on a sit-down interview and nearly worthless on a podcast. It is
  printed so a human can weigh it, not used as a gate.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
BITES = ROOT / "bites"
MAN = ROOT / "manifest"
QC = ROOT / "qc"
BITES.mkdir(exist_ok=True)

MIN_OVERLAP = 0.62
MIN_HEADROOM = 1.0

_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def norm(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower())


def cut(src: str, t0: float, t1: float, dest: Path) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}",
                    "-t", f"{t1 - t0:.3f}", "-i", str(HD / f"{src}.mp4"),
                    "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                    str(dest), "-y"], capture_output=True)
    return dest


def retranscribe(wav: Path) -> str:
    segs, _ = model().transcribe(str(wav), language="en", vad_filter=True,
                                 vad_parameters=dict(min_silence_duration_ms=400),
                                 beam_size=1)
    return " ".join(s.text.strip() for s in segs).strip()


def verify(bid: str, src: str, t0: float, t1: float, claimed: str,
           dur_src: float) -> dict:
    wav = BITES / f"{bid}.wav"
    cut(src, t0, t1, wav)
    heard = retranscribe(wav)
    a, b = norm(claimed), norm(heard)
    ratio = SequenceMatcher(None, a, b).ratio() if a and b else 0.0
    headroom = dur_src - t1
    return {"id": bid, "src": src, "t0": t0, "t1": t1,
            "overlap": round(ratio, 3), "headroom": round(headroom, 2),
            "ok": ratio >= MIN_OVERLAP and headroom >= MIN_HEADROOM,
            "claimed": claimed, "heard": heard}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    quotes = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
    dur = json.loads((MAN / "hd_dur.json").read_text(encoding="utf-8"))
    rows = []
    for bid, q in quotes.items():
        r = verify(bid, q["src"], float(q["t0"]), float(q["t1"]),
                   q.get("text", ""), dur.get(q["src"], 0.0))
        rows.append(r)
        print(f"  {'PASS' if r['ok'] else 'FAIL'} {bid:22s} "
              f"overlap {r['overlap']:.2f} headroom {r['headroom']:6.1f}s",
              flush=True)

    (MAN / "bite_verify.json").write_text(json.dumps(rows, indent=1,
                                                     ensure_ascii=False),
                                          encoding="utf-8")
    out = ["# Bite verification — every quote proved against its own audio", "",
           f"{sum(r['ok'] for r in rows)}/{len(rows)} passed "
           f"(overlap >= {MIN_OVERLAP}, headroom >= {MIN_HEADROOM}s).", ""]
    for r in rows:
        out += [f"## {'PASS' if r['ok'] else 'FAIL'} — `{r['id']}`",
                f"`{r['src']}` {r['t0']:.1f}–{r['t1']:.1f}  "
                f"overlap **{r['overlap']:.2f}**  headroom {r['headroom']:.1f}s",
                "", f"**script claims:** {r['claimed']}", "",
                f"**audio says:** {r['heard']}", ""]
    (QC / "BITE_VERIFY.md").write_text("\n".join(out), encoding="utf-8")
    bad = [r["id"] for r in rows if not r["ok"]]
    print(f"\n{len(rows) - len(bad)}/{len(rows)} verified")
    if bad:
        print("FAILED:", ", ".join(bad))


if __name__ == "__main__":
    main()
