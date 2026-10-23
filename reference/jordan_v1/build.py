"""Script -> timing -> shots -> pieces -> film.

TIMING IS QUANTISED, NEVER DISTRIBUTED
--------------------------------------
`manifest/edl_full.json` is the only source of timing in this build. Never a
transcript: Whisper merges long pauses and drifts ten seconds or more over a
feature-length file.

Each EDL boundary becomes `round(t * FPS)` and every duration derives from those
integers, so the totals telescope exactly with no reconciliation step. The
tempting alternative - allocate one global frame pool and distribute the
rounding error - guarantees the TOTAL but pushes the error onto individual cuts,
and it lands on sync boundaries, where 1.35 frames is ~45ms of wrong picture
under the subject's own voice.

Integer frames, summed exactly. Never pad, never loop: a short piece is an
error, not something to stretch. Rounding across 130 shots once accumulated
3.8 seconds on this project and the "fix" inserted an 18-second frozen frame.

PIECES CACHE ON CONTENT, NOT POSITION
-------------------------------------
Every shot renders to its own file, keyed on a hash of everything that affects
its pixels - source, in-point, duration, crop, motion, filters. Change one shot
and exactly one piece re-renders. Shot NAMES are positional; a name-keyed cache
serves the stale render the moment a clip is swapped, which is the same species
of bug as the audio cache that served V5's soundtrack under V6's picture.

NEVER PILLARBOX
---------------
Padding a vertical or 4:3 source to black puts the picture in a narrow strip
with huge bars either side. The frame is filled with a blurred, zoomed copy of
the same image and the sharp version is laid on top. Most of this library is
4:3 archive, so this path is the norm here, not the exception.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import edit as E
import srcindex as SI
import voice as V

ROOT = Path(__file__).resolve().parent
HD = ROOT / "hd"
MAN = ROOT / "manifest"
PIECES = ROOT / "pieces"
WORK = ROOT / "work"
QC = ROOT / "qc"

FPS = 30
W, H = SI.OUT_W, SI.OUT_H

# The channel cuts fast: measured median shot 1.4s, 62% under two seconds, 323
# cuts in 12:22. REFERENCE_SPEC.md governs over docs/EDIT_RULES.md, which asks
# for 8-12s shots - "where the document and the channel disagree, the channel
# wins". These are the pool-shot lengths; a BITE is never chopped, it plays as
# one continuous shot for as long as the thought lasts.
SHOT_MIN, SHOT_MAX = 1.8, 3.4

for d in (PIECES, WORK, MAN, QC):
    d.mkdir(exist_ok=True)


# --------------------------------------------------------------------------
# script
# --------------------------------------------------------------------------
BLOCK_RE = re.compile(r"^###\s+(\S+)\s*\|\s*(.*)$")


def parse_script(p: Path) -> list[dict]:
    """One block per `###` header. Only kind=vo counts toward narration."""
    blocks: list[dict] = []
    cur: dict | None = None
    for line in p.read_text(encoding="utf-8").splitlines():
        m = BLOCK_RE.match(line)
        if m:
            if cur:
                blocks.append(cur)
            attrs = dict(kv.split("=", 1) for kv in
                         (a.strip() for a in m.group(2).split("|")) if "=" in kv)
            cur = {"id": m.group(1), "text": "", **attrs}
        elif cur is not None:
            cur["text"] += line + "\n"
    if cur:
        blocks.append(cur)
    for b in blocks:
        b["text"] = b["text"].strip()
        b.setdefault("kind", "vo")
        b.setdefault("section", "body")
    return blocks


# --------------------------------------------------------------------------
# audio per block
# --------------------------------------------------------------------------
def cut_bite_audio(q: dict, dest: Path) -> Path:
    """A bite's audio is its OWN audio, cut from its own source."""
    src = HD / f"{q['src']}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{q['t0']:.3f}",
                    "-t", f"{q['t1'] - q['t0']:.3f}", "-i", str(src),
                    "-vn", "-ac", "2", "-ar", str(V.SR), "-c:a", "pcm_s16le",
                    str(dest), "-y"], capture_output=True)
    return dest


def block_audio(b: dict, quotes: dict, final: bool) -> Path:
    if b["kind"] == "bite":
        q = quotes[b["quote"]]
        dest = WORK / f"bite_{b['quote']}.wav"
        if not dest.exists():
            cut_bite_audio(q, dest)
        return dest
    return V.render_block(b["text"], final=final)


