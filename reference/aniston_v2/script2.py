"""Script v3 — narration plus her own voice.

Three changes from v2, all of them editorial rather than technical.

1. SHE TALKS. v2 was 711 seconds of narrator across a 722 second film, so the
   subject of the documentary never spoke. Six bites are cut in, each one
   verified frame by frame as her on camera saying it — not a caption's
   speaker guess, and not a presenter reading a magazine quote aloud. The
   famous "burnt out and broke my body" line is exactly that second thing: a
   print quote from InStyle read by an Access Hollywood presenter. It stays a
   card, because no footage of her saying it exists.

2. NARRATION NEVER RESTATES A BITE. Where she names the old routine herself,
   the paragraph that used to list spinning and treadmills is gone. What the
   narrator keeps is what she does not supply: dates, mechanism, argument.

3. FOUR FIXED CHAPTERS. THE ROLE, THE WORKOUT, THE DIET, THE RESULTS — the
   permanent channel set, not six invented ones.

Bite windows are in the REAL video timebase and hd/ holds full-length copies,
so local time == real time. Never take a window from raw/: eleven of those
files were pulled through --download-sections and start partway in.
"""
from __future__ import annotations

VOICE_ID = "nPczCjzI2devNBz1zQrb"   # Brian - deep, resonant, middle-aged american
VOICE_SETTINGS = {
    "stability": 0.42,
    "similarity_boost": 0.75,
    "style": 0.30,
    "use_speaker_boost": True,
    "speed": 0.92,
}

# Fixed channel chapters. The film's sections map onto these, not the reverse.
CHAPTERS = [
    ("THE ROLE",    "B04"),
    ("THE WORKOUT", "B09"),
    ("THE DIET",    "B18"),
    ("THE RESULTS", "B20"),
]

# ── bites ────────────────────────────────────────────────────────────────
# id: (source, t0, t1, credit, transcript, why it is here)
# Every window below was checked on frames at its head, middle and tail:
# she is on camera and speaking throughout. Windows that turned out to be a
# reaction shot of the host, or a wide where the speaker is ambiguous, were
# dropped rather than guessed at — see DROPPED_BITES.
BITES = {
 "OLD": ("zbnHO-r5HRs", 29.92, 41.88, "Mondays with Marlo",
         "at least five days a week is great. Changing it up. I get bored "
         "really easily. I mix it up between spinning and yoga, strength "
         "training, circuit training, treadmill training."),
 "PAST40": ("zbnHO-r5HRs", 55.52, 65.84, "Mondays with Marlo",
            "And in my past 40, it's not as easy to drop the LBs, sadly. So "
            "you just have to work a little harder."),
 # tails trimmed after transcribing the cut: 147.60 ran into "and my", and a
 # 147.76 in-point clipped the "My" off "My friend said"
 "INJURY": ("K3puGMuBWKw", 137.12, 147.15, "The Drew Barrymore Show",
            "I was doing harness work hanging from the Eiffel Tower, like you "
            "do. And so anyway, I had a back injury and I couldn't work out."),
 "METHOD": ("K3puGMuBWKw", 147.32, 154.10, "The Drew Barrymore Show",
            "My friend said, you should try Pvolve, because it's functional "
            "exercise. Functional fitness."),
 # VO bite, not sync: her voice runs over the campaign's B-roll, and at this
 # timecode that B-roll is the Pvolve FOUNDER talking to camera. Left alone it
 # reads as though the other woman is saying Aniston's line, so the picture is
 # pointed at her own session instead. Only ever do this where the bite is
 # voiceover - on a sync bite it would slide her lips off her voice.
 "NOTPAIN": ("voC2DxCL6jQ", 30.60, 36.20, "Pvolve",
             "because working out shouldn't be painful. It shouldn't be a chore."),
 "STRONG": ("voC2DxCL6jQ", 50.44, 58.00, "Pvolve",
            "I feel strong from the inside out, and there's nothing more "
            "powerful than that."),
}

# bite key -> (source, t0) to take the PICTURE from instead of the bite's own
# source. Permitted only for voiceover bites, listed in VO_BITES.
VO_BITES = {"NOTPAIN", "STRONG"}
BITE_PICTURE = {
    "NOTPAIN": ("JJLe4jmbrN0", 6.2),
}
for _k in BITE_PICTURE:
    assert _k in VO_BITES, f"{_k} is a sync bite; its picture cannot be swapped"

