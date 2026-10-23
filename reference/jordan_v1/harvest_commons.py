"""Broad Commons harvest -> identity filter -> eyeball. Real files, real names."""
import json, re, sys
from pathlib import Path
import fetch_photos as F

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAW = Path("photos_raw"); RAW.mkdir(exist_ok=True)

QUERIES = [
    "Michael Jordan Lipofsky", "Michael Jordan 1984 Bulls", "Michael Jordan 1985",
    "Michael Jordan 1987 dunk", "Michael Jordan 1988", "Michael Jordan 1990",
    "Michael Jordan 1991 Bulls", "Michael Jordan 1993", "Michael Jordan 1997",
    "Michael Jordan 1998 Bulls", "Michael Jordan North Carolina 1983",
    "Michael Jordan Olympics 1984", "Michael Jordan dunk contest",
    "Scottie Pippen Lipofsky", "Scottie Pippen Bulls 1996", "Scottie Pippen 1992",
    "Ron Harper basketball Bulls", "Dennis Rodman Bulls",
    "Detroit Pistons 1990 Isiah Thomas", "Bill Laimbeer Pistons",
    "Dean Smith North Carolina", "Phil Jackson Bulls coach",
    "Chicago Bulls 1996 team", "basketball weight training gym",
]
seen, n = set(), 0
for q in QUERIES:
    try:
        titles = F.search(q, 10)
    except Exception as e:
        print(f"  {q[:38]:40s} search error {e}"); continue
    got = 0
    for t in titles:
        if not re.search(r"\.(jpe?g|png)$", t, re.I) or t in seen:
            continue
        seen.add(t)
        try:
            r = F.image_url(t, 1400)
        except Exception:
            continue
        if not r:
            continue
        slug = re.sub(r"[^a-z0-9]+", "_", q.lower())[:22]
        dest = RAW / f"cm_{slug}_{got:02d}.jpg"
        if F.download(r[0], dest):
            got += 1; n += 1
        if got >= 6:
            break
    print(f"  {q[:38]:40s} {got}", flush=True)
print(f"\n{n} new files; {len(list(RAW.glob('*.jpg')))} total in photos_raw/")
