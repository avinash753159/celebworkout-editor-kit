"""Is the face in this window HERS?

Face DETECTION was not enough. The presence index passed a full-frame magazine
portrait of Eminem, because Eminem has a face. That shot went to air. Lisa
Kudrow, a makeup artist and an unnamed actor passed the same way.

This builds a reference embedding of Jennifer Aniston from windows that were
verified by eye in earlier passes (the six sync bites, the thumbnail frame, the
Pvolve campaign close-ups), then scores every candidate window by cosine
similarity against it. SFace's usual same-person threshold is 0.363.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
M = ROOT / "models"
OUT = ROOT / "manifest" / "identity.json"
REF = ROOT / "manifest" / "identity_ref.json"
THRESH = 0.32          # slightly under SFace's 0.363, archive is soft

# Windows verified as her by eye in earlier passes.
REFERENCE = [
    ("JJLe4jmbrN0", 3.4), ("JJLe4jmbrN0", 14.0), ("JJLe4jmbrN0", 8.0),
    ("lrZKJPVn89s", 14.4), ("lrZKJPVn89s", 12.3),
    ("K3puGMuBWKw", 140.0), ("K3puGMuBWKw", 145.0),
    ("zbnHO-r5HRs", 33.0), ("zbnHO-r5HRs", 58.0),
    ("c_ci5IriLG0", 48.0),
    ("e1hAV-ZrRpI", 40.0), ("e1hAV-ZrRpI", 90.0),
    ("LzisOKB_sEU", 31.0), ("LzisOKB_sEU", 70.0),
]


def models():
    det = cv2.FaceDetectorYN.create(
        str(M / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.75, 0.3, 5000)
    rec = cv2.FaceRecognizerSF.create(
        str(M / "face_recognition_sface_2021dec.onnx"), "")
    return det, rec


def grab(vid, t, w=640):
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(ROOT/"hd"/f"{vid}.mp4"),
         "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "3", "-"], capture_output=True)
    if not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)


def embed(det, rec, img):
    """Largest face in the frame -> 128-d embedding."""
    if img is None:
        return None
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    ok, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        return None
    faces = sorted(faces, key=lambda f: -f[2] * f[3])
    aligned = rec.alignCrop(img, faces[0])
    return rec.feature(aligned).flatten()


def main():
    det, rec = models()
    if REF.exists():
        ref = np.array(json.loads(REF.read_text()), np.float32)
    else:
        vecs = []
        for vid, t in REFERENCE:
            e = embed(det, rec, grab(vid, t))
            if e is not None:
                vecs.append(e / np.linalg.norm(e))
        if not vecs:
            raise SystemExit("no reference faces found")
        ref = np.mean(vecs, axis=0)
        ref = ref / np.linalg.norm(ref)
        REF.write_text(json.dumps(ref.tolist()), encoding="utf-8")
        print(f"  reference built from {len(vecs)}/{len(REFERENCE)} verified frames")

    # Enumerate from the raw source lists, NOT from POOLS. POOLS is built by
    # spool(subject=True), so it only holds windows that already have a score
    # above threshold - scoring from it can never reach a newly added source.
    # That deadlock hid all 111 sources added in pass 14.
    from presence import candidate_windows
    pres = json.loads((ROOT/"manifest"/"presence.json").read_text())
    wins = candidate_windows()
    # only windows that already have a face are worth scoring
    wins = [w for w in wins if pres.get(f"{w[0]}@{w[1]}", {}).get("faces", 0) > 0]
    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [w for w in wins if f"{w[0]}@{w[1]}" not in have]
    print(f"  {len(wins)} windows with a face, {len(todo)} to score")
    for i, (vid, t) in enumerate(todo, 1):
        e = embed(det, rec, grab(vid, t))
        if e is None:
            have[f"{vid}@{t}"] = -1.0
        else:
            e = e / np.linalg.norm(e)
            have[f"{vid}@{t}"] = round(float(np.dot(e, ref)), 4)
        if i % 300 == 0:
            OUT.write_text(json.dumps(have), encoding="utf-8")
            print(f"    {i}/{len(todo)}")
    OUT.write_text(json.dumps(have), encoding="utf-8")
    hits = sum(1 for v in have.values() if v >= THRESH)
    print(f"\n  scored {len(have)}; {hits} match her ({hits/len(have)*100:.0f}%)")


if __name__ == "__main__":
    main()