DROPPED_BITES = {
 ("K3puGMuBWKw", 111.92): "her voice, but the camera is on Drew listening",
 ("K3puGMuBWKw", 162.24): "wide two-shot, cannot confirm which of them says it",
 ("K3puGMuBWKw", 169.04): "wide two-shot, speaker ambiguous",
 ("lLqtWLL5pXw", 196.95): "cheat-day line, but on a wide under a Morning Show banner",
 ("_17zulAlAzw", 15.36): "PRESENTER reading an InStyle print quote — not her voice",
}

# ── blocks ───────────────────────────────────────────────────────────────
# ("VO",   id, argument, narration)
# ("BITE", id, bite_key)
BLOCKS = [

# ── COLD OPEN ─────────────────────────────────────────────────────────────
("VO", "B01", "The routine everyone quotes is one she gave up.",
 "Almost everything you have read about how Jennifer Aniston trains is "
 "describing a routine she does not do any more. The boxing. The jump rope. "
 "The spin bike at five in the morning before a call time. She did all of it, "
 "for the better part of twenty years, and then in twenty twenty-one she "
 "stopped."),

("VO", "B02", "It stopped because of an injury, and what replaced it is easier.",
 "She did not stop because it stopped working. She stopped because she got "
 "hurt, and not in a gym. What replaced it is genuinely easier than what she "
 "was doing at thirty. Shorter. Lower impact. And by most accounts she is in "
 "better shape now, at fifty-seven, than she was when the hard version was "
 "running. Stay with me, because we are going to go through her whole "
 "training history, the exact week she trains on now, movement by movement, "
 "and everything she eats around it."),

("VO", "B03", "The channel ask. Fifteen seconds, not forty-five.",
 "Quick thing before we start. If you get something out of this one, hit "
 "subscribe. It genuinely helps the channel keep making these. Right, let's "
 "get into it."),

# ── THE ROLE ──────────────────────────────────────────────────────────────
("VO", "B04", "She was born into the industry, which is not the same as being handed it.",
 "Jennifer Joanna Aniston was born on the eleventh of February, nineteen "
 "sixty-nine, in Sherman Oaks, California. Acting was the family business. "
 "Her father, John Aniston, was a working actor who spent decades on daytime "
 "television. Her mother, Nancy Dow, had acted too. Her godfather was Telly "
 "Savalas. So she grew up close enough to the industry to see exactly what it "
 "cost, which is a very different thing from being handed a career in it."),

("VO", "B05", "Her training began as a discipline, before it was ever about a body.",
 "The family moved to New York when she was small. She went to the Rudolf "
 "Steiner School on the Upper East Side, and then she did the thing that "
 "actually mattered. She auditioned for, and got into, the High School of "
 "Performing Arts. LaGuardia. The Fame school. That is the first point in "
 "this story where she chose a discipline for herself and then showed up to "
 "it every day, and it is worth marking, because the pattern repeats for the "
 "next forty years."),

("VO", "B06", "Six years of failure is the part that gets skipped.",
 "Then came the part that gets skipped. She graduated, and nothing happened. "
 "For roughly six years she was an actor who could not get a job that stuck. "
 "There were pilots that were made and never aired. There were shows that "
 "were cancelled almost immediately. To pay for it she worked as a "
 "telemarketer, she worked as a bike messenger, she waited tables. She has "
 "been open about how close she came to giving it up. This is not a story "
 "about someone who was discovered. It is a story about someone who did not "
 "leave."),

("VO", "B07", "Friends made her one of the most looked-at women alive, which is the constraint the rest of the film runs on.",
 "And then, in September nineteen ninety-four, a sitcom about six people in "
 "New York went to air, and the ground moved. Friends ran for ten years and "
 "two hundred and thirty-six episodes. Her haircut became a haircut people "
 "asked for by name. She won an Emmy for it, a Golden Globe, a Screen Actors "
 "Guild award. And from that point onward she was one of the most "
 "photographed women on earth, which matters here for one reason. From "
 "nineteen ninety-four onward, her body was public."),

("VO", "B08", "The film career, and the fact she kept working when the story was about her private life.",
 "The films came alongside it and kept coming after it. The Break-Up. Marley "
 "and Me. Horrible Bosses. Cake, in twenty fourteen, where she stripped the "
 "gloss off entirely and got some of the best reviews of her career. She "
 "married twice, and both marriages ended in public, in a decade when the "
 "tabloid industry was at its absolute worst and she was its favourite "
 "subject. Through all of it she kept working. And in twenty nineteen she "
 "came back to television on her own terms, on The Morning Show, not just "
 "starring in it but producing it."),

# ── THE WORKOUT ───────────────────────────────────────────────────────────
("VO", "B09", "The through-line under all of it was the training. Hand straight to her.",
 "So that is the life. Here is the thing that ran underneath all of it, "
 "quietly, for thirty years. The training. And rather than describe the old "
 "version to you, here she is describing it herself, back when it was still "
 "the one she was doing."),

("BITE", "T01", "OLD"),

("VO", "B10", "Name the teacher and the method she did not name.",
 "Every part of that had a name attached to it. The yoga was Mandy Ingber, "
 "from around two thousand and six, and Ingber is not a generic yoga "
 "teacher. She built her own system, which pairs a traditional pose with an "
 "added toning movement, so you are never just holding a shape. Ingber has "
 "said, on the record, that she was training her on set, during production, "
 "not just in a studio between jobs."),

("VO", "B11", "The volume, which is the part she skipped past.",
 "What she says lightly there, and what is worth slowing down on, is the "
 "amount. That number was her floor, not her target. Thirty minutes of "
 "cardio at a time on top of everything else. Pilates. Barre. A workout DVD "
 "in her own living room. And the variety she describes so casually was a "
 "deliberate principle, not a mood. Keeping it different was the point, "
 "because boredom was the thing most likely to stop her."),

("VO", "B12", "Boxing was the one she stayed with, and it is the most intense thing in the whole history.",
 "And then there is boxing. She started working with Leyon Azubuike, a "
 "trainer who co-founded a boxing gym in Santa Monica, and this is the one "
 "she talks about most warmly. She has called it the longest workout she has "
 "ever actually stayed with, other than yoga, and the reason she gives is "
 "mental. Your brain has to work. You are not sitting on a bike. Azubuike's "
 "stated method was to keep changing what she did so that it never got "
 "easier."),

("VO", "B13", "Quantify the old routine, so the change has something to be measured against.",
 "Put a number on that. Three sessions a week at forty-five minutes at the "
 "low end. Seven sessions a week at an hour at the high end. If she had a "
 "five a.m. call time, she trained before it. That is not a celebrity "
 "dabbling. That is a serious training load, sustained across two decades, "
 "on top of a full film and television career. And she was already noticing "
 "what it cost."),

("BITE", "T02", "PAST40"),

("VO", "B14", "The injury. Set it up in one line and get out of the way.",
 "And then, in twenty twenty-one, on a film set, it ended."),

("BITE", "T03", "INJURY"),

("VO", "B15", "The analysis she does not supply: every method she owned was impact.",
 "Here is why that is the whole story. Nothing she had ever done in a workout "
 "caused that. But every single method she owned asked her body to absorb "
 "force. The rope. The bike. The running. The bag. All of it is impact, in "
 "one form or another, and impact was now the one thing her back could not "
 "give her. Most training stories reach that point and describe somebody "
 "pushing through. She did the opposite."),

("BITE", "T04", "METHOD"),

("VO", "B16", "The replacement method, explained mechanically in one paragraph.",
 "Functional fitness is a broad phrase, so here is the mechanical version in "
 "one plain sentence. Instead of loading your body by hitting the ground "
 "harder, you load it by controlling where it is and how far it travels. A "
 "band gets tighter as your limb moves away from the anchor, so the hardest "
 "part of the repetition is the end of the range, not the landing. The "
 "tension stays on the muscle the whole way through, and nothing gets driven "
 "down through a joint. For a back that cannot take a shock, that is the "
 "difference between training and not training at all. She has been working "
 "with a trainer called Dani Coleman for about five years now, and the "
 "sessions run from about fifteen minutes up to about fifty."),

("BITE", "T05", "NOTPAIN"),

("VO", "B17", "The week, flagged as a synthesis before it is delivered.",
 "So here is the week. One thing said plainly first. This schedule is put "
 "together from the methods she has publicly described. It is not a leaked "
 "copy of her private programme, and nobody outside her training has one. "
 "Monday, low impact resistance, lower body. Tuesday, her stated favourite, "
 "a format that blends the cardio into the resistance work instead of "
 "putting it in its own session. Wednesday is the short one. Fifteen "
 "minutes, arms and abs. Thursday, upper body and back, and note that the "
 "back gets trained rather than avoided. Friday, boxing or rope, if the body "
 "allows it, and that condition is doing real work in that sentence. "
 "Saturday, mobility. Sunday, rest."),

("VO", "B18", "The movements, cut to the ones she can actually be seen doing.",
 "Six movements carry it, and you are about to watch her do all six. The "
 "banded lateral raise. Arms out against the band, slow on the way back. The "
 "squat, light dumbbells at the shoulders, heels down. The reverse lunge, "
 "letting the back foot travel so the front leg does the work. The "
 "quadruped leg raise, which is the least impressive thing here and the one "
 "a hip actually needs. The kneeling row, elbow driving back past the ribs "
 "rather than out to the side. And the plank, hips square, for as long as it "
 "stays honest."),

# ── THE DIET ──────────────────────────────────────────────────────────────
("VO", "B19", "The eating pattern, described not prescribed.",
 "The eating is much less complicated than the training. She uses a sixteen "
 "eight fasting window. Eight hours in which she eats, and outside it, water, "
 "black coffee, juice or herbal tea. She has said she noticed a real "
 "difference when she started doing it. Inside the window it is whole food. "
 "Protein, leafy greens, bright vegetables, healthy fats, whole grains. A "
 "representative day runs eggs with avocado, or oatmeal. A chicken burger. A "
 "vegetable lasagna. And she drinks a genuinely large amount of water."),

("VO", "B20", "The two human details that stop it reading like a cleanse.",
 "Two details are worth keeping, because they are the ones that stop this "
 "sounding like a cleanse. On the days she is not eating clean, she eats "
 "Mexican food. And if she gets a late night craving, it is frozen yogurt "
 "with granola on top. That is the honest version, and the honest version is "
 "more useful to you than the tidy one."),

# ── THE RESULTS ───────────────────────────────────────────────────────────
("VO", "B21", "The takeaway, scaled to the viewer, plus the one caution.",
 "So what do you actually take from this. Not the celebrity. The structure. "
 "She trained extremely hard for twenty years, got hurt in a way that had "
 "nothing to do with training, and then had the sense to change the method "
 "instead of abandoning the goal. And the most useful piece of it is the "
 "smallest one. The fifteen minute session. An hour long workout has a "
 "failure mode, which is that on a bad day you do not do a shorter version, "
 "you skip it, and then the week has a hole in it. A fifteen minute session "
 "barely has one. One caution, and I mean it. If you are training around "
 "something that hurts, this is where the celebrity comparison stops and "
 "somebody who can actually examine you begins."),

("BITE", "T06", "STRONG"),

("VO", "B22", "Two options, asked into the comments.",
 "So here is my question for you. Would you rather train the way she did at "
 "thirty. An hour a day, almost every day, all of it impact. Or the way she "
 "trains now. Fifteen minutes, low impact, every single day you can manage "
 "it. Tell me which one in the comments, and I will see you in the next "
 "one."),
]

