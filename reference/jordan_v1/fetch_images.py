"""Harvest real photographs by image search, many per query, then verify by eye.

The previous attempt used Wikimedia Commons, got rate-limited, and returned
files whose TITLES matched but whose CONTENT did not - "Michael Jordan North
Carolina.JPG" was a jersey in a display case, "Pistons Bad Boys" was a box
score. Four usable pictures out of fourteen, and the film shipped with game
footage under sentences about his childhood.

This fetches from the image searches the owner actually linked - him as a kid,
him skinny, skinny versus big, him with Pippen, his workouts - and pulls MANY
candidates per query so there is something to choose from. Nothing here decides
what a picture IS: every candidate goes onto a contact sheet and is picked by
eye before it can enter the film.

DuckDuckGo is used rather than Google: it returns a clean JSON payload for a
token-plus-query request, and it does not throttle a few dozen calls into
silence the way Commons did.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "photos_raw"
MAN = ROOT / "manifest"
RAW.mkdir(exist_ok=True)

UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/124.0 Safari/537.36")}

# Straight from the owner's links, plus the specific gaps in the film.
QUERIES: dict[str, str] = {
    "kid":        "Michael Jordan basketball childhood young boy photo",
    "laney":      "Michael Jordan Laney High School basketball team photo",
    "unc":        "Michael Jordan North Carolina Tar Heels 1982 basketball",
    "skinny":     "Michael Jordan skinny thin rookie Bulls 1985 basketball",
    "skinnybig":  "Michael Jordan body transformation skinny to muscular Bulls",
    "youngold":   "Michael Jordan rookie versus 1996 physique Bulls",
    "pippen":     "Michael Jordan and Scottie Pippen Bulls together photo",
    "harper":     "Ron Harper Chicago Bulls 1996 basketball player",
    "grover":     "Tim Grover trainer Michael Jordan Bulls",
    "workout":    "Michael Jordan lifting weights weight room Bulls",
    "workout2":   "Michael Jordan training workout basketball Bulls gym",
    "muscle":     "Michael Jordan muscular arms 1996 Chicago Bulls",
    "pistons":    "Michael Jordan Detroit Pistons Bad Boys 1990 foul",
    "deansmith":  "Dean Smith coach North Carolina basketball Michael Jordan",
}

PER_QUERY = 14


def bing(q: str, n: int) -> list[dict]:
    """Bing image results, parsed from the HTML `murl` payloads.

    DuckDuckGo answers this request with 403. Bing does not, and its results
    carry the original image URL rather than a proxied thumbnail, so the
    downloads are full size.

    Every query is anchored with "basketball" or "Bulls": a bare
    "michael jordan kid childhood" returned a page of Michael JACKSON.
    """
    out, seen = [], set()
    for page in (1, 2):
        url = ("https://www.bing.com/images/search?q=" + urllib.parse.quote(q)
               + f"&form=HDRSC2&first={page}")
        try:
            req = urllib.request.Request(url, headers=UA)
            html = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
        except Exception:
            continue
        for m in re.findall(r"murl&quot;:&quot;(.*?)&quot;", html):
            u = m.replace("&amp;", "&")
            if u in seen or not re.search(r"\.(jpe?g|png)", u, re.I):
                continue
            seen.add(u)
            out.append({"url": u, "title": q})
            if len(out) >= n:
                return out
    return out


def vqd(q: str) -> str | None:
    url = "https://duckduckgo.com/?q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        html = r.read().decode("utf-8", "replace")
    for pat in (r'vqd="([\d-]+)"', r"vqd=([\d-]+)&", r'vqd=\\"([\d-]+)\\"'):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


def search_images(q: str, n: int) -> list[dict]:
    token = vqd(q)
    if not token:
        print(f"    no token for {q!r}")
        return []
    url = ("https://duckduckgo.com/i.js?l=us-en&o=json&q="
           + urllib.parse.quote(q) + "&vqd=" + token + "&f=,,,&p=1")
    req = urllib.request.Request(url, headers={**UA, "Referer": "https://duckduckgo.com/"})
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.load(r)
    out = []
    for it in d.get("results", []):
        if int(it.get("width") or 0) < 400:
            continue
        out.append({"url": it.get("image"), "w": it.get("width"),
                    "h": it.get("height"), "title": it.get("title", ""),
                    "src": it.get("url", "")})
        if len(out) >= n:
            break
    return out


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            data = r.read()
        if len(data) < 12000:
            return False
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    only = sys.argv[1:] or list(QUERIES)
    ledger = {}
    for slug in only:
        q = QUERIES.get(slug)
        if not q:
            continue
        got = 0
        try:
            hits = bing(q, PER_QUERY * 3)
        except Exception as e:
            print(f"  {slug}: search failed: {e}")
            continue
        for i, h in enumerate(hits):
            if got >= PER_QUERY:
                break
            ext = ".jpg"
            dest = RAW / f"{slug}_{got:02d}{ext}"
            if download(h["url"], dest):
                ledger[dest.name] = h
                got += 1
        print(f"  {slug:11s} {got:2d} images  ({q})", flush=True)
    (MAN / "images_raw.json").write_text(
        json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(list(RAW.glob('*.jpg')))} candidate images in photos_raw/")


if __name__ == "__main__":
    main()
