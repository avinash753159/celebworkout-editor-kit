"""Score every harvested image against the verified Jordan reference.

Image search cannot be trusted to return the right man. "Michael Jordan
basketball childhood young boy photo" returned thirteen photographs of Michael
JACKSON and one of Jordan. Reading 196 candidates by eye is possible but slow,
and the tool for this already exists in the build: the SFace reference
assembled in `ident.py` from nine frames verified by eye, which separates Jordan
from his own teammates (Jordan 0.668, Pippen 0.025, Horace Grant 0.171).

So the recogniser does the first pass and throws out the Jacksons. It does NOT
decide what goes in the film - it only decides what is worth looking at. Every
survivor still goes on a contact sheet and is chosen by eye, because the score
says who is in the frame and says nothing about whether the picture is any good,
what era it is, or whether it is a magazine cover with type all over it.

Images with no detectable face are kept in a separate bucket rather than
discarded: a wide weight-room shot is exactly what the workout section needs and
the detector will find nothing in it.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

import ident

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "photos_raw"
OUT = ROOT / "photos_ranked"
MAN = ROOT / "manifest"

KEEP = 0.34          # at or above: the recogniser says it is him


def embed_file(p: Path):
    im = cv2.imread(str(p))
    if im is None:
        return None
    h, w = im.shape[:2]
    if max(h, w) > 1400:
        s = 1400 / max(h, w)
        im = cv2.resize(im, (int(w * s), int(h * s)))
    return ident.embed(im)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(exist_ok=True)
    ref = ident.build_reference()
    rows = []
    for p in sorted(RAW.glob("*.jpg")):
        e = embed_file(p)
        score = -1.0 if e is None else round(float(np.dot(e, ref)), 4)
        rows.append({"file": p.name, "score": score})
    rows.sort(key=lambda r: -r["score"])

    hit = [r for r in rows if r["score"] >= KEEP]
    noface = [r for r in rows if r["score"] < 0]
    rej = [r for r in rows if 0 <= r["score"] < KEEP]

    for r in hit:
        shutil.copy2(RAW / r["file"], OUT / f"HIT_{r['score']:.2f}_{r['file']}")
    for r in noface:
        shutil.copy2(RAW / r["file"], OUT / f"NOFACE_{r['file']}")

    (MAN / "image_scores.json").write_text(json.dumps(rows, indent=1),
                                           encoding="utf-8")
    print(f"{len(rows)} candidates")
    print(f"  {len(hit):3d} identified as Jordan (>= {KEEP})")
    print(f"  {len(rej):3d} rejected - a face, but not his")
    print(f"  {len(noface):3d} no face detected (kept: wide/action shots)")
    print("\ntop 24:")
    for r in rows[:24]:
        print(f"  {r['score']:6.3f}  {r['file']}")


if __name__ == "__main__":
    main()
