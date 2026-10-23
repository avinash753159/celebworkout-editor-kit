"""Find every moment she talks about her health, workout or diet, in her own words.

The brief: "the interviews should be straight from the horse's mouth type thing
- make sure you include as many as possible". The previous cut had five such
moments in fifteen minutes and the rest was a narrator reading magazine
quotations aloud. That is the flow problem.

This reads `asr/` - every source transcribed by `src_transcribe.py` - and
returns ranked candidate BITES: contiguous runs of speech that are (a) on
topic, (b) in the first person, and (c) spoken while her face is on screen.

None of the three tests is sufficient alone, and that is the point:

- Topic alone returns the interviewer asking "so what IS your workout?"
- First person alone returns her talking about a film role.
- Identity alone returns every second she is on camera, including the ones
  where somebody else is speaking over her reaction shot.

The output is a SHORTLIST, not a cut. Every surviving window still has to be
listened to and trimmed by hand, because ASR gives no speaker turns and cannot
tell a complete thought from half of one. What this removes is the 16 hours of
listening needed to find the candidates in the first place.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASR = ROOT / "asr"

# Topic vocabulary. Weighted, because "Pvolve" is decisive and "body" is not.
TOPIC = {
    3.0: ["pvolve", "yogalosophy", "intermittent fasting", "collagen", "pilates",
          "kinesio", "physical therapist", "herniated", "spin class", "crossfit"],
    2.0: ["workout", "work out", "working out", "exercise", "training", "trainer",
          "diet", "nutrition", "protein", "cardio", "yoga", "boxing", "weights",
          "lifting", "squat", "treadmill", "elliptical", "gym", "fasting",
          "smoothie", "juice", "meditation", "sleep", "injury", "back injury",
          "resistance", "muscle", "metabolism", "stretch", "core"],
    1.0: ["body", "health", "healthy", "eat", "eating", "food", "meal", "breakfast",
          "lunch", "dinner", "calories", "sugar", "carbs", "water", "energy",
          "strong", "strength", "routine", "discipline", "wellness", "skin",
          "aging", "forties", "fifties", "weight"],
}

# First person, present tense - her describing her own practice.
SELF = re.compile(r"\b(i|i'm|i've|i'll|my|me|myself|we)\b", re.I)

# An interviewer's question. Second person plus a question mark is the giveaway.
ASKING = re.compile(r"\byou\b.*\?|^\s*(so|and|but)?\s*(what|how|do|does|did|are|is|can|would|when|why)\b.*\?", re.I)

# SOMEBODY ELSE TALKING OVER HER FOOTAGE.
#
# This is the filter the first version lacked, and it let through most of the
# shortlist: compilation channels narrate over b-roll of her, so her face sits
# on screen at high confidence while a voiceover artist speaks. "I tried
# Jennifer Aniston's 15-minute workout for 30 days" scored 7.0 on topic and
# 0.769 on identity, and is a stranger in their own kitchen.
#
# The tell is grammatical and close to perfectly reliable: she does not refer
# to herself in the third person, and she does not report her own quotes. A run
# carrying her NAME, or a reporting verb, is somebody describing her.
THIRD_PERSON = re.compile(
    r"\b(jennifer|aniston|jen's|the actress|the star|the friends star)\b", re.I)
REPORTING = re.compile(
    r"\b(opened up about|revealed|reveals|told the outlet|told the magazine|"
    r"according to|shared her|the star said|she said|she added|she credited|"
    r"her secrets|keep watching|subscribe|in this video|we will be revealing|"
    r"let's start with|stay tuned|welcome back)\b", re.I)

FIRST_RE = re.compile(r"\b(i|i'm|i've|i'll|my|me|myself)\b", re.I)
THIRD_RE = re.compile(r"\b(she|her|hers)\b", re.I)

# A WHOLE SOURCE that is somebody talking ABOUT her.
#
# The per-run filters above cannot catch a first-person REVIEW: "I tried
# Jennifer Aniston's 15-minute workout for 30 days" is first-person, on topic,
# and plays over her footage, so five of its runs reached the shortlist. But
# the giveaway is in the opening seconds of the source, not in the run - so
# classify the SOURCE once and drop all of it.
#
# Judged on the first 60 seconds, because a compilation announces itself
# immediately and an interview never does.
COMMENTARY = re.compile(
    r"\b(i tried|we tried|for 30 days|30 day (challenge|experiment)|"
    r"in this video|make sure to subscribe|hit that like|top \d+ |"
    r"here'?s what (happened|we|i)|we will be revealing|keep watching till|"
    r"let's dive in|welcome back to (the )?channel|"
    r"(her|the star'?s) (secrets|diet plan|workout plan) revealed)\b", re.I)


def commentary_sources() -> set[str]:
    """Sources whose opening minute is a presenter talking about her."""
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

MIN_SEC, MAX_SEC, GAP = 3.0, 26.0, 1.4
MIN_IDENTITY = 0.35


def topic_score(t: str) -> float:
    low = t.lower()
    return sum(w for w, keys in TOPIC.items() for k in keys if k in low)


def _identity_index() -> dict:
    raw = json.loads((ROOT / "manifest" / "identity.json").read_text(encoding="utf-8"))
    idx: dict[str, list] = {}
    for key, score in raw.items():
        src, _, t = key.rpartition("@")
        try:
            idx.setdefault(src, []).append((float(t), float(score)))
        except ValueError:
            continue
    for v in idx.values():
        v.sort()
    return idx


def identity_over(idx: dict, src: str, t0: float, t1: float) -> tuple[float, int]:
    """(best similarity, samples) inside the window. Absent data returns (-1, 0)
    so 'unmeasured' can never be mistaken for 'verified'."""
    pts = [s for t, s in idx.get(src, []) if t0 - 1.5 <= t <= t1 + 1.5]
    return (max(pts), len(pts)) if pts else (-1.0, 0)


def build() -> list[dict]:
    idx = _identity_index()
    deny = commentary_sources()
    out = []

    for f in sorted(ASR.glob("*.json")):
        src = f.stem
        if src in deny:                      # a presenter's whole video
            continue
        try:
            segs = json.loads(f.read_text(encoding="utf-8")).get("segments", [])
        except Exception:
            continue

        # group into runs of adjacent speech, then keep the on-topic ones
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
            if topic < 2.0:
                continue
            if not SELF.search(text):
                continue
            if ASKING.match(text.strip()):
                continue
            # somebody narrating ABOUT her, over footage OF her
            if THIRD_PERSON.search(text) or REPORTING.search(text):
                continue
            # first person must actually DOMINATE, not merely appear once - a
            # narrator saying "I tried her routine" has one "I" and is not her
            first = len(FIRST_RE.findall(text))
            third = len(THIRD_RE.findall(text))
            if first < 2 or first <= third:
                continue

            ident, n = identity_over(idx, src, t0, t1)
            out.append(dict(src=src, t0=round(t0, 2), t1=round(t1, 2),
                            dur=round(dur, 2), topic=round(topic, 1),
                            identity=round(ident, 3), id_samples=n, text=text))

    out.sort(key=lambda r: (-r["topic"], -r["identity"]))
    return out


def main() -> None:
    rows = build()
    verified = [r for r in rows if r["identity"] >= MIN_IDENTITY]
    unmeasured = [r for r in rows if r["identity"] < 0]

    (ROOT / "manifest" / "bite_candidates.json").write_text(
        json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")

    report = [
        "# Candidate bites - her own voice on health, workout and diet",
        "",
        f"{len(rows)} candidates from {len(list(ASR.glob('*.json')))} transcribed sources.",
        f"{len(verified)} have her face verified on screen (>= {MIN_IDENTITY}).",
        f"{len(unmeasured)} have NO identity data for that window - unmeasured, not clean.",
        "",
        "Ranked by topic weight, then identity. Every one still needs listening to:",
        "ASR carries no speaker turns, so a run can start mid-answer or include",
        "an interviewer's words.",
        "",
    ]
    for r in verified[:120]:
        report.append(f"## {r['src']} @ {r['t0']:.1f}-{r['t1']:.1f} "
                      f"({r['dur']:.1f}s, topic {r['topic']}, id {r['identity']})")
        report.append(f"> {r['text']}")
        report.append("")
    (ROOT / "qc" / "BITE_CANDIDATES.md").write_text("\n".join(report), encoding="utf-8")

    print(f"{len(commentary_sources())} sources dropped as commentary")
    print(f"{len(rows)} candidates, {len(verified)} identity-verified, "
          f"{len(unmeasured)} unmeasured")
    src = {}
    for r in verified:
        src[r["src"]] = src.get(r["src"], 0) + 1
    print(f"verified candidates span {len(src)} distinct sources")
    print(f"total verified runtime: {sum(r['dur'] for r in verified)/60:.1f} min")


if __name__ == "__main__":
    main()
