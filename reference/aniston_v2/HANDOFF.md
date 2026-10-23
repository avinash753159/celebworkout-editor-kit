# Aniston video — where things stand, and what to do next

## What this is

A Jennifer Aniston "Workout And Diet" episode for the **Celeb Workout** YouTube
channel, built in `C:/Users/avina/OneDrive/Desktop/Claude Projects/YouTube/aniston_v2`.

- **Current cut:** `JENNIFER_ANISTON_V5.mp4` (11:05, 258 shots, 1920x1080)
- **The target to match:** `REFERENCE_CelebWorkout_Aniston_309k.mp4` — the
  channel's OWN Aniston video, 309k views. Measured spec in `REFERENCE_SPEC.md`.
- **Build:** `python3 build5.py` (~12 min). Script `script4.py`, pools
  `reels5.py`, cue table `cues.py`, graphics `graphics4.py`, narration already
  rendered in `audio4/` — do NOT re-render TTS unless the script text changes.
- Copyright is NOT a concern. Use any footage or images needed.

## Read the reference before anything else

Eleven passes were spent auditing this cut against itself. The single most
useful hour was generating two contact sheets of
`REFERENCE_CelebWorkout_Aniston_309k.mp4` and reading them. It answered the
format questions immediately: anonymous stock demonstrators ARE the format,
the day card belongs over a person exercising, the pacing is bimodal, and the
channel tolerates far more foreign branding and far worse footage quality than
this build was enforcing. `qc/REF_0.jpg` and `qc/REF_1.jpg`.

## The one rule

**A number improving is not verification. Generate a contact sheet and READ the
frames before calling anything fixed.** Every defect that mattered was found by
looking, never by measuring. If you did not look, say so.

## How to check — run this every time

```
python3 depth_gen.py       # depth maps for any NEW stills (~1.5s each)
python3 cuts.py            # cut detection for any NEW source windows
python3 semantic.py        # CLIP embeddings for any NEW windows (~92ms each)
python3 build5.py          # ~25 min (GL still pass is ~11 min of it)
python3 transcript.py      # shot <-> spoken words, manifest/shot_transcript.json
python3 contact_sheet.py   # qc/sheets/S00..S21.jpg, one labelled frame per shot
```

Then READ all 22 sheets, and run the motion gates:

```
python3 -c "
from pathlib import Path; import qc_motion as q
q.report('still', q.frames_of(Path('JENNIFER_ANISTON_V5.mp4'), 366.65, 80, Path('qc/mot/x')))"
```

Gate is jerk <= 0.35 and reversals <= 2. The defect this catches scored jerk
1.203 with 74 reversals in 88 frames. Each cell carries the shot number, its time, its
source tag and the words spoken over it, so the picture and the audio can be
compared without opening the film. `/vidcheck` is the same audit as a command.
`qc/pass8/` holds the sheets for the current cut, already read.

## What was found and fixed in pass 8 (all read off frames, not scores)

| Defect in the previous cut | Fix |
|---|---|
| Full-frame foreign graphics: an Apple tv+ card x3, GMA InStyle spreads, a GMA HEAT INDEX package, an E! tabloid card, a MARCH FITNESS studio show with three men | 16 sources banned in `reels5.BANNED`, each with the shot number it reached |
| Gayle King held four frames, Lisa Kudrow six, two podcast hosts five, a Pvolve model three, Billy Crudup one | three separate causes, three separate fixes — see below |
| "Victor Kiriakis" showed John Aniston in a cardigan; "Courteney Cox" showed Aniston; "Nancy Dow" showed an empty set; "Spinning" a road bike; "The bike" a treadmill; "The bag" a pair of gloves; "Dani Coleman" an ET logo wipe | `cues.py` re-audited entry by entry against a rendered frame; 12 re-pinned, 6 added (Telly Savalas, the impact list, the opening shot) |
| LOS ANGELES / 1990 played four times, RUDOLF STEINER twice five seconds apart, LAGUARDIA twice, SHERMAN OAKS twice | labelled cards are now reachable ONLY through `cues.py`; `build5` asserts none repeats |
| Day markers were unchosen pool draws — a men's fitness TV show under TUESDAY and SUNDAY, a red-carpet step-and-repeat under FRIDAY, a facial under THURSDAY, people mid-workout under REST | seven purpose-built stills, `reels5.DAY_FOOTAGE`, pinned like the movements |
| Day-card session line was unreadable on bright stills | `graphics4.day_png` puts it on its own bar |
| Food list showed bananas under PEACHES, sweet potato under MUSHROOMS, a squash stew under SEEDS | `reels5.FOOD_PIC` maps each item name to its picture; `f_seeds` regenerated |
| A Leprechaun (1993) frame played under "when she was six" | `CsLRK1JphL4` moved out of `CHILD_SRC`; L1/L2 draw only on `ARCHIVE_TALK` |
| Four regenerated stills never reached the cut | piece fingerprints now include the still's size and mtime (`build5.still_sig`) |
| `p_diner`'s sign read "DINER DINER"; `mv_kneelingrow` showed a lunge | both regenerated and looked at |