VO_BLOCKS = [b for b in BLOCKS if b[0] == "VO"]
BITE_BLOCKS = [b for b in BLOCKS if b[0] == "BITE"]


def bite_seconds() -> float:
    return sum(BITES[k][2] - BITES[k][1] for _, _, k in BITE_BLOCKS)


def word_count() -> int:
    return sum(len(b[3].split()) for b in VO_BLOCKS)


def echo_check() -> list[str]:
    """Any narration phrase that restates a bite is a blocker, not a note."""
    hits = []
    stop = {"the", "and", "a", "to", "of", "it", "is", "in", "that", "you",
            "she", "her", "for", "on", "was", "with", "as", "at", "so", "not",
            "up", "out", "my", "i", "be", "this", "there", "they", "have"}
    for _, _, key in BITE_BLOCKS:
        words = [w.strip(".,\"'").lower() for w in BITES[key][4].split()]
        grams = {" ".join(words[i:i + 3]) for i in range(len(words) - 2)
                 if not all(w in stop for w in words[i:i + 3])}
        for _, bid, _, txt in VO_BLOCKS:
            low = " ".join(w.strip(".,\"'").lower() for w in txt.split())
            for g in grams:
                if g in low:
                    hits.append(f"{bid} restates {key}: '{g}'")
    return hits


if __name__ == "__main__":
    w = word_count()
    print(f"VO blocks {len(VO_BLOCKS)}  bites {len(BITE_BLOCKS)}  words {w}")
    print(f"est VO at 150 wpm : {w/150*60:6.1f}s")
    print(f"bites, measured   : {bite_seconds():6.1f}s")
    print(f"est total         : {w/150*60 + bite_seconds():6.1f}s "
          f"= {(w/150*60 + bite_seconds())/60:.1f} min")
    print()
    for e in echo_check() or ["echo check clean"]:
        print(f"  {e}")
