"""Browser-rendered graphics for build5.

Only the quote treatment for now. It used to be a translucent bar along the
bottom with PIL-drawn text in it, which read as a subtitle rather than a pull
quote and collided with the burned-in captions several sources already carry.
gl/card.mjs renders it as a card in CSS instead - real leading, letter-spaced
credit, a hanging opening mark, and a shadow that lifts it off the footage.

Cards live in cards/, NOT in work5/, because work5 is wiped between builds and
re-rendering them would cost a browser launch each time. That is the same trap
that made the .trf files vanish and silently disable stabilisation.

── ONE CARD PER QUOTE ────────────────────────────────────────────────────────
`quote_card` used to take a `reveal` fraction and build the card one word at a
time across the shots the quote spanned, so every shot but the last carried a
PREFIX of the sentence. build5 cached on `fingerprint(qspec, round(frac,3))`,
so cards/ filled up with 74 half-sentences. The fraction is gone: the file name
is now the content hash of (text, credit, geometry) and nothing else, so one
quote is exactly one PNG and the same PNG is composited on every shot of the
span. A partial card is no longer expressible.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "cards"
NODE_SCRIPT = ROOT / "gl" / "card.mjs"
W, H = 1920, 1080


def size_for(text: str) -> int:
    """Type size from length. A 40-word quote at 46px is six lines and half the
    frame; stepping down two points a band keeps every card inside the same
    lower-left third without ever shrinking the text below comfortable."""
    n = len(text.split())
    if n <= 22:
        return 48
    if n <= 30:
        return 44
    return 40


def renderer_sig() -> tuple:
    """Identity of the renderer itself.

    The FIRST version of this hash covered only (text, credit, size). Editing
    gl/card.mjs then left every cached PNG stale with an unchanged name, and
    build5's piece fingerprint keys on the PNG's name - so a renderer change
    would have gone into the film invisibly. That exact trap has cost this
    project three builds (see motion.renderer_sig, build5.still_sig). The
    renderer's mtime is part of the content.
    """
    f = NODE_SCRIPT
    return (f.name, int(f.stat().st_mtime))


def card_path(text: str, credit: str) -> Path:
    """Content-addressed, and the content is the FINISHED card - no fraction.

    Named q_<hash>.png the way the old cards were, but the hash now covers only
    things that change the picture. Two shots showing the same quote resolve to
    the same file, which is the mechanical reason a prefix can no longer reach
    the screen: there is only one rendering of a quote in existence.
    """
    sig = json.dumps([text, credit, size_for(text), W, H, 60, renderer_sig()],
                     ensure_ascii=False)
    return OUT / f"q_{hashlib.sha1(sig.encode('utf-8')).hexdigest()[:12]}.png"


def quote_card(text: str, credit: str, out: Path | None = None) -> Path:
    """Render one quote card as a full-frame transparent PNG.

    One browser launch per card, ~1.6s. There are nine in the film and they are
    cached in cards/, so a rebuild pays nothing.
    """
    out = Path(out) if out is not None else card_path(text, credit)
    box = out.with_suffix(".json")
    if out.exists() and box.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    job = [{"out": str(out).replace("\\", "/"),
            "box": str(box).replace("\\", "/"),
            "text": text, "credit": credit,
            "size": size_for(text), "width": 60, "w": W, "h": H}]
    jf = OUT / "_job.json"
    OUT.mkdir(exist_ok=True)
    jf.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(["node", str(NODE_SCRIPT), str(jf)],
                       cwd=str(NODE_SCRIPT.parent), capture_output=True, text=True)
    if r.returncode or not out.exists():
        raise RuntimeError(f"card render failed: {r.stderr[-600:]}")
    return out


def card_box(out: Path) -> tuple[int, int, int, int]:
    """(x, y, w, h) of the drawn card inside the 1920x1080 frame."""
    d = json.loads(Path(out).with_suffix(".json").read_text(encoding="utf-8"))
    return d["x"], d["y"], d["w"], d["h"]


def prune(keep) -> int:
    """Delete every card in cards/ that is not in `keep`.

    A stale card cannot reach the film - build5 composites the Path that
    `quote_card` HANDS BACK, never whatever is lying in the directory - but
    this project has been burned three times by trusting a directory listing,
    and 73 half-sentence PNGs from the reveal era were sitting here at the
    start of this pass. Leaving retired cards around is an invitation to
    verify last week's picture.

        python -c "import quotecards,cards; cards.prune([cards.card_path(v['text'],v['credit']) for v in quotecards.slate().values()])"
    """
    keep = {Path(k).resolve() for k in keep}
    n = 0
    for f in OUT.glob("q_*.*"):
        if f.with_suffix(".png").resolve() not in keep:
            f.unlink()
            n += 1
    return n
