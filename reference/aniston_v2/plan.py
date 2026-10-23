"""Picture plan. Archive-led.

The rule that shapes everything: one clip per source, nine seconds, never
repeated. So archive is assigned first, block by block, and graphics fill what
is left rather than the other way round. That inversion is the whole
difference from the previous build, where graphics were the picture and
archive did not exist.

The six demonstration clips are RESERVED for the movements block. They are the
only place in the film where a real human performs a named movement, and
spending them earlier as texture is what would leave the payoff to a drawing.
"""
from __future__ import annotations

STYLE = ("shot on 35mm, shallow depth of field, one motivated light source, "
         "natural colour, controlled contrast, mild grain, photographic not "
         "rendered, nobody present, no people, no hands, 16:9")
BLANK = ("every surface completely blank with no lettering, labels, numbering "
         "or branding of any kind anywhere in frame")

# Reserved for B17 only.
DEMO = ["fnTFycw2q1w", "6a6MDIvrc_o", "Oc9ufH7lxnw",
        "FXywTKuiYnM", "cBZC-8S9b8g", "c_ci5IriLG0"]

MOVEMENTS = [
    (1, "Banded Glute Bridge",     "3 × 15",          "Drive through the heels, keep the ribs down."),
    (2, "Standing Hip Abduction",  "3 × 12 each side", "Lift the leg without letting the torso tip."),
    (3, "Slider Reverse Lunge",    "3 × 10 each side", "Let the back foot travel; the front leg works."),
    (4, "Banded Row",              "3 × 12",          "Elbow back past the ribs, not out to the side."),
    (5, "Overhead Press",          "3 × 10",          "Squeeze the glutes so it isn't your low back."),
    (6, "Plank with Slider Reach", "3 × 8 each side", "Hips square; the reach is small and slow."),
    (7, "Dead Bug",                "3 × 8 each side", "Low back into the floor before you reach."),
    (8, "Cat-Cow",                 "2 × 8",           "One vertebra at a time; breath sets the pace."),
    (9, "Jab–Cross",               "3 × 30 sec",      "Rotate the back foot, hand straight back to the chin."),
]

WEEK_ROWS = [
    ("Mon", "Low-impact resistance — lower body", "30–50 min"),
    ("Tue", "Cardio blended into the resistance work", "30–50 min"),
    ("Wed", "Arms and abs, short format", "15 min"),
    ("Thu", "Low-impact resistance — upper body and back", "30–50 min"),
    ("Fri", "Boxing or rope, if the body allows", "20–30 min"),
    ("Sat", "Mobility and stretching", "15–20 min"),
    ("Sun", "Rest", "—"),
]

STILLS = {
    "s_soap":      "A vintage cathode-ray television set switched off in a 1970s living room, close, warm lamp light from one side, muted browns and ochre, " + BLANK,
    "s_school":    "An empty school corridor with worn wooden floors and tall windows, late afternoon light down the length of it, nobody present, muted institutional green, " + BLANK,
    "s_diner":     "A stacked tray of empty coffee cups on a diner counter at closing, one overhead light, everything else dark, muted warm tones, " + BLANK,
    "s_payphone":  "A row of empty theatre seats in a small dark rehearsal room, one work light on the stage beyond, deep shadow, muted grey, " + BLANK,
    "s_yogamat":   "A well-used yoga mat unrolled on a bare studio floor, overhead view, creases and worn patches, soft north light, muted sage and grey, " + BLANK,
    "s_spin":      "A stationary spin bike alone in a dim studio, side on, one cold overhead light, cool grey and deep shadow, plain unbranded machine, " + BLANK,
    "s_treadmill": "A worn rubber tread belt on a treadmill, extreme close and low, decades of shoe scuffs polished into the surface, one hard overhead lamp, cool grey, " + BLANK,
    "s_gloves":    "A pair of worn boxing gloves hanging by their laces against a dark wall, leather cracked from long use, one warm raking light, deep shadow, " + BLANK,
    "s_clock":     "A plain wall clock in a dim empty gym, close, one hard overhead light, cool grey, plain unmarked face with no numerals or branding, " + BLANK,
    "s_set":       "An empty film set at the end of a shooting day, lighting stands and cable runs still in place, one work light burning, everything else dark, wide lens, " + BLANK,
    "s_harness":   "A stunt harness and steel carabiners hanging from a rigging truss in a dark studio, close, scuffed webbing, one hard raking light, cold grey on black, " + BLANK,
    "s_bands":     "Two fabric resistance loop bands and two round gliding discs in a neat flat lay on a pale wooden floor, directly overhead, soft window light, " + BLANK,
    "s_room":      "A corner of a bright living room cleared for training, a mat down and a light band at the edge, low afternoon sun across the floor, nobody there, " + BLANK,
    "s_dumbbell":  "Two light dumbbells standing on end on a pale floor, close and low, one soft window light from the side, matte metal, " + BLANK,
    "s_mat_am":    "A mat already unrolled at the foot of a made bed in a small bedroom, morning light through a half-open blind, warm and quiet, nobody present, " + BLANK,
    "s_plate":     "A plated meal on a plain ceramic dish, grilled chicken, dark leafy greens and roasted vegetables, overhead, soft diffuse daylight, natural colour, " + BLANK,
    "s_eggs":      "Eggs and sliced avocado on toast beside a bowl of oatmeal, overhead, soft morning window light, warm natural colour, plain unmarked crockery, " + BLANK,
    "s_water":     "A tall glass of water and a small cup of black coffee on a plain wooden table, morning light from a window, warm neutral tones, " + BLANK,
    "s_froyo":     "A small bowl of frozen yogurt topped with granola on a kitchen counter at night, one warm lamp overhead, everything else dark, " + BLANK,
}

