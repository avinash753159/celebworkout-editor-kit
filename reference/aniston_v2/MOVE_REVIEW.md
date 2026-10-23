# Exercise pin review — what is ACTUALLY in each pinned frame

Pass 2. Every frame below was extracted and looked at. This is what is in it,
not what the label claims.

**Result: 2 of 17 correct.** This is the third build in which I have reported
these as matched without looking at them.

| # | Label | Pinned source | What is actually in the frame | Verdict |
|---|---|---|---|---|
| 00 | BANDED GLUTE BRIDGE | cBZC-8S9b8g@96 | Three women **standing up** in the TODAY studio | WRONG |
| 01 | STANDING HIP ABDUCTION | cBZC-8S9b8g@150 | Three women standing, one mid-lunge | WRONG |
| 02 | SLANT BOARD SQUAT | lrZKJPVn89s@7.2 | A midriff close-up. No board, no squat | WRONG |
| 03 | REVERSE LUNGE | lrZKJPVn89s@11.5 | Her face, sweaty, close-up | WRONG |
| 04 | THE FIFTEEN FIFTEEN | G1HmBSzxXV0@130 | A woman hitting pads with a trainer — boxing, not intervals | WRONG |
| 05 | SPIN, ELLIPTICAL OR RUN | G1HmBSzxXV0@100 | A trainer and a woman standing in a gym talking | WRONG |
| 06 | BANDED LATERAL RAISE | JJLe4jmbrN0@8.0 | **Aniston doing a banded lateral raise in class** | CORRECT |
| 07 | KNEELING ROW | c_ci5IriLG0@48 | **Aniston doing a kneeling banded row** | CORRECT |
| 08 | PLANK | JJLe4jmbrN0@19.2 | Her on all fours on the mat — quadruped, not a plank | CLOSE |
| 09 | DEAD BUG | aZiwqY_e9ZQ@60 | Someone in a plank with gliding discs under the feet | WRONG |
| 10 | BANDED ROW | cBZC-8S9b8g@40 | Three women standing with an instructor | WRONG |
| 11 | OVERHEAD PRESS | 6a6MDIvrc_o@70 | A seated man, with a burned-in caption reading **"5: LATERAL DELTOID RAISE"** | WRONG + conflicting text |
| 12 | QUADRUPED LEG RAISE | lrZKJPVn89s@16 | Her standing by curtains, arm raised | WRONG |
| 13 | JUMP ROPE | 6a6MDIvrc_o@110 | Two men in a gym, caption "BUT HERE, I'M PROTECTED BY MY DELTOIDS" | WRONG + conflicting text |
| 14 | PAD WORK | G1HmBSzxXV0@60 | A beauty shot of her face from an advert | WRONG |
| 15 | CAT COW | fnTFycw2q1w@30 | Two women in a push-up position outdoors | WRONG |
| 16 | HIP OPENERS | fnTFycw2q1w@45 | A woman kneeling, looking up | WRONG |

## Why it was wrong

I picked these timecodes from memory of what a source contained, not from the
frame. Two happened to be right. `MOVE_FOOTAGE` was then reported as "pinned to
matching footage" in three separate build reports.

## The fix

The footage does not exist for most of these — she has never been filmed doing
a dead bug or a cat-cow. Per the owner's instruction, use a PICTURE where no
video exists. Each movement gets a generated still that actually depicts it,
and the two correct video pins are kept.
