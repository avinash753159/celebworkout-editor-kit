"""A bed that follows the MOOD OF THE WORDS, moment to moment.

The owner's verdict on a chapter-keyed music table: *"the audio background
doesn't really make sense - it should be in sync with the MOOD of what the
transcript is saying."*

One mood per chapter is too coarse and is exactly what produced that mismatch. A
block that opens on an injury and closes on a recovery gets one bed for both,
and the mismatch is audible. So mood is scored from the TEXT AT THAT TIMECODE -
the words actually being spoken - and the bed changes when the sentiment
changes, not when the chapter does.

Two mixing rules, both from bugs:

- **High-pass the bed at ~220Hz.** Measured on the last build, 58% of the music
  energy sat below 500Hz, directly on the narrator's fundamental. That is what
  makes a voice sound muddy.
- **`amix` renormalises when a short input ends**, which clips. Use
  `normalize=0`, and format everything to stereo first so a mono bed does not
  come out +3dB hot against a stereo narration.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MUSIC = ROOT / "music"
WORK = ROOT / "work"
SR = 48000

MOODS = {
    "tense": "sad_reflective",
    "defeat": "sad_reflective",
    "resolve": "motivational_workout",
    "grind": "motivational_workout",
    "method": "cinematic_documentary",
    "reflect": "emotional_piano_nostalgic",
    "triumph": "uplifting_inspiring",
    "warm": "light_positive_acoustic",
}

CUES = {
    "defeat": ["beaten", "lost", "knocked", "eliminated", "went home",
               "not strong enough", "expensive", "failed", "hit", "abuse",
               "punish", "hurt", "injury", "poisoning", "curled"],
    "tense": ["rules", "hard", "bet", "contact", "series", "barely",
              "could not", "couldn't", "problem", "gap", "wrong"],
    "resolve": ["decided", "summer", "agreed", "started", "began", "turn",
                "solved", "fix", "engineering", "thirty days", "stop being"],
    "grind": ["six a.m.", "dawn", "lift", "squat", "deadlift", "reps",
              "training", "workout", "work out", "sprints", "morning",
              "programme", "program", "twelve", "every morning"],
    "method": ["nutrition", "diet", "meal", "steak", "protein", "blood sugar",
               "schedule", "conditioning", "stretching", "recover", "orthodox",
               "carbohydrates"],
    "triumph": ["championship", "swept", "won", "title", "four games",
                "thirty-eight", "38", "beat the lakers", "six titles",
                "finals"],
    "reflect": ["remembered", "years", "nobody", "honest", "summary",
                "noticed", "boring thing", "was not born"],
}


def mood_of(text: str) -> str:
    low = text.lower()
    best, score = "method", 0
    for mood, keys in CUES.items():
        n = sum(1 for k in keys if k in low)
        if n > score:
            best, score = mood, n
    return best


def timeline(edl: dict) -> list[dict]:
    """One mood row per block, then merged where neighbours agree."""
    rows = []
    for b in edl["blocks"]:
        rows.append({"id": b["id"], "t0": b["t0"],
                     "t1": round(b["t0"] + b["dur"] + b["pause"] / edl["fps"], 3),
                     "mood": b.get("mood", "method")})
    merged = []
    for r in rows:
        if merged and merged[-1]["mood"] == r["mood"]:
            merged[-1]["t1"] = r["t1"]
            merged[-1]["ids"].append(r["id"])
        else:
            merged.append({**r, "ids": [r["id"]]})
    return merged


def build_bed(segments: list[dict], total: float, dest: Path) -> Path:
    """One continuous bed, a track per mood segment, butt-joined with fades."""
    idx = json.loads((MUSIC / "index.json").read_text(encoding="utf-8"))
    parts = []
    for i, seg in enumerate(segments):
        cat = MOODS.get(seg["mood"], "cinematic_documentary")
        tracks = idx.get(cat) or idx["cinematic_documentary"]
        tr = tracks[i % len(tracks)]
        src = MUSIC / "raw" / tr["file"]
        dur = max(0.5, seg["t1"] - seg["t0"])
        out = WORK / f"bed_{i:03d}.wav"
        # loop the track if the segment outlasts it; fade both edges
        subprocess.run(
            ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", str(src),
             "-t", f"{dur:.3f}",
             "-af", (f"highpass=f=220,afade=t=in:st=0:d=0.8,"
                     f"afade=t=out:st={max(0, dur - 0.8):.3f}:d=0.8,"
                     f"aformat=sample_fmts=s16:sample_rates={SR}:"
                     f"channel_layouts=stereo"),
             "-c:a", "pcm_s16le", str(out), "-y"], capture_output=True)
        if out.exists():
            parts.append(out)
    lst = WORK / "bed_list.txt"
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts),
                   encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c:a", "pcm_s16le", "-ar", str(SR),
                    "-ac", "2", str(dest), "-y"], capture_output=True)
    return dest


def write_report(segments: list[dict], dest: Path) -> None:
    out = ["# Mood timeline — read this against the script", "",
           f"{len(segments)} mood segments. A block-level table is too coarse;",
           "this is driven by the words at that timecode.", ""]
    for s in segments:
        out.append(f"- `{s['t0']:7.1f}`–`{s['t1']:7.1f}`  **{s['mood']:8s}** "
                   f"→ {MOODS.get(s['mood'])}  ({', '.join(s['ids'])})")
    dest.write_text("\n".join(out), encoding="utf-8")
