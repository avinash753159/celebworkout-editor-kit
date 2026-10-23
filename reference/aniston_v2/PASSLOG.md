# Pass log — autonomous run

Target: `REFERENCE_CelebWorkout_Aniston_309k.mp4`. Standard: a number improving
is not verification; a contact sheet must be read.

---

## Pass 1 — Presence, identity and branding

**Built a presence index** over 8,887 candidate windows (face detected, face
size, face count). Result: **26% of all candidate windows contain no face at
all.** Those are now excluded from any section whose narration is about her.

**Detection turned out to be insufficient — and the contact sheet proved it.**
The rebuild still carried a full-frame magazine portrait of **Eminem**, plus
Lisa Kudrow, a makeup artist and an unnamed actor. All passed the gate because
they have faces. Traced the Eminem shot to `w2X4wxwB-qQ`, which I had labelled
"campaign coverage" off its search title; it is a design-portfolio showreel
featuring several celebrities. Banned.

**So I built face RECOGNITION.** Downloaded YuNet + SFace, made a reference
embedding of Aniston from 13 frames verified by eye in earlier passes, and
scored 6,230 face-bearing windows by cosine similarity. The separation is wide
and independently correct:

| Source | Median identity | Who it actually is |
|---|---|---|
| `wR1SuuB-hWI` | **+0.002** | her father, John Aniston |
| `hxWPeK2YHLw` | +0.104 | the Vanity Fair cast panel |
| `ZoqjGormrds` | +0.143 | Lisa Kudrow |
| `qAp9lq2CT5M` | **+0.749** | her, to camera |
| `K3puGMuBWKw` | +0.739 | her, Drew Barrymore Show |

**Only 45% of face-bearing windows are actually her.** Gate set at 0.35.

**Branding:** wrote an automatic title-card detector, then checked it by eye —
it flagged 70% of the Friends compilation, all ordinary footage. **Scrapped
it** and replaced it with head/tail exclusions, which is what actually holds.
That cut the exclusion from 1,989s of false positives to 154s of real cards.

## Pass 2 — Exercises

Extracted and looked at all 17 pinned frames. **2 of 17 were correct.** Full
audit in `MOVE_REVIEW.md`: BANDED GLUTE BRIDGE was three women standing;
OVERHEAD PRESS was a man under a caption reading "LATERAL DELTOID RAISE".

Generated a picture for every movement, looked at them, regenerated the three
that were wrong (plank came back as a downward dog, cat-cow as a seated
backbend), and re-pinned. **15 of 17 now on verified pictures**; the two
correct video pins kept.

## Pass 3 — Material

Fetched the awards material the narration names and never showed: SAG
acceptance speech, Golden Globe speeches, the 2002 Emmy win, childhood
photographs. Banned two at 320×240 (6× upscale). Also fixed the reason 25
minutes of Friends yielded four shots: `interleave` walked every source from
its head, so a cursor stopping at 100 shots never saw past the first minutes.
Windows are now shuffled deterministically per source, sampling the whole
runtime.

## Pass 4 — Polish

- **Music**: measured the bed — 58% of its energy sat below 500Hz, on the
  narrator's fundamental. Added an FFT high-pass at 220Hz; low-end share now
  30%. First time this file has ever been analysed.
- **Opening**: the first shot is now chosen for the largest verified face
  (27% of frame) instead of opening on a leg and a foot.
- **Exposure**: extended matching to stills and cards, which had been bypassing
  it entirely (28% of runtime).

## Pass 5 — Publish

Captions (`.srt`, 131 cues, her bites marked), chapter markers, description,
final metadata, thumbnail regenerated.

---

## Measured result

| | V4 | V5 mid-run | **Final** |
|---|---|---|---|
| Identical frame pairs | 47 | 19 | **15** |
| Near-identical pairs | 90 | 23 | **23** |
| Brightness stdev | 41.8 | 35.6 | **31.9** |
| Hard cuts >55 levels | 90 | 92 | **61** |
| Dark frames | 16 orig | 7 | **4** (incl. the 6s endcard) |
| Distinct on-screen elements | 92 | 122 | **146** |

