# Edit rules — from the owner's review of the MrBeast film

Verbatim verdict: *"I thought it was pretty awful. I would never watch that
video."* Every rule below comes from a specific thing he named. These are not
preferences; each one describes a failure he sat through.

---

## R1 — A shot illustrates the ARGUMENT, not a word in the sentence

> *"They'll cling to a word and then create a visual. But if you take the
> context of the entire thing, it's not meshing."*

The failure mode is keyword-triggered literalism: the line contains "cling",
so a shot of clinging appears. The viewer is not listening to words, they are
following an argument.

**Test before a prompt is written:** what is this *paragraph* claiming, and
does the image advance that claim? If the image only connects to one word, it
is wrong even when it is beautiful.

## R2 — Fewer shots, held longer

> *"The visuals are very fragmented. It's not flowing well with the
> narrator."* … *"just images after images."*

Rapid cutting between loosely-related images reads as filler and exhausts the
viewer. **Default hold is 8–12 seconds, not 4–6.** A shot that earns 12
seconds is worth more than three that earn four. This is also cheaper and
faster to produce, so there is no excuse.

## R3 — A bite plays a COMPLETE THOUGHT, or it is not used

> *"Sometimes he'll be speaking and he hasn't finished his sentence and then
> it'll go to the narrator again."*
> *"It'll flash to the interviewer and he'll just say one little 'uh'."*

Never cut away mid-sentence. Never include an interviewer's acknowledgement,
filler or reaction. A bite starts at the beginning of a thought and ends at
the end of one. If the clean thought does not fit inside 10 seconds, the quote
becomes an on-screen document instead.

## R4 — Narration must never restate a bite

> *"The narrator will say something and then it cuts to MrBeast saying the
> exact same thing. If the narrator's not providing value, you don't need the
> narrator."*

The narrator **sets up, frames or moves on**. It never delivers the same
information as the clip beside it, before or after. `pipeline/echo_check.py`
exists for exactly this and was not enforced hard enough. Run it and treat
every hit as a blocker, not a warning.

## R5 — One clip per source, for an editorial reason as well as a legal one

> *"So many clips of the interview were taken from the same one. I'd rather
> just watch the original interview — which means your video is useless."*

Repeatedly returning to one interview invites the viewer to leave and watch
that interview. The YouTube rule and the editorial rule point the same way:
**one clip, one source, one appearance in the film.**

## R6 — Every frame carries the brand

> *"It didn't seem like it was one brand theme. It was just cut and paste."*

Same red, same three type families, same devices, same chapter cards, every
time. See `docs/BRAND.md`. A film assembled from individually-good frames
with no shared identity reads as machine output, which is exactly what he
identified.

## R7 — If the narrator adds nothing, cut the narrator

The hardest one, and the summary of all of it. Every narration block must do
something the picture and the quote cannot: supply context, make a link, land
a judgement, or turn the story. Blocks that merely describe what is on screen
are deleted.

---

## What this changes about production

| Before | After |
|---|---|
| ~135 shots in 12 min | **~90 shots in 14 min** |
| 4–6s average hold | **8–12s average hold** |
| 25 bites, 8 from one source | **2 bites, 2 sources, one clip each** |
| Quotes as clips | **Quotes as on-screen documents** (`source_highlight`) |
| Prompt written per beat | **Prompt written per argument** |

Fewer shots is not a compromise. It is the fix.
