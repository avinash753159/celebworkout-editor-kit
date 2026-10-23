"""Source pools per section, for the fast-cut assembler.

A "reel" is (source_id, start_seconds). The assembler keeps a playhead on each
reel and takes the next 1-2 seconds off it each time that reel comes round, so
consecutive shots from one source are consecutive MOMENTS - continuous action
chopped into pieces, which is what a fast montage actually is. It cuts between
reels every shot.

The SUBSTITUTE quarantine from v3 is GONE. The reference demonstrates
"TEMPLE POSE, 8 REPS, 8 BREATHS" over a stock yoga model who is obviously not
Aniston, and the current Statham video demos every exercise with stock gym
footage. Those clips are the format, not a defect. They live in DEMO below and
are used exactly where the reference uses them: under the exercise wedges.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DUR = json.loads((ROOT / "manifest" / "hd_dur.json").read_text())


def _ok(v: str, t: float) -> bool:
    # a reel needs room for at least two shots off its start point
    return v in DUR and DUR[v] > t + 3.5


# ── her, training (the Pvolve campaign films and her own posts) ──────────
HER_TRAIN = [
    ("lrZKJPVn89s", 1.0), ("lrZKJPVn89s", 6.5), ("lrZKJPVn89s", 13.0),
    ("lrZKJPVn89s", 18.0), ("lrZKJPVn89s", 24.0),
    ("JJLe4jmbrN0", 2.0), ("JJLe4jmbrN0", 7.5), ("JJLe4jmbrN0", 13.0),
    ("JJLe4jmbrN0", 18.0), ("JJLe4jmbrN0", 21.5),
    ("f8YLI3POJnM", 1.5), ("f8YLI3POJnM", 23.5),
    ("qqipyG6bpLA", 2.0), ("qqipyG6bpLA", 13.0), ("qqipyG6bpLA", 24.0),
    ("voC2DxCL6jQ", 8.0), ("voC2DxCL6jQ", 20.0), ("voC2DxCL6jQ", 44.0),
    ("c_ci5IriLG0", 3.0), ("c_ci5IriLG0", 8.0), ("c_ci5IriLG0", 27.0),
    ("c_ci5IriLG0", 37.0), ("c_ci5IriLG0", 47.0),
    ("dADifrjs6Og", 6.0), ("dADifrjs6Og", 30.0), ("dADifrjs6Og", 55.0),
    ("w2X4wxwB-qQ", 8.0), ("w2X4wxwB-qQ", 40.0),
    ("d7hb5JTpbFE", 10.0), ("d7hb5JTpbFE", 45.0),
]

# ── exercise demonstrations. Stock models and correspondents performing the
#    movements, exactly as the reference does it.
DEMO = [
    ("cBZC-8S9b8g", 40.0), ("cBZC-8S9b8g", 95.0), ("cBZC-8S9b8g", 150.0),
    ("cBZC-8S9b8g", 200.0),
    ("G1HmBSzxXV0", 60.0), ("G1HmBSzxXV0", 100.0), ("G1HmBSzxXV0", 130.0),
    ("6a6MDIvrc_o", 30.0), ("6a6MDIvrc_o", 70.0), ("6a6MDIvrc_o", 110.0),
    ("Oc9ufH7lxnw", 45.0), ("Oc9ufH7lxnw", 90.0), ("Oc9ufH7lxnw", 140.0),
    ("FXywTKuiYnM", 60.0), ("FXywTKuiYnM", 120.0), ("FXywTKuiYnM", 180.0),
    ("fnTFycw2q1w", 12.0), ("fnTFycw2q1w", 30.0), ("fnTFycw2q1w", 45.0),
    ("aZiwqY_e9ZQ", 20.0), ("aZiwqY_e9ZQ", 60.0), ("aZiwqY_e9ZQ", 90.0),
    ("C03vLBSWJN0", 3.0), ("C03vLBSWJN0", 14.0), ("C03vLBSWJN0", 26.0),
]

# ── 1990s / early career
EARLY = [
    ("LzisOKB_sEU", 12.0), ("LzisOKB_sEU", 30.0), ("LzisOKB_sEU", 55.0),
    ("LzisOKB_sEU", 70.0), ("LzisOKB_sEU", 84.0),
    ("Zyy2RUx6BRM", 40.0), ("Zyy2RUx6BRM", 96.0), ("Zyy2RUx6BRM", 140.0),
    ("Zyy2RUx6BRM", 200.0), ("Zyy2RUx6BRM", 228.0),
    ("znYk2xtNXrM", 40.0), ("znYk2xtNXrM", 108.0), ("znYk2xtNXrM", 170.0),
]

FRIENDS = [
    ("sjLDT-hLkFQ", 16.0), ("sjLDT-hLkFQ", 60.0), ("sjLDT-hLkFQ", 110.0),
    ("9Piy6m3UF3w", 40.0), ("9Piy6m3UF3w", 80.0), ("9Piy6m3UF3w", 160.0),
    ("KHmVdNl1cos", 40.0), ("KHmVdNl1cos", 102.0), ("KHmVdNl1cos", 168.0),
    ("KHmVdNl1cos", 216.0),
]

FILMS = [
    ("Ny0zaM7RNg0", 20.0), ("Ny0zaM7RNg0", 60.0),
    ("aNAAWzLOEKc", 40.0), ("aNAAWzLOEKc", 74.0), ("aNAAWzLOEKc", 140.0),
    ("asBfqGQ7b6E", 12.0), ("asBfqGQ7b6E", 60.0), ("asBfqGQ7b6E", 110.0),
    ("oZaoendJ5GQ", 40.0), ("oZaoendJ5GQ", 78.0), ("oZaoendJ5GQ", 140.0),
    ("tkYSEbt_3io", 20.0), ("tkYSEbt_3io", 60.0),
    ("vPrtuy_4lHM", 8.0), ("vPrtuy_4lHM", 30.0),
]

NOW = [
    ("dO0akkBV8nc", 40.0), ("dO0akkBV8nc", 94.0), ("dO0akkBV8nc", 160.0),
    ("wyLz-XeJL9o", 120.0), ("wyLz-XeJL9o", 240.0), ("wyLz-XeJL9o", 356.0),
    ("ZoqjGormrds", 200.0), ("ZoqjGormrds", 430.0), ("ZoqjGormrds", 700.0),
    ("BpgMda_4JDI", 200.0), ("BpgMda_4JDI", 400.0), ("BpgMda_4JDI", 660.0),
    ("qAp9lq2CT5M", 40.0), ("qAp9lq2CT5M", 70.0), ("qAp9lq2CT5M", 130.0),
    ("iUVWGBaW1b0", 40.0), ("iUVWGBaW1b0", 104.0),
    ("2A2MCCK_pHs", 60.0), ("2A2MCCK_pHs", 160.0),
    ("Q0Iu0ZZ72Ic", 30.0), ("Q0Iu0ZZ72Ic", 120.0),
    ("hxWPeK2YHLw", 40.0), ("hxWPeK2YHLw", 140.0),
    ("Tk07W15MCr0", 8.0), ("ol-7Wjrk3hk", 40.0), ("_wUC6czee2s", 15.0),
    ("jHtULFrKa2g", 30.0), ("yQVyPITj6Y8", 40.0), ("wvO0FMjlnHo", 60.0),
    ("lLqtWLL5pXw", 40.0), ("lLqtWLL5pXw", 150.0),
]

TURN = [
    ("K3puGMuBWKw", 100.0), ("K3puGMuBWKw", 158.0), ("K3puGMuBWKw", 186.0),
    ("_17zulAlAzw", 20.0), ("_17zulAlAzw", 60.0),
    ("InUyN6CduEA", 30.0), ("InUyN6CduEA", 90.0), ("InUyN6CduEA", 150.0),
    ("XYcNVESFs4Y", 20.0), ("XYcNVESFs4Y", 60.0),
    ("ak5GBTYJArw", 20.0), ("ak5GBTYJArw", 70.0),
    ("zbnHO-r5HRs", 20.0), ("zbnHO-r5HRs", 44.0), ("zbnHO-r5HRs", 68.0),
    ("BZsQtQ-gEw4", 30.0), ("BZsQtQ-gEw4", 62.0), ("BZsQtQ-gEw4", 120.0),
]

TRAINERS = [
    ("zbCniZvVfgQ", 10.0), ("zbCniZvVfgQ", 50.0),
    ("W2A_JiQgHrs", 60.0), ("W2A_JiQgHrs", 200.0), ("W2A_JiQgHrs", 400.0),
    ("zMLEopVAzEE", 60.0), ("zMLEopVAzEE", 300.0), ("zMLEopVAzEE", 550.0),
]

# food stills (generated) - the diet section cuts over these
FOOD_STILLS = [
    "f_berries", "f_apples", "f_bananas", "f_stonefruit", "f_kiwi",
    "f_greens", "f_broccoli", "f_tomatoes", "f_sweetpot", "f_saladbowl",
    "f_chicken", "f_fish", "f_eggs2", "f_turkey",
    "f_quinoa", "f_oats", "f_rice",
    "f_oliveoil", "f_avocado", "f_nuts",
    "f_water2", "f_coffee2", "f_tea", "f_juice",
    "f_lasagna", "f_burger", "f_smoothie", "f_mexican", "f_froyo2", "f_clock",
]

FOOD_BY_CAT = {
    "FRUITS":       ["f_berries", "f_apples", "f_bananas", "f_stonefruit", "f_kiwi"],
    "VEGETABLES":   ["f_greens", "f_broccoli", "f_tomatoes", "f_sweetpot", "f_saladbowl"],
    "PROTEINS":     ["f_chicken", "f_fish", "f_eggs2", "f_turkey"],
    "WHOLE GRAINS": ["f_quinoa", "f_oats", "f_rice"],
    "HEALTHY FATS": ["f_oliveoil", "f_avocado", "f_nuts"],
    "BEVERAGES":    ["f_water2", "f_coffee2", "f_tea", "f_juice"],
}

# ── illustrative material. A reel whose id starts with "still:" or "split:"
# is a generated establishing frame or a side-by-side comparison rather than
# a clip. Interleaving these INTO the pools is the whole point: the reference's
# biography alternates interview / archive / map / split / aerial, while V4's
# ran twenty-four seated interviews in a row and felt static despite cutting
# every 1.6s. Round-robin over a mixed pool produces that alternation for free.
S = lambda name: (f"still:{name}", 0.0)
SP = lambda a, b, la, lb: (f"split:{a}|{b}|{la}|{lb}", 0.0)

PLACE_LABEL = {
    "p_shermanoaks": ("Sherman Oaks", "California, 1969"),
    "p_nycstreet":   ("New York City", "she was six"),
    "p_school":      ("Rudolf Steiner School", "Upper East Side"),
    "p_artschool":   ("LaGuardia", "the Fame school"),
    "p_studio90s":   ("Los Angeles", "1990"),
    "p_diner":       ("Six years", "before Friends"),
}

BIO_TEXTURE = [
    S("p_shermanoaks"), S("p_la70s"), S("p_nycstreet"), S("p_nycskyline"),
    S("p_school"), S("p_artschool"), S("p_corridor"), S("p_studio90s"),
    S("p_soapset"), S("p_diner"), S("p_waitress"), S("p_office"),
    S("p_bike"), S("p_marquee"), S("p_carpet"), S("p_apartment"),
    S("s_soap"), S("s_school"), S("s_diner"), S("s_payphone"), S("s_set"),
    SP("p_la70s", "p_nycstreet", "Los Angeles", "New York"),
    SP("p_soapset", "p_studio90s", "Her father", "Her first job"),
    SP("p_office", "p_waitress", "Telemarketer", "Waitress"),
    SP("p_marquee", "p_carpet", "Six years of nothing", "Then Friends"),
]

# interleave one texture shot between every two interview reels
def _weave(clips, texture):
    out, ti = [], 0
    for i, c in enumerate(clips):
        out.append(c)
        if i % 2 == 1 and ti < len(texture):
            out.append(texture[ti]); ti += 1
    out += texture[ti:]
    return out


# section -> reel pool
POOLS = {
    "hook":          HER_TRAIN + TURN[:6],
    "subscribe":     HER_TRAIN + NOW[:10],
    "life":          _weave(EARLY + FRIENDS + FILMS + NOW[:8], BIO_TEXTURE),
    "turn":          _weave(TURN + HER_TRAIN[:10] + TRAINERS[:4],
                             [S("s_set"), S("s_clock"), S("s_spin"),
                              S("s_treadmill"), S("p_studio90s"), S("p_carpet")]),
    "workout_intro": HER_TRAIN + DEMO[:8],
    "week_intro":    HER_TRAIN + DEMO[:6],
    "week":          DEMO + HER_TRAIN,
    "diet_intro":    NOW[:10] + HER_TRAIN[:6],
    "diet":          NOW[:8],
    "outro":         HER_TRAIN + NOW[:10],
}

for _s, _p in POOLS.items():
    bad = [r for r in _p
           if not r[0].startswith(("still:", "split:")) and not _ok(*r)]
    assert not bad, f"{_s}: reels past end of source: {bad}"


if __name__ == "__main__":
    print(f"{len(POOLS)} sections")
    for s, p in POOLS.items():
        print(f"  {s:<14} {len(p):>3} reels  {len({r[0] for r in p}):>2} sources")
    print(f"\nfood stills {len(FOOD_STILLS)}")
