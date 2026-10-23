# Copyright rules — binding on every Celeb Workout film

These are the owner's rules, stated verbatim, twice, on 3 August 2026. They are
not guidance and they are not tradeable against production convenience.

---

## The three rules

> **1. Avoid using clips longer than 10 seconds.**
>
> **2. Don't repeat the same video clips over and over.**
>
> **3. Also, don't take multiple clips from the same source video.** For example,
> if you're using a 10-minute YouTube video or a movie, only use one short clip
> (under 10 seconds) from that video. Avoid taking another clip from the middle
> or the end of the same video, as that increases the risk of copyright issues.

Rule 3 is the one that gets rationalised away. It has now been broken once in
production and proposed for breaking a second time. It applies to **b-roll and
background footage exactly as it applies to soundbites.** A "background clip" is
a clip.

---

## What this means arithmetically

A source video yields **one** clip of **at most ten seconds**, ever. Therefore:

| Real footage wanted | Distinct source videos required |
|---|---|
| 60 s | 6+ |
| 120 s | 12+ |
| 300 s (5 min) | 30+ |
| 600 s (10 min) | 60+ |

**There is no other lever.** Not "it's only b-roll". Not "it's the same subject".
Not "the trailer is promotional". If the film needs more real footage, the film
needs more sources — that is the entire solution space.

This is exactly the reasoning already recorded in
`dossier/hemsworth/SOURCES.md`:

> The previous film took 8 bites from a single Rogan episode; under this rule it
> needed 14 sources. So the sources come first and the script is written against
> them.

---

## The failure this prevents

YouTube's Content ID matches against a reference file. Taking several clips from
one source multiplies the matched duration against that single reference, which
is what escalates a claim from "negligible" to "actionable". Ten separate
ten-second clips from ten different sources present ten trivial matches. Ten
ten-second clips from one source present a hundred-second match against one
rights holder.

Duration against a single reference is the risk. Not total screen time.

---

## What does NOT consume the budget

- **Print and document sources.** A magazine sentence rendered as a
  `source_highlight`, or a headline as `headline_over`, is not a clip. Unlimited.
  This is the cheapest way to raise the evidence ratio.
- **Our own generated picture.** Costs money, not rights.
- **Licensed stock and CC-BY music**, used per licence with attribution recorded.
- **Brand graphics and cards** rendered locally.

---

## Fair use is a defence, not a permission

Fair use is decided after somebody objects. It is not a setting to enable. The
four factors that matter here:

1. **Purpose** — commentary, criticism and biography are favoured. A clip must
   be *discussed*, not merely shown as wallpaper. A clip used as background
   texture has a weaker claim than the same clip used as evidence for a point
   the narrator is making.
2. **Nature** — published news and interview footage is more favourable than
   unreleased or highly creative work.
3. **Amount** — ten seconds of a five-minute package is small; ten seconds
   taken four times is not.
4. **Market effect** — the strongest factor. Never assemble enough of one source
   that a viewer can skip the original. This is also the owner's editorial note:
   *"I'd rather just watch the original interview — which means your video is
   useless."*

Attribution is not a licence. Crediting a source on screen is correct practice
and strengthens factor 1; it does not create permission.

---

## Production checklist

Before any assemble:

- [ ] Every clip ≤ 10.0 s, measured on the rendered file, not the plan
- [ ] Exactly one clip per source video — assert on `source_id`, count must be 1
- [ ] No moment used twice anywhere in the film
- [ ] Every clip's rights holder credited on screen
- [ ] No third-party burned-in text, bug, lower-third or watermark in frame
- [ ] Music attributed per cue in the description
- [ ] A source that cannot supply its one clip cleanly is dropped, not stretched

`pipeline/hems_script.py` already reports `MULTIPLE CLIPS FROM ONE SOURCE`.
**That line is a blocker, not a warning.** It was printed and ignored on V4 and
V5.

---

## Standing note

When quality and these rules conflict, the rules win and the fix is more
sources. Asking to relax rule 3 is not a legitimate option to put to the owner;
it has been answered twice and the answer is no.
