"""Script v4 — written to the channel's measured format, not to a brand doc.

See REFERENCE_SPEC.md. Every structural choice here is copied off
`REFERENCE_CelebWorkout_Aniston_309k.mp4` (309k views), including the ones
that contradict the ytceleb edit rules:

- The biography is LONG (~40% of runtime). The reference spends five minutes
  on birth dates, schools and cancelled 1990 pilots. V3 cut this down as a
  "retention problem"; that was wrong for this channel.
- The subscribe ask is LONG (~30s) and comes early (~0:20). V3 had 10.6s at
  0:53.
- The routine is READ OUT LITERALLY, day by day, with rep counts, exactly as
  the reference does ("sun salutes, 8 reps, 8 breaths").
- The diet is READ OUT as food lists by category.
- Register is plain and warm, not literary. The reference says "the adorable
  jennifer" and "without further ado". V3 wrote an argumentative essay.

What is NOT copied: the reference predates her 2021 injury and describes the
old spinning/yoga routine as current. The facts here are the researched
current ones (the injury, Pvolve, Dani Coleman, 16:8). Same form, current
content.
"""
from __future__ import annotations

VOICE_ID = "nPczCjzI2devNBz1zQrb"   # Brian
VOICE_SETTINGS = {
    "stability": 0.42,
    "similarity_boost": 0.75,
    "style": 0.30,
    "use_speaker_boost": True,
    "speed": 0.95,
}

# ── her own voice ────────────────────────────────────────────────────────
# Windows verified frame-by-frame in the v3 pass; carried over unchanged.
BITES = {
 "OLD": ("zbnHO-r5HRs", 29.92, 41.88, "Mondays with Marlo",
         "at least five days a week is great. Changing it up. I get bored "
         "really easily. I mix it up between spinning and yoga, strength "
         "training, circuit training, treadmill training."),
 "PAST40": ("zbnHO-r5HRs", 55.52, 65.84, "Mondays with Marlo",
            "And in my past 40, it's not as easy to drop the LBs, sadly. So "
            "you just have to work a little harder."),
 "INJURY": ("K3puGMuBWKw", 137.12, 147.15, "The Drew Barrymore Show",
            "I was doing harness work hanging from the Eiffel Tower, like you "
            "do. And so anyway, I had a back injury and I couldn't work out."),
 "METHOD": ("K3puGMuBWKw", 147.32, 154.10, "The Drew Barrymore Show",
            "My friend said, you should try Pvolve, because it's functional "
            "exercise. Functional fitness."),
 "NOTPAIN": ("voC2DxCL6jQ", 30.60, 36.20, "Pvolve",
             "because working out shouldn't be painful. It shouldn't be a chore."),
 "STRONG": ("voC2DxCL6jQ", 50.44, 58.00, "Pvolve",
            "I feel strong from the inside out, and there's nothing more "
            "powerful than that."),
 "JUICE": ("lLqtWLL5pXw", 70.10, 78.62, "Adam Tanswell interview",
           "I don't do coffee first up. I do a juice first up, and then "
           "coffee about a half hour later after meditation, and then "
           "feed the dogs."),
}
VO_BITES = {"NOTPAIN", "STRONG"}
BITE_PICTURE = {"NOTPAIN": ("JJLe4jmbrN0", 6.2)}

# ── the week, read out loud, in the reference's format ───────────────────
# (day, session label, duration, [(exercise, reps)])
WEEK = [
 ("MONDAY", "Low-impact resistance - lower body", "30-50 MINUTES", [
    ("BANDED GLUTE BRIDGE", "3 SETS OF 15"),
    ("STANDING HIP ABDUCTION", "3 SETS OF 12 EACH SIDE"),
    ("SLANT BOARD SQUAT", "3 SETS OF 12"),
    ("REVERSE LUNGE", "3 SETS OF 10 EACH SIDE")]),
 ("TUESDAY", "Cardio blended into the resistance work", "30-50 MINUTES", [
    ("THE FIFTEEN FIFTEEN", "15 MINUTES EACH"),
    ("SPIN, ELLIPTICAL OR RUN", "INTERVALS")]),
 ("WEDNESDAY", "Arms and abs, the short one", "15 MINUTES", [
    ("BANDED LATERAL RAISE", "3 SETS OF 12"),
    ("KNEELING ROW", "3 SETS OF 12"),
    ("PLANK", "3 ROUNDS OF 30 SECONDS"),
    ("DEAD BUG", "3 SETS OF 8 EACH SIDE")]),
 ("THURSDAY", "Low-impact resistance - upper body and back", "30-50 MINUTES", [
    ("BANDED ROW", "3 SETS OF 12"),
    ("OVERHEAD PRESS", "3 SETS OF 10"),
    ("QUADRUPED LEG RAISE", "3 SETS OF 10 EACH SIDE")]),
 ("FRIDAY", "Boxing or rope, if the body allows it", "20-30 MINUTES", [
    ("JUMP ROPE", "3 ROUNDS"),
    ("PAD WORK", "3 ROUNDS")]),
 ("SATURDAY", "Mobility and stretching", "15-20 MINUTES", [
    ("CAT COW", "2 SETS OF 8"),
    ("HIP OPENERS", "8 BREATHS EACH")]),
 ("SUNDAY", "Rest", "REST DAY", []),
]

