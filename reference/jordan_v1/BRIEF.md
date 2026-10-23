# Michael Jordan — the locked brief

Episode 2 of Celeb Workout, built on the V12 Aniston pipeline. Everything the
owner has ruled on lives here so it stops being re-litigated.

**Sources:** the two annotated PDFs over the Aniston V11 cut (`JenAniston-Claude.pdf`,
`JenAniston-Claude 2.pdf`, 25 Aug 2026), carried forward verbatim from
`aniston_v2/BRIEF.md`; plus the subject decisions taken 27 Aug 2026.

**This file governs.** Where a skill, an agent or a code comment disagrees with
it, this file is right and the other thing is stale.

---

## 0. One reversal, called out

The brief changed on one point. Both halves are quoted so nobody re-applies the
dead rule from memory:

| Earlier | Now |
|---|---|
| "dont ask for subscribe or like or any of that" | "it doesn't have subscribe and like at the end - which it should or check out our other videos etc" |

**Resolution: the ask goes at the END only.** Never in the opening, never
mid-film. The earlier instruction was about not interrupting; the new one is
about not finishing cold. They are compatible if, and only if, the ask is last.

---

## 1. This episode — decisions taken 27 Aug 2026

| Question | Ruling |
|---|---|
| **Which Michael Jordan** | **The basketball player.** Not Michael B. Jordan the actor — the channel already has a Short on him (`CelebWorkout_Shorts/michael_b_jordan.mp4`, trainer Corey Calliet). Do not let the two collide in search queries, filenames or thumbnails. |
| **Era** | **Prime, 1989–1998.** The Breakfast Club, the rebuild after the Pistons' "Jordan Rules", the second three-peat, the flu game. Not the Wizards comeback, not present-day golf. |
| **Second voice** | **Tim Grover** (personal trainer 1989–1998, *Relentless*) is the primary second voice. **Chip Schaefer** (Bulls athletic trainer, both three-peats) and the **Breakfast Club** — Scottie Pippen, Ron Harper, Randy Brown — are supporting voices. |
| **Run scope** | **Full pipeline, steps 0–10, autonomously.** Stop and report if the bite budget comes in under ~30%. |

### Why the era matters to the harvest

1989–1998 is the only window where the training story is documented in the
subject's own words *and* the trainer's. It is also the window the footage
exists for. A query that returns 2020s golf content or Wizards-era material is
off-brief and should be dropped at the source gate, not left for the picture
stage to notice.

---

## 2. Structure and flow

- **He leads. The narrator bridges.** Every point that can be made in his own
  voice is made in his own voice; narration exists to set up and connect, not to
  read magazine quotations aloud. This is the fix for "doesn't flow well".
- **Intro: about 5 seconds, no more.** A short statement of what the video
  covers. *"we need a bit more intro to what we cover - but very little - like 5
  seconds max."*
- **End: the ask.** Subscribe / like / check out our other videos.
- **Runtime 20–25 minutes.**
- **The script needs work** — it is not a solved problem, it is a named defect.

### The known risk on this subject, stated up front

Jordan is far more guarded than Aniston, and much of his recorded speech is
about winning, opponents and pressure rather than *training and diet*. The
trainer side is the opposite: Grover has hundreds of hours of long-form audio.
**This film may legitimately be trainer-led rather than subject-led**, and that
is a different shape from the Aniston cut. Measure it at step 3 and report the
honest number — bite-seconds ÷ runtime — before writing a script around it. Do
not pad narration to cover a thin harvest.

## 3. Interviews — "straight from the horse's mouth"

- **Find and use as many as possible.** Transcribe the WHOLE library and mine it.
  Do not rely on the handful of quotes somebody already knew about.
- **Search the TRAINERS by name**, as their own sweeps — what they have said in
  their own words, not paraphrased.
- **Report the number that survives READING**, never the number that passes the
  gates. On Aniston that was 71 → 24 on-topic → 22 that survived a read.
- **A face score is not a voice.** See §8.
- **When he is quoted, PLAY THE REAL CLIP.** *"Video doesn't make sense with
  audio - put the real clip."* A quotation over unrelated b-roll is the defect.

