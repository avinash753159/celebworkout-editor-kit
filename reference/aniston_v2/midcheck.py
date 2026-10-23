"""Mid-shot identity check — is she still on screen 1.6s later?

The defect this fixes, found by eye in the V5 cut: Gayle King held a full frame
four times, under "back to the video", "delaying breakfast until about ten",
"a very large amount of water" and "a push to get started with your own".

Cause, measured: every passing window of iUVWGBaW1b0 IS her - all 24 were
rendered and looked at. The gate samples ONE frame, at the window start. A shot
runs ~1.6s and the source cuts to the interviewer inside it. Same mechanism put
an ET red-carpet step-and-repeat under FRIDAY / BOXING OR ROPE.

So sample the half-grid point too - t + SPREAD/2 - with the same detector and
the same reference embedding, and require BOTH ends of the shot to be her.
YuNet + SFace here rather than presence.py's Haar cascades: one grab, one
detect, one embedding, written to manifest/mid.json as
  "vid@t": [faces, biggest, identity]
with identity -1.0 when no face was found.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
M = ROOT / "models"
OUT = ROOT / "manifest" / "mid.json"
REF = ROOT / "manifest" / "identity_ref.json"


def models():
    det = cv2.FaceDetectorYN.create(
        str(M / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.75, 0.3, 5000)
    rec = cv2.FaceRecognizerSF.create(
        str(M / "face_recognition_sface_2021dec.onnx"), "")
    return det, rec


def grab(vid, t, w=640):
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(ROOT / "hd" / f"{vid}.mp4"),
         "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "3", "-"], capture_output=True)
    if not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)


def score(det, rec, ref, img):
    if img is None:
        return [0, 0.0, -1.0]
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    ok, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        return [0, 0.0, -1.0]
    faces = sorted(faces, key=lambda f: -f[2] * f[3])
    big = float(faces[0][2] * faces[0][3]) / float(w * h)
    e = rec.feature(rec.alignCrop(img, faces[0])).flatten()
    e = e / np.linalg.norm(e)
    return [len(faces), round(big, 4), round(float(np.dot(e, ref)), 4)]


def main():
    det, rec = models()
    ref = np.array(json.loads(REF.read_text()), np.float32)

    import reels5 as R
    # every window that currently passes the start-of-shot gate, plus the
    # ungated week pool - those are the ones a build can actually reach.
    # NOT windows(subject=True) - that gate REQUIRES a mid entry, which is what
    # this script exists to produce, so it can never reach a new source. It is
    # the same deadlock that hid all 111 sources added in pass 14 from
    # presence.py and recognise.py. Enumerate on the start-of-shot gate only:
    # a face, not a panel, and identity above threshold at t.
    want = set()
    for v in R.DUR:
        if v in R.BANNED:
            continue
        for _, t in R.windows(v):
            # NOT `rec` - that name holds the SFace recogniser in this
            # function, and shadowing it passed a dict into score().
            pres_rec = R.PRESENCE.get(f"{v}@{t}")
            ident = R.IDENTITY.get(f"{v}@{t}")
            if not pres_rec or ident is None or ident < R.MIN_IDENTITY:
                continue
            if not (0 < pres_rec["faces"] <= R.MAX_FACES
                    and pres_rec["biggest"] >= R.MIN_FACE):
                continue
            want.add((v, round(t + R.SPREAD / 2, 2)))
    for src in (R.DEMO_SRC + R.HER_TRAIN_SRC):
        for _, t in R.windows(src):
            want.add((src, round(t + R.SPREAD / 2, 2)))

    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = sorted(w for w in want if f"{w[0]}@{w[1]}" not in have)
    print(f"  {len(want)} half-grid points, {len(todo)} to score")
    for i, (vid, t) in enumerate(todo, 1):
        have[f"{vid}@{t}"] = score(det, rec, ref, grab(vid, t))
        if i % 250 == 0:
            OUT.write_text(json.dumps(have), encoding="utf-8")
            print(f"    {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have), encoding="utf-8")
    her = sum(1 for v in have.values() if v[2] >= 0.35)
    print(f"\n  scored {len(have)}; still her 1.6s later: {her} "
          f"({her / max(1, len(have)) * 100:.0f}%)")


if __name__ == "__main__":
    main()