# ── the diet, read out loud, by category ─────────────────────────────────
FOODS = [
 ("FRUITS",      ["BERRIES", "APPLES", "BANANAS", "PEACHES", "PLUMS", "KIWIS"]),
 ("VEGETABLES",  ["SPINACH", "KALE", "BROCCOLI", "CELERY", "TOMATOES",
                  "MUSHROOMS", "SWEET POTATOES"]),
 ("PROTEINS",    ["CHICKEN", "TURKEY", "EGGS", "FISH", "LEAN BEEF"]),
 ("WHOLE GRAINS",["QUINOA", "COUSCOUS", "OATS", "BROWN RICE", "WHOLE WHEAT PASTA"]),
 ("HEALTHY FATS",["OLIVE OIL", "AVOCADO", "ALMONDS", "WALNUTS", "SEEDS"]),
 ("BEVERAGES",   ["WATER", "BLACK COFFEE", "HERBAL TEA", "CELERY JUICE"]),
]

# ── blocks ───────────────────────────────────────────────────────────────
# ("VO", id, section, narration) | ("BITE", id, key)
BLOCKS = [

# ── HOOK ─────────────────────────────────────────────────────────────────
("VO", "H1", "hook",
 "The celebrities we feature on this channel all have one thing in common. "
 "They make us question the laws of nature when it comes to body shape and "
 "ageing. Today's superstar got hurt at fifty-two, threw out the routine she "
 "had used for twenty years, and came back fitter than she was at thirty. "
 "We'll be discussing Jennifer Aniston's workout routine and diet plan in "
 "today's video."),

# ── SUBSCRIBE ────────────────────────────────────────────────────────────
("VO", "H2", "subscribe",
 "Just a quick request before we start. Each of these videos takes hours to "
 "research and put together, and believe me, I get it, I hate being "
 "bombarded with requests to subscribe. But most of the people watching this "
 "channel are not subscribed. If you get something out of this one, hit the "
 "like and subscribe button. It genuinely helps us keep making them. Thank "
 "you, and now back to the video."),

# ── LIFE ─────────────────────────────────────────────────────────────────
("VO", "L1", "life",
 "Of course we all know and love Jennifer Aniston, the American actress, "
 "film producer and businesswoman. Jennifer Joanna Aniston was born on the "
 "eleventh of February, nineteen sixty-nine, in Sherman Oaks, California. "
 "Acting was the family business. Her father, John Aniston, was best known "
 "for playing Victor Kiriakis on the NBC soap opera Days of our Lives. Her "
 "mother, Nancy Dow, was an actress too. Her godfather was Telly Savalas, "
 "the star of Kojak."),

("VO", "L2", "life",
 "The family moved to New York City when she was six. She was accepted into "
 "the Rudolf Steiner School, a Waldorf school on the Upper East Side. Her "
 "parents divorced three years later. From her father's second marriage she "
 "has a half brother named Alexander. She began acting at eleven, while she "
 "was still at Waldorf, and went on to the Fiorello H. LaGuardia High School "
 "of Music and Art and Performing Arts, the Fame school, graduating in "
 "nineteen eighty-nine."),

("VO", "L3", "life",
 "Then came the part that usually gets skipped. She moved to Los Angeles, "
 "and for roughly six years success completely eluded her. In nineteen "
 "ninety she was cast in her first television series, Molloy. It aired from "
 "the twenty-fifth of July to the twenty-ninth of August, and was gone. Next "
 "came a television version of Ferris Bueller, first aired that same August "
 "on NBC. It could not last the season. She kept working, in The Edge, in "
 "Muddling Through, and none of them lasted either. To pay for it she "
 "waited tables, worked as a telemarketer, and worked as a bike messenger."),

("VO", "L4", "life",
 "The breakthrough came with Friends, which ran on NBC from the twenty-second "
 "of September nineteen ninety-four to the sixth of May, two thousand and "
 "four. Jennifer played Rachel Green. Two hundred and thirty-six episodes. "
 "The show was an enormous success, and the haircut she wore in it became so "
 "popular that it is still known as The Rachel. Did you know she was not the "
 "first choice for the part? The producers had originally pencilled Courteney "
 "Cox in as Rachel, and Jennifer as Monica. It earned her a Primetime Emmy, a "
 "Golden Globe, and a Screen Actors Guild award."),

("VO", "L5", "life",
 "The films came alongside it and kept coming after it. The Break-Up. Marley "
 "and Me. Horrible Bosses. Cake, in twenty fourteen, where she stripped the "
 "glamour off completely and got some of the best reviews of her career. She "
 "has been one of the highest paid actresses in the industry since the "
 "nineteen nineties. And in twenty nineteen she came back to television on "
 "her own terms with The Morning Show, not just starring in it but producing "
 "it. Aniston is also regularly named one of the most beautiful women alive, "
 "and she has worked extremely hard for that body. So what does Jennifer "
 "Aniston's workout routine actually look like?"),

# ── THE TURN ─────────────────────────────────────────────────────────────
("BITE", "T1", "OLD"),

("VO", "W1", "turn",
 "Here is the part most articles about her get wrong. For about twenty years "
 "Jennifer trained hard, and I mean hard. Yoga with Mandy Ingber. Spinning. "
 "Running. Boxing with Leyon Azubuike. Three to seven sessions a week, forty "
 "five minutes to an hour, and if she had a five a.m. call time, she trained "
 "before it. She was open about what that cost her."),

("BITE", "T2", "PAST40"),

("VO", "W2", "turn",
 "And then in twenty twenty-one, on a film set, it ended."),

("BITE", "T3", "INJURY"),

("VO", "W3", "turn",
 "That was a back injury, and it changed everything, because every method she "
 "owned was impact. The rope. The bike. The running. The bag. All of it drives "
 "force down through the body, and force was the one thing her back could no "
 "longer take. So she did not push through it. She changed the method."),

("BITE", "T4", "METHOD"),

("VO", "W4", "workout_intro",
 "Pvolve is low impact resistance training. Instead of loading your body by "
 "hitting the ground harder, you load it with bands and light weights, so the "
 "tension stays on the muscle the whole way through and nothing gets driven "
 "down through a joint. She has trained with Dani Coleman for about five "
 "years now, and the sessions run from about fifteen minutes up to about "
 "fifty. So without further ado, let's get straight into her workout routine."),

("VO", "W5", "week_intro",
 "One thing first. This schedule is put together from the methods she has "
 "publicly described. It is not a leaked copy of her private programme. Here "
 "is Jennifer Aniston's workout routine, with the daily breakdown."),

# The week is generated from WEEK by expand_week() below.
("WEEK", "WK", "week"),

("BITE", "T5", "NOTPAIN"),

# ── DIET ─────────────────────────────────────────────────────────────────
("VO", "D1", "diet_intro",
 "Of course the workout is nothing without the right diet. Jennifer is one of "
 "a number of celebrities who swear by intermittent fasting. She uses a "
 "sixteen eight window. Sixteen hours without food, and an eight hour window "
 "in which she eats. Fortunately your sleeping hours count as part of the "
 "fast, so in practice it means delaying breakfast until about ten in the "
 "morning. She has said she noticed a big difference just from going those "
 "sixteen hours. Here is the list of food she has said she eats."),

("FOODS", "FD", "diet"),

("VO", "D2", "diet",
 "So what does a representative day actually look like? She breaks the fast "
 "at about ten in the morning, and it is usually eggs with avocado, or "
 "oatmeal, or a smoothie with protein powder, banana and blueberries. Lunch "
 "is a salad with a lean protein in it, or a vegetable lasagna. Dinner is "
 "often a chicken burger, or fish with roasted vegetables. And in between, "
 "there is a very large amount of water."),

("BITE", "T7", "JUICE"),

("VO", "D3", "diet",
 "A few more details worth having. She drinks lemon water every morning as "
 "soon as she wakes up. Lemon water is a good way to start the day hydrated, "
 "and it is high in vitamin C. She has said she does a celery juice first, "
 "and then coffee about half an hour later, not the other way around. She has "
 "also been open about the fact that she has tried a few fad diets over the "
 "years, including the grapefruit diet and Nutrisystem, before she settled "
 "into what she does now."),

("VO", "D4", "diet",
 "And two details are worth keeping, because they are the ones that stop all "
 "of this sounding like a cleanse. On the days she is not eating clean, she "
 "eats Mexican food. And if she gets a late night craving, it is frozen "
 "yogurt with granola on top. That is the honest version, and the "
 "honest version is a lot more "
 "useful to you than the tidy one."),

# ── OUTRO ────────────────────────────────────────────────────────────────
("VO", "O1", "outro",
 "The most useful piece of all this is the smallest one. The fifteen minute "
 "session. An hour long workout has a failure mode, which is that on a bad "
 "day you skip it entirely. A fifteen minute one barely has that problem. And "
 "one caution, which I mean sincerely. If you are training around something "
 "that hurts, this is where the celebrity comparison stops and a professional "
 "begins."),

("BITE", "T6", "STRONG"),

("VO", "O2", "outro",
 "I'd say Jennifer Aniston's body is the result of committing to a rigorous "
 "mix of exercise, nutrition and consistency, for thirty years, through an "
 "injury that would have stopped most people. Sometimes all you need is a "
 "push to get started with your own workout and diet plan, and I hope this "
 "video has given you just that. If it motivated you, or you just love "
 "Jennifer Aniston, leave us a comment below. And as always, thank you for "
 "watching this episode. If you want to see how other celebrities get in "
 "shape, let me know in the comments, and make sure you like and subscribe, "
 "since that helps us make more content like this for you."),
]


