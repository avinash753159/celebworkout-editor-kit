"""Measure cut-continuity for every window a build can reach.

`clear_seconds` returns 99.0 for a window with no cut data - a "no data"
default, not a measurement. Trusting it let a 6.2s shot on vMuarx9iWdg@860.6
run past a cut into Vince Vaughn: both sampled ends scored as her, because the
mid check only looks at t+1.6s and 4.6s of that shot were never examined.

build5._fits now measures on demand, but doing it inside the build makes the
first build after a source harvest far too slow. This does it up front, in
resumable chunks.

    python3 premeasure.py [seconds_budget]
"""
import json
import sys
import time
from pathlib import Path

import cuts
import reels5 as R

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "manifest" / "cuts.json"

budget = float(sys.argv[1]) if len(sys.argv) > 1 else 540.0
have = json.loads(OUT.read_text(encoding="utf-8"))

want = []
for pool in R.POOLS.values():
    for vid, t in pool:
        if str(vid).startswith(("still:", "split:")):
            continue
        if f"{vid}@{t:.2f}" not in have:
            want.append((vid, round(t, 2)))
want = sorted(set(want))
print(f"  {len(want)} pool windows unmeasured")

t0 = time.time()
done = 0
for vid, t in want:
    if time.time() - t0 > budget:
        break
    have[f"{vid}@{t:.2f}"] = cuts.spike(vid, t)
    done += 1
    if done % 50 == 0:
        OUT.write_text(json.dumps(have), encoding="utf-8")
        print(f"    {done}/{len(want)}", flush=True)
OUT.write_text(json.dumps(have), encoding="utf-8")
print(f"  measured {done}, {len(want) - done} left")
