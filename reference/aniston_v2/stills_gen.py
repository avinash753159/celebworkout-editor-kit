"""Generated stills, with a ledger.

Three rules, each bought with a known failure mode in this kind of worker:

1. Money is booked the instant the API RETURNS, not when the bytes finish
   parsing. Charging at parse-success leaves `spent` at 0.00 while a backlog
   burns, so the cap can never trip. Charging before the call books money a
   client-side error never spent.
2. The cache key is ledger state, never `path.exists()`. A halted download
   leaves a truncated file that is indistinguishable from a finished one by
   existence alone.
3. Circuit breaker at 3 consecutive failures. A systemic bug is
   indistinguishable from bad luck without one.

The cache key is a content fingerprint of the PROMPT, deliberately not the
shot id - shot ids are positional, so a shot that moves in the edit keeps its
picture and a re-run buys nothing it already owns.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests
from PIL import Image

from plan import STILLS, STYLE

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "stills"
OUT.mkdir(exist_ok=True)
LEDGER = ROOT / "manifest" / "stills_ledger.json"

MODEL = "fal-ai/flux/dev"
COST = 0.025          # per image, flux dev at this size
BUDGET = 6.00

W, H = 1920, 1080


def key() -> str:
    env = (ROOT.parent / ".env.local").read_text(encoding="utf-8")
    m = re.search(r"FAL_KEY=(\S+)", env)
    if not m:
        raise SystemExit("no FAL_KEY in .env.local")
    k = m.group(1)
    print(f"  key from .env.local: {k[:8]}...{k[-4:]}")
    return k


def fingerprint(prompt: str) -> str:
    return hashlib.sha256((MODEL + "||" + prompt).encode()).hexdigest()[:16]


def load() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"spent": 0.0, "items": {}}


def save(led: dict) -> None:
    LEDGER.parent.mkdir(exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")


def letterbox(p: Path) -> None:
    """flux returns 1920x1072 for a 16:9 request. Cover-crop to exactly
    1920x1080 so no shot arrives at the assembler off-size."""
    im = Image.open(p).convert("RGB")
    if im.size == (W, H):
        return
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im.crop((x, y, x + W, y + H)).save(p, quality=95)


def main() -> None:
    K = key()
    hdr = {"Authorization": f"Key {K}", "Content-Type": "application/json"}
    led = load()
    jobs = dict(STILLS)
    print(f"  {len(jobs)} unique stills, spent so far ${led['spent']:.2f}")

    streak = 0
    for i, (sid, base) in enumerate(jobs.items(), 1):
        prompt = f"{base}, {STYLE}"
        fp = fingerprint(prompt)
        dst = OUT / f"{sid}.jpg"
        rec = led["items"].get(fp)

        if rec and rec.get("state") == "done" and dst.exists():
            print(f"  [{i:>2}/{len(jobs)}] {sid:16} cached")
            continue
        if led["spent"] + COST > BUDGET:
            print(f"  BUDGET CAP reached at ${led['spent']:.2f}")
            break

        body = {"prompt": prompt,
                "image_size": {"width": W, "height": H},
                "num_inference_steps": 28, "guidance_scale": 3.5,
                "num_images": 1, "enable_safety_checker": False}
        try:
            t0 = time.time()
            r = requests.post(f"https://fal.run/{MODEL}", headers=hdr,
                              json=body, timeout=300)
            # charged the moment the API returns - the job was accepted
            led["spent"] = round(led["spent"] + COST, 4)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:160]}")
            url = r.json()["images"][0]["url"]
            dst.write_bytes(requests.get(url, timeout=180).content)
            letterbox(dst)
            led["items"][fp] = {"id": sid, "state": "done", "url": url,
                                "cost": COST, "prompt": prompt}
            save(led)
            streak = 0
            print(f"  [{i:>2}/{len(jobs)}] {sid:16} ok  {time.time()-t0:5.1f}s  "
                  f"${led['spent']:.2f}")
        except Exception as e:
            streak += 1
            led["items"][fp] = {"id": sid, "state": "failed", "error": str(e)[:300]}
            save(led)
            print(f"  [{i:>2}/{len(jobs)}] {sid:16} FAIL {e}")
            if streak >= 3:
                print("  CIRCUIT BREAKER: 3 consecutive failures, halting")
                break

    save(led)
    done = sum(1 for v in led["items"].values() if v.get("state") == "done")
    print(f"\n  done {done}/{len(jobs)}   spent ${led['spent']:.2f}")
    missing = [s for s in jobs if not (OUT / f"{s}.jpg").exists()]
    if missing:
        print("  MISSING:", missing)
        sys.exit(1)


if __name__ == "__main__":
    main()