def expand_week() -> list[tuple[str, str, str, str]]:
    """The week, spoken the way the reference speaks it: day, session, then
    every exercise with its rep count, read out."""
    out = []
    for day, label, dur, moves in WEEK:
        say = f"{day.capitalize()}. {label}. "
        if moves:
            say += f"{dur.lower()}. "
            say += " ".join(f"{n.capitalize()}, {r.lower()}." for n, r in moves)
        else:
            say += "Rest day. Nothing at all, and that is deliberate."
        out.append((f"WK_{day}", day, say, dur))
    return out


def expand_foods() -> list[tuple[str, str, str]]:
    out = []
    for cat, items in FOODS:
        say = f"{cat.capitalize()}. " + ", ".join(i.capitalize() for i in items) + "."
        out.append((f"FD_{cat.replace(' ', '_')}", cat, say))
    return out


def all_speech() -> list[tuple[str, str, str]]:
    """(block_id, kind, text) in final order, weeks and foods expanded."""
    out = []
    for item in BLOCKS:
        kind = item[0]
        if kind == "VO":
            out.append((item[1], "vo", item[3]))
        elif kind == "BITE":
            out.append((item[1], "bite", item[2]))
        elif kind == "WEEK":
            for bid, day, say, dur in expand_week():
                out.append((bid, "vo", say))
        elif kind == "FOODS":
            for bid, cat, say in expand_foods():
                out.append((bid, "vo", say))
    return out