### The three identity causes, because the obvious fix does not work

Raising `MIN_IDENTITY` from 0.35 to 0.45, which the last handoff suggested,
would have changed nothing. Gayle King's source scores 0.59–0.72 and Reese's
0.69: those numbers are Aniston's face, measured at the start of the window.
The three real causes were:

1. **The gate failed open.** 385 face-bearing candidate windows had no identity
   score and were waved through. `_has_subject` now rejects anything unproven.
2. **It tested one frame.** A shot runs ~1.6s and the source cuts inside it.
   `midcheck.py` indexes the half-grid point, and both ends must be her. This
   is what Gayle King was: all 24 of her source's windows were rendered and
   every one is Aniston.
3. **Similarity is one-sided.** Kudrow and the podcast hosts passed both ends.
   `impostors.py` builds reference embeddings for the five people the cut was
   caught showing and rejects a window that is closer to one of them than to
   her. Kudrow measures 0.079 against Aniston, so the recogniser was right all
   along and the sampling was wrong. Two long two-hander sources are banned as
   well, because an interview edit cuts between speakers faster than any
   sampling can follow.

## The picture layer, since pass 9

Motion is no longer ffmpeg `zoompan` - that filter floored the crop origin and
the crop size independently and made every shot vibrate at ~15Hz. Now:

- **stills** go through `gl/` - three.js in headless Chrome, a plane displaced
  by a monocular depth map with the camera dollying toward it. Real parallax:
  p_nycstreet renders with more than double the motion of a flat push, and the
  extra motion lands on the near railings while the vanishing point stays put.
- **clips** go through `motion.warp_clip` - a per-frame float affine warp.
- **`cuts.py`** rejects any window where the source cuts mid-shot. This took
  cut-spanning shots from 28 to 6 out of 213.
- **stabilisation is OFF.** It was measured and made things worse; see
  `stabilise.py` for the numbers.

`motion.py` holds the dials. RELIEF is the parallax/crop trade-off: the plane
must overscan by 1 + RELIEF*tan(fov/2), so 0.45 keeps 87% of the image.

## Pass 14 - the repetition fix, and four things that were quietly broken

The owner's note was "you're not using google images/youtube videos more -
several are repeated". Both halves were right and both had structural causes.

**Measured before:** 174 video shots drawn from **40 sources**, nine of which
carried 60% of the film; `qAp9lq2CT5M` alone had 22 shots. Zero photographs -
every still in the project was generated.

**After:** 194 source files (was 85), **58 distinct sources** in the cut,
heaviest source 13 shots, zero repeated-source clusters, 32 photographs
fetched (`fetch_photos.py` + `gl/img_scrape.mjs`, both new - there was no
image fetcher at all).

### 1. The bootstrap deadlock - any source added since pass 8 was invisible

`spool()` builds pools with `subject=True`, which needs an identity score.
`presence.py`, `recognise.py` and `midcheck.py` all enumerated their work FROM
THOSE POOLS. So: no score -> no window -> never scored. All 111 newly
harvested sources landed in it and produced exactly zero usable windows.

All three now enumerate from the raw source lists via
`presence.candidate_windows()`. Pools went from 912 to 7,480 windows (`life`),
152 to 3,436 (`turn`), 651 to 5,577 (`outro`).

**If you add sources, run: presence -> recognise -> midcheck -> cuts ->
semantic, in that order.**

