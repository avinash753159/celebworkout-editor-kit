---
name: celebvid
description: Use when the user wants a Celeb Workout YouTube episode about any celebrity — "make a celeb workout video", "do <name> next", "train like <name>", "build the <celebrity> video", /celebvid — or wants to fix, re-cut or re-render one. Covers the whole pipeline: harvesting long-form interviews, mining the subject's own words, writing a bite-led script, verifying every bite against its audio, picture, music mood, full-frame graphics, render and QC.
---

# Celeb Workout video builder (V16 — bite-led, glass cards, Kokoro voice)

**Repo:** `C:/Users/avina/ytceleb`. Reference builds: `YouTube/aniston_v2`
(structure) and `YouTube/jordan_v1` (voice, cards, cues, photographs).

**What this builds:** a 15-25 minute documentary where the SUBJECT and their
TRAINER carry the film in their own recorded words, with the narrator only
bridging between them, full-frame data graphics synced to the spoken word, and
every quotation proven against its own audio.

**Start at "§0 THE STANDING RULINGS", then "RUN IT".** §0 is what three rounds of
rejected cuts bought; RUN IT is the pipeline in order.

**Reference builds:**
- `YouTube/aniston_v2` — V12. 18:08, 32 bites, 40% recorded voice. The owner's
  verdict on the version before it was "it's shit, start again"; on this one,
  "this is fantastic". The difference was almost entirely step 1.
- `YouTube/jordan_v1` — V16. 15:08, 17 bites across 3 speakers, 45% recorded
  voice, 13 glass cards, 31 cue/card shots.

---

## 0. THE STANDING RULINGS — apply on EVERY build, from the start

Each cost a rejected cut. None is negotiable; none should be rediscovered.

### Voice: Kokoro. Not edge-tts, not ElevenLabs.

| Attempt | Verdict |
|---|---|
| edge-tts draft | *"The audio is complete crap."* |
| ElevenLabs Brian | *"elevenlabs brian doesn't work"* |
| **Kokoro `am_michael`** | **current standard** |

The owner pointed at `github.com/abus-aikorea/voice-pro`. Voice-Pro itself is a
Gradio app — NVIDIA GPU, ~20GB, a browser, no documented CLI — so it cannot be
driven headlessly over 40+ narration blocks. What it IS is a front end onto
engines, and the strongest is **Kokoro**, which ships as ONNX and runs locally on
CPU with no key, no quota and no network:

```bash
pip install kokoro-onnx soundfile   # NOT `kokoro`: it needs spacy, which does
                                    # not build on Python 3.14
# models/kokoro/{kokoro-v1.0.onnx,voices-v1.0.bin} from
# github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
```

`am_michael` measured 158 wpm against the channel's own 161. Auditioned and
rejected: `am_onyx` (flatter), `am_eric` (193 wpm, too fast), `bm_george`
(British, wrong register). Cache on a hash of the TEXT plus voice, never a block
id. See `jordan_v1/voice.py`.

### NO MUSIC BED AT ALL

> *"Your background audio track is super weird. Remove the complete background
> audio track. Just have it be the voiceover part and even in the interviews
> don't put sound over their voice or anything like that."*

The only audio is narration plus the bites' own recorded sound. Keep `mood.py`
and still write `qc/MOOD_TIMELINE.md` — the analysis remains the right design if
a bed is ever wanted again — but **do not mix it**. One audio stream,
`loudnorm=I=-14:TP=-1.5:LRA=11`, no `amix`.

### PICTURES PINNED TO NAMES AND ERAS — build `cues.py` before the first cut

> *"whenever it mentions other players like Scotty Pippen or whoever it is, you
> need to have pictures of them. Also when you're talking about his childhood
> and all that stuff, it needs to be a picture of him as a kid... Why is it that
> you're using the footage when you should really be using him as a kid?"*

Game footage under a sentence about somebody's childhood is the defect. Every
NAMED person and every NAMED era gets a photograph pinned to the block that says
the name. On Jordan: 18 cue pictures across 11 blocks.

**Build the transformation card.** *"When you're talking about him being scrawny,
it should be him looking really skinny and then you should have a comparison of
him being built right next to it."* Two photographs side by side, labelled with
year and weight. One of the strongest cards in the film — make one for every
subject whose body changed.

### Harvesting photographs — three sources, each lying differently

1. **Wikimedia Commons** — real files, correct licensing, but TITLE ≠ CONTENT:
   "Michael Jordan North Carolina.JPG" was a jersey in a display case, "Pistons
   Bad Boys" a box score, "Dean Smith" an arena banner. It also rate-limits with
   HTTP 429 — throttle ~1.2s between calls and let the error RAISE. An
   `except: return []` turns a 429 into "no results found" and eleven of fourteen
   pictures vanish silently.
2. **Bing image HTML** — serves one cached result set for EVERY query when
   scraped, and drifts on ambiguous names: "michael jordan kid" returns a page of
   **Michael Jackson**. Check distinctness before trusting it (57 distinct files
   out of 196 was the tell).
3. **The video library you already have** — often the best source. Frames of the
   trainer and team-mates pulled from their own interviews beat stock, and sit in
   footage you have already gated.

**Then filter by identity.** Run every candidate through the subject's SFace
reference (`ident.py`) before looking — it discards the Jacksons for free. It is
triage, not verdict: one Jordan candidate scored 0.332 and was a religious icon
painting of the **Archangel Michael**. Eyeball the survivors.

### CARDS: HyperFrames, glass, Material 3 elevation, one layout each

Three rounds of notes, all structural:

1. *"Make these cards the whole window."* → full frame, 1280x720.
2. *"Change the format of these cards - they all look the same."* → one layout
   per card, enforced in code.
