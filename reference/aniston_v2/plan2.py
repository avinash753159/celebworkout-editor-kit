"""Picture plan v3 — relevance is enforced, not intended.

Every block declares which `shows` tags may appear under it, and `check()`
fails the build if a shot's tag is not allowed there. That rule exists because
v2 had no such check and put a Vanity Fair cast panel under a line about her
training, a red carpet under the workout chapter, and a GMA correspondent
under "hitting pads with her boxing trainer".

Two consequences worth stating:

- There is no footage of Aniston boxing. The narration names her boxing
  trainer, so that block runs on her own gym footage and a card, rather than
  on the trainer working with somebody else and letting the viewer assume.
- The nine prescriptive movements are now six, because six is how many the
  footage can actually show her performing. The names were changed to match
  what she does on screen, not the other way round.
"""
from __future__ import annotations

from clips2 import CLIPS

# Which `shows` tags each block may draw on.
ALLOWED = {
    "B01": {"train", "talk_train"},
    "B02": {"train", "talk_train"},
    "B03": {"card"},
    "B04": {"early", "still"},
    "B05": {"early", "still"},
    "B06": {"early", "still"},
    "B07": {"friends", "still"},
    "B08": {"films", "still"},
    "B09": {"talk_train", "train"},
    "B10": {"talk_train", "train", "still"},
    "B11": {"train", "still", "talk_train"},
    "B12": {"train", "still", "talk_train"},
    "B13": {"train", "still", "talk_train"},
    "B14": {"films", "now", "still"},
    "B15": {"train", "talk_train", "now", "still"},
    "B16": {"train"},
    "B17": {"train"},
    "B18": {"train"},
    "B19": {"still"},
    "B20": {"still", "train"},
    "B21": {"train", "still", "talk_train"},
    "B22": {"train"},
}

# The six movements, each named for what she is actually doing on screen.
# Each name was checked against the frame it appears over. Two changed after
# that check: the "slant board squat" window showed a midriff, and the
# "side-lying leg lift" window is a quadruped raise. The names moved to the
# footage rather than the footage being stretched to the names.
MOVES = [
    (1, "Banded Lateral Raise", "Arms out against the band. Slow on the way back."),
    (2, "Dumbbell Squat",       "Weight at the shoulders, heels down, chest up."),
    (3, "Reverse Lunge",        "Let the back foot travel; the front leg works."),
    (4, "Quadruped Leg Raise",  "Unimpressive, and the one a hip actually needs."),
    (5, "Kneeling Row",         "Elbow back past the ribs, not out to the side."),
    (6, "Plank",                "Hips square, for as long as it stays honest."),
]

WEEK_ROWS = [
    ("Mon", "Low-impact resistance - lower body", "30-50 min"),
    ("Tue", "Cardio blended into the resistance work", "30-50 min"),
    ("Wed", "Arms and abs, short format", "15 min"),
    ("Thu", "Low-impact resistance - upper body and back", "30-50 min"),
    ("Fri", "Boxing or rope, if the body allows", "20-30 min"),
    ("Sat", "Mobility and stretching", "15-20 min"),
    ("Sun", "Rest", "-"),
]

A = lambda vid, t: ("arch", (vid, t), 1.0)
S = lambda sid, w=0.85: ("still", sid, w)
C = lambda key, w=1.0: ("card", key, w)
M = lambda i, vid, t: ("move", (i, vid, t), 1.0)

