# Celeb Workout — Editor Kit

Everything you need to re-cut and improve the Celeb Workout YouTube episodes.
The channel makes 15–25 minute "Train Like ___" documentaries: the celebrity and
their trainer tell the story in their own recorded words, a narrator bridges,
and full-frame graphics carry the numbers (sets, reps, diet).

## Your job

Take the cuts below that are ready, and make them better. Start with the
**"Ready to improve"** table. For each film, watch the review cut, read the
notes, then rebuild.

## The videos (Google Drive)

All footage lives in one Drive folder: **[Videos to Edit](https://drive.google.com/drive/folders/1_zn__cw0EZLr4NhMNvGIZkKtxX7NsZRl)**

### Ready to improve

| Film | Review cut | Editor package (Premiere + After Effects) |
|---|---|---|
| Bruce Lee V1 | [BRUCE LEE V1.mp4](https://drive.google.com/file/d/1-0j7Yd9DDQvWZNguv6BLqlWjdWSMMpCD/view) | [V2 package](https://drive.google.com/file/d/1N9Ikp7Q4ERqmytcMpXA-PdEpOZ1wOxxo/view) |
| Jennifer Aniston V12 (re-edit) | [JENNIFER ANISTON V12 reedit.mp4](https://drive.google.com/file/d/1AtW4ByFpHvARde6SR3geMsNd4yZCHp8G/view) | [V14 package](https://drive.google.com/file/d/1v5E8SVP0fL_C5UYzZp13eozFxCeOAcM8/view) |
| Michael Jordan V2 | [MICHAEL JORDAN V2.mp4](https://drive.google.com/file/d/1eoflCWG2QNe4Xe-xsz1tSIg8mzZLVCQ7/view) | [V5 package](https://drive.google.com/file/d/1jBPWrrrokNooAn3GURzX-GANfOCqyfrS/view) |
| Matt Damon V1 | [MATT DAMON V1 REVIEW.mp4](https://drive.google.com/file/d/1QrK1AciF7ZZQtKBmvtAl0b5x1WA7X8Wa/view) | [V2 package](https://drive.google.com/file/d/1f5Osw_iA665pEsAeFD6sh28NWj8K4K7r/view) |
| Dita Von Teese V2 | [DITA VON TEESE V2 REVIEW.mp4](https://drive.google.com/file/d/1W6q4ncZ704OOXeHON1ROs32t8QTmInw0/view) | see `EDITOR PACKAGES` folder |
| Priyanka Chopra V1 | [PRIYANKA CHOPRA V1 REVIEW.mp4](https://drive.google.com/file/d/10lKTjjqcDIS-gsU37SOhFFcUB9pmOdlV/view) | see `EDITOR PACKAGES` folder |
| The Disease That Built MrBeast V12 | [MRBEAST V12.mp4](https://drive.google.com/file/d/1qXmRIaLPvl4nPMuyxEP8XWqbGQQf8hSD/view) | [V13 package](https://drive.google.com/file/d/1mdfHLQ1p3pKhcfNoXDgUaN4OJbKjW6bh/view) |

### Also in the folder (later or alternate builds, for reference)

| Film | Review cut |
|---|---|
| Bruce Lee V2 | [BRUCE_LEE_V2_REVIEW.mp4](https://drive.google.com/file/d/1G97YATBOuEaCaSWNBp5yKHHF4NNmzuvn/view) |
| Jennifer Aniston V14 | [JENNIFER_ANISTON_V14_REVIEW.mp4](https://drive.google.com/file/d/1SceS64neDHYKCQyNY1Fn7cINsJVWt9qC/view) |
| Michael Jordan V5 | [MICHAEL_JORDAN_V5_REVIEW.mp4](https://drive.google.com/file/d/1Fe3IzI73zGPLLsK9-6b9h70y_5xq9e79/view) |
| Matt Damon V2 | [MATT_DAMON_V2_REVIEW.mp4](https://drive.google.com/file/d/1Veje99j_7YVfPQ6BOVFBYGobM_w3THuU/view) |
| MrBeast V13 | [MRBEAST_V13_REVIEW.mp4](https://drive.google.com/file/d/1QQMLzwggvzRznMbcEZGeE2ju6Y-_phKO/view) |
| Zendaya V1 / V2 | [V1](https://drive.google.com/file/d/1UfEzV0Kuxl45vhV5-wrGh1eejjKHA58s/view) · [V2](https://drive.google.com/file/d/1r3Rt4Ti2eI-jmfwRd4FtfUcoHqnhoB21/view) · [V2 package](https://drive.google.com/file/d/1RStPD0KPzgErIny-_YYvaFFjlPhmpakx/view) |

How to open a package (Premiere XML or After Effects `.jsx`):
[`docs/delivery/README.md`](docs/delivery/README.md).

## How a video is made — read in this order

1. **[`.claude/skills/celebvid/SKILL.md`](.claude/skills/celebvid/SKILL.md)** — the full playbook.
   Start at **§0 The Standing Rulings** (every rule cost a rejected cut), then
   **RUN IT** (the 10-step pipeline). If you use Claude Code, this file is
   picked up automatically as the `/celebvid` skill when you open this repo.
2. **[`docs/channel/EDIT_RULES.md`](docs/channel/EDIT_RULES.md)** — the owner's edit rules from review.
3. **[`docs/channel/COPYRIGHT_RULES.md`](docs/channel/COPYRIGHT_RULES.md)** and
   **[`docs/delivery/COPYRIGHT_REVIEW_ALL_FILMS.md`](docs/delivery/COPYRIGHT_REVIEW_ALL_FILMS.md)** — clip limits and where each film stands.
4. **[`docs/channel/BRAND.md`](docs/channel/BRAND.md)** + `brand/` — fonts (Anton, Archivo) and brand kit.
5. **`reference/jordan_v1/OWNER_EDITS.txt`** — every instruction the owner gave on one film, and what changed. The best single picture of what "good" means here.

### The pipeline in one screen

| Step | What | Reference script |
|---|---|---|
| 0 | Write the brief (which person, era, second voice) | `BRIEF.md` |
| 1 | Harvest long-form interviews — speech, not b-roll | `fetch_talk.py` |
| 2 | Transcribe everything | `src_transcribe.py` |
| 3 | Mine the subject's own quotes ("bites") | `bites.py` |
| 4 | Write the script around the bites | `script.md`, `quotes.json` |
| 5 | Prove every bite against its audio | `cut_bites.py` |
| 6 | Narration — Kokoro `am_michael` (local, free) | `tts6.py` / `voice.py` |
| 7 | Picture — real footage first | `build5.py` |
| 8 | Photographs pinned to names and eras | `fetch_images.py`, `cues.py` |
| 9 | Graphics — HyperFrames glass cards | `reference/jordan_v1_hyperframes/` |
| 10 | Render, then **watch it** and QC | `card_qc.py`, `contact_sheet.py` |

Hard rules that keep coming back: **no music bed**, Kokoro voice only, pictures
must match the name/era being spoken, no burned-in third-party channel graphics,
every quote verified against the source audio.

## What's in this repo

```
.claude/skills/celebvid/SKILL.md   the playbook (also a Claude Code skill)
docs/channel/                      channel rules, brand, edit rules, shot lists, plans
docs/delivery/                     editor-package guide + copyright review of every film
brand/                             fonts + brand kit
reference/jordan_v1/               Michael Jordan build: scripts, brief, owner edits, quotes
reference/aniston_v2/              Jennifer Aniston build (the "this is fantastic" cut)
reference/jordan_v1_hyperframes/   HyperFrames compositions for the cards
```

Older automated pipeline (v1–v11 era): <https://github.com/avinash753159/ytceleb>.

## Notes

- Paths inside the docs (`C:/Users/avina/...`) point at the owner's machine; the
  same files are in this repo under `reference/`.
- No API keys are included. Narration uses Kokoro, which needs none.
- Footage and renders are **not** in git — they are on Drive.