3. *"the cards are still shit... use the hyper frames GitHub... Material Design
   by Google or these Radix Primitives... Primer by GitHub...
   `github.com/voltagent/awesome-design-md`... the cards should be transparent a
   bit - 3d looking like"*

Round 3 is the standard. Flat opaque panels do not meet it:

- **Render with HyperFrames** (`github.com/heygen-com/hyperframes`): HTML → MP4
  via headless Chrome. `npx hyperframes render -c compositions/<id>.html`. Load
  `/hyperframes` then `/hyperframes-core` BEFORE writing composition HTML — the
  contract is real (one paused GSAP timeline at `window.__timelines[id]`,
  `fromTo` for anything CSS also transforms, `autoAlpha` never `display`, sized
  root, finite repeats). `check` takes a project dir, `render` takes `-c`.
- **Glass, over the film.** Each card is a translucent plate floating over a
  blurred, darkened frame from the episode's OWN footage. That is what
  "transparent a bit" means: the picture is behind the data, not replaced by it.
- **Depth by Material 3** — shadow AND surface tint together, plus a 1px inner
  highlight along the top edge (the specular line that actually sells glass) and
  a 1px dark line along the bottom.
- **Real 3D** — plates enter on a perspective `rotationX/Y` from `z:-260`, inner
  elements on their own Z planes so they separate as the plate settles, and a
  sheen that sweeps once across the glass.
- **Type from Nike's system** (via awesome-design-md): extreme contrast between a
  towering uppercase display face and small, quiet information type, colour
  reserved for a single accent.

Working set of 13 layouts in `jordan_v1/hf/cards/gen_cards.py`: record, concept,
event, counter, gauge, clock, checklist, versus, split, clockface, bracket,
bignumber, transform.

### Watch for burned-in channel graphics

A Chip Schaefer bite played over a podcast frame carrying a **SUBSCRIBE button
and channel banner**. The owner caught it: *"you have 'subscribe' and 'like'...
but really that has nothing to do with the video."* Sample any bite window before
committing, and drop the bite if its only picture is branded. Compilation
channels also burn in SUBTITLES of the very words you are quoting —
`1oCATl-7FsI` passed every text gate AND word-overlap verification at 0.90,
because the audio genuinely does say those words. Only looking at the frames
caught it.

## The owner's brief, 25 Aug 2026 — this governs

Delivered as two annotated PDFs over the Aniston V11 cut. It changes the SHAPE of
the film, not just its finish. Full text in `YouTube/aniston_v2/BRIEF.md`.

**One reversal, quoted both ways so nobody re-applies the old rule:**

| Earlier | Now |
|---|---|
| "dont ask for subscribe or like or any of that" | "it doesn't have subscribe and like at the end - which it should" |

Resolution: **the ask goes at the END only.** Never in the opening, never mid-film.

**Structure**
- **She leads, the narrator bridges.** Every point that can be made in her own voice
  is. Narration sets up and connects; it does not read magazine quotations aloud.
  A narration-led cut is what "doesn't flow well" means.
- **Intro ~5 seconds** of what the video covers. "very little - like 5 seconds max."
- **20–25 minutes.**

**Interviews — "straight from the horse's mouth"**
- Transcribe the WHOLE library and mine it. Do not rely on the handful of quotes
  somebody already knew about. On Aniston that was 5 bites out of 16.5 hours; mining
  found **71 verified moments across 39 sources**.
- **Search the TRAINER too**, and use their words directly.
- **When she is quoted, play the REAL CLIP.** "Video doesn't make sense with audio -
  put the real clip." A quotation over unrelated b-roll is the defect.

**Picture**
- **Her WORKING OUT beats her talking.** "Too many interview videos - it should be
  her working out if possible."
- **Real photographs** — campaign shots, gym selfies, magazine spreads.
- **But EDIT them.** "you have to edit it so that it looks like there's edit done."
- **Collages**, not one picture at a time.
- **Parallax and real motion.** "right now it looks like a slideshow."
  Reference: `github.com/topics/image-effects?l=shaderlab&o=asc&s=forks`

**Cards**
- **FULL FRAME.** "Make these cards the whole window." The picture cuts away, the
  data owns the screen, then it cuts back.
- **Every card a different format.** "Change the format of these cards - they all
  look the same." Shape follows data: ring, gauge, thermometer, counter, bar, split.
  One template reused nineteen times is the defect.
- **Show the REAL article.** Citing InStyle or People means the actual page on
  screen, not a typographic re-set of the sentence.

**Audio**
- **Music follows the MOOD OF THE WORDS**, moment to moment — not a mood per chapter.
  A block-level table is too coarse and is what produced the mismatch.

## RUN IT: the pipeline for a new celebrity

The V12 Aniston cut is the reference build. It went from the owner's "it's shit,
start again" to "this is fantastic" by inverting one thing: **the subject and
their trainer carry the film, and the narrator only bridges.** Everything below
exists to make that possible and to prove it afterwards.

Working reference: `YouTube/aniston_v2`. Copy the scripts, not the data.

### 0. Write the brief down first

`BRIEF.md` in the episode folder. Quote the owner verbatim, including anything
that REVERSES an earlier instruction, with both halves side by side. On Aniston
the subscribe ask flipped from "never" to "at the end", and without both quotes
on the page somebody re-applies the dead rule from memory.

### 1. Harvest SPEECH, not b-roll — `fetch_talk.py`

The single highest-leverage step, and the one that was missed for four versions.
A library harvested for pictures will not carry a bite-led film: Aniston's 194
b-roll sources yielded **4.6 minutes** of her actually talking about her subject.
One targeted fetch for long-form interviews added 41 sources and made it viable.

