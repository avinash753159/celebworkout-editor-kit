"""Narration, take two.

Rebuilt to the shape of the channel's own biggest Aniston video (12:22,
309,692 views), not to the shape I inferred from male action-star uploads:

  cold open -> short subscribe ask -> LIFE (the long biography act) ->
  WORKOUT MINDSET -> WORKOUT ROUTINE -> DIET -> outro

The biography is back because deleting it was the single worst call in the
first build. The video that worked is seven minutes of biography.

What survives from the first pass is the hook - the routine everyone quotes is
one she gave up after a 2021 injury, and what replaced it is easier. That is
true, checkable, and better than the flattery open the 2022 video used.

Editorial lines held:
  * the commercial low-impact brand is described, never named; the trainers
    are named because who trains her is an editorial fact
  * no calorie target, no macro split, no instruction to fast
  * the injury is stated, never re-enacted, and the production is not named
  * no fertility or relationship speculation anywhere, in any form
  * the weekly schedule is called a synthesis, out loud, before it is given
"""

VOICE_ID = "nPczCjzI2devNBz1zQrb"   # Brian - deep, resonant, middle-aged american
VOICE_SETTINGS = {
    "stability": 0.48,
    "similarity_boost": 0.75,
    "style": 0.32,
    "use_speaker_boost": True,
    "speed": 0.92,
}

CHAPTERS = [
    ("Intro",           "B01"),
    ("Her Life",        "B03"),
    ("Workout Mindset", "B09"),
    ("Workout Routine", "B15"),
    ("Diet Plan",       "B18"),
    ("Time to workout", "B20"),
]

