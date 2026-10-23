"""Shot list v3. Windows are in the REAL video timebase, against hd/.

Three rules replaced the old ones.

RELEVANCE. A clip earns its place by showing what the sentence over it is
about. When the line is about her training, the picture is HER training - not
a correspondent demonstrating her routine, not her trainer with a different
client, not a red carpet. Everything below carries a `shows` tag and
`relevance.py` fails the build if a shot's tag does not match its block.

ONE SOURCE, MANY CLIPS. The old build allowed exactly one clip per source, to
limit rights exposure. That constraint is what pushed it onto red carpets and
cast Q&As while eight workout videos sat unused. It is gone. Sources are now
mined for every good moment in them.

SUBSTITUTES ARE NAMED. Footage where someone else performs her routine is
still useful - as a shot of that person, credited as that person. It is never
cut under a line about her body. See SUBSTITUTE below for the sources that
were mistaken for her in v2.

Offsets: eleven v2 windows were measured against files pulled with
--download-sections, so their timecodes were short by the window start. Those
are corrected here (old_t + window_start) and marked `# +off`.
"""
from __future__ import annotations

# Where the previous build's windowed downloads began, for offset correction.
V2_WINDOW_START = {
    "Q0Iu0ZZ72Ic": 60, "hxWPeK2YHLw": 60, "wyLz-XeJL9o": 120, "ZoqjGormrds": 300,
    "BpgMda_4JDI": 600, "jHtULFrKa2g": 60, "yQVyPITj6Y8": 30, "wvO0FMjlnHo": 60,
    "qAp9lq2CT5M": 30, "K3puGMuBWKw": 30, "znYk2xtNXrM": 30,
}

# Sources where the ROUTINE IS HERS but the BODY ON SCREEN IS NOT.
# v2 cut all six of these as if they were her.
SUBSTITUTE = {
    "G1HmBSzxXV0": "a GMA correspondent trains with Azubuike, not Aniston",
    "6a6MDIvrc_o": "a male GMA reporter demonstrates ten named moves",
    "Oc9ufH7lxnw": "Strahan and Azubuike in a studio; she is not present",
    "FXywTKuiYnM": "Azubuike teaches a local-TV host on a white cyc",
    "fnTFycw2q1w": "Mandy Ingber and a model on a patio",
    "cBZC-8S9b8g": "Olivia Munn, credited on screen as a paid spokesperson",
    "aZiwqY_e9ZQ": "an InStyle host with a Lagree trainer",
    "C03vLBSWJN0": "Pvolve brand film, several models, mostly not her",
}

