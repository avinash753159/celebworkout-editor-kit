# Celeb Workout — the locked brief

Everything the owner has ruled on, in one place, so it stops being re-litigated.
Sources: the two annotated PDFs (`JenAniston-Claude.pdf`, `JenAniston-Claude 2.pdf`,
25 Aug 2026) plus the choices made in session.

**This file governs.** Where a skill, an agent or a code comment disagrees with it,
this file is right and the other thing is stale.

---

## 0. One reversal, called out

The brief changed on one point, and both halves are quoted so nobody re-applies the
old one:

| Earlier | Now |
|---|---|
| "dont ask for subscribe or like or any of that" | "it doesn't have subscribe and like at the end - which it should or check out our other videos etc" |

**Resolution: the ask goes at the END only.** Never in the opening, never mid-film.
The earlier instruction was about not interrupting; the new one is about not
finishing cold. They are compatible if, and only if, the ask is last.

---

## 1. Structure and flow

- **She leads. The narrator bridges.** Every point that can be made in her own voice
  is made in her own voice; narration exists to set up and connect, not to read
  magazine quotations aloud. This is the fix for "doesn't flow well".
- **Intro: about 5 seconds, no more.** A short statement of what the video covers.
  "we need a bit more intro to what we cover - but very little - like 5 seconds max."
- **End: the ask.** Subscribe / like / check out our other videos.
- **Runtime 20–25 minutes.**
- **The script needs work** — it is not a solved problem, it is a named defect.

## 2. Interviews — "straight from the horse's mouth"

- **Find and use as many as possible.** All 194 sources are transcribed under `asr/`;
  `bites.py` mines them. Honest yield, after reading them: **71 pass the gates, but
  only 24 are genuinely on-topic (9.6 min), and 22 survive a read (4.6 min)** - the
  lower band drifts into dogs, films and Friends dialogue. Adding Dani Coleman's own
  on-camera segments takes it to about **6 min of authentic recorded voice**.
- **That is not enough for a 20-25 min film where she leads** - it would still be
  ~70% narrator. The owner's decision, 25 Aug: **go and download more interviews
  first**, then re-mine. The existing library was harvested for B-ROLL, which is why
  it is thin on long-form speech.
- **Search her TRAINER too.** Dani Coleman interviews specifically — what the trainer
  has said in her own words, not paraphrased.
- **A face score is not a voice.** See §7.
- **When she is quoted, PLAY THE REAL CLIP.** "Video doesn't make sense with audio -
  put the real clip." A quotation over unrelated b-roll is the defect.

## 3. Picture

- **Prefer her WORKING OUT over her talking.** "Too many interview videos - it should
  be her working out if possible." Talking heads are the fallback, not the default.
- **Use real photographs** — the Pvolve campaign shots, gym mirror selfies, magazine
  spreads. Google Images is an acceptable source.
- **But EDIT them.** "you have to edit it so that it looks like there's edit done to
  the video/images." A photograph dropped in unaltered is a slideshow frame.
- **Collages and layered compositions**, not one picture at a time.
- **Parallax and real motion.** "there needs to be way more effects for pictures -
  like parallax etc - right now it looks like a slideshow." Reference:
  `github.com/topics/image-effects?l=shaderlab&o=asc&s=forks`

## 4. Graphics / cards

- **FULL FRAME.** "Make these cards the whole window." "Make these the whole screen."
  The picture cuts away, the data owns the frame, then it cuts back.
- **Every card a different format.** "Change the format of these cards - they all look
  the same." One panel template reused for nineteen graphics is the defect. Shape
  follows data: ring, gauge, thermometer, counter, bar, area, split, timeline.
- **Show the REAL article.** "Put the REAL image of the article and what it says on
  there." When citing InStyle, Elle, People, Radio Times — show the actual page or
  web page, not a typographic re-set of the quotation.
- **Style reference:** open white line-art over picture (the reference sheet supplied),
  and full-frame when it is a data moment.

## 5. Audio

- **The music must follow the MOOD of the words.** "the audio background doesn't
  really make sense - change that too - it should be in sync with the MOOD of what
  the transcript is saying."
- Mood is driven by what is being SAID at that moment, not by which chapter it is in.
  A block-level mood table is too coarse — that is what produced the current mismatch.

## 6. Standing rules from earlier, still in force

- Focus on diet, health and workout. It is a workout channel.
- Give as much value as possible; every claim carries its source on screen.
- Copyright is explicitly not a concern the owner wants managed.
- Over 10 minutes, always.

## 7. Hard-won rules that must not be re-learned

- **A number improving is not verification.** Look at the frames, or say you did not.
- **A face-identity score says who is ON SCREEN, never who is SPEAKING.** Compilation
  channels narrate over celebrity b-roll. Gate on text as well: reject runs carrying
  her name or a reporting verb, and drop whole sources that open like a presentation.
- **Sample the MIDDLE of a span, not its end.** Sampling 1.2s before a graphic's exit
  lands on the next topic's first shot and invents defects that are not there.
- **Pin timing to WORDS, never to word-count fractions.** Use word-level ASR times.
- **Write JSON with `encoding="utf-8"` explicitly.** Windows defaults to cp1252 and
  turns an em dash into tofu that the fonts are then blamed for.
- **Long renders do not survive a wrapper that returns.** Render in resumable chunks.
- **Cache on a content fingerprint**, never on a name or a position.

## 8. Named defects from the PDFs, not yet fixed

- **A picture of Matthew Perry is in the cut somewhere.** Owner, p9: *"Also, there's a
  pic of mathew perry in there somewhere."* Confirmed NOT in the 19 harvested
  photographs - every one of those is her alone - so it is a video frame from one of
  the 194 sources. Needs a full sweep of the 365 shots to locate. A workout/diet film
  has no reason to show him at all.
- **The endcard exists but has no ask.** The `CELEB WORKOUT / TRAIN LIKE THE ICONS`
  card is already there; the subscribe / like / other-videos line has to be added TO
  it, not built from nothing.

## 9. The reference material the owner supplied

Do not go looking for these again - they are the supplied answer to "what should this
look like".

| Where | What |
|---|---|
| p5 | Gym mirror selfie, her with Dani Coleman |
| p6 | Her training on the Pvolve mat |
| p7-8 | Pvolve campaign stills - band across chest, dumbbell overhead |
| p10 | VideoHive collage/effects template + `github.com/topics/image-effects` |
| p11-12 | Design-portfolio grid - layered layouts, duotone, device mockups |
| p14-17 | Dani Coleman - with Aniston, solo, and class footage |
| p9 | Google Images `jen aniston workout` - "pretty much a lot from here" |
| p18 | Google search `Dani Coleman` |
