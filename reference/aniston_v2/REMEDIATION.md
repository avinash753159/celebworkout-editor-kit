# What I got wrong, what I will do, and how it gets checked

Written after V5 review. Every item below is a defect I shipped and reported as
working. The list is ordered by how badly it damages the video.

## Root cause

**I verified aggregates, not content.** Hash counts, luma means, shot-length
medians, pool-consumption stats. Not one of those can see Jimmy Kimmel's face,
a mislabelled exercise, or a competitor's title card. Every failure below is
downstream of that single habit.

Second cause: **I twice edited a call site with a string replace that silently
did not match**, then reported the feature as shipped. The quote bars and the
alternating push-ins both "worked" for a whole build cycle while rendering
nothing.

---

## The failures

| # | Failure | Evidence |
|---|---|---|
| F1 | **The subject is missing from her own video.** Talk-show hosts and co-stars hold frame alone | Kimmel x4, Colbert x3, Reese alone x2, a GMA panel of five strangers, Strahan, Mandy Ingber, stock models |
| F2 | **Her quotes play over other people's faces** | "every Sunday is a cheat day" over Colbert; the Azubuike quote over a GMA panel |
| F3 | **Exercise cards do not match the footage** | BANDED GLUTE BRIDGE over three women standing; CAT COW over someone lying flat; SPIN/ELLIPTICAL over a floor mat; BANDED ROW over Strahan talking |
| F4 | **Same footage recurs; huge material unused** | 25 min of Friends yielded 4 shots; 3 archive clips never used at all |
| F5 | **Competitors' graphics on screen** | "WE'RE THE MILLERS" title, "DIRECTED BY" trailer credits, a "JENNIFER ANISTON" name super, Days of our Lives captions |
| F6 | **Opens on body parts** | first two shots are a leg on a mat and a foot; no face for several seconds |
| F7 | **No awards, no acceptance speeches** | obvious, available material for a celebrity profile; never fetched |
| F8 | **Reported fixes as done without looking** | movement pins, quote bars, push alternation - all announced as working while broken |
| F9 | **Never watched the video end to end** | not once, across five builds |
| F10 | **Never watched the channel properly** | studied two videos; never played mine against theirs |
| F11 | Music never evaluated | one bed, fixed level, never listened to |
| F12 | No captions file, no chapters | narration text exists verbatim |

---

## What I will do

### 1. Verify every window contains her (fixes F1, F2)
Build a **presence index**: sample every candidate window, run face detection,
and record whether a face is present, how large it is, and how many faces.
Windows with no face, or with a dominant face that is not hers, are excluded
from any pool that plays under a line about her. Talk-show sources stay, but
only their windows where she is on screen.

### 2. Pin exercises to verified frames (fixes F3)
Every movement's footage gets looked at as a frame and captioned by hand before
it is allowed into MOVE_FOOTAGE. Where no footage of a movement exists, use a
STILL of that movement rather than unrelated video.

### 3. Use images where video does not exist (fixes F3, F7)
Fetch stills for the awards, the acceptance speeches, the yearbook, childhood
photos, and every named exercise. Wire them into the same pools as video.

### 4. Ban sources by burned-in graphic (fixes F5)
Scan the head and tail of every source for title cards and credits, and exclude
those ranges rather than the whole source.

### 5. Mine the long sources properly (fixes F4)
Spread windows across the full duration of the 25-minute Friends compilation
and the other long clips, instead of clustering at the head.

### 6. Open on her face (fixes F6)
First shot must contain a face above a minimum size. Enforced.

---

## How each gets checked — gates that FAIL THE BUILD

| Gate | Rule | Fixes |
|---|---|---|
| `gate_presence` | Every clip window used under a subject line must be in the presence index with a face present | F1 |
| `gate_quote_face` | Every shot carrying a quote bar must have a verified face | F2 |
| `gate_moves` | Every MOVE_FOOTAGE entry must have a hand-written caption in a review file, and the file must be newer than the pin | F3 |
| `gate_reuse` | No source may exceed N shots or N seconds of runtime | F4 |
| `gate_branding` | No window may fall inside a source's flagged title/credit ranges | F5 |
| `gate_open` | Shot 1 must contain a face occupying >6% of frame | F6 |
| `gate_contact_sheet` | A 40-frame contact sheet must be generated AND read before any "verified" claim | F8, F9 |

**No build is reported as working until every gate passes and I have looked at
the contact sheet.** "The numbers improved" is not a verification.

---

## Iteration plan

Five passes, each ending with a contact-sheet review and a written diff of what
changed:

1. **Presence + branding** - get strangers and competitors' graphics off screen
2. **Exercises** - every card matches its picture, images where video is absent
3. **Material** - awards, speeches, photos; mine the long sources
4. **Polish** - grade, dark frames, music, opening shot
5. **Publish** - captions, chapters, description, thumbnail, final watch