# --------------------------------------------------------------------------
# EDL
# --------------------------------------------------------------------------
def build_edl(blocks: list[dict], quotes: dict, final: bool = False,
              gap: float = 0.32) -> dict:
    """Block timings, quantised to whole frames.

    `gap` is a real silence after each thought. A build with narration covering
    92% of runtime and ZERO pauses is exhausting and no frame-based check can
    see it, so the pause is structural rather than something to remember.
    """
    rows, f = [], 0
    for i, b in enumerate(blocks):
        a = block_audio(b, quotes, final)
        dur = V.duration(a)
        if dur <= 0.05:
            raise RuntimeError(f"block {b['id']} produced no audio")
        nf = round(dur * FPS)
        pause = 0 if i == len(blocks) - 1 else round(gap * FPS)
        rows.append({"id": b["id"], "kind": b["kind"], "section": b["section"],
                     "quote": b.get("quote"), "audio": str(a),
                     "f0": f, "nf": nf, "pause": pause,
                     "t0": round(f / FPS, 3), "dur": round(nf / FPS, 3)})
        f += nf + pause
    edl = {"fps": FPS, "w": W, "h": H, "frames": f,
           "seconds": round(f / FPS, 3), "blocks": rows}
    (MAN / "edl_full.json").write_text(json.dumps(edl, indent=1),
                                       encoding="utf-8")
    return edl


# --------------------------------------------------------------------------
# shots
# --------------------------------------------------------------------------
def plan_shots(edl: dict, blocks: list[dict], quotes: dict,
               pools: dict) -> list[dict]:
    """Every shot in the film, in order.

    A BITE is one shot: its own source, at its own in-point, for its own
    length. `src_t0` comes from the EDL's bite in-point and never from a scan
    window's t0 - `bite_windows` style scanning widens by 1.5s and nudges edges,
    so a run's t0 is the in-point minus 1.25s by construction. That put over a
    second of wrong picture under his voice on all 17 sync shots of the previous
    build, and it passed every check that only asked whether the field was
    present and positive.
    """
    shots: list[dict] = []
    bite_srcs = E.bite_sources(quotes)
    prev_src: str | None = None

    for i, row in enumerate(edl["blocks"]):
        want = row["dur"] + row["pause"] / FPS

        if row["kind"] == "bite":
            q = quotes[row["quote"]]
            shots.append({"block": row["id"], "kind": "bite",
                          "src": q["src"], "src_t0": float(q["t0"]),
                          "f0": row["f0"], "nf": row["nf"] + row["pause"],
                          "cue": None})
            prev_src = q["src"]
            continue

        # one block of lookahead, so the last pool shot before a bite is never
        # that bite's own source
        nxt = edl["blocks"][i + 1] if i + 1 < len(edl["blocks"]) else None
        look = (quotes[nxt["quote"]]["src"]
                if nxt and nxt["kind"] == "bite" else None)

        pool = pools[row["section"]]
        remaining = row["nf"] + row["pause"]
        while remaining > 0:
            take = min(remaining, round(SHOT_MAX * FPS))
            if remaining - take < round(SHOT_MIN * FPS):
                take = remaining
            got = pool.take(take / FPS, avoid={prev_src} | bite_srcs,
                            need_subject=False, lookahead_src=look)
            if got is None:
                # never loop a used window to fill time - extend the last shot
                if shots and shots[-1]["block"] == row["id"]:
                    shots[-1]["nf"] += remaining
                    remaining = 0
                    break
                raise RuntimeError(f"pool '{row['section']}' exhausted at "
                                   f"block {row['id']}")
            vid, t, clear = got
            nf = min(take, max(round(clear * FPS), round(SHOT_MIN * FPS)))
            nf = min(nf, remaining)
            shots.append({"block": row["id"], "kind": "pool", "src": vid,
                          "src_t0": t, "f0": None, "nf": nf, "cue": None})
            prev_src = vid
            remaining -= nf

    # assign absolute frame positions by summing exactly
    f = 0
    for s in shots:
        s["f0"] = f
        f += s["nf"]
    if f != edl["frames"]:
        raise RuntimeError(f"shot frames {f} != edl frames {edl['frames']}")
    (MAN / "shots.json").write_text(json.dumps(shots, indent=1), encoding="utf-8")
    return shots


# --------------------------------------------------------------------------
# pieces
# --------------------------------------------------------------------------
def piece_key(s: dict) -> str:
    c = SI._crop.get(s["src"], {})
    sig = (f"{s['src']}|{s['src_t0']:.3f}|{s['nf']}|{FPS}|{W}x{H}|"
           f"{c.get('x')},{c.get('y')},{c.get('w')},{c.get('h')}|v3")
    return hashlib.sha256(sig.encode()).hexdigest()[:20]