### 2. Five bans named files that do not exist

Ids were transcribed BY EYE off small labels on the contact sheets, where
`l`, `I` and `K` are indistinguishable. A KFC advert, Vince Vaughn, a crowd
shot and a breaking-news package all stayed live - the news package became the
single heaviest source in the cut at 12 shots. `reels5` now refuses to import
if any BANNED id has no file in `hd/`. **Read ids from the data.**

### 3. The impostor references were anchored to the FILM, and rotted

`IMPOSTOR_FRAMES` are timecodes into `JENNIFER_ANISTON_V5.mp4` - a file that no
longer exists, and a timeline that has changed many times since. Rebuilt
against V6 they produced references scoring, against HER own reference:

    kudrow       +0.836      pvolve_model +0.789
    podcast      +0.650      crudup       no face at all

Three "impostors" that ARE Aniston. Had they been used, the impostor test
(reject when closer to an impostor than to her) would have rejected her own
windows wholesale. Film-time references are disabled; they must come from a
SOURCE at a fixed timecode. Only `vaughn` remains, built from
`vMuarx9iWdg@860.6` and verified by eye.

**Still owed:** kudrow, the podcast hosts and the Pvolve model need
source-based references. `iUVWGBaW1b0` being banned mitigates the Gayle King
case but not the others.

### 4. The continuity gate trusted a default, and the mid check is too short

`clear_seconds` returns 99.0 for an unmeasured window. `_fits` believed it, and
`midcheck` only samples t+1.6s - so on a **6.2 second** shot, 4.6s were never
examined. `vMuarx9iWdg@860.6` ran full-frame VINCE VAUGHN for 6.2s under "a
smoothie with protein powder, banana and blueberries", with no cut in the
window: the recogniser simply scored him 0.43 and 0.52 as her.

`_fits` now MEASURES any window not present in `cuts.json`. Note 99.0 means
both "no data" and "measured, no cut" - test membership, not the value, or
every clean window is re-measured and the build times out.

## Pass 13 (V6) - the full contact-sheet audit, and what it changed

**All 17 sheets were read for the first time.** Every earlier pass sampled.
Fifteen defects came out of it; the three below are the ones that matter.

### 1. Quote cards can sit over people who are not her - UNFIXED, most important

`W3` works: it reveals over OBJECTS - the spin bike, the treadmill, the heavy
bag, a spine model - which is the equipment the narration is naming.

`W4` and `O1` reveal over anonymous demonstrators and, before the ban, over an
InStyle video of a blonde influencer with her own name caption. The card says
"JENNIFER ANISTON TO INSTYLE" over a stranger's face and the viewer reads that
woman as Aniston.

Nothing in `build5.py` constrains what a card sits over, so this survives every
reshuffle. **The rule to enforce: a quote card may sit over objects, or over
Aniston, never over another identifiable person.**

### 2. The pipeline could not name a bad window - NOW FIXED

Two defects (a Vital Proteins advert, an ET burned-in subtitle) were each ONE
bad window inside a source carrying 20+ good shots. They could not be fixed,
because the build never recorded WHICH source second a shot came from. The only
instrument available was banning the whole source - which is why earlier passes
reached for whole-source bans so often.

- `build5.py` now writes `src_t0` on every footage shot; `transcript.py` carries
  it. 229 of 257 shots (the rest are stills, bites and cards - no window).
- `reels5.BANNED_WINDOW` declares where a foreign graphic IS, in source
  seconds. `windows()` applies the shot-length margin itself.

### 3. `ocr_sweep.py` - foreign burned-in text, mechanically

Every graphics defect found by eye was TEXT. This reads one frame per shot,
subtracts the text the film burns in itself, and reports the rest. It took the
count from 22 shots to 18, all 18 now benign.

**It does not replace looking.** It cannot see that a woman is not Aniston,
that a pose is wrong, or that a shot is pillarboxed - and it misses small
product labels on objects (it caught the Vital Proteins super but not the
bottles she holds in shots 173/174).

### Pinned windows now step off cuts automatically (`build5.clean_pin`)

A cue or MOVE/DAY pin sets vid+t0 directly and skips the continuity check that
pool windows pass through. Measuring every shot found **10 spanning a cut** -
including a Cake pin at `aNAAWzLOEKc@83.3` that was fine when its shot was 1.5s
and broke when time-based cues grew it to 3.8s.