- Search for CONVERSATION: podcasts, sit-downs, the brand's own library, and
  **the trainer's own interviews**. Sort candidates longest-first.
- Search the trainer by name as its own sweep. Dani Coleman gave 144 minutes
  across three long-forms and became the film's second voice.
- **`--no-continue`, and delete stale `.part` files.** A resumed ranged request
  gets **403 Forbidden** from YouTube, which reads exactly like a block and is
  not one. This alone caused a 31-of-34 failure rate.
- Use a permissive format chain (`bv*+ba/b`) and several player clients. The
  strict `bestvideo[ext=mp4]+bestaudio[ext=m4a]` has no fallback.

### 2. Transcribe EVERYTHING — `src_transcribe.py`

faster-whisper `base`, int8, VAD on. 16.5 hours costs about 3.5 hours of CPU.

- **Shortest first.** Alphabetical order put a 146-minute podcast fourth and
  blocked 190 short sources behind it.
- **Save in resumable slices.** That same podcast consumed an entire window,
  was killed, and saved nothing — twice — before slicing was added.
- VAD matters: a third of a library is applause and music, and without it those
  minutes get hallucinated into sentences the subject never said.

### 3. Mine the bites — `bites.py`

Topic vocabulary + first person + identity + the two voice gates in gate 5
below. Then READ the survivors: on Aniston 71 passed the gates but only 24 were
genuinely on topic, and 22 survived a read. **Report the number that survives
reading, not the number that passes.**

### 4. Write the script around the bites — `script.md` + `quotes.json`

Narration exists to set up a bite and connect it to the next one. If a block
runs 50 seconds of voiceover, it has reverted to the old shape.

Budget it honestly before writing: bite-seconds ÷ target runtime is the share
the subject actually carries. If that is under ~30%, go back to step 1 rather
than padding narration — and say so.

### 5. PROVE every bite — `cut_bites.py`

Cut each bite, **re-transcribe the cut**, and compare word-for-word against what
the script claims. A transcript is an index, not the audio; an index can be off
by two seconds or belong to a different speaker in the room. 32/32 on Aniston at
75–100% overlap. Nothing ships unverified.

Also check every bite has **at least a second of headroom** before its source
ends, or the video will be frames shorter than the audio.

### 6. Narration — `tts6.py`

**Cache on a fingerprint of the TEXT.** Keying on block id plus "does the file
exist" would have served V10's narration under V11's words, because both scripts
use `W1` and `H1` for different sentences. Same species as the bug that put V5's
soundtrack under V6's picture.

### 7. Picture — `build5.py`

- A **bite plays its REAL CLIP**, at its real source timecode.
- Derive the block→pool map from the `section=` tag in the script, never a
  hand-kept list of block ids — a new block otherwise ends up silently poolless.
- New footage must be added to the **cut-measured** list as well as the pool
  list. An unmeasured window gets `clear_seconds()`'s optimistic 99.0, which
  reads as "no cut" and lets a shot run straight through one.
- **Exempt bite-to-bite pairs from the consecutive-source and group gates.** Two
  bites from one interview are the same person still answering. The gates still
  bind on every pool-selected shot.
- Give the picker **one block of lookahead** so the last pool shot before a bite
  is never that bite's own source.
- A source that supplies a BITE should not also be pool filler.

### 8. Music — `mood.py` + `bed.py`

Score the mood from the WORDS at that timecode, not from the block id. A block
that opens on an injury and closes on a recovery gets one bed otherwise, and the
mismatch is audible. 68 blocks → 34 mood changes on Aniston. Write
`qc/MOOD_TIMELINE.md` and read it against the script.

### 8b. Photographs and cues — `fetch_images.py` + `pick_images.py` + `cues.py`

**Do this before the first cut, not after a rejection.** See §0 for the three
harvest sources and how each one lies. Order: harvest broadly → identity-filter
→ contact sheet → pick by eye → pin to blocks in `cues.py`.

A cue is `(block, ordered list of pictures)`. It plays at the FRONT of its
block, before pool filler, because the point is that the named person is on
screen while the narration names them. Cues bypass the identity gate by design —
a picture of Dean Smith is supposed to be somebody other than the subject.
`cues.check_against_script()` refuses to run if a cue names a block that no
longer exists; 47 stale pins survived a script rewrite on an earlier build.

Reuse of one picture is fine and often unavoidable — vary the MOVE by use index
(`build.render_photo(..., variant=n)`) so a repeat reads as a second shot rather
than a stuck frame.

### 9. Graphics — HyperFrames glass cards (`hf/cards/gen_cards.py`)

**FULL FRAME, glass, one layout each.** See §0 for the design system, the
HyperFrames contract and the render command. `render_cards()` refuses to build
if two blocks resolve to the same card, and refuses on a missing render rather
than silently dropping one — a missing card just looks like a gap.

**Trim cached on CONTENT, never on the card's name.** A card is rendered at a
fixed length and trimmed to whatever its block needs; keying that trim on
`c_transform` alone served the previous render after its photographs and labels
had been replaced, and the film shipped reading "1987 · 195 LB" over the old
picture. Hash size+mtime into the key.

Match trigger phrases to the **ASR**, not to the script — the narrator says
"45", the script says "forty-five".

The older static-PNG generator (`infographics.py`, `emit()` with its duplicate
`kind` guard) is superseded. Keep it only as a fallback if Node is unavailable.

### 10. Render and QC — chunked, then READ IT

