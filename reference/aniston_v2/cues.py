"""Pin a picture to the WORDS that name it.

The defect this fixes, measured on an earlier cut: the narration said "her
father, John Aniston" over an empty TV studio; "LaGuardia" over a
telemarketing office; "Ferris Bueller" over a diner; "a five a.m. call time"
over a street in Paris.

Cause: shots were drawn from a per-SECTION pool, so any window in the section
could play under any sentence in it. Nouns and their pictures were unrelated.

Each entry below is (block, phrase, picture, start seconds). At build time the
phrase is located in that block's narration, converted to a TIME with
manifest/word_times5.json, and the picture is forced onto the shot covering
that moment.

TWO THINGS THAT HAVE BURNED THIS TABLE BEFORE, both still true:

* A CUE PIN BYPASSES EVERY GATE - identity, impostor, branding and cut. That
  is correct when the sentence is about somebody who is not her, and
  catastrophic otherwise: a 6.2s pin on a recap compilation once played John
  Aniston, then a different actress, then the source's own YouTube "WATCH
  NEXT" end card. build5 runs clean_pin() on every entry here, which nudges a
  pin off a cut it cannot hold, and cue_card_ok() on any that carries a quote
  card. Neither of those can tell you what is IN the picture, so every video
  pin below was rendered and looked at.

* CUES COLLIDE. Two phrases inside one shot means the second is bumped to the
  next shot, which bumps anything already there, and the drift cascades - that
  is how "Nancy Dow, was" ended up playing over a man. The narration here
  reads four-item lists fast ("running, spinning, jumping rope, the heavy
  bag" is about three seconds, one shot), so those lists get ONE pin each, not
  four. Run `python3 cues.py` to see exactly which shot and second every cue
  resolves to before trusting the layout.

THE TABLE IS FOR script.md - hook, before, injury, method, now, evidence,
diet, takeaway, close. It was keyed on L1..L5, the biography chapters, which
this script does not have; every one of those cues was dead.
"""
from __future__ import annotations

# Which narration this pipeline is built on. audio6 = the bite-led script
# (she leads, narrator bridges). Set ANISTON_AUDIO=audio5 to rebuild the
# old narration-led cut. One switch, so no run can straddle both.
import os as _os
AUDIO_DIR = _os.environ.get("ANISTON_AUDIO", "audio6")
AUDIO_MAN = AUDIO_DIR + ".json"