PLAN = {
 # ── cold open
 "B01": [C("title", 1.1), A("lrZKJPVn89s", 1.2)],
 "B02": [A("JJLe4jmbrN0", 14.0), A("lrZKJPVn89s", 6.6),
         C("stat57", 0.9), A("JJLe4jmbrN0", 22.4)],
 "B03": [C("subscribe")],

 # ── THE ROLE
 "B04": [C("ch_role", 0.55), A("LzisOKB_sEU", 31.0), S("s_soap", 0.6),
         A("Zyy2RUx6BRM", 142.0)],
 "B05": [A("LzisOKB_sEU", 70.0), S("s_school", 1.1), A("znYk2xtNXrM", 108.0)],
 "B06": [S("s_diner", 0.9), A("LzisOKB_sEU", 84.0), S("s_payphone", 0.8),
         A("Zyy2RUx6BRM", 228.0)],
 "B07": [A("sjLDT-hLkFQ", 16.0), A("9Piy6m3UF3w", 80.0),
         C("stat236", 0.8), A("KHmVdNl1cos", 102.0)],
 "B08": [A("Ny0zaM7RNg0", 30.0), A("aNAAWzLOEKc", 74.0),
         A("asBfqGQ7b6E", 12.0), A("oZaoendJ5GQ", 78.0)],

 # ── THE WORKOUT
 "B09": [C("ch_workout", 0.6), A("zbnHO-r5HRs", 44.0)],
 "B10": [A("BZsQtQ-gEw4", 62.0), S("s_yogamat", 0.9), A("zbnHO-r5HRs", 68.0)],
 "B11": [S("s_spin", 0.85), A("c_ci5IriLG0", 28.0), S("s_treadmill", 0.8)],
 "B12": [A("c_ci5IriLG0", 4.0), S("s_gloves", 0.9), A("c_ci5IriLG0", 9.0),
         C("boxquote", 0.9)],
 "B13": [C("stat37", 0.85), A("c_ci5IriLG0", 38.0), S("s_clock", 0.7)],
 "B14": [S("s_set", 1.0)],
 "B15": [A("K3puGMuBWKw", 158.0), S("s_harness", 0.9), C("quote_instyle", 1.2)],
 "B16": [A("lrZKJPVn89s", 3.6), A("JJLe4jmbrN0", 11.2), A("lrZKJPVn89s", 9.8),
         A("voC2DxCL6jQ", 10.0), A("f8YLI3POJnM", 25.0), A("lrZKJPVn89s", 13.2)],
 "B17": [C("week", 1.9), A("JJLe4jmbrN0", 2.2), A("qqipyG6bpLA", 3.0),
         A("f8YLI3POJnM", 2.2), A("qqipyG6bpLA", 14.0)],
 "B18": [M(1, "JJLe4jmbrN0", 8.0), M(2, "JJLe4jmbrN0", 18.0),
         M(3, "lrZKJPVn89s", 11.5), M(4, "lrZKJPVn89s", 16.0),
         M(5, "c_ci5IriLG0", 48.0), M(6, "JJLe4jmbrN0", 19.2)],

 # ── THE DIET
 "B19": [C("ch_diet", 0.5), S("s_water", 0.9), S("s_eggs", 0.9),
         S("s_plate", 0.9)],
 "B20": [S("s_froyo", 1.0), S("s_room", 0.8), S("s_dumbbell", 0.8)],

 # ── THE RESULTS
 "B21": [C("ch_results", 0.5), A("lrZKJPVn89s", 24.6), C("stat15", 0.9),
         A("JJLe4jmbrN0", 20.6), S("s_mat_am", 0.8), C("caution", 1.1)],
 "B22": [C("question", 1.3), A("lrZKJPVn89s", 18.4), C("end", 0.8)],
}

TAG = {(c[0], c[1]): c[4] for c in CLIPS}


def check() -> list[str]:
    bad = []
    for bid, shots in PLAN.items():
        allowed = ALLOWED[bid]
        for kind, key, _ in shots:
            if kind == "arch":
                tag = TAG.get(key)
                if tag is None:
                    bad.append(f"{bid}: {key} is not in clips2.CLIPS")
                elif tag not in allowed:
                    bad.append(f"{bid}: {key} shows '{tag}', "
                               f"block allows {sorted(allowed)}")
            elif kind == "move":
                i, vid, t = key
                tag = TAG.get((vid, t))
                if tag != "train":
                    bad.append(f"{bid}: move {i} backed by '{tag}', must be 'train'")
            elif kind == "still" and "still" not in allowed:
                bad.append(f"{bid}: still '{key}' not allowed here")
    return bad


def duplicates() -> list[str]:
    """The same three-second window twice in one film reads as a fault."""
    seen, dupes = {}, []
    for bid, shots in PLAN.items():
        for kind, key, _ in shots:
            k = key if kind == "arch" else (key[1], key[2]) if kind == "move" else None
            if k is None:
                continue
            if k in seen:
                dupes.append(f"{k[0]}@{k[1]} used in {seen[k]} and again in {bid}")
            seen[k] = bid
    return dupes


def used_windows() -> list[tuple[str, float]]:
    out = []
    for shots in PLAN.values():
        for kind, key, _ in shots:
            if kind == "arch":
                out.append(key)
            elif kind == "move":
                out.append((key[1], key[2]))
    return out


if __name__ == "__main__":
    errs = check() + duplicates()
    for e in errs:
        print(f"  RELEVANCE  {e}")
    print(f"\n{len(PLAN)} blocks, {sum(len(v) for v in PLAN.values())} shots")
    uw = used_windows()
    print(f"archive windows used {len(uw)}, distinct {len(set(uw))}")
    unused = sorted({(c[0], c[1]) for c in CLIPS} - set(uw))
    print(f"clips selected but unused: {len(unused)}")
    for u in unused:
        print(f"    {u[0]} @{u[1]}")
    if errs:
        raise SystemExit(1)
    print("\nrelevance check clean")