`clean_pin(vid, t0, secs)` searches +/-30s in 0.5s steps for the nearest offset
that can hold the shot, and logs every move. Result: **10 -> 1**.

**Two traps hit while building it, both worth remembering:**

1. The first version used `reels5.clear_seconds`, which returns an optimistic
   99.0 for any window not in cuts.json. Every one of the ten "fixed" by
   stepping 0.25s onto a hole in the data. It must MEASURE - `cuts.spike()`.
2. The search started at +/-8s and reported `aZiwqY_e9ZQ@47.8 cannot hold 5.0s
   anywhere near it` while clean windows sat at 32, 34, 66, 75. Widened to 30s.

**`f8YLI3POJnM` is the one that remains** (shot 138, the MONDAY card). It is
29.3s long and has NO clean 3.5s window at any offset - it cuts too fast
throughout. It needs a different source or a shorter hold; repinning cannot fix
it.

### `clean_pin` is content-blind - always LOOK after it moves something

It only knows about cuts. Nudging THURSDAY off a cut took
`aZiwqY_e9ZQ@47.8 -> 56.3`, which is genuinely continuous - and is a tight
close-up of FEET on sliders, under a card reading "upper body and back". Every
number said clean. The picture said otherwise.

Repinned by hand to 75.0, which is clean AND shows two women in a plank on the
sliders. Candidates read off `qc/THURSDAY_OPTS.jpg`.

So: after any build that logs `~ pin`, render those shots and look at them. The
nudge fixes continuity and can quietly break meaning.

### No two consecutive shots from the same source

`Reels.best` scored purely on meaning and ignored what the previous shot used,
producing runs of 4-in-6 from one file (`CsLRK1JphL4` at shot 56,
`jHtULFrKa2g` at 215) - the self-similarity that got `dADifrjs6Og` banned in
pass 6. It now drops candidates matching `self.last_src` when anything else is
available. Non-foodlist clusters of 4+/6: **4 -> 0**. (The FRUITS/VEGETABLES
runs are the progressive food list and are correct.)

### Cue drift is FIXED, and the audit tool was lying

`word_times.py` transcribes every VO block in `audio4/` with faster-whisper
`word_timestamps=True` and writes `manifest/word_times.json` - 18 blocks,
`block -> [[word, start, end], ...]`, seconds from the start of that block.

`cues.cue_positions` now resolves a phrase to the second it is SPOKEN and
returns that as a fraction of the block. **53 of 61 cues resolve by time**;
the other 8 fall back to the old word-count estimate. Corrections reach
+/-0.088 of a block, which is more than a whole shot.

The phrase is located by matching a normalised 4-word run against the spoken
sequence, then 3, 2, 1 - whisper renders numbers and proper nouns differently
from the script ("two hundred and thirty-six", "Telly Savalas", "Dani Coleman"
all failed an exact 4-word match). Among equal candidates it takes the one
nearest the word-count estimate.

**`transcript.py` had the SAME bug**, and that matters more than the cue drift
itself. It labelled each shot with `words[a:b]` sliced in proportion to frames
- the identical "every word takes equally long" assumption. So the tool used to
verify cue placement shared the flaw of the thing it was measuring. Several
"defects" reported against it were measurement artifacts: `p_kojak` was always
on the shot that says "Telly Savalas", and the old ruler showed it one shot
late. It now labels by time too.

Verified after the change, from `word_times.json` against shot spans:

    "Nancy Dow"     spoken 68.55-69.25s   shot 28 = 63.43-69.63  still:p_dressing  OK
    "Telly"         spoken 71.91s         shot 30 = 70.93-73.53  still:p_kojak     OK
    "still known as" -                    shot 70                still:p_hairtimeline OK

Re-run `word_times.py` after any change to narration text or TTS.

### The fix for cue drift: word-level timestamps

Cue drift has been on the "still wrong" list for several passes and the cause
is now pinned down. `cues.cue_positions` returns

    frac = len(text[:i].split()) / len(words)      # cues.py:174

i.e. position by WORD COUNT through the block. `build5.main` compares that
against shot starts built from cumulative FRAME counts. Those two only agree if
every word takes the same time, and they do not - the narrator varies, and
pauses are unevenly distributed.

