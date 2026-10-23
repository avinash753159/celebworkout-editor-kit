"""Real photographs, from image search.

Every still in this project until now was GENERATED. That is right for food and
for movements nobody has filmed her doing, and wrong for a biography: there are
thousands of real photographs of her and the cut was using none of them. The
picture layer leaned on 40 video sources, nine of which carried 60% of the
shots, and it repeated.

Uses DuckDuckGo's image endpoint, which needs no key. Results are filtered on
size, deduped on content hash, and every one still has to be LOOKED AT before
it reaches a pool - image search returns other people, fan art and posters
under her name, and none of that is caught by any automatic check here.

    python3 fetch_photos.py                # all queries in QUERIES
    python3 fetch_photos.py "some query"   # one ad-hoc query

Writes photos/<slug>_<n>.jpg and manifest/photos.json (query + source url).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "photos"
LEDGER = ROOT / "manifest" / "photos.json"

MIN_W, MIN_H = 900, 600          # under this an upscale to 1080p is mush
PER_QUERY = 14

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

# Spread across eras and contexts so the pools stop leaning on one shoot.
QUERIES = [
    "Jennifer Aniston 1994 portrait",
    "Jennifer Aniston 1990s red carpet",
    "Jennifer Aniston Friends Rachel Green",
    "Jennifer Aniston 2000s premiere",
    "Jennifer Aniston Golden Globes award",
    "Jennifer Aniston Emmy award 2002",
    "Jennifer Aniston magazine cover portrait",
    "Jennifer Aniston 2010s red carpet gown",
    "Jennifer Aniston The Morning Show press",
    "Jennifer Aniston workout gym",
    "Jennifer Aniston running outdoors",
    "Jennifer Aniston yoga mat",
    "Jennifer Aniston candid street",
    "Jennifer Aniston smiling headshot",
]


HITS = ROOT / "gl" / "img_hits.json"


def search(query: str) -> list[str]:
    """URLs harvested by gl/img_scrape.mjs.

    The keyless JSON endpoints 403 now, so the search itself runs in headless
    Chrome (same approach as the Pixabay music harvest) and lands in
    img_hits.json. This just consumes it.
    """
    if not HITS.exists():
        raise RuntimeError("run: node gl/img_scrape.mjs \"<query>\" first")
    return json.loads(HITS.read_text(encoding="utf-8")).get(query, [])


def grab(query: str, ledger: dict) -> int:
    slug = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_")[:34]
    try:
        hits = search(query)
    except Exception as e:
        print(f"  {query[:38]:38s} SEARCH FAILED: {str(e)[:60]}")
        return 0
    got = 0
    for src in hits:
        if got >= PER_QUERY:
            break
        if not src or src in ledger.get("seen", []):
            continue
        try:
            req = urllib.request.Request(src, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=30).read()
        except Exception:
            time.sleep(0.8)
            continue
        time.sleep(0.4)          # hosts start refusing after a fast run
        if len(raw) < 60_000:
            continue
        digest = hashlib.sha1(raw).hexdigest()[:12]
        if digest in ledger["by_hash"]:
            continue
        # size is only knowable after the download now, so check it here
        try:
            from PIL import Image
            import io
            w, hh = Image.open(io.BytesIO(raw)).size
        except Exception:
            continue
        if w < MIN_W or hh < MIN_H:
            continue
        dst = OUT / f"{slug}_{digest}.jpg"
        dst.write_bytes(raw)
        ledger["by_hash"][digest] = {"file": dst.name, "query": query,
                                     "url": src, "w": w, "h": hh}
        ledger.setdefault("seen", []).append(src)
        got += 1
    print(f"  {query[:38]:38s} {got:2d} kept of {len(hits)}")
    return got


def main() -> None:
    OUT.mkdir(exist_ok=True)
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() \
        else {"by_hash": {}, "seen": []}
    queries = sys.argv[1:] or QUERIES
    total = 0
    for q in queries:
        total += grab(q, ledger)
        LEDGER.write_text(json.dumps(ledger, indent=1), encoding="utf-8")
        time.sleep(1.5)
    print(f"\n  {total} new photos, {len(ledger['by_hash'])} in the library -> {OUT}")
    print("  NOTHING here is usable until it has been looked at.")


if __name__ == "__main__":
    main()
