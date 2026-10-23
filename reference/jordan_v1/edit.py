"""Which picture plays over which words.

Every rule in this file is here because its absence produced a specific defect
on the previous build. None of them is a preference.

1. NO WINDOW TWICE, AND ONE CURSOR PER SECTION
   A reel that rewinds to its start when a short source runs out replays
   identical seconds: 322 of 365 sampled frames had a near-duplicate, several
   byte-identical. Worse, building a fresh cursor per narration BLOCK restarts
   the same pool at index 0 for every block, so five biography blocks re-served
   the same opening windows - a bug that survived three rebuilds and undid every
   other repetition fix. Windows are enumerated once, shuffled per source
   (seeded on the source id, so long files are sampled throughout instead of
   only at the head), and consumed exactly once.

2. IDENTITY, NOT PRESENCE
   Face detection passes anyone with a face. Measured on this library, the
   recogniser separates Jordan (0.668) from Pippen (0.025) and Horace Grant
   (0.171) sitting on the same couch. Windows carrying a claim about him must
   clear the threshold - and CUE shots deliberately bypass it, because "the
   Pistons' Jordan Rules" is supposed to show somebody else.

3. CUES PIN THE PICTURE TO THE WORDS
   Choosing from a per-section pool means any era-appropriate clip plays under
   any era-appropriate line. That put "her father, John Aniston" over an empty
   studio and "Cake, in twenty fourteen" over the Golden Globes, with the right
   footage sitting unused in the pool. A cue forces a specific source and
   timecode onto the shot covering a specific phrase.

4. A BITE PLAYS ITS REAL CLIP
   "Video doesn't make sense with audio - put the real clip." A quotation over
   unrelated b-roll is the defect, so a bite's picture is its own source at its
   own timecode, always.

5. THE GATES MUST NOT FIRE ON CONSECUTIVE BITES
   Two bites from one interview are the same person still answering, not
   repetition. The consecutive-source and group gates skip bite-to-bite pairs
   and still bind on every pool-selected shot.

6. ONE BLOCK OF LOOKAHEAD
   Without it the last pool shot before a bite can be that bite's own source,
   so the film cuts from a clip to the same clip.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import ident
import srcindex as SI

ROOT = Path(__file__).resolve().parent
MAN = ROOT / "manifest"

MIN_IDENTITY = 0.32
SPREAD = 3.0          # seconds between candidate windows inside one source
HEAD = 4.0            # skip openings: titles, fades, channel idents
TAIL = 3.0

_dur: dict = json.loads((MAN / "hd_dur.json").read_text(encoding="utf-8"))
_IDF = MAN / "identity.json"
_idmap: dict = (json.loads(_IDF.read_text(encoding="utf-8"))
                if _IDF.exists() else {})
_ref = None
_pending = 0


def _save_identity() -> None:
    _IDF.write_text(json.dumps(_idmap), encoding="utf-8")


def identity_near(vid: str, t: float, tol: float = 3.0) -> float:
    """Best identity score near t, measured ON DEMAND. -1 means no face.

    Pre-scoring the whole library was the obvious design and the wrong one:
    30 hours at a 6-second step is 18,325 windows, ~9 hours of compute, and the
    overwhelming majority of it is spent on footage the picker will never
    consider. Scoring lazily costs a few hundred measurements instead.

    It also removes an entire class of bug. There is no pre-built index that
    can be MISSING a source, so a newly added source cannot land in the
    deadlock that hid 111 sources on the previous build - where an unscored
    window failed the identity gate, never entered the pool, and therefore was
    never scored.

    Cached by exact (source, time), so a re-run is free.
    """
    global _ref, _pending
    best = -1.0
    lo, hi = t - tol, t + tol
    for k, v in _idmap.items():
        src, _, ts = k.rpartition("@")
        if src != vid:
            continue
        try:
            tt = float(ts)
        except ValueError:
            continue
        if lo <= tt <= hi and float(v) > best:
            best = float(v)
    if best > -1.0:
        return best

    key = f"{vid}@{round(t, 1)}"
    if key in _idmap:
        return float(_idmap[key])
    if _ref is None:
        _ref = ident.build_reference()
    val = ident.score(vid, t, _ref)
    _idmap[key] = val
    _pending += 1
    if _pending % 25 == 0:
        _save_identity()
    return val


_CLS: dict | None = None
_QF = MAN / "framequal.json"
_qual: dict = json.loads(_QF.read_text(encoding="utf-8")) if _QF.exists() else {}
_qpend = 0


def _class_of(vid: str) -> str:
    global _CLS
    if _CLS is None:
        p = MAN / "source_class.json"
        _CLS = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _CLS.get(vid, {}).get("class", "archive")


def _frame_usable(vid: str, t: float) -> bool:
    """Reject frames with nothing in them.

    A channel bumper - the Model Health Show's black card with a logo - reached
    the cut under narration about his diet, because "has a valid crop box and no
    scene change" was the whole test. Near-black frames and flat single-colour
    cards both fail on mean luma and variance, which is cheap and catches
    fades, slates, idents and title cards without a special case for each.
    """
    global _qpend
    key = f"{vid}@{round(t, 1)}"
    if key in _qual:
        return bool(_qual[key])
    import cv2
    import numpy as np
    im = ident.grab(vid, t, 320)
    if im is None:
        ok = False
    else:
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        ok = bool(g.mean() >= 26 and g.std() >= 22)
    _qual[key] = ok
    _qpend += 1
    if _qpend % 40 == 0:
        _QF.write_text(json.dumps(_qual), encoding="utf-8")
    return ok


def save_quality() -> None:
    _QF.write_text(json.dumps(_qual), encoding="utf-8")


def windows(vid: str) -> list[float]:
    """Every distinct start time worth considering inside one source."""
    d = _dur.get(vid, 0.0)
    if d <= HEAD + TAIL + 2:
        return []
    out, t = [], HEAD
    while t < d - TAIL:
        out.append(round(t, 1))
        t += SPREAD
    return out


# Consumed windows, GLOBAL across every pool in the film.
#
# Per-pool `used` sets are not enough and the mock run proved it: with one Pool
# per section, `jHkkaTt1OdU@8008.0` was served to the intro AND to the workout
# section, because the two pools draw on the same underlying windows and each
# only knew about its own consumption. That is the "no window twice" rule
# defeated by exactly the same shape of bug as the per-BLOCK cursor it was
# written to prevent - the cursor moved up a level instead of going away.
#
# The rule is: enumerate every distinct window once, and consume the list once,
# for the whole film.
USED: set[tuple[str, float]] = set()

# Windows proved unusable by a gate. Kept separately from USED because they
# were never shown - they are simply not worth measuring again.
DEAD: set[tuple[str, float]] = set()

# Ceiling on how many windows one shot may MEASURE before giving up and letting
# the caller extend the previous shot. Without it a single take() can walk tens
# of thousands of windows at roughly a third of a second each, which is how a
# build spent forty minutes in shot planning and printed nothing.
MAX_TESTS = 220


def reset_used() -> None:
    USED.clear()
    DEAD.clear()


class Pool:
    """A shuffled, single-use supply of windows for one section.

    One instance per SECTION, created once and carried across every block in
    that section - never re-created per block. Consumption is recorded in the
    module-level USED registry, so two sections can never serve the same window.
    """

    def __init__(self, sources: list[str], seed: int = 7,
                 subject_only: bool = False):
        self.items: list[tuple[str, float]] = []
        for vid in sources:
            if not SI.usable(vid):
                continue
            ws = windows(vid)
            random.Random(f"{vid}|{seed}").shuffle(ws)
            self.items += [(vid, t) for t in ws]
        # interleave sources so the reel does not sit in one file
        self.items.sort(key=lambda it: (self._rank(it), it[0]))
        self.subject_only = subject_only
        self.i = 0

    @staticmethod
    def _rank(it) -> float:
        return random.Random(f"{it[0]}@{it[1]}").random()

    def _content_ok(self, vid: str, t: float) -> bool:
        """Is there a usable PICTURE here, and is it the right person?

        Two separate failures, both visible in the first cut:

        - An `mj_rich` source is rich in him, not made of him. The 1991 Bulls
          Oprah tape scored 0.50 and duly served Oprah in a crowd, the Oprah
          couch, and Scottie Pippen twice - under narration about Jordan. So a
          source that CAN show him must PROVE it per window.
        - Game footage has no detectable face at all, and demanding identity
          there would delete the best material in the film. An `archive` source
          is judged on picture quality instead.

        Both branches measure. Neither has a "no data" path that returns True.
        """
        cls = _class_of(vid)
        if cls == "mj_rich":
            # Measured at the START and again mid-window. Checking only the
            # start let the 1991 Oprah tape through twice: identity found him
            # at t, the picture cut to the host inside the next two seconds,
            # and scene detection missed the cut because two talk-show shots
            # of similar brightness do not trip a 0.35 scene score.
            if identity_near(vid, t, tol=1.0) < MIN_IDENTITY:
                return False
            if identity_near(vid, t + 1.6, tol=1.0) < MIN_IDENTITY:
                return False
            return True
        return _frame_usable(vid, t)

    def take(self, want: float, avoid: set[str], need_subject: bool,
             lookahead_src: str | None = None) -> tuple[str, float, float] | None:
        """Next unused window that satisfies the gates, or None.

        `avoid` holds sources that must not be used for this shot: the previous
        shot's source, any source that supplies a BITE, and - via
        `lookahead_src` - the source of the NEXT block, so the last pool shot
        before a bite is never that bite's own clip.
        """
        block = set(avoid) | ({lookahead_src} if lookahead_src else set())
        n = len(self.items)
        scanned = tested = 0
        while scanned < n and tested < MAX_TESTS:
            it = self.items[self.i % n]
            self.i += 1
            scanned += 1
            if it in USED or it[0] in block:
                continue
            vid, t = it
            tested += 1
            if not self._content_ok(vid, t):
                DEAD.add(it)          # never pay for this window again
                continue
            clear = SI.clear_seconds(vid, t, want)
            if clear < min(want, 1.2):
                DEAD.add(it)
                continue
            USED.add(it)
            return vid, t, min(clear, want)
        return None

    def prune(self) -> int:
        """Drop windows already proved unusable.

        Without this the picker re-walks the same rejects for every shot. The
        gate results are cached, so a re-walk is cheap per item - but there are
        tens of thousands of items and ~190 shots, and the first pass over each
        one costs an ffmpeg call. Pruning turns an O(shots x windows) scan into
        something that shrinks as the film is built.
        """
        before = len(self.items)
        self.items = [it for it in self.items if it not in DEAD and it not in USED]
        self.i = 0
        return before - len(self.items)


def load_cues() -> dict:
    p = MAN / "cues.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def bite_sources(quotes: dict) -> set[str]:
    """A source that supplies a BITE should not also be pool filler."""
    return {q["src"] for q in quotes.values() if q.get("src")}