Render **video-only in resumable chunks** and mux the approved audio separately.
Long renders do not survive a wrapper that returns; one was killed twice at 1166
and 6230 frames of 27525. Never `-shortest` on the final mux — it clipped six
seconds of endcard.

Then sample the MIDDLE of every span, never the end. Sampling 1.2s before a
graphic's exit lands on the next topic's first shot and invents defects that are
not there — it produced six false reports on V11.

## WHAT WORKED — the six things that actually moved the needle

Ranked by how much they changed the result. Everything else is detail.

1. **Harvesting SPEECH as a separate pass.** The single biggest lever, and it was
   missed for four versions. A b-roll library cannot carry a bite-led film. One
   targeted fetch took the subject's own voice from 4.6 min to 7.2 and made the
   whole structure possible.
2. **Searching the TRAINER by name.** 144 minutes across three long-forms. It
   turned a cited source into a second character who explains the method, says
   what changed, and names what everyone else gets wrong.
3. **Proving every bite against its own audio.** Cut it, re-transcribe the cut,
   compare word for word. 32/32. The first time on this project the audio was
   checked rather than assumed.
4. **Content-fingerprint caching, everywhere.** Text hash for narration, content
   hash for pieces. Every stale-cache disaster on this project traces to a key
   that was a NAME or a POSITION.
5. **Enforcing design rules in code, not in review.** `emit()` refuses to write
   if two graphics share a layout. "They all look the same" is invisible until
   they are all on screen together, which is far too late.
6. **Reading frames.** Every defect that mattered was found by looking. None was
   found by measuring, and several were found DESPITE a measurement saying the
   opposite.

## EVERY FUCK-UP ON THIS PROJECT

Written down because each one cost real time, and because most of them are the
same three mistakes wearing different clothes: **trusting a name instead of
content, trusting a number instead of looking, and trusting a tool without
checking what it actually measured.**

### Wrong claims I made to the owner

- **"71 verified moments, 28.4 minutes."** The truthful figure, after reading
  them, was 24 on topic and 22 that survived reading — 4.6 minutes. The lower
  band was dogs, films and Friends dialogue. I quoted the number that passed the
  gates instead of the number that survived being read.
- **Six graphics reported as sitting on contradictory footage.** All six were an
  artefact of sampling 1.2s before each span's EXIT, which lands on the next
  topic's first shot. At 60% through, every one was correct. My instrument was
  broken, not the film.
- **Two shots reported as defects for three consecutive rounds.** They were
  deliberate cues — "bands and light weights" over equipment, "Dani Coleman" over
  the trainer. My checker did not know cues existed.
- **A dsh coverage check that was wrong by construction**, matching the first 24
  letters of ledger text against card text that is deliberately shortened. It
  faithfully returned "20 of 25 missing"; by ID all 25 were present.
- **"Nothing is in the PDF I have not seen."** I had extracted the text of all 18
  pages but only LOOKED at five, and missed a defect report — "there's a pic of
  mathew perry in there somewhere" — sitting under a URL I had truncated.

### Damage I did by acting on unverified reads

- **Killed a worker agent on a false timestamp.** I was watching `CARD_SHEET`,
  which was static because the cards were final; the remaining work was placement,
  visible only in `CARD_OVER`. The kill destroyed its transcript unrecoverably and
  cost a full round of rework.
- **Watched `pieces5/` while the build wrote to `pieces6/`** and reported zeros
  for several checks while the build ran perfectly.
- **Banned five source files that do not exist.** I read IDs by eye off contact
  sheet labels where `l`, `I` and `K` are identical. A breaking-news package then
  became the heaviest source in the film at 12 shots.
- **Corrupted the impostor references** by rebuilding them against the finished
  film instead of the source timecodes. Kudrow scored +0.836 against Aniston's own
  reference. They WERE her. Film-anchored references rot; source-anchored only.
- **Shipped a "fix" that was not one.** `clean_pin` v1 used `clear_seconds`, which
  returns an optimistic 99.0 for unmeasured windows, so all ten pins "passed" by
  stepping onto a hole in the data. Only caught because every nudge was
  suspiciously +0.25s.

### Tooling mistakes, repeated more than once

- **Wrapped long renders in `nohup … &; sleep; tail`.** When the wrapper returned
  it took the render with it — killed at 1166 and again at 6230 frames of 27525.
- **Rendered at concurrency 8**, which crashed the compositor. 4 is stable.
- **Heredocs mangled regexes twice**, turning `\b` into literal backspace bytes
  that silently broke word-boundary matching. Use the Edit tool for anything
  containing escapes.
- **Edited the wrong list.** Removing a source from `DEMO_CLEAN` when the goal was
  `DEMO_SRC5`, because the same line appeared in both with different indentation.
- **Converted minutes to seconds wrongly** when grabbing QC frames, then read the
  wrong frames and nearly drew conclusions from them.

### Pipeline bugs found and fixed

- **The audio cache served V5's soundtrack under V6's picture.** The test was
  "file exists and duration > 600s". Both were true. Neither meant current.
- **The TTS cache would have served V10's narration under V11's words**, keyed on
  block id plus existence, because both scripts use `W1` and `H1` for different
  sentences. Caught before spending.
- **`probe()` crashed on a 48-byte truncated piece** and took down the NEXT build,
  not the one that made it.
- **Cue drift**: positions returned as a word-count fraction and compared against
  cumulative frames. Fixed with word-level timings — and then found that
  `transcript.py`, the audit tool, had the SAME bug, so the ruler shared the flaw
  of the thing it measured.
- **Quote cards over strangers' faces**, three attempts. `best()` returned early
  for stills, empty text and not-ready semantics, and every early return bypassed
  the identity filter. Fixed by moving the rule ahead of any early return.
