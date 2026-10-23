"""Re-fetch the whole pool FULL LENGTH at 1080p into hd/.

Two defects in the original pull, both invisible until you try to cut sync:

1. `-f 18` capped everything at 360p. That was read as YouTube's limit; it is
   the android player client's limit. `web_embedded` serves 1080p.
2. Eleven sources were pulled through `--download-sections`, so the local file
   starts partway into the video. Caption timings and any timecode quoted from
   the real video are offset by the window start, silently. A bite located at
   2:05 in the transcript lands 30s wrong in the cut.

Full-length copies remove the offset entirely: local time == real time. The
360p files stay in raw/ until every piece has been re-rendered off hd/.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
HD.mkdir(exist_ok=True)

ARGS = ["--no-warnings", "--extractor-args", "youtube:player_client=web_embedded",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/18",
        "--merge-output-format", "mp4", "--no-playlist"]


def probe(p: Path) -> tuple[float, str]:
    if not p.exists() or p.stat().st_size < 60_000:
        return 0.0, "?"
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "format=duration:stream=width,height", "-of", "json", str(p)],
        capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        dur = float(d["format"]["duration"])
        s = d["streams"][0]
        return dur, f"{s['width']}x{s['height']}"
    except Exception:
        return 0.0, "?"


def main() -> None:
    ids = sorted({p.stem for p in (ROOT / "raw").glob("*.mp4")})
    print(f"  re-fetching {len(ids)} sources full-length at 1080p\n")
    ledger, ok, fail = {}, 0, 0
    for i, vid in enumerate(ids, 1):
        dst = HD / f"{vid}.mp4"
        dur, size = probe(dst)
        if dur > 3:
            print(f"  [{i:>2}/{len(ids)}] {vid} cached {dur:7.1f}s {size}")
            ledger[vid] = {"seconds": dur, "size": size}
            ok += 1
            continue
        r = subprocess.run([*["yt-dlp", *ARGS], "-o", str(dst),
                            f"https://www.youtube.com/watch?v={vid}"],
                           capture_output=True, text=True)
        dur, size = probe(dst)
        if dur > 3:
            print(f"  [{i:>2}/{len(ids)}] {vid} ok     {dur:7.1f}s {size}")
            ledger[vid] = {"seconds": dur, "size": size}
            ok += 1
        else:
            tail = (r.stderr or r.stdout or "").strip().splitlines()
            print(f"  [{i:>2}/{len(ids)}] {vid} FAIL   {tail[-1][:70] if tail else '?'}")
            dst.unlink(missing_ok=True)
            fail += 1
    (ROOT / "manifest" / "hd.json").write_text(
        json.dumps(ledger, indent=1), encoding="utf-8")
    tot = sum(v["seconds"] for v in ledger.values())
    print(f"\n  {ok} ok, {fail} failed, {tot/60:.0f} min of source at full length")
    if fail > len(ids) // 3:
        sys.exit(1)


if __name__ == "__main__":
    main()