Contact sheets read: 48 frames across the full film. **23 of 24 frames in the
first half contain Jennifer Aniston**, against a V5 sample where hosts,
co-stars and strangers held frame repeatedly.

## Still wrong

1. **Gayle King holds one frame** (~0:50). Her window scored above the identity
   threshold — a false positive. The gate is good, not perfect.
2. **Nobody has watched it end to end, including me.** Everything above is
   contact sheets and measurement.
3. Exercise demos still use stock people where the channel format permits it —
   correct for the format, but worth knowing.
4. Music is high-passed but still a synthesised bed, not library tracks.
5. `voC2DxCL6jQ` appears 16 times — the most repeated single source.

## What I would do next

Raise the identity threshold to ~0.45 and re-check what it costs in pool size;
that would likely remove the Gayle King frame. Then watch the film.

---

## Pass 6 — Picture/narration alignment (added after review)

**The defect:** the picture had no relationship to the sentence being spoken.
Shots were drawn from a per-SECTION pool, so any life-era window could play
under any life-era line. Measured on the previous cut:

| Narration said | Picture showed |
|---|---|
| "Her father, **John Aniston**" | an empty TV studio |
| "the **Rudolf Steiner School**" | a 1970s Los Angeles street |
| "**LaGuardia** High School" | a telemarketing office |
| "**Ferris Bueller**" | a diner |
| "**Friends** ran from September 1994" | a 2014 Cake interview |
| "**Cake**, in twenty fourteen" | the Golden Globes |
| "a five a.m. **call time**" | a street in Paris |

I had his soap footage, the actual Ferris Bueller pilot, Friends and the Cake
trailer sitting in the pools, landing nowhere near the words that name them.

**The fix:** `cues.py` — 57 entries binding a phrase to a picture. At build time
the phrase is located in the block's narration by word position, converted to a
time, and the picture forced onto the shot covering that moment. The identity
gate is bypassed for cue shots, because some sentences are ABOUT other people:
"her father, John Aniston" should show John Aniston.

**Verified: 46 of 57 cues land on their words (81%).** The misses are adjacent
cues competing for the same 1.6s shot. Checked by eye at 18 cue moments — her
father's soap under his name, the labelled Steiner School and LaGuardia, the
Ferris Bueller pilot, an empty restaurant under "waited tables", Ross under
"Friends", Rachel at the purple door under "played Rachel Green", the SAG speech
under "Screen Actors Guild award", eggs on avocado toast under "eggs with
avocado", green juice under "celery juice", frozen yogurt under "frozen yogurt".

## Final deliverables

- `JENNIFER_ANISTON_V5.mp4` — 11:05, 365 shots, 347 MB
- `JENNIFER_ANISTON_V5.srt` — 131 cues
- `CHAPTERS.txt`, `METADATA_FINAL.md`, `THUMBNAIL_V4.png`

## Still wrong

1. 11 of 57 cues drift to a neighbouring shot when two cues compete.
2. Gayle King and Robin Roberts each hold a frame — identity false positives.
3. **Nobody has watched it end to end, including me.**
4. Music is high-passed but still synthesised.

---

## Pass 7 — vertical shots, and era-locked pools

**Pillarboxing.** A vertical portrait was padded to black two seconds into the
film — a narrow strip with huge bars either side. The fitter padded anything
under 1.3:1. Replaced with a blurred, zoomed copy of the same frame behind the
sharp version, so the frame is always full 16:9.

**Era-blind biography.** With `shot_transcript.json` — every shot against the
words spoken over it — the remaining problem was exact: cues landed correctly,
but the shots BETWEEN cues came from one "life" pool spanning 1969 to 2024.

| Narration | Was showing |
|---|---|
| "Jennifer Joanna Aniston was **born**" | the 1990 Ferris Bueller pilot |
| "**Days of our Lives**" | the Friends set |
| "moved to New York when she was **six**" | the Friends set |
| "still at **Waldorf**" | her 2020 SAG acceptance speech |
| "she **moved to Los Angeles**" | the Golden Globes |

Split the biography into five era-locked pools (`life_L1`..`life_L5`), each
drawing only on its own decade. Verified against the transcript afterwards:
John Aniston under his own name three times, Sherman Oaks under "Sherman Oaks",
the Steiner School and LaGuardia under their names, a 1990s studio under "moved
to Los Angeles".

