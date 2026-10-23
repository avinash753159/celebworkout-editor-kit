"""Source pool for the Aniston rebuild.

One clip per source, ten seconds maximum, never repeated. That rule is what
forces the pool to be this wide: roughly five minutes of archive in a twelve
minute film needs thirty-plus separate sources, and there is no other lever.

Every entry is a real, published, findable video and every one gets credited
on screen. `era` groups them so the edit can reach for the right decade
instead of whatever is nearest.
"""
from __future__ import annotations

# id, era, rights_holder, what it is
POOL = [
    # ── 1990s / Friends era — the biography act
    ("LzisOKB_sEU", "90s",  "Entertainment Tonight", "21-year-old Aniston, first ET interview"),
    ("Zyy2RUx6BRM", "90s",  "E! News",               "Her first E! interview, rewind"),
    ("sjLDT-hLkFQ", "90s",  "Entertainment Tonight", "Friends co-stars interrupt her 1994 interview"),
    ("9Piy6m3UF3w", "90s",  "TODAY",                 "Friends cast on the show's success, 1994"),
    ("KHmVdNl1cos", "90s",  "NBC 10 WJAR",           "Friends rewind, on the set"),
    ("znYk2xtNXrM", "90s",  "JenniferAniston1013",   "Friends-era interview"),
    ("yf08roeCXXQ", "90s",  "take2markTV",           "Rewind: Friends actress interviews"),

    # ── 2010s — mid-career, the intense-training years
    ("Ny0zaM7RNg0", "2010s", "CBS Sunday Morning",   "On her role in Cake"),
    ("tkYSEbt_3io", "2010s", "Los Angeles Times",    "Cake: on the scars she wears"),
    ("aNAAWzLOEKc", "2010s", "ABC News",             "Cake: 'I went back to class'"),
    ("asBfqGQ7b6E", "2010s", "The Queen Latifah Show", "A different side of Aniston in Cake"),
    ("BZsQtQ-gEw4", "2010s", "The Talk",             "On the We're the Millers workout"),
    ("oZaoendJ5GQ", "2010s", "Kjersti Flaa",         "On stripping and being a mother to her Friends"),

    # ── training and diet, on the record
    ("c_ci5IriLG0", "train", "Entertainment Tonight", "Reveals hardcore workout routine"),
    ("G1HmBSzxXV0", "train", "Good Morning America",  "Workout secrets revealed"),
    ("6a6MDIvrc_o", "train", "Good Morning America",  "Ten moves from her boxing trainer"),
    ("Oc9ufH7lxnw", "train", "Good Morning America",  "Leyon Azubuike full body workout"),
    ("4aA0KiW5tAg", "train", "Us Weekly",             "Inside her gym workouts with her trainer"),
    ("fnTFycw2q1w", "train", "People",                "How to get her arms"),
    ("zbnHO-r5HRs", "train", "marlothomas",           "Weekly exercise routine"),
    ("9vV4ZpxQLZg", "train", "an air21991",           "Azubuike on her training"),
    ("FXywTKuiYnM", "train", "WFSB 3",                "Workout with her personal trainer"),
    ("QqXmrInJFik", "diet",  "BuzzFresh News",        "On noticing a big difference from fasting"),

    # ── the injury and the change — the spine of the film
    ("_17zulAlAzw", "turn",  "Access Hollywood",      "Reveals she broke her body after years of intense workouts"),
    ("K3puGMuBWKw", "turn",  "The Drew Barrymore Show", "How a work injury changed what she does"),
    ("cBZC-8S9b8g", "turn",  "TODAY with Jenna & Sheinelle", "Her current low-impact method, demonstrated"),

    # ── now — 2019 onward, The Morning Show, red carpet
    ("iUVWGBaW1b0", "now",   "CBS Mornings",          "With Reese Witherspoon, interviewed by Gayle King"),
    ("2A2MCCK_pHs", "now",   "Good Morning America",  "On their 25-year friendship"),
    ("lLqtWLL5pXw", "now",   "adamtanswell",          "On morning routines, breakfast and working out"),
    ("qAp9lq2CT5M", "now",   "Harper's Bazaar UK",    "What's really in her beauty bag"),
    ("jHtULFrKa2g", "now",   "Jimmy Kimmel Live",     "Addresses the rumours about her"),
    ("yQVyPITj6Y8", "now",   "The Late Show",         "On her rescue dog Norman"),
    ("Tk07W15MCr0", "now",   "Page Six",              "2024 Emmys red carpet"),
    ("ol-7Wjrk3hk", "now",   "KTLA 5",                "Critics Choice red carpet"),
    ("dO0akkBV8nc", "now",   "Entertainment Tonight", "On a Friends milestone"),
    ("wvO0FMjlnHo", "now",   "LADbible Entertainment", "With Reese Witherspoon, friendship quiz"),
    # ── second wave: added to push archive past 60% of runtime. One clip per
    #    source is the binding constraint, so more minutes means more sources.
    ("EZ11w5SKOXU", "train", "Next9World",            "on hiring her boxing trainer"),
    ("_wUC6czee2s", "now",   "Viral News",            "Golden Globes 2024 red carpet"),
    ("TLY4PFZPbqc", "now",   "Sunday England",        "Emmys 2024 red carpet"),
    ("qhi6QFv303M", "now",   "Apple TV+",             "The Morning Show, in character"),
    ("vPrtuy_4lHM", "now",   "Apple TV+",             "The Morning Show trailer"),
    ("EXQbHPcoack", "now",   "Harper's Bazaar UK",    "Emmys 2024 best dressed"),
    ("Q0Iu0ZZ72Ic", "now",   "Glamour",               "Morning Show cast Q&A"),
    ("hxWPeK2YHLw", "now",   "Vanity Fair",           "Morning Show cast, how well they know each other"),
    ("wyLz-XeJL9o", "now",   "The Hollywood Reporter", "in conversation, Morning Show"),
    ("ZoqjGormrds", "2010s", "Variety",               "Actors on Actors, with Lisa Kudrow"),
    ("BpgMda_4JDI", "2010s", "Armchair Expert",       "long-form interview"),
]


# Long sources: pull a window rather than the whole thing.
WINDOW = {
    "Q0Iu0ZZ72Ic": (60, 300),
    "hxWPeK2YHLw": (60, 300),
    "wyLz-XeJL9o": (120, 420),
    "ZoqjGormrds": (300, 600),
    "BpgMda_4JDI": (600, 900),
    "jHtULFrKa2g": (60, 240),
    "yQVyPITj6Y8": (30, 210),
    "wvO0FMjlnHo": (60, 240),
    "qAp9lq2CT5M": (30, 240),
    "K3puGMuBWKw": (30, 300),
    "znYk2xtNXrM": (30, 270),
}

BY_ID = {p[0]: p for p in POOL}
assert len({p[0] for p in POOL}) == len(POOL), "duplicate source id"

if __name__ == "__main__":
    from collections import Counter
    print(f"{len(POOL)} sources")
    for era, n in Counter(p[1] for p in POOL).most_common():
        print(f"  {era:6} {n}")
    print(f"\nmax archive at 10s/source: {len(POOL)*10/60:.1f} min")
