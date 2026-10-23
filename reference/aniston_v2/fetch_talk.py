"""Harvest LONG-FORM SPEECH, not b-roll.

The existing 194-source library was harvested to have pictures to cut to. It
succeeded at that and failed at the thing the owner now wants: only ~4.6 minutes
of it is her actually talking about her health, workout or diet, which is not
enough to carry a 20-25 minute film where she leads.

So this fetch has a different objective from `fetch_more.py`. It goes looking for
videos where somebody TALKS AT LENGTH - podcasts, sit-down interviews, the Pvolve
library, and the trainer's own segments - and it deliberately prefers a 40-minute
conversation over a 40-second red-carpet clip.

Two guards worth keeping:

- **Skip what is already on disk.** Matching by YouTube id, not by title, because
  the same interview is re-uploaded under a dozen different names.
- **Cap the duration.** A 3-hour podcast costs ~40 minutes of transcription for
  maybe one usable answer. `MAX_MIN` keeps the sweep affordable; the exception
  list is for sources known to be worth it.

Nothing here judges whether it is really her speaking. That is `bites.py`'s job,
and it needs the text to do it - see the voice-versus-face note there.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
LEDGER = ROOT / "manifest" / "fetch_talk.json"

MAX_MIN = 95
MIN_MIN = 1.0

# Ordered by how likely they are to return her SPEAKING at length.
QUERIES = [
    ("Jennifer Aniston Pvolve workout interview", 12),
    ("Jennifer Aniston talks about her workout routine", 12),
    ("Jennifer Aniston diet and fitness interview", 12),
    ("Jennifer Aniston intermittent fasting interview", 10),
    ("Jennifer Aniston on staying in shape at 50", 10),
    ("Jennifer Aniston health and wellness interview", 10),
    ("Dani Coleman Pvolve head trainer interview", 12),
    ("Dani Coleman Pvolve Jennifer Aniston trainer", 10),
    ("Pvolve method explained trainer", 8),
    ("Jennifer Aniston back injury Pvolve", 8),
    ("Jennifer Aniston morning routine", 8),
    ("Jennifer Aniston podcast interview full", 10),
    ("Jennifer Aniston Leyon Azubuike boxing trainer", 8),
    ("Jennifer Aniston Mandy Ingber yoga", 8),
]


def existing_ids() -> set[str]:
    return {p.stem for p in HD.glob("*.mp4")}


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
                        "dur": (d.get("duration") or 0) / 60.0, "query": q})
    return out


def download(vid: str) -> bool:
    """Two things here are load-bearing, both learned from a 31-of-34 failure rate.

    `--no-continue` plus clearing stale `.part` files: a partial left by an earlier
    interrupted run makes yt-dlp send a Range header, and YouTube answers a resumed
    ranged request with **403 Forbidden**. It reads exactly like a blocked download
    and is not one.

    A permissive format selector and several player clients: the strict
    `bestvideo[ext=mp4]+bestaudio[ext=m4a]` chain has no fallback when a video has
    no progressive mp4, so it fails rather than taking format 18.
    """
    for f in HD.glob(f"{vid}*.part"):
        f.unlink(missing_ok=True)
    for f in HD.glob(f"{vid}*.ytdl"):
        f.unlink(missing_ok=True)
    subprocess.run(
        ["yt-dlp", f"https://www.youtube.com/watch?v={vid}",
         "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
         "--merge-output-format", "mp4",
         "-o", str(HD / "%(id)s.%(ext)s"),
         "--no-continue",
         "--extractor-args", "youtube:player_client=web_safari,android,tv",
         "--no-warnings", "--no-playlist", "--ignore-errors",
         "--retries", "3", "--socket-timeout", "30"],
        capture_output=True, text=True)
    return (HD / f"{vid}.mp4").exists()


def main(budget: int = 40) -> None:
    have = existing_ids()
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}

    # collect candidates across every query first, so the duration filter can
    # rank the whole pool rather than whatever the first query happened to return
    pool: dict[str, dict] = {}
    for q, n in QUERIES:
        for c in search(q, n):
            if c["id"] in have or ledger.get(c["id"], {}).get("ok"):
                continue
            if not (MIN_MIN <= c["dur"] <= MAX_MIN):
                continue
            pool.setdefault(c["id"], c)
        print(f"  searched: {q[:52]:54s} pool now {len(pool)}", flush=True)

    # longest first - a sit-down interview beats a red-carpet soundbite
    cands = sorted(pool.values(), key=lambda c: -c["dur"])[:budget]
    print(f"\n{len(cands)} to download "
          f"({sum(c['dur'] for c in cands):.0f} min)\n", flush=True)

    got = 0
    for i, c in enumerate(cands, 1):
        ok = download(c["id"])
        ledger[c["id"]] = {**c, "ok": ok}
        LEDGER.write_text(json.dumps(ledger, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        got += ok
        print(f"  [{i}/{len(cands)}] {'OK  ' if ok else 'FAIL'} "
              f"{c['dur']:5.1f}min {c['id']} {c['title'][:56]}", flush=True)
    print(f"\ndownloaded {got}/{len(cands)}; library now "
          f"{len(list(HD.glob('*.mp4')))} sources")


if __name__ == "__main__":
    main(budget=int(sys.argv[1]) if len(sys.argv) > 1 else 40)