**`/celebvid` skill updated** (297 -> 400 lines) so none of this is relearned:
the channel-is-the-spec reversal with the measured table, the verify-by-eye
rule, the four gates (identity not presence; cue the words; no window twice
with one cursor per section; never pillarbox), source hygiene, the exercise
audit, audio pauses and the music high-pass, and grade matching including
stills.

---

## Pass 8 — the picture against the audio, all 342 shots

Method: build, `transcript.py`, `contact_sheet.py`, then read all 22 sheets.
Every claim below was read off a frame. Three build cycles.

### Round 1 — audit of the V5 cut (342 shots + all 57 cues read)

Cue table, 57 entries rendered and compared with their phrase:
7 wrong (`Victor Kiriakis` = a duplicate of the John Aniston interview frame,
`Courteney Cox` = Aniston, `Nancy Dow` = an empty living-room set, `Spinning` =
a road bike, `The bike` = a treadmill, `The bag` = gloves, `Dani Coleman` = an
ET logo wipe with a joke subtitle), 6 weak, 1 phrase uncued that named a person
(Telly Savalas).

Film, 342 shots:
- full-frame foreign graphics at shots 20, 130, 144, 156, 161, 173, 176, 183,
  189, 195, 221, 222, 223, 329
- wrong person at 26, 194, 196, 216, 237, 241, 243, 280, 285, 287, 294, 298,
  302, 309, 336, 339, 343, 346
- labelled place cards repeated: LOS ANGELES x4, RUDOLF STEINER x2, LAGUARDIA
  x2, SHERMAN OAKS x2
- `CsLRK1JphL4`, listed as childhood footage, is Leprechaun (1993); it played
  under "when she was six", "Days of our Lives" and "still at Waldorf"
- food list off by one in three of six categories
- day markers: TUESDAY and SUNDAY held by a men's fitness TV show, FRIDAY by a
  Verizon red carpet, THURSDAY by a facial, REST by people mid-workout

### The identity finding

The previous handoff proposed 0.35 -> 0.45. Measured: Gayle King's source
scores 0.59-0.72 median and Reese's 0.69, so the threshold move changes
nothing. All 24 passing windows of `iUVWGBaW1b0` were rendered and every one is
Aniston. The score is taken on the first frame of a ~1.6s shot and the source
cuts to the interviewer inside it.

Three fixes, in order of how much they caught:
1. fail closed — 385 face-bearing candidates had no identity score at all
2. `midcheck.py` — index t + SPREAD/2, require her at both ends (3127 points,
   61% survive)
3. `impostors.py` — reference embeddings for Kudrow, two podcast hosts, a
   Pvolve model and Billy Crudup, built from frames of the cut itself; reject a
   window closer to one of them than to her. Kudrow measures 0.079 against her.

Two long two-hander sources (`ZoqjGormrds`, 44 min of Aniston and Kudrow
alternating; `BpgMda_4JDI`, a 75-min podcast) survived all three and were
banned: an interview edit cuts between speakers faster than any two-point
sampling can follow. Cost nothing — diet keeps 419 windows for the 70 it spends.

### Round 2 — read again, 15 wrong-person shots remained

6 Kudrow, 5 podcast, 3 Pvolve model, 1 Billy Crudup. Two of my own
hand-verified whitelist entries (`voC2DxCL6jQ` 44.6 and 54.2) were wrong: read
at thumbnail size they passed, read at 600px they are a different woman. The
whole whitelist was re-read at 600px afterwards.

### Round 3 — four regenerated stills had not reached the cut

`f_seeds`, `p_diner`, `mv_hipabduction`, `mv_kneelingrow` were fixed on disk
and still showed the old picture, because piece filenames fingerprint the still
SPEC and not the file. `build5.still_sig` now folds in size and mtime. Same
cause behind the day-card legibility fix not landing: `work5/day_*.png` was
cached and had to be deleted.

### Result

342 shots. No full-frame foreign graphics. No wrong-person shot found in the
final read. 6 place cards, none repeated. No still repeats inside 20s. Food
lists aligned. Every day marker and every movement carries a chosen picture.

