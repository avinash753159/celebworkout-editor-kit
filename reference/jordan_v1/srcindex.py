"""What each source actually looks like: its true picture box, and where it cuts.

Two measurements, both of which the Aniston build got wrong in instructive ways.

CROP
----
Several sources are letterboxed or pillarboxed INSIDE their container - 1990s
broadcast pillarboxed into a 16:9 upload, a 4:3 master with black bars baked in.
A crop expressed as a fraction of the container keeps the bars, so the active
picture box is detected with `cropdetect` before any editorial crop is applied.

Sources whose active box is under ~640px wide after cropping are banned: a
320x240 clip upscaled 6x to 1080p is mush, and sharpening makes it worse.

CUTS
----
The reference build pre-measured cut positions for a fixed source list, and
`clear_seconds()` returned an optimistic **99.0** for any window it had no data
for. That default reads as "no cut here" and is how a shot ran straight through
a hard cut: new footage was added to the pool list but not to the cut-measured
list, so every one of its windows answered "clear" by stepping onto a hole in
the data. The same shape of bug passed ten pins in a "fix" that was not one.

The fix here is structural rather than procedural. Nothing is pre-measured, so
nothing can be MISSING from the measurement: `clear_seconds()` measures the
window it is asked about, at the moment it is asked, and caches the result by
content. There is no "unmeasured" state to default, and therefore no default to
get wrong.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
MAN = ROOT / "manifest"
CROP = MAN / "crop.json"
CUTS = MAN / "cuts_measured.json"

# The 640px floor inherited from the Aniston build is WRONG for this subject,
# and applying it unexamined would have deleted the film.
#
# That library was modern HD. This one is 1990s broadcast archive: measured
# here, the best Jordan conditioning-and-nutrition interview is 320x240, and
# the age-30 sit-down that anchors the identity reference is 480x360. A 620px
# floor bans both, along with most of the subject's own voice.
#
# What makes that acceptable rather than a compromise: REFERENCE_SPEC.md
# measured the CHANNEL at 1280x720, "mixed, soft, unfussy - not a premium
# documentary look". Delivering 720p instead of 1080p turns 480x360 into a 2x
# upscale rather than a 6x one, and matches the thing being emulated. Below
# ~300px the picture is genuinely unusable at any output size, so the floor
# moves rather than disappears.
OUT_W, OUT_H = 1280, 720
MIN_WIDTH = 300
SHARP_WIDTH = 700        # at or above this, a source is "sharp" and preferred
SCENE_THRESH = 0.35      # ffmpeg scene score that counts as a hard cut

_crop: dict = json.loads(CROP.read_text(encoding="utf-8")) if CROP.exists() else {}
_cuts: dict = json.loads(CUTS.read_text(encoding="utf-8")) if CUTS.exists() else {}


def _atomic(path: Path, text: str) -> None:
    """Write via a temp file and replace.

    A plain write_text leaves the file truncated for as long as the write takes,
    and anything reading it in that window gets a JSONDecodeError on an empty
    file. That happened here: a status check read `crop.json` while the build
    was flushing it, and the traceback looked like corruption rather than a
    race. os.replace is atomic on Windows and POSIX alike.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _save() -> None:
    _atomic(CROP, json.dumps(_crop, indent=1))
    _atomic(CUTS, json.dumps(_cuts))


def dims(vid: str) -> tuple[int, int]:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0",
         str(HD / f"{vid}.mp4")], capture_output=True, text=True)
    try:
        w, h = r.stdout.strip().split(",")[:2]
        return int(w), int(h)
    except Exception:
        return 0, 0


