"""Cut every on-camera bite, then PROVE the cut contains what the script claims.

The in/out points in `quotes.json` were chosen by reading a transcript, and a
transcript is an index, not the audio. An index can be wrong in two ways that both
ship silently: the window can be a second or two off, so the bite opens mid-word;
or the text can belong to a different speaker in the same room.

So this does not stop at extracting. It re-transcribes each extracted clip and
compares that against the text the script promises, word for word. A bite that
does not contain what it claims is a defect here, not a surprise at review.

This is the same discipline as reading frames instead of trusting a shot count -
see BRIEF.md section 7 - applied to audio, which is the half of the film nobody
has ever actually checked on this project.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
OUT = ROOT / "bites"
PAD = 0.35          # a beat of air either side, so a cut never clips a consonant

OUT.mkdir(exist_ok=True)

_W = re.compile(r"[^a-z0-9 ]+")


def norm(s: str) -> list[str]:
    return _W.sub(" ", s.lower()).split()


def overlap(a: list[str], b: list[str]) -> float:
    """Fraction of the CLAIMED words that actually appear in the cut."""
    if not a:
        return 0.0
    pool = list(b)
    hit = 0
    for w in a:
        if w in pool:
            pool.remove(w)
            hit += 1
    return hit / len(a)


def cut(q: dict) -> Path | None:
    src = HD / f"{q['video_id']}.mp4"
    if not src.exists():
        return None
    dest = OUT / f"{q['id']}.wav"
    t0 = max(0.0, q["in_point"] - PAD)
    dur = (q["out_point"] - q["in_point"]) + PAD * 2
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}",
         "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(dest), "-y"], capture_output=True)
    return dest if r.returncode == 0 and dest.exists() else None


def main() -> None:
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")

    quotes = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
    oncam = [q for q in quotes if q["kind"] == "on_camera"]

    rows, bad = [], []
    for q in oncam:
        wav = cut(q)
        if wav is None:
            bad.append((q["id"], "NO SOURCE / cut failed"))
            continue
        segs, _ = model.transcribe(str(wav), language="en", beam_size=1)
        heard = " ".join(s.text for s in segs).strip()
        score = overlap(norm(q["text"]), norm(heard))
        rows.append({"id": q["id"], "speaker": q["speaker"], "score": round(score, 3),
                     "dur": round(q["out_point"] - q["in_point"], 2),
                     "claimed": q["text"], "heard": heard})
        if score < 0.70:
            bad.append((q["id"], f"only {score:.0%} of the claimed words are in the cut"))
        print(f"  {q['id']:26s} {score:5.0%}  {rows[-1]['dur']:5.1f}s", flush=True)

    (ROOT / "manifest" / "bite_check.json").write_text(
        json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")

    md = ["# Bite verification", "",
          "Each on-camera bite was CUT and then re-transcribed. `heard` is what is",
          "actually in the audio; `claimed` is what the script says it is.", ""]
    for r in sorted(rows, key=lambda r: r["score"]):
        md += [f"## {r['id']} — {r['score']:.0%} ({r['speaker']}, {r['dur']}s)",
               f"**claimed:** {r['claimed']}", "", f"**heard:** {r['heard']}", ""]
    (ROOT / "qc" / "BITE_CHECK.md").write_text("\n".join(md), encoding="utf-8")

    good = sum(1 for r in rows if r["score"] >= 0.70)
    print(f"\n{good}/{len(rows)} bites verified at >=70% word overlap; "
          f"{sum(r['dur'] for r in rows)/60:.1f} min total")
    if bad:
        print("PROBLEMS:")
        for b in bad:
            print("  ", b)


if __name__ == "__main__":
    main()