## 4. Picture

- **Prefer him TRAINING over him talking.** *"Too many interview videos - it
  should be her working out if possible."* Talking heads are the fallback, not
  the default. For this subject that means the weight room, the 6am sessions,
  practice footage and in-game conditioning — not podium press conferences.
- **Use real photographs** — Nike campaign shots, weight-room stills, magazine
  spreads, Sports Illustrated covers.
- **But EDIT them.** *"you have to edit it so that it looks like there's edit
  done to the video/images."* A photograph dropped in unaltered is a slideshow
  frame.
- **Collages and layered compositions**, not one picture at a time.
- **Parallax and real motion.** *"there needs to be way more effects for pictures
  - like parallax etc - right now it looks like a slideshow."* Reference:
  `github.com/topics/image-effects?l=shaderlab&o=asc&s=forks`

## 5. Graphics / cards

- **FULL FRAME.** *"Make these cards the whole window."* The picture cuts away,
  the data owns the frame, then it cuts back.
- **Every card a different format.** *"Change the format of these cards - they
  all look the same."* Shape follows data: ring, gauge, thermometer, counter,
  bar, split, timeline. `emit()` refuses to write two graphics sharing a `kind`.
- **Show the REAL article.** *"Put the REAL image of the article and what it says
  on there."* Citing Sports Illustrated or ESPN means the actual page on screen,
  not a typographic re-set of the sentence.

## 6. Audio

- **The music must follow the MOOD of the words**, moment to moment. *"the audio
  background doesn't really make sense - change that too - it should be in sync
  with the MOOD of what the transcript is saying."* A block-level table is too
  coarse and is what produced the mismatch.
- **AUDIO LAST.** Build the visual cut on a free draft; paid TTS fires once on
  the locked script.
- **Leave silences.** A build with narration over 92% of runtime and zero pauses
  is exhausting, and no frame-based check can see it.

## 7. Standing rules from earlier, still in force

- Focus on diet, health and workout. It is a workout channel.
- Give as much value as possible; every claim carries its source on screen.
- Copyright is explicitly **not** a concern the owner wants managed.
- Over 10 minutes, always.

## 8. Hard-won rules that must not be re-learned

- **A number improving is not verification.** Look at the frames, or say you did
  not.
- **A face-identity score says who is ON SCREEN, never who is SPEAKING.**
  Compilation channels narrate over celebrity b-roll. Gate on text as well:
  reject runs carrying his name or a reporting verb, and drop whole sources that
  open like a presentation.
- **Sample the MIDDLE of a span, not its end.**
- **Pin timing to WORDS, never to word-count fractions.** Use word-level ASR.
- **Write JSON with `encoding="utf-8"` explicitly.** Windows defaults to cp1252.
- **Long renders do not survive a wrapper that returns.** Render in resumable
  chunks. Never `-shortest` on the final mux.
- **Cache on a content fingerprint**, never on a name or a position.
- **`--no-continue`, and delete stale `.part` files.** A resumed ranged request
  gets 403 Forbidden from YouTube, which reads exactly like a block and is not.
- **Prove every bite against its own audio** — cut it, re-transcribe the cut,
  compare word for word. Nothing ships unverified.
- **Never pillarbox.** Fill the frame with a blurred zoomed copy, sharp version
  on top.

## 9. Subject-specific traps for this episode

- **Two Michael Jordans.** Every search query must be disambiguated. A bare
  "Michael Jordan workout" will return Michael B. Jordan's Creed training.
- **Impostors are the norm here.** Jordan footage is drowned in lookalikes,
  highlight-mix channels and AI-narrated compilations. The per-source
  presentation gate matters more on this subject than it did on Aniston.
- **Era drift.** Wizards-era (2001–03) and present-day Jordan look different
  enough to read as a continuity error inside a 1989–1998 film. Era-lock the
  pools.
- **Burned-in captions and score bugs.** Broadcast basketball footage carries
  network graphics, scorelines and clocks that fight our own labels.
- **The identity reference must be era-matched.** A 2020s Last Dance
  interview frame is a poor reference for 1991 footage. Build the reference
  embedding from frames verified by eye *inside the target era*.