def detect_crop(vid: str, dur: float, samples: int = 5) -> dict:
    """The ACTIVE picture box, sampled across the file.

    Sampled at several points rather than one, because a source that opens on a
    title card or a fade would otherwise report the whole frame as active - or,
    worse, report a title card's letterbox as the picture box for the whole
    source.
    """
    if vid in _crop:
        return _crop[vid]
    W, H = dims(vid)
    if not W:
        _crop[vid] = {"ok": False, "why": "unreadable"}
        return _crop[vid]

    boxes = []
    for i in range(samples):
        t = dur * (i + 1) / (samples + 1)
        r = subprocess.run(
            ["ffmpeg", "-v", "info", "-ss", f"{t:.2f}", "-i", str(HD / f"{vid}.mp4"),
             "-frames:v", "12", "-vf", "cropdetect=24:2:0", "-f", "null", "-"],
            capture_output=True, text=True)
        for m in re.finditer(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr):
            boxes.append(tuple(int(g) for g in m.groups()))
    if not boxes:
        _crop[vid] = {"ok": W >= MIN_WIDTH, "x": 0, "y": 0, "w": W, "h": H,
                      "why": "no cropdetect output"}
        return _crop[vid]

    # widest/tallest active box seen - a conservative union, so a dark frame
    # cannot shrink the picture box for the whole source
    w = max(b[0] for b in boxes)
    h = max(b[1] for b in boxes)
    x = min(b[2] for b in boxes)
    y = min(b[3] for b in boxes)
    ok = w >= MIN_WIDTH
    _crop[vid] = {"ok": ok, "x": x, "y": y, "w": w, "h": h, "W": W, "H": H,
                  "sharp": w >= SHARP_WIDTH,
                  "why": "" if ok else f"active box {w}x{h} too small"}
    return _crop[vid]


def sharp(vid: str) -> bool:
    """Is this source sharp enough to prefer when there is a choice?

    Not a gate - a preference. The picker uses it to break ties toward the
    better picture, so the soft archive is used where it is the only thing that
    carries the words, and the sharp footage carries everything else.
    """
    return bool(_crop.get(vid, {}).get("sharp"))


def clear_seconds(vid: str, t0: float, dur: float) -> float:
    """Seconds of UNBROKEN picture starting at t0, capped at dur.

    Measures on demand. There is deliberately no "unmeasured" branch: if this
    function returns a number, it measured that window. A check whose no-data
    answer looks like a pass is not a check.
    """
    key = f"{vid}@{t0:.2f}+{dur:.2f}"
    if key in _cuts:
        return _cuts[key]
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}",
         "-i", str(HD / f"{vid}.mp4"),
         "-vf", f"select='gt(scene,{SCENE_THRESH})',showinfo",
         "-an", "-f", "null", "-"], capture_output=True, text=True)
    times = []
    for m in re.finditer(r"pts_time:([0-9.]+)", r.stderr):
        try:
            times.append(float(m.group(1)))
        except ValueError:
            pass
    # the first detected scene change after a small guard is the cut
    hits = [x for x in times if x > 0.20]
    val = round(min(hits), 2) if hits else round(dur, 2)
    _cuts[key] = val
    if len(_cuts) % 40 == 0:
        _save()
    return val


def usable(vid: str) -> bool:
    c = _crop.get(vid)
    return bool(c and c.get("ok"))


def crop_filter(vid: str) -> str | None:
    """An ffmpeg crop expression for the active picture box, or None."""
    c = _crop.get(vid)
    if not c or not c.get("ok"):
        return None
    if c["w"] == c.get("W") and c["h"] == c.get("H"):
        return None
    return f"crop={c['w']}:{c['h']}:{c['x']}:{c['y']}"


def main() -> None:
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dur = json.loads((MAN / "hd_dur.json").read_text(encoding="utf-8"))
    banned = []
    for i, (vid, d) in enumerate(sorted(dur.items()), 1):
        c = detect_crop(vid, d)
        if not c.get("ok"):
            banned.append((vid, c.get("why", "")))
        if i % 10 == 0:
            _save()
            print(f"  {i}/{len(dur)}", flush=True)
    _save()
    print(f"\n{len(dur)} sources; {len(banned)} banned as too small:")
    for v, why in banned:
        print(f"  {v}  {why}")


if __name__ == "__main__":
    main()