# (block, phrase to find, source-or-still, start seconds)
CUES = [
    # ── H1 hook ───────────────────────────────────────────────────────────
    # The opening frame is chosen, not drawn. qqipyG6bpLA@6.2 is the ONE
    # window of the Pvolve campaign that survives the live gate, and it is the
    # picture the film is promising: her, training, no caption.
    ("H1", "In twenty twenty-one", "qqipyG6bpLA", 6.2),
    ("H1", "on the set of Murder Mystery 2", "still:q_filmset", 0.0),
    ("H1", "doing harness work", "still:q_harness", 0.0),
    ("H1", "hanging off the Eiffel Tower", "still:q_eiffel", 0.0),
    ("H1", "she hurt her back", "still:q_spine", 0.0),
    # The impact list is four nouns in about three seconds - one shot. Pin the
    # LAST one only; the other three would be bumped forward onto sentences
    # they are not in.
    ("H1", "the heavy bag", "still:q_heavybag", 0.0),
    ("H1", "what she actually eats in a day", "still:f_saladplate", 0.0),

    # ── W1 before: the volume ─────────────────────────────────────────────
    # Mandy Ingber's own yoga film. Her name super runs 4.5-9.0s and is in
    # BANNED_WINDOW; 19.0 is the outdoor class, clean.
    ("W1", "Mandy Ingber", "fnTFycw2q1w", 19.0),
    ("W1", "minutes of cardio first", "still:s_treadmill", 0.0),
    ("W1", "then a yoga practice", "still:s_yogamat", 0.0),
    ("W1", "Then came boxing", "still:q_gloves", 0.0),
    ("W1", "jump rope", "still:mv_jumprope", 0.0),
    ("W1", "military press", "still:mv_overheadpress", 0.0),
    ("W1", "called boxing the longest workout", "still:mv_padwork", 0.0),

    # ── W2 before: the rule, and what it cost ─────────────────────────────
    # Keyed on "minutes of cardio", not "forty-five minutes of cardio":
    # the narrator says the numeral and the transcript writes "45", so a
    # run starting on the spelled-out number matches nothing and the cue
    # silently falls back to a word-count fraction. Every phrase in this
    # table now starts on words the TRANSCRIPT also has - run cues.py and
    # it says so out loud if one does not.
    ("W2", "minutes of cardio or I will not", "still:q_treadmill", 0.0),
    ("W2", "her physical therapist", "still:q_physio", 0.0),
    ("W2", "wrapped in kinesio tape", "still:q_kinesio", 0.0),

    # ── W3 injury ─────────────────────────────────────────────────────────
    ("W3", "Running, rope", "still:q_running", 0.0),
    ("W3", "hard spinning", "still:q_spinbike3", 0.0),

    # ── W4 method ─────────────────────────────────────────────────────────
    # s_bands, NOT q_bands. Both stills are a set of resistance bands on a
    # surface and they read as the same picture; q_bands is script5's
    # BITE_PICTURE for T4, 55 seconds later, and the first cut played the two
    # of them as an obvious repeat. Reels.TAKEN cannot catch this - neither a
    # cue pin nor a bite picture is refusable, they are both statements - so
    # the two tables have to not collide in the first place. reels5's pool
    # audit now asserts it.
    ("W4", "resistance bands, ankle bands", "still:s_bands", 0.0),
    ("W4", "light dumbbells", "still:q_dumbbells", 0.0),

    # ── W5 now: the week as it actually is ────────────────────────────────
    # cBZC-8S9b8g is the Pvolve segment Dani Coleman presents. Her name super
    # runs 14.0-18.5s and is banned as a burned-in graphic.
    # 19.0 was tried and is WRONG: the shot this cue lands on is 5.5s and the
    # source cuts at +4.73s onto Olivia Munn alone, so the last 0.8s of "her
    # trainer is Dani Coleman" would have played over a different woman.
    # clean_pin would have nudged it, but clean_pin is content-blind - it only
    # knows about cuts - so the nudge is a lottery. 31.8 is measured clear for
    # the full 7s cuts.spike can see and shows all three of them working on
    # the mats, which is what the sentence is about.
    ("W5", "Her trainer is Dani Coleman", "cBZC-8S9b8g", 31.8),
    ("W5", "three times a week", "still:s_clock", 0.0),
    ("W5", "a great deal of core work", "still:mv_plank", 0.0),
    ("W5", "and heavy weights", "still:s_dumbbell", 0.0),

    # ── W6 now: duration is the transferable part ─────────────────────────
    ("W6", "six on-demand classes", "still:q_tvwall", 0.0),
    ("W6", "of them runs fifteen minutes or less", "still:q_clockgym", 0.0),

    # ── W7 evidence ───────────────────────────────────────────────────────
    # WAS still:q_stretch, and q_stretch is not a stretch. The file is an
    # EMPTY ROOM with stacked lumber and cardboard boxes against the far wall
    # - no person, no movement, nothing being stretched - and it held four
    # seconds of the V7 cut under "twenty-one per cent better whole-body
    # flexibility, and ten per cent better balance and mobility". The name was
    # the only evidence anyone ever had for it; the picture was never looked
    # at. Read on qc/groups/QSTILLS.jpg, which is every q_* still in the
    # project at 320px, rendered for this pass precisely so the other
    # twenty-four could be checked the same way.
    #
    # Zero spend this pass, so the replacement had to already exist. All
    # sixteen stills_move/mv_* demonstrations are spent - each one is pinned
    # to its own MOVEMENT CARD and appears exactly once - so mv_catcow and
    # mv_hipopener, which do depict the thing, are not available. This is
    # Mandy Ingber's outdoor yoga class, the same source W1 cues at 19.0,
    # eleven seconds in: two women on mats going from standing through a
    # forward fold into a down dog. cuts.spike measures 4.4s clear from 11.0,
    # which covers the 4.0s this shot runs, and the span was rendered at one
    # second intervals and read (qc/groups/SCAN_fnT2.jpg) rather than
    # inferred from the first frame. Flexibility, balance and mobility, being
    # done, over a sentence about flexibility, balance and mobility.
    ("W7", "flexibility, and ten per cent better balance", "fnTFycw2q1w", 11.0),

    # ── D1 diet: the fasting window ───────────────────────────────────────
    ("D1", "Start with the fasting", "still:q_watchclock", 0.0),
    ("D1", "no food in the morning", "still:q_kitchen", 0.0),
    ("D1", "hours fasted, an eight-hour window", "still:f_clock", 0.0),

    # ── D3 diet: the morning, in order ────────────────────────────────────
    ("D3", "Juice first", "still:f_juice", 0.0),
    ("D3", "coffee roughly thirty minutes later", "still:f_coffee2", 0.0),
    ("D3", "warm lemon water on waking", "still:f_lemonwater", 0.0),
    ("D3", "avocado and eggs", "still:f_avocado", 0.0),
    ("D3", "or oatmeal with an egg white", "still:f_porridge", 0.0),
    ("D3", "banana, blueberries", "still:f_smoothie", 0.0),

    # ── D4 diet: the prep system ──────────────────────────────────────────
    ("D4", "vegetables or salad with a protein", "still:f_saladbowl", 0.0),
    ("D4", "cut raw vegetables", "still:f_cucumber", 0.0),
    ("D4", "eggs in the fridge, a big head", "still:f_eggs3", 0.0),
    # "a big head of butter lettuce" -> f_greens was here and is gone: it
    # is 1.8s after the eggs, which is inside the same shot, so it was
    # bumped forward onto "and a cooked protein such as pulled chicken" -
    # which is the next cue's own words. f_greens is texture in the diet
    # pool instead.
    ("D4", "such as pulled chicken", "still:f_chicken", 0.0),

    # ── D5 diet: the cheat day, corrected ─────────────────────────────────
    ("D5", "usually Mexican food", "still:f_mexican", 0.0),
    ("D5", "maybe Italian pasta", "still:f_lasagna", 0.0),
    ("D5", "burgers or Mexican food", "still:f_burger", 0.0),

    # ── O1 takeaway ───────────────────────────────────────────────────────
    # "the arms everybody screenshots" - a photograph of the arms, not a
    # sentence about them.
    ("O1", "the arms everybody screenshots", "still:ph_portrait94_1", 0.0),
    ("O1", "Rotation and side-to-side loading", "still:mv_hipabduction", 0.0),
    ("O1", "cut vegetables, boiled eggs", "still:q_fridge", 0.0),
]

