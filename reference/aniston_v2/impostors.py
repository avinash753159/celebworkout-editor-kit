"""Reject a window because of WHO ELSE it looks like, not just how much it
looks like her.

A one-sided similarity test cannot tell "her" from "somebody the model finds
similar". Measured on the current cut, with the tightened gate already in
place and read off frames, not scores:

  Lisa Kudrow      held 6 full frames (Variety, shots 21/129/215/258/298/320)
                   - one of them under the quote bar "Yes, so every Sunday is
                   a cheat day - JENNIFER ANISTON"
  two podcast      held 5 (shots 23/130/217/262/321), neither of them her
  a Pvolve model   held 3 (shots 4/176/337)
  Billy Crudup     held 1 (shot 121)

Every one scored >= 0.35 against her reference at BOTH ends of the shot.
Raising the threshold does not separate them: iUVWGBaW1b0's windows score
0.59-0.72 and are her; these score in the same band and are not.

So this builds reference embeddings for the impostors from the frames above -
frames of the finished film, verified by eye - and scores every candidate
window against them too. A window is rejected when it is closer to an impostor
than to her. That is a comparison, not a threshold, so it does not cost pool
size the way a higher cut-off does.

Writes manifest/impostor.json: "vid@t" -> best impostor cosine, at t and at
t + SPREAD/2.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
M = ROOT / "models"
OUT = ROOT / "manifest" / "impostor.json"
REFS = ROOT / "manifest" / "impostor_ref.json"
FILM = ROOT / "JENNIFER_ANISTON_V6.mp4"   # was V5, which no longer exists

# (film time in seconds, who) - read off the contact sheets by eye.
IMPOSTOR_FRAMES = [
    (35.6, "kudrow"), (227.9, "kudrow"), (444.6, "kudrow"),
    (515.3, "kudrow"), (581.8, "kudrow"), (624.7, "kudrow"),
    (39.0, "podcast"), (229.9, "podcast"), (447.5, "podcast"),
    (521.6, "podcast"), (626.2, "podcast"),
    (6.7, "pvolve_model"), (330.4, "pvolve_model"), (653.2, "pvolve_model"),
    (214.9, "crudup"),
]

# (source id, seconds, who) - for people the film never showed, so there is no
# frame of them in it to point at. Vince Vaughn scored 0.43 at the window start
# and 0.52 at the mid point against HER reference and held shot 201 full frame
# for 6.2s under "a smoothie with protein powder, banana and blueberries".
# There is no cut in that window; the recogniser simply thinks he looks like
# her. That is exactly the case this file exists for.
#
# Pass 15. The ORIGINAL three vaughn timecodes (860.6, 862.2, 863.8) were
# read as "the Vince Vaughn stretch" without checking each frame - two of the
# three (860.6, 862.2) are actually HER, carrying a bag of lemons across the
# room in the same Late Show sketch cut. The averaged reference was therefore
# two-thirds her own face, which is exactly why it scored 0.5096 against
# identity_ref.json - above the 0.5 line the acceptance criteria require.
# Replaced with five frames from the same source, all individually rendered
# and confirmed to be Vaughn alone: the sketch cuts rapidly between the two of
# them and 865.0/872.0/874.0 are her again, so those are excluded too.
#
# kudrow, podcast and pvolve_model were owed from a previous pass and are
# added here for the first time, each from a SOURCE at a fixed timecode, never
# the film - see the references() docstring above for why that matters.
# kudrow: ZoqjGormrds, "Variety Actors on Actors" - Kudrow and Aniston
# alternate throughout, on a fixed even-spaced scan, and one of the scan's own
# candidates (1153.7) turned out to be HER at full render even though the
# contact-sheet thumbnail read as Kudrow's bob - dropped for exactly that
# reason. The seven kept here were each rendered at full size and confirmed
# Kudrow alone, not a two-shot.
# podcast: BpgMda_4JDI - two hosts, neither of them her: one woman (dark
# curly hair) and one man (bearded, tattooed). Both are represented.
# pvolve_model: voC2DxCL6jQ@44.6 and @54.2 were in TRAIN_OK for a previous
# pass and were WRONG - both are a younger Pvolve model, not her, caught only
# when re-read at full size (see TRAIN_OK below). @54.2 itself turned out to
# be a bad reference frame too - a blurred, extreme profile angle that scored
# 0.62 against her own identity_ref despite being a different person, which
# would have dragged the averaged reference back toward the 0.5 line. Dropped
# in favour of @31.8 and @46.0, both frontal and both confirmed the same
# woman.
IMPOSTOR_SOURCE_FRAMES = [
    ("vMuarx9iWdg", 863.8, "vaughn"),
    ("vMuarx9iWdg", 868.0, "vaughn"),
    ("vMuarx9iWdg", 870.0, "vaughn"),
    ("vMuarx9iWdg", 876.0, "vaughn"),
    ("ZoqjGormrds", 209.8, "kudrow"),
    ("ZoqjGormrds", 419.5, "kudrow"),
    ("ZoqjGormrds", 734.2, "kudrow"),
    ("ZoqjGormrds", 1363.5, "kudrow"),
    ("ZoqjGormrds", 1573.3, "kudrow"),
    ("ZoqjGormrds", 1678.1, "kudrow"),
    ("ZoqjGormrds", 1992.8, "kudrow"),
    ("BpgMda_4JDI", 1756.2, "podcast"),
    ("BpgMda_4JDI", 3512.4, "podcast"),
    ("BpgMda_4JDI", 6322.3, "podcast"),
    ("BpgMda_4JDI", 8078.5, "podcast"),
    ("BpgMda_4JDI", 7727.3, "podcast"),
    ("BpgMda_4JDI", 7900.0, "podcast"),
    ("voC2DxCL6jQ", 31.8, "pvolve_model"),
    ("voC2DxCL6jQ", 44.6, "pvolve_model"),
    ("voC2DxCL6jQ", 46.0, "pvolve_model"),
]


def models():
    det = cv2.FaceDetectorYN.create(
        str(M / "face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.75, 0.3, 5000)
    rec = cv2.FaceRecognizerSF.create(
        str(M / "face_recognition_sface_2021dec.onnx"), "")
    return det, rec


def grab(src: Path, t: float, w=640):
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src),
         "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "3", "-"], capture_output=True)
    if not r.stdout:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)


def embed(det, rec, img):
    if img is None:
        return None
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    ok, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        return None
    faces = sorted(faces, key=lambda f: -f[2] * f[3])
    e = rec.feature(rec.alignCrop(img, faces[0])).flatten()
    return e / np.linalg.norm(e)


def references(det, rec):
    if REFS.exists():
        return {k: np.array(v, np.float32) for k, v in
                json.loads(REFS.read_text()).items()}
    acc: dict[str, list] = {}
    # IMPOSTOR_FRAMES is DISABLED. Those are film timecodes from V5, and a
    # reference anchored to a film that changes silently becomes a reference to
    # whoever now sits at that second. Rebuilt against V6 they produced:
    #     kudrow       +0.836 against HER reference
    #     pvolve_model +0.789
    #     podcast      +0.650
    # i.e. three "impostors" that are Aniston. Used, they would have rejected
    # her own windows wholesale. crudup came back with no face at all.
    # References must come from a SOURCE at a fixed timecode, never the film.
    for t, who in []:
        e = embed(det, rec, grab(FILM, t))
        if e is not None:
            acc.setdefault(who, []).append(e)
    for vid, t, who in IMPOSTOR_SOURCE_FRAMES:
        e = embed(det, rec, grab(ROOT / "hd" / f"{vid}.mp4", t))
        if e is not None:
            acc.setdefault(who, []).append(e)
        else:
            print(f"    no face at {vid}@{t}s ({who})")
    refs = {}
    for who, vs in acc.items():
        v = np.mean(vs, axis=0)
        refs[who] = v / np.linalg.norm(v)
        print(f"  {who:<14} from {len(vs)} frames")
    REFS.write_text(json.dumps({k: v.tolist() for k, v in refs.items()}),
                    encoding="utf-8")
    return refs


def main():
    det, rec = models()
    refs = references(det, rec)
    if not refs:
        raise SystemExit("no impostor references built")

    import reels5 as R
    want = set()
    for v in R.DUR:
        if v in R.BANNED:
            continue
        for _, t in R.windows(v, subject=True):
            want.add((v, t))
            want.add((v, round(t + R.SPREAD / 2, 2)))
    for vid, t in R.TRAIN_OK:
        want.add((vid, t))
        want.add((vid, round(t + R.SPREAD / 2, 2)))

    have = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = sorted(w for w in want if f"{w[0]}@{w[1]}" not in have)
    print(f"  {len(want)} points, {len(todo)} to score")
    for i, (vid, t) in enumerate(todo, 1):
        e = embed(det, rec, grab(ROOT / "hd" / f"{vid}.mp4", t))
        if e is None:
            have[f"{vid}@{t}"] = -1.0
        else:
            have[f"{vid}@{t}"] = round(
                max(float(np.dot(e, r)) for r in refs.values()), 4)
        if i % 250 == 0:
            OUT.write_text(json.dumps(have), encoding="utf-8")
            print(f"    {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have), encoding="utf-8")

    beaten = sum(1 for k, v in have.items()
                 if v > (R.IDENTITY.get(k) if R.IDENTITY.get(k) is not None
                         else (R.MID.get(k, [0, 0, -1])[2])))
    print(f"\n  scored {len(have)}; {beaten} look more like somebody else")


if __name__ == "__main__":
    main()
