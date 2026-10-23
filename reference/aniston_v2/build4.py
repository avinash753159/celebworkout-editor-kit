"""Assemble v4 — fast-cut, to the channel's measured rhythm.

The one change that matters: the reference cuts every 2.3s (median shot 1.4s,
62% under two seconds). V3 cut every 8.2s with nothing under four. This
assembler carves each narration block into 1.1-2.6s shots drawn round-robin
from that section's reel pool, so the picture changes three to five times per
sentence instead of once per paragraph.

Timing discipline is unchanged and still not negotiable: cumulative narration
boundaries are quantised to whole frames, block durations are the differences
of those integers, shot lengths inside a block are integers summing exactly to
the block, every piece is verified frame-exact, and the mux refuses on more
than 0.25s of drift.

Sync bites are the exception to the fast cutting: they play as one locked shot
at the timecode their audio came from. Never cut inside a bite - the reference
holds on the speaker too, and cutting would slide her lips off her voice.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

import graphics4 as G
import score
from clips2 import crop_of
from reels4 import FOOD_BY_CAT, FOOD_STILLS, PLACE_LABEL, POOLS
from script4 import BITE_PICTURE, BITES, BLOCKS, FOODS, WEEK

ROOT = Path(__file__).resolve().parent
PIECES = ROOT / "pieces4"
WORK = ROOT / "work4"
HD = ROOT / "hd"
OUT = ROOT / "JENNIFER_ANISTON_V4.mp4"
for d in (PIECES, WORK, ROOT / "manifest"):
    d.mkdir(exist_ok=True)

FPS, W, H = 30, 1920, 1080
GAP = 0.28              # the reference barely breathes between paragraphs
SR = 48_000
MUSIC_DB = -20.0
MUSIC_DB_UNDER_BITE = -26.0

GRADE = ("unsharp=5:5:0.45:5:5:0.0,"
         "eq=contrast=1.05:saturation=0.97:gamma=0.99")

# Shot lengths cycle through this so the rhythm is fast but not metronomic.
# Median 1.6s, matching the reference's 1.4-1.9s.
SHOT_CYCLE = [1.5, 1.2, 2.0, 1.4, 2.6, 1.3, 1.8, 1.1, 2.2, 1.6]
MIN_SHOT = 0.9


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{' '.join(str(c) for c in cmd[:9])}\n{r.stderr[-1000:]}")


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


def fingerprint(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:8]


_SIZE: dict[str, tuple[int, int]] = {}


def src_size(vid: str) -> tuple[int, int]:
    if vid not in _SIZE:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0",
                            str(source(vid))], capture_output=True, text=True)
        w, h = r.stdout.strip().split(",")[:2]
        _SIZE[vid] = (int(w), int(h))
    return _SIZE[vid]


def source(vid: str) -> Path:
    hd = HD / f"{vid}.mp4"
    if hd.exists():
        return hd
    raw = ROOT / "raw" / f"{vid}.mp4"
    if not raw.exists():
        raise SystemExit(f"{vid}: no copy in hd/ or raw/")
    return raw


ACTIVE = json.loads((ROOT / "manifest" / "active_box.json").read_text()) \
    if (ROOT / "manifest" / "active_box.json").exists() else {}


def frame_vf(vid: str, t0: float | None = None) -> str:
    """Crop to the ACTIVE picture first, then apply the editorial crop inside
    it, then fit. Four sources - the Pvolve campaign films among them - are
    pillarboxed inside a 1920x1080 container, so a crop expressed as a
    fraction of the container kept their black bars and then cover-cropped the
    bars along with the picture. Detected boxes live in manifest/active_box.json."""
    l, rr, t, b = crop_of(vid, t0)
    sw, sh_ = src_size(vid)
    aw, ah, ax, ay = ACTIVE.get(vid, (sw, sh_, 0, 0))
    cw, ch = aw * (1 - l - rr), ah * (1 - t - b)
    cx, cy = ax + aw * l, ay + ah * t
    crop = f"crop={int(cw)}:{int(ch)}:{int(cx)}:{int(cy)}"
    if cw / ch < 1.30:
        fit = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0D0D0D")
    else:
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
        a = decode(ROOT / "audio4" / b["file"])
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
    k = int(0.35 * SR) | 1
    pad = np.pad(gain, (k // 2, k // 2), mode="edge").astype(np.float64)
    c = np.cumsum(pad)
    gain = np.resize(((c[k:] - c[:-k]) / k).astype(np.float32), len(vo))
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


def carve(total_frames: int, phase: int) -> list[int]:
    """Split a block into fast shots whose integer frame counts sum EXACTLY to
    the block. Never pad, never leave a remainder on the floor."""
    out, left, i = [], total_frames, phase
    while left > 0:
        want = int(round(SHOT_CYCLE[i % len(SHOT_CYCLE)] * FPS))
        i += 1
        if left - want < int(MIN_SHOT * FPS):      # absorb the tail
            out.append(left)
            break
        out.append(want)
        left -= want
    return out


LUMA = json.loads((ROOT / "manifest" / "luma.json").read_text())     if (ROOT / "manifest" / "luma.json").exists() else {}
LUMA_STEP = 1.5
DARK = 26.0


def too_dark(vid: str, t0: float, secs: float) -> bool:
    """True if this window is mostly dead frames. A post-build scan found 16
    shots under luma 26 - the amber silhouette stretch of one campaign film,
    walked into repeatedly by two reel start points. Checking here makes the
    whole class impossible instead of patching each instance."""
    track = LUMA.get(vid)
    if not track:
        return False
    a = int(t0 / LUMA_STEP)
    b = max(a + 1, int((t0 + secs) / LUMA_STEP))
    win = [x for x in track[a:b + 1] if x >= 0]
    if not win:
        return False
    # MIN, not mean. A window straddling a black frame (6.3) and a bright one
    # (47.4) averages to 26.9 and slipped past a mean test - but the viewer
    # still sees the black flash. Any dead sample condemns the window.
    return min(win) < 20.0 or sum(win) / len(win) < DARK


class Reels:
    """Round-robin over a section's reels, advancing each reel's playhead so
    successive shots off one source are successive moments."""

    def __init__(self, pool):
        self.pool = list(pool)
        self.head = {r: r[1] for r in self.pool}
        self.i = 0

    def next(self, secs: float):
        from reels4 import DUR
        for _ in range(len(self.pool)):
            r = self.pool[self.i % len(self.pool)]
            self.i += 1
            if r[0].startswith(("still:", "split:")):
                return r[0], 0.0          # synthetic: no playhead to advance
            t = self.head[r]
            if t + secs + 0.4 < DUR.get(r[0], 0):
                self.head[r] = t + secs
                if too_dark(r[0], t, secs):
                    continue                       # skip a dead window
                return r[0], t
            self.head[r] = r[1]                    # rewind this reel
        r = self.pool[0]
        return r[0], r[1]


def clip_piece(vid, t0, frames, out, overlay: Path | None = None):
    vf = frame_vf(vid, None)
    inputs = ["-ss", f"{t0:.3f}", "-i", str(source(vid))]
    filt = f"[0:v]{vf}[b]"
    last = "[b]"
    if overlay is not None:
        inputs += ["-i", str(overlay)]
        filt += f";{last}[1:v]overlay=0:0[o]"
        last = "[o]"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt,
        "-map", last, "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-pix_fmt", "yuv420p", str(out)])


def still_piece(path: Path, frames, out, push: bool, overlay: Path | None = None):
    z = ("min(1.001+0.00055*on,1.16)" if push else "max(1.16-0.00055*on,1.001)")
    vf = (f"scale=3200:1800:flags=lanczos,zoompan=z='{z}':"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    inputs = ["-loop", "1", "-i", str(path)]
    filt = f"[0:v]{vf}[b]"
    last = "[b]"
    if overlay is not None:
        inputs += ["-i", str(overlay)]
        filt += f";{last}[1:v]overlay=0:0[o]"
        last = "[o]"
    sh(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt,
        "-map", last, "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-pix_fmt", "yuv420p", str(out)])


def synthetic_piece(spec: str, frames: int, out: Path, push: bool):
    """A generated establishing still (with an optional place label) or a
    side-by-side comparison. These are what give the biography the texture the
    reference has and V4 lacked."""
    if spec.startswith("split:"):
        a, b, la, lb = spec[len("split:"):].split("|")
        G.split_piece(_still_path(a), _still_path(b), la, lb, frames, out)
        return
    name = spec[len("still:"):]
    ov = None
    if name in PLACE_LABEL:
        pl, sub = PLACE_LABEL[name]
        ov = WORK / f"place_{fingerprint(pl, sub)}.png"
        if not ov.exists():
            G.place_png(pl, sub, ov)
    still_piece(_still_path(name), frames, out, push, overlay=ov)


def _still_path(name: str) -> Path:
    for d in ("stills_place", "stills_food", "stills"):
        p = ROOT / d / f"{name}.jpg"
        if p.exists():
            return p
    raise SystemExit(f"still not found: {name}")


def bite_piece(key, frames, out):
    vid, t0, t1, credit, _ = BITES[key]
    if key in BITE_PICTURE:
        vid, t0 = BITE_PICTURE[key]
    cp = WORK / f"cred_{fingerprint(credit)}.png"
    if not cp.exists():
        G.credit_png(credit, cp)
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
        "-i", str(source(vid)), "-i", str(cp),
        "-filter_complex", f"[0:v]{frame_vf(vid, None)}[b];[b][1:v]overlay=0:0[o]",
        "-map", "[o]", "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-pix_fmt", "yuv420p", str(out)])


# section lookup for every speech block
SECTION = {}
for _it in BLOCKS:
    if _it[0] == "VO":
        SECTION[_it[1]] = _it[2]
WEEK_BY_ID = {f"WK_{d}": (d, lab, dur, mv) for d, lab, dur, mv in WEEK}
FOOD_BY_ID = {f"FD_{c.replace(' ', '_')}": (c, items) for c, items in FOODS}


def main():
    man = json.loads((ROOT / "manifest" / "audio4.json").read_text(encoding="utf-8"))
    wav = build_audio(man)
    per = block_frames(man)

    order, rows = [], []
    push = True
    phase = 0
    print("  picture ...")

    for b, total in zip(man["blocks"], per):
        bid = b["block"]

        # ── her voice: one locked shot, no cutting
        if b["kind"] == "bite":
            _bv = BITE_PICTURE.get(b["bite"], (BITES[b["bite"]][0], None))[0]
            fp = fingerprint("bite", b["bite"], BITES[b["bite"]],
                             BITE_PICTURE.get(b["bite"]), frame_vf(_bv),
                             GRADE, total)
            out = PIECES / f"{bid}_00_bite_{b['bite']}_{fp}.mp4"
            if not out.exists() or nframes(out) != total:
                bite_piece(b["bite"], total, out)
            if nframes(out) != total:
                raise SystemExit(f"{out.name}: {nframes(out)} != {total}")
            order.append(out)
            rows.append(dict(block=bid, kind="bite", tag=b["bite"], frames=total))
            print(f"    {bid:<13} BITE  {total/FPS:5.2f}s   1 shot")
            continue

        # ── the week: day marker, then a wedge per exercise
        if bid in WEEK_BY_ID:
            day, label, dur, moves = WEEK_BY_ID[bid]
            reels = Reels(POOLS["week"])
            segs = []
            if moves:
                head = int(total * 0.26)
                segs.append((head, G.day_png(day, label,
                             WORK / f"day_{fingerprint(day, label)}.png")))
                rest = total - head
                each = rest // len(moves)
                for j, (name, reps) in enumerate(moves):
                    n = each if j < len(moves) - 1 else rest - each * (len(moves) - 1)
                    segs.append((n, G.exercise_png(
                        name, reps, WORK / f"ex_{fingerprint(name, reps)}.png")))
            else:
                segs.append((total, G.day_png(day, label,
                             WORK / f"day_{fingerprint(day, label)}.png")))
            n_shots = 0
            for si, (seg_frames, ov) in enumerate(segs):
                for k, fr in enumerate(carve(seg_frames, phase)):
                    phase += 1
                    vid, t0 = reels.next(fr / FPS)
                    if vid.startswith(("still:", "split:")):
                        continue_vid = _still_path(vid[len("still:"):])
                        fp = fingerprint(vid, fr, ov.name, GRADE)
                        out = PIECES / f"{bid}_{si:02d}{k:02d}_wk_{fp}.mp4"
                        if not out.exists() or nframes(out) != fr:
                            still_piece(continue_vid, fr, out, True, overlay=ov)
                    else:
                        fp = fingerprint(vid, round(t0, 2), fr, ov.name,
                                         frame_vf(vid), GRADE)
                        out = PIECES / f"{bid}_{si:02d}{k:02d}_wk_{fp}.mp4"
                        if not out.exists() or nframes(out) != fr:
                            clip_piece(vid, t0, fr, out, overlay=ov)
                    if nframes(out) != fr:
                        raise SystemExit(f"{out.name}: {nframes(out)} != {fr}")
                    order.append(out)
                    rows.append(dict(block=bid, kind="week", tag=vid, frames=fr))
                    n_shots += 1
            print(f"    {bid:<13} {total/FPS:5.2f}s  {n_shots:>3} shots  ({len(moves)} moves)")
            continue

        # ── the food lists: list overlay building over food stills
        if bid in FOOD_BY_ID:
            cat, items = FOOD_BY_ID[bid]
            pics = FOOD_BY_CAT.get(cat, FOOD_STILLS)
            cuts = carve(total, phase)
            n_shots = 0
            for k, fr in enumerate(cuts):
                phase += 1
                reveal = max(1, int(round((k + 1) / len(cuts) * len(items))))
                ov = WORK / f"fd_{fingerprint(cat, tuple(items), reveal)}.png"
                if not ov.exists():
                    G.food_png(cat, items, ov, reveal=reveal)
                still = ROOT / "stills_food" / f"{pics[k % len(pics)]}.jpg"
                fp = fingerprint(still.name, fr, ov.name, push)
                out = PIECES / f"{bid}_{k:02d}_fd_{fp}.mp4"
                if not out.exists() or nframes(out) != fr:
                    still_piece(still, fr, out, push, overlay=ov)
                    push = not push
                if nframes(out) != fr:
                    raise SystemExit(f"{out.name}: {nframes(out)} != {fr}")
                order.append(out)
                rows.append(dict(block=bid, kind="food", tag=cat, frames=fr))
                n_shots += 1
            print(f"    {bid:<13} {total/FPS:5.2f}s  {n_shots:>3} shots  (list)")
            continue

        # ── everything else: straight fast montage off the section pool
        sec = SECTION.get(bid, "life")
        reels = Reels(POOLS.get(sec, POOLS["life"]))
        n_shots = 0
        for k, fr in enumerate(carve(total, phase)):
            phase += 1
            vid, t0 = reels.next(fr / FPS)
            synth = vid.startswith(("still:", "split:"))
            fp = fingerprint(vid, round(t0, 2), fr,
                             "synthetic" if synth else frame_vf(vid), GRADE, push)
            out = PIECES / f"{bid}_{k:02d}_{sec[:4]}_{fp}.mp4"
            if not out.exists() or nframes(out) != fr:
                if synth:
                    synthetic_piece(vid, fr, out, push)
                    push = not push
                else:
                    clip_piece(vid, t0, fr, out)
            if nframes(out) != fr:
                raise SystemExit(f"{out.name}: {nframes(out)} != {fr}")
            order.append(out)
            rows.append(dict(block=bid, kind=sec, tag=vid, frames=fr))
            n_shots += 1
        print(f"    {bid:<13} {total/FPS:5.2f}s  {n_shots:>3} shots  [{sec}]")

    (ROOT / "manifest" / "shots4.json").write_text(
        json.dumps({"fps": FPS, "gap": GAP, "shots": rows}, indent=1), encoding="utf-8")

    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in order), encoding="utf-8")
    body = WORK / "body.mp4"
    print(f"  concat {len(order)} shots ...")
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
    import statistics
    lens = sorted(r["frames"] / FPS for r in rows)
    print(f"\n  {OUT.name}  {int(d)//60}:{d%60:05.2f}  "
          f"{OUT.stat().st_size/1e6:.1f} MB  {len(order)} shots")
    print(f"  median shot {statistics.median(lens):.2f}s   "
          f"cut every {d/len(order):.2f}s   "
          f"(reference: 1.4s / 2.3s)")


if __name__ == "__main__":
    main()
