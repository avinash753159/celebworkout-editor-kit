# Celeb Workout — format spec, measured off the channel

Source of truth: `REFERENCE_CelebWorkout_Aniston_309k.mp4` (the channel's own
Jennifer Aniston video, 309,000 views, 12:22) plus a current 2026 upload
(Jason Statham, 10:53). Measured, not inferred from a brand document.

**This file overrides `ytceleb/docs/EDIT_RULES.md` wherever they disagree.**
Those rules say "fewer shots, held longer, 8-12s not 4-6" and "fewer shots is
not a compromise, it is the fix." The channel's own most-watched Aniston video
does the exact opposite, and it is the thing being emulated.

## Pacing — the single biggest gap

| | Ref (309k) | Ref (2026) | V3 (mine) |
|---|---|---|---|
| Median shot | **1.4s** | 1.9s | 8.2s |
| Shots < 2s | 62% | 53% | 0% |
| Cut every | 2.3s | 3.0s | 8.2s |
| Total cuts | 323 | 216 | 84 |

Target: **median 1.4-2.0s, 300+ cuts** over ~11 minutes.

## Structure (ref, 12:22)

| Time | Section | Share |
|---|---|---|
| 0:00-0:19 | Channel hook over stock footage, names format + subject | 3% |
| 0:19-0:51 | Subscribe plea — personal, 32s, cites analytics | 4% |
| 0:51-5:46 | Biography — dates, addresses, half-brother, cancelled pilots | 40% |
| 5:46-6:20 | Transition into the routine | 5% |
| 6:20-8:50 | Workout, day by day, read literally with reps | 20% |
| 8:50-11:40 | Diet, read literally as food lists | 23% |
| 11:40-12:22 | Outro — comment ask, like + subscribe | 5% |

The long biography is **correct**, not a retention bug. So is the long
subscribe ask (theirs is 32s at 0:19; V3's was 10.6s at 0:53).

## Footage vocabulary

- **Stock footage of anonymous people is the norm.** A stock yoga model
  performs "TEMPLE POSE, 8 REPS, 8 BREATHS"; the Statham video demos exercises
  with stock gym models. V3's `SUBSTITUTE` quarantine was solving a problem
  this channel does not have — those clips are the format.
- Movie and TV clips used freely (Friends, Ferris Bueller, The Meg).
- Her own interview bites cut in throughout — confirmed on-format.
- Red carpet, paparazzi, magazine and perfume ads, childhood photos, a
  yearbook photo with her circled.
- Generic stock for concepts: hands on a laptop, a town aerial, food on a
  board, a close-up of eyes.
- 1280x720. Mixed, soft, unfussy. Not a premium documentary look.

## Graphics

**Exercise banner** — red diagonal wedge, bottom-right corner, thin white
diagonal separator line, white text, two lines left-aligned inside the wedge:

```
CARDIO              TEMPLE POSE
30 MINUTES          8 REPS, 8 BREATHS
```

Red is a bright pure red (~`#E8121A`), NOT the brand doc's `#B22B1A`.

**Food list** — category header in heavy black type on a white box, top-left;
items below in large white all-caps with a dark edge, one per line, over food
footage:

```
[VEGETABLES]
SPINACH
KALE
BROCCOLI
CELERY
TOMATOES
MUSHROOMS
SWEET POTATOES
```

**Day marker** — white box, red border, day name in black caps.

**Quote bar** — translucent blue bar along the bottom, small white text, for
quotes attributed to her.

No austere black chapter cards. No full-frame minimalist stat cards. No
generated empty-room stills — the channel fills concept beats with cheap
literal stock, not art.

## Narration register

Plain, warm, slightly promotional. Reads lists aloud in full. Examples:

- "the adorable jennifer was born on february 11 1969 in sherman oaks"
- "aniston is also well known for being one of the hottest women alive"
- "so without further ado let's get straight into her workout routine"
- "here is jennifer aniston's workout routine with the daily breakdown"
- "fruits: berries, apples, bananas, peaches, plums, kiwis"

Not literary, not argumentative. It informs; it does not build a thesis.
V3's script was an essay. This is a briefing.
