"""One window per source, chosen by eye off the scan sheets.

Every entry was picked by looking at a frame, not by guessing. `t` is the
in-point in the downloaded file, `d` the duration. Ten seconds is the hard
ceiling and nothing here reaches it.

Two sources were seen and DROPPED rather than used:
  QqXmrInJFik  BuzzFresh - built on midriff before/after comparisons. Body
               scrutiny is the thing this film is arguing against; using it
               as texture would contradict the narration.
  9vV4ZpxQLZg  an air21991 - entirely screenshots of article text, no footage.

Reuploader watermarks (take2markTV, friendscafe.org, JenniferAniston1013) are
treated as a downgrade: those sources are kept only where an official outlet
does not cover the same era, and they are credited to the outlet whose footage
it originally is where that is legible on screen.
"""
from __future__ import annotations

# id, in-point, duration, on-screen credit, what the shot actually is
CLIPS = [
    # ── 1990s
    ("LzisOKB_sEU", 30.0, 9.0, "Entertainment Tonight", "1990 interview, to camera"),
    ("Zyy2RUx6BRM", 96.0, 9.0, "E! News", "early interview, seated"),
    ("sjLDT-hLkFQ", 16.0, 9.0, "Entertainment Tonight", "on the Friends set, 1994"),
    ("9Piy6m3UF3w", 80.0, 9.0, "TODAY", "1994, Friends cast"),
    ("KHmVdNl1cos", 92.0, 9.0, "NBC 10 WJAR", "on set, mid-90s"),
    ("znYk2xtNXrM", 78.0, 9.0, "NBC", "90s talk-show appearance"),
    ("yf08roeCXXQ", 45.0, 9.0, "ABC", "late-90s seated interview"),

    # ── 2010s
    ("Ny0zaM7RNg0", 30.0, 9.0, "CBS Sunday Morning", "on Cake"),
    ("tkYSEbt_3io", 60.0, 9.0, "Los Angeles Times", "Cake press panel"),
    ("aNAAWzLOEKc", 74.0, 9.0, "ABC News", "Cake, live interview"),
    ("asBfqGQ7b6E", 12.0, 9.0, "The Queen Latifah Show", "seated, to camera"),
    ("BZsQtQ-gEw4", 62.0, 9.0, "The Talk", "on training for a role"),
    ("oZaoendJ5GQ", 78.0, 9.0, "Kjersti Flaa", "junket interview"),

    # ── training, on the record
    ("c_ci5IriLG0", 14.0, 9.0, "Entertainment Tonight", "DEMO: training footage, studio floor"),
    ("G1HmBSzxXV0", 86.0, 9.0, "Good Morning America", "hitting pads with her boxing trainer"),
    ("6a6MDIvrc_o", 88.0, 9.0, "Good Morning America", "DEMO: named boxing drills"),
    ("Oc9ufH7lxnw", 62.0, 9.0, "Good Morning America", "DEMO: full-body circuit"),
    ("4aA0KiW5tAg", 24.0, 9.0, "Us Weekly", "trainer on how she trains"),
    ("fnTFycw2q1w", 10.0, 9.0, "People", "DEMO: Ingber demonstrating the yoga pairing"),
    ("zbnHO-r5HRs", 24.0, 9.0, "Marlo Thomas", "on her weekly routine, to camera"),
    ("FXywTKuiYnM", 56.0, 9.0, "WFSB 3", "DEMO: boxing stance and jab"),

    # ── the turn
    ("_17zulAlAzw", 22.0, 9.0, "Access Hollywood", "on burning out and breaking her body"),
    ("K3puGMuBWKw", 52.0, 9.0, "The Drew Barrymore Show", "on the injury that changed it"),
    ("cBZC-8S9b8g", 140.0, 9.0, "TODAY", "DEMO: low-impact resistance work"),

    # ── now
    ("iUVWGBaW1b0", 104.0, 9.0, "CBS Mornings", "with Reese Witherspoon"),
    ("2A2MCCK_pHs", 226.0, 9.0, "Good Morning America", "on the 25-year friendship"),
    ("lLqtWLL5pXw", 20.0, 9.0, "Apple TV+ press", "on morning routines and working out"),
    ("qAp9lq2CT5M", 40.0, 9.0, "Harper's Bazaar UK", "to camera, seated"),
    ("jHtULFrKa2g", 14.0, 9.0, "Jimmy Kimmel Live", "late-night appearance"),
    ("yQVyPITj6Y8", 76.0, 9.0, "The Late Show", "late-night appearance"),
    ("Tk07W15MCr0", 10.0, 9.0, "Page Six", "2024 Emmys red carpet"),
    ("ol-7Wjrk3hk", 70.0, 9.0, "KTLA 5", "Critics Choice red carpet"),
    ("dO0akkBV8nc", 94.0, 9.0, "Entertainment Tonight", "reflective interview"),
    ("wvO0FMjlnHo", 118.0, 9.0, "LADbible Entertainment", "seated, to camera"),
    # ── second wave, picked off NEW_0/NEW_1 scan sheets
    ("_wUC6czee2s", 20.0,  8.0, "Viral News",             "Golden Globes 2024 carpet"),
    ("Q0Iu0ZZ72Ic", 18.0, 9.0, "Glamour",                "Morning Show cast Q&A"),
    ("hxWPeK2YHLw", 104.0, 9.0, "Vanity Fair",            "Morning Show cast"),
    ("wyLz-XeJL9o", 236.0, 9.0, "The Hollywood Reporter", "in conversation, seated"),
    ("ZoqjGormrds", 130.0, 9.0, "Variety",                "Actors on Actors, close"),
    ("BpgMda_4JDI", 60.0,  9.0, "Armchair Expert",        "long-form interview, seated"),
    ("qhi6QFv303M", 74.0, 5.0, "Apple TV+",              "The Morning Show, in character"),
    ("vPrtuy_4lHM", 14.0,  6.0, "Apple TV+",              "The Morning Show, anchor desk"),
]

# Seen and dropped, second wave:
#   EZ11w5SKOXU  aggregator slideshow of stills over a channel logo
#   TLY4PFZPbqc  red carpet reel, almost entirely other people
#   EXQbHPcoack  best-dressed roundup, she is barely in it


DROPPED = {
    "QqXmrInJFik": "built on midriff before/after comparisons - body scrutiny",
    "9vV4ZpxQLZg": "screenshots of article text, no usable footage",
}

BY_ID = {c[0]: c for c in CLIPS}

assert len({c[0] for c in CLIPS}) == len(CLIPS), "a source is used twice"
for _c in CLIPS:
    assert _c[2] <= 10.0, f"{_c[0]} exceeds the ten second ceiling"

if __name__ == "__main__":
    total = sum(c[2] for c in CLIPS)
    print(f"{len(CLIPS)} clips, {len(DROPPED)} sources dropped")
    print(f"archive total {total:.0f}s = {total/60:.1f} min")
    print(f"longest {max(c[2] for c in CLIPS):.0f}s")
