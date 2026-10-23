"""Download the source pool at 360p, the only format YouTube will serve here.

360p is fine for what these are: archive. It gets an archive treatment and
sits alongside 1080p graphics, which is exactly how the reference channel and
every documentary in this genre looks. Upscaling is done once, at render, with
a good filter - never by the player.

Downloads are skipped if the file already exists AND probes as playable. A
file existing is not proof of a usable clip; a halted download leaves a
truncated mp4 that looks identical by name.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sources import POOL, WINDOW

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
RAW.mkdir(exist_ok=True)

ARGS = ["--no-warnings", "--extractor-args", "youtube:player_client=android",
        "-f", "18", "--no-playlist"]


def playable(p: Path) -> float:
    if not p.exists() or p.stat().st_size < 60_000:
        return 0.0
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def main() -> None:
    ledger = {}
    ok = fail = 0
    for i, (vid, era, holder, what) in enumerate(POOL, 1):
        dst = RAW / f"{vid}.mp4"
        have = playable(dst)
        if have > 5:
            print(f"  [{i:>2}/{len(POOL)}] {vid} cached {have:6.1f}s")
            ledger[vid] = {"seconds": have, "era": era, "holder": holder, "what": what}
            ok += 1
            continue

        cmd = ["yt-dlp", *ARGS, "-o", str(dst)]
        if vid in WINDOW:
            a, b = WINDOW[vid]
            cmd += ["--download-sections", f"*{a}-{b}", "--force-keyframes-at-cuts"]
        cmd.append(f"https://www.youtube.com/watch?v={vid}")

        r = subprocess.run(cmd, capture_output=True, text=True)
        dur = playable(dst)
        if dur > 5:
            print(f"  [{i:>2}/{len(POOL)}] {vid} ok     {dur:6.1f}s  {holder}")
            ledger[vid] = {"seconds": dur, "era": era, "holder": holder, "what": what}
            ok += 1
        else:
            tail = (r.stderr or r.stdout or "").strip().splitlines()
            print(f"  [{i:>2}/{len(POOL)}] {vid} FAIL   {tail[-1][:90] if tail else '?'}")
            dst.unlink(missing_ok=True)
            fail += 1

    (ROOT / "manifest" / "raw.json").write_text(
        json.dumps(ledger, indent=1), encoding="utf-8")
    print(f"\n  {ok} downloaded, {fail} failed, "
          f"{sum(v['seconds'] for v in ledger.values())/60:.1f} min of source")
    if ok < 20:
        print("  NOT ENOUGH SOURCES - stopping rather than shipping a thin film")
        sys.exit(1)


if __name__ == "__main__":
    main()
