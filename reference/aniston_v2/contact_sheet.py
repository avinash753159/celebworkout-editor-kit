"""One labelled frame per shot, tiled, with the words spoken over it.

This is the audit. A number improving is not verification - every defect that
mattered in this project was found by looking at a frame and not by measuring
anything. Run transcript.py first, then this, then READ the sheets.

    python3 build5.py && python3 transcript.py && python3 contact_sheet.py

Writes qc/sheets/S00..S21.jpg, sixteen shots each.
"""
import json, subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SCR  = ROOT / "qc"
# Keyed on the FILM's mtime. Keying on shot index alone meant a rebuild with a
# different shot count silently reused the previous cut's frames, and the sheet
# showed a spin bike under a glute-bridge label that the film did not contain.
# A stale audit is worse than no audit.
# The film's name comes from build5, not from a literal. This file used to
# hardcode JENNIFER_ANISTON_V6.mp4 and key its frame cache on that file's
# mtime, so pointing the build at a new output silently produced sheets of the
# OLD cut - stale-audit, the bug that has bitten this project three times.
#
# FILM= overrides it. build5.OUT moves when a pass produces a new cut, and an
# audit of the film that is on disk must not become impossible the moment
# somebody points the assembler at the next name.
import os
import build5 as _B
MP4  = Path(os.environ["FILM"]) if os.environ.get("FILM") else _B.OUT
if not MP4.exists():
    raise SystemExit(f"contact_sheet: {MP4.name} does not exist - build it "
                     f"before auditing it.")
# Keyed on the film's NAME and mtime. Name alone let a rebuild reuse the
# previous cut's frames; mtime alone let two different films share a cache
# directory if they happened to be written in the same second.
TMP  = SCR / "frames" / f"{MP4.stem}_{int(MP4.stat().st_mtime)}"
TMP.mkdir(parents=True, exist_ok=True)
OUT  = SCR/"sheets"; OUT.mkdir(parents=True, exist_ok=True)
# A shorter film leaves the previous cut's trailing sheets on disk, and a
# reviewer reads them as part of this cut.
for _old in OUT.glob("S*.jpg"):
    _old.unlink()

T = json.load(open(ROOT/"manifest/shot_transcript.json"))
_shots = json.load(open(ROOT/"manifest/shots6.json"))
if _shots.get("film") and _shots["film"] != MP4.name:
    raise SystemExit(f"contact_sheet: shots6.json describes {_shots['film']} "
                     f"but the film is {MP4.name}. Re-run build5.")
if len(T) != len(_shots["shots"]):
    raise SystemExit(f"contact_sheet: the transcript has {len(T)} shots and "
                     f"the film has {len(_shots['shots'])}. Re-run "
                     f"transcript.py.")
# midpoint of each shot
mids = []
for k,r in enumerate(T):
    nxt = T[k+1]["t"] if k+1 < len(T) else r["t"]+2.0
    mids.append(min(r["t"] + max(0.35,(nxt-r["t"])*0.45), nxt-0.1 if nxt>r["t"] else r["t"]+0.4))

W,H = 440,248
LBL = 74
todo=[]
for k,r in enumerate(T):
    p = TMP/f"f{k:03d}.jpg"
    if not p.exists(): todo.append((mids[k],p))
# batch extract
for t,p in todo:
    subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{t:.2f}","-i",str(MP4),
                    "-frames:v","1","-vf",f"scale={W}:{H}",str(p)],check=False)

try:
    F  = ImageFont.truetype("arialbd.ttf",16)
    Fs = ImageFont.truetype("arial.ttf",14)
except Exception:
    F=Fs=ImageFont.load_default()

COLS,ROWS = 4,4
per = COLS*ROWS
n = len(T)
for s in range(0,n,per):
    chunk = list(range(s,min(s+per,n)))
    sheet = Image.new("RGB",(COLS*W,((len(chunk)+COLS-1)//COLS)*(H+LBL)),(8,8,10))
    d = ImageDraw.Draw(sheet)
    for j,k in enumerate(chunk):
        x=(j%COLS)*W; y=(j//COLS)*(H+LBL)
        p=TMP/f"f{k:03d}.jpg"
        im = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB",(W,H),(70,0,0))
        sheet.paste(im,(x,y+LBL))
        r=T[k]
        d.text((x+5,y+3), f"#{k}  {r['t']:.1f}s  [{r['block']}]  {r['tag'][:22]}", font=F, fill=(255,225,110))
        wrapped = textwrap.wrap(r["says"] or "-", 58)[:2]
        for li,ln in enumerate(wrapped):
            d.text((x+5,y+24+li*17), ln, font=Fs, fill=(200,230,255))
        d.rectangle([x,y,x+W-1,y+H+LBL-1], outline=(45,45,55))
    o=OUT/f"S{s//per:02d}_{s:03d}.jpg"
    sheet.save(o, quality=85)
print("sheets:", len(list(OUT.glob('*.jpg'))))
