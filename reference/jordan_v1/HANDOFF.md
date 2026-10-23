# Michael Jordan — build handoff

Episode 2 of Celeb Workout. Built 27–28 Aug 2026 on a fresh pipeline derived
from `aniston_v2` (V12/V15). Scripts copied, **no data copied** — every ban,
class and measurement here was made against this library.

## What exists

| File | What it is |
|---|---|
| `MICHAEL_JORDAN_V1.mp4` | the film, 1280×720, 30fps |
| `BRIEF.md` | the locked brief — governs everything |
| `script.md` | 68 blocks; `kind=vo` narration, `kind=bite` recorded voice |
| `quotes.json` | 18 bites, all verified against their own audio |
| `claims.json` | every factual claim + the source shown on screen |
| `METADATA.md` | title, description, chapters, tags, thumbnail direction |
| `qc/BITE_REVIEW.md` | the honest read — what survived, what was rejected, why |
| `qc/BITE_VERIFY.md` | word-for-word proof of all 18 bites |
| `qc/MOOD_TIMELINE.md` | the music bed, read against the script |
| `qc/FILM_SHEET.jpg`, `qc/FILM2.jpg` | eyes-on passes over the cut |

## The pipeline, in order

```
fetch_talk.py      speech harvest, tiered subject/trainer     -> hd/
fetch_broll.py     picture harvest (games, practice, gym)     -> hd/
src_transcribe.py  whole library, shortest-first, sliced      -> asr/
bites.py           mine candidates, tier-aware grammar gates  -> manifest/
cut_bites.py       PROVE each bite against its own audio      -> qc/BITE_VERIFY.md
ident.py           identity reference + lazy scoring          -> manifest/identity.json
srcindex.py        crop box + on-demand cut measurement       -> manifest/
pools.py           classify sources by CONTENT, not title     -> manifest/source_class.json
voice.py           narration, cached on a hash of the TEXT    -> audio/blocks/
infographics.py    12 full-frame cards, 12 distinct layouts   -> cards/
music.py           bed follows the mood of the WORDS          -> work/bed.wav
edit.py            the five gates + the shot picker
build.py           EDL, quantised integer frames, pieces
make_film.py       assemble + mux
```

## Decisions that differ from the Aniston build, and why

**The film is trainer-led, and that is deliberate.** Jordan's own recorded
speech about training amounts to about 95 seconds of unique material — see
`qc/BITE_REVIEW.md` for the full accounting. Every second of it is used. The
method is carried by Tim Grover (10 bites) and Chip Schaefer (2), which
`BRIEF.md` §2 explicitly permits. Recorded voice is ~43% of runtime.

**720p, not 1080p, and a 300px source floor instead of 640.** This archive is
1990s broadcast: the best conditioning interview is 320×240. A 620px floor would
have deleted the film. `REFERENCE_SPEC.md` measured the channel itself at
1280×720, "mixed, soft, unfussy", so 720p is on-format and makes 480×360 a 2×
upscale rather than 6×.

**Nothing is pre-measured.** Cuts (`srcindex.clear_seconds`) and identity
(`edit.identity_near`) are measured on demand and cached by content. This
removes the whole class of bug where an unmeasured window defaults to a pass —
the previous build's `clear_seconds` returned an optimistic 99.0 and let shots
run through hard cuts.

**Identity is checked twice per window.** Start and mid. Checking only the start
let the 1991 Oprah tape put Oprah on screen twice, because the picture cut
inside the shot and scene detection missed it between two similar talk-show
framings.

## Bans, each verified by eye

| Source | Why |
|---|---|
| `jHkkaTt1OdU` | two hours of OTHER people's HOF speeches — put Yao Ming and Vanessa Bryant under the opening narration |
| `1oCATl-7FsI` | caption-burned highlight compilation, not an interview. Passed every text gate AND word-overlap verification at 0.90/0.95 — settled only by looking |
| `iTFtY6KgS58` | GQ trainer feature; Grover alone in a gym, entered via a b-roll query so the trainer-tier exclusion missed it |
| `ahtfxlaufBk` | modern three-way Zoom podcast under 1980s biography |
| `u1_3Zt0Ij6Q` | 1991 Bulls Oprah episode — genuinely mixed; served Oprah, her audience and Pippen across two cuts |

## Final state, 28 Aug 2026 03:5x

| | |
|---|---|
| Runtime | **15:30** (930.25s, 27,908 frames) |
| Format | 1280×720, 30fps, 201 MB |
| Loudness | **−13.9 LUFS** (target −14) |
| A/V sync | exact — 27,908 frames ÷ 30 = 930.27s |
| Blocks | 64 (46 narration, 18 bites) |
| Recorded voice | **7.2 min = 46% of runtime**, 3 speakers, 8 sources |
| Shots | 184, median 3.4s |
| Cards | 12, all full-frame, 12 distinct layouts |
| Mood changes | 44 |
| Bites verified | **18/18** against their own audio, 0.85–1.00 overlap |
| Echo check | 9 hits → 4, all remaining are false positives or speaker intros |

### Eyes-on result

`qc/FINAL_SHEET.jpg`, 24 frames sampled mid-span. **Two defects remain in 24**
(down from six in the first cut):

- `W6` @5.6m — a couple on an ESPN couch, not Jordan
- `S3` @13.4m — mostly Pat Riley at an event

Both come from `mj_rich` sources that passed the two-point identity check, which
means either a false-positive face match or a cut between the two sample points.
A third sample point, or narrowing `mj_rich` to sources above ~0.6 mj_rate,
would likely close it.

## Known gaps / next pass

1. **Runtime is short of the 20–25 min brief.** The material supports more
   biography (`REFERENCE_SPEC` measures the channel at 40% biography and calls
   it correct) and there are ~50 more mined trainer candidates unused in
   `manifest/bite_candidates.json`.
2. **Pacing is slower than the channel.** Median shot ~3.4s here; the channel's
   own Aniston video measures 1.4s median with 323 cuts. `build.SHOT_MIN/MAX`
   controls this — lowering it costs render time, nothing else.
3. **Narration is the free edge-tts draft.** `make_film.py --final` switches to
   ElevenLabs. AUDIO LAST: do it only on a locked script. `voice.py` caches on a
   hash of the text, so a re-run costs only changed blocks.
4. **No parallax/DIBR yet.** The brief asks for real motion on stills; the cut
   is currently video-led with push-in only on cards. `depth_gen.py` and
   `photo_frame.py` were copied over but are unused.
5. **No photographs harvested.** `fetch_photos.py` is present but not run; the
   brief wants campaign stills and collages.
6. A `--final` run should re-check that no bite has drifted, since `cut_bites`
   is cheap and the script has changed twice.