if __name__ == "__main__":
    sp = all_speech()
    words = sum(len(t.split()) for b, k, t in sp if k == "vo")
    bites = sum(BITES[t][2] - BITES[t][1] for b, k, t in sp if k == "bite")
    est = words / 165 * 60
    print(f"speech blocks {len(sp)}  ({sum(1 for x in sp if x[1]=='bite')} bites)")
    print(f"narration words {words}  est {est:6.1f}s")
    print(f"bites measured        {bites:6.1f}s")
    print(f"est total {est+bites:.0f}s = {(est+bites)/60:.1f} min")
    print()
    for bid, kind, txt in sp:
        if kind == "vo":
            print(f"  {bid:<12} {len(txt.split()):>4}w  ~{len(txt.split())/165*60:5.1f}s")
        else:
            print(f"  {bid:<12} BITE {txt}")


# ── printed quotes ────────────────────────────────────────────────────────
# GONE, deliberately. This used to be a three-entry dict keyed W3/W4/O1
# with the string 'Jennifer Aniston to InStyle' typed into all three
# credits - and the W4 line ("the longest workout I've actually stayed
# with") was said to Good Morning America, not to InStyle. The film was
# printing a fabricated attribution on screen.
#
# The quotes live in quotes.json now, one record each with kind, speaker,
# outlet, source_url and a verification note, and quotecards.py decides
# which of them is carded on which block. Nothing in the picture layer
# invents a credit any more. Do not put a quote back in this file.