# block -> ordered shots. kind: arch | still | card | plate
# weight is only used to divide whatever the block's narration leaves over.
PLAN = {
"B01": [("card", "title", 1.15), ("arch", "Tk07W15MCr0", 1.0)],
"B02": [("arch", "_17zulAlAzw", 1.0), ("arch", "K3puGMuBWKw", 1.0),
        ("card", "stat57", 1.0), ("arch", "wyLz-XeJL9o", 1.0)],
"B03": [("card", "subscribe", 1.0)],
"B04": [("card", "ch1", 0.62), ("arch", "LzisOKB_sEU", 1.0),
        ("still", "s_soap", 0.55), ("arch", "Zyy2RUx6BRM", 1.0)],
"B05": [("arch", "yf08roeCXXQ", 1.0), ("still", "s_school", 1.2),
        ("arch", "znYk2xtNXrM", 1.0)],
"B06": [("still", "s_diner", 0.85), ("arch", "KHmVdNl1cos", 1.0),
        ("still", "s_payphone", 0.72), ("arch", "BpgMda_4JDI", 1.0)],
"B07": [("arch", "sjLDT-hLkFQ", 1.0), ("arch", "9Piy6m3UF3w", 1.0),
        ("arch", "dO0akkBV8nc", 1.0), ("card", "stat236", 0.78)],
"B08": [("arch", "Ny0zaM7RNg0", 1.0), ("arch", "aNAAWzLOEKc", 1.0),
        ("arch", "qhi6QFv303M", 0.56), ("arch", "vPrtuy_4lHM", 0.67),
        ("arch", "tkYSEbt_3io", 1.0)],
"B09": [("card", "ch2", 0.72), ("arch", "oZaoendJ5GQ", 1.0)],
"B10": [("arch", "asBfqGQ7b6E", 1.0), ("still", "s_yogamat", 0.86),
        ("arch", "ZoqjGormrds", 1.0), ("card", "ingber", 0.86)],
"B11": [("still", "s_spin", 0.85), ("arch", "zbnHO-r5HRs", 1.0),
        ("still", "s_treadmill", 0.78)],
"B12": [("arch", "G1HmBSzxXV0", 1.0), ("still", "s_gloves", 0.9),
        ("arch", "4aA0KiW5tAg", 1.0), ("arch", "lLqtWLL5pXw", 1.0),
        ("card", "boxquote", 0.55)],
"B13": [("card", "stat37", 0.8), ("arch", "jHtULFrKa2g", 1.0),
        ("still", "s_clock", 0.62)],
"B14": [("arch", "BZsQtQ-gEw4", 1.0), ("still", "s_set", 1.0),
        ("still", "s_harness", 1.0), ("card", "quote_access", 1.6),
        ("arch", "iUVWGBaW1b0", 1.0)],
"B15": [("card", "ch3", 0.55), ("card", "mechanism", 1.25),
        ("still", "s_bands", 0.95), ("arch", "qAp9lq2CT5M", 1.0),
        ("still", "s_mat_am", 0.9)],
"B16": [("card", "week", 1.7), ("arch", "Q0Iu0ZZ72Ic", 1.0),
        ("still", "s_room", 0.95), ("arch", "hxWPeK2YHLw", 1.0),
        ("still", "s_dumbbell", 1.1)],
"B17": [("plate", i, 1.0) for i in range(9)],
"B18": [("card", "ch4", 0.5), ("arch", "yQVyPITj6Y8", 1.0),
        ("still", "s_water", 0.85), ("still", "s_eggs", 0.85),
        ("arch", "ol-7Wjrk3hk", 1.0)],
"B19": [("still", "s_froyo", 0.95), ("arch", "wvO0FMjlnHo", 1.0),
        ("still", "s_plate", 0.75)],
"B20": [("card", "ch5", 0.5), ("arch", "2A2MCCK_pHs", 1.0),
        ("card", "stat15", 0.95), ("arch", "_wUC6czee2s", 1.0),
        ("card", "caution", 1.0)],
"B21": [("card", "question", 1.4), ("card", "end", 0.8)],
}

# B17 pairs six real demonstration clips with three plates over stills.
B17_BACKING = [
    ("arch", "fnTFycw2q1w"), ("arch", "cBZC-8S9b8g"), ("still", "s_bands2"),
    ("arch", "c_ci5IriLG0"), ("arch", "Oc9ufH7lxnw"), ("still", "s_room2"),
    ("still", "s_mat_am2"), ("arch", "6a6MDIvrc_o"), ("arch", "FXywTKuiYnM"),
]

# stills that are second uses of a generated frame - allowed, they cost money
# not rights, but flagged so the reuse is deliberate rather than accidental
ALIAS = {"s_bands2": "s_bands",
         "s_room2": "s_room", "s_mat_am2": "s_mat_am"}


def used_archive() -> list[str]:
    out = []
    for shots in PLAN.values():
        out += [k for kind, k, _ in shots if kind == "arch"]
    out += [k for kind, k in B17_BACKING if kind == "arch"]
    return out


if __name__ == "__main__":
    from clips import CLIPS
    ua = used_archive()
    have = {c[0] for c in CLIPS}
    dupes = [x for x in set(ua) if ua.count(x) > 1]
    print(f"archive used {len(ua)}, unique {len(set(ua))}, available {len(have)}")
    print("DUPLICATE USE:", dupes or "none")
    print("MISSING CLIP :", sorted(set(ua) - have) or "none")
    print("UNUSED CLIP  :", sorted(have - set(ua)) or "none")
    print(f"stills to generate: {len(STILLS)}")