# (block_id, argument, narration)
BLOCKS = [

# ── COLD OPEN ─────────────────────────────────────────────────────────────
("B01", "The routine everyone quotes is one she gave up.",
 "Almost everything you have read about how Jennifer Aniston trains is "
 "describing a routine she does not do any more. The boxing. The jump rope. "
 "The spin bike at five in the morning before a call time. She did all of it, "
 "for the better part of twenty years, and then in twenty twenty-one she "
 "stopped."),

("B02", "It stopped because of an injury, and what replaced it is easier. Promise the whole routine.",
 "She did not stop because it stopped working. She stopped because she got "
 "hurt on a film set, and the thing she was hurt in was her back. What "
 "replaced it is genuinely easier than what she was doing at thirty. Shorter. "
 "Lower impact. And by most accounts she is in better shape now, at "
 "fifty-seven, than she was when the hard version was running. Stay with me, "
 "because we are going to go through her whole life, her whole training "
 "history, the exact week she trains on now, movement by movement, and "
 "everything she eats around it."),

# ── SUBSCRIBE, short, channel convention ──────────────────────────────────
("B03", "The channel ask. Fifteen seconds, not forty-five.",
 "Quick thing before we start. If you get something out of this one, hit "
 "subscribe. It genuinely helps the channel keep making these. Right, let's "
 "get into it."),

# ── LIFE ──────────────────────────────────────────────────────────────────
("B04", "She was born into the industry, which is not the same as being handed it.",
 "Jennifer Joanna Aniston was born on the eleventh of February, nineteen "
 "sixty-nine, in Sherman Oaks, California. Acting was the family business. "
 "Her father, John Aniston, was a working actor who spent decades on daytime "
 "television. Her mother, Nancy Dow, had acted too. Her godfather was Telly "
 "Savalas. So she grew up close enough to the industry to see exactly what it "
 "cost, which is a very different thing from being handed a career in it."),

("B05", "Her training began as a discipline, before it was ever about a body.",
 "The family moved to New York when she was small. She went to the Rudolf "
 "Steiner School on the Upper East Side, a Waldorf school, and then she did "
 "the thing that actually mattered. She auditioned for, and got into, the "
 "High School of Performing Arts. LaGuardia. The Fame school. That is the "
 "first point in this story where she chose a discipline for herself and then "
 "showed up to it every day, and it is worth marking, because the pattern "
 "repeats for the next forty years."),

("B06", "Six years of failure is the part that gets skipped.",
 "Then came the part that gets skipped. She graduated, and nothing happened. "
 "For roughly six years she was an actor who could not get a job that stuck. "
 "There were pilots that were made and never aired. There were shows that "
 "were cancelled almost immediately. To pay for it she worked as a "
 "telemarketer, she worked as a bike messenger, she waited tables. She has "
 "been open about how close she came to giving it up. This is not a story "
 "about someone who was discovered. It is a story about someone who did not "
 "leave."),

("B07", "Friends made her one of the most looked-at women alive, which is the constraint the rest of the film runs on.",
 "And then, in September nineteen ninety-four, a sitcom about six people in "
 "New York went to air, and the ground moved. Friends ran for ten years and "
 "two hundred and thirty-six episodes. It made her famous in a way that is "
 "difficult to describe now. Her haircut became a haircut people asked for by "
 "name. She won an Emmy for it, a Golden Globe, a Screen Actors Guild award. "
 "And from that point onward she was one of the most photographed women on "
 "earth, which matters here for one reason. From nineteen ninety-four onward, "
 "her body was public."),

("B08", "The film career, and the fact she kept working when the story was about her private life.",
 "The films came alongside it and kept coming after it. The Break-Up. Marley "
 "and Me. Horrible Bosses. Cake, in twenty fourteen, where she stripped the "
 "gloss off entirely and got some of the best reviews of her career. She "
 "married twice, and both marriages ended in public, in a decade when the "
 "tabloid industry was at its absolute worst and she was its favourite "
 "subject. Through all of it she kept working. And in twenty nineteen she "
 "came back to television on her own terms, on The Morning Show, not just "
 "starring in it but producing it."),

# ── WORKOUT MINDSET ───────────────────────────────────────────────────────
("B09", "The through-line under all of it was the training.",
 "So that is the life. Here is the thing that ran underneath all of it, "
 "quietly, for thirty years. The training. And to understand why it changed "
 "in twenty twenty-one, you have to understand how hard the old version "
 "actually was."),

("B10", "Yoga was the foundation, and it came with a named teacher and a named method.",
 "It starts with yoga. Somewhere around two thousand and six she began "
 "working with Mandy Ingber, and Ingber is not a generic yoga teacher. She "
 "built her own system, which pairs a traditional yoga pose with an added "
 "toning movement, so you are never just holding a shape. Aniston named her "
 "in Vogue in two thousand and six. A magazine spread that same year "
 "photographed Ingber teaching her the poses directly. And Ingber has said, "
 "on the record, that she was training her on set, during production, not "
 "just in a studio between jobs."),

("B11", "Cardio, and the volume of it.",
 "On top of the yoga there was cardio, and a lot of it. Thirty minutes at a "
 "time, most days of the week, on a spin bike or a treadmill or an elliptical. "
 "There was Pilates. There were barre classes. She has talked about doing a "
 "workout DVD in her own living room. The principle underneath all of it was "
 "variety, and she was explicit about that. Keeping it different was the point."),

("B12", "Boxing was the one she stayed with, and it is the most intense thing in the whole history.",
 "And then there is boxing. She started working with Leyon Azubuike, a trainer "
 "who co-founded a boxing gym in Santa Monica, and this is the one she talks "
 "about most warmly. She has called it the longest workout she has ever "
 "actually stayed with, other than yoga, and the reason she gives is mental. "
 "Your brain has to work. You are not sitting on a bike. Jump rope, pad work, "
 "lat pulldowns, squat to row, military press, wood chops, kettlebell squat to "
 "press. Azubuike's stated method was to keep changing what she did so that it "
 "never got easier."),

("B13", "Quantify the old routine, so the change has something to be measured against.",
 "Put a number on that. Three sessions a week at forty-five minutes at the "
 "low end. Seven sessions a week at an hour at the high end. If she had a five "
 "a.m. call time, she trained before it. That is not a celebrity dabbling. "
 "That is a serious training load, sustained across two decades, on top of a "
 "full film and television career."),

("B14", "The injury, and why it ended a method rather than a habit.",
 "And then, in twenty twenty-one, on a set, it ended. A harness. A rig. The "
 "kind of thing that happens on a film and has nothing to do with a gym. She "
 "has been open about it since, and about how serious it was. Nothing she had "
 "ever done in a workout caused it. But here is the problem, and it is the "
 "whole reason this story is interesting. Every single method she owned asked "
 "her body to absorb force. The rope. The bike. The running. The bag. All of "
 "it is impact, in one form or another, and impact was now the one thing her "
 "back could not give her. Most training stories reach that point and describe "
 "somebody pushing through. She did the opposite. She kept the goal and threw "
 "away the method."),

# ── WORKOUT ROUTINE ───────────────────────────────────────────────────────
("B15", "The replacement method, explained mechanically in one paragraph.",
 "What she moved to is low impact resistance training, and the idea underneath "
 "it is worth one plain sentence. Instead of loading your body by hitting the "
 "ground harder, you load it by controlling where it is and how far it travels. "
 "A band gets tighter as your limb moves away from the anchor, so the hardest "
 "part of the repetition is the end of the range, not the landing. The tension "
 "stays on the muscle the whole way through, and nothing gets driven down "
 "through a joint. For a back that cannot take a shock, that is the difference "
 "between training and not training at all. She has been working with a trainer "
 "called Dani Coleman for about five years now, and the sessions run from about "
 "fifteen minutes up to about fifty."),

("B16", "The week, flagged as a synthesis before it is delivered.",
 "So here is the week. One thing said plainly first. This schedule is put "
 "together from the methods she has publicly described. It is not a leaked copy "
 "of her private programme, and nobody outside her training has one. Monday, "
 "low impact resistance, lower body, thirty to fifty minutes. Tuesday, her "
 "stated favourite, a format that blends the cardio into the resistance work "
 "instead of putting it in its own session. Her words on that one are that you "
 "can hit every part of your body pretty efficiently. Wednesday is the short "
 "one. Fifteen minutes, arms and abs. Thursday, back to resistance, upper body "
 "and back, and note that the back gets trained rather than avoided. Friday, "
 "boxing or rope, if the body allows it, and that condition is doing real work "
 "in that sentence. Saturday, mobility. Sunday, rest."),

("B17", "The nine movements, each with the one cue that makes it work.",
 "Nine movements carry it. One, the banded glute bridge. Three sets of fifteen. "
 "Drive through your heels and keep your ribs down. Two, standing hip abduction "
 "with a band at the ankles. Three sets of twelve each side. Lift the leg "
 "without letting your torso tip away from it. Three, the slider reverse lunge. "
 "Three sets of ten each side. Let the back foot travel and make the front leg "
 "do the work. Four, the banded row. Three sets of twelve. Pull your elbow back "
 "past your ribs, not out to the side. Five, an overhead press, light. Three "
 "sets of ten. Squeeze your glutes so the press does not come out of your lower "
 "back. Six, a plank with a slider reach. Three sets of eight each side. Hips "
 "stay square, and the reach is small and slow. Seven, the dead bug. Three sets "
 "of eight each side. Press your lower back into the floor before you reach, "
 "not after. Eight, cat cow. Two sets of eight, one vertebra at a time, letting "
 "your breath set the pace. And nine, the jab cross. Three rounds of thirty "
 "seconds. Rotate the back foot and snap your hand straight back to your chin."),

# ── DIET ──────────────────────────────────────────────────────────────────
("B18", "The eating pattern, described not prescribed.",
 "The eating is much less complicated than the training. She uses a sixteen "
 "eight fasting window. Eight hours in which she eats, and outside it, water, "
 "black coffee, juice or herbal tea. She has said she noticed a real difference "
 "when she started doing it. Inside the window it is whole food. Protein, leafy "
 "greens, bright vegetables, healthy fats, whole grains. A representative day "
 "runs eggs with avocado, or oatmeal. A chicken burger. A vegetable lasagna. "
 "And she drinks a genuinely large amount of water."),

("B19", "The two human details that stop it reading like a cleanse.",
 "Two details are worth keeping, because they are the ones that stop this "
 "sounding like a cleanse. On the days she is not eating clean, she eats "
 "Mexican food. And if she gets a late night craving, it is frozen yogurt with "
 "granola on top. That is the honest version, and the honest version is more "
 "useful to you than the tidy one."),

# ── OUTRO ─────────────────────────────────────────────────────────────────
("B20", "The takeaway, scaled to the viewer, plus the one caution.",
 "So what do you actually take from this. Not the celebrity. The structure. She "
 "trained extremely hard for twenty years, got hurt in a way that had nothing "
 "to do with training, and then had the sense to change the method instead of "
 "abandoning the goal. And the most useful piece of it is the smallest one. The "
 "fifteen minute session. An hour long workout has a failure mode, which is "
 "that on a bad day you do not do a shorter version, you skip it, and then the "
 "week has a hole in it. A fifteen minute session barely has one. One caution, "
 "and I mean it. If you are training around something that hurts, this is where "
 "the celebrity comparison stops and somebody who can actually examine you "
 "begins."),

("B21", "Two options, asked into the comments.",
 "So here is my question for you. Would you rather train the way she did at "
 "thirty. An hour a day, six days a week, all of it impact. Or the way she "
 "trains now. Fifteen minutes, low impact, every single day you can manage it. "
 "Tell me which one in the comments, and I will see you in the next one."),
]


def word_count() -> int:
    return sum(len(b[2].split()) for b in BLOCKS)


def char_count() -> int:
    return sum(len(b[2]) for b in BLOCKS)


if __name__ == "__main__":
    print(f"blocks {len(BLOCKS)}  words {word_count()}  chars {char_count()}")
    print(f"est at 150 wpm: {word_count()/150:.1f} min")
    for bid, arg, txt in BLOCKS:
        w = len(txt.split())
        print(f"  {bid}  {w:>4}w  ~{w/150*60:>5.1f}s  {arg[:56]}")
