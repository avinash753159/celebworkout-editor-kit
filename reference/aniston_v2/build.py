"""Assemble. Archive-led, audio is the master clock.

Same timing discipline as before, and it is not negotiable: cumulative
narration boundaries are quantised to whole frames, block durations are the
differences of those integers, and each block's frames are divided among its
shots with the remainder handed to the longest. Every piece is checked frame
exact before the concat, and the mux refuses on more than 0.25 s of drift.

The one new problem here is that archive clips have a FIXED length (nine
seconds) while a block's allocation does not. Where the allocation is shorter,
the clip is trimmed. Where it is longer, the clip is slowed with setpts rather
than freeze-framed - a held frame in the middle of an interview reads as a
playback fault, a 5% slow does not.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

import graphics as G
import score
from clips import BY_ID as CLIP_META
from plan import ALIAS, B17_BACKING, MOVEMENTS, PLAN, STILLS, WEEK_ROWS
from script import BLOCKS

ROOT = Path(__file__).resolve().parent
PIECES = ROOT / "pieces"
WORK = ROOT / "work"
OUT = ROOT / "JENNIFER_ANISTON_V2.mp4"
for d in (PIECES, WORK, ROOT / "manifest"):
    d.mkdir(exist_ok=True)

FPS, W, H = 30, 1920, 1080
GAP = 0.55
SR = 48_000
MUSIC_DB = -21.0

# One grade over everything so 360p archive and 1080p graphics sit together.
ARCH_VF = ("scale=1920:1080:flags=lanczos,setsar=1,"
           "unsharp=5:5:0.55:5:5:0.0,"
           "eq=contrast=1.06:saturation=0.94:gamma=0.99,"
           "noise=alls=5:allf=t")


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{cmd[:6]}...\n{r.stderr[-900:]}")


def probe(p: Path, kind="v") -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", f"{kind}:0",
                        "-show_entries", "stream=duration", "-of", "default=nw=1:nk=1",
                        str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "default=nw=1:nk=1", str(p)],
                           capture_output=True, text=True)
        return float(r.stdout.strip())


def nframes(p: Path) -> int:
    return int(round(probe(p) * FPS))


# ─────────────────────────────────────────────────────────────── audio

def decode(p: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le",
                        "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2).copy()


def build_audio(man):
    print("  audio ...")
    edge = int(0.03 * SR)
    parts = []
    for i, b in enumerate(man["blocks"]):
        a = decode(ROOT / "audio" / b["file"])
        a[:edge] *= np.linspace(0, 1, edge)[:, None]
        a[-edge:] *= np.linspace(1, 0, edge)[:, None]
        parts.append(a)
        if i < len(man["blocks"]) - 1:
            parts.append(np.zeros((int(GAP * SR), 2), np.float32))
    vo = np.concatenate(parts)
    bed = score.build(len(vo) / SR)
    bed = bed[:len(vo)] if len(bed) >= len(vo) else np.pad(bed, ((0, len(vo) - len(bed)), (0, 0)))
    vp = float(np.max(np.abs(vo))) or 1.0
    bp = float(np.max(np.abs(bed))) or 1.0
    mix = vo + bed * (vp * 10 ** (MUSIC_DB / 20) / bp)
    m = float(np.max(np.abs(mix)))
    if m > 0.99:
        mix *= 0.99 / m
    raw = WORK / "mix.f32"
    raw.write_bytes(mix.astype(np.float32).tobytes())
    wav = WORK / "mix.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2",
        "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "pcm_s16le", str(wav)])
    print(f"    {len(mix)/SR:.3f}s")
    return wav


# ─────────────────────────────────────────────────────────── picture

def block_frames(man):
    bounds, t = [0.0], 0.0
    bl = man["blocks"]
    for i, b in enumerate(bl):
        t += b["seconds"] + (GAP if i < len(bl) - 1 else 0.0)
        bounds.append(t)
    q = [int(round(x * FPS)) for x in bounds]
    return [q[i + 1] - q[i] for i in range(len(bl))]


def allocate(weights, total):
    ws = sum(weights)
    raw = [total * w / ws for w in weights]
    got = [int(x) for x in raw]
    order = sorted(range(len(raw)), key=lambda i: raw[i] - got[i], reverse=True)
    for i in range(total - sum(got)):
        got[order[i % len(order)]] += 1
    return got


def arch_piece(vid, frames, out, credit_only=True, plate=None):
    src = ROOT / "clips" / f"{vid}.mp4"
    have = nframes(src)
    want = frames
    vf = ARCH_VF
    if want > have:                       # slow rather than freeze
        vf = f"setpts={want/have:.6f}*PTS," + vf
    ov = []
    inputs = ["-i", str(src)]
    filt = f"[0:v]{vf}[base]"
    cred = CLIP_META[vid][3]
    cp = WORK / f"cred_{vid}.png"
    if not cp.exists():
        G.credit_png(cred, cp)
    inputs += ["-i", str(cp)]
    filt += ";[base][1:v]overlay=0:0[c]"
    last = "[c]"
    if plate is not None:
        pp = WORK / f"plate_{plate[0]}.png"
        if not pp.exists():
            G.plate_png(*plate, pp)
        inputs += ["-i", str(pp)]
        filt += f";{last}[2:v]overlay=0:0[o]"
        last = "[o]"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt,
        "-map", last, "-frames:v", str(want), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out)])


def still_piece(sid, frames, out, push, plate=None):
    real = ALIAS.get(sid, sid)
    src = ROOT / "stills" / f"{real}.jpg"
    z = ("min(1.001+0.00040*on,1.13)" if push else "max(1.13-0.00040*on,1.001)")
    vf = (f"scale=3840:2160:flags=lanczos,zoompan=z='{z}':"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    inputs = ["-loop", "1", "-i", str(src)]
    filt = f"[0:v]{vf}[base]"
    last = "[base]"
    if plate is not None:
        pp = WORK / f"plate_{plate[0]}.png"
        if not pp.exists():
            G.plate_png(*plate, pp)
        inputs += ["-i", str(pp)]
        filt += ";[base][1:v]overlay=0:0[o]"
        last = "[o]"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt,
        "-map", last, "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out)])


CARDS = {
 "title":    lambda: G.title_card(["She stopped", "training", "like this"],
                                  "The routine everyone quotes is one she gave up in 2021."),
 "subscribe": G.subscribe,
 "stat57":   lambda: G.stat("57", "and training less than at 30", "Born 11 February 1969."),
 "ch1":      lambda: G.chapter("01", "Her Life"),
 "ch2":      lambda: G.chapter("02", "Workout Mindset"),
 "ch3":      lambda: G.chapter("03", "Workout Routine"),
 "ch4":      lambda: G.chapter("04", "Diet Plan"),
 "ch5":      lambda: G.chapter("05", "The Takeaway"),
 "stat236":  lambda: G.stat("236", "episodes of Friends", "Ten seasons, 1994 to 2004."),
 "ingber":   lambda: G.quote("Every yoga pose is paired with a toning move, so you are "
                             "never just holding a shape.", "the Yogalosophy method"),
 "boxquote": lambda: G.quote("It's the longest workout I've actually stayed with, "
                             "other than yoga.", "Jennifer Aniston, InStyle"),
 "stat37":   lambda: G.stat("3–7", "sessions a week", "45 minutes to an hour, for two decades."),
 "quote_access": lambda: G.quote("I need to do 45 minutes of cardio or I won't get a good "
                                 "workout — I believed it for so long. I just burnt out and "
                                 "broke my body.", "Jennifer Aniston, Access Hollywood"),
 "mechanism": G.mechanism,
 "week":     lambda: G.week(WEEK_ROWS),
 "stat15":   lambda: G.stat("15", "minutes", "Short enough that a bad day is not a reason."),
 "caution":  lambda: G.quote("If you are training around something that hurts, this is where "
                             "the celebrity comparison stops and a professional begins.",
                             "not medical advice"),
 "question": lambda: G.title_card(["An hour a day", "at thirty?", "Or fifteen minutes?"],
                                  "Tell me which one in the comments."),
 "end":      G.endcard,
}


def main():
    man = json.loads((ROOT / "manifest" / "audio.json").read_text(encoding="utf-8"))
    wav = build_audio(man)
    per = block_frames(man)

    order, rows, push = [], [], True
    print("  picture ...")
    for b, total in zip(man["blocks"], per):
        bid = b["block"]
        shots = PLAN[bid]
        alloc = allocate([s[2] for s in shots], total)
        for n, ((kind, key, _), fr) in enumerate(zip(shots, alloc)):
            tag = key if not isinstance(key, int) else f"mv{key}"
            out = PIECES / f"{bid}_{n:02d}_{kind}_{tag}.mp4"
            if not out.exists() or nframes(out) != fr:
                if kind == "arch":
                    arch_piece(key, fr, out)
                elif kind == "still":
                    still_piece(key, fr, out, push); push = not push
                elif kind == "card":
                    G.render_still_image(CARDS[key](), fr, out,
                                         drift=key not in ("week", "mechanism"))
                elif kind == "plate":
                    mv = MOVEMENTS[key]
                    bk, bid2 = B17_BACKING[key]
                    if bk == "arch":
                        arch_piece(bid2, fr, out, plate=(mv[0], mv[1], mv[2], mv[3]))
                    else:
                        still_piece(bid2, fr, out, push, plate=(mv[0], mv[1], mv[2], mv[3]))
                        push = not push
            got = nframes(out)
            if got != fr:
                raise SystemExit(f"{out.name}: {got} frames, wanted {fr}")
            order.append(out)
            rows.append(dict(block=bid, kind=kind, tag=str(tag), frames=fr))
        print(f"    {bid}  {len(shots):>2} shots  {total:>5} f  {total/FPS:6.2f}s"
              f"  (vo {b['seconds']:.2f}s)")

    (ROOT / "manifest" / "shots.json").write_text(
        json.dumps({"fps": FPS, "gap": GAP, "shots": rows}, indent=1), encoding="utf-8")

    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in order), encoding="utf-8")
    body = WORK / "body.mp4"
    print("  concat ...")
    sh(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", str(lst), "-c", "copy", str(body)])

    v, a = probe(body), probe(wav, "a")
    print(f"    video {v:.3f}s  audio {a:.3f}s  delta {abs(v-a):.3f}s")
    if abs(v - a) > 0.25:
        raise SystemExit("SYNC GATE FAILED")

    print("  mux ...")
    OUT.unlink(missing_ok=True)
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(body), "-i", str(wav),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(OUT)])
    d = probe(OUT)
    arch = sum(r["frames"] for r in rows if r["kind"] in ("arch",)) / FPS
    plate_arch = sum(r["frames"] for r in rows if r["kind"] == "plate") / FPS
    print(f"\n  {OUT.name}  {int(d)//60}:{d%60:05.2f}  {OUT.stat().st_size/1e6:.1f} MB"
          f"  {len(order)} shots")
    print(f"  archive on screen: {arch:.0f}s + {plate_arch:.0f}s demo = "
          f"{(arch+plate_arch)/d*100:.0f}% of runtime")


if __name__ == "__main__":
    main()