# Crop insets as fractions of width/height: (left, right, top, bottom).
# Applied before the upscale, to push burned-in bugs off frame. Default kills
# corner bugs; overrides handle lower thirds and stubborn watermarks.
CROP_DEFAULT = (0.06, 0.06, 0.06, 0.10)
CROP = {
    # Depths below were set by looking at the rendered film, not by guessing.
    # Every one of these had its logo still visible at the previous depth.
    "K3puGMuBWKw": (0.17, 0.05, 0.15, 0.13),   # DREW bottom-left + "watch drew weekdays" top-left
    "zbnHO-r5HRs": (0.04, 0.13, 0.05, 0.10),   # marlothomas.com bottom-right
    # A locked two-shot: Witherspoon left in pink, Aniston right in black,
    # for all 236s. Uncropped, the JUICE bite plays both women while only
    # one of them is speaking, and the viewer cannot tell which. This
    # takes the right 1280x720 - her, and none of Witherspoon.
    "lLqtWLL5pXw": (0.333, 0.0, 0.167, 0.167),
    "JJLe4jmbrN0": (0.04, 0.04, 0.04, 0.17),   # Pvolve subtitles along the bottom
    "lrZKJPVn89s": (0.02, 0.02, 0.02, 0.06),   # clean film, minimal trim
    "voC2DxCL6jQ": (0.03, 0.03, 0.03, 0.17),   # Pvolve subtitles
    "f8YLI3POJnM": (0.03, 0.03, 0.03, 0.08),
    "qqipyG6bpLA": (0.03, 0.03, 0.03, 0.08),
    "c_ci5IriLG0": (0.335, 0.335, 0.02, 0.06),  # strips the blue IG side panels
    "2A2MCCK_pHs": (0.06, 0.06, 0.06, 0.16),
    "ol-7Wjrk3hk": (0.06, 0.06, 0.06, 0.18),
    "aNAAWzLOEKc": (0.06, 0.06, 0.06, 0.26),   # ABC News lower third
    "dO0akkBV8nc": (0.07, 0.07, 0.07, 0.12),
    "Ny0zaM7RNg0": (0.06, 0.06, 0.06, 0.12),
    "9Piy6m3UF3w": (0.06, 0.06, 0.06, 0.34),   # big burned-in TODAY caption
    "LzisOKB_sEU": (0.10, 0.16, 0.13, 0.17),   # "1990" top-right, ET + Courtesy bottom
    "Zyy2RUx6BRM": (0.06, 0.14, 0.06, 0.15),   # REWIND bottom-right, E! NEWS
    "BZsQtQ-gEw4": (0.13, 0.14, 0.06, 0.17),   # THE TALK logo bottom-left and right
    "znYk2xtNXrM": (0.08, 0.08, 0.08, 0.12),
    "oZaoendJ5GQ": (0.22, 0.05, 0.16, 0.12),   # "WE'RE THE MILLERS" title top-left
    "asBfqGQ7b6E": (0.06, 0.06, 0.06, 0.14),
    "KHmVdNl1cos": (0.06, 0.08, 0.06, 0.10),
    # ── real archive added in v5. Crops measured off frames, on top of the
    # detected active box (several are letterboxed inside their container).
    "7mM-82tY-ts": (0.08, 0.08, 0.06, 0.34),   # fan-page URL sits lower-centre; 0.20 did not reach it
    "cZh-kPkKcvU": (0.04, 0.04, 0.04, 0.06),
    "XbywiblA1eQ": (0.04, 0.04, 0.04, 0.06),
    "Xm0jeY5Mp5c": (0.04, 0.04, 0.04, 0.06),
    "wR1SuuB-hWI": (0.05, 0.05, 0.05, 0.16),   # "Days Of Our Lives - 2017" caption
    "_K3cpT4-upk": (0.05, 0.05, 0.05, 0.16),   # episode caption along the bottom
    "P3IsUOSHlnU": (0.04, 0.04, 0.05, 0.10),
    "Ws-9ra38AlI": (0.04, 0.04, 0.05, 0.10),
    "JlpIdAmkT_k": (0.05, 0.05, 0.05, 0.12),
    "BrbwSDa3crU": (0.05, 0.05, 0.05, 0.08),
    # ── awards and childhood material (pass 3)
    "e1hAV-ZrRpI": (0.05, 0.05, 0.05, 0.12),   # tbs / SAG-AFTRA bugs
    "nivqKWke94k": (0.05, 0.05, 0.05, 0.14),
    "MpEnM_zYNgo": (0.05, 0.05, 0.05, 0.12),
    "0vy5wFgkP2U": (0.05, 0.05, 0.05, 0.08),
    "yN_Tp10MHmQ": (0.05, 0.05, 0.05, 0.08),
    "D0PDC03Cu5c": (0.06, 0.06, 0.06, 0.10),
    "wXjjzHrpZCQ": (0.06, 0.16, 0.06, 0.16),   # WireImage watermark bottom-right
    "CsLRK1JphL4": (0.05, 0.05, 0.05, 0.10),
}

# Per-WINDOW overrides. c_ci5IriLG0 intercuts pillarboxed phone video with
# full-width Pvolve footage, so a single per-source crop cannot serve both:
# the 33.5% side trim that strips the blue IG panels would gut the wide shot.
CROP_WINDOW = {
    ("c_ci5IriLG0", 48.0): (0.05, 0.05, 0.05, 0.14),
}

