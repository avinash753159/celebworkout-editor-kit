"""Assemble v5 — fast-cut, and every window used exactly once.

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
import os
import subprocess
from pathlib import Path

import numpy as np

import graphics4 as G
import bed as bed_music
import score
from clips2 import crop_of
from reels5 import (DAY_FOOTAGE, FOOD_BY_CAT, FOOD_PIC, FOOD_SPARE,
                    FOOD_STILLS, MOVE_FOOTAGE, PLACE_LABEL, POOLS,
                    SECTION_POOL)
import cards as CARD

# The owner's verdict on the burned-in quote cards was "they offer 0 value and
# also doesn't sync with what's being said". They are replaced by the synced
# infographics in `infographics.py`, which are composited in Remotion instead.
#
# The card SPANS are left in place: `her_only=card_here` still forces those
# shots onto identity-verified footage, so the picture selection is unchanged
# and only the overlay disappears. That keeps the re-render to the handful of
# pieces that actually carried a card, because pieces are fingerprinted on
# their overlay name among other things.
NO_QUOTE_CARDS = os.environ.get("NO_QUOTE_CARDS", "1") != "0"
import motion as M
import cues as CUES_MOD
from cues import cue_positions
from depth_gen import depth_path
# script4 is the ELEVEN-MINUTE BIOGRAPHY - hook, subscribe ask, L1..L5, a
# read-out week and six food lists - and none of those blocks exist in
# script.md. Importing it here is what kept this assembler wired to the film
# we are not making. script5 reads script.md and manifest/audio5.json and
# cross-checks them.
from script5 import BITE_PICTURE, BITES, BLOCKS, FOODS, WEEK
import script5 as SCRIPT
# The quote slate comes from section 1's quotes.json via quotecards, NOT
# from the three hardcoded entries script4 used to carry - all three of
# which were credited 'Jennifer Aniston to InStyle' and one of which was
# said to Good Morning America.
import quotecards as QC

# Which narration this pipeline is built on. audio6 = the bite-led script
# (she leads, narrator bridges). Set ANISTON_AUDIO=audio5 to rebuild the
# old narration-led cut. One switch, so no run can straddle both.
import os as _os
AUDIO_DIR = _os.environ.get("ANISTON_AUDIO", "audio6")
AUDIO_MAN = AUDIO_DIR + ".json"

QC.check()
SLATE = QC.slate()

ROOT = Path(__file__).resolve().parent
# pieces6/, not pieces5/. A piece filename is BLOCK_INDEX_SECTION_FINGERPRINT
# and both films have blocks called W1 and D3, so the two cuts would share a
# directory and a stale piece could be served to the new film on a
# fingerprint collision. A separate directory makes that impossible instead
# of unlikely.
PIECES = ROOT / "pieces6"
WORK = ROOT / "work5"
HD = ROOT / "hd"
# V7 was the first cut of the NEW film; V8 is the pass-18 cut; V9 is pass 19,
# which bans the InStyle editorial-spread insert (see reels5.BANNED_WINDOW
# "eKKDRdE-WKs"). V6 on disk is the old biography and is left alone so they
# can be compared.
#
# THE NAME CHANGES WHEN THE CUT CHANGES, and that is not cosmetic. Everything
# downstream that caches frames - contact_sheet.py above all - keys on this
# file's NAME and mtime, so overwriting V7 in place asks the audit to tell two
# different films apart by a timestamp. Writing a new name makes it
# impossible for a V7 frame to appear on a V8 sheet, which is the failure this
# project has shipped three times ("a spin bike under a glute-bridge label").
OUT = ROOT / os.environ.get("BUILD_OUT", "JENNIFER_ANISTON_V10.mp4")
for d in (PIECES, WORK, ROOT / "manifest"):
    d.mkdir(exist_ok=True)

# DRY RUN. BUILD5_DRY=1 runs the whole picture PASS - pools, cursors, cues,
# card spans, every gate - and renders nothing. A full build is twenty-five
# minutes and most of that is ffmpeg; a pool that exhausts on shot 300, a cue
# that lands on a banned window, or a card that has nowhere safe to sit are
# all decisions, not renders, and waiting for the encoder to find them out is
# how a pass gets spent on one mistake.
DRY = bool(os.environ.get("BUILD5_DRY"))

FPS, W, H = 30, 1920, 1080
# The reference has ELEVEN silences longer than 0.35s; v5 had ZERO, with
# narration covering 92% of runtime. A film that never stops talking is
# exhausting in a way no frame-based check can see. Most joins stay tight;
# the ones that end a thought get a real beat.
GAP = 0.28
# The gaps are no longer a table in this file. Section 2 wrote a `gap_after`
# onto every block of manifest/audio5.json when it recorded the narration, and
# two tables that both claim to own the pacing is how a picture pass and an
# audio pass end up describing different films. The old BEAT dict named H2,
# L5, WK_SUNDAY and T6 - four blocks that do not exist - and silently gave
# every real block the 0.28s default.
_GAPS = {b["block"]: b.get("gap_after", GAP)
         for b in json.loads((Path(__file__).resolve().parent / "manifest"
                              / AUDIO_MAN).read_text(encoding="utf-8"))["blocks"]}


def gap_after(bid: str) -> float:
    return _GAPS.get(bid, GAP)
SR = 48_000
MUSIC_DB = -20.0
MUSIC_DB_UNDER_BITE = -26.0

# v4 ran unsharp=0.45 over everything, including footage upscaled 2x, which
# sharpened compression artifacts into the grain the picture was criticised
# for. Sharpening is now gentle and only applied to material that is already
# near native resolution; anything magnified gets denoised instead.
GRADE_NATIVE = ("unsharp=5:5:0.22:5:5:0.0,"
                "eq=contrast=1.04:saturation=0.97:gamma=0.99")
GRADE_UPSCALED = ("hqdn3d=2.0:1.5:6:6,"
                  "eq=contrast=1.04:saturation=0.97:gamma=0.99")
GRADE = GRADE_NATIVE          # fingerprint compatibility

# Shot lengths cycle through this. The old cycle was
#     [1.5, 1.2, 2.0, 1.4, 2.6, 1.3, 1.8, 1.1, 2.2, 1.6]
# - nothing under 1.1s, nothing over 2.6s - and it claimed to be "fast but not
# metronomic". It was metronomic. Scene-detecting both films side by side:
#
#                  reference      that cycle
#     median          1.80s          1.40s
#     p75             3.62s          2.00s
#     p90             5.91s          2.79s
#     over 3s          32%             9%
#     over 5s          13%             2%
#     sd              2.46           1.31
#
# The reference BREATHES: it cuts in fast bursts and then holds a shot for five
# to fifteen seconds. Everything here sat in a 1-2.8s band, which is why it
# reads as relentless rather than energetic. This cycle is bimodal to match -
# roughly a fifth under a second, a third over three seconds, an eighth over
# five. Holding a shot is only affordable because the pictures are now
# meaning-matched and gated; it would have been a bad idea two passes ago.
SHOT_CYCLE = [0.9, 1.5, 3.8, 1.2, 0.8, 2.2, 5.5, 1.4,
              1.0, 3.2, 0.9, 1.8, 6.2, 1.3, 2.6, 4.0]
MIN_SHOT = 0.7

# reels5.MAX_SHOT is the length every window-level check assumes a shot might
# reach. It sat at 2.6 for several passes with a comment claiming that was the
# longest shot carve() cuts, while this very cycle asked for 6.2 - so
# _window_banned and the card gate were both under-checking by 3.6 seconds.
# A comment cannot keep two files in step; this can.
def _check_max_shot() -> None:
    import reels5
    if reels5.MAX_SHOT < max(SHOT_CYCLE):
        raise SystemExit(
            f"build5: SHOT_CYCLE asks for shots up to {max(SHOT_CYCLE)}s but "
            f"reels5.MAX_SHOT is {reels5.MAX_SHOT}s, so every window-level "
            f"check is blind to the last {max(SHOT_CYCLE) - reels5.MAX_SHOT:.1f}s "
            f"of the longest shots. Raise reels5.MAX_SHOT.")


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
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
        # A killed build leaves a truncated piece behind - one 48-byte
        # W4_08_work_*.mp4 was enough to make ffprobe return nothing and take
        # the NEXT build down with ValueError: could not convert string to
        # float: ''. Report an unreadable file as 0.0 so the caller's
        # `nframes(out) != fr` test re-renders it, which is the behaviour the
        # cache check already wanted.
        txt = r.stdout.strip()
        return float(txt) if txt else 0.0


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


# Per-source exposure match. Measured on the v5 cut: brightness stdev 41.8
# across shots, range 13-246, and 90 hard jumps of more than 55 levels between
# adjacent shots. Fifty-odd sources were being cut together with one fixed
# grade, which is most of why the picture reads as assembled rather than
# produced. Each source is nudged toward a common target; the correction is
# partial and clamped so nothing gets crushed or washed out.
GRADE_TARGET = 104.0
GRADE_STRENGTH = 0.62
GRADE_CLAMP = 0.16


def exposure_of(vid: str) -> float:
    t = [x for x in LUMA.get(vid, []) if x >= 0]
    return sum(t) / len(t) if t else GRADE_TARGET


def match_vf(vid: str) -> str:
    """An eq brightness offset bringing this source toward the common target."""
    src = exposure_of(vid)
    if not src:
        return ""
    delta = (GRADE_TARGET - src) / 255.0 * GRADE_STRENGTH
    delta = max(-GRADE_CLAMP, min(GRADE_CLAMP, delta))
    if abs(delta) < 0.008:
        return ""
    return f",eq=brightness={delta:.4f}"


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
        # Vertical source. NEVER pad to black - that put a portrait in a narrow
        # strip with huge black bars either side, two shots into the film.
        # Fill the frame with a blurred, zoomed copy of the same picture and
        # lay the sharp version on top, which is what an editor does with
        # phone footage. Frame stays 16:9 and nothing is lost off the top.
        fit = (f"split=2[bg][fg];"
               f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
               f"crop={W}:{H},boxblur=28:2,eq=brightness=-0.06[bgb];"
               f"[fg]scale=-2:{H}:flags=lanczos[fgs];"
               f"[bgb][fgs]overlay=(W-w)/2:0")
    else:
        fit = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
               f"crop={W}:{H}")
    grade = GRADE_NATIVE if (W / max(1.0, cw)) <= 1.45 else GRADE_UPSCALED
    return f"{crop},{fit},setsar=1,{grade}{match_vf(vid)}"


# ───────────────────────────────────────────────────────────────── audio

def decode(p: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le",
                        "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2).copy()


def audio_sig(man) -> str:
    """Content fingerprint for the mix.

    This used to be `exists() and duration > 600`, which is a sanity check
    wearing a cache's clothes: it re-served a mix built from a DIFFERENT block
    order, a different bite list and a different music bed, because the stale
    file was also longer than 600 seconds. Same class of bug as the piece cache
    keyed on a shot's name.
    """
    h = hashlib.sha1()
    for b in man["blocks"]:
        h.update(f"{b['block']}|{b['kind']}|{b['file']}|{b['seconds']:.4f}|"
                 f"{gap_after(b['block']):.3f}".encode())
    h.update(f"{MUSIC_DB}|{MUSIC_DB_UNDER_BITE}".encode())
    for k in sorted(bed_music.MOOD_OF):
        h.update(f"{k}={bed_music.MOOD_OF[k]}".encode())
    for k in sorted(bed_music.MOOD_TRACK):
        h.update(f"{k}#{bed_music.MOOD_TRACK[k]}".encode())
    return h.hexdigest()[:12]


def build_audio(man):
    print("  audio ...")
    sig = audio_sig(man)
    cached = WORK / f"mix_{sig}.wav"
    if cached.exists() and probe(cached, "a") > 600:
        print(f"    cached {probe(cached, 'a'):.3f}s  sig {sig}")
        return cached
    edge = int(0.03 * SR)
    parts, duck, runs = [], [], []
    bl = man["blocks"]
    for i, b in enumerate(bl):
        a = decode(ROOT / AUDIO_DIR / b["file"])
        a[:edge] *= np.linspace(0, 1, edge)[:, None]
        a[-edge:] *= np.linspace(1, 0, edge)[:, None]
        parts.append(a)
        duck.append(np.full(len(a), b["kind"] == "bite"))
        runs.append((b["block"], len(a)))
        if i < len(bl) - 1:
            g = int(gap_after(b["block"]) * SR)
            parts.append(np.zeros((g, 2), np.float32))
            duck.append(np.zeros(g, bool))
            runs.append((b["block"], g))   # a gap holds the mood before it
    vo = np.concatenate(parts)
    is_bite = np.concatenate(duck)

    # One synth loop ran under all eleven minutes and the owner's verdict was
    # that it was "so bad for the audio". bed.build_for cuts real library music
    # to the film's emotional beats instead - see bed.MOOD_OF.
    bed = bed_music.build_for(runs)
    bed = bed[:len(vo)] if len(bed) >= len(vo) else np.pad(
        bed, ((0, len(vo) - len(bed)), (0, 0)))

    # High-pass the bed. Measured: 30% of its energy sits under 120Hz and
    # another 28% between 120-500Hz - right on top of the narrator's
    # fundamental, which is what makes a voice sound muddy rather than making
    # the music sound loud. Done in the frequency domain: a sample-by-sample
    # IIR over 32M samples in Python takes hours, an rfft takes a second.
    def highpass(x: np.ndarray, fc: float = 220.0) -> np.ndarray:
        n = len(x)
        f = np.fft.rfftfreq(n, 1.0 / SR)
        # gentle 12 dB/oct rolloff below fc, flat above
        gain = (f / fc) ** 2 / (1.0 + (f / fc) ** 2)
        gain = gain.astype(np.float32)
        out = np.empty_like(x)
        for ch in range(x.shape[1]):
            out[:, ch] = np.fft.irfft(np.fft.rfft(x[:, ch]) * gain, n)
        return out

    bed = highpass(bed)
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
    raw = WORK / f"mix_{sig}.f32"
    raw.write_bytes(mix.astype(np.float32).tobytes())
    wav = cached
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
        t += b["seconds"] + (gap_after(b["block"]) if i < len(bl) - 1 else 0.0)
        bounds.append(t)
    q = [int(round(x * FPS)) for x in bounds]
    return [q[i + 1] - q[i] for i in range(len(bl))]


def shot_words(bid: str, cuts: list[int], k: int) -> str:
    """The words spoken over shot k, by proportional split of the block's
    narration. Same arithmetic as transcript.py, so what the audit reads is
    what the chooser saw."""
    words = (VO_TEXT.get(bid) or "").split()
    if not words or not cuts:
        return ""
    tot = sum(cuts)
    before = sum(cuts[:k])
    a = int(len(words) * before / max(1, tot))
    b = int(len(words) * (before + cuts[k]) / max(1, tot))
    return " ".join(words[a:max(b, a + 1)])


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


def _remember_cut(vid: str, t: float, clear: float) -> None:
    """Persist a measured window into cuts.json so it is measured once."""
    import json
    import reels5
    key = f"{vid}@{t:.2f}"
    f = ROOT / "manifest" / "cuts.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return
    if key in d:
        return
    d[key] = [0.0, clear]
    f.write_text(json.dumps(d), encoding="utf-8")
    reels5.CUTS[key] = d[key]


def clean_pin(vid: str, t0: float, secs: float) -> float:
    """Nudge a PINNED window off a cut.

    A cue or a MOVE/DAY pin sets vid+t0 directly and skips the continuity
    check that pool windows go through, so a pin can sit 2s before a cut and
    the shot runs straight through it. That is how shot 28 played John
    Aniston, then a different actress, then the source's own YouTube end card.

    Ten shots in the V6 cut span a cut this way - including a Cake pin at 83.3
    that was fine when its shot was 1.5s and broke when time-based cues grew it
    to 3.8s. The pin is not wrong; it just cannot hold that long. So search
    outward for the nearest offset that can, and keep the original if none can.
    """
    import cuts
    import reels5
    if str(vid).startswith(("still:", "split:")):
        return t0

    def clear_at(t: float) -> float:
        """MEASURE the offset. clear_seconds() falls back to an optimistic
        99.0 for any window not in cuts.json, so a nudge to an unmeasured
        offset always looks clean - the first version of this function
        "fixed" all ten shots by stepping 0.25s onto a hole in the data."""
        return float(cuts.spike(vid, round(t, 2))[1])

    if clear_at(t0) >= secs:
        return t0
    dur = reels5.DUR.get(vid) or 0.0
    best = None
    # +/- 30s. The first version searched +/- 8s and gave up on the THURSDAY
    # card at aZiwqY_e9ZQ@47.8, reporting "cannot hold 5.0s anywhere near it"
    # - while clean 5s windows sat at 32, 34, 66 and 75, all outside the range.
    for step in range(1, 61):                       # +/- 30s in 0.5s steps
        for cand in (t0 + 0.5 * step, t0 - 0.5 * step):
            if cand < 0.5 or cand + secs > dur - 0.5:
                continue
            if clear_at(cand) >= secs:
                best = round(cand, 2)
                break
        if best is not None:
            break
    if best is None:
        print(f"    ! pin {vid}@{t0} cannot hold {secs:.1f}s anywhere near it")
        return t0
    print(f"    ~ pin {vid}@{t0} -> {best} (needs {secs:.1f}s clear)")
    return best

class Reels:
    """Hands out each window ONCE, in order.

    v4 kept a playhead per reel and rewound it when the source ran out, so
    short sources replayed identical seconds - 322 of 365 sampled frames had a
    near-duplicate, several byte-identical. There is no playhead here: the pool
    is already every distinct window, interleaved by source, and this is just a
    cursor over it. Running off the end is a hard error rather than a silent
    wrap, because a silent wrap is exactly the bug being fixed."""

    # ── film-wide registers ───────────────────────────────────────────────
    # `used` is per-cursor and was never enough. reels5 now deals the clip
    # windows so no window is in two pools, but a still CAN be reached from
    # two places (a texture and a cue), and a cue pin is not a pool draw at
    # all. TAKEN is the film's answer to "has this picture already played",
    # and it is what makes "no still may hold two shots inside twenty
    # seconds" impossible rather than merely warned about.
    TAKEN: set = set()
    # source id -> shots it has supplied, ANYWHERE, including cues and bites.
    # The acceptance bar is that no source supplies more than 8% of the film,
    # and the owner's oldest complaint is nine sources carrying 60% of it.
    # A cap that only the reels obeyed would be a cap the cue table could walk
    # straight through, so main() registers every pin here too.
    SRC_USED: dict = {}
    SRC_CAP: int = 10 ** 9        # set by main() from the real shot count
    # ...and the same count per VISUAL GROUP. A press junket is uploaded by
    # six outlets under six ids, so SRC_USED sees six sources at 2% each and
    # reports a clean sheet while the film shows one afternoon eighteen times.
    # See reels5.GROUP for how the groups were found and confirmed. Ungrouped
    # sources are their own group, so for them this counter is SRC_USED with
    # extra steps and the tighter cap simply never binds - GRP_CAP is checked
    # only against ids reels5 actually groups.
    GRP_USED: dict = {}
    GRP_CAP: int = 10 ** 9
    # The tag of the shot that just played, ACROSS the whole film. Rule 1 was
    # enforced per-cursor (self.last_src), which cannot see the shot before it
    # if that shot was a bite, a cue pin, or the last shot of the previous
    # section - three of the places two identical sources can meet.
    LAST_TAG: str | None = None
    # ...and its GROUP. Shots 349/350 and 355/356 of the V7 cut were adjacent
    # pairs from one junket and one podium under two ids each, and LAST_TAG
    # said they were different files, which they were, and identical pictures,
    # which it could not see.
    LAST_GROUP: str | None = None
    # The source of the NEXT bite, if the next block is one.
    #
    # LAST_TAG looks backwards, which is enough while every shot is a pool
    # draw. In a bite-led film it is not: the last pool shot of a VO block is
    # chosen BEFORE the bite that follows it, so nothing stops the reel handing
    # back the very interview that is about to play in full. That is how
    # ('T15', 'cBZC-8S9b8g') failed the consecutive-source gate - the gate was
    # right, the picker was blind. Set by main() one block ahead.
    NEXT_TAG: str | None = None
    # ...and the last RECENT_N groups, not just the last one.
    #
    # The V8 sheets are what forced this. Every mechanical criterion passed -
    # 0 consecutive same-source, 0 consecutive same-group, top group 4.4% -
    # and the film still repeated itself, because the rule only ever looked
    # ONE shot back and the montage weaves a still between two clips. Read on
    # qc/sheets: 349/351 Lko6LrBHSRc four seconds apart with one still
    # between them, 341/343 InUyN6CduEA 2.4s apart, 316/319 CFQcpm-wKuk,
    # 315/317 HyJALzFY7VU, 135/137 cBZC-8S9b8g two seconds apart, 164/167
    # 8Na0YrtG3AI. A viewer does not see "different windows of one file"; a
    # viewer sees the same shot come back.
    #
    # THREE, and it is a preference, not a wall: `next()` and `best()` both
    # keep their fallback pass, so a pool with nothing else left still yields
    # rather than raising. That matters - the diet and close pools are the
    # thin ones and they are exactly where the repeats were.
    RECENT_N: int = 3
    RECENT: list = []

    @classmethod
    def reset(cls, cap: int, gcap: int | None = None) -> None:
        cls.TAKEN = set()
        cls.SRC_USED = {}
        cls.GRP_USED = {}
        cls.SRC_CAP = cap
        cls.GRP_CAP = cap if gcap is None else gcap
        cls.LAST_TAG = None
        cls.LAST_GROUP = None
        cls.RECENT = []

    @classmethod
    def register(cls, r) -> None:
        """Record that this picture has played. Called for pool draws, cue
        pins and bites alike."""
        import reels5
        cls.TAKEN.add(tuple(r))
        cls.SRC_USED[r[0]] = cls.SRC_USED.get(r[0], 0) + 1
        g = reels5.group_of(r[0])
        cls.GRP_USED[g] = cls.GRP_USED.get(g, 0) + 1
        cls.LAST_TAG = r[0]
        cls.LAST_GROUP = g
        # Stills carry their own single-use rule (TAKEN) and the 20s proximity
        # warning, and a still between two clips is the WEAVE, not a repeat -
        # so they take a slot in the history without being avoidable
        # themselves. That is the point: the history has to count the still,
        # or "three shots ago" means something different in a still-heavy
        # stretch than in a talking-head one.
        cls.RECENT = (cls.RECENT + [g])[-cls.RECENT_N:]

    @classmethod
    def at_cap(cls, src: str) -> bool:
        # Stills are single-use by construction (TAKEN), so the cap is about
        # video sources. Applying it to stills as well would be harmless but
        # meaningless.
        if cls.SRC_USED.get(src, 0) >= cls.SRC_CAP:
            return True
        # ...and the group cap applies to EVERY group, including the
        # one-id groups that group_of() invents for ungrouped sources. A lone
        # source is a shoot too, and "no shoot may hold more than 5% of the
        # film" is the rule; making it apply only where several ids happen to
        # exist would mean an uploader who posts a junket once gets 8% and one
        # who posts it six times gets 5%, which is backwards.
        import reels5
        return cls.GRP_USED.get(reels5.group_of(src), 0) >= cls.GRP_CAP

    def __init__(self, pool, name="?"):
        self.pool = list(pool)
        self.name = name
        self.i = 0
        self.used = set()
        self.last_src = None
        self.card_unsafe = False      # set by best(her_only=True) - see there

    def _free(self, r) -> bool:
        """Available to THIS shot: not spent here, not spent anywhere else in
        the film, and its source not already at the 8% cap."""
        return (r not in self.used and tuple(r) not in Reels.TAKEN
                and not Reels.at_cap(r[0]))

    def _take(self, r):
        self.used.add(r)
        Reels.register(r)
        self.last_src = r[0]
        return r[0], r[1]

    def _fits(self, r, secs: float) -> bool:
        """A window can only carry a shot as long as its continuous run.
        A 6-second hold on a window that cuts after 2 seconds shows two
        different scenes, which is the defect that made one shot of the
        previous cut contain four."""
        if r[0].startswith(("still:", "split:")):
            return True
        import reels5
        # Ask whether the window has been MEASURED, not whether its value
        # looks like the default. 99.0 means both "no data" and "measured, no
        # cut found", so testing the number re-measured every clean window on
        # every access and made the build time out.
        if f"{r[0]}@{r[1]:.2f}" not in reels5.CUTS:
            # 99.0 is the "no data" default, not a measurement. Trusting it is
            # how a 6.2s shot on vMuarx9iWdg@860.6 ran past a cut into Vince
            # Vaughn: both sampled ends scored as her, because the mid check
            # only looks at t+1.6s and 4.6s of that shot were never examined.
            # Measure it, and remember the answer.
            import cuts
            clear = float(cuts.spike(r[0], round(r[1], 2))[1])
            _remember_cut(r[0], r[1], clear)
        else:
            clear = reels5.clear_seconds(r[0], r[1])
        return clear >= secs

    def next(self, secs: float):
        # THREE passes, and the middle one is the whole point.
        #
        # This used to be two: refuse anything in the last RECENT_N (=3)
        # groups, and if that finds nothing, take ANYTHING. The second rung is
        # a cliff, not a fallback - it drops the preference and the HARD rule
        # in the same step, so a pool that has run thin hands back the file
        # that is playing right now. Pass 19 hit exactly that: banning
        # InUyN6CduEA took the diet pool below what D6 needs and the build
        # failed its own consecutive-source gate on one pair,
        # ('D6', '5O3fyVHdw50').
        #
        # The three-group window is a PREFERENCE and may be given up. "No two
        # consecutive shots from the same source" is the rule the finished
        # film is checked against and must be given up last, so it gets its
        # own rung: refuse the last three, else refuse the last ONE, else take
        # anything. The bottom rung still exists - a pool with one window left
        # must be allowed to use it - but it is now reached only when the
        # alternative is no picture at all.
        import reels5
        for avoid in (Reels.RECENT, Reels.RECENT[-1:], []):
            j = self.i
            while j < len(self.pool):
                r = self.pool[j]
                if not self._free(r) or not self._fits(r, secs):
                    j += 1
                    continue
                # The GROUP, not the id. Two ids of the same junket back to
                # back are one picture twice to a viewer, and that is what
                # shots 349/350 of the V7 cut were.
                if avoid and reels5.group_of(r[0]) in avoid:
                    j += 1
                    continue
                # ...and never hand back the source that is about to play as a
                # bite. Treated as a hard rule, not a preference: it survives
                # every rung of the fallback, because cutting from a clip
                # straight into the same clip reads as a glitch.
                if (Reels.NEXT_TAG
                        and reels5.group_of(r[0]) == reels5.group_of(Reels.NEXT_TAG)):
                    j += 1
                    continue
                self.i = j + 1
                return self._take(r)
        raise SystemExit(
            f"reel pool '{self.name}' exhausted after {len(self.used)} windows "
            f"- widen the pool rather than repeating footage")

    def _still_ok(self, r) -> bool:
        """A still that may carry a card: no person in the picture."""
        if not r[0].startswith("still:"):
            return False                 # a split is two pictures, not one
        import reels5
        try:
            return reels5.card_still_ok(_still_path(r[0][len("still:"):]))
        except FileNotFoundError:
            return False

    def _pick_safe(self, secs: float, text: str):
        """A window that may carry a QUOTE CARD. Returns None if the pool has
        none left.

        TWO gates, and they answer different questions:

          IDENTITY    - is this her? `reels5._has_subject`. Unchanged, and not
                        relaxed by anything here.
          COMPOSITION - can she be READ in this frame, and is there room for
                        the card? `reels5.card_composition_ok`.

        The second one is new and is the 05:19 defect. `_has_subject` waves
        through every `TRAIN_OK` window without looking for a face at all,
        because the Pvolve films are mostly a shoulder and a band - genuinely
        her, and genuinely unreadable as her. A card over a back-turned,
        body-framed shot of the real subject passes an identity test and still
        makes no sense to a viewer. So a card slot now also needs a frontal
        face, big enough to be a portrait, clear of the card rectangle.

        Scans without moving self.i, because the cursor's skip-and-advance
        would silently burn every window it stepped over.

        This exists because filtering inside best() was not enough: best()
        returns early for a still slot, for empty text and when semantic is not
        ready, and that early return went straight to next(), which takes
        whatever is in front of the cursor. That is how shots 122 and 127 kept
        the W4 card over two UNSCORED faces after the first fix.
        """
        import reels5
        stills, clips = [], []
        for r in self.pool:
            if not self._free(r) or not self._fits(r, secs):
                continue
            if r[0].startswith(("still:", "split:")):
                if self._still_ok(r):
                    stills.append(r)
                continue
            if reels5._has_subject(r[0], r[1]):
                clips.append(r)          # identity only - composition below
        # Composition needs a frame grab, so rank by meaning FIRST and test the
        # shortlist. Testing the whole pool would be thousands of ffmpeg calls.
        ranked = clips
        if text and clips:
            import semantic
            if semantic.ready():
                sc = semantic.score(text, clips)
                ranked = [clips[i] for i in sc.argsort()[::-1]]
        # Never two in a row from the same file if anything else qualifies -
        # the rule best() already has. Without it the W4 card sat on three
        # consecutive shots of qAp9lq2CT5M and read as one long take with a
        # jump cut in it.
        # Prefer, in order: a window no card has used and not the previous
        # source; then any window no card has used; then anything that passes.
        # The last tier is a real fallback, not a formality - the outro pool
        # has only a handful of card-safe windows in it.
        fresh = [r for r in ranked if r not in CARD_WINDOWS_USED]
        # The two FRESH tiers scan deeper than the fallback. Twelve was not
        # enough: `oSb8auYSOcA@252.6` still came up under both W1 and D3
        # because no untried window in the first twelve passed the composition
        # gate, and the third tier then handed back the one already in use.
        # The frame grabs are cached in manifest/cardface2.json, so a deeper
        # scan is paid once.
        #
        # THE WHOLE LADDER RUNS TWICE, and the outer loop is the hard rule.
        # Freshness is a preference; "no two consecutive shots from the same
        # source" is the criterion the finished film is measured against, and
        # the three tiers below had it only in the first one - so a card bed
        # that could not be found among the fresh non-recent windows fell to
        # tier two, which filters on freshness alone, and took the file that
        # was on screen a moment ago. Pass 19: D6 shots 306 and 307 were both
        # `5O3fyVHdw50` under the today_basics card, four seconds of one
        # interview with a jump cut in the middle of a quote. So the first
        # pass forbids the previous group at EVERY tier and only the second
        # gives that up - and if it is given up, the alternative was no
        # card-safe footage at all.
        # NOT THE FILE THAT JUST PLAYED - AT EVERY TIER, WITH NO FALLBACK.
        #
        # The three tiers below trade freshness away as they go, and that is
        # right: reusing a window that has already carried a card somewhere
        # else in the film is a blemish, and running out of beds entirely is
        # worse. But only the first tier refused the source that just played,
        # so a card span longer than the pool's supply of card-safe windows
        # dropped to tier two and took the file that was on screen a moment
        # ago. D6 shots 306 and 307 were both `5O3fyVHdw50` under the
        # today_basics card: four seconds of one interview with a jump cut in
        # the middle of a quote, and a hard failure of the consecutive-source
        # gate this film is measured by.
        #
        # A bed that repeats the shot before it is not a safe bed, so it is
        # refused the same way an unvetted face is refused - and the fall
        # through is the one already written below: a person-free STILL, which
        # can never repeat because stills are single-use, and after that
        # `card_unsafe`, which ends the span. Deepening the scan was tried
        # first and is not the answer: at depth 180 the pool simply reshuffles
        # and produces three repeats instead of one. The supply is the
        # constraint; the honest response is to take the card off, not to
        # print the same picture twice.
        # THE TIERS SCAN DEEPER NOW THAT THE PREVIOUS SOURCE IS REFUSED.
        # 36/36/12 was sized when the third tier could always fall back on the
        # file that had just played; with that gone, a shallow scan turns a
        # thin pool into a DROPPED CARD instead of a repeat, and the D6
        # today_basics card vanished from the film entirely. The composition
        # grabs are cached in manifest/cardface2.json, so depth is paid once.
        for pool, depth in ((([r for r in fresh
                               if reels5.group_of(r[0]) not in Reels.RECENT]), 96),
                            (fresh, 96), (ranked, 96)):
            for r in pool[:depth]:
                if not self._free(r):
                    continue
                if reels5.group_of(r[0]) in Reels.RECENT[-1:]:
                    continue
                # `secs` is the shot's REAL rendered length. The gate used to
                # take only (vid, t) and look at t and t+1.6s; that is how a
                # 6.2s card shot could be vetted on its first 1.6 seconds and
                # spend its last 3.2 on Jay Leno.
                if reels5.card_composition_ok(r[0], r[1], secs):
                    CARD_WINDOWS_USED.add(r)
                    return self._take(r)
        if stills:
            # Rule 3's other half: an object cannot be misread as a person, so
            # a still is the SAFEST thing under a card, not a downgrade. But
            # safe is not the same as APPROPRIATE - taking stills[0] put a wall
            # of televisions under "consistency doesn't have to mean long
            # workouts", so choose by meaning like everything else does.
            #
            # ...except that for every pass up to this one it did NOT. No still
            # was in the CLIP index, so score() returned all zeros, argmax()
            # returned 0, and this line silently took whichever still happened
            # to be first in the pool list while claiming to choose by meaning.
            # D3 shot 211 is what that looks like on screen: f_saladplate, a
            # grilled chicken breast on salad leaves, under a card that reads
            # "When I wake up, I have warm lemon water and then I have a shake
            # or avocado and eggs" - first entry in DIET_TEXTURE, card-safe,
            # and about a different meal of a different day.
            #
            # semantic.main() now embeds the stills, and the degenerate case is
            # no longer silent: if the index cannot score these candidates the
            # build SAYS the pick was arbitrary instead of dressing it up.
            pick_from = [r for r in stills if r not in CARD_WINDOWS_USED] or stills
            r, how = pick_from[0], "pool order (no text)"
            if text and len(pick_from) > 1:
                import semantic
                if not semantic.ready():
                    how = "pool order (semantic index absent)"
                else:
                    have = semantic.embedded(pick_from)
                    known = [x for x, ok in zip(pick_from, have) if ok]
                    if not known:
                        how = "pool order (NOTHING HERE IS EMBEDDED)"
                        print(f"    !! card slot: none of the "
                              f"{len(pick_from)} candidate stills is in the "
                              f"CLIP index, so 'choose by meaning' cannot "
                              f"run and this pick is arbitrary. Re-run "
                              f"semantic.py - see semantic.embedded().")
                    else:
                        sc = semantic.score(text, known)
                        r = known[int(sc.argmax())]
                        how = f"meaning {float(sc.max()):.3f} of {len(known)}"
                        if len(known) < len(pick_from):
                            print(f"    ~ card slot: {len(pick_from) - len(known)}"
                                  f" of {len(pick_from)} candidate stills are "
                                  f"not embedded and could not be considered")
            print(f"    ~ card slot: no card-safe FOOTAGE in pool "
                  f"'{self.name}' for {secs:.1f}s - using the still {r[0]} "
                  f"[{how}]")
            CARD_WINDOWS_USED.add(r)
            return self._take(r)
        return None

    def best(self, secs: float, text: str, her_only: bool = False):
        """Same rhythm, better choice.

        The texture weave is deliberate - it is what gives the biography the
        establishing shots the reference has - so a still slot stays a still
        slot and is taken in order. Only CLIP slots are chosen by meaning:
        among every clip still unused in this pool, take the one whose picture
        best matches the words being spoken over it.

        Era-locking already decides WHICH pool, and the impostor and cut gates
        have already filtered it, so this only ever reorders windows that were
        all safe to use.

        `her_only` is for shots carrying a QUOTE CARD. Most pools are built
        with subject=False on purpose - anonymous demonstrators ARE the format
        for the exercise sections. But a card reading "JENNIFER ANISTON TO
        INSTYLE" over a stranger's face makes the viewer read that stranger as
        Aniston, and the V6 audit found it doing exactly that under W4 and O1.
        With her_only set, a clip must pass the identity AND the composition
        gate; a person-free still is fine, because an object cannot be mistaken
        for a person.

        WHEN NOTHING IS SAFE, THE CARD COMES OFF - the picture does not get
        downgraded. This used to read:

            safe = self._pick_safe(secs, text)
            if safe is not None:
                return safe
            # nothing safe anywhere in the pool - fall through rather than fail

        i.e. it silently took the next window in the cursor, card and all. That
        is the step-onto-a-hole shape that has burned this project repeatedly:
        the gate reports failure and the caller keeps walking. `card_unsafe` is
        set instead, build5.main reads it, ENDS THE CARD SPAN at this shot and
        prints the reason. The picture is still whatever the montage would have
        chosen - it just has no quote over it.
        """
        self.card_unsafe = False
        if her_only:
            safe = self._pick_safe(secs, text)
            if safe is not None:
                return safe
            self.card_unsafe = True
            print(f"    !! CARD SLOT UNSAFE: pool '{self.name}' has no window "
                  f"that is both provably her and readable as her, and no "
                  f"person-free still, for a {secs:.1f}s shot. PULLING THE "
                  f"CARD off this shot rather than sitting it on an unvetted "
                  f"picture.")
        import reels5
        import semantic
        while self.i < len(self.pool) and not self._free(self.pool[self.i]):
            self.i += 1
        if self.i >= len(self.pool):
            return self.next(secs)                    # raises with the message
        nxt = self.pool[self.i]
        synth = nxt[0].startswith(("still:", "split:"))
        if synth or not text or not semantic.ready():
            return self.next(secs)
        cands = [r for r in self.pool
                 if self._free(r)
                 and not r[0].startswith(("still:", "split:"))
                 and self._fits(r, secs)]
        if not cands:
            return self.next(secs)
        # Never take two consecutive shots from the SAME source if anything
        # else is available. best() scored purely on meaning and ignored what
        # the previous shot used, which produced runs of 4-in-6 from one file
        # (CsLRK1JphL4 at shot 56, jHtULFrKa2g at 215) - the self-similarity
        # that got dADifrjs6Og banned outright in pass 6.
        # Same three-rung ladder as next(): the three-group preference first,
        # then the hard consecutive rule on its own, then everything.
        others = [r for r in cands
                  if reels5.group_of(r[0]) not in Reels.RECENT]
        if not others:
            others = [r for r in cands
                      if reels5.group_of(r[0]) not in Reels.RECENT[-1:]]
        if others:
            cands = others
        sc = semantic.score(text, cands)
        pick = cands[int(sc.argmax())]
        # ADVANCE THE CURSOR EVEN THOUGH THE PICK CAME FROM ELSEWHERE.
        #
        # This one line is why the texture weave has never worked. The pool is
        # built by reels5.weave() as clip, clip, STILL, clip, clip, STILL ...
        # and self.i is the pointer that decides which kind of slot this shot
        # is. But a clip slot picked by MEANING, from anywhere in the pool,
        # left self.i exactly where it was - so the next shot looked at the
        # same clip again, and again, and the cursor only crawled forward when
        # the semantic ranker happened to choose the very window it was
        # sitting on. The stills three places further along were reached
        # almost never: the V6 cut is 257 shots and only 59 of them are
        # stills, most of those from the read-out food lists, and ZERO are
        # photographs.
        #
        # Advancing costs nothing - the window under the cursor is not
        # consumed, it stays in `cands` and can still be picked by a later
        # shot - and it makes `every=` in weave() mean what it says.
        self.i += 1
        return self._take(pick)


# Windows that have already carried a card, ANYWHERE in the film.
#
# Reels are per-section, and a window is single-use WITHIN a pool - which was
# enough while cards could sit on most of the footage. It stopped being enough
# once the composition gate cut the card-eligible set down to a few dozen
# windows: `oSb8auYSOcA@252.6` came out of the 'turn', 'diet_intro' AND 'diet'
# pools and carried three different quote cards, and `oSb8auYSOcA@441.4`
# carried two. The same frame of her under three different quotes reads as a
# mistake even though each one is individually correct.
#
# This is a card-only register. The montage may still reuse a window in another
# section; only the card beds have to be distinct.
CARD_WINDOWS_USED: set = set()


def cue_card_ok(vid: str, t0: float, dur: float) -> bool:
    """May a CUE shot carry a quote card for `dur` seconds?

    Cues are pinned by cues.py and skip the reel gates on purpose - shot 127 is
    pinned to Dani Coleman, who is a real and identifiable person who is not
    Aniston, and that is correct for the shot and wrong for a card over it.
    So the cue gets the same two questions every other card shot gets, just
    asked here instead of inside the cursor:

        a still  -> is there a person in the picture?  (rule 3)
        a clip   -> is it provably her, and framed so she reads as her?

    `dur` is REQUIRED and is the shot's real rendered length. A cue is pinned
    at an arbitrary t0 and can be any length the block gives it, so asking
    "is this window all right" without saying for how long is the same hole
    card_composition_ok had.

    Anything unmeasurable is a NO. Failing closed is the whole point.
    """
    import reels5
    if vid.startswith("split:"):
        return False                     # two pictures, one card - no
    if vid.startswith("still:"):
        try:
            return reels5.card_still_ok(_still_path(vid[len("still:"):]))
        except (FileNotFoundError, OSError):
            return False
    return reels5.card_composition_ok(vid, round(t0, 2), dur)


# Push-in strength. The reference punches in constantly; every clip here was a
# static crop, so a run of seated interviews read as a slideshow no matter how
# fast it was cut. 4% over a ~1.6s shot is felt, not seen.
PUSH = M.PUSH_CLIP
GL_JOBS: list[dict] = []
GL_PENDING: dict[Path, tuple] = {}
GL_DIR = ROOT / "gl"


def clip_piece(vid, t0, frames, out, overlay: Path | None = None,
               inward: bool = True):
    """A video shot. push_vf/zoompan used to live here and was the defect:
    it floored the crop origin and the crop size independently, so the picture
    jerked backwards every few frames. See motion.warp_clip."""
    import stabilise
    M.warp_clip(source(vid), t0, frames, out, inward,
                frame_vf(vid, None), overlay, sh,
                trf=stabilise.trf_for(vid, t0))


STILL_EXPOSURE = json.loads(
    (ROOT / "manifest" / "still_exposure.json").read_text())     if (ROOT / "manifest" / "still_exposure.json").exists() else {}


def still_match_vf(path: Path) -> str:
    """The exposure match lived inside frame_vf, which only runs on video.
    Measured on the last cut, 28% of runtime - every still, split, food list
    and card - bypassed it, so matching the clips barely moved the overall
    spread and hard cuts between shots actually went UP. Stills get the same
    correction here."""
    src = STILL_EXPOSURE.get(path.stem)
    if not src:
        return ""
    delta = (GRADE_TARGET - src) / 255.0 * GRADE_STRENGTH
    delta = max(-GRADE_CLAMP, min(GRADE_CLAMP, delta))
    if abs(delta) < 0.008:
        return ""
    return f",eq=brightness={delta:.4f}"


def still_piece(path: Path, frames, out, push: bool, overlay: Path | None = None):
    """Record a GL job. Rendering happens later, in one batch.

    The overlay is burned on AFTERWARDS, in flush_gl. Exercise wedges, day
    cards, food lists and place cards are titles, not scenery - they must not
    dolly with the camera.
    """
    if out.exists() and nframes(out) == frames:
        return                                    # already composited
    raw = out.with_name(out.stem + "_raw.mp4")
    if not raw.exists() or nframes(raw) != frames:
        GL_JOBS.append(M.gl_job(path, depth_path(path.stem), frames,
                                "in" if push else "out", raw))
    GL_PENDING[out] = (raw, frames, overlay, still_match_vf(path))


def flush_gl():
    """Render every recorded still job in one Chrome launch, then composite.

    Chrome costs ~1.5s to start and the film has ~140 still shots, so a launch
    per shot would waste three and a half minutes doing nothing."""
    todo = [j for j in GL_JOBS if not Path(j["out"]).exists()]
    if todo:
        jf = WORK / "gl_jobs.json"
        jf.write_text(json.dumps(todo, indent=1), encoding="utf-8")
        print(f"  gl: {len(todo)} still shots ...", flush=True)
        r = subprocess.run(["node", str(GL_DIR / "render_batch.mjs"), str(jf)],
                           cwd=str(GL_DIR))
        if r.returncode:
            raise SystemExit(f"gl renderer failed with {r.returncode}")
    for out, (raw, frames, overlay, eqvf) in GL_PENDING.items():
        if out.exists() and nframes(out) == frames:
            continue
        vf = eqvf.lstrip(",") or "null"
        if overlay is None:
            sh(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-vf", vf,
                "-frames:v", str(frames), "-c:v", "libx264", "-preset", "medium",
                "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
        else:
            sh(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-i", str(overlay),
                "-filter_complex", f"[0:v]{vf}[b];[b][1:v]overlay=0:0[o]",
                "-map", "[o]", "-frames:v", str(frames), "-c:v", "libx264",
                "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                str(out)])
        if nframes(out) != frames:
            raise SystemExit(f"{out.name}: {nframes(out)} != {frames}")


def synthetic_piece(spec: str, frames: int, out: Path, push: bool,
                    overlay: Path | None = None):
    """A generated establishing still (with an optional place label) or a
    side-by-side comparison. These are what give the biography the texture the
    reference has and V4 lacked."""
    if spec.startswith("split:"):
        a, b, la, lb = spec[len("split:"):].split("|")
        G.split_piece(_still_path(a), _still_path(b), la, lb, frames, out)
        return
    name = spec[len("still:"):]
    ov = overlay
    if ov is None and name in PLACE_LABEL:
        pl, sub = PLACE_LABEL[name]
        ov = WORK / f"place_{fingerprint(pl, sub)}.png"
        if not ov.exists():
            G.place_png(pl, sub, ov)
    still_piece(_still_path(name), frames, out, push, overlay=ov)


def still_sig(spec: str):
    """Size and mtime of the image(s) behind a still: / split: spec.

    Piece filenames are fingerprinted on the SPEC, not the file, so
    regenerating a still left the old picture in the cut. Four regenerated
    images - f_seeds, p_diner, mv_hipabduction, mv_kneelingrow - were fixed
    on disk and none of them reached the pass-7 build.
    """
    names = (spec[len("split:"):].split("|")[:2] if spec.startswith("split:")
             else [spec[len("still:"):]])
    out = []
    for n in names:
        try:
            st = _still_path(n).stat()
            out.append((n, st.st_size, int(st.st_mtime)))
        except SystemExit:
            out.append((n, 0, 0))
    return tuple(out)


_PHOTOS_LEDGER = ROOT / "manifest" / "photos.json"
# Real photographs, registered under short stable names (ph_*) so still:ph_NAME
# can reach them the same way still:q_gymfloor reaches a generated still. The
# files on disk keep their long hash-suffixed names - photos/ is inert
# otherwise, unreachable from any pool even after presence/identity/cuts have
# cleared it. See manifest/photos.json["names"]: name -> content hash -> file.
_PHOTO_NAMES: dict = {}
if _PHOTOS_LEDGER.exists():
    _pd = json.loads(_PHOTOS_LEDGER.read_text(encoding="utf-8"))
    _by_hash = _pd.get("by_hash", {})
    for _n, _h in _pd.get("names", {}).items():
        if _h in _by_hash:
            _PHOTO_NAMES[_n] = _by_hash[_h]["file"]


def _still_path(name: str) -> Path:
    for d in ("stills_move", "stills_place", "stills_food", "stills"):
        p = ROOT / d / f"{name}.jpg"
        if p.exists():
            return p
    if name in _PHOTO_NAMES:
        # photos_169/ FIRST. gl/scene.js maps a texture onto a 16:9 plane with
        # no cover and no letterbox, so the original portrait files come out
        # stretched two and a half times wide. photo_frame.py writes a 16:9
        # rendition of each one; photos/ stays as the untouched original and
        # the audit trail. See photo_frame.py for why this is not black bars.
        for d in ("photos_169", "photos"):
            p = ROOT / d / _PHOTO_NAMES[name]
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
    if vid.startswith(("still:", "split:")):
        # A bite whose own footage is unusable - see script5.BITE_PICTURE.
        # The credit still burns in, because the words are still hers and
        # still quoted; only the picture changed.
        still_piece(_still_path(vid[len("still:"):]), frames, out, True,
                    overlay=cp)
        return
    sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
        "-i", str(source(vid)), "-i", str(cp),
        "-filter_complex", f"[0:v]{frame_vf(vid, None)}[b];[b][1:v]overlay=0:0[o]",
        "-map", "[o]", "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out)])


# section lookup for every speech block
SECTION = {}
VO_TEXT = {}
for _it in BLOCKS:
    if _it[0] == "VO":
        SECTION[_it[1]] = _it[2]
        VO_TEXT[_it[1]] = _it[3]
WEEK_BY_ID = {f"WK_{d}": (d, lab, dur, mv) for d, lab, dur, mv in WEEK}
FOOD_BY_ID = {f"FD_{c.replace(' ', '_')}": (c, items) for c, items in FOODS}


def main():
    _check_max_shot()
    SCRIPT.check()
    CUES_MOD.check()
    bed_music.check()
    man = json.loads((ROOT / "manifest" / AUDIO_MAN).read_text(encoding="utf-8"))
    wav = None if DRY else build_audio(man)
    per = block_frames(man)

    # THE 8% RULE, ARITHMETIC RATHER THAN HOPE.
    # Count the shots before choosing any of them, so the per-source cap is a
    # real fraction of the real film and not a guess that goes stale the next
    # time SHOT_CYCLE changes. 7.5% leaves margin: cue pins and bites are
    # registered against the same counters and they are not refusable.
    n_shots, _ph = 0, 0
    for _b, _t in zip(man["blocks"], per):
        if _b["kind"] == "bite":
            n_shots += 1
            continue
        _c = carve(_t, _ph)
        _ph += len(_c)
        n_shots += len(_c)
    # The GROUP cap is arithmetic in the same way, off reels5.GROUP_CAP_FRAC,
    # and it is deliberately tighter than the id cap - see reels5.GROUP. The
    # 0.9 is the same margin logic as the 0.075 above: cue pins and bites are
    # registered against these counters and cannot be refused, so the cap the
    # cursors obey has to sit under the bar the audit measures.
    import reels5 as _R5
    Reels.reset(max(4, int(0.075 * n_shots)),
                max(4, int(0.9 * _R5.GROUP_CAP_FRAC * n_shots)))
    print(f"  {n_shots} shots planned; no source may supply more than "
          f"{Reels.SRC_CAP} of them ({Reels.SRC_CAP / n_shots * 100:.1f}%), "
          f"and no visual GROUP more than {Reels.GRP_CAP} "
          f"({Reels.GRP_CAP / n_shots * 100:.1f}%) - "
          f"{len(_R5.GROUP)} groups over {len(_R5.GROUP_OF)} ids")

    order, rows = [], []
    push = True
    phase = 0
    # One cursor per SECTION, shared by every block in it, for the whole film.
    # Until now a fresh Reels was built per narration block, so L1..L5 each
    # restarted the 'life' pool at index 0 and re-served the same opening
    # windows - which is why SHERMAN OAKS and NEW YORK CITY kept coming back
    # even after windows were made single-use. This is the root of the
    # repetition, and it predates v5.
    cursors: dict[str, Reels] = {}

    # The bite-led script names sections the old pool map never had. Rather than
    # invent thin new pools, alias each onto the one whose FOOTAGE actually fits:
    # the trainer chapters want present-day training footage, the mistakes
    # chapter wants the method's equipment, and the ask reuses the close.
    SECTION_ALIAS = {
        "intro": "hook",
        "trainer": "now",
        "mistakes": "evidence",
        "ask": "close",
    }

    def cursor(sec: str) -> Reels:
        sec = SECTION_ALIAS.get(sec, sec)
        if sec not in cursors:
            if sec not in POOLS:
                raise SystemExit(f"build5: no pool named {sec!r}")
            cursors[sec] = Reels(POOLS[sec], sec)
        return cursors[sec]
    print("  picture ...")

    _mb = man["blocks"]
    for _bi, (b, total) in enumerate(zip(_mb, per)):
        bid = b["block"]

        # One block of lookahead, so the picker can refuse the source that is
        # about to play as a bite. Without it the last pool shot of a VO block
        # is chosen blind to what follows, and cuts from a clip straight into
        # the same clip.
        _nb = _mb[_bi + 1] if _bi + 1 < len(_mb) else None
        Reels.NEXT_TAG = (BITES.get(_nb["block"], (None,))[0]
                          if _nb is not None and _nb["kind"] == "bite" else None)

        # ── her voice: one locked shot, no cutting
        # The bite key IS the block id now. script4 carried a third naming
        # scheme for the same five clips (OLD, PAST40, INJURY, NOTPAIN,
        # JUICE) and audio5.json keys them by quote id, so two of the three
        # had to be kept in step by hand.
        if b["kind"] == "bite":
            pic = BITE_PICTURE.get(bid)
            _bv = pic[0] if pic else BITES[bid][0]
            fp = fingerprint("bite", bid, BITES[bid], pic,
                             still_sig(_bv) if _bv.startswith(("still:", "split:"))
                             else frame_vf(_bv), GRADE, total)
            out = PIECES / f"{bid}_00_bite_{fp}.mp4"
            if not DRY:
                if not out.exists() or nframes(out) != total:
                    bite_piece(bid, total, out)
                if out not in GL_PENDING and nframes(out) != total:
                    raise SystemExit(f"{out.name}: {nframes(out)} != {total}")
            tag = pic[0] if pic else BITES[bid][0]
            Reels.register((tag, pic[1] if pic else BITES[bid][1]))
            order.append(out)
            rows.append(dict(block=bid, kind="bite", tag=tag, frames=total,
                             src_t0=(pic[1] if pic else BITES[bid][1])))
            print(f"    {bid:<13} BITE  {total/FPS:5.2f}s   1 shot  [{tag}]")
            continue

        # The read-out WEEK (WK_MONDAY..WK_SUNDAY) and the read-out FOOD
        # LISTS (FD_FRUITS..FD_BEVERAGES) were two whole picture branches -
        # a day card with a wedge per exercise, and a list overlay building
        # over food stills. script.md has neither: there is no spoken week
        # and no spoken food list in the new film. The branches are gone
        # rather than left dead, because dead code that keys on block ids is
        # exactly the shape of thing that wakes up when a block id is reused.
        # reels5.MOVE_FOOTAGE / DAY_FOOTAGE / FOOD_* are still exported for
        # section 5's card work.

        # ── everything else: straight fast montage off the section pool
        # SECTION_POOL is exhaustive and a miss is fatal. It used to be
        #     sec = SECTION.get(bid, "life")
        # so any block the map had not heard of drew on the biography pool -
        # which is how a sentence about her diet could be illustrated with
        # 1990s footage and nothing complained.
        if bid not in SECTION_POOL:
            raise SystemExit(
                f"build5: block {bid} (section {SECTION.get(bid)!r}) has no "
                f"pool in reels5.SECTION_POOL. Add it rather than letting it "
                f"fall through to a default.")
        sec = SECTION_POOL[bid]
        reels = cursor(sec)
        n_shots = 0
        # A quote runs as a CARD over the middle of its block. It arrives
        # whole and it leaves whole; see cards.py and quotecards.py.
        qspec = SLATE.get(bid)
        cuts_all = carve(total, phase)
        # CUE SHOTS: a picture forced onto the shot covering the words that
        # name it. Without this the picture is chosen per-section, so "her
        # father, John Aniston" played over an empty studio and "Ferris
        # Bueller" over a diner.
        cue_for = {}
        if bid in VO_TEXT:
            starts, acc = [], 0
            for fr in cuts_all:
                starts.append(acc / max(1, total)); acc += fr
            for frac, src, t0c in cue_positions(bid, VO_TEXT[bid]):
                k = max(0, min(len(cuts_all) - 1,
                               max(i for i, st in enumerate(starts) if st <= frac)))
                while k in cue_for and k + 1 < len(cuts_all):
                    k += 1
                cue_for[k] = (src, t0c)
        # ── WHERE THE CARD SITS, AND FOR HOW LONG ────────────────────────────
        # It used to be shots 28%..92% of the block, and the card was rendered
        # at frac = (k - q_from + 1)/(q_to - q_from) of its own text on each of
        # them - so the viewer read a growing half-sentence for all of it and
        # the whole quote only on the last shot. Both halves of that are gone.
        #
        # The span is now derived from READING TIME (quotecards.hold_seconds:
        # 2.6 words/sec plus a beat to notice the card), centred in the block,
        # and the card is ONE finished PNG held across every shot in it. If the
        # block cannot hold the quote for long enough to read, that is a hard
        # complaint, not a silent squeeze - the quote is too long and belongs
        # in quotecards.SLATE as a shortened card text.
        q_from = q_to = 0
        if qspec:
            secs = [f / FPS for f in cuts_all]
            starts = [sum(secs[:i]) for i in range(len(secs) + 1)]
            block_s = starts[-1]
            need = qspec["hold"]
            lead = max(0.0, (block_s - need) / 2.0)

            def _span(a, cap=None):
                """The shortest run starting at `a` that holds the quote,
                stopping at `cap` (the first shot the card may not touch)."""
                end = len(secs) if cap is None else cap
                b = next((i for i in range(a + 1, end + 1)
                          if starts[i] - starts[a] >= need), end)
                return a, b, starts[b] - starts[a]

            centre = max((i for i, s in enumerate(starts[:-1]) if s <= lead),
                         default=0)
            # A CUE shot is pinned by cues.py and bypasses the reel gates
            # entirely, so a card sitting on one has nothing vouching for it.
            # But "cue" is not the same as "unsafe": most cues are object
            # stills - q_ropes, f_mexican, q_watchclock - and an object is the
            # SAFEST thing under a card. Testing cue-ness instead of safety
            # threw away six of the nine cards on the first run, including the
            # W3 card over the spin bike, which is the one shot in the film
            # everybody agrees is right. So ask the real question.
            bad_cue = {k for k, (cv, ct) in cue_for.items()
                       if not cue_card_ok(cv, ct, secs[k])}
            # ...and the shots whose CONTENT the card contradicts. Same
            # treatment - the card may not touch them - but a different
            # question: cue_card_ok asks "who is in this picture", SPAN_DENY
            # asks "do these words belong over this picture at all". See
            # quotecards.SPAN_DENY; D2's shake card used to run on to a chicken
            # burger.
            deny_tags = QC.SPAN_DENY.get(bid, {})
            bad_cue |= {k for k, (cv, ct) in cue_for.items() if cv in deny_tags}
            # The block splits into runs of shots the card MAY touch. Pick the
            # run that can hold the quote and sits nearest the middle; if none
            # can, take the longest run there is and say how short it falls.
            # The first attempt at this only slid the span when a fully clean
            # one existed and otherwise left it where it was - which put q_from
            # ON a bad cue in five blocks and killed the card on its own first
            # shot. W4 lost its card entirely that way.
            runs, cur = [], []
            for i in range(len(secs)):
                if i in bad_cue:
                    if cur:
                        runs.append(cur)
                    cur = []
                else:
                    cur.append(i)
            if cur:
                runs.append(cur)
            fits = [r for r in runs
                    if starts[r[-1] + 1] - starts[r[0]] >= need - 0.05]
            if fits:
                run = min(fits, key=lambda r: abs((r[0] + r[-1]) / 2 - centre))
                a = min(max(run[0], centre), run[-1])
                while a > run[0] and starts[run[-1] + 1] - starts[a] < need:
                    a -= 1
                q_from, q_to, got = _span(a, cap=run[-1] + 1)
            elif runs:
                run = max(runs, key=lambda r: starts[r[-1] + 1] - starts[r[0]])
                q_from, q_to = run[0], run[-1] + 1
                got = starts[q_to] - starts[q_from]
            else:
                q_from = q_to = got = 0
            if bad_cue:
                print(f"    ~ card {bid}: unvetted cue shots {sorted(bad_cue)} "
                      f"- card laid into shots {q_from}-{q_to-1}")
            if got < need - 0.05:
                print(f"    !! CARD TOO LONG: {bid} can only hold "
                      f"{qspec['id']} for {got:.1f}s, it needs {need:.1f}s to "
                      f"read. SHORTEN THE QUOTE in quotecards.SLATE.")
            else:
                print(f"    card {bid}: {qspec['id']} shots {q_from}-{q_to-1}, "
                      f"{got:.1f}s on screen (needs {need:.1f}s)")
        for k, fr in enumerate(cuts_all):
            phase += 1
            card_here = bool(qspec) and q_from <= k < q_to
            if k in cue_for:
                vid, t0 = cue_for[k]          # a cue outranks any similarity
                t0 = clean_pin(vid, t0, fr / FPS)
                # A pin is not refusable, but it still counts against the 8%
                # rule and it still marks the picture as spent - otherwise the
                # reels could hand the same still back as texture ten seconds
                # later, which is how p_office played twice.
                Reels.register((vid, round(t0, 2)))
                if card_here and not cue_card_ok(vid, t0, fr / FPS):
                    print(f"    !! card {bid}: shot {k} is a CUE ({vid}) that "
                          f"fails the card gates and nothing vouches for who "
                          f"is in it. Pulling the card from here on.")
                    q_to, card_here = k, False
            else:
                vid, t0 = reels.best(fr / FPS, shot_words(bid, cuts_all, k),
                                     her_only=card_here)
                if card_here and reels.card_unsafe:
                    # best() already said why, loudly. End the span here rather
                    # than sit the card on a picture nothing vouched for.
                    q_to, card_here = k, False
            # A SPAN_DENY tag can also arrive on a shot that is not a cue - the
            # reel is free to pick the same still. The span walls above cover
            # the cue case at layout time; this covers the rest at the moment
            # the picture is known, and ends the span rather than trusting that
            # the earlier calculation saw everything.
            if card_here and vid in QC.SPAN_DENY.get(bid, {}):
                print(f"    !! card {bid}: shot {k} is {vid}, which "
                      f"quotecards.SPAN_DENY says this card must not sit on "
                      f"({QC.SPAN_DENY[bid][vid][:60]}...). Ending the span.")
                q_to, card_here = k, False
            synth = vid.startswith(("still:", "split:"))
            qov = None
            if card_here and not NO_QUOTE_CARDS:
                # ONE PNG per quote, content-addressed on the FINISHED text.
                # There is no fraction any more, so a prefix is not expressible.
                qov = CARD.quote_card(qspec["text"], qspec["credit"])
            fp = fingerprint(vid, round(t0, 2), fr,
                             (still_sig(vid), M.PUSH_STILL, M.RELIEF, M.renderer_sig()) if synth
                             else (frame_vf(vid), M.PUSH_CLIP),
                             GRADE, push, M.EASE_NAME, qov.name if qov else "")
            out = PIECES / f"{bid}_{k:02d}_{sec[:4]}_{fp}.mp4"
            if DRY:
                pass
            elif synth:
                synthetic_piece(vid, fr, out, push, overlay=qov)
            elif not out.exists() or nframes(out) != fr:
                clip_piece(vid, t0, fr, out, overlay=qov, inward=push)
            push = not push          # alternate the push direction every shot
            if not DRY and out not in GL_PENDING and nframes(out) != fr:
                raise SystemExit(f"{out.name}: {nframes(out)} != {fr}")
            order.append(out)
            rows.append(dict(block=bid, kind=sec, tag=vid, frames=fr,
                             src_t0=round(t0, 2),
                             card=(qspec['id'] if card_here else None),
                             cue=(k in cue_for)))
            n_shots += 1
        print(f"    {bid:<13} {total/FPS:5.2f}s  {n_shots:>3} shots  [{sec}]")

    # YouTube end screens need somewhere calm to sit. The film ended on
    # fourteen shots of 1.1-2.6s, so a subscribe button or next-video card
    # would fight a hard cut every second. Hold the wordmark for six seconds.
    END_SECS = 6.0
    end_frames = int(round(END_SECS * FPS))
    end_out = PIECES / f"ZZ_endcard_{fingerprint('endcard', end_frames)}.mp4"
    if not DRY and (not end_out.exists() or nframes(end_out) != end_frames):
        G.render_still_image(G.endcard(), end_frames, end_out)
    order.append(end_out)
    rows.append(dict(block="END", kind="card", tag="endcard", frames=end_frames))

    # A labelled card may appear exactly once. LOS ANGELES / 1990 played four
    # times in the V5 cut, RUDOLF STEINER SCHOOL twice five seconds apart.
    from collections import Counter
    cards = Counter(r["tag"][len("still:"):] for r in rows
                    if r["tag"].startswith("still:")
                    and r["tag"][len("still:"):] in PLACE_LABEL)
    dupes = {k: n for k, n in cards.items() if n > 1}
    if dupes:
        raise SystemExit(f"LABEL GATE FAILED: place cards repeated {dupes}")
    print(f"    place cards: {len(cards)} shown, none repeated")
    # No still may hold two shots inside twenty seconds of each other.
    seen_at: dict[str, float] = {}
    t = 0.0
    near = []
    for r in rows:
        if r["tag"].startswith("still:"):
            prev = seen_at.get(r["tag"])
            if prev is not None and t - prev < 20.0:
                near.append((r["tag"], round(prev, 1), round(t, 1)))
            seen_at[r["tag"]] = t
        t += r["frames"] / FPS
    if near:
        print(f"    WARNING: {len(near)} stills repeat within 20s: {near[:8]}")

    # ── the acceptance criteria, measured on what was actually built ──────
    # Printing "shots per source" at the end of a 25-minute build is not the
    # same as enforcing it, so these are hard failures. Every one of them is
    # a defect the owner has already complained about once.
    from collections import Counter as _C
    tags = _C(r["tag"] for r in rows if r["tag"] != "endcard")
    n = sum(tags.values())
    worst, worst_n = tags.most_common(1)[0]
    if worst_n / n > 0.08:
        raise SystemExit(
            f"REPETITION GATE FAILED: {worst} supplies {worst_n} of {n} shots "
            f"({worst_n / n * 100:.1f}%), over the 8% bar. Widen the pool.")
    # The same bar, per VISUAL GROUP. Measured on the V7 cut, which passed the
    # line above with room to spare: the Horrible Bosses junket held 18 shots
    # (4.9%) under three ids and the SAG 2020 white dress 14 (3.8%) under
    # three more - 8.8% of the film for two afternoons, invisible to a counter
    # that keys on the YouTube id. See reels5.GROUP.
    gtags = _C(_R5.group_of(t) for t in tags.elements()
               if not t.startswith(("still:", "split:")))
    gworst, gworst_n = gtags.most_common(1)[0]
    if gworst_n / n > _R5.GROUP_CAP_FRAC:
        raise SystemExit(
            f"GROUP REPETITION GATE FAILED: the visual group {gworst!r} "
            f"({', '.join(_R5.GROUP.get(gworst, [gworst]))}) supplies "
            f"{gworst_n} of {n} shots ({gworst_n / n * 100:.1f}%), over the "
            f"{_R5.GROUP_CAP_FRAC * 100:.0f}% bar. Widen the pool.")
    dupes = [t for t, c in tags.items() if c > 1
             and not t.startswith(("still:", "split:"))]
    # A BITE's source is not a choice - it is wherever the person happens to
    # have said the sentence. Two consecutive bites from one interview are the
    # same speaker continuing to answer, which is exactly what a bite-led film
    # is supposed to look like; flagging it as repetition confuses "we ran out
    # of footage" with "she kept talking". The gate still applies in full to
    # every pool-selected shot, which is what it was built to police.
    runs = [(rows[i]["block"], rows[i]["tag"])
            for i in range(1, len(rows))
            if rows[i]["tag"] == rows[i - 1]["tag"]
            and not (rows[i].get("kind") == "bite"
                     and rows[i - 1].get("kind") == "bite")]
    if runs:
        idx = [i for i in range(1, len(rows))
               if rows[i]["tag"] == rows[i - 1]["tag"]
               and not (rows[i].get("kind") == "bite"
                        and rows[i - 1].get("kind") == "bite")]
        ctx = []
        for i in idx[:4]:
            a, b_ = rows[i - 1], rows[i]
            ctx.append(f"{a['block']}({a.get('kind','vo')},cue={a.get('cue')})"
                       f" -> {b_['block']}({b_.get('kind','vo')}) both {b_['tag']}")
        raise SystemExit(
            "CONSECUTIVE-SOURCE GATE FAILED: "
            f"{len(runs)} places where two shots in a row come from the same "
            "tag:\n    " + "\n    ".join(ctx))
    granges = [(rows[i]["block"], rows[i - 1]["tag"], rows[i]["tag"])
               for i in range(1, len(rows))
               if not rows[i]["tag"].startswith(("still:", "split:"))
               and not rows[i - 1]["tag"].startswith(("still:", "split:"))
               and rows[i]["tag"] != "endcard"
               and rows[i - 1]["tag"] != "endcard"
               # Same exemption as the source gate above: two consecutive BITES
               # from one interview are one person still answering, which is
               # what a bite-led film is made of. The rule still binds on every
               # pool-selected shot, including a pool shot next to a bite.
               and not (rows[i].get("kind") == "bite"
                        and rows[i - 1].get("kind") == "bite")
               and _R5.group_of(rows[i]["tag"])
               == _R5.group_of(rows[i - 1]["tag"])]
    if granges:
        raise SystemExit(
            f"CONSECUTIVE-GROUP GATE FAILED: {len(granges)} places where two "
            f"shots in a row are the same shoot under different ids: "
            f"{granges[:6]}")
    print(f"    sources: {len(tags)} distinct tags over {n} shots; "
          f"heaviest {worst} at {worst_n} ({worst_n / n * 100:.1f}%)")
    photos = sorted({r["tag"] for r in rows if r["tag"].startswith("still:ph_")})
    print(f"    photographs in the cut: {len(photos)} - "
          f"{', '.join(p[len('still:ph_'):] for p in photos)}")

    (ROOT / "manifest" / "shots6.json").write_text(
        json.dumps({"fps": FPS, "gap": GAP, "film": OUT.name,
                    "shots": rows}, indent=1), encoding="utf-8")

    # Retired cards are deleted HERE, by the thing that knows which nine the
    # film actually uses, rather than by somebody remembering to run the
    # one-liner in cards.prune's docstring. Editing a quote leaves the previous
    # rendering in cards/ under its old content hash, and a directory holding
    # thirteen PNGs for nine cards is how a reviewer ends up reading last
    # week's picture. It cannot reach the film - build5 composites the Path
    # quote_card hands back - but it can absolutely reach an eye.
    gone = CARD.prune(CARD.card_path(v["text"], v["credit"])
                      for v in SLATE.values())
    print(f"    cards/: {len(SLATE)} in the film, {gone} retired files deleted")

    if DRY:
        print("\n  DRY RUN - nothing rendered. Re-run without BUILD5_DRY "
              "to make the film.")
        for sec, c in sorted(cursors.items()):
            print(f"    pool {sec:<10} used {len(c.used):>4} of {len(c.pool):>5}")
        return

    flush_gl()

    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in order), encoding="utf-8")
    body = WORK / "body.mp4"
    print(f"  concat {len(order)} shots ...")
    sh(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", str(lst), "-c", "copy", str(body)])

    v, a = probe(body), probe(wav, "a")
    tail = v - a                       # the endcard runs past the narration
    print(f"    video {v:.3f}s  audio {a:.3f}s  tail {tail:.3f}s")
    if abs(tail - END_SECS) > 0.25:
        raise SystemExit(
            f"SYNC GATE FAILED: tail {tail:.3f}s, expected {END_SECS:.1f}s")

    print("  mux ...")
    OUT.unlink(missing_ok=True)
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(body), "-i", str(wav),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
        str(OUT)])          # NOT -shortest: the endcard outlives the audio
    d = probe(OUT)
    import statistics
    lens = sorted(r["frames"] / FPS for r in rows)
    print(f"\n  {OUT.name}  {int(d)//60}:{d%60:05.2f}  "
          f"{OUT.stat().st_size/1e6:.1f} MB  {len(order)} shots")
    for sec, c in sorted(cursors.items()):
        print(f"    pool {sec:<14} used {len(c.used):>4} of {len(c.pool):>5}")
    print(f"  median shot {statistics.median(lens):.2f}s   "
          f"cut every {d/len(order):.2f}s   "
          f"(reference: 1.4s / 2.3s)")


if __name__ == "__main__":
    main()