**The missing quantity is the duration of each word.** `faster-whisper` with
`word_timestamps=True` gives exactly that, and is already used in this repo -
it is how the JUICE bite's in/out points (70.18 -> 78.58) were set. Running it
over each VO mp3 in `audio4/` would let a cue phrase resolve to a real time
instead of a word fraction, and the drift disappears.

Compensating by re-keying the cue phrase does NOT work - see above.

### Cue pins bypass EVERY gate, and nothing measured them

A cue sets `vid, t0` directly and skips the identity gate, the impostor gate
and the cut check. That is correct for identity - "her father, John Aniston" is
supposed to show someone else - but it also meant no cue window was ever
measured for CUTS.

Worse, `cuts.py` enumerated pool windows only, and `windows()` emits every
SPREAD seconds from HEAD, so an arbitrary cue t0 was never in the set.
`clear_seconds` then returned its optimistic 99.0 "no data" default. **3 of 20
cue-pinned sources had no cut data at all.**

What that produced: shot 28 held 6.2s on `wR1SuuB-hWI@80`, a window measuring
spike 25.09 with 2.07s clear. It played John Aniston, then a different
actress, then the source's own YouTube **"WATCH NEXT" end screen**. Nothing in
the build complained.

`cuts.py` now measures every cue window (1197 windows, was ~1013). Run it after
adding or moving a cue.

**Both L1 soap sources are unusable for cue pins.** `wR1SuuB-hWI` and
`_K3cpT4-upk` are "liquid soap" recap compilations: they cut every second or
two, carry a channel watermark, joke title cards, and an end screen. Only
`_K3cpT4-upk@40` is genuinely John Aniston and even that has 2.27s clear. The
"Victor Kiriakis" and "Days of our Lives" cues were removed; those sentences
now run on the era-locked L1 pool, which IS cut-checked.

**Cue drift is real and compensating for it by re-keying the phrase does not
work.** Removing two cues removed two collision-bumps and shifted the whole
cluster one shot EARLY, so a phrase re-key that fixed a late drift then
overshot. `p_dressing` currently sits one shot early. Fixing this properly
means reworking `cue_positions`, not re-keying phrases.

Also fixed: `cuts.py`'s summary crashed with TypeError comparing a list to a
float - `spike()` returns `[ratio, clear_seconds]` and the reporter treated
each value as a scalar. It had been failing on every run.

### The one bug shape that keeps recurring: trusting that a file is current

Three separate instances this pass, all the same mistake:

| Where | Test that was wrong | What it did |
|---|---|---|
| `build_audio` | "exists and duration > 600s" | served V5's soundtrack under V6's picture for a whole build |
| `ocr_sweep.frame_for` | keyed on shot index alone | would re-read the PREVIOUS cut's frames after a rebuild |
| `probe()` | `float(r.stdout.strip())` | a 48-byte piece left by a killed build made ffprobe return "" and took the next build down with ValueError |

All three now key on content or mtime, and `probe()` reports an unreadable
file as 0.0 so the caller's `nframes(out) != fr` check re-renders it. If a
build is interrupted, nothing needs cleaning by hand any more.

### Quote cards are constrained now - `Reels._pick_safe`

`best()` takes `her_only`, set by `build5.main` whenever a card is on screen.
A clip must pass the identity gate; stills are always allowed because an
object cannot be mistaken for a person.

Two earlier attempts at this did NOT work, and the reason is worth keeping:
`best()` returns early for a still slot, for empty text, and when semantic is
not ready, and that early return went straight to `next()`, which takes
whatever is in front of the cursor. Filtering inside `best()` only covered the
semantic path. The rule now lives in `_pick_safe()` and runs before any early
return. `_pick_safe` also scans WITHOUT moving the cursor, because `next()`'s
skip-and-advance silently burns every window it steps over.

**Cue shots deliberately bypass this and should.** Shots 122 and 127 are pinned
to "bands and light weights" and to "Dani Coleman" - a piece of equipment and
her trainer. Neither is Aniston and neither should be. A checker that flags
"not her under a card" must exclude cue shots or it will report these forever;
I reported them as a defect for three rounds before reading `cues.py`.

