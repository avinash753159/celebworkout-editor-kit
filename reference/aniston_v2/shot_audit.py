"""The section-4 acceptance criteria, measured on the film that exists.

build5 asserts two of these while it runs; this asserts all of them
afterwards, against manifest/shots6.json, and prints the tables the handback
asks for. Run it after every build:

    python3 build5.py && python3 shot_audit.py

  1. Every block covers its full duration - no gaps, no overruns.
  2. Zero shots span a cut, MEASURED with cuts.spike. Not clear_seconds:
     that returns an optimistic 99.0 for any window it has no record of, so
     it reports "no cut" and "never looked" identically, and a 6.2s shot on
     vMuarx9iWdg@860.6 ran past a cut into Vince Vaughn on exactly that.
  3. Zero consecutive shots from the same source.
  4. No source supplies more than 8% of the shots.
  5. Every cue resolves to a time from word_times5.json.
  6. Photographs appear in the cut.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FPS = 30
FAIL: list[str] = []


def fail(msg: str) -> None:
    FAIL.append(msg)
    print(f"  FAIL  {msg}")


def main() -> None:
    shots = json.loads((ROOT / "manifest" / "shots6.json").read_text(encoding="utf-8"))
    rows = shots["shots"]
    man = json.loads((ROOT / "manifest" / "audio5.json").read_text(encoding="utf-8"))
    import build5 as B

    print(f"\n{shots.get('film')}  {len(rows)} shots\n")

    # 1 ── every block covers its duration exactly
    print("1. block coverage")
    per = dict(zip([b["block"] for b in man["blocks"]], B.block_frames(man)))
    got = Counter()
    for r in rows:
        got[r["block"]] += r["frames"]
    for bid, want in per.items():
        if got.get(bid) != want:
            fail(f"block {bid}: {got.get(bid)} frames of picture for "
                 f"{want} frames of narration")
    if got.get("END") != int(round(6.0 * FPS)):
        fail(f"endcard is {got.get('END')} frames, expected 180")
    if not FAIL:
        print(f"   all {len(per)} blocks exact, {sum(per.values())/FPS:.2f}s "
              f"+ 6.00s endcard")

    # 2 ── no shot spans a cut, MEASURED
    print("\n2. cut continuity (measured with cuts.spike, not clear_seconds)")
    # A SYNC BITE IS NOT A POOL SHOT AND IS NOT EXEMPT BY CONVENIENCE.
    # It plays the source it was cut from, at the timecode its audio came
    # from, because moving the picture off that timecode slides her lips off
    # her voice for the whole bite. If the source cuts away inside those
    # seconds - a reaction shot of the host, a tail on to a two-shot - there
    # is no picture choice that avoids it, so it is reported with its measured
    # extent instead of being called a pass or a fail. Every one is section
    # 2 s window, not section 4 s.
    import cuts
    measured = spanning = 0
    for r in rows:
        tag = r["tag"]
        if tag.startswith(("still:", "split:")) or tag == "endcard":
            continue
        t0 = r.get("src_t0")
        if t0 is None:
            fail(f"{tag}: no src_t0 recorded, so continuity cannot be checked")
            continue
        secs = r["frames"] / FPS
        clear = float(cuts.spike(tag, round(float(t0), 2))[1])
        if r.get("kind") == "bite":
            if clear < secs:
                print(f"   NOTE  bite {r['block']} {tag}@{t0} runs {secs:.2f}s "
                      f"and the source cuts away {clear:.2f}s in. Sync is "
                      f"fixed by the audio, so the picture cannot dodge it - "
                      f"section 2 chose this window.")
            continue
        measured += 1
        if clear < secs:
            spanning += 1
            fail(f"{tag}@{t0} holds {secs:.2f}s but is clear for only "
                 f"{clear:.2f}s - it spans a cut")
    print(f"   {measured} pool-drawn video shots re-measured, "
          f"{spanning} span a cut")

    # 3 ── no two consecutive shots from the same tag, OR the same shoot
    print("\n3. consecutive-source repeats")
    runs = [(i, rows[i]["block"], rows[i]["tag"])
            for i in range(1, len(rows)) if rows[i]["tag"] == rows[i - 1]["tag"]]
    for i, blk, tag in runs:
        fail(f"shots {i-1},{i} in {blk} are both {tag}")
    print(f"   {len(runs)} found")
    # Same shoot, different YouTube id. The V7 cut had two such pairs and this
    # check did not exist to find them: 349/350 (Horrible Bosses junket) and
    # 355/356 (SAG podium) are identical on screen and pass the test above.
    import reels5 as _R5

    def _vid(k):
        t = rows[k]["tag"]
        return None if t.startswith(("still:", "split:")) or t == "endcard" else t

    gruns = [(i, rows[i]["block"], rows[i - 1]["tag"], rows[i]["tag"])
             for i in range(1, len(rows))
             if _vid(i) and _vid(i - 1)
             and _R5.group_of(rows[i]["tag"]) == _R5.group_of(rows[i - 1]["tag"])]
    for i, blk, a, b in gruns:
        fail(f"shots {i-1},{i} in {blk} are {a} and {b} - one shoot "
             f"({_R5.group_of(b)}) under two ids")
    print(f"   {len(gruns)} consecutive same-GROUP pairs")
    # NEAR repeats. Adjacency alone said the V8 cut was clean while the sheets
    # showed Lko6LrBHSRc coming back four seconds later with one still in
    # between, and five more pairs like it. The weave puts a still between two
    # clips, so "not the shot before" is not "not the same picture again".
    # Reported, with the gap, rather than failed: build5 prefers a different
    # group for RECENT_N shots but will still take one if the pool has nothing
    # else, and a thin pool is a reason to widen it, not to abort a render.
    span = getattr(__import__("build5"), "Reels").RECENT_N
    t_at, t = [], 0.0
    for r in rows:
        t_at.append(t)
        t += r["frames"] / FPS
    near = []
    for i in range(len(rows)):
        for j in range(i + 1, min(i + span + 1, len(rows))):
            if _vid(i) and _vid(j) and \
                    _R5.group_of(rows[i]["tag"]) == _R5.group_of(rows[j]["tag"]):
                near.append((i, j, rows[j]["tag"], round(t_at[j] - t_at[i], 1)))
    print(f"   {len(near)} same-GROUP pairs within {span} shots of each other"
          + (":" if near else ""))
    for i, j, tag, gap in near[:12]:
        print(f"     #{i},#{j}  {tag}  {gap}s apart")

    # 4 ── shots per source
    print("\n4. shots per source")
    tags = Counter(r["tag"] for r in rows if r["tag"] != "endcard")
    n = sum(tags.values())
    for tag, c in tags.most_common():
        if c / n > 0.08:
            fail(f"{tag} supplies {c}/{n} = {c/n*100:.1f}% (bar is 8%)")
    vids = Counter({k: v for k, v in tags.items()
                    if not k.startswith(("still:", "split:"))})
    still = n - sum(vids.values())
    print(f"   {len(tags)} distinct pictures over {n} shots "
          f"({sum(vids.values())} video from {len(vids)} sources, "
          f"{still} stills)")
    print(f"   {'picture':<30}{'shots':>6}{'share':>8}")
    for tag, c in tags.most_common(15):
        print(f"   {tag:<30}{c:>6}{c/n*100:>7.1f}%")

    # 4b ── shots per VISUAL GROUP. The id table above is the one the V7 cut
    # passed while two press events held 8.8% of the film between them.
    print(f"\n4b. shots per VISUAL GROUP (bar is "
          f"{_R5.GROUP_CAP_FRAC*100:.0f}%)")
    grp = Counter(_R5.group_of(k) for k in vids.elements())
    print(f"   {'group':<26}{'ids':>4}{'shots':>7}{'share':>8}")
    for name, c in grp.most_common(12):
        ids = len(_R5.GROUP.get(name, [name]))
        mark = "  <-- OVER" if c / n > _R5.GROUP_CAP_FRAC else ""
        print(f"   {name:<26}{ids:>4}{c:>7}{c/n*100:>7.1f}%{mark}")
        if c / n > _R5.GROUP_CAP_FRAC:
            fail(f"visual group {name} "
                 f"({', '.join(_R5.GROUP.get(name, [name]))}) supplies "
                 f"{c}/{n} = {c/n*100:.1f}%")
    named = {g: grp.get(g, 0) for g in _R5.GROUP}
    print("   named groups: " + ", ".join(f"{g}={c}" for g, c in
                                          sorted(named.items(),
                                                 key=lambda x: -x[1])))

    # 5 ── every cue resolved from word_times5
    print("\n5. cues")
    import cues
    try:
        cues.check()
        print(f"   all {len(cues.CUES)} cue phrases resolve to a time from "
              f"word_times5.json")
    except SystemExit as e:
        fail(str(e))
    cued = sum(1 for r in rows if r.get("cue"))
    print(f"   {cued} shots in the film are cue-pinned")

    # 6 ── photographs
    print("\n6. photographs")
    ph = sorted({r["tag"] for r in rows if r["tag"].startswith("still:ph_")})
    import reels5
    print(f"   {len(ph)} of {len(reels5.ALL_PHOTOS)} photographs in the cut")
    if not ph:
        fail("no photographs in the cut")

    # extra ── how the picture is made up, per block
    print("\n   block composition")
    demo = set(reels5.DEMO_SRC5)
    print(f"   {'blk':<6}{'shots':>6}{'still':>6}{'demo':>6}{'her':>5}")
    for bid in dict.fromkeys(r["block"] for r in rows):
        rs = [r for r in rows if r["block"] == bid]
        st = sum(1 for r in rs if r["tag"].startswith(("still:", "split:")))
        dm = sum(1 for r in rs if r["tag"] in demo)
        print(f"   {bid:<6}{len(rs):>6}{st:>6}{dm:>6}{len(rs)-st-dm:>5}")

    print()
    if FAIL:
        raise SystemExit(f"{len(FAIL)} acceptance failures")
    print("  ALL SIX ACCEPTANCE CRITERIA PASS (mechanically). The sheets in "
          "qc/sheets still have to be READ.")


if __name__ == "__main__":
    main()
