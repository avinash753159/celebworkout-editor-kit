"""Music bed, cut to the film's emotional beats.

Replaces `score.build`, which synthesised one four-chord loop and ran it for
eleven minutes under everything. That loop was written to dodge Content-ID, and
it worked, but the owner's verdict on the result was that it was "so bad for the
audio". The fix is not a better synth - it is real library music that CHANGES
with the story.

Licensing: every track is Pixabay Content License - free for commercial and
YouTube use, no attribution required, not Content-ID claimed. So the property
score.py was hand-built to guarantee is kept, and we stop paying for it with a
synth loop.

Mapping is by BLOCK ID, not by section tag, because the tags do not split where
the chapters do: W1-W5 are all tagged "turn" but span both the injury and the
workout, which want opposite music.

To swap a track, change one index in MOOD_TRACK. Nothing else needs touching.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

# Which narration this pipeline is built on. audio6 = the bite-led script
# (she leads, narrator bridges). Set ANISTON_AUDIO=audio5 to rebuild the
# old narration-led cut. One switch, so no run can straddle both.
import os as _os
AUDIO_DIR = _os.environ.get("ANISTON_AUDIO", "audio6")
AUDIO_MAN = AUDIO_DIR + ".json"


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "music" / "raw"
SR = 48_000

# Which mood underscores which block.
#
# Rewritten for script.md. The previous table named H2, L1-L5, T6 and T7 -
# the subscribe ask, five biography chapters and two bites that no longer
# exist - and had no entry at all for W6, W7, D5 or D6, which therefore fell
# through mood_for()'s default and ran the hook's music under the clinical
# trial and the collagen. A missing key here is silent; that is why the
# assertion below exists.
MOOD_OF = {
    "H1": "cinematic_documentary",        # the hook: the injury, and a promise
    "W1": "motivational_workout",         # fifteen years of training hard
    "T1": "motivational_workout",         # her own voice on the old routine
    "W2": "sad_reflective",               # the burnout and the taped Barbie
    "T2": "sad_reflective",               # "past 40 it's not as easy"
    "W3": "sad_reflective",               # what the injury took off the menu
    "T3": "sad_reflective",               # the injury, in her voice
    "W4": "motivational_workout",         # Pvolve - the recovery begins
    "T4": "motivational_workout",
    "W5": "motivational_workout",         # the week as it is now
    "W6": "motivational_workout",         # fifteen minutes
    "W7": "cinematic_documentary",        # the trial: sober, not a workout
    "D1": "light_positive_acoustic",      # the diet
    "D2": "light_positive_acoustic",
    "T5": "light_positive_acoustic",      # her voice, juice before coffee
    "D3": "light_positive_acoustic",
    "D4": "light_positive_acoustic",
    "D5": "light_positive_acoustic",
    "D6": "light_positive_acoustic",
    "O1": "uplifting_inspiring",          # the takeaway
    "O2": "uplifting_inspiring",          # the close
}
# the generated blocks (the week, the food lists) follow their chapter
PREFIX_MOOD = {"WK_": "motivational_workout", "FD_": "light_positive_acoustic"}

# Which track within each mood. Indices are into music/index.json.
MOOD_TRACK = {
    "cinematic_documentary": 0,
    "emotional_piano_nostalgic": 0,
    "sad_reflective": 0,
    "motivational_workout": 0,
    "light_positive_acoustic": 0,
    "uplifting_inspiring": 0,
}

XF = 2.0        # crossfade between two moods, seconds
LOOP_XF = 1.5   # crossfade where a track wraps to cover a long chapter


_TEXT_MOOD: dict | None = None


def _text_mood() -> dict:
    """block -> mood, scored from that block's own narration text."""
    global _TEXT_MOOD
    if _TEXT_MOOD is None:
        import mood as _m
        _TEXT_MOOD = _m.build()
    return _TEXT_MOOD


def check() -> None:
    """Every block in the film has a mood. A default is not a choice.

    Mood now comes from mood.py, which scores the WORDS. That satisfies the
    owner's note - "it should be in sync with the MOOD of what the transcript is
    saying" - and it also means this check can no longer go stale: a renamed or
    added block is scored like any other rather than falling through MOOD_OF.
    """
    m = _text_mood()
    man = json.loads((ROOT / "manifest" / AUDIO_MAN).read_text(encoding="utf-8"))
    missing = [b["block"] for b in man["blocks"] if b["block"] not in m]
    if missing:
        raise SystemExit(f"bed: mood.build() returned nothing for {missing}")
    return


