"""Assemble v3. Audio is still the master clock; bites are their own clock.

Timing discipline is unchanged and not negotiable: cumulative boundaries are
quantised to whole frames, block durations are the differences of those
integers, each block's frames are divided among its shots, every piece is
checked frame-exact before the concat, and the mux refuses on >0.25s drift.

Three things are new.

BITES. A bite block's picture is the source at the same timecode its audio
came from, for the same number of frames. It is never trimmed to fit an
allocation and never slowed - either would slide her lips off her voice.

CROP. Archive is cropped before the upscale to push burned-in logos off frame.
v2 shipped with hulu, ET, GMA, Apple TV+, Variety, Vanity Fair, "Take2MarkTV
on YouTube" and a pink Us Weekly quote card visible in the final film, with
its own credit chip stacked on top of them.

ASPECT. Some sources are vertical phone video inside a 16:9 container. Cropping
those to fill would cut her head off, so anything narrower than 1.3:1 after its
crop is centred on black instead of stretched. Black is 70% of the brand, so a
pillarboxed shot reads as a decision rather than an accident.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

import graphics2 as G
import score
from clips2 import BY_KEY, crop_of
from plan2 import MOVES, PLAN, WEEK_ROWS
from script2 import BITE_PICTURE, BITES

ROOT = Path(__file__).resolve().parent
PIECES = ROOT / "pieces2"
WORK = ROOT / "work2"
HD = ROOT / "hd"
OUT = ROOT / "JENNIFER_ANISTON_V3.mp4"
for d in (PIECES, WORK, ROOT / "manifest"):
    d.mkdir(exist_ok=True)

FPS, W, H = 30, 1920, 1080
GAP = 0.55
SR = 48_000
MUSIC_DB = -21.0
MUSIC_DB_UNDER_BITE = -27.0      # duck the bed under her voice

GRADE = ("unsharp=5:5:0.45:5:5:0.0,"
         "eq=contrast=1.05:saturation=0.95:gamma=0.99,"
         "noise=alls=3:allf=t")


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{' '.join(str(c) for c in cmd[:8])}...\n{r.stderr[-1200:]}")


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


def source(vid: str) -> Path:
    """Full-length HD copy, or the old 360p one if YouTube will no longer
    serve it. Falling back is only safe for sources that were NOT pulled with
    --download-sections - those raw files start partway in, so every timecode
    against them is silently short by the window start."""
    hd = HD / f"{vid}.mp4"
    if hd.exists():
        return hd
    from clips2 import V2_WINDOW_START
    if vid in V2_WINDOW_START:
        raise SystemExit(f"{vid}: no HD copy and the raw one is windowed "
                         f"(+{V2_WINDOW_START[vid]}s) - timecodes would be wrong")
    raw = ROOT / "raw" / f"{vid}.mp4"
    if not raw.exists():
        raise SystemExit(f"{vid}: no copy in hd/ or raw/")
    return raw


def src_size(vid: str) -> tuple[int, int]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0",
                        str(source(vid))], capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def frame_vf(vid: str, t0: float | None = None) -> str:
    """Crop off the burned-in branding, then fit to frame without stretching."""
    l, rr, t, b = crop_of(vid, t0)
    sw, sh_ = src_size(vid)
    cw, ch = sw * (1 - l - rr), sh_ * (1 - t - b)
    crop = (f"crop=iw*{1-l-rr:.4f}:ih*{1-t-b:.4f}:iw*{l:.4f}:ih*{t:.4f}")
    if cw / ch < 1.30:                       # vertical: centre on black
        fit = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0D0D0D")
    else:                                    # cover and centre-crop
        fit = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
               f"crop={W}:{H}")
    return f"{crop},{fit},setsar=1,{GRADE}"


# ───────────────────────────────────────────────────────────────── audio

def decode(p: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le",
                        "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2).copy()


def build_audio(man):
    print("  audio ...")
    edge = int(0.03 * SR)
    parts, duck = [], []
    bl = man["blocks"]
    for i, b in enumerate(bl):
        a = decode(ROOT / "audio2" / b["file"])
        a[:edge] *= np.linspace(0, 1, edge)[:, None]
        a[-edge:] *= np.linspace(1, 0, edge)[:, None]
        parts.append(a)
        duck.append(np.full(len(a), b["kind"] == "bite"))
        if i < len(bl) - 1:
            parts.append(np.zeros((int(GAP * SR), 2), np.float32))
            duck.append(np.zeros(int(GAP * SR), bool))
    vo = np.concatenate(parts)
    is_bite = np.concatenate(duck)

    bed = score.build(len(vo) / SR)
    bed = bed[:len(vo)] if len(bed) >= len(vo) else np.pad(
        bed, ((0, len(vo) - len(bed)), (0, 0)))

    vp = float(np.max(np.abs(vo))) or 1.0
    bp = float(np.max(np.abs(bed))) or 1.0
    gain = np.where(is_bite, 10 ** (MUSIC_DB_UNDER_BITE / 20),
                    10 ** (MUSIC_DB / 20)).astype(np.float32)
    # Smooth the duck so it does not step. A box filter via cumsum is O(n);
    # np.convolve here is O(n*k) = 33M samples x 16.8k taps, which hangs.
    k = int(0.35 * SR) | 1
    pad = np.pad(gain, (k // 2, k // 2), mode="edge").astype(np.float64)
    c = np.cumsum(pad)
    gain = ((c[k:] - c[:-k]) / k).astype(np.float32)
    gain = np.resize(gain, len(vo))
    mix = vo + bed * (vp / bp) * gain[:, None]
    m = float(np.max(np.abs(mix)))
    if m > 0.99:
        mix *= 0.99 / m
    raw = WORK / "mix.f32"
    raw.write_bytes(mix.astype(np.float32).tobytes())
    wav = WORK / "mix.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2",
        "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
        "-c:a", "pcm_s16le", str(wav)])
    print(f"    {len(mix)/SR:.3f}s")
    return wav


# ─────────────────────────────────────────────────────────────── picture

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


def arch_piece(key, frames, out, move=None):
    vid, t0 = key
    credit = BY_KEY[key][3]
    have = BY_KEY[key][2]
    want = frames / FPS
    vf = frame_vf(vid, t0)
    if want > have + 0.05:                    # slow rather than freeze
        vf = f"setpts={want/have:.6f}*PTS," + vf
    cp = WORK / f"cred_{abs(hash(credit)) % 10**9}.png"
    if not cp.exists():
        G.credit_png(credit, cp)
    inputs = ["-ss", f"{t0:.3f}", "-i", str(source(vid)), "-i", str(cp)]
    filt = f"[0:v]{vf}[base];[base][1:v]overlay=0:0[c]"
    last = "[c]"
    if move is not None:
        i, name, cue = move
        # keyed on the TEXT, not the index: renaming a movement must
        # re-render its card, and index-keyed caching silently shipped two
        # stale names ("Slant Board Squat", "Side-Lying Leg Lift") after the
        # movements were renamed to match their footage.
        mp = WORK / f"move_{i}_{fingerprint(i, name, cue)}.png"
        if not mp.exists():
            G.move_png(i, name, cue, mp)
        inputs += ["-i", str(mp)]
        filt += f";{last}[2:v]overlay=0:0[o]"
        last = "[o]"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt,
        "-map", last, "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out)])


def bite_piece(key, frames, out):
    """Locked: the source at the timecode its audio came from. No trim, no slow.

    The exception is a VOICEOVER bite, where her voice was never in sync with
    the picture to begin with; those may point the picture elsewhere."""
    vid, t0, t1, credit, _ = BITES[key]
    if key in BITE_PICTURE:
        vid, t0 = BITE_PICTURE[key]
    cp = WORK / f"cred_{abs(hash(credit)) % 10**9}.png"
    if not cp.exists():
        G.credit_png(credit, cp)
    vf = frame_vf(vid, t0)
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
        "-i", str(source(vid)), "-i", str(cp),
        "-filter_complex", f"[0:v]{vf}[base];[base][1:v]overlay=0:0[o]",
        "-map", "[o]", "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out)])


def still_piece(sid, frames, out, push):
    src = ROOT / "stills" / f"{sid}.jpg"
    z = ("min(1.001+0.00040*on,1.13)" if push else "max(1.13-0.00040*on,1.001)")
    vf = (f"scale=3840:2160:flags=lanczos,zoompan=z='{z}':"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    sh(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(src), "-vf", vf,
        "-frames:v", str(frames), "-r", str(FPS), "-c:v", "libx264",
        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])


CARDS = {
 "title": lambda: G.title_card(["She stopped", "training", "like this"],
                               "The routine everyone quotes is one she gave up in 2021."),
 "subscribe": G.subscribe,
 "stat57": lambda: G.stat("57", "and training less than at 30", "Born 11 February 1969."),
 "ch_role":    lambda: G.chapter("01", "THE ROLE"),
 "ch_workout": lambda: G.chapter("02", "THE WORKOUT"),
 "ch_diet":    lambda: G.chapter("03", "THE DIET"),
 "ch_results": lambda: G.chapter("04", "THE RESULTS"),
 "stat236": lambda: G.stat("236", "episodes of Friends", "Ten seasons, 1994 to 2004."),
 "boxquote": lambda: G.quote(
     "It's the longest workout I've actually stayed with, other than yoga.",
     "Jennifer Aniston to InStyle"),
 "stat37": lambda: G.stat("3-7", "sessions a week", "45 minutes to an hour, for two decades."),
 "quote_instyle": lambda: G.quote(
     "I just burnt out and broke my body. My physical therapist gave me a Barbie "
     "doll covered in kinesio tape - every injury I've had in fifteen years.",
     "Jennifer Aniston to InStyle - read on air, not said on camera"),
 "week": lambda: G.week(WEEK_ROWS),
 "stat15": lambda: G.stat("15", "minutes", "Short enough that a bad day is not a reason."),
 "caution": lambda: G.quote(
     "If you are training around something that hurts, this is where the celebrity "
     "comparison stops and a professional begins.", "not medical advice"),
 "question": lambda: G.title_card(["An hour a day", "at thirty?", "Or fifteen minutes?"],
                                  "Tell me which one in the comments."),
 "end": G.endcard,
}

MOVE_BY_I = {m[0]: m for m in MOVES}


def fingerprint(*parts) -> str:
    """Cache key on CONTENT, never on position. A piece name like
    `B18_01_move_mv2` is positional: swap which clip backs move 2, or deepen a
    source's crop, and the name is unchanged while the render should not be.
    Both happened in this project - the crop pass changed 12 sources and every
    affected piece would have been served stale from the previous build."""
    h = hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()
    return h[:8]


def main():
    man = json.loads((ROOT / "manifest" / "audio2.json").read_text(encoding="utf-8"))
    wav = build_audio(man)
    per = block_frames(man)

    order, rows, push = [], [], True
    print("  picture ...")
    for b, total in zip(man["blocks"], per):
        bid = b["block"]

        if b["kind"] == "bite":
            fp = fingerprint("bite", b["bite"], BITES[b["bite"]],
                             BITE_PICTURE.get(b["bite"]),
                             crop_of(b["source"]), GRADE, total)
            out = PIECES / f"{bid}_00_bite_{b['bite']}_{fp}.mp4"
            if not out.exists() or nframes(out) != total:
                bite_piece(b["bite"], total, out)
            got = nframes(out)
            if got != total:
                raise SystemExit(f"{out.name}: {got} frames, wanted {total}")
            order.append(out)
            rows.append(dict(block=bid, kind="bite", tag=b["bite"], frames=total))
            print(f"    {bid}  BITE {b['bite']:<8} {total:>5} f  {total/FPS:6.2f}s")
            continue

        shots = PLAN[bid]
        alloc = allocate([s[2] for s in shots], total)
        for n, ((kind, key, _), fr) in enumerate(zip(shots, alloc)):
            if kind == "arch":
                tag = f"{key[0]}_{key[1]:.0f}"
                fp = fingerprint(kind, key, crop_of(*key), GRADE, fr)
            elif kind == "move":
                i, vid, t = key
                tag = f"mv{i}"
                fp = fingerprint(kind, key, MOVE_BY_I[i], crop_of(vid, t), GRADE, fr)
            elif kind == "still":
                tag = str(key)
                fp = fingerprint(kind, key, push, fr)
            else:
                tag = str(key)
                fp = fingerprint(kind, key, fr)
            out = PIECES / f"{bid}_{n:02d}_{kind}_{tag}_{fp}.mp4"
            if not out.exists() or nframes(out) != fr:
                if kind == "arch":
                    arch_piece(key, fr, out)
                elif kind == "move":
                    i, vid, t = key
                    arch_piece((vid, t), fr, out, move=MOVE_BY_I[i])
                elif kind == "still":
                    still_piece(key, fr, out, push); push = not push
                elif kind == "card":
                    G.render_still_image(CARDS[key](), fr, out,
                                         drift=key not in ("week",))
            got = nframes(out)
            if got != fr:
                raise SystemExit(f"{out.name}: {got} frames, wanted {fr}")
            order.append(out)
            rows.append(dict(block=bid, kind=kind, tag=tag, frames=fr))
        print(f"    {bid}  {len(shots):>2} shots  {total:>5} f  {total/FPS:6.2f}s")

    (ROOT / "manifest" / "shots2.json").write_text(
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
        "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
        "-shortest", str(OUT)])
    d = probe(OUT)
    train = sum(r["frames"] for r in rows
                if r["kind"] in ("arch", "move", "bite")) / FPS
    print(f"\n  {OUT.name}  {int(d)//60}:{d%60:05.2f}  "
          f"{OUT.stat().st_size/1e6:.1f} MB  {len(order)} shots")
    print(f"  real footage on screen: {train:.0f}s = {train/d*100:.0f}% of runtime")


if __name__ == "__main__":
    main()
