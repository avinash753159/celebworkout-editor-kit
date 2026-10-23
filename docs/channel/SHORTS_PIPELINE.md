# Celeb Workout Shorts — where it lives

The Shorts pipeline is **MoneyPrinterTurbo**, installed outside OneDrive so the
virtualenv and the 250MB+ footage cache do not sync:

    C:\Users\avina\ytshorts\MoneyPrinterTurbo

(Same convention as `C:\Users\avina\ytceleb`, which the long-form pipeline uses.)

| Path | What |
|---|---|
| `shorts/README.md` | how it works and what was changed in MPT |
| `celeb_footage.py` | harvests + identity-gates real footage of each celebrity |
| `celeb_plan.py` | builds each Short's shot list, celebrity footage first |
| `celeb/` | source videos, verified clips, photographs, ledgers, QC sheets |
| `shorts/celebworkout_shorts.json` | the scripts, search terms, sources |
| `shorts/METADATA.md` | titles, descriptions, tags for upload |
| `shorts/out/` | finished `.mp4` + `.srt` |
| `make_celeb_shorts.py` | the driver |
| `config.toml` | Pexels + ElevenLabs keys and tuning (live keys — do not commit) |

Finished Shorts are also copied to `CelebWorkout_Shorts/` in this folder for
convenience.

## Run

```
cd C:\Users\avina\ytshorts\MoneyPrinterTurbo
run_shorts.bat                  # all not-yet-rendered
run_shorts.bat henry_cavill
.venv\Scripts\python.exe qc_shorts.py     # check every output before uploading
```

`qc_shorts.py` fails a file for anything that would get it rejected as a Short
or make it look amateur: not 1080x1920, runtime outside 20–60s, loudness off
target, a caption cue wider than four words, or a proper noun from the script
that did not survive into the burned captions.

## Credentials it uses

Pulled from what was already in this folder — nothing new was created:

- **ElevenLabs** — `CelebWorkout/elevenlabs_key.txt`, narrating with voice
  `nPczCjzI2devNBz1zQrb` ("Brian"), the same voice id and voice settings the
  long-form pipeline uses (`aniston_v2/script4.py`).
- **Pexels** — `CelebWorkout/pexels_key.txt`, for the stock footage.
- No LLM key: the scripts are written and sourced by hand, and MoneyPrinterTurbo
  skips its own script generation when one is supplied.

Narration is cached on a content fingerprint in
`storage/tts_cache/`, so re-rendering a Short for a caption or footage change
does not spend ElevenLabs credit again.

## Showing the actual celebrity

Stock footage alone is not enough — a Short about how Henry Cavill trains has
to show Henry Cavill. So before rendering:

```
cd C:\Users\avina\ytshorts\MoneyPrinterTurbo
.venv\Scripts\python.exe celeb_footage.py all
```

That builds a reference face for each person from their Wikimedia Commons
category, harvests workout / diet / interview footage from YouTube, scores
every sampled frame against the reference, keeps only *runs* of consecutive
matches, and exports each run as a 9:16 clip cropped around the face — then
re-verifies the exported clip and deletes it if it fails.

**Then look at the contact sheets** in `celeb/qc/CLIPS_<slug>.jpg`. The
identity gate proves who is on screen; it cannot see another channel's burned-
in subtitles or reaction overlays. Put unusable clip ids in
`celeb/ledger/bans.json` and run `celeb_footage.py bans`.

Each render logs what share of its timeline is genuinely the subject.

## Format decisions, and where they came from

- 1080x1920, 45–50s, clips capped at 2s — the 1.4–2.0s median measured off the
  channel's own reference cut in `aniston_v2/REFERENCE_SPEC.md`.
- Titles follow the channel's existing Shorts convention,
  `<Name> Workout And Diet #short`; descriptions and tags follow the live
  uploads' house style.
- The subscribe ask is the last line of each script and appears nowhere else,
  per `aniston_v2/BRIEF.md` §0.
- Each Short is built from a celebrity the channel already has a long-form
  video for, so the Short feeds that video rather than sitting on its own.