Unfixed and listed in HANDOFF.md: `mv_hipabduction` (four generations, the
model will not make the pose), PAD WORK, corner network bugs, one near-black
shot, cue placement being one shot early in places.

---

## Pass 9 — the camera move

Reported by the owner: "the camera is weirdly shakey". It is not the footage.

### Root cause

Every shot carries a push-in rendered with ffmpeg `zoompan`. That filter floors
TWO things to whole pixels, independently: the crop origin `x`, and the crop
size `iw/zoom`. The two staircases step at different rates, so the apparent
position of the image drifts one way for three frames and then jumps BACK.
Reproduced arithmetically, and measured on shot 193 - a STILL image, so nothing
in it can move except by the renderer:

    dx per frame: -0.53 -0.35 -0.34 -0.35 +0.17 -0.34 -0.34 -0.35 -0.50 ...

Through the canonical measurement box in `qc_motion.py`:

    zoompan (current)   step 0.941px  sd 0.371  sd/mean 0.394  reversals 74/88

A ~0.7px oscillation at ~15Hz, on all 342 shots.

### Candidates measured on the same still

| method                     | sd/mean | reversals |
|----------------------------|---------|-----------|
| zoompan (shipping)         | 0.18    | 28 of 88  |
| ffmpeg `perspective` warp  | 0.45    | 14 of 88  |
| zoompan supersampled 4x    | 0.18    | 0 of 88   |
| per-frame float warp (cv2) | 0.05    | 0 of 88   |

(These four were measured with a wider patch box than the harness default,
which is why the shipping figure reads 0.18 here and 0.394 above. The ordering
is what matters and it is stable.)

### Decision

Full GL renderer, chosen by the owner over the cheaper fixes. Motion splits by
shot type: stills get a three.js 2.5D dolly driven by a monocular depth map,
video clips get the float warp. Plan in
`docs/superpowers/plans/2026-08-18-gl-parallax-renderer.md`.

Risks retired before writing any of it: headless Chrome reaches the real GPU
(ANGLE / AMD Radeon 880M / D3D11), readback is 7.4ms/frame at 1080p, depth
estimation is 1.55s/still on CPU torch, and three.js loads in the page - but
only as an esbuild IIFE bundle, because 0.185 ships no UMD build and
`three.module.js` carries a relative import that a blob URL cannot resolve.

Working cut preserved as `JENNIFER_ANISTON_V5_zoompan.mp4` for A/B.

### Task 1 - depth maps

147 stills, 147 depth maps, ~4 min on CPU torch. 36 reviewed by eye across two
sheets (`qc/DEPTH.jpg`, `qc/DEPTH_FOOD.jpg`). Quality is high: streets recede to
a vanishing point, figures separate cleanly from rooms, shallow-DOF food shots
carry a correct near-to-far table gradient.

Tried and DISCARDED a numeric screen for "balloon risk" (fraction of mid-band
depth pixels). It flagged q_kitchen, p_lasign and p_kojak, all of which I had
already judged good by eye - a subject against a wall legitimately has a
bimodal depth map and parallaxes correctly. The metric measured hard edges, not
harm. The FLAT_STILLS decision moves to Task 2 where actual motion can be
watched instead of a histogram guessed at.

Watch list for Task 2, all flat-lay overheads where the subject is a blob on a
uniform ground: f_citrus, f_kiwi, f_seeds.

### Tasks 2-5 - the GL renderer, and three defects the audit loop found

**Result.** Renderer-injected shake is gone. Measured on shot 193, a STILL
image, where nothing can move except by the renderer:

    zoompan (was)     step 0.941px  jerk 1.203  reversals 74/88   FAIL
    three.js 2.5D     step 0.245px  jerk 0.209  reversals  0      PASS

And on a locked-off interview, where the only motion should be the push:

    zoompan (was)     jerk 1.051  reversals 37   FAIL
    float warp        jerk 0.232  reversals  0   PASS

