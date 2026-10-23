"""OCR every POOLED window of named sources, to size a ban.

Reading the contact sheets tells you a source carries burned-in text. It does
not tell you whether that text is in every window (ban the source) or in a
stretch of it (ban the window) - and getting that wrong either throws away
usable footage or leaves the defect live somewhere the sheets did not sample.

Samples each window at t, t+1.6 and t+3.2 - the same spread the card gate
uses - because a caption that starts 0.2s after the window's first frame is
still in the shot. Anything with three or more letters at >=0.6 confidence
counts.

    python3 src_ocr.py SRC [SRC ...]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TMP = ROOT / "qc" / "src_ocr"
OFFSETS = (0.0, 1.6, 3.2)


def main() -> None:
    import reels5 as R
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    TMP.mkdir(parents=True, exist_ok=True)
    for vid in sys.argv[1:]:
        wins = R.windows(vid, subject=False) or R.windows(vid, subject=True)
        # pooled windows only - the rest cannot reach the film
        pooled = sorted({w[1] for p in R.POOLS.values() for w in p if w[0] == vid})
        if pooled:
            wins = [(vid, t) for t in pooled]
        dirty = 0
        print(f"\n=== {vid}  ({len(wins)} pooled windows) ===")
        for v, t in wins:
            hits = []
            for off in OFFSETS:
                p = TMP / f"{v}_{t + off:.2f}.jpg"
                if not p.exists():
                    subprocess.run(
                        ["ffmpeg", "-y", "-v", "error", "-ss", f"{t + off:.2f}",
                         "-i", f"hd/{v}.mp4", "-frames:v", "1",
                         "-vf", "scale=960:-2", str(p)],
                        cwd=str(ROOT), check=False)
                if not p.exists():
                    continue
                res, _ = ocr(str(p))
                for det in (res or []):
                    txt, conf = det[1], float(det[2])
                    if conf < 0.60:
                        continue
                    if len(re.sub(r"[^A-Za-z]", "", txt)) < 3:
                        continue
                    hits.append(f"+{off:.1f} {txt.strip()!r}")
            if hits:
                dirty += 1
                print(f"  {t:8.2f}  " + " | ".join(hits[:5]))
            else:
                print(f"  {t:8.2f}  clean")
        print(f"  -> {dirty} of {len(wins)} pooled windows carry text")


if __name__ == "__main__":
    main()
