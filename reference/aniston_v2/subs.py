"""Turn YouTube auto-caption VTT into clean timed lines.

Auto-captions arrive as a rolling window: each cue repeats the tail of the
previous one so the text scrolls. Read naively you get every phrase three or
four times. This keeps only newly-added words and stamps each with the time it
first appeared, which is what a bite in-point needs.

These timings LOCATE a bite. They do not cut one - the in-point still gets
eyeballed on a frame before it goes in the film.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TS = re.compile(r"(\d\d):(\d\d):(\d\d)\.(\d\d\d)\s+-->\s+(\d\d):(\d\d):(\d\d)\.(\d\d\d)")
TAG = re.compile(r"<[^>]+>")


def secs(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse(path: Path) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    seen: list[str] = []
    t = None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = TS.match(line.strip())
        if m:
            t = secs(*m.groups()[:4])
            continue
        if t is None or not line.strip():
            continue
        txt = TAG.sub("", line).strip()
        if not txt or txt.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        words = txt.split()
        # drop the leading overlap with what we already emitted
        tail = " ".join(seen[-40:])
        new = words
        for k in range(len(words), 0, -1):
            if tail.endswith(" ".join(words[:k])):
                new = words[k:]
                break
        if new:
            out.append((t, " ".join(new)))
            seen += new
    return out


def blocks(lines: list[tuple[float, str]], gap: float = 2.5) -> list[tuple[float, str]]:
    """Join adjacent lines into sentence-ish blocks for readability."""
    out: list[tuple[float, str]] = []
    for t, txt in lines:
        if out and t - out[-1][0] < gap and not out[-1][1].rstrip().endswith((".", "?", "!")):
            out[-1] = (out[-1][0], out[-1][1] + " " + txt)
        else:
            out.append((t, txt))
    return out


def main() -> None:
    for vid in sys.argv[1:]:
        p = ROOT / "subs" / f"{vid}.en.vtt"
        if not p.exists():
            p = ROOT / "subs" / f"{vid}.en-orig.vtt"
        if not p.exists():
            print(f"### {vid}  NO CAPTIONS")
            continue
        print(f"\n### {vid}")
        for t, txt in blocks(parse(p)):
            print(f"[{int(t)//60:02d}:{t%60:05.2f}] {txt}")


if __name__ == "__main__":
    main()
