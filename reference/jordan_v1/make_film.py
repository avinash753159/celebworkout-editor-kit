"""Assemble the film: script -> EDL -> shots -> pieces -> mux.

Order of operations matters and is not arbitrary:

1. Audio first, because timing comes from it. `edl_full.json` is written here
   and is the ONLY source of timing downstream.
2. Shots planned against the EDL's integer frames, so the totals telescope.
3. Pieces rendered and each one's frame count VERIFIED against what was asked
   for. A short piece is an error, never something to pad or loop.
4. Video concatenated by stream copy - the pieces are already encoded and
   re-encoding them would be both slow and lossy.
5. Muxed with a hard sync gate. Never `-shortest`: it silently clipped six
   seconds of endcard on the previous build.

Cards are full-frame: the picture cuts away, the data owns the screen, then it
cuts back. They are placed by BLOCK ID rather than by timecode, so editing the
script moves them automatically instead of stranding them.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import build as B
import edit as E
import infographics as G
import music as M
import cues as CU
import pools as P
import voice as V

ROOT = Path(__file__).resolve().parent
MAN = ROOT / "manifest"
WORK = ROOT / "work"
QC = ROOT / "qc"
OUT = ROOT / "MICHAEL_JORDAN_V1.mp4"

FPS = B.FPS
CARD_SECONDS = 3.4

# Which card sits in which block. Keyed on block id, so a script edit moves the
# card with the words instead of leaving it at a stale timecode.
# Which HyperFrames card sits in which block. Keyed on block id, so a script
# edit moves the card with the words instead of stranding it at a timecode.
CARD_BLOCKS: dict[str, str] = {
    "H2":  "c_record",      # 1988 / 1989 / 1990, struck through
    "H3":  "c_concept",     # THE JORDAN RULES
    "T1":  "c_event",       # 1989 on a timeline
    "T3b": "c_counter",     # 30 DAYS -> 15 YEARS
    "T5":  "c_gauge",       # +15 LB, counting up
    "W1":  "c_clock",       # 5-7 AM arc
    "W3":  "c_checklist",   # the eight lifts
    "W4":  "c_versus",      # asked for 6, did 12
    "R6":  "c_transform",   # skinny 1987 | built 1997
    "D2":  "c_split",       # CARBS / STEAK
    "D3":  "c_clockface",   # 4 HOURS to tip-off
    "S2":  "c_bracket",     # swept Detroit 4-0
    "S3":  "c_bignumber",   # 38
}

HF_RENDERS = ROOT / "hf" / "cards" / "renders"


def render_cards() -> dict[str, Path]:
    """The 12 cards, as HyperFrames MP4s.

    These replace the previous static PNGs entirely. The owner's note was
    "the cards that you're using are complete crap ... each info card needs to
    be different looking than the other info cards", with an explicit
    instruction to use HyperFrames. Each card is an HTML composition rendered
    to video, so the data animates: the strike draws, the gauge fills, the
    clock arc sweeps, the number counts, the two photographs wipe.

    Refuses to proceed on a missing render rather than silently dropping a
    card - a missing card would just look like a gap in the film.
    """
    out: dict[str, Path] = {}
    missing = []
    for block, cid in CARD_BLOCKS.items():
        p = HF_RENDERS / f"{cid}.mp4"
        if p.exists() and p.stat().st_size > 20000:
            out[block] = p
        else:
            missing.append(cid)
    if missing:
        raise SystemExit(f"card renders missing: {missing}. "
                         f"Run hf/cards/render_all.py")
    kinds = list(out.values())
    if len({k.name for k in kinds}) != len(kinds):
        raise SystemExit("two blocks share one card layout")
    return out


def trim_card(src: Path, nf: int) -> Path:
    """Cut a rendered card to exactly nf frames.

    HyperFrames renders each card at a fixed 3.6s; the block it sits in decides
    how long it actually plays. Trimming re-encodes rather than stream-copies
    because a copy can only cut on a keyframe, which would silently hand back
    the wrong frame count - and a piece whose length is not exactly nf breaks
    the frame budget for everything after it.
    """
    # Keyed on the CONTENT of the rendered card, not its name. Keying on
    # `c_transform` alone served the previous render of that card after its
    # photographs and labels had been replaced - the film still read
    # "1987 - 195 LB" over the old picture. Every stale-cache failure on this
    # project has been a key that was a name or a position.
    st = src.stat()
    sig = f"{src.name}|{st.st_size}|{int(st.st_mtime)}|{nf}|{FPS}"
    key = __import__("hashlib").sha256(sig.encode()).hexdigest()[:16]
    dest = B.PIECES / f"hfcard_{key}.mp4"
    if dest.exists() and dest.stat().st_size > 4096:
        return dest
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(src), "-frames:v", str(nf),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", str(dest), "-y"],
        capture_output=True, timeout=180)
    if not dest.exists() or dest.stat().st_size <= 4096:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"card trim failed: {src.name}")
    return dest


def plan(edl: dict, blocks: list[dict], quotes: dict,
         card_png: dict[str, Path]) -> list[dict]:
    """Shots for the whole film, cards included, frames summing exactly."""
    E.reset_used()
    cue_map = CU.resolved()
    cue_use: dict[str, int] = {}
    srcs = P.section_pool("any")
    sections = {b["section"] for b in blocks}
    pl = {s: E.Pool(srcs, seed=17) for s in sections}
    bite_srcs = E.bite_sources(quotes)
    shots: list[dict] = []
    prev: str | None = None

    for i, row in enumerate(edl["blocks"]):
        total = row["nf"] + row["pause"]

        if row["kind"] == "bite":
            q = quotes[row["quote"]]
            shots.append({"block": row["id"], "kind": "bite", "src": q["src"],
                          "src_t0": float(q["t0"]), "nf": total, "f0": None})
            prev = q["src"]
            continue

        nxt = edl["blocks"][i + 1] if i + 1 < len(edl["blocks"]) else None
        look = (quotes[nxt["quote"]]["src"]
                if nxt and nxt["kind"] == "bite" else None)
        remaining = total

        # a full-frame card takes the front of its block
        if row["id"] in card_png and remaining > round(1.6 * FPS):
            nf = min(round(CARD_SECONDS * FPS), remaining - round(0.8 * FPS))
            shots.append({"block": row["id"], "kind": "card",
                          "src": str(card_png[row["id"]]), "src_t0": 0.0,
                          "nf": nf, "f0": None})
            remaining -= nf

        # CUES: a picture pinned to the words. These come before pool filler,
        # because the whole point is that the named person appears WHILE the
        # narration names them, not whenever the pool happens to allow it.
        for photo in cue_map.get(row["id"], []):
            if remaining < round(2.0 * FPS):
                break
            nf = min(round(2.9 * FPS), remaining - round(0.8 * FPS))
            if nf < round(1.5 * FPS):
                break
            use = cue_use.get(photo.stem, 0)
            cue_use[photo.stem] = use + 1
            shots.append({"block": row["id"], "kind": "photo",
                          "src": str(photo), "src_t0": 0.0, "variant": use,
                          "nf": nf, "f0": None})
            remaining -= nf

        pool = pl[row["section"]]
        pool.prune()
        while remaining > 0:
            take = min(remaining, round(B.SHOT_MAX * FPS))
            if remaining - take < round(B.SHOT_MIN * FPS):
                take = remaining
            got = pool.take(take / FPS, avoid={prev} | bite_srcs,
                            need_subject=False, lookahead_src=look)
            if got is None:
                if shots and shots[-1]["block"] == row["id"]:
                    shots[-1]["nf"] += remaining
                    remaining = 0
                    break
                raise RuntimeError(f"pool exhausted at {row['id']}")
            vid, t, clear = got
            nf = min(take, max(round(clear * FPS), round(B.SHOT_MIN * FPS)),
                     remaining)
            shots.append({"block": row["id"], "kind": "pool", "src": vid,
                          "src_t0": t, "nf": nf, "f0": None})
            prev = vid
            remaining -= nf

    f = 0
    for s in shots:
        s["f0"] = f
        f += s["nf"]
    if f != edl["frames"]:
        raise RuntimeError(f"shots {f} != edl {edl['frames']}")
    (MAN / "shots.json").write_text(json.dumps(shots, indent=1), encoding="utf-8")
    return shots


def render_all(shots: list[dict]) -> list[Path]:
    paths = []
    for i, s in enumerate(shots, 1):
        if s["kind"] == "card":
            dest = trim_card(Path(s["src"]), s["nf"])
        elif s["kind"] == "photo":
            dest = B.render_photo(Path(s["src"]), s["nf"], s.get("variant", 0))
        else:
            try:
                dest = B.render_piece(s)
            except RuntimeError:
                # One damaged region should not end a twenty-minute build.
                # Nudge the in-point and retry, keeping nf identical so the
                # frame budget still telescopes. NEVER nudge a bite: its
                # picture is pinned to its own audio and moving it puts the
                # wrong second under somebody's voice.
                if s["kind"] == "bite":
                    raise
                s = {**s, "src_t0": s["src_t0"] + 0.75}
                dest = B.render_piece(s)
                shots[i - 1]["src_t0"] = s["src_t0"]
        n = B.probe_frames(dest)
        if n != s["nf"]:
            raise RuntimeError(f"piece {dest.name} has {n} frames, want {s['nf']}")
        paths.append(dest)
        if i % 40 == 0:
            print(f"  pieces {i}/{len(shots)}", flush=True)
    return paths


def concat_video(paths: list[Path], dest: Path) -> Path:
    lst = WORK / "video_list.txt"
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in paths),
                   encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(dest), "-y"],
                   capture_output=True)
    return dest


def narration_track(edl: dict, dest: Path) -> Path:
    parts = []
    for i, row in enumerate(edl["blocks"]):
        parts.append(Path(row["audio"]))
        if row["pause"]:
            sp = WORK / f"sil_{i:03d}.wav"
            V.silence(row["pause"] / FPS, sp)
            parts.append(sp)
    return V.join(parts, dest)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    final = "--final" in sys.argv

    blocks = B.parse_script(ROOT / "script.md")
    quotes = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
    missing = [b["quote"] for b in blocks
               if b["kind"] == "bite" and b.get("quote") not in quotes]
    if missing:
        raise SystemExit(f"script references unknown quotes: {missing}")

    print(f"{len(blocks)} blocks, {sum(1 for b in blocks if b['kind']=='bite')} bites")
    card_png = render_cards()
    print(f"{len(card_png)} full-frame cards, all distinct layouts")

    edl = B.build_edl(blocks, quotes, final=final)
    for row in edl["blocks"]:
        blk = next(b for b in blocks if b["id"] == row["id"])
        row["mood"] = M.mood_of(blk["text"] or quotes.get(row["quote"], {})
                                .get("text", ""))
    (MAN / "edl_full.json").write_text(json.dumps(edl, indent=1), encoding="utf-8")
    print(f"EDL: {edl['seconds']/60:.1f} min ({edl['frames']} frames)")

    bite_s = sum(r["dur"] for r in edl["blocks"] if r["kind"] == "bite")
    print(f"recorded voice: {bite_s/60:.1f} min = "
          f"{bite_s/edl['seconds']*100:.0f}% of runtime")

    shots = plan(edl, blocks, quotes, card_png)
    print(f"{len(shots)} shots, median "
          f"{sorted(s['nf'] for s in shots)[len(shots)//2]/FPS:.1f}s")

    paths = render_all(shots)
    vid = concat_video(paths, WORK / "video.mp4")
    print(f"video: {B.probe_frames(vid)} frames")

    vo = narration_track(edl, WORK / "narration.wav")
    # NO MUSIC BED. The owner's instruction, 28 Aug: "Your background audio
    # track is super weird. Remove the complete background audio track. Just
    # have it be the voiceover part and even in the interviews don't put sound
    # over their voice or anything like that."
    #
    # music.py and qc/MOOD_TIMELINE.md are kept, unused, because the mood
    # analysis is still the right design if a bed is ever wanted again - but
    # nothing mixes it in. The film's only audio is the narration and the bites'
    # own recorded sound.
    segs = M.timeline(edl)
    M.write_report(segs, QC / "MOOD_TIMELINE.md")
    print(f"{len(segs)} mood segments analysed (bed NOT mixed - voice only)")

    vdur = edl["frames"] / FPS
    adur = V.duration(vo)
    if abs(vdur - adur) > 0.25:
        raise SystemExit(f"A/V drift {vdur - adur:+.3f}s - refusing to mux")

    # Voice only. No amix, so none of amix's clipping/renormalise traps apply.
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(vid), "-i", str(vo),
         "-filter_complex",
         "[1:a]aformat=sample_fmts=fltp:channel_layouts=stereo,"
         "loudnorm=I=-14:TP=-1.5:LRA=11[a]",
         "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         str(OUT), "-y"], capture_output=True)
    print(f"\nwrote {OUT.name}  {V.duration(OUT)/60:.2f} min")


if __name__ == "__main__":
    main()