# id, t0, dur, credit, shows, description
# `shows` is the relevance tag, checked against the block it is placed in.
CLIPS = [

 # ── HER TRAINING, verified frame by frame as her ─────────────────────────
 ("lrZKJPVn89s",   1.2, 2.4, "Pvolve", "train", "standing reach, curtains"),
 ("lrZKJPVn89s",   3.6, 2.6, "Pvolve", "train", "banded arm work, close"),
 ("lrZKJPVn89s",   6.6, 2.2, "Pvolve", "train", "arms overhead, full body"),
 ("lrZKJPVn89s",   7.2, 1.8, "Pvolve", "train", "feet on the slant board"),
 ("lrZKJPVn89s",   9.8, 2.4, "Pvolve", "train", "P.ball pressed forward, standing"),
 ("lrZKJPVn89s",  11.5, 1.6, "Pvolve", "train", "lunge with band, wide"),
 ("lrZKJPVn89s",  13.2, 1.6, "Pvolve", "train", "feet on the rocker board, close"),
 ("lrZKJPVn89s",  16.0, 2.0, "Pvolve", "train", "side-lying leg lift"),
 ("lrZKJPVn89s",  18.4, 3.0, "Pvolve", "train", "silhouette, amber, moving"),
 ("lrZKJPVn89s",  24.6, 2.4, "Pvolve", "train", "on the mat afterwards, spent"),

 ("JJLe4jmbrN0",   2.2, 2.6, "Pvolve", "train", "arriving, before it starts"),
 ("JJLe4jmbrN0",   6.2, 2.0, "Pvolve", "train", "working, moving on the spot"),
 ("JJLe4jmbrN0",   8.0, 2.4, "Pvolve", "train", "banded lateral raise in class"),
 ("JJLe4jmbrN0",  11.2, 2.2, "Pvolve", "train", "banded arm work, side on"),
 ("JJLe4jmbrN0",  14.0, 2.2, "Pvolve", "train", "her face, mid-effort"),
 ("JJLe4jmbrN0",  16.0, 2.0, "Pvolve", "train", "lunge and step, wide"),
 ("JJLe4jmbrN0",  18.0, 1.8, "Pvolve", "train", "squat holding dumbbells"),
 ("JJLe4jmbrN0",  19.2, 1.8, "Pvolve", "train", "on all fours on the mat"),
 ("JJLe4jmbrN0",  20.6, 2.4, "Pvolve", "train", "face down on the mat, done"),
 ("JJLe4jmbrN0",  22.4, 2.6, "Pvolve", "train", "flat on the numbered mat, arms out"),

 ("c_ci5IriLG0",   4.0, 3.0, "her Instagram", "train", "squatting on the slant board"),
 ("c_ci5IriLG0",   9.0, 3.0, "her Instagram", "train", "mountain climbers on the mat"),
 ("c_ci5IriLG0",  28.0, 2.6, "her Instagram", "train", "push-up position, gym mirror"),
 ("c_ci5IriLG0",  38.0, 4.0, "her Instagram", "train", "collapsed on the mat, done"),
 ("c_ci5IriLG0",  48.0, 3.0, "Pvolve",        "train", "kneeling banded row, side on"),

 ("f8YLI3POJnM",   2.2, 2.6, "Pvolve", "train", "standing, close"),
 ("f8YLI3POJnM",  25.0, 2.6, "Pvolve", "train", "arms overhead, close"),
 ("qqipyG6bpLA",   3.0, 3.0, "her Instagram", "train", "moving behind sheer curtains"),
 ("qqipyG6bpLA",  14.0, 3.0, "her Instagram", "train", "on the numbered mat"),

 # ── HER, TALKING (non-sync cutaways) ─────────────────────────────────────
 ("zbnHO-r5HRs",  44.0, 3.0, "Mondays with Marlo", "talk_train", "on her routine"),
 ("zbnHO-r5HRs",  68.0, 3.0, "Mondays with Marlo", "talk_train", "on stretching"),
 ("K3puGMuBWKw", 158.0, 3.0, "The Drew Barrymore Show", "talk_train", "on being injured"),
 ("K3puGMuBWKw", 186.0, 3.0, "The Drew Barrymore Show", "talk_train", "on turning fifty"),
 ("voC2DxCL6jQ",  10.0, 3.0, "Pvolve", "train", "her equipment, close"),

 # ── 1990s, THE ROLE  (v2 windows, offset-corrected) ──────────────────────
 ("LzisOKB_sEU",  31.0, 3.0, "Entertainment Tonight", "early", "1990 interview, to camera"),
 ("LzisOKB_sEU",  70.0, 3.0, "Entertainment Tonight", "early", "1990 interview, mid-answer"),
 ("LzisOKB_sEU",  84.0, 3.0, "Entertainment Tonight", "early", "1990 interview, close"),
 ("Zyy2RUx6BRM", 142.0, 3.0, "E! News", "early", "early interview, her alone"),
 ("Zyy2RUx6BRM", 228.0, 3.0, "E! News", "early", "early interview, laughing"),
 ("sjLDT-hLkFQ",  16.0, 3.0, "Entertainment Tonight", "friends", "on the Friends set, 1994"),
 ("9Piy6m3UF3w",  80.0, 3.0, "TODAY", "friends", "1994, the cast"),
 ("KHmVdNl1cos", 102.0, 3.0, "NBC 10 WJAR", "friends", "on set, mid-90s"),
 ("KHmVdNl1cos", 216.0, 3.0, "NBC 10 WJAR", "friends", "on set, second angle"),
 ("znYk2xtNXrM", 108.0, 3.0, "NBC", "early", "90s appearance"),          # +off 30

 # ── 2010s, the film career ───────────────────────────────────────────────
 ("Ny0zaM7RNg0",  30.0, 3.0, "CBS Sunday Morning", "films", "on Cake"),
 ("aNAAWzLOEKc",  74.0, 3.0, "ABC News", "films", "Cake, live"),
 ("asBfqGQ7b6E",  12.0, 3.0, "The Queen Latifah Show", "films", "seated, to camera"),
 ("BZsQtQ-gEw4",  62.0, 3.0, "The Talk", "talk_train", "on training for a role"),
 ("oZaoendJ5GQ",  78.0, 3.0, "Kjersti Flaa", "films", "junket"),

 # ── now, reflective ──────────────────────────────────────────────────────
 ("dO0akkBV8nc",  94.0, 3.0, "Entertainment Tonight", "now", "reflective interview"),
 ("wyLz-XeJL9o", 356.0, 3.0, "The Hollywood Reporter", "now", "in conversation"),  # +off 120
 ("ZoqjGormrds", 430.0, 3.0, "Variety", "now", "Actors on Actors, close"),          # +off 300
 ("BpgMda_4JDI", 660.0, 3.0, "Armchair Expert", "now", "long-form, seated"),        # +off 600
 ("qAp9lq2CT5M",  70.0, 3.0, "Harper's Bazaar UK", "now", "to camera"),             # +off 30
 ("iUVWGBaW1b0", 104.0, 3.0, "CBS Mornings", "now", "with Reese Witherspoon"),
]

BY_KEY = {(c[0], c[1]): c for c in CLIPS}

_seen = set()
for _c in CLIPS:
    assert (_c[0], _c[1]) not in _seen, f"duplicate window {_c[0]}@{_c[1]}"
    _seen.add((_c[0], _c[1]))
    assert _c[0] not in SUBSTITUTE, f"{_c[0]} is a substitute, never cut as her"


def crop_of(vid: str, t0: float | None = None) -> tuple[float, float, float, float]:
    if t0 is not None and (vid, t0) in CROP_WINDOW:
        return CROP_WINDOW[(vid, t0)]
    return CROP.get(vid, CROP_DEFAULT)


if __name__ == "__main__":
    from collections import Counter
    print(f"{len(CLIPS)} windows from {len({c[0] for c in CLIPS})} sources")
    for tag, n in Counter(c[4] for c in CLIPS).most_common():
        print(f"  {tag:12} {n:>3}")
    print(f"\n{len(SUBSTITUTE)} sources quarantined as substitutes:")
    for k, v in SUBSTITUTE.items():
        print(f"  {k}  {v}")
