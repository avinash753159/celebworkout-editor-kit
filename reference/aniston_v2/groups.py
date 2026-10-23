"""Which SOURCE IDS are the same shoot - and what share of the film each
shoot holds.

The 8% cap and the consecutive-source rule both key on the YouTube id, and a
press junket is uploaded by six outlets under six ids. Measured on the V7 cut:
`hPX9_UV478Q` + `iwiHdFYJf9k` + `6B7lM_DGMqA` are one Horrible Bosses junket -
same backdrop, same day, same dress - and between them held 18 shots, 4.9% of
the film, with two of them CONSECUTIVE. The id-level numbers were all green.

Two jobs:

  propose   cluster the sources in the cut by CLIP similarity of the windows
            the cut actually used, and render qc/groups/*.jpg so the pairs can
            be CONFIRMED BY EYE. A number does not make two ids the same
            shoot; a picture does. Nothing here writes reels5.GROUP.
  report    the shots-per-group table for the current manifest, using
            reels5.GROUP - the list a human confirmed.

    python3 groups.py propose      # candidates + sheets to look at
    python3 groups.py report       # the table
"""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "manifest" / "shots6.json"
NPZ = ROOT / "manifest" / "clip.npz"
OUT = ROOT / "qc" / "groups"
TMP = ROOT / "qc" / "srcstrip"

# Two ids are proposed as one shoot when this fraction of one's windows has a
# twin in the other above MATCH. Tuned on the two junkets the owner named:
# both clear 0.40, and the pair that is merely "two talk shows with a beige
# set" does not.
MATCH = 0.90
FRAC = 0.30


def used(rows) -> dict:
    u = defaultdict(list)
    for r in rows:
        t = r["tag"]
        if t.startswith(("still:", "split:")) or t == "endcard":
            continue
        u[t].append(float(r["src_t0"]))
    return u


def propose() -> None:
    import numpy as np
    rows = json.loads(SHOTS.read_text(encoding="utf-8"))["shots"]
    u = used(rows)
    d = np.load(NPZ, allow_pickle=True)
    V, K = d["vecs"], d["keys"].tolist()
    byv = defaultdict(list)
    for i, k in enumerate(K):
        v, _, _t = k.rpartition("@")
        if not v.startswith("still:"):
            byv[v].append(V[i])
    mats = {s: np.array(byv[s]) for s in u if byv.get(s)}
    pairs = []
    for a, b in itertools.combinations(sorted(mats), 2):
        S = mats[a] @ mats[b].T
        f = max(float((S.max(axis=1) >= MATCH).mean()),
                float((S.max(axis=0) >= MATCH).mean()))
        if f >= FRAC:
            pairs.append((f, float(S.max()), a, b))
    pairs.sort(reverse=True)
    print(f"\ncandidate same-shoot pairs (>= {FRAC:.0%} of one side's windows "
          f"match the other above {MATCH})\n")
    for f, mx, a, b in pairs:
        print(f"  {f:5.0%}  max {mx:.3f}   {a} ({len(u[a])} shots) "
              f"~ {b} ({len(u[b])} shots)")
    # union-find so the sheets show whole candidate clusters together
    par = {s: s for s in mats}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for _f, _mx, a, b in pairs:
        par[find(a)] = find(b)
    cl = defaultdict(list)
    for s in mats:
        cl[find(s)].append(s)
    clusters = sorted([v for v in cl.values() if len(v) > 1], key=len, reverse=True)
    print(f"\n{len(clusters)} candidate clusters. LOOK at them:")
    for c in clusters:
        print("   " + " ".join(sorted(c)) +
              f"   = {sum(len(u[s]) for s in c)} shots")
    _sheets(u, clusters)


def _sheets(u, clusters) -> None:
    from PIL import Image, ImageDraw, ImageFont
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    W, H, LBL, N = 300, 169, 22, 3
    try:
        F = ImageFont.truetype("arialbd.ttf", 13)
    except Exception:
        F = ImageFont.load_default()
    for ci, c in enumerate(clusters):
        cells = []
        for s in sorted(c):
            ts = sorted(set(u[s]))
            pick = ([ts[i * len(ts) // N] for i in range(N)]
                    if len(ts) >= N else (ts * N)[:N])
            for t in pick:
                p = TMP / f"{s}_{t:.2f}.jpg"
                if not p.exists():
                    subprocess.run(
                        ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}",
                         "-i", f"hd/{s}.mp4", "-frames:v", "1",
                         "-vf", f"scale={W}:{H}", str(p)],
                        cwd=str(ROOT), check=False)
                cells.append((s, t, len(u[s]), p))
        cols = N
        rows_n = (len(cells) + cols - 1) // cols
        im = Image.new("RGB", (cols * W, rows_n * (H + LBL)), (10, 10, 12))
        d = ImageDraw.Draw(im)
        for j, (s, t, n, p) in enumerate(cells):
            x, y = (j % cols) * W, (j // cols) * (H + LBL)
            f = (Image.open(p).convert("RGB") if p.exists()
                 else Image.new("RGB", (W, H), (80, 0, 0)))
            im.paste(f, (x, y + LBL))
            d.text((x + 4, y + 4), f"{s} @{t:.1f}  [{n} shots]", font=F,
                   fill=(255, 220, 110))
            d.rectangle([x, y, x + W - 1, y + H + LBL - 1], outline=(50, 50, 60))
        im.save(OUT / f"G{ci:02d}.jpg", quality=88)
    print(f"  -> {len(clusters)} sheets in qc/groups/")


def report() -> None:
    import reels5
    rows = json.loads(SHOTS.read_text(encoding="utf-8"))["shots"]
    tags = [r["tag"] for r in rows if r["tag"] != "endcard"]
    n = len(tags)
    g = Counter(reels5.group_of(t) for t in tags
                if not t.startswith(("still:", "split:")))
    print(f"\n  shots per VISUAL GROUP ({n} shots in the film)\n")
    print(f"  {'group':<26}{'ids':>4}{'shots':>7}{'share':>8}")
    bad = []
    for name, c in g.most_common(18):
        ids = len(reels5.GROUP.get(name, [name]))
        print(f"  {name:<26}{ids:>4}{c:>7}{c / n * 100:>7.1f}%")
        if c / n > reels5.GROUP_CAP_FRAC:
            bad.append((name, c))
    adj = [(i, tags[i]) for i in range(1, len(tags))
           if not tags[i].startswith(("still:", "split:"))
           and not tags[i - 1].startswith(("still:", "split:"))
           and reels5.group_of(tags[i]) == reels5.group_of(tags[i - 1])]
    print(f"\n  consecutive same-GROUP shots: {len(adj)}")
    for i, t in adj:
        print(f"    #{i-1},#{i}  {tags[i-1]} / {t}  "
              f"= {reels5.group_of(t)}")
    if bad:
        raise SystemExit("  group share over the cap: " + repr(bad))


if __name__ == "__main__":
    (report if (len(sys.argv) > 1 and sys.argv[1] == "report") else propose)()
