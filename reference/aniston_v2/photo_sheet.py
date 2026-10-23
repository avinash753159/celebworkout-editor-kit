"""Contact sheets for photos/ - the eye-audit QC artifact for Section 3.

Every photograph is labelled with its hash id (read from manifest/photos.json,
never from a rendered label) and its query, so a ban can be written back
against data. Writes qc/PHOTOS_0..N.jpg, 12 tiles each.

    python3 photo_sheet.py
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT / "photos"
OUT = ROOT / "qc"
LEDGER = json.loads((ROOT / "manifest" / "photos.json").read_text(encoding="utf-8"))

W, H = 320, 320
LBL = 46
COLS, ROWS = 4, 3
PER = COLS * ROWS

try:
    F = ImageFont.truetype("arialbd.ttf", 14)
    Fs = ImageFont.truetype("arial.ttf", 12)
except Exception:
    F = Fs = ImageFont.load_default()

items = sorted(LEDGER["by_hash"].items())  # (hash, {file, query, url, w, h})
print(f"{len(items)} photographs in manifest")

for s in range(0, len(items), PER):
    chunk = items[s:s + PER]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * W, rows * (H + LBL)), (8, 8, 10))
    d = ImageDraw.Draw(sheet)
    for j, (h, rec) in enumerate(chunk):
        x = (j % COLS) * W
        y = (j // COLS) * (H + LBL)
        p = PHOTOS / rec["file"]
        if p.exists():
            im = Image.open(p).convert("RGB")
            im.thumbnail((W, H))
            ox = x + (W - im.width) // 2
            oy = y + LBL + (H - im.height) // 2
            sheet.paste(im, (ox, oy))
        else:
            d.rectangle([x, y + LBL, x + W, y + LBL + H], fill=(70, 0, 0))
        d.text((x + 4, y + 2), f"{h}", font=F, fill=(255, 225, 110))
        d.text((x + 4, y + 18), f"{rec['query'][:34]}", font=Fs, fill=(200, 230, 255))
        d.text((x + 4, y + 32), f"{rec['w']}x{rec['h']}", font=Fs, fill=(160, 160, 170))
        d.rectangle([x, y, x + W - 1, y + H + LBL - 1], outline=(45, 45, 55))
    o = OUT / f"PHOTOS_{s // PER}.jpg"
    sheet.save(o, quality=88)
    print("wrote", o)