**The gate was wrong first.** `sd/mean` assumed a LINEAR ramp. The new renderer
eases with a smoothstep, so step size varies by design and a beautifully eased
move scored worse than a mechanical one. Replaced with the second difference
(jerk), which does not care about the shape of the ramp, only whether it is
continuous. Calibrated: 1.203 for the defect, 0.209-0.32 for the fix.

**Defect 1, found by eye: every still opened already cropped.** mv_lateralraise
lost the model's hand off the right edge on its FIRST frame. Cause:
displacement `(d - 0.5) * relief` brings near vertices TOWARD the camera, which
magnifies them ~17% at relief 0.9. Fixed by displacing backward only,
`(d - 1.0) * relief` - the near plane holds its framing and the background is
pushed away instead.

**Defect 2, caused by fixing defect 1: black wedges at every frame edge.** The
far field now sits at z0+relief and projects smaller than the frame. OVERSCAN
was a hand-picked 1.12; the requirement is 1 + relief*tan(fov/2), which is 1.28
at relief 0.9. Overscan is now derived, and RELIEF dropped 0.9 -> 0.45 because
the crop is the price of the parallax: 0.45 keeps 87% of the image, 0.9 keeps
76%.

**Defect 3, the biggest: shots that span a cut in the source.** Pulling one
2-second piece apart frame by frame showed FOUR different scenes inside it -
her on a mat, motion-blurred frames at the transition, legs on a slant board, a
torso. It reads as corruption. `ffmpeg -v error` reports ZERO decode errors in
the file; the source simply cuts inside the window and nothing ever asked.

Same blind spot that let Gayle King hold four frames: the gate samples t0 and
t0+1.6 and a campaign film can cut twice between them. `cuts.py` measures the
frame-difference spike over each candidate window. The distribution is sharply
bimodal - 50th 2.6, 75th 5.8, then 90th 29.6 - so the threshold sits in the
gap at 8.0. 22% of candidate windows contain a cut.

Measured on the finished films:

    before the cut gate   28 of 213 clip shots span a cut
    after                  6 of 213

The remaining six are harmless and were checked individually: three are
cue-pinned (both sides of the cut are still Ferris Bueller, still Rachel Green)
and three are locked sync bites, where a cut is an angle change inside one
interview.

**Stabilisation: measured, and REVERSED.** vidstabtransform on the 17% of
windows that measured shaky made the film worse, not better - #8 45.73 ->
51.08px, #14 48.52 -> 51.81px, #24 43.19 -> 49.24px - cost shot #173 23% of its
sharpness, and the shake metric cannot tell handheld wobble from fast content
(the top scores, 100-147px/frame, are campaign close-ups with hard cuts).
Disabled in stabilise.py with the numbers recorded. The MEASUREMENT is kept and
is sound; only the transform is off.

**Renderer facts worth keeping.** Headless Chrome reaches the real GPU (ANGLE /
AMD Radeon 880M / D3D11). Draw is 1.7ms/frame, readPixels 8.7ms, ws.send
19.7ms, x264 ~10ms; end to end 12-13 fps, and three worker pages did not beat
one because they share a GPU process. 152 still shots render in ~11 min, cached
after that. Depth is Depth-Anything-V2-Small on CPU torch, 1.55s per still,
blurred 2% of width before use - a raw depth map has cliffs at every silhouette
and a displaced mesh TEARS across a cliff (measured: sawtoothed forearm,
radially smeared orange, ragged treadmill console; all gone after the blur).

## Pass 10 — quote cards, and b-roll chosen by meaning

**Quote card.** The quote treatment was a translucent bar with PIL-drawn text
in it; it read as a subtitle and collided with the burned-in captions several
sources carry. It is a CARD now - dark panel, red left rule in the channel's
own #E8121A, hanging opening mark, spaced-caps credit - rendered in the browser
(`gl/card.mjs`, `cards.py`) so the typography is CSS rather than PIL: real
leading, real letter-spacing, a shadow that lifts it off the footage. Words
that have not been reached yet keep their space and show no ink, so the card
does not resize and jump on every cut. Cards are cached in `cards/`, not
`work5/`, because work5 is wiped between builds.

