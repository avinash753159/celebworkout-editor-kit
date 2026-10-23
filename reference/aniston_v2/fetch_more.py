"""Fetch the new source candidates. Repetition in the V6 cut traced to source
poverty: 174 video shots drawn from 40 sources, nine of which carried 60% of
them. More distinct footage is the only real cure."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
ARGS = ["--no-warnings", "--extractor-args", "youtube:player_client=web_embedded",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/18",
        "--merge-output-format", "mp4", "--no-playlist", "--no-progress"]

LIST = Path(sys.argv[1])
lo, hi = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 10**9)
rows = [l.strip().split("|") for l in LIST.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
rows = rows[lo:hi]
ok = fail = skip = 0
for i, r in enumerate(rows, 1):
    vid = r[0]
    dst = HD / f"{vid}.mp4"
    if dst.exists() and dst.stat().st_size > 200_000:
        skip += 1
        continue
    p = subprocess.run(["yt-dlp", *ARGS, "-o", str(dst), f"https://www.youtube.com/watch?v={vid}"],
                       capture_output=True, text=True)
    if dst.exists() and dst.stat().st_size > 200_000:
        ok += 1
        print(f"  [{i}/{len(rows)}] {vid}  {dst.stat().st_size/1e6:.0f} MB", flush=True)
    else:
        fail += 1
        print(f"  [{i}/{len(rows)}] {vid}  FAILED", flush=True)
print(f"\n  downloaded {ok}, skipped {skip}, failed {fail}")
