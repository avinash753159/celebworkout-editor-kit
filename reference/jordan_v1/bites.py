"""Find every moment Jordan - or the men who trained him - talk about the work.

Reads `asr/` and returns ranked candidate BITES: contiguous runs of speech that
are on topic, in the right grammatical person, and not a presenter talking over
archive footage.

THE STRUCTURAL DIFFERENCE FROM THE ANISTON BUILD
------------------------------------------------
On Aniston, every wanted voice was a first-person voice, so one gate served the
whole library: reject any run carrying her NAME, because nobody refers to
themselves in the third person.

That gate would destroy this film. Tim Grover's entire value is that he talks
ABOUT Michael Jordan - "I told him", "he came in at six" - and Chip Schaefer's
and the Breakfast Club's likewise. A name-rejection gate applied library-wide
would delete the second voice completely and leave only the subject, who is the
scarcer of the two.

So the gate is TIER-AWARE, and the tier comes from the fetch ledger, not from a
hand-kept list:

  subject tier - Jordan's own sources. First person must DOMINATE, and his own
                 name is disqualifying. Same logic as Aniston.
  trainer tier - Grover, Schaefer, teammates. First person AND third person must
                 BOTH appear: that is the grammar of somebody recounting what
                 they did with somebody else ("I told him", "we had him in at
                 six"). A host asking a question has the third person without
                 the first; a motivational monologue has the first without the
                 third.

WHAT NONE OF THIS PROVES
------------------------
That the person on the microphone is who we think it is. ASR carries no speaker
turns. On a podcast the host and the guest are both first-person, both on topic,
and indistinguishable in text. That is what the identity score and, decisively,
step 5 - cut the bite, re-transcribe the CUT, compare word for word - are for.
This stage produces a SHORTLIST to read, never a cut.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASR = ROOT / "asr"
MAN = ROOT / "manifest"

# --- topic vocabulary -------------------------------------------------------
# Weighted: "breakfast club" is decisive, "body" is not.
TOPIC = {
    3.0: ["breakfast club", "weight room", "attack athletics", "tim grover",
          "strength and conditioning", "jordan rules", "flu game",
          "weight training", "off-season program", "offseason program",
          "chip schaefer", "strength coach", "six a.m.", "6 a.m.",
          "six in the morning", "weight lifting", "weightlifting"],
    2.0: ["workout", "work out", "working out", "worked out", "training",
          "trained", "trainer", "conditioning", "lifting", "lift weights",
          "weights", "gym", "practice", "practising", "practicing", "diet",
          "nutrition", "protein", "steak", "stamina", "endurance", "strength",
          "muscle", "injury", "injured", "rehab", "recovery", "regimen",
          "routine", "reps", "sets", "squat", "bench press", "treadmill",
          "cardio", "stretching", "physical therapy", "fatigue", "exhausted",
          "shootaround", "drills", "conditioned"],
    1.0: ["body", "strong", "stronger", "physical", "shape", "fitness",
          "energy", "food", "meal", "breakfast", "lunch", "dinner", "eat",
          "eating", "ate", "discipline", "preparation", "prepare", "prepared",
          "work ethic", "hard work", "weight", "pounds", "sleep", "rest",
          "tired", "sweat", "effort", "competitive", "compete"],
}

# The subject, referred to in the third person.
SUBJECT_NAME = re.compile(
    r"\b(michael\s+jordan|jordan|michael|mj|his\s+airness|air\s+jordan|"
    r"the\s+goat|twenty[- ]three)\b", re.I)

# A trainer recounting: needs BOTH persons present.
FIRST_RE = re.compile(r"\b(i|i'm|i've|i'll|i'd|my|me|myself|we|our|us)\b", re.I)
THIRD_RE = re.compile(r"\b(he|him|his|she|her|they|them)\b", re.I)
SELF = re.compile(r"\b(i|i'm|i've|i'll|i'd|my|me|myself|we)\b", re.I)

# An interviewer's question.
ASKING = re.compile(
    r"\byou\b.*\?|^\s*(so|and|but|now)?\s*"
    r"(what|how|do|does|did|are|is|was|were|can|could|would|when|why|tell)\b.*\?",
    re.I)

# A presenter narrating over archive.
REPORTING = re.compile(
    r"\b(opened up about|revealed|reveals|told the outlet|told the magazine|"
    r"according to|the star said|he said|he added|sources say|reportedly|"
    r"keep watching|subscribe|in this video|we will be revealing|stay tuned|"
    r"welcome back|let's get into|number (one|two|three|four|five)|"
    r"coming up next|don't forget to|smash that|like and subscribe)\b", re.I)

# A WHOLE SOURCE that is a presentation rather than a conversation. Judged on
# the opening 60 seconds, because a compilation announces itself immediately
# and an interview never does. This matters more on Jordan than it did on
# Aniston: the archive is drowned in highlight-mix and AI-narrated channels.
COMMENTARY = re.compile(
    r"\b(i tried|we tried|for 30 days|in this video|make sure to subscribe|"
    r"hit that like|top \d+ |here'?s what (happened|we|i)|welcome back to|"
    r"let's dive in|we will be revealing|keep watching till|"
    r"in today'?s video|this is the story of|have you ever wondered|"
    r"what if i told you|ladies and gentlemen, welcome)\b", re.I)

MIN_SEC, MAX_SEC, GAP = 3.0, 26.0, 1.4
MIN_TOPIC = 2.0


def source_tiers() -> dict[str, str]:
    """subject | trainer, per source id, from the fetch ledger.

    Derived from the ledger's recorded query, never from a hand-kept list of
    ids - the same reason the block->pool map is derived from the script's own
    section tags. A source added by a later fetch gets a tier automatically;
    a hand-kept list would silently leave it untiered.
    """
    from fetch_talk import SUBJECT_QUERIES
    led = json.loads((MAN / "fetch_talk.json").read_text(encoding="utf-8"))
    return {k: ("subject" if v.get("query") in SUBJECT_QUERIES else "trainer")
            for k, v in led.items()}


def commentary_sources() -> set[str]:
    bad = set()
    for f in sorted(ASR.glob("*.json")):
        try:
            segs = json.loads(f.read_text(encoding="utf-8")).get("segments", [])
        except Exception:
            continue
        head = " ".join(s["text"] for s in segs if s["t0"] < 60.0)
        if COMMENTARY.search(head):
            bad.add(f.stem)
    return bad


def topic_score(t: str) -> float:
    low = t.lower()
    return sum(w for w, keys in TOPIC.items() for k in keys if k in low)


def passes_person(text: str, tier: str) -> bool:
    """The tier-aware grammar gate. This is the heart of the file."""
    first = len(FIRST_RE.findall(text))
    third = len(THIRD_RE.findall(text))

    if tier == "subject":
        # He is describing his own practice. His own name is disqualifying:
        # nobody refers to themselves in the third person, so a run carrying
        # it is a narrator over his footage.
        if SUBJECT_NAME.search(text):
            return False
        return first >= 2 and first > third

    # trainer: recounting what they did WITH him. Both persons required.
    # - first without third  -> a motivational monologue, not about Jordan
    # - third without first  -> a host narrating, or a question
    return first >= 1 and third >= 1


def build() -> list[dict]:
    tiers = source_tiers()
    deny = commentary_sources()
    out: list[dict] = []

    for f in sorted(ASR.glob("*.json")):
        src = f.stem
        if src in deny:
            continue
        tier = tiers.get(src, "subject")
        try:
            segs = json.loads(f.read_text(encoding="utf-8")).get("segments", [])
        except Exception:
            continue

        runs, cur = [], []
        for s in segs:
            if cur and (s["t0"] - cur[-1]["t1"] > GAP
                        or s["t1"] - cur[0]["t0"] > MAX_SEC):
                runs.append(cur)
                cur = []
            cur.append(s)
        if cur:
            runs.append(cur)

        for run in runs:
            text = " ".join(s["text"] for s in run).strip()
            t0, t1 = run[0]["t0"], run[-1]["t1"]
            dur = t1 - t0
            if not (MIN_SEC <= dur <= MAX_SEC) or len(text) < 40:
                continue
            topic = topic_score(text)
            if topic < MIN_TOPIC:
                continue
            if not SELF.search(text):
                continue
            if ASKING.match(text.strip()) or REPORTING.search(text):
                continue
            if not passes_person(text, tier):
                continue
            # A trainer talking generically about winning is not this film.
            # Require either an explicit reference to the subject or a strong
            # training topic - otherwise Grover's business-motivation hours
            # flood the shortlist.
            if tier == "trainer" and topic < 4.0 and not SUBJECT_NAME.search(text):
                continue

            out.append(dict(src=src, tier=tier, t0=round(t0, 2), t1=round(t1, 2),
                            dur=round(dur, 2), topic=round(topic, 1),
                            identity=-1.0, id_samples=0, text=text))

    out.sort(key=lambda r: (-r["topic"], -r["dur"]))
    return dedupe(out)


def _shingles(text: str) -> set[str]:
    w = re.findall(r"[a-z']+", text.lower())
    return {" ".join(w[i:i + 5]) for i in range(max(0, len(w) - 4))}


def dedupe(rows: list[dict]) -> list[dict]:
    """Collapse the same words appearing in more than one place.

    Two distinct problems, one fix:

    - The SAME interview is re-uploaded under different titles. Jordan's 1980s
      conditioning-and-nutrition piece is in this library at least twice, under
      "Michael Jordan Conditioning and Nutrition" and "Michael Jordan
      Basketball Training". Different source ids, different timecodes, the same
      sentences.
    - Adjacent runs inside ONE source overlap at their edges, because a run
      boundary falls mid-answer.

    Either way, quoting both would put the same words on screen twice. The
    survivor keeps the losers in `alts`, because a duplicate is not waste - it
    is a second camera angle on a line we already want, and step 7 can prefer
    whichever source has the better picture.
    """
    kept: list[dict] = []
    for r in rows:
        sh = _shingles(r["text"])
        if not sh:
            continue
        hit = None
        for k in kept:
            inter = len(sh & k["_sh"])
            if inter / min(len(sh), len(k["_sh"])) >= 0.5:
                hit = k
                break
        if hit is None:
            kept.append({**r, "_sh": sh, "alts": []})
        else:
            hit["alts"].append({"src": r["src"], "t0": r["t0"], "t1": r["t1"]})
    for k in kept:
        k.pop("_sh", None)
    return kept


def main() -> None:
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rows = build()
    MAN.mkdir(exist_ok=True)
    (MAN / "bite_candidates.json").write_text(
        json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")

    subj = [r for r in rows if r["tier"] == "subject"]
    trn = [r for r in rows if r["tier"] == "trainer"]

    report = ["# Candidate bites - Jordan and the men who trained him", "",
              f"{len(rows)} candidates from {len(list(ASR.glob('*.json')))} "
              f"transcribed sources.",
              f"- subject tier: {len(subj)} runs, "
              f"{sum(r['dur'] for r in subj)/60:.1f} min",
              f"- trainer tier: {len(trn)} runs, "
              f"{sum(r['dur'] for r in trn)/60:.1f} min", "",
              "NOT YET VERIFIED. Passing these gates is not the same as being",
              "on topic, being a complete thought, or being the right speaker.",
              "Every one still has to be READ, and then proved against its own",
              "audio by cut_bites.py. Report the number that survives reading.",
              ""]
    for label, group in (("SUBJECT", subj), ("TRAINER", trn)):
        report.append(f"\n---\n\n# {label} TIER\n")
        for r in group:
            report.append(f"## {r['src']} @ {r['t0']:.1f}-{r['t1']:.1f} "
                          f"({r['dur']:.1f}s, topic {r['topic']})")
            report.append(f"> {r['text']}")
            report.append("")
    (ROOT / "qc" / "BITE_CANDIDATES.md").write_text("\n".join(report),
                                                    encoding="utf-8")

    print(f"{len(deny := commentary_sources())} sources dropped as commentary")
    print(f"{len(rows)} candidates: {len(subj)} subject "
          f"({sum(r['dur'] for r in subj)/60:.1f} min), "
          f"{len(trn)} trainer ({sum(r['dur'] for r in trn)/60:.1f} min)")
    print(f"spanning {len({r['src'] for r in rows})} distinct sources")


if __name__ == "__main__":
    main()