**B-roll by meaning.** The standing gap was that cues.py pins 61 moments and
the other ~280 shots were drawn round-robin from an era-locked pool - nothing
asked whether THIS window suited THIS sentence. `semantic.py` embeds every
candidate window with CLIP (openai/clip-vit-base-patch32, 92ms per window on
CPU torch, 3602 windows in ~20 min, cached in manifest/clip.npz) and every
shot's narration with the same model. `Reels.best` then fills a clip slot with
the highest-scoring unused window in that pool.

Three things it deliberately does NOT do:
  - it does not touch still slots, so the texture weave that gives the
    biography its establishing shots keeps its rhythm;
  - it does not override cues.py, because a cue is a hand-made statement about
    what a sentence means;
  - it cannot reintroduce a wrong person, because it only reorders windows the
    identity, impostor and cut gates have already passed.

Read off the sheets afterwards. "and the haircut she" now lands on her at a
mirror having her hair done. "a representative day actually look like" lands on
an open fridge, "ten in the morning" on a produce market, "lunch is a salad" on
a salad, "in between there is a very large amount of water" on a teapot. Before
this those were interview shots chosen by turn.

Transformers 5.x note: `get_image_features` / `get_text_features` return
`BaseModelOutputWithPooling`, not a tensor. The 512-d embedding is
`pooler_output`; `last_hidden_state` is a 50x768 token stack and is the wrong
thing to normalise.

## Pass 11 — measured against the reference, at last

The owner said the cut was fucked on all four axes: pictures, pacing, motion,
overall quality. The thing I had never actually done in eleven passes was LOOK
AT THE REFERENCE. I had read REFERENCE_SPEC.md and audited my cut against
itself. Two contact sheets of the reference answered most of it.

### What the reference does that this did not

Its exercise wedge at 7:08 sits over a stock woman doing a sun salute. Its
TUESDAY card at 7:32 sits over a stock woman mid-exercise. REFERENCE_SPEC.md
said it in plain words - "Stock footage of anonymous people is the norm ...
those clips are the format" - and I had banned exactly that footage for "not
being her": aZiwqY_e9ZQ, d7hb5JTpbFE, f8YLI3POJnM, C03vLBSWJN0, all clean, all
unbranded, all showing real people doing the movements.

So the identity gate now applies where the narration is ABOUT her - biography,
quotes, hook - and not to exercise demonstrations. Sources that stay banned are
the ones with burned-in broadcast graphics (GMA, MARCH FITNESS, Better,
InStyle covers), which is a different problem from "not her".

Day markers now sit over people training. Four of seventeen movements point at
real footage of that movement (REVERSE LUNGE, PLANK, DEAD BUG, OVERHEAD PRESS);
CLIP shortlisted candidates and every one was looked at, it got about six of
seventeen right on its own, and the pool has no slant board squat or dead bug -
so a generated still that depicts the movement still beats real footage of the
wrong one.

### Pacing was metronomic and the old comment said otherwise

Scene-detected, both films:

                     reference    old cycle
    median             1.80s        1.40s
    p75                3.62s        2.00s
    p90                5.91s        2.79s
    over 3s              32%           9%
    over 5s              13%           2%

The reference BREATHES - fast bursts, then a five-to-fifteen-second hold.
Everything here sat in a 1-2.8s band. New cycle is bimodal, and as planned the
distribution now matches: median 1.80, p75 3.53, p90 5.50, 33% over 3s, 13%
over 5s.

Long holds broke two things that had to be fixed with them:
  - cuts.py checked a 2.4s span while shots now run to 6.2s, so a hold could
    span a cut nothing had looked at. SPAN is 7.0s now, and the score records
    WHEN the first cut lands, not just whether one exists - over 7s, 54% of
    windows contain a cut, but a 1s shot does not care about a cut at 5.5s.
    Pool membership needs 1s clear; each shot then filters for its own length.
  - that also carries identity: with no cut inside a shot, the person on
    screen cannot change partway through it.

### A stale audit is worse than no audit

contact_sheet.py cached extracted frames by shot index. The shot count changed
from 342 to 258 and it silently reused the previous cut's frames - the sheet
showed a spin bike under a BANDED GLUTE BRIDGE label the film did not contain,
and I nearly filed it as a defect. The cache is keyed on the film's mtime now.
