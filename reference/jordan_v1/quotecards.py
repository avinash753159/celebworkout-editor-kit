"""Which quote goes on which block, and what it is credited to.

WHY THIS FILE EXISTS
--------------------
`build5.py` used to import a hardcoded `QUOTES` dict out of `script4.py`: three
entries, keyed W3/W4/O1, with the literal string 'Jennifer Aniston to InStyle'
baked into all three credits. One of those three is not an InStyle quote at all
- "the longest workout I've actually stayed with" was said to Good Morning
America - so the film credited the wrong outlet on screen. There was no way to
express the print/on-camera credit rule either, because the build had no idea
which quotes were which.

Section 1 produces `quotes.json`: 25 verified quotes, each with `kind`
(on_camera / print / attributed), `speaker`, `outlet`, `source_url` and a
`speaker_verified` note. That ledger is the source of truth now. Nothing in the
picture layer invents a credit.

THE BLOCK MAPPING IS NOT AUTOMATIC, AND CANNOT BE
-------------------------------------------------
`quotes.json` carries `used_in_block`, but those keys (T1..T5, W1..W6, D1..D6,
O1..O2) belong to `script.md`, section 1's NEWER script. The film that exists
was voiced from `script4.BLOCKS`, which has a different shape: seven bites
T1..T7, five life blocks L1..L5, W1..W5, D1..D4, O1..O2 and no W6/D5/D6 at all.
Reading `used_in_block` straight would put the fasting quote over the Friends
paragraph. So the mapping below is by NARRATION CONTENT, block by block, and
each row says which words it sits under.

RULES THIS FILE ENFORCES
------------------------
* Rule 5 - print quotes credit the publication; on-camera quotes do not need
  it. Every on-camera quote in the ledger is already in the film as SYNC SOUND
  (a `BITE`), her own voice over her own face, so none of them is carded at
  all: a card would be a subtitle of a line the viewer can hear.
* Rule 2 - a card must be readable for its whole life on screen. `hold_seconds`
  is the floor build5 lays the span out against, and any quote that could not
  be read inside its block was SHORTENED here, with the cut marked by an
  ellipsis and the full text left untouched in quotes.json.
* An abbreviated card is never a PREFIX of the quote it came from. Truncating
  the tail is exactly the defect this section was opened for. `slate()`
  asserts it on every row.
* A card is never a SILENT edit of a quotation. Every stretch of words between
  ellipses must appear VERBATIM in the ledger, and the stretches must appear in
  the ledger in the same order they appear on the card. `slate()` asserts that
  too - see `_verbatim`. It exists because D3 read "... or oatmeal with an egg
  white whipped in at the end" where Elle printed "... or I'll do oatmeal with
  an egg white whipped in at the end": two words dropped INSIDE a segment, with
  no ellipsis marking the cut, on a card whose every other elision was marked.
  Nothing but a reader comparing the card to the ledger word by word would have
  caught it, and now nothing has to.

  This is the check that replaced a weaker claim. The docstring used to say
  "every shortening below cuts from the middle and keeps the ending", and that
  stopped being true when O2 was cut down: O2 drops the ledger's whole closing
  sentence, because the outro has no card-safe run long enough to hold it. The
  invariant that actually holds, and is enforced, is the two above - verbatim
  segments, in order, never a bare prefix. Where a shortening does NOT keep the
  ledger's ending, its own row says so (O2 is the only one).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "quotes.json"

# -- reading speed -----------------------------------------------------------
# 2.6 words/second is a comfortable rate for text a viewer reads while also
# listening to narration - slower than the ~3 w/s subtitle standard, because
# the words on the card are NOT the words in the ear. LEAD is the beat it takes
# to notice a card has arrived and move the eye to it.
WORDS_PER_SEC = 2.6
LEAD = 1.4


def hold_seconds(text: str) -> float:
    """The minimum time this card must stay up to be readable."""
    return len(text.split()) / WORDS_PER_SEC + LEAD


# -- outlet names, as they are set on the card -------------------------------
# Explicit, because the ledger's `outlet` field is prose ("ABC News, reporting
# from a Self magazine event") and guessing at it with a regex is how a wrong
# credit gets on screen in the first place.
OUTLET = {
    "InStyle": "InStyle",
    "Elle": "Elle",
    "Radio Times": "Radio Times",
    "Well + Good": "Well+Good",
    "People": "People",
    "TODAY": "TODAY",
    "HELLO!": "HELLO!",
    "Athletech News": "Athletech News",
    "ABC News, reporting from a Self magazine event": "ABC News",
    "Good Morning America (goodmorningamerica.com)": "Good Morning America",
    "Good Morning America / ABC News": "Good Morning America",
    "Pvolve press release (PR Newswire)": "Pvolve, via PR Newswire",
    "Vital Proteins press release (PR Newswire)": "Vital Proteins, via PR Newswire",
    "Mondays with Marlo (marlothomas)": "Mondays with Marlo",
    "The Drew Barrymore Show": "The Drew Barrymore Show",
    "Pvolve (brand advertisement)": "Pvolve",
    "adamtanswell (The Morning Show junket, joint interview with Reese Witherspoon)":
        "Adam Tanswell interview",
}

# Who is speaking, when it is not her. A card that quotes her trainer must say
# so on its face, or the viewer reads the words as Aniston's.
SPEAKER = {
    "Mandy Ingber, yoga instructor": "Mandy Ingber, her yoga instructor",
    "Dani Coleman, Pvolve VP of Training and Head Trainer": "Dani Coleman, her trainer",
    "Jennifer Aniston": "Jennifer Aniston",
}

# -- the slate ---------------------------------------------------------------
# build block id -> (quote id, card text or None for the full quote, why here)
# One card per block. `None` means the ledger text is short enough to run whole.
SLATE: dict[str, tuple[str, "str | None", str]] = {

    # REMAPPED FOR script.md. Every key below was already a real block id, so
    # nothing crashed - the cards simply sat on the wrong sentences. Under the
    # old (script4) blocks W4 was Pvolve and D4 was the cheat day; under
    # script.md W4 is the METHOD and D4 is the PREP SYSTEM, so
    # coleman_gold_standard and abc_cheat_day were both one block adrift, and
    # D2 - fourteen seconds about a press junket - carried the shake recipe.
    # Six quotes filed "no block" in NOT_CARDED now have one, because the new
    # script covers material the old one did not (the burnout, the
    # fifteen-minute classes, the prep system, TODAY).
    #
    # SECTION 5 OWNS THE WORDING AND THE SHORTENINGS. What section 4 changed
    # is only WHICH BLOCK each quote belongs to, plus the D4 shortening, which
    # did not exist before because D4 carried a different quote.

    "W1": ("ingber_format",
           "What I do with Jennifer Aniston ... 20 to 30 minutes of cardio "
           "activity, and then we'll practice yoga.",
           "W1 narrates the old volume by name - Ingber, twenty to thirty "
           "minutes of cardio, then a yoga practice - and this is Ingber "
           "describing that exact format, from the person who ran the "
           "sessions. Shortened: W1's card-safe run is broken by the "
           "fnTFycw2q1w cue, which is a yoga class full of people who are not "
           "her. The cut is 'is that I will incorporate', which carries no "
           "information the ellipsis does not."),

    "W2": ("instyle_burnt_out", None,
           "W2 IS this quote in the narrator's words - 'when you are in a "
           "mindset of, I need to do forty-five minutes of cardio or I will "
           "not get a good workout, it is daunting ... she burnt out and "
           "broke her body'. The card is the receipt for the paraphrase. It "
           "had no block at all under script4, which never covered the "
           "burnout."),

    "W5": ("coleman_gold_standard",
           "She is the gold standard ... three times a week, she shows up and "
           "hits it.",
           "W5 says 'Coleman said that for nearly five years, three times a "
           "week, Aniston shows up and hits it, and called her the gold "
           "standard'. This is the sentence being quoted. It was on W4, which "
           "under script.md is the Pvolve MECHANICS block and does not "
           "mention Coleman. Shortened because W5's people-free run is split "
           "by the cBZC-8S9b8g cue; 'for nearly five years' is the part cut, "
           "and the narration says five years out loud in the same sentence."),

    "W6": ("pvolve_pr_consistency", None,
           "W6's whole argument is duration - six classes, all fifteen "
           "minutes or less - and it names this press release outright: 'the "
           "line attributed to her is that she has learned consistency does "
           "not have to mean long workouts'. It was on O1, which makes the "
           "same argument second-hand; W6 is where the quote is actually "
           "cited."),

    "D1": ("radiotimes_fasting", None,
           "D1 quotes this interview directly - 'In a Radio Times interview "
           "she said: I do intermittent fasting, so there is no food in the "
           "morning'. The card is the receipt."),

    "D3": ("elle_breakfast",
           "When I wake up, I have warm lemon water and then I have a shake or "
           "avocado and eggs ... or I'll do oatmeal with an egg white whipped "
           "in at the end.",
           "D3 reads this quote out in paraphrase - warm lemon water, then a "
           "shake, or avocado and eggs, or oatmeal with an egg white whipped "
           "in. The coconut-oil and puffed-millet sentences are cut from the "
           "middle - 56 words will not read in a 50s block - and the oatmeal "
           "ending is kept, so this is not a prefix."),

    "D4": ("elle_lunch_prep",
           "Some form of vegetables or salad with protein - pretty basic. I "
           "always have cut raw vegetables in a Tupperware container ... a big "
           "head of butter lettuce. I also include protein, such as pulled "
           "chicken.",
           "D4 IS the prep system: the Tupperware, the hard-boiled eggs, the "
           "butter lettuce, the pulled chicken. Under script4 there was no "
           "block about it and this quote was filed 'no room'. Shortened by "
           "one sentence from the middle - the hard-boiled eggs, which the "
           "narration says out loud anyway - and the ending is kept, so this "
           "is not a prefix. The full 48 words need 19.9s and the block is "
           "40s."),

    "D5": ("abc_cheat_day", None,
           "D5 is the cheat-day correction and it quotes ABC News almost word "
           "for word: 'cheat days for her are usually Mexican food, maybe "
           "Italian pasta, and that you always have to do it in moderation.' "
           "The ellipses inside this one are the source's, not ours. It was "
           "on D4, which under script.md is lunch and dinner."),

    "D6": ("today_basics", None,
           "D6 lists exactly this - exercise, good nutrition, a good amount of "
           "sleep, meditation, looking after her mental health, and enjoying "
           "her life, and that she gives herself days where she can have "
           "whatever she wants. D6 did not exist under script4, which is why "
           "this quote was filed 'no block'."),

    "O2": ("people_thirty_minutes",
           "I can do a 30-minute Pvolve workout ... without literally breaking "
           "my body.",
           "O2 closes on this interview: 'she can do a thirty-minute session, "
           "finish it drenched, and get results out of it without breaking "
           "her body'. THIS IS THE ONE CARD THAT DOES NOT KEEP THE LEDGER'S "
           "ENDING, and it is deliberate: the close is a 35s block and the "
           "full 40 words need 17s. Two cuts - 'and be drenched and have such "
           "incredible results' from the middle, and the closing sentence off "
           "the tail. Cutting the tail alone WOULD be the prefix defect; "
           "cutting the middle as well is what keeps it honest - the ledger "
           "continues 'and be drenched' exactly where the card has its "
           "ellipsis, so a reader can see a cut was made."),
}

# -- where a card must STOP -------------------------------------------------
# A card is the receipt for what the narration is claiming while it is up. When
# the narration moves on to something else, the receipt stops being one, and if
# the picture moves with the narration the card is left sitting over a
# contradiction.
#
# block id -> {shot tag: why the card may not touch it}. build5 treats these
# exactly like an unvetted cue - the run of shots the card may occupy is cut
# here, and the span slides to a run that fits.
#
# EMPTY, and that is a statement rather than an omission. The only entry this
# table has ever held was D2/still:f_burger - the shake card running on to a
# grilled chicken burger - and under script.md D2 carries no card at all while
# f_burger is cued in D5, whose card is ABOUT burgers. Every card is now on
# the block that quotes it, and the cued stills inside those blocks are
# congruent with the quote by construction (D3's cues are all breakfast, D4's
# all prep, D5's all cheat food). This has to be RE-DERIVED BY EYE from
# qc/CARD_OVER_*.jpg after the first build of the new film; an empty table is
# the honest starting point, not a finding.
SPAN_DENY: dict[str, dict] = {}

# Quotes deliberately NOT carded, and why. Kept here so the next pass does not
# have to re-derive it, and so the count always adds up to the ledger's 25.
NOT_CARDED: dict[str, str] = {
    "jen_mix_it_up": "on_camera - plays as sync sound, bite T1",
    "jen_past_forty": "on_camera - plays as sync sound, bite T2",
    "jen_injury": "on_camera - plays as sync sound, bite T3",
    "jen_twenty_minutes": "on_camera - plays as sync sound, bite T4",
    "jen_juice_first": "on_camera - plays as sync sound, bite T5",
    "instyle_barbie":
        "no room. Its block is W2 - the Barbie doll wrapped in kinesio tape "
        "is W2's own image - and W2 carries instyle_burnt_out, from the same "
        "interview, which W2 paraphrases more closely. W3 next door is the "
        "injury CONSTRAINT (what running, rope and spinning do to a lumbar "
        "spine), thirty seconds long, and mentions no interview at all.",
    "instyle_crossfit_boxing":
        "no room. Third InStyle quote competing for W2, which can hold one "
        "card and quotes the burnout sentence in its own narration.",
    "wellgood_shake":
        "no room. The shake is described in D3, and D3 carries elle_breakfast "
        "- the quote D3 paraphrases first and at greater length. It was on D2 "
        "under script4; script.md's D2 is fourteen seconds about a press "
        "junket and cannot hold a card at all.",
    "people_eighty_twenty":
        "no room. Same block as abc_cheat_day (D5) and the same territory; D5 "
        "quotes the ABC wording almost verbatim in the narration.",
    "people_comfort_food": "no room. Third quote competing for D5.",
    "today_bones":
        "no room. Same block as today_basics (D6) and the same interview; D6 "
        "reads the basics list out in full and only summarises the bones "
        "line.",
    "vital_proteins_collagen":
        "no room, and the weakest of the 25 to put on screen as her view - a "
        "product endorsement in a press release. D6 says so out loud ('file "
        "that one under paid position, not finding') and carries today_basics "
        "instead.",
    "coleman_spine":
        "no room. Same block as coleman_gold_standard (W5) and the same "
        "interview subject; W5 can hold one card.",
    "coleman_heavy_weights": "no room. Third Coleman quote, same block.",
    "gma_boxing_longest":
        "no room. Its block is W1 and W1 carries ingber_format, which "
        "describes the same era more completely and comes from the person who "
        "ran the sessions. This is also the quote that produced the broken "
        "\"It's the longest\" frame at 05:19 in V6.",
}


def _entries() -> dict:
    return {e["id"]: e for e in json.loads(LEDGER.read_text(encoding="utf-8"))}


def credit_for(e: dict) -> str:
    """The credit line, from the ledger. Never guessed.

    print      -> speaker to outlet          ("Jennifer Aniston to InStyle")
    attributed -> speaker, role, to outlet   ("Dani Coleman, her trainer, to HELLO!")
    on_camera  -> "" (rule 5: not needed - and nothing on-camera is carded)
    """
    if e["kind"] == "on_camera":
        return ""
    who = SPEAKER.get(e["speaker"], e["speaker"])
    outlet = OUTLET.get(e["outlet"])
    if outlet is None:
        raise SystemExit(
            f"quotecards: no card spelling for outlet {e['outlet']!r} "
            f"(quote {e['id']}). Add it to OUTLET rather than guessing.")
    joiner = ", to " if "," in who else " to "
    return f"{who}{joiner}{outlet}"


def _fold(s: str) -> str:
    """Compare like a reader: curly punctuation and runs of space folded away,
    letters and words otherwise untouched. NOT case-folded and NOT
    punctuation-stripped - a card that turns a comma into a full stop, or
    lower-cases a name, has still altered the quotation."""
    s = (s.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-"))
    return re.sub(r"\s+", " ", s).strip()


def _segments(text: str) -> list:
    """The stretches of quotation between our ellipses."""
    return [p.strip() for p in re.split(r"\s*(?:\.\.\.|…)\s*", text)
            if p.strip()]


def _verbatim(bid: str, qid: str, card: str, full: str) -> None:
    """Every segment of the card is IN the ledger text, word for word, and the
    segments occur in the ledger in the order the card puts them.

    The prefix rule catches a card that stops early. This catches the other
    half: a card that quietly rewrites the words it does keep, or that
    re-orders them. D3 dropped "I'll do" from the middle of a segment and no
    check saw it, because the segment still ENDED where the ledger ends and the
    card was still not a prefix.

    D4's ellipses are the SOURCE'S own, printed by ABC News. Splitting on them
    is still correct - each piece either is or is not in the ledger, and for an
    unshortened card every piece trivially is.
    """
    hay = _fold(full)
    at = 0
    for seg in _segments(card):
        s = _fold(seg)
        i = hay.find(s, at)
        if i < 0:
            elsewhere = hay.find(s)
            why = ("it appears earlier in the quote - the card re-orders it"
                   if elsewhere >= 0 else
                   "it is not in the ledger text at all - the card ALTERS the "
                   "quotation")
            raise SystemExit(
                f"quotecards: {bid}/{qid} is not verbatim. The segment\n"
                f"    {seg!r}\n"
                f"  is not a substring of quotes.json at or after character "
                f"{at}: {why}. Mark every cut with an ellipsis and copy the "
                f"words that remain out of the ledger unchanged.")
        at = i + len(s)


def slate() -> dict:
    """The card table. Empty when the film has no quote cards.

    SLATE still names the twenty-five quotes of the OLD narration-led script.
    Under the current brief none of them are carded - quotations are delivered
    by playing the real clip - so resolving that table against the new
    `quotes.json` would fail on ids that legitimately no longer exist.
    """
    import os
    if os.environ.get("NO_QUOTE_CARDS", "1") != "0":
        return {}
    
    """block id -> {text, credit, id, kind, outlet, full, shortened, hold}."""
    ents = _entries()
    out: dict = {}
    for bid, (qid, short, why) in SLATE.items():
        e = ents.get(qid)
        if e is None:
            raise SystemExit(f"quotecards: {qid} is not in quotes.json")
        text = short or e["text"]
        if short and e["text"].startswith(short.rstrip(".")[:60]) and \
                e["text"].startswith(short):
            raise SystemExit(
                f"quotecards: the card text for {qid} is a strict PREFIX of the "
                f"full quote. That is the bug this section exists for.")
        _verbatim(bid, qid, text, e["text"])
        out[bid] = dict(id=qid, text=text, credit=credit_for(e),
                        kind=e["kind"], outlet=e["outlet"], full=e["text"],
                        shortened=bool(short), why=why,
                        hold=hold_seconds(text))
    return out


def check() -> None:
    """Every ledger quote is either carded or explained. No third state.

    Unless the film has no quote cards at all. Under the 25 Aug 2026 brief the
    burned-in quote bars are gone - replaced by full-frame infographics - and
    every quotation is delivered by PLAYING THE REAL CLIP instead of reprinting
    it as type. In that mode there is nothing for this guard to be right about,
    and requiring an explicit NOT_CARDED row for all forty quotes would be
    bookkeeping that protects nothing.
    """
    import os
    if os.environ.get("NO_QUOTE_CARDS", "1") != "0":
        return
    ents = _entries()
    carded = {v[0] for v in SLATE.values()}
    for qid in ents:
        if qid not in carded and qid not in NOT_CARDED:
            raise SystemExit(f"quotecards: {qid} is neither carded nor explained")
    for qid in NOT_CARDED:
        if qid not in ents:
            raise SystemExit(f"quotecards: NOT_CARDED names unknown quote {qid}")
    for bid in SPAN_DENY:
        if bid not in SLATE:
            raise SystemExit(f"quotecards: SPAN_DENY names block {bid}, which "
                             f"carries no card")
    for bid, s in slate().items():
        if s["kind"] in ("print", "attributed"):
            head = OUTLET[s["outlet"]].split(",")[0].lower()
            if head not in s["credit"].lower():
                raise SystemExit(f"quotecards: {bid} carries no outlet on the card")


if __name__ == "__main__":
    check()
    s = slate()
    print(f"{len(s)} cards, {len(NOT_CARDED)} quotes not carded, "
          f"{len(_entries())} in the ledger\n")
    for bid, v in s.items():
        print(f"{bid:<4} {v['id']:<24} {v['kind']:<10} "
              f"{len(v['text'].split()):>2}w  hold {v['hold']:5.1f}s"
              f"  {'SHORTENED' if v['shortened'] else ''}")
        print(f"     “{v['text']}”")
        print(f"     -- {v['credit']}\n")
