"""Awards, acceptance speeches and childhood material.

F7 in REMEDIATION.md: a celebrity workout-and-diet profile that never shows the
Emmy, the SAG award, or a single childhood photograph, while the reference
carries all three. The narration already names the Emmy, the Golden Globe and
the Screen Actors Guild award; none of them were on screen.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
ARGS = ["--no-warnings", "--extractor-args", "youtube:player_client=web_embedded",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/18",
        "--merge-output-format", "mp4", "--no-playlist"]

POOL = [
    ("0vy5wFgkP2U", "awards", "wins the 2002 Emmy for Lead Actress"),
    ("yN_Tp10MHmQ", "awards", "wins Best Actress, Golden Globes"),
    ("e1hAV-ZrRpI", "awards", "SAG acceptance speech, 26th SAG Awards"),
    ("nivqKWke94k", "awards", "wins the SAG award for The Morning Show"),
    ("D0PDC03Cu5c", "awards", "People's Choice Award, 2001"),
    ("wXjjzHrpZCQ", "friends", "the Friends cast arrive, 1996 Golden Globes"),
    ("MpEnM_zYNgo", "awards", "her Golden Globe acceptance speeches"),
    ("CsLRK1JphL4", "early",  "childhood photographs and first roles"),
    ("NP5IP8715vg", "early",  "transformation, age 1 to 52"),
]


def probe(p: Path):
    if not p.exists() or p.stat().st_size < 60_000:
        return 0.0, "?"
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "format=duration:stream=width,height",
                        "-of", "json", str(p)], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout); st = d["streams"][0]
        return float(d["format"]["duration"]), f"{st['width']}x{st['height']}"
    except Exception:
        return 0.0, "?"


def main():
    led, ok, fail = {}, 0, 0
    for i, (vid, kind, what) in enumerate(POOL, 1):
        dst = HD / f"{vid}.mp4"
        d, size = probe(dst)
        if d > 3:
            print(f"  [{i}/{len(POOL)}] {vid} cached {d:6.1f}s {size}")
            led[vid] = {"seconds": d, "size": size, "kind": kind, "what": what}
            ok += 1; continue
        r = subprocess.run([*["yt-dlp", *ARGS], "-o", str(dst),
                            f"https://www.youtube.com/watch?v={vid}"],
                           capture_output=True, text=True)
        d, size = probe(dst)
        if d > 3:
            print(f"  [{i}/{len(POOL)}] {vid} ok    {d:6.1f}s {size:>10}  {what}")
            led[vid] = {"seconds": d, "size": size, "kind": kind, "what": what}
            ok += 1
        else:
            t = (r.stderr or "").strip().splitlines()
            print(f"  [{i}/{len(POOL)}] {vid} FAIL  {t[-1][:60] if t else '?'}")
            dst.unlink(missing_ok=True); fail += 1
    (ROOT / "manifest" / "awards.json").write_text(json.dumps(led, indent=1), encoding="utf-8")
    print(f"\n  {ok} ok, {fail} failed, {sum(v['seconds'] for v in led.values())/60:.1f} min")


if __name__ == "__main__":
    main()
