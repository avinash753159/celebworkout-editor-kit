"""Does this window contain a CUT in the source?

Found by pulling one 2-second piece apart frame by frame: shot 332 of the
pass-10 cut contained FOUR different scenes - her on a mat, a smear of
motion-blurred frames at the transition, a pair of legs on a slant board, and
a torso. It reads as a glitch. There were zero decode errors in the file; the
source simply cuts inside the window and the build never asked.

This is the same blind spot that let Gayle King hold four frames, that put Jay
Leno under a card credited to Jennifer Aniston for the last 3.2s of shot 169,
and that put a full-frame ELLE cover under the Well+Good card in shot 201.

Measurement is a mean absolute frame difference on a small, fast decode. A cut
shows up as a spike far above the window's own median, so the test is relative
and does not care whether the shot is dark, bright, busy or still.

Writes manifest/cuts.json: "vid@t" -> [spike ratio, seconds clear before the
first cut].


THE DECODE BUG THAT MADE 28 SOURCES UNMEASURABLE
------------------------------------------------
For several passes this file decoded with `scale=192:-2` - height derived from
the source's aspect ratio - and then GUESSED that height back out of the byte
count, by trying a candidate list until one divided evenly:

    for cand in (108, 106, 110, 144, 96, 128, 102, 100):
        if len(buf) % (SMALL_W * cand) == 0 and ...

108 is first in that list, and for a 105-frame decode of a 4:3 source - true
height 144 - the total byte count divides by 192*108 as well (105*144 is
divisible by 108). So every 4:3 source was reshaped on 108-row boundaries out
of a 144-row stream. Frames were sliced ACROSS each other, permanently
misaligned, and "the difference between consecutive frames" was actually the
difference between two unrelated bands of the picture.

What that looks like in the data is a source with an enormous, flat median
diff and no spike that can ever reach 8x its own median. Measured before the
fix, on the two windows that shipped a hard failure:

    8Na0YrtG3AI@492.6   median 36.52/255, best ratio anywhere 1.38  -> "clear"
    jD2V79_dNuQ@25.4    median 47.25/255, best ratio anywhere 1.32  -> "clear"

and both were stored as [~1.3, 99.0], i.e. "no cut in seven seconds". After
the fix, same windows, same metric:

    8Na0YrtG3AI@492.6   median  1.79/255, ratio 21.42 at +2.80s -> cut at 2.80
    jD2V79_dNuQ@25.4    median  4.47/255, ratio 12.49 at +3.87s -> cut at 3.87

Those are the cuts to Leno and to the magazine cover.

This was NOT a property of noisy or telecined footage, though it correlated
perfectly with it: 4:3 sources are the old ones. Checked across all 112
sources in manifest/cuts.json, 21 decode to a height the guesser gets wrong
(16 at 144, 3 at 128, one 148, one 140 that divided by nothing and returned
the optimistic "no data" default), and ALL 21 are in the set of 28 sources
that had never had a single cut detected at any window.

So the height is no longer inferred. It is FORCED, the decode is square-scaled
to a fixed WxH, and a buffer that does not divide evenly is an error rather
than a guess. There is no candidate list to get wrong.


WHY THERE IS ALSO AN ABSOLUTE FLOOR
-----------------------------------
Fixing the decode is necessary and, on this corpus, sufficient - but the
ratio-only test still has the failure mode the misalignment was mistaken for.
`ratio = max_diff / median_diff` divides by the window's own median, so a
window that genuinely IS busy end to end (a handheld pan, a strobing red
carpet) hides its cuts behind its own churn, and a window that is genuinely
static gets a huge ratio out of a trivial absolute change. Both are real:
qAp9lq2CT5M@163.0 scores 48.81 off a median of 0.79.

So a cut is now EITHER a large relative spike OR a large absolute one, and
the absolute arm is what makes continuity measurable on a source whose median
is high for honest reasons. Both arms are recorded, so a later pass can see
which one fired.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "manifest" / "cuts.json"
# Must cover the LONGEST shot the cycle can produce. SHOT_CYCLE tops out at
# 6.2s since the pacing rebuild, and a 2.4s span silently stopped covering
# most of a long hold - a shot could span a cut in its last four seconds and
# nothing would have looked. This also carries the identity gate: if there is
# no cut inside a shot, the person on screen cannot change partway through it.
SPAN = 7.0
# FORCED decode size. Aspect ratio is deliberately not preserved - squashing a
# 4:3 source into 16:9 changes nothing about whether consecutive frames differ,
# and it removes the only free variable the old code had to get wrong.
SMALL_W, SMALL_H = 192, 108
FPS = 15
# A cut is a frame difference many times the window's own median. Measured
# over 1013 windows the distribution is heavily bimodal - continuous takes sit
# under 4, and anything with a cut in it lands well above 8.
MAX_SPIKE = 8.0
# ...or a frame difference large enough in absolute terms that the window's own
# median does not get a vote. Mean absolute luma difference, 0-255.
#
# CALIBRATED, on all 2761 windows re-measured with the fixed decode. The
# largest diff in a window runs p10 2.74, p25 5.81, p50 31.31, p75 55.21,
# p90 81.30. The relative arm alone, at MAX_SPIKE 8.0, flags 53% of windows -
# which reproduces the 54% this file's docstring recorded back when it was
# only ever measuring the 16:9 sources correctly, and is the evidence that the
# metric and its threshold were always sound and only the decode was broken.
# Adding this arm at 32.0 takes that to 56%: 83 further windows, each one a
# window whose own churn was hiding its cut. 24.0 and 40.0 give 57% and 56%,
# so the exact value is not load-bearing; it sits above ordinary motion and at
# or below the smallest pair of different-scene frames read by eye on
# qc/_CUT_A.jpg and qc/_CUT_B.jpg.
ABS_DIFF = 32.0

_CACHE: dict | None = None



def _scores() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(OUT.read_text()) if OUT.exists() else {}
    return _CACHE


def clear_seconds(vid: str, t: float) -> float:
    """How many seconds of CONTINUOUS source this window has before the first
    cut. 99.0 if none, or if it has not been measured.

    A single yes/no per window was the wrong shape. Over a 7-second span 54%
    of windows contain a cut, but a 1-second shot does not care about a cut at
    5.5s - only a long hold does. Storing WHEN the cut lands lets a window be
    usable for a short shot and rejected for a long one."""
    v = _scores().get(f"{vid}@{t:.2f}")
    if v is None:
        return 99.0
    return float(v[1]) if isinstance(v, list) else (99.0 if v < MAX_SPIKE else 0.0)


def is_continuous(vid: str, t: float, need: float = 2.5) -> bool:
    return clear_seconds(vid, t) >= need


def spike(vid: str, t: float):
    """(max spike ratio, seconds of clear source before the first cut).

    The height is FORCED, not inferred - see the module docstring. A decode
    whose byte count does not divide by SMALL_W*SMALL_H means ffmpeg did not
    give us what was asked for, and that is reported as unmeasurable rather
    than reshaped on a guessed stride.
    """
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", f"hd/{vid}.mp4",
         "-t", str(SPAN), "-vf", f"scale={SMALL_W}:{SMALL_H},format=gray",
         "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, cwd=str(ROOT))
    if not r.stdout:
        return [0.0, 99.0]
    buf = np.frombuffer(r.stdout, np.uint8)
    px = SMALL_W * SMALL_H
    if len(buf) % px:
        # Never guess a stride. Guessing one is the bug this file was rewritten
        # for; a wrong stride reads as "no cut anywhere, ever".
        print(f"    !! cuts: {vid}@{t:.2f} decoded {len(buf)} bytes, not a "
              f"multiple of {SMALL_W}x{SMALL_H} - UNMEASURABLE")
        return [0.0, 0.0]                # fail CLOSED: no clear seconds
    n = len(buf) // px
    if n < 4:
        return [0.0, 99.0]
    f = buf.reshape(n, px).astype(np.int16)
    d = np.abs(np.diff(f, axis=0)).mean(axis=1)
    med = float(np.median(d))
    ratio = d / max(0.35, med)
    # EITHER arm counts as a cut. The relative arm catches a cut inside a calm
    # window; the absolute arm catches one inside a window too busy for any
    # spike to stand out from its own median, which is the case the old
    # ratio-only test could not express at all.
    hits = np.nonzero((ratio >= MAX_SPIKE) | (d >= ABS_DIFF))[0]
    # diff i sits between frame i and i+1, at FPS frames per second
    clear = 99.0 if len(hits) == 0 else float(hits[0]) / FPS
    return [round(float(ratio.max()), 2), round(clear, 2)]


def main() -> None:
    import reels5 as R
    # subject=True windows for the sections about her, PLUS every window of
    # the anonymous-demo sources, which carry no identity gate by design.
    # CUE windows too. windows() only emits every SPREAD seconds from HEAD, so
    # a cue pinned at an arbitrary t0 was never measured - clear_seconds then
    # returned its optimistic 99.0 "no data" default and the cue shot was free
    # to span cuts. That is how a 6.2s shot ran John Aniston -> a different
    # actress -> the source's own YouTube "WATCH NEXT" end card, with nothing
    # in the build complaining. 3 of 20 cue sources had no cut data at all.
    import cues as C
    cue_wins = {(v, float(t)) for _, _, v, t in C.CUES
                if not str(v).startswith(("still:", "split:"))}
    wins = sorted({w for v in R.DUR if v not in R.BANNED
                   for w in R.windows(v, subject=True)}
                  | {w for v in R.DEMO_CLEAN for w in R.windows(v)}
                  | set(R.TRAIN_OK) | cue_wins)
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [w for w in wins if f"{w[0]}@{w[1]:.2f}" not in have]
    print(f"  {len(wins)} windows, {len(todo)} to measure")
    for i, (vid, t) in enumerate(todo, 1):
        have[f"{vid}@{t:.2f}"] = spike(vid, t)
        if i % 100 == 0:
            OUT.write_text(json.dumps(have), encoding="utf-8")
            print(f"    {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have), encoding="utf-8")
    # spike() returns [ratio, clear_seconds]; the summary used to compare the
    # whole list against MAX_SPIKE and died with TypeError. Older entries may
    # still be bare floats, so accept both shapes.
    v = sorted(x[0] if isinstance(x, (list, tuple)) else x for x in have.values())
    cut = sum(1 for x in v if x >= MAX_SPIKE)
    if v:
        pc = lambda q: v[min(len(v) - 1, int(len(v) * q))]
        print(f"\n  spike percentiles  50th {pc(.5):.1f}  75th {pc(.75):.1f}  "
              f"90th {pc(.9):.1f}  95th {pc(.95):.1f}  max {v[-1]:.1f}")
    print(f"  {cut} of {len(have)} windows contain a cut "
          f"({cut / max(1, len(have)) * 100:.0f}%)")


if __name__ == "__main__":
    main()