- **JSON written in cp1252**, so every em dash became tofu. The fonts were checked
  first and had every glyph. The terminal's own cp1252 stdout then made the FIXED
  data still print as `?`, which nearly sent the diagnosis wrong a second time.
- **`-shortest` on the final mux** silently clipped six seconds of endcard.
- **`SECTION_POOL` was a hand-kept list of block IDs**, so every new block was
  silently poolless. Now derived from the script's own `section=` tags.
- **New footage had no cut measurement**, and unmeasured returns an optimistic
  99.0 that reads as "no cut". Sources must be added to the cut-measured list as
  well as the pool list.
- **The consecutive-source and group gates fired on consecutive BITES** — one
  person still answering, flagged as repetition.
- **The picker had no lookahead**, so the last pool shot before a bite could be
  that bite's own source.
- **yt-dlp returned 403 Forbidden** on every resumed download because of stale
  `.part` files. It reads exactly like a block. 31 of 34 failed before this.
- **Whole-file transcription lost everything on a kill**, and alphabetical order
  put a 146-minute podcast fourth, blocking 190 short sources behind it.
- **A bite ran past the end of its source**, leaving the video four frames shorter
  than the audio.
- **47 cue pins survived a script rewrite** pointing at blocks and phrases that no
  longer existed, and the build aborted rather than pruning them.

### The pattern, stated once

Three failure modes account for nearly all of the above:

1. **A key that is a name or a position, not content.** Every cache disaster.
2. **A measurement mistaken for an observation.** Every false defect report.
3. **A tool whose "no data" answer looks like a "pass".** `clear_seconds`
   returning 99.0; face identity answering a question about voice; "file exists"
   answering a question about currency.

When a check passes, ask what it would have done with no data at all. If the
answer is "passed", it is not a check.

## Read this before anything else

**The channel is the spec, not `docs/BRAND.md`.** V12 was built against the
brand document and produced a different kind of object entirely. Download the
channel's own video on a comparable subject and MEASURE it. For Jennifer
Aniston that was their 309k-view "Workout And Diet" episode, and the gap was
not subtle:

| | Their video | The doc-driven build |
|---|---|---|
| Median shot | **1.4s** | 8.2s |
| Shots under 2s | 62% | **0%** |
| Total cuts | 323 | 84 |
| Biography share | 40% | cut down as a "retention problem" |
| Subscribe ask | 32s at 0:19 | 10.6s at 0:53 |
| Exercise demos | stock models | banned by a rule |
| Accent red | `#E8121A` | `#B22B1A` from the doc |

Where the document and the channel disagree, **the channel wins**. Write the
measured spec to `REFERENCE_SPEC.md` and build against that.

## The rule that matters more than any other

> **A number improving is not verification. Generate a contact sheet and READ
> the frames before calling anything fixed.**

Every defect that actually mattered in the Aniston build was found by looking,
never by measuring: a ten-second static open, twenty-four identical talking
heads, stale exercise cards, a repeated place label, a full-frame **Eminem**
magazine spread, and a portrait pillarboxed into a narrow strip two seconds in.
All of them passed every automated check that existed at the time.

Corollary: **an edit that does not apply is worse than no edit.** Twice a
string-replace silently failed to match and the feature was reported as
shipped while rendering nothing — quote bars generated to disk and never
composited, push-ins never alternating. Grep the call site after every patch.

## Five gates, or the picture will be wrong

Build these before the first cut, not after the fifth.

**1. IDENTITY, not presence.** Face *detection* is not enough — it passes
Eminem, because Eminem has a face. Use `FaceDetectorYN` + `FaceRecognizerSF`
(ONNX models from `opencv_zoo`), build a reference embedding from frames
verified by eye, and score every candidate window by cosine similarity.
Measured on Aniston: **26% of windows had no face at all, and only 45% of the
face-bearing ones were actually her.** The recogniser independently scored her
father at +0.002 and Lisa Kudrow at +0.143 against her own +0.72 to +0.75.
Threshold ~0.35. **Bypass it for cue shots** — "her father, John Aniston" is
supposed to show somebody else.

**2. CUES: pin the picture to the WORDS.** Choosing shots from a per-section
pool means any era-appropriate clip plays under any era-appropriate line. That
produced "her father, John Aniston" over an empty studio, "the Rudolf Steiner
School" over a Los Angeles street, "Ferris Bueller" over a diner, and "Cake, in
twenty fourteen" over the Golden Globes — with the correct footage sitting
unused in the pool. Build a `(block, phrase, source, timecode)` table, locate
the phrase by word position, convert to a time, and force that picture onto the
shot covering it.
**Pick each cue's timecode from the identity ranking, not from memory** —
hand-guessed timecodes were 9 of 25 correct and put Brad Pitt under "Primetime
Emmy" and Ross alone under "the breakthrough came with Friends". Assign a
DISTINCT frame per cue, or two cues collide on one shot.

**3. NO WINDOW TWICE, and ONE CURSOR PER SECTION.** A reel that rewinds to its
start when a short source runs out replays identical seconds — 322 of 365
sampled frames had a near-duplicate, several byte-identical. Worse, building a
fresh cursor per narration BLOCK restarts the same pool at index 0 for every
block, so five biography blocks re-served the same opening windows; that single
bug survived three rebuilds and undid every other repetition fix. Enumerate
every distinct window up front, shuffle per source (seeded on the source id) so
long files are sampled throughout instead of only at the head, and consume the
list once.