BY_BLOCK: dict[str, list] = {}
for blk, phrase, src, t in CUES:
    BY_BLOCK.setdefault(blk, []).append((phrase, src, t))


def _norm(w: str) -> str:
    return "".join(ch for ch in w.lower() if ch.isalnum())


_WORD_TIMES = None
_BLOCK_SECS = None


def _timing():
    """Lazy-load word timings and block durations.

    word_times5.json and audio5.json, NOT the v4 pair - those are the old
    eleven-minute biography cut and are keyed on blocks (L1..L5, H2, WK_*,
    FD_*) that script.md does not contain. Loading them here would have made
    every _time_frac() call return None and silently dropped the whole table
    back onto word-count fractions, which is the drift this file exists to
    remove.
    """
    global _WORD_TIMES, _BLOCK_SECS
    if _WORD_TIMES is None:
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parent
        wt = root / "manifest" / "word_times5.json"
        am = root / "manifest" / AUDIO_MAN
        if not wt.exists():
            raise SystemExit(
                "cues: manifest/word_times5.json is missing. Cue positions "
                "would fall back to word-count fractions, which drift more "
                "than a whole shot. Run word_times5.py.")
        _WORD_TIMES = json.loads(wt.read_text(encoding="utf-8"))
        _BLOCK_SECS = {}
        for b in json.loads(am.read_text(encoding="utf-8"))["blocks"]:
            _BLOCK_SECS[b["block"]] = b["seconds"]
    return _WORD_TIMES, _BLOCK_SECS


def _time_frac(block: str, text: str, word_index: int):
    """Fraction through the block by TIME, from the spoken word timings.

    Word count is not time. The narrator's pace varies and pauses fall
    unevenly, so a word-count fraction and a frame-count fraction disagree and
    cues land a shot early or late.

    The spoken word list will not index-align with text.split() - punctuation
    and contractions differ - so the phrase's first word is located by matching
    a short normalised run against the spoken sequence.
    """
    times, secs = _timing()
    spoken = times.get(block)
    total = secs.get(block)
    if not spoken or not total:
        return None
    script = [_norm(w) for w in text.split()]
    said = [_norm(w[0]) for w in spoken]
    for n in (4, 3, 2, 1):
        run = [w for w in script[word_index:word_index + n] if w]
        if len(run) < n:
            continue
        hits = [i for i in range(len(said) - n + 1) if said[i:i + n] == run]
        if hits:
            i = min(hits, key=lambda h: abs(h - word_index))
            return min(1.0, max(0.0, spoken[i][1] / total))
    return None


def cue_positions(block: str, text: str) -> list[tuple[float, str, float]]:
    """(fraction through the block, source, start) for each cue that is
    actually present in this block's narration.

    The fraction is by TIME, from manifest/word_times5.json. A cue whose
    phrase resolves to no time at all is reported rather than silently
    estimated - a word-count fallback is how cues drifted in the first place,
    and a phrase this table cannot find is a typo in the table, not a
    timing problem.
    """
    low = text.lower()
    out = []
    for phrase, src, t in BY_BLOCK.get(block, []):
        i = low.find(phrase.lower())
        if i < 0:
            continue
        wi = len(text[:i].split())
        frac = _time_frac(block, text, wi)
        if frac is None:
            print(f"    !! cue {block} {phrase!r}: no word timing matched, "
                  f"falling back to a word-count fraction (this DRIFTS)")
            frac = wi / max(1, len(text.split()))
        out.append((frac, src, t))
    return sorted(out)