def render_piece(s: dict) -> Path:
    """One shot -> one file. Fills the frame; never pillarboxes."""
    dest = PIECES / f"{piece_key(s)}.mp4"
    if dest.exists() and dest.stat().st_size > 4096:
        return dest
    src = HD / f"{s['src']}.mp4"
    dur = s["nf"] / FPS
    cf = SI.crop_filter(s["src"])
    pre = f"{cf}," if cf else ""

    # blurred zoomed copy behind, sharp copy on top - the archive is 4:3 and
    # padding it to black would put the picture in a narrow strip
    vf = (f"[0:v]{pre}scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},boxblur=28:2,eq=brightness=-0.06[bg];"
          f"[0:v]{pre}scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
          f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
          f"scale={W}:{H},setsar=1,fps={FPS},format=yuv420p")

    # A timeout, because one ffmpeg call hung indefinitely on a seek into a
    # damaged region and stalled a whole build with no output at all - the
    # piece it left behind was 48 bytes. subprocess.run without a timeout turns
    # one bad frame into an unbounded wait.
    try:
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{s['src_t0']:.3f}",
             "-t", f"{dur:.3f}",
             "-i", str(src), "-filter_complex", vf, "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-frames:v", str(s["nf"]), str(dest), "-y"],
            capture_output=True, text=True, timeout=180)
        err = r.stderr[-300:]
    except subprocess.TimeoutExpired:
        err = "ffmpeg timed out after 180s"
    if not dest.exists() or dest.stat().st_size <= 4096:
        dest.unlink(missing_ok=True)          # never leave a truncated piece
        raise RuntimeError(f"piece failed {s['src']}@{s['src_t0']}: {err}")
    return dest


def purge_truncated(min_bytes: int = 5120) -> int:
    """Delete part-written pieces before they poison the NEXT build.

    On the previous project a 48-byte truncated piece survived in the cache and
    crashed `probe()` on the following build - not the one that produced it,
    which made it look like an unrelated regression. One appeared in this cache
    too. A piece that small cannot be a valid clip, so it is removed rather than
    trusted; the content hash means it simply re-renders.
    """
    n = 0
    for p in PIECES.glob("*.mp4"):
        try:
            if p.stat().st_size < min_bytes:
                p.unlink()
                n += 1
        except OSError:
            pass
    return n


def render_photo(src: Path, nf: int, variant: int = 0) -> Path:
    """A photograph as a full-frame shot with a slow move.

    The same picture can be cued more than once - there are only so many
    photographs of Jordan at fifteen - so the move VARIES by use index. Two
    identical stills back to back read as a stuck frame; the same still pushing
    in one time and drifting the other reads as two shots.

    Never pillarboxed: portrait and 4:3 scans fill the frame against a blurred,
    zoomed copy of themselves.
    """
    key = hashlib.sha256(
        f"photo|{src.name}|{nf}|{variant}|{W}x{H}|v2".encode()).hexdigest()[:20]
    dest = PIECES / f"{key}.mp4"
    if dest.exists() and dest.stat().st_size > 4096:
        return dest

    # four distinct moves, chosen by use index
    moves = [
        "z='min(zoom+0.0011,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        "z='if(lte(zoom,1.0),1.20,max(1.001,zoom-0.0011))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        "z='min(zoom+0.0009,1.16)':x='(iw-iw/zoom)*(on/{n})':y='ih/2-(ih/zoom/2)'".format(n=max(nf - 1, 1)),
        "z='min(zoom+0.0009,1.16)':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(on/{n})'".format(n=max(nf - 1, 1)),
    ]
    mv = moves[variant % len(moves)]
    vf = (
        f"[0:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop={W*2}:{H*2},boxblur=42:2,eq=brightness=-0.10,"
        f"scale={W}:{H}[bg];"
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
        f"zoompan={mv}:d={nf}:s={W}x{H}:fps={FPS},"
        f"setsar=1,format=yuv420p"
    )
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-loop", "1", "-i", str(src),
         "-filter_complex", vf, "-frames:v", str(nf),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
         "-pix_fmt", "yuv420p", "-r", str(FPS), str(dest), "-y"],
        capture_output=True, text=True, timeout=180)
    if not dest.exists() or dest.stat().st_size <= 4096:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"photo piece failed {src.name}: {r.stderr[-300:]}")
    return dest


def probe_frames(p: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-count_frames", "-show_entries", "stream=nb_read_frames",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split(",")[0])
    except Exception:
        return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("build.py is a library; run make_film.py")
