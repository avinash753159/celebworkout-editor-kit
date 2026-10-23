"""Shared motion parameters, and the job spec the GL renderer consumes.

Motion splits by shot type, deliberately:

  stills -> a three.js 2.5D dolly (gl/scene.js). This is where flat scaling
            looked worst, and where depth pays: p_nycstreet renders with more
            than DOUBLE the motion of a flat push, with the extra motion
            landing on the near railings while the vanishing point stays put.
  clips  -> a per-frame floating-point affine warp. They already carry real
            camera motion, and per-frame depth on a CPU-only torch would cost
            hours for a subtler gain.

Both replace ffmpeg `zoompan`, which floors the crop origin AND the crop size
independently. The two staircases step at different rates, so every shot in
the previous cut vibrated at ~15Hz - measured at 74 direction reversals in 88
frames on a still image, where nothing can move except by the renderer.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def renderer_sig() -> tuple:
    """Identity of the GL renderer itself, for the piece fingerprint.

    RELIEF and PUSH_STILL are already folded in, but the geometry lives in
    gl/scene.js - and editing that file alone would leave every cached piece
    stale with no warning. That exact trap has already cost this project one
    build (see build5.still_sig)."""
    out = []
    for n in ("scene.js", "render_batch.mjs"):
        f = ROOT / "gl" / n
        out.append((n, int(f.stat().st_mtime)) if f.exists() else (n, 0))
    return tuple(out)

EASE_NAME = "smoothstep"
PUSH_STILL = 0.10        # a dolly reads as less than a scale, so it can be bigger
PUSH_CLIP = 0.040        # unchanged from the zoompan build
# Depth displacement in world units. This is the parallax/crop dial: the plane
# has to overscan by 1 + RELIEF*tan(fov/2) to keep the far field covering the
# frame, so 0.35 keeps 88% of the image and 0.9 keeps only 76%. 0.9 was tried
# and the crop was too expensive for what it bought.
RELIEF = 0.45
W, H, FPS = 1920, 1080, 30

# Stills to render FLAT even though a depth map exists. Empty, and that is a
# measured result rather than an oversight: softening the depth map removed the
# tearing on every case that worried me, including the flat-lay food overheads
# (f_citrus, f_kiwi, f_seeds) which were the whole reason this set existed.
FLAT_STILLS: set[str] = set()


def ease(u: float) -> float:
    """Smoothstep. A linear push starts and stops dead, which at a 1.6s cut
    rate reads as mechanical."""
    return u * u * (3 - 2 * u)


def gl_job(image: Path, depth: Path | None, frames: int, dir_: str,
           out: Path) -> dict:
    return {
        "out": str(out).replace("\\", "/"),
        "image": str(image).replace("\\", "/"),
        "depth": (str(depth).replace("\\", "/")
                  if depth is not None and image.stem not in FLAT_STILLS
                  else None),
        "frames": int(frames), "push": PUSH_STILL, "dir": dir_,
        "fps": FPS, "w": W, "h": H, "relief": RELIEF,
    }


def warp_clip(src, t0, frames, out, inward, vf, overlay, sh, trf=None,
              ss=1.35):
    """Decode -> per-frame float affine -> encode, all through pipes.

    Measured against zoompan on the same still: step sd 0.016px against
    0.091px, and zero direction reversals against 28. Costs ~55ms/frame.
    """
    import subprocess

    import cv2
    import numpy as np

    sw = int(W * ss) // 2 * 2
    sh_ = int(H * ss) // 2 * 2
    # RELATIVE path and cwd=ROOT below. An absolute Windows path carries a
    # drive-letter colon, and ffmpeg reads a colon inside a filter argument as
    # the next option - the same trap that made vidstabdetect fail silently.
    stab = ""
    if trf is not None:
        rel = trf.resolve().relative_to(ROOT).as_posix()
        stab = (f"vidstabtransform=input={rel}:smoothing=18:"
                f"crop=black:zoom=2,unsharp=5:5:0.6,")
    parts = [p for p in (stab.rstrip(","), vf) if p]
    parts.append(f"scale={sw}:{sh_}:flags=lanczos")
    chain = ",".join(parts)

    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", str(src),
         "-vf", chain, "-frames:v", str(frames), "-r", str(FPS),
         "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE,
        cwd=str(ROOT))
    enc_cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo",
               "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if overlay is not None:
        enc_cmd += ["-i", str(overlay), "-filter_complex",
                    "[0:v][1:v]overlay=0:0[o]", "-map", "[o]"]
    enc_cmd += ["-frames:v", str(frames), "-c:v", "libx264", "-preset", "medium",
                "-crf", "18", "-pix_fmt", "yuv420p", str(out)]
    enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)

    nbytes = sw * sh_ * 3
    last = None
    for k in range(frames):
        buf = dec.stdout.read(nbytes)
        if len(buf) < nbytes:
            if last is None:
                break
            f = last                      # short source: hold the last frame
        else:
            f = np.frombuffer(buf, np.uint8).reshape(sh_, sw, 3)
            last = f
        u = k / max(1, frames - 1)
        e = ease(u)
        t = e if inward else 1 - e
        z = 1.0 + PUSH_CLIP * t
        s = (sw / W) / z
        M_ = np.float32([[1 / s, 0, (W / 2) - (sw / 2) / s],
                         [0, 1 / s, (H / 2) - (sh_ / 2) / s]])
        enc.stdin.write(cv2.warpAffine(f, M_, (W, H), flags=cv2.INTER_CUBIC,
                                       borderMode=cv2.BORDER_REPLICATE).tobytes())
    enc.stdin.close()
    enc.wait()
    dec.wait()
