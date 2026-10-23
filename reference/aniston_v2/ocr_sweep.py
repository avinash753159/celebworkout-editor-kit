"""Find burned-in FOREIGN text in the finished cut, mechanically.

Why this exists: every graphics defect the V6 audit turned up by eye was TEXT
burned into somebody else's footage - a Page Six headline card, an InStyle
logo, a Vital Proteins product super, LAD BIBLE cards, MONDAYS WITH MARLO,
TURNER CLASSIC MOVIES. Reading contact sheets finds them, but it found them
across 11 of 17 sheets because that is as far as a person gets. OCR reads all
257.

It does not replace looking. It cannot see that a woman is not Aniston, that a
pose is not a hip abduction, or that a shot is pillarboxed - the three defect
classes that need eyes. It catches exactly one class, and it catches all of it.

Method: pull one frame per shot from the film, OCR it, then subtract the text
the film puts there ITSELF - day cards, food lists, movement cards, place
cards, quote cards, bite credits, the endcard. Whatever survives is foreign.

    python3 ocr_sweep.py            # writes qc/OCR_SWEEP.md
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILM = ROOT / "JENNIFER_ANISTON_V6.mp4"
FRAMES = ROOT / "qc" / "ocr"
OUT = ROOT / "qc" / "OCR_SWEEP.md"

sys.path.insert(0, str(ROOT))
from script4 import BITES, FOODS, WEEK  # noqa: E402
import quotecards as QC  # noqa: E402


def own_text() -> tuple[set[str], str]:
    """Everything the film burns in on purpose.

    Returned twice: as words, and as one de-spaced blob. OCR reads a card as
    "3SETSOF10EACHSIDE" with the spaces gone, so word matching alone reports
    the film's own movement cards as foreign text. Substring matching against
    the blob is what actually subtracts them.
    """
    words: set[str] = set()
    phrases: list[str] = []

    def add(s: str) -> None:
        phrases.append(str(s))
        for w in re.findall(r"[A-Za-z']+", str(s).upper()):
            if len(w) > 2:
                words.add(w)

    for day, label, dur, moves in WEEK:
        add(day); add(label)
        for mv, reps in moves:
            add(mv); add(reps)
    for cat, items in FOODS:
        add(cat)
        for it in items:
            add(it)
    # the film's own quote cards, from the ledger - not from a
    # hardcoded copy that can drift out of step with what is rendered
    for v in QC.slate().values():
        add(v['text']); add(v['credit'])
    for vid, t0, t1, credit, text in BITES.values():
        add(credit)
    add("NEW YORK CITY SHE WAS SIX RUDOLF STEINER SCHOOL UPPER EAST SIDE")
    add("LAGUARDIA THE FAME SCHOOL LOS ANGELES SIX YEARS BEFORE FRIENDS")
    add("SHERMAN OAKS CALIFORNIA CELEB WORKOUT TRAIN LIKE THE ICONS")
    add("REST DAY SETS OF EACH SIDE MINUTES SECONDS REPS")
    blob = "|" + "|".join(re.sub(r"[^A-Z]", "", x.upper()) for x in phrases) + "|"
    return words, blob


def frame_for(t: float, dur: float, out: Path) -> Path:
    """Mid-shot frame - the same sampling point the contact sheets use.

    The cache is keyed on the FILM's mtime, the way contact_sheet.py does it.
    Keyed on shot index alone, a rebuild re-serves the previous cut's frames
    and the sweep reports the OLD film - the same trap that had build_audio
    handing back a stale mix because the only test was "exists and > 600s".
    """
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t + dur / 2:.3f}",
                        "-i", str(FILM), "-frames:v", "1", str(out)], check=True)
    return out


def main() -> None:
    if not FILM.exists():
        raise SystemExit(f"no film at {FILM}")
    FRAMES.mkdir(parents=True, exist_ok=True)
    rows = json.loads((ROOT / "manifest" / "shot_transcript.json").read_text(encoding="utf-8"))
    rows = rows if isinstance(rows, list) else rows.get("shots", rows)

    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    mine, blob = own_text()
    stamp = f"{int(FILM.stat().st_mtime)}"

    findings = []
    for r in rows:
        i, t, dur, tag = r["i"], r["t"], r["dur"], r["tag"]
        # a still we generated cannot carry someone else's chyron
        if str(tag).startswith(("still:", "split:")):
            continue
        f = frame_for(t, dur, FRAMES / f"s{i:03d}_{stamp}.jpg")
        res, _ = ocr(str(f))
        foreign = []
        for det in (res or []):
            txt, conf = det[1], float(det[2])
            if conf < 0.60:
                continue
            flat = re.sub(r"[^A-Z]", "", txt.upper())
            if len(flat) < 3:
                continue
            # ours if the de-spaced detection sits inside anything we burn in
            if flat in blob:
                continue
            toks = [w for w in re.findall(r"[A-Za-z']+", txt.upper()) if len(w) > 2]
            if toks and not any(w in mine for w in toks):
                foreign.append((txt.strip(), conf))
        if foreign:
            findings.append((i, t, tag, r.get("block", "?"), foreign))
        if i % 40 == 0:
            print(f"  ...shot {i}/{len(rows)}")

    lines = ["# OCR sweep - foreign burned-in text",
             "",
             f"Film: `{FILM.name}` - {len(rows)} shots, "
             f"{sum(1 for r in rows if not str(r['tag']).startswith(('still:', 'split:')))} "
             "carrying real footage (generated stills skipped).",
             "",
             "Text the film burns in itself (day cards, food lists, movement cards,",
             "place cards, quote cards, bite credits, endcard) is subtracted. What is",
             "listed below is text that came in with somebody else's footage.",
             "",
             f"**{len(findings)} shots carry foreign text.**", ""]
    for i, t, tag, block, foreign in findings:
        m, s = int(t) // 60, t % 60
        lines.append(f"- **shot {i}** @ {m}:{s:05.2f} · `{tag}` · block {block}")
        for txt, conf in foreign[:6]:
            lines.append(f"    - `{txt}`  ({conf:.2f})")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(findings)} shots with foreign text -> {OUT}")


if __name__ == "__main__":
    main()
