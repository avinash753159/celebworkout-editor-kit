"""Reel pools v5 — every window distinct, by construction.

v4's bug, and it was a bad one: a reel kept a playhead and, when its source ran
out, REWOUND to its start. Short sources therefore replayed the same seconds
every cycle. Measured on the v4 cut: 322 of 365 sampled frames had a
near-duplicate elsewhere in the film, several byte-identical - the frame at
0:00 came back at 5:31. Seven Pvolve files under five minutes total supplied
22% of an eleven minute film.

v5 does not carry playheads at all. It enumerates every usable window in every
source up front, interleaves them by source so consecutive shots differ, and
consumes the list ONCE. A window can therefore never appear twice.

Supply check: 441 minutes of source at one window per SPREAD seconds is a few
thousand windows against ~364 shots needed. Repetition was never a supply
problem; it was a bookkeeping one.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DUR = json.loads((ROOT / "manifest" / "hd_dur.json").read_text())
LUMA = json.loads((ROOT / "manifest" / "luma.json").read_text()) \
    if (ROOT / "manifest" / "luma.json").exists() else {}
LUMA_STEP = 1.5
SPREAD = 3.2            # seconds between candidate windows in one source
HEAD = 3.0              # skip the first seconds (titles, fades)

# Sources barred outright.
BANNED = {
    "znYk2xtNXrM": "320x240 - a 7x upscale to 1080p, mush and grain",
    "yf08roeCXXQ": "take2markTV watermark across the middle of frame",
    "EZ11w5SKOXU": "aggregator slideshow over a channel logo",
    "TLY4PFZPbqc": "red carpet reel, almost entirely other people",
    "EXQbHPcoack": "best-dressed roundup, she is barely in it",
    "9vV4ZpxQLZg": "screenshots of article text, no footage",
    "QqXmrInJFik": "midriff before/after comparisons",
    "dADifrjs6Og": "aggregator repost with a burned-in channel bug; also the "
                   "single most self-similar source in the v5 cut",
    "NP5IP8715vg": "TIME LAPSE captions and a running age counter burned in",
    "w2X4wxwB-qQ": "a design-portfolio showreel, not campaign coverage - it "
                   "carries a full-frame EMINEM magazine spread, which reached "
                   "the V5 cut. Mislabelled by me off its search title.",
    "D0PDC03Cu5c": "320x240 - a 6x upscale, same mush that got znYk2xtNXrM banned",
    "wXjjzHrpZCQ": "318x240 - 6x upscale, plus a WireImage watermark",
    "tkYSEbt_3io": "opens on an LA Times THE ENVELOPE title card",
    # Pass 18, section 4, found by src_ocr.py over every pooled window rather
    # than by a sheet: ALL SIX carry burned-in FRENCH SUBTITLES, full width,
    # one and two lines - "Le film et ses situations sont credibles.", "tu
    # regardes ton courrier, tout est normal, quoi...", "Depuis le debut du
    # tournage jusqu'a ce moment, assis ici,". A subtitle is the most
    # unmistakable foreign text there is and it was in six shots of the V7
    # cut. This is a source ban rather than a window ban because there is no
    # clean window left to save: 6 of 6. Two of them are not even her - 38.2
    # is a film clip with Owen Wilson in it.
    "nZWKuh-Calk": "burned-in French subtitles on every pooled window (6/6)",
    # Pass 19, section 4, found by READING the V9 sheets. A Jonathan Ross
    # clip with Adam Sandler, and it is HARD-SUBTITLED end to end: a large
    # white two-line caption sits across the bottom of the frame in almost
    # every second of it. Shot 330 of the V9 cut is nKHOp72TIso@73.4 and the
    # words "My wrap gift to him." are burned across it, under narration
    # about training. Scanned every 3s from 0 to 108 on qc/s4p19/NKHO_0.jpg
    # and NKHO_1.jpg: of the 32 pooled windows only two samples (87 and 93)
    # were caption-free, and neither gap reaches the 6.4s a shot can run.
    # Same call as nZWKuh-Calk and JJLe4jmbrN0 - there is no clean window
    # left to save, so it is a source ban. It also cuts to pillarboxed
    # paparazzi stills of a MAN on a phone at 48-57, captioned "You are
    # absolutely kidding me.", which the identity gate cannot see.
    "nKHOp72TIso": "burned-in subtitles on almost every pooled window (30/32)",
    # Pass 18, second sweep - found by READING the V8 sheets, not by OCR.
    # Every one of its ten pooled windows carries a large bright
    # "maximotv.com" watermark across the bottom-left quarter. That is not the
    # corner bug this project tolerates (NBC, ellentube, BAZAAR, EdKclips are
    # all small marks in the extreme corner); it is the take2markTV case, an
    # aggregator branding the picture, and take2markTV is already banned for
    # it. Costs one shot. qc/groups/SCAN_V8FIX.jpg.
    "H-4zyq-NNFQ": "large maximotv.com watermark on all 10 pooled windows",
    # Pass 18, third read. Not footage at all - a SLIDESHOW of magazine
    # stills, pillarboxed with black bars either side, and all three of its
    # pooled windows are bad in a different way:
    #   6.2   a full-frame ELLE COVER, cover lines and all ("FALL FASHION
    #         SHOPPING GUIDE / 600 OF THE SEASON'S BEST LOOKS / JENNIFER!").
    #         This is the w2X4wxwB-qQ defect exactly - that source was banned
    #         for putting a magazine spread on screen - and it was shot 4,
    #         seven seconds into the film.
    #   9.4   an editorial photograph in which she is topless under an open
    #         jacket. It carried the ABC News cheat-day QUOTE CARD at shot
    #         284. Whatever else is arguable, that is not a picture this film
    #         puts a card on.
    #   25.4  a black-and-white studio portrait; fine on its own, and not
    #         worth keeping a pillarboxed slideshow in the pool for.
    # Read on qc/groups/SCAN_jD.jpg and qc/sheets/S00.
    "jD2V79_dNuQ": "pillarboxed magazine-still slideshow - a full-frame ELLE "
                   "cover and a topless editorial, one of them under a card",
    # ── PASS 19: THE WHOLE POOL, LOOKED AT ONCE ─────────────────────────
    # jD2V79_dNuQ above was found one shot at a time, which is how the ELLE
    # cover got to be shot 4 of the film. src_sweep.py tiles five frames of
    # EVERY source in hd/ - at 2, 25, 50, 75 and 98% of duration, so heads and
    # tails are sampled tightly - and all 18 sheets were read
    # (qc/srcsweep/SRC_00..17.jpg). These five are what a whole-pool read
    # found that a per-shot read had not. None of them was in the V9 cut and
    # three are not even in the pools; they are banned anyway, because
    # "reachable" is exactly how the ELLE cover arrived.
    #
    # A STOCK-AGENCY WATERMARK ACROSS THE PICTURE. Not the corner bug this
    # project tolerates: "gettyimages" is set diagonally across the middle of
    # every frame with the asset id "wi_9240072" burned bottom-left. Same
    # defect as se9PupQYj7g (HISTORIC FILMS + timecode) and wXjjzHrpZCQ
    # (WireImage), both already banned. Read on SRC_07 and qc/S4P19_BORD2.
    "PpKHUqJ7DRY": "gettyimages watermark across the middle of every frame "
                   "plus the asset id wi_9240072",
    # A FAN PAGE'S OWN WATERMARK, full width along the bottom of every frame:
    # "https://www.facebook.com/JennJoannaAniston/ by dheidevil888". The
    # u2G5MQ6nJuE / yf08roeCXXQ class. The content is 1980s sitcom work with
    # other actors in it, so there is nothing to save. SRC_01, S4P19_BORD2.
    "7mM-82tY-ts": "a fan page's facebook URL and handle burned across the "
                   "bottom of every frame",
    # AN AGGREGATOR'S BLOOPER REEL. A full-frame animated "Bloopers /
    # FILMISNOW EXTRA" clapperboard at the head, a full-frame "STAY TUNED
    # youtube.com/user/filmisnowextra" card at the tail, and between them
    # Bateman, Day, Sudeikis and Jamie Foxx without her, over a film clip
    # running its "CASTING BY LISA BEACH AND SARAH KATZMAN" credit across the
    # frame. SRC_12, S4P19_BORD2.
    "gb67coRCOl0": "FILMISNOW EXTRA blooper reel - channel cards at both ends, "
                   "a credit crawl in the middle, and mostly not her",
    # BURNED-IN SUBTITLES, full width, on three of three sampled windows:
    # "But, I mean, I don't know.", "He was fashion icon of the year.", "My
    # wrap gift to him." This is the nZWKuh-Calk case in English - a subtitle
    # is the most unmistakable foreign text there is, and being in English
    # makes it MORE readable on screen, not less. SRC_13, S4P19_BORD2.
    "nKHOp72TIso": "burned-in English subtitles across the bottom of the "
                   "sampled windows",
    # A STOCK-ILLUSTRATED TABLOID LISTICLE, and the X8_Ly9UL-0Y precedent
    # applies exactly: a source that needs a fourth window ban after three is
    # a source whose FORMAT is graphics. Rendered at fifteen points
    # (qc/S4P19_InU.jpg, qc/S4P19_InU2.jpg):
    #     0.0-11.5   a full-frame "SLAM MOTION" channel ident, then a
    #                full-frame headline card, "JENNIFER ANISTON ONCE 'BROKE
    #                HER BODY' BY DOING TOO MUCH OF THIS"
    #     58-72      stock inserts, including a full-frame image of a
    #                SCREAMING MAN disintegrating
    #     80-106     a gym clip with a trainer and a different blonde - the
    #                existing ban covered only 90.5-106 of it
    #     122-126    a full-frame cartoon "SOCIETIES" motion panel
    #     236-249    "THANKS FOR WATCHING! Don't forget to subscribe"
    # What is left is ordinary interview and Fallon material that sixty other
    # sources supply. It held eight shots and sat in sixteen pools; that is
    # the cost, and it is the same cost X8_Ly9UL-0Y was worth paying.
    "InUyN6CduEA": "stock-illustrated tabloid listicle - channel ident, "
                   "headline card, stock inserts that are not her, a cartoon "
                   "panel and an end card; five graphic regions",
    # A FULL-WIDTH BROADCAST CHYRON ON EVERY FRAME OF THE FILE. Sampled at 30,
    # 100, 180, 240 and 256s and rendered at the head and the last allowed
    # window: all seven carry "JENNIFER ANISTON & REESE WITHERSPOON TALK 'THE
    # MORNING SHOW'" or "...ON EMPOWERING OTHER WOMEN" as a two-tone bar
    # across the bottom of the picture, and one also carries a full-frame
    # "WELCOME BACK" graphic. That is not the corner bug this project accepts
    # (NBC, ellentube, BAZAAR, EdKclips, DREW are all small marks in the
    # extreme corner); it is the CeHYHu3C064 full-width AP chyron, which
    # needed a window ban - except that here there is no window without one.
    # Half the file is Robin Roberts and Reese Witherspoon besides. SRC_00,
    # TAIL_00, qc/S4P19_HEAD3.jpg.
    "2A2MCCK_pHs": "a full-width two-line ABC News chyron on every sampled "
                   "frame, and half of it is not her",
    # AN EXTRA PACKAGE, graphics end to end. "#ExtraTV25" is burned into the
    # bottom-left of every frame; the head is a full-width "when we FIRST
    # MET... JENNIFER ANISTON" title over her; 9.4 is a two-panel split-screen
    # composite; there is a full-frame FRIENDS logo card around 51; and the
    # tail is a "VISIT EXTRATV.COM FOR LOCAL LISTINGS" banner. Four graphic
    # regions on a source that contributes one pooled window - the
    # X8_Ly9UL-0Y test, and this one is not even close. SRC_07, TAIL_04,
    # qc/S4P19_HEAD2.jpg, qc/S4P19_BORD2.jpg.
    "TKAfdfzBiDs": "an Extra package - burned-in hashtag, full-width title "
                   "card, split-screen composite, a FRIENDS logo card and a "
                   "promo banner",
    # THE CAKE TRAILER, and a trailer's format is cards. Three rounds of
    # tail-margin were spent on this one before the shape became obvious: a
    # green MPAA card at the head, a full-frame "Cinelou FILMS" production
    # ident at 20, a purple review quote at 108.6 ("It's raw, poignant, and
    # unexpected." - Pete Hammond, DEADLINE), another at 121.4 ("An
    # Oscar-worthy performance for Jennifer Aniston"), the cast cards from
    # about 128 and the CAKE title card at the end. Every margin that cleared
    # one landed on another. It supplies no pooled window today, so this costs
    # nothing and stops a reshuffle finding it. qc/S4P19_TAILFIX2.jpg,
    # qc/S4P19_TAILFIX3.jpg.
    "P3IsUOSHlnU": "the CAKE trailer - MPAA card, production ident, two "
                   "full-frame review quotes, cast cards and a title card",
    # A tabloid-format compilation. Pass 18 first tried three window bans on
    # it - a pink full-frame graphics panel with an inset photo, a BOUNTY
    # HUNTER one-sheet, a COLLAGEN/PROBIOTICS supplement super - and a fourth
    # stretch of the same pink panel treatment (250-268) still reached the V8
    # cut at shot 117. A source that needs a fourth window ban after three is
    # a source whose FORMAT is graphics, and the window-ban rule is for
    # sources that are clean nearly everywhere. Its clean windows are ordinary
    # carpet and interview material that fifty-eight other sources supply, and
    # it only held two shots. Read on qc/sheets/S07 and qc/groups/SCAN_V8FIX.
    "X8_Ly9UL-0Y": "tabloid compilation - pink graphics panels in at least "
                   "two stretches, plus product supers; four window bans deep",
    # Pass 12. Both read off frames of the V6 cut.
    "CsLRK1JphL4": "a VERTICAL phone-format compilation - two clips stacked in "
                   "a 9:16 frame with black bars either side. active_box read "
                   "it as landscape (1614x1000) so the split-screen and the "
                   "bars went straight into the cut. It supplied 7 of 16 shots "
                   "in one L3 stretch across several passes and is the source "
                   "the owner meant by 'several are repeated'.",
    "QqBh30QBzJo": "Ellen BURNING QUESTIONS - full-width caption cards, one of "
                   "which reads 'Besides making love, showering, or swimming, "
                   "what is something you have enjoyed doing naked?'. It landed "
                   "under the diet narration.",
    "7G6p0mq35xA": "red carpet wall of logos - CALL ME CRAZY, Lifetime, SONY, "
                   "plus a maximotv.com watermark.",
    # Pass 14. 111 new sources were harvested to break the repetition (174
    # video shots were coming from 40 files, nine of which carried 60%).
    # Every one was rendered to a frame and read - qc/NEWSRC_0..4.jpg. These
    # are the ones that are not usable, and none of them would have been
    # caught by a title: the harness classified 0MBzDqPQX_Y as "AWARDS" and it
    # is Whoopi Goldberg.
    "0MBzDqPQX_Y": "Whoopi Goldberg, not her",
    "K_mzQZfvI04": "a different woman on Ellen",
    "PVrmAAWBnMY": "a different woman under a JENNIFER ANISTON TALKS chyron",
    "sCF-mCeW7Ig": "Zach Galifianakis",
    "L1z880RVLCE": "Owen Wilson alone",
    "ywtxjkaPm10": "Matt LeBlanc in a Friends scene",
    "dnXEvHwiGIo": "Vince Vaughn",
    "2v8Tuqfum_A": "Gerard Butler on a premiere line",
    "JB_DkFYkSYQ": "Jimmy Fallon alone",
    "ovtnkGoUhno": "Jimmy Fallon alone",
    "ttjt7NBOCV4": "Fallon and a guest, MARTINI graphic",
    "SXRvW056NqM": "Graham Norton alone",
    "Pf20oFtjYso": "a producer collecting an award",
    "Jsw-jXaSVPE": "an interviewer reading, Marley & Me poster",
    "GdkaVjJAtWI": "an interviewer, Horrible Bosses poster",
    "-Saks67VeyI": "an interviewer, Marley & Me poster",
    "hWruEaP4ysI": "a man carrying a sofa, film clip",
    "7pEsrAwvmhI": "a car and a dog under an ANISTON OPENS UP chyron",
    "i7WQ2JcFc6Q": "open water, nobody in frame",
    "ZHqmKFtqV_M": "near-black bokeh silhouette",
    "1ll6M4T5qSA": "a crowd, HOLLYWOOD.com watermark",
    "izzb0C4SmbQ": "fan edit - KINEMASTER watermark and a caption card",
    "u2G5MQ6nJuE": "screen recording - dhldevil888 + DU Recorder watermarks",
    "se9PupQYj7g": "HISTORIC FILMS stock watermark and a burned-in timecode",
    "ejMo0aIevj8": "a KFC Double Down advert",
    "bifTkKXGu3w": "a breaking-news package about a Pvolve workout",
    "4aA0KiW5tAg": "aggregator with a full-frame pink pull-quote overlay",
    # Pass 13, found by ocr_sweep.py rather than by eye.
    "XYcNVESFs4Y": "red-carpet source whose every window carries event "
                   "branding. All THREE shots it served in V6 were flagged: "
                   "shot 95 \"29TH ANNUAL CRITICS CHOICE\", shot 106 "
                   "\"TURNER CLASSIC MOVIES\", shot 116 \"E NEWS\". A step-"
                   "and-repeat is not a corner bug; it is a wall of logos.",
    "wvO0FMjlnHo": "LADbible sit-down with Witherspoon. At 120s it is REESE "
                   "alone, full frame, no Aniston - the same failure as "
                   "iUVWGBaW1b0 below. It served shots 247 and 254 of the V6 "
                   "outro, and the LADbible cards are foreign branding too.",
    "aZiwqY_e9ZQ": "an InStyle workout demo with two blonde women, neither of "
                   "them her, carrying an InStyle logo. It landed under the W4 "
                   "quote card - which is credited \"Jennifer Aniston to "
                   "InStyle\". A viewer reads that woman as Aniston delivering "
                   "the quote. Worst single frame found in the V6 audit.",
    "Tk07W15MCr0": "a Page Six repackage - carries a full headline card, "
                   "\"Jennifer Aniston stuns in sparkling strapless gown on "
                   "2024 Emmys red carpet / Page Six\", across the lower left. "
                   "It reached shot 207 of the V6 cut at 543.6s. Same class as "
                   "the LA Times envelope card above, not a corner bug.",
    "iUVWGBaW1b0": "CBS This Morning three-hander. At 90s it is GAYLE KING "
                   "full frame with no Aniston at all - the defect pass 8 "
                   "believed it had fixed. Two-handers pass the identity gate "
                   "because Aniston really is in them, so the gate cannot "
                   "catch this; it put her and Witherspoon under \"stripped "
                   "the glamour off completely\", a line about Cake (2014).",
    # archive pulls that came back too small to upscale cleanly
    "HdZTcltXgy0": "476x360",
    "OJMVlOcu7ew": "480x360",
    "UaCksy-pd-M": "640x320",

    # Pass 6. Every one of these was read off a frame of the V5 cut, not
    # inferred from a score. The frame number is the shot in that cut.
    "G1HmBSzxXV0": "a GMA package - full-frame InStyle magazine spreads with "
                   "burned-in headline type (\"...she thinks he hung the "
                   "moon.\", \"Jen SUPERSTAR, MEGA-BABE\") and an abc/GMA "
                   "bug. Reached shots 176, 183, 189, 221.",
    "ak5GBTYJArw": "opens on a full-screen GMA HEAT INDEX graphic reading "
                   "JENNIFER ANISTON'S FITNESS SECRETS. Shot 144.",
    "zbCniZvVfgQ": "an E! tabloid card, THE FRIENDS STAR LOOKED UN... set "
                   "full frame over a photo. Shot 156.",
    "Oc9ufH7lxnw": "a MARCH FITNESS studio segment - three men and a "
                   "basketball court. Shots 195 and 223, under TUESDAY and "
                   "SUNDAY.",
    "6a6MDIvrc_o": "a man demonstrating band work in a gym, with his own "
                   "burned-in captions. Shots 194 and 222.",
    "FXywTKuiYnM": "a different show entirely - a presenter in an apron. "
                   "Shot 196, under TUESDAY.",
        "wyLz-XeJL9o": "holds a full-frame Apple tv+ card. It reached the cut "
                   "three times - shots 20, 130 and 329, the last under "
                   "\"Jennifer Aniston's body is the result\".",
    "ol-7Wjrk3hk": "red carpet; the frame belongs to another actress in red. "
                   "Shots 298 and 346. One window passes, at 0.377.",
    "hxWPeK2YHLw": "a Vanity Fair four-hander. The panel reached the cut at "
                   "shots 243 and 287 despite MAX_FACES, because the gate "
                   "samples the START of the window and the source cuts to "
                   "the wide inside the shot.",
    "Q0Iu0ZZ72Ic": "a Glamour roundtable of six; Reese Witherspoon holds the "
                   "middle of frame. Shots 241, 285, 309, 339.",
        "_17zulAlAzw": "carries a full-frame THE MORNING SHOW / Apple tv+ promo "
                   "graphic with two third-party watermarks. Shot 161.",
    "c_ci5IriLG0": "an ET package, and the worst offender in the file. All "
                   "nine of its passing windows were rendered: every one "
                   "carries an ET bug, and most are FULL-FRAME pull-quote "
                   "cards (I'M IN BETTER SHAPE THAN I WAS IN MY 20s), a LIFE "
                   "OF CRIME title, a WE'RE THE MILLERS title, a CHEAT DAYS "
                   "chyron or a Verizon/SEE HER step-and-repeat. It is also "
                   "pillarboxed, which is why shots 1, 2, 10, 13, 175, 318 "
                   "and 349 all read as a phone video. Its one good window, "
                   "48.0, is kept as the KNEELING ROW pin.",
        
    # Pass 7. Long two-hander conversations, and the reason they are lethal:
    # the gate can only test the frame at the start of a window and the frame
    # 1.6s later, and an interview edit cuts between the two speakers INSIDE
    # that span. Both ends score as her; the middle of the shot - which is
    # what the viewer sees - is the other person. Between them these two
    # supplied eleven of the fifteen wrong-person shots in the pass-6 build.
    # Neither is needed: without them the diet pool still holds 419 windows
    # for the ~70 it spends, and the outro 554 for ~30.
    "ZoqjGormrds": "Variety Actors on Actors, 44 minutes of Aniston and Lisa "
                   "Kudrow alternating. Kudrow held six full frames - shots "
                   "21, 129, 215, 258, 298 and 320 - and shot 298 sat under "
                   "the quote bar \"Yes, so every Sunday is a cheat day - "
                   "JENNIFER ANISTON\". Her face scores 0.079 against the "
                   "reference, so the recogniser is right and the sampling "
                   "is what fails.",
    "BpgMda_4JDI": "a 75-minute podcast. Its two hosts, neither of them her, "
                   "held shots 23, 130, 217, 262 and 321 - the same wide "
                   "two-shot every time.",
    "vPrtuy_4lHM": "The Morning Show. One window survived the gate and it is "
                   "Billy Crudup (shot 121). Kept as the cue picture for "
                   "\"The Morning Show\" at 88.0s, which is her on the "
                   "studio floor and was looked at.",
    # Pass 15. Read off frames, not scores - all four candidate windows carry
    # zero faces (manifest/presence.json), so this has been dead weight in
    # EARLY_SRC all along, contributing nothing to any subject pool. The
    # content is a 1990s drama - two people embracing/kissing, a separate
    # office scene, an "NBC MONDAY" promo card - and nobody in the four
    # rendered frames is recognisably her. Banning it removes a
    # never-activates-today landmine (a future identity-threshold change could
    # wake it up) and a source that would not belong in a diet/health/workout
    # film even if it did pass: this project carries no biography chapters.
    "BrbwSDa3crU": "1990 NBC promo reel - a couple embracing/kissing and an "
                   "office scene, zero faces detected in any of its four "
                   "candidate windows, and romance-drama content with no "
                   "place in a diet/workout film regardless.",
    # Pass 17, section 4. Both sat in TRAINER_SRC, which only the retired
    # 'turn' pool drew on, so neither had ever been read. Both were rendered
    # (qc/S4_DEMOSHEET.jpg) before the new pools were written and neither can
    # be used at any window.
    # Pass 17, read off qc/sheets/S00..S22 of the FIRST cut of the new film
    # and then SIZED with src_ocr.py, which OCRs every pooled window of a
    # source at t, t+1.6 and t+3.2. Reading a sheet tells you a source is
    # dirty; it does not tell you whether to ban the source or the window, and
    # guessing that either throws away usable footage or leaves the defect
    # live somewhere the sheets did not sample. The count after each entry is
    # pooled windows carrying text / pooled windows.
    #
    # Five of these are the same thing: a press-junket chair in front of a
    # POSTER WALL. That is not a corner bug, it is the wall of logos that got
    # XYcNVESFs4Y and 7G6p0mq35xA banned, and between them they supplied 22
    # shots of the first cut - including four in a row under D6, a paragraph
    # about collagen and osteoporosis, and the last picture before the
    # endcard.
    "hPX9_UV478Q": "HORRIBLE BOSSES junket poster wall behind every frame. "
                   "12/12 pooled windows carry burned-in text. 9 shots of the "
                   "first cut.",
    "iwiHdFYJf9k": "the same HORRIBLE BOSSES poster wall, a different sitting. "
                   "12/12. 6 shots.",
    "6B7lM_DGMqA": "the same HORRIBLE BOSSES poster wall again. 12/12. It "
                   "played under \"a joint press interview alongside Reese "
                   "Witherspoon\" and as the last picture before the endcard.",
    "NyY8lvGQbKw": "HORRIBLE BOSSES 2 poster wall. 11/12.",
    "ONzCbZ8jLLo": "\"the break-up\" / MasterCard / Volkswagen / UNIVERSAL "
                   "step-and-repeat. 12/12.",
    "q6X1jyPSxhs": "a FIRST LOOK branded segment - the show's own logo in "
                   "frame throughout plus a \"JENNIFER ANISTON / 'ALEX LEVY' "
                   "EXECUTIVE PRODUCER - THE MORNING SHOW\" lower third. 12/12.",
    "b6ETxfr76Ts": "a compilation carrying FRIENDS title cards, a UNYTRON "
                   "logo and, at 761-780s, a full END CREDIT ROLL (DIRECTOR, "
                   "DIRECTOR OF PHOTOGRAPHY, SET DESIGNER, names). 8/12, and "
                   "the credit roll reached the cut at 320.6s under \"in "
                   "February, 2026\".",
    "LOEWwW97yW4": "a junket backdrop carrying BATEMAN and TECH/WITH graphics "
                   "plus a tenNEWS bug. 4/4.",
    # Not text - people.
    "oSb8auYSOcA": "an Ellen DeGeneres two-hander, and the exact failure "
                   "ZoqjGormrds and BpgMda_4JDI are banned for: the gate "
                   "scores HER and says nothing about who else is in frame. "
                   "Three of its nine windows in the first cut are Ellen "
                   "two-shots, and 684.6 - Ellen full-face in pink on the "
                   "right, Aniston's back to camera on the left - carried the "
                   "D5 quote card, credited JENNIFER ANISTON TO ABC NEWS. A "
                   "card over a stranger is the defect this section exists to "
                   "prevent.",
    "BOLYn4l_pMs": "an Allure shoot with an \"allure\" watermark burned into "
                   "every frame, and two of its five passing windows (38.2, "
                   "41.4) are a DIFFERENT blonde woman - not Aniston. It "
                   "reached shot 189 of the first cut under \"the standard "
                   "public health guideline of 150 minutes\".",
    "W2A_JiQgHrs": "carries a full-width green burned-in caption, \"WE TRY "
                   "JENNIFER ANISTON'S FAVOURITE WORKOUT\", across the bottom "
                   "of the frame for almost its entire length - three of four "
                   "sampled windows show it. 184 candidate windows, all of "
                   "them foreign text on screen. Same class as the InStyle "
                   "and ET burn-ins already banned.",
    "zMLEopVAzEE": "a Vanity Fair training film about a MAN - a bearded actor "
                   "in a gym, plus full-frame title cards (\"ONLY THE BRAVE\" "
                   "TRAINING) and calendar graphics, under a VF watermark. "
                   "Aniston is not in it. 218 candidate windows, none usable.",
}


BRANDING = json.loads((ROOT / "manifest" / "branding.json").read_text())     if (ROOT / "manifest" / "branding.json").exists() else {}
PRESENCE = json.loads((ROOT / "manifest" / "presence.json").read_text())     if (ROOT / "manifest" / "presence.json").exists() else {}
# Face detection was not enough: it passed a full-frame magazine portrait of
# EMINEM, which went to air, plus Lisa Kudrow, a makeup artist and John Aniston.
# IDENTITY is a cosine score against a reference embedding of Aniston built from
# frames verified by eye. SFace calls 0.363 the same-person line; the measured
# separation here is wide - her father's soap footage scores +0.002 and Kudrow
# +0.143, while her own interviews score +0.72 to +0.75.
IDENTITY = json.loads((ROOT / "manifest" / "identity.json").read_text())     if (ROOT / "manifest" / "identity.json").exists() else {}
# Half-grid samples: [faces, biggest, identity] at t + SPREAD/2, so a window
# can be tested at BOTH ends of the shot it will become. See midcheck.py.
MID = json.loads((ROOT / "manifest" / "mid.json").read_text())     if (ROOT / "manifest" / "mid.json").exists() else {}
# How much this window looks like somebody the cut has already been caught
# showing - Lisa Kudrow, two podcast hosts, a Pvolve model, Billy Crudup. See
# impostors.py. A window is rejected when it is closer to one of them than to
# her, which is a comparison and not a threshold: it costs nothing on windows
# that really are her.
IMPOSTOR = json.loads((ROOT / "manifest" / "impostor.json").read_text())     if (ROOT / "manifest" / "impostor.json").exists() else {}
# Does the source CUT inside this window? A 2s shot drawn across a cut shows
# two or three different scenes and reads as a glitch - shot 332 of the
# pass-10 cut contained four. See cuts.py. 22% of candidate windows have one.
CUTS = json.loads((ROOT / "manifest" / "cuts.json").read_text())     if (ROOT / "manifest" / "cuts.json").exists() else {}
MAX_CUT_SPIKE = 8.0
# Pool membership needs only a short clear run; each SHOT then filters for its
# own length (Reels.next / Reels.best). Measured over 1183 windows: 90% are
# clear for 1s, 73% for 2.5s, 47% for 6.5s - so long holds are affordable, but
# only from the windows that can actually carry them.
MIN_CLEAR = 1.0



# Every id above must name a real file. Five pass-14 bans did not: the ids were
# transcribed BY EYE off small labels on the contact sheets and l/I/K are
# indistinguishable at that size, so a KFC advert, Vince Vaughn and a
# breaking-news package stayed live - the news package became the single
# heaviest source in the cut at 12 shots. Read ids from the data, never from a
# rendered label.
_ghosts = sorted(b for b in BANNED if not (ROOT / "hd" / f"{b}.mp4").exists())
if _ghosts:
    raise SystemExit("BANNED names files that do not exist: " + ", ".join(_ghosts))

def clear_seconds(vid: str, t: float) -> float:
    """Seconds of continuous source before the first cut, 99 if none."""
    v = CUTS.get(f"{vid}@{t:.2f}")
    if v is None:
        return 99.0
    return float(v[1]) if isinstance(v, list) else (99.0 if v < MAX_CUT_SPIKE else 0.0)
MIN_IDENTITY = 0.35

# Sections whose narration is about HER. A window used here must contain a
# face. F1: the v5 cut ran Kimmel alone x4, Colbert x3 and a panel of five
# strangers under lines about Jennifer Aniston.
SUBJECT_SECTIONS = {"hook", "subscribe", "life", "turn", "workout_intro",
                    "week_intro", "diet_intro", "diet", "outro"}
MIN_FACE = 0.010          # largest face must be >=1% of frame
MAX_FACES = 2             # 3+ detected faces is a panel, not a portrait


# Hand-verified windows. Every candidate window of the four surviving Pvolve
# films was rendered at t AND at t+1.6s and read; these are the ones where she
# holds both ends of the shot. They exist because those films are mostly
# movement - a shoulder, a band, a foot on the mat - and a face detector
# rightly finds no face, which would otherwise throw away the only footage in
# the project of her actually training. Rejected here and worth recording:
# lrZKJPVn89s@25.4 cuts to a PVOLVE end card; JJLe4jmbrN0@6.2 cuts to an empty
# wall and @9.4 cuts to a different woman doing the same movement.
#
# JJLe4jmbrN0 and voC2DxCL6jQ are GONE from this set - pass 16's audit found
# both are testimonial ads with burned-in caption text running almost their
# entire length (measured with RapidOCR every 0.1-0.4s across the whole clip;
# see BANNED_WINDOW below for the extents). Two entries here read as caption-
# free at their single sampled frame - JJLe4jmbrN0@22.2 and voC2DxCL6jQ@9.4 -
# and were reported clean on that basis, but the NEXT caption in each starts
# only ~0.2s later ("How incredible do we feel right now?" at JJLe4jmbrN0
# t=22.4; "And I love...that I can get an efficient total body workout in
# just 20 minutes" at voC2DxCL6jQ t=9.6). No shot this pipeline ever cuts -
# not even MIN_SHOT=0.7s - can start at either point without immediately
# showing the caption, so neither survives once the shot actually has a
# length. Checked every OTHER windows() grid point in both sources
# (HEAD=3.0, SPREAD=3.2) against the measured caption extents too: none has
# a 6.4s (MAX_SHOT) caption-free run anywhere. Nothing usable is left in
# either source - the surviving four-Pvolve-films footage is now these two.
TRAIN_OK = {
    ("lrZKJPVn89s", 3.0), ("lrZKJPVn89s", 6.2), ("lrZKJPVn89s", 9.4),
    ("lrZKJPVn89s", 12.6), ("lrZKJPVn89s", 15.8),
    ("qqipyG6bpLA", 3.0), ("qqipyG6bpLA", 6.2), ("qqipyG6bpLA", 9.4),
    ("qqipyG6bpLA", 15.8),
    # 44.6 and 54.2 were in this list and were WRONG - both are a younger
    # Pvolve model, not her, and they reached shots 4, 176 and 337 of the
    # build that followed. Read at thumbnail size they passed; read at full
    # size they do not. Everything above was re-read at 600px afterwards.
}


def _continuous(vid: str, t: float) -> bool:
    """No cut inside the window. Applies to hand-verified windows too: being
    sure the first frame is her says nothing about whether the source cuts to
    a different scene half a second later."""
    if not CUTS:
        return True
    return clear_seconds(vid, t) >= MIN_CLEAR


def _has_subject(vid: str, t: float) -> bool:
    """A face, not a panel, it has to be HER - and she has to STAY.

    The v5 gate tested one frame, the first of the window, and passed anything
    it had no record for. Both halves of that were wrong, and both were caught
    by looking rather than by measuring:

    * Fails open. 385 of 6601 face-bearing candidates had no identity score at
      all and were waved through.
    * Tests one frame. Every one of iUVWGBaW1b0's 24 passing windows was
      rendered and IS her - yet Gayle King held four full frames of the cut.
      The source cuts to the interviewer inside the ~1.6s the shot runs. The
      same mechanism put an ET red-carpet step-and-repeat under FRIDAY /
      BOXING OR ROPE, and a full-frame InStyle cover under "Dani Coleman".

    So: no record is a rejection, and the half-grid point 1.6s later - the far
    end of the shot - has to be her too.
    """
    if not _continuous(vid, t):
        return False                     # the source cuts inside this window
    if (vid, t) in TRAIN_OK:
        return True                      # looked at, both ends, by hand
    if IMPOSTOR:
        for tt, her in ((t, IDENTITY.get(f"{vid}@{t}")),
                        (round(t + SPREAD / 2, 2),
                         (MID.get(f"{vid}@{round(t + SPREAD / 2, 2)}")
                          or [0, 0, None])[2])):
            them = IMPOSTOR.get(f"{vid}@{tt}")
            if them is not None and her is not None and them > her:
                return False
    rec = PRESENCE.get(f"{vid}@{t}")
    if rec is None:
        return False                     # fail CLOSED: unproven is not passed
    if not (rec["faces"] > 0 and rec["faces"] <= MAX_FACES
            and rec["biggest"] >= MIN_FACE):
        return False
    ident = IDENTITY.get(f"{vid}@{t}")
    if ident is None or ident < MIN_IDENTITY:
        return False
    if MID:                              # only once the index has been built
        m = MID.get(f"{vid}@{round(t + SPREAD / 2, 2)}")
        if m is None:
            return False
        faces, big, mid_id = m
        if not (0 < faces <= MAX_FACES and big >= MIN_FACE
                and mid_id >= MIN_IDENTITY):
            return False
    return True


# ── COMPOSITION, which is a different question from IDENTITY ────────────────
# `_has_subject` asks "is this her". A quote card also has to ask "can I read
# her in this frame, and is there room for the card". Those come apart:
#
#   * TRAIN_OK above waves through every Pvolve movement window WITHOUT any
#     face check, on purpose - those films are "a shoulder, a band, a foot on
#     the mat" and a face detector rightly finds nothing. They are genuinely
#     her, so the identity gate passes them, and they are exactly the shots a
#     card must not sit on: body-framed, often turned away. `qqipyG6bpLA` is
#     in TRAIN_OK, and `qqipyG6bpLA` is what was under the broken card at
#     05:19 in V6.
#   * MIN_FACE is 1% of frame AREA - a head about a tenth of the frame wide.
#     That is a wide two-shot, not a portrait.
#   * presence.faces_in counts PROFILE detections as well as frontal ones, so
#     a shot of the back of a head that catches an ear passes.
#
# So this gate is separate, stricter, and is applied ON TOP of `_has_subject`,
# never instead of it. Nothing below can make an unsafe window safe.
CARD_MIN_FACE = 0.020      # >=2% of frame area: a portrait, not a body shot
# ONE face, not two. MAX_FACES is 2 for ordinary shots and that is right - she
# is interviewed sitting next to people all day. It is wrong under a card: the
# W1 card, credited to Mandy Ingber, landed on a two-shot of Aniston and Reese
# Witherspoon, and a viewer reading "MANDY INGBER" over two women picks one of
# them. Read on qc/CARD_OVER_W1.jpg, shot 101.
CARD_MAX_FACES = 1
# Where the card is drawn, in fractions of the frame. Deliberately larger than
# the biggest card (O2, six lines at 40px) so the answer does not depend on
# which quote lands here.
CARD_ZONE = (0.05, 0.47, 0.67, 0.95)      # x0, y0, x1, y1
_CARDFACE = ROOT / "manifest" / "cardface2.json"   # v2: also counts faces
CARDFACE: dict = (json.loads(_CARDFACE.read_text(encoding="utf-8"))
                  if _CARDFACE.exists() else {})
_cardface_dirty = False


def _frontal(vid: str, t: float) -> "tuple | None":
    """FRONTAL faces at this second: (count, area, x0, y0, x1, y1), normalised,
    for the LARGEST one. `count` is how many frontal faces are big enough to
    read as a person rather than a detector artefact.

    Frontal only - no profile cascade. A profile or a back-turned head is
    precisely what must not carry a card, so counting it here would rebuild
    the hole this function exists to close.
    """
    global _cardface_dirty
    key = f"{vid}@{t:.2f}"
    if key in CARDFACE:
        v = CARDFACE[key]
        return tuple(v) if v else None
    import cv2
    import presence
    img = presence.grab(vid, t, w=640)
    best = None
    if img is not None:
        g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        H, W = g.shape[:2]
        c = cv2.CascadeClassifier(cv2.data.haarcascades
                                  + "haarcascade_frontalface_default.xml")
        n = 0
        if not c.empty():
            for (x, y, w, h) in c.detectMultiScale(g, 1.1, 6, minSize=(28, 28)):
                a = (w * h) / float(W * H)
                if a >= CARD_MIN_FACE * 0.35:
                    n += 1
                if best is None or a > best[1]:
                    best = (0, round(a, 5), round(x / W, 4), round(y / H, 4),
                            round((x + w) / W, 4), round((y + h) / H, 4))
        if best is not None:
            best = (n,) + best[1:]
    CARDFACE[key] = list(best) if best else None
    _cardface_dirty = True
    return best


def save_cardface() -> None:
    if _cardface_dirty:
        _CARDFACE.write_text(json.dumps(CARDFACE, indent=0), encoding="utf-8")


def _overlaps_card(box) -> bool:
    """box is (count, area, x0, y0, x1, y1)."""
    x0, y0, x1, y1 = CARD_ZONE
    return not (box[4] <= x0 or box[2] >= x1 or box[5] <= y0 or box[3] >= y1)


_CARDTEXT = ROOT / "manifest" / "cardtext.json"
CARDTEXT: dict = (json.loads(_CARDTEXT.read_text(encoding="utf-8"))
                  if _CARDTEXT.exists() else {})
_cardtext_dirty = False
_RAPID = None


def _card_zone_clear(vid: str, t: float) -> bool:
    """No FOREIGN burned-in text where the card goes.

    Rule 4 - a card must not collide with what is underneath it. Found by
    looking, not by reasoning: W1 shot 104 (InUyN6CduEA) carries an aggregator
    headline, "JENNIFER ANISTON BELIEVES SHE'S IN BETTER SHAPE NOW THAN IN HER
    20S", burned across the lower middle of frame. The card landed on top of
    it and the two read as competing headlines. Nothing in the identity or the
    composition gate can see text, because neither of them looks for it.

    ocr_sweep.py finds this class of defect AFTER the film is built. This is the
    same detector, asked BEFORE the window is chosen, and only about the
    rectangle the card occupies - text elsewhere in frame is somebody else's
    problem and is often legitimate (a press backdrop, a set dressing).
    """
    global _cardtext_dirty, _RAPID
    key = f"{vid}@{t:.2f}"
    if key in CARDTEXT:
        return bool(CARDTEXT[key])
    import presence
    img = presence.grab(vid, t, w=960)
    ok = True
    if img is not None:
        if _RAPID is None:
            from rapidocr_onnxruntime import RapidOCR
            _RAPID = RapidOCR()
        import cv2
        tmp = ROOT / "work5" / "_cardzone.png"
        tmp.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(tmp), img)
        H, W = img.shape[:2]
        x0, y0, x1, y1 = CARD_ZONE
        res, _ = _RAPID(str(tmp))
        for det in (res or []):
            pts, txt, conf = det[0], det[1], float(det[2])
            if conf < 0.60 or len([c for c in txt if c.isalnum()]) < 3:
                continue
            xs = [q[0] / W for q in pts]
            ys = [q[1] / H for q in pts]
            if not (max(xs) <= x0 or min(xs) >= x1
                    or max(ys) <= y0 or min(ys) >= y1):
                ok = False
                break
    CARDTEXT[key] = ok
    _cardtext_dirty = True
    return ok


def save_cardtext() -> None:
    if _cardtext_dirty:
        _CARDTEXT.write_text(json.dumps(CARDTEXT, indent=0), encoding="utf-8")


# Windows that are a perfectly good picture and a bad BED FOR A CARD. Found by
# eye on qc/CARD_OVER.jpg, which asks "is the thing behind it appropriate to
# the words?" - a question no detector in this file asks.
#
# The failure they share: the shot has its own loud subject, and the card's
# words have nothing to do with it, so the frame reads as two unrelated
# statements stacked on each other. Worst case is a PRODUCT held to camera
# under a quote about food - that reads as an advertisement with a caption.
#
# These are denied for CARDS ONLY. The montage may still use them; the picture
# is not the problem, the pairing is.
CARD_WINDOW_DENY: dict = {
    # A Harper's BAZAAR "what's in my bag" shoot. She is on a director's chair
    # in a studio, holding a product up to the lens, and the BAZAAR wordmark is
    # burned into the top left. Under D3 - "warm lemon water ... oatmeal with
    # an egg white" - shot 213 read as a haircare advertisement with a
    # breakfast caption. The whole product-handling stretch goes, not just the
    # frame I caught, because the next re-pick lands two seconds away.
    # Sampled every few seconds across the whole 300s file and read by eye.
    # The BAZAAR wordmark is burned into the top left for all of it - that is a
    # corner bug and this film tolerates those (ET, ellen, NBC all appear). The
    # bag on her lap and the products in her hand are the problem: 128 put "SHE
    # IS THE GOLD STANDARD - DANI COLEMAN, HER TRAINER" over her holding a
    # white tube to camera for 6.2 seconds, which is the longest shot of the W4
    # card and reads as a sponsored segment. The clean stretches (155-195,
    # 230-276) are still available to cards.
    "qAp9lq2CT5M": [(48.0, 152.0, "the bag is open on her lap and she is "
                                  "lifting products out of it one at a time"),
                    (196.0, 226.0, "holds two haircare bottles to camera"),
                    (286.0, 296.0, "holds a blue product to camera")],
}


def _card_window_denied(vid: str, t: float) -> str:
    for a, b, why in CARD_WINDOW_DENY.get(vid, []):
        if a <= t <= b:
            return why
    return ""


# How far apart the gate may sample inside one shot. A card shot is gated at
# t, at t+dur (the last frame the viewer sees) and at every step in between,
# so no more than this many seconds of a card's bed is ever unexamined.
#
# THE HOLE THIS CLOSES. The previous version sampled exactly two instants -
# t and t+SPREAD/2, i.e. t+1.6s - and the module-level constant that was
# supposed to justify that, `MAX_SHOT = 2.6  # longest shot the assembler
# cuts, per carve()`, was simply not true: manifest/shots5.json carries 59
# video shots longer than 2.6s, six of them carded and four of those a full
# 6.2s. So everything past 1.6s of a carded shot was ungated, and two hard
# failures came out of exactly that gap:
#
#   shot 169  8Na0YrtG3AI@492.6, 6.2s.  Opens a clean single on her; at +3.0s
#             the SOURCE cuts to a wide two-shot with Jay Leno at his desk,
#             who then holds the last 3.2s under a card reading "JENNIFER
#             ANISTON TO RADIO TIMES". Read at film 7:38.0.
#   shot 201  jD2V79_dNuQ@25.4, 6.2s.   Opens on a B&W portrait; at +4.5s the
#             source cuts to a full-frame ELLE cover with burned-in cover
#             lines ("FALL FASHION SHOPPING GUIDE", "CLEAR SKIN NOW!") under
#             the Well+Good smoothie card. Read at film 8:45.5. reels5's own
#             docstring already named this failure once, for "Dani Coleman".
#
# Both were sampled at +0.0s and +1.6s, both times on the good half.
CARD_SAMPLE = 1.5


def card_sample_times(t: float, dur: float) -> list[float]:
    """Every instant the card gate must look at for a shot of this length.

    Always includes the head and the LAST frame the viewer sees. A constant
    that "describes the assembler" is what failed here, so this derives from
    the duration it is handed and nothing else.
    """
    if dur is None or dur <= 0:
        raise ValueError("card_sample_times needs the shot's real duration - "
                         "guessing it is the bug this argument exists to fix")
    n = max(1, int(math.ceil(dur / CARD_SAMPLE)))
    out = [round(t + dur * i / n, 2) for i in range(n + 1)]
    out[-1] = round(t + max(0.0, dur - 0.05), 2)     # the last frame, not past it
    return sorted(set(out))


# ── WHOSE FACE IS THE BIG ONE ───────────────────────────────────────────────
#
# The documented hole, and the one that shipped: "it scores HER. It says
# nothing about who else is in frame." `oSb8auYSOcA@662.2` carried the ABC
# News cheat-day card for FIVE AND A HALF SECONDS over a frame in which Ellen
# DeGeneres is the only clearly visible face and Aniston is the back of a head
# at the left edge. Every gate above passed it honestly:
#
#   _has_subject           she IS in the window, and the identity index scores
#                          the LARGEST face at the window's grid time, which
#                          at 662.2 was still hers.
#   CARD_MAX_FACES == 1    exactly one FRONTAL face - Ellen's. A face detector
#                          counts heads; it does not name them.
#
# So this asks the missing question at every sample across the shot: is the
# BIGGEST face in this frame hers? Same detector and same reference embedding
# the pool identity gate uses (recognise.py: YuNet largest face -> SFace ->
# cosine against manifest/identity_ref.json), pointed at the exact instants
# the card is on screen rather than at a grid point 1.4s away.
#
# THE THRESHOLD IS MEASURED, not inherited. Scored across the sample times of
# every card bed in the V7 cut plus the Ellen frame:
#
#   Ellen frame                          0.360 0.367 0.398 0.400 0.398
#   8Na0YrtG3AI@124.6 (the V7 D5 bed)    0.586 0.552 0.492 0.099 0.487
#   8Na0YrtG3AI@287.8                    0.636 0.605 0.065
#   OiI3zevZEHQ@67.0                     0.371 0.443 0.424
#   ... 28 other beds, every sample      0.489 .. 0.802
#
# The population is bimodal with a real gap between 0.371 and 0.489, so the
# line goes in the gap rather than on top of a cluster. MIN_IDENTITY (0.35) is
# too low - it passes Ellen - and it is right for its own job, which is "is
# this her at all" on a shot with no words attributed to anyone.
#
# Two of the worst offenders are not a stranger at all but a MID-SHOT DROP:
# 8Na0YrtG3AI@124.6 scores 0.099 at its fourth sample because the source cuts
# to the audience. clear_seconds() said the window was continuous, which is
# how a 5.5s card bed can be vetted and still spend a second on somebody else.
# Sampling identity across the whole shot catches both failures with one test.
CARD_MIN_IDENTITY = 0.45
_CARDID = ROOT / "manifest" / "cardid.json"
# Versioned key. An unversioned cache of "is this her" is exactly the thing
# that must not be served by a later, different detector - the same reason
# CARDSTILL drops anything that is not v3 at the door.
CARDID: dict = {k: v for k, v in
                (json.loads(_CARDID.read_text(encoding="utf-8"))
                 if _CARDID.exists() else {}).items()
                if k.startswith("v1:")}
_cardid_dirty = False
_RECOG = None


def _recogniser():
    """(detector, recogniser, reference vector), built once.

    Returns None if the reference embedding has not been built - and the
    CALLER then fails CLOSED. An unmeasurable frame is a no; that is the whole
    point of this gate.
    """
    global _RECOG
    if _RECOG is None:
        ref_p = ROOT / "manifest" / "identity_ref.json"
        if not ref_p.exists():
            _RECOG = False
        else:
            import numpy as np
            import recognise
            det, rec = recognise.models()
            ref = np.array(json.loads(ref_p.read_text(encoding="utf-8")),
                           np.float32)
            _RECOG = (det, rec, ref)
    return _RECOG or None


def card_identity(vid: str, t: float) -> float:
    """Cosine similarity of the LARGEST face in this exact frame to her
    reference. -1.0 for "no face found" and for "cannot measure"."""
    global _cardid_dirty
    key = f"v1:{vid}@{t:.2f}"
    if key in CARDID:
        return CARDID[key]
    r = _recogniser()
    if r is None:
        return -1.0
    import numpy as np
    import recognise
    det, rec, ref = r
    e = recognise.embed(det, rec, recognise.grab(vid, t))
    v = -1.0 if e is None else round(
        float(np.dot(e / np.linalg.norm(e), ref)), 4)
    CARDID[key] = v
    _cardid_dirty = True
    return v


def card_dominant_is_her(vid: str, t: float) -> bool:
    return card_identity(vid, t) >= CARD_MIN_IDENTITY


def save_cardid() -> None:
    if _cardid_dirty:
        _CARDID.write_text(json.dumps(CARDID, indent=0), encoding="utf-8")


def card_composition_ok(vid: str, t: float, dur: float) -> bool:
    """May a quote card sit on this window for `dur` seconds?

    Cheap tier first, off the manifests, so the whole pool can be filtered
    without touching ffmpeg; the frame grab only runs on windows that already
    look plausible.

    A window qualifies when, at EVERY sample across the shot's real rendered
    duration (see card_sample_times):
      - a frontal face is found at all (so she is facing the camera, not away),
      - that face is at least CARD_MIN_FACE of the frame (so the shot is framed
        on her face, not on her body), and
      - it does not sit inside the rectangle the card is drawn in.

    ...and the source does not CUT inside those `dur` seconds, and it is not on
    CARD_WINDOW_DENY, which is the eye's list rather than the detector's.

    `dur` is REQUIRED. Every caller knows the shot length it is asking about,
    and the one thing this function must never do again is assume one.
    """
    times = card_sample_times(t, dur)
    if any(_card_window_denied(vid, tt) for tt in times):
        return False
    if not _has_subject(vid, t):
        return False                     # identity gate is never relaxed
    # A cut inside the shot means the person at the head is not necessarily the
    # person at the tail, and no number of face samples can vouch for a frame
    # the detector was never pointed at. Ask for the WHOLE duration clear.
    if clear_seconds(vid, t) < dur:
        return False
    # cheap: presence already measured the largest face (frontal OR profile)
    mid = round(t + SPREAD / 2, 2)
    rec = PRESENCE.get(f"{vid}@{t}")
    m = MID.get(f"{vid}@{mid}")
    if rec is not None and (rec["biggest"] < CARD_MIN_FACE
                            or rec["faces"] > CARD_MAX_FACES):
        return False
    if m is not None and (m[1] < CARD_MIN_FACE or m[0] > CARD_MAX_FACES):
        return False
    for tt in times:
        f = _frontal(vid, tt)
        if f is None or f[0] != CARD_MAX_FACES or f[1] < CARD_MIN_FACE                 or _overlaps_card(f):
            return False
    # WHOSE face is it. Everything above this line counts faces; nothing above
    # it asks who they belong to, and _has_subject only asks whether she is
    # SOMEWHERE in the window. See card_dominant_is_her.
    for tt in times:
        if not card_dominant_is_her(vid, tt):
            return False
    # last, because it costs an OCR pass: nothing already written where the
    # card is about to be drawn
    return all(_card_zone_clear(vid, tt) for tt in times)


# Stills. Every still in this project is a generated OBJECT or PLACE - "a
# stationary spin bike alone in a dim studio", "an empty school corridor,
# nobody present" - so a card over one cannot be misread as a person, which is
# why `_pick_safe` lets stills through. That is only true while it stays true:
# this checks the picture rather than trusting the prompt, and the deny list
# below is what an eye found on qc/CARD_OVER.jpg that a detector would not.
# stills_move/mv_* are GENERATED DEMONSTRATIONS - a person performing the
# movement is the entire content of the image. The cascade catches six of them
# and misses the rest, and mv_padwork (two women boxing, in profile) went
# straight under the W1 card in the first build of this pass. Read on
# qc/CARD_OVER_W1.jpg, shot 100. So they are denied as a FAMILY, by where they
# live, not one at a time by whether a detector happened to see a face.
CARD_STILL_DENY_PREFIX = ("mv_",)
CARD_STILL_DENY: set = {
    # press pit - a crowd of silhouetted heads across the middle distance and
    # two men standing at frame right, in front of the cameras. Read on
    # qc/CARD_OVER_O1.jpg shot 234, and again on qc/CARD_STILLS_4.jpg.
    #
    # THE RULE, because this was inconsistent for one pass and an inconsistent
    # rule is worse than a strict one: A SILHOUETTE IS A PERSON. Whether the
    # viewer can name the face has nothing to do with it - the misread that
    # rule 3 is about is "the words on this card belong to somebody in this
    # picture", and a body-shaped shadow is somebody. q_spinbike3 (six
    # silhouetted riders) is denied on exactly this ground, and q_flashbulb was
    # allowed on the ground that its silhouettes are "plainly men" and the card
    # is her own words. That is two rules. Now there is one, and it costs
    # nothing: q_flashbulb was never load-bearing - O1 holds its card on
    # q_tvwall / q_gymfloor / q_sunrise / q_running with seconds to spare.
    "q_flashbulb",
}

# ── WHAT COUNTS AS A PERSON ─────────────────────────────────────────────────
# The previous version of this ran a frontal cascade and, later, a frontal +
# profile pair, and reasoned only about FALSE POSITIVES ("noisy in exactly one
# direction"). That premise was wrong and it cost a hard failure: mv_padwork is
# two women doing pad work with BOTH FACES SHARP IN PROFILE, and it went under
# the W1 card - credited to Mandy Ingber, who is neither of them - because
#
#   * `haarcascade_profileface` is SINGLE-HANDED. It finds heads facing one way
#     only. Both women in mv_padwork face the other way, so the profile pass
#     scored 0.0000 and the mirrored pass scores 0.0125. The flip is not an
#     optimisation, it is half the detector.
#   * a face detector cannot see a PERSON WITH NO FACE IN FRAME - a back, a
#     silhouette, a body cropped at the neck. p_carpet (a red carpet lined with
#     spectators), p_studio90s (a camera operator and a standing figure),
#     q_filmset (four crew in silhouette), s_diner (a seated figure at the
#     window) and q_paris (pedestrians) all scored 0.0000 on faces and all
#     contain people.
#
# So the evidence is now five detectors, and the thresholds differ per family
# because a torso box is not the same size as a face box.
#
# MEASURED, over all 148 stills, so the next pass does not have to re-derive it:
# the body detectors find every one of the five misses above, and they also
# fire on 20-odd object stills - a spin bike, a dumbbell rack, a wall clock, a
# wall of televisions, straps on a wall. There is NO threshold that separates
# them (HOG scores the bike at 0.125 and a real red-carpet crowd at 0.094).
# That is why CARD_STILL_CLEAR below is long, and why it may only ever grow by
# somebody LOOKING at qc/CARD_STILLS_*.jpg. The default is deny, which is the
# direction that fails safe: a false positive costs a card bed, a false
# negative puts a stranger under a credit.
CARD_PERSON_FACE = 0.004    # frontal or profile (either hand), fraction of area
CARD_PERSON_UPPER = 0.010   # haarcascade_upperbody
CARD_PERSON_FULL = 0.015    # haarcascade_fullbody
CARD_PERSON_HOG = 0.030     # HOG people detector, weight >= 0.6

# READ BY EYE, twice: once on qc/_denied_stills.jpg during the first pass, and
# again in this pass on the five sheets qc/CARD_STILLS_0..4.jpg, which show
# EVERY still in the project at 420px with its verdict and its detector
# numbers burned in. There is no person in any of these. The detector's answer
# is overridden HERE, by name, rather than by loosening a threshold for
# everything.
#
# NOT on this list, deliberately, and also read by eye:
#   q_spinbike3  a spin class - six silhouetted riders.
#   q_market     a street market with figures in the aisle.
#   p_nycstreet  a walking figure, small but unmistakably a person.
#   q_filmset    four crew silhouetted around the lamps.
#   q_paris      pedestrians on both pavements.
#   p_carpet     a red carpet lined with spectators.
#   p_studio90s  a camera operator, and a second figure standing at the back.
#   s_diner      a seated figure at the window, out of focus but plainly a man.
#   p_kojak      a man on a television screen. A face on a screen is a face.
#   p_hairtimeline  three portraits of Aniston herself, with dates set on them.
CARD_STILL_CLEAR: set = {
    # objects and empty rooms (stills/)
    "q_fridge", "q_gymfloor", "q_bands", "q_clockgym", "q_dumbbells",
    "q_eiffel", "q_harness", "q_spinbike", "q_spinbike2", "q_towel",
    "q_tvwall", "q_watchclock",
    "s_eggs", "s_plate", "s_harness", "s_bands", "s_payphone", "s_set",
    # food (stills_food/) - plates, bowls, boards and glasses, every one
    "f_berries", "f_bread", "f_clock", "f_nuts", "f_oats", "f_prawns",
    "f_sweetpot", "f_chicken", "f_coffee2", "f_eggs3", "f_smoothie",
    "f_steak", "f_tomatoes",
    # places (stills_place/) - all empty
    "p_waitress", "p_la70s", "p_artschool", "p_corridor", "p_office",
    "p_shermanoaks",
    # day cards (stills_place/d_*) - kit laid out on a floor
    "d_saturday",
}

# The one card bed in the film with a HUMAN BODY in it, and the one thing no
# detector here found: q_treadmill is a pair of legs in running shoes on a
# treadmill belt, cropped at mid-thigh. Every detector scores it 0.0000 and an
# eye sees a person immediately.
#
# It is kept, as a judgement, and the judgement is: there is no IDENTITY in the
# frame. Rule 3's harm is "the viewer maps the name on the card onto the person
# in the picture", and a pair of legs carries no name to map. It also carries
# W3, which is Aniston's own words to InStyle - there is no third party in the
# credit for a viewer to hand the legs to. Both halves of that have to hold, so
# card_qc.py asserts the second one against the finished manifest: a still
# listed here may only ever carry a card whose speaker is the subject. If a
# card credited to Ingber or Coleman is ever laid on W3, the assertion fails
# and this decision gets re-taken rather than quietly inherited.
CARD_STILL_BODY: dict = {
    "q_treadmill": "legs and running shoes on a treadmill belt, cropped at "
                   "mid-thigh - a person, but not an identity",
}

_CARDSTILL = ROOT / "manifest" / "cardstill.json"
# Only v3 entries survive the load. The previous schema stored a single float
# (the biggest face) under an un-versioned key; keeping those around means a
# reader of this file cannot tell which detector produced which number, and a
# future `if key in CARDSTILL` could serve one. Drop them at the door.
CARDSTILL: dict = {k: v for k, v in
                   (json.loads(_CARDSTILL.read_text(encoding="utf-8"))
                    if _CARDSTILL.exists() else {}).items()
                   if k.startswith("v3:")}
_cardstill_dirty = False
# stills where a human said "no person" and the detectors disagree. Not an
# error - it is the whole point of CARD_STILL_CLEAR - but it is the list of
# places where the gate rests on somebody's eyes, so card_qc prints it.
CARD_STILL_OVERRIDE: dict = {}


def person_evidence(path) -> dict:
    """How much evidence of a PERSON is in this still, per detector family.

    Values are the largest detection of that family as a fraction of frame
    area. Cached on the file's identity AND on a schema tag - `v3` here -
    because a cache keyed only on the file serves the previous detector's
    answer for a picture that never changed, and this project has shipped a
    stale cached picture three times.
    """
    global _cardstill_dirty
    from pathlib import Path as _P
    p = _P(path)
    st = p.stat()
    key = f"v3:{p.stem}:{st.st_size}:{int(st.st_mtime)}"
    if key in CARDSTILL:
        return CARDSTILL[key]
    import cv2
    ev = dict(face=0.0, upper=0.0, full=0.0, hog=0.0)
    img = cv2.imread(str(p))
    if img is not None:
        g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        H, W = g.shape[:2]

        def run(name, gray, mn):
            c = cv2.CascadeClassifier(cv2.data.haarcascades + name)
            if c.empty():
                return 0.0
            big = 0.0
            for (x, y, w, h) in c.detectMultiScale(gray, 1.1, 6, minSize=mn):
                big = max(big, (w * h) / float(W * H))
            return big

        flip = cv2.flip(g, 1)
        ev["face"] = max(
            run("haarcascade_frontalface_default.xml", g, (32, 32)),
            run("haarcascade_profileface.xml", g, (32, 32)),
            # the mirror: the profile cascade only finds heads facing one way
            run("haarcascade_profileface.xml", flip, (32, 32)))
        ev["upper"] = run("haarcascade_upperbody.xml", g, (60, 60))
        ev["full"] = run("haarcascade_fullbody.xml", g, (40, 80))
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        sc = 640.0 / max(W, H)
        small = cv2.resize(img, (int(W * sc), int(H * sc))) if sc < 1 else img
        sh, sw = small.shape[:2]
        try:
            rects, wts = hog.detectMultiScale(small, winStride=(8, 8),
                                              padding=(8, 8), scale=1.05)
            for (x, y, w, h), wt in zip(rects, list(wts) or [0] * len(rects)):
                if float(wt) >= 0.6:
                    ev["hog"] = max(ev["hog"], (w * h) / float(sw * sh))
        except cv2.error:
            pass
    ev = {k: round(v, 5) for k, v in ev.items()}
    CARDSTILL[key] = ev
    _cardstill_dirty = True
    return ev


def person_found(ev: dict) -> bool:
    return (ev["face"] >= CARD_PERSON_FACE or ev["upper"] >= CARD_PERSON_UPPER
            or ev["full"] >= CARD_PERSON_FULL or ev["hog"] >= CARD_PERSON_HOG)


def card_still_ok(path) -> bool:
    """A still may carry a card if there is no PERSON in it."""
    from pathlib import Path as _P
    p = _P(path)
    if p.stem in CARD_STILL_DENY or p.stem.startswith(CARD_STILL_DENY_PREFIX):
        return False
    ev = person_evidence(p)
    if p.stem in CARD_STILL_CLEAR:
        if person_found(ev):
            CARD_STILL_OVERRIDE[p.stem] = ev
        return True
    if p.stem in CARD_STILL_BODY:
        return True                      # see CARD_STILL_BODY - a judgement
    return not person_found(ev)


def save_cardstill() -> None:
    if _cardstill_dirty:
        _CARDSTILL.write_text(json.dumps(CARDSTILL, indent=0), encoding="utf-8")


# Both indices are expensive (a frame grab and a cascade each) and both are
# pure functions of the material, so they persist. Written on the way out
# rather than per-entry: a build that dies half way through simply re-measures,
# which is the safe direction for a gate.
import atexit as _atexit
_atexit.register(save_cardface)
_atexit.register(save_cardid)
_atexit.register(save_cardstill)
_atexit.register(save_cardtext)


def _branded(vid: str, t: float, secs: float = 2.5) -> bool:
    """Inside a title-card / credits range at the head or tail of a source."""
    for a, b in BRANDING.get(vid, []):
        if t < b and (t + secs) > a:
            return True
    return False


def _bright(vid: str, t: float, secs: float = 2.0) -> bool:
    track = LUMA.get(vid)
    if not track:
        return True
    a = int(t / LUMA_STEP)
    b = max(a + 1, int((t + secs) / LUMA_STEP))
    win = [x for x in track[a:b + 1] if x >= 0]
    if not win:
        return True
    return min(win) >= 22.0 and sum(win) / len(win) >= 30.0


# Foreign graphics inside an OTHERWISE GOOD source, as (start, end) seconds of
# the graphic itself. Banning the whole source was the only tool this pipeline
# had, and for a source carrying 24 usable shots that cure is worse than the
# disease - which is why both of these survived into V6.
#
# Ranges are the graphic's own extent, measured by OCR. The margin for a shot
# that STARTS before the graphic and runs into it is applied in windows().
# Found by ocr_sweep.py; each was then confirmed on the rendered frame.
BANNED_WINDOW = {
    "qAp9lq2CT5M": [(280.9, 283.9)],   # "Vital Proteins" product super - an ad
    "sjLDT-hLkFQ": [(120.9, 123.9)],   # ET two-line burned-in subtitle
    # Pass 15. f8YLI3POJnM is otherwise clean Pvolve class footage (a bald
    # male trainer and three women, Aniston among them) and reads as landscape
    # 1920x1080 to ffprobe, but this stretch is a VERTICAL 9:16 group-photo
    # insert with black pillarbox bars either side - the exact defect that got
    # CsLRK1JphL4 banned outright. Found by scanning every second of the
    # source and confirmed on the rendered frame; the clean footage either
    # side of it (24 usable shots' worth) is not the problem.
    "f8YLI3POJnM": [(4.5, 6.0)],       # vertical pillarboxed group photo insert
    # Pass 16. Both are Pvolve testimonial ADS, not demo footage, and both
    # burn in caption text almost wall-to-wall - measured with RapidOCR every
    # 0.1-0.4s across the full clip, then confirmed on the rendered frame.
    # Ranges are the caption's own extent (the brief gaps between caption
    # cards - JJLe4jmbrN0 3.1-4.0, voC2DxCL6jQ 8.2-9.5 / 20.2-20.9 /
    # 35.4-36.8 / 53.8-55.4 - are genuinely clean but none reaches the 6.4s
    # a shot could run, so none rescues a windows() grid point; see TRAIN_OK
    # above). Kept as BANNED_WINDOW rather than moved to BANNED because
    # rule 3 says ban the window not the source - these stay available if a
    # future pass finds an uncaptioned cut of either ad.
    "JJLe4jmbrN0": [(0.0, 3.0), (4.1, 27.0)],
    "voC2DxCL6jQ": [(0.0, 8.1), (9.6, 20.1), (21.0, 35.3), (36.9, 53.7),
                     (55.5, 60.0)],
    # Pass 17, section 4. Every candidate window of the five demonstrator
    # sources was rendered and read (qc/S4_DEMOALL_0..2.jpg) because they now
    # carry the workout chapters - the Pvolve campaign films are gone and
    # anonymous demonstrators ARE the format. Three defects, all foreign text,
    # none of them the small NBC/JENNA&FRIENDS corner bug (which is a corner
    # bug and stays - see the c_ci5IriLG0 note above for the distinction).
    "cBZC-8S9b8g": [(14.0, 18.5),    # "DANI COLEMAN @DANI_BCOLEMAN" lower third
                    (84.0, 88.5),    # "OLIVIA MUNN PAID SPOKESPERSON" lower third
                    (243.0, 258.0)], # full-frame TODAY WITH JENNA & FRIENDS card
    # A "Mandy Ingber / Celebrity Fitness Trainer" lower third. She is the
    # yoga teacher W1 names, so the temptation is to cue it - but the super is
    # burned-in text and this project bans those on sight.
    "fnTFycw2q1w": [(4.5, 9.0)],
    # Pass 17. Sized with src_ocr.py - in each of these the source is clean
    # nearly everywhere and dirty in one stretch, which is what this table is
    # for. Banning the whole file would have cost 40 usable windows.
    # Pass 18 WIDENED this from (555.0, 632.0). That range was sized off the
    # ONE caption src_ocr happened to sample, and the caption is not the
    # feature - the GAME is. From about 506s to the end of the file Late Night
    # is playing charades, and every round burns its answer in full width with
    # a :NN countdown box beside it: "THE GIRL WHO KICKED THE HORNET'S NEST"
    # 556-621, "BUST A MOVE" 648-690, "JERSEY SHORE" 708-740, "THE HUNGER
    # GAMES" 772-804. 555-632 caught the first round and left three more live.
    # Scanned every 8-10s from 460 to 811 and read on qc/groups/SCAN_HyJ*.jpg:
    # 460-490 is clean interview, 493-505 carries a burned-in LATE NIGHT WITH
    # JIMMY FALLON super, 506 to the end is the game. Windows 179.0 and 463.8
    # survive and are clean, which is the whole reason this is a window ban.
    "HyJALzFY7VU": [(493.0, 811.5)],
    # Pass 18 widened this from (95.0, 106.0) for the same reason: the
    # headline card is the SECOND graphic here. A full-frame animated
    # infographic - illustrated figures, charts, a spinning ring - fades in
    # about 91s and runs to about 95s, and 95.0 starts one grid step too late
    # to exclude the window that lands on it. Read on qc/groups/SCAN_2.jpg
    # and SCAN_3.jpg. The card itself is the pink-and-white "JENNIFER ANISTON
    # BELIEVES SHE'S IN BETTER SHAPE NOW THAN IN HER 20S", 98.5-102.5, which
    # is shot 113 of the V7 cut.
    "InUyN6CduEA": [(90.5, 106.0)],
    "GS8nqYf5NvQ": [(19.0, 28.0)],     # "Emirates A380 First Class Shower Spa"
                                       # product caption; 1/5. The rest of this
                                       # source is her with a juice and her at
                                       # a fridge, both of which the diet
                                       # section cues correctly.
    "CuxqL5IsiOc": [(168.0, 192.0)],   # "SEPTEMBER 8, 2003" date caption.
                                       # The ellentube corner bug on the other
                                       # windows STAYS - it is a corner bug,
                                       # the same call already made for the
                                       # NBC and JENNA&FRIENDS bugs.
    # NOT A GRAPHIC, and flagged as such so the next pass does not read this
    # table as "graphics only". d7hb5JTpbFE 3.0-25.4 is a backstage MAKE-UP
    # ROOM - a vanity mirror, bottles, a woman having her face done. It is
    # clean and it is not a workout, and because it is eight consecutive
    # windows of one location the cut used it FIVE times: under "the principle
    # transfers", "Pvolve funded it", "the university's own release", "should
    # hear before the numbers" and "the more accurate version is". Different
    # windows, one picture, which is what repetition looks like to a viewer.
    # The other thirteen windows of this source are the studio and the mat.
    "d7hb5JTpbFE": [(0.0, 27.0)],
    # Pass 18. An AP wire clip whose first ~13 seconds carry a full-width AP
    # chyron - "JENNIFER ANISTON / ACTRESS", then "LOS ANGELES". Window 3.0 of
    # it is shot 345 of the V7 cut, in O1, and the contact sheet read did not
    # catch it. Found while measuring whether HEAD needs a tail-style margin
    # (see windows()): it is a HEAD defect that no head margin short of 14s
    # would have caught, which is the argument for sizing graphics one at a
    # time rather than by a blanket rule. Confirmed on qc/groups/SCAN_CeH.jpg.
    # After 13s only the small AP corner bug remains and that stays, on the
    # same ground as the NBC and ellentube bugs.
    "CeHYHu3C064": [(0.0, 13.5)],
    # Pass 18, found while confirming the globes_podium visual group rather
    # than by an OCR sweep - which is the argument for looking at a source
    # whole instead of only where the sheets point. The Golden Globes telecast
    # supers her win over the acceptance speech: a gold two-line lower third,
    # "JENNIFER ANISTON / ACTRESS - TV SERIES - MUSICAL OR COMEDY", plus the
    # 60TH GOLDEN GLOBE AWARDS wordmark under it. It animates in at 43 and is
    # fully out by 49, and windows 44.6 and 47.8 were BOTH in the V7 cut (D5
    # and D6). Confirmed on qc/groups/SCAN_yN3.jpg at one-second intervals.
    #
    # It names her correctly, which is exactly why it is tempting and exactly
    # why it goes: the rule is that the film does not carry somebody else's
    # burned-in text, and "but this super is true" is how the next one gets
    # in. The other eleven pooled windows of this source are the same speech
    # with nothing written on it. The 60TH GOLDEN GLOBE AWARDS title cards at
    # 3.0 and 6.2 are full-frame graphics of the same family; they are not
    # pooled (no face, so the identity gate already refuses them) and are left
    # to that gate rather than duplicated here.
    "yN_Tp10MHmQ": [(42.5, 49.0)],
    # ── pass 18, the OCR sweep. Reading the sheets finds what the sheets
    # happened to sample; src_ocr.py reads EVERY pooled window of a source at
    # t, t+1.6 and t+3.2, which is the only way to know whether a graphic is
    # one window or fifteen. Run over the nineteen heaviest sources in the cut
    # (qc/src_ocr_p18.log), then every hit rendered and read on
    # qc/groups/SCAN_OCR.jpg and SCAN_EXT.jpg before anything was written here.
    #
    # WHAT WAS DELIBERATELY NOT BANNED, because "OCR found text" is not the
    # test: the EdKclips, ellentube, ellen, Variety, ET and Harper's BAZAAR
    # CORNER BUGS (8Na0YrtG3AI 15/16 windows, alR1NeotIso 16/16,
    # vUF8TJXSzKg 16/16, qAp9lq2CT5M 16/16) stay, on the rule already written
    # for the NBC bug; the SAG-AFTRA step-and-repeat lettering behind her on
    # nivqKWke94k 13/16 is a real wall in the real room; and the French shop
    # signs on B9npiMH76eU are set dressing in a Friends scene. Banning those
    # would cost sixty usable windows to remove nothing a viewer reads as an
    # overlay.
    #
    # A full-width three-line broadcast super, "FEMALE ACTOR IN A DRAMA SERIES
    # / JENNIFER ANISTON / THE MORNING SHOW", across the bottom of the SAG
    # acceptance speech. Same call as the Golden Globes chyron above, and
    # taken the same way: it is true, it names her, and it is still somebody
    # else's burned-in text. Clean at 47 and 49, on at 51/53/55.
    "e1hAV-ZrRpI": [(49.5, 58.0)],
    # "JENNIFER ANISTON / 'THE GOOD GIRL'" - a full-width morning-show lower
    # third with a temperature-and-clock bug beside it. On at 14 and 16, gone
    # by 18. One window of sixteen.
    # TWO ranges, and the second one is the lesson. src_ocr found the super at
    # 15.8 and nowhere else, so pass 18 banned 13.0-17.5 - and shot 229 of the
    # V8 cut then played window 111.8 with the SAME super on it, full width.
    # The graphic recurs every time the segment restarts; an OCR sweep that
    # samples t, t+1.6, t+3.2 of each pooled window can miss a re-entry that
    # lands between samples, which is exactly why the sheets are read after
    # the sweep and not instead of it. Confirmed at 112 and clear by 115 on
    # qc/groups/SCAN_V8FIX.jpg. The small 84F/8:14 clock bug on the later
    # windows is a corner bug and stays.
    "kko5oEDAH40": [(13.0, 17.5), (110.0, 115.0)],
    # The same sit-down interview under two ids (see GROUP
    # "blackjacket_sitdown"), so the same lower third - "JENNIFER ANISTON"
    # across the bottom with a channel mark - and the same extent: on at 32,
    # 34 and 36, gone by 38. src_ocr caught it on both uploads independently,
    # which is a useful check that the group is really one shoot.
    "CFQcpm-wKuk": [(31.0, 37.5)],
    "UDcgIYu-TEE": [(31.0, 37.5)],
    # (X8_Ly9UL-0Y had three window bans here for a pink graphics panel, a
    # BOUNTY HUNTER one-sheet and a COLLAGEN/PROBIOTICS super. A fourth
    # stretch of the same treatment still reached the cut, so it is a source
    # ban now - see BANNED.)
    # A Variety piece that cuts to CLIPS with the show's name supered on them:
    # "FRIENDS" in caps at top left over four consecutive windows (200-212),
    # and a "DEIDRE BEHAR" reporter name plate on the step-and-repeat window
    # at 195. THREE of those windows were in the V8 cut (#148, #222, #270) and
    # the sheets show the label plainly. src_ocr did report 'FRIENDS' here and
    # pass 18's first read dismissed it as a backdrop; it is not, it is a
    # caption. The Variety and ET corner bugs on the other nine windows stay.
    "dO0akkBV8nc": [(193.0, 215.0)],
    # The Emmy telecast's own gold nameplate under the acceptance speech -
    # "ACTRESS COMEDY SERIES / JENNIFER ANISTON / Friends" - animating in at
    # 118.2 and gone by 124.6. Window 118.2 was shot 115 of the V9 cut. Third
    # instance of the same family in this pass (Golden Globes, SAG, Emmy):
    # every awards broadcast supers the winner, and every one of those supers
    # is somebody else's text on our picture. The other six pooled windows are
    # the same speech with nothing written on it. qc/groups/SCAN_ENC.jpg.
    #
    # Pass 19, section 4, SECOND RANGE ADDED. The head of this file carries a
    # different kind of foreign text: a FAN-UPLOAD WATERMARK,
    # "#DownloadFriends DALnet", small white type across the bottom-left. It
    # is on from 1.0 and gone by 10.0, covering pooled windows 3.0, 6.2 and
    # 9.4 - and those fourteen seconds are the presenters walking on, the
    # nominee audience and the stage, with no Aniston in them at all. Read at
    # 1s intervals on qc/s4p19/ENCA_0.jpg. Same call as take2markTV and
    # H-4zyq-NNFQ: an uploader branding the picture is not the corner bug this
    # project tolerates. The chyron range above was re-measured at 0.5s on
    # qc/s4p19/ENCB_0.jpg and is right: the nameplate animates in at 118.0,
    # holds 119.0-123.0 and is gone at 123.5.
    "Enc2ocQRXik": [(0.0, 10.0), (117.5, 123.5)],
    # A Variety sit-down with B-ROLL CUT INTO IT, and the b-roll is the
    # problem rather than any super. 107-118 is a Women's March crowd -
    # hundreds of strangers, placards reading #MeToo SURVIVORS' MARCH and
    # WE ARE THE ONES WE'VE BEEN WAITING FOR, and no Aniston in it at all;
    # 126-132 is a Dumplin' premiere line-up with a caption on it; 156-161 is
    # a film clip captioned "Dumplin' (2018)"; 182-191 is a full-frame Apple
    # TV+ THE MORNING SHOW key-art card. Every one of those is a picture the
    # montage would be making a statement with, under narration about her
    # training. The interview windows either side (100, 104, 120, 124, 162,
    # 192, 250, 254) are clean and are what this source is in the pool for.
    "-MXQ_3DNX_Y": [(107.0, 118.0), (126.0, 132.0), (156.0, 161.0),
                    (182.0, 191.0)],
    # ── pass 19, section 4. A NEW SHAPE OF DEFECT, and the reason this entry
    # is long: a graphic insert of a DIFFERENT PERSON composited inside an
    # otherwise-genuine source. Not a caption, not an end card, not a
    # pillarboxed group photo - an editorial spread cut into a
    # behind-the-scenes film, which the recogniser happily scores as her.
    #
    # eKKDRdE-WKs is InStyle's "At the Cover Shoot with Jennifer Aniston".
    # 4.4-24.3 and 36.3-43.5 are genuine BTS of Aniston on a greenhouse set;
    # in between, the film cuts to the FINISHED editorial pages, each one a
    # pink-graded still sitting inside a film-strip surround with black bars
    # either side of it. Window 31.8 was shot 285 of the V8 cut - a 1.0s
    # picture under the ABC "cheat days" quote card - and the woman in that
    # spread is a platinum blonde with a heavier brow and a wider-set eye
    # than Aniston. It is not her, and the card credited the line to her.
    #
    # THE IDENTITY GATE CANNOT REACH THIS AND RAISING IT WOULD NOT HELP.
    # eKKDRdE-WKs@31.8 scores 0.65 in manifest/identity.json. Two shots in
    # the V8 cut that ARE her score lower - B9npiMH76eU@169.4 at 0.532 and
    # HyJALzFY7VU@169.4 at 0.533 - so no value of MIN_IDENTITY separates the
    # impostor from the genuine article. Pass 8 reached the same conclusion.
    # A window ban is the only tool that works on this, which is why the
    # extents below were measured frame by frame rather than guessed.
    #
    # Boundaries, read on qc/s4p19/EKK_EDGE.jpg at 0.1s steps: the title card
    # dissolves out over 4.3-4.4; the spread montage is off at 24.30 and on
    # at 24.40; it is on at 36.20 and off at 36.30; the closing "Look for
    # Jennifer Aniston's full feature in the February issue" end card is off
    # at 43.50 and on at 43.55. Ranges are set just inside each measurement.
    #
    # Three ranges, not one, because a whole-source read found three separate
    # defects where the sheets had shown one:
    #   0.0-4.5    full-frame white title card, "At the Cover Shoot with
    #              Jennifer Aniston". Window 3.0 sits on it. HEAD is 3.0 and
    #              no head margin short of 4.5s would have caught it.
    #   24.3-36.3  the editorial-spread montage described above.
    #   43.5-47.9  the closing subscription end card. The TAIL rule (DUR-9.4)
    #              keeps windows from STARTING after 38.5, but 38.2 + a full
    #              MAX_SHOT runs to 44.6, four seconds into the card - the
    #              same "the last seconds of an upload are the uploader's own
    #              material" failure the TAIL rule was written for, on a file
    #              short enough that the margin does not cover it.
    # Four of the twelve pooled windows survive - 6.2, 9.4, 12.6, 15.8 - and
    # every one is Aniston on the set. 19.0, 22.2 and 38.2 go with the
    # montage and the end card because _window_banned measures at MAX_SHOT
    # (19.0 + 6.4 lands at 25.4, inside the spread), which is the safe
    # direction for pool membership. windows(subject=True) is now EMPTY for
    # this source: 31.8 was the only window with a face the detector found,
    # so the card gate can never route a quote card back onto this file.
    #
    # The InStyle wordmark bottom-right stays. It is a corner bug, the same
    # call already made for the NBC, ellentube, AP and Harper's BAZAAR bugs.
    "eKKDRdE-WKs": [(0.0, 4.5), (24.3, 36.3), (43.5, 47.9)],
    # jD2V79_dNuQ IS NOT LISTED HERE. Pass 19 measured window ranges for it
    # and then found the source itself banned outright in BANNED above (the
    # "pillarboxed magazine-still slideshow" entry), written by a concurrent
    # read of the same cut. The source ban is the stricter call and it stands;
    # the measurements are kept here because they are what a future pass would
    # need to reinstate the clean half of that file rather than re-measure it:
    #   0.0-3.6    "one true media / Created at OneTrueMedia.com" title card,
    #              which is where window 3.0 sat.
    #   4.7-9.1    ELLE cover one, masthead and cover lines readable. It
    #              slides out of frame between 8.7 and 9.1.
    #   28.7-33.6  ELLE cover two, same masthead.
    #   34.5-end   the OneTrueMedia end card.
    # i.e. the ranges would have been [(0.0, 9.1), (28.6, 40.4)], leaving
    # windows 9.4, 15.8, 19.0 and 22.2 - four clean B&W editorial portraits of
    # her, not the three the BANNED note names. Read at 1s over the whole file
    # on qc/s4p19/JD2V_0..1.jpg and at 0.1s on JD2VE_0.jpg / JD2VF_0.jpg.
}


# ── PASS 19: THE SWEEP ABOVE, ACTED ON ──────────────────────────────────────
#
# Everything in the "measured, confirmed by eye, NOT YET BANNED" note below
# was left live because it was sized at 1-second resolution and the note asked
# for a frame-by-frame pass before any of it became a ban. Pass 19 re-rendered
# every one of them (qc/S4P19_HAZ.jpg) and they are all exactly what the note
# says they are, so they are banned at the extents the note measured. A window
# ban only ever removes material - being a second wide either way costs
# windows, never correctness - so 1-second resolution is precise enough to act
# on and waiting a second pass for it was the more expensive mistake.
#
# The head entries come from the other half of pass 19: tailproof.py renders
# the FIRST and LAST allowed window of every source in the pool, and eleven
# sources opened their first allowed window on a full-frame title card
# (qc/S4P19_HEAD1..3.jpg, qc/srcsweep/TAIL_00..09.jpg). HEAD stays at 3.0 for
# the reason argued at TAIL - raising it globally costs the only real training
# footage in the film - so the heads are policed here, one source at a time,
# which is what this table is for.
#
# Kept as a separate dict and merged, rather than edited into the entries
# above, so that a reader can see which pass put which range in.
BANNED_WINDOW_P19 = {
    # HEADS: the first allowed window is a full-frame card. Read on
    # qc/S4P19_HEAD1.jpg / HEAD2.jpg unless noted.
    "BZsQtQ-gEw4": [(0.0, 11.5)],      # a film clip inset in a rainbow-bar
                                       # frame - the whole picture is a
                                       # graphic surround. Clean from 12.6.
    "Imj67wZds0s": [(0.0, 12.5),       # yellow satellite ident, then a
                                       # "BRAD BLANKS" panel, then a full
                                       # "shooting BLANKS" title card
                    (139.0, 146.0)],   # B&W man holding a ".COM" sign
    "LzisOKB_sEU": [(0.0, 6.0)],       # full-frame "ET FLASHBACK" card
    "QMp5NDQlZoE": [(0.0, 14.0)],      # black cards carrying the interview
                                       # questions in white type
    "hOJ4qbGYiCs": [(0.0, 5.5)],       # "COLUMBIA PICTURES" banner over a
                                       # pillarboxed film clip
    "idQRtrPGHjw": [(0.0, 14.0)],      # "TOTALLY HOLLYWOOD TV" channel sting
    "le9OrAofjP4": [(0.0, 5.5)],       # green Movies.ie "M" ident
    "sIc7ae_ylSs": [(0.0, 5.5)],       # Santa Barbara Film Festival poster
                                       # card, "Montecito Award - Jennifer
                                       # Aniston Acceptance Speech"
    "ykScGjlKsCQ": [(0.0, 5.5)],       # "At the Cover Shoot with Jennifer
                                       # Aniston" title card
    "yN_Tp10MHmQ": [(0.0, 8.5)],       # the "60" ident, then a full-frame
                                       # "60TH GOLDEN GLOBE AWARDS" card
    "zbnHO-r5HRs": [(0.0, 8.5)],       # "MONDAYS with MARLO featuring
                                       # Jennifer Aniston", then "Jennifer
                                       # Aniston's Exercise Routine", both
                                       # full-width red title cards. The T1
                                       # and T2 bites are cut at 29.9 and
                                       # 55.5 and are not touched by this.
    # MIDDLES, from the sweep note below, each re-rendered and confirmed.
    "-MXQ_3DNX_Y": [(11.0, 13.0),      # a clip captioned "Dumplin' (2018)"
                    (265.0, 269.0)],   # two men in tuxedos, no Aniston
    "0vy5wFgkP2U": [(21.0, 25.0),      # pillarboxed clip of another woman
                    (28.0, 37.0)],     # full-frame "ACTRESS COMEDY SERIES"
                                       # nominee grid
    "5O3fyVHdw50": [(27.0, 31.0)],     # pillarboxed sketch, two other women
    "Enc2ocQRXik": [(0.0, 14.0),       # the stage under a wall-sized
                                       # "ACTRESS COMEDY SERIES" screen
                    (82.0, 93.0)],     # full-frame nominee grid
    "L7PpXV1agc8": [(100.0, 116.0)],   # a "Kevin Frazier" full-width name
                                       # plate over Brad Pitt, then a
                                       # "BRENNIFER 2020" graphic
    "MfX4_OB5pJ4": [(576.0, 631.0)],   # letterboxed dark film clips of a
                                       # different actress - and this is one
                                       # of the heaviest sources in the cut
    "aNAAWzLOEKc": [(32.0, 63.0),      # Cake clips under a full-width
                                       # "R CAKE / abcNEWS.com" ratings bar,
                                       # several with no Aniston in them
                    (124.0, 129.0),    # "LIVE IN TIMES SQUARE / JENNIFER
                    (193.0, 199.0)],   # ANISTON / 'CAKE'" full-width chyron
    "alR1NeotIso": [(206.0, 233.0)],   # an Ellen home-video insert of two
                                       # small children under a
                                       # "SEPTEMBER 8, 2003" caption
    "fnTFycw2q1w": [(4.5, 9.8)],       # the Mandy Ingber lower third is on
                                       # until 9.8, not 9.0 as banned above
    "hfXZ0jZ6_NU": [(3.0, 7.0),        # full-screen archive photo of Julie
                    (30.0, 34.0)],     # Andrews, then Reese Witherspoon,
                                       # each holding an Oscar. Not her.
    "nabfcX7IfsE": [(258.0, 266.0)],   # an advert break inside an awards
                                       # telecast - full-frame Head &
                                       # Shoulders, then Saturn
    "zuVUp2qEnHE": [(33.0, 36.0),      # pillarboxed paparazzi still
                    (96.0, 100.0)],    # a MARY POPPINS film still
    # Two more found by the tail proof itself rather than by the note.
    "_wUC6czee2s": [(81.0, 93.0)],     # a three-panel composite of a
                                       # lingerie portrait, pillarboxed
                                       # inserts either side of the carpet
                                       # footage
}

for _vid, _ranges in BANNED_WINDOW_P19.items():
    BANNED_WINDOW.setdefault(_vid, [])
    BANNED_WINDOW[_vid] = list(BANNED_WINDOW[_vid]) + list(_ranges)

# ── PASS 19 SWEEP: MEASURED, CONFIRMED BY EYE, NOT YET BANNED ────────────────
#
# The #285 defect above has a SHAPE - a composited frame-within-a-frame that
# the identity gate cannot see - and pass 19 swept the whole library for it
# rather than only fixing the one window. HOW: every one of the 108 pooled
# sources was decoded at 1 fps into greyscale and each frame measured for
# MATCHED, SYMMETRIC dark bars (both left and right, or both top and bottom,
# each more than 0.05 of the frame past that source's own baseline geometry,
# the two sides within 0.035 of each other) around a bright middle, held for
# two seconds or more. Symmetry is the discriminator: a shot that is merely
# dark down one side fails it, a composited insert does not. That flagged 27
# sources and 67 runs; every run was then RENDERED and READ
# (qc/s4p19/BOXHIT_0..3.jpg, HAZ1..3.jpg). The detector reproduces the known
# f8YLI3POJnM pillarbox and the eKKDRdE montage, which is the check that it
# works.
#
# NONE of the following is in the V9 cut. All of it is live in the pool, so
# any future reshuffle can draw it, exactly as the reshuffle that put
# eKKDRdE-WKs@31.8 into V8 did. Extents are at 1-SECOND resolution and must be
# sized frame by frame before any of them becomes a ban.
#
#   gb67coRCOl0  ~128.5-134.5  a full-frame YOUTUBE END SCREEN, "STAY TUNED /
#                youtube.com/user/filmisnowextra". This is the exact defect
#                clean_pin was written for and window 124.6 reaches it.
#   jD2V79_dNuQ  3.0 and 6.2 - and this one the geometric sweep MISSED,
#                because the whole source is letterboxed stills so the
#                baseline already has bars. It is a photo montage: 3.0 is a
#                branded "one true media / Created at OneTrueMedia.com" card,
#                6.2 is an ELLE COVER with the masthead and cover lines
#                readable. 6.2 is in windows(subject=True), so it is
#                CARD-ELIGIBLE. 9.4 is in the cut and is genuinely her.
#   hfXZ0jZ6_NU  3-7 and 30-34  Graham Norton cuts to full-screen archive
#                photos of OTHER PEOPLE holding Oscars - Julie Andrews in
#                black and white, then Reese Witherspoon. Same shape as #285.
#   aNAAWzLOEKc  32-63 Cake film clips under a full-width "R CAKE /
#                abcNEWS.com" ratings bar, several with no Aniston in them;
#                124-129 and 193-199 a "LIVE IN TIMES SQUARE / JENNIFER
#                ANISTON / 'CAKE'" full-width chyron.
#   L7PpXV1agc8  ~100-110 a "Kevin Frazier" full-width name plate and a
#                "JANUARY 2020" super; ~113-116 a "BRENNIFER 2020" graphic.
#                Windows 102.2/105.4/108.6/111.8 are pooled. (Its 42-63 run
#                carries a small top-right "Courtesy of the 26th Annual
#                Screen Actors Guild Awards" credit; three CARD-BEARING shots
#                of the V8 cut sat on it. Read as a corner bug on the
#                ellentube/NBC precedent, but it is wordier than those and
#                the next pass should make that call deliberately.)
#   zbnHO-r5HRs  ~76-83  a "MONDAYS with MARLO / MarloThomas.com" end card.
#                The source IS in the cut and window 73.4 reaches it.
#   nabfcX7IfsE  258-266  an ADVERT BREAK inside an awards telecast: full
#                frame Head & Shoulders, then Saturn.
#   idQRtrPGHjw  0-14  a "TOTALLY HOLLYWOOD TV" channel sting.
#   nKHOp72TIso  48-57  a pillarboxed paparazzi photo of a MAN on a phone
#                with a burned-in caption, "You are absolutely kidding me."
#   zuVUp2qEnHE  33-36 a pillarboxed paparazzi still; 96-100 a MARY POPPINS
#                film still. Neither is footage of her.
#   PpKHUqJ7DRY  55-57  an archive photo carrying a GETTYIMAGES watermark and
#                the asset number "wi_9240072".
#   MfX4_OB5pJ4  576-631  letterboxed dark film clips of a different actress.
#                This is the third heaviest source in the cut.
#   7mM-82tY-ts  223-231  a burned-in FAN-UPLOAD watermark,
#                "https://www.facebook.com/JennJoannaAniston by dheldevil888".
#   alR1NeotIso  206-233  an Ellen home-video insert of two small children
#                under a "SEPTEMBER 8, 2003" caption.
#   -MXQ_3DNX_Y  11-13 a film clip captioned "Dumplin' (2018)"; 265-269 two
#                men in tuxedos at a party, no Aniston. Both are ADDITIONS to
#                the four ranges already banned on this source.
#   Imj67wZds0s  0-12 an animated title graphic; 139-146 a black-and-white
#                clip of a man with a ".COM" sign.
#   5O3fyVHdw50  27-31  a pillarboxed sketch clip of two other women.
#   0vy5wFgkP2U  21-25  a pillarboxed clip of an auburn-haired woman;
#                identity not established either way.
#   eHHBXaUdna4  14-16  an "#EXTRATV" burned-in hashtag.
#   dO0akkBV8nc  111-115  a pillarboxed archive photo. It IS her, with
#                Matthew Perry; listed only so the next pass does not
#                rediscover it and assume it was missed.
#   fnTFycw2q1w  the Mandy Ingber lower third banned above as (4.5, 9.0) is
#                actually on until 9.8. No live window sits on it - 9.4 is
#                not pooled and 12.6 is clean - so it is recorded, not fixed.
#
# WHAT THIS SWEEP CANNOT SEE, stated so the next pass does not read a clean
# result as proof: an insert composited FULL FRAME leaves no bars and is
# invisible to it; a source that is entirely inserts has bars in its baseline
# and cancels out (jD2V79_dNuQ, found by reading it instead); and at 1 fps
# with a two-second minimum an insert shorter than about two seconds can fall
# between samples.
# ─────────────────────────────────────────────────────────────────────────────
# The longest shot the assembler can actually cut from a reel window. This was
# 2.6, commented "longest shot the assembler cuts, per carve()", and that was
# FALSE - manifest/shots5.json contains 59 video shots longer than 2.6s, six of
# them carded and four a full 6.2s. Measured on the V6 manifest: the longest
# reel-picked video shot is 6.3s (kko5oEDAH40 in D3); the only longer video
# shots are the T-block sync BITES, which are pinned by tag and never drawn
# from a window, so they do not constrain this.
#
# A stale constant is what made the lie possible, so build5 now ASSERTS this
# covers max(SHOT_CYCLE) at import - if the pacing grows again the build stops
# instead of quietly under-checking. Anything that needs the real length of a
# real shot must be HANDED it; see card_composition_ok, which now requires it.
MAX_SHOT = 6.4

# HOW CLOSE TO THE END OF A FILE A WINDOW MAY START.
#
# `windows()` used DUR - 4.0, which is not a margin at all: it is barely more
# than half of MAX_SHOT, so a 6.4s shot starting at DUR-4.1 runs 2.3 seconds
# past the end of the file. Worse, the last seconds of a YouTube upload are
# STRUCTURALLY the uploader's own material - end cards, "WATCH NEXT" screens,
# credit rolls - and this project has now shipped that twice:
#
#   * a 6.2s cue shot on a YouTube end screen (the reason clean_pin exists),
#   * b6ETxfr76Ts@771.0, shot 117 of the V7 cut, 5.2 seconds before the end of
#     a 776.2s file, with the source's own credit roll running up the right
#     third of frame: "POST PRODUCTION ... SUPERVISING ... ADDITIONAL ...".
#
# So it is a RULE, not another BANNED_WINDOW entry: MAX_SHOT (the shot can
# never run past the file) plus three seconds of credits. Measured over the
# whole library it costs 169 of 7701 pooled windows (2.2%) and takes eight
# shots out of the V7 cut, of which b6ETxfr76Ts@771.0 is one - see the
# handback for the other seven.
#
# THE HEAD IS NOT SYMMETRIC AND THIS WAS MEASURED, not assumed. Every window
# in the V7 cut starting inside 9.4s was rendered and read
# (qc/groups/SCAN_HEAD.jpg): seven of the eight are clean, and the eighth
# (CeHYHu3C064@3.0, a full-width AP chyron) runs to 13.5s, so a 9.4s head
# margin would not have caught it either - it needed a BANNED_WINDOW, and it
# has one. Meanwhile a 9.4s head margin takes `qqipyG6bpLA` - the ONE training
# source that passes the live gate, whose single usable window is at 6.2 - to
# zero, along with f8YLI3POJnM and f6zuX21_098. Raising HEAD would cost the
# workout chapters their only real training footage to fix nothing. HEAD stays
# at 3.0, and the head is policed by BRANDING/_branded and by this table.
#
# ── pass 19: A FLAT MARGIN WAS NEVER RIGHT ──────────────────────────────
#
# TAIL was MAX_SHOT + 3.0 = 9.4s for every file in the library. A YouTube end
# card is not 3 seconds long; it is ten to twenty. Measured by reading five
# frames of all 194 sources (src_sweep.py, qc/srcsweep/SRC_00..17.jpg),
# FIFTY-FIVE of the ~110 un-banned sources end on a full-frame graphic -
# SUBSCRIBE / WATCH MORE, a channel ident, a magazine cover, an advertiser's
# product card. The flat margin left the last allowed window inside the card
# on at least these:
#
#   -MXQ_3DNX_Y  303.8s and still 308.0s: "WATCH MORE / SUBSCRIBE", full frame
#   5O3fyVHdw50  "SUBSCRIBE NOW / WATCH MORE" over the Fallon skyline
#   6YGaOzMMQUs  "THE TONIGHT SHOW ... SUBSCRIBE", full frame
#   CuxqL5IsiOc  "The Farewell Season / Check your local listings"
#   yN_Tp10MHmQ  a "dick clark productions" logo card
#
# and it is the same defect as the one this rule was written for. So the
# margin is now PER FILE. It scales with duration, because a 20-second card on
# a 30-second Pvolve ad would take the source to zero while the same 20
# seconds is nothing on a nine-minute talk show, and it is CLAMPED at both
# ends: never below the old 3.0 (so the five short training sources - 14.2s
# f6zuX21_098 among them - keep exactly the windows they had), never above 20
# (past that the cost stops buying anything, and the measurement below says
# no card in this library runs longer).
#
# WHY A RULE PLUS A TABLE, and not a measured number per file. cardscan.py
# measures the held-picture run at each end by asking "is this frame the same
# picture as the last frame of the file?", which is a far better signature
# than the two in src_sweep.py's docstring - it catches every static card. But
# it is not trustworthy enough to BE the margin, in both directions: it reads
# 29s of "card" on KHmVdNl1cos and 31s on lLqtWLL5pXw, which are locked-off
# interviews that simply do not move, and it reads only 1.5s on ykScGjlKsCQ,
# whose InStyle cover card is longer than that but animates. So the rule
# carries the whole library and TAIL_EXTRA carries the exceptions - and every
# entry in TAIL_EXTRA was put there by RENDERING the last allowed window of
# that source and looking at it (qc/srcsweep/TAIL_*.jpg).
TAIL_FLOOR = 3.0        # the old margin; the short sources keep it
TAIL_CEIL = 20.0
TAIL_FRAC = 0.10

# Seconds of extra margin for a named source, on top of the rule. Every one
# was READ off qc/srcsweep/TAIL_*.jpg, which renders the last allowed window
# of every source in the pool at its start and at +6.4s.
TAIL_EXTRA: dict[str, float] = {
    # Every one of these was found by RENDERING the last allowed window under
    # the rule alone and looking at it and at t0+6.4 - the last frame a
    # MAX_SHOT shot starting there could reach. The rule was right for 95 of
    # the 102 sources that have windows; these seven are the ones whose end
    # card is longer than a tenth of the file.
    "-MXQ_3DNX_Y": 8.0,    # a full-frame "Variety / SHARE VIDEO" card is up
                           # by 292.0 and the rule's last window ran to 294.2
    "JlpIdAmkT_k": 6.0,    # a full-frame "Apple tv+ / NOW STREAMING" card at
                           # 287.8; BRANDING had it starting at 300.7
    "PsXXGwspfNk": 8.0,    # a full-frame "THE GRAHAM NORTON SHOW / ALL NEW
                           # SATURDAY 10/9c" promo card from about 97
    "Ws-9ra38AlI": 8.0,    # the "Marley & Me" title animates in from about
                           # 135; BRANDING had it starting at 137.9
    "Zyy2RUx6BRM": 16.0,   # E! Rewind burns full-width subtitles over the
                           # last half-minute ("But there's nothing in the
                           # works?", "Are you going to be working
                           # together?") and ends on an E! copyright card.
                           # 262.2 was clean and 268.6 was not, so the margin
                           # has to clear 268
    "_wUC6czee2s": 4.0,    # fades to black around 98 and the rule's last
                           # window ended exactly on the fade
}


def tail_for(vid: str) -> float:
    """How far from the end of `vid` a window may no longer start."""
    d = DUR.get(vid, 0.0)
    m = max(TAIL_FLOOR, min(TAIL_CEIL, TAIL_FRAC * d))
    return MAX_SHOT + m + TAIL_EXTRA.get(vid, 0.0)


# Kept as a name because the old flat value is still the floor of the rule and
# several comments above quote it.
TAIL = MAX_SHOT + TAIL_FLOOR


# ── VISUAL GROUPS: several YouTube ids that are ONE shoot ───────────────────
#
# The owner's oldest complaint is repetition, and it survived every mechanical
# fix because both defences key on the YOUTUBE ID. A press junket is uploaded
# by six outlets under six ids; the 8% cap sees six sources at 2% each and the
# consecutive-source rule sees two different files. Measured on the V7 cut,
# which passed both:
#
#   Horrible Bosses junket  hPX9_UV478Q 9 + iwiHdFYJf9k 6 + 6B7lM_DGMqA 3
#                           = 18 shots, 4.9% of the film, and shots 349 and
#                           350 CONSECUTIVE and identical on screen.
#   SAG podium, white dress e1hAV-ZrRpI 6 + L7PpXV1agc8 4 + nivqKWke94k 4
#                           = 14 shots, 3.8%, 355 and 356 consecutive.
#
# 32 shots - 8.8% of the film - were two afternoons.
#
# HOW THESE WERE FOUND, because the next pass must be able to redo it rather
# than inherit a hand list: `groups.py propose` embeds every pooled window
# with CLIP (manifest/clip.npz, already built for semantic.py) and proposes a
# pair when >=30% of one side's windows have a twin in the other above 0.90
# cosine. That is a CANDIDATE list, not an answer - the same metric merges
# seven unrelated late-night appearances because a beige couch in front of a
# city skyline looks like a beige couch in front of a city skyline. Every
# candidate cluster is rendered to qc/groups/G*.jpg and read. What survives
# the eye is below; what did not is written down under it, because a rejected
# merge is as much a finding as an accepted one.
#
# The test the eye applies: SAME DAY. Same backdrop AND same outfit AND same
# hair. Two episodes of the same talk show, years apart, in different clothes,
# are not one shoot and do not read as a repeat.
GROUP: dict[str, list[str]] = {
    # A "HORRIBLE BOSSES" step-and-repeat, three outlets' cuts of the same
    # junket day. hPX9 is the mauve strapless, iwiHdFYJf9k and 6B7lM are the
    # olive dress with the gold strap hardware; same wall, same lighting,
    # same room. qc/groups/G03.jpg and GX_check.jpg.
    "horrible_bosses": ["hPX9_UV478Q", "iwiHdFYJf9k", "6B7lM_DGMqA"],
    # SAG Awards 2020, the white silk dress - ONE NIGHT, and deliberately one
    # group rather than two. Three ids are the acceptance speech at the
    # podium with the statuette (e1hAV-ZrRpI, nivqKWke94k, and the podium
    # windows of the ET compilation L7PpXV1agc8) and three are the SAG-AFTRA
    # step-and-repeat and press line in the same dress an hour earlier
    # (X8_Ly9UL-0Y, _XfKW4nfMwI, 6VOJ9NwMf14). Splitting them would let the
    # film run 18 shots of the podium AND 18 of the carpet in the same dress,
    # which is the defect with an extra step in it. qc/groups/G01.jpg, GY.
    #
    # L7PpXV1agc8 and X8_Ly9UL-0Y are COMPILATIONS - L7Pp also carries a Brad
    # Pitt red carpet, X8 also carries a kitchen ad - so grouping them by id
    # over-restricts their other windows. Accepted knowingly: the alternative
    # is grouping by (id, time range), and a rule nobody can check by looking
    # at one frame is a rule that rots. Both are small contributors.
    "sag2020_white": ["e1hAV-ZrRpI", "nivqKWke94k", "L7PpXV1agc8",
                      "X8_Ly9UL-0Y", "_XfKW4nfMwI", "6VOJ9NwMf14"],
    # The Graham Norton red couch: Ian McKellen, Julie Walters, Aniston and
    # Reese Witherspoon in a row. Three uploads of ONE episode - the frames
    # match at 0.996 and the guests are in the same seats in the same clothes.
    # qc/groups/GY_check.jpg.
    "graham_norton": ["VsT5pB04QMI", "zuVUp2qEnHE", "hfXZ0jZ6_NU"],
    # Golden Globes acceptance, black halter with the beaded neckline, at the
    # podium. yN_Tp10MHmQ carries the telecast's own "JENNIFER ANISTON /
    # ACTRESS - TV SERIES - MUSICAL OR COMEDY" chyron on some windows, which
    # is a burned-in super and is flagged in the handback. qc/groups/G07.jpg.
    "globes_podium": ["MpEnM_zYNgo", "yN_Tp10MHmQ"],
    # An Emmy telecast: the gold dress at the podium and the nominee montage
    # from the same broadcast, two uploads with different network bugs (NBC,
    # CTV). qc/groups/GY_check.jpg.
    "emmy_telecast": ["0vy5wFgkP2U", "Enc2ocQRXik"],
    # The same sit-down interview, black jacket, blue-green studio wall,
    # pillarboxed the same way in both uploads - 1.00 of one side's windows
    # match, at 0.997. qc/groups/G05.jpg.
    "blackjacket_sitdown": ["CFQcpm-wKuk", "UDcgIYu-TEE"],
    # A 90s talk show, brown tee, blue curtain, the same gold hand sculpture
    # over her shoulder in both. qc/groups/G06.jpg.
    "browntee_90s": ["Lko6LrBHSRc", "vsxLNncKDz0"],
}
# LOOKED AT AND REJECTED. Kept because the CLIP metric will propose all of
# these again next pass and somebody has to know they were already judged.
#
#   5O3fyVHdw50 / 6YGaOzMMQUs / HyJALzFY7VU / InUyN6CduEA / TtyNQ3RNMyg /
#   jHtULFrKa2g / ssiU8JHS-Eo - proposed as one cluster of 24 shots, and it is
#   not one shoot. It is "a chat-show couch in front of a lit city skyline":
#   black strapless at the Tonight Show desk, black turtleneck at Leno's,
#   black tank in a teal chair at Late Night, a patterned strapless and a pale
#   pink knit on Conan's purple mountain backdrop, and InUyN6CduEA is not even
#   a talk show - it is a daytime interview against a window. Seven different
#   days. qc/groups/G00.jpg.
#   8Na0YrtG3AI / MfX4_OB5pJ4 - both Leno, both 90s, but one is the neon-swirl
#   backdrop with the Rachel bob and the other is the skyline backdrop with
#   long hair. Different years. qc/groups/G02.jpg.
#   B9npiMH76eU / ca5T29K5tn8 - Friends, different episodes, different sets
#   and seasons. The 1.000 pair that proposed them is a black frame.
#   qc/groups/G04.jpg.
GROUP_OF: dict[str, str] = {v: k for k, vs in GROUP.items() for v in vs}
# A GROUP may hold no more than this share of the film's shots. Lower than the
# id-level 8% on purpose: 8% of 365 shots is 29, and 29 shots of one afternoon
# is the complaint. 5% is 18 - which is exactly what the Horrible Bosses
# junket held in V7, so this binds on the case it was written for.
GROUP_CAP_FRAC = 0.05


def group_of(tag: str) -> str:
    """The visual group a picture belongs to. Ungrouped sources - and every
    still, which is single-use anyway - are their own group, so a caller can
    use this everywhere the source id was used and get the old behaviour where
    no grouping applies."""
    return GROUP_OF.get(tag, tag)


def _window_banned(vid: str, t: float, dur: float = MAX_SHOT) -> bool:
    """True if a shot of `dur` seconds starting at t would show a banned
    graphic. Defaults to the ceiling, which is the safe direction for pool
    membership; callers that know the shot length should pass it."""
    for a, b in BANNED_WINDOW.get(vid, ()):
        if t + dur > a and t < b:
            return True
    return False


def windows(vid: str, start: float = HEAD, end: float | None = None,
            spread: float = SPREAD, subject: bool = False) -> list[tuple[str, float]]:
    """Every usable window in one source: bright, not a title card, and - when
    `subject` is set - containing a face."""
    if vid in BANNED or vid not in DUR:
        return []
    stop = min(DUR[vid] - tail_for(vid), end if end is not None else DUR[vid])
    out, t = [], start
    while t < stop:
        if (_bright(vid, t) and not _branded(vid, t)
                and not _window_banned(vid, round(t, 2))
                and _continuous(vid, round(t, 2))):
            if not subject or _has_subject(vid, round(t, 2)):
                out.append((vid, round(t, 2)))
        t += spread
    return out


def interleave(groups: list[list[tuple[str, float]]]) -> list[tuple[str, float]]:
    """Round-robin across sources so consecutive shots come from different
    footage.

    Each source's windows are SHUFFLED first, deterministically by source id.
    Without that, interleaving walks every source from its head, and a cursor
    that stops after 100 shots has only ever seen the first few minutes of each
    file - which is why 25 minutes of Friends yielded four shots (F4). Shuffling
    means the same small number of picks samples the whole runtime instead.
    The seed is fixed so a rebuild is reproducible."""
    groups = [_shuffled(g) for g in groups]
    out, i = [], 0
    groups = [g for g in groups if g]
    while any(i < len(g) for g in groups):
        for g in groups:
            if i < len(g):
                out.append(g[i])
        i += 1
    return out


def _shuffled(g):
    if not g:
        return g
    r = random.Random(g[0][0])          # seeded on the source id
    out = list(g)
    r.shuffle(out)
    return out


def pool(vids: list[str], **kw) -> list[tuple[str, float]]:
    return interleave([windows(v, **kw) for v in vids])


def spool(vids: list[str], **kw) -> list[tuple[str, float]]:
    """A pool for a section whose narration is about her: face required."""
    return interleave([windows(v, subject=True, **kw) for v in vids])


# ── pass 14: the repetition fix ────────────────────────────────────────
# The V6 cut drew 174 video shots from 40 sources and nine of them carried
# 60% of it, so it repeated. These are the survivors of a 111-source harvest,
# every one rendered to a frame and read (qc/NEWSRC_0..4.jpg); the rejects are
# in BANNED above with the reason.
#
# They are NOT era-locked. L1 and L2 stay on their curated 90s sources - the
# whole point of era locking is that a 2019 talk show cannot play under "she
# was accepted into the Rudolf Steiner School". These widen the pools that are
# about her now, plus the film/awards stretches.
EXTRA_SRC = [
    "-MXQ_3DNX_Y", "1ll6M4T5qSA", "3-2agJ776mw", "3117yQRAees",
    "5O3fyVHdw50", "5zcFaqFbrTU", "6B7lM_DGMqA", "6VOJ9NwMf14",
    "6YGaOzMMQUs", "7G6p0mq35xA", "7QZcFa-MXrQ", "7tqDOEcsUio",
    "8Na0YrtG3AI", "AEXWuXEyXuY", "B9npiMH76eU", "BOLYn4l_pMs",
    "CFQcpm-wKuk", "CIqe67jsdoQ", "Cb6Nt53D3RY", "CeHYHu3C064",
    "CuxqL5IsiOc", "Enc2ocQRXik", "Evs4VoyaR4g", "GS8nqYf5NvQ",
    "H-4zyq-NNFQ", "HyJALzFY7VU", "Imj67wZds0s", "K_mzQZfvI04",
    "L7PpXV1agc8", "LOEWwW97yW4", "LTS9zTgxBa4", "Lko6LrBHSRc",
    "MfX4_OB5pJ4", "NyY8lvGQbKw", "ONzCbZ8jLLo", "OWWODP5PYn8",
    "OiI3zevZEHQ", "PpKHUqJ7DRY", "PsXXGwspfNk", "QFGVCVsAvYg",
    "QMp5NDQlZoE", "QmeDaLhFnzA", "QqBh30QBzJo", "TKAfdfzBiDs",
    "TtyNQ3RNMyg", "UDcgIYu-TEE", "VdnzR0F5NVg", "VjmD2wK8Dsw",
    "VsT5pB04QMI", "X4h873T3XS4", "X8_Ly9UL-0Y", "Y89PlheZYHg",
    "_XfKW4nfMwI", "alR1NeotIso", "b6ETxfr76Ts", "bL7Hcjfz26s",
    "bifTkKXGu3w", "bncSYcADOQg", "ca5T29K5tn8", "dnXEvHwiGIo",
    "eHHBXaUdna4", "eKKDRdE-WKs", "ejMo0aIevj8", "f6zuX21_098",
    "fcR1FXo00W8", "gb67coRCOl0", "hOJ4qbGYiCs", "hPX9_UV478Q",
    "hPni_C4EYK0", "hfXZ0jZ6_NU", "idQRtrPGHjw", "iwiHdFYJf9k",
    "jD2V79_dNuQ", "kko5oEDAH40", "le9OrAofjP4", "nKHOp72TIso",
    "nZWKuh-Calk", "nabfcX7IfsE", "o9BrmbmF4QI", "oSb8auYSOcA",
    "ozt4H_ILZT4", "q6X1jyPSxhs", "sIc7ae_ylSs", "ssiU8JHS-Eo",
    "vMuarx9iWdg", "vUF8TJXSzKg", "vsxLNncKDz0", "ykScGjlKsCQ",
    "zuVUp2qEnHE",
]

# ── source groups ────────────────────────────────────────────────────────
# ANONYMOUS DEMONSTRATORS ARE THE FORMAT, and banning them was my mistake.
#
# aZiwqY_e9ZQ, d7hb5JTpbFE, f8YLI3POJnM and C03vLBSWJN0 were all banned for
# "not being her". Then I finally looked at the reference the whole project is
# supposed to match, and at 7:08 its SUN SALUTES wedge sits over a stock woman
# doing a sun salute, and at 7:32 its TUESDAY card sits over a stock woman
# mid-exercise. REFERENCE_SPEC.md says it outright and I had not acted on it:
# "Stock footage of anonymous people is the norm ... those clips are the
# format."
#
# So the identity gate belongs on the sections ABOUT HER - the biography, her
# quotes, the hook - and NOT on the exercise demonstrations, where an
# anonymous body performing the movement is exactly right and an AI-generated
# empty room with a band on the floor is exactly wrong.
#
# The sources that stay banned are the ones with burned-in broadcast graphics
# (GMA, MARCH FITNESS, Better, InStyle covers), which is a different problem.
DEMO_CLEAN   = ["f8YLI3POJnM",   # three people on Pvolve mats, no branding
                "C03vLBSWJN0",   # banded lateral raise, bird-dog, clean studio
                "aZiwqY_e9ZQ",   # reverse lunges on sliders (small InStyle bug)
                "d7hb5JTpbFE",   # studio demo, clean
                "fnTFycw2q1w",   # yoga and plank work outdoors
                "cBZC-8S9b8g",   # Pvolve on Today (NBC bug, used sparingly)
                # Added 25 Aug 2026 with DEMO_SRC5. They must be listed HERE as
                # well, not only there: cuts.py measures DEMO_CLEAN, and a
                # window with no cut measurement gets clear_seconds()'s
                # optimistic 99.0 "no data" answer, which reads as "no cut" and
                # lets a shot run straight through one.
                "1JDlnr1ARyw", "WBnHWsTGAR0", "hS2OHNdo1SM", "fJUyYBh1L0s",
                "M3apR08_HMU", "eYne5mPO71c", "kfu9Vsyvut8", "BMpF6c81cSY"]

# What is left of the Pvolve campaign after every window in all ten of the
# original sources was rendered and looked at. Four films, and she is the
# only person in them.
HER_TRAIN_SRC = ["lrZKJPVn89s", "JJLe4jmbrN0", "qqipyG6bpLA", "voC2DxCL6jQ"]
# Long, clean, unbranded interviews of her - added because the campaign films
# are short and the tightened gate left the hook with 18 windows for 16 shots.
TALK_SRC      = ["BpgMda_4JDI", "qAp9lq2CT5M"]
DEMO_SRC      = ["cBZC-8S9b8g", "G1HmBSzxXV0", "6a6MDIvrc_o", "Oc9ufH7lxnw",
                 "FXywTKuiYnM", "fnTFycw2q1w", "aZiwqY_e9ZQ"]
# Real archive, added after the generated establishing shots proved to be a
# stand-in rather than the thing itself. Slotted by era so a Friends clip
# cannot play under a line about 2021.
# Young-Aniston INTERVIEW footage. She is talking, not playing a part, so it
# reads as archive under any biography line and is the only moving picture
# available for L1 and L2 - nobody filmed her childhood.
ARCHIVE_TALK  = ["LzisOKB_sEU", "Zyy2RUx6BRM"]
# Her father. Not her, so the identity gate rejects every window; these reach
# the cut only through the cue table, which is the point.
FATHER_SRC    = ["wR1SuuB-hWI",   # her father in character as Victor Kiriakis
                 "_K3cpT4-upk"]   # John Aniston interviewed, Days of our Lives
# Her first SCREEN work, 1990-93. Era-correct for L3 and no earlier.
EARLY_SRC     = ARCHIVE_TALK + FATHER_SRC + [
                 "CsLRK1JphL4",   # Leprechaun, 1993
                 "7mM-82tY-ts",   # her scenes from the Ferris Bueller pilot
                 "BrbwSDa3crU"]   # the 1990 NBC promo she is in
FRIENDS_SRC   = ["sjLDT-hLkFQ", "9Piy6m3UF3w", "KHmVdNl1cos",
                 "cZh-kPkKcvU", "XbywiblA1eQ", "Xm0jeY5Mp5c"]  # actual Friends
# Pass 3. The narration names the Emmy, the Golden Globe and the Screen Actors
# Guild award and previously showed none of them.
AWARDS_SRC    = ["e1hAV-ZrRpI", "nivqKWke94k", "MpEnM_zYNgo",
                 "0vy5wFgkP2U", "yN_Tp10MHmQ", "D0PDC03Cu5c", "wXjjzHrpZCQ"] + EXTRA_SRC
# CsLRK1JphL4 was listed here as childhood material and fed life_L1 and
# life_L2 - her birth, Sherman Oaks, the move to New York, the Waldorf school.
# It is Leprechaun, 1993. In the V5 cut it played her holding a pump-action
# shotgun under "to New York City when she was six" (shot 46), and again under
# "on the NBC soap opera Days of our Lives" (39) and "still at Waldorf" (56).
# There is no childhood footage of her; those blocks run on stills.
CHILD_SRC     = []
FILMS_SRC     = ["Ny0zaM7RNg0", "aNAAWzLOEKc", "asBfqGQ7b6E", "oZaoendJ5GQ",
                 "vPrtuy_4lHM",
                 "P3IsUOSHlnU",   # Cake trailer
                 "Ws-9ra38AlI",   # Marley & Me trailer
                 "JlpIdAmkT_k"] + EXTRA_SRC   # The Morning Show
NOW_SRC       = ["dO0akkBV8nc", "wyLz-XeJL9o", "ZoqjGormrds", "BpgMda_4JDI",
                 "qAp9lq2CT5M", "iUVWGBaW1b0", "2A2MCCK_pHs", "Q0Iu0ZZ72Ic",
                 "hxWPeK2YHLw", "jHtULFrKa2g", "yQVyPITj6Y8", "wvO0FMjlnHo",
                 "lLqtWLL5pXw", "Tk07W15MCr0", "ol-7Wjrk3hk", "_wUC6czee2s"] + EXTRA_SRC
TURN_SRC      = ["K3puGMuBWKw", "_17zulAlAzw", "InUyN6CduEA", "XYcNVESFs4Y",
                 "ak5GBTYJArw", "zbnHO-r5HRs", "BZsQtQ-gEw4"] + EXTRA_SRC
TRAINER_SRC   = ["zbCniZvVfgQ", "W2A_JiQgHrs", "zMLEopVAzEE"]


S  = lambda n: (f"still:{n}", 0.0)
SP = lambda a, b, la, lb: (f"split:{a}|{b}|{la}|{lb}", 0.0)

# Real photographs (photos/), registered under short stable names so
# still:ph_NAME resolves the same way still:q_gymfloor does - see
# build5._still_path. Grouped by what the picture actually SHOWS
# (carpet90s, friends, globes, portrait94, pressportrait) - never by the
# query that harvested it. A category used to be named "pvolve" because that
# was the search phrase, and both members were press portraits (a 2018
# InStyle Awards red carpet shot, a hairstyles-article studio photo) with no
# workout, diet or Pvolve content in frame - a caller reading the category
# name would have been misled into thinking this library holds fitness
# photography of her. It does not: the honest count of diet/fitness/workout
# photographs here is ZERO. This is only a REGISTRATION SURFACE: nothing here
# adds a photo to any section's texture weave, that is section 4's call.
# Every name was assigned programmatically from manifest/photos.json["names"],
# never typed by eye, and every photo behind it has been through the
# eye-audit - see qc/PHOTOS_*.jpg for what stayed and
# manifest/photos_denied.json for what was cut and why (16 denied: other
# people mislabelled as her by the image search - Jennifer Lopez, Jennifer
# Lawrence - plus one two-up composite that was genuinely her but with Brad
# Pitt filling the other half of the frame; 19 photographs survive).
_PHOTOS_MANIFEST = ROOT / "manifest" / "photos.json"
PHOTO_STILLS: dict = {}
if _PHOTOS_MANIFEST.exists():
    _pj = json.loads(_PHOTOS_MANIFEST.read_text(encoding="utf-8"))
    for _pn in sorted(_pj.get("names", {})):
        _cat = _pn[len("ph_"):].rsplit("_", 1)[0]
        PHOTO_STILLS.setdefault(_cat, []).append(S(_pn))
ALL_PHOTOS = [s for cat in PHOTO_STILLS.values() for s in cat]

# A labelled card is a STATEMENT, not texture, so it may appear exactly once
# and only on the words that name it. In the V5 cut LOS ANGELES / 1990 played
# four times, RUDOLF STEINER SCHOOL twice five seconds apart, LAGUARDIA twice
# and SHERMAN OAKS twice - because the cue table forced the card AND the
# texture weave spent it, and because life_L1..L5 are five separate cursors
# that each spend their own copy. The fix is structural: every still named
# here is now reachable ONLY through cues.py, and none of them appears in any
# texture list. build5 asserts the count at the end of the picture pass.
PLACE_LABEL = {
    "p_shermanoaks": ("Sherman Oaks", "California, 1969"),
    "p_nycstreet":   ("New York City", "she was six"),
    "p_school":      ("Rudolf Steiner School", "Upper East Side"),
    "p_artschool":   ("LaGuardia", "the Fame school"),
    "p_lasign":      ("Los Angeles", "1989"),
    "p_diner":       ("Six years", "before Friends"),
}

BIO_TEXTURE = [
    S("p_la70s"), S("p_nycskyline"), S("p_corridor"), S("p_studio90s"),
    S("p_soapset"), S("p_waitress"), S("p_office"), S("p_hospital69"),
    S("p_bike"), S("p_marquee"), S("p_carpet"), S("p_apartment"),
    S("p_nychome"), S("p_lapalms"), S("p_audition"), S("p_tvdial"),
    S("s_soap"), S("s_school"), S("s_diner"), S("s_payphone"), S("s_set"),
]
# q_filmset, q_spine, q_ropes, q_treadmill, q_clockgym and the two spin bikes
# are all cued in W1/W3/O1 and are therefore out of the texture. The two
# captioned split-screens are out too: they were landing on sentences that had
# not reached the injury yet - BEFORE THE INJURY / AFTER sat under "the part
# most articles about her get wrong", and IMPACT / LOW IMPACT under "Jennifer
# trained hard, and I mean hard".
TURN_TEXTURE = [
    S("q_harness"), S("q_eiffel"), S("q_paris"), S("q_physio"),
    S("q_kinesio"), S("q_gloves"), S("q_stretch"), S("s_room"),
    S("s_clock"), S("q_gymfloor"), S("q_towel"), S("q_slantboard"),
]

# Training and diet needed their own illustrative material too - v5 ran those
# sections almost entirely on campaign footage and interviews.
# q_gymfloor is in TURN_TEXTURE as well and the two cursors spent it 17s apart
# in the pass-7 build - the same empty studio twice inside the hook.
TRAIN_TEXTURE = [
    S("q_dumbbells"), S("q_mat"), S("q_slantboard"),
    S("q_towel"), S("q_stretch"), S("q_gloves"), S("q_heavybag"),
    S("s_bands"), S("s_yogamat"), S("s_dumbbell"), S("s_room"),
]
# q_kitchen, q_watchclock, f_lemonwater and q_running are cued in D1/D3/W1.
# In the V5 cut q_watchclock played twice five seconds apart and once under
# "or a vegetable lasagna"; q_running played under "She drinks".
# TEN stills for four diet blocks, and the first of them a lunch plate. That
# is how D3 shot 211 got f_saladplate - a grilled chicken breast on salad
# leaves with tomato and lime - under a breakfast quote, with the narration on
# "to start the day hydrated, and it is high in vitamin C". Two things had to
# be true at once for that, and both are now false:
#
#   * the pick was NOT by meaning. build5 ranks card-bed stills with
#     semantic.score(), but semantic.main() had never embedded a single still,
#     so every still scored 0.0000, argmax() returned index 0, and the code
#     took element 0 of this list while its comment said "choose by meaning
#     like everything else does". Measured: f_saladplate 0.0000, f_avocado
#     0.0000, f_citrus 0.0000 - all of them. See semantic.embedded().
#   * the list had almost nothing congruent to offer anyway. Of ten entries,
#     one is breakfast-adjacent.
#
# So the ranker now runs, and it now has material. Re-measured with the stills
# embedded, against shot 211's own narration, the ranking is f_lemonwater
# .290, f_water2 .283, f_citrus .276, f_juice .268, f_smoothie .260 - and
# f_saladplate ninth of fourteen. f_saladplate stays in the list because it is
# honest texture for a lunch line; what changed is that something has to ASK
# for it. Nothing here may appear in cues.py (see the p_office note above),
# which is why f_lemonwater, f_juice, f_eggs2, f_porridge, f_burger,
# f_mexican and f_froyo2 are all absent.
DIET_TEXTURE = [
    S("q_fridge"), S("q_market"), S("f_saladplate"), S("f_soup"),
    S("f_greentea"), S("f_smoothie"), S("s_water"), S("s_eggs"),
    S("s_plate"), S("f_clock"),
    # breakfast and hydration, the half of the diet section that had no
    # pictures of its own
    S("f_citrus"), S("f_water2"), S("f_avocado"), S("f_oats"), S("f_berries"),
]
NOW_TEXTURE = [
    S("q_award"), S("q_flashbulb"), S("q_tvwall"), S("q_gymfloor"),
    S("q_sunrise"), S("q_running"), S("q_mat"), S("q_bands"),
]


# Generated stills were never luminance-gated the way video windows are, so
# seven dark frames survived into the v5 cut. Measured once, excluded here.
DARK_STILLS = set(json.loads(
    (ROOT / "manifest" / "dark_stills.json").read_text()))     if (ROOT / "manifest" / "dark_stills.json").exists() else set()


def _drop_dark(items):
    out = []
    for it in items:
        k = it[0]
        if k.startswith("still:") and k[len("still:"):] in DARK_STILLS:
            continue
        if k.startswith("split:") and any(
                n in DARK_STILLS for n in k[len("split:"):].split("|")[:2]):
            continue
        out.append(it)
    return out


def _once_only(item) -> bool:
    """A shot that names something can only be used once.

    A labelled place card (SHERMAN OAKS / CALIFORNIA, 1969) or a captioned
    split-screen is a statement, not texture. Cycling the texture list put
    SHERMAN OAKS and LOS ANGELES on screen twice each inside sixty seconds,
    which reads as an editing mistake rather than a motif. Unlabelled scenery
    may repeat; anything carrying words may not."""
    kind = item[0]
    if kind.startswith("split:"):
        return True
    return kind.startswith("still:") and kind[len("still:"):] in PLACE_LABEL


def weave(clips, texture, every=1):
    """Interleave illustrative shots among the clips.

    Labelled items are spent once, in order. Everything else cycles, so the
    ratio holds across a long section instead of running dry after 50 shots
    the way the first version did.
    """
    if not texture:
        return list(clips)
    once = [t for t in texture if _once_only(t)]
    loop = [t for t in texture if not _once_only(t)]
    out, oi, li = [], 0, 0
    for i, c in enumerate(clips):
        out.append(c)
        if i % every == every - 1:
            if oi < len(once):
                out.append(once[oi]); oi += 1
            elif loop:
                out.append(loop[li % len(loop)]); li += 1
    return out


BIO_TEXTURE   = _drop_dark(BIO_TEXTURE)
TURN_TEXTURE  = _drop_dark(TURN_TEXTURE)
TRAIN_TEXTURE = _drop_dark(TRAIN_TEXTURE)
DIET_TEXTURE  = _drop_dark(DIET_TEXTURE)
NOW_TEXTURE   = _drop_dark(NOW_TEXTURE)

# ERA DISCIPLINE: the life section draws only on era-appropriate footage.
# v4 let 2024 red-carpet clips play under 1990s narration because its pools
# were section-level only and the v3 relevance gate had been dropped.
def face_first(pool_):
    """Put the biggest face at the front.

    F6: the v5 cut opened on a leg on a mat and then a close-up of a foot. The
    thumbnail is her face; the first frame should be too."""
    def score_(r):
        rec = PRESENCE.get(f"{r[0]}@{r[1]}")
        return -(rec or {}).get("biggest", 0.0)
    clips = [r for r in pool_ if not r[0].startswith(("still:", "split:"))]
    rest = [r for r in pool_ if r[0].startswith(("still:", "split:"))]
    best = sorted(clips, key=score_)[:6]
    return best + [r for r in pool_ if r not in best]


# The V6 pool map is RETIRED. It was hook / subscribe / life x5 / turn /
# workout_intro / week_intro / week / diet_intro / diet / outro - a biography
# structure with a subscribe ask and a read-out training week and food list.
# script.md has none of those: 21 blocks in nine sections (hook, before,
# injury, method, now, evidence, diet, takeaway, close), no biography, no
# subscribe ask, no WK_/FD_ generated blocks. Keeping the old dict alive as a
# fallback would only give a mis-mapped block somewhere plausible to land, so
# it is gone; POOLS is built at the bottom of this file from SECTIONS.

# The list graphic reveals the food names one or two at a time; the picture
# under it must be the food the list JUST named. V5 walked the category list
# by shot index instead, which drifts as soon as a reveal step adds two names,
# and it showed bananas under a list ending PEACHES, sweet potato under one
# ending MUSHROOMS, and a squash stew under HEALTHY FATS / SEEDS.
# Several stills deliberately carry two foods - f_stonefruit is peaches AND
# plums, f_quinoa is quinoa AND couscous - which is why two names can share a
# picture. FOOD_SPARE covers the case where that would put the same frame on
# two consecutive shots.
FOOD_PIC = {
    "FRUITS":       {"BERRIES": "f_berries", "APPLES": "f_apples",
                     "BANANAS": "f_bananas", "PEACHES": "f_stonefruit",
                     "PLUMS": "f_stonefruit", "KIWIS": "f_kiwi"},
    "VEGETABLES":   {"SPINACH": "f_greens", "KALE": "f_greens",
                     "BROCCOLI": "f_broccoli", "CELERY": "f_broccoli",
                     "TOMATOES": "f_tomatoes", "MUSHROOMS": "f_tomatoes",
                     "SWEET POTATOES": "f_sweetpot"},
    "PROTEINS":     {"CHICKEN": "f_chicken", "TURKEY": "f_turkey",
                     "EGGS": "f_eggs2", "FISH": "f_fish",
                     "LEAN BEEF": "f_steak"},
    "WHOLE GRAINS": {"QUINOA": "f_quinoa", "COUSCOUS": "f_quinoa",
                     "OATS": "f_oats", "BROWN RICE": "f_rice",
                     "WHOLE WHEAT PASTA": "f_rice"},
    "HEALTHY FATS": {"OLIVE OIL": "f_oliveoil", "AVOCADO": "f_avocado",
                     "ALMONDS": "f_nuts", "WALNUTS": "f_nuts",
                     "SEEDS": "f_seeds"},
    "BEVERAGES":    {"WATER": "f_water2", "BLACK COFFEE": "f_coffee2",
                     "HERBAL TEA": "f_tea", "CELERY JUICE": "f_juice"},
}
FOOD_SPARE = {
    "FRUITS":       ["f_berries2", "f_citrus", "f_melon"],
    "VEGETABLES":   ["f_saladbowl", "f_peppers", "f_cucumber", "f_asparagus"],
    "PROTEINS":     ["f_eggs3", "f_prawns"],
    "WHOLE GRAINS": ["f_lentils", "f_bread", "f_porridge"],
    "HEALTHY FATS": ["f_olives", "f_avocado", "f_nuts"],
    "BEVERAGES":    ["f_greentea", "f_lemonwater", "f_water2"],
}

FOOD_BY_CAT = {
    "FRUITS":       ["f_berries", "f_apples", "f_bananas", "f_stonefruit",
                     "f_kiwi", "f_berries2", "f_citrus", "f_melon"],
    "VEGETABLES":   ["f_greens", "f_broccoli", "f_tomatoes", "f_sweetpot",
                     "f_saladbowl", "f_peppers", "f_cucumber", "f_asparagus"],
    "PROTEINS":     ["f_chicken", "f_fish", "f_eggs2", "f_turkey",
                     "f_eggs3", "f_prawns", "f_steak"],
    "WHOLE GRAINS": ["f_quinoa", "f_oats", "f_rice", "f_lentils",
                     "f_bread", "f_porridge"],
    "HEALTHY FATS": ["f_oliveoil", "f_avocado", "f_nuts", "f_seeds", "f_olives"],
    "BEVERAGES":    ["f_water2", "f_coffee2", "f_tea", "f_juice",
                     "f_greentea", "f_lemonwater"],
}
FOOD_STILLS = [x for v in FOOD_BY_CAT.values() for x in v] + [
    "f_lasagna", "f_burger", "f_smoothie", "f_mexican", "f_froyo2", "f_clock",
    "f_saladplate", "f_soup"]

# Each movement pinned to a picture that ACTUALLY SHOWS IT.
# MOVE_REVIEW.md records the audit that forced this: of the previous 17 video
# pins, 15 showed something else - three women standing under BANDED GLUTE
# BRIDGE, a face close-up under REVERSE LUNGE, a burned-in caption reading
# "LATERAL DELTOID RAISE" under OVERHEAD PRESS. The footage simply does not
# exist; nobody has filmed her doing a dead bug. Generated stills do, and each
# one below was looked at before it went in.
# The two video pins that were verified correct are kept.
# Four of the seventeen now point at REAL footage of a person doing the
# movement, which is what the reference does throughout. CLIP was used to
# shortlist candidates and every one was then looked at; it got roughly six of
# seventeen right on its own, and the pool simply does not contain a slant
# board squat or a dead bug, so the generated stills stay where no real clip
# exists. A generated still that depicts the movement beats real footage of the
# wrong movement.
# Pass 13: OVERHEAD PRESS pointed at C03vLBSWJN0@3.0, which renders as a
# blurry close-up of a leg, and PLANK at fnTFycw2q1w@38.2, which is an
# upward dog. Correct generated stills for both were sitting unused in
# stills_move/. Read off the V6 contact sheets (shots 149 and 153).
# DEAD BUG is still wrong - its card sits over an abstract torso crop - but
# mv_deadbug.jpg is a malformed two-figure composite, so there is nothing
# better to point it at yet.
MOVE_FOOTAGE = {
    "BANDED GLUTE BRIDGE":     ("still:mv_glutebridge", 0.0),
    "STANDING HIP ABDUCTION":  ("still:mv_hipabduction", 0.0),
    "SLANT BOARD SQUAT":       ("still:mv_slantsquat", 0.0),
    "REVERSE LUNGE":           ("cBZC-8S9b8g", 147.0),   # real: women lunging
    "THE FIFTEEN FIFTEEN":     ("still:mv_intervals", 0.0),
    "SPIN, ELLIPTICAL OR RUN": ("still:mv_elliptical", 0.0),
    # was JJLe4jmbrN0@8.0. Rendering it at +1.6s shows the source cutting to a
    # DIFFERENT woman doing the same raise, inside the shot.
    "BANDED LATERAL RAISE":    ("still:mv_lateralraise", 0.0),
    # was c_ci5IriLG0@48.0 - her, and a correct kneeling row, but the frame is
    # cropped so close that the movement is unreadable and the source is now
    # banned for its ET graphics. mv_kneelingrow was regenerated for this.
    "KNEELING ROW":            ("still:mv_kneelingrow", 0.0),
    "PLANK":                   ("still:mv_plank", 0.0),    # real: two people in plank
    "DEAD BUG":                ("C03vLBSWJN0", 31.8),    # real: on back, legs extended
    "BANDED ROW":              ("still:mv_bandedrow", 0.0),
    "OVERHEAD PRESS":          ("still:mv_overheadpress", 0.0),     # real: dumbbell press overhead
    "QUADRUPED LEG RAISE":     ("still:mv_quadruped", 0.0),
    "JUMP ROPE":               ("still:mv_jumprope", 0.0),
    "PAD WORK":                ("still:mv_padwork", 0.0),
    "CAT COW":                 ("still:mv_catcow", 0.0),
    "HIP OPENERS":             ("still:mv_hipopener", 0.0),
}

# The day card itself gets a chosen picture, exactly as each movement does.
# Before this it was whatever the ungated week pool handed over: a MARCH
# FITNESS studio segment with three men held TUESDAY and again SUNDAY, a GMA
# reporter held MONDAY, a Verizon red-carpet step-and-repeat held FRIDAY, a
# woman having a facial held THURSDAY, and SUNDAY - REST - showed three people
# mid-workout. See d_* in place_gen.py.
DAY_FOOTAGE = {
    # The reference puts its TUESDAY card over a stock woman mid-exercise
    # (7:32), not over an empty room. Real demonstrators where the day's theme
    # has one; the generated still stays only where footage would contradict
    # the card - there is no boxing in this pool, and REST cannot be people
    # working out.
    "MONDAY":    ("f8YLI3POJnM", 9.4),     # three people, lunge and reach
    "TUESDAY":   ("cBZC-8S9b8g", 195.0),   # mid-step cardio on the mats
    "WEDNESDAY": ("C03vLBSWJN0", 19.0),    # core work on the back
    # was 47.8, which spans a cut. clean_pin nudged it to 56.3 and that IS
    # continuous - but it is a tight close-up of FEET on sliders, under a card
    # reading "upper body and back". The nudge is content-blind; it only knows
    # about cuts. 75.0 is clean AND shows two women in a plank on the sliders,
    # which is what the card claims. Read off qc/THURSDAY_OPTS.jpg.
    "THURSDAY":  ("aZiwqY_e9ZQ", 75.0),    # upper body, plank and press
    "FRIDAY":    ("still:d_friday", 0.0),  # gloves and rope - no boxing footage
    "SATURDAY":  ("fnTFycw2q1w", 15.8),    # hands-and-knees mobility stretch
    "SUNDAY":    ("still:d_sunday", 0.0),  # REST. People exercising would lie.
}

# ══════════════════════════════════════════════════════════════════════════
# PASS 17 — THE POOL MAP FOR THE FILM WE ARE ACTUALLY MAKING
# ══════════════════════════════════════════════════════════════════════════
#
# script.md is 21 blocks in nine sections and there is no biography in it:
#
#   hook      H1   the injury on the Murder Mystery 2 set, and the promise
#   before    W1   the volume - Ingber, yoga, boxing, jump rope
#             W2   the 45-minute rule, the burnout, the taped Barbie doll
#   injury    W3   what a lumbar injury takes off the menu
#   method    W4   Pvolve, mechanically - bands, time under tension, 3 planes
#   now       W5   Dani Coleman, three times a week, 30-40 minutes
#             W6   duration: every class fifteen minutes or less
#   evidence  W7   the Exeter trial, and who paid for it
#   diet      D1   16:8 fasting          D4  lunch, dinner, the prep system
#             D2   the morning order     D5  the cheat-day correction
#             D3   juice, coffee, food   D6  collagen, TODAY, osteoporosis
#   takeaway  O1   the four things that transfer
#   close     O2   gentler, and stronger
#
# WHAT THE POOLS HAVE TO SOLVE, in order of how much damage each has done:
#
# 1. REPETITION. 174 shots from 40 sources, nine carrying 60%. Three defences
#    here: every source contributes at most CAP_PER_SOURCE windows to the
#    whole film's pools (so a heavy source cannot dominate even if it is the
#    best semantic match every time); the clip windows are dealt ROUND-ROBIN
#    across the nine sections from one shared list, so two sections cannot
#    both spend the same window; and Reels.TAKEN (build5) makes a window
#    single-use across the whole film rather than merely within one pool.
#
# 2. THE TRAINING FOOTAGE IS GONE. TRAIN_OK has nine hand-verified windows;
#    exactly ONE survives the live gate (qqipyG6bpLA@6.2 - the rest fail
#    _continuous, and JJLe4jmbrN0 / voC2DxCL6jQ are 91%-captioned ads). So the
#    workout chapters run on what the reference itself runs on: anonymous
#    demonstrators (DEMO_SRC5), generated movement stills (mv_*), gym-object
#    stills (q_*, s_*) and photographs. Not on footage of her training,
#    because there is one second of it.
#
# 3. THE PHOTOGRAPHS. Nineteen audited press photographs were embedded,
#    registered in ALL_PHOTOS, and in NO POOL. They are in the textures below,
#    at the FRONT of each list, because weave() spends a texture in order and
#    a photograph at the back of a long list never gets reached.
#
# ERA: not locked, and deliberately. Rule 4 - lock only where the script is
# about a period, and this script is about 2021-2026 throughout. All nineteen
# photographs were read (qc/PHOTOS_0..1.jpg) and despite the harvest queries
# saying "1990s red carpet" and "1994 portrait" every one of them is a modern
# press photograph, so none of them contradicts a sentence about now.

# Her, talking: interviews, press junkets, red carpet. The identity gate is ON
# for all of these (spool) because every block is about her.
HER_SRC5 = sorted(set([
    "dO0akkBV8nc", "qAp9lq2CT5M", "2A2MCCK_pHs", "jHtULFrKa2g", "yQVyPITj6Y8",
    "lLqtWLL5pXw", "_wUC6czee2s", "K3puGMuBWKw", "InUyN6CduEA", "zbnHO-r5HRs",
    "BZsQtQ-gEw4", "e1hAV-ZrRpI", "nivqKWke94k", "MpEnM_zYNgo", "0vy5wFgkP2U",
    "yN_Tp10MHmQ",
] + EXTRA_SRC) - set(BANNED))

# Anonymous demonstrators. REFERENCE_SPEC.md: "Stock footage of anonymous
# people is the norm ... those clips are the format." Every candidate window
# of all five was rendered and read - qc/S4_DEMOALL_0..2.jpg - and the three
# burned-in supers that turned up are in BANNED_WINDOW above.
DEMO_SRC5 = ["d7hb5JTpbFE",    # clean white studio, Pvolve mat and equipment
             "fnTFycw2q1w",    # outdoor yoga, plank and mobility
             "C03vLBSWJN0",    # studio floor work
             "f8YLI3POJnM",    # three people on Pvolve mats
             # cBZC-8S9b8g is deliberately NOT here any more. It supplies two
             # of Dani Coleman's bites, so leaving it in the demo pool let the
             # reel hand back the same interview immediately before it played
             # in full - ('T15', 'cBZC-8S9b8g') failing the consecutive-source
             # gate. It also carries an NBC corner bug. A source that is a
             # BITE source should not also be pool filler.
             # --- added 25 Aug 2026 ---------------------------------------
             # The owner's note was "too many interview videos - it should be
             # her working out if possible", and the method pool was ALSO
             # exhausting after 39 windows, which is the same shortage seen
             # from the other side: five demo sources cannot carry a film whose
             # middle third is about how the training works.
             #
             # These are full Pvolve and mobility sessions, downloaded by
             # fetch_talk.py. They are not her - the surviving windows of her
             # actually training are still only the two in HER_TRAIN5 - but
             # they are REAL training footage of the method being described,
             # which beats another talking head by a distance.
             "1JDlnr1ARyw",    # 25 min low-impact bodyweight sculpt
             "WBnHWsTGAR0",    # 15 min lower-back strengthening
             "hS2OHNdo1SM",    # 35 min hip and lower-back stretch
             "fJUyYBh1L0s",    # 20 min standing upper body, Dani Coleman
             "M3apR08_HMU",    # feel-good feel-strong yoga
             "eYne5mPO71c",    # Pvolve segment, break a sweat not your body
             "kfu9Vsyvut8",    # boxing from home
             "BMpF6c81cSY"]    # camp mode: MSA, boxing, strength

# The single surviving window of her actually training.
HER_TRAIN5 = ["qqipyG6bpLA", "lrZKJPVn89s"]

# No source may supply more than this many windows to the whole film's pools.
# The film is 365 shots and the acceptance bar is 8% (29). A source cannot
# reach 29 if it never offers more than 12 windows, and 12 x 77 sources is
# still several times the clip budget. This is the anti-repetition rule
# expressed as arithmetic instead of as a hope.
#
# Raised from 12 to 16 in pass 17, after ten sources were banned on the first
# cut's contact sheets (five junket poster walls, a FIRST LOOK super, an end
# credit roll, an Ellen two-hander, an Allure watermark with a lookalike in
# it). That took the pools from 3.2x headroom to 2.4x, which is too close to
# exhaustion for a pool whose windows are also filtered per shot by length.
# 16 windows is still at most 4.4% of a 364-shot film, and the film-level cap
# in build5 (7.5%) is the thing that actually enforces the acceptance bar.
CAP_PER_SOURCE = 16


def cap_per_source(items, n: int = CAP_PER_SOURCE):
    """At most `n` windows from any one source, in the order given.

    interleave() already round-robins the sources, so taking the first n of
    each preserves the source-alternating order that rule 1 depends on."""
    seen: dict = {}
    out = []
    for r in items:
        k = r[0]
        if seen.get(k, 0) >= n:
            continue
        seen[k] = seen.get(k, 0) + 1
        out.append(r)
    return out


def deal(items, weights: dict) -> dict:
    """Deal one list of windows into named buckets, round-robin, in
    proportion to `weights`.

    This is the structural fix for cross-section repetition. Previously each
    section called spool() on its own source list, several of those lists
    overlapped, and two sections could therefore hand out the SAME window -
    which is how oSb8auYSOcA@252.6 carried three different quote cards. Deal
    once and no window exists in two pools at all.

    Round-robin, not slicing: a slice would give the first section every
    window of the first few sources (interleave puts them first), so the
    hook would be one source and the close another. Dealing keeps every
    bucket source-diverse.
    """
    names = list(weights)
    if not names:
        return {}
    total = sum(weights.values()) or 1
    order = []
    for nm in names:
        order.extend([nm] * max(1, round(weights[nm] * 24 / total)))
    out = {nm: [] for nm in names}
    for i, r in enumerate(items):
        out[order[i % len(order)]].append(r)
    return out


# -- textures --------------------------------------------------------------
# One list per section, and NO STILL APPEARS IN TWO OF THEM - asserted below.
# A still is single-use inside a cursor, but two cursors used to be able to
# spend the same one (q_gymfloor played twice 17s apart in the pass-7 build).
# Disjoint lists make that impossible before Reels.TAKEN is even consulted.
#
# Photographs are FIRST in each list. weave() walks a texture in order and the
# tail of a long list is never reached, which is how "registered but unused"
# happens.
#
# Nothing in these lists may also appear in cues.py - a cued still that is
# also texture plays twice, which is how p_office turned up under "a
# television version of Ferris Bueller" ten seconds before it turned up,
# correctly, under "telemarketer". Asserted below.

TEX_HOOK = [
    S("ph_friends_4"),        # her at a MURDER MYSTERY 2 backdrop - H1's own film
    S("ph_carpet90s_4"),      # the same premiere, wider
    S("q_paris"), S("s_harness"),
]
TEX_BEFORE = [
    S("ph_portrait94_2"), S("ph_carpet90s_1"), S("ph_friends_2"),
    S("q_mat"), S("mv_catcow"), S("mv_hipopener"), S("s_gloves"),
    # q_spinbike WAS here and is gone. It is not a spin bike: it is a ROAD
    # BIKE - drop handlebars, a chain and two spoked road wheels - standing in
    # an empty white void. This is a REGRESSION, not a new fault; the project
    # history already contains "'Spinning' a road bike", and it came back
    # because the only thing anyone checked was the filename. It reached the
    # V7 cut under a quote card. The two spin bikes either side of it here,
    # s_spin and q_spinbike2, are both real studio spin bikes with the
    # flywheel and the upright bars, so nothing is lost by deleting the entry
    # rather than repointing it at a picture that would then play twice under
    # two names. Read on qc/groups/QSTILLS.jpg.
    S("s_spin"), S("q_spinbike2"), S("q_sunrise"),
]
TEX_INJURY = [
    S("q_slantboard"), S("s_mat_am"), S("mv_elliptical"),
]
TEX_METHOD = [
    S("ph_pressportrait_1"),
    S("mv_bandedrow"), S("mv_lateralraise"),
    S("mv_glutebridge"), S("mv_quadruped"), S("mv_slantsquat"),
    S("mv_reverselunge"),
]
TEX_NOW = [
    S("ph_pressportrait_2"), S("ph_portrait94_4"),
    S("mv_kneelingrow"), S("mv_intervals"), S("q_gymfloor"),
]
# W6 gets its OWN pool, not a share of W5's. They are both tagged "now" and
# a single cursor spent the whole texture on W5 - the first dry run gave W6
# two stills and twenty-two talking heads for the one argument in the film
# that is purely about a NUMBER. A texture is spent in order, so the second
# block of a two-block section always starves; splitting is the only fix that
# is not "hope the first block is short".
TEX_DURATION = [
    S("ph_carpet90s_5"), S("q_ropes"), S("s_room"), S("q_towel"),
]
TEX_EVIDENCE = [
    S("ph_carpet90s_2"), S("ph_portrait94_6"),
    S("s_water"), S("q_market"),
]
# The diet is the one section with enough illustrative material to run at
# every=1. Everything here is food, a kitchen or her; nothing here is cued -
# the cued food stills (f_juice, f_lemonwater, f_mexican and the rest) are
# absent on purpose, because a picture that plays on the words that name it
# must not also play somewhere arbitrary.
TEX_DIET = [
    S("ph_friends_1"), S("ph_portrait94_5"), S("ph_carpet90s_3"),
    S("f_citrus"), S("f_water2"), S("f_greentea"), S("f_tea"),
    S("f_eggs2"), S("f_oats"), S("f_berries"), S("f_berries2"),
    S("f_bananas"), S("f_apples"), S("f_kiwi"), S("f_melon"),
    S("f_stonefruit"),
    S("f_greens"), S("f_broccoli"), S("f_tomatoes"), S("f_peppers"),
    S("f_asparagus"),
    S("f_sweetpot"),
    S("f_turkey"), S("f_fish"), S("f_prawns"), S("f_steak"),
    S("f_quinoa"), S("f_rice"), S("f_lentils"), S("f_bread"), S("f_soup"),
    S("f_oliveoil"), S("f_olives"), S("f_nuts"), S("f_seeds"),
    S("f_froyo2"), S("s_froyo"), S("s_eggs"), S("s_plate"),
]
TEX_TAKEAWAY = [
    S("ph_globes_1"), S("ph_portrait94_3"),
]
# The close was fifteen shots and fourteen of them were interviews - a
# talking-head wall over the one paragraph the viewer is meant to remember.
# q_flashbulb is here on purpose: O2 opens on "the version of this story that
# usually gets told", and press flashbulbs are what that version looks like.
TEX_CLOSE = [
    S("ph_friends_3"), S("ph_carpet90s_6"), S("q_flashbulb"),
]

TEXTURES = {
    "hook": TEX_HOOK, "before": TEX_BEFORE, "injury": TEX_INJURY,
    "method": TEX_METHOD, "now": TEX_NOW, "duration": TEX_DURATION,
    "evidence": TEX_EVIDENCE,
    "diet": TEX_DIET, "takeaway": TEX_TAKEAWAY, "close": TEX_CLOSE,
}
for _k in TEXTURES:
    TEXTURES[_k] = _drop_dark(TEXTURES[_k])

# -- how many shots each section has to fill -------------------------------
# Measured off manifest/audio5.json and build5.carve(), not guessed.
SHOTS_NEEDED = {"hook": 23, "before": 46, "injury": 11, "method": 29,
                "now": 32, "duration": 24, "evidence": 34, "diet": 119,
                "takeaway": 26, "close": 15}

# -- the deal --------------------------------------------------------------
_HER_ALL = cap_per_source(spool(HER_SRC5))
_DEMO_ALL = cap_per_source(pool(DEMO_SRC5), 24)
_TRAIN_ALL = cap_per_source(pool(HER_TRAIN5), 4)

_HER = deal(_HER_ALL, SHOTS_NEEDED)

# Demonstrators go where a body performing a movement is the right picture:
# the volume she used to do, the method, the week as it is now, and the trial
# (seventy-two women aged forty to sixty, four sessions a week - anonymous
# demonstrators are literally what that sentence describes). NOT the diet, not
# the hook, not the close.
# Weighted towards the chapters where a body performing a movement IS the
# subject, not by block length. W7 describes seventy-two women aged forty to
# sixty doing four sessions a week; anonymous demonstrators are literally what
# that sentence is about, and it was running on red-carpet interviews.
_DEMO = deal(_DEMO_ALL, {"before": 30, "injury": 11, "method": 40,
                         "now": 40, "duration": 25, "evidence": 45,
                         "takeaway": 20, "close": 12})

# The one surviving window of her actually training opens the film.
_TRAIN = deal(_TRAIN_ALL, {"hook": 3, "method": 1})


def _mix(sec: str, every: int = 2):
    """clips for `sec`, interleaved by source, woven with its texture."""
    groups = [g for g in (_TRAIN.get(sec, []), _DEMO.get(sec, []),
                          _HER.get(sec, [])) if g]
    return weave(interleave(groups), TEXTURES[sec], every=every)


POOLS = {
    # The hook opens on the one window of her training that survives, then
    # runs on her and on the harness/Paris/film-set stills the injury story
    # needs. face_first is NOT used: it sorts on face SIZE and opened the V5
    # cut on a grimace with a joke subtitle burned in. The first shot is a cue.
    "hook":     _mix("hook", every=3),
    "before":   _mix("before", every=2),
    "injury":   _mix("injury", every=3),
    "method":   _mix("method", every=2),
    "now":      _mix("now", every=2),
    "duration": _mix("duration", every=2),
    "evidence": _mix("evidence", every=2),
    # The diet is the section with the most illustrative material and the
    # least reason to watch somebody talk: every=1 alternates food and her.
    "diet":     _mix("diet", every=1),
    "takeaway": _mix("takeaway", every=2),
    "close":    _mix("close", every=2),
}

# block id -> pool name. Every block in script.md is here; build5 raises if a
# block is missing rather than falling through to a default, because a default
# is how a block ends up drawing on a pool that is about something else.
SECTION_POOL = {
    # Derived from the `section=` tag on each vo block in script.md;
    # do not hand-edit. The script is the authority, so adding a block
    # can no longer leave it silently poolless.
    'I1': 'hook',
    'H1': 'hook',
    'W1': 'before',
    'W2': 'before',
    'W3': 'before',
    'W4': 'before',
    'W5': 'before',
    'W6': 'injury',
    'W7': 'injury',
    'W8': 'now',
    'W9': 'now',
    'W10': 'now',
    'W11': 'now',
    'W11b': 'now',
    'W12': 'method',
    'W13': 'method',
    'W14': 'method',
    'W15': 'method',
    'W16': 'duration',
    'W17': 'duration',
    'W18': 'evidence',
    'W19': 'evidence',
    'W19b': 'evidence',
    'W20': 'evidence',
    'W20b': 'now',
    'W21': 'now',
    'W22': 'diet',
    'W23': 'diet',
    'W24': 'diet',
    'W25': 'diet',
    'W26': 'diet',
    'W27': 'diet',
    'W28': 'diet',
    'W29': 'takeaway',
    'W30': 'close',
    'W31': 'close',
    'W32': 'close',
    'O1': 'close',
}


def _audit_pools() -> None:
    """Fail at IMPORT if the map has a defect a build would only reveal at
    minute twenty."""
    seen: dict = {}
    for sec, tex in TEXTURES.items():
        for r in tex:
            if r[0] in seen:
                raise SystemExit(
                    f"reels5: {r[0]} is texture in both {seen[r[0]]} and "
                    f"{sec}. Two cursors will play the same picture twice.")
            seen[r[0]] = sec
    # Cued pictures AND bite pictures. script5.BITE_PICTURE was invisible to
    # this check, which is how still:q_bands ended up as both the W4 cue and
    # the T4 bite picture and played twice 55 seconds apart. Neither is a pool
    # draw, so neither is refusable at build time; the only place to catch a
    # collision is here, before the build starts.
    pinned = set()
    try:
        import cues
        pinned |= {src for _, _, src, _ in cues.CUES}
    except Exception:
        pass
    try:
        import script5
        pinned |= {v[0] for v in script5.BITE_PICTURE.values()}
    except Exception:
        pass
    # A STILL is one picture, so pinning it twice plays it twice. A VIDEO
    # source is many pictures, so two pins on it are only a repeat if they are
    # the same window - fnTFycw2q1w is legitimately pinned at 19.0 (the yoga
    # class, under Ingber's name) and at 11.0 (a stretch, under "flexibility").
    from collections import Counter as _Ct
    pins = []
    try:
        import cues as _c
        pins += [(s, t) for _, _, s, t in _c.CUES]
    except Exception:
        pass
    try:
        import script5 as _s
        pins += list(_s.BITE_PICTURE.values())
    except Exception:
        pass
    keys = [p[0] if p[0].startswith(("still:", "split:")) else f"{p[0]}@{p[1]:.2f}"
            for p in pins]
    dupes = sorted(k for k, n in _Ct(keys).items() if n > 1)
    if dupes:
        raise SystemExit(
            f"reels5: {dupes} are pinned more than once (cues.py and/or "
            f"script5.BITE_PICTURE). A pinned picture is a statement and may "
            f"be made once; neither a cue nor a bite picture is refusable at "
            f"build time, so Reels.TAKEN cannot catch this.")
    both = sorted(pinned & set(seen))
    if both:
        raise SystemExit(
            f"reels5: {both} are cued AND woven as texture. A cued picture "
            f"plays on the words that name it; the same picture as texture "
            f"plays it a second time somewhere arbitrary.")
    import os
    dirs = ("stills_move", "stills_place", "stills_food", "stills")
    photo_names = set()
    if _PHOTOS_MANIFEST.exists():
        photo_names = set(json.loads(
            _PHOTOS_MANIFEST.read_text(encoding="utf-8")).get("names", {}))
    missing = []
    for name, sec in seen.items():
        stem = name[len("still:"):]
        if stem in photo_names:
            continue
        if not any(os.path.exists(ROOT / d / f"{stem}.jpg") for d in dirs):
            missing.append(f"{sec}:{stem}")
    if missing:
        raise SystemExit(f"reels5: textures name stills that do not exist: "
                         f"{missing}")


_audit_pools()


if __name__ == "__main__":
    print("%-10s %6s %6s %7s  %s" % ("section", "have", "need", "stills", "headroom"))
    for s, p in POOLS.items():
        n = SHOTS_NEEDED.get(s, 0)
        st = sum(1 for r in p if r[0].startswith(("still:", "split:")))
        print("  %-10s %5d %6d %7d  %.1fx" % (s, len(p), n, st, len(p) / max(1, n)))
    allw = [w for p in POOLS.values() for w in p
            if not w[0].startswith(("still:", "split:"))]
    print(f"\nclip windows {len(allw)}, distinct {len(set(allw))}  (must be equal)")
    photos = {w[0] for p in POOLS.values() for w in p
              if w[0].startswith("still:ph_")}
    print(f"photographs in a pool: {len(photos)} of {len(ALL_PHOTOS)}")
    from collections import Counter
    c = Counter(w[0] for w in allw)
    print(f"sources {len(c)}, heaviest {c.most_common(3)}")
    print(f"banned sources: {len(BANNED)}")
