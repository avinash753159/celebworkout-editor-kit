"""Harvest LONG-FORM SPEECH about Michael Jordan's training, not b-roll.

Step 1 of the pipeline, and the highest-leverage one. A library harvested for
PICTURES will not carry a bite-led film: on Aniston, 194 b-roll sources yielded
4.6 minutes of her actually talking about her subject. This fetch goes looking
for people TALKING AT LENGTH and deliberately prefers a 40-minute conversation
to a 40-second soundbite.

Three guards, each earned:

- **`--no-continue`, and clear stale `.part` files.** A partial left by an
  interrupted run makes yt-dlp send a Range header, and YouTube answers a
  resumed ranged request with **403 Forbidden**. It reads exactly like a block
  and is not one. This alone caused a 31-of-34 failure rate.
- **A permissive format chain and several player clients.** The strict
  `bestvideo[ext=mp4]+bestaudio[ext=m4a]` has no fallback when a video has no
  progressive mp4.
- **Skip what is on disk by YouTube ID, not by title.** The same interview is
  re-uploaded under a dozen different names.

Two guards NEW to this subject, both from BRIEF.md §9:

- **There are two Michael Jordans.** A bare "Michael Jordan workout" returns
  Michael B. Jordan's Creed training. `WRONG_SUBJECT` kills those at the title,
  before they cost a download or 40 minutes of transcription.
- **Era drift.** The brief locks 1989-1998. Wizards-era and present-day golf
  content is off-brief and is dropped here rather than left for the picture
  stage to notice.

Nothing here judges whether it is really HIM speaking. That is `bites.py`'s job
and it needs the text to do it - a face score says who is on screen, never who
is talking.

Usage:
    python fetch_talk.py --dry          # search only, write the pool, download nothing
    python fetch_talk.py 40             # download the 40 longest survivors
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
MAN = ROOT / "manifest"
LEDGER = MAN / "fetch_talk.json"
POOL = MAN / "talk_pool.json"

# Jordan is guarded, and clips of him actually SPEAKING about training are rare
# and short. The Aniston floor of 1 minute dropped "Michael Jordan talks about
# PRACTICE (1997)" at 12 seconds and a 54-second 60 Minutes item - on this
# subject those are the scarce resource, not the filler. The ceiling is raised
# to admit a 167-minute compilation of his own finals interviews.
MAX_MIN = 175.0
MIN_MIN = 0.2

# ---------------------------------------------------------------------------
# Queries, ordered by how likely they are to return SPEECH at length.
# Every subject query is disambiguated - never a bare "Michael Jordan workout".
# ---------------------------------------------------------------------------
QUERIES: list[tuple[str, int]] = [
    # --- the subject, in his own voice ---
    ("Michael Jordan interview training regimen Chicago Bulls", 12),
    ("Michael Jordan talks about weight training Tim Grover", 12),
    ("Michael Jordan interview work ethic practice Bulls 1990s", 12),
    ("Michael Jordan Last Dance interview training preparation", 12),
    ("Michael Jordan on getting stronger Detroit Pistons Jordan Rules", 10),
    ("Michael Jordan interview conditioning offseason Bulls", 10),
    ("Michael Jordan diet nutrition interview basketball", 10),
    ("Michael Jordan flu game interview what happened", 8),
    ("Michael Jordan Ahmad Rashad full interview", 10),
    ("Michael Jordan 1996 press conference practice full", 8),
    ("Michael Jordan Oprah interview full", 6),
    ("Michael Jordan Hall of Fame speech", 4),
    ("Michael Jordan 60 Minutes interview Bulls", 6),
    ("Michael Jordan sit down interview 1992 1993", 8),
    # --- Tim Grover, the primary second voice ---
    ("Tim Grover Michael Jordan training interview", 12),
    ("Tim Grover Relentless podcast full interview", 12),
    ("Tim Grover Attack Athletics Michael Jordan", 10),
    ("Tim Grover on training Michael Jordan Kobe", 10),
    ("Tim Grover how Michael Jordan trained podcast", 10),
    ("Tim Grover Winning podcast interview", 8),
    # --- Chip Schaefer, Bulls athletic trainer ---
    ("Chip Schaefer Chicago Bulls athletic trainer interview", 10),
    ("Chip Schaefer Michael Jordan flu game truth", 8),
    ("Chip Schaefer Bulls training staff interview", 6),
    # --- the Breakfast Club ---
    ("Scottie Pippen Michael Jordan Breakfast Club workouts", 10),
    ("Ron Harper Michael Jordan Breakfast Club training", 8),
    ("Randy Brown Michael Jordan Breakfast Club 6am workouts", 8),
    ("Bulls Breakfast Club Michael Jordan weight room", 8),
    ("Michael Jordan teammates on his practice habits", 8),
]

# ---------------------------------------------------------------------------
# Title-level rejection. Cheap, and it runs before anything is downloaded.
# ---------------------------------------------------------------------------

# The OTHER Michael Jordan. The channel already has a Short on him.
WRONG_SUBJECT = re.compile(
    r"michael\s+b\.?\s+jordan|creed\b|killmonger|black\s+panther|"
    r"wakanda|adonis|sinners\b|corey\s+calliet|without\s+remorse|"
    r"fruitvale|fantastic\s+four",
    re.I,
)

# Off-brief eras. BRIEF.md locks 1989-1998.
WRONG_ERA = re.compile(
    r"\bwizards\b|\bgolf\b|hornets\s+owner|nascar|"
    r"\b(?:2018|2019|2020|2021|2022|2023|2024|2025|2026)\s+interview\b",
    re.I,
)

# Presentation-shaped uploads. bites.py has a per-source version of this that
# judges the first 60 seconds, but killing the obvious ones at the title saves
# the download AND the transcription.
PRESENTATION = re.compile(
    r"\bi\s+tried\b|\btop\s*\d+\b|\bin\s+this\s+video\b|reaction\b|"
    r"\btier\s+list\b|\branking\b|AI\s+voice|edit\b|highlight\s+mix|"
    r"\bmix\s*\d{4}\b|\bmixtape\b|\btribute\b|\bmotivation(?:al)?\s+video\b",
    re.I,
)


# Full broadcast games. These are PICTURE, not speech - a 103-minute game costs
# ~20 minutes of transcription to return commentary by Marv Albert. Game footage
# is wanted for the picture pool and is fetched separately at step 7.
FULL_GAME = re.compile(
    r"\bgame\s*[1-7]\b|conference\s+finals|nba\s+finals\s+game|full\s+game|"
    r"\bvs\.?\s+(?:the\s+)?\w+\s*\|\s*\w+\s+\d{4}|holds?\s+mj\s+to|"
    r"\bq[1-4]\b|full\s+broadcast|\d{4}\s+nba\s+(?:playoffs|regular)",
    re.I,
)

# Music-over-speech motivation edits. They DO contain real Jordan audio, but it
# is chopped, layered under a score and re-ordered - which is hallucination bait
# for ASR and unusable as a verifiable bite even when the words are real.
MOTIVATION = re.compile(
    r"motivational?\s+(?:speech|video)|\bmotivation\b|inspirational|"
    r"\bmindset\b\s*[-–|]|best\s+moments|compilation\s+of\s+the\s+best|"
    r"how\s+to\s+be\s+like|obsession\s+beats|takes?\s+everything\s+you",
    re.I,
)

# Off-topic noise that reached the pool through a shared keyword.
NOISE = re.compile(
    r"rookie\s+card|authenticat|50\s+cent|irv\s+gotti|racist|"
    r"trash\s+talk(?:ing)?\s*$|sneaker\s+review|\bunboxing\b|"
    # a commercial weight-loss programme trading on the name, and a juice-bar
    # promo that reached the pool through the word "organic"
    r"weight\s+loss\s+experience|clean\s+juice|eric\s+gordon",
    re.I,
)


def reject(title: str) -> str | None:
    """Return a reason string if this title should never be downloaded."""
    if WRONG_SUBJECT.search(title):
        return "wrong-subject"
    if WRONG_ERA.search(title):
        return "wrong-era"
    if FULL_GAME.search(title):
        return "full-game"
    if MOTIVATION.search(title):
        return "motivation-edit"
    if NOISE.search(title):
        return "noise"
    if PRESENTATION.search(title):
        return "presentation"
    return None


# Index of the first TRAINER query in QUERIES. Everything before it is a query
# aimed at the subject's own voice.
FIRST_TRAINER_Q = next(i for i, (q, _) in enumerate(QUERIES) if q.startswith("Tim Grover"))
SUBJECT_QUERIES = {q for q, _ in QUERIES[:FIRST_TRAINER_Q]}


def existing_ids() -> set[str]:
    return {p.stem for p in HD.glob("*.mp4")}


# The trainer side is budgeted in MINUTES, not in sources: Grover's material is
# 90-minute podcasts and the real cost of this step is transcription time, which
# is proportional to audio length. Two per channel, because a dozen Grover
# long-forms repeat the same anecdotes and the brief wants the selection spread
# across appearances anyway - it cuts better.
TRAINER_MIN_BUDGET = 850.0
PER_CHANNEL_CAP = 2

# Long subject sit-downs reserved before the short clips compete for the quota.
SUBJ_LONG_RESERVE = 11


def select(cands: list[dict], budget: int) -> list[dict]:
    """Choose what to download.

    Pure longest-first is wrong for THIS subject and so is pure scarcity-first.
    Jordan's own speech about training is scarce and arrives in clips of one to
    five minutes; Grover's is abundant and arrives in 90-minute podcasts.

    - Rank everything by duration and the budget goes entirely to the trainer.
    - Take every cheap subject clip first and it goes entirely to the subject.

    Both are the same mistake: letting one tier's shape decide the split. So
    each tier gets an explicit quota, and the trainer's is denominated in
    minutes because that is what actually costs.
    """
    subj = [c for c in cands if c["query"] in SUBJECT_QUERIES]
    trainer = [c for c in cands if c["query"] not in SUBJECT_QUERIES]

    picked: list[dict] = []
    seen: set[str] = set()
    per_channel: dict[str, int] = {}

    def add(c: dict, cap: bool = False) -> bool:
        if c["id"] in seen:
            return False
        ch = (c["channel"] or "?").lower()
        if cap and per_channel.get(ch, 0) >= PER_CHANNEL_CAP:
            return False
        seen.add(c["id"])
        per_channel[ch] = per_channel.get(ch, 0) + 1
        picked.append(c)
        return True

    # --- subject tier. Two shapes here, and they starve each other if they
    #     share one pool: there are 40+ short clips and only a handful of long
    #     sit-downs, so filling the quota by scarcity-first takes forty
    #     30-second clips and drops the Oprah interview, the Ahmad Rashad
    #     sit-downs and the 167-minute compilation of his own finals
    #     interviews - which are the densest subject speech that exists.
    #     So the long sit-downs get a reserved allocation of their own.
    subj_quota = max(1, int(budget * 0.62))
    n0 = len(picked)

    for c in sorted([c for c in subj if c["dur"] > 6.0], key=lambda c: -c["dur"])[:SUBJ_LONG_RESERVE]:
        add(c)
    for c in sorted([c for c in subj if c["dur"] <= 6.0], key=lambda c: -c["dur"]):
        if len(picked) - n0 >= subj_quota:
            break
        add(c)

    # --- trainer tier: longest-first, spend a MINUTE budget, cap per channel
    spent = 0.0
    for c in sorted(trainer, key=lambda c: -c["dur"]):
        if spent >= TRAINER_MIN_BUDGET or len(picked) >= budget:
            break
        if add(c, cap=True):
            spent += c["dur"]
    return picked


def search(q: str, n: int) -> list[dict]:
    """Flat search - metadata only, no download, so the filter is free."""
    r = subprocess.run(
        ["yt-dlp", f"ytsearch{n}:{q}", "--flat-playlist", "--dump-json",
         "--no-warnings", "--ignore-errors"],
        capture_output=True, text=True)
    out = []
    for line in r.stdout.splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("id"):
            out.append({"id": d["id"], "title": d.get("title", ""),
                        "channel": d.get("channel") or d.get("uploader") or "",
                        "dur": (d.get("duration") or 0) / 60.0, "query": q})
    return out


def build_pool() -> tuple[dict[str, dict], list[dict]]:
    """Collect across EVERY query before filtering, so duration ranking sees
    the whole pool rather than whatever the first query happened to return."""
    have = existing_ids()
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    pool: dict[str, dict] = {}
    dropped: list[dict] = []

    for q, n in QUERIES:
        hits = search(q, n)
        for c in hits:
            if c["id"] in pool or c["id"] in have:
                continue
            if ledger.get(c["id"], {}).get("ok"):
                continue
            why = reject(c["title"])
            if why:
                dropped.append({**c, "why": why})
                continue
            if not (MIN_MIN <= c["dur"] <= MAX_MIN):
                dropped.append({**c, "why": f"duration {c['dur']:.0f}min"})
                continue
            pool[c["id"]] = c
        print(f"  {q[:56]:58s} +{len(hits):3d} hits, pool {len(pool)}", flush=True)

    return pool, dropped


def download(vid: str, maxh: int = 1080) -> bool:
    for f in HD.glob(f"{vid}*.part"):
        f.unlink(missing_ok=True)
    for f in HD.glob(f"{vid}*.ytdl"):
        f.unlink(missing_ok=True)
    subprocess.run(
        ["yt-dlp", f"https://www.youtube.com/watch?v={vid}",
         "-f", f"bv*[height<={maxh}]+ba/b[height<={maxh}]/b",
         "--merge-output-format", "mp4",
         "-o", str(HD / "%(id)s.%(ext)s"),
         "--no-continue",
         "--extractor-args", "youtube:player_client=web_safari,android,tv",
         "--no-warnings", "--no-playlist", "--ignore-errors",
         "--retries", "3", "--socket-timeout", "30"],
        capture_output=True, text=True)
    return (HD / f"{vid}.mp4").exists()


def main() -> None:
    # Windows stdout is cp1252 and dies on the first non-Latin-1 channel name.
    # The JSON is written utf-8 explicitly; this is only the terminal.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    MAN.mkdir(parents=True, exist_ok=True)
    HD.mkdir(parents=True, exist_ok=True)
    dry = "--dry" in sys.argv
    budget = next((int(a) for a in sys.argv[1:] if a.isdigit()), 40)

    pool, dropped = build_pool()
    cands = sorted(pool.values(), key=lambda c: -c["dur"])

    POOL.write_text(json.dumps({"pool": cands, "dropped": dropped}, indent=1,
                               ensure_ascii=False), encoding="utf-8")

    by_why: dict[str, int] = {}
    for d in dropped:
        k = d["why"].split()[0]
        by_why[k] = by_why.get(k, 0) + 1
    print(f"\n{len(cands)} candidates ({sum(c['dur'] for c in cands):.0f} min), "
          f"{len(dropped)} dropped: {by_why}")
    print(f"pool written to {POOL}")

    take = select(cands, budget)
    n_subj = sum(1 for c in take if c["query"] in SUBJECT_QUERIES)
    print(f"selected {len(take)}: {n_subj} subject-voice, "
          f"{len(take) - n_subj} trainer/insider "
          f"({sum(c['dur'] for c in take):.0f} min)")

    if dry:
        print("\n--- selection ---")
        for c in take:
            tier = "SUBJ" if c["query"] in SUBJECT_QUERIES else "TRNR"
            print(f"  {tier} {c['dur']:6.1f}min  {c['id']}  "
                  f"{c['channel'][:20]:22s} {c['title'][:58]}")
        print("\n--dry: nothing downloaded")
        return

    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    print(f"\ndownloading {len(take)} ({sum(c['dur'] for c in take):.0f} min)\n")
    got = 0
    for i, c in enumerate(take, 1):
        # Trainer sources are podcast talking-heads: we need the AUDIO and a
        # usable clip to play when they are quoted, not detail. 720p there and
        # 1080p for the subject saves ~half the disk for no editorial loss.
        maxh = 1080 if c["query"] in SUBJECT_QUERIES else 720
        ok = download(c["id"], maxh)
        ledger[c["id"]] = {**c, "ok": ok, "maxh": maxh}
        LEDGER.write_text(json.dumps(ledger, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        got += ok
        print(f"  [{i}/{len(take)}] {'OK  ' if ok else 'FAIL'} {c['dur']:6.1f}min "
              f"{c['id']} {c['title'][:56]}", flush=True)
    print(f"\ndownloaded {got}/{len(take)}; library now "
          f"{len(list(HD.glob('*.mp4')))} sources")


if __name__ == "__main__":
    main()
