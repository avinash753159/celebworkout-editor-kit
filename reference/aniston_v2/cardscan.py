"""Measure, per source, how many seconds of TITLE CARD sit at its head and how
many seconds of END CARD sit at its tail.

WHY THIS EXISTS
---------------
`reels5.TAIL` was a single constant, MAX_SHOT + 3.0 = 9.4s, and a flat margin
cannot be right for every file: a YouTube end card runs ten to twenty seconds.
Measured on this library, 55 of the ~110 un-banned sources end on a full-frame
graphic - SUBSCRIBE, WATCH MORE, a channel ident, an advertiser's product
card - and `-MXQ_3DNX_Y`'s last allowed window (303.8s) was squarely inside a
"WATCH MORE / SUBSCRIBE" screen.

HOW IT MEASURES, and why this signature works where the two in src_sweep.py's
docstring failed. Pillarbox fraction and inter-frame motion both ask "is this
frame graphic-like?", and neither can tell a dark stage from a black bar or a
Ken Burns push from a hand-held. This asks a different question: IS THIS FRAME
THE SAME PICTURE AS THE LAST FRAME OF THE FILE? An end card is, by
construction, held to the end; footage is not. So walk backwards from the end
and stop at the first frame that does not match. That gives the card's LENGTH,
which is the number the tail rule actually needs.

The same walk forwards from frame 0 gives the head title card.

Sampling is 2fps over the last/first 45 seconds, pulled in ONE ffmpeg call per
end per source into a 32x18 grey rawvideo stream, so the whole library costs a
few minutes rather than 7,700 seeks.

    python3 cardscan.py            # writes manifest/cards_scan.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DUR = json.loads((ROOT / "manifest" / "hd_dur.json").read_text(encoding="utf-8"))

WIN = 45.0          # how far in from each end to look
FPS = 2.0           # sample rate
CW, CH = 32, 18     # thumbnail the comparison runs on
# Mean absolute difference, 0-255, below which two thumbnails are "the same
# picture". 14 was chosen by reading the sheets: the Graham Norton gold card
# and the Fallon SUBSCRIBE screen both sit under 6, and the tightest real
# footage pair - a locked-off interview two-shot - sits above 18.
SAME = 14.0
PAD = 1.5           # seconds of dissolve to give back


def strip(vid: str, start: float, dur: float) -> np.ndarray | None:
    src = ROOT / "hd" / f"{vid}.mp4"
    if not src.exists():
        return None
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, start):.2f}", "-t", f"{dur:.2f}",
         "-i", str(src), "-vf", f"fps={FPS},scale={CW}:{CH}", "-pix_fmt", "gray",
         "-f", "rawvideo", "-"],
        capture_output=True)
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = buf.size // (CW * CH)
    if n < 3:
        return None
    return buf[:n * CW * CH].reshape(n, CH, CW).astype(np.float32)


def run_from_end(fr: np.ndarray) -> float:
    """Seconds of held picture at the END of this strip."""
    ref = np.median(fr[-3:], axis=0)
    k = 0
    for i in range(fr.shape[0] - 1, -1, -1):
        if np.abs(fr[i] - ref).mean() > SAME:
            break
        k += 1
    return k / FPS


def run_from_head(fr: np.ndarray) -> float:
    ref = np.median(fr[:3], axis=0)
    k = 0
    for i in range(fr.shape[0]):
        if np.abs(fr[i] - ref).mean() > SAME:
            break
        k += 1
    return k / FPS


def main() -> None:
    vids = sorted(p.stem for p in (ROOT / "hd").glob("*.mp4"))
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        vids = [v for v in vids if v in sys.argv[1:]]
    out = {}
    for i, v in enumerate(vids):
        d = DUR.get(v)
        if not d:
            continue
        w = min(WIN, max(4.0, d - 1.0))
        tail = strip(v, d - w - 0.2, w)
        head = strip(v, 0.0, w)
        t = run_from_end(tail) if tail is not None else 0.0
        h = run_from_head(head) if head is not None else 0.0
        # a "card" that fills the whole window means the measurement failed
        if t >= w - 0.6:
            t = 0.0
        if h >= w - 0.6:
            h = 0.0
        out[v] = dict(dur=round(d, 1), head=round(h, 1), tail=round(t, 1))
        if h >= 2.0 or t >= 2.0:
            print(f"{v:16s} dur {d:7.1f}   head {h:5.1f}   tail {t:5.1f}")
    (ROOT / "manifest" / "cards_scan.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n{len(out)} sources scanned -> manifest/cards_scan.json")


if __name__ == "__main__":
    main()
