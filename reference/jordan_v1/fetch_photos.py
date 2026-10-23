"""Photographs, because some things the narration says have no footage at all.

The owner's note, 28 Aug: *"whenever it mentions other players like Scotty
Pippen or whoever it is, you need to have pictures of them. Also when you're
talking about his childhood and all that stuff, it needs to be a picture of him
as a kid... When you're talking about him being scrawny, it should be him
looking really skinny and then you should have a comparison of him being built
right next to it."*

The video library cannot answer any of that. There is no 1990s broadcast footage
of Jordan aged fifteen, and a game clip of him in a Bulls jersey is the wrong
picture for a sentence about Laney High School. So named people and named eras
get PHOTOGRAPHS, pinned to the words by `cues.py`.

Fetched from Wikimedia Commons, which is freely licensed and - more useful here
- has stable, describable filenames, so a picture can be labelled by what is IN
it rather than by a search-result title.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT / "photos"
MAN = ROOT / "manifest"
LEDGER = MAN / "photos.json"
PHOTOS.mkdir(exist_ok=True)

UA = {"User-Agent": "CelebWorkout/1.0 (documentary research)"}

# slug -> search terms, most specific first. The slug is what cues.py pins to.
WANTED: dict[str, list[str]] = {
    "mj_young":        ["Michael Jordan 1984 Olympics", "Michael Jordan 1985"],
    "mj_unc":          ["Michael Jordan North Carolina", "Michael Jordan Tar Heels"],
    "mj_rookie_slim":  ["Michael Jordan 1987", "Michael Jordan Bulls 1986"],
    "mj_built":        ["Michael Jordan 1997", "Michael Jordan 1998 Bulls"],
    "scottie_pippen":  ["Scottie Pippen 1997", "Scottie Pippen Bulls"],
    "ron_harper":      ["Ron Harper basketball", "Ron Harper Bulls"],
    "randy_brown":     ["Randy Brown basketball player"],
    "dean_smith":      ["Dean Smith basketball coach"],
    "phil_jackson":    ["Phil Jackson Bulls", "Phil Jackson coach"],
    "pistons_bad_boys": ["Detroit Pistons 1990", "Isiah Thomas Pistons"],
    "hakeem":          ["Hakeem Olajuwon 1984"],
    "magic_johnson":   ["Magic Johnson 1991 Lakers", "Magic Johnson Lakers"],
    "united_center":   ["Chicago Stadium 1994", "United Center Chicago"],
    "wilmington_nc":   ["Wilmington North Carolina downtown"],
}


_last_call = [0.0]
MIN_GAP = 1.2          # seconds between API calls


def api(params: dict) -> dict:
    """One Commons call, throttled, with backoff on 429.

    The first version swallowed every exception and returned an empty result.
    Commons then rate-limited the run with HTTP 429 and eleven of fourteen
    photographs were reported as "nothing usable found" - a transport failure
    wearing the costume of an honest negative. Errors are raised now; only a
    genuinely empty result set is empty.
    """
    import time
    gap = MIN_GAP - (time.monotonic() - _last_call[0])
    if gap > 0:
        time.sleep(gap)
    url = ("https://commons.wikimedia.org/w/api.php?"
           + urllib.parse.urlencode({**params, "format": "json"}))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                _last_call[0] = time.monotonic()
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(6 * (attempt + 1))
                continue
            raise
    return {}


def search(term: str, n: int = 8) -> list[str]:
    """Image-namespace search. `filetype:bitmap` is NOT used - it silently
    matched nothing on this wiki - so extensions are filtered by the caller."""
    d = api({"action": "query", "list": "search", "srsearch": term,
             "srnamespace": "6", "srlimit": n})
    return [s["title"] for s in d.get("query", {}).get("search", [])]


def image_url(title: str, width: int = 1400) -> tuple[str, str] | None:
    d = api({"action": "query", "titles": title, "prop": "imageinfo",
             "iiprop": "url|extmetadata", "iiurlwidth": width})
    for p in d.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        u = ii.get("thumburl") or ii.get("url")
        if not u:
            continue
        meta = ii.get("extmetadata", {})
        credit = (meta.get("Artist", {}).get("value", "")
                  or meta.get("Credit", {}).get("value", ""))
        credit = re.sub(r"<[^>]+>", "", credit)[:120]
        return u, credit
    return None


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
        return dest.exists() and dest.stat().st_size > 8192
    except Exception:
        return False


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    want = [s for s in WANTED if not (PHOTOS / f"{s}.jpg").exists()]
    print(f"{len(want)} photographs to fetch")

    for slug in want:
        got = False
        for term in WANTED[slug]:
            for title in search(term):
                if not re.search(r"\.(jpe?g|png)$", title, re.I):
                    continue
                r = image_url(title)
                if not r:
                    continue
                url, credit = r
                dest = PHOTOS / f"{slug}.jpg"
                if download(url, dest):
                    ledger[slug] = {"title": title, "url": url, "credit": credit,
                                    "term": term}
                    print(f"  OK  {slug:18s} {title[:58]}")
                    got = True
                    break
            if got:
                break
        if not got:
            print(f"  --  {slug:18s} nothing usable found")
    LEDGER.write_text(json.dumps(ledger, indent=1, ensure_ascii=False),
                      encoding="utf-8")
    print(f"\n{len(list(PHOTOS.glob('*.jpg')))} photographs on disk")


if __name__ == "__main__":
    main()
