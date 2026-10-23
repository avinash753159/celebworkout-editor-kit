"""Real archival material — the thing the reference has and this build did not.

The channel's own Aniston video carries its biography on HER: a childhood photo
split against her adult face, her father's Days of our Lives, Friends, the
Ferris Bueller pilot that was cancelled after one season, the perfume ad. This
build was answering those beats with generated pictures of empty rooms - a
competent stand-in for texture, but a stand-in.

Every id below was picked off a search result whose title names the thing the
narration actually says. `kind` maps to the section that may use it, so a
Friends clip cannot land under a line about 2021.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
HD.mkdir(exist_ok=True)

ARGS = ["--no-warnings", "--extractor-args", "youtube:player_client=web_embedded",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/18",
        "--merge-output-format", "mp4", "--no-playlist"]

# id, kind, what
POOL = [
    # ── Friends, the breakthrough
    ("cZh-kPkKcvU", "friends", "Rachel comes back from Greece"),
    ("XbywiblA1eQ", "friends", "Rachel gossiping, season 5"),
    ("Xm0jeY5Mp5c", "friends", "The ones with Rachel, season 5"),

    # ── the six years that get skipped: the cancelled 1990 pilots
    ("7mM-82tY-ts", "early",   "her scenes from the Ferris Bueller pilot"),
    ("BrbwSDa3crU", "early",   "1990 NBC Ferris Bueller promo with her in it"),
    ("HdZTcltXgy0", "early",   "Ferris Bueller TV series, s01e04"),

    # ── her father, the family business
    ("wR1SuuB-hWI", "early",   "John Aniston as Victor Kiriakis"),
    ("_K3cpT4-upk", "early",   "John Aniston, Days of our Lives"),
    ("OJMVlOcu7ew", "early",   "a Victor Kiriakis moment"),

    # ── the film career
    ("P3IsUOSHlnU", "films",   "Cake, official trailer 2014"),
    ("Ws-9ra38AlI", "films",   "Marley & Me trailer"),
    ("JlpIdAmkT_k", "films",   "The Morning Show, Alex and her father"),
    ("UaCksy-pd-M", "films",   "The Morning Show"),
]


def probe(p: Path) -> tuple[float, str]:
    if not p.exists() or p.stat().st_size < 60_000:
        return 0.0, "?"
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "format=duration:stream=width,height", "-of", "json", str(p)],
        capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        s = d["streams"][0]
        return float(d["format"]["duration"]), f"{s['width']}x{s['height']}"
    except Exception:
        return 0.0, "?"


def main() -> None:
    led, ok, fail = {}, 0, 0
    for i, (vid, kind, what) in enumerate(POOL, 1):
        dst = HD / f"{vid}.mp4"
        dur, size = probe(dst)
        if dur > 3:
            print(f"  [{i:>2}/{len(POOL)}] {vid} cached {dur:6.1f}s {size}")
            led[vid] = {"seconds": dur, "size": size, "kind": kind, "what": what}
            ok += 1
            continue
        r = subprocess.run([*["yt-dlp", *ARGS], "-o", str(dst),
                            f"https://www.youtube.com/watch?v={vid}"],
                           capture_output=True, text=True)
        dur, size = probe(dst)
        if dur > 3:
            print(f"  [{i:>2}/{len(POOL)}] {vid} ok     {dur:6.1f}s {size:>9}  {what}")
            led[vid] = {"seconds": dur, "size": size, "kind": kind, "what": what}
            ok += 1
        else:
            tail = (r.stderr or "").strip().splitlines()
            print(f"  [{i:>2}/{len(POOL)}] {vid} FAIL   {tail[-1][:70] if tail else '?'}")
            dst.unlink(missing_ok=True)
            fail += 1
    (ROOT / "manifest" / "archive.json").write_text(
        json.dumps(led, indent=1), encoding="utf-8")
    print(f"\n  {ok} downloaded, {fail} failed, "
          f"{sum(v['seconds'] for v in led.values())/60:.1f} min of real archive")


if __name__ == "__main__":
    main()