def check() -> None:
    """Every cue's phrase is in its block, and every one resolves to a TIME.

    Called by build5.main before anything is rendered. A phrase that the
    transcript cannot match still produces a picture - from a word-count
    fraction - so nothing crashes and nothing looks wrong until somebody
    notices the shot is a second and a half off the word it illustrates. Six
    of the forty-seven cues in this table were in that state when it was
    written, all of them because the narrator says "45" where the script says
    "forty-five".
    """
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent
    man = json.loads((root / "manifest" / AUDIO_MAN).read_text(encoding="utf-8"))
    text_of = {b["block"]: b.get("text", "") for b in man["blocks"]}
    bad = []
    for blk, phrase, src, t in CUES:
        txt = text_of.get(blk)
        if txt is None:
            bad.append(f"{blk}/{phrase!r}: no such block in audio5.json")
            continue
        i = txt.lower().find(phrase.lower())
        if i < 0:
            bad.append(f"{blk}/{phrase!r}: not in the narration")
            continue
        if _time_frac(blk, txt, len(txt[:i].split())) is None:
            bad.append(f"{blk}/{phrase!r}: no word timing matches - it would "
                       f"be placed by WORD COUNT, which drifts. Re-key it on "
                       f"words the transcript also has (run cues.py to see "
                       f"them).")
    if bad:
        # PRUNE, do not abort - but say exactly what was dropped.
        #
        # This table was written against the narration-led script. The bite-led
        # rewrite kept some sentences word for word and replaced others outright,
        # so a cue can now name a block that no longer exists, or a phrase the
        # narrator no longer says. Those cues are already dead: they pin a
        # picture to words nobody speaks.
        #
        # Aborting the whole build was the right behaviour while the script was
        # stable, because a broken cue degrades silently to word-count placement
        # and drifts. It is the wrong behaviour across a rewrite, where failing
        # hard only blocks every VALID cue behind the stale ones. So drop the
        # dead ones loudly and keep the rest, which passed the same three tests.
        keep = [c for c in CUES
                if not any(b.startswith(f"{c[0]}/{c[1]!r}") for b in bad)]
        print(f"cues: dropping {len(CUES) - len(keep)} stale cues from the "
              f"previous script; {len(keep)} still resolve")
        for line in bad:
            print(f"    dropped  {line}")
        CUES[:] = keep


def _report() -> None:
    """Resolve every cue against the real shot layout and print it.

    This is the artefact section 4 has to hand back: block, phrase, the second
    it is spoken according to word_times5.json, the shot it lands on, and
    whether a collision bumped it. Run it before every build.
    """
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent
    import build5 as B

    man = json.loads((root / "manifest" / AUDIO_MAN).read_text(encoding="utf-8"))
    per = B.block_frames(man)
    text_of = {b["block"]: b.get("text", "") for b in man["blocks"]}
    secs_of = {b["block"]: b["seconds"] for b in man["blocks"]}

    phase = 0
    found, missing = 0, []
    print(f"{'blk':<4} {'phrase':<38} {'says@':>7} {'shot':>5} {'shot@':>7} "
          f"{'len':>5}  picture")
    for b, total in zip(man["blocks"], per):
        bid = b["block"]
        if b["kind"] == "bite":
            phase += 1
            continue
        cuts_all = B.carve(total, phase)
        starts, acc = [], 0
        for fr in cuts_all:
            starts.append(acc / max(1, total))
            acc += fr
        cue_for = {}
        for frac, src, t0c in cue_positions(bid, text_of[bid]):
            k = max(0, min(len(cuts_all) - 1,
                           max(i for i, st in enumerate(starts) if st <= frac)))
            bumped = ""
            while k in cue_for and k + 1 < len(cuts_all):
                k += 1
                bumped = " BUMPED"
            cue_for[k] = (src, t0c, frac, bumped)
        for k in sorted(cue_for):
            src, t0c, frac, bumped = cue_for[k]
            phrase = next(p for p, s, t in BY_BLOCK[bid]
                          if s == src and abs(t - t0c) < 1e-6)
            t_says = frac * secs_of[bid]
            t_shot = sum(cuts_all[:k]) / B.FPS
            print(f"{bid:<4} {phrase[:38]:<38} {t_says:>7.2f} {k:>5} "
                  f"{t_shot:>7.2f} {cuts_all[k]/B.FPS:>5.2f}  "
                  f"{src}@{t0c}{bumped}")
            found += 1
        phase += len(cuts_all)

    for blk, phrase, src, t in CUES:
        txt = text_of.get(blk, "")
        if phrase.lower() not in txt.lower():
            missing.append((blk, phrase))
    print()
    for blk, phrase in missing:
        print(f"  NOT FOUND  {blk}: {phrase!r}")
    print(f"\n{found} cues placed, {len(missing)} phrases not in the narration")


if __name__ == "__main__":
    _report()
