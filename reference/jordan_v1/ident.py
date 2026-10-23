"""Is the face in this window HIS?

Face DETECTION is not enough. On the Aniston build it passed a full-frame
magazine portrait of Eminem, because Eminem has a face, and that shot went to
air. This subject is worse: the archive is saturated with teammates, opponents,
hosts and lookalikes, and in the first twenty-eight frames I looked at by eye
there were already three impostors sitting inside sources whose TITLES say
Michael Jordan - Larry King twice inside a source filed as a Jordan interview,
Scottie Pippen inside the 1991 Bulls Oprah show, and a man in a beret inside
"Michael Jordan | Interview | 1997".

Two rules this file exists to enforce:

1. **References are verified BY EYE, and anchored to SOURCE timecodes** - never
   to the finished film. Film-anchored references rot: on Aniston they were
   rebuilt against the cut and Lisa Kudrow then scored +0.836 against Aniston's
   own reference, because by then the reference WAS partly Kudrow.

2. **Absent data returns -1, never a pass.** `identity_at()` answers "no data"
   distinctly from "no match", because a check whose no-data answer looks like
   a pass is not a check.

Bootstrapped deliberately: a small seed of hand-verified frontal frames scores
a wide sample, the top of that ranking is put on a contact sheet, and only the
frames confirmed by eye are promoted into the reference. Automation proposes;
the eye disposes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
M = ROOT / "models"
MAN = ROOT / "manifest"
OUT = MAN / "identity.json"
REF = MAN / "identity_ref.json"

# SFace's usual same-person threshold is 0.363. The archive here is 1990s
# broadcast - soft, interlaced, heavily compressed - so the working threshold
# sits slightly under it and the cost is paid in the eyes-on pass.
THRESH = 0.32

# Frames confirmed as Michael Jordan by eye, in the 1989-1998 era, on contact
# sheets qc/REF_SHEET.jpg and qc/REF_SHEET2.jpg.
#
# NOT in this list, and each rejected for a stated reason:
#   U1dMA2GTheQ@600,1400  Larry King, not Jordan
#   u1_3Zt0Ij6Q@900       Scottie Pippen
#   HjFfqg_wuIg@60        not Jordan, despite the source title
#   GDbOs5LMATM@600       Jordan, but present-day - wrong era to match 1990s
#   XYZaagc4j3Y@600       Jordan beside Bill Cosby; two faces, largest is
#                         ambiguous and embed() takes the largest
SEED = [
    ("77Q3X2S1tbo", 300.0),     # frontal, red hoodie, age 30
    ("U1dMA2GTheQ", 250.0),     # frontal, CNN sit-down
    ("lhUTSxQasIU", 50.0),      # frontal portrait, instructional piece
    ("lhUTSxQasIU", 20.0),      # near-profile, same source
    ("HjFfqg_wuIg", 55.0),      # beret + hoodie, 1993 press - see note below
    ("HjFfqg_wuIg", 60.0),
    ("R57g3vFIHZk", 1500.0),    # white hat, young
    ("XYZaagc4j3Y", 600.0),     # Oprah couch; MJ is the dominant face
    ("u1_3Zt0Ij6Q", 2200.0),    # 1991 Bulls Oprah show, grey shirt
]

# A correction worth keeping, because it cuts against this file's own bias.
# HjFfqg_wuIg@60 was rejected by eye off a 300px contact sheet as "not Jordan",
# and the recogniser scored it 0.564. At 560px it is plainly him. The model was
# right and the eyeball was wrong - so contact sheets for IDENTITY decisions are
# rendered large here, and a disagreement between eye and score is re-examined
# at full size rather than settled by assuming the eye wins.
#
# Measured separation on the 1991 Bulls Oprah show, where Jordan sits beside his
# own teammates - the hardest available negative test:
#     Jordan          0.668
#     Horace Grant    0.171, 0.234
#     Scottie Pippen  0.025
#     audience member -0.057
# The threshold at 0.32 sits in the middle of a wide, real gap.

_det = _rec = None


def models():
    global _det, _rec
    if _det is None:
        _det = cv2.FaceDetectorYN.create(
            str(M / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.75, 0.3, 5000)
        _rec = cv2.FaceRecognizerSF.create(
            str(M / "face_recognition_sface_2021dec.onnx"), "")
    return _det, _rec


def grab(vid: str, t: float, w: int = 640):
    p = HD / f"{vid}.mp4"
    if not p.exists():
        return None
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p),
         "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "3", "-"], capture_output=True)
    if not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)


def embed(img):
    """Largest face in the frame -> normalised 128-d embedding."""
    if img is None:
        return None
    det, rec = models()
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    ok, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        return None
    faces = sorted(faces, key=lambda f: -f[2] * f[3])
    e = rec.feature(rec.alignCrop(img, faces[0])).flatten()
    n = np.linalg.norm(e)
    return None if n == 0 else e / n


def face_geometry(img):
    """(n_faces, biggest_area_fraction) - presence, separate from identity."""
    if img is None:
        return 0, 0.0
    det, _ = models()
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    ok, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        return 0, 0.0
    big = max(f[2] * f[3] for f in faces) / float(w * h)
    return len(faces), round(float(big), 4)


def build_reference(pairs=None, force=False) -> np.ndarray:
    if REF.exists() and not force:
        return np.array(json.loads(REF.read_text(encoding="utf-8")), np.float32)
    vecs = []
    for vid, t in (pairs or SEED):
        e = embed(grab(vid, t))
        if e is not None:
            vecs.append(e)
        else:
            print(f"  no face at {vid}@{t}")
    if not vecs:
        raise SystemExit("no reference faces found")
    ref = np.mean(vecs, axis=0)
    ref = ref / np.linalg.norm(ref)
    REF.write_text(json.dumps(ref.tolist()), encoding="utf-8")
    print(f"  reference built from {len(vecs)}/{len(pairs or SEED)} frames")
    return ref


def score(vid: str, t: float, ref: np.ndarray) -> float:
    e = embed(grab(vid, t))
    return -1.0 if e is None else round(float(np.dot(e, ref)), 4)


def identity_at(vid: str, t: float, tol: float = 1.5) -> tuple[float, int]:
    """(best score, samples) near t. (-1, 0) means UNMEASURED, not clean."""
    idx = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    pts = []
    for k, v in idx.items():
        src, _, ts = k.rpartition("@")
        if src != vid:
            continue
        try:
            tt = float(ts)
        except ValueError:
            continue
        if t - tol <= tt <= t + tol:
            pts.append(float(v))
    return (max(pts), len(pts)) if pts else (-1.0, 0)


def sheet(entries, path: Path, cols: int = 5, w: int = 260) -> None:
    """Contact sheet. Every claim about picture gets looked at."""
    imgs = []
    for vid, t, label in entries:
        im = grab(vid, t, w)
        if im is None:
            continue
        im = cv2.resize(im, (w, int(w * im.shape[0] / im.shape[1])))
        im = cv2.copyMakeBorder(im, 24, 3, 3, 3, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        cv2.putText(im, label[:34], (5, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.40,
                    (0, 255, 255), 1)
        imgs.append(im)
    if not imgs:
        return
    h = max(i.shape[0] for i in imgs)
    imgs = [cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, 0, cv2.BORDER_CONSTANT,
                               value=(0, 0, 0)) for i in imgs]
    rows = [np.hstack(imgs[i:i + cols]) for i in range(0, len(imgs), cols)]
    W = max(r.shape[1] for r in rows)
    rows = [r if r.shape[1] == W else
            np.hstack([r, np.zeros((r.shape[0], W - r.shape[1], 3), np.uint8)])
            for r in rows]
    cv2.imwrite(str(path), np.vstack(rows))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ref = build_reference(force="--rebuild" in sys.argv)
    step = 6.0
    dur = json.loads((MAN / "hd_dur.json").read_text(encoding="utf-8"))
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = []
    for vid, d in dur.items():
        t = 3.0
        while t < d - 1.0:
            if f"{vid}@{t}" not in have:
                todo.append((vid, round(t, 1)))
            t += step
    print(f"{len(todo)} windows to score")
    for i, (vid, t) in enumerate(todo, 1):
        have[f"{vid}@{t}"] = score(vid, t, ref)
        if i % 400 == 0:
            OUT.write_text(json.dumps(have), encoding="utf-8")
            print(f"  {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have), encoding="utf-8")
    hits = sum(1 for v in have.values() if v >= THRESH)
    noface = sum(1 for v in have.values() if v < 0)
    print(f"scored {len(have)}: {hits} match ({hits/max(1,len(have))*100:.0f}%), "
          f"{noface} no face")


if __name__ == "__main__":
    main()