**5. VOICE, not just FACE.** A face-identity score says who is ON SCREEN. It says
nothing about who is SPEAKING, and compilation channels are built out of exactly
that gap — licensed b-roll of the subject under a presenter's voiceover. Mining
Aniston's library for "her own words" returned, at the top of the ranking, a
YouTuber saying *"I tried Jennifer Aniston's 15-minute workout for 30 days"*: topic
7.0, identity **0.769**, and not her. Two text gates fix it, and both are needed:

- **Per run** — reject anything containing the subject's NAME or a reporting verb
  ("revealed", "told the outlet", "she said"). Nobody refers to themselves in the
  third person or quotes themselves.
- **Per source** — judge the first 60 seconds and drop the whole video if it opens
  like a presentation ("I tried…", "in this video", "top 10"). A first-person
  *review* passes every per-run test; only source-level classification catches it.

163 candidates → 133 → **71 verified**. See `aniston_v2/bites.py`.

**4. NEVER PILLARBOX.** Padding a vertical source to black puts a portrait in a
narrow strip with huge bars either side. Fill the frame with a blurred, zoomed
copy of the same picture and lay the sharp version on top.

## Source hygiene

- **Label a source by what is IN it, not by its search-result title.** A clip
  filed as "campaign coverage" was a design-portfolio showreel carrying a
  full-frame Eminem spread. Scan every new source before trusting it.
- **Ban anything under ~640px** after cropping. A 320x240 clip upscaled 6x to
  1080p is mush, and sharpening makes it worse.
- **Crop per WINDOW where a source mixes formats** — one file intercut
  pillarboxed phone video with full-width footage, and a single per-source crop
  could not serve both.
- **Detect the active picture box** (`cropdetect`) before applying an editorial
  crop; several sources are letterboxed or pillarboxed inside their container,
  and a crop expressed as a fraction of the container keeps the bars.
- **Do not trust an automatic title-card detector.** One written for this
  flagged 70% of a Friends compilation, all ordinary footage. Head/tail
  exclusions on packaged clips are what actually holds.
- Burned-in captions fight your own labels: a frame reading "5: LATERAL DELTOID
  RAISE" under a card saying OVERHEAD PRESS is worse than no shot.

## Exercises: the picture must show the movement

Audited on Aniston: **2 of 17 exercise pins were correct.** BANDED GLUTE BRIDGE
sat over three women standing in a TV studio; CAT COW over someone lying flat.
The footage does not exist — nobody has filmed the subject doing a dead bug.

**Generate a still for every named movement**, look at it, and regenerate the
ones that come back wrong (a "plank" prompt returned a downward dog twice).
Keep any video pin that a frame check proves correct. Write the audit to
`MOVE_REVIEW.md` with what is ACTUALLY in each frame.

## Audio

- **The bed must follow the MOOD OF THE WORDS, moment to moment.** The owner's
  verdict on a chapter-keyed music table: *"the audio background doesn't really make
  sense - it should be in sync with the MOOD of what the transcript is saying."* One
  mood per block is too coarse — a block that opens on an injury and closes on a
  recovery gets one bed for both, and the mismatch is audible. Drive mood from the
  narration text at that timecode, and change the bed when the sentiment changes,
  not when the chapter does.
- **Leave silences.** The reference has eleven pauses over 0.35s; a build with
  narration covering 92% of runtime and ZERO pauses is exhausting, and no
  frame-based check can see it. Put a real beat after each thought.
- **High-pass the music bed.** Measured at 58% of its energy below 500Hz, sitting
  on the narrator's fundamental — that is what makes a voice sound muddy. An FFT
  high-pass at ~220Hz fixes it. A per-sample IIR loop over 32M samples in Python
  takes hours; do it in the frequency domain.
- **-14 LUFS, not the reference's -23.3.** YouTube normalises to about -14, so
  copying their level would be a regression.
- Speaking rate ~161 wpm matches theirs; pacing problems are pauses, not speed.

## Grade

Match exposure PER SOURCE toward a common target, and **apply it to stills and
cards too** — a correction living only in the video path missed 28% of runtime
and made hard cuts worse, not better. Measured spread fell from stdev 41.8 to
31.9 and hard cuts from 90 to 61 once stills were included.

## Medium: stills beat video 7.5:1, and usually look better

| Medium | Cost | Use for |
|---|---|---|
| Still + depth push-in | **~$0.04/shot** | Default. Compositions: objects, documents, landscapes, portraits of things |
| Veo video | **~$0.30/shot** | Process/change over time, scale revealed by movement, organic motion, the film's biggest beats |

A 12-minute film is ~$4 as stills, ~$30 as video. Budget the split
explicitly: ~30 video shots in a 12-minute film is a good ratio, chosen by
asking **does motion carry meaning a single frame cannot?**

Stills are also *sharper* than 720p Veo, which suits documents and objects.

- `pipeline/flow_still.py` — generate image + render the move
- `pipeline/flow_dibr.py` — depth-image-based push-in
- `pipeline/flow_gen.py` — Veo worker

**Use DIBR, not band-splitting.** Splitting an image into 3 depth bands and
scaling each produces no depth and reads as cardboard. A continuous per-pixel
warp driven by a dense depth map does. Depth-Anything-V2-Small + `cv2.remap`
with float32 maps. **Never round a coordinate** — integer rounding of the
crop box reads as judder (measured 1.008px; subpixel version 0.031px).

DepthFlow (`pip install depthflow`) does not install on Python 3.14 —
`moderngl`/`glcontext` have no wheels and need a C++ toolchain. Don't retry it.

Parallax only works where the depth map has structure. Flat or macro
compositions degrade to a plain zoom — that is automatic and correct, not a
bug to fix.

## The Gemini Developer API rejects most config fields

This cost four failed runs, discovered one at a time. **The Developer API
raises `ValueError` client-side, before any request is sent** — so these cost
$0, but they look like the API is broken.

