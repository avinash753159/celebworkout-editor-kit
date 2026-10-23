"""QC. Machine checks, then contact sheets for the eyes-on pass.

Every previous build in this project passed its automated checks and still
failed review, so nothing here claims the film is good. What it does is make
the failure modes cheap to look at: one frame per shot, in order, so a
watermark, a stranger holding frame, or a card nobody can read is visible in
a single image rather than after a twelve minute watch.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "JENNIFER_ANISTON_V3.mp4"
SHEETS = ROOT / "qc"
SHEETS.mkdir(exist_ok=True)


def probe_json(p: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                        "-of", "json", str(p)], capture_output=True, text=True)
    return json.loads(r.stdout)


def main() -> None:
    if not OUT.exists():
        sys.exit("no output film yet")
    info = probe_json(OUT)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    dur = float(info["format"]["duration"])
    print(f"  {OUT.name}")
    print(f"  {v['width']}x{v['height']} @ {v['r_frame_rate']}  "
          f"{int(dur)//60}:{dur%60:05.2f}  {int(info['format']['size'])/1e6:.0f} MB")
    print(f"  video {float(v['duration']):.3f}s   audio {float(a['duration']):.3f}s   "
          f"drift {abs(float(v['duration'])-float(a['duration'])):.3f}s")

    shots = json.loads((ROOT / "manifest" / "shots2.json").read_text())["shots"]
    fps = 30
    print(f"\n  {len(shots)} shots")
    from collections import Counter
    kinds = Counter(s["kind"] for s in shots)
    secs = {k: sum(s["frames"] for s in shots if s["kind"] == k) / fps for k in kinds}
    for k in sorted(kinds, key=lambda x: -secs[x]):
        print(f"    {k:<6} {kinds[k]:>3} shots  {secs[k]:>6.1f}s  "
              f"{secs[k]/dur*100:>4.0f}%")
    real = sum(secs.get(k, 0) for k in ("arch", "move", "bite"))
    print(f"    {'REAL':<6} {'':>3}         {real:>6.1f}s  {real/dur*100:>4.0f}%  "
          f"of runtime is real footage")

    durs = sorted(s["frames"] / fps for s in shots)
    mid = durs[len(durs) // 2]
    print(f"\n  shot length  median {mid:.1f}s   min {durs[0]:.1f}s   max {durs[-1]:.1f}s")
    short = [s for s in shots if s["frames"] / fps < 4.0]
    if short:
        print(f"  {len(short)} shots under 4s (rapid cutting reads as filler):")
        for s in short:
            print(f"    {s['block']} {s['tag']} {s['frames']/fps:.1f}s")

    # one frame per shot, in order
    print("\n  contact sheets ...")
    t, marks = 0.0, []
    for s in shots:
        marks.append(t + (s["frames"] / fps) / 2)
        t += s["frames"] / fps
    tmp = SHEETS / "f"
    tmp.mkdir(exist_ok=True)
    for i, m in enumerate(marks):
        subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{m:.2f}", "-i", str(OUT),
                        "-frames:v", "1", "-vf", "scale=320:180", "-y",
                        str(tmp / f"s{i:03d}.jpg")], check=True)
    per = 24
    for page in range((len(marks) + per - 1) // per):
        subprocess.run(["ffmpeg", "-v", "error", "-start_number", str(page * per),
                        "-i", str(tmp / "s%03d.jpg"), "-vf", f"tile=6x4",
                        "-frames:v", "1", "-y",
                        str(SHEETS / f"sheet{page+1}.jpg")], check=True)
    print(f"    {len(marks)} frames -> {SHEETS}")


if __name__ == "__main__":
    main()