### Fixed in pass 13

| Defect | Fix |
|---|---|
| `aZiwqY_e9ZQ` InStyle demo under the Aniston quote card | banned from pools (stays in `DEMO_CLEAN`) |
| `iUVWGBaW1b0` CBS three-hander - Gayle King full frame at 90s | banned |
| `wvO0FMjlnHo` LADbible - Witherspoon alone at 120s | banned |
| `Tk07W15MCr0` Page Six headline card | banned |
| `XYcNVESFs4Y` - all 3 of its shots branded (Critics Choice, TCM, E!) | banned |
| Vital Proteins advert; ET burned-in subtitle | window-excluded |
| "stripped the glamour off completely" over a Witherspoon two-shot | repinned to the actual Cake footage, `aNAAWzLOEKc@83.3` |
| `OVERHEAD PRESS` card over a blurry leg; `PLANK` over an upward dog | repointed to the correct stills, which were on disk unused |

### Still wrong after pass 13

1. Quote cards over non-Aniston people (see above).
2. **Three exercise cards do not depict their movement:** `hipabduction` (six
   generations failed, incl. flux-pro ultra front/rear), `padwork` (shows two
   women sparring), `deadbug` (`mv_deadbug.jpg` is a malformed two-figure
   composite). All three need REAL FOOTAGE - blocked on a Pexels/Pixabay key.
3. **`CsLRK1JphL4` supplies 7 of 16 shots** in the L3 stretch with near
   duplicates - the same self-similarity that got `dADifrjs6Og` banned in pass
   6 - and pillarboxes to hard black bars twice.
4. "Nancy Dow" still plays over a man; "Victor Kiriakis" over a blonde woman.
5. Under the subscribe ask, the picture is an anonymous backside close-up.
6. Shot 0 - the opening frame of the film - is soft and motion-blurred.
7. The Vital Proteins SHOOT still supplies shots; only the branded super is
   excluded.

## What is STILL WRONG — start here

1. **`mv_hipabduction` does not depict a standing hip abduction.** Four
   generations tried (arabesque, feet only, front view, rear view); the model
   will not produce the pose. The card currently sits over a rear view of a
   woman standing still, which reads as the start position and no longer
   contradicts the label, but it does not show the movement. Either find real
   footage or accept it.
2. **`PAD WORK` shows two women sparring in gloves, not pad work.**
3. **Corner network bugs remain** — ET, Variety, CBS, Apple tv+, hulu, DREW,
   E! — on interview and red-carpet footage. Full-frame graphics are gone. This
   was a deliberate line: a small corner bug is normal for the genre, a
   full-frame magazine spread is not. Revisit if you disagree.
4. **Some cues land one shot early.** Cue position is computed from word
   position within a block, which is close but not sample-accurate. It shows as
   e.g. `p_dressing` on "Lives. Her mother," rather than on "Nancy Dow".
5. **Shot 290 is nearly black** (`_wUC6czee2s`). The luma gate let it through.
   Still present after pass 9.
6. **Non-cue shots are now meaning-matched too**, by CLIP similarity between
   the window and the sentence spoken over it (`semantic.py`). The cue table
   still outranks it. What is NOT done: stock b-roll (blocked - needs a free
   Pexels or Pixabay key in `.env.local` as `PEXELS_KEY=`) and motion graphics
   (animated maps, kinetic stat cards), which the reference does and this cut
   does not.
7. **Nobody has WATCHED it end to end** — not the owner, not the assistant.
   Every one of the 342 shots has been read as a still, with its narration
   beside it, but that is not the same as watching it with sound.

## Costs so far

~$4.05 of image generation (food, places, movements, day markers), one
ElevenLabs narration render. Budget cap $8.

## Files worth knowing

- `cues.py` — 61 entries pinning a picture to the words that name it
- `reels5.py` — pools, bans, the identity gates, `DAY_FOOTAGE`, `MOVE_FOOTAGE`,
  `FOOD_PIC`, and the hand-verified `TRAIN_OK` whitelist
- `midcheck.py` / `impostors.py` — the two index builds behind the gates
- `transcript.py` / `contact_sheet.py` — the audit tools
- `PASSLOG.md` — full history; `REMEDIATION.md` — the failure list and gates