def _check_legacy() -> None:
    """The old block-table check, kept for ANISTON_AUDIO=audio5 rebuilds."""
    import json
    from pathlib import Path
    man = json.loads((ROOT / "manifest" / AUDIO_MAN).read_text(encoding="utf-8"))
    ids = [b["block"] for b in man["blocks"]]
    missing = [b for b in ids if b not in MOOD_OF]
    if missing:
        raise SystemExit(f"bed: no mood for {missing}. mood_for() would give "
                         f"them the documentary bed by default and nothing "
                         f"would say so.")
    extra = [b for b in MOOD_OF if b not in ids]
    if extra:
        raise SystemExit(f"bed: MOOD_OF names blocks the film does not have: "
                         f"{extra}")


def mood_for(block: str) -> str:
    # The WORDS decide. MOOD_OF survives only as an explicit override for a
    # block the vocabulary gets wrong; it is consulted second, not first.
    m = _text_mood()
    if block in m:
        return m[block]
    if block in MOOD_OF:
        return MOOD_OF[block]
    for p, m in PREFIX_MOOD.items():
        if block.startswith(p):
            return m
    return "cinematic_documentary"


def _decode(p: Path) -> np.ndarray:
    """mp3 -> float32 stereo at SR, via ffmpeg (no extra dependency)."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le",
         "-ar", str(SR), "-ac", "2", "-"],
        capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()


_cache: dict[str, np.ndarray] = {}


def _track(mood: str) -> np.ndarray:
    if mood not in _cache:
        idx = json.loads((ROOT / "music" / "index.json").read_text(encoding="utf-8"))
        items = idx[mood]
        a = _decode(RAW / items[MOOD_TRACK[mood] % len(items)]["file"])
        # every track normalised to the same peak, so a mood change reads as a
        # change of music and not a change of level
        pk = float(np.max(np.abs(a))) or 1.0
        _cache[mood] = (a / pk * 0.5).astype(np.float32)
    return _cache[mood]


def _fill(mood: str, n: int) -> np.ndarray:
    """n samples of `mood`. A track shorter than the chapter is wrapped by
    overlap-add, so the seam is a 1.5s crossfade rather than a hard restart."""
    a = _track(mood)
    if len(a) >= n:
        return a[:n].copy()
    xf = max(1, min(int(LOOP_XF * SR), len(a) // 4))
    fin = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
    out = np.zeros((n, 2), np.float32)
    pos = 0
    while pos < n:
        take = min(len(a), n - pos)
        chunk = a[:take].copy()
        if pos > 0 and take >= xf:
            chunk[:xf] *= fin                    # fade this copy in ...
        if pos + take < n and take >= xf:
            chunk[take - xf:] *= fin[::-1]       # ... and the last one out
        out[pos:pos + take] += chunk
        if take < len(a):
            break
        pos += len(a) - xf                       # step back by the overlap
    return out


def build_for(runs: list[tuple[str, int]]) -> np.ndarray:
    """runs = [(block_id, n_samples), ...] in play order; a gap inherits the
    mood of the block before it. Returns float32 (N, 2)."""
    total = sum(n for _, n in runs)
    out = np.zeros((total, 2), np.float32)

    # collapse consecutive runs sharing a mood into one span
    spans: list[list] = []
    pos = 0
    for blk, n in runs:
        m = mood_for(blk)
        if spans and spans[-1][0] == m:
            spans[-1][2] += n
        else:
            spans.append([m, pos, n])
        pos += n

    xf = int(XF * SR)
    fin = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
    for i, (m, start, n) in enumerate(spans):
        last = i + 1 == len(spans)
        # a span renders xf longer than it owns and overlaps the next one, so
        # the handover is a true crossfade and neither track restarts mid-fade
        ln = n if last else n + xf
        seg = _fill(m, ln)
        if i:
            seg[:xf] *= fin
        if not last:
            seg[ln - xf:] *= fin[::-1]
        end = min(total, start + ln)
        out[start:end] += seg[:end - start]

    head = min(int(3.0 * SR), total)
    out[:head] *= np.linspace(0, 1, head, dtype=np.float32)[:, None]
    tail = min(int(3.0 * SR), total)
    out[-tail:] *= np.linspace(1, 0, tail, dtype=np.float32)[:, None]
    pk = float(np.max(np.abs(out))) or 1.0
    return (out / pk * 0.42).astype(np.float32)
