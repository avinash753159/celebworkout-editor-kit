"""Second-wave fetch: real footage of HER, at the best resolution YouTube serves.

Two things changed since fetch.py:

1. `web_embedded` serves 720p/1080p where the android client caps at 360p.
   The old pool is 360p because that cap was mistaken for YouTube's limit.
2. The one-clip-per-source rule is gone, so a source is now worth downloading
   in full if it contains several usable moments rather than exactly one.

The pool below is chosen against a single question: is JENNIFER ANISTON
herself on screen doing the thing the narration is about? Sources where a
correspondent, a trainer or a spokesperson performs her routine in her place
are listed at the bottom as CONTEXT and are never cut as if they were her.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
RAW.mkdir(exist_ok=True)

# id, kind, holder, what
POOL = [
    # ── HER, training, official brand films (clean, no third-party bug)
    ("lrZKJPVn89s", "her_train", "Pvolve", "campaign: A Strength That Sets You Free"),
    ("JJLe4jmbrN0", "her_train", "Pvolve", "campaign: Worth It Every Time"),
    ("f8YLI3POJnM", "her_train", "Pvolve", "campaign: Strength Redefined"),
    ("C03vLBSWJN0", "her_train", "Pvolve", "Welcome to Pvolve"),
    ("d7hb5JTpbFE", "her_train", "Pvolve", "What is Pvolve"),
    ("voC2DxCL6jQ", "her_talk",  "Pvolve", "Aniston x founder Rachel Katzman interview"),
    ("qqipyG6bpLA", "her_train", "jenniferaniston", "her own fitness post"),
    ("f6zuX21_098", "her_train", "pyrmontbridge", "arms, close"),
    ("w2X4wxwB-qQ", "her_train", "TCP", "campaign coverage"),
    ("dADifrjs6Og", "her_train", "Celebrity N", "fitness ad footage"),

    # ── HER, the injury and the turn
    ("InUyN6CduEA", "her_talk", "Slam Motion", "broke her body doing too much"),

    # ── HER, on her body / fitness, older
    ("aZiwqY_e9ZQ", "her_talk", "InStyle",  "Get That Body: abs"),
    ("XYcNVESFs4Y", "her_talk", "E! News",  "the fitness secret"),
    ("ak5GBTYJArw", "her_talk", "ABC News", "fitness secrets revealed"),

    # ── CONTEXT: her trainers speaking about her. Never cut as her.
    ("zbCniZvVfgQ", "context", "TCP",         "trainer on her training at 56"),
    ("W2A_JiQgHrs", "context", "This Morning", "trainer reveals her fitness secrets"),
    ("zMLEopVAzEE", "context", "Vanity Fair",  "celebrity trainer on getting her in shape"),
]

ARGS = ["--no-warnings", "--extractor-args", "youtube:player_client=web_embedded",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/18",
        "--merge-output-format", "mp4", "--no-playlist"]


def playable(p: Path) -> float:
    if not p.exists() or p.stat().st_size < 60_000:
        return 0.0
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def probe_size(p: Path) -> str:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(p)],
        capture_output=True, text=True)
    return r.stdout.strip() or "?"


def main() -> None:
    ledger_path = ROOT / "manifest" / "raw2.json"
    ledger = {}
    ok = fail = 0
    for i, (vid, kind, holder, what) in enumerate(POOL, 1):
        dst = RAW / f"{vid}.mp4"
        have = playable(dst)
        if have > 3:
            print(f"  [{i:>2}/{len(POOL)}] {vid} cached {have:6.1f}s {probe_size(dst)}")
            ledger[vid] = {"seconds": have, "kind": kind, "holder": holder,
                           "what": what, "size": probe_size(dst)}
            ok += 1
            continue

        cmd = ["yt-dlp", *ARGS, "-o", str(dst),
               f"https://www.youtube.com/watch?v={vid}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        dur = playable(dst)
        if dur > 3:
            sz = probe_size(dst)
            print(f"  [{i:>2}/{len(POOL)}] {vid} ok     {dur:6.1f}s {sz:>9}  {holder}")
            ledger[vid] = {"seconds": dur, "kind": kind, "holder": holder,
                           "what": what, "size": sz}
            ok += 1
        else:
            tail = (r.stderr or r.stdout or "").strip().splitlines()
            print(f"  [{i:>2}/{len(POOL)}] {vid} FAIL   "
                  f"{tail[-1][:80] if tail else '?'}")
            dst.unlink(missing_ok=True)
            fail += 1

    ledger_path.write_text(json.dumps(ledger, indent=1), encoding="utf-8")
    her = sum(v["seconds"] for v in ledger.values() if v["kind"].startswith("her"))
    print(f"\n  {ok} downloaded, {fail} failed")
    print(f"  {her/60:.1f} min of HER on camera added")
    if ok < 8:
        print("  TOO THIN - not enough new real footage, stopping")
        sys.exit(1)


if __name__ == "__main__":
    main()