**Rejected:** `seed`, `generate_audio`, `negative_prompt`, `person_generation`,
`fps`, `enhance_prompt`, `compression_quality`, `resize_mode`, `labels`,
`mask`, `output_gcs_uri`.

**Accepted:** `aspect_ratio`, `duration_seconds`, `resolution`,
`number_of_videos`, `last_frame`, `reference_images`, `http_options`.

Two consequences to plan around:
- **No seed = no reproducibility.** A rejected shot can only be re-rolled,
  never refined.
- **No negative_prompt.** Anti-text/logo defence lives entirely in prompt
  wording plus post-hoc QC.

**Veo attaches an AAC track that cannot be disabled.** Map video explicitly at
assembly; do not rely on `-shortest`.

**Imagen 4 is closed to new users** (404). Use `generate_content` with
`gemini-3.1-flash-lite-image`.

Verify the whole allow-list with a test that asserts config emits *only* the
accepted keys, so re-adding a rejected field fails in the suite, not live.

## Money safety (a worker that spends unattended)

- **Charge the ledger when the API accepts the job**, not when the local
  client finishes parsing. Charging at parse-success means a wrong
  response-shape assumption leaves `spent` at $0.00 — so the cap never trips
  and the worker burns the whole backlog while printing `spent $0.00`.
  Charging *before* the call is also wrong: a client-side validation error
  books money that was never spent.
- **Circuit breaker: halt after 3 consecutive failures.** A systemic bug is
  indistinguishable from bad luck without one. Add a total-failure budget too
  — a consecutive-streak breaker is starved by alternating fail/succeed.
- **Split submit from download.** A failed download must retry the download,
  never resubmit — resubmitting buys the same video twice.
- **Record the error on every non-done state.** A ledger that says `failed`
  without saying why costs a diagnostic run to rediscover a one-line error.
- **A file on disk is not proof of a usable clip.** Quota-halted attempts
  leave partial mp4s. Trust `state == "done"`, never `path.exists()`.
- **Veo quota (429) is periodic, not spent budget.** The model stays
  reachable. Generate stills as a floor so the film is always complete, and
  let video upgrade over them when quota returns.
- **The project key file beats an ambient env var.** An operator's shell can
  carry a stale `GOOGLE_API_KEY` from another project — this one did, for
  three runs. Print which source the key came from, masked.
- The API key goes in `?key=`, never as an OAuth bearer. Bearer returns
  `API_KEY_SERVICE_BLOCKED`, which reads exactly like a revoked key.

## Timing — the rules that survived every rebuild

- **`manifest/edl_full.json` is the only source of timing.** Never a
  transcript. Whisper merges long pauses and drifts 10+ seconds.
- **Quantise boundaries, don't distribute drift.** Each EDL boundary becomes
  `round(t * FPS)`; durations derive from those integers. The totals telescope
  exactly with no reconciliation step. Allocating one global frame pool
  guarantees the *total* but pushes error onto individual cuts — and it lands
  on **sync boundaries**, where 1.35 frames is ~56ms of wrong picture under
  the subject's own voice.
- **`src_t0` comes from the EDL's bite in-point, never a scan window's `t0`.**
  `bite_windows.py` widens its search by 1.5s and nudges edges +0.25s, so a
  run's `t0` is the in-point minus 1.25s *by construction*. This put over a
  second of wrong picture under his voice on all 17 sync shots, and it passed
  every check that only asked whether the field was present and positive.
- **Integer frames, summed exactly. Never pad, never loop.** A short piece is
  an error. Rounding across 130 shots once accumulated 3.8s and the "fix"
  inserted an 18-second frozen frame.
- **Cache pieces on a content fingerprint, not the shot name.** Shot names are
  positional; swap a clip and a name-keyed cache serves the stale render.

## Prompts are the film

**A shot that needs explaining has failed.** The viewer gets one read of a
4–10 second image. Literal beats metaphorical; showing the state the sentence
describes beats showing a symbol of it.

Audit every prompt against the narration it plays under before generating.
On the MrBeast film that found 88 KEEP / 20 WEAK / 10 FAIL, and the failures
were systemic rather than isolated:

- **"Objects moved by nothing visible"** drove five separate shots. The
  operator rejected two by eye; the audit found the pattern.
- **Two shots contradicted their own line** — three chairs under "room for
  exactly one".
- **A quarter of the script was a sequence of events, not an image** —
  calendars igniting, grids filling. Those collapse to nothing as stills.

Mark shots whose meaning *is* the change over time as `needs_video` so they
stay on the expensive path deliberately, not by accident.

**Any visible human must be consistent with the subject or unreadable as
him** — hands operating a prop, a crowd, a figure at distance. A generated
person who reads as "young <subject>" and looks nothing like him is worse
than no shot, because the viewer knows who the film is about.

## Audio architecture (unchanged — 4 bugs, never regress)

1. `amix` renormalises when a short input ends → clipping. Use `normalize=0`.
2. Mono SFX + stereo VO in `amix` → narration comes out +3dB hot. `aformat`
   both to stereo first.
3. **Never slice narration per beat** — per-beat AAC re-encode puts an audible
   glitch at every join. Narration plays continuously between interludes.
4. **Never `acrossfade` audio chunks** — each crossfade overlaps its inputs,
   shortening total audio ~0.3s per junction → cumulative A/V drift. Butt-join
   with 30ms edge fades. Keep the hard sync gate: refuse to mux if
   `|video_dur − audio_dur| > 0.25s`.

**AUDIO LAST.** Build the whole visual cut on a free edge-tts draft; paid TTS
fires once on the locked script. Check for pre-staged `voiceover_<slug>.mp3`
before spending anything.

