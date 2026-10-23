"""Monocular depth for every generated still, so a push-in can be a DOLLY.

Flat scaling moves every pixel by the same proportion, which is why a generated
establishing shot reads as a photograph being zoomed rather than a camera
moving through a room. Depth-Anything-V2-Small runs in 1.55s per image on this
CPU torch build; ~90 stills is about two minutes.

Grayscale, 8-bit, same pixel dimensions as the source. WHITE IS NEAR - that is
what the model emits and what the shader in gl/scene.js assumes.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "depth"
SOFT = ROOT / "depth_soft"
LEDGER = ROOT / "manifest" / "depth_ledger.json"
# Blur radius as a FRACTION of image width, so it behaves the same whatever
# size the still is. A raw depth map has cliffs at every silhouette, and a
# displaced mesh tears across a cliff: measured at relief 0.8 the forearm in
# mv_plank came out sawtoothed, f_citrus smeared into radial streaks and the
# treadmill console in d_tuesday went ragged against the window. Softening the
# map turns each cliff into a ramp, so the mesh bends instead of tearing. All
# three artifacts are gone at 2%, and p_nycstreet still shows more than double
# the motion of a flat render.
BLUR_FRAC = 0.02
DIRS = ("stills_place", "stills_food", "stills_move", "stills")
# photos/ too. The nineteen real photographs were never in this list, because
# until pass 17 they were in no pool and nothing rendered them. gl_job accepts
# depth=None and falls back to a flat scale, so the omission would not have
# crashed anything - it would just have made every photograph the one shot in
# the film that reads as a zoom instead of a camera move. Their files are
# hash-named rather than stem-named, which is fine: this keys on the file's
# own stem and so does build5.still_piece.
# photos_169, not photos: the 16:9 renditions are what the renderer draws, and
# a depth map computed on the original portrait would be the wrong shape.
PHOTOS = ROOT / "photos_169"
MODEL = "depth-anything/Depth-Anything-V2-Small-hf"


def depth_path(name: str) -> Path | None:
    """The SOFTENED map - that is the one the renderer must use."""
    p = SOFT / f"{name}.png"
    return p if p.exists() else None


def _sources() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in DIRS:
        for p in sorted((ROOT / d).glob("*.jpg")):
            out.setdefault(p.stem, p)
    for p in sorted(PHOTOS.glob("*.jpg")):
        out.setdefault(p.stem, p)
    return out


def soften() -> int:
    import cv2
    SOFT.mkdir(exist_ok=True)
    n = 0
    for p in sorted(OUT.glob("*.png")):
        dst = SOFT / p.name
        if dst.exists() and dst.stat().st_mtime >= p.stat().st_mtime:
            continue
        a = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if a is None:
            continue
        k = int(a.shape[1] * BLUR_FRAC) | 1
        cv2.imwrite(str(dst), cv2.GaussianBlur(a, (k, k), 0))
        n += 1
    return n


def main() -> None:
    OUT.mkdir(exist_ok=True)
    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    src = _sources()
    todo = [(n, p) for n, p in src.items()
            if led.get(n) != int(p.stat().st_mtime)
            or not (OUT / f"{n}.png").exists()]
    print(f"  {len(src)} stills, {len(todo)} need depth")
    if not todo:
        print(f"  softened {soften()}")
        return
    from transformers import pipeline
    pipe = pipeline("depth-estimation", model=MODEL, device="cpu")
    for i, (name, p) in enumerate(todo, 1):
        d = pipe(Image.open(p).convert("RGB"))["depth"]
        d.convert("L").save(OUT / f"{name}.png")
        led[name] = int(p.stat().st_mtime)
        if i % 10 == 0 or i == len(todo):
            LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")
            print(f"    {i}/{len(todo)}", flush=True)
    LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")
    print(f"  {len(list(OUT.glob('*.png')))} depth maps in depth/")
    print(f"  softened {soften()} into depth_soft/")


if __name__ == "__main__":
    main()
