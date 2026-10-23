# Jennifer Aniston V5 — everything that could still be better

Measured against `REFERENCE_CelebWorkout_Aniston_309k.mp4` (309k views).
Current build: `JENNIFER_ANISTON_V5.mp4`, 10:52, 364 shots, median 1.60s.

Ordered within each section by impact. "Measured" means I have a number for it;
"observed" means I saw it; "untested" means I am flagging a gap, not a defect.

---

## A. Devices the reference has and this build does not

| # | Item | Why it matters | Effort |
|---|---|---|---|
| A1 | **Blue quote bar** — her printed quotes as text over footage | Solves the whole "great quote, no footage of her saying it" problem. Recurring branded device. The InStyle "burnt out and broke my body" line has no home right now | S |
| A2 | **TV-in-a-room framing** — archive played on a physical TV | Turns a flat clip into a designed shot AND hides low-resolution sources | M |
| A3 | **Real photographs** — childhood, yearbook, family | The split-screen renderer exists and is being fed generated rooms instead of her face at 5 vs 55 | M |
| A4 | **Real product imagery** — Yogalosophy DVD, Pvolve equipment, magazine covers | The narration names these and shows none of them | S |
| A5 | **Stat cards** — "236 EPISODES", "16:8", "57" | V3 had them, V4/V5 dropped them. The reference puts numbers on screen | S |

## B. Picture quality

| # | Item | Evidence | Effort |
|---|---|---|---|
| B1 | **No grade matching between sources** | brightness stdev 41.8, range 13-246, **90 hard jumps >55 levels** between adjacent shots | M |
| B2 | **13 new archive sources have no crops** | "Days Of Our Lives - 2017" and "Victor Does Not Like Melons" visible on screen | S |
| B3 | **7 near-black frames** | 0:32, 2:14, 3:56, 4:09, 9:26, 9:52 - generated stills are not luminance-gated, only video windows are | S |
| B4 | Residual upscale softness | LzisOKB_sEU 2.0x, G1HmBSzxXV0 1.7x after crop | M |
| B5 | Colour cast varies 25.7% +/- 13.6% between shots | same root cause as B1 | M |

## C. Audio — the least examined part of the film

| # | Item | Evidence | Effort |
|---|---|---|---|
| C1 | **The film never breathes** | reference has **11 silences >0.35s; this has ZERO**. Narration covers 92% of runtime | S |
| C2 | **Music never evaluated** | one synthesised bed, fixed -20dB, whole film. Never listened to | S |
| C3 | No music variation by section | reference shifts between sections | M |
| C4 | No sound design | no accent on graphic entries | M |
| C5 | Bites not EQ-matched to narration | archive audio vs studio TTS sit differently | M |

**Verified good:** loudness -14.8 LUFS (correct for YouTube; the reference is
-23.3 and gets turned up), speaking rate 161 wpm vs their 164, pronunciation of
"P-Volve" / "Kiriakis" / "16-8" all correct, A/V drift 0.009s.

## D. Footage use

| # | Item | Evidence | Effort |
|---|---|---|---|
| D1 | **25 minutes of Friends yielded 4 shots** | Xm0jeY5Mp5c barely touched | S |
| D2 | 3 of 13 archive clips never reached the cut | | S |
| D3 | More archive worth pulling | Smartwater and Aveeno ads, Emmy/SAG acceptance speeches, the Friends reunion | M |
| D4 | Pool usage is tiny | life used 103 of 3148 windows; diet 47 of 11090 | - |

## E. Structure and pacing

| # | Item | Evidence | Effort |
|---|---|---|---|
| E1 | **No end-screen zone** | last 25s is 14 shots of 1.1-2.6s; nowhere calm for YouTube's end cards | S |
| E2 | Cold open could lead with the injury bite | currently the hook describes it; her saying it is stronger | S |
| E3 | No mid-roll re-hook | 10:52 with no restatement of the promise | S |
| E4 | No chapter markers in the description | five clear sections | S |

## F. Text and graphics

| # | Item | Effort |
|---|---|---|
| F1 | **No captions/.srt shipped** — the narration text already exists verbatim | S |
| F2 | Text safe margins not checked at phone size | S |
| F3 | Exercise wedges and food lists appear as hard cuts; reference animates | M |
| F4 | Source credit chips — the reference credits nothing; consider dropping | S |

## G. Publishing

| # | Item | Effort |
|---|---|---|
| G1 | Description with timestamps, not yet written for V5 | S |
| G2 | Thumbnail variants for A/B | S |
| G3 | Vertical Shorts cut-downs for promotion | M |
| G4 | Title variants against their series naming | S |

## H. Verification

| # | Item |
|---|---|
| H1 | **Nobody has watched it end to end, including me.** Every defect that mattered in this project was found by looking, not measuring |
| H2 | No echo check between narration and bites on the V4 script (V3 had one) |
| H3 | No fact-check pass on the claims in the current script |
| H4 | The week is a synthesis; stated on screen, but never re-verified against sources |

---

## If only three things get done

1. **C1 — put pauses in.** Cheapest fix on the list, and a structural problem no
   frame-based check could ever surface.
2. **A1 — the quote bar.** Unlocks material already researched and matches the
   reference's most-used device.
3. **B1 — match the grade.** The single largest contributor to "assembled" rather
   than "produced".