**Profanity:** mute on a *copy* of the master, never the approved original.
Duration must stay byte-identical or the frame budget breaks. Note YouTube
auto-captions mask profanity as `[&nbsp;__&nbsp;]` — a regex for `[ __ ]`
misses it, which is how a "no profanity found" answer was wrong.

## Delivery

- Drive uploads through the gcloud OAuth client need an
  `x-goog-user-project` header and `drive.googleapis.com` enabled on a
  billable project. Without it every call is `403 Forbidden`, which reads
  like a permissions problem. Resumable session, 8 MiB chunks.
- **Background renders get killed at tool boundaries.** Do the final concat
  and mux in the foreground. Never re-encode a body that is already encoded —
  concat a matching black tail and stream-copy.
- Writing to a locked output path silently produces a corrupt file
  (`moov atom not found`). Write to a fresh filename.

## YouTube copyright — WITHDRAWN by the owner

> "don't worry about copyright - that is not your concern"
> — and then: "include ALL interviews with her talking about her health/workout"

**The three limits below no longer apply.** They are kept only so that a future
reader who remembers them knows they were retired deliberately, not forgotten.
Taking one clip per source directly contradicts the current brief, which wants as
many of her own words as can be found, including several from the same interview.

~~The retired limits:~~

1. **No clip longer than 10 seconds.**
2. **Never repeat a clip.** Already enforced by the no-reuse registry.
3. **One clip per source video.** Not one per scene — **one per source.** If a
   90-minute podcast yields a perfect moment, take that moment and nothing
   else from that video.

Rule 3 is the expensive one and it invalidates the previous film's structure:
*The Disease That Built MrBeast* draws **8 bites from a single Rogan episode**
and 6 more from one Airrack video. Under this rule that film would need 14
different sources.

What survives from that thinking: **widen the source pool anyway.** Not for legal
reasons but for picture variety — a film drawing 8 bites from one podcast looks like
one room for eight minutes. Mine everything, then spread the selection across
appearances because it CUTS better, not because a rule says so.

## Branding — the largest quality gap

Read `docs/BRAND.md` before building any graphic. It is measured off
`library/brand/channel_banner.png`, the only authoritative statement of the
identity.

The failure to avoid, in the owner's words: *"it's very easy to tell that it
was generated with AI — the fonts, animations, layouts and overall design look
like the default style Claude uses for almost every project."*

The system, in short — full detail in `docs/BRAND.md`:

- **Celebrity Red `#B22B1A`.** `#E3120B` is wrong and appears throughout the
  existing code. So is any per-celebrity accent colour.
- **70% black/white/photography, 20% neutral, 10% red.** Red is the signature,
  not the ground.
- **Four type roles, three families, all installed and OFL:** Anton (hero
  condensed), Archivo Black (names, logo), Archivo Regular/Medium (information),
  Allura (a one- or two-word script accent). **Never more than two families in
  one frame.**
- **Chapters are fixed:** THE ROLE, THE WORKOUT, THE DIET, THE RESULTS.
- **The red circle behind cut-out subjects is permanent brand**, not decoration.

Check contrast wherever type meets image. A matte over dark footage goes
black-on-black; separate with the thin warm-white edge the guidelines allow,
never with a glow or a second colour.

Identity is cumulative. It will not be fixed by restyling one video; every
film has to use the same faces, the same red, the same devices.

## Revisions — keep the unit of change small

A fix in Premiere is quick because you change one clip. An AI workflow only
matches that if the pipeline is granular, and this one is: every shot renders
to its own piece, cached on a **content fingerprint**, so changing one prompt
re-renders exactly one shot and nothing else. A re-roll costs $0.04 and the
assembler stitches around it.

Protect that property. It breaks the moment anything caches on position, or a
single render covers several beats.

## Edit rules — from the owner's review of the last film

His verdict on it: *"I thought it was pretty awful. I would never watch that
video."* Full detail in `docs/EDIT_RULES.md`. The seven that matter:

1. **A shot illustrates the ARGUMENT, not a word.** The failure is
   keyword-triggered literalism — the line says "cling", a shot of clinging
   appears. Ask what the *paragraph* claims and whether the image advances it.
2. **Fewer shots, held longer.** 8–12s, not 4–6. Rapid cutting between loosely
   related images reads as filler: *"just images after images"*. Also cheaper.
3. **A bite plays a COMPLETE THOUGHT or is not used.** Never cut mid-sentence.
   Never include the interviewer's "uh". If the clean thought exceeds 10s, the
   quote becomes an on-screen document instead.
4. **Narration never restates a bite.** *"If the narrator's not providing
   value, you don't need the narrator."* `echo_check.py` exists for this — run
   it and treat every hit as a blocker.
5. **One clip per source, editorially as well as legally.** Returning to one
   interview invites the viewer to go and watch that interview instead:
   *"which means your video is useless."*
6. **Every frame carries the brand.** *"It didn't seem like one brand theme.
   It was just cut and paste."*
7. **If the narrator adds nothing, cut the narrator.** Every block must supply
   context, make a link, land a judgement or turn the story. Blocks that
   describe what is already on screen get deleted.

Fewer shots is not a compromise, it is the fix.

## Red flags — stop

- Hunting for more footage because the pool is thin → generate it
- Trusting a file's existence instead of the ledger
- Charging the budget anywhere but on API acceptance
- Allocating frames globally instead of quantising boundaries
- `src_t0` from anything but the EDL
- A test whose expected value was copied from the output it checks
- Shipping without an eyes-on pass — every previous build was machine-clean
  and still failed review
